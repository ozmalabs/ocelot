"""figure_ground_concepts — the agent's SELF-COMPOSED 'area is a thing' concept.

Closing the authoring boundary for figure/ground. I ground only the irreducible
PERCEPTUAL/TRAVERSAL ATOMS (the sensorium: reading a cell's row/col, traversing a
region's member cells, an order-bounded box — none expressible as genus-differentia,
because they ARE perception). The agent then COMPOSES the conceptual layer itself,
via its own ``_spec_to_term`` over genus-differentia specs in its grounded
vocabulary — I never hand it a built composite Term.

ATOMS I ground (Term-trees; traversal/comparison the spec language can't express):
  · is_region(x)               — a Location with >=1 cell.
  · region_touches_boundary(x) — some member cell sits on the world's edge
        (row/col at an extremity; ymax/xmax = the world's own dimensions, bound
        at evaluation, the same mechanical I/O as observe).
  · bbox_inside_play(x)        — x's bounding box sits inside the play area's
        bounding box (play bbox bound at evaluation).

CONCEPTS the agent composes (its own _spec_to_term assembles each Term). Named so
they COEXIST with the seed's lexical 'area'/'ground' (the wiki measure/background
word-senses) rather than clobber them — the operational figure/ground sense is a
distinct, perceptual sense:
  · background_region(x) := region_touches_boundary(x)         (the ground)
  · bounded_area(x)      := is_region(x) AND NOT background_region(x)  (a THING)
  · in_play(x)           := bbox_inside_play(x)                (enclosed by play)
The genus-differentia of `bounded_area` (a region that is not background) is the
agent's, built by its machinery; it can EXPLAIN it by walking And/Not/Holds to the
atoms.
"""
from __future__ import annotations

from substrate import (And, Attr, Count, Eq, Exists, Gte, InNeighbours, Lit, Lte,
                        MaxOver, MinOver, Or, Var)

GENUS = {
    "is_region": "atom: a location with cells (perceptual)",
    "region_touches_boundary": "atom: a member cell at the world's edge (perceptual)",
    "bbox_inside_play": "atom: bounding box inside the play area (perceptual)",
    "background_region": "a region that touches the world's boundary (the ground)",
    "bounded_area": "is_region AND NOT background_region — a bounded interior THING (agent-composed)",
    "in_play": "enclosed by the play area (agent-composed)",
}


def _install_atoms(agent):
    """Ground the perceptual/traversal atoms as Term-trees (the sensorium floor)."""
    x = Var("x")
    cells = InNeighbours(x, "within")
    if "is_region" not in agent._concept_nodes:
        agent.ground_concept("is_region", Gte(Count(cells), Lit(1)), domain="space")
    if "region_touches_boundary" not in agent._concept_nodes:
        on_edge = Or(items=(
            Eq(Attr(Var("c"), "row"), Lit(0)),
            Eq(Attr(Var("c"), "row"), Var("ymax")),
            Eq(Attr(Var("c"), "col"), Lit(0)),
            Eq(Attr(Var("c"), "col"), Var("xmax")),
        ))
        agent.ground_concept("region_touches_boundary",
                             Exists(cells, "c", on_edge), domain="space")
    if "bbox_inside_play" not in agent._concept_nodes:
        inside = And(items=(
            Gte(MinOver(cells, "c", Attr(Var("c"), "row"), default=Lit(0)), Var("pminrow")),
            Lte(MaxOver(cells, "c", Attr(Var("c"), "row"), default=Lit(0)), Var("pmaxrow")),
            Gte(MinOver(cells, "c", Attr(Var("c"), "col"), default=Lit(0)), Var("pmincol")),
            Lte(MaxOver(cells, "c", Attr(Var("c"), "col"), default=Lit(0)), Var("pmaxcol")),
        ))
        agent.ground_concept("bbox_inside_play", inside, domain="space")


# the genus-differentia SPECS — in the agent's own grounded vocabulary. The agent's
# _spec_to_term assembles each into a Term it owns; I never build the composite Term.
_SPECS = {
    "background_region": ["Holds", "region_touches_boundary", ["Var", "x"]],
    "bounded_area": ["And", ["Holds", "is_region", ["Var", "x"]],
                     ["Not", ["Holds", "background_region", ["Var", "x"]]]],
    "in_play": ["Holds", "bbox_inside_play", ["Var", "x"]],
}


def install_figure_ground_concepts(agent):
    """Ground the atoms, then have the AGENT compose ground / area / in_play from
    genus-differentia specs in its own vocabulary (idempotent)."""
    _install_atoms(agent)
    for name, spec in _SPECS.items():
        if name in agent._concept_nodes:
            continue
        cid = agent.ground_concept(name, agent._spec_to_term(spec), domain="space")
        agent.mind_graph.node(cid).attrs["because"] = GENUS[name]
    return {n: agent._concept_nodes[n] for n in
            ("is_region", "region_touches_boundary", "bbox_inside_play",
             "background_region", "bounded_area", "in_play")}


def eval_concept(agent, name, node, **env):
    """Run an authored concept's definition (the agent's own evaluator) on ``node``
    with grid dims / play-bbox bound in env (mechanical I/O — the Term decides)."""
    from substrate import term_from_subgraph
    cid = agent._concept_nodes[name]
    term = None
    for e in agent.mind_graph.out_edges(cid, "definition"):
        term = term_from_subgraph(agent.mind_graph, e.key.tgt)
        break
    base = {"x": node, "self": agent.agent_root, "agent": agent.agent_root,
            "_resolve_concept": agent._concept_term}
    base.update(env)
    try:
        return term.evaluate(base, agent.mind_graph)
    except Exception as exc:
        return f"<err {type(exc).__name__}: {exc}>"


def explain(agent, name, _depth=0, _seen=None):
    """The agent EXPLAINS a concept by walking its definition's Holds references
    down to the atoms — its genus-differentia, in its own words."""
    _seen = _seen or set()
    cid = agent._concept_nodes.get(name)
    because = agent.mind_graph.node(cid).attrs.get("because", "") if cid else ""
    lines = ["  " * _depth + f"{name}: {because}"]
    if name in _seen or cid is None:
        return lines
    _seen.add(name)
    # the concepts this one composes on = the Holds references in its definition,
    # read with the agent's OWN definition-walker (_term_references).
    from substrate import term_from_subgraph
    for e in agent.mind_graph.out_edges(cid, "definition"):
        term = term_from_subgraph(agent.mind_graph, e.key.tgt)
        _attrs, _types, concepts = agent._term_references(term)
        for ref in sorted(concepts):
            lines += explain(agent, ref, _depth + 1, _seen)
        break
    return lines
