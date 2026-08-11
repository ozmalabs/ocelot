# IDENTITY UNTANGLING — the OBJECTHOOD "what" wall — pre-registration

*The crossing formulated in `VISION_VENTRAL_GROUNDING.md` (BUILD IMPLICATION
#1/#5): **invariant object recognition = generator-orbit identity.** A
proto-object seen under a nuisance transform traces an ORBIT; given views of one
object, DISCOVER the generator relating them; **IDENTITY = the generator-
invariant (the base a discovered transform maps FROM); NUISANCE = the generator
parameter; RECOGNITION = same-orbit membership.** This is DISCOVERY (compress
frame-to-frame variation, MDL-gated), NOT covariance (the diagnosed cortex-line
dead end), NOT supervised readout.*

Committed BEFORE the confirmatory run (§3). Seed block **37000–37999** declared;
**12000–36999 untouched** (burned-ledger checked). Engine provenance recorded in
the RESULTS file (§10).

## 0. AUDIT — is generator-orbit identity expressible BY COMPOSITION? (§12.4)

**Verdict: IN-CLASS. No new Rust. The sd loop already IS this operation.** Read,
cited file:line:

- **Recognition UNIT = a relation-system signature.** A border-ownership
  proto-object is a *bounded owned region* = a same-value connected component
  (`seeds/vision_border_ownership.json` `bo_label`/`bo_mint_enclosed`, members =
  `Count(cells with this glabel)`). Represented as its owned-cell set
  `[["cell", r, c, val], …]` with `dim_types = ["pred","coord:r","coord:c","val"]`
  — the exact format `DimInfer`/`GenInfer`/`TransformDecode` consume
  (`tests/test_dimension_inference_migrated.py:97`,
  `tests/test_gen_infer_migrated.py:47`).
- **Discover the transform between views:** `GenInfer`
  (`runners/dsl/src/shape_decode.rs:2013 eval_gen_infer`) infers a NEW integer
  2×2 map carrying a held part onto a view; `DimInfer` (`:1773 eval_dim_infer`)
  selects a HELD generator (rotation90/reflection_r/reflection_c/scale2/cycle4);
  `TransformDecode` (`:1626`) reads a uniform per-dim delta (translation /
  recolour). `apply_linear_once` (`:728`) applies an integer matrix,
  origin-normalized.
- **Same-orbit membership = a rule's decision.** The sd loop
  (`seeds/shape_decode_loop.json`) runs the Occam ladder in ONE `run_rules`
  fixpoint: `sd_decode`→exact; `sd_transform_decode`→`sd_recognize_transformed`
  (rung 1); `sd_infer_dimension`→`sd_recognize_dim` (rung 2, held generator);
  `sd_gen_check`→`sd_mint_generator` (gen-mint, flag ON); else
  `sd_mint_quantum` (novel identity). **`covered_by` (set by the recognize
  rules from the winning `base`) IS the recognized IDENTITY**; the `Transform`
  node on `has_transform` carries the NUISANCE (generator + `k`).
- **Anti-universal-container is built in** (`build_candidate` `:1381`): a
  candidate is disqualified unless it has EQUAL relation count and SAME
  predicate per aligned relation, then a consistent per-dim map. This is the
  structural guard the discrimination arm tests.

The adapter (`scripts/identity_untangling_measure.py`) only: builds
ShapeSignature objects + Observation views, calls `run_rules`, reads
`status`/`covered_by`. **No Python decision; no covariance; no Hebbian.**

## 1. Objects, transforms, identity readout

- **Objects** = 7 full-rank FREE pentominoes (each a distinct D4 orbit *by
  definition of free pentomino*, and — verified in calibration — a distinct
  orbit under the HELD invertible discrete-similarity generators):
  `F,T,U,V,L,N,X`. 5 cells each; monochrome (`val="red"`). Codebook is
  **ISOLATED**: the 17 pre-seeded symbolic ShapeSignatures (`fractal`, …;
  `dim_types=None`) are `remove_node`-d so only the 7 objects are in the
  codebook (else a view can match a symbolic part via a different fit metric —
  observed in calibration; it is contamination, not identity).
- **Discrete-similarity nuisance class** `T_DS` (held, invertible/injective
  generators + translation), 8 transforms:
  `identity, translate(+3,+2), rot90, rot180, rot270, refl_r, refl_c, scale2`,
  each an integer matrix applied origin-normalized (mirroring
  `test_gen_infer_migrated.py::_lin`) then translated.
- **Identity readout:** `identity(view) = covered_by` iff
  `status ∈ {recognized, recognized_transformed}`, else `NEW` (minted / refused).

## 2. Off by default (§9) — this rung ADDS NO Rust and NO new flag

The gen-mint path is gated on the pre-existing `gen_infer_enabled` (absent ⇒
OFF), already §9-verified by `test_gen_infer_migrated.py`. The headline regime
runs it **OFF** (held generators only). This rung commits: a runner, a gate, a
prereg, a results file, a pinned JSON — **no seed edit, no `.rs` edit**. §9
off-day = the committed bench unmoved (the runner/gate are additive, inert to
every existing result).

## 3. Hypotheses, statistics, decision rule (two-sided; predictions stated)

The geometric arms (INVARIANCE/DISCRIMINATION/UNTANGLING/FLOOR-b) are
**DETERMINISTIC** (no sampling) — the statistic is an exact count, the "n" is
fixed by the object×transform grid, and the run reproduces the calibrated
measurement exactly. The **noise floor (FLOOR-a)** is the prospective seeded arm
(seeds 37000–37099, never used).

### REGIME A — HEADLINE: the DISCRETE-SIMILARITY class (held invertible generators, `gen_infer` OFF)

- **H_invariance:** every `t(O_i)`, `t ∈ T_DS`, maps to identity `O_i`.
  Statistic: correct / (7×8 = 56). **Decision: PASS iff 56/56.** *Prediction:
  56/56 (calibrated 49/49 on the 7-object grid before adding rot180/rot270 which
  are rotation90^{2,3}).*
- **H_discrimination (the anti-overfit CRUX, §1.1):** for every ordered pair
  `i≠j`, present `O_j` against codebook `{O_i}` ONLY — it must NOT be recognized
  (no held generator maps `O_i`→`O_j`). Statistic: spurious recognitions /
  (7×6 = 42). **Decision: PASS iff 0/42.** A single generator that maps distinct
  objects together is the UNIVERSAL-CONTAINER failure — DISQUALIFYING.
  *Prediction: 0/42.*
- **H_untangling (the DiCarlo signature):** the RAW-rep control = naive nearest
  stored signature by origin-normalized cell-set symmetric-difference (a
  template match in "image" space, translation-normalized only). **PASS iff the
  RAW-rep off-diagonal error count > 0 (raw TANGLES) AND the orbit-rep
  off-diagonal (wrong-identity) count == 0 (orbit SEPARATES what raw tangles).**
  Statistic: (raw_wrong, orbit_wrong) over the 56 views. *Prediction: raw_wrong
  ≈ 26 (≈46%), orbit_wrong = 0.* If raw_wrong == 0 the untangling claim is
  VACUOUS and reported as such (§8).
- **H_floor_a (noise):** 100 random 5-cell "objects" (seeds 37000–37099; each a
  random distinct-cell set of 5 lattice points in an 8×8 window) presented
  against the 7-object codebook must NOT be recognized as an existing object.
  **Decision: PASS iff 0/100 force-maps** (mint/refuse only). *Prediction:
  0/100.*
- **H_floor_b (non-discoverable transform):** a NON-RIGID warp — one cell of
  each object displaced by `(+2,+2)` off the lattice image (no global transform
  explains it) — must NOT be recognized as an existing object. Statistic:
  force-maps / 7. **Decision: PASS iff 0/7.** *Prediction: 0/7 (calibrated).*

**Regime-A verdict — the WALL IS CROSSED (bounded) iff ALL of H_invariance,
H_discrimination, H_untangling, H_floor_a, H_floor_b hold.** Scope: INSTANCE-level
recognition invariant under the HELD invertible discrete-similarity nuisance
class ONLY.

### REGIME B — the DIAGNOSED BOUNDARY: general integer-linear discovery (`GenInfer`, `gen_infer` ON)

*Pre-registered as a two-sided probe of whether the DISCOVERY path the ventral
crossing calls for (mint a NEW generator) preserves a clean identity.* Report,
whatever the outcome:

- **B1 — singular-map universal-container leak:** present a COLLINEAR object
  (the `I` pentomino, 5 cells in a line) against the full-rank 7-object codebook.
  *Prediction: it IS recognized as a full-rank object* (a det=0 integer map
  collapses any 2-D shape onto a line, so a degenerate target is in the orbit of
  EVERYTHING). If recognized ⇒ **universal-container leak present** (bounded
  scope). If refused ⇒ GenInfer excludes non-injective maps and the class is
  clean.
- **B2 — not-a-group / floor collapse:** re-run H_invariance/H_discrimination
  (with shears added to `T_DS`) and H_floor_b under `gen_infer` ON. *Prediction:
  invariance gains shears BUT (i) some `t(O_i)` are recognized as `O_j≠O_i`
  (the reachable set is not a group ⇒ "same orbit" is not an equivalence
  relation), and (ii) FLOOR-b force-maps rise sharply* (calibrated: 11/21 on a
  real-angle-rotation + warp floor). Report exact counts.
- **MECHANISM (the diagnosis):** `GenInfer` enumerates ALL integer 2×2 matrices
  in `[-B,B]` (`shape_decode.rs:2087`), including NON-INJECTIVE (det=0) and
  |det|>1. A nuisance transform must be INVERTIBLE (you cannot un-collapse a
  line); the reachable set of a non-group is not an equivalence, so IDENTITY is
  ill-defined. **Named fix, NOT built:** restrict the enumeration to |det|=1
  (the actual `GL(2,ℤ)`) — a Rust change, deferred; `gen_infer` stays OFF by
  default so no committed result moves.

## 4. BOUNDS (§8) — stated in advance, not overclaimed

This is INSTANCE-level recognition invariant under the DISCOVERABLE discrete-
similarity nuisance class ONLY. **NOT** "object recognition solved." Named
frontier, NOT this rung: continuous / real-angle pose (cross-frame CONTINUOUS —
and note the IDENTIFIABILITY LIMIT this rung will surface: at 5-cell resolution a
rounded real rotation ALIASES onto a lattice similarity — "any given circle is
stepped"); lighting/appearance nuisance; non-rigid deformation; style;
CATEGORY-level (vs instance) recognition; the full learned axis-codebook at
scale; the failure-mode gates (McCollough, apperceptive/associative, inversion).

## 5. §9 off-day / sibling gates (verified in RESULTS)

Runner/gate additive & inert ⇒ committed bench unmoved. Sibling gates green:
`test_gen_infer_migrated`, `test_dimension_inference_migrated`,
`test_sdloop_vision_migrated` (orbit law {2:1,3:2,4:2,6:2,12:4} unmoved),
`test_border_ownership_migrated`, `test_engine_provenance_migrated`.
