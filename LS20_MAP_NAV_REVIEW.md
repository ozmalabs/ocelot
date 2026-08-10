# LS20 MAP NAVIGATION — REVIEW + WIRING PLAN

**Status:** review + plan only. No rung, no seed, no gate, no prereg. Nothing
built. `VISION_PROTOCOL.md` untouched. Canonical `.so` (`793ce09e…`) unchanged;
no Rust touched.

**Worktree note (surprise #0):** the worktree was created at `8807ce351b`
(ledger 161000), an ancestor of the intended base `5ae84ba0d1` (ledger 218000 —
the ls20 planner, the subject of this review). At 161000 the ls20 planner files
do not exist yet. Reset the worktree branch to `5ae84ba0d1` per the task's
explicit intent before reviewing; `.so` re-verified `793ce09e…` after.

---

## HEADLINE (read this first)

1. **The 2D-map + fog machinery EXISTS and is battle-tested — on mazes and Doom,
   WITH walls.** It is three composable layers: an occupancy *belief* builder
   (161000), a *quantizer* that turns belief into routable boxes+portals+frontiers
   (`space_quantize.rs`), and a *nav engine* that Bellman-floods and hops over
   those portals (205000 `quanta_navigation`). A one-call adapter helper
   (`spatial_sense.quanta_flood_step`) drives the whole pass.

2. **Fog is native and measured, not a TODO.** Fog = a *partial* belief.
   `unknown = absence` (poses not present in `has_cell`) is first-class in the
   Rust: `body_admissible` requires *known* passable cells; `unknown_faces` mints
   thin `frontier` `SpaceQuantum` boxes wherever passable borders unknown; the
   `qf_seed_frontier`/`qf_frontier_goal` rules multi-source-flood and commit
   frontiers to drive exploration. **No-fog = complete belief = zero frontiers**,
   and that is the *same code path*, confirmed by a Rust unit test
   (`space_quantize.rs:893`, `frontiers == 0` for a fully-enclosed belief).

3. **THE SURPRISE: the ls20 planner does not use ANY of it. The real ls20 map is
   never parsed.** `worlds/arc_ls20_scenario.py` builds no belief at all (only
   `Game`/`Station`/`Ping` nodes), generates an **open** 16×16 grid with **no
   walls**, and routes with `_greedy_step` — straight-line Manhattan toward the
   rule-chosen waypoint. `worlds/arc.py` *knows* the real ls20 palette has walls
   (value `4` = "dark-grey field/walls") but the scenario ignores wall structure
   entirely. So this is not "review + wire an under-used router"; it is **the
   router exists and works; the ls20 world is a wall-free fiction that never feeds
   it a map.**

4. **First wiring rung:** give `make_scenario` real walls + wall-collision
   physics (so straight-line greedy *stalls*), stamp the whole grid as a
   `has_cell` belief (no-fog), and replace `_greedy_step` with
   `quanta_flood_step` to the rule-chosen waypoint. Gate: quanta arm beats the
   greedy arm on walled layouts (CI-separated) **and** is route-equivalent on
   open layouts (the degenerate no-fog parity check). Honest baseline: on the
   *current* open grid the greedy router "wins" only because there is nothing to
   route around — it walks through where walls would be.

---

## PART A — THE MAP / FOG MACHINERY INVENTORY (measured)

### A.1 — 161000 occupancy belief builder — `seeds/doom_ingraph_map.json`

- **id** `doom_ingraph_map` v1.0.0, `depends_on: []`. Driver
  `scripts/doom_ingraph_map_run.py`; ingest helpers `domains/doom_map_ingest.py`.
- **What it does:** grows a *persistent, graph-native occupancy belief* from the
  agent's own senses. `has_cell` edges link `Cell{row,col,value}` belief points
  to the game node. `dm_free_new`/`dm_wall_new` mint free/wall belief from
  pose-self-motion (walk-free) and depth range-vision (depth_free/depth_wall);
  `dm_walk_frees_wall` is the merge policy (walk-free is authoritative) *as a
  rule*, never Python. `dm_kind_room`/`_corridor`/`_area`/`_frontier`/`_lava` type
  each decoded box by its geometry relative to the body width (config-space).
- **unknown = absence, first-class** (the CLAUDE.md invariant). A pose the agent
  has not sensed is simply *not* in `has_cell`.
- **Role for us:** this is the **belief layer** — the `has_cell` format that the
  quantizer reads. It composes the *existing* `space_quantize` primitive
  (`has_cell` → `SpaceQuantum` passable/frontier). This is the representation the
  ls20 wiring should reuse.

### A.2 — `space_quantize` — the quantizer — `runners/dsl/src/space_quantize.rs` (Rust)

- **What it does (module docs, lines 1–64):** reads the `has_cell` belief within
  a `focus` box (foveation), erodes it by a body shape (`BodySpec::Extents` /
  `Offsets`, config-space admissibility), decomposes the admissible region into
  maximal axis-aligned N-dim boxes (`SpaceQuantum{lo,hi,ndim,kind,body_key,
  epoch,…}`), mints `portal` edges (`dim`,`dir`,`span_lo/hi`,`cost`,`oneway_ok`)
  between face-adjacent quanta, and **mints thin `frontier` quanta where a
  passable quantum borders UNKNOWN poses.** Incremental (reuse valid quanta,
  split stale ones only along the failing dim) and foveated (scoped to `focus`).
- **This is where fog lives.** `read_belief` (l.268) maps only known poses;
  `body_admissible` (l.356) is true "iff every offset cell `p+o` is a KNOWN,
  passable belief point"; `unknown_faces` (l.531) computes "maximal boxes of
  UNKNOWN poses (absent from `belief`)" and skips a face "if every adjacent pose
  is already known (no frontier needed there)".
- **Degenerate no-fog case is handled HERE, and measured:** unit test
  `l.893` — a fully wall-enclosed belief → `summary.frontiers == 0`. Complete
  belief ⇒ no unknown faces ⇒ no frontier quanta ⇒ pure passable-boxes+portals.
  N-dim + body-conditional throughout (`two_bodies_over_one_belief` test l.972).
- **Dimension-arbitrary, general.** Nothing Doom- or ls20-specific. `slide_flood`
  (the in-binding BFS) is explicitly the anti-pattern this module replaces.

### A.3 — 205000 quanta navigation engine — `seeds/quanta_navigation.json`

- **id** `quanta_navigation` v1.0.0, `depends_on: [navigation_modes,
  affordance_basis]`. ~6600 lines of generated Term-JSON; the rule roster
  (from the rule comments, verified):
  - `qf_seed_goal` — a `world==1` committed goal's containing quantum → `qdist=0`
    (single-source flood root).
  - `qf_seed_frontier` — no world goal (pure exploration) → *every* `frontier`
    quantum is a flood source (multi-source `qdist=0`). **This is the fog/explore
    driver.**
  - `qf_relax` — Bellman relax `qdist ← min(qdist, R.qdist+cost)` over `portal`
    edges gated by `oneway_ok`, epoch-fresh; batched to fixpoint.
  - `qf_visit` — mark the avatar's containing quantum visited.
  - `qf_hop_direct` — goal inside the avatar's own box → per-dim sign step to it.
  - `qf_hop_route` — else pick the portal minimising `neighbour.qdist + cost`
    from the `oneway_ok`+fresh-filtered pool, then step; **writes
    `game.chosen_action`** by an `Argmax` over the self-region's `responds_via`
    `ControlResponse` nodes via a `Dot` on `(dr,dc,dz)` — i.e. it maps the desired
    displacement onto the world's *learned* action vocabulary, N-dim, no
    hardcoded Up/Down/Left/Right.
  - `qf_frontier_goal` — commit the nearest frontier as a bookkeeping
    `Goal{pose,exploration}` (Argmin, one mint/cycle).
  - `qf_goal_retire`, `qf_stale_on_belief_change`/`_block_interior`/`_block_portal`,
    `qf_requantize_flag`, `qf_closed`/`qf_mint_hyp` — lifecycle, staleness→resplit,
    epoch-gated re-quantize cue, movement-exhausted → non-movement hypothesis.
- **All `qf_*` guard on `game.nav_repr == "quanta"`.** Cell-mode
  `hop_descend_gradient` (`seeds/grid_navigation.json`) is untouched and starves
  in quanta mode. So the mode is pure DATA on the game node.
- **The single decision written each tick is `game.chosen_action`.** Everything
  else is `qdist`/`visited`/portal bookkeeping.

### A.4 — 203000 allocentric held-surface map — `seeds/doom_allocentric_surface.json`

- **id** `doom_allocentric_surface` v1.0.0. Rules `as_new`/`as_blend`/`as_gate`/
  `as_freshness`/`as_tier`/`as_demote`. A first-class
  `AlloCell{pose,value,density,residual,half_life,freshness,tier,…}` map in
  *world* coordinates: pose-registered SEEN observations, EMA/Kalman blend
  (dwelt cells denoise/super-resolve), inverse-surprise half-life decay,
  demote-not-delete. `as_new` mints for a newly-seen pose (`unknown = absence`).
- **Role for us:** this is the **fog-over-time / moving-eye** upgrade of the
  belief layer — richer than ls20 needs (ls20 is handed a static grid each frame;
  it does not need density/decay/tiers to reconstruct a surface). **Retain as the
  future path** when ls20 fog is genuinely partial-across-time; do **not** wire it
  for the first rung (overkill, and its decay would fight a stable given grid).

### A.5 — the adapter helper + consumers

- **`domains/spatial_sense.py :: quanta_flood_step(agent, game, pose_rc, body_hw,
  passable_values, slide, grid_hw, pending_block, focus)`** — the one-call driver:
  stamps `avatar_pose`/`scale`/`focus`, fires `space_quantize` when the graph asks
  (`needs_quantize`) or belief epoch moved, then a two-phase `run_rules` (flood to
  fixpoint; arm `closed=0`; re-run so `qf_closed` reads a *converged* `qdist`).
  Pure mechanical I/O + fixpoint scheduling — every decision is a `qf_*` rule.
  **This is the exact reuse handle for ls20.**
- **Consumers that opt in via `nav_repr="quanta"`:** `scripts/maze_run.py`
  (mazes — **with walls**, `_wall_values`, `quanta_flood_step`),
  `scripts/arc_run.py`, `scripts/doom_active_explore_run.py`,
  `domains/spatial_sense.py`. Deps `affordance_basis` (learns each control's
  `ControlResponse.(dr,dc)` displacement from observation — the action basis) and
  `navigation_modes` (frontier_seek / mover_avoid / pocket_escape concepts).

### A.6 — where fog IS and IS NOT supported (summary table)

| Layer | Fog support | Evidence |
|---|---|---|
| 161000 belief (`has_cell`) | **Yes** — grows partial belief from senses; unknown=absence | `dm_*` rules; seed desc |
| `space_quantize.rs` | **Yes** — mints `frontier` at passable↔unknown border; no-fog ⇒ 0 frontiers | `unknown_faces` l.531; test l.893 |
| 205000 `quanta_navigation` | **Yes** — `qf_seed_frontier`/`qf_frontier_goal` explore frontiers | rule roster |
| 203000 allocentric | **Yes (temporal/decaying)** — richer, moving-eye | `as_new` unknown=absence |
| **ls20 planner (218000)** | **NONE — no map at all** | `arc_ls20_scenario.py`: open grid, `_greedy_step`, no `has_cell`, no walls |

**The machinery supports fog; the ls20 planner supports nothing — it never builds
a map.** ls20's "no fog" is not "the fog case turned off"; it is "no map exists."

---

## PART B — THE WIRING PLAN

### B.1 — the gap, precisely

`worlds/arc_ls20_scenario.py`:
- `Planner.__init__` builds `Game` + `Ping` + `Station` nodes only. **No belief,
  no `has_cell`, no `SpaceQuantum`, no walls.**
- `make_scenario` lays out an **open** 16×16 grid; it *rejects* layouts where the
  straight greedy path crosses a station, i.e. it engineers the world so that
  straight-line motion is always fine. There is no structure to route around.
- `plan_seek_station` (rule) writes `wp_r`/`wp_c` = the matching station's cell;
  `plan_deliver` writes `wp_* = goal`. The **decision** (which waypoint) is
  graph-native and correct — that is the 218000 achievement and stays.
- `run_episode` executes with `pos = _greedy_step(pos, dec["wp"])` — the
  "slide_flood-analogue on an open grid" the task names. It ignores obstacles.

So the wiring changes **execution only**: keep the rules that pick the waypoint;
replace Manhattan stepping with quanta routing over a real belief.

### B.2 — which representation

Use **161000 occupancy belief (`has_cell` `Cell{row,col,value}`) + 205000
`quanta_navigation`**. Not 203000 allocentric (its decay/density/tier is a
moving-eye surface reconstruction — wrong tool for a static given grid; keep it as
the temporal-fog upgrade). The ls20 render grid → belief is mechanical:

- The scenario already SEES the grid (`recover_grid_from_render`, the 216000 eye).
- For each seen non-avatar cell, stamp `has_cell → Cell{row,col,value}`.
- `passable_values` = every value except walls (`4`); walls are simply *absent
  from passable*, so `body_admissible` excludes them and portals never cross them.
- **No-fog:** stamp the WHOLE grid → complete belief → `space_quantize` emits zero
  frontier quanta → pure Bellman-to-goal. **Fog (future):** stamp only viewed
  cells → frontiers appear → exploration rules fire. Same code, different belief
  completeness — fog is retained by construction, not by a flag.

### B.3 — how the planner consumes it

Per episode step, after the rules write the waypoint:
1. Mint/refresh a `committed_goal{pose:[wp_r,wp_c], world:1}` on the game from the
   rule-written `wp_r`/`wp_c` (mechanical I/O — the coords are already graph
   attrs; the adapter just reflects them onto the goal node the router reads).
2. Call `quanta_flood_step(agent, game, pos, body_hw=(1,1), passable_values,
   slide=1, grid_hw=(H,W))`.
3. Read `game.chosen_action` (a `ControlResponse` move) and apply it as the step.

The `qf_*` Bellman/portal flood routes **around walls** to the waypoint. Station
"use" physics and goal scoring are unchanged. The 218000 architecture is
preserved: rules pick the waypoint; the executor now routes with quanta instead of
Manhattan.

### B.4 — clean reuse vs new work

**Clean reuse (no change):**
- `space_quantize.rs` (Rust — untouched; canonical `.so`).
- all `qf_*` rules in `quanta_navigation.json`.
- `spatial_sense.quanta_flood_step`.
- the `has_cell` belief format (from `worlds/arc.py`'s existing `["cell",r,c,v]`
  emitter — nothing ls20-specific).

**New (small, all mechanical world-adapter — no decisions):**
- A belief-stamping pass in `arc_ls20_scenario.py`: render grid → `has_cell`.
- A self-region + 4 grid-move `Control` nodes so `affordance_basis` learns the
  `ControlResponse.(dr,dc)` basis `qf_hop_*` needs (maze/arc boot this already;
  ls20 must declare its move set — mechanical). Grid-move collision physics
  (a step into a wall is refused) in the world.
- Reflecting `wp_r`/`wp_c` → `committed_goal{world:1}` (mechanical; or ONE tiny
  bridge rule `plan_waypoint_to_goal` if we want it fully graph-side — preferred,
  since it keeps even the reflection a rule).

**Falsification bar (keep it general):** the wired path must be *the same*
`quanta_flood_step` + `qf_*` that maze/Doom use, driven by pose-lists and a
Control-declared basis — **not** an ls20-special router. If the wiring introduces
any ls20-only routing branch, it has failed the "same nav serves Doom" test.

### B.5 — the smallest first wiring rung (pre-registerable)

**Build:**
1. `make_scenario`: insert a wall barrier (value `4` cells) between avatar and
   the matching station / goal so a straight path is blocked; add wall-collision
   to the step (move into a wall is refused → avatar stalls).
2. Stamp the whole grid as `has_cell` belief (no-fog); declare the 4-move Control
   basis + self-region.
3. Add a `quanta` execution arm: waypoint → `committed_goal{world:1}` →
   `quanta_flood_step` → apply `chosen_action`. Keep the current `_greedy_step`
   arm as the control.

**Gate (two clauses):**
- (a) **Walled layouts:** quanta-arm win-rate > greedy-arm win-rate,
  CI-separated (n powered — per the standing "power the gate before the endgame"
  rule; deltas within ~3× the per-episode step are not results).
- (b) **Open layouts (degenerate no-fog parity):** quanta-arm route ≡ greedy-arm
  route (both reach the waypoint in the same step count) — confirming the
  whole-map zero-frontier flood reduces to Manhattan on an open grid, i.e. we did
  not regress the 218000 open-grid behaviour.

**Honest baseline:** on the *current* open grid, 218000 measured curious=1.0 vs
blind=0.0 (7/7). There is **no existing baseline for walled ls20** — the greedy
router has never faced a wall. Worse, the current world has no wall-collision, so
today's greedy arm would "win" by passing straight through where walls belong;
the first rung must add collision precisely so there is something to route
around. Expected: greedy stalls/times-out on walled layouts (≈0 where the barrier
fully separates), quanta routes around (≈ the 218000 win-rate). That gap is the
lever this rung measures; it is a *guess* until measured, flagged as such.

**Cost/kind honesty:** this is one adapter + one arm + walls in the generator; it
proves *mechanism* (routing over real structure), not benchmark value — live ls20
still needs `ARC_API_KEY` (absent, the standing 216000/217000/218000 frontier).
Synthetic-proven ≠ benchmark value; report both.

---

## PART C — NO-FOG DEGENERATE CASE + FOG RETENTION (explicit)

- **ls20's no-fog whole-map mode IS the degenerate case of the fog machinery,
  and the reduction is in the quantizer, measured.** A complete belief (every
  in-focus pose known) makes `unknown_faces` return nothing → `space_quantize`
  mints **zero** `frontier` quanta (`space_quantize.rs:893` asserts exactly this)
  → `qf_seed_frontier` has no sources → only the `world==1` committed goal seeds
  the flood (`qf_seed_goal`) → `qf_relax`/`qf_hop_route` route to it over the
  passable-box portal graph. ls20 gets "route the fully-known map to the goal"
  from the identical rules that, under partial belief, would also explore. It is
  the *same* path with one input (belief completeness) at its extreme.

- **Fog is retained by construction, not by a preserved flag.** ls20 achieves
  "no fog" by stamping a *complete* belief, NOT by disabling frontier minting.
  The plan explicitly forbids an ls20 "assume fully observed" shortcut that
  bypasses `unknown_faces` — that would strip fog. Because the belief is stamped
  cell-by-cell, a future ls20-under-fog rung need only stamp *fewer* cells (what
  the eye has seen), and frontiers + `qf_seed_frontier`/`qf_frontier_goal`
  exploration reappear with zero rule changes. Other domains (Doom, maze) that
  feed partial belief keep full fog behaviour untouched — the ls20 wiring adds a
  consumer, it does not modify the shared quantizer or `qf_*` rules.

- **One-line invariant:** *fog = partial belief; no-fog = complete belief; the
  code is one path parameterised by how much of the belief is stamped.* Wiring
  ls20 is "stamp it all and commit a `world==1` goal"; wiring fog is "stamp what
  you saw and let frontiers drive." Both are already supported.

---

## Files reviewed (all absolute)

- `worlds/arc_ls20_scenario.py` — the 218000 planner scenario (open grid,
  `_greedy_step`, no belief/walls).
- `domains/ls20_planning_seed.py` — the salience→investigate→act rules
  (`plan_seek_station` writes the waypoint; decision is graph-native).
- `seeds/quanta_navigation.json` — the `qf_*` nav engine.
- `runners/dsl/src/space_quantize.rs` — the quantizer + fog (frontier) minting.
- `seeds/doom_ingraph_map.json` — 161000 `has_cell` occupancy belief builder.
- `seeds/doom_allocentric_surface.json` — 203000 `AlloCell` held-surface map.
- `domains/spatial_sense.py :: quanta_flood_step` — the one-call adapter driver.
- `scripts/maze_run.py`, `scripts/arc_run.py` — quanta consumers over walls.
- `seeds/affordance_basis.json`, `seeds/navigation_modes.json` — nav deps
  (control basis + mode concepts).
- `worlds/arc.py` — real ls20 palette (value `4` = walls), `has_cell` "cell" emitter.
