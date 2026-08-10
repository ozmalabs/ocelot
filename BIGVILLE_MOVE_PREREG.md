# BIGVILLE R1 — MOVEMENT + ENERGY (block 249000) — PRE-REGISTRATION

**Pre-registered BEFORE any number.** This document is committed in a separate
prereg commit, ahead of the build/measurement commit. It fixes the claims, the
gates, the failing controls, and the discipline ledger the results must satisfy.

Base SHA (merge-base, origin/main): `aa644fc2a37cf64aa2d8cd169bf39696c2503ee4`
Branch: `worktree-agent-a92fba8037770d2d1`
Block: **249000–249999** (R1 of the bigville movement/economy ladder;
spec `BIGVILLE_MOVEMENT_ECONOMY_SPEC.md` §3 R1).

## Seed claim (verbatim, `python scripts/seed_claim.py 249000 249999`)

```
SEED CLAIM 249000-249999: CLEAN -- no collision DETECTED.
  Scope: 971 files with seed sinks; 681 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

## Architecture (target: ZERO new Rust)

- Movement + energy are **graph rules over a persistent map-belief**, composed
  from existing DSL Terms (Argmin / MinOver / Neighbours / Filter / Plus /
  Minus / IfThenElse / Eq / Gte …). No new Rust Term. `git diff runners/dsl`
  MUST be empty.
- New additive files only, all prefixed `bigville_move_`:
  `seeds/bigville_move_nav.json`, `seeds/bigville_move_energy.json`,
  `worlds/bigville_move_world.py`, `scripts/bigville_move_run.py`,
  `tests/test_bigville_move_migrated.py`, this file, `BIGVILLE_MOVE_RESULTS.md`,
  `results/bigville_move/*`. No existing tracked file is edited; the scaffold
  (`bigville_sim_world` / `bigville_drama_world`) and the 245/247/248 seeds are
  reused BY IMPORT / subclass.
- **Movement runs in an ISOLATED movement substrate** (`substrate_rs.Substrate()`,
  `root_node=None`) so the nav/energy fixpoint never cross-fires the drama rules.
  The bridge to the proven social layer is the scaffold's `self.pos` dict
  (mechanical host I/O), exactly the channel the scaffold already perceives
  through. After each move, `BigvilleSimWorld.step()` re-runs the scaffold's
  occlusion-gated LOS/earshot query at the NEW position.
- **Every DECISION is a rule.** Which neighbour to step to = an Argmin rule
  (`mv_pick_hop`) descending a graph-native Bellman flood field
  (`mv_relax`). The per-tick move budget (the slow-down) = a rule reading energy
  (`mv_energy_budget`). Energy depletion per hop = a rule (`mv_deplete`). The
  adapter only: builds the walkable cell graph from the grid (mechanical
  ingest), seeds a goal, applies the rule-chosen position delta to `self.pos`,
  and reads state. No Python `if`/`else` over agent state decides movement —
  source-audit gate.

## Claims / gates (measured in the results doc)

### G-move-changes-witnessing (HEADLINE)
A villager whose SEED position has **no line-of-sight to John's enclosed office**
does NOT witness the scheme and (via the proven 245 credibility rule
`bd_villager_backs`) **backs John**. When it MOVES (graph-native nav) onto a cell
that DOES have LOS to the office, it begins accruing `seen_hostile` at the
office event-point → the SAME `bd_villager_backs` rule **flips it to back Mary**,
and the 245/247 witness→credibility→enforcement chain fires differently.
PASS iff: before (seed pos) `backs == John`, `seen_hostile == 0`; after (moved
into office LOS) `seen_hostile > 0` and `backs == Mary`. Both states pasted
verbatim from the graph read-off. Movement is proven by its effect on the
already-proven social layer, not by a position delta alone.

### G-energy-slows
Distance covered per tick DECREASES as the energy budget depletes. The per-tick
move budget is a graded step function of energy (rested → 3 hops/tick; tiring →
2; low → 1; exhausted → 0). PASS iff the cells-moved-per-tick curve is monotone
non-increasing as energy drains, and a rested agent covers strictly more ground
over equal ticks than an exhausted one. Report the full curve.

### Failing controls (each must fail as stated)
- **no goal → no purposeful movement.** A mover with no `seeks` edge: the flood
  never seeds, `mv_pick_hop`'s reachability guard (`gdist < BIG`) is false → the
  rule does not fire → **zero moves (idle)**. (No wander: an unseeded field is
  uniform-BIG, so there is no descent gradient to follow.)
- **wall on the straight line → routes AROUND, no teleport.** Goal placed so the
  straight line crosses a wall. Every applied hop is to an orthogonally ADJACENT
  walkable cell (adjacency graph only connects walkable cells) → path length >
  Manhattan distance, no cell is skipped, no wall cell is entered.
- **goal at current cell → zero moves.** Current cell `gdist == 0` → `mv_pick_hop`
  guard (`gdist >= 1`) false → no hop.
- **energy-cost ablated → no slow-down (cost is load-bearing).** With
  `slow_on = 0` (flat budget) and `energy_cost = 0`, the cells-per-tick curve is
  FLAT (no graded decrease) and the goal is reached in fewer ticks than the
  cost-on arm. Proves the energy cost is load-bearing for the slow-down.

### G-discipline (hard; a rung violating any is void)
- Own engine built in THIS worktree (`cargo build --release`); report md5;
  `test_engine_provenance_migrated` reports `source_match == own`.
- `git diff runners/dsl` empty (no Rust). Canonical shared `.so` never touched
  (this worktree is isolated and builds its own).
- Oracles `rung7_vision_bench.sh` + `per_area_settlement_regression.sh`: fail-set
  node-id SET ⊆ enumerated `results/failure_baseline.json`;
  `test_failure_baseline_migrated` green; ZERO new reds. (A pre-existing
  provenance red on main is not the arbiter — the enumerated baseline is.)
- No brittle engine-identity test (no pinned-md5 equality assertion); any engine
  check asserts the invariant `source_match in {own, shared}`.
- Non-nested worktree; NEVER create a worktree under `gamma-substrate/.worktrees/`.
- Cost: reuse incremental/foveated flood (re-flood only when the active mover's
  goal changed) so movement does not blow the per-tick cost; measure and report
  per-tick cost.
- Git: commits stay on this branch; do NOT merge (supervisor merges). Explicit
  `git add <path>`, never `-A`. Never touch a peer session's uncommitted files.

## Honest scope
Synthetic small-cast model (the 245/247/248 scaffold cast). Mechanism-proven ≠
benchmark. N-scope: the scaffold's small cast on a 30×18 grid; 200-scale is the
separate scale probe (R4), not claimed here.
