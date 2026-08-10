"""Rings, migrated — the ring/field floor on the seed-booted agent via the
WorldAdapter (no CuriousAgent). Covers every check of tests/test_rings.py.

A ring is perceived as a carrier set + an add-table + a mul-table (OpTriples on
``add_triple`` / ``mul_triple`` edges). The agent grounds the concepts that live
at this floor as Term-trees over the observed structure:

  • distributive — the law linking the two operations; holds for BOTH ℤ/3 and
    ℤ/4 (both are rings);
  • field — every nonzero element has a multiplicative inverse; distinguishes
    ℤ/3 (a field) from ℤ/4 (a ring but NOT a field: 2 has no inverse mod 4).

The structure IS the perception (a single ingest mirrors every ring's carrier +
operation tables into WorldInstance nodes); the DECISION is the taught Term,
evaluated by the agent's own graph. The adapter only ingests and runs the Term.
"""
from __future__ import annotations

from substrate.world_adapter import WorldAdapter
from domains.structure_world import StructureWorld, structure_world_handle

# --- Term-tree builders (JSON the substrate evaluates) ----------------------
_V = lambda n: {"type": "Var", "name": n}
_L = lambda x: {"type": "Lit", "value": x}
_NB = lambda v, e: {"type": "Neighbours", "node": _V(v), "edge_type": e}


# carrier elements of the ring bound to ``x``.
_CARR = {"type": "MapNeighbours", "source": _NB("x", "carrier"), "edge_type": "element"}


def _op(edge, a, b):
    """The result(s) of operation ``edge`` applied to (a, b): the OpTriples on
    that edge whose left=a and right=b, mapped to their result element."""
    return {"type": "MapNeighbours", "edge_type": "result",
            "source": {"type": "Filter", "source": _NB("x", edge), "var_name": "t",
                       "predicate": {"type": "And", "items": [
                           {"type": "In", "member": _V(a), "container": _NB("t", "left")},
                           {"type": "In", "member": _V(b), "container": _NB("t", "right")}]}}}


def _add(a, b):
    return _op("add_triple", a, b)


def _mul(a, b):
    return _op("mul_triple", a, b)


def _forall(source, var, predicate):
    """∀ ``var`` ∈ ``source``. ``predicate`` — expressed (as the original does)
    as: the count of elements that FAIL the predicate is 0."""
    return {"type": "Eq", "b": _L(0), "a": {"type": "Count", "source": {
        "type": "Filter", "source": source, "var_name": var,
        "predicate": {"type": "Not", "arg": predicate}}}}


# distributive: ∀a ∀b ∀c.  a·(b+c) = a·b + a·c
_DISTRIBUTIVE = _forall(_CARR, "a", _forall(_CARR, "b", _forall(_CARR, "c",
    {"type": "Exists", "source": _add("b", "c"), "var_name": "bc",
     "predicate": {"type": "Exists", "source": _mul("a", "bc"), "var_name": "lhs",
        "predicate": {"type": "Exists", "source": _mul("a", "b"), "var_name": "ab",
            "predicate": {"type": "Exists", "source": _mul("a", "c"), "var_name": "ac",
                "predicate": {"type": "Exists", "source": _add("ab", "ac"), "var_name": "rhs",
                    "predicate": {"type": "Eq", "a": _V("lhs"), "b": _V("rhs")}}}}}})))


# field: ∃ additive identity z, ∃ multiplicative identity e, and every nonzero
# element a has some b with a·b = e (a multiplicative inverse).
_FIELD = {"type": "Exists", "source": _CARR, "var_name": "z", "predicate": {
    "type": "And", "items": [
        # z is the additive identity: ∀a.  z + a = a
        _forall(_CARR, "a", {"type": "In", "member": _V("a"), "container": _add("z", "a")}),
        {"type": "Exists", "source": _CARR, "var_name": "e", "predicate": {
            "type": "And", "items": [
                # e is the multiplicative identity: ∀a.  e · a = a
                _forall(_CARR, "a", {"type": "In", "member": _V("a"), "container": _mul("e", "a")}),
                # no nonzero a LACKS a multiplicative inverse: the count of a
                # with (a ≠ z AND no b s.t. a·b = e) is 0.
                {"type": "Eq", "b": _L(0), "a": {"type": "Count", "source": {
                    "type": "Filter", "source": _CARR, "var_name": "a",
                    "predicate": {"type": "And", "items": [
                        {"type": "Not", "arg": {"type": "Eq", "a": _V("a"), "b": _V("z")}},
                        {"type": "Not", "arg": {"type": "Exists", "source": _CARR, "var_name": "b",
                            "predicate": {"type": "In", "member": _V("e"),
                                          "container": _mul("a", "b")}}}]}}}}]}}]}}


def _world():
    """Boot the seed agent, drive the structure world, perceive the rings.
    Returns (adapter, {world_id -> WorldInstance NodeID})."""
    wa = WorldAdapter()
    handle = structure_world_handle(StructureWorld(), None)
    substrate, ctx = handle["reset"]()
    wa.ingest(substrate)
    for _ in range(20):
        substrate, ctx = handle["apply_action"](substrate, ctx, ("focus_next",))
        wa.ingest(substrate)
    inst = {wid: nid for (t, wid), nid in wa._instances.items()}
    return wa, inst


def test_rings_perceived():
    wa, inst = _world()
    assert "ring_Z3" in inst and "ring_Z4" in inst
    assert "Ring" in {t for (t, _) in wa._instances}


def test_distributive_holds_for_both_rings():
    wa, inst = _world()
    wa.learn_word("distributive", _DISTRIBUTIVE)
    assert "distributive" in wa._concepts
    assert wa.concept_holds("distributive", inst["ring_Z3"]) is True
    assert wa.concept_holds("distributive", inst["ring_Z4"]) is True


def test_field_distinguishes_Z3_from_Z4():
    wa, inst = _world()
    wa.learn_word("field", _FIELD)
    assert "field" in wa._concepts
    assert wa.concept_holds("field", inst["ring_Z3"]) is True     # ℤ/3 is a field
    assert wa.concept_holds("field", inst["ring_Z4"]) is False    # ℤ/4 is not
