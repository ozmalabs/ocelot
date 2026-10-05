# Paper plan: Mary’s Room as a test of sensory prediction and representation

## Purpose and relation to the existing qualia paper

The existing paper, *The Law of Graphic Equalisation — Qualia and Consciousness
Grounding*, is a conceptual argument. It proposes that qualia are relational
structure and describes qualia-space as active compression. The new paper should
not restate that argument or present the current eye run as proof of it.

The new paper is an empirical/computational case study of Mary’s Room. It asks
which parts of the thought experiment can be operationalised in a biologically
grounded visual system: what color distinctions are predictable from physical
and visual science before exposure; what state changes when the eye receives
light; whether those states remain in the same representational space; and what
information can be retained by a compact code without losing discrimination.
Its contribution is to replace the thought experiment’s all-or-nothing intuition
with measurable predictions and explicit limits.

## Working title

**What Mary Can Predict Before Seeing Red: A Computational Test of Color
Knowledge, Sensory Encoding, and Compression**

Alternative shorter title: **Mary’s Room in a Biologically Grounded Eye Model**.

## Central thesis

For specified color contrasts and a biologically grounded eye model, held
physical/visual knowledge can predict the eye’s later color-discriminating state
before exposure. Exposure supplies an instantiated sensory state, but in the
tested system that state is quantitatively related to the research prediction
and remains usable in the same opponent-color representation. A compact code may
preserve the relevant distinctions. This makes a separate, nonphysical addition
unnecessary to explain the tested identification and coding results; it does not
establish that human phenomenal experience is exhausted by this model.

The paper should state the user's stronger philosophical interpretation as a
motivating hypothesis: Mary’s post-release change may be a change in access,
acquaintance, or representational format, rather than a new ontological kind.
The experiment tests the representational claim, not the metaphysical identity
claim directly.

## Research questions

1. **Pre-exposure identification:** Can a theory-only decoder, fixed from
   published cone fundamentals and opponent axes, classify stimuli without
   running the eye?
2. **Prediction of sensory state:** How close are the eye’s opponent responses
   to research-derived predictions across color, intensity, and illumination?
3. **Same-kind change:** Can both predicted and sensory states be described in
   one shared coordinate system, with exposure changing state values rather
   than requiring a new representational type?
4. **Compression and preserved function:** Does a compact code reduce description
   length on held-out sensory samples while preserving color discrimination?
5. **Boundary conditions:** Where do predictions fail—for example, near opponent
   boundaries, under adaptation, for metameric spectra, or when assumptions about
   observer and illumination are wrong?

## Current pilot and what it establishes

The present v2 pilot compares CIE 2006 2-degree LMS predictions for 610 nm red
and 530 nm green against one 24-column photon-eye exposure. The research-only
sign rule classifies 2/2 stimuli; the eye output classifies all 24 columns; mean
opponent-vector direction match is 99.90/100. The graph loop creates two color
categories and reports a declared coordinate-code proxy of 48 raw units versus
28 category-plus-label units.

Treat this as a feasibility pilot, not the main paper result. It has only two
spectral stimuli, categorical sign labels, and one illumination/exposure regime.
All columns of a given color return the same vector, so the reported MDL saving
mostly reflects repeated samples of two values. The current code-length proxy is
not yet a general compression benchmark, a neural resource measurement, or
evidence of human subjective experience. Preserve it as preliminary evidence and
make these limits explicit.

## Confirmatory study design

### Arm A: theory-only prediction

- Predeclare spectral stimuli, photon counts, observer fundamentals, opponent
  transform, decoder, and evaluation metrics before executing the eye arm.
- Sample many wavelengths across the visible range, with dense sampling around
  the RG opponent zero-crossing and category boundaries.
- Include multiple intensities and illuminants, and both isolated spectral
  lights and broadband/reflected-color mixtures.
- Predict LMS and opponent responses solely from published fundamentals and the
  declared optics/illumination model. Do not tune predictions to eye outputs.
- Report classification and regression metrics, calibration, and error as a
  function of distance from the opponent boundary.

### Arm B: photon-eye encoding

- Run the identical stimuli through fresh, documented eye instances.
- Save raw photons, retinal outputs, intermediate signals, adaptation state,
  and engine provenance for every trial.
- Compare theory-only predictions with eye output using predeclared vector
  distance, angular error, rank correlation, and classification agreement.
- Include repeated independent trials or seeds where the implementation has
  stochasticity; otherwise identify deterministic repeats as such.

### Arm C: representation and compression

- Keep physical vectors, sensory vectors, category labels, and any learned
  prototypes separate in the data model so the evaluation cannot leak labels.
- Fit the compressed codebook on a training subset, then measure held-out
  description length and downstream discrimination on untouched samples.
- Compare against raw coordinates, a fixed opponent basis, PCA, and a simple
  vector-quantisation baseline with matched code budget.
- Report rate–distortion curves: bits or declared code units against perceptual
  error and task accuracy. Use an explicit prefix/code-length accounting or
  label the result only as a proxy; do not describe coordinate counts as
  physical storage or neural energy.
- Ablate opponent axes and category rules to test whether compression preserves
  task-relevant distinctions because of the representation, not because labels
  are copied into the code.

### Arm D: biological and human relevance

Use two distinct validation levels and do not conflate them:

1. **Biological grounding:** document which eye-model components correspond to
   known ocular/retinal mechanisms, which are simplified, and which stages are
   absent. Compare available model responses with published physiological
   measurements where an appropriate dataset exists.
2. **Human behavior:** if the paper claims human relevance, collect or reuse
   psychophysical color-discrimination/similarity judgments under matched
   stimuli, with observer-specific calibration. Compare the model’s geometry
   and predictions with those judgments. If no human data are collected, keep
   conclusions explicitly about the model.

The Mary analogy is clearest if a behavioral observer can make a forced-choice
prediction from the research arm before exposure and then compare that prediction
with the later sensory arm. No claim that a model literally has human
phenomenology is required for this operational test.

## Preregistered predictions

- Physical-model decoding will outperform chance across the predeclared
  stimulus set, including held-out wavelengths and conditions.
- Eye outputs will preserve the main predicted color distinctions and be
  quantitatively predictable from the declared theory model, with measurable
  error near boundary cases.
- Exposure will instantiate a sensory vector in the same coordinate system;
  a type discontinuity will not be required to represent the post-exposure
  state.
- A learned compact code will improve held-out description length over raw
  coordinates at a specified distortion/accuracy level. If it does not, the
  compression thesis is not supported for that operating regime.
- Failures, including a failure to predict novel conditions, count against the
  stated scope and will be reported rather than excluded post hoc.

## Analysis plan

- Primary: held-out color discrimination accuracy and balanced accuracy for
  research-only versus eye outputs.
- Primary: predictive fit of the eye’s opponent vectors from physical inputs,
  with error intervals over trials/conditions.
- Primary: held-out rate–distortion curve and task accuracy at matched code
  budgets for each compression baseline.
- Secondary: category geometry, cross-condition generalisation, calibration,
  and error around opponent sign boundaries.
- Report every stimulus, transform, threshold, exclusion, seed, and model
  revision. Keep pilot and confirmatory results separate.

## Proposed paper structure

1. **Introduction:** Mary’s Room as a knowledge-versus-experience inference;
   state why identification before exposure and representational continuity
   are experimentally separable from metaphysics.
2. **Background:** knowledge argument and major physicalist replies; CIE LMS
   and opponent-color coding; biologically grounded eye model; compression as
   an operational hypothesis. Clearly distinguish the present work from the
   existing conceptual qualia-grounding paper.
3. **Operational reconstruction of Mary:** define “knowledge,” “exposure,”
   “identification,” “experienced state” in model terms; specify what the
   analogy preserves and omits.
4. **Methods:** apparatus, stimuli, preregistration, theory decoder, eye,
   shared representation, compression baselines, held-out evaluation.
5. **Results:** prediction before exposure; eye responses after exposure;
   representational alignment; compression and discrimination trade-off;
   boundary/failure cases.
6. **Discussion:** interpret the results as evidence that sensory experience
   need not introduce a different representational kind to explain the tested
   color judgments. Discuss acquaintance and new modes of presentation as
   possible descriptions of the post-exposure gain.
7. **Limits:** model-to-human gap, no direct access to phenomenal character,
   stimulus coverage, simplifications in eye model, and limits of the selected
   code-length metric.
8. **Conclusion:** Mary-style “newness” can be studied as a measurable update
   or change in access/representation; the thought experiment alone does not
   establish that the update is ontologically magical or categorically
   different.

## Position relative to the existing paper

The existing qualia paper argues conceptually that determinate qualia are
relational and that qualia-space can be understood as active compression. This
paper should cite it as the motivating framework, then remain answerable to
measured outcomes. It must not assume the framework’s conclusion in its
operational definitions. In particular, compression is a hypothesis to measure
against baselines, and shared coordinate representation is evidence about
continuity of model states—not by itself proof that phenomenal states are
identical to neural or computational states.

The distinct contribution is the empirical bridge: a preregistered, auditable
comparison between what a visual theory predicts before exposure and what a
biologically grounded eye computes after exposure, followed by a held-out test
of whether compact coding preserves the distinctions Mary would need to name.

## Immediate next steps

1. Audit the eye model’s biological lineage and write a mechanism-to-code table.
2. Design a broad stimulus set with held-out wavelengths, mixed spectra,
   intensities, and illuminants; choose edge cases before execution.
3. Replace the current duplicated-vector MDL proxy with held-out rate–distortion
   and matched-budget baselines.
4. Preregister the confirmatory protocol and analysis before running it.
5. Decide whether to include new human psychophysics. If not, title and abstract
   should say “eye model” and “computational Mary case,” not claim direct human
   qualia evidence.
6. Draft only after the confirmatory results are available; retain all pilot
   runs and deviations in supplementary materials.

## Core references to start from

- Parslow, *The Law of Graphic Equalisation — Qualia and Consciousness
  Grounding* (existing conceptual paper in this repository).
- CIE 170-1:2006 and the CIE 2006 LMS cone fundamentals used in the pilot.
- Berent (2023), “The ‘Hard Problem of Consciousness’ Arises from Human
  Psychology,” for experimental studies of intuitions about Mary; treat its
  results as judgments about a vignette, not direct measurements of qualia.
- Hirao et al. (2025), “A neuroimaging dataset during sequential color qualia
  similarity judgments with and without reports,” for recent human fMRI and
  color-similarity data.
- Zimnicki & Rogers (2025), “Triadic comparisons reveal representational motifs
  in human color perception,” for individual variation and geometry of color
  similarity representations.
- Kind (2024), “What Counts as Cheating? Deducibility, Imagination, and the
  Mary Case,” and Morris (2025), “Acquaintance and Mary’s Revelation,” for
  current dispute over what Mary’s post-release epistemic gain amounts to.

## Execution status (2026-10-04)

All work was done in the worktree `/tmp/ocelot-marys-room`, branch
`experiment/marys-room-eye-qualia`, at HEAD `3649fb17`, with no commits. Engine
`b6a41e3bbba6`. Full results: `docs/experiments/marys-room-broad-results.md`.

**What ran:**

- **Phase 0–1:** pilot limits (`docs/experiments/pilot-limits.md`, which retires `48→28`) and the mechanism table (`docs/research/eye-mechanism-table.md`).
- **Phase 2:** the spectral forward model.
  - Code is `domains/spectral_forward.py`, with 38 tests in `tests/test_spectral_forward.py`.
  - CIE/CVRL and ColorChecker data are in `data/colour/`; their provenance is in `PROVENANCE.md`.
  - Amendment A0 is in the spec.
- **Phase 3:** prereg Amendment A1, the frozen manifest (721 entries, 626 distinct eye inputs), and Arm A.
  - These are hash-locked in `results/marys_room_broad_freeze.json`.
  - Phase 5 re-verified the lock: all files match, and the A1 prefix of the prereg matches. The A2 append is locked separately.
- **Arm B:** the eye run (`scripts/marys_room_broad.py`, which writes `results/marys_room_broad.json` and a per-stimulus CSV).
  - The pilot regression matches exactly.
  - The eye equals its documented formula to within 7e-16.
- **Arm C:** prereg Amendment A2 and the rate–distortion analysis (`scripts/marys_room_rate_distortion.py`, which writes `results/marys_room_rate_distortion.json` and CSVs).
- **Phase 5:**
  - An independent audit (`scripts/marys_room_broad_audit.py`) passed 19/19 headline checks, with no discrepancies.
  - A post-hoc boundary analysis (`scripts/marys_room_broad_boundary.py`) followed.

**Verdicts:**

- P1 (theory beats chance): mixed. The sign rule fails; the anchor decoder passes.
- P2 (eye agrees with theory except near the boundary): supported, though angular error is not elevated near the boundary.
- P3 (metamers broken): supported, 8/8.
- P4 (wrong observer/optics degrades theory): **not supported**. The 10° observer is closer to the eye's Gaussians than the 2° observer.
- P5 (closed eyelid gives positive RG): supported, 27/27. In independent Poisson trials, 1/10 flipped at 100 td.
- P6 (compression): **not supported** once codebook cost is charged (VQ 19.56 bits against raw 18.64). The fixed opponent basis, 12.42 bits, is the cheapest representation that meets the target.

**Headline figures:**

- Held-out theory↔eye median angle: 3.64°.
- Held-out eye anchor accuracy: 0.768; theory anchor accuracy: 0.702.
- Post-hoc finding: every RG sign disagreement and every metamer break comes from the Gaussian-vs-CIE sensitivity mismatch. Saturation dominates at high intensity.

**Open items:**

1. An independent review of the four arms and the results document.
2. Drafting the paper, with model-level claims only.
3. A decision on human psychophysics (Arm D.2). None was collected, so the title and abstract must say "eye model".
4. Committing the work if requested. `data/` and `results/` are gitignored, so they need `git add -f`.
5. Optional follow-ups. These are new preregistrations, not edits:
   - an Arm A with an adaptation model
   - von-Kries illuminant discounting for the illuminant-A failure
   - eyelid parameters matched to the cited mean OD of 2.1
