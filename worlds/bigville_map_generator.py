"""bigville_map_generator -- block 340000: the TOWN MAP, generated from a spec + seed.

Replaces hand-editing every place/room in every world adapter. The map is the WORLD, so
this is an admissible world-BUILDER (mechanical graph construction, deterministic given a
spec + rng seed -- NO agent decisions). It emits a containment hierarchy:

    Town -has_place-> Place{kind,name,wealth,x,y}
    Place -has_room-> Room{kind,name,private,x,y}
    Room  -affords-> <AffordanceNode>          (Station / Larder / Bed / Bell / ...)
    Room  -door->    Room                        (interior connectivity)
    Place -entrance-> Room ; Room -street-> Square   (exterior connectivity)

AFFORDANCES reuse the EXISTING typed nodes (Station{heat,prep_power,fuel,fuel_cost} from the
food/tools rungs, Larder, ...) so a generated kitchen is directly cookable by fs_prepare --
no reinvention. They come from a PRESET LIBRARY: a CommercialKitchen, a NormalKitchen and a
PoorKitchen are named profiles with different DEFAULTS. Add a preset here once; the generator
drops it everywhere.

FIXED-POINTS (the church with Mary's private counsel room + bell, the inn with a commercial
kitchen + guest beds, the jail with cells, the market, the council hall) are always emitted,
regardless of seed. Ordinary HOUSES are procedurally filled -- some with a kitchen, some
without -- from per-wealth distributions in the spec. The rng seed varies the fill
deterministically (same seed -> same town).
"""
from __future__ import annotations

import os
import random
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (os.path.join(_ROOT, "runners", "dsl", "python"), _ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import substrate_rs                                     # noqa: E402

# ---------------------------------------------------------------------------
# AFFORDANCE PRESETS -- named profiles with default parameter bundles.
# Each entry is a list of (NodeType, attrs) to mint and `affords`-link to a room.
# Kitchen presets emit a real Station (heat>=1 => cookable by fs_prepare).
# ---------------------------------------------------------------------------
PRESETS = {
    # --- kitchens: same Station type, different defaults (commercial > normal > poor) ---
    "CommercialKitchen": [("Station", {"name": "range", "heat": 1.0, "prep_power": 1.2,
                                       "fuel": 50.0, "fuel_cost": 1.0}),
                          ("Larder", {"cold": 1.0, "capacity": 200.0, "cold_factor": 0.4})],
    "NormalKitchen":     [("Station", {"name": "stove", "heat": 1.0, "prep_power": 0.6,
                                       "fuel": 15.0, "fuel_cost": 1.0})],
    "PoorKitchen":       [("Station", {"name": "hearth", "heat": 1.0, "prep_power": 0.3,
                                       "fuel": 5.0, "fuel_cost": 1.0})],
    # --- other affordances ---
    "Bench":   [("Station", {"name": "bench", "heat": 0.0, "prep_power": 0.6,
                             "fuel": 0.0, "fuel_cost": 0.0})],   # prep surface, no heat
    "Bed":     [("Bed", {"rest_rate": 0.3})],
    "Pantry":  [("Larder", {"cold": 1.0, "capacity": 60.0, "cold_factor": 0.4})],
    "Bell":    [("Bell", {"range": 120.0})],
    "Cell":    [("Cell", {"secure": 1.0})],
    "Stall":   [("MarketStall", {"trades": 1.0})],
    "Pew":     [("Pew", {"seats": 20.0})],
    # --- crafts: the forge is self-lit (its fire) so the smith can work after dark ---
    "Forge":   [("Forge", {"name": "forge", "heat": 1.0, "lit": 1.0, "fuel": 50.0})],
    "Workbench": [("Station", {"name": "workbench", "heat": 0.0, "prep_power": 0.6,
                               "fuel": 0.0, "fuel_cost": 0.0})],
    "Clamp":   [("Clamp", {"name": "charcoal clamp", "burns": 1.0})],   # the collier's earth-covered pile
}

# ---------------------------------------------------------------------------
# DEFAULT SPEC -- the fixed-points + the procedural-house distributions.
# Edit here to change the town; the generator reads this data, it hard-codes nothing.
# ---------------------------------------------------------------------------
DEFAULT_SPEC = {
    "fixed_points": [
        {"kind": "church", "name": "Church", "wealth": "communal", "staff": "Mary",
         "staff_role": "pastor", "attrs": {"non_denominational": 1.0}, "staff_attrs": {"draw": 0.8},
         "rooms": [
            {"kind": "nave", "preset": "Pew"},
            {"kind": "counsel", "private": 1.0},          # Mary's private counsel room
            {"kind": "belfry", "preset": "Bell"}]},
        {"kind": "inn", "name": "Inn", "wealth": "rich", "rooms": [
            {"kind": "kitchen", "preset": "CommercialKitchen"},
            {"kind": "taproom", "preset": "Bench"},
            {"kind": "guestroom", "preset": "Bed"},
            {"kind": "guestroom", "preset": "Bed"},
            {"kind": "guestroom", "preset": "Bed"}]},
        {"kind": "jail", "name": "Jail", "wealth": "communal", "rooms": [
            {"kind": "cell", "preset": "Cell"},
            {"kind": "cell", "preset": "Cell"}]},
        {"kind": "market", "name": "Market", "wealth": "communal", "rooms": [
            {"kind": "square", "preset": "Stall"}]},
        {"kind": "council_hall", "name": "Council Hall", "wealth": "communal", "rooms": [
            {"kind": "chamber"}]},
        # the FORGE -- a sheltered, self-lit smithy; the blacksmith makes tool heads (bigville_craft)
        {"kind": "forge", "name": "Forge", "wealth": "normal", "staff": "Wayland",
         "staff_role": "blacksmith", "provides": "smith", "attrs": {"sheltered": 1.0},
         # the smith burns his own charcoal (a clamp out back); no dedicated collier at village scale
         "staff_attrs": {"skill": 0.7, "yield": 0.25, "burn_armed": 0.0, "wood_in": 0.0, "burned": 0.0},
         "rooms": [{"kind": "smithy", "preset": "Forge"}, {"kind": "clamp", "preset": "Clamp"}]},
        # the WOODSHOP -- the woodworker makes handles/shafts (bigville_craft)
        {"kind": "woodshop", "name": "Woodshop", "wealth": "normal", "staff": "Grip",
         "staff_role": "woodworker", "provides": "woodworker", "attrs": {"sheltered": 1.0},
         "staff_attrs": {"skill": 0.6}, "rooms": [{"kind": "shop", "preset": "Workbench"}]},
    ],
    "houses": {
        "count": 6,
        "wealth_weights": {"poor": 3, "normal": 4, "rich": 1},
        "kitchen_prob_by_wealth": {"poor": 0.4, "normal": 0.85, "rich": 1.0},
        "kitchen_preset_by_wealth": {"poor": "PoorKitchen", "normal": "NormalKitchen", "rich": "CommercialKitchen"},
        # every house has a bedroom (a Bed); richer houses add a pantry (a Larder)
        "pantry_prob_by_wealth": {"poor": 0.0, "normal": 0.3, "rich": 0.9},
    },
}


class BigvilleMapGenerator:
    def __init__(self, spec=None, *, seed=0, eng=None):
        self.spec = spec if spec is not None else DEFAULT_SPEC
        self.seed = int(seed)
        self.eng = eng if eng is not None else substrate_rs.Substrate()._inner
        self._town = None
        self._square = None
        self._places = {}       # name -> place node
        self._rooms = {}        # (place_name, room node id list)
        self._room_list = {}    # place_name -> [(room node, kind)]
        self._generated = False

    # ------------------------------------------------------------------ build
    def generate(self):
        rng = random.Random(self.seed)
        self._town = self.eng.add_node("Town", {"name": "Bigville"})
        self._square = self.eng.add_node("Square", {"name": "town square", "x": 0.0, "y": 0.0})
        self.eng.add_edge_unchecked(self._town, "has_square", self._square)
        x = 1.0
        # 1) FIXED-POINTS -- always present, deterministic
        for fp in self.spec["fixed_points"]:
            self._build_place(fp, x, staff=fp.get("staff"))
            x += 2.0
        # 2) HOUSES -- procedurally filled from per-wealth distributions
        h = self.spec.get("houses", {})
        wealths, weights = zip(*[(w, n) for w, n in h.get("wealth_weights", {"normal": 1}).items()])
        for i in range(h.get("count", 0)):
            wealth = rng.choices(wealths, weights=weights, k=1)[0]
            rooms = [{"kind": "bedroom", "preset": "Bed"}]           # every home has a bed
            # a kitchen -- MAYBE, by wealth (this is the "houses may or may not cook" knob)
            if rng.random() < h["kitchen_prob_by_wealth"][wealth]:
                rooms.insert(0, {"kind": "kitchen", "preset": h["kitchen_preset_by_wealth"][wealth]})
            if rng.random() < h.get("pantry_prob_by_wealth", {}).get(wealth, 0.0):
                rooms.append({"kind": "pantry", "preset": "Pantry"})
            self._build_place({"kind": "house", "name": f"house{i+1}", "wealth": wealth, "rooms": rooms}, x)
            x += 2.0
        self._generated = True
        return self

    # kinds that carry a behavioural role edge (town -has_<role>-> place), so the existing
    # institution rules (ch_* / jl_* / inn) bind to generated geography instead of hand-built nodes
    _ROLE = {"church": "church", "inn": "inn", "jail": "jail", "market": "market",
             "council_hall": "council", "forge": "forge", "woodshop": "woodshop"}

    def _build_place(self, spec, x, *, staff=None):
        name = spec["name"]
        p = self.eng.add_node("Place", {"kind": spec["kind"], "name": name,
                                        "wealth": spec.get("wealth", "normal"), "x": float(x), "y": 0.0})
        self.eng.add_edge_unchecked(self._town, "has_place", p)
        role = self._ROLE.get(spec["kind"])
        if role is not None:
            self.eng.add_edge_unchecked(self._town, f"has_{role}", p)   # e.g. has_church, has_jail
        for k, v in spec.get("attrs", {}).items():
            self.eng.set_attr(p, k, v)                                   # e.g. non_denominational
        self._places[name] = p
        self._room_list[name] = []
        prev_room = None
        for j, rspec in enumerate(spec.get("rooms", [])):
            r = self.eng.add_node("Room", {"kind": rspec["kind"], "name": f"{name}:{rspec['kind']}",
                                           "private": float(rspec.get("private", 0.0)),
                                           "x": float(x), "y": float(j + 1)})
            self.eng.add_edge_unchecked(p, "has_room", r)
            self._room_list[name].append((r, rspec["kind"]))
            if j == 0:                                        # first room is the entrance
                self.eng.add_edge_unchecked(p, "entrance", r)
                self.eng.add_edge_unchecked(r, "street", self._square)
                self.eng.add_edge_unchecked(self._square, "street", r)
            if prev_room is not None:                          # chain rooms with doors (both ways)
                self.eng.add_edge_unchecked(prev_room, "door", r)
                self.eng.add_edge_unchecked(r, "door", prev_room)
            prev_room = r
            # affordances from the preset library
            preset = rspec.get("preset")
            if preset:
                for ntype, attrs in PRESETS[preset]:
                    a = self.eng.add_node(ntype, dict(attrs))
                    self.eng.add_edge_unchecked(r, "affords", a)
        if staff is not None:
            attrs = {"name": staff, "role": spec.get("staff_role", f"{spec['kind']}_staff")}
            attrs.update(spec.get("staff_attrs", {}))
            s = self.eng.add_node("Agent", attrs)
            self.eng.add_edge_unchecked(p, "staffed_by", s)
            # a trade PROVIDES a maker: town -has_smith/has_woodworker-> the staff agent, so the
            # bigville_craft rules (which match town -has_smith-> maker) bind to the town's geography
            provides = spec.get("provides")
            if provides is not None:
                self.eng.add_edge_unchecked(self._town, f"has_{provides}", s)
            self._places[f"__staff__{name}"] = s
        return p

    def role_place(self, role):
        """The generated place carrying a behavioural role (church/inn/jail/market/council)."""
        for name, p in self._places.items():
            if name.startswith("__staff__"):
                continue
            if self._ROLE.get(self.eng.node(p)["attrs"]["kind"]) == role:
                return p
        return None

    def staff_node(self, place_name):
        return self._places.get(f"__staff__{place_name}")

    # ------------------------------------------------- glass-box read-offs
    def places(self):
        return [n for n in self._places if not n.startswith("__staff__")]
    def place_kind(self, name): return self.eng.node(self._places[name])["attrs"]["kind"]
    def place_wealth(self, name): return self.eng.node(self._places[name])["attrs"]["wealth"]
    def rooms(self, name): return [k for _, k in self._room_list[name]]
    def room_node(self, name, kind):
        for r, k in self._room_list[name]:
            if k == kind:
                return r
        return None
    def room_is_private(self, name, kind):
        r = self.room_node(name, kind)
        return r is not None and float(self.eng.node(r)["attrs"].get("private", 0.0)) == 1.0
    def staff_of(self, name):
        s = self._places.get(f"__staff__{name}")
        return None if s is None else self.eng.node(s)["attrs"]["name"]

    def affordances(self, name):
        """All (node_type, attrs) a place affords, across its rooms."""
        out = []
        for r, _ in self._room_list[name]:
            for a in self.eng.neighbours(r, "affords"):
                nd = self.eng.node(a)
                out.append((nd["type"], nd["attrs"]))
        return out

    def kitchen_station(self, name):
        """The heated Station of the place's kitchen, or None (no cooking facilities)."""
        for r, k in self._room_list[name]:
            if k == "kitchen":
                for a in self.eng.neighbours(r, "affords"):
                    nd = self.eng.node(a)
                    if nd["type"] == "Station" and float(nd["attrs"].get("heat", 0.0)) >= 1.0:
                        return a
        return None
    def has_kitchen(self, name): return self.kitchen_station(name) is not None
    def prep_power(self, name):
        st = self.kitchen_station(name)
        return None if st is None else round(float(self.eng.node(st)["attrs"]["prep_power"]), 4)

    def fingerprint(self):
        """A structural signature of the whole town -- for determinism gates."""
        sig = []
        for n in sorted(self.places()):
            sig.append((n, self.place_kind(n), self.place_wealth(n),
                        tuple(self.rooms(n)), self.has_kitchen(n)))
        return tuple(sig)
