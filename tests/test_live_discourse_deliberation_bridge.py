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


def test_live_held_graph_path_is_partial_grounding_not_a_candidate():
    from evaluation.phase4_partial_evidence_audit import audit_live_event

    agent = _agent()
    topic = agent._ensure_concept("moon")
    fact = agent._ensure_concept("satellite")
    agent.inner.add_edge_unchecked(topic, "causal_influence", fact)
    mid = agent.receive_utterance("What do you know about the moon?",
                                  speech_act="question")
    agent._record_live_discourse_state(mid, None)
    message_attrs = agent.s.node(mid)["attrs"]
    event = message_attrs["discourse_event_id"]
    state = message_attrs["discourse_state_id"]
    goal = agent.s.add_node("Goal", {
        "kind": "answer_topic", "concept": "moon", "status": "active",
    })
    agent.inner.add_edge_unchecked(agent.agent, "has_goal", goal)
    agent.inner.add_edge_unchecked(goal, "comprehends", mid)
    agent.inner.add_edge_unchecked(goal, "originated_in", event)
    agent.inner.add_edge_unchecked(state, "has_active_goal", goal)

    agent._bind_live_goals_and_deliberation(mid)

    report = audit_live_event(agent, event)
    assert report["source_count"] == 1
    assert report["complete_tuple_count"] == 0
    assert report["promotion_count"] == 0
    source = next(node for node in agent.s.nodes("Phase4PartialEvidence")
                  if event in agent.inner.neighbours(node, "evidence_for_event"))
    source_attrs = agent.s.node(source)["attrs"]
    assert source_attrs["evidence_faculty"] == "self_dialogue"
    assert source_attrs["phase4_dimensions_present"] == ["grounding"]
    assert source_attrs["grounding_measure"] == "binary_held_graph_path_presence"
    assert not list(agent.inner.neighbours(source, "proposes_candidate"))
    deliberations = [d for d in agent.s.nodes("Deliberation")
                     if event in agent.inner.neighbours(
                         d, "generated_from_discourse_event")]
    assert len(deliberations) == 1
    assert agent.s.node(deliberations[0])["attrs"]["status"] == "no_candidate"
    assert not list(agent.inner.neighbours(deliberations[0], "has_candidate"))


def test_live_held_topic_answer_projects_grounding_only_not_a_candidate():
    from evaluation.phase4_partial_evidence_audit import audit_live_event

    agent = _agent()
    agent._ensure_concept("sensor")
    held_answer = agent._persist_held_answer("sensor", "nominal")
    assert held_answer is not None
    mid = agent.receive_utterance("What is the sensor status?",
                                  speech_act="question")
    agent._record_live_discourse_state(mid, None)
    message_attrs = agent.s.node(mid)["attrs"]
    event = message_attrs["discourse_event_id"]
    state = message_attrs["discourse_state_id"]
    goal = agent.s.add_node("Goal", {
        "kind": "answer_topic", "concept": "sensor", "status": "active",
    })
    agent.inner.add_edge_unchecked(agent.agent, "has_goal", goal)
    agent.inner.add_edge_unchecked(goal, "comprehends", mid)
    agent.inner.add_edge_unchecked(goal, "originated_in", event)
    agent.inner.add_edge_unchecked(state, "has_active_goal", goal)

    agent._bind_live_goals_and_deliberation(mid)

    report = audit_live_event(agent, event)
    assert report["source_count"] == 1
    assert report["complete_tuple_count"] == 0
    assert report["promotion_count"] == 0
    source = next(node for node in agent.s.nodes("Phase4PartialEvidence")
                  if event in agent.inner.neighbours(node, "evidence_for_event"))
    attrs = agent.s.node(source)["attrs"]
    assert attrs["evidence_faculty"] == "topic_grounding"
    assert attrs["phase4_dimensions_present"] == ["grounding"]
    assert attrs["grounding_measure"] == (
        "binary_supported_held_topic_answer_path_presence")
    assert held_answer in agent.inner.neighbours(source, "held_answer")
    assert not list(agent.inner.neighbours(source, "proposes_candidate"))
    deliberations = [d for d in agent.s.nodes("Deliberation")
                     if event in agent.inner.neighbours(
                         d, "generated_from_discourse_event")]
    assert len(deliberations) == 1
    assert agent.s.node(deliberations[0])["attrs"]["status"] == "no_candidate"
    assert not list(agent.inner.neighbours(deliberations[0], "has_candidate"))


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


def test_refusal_with_imperative_complement_keeps_refusal_evidence():
    agent = _agent()
    reply = agent.converse(
        "No, hold position.", speech_act="refusal", speaker="alice",
        context={"interaction_mode": "turn_compatible",
                 "interaction_relation": "response"})
    mid = agent._last_turn_inbound
    interpretation = agent.s.node(
        agent.s.node(mid)["attrs"]["communication_interpretation_id"])
    attrs = interpretation["attrs"]
    assert attrs["evidence_force"] == "refusal"
    assert attrs["cognitive_disposition"] == "defer"
    assert attrs["arbitration_basis"] == "typed_refusal"
    assert reply is None
    assert agent.graph_turn_reply_expectation(mid)["status"] == "not_expected"
    assert agent.graph_turn_reply_outcome(mid) == "not_expected"
    assert not [message for message in agent.agent_outbound_messages()
                if mid in agent.responds_to(message)]


def test_unanswered_reason_question_selects_learning_not_user_repair():
    agent = _agent()
    reply = agent.converse("Why did the alarm trigger?", speech_act="question",
                           speaker="alice")
    mid = agent._last_turn_inbound
    interpretation = agent.s.node(
        agent.s.node(mid)["attrs"]["communication_interpretation_id"])
    attrs = interpretation["attrs"]
    assert attrs["relation_focus"] == "reason"
    assert attrs["relation_support"] == "missing"
    assert attrs["cognitive_disposition"] == "learn"
    assert attrs["cognitive_goal"] == "answer_or_learn"
    assert attrs["arbitration_basis"] == "missing_causal_relation_evidence"
    # A `learn` disposition is not itself evidence of a cause. Until a native
    # causal path and production commitment exist, release must fail closed.
    assert reply == "ERROR: no communicative response could be generated."


def test_async_ingress_materializes_neutral_evidence_for_native_arbitration():
    # This is the daemon's real input boundary: materialize evidence now, then
    # let native quanta arbitrate it. It must not bypass cognition or fall back
    # to converse()'s synchronous selector.
    agent = WorldAdapter()
    mid = agent.ingest_turn(
        "Where—", speech_act="statement",
        context={
            "interaction_mode": "non_turn",
            "interaction_relation": "overlap",
            "literal_form": "fragment",
        })
    interpretation_id = agent.s.node(mid)["attrs"].get(
        "communication_interpretation_id")
    assert interpretation_id is not None
    attrs = dict(agent.s.node(interpretation_id)["attrs"])
    assert attrs["schema"] == "communication_interpretation.v1"
    assert attrs["evidence_schema"] == "communication_evidence.v1"
    assert attrs["interaction_mode"] == "non_turn"
    assert attrs["interaction_relation"] == "overlap"
    assert attrs["literal_form"] == "fragment"
    assert attrs["cognitive_disposition"] is None

    # `tick` and `comprehend` invoke graph/native arbitration; Python has only
    # transported the selected parse and the typed partial-event evidence.
    agent.tick()
    agent.comprehend()
    settled = dict(agent.s.node(interpretation_id)["attrs"])
    assert settled["cognitive_disposition"] == "defer"
    assert settled["arbitration_basis"] == "typed_overlap_partial_event"


def test_native_arbitration_defers_typed_uncertain_continuation_fragment():
    agent = _agent()
    agent.converse(
        "Please—", speech_act="statement", speaker="alice",
        context={
            "interaction_mode": "non_turn",
            "interaction_relation": "continuation",
            "literal_form": "fragment",
            "evidence": ["explicit_uncertainty", "discourse_state"],
        })
    mid = agent._last_turn_inbound
    interpretation = agent.s.node(
        agent.s.node(mid)["attrs"]["communication_interpretation_id"])
    attrs = interpretation["attrs"]
    assert attrs["cognitive_disposition"] == "defer"
    assert attrs["arbitration_basis"] == "typed_continuation_fragment"


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


def test_live_deliberation_seed_probe_uses_scoped_native_rule_readback(monkeypatch):
    agent = WorldAdapter(seeds=())

    def fail_full_export(_self):
        raise AssertionError("Phase 4 seed probe must not export every held rule")

    # The native facade forwards ordinary native methods through __getattr__;
    # patch its instance seam rather than requiring export_rules to be a class
    # attribute on the facade itself.
    monkeypatch.setattr(agent.inner, "export_rules", fail_full_export,
                        raising=False)

    assert agent._ensure_live_deliberation_seeds() is True
    assert any(rule.get("name") == "cm4a_no_candidate"
               for rule in agent.inner.export_rules_prefix("cm4a_"))



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
