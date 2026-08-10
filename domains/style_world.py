"""style_world — a world adapter for STYLE AS A DISCOVERED DIMENSION
(VISION_STYLE_PREREG.md).

Mechanical I/O ONLY (CLAUDE.md / PROTOCOL §0): builds a Scene, a set of ObjSource
nodes, and one ObjItem per instance (each an INTEGER axis coordinate: a DISCRETE
part-signature d0,d1 and CONTINUOUS proportion axes v0,v1, plus a creation-order oidx
for the canonical-representative mint guard), wires `Scene -has_obj-> ObjItem` and
`ObjSource -produced-> ObjItem`, blind-writes the OFF-by-default flag, ticks the
substrate to a fixpoint, and reads the minted ObjStyle nodes and each item's
projection / recognition attrs back.

It makes NO percept decision. The within-category projection, the per-source
coherence test, the axis discovery, the minting, the source-blind recognition and the
memorization control are ALL in the vision_style seed rules (sty_project /
sty_mint_a0 / sty_mint_a1 / sty_recognize_a0 / sty_recognize_a1 / sty_memorize); this
file only translates a sourced axis-coordinate field into graph nodes and reads attrs
out.

Supplying (d0,d1,v0,v1) per item is mechanical ingest, exactly as category_world does
it; supplying the SOURCE is likewise mechanical — which hand produced an instance is
an OBSERVABLE of the world (the writer rung's `Writer -wrote_transform-> Transform`
edge is the same fact), NOT a category label. No seed rule reads any ground-truth
`kind` or `style` field; those may be attached to the runner's own bookkeeping dicts
for scoring and are never written into the graph.

NOTE (engine gotcha, CLAUDE.md): two incoming edges of the SAME type on one node can
break rule matching for that edge type. `has_obj` (from the Scene) and `produced`
(from the ObjSource) are DELIBERATELY different types, and item liveness (`dv_set`) is
reported by the runner so an under-counted pool would be visible rather than silent.
"""
from __future__ import annotations


def add_scene(s) -> dict:
    """Create an empty Scene handle. Mechanical."""
    scene = s.add_node("Scene", {"epoch": 0.0})
    return {"scene": scene, "item_ids": [], "next_oidx": 0, "sources": {}, "meta": []}


def add_source(s, handle: dict, sid: int) -> int:
    """Create (or return) the ObjSource node for source id `sid`. Mechanical."""
    if sid in handle["sources"]:
        return handle["sources"][sid]
    n = s.add_node("ObjSource", {"sid": float(sid)})
    handle["sources"][sid] = n
    return n


def add_obj(s, handle: dict, spec: dict) -> int:
    """Add ONE ObjItem produced by ObjSource `spec['src']`. Mechanical. Returns the
    node id. oidx is assigned in creation order (global monotonic) — the
    canonical-representative key the mint rules use."""
    oidx = handle["next_oidx"]
    handle["next_oidx"] = oidx + 1
    n = s.add_node("ObjItem", {
        "d0": float(spec["d0"]), "d1": float(spec["d1"]),
        "v0": float(spec["v0"]), "v1": float(spec["v1"]),
        "oidx": float(oidx),
        # T2 readback attrs, neutral init (category_world's contract):
        "cat_recognized": 0.0, "cat_sig0": -1.0, "cat_sig1": -1.0,
        "mem_recognized": 0.0,
        # T5 projection / recognition attrs, neutral init:
        "dv0": 0.0, "dv1": 0.0, "dv_set": 0.0,
        "sty_recognized_a0": 0.0, "sty_src_a0": -1.0,
        "sty_recognized_a1": 0.0, "sty_src_a1": -1.0,
        "sty_mem_recognized": 0.0,
    })
    # add_edge_unchecked: EXTERNAL world scaffolding (scene membership, and which
    # source produced the instance), not an agent claim — bypasses Γ exactly like
    # category_world / colour_identity_world.
    s.add_edge_unchecked(handle["scene"], "has_obj", n)
    src = add_source(s, handle, int(spec["src"]))
    s.add_edge_unchecked(src, "produced", n)
    handle["item_ids"].append(n)
    handle["meta"].append(dict(spec))
    return n


def add_field(s, *, items: list[dict]) -> dict:
    """Create a Scene + one ObjItem per entry of `items` (each carrying `src`)."""
    handle = add_scene(s)
    for spec in items:
        add_obj(s, handle, spec)
    return handle


def set_flag(s, *, style: float, identity: float | None = None) -> None:
    """Blind-write the flags. No read, no branch. `identity` is T2's CategoryParams
    flag (categories must be minted for styles to have a frame); left alone if None."""
    for p in s.nodes("StyleParams"):
        s.set_attr(p, "style", float(style))
    if identity is not None:
        for p in s.nodes("CategoryParams"):
            s.set_attr(p, "identity", float(identity))


def tick(s, max_steps: int = 200_000) -> int:
    """run_rules to a fixpoint. Returns the sweep count."""
    return s.tick(max_steps)


# --- readouts (pure mechanical queries, no decision) ---------------------------
def n_styles(s) -> int:
    return len(list(s.nodes("ObjStyle")))


def n_categories(s) -> int:
    return len(list(s.nodes("ObjCategory")))


def styles(s) -> list[dict]:
    """Every minted ObjStyle as its source + DISCOVERED axis + delta (sorted)."""
    out = []
    for n in s.nodes("ObjStyle"):
        a = s.node(n)["attrs"]
        out.append({
            "src": int(round(float(a.get("src", -1.0)))),
            "axis": int(round(float(a.get("axis", -1.0)))),
            "delta": int(round(float(a.get("delta", 0.0)))),
            "members": int(round(float(a.get("members", 0.0)))),
            "ex_v0": int(round(float(a.get("ex_v0", 0.0)))),
            "ex_v1": int(round(float(a.get("ex_v1", 0.0)))),
        })
    out.sort(key=lambda d: (d["src"], d["axis"], d["delta"]))
    return out


def obj_attr(s, nid: int, key: str) -> float:
    return float(s.node(nid)["attrs"].get(key, 0.0))


def readout(s, nid: int) -> dict:
    """The full readback for one ObjItem (mechanical). `sty_recognized` / `sty_src` /
    `sty_axis` are a mechanical TALLY over the two per-axis attributes the rules
    write separately (a0 reported first when both fire) — no decision, just a read."""
    a = s.node(nid)["attrs"]

    def f(k, d=0.0):
        return float(a.get(k, d))

    r0 = int(round(f("sty_recognized_a0")))
    r1 = int(round(f("sty_recognized_a1")))
    if r0:
        axis, src = 0, int(round(f("sty_src_a0", -1.0)))
    elif r1:
        axis, src = 1, int(round(f("sty_src_a1", -1.0)))
    else:
        axis, src = -1, -1
    return {
        "v0": int(round(f("v0"))), "v1": int(round(f("v1"))),
        "d0": int(round(f("d0"))), "d1": int(round(f("d1"))),
        "dv0": int(round(f("dv0"))), "dv1": int(round(f("dv1"))),
        "dv_set": int(round(f("dv_set"))),
        "cat_recognized": int(round(f("cat_recognized"))),
        "cat_sig": (int(round(f("cat_sig0", -1.0))), int(round(f("cat_sig1", -1.0)))),
        "sty_recognized_a0": r0, "sty_recognized_a1": r1,
        "sty_recognized": int(bool(r0 or r1)),
        "sty_axis": axis, "sty_src": src,
        "sty_both_axes": int(bool(r0 and r1)),
        "sty_mem_recognized": int(round(f("sty_mem_recognized"))),
    }
