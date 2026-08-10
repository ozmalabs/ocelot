"""decay_world — the world adapter for THE EDGE-ANCHORED DECAYING GRADIENT
(VISION_DECAY_PREREG.md).

Mechanical I/O ONLY (CLAUDE.md / PROTOCOL §0). It is a THIN layer over
`paint_world`, and it exists as a separate file for one reason: the paint rung's
committed gate reads `domains/paint_world.py`'s live source and asserts that its
only `set_attr` write is `paint`. That rung's result is not this rung's to
disturb, so `paint_world.py` is NOT EDITED AT ALL and the second flag is written
here instead.

Three mechanical jobs, no decisions:

  1. PRE-SEED the v1.1.0 cell attributes to 0.0 — the same clean-zero
     initialisation `paint_world._CELL_ZEROS` does for v1.0.0's, so an OFF run
     reads a readable zero rather than a missing key.
  2. BLIND-WRITE `pdecay` on every PaintParams node. No read, no branch.
  3. READ BACK — pure queries.

There is NO decision here: the anchor, the distance, the decay length and the
weight are ALL rules in `seeds/vision_paint.json`. A source gate in
`tests/test_decay_gradient_migrated.py` enforces it by AST, exactly as the paint
rung's does — and it FIRED on the first version of this file, which selected the
anchor cells with a Python comprehension guard over `panchor`. That guard was
DELETED rather than exempted: the anchor set is now reported as the raw
`panchor` FIELD, so there is no conditional at all and the read-back is strictly
MORE informative than the filtered list it replaced. (Widening the gate's
attribute list to make the failure go away would have been exactly the
allowlist-widening PROTOCOL §12.3 forbids.)
"""
from __future__ import annotations

import numpy as np

from domains import paint_world as pw

# The v1.1.0 attributes, pre-seeded to 0.0 for the same reason v1.0.0's are.
_DECAY_ZEROS = ("panchor", "panchor_done", "pdist", "panch_n", "plam")


def add_field(s, lum, app=None, sensed=None, *, pquant: float = 1.0) -> dict:
    """`paint_world.add_field`, plus the v1.1.0 clean-zero initialisation."""
    hnd = pw.add_field(s, lum, app, sensed, pquant=pquant)
    for n in hnd["cells"].values():
        for k in _DECAY_ZEROS:
            s.set_attr(n, k, 0.0)
    return hnd


def set_decay(s, *, pdecay: float) -> None:
    """Blind-write the second flag on every PaintParams node. No read, no
    branch — the mirror of `paint_world.set_flag`."""
    for p in s.nodes("PaintParams"):
        s.set_attr(p, "pdecay", float(pdecay))


def run(s, lum, app=None, sensed=None, *, paint: float, pdecay: float,
        pquant: float = 1.0) -> dict:
    """add_field + both flags + tick, in that order. Pure sequencing."""
    hnd = add_field(s, lum, app, sensed, pquant=pquant)
    pw.set_flag(s, paint=paint)
    set_decay(s, pdecay=pdecay)
    pw.tick(s)
    return hnd


# --- read-outs (pure mechanical queries, no decision) ----------------------- #
def hub_readout(s, nid) -> dict:
    """`paint_world.hub_readout` widened by the v1.1.0 hub attributes."""
    a = s.node(nid)["attrs"]
    out = pw.hub_readout(s, nid)
    out.update({k: float(a.get(k, 0.0)) for k in ("panch_n", "plam")})
    return out


def region_report(s, hnd) -> list[dict]:
    rows = [hub_readout(s, n) for n in pw.hubs(s, hnd)]
    return sorted(rows, key=lambda d: -d["pnall"])


def hub_for(s, hnd, rc) -> dict:
    """The readout of the hub that painted cell `rc`. `pt_hub` and `pt_flood`
    already decided which cell that is; this is a lookup by the region id the
    graph assigned."""
    reg = pw.cell_attr(s, hnd, rc, "pregion")
    by_idx = {float(s.node(n)["attrs"].get("pidx", -1.0)): n
              for n in hnd["cells"].values()}
    n = by_idx.get(reg)
    return hub_readout(s, n) if n is not None else {}


def induction_profile(s, hnd, cells) -> list[dict]:
    """(painted − observed) at a list of (row, col) cells. A subtraction of two
    graph read-backs; the DISTANCE that this profile is plotted against is NOT
    read from the graph (see the runner) — `pdist` is the mechanism's own
    variable and must not be the ruler that measures it."""
    return [{"rc": list(rc),
             "observed": pw.cell_attr(s, hnd, rc, "plum"),
             "painted": pw.cell_attr(s, hnd, rc, "ppaint_lum"),
             "induction": (pw.cell_attr(s, hnd, rc, "ppaint_lum")
                           - pw.cell_attr(s, hnd, rc, "plum"))}
            for rc in cells]


def field_of(s, hnd, key: str) -> np.ndarray:
    return pw.field_of(s, hnd, key)


__all__ = ["add_field", "set_decay", "run", "hub_readout", "region_report",
           "hub_for", "induction_profile", "field_of"]
