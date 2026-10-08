from __future__ import annotations

import json
from pathlib import Path

import pytest

pytest.importorskip("substrate_rs")

from domains.communication_evidence import from_semantic_frame
from domains.interrogative_reference import proform_placeholder
from substrate.boot_all import load_all_seeds
from substrate.world_adapter import WorldAdapter


FIXTURE = Path(__file__).resolve().parent / "fixtures" / "comprehension_divergence" / \
    "language_neutral_variation.json"


def test_spanish_and_japanese_interrogatives_share_neutral_proforms():
    # Closed-class language forms map to the same queried-role placeholders;
    # downstream cognition receives no language-specific surface vocabulary.
    assert proform_placeholder("qué", "es") == "?WHAT"
    assert proform_placeholder("どの", "ja") == "?WHAT"
    assert proform_placeholder("誰", "ja") == "?WHO"
    assert proform_placeholder("いつ", "ja") == "?WHEN"


def test_spanish_and_japanese_wh_nps_survive_grounded_tokenization():
    agent = WorldAdapter(seeds=())
    producer = agent._full_text_producer()
    assert producer is not None
    world = producer.world
    es_text = "¿Qué gato se sentó en la alfombra?"
    _, _, es_shape = world._identify(es_text, "es")
    es_frame = world._parse_with_grounded(es_text, "es", es_shape)
    assert es_frame.get("agent") == "?WHAT", es_frame
    assert es_frame.get("event") == "sit", es_frame
    assert es_frame.get("location") == "mat", es_frame

    text = "どの猫がマットの上に座った？"
    _, _, shape = world._identify(text, "ja")
    frame = world._parse_with_grounded(text, "ja", shape)
    assert frame.get("agent") == "?WHAT", frame
    assert frame.get("event") == "sit", frame
    assert frame.get("location") == "mat", frame


def test_grounded_temporal_selection_frames_reach_shared_native_history_selector():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    agent.converse("Good morning.", speech_act="greeting")
    history = agent.s.nodes("RuleFiringHistory")
    assert len(history) == 1
    prior = dict(agent.s.node(history[0])["attrs"])

    producer = agent._full_text_producer()
    assert producer is not None
    world = producer.world
    texts = {
        "es": "¿Qué regla se ejecutó por última vez?",
        "ja": "最後にどのルールが発火しましたか？",
    }

    for language, text in texts.items():
        world.install_conversation_selection_lexicon(language)
        _, _, shape = world._identify(text, language)
        frame = world._parse_with_grounded(text, language, shape)
        assert frame.get("event") == "fire", (language, frame)
        assert frame.get("temporal_order") == "last", (language, frame)
        assert frame.get("relation_scope") == "event_specific", (language, frame)
        assert frame.get("relation_focus") == "selection", (language, frame)
        assert frame.get("selection_target_kind") == "rule", (language, frame)

        result = agent.ingest_semantic_event(
            frame, provider=f"language_world:{language}",
            interaction_mode="turn_compatible")
        attrs = agent.s.node(result["interpretation_id"])["attrs"]
        assert attrs["cognitive_disposition"] == "answer", (language, attrs)
        assert attrs["arbitration_basis"] == "grounded_rule_firing_history"
        assert attrs["selected_rule_name"] == prior["last_rule_name"]


def test_non_english_semantic_frames_drive_the_same_arbitration_rules():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    assert payload["schema"] == "language_neutral_communication_variation.v1"
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)

    for event in payload["events"]:
        evidence = from_semantic_frame(
            event["semantic_frame"], provider=f"language_adapter:{event['language']}")
        interpretation = agent.s.add_node("CommunicationInterpretation", {
            "schema": "communication_interpretation.v1",
            **evidence,
            "communicative_force": None,
            "cognitive_goal": None,
        })
        agent.inner.add_edge_unchecked(agent.agent, "holds_interpretation", interpretation)
        agent.inner.run_rules()
        attrs = agent.s.node(interpretation)["attrs"]
        assert attrs["communicative_force"] == event["force"], event["text"]
        assert attrs["cognitive_goal"] == event["goal"], event["text"]


def test_live_language_world_frames_feed_neutral_arbitration():
    """Use the existing multilingual text-to-frame adapter, then cross the
    neutral evidence boundary before graph arbitration."""
    try:
        from domains.language_world import LanguageWorld, teacher_stub
    except ModuleNotFoundError as exc:
        pytest.skip(f"LanguageWorld dependency unavailable in local venv: {exc.name}")
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    tasks = [
        {"text": "¿Quién rompió el jarrón?", "language": "es",
         "expected_meaning": {"event": "break", "agent": "?WHO",
                               "patient": "vase", "tense": "past",
                               "speech_act": "question"}},
        {"text": "María ama a Juan.", "language": "es",
         "expected_meaning": {"event": "love", "agent": "Mary",
                               "patient": "John", "tense": "present"}},
        {"text": "誰が花瓶を割った？", "language": "ja",
         "expected_meaning": {"event": "break", "agent": "?WHO",
                               "patient": "vase", "tense": "past",
                               "speech_act": "question"}},
    ]
    world = LanguageWorld(agent.inner, tasks, teacher_stub)
    log = world.run()
    assert len(log) == 3

    for entry in log:
        frame = entry["frame"]
        result = agent.ingest_semantic_event(
            frame, provider=f"language_world:{entry['language']}")
        interpretation = result["interpretation_id"]
        attrs = agent.s.node(interpretation)["attrs"]
        expected_force = (
            "request_information"
            if frame.get("speech_act") == "question"
            else "assertion_or_correction")
        expected_goal = (
            "answer_or_learn"
            if frame.get("speech_act") == "question"
            else "update_common_ground")
        assert attrs["communicative_force"] == expected_force, entry["text"]
        assert attrs["cognitive_goal"] == expected_goal, entry["text"]
        assert attrs["evidence_provider"] == (
            f"language_world:{entry['language']}")
        assert attrs["discourse_event_id"] == result["discourse_event_id"]
        assert agent.inner.has_edge(
            result["discourse_event_id"], "has_interpretation", interpretation)


def test_live_text_ingress_records_script_language_without_claiming_meaning():
    agent = WorldAdapter(seeds=())
    examples = {
        "en": "Which rule fired last?",
        "es": "¿Qué regla se ejecutó por última vez?",
        "ja": "最後にどのルールが発火しましたか？",
    }
    for expected, text in examples.items():
        message = agent.receive_utterance(text, speech_act="question")
        attrs = agent.s.node(message)["attrs"]
        assert attrs["language"] == expected
        # Ingress language identification must not synthesize a parse or a
        # selected answer; those remain separate faculty/native decisions.
        assert attrs.get("communication_interpretation_id") is None
        assert attrs.get("comp_predicate") is None


def test_grounded_native_rule_identifier_roundtrips_as_one_lexeme():
    """Code-like IDs stay exact only when grounded in the active language."""
    agent = WorldAdapter(seeds=())
    producer = agent._full_text_producer()
    assert producer is not None
    world = producer.world
    selected = "test_native_rule_42"
    examples = {
        "en": f"{selected} broke the vase.",
        "es": f"{selected} rompió el jarrón.",
        "ja": f"{selected}が花瓶を割った。",
    }

    # A selected graph identifier is an opaque lexical identity. It is not
    # split into ordinary English words or inferred from its spelling.
    for language in examples:
        world._add_lex_entry(
            language, selected, selected,
            source="selected_graph_identifier")

    for language, text in examples.items():
        _, _, shape = world._identify(text, language)
        frame = world._parse_with_grounded(text, language, shape)
        assert frame.get("agent") == selected, (language, frame)

    # Without an exact language-local lexical binding, the same orthographic
    # token must not be promoted to the selected ID.
    unselected = "unselected_native_rule_43"
    _, _, shape = world._identify(f"{unselected} broke the vase.", "en")
    unknown_frame = world._parse_with_grounded(
        f"{unselected} broke the vase.", "en", shape)
    assert unknown_frame.get("agent") != unselected


def test_selected_identifier_answer_fragment_is_realized_and_gated_multilingually():
    agent = WorldAdapter(seeds=())
    producer = agent._full_text_producer()
    assert producer is not None
    selected = "test_native_rule_42"
    audience = {"id": "user", "observed": False, "known_concepts": []}

    for language in ("en", "es", "ja"):
        producer.world._add_lex_entry(
            language, selected, selected,
            source="selected_graph_identifier")
        surface = agent._realize_frame_reply(
            {"agent": selected, "intent": "inform",
             "answer_fragment": True}, audience, language=language)

        assert surface == selected + ("。" if language == "ja" else ".")
        trace = agent._last_frame_realization
        assert trace["result"]["produce"]["self_monitor"]["match"] is True
        assert trace["gate_attempts"][-1]["gate"]["recoverable"] is True
        assert trace["gate_attempts"][-1]["gate"]["coverage"] == 1.0
        assert trace["committed"] is not None

    # Cognition hands the same role-labelled frame to each language realizer.
    # Verify actual LanguageProduction output and its output-null semantic gate,
    # not just the multilingual input adapters above.
    neutral_reply = {
        "event": "break", "agent": "Mary", "patient": "vase",
        "tense": "past", "intent": "inform",
    }
    expected_surfaces = {
        "en": "Mary broke the vase.",
        "es": "María rompió el jarrón.",
        "ja": "メアリーが花瓶を割った。",
    }
    for language, expected_surface in expected_surfaces.items():
        surface = agent._realize_frame_reply(neutral_reply, language=language)
        assert surface == expected_surface, language
        attempts = agent._last_frame_realization["gate_attempts"]
        assert len(attempts) == 1, language
        gate = attempts[0]["gate"]
        assert gate["recoverable"] is True, language
        assert gate["coverage"] == 1.0, language
        assert set(gate["recovered"]) == set(gate["intended"]), language
        assert gate["committed"] is not None, language


def test_non_english_event_selection_uses_neutral_rule_target_and_graph_history():
    frames = [
        {"language": "es", "communicative_force": "repair_or_defer",
         "cognitive_goal": "clarify_or_defer", "relation_scope": "event_specific",
         "relation_focus": "selection", "selection_target_kind": "rule",
         "grounding_status": "unresolved"},
        {"language": "ja", "communicative_force": "repair_or_defer",
         "cognitive_goal": "clarify_or_defer", "relation_scope": "event_specific",
         "relation_focus": "selection", "selection_target_kind": "rule",
         "grounding_status": "unresolved"},
    ]

    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    agent.converse("Good morning.", speech_act="greeting")
    history = agent.s.nodes("RuleFiringHistory")
    assert len(history) == 1
    prior = dict(agent.s.node(history[0])["attrs"])

    for frame in frames:
        result = agent.ingest_semantic_event(
            frame, provider=f"language_adapter:{frame['language']}",
            interaction_mode="turn_compatible")
        attrs = agent.s.node(result["interpretation_id"])["attrs"]
        assert attrs["selection_target_kind"] == "rule"
        assert attrs["relation_focus"] == "selection"
        assert attrs["cognitive_disposition"] == "answer"
        assert attrs["arbitration_basis"] == "grounded_rule_firing_history"
        assert attrs["selected_rule_name"] == prior["last_rule_name"]
        evidence = agent.inner.neighbours(
            result["interpretation_id"],
            "has_rule_firing_answer_evidence")
        assert len(evidence) == 1
        assert agent.s.node(evidence[0])["attrs"]["source_message_id"] == \
            prior["last_inbound_message_id"]


def test_unbound_event_selection_without_history_still_repairs_natively():
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    frame = {
        "language": "es", "communicative_force": "repair_or_defer",
        "cognitive_goal": "clarify_or_defer", "relation_scope": "event_specific",
        "relation_focus": "selection", "selection_target_kind": "rule",
        "grounding_status": "unresolved",
    }
    result = agent.ingest_semantic_event(
        frame, provider="language_adapter:es",
        interaction_mode="turn_compatible")
    attrs = agent.s.node(result["interpretation_id"])["attrs"]
    assert attrs["cognitive_disposition"] == "repair"
    assert attrs["arbitration_basis"] == "missing_event_history_support"
    assert not list(agent.inner.neighbours(
        result["interpretation_id"], "has_rule_firing_answer_evidence"))


def test_selection_target_kind_is_validated_at_the_semantic_boundary():
    with pytest.raises(ValueError, match="selection_target_kind is unsupported"):
        from_semantic_frame({
            "communicative_force": "repair_or_defer",
            "relation_focus": "selection",
            "selection_target_kind": "alarm",
        }, provider="invalid_adapter")
