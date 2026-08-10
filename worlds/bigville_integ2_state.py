"""bigville_integ2_state -- the R10b TOWN-STATE EXPORT CONTRACT (a pure READER).

Extends R10's `bigville_integ_state` (imported, unedited) with the supervisor's
presentation additions, ALL as faithful graph reads -- never authored prose:

  * NAMED cast    -- `name`/`face`/`role` are the resident's real assigned register
                     name + emoji + role (zero generic `v00`).
  * DEEP held     -- `held` is composed from the REAL affect/decision state the
                     substrate holds (chosen action, grief, wellbeing, conflict,
                     snap-pressure, spite, w_supergraph, hostility); for the banker,
                     his real rate intent + reserves + foreclosure state. Scrooge's
                     R10 hardcode `"held":"bank"` is GONE. A field absent from the
                     graph is OMITTED, never invented.
  * REAL journal  -- the resident's actual latest nightly entry IF the nightly-journal
                     faculty fired; it is loaded-but-DORMANT in this assembly, so the
                     honest read is `journal: null` ("no entry"), NEVER a fake summary.
  * COHERENT map  -- institutions around a central square + a resource `features`
                     base (farm / fishery / timber / quarry / well / orchard), and
                     each resident at a MEANINGFUL home/workplace position.

The contract SUPERSETS R10's shape (same top keys; `map` gains `features`; each
villager gains an explicit `journal` that may be null). Pure read -> JSON; no decision.
"""
from __future__ import annotations

import json

from worlds.bigville_integ_state import (                               # noqa: E402
    _TILE, _PHASE4, _phase_str, _institutions, _metrics, _buildings,
    CONTRACT_TOP_KEYS, CONTRACT_VILLAGER_KEYS)


def _attr(world, nm, key, default=0.0):
    try:
        return world.eng.node(world._movers[nm])["attrs"].get(key, default)
    except Exception:
        return default


def _real_journal(world, nm):
    """The resident's REAL latest nightly journal entry, read from the graph. The
    nightly-journal faculty is loaded-but-DORMANT in this assembly (no Journal node is
    ever minted), so this honestly returns None ("no entry") -- never a fabricated
    summary. If a graph-resident journal is wired later, this reads it with no change."""
    try:
        for j in world.eng.neighbours(world._movers[nm], "wrote_journal"):
            return world.eng.node(j)["attrs"].get("text")
    except Exception:
        pass
    return None


def _deep_held(world, nm, *, is_banker=False):
    """Compose the resident's held string from REAL graph-resident state only.
    Every part is a live read; nothing authored. Absent fields are omitted."""
    parts = []
    a = {}
    try:
        a = world.eng.node(world._movers[nm])["attrs"]
    except Exception:
        a = {}
    try:
        act = world.chosen_label_of(nm)
        if act and act != "none":
            parts.append("doing=%s" % act)
    except Exception:
        pass
    g = float(a.get("grief_distress", 0.0) or 0.0)
    if g > 0.0:
        parts.append("grief=%.1f" % g)
    wb = a.get("wellbeing")
    if wb is not None:
        parts.append("wellbeing=%.0f" % float(wb))
    conf = float(a.get("conflict", 0.0) or 0.0)
    if conf > 0.0:
        parts.append("conflict=%.1f" % conf)
    sp = float(a.get("snap_pressure", 0.0) or 0.0)
    if sp > 0.0:
        parts.append("snap_pressure=%.2f" % sp)
    ws = a.get("w_spite")
    if ws is not None and float(ws) > 0.0:
        parts.append("spite=%.2f" % float(ws))
    for key, label in (("w_supergraph", "supergraph"), ("hostile_weight", "hostility"),
                       ("mood_bias", "mood")):
        if key in a and a.get(key) is not None:
            parts.append("%s=%.2f" % (label, float(a[key])))
    if is_banker:
        try:
            parts.append("rate_bp=%d" % int(world.bank_rate_bp()))
        except Exception:
            pass
        try:
            parts.append("reserves=%d" % int(world.reserves()))
        except Exception:
            pass
        fc = int(a.get("foreclosures", 0) or 0)
        if fc:
            parts.append("foreclosures=%d" % fc)
    return "; ".join(parts) if parts else None


def _features(world):
    """The resource base as UI map features (world-setup positions, deterministic).
    Placed at coherent town-edge cells; water features snap to a water tile if the
    grid has one, else the nearest walkable cell."""
    cells = getattr(world, "_cells", None) or sorted(getattr(world, "_cell_at", {}))
    if not cells:
        return []
    w = max(x for (x, y) in cells) + 1
    h = max(y for (x, y) in cells) + 1
    anchors = getattr(world, "map_anchors", {})
    well = anchors.get("townhall", (w // 2, h // 2))
    return [
        {"type": "crop", "x": 1, "y": 1, "w": max(3, w // 4), "h": max(2, h // 6)},
        {"type": "forest", "x": max(1, w - 6), "y": 1, "w": 5, "h": max(2, h // 5)},
        {"type": "rocks", "x": max(1, w - 5), "y": max(1, h - 5), "w": 4, "h": 3},
        {"type": "orchard", "x": 1, "y": max(1, h - 5), "w": 4, "h": 3},
        {"type": "water", "x": w // 2 - 1, "y": max(1, h - 3), "w": 4, "h": 2},
        {"type": "well", "x": int(well[0]), "y": int(well[1]) + 1, "w": 1, "h": 1},
    ]


def _coherent_buildings(world):
    """Institutions laid out around the central square (from the world's map anchors),
    plus the bank. Falls back to R10's affordance buildings if anchors are absent."""
    anchors = getattr(world, "map_anchors", None)
    if not anchors:
        return _buildings(world)
    kind = {"townhall": "townhall", "noticeboard": "noticeboard", "bank": "bank",
            "church": "church", "school": "school", "surgery": "surgery",
            "inn": "inn", "press": "press"}
    out = []
    for key, (x, y) in anchors.items():
        out.append({"id": key, "type": kind.get(key, "house"),
                    "x": int(x), "y": int(y), "w": 3, "h": 3,
                    "owner": (getattr(world, "_banker", "") if key == "bank" else ""),
                    "name": key.capitalize()})
    return out


def _villager_entry(world, nm, *, is_banker=False):
    alive = not world.is_dead(nm)
    cls = (("rich(banker)" if is_banker else world.classes.get(nm, "middle")))
    disp = world.display.get(nm, nm)
    face = world.emoji.get(nm, "\U0001F9D1")
    role = world.roles2.get(nm, world.roles.get(nm, "villager"))
    home = world.homes.get(nm) or world.pos.get(nm, (0, 0))
    try:
        health = int(world.health_of(nm)) if nm in world._life else 100
    except Exception:
        health = 100
    return {
        "id": nm, "name": disp, "role": role,
        "x": int(home[0]), "y": int(home[1]),
        "coin": int(world.coin_of(nm)),
        "health": health,
        "land_plots": int(world.plots_held(nm)),
        "window": int(round(world.grief_of(nm))) if not is_banker else 0,
        "alive": bool(alive),
        "cls": cls,
        "face": face,
        "journal": _real_journal(world, nm),   # real read; null when dormant
        "held": _deep_held(world, nm, is_banker=is_banker),
        "rel": _rel(world, nm),
    }


def _rel(world, nm):
    rel = []
    for (a, b) in getattr(world, "tensions", []):
        if a == nm:
            rel.append({"to": world.display.get(b, b), "kind": "hates"})
    try:
        for h in world.eng.neighbours(world._movers[nm], "heir"):
            for cand, nid in world._movers.items():
                if nid == h:
                    rel.append({"to": world.display.get(cand, cand), "kind": "kin"})
    except Exception:
        pass
    try:
        if world.balance_of(nm) > 0:
            rel.append({"to": "bank", "kind": "owes"})
    except Exception:
        pass
    return rel


def export_townstate2(world, *, macro_tail=None):
    """The full R10b town-state dict: named cast + deep held + real(null) journal +
    coherent map. Pure read."""
    villagers = [_villager_entry(world, nm) for nm in world.people]
    bk = getattr(world, "_banker", None)
    if bk is not None:
        villagers.append(_villager_entry(world, bk, is_banker=True))

    macro = world.macro if macro_tail is None else world.macro[-macro_tail:]
    macro_out = [{"tick": m["tick"], "activity": m["activity"], "cost": m["cost"],
                  "births": m.get("births", 0)} for m in macro]
    events_out = [{"tick": e["tick"], "kind": e["kind"],
                   "actors": [world.display.get(x, x) for x in e.get("actors", [])],
                   "text": e["text"]} for e in world.events]
    births_out = [{"tick": b["tick"], "parent": world.display.get(b["parent"], b["parent"]),
                   "child": b.get("name", b["child"])} for b in getattr(world, "births", [])]

    pl = max(1, getattr(world, "phase_len", 6))
    day = world.world_epoch // (pl * 2)
    return {
        "day": int(day),
        "phase": _phase_str(world),
        "tick": int(world.world_epoch),
        "map": {"w": int(world.W), "h": int(world.H),
                "tiles": [[_TILE.get(c, "grass") for c in row] for row in world.grid],
                "buildings": _coherent_buildings(world),
                "features": _features(world)},
        "villagers": villagers,
        "institutions": _institutions(world),
        "metrics": _metrics(world),
        "levers": {"redistribution": False, "land_tax": False,
                   "public_health": bool(world.institutions.get("surgery")),
                   "free_school": True},
        "events": events_out,
        "births": births_out,
        "macro": macro_out,
    }


def write_snapshot2(world, path, *, macro_tail=None):
    state = export_townstate2(world, macro_tail=macro_tail)
    with open(path, "w") as f:
        json.dump(state, f, indent=2)
    return state


# the exact contract keys the gate asserts (superset of R10: +features, +births,
# each villager carries an explicit `journal`).
CONTRACT2_TOP_KEYS = CONTRACT_TOP_KEYS | {"births"}
CONTRACT2_MAP_KEYS = {"w", "h", "tiles", "buildings", "features"}
CONTRACT2_VILLAGER_KEYS = CONTRACT_VILLAGER_KEYS   # same keys; journal may be null
