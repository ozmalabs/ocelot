"""Frame-layer teach->learn loop + semiotic definitions — slice 4 (teaching),
on the seed-booted WorldAdapter.

When the agent can't recognise a question it records an Impasse and escalates to
the teacher; the teacher's `learn` payload INSTALLS a Frame (+ its Concept, Mt,
operates_in) so the SECOND ask recognises it and routes through the agent's own
machinery (strategy "learned"), no impasse. With a `language` spec the teaching
is a COMPUTABLE semiotic definition (a DSL Term evaluated against the subject) —
one teaching, many computed answers — that OVERRIDES the memoised answer.

Covers the teaching subset of tests/test_frames.py. (The async master_tick
teacher-thread reflex + op-introspection are slice 4c.)
"""
from __future__ import annotations

import os
import tempfile

import pytest

pytest.importorskip("substrate_rs")

from domains.reason import answer_within
from substrate.boot_core import CORE_SEEDS
from substrate.world_adapter import WorldAdapter

_FRAMES = CORE_SEEDS + ("frames",)


def _agent():
    return WorldAdapter(seeds=_FRAMES)


def test_taught_operation_installs_a_frame_and_routes_through_it():
    a = _agent()
    calls = []

    def teacher(q):
        calls.append(q)
        return {"answer": "42", "learn": [{"phrase": "frobnicator number"}]}

    ans1, _, strat1 = answer_within(
        "Compute the frobnicator number of 7", {}, 1e8, teacher=teacher, agent=a)
    assert ans1 == "42" and strat1 == "taught"
    assert a.frame("taught_frobnicator_number_inquiry") is not None
    impasses_after_first = len(a.impasses())

    ans2, _, strat2 = answer_within(
        "Compute the frobnicator number of 7", {}, 1e8, teacher=teacher, agent=a)
    assert ans2 == "42" and strat2 == "learned"
    assert len(calls) == 1
    assert len(a.impasses()) == impasses_after_first


def test_teacher_can_install_a_new_microtheory_with_a_frame():
    a = _agent()
    assert a.microtheory("algebraic_topology") is None

    def teacher(q):
        return {"answer": "Z+Z+Z+Z+Z",
                "learn": [{"phrase": "spin bordism", "microtheory": "algebraic_topology",
                           "genl_mt": "mathematics",
                           "binding_pattern": "function_of_subject"}]}

    ans1, _, strat1 = answer_within(
        "What is the spin bordism of 12", {}, 1e8, teacher=teacher, agent=a)
    assert ans1 == "Z+Z+Z+Z+Z" and strat1 == "taught"
    mt = a.microtheory("algebraic_topology")
    assert mt is not None and mt in a._agent_scope_mts()
    f = a.frame("taught_spin_bordism_inquiry")
    assert f is not None
    assert mt in set(a.inner.neighbours(f, "holds_in"))


def test_teacher_can_install_a_predicate_frame():
    a = _agent()

    def teacher(q):
        return {"answer": True,
                "learn": [{"phrase": "magic", "binding_pattern": "predicate_of_subject"}]}

    ans1, _, strat1 = answer_within("Is 7 magic?", {}, 1e8, teacher=teacher, agent=a)
    assert ans1 is True and strat1 == "taught"
    ans2, _, strat2 = answer_within("Is 7 magic?", {}, 1e8, teacher=lambda _: None, agent=a)
    assert ans2 is True and strat2 == "learned"


def test_teacher_can_install_a_binary_frame():
    a = _agent()

    def teacher(q):
        return {"answer": 42,
                "learn": [{"phrase": "qux combine",
                           "binding_pattern": "function_of_two_subjects",
                           "slot_a": "a", "slot_b": "b"}]}

    ans1, _, strat1 = answer_within(
        "What is the qux combine of 3 and 4", {}, 1e8, teacher=teacher, agent=a)
    assert ans1 == 42 and strat1 == "taught"
    ans2, _, strat2 = answer_within(
        "What is the qux combine of 3 and 4", {}, 1e8, teacher=lambda _: None, agent=a)
    assert ans2 == 42 and strat2 == "learned"


def test_agent_self_teaches_from_its_own_impasses():
    a = _agent()
    teacher_calls = []

    def self_teacher(q):
        teacher_calls.append(q)
        return {"answer": "42",
                "learn": [{"phrase": "garbloop", "microtheory": "garbology",
                           "binding_pattern": "function_of_subject"}]}

    a.set_self_teacher(self_teacher)
    ans1, _, strat1 = answer_within("What is the garbloop of 7", {}, 1e8, agent=a)
    assert ans1 == "42" and strat1 == "taught"
    assert len(teacher_calls) == 1
    impasses = a.impasses()
    assert len(impasses) == 1
    assert a.s.node(impasses[0])["attrs"]["question"] == "What is the garbloop of 7"
    assert a.s.node(impasses[0])["attrs"]["resolved"] is True
    assert a.microtheory("garbology") is not None

    ans2, _, strat2 = answer_within("What is the garbloop of 7", {}, 1e8, agent=a)
    assert ans2 == "42" and strat2 == "learned"
    assert len(teacher_calls) == 1


def test_unresolved_impasses_introspector():
    from domains.reason import UnknownShape
    a = _agent()
    with pytest.raises(UnknownShape):
        answer_within("Compute the frob of M.", {}, 1e8, agent=a)
    assert len(a.unresolved_impasses()) == 1


def test_teacher_can_install_a_computable_semiotic_definition():
    a = _agent()
    a.set_self_teacher(lambda q: {
        "answer": True,
        "learn": [{"phrase": "modtwo", "binding_pattern": "predicate_of_subject",
                   "language": ["Eq", ["Mod", "value", 2], 0]}]})
    ans, _, strat = answer_within("Is 2 modtwo?", {}, 1e8, agent=a)
    assert ans is True and strat == "taught"
    for n, expected in ((3, False), (4, True), (7, False), (100, True),
                        (1001, False), (99998, True)):
        ans, _, strategy = answer_within(f"Is {n} modtwo?", {}, 1e8, agent=a)
        assert ans is expected, f"{n} -> {ans}, expected {expected}"
        assert strategy == "learned"
    assert a.semiotic_spec("taught_modtwo") == ["Eq", ["Mod", "value", 2], 0]


def test_semiotic_definition_overrides_memoised_lookup():
    a = _agent()
    a.set_self_teacher(lambda q: {
        "answer": "MEMOISED",
        "learn": [{"phrase": "modfour", "binding_pattern": "predicate_of_subject",
                   "language": ["Eq", ["Mod", "value", 4], 0]}]})
    answer_within("Is 8 modfour?", {}, 1e8, agent=a)
    assert answer_within("Is 12 modfour?", {}, 1e8, agent=a)[0] is True
    assert answer_within("Is 13 modfour?", {}, 1e8, agent=a)[0] is False


def test_semiotic_definition_round_trips_through_persistence(tmp_path):
    a = _agent()
    a.set_self_teacher(lambda q: {
        "answer": True,
        "learn": [{"phrase": "modthree", "binding_pattern": "predicate_of_subject",
                   "language": ["Eq", ["Mod", "value", 3], 0]}]})
    answer_within("Is 9 modthree?", {}, 1e8, agent=a)
    path = str(tmp_path / "agent.json")
    a.save(path)
    b = WorldAdapter.load(path)
    assert "taught_modthree" in b._semiotic_definitions
    ans, _, strat = answer_within("Is 15 modthree?", {}, 1e8, agent=b)
    assert ans is True and strat == "learned"
    assert answer_within("Is 17 modthree?", {}, 1e8, agent=b)[0] is False


def test_frame_layer_survives_persistence(tmp_path):
    a = _agent()
    path = str(tmp_path / "agent.json")
    a.save(path)
    b = WorldAdapter.load(path)
    assert b.microtheory("elementary_arithmetic") is not None
    assert b.frame("largest_prime_factor_inquiry") is not None
    fid = b.frame("largest_prime_factor_inquiry")
    assert b.microtheory("elementary_arithmetic") in set(b.inner.neighbours(fid, "holds_in"))
