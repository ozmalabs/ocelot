# PERF FINDINGS — where the town's tick time actually goes (block 290000)

A measure-first pass triggered by the 289000 residual "the conduct pass is not yet
O(surprise) at town scale (~0.8 s/tick)." **That claim was a MISATTRIBUTION.** No
code changed (a flood-cache fix was tried and REVERTED — it was a red herring, see
below). Canonical `.so` `fd82dc2978dbb055496dd82390ac2ebe` untouched; NO Rust.

## 1. The conduct spine is NEGLIGIBLE

| measurement | result |
|---|---|
| conduct pass alone (cast 6 / 10 / 14) | **4 / 11 / 24 ms/tick** (O(N²) in pre-minted options, but tiny) |
| `integ_step` conduct=False vs True (cast 8) | **818 vs 814 ms** (within noise) |
| conduct=False vs True (cast 12) | 941 vs 998 ms (~57 ms = the conduct pass) |

The ~0.8 s/tick I attributed to the conduct fold-in in the 289000 ledger is the
**town's own `integ_step`**, which is that slow WITH OR WITHOUT conduct. The 289000
residual is corrected: the conduct spine adds ~5–60 ms, not 0.8 s.

## 2. The real cost is the nav's PER-HOP run_rules

Profiling (cProfile, cast 10, conduct off): `_route_residents` is **~1.4 s/tick**.
The town's daily-routine routing advances each resident by calling `move_one`, which
runs the nav fixpoint. Breaking down the rule-fires per tick (deterministic, unlike
wall-clock which was noisy across runs: 818–1480 ms):

| rule-fires / tick | share |
|---|---|
| flood (`mv_relax`) | ~6 | **2%** |
| per-hop (`mv_pick_hop` + `mv_deplete`, × move-budget × residents) | ~265 | **98%** |

**The wall is the per-hop full-fixpoint `run_rules`** — a whole-substrate fixpoint
fires *per hop, per resident, per tick* to decide one gradient-descent step.

## 3. The flood-cache "fix" was a RED HERRING (measured, reverted)

`_flood_and_budget` keys its BFS-field cache on `(mover_name, goal_cell)`, but the
field is goal-centric (per-cell distance to goal, "map + goal fixed"), so the name is
spurious — N residents to the same cell re-flood an identical field. Dropping the name
(and sorting routing by goal) is **byte-identical** to the reference positions... and
reduced floods by **0%**: this town's routine spreads residents across ~unique goals
(distributed workplaces mornings, distinct homes evenings), so consecutive movers
rarely share a goal cell. And floods are only 2% of cost anyway. **Reverted** — a
byte-identical 0%-gain change is not a perf win, it's noise. (The keying is still a
latent inconsistency worth a one-line cleanup, but it moves nothing here.)

## 4. Conclusion + the honest next step

- The thing I was asked to optimise (the conduct pass) **does not need optimising** —
  it is negligible.
- The town's tick is bound by the **nav's per-hop `run_rules`**, an ENGINE-level cost:
  each hop re-runs a whole-substrate fixpoint. The fix is the SAME incremental-match /
  binding-projection work already built for the eye (blocks 192000 / 195000) — a
  RETE-style matcher that re-evaluates only changed bindings — applied to the nav's
  per-hop rules. That is a Rust/engine change, OUT OF SCOPE for a no-Rust Python pass,
  and it belongs to the movement subsystem, not the conduct spine.
- Net: the fold-in is efficient; the town's *pre-existing* routing scaffold is not, and
  its cure is engine-side, not adapter-side.
