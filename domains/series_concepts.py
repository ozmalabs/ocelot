"""series_concepts — the agent's GRAPH-NATIVE, SELF-COMPOSED 'even collinear' concept.

Closing the authoring boundary: the conceptual COMPOSITION is now the agent's, not
mine. I ground only the two irreducible ORDER-N ATOMS (the sensorium — you cannot
define "read this cell's row" or "take the order-2 difference" as genus-differentia;
it is how the agent perceives). The agent then COMPOSES the concept itself, via its
own ``_spec_to_term`` over a genus-differentia spec written in its own grounded
vocabulary — the same teach-don't-hack channel it grounds every read word through.

ATOMS I ground (Term-trees — order-N perception, not expressible as genus-differentia):
  · rows_evenstep(triple)  — |order2(r0,r1,r2)| <= tol   (even/aligned on the row axis)
  · cols_evenstep(triple)  — |order2(c0,c1,c2)| <= tol   (even/aligned on the col axis)

CONCEPT the agent composes (its own _spec_to_term assembles the Term):
  · even_collinear(x) := rows_evenstep(x) AND cols_evenstep(x)
        i.e. a straight, evenly-stepped line = order-2 ~0 on BOTH axes. The agent
        can EXPLAIN it by walking the And down to the two atoms.
"""
from __future__ import annotations

from substrate import Abs, Attr, Lit, Lte, Minus, Var

# the looked-up genus, stamped as provenance (jabberwock_grounds_bounds --concepts
# series sequence row interval spacing ...): series -> ordering -> arrangement; the
# even step is interval/spacing; 'collinear' is the adjective WordNet can't type.
_BECAUSE = ("even_collinear = rows_evenstep AND cols_evenstep; the agent composed "
            "this; the atoms are the order-2 finite difference (its own order-N)")
_TOL = 1.0


def _order2(a0, a1, a2):
    """Order-2 finite difference (b->c step minus a->b step) as a DSL Term — the
    agent's order-N operator at order 2 over a fixed triple."""
    return Minus(Minus(a2, a1), Minus(a1, a0))


def _install_atoms(agent, tol: float):
    """Ground the two order-N ATOMS as Term-trees (the sensorium floor)."""
    x = Var("x")
    if "rows_evenstep" not in agent._concept_nodes:
        agent.ground_concept(
            "rows_evenstep",
            Lte(Abs(_order2(Attr(x, "r0"), Attr(x, "r1"), Attr(x, "r2"))),
                Lit(float(tol))),
            domain="space")
    if "cols_evenstep" not in agent._concept_nodes:
        agent.ground_concept(
            "cols_evenstep",
            Lte(Abs(_order2(Attr(x, "c0"), Attr(x, "c1"), Attr(x, "c2"))),
                Lit(float(tol))),
            domain="space")


def install_series_concepts(agent, tol: float = _TOL):
    """Ground the atoms, then have the AGENT compose even_collinear from a
    genus-differentia spec in its own vocabulary (idempotent). Returns the
    composed concept's node id."""
    if "even_collinear" in agent._concept_nodes:
        return agent._concept_nodes["even_collinear"]
    _install_atoms(agent, tol)
    # THE AGENT composes the concept: a spec in its grounded vocabulary, assembled
    # into a Term by its own _spec_to_term — I do not hand it a built Term.
    spec = ["And",
            ["Holds", "rows_evenstep", ["Var", "x"]],
            ["Holds", "cols_evenstep", ["Var", "x"]]]
    term = agent._spec_to_term(spec)
    cid = agent.ground_concept("even_collinear", term, domain="space")
    agent.mind_graph.node(cid).attrs["because"] = _BECAUSE
    return cid
