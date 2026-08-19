"""Focused contract tests for the generic two-timescale safety boundary."""

from __future__ import annotations

import math

import pytest

from domains.two_timescale_safety_supervisor import (
    ConstraintSpec,
    FastObservation,
    Program,
    SafetySupervisor,
    SlowPublication,
)


CONSTRAINTS = (
    ConstraintSpec("separation", "avoid", minimum_margin=0.0, trigger_margin=1.0),
    ConstraintSpec("headroom", "envelope", minimum_margin=0.0, trigger_margin=0.5),
)


def observation(index: int, separation: float = 3.0, headroom: float = 3.0, *, projected=None):
    projected = {} if projected is None else projected
    return FastObservation(
        action_index=index,
        timestamp=100 + index,
        margins={"separation": separation, "headroom": headroom},
        projected_margins=projected,
    )


def publication(version=1, *, base=0, published=0, validated=True, digest="ok", predicted=None):
    return SlowPublication(
        publication_id=f"candidate-{version}",
        version=version,
        base_version=base,
        published_action=published,
        program=Program("candidate", {"version": version}),
        validated=validated,
        validation_digest=digest,
        predicted_margins=predicted or {"separation": 2.0, "headroom": 2.0},
    )


def supervisor(**kwargs):
    return SafetySupervisor(
        CONSTRAINTS,
        Program("safe", {"mode": "safe"}),
        reflex_program=Program("reflex", {"mode": "bounded-reflex"}),
        **kwargs,
    )


def test_unvalidated_stale_and_unsafe_publications_are_rejected_without_mutation():
    gate = supervisor()

    assert not gate.submit(publication(validated=False)).accepted
    assert not gate.submit(publication(digest=" ")).accepted
    assert not gate.submit(publication(predicted={"separation": 0.1, "headroom": 2.0})).accepted
    assert gate.active_version == 0
    assert gate.pending_publication is None

    assert gate.step(observation(0)).mode == "normal"
    assert not gate.submit(publication(version=1, base=99)).accepted
    assert not gate.submit(publication(version=1, published=99)).accepted
    assert gate.active_version == 0


def test_valid_publication_is_atomic_and_payload_isolated():
    gate = supervisor()
    receipt = gate.submit(publication())
    assert receipt.accepted
    assert gate.active_version == 0
    assert gate.pending_publication is not None

    first = gate.step(observation(0))
    assert first.mode == "normal"
    assert first.active_version == 1
    assert first.program == Program("candidate", {"version": 1})

    # Returned and submitted payloads cannot mutate the active copy.
    first.program.payload["version"] = 99
    assert gate.active_program.payload["version"] == 1

    # A publication based on the prior active version is now stale.
    assert not gate.submit(publication(version=2, base=0, published=0)).accepted


def test_projected_margin_triggers_fixed_length_reflex_and_then_recovers():
    gate = supervisor(reflex_action_limit=2)
    assert gate.step(observation(0)).mode == "normal"

    # Current margin remains comfortable; the declared projection is exhausted.
    triggered = gate.step(observation(1, projected={"separation": 0.25}))
    assert triggered.mode == "reflex"
    assert triggered.event is not None
    assert triggered.event.constraint == "separation"
    assert triggered.reflex_remaining == 1

    held = gate.step(observation(2, projected={"separation": 0.25}))
    assert held.mode == "reflex"
    assert held.event is None
    assert held.reflex_remaining == 0

    recovered = gate.step(observation(3))
    assert recovered.mode == "normal"
    assert gate.reflex_events == 1


def test_reflex_events_and_actions_are_bounded_by_action_counts():
    gate = supervisor(reflex_action_limit=2, max_reflex_events=1)
    gate.submit(publication())
    assert gate.step(observation(0)).mode == "normal"
    assert gate.step(observation(1, separation=0.1)).mode == "reflex"
    assert gate.step(observation(2, separation=0.1)).mode == "reflex"
    exhausted = gate.step(observation(3, separation=0.1))
    assert exhausted.mode == "hold"
    assert exhausted.program.name == "candidate"
    assert gate.reflex_events == 1


def test_rejected_observations_do_not_advance_action_or_use_wall_clock():
    gate = supervisor()
    assert gate.step(observation(0)).accepted
    duplicate = gate.step(observation(0))
    assert not duplicate.accepted
    assert duplicate.mode == "rejected"
    assert gate.last_action == 0

    old_timestamp = FastObservation(1, 99, {"separation": 3.0, "headroom": 3.0})
    stale = gate.step(old_timestamp)
    assert not stale.accepted
    assert "timestamp" in stale.reason
    assert gate.last_action == 0


def test_replay_of_same_stream_is_identical():
    stream = [
        observation(0),
        observation(1, projected={"headroom": 0.1}),
        observation(2, projected={"headroom": 0.1}),
        observation(3),
    ]

    def run():
        gate = supervisor(reflex_action_limit=2)
        gate.submit(publication())
        return [gate.step(sample) for sample in stream]

    left, right = run(), run()
    assert left == right


def test_constraint_and_observation_validation_is_finite_and_generic():
    with pytest.raises(ValueError):
        ConstraintSpec("bad", "other")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        FastObservation(0, 0, {"separation": math.inf, "headroom": 1.0})
    with pytest.raises(ValueError):
        SlowPublication("x", 1, 0, 0, Program("p", {}), True, "d", {"separation": math.nan})
