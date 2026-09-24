"""Focused regressions for the live event/goal/deliberation bridge."""

from substrate.boot_all import load_all_seeds
from substrate.world_adapter import WorldAdapter


def _agent():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    return agent


def test_action_path_binds_event_goal_and_empty_deliberation_before_return():
    agent = _agent()
    agent.converse("Check the pressure.", speech_act="instruction",
                   speaker="alice", context={"interaction_mode": "non_turn"})
    mid = agent._last_turn_inbound
    state = agent.s.node(mid)["attrs"]["discourse_state_id"]
    event = agent.s.node(mid)["attrs"]["discourse_event_id"]
    goals = [g for g in agent.inner.neighbours(agent.agent, "has_goal")
             if mid in agent.inner.neighbours(g, "comprehends")]
    assert goals
    deliberations = [d for d in agent.s.nodes("Deliberation")
                     if goals[0] in agent.inner.neighbours(d, "about_goal")]
    assert deliberations
    attrs = agent.s.node(deliberations[0])["attrs"]
    assert attrs["status"] == "no_candidate"
    assert attrs["candidate_trace_complete"] == 1.0
    assert event in agent.inner.neighbours(deliberations[0],
                                           "generated_from_discourse_event")
    assert state in agent.inner.neighbours(deliberations[0],
                                           "generated_from_discourse_state")


def test_empty_live_deliberation_has_no_invented_candidate_evidence():
    agent = _agent()
    mid = agent.receive_utterance("Check the pressure.", speaker="alice")
    agent._record_live_discourse_state(mid, None)
    goal = agent.s.add_node("Goal", {"kind": "instruction", "status": "active"})
    agent.inner.add_edge_unchecked(agent.agent, "has_goal", goal)
    agent.inner.add_edge_unchecked(goal, "comprehends", mid)
    agent._bind_live_goals_and_deliberation(mid)
    deliberations = list(agent.s.nodes("Deliberation"))
    assert len(deliberations) == 1
    attrs = agent.s.node(deliberations[0])["attrs"]
    assert attrs["candidate_source"] == "discourse_state"
    assert attrs["source_candidate_count"] == 0.0
    assert not list(agent.inner.neighbours(deliberations[0], "has_candidate"))
    assert attrs["status"] == "no_candidate"
    assert attrs["candidate_trace_complete"] == 1.0


def test_event_uses_message_speaker_and_received_agent_provenance():
    agent = _agent()
    agent.converse("Hello.", speech_act="statement", speaker="alice")
    mid = agent._last_turn_inbound
    event = agent.s.node(mid)["attrs"]["discourse_event_id"]
    speakers = list(agent.inner.neighbours(event, "from_speaker"))
    assert len(speakers) == 1
    assert agent.s.node(speakers[0])["attrs"]["name"] == "alice"
    assert agent.agent in agent.inner.neighbours(event, "to_addressee")


def test_discourse_event_preserves_typed_interaction_metadata():
    agent = _agent()
    agent.converse(
        "Where—", speech_act="statement", speaker="alice",
        context={
            "interaction_mode": "non_turn",
            "interaction_relation": "overlap",
            "literal_form": "fragment",
        })
    mid = agent._last_turn_inbound
    event = agent.s.node(mid)["attrs"]["discourse_event_id"]
    payload = agent.s.node(event)["attrs"]["payload"]
    assert payload["interaction_relation"] == "overlap"
    assert payload["literal_form"] == "fragment"


def test_native_arbitration_consumes_typed_overlap_as_cognitive_disposition():
    agent = _agent()
    agent.converse(
        "Where—", speech_act="statement", speaker="alice",
        context={
            "interaction_mode": "non_turn",
            "interaction_relation": "overlap",
            "literal_form": "fragment",
        })
    mid = agent._last_turn_inbound
    interpretation = agent.s.node(
        agent.s.node(mid)["attrs"]["communication_interpretation_id"])
    attrs = interpretation["attrs"]
    assert attrs["cognitive_disposition"] == "defer"
    assert attrs["arbitration_basis"] == "typed_overlap_partial_event"
    assert attrs["interaction_mode"] == "non_turn"


def test_core_only_boot_loads_native_interaction_arbitration_on_demand():
    # Production-shaped minimal boot: no load_all_seeds() call. The selected
    # communication faculty must still interpret typed, non-turn overlap from
    # graph evidence rather than falling through to an ask-back-only route.
    agent = WorldAdapter()
    agent.converse(
        "Where—", speech_act="statement", speaker="alice",
        context={
            "interaction_mode": "non_turn",
            "interaction_relation": "overlap",
            "literal_form": "fragment",
        })
    mid = agent._last_turn_inbound
    interpretation = agent.s.node(
        agent.s.node(mid)["attrs"]["communication_interpretation_id"])
    attrs = interpretation["attrs"]
    assert attrs["cognitive_disposition"] == "defer"
    assert attrs["arbitration_basis"] == "typed_overlap_partial_event"
    native_rules = agent.inner.export_rules_prefix(
        "arbitrate_typed_overlap_fragment_as_defer")
    assert any(rule.get("name") ==
               "arbitrate_typed_overlap_fragment_as_defer"
               for rule in native_rules)



def test_unresolved_topic_is_evidence_but_not_grounded_current_topic():
    agent = _agent()
    agent.converse("Why did the qux close?", speech_act="question",
                   speaker="alice")
    mid = agent._last_turn_inbound
    state = agent.s.node(agent.s.node(mid)["attrs"]["discourse_state_id"])
    event = agent.s.node(agent.s.node(mid)["attrs"]["discourse_event_id"])
    interpretation = agent.s.node(
        agent.s.node(mid)["attrs"]["communication_interpretation_id"])
    assert interpretation["attrs"].get("grounding_status") != "candidate_grounded"
    assert state["attrs"].get("current_topic") is None
    assert event["attrs"]["topic"] is None
    assert event["attrs"]["payload"].get("parsed_topic")
    assert event["attrs"]["payload"].get("grounding_status") != "candidate_grounded"


def test_live_deliberation_integration_failure_is_graph_auditable_and_fail_closed():
    agent = _agent()

    def fail(*args, **kwargs):
        raise RuntimeError("synthetic bridge failure")

    agent._live_thought_manifold_evidence = fail
    agent.converse("Check the pressure.", speech_act="instruction",
                   speaker="alice", context={"interaction_mode": "non_turn"})
    mid = agent._last_turn_inbound
    agent._bind_live_goals_and_deliberation(mid)
    diagnostics = list(agent.s.nodes("CognitiveIntegrationDiagnostic"))
    assert len(diagnostics) == 1
    attrs = agent.s.node(diagnostics[0])["attrs"]
    assert attrs["schema"] == "cognitive_integration_diagnostic.v1"
    assert attrs["stage"] == "phase4_live_deliberation"
    assert attrs["status"] == "error"
    assert attrs["error_type"] == "RuntimeError"
    assert attrs["surface_fallback"] is False
    assert mid in agent.inner.neighbours(diagnostics[0], "for_message")
    assert not any(agent.s.node(d)["attrs"].get("status") == "selected"
                   for d in agent.s.nodes("Deliberation"))
