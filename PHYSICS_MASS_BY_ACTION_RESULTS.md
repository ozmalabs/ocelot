# PHYSICS — INERTIAL MASS BY ACTION (results)

**Verdict: CONFIRM** (mechanism + exact recovery), with one honest boundary
disclosed below. The agent PUSHES objects it SEES and discovers their HIDDEN
inertial mass FROM THE PUSH — the operational definition of inertial mass, F=ma
inverted (`m = impulse / Δv`). The world outputs ONLY pixels + affordances; the
mass lives in PRIVATE Python state and is NEVER graphed. Grouping is by the eye's
PERCEIVED `Region` identity, never a world id. NO Rust — pure composition of the
existing eye + order-N + action-choice machinery plus ONE graph-native seed rule.

## What was built (NO Rust, NO new Term)

- **Push world** — `domains/push_world.py` (thin adapter). N blobs, each with a
  HIDDEN integer mass (Python-local, never graphed). Each tick it renders the
  blobs' positions to a 0/1 pixel field and hands it to the eye
  (`native.segment` → `segment_and_track`). `legal_actions` offers, per SEEN
  `Region`, `("push", region_node, impulse)` over a small impulse menu.
  `apply_action` maps the pushed Region to the private object under it (nearest
  perceived centroid — world book-keeping, never published), applies the world's
  PHYSICAL response `v += impulse / mass`, integrates `pos += v` (semi-implicit
  Euler, no gravity, no friction), re-renders. Pixels + affordances out.
- **Act on a seen object** — the agent selects the push via the existing
  `choose_action_meta_curious(..., target_fn)`. `target_fn` returns the object's
  `Body` node, which the adapter binds `seen_as` → the perceived Region, so a push
  on a SEEN thing lifts `asym_count` (see→link→ACT). The choice is the seeded
  `action_score_term`; the adapter only measures and stamps.
- **Discover mass by action** — a sustained push (the same action every tick)
  makes the object accelerate uniformly at `a = J/m`; the eye tracks it as ONE
  Region (the velocity-predictive association fix carries the acceleration) and
  the dimension-generic order-N loop (`TimeInfer` / `time_axis`, the SAME machinery
  that mints the fall's order-2) mints an ORDER-2 `latent:time` dimension whose
  `coeffs[1]` leading vector IS the perceived per-tick `Δv` (= a). This constancy
  of `Δv` across the repeated pushes IS the invariance.
- **The graph-native rule** — `seeds/mass_by_action.json` (`mass_from_push`): on a
  time-inferred motion Observation carrying the impulse `J` and an ORDER-2 latent
  dimension, mint `MassScalar = IDiv(J, |a|)` (with
  `|a| = |coeffs[1][0]| + |coeffs[1][1]|`, direction-agnostic) linked to the
  PERCEIVED Region via `has_mass`. Guards: order exactly 2 (a single push is
  order-1 → no mass); nonzero acceleration; idempotent per Observation
  (`yielded_mass`), so DIFFERENT-impulse pushes each mint a scalar and `J/a` is
  invariant. **Python computes NO `impulse/Δv`** — the ratio is the `IDiv` Term in
  the rule; Python only computes the WORLD's private `Δv = J/mass` response and
  mechanically ingests the perceived trajectory.

## The untuned masses + impulse menu used

- Hidden masses: adjacent `{2, 3}` for the ratio arm (the HARDEST to separate — the
  opposite of a separability tune); `{3}`, `{6}`, `{2,6}`, `{3,3}` for the other
  arms; and a random draw of 4 from `{2,3,4,5,6,7}` (seed 140100, in the
  registered block) for the distribution arm. NONE is 1/4/9.
- Impulse menu: small integers `{6, 10, 12, 14, 15}` (distribution arm); single
  values `{6}`, `{12}`, `{18}` for the invariance/headline arms.
- **Disclosed requirement (a property of the integer eye, NOT a tune):** exact
  recovery needs the perceived acceleration `a = J/m` to be an INTEGER
  (`J` a multiple of `m`) AND `a ≤ span+2 = 5` (the eye's tracking radius — the
  velocity-predictive fix absorbs ACCELERATION, not velocity, within the radius).
  This is the frame/continuum invariant in action: in-frame coordinates are
  integer, so mass is witnessed exactly at the integer-`a` resonances `J ∈ {m,2m,…}`
  and is silent between them.

## MEASURED — the agent pushes seen objects and discovers their mass

All products read from `native.evaluate()` (TUPLES) and the `run_rules` graph
state; masses read FROM THE GRAPH via `Region -has_mass-> MassScalar.mass`.
`tests/test_mass_by_action_migrated.py` — **10/10**.

| arm | hidden mass(es) | impulse J | perceived a | minted MassScalar (from graph) | error |
|---|---|---|---|---|---|
| **headline** (agent-chosen push, order-2 PRODUCT + graph) | 3 | 6 | 2 | **3** | 0 |
| single push then coast (CONTROL) | 3 | 6 | — (order-1) | **none** | — |
| equal mass (CONTROL) | 3, 3 | 6 | 2, 2 | **3, 3** | 0 |
| **ratio** (adjacent, hardest) | 2, 3 | 6 | 3, 2 | **2, 3** → ratio 2/3 = hidden ratio | 0 |
| **invariance across impulses** | 6 | 6 / 12 / 18 | 1 / 2 / 3 | **6 / 6 / 6** (J/Δv constant) | 0 |
| grouping by perceived Region | 2, 6 | 6 | 3, 1 | **2, 6** on two distinct Region nodes | 0 |
| distribution (drawn {2,3,4,5,6,7}) | 4 drawn | resonant menu J | int | **= hidden mass at every resonant J** | 0 |
| **DEGRADE** (non-resonant) | 3 | 5 | 5/3 (fractional) | **none** (order-2 floors) | — |

- **Headline (CONFIRM):** the agent CHOSE to push a SEEN Region every tick
  (`choose_action_meta_curious` + `target_fn`; every chosen action a push on a
  target with a `seen_as` edge). The order-N Term's verdict on the perceived
  trajectory is `order == 2` (PRODUCT, tuple), and the `run_rules` fixpoint mints
  `MassScalar{mass:3}` on the perceived Region — recovering the hidden mass, read
  from the graph. Un-seeded (the mass VALUE is discovered; only the general rule
  is seed data, like `time_axis`).
- **Controls have teeth:** a single push then coast is constant velocity → order-1
  → NO mass (insufficient evidence). Equal hidden masses → equal scalars. Two
  adjacent masses `2,3` → scalars `2,3` (ratio exact). The `J/Δv` invariant holds
  across three different impulses on one mass (`6 = 6/1 = 12/2 = 18/3`).
- **Grouping is PERCEIVED:** two distinct-mass objects are carved as two distinct
  eye Regions and get two distinct scalars keyed to those Region NODES; the mass
  rule reaches the scalar only through `has_mass` from a live eye Region, and the
  MassScalar carries only `{mass, impulse, accel, source}` — no world object-id.
- **No published mass:** the world graph (hub, cells, Regions, Bodies) carries no
  `mass`/position/velocity/object-id key (scanned by the gate). A Body carries only
  its type marker. The blobs' true mass exists ONLY as a Python local.

## The DEGRADE boundary (honest)

The order-N witness is EXACT (a witnessed CONSTANT second difference). On the
synthetic integer-rendered world the eye is EXACT (it perceives integer centroids),
so recovery is **exact-or-silent, not noisy**: for a RESONANT impulse (`a = J/m`
integer) the mass is recovered with ZERO error; for a NON-RESONANT impulse
(fractional `a`) the integer eye jitters the perceived 2nd difference, the order-2
witness floors, and NO mass is minted. Verified on the PRODUCT: for mass 3, J=5
(`a = 5/3`), the eye still TRACKS the object (one live Region, 8 samples — NOT a
tracking failure) but `TimeInfer(...).explained` is not True, so the rule never
fires. Every object in an untuned distribution has at least one resonant menu
impulse (coverage total in the tested pool), so the agent recovers each object's
mass by probing the menu; `J/a` is invariant across the resonant impulses (= the
mass). **The ~7–9% real-data confab floor is NOT exercised here** — synthetic
integer rendering makes the eye exact — so it is a named SCOPE condition, not a
hidden weakness (the frame/continuum invariant: the fractional acceleration is a
cross-frame quantity the in-frame integer eye cannot witness as a constant).

## Push-count needed

The order-2 witness minimum is 4 samples (a witnessed constant 2nd difference).
The arms use 6 ticks (7 perceived samples) for margin. The tracked Region must be
ALIVE at discovery time, so episodes are kept in-field (the object must not exit;
`a ≤ 5` keeps the eye tracking through the acceleration).

## Provenance / discipline

- Branch **`worktree-agent-a0a7c09290807ed6c`** (own worktree, NOT main); prereg
  commit **`9d2541e3df`**.
- **NO Rust, NO new Term, NO new Rust primitive.** Pure composition: the push
  adapter (`domains/push_world.py`) + one graph-native seed rule
  (`seeds/mass_by_action.json`, using the existing `IDiv`/`IndexAt`/`Abs`/`Plus`/
  `Attr` Terms) + the unchanged eye (`segment_and_track`), order-N
  (`TimeInfer`/`shape_decode.rs`), and action-choice
  (`choose_action_meta_curious`) machinery.
- Engine sha256 (short) **`ac8625525b09`**, **`source_match = shared`** (Rust
  source in this worktree byte-identical to canonical; no Rust edited) — asserted
  in {own, shared}.
- Seed: **`SEED CLAIM 140000-140999: CLEAN -- no collision DETECTED.`** (noise RNG
  seeded at 140100; every other arm deterministic).
- Oracle `scripts/rung7_vision_bench.sh` (with `data/` symlinked):
  **BEFORE 222 passed / 0 failed (222/0)**; **AFTER 222 passed / 0 failed (222/0)**
  (no Rust, no existing file touched).
- Gate: `tests/test_mass_by_action_migrated.py` — **10/10**. Related benches +
  instrument seams green together (67 passed): `test_fall_from_eye_migrated`,
  `test_time_infer_migrated`, `test_generic_order_n_migrated`,
  `test_meta_curiosity_and_t3_migrated`, `test_engine_provenance_migrated`,
  `test_failure_baseline_migrated` — no new red.

## What I got WRONG / honest scope

- **Dead-Region node-id reuse (a real bug I hit).** My first `discover_masses` fed
  EVERY non-ground Region's trajectory, including transient/reaped ones. The eye
  REAPS dead Regions and their node ids get recycled, so a stale trajectory key
  became a different-typed node → `Γ rejects (Observation) -[of_region]->
  (Observation)`. Fixed by filtering to LIVE regions
  (`rnode in neighbours(game,"has_region")`). Lesson: a reaped node id is not
  inert — it can come back as another type.
- **The tracked object exits the field on the last push, reaping its Region.**
  End-of-episode liveness then dropped the (good) trajectory. Fixed by keeping
  episodes in-field (bounded ticks + wide field). Honest limitation: the tracked
  Region must be ALIVE at discovery time; an object pushed off-screen loses its
  perceived identity (correctly).
- **The meta-curious chooser acts on ONE target per tick.** With multiple objects
  it pushed only the top-scoring one, so the ratio/equal arms first minted only one
  mass. The chooser is exercised in the headline + the seen-preference control; the
  multi-object arms use an explicit all-seen-push driver (`run_push_all`) — still
  the world's action machinery (`_push`/`_step`), no agent decision in Python.
- **I over-anticipated a NOISY DEGRADE in the prereg (the ~7–9% confab).** The real
  boundary is binary: the integer eye is EXACT on synthetic rendering, so recovery
  is exact-at-resonance / silent-between, not a widening estimate. The confab floor
  would only bind on REAL (sub-pixel, noisy) input — a named scope condition, not
  a measured number here.
- **The discovery REUSES the fall's exact order-2 pipeline.** The physics, eye, and
  order-N are unchanged; the NEW content is (a) the acceleration source is the
  AGENT'S chosen impulse (recorded as the action parameter), (b) different masses
  give different accelerations under the same impulse, and (c) `m = J/a` via the
  graph-native `IDiv` rule. That composition IS mass-from-action; I claim no more.

## Ledger row (this doc, not VISION_PROTOCOL.md)

| rung | claim | engine | oracle before/after | verdict |
|---|---|---|---|---|
| mass-by-action | the agent pushes SEEN objects (choose_action_meta_curious + target_fn→seen Region); a sustained push accelerates them; order-N mints ORDER-2 from the perceived Region trajectory and the graph-native `IDiv(J,\|a\|)` rule mints a per-object MassScalar = impulse/Δv, grouped by PERCEIVED Region identity, un-seeded; recovers the hidden masses EXACTLY at resonant impulses (3; 2:3; 6 via J=6/12/18; drawn {2,3,4,5,6,7}); single-push→nothing, equal-mass→equal, ratio exact; no published mass, no world-id grouping; DEGRADE: fractional a → integer eye floors → silent (confab not exercised on synthetic input) | `ac8625525b09` (shared, no Rust) | 222/0 → 222/0 | **CONFIRM** (mechanism + exact recovery at resonance; the integer-eye boundary disclosed) |
