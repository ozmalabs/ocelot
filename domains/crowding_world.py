"""crowding_world — a world adapter for CROWDING / eccentricity-scaled pooling
(VISION_CROWDING_PREREG.md).

Mechanical I/O ONLY (CLAUDE.md / PROTOCOL §0): builds a CrowdField + CrowdItem nodes at
integer positions, wires the LOCAL `co_item` 2-clique among same-field items (external
scaffolding, exactly like border_ownership's 4-neighbour wiring — NOT an agent claim),
blind-writes the OFF-by-default flag, ticks the substrate to a fixpoint (run_rules), and
reads pool_n / recognized / crowded / pooled_ident back.

It makes NO percept decision — the eccentricity, the pooling radius, the pool membership,
the summary statistic and the recognized/crowded verdict are ALL in seeds/vision_crowding
.json's rules (cr_ecc / cr_pool). This file only translates item positions into graph
nodes/edges and reads attrs out.
"""
from __future__ import annotations


def add_field(s, items: list[dict], *, gaze=(0, 0)) -> dict:
    """Create a CrowdField (fixation at `gaze`) + one CrowdItem per `items` entry.

    Each item dict: {irow, icol, ident, is_target(optional)}. `iid` is assigned by
    order. Wires field -has_item-> item, and item -co_item-> other for every ORDERED
    pair of distinct same-field items (both directions; NO self-loop). Returns a handle
    {field, item_ids, targets}.
    """
    field = s.add_node("CrowdField",
                       {"gaze_row": float(gaze[0]), "gaze_col": float(gaze[1])})
    item_ids: list = []
    targets: list = []
    for i, it in enumerate(items):
        is_t = 1.0 if it.get("is_target") else 0.0
        n = s.add_node("CrowdItem", {
            "irow": float(it["irow"]), "icol": float(it["icol"]),
            "ident": float(it["ident"]),
            "iid": float(i), "is_target": is_t,
            # readout attrs pre-seeded so an OFF run reads a clean 0 (no KeyError):
            "ecc2": 0.0, "pool_radius2": 0.0, "ecc_done": 0.0, "pool_done": 0.0,
            "pool_n": 0.0, "n_flank_in_pool": 0.0, "pooled_ident": 0.0,
            "crowded": 0.0, "recognized": 0.0,
        })
        # add_edge_unchecked: EXTERNAL world scaffolding, bypasses Γ exactly like
        # border_ownership / vision_ground / colour_world.
        s.add_edge_unchecked(field, "has_item", n)
        item_ids.append(n)
        if is_t:
            targets.append(n)
    # LOCAL co_item 2-clique (both directions, no self-loop) — the pool's neighbourhood.
    for a in range(len(item_ids)):
        for b in range(len(item_ids)):
            if a != b:
                s.add_edge_unchecked(item_ids[a], "co_item", item_ids[b])
    return {"field": field, "item_ids": item_ids, "targets": targets}


def set_flag(s, *, crowd: float, bouma: float | None = None) -> None:
    """Blind-write the flag (and optional bouma scale) on every CrowdParams node.
    No read, no branch."""
    for p in s.nodes("CrowdParams"):
        s.set_attr(p, "crowd", float(crowd))
        if bouma is not None:
            s.set_attr(p, "bouma", float(bouma))


def tick(s, max_steps: int = 200_000) -> int:
    """run_rules to a joint fixpoint. Returns the sweep count."""
    return s.tick(max_steps)


# --- readouts (pure mechanical queries, no decision) -------------------------------
def item_attr(s, nid, key: str) -> float:
    return float(s.node(nid)["attrs"].get(key, 0.0))


def target_readout(s, handle: dict) -> dict:
    """The first target item's pooling readout as a plain dict (mechanical query)."""
    nid = handle["targets"][0]
    a = s.node(nid)["attrs"]
    return {k: float(a.get(k, 0.0)) for k in
            ("ecc2", "pool_radius2", "pool_n", "n_flank_in_pool",
             "pooled_ident", "crowded", "recognized")}


def recognized(s, handle: dict) -> int:
    return int(round(item_attr(s, handle["targets"][0], "recognized")))


def crowded(s, handle: dict) -> int:
    return int(round(item_attr(s, handle["targets"][0], "crowded")))
