"""breadth — load the agent's cross-domain conceptual reservoir from its seed.

The DATA lives in `seeds/breadth.json` — structural FORMS the agent learned in
other worlds (vision / physics / chess / math / topology), each a Concept with a
Term-tree predicate (the shape), as graph data. This module is the thin mechanical
loader (JSON -> graph): no decisions, no Python-built Terms.

Analogy ([[ozma_analogical_transfer]]) needs these to fire: `abstract_patterns`
hollows them to skeletons and `generate_by_transfer` re-instantiates them over a
new domain's features. Breadth is creative capacity — the in-seed argument for
raising the agent across many worlds.
"""
from __future__ import annotations

import json
from pathlib import Path

_SEED_PATH = (Path(__file__).resolve().parent.parent / "seeds" / "breadth.json")


def install_breadth(substrate) -> int:
    """Mint the seeded cross-domain forms as graph-resident Concepts (idempotent).
    Mechanical JSON -> graph translation. Returns the number installed."""
    with _SEED_PATH.open() as f:
        seed = json.load(f)
    have = {substrate.node(c)["attrs"].get("name")
            for c in substrate.nodes("Concept")}
    n = 0
    for form in seed.get("forms", []):
        if form["name"] in have:
            continue
        substrate.add_node("Concept", {
            "name": form["name"], "origin": form.get("origin", "breadth"),
            "from_world": form.get("from_world", ""),
            "feature_kind": form.get("feature_kind", "cross_domain_form"),
            "predicate": form["predicate"]})
        n += 1
    return n


__all__ = ["install_breadth"]
