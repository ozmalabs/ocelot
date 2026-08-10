"""category_world — a world adapter for CATEGORY-LEVEL RECOGNITION
(VISION_CATEGORY_PREREG.md).

Mechanical I/O ONLY (CLAUDE.md / PROTOCOL §0): builds a Scene + a set of ObjItem
nodes (each an integer axis coordinate: a DISCRETE part-signature d0,d1 and
CONTINUOUS proportion axes v0,v1, plus a creation-order oidx for the
canonical-representative mint guard), blind-writes the OFF-by-default flag, ticks
the substrate to a fixpoint, and reads the minted ObjCategory regions and each
item's recognition attrs back. It makes NO percept decision — the MDL-gated minting,
the region box, the containment recognition and the memorization control are ALL in
the vision_category seed rules (cat_mint / cat_recognize / cat_memorize); this file
only translates an axis-coordinate field into graph nodes and reads attrs out.

Supplying (d0,d1,v0,v1) per item is mechanical ingest — exactly like colour_world
supplies (cL,cM,cS). The adapter never computes or interprets a cluster, a region or
a recognition. A ground-truth `label` may be attached for the RUNNER's train/test
bookkeeping and scoring, but it is NEVER read by any seed rule (minting is
unsupervised).
"""
from __future__ import annotations


def add_field(s, *, items: list[dict]) -> dict:
    """Create a Scene + one ObjItem per entry of `items`.

    Each entry is a dict with integer d0,d1 (discrete signature) and v0,v1
    (continuous axes); optional `label` (runner bookkeeping only). Returns a handle
    {scene, item_ids, next_oidx, meta}. oidx is assigned in creation order (global
    monotonic) — the canonical-representative key the mint rule uses.
    """
    scene = s.add_node("Scene", {"epoch": 0.0})
    handle = {"scene": scene, "item_ids": [], "next_oidx": 0, "meta": []}
    for spec in items:
        add_obj(s, handle, spec)
    return handle


def add_obj(s, handle: dict, spec: dict) -> int:
    """Add ONE ObjItem to a scene (used for held-out test instances added AFTER
    minting). Mechanical. Returns the node id."""
    oidx = handle["next_oidx"]
    handle["next_oidx"] = oidx + 1
    n = s.add_node("ObjItem", {
        "d0": float(spec["d0"]), "d1": float(spec["d1"]),
        "v0": float(spec["v0"]), "v1": float(spec["v1"]),
        "oidx": float(oidx),
        # readback / recognition attrs, neutral init:
        "cat_recognized": 0.0, "cat_sig0": -1.0, "cat_sig1": -1.0,
        "mem_recognized": 0.0,
    })
    # add_edge_unchecked: EXTERNAL world scaffolding (scene membership), not an agent
    # claim — bypasses Γ exactly like colour_identity_world / colour_world.
    s.add_edge_unchecked(handle["scene"], "has_obj", n)
    handle["item_ids"].append(n)
    handle["meta"].append(dict(spec))
    return n


def set_flag(s, *, identity: float) -> None:
    """Blind-write the flag on every CategoryParams node. No read, no branch."""
    for p in s.nodes("CategoryParams"):
        s.set_attr(p, "identity", float(identity))


def tick(s, max_steps: int = 200_000) -> int:
    """run_rules to a fixpoint. Returns the sweep count."""
    return s.tick(max_steps)


# --- readouts (pure mechanical queries, no decision) ---------------------------
def n_categories(s) -> int:
    return len(list(s.nodes("ObjCategory")))


def categories(s) -> list[dict]:
    """Every minted ObjCategory as its signature + box + members (sorted)."""
    out = []
    for c in s.nodes("ObjCategory"):
        a = s.node(c)["attrs"]
        out.append({
            "d0": int(round(float(a.get("d0", 0.0)))),
            "d1": int(round(float(a.get("d1", 0.0)))),
            "members": int(round(float(a.get("members", 0.0)))),
            "v0lo": int(round(float(a.get("v0lo", 0.0)))),
            "v0hi": int(round(float(a.get("v0hi", 0.0)))),
            "v1lo": int(round(float(a.get("v1lo", 0.0)))),
            "v1hi": int(round(float(a.get("v1hi", 0.0)))),
            "ex_v0": int(round(float(a.get("ex_v0", 0.0)))),
            "ex_v1": int(round(float(a.get("ex_v1", 0.0)))),
        })
    out.sort(key=lambda d: (d["d0"], d["d1"]))
    return out


def obj_attr(s, nid: int, key: str) -> float:
    return float(s.node(nid)["attrs"].get(key, 0.0))


def recognition(s, nid: int) -> dict:
    """The recognition readback for one ObjItem (mechanical)."""
    a = s.node(nid)["attrs"]
    return {
        "d0": int(round(float(a.get("d0", 0.0)))),
        "d1": int(round(float(a.get("d1", 0.0)))),
        "v0": int(round(float(a.get("v0", 0.0)))),
        "v1": int(round(float(a.get("v1", 0.0)))),
        "cat_recognized": int(round(float(a.get("cat_recognized", 0.0)))),
        "cat_sig0": int(round(float(a.get("cat_sig0", -1.0)))),
        "cat_sig1": int(round(float(a.get("cat_sig1", -1.0)))),
        "mem_recognized": int(round(float(a.get("mem_recognized", 0.0)))),
    }
