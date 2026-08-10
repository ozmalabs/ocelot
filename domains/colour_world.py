"""colour_world — a world adapter for COLOUR SALIENCE (VISION_COLOUR_PREREG.md).

Mechanical I/O ONLY (CLAUDE.md / PROTOCOL §0): builds a Scene + a grid of cone
cells (Region nodes with integer cL,cM,cS attrs), wires 4-adjacency `neighbour`
edges as grid geometry, blind-writes the OFF-by-default flags, ticks the substrate
to a fixpoint, and reads the stream order / computed salience back. It makes NO
percept decision -- the opponent-contrast computation, the interactive combine and
the salience ordering are ALL in seeds (vision_colour + vision_stream); this file
only translates a cone-cell field into graph nodes and reads attrs out.

Supplying cL,cM,cS per cell is mechanical ingest -- exactly like supplying
luminance. The adapter never computes or interprets opponent contrast.
"""
from __future__ import annotations


def add_field(s, *, budget: int, cells: list[dict], nrows: int, ncols: int) -> dict:
    """Create a Scene{budget, spent:0} + one Region cone-cell per entry of `cells`,
    laid out on an (nrows x ncols) grid, and wire 4-adjacency `neighbour` edges.

    Each `cells` entry is a dict with integer `rrow`, `rcol`, `cL`, `cM`, `cS`
    (and optional `scale`). Returns {scene, region_ids, meta, index} where
    index[(rrow,rcol)] -> node id.
    """
    scene = s.add_node("Scene", {"budget": float(budget), "spent": 0.0})
    region_ids: list = []
    index: dict = {}
    for spec in cells:
        n = s.add_node("Region", {
            "rrow": float(spec["rrow"]),
            "rcol": float(spec["rcol"]),
            "scale": float(spec.get("scale", 0)),
            "cL": float(spec["cL"]),
            "cM": float(spec["cM"]),
            "cS": float(spec["cS"]),
            "residual": 0.0,
            "resolved": 0.0,
            "order": -1.0,
            "csal": 0.0,
            "lsal": 0.0,
            "cc_done": 0.0,
            "sal_done": 0.0,
        })
        # add_edge_unchecked: EXTERNAL world scaffolding (grid geometry), not an
        # agent claim -- bypasses Γ exactly like vision_lateral wires `neighbour`
        # and space_quantize wires portals (host-owned bookkeeping).
        s.add_edge_unchecked(scene, "has_region", n)
        region_ids.append(n)
        index[(int(spec["rrow"]), int(spec["rcol"]))] = n
    # 4-adjacency neighbour edges (both directions), grid geometry.
    for (r, c), nid in index.items():
        for (dr, dc) in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            m = index.get((r + dr, c + dc))
            if m is not None:
                s.add_edge_unchecked(nid, "neighbour", m)
    return {"scene": scene, "region_ids": region_ids, "meta": list(cells),
            "index": index, "nrows": nrows, "ncols": ncols}


def set_flags(s, *, salience: float, colour: float) -> None:
    """Blind-write the two flags on every ColourParams node. No read, no branch."""
    for p in s.nodes("ColourParams"):
        s.set_attr(p, "salience", float(salience))
        s.set_attr(p, "colour", float(colour))


def set_stream(s, stream: float = 1.0) -> None:
    """Blind-write the vision_stream flag on every StreamParams node."""
    for p in s.nodes("StreamParams"):
        s.set_attr(p, "stream", float(stream))


def tick(s, max_steps: int = 200_000) -> int:
    """run_rules to a fixpoint. Returns the sweep count."""
    return s.tick(max_steps)


def read_order(s, handle: dict) -> list[int]:
    out = []
    for n in handle["region_ids"]:
        out.append(int(round(float(s.node(n)["attrs"].get("order", -1.0)))))
    return out


def read_attr(s, handle: dict, key: str) -> list[float]:
    """Per-cell value of a computed attr (csal / lsal / residual), in cell order."""
    return [float(s.node(n)["attrs"].get(key, 0.0)) for n in handle["region_ids"]]


def read_spent(s, handle: dict) -> int:
    return int(round(float(s.node(handle["scene"])["attrs"].get("spent", 0.0))))


def cell_attr(s, handle: dict, rrow: int, rcol: int, key: str) -> float:
    """A single cell's attr by grid coordinate (measurement, no decision)."""
    return float(s.node(handle["index"][(rrow, rcol)])["attrs"].get(key, 0.0))


def cell_order(s, handle: dict, rrow: int, rcol: int) -> int:
    return int(round(cell_attr(s, handle, rrow, rcol, "order")))
