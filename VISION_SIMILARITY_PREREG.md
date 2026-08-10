# SIMILARITY subgroup — the restriction on GenInfer that excludes the shears — pre-registration

*The named-not-built fix from the `|det|=1` rung (`VISION_DET1_RESULTS.md`,
OUTCOME 2). `|det|=1` fixed the det=0 universal-container collapse but ADMITTED
the shears (det=1, invertible but identity-CHANGING): `shearY(F)→X`,
`shearX(T)→X` still over-merged, so discrimination was NOT exact-0. The measured
characterization: the identity-preserving nuisance group is the **SIMILARITY
subgroup** (rotation / reflection / uniform scale — scaled-orthogonal maps,
`M·Mᵀ = λ·I`), a PROPER SUBGROUP of `GL(2,ℤ)`. This rung restricts GenInfer's
discovery to that subgroup, which should EXCLUDE the shears and convert
OUTCOME 2 → a FULL discovery-path crossing.*

Committed BEFORE the confirmatory run (§3). Seed block **39000–39999**
declared; **12000–38999 burned** (ledger honoured — the noise floor uses
39000–39099, never used before; det1 used 38000–38099). Engine provenance
recorded in the RESULTS file (§10). Pinned against base `main` HEAD **4f05d008**
(`git merge-base --is-ancestor 4f05d008 HEAD` verified).

## THE SIMILARITY CONDITION (verified in-code, §12.4 — before building)

For a discovered matrix `M = [[m00,m01],[m10,m11]]` (row-major; the discovered
`matrix` field is the tuple `[m00,m01,m10,m11]`; columns are `[m00,m10]` at
indices 0,2 and `[m01,m11]` at indices 1,3), `M` is a similarity (scaled
rotation/reflection, `M·Mᵀ = λ·I` with `λ>0`) iff ALL THREE hold:

- **ORTHOGONAL columns:** `m00·m01 + m10·m11 = 0`
- **EQUAL squared length:** `m00² + m10² = m01² + m11²`
- **NON-DEGENERATE (λ>0):** `det = m00·m11 − m01·m10 ≠ 0`

The first two are the task's stated condition; the third is REQUIRED because the
first two are BOTH satisfied by the zero matrix (`0=0`, `0=0`), and GenInfer's
*empty* result (no map found) reads via `Nth`→None. (Measured: `Nth` of an empty
matrix returns None and the numeric Terms SKIP None — empty product `= 1`, empty
sum `= 0` — so an empty matrix gives `ortho = 1+1 = 2 ≠ 0` AND `det = 1−1 = 0`,
failing BOTH `ortho=0` and `det≠0`; the empty case is doubly-refused.) For a real
scaled-orthogonal `M`, `|det| = λ`, so `det≠0 ⟺ λ>0` and the three together are
exactly "similarity, excluding the degenerate map."

**Verified by construction (`python3`, before writing any rule):**

| matrix | ortho | eqlen−diff | det | similarity? |
|---|---|---|---|---|
| rot90 `[0,-1,1,0]` | 0 | 0 | 1 | **YES** ✓ |
| rot180 `[-1,0,0,-1]` | 0 | 0 | 1 | **YES** ✓ |
| rot270 `[0,1,-1,0]` | 0 | 0 | 1 | **YES** ✓ |
| refl_r `[-1,0,0,1]` | 0 | 0 | −1 | **YES** ✓ |
| refl_c `[1,0,0,-1]` | 0 | 0 | −1 | **YES** ✓ |
| identity `[1,0,0,1]` | 0 | 0 | 1 | **YES** ✓ |
| scale2 `[2,0,0,2]` | 0 | 0 | 4 | **YES** ✓ |
| scale3 `[3,0,0,3]` | 0 | 0 | 9 | **YES** ✓ (uniform scale IS a similarity) |
| **shearX** `[1,1,0,1]` | **1** | −1 | 1 | **no** ✗ (orthogonality) |
| **shearY** `[1,0,1,1]` | **1** | 1 | 1 | **no** ✗ (orthogonality) |
| **det=0 collapse** `[1,0,1,0]` | 0 | **2** | 0 | **no** ✗ (equal-length) |
| **det=0** `[1,1,0,0]` | 1 | 0 | 0 | **no** ✗ (both) |
| **zero/empty** `[0,0,0,0]` | 0 | 0 | **0** | **no** ✗ (non-degenerate) |
| scaled-rot `[2,-2,2,2]` | 0 | 0 | 8 | **YES** ✓ |

The condition ADMITS the identity-preserving transforms (rotation/reflection/
uniform scale) and EXCLUDES the identity-changing ones (shears via orthogonality;
det=0 collapse via equal-length; empty via non-degenerate).

## 0. AUDIT — seed guard, NO new Rust (§12.4, cited file:line)

**Verdict: SEED-LEVEL GUARD. No new Rust. The similarity test is expressible as
graph DATA over Terms that already exist — the SAME vocabulary as `|det|=1`, plus
`Plus` (which the DSL already has, `term.rs:492`/`:5529`, used by 100+ seeds).**

- **Where GenInfer enumerates:** `eval_gen_infer` (`runners/dsl/src/shape_decode.rs:2013`)
  enumerates every integer 2×2 matrix `[m00,m01,m10,m11]` in a data-derived
  `[-b,b]`, applies each via `apply_linear_once` (`:728`), keeps the Occam-best,
  and emits the winner as the `matrix` field (`:2137`); on no match `matrix` is
  an **empty** tuple (`:2149`).
- **The similarity test IS graph data.** `matrix = GenInfer(field="matrix")` →
  `[m00,m01,m10,m11]`; `Nth` (`term.rs`, empty→None, no panic), `Times`, `Plus`
  (`term.rs:5529`), `Minus`, `Eq` (`And` short-circuits, `term.rs:5495`) compute
  the three conditions. **NO new Term, NO `.rs` change** — exactly like `|det|=1`,
  which used `Nth`/`Times`/`Minus`/`Abs`/`Eq`; this rung swaps `Abs(det)` for the
  three-clause similarity test and adds `Plus`.
- **The guard is two new seed rules + one committed-rule suppression clause**
  (`seeds/shape_decode_loop.json`, gated on a NEW flag `agent.gen_similarity`,
  absent ⇒ OFF ⇒ every committed result byte-identical, §9):
  - `sd_gen_check` gains one clause `Not(Eq(ag.gen_similarity, 1))` — it runs
    unchanged when the flag is absent (clause true), suppressed in similarity
    mode. (It already carries `Not(Eq(ag.gen_unimodular, 1))` from det1; the two
    restriction modes are mutually exclusive by their flags.)
  - `sd_gen_check_sim_yes` (flag ON, `M` a non-degenerate similarity): sets
    `gen_checked=1` AND `gen_explained=1` ⇒ `sd_mint_generator` mints the SAME
    similarity matrix.
  - `sd_gen_check_sim_no` (flag ON, `M` NOT a non-degenerate similarity — incl.
    shears / det=0 / `|det|>1`-non-conformal / empty): sets `gen_checked=1` ONLY
    ⇒ `gen_explained` absent ⇒ falls through to `sd_mint_quantum` (novelty mint /
    honest refuse). The shear leak is REFUSED here.

**The HONESTY caveat this MEASURES (not assumes).** This is a POST-HOC veto on
GenInfer's SINGLE best matrix, NOT a restriction of the argmin SEARCH range. They
coincide iff the winner's matrix being non-similarity means no similarity-reachable
explanation existed that a filtered search would have returned. For a **full-rank**
base the exact recovering linear map is **unique**, so the winner is the ONE exact
map and there is no re-selection divergence. This is MEASURED per view: I record
GenInfer's best matrix on every recognized/refused view AND run an independent
Python enumeration CONTROL that filters to similarity matrices, and confirm the
graph's recognized/refused verdict matches "held-recognized OR (discovered ∧
similarity)" on 100% of views. **DECISIVE PRE-MEASUREMENT (recorded here before the
run, on already-burned construction, not a confirmatory seed):** for the two
aliasing shears, GenInfer's minted matrix is the SHEAR ITSELF — `shearY(F)→X`
mints `[1,0,1,1]` (ortho 1, non-similarity), `shearX(T)→X` mints `[1,1,0,1]`
(ortho 1, non-similarity) — so the similarity guard REFUSES them and no similarity
alternative was the argmin winner. If any view diverged (a similarity-reachable
view refused because the argmin winner was a non-similarity), I would report it and
conclude a Rust enumeration filter is needed. Preferring the seed guard (task §3:
"PREFER the seed guard") is conditional on this measured equivalence.

The adapter (`scripts/similarity_measure.py`) only builds ShapeSignature objects +
Observation views, sets flags, calls `run_rules`, reads `status`/`covered_by` and
(for the audit) the minted generator matrices. **No Python decision; no
covariance; no Hebbian.**

## 1. Objects, transforms, mode (re-use the WALL / det1 construction)

- **Objects** = the SAME 7 full-rank free pentominoes `F,T,U,V,L,N,X` (5 cells,
  monochrome `red`; codebook ISOLATED — the pre-seeded symbolic ShapeSignatures
  `remove_node`-d), exactly as `scripts/det1_measure.py`.
- **Mode under test** = `gen_infer_enabled=1` AND `gen_similarity=1` (the
  restricted DISCOVERY setting). Held generators (rotation90, reflections, scale2,
  cycle4) are in the DimInfer codebook and fire FIRST (rung 2), BEFORE the GenInfer
  rung — so the similarity restriction affects ONLY the discovery rung, not held
  similarity recognition.
- **Discrete-similarity class** `T_DS` (held): `identity, translate(+3,+2), rot90,
  rot180, rot270, refl_r, refl_c, scale2`. **Shears** `shearX=[1,1,0,1]`,
  `shearY=[1,0,1,1]` (both det=1 but ortho=1 — NOT similarities) added for the
  discovery arms.
- **Identity readout:** `covered_by` iff `status ∈ {recognized,
  recognized_transformed}`, else `NEW` (minted / refused).

## 2. Off by default (§9) — ONE new flag, no Rust

`gen_similarity` is a NEW flag, absent by default. With it absent every committed
path (incl. `gen_infer` ON and `gen_unimodular` ON, the whole Regime-B / det1
machinery) is byte-identical: `sd_gen_check`'s added clause is
satisfied-when-absent, and the two `sim` rules require `gen_similarity==1` to fire.
This rung commits: a seed edit (2 new rules + 1 suppression clause), a runner, a
gate, this prereg, a results file, a pinned JSON. **No `.rs` edit** ⇒ the shared
canonical engine is a legitimate build of this tree's source (§10;
`test_engine_provenance_migrated` green). §9 off-day = the committed bench unmoved.

## 3. Hypotheses, statistics, decision rule (two-sided; predictions stated)

The geometric arms are **DETERMINISTIC** (no sampling) — the statistic is an exact
count over the object×transform grid. The **noise floor** is the prospective
seeded arm (seeds 39000–39099, never used).

Mode for ALL arms below unless stated: `gen_infer=1, gen_similarity=1`.

### THE PREDICTION, STATED IN ADVANCE (§3.7)

**I predict OUTCOME 1 — a FULL discovery-path crossing.** The reasoning: the two
shears that over-merged under `|det|=1` are NON-similarities (orthogonality fails,
`ortho=1`), and the DECISIVE pre-measurement shows GenInfer's minted matrix for
each aliasing view IS the shear itself — so the similarity guard REFUSES them, the
sheared `F`/`T` are minted as NOVEL (not recognized as `X`), the pentominoes stay
on distinct orbits, and discrimination becomes exact-0. Held similarity (rot/refl/
scale2) is untouched (routes via DimInfer before GenInfer), so invariance stays
49/49. What a RESIDUAL would mean: if any shear STILL aliased (discrimination not
exact-0) despite the guard, it would mean GenInfer found a genuine *similarity*
matrix mapping one pentomino's cell-set onto another (a real lattice coincidence at
5-cell resolution) — an identifiability limit, NOT a guard failure, which I would
report and diagnose, not relax the floor (§5/§1.1). A second possible residual: a
similarity-reachable view wrongly refused by the post-hoc veto (re-selection
divergence) — I measure for it and would prescribe the Rust filter.

### THREE HONEST OUTCOMES (stated in advance)

1. **FULL CROSSING (predicted)** — similarity restriction passes invariance
   (49/49) + discrimination (exact-0: shears refused, B1 refused, pairwise 0/42) +
   untangling (orbit separates raw tangle) + floors ⇒ the SIMILARITY subgroup IS
   the identity-preserving nuisance group and the discovery path now matches
   Regime A.
2. **RESIDUAL** — a shear still aliases (a genuine similarity coincidence) and/or a
   similarity-reachable view is wrongly refused (re-selection divergence) ⇒ report
   + diagnose, do NOT relax the floor.
3. **IN BETWEEN** — report exactly what holds/breaks, diagnosed.

### ARMS

- **A1 — INVARIANCE (held similarity).** every `t(O_i)`, `t ∈ T_DS`, → `O_i`.
  Statistic: correct / (7×7 = 49). **PASS iff 49/49.** *Prediction: 49/49 — held
  generators fire before GenInfer, so the similarity restriction on discovery does
  NOT touch this; identical to Regime A and to det1's A1.*
- **A2 — INVARIANCE (shears, the DISCOVERY crux).** every `shear(O_i)`, `shear ∈
  {shearX, shearY}`. Statistic: (correct, wrong_id, new) / (7×2 = 14). *Prediction:
  the shears are NON-similarities → REFUSED at discovery → all 14 → NEW.
  **(0 correct, 0 wrong_id, 14 new).** The det1 wrong_ids (`shearY(F)→X`,
  `shearX(T)→X`) are GONE — a sheared pentomino no longer lands on another's
  identity because the shear map is refused, not admitted. A wrong_id here would be
  a genuine similarity coincidence (residual, reported).*
- **A3 — DISCRIMINATION exact-0 (the CRUX, §1.1).**
  - **B1 collinear leak:** collinear `I` vs full 7-object codebook. **PASS iff
    REFUSED (NEW).** *Prediction: REFUSED — det=0 excluded by equal-length
    (`[1,0,1,0]`: eqlen 2≠0) exactly as `|det|=1` excluded it, and a shear/collapse
    map is not a similarity.*
  - **Pairwise:** for every ordered `i≠j`, `O_j` (untransformed) vs `{O_i}` only.
    Statistic: spurious recognitions / (7×6 = 42). *Prediction: 0/42.*
  - **DISCRIMINATION VERDICT:** exact-0 identity preservation holds iff A2
    wrong_id == 0 AND B1 refused AND pairwise 0/42. *Prediction: **exact-0 = TRUE**
    ⇒ OUTCOME 1. This is the whole point: `|det|=1`'s A2 wrong_id=2 becomes 0.*
- **A4 — UNTANGLING (DiCarlo).** raw-template control = nearest stored signature by
  origin-normalized cell-set symmetric-difference; over the T_DS grid (49) and the
  shear grid (14). **PASS iff raw off-diagonal error > 0 AND orbit-rep separates
  it.** Statistic: (raw_wrong, orbit_wrong) per grid. *Prediction: T_DS raw_wrong
  ≈ 26, orbit 0; shear grid raw tangles (raw_wrong > 0), orbit_wrong = 0 (the
  shears are refused = orbit-NEW, NOT mapped onto a wrong identity — the shear-
  induced tangle is now GONE, where det1 left 2).*
- **A5 — FLOOR (refused, not force-mapped).**
  - **Noise:** 100 random 5-cell objects, **seeds 39000–39099**, vs the 7-object
    codebook. **PASS iff 0/100.** *Prediction: 0/100.*
  - **det=0 map:** a singular map `[1,1,0,0]` applied to each object. **PASS iff
    0/7 recognized.** *Prediction: 0/7 (not a similarity).*
  - **shear as a floor (`shearX`/`shearY`) explicitly refused:** covered by A2 —
    stated here as the "a genuine shear REFUSED not force-mapped" floor. *Prediction:
    0/14 recognized (all NEW).*
  - **non-rigid warp:** one cell of each object displaced `(+2,+2)`. **PASS iff
    0/7.** *Prediction: 0/7 (no global linear map explains it → GenInfer empty →
    doubly-refused).*
  - **non-held scale (`scale3=[3,0,0,3]`, det=9) — REPORTED, the DIFFERENCE from
    det1:** applied to each object. *Prediction: **RECOGNIZED 7/7** — a uniform
    integer scale IS a similarity (`ortho=0`, `eqlen=0`, `det=9≠0`), so the
    similarity guard ADMITS it and the DISCOVERY path mints scale3 as a generator;
    `scale3(O_i)→O_i`. This is the CORRECT physics and the sharpest contrast with
    `|det|=1` (which REFUSED scale3 for `det≠1`): similarity is the RIGHT group —
    it keeps uniform scale (which det1 wrongly dropped) AND drops the shears (which
    det1 wrongly kept). REPORTED as recognized; NOT gated as a refusal.* A residual
    here (scale3 refused) would mean the seed guard's post-hoc veto diverges from a
    similarity-filtered search — measured by the AUDIT arm.
  - **real-angle rotation (37°/53°) — REPORTED, not gated:** the identifiability
    limit (a rounded real rotation ALIASES onto a lattice similarity). *Predict the
    similarity restriction still admits the det=±1 lattice aliases AND now also the
    scaled-similarity aliases, so the count is ≈ det1's 10/14 or somewhat higher;
    report the exact count, do not gate (§5 — resolution limit, not a leak).*
- **AUDIT arm — winner matrix (faithfulness of the seed-guard veto).** For every
  view recognized via the DISCOVERY rung (a minted `DimensionGenerator{kind:
  "linear"}`), record its matrix; confirm every minted linear generator is a
  non-degenerate similarity. Independently (Python control, a MEASUREMENT not an
  agent decision) enumerate whether GenInfer's best map is a similarity and confirm
  the graph's recognized/refused verdict matches "held-recognized OR (discovered ∧
  similarity)". *Prediction: every minted linear generator is a similarity; verdict
  matches the control on 100% of views (no re-selection divergence).*

## 4. BOUNDS (§8) — stated in advance, not overclaimed

Even a FULL crossing is INSTANCE-level recognition under the DISCRETE-similarity
nuisance group (integer-lattice rotation90 / reflection / integer uniform scale).
The win, IF it crosses: **the substrate DISCOVERS its own identity-preserving
nuisance group (the similarity subgroup) from an unrestricted integer-linear
search, rather than being handed a curated held-generator set** — the discovery
path is made to match Regime A's held-generator crossing, by the substrate's own
graph-data test of what a nuisance IS (a scaled orthogonal map). This does NOT
claim "object recognition solved." NAMED frontier, UNCHANGED: continuous / real-
angle pose (cross-frame CONTINUOUS — with the aliasing identifiability limit
above); lighting / appearance; non-rigid deformation; style; **CATEGORY**-level
(vs instance); the full learned axis-codebook at scale; the failure-mode gates
(McCollough, apperceptive/associative, inversion). The object set is 7 hand-chosen
full-rank free pentominoes; the discrimination claim is over those 42 ordered pairs
+ the shear/floor grids, not over all shapes.

## 5. §9 off-day / sibling gates (verified in RESULTS)

`gen_similarity` absent by default ⇒ committed bench unmoved. Sibling gates to stay
green: `test_det1_migrated`, `test_gen_infer_migrated`,
`test_dimension_inference_migrated`, `test_sdloop_vision_migrated` (orbit law
{2:1,3:2,4:2,6:2,12:4} unmoved), `test_border_ownership_migrated`,
`test_identity_untangling_migrated`, `test_engine_provenance_migrated`; broad
vision bench 200/0 (`data/` symlinked, §10.2).
