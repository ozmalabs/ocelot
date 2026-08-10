# |det|=1 — the UNIMODULAR restriction on GenInfer — pre-registration

*The named-not-built fix from the objecthood WALL rung
(`VISION_IDENTITY_UNTANGLING_RESULTS.md`, Regime B). Regime B was a CLEAN
DIAGNOSED NEGATIVE: `GenInfer` (general integer-linear discovery, `gen_infer`
ON) enumerates ALL integer 2×2 maps — including NON-INJECTIVE (det=0), which
collapse any shape onto a line (collinear `I` → "L", the universal-container
leak, B1), and shears/`|det|>1`, so "same orbit" is not an equivalence (B2).
The named fix: restrict discovery to **|det|=1 (the unimodular group
GL(2,ℤ))** so discovered generators are INVERTIBLE and form a group.*

Committed BEFORE the confirmatory run (§3). Seed block **38000–38999**
declared; **12000–37999 burned** (ledger honoured — the noise floor uses
38000–38099, never used before). Engine provenance recorded in the RESULTS
file (§10). Pinned against base `main` HEAD **10796886**.

## 0. AUDIT — seed guard, NO new Rust (§12.4, cited file:line)

**Verdict: SEED-LEVEL GUARD. No new Rust. The `|det|` test is expressible as
graph DATA over Terms that already exist.**

- **Where GenInfer enumerates:** `eval_gen_infer`
  (`runners/dsl/src/shape_decode.rs:2013`) enumerates every integer 2×2 matrix
  `[m00,m01,m10,m11]` with entries in a data-derived `[-b,b]`
  (`:2087`–`:2123`), applies each via `apply_linear_once` (`:728`), keeps the
  Occam-best (`:2113`). It emits the winning `matrix` as a field
  (`:2137`); on no match, `matrix` is an **empty** tuple (`:2149`).
- **The `|det|` test IS graph data.** `matrix = GenInfer(field="matrix")` →
  `[m00,m01,m10,m11]`; the determinant `m00·m11 − m01·m10` and `|det|=1` are
  computed by Terms that already exist and parse from JSON: `Nth`
  (`shape_decode`/`term.rs:6021`, empty→`None`, no panic), `Times`, `Minus`,
  `Abs`, `Eq` (`term.rs:5513`–`5531`; `And` short-circuits, `term.rs:5495`).
  When GenInfer finds nothing the matrix is empty → `Nth`→`None` → determinant
  `0` (numeric coercion) → `|det|≠1` → the guard is false. **So the guard needs
  NO new Term and NO `.rs` change.**
- **The guard is two new seed rules + one committed-rule suppression**
  (`seeds/shape_decode_loop.json`, gated on a NEW flag `agent.gen_unimodular`,
  absent ⇒ OFF ⇒ every committed result byte-identical, §9):
  - `sd_gen_check` gains one clause `Not(Eq(ag.gen_unimodular, 1))` — it runs
    unchanged in the unrestricted mode (flag absent ⇒ clause true), suppressed
    in unimodular mode.
  - `sd_gen_check_uni_yes` (flag ON, `|det|=1`): sets `gen_checked=1` AND
    `gen_explained=1` ⇒ `sd_mint_generator` mints the SAME `|det|=1` matrix.
  - `sd_gen_check_uni_no` (flag ON, `|det|≠1` incl. det=0 / empty): sets
    `gen_checked=1` ONLY ⇒ `gen_explained` absent ⇒ falls through to
    `sd_mint_quantum` (novelty mint / honest refuse). The det=0 leak is REFUSED
    here.

**The HONESTY caveat this measures (not assumes).** This is a POST-HOC veto on
GenInfer's SINGLE best matrix, NOT a restriction of the argmin SEARCH range.
They coincide iff the winner's determinant equals what an enumeration-filtered
search would return. For a **full-rank** base the exact recovering linear map is
**unique**, so the winner's det equals the applied transform's det and there is
no re-selection divergence — but this is a claim we **MEASURE per view**
(record the winner's determinant on every recognized/refused view;
cross-checked against an independent Python enumeration CONTROL). If any view
diverged (a `|det|=1`-reachable view refused because the argmin winner was
`|det|≠1`), we would report it and conclude a Rust enumeration filter is needed.
Preferring the seed guard (task §3: "PREFER the no-Rust seed guard") is
conditional on this measured equivalence.

The adapter (`scripts/det1_measure.py`) only builds ShapeSignature objects +
Observation views, sets flags, calls `run_rules`, reads `status`/`covered_by`
and (for the audit) the minted generator matrices. **No Python decision; no
covariance; no Hebbian.**

## 1. Objects, transforms, mode (re-use the WALL rung's construction)

- **Objects** = the SAME 7 full-rank free pentominoes `F,T,U,V,L,N,X` (5 cells,
  monochrome `red`; codebook ISOLATED — the 17 pre-seeded symbolic
  ShapeSignatures `remove_node`-d), exactly as
  `scripts/identity_untangling_measure.py`.
- **Mode under test** = `gen_infer_enabled=1` AND `gen_unimodular=1` (the
  restricted DISCOVERY setting). Held generators (rotation90, reflections,
  scale2, cycle4) are in the DimInfer codebook and fire FIRST (rung 2), BEFORE
  the GenInfer rung — so the `|det|=1` restriction affects ONLY the discovery
  rung, not held similarity recognition.
- **Discrete-similarity class** `T_DS` (held): `identity, translate(+3,+2),
  rot90, rot180, rot270, refl_r, refl_c, scale2`. **Shears** `shearX=[1,1,0,1]`,
  `shearY=[1,0,1,1]` (both **det=1**) added for the discovery arms.
- **Identity readout:** `covered_by` iff `status ∈ {recognized,
  recognized_transformed}`, else `NEW` (minted / refused).

## 2. Off by default (§9) — ONE new flag, no Rust

`gen_unimodular` is a NEW flag, absent by default. With it absent every
committed path (incl. `gen_infer` ON, the whole Regime-B machinery) is
byte-identical: `sd_gen_check`'s added clause is satisfied-when-absent, and the
two `uni` rules require `gen_unimodular==1` to fire. This rung commits: a seed
edit (2 new rules + 1 suppression clause), a runner, a gate, this prereg, a
results file, a pinned JSON. **No `.rs` edit** ⇒ the shared canonical engine is
a legitimate build of this tree's source (§10; `test_engine_provenance_migrated`
green). §9 off-day = the committed bench unmoved.

## 3. Hypotheses, statistics, decision rule (two-sided; predictions stated)

The geometric arms are **DETERMINISTIC** (no sampling) — the statistic is an
exact count over the object×transform grid. The **noise floor** is the
prospective seeded arm (seeds 38000–38099, never used).

Mode for ALL arms below unless stated: `gen_infer=1, gen_unimodular=1`.

### THREE HONEST OUTCOMES (stated in advance)

1. **FULL RECOVERY** — `|det|=1` passes invariance + discrimination (exact-0
   false merge) + untangling + floors ⇒ the unimodular group IS the identity-
   preserving nuisance group; the wall crossing extends to discovery.
2. **PARTIAL (the deeper finding)** — `|det|=1` fixes the det=0 collapse but
   the SHEARS (det=1) still over-merge (discrimination not exact-0) and/or
   non-held scale is refused ⇒ the identity-preserving group is the SIMILARITY
   subgroup, NOT the full unimodular group; shears are identity-CHANGING.
3. **IN BETWEEN** — report exactly what holds/breaks, diagnosed.

### ARMS

- **A1 — INVARIANCE (held similarity).** every `t(O_i)`, `t ∈ T_DS`, → `O_i`.
  Statistic: correct / (7×7 = 49). **PASS iff 49/49.** *Prediction: 49/49 —
  held generators fire before GenInfer, so the `|det|=1` restriction on
  discovery does NOT touch this; identical to Regime A.*
- **A2 — INVARIANCE (shears, the DISCOVERY crux).** every `shear(O_i)`,
  `shear ∈ {shearX, shearY}`, → `O_i`. Statistic: (correct, wrong_id, new) /
  (7×2 = 14). *Prediction: shears ARE discovered (det=1 admitted) so most are
  recognized, BUT the WALL rung's `shearY(F)→X` and `shearX(T)→X` WRONG-ids
  PERSIST (a sheared pentomino aliases onto ANOTHER pentomino's held orbit).
  Predict ~12/14 correct, **2 wrong_id**. A wrong_id here IS a
  discrimination/identity failure — shears do not preserve identity.*
- **A3 — DISCRIMINATION exact-0 (the CRUX, §1.1).**
  - **B1 collinear leak:** collinear `I` vs full 7-object codebook. **PASS iff
    REFUSED (NEW).** *Prediction: REFUSED — det=0 excluded (pilot on burned
    stimuli: leak `→L` under `gen_infer` ON becomes `minted` under
    `gen_unimodular` ON). **B1 FIXED.***
  - **Pairwise:** for every ordered `i≠j`, `O_j` (untransformed) vs `{O_i}`
    only. Statistic: spurious recognitions / (7×6 = 42). *Prediction: 0/42 (the
    full-rank pairs were never merged by det=0/`|det|>1` maps — the leak is on
    DEGENERATE targets and SHEAR-aliasing, captured by B1 and A2, not here).*
  - **DISCRIMINATION VERDICT:** exact-0 identity preservation holds iff A2
    wrong_id == 0 AND B1 refused AND pairwise 0/42. *Prediction: **FAILS** on A2
    (shear wrong_id = 2) ⇒ OUTCOME 2. We do NOT relax this to force a pass
    (§5/§1.1).*
- **A4 — UNTANGLING (DiCarlo).** raw-template control = nearest stored
  signature by origin-normalized cell-set symmetric-difference; measured over
  the T_DS grid (49) and the shear grid (14). **PASS iff raw off-diagonal
  error > 0 AND the orbit-rep off-diagonal error separates it.** Statistic:
  (raw_wrong, orbit_wrong) per grid. *Prediction: T_DS raw_wrong ≈ 26, orbit
  0; shear grid raw tangles, orbit_wrong = 2 (the persistent shear aliases).*
- **A5 — FLOOR (refused, not force-mapped).**
  - **Noise:** 100 random 5-cell objects, **seeds 38000–38099**, vs the
    7-object codebook. **PASS iff 0/100.** *Prediction: 0/100.*
  - **det=0 map:** a singular map `[1,1,0,0]` applied to each object. **PASS
    iff 0/7 recognized.** *Prediction: 0/7 (det=0 excluded).*
  - **non-held scale (`scale3=[3,0,0,3]`, det=9):** applied to each object.
    **PASS iff 0/7 recognized** (the DISCOVERY path cannot mint `|det|=9`).
    *Prediction: 0/7 refused — held scale2 is preserved (A1) but a non-held
    integer scale needs discovery, which `|det|=1` excludes. This ANSWERS the
    "is integer-scale lost?" question by measurement: HELD scale preserved,
    non-held discovered scale refused.*
  - **non-rigid warp:** one cell of each object displaced `(+2,+2)`. **PASS iff
    0/7.** *Prediction: 0/7 (no global linear map explains it).*
  - **real-angle rotation (37°/53°) — REPORTED, not gated:** the identifiability
    limit (a rounded real rotation ALIASES onto a lattice similarity). Under
    `gen_infer` ON (unrestricted) the wall rung read 11/21 force-maps. *Predict
    the `|det|=1` restriction REDUCES this (the det≠1 rounded maps refused) but
    not to 0 (det=1 aliases persist). Report the exact count; do not gate on it
    (§5 — it is the resolution limit, not a leak).*
- **AUDIT arm — winner determinant (faithfulness of the seed-guard veto).** For
  every recognized view whose recognition came via the DISCOVERY rung (a minted
  `DimensionGenerator{kind:"linear"}`), record its matrix + determinant; confirm
  every minted linear generator is `|det|=1`. Independently (Python control,
  a MEASUREMENT not an agent decision) enumerate whether GenInfer's best map is
  `|det|=1` and confirm the graph's recognized/refused verdict matches
  "held-recognized OR (discovered ∧ `|det|=1`)". *Prediction: every minted
  linear generator `|det|=1`; verdict matches the control on 100% of views
  (no re-selection divergence).*

## 4. BOUNDS (§8) — stated in advance, not overclaimed

INSTANCE-level recognition, bounded to whatever nuisance GROUP the measurement
shows is identity-preserving. This rung does NOT claim "object recognition
solved." NAMED frontier, unchanged: continuous / real-angle pose (cross-frame
CONTINUOUS — with the aliasing identifiability limit above);
lighting/appearance; non-rigid deformation; style; **CATEGORY**-level (vs
instance); the full learned axis-codebook at scale; the failure-mode gates
(McCollough, apperceptive/associative, inversion). The object set is 7
hand-chosen full-rank free pentominoes; the discrimination claim is over those
42 ordered pairs + the shear/floor grids, not over all shapes.

## 5. §9 off-day / sibling gates (verified in RESULTS)

`gen_unimodular` absent by default ⇒ committed bench unmoved. Sibling gates to
stay green: `test_gen_infer_migrated`, `test_dimension_inference_migrated`,
`test_sdloop_vision_migrated` (orbit law {2:1,3:2,4:2,6:2,12:4} unmoved),
`test_border_ownership_migrated`, `test_identity_untangling_migrated`,
`test_engine_provenance_migrated`; broad vision bench 200/0.
