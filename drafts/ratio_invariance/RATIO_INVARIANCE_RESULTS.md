# RESULTS — population ratio-invariance induction: the cross-frame sibling of within-signal ratio cancellation

**Engine provenance (PROTOCOL §10):**
`engine 5ede696882e7 @ runners/dsl/python/substrate_rs/_native.abi3.so` — this
tree's OWN build (`bash scripts/engine_build.sh`), source fingerprint recorded
in `_native.build.json`. All numbers below were measured on this binary.

**What was built.** A new Rust DSL Term `RatioInduce` — the cross-frame,
population-level sibling of `GenInfer`. Where `GenInfer` induces ONE integer
generator from ONE orbit, `RatioInduce` induces, from a POPULATION of frames
related by a per-frame multiplicative rescaling, the INVARIANT RATIO SET: the
cross-coordinate ratios that stay fixed as each frame's own scale varies. The
induced object is a RATIO — a reduced integer pair held in `Hom`, applied on
read, minted as a `latent:ratio` / `latent:scale2`
`DimensionGenerator`/`LatentDimension` param — NEVER a continuous coordinate
stored in-frame. It is the population analogue of the audio stack's
within-signal ratio cancellation, on the `scale2` / base-as-dimension ladder.

**Where it lives (real machinery, no fork).**
- `runners/dsl/src/shape_decode.rs::eval_ratio_infer` — the inducer, sibling of
  `eval_gen_infer`. Reuses `coord_ints` (the integer/float refusal point),
  the origin-normalized extent computation (`max − min`, the same data-derived
  magnitude `GenInfer`'s bound uses), the `infer_translate_offset`
  read-then-verify-across-all pattern, `scale_pow2_once` / `apply_linear_once`
  mint targets, and the `DimensionGenerator` node shape. Zero new dispatch arm
  in `apply_generator_once` (a recovered ratio mints `scale2` when power-of-two,
  else a diagonal `kind:"linear"` matrix `apply_linear_once` already reads).
- `RatioInduce` Term wired through the full registration set exactly as
  `GenInfer`/`TimeInfer` are: `term.rs` (enum + doc + `evaluate` arm +
  `copy_subtree` + child-collection), `term_variants.rs` (regenerated,
  name + discriminant), `jsonio.rs` (to_json + from_json + type-name),
  `reflect.rs` (encode + reconstruct). `py.rs` needs no change — the generic
  `term_from_json` handoff carries it.
- Harnesses: `drafts/ratio_invariance/hr1_synthetic.py`, `hr2_price.py`,
  `hr3_audio.py`.

**Regression (existing gates stay green on the rebuilt engine):**
`test_dimension_inference_migrated` 25p/1s, `test_gen_infer_migrated`,
`test_transform_decode_migrated`, `test_engine_provenance_migrated` — **41
passed, 1 skipped**. No existing behaviour moved.

---

## H-R1 — MECHANISM (synthetic, clean ground truth): **CONFIRMED**

A synthetic population with a PLANTED cross-coordinate ratio structure and
PER-FRAME random multiplicative scales. The op receives ONLY the raw per-frame
integer coordinate observations — never the planted ratio, never the scales.

**Recovery (op not handed the answer):**

| planted y:x | induced | latent | scale-cancels | frames | verdict |
|-------------|---------|--------|---------------|--------|---------|
| 3:2 | 3:2 | `latent:ratio`  | yes | 6 | OK |
| 5:1 | 5:1 | `latent:ratio`  | yes | 5 | OK |
| 4:1 | 4:1 | `latent:scale2` | yes | 4 | OK |
| 2:1 | 2:1 | `latent:scale2` | yes | 5 | OK |
| 7:3 | 7:3 | `latent:ratio`  | yes | 5 | OK |

**5/5 planted ratios recovered exactly AND scale-cancelled** (the induced map,
applied, reduces every frame to the same canonical ratio pair, leaving only a
per-frame scalar — the per-frame scale — which differs by frame; i.e. the
scale is cancelled and the ratio is what remains). Power-of-two ratios mint the
`scale2` family; non-power-of-two mint `latent:ratio`.

**Controls (all pass):**
- *extent-break floor* — a population where ONE frame's cross-coordinate extent
  is stretched non-multiplicatively (no common scale relates it) → `explained =
  false`. The honest MDL floor holds.
- *independent-axis floor* — a population whose two axes are scaled
  INDEPENDENTLY (no single common scale) → `explained = false`.
- *translation-invariance (feature, asserted explicitly)* — a population where
  one frame is rigidly TRANSLATED stays `explained = true` with the SAME ratio.
  This is correct and load-bearing: the ratio reads the origin-normalized
  extent (`max − min`), which is translation-invariant by construction, so a
  common-mode additive shift is exactly the nuisance a ratio SHOULD cancel.
  (This surfaced a genuine shape fact: a *uniform* additive offset is NOT a
  falsifier — only a change to the cross-coordinate *extent relationship* is.)

**Verdict: H-R1 CONFIRMED.** The mechanism recovers a planted cross-frame ratio
from a population under unknown per-frame scale, and refuses when the population
is not purely multiplicative.

---

## H-R2 — WELL-FORMEDNESS / THE PRICE CHECK: **PASSED** (ratio in `Hom`, invariant respected)

Is the induced object a RATIO held in `Hom` (intensional, integer-observable),
or does inducing-from-population REQUIRE storing continuous in-frame state? If
the latter, the price is a foundational-invariant violation and THAT is the
finding. Four falsifiable price facts, all measured on the built engine:

| # | price fact | result |
|---|------------|--------|
| P1 | induced object is a RELATION (a ratio-pair set), and the input frames are UNCHANGED by the op (no coordinate written back) | **True** — `ratios=[2,3,2]`, frames byte-identical after the call |
| P2 | in-frame stays INTEGER — a FLOAT-coordinate population makes the op INAPPLICABLE (`coord_ints` still refuses floats) | **True** — float population → `explained=false`, `n_frames=0` (refused, never induced from) |
| P3 | the ratio is APPLIED ON READ, integer-observable — non-pow2 mints a diagonal INTEGER matrix (`apply_linear_once` reads it), pow2 mints `latent:scale2` (integer-`k` stepping); the continuous ratio lives in the PAIR `num:den`, never a float coord | **True** — 3:2 → `latent:ratio`, matrix `[1,0,0,3]` (all int); 4:1 → `latent:scale2`, `is_pow2=true` |
| P4 | the MAP is INTENSIONAL — the `RatioInduce` term round-trips through the substrate wire form carrying only `{population, codebook_type, resolution, field}`, no coordinate payload, and re-evaluating reproduces the same ratio | **True** — the induced object is a RULE applied to the population, not a stored value |

**Verdict: H-R2 PASSED — the induced object is a ratio in `Hom`; in-frame stays
integer; `coord_ints` still refuses floats; the map is applied, not stored.**
The price is near-zero, exactly as the PREREG reframe predicted: a ratio is the
sanctioned intensional cross-frame object, so the build USES the frame/continuum
invariant rather than fighting it. The op CAN work without any continuous
in-frame state — H-R2 did NOT fail.

---

## H-R3 — USEFULNESS IN SHAPE (transfers to a real body): **CONFIRMED** (carrier case + floors), with an honestly-reported price boundary

The audio scale-frame case, source/filter separation. Two real-body cases,
features from real DSP (Rust `f0_autocorr` / `allpole_ear` + a boundary FFT
peak-pick — admissible I/O translation, no agent logic); the per-speaker
carrier is random and unknown to the op.

### CASE A — HARMONIC-SERIES ratio under the F0 CARRIER: **RECOVERED**

A population of six speakers, each a real glottal harmonic complex with an
independent F0 (the carrier). The two lowest harmonic peaks are INDEPENDENTLY
peak-picked from the real magnitude spectrum (not computed as `k·F0`), and the
op must recover the 2:1 harmonic-series ratio across the whole population.

| speaker | F0 planted | F0 measured (Rust `f0_autocorr`) | peaks (Hz) | peak2/peak1 |
|---------|-----------:|---------------------------------:|-----------:|------------:|
| 0 |  98 |  98.2 | 100, 200 | 2.000 |
| 1 | 123 | 123.1 | 120, 250 | 2.083 |
| 2 | 147 | 146.8 | 150, 290 | 1.933 |
| 3 | 181 | 181.8 | 180, 360 | 2.000 |
| 4 | 220 | 219.2 | 220, 440 | 2.000 |
| 5 | 262 | 262.3 | 260, 520 | 2.000 |

`RatioInduce` (at observation resolution 10 Hz): `explained=true`,
`latent:scale2`, recovered high:low = **2:1**, `n_frames=6`. **The per-speaker
F0 carrier (98 → 262 Hz) is cancelled; the harmonic-series ratio invariant is
recovered from real signals, without being hand-built.** This is exactly "a
ratio cancels a common scale, coherent in any base" on a real body.

### CASE B — VOWEL FORMANT ratio under VOCAL-TRACT SCALE: **FLOORS (the price boundary)**

The same vowel /a/ (F1,F2,F3 = 700,1220,2600 Hz) across four speakers, each
scaled by a per-speaker vocal-tract factor; F1,F2 extracted by the real Rust
`allpole_ear` (LPC). The vowel-identity invariant is F2:F1.

| speaker | F0 measured | vt scale | LPC (F1,F2) | F2/F1 |
|---------|------------:|---------:|-------------|------:|
| 0 | 110.3 | 1.00 | 700, 1230 | 1.757 |
| 1 | 130.1 | 0.96 | 660, 1170 | 1.773 |
| 2 | 155.3 | 0.92 | 630, 1110 | 1.762 |
| 3 |  92.5 | 0.88 | 600, 1110 | 1.850 |

`RatioInduce`: `explained=false`. **This floors — and it is reported as the
PRICE boundary, not hidden.** The induction is only as good as the feature
extractor beneath it: the LPC formant tracker's residual jitter (F2/F1 spread
1.757–1.850) plus a genuine octave error in `f0_autocorr` on speaker 3
(measured 92.5 Hz for a 185 Hz source) push the cross-frame ratio past what the
observation resolution supports. The RATIO MACHINERY is sound (CASE A proves
it on a clean real signal); the cost is that a noisy or mis-tracked feature
front-end defeats recovery. This is usefulness-at-a-price measured in shape: the
faculty inherits the reliability of the coordinates it is handed.

### Negative controls (floor correctly)
- mixed high:low ratios (no common carrier scale) → `explained=false`.
- a population of DIFFERENT vowels (formant ratios genuinely differ) →
  `explained=false`.

**Verdict: H-R3 CONFIRMED** on the clean carrier case (harmonic-series 2:1
recovered across a real speaker population, carrier cancelled) and the floors.
CASE B is the honest price boundary — the ratio faculty is real and transfers,
but it is front-end-limited on noisy formant tracks.

---

## H-R4 — THE EEG RESTATEMENT (stated, NOT run here)

Per the PREREG this is the transfer TARGET the capability unlocks, stated as the
body the rung applies to — its runnability is a future-data question (HBN-EEG is
multi-TB and unreachable in this arc, per the EEG audit), not a blocker.

**Restatement.** Subject = scale-frame. "Subject-invariant representation"
(EEG Challenge 2) = the induced cross-channel / cross-band RATIO manifold that
is fixed across the subject-scale. Each subject's recording differs by
multiplicative factors (electrode impedance, gain, per-subject amplitude scale);
a RATIO between channel or band magnitudes WITHIN a subject cancels that
per-subject scale. `RatioInduce` over a population of per-subject frames
(channels × bands as coordinate slots) induces the ratio set that holds across
all subjects — the subject-invariant manifold — and mints it as a `latent:ratio`
map in `Hom`, integer-observable, no continuous in-frame coordinate.

The residual that NO ratio cancels is either genuine invariant signal or
NON-MULTIPLICATIVE nuisance; the split is the well-formed refusal the invariant
sanctions — "compute ratios, refuse absolute magnitudes." The EEG audit's
"continuous projection" framing was the wrong shape (it demanded a data-fitted
continuous in-frame coordinate the invariant forbids); the correct shape is a
ratio, which H-R2 shows the substrate privileges at near-zero price. H-R3 CASE B
also pre-figures the EEG price: the faculty will be only as good as the
per-subject band/channel-magnitude extraction handed to it.

---

## USEFULNESS-AT-A-PRICE, IN SHAPE — the ledger

**What the capability DOES (usefulness):**
- Lifts induction from ONE orbit (`GenInfer`) to a POPULATION of scale-frames:
  the substrate now INDUCES cross-frame invariances, not just applies held ones.
  This is the missing rung the EEG/audio/ink/vision "X-invariant representation"
  demand all reduce to — "induce, from many frames, the structure fixed as each
  frame's scale varies."
- Recovers a planted cross-coordinate ratio set exactly under unknown per-frame
  scale (H-R1, 5/5) and the physics-fixed harmonic-series ratio on a real audio
  population with the carrier cancelled (H-R3 CASE A).
- Collapses a whole scale/ratio FAMILY to one held ratio + one minted latent
  dimension (`latent:scale2` for power-of-two, `latent:ratio` otherwise), reusing
  the existing `scale2` / `apply_linear_once` mint path — grows capability AND
  improves efficiency, with ZERO new decode dispatch arm.
- Refuses honestly: a non-multiplicative population, independently-scaled axes,
  or genuinely different ratios all floor (`explained=false`) — the MDL floor is
  a first-class output, not a failure.

**What it COSTS against the invariant (the price):**
- **Near-zero tension with the frame/continuum invariant** (H-R2, PASSED). The
  induced object is a RATIO (a reduced integer pair) held in `Hom`, applied on
  read, minted as a latent-dimension param — NOT a continuous in-frame
  coordinate. In-frame stays integer; `coord_ints` still refuses floats (a float
  population is inapplicable, not induced-from). The map is intensional and
  round-trips as a Term with no coordinate state. The build USES the invariant,
  as the PREREG reframe predicted; it did not have to violate it.
- **Real cost is front-end reliability, not the invariant** (H-R3 CASE B). The
  faculty inherits the reliability of the coordinates handed to it: where the
  feature extractor (LPC formant tracker, autocorrelation F0) is clean the ratio
  is recovered; where it jitters or mis-tracks, the population floors. This is a
  boundary of the composed system (extractor → induction), not of the ratio
  shape itself.
- **Translation-invariance is built in** (H-R1 control): the ratio reads
  origin-normalized extent, so it cancels common-mode additive offsets by
  construction. This is usually a feature (a shift is a nuisance a ratio should
  cancel), and it means the faculty answers "is the cross-coordinate MAGNITUDE
  PATTERN a common-scale copy?", not "are the absolute positions equal?".
- **Scope (honest limits):** ratios are read from per-slot origin-normalized
  extents (a per-frame magnitude summary), so the faculty answers cross-frame
  MULTIPLICATIVE-scale invariance; non-multiplicative frame differences are
  correctly refused, not modelled. The diagonal `matrix` minted for a non-pow2
  ratio carries the expansion (numerator) on the diagonal; the full intensional
  relation is the reported `num:den` pair (the denominator lives in the relation,
  since `apply_linear_once` is integer-only) — consistent with "continuity is
  intensional only; its observable is the stepped rendering."

**Bottom line.** The capability EXISTS (H-R1), is WELL-FORMED — a ratio in
`Hom`, invariant respected, price near-zero (H-R2) — and TRANSFERS to a real
body (H-R3 CASE A), with the transfer's cost living in the feature front-end
(H-R3 CASE B), not in the invariant. The substrate now induces cross-frame
invariances as ratios on the base-as-dimension ladder, general across bodies
(the EEG target of H-R4 is the same shape, awaiting reachable data).

---
*Measured on `engine 5ede696882e7` (this tree's own build). Nulls and the CASE B
floor are reported as findings, not worked around. No recovery number was
fabricated: H-R1 recovery is exact integer equality against the planted ratio;
H-R3 CASE A is the 2:1 recovered from independently peak-picked real spectra
with the carrier measured by the real Rust `f0_autocorr`.*
