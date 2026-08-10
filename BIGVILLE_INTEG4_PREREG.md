# BIGVILLE R10d — MAKE CIRCULATION REAL (know → seek → walk → buy) — PRE-REGISTRATION

**Block 275000. Pre-registered BEFORE any recorded number.** Base = commit `92d8f71ea4`
(the R10c ACTIVATE-SOCIAL-RUNGS rung, `bigville_integ3_*`, on top of the whole ladder).
Seed-claim: `python scripts/seed_claim.py 275 275` → **CLEAN — no collision DETECTED**
(with the tool's standing caveats: the unit is the seed integer; a CLEAN result means "no
collision detected", never "no collision exists"; the tool under-reports by design).

## The gap (diagnosed, to be verified then fixed)

Since R10 the town's `circulation` reads **0**. It is NOT a read-off artifact — it is a
real DYNAMICS gap, three defects deep:

1. **No seller at the shop.** `be_exchange` (`bigville_econ_exchange`) fires only when a
   buyer AND a shopkeeper are `is_at` the SAME cell as the shop. R10 placed keepers at
   arbitrary `_walk()` cells and R10b's `_layout_town` parked them elsewhere — a keeper was
   never on its own stall, so no buyer could co-locate with a seller.
2. **No knowledge of where a good is sold.** `add_shop` mints a `Shop` + `Good` but NO
   `Source` node; `nd_choose_good`'s Argmax ranges over `NodesOfType("Source")`, finds
   none, so a buyer forms no spatial goal, never seeks a shop, never co-locates.
3. **The walk phase is never stepped.** `integ_step` only ARMS a purchase (`buy_armed`)
   each tick with buyers parked at home; the drive→goal→seek→WALK pipeline
   (`nd_form_sustenance_goal`/`nd_choose_good` → `mv_seed_goal`/`mv_relax`/`mv_pick_hop`) is
   never driven for shopping.

The creator's directive: *"the buyers can't get to the shops … do they know about the
shops? they should be seeded with the knowledge."* In this substrate a buyer's knowledge of
a shop IS a `Source` node at the shop's cell carrying its good.

## The fix — `BigvilleInteg4World(BigvilleInteg3World)` (additive, all admissible)

Subclass R10c. Ship NO new seed and NO new Rust; reuse the LANDED `nd_*` (choice), `mv_*`
(navigation) and `be_*` (exchange) rules exactly as their own R1/R2/R4 adapters drive them.
Every DECISION stays a seed rule; the adapter only seeds knowledge, wires `seeks`
mechanically, and steps the pipeline.

- **SEED THE KNOWLEDGE.** One `Source` per shop, edged `at_cell` the shop cell, carrying the
  shop's good (a belief the buyer HOLDS, like seeding home/class/heir). Buyers get a
  heterogeneous `has_pref` (drawn ~Normal — population = distribution over seeds, NEVER
  wealth) so `nd_choose_good` can rank, plus an inventory `Good` per sellable good so
  `be_exchange`'s `has_good` match is satisfiable.
- **A COHERENT MARKET (layout calibration on principle, NOT a day dial).** R10's two stalls
  sat at arbitrary `_walk()` corners ~24 cells apart — no cluster can be near both, and the
  far stall exceeds one energy tank. A village clusters around ITS market: seat both stalls
  in a central market square, place each keeper ON its stall cell (a seller mans it), and
  seat the housing district a few cells away. The **day is UNCHANGED at 36 ticks** — homes
  are moved to fit the trip inside the existing budget, the budget is NOT stretched to fit
  the trip. Measured home→shop Manhattan distance and the tick/energy budget are REPORTED.
- **RAW-MATERIAL INFLOW.** R10 seeded shops with `input_qty=6` and no working up-chain
  supplier, so `be_produce` starves after ~1 day. The sea/field keep yielding: each tick top
  each shop's raw input to a floor. A GOOD inflow (not coin), so Σ(coin) is unaffected — this
  removes a starved-supply BUG, it is not a circulation dial (the buy count still emerges
  from hunger, coin, and the sellers' rule-driven trade).
- **ARM + STEP THE SHOPPING LOOP.** Each day, for each living hungry buyer (metabolism
  raises `hunger_level`; the buy's `satiety` lowers it — endogenous regulation): arm the
  sustenance drive; `nd_arbitrate`/`nd_form_sustenance_goal`/`nd_choose_good` DECIDE the food
  goal + good + source and wire `seeks`; step the nav pipe to the stall; `self.buy(nm)` →
  `be_exchange` (coin) or `be_credit` (short+trust) fires at co-location; walk home (fed →
  energy restored). `decide` is shadowed by `BigvilleAffectWorld.decide` on the MRO, so the
  need-choice is invoked explicitly via `BigvilleNeedWorld.decide(self, nm)` — the same
  proven mechanical sequencing, not a re-decision.

## Pre-registered measurements (whatever emerges is reported — anti-tuning absolute)

Run LONG (**1800 ticks / 50 days, cast 16, seed 275000**) and report:

1. **circulation before (0) → after** — the real per-run total and the per-day buy count;
   coin flowing buyer→keeper (keeper takings); hunger satisfied at the market; a few movers'
   `is_at` traces showing them walking home→stall.
2. **Σ(coin+reserves+pool+funds) INVARIANCE** — Δ must be 0 after wiring real buying
   (R10b/R10c hold it; a purchase is a conserved buyer→keeper transfer).
3. **measured home→shop Manhattan distance vs the day's tick budget** (36 ticks, 1 hop/tick)
   and one energy tank — reported honestly; the day is NOT lengthened.
4. **RE-CLASSIFIED macro regime** with R10's UNCHANGED `bigville_integ_measure.classify_regime`
   — does real circulation change the dynamics vs R10c's CLEAN_PERIODIC? Whatever regime
   emerges (verdict, heavy_tail_ratio, activity head/tail) is MEASURED and reported. The
   layout/market/inflow are correctness calibrations on principle — never dials to force
   circulation>0 or a particular regime.

## Discipline (self-imposed gates)

- **Additive-only.** New `bigville_integ4_*` files (`worlds/bigville_integ4_world.py`,
  `scripts/bigville_integ4_run.py`, `tests/test_bigville_integ4_migrated.py`). NO edit to any
  tracked R10/R10b/R10c/landed-seed file (import + subclass). No new seed shipped.
- **No Rust.** `git diff 92d8f71ea4 -- runners/dsl` MUST be EMPTY. No engine rebuild; no
  committed `.so` (gitignored; the canonical is copied in for imports only).
- **Provenance.** The pre-existing canonical-stale red (`test_engine_provenance_migrated`,
  engine `ada5f2ae`) is NOT mine — it persists, untouched.
- **Gates.** `tests/test_bigville_integ4_migrated.py` + `tests/test_failure_baseline_migrated.py`
  (stays 11/11). The two ~43-min bench oracles are relaxed (additive / no-Rust).
