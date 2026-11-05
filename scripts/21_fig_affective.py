"""P1 — 21: affective decoding figure (full montage vs single-channel)."""
from __future__ import annotations
import json, pathlib
FIG = pathlib.Path("figures"); RES = pathlib.Path("results")

def main() -> None:
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np
    data = json.loads((RES / "affective.json").read_text())["summary"]
    emo = json.loads((RES / "emotiv.json").read_text())["summary"]
    emo_map = {"valence": "valence_emotiv", "arousal": "arousal_emotiv", "quadrant": "quadrant_emotiv"}
    for k, v in emo_map.items():
        data[v] = emo[k]
    keys = [("valence_full", "valence\nhigh-end"), ("valence_emotiv", "valence\nEmotiv 14ch"), ("valence_single", "valence\nsingle ch"),
            ("arousal_full", "arousal\nhigh-end"), ("arousal_emotiv", "arousal\nEmotiv 14ch"), ("arousal_single", "arousal\nsingle ch"),
            ("quadrant_full", "4-class\nhigh-end"), ("quadrant_emotiv", "4-class\nEmotiv 14ch"), ("quadrant_single", "4-class\nsingle ch")]
    labels, means, los, his = [], [], [], []
    for k, lab in keys:
        d = data[k]
        if d.get("mean") is None: continue
        labels.append(lab); means.append(d["mean"])
        los.append(d["mean"] - (d["ci_low"] if d["ci_low"] is not None else d["mean"]))
        his.append((d["ci_high"] if d["ci_high"] is not None else d["mean"]) - d["mean"])
    plt.rcParams.update({"font.size": 9})
    fig, ax = plt.subplots(figsize=(12, 4.8))
    x = np.arange(len(labels)); width = 0.4
    colors = ["#1f77b4" if "high-end" in l else ("#2ca02c" if "Emotiv" in l else "#ff7f0e") for l in labels]
    ax.bar(x, means, yerr=[los, his], capsize=4, color=colors)
    ax.axhline(0.5, color="black", ls="--", lw=1)
    ax.axhline(0.25, color="grey", ls=":", lw=1)
    ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=8)
    ax.set_ylim(0.2, 0.85); ax.set_ylabel("balanced accuracy")
    fig.tight_layout(); FIG.mkdir(exist_ok=True)
    fig.savefig(FIG / "fig3_affective.pdf"); fig.savefig(FIG / "fig3_affective.png", dpi=300)
    print("wrote figures/fig3_affective.pdf")
if __name__ == "__main__": main()
