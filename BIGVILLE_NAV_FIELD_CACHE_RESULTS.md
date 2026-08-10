# RESULTS — Nav flood-field cache (block 291000)

The measure-first perf pass (290000) located the town's real bottleneck: the nav's
Bellman-Ford **flood** (`mv_relax`), 79% of rule-fires, re-run on every goal-switch.
**This is the fix — and it is NOT the Rust fix I predicted.**

## The honest correction (twice over)
- 290000 said "the cure is the incremental matcher (192000/195000) applied to the
  nav's rules -- a Rust change." **Measured false:** enabling `binding_projection`
  and `set_incremental_match` on the nav substrate gives **0 speedup** (isolated
  flood: 103.4 ms off vs 103.5 / 104.8 ms on -- flat; `cost_steps` identical).
  Reason: the matcher fires on EDGE changes, but `mv_relax` matches the STATIC `adj`
  edges and is triggered by a `gdist` ATTRIBUTE change -- the incremental matcher
  does not index attr-triggered relaxation, so it cannot make a BFS frontier-incremental.
- So the effective fix is **caching the field, not matching faster** -- and it is an
  ADAPTER change, not Rust. The canonical `.so` `fd82dc2978dbb055496dd82390ac2ebe`
  is UNTOUCHED.

## What landed
`_flood_and_budget` now caches each goal's gdist field. The map is STATIC (walls
never move), so a goal's BFS field is valid for the whole run and every mover heading
there. Flood a goal ONCE; RESTORE it (O(cells) writes) on every later goal-switch
instead of re-running the flood (O(cells x passes) rule-fires). A droppable,
byte-identical mirror -- it removes a re-derivation, never a decision.

## Measured (byte-identical throughout)
| metric | before | after |
|---|---|---|
| floods (16 ticks, cast 10) | 97 | **9** (= unique goals) — **10.8×** fewer |
| total rule-fires (`cost_steps`) | 4339 | **1273** — **3.4×** fewer |
| per goal-switch (isolated) | fresh flood **109 ms** | cached restore **12 ms** — **9×** |

Byte-identity gated directly: with the cache ON vs OFF, every resident's position
every tick is identical (`_use_field_cache` toggle); the restored field is bit-for-bit
a fresh flood. 3/3 field-cache gate + 6/6 living-town (which exercises the full nav).

Wall-clock was NOT reliably measurable in this environment (parallel jobs swung the
"same" tick 770–1518 ms); the deterministic fire/flood counts are the honest metric.

## Honest residual — the genuine Rust fix, scoped not started
A real engine win remains: extend the incremental matcher to fire on ATTR changes so
a relaxation flood (`mv_relax`, and every BFS/Bellman flood in the tree — vision,
quanta-nav) becomes frontier-incremental (O(cells) per flood, not O(cells x passes)).
That is a general capability, but it is deep matcher surgery that REBUILDS the
canonical engine and requires re-verifying the WHOLE bench -- a large, high-risk
effort I did not start unilaterally. The field cache delivers the town-nav speedup
now, byte-identically, with zero engine risk; the attr-incremental matcher is the
follow-up if the general win is wanted.
