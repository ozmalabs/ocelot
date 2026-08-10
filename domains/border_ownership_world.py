"""border_ownership_world — a world adapter for BORDER-OWNERSHIP / PROTO-OBJECT
(VISION_BORDER_OWNERSHIP_PREREG.md).

Mechanical I/O ONLY (CLAUDE.md / PROTOCOL §0): builds a Field + a grid of Cell nodes
(integer val, frame flag, stable cid), wires the 4-neighbour `neighbour` edges,
blind-writes the OFF-by-default flag, ticks the substrate to a fixpoint (run_rules),
and reads the flood/ownership/proto results back. It makes NO percept decision -- the
surroundedness flood, the component labelling, the figure/ground DECISION, the
proto-object minting and the directed ownership are ALL in seeds/vision_border_ownership
.json's rules; this file only translates a value grid into graph nodes/edges and reads
attrs and owns_figure edges out.

A `val` here is the observed luminance (an integer, mechanical ingest -- exactly like
vision_ground's gobs / colour_world's cones). The adapter never computes bg, glabel,
figure, a proto, or an owner.
"""
from __future__ import annotations
from typing import Optional


def add_field(s, grid: list[list[int]]) -> dict:
    """Create a Field + one Cell per grid entry (grid[r][c] = integer val), with
    frame=1 on the border, cid=r*W+c, and 4-neighbour `neighbour` edges. Returns a
    handle {field, cell_ids, index, H, W} -- index[(r,c)] -> node id."""
    H = len(grid)
    W = len(grid[0])
    field = s.add_node("Field", {"H": float(H), "W": float(W)})
    index: dict = {}
    cell_ids: list = []
    for r in range(H):
        for c in range(W):
            frame = 1.0 if (r == 0 or r == H - 1 or c == 0 or c == W - 1) else 0.0
            n = s.add_node("Cell", {
                "crow": float(r), "ccol": float(c),
                "val": float(grid[r][c]),
                "frame": frame,
                "cid": float(r * W + c),
                "bg": 0.0,
                "glabel": float(r * W + c),   # init = own cid
                "owns": 0.0,
                # rim = the component's own contour length in cells, MATERIALISED
                # by bo_rim (v1.1.0). Initialised to 0 exactly like bg/owns, so a
                # gate that reads it before bo_rim fires reads 0 and REFUSES --
                # rims can only turn a refusal into a mint, never the reverse.
                # No rule reads `rim` while bown_own is at its 0.0 default, so the
                # incumbent path is unaffected (§9).
                "rim": 0.0,
            })
            # add_edge_unchecked: EXTERNAL world scaffolding (grid membership +
            # 4-neighbourhood), not an agent claim -- bypasses Γ exactly like
            # vision_ground / colour_world / stream_world.
            s.add_edge_unchecked(field, "has_cell", n)
            index[(r, c)] = n
            cell_ids.append(n)
    # wire the 4-neighbourhood (undirected: both directions)
    for r in range(H):
        for c in range(W):
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                rr, cc = r + dr, c + dc
                if 0 <= rr < H and 0 <= cc < W:
                    s.add_edge_unchecked(index[(r, c)], "neighbour", index[(rr, cc)])
    return {"field": field, "cell_ids": cell_ids, "index": index, "H": H, "W": W}


def set_flag(s, *, bown: float, bown_own: float = 0.0,
             bown_wp: float = 0.0, bown_nest: float = 0.0) -> None:
    """Blind-write the flags on every BorderOwnParams node. No read, no branch.

    `bown_own` selects WHICH mint predicate is armed (v1.1.0): 0.0 = the
    incumbent `bo_mint_enclosed` (isolation / G_figadj), 1.0 = the competitive
    `bo_mint_owned` (a shared border is ASSIGNED, not disqualifying). The two
    are mutually exclusive in the seed, so exactly one is ever live. Defaults to
    the incumbent, so every existing caller is byte-identical (§9).

    `bown_wp` (v1.2.0) arms the WELL-POSEDNESS conjunct inside `bo_mint_owned`:
    a competition whose shared border is claimed in full by two rivals at once
    is HELD OPEN, exactly as a tie is. Defaults to 0.0, so the committed v1.1.0
    replacement result reproduces byte-identically (§9).

    `bown_nest` (v1.3.0) scopes the RIVAL SET of both the ownership comparison
    and the well-posedness conjunct to R's OUTER CONTOUR: a component R
    ENCLOSES is not a competitor for R's figurehood, because that border is the
    contour of R's own hole, not of R. Defaults to 0.0, so the committed v1.2.0
    well-posed result reproduces byte-identically (§9)."""
    for p in s.nodes("BorderOwnParams"):
        s.set_attr(p, "bown", float(bown))
        s.set_attr(p, "bown_own", float(bown_own))
        s.set_attr(p, "bown_wp", float(bown_wp))
        s.set_attr(p, "bown_nest", float(bown_nest))


def tick(s, max_steps: int = 200_000) -> int:
    """run_rules to a joint fixpoint. Returns the sweep count (the recurrence depth)."""
    return s.tick(max_steps)


# --- readouts (pure mechanical queries, no decision) ---------------------------
def cell_attr(s, handle: dict, r: int, c: int, key: str) -> float:
    return float(s.node(handle["index"][(r, c)])["attrs"].get(key, 0.0))


def owns(s, handle: dict, r: int, c: int) -> int:
    return int(round(cell_attr(s, handle, r, c, "owns")))


def bg(s, handle: dict, r: int, c: int) -> int:
    return int(round(cell_attr(s, handle, r, c, "bg")))


def n_protos(s) -> int:
    return len(list(s.nodes("ProtoObject")))


def protos(s) -> list[dict]:
    """Every minted ProtoObject as {root, members, gestalt} (sorted for stable out)."""
    out = []
    for p in s.nodes("ProtoObject"):
        a = s.node(p)["attrs"]
        out.append({"root": int(round(float(a.get("root", -1.0)))),
                    "members": int(round(float(a.get("members", 0.0)))),
                    "gestalt": int(round(float(a.get("gestalt", 0.0))))})
    out.sort(key=lambda d: d["root"])
    return out


def owns_figure_target(s, handle: dict, r: int, c: int) -> Optional[int]:
    """The ProtoObject.root this cell's owns_figure edge points at (or None). Reads the
    directed owns_figure edge via the substrate's own neighbours(edge_type) query."""
    nid = handle["index"][(r, c)]
    tgts = s.neighbours(nid, "owns_figure")
    if not tgts:
        return None
    return int(round(float(s.node(tgts[0])["attrs"].get("root", -1.0))))


def owned_proto_roots(s, handle: dict) -> set[int]:
    """The set of DISTINCT ProtoObject roots owned by any cell in the field (for the
    global-consistency / recurrence arm)."""
    roots: set[int] = set()
    for nid in handle["cell_ids"]:
        for tgt in s.neighbours(nid, "owns_figure"):
            roots.add(int(round(float(s.node(tgt)["attrs"].get("root", -1.0)))))
    return roots
