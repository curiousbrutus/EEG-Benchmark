# P1 — Single-channel and low-cost EEG: what it can and cannot measure

**Status:** v4.2 (2026-11-06), APA-style author–year citations, BRM declarations and
Open Practices Statement added. Manuscript: `main.pdf` (19 pp).

**Links:** [GitHub](https://github.com/curiousbrutus/EEG-Benchmark) ·
[OSF project](https://osf.io/8wxqj/) (unregistered project, not a registration) ·
[Zenodo concept DOI](https://doi.org/10.5281/zenodo.23976431) (always latest version;
v4.1 version DOI: 10.5281/zenodo.24021733).

## What the paper does

Low-cost EEG headsets are used for claims about attention, relaxation and emotion, often
without enough information to judge whether a recording can support them. This project
builds a reproducible degradation benchmark from open multi-channel recordings: one
electrode, 128 Hz sampling, 1 µV quantisation, 1–40 Hz band-limiting, pink noise at
20/10/5/0 dB, synthetic blinks at 5/15/30 per minute, and a combined condition. Four
analysis families are tested: alpha reactivity, affective decoding, motor decoding
(exploratory) and reliability.

Main results:

- Alpha reactivity survives the acquisition chain at the same electrode (99.99%
  retained); electrode choice costs about 42% of eyes-closed alpha power; noise
  attenuates the effect monotonically.
- In the open affective dataset (18 high-end recordings, 12 Emotiv recordings), full
  montage valence/arousal/four-class accuracy is 0.69/0.68/0.58; with one electrode,
  valence is not detectable (0.52), arousal weakens (0.56) and four-class accuracy falls
  to 0.34. None of four midline sites rescues valence.
- A band control shows that part of the montage advantage is carried by beta-band
  features, possibly muscle activity.
- A 14-channel Emotiv performs similarly to the matched high-end montage, but a
  ±10-point equivalence test does not pass.
- Short-lag alpha stability is low; block-level alpha power is stable (ICC 0.92).
- The motor arm is invalid because its reference decoder does not exceed chance.

## Repository contents

| Path | Content |
| :--- | :--- |
| `main.tex`, `sections/` | manuscript source (single-column) |
| `main.pdf` | compiled manuscript |
| `main_twocol.tex`, `main_twocol.pdf`, `tables_twocol/` | optional full two-column layout variant |
| `tables/` | LaTeX tables generated from `results/*.json` |
| `figures/` | figures generated from `results/*.json` |
| `scripts/` | download, degradation, analysis and figure code |
| `results/*.json` | derived results behind every number reported |
| `CHECKLIST.md` | single-channel reporting checklist |
| `PREREGISTRATION.md` | pre-specified plan, unregistered; deviations log |
| `submission/` | cover letter, supplementary material, submission checklist |
| `CITATION.cff` | citation metadata |

Raw and derived data are **not** included. `scripts/00_download_zenodo.py` downloads the
affective archive; `scripts/01_download.py` downloads the EEGBCI files. Data are public
(PhysioNet; Zenodo CC BY 4.0).

## Reproduce

```bash
python scripts/00_download_zenodo.py
python scripts/01_download.py --subjects 109 --runs 1 2
python scripts/run_all.py --subjects 109
```

Environment: `requirements.txt` (pinned versions in `requirements.lock.txt`).

## Layout

The default is a single-column manuscript with a single-column abstract page. Set
`\twocolabstractfalse` in `main.tex` for the standard single-column abstract; set
`\twocolabstracttrue` for a two-column abstract cover page. The full two-column variant
is `main_twocol.tex` / `main_twocol.pdf`; it is a readability experiment and needs float
polishing before submission.

## Use of generative AI

Generative AI (DeepSeek Harness, DeepSeek model) was used for analysis-code development,
automation of the statistical pipeline, citation-metadata checking, simulated reviewer
feedback and language editing. All numerical results were verified against
`results/*.json`, all references were checked against DOI records, and the AI is not an
author. See the manuscript's "Use of generative AI" section.

## Citation

Please cite the concept DOI (all versions): **10.5281/zenodo.23976431**. The current
version is v4.1 (10.5281/zenodo.24021733); a v4.2 update will follow the final format
review.

## License

Code: MIT (`LICENSE`). Manuscript text and figures: please cite the paper.
