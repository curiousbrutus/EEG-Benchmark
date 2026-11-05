# Supplementary material

## S1. Condition grid and JSON evidence
| Analysis | File |
| :--- | :--- |
| Alpha reactivity, N=109 (all conditions, means and CIs) | `results/summary.json` |
| Paired contrasts vs reference | `results/paired.json` |
| Site-matched alpha sensitivity (N=109) | `results/alpha_site_sensitivity.json` |
| Reliability (short-lag stability N=109; block ICC N=10) | `results/summary.json`, `results/icc.json` |
| Exploratory motor decoding and CSP | `results/summary.json`, `results/csp.json` |
| Affective decoding (high-end, Emotiv, single-channel) | `results/affective.json`, `results/emotiv.json` |
| Decomposition and site sweep | `results/affective_decomp.json` |
| Paired contrasts, BH-FDR, TOST | `results/inference.json` |
| Within-subject device comparison (12 matched subjects) | `results/device_compare.json` |
| Data manifest (hashes, versions, commit) | `results/data_manifest.json` |

## S2. Analysis pipeline
`scripts/run_all.py` reproduces the alpha/reliability arms; `scripts/20_affective.py`,
`22_emotiv.py`, `23_device_compare.py` reproduce the affective arms. Seeds are fixed in
each script; the environment is pinned in `requirements.lock.txt`.

## S3. Single-channel reporting checklist
`CHECKLIST.md` (also proposed as a supplementary table).

## S4. Deviations from the pre-specified plan
`PREREGISTRATION.md`, Deviations log: interim 30-subject subset during drafting (final uses all 109); affective dataset replacement;
exploratory motor arm; no test–retest ICC; BH-FDR applied in v2.0.

## S5. Auxiliary 60% threshold and retention bounds
Using the lower 95% bound of balanced accuracy against the pre-specified 60% practical
floor: full-montage valence passes (0.62), full-montage four-class fails (0.49), single
sites fail, Emotiv valence fails (0.57) and Emotiv arousal passes (0.63), high-end
arousal passes (0.60). Retention lower bounds for the alpha grid: chain 0.999; 20 dB
0.78; 10 dB 0.73; 5 dB 0.64; 0 dB 0.45; blinks 0.78 (model check).
