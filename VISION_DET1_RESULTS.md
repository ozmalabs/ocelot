# |det|=1 — the UNIMODULAR restriction on GenInfer — RESULTS

*Pre-registered in `VISION_DET1_PREREG.md` (committed `c5c7d89d`, BEFORE this
run). Runner `scripts/det1_measure.py`, gate `tests/test_det1_migrated.py`,
pinned `results/det1.json`. Noise floor seeds 38000–38099 (never previously
used). Base `main` HEAD **10796886**.*

**Provenance (§10):**
`engine 7d5f50c18673 @ …/runners/dsl/python/substrate_rs/_native.abi3.so
[shared build from …/gamma-substrate — Rust source identical]`. This rung adds
**NO Rust** — the `|det|` restriction is a SEED GUARD (graph data over existing
Terms). The shared canonical engine is a legitimate build of this tree's source
(`test_engine_provenance_migrated` green, source `own`/`shared`). **No new
engine hash: shared-legit, because there is truly no `.rs` change.**

## HEADLINE — OUTCOME 2 (PARTIAL): the deeper finding, exactly as predicted

**`|det|=1` FIXES the det=0 universal-container collapse but does NOT recover a
clean identity, because SHEARS (det=1) survive the restriction and are
identity-CHANGING.** The identity-preserving nuisance group is the SIMILARITY
subgroup (held rotation / reflection / scale), **NOT** the full unimodular
group `GL(2,ℤ)`. Every pre-registered prediction held.

- **AUDIT verdict: SEED GUARD, no new Rust.** GenInfer's inferred `matrix`
  (`shape_decode.rs:2137`) is read as graph data; the determinant
  `m00·m11 − m01·m10` and `|det|=1` are computed by `Nth`/`Times`/`Minus`/`Abs`
  Terms in a rule `where`-clause (`seeds/shape_decode_loop.json`:
  `sd_gen_check_uni_yes` / `sd_gen_check_uni_no`, gated on a new
  `agent.gen_unimodular` flag, OFF by default; `sd_gen_check` gains one
  suppression clause). The vision bench's own scan confirms it:
  *"[no-python-thresholds scan findings] (none — every knob is graph data)."*
- **The seed-guard veto is MEASURED faithful.** It is a post-hoc veto on
  GenInfer's single best matrix, not a search restriction — but every one of the
  **13 linear generators the discovery path minted is `|det|=1`** (twelve `+1`,
  one `−1`), and the graph's recognized/refused verdict matches the independent
  determinant control on 100% of views. For full-rank bases the exact recovering
  map is unique, so the winner's det equals the applied transform's det — no
  re-selection divergence. (Had any `|det|=1`-reachable view been wrongly refused,
  a Rust enumeration filter would have been required; it was not.)

## RESULTS (mode: `gen_infer=1, gen_unimodular=1`, all arms)

| arm | statistic | result | vs prereg |
|---|---|---|---|
| **A1 INVARIANCE (held similarity)** | `t(O_i)→O_i` | **49/49**, 0 wrong, 0 new | 49/49 ✓ |
| **A2 INVARIANCE (shears — discovery)** | (correct, wrong_id, new)/14 | **12, 2, 0** — `shearY(F)→X`, `shearX(T)→X` | ~12/14, 2 wrong ✓ |
| **A3 B1 collinear leak** | recognized? | **REFUSED** (`minted`, was `→L`) | REFUSED ✓ |
| **A3 pairwise discrimination** | spurious/42 | **0/42** | 0/42 ✓ |
| **A3 EXACT-0 identity** | conjunction | **FALSE** (shear_wrong_id=2) | FALSE → OUTCOME 2 ✓ |
| **A4 untangling (held)** | (raw_wrong, orbit_wrong)/49 | **26, 0** | 26, 0 ✓ |
| **A4 untangling (shears)** | (raw_wrong, orbit_wrong)/14 | **9, 2** | tangles, orbit 2 ✓ |
| **A5 noise** (seeds 38000–38099) | force-maps/100 | **0/100** | 0/100 ✓ |
| **A5 det=0 singular** | force-maps/7 | **0/7** | 0/7 ✓ |
| **A5 scale3 (det=9, non-held)** | force-maps/7 | **0/7** | 0/7 ✓ |
| **A5 non-rigid warp** | force-maps/7 | **0/7** | 0/7 ✓ |
| **A5 real-angle 37°/53° (REPORTED)** | aliased/14 | **10/14** | reduced, not 0 ✓ |
| **AUDIT held scale2/rot90** | covered_by | **F / V** (preserved) | preserved ✓ |
| **AUDIT minted linear gens** | all `|det|=1`? | **13/13 unimodular** | all unimodular ✓ |

## The three questions the task demanded, ANSWERED by measurement

**1. Did `|det|=1` fix the det=0 collapse (B1)?** YES. Collinear `I` presented
against the full-rank codebook was recognized as `L` under unrestricted
`gen_infer` (`recognized_transformed`) and is **REFUSED** (`minted`, no
`covered_by`) under `gen_unimodular`. A singular (det=0) map applied to every
object is refused **0/7**. The universal-container leak the wall was DEFINED by
is closed on the degenerate axis.

**2. Did the shears over-merge?** YES — they PERSIST, and this is the deeper
finding. `shearX`/`shearY` are **det=1**, so `|det|=1` ADMITS them: they are
discovered (all 13 minted shear-generators are unimodular, det ±1), and
**`shearY(F)` still aliases onto `X`** and **`shearX(T)` onto `X`** (2/14 wrong
identity). A sheared pentomino lands on a DIFFERENT pentomino's cell set via a
legitimately-unimodular map. So "same unimodular orbit" is NOT an equivalence
that preserves instance identity — a shear (volume-preserving but non-conformal)
CHANGES the object. DISCRIMINATION is therefore **not exact-0**, and we do NOT
relax that verdict to force a pass (§5/§1.1): the failure IS the result.

**3. Is integer-scale invariance lost?** NO — and the framing needed
correcting by measurement. `|det|=1` excludes integer scale from the
*discovery* path (`scale3`, det=9, is refused 0/7), but `scale2` (det=4) is a
**HELD** `DimensionGenerator` that fires in the DimInfer rung BEFORE GenInfer,
so `scale2(F)→F` and `rot90(V)→V` are recognized under uni mode unchanged (A1
49/49; AUDIT covered_by F / V). **Held similarity scale is preserved; only a
non-held integer scale, which would require discovery, is refused.** The naive
"`|det|=1` loses scaling" is true of the discovery path alone and false of the
system, which carries scale as a held generator.

## The GROUP characterization this establishes (the real result)

`|det|=1` cleanly separates the two failure axes the wall rung diagnosed:

- **det=0 (non-injective)** — EXCLUDED. Fixes B1 and the singular-map floor.
  These maps are not invertible; you cannot un-collapse a line; they are not
  nuisances. `|det|=1` is exactly right here.
- **shears (det=1, non-conformal)** — ADMITTED, and they should NOT be. They are
  invertible and form a group, but they do not preserve the *identity* of a
  rigid glyph: a sheared `F` is an `X`, not a viewing-transform of `F`.

So the identity-preserving nuisance group is the **discrete similarity group**
(rotation, reflection, uniform scale — angle- and shape-preserving up to
scale), which is a PROPER SUBGROUP of `GL(2,ℤ)`. The unimodular group is too big
by exactly the shears; the rung-A held-generator set (which contains no shear)
is the right group, and Regime A's clean 5/5 crossing is why. `|det|=1` is the
correct fix for the det=0 half of the wall-rung negative and a MEASURED
demonstration of where the boundary actually sits for the shear half.

## The real-angle count (REPORTED, not gated) — the identifiability limit

10/14 rounded real rotations (37°/53°) still alias onto a lattice similarity
(vs 11/14 rotation-only force-maps under unrestricted `gen_infer`): the
restriction refuses one, the rest persist because a rounded near-lattice
rotation IS close to a unimodular map. This is the frame/continuum invariant
(“any given circle is stepped”), the resolution limit, NOT a leak — which is
why the clean floor is the resolution-independent non-rigid warp (0/7), and the
real-angle number is reported, not gated (§5/§8). `X` (D4-symmetric) is
correctly recognized as itself at both angles.

## BOUNDS (§8) — what is NOT shown

INSTANCE-level recognition, bounded to the SIMILARITY subgroup (translation,
90° rotation, reflection, HELD integer scale) — NOT the full unimodular group
(shears break identity), and NOT continuous pose. **NOT** "object recognition
solved." NAMED frontier, unchanged: continuous / real-angle pose (cross-frame
CONTINUOUS, with the aliasing identifiability limit above);
lighting / appearance; non-rigid deformation; style; **CATEGORY**-level (vs
instance); the full learned axis-codebook at scale; the failure-mode gates
(McCollough, apperceptive/associative, inversion). The object set is 7 full-rank
free pentominoes; claims are over those 42 pairs + the shear/floor grids. A
`GenInfer` restricted to the *similarity subgroup* (rotation/reflection/scale,
excluding shears) is the named next fix this rung motivates but does not build.

## §9 off-day / sibling gates

`gen_unimodular` absent by default ⇒ committed bench unmoved. At engine
`7d5f50c18673`:
- new gate `tests/test_det1_migrated.py` **7/7**;
- sibling gates **54 passed** together: `test_gen_infer_migrated`,
  `test_dimension_inference_migrated`, `test_sdloop_vision_migrated` (orbit law
  {2:1,3:2,4:2,6:2,12:4} unmoved), `test_border_ownership_migrated`,
  `test_identity_untangling_migrated`, `test_engine_provenance_migrated`;
- broad vision bench `scripts/rung7_vision_bench.sh` (`data/` symlinked,
  §10.2): **200 passed / 0 failed** — the committed vision bench is unmoved,
  and its no-Python-thresholds scan reports zero findings (the `|det|` knob is
  graph data).
