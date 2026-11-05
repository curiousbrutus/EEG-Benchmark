"""P1 — 06: affective decoding on DEAP (H3).

DEAP is not downloadable automatically. After accepting the data-use agreement at
https://www.eecs.qmul.ac.uk/mmv/datasets/deap/, place the preprocessed Python
files at data/raw/deap/data_preprocessed_python/s01.dat ... s32.dat.

Expected structure per subject file (pickle dict):
    data:   (40 trials, 40 channels, 8064 samples)  # 32 EEG + 8 peripheral
    labels: (40 trials, 4)  # valence, arousal, dominance, liking (1..9)

Features: log band power (theta 4-8, alpha 8-12, beta 13-30) on the 32 EEG
channels, per trial. Labels: within-subject median split of valence and arousal.
Classifier: shrinkage LDA, 5-fold stratified CV. Output: balanced accuracy and AUC.

Usage:
    python scripts/06_deap.py
    python scripts/06_deap.py --subject 1
"""
from __future__ import annotations

import argparse
import json
import pathlib
import pickle

import numpy as np
from scipy.signal import welch

BANDS = {"theta": (4, 8), "alpha": (8, 12), "beta": (13, 30)}
N_EEG_CHANNELS = 32
FS = 128.0
SEED = 20261103


def load_subject(path: pathlib.Path) -> tuple[np.ndarray, np.ndarray]:
    with path.open("rb") as fh:
        try:
            subject = pickle.load(fh, encoding="latin1")
        except TypeError:  # very old pickles
            subject = pickle.load(fh)
    return np.asarray(subject["data"]), np.asarray(subject["labels"])


def trial_features(data: np.ndarray) -> np.ndarray:
    """(trials, 32ch, samples) -> (trials, 32ch*3bands) log band power."""
    feats = []
    for trial in data:
        eeg = trial[:N_EEG_CHANNELS]
        row = []
        for lo, hi in BANDS.values():
            f, p = welch(eeg, fs=FS, nperseg=int(2 * FS), noverlap=int(FS), axis=-1)
            mask = (f >= lo) & (f <= hi)
            row.append(np.log(np.mean(p[..., mask], axis=-1) + 1e-12))
        feats.append(np.concatenate(row))
    return np.vstack(feats)


def decode_subject(path: pathlib.Path) -> dict:
    from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
    from sklearn.metrics import roc_auc_score
    from sklearn.model_selection import StratifiedKFold, cross_val_predict, cross_val_score

    data, labels = load_subject(path)
    X = trial_features(data)
    out = {"subject_file": path.name, "n_trials": int(X.shape[0]), "targets": {}}

    for idx, name in ((0, "valence"), (1, "arousal")):
        y = (labels[:, idx] > np.median(labels[:, idx])).astype(int)
        if len(np.unique(y)) < 2:
            out["targets"][name] = {"status": "single_class"}
            continue
        clf = LinearDiscriminantAnalysis(solver="lsqr", shrinkage="auto")
        cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
        acc = cross_val_score(clf, X, y, cv=cv, scoring="balanced_accuracy").mean()
        try:
            proba = cross_val_predict(clf, X, y, cv=cv, method="predict_proba")[:, 1]
            auc = roc_auc_score(y, proba)
        except Exception:
            auc = None
        out["targets"][name] = {"status": "ok", "balanced_accuracy": float(acc),
                                "auc": float(auc) if auc is not None else None}
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=pathlib.Path,
                        default=pathlib.Path("data/raw/deap/data_preprocessed_python"))
    parser.add_argument("--subject", type=int, default=None)
    parser.add_argument("--out", type=pathlib.Path, default=pathlib.Path("results"))
    args = parser.parse_args()

    if not args.root.exists():
        raise SystemExit(
            "DEAP data not found. Accept the data-use agreement, download the "
            "preprocessed Python files, and unpack them to data/raw/deap/. "
            "This script cannot download them for you."
        )
    files = sorted(args.root.glob("s*.dat"))
    if args.subject is not None:
        files = [f for f in files if f.stem == f"s{args.subject:02d}"]
    if not files:
        raise SystemExit(f"no s*.dat files under {args.root}")

    results = [decode_subject(f) for f in files]
    summary = {"n_subjects": len(results), "results": results}
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "deap_metrics.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
