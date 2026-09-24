"""Phase 4: live communication evidence reaches native deliberation."""

from substrate.boot_all import load_all_seeds
from substrate.world_adapter import WorldAdapter


def _agent():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    return agent


def _event_goal(agent, text):
    mid = agent.receive_utterance(text, speaker="alice")
    state, event = agent._record_live_discourse_state(mid, None)
    goal = agent.s.add_node("Goal", {
        "kind": "answer", "status": "active", "origin_turn_id": int(mid.value),
    })
    agent.inner.add_edge_unchecked(agent.agent, "has_goal", goal)
    agent.inner.add_edge_unchecked(goal, "comprehends", mid)
    return mid, state, event, goal


def test_grounded_live_event_materializes_native_candidate_lifecycle_and_trace():
    agent = _agent()
    mid, state, event, goal = _event_goal(agent, "The gate is open.")
    grounded = agent.s.add_node("Concept", {
        "name": "gate-open-grounded",
        "candidate_id": "grounded-gate",
        "grounding": 1.0,
        "expected_value": 0.8,
        "residual_cost": 0.1,
        "consequence": 0.6,
        "novelty": 0.2,
        "execution_ready": 1.0,
        "outcome_status": "resolved",
        "evidence_path": "grounded_concept->relation->event",
    })
    unsupported = agent.s.add_node("Relation", {
        "name": "unresolved-alternative",
        "candidate_id": "unsupported-alternative",
        "grounding": 0.0,
        "expected_value": 0.9,
        "residual_cost": 0.0,
        "consequence": 0.9,
        "novelty": 0.9,
        "evidence_path": "event->unresolved_relation",
    })
    agent.inner.add_edge_unchecked(event, "grounded_in", grounded)
    agent.inner.add_edge_unchecked(event, "grounded_in", unsupported)

    agent._bind_live_goals_and_deliberation(mid)
    agent._bind_live_goals_and_deliberation(mid)

    manifolds = [m for m in agent.s.nodes("ThoughtManifold")
                 if m in agent.inner.in_neighbours(
                     event, "generated_from_discourse_event")]
    assert len(manifolds) == 1
    source_candidates = list(agent.inner.neighbours(manifolds[0], "has_goal_evidence"))
    assert len(source_candidates) == 2

    deliberations = [d for d in agent.s.nodes("Deliberation")
                     if goal in agent.inner.neighbours(d, "about_goal")]
    assert len(deliberations) == 1
    d = deliberations[0]
    attrs = agent.s.node(d)["attrs"]
    assert attrs["candidate_source"] == "live_thought_manifold"
    assert attrs["source_candidate_count"] == 2.0
    assert attrs["candidate_trace_complete"] == 1.0
    assert attrs["status"] == "resolved"
    assert list(agent.inner.neighbours(d, "has_selection"))
    assert list(agent.inner.neighbours(d, "has_settlement"))

    ledger = [agent.s.node(c)["attrs"]
              for c in agent.inner.neighbours(d, "has_candidate")]
    unsupported_ledger = next(
        attrs for attrs in ledger
        if attrs["candidate_id"].endswith(":unsupported-alternative"))
    assert unsupported_ledger["rejection_trace"] == 1.0
    # ``receive_utterance`` is the graph-ingest path and does not mint an
    # interlocutor reply trace; the native lifecycle above is the contract
    # under test here.


def test_unsupported_live_event_remains_native_no_candidate_without_defaults():
    agent = _agent()
    mid, state, event, goal = _event_goal(agent, "What is beyond the wall?")

    agent._bind_live_goals_and_deliberation(mid)
    agent._bind_live_goals_and_deliberation(mid)

    deliberations = [d for d in agent.s.nodes("Deliberation")
                     if goal in agent.inner.neighbours(d, "about_goal")]
    assert len(deliberations) == 1
    attrs = agent.s.node(deliberations[0])["attrs"]
    assert attrs["candidate_source"] == "discourse_state"
    assert attrs["source_candidate_count"] == 0.0
    assert attrs["status"] == "no_candidate"
    assert attrs["candidate_trace_complete"] == 1.0
    assert not list(agent.inner.neighbours(deliberations[0], "has_candidate"))
