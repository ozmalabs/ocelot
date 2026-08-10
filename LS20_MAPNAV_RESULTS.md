# LS20 MAP-NAV WIRING — RESULTS (block 220000)

**Prereg:** `LS20_MAPNAV_PREREG.md`, committed ALONE at
`f3f179c91e95ef36756b89723815dc5ca4b04724`. Block `220000` claimed CLEAN
(`scripts/seed_claim.py 220000 220999`, exit 0). MEASURE-FIRST: the walled baseline
was established before the gate thresholds were fixed.

## HEADLINE (lead with the honesty)

RUNG 218000's `curious=1.0` was **trivial open-grid routing** — the ls20 planner
built no map, laid an OPEN 16×16 grid with NO walls, and routed greedy Manhattan,
using NONE of the existing 2D-map/fog machinery. This rung **corrects that**: it
stamps a real `has_cell` occupancy belief with walls (value 4) and swaps the
executor to the shared `quanta_flood_step` (`space_quantize` + the 14 `qf_*`
Bellman/portal flood rules) — the **identical** nav machinery the maze/Doom use.
The 218000 **DECISION** rules (`plan_seek_station`, `plan_deliver`, `plan_blind`)
are **UNTOUCHED**; only the router changes. **Fog is retained by construction.**

**All five pre-registered gates PASS at n=100.** No Rust; canonical `.so` md5
`793ce09e…` unchanged.

## GATES (all pre-registered, n=100 powered, Wilson 95% CIs)

| Gate | Result | Numbers |
|---|---|---|
| **G-walled 1-station** (headline) | **PASS** | greedy **0.03** [0.010, 0.085] (3/100, timeout 97) vs quanta **1.00** [0.963, 1.0] (100/100). CI-separated (0.963 > 0.085). |
| **G-walled 3-station** | **PASS** | greedy **0.07** [0.034, 0.137] (7/100, timeout 93) vs quanta **1.00** [0.963, 1.0] (100/100). CI-separated. |
| **G-open-parity** (degenerate no-fog) | **PASS** | greedy 100/100, quanta 100/100, **same_win 100/100 AND same_steps 100/100** → route_equivalent. The whole-map zero-frontier flood reduces to Manhattan exactly. |
| **G-fog-retained** | **PASS** | complete belief → **0** frontier quanta; partial belief (unknown=absence) → **2** frontier quanta. SAME `space_quantize` path, ZERO rule changes. |
| **G-graph-native** | **PASS** | source audit clean: the router reads the qf_* rules' `chosen_action`; no Python path-search (`dijkstra`/`a_star`/`heapq`/`networkx`/…) selects the move. |

Result JSON: `results/arc_ls20_mapnav_first.json`. Gate test:
`tests/test_arc_ls20_mapnav_migrated.py` — **5 passed** (36s).

### The walled-vs-open picture

- **WALLED:** greedy **stalls on structure** (97/100 and 93/100 time out — a
  straight Manhattan run hits a wall and refuses), quanta **routes around every
  time** (100/100 delivered). The barrier is exactly the lever the review predicted.
- **OPEN:** the two routers are **byte-for-byte route-equivalent** (same win, same
  step count, all 100) — no regression on the case 218000 already won. On a complete
  belief `space_quantize` mints zero frontiers, so the Bellman flood degenerates to
  the Manhattan gradient.

### Fog retained by construction

ls20 achieves "no fog" by stamping a **complete** belief, NOT by disabling frontier
minting. Drop cells (unknown = absence) and the SAME `unknown_faces` code mints
`frontier` `SpaceQuantum` again (0 → 2 here) with zero rule changes — a future
ls20-under-fog rung need only stamp fewer cells. The Doom/maze partial-belief
exploration path is untouched.

## GRAPH-NATIVE / FALSIFICATION BAR

The routing decision is the `qf_*` rules + the untouched `plan_seek_station`. The
new Python is pure world-adapter: `setup_quanta` (grid→`has_cell` belief + self-region
+ 4-move Control basis — identical to `scripts/maze_run.setup_quanta`),
`_reflect_goal` (waypoint→`committed_goal{world:1}`), `quanta_route_step` (reads
`chosen_action`, applies with collision). `_reachable` is generator-side world
VALIDATION (BFS over the wall layout to guarantee solvability), never the agent's
routing. This is the SAME dimension-arbitrary machinery serving Doom/mazes — not an
ls20 hack; routing is DISCOVERED by the flood, not hardcoded.

## G-DISCIPLINE (before/after)

- **Default-OFF byte-identical:** `walls=False` + `router="greedy"` (both defaults)
  never touch the belief/quanta machinery. Existing 218000 test
  `test_arc_ls20_planning_migrated.py` — **7 passed** (unchanged); open-parity's
  same-steps 100/100 confirms identical greedy behaviour.
- **Canonical `.so`:** md5 `793ce09ed498a749abb79aeaea44b92e` UNCHANGED (no Rust).
- **`runners/dsl` diff EMPTY** (`term.rs` included) — verified `git diff --stat`.
- **Oracle `rung7_vision_bench`:** BEFORE **214 passed, 10 skipped** == AFTER
  **214 passed, 10 skipped**.
- **34-file `per_area_settlement_regression`:** the failing NODE-ID SET is
  **IDENTICAL** before and after (23 pre-existing conversation/elaboration/gap/
  topic-route fails, unrelated to nav — enumerated in
  `results/mapnav_regress_before.txt`; `diff` empty). Per the standing rule the
  baseline is the LIST of node ids, not a count.
- **Integer-native:** poses are the integer lattice; the belief value is a
  categorical wall/floor token; the continuous `qdist` is the cross-frame Bellman
  metric (correct — it is a MAP over the portal graph, not an in-frame coordinate).

## SCOPE HONESTY (synthetic-proven ≠ benchmark value — both reported)

This is the SCENARIO wiring, on offline ls20-shaped scenarios (the real ls20 palette,
SEEN through the 216000 pixel eye; the transform recogniser is the general 217000
sd-loop). It proves the MECHANISM — routing over real wall structure with the shared
map machinery, fog retained. It is NOT live-ls20 benchmark value: LIVE ls20 needs
`ARC_API_KEY` (absent — the standing 216000/217000/218000 frontier).

**NAMED parallel next:** wiring the full stack (218000 planner + 217000 transform +
pixel-eye) into the LIVE `arc_run` loop + goal-binding to the win condition (219000's
gap #1). This rung leaves that untouched.

## FILES

- `worlds/arc_ls20_scenario.py` — walls generator (`walls=` kwarg, `_reachable` BFS),
  wall collision in `_greedy_step`, the quanta router on `Planner`
  (`setup_quanta`/`_reflect_goal`/`quanta_route_step`), `run_episode(router=)`.
- `scripts/arc_ls20_mapnav_measure.py` — the powered gate driver.
- `tests/test_arc_ls20_mapnav_migrated.py` — the 5 gate tests.
- `results/arc_ls20_mapnav_first.json`, `results/mapnav_regress_before.txt`.
- Reused unchanged: `runners/dsl/src/space_quantize.rs`, `seeds/quanta_navigation.json`
  (14 `qf_*`), `seeds/{navigation_modes,affordance_basis}.json`,
  `domains/spatial_sense.py::quanta_flood_step`, the `has_cell` belief format.
