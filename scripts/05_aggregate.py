"""P1 — 05: aggregate single-subject metrics into results/summary.json.

Computes mean, 95% CI (t-based) and N per condition / outcome. This file is the
only input for the manuscript's Results numbers.

Usage:
    python scripts/05_aggregate.py
"""
from __future__ import annotations

import glob
import json
import math
import pathlib

import numpy as np
from scipy.stats import t as _t


def mean_ci(values: list[float]) -> dict:
    vals = [v for v in values if v is not None and not (isinstance(v, float) and math.isnan(v))]
    if not vals:
        return {"n": 0, "mean": None, "ci_low": None, "ci_high": None}
    arr = np.asarray(vals, dtype=float)
    mean = float(arr.mean())
    n = len(arr)
    if n <= 1:
        return {"n": n, "mean": mean, "ci_low": None, "ci_high": None}
    sem = float(arr.std(ddof=1) / math.sqrt(n))
    # t critical for 95% with df=n-1 (approx table for small n)
    t_crit = float(_t.ppf(0.975, max(n - 1, 1)))
    return {"n": n, "mean": mean,
            "ci_low": mean - t_crit * sem, "ci_high": mean + t_crit * sem}


def main() -> None:
    files = sorted(glob.glob("results/metrics_S*.json"))
    if not files:
        raise SystemExit("no results/metrics_S*.json; run 03_analyze.py first")
    runs = [json.loads(pathlib.Path(f).read_text()) for f in files]

    conditions = list(runs[0]["alpha_reactivity"])
    alpha = {c: mean_ci([r["alpha_reactivity"][c]["log_ratio"] for r in runs])
             for c in conditions}

    decoding = {
        "fz": mean_ci([r["motor_decoding_fz"].get("accuracy") for r in runs]),
        "full": mean_ci([r["motor_decoding_full"].get("accuracy") for r in runs]),
    }
    reliability = mean_ci([r["reliability"].get("spearman_brown") for r in runs])

    summary = {
        "n_subjects": len(runs),
        "subjects": [r["subject"] for r in runs],
        "alpha_reactivity_log_ratio": alpha,
        "motor_decoding_balanced_accuracy": decoding,
        "split_half_reliability_spearman_brown": reliability,
        "deap": runs[0]["deap"],
        "note": "Preliminary: EEGBCI only, imagined left/right hand runs 4/8/12. "
                "DEAP affective decoding not yet available (manual data access).",
    }
    pathlib.Path("results").mkdir(exist_ok=True)
    pathlib.Path("results/summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
