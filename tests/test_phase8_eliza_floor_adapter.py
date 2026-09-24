from __future__ import annotations

import json

from evaluation.comparative_release_gate import DIMENSIONS
from evaluation.conversational_manifold_phase0 import load_corpus
from evaluation.reference_adapters.eliza_floor import (
    ADAPTER_ENTRYPOINT,
    run_eliza_floor,
    scorecard,
)


def test_eliza_floor_emits_one_raw_deterministic_observation_per_case():
    report = run_eliza_floor(load_corpus())
    corpus = load_corpus()
    assert len(report["observations"]) == 74
    assert [item["case_id"] for item in report["observations"]] == [item["id"] for item in corpus["events"]]
    assert all(item["adapter_entrypoint"] == ADAPTER_ENTRYPOINT for item in report["observations"])
    assert all(item["raw_trace_complete"] for item in report["observations"])
    assert all(item["raw_trace"]["deterministic"] for item in report["observations"])
    assert all(item["output"].strip() for item in report["observations"])


def test_eliza_floor_does_not_read_annotations_or_claim_cognitive_labels():
    corpus = load_corpus()
    baseline = run_eliza_floor(corpus)
    for event in corpus["events"]:
        event["communicative_force"] = "request_action"
        event["expected_state"] = "act"
        event["grounding_status"] = "grounded"
    changed = run_eliza_floor(corpus)
    assert [item["output"] for item in baseline["observations"]] == [item["output"] for item in changed["observations"]]
    assert all(item["raw_trace"]["cognitive_labels"] is None for item in changed["observations"])


def test_eliza_floor_scores_only_protocol_supported_provenance():
    card = scorecard(run_eliza_floor(load_corpus())["observations"])
    assert card.validate() == []
    assert set(item.dimension for item in card.measurements) == set(DIMENSIONS)
    assert card.by_dimension()["provenance"].status == "measured"
    assert card.by_dimension()["provenance"].mean == 1.0
    assert all(
        card.by_dimension()[dimension].status == "unavailable"
        for dimension in DIMENSIONS if dimension != "provenance"
    )


def test_eliza_floor_report_keeps_other_baselines_unavailable_and_gate_blocked():
    report = run_eliza_floor(load_corpus())
    assert report["release_gate"]["status"] == "blocked"
    assert report["release_gate"]["empirically_complete"] is False
    assert set(report["other_baselines"]) == {"small_llm", "modern_llm", "base_human", "advanced_human"}
    assert all(
        measurement["status"] == "unavailable"
        for card in report["other_baselines"].values()
        for measurement in card["measurements"]
    )
    assert report["comparison_summary"]["target_status"] == "unavailable"
    assert report["comparison_summary"]["baselines"]["eliza_floor"]["comparison_status"] == "not_comparable"
    assert report["comparison_summary"]["baselines"]["small_llm"]["comparison_status"] == "unavailable"
    assert report["comparison_summary"]["baselines"]["small_llm"]["dimensions"] == {}


def test_eliza_floor_output_is_stable_for_representative_patterns():
    corpus = load_corpus()
    first = run_eliza_floor(corpus)
    second = run_eliza_floor(corpus)
    assert [item["output"] for item in first["observations"]] == [item["output"] for item in second["observations"]]
    assert first["observations"][0]["rule_id"] == "fallback"
    assert first["observations"][1]["rule_id"] == "question"
    assert first["observations"][6]["rule_id"] == "greeting"
