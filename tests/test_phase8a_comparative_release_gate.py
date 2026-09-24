from __future__ import annotations

from evaluation.comparative_release_gate import (
    BASELINES,
    DIMENSIONS,
    TARGET,
    DimensionMeasurement,
    Scorecard,
    evaluate_release_gate,
    comparison_summary,
    protocol_contract,
    scorecard_from_dict,
)


def _card(system: str, *, mean: float = 0.8, spread: float = 0.02) -> Scorecard:
    return Scorecard(
        system=system,
        protocol_id="phase8a-fixed-corpus-v1",
        reference_class=system if system in BASELINES else "",
        measurements=tuple(
            DimensionMeasurement(
                dimension=dimension,
                mean=mean,
                n=20,
                ci95_low=max(0.0, mean - spread),
                ci95_high=min(1.0, mean + spread),
                evidence_refs=(f"fixture://phase8a/{system}/{dimension}",),
                raw_metric=f"{dimension}_normalized_score",
            )
            for dimension in DIMENSIONS
        ),
    )


def test_protocol_has_exact_baselines_and_fixed_cognition_dimensions():
    contract = protocol_contract()
    assert contract["schema"] == "comparative_cognition_evaluation.v1"
    assert [item["id"] for item in contract["baselines"]] == list(BASELINES)
    assert contract["dimensions"] == list(DIMENSIONS)
    assert contract["score_semantics"]["direction"] == "higher_is_better"
    assert contract["corpus_protocol"]["event_count"] == 74
    assert [item["id"] for item in contract["reference_protocols"]] == list(BASELINES)


def test_complete_scorecards_can_release_when_target_is_above_every_baseline():
    cards = [_card(TARGET, mean=0.9)] + [_card(baseline, mean=0.5) for baseline in BASELINES]
    result = evaluate_release_gate(cards)
    assert result["status"] == "ready"
    assert result["complete"] is True
    assert result["regressions"] == []
    assert all(
        result["comparisons"][baseline][dimension] == "above"
        for baseline in BASELINES
        for dimension in DIMENSIONS
    )


def test_gate_blocks_missing_evidence_and_does_not_invent_a_baseline_result():
    cards = [_card(TARGET), *[_card(baseline) for baseline in BASELINES[:-1]]]
    result = evaluate_release_gate(cards)
    assert result["status"] == "blocked"
    assert "missing scorecard: advanced_human" in result["errors"]
    assert result["next_bottleneck"] == "complete_missing_scorecard_or_evidence"


def test_overlapping_intervals_are_indeterminate_and_do_not_claim_superiority():
    cards = [_card(TARGET, mean=0.8, spread=0.1)] + [_card(baseline, mean=0.8, spread=0.1) for baseline in BASELINES]
    result = evaluate_release_gate(cards)
    assert result["status"] == "ready"
    assert result["comparisons"]["modern_llm"]["grounding"] == "indeterminate"
    assert result["next_bottleneck"] == "interpretation"


def test_scorecard_loader_preserves_evidence_and_rejects_incomplete_dimensions():
    card = scorecard_from_dict(
        {
            "system": "small_llm",
            "protocol_id": "phase8a-fixed-corpus-v1",
            "measurements": [
                {
                    "dimension": "interpretation",
                    "mean": 0.5,
                    "n": 3,
                    "ci95_low": 0.3,
                    "ci95_high": 0.7,
                    "evidence_refs": ["fixture://raw/1"],
                    "raw_metric": "annotator_agreement",
                }
            ],
        }
    )
    assert card.by_dimension()["interpretation"].evidence_refs == ("fixture://raw/1",)
    errors = card.validate()
    assert any("missing dimension grounding" in error for error in errors)


def test_comparison_summary_distinguishes_unavailable_from_zero_or_superiority():
    cards = [_card(TARGET), _card("eliza_floor")]
    summary = comparison_summary(cards)
    assert summary["target_status"] == "measured"
    assert summary["baselines"]["eliza_floor"]["comparison_status"] == "measured"
    assert summary["baselines"]["small_llm"]["comparison_status"] == "missing"
    assert summary["baselines"]["small_llm"]["dimensions"] == {}


def test_comparison_summary_marks_unavailable_reference_without_comparing_it():
    target = _card(TARGET)
    unavailable = Scorecard(
        system="small_llm", protocol_id="phase8a-fixed-corpus-v1",
        reference_class="small_llm", collection_status="unavailable",
        measurements=tuple(
            DimensionMeasurement(
                dimension=dimension, mean=0.0, n=0, ci95_low=0.0, ci95_high=0.0,
                evidence_refs=("fixture://unavailable",), raw_metric="",
                notes="Not collected.", status="unavailable",
            ) for dimension in DIMENSIONS
        ),
    )
    summary = comparison_summary([target, unavailable])
    item = summary["baselines"]["small_llm"]
    assert item["collection_status"] == "unavailable"
    assert item["comparison_status"] == "unavailable"
    assert item["dimensions"] == {}
