# PREREG — population ratio-invariance induction: the cross-frame sibling of within-signal ratio cancellation

**Committed BEFORE any number.** This expands a FUNDAMENTAL substrate capability;
it is not a competition entry. Judged by usefulness-at-a-price IN SHAPE, not by a
benchmark. Per CLAUDE.md: a held, transferable shape is the goal; the frame/
continuum invariant is the well-formedness constraint the build must satisfy.

## The capability (stated plainly)

OCELOT can APPLY held cross-frame maps (`DimInfer` selects from the fixed
generator table; `scale2` steps a ×2 log-scale) and can INDUCE one integer
generator from ONE orbit (`GenInfer`, `shape_decode.rs:2999`). It CANNOT induce
the invariant structure shared across a POPULATION of frames related by a
per-frame rescaling. "Subject-invariant representation" (EEG Challenge 2),
"speaker-invariant" (audio), "writer-invariant" (ink) are all the same demand:
induce, from many frames, the structure that is fixed as each frame's SCALE
varies. That faculty is the missing rung.

## The reframe that makes it well-formed: the invariant is a RATIO, not a projection

The EEG audit called the operator ABSENT because it read "remove the subject
frame" as a data-fitted CONTINUOUS PROJECTION — which the frame/continuum
invariant forbids in-frame. That framing is wrong. The correct shape is a RATIO,
and the substrate already privileges it (CLAUDE.md audio finding: "a rank or a
ratio is coherent in any base — the relation, not its decimal expansion; a ratio
cancels a common scale"). A subject/speaker/writer frame differs by MULTIPLICATIVE
factors (impedance/gain/scale). A ratio between coordinates WITHIN a frame CANCELS
the frame-scale. So:

- the invariant is the **cross-coordinate ratio structure** fixed as the per-frame
  scale varies;
- a ratio is a RELATION (intensional), not a stored continuous coordinate — it
  lives in `Hom(frame, invariant-frame)`, applied not stored, exactly where the
  invariant sanctions continuous structure; in-frame stays integer (observed
  magnitudes / ranks), the ratio is the map;
- this IS the `scale2` / base-as-dimension line already landed (`shape_decode.rs:722`),
  lifted from a fixed ×2 on one orbit to an INDUCED ratio set across a population.

So the price is near-zero tension with the invariant: a ratio is the sanctioned
intensional cross-frame object. The build uses the invariant, not fights it.

## The rung (what is built)

A population ratio-invariance induction op — the cross-frame, population-level
sibling of `GenInfer`. Given a POPULATION of frames (each a set of integer
coordinate observations) that share latent ratio structure under per-frame
multiplicative rescaling, INDUCE the invariant ratio set (the cross-coordinate
ratios that hold across all frames) and mint it as a `latent:ratio` /
held-ratio-map object in `Hom` — intensional, integer-observable. Reuses the
`DimensionGenerator`/`LatentDimension` node types + the `scale2` ratio machinery
+ `GenInfer`'s induce-from-orbit pattern, lifted to induce-from-population.

## Hypotheses (falsifiable, pre-declared)

- **H-R1 (mechanism — synthetic, clean ground truth):** on a SYNTHETIC population
  with a PLANTED invariant ratio structure and per-frame random scales, the op
  INDUCES the planted ratios (recovers the cross-coordinate ratio set that was
  fixed across frames), and the induced map, APPLIED, collapses the population
  onto its shared invariant. CONFIRMED iff the recovered ratio set matches the
  planted one (within observation resolution) and residual per-frame scale is
  cancelled. NULL iff it cannot recover a planted ratio from a population —
  the mechanism doesn't work, reported as headline.

- **H-R2 (well-formedness — the invariant is respected):** the induced object is
  a RATIO held in `Hom` (intensional), NOT a continuous in-frame coordinate;
  in-frame coordinates stay integer; the observable is the stepped rendering.
  CONFIRMED iff no continuous coordinate is stored in-frame (the induced map is a
  relation applied on read, `coord_ints` still refuses floats). This is the price
  check: if inducing-from-population REQUIRES storing continuous in-frame state,
  the price is "violate the foundational invariant" — too high — and that is the
  finding (a real boundary of what the invariant permits).

- **H-R3 (usefulness in shape — transfers to a real body):** on the AUDIO
  scale-frame case the stack already proves ratios cancel the carrier
  (source/filter separation, log-multiplicative), the INDUCTION faculty recovers
  the speaker/carrier-scale invariance ACROSS a population of utterances WITHOUT
  it being hand-built — i.e. the same rung that solved the synthetic planted case
  produces a known-real invariance on a real body. CONFIRMED iff the induced
  ratio-invariant separates carrier-scale from content on the audio population as
  the held audio ratio machinery does by construction. This is usefulness-at-a-
  price measured in shape on a body with known ground truth.

- **H-R4 (the EEG restatement — stated, not run here):** subject = scale-frame;
  subject-invariant representation = the induced cross-channel/cross-band ratio
  manifold fixed across the subject-scale. The residual that NO ratio cancels is
  either genuine invariant signal or non-multiplicative nuisance — the split is
  the well-formed refusal ("compute ratios, refuse absolute magnitudes"). This
  hypothesis is the TRANSFER TARGET the capability unlocks; it is NOT run in this
  arc (HBN-EEG multi-TB unreachable, per the audit) — it is stated as the body
  the rung applies to, and its runnability is a future-data question, not a
  blocker for building the capability.

## What each outcome MEANS (pre-committed)

- **H-R1 ∧ H-R2 ∧ H-R3** → the capability exists, is well-formed (ratio in `Hom`,
  invariant respected), and transfers to a real body. The substrate now INDUCES
  cross-frame invariances, not just applies held ones — a fundamental capability
  on the base-as-dimension ladder, general across bodies (EEG/audio/ink/vision).
- **H-R2 fails (needs continuous in-frame state)** → inducing-from-population
  cannot be done as a ratio-in-`Hom`; the price is a foundational-invariant
  violation. Report as the boundary: this class of invariance is not
  well-formedly inducible in the current substrate, here is exactly why.
- **H-R1 or H-R3 null** → the ratio framing does not recover the planted/real
  invariance (the frame is not purely multiplicative, or ratios are insufficient).
  Report the residual — the part of the frame no ratio cancels — as the finding.

## Method / discipline

- Build on the REAL machinery: `GenInfer`/`DimInfer` (`shape_decode.rs`), the
  `scale2`/`DimensionGenerator`/`LatentDimension` types, `apply_generator_once`.
  Add the population-induction op as a Rust term + `py.rs` one-line handoff on the
  existing crate/wheel path; do NOT fork.
- Synthetic body FIRST (planted ratios, known ground truth — clean mechanism),
  audio body SECOND (real, known invariance — usefulness in shape). EEG stated,
  not run.
- The frame/continuum invariant is the gate: induced map is a ratio (relation) in
  `Hom`, applied intensionally, in-frame stays integer. H-R2 is the price check
  and a failure there is a real finding, not a workaround target.
- PREREG-then-measure; nulls are findings; usefulness-at-a-price reported in shape
  (what the capability does + what it costs against the invariant), not as a score.

## Deliverables

- `RATIO_INVARIANCE_RESULTS.md` — H-R1 (synthetic recovery), H-R2 (invariant
  respected / price), H-R3 (audio transfer), H-R4 (the EEG restatement stated),
  and the usefulness-at-a-price-in-shape ledger.
- the Rust population-ratio-induction op + `py.rs` handoff + the synthetic and
  audio exercise harnesses. Reuse the crate/wheel path; invariant respected.

---
MEASUREMENT GATE — nothing above this line is edited once numbers exist.
