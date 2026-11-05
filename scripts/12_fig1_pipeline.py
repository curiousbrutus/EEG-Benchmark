"""P1 — 12: Figure 1, the degradation tree.

Draws the pipeline as a tree: reference → single channel → 128 Hz → quantisation →
band-limit, then separate noise, blink and combined arms. Grayscale-safe.
"""
from __future__ import annotations

import pathlib

FIG = pathlib.Path("figures")


def main() -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

    fig, ax = plt.subplots(figsize=(11, 4.2))
    ax.set_xlim(0, 11)
    ax.set_ylim(0, 4.2)
    ax.axis("off")

    def box(x, y, w, h, label, style="round,pad=0.02"):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=style,
                                    linewidth=1.2, facecolor="white", edgecolor="black"))
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=8.5)

    def arrow(x1, y1, x2, y2):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                                     mutation_scale=12, linewidth=1.0, color="black"))

    box(0.2, 2.9, 1.7, 0.8, "Reference\n64 ch, 160 Hz")
    box(2.3, 2.9, 1.5, 0.8, "Single channel\n(Fz)")
    box(4.2, 2.9, 1.2, 0.8, "128 Hz")
    box(5.8, 2.9, 1.4, 0.8, "1 µV\nquantisation")
    box(7.6, 2.9, 1.4, 0.8, "1–40 Hz\nband-limit")
    arrow(1.9, 3.3, 2.3, 3.3)
    arrow(3.8, 3.3, 4.2, 3.3)
    arrow(5.4, 3.3, 5.8, 3.3)
    arrow(7.2, 3.3, 7.6, 3.3)

    # branches
    box(4.2, 1.4, 2.0, 0.8, "Noise arm\n20/10/5/0 dB")
    box(6.6, 1.4, 2.0, 0.8, "Blink arm\n5/15/30 per min")
    box(8.9, 1.4, 1.9, 0.8, "Combined\n0 dB + 30/min")
    arrow(8.3, 2.9, 5.2, 2.2)
    arrow(8.6, 2.9, 7.6, 2.2)
    arrow(8.9, 2.9, 9.8, 2.2)

    box(0.2, 0.3, 3.1, 0.8, "Analysis A: alpha reactivity\n(runs 1–2)")
    box(4.2, 0.3, 3.1, 0.8, "Analysis B: motor decoding\n(runs 4/8/12)")
    box(8.0, 0.3, 2.8, 0.8, "Sensitivity: site-matched\nalpha (Fz vs Fz)")
    ax.text(0.2, 1.55, "n = 109 (alpha); 18 high-end + 12 Emotiv (affective); arms separate so the\n"
                       "noise and blink effects are not confounded.",
            fontsize=8, va="center")

    fig.tight_layout()
    FIG.mkdir(exist_ok=True)
    fig.savefig(FIG / "fig1_pipeline.pdf")
    fig.savefig(FIG / "fig1_pipeline.png", dpi=300)
    print("wrote figures/fig1_pipeline.pdf")


if __name__ == "__main__":
    main()
