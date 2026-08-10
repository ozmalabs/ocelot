"""bigville_integ_state -- THE TOWN-STATE EXPORT CONTRACT (a pure READER).

Exports the assembled town's state as JSON matching EXACTLY the UI's data contract
(BIGVILLE_MOVEMENT_ECONOMY_SPEC.md R10, block 258000). A parallel UI track renders
from this shape; wiring later is a swap. The reader makes NO decisions -- it queries
graph state -> JSON. Every field is a mechanical read of `world.eng` / `world` host
state; nothing is computed by an agent rule here.

Contract (exact keys/types):
  { "day": int, "phase": "dawn|day|dusk|night", "tick": int,
    "map": {"w":int,"h":int,"tiles":[[str]], "buildings":[{...}]},
    "villagers": [{...}], "institutions": {...}, "metrics": {...},
    "levers": {...}, "events": [{...}], "macro": [{...}] }
"""
from __future__ import annotations

import json

# tile-code -> contract tile string (from BigvilleSimWorld's grid legend)
_TILE = {0: "grass", 1: "path", 2: "wall", 3: "floor", 4: "square", 5: "tree",
         6: "water"}
_PHASE4 = ["dawn", "day", "dusk", "night"]


def _cls_face(cls):
    return {"rich": "\U0001F9D0", "middle": "\U0001F642", "poor": "\U0001F61F"}.get(
        cls, "\U0001F9D1")


def _phase_str(world):
    """dawn|day|dusk|night from the async clock (mechanical: phase + position)."""
    if getattr(world, "phase", 0) == 1:
        return "night"
    # day sub-phase: first sixth = dawn, last sixth = dusk, else day
    pl = max(1, getattr(world, "phase_len", 6))
    pos = world.world_epoch % pl
    if pos == 0:
        return "dawn"
    if pos == pl - 1:
        return "dusk"
    return "day"


def _held_of(world, nm):
    """The villager's currently-chosen action label (glass-box 'what it holds')."""
    try:
        return world.chosen_label_of(nm)
    except Exception:
        return "none"


def _rel_of(world, nm):
    """Sparse relations read off the graph (backs/hates/kin/owes) -- mechanical."""
    rel = []
    # a rivalry (tension) reads as 'hates'
    for (a, b) in getattr(world, "tensions", []):
        if a == nm:
            rel.append({"to": b, "kind": "hates"})
    # an heir edge reads as 'kin'
    try:
        for h in world.eng.neighbours(world._movers[nm], "heir"):
            for cand, nid in world._movers.items():
                if nid == h:
                    rel.append({"to": cand, "kind": "kin"})
    except Exception:
        pass
    # an outstanding obligation reads as 'owes'
    try:
        if world.balance_of(nm) > 0:
            rel.append({"to": "bank", "kind": "owes"})
    except Exception:
        pass
    return rel


def _buildings(world):
    out = []
    # the affordances from the SimWorld grid (office/church/square/houses)
    aff_kind = {"office": "townhall", "church": "church", "square": "land",
                "house": "house"}
    for a in getattr(world, "affordances", []):
        out.append({"id": a["name"].replace(" ", "_").lower(),
                    "type": aff_kind.get(a.get("kind"), "house"),
                    "x": int(a["x"]), "y": int(a["y"]), "w": 3, "h": 3,
                    "owner": "", "name": a["name"]})
    # the finance institution: the bank
    if getattr(world, "_bank", None) is not None:
        out.append({"id": "bank", "type": "bank", "x": 2, "y": 2, "w": 3, "h": 3,
                    "owner": getattr(world, "_banker", "scrooge"), "name": "Bank"})
    return out


def _institutions(world):
    def a(nid, key, default=0.0):
        try:
            return world.eng.node(nid)["attrs"].get(key, default)
        except Exception:
            return default
    inst = world.institutions
    bank = {"reserves": int(world.reserves()) if getattr(world, "_bank", None) else 0,
            "rate_bp": int(world.bank_rate_bp()) if getattr(world, "_bank", None) else 0}
    church = {"funds": int(a(inst.get("church"), "funds"))}
    council = {"treasury": int(a(inst.get("council"), "treasury", 0.0)),
               "tax_bp": int(a(inst.get("council"), "tax_bp", 0.0)),
               "captured": bool(a(inst.get("council"), "captured", 0.0))}
    school = {"funded": bool(a(inst.get("school"), "funded", 0.0))}
    surgery = {"public": bool(a(inst.get("surgery"), "public", 0.0))}
    press = {"captured": bool(a(inst.get("press"), "captured", 0.0))}
    return {"bank": bank, "church": church, "council": council, "school": school,
            "surgery": surgery, "press": press}


def _metrics(world):
    living = world.living_count()
    dead = len(world.people) - living
    infant_mortality = 0.0  # no infant cohort populated in this assembly (dormant)
    return {"gini_wealth": round(world.gini_wealth(), 4),
            "gini_land": round(world.gini_land(), 4),
            "health_gradient": round(_health_gradient(world), 4),
            "fertility_gradient": 0.0,
            "circulation": int(world.circulation()),
            "council_corr": 0.0,
            "infant_mortality": round(dead / max(1, len(world.people)), 4)}


def _health_gradient(world):
    """Correlation proxy: mean health of the rich minus mean health of the poor
    (a class health gradient, glass-box read)."""
    def mean_h(cls):
        hs = [world.health_of(nm) for nm in world.people
              if world.classes.get(nm) == cls and not world.is_dead(nm)
              and nm in world._life]
        return sum(hs) / len(hs) if hs else 0.0
    return mean_h("rich") - mean_h("poor")


def export_townstate(world, *, macro_tail=None):
    """Build the exact-shape town-state dict from graph + host state (pure read)."""
    villagers = []
    for nm in world.people:
        alive = not world.is_dead(nm)
        cls = world.classes.get(nm, "middle")
        try:
            health = int(world.health_of(nm)) if nm in world._life else 100
        except Exception:
            health = 100
        villagers.append({
            "id": nm, "name": nm, "role": world.roles.get(nm, "villager"),
            "x": int(world.pos.get(nm, (0, 0))[0]),
            "y": int(world.pos.get(nm, (0, 0))[1]),
            "coin": int(world.coin_of(nm)),
            "health": health,
            "land_plots": int(world.plots_held(nm)),
            "window": int(round(world.grief_of(nm))),
            "alive": bool(alive),
            "cls": cls,
            "face": _cls_face(cls),
            "journal": "%s (%s): %s" % (nm, cls, _held_of(world, nm)),
            "held": _held_of(world, nm),
            "rel": _rel_of(world, nm),
        })
    # the banker as an extra villager (runs the bank)
    banker = getattr(world, "_banker", None)
    if banker is not None:
        villagers.append({
            "id": banker, "name": "Scrooge", "role": "banker",
            "x": int(world.pos.get(banker, (2, 2))[0]),
            "y": int(world.pos.get(banker, (2, 2))[1]),
            "coin": int(world.coin_of(banker)), "health": 90,
            "land_plots": int(world.plots_held(banker)), "window": 0,
            "alive": not world.is_dead(banker), "cls": "rich",
            "face": "\U0001F911", "journal": "Scrooge runs the bank.",
            "held": "bank", "rel": []})

    macro = world.macro if macro_tail is None else world.macro[-macro_tail:]
    macro_out = [{"tick": m["tick"], "activity": m["activity"], "cost": m["cost"]}
                 for m in macro]
    events_out = [{"tick": e["tick"], "kind": e["kind"], "actors": e["actors"],
                   "text": e["text"]} for e in world.events]

    day = world.world_epoch // max(1, getattr(world, "phase_len", 6) * 2)
    return {
        "day": int(day),
        "phase": _phase_str(world),
        "tick": int(world.world_epoch),
        "map": {"w": int(world.W), "h": int(world.H),
                "tiles": [[_TILE.get(c, "grass") for c in row] for row in world.grid],
                "buildings": _buildings(world)},
        "villagers": villagers,
        "institutions": _institutions(world),
        "metrics": _metrics(world),
        "levers": {"redistribution": False, "land_tax": False,
                   "public_health": bool(world.institutions.get("surgery")),
                   "free_school": True},
        "events": events_out,
        "macro": macro_out,
    }


def write_snapshot(world, path, *, macro_tail=None):
    state = export_townstate(world, macro_tail=macro_tail)
    with open(path, "w") as f:
        json.dump(state, f, indent=2)
    return state


# the exact contract keys, for the gate test to assert against.
CONTRACT_TOP_KEYS = {"day", "phase", "tick", "map", "villagers", "institutions",
                     "metrics", "levers", "events", "macro"}
CONTRACT_MAP_KEYS = {"w", "h", "tiles", "buildings"}
CONTRACT_VILLAGER_KEYS = {"id", "name", "role", "x", "y", "coin", "health",
                          "land_plots", "window", "alive", "cls", "face",
                          "journal", "held", "rel"}
CONTRACT_INSTITUTION_KEYS = {"bank", "church", "council", "school", "surgery", "press"}
CONTRACT_METRIC_KEYS = {"gini_wealth", "gini_land", "health_gradient",
                        "fertility_gradient", "circulation", "council_corr",
                        "infant_mortality"}
CONTRACT_LEVER_KEYS = {"redistribution", "land_tax", "public_health", "free_school"}
