# DEPTH AS AN INFERRED DIMENSION — pre-registration (monocular structure-from-motion)

**Committed BEFORE the confirmatory run (PROTOCOL §3).** Extends the chain
gen-mint (`07515e87`) → time (`5aca5a2f`). The operation is the DEPTH sibling of
TimeInfer, one level out: read the **residual** of TimeInfer's single-generator
question as discrete depth.

## The claim, bounded

`DimInfer` already mints a latent Z-dimension when a 2D XY residual is only
explicable by a rotation through Z. **Depth-from-motion is that operation driven
by the TEMPORAL residual.** A scene with real depth translated past a moving eye
produces a 2D image transformation that **NO SINGLE flat (in-plane) generator can
explain** — near regions sweep faster than far ones (motion parallax). That
unexplained residual — **different regions needing different translate
generators** — IS the depth signal. `latent:depth` is the ORDINAL dimension
indexing the regions by their motion (velocity ⇒ depth ordering).

**Scope, held to the frame/continuum invariant (`CLAUDE.md`).** Continuous
perspective (a real velocity gradient, continuous foreshortening) is **CROSS-FRAME
(non-integer)** and is DEFERRED, exactly as real-angle rotation is. What is built
here is the **IN-FRAME, DISCRETE** core: **N depth layers, each translating at a
different INTEGER velocity.** The residual of "explain the whole scene with one
generator" is "you need a SET of translate generators, one per layer"; depth is
the ordinal dimension indexing them by velocity. That is integer/in-frame — the
same boundary gen-mint and time respect. Continuous projective recovery is named
as the cross-frame continuation, NOT claimed.

## The mechanism (BUILT before this prereg; the pilots decided the design)

- Rust **`DepthInfer`** Term (`shape_decode.rs::eval_depth_infer`): partition a
  frame's cells into SURFACES by their non-coord slots (`surface_key` — an
  appearance-coherent region; appearance is observable, depth is NOT read off it).
  Each surface must be a **rigid constant-velocity translate across the whole
  orbit** (the SAME `infer_translate_offset` + exact-equality verification
  `TimeInfer` runs, restricted to the surface). Then the DECISION, which is the
  whole result:
  - **`distinct velocities ≤ 1`** ⇒ the whole scene IS carried by one generator ⇒
    residual ZERO ⇒ **NO `latent:depth`** (`explained=false`, `reason=single_velocity`).
  - **`distinct velocities ≥ 2`** ⇒ one generator cannot carry all regions ⇒
    **MINT `latent:depth`**, ordering surfaces near→far by speed (L1 of the offset).
    `n_layers` = the count of DISTINCT velocities, **read from the data**; surfaces
    sharing a velocity are DEDUPED (the MDL compression).
- Seed **`seeds/depth_axis.json`** (rules `depth_infer_mint` / `depth_infer_floor`),
  flag-gated on `agent.depth_infer_enabled==1`, **OFF by default (§9)**, matching
  only `status=='depth_seq'` observations (the normal decode ladder never produces
  these).
- The mint/floor DECISION is the Rust Term + the seed rule — **never a Python `if`
  over graph state** (the architecture rule IS the experiment).

## The confirmatory arms, and what each failure means

All arms DETERMINISTIC except **H_shuffle**, whose random shuffles draw from
**declared seeds 27100–27499**. Runner: `scripts/depth_measure.py`. Frames are
built from surfaces sharing the SAME coordinate span so no position-gradient
(shear) can fake a velocity difference.

- **H_flat — THE DECISIVE ANTI-FORCED CONTROL. Run FIRST.** A FLAT scene (single
  depth, one integer velocity everywhere), AND a multi-COLOUR scene at a SINGLE
  velocity, → `depth_none`, **NO mint**. *If a flat plane mints depth, the
  operation is hallucinating structure that isn't there — the §1.1 dead-arm / §13
  magic-dimension disease in the depth domain, and this KILLS the claim.* Reported
  as "no depth dimension shorter than a single generator (provisional)".
- **H_depth — IDEAL + MDL.** A 2-layer scene (two integer velocities, same coord
  span) → mint `latent:depth`, `n_layers=2`, correct velocities and near→far
  ordering. MDL: since NO single generator carries the scene, the "without" baseline
  is enumeration (K·cells); "with" = f0 cells + Σ distinct-velocity offsets +
  per-surface depth index + 1. **PASS iff mint AND `mdl_with < mdl_without`.**
- **H_multiheld — §13.1, frozen machinery, multi-held-out.** Several DIFFERENT
  depth structures (2-layer, 3-layer, a REVERSED velocity ordering) → the correct
  DIFFERENT ordering per scene, one frozen Term. **Same-ordering-regardless = forced
  ⇒ FAIL.** Includes a DEDUP scene (3 surfaces, 2 velocities → `n_layers=2`) —
  the compression case.
- **H_shuffle — the floor at the LONGEST window.** Random shuffles of a multi-depth
  scene at window **K=8** → `depth_none` (per-surface velocity no longer constant).
  Gate: **0 spurious mints** (an exact monotone reversal is a legitimate depth
  orbit under negated velocities and is counted separately, NOT spurious — the time
  precedent). A forced minter eventually hallucinates a layering; verified at the
  longest window, not a short one.
- **H_downstream — §1.5 / §13.2, LOAD-BEARING.** The minted depth predicts the
  UNSEEN view at tick K (each surface advanced by its OWN velocity K times) EXACTLY.
  Toggle the flag: **`D_mint>0` AND `D_pred>0`**, `predicted==withheld`. A depth map
  that does not predict a new view is FM-0 decoration. A single (naive) generator
  CANNOT produce this view — depth is what makes it predictable.
- **H_offday — §9.** Flag OFF ⇒ ordered multi-depth scene does NOT mint (inert).

## Predictions (what I expect, declared in advance)

1. **H_flat PASSES** — flat and multi-colour-single-velocity both `depth_none`.
   (The pilot already shows this on both the existing TimeInfer and the new Term;
   if the confirmatory contradicts the pilot, the pilot is retracted.)
2. **H_depth PASSES** — mint, `n_layers` READ as 2, MDL compresses (K·cells ≫ the
   depth description).
3. **H_multiheld PASSES** — 2/3/reversed give three DIFFERENT correct orderings;
   dedup gives `n_layers=2` over 3 surfaces.
4. **H_shuffle PASSES** — 0 spurious mints at K=8.
5. **H_downstream PASSES** — `predicted==withheld`, `D_mint=1`, `D_pred=1`.
6. **H_offday PASSES** — inert.

## Provisos (any of these breaking is a reportable finding, not a rescue)

- **P1 (segmentation).** Surfaces are grouped by observable appearance (non-coord
  slots). Depth is inferred from their differential MOTION, not from appearance —
  the multi-colour-single-velocity control proves appearance alone mints nothing.
  UNLABELLED common-fate segmentation (recovering surfaces from motion when
  appearance is uniform) is a **separate rung**, named not built (the time rung's
  precedent for retinal scope).
- **P2 (in-frame only).** Continuous perspective is cross-frame and deferred; a
  scene whose depth is a real velocity gradient is OUT of scope and will reach the
  floor or require a linear generator. If a single shear DOES explain a scene
  (depth correlated with a position gradient), MDL correctly prefers the shear and
  mints no depth — that is honest, not a miss.
- **P3 (rigidity).** Each layer must translate rigidly at constant integer
  velocity. A rotating/accelerating region reaches the floor (`non_constant_velocity`
  / `non_rigid_surface`). Rotation-as-depth is the linear-generator regime, a
  separate extension.
- **P4 (cardinality is free).** The number of frames AND the number of depth layers
  are READ FROM THE DATA (`window` = frames seen; `n_layers` = distinct-velocity
  count). The runner asserts no hardcoded frame/layer count is used.

## Every constant — what it falls out of (§13)

- **The velocity search bound** is READ from the data (max normalized coord), as
  gen-mint's entry bound was; `max_b=8` is only a safety cap, itself data-scaled
  (inherited from TimeInfer, unchanged).
- **`n_layers`** is `Count` of distinct velocities — falls out of the data, never a
  literal 2 or 3.
- **The depth ordering** falls out of the measured per-surface velocities (L1
  norm), not a chosen scale.
- **No float is committed by this rung.** Depth is an ordinal (ℕ); the orbit test
  is EXACT integer equality. There is nothing to tune.

## §9 regression oracle (must be byte-identical after this rung)

- sd orbit law `{2:1, 3:2, 4:2, 6:2, 12:4}` — UNMOVED (the held path is untouched).
- genmint 6 H-arms PASS; time gate 6/6; dimension-inference 8/8; provenance 7/7.
- fm0 VACUOUS `D=0.0`; fm0b at `8.071079e-01`.
- bench **200/0 with `data/`** (`190/10` without — the §10.2 condition).
- New gate `tests/test_depth_infer_migrated.py`. Seed block **27000–27999**;
  H_shuffle consumes **27100–27499**; 27000–27099 + 27500–27999 exploratory/clean.
  **12000–26999 untouched.**

## The bottom line this rung will answer

**Is DEPTH an inferred dimension in this substrate — recovered MONOCULARLY from
motion, bounded to the discrete integer-velocity class — or not, and why?** The
decisive pair is H_flat (a flat scene mints NOTHING) and H_depth (a multi-depth
scene mints `latent:depth`). Either answer is a result (§7).
