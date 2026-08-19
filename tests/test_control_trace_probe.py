"""Deterministic, controller-independent tests for the flicker reducer."""
from __future__ import annotations

from substrate.control_trace_probe import reduce_trace


def test_reduces_ordinal_flicker_and_same_action_selection_switches():
    records = [
        {
            "action": 10,
            "instantaneous_surprise_ordinal": 0.0,
            "confirmed_regime_ordinal": 0.0,
            "condensed": False,
            "selected_model_id": "nominal:m0",
            "selected_program_members": ["elevator"],
        },
        {
            "action": 11,
            "instantaneous_surprise_ordinal": 1.0,
            "confirmed_regime_ordinal": 0.0,
            "condensed": False,
            "selected_model_id": "nominal:m0",
            "selected_program_members": ["elevator"],
        },
        {
            "action": 12,
            "instantaneous_surprise_ordinal": 0.0,
            "confirmed_regime_ordinal": 1.0,
            "condensed": True,
            "selected_model_id": "jam:m1",
            "selected_program_members": ["aileron", "elevator"],
        },
        {
            "action": 13,
            "instantaneous_surprise_ordinal": 0.0,
            "confirmed_regime_ordinal": 1.0,
            "condensed": True,
            "selected_model_id": "jam:m1",
            "selected_program_members": ["aileron", "elevator"],
        },
        {
            "action": 14,
            "instantaneous_surprise_ordinal": 2.0,
            "confirmed_regime_ordinal": 2.0,
            "condensed": False,
            "selected_model_id": "jam:m2",
            "selected_program_members": ["aileron", "elevator"],
        },
    ]

    metrics = reduce_trace(records)

    assert metrics.actions == 5
    assert metrics.ordinal_transition_actions == (1, 2, 4)
    assert metrics.confirmed_transition_actions == (2, 4)
    assert metrics.condensed_transition_actions == (2, 4)
    assert metrics.model_selection_transition_actions == (2, 4)
    assert metrics.program_selection_transition_actions == (2,)
    assert metrics.ordinal_transitions_per_action == 3 / 5
    assert metrics.model_selection_transitions_per_action == 2 / 5
    assert metrics.ordinal_confirmed_coincident == 2
    assert metrics.ordinal_condensed_coincident == 2
    assert metrics.ordinal_model_coincident == 2
    assert metrics.ordinal_program_coincident == 1
    assert metrics.ordinal_to_confirmed_lags == (0, 0)
    assert metrics.ordinal_to_condensed_lags == (0, 0)
    assert metrics.ordinal_to_model_lags == (0, 0)
    assert metrics.ordinal_to_program_lags == (0,)
    assert metrics.as_dict()["ordinal_to_model_lag_histogram"] == {"0": 2}


def test_reports_selection_lag_and_does_not_treat_missing_samples_as_flicker():
    records = [
        {"surprise_ordinal": 3, "selected_model": "a"},
        # The ordinal is not published on this action; it is not a transition.
        {"selected_model": "a"},
        {"surprise_ordinal": 4, "selected_model": "b"},
        {"surprise_ordinal": 4, "selected_model": "c"},
    ]
    metrics = reduce_trace(records)

    assert metrics.ordinal_transition_actions == (2,)
    assert metrics.model_selection_transition_actions == (2, 3)
    assert metrics.ordinal_to_model_lags == (0, 1)
    assert metrics.ordinal_model_coincident == 1
    assert metrics.mean_ordinal_to_model_lag == 0.5
    assert metrics.ordinal_to_model_lag_histogram == {"0": 1, "1": 1}
    assert "confirmed ordinal" in metrics.missing_fields
    assert "condensed" in metrics.missing_fields
    assert "program selection" in metrics.missing_fields


def test_explicit_fields_make_the_probe_generic_and_identity_is_canonical():
    records = [
        {"shock": 0, "stable": "base", "chosen": {"b": 2, "a": 1}},
        {"shock": 1.0, "stable": "base", "chosen": {"a": 1, "b": 2}},
        {"shock": 1, "stable": "fault", "chosen": {"a": 1, "b": 3}},
    ]
    metrics = reduce_trace(
        records,
        instantaneous_ordinal_field="shock",
        confirmed_ordinal_field="stable",
        model_field="chosen",
        condensed_field=("never_declared",),
        program_field=("never_declared",),
    )

    assert metrics.ordinal_transition_actions == (1,)
    assert metrics.confirmed_transition_actions == (2,)
    assert metrics.model_selection_transition_actions == (2,)
    assert metrics.ordinal_to_confirmed_lags == (1,)
    assert metrics.ordinal_to_model_lags == (1,)
    assert metrics.condensed_transitions == 0
    assert metrics.program_selection_transitions == 0
    # Dict key order is not a controller event and must not create a switch.
    assert records[0]["chosen"] == {"b": 2, "a": 1}


def test_metrics_json_is_stable_for_the_same_records():
    records = [
        {"surprise_ordinal": 0, "selected_program": ["a", "b"]},
        {"surprise_ordinal": 1, "selected_program": ["b", "a"]},
    ]
    first = reduce_trace(records).to_json()
    second = reduce_trace(tuple(records)).to_json()
    assert first == second
