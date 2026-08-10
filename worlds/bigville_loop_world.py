"""BigvilleLoopWorld -- bigville R5 (block 253000): THE LOOP CLOSES + emergent
cascades. The INTEGRATION rung -- the full day loop (work -> produce -> buy inputs
up-chain -> sell -> earn -> buy needs down-chain -> consume -> tire -> sleep ->
journal) run over MULTIPLE days with the 30-cast, the economy (R4), the day/night
clock (R3), movement+energy (R1), needs+preference (R2), AND the John/Mary 245 drama
all live together.

WHAT THIS ADDS (spec BIGVILLE_MOVEMENT_ECONOMY_SPEC.md sec 3 R5)
---------------------------------------------------------------
Nothing but SEQUENCING + one integration seed. The ONE new mechanism is the
economy->affect->SOCIETY closing hop (`seeds/bigville_loop_reputation.json`): a
creditor soured by a DEFAULT (R4 be_default_affect -> demand_cash=1) BADMOUTHS the
defaulting debtor (bl_badmouth), and townsfolk who opine on that debtor flip their
backing via the SAME standing>testimony credibility comparison 245's bd_villager_backs
uses (bl_townsfolk_opinion). Everything else is R1-R4, reused by import.

ARCHITECTURE-RULE COMPLIANCE (experiments/gamma-substrate/CLAUDE.md)
-------------------------------------------------------------------
A WORLD ADAPTER. It SUBCLASSES R4 (BigvilleEconWorld) by IMPORT, edits no tracked
file, and holds NO agent decision. It ONLY: ingests the cast/shops/skills/prefs/
drives/homes as graph data; SEQUENCES the async day (advance the R3 clock, arm the
R4/R3 one-shot flags for the phase being advanced, run the Rust fixpoint, move
scheduled awake movers, register witnessed collapse); and reads state back. Every
produce / buy / credit / default / affect-flip / badmouth / opinion / open-shut /
surprise / satisfice / sleep / collapse is a seed RULE. No `if`/`else` over graph
state selects an agent action. No new Rust.
"""
from __future__ import annotations

import json
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(_ROOT, "runners", "dsl", "python") not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "runners", "dsl", "python"))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from substrate.seed_loader import manifest_for                       # noqa: E402
from worlds.bigville_econ_world import (                             # noqa: E402
    BigvilleEconWorld, GRAIN, BREAD, FISH, BAIT, ALE,
    BAKING, FISHING, BAITING, BREWING)

# a fresh activity code for the raw land producer (does not collide with R4's
# BAKING=1/FISHING=2/BAITING=3/BREWING=4). Raw producers (farm, baitshop) draw on a
# RENEWABLE own-input buffer (the land / the sea), seeded large so it does not run dry
# over a short run -- the up-chain terminus of the supply network.
FARMING = 5.0
from worlds.bigville_time_world import DAY, NIGHT                    # noqa: E402

CAST_SEED = os.path.join(_ROOT, "seeds", "bigville_townspeople_30.json")

# A curated economic town over the 30 cast (spec: comparative advantage -> a supply
# network). Trades assigned to the shipped cast roles; the fish-supply up-chain adds a
# `fisherman` supplier + a `baitseller` because the shipped cast has a fishmonger
# (Doreen) but no upstream fisherman (honest scope, prereg). (name, cell, activity,
# output, input_good, supplier_shop, skill, price, start_stock, start_input).
TRADES = [
    # farmer: RAW grain producer -- FARMING skill, renewable land buffer (input_qty=99)
    ("Ferdinand Cloot",  "farm",     (2, 11),  FARMING, GRAIN, GRAIN, None,        3, 4, 6, 99),
    ("Marjorie Dough",   "bakery",   (5, 8),   BAKING,  BREAD, GRAIN, "farm",      3, 4, 0, 2),
    ("Cask Barleigh",    "alehouse", (9, 11),  BREWING, ALE,   GRAIN, "farm",      3, 3, 4, 2),
    # baitseller: RAW bait producer -- BAITING skill, renewable sea buffer (input_qty=99)
    ("__baitseller",     "baitshop", (27, 2),  BAITING, BAIT,  BAIT,  None,        2, 2, 10, 99),
    ("__fisherman",      "fisherman",(28, 4),  FISHING, FISH,  BAIT,  "baitshop",  4, 5, 3, 0),
    ("Doreen Ferrety",   "fishstall",(26, 8),  0.0,     FISH,  FISH,  "fisherman", 0, 6, 0, 0),
]
# hungry consumers who buy bread from Marjorie (the down-chain that closes the loop),
# posted on the east-west path near the bakery so reachability is NOT a confound on the
# carrying-capacity measurement (who eats is decided by supply vs demand, not distance).
CONSUMERS = ["Peony Fen", "Agnes Thorn", "Sergeant Bram Cobble", "Nettie Sparrow"]
CONSUMER_CELLS = [(2, 8), (3, 8), (7, 8), (8, 8)]

# CARRYING CAPACITY -- the town SUSTAINS only if harvest (producers x skill) meets
# consumption (heads x need-rate). The baker's skill IS the town's bread carrying
# capacity knob: the VIABLE regime sizes it ABOVE population bread-demand (4 heads x
# 1 loaf); the SHORTFALL regime sizes it BELOW -> a marginal head goes unfed (famine),
# the honest imbalance finding. NOT hand-forced sustainability: the knob is named and
# both regimes are measured.
BAKER_SKILL = {"viable": 5, "shortfall": 3}
# key goods tracked for the town-level resource BALANCE (produced - consumed per day).
KEY_GOODS = [("grain", GRAIN), ("bread", BREAD), ("ale", ALE),
             ("fish", FISH), ("bait", BAIT)]
# MONEY IS CONSERVED -- total coin is FIXED; every flow is a TRANSFER, never a mint.
# The consumers' daily income is a WAGE: a CONSERVING transfer FROM the producer wage-
# pool (the coin bread-sales pooled there) TO the workers (Peony teaches, Agnes sells
# herbs, Bram walks the watch, Nettie sews) -- a DISCLOSED abstraction of the wage loop
# the full town circulates (per-trade wage learning is R6). Sized to the bread price so
# an eating worker breaks even and coin CIRCULATES rather than draining to the
# producers. `wages_on=False` probes the no-wage regime: coin POOLS at the producers and
# demand seizes though goods are plentiful (a monetary finding, not a mint bug).
# money is FIXED-PRECISION integer CENTS (1 coin = 100 cents), never float -- prices/wages/coin are
# whole cents, so every transfer is exact and conservation holds to the cent. Prices are the SELLER's.
CENT = 100
WAGE = 4 * CENT              # 4.00 coin/day, sized to the bread price


class BigvilleLoopWorld(BigvilleEconWorld):
    def __init__(self, *, cascade_only=False, regime="viable",
                 wages_on=True, wage=WAGE, **kw):
        super().__init__(**kw)
        self.regime = regime
        self.wages_on = bool(wages_on)
        self.wage = float(wage)
        self.eng.load_seed_manifest(manifest_for("bigville_loop_reputation"), None)
        self.cast = json.load(open(CAST_SEED))["inhabitants"]
        self._home = {}          # name -> home cell
        self._journal = []       # (day, name, line) glass-box journal
        self._focus_log = []     # per-day phase-by-phase log for the focus villager
        self._census = []        # per-day census rows
        self._shop_keeper = {}   # shop name -> keeper name
        self._shop_good = {}     # shop name -> output good code
        self._trade_names = set()
        if not cascade_only:
            self._place_cast()
            self._assign_trades()
            self._assign_consumers()

    # ------------------------------------------------------------------ ingest
    def _walkable_spread(self, n):
        """n deterministic spread walkable cells (for placing the cast)."""
        cells = sorted(self._cell_at.keys())
        if not cells:
            return []
        step = max(1, len(cells) // n)
        return [cells[(i * step) % len(cells)] for i in range(n)]

    def _place_cast(self):
        """Place all 30 cast on the grid as movers (so '30-cast' is literal), each
        carrying its seeded psychology params (glass-box). Mechanical graph data."""
        spread = self._walkable_spread(len(self.cast))
        for i, p in enumerate(self.cast):
            nm = p["name"]
            cell = spread[i % len(spread)]
            if nm in self._movers:
                continue
            self.make_trader(nm, cell, coin=10.0, energy=100.0, e_low=15.0,
                             sleep_threshold=40.0)
            self._home[nm] = cell
            pr = p.get("params", {})
            for k in ("charm_weight", "w_spite", "prior_world_safe"):
                if k in pr:
                    self.eng.set_attr(self._movers[nm], k, float(pr[k]))

    def _ensure(self, nm, cell, **econ):
        if nm not in self._movers:
            self.make_trader(nm, cell, **econ)
            self._home[nm] = cell
        else:
            for k, v in econ.items():
                self.eng.set_attr(self._movers[nm], k, float(v))
        return self._movers[nm]

    def _assign_trades(self):
        """Give the economic subset a workplace SHOP, a per-(agent,activity) SKILL, and
        the up-chain `supplied_by` edge -- the sparse supply NETWORK. The baker's skill
        IS the town's bread carrying-capacity knob (regime-driven). Mechanical."""
        for (nm, shop, cell, act, out, ing, sup, skill, price, stock, inq) in TRADES:
            if shop == "bakery":                        # carrying-capacity knob
                skill = BAKER_SKILL.get(self.regime, skill)
            self._ensure(nm, cell, coin=30 * CENT)       # producer coin buffer, in cents
            # the keeper stands AT the workplace cell (be_exchange needs keeper is_at)
            self._apply_hop(nm, self._movers[nm], cell)
            if skill > 0 and act > 0:
                self.set_skill(nm, act, skill)
            self.add_shop(shop, good=out, price=price * CENT, cell=cell, keeper=nm,   # the SELLER's price, in cents
                          activity=act, input_good=ing, stock=stock, input_qty=inq,
                          supplier=sup)
            self._shop_keeper[shop] = nm
            self._shop_good[shop] = out
            self._trade_names.add(nm)

    def _assign_consumers(self):
        """Give the down-chain buyers a hunger drive + a bread inventory slot so a
        hungry buyer navigates to the bakery and buys (the loop's demand side). Posted
        near the bakery so reachability is not a carrying-capacity confound."""
        for i, nm in enumerate(CONSUMERS):
            if nm not in self._movers:
                continue
            cell = CONSUMER_CELLS[i % len(CONSUMER_CELLS)]
            if cell in self._cell_at:
                self._apply_hop(nm, self._movers[nm], cell)
                self._home[nm] = cell
            self.give_good(nm, BREAD)
            self.set_econ(nm, hunger_level=8.0, satiety=5.0, coin=12 * CENT)   # a labourer's purse, in cents

    # ------------------------------------- money (CONSERVED) + carrying capacity
    def total_coin(self):
        """Total coin over ALL agents -- the FIXED money supply. Every exchange / wage /
        restock / repay is a TRANSFER, so this is INVARIANT across the loop; a drift
        would mean a rule mints/burns currency (a bug to find)."""
        return round(sum(self.coin_of(nm) for nm in self._movers), 6)

    def _transfer(self, src, dst, amount):
        """Move `amount` coin src->dst, capped at src's balance. Pure transfer (money
        conserved). Mechanical host I/O -- the WAGE loop the full town circulates."""
        amt = min(float(amount), self.coin_of(src))
        if amt <= 0:
            return 0.0
        self.eng.set_attr(self._movers[src], "coin", self.coin_of(src) - amt)
        self.eng.set_attr(self._movers[dst], "coin", self.coin_of(dst) + amt)
        return amt

    def _pay_wages(self):
        """CONSERVING wage loop: transfer `wage` to each consumer FROM the producer
        holding the most coin (the wage-pool where bread-sales pooled). Never mints --
        pure producer->worker transfer, so total_coin is invariant. Off -> coin pools at
        producers and demand seizes (the monetary finding)."""
        if not self.wages_on:
            return 0.0
        paid = 0.0
        for nm in CONSUMERS:
            if nm not in self._movers or not self._trade_names:
                continue
            employer = max(self._trade_names, key=lambda t: self.coin_of(t))
            paid += self._transfer(employer, nm, self.wage)
        return paid

    def _good_totals(self):
        """Town-level total held of each key good = Σ shop stock + Σ shop input +
        Σ consumer inventory. The carrying-capacity BALANCE is the day-over-day delta
        of this (produced - consumed)."""
        tot = {name: 0.0 for name, _ in KEY_GOODS}
        code_to_name = {code: name for name, code in KEY_GOODS}
        for shop, g in self._shop_good.items():
            nm = code_to_name.get(g)
            if nm is not None:
                tot[nm] += self.stock_of(shop)
        # consumer-held bread (final goods not yet eaten)
        for nm in CONSUMERS:
            if nm in self._movers:
                tot["bread"] += self.inventory_of(nm, BREAD)
        return tot

    def carrying_capacity(self):
        """The town's harvest-vs-demand BALANCE, the measured carrying-capacity margin.
        Per key good: production CAPACITY (Σ producer skill/day), consumption DEMAND
        (population need + downstream input need), and the margin = capacity - demand.
        Positive => sustaining; negative => drawing down / famine."""
        # production capacity: each producer's skill (units/day)
        cap = {name: 0.0 for name, _ in KEY_GOODS}
        code_to_name = {code: name for name, code in KEY_GOODS}
        for (nm, shop, cell, act, out, ing, sup, skill, *_r) in TRADES:
            if shop == "bakery":
                skill = BAKER_SKILL.get(self.regime, skill)
            gname = code_to_name.get(out)
            if gname is not None and act > 0:
                cap[gname] += float(skill)
        # demand: population final-consumption + downstream production-input draw
        dem = {name: 0.0 for name, _ in KEY_GOODS}
        n_bread_eaters = sum(1 for nm in CONSUMERS if nm in self._movers)
        dem["bread"] += float(n_bread_eaters)          # each eats one loaf/day
        for (nm, shop, cell, act, out, ing, sup, *_r) in TRADES:
            gname = code_to_name.get(ing)
            if gname is not None and act > 0:            # a producer draws 1 input/day
                dem[gname] += 1.0
        out = {}
        for name, _ in KEY_GOODS:
            out[name] = dict(capacity=cap[name], demand=dem[name],
                             margin=cap[name] - dem[name])
        return out

    # ------------------------------------------------- the async day loop
    def _navigate_to(self, name, cell, max_hops=40):
        self.set_goal(name, cell)
        for _ in range(max_hops):
            if self.pos[name] == cell:
                break
            traj = self.move_one(name)
            if not traj:
                break
        return self.pos[name] == cell

    def run_day(self, day, focus="Marjorie Dough"):
        """One full async day, sequenced (every DECISION is a rule; this only advances
        the clock, arms one-shots, ticks, moves, and reads).

        MORNING (DAY phase, open hours): keepers produce from inputs+skill; hungry
        consumers navigate to the bakery and buy (down-chain); keepers restock inputs
        up-chain from their supplier. EVENING: energy has depleted from the walking;
        sleep decisions fire; restful sleep (safe at home) replenishes. NIGHT: journal.

        `focus` records a phase-by-phase glass-box for one villager (the spec headline:
        wake -> bake during hours -> sell -> buy grain -> tire -> sleep -> journal)."""
        fshop = next((s for s, k in self._shop_keeper.items() if k == focus), None)
        log = dict(day=day, name=focus)
        if focus in self._movers:
            log["wake_energy"] = float(self.eng.node(self._movers[focus])["attrs"].get("energy", 0))
            log["wake_coin"] = self.coin_of(focus)
        goods_before = self._good_totals()
        # ---- DAWN: pay the conserving wage loop (producer pool -> workers) -----------
        self._pay_wages()
        # ---- MORNING: open the town -------------------------------------------------
        self.set_phase(DAY)
        self.set_hours(1)
        self.refresh_open()
        if fshop is not None:
            log["shop_open"] = self.shop_open(fshop)
            log["grain_before_bake"] = self.input_of(fshop)
        # producers PRODUCE (yield proportional to skill; consumes one input)
        for shop in self._shop_keeper:
            if self._shops and self.eng.node(self._shops[shop])["attrs"].get("activity", 0) > 0:
                self.produce(shop)
        if fshop is not None:
            log["baked_to_stock"] = self.stock_of(fshop)
        # DEMAND: hungry consumers navigate to the bakery and buy bread (down-chain).
        # A hungry consumer who cannot buy (stall empty / no coin) is UNMET DEMAND --
        # the carrying-capacity shortfall / demand-seizure signal, read off the graph.
        sold_before = self.coin_of(focus) if focus in self._movers else 0
        stock_before = self.stock_of(fshop) if fshop is not None else 0
        unmet = []
        for nm in CONSUMERS:
            if nm not in self._movers:
                continue
            b0 = self.bought_of(nm)
            self._navigate_to(nm, TRADES[1][2])      # bakery cell
            if self.pos[nm] == TRADES[1][2]:
                self.buy(nm)
            if self.bought_of(nm) == b0:             # attempted, got no bread
                unmet.append(nm)
        log["unmet_demand"] = unmet
        if fshop is not None:
            log["sold_units"] = stock_before - self.stock_of(fshop)
            log["coin_from_sales"] = self.coin_of(focus) - sold_before
        # CONSUMPTION: each consumer EATS one held loaf (destroyed -> leaves the town),
        # so the observed balance reflects real production - consumption (not hoarding).
        eaten = 0
        for nm in CONSUMERS:
            if nm not in self._movers:
                continue
            held = self.inventory_of(nm, BREAD)
            if held >= 1.0:
                self.give_good(nm, BREAD, qty=held - 1.0)   # eat one loaf
                eaten += 1
        log["eaten"] = eaten
        # SUPPLY: keepers restock their input up-chain from the supplier
        for (nm, shop, cell, act, out, ing, sup, *_rest) in TRADES:
            if sup is not None:
                self.restock(shop)
        if fshop is not None:
            log["grain_after_restock"] = self.input_of(fshop)
        # ---- EVENING: everyone is safe at home, tired -> sleep + replenish ----------
        for nm in self._movers:
            self.configure_time(nm, safe=1.0, lateness=1.0)
        self.set_phase(NIGHT)
        self.run_sleep_decisions()
        # a day passes for the perishables: unsold bread/fish on the stalls lose freshness and,
        # left too long, rot away (a WORLD FACT -- what a seller then charges for stale stock is the
        # seller's own pricing decision, not done here).
        self.tick_spoilage()
        if focus in self._movers:
            a = self.eng.node(self._movers[focus])["attrs"]
            log["night_energy"] = float(a.get("energy", 0))
            log["asleep"] = int(a.get("asleep", 0))
            log["end_coin"] = self.coin_of(focus)
        # observed carrying-capacity balance: day-over-day change in town-held goods
        goods_after = self._good_totals()
        log["observed_balance"] = {g: round(goods_after[g] - goods_before[g], 3)
                                   for g in goods_after}
        self._focus_log.append(log)
        # ---- NIGHT: journal (glass-box) ---------------------------------------------
        self._write_journals(day)
        row = self._census_row(day)
        row["observed_balance"] = log["observed_balance"]
        row["unmet_demand"] = log["unmet_demand"]
        row["total_coin"] = self.total_coin()
        self._census.append(row)

    def run_town(self, days=3):
        """Run the multi-day loop. Asserts the MONEY-CONSERVATION invariant: total coin
        is FIXED across the whole loop (every flow a transfer, never a mint). A drift is
        a currency-minting bug, surfaced here, not hidden."""
        self._coin0 = self.total_coin()
        for d in range(1, days + 1):
            self.run_day(d)
            drift = round(self.total_coin() - self._coin0, 6)
            assert drift == 0.0, (
                "MONEY NOT CONSERVED: day %d total_coin drift %g (a rule minted/burned "
                "currency)" % (d, drift))
        return self._census

    def coin_conserved(self):
        """(start_total, end_total, drift) -- the money-conservation ledger for the run."""
        end = self.total_coin()
        start = getattr(self, "_coin0", end)
        return dict(start=start, end=end, drift=round(end - start, 6))

    def _write_journals(self, day):
        for (nm, shop, *_r) in TRADES:
            a = self.eng.node(self._movers[nm])["attrs"]
            self._journal.append(dict(
                day=day, name=nm, coin=self.coin_of(nm), energy=float(a.get("energy", 0)),
                stock=self.stock_of(shop), asleep=int(a.get("asleep", 0))))

    def _census_row(self, day):
        rows = {}
        for nm in self._trade_names | set(c for c in CONSUMERS if c in self._movers):
            a = self.eng.node(self._movers[nm])["attrs"]
            rows[nm] = dict(coin=self.coin_of(nm), hunger=self.hunger_of(nm),
                            energy=float(a.get("energy", 0.0)),
                            collapsed=int(a.get("collapsed", 0)))
        stocks = {shop: self.stock_of(shop) for shop in self._shop_keeper}
        inputs = {shop: self.input_of(shop) for shop in self._shop_keeper}
        return dict(day=day, agents=rows, stocks=stocks, inputs=inputs)

    # ------------------------------------------------- glass-box read-offs
    def marjorie_day(self, day=1):
        """One villager's WHOLE day read straight off the graph, phase by phase (spec
        headline: wake -> bake -> sell -> buy grain up-chain -> sleep -> journal)."""
        return [j for j in self._focus_log if j["name"] == "Marjorie Dough" and j["day"] == day]

    def focus_log(self):
        return self._focus_log

    def census(self):
        return self._census

    def journal(self):
        return self._journal

    # ------------------------------------------------- reputation read-offs
    def opines(self, townsperson, debtor):
        """Wire a `opines_on` edge (the sparse social graph) + the opinion attrs."""
        t = self._movers[townsperson]
        self.eng.set_attr(t, "opinion_on", 1.0)
        self.eng.set_attr(t, "badmouth_weight", 2.0)
        self.eng.set_attr(t, "backs_debtor", 1.0)
        self.eng.add_edge_unchecked(t, "opines_on", self._movers[debtor])

    def backs_debtor_of(self, townsperson):
        return int(self.eng.node(self._movers[townsperson])["attrs"].get("backs_debtor", -1))

    def badmouthed_of(self, name):
        return float(self.eng.node(self._movers[name])["attrs"].get("badmouthed", 0.0))

    def badmouth_count(self):
        return len(list(self.eng.nodes("Badmouth")))
