# ARC-ls20 PLANNING / EXECUTION — pre-registration (rung 218000)

**Lead honestly:** this rung closes the ls20 loop **see -> understand -> DO**. It
builds the ACTING half on top of 216000 (the pixel eye SEES) and 217000 (the
general `TransformDecode`/`DimInfer` UNDERSTANDS the required transform). The
planner is **INVESTIGATION-driven, not search-driven** — the owner steer, taken
as the architecture: *"It works by SALIENCE and INVESTIGATION. CURIOSITY FIRST.
GOAL BLINDNESS is how you lose."*

The salience -> investigate -> act loop is **graph rules**
(`domains/ls20_planning_seed.py` -> `seeds/ls20_planning.json`), reusing the
EXISTING machinery:
- **SALIENCE** — the symbol<->goal MISMATCH is salient (surprise -> ORIENT, the
  208000 emotion vocabulary); `symbol_matches_goal==0` is the surprise.
- **INVESTIGATE** — the required transform is RECOGNISED by the general 217000
  sd-loop (graph-native), and the agent seeks the station whose transform MATCHES
  the recognised key (`plan_seek_station`) — investigation, not just any detour.
- **ACT** — route to the rule-chosen waypoint; deliver when the carried symbol
  matches the goal form (`plan_deliver`).

The adapter (`worlds/arc_ls20_scenario.py`) is MECHANICAL: it renders + SEES the
symbol/goal (216000), writes perception facts, reads the rule-chosen waypoint,
and steps toward it (greedy routing — the slide_flood analogue). No Python
planning decision.

## What is measured (offline, ls20-shaped; measure-first)

Randomised ls20-shaped scenarios: a chiral polyomino symbol (real ls20 palette),
a required NON-identity transform (rotate90 k∈{1,2,3} / reflect_r / reflect_c /
recolour), a goal form (= transform applied), an avatar, a goal cell, and
`n_stations` transform stations (exactly ONE performs the required transform).
Ground truth by construction; the WIN verdict at the goal is **integer-native
exact set equality** (the "in-frame is integer" ARC path). Three policy ARMS
share IDENTICAL mechanical routing, differing only in which rules fire:
- **curious** — the full salience -> investigate -> act loop.
- **blind** (THE control) — tunnels straight to the goal, ignoring the mismatch.
- **detour** (second control) — detours to the lowest-order station WITHOUT
  recognising which transform is needed.

## First honest measurement (N=100, seed 218000 / 218001)

| arm | 1-station success | 3-station success |
|---|---|---|
| **curious** | **1.0000 [0.9630, 1.0000]** | **1.0000 [0.9630, 1.0000]** |
| blind | 0.0000 [0.0000, 0.0370] | 0.0000 [0.0000, 0.0370] |
| detour | 1.0000 (only station is the matching one) | 0.3200 [0.2367, 0.4166] |

blind fails 100% as `delivered_wrong` (reaches the goal, delivers the
un-transformed symbol). detour on 3-station wins only ~1/3 (by luck of the
lowest-order station matching). Reproduction deterministic; source-audit clean
(the rules name no transform family / ls20 constant).

## Pre-registered gates (thresholds set from the first measurement)

- **G-solve (headline):** curiosity-first success **≥ 0.95** on BOTH the 1-station
  and 3-station configs (measured 1.0000, CI lower 0.9630).
- **G-vs-goal-blind (THE load-bearing control):** the curious success CI is
  SEPARATED from the goal-blind success CI (curious CI-lower > blind CI-upper) on
  BOTH configs, AND blind success ≤ 0.05. *Goal blindness is how you lose.* If
  goal-blind does NOT lose, that is reported straight (it would falsify the steer).
- **G-investigation (not mere detour):** on 3-station, curious CI-lower > detour
  CI-upper — investigation (recognising WHICH transform), not just a detour, is
  the lever.
- **G-curiosity-first:** the plan is DISCOVERED by investigation — an exemplar
  trace shows salience (surprise->orient) -> investigate (recognise the transform
  via 217000) -> discover the matching station -> act (deliver).
- **G-graph-native:** the planning DECISIONS are rules (`seeds/ls20_planning.json`,
  6 rules); the adapter is mechanical (source-audit: the rules name no transform
  family / ls20 token; no Python `if goal_reached` selects the move).
- **G-discipline:** integer-native; the seed is **default-OFF byte-identical**
  (guarded on `game.plan_on==1`); canonical `.so` md5
  `793ce09ed498a749abb79aeaea44b92e` UNCHANGED; `term.rs` + the whole `runners/dsl`
  tracked diff EMPTY; oracle `rung7_vision_bench` BEFORE==AFTER; the 34-file
  regression failing-node-id set BEFORE==AFTER.

## Confirmatory run

A held-out confirmatory run on a FRESH seed (218500) at N=100 must hold every
gate. Reported in `LS20_PLANNING_RESULTS.md` alongside the first run.

## Honest scope (standing rule — synthetic-proven != benchmark value, report both)

These are ls20-SHAPED offline scenarios on the real ls20 palette, SEEN through the
216000 pixel eye; the recogniser is the GENERAL 217000 sd-loop; ground truth is by
construction. **LIVE ls20 (levels-completed / action-efficiency) needs
`ARC_API_KEY` (absent — the named frontier, exactly as 216000/217000).** The
mechanism (the loop closes; goal-blindness loses; investigation beats detour) is
proven offline; the benchmark value is unmeasured. Named next gaps: multi-step
transform COMPOSITION (a symbol needing two stations in sequence); routing around
WALLS/obstacles (these scenarios are open-grid); station DISCOVERY under fog (here
the map is fully observed — the curiosity-driven exploration of an unknown map,
205000, is the named extension); and the real anti-aliased 64×64 ls20 render.
