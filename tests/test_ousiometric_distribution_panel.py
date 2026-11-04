"""Sampling weights preserve event facts and expose rare adverse errors."""
from dataclasses import replace
import pytest

from evaluation.ousiometrics.distribution_panel import (
    present_regime, summarize_presentations, verified_receipt_row,
)
from evaluation.ousiometrics.worlds import FactorProfile, ToolInterventionWorld


def _receipts():
    rows = []
    for episode, seed, action, type_id, token_id, error in (
        ("e1", 281001, "apply_small", "tool-small", "common", False),
        ("e2", 281006, "apply_large", "tool-large", "common", False),
        ("e3", 281002, "apply_small", "rare-harm", "rare", True),
    ):
        world = ToolInterventionWorld(FactorProfile(.8, .8, 0.0, 0.0, 0.0),
                                      seed=seed, episode_id=episode,
                                      context_id=f"context-{episode}")
        receipt = world.apply_action(action)
        rows.append(verified_receipt_row(world, receipt, type_id=type_id,
                                         token_id=token_id,
                                         prediction_error=error))
    return rows


def _all_regimes():
    return [present_regime(_receipts(), "uniform_type"),
            present_regime(_receipts(), "measured_token_frequency",
                           token_frequency={"common": 20, "rare": 1}),
            present_regime(_receipts(), "shuffled_frequency", seed=19,
                           token_frequency={"common": 20, "rare": 1})]


def test_frequency_shift_preserves_world_dynamics():
    source = _receipts()
    views = _all_regimes()
    expected = {(row["event_id"], row["adverse"], row["prediction_error"])
                for row in source}
    assert all({(row.event_id, row.adverse, row.prediction_error) for row in view} == expected
               for view in views)
    assert all(len(view) == len(source) for view in views)
    assert len({tuple(row.presentation_weight for row in view) for view in views}) > 1


def test_replay_not_independent_support():
    duplicate = [*_receipts(), dict(_receipts()[0])]
    with pytest.raises(ValueError, match="replay"):
        present_regime(duplicate, "uniform_type")


def test_rare_adverse_errors_never_hidden_in_mean():
    summary = summarize_presentations(_all_regimes()[0])
    assert summary["event_error_rate"] == 1 / 3
    assert summary["adverse_event_count"] == 1
    assert summary["adverse_error_rate"] == 1.0
    assert summary["adverse_event_ids"] == [_receipts()[2]["event_id"]]


def test_type_and_token_statistics_separate():
    uniform, measured, _ = _all_regimes()
    uniform_stats, token_stats = summarize_presentations(uniform), summarize_presentations(measured)
    assert token_stats["unique_type_count"] == uniform_stats["unique_type_count"] == 3
    assert token_stats["unique_event_count"] == uniform_stats["unique_event_count"] == 3
    assert token_stats["type_weighted_error_rate"] == uniform_stats["type_weighted_error_rate"] == 1 / 3
    assert token_stats["token_weighted_error_rate"] == pytest.approx(1 / 21)
    assert token_stats["event_error_rate"] == 1 / 3
    assert token_stats["geometry"]["event_weighted_centroid"] == pytest.approx(
        token_stats["geometry"]["type_weighted_centroid"])
    assert token_stats["geometry"]["token_frequency_weighted_centroid"] != pytest.approx(
        token_stats["geometry"]["event_weighted_centroid"])


def test_verified_world_receipts_supply_immutable_event_facts():
    world = ToolInterventionWorld(FactorProfile(.8, 0.0, 0.0, 0.0, 0.0),
                                  seed=281001, episode_id="frozen-e1",
                                  context_id="frozen-context-e1")
    receipt = world.apply_action("apply_small")
    row = verified_receipt_row(world, receipt, type_id="tool-small",
                               token_id="common", prediction_error=False)
    assert row["event_id"] == receipt.event_id
    assert row["coordinates"] == receipt.raw_coordinates
    assert row["adverse"] == receipt.adverse_consequence
    with pytest.raises(ValueError, match="verified"):
        verified_receipt_row(world, replace(receipt, event_id="forged"), type_id="tool-small",
                             token_id="common", prediction_error=False)


def test_no_adverse_events_is_typed_unknown():
    rows = present_regime([dict(row, adverse=False) for row in _receipts()], "uniform_type")
    summary = summarize_presentations(rows)
    assert summary["adverse_status"] == "unknown_no_adverse_events"
    assert summary["adverse_error_rate"] is None
