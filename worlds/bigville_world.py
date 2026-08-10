"""BigvilleWorld -- bigville R72/R76 (blocks 390000, 394000): the canonical, data-driven, FLOAT-FREE
world, on the ONE general action engine.

Every entity comes from the ONE data file (domains/bigville_entities.py): items, containers,
recipes, buildings. There is now a SINGLE making engine -- the generic action (bigville_action_
general): perform an action on N things with Y tools, optionally timed, producing a bulk material or
a discrete tool (quality = maker's skill) that wears. A recipe is just an action. Commodities are
PHYSICAL Stock piles, never store floats. Adding a tool/material/recipe (any inputs, any tools) is a
DATA EDIT, no code change.
"""
from __future__ import annotations

import math
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import substrate_rs                                     # noqa: E402
from substrate.seed_loader import manifest_for          # noqa: E402
from domains import bigville_entities as E               # noqa: E402

MINUTES_PER_TICK = 15.0


class BigvilleWorld:
    def __init__(self):
        self.eng = substrate_rs.Substrate()._inner
        self.eng.load_seed_manifest(manifest_for("bigville_action_general"), None)   # the ONE making engine
        self.eng.load_seed_manifest(manifest_for("bigville_action_decide"), None)    # observed-demand decision
        self.eng.load_seed_manifest(manifest_for("bigville_action_container"), None) # containers + lock/key
        self.eng.load_seed_manifest(manifest_for("bigville_action_animal"), None)    # animals eat / starve
        self.eng.load_seed_manifest(manifest_for("bigville_action_merchant"), None)  # a merchant delivers goods
        self.eng.load_seed_manifest(manifest_for("bigville_action_life"), None)      # crops grow; residents eat
        self.eng.load_seed_manifest(manifest_for("bigville_action_decay"), None)     # wear over time + spoilage
        self.eng.load_seed_manifest(manifest_for("bigville_action_clothing"), None)  # clothes: dyed, worn, protective
        self.eng.load_seed_manifest(manifest_for("bigville_action_skill"), None)     # apprenticeship: skill grows under a master
        self._town = self.eng.add_node("Town", {"name": "Bigville", "clock": 0.0, "period": 0.0,
                                                "season": "spring", "observed_harvest": 0.0,
                                                "observed_building": 0.0, "observed_storage": 0.0,
                                                "cold": 0.0, "wet": 0.0})   # the weather clothes protect against
        self._store = self.eng.add_node("Store", {"name": "store"})           # holds Stock NODES, no commodity floats
        self.eng.add_edge_unchecked(self._town, "has_store", self._store)
        self._stock = {}; self._actors = {}; self._items = {}; self._actions = {}; self._tools = {}
        self._item_specs = dict(E.ITEMS)   # runtime item registry (data + runtime-added)
        self._tool_kinds = set()
        self.set_stock("none", 1e9)
        for kind, spec in E.ITEMS.items():
            self._install_item(kind, spec)
        for r in E.RECIPES:
            self._install_recipe(r)
        for tk in self._tool_kinds:                     # provide the instruments the recipes call for
            t = self.eng.add_node("Tool", {"kind": tk, "condition": 1.0, "wear": 0.02})
            self.eng.add_edge_unchecked(self._town, "has_tool", t)
            self._tools[tk] = t
        self._places = {}; self._containers = {}
        for kind, spec in E.BUILDINGS.items():           # install the town's buildings from the data
            self._install_building(kind, spec)

    def _run(self):
        for _ in range(6):
            self.eng.force_all_dirty(); self.eng.run_rules(1000000)

    # ---------------------------------------------------- install the data as graph nodes
    def _install_item(self, kind, spec):
        n = self.eng.add_node("ItemSpec", {"kind": kind, **{k: (float(v) if not isinstance(v, bool)
                                                               and isinstance(v, (int, float)) else v)
                                                             for k, v in spec.items()}})
        self.eng.set_attr(n, "scarcity", E.scarcity(kind))   # the raw material's general scarcity (data)
        self.eng.add_edge_unchecked(self._town, "has_itemspec", n)
        self._items[kind] = n
        return n

    def _install_recipe(self, r):
        out_kind, out_qty = r["out"]
        out = self._item_specs.get(out_kind, {})
        # anything that is not a bulk material (tool/component/good/furniture) is a discrete item
        discrete = out.get("class", "material") != "material" and out.get("discrete", True)
        attrs = {"name": r["name"], "requires": r.get("requires", ""), "out_kind": out_kind,
                 "out_qty": float(out_qty), "out_discrete": 1.0 if discrete else 0.0,
                 "difficulty": float(r.get("difficulty", 1.0)), "time_minutes": float(r.get("time_minutes", 0.0)),
                 "min_skill": E.min_skill(r["name"]),   # the skill FLOOR to attempt it (apprenticeship)
                 "common": 0.0 if r.get("common") is False else 1.0}   # commonly known by the trade, or must be learned
        if discrete:                                    # carry the item's tool data onto the action
            attrs.update(verb=out.get("verb", ""), base_mult=float(out.get("base_mult", 1.0)),
                         wear_rate=float(out.get("wear_rate", 0.0)), decay=E.decay_rate(out_kind))
        # carry the output's DEMAND data onto the action (for the pd_decide collapse)
        attrs.update(out_driver=out.get("demand_driver", ""),
                     out_demand_weight=float(out.get("demand_weight", 0.0)),
                     out_base_demand=float(out.get("base_demand", 0.0)))
        asp = self.eng.add_node("ActionSpec", attrs)
        self.eng.add_edge_unchecked(self._town, "has_actionspec", asp)
        for kind, qty in r["in"]:                       # N input needs (data)
            icls = self._item_specs.get(kind, {}).get("class")
            is_item = 1.0 if icls not in (None, "material") and self._item_specs.get(kind, {}).get("discrete", True) else 0.0
            need = self.eng.add_node("Need", {"kind": kind, "qty": float(qty), "is_item": is_item})
            self.eng.add_edge_unchecked(asp, "in_need", need)
        for tk in r.get("tools", []):                   # Y tool uses (data)
            tu = self.eng.add_node("ToolUse", {"kind": tk})
            self.eng.add_edge_unchecked(asp, "in_tool", tu)
            self._tool_kinds.add(tk)
        if not discrete:
            self.set_stock(out_kind, self.qty(out_kind))
        self._actions[r["name"]] = asp
        return asp

    def add_item(self, kind, spec):
        """Add a NEW item as pure data (a dict) -- no code change."""
        self._item_specs[kind] = spec
        return self._install_item(kind, spec)

    def add_recipe(self, r):
        """Add a NEW recipe/action (any inputs, any tools) as pure data (a dict) -- no code change."""
        asp = self._install_recipe(r)
        for tk in r.get("tools", []):                   # provide any newly-required instrument
            if tk not in self._tools:
                t = self.eng.add_node("Tool", {"kind": tk, "condition": 1.0, "wear": 0.02})
                self.eng.add_edge_unchecked(self._town, "has_tool", t)
                self._tools[tk] = t
        if r.get("common") is not False:                # a new COMMON recipe is common knowledge for its trade
            for name, a in self._actors.items():
                if self.eng.node(a)["attrs"].get("role") == r.get("requires"):
                    self.eng.add_edge_unchecked(a, "knows", asp)
        return asp

    # ---------------------------------------------------- physical stock (piles), NOT floats
    def _phys(self, kind):
        """The physical properties of a commodity, from the item data (defaults 1/1, not a fluid)."""
        spec = self._item_specs.get(kind, {})
        return (float(spec.get("weight", 1.0)), float(spec.get("volume", 1.0)),
                1.0 if spec.get("fluid") else 0.0)

    def set_stock(self, kind, qty):
        w, v, fl = self._phys(kind)
        food = 1.0 if self._item_specs.get(kind, {}).get("food") else 0.0
        perishable = 1.0 if E.adjectival(kind) == "perishable" else 0.0
        if kind in self._stock:
            self.eng.set_attr(self._stock[kind], "qty", float(qty))
        else:
            colour = self._item_specs.get(kind, {}).get("colour", "")   # a dye names a colour (madder->red)
            s = self.eng.add_node("Stock", {"kind": kind, "qty": float(qty),   # a first-class physical pile
                                            "weight": w, "volume": v, "fluid": fl, "food": food, "colour": colour,
                                            # spoilage: a perishable pile has a freshness that decays over time
                                            "perishable": perishable, "condition": 1.0,
                                            "decay": E.decay_rate(kind), "decay_epoch": 0.0})
            self.eng.add_edge_unchecked(self._store, "stock", s)
            self._stock[kind] = s
        return self._stock[kind]

    # ---------------------------------------------------- condition adjectives (wear + decay stages)
    def tool_adjective(self, tool):
        """The adjective describing a discrete tool at its current condition (pristine/worn/rusty/...)."""
        a = self.eng.node(tool)["attrs"]
        return E.adjective(a["kind"], a["condition"])

    def stock_adjective(self, kind):
        """The adjective describing a perishable stock (fresh/stale/rotten/putrid)."""
        return E.adjective(kind, self.eng.node(self._stock[kind])["attrs"].get("condition", 1.0))

    def stock_condition(self, kind):
        return round(float(self.eng.node(self._stock[kind])["attrs"].get("condition", 1.0)), 4)
    def stored_condition(self, container, kind):
        return round(float(self.eng.node(self._containers[container][1][kind])["attrs"].get("condition", 1.0)), 4)
    def stored_adjective(self, container, kind):
        return E.adjective(kind, self.eng.node(self._containers[container][1][kind])["attrs"].get("condition", 1.0))
    def item_wear_rate(self, kind): return float(self._item_specs.get(kind, {}).get("wear_rate", 0.0))
    def item_decay_rate(self, kind): return E.decay_rate(kind)
    def adjectival_class(self, kind): return E.adjectival(kind)

    # ------------------------------- BACKEND value read-offs (for the operator; NOT an agent input)
    # scarcity is a raw-material fact a seller knows; reference_value is an analyst baseline the human
    # holds the market's discovered price against -- the agents price for themselves, the market clears.
    def scarcity(self, kind): return E.scarcity(kind)
    def reference_value(self, kind): return E.reference_value(kind)
    def material_value(self, kind): return E.material_value(kind)
    def embodied_labour(self, kind): return E.embodied_labour(kind)

    # ---------------------------------------------------- buildings (from the BUILDINGS data)
    def _install_building(self, kind, spec):
        p = self.eng.add_node("Place", {"kind": kind, "name": kind.capitalize(),
                                        "sheltered": 1.0 if spec.get("sheltered") else 0.0})
        self.eng.add_edge_unchecked(self._town, "has_place", p)
        staff = self.eng.add_node("Agent", {"name": f"{kind}_staff", "role": spec.get("staff_role", "")})
        self.eng.add_edge_unchecked(p, "staffed_by", staff)
        if spec.get("provides"):                          # town -has_<provides>-> the staff (a maker role)
            self.eng.add_edge_unchecked(self._town, f"has_{spec['provides']}", staff)
        for room in spec.get("rooms", []):
            r = self.eng.add_node("Room", {"kind": room})
            self.eng.add_edge_unchecked(p, "has_room", r)
        self._places[kind] = p
        return p

    def building(self, kind): return self._places.get(kind)
    def building_provides(self, kind):
        staff = list(self.eng.neighbours(self._places[kind], "staffed_by"))
        return self.eng.node(staff[0])["attrs"]["role"] if staff else None
    def building_sheltered(self, kind):
        return float(self.eng.node(self._places[kind])["attrs"]["sheltered"]) == 1.0
    def buildings(self): return set(self._places)

    # ---------------------------------------------------- containers (volume capacity, many kinds, fluids)
    def _vessel_data(self, kind):
        """Capacity, watertightness, and decay_factor of a vessel kind, from the data (or CONTAINERS)."""
        spec = self._item_specs.get(kind, {}) or E.CONTAINERS.get(kind, {})
        return (float(spec.get("capacity", 10.0)), 1.0 if spec.get("watertight") else 0.0,
                float(spec.get("decay_factor", 1.0)))

    def _wire_container(self, name, node, kind, holds, lock_id, locked, max_load=None, capacity=None):
        cap, wt, df = self._vessel_data(kind)
        if capacity is not None:
            cap = float(capacity)
        ml = max_load if max_load is not None else float(self._item_specs.get(kind, {}).get("max_load", 1e9))
        for k, v in (("capacity", cap), ("watertight", wt), ("decay_factor", df), ("max_load", ml),
                     ("lock_id", float(lock_id)), ("locked", 1.0 if locked else 0.0)):
            self.eng.set_attr(node, k, v)
        self.eng.add_edge_unchecked(self._town, "has_container", node)
        inners = {}
        for hk in ([holds] if isinstance(holds, str) else holds):   # an inner Stock per kind it will hold
            w, vol, fl = self._phys(hk)
            per = 1.0 if E.adjectival(hk) == "perishable" else 0.0
            inner = self.eng.add_node("Stock", {"kind": hk, "qty": 0.0, "weight": w, "volume": vol, "fluid": fl,
                                                "perishable": per, "condition": 1.0, "decay": E.decay_rate(hk),
                                                "decay_epoch": 0.0})
            self.eng.add_edge_unchecked(node, "contains", inner)
            inners[hk] = inner
        self._containers[name] = (node, inners)
        return node

    def add_container(self, name, *, kind="barrel", holds, lock_id=0.0, locked=False):
        c = self.eng.add_node("Container", {"kind": kind, "name": name})
        return self._wire_container(name, c, kind, holds, lock_id, locked)

    def add_carrier(self, name, *, holds, max_load, capacity=1e9):
        """A weight-bounded CARRIER -- a person's carry-bag (small max_load) or a cart (large). WEIGHT
        drives what fits: a person carries little, a horse-drawn cart carries a lot."""
        c = self.eng.add_node("Carrier", {"kind": "carrier", "name": name})
        return self._wire_container(name, c, "carrier", holds, 0.0, False,
                                    max_load=float(max_load), capacity=float(capacity))

    def max_load(self, carrier): return round(float(self.eng.node(self._containers[carrier][0])["attrs"]["max_load"]), 4)

    # ---------------------------------------------------- animals (from the ANIMALS data) + carts/horses
    def add_animal(self, name, species):
        spec = E.ANIMALS[species]
        a = self.eng.add_node("Animal", {"name": name, "species": species, "role": spec.get("role", ""),
                                         "pull": float(spec.get("pull", 0.0)), "alive": 1.0,
                                         "matures": float(spec.get("matures", 0)), "lifespan": float(spec.get("lifespan", 0)),
                                         # feeding state (data-driven): what it eats, how much, and its starve limit
                                         "hunger": 0.0, "hunger_epoch": 0.0, "eats": spec.get("eats", ""),
                                         "ration": float(spec.get("ration", 1)), "starve_limit": float(spec.get("starve_limit", 3))})
        self.eng.add_edge_unchecked(self._town, "has_animal", a)
        self._animals = getattr(self, "_animals", {}); self._animals[name] = a
        return a

    def pass_period(self, n=1):
        """A period passes: crops thirst / grow (if watered) / wilt; animals and residents get hungrier,
        eat if fed, or starve."""
        for _ in range(int(n)):
            self.eng.set_attr(self._town, "period", float(self.eng.node(self._town)["attrs"]["period"]) + 1.0)
            self._run()

    # ---------------------------------------------------- crops (seed -> grow -> harvest)
    def season(self): return self.eng.node(self._town)["attrs"]["season"]

    def set_season(self, season):
        """Turn the year to a season (spring/summer/autumn/winter) -- crops are sown in their season."""
        self.eng.set_attr(self._town, "season", season)

    def sow(self, sower, crop):
        """Sow a crop from its SEED -- but only IN ITS SEASON (you cannot sow a spring crop in autumn).
        Consumes one seed and plants a growing Crop (which then needs water each period, or it wilts).
        Returns None if it is the wrong season."""
        spec = E.CROPS[crop]
        if spec["season"] != self.season():
            return None                                     # out of season -- nothing is sown
        self.set_stock(spec["seed"], max(0.0, self.qty(spec["seed"]) - 1.0))    # a seed is used
        c = self.eng.add_node("Crop", {"crop": crop, "age": 0.0, "thirst": 0.0, "thirst_epoch": 0.0,
                                       "alive": 1.0, "water": float(spec["water"]), "wilt": float(spec["wilt"]),
                                       "grow_periods": float(spec["grow_periods"]), "harvest": spec["harvest"],
                                       "yield": float(spec["yield"])})
        self.eng.add_edge_unchecked(self._town, "has_crop", c)
        self._crops = getattr(self, "_crops", {}); self._crops[len(self._crops)] = c
        return c

    def harvest_crop(self, crop_node):
        """Harvest a MATURE living crop -> its yield of the product enters the store; the crop is done."""
        a = self.eng.node(crop_node)["attrs"]
        if float(a["alive"]) == 1.0 and float(a["age"]) >= float(a["grow_periods"]):
            self.set_stock(a["harvest"], self.qty(a["harvest"]) + float(a["yield"]))
            self.eng.set_attr(crop_node, "alive", 0.0)
            self.eng.remove_edge_unchecked(self._town, "has_crop", crop_node)
            return float(a["yield"])
        return 0.0

    def crop_age(self, crop_node): return round(float(self.eng.node(crop_node)["attrs"]["age"]), 4)
    def crop_alive(self, crop_node): return float(self.eng.node(crop_node)["attrs"]["alive"]) == 1.0
    def crop_mature(self, crop_node):
        a = self.eng.node(crop_node)["attrs"]
        return float(a["alive"]) == 1.0 and float(a["age"]) >= float(a["grow_periods"])
    def hunger(self, actor): return round(float(self.eng.node(self._actors[actor])["attrs"]["hunger"]), 4)
    def is_alive(self, actor): return float(self.eng.node(self._actors[actor])["attrs"]["alive"]) == 1.0

    def import_good(self, kind, qty):
        """Acquire an IMPORTED good from outside bigville (ink/paper/dye/salt). Only goods marked
        imported in the data can be imported -- the rest must be made locally."""
        assert self._item_specs.get(kind, {}).get("imported"), f"{kind} is not an imported good"
        return self.set_stock(kind, self.qty(kind) + float(qty))

    def animal_hunger(self, name): return round(float(self.eng.node(self._animals[name])["attrs"]["hunger"]), 4)
    def animal_alive(self, name): return float(self.eng.node(self._animals[name])["attrs"]["alive"]) == 1.0
    def is_imported(self, kind): return bool(self._item_specs.get(kind, {}).get("imported"))

    def give_product(self, animal, product):
        """The animal yields one of its products (a cow's milk, a chicken's eggs) into the store."""
        spec = E.ANIMALS[self.eng.node(self._animals[animal])["attrs"]["species"]]
        yield_ = float(spec.get("gives", {}).get(product, 0.0))
        if yield_ > 0:
            self.set_stock(product, self.qty(product) + yield_)
        return yield_

    def hitch(self, horse, cart):
        """Hitch a draught animal to a cart -- the cart can now haul up to the animal's PULL."""
        pull = float(self.eng.node(self._animals[horse])["attrs"]["pull"])
        self.eng.set_attr(self._containers[cart][0], "max_load", pull)
        self.eng.add_edge_unchecked(self._animals[horse], "pulls", self._containers[cart][0])
        return pull

    _SLAUGHTER = {"pork", "beef", "mutton", "poultry", "fish", "ham", "bacon", "sausage", "hide"}

    def butcher(self, butcher, animal):
        """BUTCHERY is a skill: a butcher turns a (living) animal into its meat + hide (the on-death
        products from ANIMALS), killing it. Only a butcher can do it."""
        assert self.eng.node(self._actors[butcher])["attrs"].get("role") == "butcher", f"{butcher} is not a butcher"
        an = self._animals[animal]
        if float(self.eng.node(an)["attrs"]["alive"]) != 1.0:
            return {}
        got = {}
        for product, qty in E.ANIMALS[self.eng.node(an)["attrs"]["species"]]["gives"].items():
            if product in self._SLAUGHTER:
                self.set_stock(product, self.qty(product) + float(qty)); got[product] = float(qty)
        self.eng.set_attr(an, "alive", 0.0)
        return got

    # ---------------------------------------------------- a merchant delivers imported goods
    def add_merchant(self, name, *, brings=None):
        m = self.eng.add_node("Merchant", {"name": name})
        self.eng.add_edge_unchecked(self._town, "has_merchant", m)
        self._merchants = getattr(self, "_merchants", {}); self._merchants[name] = m
        for good, qty in (brings or {}).items():
            self.set_stock(good, self.qty(good))                    # ensure a store pile exists to receive it
            g = self.eng.add_node("Stock", {"kind": good, "qty": float(qty)})
            self.eng.add_edge_unchecked(m, "carries", g)
        return m

    def deliver(self, merchant):
        """The merchant unloads what he carries into the store (mc_deliver)."""
        self._run()

    # ---------------------------------------------------- books (physical, record a recipe, read to learn)
    def write_in_book(self, author, book, recipe):
        """An author who KNOWS a recipe writes it into a made book (a physical record with weight).
        Refused (None) if the author cannot write (below functional literacy)."""
        assert self.knows(author, recipe), f"{author} does not know {recipe}"
        if not self._can_read(author):
            return None
        self.eng.set_attr(book, "recipe", recipe)
        self.eng.add_edge_unchecked(self._actors[author], "wrote", book)
        return book

    def read_book(self, reader, book):
        """Read a book -- a LITERATE reader learns the recipe written in it. Refused (None, no learning)
        if the reader cannot read (below functional literacy)."""
        if not self._can_read(reader):
            return None
        recipe = self.eng.node(book)["attrs"].get("recipe", "")
        if recipe:
            self.eng.add_edge_unchecked(self._actors[reader], "knows", self._actions[recipe])
        return recipe

    def book_recipe(self, book): return self.eng.node(book)["attrs"].get("recipe", "")

    def animal_role(self, animal): return self.eng.node(self._animals[animal])["attrs"]["role"]
    def animal_gives(self, species): return dict(E.ANIMALS[species]["gives"])
    def animal_pull(self, animal): return round(float(self.eng.node(self._animals[animal])["attrs"]["pull"]), 4)

    def use_as_store(self, name, item, holds, *, lock_id=0.0, locked=False):
        """Press a MADE container-item (a cooper's barrel, a joiner's chest) into service as a real
        container -- the SAME node gains a capacity (from the item data) + an inner Stock + a
        has_container edge, so the container rules fill it. A made barrel IS a container."""
        kind = self.tool_kind(item)
        spec = self._item_specs.get(kind, {})
        assert spec.get("container"), f"{kind} is not a container item"
        return self._wire_container(name, item, kind, holds, lock_id, locked)

    def give_key(self, actor, opens):
        k = self.eng.add_node("Key", {"opens": float(opens)})
        self.eng.add_edge_unchecked(self._actors[actor], "holds_key", k)
        return k

    def fill(self, actor, container, kind, amount):
        """Fill `amount` of `kind` into a container (if it fits by volume and, for a fluid, the vessel
        is watertight)."""
        self.eng.set_attr(self._actors[actor], "fill_kind", kind)
        self.eng.set_attr(self._actors[actor], "fill_amount", float(amount))
        self.eng.set_attr(self._actors[actor], "fill_armed", 1.0); self._run()

    def empty(self, actor, container, kind, amount):
        self.eng.set_attr(self._actors[actor], "empty_kind", kind)
        self.eng.set_attr(self._actors[actor], "empty_amount", float(amount))
        self.eng.set_attr(self._actors[actor], "empty_armed", 1.0); self._run()

    def lock(self, actor): self.eng.set_attr(self._actors[actor], "lock_armed", 1.0); self._run()
    def unlock(self, actor): self.eng.set_attr(self._actors[actor], "unlock_armed", 1.0); self._run()

    def contents(self, container, kind):
        inners = self._containers[container][1]
        return round(float(self.eng.node(inners[kind])["attrs"]["qty"]), 4) if kind in inners else 0.0
    def capacity(self, container): return round(float(self.eng.node(self._containers[container][0])["attrs"]["capacity"]), 4)
    def is_locked(self, container): return float(self.eng.node(self._containers[container][0])["attrs"]["locked"]) == 1.0
    def used_volume(self, container):
        return round(sum(float(self.eng.node(i)["attrs"]["qty"]) * float(self.eng.node(i)["attrs"]["volume"])
                         for i in self._containers[container][1].values()), 4)
    def contents_weight(self, container):
        return round(sum(float(self.eng.node(i)["attrs"]["qty"]) * float(self.eng.node(i)["attrs"]["weight"])
                         for i in self._containers[container][1].values()), 4)
    def item_weight(self, kind): return self._phys(kind)[0]
    def item_volume(self, kind): return self._phys(kind)[1]
    def is_fluid(self, kind): return self._phys(kind)[2] == 1.0

    def add_tradesperson(self, name, trade, *, skill=None, station="educated", literacy=None, capability=None):
        """Add a tradesperson: role = the trade, skill from the TRADES table (unifies trade + skill).
        Townsfolk are UPPITY -- educated by default; `station` (labouring/middle/educated) or an
        explicit literacy/capability sets a lower tier, and literate trades (scribe, teacher) carry
        their own in the TRADES data."""
        t = E.TRADES.get(trade, {})
        s = skill if skill is not None else float(t.get("base_skill", 0.7))
        prof = E.STATION_EDUCATION.get(station, E.STATION_EDUCATION["educated"])
        lit = literacy if literacy is not None else float(t.get("literacy", prof["literacy"]))
        cap = capability if capability is not None else float(t.get("capability", prof["capability"]))
        return self.add_actor(name, role=trade, skill=s, literacy=lit, capability=cap)

    def add_actor(self, name, *, role, skill=0.7, station="educated", literacy=None, capability=None, learn=1.0):
        """Add a resident. LITERACY + general CAPABILITY are class-graded (station), but this town is
        UPPITY -- residents default to EDUCATED. `station` (labouring/middle/educated) or an explicit
        literacy/capability picks a lower tier; `learn` is the aptitude that scales schooling (0 = cannot learn)."""
        prof = E.STATION_EDUCATION.get(station, E.STATION_EDUCATION["labouring"])
        lit = prof["literacy"] if literacy is None else float(literacy)
        cap = prof["capability"] if capability is None else float(capability)
        a = self.eng.add_node("Agent", {"name": name, "role": role, "skill": float(skill),
                                        "fatigue": 0.0, "busy": 0.0,
                                        # residents get hungry, eat food, and starve without it
                                        "hunger": 0.0, "hunger_epoch": 0.0, "alive": 1.0, "starve_limit": 4.0,
                                        "appr_epoch": 0.0,   # apprenticeship: skill grows under a master
                                        # reading/writing + general capability (class-graded; raised at school)
                                        "literacy": lit, "capability": cap, "learn": float(learn), "school_epoch": 0.0,

                                        # observed-demand decision state
                                        "decide_armed": 0.0, "observe_armed": 0.0, "will_make": "",
                                        "want_qty": 0.0, "last_driver": "", "unsold": 0.0,
                                        "belief_harvest": 0.0, "belief_building": 0.0, "belief_storage": 0.0,
                                        # container-op state
                                        "fill_armed": 0.0, "fill_amount": 0.0, "fill_kind": "",
                                        "empty_armed": 0.0, "empty_amount": 0.0, "empty_kind": "",
                                        "lock_armed": 0.0, "unlock_armed": 0.0})
        self.eng.add_edge_unchecked(self._town, "has_actor", a)
        self._actors[name] = a
        self._made = getattr(self, "_made", {}); self._made[name] = 0
        for r in E.RECIPES:                              # a tradesperson KNOWS their trade's COMMON recipes
            if r.get("requires") == role and r.get("common") is not False:
                self.eng.add_edge_unchecked(a, "knows", self._actions[r["name"]])
        return a

    # ---------------------------------------------------- recipe knowledge (taught + written down)
    def knows(self, actor, recipe):
        return self.eng.has_edge(self._actors[actor], "knows", self._actions[recipe])

    def teach(self, teacher, learner, recipe):
        """A resident who KNOWS a recipe teaches it to another -- the learner now knows it."""
        if self.knows(teacher, recipe):
            self.eng.add_edge_unchecked(self._actors[learner], "knows", self._actions[recipe])
        return self.knows(learner, recipe)

    def write_recipe(self, author, recipe):
        """Write a known recipe down -- a Recipe record anyone LITERATE can later read to learn it.
        Refused (None) if the author cannot write (below functional literacy)."""
        assert self.knows(author, recipe), f"{author} does not know {recipe} to write it"
        if not self._can_read(author):
            return None                                 # a labourer's low literacy -- cannot write it down
        rec = self.eng.add_node("WrittenRecipe", {"recipe": recipe})
        self.eng.add_edge_unchecked(self._actors[author], "wrote", rec)
        return rec

    def read_recipe(self, reader, record):
        """Read a written recipe -- a LITERATE reader learns it. Refused (None, no learning) if the
        reader cannot read (below functional literacy). Knowing it is still not being able to MAKE it
        (master work needs the skill -- apprenticeship)."""
        if not self._can_read(reader):
            return None                                 # cannot read it -- must be TAUGHT instead (orally)
        recipe = self.eng.node(record)["attrs"]["recipe"]
        self.eng.add_edge_unchecked(self._actors[reader], "knows", self._actions[recipe])
        return recipe

    # ---------------------------------------------------- apprenticeship (skill built under a master)
    def apprentice(self, learner, master):
        """Apprentice a learner to a master: the learner's skill then rises toward the master's, a
        little each period (the sk_apprentice rule), until they are skilled enough for the master's work."""
        self.eng.add_edge_unchecked(self._actors[learner], "apprenticed_to", self._actors[master])

    def finish_apprenticeship(self, learner, master):
        """End an apprenticeship -- the learner keeps the skill they built."""
        self.eng.remove_edge_unchecked(self._actors[learner], "apprenticed_to", self._actors[master])

    # ---------------------------------------------------- literacy + schooling (reading/writing, education)
    def _lit(self, actor): return float(self.eng.node(self._actors[actor])["attrs"].get("literacy", 0.0))
    def _cap(self, actor): return float(self.eng.node(self._actors[actor])["attrs"].get("capability", 0.0))
    def _can_read(self, actor): return self._lit(actor) >= E.LIT_FUNCTIONAL

    def literacy(self, actor): return round(self._lit(actor), 4)
    def capability(self, actor): return round(self._cap(actor), 4)
    def literacy_tier(self, actor): return E.literacy_tier(self._lit(actor))
    def can_read(self, actor):
        """Functional literacy -- read/write a note, read a written recipe, read the newspaper."""
        return self._can_read(actor)
    def can_read_law(self, actor):
        """Read AND understand the council laws -- only the well educated (needs high capability)."""
        return self._cap(actor) >= E.LIT_EDUCATED and self._lit(actor) >= E.LIT_EDUCATED
    def can_account(self, actor):
        """Keep accounts (reckoning) -- only the well educated."""
        return self._cap(actor) >= E.LIT_EDUCATED
    def can_learn(self, actor): return float(self.eng.node(self._actors[actor])["attrs"].get("learn", 0.0)) > 0.0

    def enrol(self, pupil, teacher):
        """Send a pupil to school under a teacher -- their literacy and capability then rise toward the
        teacher's, a little each period (the ed_school rule), IF they can learn. Reading is learned here;
        a labourer who goes to school can become functionally literate, then educated."""
        self.eng.add_edge_unchecked(self._actors[pupil], "attends", self._actors[teacher])

    def leave_school(self, pupil, teacher):
        self.eng.remove_edge_unchecked(self._actors[pupil], "attends", self._actors[teacher])

    def skill(self, actor): return round(float(self.eng.node(self._actors[actor])["attrs"]["skill"]), 4)
    def recipe_min_skill(self, action_name):
        return round(float(self.eng.node(self._actions[action_name])["attrs"].get("min_skill", 0.0)), 4)
    def can_make(self, actor, action_name):
        """Whether the actor could make it right now -- knows it AND is skilled enough."""
        return self._can_attempt(actor, action_name)

    # ---------------------------------------------------- observed-demand production loop
    def observe(self, maker, *, harvest=None, building=None, storage=None):
        """The maker OBSERVES the town's signals and updates his beliefs (po_observe)."""
        for k, v in (("observed_harvest", harvest), ("observed_building", building),
                     ("observed_storage", storage)):
            if v is not None:
                self.eng.set_attr(self._town, k, float(v))
        self.eng.set_attr(self._actors[maker], "observe_armed", 1.0); self._run()

    def decide(self, maker):
        """The maker DECIDES what and how many to make from his beliefs (pd_decide collapse)."""
        self.eng.set_attr(self._actors[maker], "decide_armed", 1.0); self._run()
        return self.will_make(maker)

    def produce_run(self, maker):
        """Make want_qty of the decided action; returns how many were produced."""
        m = self._actors[maker]
        qty = int(round(float(self.eng.node(m)["attrs"]["want_qty"])))
        made = 0
        for _ in range(qty):
            before = len(list(self.eng.neighbours(self._town, "has_tool_item")))
            self.do(maker, self.will_make(maker))
            made += len(list(self.eng.neighbours(self._town, "has_tool_item"))) - before
        self._made[maker] += made
        return made

    def sell(self, maker, n):
        unsold = max(0, self._made[maker] - int(n))
        self.eng.set_attr(self._actors[maker], "unsold", float(unsold))
        return unsold

    def belief(self, maker, driver="harvest"):
        return round(float(self.eng.node(self._actors[maker])["attrs"][f"belief_{driver}"]), 4)
    def will_make(self, maker): return self.eng.node(self._actors[maker])["attrs"].get("will_make", "")
    def want_qty(self, maker): return round(float(self.eng.node(self._actors[maker])["attrs"]["want_qty"]), 4)

    # ---------------------------------------------------- do an action (the ONE engine)
    def _open_job(self, actor, action_name, remaining):
        asp = self._actions[action_name]
        job = self.eng.add_node("Job", {"remaining": float(remaining), "last_tick": 0.0,
                                        "min_quality": 1.0, "item_inputs": 0.0})
        self.eng.add_edge_unchecked(self._actors[actor], "on_job", job)
        self.eng.add_edge_unchecked(job, "runs", asp)
        self.eng.set_attr(self._actors[actor], "busy", 1.0)
        for need in self.eng.neighbours(asp, "in_need"):
            a = self.eng.node(need)["attrs"]
            jn = self.eng.add_node("Need", {"kind": a["kind"], "qty": float(a["qty"]), "met": 0.0,
                                            "is_item": float(a.get("is_item", 0.0))})
            self.eng.add_edge_unchecked(job, "need", jn)
        for tu in self.eng.neighbours(asp, "in_tool"):
            a = self.eng.node(tu)["attrs"]
            jt = self.eng.add_node("ToolUse", {"kind": a["kind"], "met": 0.0})
            self.eng.add_edge_unchecked(job, "uses", jt)

    def _knows_or_none(self, actor, action_name):
        """An actor can only attempt a recipe they KNOW (a graph fact). Returns False if they don't."""
        return self.eng.has_edge(self._actors[actor], "knows", self._actions[action_name])

    def _skilled_enough(self, actor, action_name):
        """An actor can only attempt a recipe they are SKILLED enough for -- their skill must reach the
        recipe's min_skill floor. Reading the recipe is not enough; the hand needs the training."""
        skill = float(self.eng.node(self._actors[actor])["attrs"]["skill"])
        floor = float(self.eng.node(self._actions[action_name])["attrs"].get("min_skill", 0.0))
        return skill >= floor

    def _can_attempt(self, actor, action_name):
        """Admissible to attempt iff the actor KNOWS the recipe AND is SKILLED enough for it."""
        return self._knows_or_none(actor, action_name) and self._skilled_enough(actor, action_name)

    def do(self, actor, action_name):
        """Perform an action INSTANTLY (no timer). Refused if the actor does not KNOW the recipe or is
        not SKILLED enough (below its min_skill floor)."""
        if not self._can_attempt(actor, action_name):
            return False
        self._open_job(actor, action_name, 0.0); self._run()
        return True

    def start(self, actor, action_name):
        """START a TIMED action; refused if the actor does not know OR is not skilled enough for it."""
        if not self._can_attempt(actor, action_name):
            return False
        mins = float(self.eng.node(self._actions[action_name])["attrs"]["time_minutes"])
        self._open_job(actor, action_name, math.ceil(mins / MINUTES_PER_TICK)); self._run()
        return True

    def tick(self, n=1):
        for _ in range(int(n)):
            self.eng.set_attr(self._town, "clock", float(self.eng.node(self._town)["attrs"]["clock"]) + 1.0)
            self._run()

    def forge(self, actor, action_name):
        self.do(actor, action_name); return self.newest_tool()

    # ---------------------------------------------------- discrete tools (use / repair) + read-offs
    def newest_tool(self):
        tools = list(self.eng.neighbours(self._town, "has_tool_item"))
        return tools[-1] if tools else None

    def use_tool(self, tool, times=1):
        for _ in range(int(times)):
            self.eng.set_attr(tool, "use_armed", 1.0); self._run()

    def repair_tool(self, maker, tool):
        self.eng.add_edge_unchecked(self._actors[maker], "repairs", tool)
        self.eng.set_attr(tool, "repair_armed", 1.0); self._run()

    def tool_kind(self, tool): return self.eng.node(tool)["attrs"]["kind"]
    def tool_quality(self, tool): return round(float(self.eng.node(tool)["attrs"]["quality"]), 4)
    def tool_condition(self, tool): return round(float(self.eng.node(tool)["attrs"]["condition"]), 4)
    def tool_broken(self, tool): return float(self.eng.node(tool)["attrs"]["broken"]) == 1.0
    def tool_fitness(self, tool):
        fits = list(self.eng.neighbours(tool, "fit_for"))
        return round(float(self.eng.node(fits[0])["attrs"]["mult"]), 4) if fits else 0.0
    def instrument_condition(self, kind): return round(float(self.eng.node(self._tools[kind])["attrs"]["condition"]), 4)

    # ---------------------------------------------------- clothes: dyed, worn, protective
    def dye_garment(self, dyer, garment, dye_kind):
        """A dyer dyes a garment a colour from a dye pile -- the RULE (cl_dye) takes the colour from the
        dye's data and consumes one dye. The adapter only arms the garment against the dye Stock."""
        dye = self.set_stock(dye_kind, self.qty(dye_kind))
        self.eng.set_attr(garment, "dye_armed", 1.0)
        self.eng.add_edge_unchecked(garment, "dyed_with", dye)
        self._run()
        return self.garment_colour(garment)

    def wear(self, actor, garment):
        """An agent PUTS ON a garment -- seen wearing it (a wears edge). The garment's warmth/rain rating
        (from the item data) is written onto the instance so the protection rules can read it."""
        spec = self._item_specs.get(self.tool_kind(garment), {})
        self.eng.set_attr(garment, "warmth", float(spec.get("warmth", 0.0)))
        self.eng.set_attr(garment, "rain", float(spec.get("rain", 0.0)))
        self.eng.set_attr(garment, "finery", float(spec.get("finery", 0.0)))
        self.eng.add_edge_unchecked(self._actors[actor], "wears", garment)
        self._run()

    def take_off(self, actor, garment):
        """Take a garment off -- no longer worn, no longer protecting."""
        self.eng.remove_edge_unchecked(self._actors[actor], "wears", garment)
        self._run()

    def worn(self, actor):
        """What an agent is SEEN wearing -- the kinds of the garments they wear."""
        return [self.tool_kind(g) for g in self.eng.neighbours(self._actors[actor], "wears")]

    def garment_colour(self, garment):
        return self.eng.node(garment)["attrs"].get("colour", "")

    def expose(self, *, cold=0.0, wet=0.0):
        """The weather turns cold/wet -- the town's exposure. cl_chill turns it into each resident's
        chill/soaked AFTER their clothes take their share."""
        self.eng.set_attr(self._town, "cold", float(cold))
        self.eng.set_attr(self._town, "wet", float(wet))
        self._run()

    def garment_station(self, garment):
        """How fine a garment is (plain/ordinary/fine) -- from the item data."""
        return self._item_specs.get(self.tool_kind(garment), {}).get("station", "ordinary")
    def dressed_stations(self, actor):
        """The stations of what an agent is seen wearing -- plain (a tradesperson) vs fine (the rich)."""
        return sorted({self.garment_station(g) for g in self.eng.neighbours(self._actors[actor], "wears")})
    def finery(self, actor): return round(float(self.eng.node(self._actors[actor])["attrs"].get("finery", 0.0)), 4)

    def warmth(self, actor):  return round(float(self.eng.node(self._actors[actor])["attrs"].get("warmth", 0.0)), 4)
    def rain_cover(self, actor): return round(float(self.eng.node(self._actors[actor])["attrs"].get("rain_cover", 0.0)), 4)
    def chill(self, actor):   return round(float(self.eng.node(self._actors[actor])["attrs"].get("chill", 0.0)), 4)
    def soaked(self, actor):  return round(float(self.eng.node(self._actors[actor])["attrs"].get("soaked", 0.0)), 4)

    def busy(self, actor): return float(self.eng.node(self._actors[actor])["attrs"]["busy"]) == 1.0
    def fatigue(self, actor): return round(float(self.eng.node(self._actors[actor])["attrs"]["fatigue"]), 4)
    def qty(self, kind):
        return round(float(self.eng.node(self._stock[kind])["attrs"]["qty"]), 4) if kind in self._stock else 0.0
    def item_kinds(self): return {self.eng.node(n)["attrs"]["kind"] for n in self.eng.nodes("ItemSpec")}
    def recipe_names(self): return {self.eng.node(n)["attrs"]["name"] for n in self.eng.nodes("ActionSpec")}
    def store_attrs(self): return self.eng.node(self._store)["attrs"]
