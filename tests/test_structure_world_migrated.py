"""structure_world, migrated — perception + set/function grounding on the seed
agent via the WorldAdapter (no CuriousAgent). Covers all four checks of the old
tests/test_structure_world.py: sets/functions perceived, and member / subset /
injective taught as Terms and classified correctly.
"""
from __future__ import annotations

from substrate.world_adapter import WorldAdapter
from domains.structure_world import StructureWorld, structure_world_handle

_V = lambda n: {"type": "Var", "name": n}
_L = lambda x: {"type": "Lit", "value": x}
_NB = lambda v, e: {"type": "Neighbours", "node": _V(v), "edge_type": e}


def _world():
    wa = WorldAdapter()
    handle = structure_world_handle(StructureWorld(), None)
    substrate, ctx = handle["reset"]()
    wa.ingest(substrate)
    for _ in range(8):
        substrate, ctx = handle["apply_action"](substrate, ctx, ("focus_next",))
        wa.ingest(substrate)
    inst = {wid: nid for (t, wid), nid in wa._instances.items()}
    return wa, inst


def test_sets_and_functions_perceived_via_seed_agent():
    wa, inst = _world()
    for key in ("set_A", "set_B", "set_C", "fn_f", "fn_g", "e1", "e4"):
        assert key in inst
    types = {t for (t, _) in wa._instances}
    assert {"MathSet", "Function", "Element", "OrderedPair"} <= types


def test_member_grounds_via_seed_agent():
    wa, inst = _world()
    wa.learn_word("member", {"type": "In", "member": _V("x"), "container": _NB("y", "element")})
    assert wa.concept_holds("member", inst["e1"], y=inst["set_A"]) is True
    assert wa.concept_holds("member", inst["e4"], y=inst["set_A"]) is False


def test_subset_grounds_via_seed_agent():
    wa, inst = _world()
    subset = {"type": "Eq", "a": {"type": "Count", "source": {"type": "Filter",
        "source": _NB("x", "element"), "var_name": "e",
        "predicate": {"type": "Not", "arg": {"type": "In", "member": _V("e"),
                                             "container": _NB("y", "element")}}}}, "b": _L(0)}
    wa.learn_word("subset", subset)
    assert wa.concept_holds("subset", inst["set_C"], y=inst["set_A"]) is True
    assert wa.concept_holds("subset", inst["set_A"], y=inst["set_B"]) is False


def test_injective_grounds_via_seed_agent():
    wa, inst = _world()
    inj = {"type": "Eq", "a": {"type": "Count", "source": _NB("x", "pair")},
           "b": {"type": "Count", "source": {"type": "MapNeighbours",
                 "source": _NB("x", "pair"), "edge_type": "cod"}}}
    wa.learn_word("injective", inj)
    assert wa.concept_holds("injective", inst["fn_f"]) is True
    assert wa.concept_holds("injective", inst["fn_g"]) is False
