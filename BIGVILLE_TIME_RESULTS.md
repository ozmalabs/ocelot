# BIGVILLE R3 — DAY/NIGHT + THE ASYNC TEMPORAL SUBSTRATE (block 251000) — RESULTS

Graph-native day/night + async time/energy on the proven R1/R2 movement+needs world
over the 245/247/248 social scaffold. Every sleep / collapse / concern / credibility
verdict is a RULE; the world adapter only advances the clock, applies rule-decided
state, ticks, and reads. **Zero new Rust** — the two R3 seeds plus the reused 239000
`arousal_window_coreg` compose existing DSL Terms. Prereg: `BIGVILLE_TIME_PREREG.md`.

Engine: own build `source_match == own`, sha256 `57182d6cef737290`, md5
`10f65be659e0d9a9290aff39f7f5b92a`. Base SHA `f9a4e0a4a326a4f87ab48c4b622f436a6dcd7608`.
Prereg commit `caf9abc377789087cc6d97647dbeb2de3d31d051`. All numbers deterministic
(no RNG). Runner: `scripts/bigville_time_run.py` → `results/bigville_time/results.json`
(`all_pass=True`). Gate suite: `tests/test_bigville_time_migrated.py` (7/7).

---

## G-dark-gates-witnessing (HEADLINE) — PASS

The SAME villager at the SAME cell `(21,6)` — a cell with a clear line-of-sight into
John's occluded office **and beyond hearing range** (distance 16 > hear 11), so the
office scheme is witnessable there by SIGHT ONLY — under two locked phases. Dark
shrinks the sight-query RANGE below the office distance, so the scheme is WITNESSED by
DAY and NOT by NIGHT, and the SAME 245 credibility rule (`bd_villager_backs`) flips:

```
        sight_range  seen_hostile  seen_benevolent  heard_claim   backs
DAY         16            11             13              9         Mary
NIGHT        3             0             13              9         John
```

The flip is on the day/night phase ALONE: `seen_benevolent` (the seed benevolence
prior) and `heard_claim` (the paper-borne channel) are IDENTICAL across the two arms
— the ONLY thing that changes is `seen_hostile`, the SIGHT-witnessed office scheme,
which the shrunk night range gates out. Perception — and therefore who witnesses
John's scheme — is now TIME-DEPENDENT: the abuser literally schemes under cover of
darkness, and the credibility/enforcement chain fires contingently on WHEN as well as
WHERE. (Hearing is unmodulated — dark reduces SIGHT only — so the witness is placed
beyond the office's earshot to make sight the sole reaching sense; this is the honest
geometric requirement, since the scaffold's `perceives` is sight-OR-hearing and
hearing carries further than sight.)

## G-async-determinism (LOAD-BEARING) — PASS

With day=CONSTANT + energy=∞ + no movers, `BigvilleTimeWorld(day_const=True)` is
DECISION-IDENTICAL to the synchronous scaffold `BigvilleSimWorld` over 14 ticks —
every inhabitant's backing, John's held/stated intent, Mary's inference/goal/claim,
the reporter's frame, and the newspaper match field-for-field. So every 245/247/248
landed number is UNCHANGED: the async substrate reduces to the scaffold in that limit.
A repeat run reproduces byte-identically — the async scheduling order is seeded and
deterministic (sorted agent names), never wall-clock-dependent.

```
reduces_to_scaffold = True   (14/14 ticks decision-identical)
deterministic_repeat = True  (run == rerun, byte-identical)
```

## G-sleep-is-chosen — PASS

The sleep-or-defer decision is `bt_decide_sleep`, a `decision_value` trade-off:
`sleep_drive = max(0, sleep_threshold − energy) + safe_bonus·safe + late_bonus·lateness`
must be actually tired (energy < threshold), safe, late, AND exceed `goal_urgency`.

```
                                        sleep_kind   energy curve (night ticks)
IDLE  (tired, safe, late, not busy)         1        20→45→70→95→100→100…   (chose RESTFUL sleep → rest_cap 100)
BUSY  (same, goal_urgency=100)              0        20→20→20→20→20…        (DEFERS — never asleep, keeps the goal)
NO-OPTION (sleep_enabled=0, e=2)            2        8→14→20→26→30→30…      (failing control: runs to COLLAPSE)
```

The idle agent elects to sleep and restful sleep replenishes it to `rest_cap` (100);
the busy agent with an unfinished high-urgency goal DEFERS (the goal wins the trade-
off); removing the sleep option (`sleep_enabled=0`) leaves the agent unable to sleep,
so it depletes and COLLAPSES (`sleep_kind=2`).

## G-collapse-nonrestorative-and-witnessed — PASS

Exhaustion collapse (`bt_collapse`: `energy < e_collapse` with no sleep option) is
INVOLUNTARY (fires wherever the agent is) and NON-restorative — it recovers only
toward `collapse_cap` (30), strictly below a restful sleep's `rest_cap` (100): the
spiral.

```
post-restful-sleep energy = 100   (a chosen restful sleep)
post-collapse      energy =  26   (recovering toward collapse_cap 30, ≪ 100)  → SPIRAL
```

A collapse WITNESSED (a witness with day line-of-sight to the collapse cell) fires
CONCERN; the SAME collapse OCCLUDED (night short sight range) fires NONE — concern is
occlusion-gated, riding the 239000 AffectiveState arousal/valence channel:

```
                  Concern nodes   witness arousal   witness valence   concerned
DAY (witnessed)         1              0 → 4             5 → 2             1
NIGHT (occluded)        0              0                 5                 0
```

Self-management (collapse) couples to the social-affect layer (a witness's concern),
and the coupling is contingent on whether the collapse is seen — the same day/night
sight-range that gates witnessing in the headline gates concern here.

## G-sleeping-is-cheap — PASS

Per-tick movement-engine work (rule-fire steps) across a DAY block (movers navigate:
Bellman floods + hops) vs a NIGHT block (the town is tired+safe+late → SLEEP → not
scheduled → near-zero surprise → near-zero work):

```
        mean per-tick   per-tick steps
DAY        152.6         160 158 148 147 150
NIGHT        1.2           2   1   1   1   1     (all 3 movers asleep through the night)
```

Night is ~127× cheaper per tick than day — a sleeping agent produces no state change,
hence no work (compute proportional to surprise, via the async scheduler skipping
sleepers). This is what makes an overnight town of many agents affordable in real
time, rather than more expensive.

---

## Discipline ledger

| check | result |
|---|---|
| Base SHA (merge-base) | `f9a4e0a4a326a4f87ab48c4b622f436a6dcd7608` |
| Prereg commit (separate) | `caf9abc377789087cc6d97647dbeb2de3d31d051` |
| Engine provenance | `source_match == own`, sha256 `57182d6cef737290`, md5 `10f65be659e0d9a9290aff39f7f5b92a` |
| `runners/dsl` diff (incl. `term.rs`) | **EMPTY** — zero new Rust |
| Canonical shared `.so` md5 start==end | `fd82dc2978dbb055496dd82390ac2ebe` (UNTOUCHED) |
| `rung7_vision_bench.sh` | 214 passed, 10 skipped, **0 failed** (zero new reds) |
| `per_area_settlement_regression.sh` | 278 passed, 5 skipped, 23 failed — all 23 FAILED node ids ⊆ enumerated `results/failure_baseline.json` (composer_driver / cortices_tick / elaboration / gap_awareness / topic_route_selfheal — all pre-existing conversation/topic reds; **zero new reds**) |
| `test_failure_baseline_migrated` | 11 passed |
| R3 gate suite `test_bigville_time_migrated` | 7 passed |
| Additive only | all-new `bigville_time_` files; no tracked file edited |
| Source-audit | adapter runs no rule engine; sleep/collapse/concern are seed rules |
| Failing controls that fail | busy DEFERS; `sleep_enabled=0` → collapse; occluded → NO concern |

## Honest scope / residuals

- **Synthetic small-cast model.** Gates use a handful of agents (the 245 cast +
  R1/R2 movers). Mechanism-proven ≠ benchmark. The "sleeping is cheap" figure is a
  per-tick rule-fire-step ratio on the movement engine, not a wall-clock 200-agent
  measurement.
- **Dark gates SIGHT only; hearing is unmodulated.** Because the scaffold's
  `perceives` is sight-OR-hearing and hearing carries further than sight (11 > 7),
  the headline witness must be placed BEYOND the office's earshot for the sight-range
  shrink to be the operative knob. This is an honest geometric consequence of reusing
  the scaffold's perception unchanged — not a new perception system. A future rung
  could make darkness reduce hearing too, but the spec scopes dark to sight.
- **Collapse duration is a config, not emergent timing.** How long a collapse persists
  (and thus its witnessing window) is set by the replenish increment; the spiral
  (post-collapse < post-restful) is the load-bearing fact, and it holds by
  construction (`collapse_cap` < `rest_cap`).
- **A rested agent could over-sleep.** `bt_wake` wakes at the applicable cap; with a
  slow night-replenish a mover can sleep past dawn if it never reaches cap (used
  deliberately in the cheap-demo to keep the town asleep). A "wake at morning"
  register is not modelled (would be an R5 loop concern).
- Pre-existing main provenance red (canonical `.so` stale vs a peer's Rust) is NOT
  from this rung; measured on this rung's OWN engine, and the enumerated baseline is
  the arbiter for the oracles.
