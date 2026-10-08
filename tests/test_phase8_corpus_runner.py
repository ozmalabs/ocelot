from __future__ import annotations

from evaluation.comparative_release_gate import BASELINES, DIMENSIONS
from evaluation.conversational_manifold_phase0 import load_corpus, validate_corpus
from evaluation.phase8_corpus_runner import (
    PROTOCOL_ID,
    CONTEXT_AWARE_PROTOCOL_ID,
    _deliberation_readback,
    build_report_scaffold,
    grounding_precision_recall,
    production_release_summary,
    scorecard_to_dict,
    unrun_scorecard,
    run_system_under_test,
)
from evaluation.phase8_corpus_runner import _speech_act
from evaluation.phase8_corpus_runner import _observed_state
from evaluation.phase8_corpus_runner import _state_evidence_metadata
from evaluation.phase8_corpus_runner import _authoritative_state_match
from evaluation.phase8_corpus_runner import _measurement
from evaluation.phase8_corpus_runner import _runtime_context
from evaluation.phase8_corpus_runner import _interpretation_matches
from evaluation.phase8_corpus_runner import compound_communication_act_summary
from evaluation.reference_protocol import reference_run_scaffold, validate_reference_observations


def test_phase8_protocol_binds_the_fixed_phase0_corpus():
    corpus = load_corpus()
    assert validate_corpus(corpus) == []
    assert 60 <= len(corpus["events"]) <= 100
    assert PROTOCOL_ID == "phase8a-fixed-phase0-corpus-v4"


def test_corpus_transport_classifies_signal_not_reference_parse_label():
    assert _speech_act({"signal": "Read this.",
                        "literal_form": "declarative"}) == "request"
    assert _speech_act({"signal": "How does it work?",
                        "literal_form": "declarative"}) == "question"
    assert _speech_act({"signal": "The sensor is ready.",
                        "literal_form": "social"}) == "statement"
    assert _speech_act({"signal": "Yes, that is the one.",
                        "literal_form": "declarative"}) == "acknowledgment"
    assert _speech_act({"signal": "Yes, proceed.",
                        "literal_form": "social"}) == "request"
    assert _speech_act({"signal": "No, hold position.",
                        "literal_form": "declarative"}) == "refusal"
    assert _speech_act({"signal": "No, I may have misread it.",
                        "literal_form": "imperative"}) == "statement"


def test_runtime_context_excludes_corpus_evidence_annotations():
    event = {
        "event_mode": "turn_compatible",
        "interaction_relation": "standalone",
        "evidence": ["explicit_uncertainty", "explicit_failure"],
        "communicative_acts": [
            {"act_type": "greeting", "force": "social_action"},
            {"act_type": "polar_question", "force": "information_request"},
        ],
        "expected_released_semantic_events": ["greeting", "repair"],
    }
    assert _runtime_context(event) == {
        "interaction_mode": "turn_compatible",
        "interaction_relation": "standalone",
    }


def test_compound_communication_act_audit_scores_both_components():
    corpus = {"events": [{
        "id": "social_question",
        "communicative_acts": [
            {"act_type": "greeting", "force": "social_action"},
            {"act_type": "polar_question", "force": "information_request"},
        ],
        "expected_released_semantic_events": ["greeting", "repair"],
    }]}
    observation = {
        "cognitive_trace": {"communication_act_evidence": [
            {"attrs": {"act_type": "greeting",
                       "communicative_force": "social_action"}},
            {"attrs": {"act_type": "polar_question",
                       "communicative_force": "information_request"}},
        ]},
        "production_gate_receipts": [
            {"attrs": {"semantic_event": "greeting", "status": "released"}},
            {"attrs": {"semantic_event": "repair", "status": "released"}},
            {"attrs": {"semantic_event": "compound_greeting_repair",
                        "status": "released"}},
        ],
    }
    result = compound_communication_act_summary([observation], corpus)
    assert result["complete"] is True
    row = result["records"][0]
    assert row["act_evidence_exact_match"] is True
    assert row["response_components_complete"] is True

    observation["production_gate_receipts"].pop(1)
    incomplete = compound_communication_act_summary([observation], corpus)
    assert incomplete["complete"] is False
    assert incomplete["records"][0]["act_evidence_exact_match"] is True
    assert incomplete["records"][0]["response_components_complete"] is False


def test_interpretation_score_requires_all_annotated_acts_but_keeps_scalar_cases():
    event = {
        "communicative_force": "social_action",
        "communicative_acts": [
            {"act_type": "greeting", "force": "social_action"},
            {"act_type": "polar_question", "force": "information_request"},
        ],
    }
    observation = {
        # The legacy scalar projection alone must not erase the second true act.
        "observed_force": "social_action",
        "cognitive_trace": {"communication_act_evidence": [
            {"attrs": {"act_type": "greeting",
                       "communicative_force": "social_action"}},
            {"attrs": {"act_type": "polar_question",
                       "communicative_force": "information_request"}},
        ]},
    }
    assert _interpretation_matches(observation, event) is True
    observation["cognitive_trace"]["communication_act_evidence"].pop()
    assert _interpretation_matches(observation, event) is False
    assert _interpretation_matches(
        {"observed_force": "social_action"},
        {"communicative_force": "offer"},
    ) is True


def test_runtime_context_defaults_signal_only_events_to_turn_compatible():
    assert _runtime_context({"signal": "What is the moon?"}) == {
        "interaction_mode": "turn_compatible",
        "interaction_relation": None,
    }


def test_settled_nonturn_permission_block_closes_silently_after_native_work():
    corpus = load_corpus()
    events = corpus["events"]
    blocked_index = next(
        index for index, event in enumerate(events)
        if event["id"] == "blocked_permission")
    # This blocked disposition depends on preceding discourse; an isolated
    # question correctly remains an unresolved explicit error.
    result = run_system_under_test({
        **corpus, "events": events[:blocked_index + 1],
    })
    observation = next(
        row for row in result["observations"]
        if row["id"] == "blocked_permission")

    assert observation["observed_state"] == "blocked"
    assert observation["disposition_authoritative"] is True
    assert observation["interaction_mode"] == "non_turn"
    assert observation["reply"] == ""
    assert observation["production_gate_receipts"] == []
    summary = result["production_release_summary"]
    assert summary["silent_unclassified_count"] == 0
    assert summary["silent_no_reply_reason_counts"][
        "native_blocked_non_turn"] == 3


def test_anaphoric_polar_question_repairs_missing_relation_support():
    corpus = load_corpus()
    events = corpus["events"]
    question_index = next(
        index for index, event in enumerate(events)
        if event["id"] == "question_response")
    result = run_system_under_test({
        **corpus, "events": events[:question_index + 1],
    })
    observation = next(
        row for row in result["observations"]
        if row["id"] == "question_response")
    turn = observation["cognitive_trace"]["turn"]

    assert observation["cognitive_state"] == "repair"
    assert observation["cognitive_state_authority"] == "native_graph_readback"
    assert observation["reply"] != "The gate is open."
    assert "ground" in observation["reply"].lower()
    assert turn["answer_commitment"] is None
    assert observation["production_gate_receipts"][0]["attrs"][
        "semantic_event"] == "repair"


def test_anaphoric_polar_question_answers_from_accepted_proposition():
    from domains.proposition_commitment import bridge_proposition_evidence
    from substrate.boot_all import load_all_seeds
    from substrate.world_adapter import WorldAdapter

    corpus = load_corpus()
    events = corpus["events"]
    question_index = next(
        index for index, event in enumerate(events)
        if event["id"] == "question_response")
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    for event in events[:question_index]:
        for held in (event.get("setup") or {}).get("held_answers") or []:
            agent._persist_held_answer(
                str(held["topic"]), str(held["answer"]))
        agent.converse(
            event["signal"], speech_act=_speech_act(event),
            context=_runtime_context(event))

    provenance = bridge_proposition_evidence(agent, {
        "schema": "neutral_proposition_evidence.v1",
        "kind": "explicit_neutral",
        "predicate": "report",
        "arguments": {"subject": "sensor", "object": "gate"},
        "polarity": "affirmed",
        "provider": "phase8_synthetic_accepted_proposition",
        "evidence_id": "phase8-sensor-report-gate-affirmed",
        "commitment_status": "accepted",
    })
    assert provenance["supported"] is True

    event = events[question_index]
    reply = agent.converse(
        event["signal"], speech_act=_speech_act(event),
        context=_runtime_context(event))
    inbound = agent._last_turn_inbound
    inbound_attrs = agent.s.node(inbound)["attrs"]
    interpretation = inbound_attrs["communication_interpretation_id"]
    interpretation_attrs = agent.s.node(interpretation)["attrs"]
    assert reply == "Yes."
    assert interpretation_attrs["cognitive_disposition"] == "answer"
    assert interpretation_attrs["arbitration_basis"] == \
        "accepted_proposition_polar_answer"
    assert inbound_attrs["communication_route"] == \
        "polar_relation_answer_graph"
    assert agent.reply_turn_trace(agent.last_turn_inbound_id())[
        "answer_commitment"]["kind"] == "supported_event_bound_polar_answer"


def test_named_topic_polar_question_cannot_use_topic_only_held_answer():
    from substrate.boot_all import load_all_seeds
    from substrate.world_adapter import WorldAdapter

    corpus = load_corpus()
    events = corpus["events"]
    question_index = next(
        index for index, event in enumerate(events)
        if event["id"] == "question_response")
    agent = WorldAdapter(seeds=())
    load_all_seeds(agent)
    for event in events[:question_index]:
        for held in (event.get("setup") or {}).get("held_answers") or []:
            agent._persist_held_answer(
                str(held["topic"]), str(held["answer"]))
        agent.converse(
            event["signal"], speech_act=_speech_act(event),
            context=_runtime_context(event))

    reply = agent.converse(
        "Is the gate open?", speech_act="question",
        context={"interaction_mode": "turn_compatible",
                 "interaction_relation": "response"})
    inbound = agent._last_turn_inbound
    attrs = agent.s.node(inbound)["attrs"]
    interpretation = attrs["communication_interpretation_id"]
    i_attrs = agent.s.node(interpretation)["attrs"]

    assert reply != "The gate is open."
    assert i_attrs.get("relation_focus") == "polar"
    assert i_attrs.get("cognitive_disposition") == "repair"
    assert attrs.get("communication_route") == "ask_back"


def test_production_release_audit_requires_exact_receipt_for_substantive_reply():
    observations = [
        {"id": "released", "reply": "Answer.",
         "production_gate_receipts": [{"attrs": {
             "status": "released", "surface": "Answer."}}]},
        {"id": "missing", "reply": "Unreceipted answer.",
         "production_gate_receipts": []},
        {"id": "error", "reply": "ERROR: no communicative response could be generated.",
         "production_gate_receipts": [{"attrs": {
             "status": "withheld",
             "surface": "ERROR: no communicative response could be generated."}}]},
        {"id": "silent", "reply": "", "production_gate_receipts": []},
    ]
    result = production_release_summary(observations)
    assert result["substantive_reply_count"] == 2
    assert result["released_substantive_reply_count"] == 1
    assert result["unreleased_substantive_event_ids"] == ["missing"]
    assert result["explicit_error_reply_count"] == 1
    assert result["withheld_error_receipt_count"] == 1
    assert result["silent_event_count"] == 1
    assert result["silent_authorized_no_reply_count"] == 0
    assert result["silent_unclassified_count"] == 1
    assert result["substantive_release_coverage_complete"] is False


def test_production_release_summary_separates_graph_authorized_nonturn_silence():
    result = production_release_summary([
        {"id": "blocked_nonturn", "reply": "", "observed_state": "blocked",
         "disposition_authoritative": True, "interaction_mode": "non_turn"},
        {"id": "fragment_nonturn", "reply": "", "observed_state": "defer",
         "disposition_authoritative": True, "interaction_mode": "non_turn",
         "literal_form": "fragment"},
        {"id": "offer_nonturn", "reply": "", "observed_state": "defer",
         "disposition_authoritative": True, "interaction_mode": "non_turn",
         "evidence_communicative_act": "ability_action_offer"},
        {"id": "continuation_nonturn", "reply": "",
         "observed_state": "defer", "disposition_authoritative": True,
         "interaction_mode": "non_turn",
         "interaction_relation": "continuation"},
        {"id": "knowledge_deficit_repair_nonturn", "reply": "",
         "observed_state": "repair", "disposition_authoritative": True,
         "cognitive_arbitration_basis":
             "nonturn_knowledge_deficit_repair",
         "interaction_mode": "non_turn",
         "interaction_relation": "continuation",
         "reply_expectation": "not_expected"},
        {"id": "overlap_defer", "reply": "", "observed_state": "defer",
         "disposition_authoritative": True,
         "interaction_mode": "turn_compatible",
         "interaction_relation": "overlap", "literal_form": "fragment"},
        {"id": "continuation_defer", "reply": "", "observed_state": "defer",
         "disposition_authoritative": True,
         "interaction_mode": "turn_compatible",
         "interaction_relation": "continuation", "literal_form": "declarative"},
        # Similar surface silence without native-authoritative no-reply state
        # stays unclassified instead of being excused by transport metadata.
        {"id": "unknown", "reply": "", "observed_state": "defer",
         "disposition_authoritative": False, "interaction_mode": "non_turn",
         "literal_form": "fragment"},
    ])

    assert result["silent_event_count"] == 8
    assert result["silent_authorized_no_reply_count"] == 7
    assert result["silent_unclassified_count"] == 1
    assert result["silent_no_reply_reason_counts"] == {
        "native_blocked_non_turn": 1,
        "native_nonturn_continuation_defer": 1,
        "native_continuation_defer": 1,
        "native_fragment_defer_non_turn": 1,
        "native_incomplete_offer_defer_non_turn": 1,
        "native_overlap_fragment_defer": 1,
        "native_nonturn_knowledge_deficit_repair": 1,
    }


def test_production_release_summary_accepts_only_native_deferred_refusal_silence():
    result = production_release_summary([
        {"id": "typed_refusal_defer", "reply": "",
         "observed_force": "refusal", "observed_state": "defer",
         "disposition_authoritative": True,
         "interaction_mode": "turn_compatible",
         "reply_expectation": "not_expected"},
        # A corpus label, lack of reply, or missing expectation alone cannot
        # authorize silence.
        {"id": "label_only", "reply": "", "observed_force": "refusal",
         "observed_state": "defer", "disposition_authoritative": True,
         "interaction_mode": "turn_compatible",
         "reply_expectation": "expected"},
    ])

    assert result["silent_authorized_no_reply_count"] == 1
    assert result["silent_unclassified_count"] == 1
    assert result["silent_no_reply_reason_counts"] == {
        "native_typed_refusal_defer": 1,
    }


def test_unrun_baselines_are_explicitly_unavailable_not_zero_scores():
    for baseline in BASELINES:
        card = unrun_scorecard(baseline)
        assert card.validate() == []
        assert [m.status for m in card.measurements] == ["unavailable"] * len(DIMENSIONS)
        assert all(m.n == 0 for m in card.measurements)
        assert all("not run" in m.notes for m in card.measurements)
        assert scorecard_to_dict(card)["measurements"][0]["status"] == "unavailable"


def test_deliberation_readback_does_not_infer_candidates_from_missing_trace():
    empty = _deliberation_readback({})
    assert empty == {
        "trace_status": "unavailable",
        "deliberation_count": 0,
        "statuses": [],
        "candidate_sources": [],
        "candidate_count": 0,
        "selection_count": 0,
        "settlement_count": 0,
    }
    measured = _deliberation_readback({
        "deliberations": [{
            "status": "no_candidate",
            "candidate_source": "discourse_state",
            "candidates": [], "selections": [], "settlements": [],
        }]
    })
    assert measured["trace_status"] == "measured"
    assert measured["statuses"] == ["no_candidate"]
    assert measured["candidate_sources"] == ["discourse_state"]
    assert measured["candidate_count"] == 0

    graph_readback = _deliberation_readback({
        "deliberations": [{
            "attrs": {"status": "selected",
                      "candidate_source": "live_thought_manifold"},
            "candidates": [{"candidate_id": "source:grounded"}],
            "selections": [{"selected_candidate_id": "source:grounded"}],
            "settlements": [],
        }]
    })
    assert graph_readback["statuses"] == ["selected"]
    assert graph_readback["candidate_sources"] == ["live_thought_manifold"]
    assert graph_readback["candidate_count"] == 1
    assert graph_readback["selection_count"] == 1


def test_observed_state_reads_deferred_goal_lifecycle_before_instruction_route():
    attrs = {"communication_route": "goal_only", "comp_kind": "instruction"}
    assert _observed_state(attrs, "I took on the goal.", [{"status": "deferred"}]) == "defer"
    assert _observed_state(attrs, "I took on the goal.", [{"status": "active"}]) == "act"


def test_observed_state_preserves_cognitive_repair_under_failed_release():
    attrs = {"comp_kind": "question", "grounding_status": "unresolved"}
    assert _observed_state(
        attrs, "ERROR: no communicative response could be generated.", []) == "repair"


def test_observed_state_keeps_error_for_events_without_cognitive_state():
    assert _observed_state(
        {}, "ERROR: no communicative response could be generated.", []) == "error"
    assert _observed_state(
        {"comp_kind": "question", "grounding_status": "candidate_grounded"},
        "ERROR: no communicative response could be generated.", [],
    ) == "error"


def test_observed_state_distinguishes_blocked_world_from_repair_gap():
    attrs = {"language_world_support": "missing", "communication_route": "ask_back"}
    assert _observed_state(
        attrs, "ERROR: no communicative response could be generated.", []) == "blocked"
    assert _observed_state(
        {"grounding_status": "authority_missing", "comp_kind": "question"},
        "ERROR: no communicative response could be generated.", []) == "blocked"


def test_observed_state_keeps_unresolved_deictic_world_request_as_repair():
    attrs = {"dispatch_path": "honest_no_world", "anaphor": 1,
             "grounding_status": "unresolved"}
    assert _observed_state(attrs, "I took on the goal.", []) == "repair"


def test_observed_state_reads_native_cognitive_disposition_before_surface():
    assert _observed_state(
        {"cognitive_disposition": "defer"},
        "ERROR: no communicative response could be generated.", [],
    ) == "defer"
    assert _observed_state(
        {"cognitive_disposition": "repair",
         "language_world_support": "missing"},
        "ERROR: no communicative response could be generated.", [],
    ) == "repair"


def test_runtime_state_metadata_separates_graph_evidence_from_adapter_heuristic():
    graph = _state_evidence_metadata(
        {"communication_route": "goal_only"}, [{"status": "deferred"}])
    assert graph == {
        "source": "graph_resident_goal_lifecycle",
        "authority": "graph_readback",
        "available": True,
    }
    interpretation = _state_evidence_metadata(
        {"grounding_status": "candidate_grounded"}, [])
    assert interpretation["authority"] == "interpretation_readback_not_disposition"
    unrelated_goal = _state_evidence_metadata(
        {"grounding_status": "unresolved"},
        [{"kind": "answer_topic", "status": "active"}],
    )
    assert unrelated_goal["authority"] == "interpretation_readback_not_disposition"
    heuristic = _state_evidence_metadata({}, [])
    assert heuristic["authority"] == "adapter_only"
    assert heuristic["available"] is False
    native = _state_evidence_metadata(
        {"cognitive_disposition": "defer"}, [])
    assert native == {
        "source": "native_graph_cognitive_disposition",
        "authority": "native_graph_readback",
        "available": True,
    }


def test_runtime_state_metadata_accepts_only_event_bound_action_goal_or_repair_pair():
    action_goal = _state_evidence_metadata(
        {"communication_route": "goal_only"},
        [{"kind": "instruction", "status": "active", "event_bound": True}],
    )
    assert action_goal["authority"] == "graph_readback"
    assert action_goal["source"] == "graph_resident_event_bound_action_goal"

    clarification_pair = _state_evidence_metadata(
        {"communication_route": "ask_back"}, [],
        {"graph_linked_to_turn": True, "expects_response": True,
         "speech_acts": ["clarification"]},
    )
    assert clarification_pair["authority"] == "graph_readback"
    assert clarification_pair["source"] == "graph_resident_clarification_pair"

    unrelated_goal = _state_evidence_metadata(
        {"communication_route": "goal_only"},
        [{"kind": "instruction", "status": "active", "event_bound": False}],
    )
    assert unrelated_goal["authority"] == "interpretation_readback_not_disposition"
    unlinked_clarification = _state_evidence_metadata(
        {"communication_route": "ask_back"}, [],
        {"graph_linked_to_turn": False, "expects_response": True,
         "speech_acts": ["clarification"]},
    )
    assert unlinked_clarification["authority"] == "interpretation_readback_not_disposition"


def test_runtime_state_metadata_accepts_typed_event_bound_answer_commitments_only():
    grounded_topic_answer = _state_evidence_metadata(
        {"grounding_status": "supported"}, [], None,
        {"kind": "supported_event_bound_topic_answer",
         "graph_linked_to_turn": True},
    )
    assert grounded_topic_answer["authority"] == "graph_readback"
    assert grounded_topic_answer["source"] == "graph_resident_answer_commitment"

    linked_answer_message = _state_evidence_metadata(
        {"comp_kind": "question"}, [], None,
        {"kind": "linked_graph_answer_message",
         "graph_linked_to_turn": True, "surface_bound": True},
    )
    assert linked_answer_message["authority"] == "graph_readback"

    empty_answer_shell = _state_evidence_metadata(
        {"comp_kind": "question"}, [], None,
        {"kind": "linked_graph_answer_message",
         "graph_linked_to_turn": True, "surface_bound": False},
    )
    missing_surface_binding = _state_evidence_metadata(
        {"comp_kind": "question"}, [], None,
        {"kind": "linked_graph_answer_message",
         "graph_linked_to_turn": True},
    )
    assert empty_answer_shell["authority"] == "interpretation_readback_not_disposition"
    assert missing_surface_binding["authority"] == "interpretation_readback_not_disposition"

    # Receipt/label lookalikes cannot promote an event into answer authority.
    unlinked = _state_evidence_metadata(
        {"grounding_status": "supported"}, [], None,
        {"kind": "supported_event_bound_topic_answer",
         "graph_linked_to_turn": False},
    )
    unknown_kind = _state_evidence_metadata(
        {"grounding_status": "supported"}, [], None,
        {"kind": "release_receipt", "graph_linked_to_turn": True},
    )
    assert unlinked["authority"] == "interpretation_readback_not_disposition"
    assert unknown_kind["authority"] == "interpretation_readback_not_disposition"


def test_matching_interpretation_label_does_not_score_as_a_disposition_outcome():
    assert not _authoritative_state_match(
        "repair", "repair", "interpretation_readback_not_disposition")
    assert not _authoritative_state_match("repair", "repair", "adapter_only")
    assert _authoritative_state_match("repair", "repair", "graph_readback")
    assert _authoritative_state_match("defer", "defer", "native_graph_readback")
    assert not _authoritative_state_match("act", "repair", "graph_readback")


def test_empty_disposition_authority_coverage_is_unavailable_not_zero_score():
    metric = _measurement("repair", 0, 0, ("corpus://test",),
                          "authoritative_repair_match")
    assert metric.status == "unavailable"
    assert metric.n == 0
    assert "no observations with disposition-grade authority" in metric.notes


def test_report_scaffold_is_blocked_without_inventing_sut_or_baseline_scores():
    report = build_report_scaffold()
    assert report["corpus"]["event_count"] == len(load_corpus()["events"])
    assert report["system_under_test"]["status"] == "not_run"
    assert report["release_gate"]["status"] == "blocked"
    assert report["release_gate"]["empirically_complete"] is False
    assert all(
        measurement["status"] == "unavailable"
        for measurement in report["scorecard"]["measurements"]
    )
    assert report["comparison_summary"]["target_status"] == "unavailable"
    assert all(
        item["comparison_status"] == "unavailable"
        for item in report["comparison_summary"]["baselines"].values()
    )


def test_v5_target_scaffold_binds_every_scorecard_to_matched_input_profile():
    report = build_report_scaffold(protocol_id=CONTEXT_AWARE_PROTOCOL_ID)
    assert report["protocol_id"] == CONTEXT_AWARE_PROTOCOL_ID
    assert report["scorecard"]["protocol_id"] == CONTEXT_AWARE_PROTOCOL_ID
    assert all(card["protocol_id"] == CONTEXT_AWARE_PROTOCOL_ID
               for card in report["baseline_scorecards"].values())
    assert report["release_gate"]["status"] == "blocked"
    assert report["release_gate"]["empirically_complete"] is False


def test_target_scaffold_rejects_unknown_input_profile():
    import pytest
    with pytest.raises(ValueError, match="unsupported Phase 8 input protocol"):
        build_report_scaffold(protocol_id="invented-profile")


def test_phase8_sealed_conversation_seed_profile_is_explicit_and_annotation_free():
    event = next(item for item in load_corpus()["events"]
                 if item["id"] == "social_question")
    report = run_system_under_test(
        {"events": [event]},
        runtime_seed_profile="conversation_corpus_prepass",
    )
    sut = report["system_under_test"]
    summary = sut["runtime_seed_profile_summary"]
    assert sut["runtime_seed_profile"] == "conversation_corpus_prepass"
    assert summary["prepass_mode"] == \
        "sealed_corpus_lexical_candidate_closure"
    assert summary["lexical_candidate_count"] > 0
    assert summary["loaded_seed_count"] > 0
    assert summary["selection_complete"] is True
    assert summary["incremental_content_loading"] is False
    # Reference labels never enter runtime inputs; native act evidence is
    # measured independently from the fixture's multi-act annotation.
    assert report["compound_communication_act_summary"]["complete"] is True


def test_phase8_rejects_unknown_runtime_seed_profile():
    import pytest
    with pytest.raises(ValueError, match="unsupported Phase 8 runtime seed profile"):
        run_system_under_test({"events": []},
                              runtime_seed_profile="invented-profile")


def test_phase8_incremental_conversation_profile_reports_live_prepass():
    event = next(item for item in load_corpus()["events"]
                 if item["id"] == "social_question")
    report = run_system_under_test({"events": [event]})
    summary = report["system_under_test"]["runtime_seed_profile_summary"]
    assert summary["profile"] == "conversation_incremental"
    assert summary["prepass_mode"] == \
        "per_turn_incremental_lexical_candidates"
    assert summary["incremental_content_loading"] is True
    assert summary["selection_complete"] is True
    assert summary["loaded_seed_count"] >= summary["initial_loaded_seed_count"]
    assert sum(summary["prepass_status_counts"].values()) == 1


def test_phase8_report_writer_forwards_selected_runtime_seed_profile(
        tmp_path, monkeypatch):
    import json
    from evaluation import phase8_corpus_runner as runner

    calls = []

    def fake_run(corpus, *, protocol_id, runtime_seed_profile):
        calls.append((corpus, protocol_id, runtime_seed_profile))
        return {
            "corpus": {"event_count": len(corpus["events"])},
            "release_gate": {"status": "blocked"},
        }

    fixture = tmp_path / "phase0.json"
    fixture.write_text('{"events": []}\n', encoding="utf-8")
    monkeypatch.setattr(runner, "FIXTURE", fixture)
    monkeypatch.setattr(runner, "run_system_under_test", fake_run)
    corpus = {"events": [{"id": "one"}]}
    output = tmp_path / "report.json"

    report = runner.write_report(
        output, corpus, protocol_id=CONTEXT_AWARE_PROTOCOL_ID,
        runtime_seed_profile="conversation_corpus_prepass")

    assert calls == [(corpus, CONTEXT_AWARE_PROTOCOL_ID,
                      "conversation_corpus_prepass")]
    assert report["corpus"]["sha256"]
    assert json.loads(output.read_text(encoding="utf-8")) == report


def test_v5_target_run_uses_matched_context_eliza_raw_profile():
    from evaluation.phase8_corpus_runner import run_system_under_test

    report = run_system_under_test({"events": [{
        "id": "v5-profile-smoke", "signal": "Hello.",
        "literal_form": "social", "communicative_force": "greeting",
        "cognitive_goal": "coordinate_socially", "grounding_status": "grounded",
        "interaction_relation": "standalone", "event_mode": "turn_compatible",
        "expected_state": "defer", "evidence": ["addressee_model"],
    }]}, protocol_id=CONTEXT_AWARE_PROTOCOL_ID)
    assert report["protocol_id"] == CONTEXT_AWARE_PROTOCOL_ID
    assert report["system_under_test"]["input_profile"] == "event_context_v5_history8"
    assert report["system_under_test"]["memory_learning_comparable"] is False
    eliza = report["baseline_scorecards"]["eliza_floor"]
    assert eliza["protocol_id"] == CONTEXT_AWARE_PROTOCOL_ID
    assert eliza["collection_status"] == "measured"
    assert next(m for m in eliza["measurements"]
                if m["dimension"] == "provenance")["status"] == "measured"
    assert all(m["status"] == "unavailable" for m in eliza["measurements"]
               if m["dimension"] != "provenance")
    raw = report["comparison_summary"]["baselines"]["eliza_floor"]["raw_provenance"]
    assert raw["protocol_id"] == CONTEXT_AWARE_PROTOCOL_ID
    assert raw["input_profile"] == "event_context_v5_history8"
    assert raw["session_history_limit"] == 8
    assert raw["observation_count"] == raw["complete_observation_count"] == 1


def test_main_report_embeds_eliza_scorecard_and_raw_provenance_only():
    from evaluation.phase8_corpus_runner import run_system_under_test

    corpus = {"events": [
        {
            "id": "eliza-integration-1", "signal": "hello", "literal_form": "social",
            "communicative_force": "greeting", "cognitive_goal": "coordinate",
            "expected_state": "defer", "grounding_status": "unknown",
            "event_mode": "async",
        },
        {
            "id": "eliza-integration-2", "signal": "open the door", "literal_form": "imperative",
            "communicative_force": "request_action", "cognitive_goal": "act",
            "expected_state": "act", "grounding_status": "grounded",
            "event_mode": "streaming",
        },
        {
            "id": "eliza-integration-3", "signal": "what is unavailable?", "literal_form": "interrogative",
            "communicative_force": "question", "cognitive_goal": "repair",
            "expected_state": "repair", "grounding_status": "unknown",
            "event_mode": "async",
        },
    ]}
    report = run_system_under_test(corpus, runtime_seed_profile="full")

    eliza_scorecard = report["baseline_scorecards"]["eliza_floor"]
    eliza_summary = report["comparison_summary"]["baselines"]["eliza_floor"]
    dimensions = {item["dimension"]: item for item in eliza_scorecard["measurements"]}

    assert eliza_scorecard["collection_status"] == "measured"
    assert dimensions["provenance"]["status"] == "measured"
    assert dimensions["provenance"]["mean"] == 1.0
    assert all(
        dimensions[dimension]["status"] == "unavailable"
        for dimension in DIMENSIONS if dimension != "provenance"
    )
    assert eliza_summary["collection_status"] == "measured"
    assert eliza_summary["comparison_status"] == "measured"
    assert eliza_summary["dimensions"]["interpretation"] == "unavailable"
    assert eliza_summary["dimensions"]["provenance"] == "indeterminate"

    raw = eliza_summary["raw_provenance"]
    assert raw["adapter_entrypoint"] == "evaluation.reference_adapters.eliza_floor"
    assert raw["deterministic"] is True
    assert raw["observation_count"] == 3
    assert raw["complete_observation_count"] == 3
    assert raw["failure_count"] == 0
    assert [item["case_id"] for item in raw["observations"]] == [
        "eliza-integration-1", "eliza-integration-2", "eliza-integration-3"
    ]
    assert all(item["raw_trace_complete"] for item in raw["observations"])

    # The measured ELIZA floor does not make the whole release protocol
    # complete; the other baselines and unavailable target dimensions remain
    # governed by the existing gate.
    assert report["release_gate"]["status"] == "blocked"
    assert all(
        report["comparison_summary"]["baselines"][baseline]["collection_status"] == "unavailable"
        for baseline in ("small_llm", "modern_llm", "base_human", "advanced_human")
    )


def test_trace_dimensions_are_declared_for_the_full_corpus_observation_contract():
    corpus = load_corpus()
    required = {
        "interpretation", "grounding", "goal_lifecycle", "mention_referent",
        "self_concern", "parse_evidence", "reply_provenance",
        "selected_candidate",
    }
    # The live runner records one boolean per dimension for every event.  The
    # test is contract-level so it does not confuse a missing runtime trace
    # with a passing score; the report must make the gap inspectable.
    from evaluation.phase8_corpus_runner import run_system_under_test
    report = run_system_under_test(corpus, runtime_seed_profile="full")
    assert len(report["observations"]) == len(corpus["events"])
    for observation in report["observations"]:
        assert set(observation["trace_coverage"]) == required
        assert isinstance(observation["information_learning_requests"], list)
    weather = next(item for item in report["observations"]
                   if item["id"] == "question_weather")
    assert len(weather["information_learning_requests"]) == 1
    request = weather["information_learning_requests"][0]
    assert request["event_bound"] is True
    assert request["attrs"]["schema"] == "information_learning_request.v1"
    assert request["answer_authority"] == "none"
    uncertain = next(item for item in report["observations"]
                     if item["id"] == "learn_uncertain")
    assert len(uncertain["information_learning_requests"]) == 1
    uncertain_request = uncertain["information_learning_requests"][0]
    assert uncertain_request["event_bound"] is True
    assert uncertain_request["attrs"]["schema"] == \
        "information_learning_request.v1"
    assert uncertain_request["answer_authority"] == "none"
    assert report["information_learning_request_summary"] == {
        "request_count": 2,
        "event_bound_count": 2,
        "status_counts": {"requested": 2},
        "requests_with_answer_authority": 0,
        "execution_performed": False,
        "notes": "Typed requests are intent only; this report does not establish retrieval or answer authority.",
    }
    for event_id in ("question_unknown", "social_question"):
        item = next(row for row in report["observations"]
                    if row["id"] == event_id)
        assert item["information_learning_requests"] == []

    # The sealed connected profile is scored against the same 74-event
    # signal-only corpus. Profile-local graph IDs differ, but every field that
    # enters semantic outcome scoring and every receipt's semantic payload
    # must match full boot.
    sealed = run_system_under_test(
        corpus, runtime_seed_profile="conversation_corpus_prepass")
    assert sealed["system_under_test"]["runtime_seed_profile_summary"] == {
        "profile": "conversation_corpus_prepass",
        "prepass_mode": "sealed_corpus_lexical_candidate_closure",
        "lexical_candidate_count": 150,
        "loaded_seed_count": 96,
        "selection_complete": True,
        "incremental_content_loading": False,
    }
    assert sealed["disposition_authority_coverage"] == \
        report["disposition_authority_coverage"]
    assert sealed["grounding_evaluation"] == report["grounding_evaluation"]
    assert sealed["scorecard"] == report["scorecard"]
    assert sealed["phase4_partial_evidence_summary"] == \
        report["phase4_partial_evidence_summary"]
    assert sealed["production_release_summary"] == \
        report["production_release_summary"]
    assert sealed["compound_communication_act_summary"] == \
        report["compound_communication_act_summary"]
    semantic_fields = (
        "reply", "observed_state", "observed_force", "grounding_status",
        "grounding_evidence_path", "disposition_authoritative",
        "cognitive_state_authority", "release_status", "reply_expectation",
        "evidence_communicative_act", "observed_literal_form",
        "literal_form_source", "provenance_complete", "reply_present",
        "trace_coverage",
    )
    for full, connected in zip(report["observations"],
                               sealed["observations"]):
        assert tuple(full.get(key) for key in semantic_fields) == tuple(
            connected.get(key) for key in semantic_fields)

        def receipt_semantics(observation):
            rows = []
            for receipt in observation["production_gate_receipts"]:
                attrs = dict(receipt["attrs"])
                attrs.pop("turn_message_id", None)
                rows.append((receipt["type"], receipt["status"], attrs))
            return rows

        assert receipt_semantics(full) == receipt_semantics(connected)

    hybrid = run_system_under_test(
        corpus, runtime_seed_profile="conversation_hybrid_prepass")
    assert hybrid["system_under_test"][
        "runtime_seed_profile_summary"] == {
            "profile": "conversation_hybrid_prepass",
            "prepass_mode": "corpus_connected_prepass_with_live_fallback",
            "lexical_candidate_count": 150,
            "loaded_seed_count": 96,
            "selection_complete": True,
            "incremental_content_loading": True,
        }
    assert hybrid["disposition_authority_coverage"] == \
        report["disposition_authority_coverage"]
    assert hybrid["grounding_evaluation"] == report["grounding_evaluation"]
    assert hybrid["scorecard"] == report["scorecard"]
    assert hybrid["phase4_partial_evidence_summary"] == \
        report["phase4_partial_evidence_summary"]
    assert hybrid["production_release_summary"] == \
        report["production_release_summary"]
    assert hybrid["compound_communication_act_summary"] == \
        report["compound_communication_act_summary"]
    for full, prepassed in zip(report["observations"],
                               hybrid["observations"]):
        assert tuple(full.get(key) for key in semantic_fields) == tuple(
            prepassed.get(key) for key in semantic_fields)
        assert receipt_semantics(full) == receipt_semantics(prepassed)

    incremental = run_system_under_test(
        corpus, runtime_seed_profile="conversation_incremental")
    incremental_summary = incremental["system_under_test"][
        "runtime_seed_profile_summary"]
    assert incremental_summary["initial_loaded_seed_count"] == 74
    assert incremental_summary["loaded_seed_count"] == 96
    assert incremental_summary["incrementally_added_seed_count"] == 22
    assert incremental_summary["prepass_status_counts"] == {
        "loaded": 50, "already_available": 1, "unavailable": 23,
    }
    assert incremental["disposition_authority_coverage"] == \
        report["disposition_authority_coverage"]
    assert incremental["grounding_evaluation"] == report["grounding_evaluation"]
    assert incremental["scorecard"] == report["scorecard"]
    assert incremental["phase4_partial_evidence_summary"] == \
        report["phase4_partial_evidence_summary"]
    assert incremental["production_release_summary"] == \
        report["production_release_summary"]
    assert incremental["compound_communication_act_summary"] == \
        report["compound_communication_act_summary"]
    for full, online in zip(report["observations"],
                            incremental["observations"]):
        assert tuple(full.get(key) for key in semantic_fields) == tuple(
            online.get(key) for key in semantic_fields)
        assert receipt_semantics(full) == receipt_semantics(online)


def test_runner_observation_contract_separates_serialized_evidence_from_flags():
    from evaluation.phase8_corpus_runner import run_system_under_test

    report = run_system_under_test({"events": [{
        "id": "fragment-1", "signal": "hello", "literal_form": "fragment",
        "communicative_force": "greeting", "cognitive_goal": "coordinate",
        "expected_state": "defer", "grounding_status": "unknown",
        "event_mode": "async",
    }]})
    observation = report["observations"][0]
    # A corpus parse annotation is reference-only: the runner does not pass it
    # into runtime cognition. An unrecognized complete word is not a fragment.
    assert observation["observed_literal_form"] == ""
    assert observation["literal_form_source"] == ""
    assert "production_gate_receipts" in observation
    assert isinstance(observation["production_gate_receipts"], list)
    assert isinstance(observation["turn_elapsed_ms"], float)
    assert 0.0 <= observation["turn_elapsed_ms"] <= observation["elapsed_ms"]
    latency = report["system_under_test"]["turn_latency_ms"]
    assert latency["scope"] == "WorldAdapter.converse synchronous call only"
    assert latency["event_count"] == 1
    assert latency["post_turn_audit_included"] is False
    assert "trace_coverage" in observation
    assert observation.get("cognitive_trace", {}).get("source") == \
        "graph_resident_conversation"
    assert "trace_coverage" not in observation["cognitive_trace"]


def test_runner_derives_fragment_from_language_adapter_not_corpus_label():
    from evaluation.phase8_corpus_runner import run_system_under_test

    report = run_system_under_test({"events": [{
        "id": "adapter-fragment", "signal": "Please—",
        "literal_form": "declarative", "communicative_force": "repair",
        "cognitive_goal": "defer", "expected_state": "defer",
        "grounding_status": "partially_grounded", "event_mode": "non_turn",
        "interaction_relation": "continuation",
        "evidence": ["explicit_uncertainty", "discourse_state"],
    }]})
    observation = report["observations"][0]
    assert observation["observed_literal_form"] == "fragment"
    assert observation["literal_form_source"] == "language_adapter_terminal_gap"

    social = run_system_under_test({"events": [{
        "id": "social-fragment", "signal": "Thanks, I—",
        "literal_form": "declarative", "communicative_force": "social_action",
        "cognitive_goal": "defer", "expected_state": "defer",
        "grounding_status": "partially_grounded", "event_mode": "non_turn",
        "interaction_relation": "overlap",
        "evidence": ["explicit_uncertainty", "discourse_state"],
    }]})
    social_observation = social["observations"][0]
    assert social_observation["observed_literal_form"] == "fragment"
    assert social_observation["literal_form_source"] == \
        "language_adapter_continuation_boundary"


def test_grounding_measurement_counts_negative_cases():
    corpus = {"events": [
        {"grounding_status": "grounded"},
        {"grounding_status": "unknown"},
        {"grounding_status": "unavailable_world"},
        {"grounding_status": "partially_grounded"},
    ]}
    observations = [
        {"grounding_status": "grounded"},
        {"grounding_status": "grounded"},
        {"grounding_status": "unknown"},
        {"grounding_status": "unknown"},
    ]
    metrics = grounding_precision_recall(observations, corpus)
    assert metrics["true_positive"] == 1
    assert metrics["false_positive"] == 1
    assert metrics["false_negative"] == 1
    assert metrics["true_negative"] == 1
    assert metrics["precision"] == 0.5
    assert metrics["recall"] == 0.5


def test_reference_protocol_scaffolds_all_cases_without_a_fabricated_score():
    envelope = reference_run_scaffold("modern_llm")
    assert envelope["collection_status"] == "unavailable"
    assert len(envelope["case_ids"]) == 74
    assert envelope["observations"] == []
    assert all(item["status"] == "unavailable" for item in envelope["scorecard"]["measurements"])
    assert validate_reference_observations(envelope) == []


def test_reference_protocol_rejects_duplicate_or_unknown_cases():
    envelope = reference_run_scaffold("eliza_floor")
    envelope["observations"] = [{"case_id": envelope["case_ids"][0]}, {"case_id": "not-a-case"}, {"case_id": envelope["case_ids"][0]}]
    errors = validate_reference_observations(envelope)
    assert "duplicate case_id observations" in errors
    assert any("unknown case IDs" in error for error in errors)
