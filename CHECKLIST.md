# Single-channel EEG reporting checklist (v0.1)

A one-page checklist derived from COBIDAS MEEG (Pernet et al., 2020) and EEG-BIDS
(Pernet et al., 2019), restricted to what a single- or few-channel consumer recording
must report. It is a deliverable of this benchmark and is intended to be attached to
a manuscript as a supplementary table.

## Acquisition
- [ ] Device make/model and firmware version
- [ ] Electrode site(s), material, dry/saline/gel, and reference scheme
- [ ] Contact quality or impedance, and how it was checked
- [ ] Sampling rate, hardware filters, ADC resolution (bits or µV/bit)
- [ ] Session length, breaks, and any re-seating of electrodes

## Preprocessing (report software + version)
- [ ] Filter type/order/cut-offs (or "none") and whether zero-phase or causal
- [ ] Artifact handling: method, thresholds, rejected trial/epoch counts per subject
- [ ] Re-referencing (if any), and whether it is possible with the channel count
- [ ] Handling of missing/duplicated samples and clock drift

## Analyses
- [ ] Band definitions with justification; spectral method and parameters
- [ ] Exact definition of the outcome (e.g. ln(eyes-closed/eyes-open) alpha power)
- [ ] Absolute powers or model estimates, not only ratios
- [ ] Statistical model, effect sizes with CIs, multiplicity correction
- [ ] Number of trials/epochs per subject and per condition

## Validity and interpretation
- [ ] Which claims are supported by the acquisition (use a benchmark table if available)
- [ ] Explicit statement of what cannot be inferred (e.g. no source localisation, no EOG)
- [ ] Acknowledged confounds: EMG above ~20 Hz, blink leakage, motion, impedance drift
- [ ] Reliability reported: test–retest if available; otherwise a clearly labelled short-lag stability measure (not a reliability coefficient)
- [ ] Pre-registration link and deviations, or an explicit statement that the plan was
      planned but not registered

## Data and code
- [ ] Dataset identifiers and versions; file hashes where possible
- [ ] Analysis code repository, commit hash and licence
- [ ] Environment file with pinned versions
- [ ] Derived data and figure source data archived with a DOI
