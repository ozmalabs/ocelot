# RESULTS — The full fold-in: conduct spine into the live town (block 289000)

The 280-287 conduct spine wired into the LIVE integ5/play town. **6/6
`test_living_town_migrated.py` on canonical `fd82dc2978dbb055496dd82390ac2ebe`;
`runners/dsl` diff EMPTY — ZERO new Rust.** Published player:
**https://claude.ai/code/artifact/25eabda6-73da-4e3c-9683-970268a478af**

## What landed

- `worlds/bigville_living_town_world.py` — `BigvilleLivingTownWorld(BigvillePlayWorld)`.
  The town is the WORLD (moves bodies, provides co-presence from real positions); a
  CONDUCT LAYER (`BigvilleSurpriseTownWorld` — the residents' minds, Bonds derived from
  the town's classes/roles/order, + the 287000 fast-path) is the AGENT GRAPH. Each town
  tick: read co-presence → drive the surprise-gated Bond-directed collapse → write
  help/give/harm back into the town's own event feed. ADDITIVE (a param on the surprise
  town, byte-compatible default; the town substrate + mechanics untouched).
- `scripts/living_town_play_run.py` + `results/living_town_play/{play.json,conduct_play_live.html}`
  — the exporter + published player.

## Measured

Cast 8, seed 276000: the town runs its own life (market/paper/council/routing) while
the residents' interpersonal conduct is computed live. Over 40 ticks:

| conduct | count |
|---|---|
| help / greet | 19 |
| give (transfer) | 4 |
| **harm** | **3** |

- **Violence is rare (3 of 26) and Bond-directed** — every harm is between the feuding
  pair (v01 ↔ v05, resentment 5), surprise-driven; never a random or a friend.
- **Help is the norm**; the town stays fully alive; conduct flows through the town's
  own `events` feed (so paper / narration / player all surface it).
- Conduct is cleanly disableable (`conduct=False`).

## What this establishes — the arc is whole

The full loop now runs inside the real town: **the world offers affordances, a decision
fires on surprise, the choice is a scoped supergraph collapse valued by the held Bond,
violence is a low-weight affordance almost always declined, and it's all layered onto a
town that keeps its own economy and institutions.** The residents' minds are the agent
graph; the town is the world adapter — the project's own split, at society scale.

## Honest residuals (NOT patched)

- **Performance is not yet O(surprise) at town scale.** The conduct pass runs
  `run_rules` over the mind layer's O(N²) pre-minted directed options each tick
  (~0.8 s/tick at cast 10). The fix is the SAME incremental-match / dirty-index work the
  eye already has (blocks 185000 / 192000) — pre-minting + provision + coupling should
  touch only the surprised residents' scenes. Until then the fold-in runs at a watchable
  cast, not the full 50 in real time.
- **Conduct is recorded into the feed + conduct-layer health.** Deeper coupling (a harm
  driving the town's own injury / life-death, or affecting trade/coin) is a follow-up.
- **Bonds are a deterministic social model** derived from class/role/order, not yet the
  town's own kin/emotion graph; reading the town's native relationships is a refinement.
- **Presence-only prediction** (the standing 284000 residual) carries over.
