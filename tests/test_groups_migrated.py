"""GROUP axioms, migrated — grounding group theory over observed structure on
the seed-booted agent via the WorldAdapter (no CuriousAgent).

Covers every behaviour of tests/test_groups.py:

  • the agent perceives a group as a carrier MathSet + an operation (a Cayley
    table of OpTriples) by INGESTING the structure_world substrate (no
    CuriousAgent.observe);
  • the GROUP axioms ground as DSL Term-trees (JSON) the agent classifies by —
    closed / commutative / has_identity / has_inverse / associative — and they
    separate a real group (ℤ/3 under +) from a non-group (left-projection
    a∘b=a);
  • the composed ``group`` concept (And over the axioms, each invoked by name
    via the ``Holds`` Term — so each axiom is registered as a concept) holds for
    ℤ/3 and fails for the left-projection;
  • ``homomorphism`` — a map preserving the operation, f(a∘b)=f(a)∘f(b) — grounds
    and separates the ×2-mod-3 map (a hom) from the swap(0,1) map (not a hom).

Discipline: the adapter only INGESTS the world and RUNS the agent's own Term;
every classification DECISION is the grounded Term, evaluated by the substrate
(``concept_holds`` for the unary axioms / group / homomorphism, with the
operation's binary structure reached through the Term's own Var bindings).
"""
from __future__ import annotations

from substrate.world_adapter import WorldAdapter
from domains.structure_world import StructureWorld, structure_world_handle

# --- Term-tree builders (JSON the substrate evaluates) ----------------------
_V = lambda n: {"type": "Var", "name": n}
_L = lambda x: {"type": "Lit", "value": x}
_NB = lambda v, e: {"type": "Neighbours", "node": _V(v), "edge_type": e}
_AND = lambda *items: {"type": "And", "items": list(items)}
_NOT = lambda arg: {"type": "Not", "arg": arg}
_IN = lambda m, c: {"type": "In", "member": m, "container": c}
_EQ0 = lambda src: {"type": "Eq", "a": {"type": "Count", "source": src}, "b": _L(0)}
_GT0 = lambda src: {"type": "Gt", "a": {"type": "Count", "source": src}, "b": _L(0)}
_FILTER = lambda src, var, pred: {
    "type": "Filter", "source": src, "var_name": var, "predicate": pred}
_EXISTS = lambda src, var, pred: {
    "type": "Exists", "source": src, "var_name": var, "predicate": pred}
_MAPNB = lambda src, e: {"type": "MapNeighbours", "source": src, "edge_type": e}


def _OP(a, b):
    """Result-set of (a ∘ b) in the group bound to x — the OpTriples of x whose
    left contains a and right contains b, mapped to their result."""
    return _MAPNB(_FILTER(_NB("x", "op_triple"), "t", _AND(
        _IN(_V(a), _NB("t", "left")),
        _IN(_V(b), _NB("t", "right")))), "result")


# The carrier elements of the group bound to x.
_CARR = _MAPNB(_NB("x", "carrier"), "element")

# e is a two-sided identity: every carrier element a has e∘a ∋ a and a∘e ∋ a.
_E_IS_ID = _EQ0(_FILTER(_CARR, "a", _NOT(_AND(
    _IN(_V("a"), _OP("e", "a")),
    _IN(_V("a"), _OP("a", "e"))))))

_AXIOMS = {
    # every op_triple's result is a carrier element (operation is closed).
    "closed": _EQ0(_FILTER(_NB("x", "op_triple"), "t",
        _NOT(_EXISTS(_NB("t", "result"), "r", _IN(_V("r"), _CARR))))),
    # for all a,b: a∘b and b∘a share a result.
    "commutative": _EQ0(_FILTER(_CARR, "a", _GT0(_FILTER(_CARR, "b",
        _NOT(_EXISTS(_OP("a", "b"), "r", _IN(_V("r"), _OP("b", "a")))))))),
    # there exists a two-sided identity.
    "has_identity": _EXISTS(_CARR, "e", _E_IS_ID),
    # an identity exists AND every element has an inverse w.r.t. it.
    "has_inverse": _EXISTS(_CARR, "e", _AND(_E_IS_ID,
        _EQ0(_FILTER(_CARR, "a", _NOT(_EXISTS(_CARR, "b", _AND(
            _IN(_V("e"), _OP("a", "b")),
            _IN(_V("e"), _OP("b", "a"))))))))),
    # for all a,b,c: (a∘b)∘c and a∘(b∘c) share a result.
    "associative": _EQ0(_FILTER(_CARR, "a", _GT0(_FILTER(_CARR, "b", _GT0(
        _FILTER(_CARR, "c", _NOT(_EXISTS(_OP("a", "b"), "ab", _EXISTS(
            _OP("b", "c"), "bc", _EXISTS(_OP("ab", "c"), "r", _IN(
                _V("r"), _OP("a", "bc")))))))))))),
}

_EXPECT = {  # (Z3, Lp)
    "closed": (True, True), "commutative": (True, False),
    "has_identity": (True, False), "has_inverse": (True, False),
    "associative": (True, True),
}


def _world():
    """Boot the seed agent, ingest the structure world (which publishes every
    group/operation as raw structure), and index the perceived instances."""
    wa = WorldAdapter()
    handle = structure_world_handle(StructureWorld(), None)
    substrate, ctx = handle["reset"]()
    wa.ingest(substrate)
    for _ in range(12):
        substrate, ctx = handle["apply_action"](substrate, ctx, ("focus_next",))
        wa.ingest(substrate)
    inst = {wid: nid for (t, wid), nid in wa._instances.items()}
    return wa, inst


def test_groups_perceived_via_seed_agent():
    wa, inst = _world()
    for key in ("grp_Z3", "grp_Lp", "hom_double", "hom_swap"):
        assert key in inst
    types = {t for (t, _) in wa._instances}
    assert {"Group", "MathSet", "OpTriple", "Element", "Function"} <= types


def test_group_axioms_ground_and_classify():
    wa, inst = _world()
    z3, lp = inst["grp_Z3"], inst["grp_Lp"]
    for name, term in _AXIOMS.items():
        wa.learn_word(name, term)
        assert name in wa._concepts, f"{name} failed to ground"
        got = (wa.concept_holds(name, z3), wa.concept_holds(name, lp))
        assert got == _EXPECT[name], (name, got)


def test_group_concept_distinguishes_group_from_nongroup():
    wa, inst = _world()
    # ground each axiom AND register it so the composed concept can invoke it
    # by name through the Holds Term.
    for name, term in _AXIOMS.items():
        wa.learn_word(name, term)
        wa.register_concept(name, term)
    group = _AND(*[{"type": "Holds", "concept": a, "node": _V("x")}
                   for a in ("closed", "associative",
                             "has_identity", "has_inverse")])
    wa.learn_word("group", group)            # ground it as a named concept
    assert "group" in wa._concepts
    # classify via the main arena so the Holds arm resolves the axiom concepts.
    assert wa.concept_holds_composed(group, inst["grp_Z3"]) is True   # ℤ/3 is a group
    assert wa.concept_holds_composed(group, inst["grp_Lp"]) is False  # left-proj is not


def test_homomorphism_grounds_and_classifies():
    """A function between groups that preserves the operation: f(a∘b)=f(a)∘f(b)
    — the first concept that RELATES two structures."""
    wa, inst = _world()
    g_tri = _MAPNB(_NB("x", "from_group"), "op_triple")
    h_tri = _MAPNB(_NB("x", "to_group"), "op_triple")
    g_car = _MAPNB(_MAPNB(_NB("x", "from_group"), "carrier"), "element")

    def op(tri, a, b):
        return _MAPNB(_FILTER(tri, "t", _AND(
            _IN(_V(a), _NB("t", "left")),
            _IN(_V(b), _NB("t", "right")))), "result")

    def f(vn):
        return _MAPNB(_FILTER(_NB("x", "pair"), "p",
            _IN(_V(vn), _NB("p", "dom"))), "cod")

    preserve = _EXISTS(op(g_tri, "a", "b"), "c",
        _EXISTS(f("c"), "r", _EXISTS(f("a"), "fa", _EXISTS(f("b"), "fb",
            _IN(_V("r"), op(h_tri, "fa", "fb"))))))
    hom = _EQ0(_FILTER(g_car, "a", _GT0(_FILTER(g_car, "b", _NOT(preserve)))))

    wa.learn_word("homomorphism", hom)
    assert "homomorphism" in wa._concepts
    assert wa.concept_holds("homomorphism", inst["hom_double"]) is True  # ×2 mod 3
    assert wa.concept_holds("homomorphism", inst["hom_swap"]) is False   # swap(0,1)
