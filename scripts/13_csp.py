"""P1 — 13: CSP reference decoder for the motor-imagery arm.

The primary decoder used log band power + LDA and did not clear chance at the
reference. This script tests a standard motor-imagery pipeline: common spatial
patterns (CSP) fitted *inside* each cross-validation fold, followed by LDA. CSP is
only defined for multiple channels, so it applies to the full montage and the
sensorimotor subset, not to the single-channel condition; that asymmetry is the
constraint the paper is about, and is reported explicitly.

Usage:
    python scripts/13_csp.py
Output: results/csp.json
"""
from __future__ import annotations

import argparse
import json
import pathlib

import numpy as np
from scipy.stats import t as _t

SEED = 20261103
MI_RUNS = [4, 8, 12]


def mean_ci(values: list[float]) -> dict:
    vals = [v for v in values if v is not None and not np.isnan(v)]
    if not vals:
        return {"n": 0, "mean": None, "ci_low": None, "ci_high": None}
    arr = np.asarray(vals, dtype=float)
    n = len(arr)
    sem = float(arr.std(ddof=1) / np.sqrt(n)) if n > 1 else 0.0
    t = float(_t.ppf(0.975, max(n - 1, 1)))
    return {"n": n, "mean": float(arr.mean()),
            "ci_low": float(arr.mean() - t * sem),
            "ci_high": float(arr.mean() + t * sem)}


def decode_subject(subject: int, data_dir: pathlib.Path, channels: list[str],
                   n_components: int = 4) -> float | None:
    import mne
    from mne.decoding import CSP
    from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
    from sklearn.model_selection import StratifiedKFold, cross_val_score
    from sklearn.pipeline import Pipeline

    epochs_list, labels = [], []
    for run in MI_RUNS:
        path = data_dir / f"S{subject:03d}R{run:02d}_ref.fif"
        if not path.exists():
            return None
        raw = mne.io.read_raw_fif(path, preload=True, verbose="ERROR")
        canon = lambda s: "".join(ch for ch in s if ch.isalnum()).lower()  # noqa: E731
        lookup = {canon(c): c for c in raw.ch_names}
        picks = [lookup[canon(c)] for c in channels if canon(c) in lookup]
        if len(picks) != len(channels):
            return None
        events, event_id = mne.events_from_annotations(raw, verbose="ERROR")
        wanted = {k: v for k, v in event_id.items() if k in ("T1", "T2")}
        if len(wanted) < 2:
            return None
        epochs = mne.Epochs(raw, events, wanted, tmin=0.5, tmax=3.0,
                            picks=picks, baseline=None, preload=True, verbose="ERROR")
        epochs_list.append(epochs.get_data())
        labels.append(epochs.events[:, -1])

    if not epochs_list:
        return None
    X = np.concatenate(epochs_list, axis=0)
    y = np.concatenate(labels)
    if len(np.unique(y)) < 2 or len(y) < 20:
        return None
    X = X - X.mean(axis=-1, keepdims=True)  # centre each epoch
    pipe = Pipeline([
        ("csp", CSP(n_components=n_components, log=True, reg="ledoit_wolf")),
        ("lda", LinearDiscriminantAnalysis()),
    ])
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    try:
        scores = cross_val_score(pipe, X, y, cv=cv, scoring="balanced_accuracy")
    except Exception:
        return None
    return float(scores.mean())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--subjects", type=int, nargs="+", default=list(range(1, 11)))
    ap.add_argument("--data-dir", type=pathlib.Path, default=pathlib.Path("data/derived"))
    ap.add_argument("--out", type=pathlib.Path, default=pathlib.Path("results/csp.json"))
    args = ap.parse_args()

    sets = {"full_montage": ["Fz"], "sensorimotor": ["C3", "Cz", "C4"]}
    # full montage: use all channels from the ref file, not just Fz
    results: dict[str, list[float]] = {"full_montage": [], "sensorimotor": []}
    for subject in args.subjects:
        # sensorimotor subset (CSP on three channels)
        acc = decode_subject(subject, args.data_dir, sets["sensorimotor"])
        if acc is not None:
            results["sensorimotor"].append(acc)
        # full montage: all EEG channels
        import mne
        path = args.data_dir / f"S{subject:03d}R04_ref.fif"
        if path.exists():
            raw = mne.io.read_raw_fif(path, preload=True, verbose="ERROR")
            channels = raw.ch_names
            acc_full = decode_subject(subject, args.data_dir, channels)
            if acc_full is not None:
                results["full_montage"].append(acc_full)
        print(f"S{subject:03d} done")

    summary = {name: {**mean_ci(vals), "per_subject": vals}
               for name, vals in results.items()}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2))
    print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk != "per_subject"}
                      for k, v in summary.items()}, indent=2))


if __name__ == "__main__":
    main()
