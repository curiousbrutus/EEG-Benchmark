"""P1 — 08: site-matched alpha sensitivity analysis.

The primary alpha comparison used the mean over all 64 channels as the reference and
a single Fz electrode as the degraded condition. That confounds channel count with
electrode site (posterior alpha generators dominate the 64-channel average). This
script computes alpha power at the *same* site in both conditions:

    ref_fz      : Fz channel from the full-montage, full-sampling recording
    fz_single   : Fz from the single-channel chain (128 Hz, quantised, band-limited)
    ref_all     : mean over all channels (the original reference)
    ref_posterior: mean over posterior channels (Pz/Oz/O1/O2/POz if present)

Output: results/alpha_site_sensitivity.json with per-subject log ratios and CIs.

Usage:
    python scripts/08_alpha_sensitivity.py
"""
from __future__ import annotations

import argparse
import json
import pathlib

import numpy as np
from scipy.stats import t as _t
from scipy.signal import welch

ALPHA = (8, 12)
POSTERIOR = ["Pz", "Oz", "O1", "O2", "POz", "PO3", "PO4"]


def canon(name: str) -> str:
    return "".join(ch for ch in name if ch.isalnum()).lower()


def alpha_power(data: np.ndarray, fs: float) -> float:
    nper = min(int(2 * fs), data.shape[-1])
    f, p = welch(data, fs=fs, nperseg=nper,
                 noverlap=min(int(fs), data.shape[-1] // 2), axis=-1)
    mask = (f >= ALPHA[0]) & (f <= ALPHA[1])
    return float(np.mean(p[..., mask]))


def mean_channels(raw, names: list[str]) -> float:
    lookup = {canon(c): c for c in raw.ch_names}
    actual = [lookup[canon(n)] for n in names if canon(n) in lookup]
    if not actual:
        return float("nan")
    return alpha_power(raw.get_data(picks=actual), raw.info["sfreq"])


def main() -> None:
    import mne

    parser = argparse.ArgumentParser()
    parser.add_argument("--subjects", type=int, nargs="+", default=list(range(1, 11)))
    parser.add_argument("--data-dir", type=pathlib.Path, default=pathlib.Path("data/derived"))
    parser.add_argument("--out", type=pathlib.Path,
                        default=pathlib.Path("results/alpha_site_sensitivity.json"))
    args = parser.parse_args()

    rows = []
    for subject in args.subjects:
        ref = mne.io.read_raw_fif(args.data_dir / f"S{subject:03d}R02_ref.fif",
                                  preload=True, verbose="ERROR")
        single = mne.io.read_raw_fif(
            args.data_dir / f"S{subject:03d}R02_fz_128_quant_band.fif",
            preload=True, verbose="ERROR")
        lookup = {canon(c): c for c in ref.ch_names}
        fz_name = lookup.get(canon("Fz"))
        ref_fz = alpha_power(ref.get_data(picks=[fz_name]), ref.info["sfreq"])
        ref_all = alpha_power(ref.get_data(), ref.info["sfreq"])
        ref_post = mean_channels(ref, POSTERIOR)
        fz_single = alpha_power(single.get_data(), single.info["sfreq"])
        rows.append({
            "subject": subject,
            "ref_fz": ref_fz, "ref_all": ref_all, "ref_posterior": ref_post,
            "fz_single": fz_single,
            "log_fz_single_vs_ref_fz": float(np.log(fz_single / ref_fz)),
            "log_fz_single_vs_ref_all": float(np.log(fz_single / ref_all)),
            "log_ref_fz_vs_ref_all": float(np.log(ref_fz / ref_all)),
        })
        print(f"S{subject:03d} done")

    def agg(key: str) -> dict:
        vals = np.array([r[key] for r in rows], dtype=float)
        n = len(vals)
        sem = vals.std(ddof=1) / np.sqrt(n)
        tcrit = float(_t.ppf(0.975, max(n - 1, 1)))
        return {"n": n, "mean": float(vals.mean()),
                "ci_low": float(vals.mean() - tcrit * sem),
                "ci_high": float(vals.mean() + tcrit * sem)}

    summary = {k: agg(k) for k in
               ["log_fz_single_vs_ref_fz", "log_fz_single_vs_ref_all",
                "log_ref_fz_vs_ref_all"]}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({"per_subject": rows, "summary": summary}, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
