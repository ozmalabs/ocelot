# LS20 MAP-NAV WIRING — PRE-REGISTRATION (block 220000)

**Status:** pre-registered, MEASURE-FIRST. Committed ALONE before the measure
script / gate test / results. Block `220000` claimed CLEAN by
`python scripts/seed_claim.py 220000 220999` (exit 0, "no collision DETECTED").

## THE CORRECTION THIS RUNG MAKES (lead with the honesty)

RUNG 218000 solved ls20-shaped scenarios on an **OPEN 16×16 grid with NO walls**,
routing with greedy Manhattan (`_greedy_step`). `LS20_MAP_NAV_REVIEW.md` measured
the surprise: **the ls20 planner used NONE of the existing 2D-map/fog machinery**
(161000 `has_cell` occupancy belief + `space_quantize.rs` quantizer + 205000
`qf_*` Bellman flood), and the real ls20 palette has WALLS (value 4) it ignored.
So the 218000 `curious=1.0` was **trivial open-grid routing** — there was nothing
to route around.

This rung wires the REAL map machinery into the ls20 planner's **EXECUTION** and
retains fog by construction. The 218000 **DECISION** rules (`plan_seek_station`,
`plan_deliver`, `plan_blind`) are **UNTOUCHED**; only the router changes
(greedy → the shared `quanta_flood_step`). No Rust (the machinery exists);
canonical `.so` md5 `793ce09e…` unchanged.

## WHAT IS BUILT (assemble, do not invent)

1. `make_scenario(..., walls=True)` — sprinkles real ls20 wall cells (value 4) at
   density 0.20, off the avatar/goal/station cells, with a **guaranteed** 4-connected
   route avatar→every station→goal (BFS retry). A step into a wall STALLS (collision
   physics). `walls=False` (default) is byte-identical to pre-220000.
2. The whole grid is stamped as a `has_cell` occupancy belief (161000 format:
   wall=value 4, floor=value 1) — a COMPLETE belief (no fog).
3. `run_episode(..., router="quanta")` — a self-region + 4-move Control basis + the
   waypoint→`committed_goal{world:1}` reflection + `quanta_flood_step` (the identical
   `space_quantize` + `qf_*` flood the maze/Doom use). `router="greedy"` (default) is
   byte-identical to pre-220000 (plus wall collision when the scenario carries walls).

Reused unchanged: `space_quantize.rs`, all 14 `qf_*` rules, `quanta_flood_step`, the
`has_cell` belief format, `navigation_modes` + `affordance_basis` seeds.

## BASELINE (established FIRST, before pre-registering the gate)

The WALLED baseline did not exist — the greedy router had never faced a wall. Pilot
(n=12, seeds in-block):

- **WALLED (1-station):** greedy **1/12** (11 timeout — stalls on the barrier),
  quanta **12/12** (delivered — routes around). Massive separation.
- **OPEN (no walls):** greedy 12/12, quanta 12/12, **same win 12/12 AND same step
  count 12/12** — the whole-map zero-frontier flood reduces to Manhattan exactly.
- **FOG:** complete belief → **0** frontier `SpaceQuantum`; a partial belief (drop
  cells) → **>0** frontiers, with ZERO rule changes (`space_quantize` `unknown_faces`).

## PRE-REGISTERED GATES (thresholds fixed NOW, powered n=100)

Seeds: walled-1 `default_rng(220000)`, walled-3 `default_rng(220001)`, open-parity
`default_rng(220100)`. Wilson 95% CIs. Both arms run the **curious** decision rules;
the ONLY variable is the router.

- **G-walled (headline):** quanta beats greedy on walled layouts, CI-separated
  (quanta success LB > greedy success UB), on BOTH 1-station and 3-station configs.
  PASS iff `quanta_LB > greedy_UB` for each.
- **G-open-parity (degenerate no-fog):** on open layouts (n=100) quanta is
  route-EQUIVALENT to greedy — **every** episode same win AND same step count
  (`same_win==n and same_steps==n`). No regression on the easy case 218000 won.
- **G-fog-retained:** complete belief mints **0** frontier quanta; a partial belief
  (identical seed file, cells dropped) mints **>0** frontier quanta — the general fog
  capability is intact; ls20 just runs the complete-belief mode.
- **G-graph-native:** source audit — the routing decision is the `qf_*` rules +
  the untouched `plan_seek_station`; the adapter is mechanical (grid→belief,
  waypoint→goal, apply `chosen_action`). No Python path-search / `if goal_reached`
  selecting the move (`quanta_route_step` reads `chosen_action`; `_reachable` is
  generator-side world validation, not agent routing).
- **G-discipline:** integer-native; default-OFF byte-identical (`walls=False`,
  `router="greedy"` unchanged — the existing 218000 test + measure paths untouched);
  canonical `.so` md5 `793ce09e…` UNCHANGED (no Rust); `runners/dsl` diff EMPTY
  (`term.rs` included); oracle `rung7_vision_bench` BEFORE==AFTER (214 passed,
  10 skipped); 34-file `per_area_settlement_regression` BEFORE==AFTER (baseline: the
  23 pre-existing conversation/elaboration/gap/topic-route fails in
  `results/mapnav_regress_before.txt`).

## FALSIFICATION BAR

General nav — the SAME quanta machinery that serves Doom/mazes, dimension-arbitrary,
NOT an ls20 hack; routing DISCOVERED by the flood, not hardcoded. If quanta does not
beat greedy on walls, or breaks open-parity (any episode differs), or fog frontiers
do not reappear on a partial belief, report the straight null + the gap.

## SCOPE HONESTY

This is the SCENARIO wiring (offline ls20-shaped scenarios; live ls20 needs
`ARC_API_KEY`, absent — the standing 216000/217000/218000 frontier). Synthetic-proven
mechanism ≠ benchmark value; both reported. Wiring the full stack (218000 planner +
217000 transform + pixel-eye) into the LIVE `arc_run` loop + goal-binding to the win
condition (219000 gap #1) is the NAMED parallel next.
