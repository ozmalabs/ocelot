"""SETTLE WORLD — the world adapter for the cortical settling loop.

**ADAPTER ONLY (CLAUDE.md).** Two functions, both mechanical:

* `wire_sheet` — states the cortical sheet's ANATOMY as `sunit_neighbour`
  edges. Which SUnits are cortical neighbours is a positional fact the adapter
  already knows (it placed the RF centres), exactly as `wave_world` states the
  retina's own 4-neighbourhood and as rung 4's `cortical_neighbour` is "wired by
  the adapter as sheet geometry". No conditional over graph state, no decision:
  a translation of a lattice into edges.
* `set_settle_params` — writes the ablation onto the params node. The ablation
  is GRAPH DATA (PROTOCOL 0), never a Python code path.

Everything that DECIDES anything — when the sheet has settled, who survives the
bubble, who learns — is a rule in `seeds/vision_settle.json`.
"""
from __future__ import annotations

from typing import Optional


def wire_sheet(world, units, *, connectivity: int = 4) -> int:
    """Wire `sunit_neighbour` edges between SUnits ADJACENT ON THE CORTICAL
    LATTICE.

    Cortical position IS the RF centre (`cy`, `cx`) — the retinotopy the
    adapter itself placed. Two units are neighbours iff their centres are one
    lattice step apart, which is the SAME 4-neighbourhood the retina uses
    (`wave_world`'s `neighbour`) and the same rule rung 4's `cortical_neighbour`
    follows. **No radius constant is introduced: the adjacency is read off the
    grid the units already sit on** (PROTOCOL 13 — `rf`/`window_steps` are
    "read from committed seeds"; this is the same move).

    Edges are added BOTH ways (the relation is symmetric — a lattice has no
    preferred direction), so `Neighbours(u, 'sunit_neighbour')` sees every
    adjacent unit regardless of insertion order.

    Returns the number of edges added. Mechanical anatomy; no decision.
    """
    s = world.s
    pos = {}
    for u in units:
        a = s.node(u)["attrs"]
        pos[(round(float(a["cy"])), round(float(a["cx"])))] = u
    # The lattice STEP is the grid the adapter laid the centres on — read off
    # the centres themselves, never assumed to be 1.
    ys = sorted({k[0] for k in pos})
    xs = sorted({k[1] for k in pos})
    dy = min((b - a for a, b in zip(ys, ys[1:])), default=1) or 1
    dx = min((b - a for a, b in zip(xs, xs[1:])), default=1) or 1
    if connectivity == 4:
        offs = [(dy, 0), (-dy, 0), (0, dx), (0, -dx)]
    elif connectivity == 8:
        offs = [(a * dy, b * dx) for a in (-1, 0, 1) for b in (-1, 0, 1)
                if (a, b) != (0, 0)]
    else:
        raise ValueError(f"connectivity must be 4 or 8, got {connectivity!r}")
    n = 0
    for (cy, cx), u in pos.items():
        for oy, ox in offs:
            v = pos.get((cy + oy, cx + ox))
            if v is None:
                continue
            s.add_edge(u, "sunit_neighbour", v)
            n += 1
    return n


def set_settle_params(world, *, settle: Optional[float] = None,
                      bubble: Optional[float] = None) -> None:
    """Write the ablation onto the SettleParams node. Mechanical."""
    s = world.s
    ps = s.nodes("SettleParams")
    if not ps:
        raise RuntimeError("no SettleParams node — is vision_settle loaded?")
    if len(ps) != 1:
        raise RuntimeError(f"{len(ps)} SettleParams nodes — the config read is "
                           f"ambiguous and PickUnique would panic (PROTOCOL 12.3)")
    p = ps[0]
    if settle is not None:
        s.set_attr(p, "settle", float(settle))
    if bubble is not None:
        s.set_attr(p, "bubble", float(bubble))
