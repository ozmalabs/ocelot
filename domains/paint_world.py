"""paint_world — the world adapter for PAINT-FROM-SAMPLE (VISION_PAINT_PREREG.md).

Mechanical I/O ONLY (CLAUDE.md / PROTOCOL §0), exactly like `crowding_world` and
`ground_world`:

  1. LAY OUT the field — a PaintField hub and one PaintCell per integer (row, col),
     wired 4-connected by `neighbour` edges. External scaffolding, not an agent
     claim.
  2. STATE the stimulus — write `plum` (luminance, the STRUCTURE channel) and
     `papp` (appearance, the SIGN channel) and `psensed` (0 in an optic disc).
  3. BLIND-WRITE the OFF-by-default flag.
  4. TICK — `run_rules` to a fixpoint.
  5. READ BACK — pure queries.

There is NO decision here. There is no `if paint`, no boundary test, no region
assignment, no order selection: the boundary, the region, the sample, the paint,
the residual and the order k are ALL rules in `seeds/vision_paint.json`. A
source-grep gate in `tests/test_paint_migrated.py` enforces it.

The stimuli are INTEGER-valued because that is what grounding IS (CLAUDE.md's
frame/continuum invariant: in-frame is INTEGER; the paint is a cross-frame
rendering and may be real). `pquant` is the field's alphabet step, stated with the
stimulus, not tuned.
"""
from __future__ import annotations

import numpy as np

# Attributes pre-seeded to 0.0 so an OFF run reads a clean zero (no KeyError) and
# so §9's inertness is readable rather than inferred.
_CELL_ZEROS = (
    "pd_e", "pd_s", "pd_has_e", "pd_has_s", "pdelta_done",
    "pblk_e", "pblk_s", "pblock_done", "pseed_done", "pregion",
    "pn", "pnall", "pmean_lum", "pmean_app", "pcen_r", "pcen_c",
    "pvar_r", "pvar_c",
    "pslope_r_plum", "pslope_c_plum", "pslope_r_papp", "pslope_c_papp",
    "ppaint_lum", "ppaint_app", "pkorder_seen",
    "presid_lum", "presid_app", "prefuted_cell", "presid_order",
    "prefuted", "presid_mean", "pverdict_done", "phub",
)


def add_field(s, lum, app=None, sensed=None, *, pquant: float = 1.0) -> dict:
    """Build a PaintField + PaintCell grid from integer arrays.

    `lum` (h, w) is the luminance/structure channel; `app` the appearance/sign
    channel (default all-zero); `sensed` a 0/1 mask (default all-sensed — a 0
    marks an optic disc, a cell that never receives data).

    `korder` is initialised to 1.0 — the BOTTOM of the ladder, i.e. paint flat
    first. It is assigned nowhere else in this file; `pt_escalate` is the only
    writer thereafter.
    """
    lum = np.asarray(lum, dtype=np.float64)
    h, w = lum.shape
    app = np.zeros((h, w)) if app is None else np.asarray(app, dtype=np.float64)
    sensed = np.ones((h, w)) if sensed is None else np.asarray(sensed, dtype=np.float64)

    field = s.add_node("PaintField", {"prows": float(h), "pcols": float(w),
                                      "pquant": float(pquant)})
    cells: dict[tuple[int, int], object] = {}
    for r in range(h):
        for c in range(w):
            attrs = {"prow": float(r), "pcol": float(c),
                     "pidx": float(r * w + c),
                     # NO DATA in an optic disc: an unsensed cell carries zero
                     # on both channels, exactly as ground_world writes nothing
                     # there. Passing the scene value through would leak the
                     # observation the hole is defined by not having.
                     "plum": float(lum[r, c]) * float(sensed[r, c]),
                     "papp": float(app[r, c]) * float(sensed[r, c]),
                     "psensed": float(sensed[r, c]),
                     "korder": 1.0}
            attrs.update({k: 0.0 for k in _CELL_ZEROS})
            n = s.add_node("PaintCell", attrs)
            # add_edge_unchecked: EXTERNAL world scaffolding, exactly as
            # crowding_world / ground_world / colour_world do.
            s.add_edge_unchecked(field, "has_pcell", n)
            cells[(r, c)] = n
    for (r, c), n in cells.items():
        for dr, dc in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            m = cells.get((r + dr, c + dc))
            if m is not None:
                s.add_edge_unchecked(n, "neighbour", m)
    return {"field": field, "cells": cells, "h": h, "w": w}


def set_flag(s, *, paint: float) -> None:
    """Blind-write the flag on every PaintParams node. No read, no branch."""
    for p in s.nodes("PaintParams"):
        s.set_attr(p, "paint", float(paint))


def tick(s, max_steps: int = 200_000) -> int:
    """run_rules to a joint fixpoint. Returns the sweep count."""
    return s.tick(max_steps)


def run(s, lum, app=None, sensed=None, *, paint: float, pquant: float = 1.0) -> dict:
    """add_field + set_flag + tick, in that order. Pure sequencing."""
    hnd = add_field(s, lum, app, sensed, pquant=pquant)
    set_flag(s, paint=paint)
    tick(s)
    return hnd


# --- read-outs (pure mechanical queries, no decision) ----------------------- #
def field_of(s, hnd, key: str) -> np.ndarray:
    a = np.zeros((hnd["h"], hnd["w"]), np.float64)
    for (r, c), n in hnd["cells"].items():
        a[r, c] = float(s.node(n)["attrs"].get(key, 0.0))
    return a


def cell_attr(s, hnd, rc, key: str) -> float:
    return float(s.node(hnd["cells"][rc])["attrs"].get(key, 0.0))


def hubs(s, hnd) -> list:
    """Every region representative, read off the `phub` flag that `pt_hub` wrote.
    A pure query: this file does not work out WHICH cell is a hub — the graph
    decided that and said so."""
    return [n for n in hnd["cells"].values()
            if float(s.node(n)["attrs"].get("phub", 0.0)) > 0.5]


def hub_readout(s, nid) -> dict:
    a = s.node(nid)["attrs"]
    return {k: float(a.get(k, 0.0)) for k in
            ("pidx", "pregion", "pn", "pnall", "korder", "prefuted",
             "presid_mean", "pmean_lum", "pmean_app",
             "pslope_r_plum", "pslope_c_plum", "pslope_r_papp", "pslope_c_papp")}


def region_report(s, hnd) -> list[dict]:
    """One row per region, sorted by size. Pure query."""
    rows = [hub_readout(s, n) for n in hubs(s, hnd)]
    return sorted(rows, key=lambda d: -d["pnall"])


def hub_for(s, hnd, rc) -> dict:
    """The readout of the hub that painted cell `rc`. Pure query: `pt_paint`
    already recorded the code it used, so this is a lookup by the region id the
    graph assigned, not a search this file reasons about."""
    reg = cell_attr(s, hnd, rc, "pregion")
    by_idx = {float(s.node(n)["attrs"].get("pidx", -1.0)): n
              for n in hnd["cells"].values()}
    n = by_idx.get(reg)
    return hub_readout(s, n) if n is not None else {}


__all__ = ["add_field", "set_flag", "tick", "run", "field_of", "cell_attr",
           "hubs", "hub_readout", "region_report", "hub_for"]
