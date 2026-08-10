"""Frame recognition — slice 2/4 of the Frame-layer migration, on the
seed-booted WorldAdapter (no CuriousAgent).

recognise_frame(question) -> (frame_id, slots, fok): the adapter PARSES the
question (I/O-boundary classification — longest evoking phrase present, subject
bound per the Frame's binding_pattern, coverage measured) into FrameMatch
candidate nodes; the SEEDED _frame_choice_term Argmax scores + gates them
(fok = hit_len*coverage + slot_bonus, gated at the 0.20 coincidence threshold)
and picks the best, scoped by the genlMt closure over operates_in. The
recognition CHOICE is graph data; only the text parse is Python.

Covers the recognition subset of tests/test_frames.py (the seed structure is
test_frames_seed_migrated; answer_within routing + teach-loop are slices 3-4).
"""
from __future__ import annotations

import pytest

pytest.importorskip("substrate_rs")

from substrate.boot_core import CORE_SEEDS
from substrate.world_adapter import WorldAdapter

_FRAMES = CORE_SEEDS + ("frames",)


def _agent():
    return WorldAdapter(seeds=_FRAMES)


def test_recogniser_evokes_seeded_frame_and_binds_subject():
    a = _agent()
    fid, slots, fok = a.recognise_frame(
        "What is the largest prime divisor of 8139881")
    assert fid == a.frame("largest_prime_factor_inquiry")
    assert slots.get("of") == 8139881 or slots.get("subject") == 8139881
    assert fok > 0


def test_recogniser_returns_no_frame_for_research_frontier_question():
    a = _agent()
    fid, slots, _ = a.recognise_frame(
        "Compute the reduced 12-th dimensional Spin bordism of the classifying"
        " space of the Lie group G2.")
    assert fid is None
    assert slots == {}


def test_recogniser_respects_mt_scope():
    a = _agent()
    # strip the agent's competence scope, point it at an off-topic Mt — every
    # seeded frame is in mathematics, so none should be in scope.
    for mt in list(a.inner.neighbours(a.agent, "operates_in")):
        a.inner.remove_edge(a.agent, "operates_in", mt)
    dd = a.s.add_node("Microtheory", {"name": "daydream", "description": "off-topic"})
    a.inner.add_edge_unchecked(a.agent, "operates_in", dd)
    fid, _, _ = a.recognise_frame("What is the largest prime divisor of 12")
    assert fid is None


def test_predicate_frame_rejects_function_shaped_question():
    a = _agent()
    fid, _, _ = a.recognise_frame("What is the prime of 17")
    if fid is not None:
        assert a.s.node(fid)["attrs"].get("name") != "primality_inquiry"


def test_binary_frame_rejects_missing_second_subject():
    a = _agent()
    fid, _, _ = a.recognise_frame("What is the gcd of 100")
    assert fid is None


def test_coverage_only_counts_numeric_bound_subjects():
    a = _agent()
    fid, _, _ = a.recognise_frame("What is the order of the Mathieu group M11?")
    assert fid is None        # non-numeric, long subject -> coverage gate rejects


def test_predicate_frame_binds_subject_before_the_phrase():
    a = _agent()
    fid, slots, _ = a.recognise_frame("Is 17 prime?")
    assert fid == a.frame("primality_inquiry")
    assert slots.get("arg") == 17


def test_binary_frame_binds_two_subjects():
    a = _agent()
    fid, slots, _ = a.recognise_frame("What is the gcd of 12 and 18")
    assert fid == a.frame("gcd_inquiry")
    assert slots.get("a") == 12 and slots.get("b") == 18
