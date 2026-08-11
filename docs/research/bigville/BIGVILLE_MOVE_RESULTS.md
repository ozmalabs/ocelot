# BIGVILLE R1 — MOVEMENT + ENERGY (block 249000) — RESULTS

Graph-native movement + energy on the proven 245/247/248 scaffold. Every movement,
energy and credibility verdict is a RULE; the world adapter only ingests the map,
seeds a goal, applies the rule-chosen position delta, ticks, and reads state. **Zero
new Rust** — both seeds compose existing DSL Terms. Prereg: `BIGVILLE_MOVE_PREREG.md`.

Engine: own build `10f65be659e0d9a9290aff39f7f5b92a` (`source_match == own`).
Base SHA `aa644fc2a37cf64aa2d8cd169bf39696c2503ee4`. All numbers deterministic (no RNG).

---

## G-move-changes-witnessing (HEADLINE) — PASS

A villager (`villager_1`, charm 1) seeded at an ISOLATED cell `(0,2)` — out of sight
of both the town square (John's public face + the newspaper) and the office —
witnesses nothing. When it NAVIGATES to `(7,5)` (a cell with line-of-sight into
John's enclosed office), it begins witnessing the scheme, and the SAME 245
credibility rule `bd_villager_backs` flips its backing. The two arms differ ONLY in
whether the agent moved.

```
                         pos      seen_hostile  seen_benevolent  heard_claim  backs
STAY  (movement OFF)   (0, 2)          0               2              0        John
MOVE  (movement ON)    (7, 5)          7               2              2        Mary
```

The flip is caused by WITNESSING, not by the newspaper: the STAY arm sits in place
for 11 ticks with `seen_hostile == 0` and stays with John; the MOVE arm's paper
signal is minimal (`heard_claim == 2`, `seen_benevolent == 2` = the seed prior) and
insufficient on its own — the credibility inequality only flips because the
witnessed-hostility term (`seen_hostile`) drags the pro-John side negative. Tick-by-
tick, the flip lands the EXACT tick the mover first gains office LOS:

```
 tick  pos      seen_hostile  backs      <- movement makes perception (and knowledge) DYNAMIC
   1  (2, 1)         0        John
   2  (5, 1)         0        John
   3  (8, 1)         0        John
   4  (9, 3)         0        John
   5  (7, 4)         1        Mary   <-- enters office line-of-sight -> witnesses -> 245 chain flips
   6  (7, 5)         2        Mary
  ...
  11  (7, 5)         7        Mary
```

Movement is proven by its effect on the ALREADY-PROVEN social layer (245 witness →
credibility), not by a position delta alone. This is the load-bearing coupling: who
witnesses what is now contingent on where each agent goes.

## G-energy-slows — PASS

Each move DEPLETES a per-agent energy budget (hunger-modulated); the per-tick move
budget is a graded step function of energy (`mv_energy_budget`: rested → 3 hops/tick,
tiring → 2, low → 1, exhausted → 0; thresholds 70/40/15). Distance covered per tick
DECREASES as the budget drains — monotone non-increasing:

```
COST-ON   tick:   1    2    3    4    5    6    7    8    9
       e_before: 100   76   52   36   20   12    4    4    4
      cells/tick:  3    3    2    2    1    1    0    0    0     (agent SLOWS then stalls)
```

A rested agent covers strictly more ground over equal ticks than an exhausted one
(first two ticks 6 cells vs last two 0). **Honest residual:** the budget re-fires on
each hop (the mover's `is_at` edge change), so it tracks energy with a ≤ one-hop
(≈8-unit) settling lag — the curve trails true energy by one step. This is
deterministic and does not affect monotonicity or the gate.

### Failing control — energy-cost ablated → NO slow-down (cost is load-bearing) — PASS

```
ABLATED (slow_on=0, cost=0)   cells/tick:  3  3  3  3  2  0  0  0  0
```

Flat at full budget every travelling tick (the terminal `2` is goal ARRIVAL, not a
slow-down), and the goal is reached in 5 ticks — whereas the cost-on arm slows and
stalls before reaching it. The graded intermediate budgets (2, 1) never appear in
the ablated arm. Energy cost is load-bearing for the slow-down.

## Failing controls — all PASS

| control | result |
|---|---|
| **no goal → idle** | 0 moves over 5 ticks; stays at `(16,10)`. Flood never seeds; `mv_pick_hop`'s reachability guard (`gdist < BIG`) is false → no fire, no wander. |
| **goal at current cell → zero moves** | `gdist == 0` at the current cell → `mv_pick_hop` guard (`gdist >= 1`) false → 0 moves. |
| **wall on the straight line → routes AROUND, no teleport** | start `(4,3)` inside the office, goal `(4,8)` outside; the only exit is the door `(8,4)`. Path length **15** vs Manhattan **5** (a real detour), **exits via the door**, every step orthogonally adjacent, no step ever enters a wall cell (no teleport). |

## Cost (spec §4) — reused incremental/foveated flood

The Bellman flood is re-run only when the active mover's goal changes (foveated
reuse). Headline run over 11 ticks on a **474-cell** map-belief: **86 rule-fire
steps total (~7.8/tick), 1 full re-flood** (the rest reused). Movement does not blow
the per-tick cost class — it stays local.

---

## Discipline ledger

| item | value |
|---|---|
| base SHA | `aa644fc2a37cf64aa2d8cd169bf39696c2503ee4` (merge-base verified) |
| prereg commit | `eae71677a7295264f1791a3a2270ba5f5600fb66` (separate, before any number) |
| own engine md5 | `10f65be659e0d9a9290aff39f7f5b92a` — `source_match == own`, not stale |
| `runners/dsl` diff | **EMPTY** (no Rust; `runners/dsl/src` + Cargo untouched) |
| canonical shared `.so` | **NOT touched** (isolated worktree built + copied its OWN `_native.abi3.so`; canonical is another checkout's) |
| new files (additive only) | `seeds/bigville_move_nav.json`, `seeds/bigville_move_energy.json`, `worlds/bigville_move_world.py`, `scripts/bigville_move_run.py`, `tests/test_bigville_move_migrated.py`, `BIGVILLE_MOVE_PREREG.md`, this file, `results/bigville_move/` — no existing tracked file edited |
| gate tests | `tests/test_bigville_move_migrated.py` — **8/8 PASS** |
| provenance + baseline | `test_engine_provenance_migrated` + `test_failure_baseline_migrated` — **18/18 PASS** (`source_match == own`) |
| rung7 vision bench | **214 passed, 10 skipped, 0 failed** (green) |
| per-area settlement | **278 passed, 5 skipped, 23 failed** — all **23 failed node-ids ∈ enumerated baseline** (verified set-wise against `results/failure_baseline.json`); the 23 are pre-existing reds (e.g. the 4 `test_topic_route_selfheal_migrated` capability-reply reds), unrelated to this rung |
| new reds | **0** (both oracle fail-sets ⊆ enumerated `results/failure_baseline.json`, 543 entries; my run's per-area fail-set is a strict subset) |
| engine-identity test | asserts the INVARIANT `source_match in {own, shared}` — no pinned-md5 equality (lesson 7b) |
| worktree | non-nested (`.claude/worktrees/agent-…`); no worktree created under `gamma-substrate/.worktrees/` |

## Honest scope / residuals

- Synthetic small-cast model (the 245/247/248 scaffold cast) on a 30×18 grid;
  mechanism-proven ≠ benchmark. 200-scale is the separate R4 scale probe, not claimed.
- The shared `gdist` field holds ONE active mover's goal at a time; multi-mover
  simultaneous fields would re-flood per switch (fine at R1 scale; a scale note for R2+).
- The energy budget trails energy by ≤ one hop (settling lag, documented above).
- Movement runs in an isolated movement substrate bridged to the drama via `self.pos`
  (the scaffold's own perception channel) — the coupling is real (dynamic perception),
  the substrates are separated only to keep the nav/energy fixpoint from cross-firing
  the drama rules.

Branch `worktree-agent-a92fba8037770d2d1`. NOT merged (supervisor merges + writes the
ledger).
