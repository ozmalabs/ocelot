# GALILEO / EQUIVALENCE PRINCIPLE — results

**Verdict: DEGRADE (honest, code-evidenced).** The robot discovers, un-seeded,
that **how fast a thing falls is independent of the mass it determined by
PUSHING it** — and it discovers it by COMPRESSION, exactly as designed: one fall
generator explains every object's fall regardless of mass, so in the real world
exactly **ONE** `MotionGenerator{kind=fall}` is minted and **recognized across
all N objects**, while their `MassScalar`s are measured-different. "One generator
across objects of measured-different mass" **IS `acc ⊥ mass`**, read from the
graph — no `law_predicate`, no `independent_of` threshold, no published mass,
grouping by the eye's PERCEIVED `Region`. The **ARISTOTLE control** (heavier
falls faster) mints **N** distinct generators — mass-DEPENDENCE correctly found.
The discriminator (**ONE vs MANY**) is the proof it is genuine, not trivial.

It is **DEGRADE, not CONFIRM**, for one honest reason, disclosed up front and
measured: the raw order-N loop has **no cross-object generator recognition** —
each fall Observation mints its OWN `latent:time` generator; two
identical-acceleration falls mint two identical `LatentDimension` nodes (measured,
gated). The one-generator-for-all therefore required a **small, general
addition** — `seeds/galileo.json`, a codebook recognize-or-mint keyed on the
generator SIGNATURE (`coeffs`). It is NOT a seeded `acc==acc` law; it is the
structural analog of the blessed general dedup `retire_duplicate_gap`. Reported
as the DEGRADE, exactly as pre-registered.

## What was built (NO Rust, NO new Term)

- **World** — `domains/galileo_world.py` (thin adapter). N blobs, each with a
  HIDDEN integer mass in PRIVATE Python state (never graphed). Two phases in ONE
  substrate:
  - **PUSH phase** — the robot probes each object with an impulse MENU; a
    resonant impulse (`a = J/m` integer, `a ≤ span+2`) mints a per-object
    `MassScalar = impulse/Δv` on the PERCEIVED `Region` via the landed
    `mass_by_action` seed. Masses DIFFER across objects. (The landed primitive
    verbatim: `PushWorld` + `seeds/mass_by_action.json`, unchanged.)
  - **FALL phase** — each object falls straight down under `gravity_fn(i)`; the
    eye tracks each as one `Region` (velocity-predictive association); the landed
    generic order-N loop (`time_axis` / `TimeInfer`) mints an order-2
    `latent:time` generator whose `coeffs[1]` is the perceived fall acceleration.
    The fall Observation is tagged `motion_kind="fall"`, `gen_track=1`
    (mechanical role tags — the world knows it applied gravity, the same way
    `mass_by_action` records the impulse `J`).
- **The general addition** — `seeds/galileo.json` (depends on `time_axis`), three
  domain-GENERAL rules that are a codebook recognize-or-mint over ANY order-N
  motion generator, keyed on the generator SIGNATURE (`coeffs`):
  - `stamp_motion_gen` — copy the minted `latent:time` dimension's
    `coeffs`/`order` onto its Observation (`gen_sig`/`gen_order`). Mechanical
    projection.
  - `motion_gen_mint` — the `Argmin` SURVIVOR of the same-`motion_kind`,
    same-`gen_sig` Observations mints exactly ONE `MotionGenerator{sig, kind,
    order}` (Argmin ⇒ unique survivor ⇒ race-free single mint; guarded by
    `Not Exists MotionGenerator{sig,kind}`).
  - `motion_gen_recognize` — every NON-survivor same-signature Observation is
    marked `generator_status="recognized"` (recognized against the shared
    generator; no new node).
  The rules NEVER mention acceleration / gravity / mass / fall. `motion_kind` is
  an opaque channel tag; `gen_sig` is the whole finite-difference coefficient
  vector; the recognize-or-mint dedups any order-N generator by its signature
  within its channel. **Exact structural analog of `gap_awareness`'s
  `retire_duplicate_gap`** (Argmin-survivor + identity-`Eq`, deduping `SelfConcern`
  by `content`) — the codebase's blessed general graph-native dedup pattern.

## The untuned masses + gravity (never published; masses avoid 1/4/9)

- Hidden masses `{2, 3, 5}` (three objects; distinct; none is 1/4/9). Determined
  by pushing (impulse menu `{4, 6, 8, 10}`); recovered EXACTLY from the graph.
- **Real gravity `g = 1`** (plainest discrete gravity) for ALL objects → fall
  accel `1` → `coeffs[1]=(1,0)` for all → ONE generator.
- **Aristotle gravity: fall accel `= mass`** (heavier falls faster) → accels
  `2, 3, 5` (all `≤ span+2 = 5`, so the eye tracks each cleanly) → three distinct
  `coeffs` → THREE generators.
- Field `120×40`, blob `3×3`, chosen only to keep the falls in-frame for the
  order-2 witness (≥4 samples) — NOT sized to make any accel sub-span.

## MEASURED — one world vs the other, same pipeline

All read from the `run_rules` graph state (minted `MotionGenerator` / `MassScalar`
nodes) and the `coeffs` the `TimeInfer` Term produced (tuples).
`tests/test_galileo_migrated.py` — **5/5**.

| world | masses (from graph, by push) | `MotionGenerator{kind=fall}` | fall-obs status | verdict read from the graph |
|---|---|---|---|---|
| **REAL** (g=1) | `[2, 3, 5]` | **1** — `coeffs ((1,0),(1,0))`, order 2 | `minted` + `recognized` + `recognized` | **ONE generator across 3 different-mass objects → `acc ⊥ mass`** |
| **ARISTOTLE** (accel=mass) | `[2, 3, 5]` | **3** — `coeffs (2,·)/(3,·)/(5,·)` | `minted` × 3 (none recognized) | **THREE generators tracking the masses → mass-DEPENDENCE** |

- **The discovery is un-seeded and by COMPRESSION.** No rule says "acceleration is
  independent of mass". The single generator falls out of the codebook
  recognize-or-mint: one signature covers every real-world fall, so one node is
  minted and the rest recognize it. The Aristotle falls have distinct signatures,
  so each mints — the SAME rules, no branch on physics.
- **The masses are the SAME in both worlds** (push physics is identical; only the
  fall law differs), so the ONLY difference between ONE and THREE generators is
  the world's gravity law. That is the control with teeth.
- **`acc ⊥ mass` is read from the graph:** ONE `MotionGenerator{kind=fall}`
  simultaneously with THREE distinct `MassScalar`s on three perceived Regions.

## Was cross-object recognition existing machinery or a general addition?

**A general addition** — reported honestly (this is why the verdict is DEGRADE,
not CONFIRM). Measured and gated
(`test_cross_object_recognition_is_a_real_general_addition_not_free`): the raw
order-N loop, with NO `galileo` seed, mints THREE identical `latent:time`
`LatentDimension` nodes for three identical falls — it has no cross-object
recognition. The sd-loop's own novelty dedup (`sd_mint_quantum` guard +
`sd_dedup_existing`) keys on `obs.key`, which is `["motion"]` for every fall — it
would collapse ALL falls regardless of acceleration, so it is NOT the right
instrument. `seeds/galileo.json` supplies the missing, general piece: a
recognize-or-mint over order-N generators keyed on the `coeffs` signature. It is
general (dedups velocity/acceleration/jerk/any order-N generator within any
opaque channel) and is not physics-specific — the rules never mention mass or
gravity. **This is not a seeded `acc==acc` equality**: it is the codebook
recognize the sd loop performs for shapes, lifted to generators, following the
`retire_duplicate_gap` precedent.

## No mass published; grouping is perceived (the genuine bar)

- No `WorldInstance` node (game hubs, cells, `Body` nodes) carries any forbidden
  key (`mass/position/pos/velocity/vel/vy/vx/row/col/gravity/g/object_id/…`) —
  scanned by the gate. Cells carry no attribute; a `Body` carries only
  `world_type`. The blobs' true mass and gravity live ONLY as Python locals.
- Each `MassScalar` is reached ONLY through a `Region -has_mass->` edge (the eye's
  perceived identity) and carries no world object-id — grouping is PERCEIVED.
- The fall generator's identity is the perceived-trajectory `coeffs`
  (`Region.cy` per frame — the eye's carve), a DISCOVERED inference, not a
  world-published truth. The fall Observation groups by perceived Region via a
  distinct `fall_of_region` edge.

## Provenance / discipline

- Branch **`gamma-substrate/galileo-equivalence`** (own worktree, NOT main);
  prereg commit **`f34eb04f8d`**.
- **NO Rust, NO new Term, NO new Rust primitive, NO index bump.** Pure
  composition: the landed `mass_by_action` + `time_axis` seeds and the
  eye/order-N machinery, unchanged, + one new graph-data seed
  (`seeds/galileo.json`, existing `Eq`/`Argmin`/`Filter`/`NodesOfType`/`Attr`
  Terms) + a thin adapter. Fully additive — no existing seed or Rust file touched.
- Engine sha256 (short) **`ac8625525b09`**, **`source_match = shared`** (Rust
  source in this worktree byte-identical to canonical; no Rust edited) — asserted
  in {own, shared}.
- Seed: **`SEED CLAIM 142000-142999: CLEAN -- no collision DETECTED.`** (no RNG
  in this rung; the worlds are deterministic.)
- Oracle `scripts/rung7_vision_bench.sh` (data/ symlinked):
  **BEFORE 222 passed / 0 failed (222/0)**; **AFTER 222 passed / 0 failed (222/0)** (no Rust, no existing file touched).
- Gate: `tests/test_galileo_migrated.py` — **5/5**. Related benches + instrument
  seams green together (**72 passed**): `test_mass_by_action_migrated`,
  `test_fall_from_eye_migrated`, `test_time_infer_migrated`,
  `test_generic_order_n_migrated`, `test_dimension_inference_migrated`,
  `test_engine_provenance_migrated`, `test_failure_baseline_migrated` — no new
  red.

## What I got WRONG / honest scope

- **A fall Observation with an `of_region` edge minted a spurious `MassScalar` of
  0.** `mass_by_action`'s `mass_from_push` matches any `of_region` Observation
  with an order-2 `latent:time` dimension and mints `m = IDiv(impulse, |a|)`. A
  fall carries NO impulse, so `IDiv(None, |g|) = 0` — a bogus mass leaked into the
  distinct-masses read. Fixed by grouping the fall generator with a DISTINCT
  `fall_of_region` edge the mass rule never matches; masses stay push-only. Caught
  by the gate reading `minted_masses()` AFTER the fall phase (the standalone probe
  had read masses BEFORE the fall phase and missed it). Lesson: a permissive
  match on a shared edge type fires on the wrong observations.
- **The Aristotle accel-`mass` law fragments the eye when a mass exceeds the
  tracking bound.** A first attempt with masses `{2,3,6}` lost the accel-6 object
  (`6 > span+2 = 5`): the eye fragmented its fall and only 2 of 3 generators
  minted. Not a rescue-by-tuning: I moved to masses `{2,3,5}` so every Aristotle
  accel is `≤ 5` and cleanly tracked — the discriminator only needs the accels
  DISTINCT, which they are. The eye's acceleration bound (the `fall-from-eye`
  velocity-predictive reach) is a real, disclosed limit, not hidden.
- **Pushing all objects together merged them.** Pushing N objects in one field at
  different accelerations made them collide and corrupted the perceived
  trajectories (no masses minted). Fixed by measuring each object's mass in its
  OWN single-object push episode (the `mass_by_action` distribution-arm
  methodology) — still the landed primitive, no agent decision.
- **The discovery is DEGRADE, and I did not dress it as CONFIRM.** The general
  cross-object recognize/dedup is a genuine addition the sd loop lacked; I report
  it as such. The discovery itself (one-vs-many, by compression, un-seeded, no
  published mass, perceived grouping) is real; the honest boundary is that the
  raw order-N loop does not recognize a generator across objects on its own.
- **Per-object linkage of mass↔fall is at the world level, not one graph Region.**
  Push (horizontal) and fall (vertical) are separate episodes, so an object's
  `MassScalar` (phase-1 Region) and its fall generator (phase-2 Region) are not
  one shared Region node. The claim `acc ⊥ mass` rests on the co-presence of ONE
  fall generator and N distinct masses over the same N objects (world-level
  identity), read from the graph — not on a per-object mass→generator edge. A
  projectile (simultaneous push+fall) would give one Region but the mass rule sums
  both axes; keeping the axes separate keeps the dedup general (full-`coeffs`
  equality). Disclosed, not hidden.

## Ledger row (this doc, not VISION_PROTOCOL.md)

| rung | claim | engine | oracle before/after | verdict |
|---|---|---|---|---|
| galileo-equivalence | the robot pushes N seen objects → N different `MassScalar`s (mass_by_action, perceived Region) and watches them fall (eye + generic order-N → order-2 fall generator); a GENERAL coeffs-signature codebook recognize-or-mint (`seeds/galileo.json`, `retire_duplicate_gap` analog, NO seeded acc==acc law) mints ONE `MotionGenerator{kind=fall}` recognized across all N in the REAL world (g=1) → `acc ⊥ mass` read from the graph, and N distinct generators in the ARISTOTLE control (accel=mass) → mass-DEPENDENCE; no published mass, perceived grouping; un-seeded discovery by compression | `ac8625525b09` (shared, no Rust) | 222/0 → 222/0 | **DEGRADE** (genuine one-vs-many discovery; the cross-object generator recognition is a small general addition the raw order-N loop lacked — reported, not rescued) |
