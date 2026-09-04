# RATIO_IN_REASONING.md — where RatioInduce adds value in OCELOT's reasoning/logic/inference layer (NOT the signal bodies)

Assessment of where the built `RatioInduce` capability (population cross-frame
ratio-invariance induction, `runners/dsl/src/shape_decode.rs::eval_ratio_infer`)
adds value in the COGNITIVE machinery — reasoning, logic, inference — as opposed
to the signal bodies (audio/EEG/ink/vision) it was exercised on. Every claim
grounded in code read this session. The honest finding is LOCALISING: one real
reasoning-layer unlock, the rest stretches, for one recurring verifiable reason.

## HEADLINE (the single highest-value cognitive site)

**The sd/decode loop's redundant-quantum collapse (`seeds/shape_decode_loop.json`
+ `shape_decode.rs`) is the ONE genuine reasoning-layer unlock** — genuine only
because it is the SAME base-as-dimension ladder RatioInduce already lives on,
lifted from one-orbit to population. Everything higher in the cognitive stack
(analogy, concept formation, grounding, forecasting) is PARTIAL or a stretch,
because the reasoning layer's core objects (`Concept` shape-vectors, grounding
marginals, regime bands) are NOT populations-of-integer-coordinate-frames-
related-by-multiplicative-scale — the exact and only shape `eval_ratio_infer`
consumes (`coord_ints` refuses `Float`; it reads origin-normalized integer
extents `max−min` per coord slot across frames). Brutal truth: **the reasoning
layer largely has no population-of-scale-frames shape, so most of RatioInduce's
value stays in the signal bodies.**

## RANKED CANDIDATE VALUE-SITES

### 1. sd/decode loop — redundant-quantum collapse across scale-frames — PARTIAL → genuinely UNLOCKED (multiplicative case only)
- **Where:** `seeds/shape_decode_loop.json` growth ladder (`sd_recognize` →
  `sd_transform_decode` → `sd_infer_dimension` → `sd_mint_quantum`);
  `eval_ratio_infer` mints `latent:scale2` (pow2) or a diagonal `kind:"linear"`
  matrix read by `apply_linear_once` — zero new dispatch arm, the same property
  `scale2` has.
- **Unlocks:** today the ladder collapses ONE orbit's magnitude family via
  `DimInfer`/`scale2`; `sd_transform_decode` reads a per-dim delta for a SINGLE
  observation. It has no POPULATION rung: when the SAME structure recurs across N
  contexts each at a different multiplicative magnitude and no held generator
  fits, the ladder falls through to `sd_mint_quantum` — N redundant quanta.
  RatioInduce is the missing population sibling of `GenInfer`: induce the
  invariant ratio from the whole population, mint ONE held shape + one
  `latent:ratio`/`latent:scale2` dimension. The cognitive-level lift of the
  "a whole scale family collapses to one held shape + one dimension — grows
  capability AND improves efficiency" win.
- **Price in shape:** BUYS efficiency (N quanta → 1) + generalisation (a "big X"
  and "small X" become one X under a minted scale dimension). COSTS a seed rung
  (`sd_infer_ratio`) wiring RatioInduce in BEFORE `sd_mint_quantum`, AND a
  population-assembly step (a set of same-signature Observations differing in
  extent) that the one-observation-at-a-time loop does not have today. RESPECTS
  the invariant fully (H-R2). Bounded scope: multiplicative differences over
  integer coordinate slots only.
- **Verdict:** PARTIAL today (single-orbit magnitude via `scale2`/`DimInfer`),
  genuinely UNLOCKED for the population case. A real, bounded unlock.

### 2. Analogical reasoning / proportional analogy A:B :: C:D — STRETCH (surface mismatch)
- **Where:** `domains/analogical_thinking.py::_pair_witness` (the `AntiUnifyWitness`
  `transform`/parallelogram) over `_concept_shape_vector`.
- **Seductive but wrong-shaped:** proportional analogy IS a ratio-invariance
  across two frames on paper. But the analogy "transform" is a SYMBOLIC
  categorical residue over discrete vocabulary axes (`role:`/`principle:`/`shape:`
  pairs, canonicalised to a `transform_key` string) — NOT a numeric cross-
  coordinate ratio over integer extents. Concept vectors have no numeric
  coordinate to take an extent of. The parallelogram delta and the induced ratio
  are different-shaped objects; connecting them needs a numeric-magnitude concept
  embedding that does not exist.
- **Verdict:** EXISTS-today-without-it for the symbolic case; UNAVAILABLE (out of
  shape) for numeric proportional analogy unless the quantitative-analogy body is
  built first. A stretch.

### 3. Concept formation / magnitude-invariance of identity — STRETCH (same numeric-coordinate absence)
- **Where:** `domains/concept_promotion_rules.py`, concept vectors via
  `analogical_thinking._concept_shape_vector`.
- **Why stretch:** a `Concept` is a symbolic relation-vector, not a set of
  integer-coordinate frames; no per-instance multiplicative scale lives anywhere
  for RatioInduce to cancel. The magnitude-invariance-of-identity idea is real
  cognitively but the substrate does not carry the scaled numeric coordinates the
  operator requires.
- **Verdict:** UNAVAILABLE (out of shape) unless concepts gain a numeric
  magnitude-coordinate representation. A stretch.

### 4. Quantitative / proportion / dimensionless-ratio reasoning — UNLOCKED capability, NO existing consumer
- **Where:** searched — the only numeric-ratio machinery is in signal/measurement
  bodies (`domains/math_hat.py`, `scripts/snap_run.py`), not a general
  dimensional-analysis / unit-conversion / proportion logic faculty. None exists.
- **Read:** IF a proportion/rate/dimensionless-quantity reasoner existed,
  RatioInduce is exactly its induction engine. There is no such faculty to plug
  into. Latent value, no current site — "build the faculty and RatioInduce is its
  engine," not "existing faculty gets sharper."

### 5. Grounding / CAN layer — cross-frame groundedness comparison — STRETCH (wrong algebra)
- **Where:** `domains/grounding_theory.py` + `causal_attitude_networks` (grounding
  = marginal ⟨σ⟩ of an Ising/attractor network).
- **Why stretch:** cross-frame groundedness comparison is about coherence/
  attitude-strength — an ADDITIVE/energy quantity (couplings J, field h, β) — not
  a per-frame MULTIPLICATIVE rescaling of integer coordinate extents. No
  population of scale-frames. The ratio shape does not fit the grounding algebra.
- **Verdict:** EXISTS-today-without-it. A stretch.

### 6. Forecasting / Seldon regime frames — STRETCH (regimes are ADDITIVE bands)
- **Where:** `drafts/seldon_t2_text/ingest.py`, `corpus_gen.py`,
  `run_calibration_eval.py`.
- **Why stretch:** a "regime" is an ADDITIVE band-shift on integer cells (a signed
  level shift toward a band), NOT a per-regime multiplicative scale on shared
  coordinates. RatioInduce cancels a multiplicative nuisance; a regime shift is
  additive. The one multiplicative object (`disp_scale`) is a calibration knob
  already scale-invariant by design, needing no induction. "regime = scale-frame"
  is a false equation for this codebase.
- **Verdict:** EXISTS-today-without-it. A stretch, honestly reported.

## BOTTOM LINE (the localising finding)

RatioInduce's one honest reasoning-layer unlock is **#1**: a population rung for
the sd/decode loop so N recurrences of one structure at different multiplicative
magnitudes collapse to one held shape + one minted scale dimension instead of N
quanta — the direct cognitive-level lift of the `scale2` efficiency+generalisation
win, same ladder, near-zero invariant cost. PARTIAL (single-orbit collapse
already exists), bounded to multiplicative differences over integer-coordinate
frames.

Everywhere higher in the cognitive stack the operator is a STRETCH, for one
recurring verifiable reason: **the reasoning layer's objects are not populations-
of-integer-coordinate-frames-related-by-multiplicative-scale.** Analogy matches
symbolic vocabulary residues (the parallelogram is categorical, not numeric);
concepts have no scaled numeric coordinates; grounding is an additive network
marginal; forecasting regimes are additive bands. So RatioInduce's real,
transferable value remains where it was exercised: the signal bodies, whose
per-frame carriers / impedances / vocal-tract-sizes / writer-scales ARE genuine
multiplicative nuisances on integer-observable coordinates. That is the truth of
it, not manufactured value.

### The one caveat worth holding for later
Sites 2/3/4 all fail for the SAME reason — no numeric magnitude-coordinate in the
cognitive objects. That is itself a locating finding: IF a future rung gave
concepts/analogies a numeric magnitude coordinate (a "how much" axis alongside
the symbolic "what"), RatioInduce would immediately become the invariance engine
for proportional analogy, magnitude-invariant concept identity, and dimensionless
reasoning at once. The missing piece is not RatioInduce — it is the numeric-
magnitude representation the reasoning layer does not yet carry. That is the real
next-capability question the reasoning layer poses, surfaced by this assessment.
