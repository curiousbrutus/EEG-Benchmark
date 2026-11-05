"""P1 — 20: affective decoding on the open low-cost-vs-high-end dataset (H3).

Dataset: Zenodo 14787743 (Sánchez-Reolid et al.). BrainVision recordings
(500 Hz, 66 channels) with BrainVision markers. Marker codes map to IAPS
valence-arousal quadrants:
    1 = AltaAlto      (high valence, high arousal)
    2 = BajoAlto      (low valence, high arousal)
    3 = AltaBajo      (high valence, low arousal)
    4 = BajaBajo      (low valence, low arousal)
    10/14 = neutral (excluded from valence/arousal analyses)

For each subject we decode (a) valence, (b) arousal and (c) the four quadrants,
first from the full montage and then from a single Fz channel degraded to consumer
conditions (128 Hz, 1 uV quantisation, 1-40 Hz). Features are log band power
(theta 4-8, alpha 8-12, beta 13-30) per channel. Classifier: shrinkage LDA,
5-fold stratified within-subject CV.

Output: results/affective.json
"""
from __future__ import annotations

import argparse
import glob
import json
import pathlib
import re

import numpy as np
from scipy.stats import t as _t
from scipy.signal import welch

BANDS = {"theta": (4, 8), "alpha": (8, 12), "beta": (13, 30)}
CODE2Q = {1: "HVHA", 2: "LVHA", 3: "HVLA", 4: "LVLA", 10: "NEUTRAL", 14: "NEUTRAL"}
SEED = 20261103
DATA = pathlib.Path("data/raw/emotion_zenodo/Comparativa EEG-BCI/EEG/Experiment_files")


def parse_vmrk(path: pathlib.Path):
    events = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.match(r"Mk\d+=Stimulus,S\s*(\d+),(\d+),", line.strip())
        if m:
            events.append((int(m.group(1)), int(m.group(2))))
    return events


def epoch_features(epochs_data: np.ndarray, fs: float) -> np.ndarray:
    """(n_epochs, n_ch, n_times) -> (n_epochs, n_ch*3) log band power."""
    feats = []
    for epoch in epochs_data:
        nper = min(int(2 * fs), epoch.shape[-1])
        f, p = welch(epoch, fs=fs, nperseg=nper,
                     noverlap=min(int(fs), epoch.shape[-1] // 2), axis=-1)
        row = []
        for lo, hi in BANDS.values():
            mask = (f >= lo) & (f <= hi)
            row.append(np.log(np.mean(p[..., mask], axis=-1) + 1e-12))
        feats.append(np.concatenate(row))
    return np.vstack(feats)


def decode(X: np.ndarray, y: np.ndarray) -> float | None:
    from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
    from sklearn.model_selection import StratifiedKFold, cross_val_score

    classes, counts = np.unique(y, return_counts=True)
    if len(classes) < 2 or counts.min() < 3:
        return None
    n_splits = min(5, int(counts.min()))
    clf = LinearDiscriminantAnalysis(solver="lsqr", shrinkage="auto")
    cv = StratifiedKFold(n_splits=n_splits, shuffle=True, random_state=SEED)
    try:
        return float(cross_val_score(clf, X, y, cv=cv, scoring="balanced_accuracy").mean())
    except Exception:
        return None


def single_channel_chain(raw):
    """Consumer chain on one Fz electrode: 128 Hz, 1 uV, 1-40 Hz."""
    raw = raw.copy().load_data()
    canon = lambda s: "".join(ch for ch in s if ch.isalnum()).lower()  # noqa: E731
    lookup = {canon(c): c for c in raw.ch_names}
    target = lookup.get("fz")
    if target is None:
        return None
    raw.pick([target])
    raw.resample(128, verbose="ERROR")
    raw._data = np.round(raw.get_data() / 1e-6) * 1e-6
    raw.filter(1.0, 40.0, method="fir", verbose="ERROR")
    return raw


def analyse_subject(vhdr: pathlib.Path) -> dict | None:
    import mne

    vm = vhdr.with_suffix(".vmrk")
    if not vm.exists():
        return None
    events = [(c, p) for c, p in parse_vmrk(vm) if c in CODE2Q]
    if not events:
        return None
    raw = mne.io.read_raw_brainvision(vhdr, preload=False, verbose="ERROR")
    picks = mne.pick_types(raw.info, eeg=True, meg=False, exclude=[])
    if len(picks) == 0:
        return None

    onsets = np.array([p for _, p in events]) - 1  # vmrk positions are 1-based
    codes = np.array([c for c, _ in events])
    tmax = 2.5
    epochs_full = []
    for onset in onsets:
        tmin_s = onset / raw.info["sfreq"]
        seg = raw.copy().crop(tmin=tmin_s, tmax=tmin_s + tmax, include_tmax=False)
        epochs_full.append(seg.get_data(picks=picks))
    X_full = epoch_features(np.array(epochs_full), raw.info["sfreq"])

    raw_one = single_channel_chain(raw)
    if raw_one is None:
        return None
    fs1 = raw_one.info["sfreq"]
    epochs_one = []
    for onset in onsets:
        tmin_s = onset / raw.info["sfreq"]
        seg = raw_one.copy().crop(tmin=tmin_s, tmax=tmin_s + tmax, include_tmax=False)
        if len(seg.times) < int(1.0 * fs1):
            return None
        epochs_one.append(seg.get_data())
    X_one = epoch_features(np.array(epochs_one), fs1)

    quad = np.array([CODE2Q[c] for c in codes])
    keep = quad != "NEUTRAL"
    result = {"recording": vhdr.name, "n_quadrant_trials": int(keep.sum()),
              "n_neutral": int((~keep).sum()), "targets": {}}

    # 4-class quadrant decoding
    result["targets"]["quadrant_full"] = {"balanced_accuracy": decode(X_full[keep], quad[keep])}
    result["targets"]["quadrant_single"] = {"balanced_accuracy": decode(X_one[keep], quad[keep])}

    for name, pos in (("valence", {"HVHA", "HVLA"}), ("arousal", {"HVHA", "LVHA"})):
        y = np.isin(quad, list(pos)).astype(int)
        result["targets"][f"{name}_full"] = {"balanced_accuracy": decode(X_full[keep], y[keep])}
        result["targets"][f"{name}_single"] = {"balanced_accuracy": decode(X_one[keep], y[keep])}
    return result


def mean_ci(vals):
    vals = [v for v in vals if v is not None and not (isinstance(v, float) and np.isnan(v))]
    if not vals:
        return {"n": 0, "mean": None, "ci_low": None, "ci_high": None}
    a = np.asarray(vals, float); n = len(a)
    sem = a.std(ddof=1) / np.sqrt(n) if n > 1 else 0.0
    t = float(_t.ppf(0.975, max(n - 1, 1)))
    return {"n": n, "mean": float(a.mean()), "ci_low": float(a.mean() - t * sem),
            "ci_high": float(a.mean() + t * sem)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=pathlib.Path, default=DATA)
    ap.add_argument("--out", type=pathlib.Path, default=pathlib.Path("results/affective.json"))
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    files = sorted(args.data.glob("eegbci*-*.vhdr"))
    if args.limit:
        files = files[: args.limit]
    rows = []
    for f in files:
        try:
            r = analyse_subject(f)
        except Exception as exc:  # keep going; record failure
            print(f"FAIL {f.name}: {exc}")
            continue
        if r:
            rows.append(r); print(f"{f.name}: trials={r['n_quadrant_trials']}")

    summary = {}
    for key in ["quadrant_full", "quadrant_single", "valence_full", "valence_single",
                "arousal_full", "arousal_single"]:
        vals = [r["targets"].get(key, {}).get("balanced_accuracy") for r in rows]
        summary[key] = mean_ci(vals)
    out = {"n_recordings": len(rows), "recordings": rows, "summary": summary,
           "chance": {"quadrant": 0.25, "binary": 0.5}}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
