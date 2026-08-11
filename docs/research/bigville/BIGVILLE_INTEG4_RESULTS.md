# BIGVILLE R10d — MAKE CIRCULATION REAL (know → seek → walk → buy) — RESULTS

**Block 275000.** Pre-registration: `BIGVILLE_INTEG4_PREREG.md` (committed before any
number). Base `92d8f71ea4`. Additive-only (`bigville_integ4_*`); **no Rust**
(`runners/dsl` diff EMPTY); no `.so` committed; own canonical engine.

> **(Supervisor note.)** The build agent completed the world + run and produced the
> results, but paused before committing them / writing this file; the supervisor
> completed the commit and authored this RESULTS from the emitted artifacts.

## The headline — circulation is REAL

`circulation 0 → 377` (total goods bought over the run). The R10 residual ("buyers not
co-located with shops; circulation ~0") is CLOSED — not as a read-off patch but by
building the missing loop the creator named: **"do they know about the shops? seed them
with the knowledge."**

- **The gap (confirmed):** `be_exchange` requires buyer+shopkeeper on the SAME cell;
  `add_shop` minted a `Shop` but **no `Source`**, so `nd_choose_good`'s Argmax over
  `NodesOfType("Source")` had nothing to pick; `integ_step` armed a purchase in place
  and never stepped the walk. Buyers sat home → 0 buys.
- **The fix (all admissible + graph-native):** mint a `Source` per shop `at_cell` its
  cell (the buyer's KNOWLEDGE of where a good is sold); cluster the housing within a
  short walk of a coherent market square; each day arm the drive, let the need rules
  DECIDE good+source, wire `seeks` via the mechanical `set_goal`, and STEP the R1 nav
  pipe (`mv_seed_goal`/`mv_relax`/`mv_pick_hop`) hop-by-hop to the stall; then `buy`
  (`be_exchange`/`be_credit` decide); then walk home. Every decision stays a seed rule.

## Measured (1800 ticks / 50 days, cast 16, seed 275000)

| quantity | value |
|---|---|
| circulation (goods bought) | **377** (was 0) |
| total buys / buys-per-day mean | 160 / **3.2** |
| shopping days with ≥1 buy | **50 / 50** |
| keeper takings | Marjorie Dough (baker) 370 · Doreen Ferrety (fishmonger) 30 |
| home→shop distance (min/median/max hops) | 3 / **4** / 5 |
| round-trip max vs day budget | 10 hops < **36 ticks/day** → `fits_day_budget: True` |
| Σcoin conservation | 2633 → 2633, **Δ=0, invariant** |
| regime (R10 classifier) | `CLEAN_PERIODIC` (unchanged from R10c) |

**Glass-box `is_at_traces`** confirm the walk: e.g. *Prudence Inkwell* home [13,5] →
stall [16,9] over 7 hops `[[13,5],[14,5],[15,5],[16,5],[16,6],[16,7],[16,8],[16,9]]`,
`arrived: True, bought: True`. Buyers physically reach shops they know about.

## Honest reads

- **The tick budget was real and now fits:** clustering homes near the market made the
  round trip (≤10 hops) fit inside a 36-tick day — the creator's "not enough ticks"
  concern, resolved by a coherent market layout rather than lengthening the day.
- **Regime stays `CLEAN_PERIODIC`:** real circulation did NOT move the regime — the
  clock-scheduled social cadences (R10c) still dominate the autocorrelation. The
  endogenous-trigger follow-on remains the lever for punctuation.
- **Economic stress rose:** feed shows violence 46 / evictions 13 / deaths 8 (vs R10c
  17 / 5 / 5) and gini_wealth 0.93 — a real read (a working market + rent stratification
  concentrates wealth and sharpens hardship), reported, not tuned.
- **Anti-tuning held:** layout/knowledge are calibrations on principle; the regime and
  circulation number are measured outcomes.

## Discipline
`runners/dsl` diff EMPTY; no `.so` committed; gate `test_bigville_integ4_migrated`;
`test_failure_baseline_migrated` 11/11. Pre-existing canonical-stale provenance red
persists (engine `ada5f2ae`, R10d changed no Rust). Raw:
`results/bigville_integ4/{macro,shopping,townstate}.json`.
