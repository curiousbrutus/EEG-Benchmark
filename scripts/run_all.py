"""P1 — run_all: end-to-end reproduction driver.

Runs download → degrade → analyze → aggregate → sensitivity → ICC → paired →
manifest → figures, over a declared subject/run list, writing a timestamped log.

Usage:
    python scripts/run_all.py --subjects 10            # full pilot run
    python scripts/run_all.py --subjects 2 --quick     # smoke test
"""
from __future__ import annotations

import argparse
import pathlib
import subprocess
import sys
import time

RUNS = [1, 2, 4, 8, 12]


def run(cmd: list[str], log: pathlib.Path) -> None:
    print("$", " ".join(cmd))
    with log.open("a") as fh:
        fh.write("$ " + " ".join(cmd) + "\n")
        result = subprocess.run(cmd, stdout=fh, stderr=subprocess.STDOUT)
    if result.returncode != 0:
        raise SystemExit(f"FAILED: {' '.join(cmd)}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--subjects", type=int, default=10)
    ap.add_argument("--quick", action="store_true", help="smoke test: 2 subjects, 1 run")
    args = ap.parse_args()

    n = 2 if args.quick else args.subjects
    runs = [1] if args.quick else RUNS
    log = pathlib.Path("results/reproduction_log.txt")
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(f"# reproduction run {time.strftime('%Y-%m-%dT%H:%M:%S')}\n")

    py = sys.executable
    run([py, "scripts/01_download.py", "--subjects", str(n)], log)
    for s in range(1, n + 1):
        for r in runs:
            run([py, "scripts/02_degrade.py", "--subject", str(s), "--run", str(r)], log)
        run([py, "scripts/03_analyze.py", "--subject", str(s)], log)
    subjects = " ".join(str(i) for i in range(1, n + 1))
    for cmd in ("05_aggregate.py", "07_sensitivity.py", "10_icc.py", "11_paired.py"):
        run([py, f"scripts/{cmd}"], log)
    run([py, "scripts/08_alpha_sensitivity.py", "--subjects", *subjects.split()], log)
    run([py, "scripts/26_site_metrics.py"], log)
    run([py, "scripts/27_stats.py"], log)
    run([py, "scripts/12_fig1_pipeline.py"], log)
    run([py, "scripts/04_figures.py"], log)
    # affective arms (require the Zenodo archive; see scripts/00_download_zenodo.py)
    for cmd in ("20_affective.py", "22_emotiv.py", "23_device_compare.py",
                "24_affective_decomp.py", "13_csp.py", "28_make_tables.py",
                "21_fig_affective.py", "29_fig_decomp.py"):
        run([py, f"scripts/{cmd}"], log)
    run([py, "scripts/09_manifest.py"], log)
    print(f"done; log: {log}")


if __name__ == "__main__":
    main()
