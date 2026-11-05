"""P1 — 11: paired contrasts against the reference and retention ratios.

Reviewers correctly noted that the primary analysis reported unpaired means. This
script computes, per condition, the within-subject paired difference from the
reference, a paired t-based 95% CI, and the per-subject retention ratio with its CI.

Usage:
    python scripts/11_paired.py
"""
from __future__ import annotations

import glob
import json
import pathlib

import numpy as np
from scipy.stats import t as _t

from scipy.stats import t as _t


def ci(values: np.ndarray) -> tuple[float, float, float]:
    n = len(values)
    mean = float(values.mean())
    if n < 2:
        return mean, float("nan"), float("nan")
    sem = float(values.std(ddof=1) / np.sqrt(n))
    t = float(_t.ppf(0.975, max(n - 1, 1)))
    return mean, mean - t * sem, mean + t * sem


def main() -> None:
    files = sorted(glob.glob("results/metrics_S*.json"))
    if not files:
        raise SystemExit("no metrics; run 03_analyze.py")
    runs = [json.loads(pathlib.Path(f).read_text()) for f in files]
    conditions = [c for c in runs[0]["alpha_reactivity"] if c != "ref"]

    out = {"n_subjects": len(runs), "conditions": {}}
    ref = np.array([r["alpha_reactivity"]["ref"]["log_ratio"] for r in runs])
    for cond in conditions:
        vals = np.array([r["alpha_reactivity"][cond]["log_ratio"] for r in runs])
        diff = vals - ref
        m, lo, hi = ci(diff)
        ratio = np.exp(vals - ref)  # per-subject retention in power ratio terms
        rm, rlo, rhi = ci(ratio)
        out["conditions"][cond] = {
            "paired_difference_log": {"mean": m, "ci_low": lo, "ci_high": hi},
            "retention_ratio": {"mean": rm, "ci_low": rlo, "ci_high": rhi},
            "mean_log_ratio": float(vals.mean()),
        }
    pathlib.Path("results/paired.json").write_text(json.dumps(out, indent=2))
    print(json.dumps({k: {"paired_log": v["paired_difference_log"],
                          "retention": v["retention_ratio"]}
                      for k, v in out["conditions"].items()}, indent=2))


if __name__ == "__main__":
    main()
