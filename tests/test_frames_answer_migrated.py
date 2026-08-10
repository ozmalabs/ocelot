"""Frame-layer answer routing — slice 3/4, on the seed-booted WorldAdapter.

The canonical "I know this kind of question" path: the module
answer_within(question, agent=wa) calls recognise_frame, builds the meaning from
the matched Frame's realised_by Concept (_meaning_from_frame), and solve
dispatches it to the CAPABILITIES compute — all because the question was
identified as in-register, not because a regex matched. A research-frontier
question matches no Frame, so the agent records an Impasse instead of fabricating
an answer.

Covers the answer-routing subset of tests/test_frames.py (seed = slice 1,
recognition = slice 2, teach->learn + semiotic + introspection = slice 4).
"""
from __future__ import annotations

import pytest

pytest.importorskip("substrate_rs")

from domains.reason import answer_within, UnknownShape
from substrate.boot_core import CORE_SEEDS
from substrate.world_adapter import WorldAdapter

_FRAMES = CORE_SEEDS + ("frames",)


def _agent():
    return WorldAdapter(seeds=_FRAMES)


def test_answer_within_routes_through_the_frame_layer():
    a = _agent()
    ans, _, strategy = answer_within(
        "What is the largest prime divisor of 8139881", {}, 1e8, agent=a)
    assert ans == 5003
    assert strategy == "default"
    assert a.impasses() == []          # recognised in-register; no impasse needed


def test_research_frontier_question_produces_an_impasse():
    a = _agent()
    with pytest.raises(UnknownShape):
        answer_within(
            "Compute the reduced 12-th dimensional Spin bordism of G2.",
            {}, 1e8, agent=a)
    assert len(a.impasses()) == 1


def test_next_batch_number_theory_capabilities_route_through_frames():
    a = _agent()
    for q, expected in [
        ("What is the factorial of 6", 720),
        ("Compute the Euler totient of 12", 4),
        ("Find the number of divisors of 60", 12),
        ("Find the sum of divisors of 12", 28),
        ("What is the Fibonacci number of 10", 55),
    ]:
        ans, _, strategy = answer_within(q, {}, 1e8, agent=a)
        assert ans == expected, f"{q!r} -> {ans!r}, expected {expected!r}"
        assert strategy == "default", f"{q!r} -> strategy {strategy!r}"


def test_predicate_frames_bind_subject_from_before_the_evoking_phrase():
    a = _agent()
    for q, expected in [
        ("Is 17 prime?", True), ("Is 4 prime?", False),
        ("Is 12 even?", True), ("Is 13 even?", False),
        ("Is 13 odd?", True),
        ("Is 144 a perfect square?", True),
        ("Is 145 a perfect square?", False),
    ]:
        ans, _, strategy = answer_within(q, {}, 1e8, agent=a)
        assert ans == expected, f"{q!r} -> {ans!r}, expected {expected!r}"
        assert strategy == "default", f"{q!r} -> strategy {strategy!r}"


def test_binary_frames_bind_two_subjects():
    a = _agent()
    for q, expected in [
        ("What is the gcd of 12 and 18", 6),
        ("What is the lcm of 4 and 6", 12),
        ("Find the gcd of 100 and 75", 25),
        ("Compute the sum of 5 and 7", 12),
        ("What is the product of 6 and 7", 42),
    ]:
        ans, _, strategy = answer_within(q, {}, 1e8, agent=a)
        assert ans == expected, f"{q!r} -> {ans!r}, expected {expected!r}"
        assert strategy == "default", f"{q!r} -> strategy {strategy!r}"
