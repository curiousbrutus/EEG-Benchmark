# Cover letter — submission to *Behavior Research Methods*

Dear Editors,

We submit the manuscript **"What Single-Channel and Low-Cost EEG Can and Cannot Measure: A
Reproducible Degradation Benchmark and Reporting Protocol"** for consideration as a
methods/reproducibility article in *Behavior Research Methods*.

**What the paper does.** Low-cost EEG headsets are used to make claims about attention,
relaxation and emotion, but the field lacks a reference for which analyses survive
reduced acquisition. We introduce a reproducible degradation benchmark that turns open
multi-channel recordings into explicit single-channel consumer conditions (one
electrode, 128 Hz, 1 µV quantisation, 1–40 Hz band-limiting, pink noise at four levels,
synthetic blinks at three rates) and measures which standard analyses survive.

**The main findings are conditional and practical.** Using all 109 subjects of the open
EEGBCI dataset, alpha reactivity survived the acquisition chain almost intact once the
reference was taken at the same electrode (99.99% retained), while the electrode-site
choice cost about 42% of eyes-closed alpha power and noise reduced the effect
monotonically (to about 0.59 of the reference at 0 dB). Using an open low-cost-versus-high-end
affective dataset, valence was decodable from a full montage (0.69) but was not
detected from a single electrode (0.52); arousal survived weakly (0.56 vs 0.68). A low-cost
14-channel headset performed at a similar level to the high-end montage without passing
a formal equivalence test. A decomposition showed that the acquisition chain was
harmless, that valence was not distinguishable from chance at any single site and the
four-class result stayed far below the montage, and that beta-band
features carry part of the full-montage advantage — a caution against reading the
montage result as purely cortical. The paper also contributes a single-channel reporting
checklist and an open, seeded analysis pipeline with the JSON files behind every
number.

**Fit with BRM.** The contribution is methodological and reproducibility-oriented: a
benchmark, a decision matrix for claim-level verdicts, a checklist derived from COBIDAS
MEEG and EEG-BIDS, and a fully released analysis. It does not make clinical, safety or
device-validation claims.

**Transparency.** The analysis plan was pre-specified but not registered; the deviations and null results
(including two untested arms and an underpowered exploratory decoding arm) are reported
explicitly. Data are public (PhysioNet; Zenodo CC BY 4.0). Code and derived results are
available at https://github.com/curiousbrutus/EEG-Benchmark and on the OSF project
https://osf.io/8wxqj/. A Zenodo archive DOI will be assigned on acceptance. The
repository state used for the submission is identified by a commit hash in the data
manifest.

We confirm this work is not under consideration elsewhere, has no competing interests,
and involved no new human participants.

Sincerely,
Eyyüb Güven
Cyber Cognition Lab (pre-incorporation), Çorlu, Türkiye
eyyub.gvn@gmail.com · ORCID 0009-0005-6017-8622
