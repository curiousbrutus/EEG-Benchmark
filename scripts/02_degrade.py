"""P1 — 02: degrade a multi-channel recording to single-channel conditions.

Conditions (the grid the manuscript describes):
    ref                     full montage, original sampling
    fz                      single channel only
    fz_128                  + 128 Hz
    fz_128_quant            + 1 uV quantisation
    fz_128_quant_band       + 1-40 Hz band-limit
    fz_noise{20,10,5,0}     + pink noise at 20/10/5/0 dB (no blinks)
    fz_blink{5,15,30}       + synthetic blinks at 5/15/30 per min (no noise)
    fz_combined             + 0 dB noise + 30 blinks/min

Each arm is separate so a dose-response can be estimated and so the noise and
blink effects are not confounded.

Usage:
    python scripts/02_degrade.py --subject 1 --run 1
"""
from __future__ import annotations

import argparse
import json
import pathlib

import numpy as np

SEED = 20261103
CHAIN = ["fz", "fz_128", "fz_128_quant", "fz_128_quant_band"]
NOISE_LEVELS = [20, 10, 5, 0]
BLINK_RATES = [5, 15, 30]
CONDITIONS = (
    ["ref"] + CHAIN
    + [f"fz_noise{snr}" for snr in NOISE_LEVELS]
    + [f"fz_blink{rate}" for rate in BLINK_RATES]
    + ["fz_combined"]
)


def quantize(data: np.ndarray, step: float = 1e-6) -> np.ndarray:
    return np.round(data / step) * step


def pink_noise(n: int, rng: np.random.Generator) -> np.ndarray:
    white = rng.standard_normal(n)
    freqs = np.fft.rfftfreq(n)
    freqs[0] = freqs[1]
    shaped = np.fft.rfft(white) / np.sqrt(freqs)
    noise = np.fft.irfft(shaped, n)
    return (noise - noise.mean()) / (noise.std() + 1e-12)


def add_noise(data: np.ndarray, snr_db: float, rng: np.random.Generator) -> np.ndarray:
    noise = pink_noise(data.shape[-1], rng)
    signal_var = float(np.var(data))
    noise *= np.sqrt(signal_var / (10 ** (snr_db / 10.0)))
    return data + noise[None, :]


def inject_blinks(data: np.ndarray, fs: float, rate_per_min: float,
                  rng: np.random.Generator, duration_s: float = 0.35) -> np.ndarray:
    n_times = data.shape[-1]
    out = data.copy()
    if rate_per_min <= 0 or n_times < int(duration_s * fs) * 2:
        return out
    n_blinks = int(round(rate_per_min * (n_times / fs / 60.0)))
    t = np.arange(int(duration_s * fs)) / fs
    template = np.hanning(t.size) * np.sin(2 * np.pi * 2.0 * t)
    scale = 4.0 * float(np.std(data)) if np.std(data) > 0 else 1.0
    for _ in range(n_blinks):
        start = int(rng.integers(0, max(1, n_times - template.size)))
        out[0, start:start + template.size] += scale * template
    return out


def find_edf(data_dir: pathlib.Path, subject: int, run: int) -> pathlib.Path:
    name = f"S{subject:03d}R{run:02d}.edf"
    flat = data_dir / name
    if flat.exists():
        return flat
    matches = list(data_dir.rglob(name))
    if not matches:
        raise FileNotFoundError(f"{name} not found under {data_dir}; run 01_download.py")
    return matches[0]


def pick_single_channel(raw):
    """Pick Fz, tolerating punctuation in channel names (EEGBCI: 'Fz.')."""
    canon = lambda s: "".join(ch for ch in s if ch.isalnum()).lower()  # noqa: E731
    lookup = {canon(c): c for c in raw.ch_names}
    return lookup.get("fz", raw.ch_names[0])


def degrade_raw(raw, condition: str, rng: np.random.Generator):
    import mne

    raw = raw.copy().load_data()
    if condition == "ref":
        return raw

    # 1) single channel
    raw.pick([pick_single_channel(raw)])

    # 2) resample (all except the plain single-channel arm)
    if condition != "fz":
        raw.resample(128, verbose="ERROR")

    # 3) quantisation (from fz_128_quant onward, including all noise/blink arms)
    if condition not in {"fz", "fz_128"}:
        raw._data = quantize(raw.get_data())

    # 4) band-limit (from fz_128_quant_band onward)
    if condition not in {"fz", "fz_128", "fz_128_quant"}:
        raw.filter(1.0, 40.0, method="fir", verbose="ERROR")

    # 5) noise arm or combined
    if condition.startswith("fz_noise"):
        snr = float(condition.replace("fz_noise", ""))
        raw._data = add_noise(raw.get_data(), snr, rng)
    elif condition == "fz_combined":
        raw._data = add_noise(raw.get_data(), 0.0, rng)

    # 6) blink arm or combined
    if condition.startswith("fz_blink"):
        rate = float(condition.replace("fz_blink", ""))
        raw._data = inject_blinks(raw.get_data(), raw.info["sfreq"], rate, rng)
    elif condition == "fz_combined":
        raw._data = inject_blinks(raw.get_data(), raw.info["sfreq"], 30.0, rng)
    return raw


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--subject", type=int, default=1)
    parser.add_argument("--run", type=int, default=1)
    parser.add_argument("--data-dir", type=pathlib.Path,
                        default=pathlib.Path("data/raw/eegbci"))
    parser.add_argument("--out", type=pathlib.Path, default=pathlib.Path("data/derived"))
    args = parser.parse_args()

    import mne

    path = find_edf(args.data_dir, args.subject, args.run)
    raw = mne.io.read_raw_edf(path, preload=True, verbose="ERROR")

    rng = np.random.default_rng(SEED + args.subject * 100 + args.run)
    args.out.mkdir(parents=True, exist_ok=True)
    metadata = {"subject": args.subject, "run": args.run, "seed": SEED,
                "source": str(path), "noise_snr_db": NOISE_LEVELS,
                "blink_rates_per_min": BLINK_RATES,
                "single_channel": pick_single_channel(raw), "conditions": {}}

    for condition in CONDITIONS:
        degraded = degrade_raw(raw, condition, rng)
        out = args.out / f"S{args.subject:03d}R{args.run:02d}_{condition}.fif"
        degraded.save(out, overwrite=True, verbose="ERROR")
        metadata["conditions"][condition] = {
            "n_channels": len(degraded.ch_names),
            "sfreq": float(degraded.info["sfreq"]),
            "duration_s": float(degraded.times[-1]),
        }
        print(f"{condition:22s} ch={len(degraded.ch_names):2d} "
              f"fs={degraded.info['sfreq']:.0f} -> {out.name}")

    (args.out / f"S{args.subject:03d}R{args.run:02d}_meta.json").write_text(
        json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
