# SIMILARITY subgroup — the restriction on GenInfer that excludes the shears — RESULTS

*Pre-registered in `VISION_SIMILARITY_PREREG.md` (committed `87d648f0`, BEFORE
this run). Runner `scripts/similarity_measure.py`, gate
`tests/test_similarity_migrated.py`, pinned `results/similarity.json`. Noise floor
seeds 39000–39099 (never previously used; det1 used 38000–38099). Base `main` HEAD
**4f05d008** (`git merge-base --is-ancestor 4f05d008 HEAD` verified).*

**Provenance (§10):**
`engine 7d5f50c18673 @ …/runners/dsl/python/substrate_rs/_native.abi3.so
[shared build from …/gamma-substrate — Rust source identical]`. This rung adds
**NO Rust** — the similarity restriction is a SEED GUARD (graph data over existing
Terms: `Nth`/`Times`/`Plus`/`Minus`/`Eq`). The shared canonical engine is a
legitimate build of this tree's source (`test_engine_provenance_migrated` green,
source `shared` — byte-identical `.rs`). **No new engine hash: shared-legit,
because there is truly no `.rs` change.**

## HEADLINE — OUTCOME 1 (FULL CROSSING on the crux): the discovery path now matches Regime A

**Restricting GenInfer to the SIMILARITY subgroup (scaled-orthogonal maps) does
what `|det|=1` could not: it REFUSES the shears at discovery, so a sheared
pentomino no longer aliases onto another identity, and DISCRIMINATION is EXACT-0
while INVARIANCE stays 49/49.** The substrate DISCOVERS its own identity-preserving
nuisance group — it MINTS a discovered similarity it did not hold (scale3
`[3,0,0,3]`) and REFUSES a discovered non-similarity (each shear) — by its OWN
graph-data test of what a nuisance IS. Every geometric prediction held; one
sub-arm carries a diagnosed residual (the identifiability limit, §7), reported not
gated.

- **AUDIT verdict: SEED GUARD, no new Rust.** GenInfer's inferred `matrix`
  (`shape_decode.rs:2137`) is read as graph data; the three similarity conditions —
  ORTHOGONAL columns `m00·m01+m10·m11=0`, EQUAL squared length
  `m00²+m10²=m01²+m11²`, NON-DEGENERATE `det=m00·m11−m01·m10≠0` — are computed by
  `Nth`/`Times`/`Plus`/`Minus`/`Eq` Terms in a rule `where`-clause
  (`seeds/shape_decode_loop.json`: `sd_gen_check_sim_yes` / `sd_gen_check_sim_no`,
  gated on a new `agent.gen_similarity` flag, OFF by default; `sd_gen_check` gains
  one suppression clause). The vision bench's own scan confirms it: *"(none — every
  knob is graph data)."* The NON-DEGENERATE clause is load-bearing and was verified
  necessary: the first two equalities are BOTH satisfied by the zero matrix
  (`0=0`, `0=0`), and GenInfer's empty result reads via `Nth`→None which the
  numeric Terms SKIP (empty product `=1`, empty sum `=0`), so an empty matrix gives
  `ortho=1+1=2` (fails `ortho=0`) AND `det=1−1=0` (fails `det≠0`) — doubly refused.
- **The seed-guard veto is MEASURED faithful.** It is a post-hoc veto on GenInfer's
  single best matrix, not a search restriction — but the graph's recognized/refused
  verdict matches the independent Python control ("held-recognized OR (discovered ∧
  similarity)") on **14/14** shear views, and every generator the discovery path
  mints under sim mode is a non-degenerate similarity. For full-rank bases the exact
  recovering map is unique, so the winner is the one exact map — no re-selection
  divergence. (Had a similarity-reachable view been wrongly refused, a Rust
  enumeration filter would have been required; it was not.)

## RESULTS (mode: `gen_infer=1, gen_similarity=1`, all arms)

| arm | statistic | result | vs prereg |
|---|---|---|---|
| **A1 INVARIANCE (held similarity)** | `t(O_i)→O_i` | **49/49**, 0 wrong, 0 new | 49/49 ✓ |
| **A2 INVARIANCE (shears — discovery)** | (correct, wrong_id, new)/14 | **1, 0, 13** — 13 shears REFUSED (NEW); shearX(F) recognized as F (held alias) | ~0/14 new, 0 wrong ✓ (+1 held alias, §7) |
| **A3 B1 collinear leak** | recognized? | **REFUSED** (`minted`) | REFUSED ✓ |
| **A3 pairwise discrimination** | spurious/42 | **0/42** | 0/42 ✓ |
| **A3 EXACT-0 identity** | conjunction | **TRUE** (shear_wrong_id=0) | TRUE → **OUTCOME 1** ✓ |
| **A4 untangling (held)** | (raw_wrong, orbit_wrong)/49 | **26, 0** | 26, 0 ✓ |
| **A4 untangling (shears)** | (raw_wrong, orbit_wrong)/14 | **9, 0** | tangles, orbit **0** (was 2 under det1) ✓ |
| **A5 noise** (seeds 39000–39099) | force-maps/100 | **0/100** | 0/100 ✓ |
| **A5 det=0 singular** | force-maps/7 | **0/7** | 0/7 ✓ |
| **A5 shear floor** | force-maps/14 | **1/14** — shearX(F)→F (held alias, §7) | 0/14 predicted; 1 diagnosed residual |
| **A5 non-rigid warp** | force-maps/7 | **0/7** | 0/7 ✓ |
| **A5 scale3 (det=9) — REPORTED** | recognized/7 | **7/7 RECOGNIZED** (discovery mints `[3,0,0,3]`) | 7/7, similarity ADMITS uniform scale ✓ |
| **A5 real-angle 37°/53° (REPORTED)** | aliased/14 | **5/14** | reduced (det1 was 10/14) ✓ |
| **AUDIT held scale2/rot90** | covered_by | **F / V** (preserved) | preserved ✓ |
| **AUDIT minted linear gens** | all similarities? | **all similarity** (e.g. scale3 `[3,0,0,3]`) | all similarity ✓ |
| **AUDIT veto matches control** | shear views | **14/14** | 100% ✓ |

## The three questions the task demanded, ANSWERED by measurement

**1. Is discrimination now exact-0? Are the shears refused?** YES to both — this is
the whole result. Under `|det|=1` the shears (det=1, admitted) over-merged:
`shearY(F)→X`, `shearX(T)→X` (wrong_id=2). Under the similarity restriction those
shears are **REFUSED at discovery**: GenInfer finds the shear matrix (measured:
`shearY(F)` mints `[1,0,1,1]`, `shearX(T)` mints `[1,1,0,1]` — both ortho=1,
non-similarities), `sd_gen_check_sim_no` fires, `gen_explained` stays absent, and
the observation falls through to `sd_mint_quantum` (`status=minted`, `covered_by`
None — a NOVEL identity, not another pentomino's). So `shearY(F)` and `shearX(T)`
stay OFF `X`'s orbit, F and T keep distinct identities, `shear_wrong_id = 0`,
pairwise `0/42`, B1 refused ⇒ **`exact0_identity = TRUE`**. `|det|=1`'s
`shear_wrong_id=2` becomes 0.

**2. Is invariance preserved?** YES — **49/49**, byte-identical to det1's A1 and to
Regime A. The held similarity generators (rot90/180/270, refl_r/refl_c, scale2)
route via the DimInfer codebook BEFORE the GenInfer rung, so the similarity
restriction on *discovery* does not touch held recognition. AUDIT: `scale2(F)→F`,
`rot90(V)→V` preserved.

**3. Is untangling measured, and is the shear-induced tangle gone?** YES. The raw
template control TANGLES on both grids (held raw_wrong **26/49**; shear grid
raw_wrong **9/14**); the orbit-rep separates it to **orbit_wrong = 0** on BOTH.
Critically the shear-grid `orbit_wrong` is now **0**, where `|det|=1` left **2**
(the two aliases) — **the shear-induced tangle is GONE**. The orbit representation
separates exactly what the raw representation tangles (the DiCarlo untangling
signature), and the shears no longer contribute a spurious merge.

## The GROUP characterization this establishes (the real result)

The similarity subgroup cleanly separates ALL THREE failure axes the wall / det1
rungs surfaced, and is the RIGHT group where `|det|=1` was wrong on two of them:

- **det=0 (non-injective)** — EXCLUDED (equal-length fails: `[1,0,1,0]` gives
  eqlen 2≠0). B1 refused, singular-map floor 0/7. `|det|=1` also got this right.
- **shears (det=1, non-conformal)** — EXCLUDED (orthogonality fails: `ortho=1`).
  This is the fix. `|det|=1` WRONGLY ADMITTED these; similarity refuses them.
  A sheared glyph is a novel shape, not a viewing-transform of the original.
- **uniform integer scale (`|det|>1` conformal)** — ADMITTED (`scale3=[3,0,0,3]`:
  ortho 0, eqlen 0, det 9≠0). The DISCOVERY path mints it (`recognized_transformed`,
  minted matrix `[3,0,0,3]`) and `scale3(O_i)→O_i`. `|det|=1` WRONGLY REFUSED this
  (det=9); similarity keeps it, because a uniform scale IS an identity-preserving
  nuisance.

So the identity-preserving nuisance group is the **discrete similarity group**
(rotation, reflection, uniform scale — scaled-orthogonal, angle-preserving), a
PROPER SUBGROUP of `GL(2,ℤ)`: `GL(2,ℤ)` is too big by the shears, and `|det|=1` is
both too big (keeps the shears) AND too small (drops non-unit scale). The
similarity condition `M·Mᵀ=λI` is exactly right on all three axes — and Regime A's
clean 5/5 crossing is now MATCHED on the DISCOVERY path, by the substrate's own
graph-data test rather than a curated held-generator set.

## The single RESIDUAL (§7, reported not gated) — the identifiability limit

**shearX(F) is recognized as F (1/14 on both A2 and the shear floor), and it is an
ALIAS, not a guard leak.** Measured by construction: `shearX(F)` normalizes to
`[(0,0),(0,1),(1,1),(1,2),(2,1)]`, which is **pixel-identical to `refl_c(F)`** (a
held reflection of F). So shearX(F) is recognized as F via the HELD reflection
generator, BEFORE GenInfer ever runs — with **NO linear generator minted** (audit:
`unrestricted_covered_by=F`, `unrestricted_best_matrices=[]`). It maps to F's OWN
identity, so `shear_wrong_id=0` and discrimination stays exact-0 — it is NOT a shear
admitted as a nuisance-of-another-object.

This is the frame/continuum identifiability limit the prereg reserved for real-angle
rotation ("any given circle is stepped"), here in a discrete guise: at 5-cell
resolution this particular shear of F is INDISTINGUISHABLE from a reflection of F —
the two maps produce the same image, and no test on the image alone can separate
them. Per §5/§1.1 the pre-registered floor prediction (0/14) is REPORTED as a
diagnosed residual, NOT relaxed and NOT rescued: the CRUX arm (discrimination
exact-0) is unaffected, and the residual is an aliasing fact about the stimulus, not
a failure of the similarity guard. (The initial runner control also under-counted
this: it computed only "(discovered ∧ similarity)" and omitted the "held-recognized
OR" disjunct the prereg's control definition explicitly includes; corrected to the
pre-registered definition, the veto matches the control 14/14. This was a fix to the
CONTROL to match the prereg, not to any arm.)

## The real-angle count (REPORTED, not gated) — the identifiability limit

5/14 rounded real rotations (37°/53°) still alias onto a lattice similarity (vs
det1's 10/14 and unrestricted `gen_infer`'s 11/14): the similarity restriction
refuses MORE of them than `|det|=1` did, because a rounded real rotation that lands
on a shear or a `|det|≠conformal` map is now refused where `|det|=1` still admitted
some. The residue is the genuine lattice-similarity aliases ("any given circle is
stepped"). Reported, not gated (§5/§8) — the resolution limit, not a leak.

## BOUNDS (§8) — what is NOT shown

Even this FULL crossing is **INSTANCE-level** recognition under the **DISCRETE-
similarity** nuisance group (integer-lattice rotation90 / reflection / integer
uniform scale). The win, precisely stated: **the substrate DISCOVERS its own
identity-preserving nuisance group (the similarity subgroup) from an unrestricted
integer-linear search — minting a discovered similarity it did not hold and refusing
a discovered non-similarity — so the DISCOVERY path matches Regime A's held-generator
crossing, by the substrate's own graph-data criterion for what a nuisance IS.** This
does **NOT** claim "object recognition solved." NAMED frontier, UNCHANGED: continuous
/ real-angle pose (cross-frame CONTINUOUS — with the aliasing identifiability limit
above); lighting / appearance; non-rigid deformation; style; **CATEGORY**-level (vs
instance); the full learned axis-codebook at scale; the failure-mode gates
(McCollough, apperceptive/associative, inversion). The object set is 7 hand-chosen
full-rank free pentominoes; the discrimination claim is over those 42 ordered pairs
+ the shear/floor grids, not over all shapes.

## §9 off-day / sibling gates

`gen_similarity` absent by default ⇒ committed bench unmoved. At engine
`7d5f50c18673`:
- new gate `tests/test_similarity_migrated.py` **10/10** (incl. the on/off
  positive-control: shears alias under sim OFF, refused under sim ON);
- sibling gates **61 passed** together: `test_det1_migrated`,
  `test_gen_infer_migrated`, `test_dimension_inference_migrated`,
  `test_sdloop_vision_migrated` (orbit law {2:1,3:2,4:2,6:2,12:4} unmoved),
  `test_border_ownership_migrated`, `test_identity_untangling_migrated`,
  `test_engine_provenance_migrated`;
- broad vision bench `scripts/rung7_vision_bench.sh` (`data/` symlinked, §10.2):
  **200 passed / 0 failed** — the committed vision bench is unmoved, and its
  no-Python-thresholds scan reports zero findings (the similarity knob is graph
  data).
