from __future__ import annotations

from evaluation.comparative_release_gate import BASELINES, DIMENSIONS
from evaluation.conversational_manifold_phase0 import load_corpus, validate_corpus
from evaluation.phase8_corpus_runner import (
    PROTOCOL_ID,
    _deliberation_readback,
    build_report_scaffold,
    grounding_precision_recall,
    scorecard_to_dict,
    unrun_scorecard,
)
from evaluation.phase8_corpus_runner import _speech_act
from evaluation.phase8_corpus_runner import _observed_state
from evaluation.phase8_corpus_runner import _state_evidence_metadata
from evaluation.reference_protocol import reference_run_scaffold, validate_reference_observations


def test_phase8_protocol_binds_the_fixed_phase0_corpus():
    corpus = load_corpus()
    assert validate_corpus(corpus) == []
    assert 60 <= len(corpus["events"]) <= 100
    assert PROTOCOL_ID == "phase8a-fixed-phase0-corpus-v3"


def test_corpus_transport_preserves_imperative_force_for_cognition():
    assert _speech_act({"literal_form": "imperative"}) == "instruction"
    assert _speech_act({"literal_form": "compound_imperative"}) == "instruction"
    assert _speech_act({"literal_form": "declarative"}) == "statement"


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
    report = run_system_under_test(corpus)

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
    report = run_system_under_test(corpus)
    assert len(report["observations"]) == len(corpus["events"])
    for observation in report["observations"]:
        assert set(observation["trace_coverage"]) == required


def test_runner_observation_contract_separates_serialized_evidence_from_flags():
    from evaluation.phase8_corpus_runner import run_system_under_test

    report = run_system_under_test({"events": [{
        "id": "fragment-1", "signal": "hello", "literal_form": "fragment",
        "communicative_force": "greeting", "cognitive_goal": "coordinate",
        "expected_state": "defer", "grounding_status": "unknown",
        "event_mode": "async",
    }]})
    observation = report["observations"][0]
    assert "production_gate_receipts" in observation
    assert isinstance(observation["production_gate_receipts"], list)
    assert "trace_coverage" in observation
    assert observation.get("cognitive_trace", {}).get("source") == \
        "graph_resident_conversation"
    assert "trace_coverage" not in observation["cognitive_trace"]


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
