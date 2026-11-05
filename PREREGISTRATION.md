# PREREGISTRATION — P1 single-channel EEG benchmark

**Status:** pre-specified analysis plan, **not registered**. The project page is public
on OSF (https://osf.io/8wxqj/) as an **unregistered project**, not a registration; the
plan was drafted before the final analyses but no timestamped registration exists.
Only the "Deviations" section changed after drafting.

**Date drafted:** 2026-11-03
**Author:** Eyyüb Güven (Cyber Cognition Lab, pre-incorporation)

## 1. Research questions

- **RQ1:** Which standard EEG analyses retain their effect under single-channel
  consumer conditions?
- **RQ2:** What acquisition constraints (sampling rate, amplitude resolution,
  bandwidth, noise, blinks) drive the largest loss in each analysis?
- **RQ3:** What minimum trial count and reliability are needed for individual-level
  claims from a single channel?

## 2. Hypotheses (with predictions)

| # | Hypothesis | Directional prediction |
| :-- | :--- | :--- |
| **H1** | Alpha reactivity (eyes closed > eyes open) is robust to single-channel conditions. | Standardised effect retains ≥50% of the full-montage value after single-channel + 128 Hz + quantisation + band-limiting; degrades mainly with blink contamination. |
| **H2** | Single-trial motor-imagery decoding degrades non-monotonically. | Band-limiting and quantisation cost less accuracy than blink contamination at 15–30 blinks/min. |
| **H3** | Affective (valence/arousal) decoding is weaker and more fragile than motor decoding. | Balanced accuracy at the single-channel condition is lower than motor-imagery accuracy; drops below the 60% practical floor earlier in the degradation chain. |
| **H4** | Short-window band-power reliability is insufficient for momentary individual-level claims. | Split-half Spearman–Brown reliability of 2 s alpha windows below 0.75 at the best single-channel condition; block-level ICC reported separately. |
| **H5** | Band-ratio indices ("attention" proxies) are biased by blinks. | False-positive rate for the planned threshold exceeds 10% at ≥15 blinks/min. |

These are directional predictions; the benchmark reports effect sizes even where
predictions are not supported.

## 3. Data

- EEGBCI (PhysioNet, doi:10.13026/C28G6P): all 109 subjects, runs 1–2 (baselines),
  runs 4, 8 and 12 (motor imagery).
- DEAP (doi:10.1109/T-AFFC.2011.15): all 40 subjects, preprocessed version.
- Fixed versions: record dataset download date and file hashes in
  `results/data_manifest.json`.

**No new participants; no personal data.** Secondary analysis of public,
de-identified data.

## 4. Degradation conditions (fixed before analysis)

Reference (all channels, 160 Hz, no added noise) and seven cumulative conditions:
(1) Fz single channel; (2) 128 Hz; (3) 1 µV quantisation; (4) 1–40 Hz band-limit;
(5) + pink noise at 20/10/5/0 dB; (6) + blinks at 5/15/30 per min.
Sensitivity: Fp1 and Cz instead of Fz. Random seed: 20261103.

## 5. Primary and secondary outcomes

| Outcome | Definition | Analysis |
| :--- | :--- | :--- |
| Alpha reactivity | Standardised eyes-closed − eyes-open difference in 8–12 Hz power (Welch, 2 s, 50% overlap) | Linear mixed model, subject random intercept |
| Motor decoding | Within-subject balanced accuracy, 5-fold stratified CV, LDA on log band power | Same model on accuracy |
| Affective decoding | Within-subject balanced accuracy + AUC, median split per subject | Same model |
| Reliability | Split-half reliability (odd/even 2 s windows) of alpha power in the eyes-closed run; Spearman–Brown corrected | Bootstrap 95% CI |
| Blink bias | Relative bias in alpha/theta and theta/beta; false-positive rate | Descriptive + mixed model |

## 6. Decision rules (planned)

A claim is **supported** if (a) the degraded effect is ≥50% of the full-montage
standardised effect **and** (b) its 95% CI excludes zero. **Partially supported** if
the direction holds but the CI includes zero. **Not supported** otherwise.
For decoding, the practical floor is defined as the lower bound of the 95% CI being
above 60% balanced accuracy.

Multiple comparisons across the two primary families (alpha condition grid; affective contrasts) use Benjamini–Hochberg FDR, q = 0.05. The post-hoc site sweep is exploratory and is reported with BH-adjusted q values but does not enter the primary family.

## 7. Exclusion rules

- Subjects with missing runs or corrupted files are excluded and counted; reason logged.
- No trial-level outlier removal beyond the planned artifact procedure
  (amplitude threshold in the single-channel condition; Autoreject in the reference).
- No post-hoc addition of analyses without a deviation entry.

## 8. Deviations log

| Date | Planned | Actual | Reason |
| :--- | :--- | :--- | :--- |
| 2026-11-05 | 60% balanced-accuracy floor as the primary decoding rule | Floor retained and fully reported, but the verdict rules use CI-vs-chance; the floor is summarised separately as a stricter auxiliary criterion | Binomial and four-class accuracies are not commensurate on one floor; demotion is recorded here and the raw floor results are reported in the decision matrix. |
| 2026-11-03 | H1: blinks would drive much of the apparent degradation | Blinks had a negligible effect in the additive model; noise and electrode site dominated | The model is spectrally orthogonal to alpha and symmetric across conditions; this is reported as a reverse of the original expectation. |
| 2026-11-03 | Primary retention at the scalp-average reference | Same-site (Fz vs Fz) promoted to primary; scalp-average reported as naive comparison | Site-matching removes the electrode-site confound identified in round 2. |
| 2026-11-03 | 50% retention rule with a difference test | Rule kept, but operationalised as geometric retention + CI, with a separate band/EMG decomposition and TOST for device equivalence | Reviewers showed the difference test is not a non-inferiority test. |
| 2026-11-03 | Standardised effect sizes + LMM; Fp1/Cz sensitivity; AUC/median split; Autoreject | Log-ratio t-CIs + BH; site sweep run for affective arm; quadrant labels used without AUC; no Autoreject | Round-2 audit; deviations are reported rather than hidden. |
| 2026-11-03 | Full 109-subject EEGBCI sample | Full 109 used in the final analysis; an interim 30-subject subset was used during drafting | Compute limits during drafting; the final version reports all 109. |
| 2026-11-03 | DEAP affective decoding (H3) | Replaced by open Zenodo 14787743; BrainVision high-end (N=18) and Emotiv (N=12) arms analysed | DEAP page unreachable; DREAMER access-restricted; the replacement dataset is open (CC BY 4.0) and includes labelled IAPS trials. |
| 2026-11-03 | H2 motor decoding with an adequate reference | Exploratory only, N=10, reported inconclusive | Only 10 subjects had imagery runs degraded in this pass; the reference decoder did not clear chance. |
| 2026-11-03 | Test-retest ICC(2,1) across sessions | Short-lag stability (N=109) plus block ICC across three repeated runs (N=10); neither is a cross-session reliability coefficient | Neither dataset contains repeated sessions; both estimates are reported with their timescales. |
| 2026-11-03 | Multiplicity correction (BH-FDR) | Applied within the alpha and affective families in v2.0 (`scripts/27_stats.py`); early drafts had not applied it | Round-2 audit. |
| 2026-11-03 | ICC(2,1) across repeated runs for reliability | Split-half reliability (odd/even 2 s windows) + Spearman–Brown | EEGBCI provides one eyes-open and one eyes-closed run per subject; a test–retest ICC is not identifiable. Change made before registration. |
| 2026-11-03 | DEAP affective decoding in the first analysis round | DEAP loader implemented (`scripts/06_deap.py`), not run | DEAP requires accepting a data-use agreement; access pending. EEGBCI results reported, H3 marked untested. |

## 9. Registration checklist

- [ ] OSF project created; this file uploaded with a timestamp
- [ ] Analysis scripts committed **before** first primary analysis (`git tag prereg-v1`)
- [ ] Deviations log maintained from the first deviation onward
- [ ] Link added to `README.md` and the manuscript
