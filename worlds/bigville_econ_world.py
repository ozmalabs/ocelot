"""BigvilleEconWorld -- bigville R4 (block 252000): graph-native ECONOMY on top of
the proven R1 movement / R2 needs+preference / R3 day-night world.

WHAT THIS ADDS (spec BIGVILLE_MOVEMENT_ECONOMY_SPEC.md sec 2 + sec 3 R4)
----------------------------------------------------------------------
Production requires SKILL; LOCAL (co-located) exchange of coin<->goods; a sparse
SUPPLY NETWORK up which producers buy their inputs and along which a failure
propagates; DEBT/obligation with a creditor AFFECT FLIP on default (economy ->
affect -> behaviour); and store hours as an EXPECTATION the town holds (a shut
stall violates a held PREDICTION -> SURPRISE -- a DIFFERENT register from a LAW
violation's censure, 247).

  * PRODUCTION      -- `be_produce`: at workplace + input + skill -> output
                       PROPORTIONAL to skill, consume input.
  * LOCAL EXCHANGE  -- `be_exchange`: co-located buyer+seller, open shop, coin ->
                       coin<->good, hunger drops. NEVER a global market clear.
  * SUPPLY NETWORK  -- `be_restock` / `be_restock_credit`: buy inputs UP-CHAIN
                       from a supplier along the `supplied_by` edge.
  * DEBT + AFFECT   -- `be_credit` mints an `owes` obligation when a buyer is
                       short and the seller extends credit (a trust
                       decision_value); `be_default` + `be_default_affect` flip
                       the creditor's AffectiveState (204000/239000) and their
                       next credit decision on a past-term default.
  * EXPECTATION     -- `be_shop_open`/`be_shop_shut` derive `open` from the R3
                       clock + keeper wakefulness; `be_expect_surprise` registers
                       a residual SURPRISE when a held expectation is violated.

ARCHITECTURE-RULE COMPLIANCE (experiments/gamma-substrate/CLAUDE.md)
-------------------------------------------------------------------
This is a WORLD ADAPTER. It SUBCLASSES R3 (BigvilleTimeWorld) by IMPORT, edits no
tracked file, and holds NO agent decision. It does ONLY mechanical I/O: register
goods/shops/skills/supply-edges/obligations/expectations as graph data (ingest);
ARM a one-shot flag for the phase being advanced (produce/buy/restock/repay/
default); run the Rust `run_rules` fixpoint; read state back. EVERY economy
decision -- produce, sell, extend credit, default, flip affect, open/shut, register
surprise -- is a seed RULE (bigville_econ_*), never Python. All economy state lives
in the R1 movement substrate `self.eng` alongside nav/energy/drive/sleep; the econ
rules are gated by one-shot arms so they never cross-fire the nav/sleep fixpoints.
No new Rust: every econ seed composes existing DSL Terms.
"""
from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(_ROOT, "runners", "dsl", "python") not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "runners", "dsl", "python"))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from substrate.seed_loader import manifest_for                 # noqa: E402
from worlds.bigville_time_world import BigvilleTimeWorld       # noqa: E402
from domains import bigville_entities as E                     # noqa: E402  the SEAM: the rich catalog drives the living economy

# integer-native good codes (coin is a scalar attr, not a Good node)
COIN, GRAIN, BREAD, FISH, BAIT, ALE = 1.0, 10.0, 11.0, 12.0, 13.0, 14.0
# catalog-driven goods (the seam): paper/ink/newspaper come from bigville_entities
PAPER, INK, NEWSPAPER = 20.0, 21.0, 22.0
# THE GOODS PORT: the living economy's goods ARE catalog kinds. The classic goods keep their codes
# for back-compat; ANY other catalog item gets a stable code (1000 + its index in the catalog), so a
# good can be added to the living economy by NAME -- no new constant. The rules only compare codes;
# the kind string + catalog weight ride on each Good node so goods are self-describing.
_GOOD_CODES = {"coin": COIN, "grain": GRAIN, "bread": BREAD, "fish": FISH, "bait": BAIT, "ale": ALE,
               "paper": PAPER, "ink": INK, "newspaper": NEWSPAPER}


def good_code(kind):
    """The living good code for a catalog KIND. Classic goods keep their codes; any other catalog item
    gets a stable code (1000 + its catalog index). `bait` has no catalog entry -- it keeps its code."""
    if kind in _GOOD_CODES:
        return _GOOD_CODES[kind]
    return 1000.0 + float(list(E.ITEMS).index(kind))


def good_kind(code):
    """The catalog kind for a living good code (reverse of good_code); '' if none."""
    code = float(code)
    for k, c in _GOOD_CODES.items():
        if c == code:
            return k
    if code >= 1000.0:
        idx = int(code - 1000.0)
        items = list(E.ITEMS)
        if 0 <= idx < len(items):
            return items[idx]
    return ""


GOOD_NAME = {GRAIN: "grain", BREAD: "bread", FISH: "fish", BAIT: "bait", ALE: "ale",
             PAPER: "paper", INK: "ink", NEWSPAPER: "newspaper"}
# activity codes (baking/fishing/... = 1-4 in the seed); printing is the catalog-driven one
PRINTING = 5.0
# activity codes (which trade a skill / shop is)
BAKING, FISHING, BAITING, BREWING = 1.0, 2.0, 3.0, 4.0

# econ defaults set on every Mover that trades (keeper or buyer). Present so the
# rules never read a missing key; population variation is set by the caller.
ECON_DEFAULTS = dict(
    coin=0.0, unpaid=0.0, default_count=0.0, demand_cash=0.0,
    credit_trust=0.0, risk_weight=100.0, sour_amount=50.0, credit_term=3.0,
    buy_armed=0.0, repay_armed=0.0, hunger_level=0.0, satiety=5.0, bought=0.0)
SHOP_DEFAULTS = dict(
    good=0.0, price=1.0, open=0.0, open_scheduled=1.0, activity=0.0,
    input_good=0.0, produce_armed=0.0, restock_armed=0.0, coin=0.0, make_armed=0.0,
    make_count=0.0, out_qty=1.0,
    strength_req=0.0, stamina_cost=0.0)   # a recipe's physical demand (0/0 = light work; heavy trades override)


class BigvilleEconWorld(BigvilleTimeWorld):
    def __init__(self, **kw):
        super().__init__(**kw)
        for sid in ("bigville_econ_production", "bigville_econ_exchange",
                    "bigville_econ_supply", "bigville_econ_debt",
                    "bigville_econ_expectation", "bigville_econ_recipe",
                    "bigville_econ_spoil", "bigville_trade",         # two-sided trade (propose/accept)
                    "bigville_delegation_exec"):                     # a delegate fetches + delivers
            self.eng.load_seed_manifest(manifest_for(sid), None)   # be_print RETIRED into the recipe engine
        self._shops = {}          # name -> Shop nid
        self._stock = {}          # shop name -> stock Good nid
        self._input = {}          # shop name -> input Good nid
        self._recipe_in = {}      # recipe-shop name -> {kind: has_input Good nid}
        self._invent = {}         # (mover, good) -> Good nid  (buyer inventory)
        self._expects = {}        # (cust, shop) -> Expect nid

    # ---------------------------------------------------------------- ingest
    def make_trader(self, name, start, **econ):
        """A Mover that trades (keeper or buyer). Adds via R1 add_mover then seeds
        the econ attrs. Mechanical graph data."""
        m = self.add_mover(name, start)
        for k, v in ECON_DEFAULTS.items():
            self.eng.set_attr(m, k, float(v))
        for k, v in econ.items():
            self.eng.set_attr(m, k, float(v))
        return m

    def carry_weight(self, name):
        """The total weight a mover is carrying (sum of held goods' weight * qty) -- what slows a laden
        hauler down (mv_energy_budget subtracts it from the move budget)."""
        m = self._movers[name]
        total = 0.0
        for g in self.eng.neighbours(m, "has_good"):
            a = self.eng.node(g)["attrs"]
            total += float(a.get("weight", 1.0)) * float(a.get("qty", 0.0))
        return round(total, 4)

    def set_econ(self, name, **kw):
        m = self._movers[name]
        for k, v in kw.items():
            self.eng.set_attr(m, k, float(v))

    def set_skill(self, name, activity, level):
        """Attach a per-(agent,activity) competence (yields scale with it)."""
        m = self._movers[name]
        s = self.eng.add_node("Skill", {"activity": float(activity), "level": float(level)})
        self.eng.add_edge_unchecked(m, "has_skill", s)
        return s

    def _good_node(self, good, qty):
        """A Good pile carrying its catalog KIND + WEIGHT + spoilage state (self-describing), keyed by
        the code the rules compare. A good IS a catalog kind -- the code is just its integer handle.
        A perishable kind carries a freshness (condition) that be_spoil decays over the living clock."""
        kind = good_kind(good)
        spec = E.ITEMS.get(kind, {}) if kind else {}
        weight = float(spec.get("weight", 1.0))
        perishable = 1.0 if (kind and E.adjectival(kind) == "perishable") else 0.0
        return self.eng.add_node("Good", {"good": float(good), "qty": float(qty),
                                          "kind": kind, "weight": weight,
                                          # spoilage: a perishable pile has a freshness that decays over time
                                          "perishable": perishable, "condition": 1.0,
                                          "decay": E.decay_rate(kind) if kind else 0.0,
                                          "decay_epoch": 0.0, "now_epoch": 0.0})

    def add_catalog_shop(self, name, kind, *, cell, keeper, price, activity=0.0,
                         input_kind=None, stock=0, input_qty=0, supplier=None):
        """Set up a shop for ANY catalog good by NAME -- the code is derived from the catalog, so a good
        new to the living economy needs no new constant. `kind`/`input_kind` are catalog item names."""
        return self.add_shop(name, good=good_code(kind), price=price, cell=cell, keeper=keeper,
                             activity=activity, input_good=(good_code(input_kind) if input_kind else 0.0),
                             stock=stock, input_qty=input_qty, supplier=supplier)

    def add_recipe_shop(self, name, recipe_name, *, cell, keeper, price, activity=0.0,
                        stock=0, inputs=None, tools=None):
        """A shop that produces via a CATALOG RECIPE -- consuming ALL N of its inputs (be_meet_input,
        all-or-nothing) with every required TOOL working (be_recipe_done), then minting the output
        proportional to skill. `inputs` = {kind: initial_stock}; `tools` = {kind: condition} overrides
        for the recipe's tools (default working 1.0). The recipe (out + N inputs + Y tools + need_qtys)
        is READ from bigville_entities; adding a real multi-ingredient, tool-using trade is a catalog edit."""
        assert cell in self._cell_at, f"shop cell {cell} not walkable"
        recipe = next(r for r in E.RECIPES if r["name"] == recipe_name)
        out_kind = recipe["out"][0]
        inputs = inputs or {}
        tools = tools or {}
        str_req, sta_cost = E.recipe_exertion(recipe_name)   # the recipe's PHYSICAL demand (catalog data)
        attrs = dict(SHOP_DEFAULTS)
        attrs.update(good=good_code(out_kind), price=float(price), activity=float(activity),
                     out_qty=float(recipe["out"][1]),      # the recipe's batch size (yield = out_qty * skill)
                     strength_req=float(str_req), stamina_cost=float(sta_cost))   # keeper must be strong enough + spends stamina
        sh = self.eng.add_node("Shop", attrs)
        self.eng.add_edge_unchecked(sh, "at_cell", self._cell_at[cell])
        self.eng.add_edge_unchecked(sh, "kept_by", self._movers[keeper])
        st = self._good_node(good_code(out_kind), stock)
        self.eng.add_edge_unchecked(sh, "stocks", st)
        self._recipe_in[name] = {}
        for in_kind, need_qty in recipe["in"]:                # one has_input Good per recipe ingredient
            g = self._good_node(good_code(in_kind), inputs.get(in_kind, 0))   # carries kind/weight/condition
            self.eng.set_attr(g, "need_qty", float(need_qty)); self.eng.set_attr(g, "met", 0.0)
            self.eng.add_edge_unchecked(sh, "has_input", g)
            self._recipe_in[name][in_kind] = g
        self._recipe_tool = getattr(self, "_recipe_tool", {}); self._recipe_tool[name] = {}
        for tk in recipe.get("tools", []):                    # one has_tool Tool per required tool (Y tools)
            t = self.eng.add_node("Tool", {"kind": tk, "condition": float(tools.get(tk, 1.0)),
                                           "wear": float(E.ITEMS.get(tk, {}).get("wear_rate", 0.05)),
                                           "worn_at": 0.0})
            self.eng.add_edge_unchecked(sh, "has_tool", t)
            self._recipe_tool[name][tk] = t
        self._shops[name] = sh
        self._stock[name] = st
        return sh

    def recipe_tool_condition(self, shop, kind):
        return round(float(self.eng.node(self._recipe_tool[shop][kind])["attrs"]["condition"]), 4)

    def recipe_demand(self, shop):
        """A recipe shop's PHYSICAL demand: (strength_req, stamina_cost) -- what the keeper's body must meet."""
        a = self.eng.node(self._shops[shop])["attrs"]
        return (round(float(a.get("strength_req", 0.0)), 4), round(float(a.get("stamina_cost", 0.0)), 4))

    def keeper_stamina_reserve(self, keeper):
        """The keeper's current stamina RESERVE (endurance) -- depleted by work, restored by rest."""
        body = list(self.eng.neighbours(self._movers[keeper], "has_body"))[0]
        return round(float(self.eng.node(body)["attrs"].get("stamina_reserve", 1.0)), 4)

    def make(self, shop):
        """Arm one CATALOG-RECIPE production; be_meet_input consumes all N inputs (all-or-nothing) and
        be_recipe_done mints the output proportional to skill (distinct from produce()/print_run())."""
        self.eng.set_attr(self._shops[shop], "make_armed", 1.0)
        return self._run()

    def recipe_input_qty(self, shop, kind):
        return round(float(self.eng.node(self._recipe_in[shop][kind])["attrs"]["qty"]), 4)
    def set_input_condition(self, shop, kind, condition):
        """Set the quality/condition of one of a recipe shop's inputs (a worn wheel, stale flour) --
        the made good will be only as good as its weakest part (be_composite_quality)."""
        self.eng.set_attr(self._recipe_in[shop][kind], "condition", float(condition))
    def made_quality(self, shop):
        """The quality (condition) of the good a shop has made -- capped by its weakest input part."""
        return round(float(self.eng.node(self._stock[shop])["attrs"].get("condition", 1.0)), 4)

    def stock_kind(self, shop):
        """The catalog kind a shop stocks (read off the Good node)."""
        return self.eng.node(self._stock[shop])["attrs"].get("kind", "")
    def stock_weight(self, shop):
        return round(float(self.eng.node(self._stock[shop])["attrs"].get("weight", 1.0)), 4)
    def stock_qty(self, shop):
        return round(float(self.eng.node(self._stock[shop])["attrs"]["qty"]), 4)
    def stock_condition(self, shop):
        """The freshness of a shop's stock (1.0 fresh -> 0.0 rotted; 1.0 for durable goods). A world
        fact; what the seller CHARGES for stale stock is the seller's own pricing decision, not this."""
        return round(float(self.eng.node(self._stock[shop])["attrs"].get("condition", 1.0)), 4)

    def add_shop(self, name, *, good, price, cell, keeper, activity=0.0,
                 input_good=0.0, stock=0, input_qty=0, supplier=None):
        """A shop/workplace at a walkable `cell`, kept by mover `keeper`. Sells
        `good` at `price`, produces it from `input_good` using the keeper's skill,
        and (optionally) restocks that input UP-CHAIN from `supplier`'s shop."""
        assert cell in self._cell_at, f"shop cell {cell} not walkable"
        attrs = dict(SHOP_DEFAULTS)
        attrs.update(good=float(good), price=float(price), activity=float(activity),
                     input_good=float(input_good))
        sh = self.eng.add_node("Shop", attrs)
        self.eng.add_edge_unchecked(sh, "at_cell", self._cell_at[cell])
        self.eng.add_edge_unchecked(sh, "kept_by", self._movers[keeper])
        st = self._good_node(good, stock)
        self.eng.add_edge_unchecked(sh, "stocks", st)
        ig = self._good_node(input_good, input_qty)
        self.eng.set_attr(ig, "need_qty", 1.0)      # consume ONE input per batch (the classic 1-input shop
        self.eng.set_attr(ig, "met", 0.0)           # is the N=1 case of the unified recipe engine; yield=skill)
        self.eng.add_edge_unchecked(sh, "has_input", ig)
        self._shops[name] = sh
        self._stock[name] = st
        self._input[name] = ig
        if supplier is not None:
            self.eng.add_edge_unchecked(sh, "supplied_by", self._shops[supplier])
        return sh

    def add_printshop(self, name, *, cell, keeper, press_condition=1.0, paper_qty=5, ink_qty=5, price=2):
        """A printer's workplace. RETIRED be_print: the printshop is now just a RECIPE shop for
        `print_newspaper` -- the printing_press is an ordinary recipe TOOL (gated + worn by the general
        engine), and the run consumes BOTH paper and ink. The whole newspaper chain now rides the same
        N-input + Y-tool production as every other trade -- one engine."""
        return self.add_recipe_shop(name, "print_newspaper", cell=cell, keeper=keeper, price=price,
                                    activity=PRINTING, inputs={"paper": paper_qty, "ink": ink_qty},
                                    tools={"printing_press": press_condition})

    def print_run(self, shop):
        """Arm one print batch (alias for make() -- the printshop is a recipe shop now)."""
        return self.make(shop)

    def newspaper_stock(self, shop):
        return self.stock_qty(shop)
    def press_condition(self, shop):
        return self.recipe_tool_condition(shop, "printing_press")

    def sever_supply(self, name, supplier):
        """Remove a `supplied_by` edge (the sever control: propagation is
        edge-mediated). Mechanical."""
        self.eng.remove_edge_unchecked(self._shops[name], "supplied_by",
                                       self._shops[supplier])

    def give_good(self, name, good, qty=0):
        """Ensure a mover holds an inventory Good{good} (created empty for goods it
        may buy; a buy increments it). Mechanical."""
        key = (name, float(good))
        g = self._invent.get(key)
        if g is None:
            g = self._good_node(good, qty)
            self.eng.add_edge_unchecked(self._movers[name], "has_good", g)
            self._invent[key] = g
        else:
            self.eng.set_attr(g, "qty", float(qty))
        return g

    def expect_source(self, agent, good, holder, *, confidence=1.0):
        """The agent EXPECTS `holder` (a person/shop keeper) to have `good` -- a held belief that drives
        generic provisioning planning (NOT co-location). It also ensures the agent holds a receiving slot
        for the good. Mechanical graph data (a real expectation; could be learned from experience)."""
        a = self._movers[agent]
        exp = self.eng.add_node("Expect", {"good": float(good), "avail": 1.0, "confidence": float(confidence)})
        self.eng.add_edge_unchecked(a, "expects", exp)
        self.eng.add_edge_unchecked(exp, "source", self._movers[holder])
        self.give_good(agent, good, 0)                 # a slot to receive the good into
        self.eng.set_attr(a, "provision_good", float(good))   # the agent provisions the good it expects to get
        return exp

    def form_household(self, members, home, *, horizon=2, ration=1, good=None, provider=None):
        """Make `members` a HOUSEHOLD living at `home`, sharing ONE food need and ONE store. The household
        provisions once (one member volunteers to fetch, carries it home, everyone eats from the shared
        store) -- so household-mates don't each set out for food. Each member gets a transit slot; give them
        expectations of a source (expect_source) so a volunteer knows where to go."""
        good = float(good) if good is not None else float(BREAD)
        hh = self.eng.add_node("Household", {"plan_horizon": float(horizon), "daily_ration": float(ration),
                                             "provision_good": good})
        self.eng.add_edge_unchecked(hh, "is_at", self._cell_at[home])
        store = self._good_node(good, 0)                     # the shared store the household holds
        self.eng.add_edge_unchecked(hh, "has_good", store)
        for nm in members:
            self.eng.add_edge_unchecked(hh, "has_member", self._movers[nm])
            self.eng.set_attr(self._movers[nm], "in_household", 1.0)   # -> no individual provisioning
            self.give_good(nm, good, 0)                       # a slot to carry the good home in
        if provider is not None:                              # a FIXED provider role -- this member does the errands
            self.eng.add_edge_unchecked(hh, "provides_via", self._movers[provider])
        self._households = getattr(self, "_households", {}); self._households[tuple(members)] = (hh, store)
        return hh

    def household_store(self, members):
        """How much food the household holds in its shared store."""
        _, store = self._households[tuple(members)]
        return round(float(self.eng.node(store)["attrs"].get("qty", 0.0)), 4)

    def set_provision_good(self, name, good):
        """Set the good an agent provisions/eats (what a delegated fetch targets), and ensure it holds a slot
        to RECEIVE it into. Use when the agent provisions a good it has no expectation-source of its own for."""
        self.eng.set_attr(self._movers[name], "provision_good", float(good))
        self.give_good(name, good, 0)

    def stock_person(self, name, good, qty, *, sell_price=1, willing=True):
        """Make a person HOLD goods to sell (has_good) with an asking price -- a seller you can trade with
        wherever they are (the baker in the street), not a shop you must stand in. Price set by the seller."""
        self.give_good(name, good, qty)
        self.eng.set_attr(self._movers[name], "sell_price", float(sell_price))
        self.eng.set_attr(self._movers[name], "sell_willing", 1.0 if willing else 0.0)

    def offer_status(self, agent):
        """The status of the agent's most recent trade offer: 0 pending, 1 accepted, -1 unmet (surprised),
        -2 declined. Glass-box read-off of the two-sided trade."""
        offs = list(self.eng.neighbours(self._movers[agent], "offers"))
        return int(round(float(self.eng.node(offs[-1])["attrs"].get("status", 0.0)))) if offs else None

    def was_surprised(self, agent):
        return len(list(self.eng.neighbours(self._movers[agent], "surprised"))) > 0

    def add_expectation(self, cust, shop, open_due=1):
        """The town HOLDS 'shop opens on schedule' as an Expect the customer holds."""
        e = self.eng.add_node("Expect", {"open_due": float(open_due), "surprised_done": 0.0})
        self.eng.add_edge_unchecked(self._movers[cust], "expects", e)
        self.eng.add_edge_unchecked(e, "about_shop", self._shops[shop])
        self._expects[(cust, shop)] = e
        return e

    def set_open_due(self, cust, shop, val):
        self.eng.set_attr(self._expects[(cust, shop)], "open_due", float(val))

    # ------------------------------------------------- rule-driven phases
    def _run(self):
        n = self.eng.run_rules(10_000_000)
        self._cost_steps += n
        return n

    def refresh_open(self):
        """Derive every shop's `open` flag (be_shop_open / be_shop_shut) from the
        R3 clock fact + keeper wakefulness. Pure rule fixpoint."""
        return self._run()

    def set_hours(self, open_scheduled):
        """World fact: business hours on/off, written onto every shop (mechanical,
        like R3's `lateness`). The OPEN decision is the rule, not this."""
        for sh in self._shops.values():
            self.eng.set_attr(sh, "open_scheduled", float(open_scheduled))

    def produce(self, shop):
        """Arm one production step -- routed through the UNIFIED recipe engine (be_recipe_done); the old
        be_produce is retired. A 1-input classic shop is the N=1 case: consume 1 input (need_qty), yield =
        the keeper's skill (out_qty 1 * skill), gated by the keeper being CONSCIOUS -- using the craft."""
        self.eng.set_attr(self._shops[shop], "make_armed", 1.0)
        return self._run()

    def buy(self, buyer):
        """Arm one purchase; be_exchange (coin) or be_credit (short+trust) decides. A purchase moves
        coin<->good into the bag -- it does NOT feed you (buying and eating are different acts)."""
        self.eng.set_attr(self._movers[buyer], "buy_armed", 1.0)
        return self._run()

    def eat(self, name, good):
        """EAT one unit of a good the mover HOLDS -- this is what feeds you (relieves hunger), NOT the
        purchase. Mechanical: consume one held unit (you can only eat what you have) + mint a Meal whose
        `feeds` is the eater's filling capacity (satiety); bd_meal_feeds then drops hunger_level. Returns
        the new hunger. A hungry agent DECIDING to eat is the drive wiring (deferred)."""
        m = self._movers[name]
        g = self._invent.get((name, float(good)))
        held = float(self.eng.node(g)["attrs"].get("qty", 0.0)) if g is not None else 0.0
        if held < 1.0:
            return self.hunger_of(name)                 # nothing held -> nothing eaten (a world-fact precondition)
        self.eng.set_attr(g, "qty", held - 1.0)         # consume one unit
        feeds = float(self.eng.node(m)["attrs"].get("satiety", 5.0))   # how filling a meal is for this body
        meal = self.eng.add_node("Meal", {"feeds": feeds, "fed_done": 0.0})
        self.eng.add_edge_unchecked(m, "ate", meal)
        self._run()                                     # bd_meal_feeds relieves hunger
        return self.hunger_of(name)

    def restock(self, shop):
        """Arm one up-chain restock; be_restock (cash) or be_restock_credit decides."""
        self.eng.set_attr(self._shops[shop], "restock_armed", 1.0)
        return self._run()

    def repay(self, debtor):
        """Arm one repayment (the debtor-pays control)."""
        self.eng.set_attr(self._movers[debtor], "repay_armed", 1.0)
        return self._run()

    def tick_spoilage(self, days=1):
        """A day passes for the larder: publish the clock onto every held Good (mechanical, like
        tick_obligations) so be_spoil can decay perishable goods once per day at their catalog rate."""
        for _ in range(int(days)):
            self._spoil_epoch = getattr(self, "_spoil_epoch", 0) + 1
            for g in self.eng.nodes("Good"):
                if float(self.eng.node(g)["attrs"].get("perishable", 0.0)) > 0.0:
                    self.eng.set_attr(g, "now_epoch", float(self._spoil_epoch))
            self._run()
        return self._spoil_epoch

    def good_condition(self, name, kind):
        """The freshness of a perishable good a mover holds (1.0 fresh -> 0.0 rotted)."""
        g = self._invent[(name, float(good_code(kind)))]
        return round(float(self.eng.node(g)["attrs"].get("condition", 1.0)), 4)
    def good_held_qty(self, name, kind):
        g = self._invent[(name, float(good_code(kind)))]
        return round(float(self.eng.node(g)["attrs"]["qty"]), 4)

    def tick_obligations(self):
        """Publish the world epoch onto every Owe (mechanical, like `lateness`) so
        be_default can compare now_epoch > due_epoch, then run the fixpoint."""
        for o in self.eng.nodes("Owe"):
            self.eng.set_attr(o, "now_epoch", float(self.world_epoch))
        return self._run()

    def attach_creditor_affect(self, keeper, **kw):
        """Give a keeper an AffectiveState so a default can flip it (reuses the R3
        204000/239000 channel + concern_mag/concern_drop)."""
        return self.attach_affect(keeper, **kw)

    # ------------------------------------------------- glass-box read-offs
    def coin_of(self, name):
        return float(self.eng.node(self._movers[name])["attrs"].get("coin", 0.0))

    def hunger_of(self, name):
        return float(self.eng.node(self._movers[name])["attrs"].get("hunger_level", 0.0))

    def bought_of(self, name):
        return int(self.eng.node(self._movers[name])["attrs"].get("bought", 0.0))

    def default_count_of(self, name):
        return int(self.eng.node(self._movers[name])["attrs"].get("default_count", 0.0))

    def unpaid_of(self, name):
        return float(self.eng.node(self._movers[name])["attrs"].get("unpaid", 0.0))

    def credit_trust_of(self, name):
        return float(self.eng.node(self._movers[name])["attrs"].get("credit_trust", 0.0))

    def demand_cash_of(self, name):
        return int(self.eng.node(self._movers[name])["attrs"].get("demand_cash", 0.0))

    def inventory_of(self, name, good):
        g = self._invent.get((name, float(good)))
        return float(self.eng.node(g)["attrs"].get("qty", 0.0)) if g is not None else 0.0

    def stock_of(self, shop):
        return float(self.eng.node(self._stock[shop])["attrs"].get("qty", 0.0))

    def input_of(self, shop):
        return float(self.eng.node(self._input[shop])["attrs"].get("qty", 0.0))

    def shop_open(self, shop):
        return int(self.eng.node(self._shops[shop])["attrs"].get("open", 0.0))

    def owes_of(self, name):
        """List of (amount, due_epoch, paid, defaulted) for a mover's obligations."""
        out = []
        for o in self.eng.neighbours(self._movers[name], "owes"):
            a = self.eng.node(o)["attrs"]
            out.append(dict(amount=float(a.get("amount", 0.0)),
                            due_epoch=float(a.get("due_epoch", 0.0)),
                            paid=int(a.get("paid", 0.0)),
                            defaulted=int(a.get("defaulted", 0.0))))
        return out

    def surprise_count(self, name=None):
        if name is not None:
            return len(list(self.eng.neighbours(self._movers[name], "surprised")))
        return len(list(self.eng.nodes("Surprise")))
