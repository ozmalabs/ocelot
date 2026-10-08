"""Neutral action/condition evidence reaches cognition and Goal lifecycle."""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for path in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if path not in sys.path:
        sys.path.insert(0, path)

pytest.importorskip("substrate_rs")

from domains.comprehend_text import comprehend_text  # noqa: E402
from substrate.boot_all import load_all_seeds  # noqa: E402
from substrate.world_adapter import WorldAdapter  # noqa: E402


@pytest.mark.parametrize("text, expected", [
    ("Check the pressure.", ("check", "pressure")),
    ("Open the hatch and check the gauge.", ("open", "hatch")),
])
def test_instruction_adapter_emits_neutral_action_evidence(text, expected):
    agent = WorldAdapter(seeds=())
    comp = comprehend_text(agent, text, kind="instruction")
    evidence = comp.dispatch["language_evidence"]
    assert evidence["action_predicate"].lower() == expected[0]
    assert evidence["action_target"].lower() == expected[1]
    assert evidence["action_target_surface"].lower().endswith(
        f"the {expected[1]}")


def test_unbacked_confirmation_asks_for_source_not_topic_definition():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)

    reply = agent.converse(
        "Can you confirm the route?", speech_act="question",
        context={"interaction_mode": "turn_compatible",
                 "interaction_relation": "response",
                 "literal_form": "interrogative"},
    )
    inbound = agent._last_turn_inbound
    attrs = agent.s.node(inbound)["attrs"]
    interpretation = agent.s.node(
        attrs["communication_interpretation_id"])["attrs"]

    assert interpretation["language_confirmation_request"] == \
        "proposition_confirmation"
    assert interpretation["cognitive_disposition"] == "repair"
    assert interpretation["arbitration_basis"] == \
        "confirmation_lacks_conversational_support"
    assert "route" in reply.lower()
    assert "source" in reply.lower() or "check" in reply.lower()
    assert "what does it mean" not in reply.lower()
    trace = agent.reply_turn_trace(int(inbound.value))
    assert trace["answer_commitment"] is None
    assert trace["production_release"]["parse_back_mode"] == \
        "conversation_action_graph"


def test_typed_speech_function_failure_is_not_a_generic_inability_statement():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)

    failed_request = comprehend_text(
        agent, "This request cannot be processed.", kind="statement")
    assert failed_request.dispatch["language_evidence"][
        "communication_failure"] is True

    ordinary_inability = comprehend_text(
        agent, "The operator cannot process this.", kind="statement")
    assert "communication_failure" not in ordinary_inability.dispatch.get(
        "language_evidence", {})

    unavailable_action = comprehend_text(
        agent, "That action is not available.", kind="statement")
    assert unavailable_action.dispatch["language_evidence"][
        "action_availability"] == "unavailable"

    unavailable_signal = comprehend_text(
        agent, "That signal is not available.", kind="statement")
    assert "action_availability" not in unavailable_signal.dispatch.get(
        "language_evidence", {})

    uncertain_selection = comprehend_text(
        agent, "I am not sure which reading is correct.", kind="statement")
    evidence = uncertain_selection.dispatch["language_evidence"]
    assert evidence["explicit_uncertainty"] is True
    assert evidence["communicative_force"] == "information_request"

    certain_selection = comprehend_text(
        agent, "I am sure which reading is correct.", kind="statement")
    assert "explicit_uncertainty" not in certain_selection.dispatch.get(
        "language_evidence", {})


def test_continuation_adverb_is_not_mistaken_for_action_head():
    agent = WorldAdapter(seeds=())
    comp = comprehend_text(
        agent, "And then inspect the pump.", kind="instruction")
    evidence = comp.dispatch["language_evidence"]
    assert comp.dispatch["predicate"].lower() == "inspect"
    assert evidence["action_predicate"].lower() == "inspect"
    assert evidence["action_target"].lower() == "pump"


def test_polite_action_target_uses_object_head_after_noun_modifier():
    agent = WorldAdapter(seeds=())
    comp = comprehend_text(agent, "Please open the north gate.",
                           kind="statement")
    evidence = comp.dispatch["language_evidence"]
    assert comp.kind == "instruction"
    assert evidence["action_predicate"].lower() == "open"
    assert evidence["action_target"].lower() == "north gate"
    assert evidence["action_target_head"].lower() == "gate"


def test_action_target_preserves_adjectival_modifiers_of_selected_head():
    agent = WorldAdapter(seeds=())
    comp = comprehend_text(agent, "Open the heavy gate.", kind="instruction")
    evidence = comp.dispatch["language_evidence"]
    assert evidence["action_target"].lower() == "heavy gate"
    assert evidence["action_target_head"].lower() == "gate"


def test_action_target_grounding_composes_supported_head_and_modifiers():
    from substrate.boot_all import load_all_seeds

    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    comp = comprehend_text(
        agent, "Inspect the lower sensor.", kind="instruction")
    evidence = comp.dispatch["language_evidence"]

    assert evidence["action_target"] == "lower sensor"
    assert evidence["action_target_head"] == "sensor"
    assert evidence["action_target_modifiers"] == ["lower"]
    status, path = agent._communication_grounding_evidence(
        comp, comp.dispatch["path"])
    assert status == "candidate_grounded"
    assert "typed_compositional_action_target" in path

    unresolved = comprehend_text(
        agent, "Activate the unknown console.", kind="instruction")
    unresolved_status, _ = agent._communication_grounding_evidence(
        unresolved, unresolved.dispatch["path"])
    assert unresolved_status == "unresolved"

    untyped_gap = comprehend_text(
        agent, "Inspect the lower quorplezap sensor.", kind="instruction")
    assert any(element["role"] == "gap"
               for element in untyped_gap.frame["elements"])
    gap_status, _ = agent._communication_grounding_evidence(
        untyped_gap, untyped_gap.dispatch["path"])
    assert gap_status == "unresolved"


def test_connected_conversation_profile_grounds_sourced_objects_but_not_oov():
    from substrate.boot_profiles import load_conversation_seed_profile

    agent = WorldAdapter(seeds=())
    report = load_conversation_seed_profile(agent)
    assert report["selection_complete"] is True
    assert "wordnet_common_objects" in report["selection"][
        "selected_seed_ids"]
    pump = agent._concept_by_name("pump")
    assert pump is not None
    assert agent.s.node(pump)["attrs"]["lexical_source_id"] == "pump.n.01"

    hatch = agent._concept_by_name("hatch")
    assert hatch is not None
    assert agent.s.node(hatch)["attrs"]["lexical_source_id"] == "hatch.n.03"

    deferred = comprehend_text(
        agent, "When ready, close the hatch.", kind="instruction")
    deferred_status, deferred_path = agent._communication_grounding_evidence(
        deferred, deferred.dispatch["path"])
    assert deferred_status == "candidate_grounded"
    assert deferred_path == "CommunicationInterpretation -> Concept.referent"

    deferred_reply = agent.converse(
        "When ready, close the hatch.", speech_act="instruction",
        context={"interaction_mode": "non_turn"})
    deferred_inbound = agent._last_turn_inbound
    deferred_interpretation = agent.s.node(deferred_inbound)["attrs"][
        "communication_interpretation_id"]
    deferred_attrs = agent.s.node(deferred_interpretation)["attrs"]
    assert deferred_attrs["grounding_status"] == "candidate_grounded"
    assert deferred_attrs["cognitive_disposition"] == "defer"
    assert "deferred" in deferred_reply.lower()
    deferred_goals = [agent.s.node(node)["attrs"] for node in
                      agent.inner.neighbours(agent.agent, "has_goal")
                      if deferred_inbound in agent.inner.neighbours(
                          node, "comprehends")]
    assert any(goal.get("source") == "conversation"
               and goal["status"] == "deferred"
               for goal in deferred_goals)

    supported = comprehend_text(
        agent, "And then inspect the pump.", kind="instruction")
    supported_status, _ = agent._communication_grounding_evidence(
        supported, supported.dispatch["path"])
    assert supported_status == "candidate_grounded"

    text = "And then inspect the pump."
    reply = agent.converse(
        text, speech_act=agent.classify_speech_act(text),
        context={"interaction_mode": "non_turn",
                 "interaction_relation": "continuation"})
    inbound = agent._last_turn_inbound
    interpretation = agent.s.node(inbound)["attrs"][
        "communication_interpretation_id"]
    attrs = agent.s.node(interpretation)["attrs"]
    assert attrs["grounding_status"] == "candidate_grounded"
    assert attrs["cognitive_disposition"] == "act"
    assert "no faculty" in reply

    unknown = comprehend_text(
        agent, "And then inspect the blorf.", kind="instruction")
    unknown_status, _ = agent._communication_grounding_evidence(
        unknown, unknown.dispatch["path"])
    assert unknown_status == "unresolved"


def test_action_target_preserves_noun_modifier_in_correction_route():
    agent = WorldAdapter(seeds=())
    comp = comprehend_text(agent, "Actually, use the east path.",
                           kind="instruction")
    evidence = comp.dispatch["language_evidence"]
    assert evidence["action_target"].lower() == "east path"
    assert evidence["action_target_head"].lower() == "path"


def test_anaphoric_action_target_is_not_replaced_by_trailing_adverb():
    agent = WorldAdapter(seeds=())
    comp = comprehend_text(agent, "Move it now.", kind="instruction")
    evidence = comp.dispatch["language_evidence"]
    assert evidence["action_target"].lower() == "it"
    assert evidence["referent_status"] == "unresolved"


def test_unresolved_second_sequential_action_marks_compound_for_repair():
    agent = WorldAdapter(seeds=())
    comp = comprehend_text(
        agent, "look left then quorplezap the door", kind="instruction")
    evidence = comp.dispatch["language_evidence"]
    assert evidence["action_predicate"] == "look"
    assert evidence["action_target"] == "left"
    assert evidence["sequence_relation"] == "sequential"
    assert evidence["sequence_status"] == "unresolved_action_head"
    assert evidence["referent_status"] == "unresolved"
    assert evidence["repair_focus"] == "quorplezap"


def test_unknown_initial_action_head_is_not_replaced_by_its_object():
    agent = WorldAdapter(seeds=())
    comp = comprehend_text(agent, "Quorplezap the door.", kind="instruction")
    evidence = comp.dispatch["language_evidence"]

    assert "action_predicate" not in evidence
    assert evidence["referent_status"] == "unresolved"
    assert evidence["repair_evidence"] == "unresolved_action_head"
    assert evidence["repair_focus"] == "Quorplezap"


@pytest.mark.parametrize("text, expected", [
    ("Actually, use the east path.", "use"),
    ("Operator, please listen.", "listen"),
])
def test_instruction_adapter_selects_verb_head_after_prefatory_constituent(
        text, expected):
    agent = WorldAdapter(seeds=())
    comp = comprehend_text(agent, text, kind="instruction")
    evidence = comp.dispatch["language_evidence"]
    assert evidence["action_predicate"].lower() == expected
    if expected == "use":
        assert evidence["discourse_relation"] == "correction"
    else:
        assert evidence["social_act_evidence"] == "addressed_attention_request"


@pytest.mark.parametrize("text", [
    "Quickly, use the east path.",
    "Please listen.",
])
def test_prefatory_adverb_and_unaddressed_politeness_do_not_overtype_social_force(text):
    agent = WorldAdapter(seeds=())
    comp = comprehend_text(agent, text, kind="instruction")
    evidence = comp.dispatch["language_evidence"]
    assert evidence.get("discourse_relation") != "correction"
    assert evidence.get("social_act_evidence") != "addressed_attention_request"


def test_temporal_focus_emits_deferred_condition_evidence():
    agent = WorldAdapter(seeds=())
    comp = comprehend_text(agent, "When ready, close the hatch.",
                          kind="instruction")
    evidence = comp.dispatch["language_evidence"]
    assert evidence["action_predicate"].lower() == "close"
    assert evidence["action_target"].lower() == "hatch"
    assert evidence["deferred_condition"] is True


@pytest.mark.parametrize("text, expected", [
    ("Promote the first concern.", "first concern"),
    ("Stop working on that.", "that"),
    ("look left then quorplezap the door", "left"),
])
def test_action_target_uses_typed_head_or_anaphoric_complement(text, expected):
    """Targets retain full nominal arguments, anaphors, and clause bounds."""
    agent = WorldAdapter(seeds=())
    comp = comprehend_text(agent, text, kind="instruction")
    evidence = comp.dispatch["language_evidence"]
    assert evidence["action_target"].lower() == expected
    if text.startswith("Promote"):
        assert evidence["action_target_head"].lower() == "concern"


def test_compound_instruction_graph_content_keeps_first_action_target():
    """Do not let the single-clause relation composer replace the first
    clause's typed target with the later clause's object in graph readback."""
    agent = WorldAdapter(seeds=())
    text = "look left then quorplezap the door"
    comp = comprehend_text(agent, text, kind="instruction")
    inbound = agent.receive_utterance(text, speech_act="instruction")
    agent._write_comprehension_to_graph(inbound, comp)

    attrs = agent.s.node(inbound)["attrs"]
    assert attrs["comp_predicate"] == "look"
    assert attrs["comp_content"] == "left"
    assert comp.dispatch["language_evidence"]["action_target"] == "left"


def test_ambiguous_adjective_before_noun_preserves_the_noun_head():
    from domains.construction_grammar import compose_relation, parse_with_gaps

    frame = parse_with_gaps("Promote the first concern.")
    assert [(e["surface"].lower().strip("."), e["pos"])
            for e in frame["elements"] if e["role"] == "content"] == [
                ("promote", "verb"), ("first", "adj"), ("concern", "noun")]
    assert compose_relation(frame)["object"]["surface"].lower().strip(".") == "concern"


def test_selected_meta_faculty_survives_incidental_spatial_pp_evidence():
    agent = WorldAdapter(seeds=())
    comp = comprehend_text(
        agent, "What gaps do you have in your knowledge?", kind="question")

    assert comp.dispatch["path"] == "table"
    assert comp.table_spec.kind == "meta"
    assert comp.dispatch["language_evidence"]["world_dependency"] == "spatial_relation"
    status, evidence_path = agent._communication_grounding_evidence(
        comp, comp.dispatch["path"])
    assert status == "candidate_grounded"
    assert evidence_path.endswith("selected_graph_faculty")


def test_unavailable_spatial_topic_remains_unresolved():
    agent = WorldAdapter(seeds=())
    comp = comprehend_text(agent, "What is in the image?", kind="question")

    assert comp.dispatch["path"] == "frontier"


def test_until_temporal_connector_emits_neutral_deferred_condition_evidence():
    agent = WorldAdapter(seeds=())
    comp = comprehend_text(agent, "Wait until the signal changes.",
                          kind="instruction")
    evidence = comp.dispatch["language_evidence"]
    assert evidence["action_predicate"].lower() == "wait"
    assert evidence["deferred_condition"] is True
    assert evidence["condition_evidence"] == "typed_temporal_connector"


def test_temporal_preposition_without_condition_predicate_is_not_deferred():
    agent = WorldAdapter(seeds=())
    comp = comprehend_text(agent, "Look after the child.",
                          kind="instruction")
    evidence = comp.dispatch["language_evidence"]
    assert "deferred_condition" not in evidence


def test_unresolved_locative_reference_stays_distinct_from_no_world_perception():
    agent = WorldAdapter(seeds=())
    reference = comprehend_text(
        agent, "Describe the place over there.", kind="instruction")
    no_world = comprehend_text(
        agent, "Describe the object behind you.", kind="instruction")

    assert reference.dispatch["path"] == "instruction"
    assert reference.dispatch["language_evidence"]["referent_status"] == "unresolved"
    assert reference.dispatch["language_evidence"]["referent_target"] == "there"
    assert no_world.dispatch["path"] == "honest_no_world"


def test_deferred_instruction_goal_is_not_immediate_execution():
    agent = WorldAdapter(seeds=())
    reply = agent.converse(
        "When ready, close the hatch.", speech_act="instruction",
        context={"interaction_mode": "non_turn"})
    assert reply
    assert "deferred" in reply.lower()
    assert "took on the goal" not in reply.lower()
    goals = [agent.s.node(node)["attrs"] for node in agent.s.nodes("Goal")
             if agent.s.node(node)["attrs"].get("predicate") == "close"]
    assert goals
    assert any(goal.get("status") == "deferred" for goal in goals)
    receipts = [agent.s.node(node)["attrs"]
                for node in agent.s.nodes("ProductionGateReceipt")]
    released = [receipt for receipt in receipts
                if receipt.get("status") == "released"]
    assert len(released) == 1
    assert released[0]["semantic_intent"] == "defer"
    trace = agent.reply_turn_trace(agent.last_turn_inbound_id())
    assert trace["reply"] == reply
    assert trace["production_release"]["semantic_intent"] == "defer"


def test_until_condition_defers_bound_goal_in_non_turn_instruction():
    agent = WorldAdapter(seeds=())
    reply = agent.converse(
        "Wait until the signal changes.", speech_act="instruction",
        context={"interaction_mode": "non_turn", "literal_form": "imperative"})
    assert reply
    inbound = agent._last_turn_inbound
    goals = [agent.s.node(goal)["attrs"]
             for goal in agent.inner.neighbours(agent.agent, "has_goal")
             if inbound in agent.inner.neighbours(goal, "comprehends")]
    assert len(goals) == 1
    assert goals[0]["status"] == "deferred"
    assert goals[0]["defer_reason"] == "typed_temporal_connector"


@pytest.mark.parametrize("text,expected_predicate", [
    ("Check the pressure.", "check"),
    ("When ready, close the hatch.", "close"),
])
def test_signal_only_imperatives_reach_native_instruction_route(
        text, expected_predicate):
    from substrate.boot_all import load_all_seeds

    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    # Exercise the live topic-shift rule too: an action object must not be
    # reinterpreted as a new answer topic merely because a current topic exists.
    agent._set_current_topic("north")
    speech_act = agent.classify_speech_act(text)
    assert speech_act == "request"
    reply = agent.converse(
        text, speech_act=speech_act,
        context={"interaction_mode": "turn_compatible"})
    inbound = agent._last_turn_inbound
    attrs = agent.s.node(inbound)["attrs"]
    assert attrs["sak_kind"] == "instruction"
    assert attrs["comp_kind"] == "instruction"
    assert attrs["comp_dispatch_path"] == "instruction"
    assert any(
        str(agent.s.node(goal)["attrs"].get("predicate") or "").lower()
        == expected_predicate
        and inbound in agent.inner.neighbours(goal, "comprehends")
        for goal in agent.inner.neighbours(agent.agent, "has_goal")
        if agent.s.has_node(goal)
    )
    assert not any(
        agent.s.node(goal)["attrs"].get("kind") == "answer_topic"
        and inbound in agent.inner.neighbours(goal, "comprehends")
        for goal in agent.inner.neighbours(agent.agent, "has_goal")
        if agent.s.has_node(goal)
    )
    assert not any(
        agent.s.node(request)["attrs"].get("status") in {"requested", "running"}
        for request in agent.s.nodes("SearchRequest")
        if agent.s.has_node(request)
    )
    assert reply


def test_graph_semantic_knowledge_deficit_enters_repair_lifecycle():
    from substrate.boot_all import load_all_seeds

    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    reply = agent.converse(
        "I need more information.", speech_act="statement",
        context={"interaction_mode": "non_turn"})
    assert reply
    assert reply != "ERROR: no communicative response could be generated."
    inbound = agent._last_turn_inbound
    attrs = agent.s.node(inbound)["attrs"]
    assert attrs["comp_dispatch_path"] == "frontier"
    assert attrs["comp_intent"] == "repair:knowledge_deficit"
    receipts = [agent.s.node(node)["attrs"]
                for node in agent.s.nodes("ProductionGateReceipt")]
    assert any(item.get("parse_back_mode") == "conversation_action_graph"
               and item.get("status") == "released" for item in receipts)


def test_world_support_gap_remains_explicit_blocked_boundary():
    from domains.comprehend_text import comprehend_text
    from domains.conversation_action import is_ask_back

    agent = WorldAdapter(seeds=())
    comp = comprehend_text(agent, "What is beyond the wall?", kind="question")
    assert comp.dispatch["language_evidence"]["world_support"] == "missing"
    assert is_ask_back(comp) is False


def test_world_support_evidence_survives_selected_interpretation():
    agent = WorldAdapter(seeds=())
    agent.converse("What is beyond the wall?", speech_act="question")
    inbound = agent._last_turn_inbound
    interpretation = agent.s.node(
        agent.s.node(inbound)["attrs"]["communication_interpretation_id"])
    assert interpretation["attrs"]["language_world_support"] == "missing"
    assert interpretation["attrs"]["cognitive_disposition"] == "blocked"
    assert interpretation["attrs"]["communicative_force"] == \
        "repair_or_defer"
    assert interpretation["attrs"]["cognitive_goal"] == "clarify_or_defer"


def test_answer_authority_requires_event_bound_goal_and_supported_graph_evidence():
    from substrate_rs import NodeID
    from substrate.boot_all import load_all_seeds

    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    agent._persist_held_answer("sensor status", "nominal")
    agent.converse(
        "What is the sensor status?", speech_act="question",
        context={"interaction_mode": "non_turn",
                 "interaction_relation": "standalone"},
    )
    inbound_id = agent.last_turn_inbound_id()
    trace = agent.reply_turn_trace(inbound_id)
    commitment = trace["answer_commitment"]
    assert commitment["kind"] == "supported_event_bound_topic_answer"
    assert commitment["graph_linked_to_turn"] is True
    assert commitment["concept"] == "sensor status"

    # A stale/unsupported HeldAnswer must not continue to authorize the turn.
    agent.inner.set_attr(
        NodeID(commitment["held_answer_id"]), "grounding_status", "unresolved")
    assert agent.reply_turn_trace(inbound_id)["answer_commitment"] is None


def test_explicit_reason_question_requires_a_graph_causal_relation():
    from substrate.boot_all import load_all_seeds

    agent = WorldAdapter(seeds=())
    seed_report = load_all_seeds(agent)
    assert "communication_causal_retrieval" in seed_report["order"]
    assert not any(
        "communication_causal_retrieval" in str(failure)
        for failure in seed_report["failed"]
    ), seed_report["failed"]
    reply = agent.converse(
        "Why did the alarm trigger?", speech_act="question",
        context={"interaction_mode": "turn_compatible",
                 "interaction_relation": "response",
                 "literal_form": "interrogative"},
    )
    inbound = agent._last_turn_inbound
    attrs = agent.s.node(inbound)["attrs"]
    assert attrs["comp_relation_focus"] == "reason"
    assert attrs["comp_know_concept"] == "alarm"
    assert agent._relation_has_causal_evidence(inbound) is False
    interpretation = agent.s.node(attrs["communication_interpretation_id"])
    assert interpretation["attrs"]["relation_support"] == "missing"
    # A non-anaphoric reason request remains a learning goal. This is an
    # event-specific past question, while the current external provider only
    # returns topic-level causes; do not dispatch that incompatible lookup.
    assert interpretation["attrs"]["cognitive_disposition"] == "learn"
    assert interpretation["attrs"]["cognitive_goal"] == "answer_or_learn"
    assert interpretation["attrs"]["language_relation_scope"] == "event_specific"
    assert interpretation["attrs"]["relation_scope"] == "event_specific"
    requests = [
        node for node in agent.s.nodes("CausalRetrievalRequest")
        if inbound in agent.inner.neighbours(node, "for_event")
    ]
    assert requests == []
    trace = agent.reply_turn_trace(int(inbound.value))
    assert trace["answer_commitment"] is None
    assert trace["production_release"]["parse_back_mode"] == \
        "conversation_action_graph"
    assert trace["production_release"]["receipt_id"]
    assert reply != "ERROR: no communicative response could be generated."
    assert "information" in reply.lower()
    merely_affected = agent.s.add_node(
        "Concept", {"name": "alarm consequence"})
    agent.inner.add_edge_unchecked(
        agent._concept_by_name("alarm"), "causal_influence", merely_affected)
    assert agent._relation_has_causal_evidence(inbound) is False, (
        "an outgoing effect cannot answer what caused the selected topic")

    # The same reason query is answer-eligible when a causal relation is
    # already present before the event. This is a structural positive control,
    # not a lexical exception for the example sentence.
    supported_agent = WorldAdapter(seeds=())
    load_all_seeds(supported_agent)
    alarm = supported_agent._concept_by_name("alarm")
    if alarm is None:
        alarm = supported_agent.s.add_node("Concept", {"name": "alarm"})
    cause = supported_agent.s.add_node(
        "Concept", {"name": "test causal antecedent"})
    supported_agent.inner.add_edge_unchecked(
        cause, "causal_influence", alarm)
    supported_reply = supported_agent.converse(
        "Why did the alarm trigger?", speech_act="question",
        context={"interaction_mode": "turn_compatible",
                 "interaction_relation": "response",
                 "literal_form": "interrogative"},
    )
    supported_inbound = supported_agent._last_turn_inbound
    supported_attrs = supported_agent.s.node(supported_inbound)["attrs"]
    supported_interpretation = supported_agent.s.node(
        supported_attrs["communication_interpretation_id"])["attrs"]
    assert supported_interpretation["relation_support"] == "supported"
    assert supported_interpretation.get("cognitive_disposition") != "repair"
    assert supported_agent._relation_has_causal_evidence(supported_inbound) is True
    assert supported_agent.s.nodes("CausalRetrievalRequest") == []
    supported_trace = supported_agent.reply_turn_trace(
        int(supported_inbound.value))
    assert supported_trace["answer_commitment"][
        "kind"] == "linked_graph_answer_message"
    assert supported_trace["answer_commitment"]["surface_bound"] is True
    assert supported_trace["production_release"]["parse_back_mode"] == \
        "conversation_causal_relation_graph"
    assert supported_agent.graph_turn_reply(supported_inbound) == supported_reply

    # A second live cause makes the answer ambiguous. A prior successful turn
    # cannot lend its selected cause or answer plan to this new event.
    alternative = supported_agent.s.add_node(
        "Concept", {"name": "alternative causal antecedent"})
    supported_agent.inner.add_edge_unchecked(
        alternative, "causal_influence", alarm)
    supported_agent.converse(
        "Why did the alarm trigger?", speech_act="question",
        context={"interaction_mode": "turn_compatible",
                 "interaction_relation": "response",
                 "literal_form": "interrogative"},
    )
    ambiguous_inbound = supported_agent._last_turn_inbound
    ambiguous_attrs = supported_agent.s.node(ambiguous_inbound)["attrs"]
    ambiguous_interpretation = supported_agent.s.node(
        ambiguous_attrs["communication_interpretation_id"])["attrs"]
    assert ambiguous_interpretation["causal_relation_candidate_count"] == 2
    assert ambiguous_interpretation.get("cognitive_disposition") != "answer"
    assert not supported_agent.inner.neighbours(
        ambiguous_attrs["communication_interpretation_id"],
        "has_causal_relation_answer_plan")
    assert supported_agent.reply_turn_trace(
        int(ambiguous_inbound.value))["answer_commitment"] is None


def test_unknown_turn_compatible_information_request_selects_learning_not_answer():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    reply = agent.converse(
        "Will it rain today?", speech_act="question",
        context={"interaction_mode": "turn_compatible",
                 "interaction_relation": "turn_compatible"},
    )
    inbound = agent._last_turn_inbound
    attrs = agent.s.node(inbound)["attrs"]
    interpretation = agent.s.node(
        attrs["communication_interpretation_id"])["attrs"]
    assert interpretation["cognitive_disposition"] == "learn"
    assert interpretation["cognitive_goal"] == "answer_or_learn"
    assert interpretation["arbitration_basis"] == (
        "turn_compatible_unknown_information_request")
    assert "information" in reply.lower() and "answer" in reply.lower()
    assert agent.reply_turn_trace(int(inbound.value))[
        "answer_commitment"] is None
    requests = [
        node for node in agent.s.nodes("InformationLearningRequest")
        if inbound in agent.inner.neighbours(node, "for_event")
    ]
    assert len(requests) == 1
    request_attrs = agent.s.node(requests[0])["attrs"]
    assert request_attrs["status"] == "requested"
    assert request_attrs["authority"] == "none"
    assert request_attrs["answer_authority"] == "none"
    assert agent._concept_by_name("rain") in agent.inner.neighbours(
        requests[0], "about_topic")
    readback = agent.production_turn_evidence(inbound)[
        "information_learning_requests"]
    assert len(readback) == 1
    assert readback[0]["node_id"] == int(requests[0].value)
    assert readback[0]["topic_concepts"][0]["name"] == "rain"
    assert readback[0]["answer_authority"] == "none"

    # The structurally distinct non-turn unknown-question control remains a
    # repair, and the new rule does not promote its unknown referent to learn.
    control = WorldAdapter(seeds=())
    load_all_seeds(control)
    control.converse(
        "Who is quorplezap?", speech_act="question",
        context={"interaction_mode": "non_turn",
                 "interaction_relation": "standalone"},
    )
    control_inbound = control._last_turn_inbound
    control_attrs = control.s.node(control_inbound)["attrs"]
    control_interpretation = control.s.node(
        control_attrs["communication_interpretation_id"])["attrs"]
    assert control_interpretation["cognitive_disposition"] == "repair"
    assert control.s.nodes("InformationLearningRequest") == []

    social = WorldAdapter(seeds=())
    load_all_seeds(social)
    social.converse(
        "Good morning, are we ready?", speech_act="question",
        context={"interaction_mode": "turn_compatible",
                 "interaction_relation": "turn_compatible"},
    )
    social_inbound = social._last_turn_inbound
    social_attrs = social.s.node(social_inbound)["attrs"]
    social_interpretation = social.s.node(
        social_attrs["communication_interpretation_id"])["attrs"]
    assert social_interpretation.get("cognitive_disposition") != "learn"
    assert social.s.nodes("InformationLearningRequest") == []
