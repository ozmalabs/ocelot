# ARC-ls20 PLANNING / EXECUTION — results (rung 218000)

**Lead honestly:** this rung **closes the ls20 loop see -> understand -> DO** via
**salience / investigation / curiosity-first**, with **goal-blindness proven to
lose**. It builds the ACTING half on 216000 (the pixel eye SEES) and 217000 (the
general `TransformDecode`/`DimInfer` UNDERSTANDS the required transform). The
planner is INVESTIGATION-driven, not search-driven (the owner steer, taken as the
architecture): the symbol<->goal mismatch is SALIENT (surprise -> ORIENT), the
agent INVESTIGATES the required transform (217000, graph-native) and seeks the
station that performs it, then ACTS. A goal-blind baseline that tunnels to the
goal LOSES; a blind-detour baseline that detours without investigating WHICH
transform also loses. Prereg: `LS20_PLANNING_PREREG.md` @
**5763f7b1740a46007221cfc2e05df4ef8d1f6a20** (committed ALONE, before the
confirmatory run).

## Result — all gates PASS (first + held-out confirmatory)

Success = the arm routes the CORRECTLY-transformed symbol to the goal (integer-
native exact set equality at the goal). N=100 scenarios per config; Wilson CIs.

| arm | 1-station (first / held-out) | 3-station (first / held-out) |
|---|---|---|
| **curious** | **1.0000 [0.9630,1.0]** / **1.0000 [0.9630,1.0]** | **1.0000 [0.9630,1.0]** / **1.0000 [0.9630,1.0]** |
| blind (control) | 0.0000 [0.0,0.0370] / 0.0000 [0.0,0.0370] | 0.0000 [0.0,0.0370] / 0.0000 [0.0,0.0370] |
| detour (control) | 1.0000 (only station matches) | 0.3200 [0.2367,0.4166] / 0.4100 [0.3187,0.5080] |

- **G-solve (headline): PASS.** Curiosity-first success **1.0000** on both configs,
  both runs (CI lower 0.9630 ≥ the pre-registered 0.95). The loop closes: it
  recognises the required transform, routes to the matching station, performs it,
  and delivers the correctly-transformed symbol.
- **G-vs-goal-blind (THE load-bearing control): PASS.** Goal-blind success
  **0.0000** — it fails EVERY scenario as `delivered_wrong` (it reaches the goal
  and delivers the UN-transformed symbol). Curious CI-lower 0.9630 > blind
  CI-upper 0.0370 on both configs, both runs — CI-separated. **Goal blindness is
  how you lose**, measured.
- **G-investigation (not mere detour): PASS.** On 3-station, blind-detour wins only
  **0.32 / 0.41** (≈ 1/n_stations, by luck of the lowest-order station matching);
  curious CI-lower 0.9630 > detour CI-upper 0.417 / 0.508 — separated. It is the
  INVESTIGATION (recognising WHICH transform is needed), not the detour itself,
  that wins.
- **G-curiosity-first: PASS.** The plan is DISCOVERED by investigation. Exemplar
  trace (held-out):
  ```
  scenario   : symbol F, required_transform rot90:2, stations [refl:c, rot90:2, rot90:3]
  salience   : mismatch symbol!=goal -> affect=surprise_orient at step 0
  investigate: recognised required transform = rot90:2 (217000 sd-loop); sought the matching station
  discovered : the matching station (key rot90:2); applied it -> carried now matches at step 6
  act        : routed to the goal and delivered -> WIN
  ```
  The required transform is NOT handed to the agent — it is recognised by the
  general sd-loop; the matching station is chosen by the `plan_seek_station` rule;
  the detour is inserted BECAUSE of the salient mismatch, not searched to the goal.

## How the loop is graph-native (G-graph-native: PASS)

Every planning DECISION is a rule in `seeds/ls20_planning.json` (6 rules, built by
the seed BUILDER `domains/ls20_planning_seed.py` with the same Term helpers as
`scripts/move_space_planner.py`):

- `plan_orient` — SALIENCE: `symbol_matches_goal==0` -> `affect=surprise_orient`
  (the 208000 surprise->ORIENT vocabulary).
- `plan_seek_station` — INVESTIGATE: route to the station whose `key` == the
  recognised `req_key` (from the 217000 sd-loop) and is unused.
- `plan_deliver` — ACT: `symbol_matches_goal==1` -> route to the goal and deliver.
- `plan_blind` (control) — always route to the goal.
- `plan_detour_seek` / `plan_detour_deliver` (control) — detour to the
  lowest-order station, then deliver.

The waypoint is written by these rules; the adapter (`worlds/arc_ls20_scenario.py`)
only (1) SEES the symbol/goal through the 216000 pixel eye and writes perception
facts (`symbol_matches_goal` by integer-native normalised set-equality; station
`used` flags; the sd-loop `req_key`), (2) reads the rule-chosen waypoint and STEPS
one cell toward it (greedy Manhattan — routing execution, the slide_flood
analogue), (3) applies a station's transform as WORLD PHYSICS when the avatar
arrives at it as the chosen destination, and scores WIN/LOSE at the goal (oracle).

**Source audit: `banned_tokens_found=[]`** — the rules name NO transform family
(rotate/reflect/recolour/rotation90/reflection) and NO ls20 constant; the decision
is generic over `req_key` / `symbol_matches_goal`. There is NO Python
`if goal_reached` / path-search selecting the agent's move. The recognition reuses
the EXISTING `shape_decode_loop` — no new recogniser. `source_match = own`.

## The falsification bar (carried from 217000)

The planner priors are GENERAL: the salience/investigation/act loop reads only
"does what I carry match what the goal wants" and "which transform relates them" —
no ls20-specific table, no per-scenario hardcoding. The per-scenario plan is
DISCOVERED (the required transform is recognised, the station matched at run time).
Dimension-arbitrary: the transform key comes from the general sd-loop, which serves
any domain (217000 proved the same op works OUTSIDE ls20 on the F-pentomino corpus).

## Discipline (G-discipline: PASS)

- **Integer-native:** the shapes are the integer lattice; the transform key is a
  categorical token; the goal verdict is exact set equality. No floats in-frame.
- **Default-OFF byte-identical:** every rule is guarded on `game.plan_on==1`; a
  graph that does not set the flag is untouched (`test_default_off_byte_identical`).
- **Canonical `.so` md5 `793ce09ed498a749abb79aeaea44b92e` — UNCHANGED.** `term.rs`
  untouched; the whole `runners/dsl` tracked diff is EMPTY. No Rust, no new Term.
- **Oracle `bash scripts/rung7_vision_bench.sh`:** BEFORE **214 passed, 10 skipped,
  0 failed** == AFTER **214 passed, 10 skipped, 0 failed**.
- **`bash scripts/per_area_settlement_regression.sh` (34-file):** BEFORE **23
  failed, 277 passed, 5 skipped** == AFTER (same); the FAILING NODE-ID SET is
  IDENTICAL (`diff` empty). The 23 reds are the pre-existing environment-conditional
  conversation/reading cluster (topic_route / gap_awareness / elaboration /
  cortices_tick / composer_driver), independent of this change (this rung touches
  none of those files).
- **New gate tests:** `tests/test_arc_ls20_planning_migrated.py` — 7/7 pass.
- Reproduction deterministic (same seed -> same wins).

## New / changed files

- NEW `domains/ls20_planning_seed.py` (seed builder — emits graph data),
  `seeds/ls20_planning.json` (the 6 planning rules),
  `worlds/arc_ls20_scenario.py` (mechanical scenario adapter + episode driver),
  `scripts/arc_ls20_planning_measure.py` (the measurement),
  `tests/test_arc_ls20_planning_migrated.py` (gates),
  `results/arc_ls20_planning_{first,heldout}.json`.
- No tracked file outside these is changed (216000/217000 `worlds/arc.py` bridge is
  reused unchanged: `_render_screen`, `recover_grid_from_render`,
  `cells_to_signature`, `SHAPE_DIM_TYPES`).

## Honest residuals + named next gap

- **Synthetic-mechanism, not live-ls20 benchmark (standing rule — report both).**
  ls20-SHAPED offline scenarios, SEEN through the pixel eye; ground truth by
  construction. LIVE ls20 (levels-completed / action-efficiency) needs
  `ARC_API_KEY` (absent — the named frontier, exactly as 216000/217000). The
  mechanism (loop closes; goal-blindness loses; investigation beats detour) is
  proven; the benchmark value is unmeasured.
- **Curious success is a clean 1.0000** because the recogniser is exact on clean
  ls20-shaped shapes (217000 measured 0.99+); the gate is nonetheless ABLE to fail
  — the CONTROLS fail it (blind 0.0000, detour 0.32/0.41), and the recogniser can
  refuse (217000's 0/110 FP control). The planner INHERITS 217000's clean render
  envelope (recognition holds to σ=16 render noise, then palette-index flips break
  the exact-equality verdict) — the recogniser is unchanged, so its envelope is.
- **Named next gaps (not attempted here):** (a) multi-step transform COMPOSITION —
  a symbol needing two stations in sequence (these scenarios use a single required
  transform); (b) routing around WALLS/obstacles (the grid is open — routing is
  the slide_flood/quanta-nav job, not exercised); (c) station DISCOVERY under FOG —
  here the map is fully observed, so the 205000 curiosity-driven exploration of an
  UNKNOWN map is the named "curiosity-first" extension (this rung realises
  curiosity-first as the transform-recognition detour, not yet as map exploration);
  (d) the 216000 multi-Region symbol grouping under motion; (e) the real
  anti-aliased 64×64 ls20 render.

**The headline, once more:** this closes the ls20 loop see -> understand -> DO via
salience / investigation / curiosity-first, with goal-blindness proven to lose
(0.0000 vs 1.0000, CI-separated) — and investigation, not mere detour, shown to be
the lever (detour 0.32/0.41).
