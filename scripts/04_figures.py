"""P1 — 04: figures from results/*.json.

fig2 = retention relative to the full-montage reference (paired ratios) with the
pre-specified 50% decision line.
fig3 = motor-decoding accuracy including the sensorimotor sensitivity analysis.
Requires matplotlib: pip install matplotlib
"""
from __future__ import annotations

import json
import pathlib

FIG_DIR = pathlib.Path("figures")
RESULTS = pathlib.Path("results")
SHORT = {
    "fz": "single channel",
    "fz_128": "+128 Hz",
    "fz_128_quant": "+quant",
    "fz_128_quant_band": "+band",
    "fz_noise20": "noise 20 dB",
    "fz_noise10": "noise 10 dB",
    "fz_noise5": "noise 5 dB",
    "fz_noise0": "noise 0 dB",
    "fz_blink5": "blinks 5/min",
    "fz_blink15": "blinks 15/min",
    "fz_blink30": "blinks 30/min",
    "fz_combined": "0 dB + 30/min",
}


def load(name: str) -> dict:
    p = RESULTS / name
    if not p.exists():
        raise SystemExit(f"missing {p}; run the analysis first")
    return json.loads(p.read_text())


def fig_retention() -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    _paired_doc = load("paired.json")
    n_subj = _paired_doc.get("n_subjects", 0)
    import math
    infer = load("inference.json")["alpha"]
    labels, means, los, his = [], [], [], []
    for key in ["fz_noise20", "fz_noise10", "fz_noise5", "fz_noise0",
                "fz_blink5", "fz_blink15", "fz_blink30", "fz_combined"]:
        if key not in infer or "vs_chain" not in infer[key]:
            continue
        d = infer[key]["vs_chain"]
        labels.append(SHORT.get(key, key))
        m = math.exp(d["mean"]); lo = math.exp(d["ci_low"]); hi = math.exp(d["ci_high"])
        means.append(m); los.append(m - lo); his.append(hi - m)

    plt.rcParams.update({"font.size": 10})
    fig, ax = plt.subplots(figsize=(9.5, 4.6))
    ax.bar(labels, means, yerr=[los, his], capsize=4)
    ax.axhline(0.5, color="black", ls="--", lw=1)
    ax.text(len(labels) - 0.6, 0.52, "50% decision line", fontsize=8, ha="right")
    ax.set_ylabel(f"geometric retention (N={n_subj}; 95\% CI)")
    ax.set_ylim(0, 1.4)
    ax.tick_params(axis="x", rotation=30)
    fig.tight_layout()
    FIG_DIR.mkdir(exist_ok=True)
    fig.savefig(FIG_DIR / "fig2_retention.pdf")
    fig.savefig(FIG_DIR / "fig2_retention.png", dpi=300)
    print("wrote figures/fig2_retention.pdf")


def fig_decoding() -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    summary = load("summary.json")["motor_decoding_balanced_accuracy"]
    csp = load("csp.json")
    bars = [("Fz\n(single)", summary["fz"]),
            ("all 64 ch", summary["full"]),
            ("CSP\nfull montage", csp["full_montage"]),
            ("CSP\nsensorimotor", csp["sensorimotor"])]
    labels = [b[0] for b in bars]
    means = [b[1]["mean"] for b in bars]
    los = [b[1]["mean"] - b[1]["ci_low"] for b in bars]
    his = [b[1]["ci_high"] - b[1]["mean"] for b in bars]

    plt.rcParams.update({"font.size": 10})
    fig, ax = plt.subplots(figsize=(7.5, 4.4))
    ax.bar(labels, means, yerr=[los, his], capsize=4)
    ax.axhline(0.5, color="black", ls="--", lw=1)
    ax.set_ylim(0.40, 0.70)
    ax.set_ylabel("balanced accuracy (chance = 0.50)")
    fig.tight_layout()
    FIG_DIR.mkdir(exist_ok=True)
    fig.savefig(FIG_DIR / "fig5_decoding.pdf")
    fig.savefig(FIG_DIR / "fig5_decoding.png", dpi=300)
    print("wrote figures/fig5_decoding.pdf")


def main() -> None:
    try:
        import matplotlib  # noqa: F401
    except ImportError:
        raise SystemExit("matplotlib is not installed: pip install matplotlib")
    FIG_DIR.mkdir(exist_ok=True)
    fig_retention()
    fig_decoding()


if __name__ == "__main__":
    main()
