# GALILEO / EQUIVALENCE PRINCIPLE — pre-registration

**Claim under test (un-seeded):** a robot that (a) PUSHES seen objects to
discover their inertial `MassScalar` by action (`m = impulse/Δv`, the landed
`mass_by_action` primitive) and (b) watches those same objects FALL under one
untuned gravity (the eye tracks; the landed generic order-N loop mints the
order-2 fall generator from the perceived trajectory) will discover, purely by
COMPRESSION, that **how fast a thing falls is independent of the mass it
determined by pushing** — because ONE fall generator explains EVERY object's
fall regardless of its mass, so exactly one generator is minted and every
subsequent object's fall is RECOGNIZED against it, while the objects'
`MassScalar`s differ. "One generator across objects of measured-different mass"
IS `acc ⊥ mass`, by construction. No `law_predicate`, no `independent_of`
threshold, no published mass, grouping by the eye's PERCEIVED `Region`.

## Design (compose landed primitives; thin adapter; graph-native discovery)

- **World** (`domains/galileo_world.py`, thin pixel+affordance adapter). N blobs,
  each with a HIDDEN integer mass in PRIVATE Python state (never graphed). Two
  phases in ONE substrate:
  - **PUSH phase** (horizontal): sustained per-tick impulse `J` per object →
    uniform horizontal acceleration `a_x = J/mass`; the eye tracks each as one
    `Region`; the landed `mass_by_action` seed (`m = IDiv(J, |a|)`) mints a
    per-object `MassScalar` keyed to the PERCEIVED `Region`. Masses DIFFER across
    objects. (Reuses the landed primitive verbatim.)
  - **FALL phase** (vertical): each object falls under gravity; the eye tracks;
    the landed generic order-N loop (`time_axis` / `TimeInfer`) mints an order-2
    `latent:time` generator whose `coeffs[1]` IS the perceived per-tick
    acceleration. The fall Observation is tagged `motion_kind="fall"` (mechanical
    — the world knows it applied gravity, the same way `mass_by_action` records
    the impulse `J` as the action parameter).
- **The cross-object recognize/dedup — a GENERAL addition** (NOT existing
  machinery; NOT a seeded `acc==acc` law). Measured up front: the raw order-N
  loop mints a SEPARATE `latent:time` generator per Observation with NO
  cross-object recognition (two identical-acceleration falls → two identical
  `LatentDimension` nodes). So the one-generator-for-all requires a small honest,
  general addition. `seeds/galileo.json` (depends on `time_axis`) adds three
  domain-GENERAL rules that are a codebook recognize-or-mint over ANY order-N
  motion generator, keyed on the generator SIGNATURE (`coeffs`) — the exact
  structural analog of the blessed general dedup `retire_duplicate_gap`
  (gap_awareness) which dedups `SelfConcern` by `content`:
  - `stamp_motion_gen`: copy the minted `latent:time` dimension's `coeffs`/`order`
    onto its Observation (`gen_sig`/`gen_order`) — mechanical projection.
  - `motion_gen_mint`: the Argmin SURVIVOR of the set of same-`motion_kind`,
    same-`gen_sig` Observations mints exactly ONE `MotionGenerator{sig, kind,
    order}` (Argmin makes the survivor unique → race-free single mint; guarded by
    `Not Exists MotionGenerator{sig,kind}` for fixpoint safety).
  - `motion_gen_recognize`: every NON-survivor Observation with the same
    `gen_sig` is marked `generator_status="recognized"` (recognized against the
    shared generator, no new node).
  The rules NEVER mention "acceleration", "gravity", "mass", or "fall" —
  `motion_kind` is an opaque channel tag and `gen_sig` is the whole
  finite-difference coefficient vector; the recognize-or-mint dedups any order-N
  generator by its signature. This is reported as the DEGRADE addition.
- **Read the discovery FROM THE GRAPH.** Distinct fall generators =
  `MotionGenerator{kind="fall"}` node count. Masses = `MassScalar.mass` values on
  the perceived `Region`s. `acc ⊥ mass` = ONE fall generator across N objects
  whose `MassScalar`s are measured-different.

## Worlds (both run the SAME pipeline)

- **Real world:** every object falls at the SAME untuned acceleration `g` →
  identical `coeffs` → exactly ONE `MotionGenerator{kind=fall}`, recognized
  across all N objects; N distinct `MassScalar`s.
- **ARISTOTLE control (wrong physics — heavier falls faster):** fall acceleration
  DEPENDS on mass → distinct `coeffs` per object → N distinct
  `MotionGenerator{kind=fall}` (no cross-object recognition) → mass-DEPENDENCE
  correctly found. Same pipeline, same rules, same adapter — only the world's
  gravity law differs.

## Untuned constants (never published; masses avoid 1/4/9)

- Hidden masses `{2, 3, 6}`. Push impulse `J=6` → horizontal `a_x = 3, 2, 1` →
  recovered masses `2, 3, 6` (single untuned impulse, all resonant, `a_x ≤ 5`).
- Real gravity `g = 1` (plainest discrete gravity) for ALL objects → fall accel
  `1` → `coeffs[1]=(1,0)` for all.
- Aristotle gravity: fall accel `= mass` (heavier faster) → accels `2, 3, 6`.
  (If `6 > span+2` fragments the eye, the acceleration is capped to the tracking
  bound and reported; the discriminator only needs the accels DISTINCT, which
  they are at `{2,3,...}`.)
- Field / blob sized only to keep the fall in-frame for the order-2 witness
  (≥4 samples); NOT sized to make any accel sub-span (the forbidden tune).

## Discriminator (registered BEFORE any number)

- **CONFIRM:** real world → exactly ONE `MotionGenerator{kind=fall}`,
  recognized across all N objects whose `MassScalar`s are measured-different
  (`acc ⊥ mass`, read from the graph); Aristotle world → N distinct fall
  generators (mass-dependence). No seeded predicate, no published mass, perceived
  `Region` grouping. The cross-object recognize/dedup is the ONE small general
  addition (`seeds/galileo.json`), reported as such → this lands as **DEGRADE**
  (honest general addition), not a clean CONFIRM, UNLESS the addition turns out
  unnecessary (existing machinery already recognizes) — measured says it is
  necessary.
- **DEGRADE (expected):** the one-generator-for-all needs the general
  recognize/dedup above (the sd loop lacks cross-object generator recognition);
  built generically (coeffs-signature codebook, `retire_duplicate_gap` analog),
  stays general. Report exactly this.
- **FALSIFY (report honestly, do NOT rescue):** if the only way to collapse N
  per-object generators to one is a seeded `acc==acc`/`independent_of(mass)`
  predicate; OR the discriminator needs published mass / a Python acc-equality
  comparison; OR the eye/order-N cannot cleanly mint identical fall generators
  across objects (fragmentation loses the fall before the order-2 witness). Name
  the specific blocker. No rescue by seeding the law, publishing mass, tuning
  geometry, or hand-coding an acc-equality check.

## Discipline

- Compose the landed primitives + one general seed. Thin world adapter
  (mechanical I/O only). Discovery is graph-native (the order-N loop + the three
  general rules), NOT a Python comparison of accelerations. Prefer NO Rust — the
  cross-object recognize is graph data (Eq/Argmin/Filter/NodesOfType), not an
  engine change. Confirmed feasible on list-valued `coeffs` before this prereg.
- Seed block: `SEED CLAIM 142000-142999: CLEAN -- no collision DETECTED.`
- Engine `ac8625525b09`, `source_match = shared` (no Rust edited).
- Oracle `scripts/rung7_vision_bench.sh` (data/ symlinked) BEFORE and AFTER.
- Gate `tests/test_galileo_migrated.py`; verify on the PRODUCT
  (`native.evaluate()` tuples + `run_rules` graph state), never a process wait.
