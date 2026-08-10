"""colour_identity_world — a world adapter for COLOUR IDENTITY
(VISION_COLOUR_IDENTITY_PREREG.md).

Mechanical I/O ONLY (CLAUDE.md / PROTOCOL §0): builds a Scene + a set of cone cells
(Region nodes with integer cL,cM,cS attrs), blind-writes the OFF-by-default flag,
ticks the substrate to a fixpoint, and reads the minted ColourCategory quanta and
each region's categorical sign back. It makes NO percept decision -- the opponent
recombination, the MDL-gated minting and the nearest-quantum assignment are ALL in
the vision_colour_identity seed rules; this file only translates a cone-cell field
into graph nodes and reads attrs out.

Supplying cL,cM,cS per cell is mechanical ingest -- exactly like colour_world. The
adapter never computes or interprets an opponent coordinate, a cluster, or a sign.
No `neighbour` edges are wired: colour identity is a per-cell VALUE categorization,
not a surround-relative computation (that was salience).
"""
from __future__ import annotations


def add_field(s, *, cells: list[dict]) -> dict:
    """Create a Scene{epoch:0} + one Region cone-cell per entry of `cells`.

    Each `cells` entry is a dict with integer `cL`, `cM`, `cS` (and optional
    `rrow`,`rcol` for readback bookkeeping). Returns
    {scene, region_ids, meta, index} where index[(rrow,rcol)] -> node id.
    """
    scene = s.add_node("Scene", {"epoch": 0.0})
    region_ids: list = []
    index: dict = {}
    for i, spec in enumerate(cells):
        rrow = int(spec.get("rrow", 0))
        rcol = int(spec.get("rcol", i))
        n = s.add_node("Region", {
            "rrow": float(rrow),
            "rcol": float(rcol),
            "cL": float(spec["cL"]),
            "cM": float(spec["cM"]),
            "cS": float(spec["cS"]),
            "crg": 0.0,
            "cby": 0.0,
            "op_done": 0.0,
            "sign_rg": 0.0,
            "sign_by": 0.0,
            "sign_dist": -1.0,
            "assigned_epoch": -1.0,
        })
        # add_edge_unchecked: EXTERNAL world scaffolding (scene membership), not an
        # agent claim -- bypasses Γ exactly like colour_world / vision_lateral.
        s.add_edge_unchecked(scene, "has_region", n)
        region_ids.append(n)
        index[(rrow, rcol)] = n
    return {"scene": scene, "region_ids": region_ids, "meta": list(cells),
            "index": index}


def add_region(s, handle: dict, spec: dict) -> int:
    """Add ONE more Region cone-cell to an existing scene (for the
    recognize-not-re-mint arm: a NEW instance of a seen colour). Mechanical."""
    rrow = int(spec.get("rrow", 0))
    rcol = int(spec.get("rcol", len(handle["region_ids"])))
    n = s.add_node("Region", {
        "rrow": float(rrow), "rcol": float(rcol),
        "cL": float(spec["cL"]), "cM": float(spec["cM"]), "cS": float(spec["cS"]),
        "crg": 0.0, "cby": 0.0, "op_done": 0.0,
        "sign_rg": 0.0, "sign_by": 0.0, "sign_dist": -1.0, "assigned_epoch": -1.0,
    })
    s.add_edge_unchecked(handle["scene"], "has_region", n)
    handle["region_ids"].append(n)
    handle["index"][(rrow, rcol)] = n
    return n


def set_flag(s, *, identity: float) -> None:
    """Blind-write the flag on every ColourIdentityParams node. No read, no branch."""
    for p in s.nodes("ColourIdentityParams"):
        s.set_attr(p, "identity", float(identity))


def tick(s, max_steps: int = 200_000) -> int:
    """run_rules to a fixpoint. Returns the sweep count."""
    return s.tick(max_steps)


# --- readouts (pure mechanical queries, no decision) ---------------------------
def n_categories(s) -> int:
    return len(list(s.nodes("ColourCategory")))


def categories(s) -> list[dict]:
    """Every minted ColourCategory as {crg,cby,members} (sorted for stable output)."""
    out = []
    for c in s.nodes("ColourCategory"):
        a = s.node(c)["attrs"]
        out.append({"crg": int(round(float(a.get("crg", 0.0)))),
                    "cby": int(round(float(a.get("cby", 0.0)))),
                    "members": int(round(float(a.get("members", 0.0))))})
    out.sort(key=lambda d: (d["crg"], d["cby"]))
    return out


def cell_attr(s, handle: dict, rrow: int, rcol: int, key: str) -> float:
    return float(s.node(handle["index"][(rrow, rcol)])["attrs"].get(key, 0.0))


def region_attr(s, nid: int, key: str) -> float:
    return float(s.node(nid)["attrs"].get(key, 0.0))


def read_attr(s, handle: dict, key: str) -> list[float]:
    """Per-cell value of a computed attr, in cell order."""
    return [float(s.node(n)["attrs"].get(key, 0.0)) for n in handle["region_ids"]]


def signs(s, handle: dict) -> list[tuple]:
    """Per-cell (sign_rg, sign_by, sign_dist) in cell order."""
    out = []
    for n in handle["region_ids"]:
        a = s.node(n)["attrs"]
        out.append((int(round(float(a.get("sign_rg", 0.0)))),
                    int(round(float(a.get("sign_by", 0.0)))),
                    float(a.get("sign_dist", -1.0))))
    return out


def scene_epoch(s, handle: dict) -> int:
    return int(round(float(s.node(handle["scene"])["attrs"].get("epoch", 0.0))))
