"""P1 — 07: sensitivity analysis for the decoding arm.

The primary decoder used all 64 channels with log band power + shrinkage LDA and did
not beat chance at the reference. This script tests whether a *sensorimotor* channel
subset (C3, Cz, C4) provides a usable reference, and compares it with Fz alone. The
point is to establish a reference decoder that clears chance before interpreting any
degradation effect.

Usage:
    python scripts/07_sensitivity.py
"""
from __future__ import annotations

import argparse
import json
import pathlib

import numpy as np
from scipy.stats import t as _t
from scipy.signal import welch

SEED = 20261103
MI_RUNS = [4, 8, 12]
CHANNEL_SETS = {
    "fz": ["Fz"],
    "sensorimotor": ["C3", "Cz", "C4"],
    "sensorimotor_lateral": ["C3", "C4"],
}
BAND = (8, 30)


def epoch_features(epochs, ch_names: list[str]) -> np.ndarray:
    """Log mean band power per selected channel, per epoch."""
    data = epochs.get_data(picks=ch_names)  # (n_epochs, n_ch, n_times)
    fs = epochs.info["sfreq"]
    out = []
    for epoch in data:
        nper = min(int(2 * fs), epoch.shape[-1])
        f, p = welch(epoch, fs=fs, nperseg=nper,
                     noverlap=min(int(fs), epoch.shape[-1] // 2), axis=-1)
        mask = (f >= BAND[0]) & (f <= BAND[1])
        out.append(np.log(np.mean(p[..., mask], axis=-1) + 1e-12))
    return np.vstack(out)


def decode(subject: int, data_dir: pathlib.Path, ch_names: list[str]) -> dict:
    import mne
    from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
    from sklearn.model_selection import StratifiedKFold, cross_val_score

    X, y = [], []
    for run in MI_RUNS:
        path = data_dir / f"S{subject:03d}R{run:02d}_ref.fif"
        if not path.exists():
            continue
        raw = mne.io.read_raw_fif(path, preload=True, verbose="ERROR")
        canon = lambda s: "".join(ch for ch in s if ch.isalnum()).lower()  # noqa: E731
        lookup = {canon(c): c for c in raw.ch_names}
        available = [lookup[canon(c)] for c in ch_names if canon(c) in lookup]
        if len(available) != len(ch_names):
            return {"status": "missing_channels", "available": available,
                    "requested": ch_names}
        events, event_id = mne.events_from_annotations(raw, verbose="ERROR")
        wanted = {k: v for k, v in event_id.items() if k in ("T1", "T2")}
        if len(wanted) < 2:
            continue
        epochs = mne.Epochs(raw, events, wanted, tmin=0.0, tmax=3.0,
                            baseline=None, preload=True, verbose="ERROR")
        X.append(epoch_features(epochs, available))
        y.append(epochs.events[:, -1])
    if not X:
        return {"status": "no_epochs", "accuracy": None}
    X = np.vstack(X)
    y = np.concatenate(y)
    if len(np.unique(y)) < 2 or len(y) < 10:
        return {"status": "insufficient", "accuracy": None, "n_trials": int(len(y))}
    clf = LinearDiscriminantAnalysis(solver="lsqr", shrinkage="auto")
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    scores = cross_val_score(clf, X, y, cv=cv, scoring="balanced_accuracy")
    return {"status": "ok", "accuracy": float(scores.mean()),
            "sd": float(scores.std()), "n_trials": int(len(y)),
            "channels": ch_names}


def mean_ci(values: list[float]) -> dict:
    vals = [v for v in values if v is not None and not np.isnan(v)]
    if not vals:
        return {"n": 0, "mean": None, "ci_low": None, "ci_high": None}
    arr = np.asarray(vals, dtype=float)
    n = len(arr)
    mean = float(arr.mean())
    if n <= 1:
        return {"n": n, "mean": mean, "ci_low": None, "ci_high": None}
    sem = float(arr.std(ddof=1) / np.sqrt(n))
    t_crit = float(_t.ppf(0.975, max(n - 1, 1)))
    return {"n": n, "mean": mean, "ci_low": mean - t_crit * sem,
            "ci_high": mean + t_crit * sem}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--subjects", type=int, nargs="+", default=list(range(1, 11)))
    parser.add_argument("--data-dir", type=pathlib.Path, default=pathlib.Path("data/derived"))
    parser.add_argument("--out", type=pathlib.Path, default=pathlib.Path("results/sensitivity.json"))
    args = parser.parse_args()

    results: dict[str, list[dict]] = {name: [] for name in CHANNEL_SETS}
    for subject in args.subjects:
        for name, channels in CHANNEL_SETS.items():
            res = decode(subject, args.data_dir, channels)
            res["subject"] = subject
            results[name].append(res)
        print(f"S{subject:03d} done")

    summary = {}
    for name, rows in results.items():
        accs = [r.get("accuracy") for r in rows if r.get("status") == "ok"]
        summary[name] = {"per_subject": rows, **mean_ci(accs)}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({"n_subjects": len(args.subjects), "summary": summary},
                                   indent=2))
    print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk != "per_subject"}
                      for k, v in summary.items()}, indent=2))


if __name__ == "__main__":
    main()
