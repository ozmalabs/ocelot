"""Load the optimization-pipelines seed.

This installs two layers of pipeline knowledge as graph data:

  1. `enables` edges between `OptimizationConcept` nodes. When concept
     A creates conditions that concept B can fire on, an `enables`
     edge from A to B records the relation. This is the agent's
     declarative knowledge of pass interactions — observed cascades
     promoted to graph-resident facts.

  2. `Pipeline` nodes — named ordered sequences of concepts. Each
     pipeline carries a description, an `iterate_to_fixed_point`
     flag, and `applies` edges to the concepts it sequences. The
     edges are attributed with `position` (0-indexed order) so the
     ordering is fully recoverable from the graph.

The agent's reasoning about pass ordering becomes a graph traversal:
follow `applies` edges sorted by position to walk a pipeline, follow
`enables` edges to see why one concept follows another.
"""
from __future__ import annotations

import json
from pathlib import Path


# ---------------------------------------------------------------------------
# grammar
# ---------------------------------------------------------------------------

def _ensure_pipeline_grammar(substrate) -> None:
    substrate.add_production({
        "src": {"type": "OptimizationConcept", "var": "src"},
        "edge_type": "enables",
        "tgt": {"type": "OptimizationConcept", "var": "tgt"},
        "where": None,
        "weight": {"type": "Lit", "value": 1.0},
        "provenance": "optimization_pipelines:enables",
    })
    substrate.add_production({
        "src": {"type": "Pipeline", "var": "src"},
        "edge_type": "applies",
        "tgt": {"type": "OptimizationConcept", "var": "tgt"},
        "where": None,
        "weight": {"type": "Lit", "value": 1.0},
        "provenance": "optimization_pipelines:applies",
    })


# ---------------------------------------------------------------------------
# loader
# ---------------------------------------------------------------------------

def load_pipelines_seed(path: str | Path) -> dict:
    p = Path(path)
    with p.open("r") as f:
        manifest = json.load(f)
    if "pipelines" not in manifest:
        raise ValueError(f"{p}: missing 'pipelines' key — not a pipelines seed")
    return manifest


def install_pipelines_seed(substrate, path: str | Path) -> dict:
    """Install `enables` edges + `Pipeline` nodes + `applies` edges from
    the seed at `path`. Returns counts.

    Requires `compiler_theory` seed already loaded (OptimizationConcept
    nodes must exist to be referenced by name).
    """
    _ensure_pipeline_grammar(substrate)
    manifest = load_pipelines_seed(path)

    # Index existing OptimizationConcept nodes by name.
    name_to_concept: dict[str, int] = {}
    for c in substrate.nodes("OptimizationConcept"):
        attrs = substrate.node(c)["attrs"]
        name = attrs.get("name")
        if isinstance(name, str):
            name_to_concept[name] = c

    enables_installed = 0
    for rel in manifest.get("enables", []):
        src = name_to_concept.get(rel["from"])
        tgt = name_to_concept.get(rel["to"])
        if src is None or tgt is None:
            continue
        substrate.add_edge(src, "enables", tgt, {
            "rationale": rel.get("rationale", ""),
        })
        enables_installed += 1

    pipelines_installed = 0
    applies_installed = 0
    for pipe in manifest.get("pipelines", []):
        # Concept ordering lives as a list attr on the Pipeline node.
        # `applies` edges record the set membership (one per concept);
        # the order is recoverable from `concept_order` rather than
        # via edge attributes (which the current Python binding doesn't
        # surface). The list mirrors the JSON manifest's `concepts`
        # array exactly.
        p_node = substrate.add_node("Pipeline", {
            "name": pipe["name"],
            "description": pipe.get("description", ""),
            "iterate_to_fixed_point": pipe.get("iterate_to_fixed_point", False),
            "concept_order": list(pipe.get("concepts", [])),
        })
        for concept_name in pipe.get("concepts", []):
            tgt = name_to_concept.get(concept_name)
            if tgt is None:
                continue
            substrate.add_edge(p_node, "applies", tgt, {})
            applies_installed += 1
        pipelines_installed += 1

    return {
        "enables_installed": enables_installed,
        "pipelines_installed": pipelines_installed,
        "applies_installed": applies_installed,
    }


# ---------------------------------------------------------------------------
# executor — walk the graph, dispatch by rule_idx
# ---------------------------------------------------------------------------

def _rule_idxs_for_concept(substrate, concept_node: int) -> list[int]:
    """Walk concept → instantiates → family → ←member_of ← RewriteRule.
    Return the native rule_idxs of every rule in the family."""
    families = substrate.neighbours(concept_node, "instantiates")
    idxs = []
    for fam in families:
        for rule_node in substrate.in_neighbours(fam, "member_of"):
            idx = substrate.node(rule_node)["attrs"].get("rule_idx")
            if isinstance(idx, int):
                idxs.append(idx)
    return idxs


def _pipeline_concepts_in_order(substrate, pipeline_node: int) -> list[int]:
    """Walk the pipeline's ordered concept list. Order is recovered from
    the `concept_order` attr on the Pipeline node (a list of concept
    names) — the current Python binding doesn't surface edge attributes,
    so we record ordering on the node itself. The `applies` edges
    encode set membership."""
    p_attrs = substrate.node(pipeline_node)["attrs"]
    order: list[str] = p_attrs.get("concept_order", [])
    # Index OptimizationConcept nodes by name once.
    name_to_concept: dict[str, int] = {}
    for c in substrate.nodes("OptimizationConcept"):
        nm = substrate.node(c)["attrs"].get("name")
        if isinstance(nm, str):
            name_to_concept[nm] = c
    return [name_to_concept[n] for n in order if n in name_to_concept]


def run_pipeline_by_name(substrate, pipeline_name: str,
                         max_steps_per_rule: int = 200) -> dict:
    """Execute a named Pipeline. Walks the graph for the Pipeline node,
    enumerates its concepts in `position` order, collects each concept's
    family's rule_idxs, and applies them. Iterates if the Pipeline
    carries `iterate_to_fixed_point: true`.

    Returns counts: `{"rules_applied": N, "iterations": M,
    "pipeline_node": NodeID}`.

    This is the actionable form of the pipeline knowledge — the agent
    can ask "run local_peephole on this graph" and the loader follows
    declarative graph data to dispatch concrete rule applications.
    No decision logic in Python: which rules to run is determined by
    walking the OptimizationConcept → RuleFamily → RewriteRule chain;
    iteration count is determined by the Pipeline's own attr.
    """
    # Locate the pipeline node by name.
    pipeline = None
    for p in substrate.nodes("Pipeline"):
        if substrate.node(p)["attrs"].get("name") == pipeline_name:
            pipeline = p
            break
    if pipeline is None:
        raise ValueError(f"no Pipeline named {pipeline_name!r}")

    p_attrs = substrate.node(pipeline)["attrs"]
    iterate = bool(p_attrs.get("iterate_to_fixed_point", False))

    concepts = _pipeline_concepts_in_order(substrate, pipeline)
    rule_idxs: list[int] = []
    for c in concepts:
        rule_idxs.extend(_rule_idxs_for_concept(substrate, c))

    rules_applied = 0
    iterations = 0
    while True:
        iterations += 1
        progress = False
        for idx in rule_idxs:
            # apply_rule_once returns True iff the rule fired.
            if substrate.apply_rule_once(idx):
                rules_applied += 1
                progress = True
                # We may need many fires of this rule; loop until it
                # stops firing in this iteration.
                while substrate.apply_rule_once(idx):
                    rules_applied += 1
                    if rules_applied >= max_steps_per_rule * len(rule_idxs):
                        # Hard safety bound. Should be unreachable for
                        # well-formed pipelines on bounded input.
                        return {
                            "rules_applied": rules_applied,
                            "iterations": iterations,
                            "pipeline_node": pipeline,
                            "bound_reached": True,
                        }
        if not progress or not iterate:
            break

    return {
        "rules_applied": rules_applied,
        "iterations": iterations,
        "pipeline_node": pipeline,
    }


__all__ = [
    "load_pipelines_seed",
    "install_pipelines_seed",
    "run_pipeline_by_name",
]
