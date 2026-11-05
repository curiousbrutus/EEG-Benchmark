"""P1 — 10: ICC(2,1) for alpha power across the three imagined left/right runs.

Runs 4, 8 and 12 are the same task (imagined left/right hand) recorded three times,
so they provide a within-session block reliability estimate. This is not a
test-retest estimate across sessions, and the manuscript labels it accordingly.

Usage:
    python scripts/10_icc.py
"""
from __future__ import annotations

import argparse
import json
import pathlib

import numpy as np
from scipy.stats import t as _t
from scipy.signal import welch

ALPHA = (8, 12)
RUNS = [4, 8, 12]


def alpha_power(path: pathlib.Path) -> float:
    import mne

    raw = mne.io.read_raw_fif(path, preload=True, verbose="ERROR")
    data = raw.get_data()
    fs = raw.info["sfreq"]
    f, p = welch(data, fs=fs, nperseg=min(int(2 * fs), data.shape[-1]),
                 noverlap=min(int(fs), data.shape[-1] // 2), axis=-1)
    mask = (f >= ALPHA[0]) & (f <= ALPHA[1])
    return float(np.mean(p[..., mask]))


def icc21(matrix: np.ndarray) -> float:
    """ICC(2,1) two-way random effects, single measurement.

    matrix: subjects x raters (rows = subjects, columns = repeated measures).
    """
    n, k = matrix.shape
    grand = matrix.mean()
    ms_rows = k * ((matrix.mean(axis=1) - grand) ** 2).sum() / (n - 1)
    ms_cols = n * ((matrix.mean(axis=0) - grand) ** 2).sum() / (k - 1)
    ss_total = ((matrix - grand) ** 2).sum()
    ss_error = ss_total - (ms_rows * (n - 1)) - (ms_cols * (k - 1))
    ms_error = ss_error / ((n - 1) * (k - 1))
    denom = ms_rows + (k - 1) * ms_error + k * (ms_cols - ms_error) / n
    return float((ms_rows - ms_error) / denom) if denom else float("nan")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--subjects", type=int, nargs="+", default=list(range(1, 11)))
    parser.add_argument("--data-dir", type=pathlib.Path, default=pathlib.Path("data/derived"))
    parser.add_argument("--out", type=pathlib.Path, default=pathlib.Path("results/icc.json"))
    args = parser.parse_args()

    rows = []
    for subject in args.subjects:
        vals = []
        for run in RUNS:
            p = args.data_dir / f"S{subject:03d}R{run:02d}_fz_128_quant_band.fif"
            if not p.exists():
                vals = []
                break
            vals.append(alpha_power(p))
        if len(vals) == len(RUNS):
            rows.append(vals)
    if not rows:
        raise SystemExit("no complete triples found; run 02_degrade.py first")
    matrix = np.asarray(rows, dtype=float)
    value = icc21(matrix)
    out = {"n_subjects": len(rows), "runs": RUNS, "icc_2_1": value,
           "note": "within-session block reliability across runs 4/8/12; not test-retest"}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(out, indent=2))
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
