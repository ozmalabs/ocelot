"""achromatopsia_world — a world adapter for the CEREBRAL ACHROMATOPSIA
dissociation (VISION_ACHROMATOPSIA_PREREG.md).

Mechanical I/O ONLY (CLAUDE.md / PROTOCOL §0). It builds ONE scene carrying BOTH
colour layers so a single lesion flag can dissociate them:

  * the SALIENCE / chromatic-STRUCTURE layer (seed vision_colour: cc_contrast /
    cc_salience) needs 4-adjacency `neighbour` edges (surround-relative contrast)
    and ColourParams{salience,colour};
  * the categorical-SIGN layer (seed vision_colour_identity: ci_opponent /
    ci_mint_category / ci_assign) needs ColourIdentityParams{identity,achromatopsia}.

The adapter builds cone-cell Regions with the union of both layers' attrs, wires
the grid `neighbour` edges, blind-writes the flags per pre-registered arm, ticks to
a fixpoint, and reads BOTH layers back (csal/lsal/residual = structure; crg/cby =
opponent signal; ColourCategory / sign_* = the categorical sign). It makes NO
percept decision -- the opponent contrast, the MDL-gated minting, the assignment,
and the achromatopsia LESION are ALL seed rules; this file only translates a
cone-cell field into graph nodes and reads attrs out. The `achromatopsia` flag is
GRAPH DATA on a params node (a flag, not a Python code path); the arms differ only
in the flag value written -- fixed pre-registered configuration, never a branch
over graph state.
"""
from __future__ import annotations


def add_field(s, *, cells: list[dict], budget: int = 0) -> dict:
    """Create a Scene{epoch:0, budget, spent:0} + one Region cone-cell per entry of
    `cells`, and wire 4-adjacency `neighbour` edges (grid geometry, for the salience
    layer). Each entry is a dict with integer rrow, rcol, cL, cM, cS.

    Returns {scene, region_ids, meta, index} where index[(rrow,rcol)] -> node id.
    """
    scene = s.add_node("Scene", {"epoch": 0.0, "budget": float(budget), "spent": 0.0})
    region_ids: list = []
    index: dict = {}
    for i, spec in enumerate(cells):
        rrow = int(spec.get("rrow", i // 6))
        rcol = int(spec.get("rcol", i % 6))
        n = s.add_node("Region", {
            "rrow": float(rrow), "rcol": float(rcol), "scale": 0.0,
            "cL": float(spec["cL"]), "cM": float(spec["cM"]), "cS": float(spec["cS"]),
            # salience / structure layer (vision_colour)
            "residual": 0.0, "resolved": 0.0, "order": -1.0,
            "csal": 0.0, "lsal": 0.0, "cc_done": 0.0, "sal_done": 0.0,
            # categorical-sign layer (vision_colour_identity)
            "crg": 0.0, "cby": 0.0, "op_done": 0.0,
            "sign_rg": 0.0, "sign_by": 0.0, "sign_dist": -1.0, "assigned_epoch": -1.0,
        })
        # add_edge_unchecked: EXTERNAL world scaffolding (scene membership + grid
        # geometry), not an agent claim -- exactly like colour_world / vision_lateral.
        s.add_edge_unchecked(scene, "has_region", n)
        region_ids.append(n)
        index[(rrow, rcol)] = n
    # 4-adjacency neighbour edges (both directions) for the surround-relative salience.
    for (r, c), nid in index.items():
        for (dr, dc) in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            m = index.get((r + dr, c + dc))
            if m is not None:
                s.add_edge_unchecked(nid, "neighbour", m)
    return {"scene": scene, "region_ids": region_ids, "meta": list(cells),
            "index": index}


def set_flags(s, *, salience: float, colour: float, identity: float,
              achromatopsia: float) -> None:
    """Blind-write the four flags on the params nodes. No read, no branch -- a fixed
    per-arm configuration written as graph data (PROTOCOL §0)."""
    for p in s.nodes("ColourParams"):
        s.set_attr(p, "salience", float(salience))
        s.set_attr(p, "colour", float(colour))
    for p in s.nodes("ColourIdentityParams"):
        s.set_attr(p, "identity", float(identity))
        s.set_attr(p, "achromatopsia", float(achromatopsia))


def tick(s, max_steps: int = 200_000) -> int:
    """run_rules to a fixpoint. Returns the sweep count."""
    return s.tick(max_steps)


# --- readouts (pure mechanical queries, no decision) ---------------------------
def read_attr(s, handle: dict, key: str) -> list[float]:
    return [float(s.node(n)["attrs"].get(key, 0.0)) for n in handle["region_ids"]]


def cell_attr(s, handle: dict, rrow: int, rcol: int, key: str) -> float:
    return float(s.node(handle["index"][(rrow, rcol)])["attrs"].get(key, 0.0))


def n_categories(s) -> int:
    return len(list(s.nodes("ColourCategory")))


def categories(s) -> list[dict]:
    out = []
    for c in s.nodes("ColourCategory"):
        a = s.node(c)["attrs"]
        out.append({"crg": int(round(float(a.get("crg", 0.0)))),
                    "cby": int(round(float(a.get("cby", 0.0)))),
                    "members": int(round(float(a.get("members", 0.0))))})
    out.sort(key=lambda d: (d["crg"], d["cby"]))
    return out


def n_chromatic_categories(s) -> int:
    """Categories with a NON-ZERO opponent coordinate (an actual colour, not grey)."""
    return sum(1 for c in categories(s) if abs(c["crg"]) + abs(c["cby"]) > 0)


def n_signs_assigned(s, handle: dict) -> int:
    """Cells that received a categorical sign (sign_dist >= 0)."""
    return sum(1 for sd in read_attr(s, handle, "sign_dist") if sd >= 0.0)


def all_signs_correct(s, handle: dict) -> bool:
    """Every cell's sign == its own colour at dist 0 (recognized as own category)."""
    for n in handle["region_ids"]:
        a = s.node(n)["attrs"]
        crg = round(float(a.get("crg", 0.0)))
        cby = round(float(a.get("cby", 0.0)))
        sr = round(float(a.get("sign_rg", 0.0)))
        sb = round(float(a.get("sign_by", 0.0)))
        sd = float(a.get("sign_dist", -1.0))
        if not (sr == crg and sb == cby and abs(sd) < 1e-9):
            return False
    return True


def csal_positive_cells(s, handle: dict) -> list[tuple]:
    """(rrow,rcol) of every cell with csal > 0 -- the chromatic-border ring."""
    out = []
    for n in handle["region_ids"]:
        a = s.node(n)["attrs"]
        if float(a.get("csal", 0.0)) > 0.0:
            out.append((int(round(float(a["rrow"]))), int(round(float(a["rcol"])))))
    return out


def csal_centroid_col(s, handle: dict):
    """Mean column of the csal>0 cells (the colour-defined boundary centroid). None
    if the boundary is empty."""
    cols = [c for (_, c) in csal_positive_cells(s, handle)]
    return (sum(cols) / len(cols)) if cols else None
