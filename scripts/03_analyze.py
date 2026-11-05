"""P1 — 03: run the pre-registered analyses and write results/metrics_Sxxx.json.

PSD is computed with scipy.signal.welch (not MNE) so the script is independent of
MNE API churn. Numbers written here are the ONLY source for the manuscript's
Results section. Aggregate with 05_aggregate.py.

Usage:
    python scripts/03_analyze.py --subject 1
"""
from __future__ import annotations

import argparse
import json
import pathlib

import numpy as np
from scipy.signal import welch

BANDS = {"theta": (4, 8), "alpha": (8, 12), "beta": (13, 30)}
SEED = 20261103
CONDITIONS = (
    ["ref", "fz", "fz_128", "fz_128_quant", "fz_128_quant_band"]
    + [f"fz_noise{snr}" for snr in (20, 10, 5, 0)]
    + [f"fz_blink{rate}" for rate in (5, 15, 30)]
    + ["fz_combined"]
)
MI_RUNS = [4, 8, 12]  # imagined left/right hand


def psd_mean_power(x: np.ndarray, fs: float, band: tuple[float, float]) -> float:
    """Mean band power from a (n_channels, n_times) array."""
    nper = max(4, int(2 * fs))
    f, p = welch(x, fs=fs, nperseg=min(nper, x.shape[-1]),
                 noverlap=min(int(fs), x.shape[-1] // 2), axis=-1)
    mask = (f >= band[0]) & (f <= band[1])
    return float(np.mean(p[..., mask]))


def load_condition(data_dir: pathlib.Path, subject: int, run: int, condition: str):
    import mne

    path = data_dir / f"S{subject:03d}R{run:02d}_{condition}.fif"
    if not path.exists():
        raise FileNotFoundError(path)
    return mne.io.read_raw_fif(path, preload=True, verbose="ERROR")


def band_power_raw(raw, band: tuple[float, float]) -> float:
    return psd_mean_power(raw.get_data(), raw.info["sfreq"], band)


def alpha_reactivity(data_dir: pathlib.Path, subject: int) -> dict:
    out = {}
    for condition in CONDITIONS:
        eo = band_power_raw(load_condition(data_dir, subject, 1, condition), BANDS["alpha"])
        ec = band_power_raw(load_condition(data_dir, subject, 2, condition), BANDS["alpha"])
        out[condition] = {
            "eyes_open": eo,
            "eyes_closed": ec,
            "log_ratio": float(np.log(ec / eo)) if eo > 0 else float("nan"),
        }
    return out


def motor_decoding(data_dir: pathlib.Path, subject: int, condition: str = "fz") -> dict:
    """H2: within-subject single-trial left/right hand accuracy (imagined)."""
    try:
        import mne
        from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
        from sklearn.model_selection import StratifiedKFold, cross_val_score
    except ImportError as exc:
        return {"status": "skipped", "reason": str(exc)}

    features, labels = [], []
    for run in MI_RUNS:
        path = data_dir / f"S{subject:03d}R{run:02d}_{condition}.fif"
        if not path.exists():
            continue
        raw = mne.io.read_raw_fif(path, preload=True, verbose="ERROR")
        events, event_id = mne.events_from_annotations(raw, verbose="ERROR")
        wanted = {k: v for k, v in event_id.items() if k in ("T1", "T2")}
        if len(wanted) < 2:
            continue
        epochs = mne.Epochs(raw, events, wanted, tmin=0.0, tmax=3.0,
                            baseline=None, preload=True, verbose="ERROR")
        data = epochs.get_data()  # (n_epochs, n_channels, n_times)
        fs = raw.info["sfreq"]
        feats = []
        for epoch in data:
            nper = max(4, int(2 * fs))
            f, p = welch(epoch, fs=fs, nperseg=min(nper, epoch.shape[-1]),
                         noverlap=min(int(fs), epoch.shape[-1] // 2), axis=-1)
            mask = (f >= 8) & (f <= 30)
            feats.append(np.log(np.mean(p[..., mask], axis=-1)))
        features.append(np.vstack(feats))
        labels.append(epochs.events[:, -1])

    if not features:
        return {"status": "no_epochs", "accuracy": None}
    X = np.vstack(features)
    y = np.concatenate(labels)
    if len(np.unique(y)) < 2 or len(y) < 10:
        return {"status": "insufficient_trials", "accuracy": None, "n_trials": int(len(y))}
    clf = LinearDiscriminantAnalysis(solver="lsqr", shrinkage="auto")
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEED)
    scores = cross_val_score(clf, X, y, cv=cv, scoring="balanced_accuracy")
    return {"status": "ok", "accuracy": float(scores.mean()),
            "sd": float(scores.std()), "n_trials": int(len(y))}


def split_half_reliability(data_dir: pathlib.Path, subject: int,
                           condition: str = "fz_128_quant_band") -> dict:
    """H4: split-half reliability of alpha power (odd vs even 2 s windows).

    DEVIATION from the draft preregistration (ICC(2,1) across repeated runs):
    EEGBCI has a single eyes-open and a single eyes-closed run, so a true
    test-retest ICC is not identifiable. Documented in the deviations log.
    """
    raw = load_condition(data_dir, subject, 2, condition)  # eyes closed
    fs = raw.info["sfreq"]
    data = raw.get_data()[0]
    win = int(2 * fs)
    n_windows = len(data) // win
    if n_windows < 6:
        return {"status": "too_short", "r": None}
    powers = [psd_mean_power(data[i * win:(i + 1) * win][None, :], fs, BANDS["alpha"])
              for i in range(n_windows)]
    powers = np.asarray(powers)
    odd, even = powers[0::2], powers[1::2]
    n = min(len(odd), len(even))
    r = float(np.corrcoef(odd[:n], even[:n])[0, 1])
    sb = 2 * r / (1 + r) if r > -1 else float("nan")
    return {"status": "ok", "r": r, "spearman_brown": sb, "n_windows": int(n * 2)}


def deap_decoding() -> dict:
    """H3 scaffold: affective decoding on DEAP (requires manual data download)."""
    root = pathlib.Path("data/raw/deap")
    if not root.exists():
        return {"status": "not_available",
                "reason": "DEAP requires accepting the data-use agreement; place files under data/raw/deap/",
                "script": "scripts/06_deap.py"}
    return {"status": "available_not_run",
            "script": "scripts/06_deap.py",
            "note": "run 06_deap.py to produce results/deap_metrics.json"}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--subject", type=int, default=1)
    parser.add_argument("--data-dir", type=pathlib.Path, default=pathlib.Path("data/derived"))
    parser.add_argument("--out", type=pathlib.Path, default=pathlib.Path("results"))
    args = parser.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    metrics = {
        "subject": args.subject,
        "seed": SEED,
        "alpha_reactivity": alpha_reactivity(args.data_dir, args.subject),
        "motor_decoding_fz": motor_decoding(args.data_dir, args.subject, "fz"),
        "motor_decoding_full": motor_decoding(args.data_dir, args.subject, "ref"),
        "reliability": split_half_reliability(args.data_dir, args.subject),
        "deap": deap_decoding(),
    }
    out = args.out / f"metrics_S{args.subject:03d}.json"
    out.write_text(json.dumps(metrics, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
