"""Contract tests for the generic deterministic temporal command encoder."""

from __future__ import annotations

import pytest

from domains.temporal_command_encoder import TemporalCommandEncoder


def test_constant_fractional_request_has_bounded_error_and_correct_average():
    encoder = TemporalCommandEncoder((-1.0, 0.0, 1.0), ("channel",))
    commands = [encoder.encode({"channel": 0.25})["channel"] for _ in range(10_000)]

    assert set(commands) <= {-1.0, 0.0, 1.0}
    assert sum(commands) / len(commands) == pytest.approx(0.25, abs=1e-4)
    assert abs(encoder.residuals["channel"]) <= encoder.error_bound


def test_channels_are_independent_and_missing_requests_hold():
    encoder = TemporalCommandEncoder((0.0, 1.0), ("left", "right"))
    first = encoder.encode({"left": 0.25, "right": 0.75})
    left_only = encoder.encode({"left": 0.25})
    right_only = encoder.encode({"right": 0.75})

    other = TemporalCommandEncoder((0.0, 1.0), ("left", "right"))
    assert first == other.encode({"left": 0.25, "right": 0.75})
    assert left_only["left"] == other.encode({"left": 0.25})["left"]
    assert right_only["right"] == other.encode({"right": 0.75})["right"]


def test_saturation_never_emits_outside_alphabet():
    encoder = TemporalCommandEncoder((-1.0, 0.0, 1.0), ("x",))
    assert encoder.encode({"x": 100.0}) == {"x": 1.0}
    assert encoder.last_requests == {"x": 1.0}
    assert encoder.encode({"x": -100.0}) == {"x": -1.0}
    assert encoder.last_requests == {"x": -1.0}


def test_tie_break_is_declared():
    lower = TemporalCommandEncoder((0.0, 1.0), ("x",), tie_break="lower")
    upper = TemporalCommandEncoder((0.0, 1.0), ("x",), tie_break="upper")
    assert lower.encode({"x": 0.5}) == {"x": 0.0}
    assert upper.encode({"x": 0.5}) == {"x": 1.0}


def test_snapshot_restore_replays_exactly_and_reset_rewinds():
    encoder = TemporalCommandEncoder((-1.0, 0.0, 1.0), ("x", "y"), tie_break="upper")
    for request in ({"x": 0.2, "y": -0.7}, {"x": 0.8, "y": 0.1}):
        encoder.encode(request)
    snapshot = encoder.snapshot()
    expected = [encoder.encode({"x": 0.2, "y": 0.6}) for _ in range(20)]

    encoder.restore(snapshot.to_dict())
    assert [encoder.encode({"x": 0.2, "y": 0.6}) for _ in range(20)] == expected
    encoder.reset()
    assert encoder.step == 0
    assert encoder.residuals == {"x": 0.0, "y": 0.0}
    assert encoder.encode({"x": 0.2, "y": 0.6}) == {"x": 0.0, "y": 1.0}


def test_invalid_configuration_and_requests_are_rejected():
    with pytest.raises(ValueError):
        TemporalCommandEncoder((0.0,), ("x",))
    with pytest.raises(ValueError):
        TemporalCommandEncoder((0.0, 1.0), ("x",), tie_break="random")
    encoder = TemporalCommandEncoder((0.0, 1.0), ("x",))
    with pytest.raises(KeyError):
        encoder.encode({"z": 0.2})
    with pytest.raises(ValueError):
        encoder.encode({"x": float("nan")})
