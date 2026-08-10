# SEIZURE DATA DIVE — real-data reach of the glass-box model's predictions

Scoping (and piloting where feasible) real-data tests of the predictions in
`SEIZURE_SCIENCE.md`, produced by the landed default-off engine seizure
capability (`seeds/seizure_dynamics.json`). **Read-only w.r.t. the engine; no
timing claims.** This document maps each prediction to the recording that would
test it, catalogs open datasets, confronts the observation-model problem
honestly, and reports a pilot attempt on the strongest temporal prediction (P1).

**Source paper.** PMC5550430 is **Rossi, Wykes, Kullmann & Carandini,
"Focal cortical seizures start as standing waves and propagate respecting
homotopy in the connectome"** ([PMC5550430](https://pmc.ncbi.nlm.nih.gov/articles/PMC5550430/)),
widefield calcium imaging of awake mouse cortex. (An earlier note in the memory
line tied this PMC id to "Wenzel/Yuste" — that is corrected here; the
Wenzel/Yuste papers are a *separate* calcium-imaging line, [PMC5551439](https://pmc.ncbi.nlm.nih.gov/articles/PMC5551439/)
and [J Neurosci 2019](https://www.jneurosci.org/content/39/43/8562).)

---

## THREAD 1 — Prediction → data mapping

What recording would actually test each prediction. Key axis: **P1 and P3 are
TEMPORAL** (they read a within-event time course and may NOT need spatial
resolution); **P2 needs a closed-loop stimulation-dose protocol**; **P4/P5 are
already declared model limits needing heterogeneous/hub structure** and are not
pursued as near-term real-data tests.

### P1 (headline) — decay-rate separator of persist vs die
- **What the recording must contain:** onset events of BOTH classes — events
  that PROGRESS to a seizure (persist) and events that ABORT (die: interictal
  events / interictal epileptiform discharges), each with a **time-resolved
  amplitude/activity trace through the ~300 ms onset/standing window** and a
  **persist/die outcome label**.
- **Modality:** the paper's own **widefield calcium imaging** is ideal (it is
  where "standing wave" is defined and where both classes are visible). Also
  testable on **intracranial LFP/microelectrode** (ictal discharges vs
  interictal discharges) and, as a weak proxy, **scalp EEG** (seizure onsets vs
  interictal transients).
- **Spatial resolution: NOT required for the core test.** P1 is a claim about a
  **temporal readout** (the decay rate of the residual amplitude), explicitly
  *independent of the spatial profile* (the model shows rank-1 morphology is
  flat across the fold). A single well-placed channel / ROI time series with the
  right temporal resolution suffices for the decay-rate contrast. Spatial data
  is needed only to *also* confirm the "morphology does not discriminate" half.
- **Temporal resolution IS the binding requirement:** to resolve a decay slope
  in a ~300 ms window you want ≥ ~100 Hz (LFP/EEG easily; calcium imaging frame
  rate ~50–150 Hz is marginal but was enough for the paper).
- **The discriminating design:** within one recording, both persist and die
  onsets, so the pre-transition decay rate can be compared *at matched onset
  morphology*. This is exactly the contrast Rossi's dataset was built for.

### P2 (strongest clinical) — hysteresis: abort-dose > onset-dose
- **What the recording must contain:** **closed-loop stimulation with recorded
  stimulation parameters (dose)**, delivering interventions BOTH to prevent
  onset (sub-clinical/interictal) and to terminate established seizures, so the
  minimal effective dose can be compared between the two regimes.
- **Modality:** responsive neurostimulation (RNS / coordinated-reset) intracranial
  systems; or an animal closed-loop desync preparation.
- **Spatial resolution:** secondary; the primary variables are **stimulation
  amplitude/dose** and **event state** (resting vs established).
- **This is a bespoke closed-loop protocol, not an observational dataset.** No
  open dataset carries per-event stimulation dose (see Thread 2, Q2). Testing P2
  requires either a device-maker collaboration (NeuroPace RNS logs are
  proprietary) or a purpose-built animal/closed-loop experiment.

### P3 (desync aborts anytime; magnitude not timing)
- **What the recording must contain:** established seizures with **desynchronizing
  interventions applied at varied latencies AND varied strengths**, and the
  abort/no-abort outcome. Overlaps P2's apparatus (closed-loop stim) plus a
  latency sweep.
- **Modality/resolution:** as P2. Temporal (when) × magnitude (how strong) design.
- **Reach:** bespoke closed-loop, like P2. Partially corroborated already by the
  coordinated-reset / RNS literature (see `SEIZURE_SCIENCE.md` Thread 2, P3).

### P4 / P5 (declared model limits)
- P4 (more coupling protective — wrong sign) and P5 (no onset-locus effect) are
  reported in `SEIZURE_SCIENCE.md` as **structural limits of the homogeneous
  lattice**, not neural predictions. Testing them is not a data problem but a
  *model* problem (needs a degree-heterogeneous / recruitment-biased-coupling
  lattice). Out of scope for a real-data dive; noted for completeness.

**Summary of the mapping.** Only **P1 is near-term testable on observational
open data** (it needs only both-class onset events with a time-resolved trace —
no spatial resolution, no intervention). **P2 and P3 require closed-loop
stimulation-dose data that is not openly available** — they are bespoke-recording
projects. P4/P5 are model extensions, not data tests.

---

## THREAD 2 — Open-dataset catalog

Assessed for: which prediction it could test, resolution/labels, and
accessibility. (Compiled from a cited search; uncertainties flagged, not
fabricated.)

### Scalp EEG

**CHB-MIT Scalp EEG** — [PhysioNet](https://physionet.org/content/chbmit/1.0.0/)
- Pediatric scalp EEG, 22 subjects/23 cases, **198 seizures**, 256 Hz, ~22–23
  bipolar channels. Seizure **onset/offset annotated**; abundant interictal
  recording, but **only clinical seizures are marked — NO IED/spike or aborted-
  onset annotations.**
- **Tests:** P1 only as a **weak proxy** (persist = seizure onsets; die must be
  *self-detected* interictal transients, since none are labeled). Cannot test
  P2/P3 (no stimulation).
- **Accessibility: OPEN, no application** (direct anonymous download). Most
  accessible option for a quick pilot.

**TUH EEG Corpus / TUSZ** — [NEDC/Temple](https://isip.piconepress.com/projects/nedc/html/tuh_eeg/)
- Clinical scalp EEG; TUSZ ≈ 613 patients / ~2,981 seizure events (counts vary
  by version — approximate), ≥250 Hz, expert onset/offset + type. The sibling
  **TUEV** corpus annotates epileptiform events incl. spike-and-slow-wave
  (IEDs) — but in *different recordings*.
- **Tests:** P1 (seizures) with IED markers available separately (TUEV) — but
  not the *same events* progressing vs aborting.
- **Accessibility: application-light but gated** (signed PDF form emailed to
  NEDC → rsync credentials; no IRB/DUA, but not one-click).

### Intracranial (ECoG / SEEG / microelectrode)

**SWEC-ETHZ iEEG** — [ieeg-swez.ethz.ch](http://ieeg-swez.ethz.ch/)
- iEEG, Bern. Short-term: 100 recordings/16 patients (3 min pre + ictal + 3 min
  post). Long-term: 18 subjects, ~2,321 h, **244 ictal events**. Onset/offset
  marked; 512 Hz; 36–100 electrodes. **Only ictal events marked (no IED/aborted).**
- **Tests:** P1 persist side at good resolution; no labeled die class.
- **Accessibility: OPEN, no application** (URL list for a download manager).

**Schevon/Merricks OSF deposit (Columbia Utah-array)** — [osf.io/zhk24](https://osf.io/zhk24/),
paper [eLife 2021](https://elifesciences.org/articles/73541)
- Human **microelectrode-array** data. The open OSF deposit is **IED-centric**:
  397 `.mat` files (`allIEDs_<patient>_<n>`), each an `thisIED` struct with
  per-IED **waveform, MUA spike times, and traveling-wave coefficients**
  (`waveBetas`, `waveVelo`, `wavePval`). **Verified by inspection: the open
  deposit contains ONLY IEDs — no ictal/seizure files.** The seizure/ictal
  comparison in the paper used **raw microelectrode data that is DUA-gated**
  (contact Columbia).
- **Tests:** the **die** side of P1 at single-unit resolution, richly — but the
  **persist** side (ictal) is not in the open deposit. So it is a superb *die-
  class* resource, not a self-contained persist-vs-die test.
- **Accessibility: OPEN (preprocessed IEDs); raw ictal is DUA-gated.**

**IEEG Portal (ieeg.org)** — [ieeg.org](https://main.ieeg.org/?q=node/21)
- Aggregator of many human iEEG studies (incl. UPenn/Mayo, NeuroVista).
  Per-study onset/offset; IED annotation study-dependent.
- **Tests:** P1 (varies by study). **Accessibility: free registration; some
  datasets further permission-gated.**

**EPILEPSIAE** — [paper](https://inria.hal.science/hal-00818198) / [access](https://campus-technologies.de/en/the-european-epilepsy-database-2/)
- Scalp + intracranial, 275 patients, >45,000 h, ~2,662 seizures, standardized
  onset annotation. **Accessibility: PAID / DUA-gated** (fee amount unconfirmed;
  not openly downloadable).

**OpenNeuro iEEG (BIDS)** — [ds003029 seizures](https://openneuro.org/datasets/ds003029/versions/1.0.7),
[ds003876 interictal](https://openneuro.org/datasets/ds003876/versions/1.0.1),
[ds003844 RESPect](https://openneuro.org/datasets/ds003844)
- Clinician onset/offset markers; **seizure and interictal are SEPARATE datasets**
  (not aborted-vs-progressing within one record). **Accessibility: OPEN.**

### Seizure-prediction competition iEEG

**AES Seizure Prediction (UPenn+Mayo, Kaggle 2014)** — [review](https://medium.com/kaggle-blog/reviewing-the-american-epilepsy-society-seizure-prediction-challenge-2e0311488310)
- iEEG, 5 dogs + 2 humans, 48 seizures, ~628 interictal h. Data are **1-h clips
  pre-labeled preictal/interictal — no within-clip onset marks, no IED labels.**
- **Tests:** preictal-vs-interictal classification (seizure *prediction*), not
  P1's within-onset decay. **Accessibility: OPEN (free Kaggle account).**

**Melbourne/NeuroVista (Kaggle 2016)** — [Brain 2018](https://academic.oup.com/brain/article/141/9/2619/5066003)
- Ambulatory human iEEG, 400 Hz, 16 electrodes; released as 10-min preictal/
  interictal clips. No IED/aborted labels. **Accessibility: OPEN (Kaggle) /
  registration for full set.**

### Microelectrode / calcium imaging (both-class, at source)

**Rossi et al. PMC5550430 (the source paper's calcium data)**
- Widefield calcium imaging, awake mouse; **compares seizures to brief
  interictal events** — i.e. it contains BOTH P1 classes as standing waves, by
  design. This is *the* dataset P1 was written against.
- **Accessibility: NOT in a public repository.** Data-availability statement:
  "available from the authors upon request," with a sample set at
  `www.ucl.ac.uk/cortexlab/data`. Full data = email the authors.

**Wearable bonus — SeizeIT2** — [Sci Data 2025](https://www.nature.com/articles/s41597-025-05580-x)
- 125 patients, 883 focal seizures, >11,000 h behind-the-ear EEG/ECG/EMG/movement;
  BIDS on OpenNeuro. **Accessibility: OPEN.** (Scalp-adjacent; seizure labels
  only — same limits as CHB-MIT for P1.)

### The three questions that decide reach

1. **Open (no application) datasets with BOTH seizures AND aborted/interictal-
   spike events, with timing markers?** *Essentially none in a single record.*
   The design that matches the progress-vs-abort question (Rossi calcium) is
   **on-request, not open**. The OSF microelectrode deposit is **open but IED-
   only**. TUSZ (seizures) + TUEV (IEDs) can be combined but are **different
   recordings**. So the clean P1 contrast has **no ready-made open dataset**.
2. **Open closed-loop responsive-stimulation dose data (for P2/P3)?** **None.**
   The only per-event-dose closed-loop system is NeuroPace **RNS**, whose data
   are **proprietary** (research use via collaboration). P2/P3 are bespoke.
3. **Most accessible for a quick pilot?** **CHB-MIT** (direct download, EDF,
   seizure onset/offset labels, standard tooling) — used for the pilot below,
   with the honest caveat that it lacks a labeled die class.

---

## THREAD 3 — The observation-model problem (residual → observable)

**The corrected premise (this is the load-bearing update).** The model's
`residual` is NOT a hidden internal quantity requiring a loose proxy. In the
engine's frame, **residual = everything worked ABOVE order 0.** Order 0 is the
direct/predicted/reflexive baseline (the cheap default path); all processing
above it is the residual being worked down. That maps **directly** onto a
quantity predictive-coding neuroscience records routinely: **prediction-error /
surprise-driven, above-baseline activity** — superficial-layer prediction-error
units, the mismatch-negativity / oddball response, and the **broadband/high-gamma
above-baseline component**. So residual is an *observable*, and the honest
proxy is principled, not arbitrary:

> **residual(t) ≈ (band-limited high-frequency / gamma activity) − (its running
> order-0 baseline)** — the above-baseline error signal in the pre-transition
> window.

This is reinforced by the model's own empirical hook: in photosensitive
epilepsy the **asynchronous broadband** component reflects the *working
dissipation channel*, while the **synchronous narrowband-gamma** component is
the *trapped residual* that predicts seizures. That is exactly a residual read
in the frequency domain.

**Honest remaining degrees of freedom (narrower than "we can't see it," but
real).** Because the observable IS available, the test's weakness is not a
missing quantity — it is a handful of mapping and data choices, each of which
must be prespecified and each of which weakens an unprespecified test:

1. **Which band / which measure of the error signal.** High-gamma envelope vs
   broadband high-frequency vs a sync/async decomposition (the model actually
   wants the *synchronous* residual isolated, which scalp EEG cannot cleanly
   give). Choosing the band post hoc is a garden of forking paths.
2. **What counts as the order-0 baseline** (running median window length,
   percentile). Different baselines change the decay slope.
3. **Seizure heterogeneity.** Onset dynamics differ across seizure types,
   patients, and foci; a decay-rate separator that holds within one focus may
   not generalize. A pooled test mixes generative processes.
4. **Label quality / the die class.** No open scalp dataset labels aborted
   onsets, so "die" events must be *self-detected* (a spike/transient detector
   with its own threshold DoF), which conflates detector behavior with the
   biology.
5. **Recording modality mismatch.** The model's "standing wave" is a mesoscale
   spatial object; scalp EEG integrates over cm of cortex and muscle, so the
   scalp "residual envelope" is a coarse shadow of the modeled quantity. LFP /
   microelectrode / calcium narrow this gap.

**Consequence for test strength.** P1 is a **strong** real-data candidate *at
the right modality* (calcium/LFP, both classes labeled): there the residual
observable is clean and the DoF collapse to band choice + prespecification. P1
is a **weak** test on scalp-EEG-with-self-detected-die (CHB-MIT): the observable
is a coarse shadow AND the die class is detector-defined. The pilot below is the
latter — deliberately, because it is what is openly reachable — and is reported
as feasibility + honest-null, not as evidence.

---

## THREAD 4 — Pilot (P1 on CHB-MIT)

**Reachability.** Network access permitted a direct anonymous download of
CHB-MIT chb01 from PhysioNet (bandwidth was low; 4 of the 7 chb01 seizure EDFs
completed in the available window and were used). This is a REAL open-data
pilot, not a synthetic one. Script: `scripts/seizure_p1_chbmit_pilot.py`; output:
`results/seizure_p1_chbmit_pilot.json`.

**Design (prespecified in the script header, BEFORE outcomes were seen).**
- *Residual observable* = high-gamma envelope (bandpass **25–45 Hz**, below the
  muscle-dominant >50 Hz range; 4th-order Butterworth + Hilbert, averaged over
  the 23 bipolar channels), with the **running-median (60 s) baseline
  subtracted** = the order-0 default removed, leaving the worked residual.
- *Events* = local maxima of the residual exceeding median + 3·MAD (threshold
  estimated on interictal data), 2 s refractory.
- *Decay slope* = slope of the log-envelope over the **1 s following each peak**
  (the standing-phase (non-)shedding readout; a persist wave should shed slowly
  → slope near 0; a die wave sheds fast → strongly negative).
- *Labels* — **PERSIST**: peaks in the pre/at-onset window [onset−6 s, +2 s] of
  the 4 annotated seizures. **DIE (proxy)**: peaks in deep-interictal periods
  (>300 s from any seizure). (CHB-MIT has no aborted-onset labels; "die" is
  self-detected — a declared DoF, Thread 3.)
- *Test*: one-sided Mann–Whitney U (H1: persist slope > die slope, i.e. persist
  sheds slower) + a 20,000-shuffle permutation test on the median difference.
  CSD control: lag-1 autocorrelation of the pre-peak window.

**Result (4 seizures, chb01, N = 14 persist transients vs 5,446 die transients).**

| metric | PERSIST | DIE (interictal proxy) |
|---|---|---|
| median log-env decay slope (/s) | **−0.80** | **−1.20** |
| mean decay slope (/s) | −0.20 | −1.27 |
| lag-1 autocorrelation | +0.37 | +0.14 |

- One-sided Mann–Whitney U (persist sheds slower): **p = 0.19** — not significant.
- Permutation median difference (persist−die) = **+0.40 /s, p = 0.38** — not significant.

**Reading — honest, and it is a NULL (direction-consistent but underpowered).**
1. The DIRECTION matches P1: persist (pre-seizure standing-phase) transients
   decay MORE SLOWLY (slope closer to 0) than interictal transients, which shed
   fast. That is the model's sign (slow-to-shed → persist).
2. But it is **not statistically significant** at any usual threshold, and the
   effect is **unstable** in a way that flags how underpowered it is: on the
   FIRST file alone the aggregate was *reversed* (persist decayed FASTER,
   one-sided p = 0.95); it only moved into the P1 direction once the 2nd–4th
   seizures were added, and the effect SIZE shrank from the 3-file to the 4-file
   run. A sign that flips on adding one of four recordings is noise, not a result.
3. **The decay-rate signal is NOT separated from critical slowing down here.**
   P1's distinctive claim is a decay-RATE separator *distinct from* rising
   autocorrelation (CSD). In this pilot the persist set ALSO had higher lag-1
   autocorrelation (0.37 vs 0.14), so the two are confounded — this data cannot
   adjudicate P1-vs-CSD, which is the very fork P1 is meant to decide.
4. **N is tiny and single-patient.** 14 persist transients from 4 seizures in
   ONE subject (chb01). No correction for within-seizure correlation of the ~3–4
   transients per event. This is a feasibility run, not a powered test.

**What this pilot IS and ISN'T.** It IS a demonstration that the residual→
above-baseline-error pipeline runs end-to-end on real open EEG and yields a
prespecified, direction-signed readout. It is NOT evidence for P1: it is an
honest **underpowered null with a P1-consistent direction and an unresolved CSD
confound**, exactly the outcome the observation-model DoF (Thread 3) predict for
the weakest reachable modality (scalp EEG, self-detected die class, single band).

---

## Bottom line

**Is real-data validation reachable now, or a bespoke-data project? Mixed —
and it splits cleanly by prediction.**

- **P1 (decay-rate separator) is the one near-term-testable prediction on
  observational data, and residual-as-observable makes it stronger than first
  briefed.** The residual is not a hidden quantity — it maps to above-baseline
  prediction-error activity (high-gamma envelope minus the order-0 baseline),
  which is routinely recorded. P1 needs only both-class onset events with a
  time-resolved trace; it needs **no spatial resolution and no intervention**.
  BUT the clean test needs a dataset that labels BOTH persist and die onsets in
  one recording, and **that dataset is not openly available**: the ideal one is
  Rossi et al.'s own calcium data (PMC5550430, on-request), and the best open
  microelectrode resource (Schevon/Merricks OSF, osf.io/zhk24) contains only the
  DIE class (IEDs) — the ictal comparison is DUA-gated. So P1 is
  **near-term testable, but on request-gated or bespoke-labeled data, not on a
  one-click download.**

- **P2 and P3 (hysteresis dose; magnitude-not-timing abort) are bespoke-data
  projects.** They require closed-loop stimulation with recorded per-event dose,
  which **no open dataset carries** (NeuroPace RNS logs are proprietary). Testing
  them means a device-maker collaboration or a purpose-built closed-loop animal
  experiment. Not reachable from open data.

- **P4/P5 are model-extension problems, not data problems** (need a
  heterogeneous/hub lattice; declared limits in `SEIZURE_SCIENCE.md`).

**Single best dataset+prediction pairing to pursue:** **P1 on the Rossi et al.
(PMC5550430) calcium data** — it is the exact recording P1 was written against
(seizures vs brief interictal events as standing waves, both visible, temporal
resolution adequate), where the decay-rate-vs-morphology and decay-rate-vs-CSD
contrasts can be made cleanly at the right modality. It requires an author data
request. **Best fully-open runner-up:** combine the Schevon/Merricks OSF IEDs
(open, microelectrode "die" class with waveforms) with a DUA request for the
matching ictal ("persist") data — a single-institution, single-modality contrast
far stronger than scalp EEG.

**Pilot outcome:** run on real open CHB-MIT scalp EEG (4 seizures, 1 patient).
Result is an **honest underpowered null**: the residual-decay slope is
*directionally* consistent with P1 (pre-seizure transients shed slower than
interictal ones) but **not significant** (p ≈ 0.19–0.38), **sign-unstable** across
n=1→4 files, and **confounded with critical slowing down** (autocorrelation also
elevated in the persist set — so this data cannot make P1's defining
decay-rate-vs-CSD distinction). This is the predicted ceiling for the weakest
reachable modality; it demonstrates the pipeline, not the prediction.

**Blunt bottom line.** The glass-box model emits one genuinely
observational-testable prediction (P1), and the observable it needs is real and
well-characterized — but **no openly-downloadable dataset carries both required
event classes in one recording**, so even P1's clean test is a
request-gated/bespoke-labeling project, and the scalp-EEG pilot that IS reachable
is too weak and confounded to move the needle. P2/P3 need closed-loop dose data
that is entirely proprietary. **Real-data validation of this model is reachable
but is a bespoke-data (or data-request) project, not something completable on
open downloads in this environment.** The honest near-term path is a data
request to the Rossi/Schevon groups, not another open dataset.
