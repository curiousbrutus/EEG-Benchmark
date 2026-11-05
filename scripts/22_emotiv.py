"""P1 — 22: affective decoding from the low-cost Emotiv arm (Zenodo 14787743).

Aligns Emotiv CSV recordings to the experiment logs using absolute timestamps:
    trial_onset = SessionStartDateTimeUtc + ImageX.OnsetTime (ms)
The CSV TIME column is parsed as local wall-clock time. For each subject, the log
session whose absolute trial times fall inside the CSV time span is selected; trials
are epoched 0-2.5 s at 128 Hz and the same band-power + LDA pipeline as the high-end
arm is applied. Output: results/emotiv.json
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re

import numpy as np
from scipy.stats import t as _t
import pandas as pd
from scipy.signal import welch

BANDS = {(4, 8): "theta", (8, 12): "alpha", (13, 30): "beta"}
PROC2Q = {"AltaAlto": "HVHA", "BajoAlto": "LVHA", "AltaBajo": "HVLA", "BajaBajo": "LVLA"}
ROOT = pathlib.Path("data/raw/emotion_zenodo/Comparativa EEG-BCI")
SEED = 20261103


def parse_log(path: pathlib.Path):
    raw = path.read_bytes()
    txt = raw.decode("utf-16", errors="replace")
    # session start (UTC) and per-trial onsets
    m = re.search(r"SessionStartDateTimeUtc:\s*(\d+)/(\d+)/(\d+) (\d+):(\d+):(\d+)", txt)
    if not m:
        return None
    d, mo, y, hh, mm, ss = map(int, m.groups())
    start = pd.Timestamp(year=y, month=mo, day=d, hour=hh, minute=mm, second=ss)
    trials = []
    for fr in re.split(r"\*\*\* LogFrame Start \*\*\*", txt)[1:]:
        fr = fr.split("*** LogFrame End ***")[0]
        proc = re.search(r"Procedure:\s*(\w+)", fr)
        onset = re.search(r"Image\w*\.OnsetTime:\s*(\d+)", fr)
        if proc and onset and proc.group(1) in PROC2Q:
            trials.append((PROC2Q[proc.group(1)], start + pd.Timedelta(milliseconds=int(onset.group(1)))))
    return trials if trials else None


def load_csv(path: pathlib.Path):
    lines = path.read_text(errors="replace").splitlines()
    if not lines:
        return None
    header = [c.strip().strip("'\" ") for c in lines[0].strip().strip("[]").split(",")]
    if "TIME" not in header:
        return None
    rows = [ln for ln in lines[1:] if ln.strip()]
    times, data = [], []
    for ln in rows:
        parts = [x.strip() for x in ln.split(",")]
        if len(parts) < 15:
            continue
        try:
            data.append([float(x) for x in parts[1:15]])
            times.append(parts[0])
        except ValueError:
            continue
    if not data:
        return None
    t = pd.Series(pd.to_datetime(times, format="%Y-%m-%d %H:%M:%S.%f", errors="coerce"))
    X = np.asarray(data, dtype=float)
    eeg = header[1:15]
    ok = t.notna()
    return t[ok].reset_index(drop=True), X[ok.values], eeg


def epoch_features(X: np.ndarray, fs: float) -> np.ndarray:
    feats = []
    for ep in X:
        f, p = welch(ep, fs=fs, nperseg=min(int(2*fs), ep.shape[-1]),
                     noverlap=min(int(fs), ep.shape[-1]//2), axis=-1)
        row = []
        for lo, hi in BANDS:
            mask = (f >= lo) & (f <= hi)
            row.append(np.log(np.mean(p[..., mask], axis=-1) + 1e-12))
        feats.append(np.concatenate(row))
    return np.vstack(feats)


def decode(X, y):
    from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
    from sklearn.model_selection import StratifiedKFold, cross_val_score
    classes, counts = np.unique(y, return_counts=True)
    if len(classes) < 2 or counts.min() < 3:
        return None
    clf = LinearDiscriminantAnalysis(solver="lsqr", shrinkage="auto")
    cv = StratifiedKFold(n_splits=min(5, int(counts.min())), shuffle=True, random_state=SEED)
    return float(cross_val_score(clf, X, y, cv=cv, scoring="balanced_accuracy").mean())


def analyse(subject: int):
    csv_path = ROOT / "BCI" / f"sujeto{subject}.csv"
    if not csv_path.exists() or csv_path.stat().st_size < 10000:
        return None
    loaded = load_csv(csv_path)
    if loaded is None:
        return None
    times, X_raw, eeg = loaded
    span0, span1 = times.min(), times.max()
    # candidate logs for this subject
    logs = list((ROOT / "tarea EEG-BCI" / "Tarea emociones").glob(f"*/*-{subject}-*.txt"))
    # The log timestamps are UTC; the CSV wall clock is local. Try offsets and pick
    # the one that places the most trials inside the recording span.
    best = None
    for lp in logs:
        trials = parse_log(lp)
        if not trials:
            continue
        for off_h in (0, 1, -1, 2, -2):
            shift = pd.Timedelta(hours=off_h)
            shifted = [(q, t + shift) for q, t in trials]
            inside = [t for _, t in shifted if span0 - pd.Timedelta(seconds=5) <= t <= span1 + pd.Timedelta(seconds=5)]
            score = len(inside)
            if score >= 20:
                cand = (score, lp, shifted)
                if best is None or score > best[0]:
                    best = cand
    if best is None:
        return None
    _, lp, trials = best
    # epoch extraction
    fs = 128.0
    offs = np.searchsorted(times.values, np.array([t.to_datetime64() for _, t in trials]))
    epochs, labels = [], []
    for (quad, t), idx in zip(trials, offs):
        if idx >= len(times) - 1:
            continue
        gap = abs((times.iloc[idx] - t).total_seconds())
        start = idx - int(0.2 * fs)
        stop = idx + int(2.3 * fs)
        if gap > 1.0 or start < 0 or stop >= len(X_raw):
            continue
        ep = X_raw[start:stop].T  # channels x time
        epochs.append(ep); labels.append(quad)
    if len(epochs) < 20:
        return None
    gaps = []
    for (quad, t), idx in zip(trials, offs):
        if idx < len(times):
            gaps.append(abs((times.iloc[idx] - t).total_seconds()))
    F = epoch_features(np.array(epochs), fs)
    y = np.array(labels)
    out = {"subject": subject, "log": lp.name, "n_trials": len(labels),
           "alignment_median_ms": float(np.median(gaps) * 1000) if gaps else None,
           "alignment_p95_ms": float(np.percentile(gaps, 95) * 1000) if gaps else None,
           "alignment_max_ms": float(np.max(gaps) * 1000) if gaps else None,
           "alignment_rejection_seconds": 1.0,
           "n_neutral_ignored": 0, "targets": {}}
    out["targets"]["quadrant"] = decode(F, y)
    for name, pos in (("valence", {"HVHA","HVLA"}), ("arousal", {"HVHA","LVHA"})):
        yy = np.isin(y, list(pos)).astype(int)
        out["targets"][name] = decode(F, yy)
    return out


def mean_ci(vals):
    vals = [v for v in vals if v is not None and not np.isnan(v)]
    if not vals: return {"n": 0, "mean": None}
    a = np.asarray(vals, float); n = len(a)
    sem = a.std(ddof=1)/np.sqrt(n) if n > 1 else 0.0
    t = float(_t.ppf(0.975, max(n - 1, 1)))
    return {"n": n, "mean": float(a.mean()), "ci_low": float(a.mean()-t*sem), "ci_high": float(a.mean()+t*sem)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--subjects", type=int, nargs="+", default=list(range(1, 21)))
    ap.add_argument("--out", type=pathlib.Path, default=pathlib.Path("results/emotiv.json"))
    args = ap.parse_args()
    rows = []
    for s in args.subjects:
        try:
            r = analyse(s)
        except Exception as exc:
            print(f"FAIL {s}: {exc}"); continue
        if r:
            rows.append(r); print(f"sujeto{s}: trials={r['n_trials']} quad={r['targets']['quadrant']}")
    summary = {k: mean_ci([r["targets"][k] for r in rows]) for k in ["quadrant","valence","arousal"]}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({"n_subjects": len(rows), "recordings": rows, "summary": summary}, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
