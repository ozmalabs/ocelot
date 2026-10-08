# EEG Foundation Challenge (NeurIPS 2025) — OCELOT well-formedness audit

**Lens:** not "can we decode EEG better" but "is the WELL-FORMEDNESS claim
MEASURABLE" — the claim that a well-formed decoder REFUSES to compute over
subject/session/montage frame-coordinates (frame-noise the transfer gate
projects out), and that a fit-everything foundation baseline mostly learns
exactly that refusable noise. Contribution OCELOT would make = the negative
space: a characterization of EEG transfer dimensionality, proving what a
well-formed system should NOT compute.

**Governing invariant (CLAUDE.md).** "Truth is frame-relative; the invariant
lives ACROSS frames; in-frame is INTEGER, non-integer math is CROSS-FRAME,
the continuum sits in `Hom(frame, frame)` not in any object" (CLAUDE.md
lines ~568–590, the BASE-AS-DIMENSION / frame-continuum section). This is
almost verbatim the challenge's own framing: organizers name subject /
session / montage as "the frame to be invariant to." The philosophical fit
is exact. The audit below asks whether the fit is more than philosophical —
whether OCELOT's *parts* construct the projection, and whether the refusal is
*measurable* here.

Every verdict is EXISTS(reuse) / PARTIAL(adapt) / ABSENT(build) with file:line.

---

## 1. The subject-frame projection (the crux) — **ABSENT (build)**

The claim needs a real operation that SEPARATES an invariant coordinate from a
frame coordinate — "subject/session is a frame, project it out, keep the
cross-frame invariant." I looked hard at the three named candidates.

### 1a. `domains/crossframe_world.py` — cross-frame IDENTITY, not cross-frame INVARIANCE
Read in full. This is a **world adapter** (ingest pixels → relation tuples →
`run_rules()` → read one attr; `crossframe_world.py:1-40` docstring states it
makes no branch over graph state). What it actually computes:
- The "frame" being generalized over is **appearance / quantization**
  (`quantize` on a fixed absolute 0..255 scale, `crossframe_world.py:38-46`;
  `sig_of` emits region-LOCAL `["cell", r, c, "v<q>"]` tuples so a probe cannot
  match by absolute position, `crossframe_world.py:60-64`).
- The "invariant" is decided in `seeds/vision_crossframe_identity.json`
  (`xf_score` / `xf_identify`): a 16-way Argmax over held `ShapeSignature`
  nodes by `ShapeDecode`'s `covered_count` (`vision_crossframe_identity.json`
  rules `xf_score`, `xf_identify`). On these tuples `covered_count` is EXACTLY
  the count of cells identical in local position and quantized value — i.e.
  **exact-cell overlap**, deliberately equivalent to Hamming-NN, which the
  adapter even computes alongside as reference R1 (`crossframe_world.py:72-80`,
  `hamming_nn`).

So "cross-frame collapse" here = pick the held exemplar with maximal exact
overlap, robust to a quantization/appearance change. There is **no operation
that estimates a subject-varying subspace and removes it**. The "frame" is a
fixed input transform applied before the graph (`crossframe_world.py:38-64`),
not a *learned nuisance direction* projected out of a representation. The
challenge's frame (inter-subject morphology, montage, paradigm) is a
statistical nuisance subspace, not a known pixel remap. **ABSENT.**

### 1b. `runners/dsl/src/shape_decode.rs` DimInfer / GenInfer / LatentDimension minting — mints INTEGER-coordinate maps, not statistical projections
Read `load_generators` and the `Generator` struct (`shape_decode.rs:434-612`)
and the seed loop rules (`seeds/shape_decode_loop.json`: `sd_infer_dimension`
line 360, `sd_recognize_dim` line 1783, `sd_mint_quantum`, `codebook_epoch`).

What DimInfer actually mints: a `LatentDimension` selected from a held
`DimensionGenerator` codebook whose `kind` dispatches to a **built-in
integer-coordinate primitive** — `rotation90` / reflections, `modular` (cyclic
Z_n, `shape_decode.rs:459-466`), `scale2` (multiplicative ×2^k), `linear`
(integer matrix `M·(v-min)`, `shape_decode.rs:474-486`), `translate` (integer
offset, `shape_decode.rs:487-503`). Every generator acts on typed
**coordinate slots** (`dim_types` = `pred`/`coord:<axis>`/`val`/`sym`,
`shape_decode.rs:156-166`) and produces an integer step `k`. This is the
CLAUDE.md invariant made literal: `coord_ints` returns `None` on a `Float`
slot BY DESIGN (CLAUDE.md ~line 570, "In-frame is INTEGER … `coord_ints`
refusing floats is CORRECT and load-bearing, NOT a gap").

That is precisely why it does not fit here. "Subject" is not a rotation, a
cyclic wrap, or an integer matrix over observed coordinate slots. Projecting
out a subject requires a **real-valued, data-estimated** nuisance subspace
(the projection matrix is fit from a population of subjects). By the tree's
own invariant that lives in `Hom(frame, frame)` — a cross-frame MAP with a
continuous parameter — and DimInfer only mints maps from a **fixed built-in
generator table** (`load_generators` dispatches on hardcoded `kind` strings;
the only data-defined map is `linear`'s INTEGER matrix, `shape_decode.rs:466-486`).
There is no generator kind whose parameters are estimated from a data
population, and no facility to mint one. So "subject" cannot today be minted
as a `LatentDimension` the decode factors out the way scale/time/base were.
**ABSENT** (the hook exists — `LatentDimension` is the right node type — but
the generator that would carry a fitted projection does not).

### 1c. Grounding-as-vector / CAN marginal read — expresses frames symbolically, does not compute the projection
The grounding/teach machinery (CLAUDE.md "grounding is a vector"; `domains/teach.py`
per CLAUDE.md ~line 200) files knowledge under meta-shapes; the gap-awareness
faculty (`seeds/gap_awareness.json`) lets the agent NAME a frame as a
coordinate it should refuse. But naming "this coordinate is subject-frame" is
not the same as an operator that separates invariant-coordinate from
frame-coordinate in a representation. No marginal-read primitive computes
"variance attributable to subject vs variance surviving subject change."
**ABSENT.**

**Section 1 verdict: ABSENT.** OCELOT has the *vocabulary* for the claim
(frames, LatentDimension, cross-frame maps in `Hom`) and one genuine
cross-frame recognizer (crossframe = exact-overlap identity), but **no
operation that estimates and removes a subject-frame subspace**. The
projection operator would need building: either (i) a new `DimensionGenerator`
kind whose map is a data-fitted linear projection (violates the current
integer-only generator contract — the matrix path is integer, `shape_decode.rs:466`),
or (ii) an out-of-graph fit that produces the nuisance basis, fed in as a
`linear` generator's data. Neither exists.

---

## 2. EEG signal ingest + spectral primitives — **PARTIAL (adapt)**

### Spectral primitives: EXISTS as Rust primitives, exposed to Python
The audio stack is genuinely multichannel-oscillatory DSP and is real:
- `gammatone_band` (`audio_primitives.rs:19`), `bandpass` (biquad,
  `audio_primitives.rs:287`), `band_autocorr` (`audio_primitives.rs:100`),
  `summary_autocorrelogram` (`audio_primitives.rs:142`), `periodicity_track`
  (`audio_primitives.rs:193`), plus LPC/all-pole.
- These are exposed via PyO3: `gammatone_band` (`py.rs:10864`), `allpole_ear`
  (`py.rs:11170`). The module header states plainly "Nothing here touches the
  substrate. All graph mutation happens in `pipeline_runtime.rs` after these
  primitives return" (`audio_primitives.rs:11-12`) — they are I/O-boundary DSP,
  the legal category for a world adapter.

Do they transfer to EEG band-power / spectral / connectivity? **Partly.**
- Band decomposition (delta/theta/alpha/beta/gamma): YES — `bandpass`/gammatone
  give per-band envelopes directly; the seizure pilot already does exactly this
  with scipy butter+hilbert (`seizure_p1_chbmit_pilot.py:65-84`, `band_envelope`).
- Periodicity / autocorrelation features: YES in principle (`band_autocorr`,
  `periodicity_track`), oscillatory by construction.
- Cross-channel COHERENCE / connectivity: **NO direct primitive.** The audio
  stack is single-channel-per-band; `summary_autocorrelogram` pools ACROSS
  bands of ONE channel (`audio_primitives.rs:142`), not across 128 spatial
  channels. Connectivity (coherence, PLV) would be new DSP. There is a
  `cross_band_coincidence` named in the brief but it is band×band within a
  channel, not channel×channel spatial connectivity.

### Ingest path (multichannel timeseries → graph): ABSENT
There is **no world adapter that turns a multichannel timeseries / EEG epoch
into a substrate graph.** Searched `domains/**` for
`multichannel|timeseries|epoch|EEG|band_power|coherence`: hits are audio ears
(`agent_frontend.py:178` `_cochlear_ear`, `many_settings_recognizer.py`),
DOOM epoch counters, blob geometry — none an EEG/timeseries ingest. Searched
for `readSignal|edf|ingest.*signal`: the ONLY EDF reader in the tree is the
standalone seizure pilot (`seizure_p1_chbmit_pilot.py:65`, `pyedflib`), and it
never touches the substrate. No BIDS reader, no epoch→graph seam. The
audio path proves the *pattern* (bytes → AudioBuffer node → ear Operations,
`py.rs:6058-6062`) but an EEG epoch adapter (128ch × time → per-band /
per-region relation tuples like crossframe's `["cell", r, c, "v<q>"]`) would
have to be written.

**Section 2 verdict: PARTIAL.** Band/spectral primitives EXIST and are
PyO3-exposed; a per-band envelope feature path is a short adapter over them.
Cross-channel connectivity and the epoch→graph ingest are ABSENT and must be
built. The natural target representation is crossframe's own tuple form
(quantized band-power per channel-region → `["cell", region, band, "v<q>"]`),
which would slot straight into `ShapeDecode` — that is the one genuinely
reusable seam.

---

## 3. Prior EEG work in the tree — **EXISTS (one pilot), but OFF-SUBSTRATE**

`scripts/seizure_p1_chbmit_pilot.py` is the closest prior art. Read in full.
- **Dataset:** CHB-MIT scalp EEG (PhysioNet), chb01, 7 seizures
  (`seizure_p1_chbmit_pilot.py:36-43`). Real open EEG.
- **Ingest/feature path:** `pyedflib` EDF read → butter bandpass 25–45 Hz
  "high-gamma residual" proxy → Hilbert envelope, mean across channels →
  decimate to 32 Hz → running-median baseline subtraction → above-baseline
  residual (`band_envelope` + `running_median` + `resid`,
  `seizure_p1_chbmit_pilot.py:65-118`). Feature = log-envelope DECAY SLOPE in a
  post-peak window (`analyse`, `seizure_p1_chbmit_pilot.py:120-160`).
- **What it did / found:** prespecified one-sided Mann-Whitney + permutation
  test on persist-vs-die decay slope, N=7, explicitly "UNDERPOWERED by
  construction" (`seizure_p1_chbmit_pilot.py:33`, `main` reports descriptives
  if <3 per arm, line ~185). It is a FEASIBILITY pilot with heavy honesty
  caveats (scalp EEG can't resolve a standing wave; muscle contamination
  >40 Hz), not a substrate decode.

**Critical finding for transfer:** the pilot is **pure Python + scipy, entirely
off the substrate** — no `ShapeDecode`, no graph, no `run_rules`. It proves (a)
the environment can read real open EEG with `pyedflib`, (b) the house
PREREG→measure→RESULTS discipline was applied to EEG once, and (c) a band-
envelope feature is computable. It does NOT provide any substrate ingest or
decode path — nothing about the well-formedness projection was exercised. What
transfers is the *DSP recipe and the data-reading capability*, not any
graph-native EEG machinery. Other biosignal/timeseries decode (window_knob_dyad,
regression-from-signal): none found on the substrate.

**Section 3 verdict: EXISTS (as an off-substrate DSP pilot).** Useful as a
data-reading + featureization template; contributes zero graph-native transfer
toward the projection claim.

---

## 4. Is the refusal MEASURABLE (the go/no-go) — **NO-GO on both legs**

The Track-3 well-posedness proof worked because the oracle was public and cheap
to perturb. The analogue here is: can we MEASURE that a fitted baseline's
representation is mostly subject-frame (dies under subject change) vs
task-invariant?

### 4a. Data reachable at proving scale? — **NO (in this environment)**
- `data/` holds arxiv, cmu_mocap, omniglot, pendata, voice/vision curricula,
  wiki/wiktionary, etc. (listed) — **no EEG, no HBN, no BIDS, no OpenNeuro
  mirror.** `file_search "eeg"` → zero files tree-wide.
- HBN-EEG is multi-TB (128ch, 3000+ subjects, 6 tasks, BIDS). No small public
  subset is present locally and nothing in the tree references an
  OpenNeuro/S3 path (`grep HBN|openneuro|s3://|eeg2025|psychopathology` → only
  unrelated "regression-test" hits). A starter sample would have to be fetched;
  the challenge's scale (cross-SUBJECT generalization) is the whole point, and a
  handful of subjects cannot prove a subject-invariance claim — the measurement
  IS a population statistic over subjects.

### 4b. Can OCELOT construct the invariance measurement? — **NO**
The measurement is: decode with the subject-frame projected out vs a
fit-everything baseline, and quantify how much signal is refusable. Section 1
established the projection operator is ABSENT. Without it there is nothing to
compare against the baseline — the left-hand side of the contrast cannot be
computed on the substrate today. `ShapeDecode` covered_count gives a decode
score, and a fitted baseline is trivially available externally, but the
"projected-out" arm requires the subject-nuisance basis and a generator that
applies it — neither exists (§1b).

### 4c. Cheapest honest experiment that would prove-or-refute the claim?
The claim to prove: "the transferable EEG coordinate is a strict low-dim
projection; fitting the rest is computing below the transfer noise floor." The
cheapest HONEST form does NOT need the full substrate:
1. Fetch a small multi-subject HBN-EEG BIDS sample (enough subjects that
   leave-subjects-out is meaningful — dozens, not thousands).
2. Featurize with the existing band-envelope recipe (`band_envelope`,
   reusing the pilot).
3. Estimate the subject-nuisance subspace (a supervised-domain / leave-subject
   linear projection — this is the operator §1 says is ABSENT; here done
   out-of-graph in numpy).
4. Measure, for Challenge-1 (CCD response-time) and Challenge-2 (psychopathology
   factor) regression targets: R^2 with vs without the projection, as a function
   of retained dimensionality — the "transfer dimensionality" curve. The
   refutable prediction: cross-subject transfer R^2 saturates at low retained
   dim, and the removed subspace carries within-subject fit but zero
   cross-subject transfer (the "refusable work below the noise floor").

That is a legitimate, cheap experiment — but note it is a **numpy/sklearn
experiment, not an OCELOT-substrate experiment.** The substrate contributes
only the band-envelope DSP (already reproducible in scipy). The projection —
the actual content of the claim — would be built outside the graph because the
graph cannot express a data-fitted projection (§1b, integer-only generators).

**Section 4 verdict: NO-GO** at proving scale in this environment, on both
legs: (a) the proving-scale multi-subject data is not reachable locally, and
(b) the projection/refusal measurement cannot be constructed with OCELOT's
parts (the projection operator is ABSENT). The Track-3 analogue fails: there is
no public, cheap-to-perturb oracle here, and the operator the claim is ABOUT is
the missing piece.

---

## 5. What OCELOT should REFUSE (the negative-space thesis, concrete)

Made concrete for THIS challenge, given the parts:

- **The refusable computation.** A fit-everything foundation baseline learns a
  representation in which subject/session/montage coordinates carry variance
  the model fits (they help in-subject reconstruction / in-distribution fit). A
  frame-relative well-formed decoder DECLINES to compute over that subspace:
  by CLAUDE.md's rule, subject identity is a FRAME, its coordinates are
  in-frame noise, and the transferable target lives in `Hom(subject, subject)`
  — the map, not the object. The refusal is: **do not spend representational
  capacity on the subject-frame subspace; keep only the cross-subject
  invariant projection.**

- **(i) Is the refusal provable as information?** In principle YES — it is a
  characterization of EEG transfer DIMENSIONALITY: "the transferable coordinate
  is a strict low-dim projection; the complement is refusable." That is a real,
  falsifiable statement (the §4c dimensionality curve). But provable HERE?
  Only with the ABSENT projection operator and unreachable data — so **not
  provable with OCELOT's current parts** (§1, §4).

- **(ii) Does being well-formed serve the score?** YES, and this is the one
  strongly positive finding: **Challenge 2 is literally named "Subject
  Invariant Representation" and rewards invariance to inter-subject
  morphology / paradigm / sensor placement.** The well-formed refusal and the
  metric point the same way — projecting out the subject frame is exactly what
  the metric pays for. The alignment is genuine; the blocker is purely
  mechanical (no projection operator, no data), not conceptual.

---

## GO / NO-GO VERDICT — **NO-GO** (localising)

The well-formedness REFUSAL CLAIM is **not measurable** with OCELOT's parts +
reachable data in this environment. This is a localising no-go, stated
honestly:

1. **The projection operation is ABSENT.** OCELOT has the frame vocabulary and
   the `LatentDimension` hook, but every `DimensionGenerator` is an
   integer-coordinate map from a fixed built-in table (`shape_decode.rs:434-612`;
   `coord_ints` refuses floats BY DESIGN, CLAUDE.md ~line 570). "Project out the
   subject" is a data-FITTED real-valued nuisance projection — a cross-frame map
   with an estimated continuous parameter — which no existing generator carries
   and no facility mints. The one real cross-frame recognizer (crossframe) is
   exact-overlap identity, not subspace removal (§1a).

2. **The data is unreachable at proving scale.** No EEG/HBN/BIDS locally
   (`data/` listing; `file_search eeg` = 0), HBN is multi-TB, and the claim is
   inherently a population statistic over MANY subjects — a small sample cannot
   prove subject-invariance (§4a).

3. **The measurement cannot be constructed on the substrate.** The "projected
   out" arm of the contrast is exactly the ABSENT operator; without it there is
   no left-hand side to compare to the fit-everything baseline (§4b).

**What would unblock it (in cost order):**
- **Build the projection operator.** Either a new `DimensionGenerator` kind
  whose map is a data-fitted linear projection (breaks the integer-only matrix
  contract at `shape_decode.rs:466` — a real design change, reviewable against
  the "continuum lives in `Hom`, applied intensionally" clause of CLAUDE.md,
  which actually SANCTIONS a continuous cross-frame map), OR an out-of-graph fit
  that emits the nuisance basis fed in as `linear` generator data. This is the
  crux build; everything else is plumbing.
- **Build the EEG epoch→graph ingest** (a ~50-100 line world adapter: 128ch ×
  time → per-band envelope via `bandpass`/`gammatone_band` PyO3 →
  quantized `["cell", region, band, "v<q>"]` tuples → `Observation`, exactly
  crossframe's seam). PARTIAL today (primitives exist, ingest doesn't).
- **Reach a small multi-subject HBN-EEG BIDS sample** (starter-kit / OpenNeuro
  subset) — enough subjects for leave-subjects-out to mean something.
- **Then** the §4c dimensionality experiment becomes runnable — but honestly, in
  its cheapest form it is numpy/sklearn with substrate DSP as a feature
  front-end, because the projection is the content and the substrate can't yet
  express it.

**The honest bottom line.** The philosophical fit is excellent — the challenge's
own "subject-invariant representation" is CLAUDE.md's frame invariant almost
word-for-word, and the refusal ALIGNS with the Challenge-2 metric (§5-ii). But a
theorem about EEG transfer requires the projection operator OCELOT does not have
and multi-subject data OCELOT cannot reach here. A hopeful "yes" would be
worthless; the truthful finding is a localising NO-GO — build the fitted-
projection generator and reach a multi-subject sample first, and the refusal
becomes measurable and metric-aligned. Until then, OCELOT can articulate the
refusal but cannot MEASURE it.
