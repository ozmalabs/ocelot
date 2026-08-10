# PHYSICS — INERTIAL MASS BY ACTION (pre-registration)

Registered BEFORE any measurement. The agent PUSHES objects it sees and
discovers their HIDDEN inertial mass FROM THE PUSH — the operational definition
of inertial mass, `F = ma` inverted (`m = impulse / Δv`). Resistance to the push
IS the mass. No `mass` attribute is ever published; grouping is by the eye's
PERCEIVED `Region` identity, never a world id.

## The genuine bar (no scaffolding)

- The world outputs ONLY pixels (a 0/1 cell field the eye carves) and AFFORDANCES
  (push actions). Each object carries a HIDDEN inertial mass in the world's PRIVATE
  Python state, drawn from an UNTUNED distribution (NOT 1/4/9). The mass is NEVER
  written to the graph.
- Mass is DISCOVERED BY ACTION: the agent pushes an object with a chosen impulse
  `J`; the world responds `Δv = J / hidden_mass` and integrates; the eye observes
  the resulting motion. Over repeated pushes of the SAME object, `J / Δv` is
  constant `= m`. The generic order-N / invariance machinery mints a hidden
  per-object scalar from that constancy, un-seeded.
- The grouping "same object" is the eye's persistent `Region` identity (the tracked
  carve), NOT a world-supplied object label.

## Design (thin adapter + existing machinery + one graph-native rule)

- **Push world** — `domains/push_world.py` (thin adapter, mechanical I/O only).
  N blobs, each a small square, each with a HIDDEN integer mass (Python-local,
  private, never graphed). Every tick the adapter renders the blobs' CURRENT
  positions to a pixel field and hands them to the eye (`native.segment` →
  `segment_and_track`). `legal_actions` offers, per currently-SEEN `Region`,
  `("push", region_id, impulse)` over a small integer impulse menu.
  `apply_action` maps `region_id` to the private object under it (nearest
  perceived centroid — the world's own book-keeping, never published), applies
  `v += impulse / mass`, integrates `pos += v` (semi-implicit Euler, no gravity,
  no friction), and re-renders. Pixels + affordances out; mass in private state.

- **Act on a seen object** — the agent selects the push via the existing
  `choose_action_meta_curious(legal_actions, preview_fn, touches_fn, target_fn)`;
  `target_fn(("push", rid, J))` returns the SEEN `Region` node, so pushing a thing
  the agent has SEEN lifts `asym_count` (the see→link→ACT path). The CHOICE is the
  existing machinery; the adapter only measures and stamps.

- **Discover mass by action** — pushing the SAME seen Region every tick with a
  fixed impulse `J` makes the object accelerate at `a = J / m` (constant). The eye
  tracks it as ONE `Region` (the velocity-predictive association fix carries an
  accelerating object) and the DIMENSION-GENERIC order-N loop (`TimeInfer` /
  `diff_pyramid`, the SAME machinery that mints the fall's order-2) mints ORDER-2
  from the PERCEIVED `cy` trajectory: the minted `coeffs[1]` leading vector IS the
  perceived per-tick `Δv` (= the acceleration `a`). This constancy of `Δv` across
  the repeated pushes IS the invariance. A graph-native seed rule
  (`seeds/mass_by_action.json`) reads the impulse `J` (the action parameter,
  recorded on the push observation — mechanical) and the minted acceleration `a`
  (`IndexAt(IndexAt(coeffs,1),0)`) and mints
  `MassScalar = IDiv(J, a)` linked to the Region — the operational inertial mass
  `m = impulse / Δv`. Read FROM THE GRAPH. No `mass` attr is ever read; no Python
  computes `J/Δv`.

- **Grouping is PERCEIVED** — order-N runs over ONE Region's `cy` sequence; the
  Region's persistent id groups the trajectory. Distinct objects = distinct Region
  ids = distinct order-2 mints = distinct MassScalars. The world's private
  object→region map is used ONLY to apply force, never to group and never graphed.

## Discriminator (registered before any number)

- **CONFIRM:** the agent pushes seen objects; the order-N/invariance machinery
  mints an order-2 acceleration from the PERCEIVED Region trajectory, and the
  graph-native rule mints a per-object `MassScalar = J/a`, grouped by PERCEIVED
  Region identity, un-seeded — and the minted scalars recover the hidden relative
  masses within the eye's noise. No published mass anywhere; grouping uses no
  world id.
- **DEGRADE:** it recovers relative mass but noisily / only at "resonant" impulses
  (the eye's integer quantization means a fractional `a = J/m` jitters the
  perceived 2nd difference and the EXACT order-N witness floors — recovery is
  exact at `J ∈ {m,2m,3m,…}` and silent between). Report which (mass, impulse)
  pairs mint, the push-count / trajectory length needed, and tie the boundary to
  the eye's integer-lattice confab (and, if exercised, a sub-pixel-jitter arm that
  widens the estimate toward the ~7–9% confab floor).
- **FALSIFY (report honestly, name the next thing):** the eye's Δv observation is
  too noisy to mint order-2 at all; OR grouping cannot be done by perceived
  identity without a seed (name exactly where the grouping axis would have to come
  from); OR the affordance contract cannot be unified with a force integrator
  without breaking something. NOT rescued by publishing mass, grouping on a world
  id, or tuning masses/impulses to be conveniently separable.

## Controls

- **single push** (one impulse, then coast) → order-1 (constant velocity) → NO
  order-2 acceleration → NO MassScalar minted (insufficient evidence).
- **equal hidden mass** → equal minted scalar.
- **mass ratio** — two objects, same impulse `J` → minted scalars in the ratio of
  the hidden masses (report the error vs the eye's confab floor).
- **no published kinematics** — the world graph carries only pixels + the eye's
  Region carve; no `mass`/position/velocity/object-id attr appears; grouping reads
  only the Region id.

## Untuned masses + impulse menu (registered)

- Hidden masses drawn from an UNTUNED set of small integers, NOT 1/4/9 (headline /
  ratio arms use adjacent `{2, 3}` — the HARDEST to separate, the opposite of a
  separability tune — plus a distribution arm drawing from a wider untuned set).
- Impulse menu: a small set of small integers. Exact recovery requires the
  perceived acceleration `a = J/m` to be an integer AND `≤ span+2` (the eye's
  tracking radius), i.e. `J` a multiple of `m` with `J/m ≤ 5`. This is a disclosed
  property of the integer eye (the frame/continuum invariant: in-frame coordinates
  are integer), NOT a mass/impulse separability tune.

## Provenance / discipline (registered)

- Branch `worktree-agent-a0a7c09290807ed6c` (own worktree, NOT main).
- **Expected NO Rust, NO new Term.** Pure composition: the push adapter
  (`domains/push_world.py`) + one graph-native seed rule
  (`seeds/mass_by_action.json`, using existing `IDiv`/`IndexAt`/`Attr` Terms) + the
  existing eye (`segment_and_track`), order-N (`TimeInfer`/`shape_decode.rs`), and
  action-choice (`choose_action_meta_curious`) machinery, all unchanged.
- Engine sha256 (short) `ac8625525b09`, `source_match = shared` (Rust source in
  this worktree byte-identical to canonical; no Rust edited) — asserted in
  {own, shared}.
- Seed: `SEED CLAIM 140000-140999: CLEAN -- no collision DETECTED.`
- Oracle `scripts/rung7_vision_bench.sh` (with `data/` symlinked): record
  BEFORE and AFTER (must be 222/0 → 222/0).
- Gate: `tests/test_mass_by_action_migrated.py` — every product read from
  `native.evaluate()` (TUPLES) and the `run_rules` graph state; NEVER a
  process-pattern wait. Also run `pytest -k migrated` on instrument seams
  (3 pre-existing reds, not mine; add none).
- Ledger row lives in `PHYSICS_MASS_BY_ACTION_RESULTS.md`, NOT `VISION_PROTOCOL.md`.
