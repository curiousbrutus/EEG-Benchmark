"""P1 — 01: download the public datasets and flatten the file names.

EEGBCI is downloaded through MNE-Python and copied to a flat directory
(`S001R01.edf`) so the rest of the pipeline is simple. DEAP cannot be
downloaded automatically: request access at
https://www.eecs.qmul.ac.uk/mmv/datasets/deap/ and place the files under
data/raw/deap/.

Runs downloaded: 1-2 (eyes open/closed) and 4, 8, 12 (imagined left/right hand).

Usage:
    python scripts/01_download.py --subjects 5
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import shutil


def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--subjects", type=int, default=5,
                        help="number of EEGBCI subjects (1..109); 5 for the smoke test")
    parser.add_argument("--out", type=pathlib.Path, default=pathlib.Path("data/raw/eegbci"))
    parser.add_argument("--runs", type=int, nargs="+", default=[1, 2, 4, 8, 12])
    args = parser.parse_args()

    try:
        from mne.datasets import eegbci
    except ImportError as exc:  # pragma: no cover
        raise SystemExit("mne is required: pip install mne") from exc

    args.out.mkdir(parents=True, exist_ok=True)
    subjects = list(range(1, args.subjects + 1))
    runs = args.runs

    manifest: dict[str, dict] = {}
    print(f"Downloading EEGBCI runs {runs} for subjects {subjects[0]}..{subjects[-1]}")
    for subj in subjects:
        files = eegbci.load_data(subj, runs, path=str(args.out),
                                 update_path=False, verbose="ERROR")
        for src in files:
            src = pathlib.Path(src)
            dst = args.out / src.name
            if not dst.exists():
                shutil.copy2(src, dst)
            manifest[dst.name] = {"bytes": dst.stat().st_size, "sha256": sha256(dst)}
        print(f"  subject {subj:03d}: {len(files)} files")

    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True))
    print(f"\nEEGBCI done: {len(manifest)} files in {args.out}")
    print("DEAP: place 'data_preprocessed_python' / 'data_original' under "
          "data/raw/deap/ after accepting the data-use agreement.")


if __name__ == "__main__":
    main()
