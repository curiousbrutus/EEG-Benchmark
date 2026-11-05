"""P1 — 28: generate LaTeX data tables from results JSON (no hand-typed numbers)."""
from __future__ import annotations
import json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
RES = ROOT / "results"
TAB = ROOT / "tables"


def fmt(x, d=2):
    return f"{x:.{d}f}"


def alpha_table():
    s = json.loads((RES / "summary.json").read_text())
    labels = {
        "ref": "Full montage (64 ch average)",
        "fz": "Single channel (Fz) chain",
        "fz_noise20": "+ noise 20\\,dB", "fz_noise10": "+ noise 10\\,dB",
        "fz_noise5": "+ noise 5\\,dB", "fz_noise0": "+ noise 0\\,dB",
        "fz_blink5": "+ blinks 5/min", "fz_blink15": "+ blinks 15/min",
        "fz_blink30": "+ blinks 30/min", "fz_combined": "+ noise 0\\,dB and blinks 30/min",
    }
    rows = []
    for key, lab in labels.items():
        v = s["alpha_reactivity_log_ratio"][key]
        rows.append(f"    {lab} & {fmt(v['mean'])} & [{fmt(v['ci_low'])}, {fmt(v['ci_high'])}] \\\\")
    body = "\n".join(rows)
    n = s["n_subjects"]
    tex = f"""\\begin{{table}}[H]
  \\centering
  \\caption{{Alpha reactivity by condition ($N={n}$; mean log ratio with 95\\% CI). Noise
  and blink arms are separate; the final row combines both.}}
  \\label{{tab:alpha}}
  \\begin{{tabular}}{{lcc}}
    \\hline
    Condition & Log ratio & 95\\% CI \\\\
    \\hline
{body}
    \\hline
  \\end{{tabular}}
\\end{{table}}
"""
    (TAB / "alpha.tex").write_text(tex)


def affective_table():
    a = json.loads((RES / "affective.json").read_text())["summary"]
    e = json.loads((RES / "emotiv.json").read_text())["summary"]

    def cell(d):
        return f"{fmt(d['mean'])} [{fmt(d['ci_low'])}, {fmt(d['ci_high'])}]"
    rows = [
        ("Valence", "valence", a["valence_full"], e["valence"], a["valence_single"]),
        ("Arousal", "arousal", a["arousal_full"], e["arousal"], a["arousal_single"]),
        ("Four quadrants", "quadrant", a["quadrant_full"], e["quadrant"], a["quadrant_single"]),
    ]
    body = "\n".join(f"    {lab} & {cell(f)} & {cell(l)} & {cell(s)} \\\\"
                     for lab, _, f, l, s in rows)
    n_aff = a["valence_full"]["n"]; n_emo = e["valence"]["n"]
    tex = f"""\\begin{{table}}[H]
  \\centering
  \\caption{{Affective decoding by acquisition representation: high-end full montage
  ($N={n_aff}$ recordings), low-cost 14-channel Emotiv ($N={n_emo}$), and high-end data
  reduced to one degraded channel ($N={n_aff}$). Balanced accuracy with 95\\% CI;
  chance 0.50 (binary) and 0.25 (four-class).}}
  \\label{{tab:affective}}
  \\begin{{tabular}}{{lccc}}
    \\hline
    Target & High-end montage & Low-cost 14 ch & Single channel \\\\
    \\hline
{body}
    \\hline
  \\end{{tabular}}
\\end{{table}}
"""
    (TAB / "affective.tex").write_text(tex)


def decomp_table():
    d = json.loads((RES / "affective_decomp.json").read_text())["summary"]
    labels = [("full", "Full montage, all bands"),
              ("full_theta_alpha", "Full montage, theta+alpha only"),
              ("full_beta", "Full montage, beta only"),
              ("band", "128\\,Hz / quantised / band-limited"),
              ("single_Fz", "Single Fz"), ("single_Cz", "Single Cz"),
              ("single_Pz", "Single Pz"), ("single_Oz", "Single Oz")]
    body = "\n".join(
        f"    {lab} & {fmt(d['valence'][k]['mean'])} & {fmt(d['arousal'][k]['mean'])} & {fmt(d['quadrant'][k]['mean'])} \\\\"
        for k, lab in labels)
    n = d["valence"]["full"]["n"]
    tex = f"""\\begin{{table}}[H]
  \\centering
  \\caption{{Decomposition of affective decoding ({n} high-end recordings; balanced
  accuracy). Chance is 0.50 for valence/arousal and 0.25 for four-class.}}
  \\label{{tab:decomp}}
  \\begin{{tabular}}{{lccc}}
    \\hline
    Representation & Valence & Arousal & Four-class \\\\
    \\hline
{body}
    \\hline
  \\end{{tabular}}
\\end{{table}}
"""
    (TAB / "decomp.tex").write_text(tex)


def main():
    TAB.mkdir(exist_ok=True)
    alpha_table(); affective_table(); decomp_table()
    print("wrote tables/alpha.tex, tables/affective.tex, tables/decomp.tex")


if __name__ == "__main__":
    main()
