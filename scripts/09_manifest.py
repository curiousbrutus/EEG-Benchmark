"""P1 — 09: write a data manifest for the derived files and the environment.

Collects: dataset file hashes (from data/raw/eegbci/manifest.json if present),
derived-file counts, library versions, git commit if available.

Usage:
    python scripts/09_manifest.py
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import platform
import subprocess
import sys


def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def versions() -> dict:
    out = {"python": sys.version.split()[0], "platform": platform.platform()}
    for mod in ["numpy", "scipy", "sklearn", "mne", "matplotlib", "pandas"]:
        try:
            m = __import__(mod)
            out[mod] = getattr(m, "__version__", "unknown")
        except Exception:
            out[mod] = None
    return out


def git_commit() -> str | None:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"],
                                       text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return None


def main() -> None:
    root = pathlib.Path(".")
    manifest = {
        "git_commit": git_commit(),
        "environment": versions(),
        "datasets": {},
        "derived": {},
    }

    raw_manifest = root / "data/raw/eegbci/manifest.json"
    if raw_manifest.exists():
        manifest["datasets"]["eegbci"] = json.loads(raw_manifest.read_text())

    zen_manifest = root / "data/raw/emotion_zenodo/manifest.json"
    if zen_manifest.exists():
        manifest["datasets"]["affective_zenodo"] = json.loads(zen_manifest.read_text())

    results_dir = root / "results"
    if results_dir.exists():
        manifest["results"] = {p.name: {"bytes": p.stat().st_size, "sha256": sha256(p)}
                               for p in sorted(results_dir.glob("*.json"))}

    derived = sorted((root / "data/derived").glob("*.fif"))
    manifest["derived"]["n_files"] = len(derived)
    manifest["derived"]["total_bytes"] = sum(p.stat().st_size for p in derived)
    manifest["derived"]["sha256_sample"] = {
        p.name: sha256(p) for p in derived[:5]
    }

    # Results files that the manuscript numbers come from
    for name in ("summary.json", "sensitivity.json", "alpha_site_sensitivity.json"):
        p = root / "results" / name
        if p.exists():
            manifest.setdefault("results", {})[name] = sha256(p)

    out = root / "results/data_manifest.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=2))
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
