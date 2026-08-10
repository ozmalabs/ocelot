"""number_world, migrated — its PERCEPTION and grounding run on the seed-booted
agent.

The burn template (see docs/burn_readiness.md): drive `number_world` through the
`WorldAdapter` over `boot_core` instead of `CuriousAgent`. The adapter ingests
the world's published substrate into `WorldInstance` nodes (mechanical mirror);
the agent's perception is the loaded seeds. NO `CuriousAgent` here.

This fully covers `tests/test_number_world.py`:
  * structure perceived            -> WorldInstance Number/Unit mirror;
  * magnitude grounded in cardinality -> value == #has_unit on small numbers;
  * even/prime taught as Terms, classified by the seed agent's own evaluator
    over the grounded definition (`learn_word` + `concept_holds`);
  * a concept needing structure the world lacks (a function's `limit`) is HELD
    awaiting, not fabricated -> `learn_word_grounds` reads the grounding gate
    (every attribute the definition names must have been perceived) and refuses
    to register the Concept, the mechanical mirror of `learn_word_term`'s
    `_unmet_dependencies`/`_is_attr_perceived` gate.
"""
from __future__ import annotations

from substrate.world_adapter import WorldAdapter
from domains.number_world import NumberWorld


def _walk_number_line(up_to: int = 18):
    """Boot the seed agent, walk the line up then down, ingesting each step.
    Returns (adapter, {value -> Number-instance NodeID})."""
    wa = WorldAdapter()
    world = NumberWorld(max_n=up_to + 4)
    substrate, ctx = world.reset()
    wa.ingest(substrate)
    for _ in range(up_to):
        substrate, ctx = world.apply_action(ctx, ("count_up",))
        wa.ingest(substrate)
    for _ in range(up_to):
        substrate, ctx = world.apply_action(ctx, ("count_down",))
        wa.ingest(substrate)
    nums = {wa.instance_attr(nid, "value"): nid
            for nid in wa.instances("Number").values()}
    return wa, nums


def test_number_structure_is_perceived_via_seed_agent():
    wa, nums = _walk_number_line(18)
    assert len(nums) >= 16
    assert len(wa.instances("Unit")) > 0


def test_magnitude_grounded_in_cardinality_via_seed_agent():
    wa, nums = _walk_number_line(18)
    for k in (2, 3, 5, 8):
        units = len(wa.instance_neighbours(nums[k], "has_unit"))
        assert wa.instance_attr(nums[k], "value") == units == k


# --- grounding: words taught as Terms, classified by the seed agent ---------

_V = lambda n: {"type": "Var", "name": n}
_L = lambda x: {"type": "Lit", "value": x}
_M = lambda v: {"type": "Attr", "node": _V(v), "key": "value"}


def test_even_grounds_via_seed_agent():
    wa, nums = _walk_number_line(18)
    even = {"type": "Eq", "a": {"type": "Mod", "a": _M("x"), "b": _L(2)}, "b": _L(0)}
    # value is perceived, so the word GROUNDS (registers a Concept).
    assert wa.learn_word_grounds("even", even) is True
    for k in (2, 3, 4, 7, 8, 13, 16):
        assert wa.concept_holds("even", nums[k]) == (k % 2 == 0)


def test_prime_grounds_via_seed_agent():
    wa, nums = _walk_number_line(18)
    known = {"type": "Filter",
             "source": {"type": "Neighbours", "node": _V("agent"), "edge_type": "knows"},
             "var_name": "d",
             "predicate": {"type": "Eq", "a": {"type": "Attr", "node": _V("d"), "key": "world_type"},
                           "b": _L("Number")}}
    prime = {"type": "And", "items": [
        {"type": "Gt", "a": _M("x"), "b": _L(1)},
        {"type": "Not", "arg": {"type": "Exists", "source": known, "var_name": "d",
            "predicate": {"type": "And", "items": [
                {"type": "Gt", "a": _M("d"), "b": _L(1)},
                {"type": "Lt", "a": _M("d"), "b": _M("x")},
                {"type": "Eq", "a": {"type": "Mod", "a": _M("x"), "b": _M("d")}, "b": _L(0)}]}}}]}
    assert wa.learn_word_grounds("prime", prime) is True

    def is_prime(n):
        return n > 1 and all(n % d for d in range(2, n))
    for k in (2, 3, 4, 5, 6, 7, 9, 11, 13, 16, 17):
        assert wa.concept_holds("prime", nums[k]) == is_prime(k)


def test_concept_needing_absent_structure_is_held_via_seed_agent():
    """continuous_at refers to a `limit` attribute the number world never
    produces — it is HELD awaiting, not fabricated. The seed agent registers no
    Concept for it (mirror of `learn_word_term` returning False / leaving the
    word out of `_concept_nodes`)."""
    wa, _ = _walk_number_line(6)
    cont = {"type": "Eq", "a": {"type": "Attr", "node": _V("x"), "key": "limit"},
            "b": {"type": "Attr", "node": _V("x"), "key": "value"}}
    assert wa.learn_word_grounds("continuous_at", cont) is False
    assert wa.concept_holds("continuous_at", None) is False
