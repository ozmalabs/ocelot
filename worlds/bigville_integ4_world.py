"""BigvilleInteg4World -- bigville R10d (block 275000): MAKE CIRCULATION REAL.

Since R10 the town's `circulation` read 0. It was NOT a read-off artifact -- it was a
real DYNAMICS gap, three defects deep:

  1. `be_exchange` (bigville_econ_exchange) fires ONLY when a buyer AND a shopkeeper are
     `is_at` the SAME cell as the shop. But the keepers were NEVER placed at their own
     shop cell (R10 placed the fisher/baker at `_walk(i+3)`; R10b's `_layout_town` parked
     them at the inn / a spread cell), so no buyer could ever co-locate with a seller.
  2. `add_shop` mints a `Shop` + `Good`, but NO `Source` node. `nd_choose_good`'s Argmax
     ranges over `NodesOfType("Source")` -- with none, a buyer had NO knowledge of WHERE
     a good is sold, formed no spatial goal, never sought a shop, never co-located.
  3. `integ_step` only ARMED a purchase (`self.buy(nm)` sets `buy_armed`) each tick with
     the buyers parked at home; the drive -> goal -> seek -> WALK phase was never stepped,
     so the buyers never travelled to the market.

R10d closes all three with the SAME admissible world-adapter moves the ladder already
uses -- and every DECISION stays a seed rule:

  * SEED THE KNOWLEDGE. One `Source` per shop, edged `at_cell` the shop cell, carrying the
    shop's good, so `nd_source_cost`/`nd_choose_good` can find and cost it. This is a
    BELIEF the buyer HOLDS (exactly like seeding home/class/heir). Buyers also get a
    heterogeneous `has_pref` (drawn ~Normal per buyer -- population = distribution over
    seeds, NEVER wealth) so the choice Argmax can rank goods, plus an inventory `Good` for
    each sellable good so `be_exchange`'s `has_good` match is satisfiable.
  * A COHERENT MARKET (the creator's "not enough ticks / do they know about the shops").
    R10's shops sat at two arbitrary `_walk()` corners 24 cells apart -- no cluster can be
    near both, and the far one (17 hops) exceeds a single energy tank (~12 hops). A village
    clusters around ITS MARKET: R10d seats both stalls in a central market square, places
    each keeper ON its stall cell (so a seller is present to sell), and seats the housing
    district a few cells away. Measured home->shop Manhattan drops to ~3-5 (see
    `trip_report`) -- inside both the day's tick budget (36 ticks, 1 hop/tick) and one
    energy tank. This is a LAYOUT correctness calibration (a market has a place; a seller
    mans it), NOT the day lengthened to manufacture circulation (the day is UNCHANGED at
    36 ticks).
  * ARM + STEP THE SHOPPING LOOP. Each day, for each living hungry buyer (metabolism
    raises `hunger_level`; the buy's `satiety` lowers it -- endogenous regulation, not a
    forced cadence): arm the sustenance drive, let `nd_arbitrate`/`nd_form_sustenance_goal`
    DECIDE there is a food goal and `nd_choose_good` DECIDE the good+source (rules), which
    wires the `seeks` edge via the inherited mechanical `set_goal`; STEP the R1 nav pipe
    (`mv_seed_goal`/`mv_relax`/`mv_pick_hop`) hop by hop to the stall; then `self.buy(nm)`
    -> `be_exchange` (coin) or `be_credit` (short+trust) fires at co-location. The buyer
    then walks home (having eaten, energy restored). The adapter only mints Source
    knowledge, wires `seeks` mechanically, and steps the pipeline; the good chosen, the
    hops taken, and the trade struck are ALL seed-rule verdicts.

ARCHITECTURE-RULE COMPLIANCE (experiments/gamma-substrate/CLAUDE.md)
-------------------------------------------------------------------
A WORLD ADAPTER. It SUBCLASSES R10c (edits no tracked R10/R10b/R10c/landed-seed file),
holds NO agent decision, ships NO new seed and NO new Rust. The shopping loop reuses the
LANDED nd_* (choice), mv_* (navigation) and be_* (exchange) rules exactly as their own
R1/R2/R4 adapters drive them. `decide` is shadowed by `BigvilleAffectWorld.decide` on the
MRO, so the need-world choice is invoked explicitly via `BigvilleNeedWorld.decide(self,
nm)` -- the same proven phase-A/phase-B mechanical sequencing, not a re-decision.

CONSERVATION: a purchase is a conserved coin transfer buyer->keeper (be_exchange:
buyer.coin -= price, keeper.coin += price). No coin is minted. Sigma(coin+reserves+pool
+funds) stays INVARIANT (verified in the run harness, as R10b/R10c verified it).
"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import numpy as np                                                    # noqa: E402

from worlds.bigville_integ3_world import BigvilleInteg3World, TICKS_PER_DAY  # noqa: E402
from worlds.bigville_need_world import BigvilleNeedWorld, SUSTENANCE  # noqa: E402
from worlds.bigville_econ_world import BREAD, FISH                    # noqa: E402

# --- shopping calibration (pre-registered; NOT dials on a result) --------------
# Metabolism: hunger accrues each day; a purchase's `satiety` (=5) lowers it. With
# +DAILY_HUNGER/day and threshold HUNGER_THRESHOLD, a fed buyer re-crosses threshold in
# ~1 day -> a roughly-daily food run. Values are sensible defaults; whatever buy count
# emerges is MEASURED and reported, never tuned to a target (anti-tuning absolute).
DAILY_HUNGER = 3.0
HUNGER_THRESHOLD = 2.0
WALK_CALLS = 24            # max move_one calls per leg (each = a rule-budgeted burst of
#                           hops); home->shop is ~3-5, so this never binds.
ENERGY_TANK = 100.0       # a rested/fed buyer's energy at the start of a leg (world fact:
#                           sleeping and eating restore the physiological budget).
# RAW-MATERIAL INFLOW. A shop PRODUCES its good from a raw input (bait from the sea, grain
# from the field) via `be_produce`, consuming the input. R10's shops were seeded with only
# `input_qty=6` and no working up-chain supplier, so production STARVED after ~1 day and
# circulation died. The sea and the field keep yielding: each tick the world tops each
# shop's raw input up to INPUT_FLOOR. This is a natural-resource inflow (a GOOD, not coin),
# so Sigma(coin) is UNAFFECTED -- production creating goods and consumption destroying them
# is the economy working, not a coin leak. It is NOT a circulation dial: it only removes a
# starved-supply BUG so the exchange rule can keep matching; the buy count still emerges
# from the buyers' hunger, coin, and the sellers' rule-driven trade. The inflow is
# THROTTLED to a stock ceiling (no raw input arrives while the stall is well-stocked), so
# production idles instead of hoarding unboundedly -- realistic AND cheaper.
INPUT_FLOOR = 8.0
STOCK_CEIL = 40.0         # keep raw input flowing only while stock is below this


class BigvilleInteg4World(BigvilleInteg3World):
    def __init__(self, *, cast=16, seed=275000, **kw):
        super().__init__(cast=cast, seed=seed, **kw)
        self._rng4 = np.random.default_rng(seed + 3)

        # bookkeeping / glass-box read-offs
        self.buys_per_day = []      # [{day, shoppers, arrivals, buys, credit}]
        self.shopping_traces = []   # [{day, name, home, shop, good, path, arrived, bought}]
        self.total_buys = 0
        self.total_credit = 0
        self._market = {}           # shop name -> (x,y) market-square cell
        self._source_of = {}        # shop name -> Source nid
        self._shop_endowed = set()  # buyers already endowed with prefs/goods/drive
        self._buyer_home = {}       # buyer -> home cell (start of each day's errand)

        self._setup_market()
        self._endow_all_buyers()
        self.trip_report = self._measure_trip_budget()

    # ============================================================ MARKET + KNOWLEDGE
    def _buyers(self):
        """Living movers that shop for food -- everyone except the two shopkeepers."""
        keepers = set(self._shopkeepers.values())
        return [nm for nm in self.people if nm not in keepers and not self.is_dead(nm)]

    def _setup_market(self):
        """Seat both stalls in a central MARKET SQUARE, place each keeper ON its stall
        cell, seed a Source (the buyers' KNOWLEDGE of where each good is sold), and
        cluster the housing district a few cells away. Admissible world-setup (placing +
        seeding a belief); makes no decision. Re-points each shop's `at_cell` (the same
        mechanical edge move `move_source` uses) -- the R10 stall cells were arbitrary
        `_walk()` corners, so establishing a coherent market IS the correctness fix."""
        cx, cy = self.W // 2, self.H // 2
        # two adjacent market stalls + a keeper on each.
        want = {"fishmonger": (cx - 1, cy), "bakery": (cx + 1, cy)}
        for nm, sh in self._shops.items():
            scell = self._nearest_cell(want.get(nm, (cx, cy)))
            self._market[nm] = scell
            for c in list(self.eng.neighbours(sh, "at_cell")):
                self.eng.remove_edge_unchecked(sh, "at_cell", c)
            self.eng.add_edge_unchecked(sh, "at_cell", self._cell_at[scell])
            keeper = self._shopkeepers[nm]
            self._place(keeper, scell)                       # a seller mans the stall
            self.homes[keeper] = scell
            # SEED THE KNOWLEDGE: a Source at the stall carrying the shop's good.
            good = float(self.eng.node(sh)["attrs"]["good"])
            self._source_of[nm] = self.add_source("src_%s" % nm, good, scell)

        # cluster the housing district within a short walk (radius 2..6) of the square.
        ring = [(dx, dy) for dy in range(-4, 5) for dx in range(-5, 6)
                if 2 <= abs(dx) + abs(dy) <= 6]
        for i, nm in enumerate(self._buyers()):
            cell = self._nearest_cell((cx + ring[i % len(ring)][0],
                                       cy + ring[i % len(ring)][1]))
            self.homes[nm] = cell
            self._buyer_home[nm] = cell
            self._place(nm, cell)

    def _endow_all_buyers(self):
        for nm in self._buyers():
            self._endow_buyer(nm)

    def _endow_buyer(self, nm):
        """Give a buyer the food-market KNOWLEDGE it holds: an inventory Good for each
        sellable good (so `be_exchange`'s has_good match is satisfiable), a heterogeneous
        per-good PREFERENCE (drawn ~Normal -- population = distribution over seeds, NEVER
        wealth), and a persistent sustenance Drive the daily errand arms."""
        if nm in self._shop_endowed:
            return
        for g in (BREAD, FISH):
            self.give_good(nm, g, 0)
        r = self._rng4
        prefs = {BREAD: float(round(max(0.3, r.normal(2.0, 0.5)), 3)),
                 FISH: float(round(max(0.3, r.normal(1.8, 0.5)), 3))}
        self.set_preferences(nm, prefs, cost_on=1.0,
                             hunger_threshold=HUNGER_THRESHOLD)
        self.set_drive(nm, SUSTENANCE, v_d=0.0, c_d=0.0)
        self._buyer_home.setdefault(nm, self.homes.get(nm, self.pos.get(nm)))
        self._shop_endowed.add(nm)

    def _measure_trip_budget(self):
        """The creator's 'not enough ticks' datum: measured home->nearest-stall Manhattan
        distance vs the day's tick budget (36 ticks, 1 hop/tick) and one energy tank
        (~ENERGY_TANK/energy_cost hops). Pure read; no decision."""
        stalls = list(self._market.values())
        ds = []
        for nm in self._buyers():
            h = self.homes.get(nm)
            if h is None or not stalls:
                continue
            ds.append(min(abs(h[0] - s[0]) + abs(h[1] - s[1]) for s in stalls))
        ds = ds or [0]
        ds_sorted = sorted(ds)
        med = ds_sorted[len(ds_sorted) // 2]
        return dict(home_to_shop_min=min(ds), home_to_shop_median=int(med),
                    home_to_shop_max=max(ds), ticks_per_day=TICKS_PER_DAY,
                    energy_tank_hops=int(ENERGY_TANK // 8.0),
                    round_trip_max_hops=2 * max(ds),
                    fits_day_budget=bool(2 * max(ds) <= TICKS_PER_DAY),
                    stalls=stalls)

    # ============================================================ THE SHOPPING LOOP
    def _walk_leg(self, nm, target):
        """Step the R1 nav pipeline (flood + rule-chosen hops) until the mover reaches
        `target` (or a leg budget runs out). The DIRECTION and STOP are mv_pick_hop
        verdicts; this only counts the legs and records the path. Returns the path."""
        target = tuple(target)
        path = [self.pos.get(nm)]
        for _ in range(WALK_CALLS):
            if self.pos.get(nm) == target:
                break
            traj = self.move_one(nm)
            if not traj:
                break                       # at goal / unreachable (a rule verdict)
            path.extend(traj)
        return path

    def _run_shopping(self, day):
        """One day's food errands. For each living hungry buyer: metabolism raises hunger;
        arm the drive; let the need rules DECIDE good+source and wire `seeks`; walk to the
        stall; `buy` (be_exchange / be_credit decides); walk home (fed -> energy restored).
        Counts buys via the `bought` delta; every decision is a seed rule."""
        shoppers = arrivals = buys = credit = 0
        trace_budget = 4 if day <= 3 else 0     # a few traces for the report
        for nm in self._buyers():
            self._endow_buyer(nm)               # lazily endow newborns
            # metabolism: hungrier each day; the buy's satiety lowers it (endogenous).
            hl = self.hunger_of(nm) + DAILY_HUNGER
            self.set_econ(nm, hunger_level=hl)
            self.eng.set_attr(self._movers[nm], "energy", ENERGY_TANK)   # rested
            self.set_drive(nm, SUSTENANCE, v_d=hl, c_d=0.0)             # urge = hunger
            out = BigvilleNeedWorld.decide(self, nm)   # need-choice (decide is shadowed)
            if out.get("goal") != "get_food" or out.get("target") is None:
                continue                        # not hungry enough today (rule verdict)
            shoppers += 1
            tgt = tuple(out["target"])
            home = self.pos.get(nm)
            path = self._walk_leg(nm, tgt)
            arrived = self.pos.get(nm) == tgt
            if arrived:
                arrivals += 1
            b0 = self.bought_of(nm)
            n_owe0 = len(list(self.eng.neighbours(self._movers[nm], "owes")))
            self.buy(nm)                        # be_exchange (coin) / be_credit (short)
            bought = self.bought_of(nm) > b0
            took_credit = (len(list(self.eng.neighbours(self._movers[nm], "owes")))
                           > n_owe0)
            if bought:
                buys += 1
            if took_credit:
                credit += 1
            if trace_budget > 0 and arrived:
                trace_budget -= 1
                self.shopping_traces.append(dict(
                    day=int(day), name=self.display.get(nm, nm), id=nm,
                    home=home, shop=tgt,
                    good=int(out.get("chosen_good_code") or 0),
                    hops=len(path) - 1, is_at_path=path[:8],
                    arrived=bool(arrived), bought=bool(bought)))
            # walk home (fed -> energy restored); coherent town, repeated daily errand.
            self.eng.set_attr(self._movers[nm], "energy", ENERGY_TANK)
            self.set_goal(nm, self._buyer_home.get(nm, home))
            self._walk_leg(nm, self._buyer_home.get(nm, home))
        self.total_buys += buys
        self.total_credit += credit
        rec = dict(day=int(day), shoppers=int(shoppers), arrivals=int(arrivals),
                   buys=int(buys), credit=int(credit))
        self.buys_per_day.append(rec)
        return rec

    def _replenish_inputs(self):
        """The sea and the field keep yielding: top each shop's raw input up to
        INPUT_FLOOR so `be_produce` never starves. A GOOD inflow (not coin) -- conservation
        unaffected. Mechanical world-delivery, no decision."""
        for shop, ig in self._input.items():
            if self.stock_of(shop) >= STOCK_CEIL:
                continue                       # well-stocked: production idles
            q = float(self.eng.node(ig)["attrs"].get("qty", 0.0))
            if q < INPUT_FLOOR:
                self.eng.set_attr(ig, "qty", INPUT_FLOOR)

    # ============================================================ TICK
    def integ_step(self):
        """R10c's composite tick (economy every tick + social on cadence), then the
        DAILY food-market errand once per day. Buys are folded into the tick's `activity`
        (a structural transition, exactly as a birth / a social event is). NO scheduled
        shocks; every shopping DECISION is a seed rule."""
        self._replenish_inputs()          # raw materials arrive (goods, not coin)
        super().integ_step()
        if self.exploded is not None or not self.macro:
            return
        if self.world_epoch % TICKS_PER_DAY != 0:
            return
        day = self.world_epoch // TICKS_PER_DAY
        if day <= 0:
            return
        rec = self._run_shopping(day)
        self.macro[-1]["buys"] = int(rec["buys"])
        self.macro[-1]["activity"] += int(rec["buys"])

    # ============================================================ read-offs
    def circulation(self):
        """Total goods bought this run -- now a REAL count (buyers walk to the market and
        trade), where R10..R10c read 0. Glass-box read of exchange activity."""
        return int(sum(self.bought_of(nm) for nm in self.people))

    def keeper_takings(self):
        """Coin held by each shopkeeper (the sink the buyer->keeper transfers flow into)."""
        return {self.display.get(k, k): round(self.coin_of(k), 2)
                for k in self._shopkeepers.values()}
