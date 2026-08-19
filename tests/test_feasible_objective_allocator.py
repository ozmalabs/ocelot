"""Pure deterministic tests for the generic feasible-objective boundary."""
from __future__ import annotations

import pytest

from domains.feasible_objective_allocator import (
    ControllabilityEvidence,
    ControllabilityMeasure,
    ControlCandidate,
    DeclaredObjective,
    FeasibleObjectiveAllocator,
    ViabilityConstraint,
)


def evidence(**values: tuple[float, float]) -> ControllabilityEvidence:
    return ControllabilityEvidence({
        name: ControllabilityMeasure(value, confidence)
        for name, (value, confidence) in values.items()
    })


def candidate(identity: str, *, metrics: dict[str, float], program=None, **kwargs):
    return ControlCandidate(identity, {"state": 0.0}, program=program, metrics=metrics, **kwargs)


def test_hard_viability_is_lexicographically_before_tracking():
    allocator = FeasibleObjectiveAllocator(
        objectives=(
            # Caller-declared names and tiers are deliberately generic.
            DeclaredObjective("tracking_error", priority=2),
            DeclaredObjective("reserve", priority=1, direction="maximize"),
        ),
        constraints=(ViabilityConstraint("safe_margin", "safe_margin", lower=0.0),),
    )
    result = allocator.allocate((
        candidate("unsafe-perfect", metrics={"safe_margin": -1.0, "reserve": 9.0, "tracking_error": 0.0}),
        candidate("safe-good", metrics={"safe_margin": 0.1, "reserve": 2.0, "tracking_error": 2.0}),
    ), evidence())
    assert result.selected.identity == "safe-good"
    assert result.feasible
    assert not result.used_infeasible_fallback


def test_safety_margin_is_preferred_before_lower_priority_tracking():
    allocator = FeasibleObjectiveAllocator(
        (DeclaredObjective("tracking", priority=2),),
        (ViabilityConstraint("margin", "margin", lower=0.0),),
    )
    result = allocator.allocate((
        candidate("close", metrics={"margin": 0.1, "tracking": 0.0}),
        candidate("buffered", metrics={"margin": 4.0, "tracking": 100.0}),
    ), evidence())
    assert result.selected.identity == "buffered"
    assert result.assessment.safety_margins == (4.0,)


def test_controllability_source_uses_measured_effectiveness_and_confidence():
    allocator = FeasibleObjectiveAllocator((
        DeclaredObjective(
            "authority", priority=1, direction="maximize",
            source="controllability", metric="channel_a",
        ),
        DeclaredObjective("tracking", priority=2),
    ))
    result = allocator.allocate((
        candidate(
            "well-measured", metrics={"tracking": 3.0},
            controllability={"channel_a": 1.0}, required_measurements=("channel_a",),
        ),
        candidate(
            "uncertain", metrics={"tracking": 0.0},
            controllability={"channel_a": 1.5}, required_measurements=("channel_a",),
        ),
    ), evidence(channel_a=(1.0, 0.8)))
    # 1.0 * 1.0 * .8 beats 1.5 * 1.0 * .8 only if the first channel value is
    # actually lower?  The second is intentionally stronger and should win.
    assert result.selected.identity == "uncertain"
    assert result.assessment.objective_values[0] == pytest.approx(-1.2)


def test_confidence_floor_is_a_controllability_gate_before_tracking():
    allocator = FeasibleObjectiveAllocator(
        (DeclaredObjective("tracking", priority=2),), confidence_floor=0.75
    )
    result = allocator.allocate((
        candidate("low-confidence", metrics={"tracking": 0.0}, required_measurements=("a",)),
        candidate("confirmed", metrics={"tracking": 5.0}, required_measurements=("b",)),
    ), evidence(a=(1.0, 0.2), b=(1.0, 0.9)))
    assert result.selected.identity == "confirmed"
    assert result.assessment.confidence_deficits == (0.0,)


def test_variation_objective_is_generic_and_program_order_is_canonical():
    allocator = FeasibleObjectiveAllocator((
        DeclaredObjective("smoothness", priority=1, source="variation"),
    ))
    result = allocator.allocate((
        ControlCandidate(
            "jittery", {"state": 0.0},
            program=({"right": 0.0, "left": 0.0}, {"left": 1.0, "right": -1.0}),
        ),
        ControlCandidate(
            "smooth", {"state": 0.0},
            program=({"left": 0.0, "right": 0.0}, {"right": 0.1, "left": 0.1}),
        ),
    ), evidence())
    assert result.selected.identity == "smooth"


def test_candidate_identity_is_final_tie_break_and_input_order_does_not_matter():
    allocator = FeasibleObjectiveAllocator((DeclaredObjective("cost", priority=1),))
    rows = (
        candidate("zeta", metrics={"cost": 1.0}),
        candidate("alpha", metrics={"cost": 1.0}),
    )
    first = allocator.allocate(rows, evidence())
    second = allocator.allocate(reversed(rows), evidence())
    assert first.selected.identity == second.selected.identity == "alpha"
    assert [item.candidate.identity for item in first.ranked] == ["alpha", "zeta"]


def test_no_feasible_candidate_returns_least_violating_fallback_or_strict_error():
    constraint = ViabilityConstraint("margin", "margin", lower=0.0)
    candidates = (
        candidate("slightly", metrics={"margin": -0.1, "cost": 0.0}),
        candidate("badly", metrics={"margin": -2.0, "cost": -100.0}),
    )
    result = FeasibleObjectiveAllocator((DeclaredObjective("cost", priority=1),), (constraint,)).allocate(
        candidates, evidence()
    )
    assert result.selected.identity == "slightly"
    assert result.used_infeasible_fallback
    assert not result.feasible
    with pytest.raises(ValueError, match="no feasible candidate"):
        FeasibleObjectiveAllocator(
            (DeclaredObjective("cost", priority=1),), (constraint,), strict=True
        ).allocate(candidates, evidence())


def test_constraints_and_objectives_reject_missing_forecast_values():
    allocator = FeasibleObjectiveAllocator(
        (DeclaredObjective("track", priority=1),),
        (ViabilityConstraint("margin", "margin", lower=0.0),),
    )
    with pytest.raises(ValueError, match="missing constraint metric"):
        allocator.allocate((candidate("incomplete", metrics={"track": 1.0}),), evidence())
