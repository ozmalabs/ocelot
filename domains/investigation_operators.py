"""INVESTIGATION OPERATORS — the agent's knowledge of WHICH held faculty investigates WHICH
capability axis, as graph data, so the autonomous loop dispatches a picked frontier WITHOUT a
Python decision.

The decision "what to investigate next" is the gap_prioritiser's native score Term. This module
adds the matching structural fact: an `Operator` node per held investigation faculty, each
carrying the keywords of the capability it investigates, and a mechanical wiring step that adds
`CapabilityAxis --investigated_by--> Operator` whenever the axis's capability_keys match an
operator's keywords. Reading that edge (the operator the GRAPH names for the picked axis) is the
dispatch — the same world-adapter role build_axis_env plays when it wires `unifies` edges.

Each Operator carries `runner` = the name of the world-side procedure (domains/investigation_
runners.py) that feeds SourceWorld data to the held op and returns a measurement. The held op
itself is the agent's function; the runner is mechanical "feed the world in, read the score out".
"""
from __future__ import annotations

OPERATOR_TYPE = "Operator"
INVESTIGATES_EDGE = "investigated_by"      # CapabilityAxis -> Operator

# The agent's faculties and the capability keywords each one investigates. Seed DATA (minted as
# Operator nodes) — the agent's self-knowledge, not a Python branch.
_OPERATORS = [
    {"name": "distributional_categories", "runner": "clustering",
     "keywords": ["cluster", "quantis", "quantiz", "categor", "continuous-to-discrete",
                  "decision boundary", "segmentation", "mode", "density"],
     "metric": "cluster_purity", "target": 0.60},
    {"name": "compose_under_selection", "runner": "composition",
     "keywords": ["composition", "compositional", "production-space", "production space",
                  "compose", "vocabulary", "generative", "open set"],
     "metric": "compose_accuracy", "target": 0.50},
    {"name": "categorical_quantiser_composition", "runner": "quantiser",
     "keywords": ["sharper sub-word parts", "density-mode parts", "quantiser for composition"],
     "metric": "compose_accuracy", "target": 0.50},
    {"name": "ear_composition", "runner": "ear",
     "keywords": ["ear", "perception", "cochlea", "front-end", "band", "liftering",
                  "cepstr", "coarticulation", "context normalization", "carryover", "filter"],
     "metric": "recognition_accuracy", "target": 0.50},
    {"name": "grown_representation", "runner": "grown",
     "keywords": ["represent", "patch", "transition", "grow", "fabric", "feature"],
     "metric": "transition_lift", "target": 0.50},
    {"name": "transition_representation", "runner": "transition_clustering",
     "keywords": ["formant-trajectory", "transition features", "trajectory", "dynamics over time"],
     "metric": "cluster_purity", "target": 0.60},
    {"name": "dtw_transition_representation", "runner": "dtw_transition",
     "keywords": ["dtw", "alignment-tolerant", "time-warp", "trajectory alignment"],
     "metric": "cluster_purity", "target": 0.60},
    {"name": "combinatorial_recognizer", "runner": "recognizer",
     "keywords": ["recogni", "discriminant", "lda", "fisher", "covariance", "classifier",
                  "combinatorial", "channel"],
     "metric": "recognition_accuracy", "target": 0.50},
]


def install_investigation_operators(substrate) -> list:
    """Mint one Operator node per held faculty + declare the investigated_by edge. Idempotent."""
    try:
        substrate.add_production({
            "src": {"type": "CapabilityAxis", "var": "a"},
            "edge_type": INVESTIGATES_EDGE,
            "tgt": {"type": OPERATOR_TYPE, "var": "b"},
            "provenance": "investigation_operators:investigated_by"})
    except Exception:
        pass
    existing = {substrate.node(o)["attrs"].get("name"): o
                for o in substrate.nodes(OPERATOR_TYPE)}
    ids = []
    for spec in _OPERATORS:
        if spec["name"] in existing:
            ids.append(existing[spec["name"]]); continue
        ids.append(substrate.add_node(OPERATOR_TYPE, {
            "name": spec["name"], "runner": spec["runner"], "metric": spec["metric"],
            "target": float(spec["target"]), "keywords": list(spec["keywords"])}))
    return ids


def _match_score(capability_keys, keywords) -> int:
    keys = " ".join(str(k).lower() for k in capability_keys)
    return sum(1 for kw in keywords if kw in keys)


def wire_operators(substrate) -> int:
    """Mechanical structural wiring: add CapabilityAxis --investigated_by--> Operator to the
    SINGLE best-matching operator (most keyword hits) for each axis. Idempotent. Returns the
    number of axes wired. No decision — a registry lookup made graph-resident."""
    ops = [(o, substrate.node(o)["attrs"]) for o in substrate.nodes(OPERATOR_TYPE)]
    if not ops:
        install_investigation_operators(substrate)
        ops = [(o, substrate.node(o)["attrs"]) for o in substrate.nodes(OPERATOR_TYPE)]
    wired = 0
    for ax in substrate.nodes("CapabilityAxis"):
        a = substrate.node(ax)["attrs"]
        if a.get("is_axis") != 1.0:
            continue
        if substrate.neighbours(ax, INVESTIGATES_EDGE):
            continue
        keys = a.get("capability_keys", [])
        best, best_s = None, 0
        for oid, oa in ops:
            s = _match_score(keys, oa.get("keywords", []))
            if s > best_s:
                best, best_s = oid, s
        if best is not None:
            substrate.add_edge(ax, INVESTIGATES_EDGE, best)
            wired += 1
    return wired


def operator_for_axis(substrate, axis_id):
    """Read the operator the GRAPH names for a picked axis -> its attrs dict (or None)."""
    nb = substrate.neighbours(axis_id, INVESTIGATES_EDGE)
    return substrate.node(nb[0])["attrs"] if nb else None


__all__ = ["install_investigation_operators", "wire_operators", "operator_for_axis",
           "OPERATOR_TYPE", "INVESTIGATES_EDGE"]
