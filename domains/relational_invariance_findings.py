"""relational_invariance_findings — load the session's CONFIRMED speech findings
into the graph as order-0 postulates the agent HOLDS.

The data lives in `seeds/relational_invariance_findings.json`. This module is the
mechanical loader (JSON -> graph): it mints the `relational_invariance_findings`
Microtheory and installs each finding as a Concept (definition + why) under it.

These Concepts are order-0 postulates: `order_n_postulates.harvest_postulates`
gathers them, the agent's `implication_harvester` reads their definition+why text
to harvest the implication-SHAPES it transfers, and `gap_prioritiser` ranks the
resulting gaps by the agent's compression payoff. NO decision lives here — the
agent's own machinery derives and ranks the next direction. This is a world<->graph
loader, the same role `install_speech_science` plays for the speech-science map.
"""
from __future__ import annotations

import json
from pathlib import Path

from .code_authoring import _install_concept

_SEED_PATH = (Path(__file__).resolve().parent.parent /
              "seeds" / "relational_invariance_findings.json")


def _load_seed() -> dict:
    with _SEED_PATH.open() as f:
        return json.load(f)


def install_relational_invariance_findings(substrate) -> dict:
    """Install the relational_invariance_findings Mt + its finding-concepts as
    order-0 postulates. Idempotent. Returns name -> NodeID for the Mt + concepts."""
    seed = _load_seed()
    for src, et, tgt in (("Microtheory", "has_concept", "Concept"),
                         ("Microtheory", "has_rule", "Rule")):
        try:
            substrate.add_production({
                "src": {"type": src, "var": "a"}, "edge_type": et,
                "tgt": {"type": tgt, "var": "b"},
                "provenance": f"relational_invariance_findings:{et}"})
        except Exception:
            pass

    mt = None
    for n in substrate.nodes("Microtheory"):
        if (substrate.node(n)["attrs"].get("name")
                == "relational_invariance_findings"):
            mt = n
            break
    if mt is None:
        mt = substrate.add_node("Microtheory", {
            "name": "relational_invariance_findings",
            "description": seed.get("description", ""),
            "origin": "relational_invariance_findings"})

    out = {"_mt": mt}
    for c in seed.get("concepts", []):
        existing = None
        for ec in substrate.neighbours(mt, "has_concept"):
            if substrate.node(ec)["attrs"].get("name") == c["name"]:
                existing = ec
                break
        if existing is not None:
            out[c["name"]] = existing
            continue
        cid = _install_concept(substrate, mt, c["name"], c["definition"],
                               c.get("term"))
        # the agent's postulate machinery reads BOTH definition + why as the
        # property text; set `why` so the harvester sees the full structural claim.
        if c.get("why"):
            substrate.set_attr(cid, "why", c["why"])
        substrate.set_attr(cid, "category", c.get("category", ""))
        substrate.set_attr(cid, "origin", "relational_invariance_findings")
        out[c["name"]] = cid
    return out
