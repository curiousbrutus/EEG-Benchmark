"""P1 — 00: download and extract the open affective dataset (Zenodo 14787743).

Requires `unrar` (or 7z) on PATH. Downloads the 1.06 GB archive, extracts the nested
RAR, and writes a small manifest of the recordings used.
"""
from __future__ import annotations
import hashlib, pathlib, shutil, subprocess, sys

URL = "https://zenodo.org/api/records/14787743/files/Comparativa%20EEG-BCI.rar/content"
OUT = pathlib.Path("data/raw/emotion_zenodo")
RAR = OUT / "dataset.rar"


def sha256(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for chunk in iter(lambda: f.read(1<<20), b''): h.update(chunk)
    return h.hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    if not RAR.exists():
        print("downloading", URL)
        subprocess.run(["curl","-L","--fail","-o",str(RAR),URL], check=True)
    extractor = shutil.which("unrar") or shutil.which("7z")
    if not extractor:
        sys.exit("install unrar or 7z")
    if extractor.endswith("unrar"):
        subprocess.run([extractor,"x","-o+",str(RAR)], cwd=OUT, check=True)
        nested = OUT/"Comparativa EEG-BCI"/"EEG-BCI.rar"
        if nested.exists():
            subprocess.run([extractor,"x","-o+",nested.name], cwd=nested.parent, check=True)
    else:
        subprocess.run([extractor,"x","-y",str(RAR),f"-o{OUT}"], check=True)
        nested = OUT/"Comparativa EEG-BCI"/"EEG-BCI.rar"
        if nested.exists():
            subprocess.run([extractor,"x","-y",nested.name], cwd=nested.parent, check=True)
    manifest={p.name: {"bytes":p.stat().st_size, "sha256":sha256(p)}
              for p in sorted((OUT/"Comparativa EEG-BCI"/"EEG"/"Experiment_files").glob("eegbci*.vhdr"))}
    (OUT/"manifest.json").write_text(__import__("json").dumps(manifest,indent=2))
    print("done:", len(manifest), "BrainVision recordings")

if __name__=="__main__": main()
