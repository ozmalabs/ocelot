"""Focused tests for the generic deterministic effectiveness faculty."""

from __future__ import annotations

import pytest

from domains.control_effectiveness_identification import (
    ControlEffectivenessIdentifier,
    EffectivenessReceiptAdapter,
    IdentificationConfiguration,
    IdentificationSample,
)


def _sample(sample_id, commands, observed, changed_axes=None):
    return IdentificationSample(sample_id, commands, observed, changed_axes)


def test_compound_commands_recover_effectiveness_in_configured_order():
    identifier = ControlEffectivenessIdentifier(
        ("left", "right"), ("roll", "yaw"),
        configuration=IdentificationConfiguration(prior_precision=1e-6),
    )
    rows = (
        ((1.0, 0.0), (2.0, -1.0)),
        ((0.0, 1.0), (-0.5, 3.0)),
        ((1.0, 1.0), (1.5, 2.0)),
        ((2.0, -1.0), (4.5, -5.0)),
    )
    for sample_id, ((left, right), (roll, yaw)) in enumerate(rows):
        identifier.update(_sample(sample_id, {"right": right, "left": left},
                                  {"yaw": yaw, "roll": roll}))
    roll = identifier.estimate("roll")
    yaw = identifier.estimate("yaw")
    assert roll.coefficient_map == pytest.approx({"left": 2.0, "right": -0.5})
    assert yaw.coefficient_map == pytest.approx({"left": -1.0, "right": 3.0})
    assert roll.identifiable and yaw.identifiable
    assert roll.rank == yaw.rank == 2
    assert roll.confidence > 0.5


def test_missing_or_unchanged_axes_are_not_updated_or_forgotten():
    identifier = ControlEffectivenessIdentifier(
        ("a", "b"), ("x", "y"),
        configuration=IdentificationConfiguration(forgetting_factor=0.5),
    )
    identifier.update(_sample(0, {"a": 1.0, "b": 0.0}, {"x": 2.0, "y": 4.0}))
    before_y = identifier.estimate("y")
    before_x = identifier.estimate("x")
    assert identifier.update(_sample(1, {"a": 0.0, "b": 1.0}, {"x": 3.0})) == ("x",)
    after_y = identifier.estimate("y")
    after_x = identifier.estimate("x")
    assert after_y == before_y
    assert after_x.observed_samples == before_x.observed_samples + 1
    assert after_x.coefficient_map != before_x.coefficient_map


def test_rank_deficiency_reports_deterministic_bounded_basis_probes():
    identifier = ControlEffectivenessIdentifier(
        ("a", "b", "c"), ("x",),
        configuration=IdentificationConfiguration(
            excitation_bounds={"a": 0.2, "b": 0.4, "c": 0.6}
        ),
    )
    identifier.update(_sample(0, {"a": 1.0, "b": 2.0, "c": 0.0}, {"x": 3.0}))
    need = identifier.excitation_needs("x")
    assert need is not None
    assert need.rank == 1
    assert need.missing_effectors == ("b", "c")
    assert need.candidate_commands == ((0.0, 0.4, 0.0), (0.0, 0.0, 0.6))
    assert all(abs(value) <= bound for candidate in need.candidate_commands
               for value, bound in zip(candidate, need.bounds))


def test_zero_command_receipt_does_not_create_information():
    identifier = ControlEffectivenessIdentifier(("a",), ("x",))
    assert identifier.update(_sample(0, {"a": 0.0}, {"x": 9.0})) == ("x",)
    estimate = identifier.estimate("x")
    assert estimate.observed_samples == 1
    assert estimate.informative_samples == 0
    assert estimate.rank == 0
    assert estimate.coefficients == (0.0,)


def test_sample_order_and_invalid_receipts_are_explicit():
    identifier = ControlEffectivenessIdentifier(("a",), ("x",))
    identifier.update(_sample(10, {"a": 1.0}, {"x": 2.0}))
    with pytest.raises(ValueError, match="increase strictly"):
        identifier.update(_sample(10, {"a": 1.0}, {"x": 2.0}))
    with pytest.raises(ValueError, match="unknown effector"):
        identifier.update(_sample(11, {"bad": 1.0}, {"x": 2.0}))


def test_receipt_adapter_is_narrow_and_axis_subset_is_preserved():
    class Receipt:
        commands = {"motor": 2.0}
        deltas = {"speed": 6.0}

    class Adapter:
        def command_values(self, receipt):
            return receipt.commands

        def observed_deltas(self, receipt):
            return receipt.deltas

    identifier = ControlEffectivenessIdentifier(("motor",), ("speed", "height"))
    adapter: EffectivenessReceiptAdapter[Receipt] = Adapter()
    assert identifier.update_from_receipt(0, Receipt(), adapter) == ("speed",)
    assert identifier.estimate("speed").observed_samples == 1
    assert identifier.estimate("height").observed_samples == 0


def test_replay_is_byte_stable_for_same_ordered_samples():
    samples = (
        _sample(0, {"b": 1.0, "a": -1.0}, {"x": 0.4}),
        _sample(1, {"a": 0.25, "b": 0.75}, {"x": 0.8}),
        _sample(2, {"a": 2.0, "b": -0.5}, {"x": -1.2}),
    )
    kwargs = dict(configuration=IdentificationConfiguration(forgetting_factor=0.93))
    left = ControlEffectivenessIdentifier(("a", "b"), ("x",), **kwargs)
    right = ControlEffectivenessIdentifier(("a", "b"), ("x",), **kwargs)
    for sample in samples:
        left.update(sample)
        right.update(sample)
    assert left.estimate("x") == right.estimate("x")
