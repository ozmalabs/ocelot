"""stream_world — a world adapter for THE STREAM (VISION_STREAM_PREREG.md).

Mechanical I/O ONLY (CLAUDE.md / PROTOCOL §0): builds a Scene + a residual-mass
Region field, blind-writes the OFF-by-default flag, ticks the substrate to a
fixpoint (run_rules, NOT apply_rule_once), and reads the stream order back. It
makes NO percept decision — the salience ordering, the budget spend and the
preemption are ALL in seeds/vision_stream.json's one rule; this file only
translates a scene into graph nodes and reads `order` out.

A `residual` here is the render-vs-input surprise MASS over a region (an integer,
supplied by the caller as mechanical measurement — the residual the just-landed
bidirectional loop computes). The adapter never interprets it.
"""
from __future__ import annotations
from typing import Optional


def add_scene(s, *, budget: int, regions: list[dict]) -> dict:
    """Create a Scene{budget, spent:0} and one Region per entry of `regions`.

    Each `regions` entry is a dict with integer `rrow`, `rcol`, `scale`,
    `residual`. Returns a handle {scene, region_ids, meta} — `meta[i]` is the
    caller's own dict for region i, `region_ids[i]` its node id.
    """
    scene = s.add_node("Scene", {"budget": float(budget), "spent": 0.0})
    region_ids: list = []
    for spec in regions:
        n = s.add_node("Region", {
            "rrow": float(spec["rrow"]),
            "rcol": float(spec["rcol"]),
            "scale": float(spec.get("scale", 0)),
            "residual": float(spec["residual"]),
            "resolved": 0.0,
            "order": -1.0,
        })
        # add_edge_unchecked: this is EXTERNAL world scaffolding, not an agent
        # claim, so it bypasses Γ exactly like space_quantize's portal/in_space
        # edges and slide_flood's neighbour/reached edges (host-owned bookkeeping).
        s.add_edge_unchecked(scene, "has_region", n)
        region_ids.append(n)
    return {"scene": scene, "region_ids": region_ids, "meta": list(regions)}


def set_stream(s, stream: float = 1.0) -> None:
    """Blind-write the flag on every StreamParams node. Does not read or branch."""
    for p in s.nodes("StreamParams"):
        s.set_attr(p, "stream", float(stream))


def run(s, max_steps: int = 200_000) -> int:
    """THE STREAM: run_rules to a fixpoint. Returns the sweep count."""
    return s.tick(max_steps)


def read_order(s, handle: dict) -> list[int]:
    """Per-region stream position (order), -1 = never streamed in this budget."""
    out = []
    for n in handle["region_ids"]:
        out.append(int(round(float(s.node(n)["attrs"].get("order", -1.0)))))
    return out


def read_spent(s, handle: dict) -> int:
    """How much of the budget was spent (the number of refinements)."""
    return int(round(float(s.node(handle["scene"])["attrs"].get("spent", 0.0))))


def resolved_indices(s, handle: dict) -> list[int]:
    """Indices of regions that were streamed in (order >= 0), in stream order."""
    order = read_order(s, handle)
    idx = [i for i, o in enumerate(order) if o >= 0]
    idx.sort(key=lambda i: order[i])
    return idx


def uniform_spend(handle: dict, budget: int) -> list[int]:
    """The residual-BLIND control: a row-major round-robin spends the SAME budget
    ignoring residual. Pure arithmetic on the scene layout (a baseline to contrast
    the salience spend against, per PROTOCOL §6) — resolves the first `budget`
    regions in (rrow, rcol) order. Returns the resolved indices."""
    order = sorted(range(len(handle["meta"])),
                   key=lambda i: (handle["meta"][i]["rrow"],
                                  handle["meta"][i]["rcol"]))
    return sorted(order[:budget])
