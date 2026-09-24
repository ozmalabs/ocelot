"""Phase 0A/0B: corpus contract and deterministic trace assertions."""
from __future__ import annotations

import pytest

from evaluation.conversational_manifold_phase0 import (
    PHASE4_TRACE_CONTRACT, assert_trace_contract, load_corpus,
    validate_candidate_lifecycle_trace, validate_corpus,
)


def _observed_phase4_trace(adapter, deliberation_id, *, event_id, event_mode):
    """Project native graph attrs into the Phase 0 observed-trace contract."""
    attrs = adapter.s.node(deliberation_id)["attrs"]
    candidates = []
    for node in adapter.inner.neighbours(deliberation_id, "has_candidate"):
        candidate = adapter.s.node(node)["attrs"]
        candidates.append({
            "candidate_id": candidate["candidate_id"],
            "status": candidate["status"],
        })
    trace = {
        "event_id": event_id,
        "deliberation_id": str(deliberation_id),
        "contract": PHASE4_TRACE_CONTRACT,
        "candidate_source": attrs["candidate_source"],
        "source_candidate_count": int(attrs["source_candidate_count"]),
        "candidates": candidates,
        "status": attrs["status"],
        "candidate_trace_complete": attrs["candidate_trace_complete"],
        "event_mode": event_mode,
    }
    if attrs.get("settle_back_trace") == 1.0:
        trace["settlement"] = {"settle_back_trace": 1.0}
    return trace


def test_phase0_corpus_has_independent_cognitive_labels():
    corpus = load_corpus()
    assert validate_corpus(corpus) == []
    events = corpus["events"]
    assert 60 <= len(events) <= 100
    assert {event["event_mode"] for event in events} == {"non_turn", "turn_compatible"}
    assert {event["interaction_relation"] for event in events} >= {
        "standalone", "continuation", "overlap", "response", "turn_compatible"
    }
    assert {event["grounding_status"] for event in events} >= {
        "grounded", "unknown", "partially_grounded", "unresolved_reference",
        "unavailable_world", "contradicted"
    }
    assert {event["communicative_force"] for event in events} >= {
        "assertion", "correction", "acknowledgement", "offer", "repair",
        "refusal", "social_action", "request_information", "request_action",
    }
    assert {event["cognitive_goal"] for event in events} >= set(
        {"answer", "act", "repair", "defer", "learn", "blocked", "error",
         "update_common_ground", "coordinate_socially"})


def test_phase0_validation_rejects_missing_or_invalid_labels():
    corpus = load_corpus()
    corpus["events"][0] = dict(corpus["events"][0], communicative_force="question")
    errors = validate_corpus(corpus)
    assert any("communicative_force is invalid" in error for error in errors)


def test_phase0_candidate_trace_is_conditional_and_cross_references_phase4():
    """The fixed corpus never fabricates a candidate for a non-candidate event."""
    corpus = load_corpus()
    assert PHASE4_TRACE_CONTRACT == "seeds/conversation_deliberation_phase4a.json"
    assert all("candidate_trace" not in event for event in corpus["events"])

    # A real runtime must attach an observed deliberation node before this
    # contract can be used.  A corpus event alone is not enough.
    errors = validate_candidate_lifecycle_trace({})
    assert "candidate/lifecycle trace needs observed deliberation_id" in errors


def test_phase0_validates_observed_phase4_lifecycles_without_fabricating_candidates():
    """Only graph-produced candidate/lifecycle observations enter Phase 0."""
    pytest.importorskip("substrate_rs")
    from substrate.seed_loader import manifest_for
    from substrate.world_adapter import WorldAdapter
    from domains.conversation_deliberation import (
        materialize_from_live_thought_manifold,
        materialize_from_thought_manifold,
    )

    adapter = WorldAdapter(seeds=())
    adapter.inner.load_seed_manifest(
        manifest_for("conversation_deliberation_phase4a"), adapter.agent)
    goal = adapter.s.add_node("Goal", {"kind": "answer", "status": "active"})
    manifold = adapter.s.add_node("ThoughtManifold", {"manifold_id": "phase0-observed"})
    for candidate_id, kind, expected_value in (
            ("observed-answer", "answer", 0.8),
            ("observed-repair", "repair", 0.2)):
        candidate = adapter.s.add_node("ThoughtCandidate", {
            "candidate_id": candidate_id, "kind": kind, "grounding": 1.0,
            "expected_value": expected_value, "residual_cost": 0.1,
            "consequence": 0.1, "novelty": 0.1})
        adapter.inner.add_edge_unchecked(
            manifold, "proposes_candidate", candidate)
    deliberation = materialize_from_thought_manifold(
        adapter, goal=goal, manifold=manifold)
    adapter.inner.run_rules()
    observed = _observed_phase4_trace(
        adapter, deliberation, event_id="phase4-observed-selected",
        event_mode="non_turn")
    assert validate_candidate_lifecycle_trace(observed) == []
    assert observed["event_mode"] == "non_turn"
    assert not observed.get("turn_id")
    assert {candidate["candidate_id"] for candidate in observed["candidates"]} == {
        "observed-answer", "observed-repair"}

    empty_goal = adapter.s.add_node(
        "Goal", {"kind": "answer", "status": "active"})
    empty_manifold = adapter.s.add_node(
        "ThoughtManifold", {"manifold_id": "phase0-observed-empty"})
    empty = materialize_from_live_thought_manifold(
        adapter, goal=empty_goal, manifold=empty_manifold)
    adapter.inner.run_rules()
    no_candidate = _observed_phase4_trace(
        adapter, empty, event_id="phase4-observed-no-candidate",
        event_mode="non_turn")
    assert no_candidate["status"] == "no_candidate"
    assert no_candidate["candidates"] == []
    assert validate_candidate_lifecycle_trace(no_candidate) == []


@pytest.fixture()
def agent():
    pytest.importorskip("substrate_rs")
    from substrate.boot_all import load_all_seeds
    from substrate.world_adapter import WorldAdapter

    adapter = WorldAdapter(seeds=())
    load_all_seeds(adapter)
    adapter._donkey = {"n": 0}
    adapter.set_self_teacher(lambda q: (adapter._donkey.__setitem__("n", adapter._donkey["n"] + 1), "D")[1])
    return adapter


@pytest.mark.parametrize(
    ("signal", "speech_act", "context", "mode"),
    [
        ("How are you organised?", "question", {"interaction_mode": "streaming_observation"}, "turn_compatible"),
        ("quorplezap the door", "statement", {"interaction_mode": "asynchronous"}, "non_turn"),
        ("hello", "greeting", {"interaction_mode": "unsolicited_signal"}, "non_turn"),
    ],
)
def test_trace_is_event_based_and_turn_compatible(agent, signal, speech_act, context, mode):
    reply = agent.converse(signal, speech_act=speech_act, context=context)
    trace = agent.reply_turn_trace(agent.last_turn_inbound_id())
    assert trace is not None
    assert_trace_contract(trace, expected_mode=mode)
    assert agent._donkey["n"] == 0
    inbound = agent._last_turn_inbound
    interpretation_nodes = list(agent.inner.neighbours(inbound, "has_interpretation"))
    assert len(interpretation_nodes) == 1
    attrs = agent.s.node(interpretation_nodes[0])["attrs"]
    assert attrs["schema"] == "communication_interpretation.v1"
    assert attrs["interaction_mode"] == context["interaction_mode"]
    assert attrs["evidence_schema"] == "communication_evidence.v1"
    assert attrs["evidence_provider"] == "language_adapter"
    assert attrs["communicative_force_hypothesis"]
    assert attrs["cognitive_goal_hypothesis"]
    assert "grounding_status" in attrs
    assert "gap_count" in attrs
    assert "kind_conflict" in attrs
    assert {"parse", "goals", "mentions", "concerns", "reply_from"} <= set(trace)
    assert isinstance(trace["goals"], list)
    assert isinstance(trace["mentions"], list)
    assert isinstance(trace["concerns"], list)
    assert attrs["status"] == "selected"
