"""The cognition rules must work from neutral adapter evidence alone.

These events deliberately omit English predicates, word order, POS, mood, and
dispatch-path labels. They model the output of a second semantic adapter.
"""
from __future__ import annotations

import pytest

pytest.importorskip("substrate_rs")

from substrate.boot_all import load_all_seeds
from substrate.world_adapter import WorldAdapter
from domains.communication_evidence import from_semantic_frame


EVENTS = [
    ("information", "information_request", "answer_or_learn", "request_information"),
    ("action", "action_request", "act_or_clarify", "request_action"),
    ("assertion", "assertion_or_correction", "update_common_ground", "assertion_or_correction"),
    ("repair", "repair_or_defer", "clarify_or_defer", "repair_or_defer"),
    ("social", "social_action", "coordinate_socially", "social_action"),
    ("acknowledgement", "acknowledgement", "update_common_ground",
     "acknowledgement"),
    ("refusal", "refusal", "update_common_ground", "refusal"),
]


def test_graph_arbitration_accepts_language_neutral_evidence_provider():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)

    for label, evidence_force, evidence_goal, expected_force in EVENTS:
        interpretation = agent.s.add_node("CommunicationInterpretation", {
            "schema": "communication_interpretation.v1",
            "evidence_schema": "communication_evidence.v1",
            "evidence_provider": "synthetic_semantic_adapter",
            "evidence_force": evidence_force,
            "evidence_goal": evidence_goal,
            "communicative_force": None,
            "cognitive_goal": None,
        })
        agent.inner.add_edge_unchecked(agent.agent, "holds_interpretation", interpretation)
        agent.inner.run_rules()
        attrs = agent.s.node(interpretation)["attrs"]
        assert attrs["communicative_force"] == expected_force, label
        assert attrs["cognitive_goal"] == evidence_goal, label
        if label in {"acknowledgement", "refusal"}:
            assert attrs["cognitive_disposition"] == "defer"


def test_unknown_adapter_force_is_an_explicit_evidence_error():
    with pytest.raises(ValueError, match="supported neutral communicative force"):
        from_semantic_frame(
            {"speech_act": "unclassified"},
            provider="incomplete_adapter",
        )


def test_anaphoric_polar_relation_requires_relation_support_not_topic_grounding():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)

    def interpretation(relation_support):
        message = agent.s.add_node("Message", {
            "text": "Is it open?", "comp_relation_focus": "polar",
            "comp_anaphor": 1.0,
        })
        node = agent.s.add_node("CommunicationInterpretation", {
            "schema": "communication_interpretation.v1",
            "evidence_schema": "communication_evidence.v1",
            "evidence_force": "information_request",
            "relation_focus": "polar",
            "relation_support": relation_support,
            "anaphor": 1,
            "cognitive_disposition": None,
        })
        agent.inner.add_edge_unchecked(
            agent.agent, "holds_interpretation", node)
        agent.inner.add_edge_unchecked(node, "interprets", message)
        goal = agent.s.add_node("Goal", {
            "kind": "answer_topic", "concept": "gate",
        })
        agent.inner.add_edge_unchecked(agent.agent, "has_goal", goal)
        agent.inner.add_edge_unchecked(goal, "comprehends", message)
        agent.inner.run_rules()
        return agent.s.node(node)["attrs"]

    unsupported = interpretation("missing")
    assert unsupported["cognitive_disposition"] == "repair"
    assert unsupported["cognitive_goal"] == "clarify_or_defer"
    assert unsupported["arbitration_basis"] == "missing_polar_relation_support"

    # A graph-projected supported relation is left eligible for its matching
    # answer faculty; topic grounding is not synthesized by this rule.
    supported = interpretation("supported")
    assert supported.get("cognitive_disposition") is None


def test_anaphoric_polar_relation_support_joins_accepted_structured_proposition():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    message = agent.s.add_node("Message", {"text": "Was it reported?"})
    agent.inner.add_edge_unchecked(agent.agent, "received", message)
    interpretation = agent.s.add_node("CommunicationInterpretation", {
        "schema": "communication_interpretation.v1",
        "evidence_schema": "communication_evidence.v1",
        "evidence_force": "information_request",
        "relation_focus": "polar",
        "relation_support": "missing",
        "anaphor": 1,
        "question_polarity": "affirmed",
        "parsed_relation_schema": "communication_relation_projection.v1",
        "parsed_relation_status": "selected_parse_unverified",
        "parsed_predicate_lemma": "report",
        "parsed_subject": "sensor",
        "parsed_object": "it",
        "cognitive_disposition": None,
    })
    agent.inner.set_attr(message, "communication_interpretation_id", interpretation)
    agent.inner.add_edge_unchecked(agent.agent, "holds_interpretation", interpretation)
    agent.inner.add_edge_unchecked(interpretation, "interprets", message)
    goal = agent.s.add_node("Goal", {
        "kind": "answer_topic", "concept": "gate",
    })
    agent.inner.add_edge_unchecked(agent.agent, "has_goal", goal)
    agent.inner.add_edge_unchecked(goal, "comprehends", message)
    held = agent.s.add_node("HeldAnswer", {
        "topic": "gate", "text": "The gate is open.",
        "grounding_referent": "gate", "grounding_status": "supported",
        "grounding_evidence_path": "test topic-only evidence",
    })
    agent.inner.add_edge_unchecked(agent.agent, "holds_answer", held)

    proposition = agent.s.add_node("Proposition", {
        "schema": "structured_proposition.v1",
        "predicate": "report",
        "polarity": "affirmed",
        "commitment_status": "accepted",
    })
    evidence = agent.s.add_node("PropositionEvidence", {
        "schema": "neutral_proposition_evidence.v1",
        "kind": "explicit_neutral",
        "evidence_id": "accepted-sensor-report",
    })
    subject = agent.s.add_node("PropositionArgument", {
        "schema": "proposition_argument.v1", "role": "subject",
        "value": "sensor",
    })
    obj = agent.s.add_node("PropositionArgument", {
        "schema": "proposition_argument.v1", "role": "object",
        "value": "gate",
    })
    agent.inner.add_edge_unchecked(
        proposition, "is_structured_proposition", proposition)
    agent.inner.add_edge_unchecked(proposition, "evidenced_by", evidence)
    agent.inner.add_edge_unchecked(proposition, "has_argument", subject)
    agent.inner.add_edge_unchecked(proposition, "has_argument", obj)

    agent.inner.run_rules()

    attrs = agent.s.node(interpretation)["attrs"]
    assert attrs["relation_support"] == "supported"
    assert attrs["polar_relation_support_minted"] == 1
    assert attrs["cognitive_disposition"] == "answer"
    assert attrs["arbitration_basis"] == "accepted_proposition_polar_answer"
    plans = list(agent.inner.neighbours(
        interpretation, "has_polar_answer_plan"))
    assert len(plans) == 1
    assert agent.s.node(plans[0])["attrs"]["value"] == "yes"
    support_nodes = list(agent.inner.in_neighbours(
        interpretation, "supports_relation"))
    assert len(support_nodes) == 1
    assert agent.s.node(support_nodes[0])["attrs"]["status"] == "supported"
    assert agent._has_polar_relation_support(message, "gate") is True
    assert not any(
        message in agent.inner.neighbours(reply, "responds_to")
        and agent.s.node(reply)["attrs"].get("text") == "The gate is open."
        for reply in agent.outbound_messages())
    surface = agent._release_polar_relation_answer(message)
    assert surface == "Yes."
    polar_replies = [reply for reply in agent.outbound_messages()
                     if message in agent.inner.neighbours(
                         reply, "responds_to")
                     and agent.s.node(reply)["attrs"].get(
                         "native_polar_relation_answer") == 1.0]
    assert len(polar_replies) == 1
    assert any(
        agent.s.node(receipt)["attrs"].get("status") == "released"
        and agent.s.node(receipt)["attrs"].get("surface") == surface
        for receipt in agent.s.nodes("ProductionGateReceipt"))

    negated_message = agent.s.add_node("Message", {
        "text": "Was it not reported?",
        "comp_relation_focus": "polar", "comp_anaphor": 1.0,
    })
    agent.inner.add_edge_unchecked(agent.agent, "received", negated_message)
    negated_interpretation = agent.s.add_node("CommunicationInterpretation", {
        "schema": "communication_interpretation.v1",
        "evidence_schema": "communication_evidence.v1",
        "evidence_force": "information_request",
        "relation_focus": "polar", "relation_support": "missing",
        "anaphor": 1, "question_polarity": "negated",
        "parsed_relation_schema": "communication_relation_projection.v1",
        "parsed_relation_status": "selected_parse_unverified",
        "parsed_predicate_lemma": "report",
        "parsed_subject": "sensor", "parsed_object": "it",
        "cognitive_disposition": None,
    })
    agent.inner.add_edge_unchecked(
        negated_message, "has_interpretation", negated_interpretation)
    agent.inner.add_edge_unchecked(
        negated_interpretation, "interprets", negated_message)
    agent.inner.add_edge_unchecked(
        agent.agent, "holds_interpretation", negated_interpretation)
    negated_goal = agent.s.add_node("Goal", {
        "kind": "answer_topic", "concept": "gate",
    })
    agent.inner.add_edge_unchecked(agent.agent, "has_goal", negated_goal)
    agent.inner.add_edge_unchecked(
        negated_goal, "comprehends", negated_message)
    agent.inner.set_attr(
        negated_message, "communication_interpretation_id",
        negated_interpretation)
    agent.inner.run_rules()
    negated_attrs = agent.s.node(negated_interpretation)["attrs"]
    assert negated_attrs["cognitive_disposition"] == "answer"
    negated_plans = list(agent.inner.neighbours(
        negated_interpretation, "has_polar_answer_plan"))
    assert len(negated_plans) == 1
    assert agent.s.node(negated_plans[0])["attrs"]["value"] == "no"
    assert agent._release_polar_relation_answer(negated_message) == "No."


def test_named_polar_relation_answers_from_accepted_unary_proposition():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    message = agent.s.add_node("Message", {
        "text": "Is the gate open?", "comp_relation_focus": "polar",
        "comp_anaphor": 0.0, "comp_know_concept": "gate",
    })
    interpretation = agent.s.add_node("CommunicationInterpretation", {
        "schema": "communication_interpretation.v1",
        "evidence_schema": "communication_evidence.v1",
        "evidence_force": "information_request",
        "relation_focus": "polar", "relation_support": "missing",
        "anaphor": 0, "question_polarity": "affirmed",
        "parsed_relation_schema": "communication_relation_projection.v1",
        "parsed_relation_status": "selected_parse_unverified",
        "parsed_predicate_lemma": "open", "parsed_subject": "gate",
        "cognitive_disposition": None,
    })
    agent.inner.add_edge_unchecked(agent.agent, "holds_interpretation", interpretation)
    agent.inner.add_edge_unchecked(interpretation, "interprets", message)
    agent.inner.set_attr(message, "communication_interpretation_id", interpretation)
    goal = agent.s.add_node("Goal", {"kind": "answer_topic", "concept": "gate"})
    agent.inner.add_edge_unchecked(agent.agent, "has_goal", goal)
    agent.inner.add_edge_unchecked(goal, "comprehends", message)
    proposition = agent.s.add_node("Proposition", {
        "schema": "structured_proposition.v1", "predicate": "open",
        "polarity": "affirmed", "commitment_status": "accepted",
        "argument_roles": '["subject"]',
    })
    evidence = agent.s.add_node("PropositionEvidence", {
        "schema": "neutral_proposition_evidence.v1",
        "kind": "explicit_neutral", "evidence_id": "named-gate-open",
    })
    subject = agent.s.add_node("PropositionArgument", {
        "schema": "proposition_argument.v1", "role": "subject",
        "value": "gate",
    })
    agent.inner.add_edge_unchecked(proposition, "is_structured_proposition", proposition)
    agent.inner.add_edge_unchecked(proposition, "evidenced_by", evidence)
    agent.inner.add_edge_unchecked(proposition, "has_argument", subject)

    agent.inner.run_rules()

    attrs = agent.s.node(interpretation)["attrs"]
    assert attrs["relation_support"] == "supported"
    assert attrs["cognitive_disposition"] == "answer"
    assert attrs["arbitration_basis"] == "accepted_proposition_polar_answer"
    assert agent._has_polar_relation_support(message, "gate") is True
    assert agent._release_polar_relation_answer(message) == "Yes."

    # A superficially matching binary predicate is not a unary property fact.
    agent.inner.set_attr(proposition, "commitment_status", "suspended")
    binary_message = agent.s.add_node("Message", {
        "text": "Is the gate open?", "comp_relation_focus": "polar",
        "comp_anaphor": 0.0, "comp_know_concept": "gate",
    })
    binary_interpretation = agent.s.add_node(
        "CommunicationInterpretation", {
            "schema": "communication_interpretation.v1",
            "evidence_schema": "communication_evidence.v1",
            "evidence_force": "information_request",
            "relation_focus": "polar", "relation_support": "missing",
            "anaphor": 0, "question_polarity": "affirmed",
            "parsed_relation_schema": "communication_relation_projection.v1",
            "parsed_relation_status": "selected_parse_unverified",
            "parsed_predicate_lemma": "open", "parsed_subject": "gate",
            "cognitive_disposition": None,
        })
    agent.inner.add_edge_unchecked(
        agent.agent, "holds_interpretation", binary_interpretation)
    agent.inner.add_edge_unchecked(
        binary_interpretation, "interprets", binary_message)
    agent.inner.set_attr(
        binary_message, "communication_interpretation_id",
        binary_interpretation)
    binary_proposition = agent.s.add_node("Proposition", {
        "schema": "structured_proposition.v1", "predicate": "open",
        "polarity": "affirmed", "commitment_status": "accepted",
        "argument_roles": '["object","subject"]',
    })
    binary_evidence = agent.s.add_node("PropositionEvidence", {
        "schema": "neutral_proposition_evidence.v1",
        "kind": "explicit_neutral", "evidence_id": "binary-gate-open-door",
    })
    binary_subject = agent.s.add_node("PropositionArgument", {
        "schema": "proposition_argument.v1", "role": "subject",
        "value": "gate",
    })
    binary_object = agent.s.add_node("PropositionArgument", {
        "schema": "proposition_argument.v1", "role": "object",
        "value": "door",
    })
    agent.inner.add_edge_unchecked(
        binary_proposition, "is_structured_proposition", binary_proposition)
    agent.inner.add_edge_unchecked(
        binary_proposition, "evidenced_by", binary_evidence)
    agent.inner.add_edge_unchecked(
        binary_proposition, "has_argument", binary_subject)
    agent.inner.add_edge_unchecked(
        binary_proposition, "has_argument", binary_object)
    agent.inner.run_rules()
    binary_attrs = agent.s.node(binary_interpretation)["attrs"]
    assert binary_attrs.get("polar_relation_support_minted") != 1
    assert binary_attrs.get("cognitive_disposition") != "answer"
    assert agent._has_polar_relation_support(binary_message, "gate") is False


def test_live_named_polar_question_releases_accepted_unary_answer():
    from domains.proposition_commitment import bridge_proposition_evidence

    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    result = bridge_proposition_evidence(agent, {
        "schema": "neutral_proposition_evidence.v1",
        "kind": "explicit_neutral", "predicate": "open",
        "arguments": {"subject": "gate"}, "polarity": "affirmed",
        "provider": "named_polar_regression",
        "evidence_id": "named-polar-gate-open",
        "commitment_status": "accepted",
    })
    assert result["supported"] is True

    reply = agent.converse(
        "Is the gate open?", speech_act="question",
        context={"interaction_mode": "turn_compatible",
                 "interaction_relation": "response"})

    inbound = agent._last_turn_inbound
    inbound_attrs = agent.s.node(inbound)["attrs"]
    interpretation = inbound_attrs["communication_interpretation_id"]
    attrs = agent.s.node(interpretation)["attrs"]
    assert reply == "Yes.", (inbound_attrs, attrs,
                               list(agent.inner.neighbours(
                                   interpretation, "has_polar_answer_plan")))
    assert attrs["cognitive_disposition"] == "answer"
    assert attrs["arbitration_basis"] == "accepted_proposition_polar_answer"
    assert inbound_attrs["communication_route"] == "polar_relation_answer_graph"
    assert agent.reply_turn_trace(agent.last_turn_inbound_id())[
        "answer_commitment"]["kind"] \
        == "supported_event_bound_polar_answer"

    negative_reply = agent.converse(
        "Is the gate not open?", speech_act="question",
        context={"interaction_mode": "turn_compatible",
                 "interaction_relation": "response"})
    negative_inbound = agent._last_turn_inbound
    negative_attrs = agent.s.node(negative_inbound)["attrs"]
    negative_interpretation = agent.s.node(
        negative_attrs["communication_interpretation_id"])["attrs"]
    assert negative_reply == "No."
    assert negative_interpretation["parsed_predicate_lemma"] == "open"
    assert negative_interpretation["question_polarity"] == "negated"
    assert agent.reply_turn_trace(agent.last_turn_inbound_id())[
        "answer_commitment"]["kind"] \
        == "supported_event_bound_polar_answer"


def test_semantic_frame_transports_only_supported_communicative_act_kinds():
    evidence = from_semantic_frame(
        {"communicative_force": "refusal",
         "communicative_act": "inability_action"},
        provider="synthetic_semantic_adapter",
    )
    assert evidence["evidence_communicative_act"] == "inability_action"
    offer = from_semantic_frame(
        {"communicative_force": "social_action",
         "communicative_act": "ability_action_offer",
         "offer_target_status": "unresolved"},
        provider="synthetic_semantic_adapter",
    )
    assert offer["evidence_offer_target_status"] == "unresolved"
    repair = from_semantic_frame(
        {"communicative_force": "repair_or_defer",
         "communicative_act": "nonunderstanding_report"},
        provider="synthetic_semantic_adapter",
    )
    assert repair["evidence_communicative_act"] == "nonunderstanding_report"
    with pytest.raises(ValueError, match="unsupported offer target status"):
        from_semantic_frame(
            {"communicative_force": "social_action",
             "communicative_act": "ability_action_offer",
             "offer_target_status": "grounded"},
            provider="incomplete_adapter",
        )
    with pytest.raises(ValueError, match="unsupported communicative act"):
        from_semantic_frame(
            {"communicative_force": "refusal",
             "communicative_act": "surface_pattern"},
            provider="incomplete_adapter",
        )


def test_standalone_nonturn_assertion_defers_without_surface_language():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)

    interpretation = agent.s.add_node("CommunicationInterpretation", {
        "schema": "communication_interpretation.v1",
        "evidence_schema": "communication_evidence.v1",
        "evidence_provider": "synthetic_semantic_adapter",
        "evidence_force": "assertion_or_correction",
        "evidence_goal": "update_common_ground",
        "language_statement_act": "assertion",
        "interaction_mode": "non_turn",
        "interaction_relation": "standalone",
        "communicative_force": None,
        "cognitive_goal": "update_common_ground",
        "cognitive_disposition": None,
    })
    agent.inner.add_edge_unchecked(
        agent.agent, "holds_interpretation", interpretation)
    agent.inner.run_rules()

    attrs = agent.s.node(interpretation)["attrs"]
    assert attrs["communicative_force"] == "assertion_or_correction"
    assert attrs["cognitive_disposition"] == "defer"
    assert attrs["cognitive_goal"] == "defer"
    assert attrs["arbitration_basis"] == "standalone_nonturn_common_ground"


def test_continuation_assertion_defers_without_proposition_uptake():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    interpretation = agent.s.add_node("CommunicationInterpretation", {
        "schema": "communication_interpretation.v1",
        "evidence_schema": "communication_evidence.v1",
        "evidence_provider": "synthetic_semantic_adapter",
        "evidence_force": "assertion_or_correction",
        "language_statement_act": "assertion",
        "interaction_mode": "turn_compatible",
        "interaction_relation": "continuation",
        "cognitive_disposition": None,
    })
    agent.inner.add_edge_unchecked(
        agent.agent, "holds_interpretation", interpretation)
    agent.inner.run_rules()

    attrs = agent.s.node(interpretation)["attrs"]
    assert attrs["cognitive_disposition"] == "defer"
    assert attrs["arbitration_basis"] == \
        "continuation_statement_common_ground"


def test_unavailable_typed_action_blocks_only_in_response_slot():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)

    def interpret(relation):
        interpretation = agent.s.add_node("CommunicationInterpretation", {
            "schema": "communication_interpretation.v1",
            "evidence_schema": "communication_evidence.v1",
            "evidence_provider": "synthetic_semantic_adapter",
            "language_action_availability": "unavailable",
            "interaction_mode": "turn_compatible",
            "interaction_relation": relation,
            "cognitive_disposition": None,
        })
        agent.inner.add_edge_unchecked(
            agent.agent, "holds_interpretation", interpretation)
        agent.inner.run_rules()
        return agent.s.node(interpretation)["attrs"]

    response = interpret("response")
    assert response["cognitive_disposition"] == "blocked"
    assert response["arbitration_basis"] == "unavailable_action_response"

    standalone = interpret("standalone")
    assert standalone["cognitive_disposition"] is None


def test_unavailable_action_response_gets_neutral_receipt_without_authority():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)

    reply = agent.converse(
        "That action is not available.", speech_act="statement",
        context={"interaction_mode": "turn_compatible",
                 "interaction_relation": "response"},
    )

    inbound = agent._last_turn_inbound
    interpretation_id = agent.s.node(inbound)["attrs"][
        "communication_interpretation_id"]
    interpretation = agent.s.node(interpretation_id)["attrs"]
    assert interpretation["cognitive_disposition"] == "blocked"
    assert interpretation["arbitration_basis"] == \
        "unavailable_action_response"
    assert reply == "I heard you."
    linked = [node for node in agent.agent_outbound_messages()
              if inbound in agent.responds_to(node)
              and agent.s.node(node)["attrs"].get(
                  "native_unavailable_action_reply") == 1]
    assert len(linked) == 1
    reply_attrs = agent.s.node(linked[0])["attrs"]
    assert reply_attrs["native_unavailable_action_reply"] == 1
    assert reply_attrs["native_standalone_assertion_reply_plan"] == \
        "neutral_receipt"
    receipts = [agent.s.node(node)["attrs"]
                for node in agent.s.nodes("ProductionGateReceipt")
                if agent.s.node(node)["attrs"].get("turn_message_id")
                == int(inbound.value)]
    assert len(receipts) == 1
    assert receipts[0]["status"] == "released"
    assert receipts[0]["parse_back_mode"] == \
        "conversation_unavailable_action_ack_graph"
    assert receipts[0]["semantic_intent"] == \
        "acknowledge_receipt_without_endorsement"
    assert not any(inbound in agent.inner.neighbours(goal, "comprehends")
                   for goal in agent.inner.neighbours(agent.agent, "has_goal"))


def test_unresolved_nonturn_response_action_request_defers():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)

    def interpret(mode):
        interpretation = agent.s.add_node("CommunicationInterpretation", {
            "schema": "communication_interpretation.v1",
            "evidence_schema": "communication_evidence.v1",
            "evidence_provider": "synthetic_semantic_adapter",
            "evidence_force": "action_request",
            "dispatch_path": "instruction",
            "interaction_mode": mode,
            "interaction_relation": "response",
            "grounding_status": "unresolved",
            "cognitive_disposition": None,
        })
        agent.inner.add_edge_unchecked(
            agent.agent, "holds_interpretation", interpretation)
        agent.inner.run_rules()
        return agent.s.node(interpretation)["attrs"]

    nonturn = interpret("non_turn")
    assert nonturn["cognitive_disposition"] == "defer"
    assert nonturn["arbitration_basis"] == \
        "unresolved_nonturn_response_action"

    turn = interpret("turn_compatible")
    assert turn["cognitive_disposition"] is None


def test_uncertain_selected_response_creates_source_constrained_learning_request():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    topic = agent.s.add_node("Concept", {"name": "reading"})
    mention = agent.s.add_node("MessageMention", {"text": "reading"})
    message = agent.s.add_node("Message", {"comp_object": "reading"})
    interpretation = agent.s.add_node("CommunicationInterpretation", {
        "schema": "communication_interpretation.v1",
        "evidence_schema": "communication_evidence.v1",
        "evidence_provider": "synthetic_semantic_adapter",
        "evidence_force": "information_request",
        "explicit_uncertainty": 1,
        "parsed_object": "reading",
        "interaction_mode": "turn_compatible",
        "interaction_relation": "response",
        "grounding_status": "unresolved",
        "cognitive_disposition": None,
    })
    for src, edge, dst in (
            (agent.agent, "holds_interpretation", interpretation),
            (interpretation, "interprets", message),
            (message, "has_mention", mention),
            (mention, "refers_to", topic)):
        agent.inner.add_edge_unchecked(src, edge, dst)
    agent.inner.run_rules()

    attrs = agent.s.node(interpretation)["attrs"]
    assert attrs["cognitive_disposition"] == "learn"
    assert attrs["arbitration_basis"] == \
        "uncertain_selected_information_gap"
    requests = agent.s.nodes("InformationLearningRequest")
    assert len(requests) == 1
    assert agent.inner.has_edge(requests[0], "about_topic", topic)
    request_attrs = agent.s.node(requests[0])["attrs"]
    assert request_attrs["answer_authority"] == "none"
    assert request_attrs["grounding_requirement"] == \
        "supported_source_evidence"


def test_generic_assertion_force_without_typed_statement_act_fails_closed():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    interpretation = agent.s.add_node("CommunicationInterpretation", {
        "schema": "communication_interpretation.v1",
        "evidence_schema": "communication_evidence.v1",
        "evidence_provider": "synthetic_semantic_adapter",
        "evidence_force": "assertion_or_correction",
        "evidence_goal": "update_common_ground",
        "interaction_mode": "non_turn",
        "interaction_relation": "standalone",
        "communicative_force": None,
        "cognitive_goal": "update_common_ground",
        "cognitive_disposition": None,
    })
    agent.inner.add_edge_unchecked(
        agent.agent, "holds_interpretation", interpretation)
    agent.inner.run_rules()
    assert agent.s.node(interpretation)["attrs"]["cognitive_disposition"] is None


def test_missing_world_blocks_without_erasing_neutral_information_goal():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    interpretation = agent.s.add_node("CommunicationInterpretation", {
        "schema": "communication_interpretation.v1",
        "evidence_schema": "communication_evidence.v1",
        "evidence_provider": "non_english_semantic_adapter",
        "evidence_force": "information_request",
        "evidence_goal": "answer_or_learn",
        "language_world_support": "missing",
        "explicit_failure": 0,
        "communicative_force": None,
        "cognitive_goal": None,
        "cognitive_disposition": None,
    })
    agent.inner.add_edge_unchecked(agent.agent, "holds_interpretation",
                                   interpretation)
    agent.inner.run_rules()

    attrs = agent.s.node(interpretation)["attrs"]
    assert attrs["communicative_force"] == "request_information"
    assert attrs["cognitive_goal"] == "answer_or_learn"
    assert attrs["cognitive_disposition"] == "blocked"
    assert attrs["arbitration_basis"] == \
        "missing_world_information_request"


def test_reflective_answer_requires_linked_native_faculty_evidence():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    inbound = agent.s.add_node("Message", {"text": "opaque signal"})
    interpretation = agent.s.add_node("CommunicationInterpretation", {
        "schema": "communication_interpretation.v1",
        "evidence_schema": "communication_evidence.v1",
        "evidence_provider": "non_english_semantic_adapter",
        "evidence_force": "information_request",
        "selected_reflective_faculty": "self_organisation",
        "interaction_mode": "turn_compatible",
        "cognitive_disposition": None,
    })
    evidence = agent.s.add_node("ReflectiveAnswerEvidence", {
        "schema": "reflective_answer_evidence.v1",
        "faculty": "self_organisation",
        "status": "supported",
    })
    microtheory = agent.s.add_node("Microtheory", {"name": "held_area"})
    agent.inner.add_edge_unchecked(agent.agent, "holds_interpretation",
                                   interpretation)
    agent.inner.add_edge_unchecked(interpretation, "interprets", inbound)
    agent.inner.add_edge_unchecked(
        interpretation, "has_reflective_answer_evidence", evidence)
    agent.inner.add_edge_unchecked(evidence, "supported_by", microtheory)

    agent.inner.run_rules()

    attrs = agent.s.node(interpretation)["attrs"]
    assert attrs["cognitive_disposition"] == "answer"
    assert attrs["arbitration_basis"] == "supported_reflective_faculty_answer"
    replies = [reply for reply in agent.agent_outbound_messages()
               if inbound in agent.responds_to(reply)]
    assert len(replies) == 1
    assert agent.s.node(replies[0])["attrs"][
        "native_reflective_answer_plan"] == "self_organisation"


def test_reflective_answer_without_graph_support_fails_closed():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    inbound = agent.s.add_node("Message", {"text": "opaque signal"})
    interpretation = agent.s.add_node("CommunicationInterpretation", {
        "schema": "communication_interpretation.v1",
        "evidence_schema": "communication_evidence.v1",
        "evidence_force": "information_request",
        "selected_reflective_faculty": "self_organisation",
        "interaction_mode": "turn_compatible",
        "cognitive_disposition": None,
    })
    agent.inner.add_edge_unchecked(agent.agent, "holds_interpretation",
                                   interpretation)
    agent.inner.add_edge_unchecked(interpretation, "interprets", inbound)

    agent.inner.run_rules()

    assert agent.s.node(interpretation)["attrs"]["cognitive_disposition"] is None
    assert not [reply for reply in agent.agent_outbound_messages()
                if inbound in agent.responds_to(reply)]


def test_self_organisation_turn_releases_native_graph_reply():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)

    reply = agent.converse(
        "How are you organised?", speech_act="question",
        context={"interaction_mode": "turn_compatible",
                 "interaction_relation": "turn_compatible"})

    inbound = agent._last_turn_inbound
    interpretation = agent.s.node(inbound)["attrs"][
        "communication_interpretation_id"]
    attrs = agent.s.node(interpretation)["attrs"]
    assert "organised into" in reply
    assert attrs["cognitive_disposition"] == "answer"
    assert attrs["arbitration_basis"] == "supported_reflective_faculty_answer"
    assert agent.graph_turn_reply(inbound) == reply
    assert agent._native_reflective_answer_selected(inbound)
    receipts = [node for node in agent.s.nodes("ProductionGateReceipt")
                if agent.s.node(node)["attrs"].get("turn_message_id")
                == int(inbound.value)]
    assert len(receipts) == 1
    receipt = agent.s.node(receipts[0])["attrs"]
    assert receipt["status"] == "released"
    assert receipt["parse_back_mode"] == \
        "conversation_reflective_self_organisation_graph"


def test_language_adapter_emits_neutral_assertion_for_parsed_predications():
    from domains.comprehend_text import comprehend_text

    agent = WorldAdapter(seeds=())
    agent.s.add_node("Concept", {
        "name": "can", "definition": "modal indicating ability or permission",
    })
    agent.s.add_node("Concept", {
        "name": "cannot", "description": "deficiency cue: inability to do something",
    })
    agent.s.add_node("Concept", {
        "name": "not", "definition": "(adverb) negation",
    })
    agent.s.add_node("Concept", {"name": "gate"})
    assertions = [
        comprehend_text(agent, text, kind="statement")
        for text in ("The sky is blue.", "The rain stopped.",
                     "The relay may be warm.", "I am leaving now.")
    ]
    offer = comprehend_text(agent, "I can check the gate.", kind="statement")
    refusal = comprehend_text(agent, "I cannot open it.", kind="statement")
    corrective_contrast = comprehend_text(
        agent, "The map was outdated, not the route.", kind="statement")
    simple_negation = comprehend_text(
        agent, "The map was not outdated.", kind="statement")
    non_assertions = [
        offer,
        refusal,
            comprehend_text(agent, "This request cannot be processed.",
                            kind="statement"),
            comprehend_text(agent, "That action is not available.",
                            kind="statement"),
        ]
    learning_report = comprehend_text(
        agent, "I learned that the gate needs power.", kind="statement")

    assert all(parsed.dispatch["language_evidence"]["statement_act"]
               == "assertion" for parsed in assertions)
    assert all("statement_act" not in
               parsed.dispatch.get("language_evidence", {})
               for parsed in non_assertions)
    # The matrix is an asserted report that the speaker learned something;
    # its embedded proposition is distinct and remains unverified. Pragmatic
    # farewell handling is a separate native discourse act, not POS evidence.
    assert learning_report.dispatch["language_evidence"]["statement_act"] == \
        "assertion"
    assert learning_report.relation["predicate"]["surface"] == "learned"
    embedded = learning_report.relation["embedded_relations"]
    assert len(embedded) == 1
    assert embedded[0]["predicate"]["surface"] == "needs"
    correction_evidence = corrective_contrast.dispatch["language_evidence"]
    assert correction_evidence["discourse_relation"] == "correction"
    assert correction_evidence["statement_act"] == "assertion"
    simple_negative_evidence = simple_negation.dispatch.get(
        "language_evidence", {})
    assert simple_negative_evidence.get("discourse_relation") != "correction"
    assert "statement_act" not in simple_negative_evidence
    assert offer.dispatch["language_evidence"]["communicative_force"] == \
        "social_action"
    assert offer.dispatch["language_evidence"]["communicative_act"] == \
        "ability_action_offer"
    assert offer.dispatch["language_evidence"]["communicative_act_evidence"] == \
        "first_person_ability_action_offer"
    assert offer.dispatch["language_evidence"]["offer_target_status"] == \
        "concept_available"
    unresolved_offer = comprehend_text(
        agent, "I can examine the blorf.", kind="statement")
    unresolved_evidence = unresolved_offer.dispatch["language_evidence"]
    assert unresolved_evidence["communicative_force"] == "social_action"
    assert unresolved_evidence["communicative_act"] == "ability_action_offer"
    assert unresolved_evidence["offer_target_status"] == "unresolved"
    assert refusal.dispatch["language_evidence"]["communicative_force"] == \
        "refusal"
    assert refusal.dispatch["language_evidence"]["communicative_act"] == \
        "inability_action"
    assert refusal.dispatch["language_evidence"]["communicative_act_evidence"] == \
        "first_person_modal_inability_action"


def test_standalone_nonturn_defer_releases_native_neutral_acknowledgement():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    reply = agent.converse(
        "The sky is blue.", speech_act="statement",
        context={"interaction_mode": "non_turn",
                 "interaction_relation": "standalone"},
    )

    inbound = agent._last_turn_inbound
    interpretation = agent.s.node(agent.s.node(inbound)["attrs"][
        "communication_interpretation_id"])["attrs"]
    assert interpretation["cognitive_disposition"] == "defer"
    assert interpretation["arbitration_basis"] == \
        "standalone_nonturn_common_ground"
    assert agent.graph_turn_reply_expectation(inbound) == {
        "status": "expected",
        "expected_response_acts": ["acknowledgment"],
    }
    assert reply == "I heard you."
    native_replies = [
        node for node in agent.agent_outbound_messages()
        if inbound in agent.responds_to(node)
        and agent.s.node(node)["attrs"].get(
            "native_standalone_assertion_reply_plan") == "neutral_receipt"
    ]
    assert len(native_replies) == 1
    assert agent.s.node(native_replies[0])["attrs"].get("text") == reply
    receipts = [
        agent.s.node(node)["attrs"]
        for node in agent.s.nodes("ProductionGateReceipt")
        if agent.s.node(node)["attrs"].get("parse_back_mode")
        == "conversation_standalone_assertion_graph"
    ]
    assert len(receipts) == 1
    assert receipts[0]["status"] == "released"
    assert receipts[0]["semantic_intent"] == \
        "acknowledge_receipt_without_endorsement"


def test_typed_response_acknowledgement_releases_neutral_receipt():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    reply = agent.converse(
        "Yes, that is the one.", speech_act="acknowledgment",
        context={"interaction_mode": "turn_compatible",
                 "interaction_relation": "response"},
    )

    inbound = agent._last_turn_inbound
    interpretation = agent.s.node(agent.s.node(inbound)["attrs"][
        "communication_interpretation_id"])["attrs"]
    assert interpretation["evidence_force"] == "acknowledgement"
    assert interpretation["cognitive_disposition"] == "defer"
    assert interpretation["cognitive_goal"] == "update_common_ground"
    assert interpretation["arbitration_basis"] == "typed_acknowledgement"
    assert reply == "I heard you."
    assert agent.graph_turn_reply_expectation(inbound) == {
        "status": "expected",
        "expected_response_acts": ["acknowledgment"],
    }

    native_replies = [
        node for node in agent.agent_outbound_messages()
        if inbound in agent.responds_to(node)
        and agent.s.node(node)["attrs"].get(
            "native_typed_acknowledgement_reply_plan") == "neutral_receipt"
    ]
    assert len(native_replies) == 1
    assert agent.s.node(native_replies[0])["attrs"].get("text") == reply
    receipts = [
        agent.s.node(node)["attrs"]
        for node in agent.s.nodes("ProductionGateReceipt")
        if agent.s.node(node)["attrs"].get("turn_message_id")
        == int(inbound.value)
    ]
    assert len(receipts) == 1
    assert receipts[0]["status"] == "released"
    assert receipts[0]["parse_back_mode"] == \
        "conversation_response_acknowledgement_graph"
    assert receipts[0]["semantic_intent"] == \
        "acknowledge_receipt_without_endorsement"

    # The receipt remains distinct from the native social-answer route and
    # does not turn acknowledgement into proposition acceptance.
    assert not agent._native_social_answer_selected(inbound)


def test_typed_refusal_does_not_use_acknowledgement_receipt_plan():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    agent.converse(
        "No, I will not open it.", speech_act="refusal",
        context={"interaction_mode": "turn_compatible",
                 "interaction_relation": "response"},
    )

    inbound = agent._last_turn_inbound
    interpretation = agent.s.node(agent.s.node(inbound)["attrs"][
        "communication_interpretation_id"])["attrs"]
    assert interpretation["evidence_force"] == "refusal"
    assert interpretation["cognitive_disposition"] == "defer"
    assert interpretation["arbitration_basis"] == "typed_refusal"
    assert not any(
        agent.s.node(reply)["attrs"].get(
            "native_typed_acknowledgement_reply_plan")
        for reply in agent.agent_outbound_messages()
        if inbound in agent.responds_to(reply)
    )


@pytest.mark.parametrize(("relation", "disposition", "basis"), [
    ("response", "error", "typed_inability_response"),
    ("standalone", "blocked", "typed_inability_standalone"),
])
def test_typed_inability_disposition_uses_neutral_act_and_relation(
        relation, disposition, basis):
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    event = agent.ingest_semantic_event(
        {"communicative_force": "refusal",
         "communicative_act": "inability_action",
         "interaction_relation": relation},
        provider="synthetic_semantic_adapter",
        interaction_mode="event" if relation == "standalone" else "turn_compatible",
    )
    interpretation = event["interpretation_id"]
    attrs = agent.s.node(interpretation)["attrs"]
    assert attrs["cognitive_disposition"] == disposition
    assert attrs["communicative_force"] == "refusal"
    assert attrs["cognitive_goal"] == "update_common_ground"
    assert attrs["arbitration_basis"] == basis


def test_untyped_refusal_response_keeps_defer_policy():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    interpretation = agent.s.add_node("CommunicationInterpretation", {
        "schema": "communication_interpretation.v1",
        "evidence_schema": "communication_evidence.v1",
        "evidence_provider": "synthetic_semantic_adapter",
        "evidence_force": "refusal",
        "evidence_goal": "update_common_ground",
        "interaction_relation": "response",
        "communicative_force": None,
        "cognitive_goal": None,
        "cognitive_disposition": None,
    })
    agent.inner.add_edge_unchecked(
        agent.agent, "holds_interpretation", interpretation)
    agent.inner.run_rules()
    attrs = agent.s.node(interpretation)["attrs"]
    assert attrs["cognitive_disposition"] == "defer"
    assert attrs["arbitration_basis"] == "typed_refusal"


def test_blocked_standalone_inability_closes_without_turn_reply():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    reply = agent.converse(
        "I cannot reach the upper switch.", speech_act="statement",
        context={"interaction_mode": "non_turn",
                 "interaction_relation": "standalone"},
    )
    inbound = agent._last_turn_inbound
    interpretation_id = agent.s.node(inbound)["attrs"][
        "communication_interpretation_id"]
    attrs = agent.s.node(interpretation_id)["attrs"]
    assert attrs["cognitive_disposition"] == "blocked"
    assert reply == ""
    trace = agent.reply_turn_trace(agent.last_turn_inbound_id())
    assert trace["reply"] == ""
    assert trace["reply_from"] == "adapter"
    assert not any(
        inbound in agent.responds_to(node)
        and agent.s.node(node)["attrs"].get("text")
        for node in agent.outbound_messages()
    )
    assert not any(
        agent.s.node(node)["attrs"].get("turn_message_id") == int(inbound.value)
        for node in agent.s.nodes("ProductionGateReceipt")
    )


def test_response_inability_uses_native_error_disposition_and_error_surface():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    reply = agent.converse(
        "I cannot reach the upper switch.", speech_act="statement",
        context={"interaction_mode": "turn_compatible",
                 "interaction_relation": "response"},
    )

    inbound = agent._last_turn_inbound
    interpretation_id = agent.s.node(inbound)["attrs"][
        "communication_interpretation_id"]
    attrs = agent.s.node(interpretation_id)["attrs"]
    assert attrs["evidence_force"] == "refusal"
    assert attrs["evidence_communicative_act"] == "inability_action"
    assert attrs["cognitive_disposition"] == "error"
    assert attrs["arbitration_basis"] == "typed_inability_response"
    assert reply == "ERROR: no communicative response could be generated."
    assert agent.reply_turn_trace(agent.last_turn_inbound_id())["reply"] == reply


@pytest.mark.parametrize("text", [
    "The south gate is open.",
    "The monitor reports a fault.",
])
def test_response_assertion_defers_and_releases_neutral_receipt(text):
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    reply = agent.converse(
        text,
        speech_act="statement",
        context={"interaction_mode": "turn_compatible",
                 "interaction_relation": "response"},
    )
    inbound = agent._last_turn_inbound
    interpretation = agent.s.node(agent.s.node(inbound)["attrs"][
        "communication_interpretation_id"])["attrs"]
    assert interpretation["cognitive_disposition"] == "defer"
    assert interpretation["cognitive_goal"] == "update_common_ground"
    assert interpretation["arbitration_basis"] == \
        "response_statement_common_ground"
    assert reply and not reply.startswith("ERROR:")
    receipts = [
        agent.s.node(node)["attrs"]
        for node in agent.s.nodes("ProductionGateReceipt")
        if agent.s.node(node)["attrs"].get("parse_back_mode")
        == "conversation_response_assertion_graph"
    ]
    assert receipts and receipts[-1]["status"] == "released"
    assert receipts[-1]["semantic_intent"] == \
        "acknowledge_receipt_without_endorsement"


def test_turn_compatible_assertion_is_not_caught_by_nonturn_deferral():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)

    interpretation = agent.s.add_node("CommunicationInterpretation", {
        "schema": "communication_interpretation.v1",
        "evidence_schema": "communication_evidence.v1",
        "evidence_provider": "synthetic_semantic_adapter",
        "evidence_force": "assertion_or_correction",
        "evidence_goal": "update_common_ground",
        "interaction_mode": "turn_compatible",
        "interaction_relation": "response",
        "communicative_force": None,
        "cognitive_goal": "update_common_ground",
        "cognitive_disposition": None,
    })
    agent.inner.add_edge_unchecked(
        agent.agent, "holds_interpretation", interpretation)
    agent.inner.run_rules()

    attrs = agent.s.node(interpretation)["attrs"]
    assert attrs["cognitive_disposition"] is None
    assert attrs.get("arbitration_basis") != \
        "standalone_nonturn_common_ground"


def test_epistemic_modal_perfect_evidence_repairs_continuation_without_gold_flag():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    text = "No, I may have misread it."
    reply = agent.converse(
        text,
        speech_act=WorldAdapter.classify_speech_act(text),
        context={"interaction_mode": "non_turn",
                 "interaction_relation": "continuation"},
    )
    inbound = agent._last_turn_inbound
    interpretation = agent.s.node(
        agent.s.node(inbound)["attrs"]["communication_interpretation_id"]
    )["attrs"]
    assert interpretation["language_modality_evidence"] == "epistemic_possibility"
    assert interpretation["explicit_uncertainty"] == 0
    assert interpretation["cognitive_disposition"] == "repair"
    assert interpretation["arbitration_basis"] == \
        "uncertain_continuing_common_ground_event"
    assert reply and not reply.startswith("ERROR:")
    assert "it" in reply.lower()

    from domains.comprehend_text import comprehend_text
    question = comprehend_text(agent, "May I leave now?")
    assert question.dispatch.get("language_evidence", {}).get(
        "modality_evidence") != "epistemic_possibility"


def test_unbacked_confirmation_is_repaired_not_sent_to_topic_search():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    from domains.comprehend_text import comprehend_text

    parsed = comprehend_text(agent, "Can you confirm the route?")
    evidence = parsed.dispatch.get("language_evidence", {})
    assert evidence.get("confirmation_request") == "proposition_confirmation"
    assert evidence.get("repair_focus") == "route"
    assert "authority_request" not in evidence

    reply = agent.converse(
        "Can you confirm the route?",
        speech_act=WorldAdapter.classify_speech_act(
            "Can you confirm the route?"),
        context={"interaction_mode": "non_turn",
                 "interaction_relation": "standalone"},
    )
    inbound = agent._last_turn_inbound
    interpretation_id = agent.s.node(inbound)["attrs"][
        "communication_interpretation_id"]
    interpretation = agent.s.node(interpretation_id)["attrs"]
    assert interpretation["cognitive_disposition"] == "repair"
    assert interpretation["language_confirmation_request"] == \
        "proposition_confirmation"
    assert interpretation["communicative_force"] == "request_information"
    assert interpretation["arbitration_basis"] == \
        "confirmation_lacks_conversational_support"
    assert interpretation["authority_status"] != "missing"
    assert not any(agent.s.node(node)["attrs"].get("source") == "answer_topic"
                   for node in agent.s.nodes("SearchRequest"))
    assert reply and not reply.startswith("ERROR:")


@pytest.mark.parametrize(
    "text, relation, expected_disposition",
    [
        ("No, the gate is closed.", "response", "defer"),
        ("Actually, use the east path.", "response", "defer"),
        ("The map was outdated, not the route.", "response", "defer"),
        ("Operator, please listen.", "standalone", "answer"),
        ("When ready, close the hatch.", "continuation", "defer"),
    ],
)
def test_native_non_action_disposition_cannot_mint_instruction_goal(
        text, relation, expected_disposition):
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    reply = agent.converse(
        text,
        speech_act=WorldAdapter.classify_speech_act(text),
        context={"interaction_mode": "non_turn" if relation != "response"
                 else "turn_compatible",
                 "interaction_relation": relation},
    )
    inbound = agent._last_turn_inbound
    interpretation_id = agent.s.node(inbound)["attrs"][
        "communication_interpretation_id"]
    interpretation = agent.s.node(interpretation_id)["attrs"]
    assert interpretation["cognitive_disposition"] == expected_disposition
    instruction_goals = [
        agent.s.node(goal)["attrs"] for goal in agent.s.nodes("Goal")
        if agent.s.node(goal)["attrs"].get("kind") == "instruction"
        and inbound in agent.inner.neighbours(goal, "comprehends")
    ]
    if relation == "continuation":
        assert instruction_goals
        assert all(goal.get("status") == "deferred"
                   for goal in instruction_goals)
    else:
        assert not instruction_goals
    if relation != "continuation":
        assert "took on the goal" not in (reply or "").lower()
        assert "instruction to" not in (reply or "").lower()
        assert "filed it as a gap" not in (reply or "").lower()
        assert not any(
            inbound in agent.inner.neighbours(concern, "about_message")
            for concern in agent.s.nodes("SelfConcern")
        )
    if expected_disposition == "answer":
        assert reply and reply.strip().lower().rstrip(".!?") in {
            "i heard you", "understood",
        }
        social_replies = [
            node for node in agent.agent_outbound_messages()
            if inbound in agent.responds_to(node)
            and any(agent.s.node(act)["attrs"].get("name") == "acknowledgment"
                    for act in agent.inner.neighbours(node, "has_speech_act"))
        ]
        assert len(social_replies) == 1
        assert agent.s.node(social_replies[0])["attrs"].get("text") == reply
        social_receipts = [
            agent.s.node(receipt)["attrs"]
            for receipt in agent.s.nodes("ProductionGateReceipt")
            if agent.s.node(receipt)["attrs"].get("parse_back_mode")
            == "conversation_social_graph"
        ]
        assert social_receipts
        assert social_receipts[-1]["status"] == "released"
    elif text.startswith(("Actually,", "No,")):
        assert interpretation["cognitive_goal"] == "update_common_ground"
        assert interpretation["arbitration_basis"] == \
            "corrective_discourse_response"
        assert reply == "I understand the correction."
        correction_replies = [
            node for node in agent.agent_outbound_messages()
            if inbound in agent.responds_to(node)
            and agent.s.node(node)["attrs"].get(
                "native_correction_reply_plan") == "correction_receipt"
        ]
        assert len(correction_replies) == 1
        assert agent.s.node(correction_replies[0])["attrs"].get("text") == reply
        correction_receipts = [
            agent.s.node(receipt)["attrs"]
            for receipt in agent.s.nodes("ProductionGateReceipt")
            if agent.s.node(receipt)["attrs"].get("parse_back_mode")
            == "conversation_correction_graph"
        ]
        assert correction_receipts
        assert correction_receipts[-1]["status"] == "released"
    elif "not the route" in text:
        assert interpretation["language_discourse_relation"] == "correction"
        assert interpretation["arbitration_basis"] == \
            "corrective_discourse_response"
        assert reply == "I understand the correction."
        correction_replies = [
            node for node in agent.agent_outbound_messages()
            if inbound in agent.responds_to(node)
            and agent.s.node(node)["attrs"].get(
                "native_correction_reply_plan") == "correction_receipt"
        ]
        assert len(correction_replies) == 1


def test_acknowledgement_is_a_distinct_neutral_force():
    assert from_semantic_frame(
        {"communicative_force": "acknowledgement"},
        provider="synthetic_semantic_adapter",
    ) == {
        "evidence_schema": "communication_evidence.v1",
        "evidence_provider": "synthetic_semantic_adapter",
        "evidence_force": "acknowledgement",
        "evidence_goal": "update_common_ground",
    }


def test_refusal_is_a_distinct_neutral_force():
    assert from_semantic_frame(
        {"communicative_force": "refusal"},
        provider="synthetic_semantic_adapter",
    )["evidence_force"] == "refusal"


def test_semantic_frame_preserves_neutral_relation_scope():
    evidence = from_semantic_frame(
        {"communicative_force": "information_request",
         "relation_scope": "event_specific"},
        provider="synthetic_semantic_adapter",
    )
    assert evidence["evidence_relation_scope"] == "event_specific"

    with pytest.raises(ValueError, match="relation_scope is unsupported"):
        from_semantic_frame(
            {"communicative_force": "information_request",
             "relation_scope": "maybe"},
            provider="incomplete_semantic_adapter",
        )

    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    event_result = agent.ingest_semantic_event(
        {"communicative_force": "information_request",
         "relation_scope": "conceptual_general"},
        provider="synthetic_semantic_adapter",
    )
    interpretation = agent.s.node(event_result["interpretation_id"])["attrs"]
    assert interpretation["relation_scope"] == "conceptual_general"


def test_semantic_frame_preserves_language_neutral_relation_focus():
    from domains.communication_evidence import from_semantic_frame

    expected = {
        "es": {
            "relation_focus": "reason", "relation_scope": "event_specific",
            "content_refs": [{"type": "Concept", "name": "signal"}],
        },
        "ja": {
            "relation_focus": "reason", "relation_scope": "event_specific",
            "content_refs": [{"type": "Concept", "name": "signal"}],
        },
    }
    for language, fields in expected.items():
        provider = f"language_adapter:{language}"
        evidence = from_semantic_frame(
            {"speech_act": "question", **fields}, provider=provider)
        assert evidence["evidence_relation_focus"] == "reason"
        assert evidence["evidence_relation_scope"] == "event_specific"
        assert evidence["evidence_content_refs"] == fields["content_refs"]

        agent = WorldAdapter(seeds=())
        load_all_seeds(agent)
        result = agent.ingest_semantic_event(
            {"speech_act": "question", **fields}, provider=provider)
        interpretation = agent.s.node(result["interpretation_id"])["attrs"]
        assert interpretation["communicative_force"] == "request_information"
        assert interpretation["cognitive_goal"] == "answer_or_learn"
        assert interpretation["relation_focus"] == "reason"
        assert interpretation["relation_scope"] == "event_specific"
        assert interpretation["evidence_provider"] == provider

    with pytest.raises(ValueError, match="relation_focus is unsupported"):
        from_semantic_frame(
            {"speech_act": "question", "relation_focus": "surface_form"},
            provider="invalid_semantic_adapter",
        )
    with pytest.raises(ValueError, match="semantic content ref needs typed name"):
        from_semantic_frame(
            {"speech_act": "question",
             "content_refs": [{"type": "Concept"}]},
            provider="incomplete_semantic_adapter",
        )

    # Adapters cannot declare relational support; only live graph evidence
    # and native rules may establish it.
    unsupported = from_semantic_frame(
        {"speech_act": "question", "relation_focus": "reason",
         "relation_support": "supported"},
        provider="untrusted_adapter",
    )
    assert "evidence_relation_support" not in unsupported


def test_spanish_and_japanese_reason_frames_share_native_causal_selection():
    plans = []
    for language in ("es", "ja"):
        agent = WorldAdapter(seeds=())
        load_all_seeds(agent)
        cause = agent.s.add_node(
            "Concept", {"name": f"phase8 semantic cause {language}"})
        effect_name = f"phase8 semantic effect {language}"
        effect = agent.s.add_node("Concept", {"name": effect_name})
        frame = {
            "speech_act": "question", "relation_focus": "reason",
            "relation_scope": "event_specific",
            "relation_target_ref": {
                "type": "Concept", "name": effect_name},
            # A provider cannot turn its semantic claim into relation support.
            "relation_support": "supported",
            "interaction_relation": "response",
        }
        missing = agent.ingest_semantic_event(
            frame, provider=f"language_adapter:{language}",
            interaction_mode="turn_compatible")
        missing_attrs = agent.s.node(
            missing["interpretation_id"])["attrs"]
        assert missing_attrs["relation_target_status"] == "graph_resolved"
        assert missing_attrs["relation_support"] == "missing"
        assert missing_attrs["causal_relation_candidate_count"] == 0
        assert missing_attrs["cognitive_disposition"] == "learn"
        assert not agent.inner.neighbours(
            missing["interpretation_id"], "has_causal_relation_answer_plan")

        agent.inner.add_edge_unchecked(cause, "causal_influence", effect)
        supported = agent.ingest_semantic_event(
            frame, provider=f"language_adapter:{language}",
            interaction_mode="turn_compatible")
        attrs = agent.s.node(supported["interpretation_id"])["attrs"]
        assert attrs["relation_support"] == "supported"
        assert attrs["causal_relation_candidate_count"] == 1
        assert attrs["cognitive_disposition"] == "answer"
        assert attrs["arbitration_basis"] == \
            "supported_causal_relation_evidence"
        selected = list(agent.inner.neighbours(
            supported["interpretation_id"],
            "has_causal_relation_answer_plan"))
        assert len(selected) == 1
        plan = selected[0]
        assert cause in agent.inner.neighbours(plan, "based_on_cause")
        assert effect in agent.inner.neighbours(plan, "based_on_effect")
        assert supported["discourse_event_id"] in agent.inner.neighbours(
            plan, "for_event")

        second_cause = agent.s.add_node(
            "Concept", {"name": f"phase8 semantic alternative {language}"})
        agent.inner.add_edge_unchecked(
            second_cause, "causal_influence", effect)
        ambiguous = agent.ingest_semantic_event(
            frame, provider=f"language_adapter:{language}",
            interaction_mode="turn_compatible")
        ambiguous_attrs = agent.s.node(
            ambiguous["interpretation_id"])["attrs"]
        assert ambiguous_attrs["relation_support"] == "ambiguous"
        assert ambiguous_attrs["causal_relation_candidate_count"] == 2
        assert ambiguous_attrs["cognitive_disposition"] == "learn"
        assert ambiguous_attrs["arbitration_basis"] == \
            "ambiguous_event_specific_causal_evidence"
        assert not agent.inner.neighbours(
            ambiguous["interpretation_id"],
            "has_causal_relation_answer_plan")
        plans.append((attrs["communicative_force"], attrs["cognitive_goal"],
                      attrs["cognitive_disposition"], attrs["arbitration_basis"]))

    assert plans == [
        ("request_information", "answer_or_learn", "answer",
         "supported_causal_relation_evidence"),
    ] * 2


@pytest.mark.parametrize(
    ("literal_form", "interaction_mode", "interaction_relation",
     "expected", "expected_goal"),
    [("social", "turn_compatible", "turn_compatible", "answer",
      "coordinate_socially"),
     ("fragment", "turn_compatible", "overlap", "defer",
      "clarify_or_defer")],
)
def test_social_coordination_disposition_is_native_and_fragment_aware(
        literal_form, interaction_mode, interaction_relation, expected,
        expected_goal):
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    interpretation = agent.s.add_node("CommunicationInterpretation", {
        "schema": "communication_interpretation.v1",
        "evidence_schema": "communication_evidence.v1",
        "evidence_provider": "synthetic_semantic_adapter",
        "evidence_force": "social_action",
        "communicative_force": None,
        "cognitive_goal": None,
        "cognitive_disposition": None,
        "literal_form": literal_form,
        "interaction_mode": interaction_mode,
        "interaction_relation": interaction_relation,
    })
    agent.inner.add_edge_unchecked(
        agent.agent, "holds_interpretation", interpretation)

    agent.inner.run_rules()
    attrs = agent.s.node(interpretation)["attrs"]
    assert attrs["cognitive_disposition"] == expected
    assert attrs["cognitive_goal"] == expected_goal


def test_unresolved_nonturn_information_and_repair_responses_get_native_repair():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    cases = (
        ("What is a blorf?", "non_turn", "standalone",
         ["lexical_syntactic", "explicit_uncertainty"]),
        ("Where is that valve?", "non_turn", "continuation",
         ["discourse_state", "explicit_uncertainty"]),
        ("Who is quorplezap?", "non_turn", "standalone",
         ["lexical_syntactic", "explicit_uncertainty"]),
        ("I did not understand that.", "non_turn", "response",
         ["discourse_state", "explicit_uncertainty"]),
    )
    for text, mode, relation, evidence in cases:
        agent.converse(
            text,
            speech_act=WorldAdapter.classify_speech_act(text),
            context={"interaction_mode": mode,
                     "interaction_relation": relation,
                     "evidence": evidence},
        )
        inbound = agent._last_turn_inbound
        interpretation = agent.s.node(
            agent.s.node(inbound)["attrs"]["communication_interpretation_id"]
        )["attrs"]
        assert interpretation["cognitive_disposition"] == "repair", text
        assert interpretation["cognitive_goal"] == "clarify_or_defer", text
        assert interpretation["arbitration_basis"] in {
            "unresolved_nonturn_information_dependency",
            "unresolved_nonturn_frontier",
            "uncertain_nonturn_frontier",
            "uncertain_response_common_ground_gap",
            "typed_nonunderstanding_report",
        }, text

    permission = "Can I access the sealed room?"
    agent.converse(
        permission,
        speech_act=WorldAdapter.classify_speech_act(permission),
        context={"interaction_mode": "non_turn",
                 "interaction_relation": "standalone",
                 "evidence": ["addressee_model", "explicit_uncertainty"]},
    )
    inbound = agent._last_turn_inbound
    interpretation = agent.s.node(
        agent.s.node(inbound)["attrs"]["communication_interpretation_id"]
    )["attrs"]
    assert interpretation["authority_status"] == "missing"
    assert interpretation["cognitive_disposition"] == "blocked"


def test_compound_unresolved_question_gets_native_repair_not_answer():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    agent.converse(
        "Should we use the north route?", speech_act="question",
        context={"interaction_mode": "turn_compatible",
                 "interaction_relation": "response"},
    )
    reply = agent.converse(
        "Good morning, are we ready?", speech_act="question",
        context={"interaction_mode": "turn_compatible",
                 "interaction_relation": "turn_compatible"},
    )
    inbound = agent._last_turn_inbound
    interpretation = agent.s.node(
        agent.s.node(inbound)["attrs"]["communication_interpretation_id"]
    )["attrs"]
    assert interpretation["evidence_force"] == "information_request"
    assert interpretation["grounding_status"] == "unresolved"
    assert interpretation["cognitive_disposition"] == "repair"
    assert interpretation["cognitive_goal"] == "clarify_or_defer"
    # The utterance contains both a greeting and a polar question. Native
    # compound-act arbitration has a more specific missing-relation basis than
    # the generic unresolved-information rule.
    assert interpretation["arbitration_basis"] == \
        "compound_polar_relation_missing_support"
    assert interpretation.get("answer_commitment_id") is None
    assert "ready" in reply.lower() and "means" in reply.lower()
    receipts = [
        agent.s.node(node)["attrs"]
        for node in agent.s.nodes("ProductionGateReceipt")
        if agent.s.node(node)["attrs"].get("turn_message_id")
        == int(inbound.value)
    ]
    assert receipts
    assert any(item["status"] == "released" for item in receipts)


def test_turn_compatible_unresolved_information_keeps_answer_learning_eligible():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    interpretation = agent.s.add_node("CommunicationInterpretation", {
        "schema": "communication_interpretation.v1",
        "evidence_schema": "communication_evidence.v1",
        "evidence_provider": "synthetic_semantic_adapter",
        "evidence_force": "information_request",
        "communicative_force": None,
        "cognitive_goal": None,
        "cognitive_disposition": None,
        "grounding_status": "unresolved",
        "explicit_uncertainty": 1,
        "interaction_mode": "turn_compatible",
    })
    agent.inner.add_edge_unchecked(
        agent.agent, "holds_interpretation", interpretation)
    agent.inner.run_rules()
    attrs = agent.s.node(interpretation)["attrs"]
    assert attrs["communicative_force"] == "request_information"
    assert attrs.get("cognitive_disposition") != "repair"


def test_supported_event_topic_answer_resolves_reflexive_frontier_natively():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    message = agent.s.add_node("Message", {"text": "event"})
    interpretation = agent.s.add_node("CommunicationInterpretation", {
        "schema": "communication_interpretation.v1",
        "evidence_schema": "communication_evidence.v1",
        "evidence_provider": "synthetic_semantic_adapter",
        "evidence_force": "repair_or_defer",
        "communicative_force": None,
        "cognitive_goal": None,
        "cognitive_disposition": None,
        "dispatch_path": "frontier",
        "reflexive": 1,
        "interaction_mode": "non_turn",
        "interaction_relation": "standalone",
        "grounding_status": "candidate_grounded",
    })
    goal = agent.s.add_node("Goal", {
        "kind": "answer_topic", "status": "active", "concept": "route",
    })
    held = agent.s.add_node("HeldAnswer", {
        "topic": "route", "grounding_referent": "route",
        "grounding_status": "supported",
    })
    evidence = agent.s.add_node("TopicGroundingEvidence", {
        "kind": "topic_answer", "referent": "route", "status": "supported",
    })
    for source, relation, target in (
            (agent.agent, "holds_interpretation", interpretation),
            (interpretation, "interprets", message),
            (agent.agent, "has_goal", goal),
            (goal, "comprehends", message),
            (agent.agent, "holds_answer", held),
            (held, "grounded_by", evidence)):
        agent.inner.add_edge_unchecked(source, relation, target)

    agent.inner.run_rules()
    attrs = agent.s.node(interpretation)["attrs"]
    assert attrs["cognitive_disposition"] == "answer"
    assert attrs["communicative_force"] == "request_information"
    assert attrs["cognitive_goal"] == "answer_or_learn"
    assert attrs["arbitration_basis"] == "supported_event_topic_answer"


def test_supported_selected_concept_answer_authorizes_ordinary_information_event():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    message = agent.s.add_node("Message", {"comp_know_concept": "gate"})
    interpretation = agent.s.add_node("CommunicationInterpretation", {
        "schema": "communication_interpretation.v1",
        "evidence_schema": "communication_evidence.v1",
        "evidence_provider": "synthetic_semantic_adapter",
        "evidence_force": "information_request",
        "grounding_status": "candidate_grounded",
        "communicative_force": None,
        "cognitive_goal": None,
        "cognitive_disposition": None,
    })
    held = agent.s.add_node("HeldAnswer", {
        "topic": "gate", "grounding_referent": "gate",
        "grounding_status": "supported",
    })
    evidence = agent.s.add_node("TopicGroundingEvidence", {
        "kind": "topic_answer", "referent": "gate", "status": "supported",
    })
    for source, relation, target in (
            (agent.agent, "holds_interpretation", interpretation),
            (interpretation, "interprets", message),
            (agent.agent, "holds_answer", held),
            (held, "grounded_by", evidence)):
        agent.inner.add_edge_unchecked(source, relation, target)

    agent.inner.run_rules()
    attrs = agent.s.node(interpretation)["attrs"]
    assert attrs["cognitive_disposition"] == "answer"
    assert attrs["cognitive_goal"] == "answer_or_learn"
    assert attrs["arbitration_basis"] == "supported_selected_concept_answer"


def test_supported_event_bound_topic_goal_selects_information_answer_natively():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    message = agent.s.add_node("Message", {})
    interpretation = agent.s.add_node("CommunicationInterpretation", {
        "schema": "communication_interpretation.v1",
        "evidence_schema": "communication_evidence.v1",
        "evidence_force": "information_request",
        "grounding_status": "candidate_grounded",
        "cognitive_disposition": None,
    })
    goal = agent.s.add_node("Goal", {
        "kind": "answer_topic", "status": "active",
        "concept": "sensor status",
    })
    held = agent.s.add_node("HeldAnswer", {
        "topic": "sensor status", "grounding_referent": "sensor status",
        "grounding_status": "supported",
        "grounding_evidence_path": "held_topic->graph_fact",
    })
    evidence = agent.s.add_node("TopicGroundingEvidence", {
        "kind": "topic_answer", "referent": "sensor status",
        "status": "supported", "evidence_path": "graph_fact->topic",
    })
    for source, relation, target in (
            (agent.agent, "holds_interpretation", interpretation),
            (interpretation, "interprets", message),
            (agent.agent, "has_goal", goal),
            (goal, "comprehends", message),
            (agent.agent, "holds_answer", held),
            (held, "grounded_by", evidence)):
        agent.inner.add_edge_unchecked(source, relation, target)

    agent.inner.run_rules()
    attrs = agent.s.node(interpretation)["attrs"]
    assert attrs["cognitive_disposition"] == "answer"
    assert attrs["communicative_force"] == "request_information"
    assert attrs["cognitive_goal"] == "answer_or_learn"
    assert attrs["arbitration_basis"] == (
        "supported_event_bound_topic_goal_answer")


@pytest.mark.parametrize(
    "relation_focus, relation_support, held_path, evidence_path", [
    ("polar", "supported", "held_topic->graph_fact", "graph_fact->topic"),
    ("reason", "missing", "held_topic->graph_fact", "graph_fact->topic"),
    (None, None, "", "graph_fact->topic"),
    (None, None, "held_topic->graph_fact", ""),
])
def test_event_bound_topic_goal_does_not_substitute_for_relation_evidence(
        relation_focus, relation_support, held_path, evidence_path):
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    message = agent.s.add_node("Message", {})
    interpretation = agent.s.add_node("CommunicationInterpretation", {
        "schema": "communication_interpretation.v1",
        "evidence_schema": "communication_evidence.v1",
        "evidence_force": "information_request",
        "grounding_status": "candidate_grounded",
        "relation_focus": relation_focus,
        "relation_support": relation_support,
        "cognitive_disposition": None,
    })
    goal = agent.s.add_node("Goal", {
        "kind": "answer_topic", "status": "active", "concept": "gate",
    })
    held = agent.s.add_node("HeldAnswer", {
        "topic": "gate", "grounding_referent": "gate",
        "grounding_status": "supported",
        "grounding_evidence_path": held_path,
    })
    evidence = agent.s.add_node("TopicGroundingEvidence", {
        "kind": "topic_answer", "referent": "gate", "status": "supported",
        "evidence_path": evidence_path,
    })
    for source, relation, target in (
            (agent.agent, "holds_interpretation", interpretation),
            (interpretation, "interprets", message),
            (agent.agent, "has_goal", goal),
            (goal, "comprehends", message),
            (agent.agent, "holds_answer", held),
            (held, "grounded_by", evidence)):
        agent.inner.add_edge_unchecked(source, relation, target)

    agent.inner.run_rules()
    assert agent.s.node(interpretation)["attrs"].get(
        "arbitration_basis") != "supported_event_bound_topic_goal_answer"


def test_typed_continuing_action_does_not_require_imperative_clause_form():
    """Semantic action force is authoritative across clause-form variation."""
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    interpretation = agent.s.add_node("CommunicationInterpretation", {
        "schema": "communication_interpretation.v1",
        "evidence_schema": "communication_evidence.v1",
        "evidence_provider": "synthetic_semantic_adapter",
        "evidence_force": "action_request",
        "evidence_goal": "act_or_clarify",
        "literal_form": "declarative",
        "interaction_mode": "non_turn",
        "interaction_relation": "continuation",
        "grounding_status": "unresolved",
        "authority_status": "not_applicable",
        "communicative_force": None,
        "cognitive_goal": None,
        "cognitive_disposition": None,
    })
    agent.inner.add_edge_unchecked(
        agent.agent, "holds_interpretation", interpretation)

    agent.inner.run_rules()
    attrs = agent.s.node(interpretation)["attrs"]
    assert attrs["cognitive_disposition"] == "act"
    assert attrs["communicative_force"] == "request_action"
    assert attrs["arbitration_basis"] == "continuing_action_request"


def test_typed_continuation_fragment_defers_before_action_commitment():
    """A continuation's typed action force must not override its partial form."""
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    interpretation = agent.s.add_node("CommunicationInterpretation", {
        "schema": "communication_interpretation.v1",
        "evidence_schema": "communication_evidence.v1",
        "evidence_provider": "synthetic_semantic_adapter",
        "evidence_force": "action_request",
        "evidence_goal": "act_or_clarify",
        "literal_form": "fragment",
        "interaction_mode": "non_turn",
        "interaction_relation": "continuation",
        "grounding_status": "unresolved",
        "language_referent_status": "supported",
        "authority_status": "not_applicable",
        "communicative_force": None,
        "cognitive_goal": None,
        "cognitive_disposition": None,
    })
    agent.inner.add_edge_unchecked(
        agent.agent, "holds_interpretation", interpretation)

    agent.inner.run_rules()
    attrs = agent.s.node(interpretation)["attrs"]
    assert attrs["cognitive_disposition"] == "defer"
    assert attrs["communicative_force"] == "request_action"
    assert attrs["arbitration_basis"] == "typed_continuation_fragment"


def test_selected_concept_without_grounding_evidence_cannot_authorize_answer():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    message = agent.s.add_node("Message", {"comp_know_concept": "gate"})
    interpretation = agent.s.add_node("CommunicationInterpretation", {
        "schema": "communication_interpretation.v1",
        "evidence_schema": "communication_evidence.v1",
        "evidence_provider": "synthetic_semantic_adapter",
        "evidence_force": "information_request",
        "grounding_status": "candidate_grounded",
        "communicative_force": None,
        "cognitive_goal": None,
        "cognitive_disposition": None,
    })
    held = agent.s.add_node("HeldAnswer", {
        "topic": "gate", "grounding_referent": "gate",
        "grounding_status": "supported",
    })
    for source, relation, target in (
            (agent.agent, "holds_interpretation", interpretation),
            (interpretation, "interprets", message),
            (agent.agent, "holds_answer", held)):
        agent.inner.add_edge_unchecked(source, relation, target)

    agent.inner.run_rules()
    assert agent.s.node(interpretation)["attrs"].get("cognitive_disposition") is None


def test_event_topic_goal_without_supported_answer_cannot_resolve_frontier():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    message = agent.s.add_node("Message", {"text": "event"})
    interpretation = agent.s.add_node("CommunicationInterpretation", {
        "schema": "communication_interpretation.v1",
        "evidence_schema": "communication_evidence.v1",
        "evidence_provider": "synthetic_semantic_adapter",
        "evidence_force": "repair_or_defer",
        "communicative_force": None,
        "cognitive_goal": None,
        "cognitive_disposition": None,
        "dispatch_path": "frontier",
        "reflexive": 1,
        "interaction_mode": "non_turn",
        "interaction_relation": "standalone",
        "grounding_status": "unresolved",
    })
    goal = agent.s.add_node("Goal", {
        "kind": "answer_topic", "status": "active", "concept": "route",
    })
    agent.inner.add_edge_unchecked(
        agent.agent, "holds_interpretation", interpretation)
    agent.inner.add_edge_unchecked(interpretation, "interprets", message)
    agent.inner.add_edge_unchecked(agent.agent, "has_goal", goal)
    agent.inner.add_edge_unchecked(goal, "comprehends", message)

    agent.inner.run_rules()
    attrs = agent.s.node(interpretation)["attrs"]
    assert attrs["cognitive_disposition"] is None
    assert attrs["communicative_force"] == "repair_or_defer"
