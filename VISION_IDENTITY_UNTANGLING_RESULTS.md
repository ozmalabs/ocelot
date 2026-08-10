# IDENTITY UNTANGLING — the objecthood "what" wall — RESULTS

*Pre-registered in `VISION_IDENTITY_UNTANGLING_PREREG.md` (committed `a6649538`,
BEFORE this run). Runner `scripts/identity_untangling_measure.py`, gate
`tests/test_identity_untangling_migrated.py`, pinned
`results/identity_untangling.json`. Seeds 37000–37099 (floor-a).*

**Provenance (§10):**
`engine 7d5f50c18673 @ …/runners/dsl/python/substrate_rs/_native.abi3.so
[shared build — Rust source identical]`. This rung adds **NO Rust** and **NO
seed edit** (runner + gate + docs only), so the shared canonical engine is a
legitimate build of this tree's source (`test_engine_provenance_migrated` green).

## HEADLINE

**The wall is CROSSED — BOUNDED to the invertible discrete-similarity nuisance
class; and the ambitious extension is a CLEAN DIAGNOSED NEGATIVE.**

- **Generator-orbit identity is expressible BY COMPOSITION** — the sd loop's
  Occam ladder already computes it; `covered_by` IS the recognized identity, the
  `Transform` on `has_transform` IS the nuisance. **No new Rust; no covariance;
  no Hebbian** — the diagnosed cortex-line dead end is not walked back into.
- **REGIME A (held invertible generators, `gen_infer` OFF): invariance +
  discrimination + measured untangling + both floors ALL HOLD.** Identity is a
  clean partition under `{translation, rot90/180/270, reflection, integer
  scale}`.
- **REGIME B (GenInfer general integer-linear discovery, `gen_infer` ON): the
  universal-container failure the wall is DEFINED by REAPPEARS**, diagnosed to a
  single mechanism: `GenInfer` enumerates **non-injective (det=0)** integer maps,
  so a degenerate (collinear) target is in the orbit of everything, and the
  reachable set is **not a group**, so "same orbit" is not an equivalence and
  identity is ill-defined. **Named fix (restrict to `|det|=1`), NOT built.**

## REGIME A — the bounded CROSSING (all pass; deterministic geometry + seeded floor)

| arm | statistic | result | decision |
|---|---|---|---|
| **INVARIANCE** | `t(O_i) -> O_i` | **49/49** correct, 0 wrong, 0 new | **PASS** |
| **DISCRIMINATION** (§1.1 crux) | spurious cross-maps, pairs `i≠j` | **0/42** | **PASS** |
| **UNTANGLING** (DiCarlo) | (raw_wrong, orbit_wrong) of 49 | raw **26**, orbit **0** | **PASS** |
| **FLOOR-a** (noise) | force-maps, seeds 37000–37099 | **0/100** | **PASS** |
| **FLOOR-b** (non-rigid warp) | force-maps | **0/7** | **PASS** |

- **INVARIANCE = 49/49.** *Count reconciliation (honest, not surgery):* the grid
  is 7 objects × 7 matrices = 49 views, and **every view already carries a
  translation** (`translate(+3,+2)`); the `identity`-matrix row IS the
  pure-translation test. The prereg's "7×8 = 56" double-counted translation as a
  separate transform; the pre-registered DECISION ("all views correct") is met
  exactly at 49/49. Each `t(O_i)` reaches `recognized`/`recognized_transformed`
  with `covered_by == O_i`: same-orbit membership decided in one `run_rules`
  fixpoint.
- **DISCRIMINATION = 0/42.** No held generator maps any distinct pentomino onto
  another. This is the anti-universal-container guard (`build_candidate`: equal
  relation count + same predicate + consistent per-dim map) doing its job. A
  generator that "explained arbitrary pairs" would DISQUALIFY — it does not, here.
- **UNTANGLING is MEASURED, with the raw control SHOWN to tangle.** The naive
  raw-template baseline (nearest stored signature by origin-normalized cell-set
  symmetric-difference — "image-space" matching) **ERRS on 26 of 49 views (53%)**:
  a rotated/reflected/scaled `O_i` lands closer to a *different* pentomino than to
  its own un-transformed stored signature. The generator-orbit representation maps
  **all 49 back to the correct identity (orbit_wrong = 0)**. **The orbit-rep
  separates exactly what the raw-rep tangles** — the DiCarlo untangling signature,
  measured against its control.
- **FLOORS hold.** 100 random 5-cell objects never join an existing orbit (0/100);
  a single displaced cell (no global transform explains it) is refused (0/7).

**Regime-A verdict: the objecthood wall is CROSSED for instance-level recognition
under the DISCOVERABLE invertible discrete-similarity nuisance class.**

## REGIME B — the DIAGNOSED NEGATIVE (general integer-linear discovery, `gen_infer` ON)

| probe | result | reading |
|---|---|---|
| **B1 singular-map leak** | collinear `I` → `covered_by = L` (recognized_transformed) | **UNIVERSAL-CONTAINER LEAK** — a det=0 map collapses any 2-D shape onto a line, so a degenerate target is in the orbit of EVERYTHING |
| **B2 not-a-group** | invariance 61/63, **2 WRONG-id**: `shearY(F)→X`, `shearX(T)→X` | the reachable set is not a group ⇒ a transformed view of one object reads as ANOTHER ⇒ identity is not a clean partition |
| **B2 floor collapse** | **11/21** out-of-class inputs force-mapped (real-angle rotations 37°/53°) | the general class "explains" inputs it should refuse |
| **B2 discrimination** | 0/42 | the hand-picked full-rank reps still discriminate pairwise even under gen-ON — the leak is on DEGENERATE targets, OUT-OF-CLASS inputs, and the GROUP property, not on these specific clean pairs |

**MECHANISM (the diagnosis):** `GenInfer` (`shape_decode.rs:2087`) enumerates
**all** integer 2×2 matrices in `[-B,B]`, including **non-injective (det=0)** and
`|det|>1`. A nuisance transform must be **invertible** — you cannot un-collapse a
line, so a map that collapses is not a nuisance you can factor out. The set
reachable by an arbitrary (non-group) family of maps is not an equivalence
relation, so "same orbit" — and therefore IDENTITY — is ill-defined. This is
§1.1's degenerate-"everything-matches" failure, caught (not passed) by the
discrimination measure: **the measure has TEETH.**

**Named fix, NOT built (§9-safe):** restrict the enumeration to `|det| = 1` (the
actual `GL(2,ℤ)`), which is exactly the invertible class Regime A already uses in
its held generators. This is a Rust change to `eval_gen_infer`; deferred. It is
NOT bolted on here because (a) the rung's remit is to MEASURE the crossing, (b)
`gen_infer` ships **OFF by default** so no committed result moves, and (c) the
clean crossing already exists in Regime A without touching Rust.

## The IDENTIFIABILITY LIMIT surfaced (a real finding, not a gate)

Under `gen_infer` the real-angle-rotation floor collapsed 11/21 — but part of
that is **NOT** a leak, it is the frame/continuum invariant made visible: **at
5-cell resolution a rounded real rotation ALIASES onto a lattice similarity**
(e.g. 53° ≈ atan(4/3) rounds to clean integer images). "Any given circle is
stepped"; a continuous pose is identifiable only to observational resolution. So
"real-angle rotation is refused" holds only above an aliasing resolution — which
is why FLOOR-b uses a **non-rigid warp** (resolution-independent, refused 0/7)
as its clean gate, and the real-rotation aliasing is REPORTED here, not gated.

## BOUNDS (§8) — what is NOT shown

INSTANCE-level recognition invariant under the DISCOVERABLE **invertible**
discrete-similarity nuisance class ONLY (translation, 90° rotation, reflection,
integer scale). **NOT** "object recognition solved." Explicitly out of scope and
NAMED as frontier: continuous / real-angle pose (cross-frame CONTINUOUS — a
richer generator class; and note the aliasing identifiability limit above);
lighting / appearance nuisance; non-rigid deformation; style; **CATEGORY**-level
(vs instance) recognition; the full learned axis-codebook at scale; and the
deeper failure-mode gates (McCollough contingent aftereffect;
apperceptive/associative dissociation; face-inversion). The object set is 7
hand-chosen full-rank free pentominoes; the discrimination claim is over those 42
ordered pairs, not over all shapes. GenInfer's general-class negative is the
honest reason the general axis-codebook at scale is not claimed.

## §9 off-day / sibling gates

Runner + gate are additive and inert; `gen_infer` OFF by default. Sibling gates
green at engine `7d5f50c18673`: `test_gen_infer_migrated`,
`test_dimension_inference_migrated`, `test_sdloop_vision_migrated` (orbit law
{2:1,3:2,4:2,6:2,12:4} unmoved), `test_border_ownership_migrated`,
`test_transform_decode_migrated`, `test_time_infer_migrated`,
`test_engine_provenance_migrated` (62 passed together); the new gate 7/7. Broad
`scripts/rung7_vision_bench.sh` (`data/` symlinked, §10.2): **200 passed / 0
failed** at engine `7d5f50c18673` — the committed vision bench is unmoved.
