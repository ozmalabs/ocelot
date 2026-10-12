"""Explicit uncertainty is a language-neutral native error disposition."""

from substrate.boot_all import load_all_seeds
from substrate.world_adapter import WorldAdapter


def test_standalone_unresolved_frontier_gets_native_repair_without_corpus_labels():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    text = "Who is quorplezap?"
    reply = agent.converse(
        text,
        speech_act=agent.classify_speech_act(text),
        context={
            "interaction_mode": "non_turn",
            "interaction_relation": "standalone",
        },
    )
    inbound = agent._last_turn_inbound
    interpretation = agent.s.node(
        agent.s.node(inbound)["attrs"]["communication_interpretation_id"]
    )["attrs"]

    assert interpretation["dispatch_path"] == "frontier"
    assert interpretation["grounding_status"] in {"unresolved", "unknown"}
    assert interpretation.get("explicit_uncertainty", 0) == 0
    assert interpretation["cognitive_disposition"] == "repair"
    assert interpretation["arbitration_basis"] == "unresolved_nonturn_frontier"
    assert "quorplezap" in reply.lower()
    assert reply != "ERROR: no communicative response could be generated."
    inbound_id = int(inbound.value)
    assert any(
        agent.s.node(node)["attrs"].get("status") == "released"
        and agent.s.node(node)["attrs"].get("parse_back_mode")
        == "conversation_action_graph"
        and agent.s.node(node)["attrs"].get("turn_message_id") == inbound_id
        and agent.s.node(node)["attrs"].get("surface") == reply
        for node in agent.s.nodes("ProductionGateReceipt")
    )


def test_parse_typed_referent_and_fragment_boundaries_need_no_corpus_evidence():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    cases = (
        ("Where is that valve?", "non_turn", "continuation", "repair"),
        ("Describe the place over there.", "turn_compatible", "continuation", "repair"),
        ("Activate the unknown console.", "turn_compatible",
         "turn_compatible", "repair"),
        ("Please—", "non_turn", "continuation", "defer"),
    )
    for text, mode, relation, expected in cases:
        agent.converse(
            text,
            speech_act=agent.classify_speech_act(text),
            context={"interaction_mode": mode,
                     "interaction_relation": relation},
        )
        inbound = agent._last_turn_inbound
        interpretation = agent.s.node(
            agent.s.node(inbound)["attrs"]["communication_interpretation_id"]
        )["attrs"]
        assert interpretation.get("explicit_uncertainty", 0) == 0, text
        assert interpretation["cognitive_disposition"] == expected, (
            text, {key: interpretation.get(key) for key in (
                "anaphor", "grounding_status", "language_referent_status",
                "authority_status", "literal_form", "dispatch_path",
                "arbitration_basis", "cognitive_goal")})
        if text == "Where is that valve?":
            assert interpretation["anaphor"] == 1
            assert interpretation["arbitration_basis"] == \
                "unresolved_nonturn_information_dependency"
        elif text == "Describe the place over there.":
            assert interpretation["evidence_force"] == "information_request"
            assert interpretation["language_referent_status"] == "unresolved"
            assert interpretation["arbitration_basis"] == \
                "unresolved_continuing_information_referent"
        elif text == "Please—":
            assert interpretation["literal_form"] == "fragment"
            assert interpretation["arbitration_basis"] in {
                "typed_continuation_fragment", "grounding_failure"}
        else:
            assert (
                interpretation.get("language_referent_status") == "unresolved"
                or interpretation.get("grounding_status") in {
                    "unresolved", "unresolved_reference", "unknown"}
                or interpretation.get("gap_count", 0) > 0
            )
            assert interpretation["arbitration_basis"] in {
                "typed_unresolved_action_dependency", "instruction_force"}


def test_native_unresolved_question_reference_releases_a_clarification():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    reply = agent.converse(
        "Where is that valve?", speech_act="question",
        context={"interaction_mode": "non_turn",
                 "interaction_relation": "continuation"})
    inbound = agent._last_turn_inbound
    interpretation = agent.s.node(
        agent.s.node(inbound)["attrs"]["communication_interpretation_id"]
    )["attrs"]

    assert interpretation["cognitive_disposition"] == "repair"
    assert interpretation["arbitration_basis"] == (
        "unresolved_nonturn_information_dependency")
    assert reply != "ERROR: no communicative response could be generated."
    assert reply == "Which valve are you referring to?"
    assert any(
        agent.s.node(node)["attrs"].get("status") == "released"
        and agent.s.node(node)["attrs"].get("parse_back_mode")
        == "conversation_action_graph"
        and agent.s.node(node)["attrs"].get("turn_message_id")
        == int(inbound.value)
        and agent.s.node(node)["attrs"].get("surface") == reply
        for node in agent.s.nodes("ProductionGateReceipt")
    )


def test_explicit_uncertainty_is_not_released_as_generic_repair():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    reply = agent.converse(
        "[unintelligible]",
        speech_act="statement",
        context={
            "interaction_mode": "turn_compatible",
            "interaction_relation": "turn_compatible",
            "literal_form": "fragment",
            "evidence": ["explicit_uncertainty", "explicit_failure", "discourse_state"],
        },
    )
    inbound = agent._last_turn_inbound
    interpretation = agent.s.node(
        agent.s.node(inbound)["attrs"]["communication_interpretation_id"]
    )["attrs"]

    assert reply == "ERROR: no communicative response could be generated."
    assert interpretation["explicit_uncertainty"] == 1
    assert interpretation["explicit_failure"] == 1
    assert interpretation["cognitive_disposition"] == "error"
    assert interpretation["cognitive_goal"] == "error"
    assert interpretation["arbitration_basis"] == "explicit_failure"


def test_asr_failure_marker_types_error_without_corpus_evidence():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    reply = agent.converse("[unintelligible]", speech_act="statement")
    inbound = agent._last_turn_inbound
    interpretation = agent.s.node(
        agent.s.node(inbound)["attrs"]["communication_interpretation_id"]
    )["attrs"]

    assert interpretation.get("explicit_uncertainty") == 0
    assert interpretation["explicit_failure"] == 1
    assert interpretation["cognitive_disposition"] == "error"
    assert reply == "ERROR: no communicative response could be generated."


def test_ordinary_uncertainty_does_not_become_error():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    agent.converse(
        "Please—",
        speech_act="statement",
        context={
            "interaction_mode": "non_turn",
            "interaction_relation": "continuation",
            "literal_form": "fragment",
            "evidence": ["explicit_uncertainty", "discourse_state"],
        },
    )
    inbound = agent._last_turn_inbound
    interpretation = agent.s.node(
        agent.s.node(inbound)["attrs"]["communication_interpretation_id"]
    )["attrs"]

    assert interpretation["explicit_uncertainty"] == 1
    assert interpretation["explicit_failure"] == 0
    assert interpretation.get("cognitive_disposition") != "error"


def test_typed_unresolved_instruction_dependency_gets_native_repair():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    agent.converse(
        "Reset that device.", speech_act="instruction",
        context={"literal_form": "imperative",
                 "evidence": ["explicit_uncertainty"]})
    inbound = agent._last_turn_inbound
    interpretation = agent.s.node(
        agent.s.node(inbound)["attrs"]["communication_interpretation_id"]
    )["attrs"]

    assert interpretation["language_referent_status"] == "unresolved"
    assert interpretation["cognitive_disposition"] == "repair"
    assert interpretation["arbitration_basis"] == "typed_unresolved_action_dependency"


def test_unresolved_instruction_gets_repair_from_typed_referent_without_uncertainty_label():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    agent.converse("Reset that device.", speech_act="instruction",
                   context={"literal_form": "imperative"})
    inbound = agent._last_turn_inbound
    interpretation = agent.s.node(
        agent.s.node(inbound)["attrs"]["communication_interpretation_id"]
    )["attrs"]

    assert interpretation["language_referent_status"] == "unresolved"
    assert interpretation["explicit_uncertainty"] == 0
    assert interpretation["cognitive_disposition"] == "repair"
    assert interpretation["arbitration_basis"] == \
        "typed_unresolved_action_dependency"


def test_typed_uncertainty_with_unresolved_action_gap_repairs_even_if_object_resolves():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    reply = agent.converse(
        "Activate the unknown console.", speech_act="instruction",
        context={"literal_form": "imperative",
                 "evidence": ["lexical_syntactic", "explicit_uncertainty"]})
    inbound = agent._last_turn_inbound
    interpretation = agent.inner.node(
        agent.s.node(inbound)["attrs"]["communication_interpretation_id"]
    )["attrs"]

    assert interpretation["grounding_status"] == "unresolved"
    assert interpretation["gap_count"] > 0
    assert interpretation["explicit_uncertainty"] == 1
    assert interpretation["cognitive_disposition"] == "repair"
    assert interpretation["arbitration_basis"] == "typed_unresolved_action_dependency"
    assert agent.s.node(inbound)["attrs"]["communication_route"] == "ask_back"
    assert reply.rstrip().endswith("?")


def test_production_parse_form_releases_native_action_repair_without_reference_label():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    expected_forces = {
        "Activate the unknown console.": "request_action",
        "Describe the place over there.": "request_information",
        "Reset that device.": "request_action",
    }
    for text, expected_force in expected_forces.items():
        agent.converse(
            text,
            speech_act=WorldAdapter.classify_speech_act(text),
            context={"interaction_mode": "turn_compatible",
                     "interaction_relation": "turn_compatible",
                     "evidence": ["lexical_syntactic", "explicit_uncertainty"]},
        )
        inbound = agent._last_turn_inbound
        interpretation = agent.s.node(
            agent.s.node(inbound)["attrs"]["communication_interpretation_id"]
        )["attrs"]
        assert interpretation["literal_form"] == "imperative"
        assert interpretation["literal_form_source"] == "language_adapter_parse"
        assert interpretation["communicative_force"] == expected_force
        assert interpretation["cognitive_disposition"] == "repair"


def test_uncertain_continuing_common_ground_event_gets_native_repair():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    agent.converse(
        "No, I may have misread it.",
        speech_act=WorldAdapter.classify_speech_act(
            "No, I may have misread it."),
        context={"interaction_mode": "non_turn",
                 "interaction_relation": "continuation",
                 "evidence": ["discourse_state", "explicit_uncertainty"]},
    )
    inbound = agent._last_turn_inbound
    interpretation = agent.s.node(
        agent.s.node(inbound)["attrs"]["communication_interpretation_id"]
    )["attrs"]
    assert interpretation["cognitive_disposition"] == "repair"
    assert interpretation["communicative_force"] == "assertion_or_correction"


def test_unresolved_locative_reference_repairs_but_unavailable_world_stays_blocked():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    agent.converse(
        "Describe the place over there.", speech_act="instruction",
        context={"literal_form": "imperative",
                 "evidence": ["explicit_uncertainty"]})
    mid = agent._last_turn_inbound
    reference = agent.s.node(
        agent.s.node(mid)["attrs"]["communication_interpretation_id"]
    )["attrs"]
    assert reference["dispatch_path"] == "instruction"
    assert reference["language_referent_status"] == "unresolved"
    assert reference["cognitive_disposition"] == "repair"

    agent.converse(
        "Describe the object behind you.", speech_act="instruction",
        context={"literal_form": "imperative",
                 "evidence": ["explicit_uncertainty"]})
    mid = agent._last_turn_inbound
    unavailable_world = agent.s.node(
        agent.s.node(mid)["attrs"]["communication_interpretation_id"]
    )["attrs"]
    assert unavailable_world["dispatch_path"] == "honest_no_world"
    assert unavailable_world["language_world_support"] == "missing"
    assert unavailable_world["cognitive_disposition"] == "blocked"
