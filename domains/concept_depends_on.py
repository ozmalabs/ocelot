"""Change 1: emit depends_on edges from grounded Term-trees.

Per jabberwock's first proposed change (commit fa6380c):
'Have grounding ALSO emit depends_on / genlMt edges in the genlMt
graph (Newton_second_law depends_on force, mass, acceleration).'

This walks each grounded Term-tree, extracts every Holds("X", _)
reference, and adds an edge from the equation's Concept node to
the referenced concept's Concept node. The grounding's structural
content becomes visible to the cortex's compositional_reuse
measure.

Pure mechanical translation of what the grounded trees say. No
authoring decisions — the edges come from the Term-tree references
the teacher's grounding pass produced.
"""
from __future__ import annotations


def _extract_holds_concepts(term_json) -> list[str]:
    """Walk a Term-tree (JSON form); collect every Holds 'concept' name."""
    out: list[str] = []
    if not isinstance(term_json, dict):
        return out
    if term_json.get("type") == "Holds":
        c = term_json.get("concept")
        if isinstance(c, str):
            out.append(c)
    for v in term_json.values():
        if isinstance(v, dict):
            out.extend(_extract_holds_concepts(v))
        elif isinstance(v, list):
            for item in v:
                out.extend(_extract_holds_concepts(item))
    return out


def _find_concept_node(substrate, name: str):
    """Find a Concept graph node by attrs.name."""
    for c in substrate.nodes("Concept"):
        if substrate.node(c)["attrs"].get("name") == name:
            return c
    return None


def install_concept_depends_on(substrate) -> dict:
    """Walk grounded Term-trees; emit depends_on edges from each
    equation's Concept to every concept its Term-tree references.

    Returns a report:
      · equations_processed
      · edges_added
      · references_missing  — concept names referenced but not found
                              as Concept nodes
      · sample_edges        — first 10 edges added (for inspection)
    """
    try:
        from .concept_grounding import GROUNDED_CONCEPTS
    except ImportError:
        return {"error": "concept_grounding not available"}

    # Open the production for depends_on if not already
    try:
        substrate.add_production({
            "src": {"type": "Concept", "var": "src"},
            "edge_type": "depends_on",
            "tgt": {"type": "Concept", "var": "tgt"},
            "where": None,
            "weight": {"type": "Lit", "value": 1.0},
            "provenance": "concept_depends_on",
        })
    except Exception:
        pass

    edges_added = 0
    missing: set[str] = set()
    sample: list = []
    processed = 0

    for name, term_json in GROUNDED_CONCEPTS:
        processed += 1
        src_nid = _find_concept_node(substrate, name)
        if src_nid is None:
            continue
        refs = sorted(set(_extract_holds_concepts(term_json)))
        for ref in refs:
            if ref == name:
                continue
            tgt_nid = _find_concept_node(substrate, ref)
            if tgt_nid is None:
                missing.add(ref)
                continue
            # Check if edge already exists
            existing = substrate.neighbours(src_nid, "depends_on")
            if tgt_nid in existing:
                continue
            try:
                substrate.add_edge(src_nid, "depends_on", tgt_nid, {})
                edges_added += 1
                if len(sample) < 10:
                    sample.append((name, ref))
            except Exception:
                pass

    return {
        "equations_processed":   processed,
        "edges_added":           edges_added,
        "references_missing":    sorted(missing),
        "sample_edges":          sample,
    }
