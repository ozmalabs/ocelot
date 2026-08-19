"""End-to-end contract tests for the generic adaptive coordinator."""

from __future__ import annotations

from domains.control_effectiveness_identification import (
    ControlEffectivenessIdentifier,
    IdentificationConfiguration,
    IdentificationSample,
)
from domains.feasible_objective_allocator import (
    ControlCandidate,
    DeclaredObjective,
    FeasibleObjectiveAllocator,
    ViabilityConstraint,
)
from domains.generic_adaptive_control import GenericAdaptiveControlCoordinator
from domains.temporal_command_encoder import TemporalCommandEncoder
from domains.two_timescale_safety_supervisor import (
    ConstraintSpec,
    FastObservation,
    Program,
    SafetySupervisor,
)


def _coordinator() -> GenericAdaptiveControlCoordinator:
    identifier = ControlEffectivenessIdentifier(
        ("channel_a", "channel_b"),
        ("response",),
        configuration=IdentificationConfiguration(
            forgetting_factor=0.9,
            prior_precision=1000.0,
        ),
    )
    allocator = FeasibleObjectiveAllocator(
        (DeclaredObjective("error", priority=0, direction="minimize"),),
        (ViabilityConstraint("margin", "margin", lower=1.0),),
        confidence_floor=0.4,
    )
    supervisor = SafetySupervisor(
        (ConstraintSpec("margin", "envelope", minimum_margin=0.0, trigger_margin=1.0),),
        Program("safe", {"channel_a": 0.0, "channel_b": 0.0}),
        reflex_program=Program("reflex", {"channel_a": -1.0, "channel_b": -1.0}),
        reflex_action_limit=1,
    )
    return GenericAdaptiveControlCoordinator(
        identifier,
        allocator,
        supervisor,
        TemporalCommandEncoder((-1.0, 0.0, 1.0), ("channel_a", "channel_b")),
    )


def _candidates() -> tuple[ControlCandidate, ...]:
    # The adaptive candidate is better but requires evidence.  The safe
    # candidate remains available while the response model is rank deficient.
    return (
        ControlCandidate(
            "safe-choice",
            {"response": 0.0},
            {"channel_a": 0.0, "channel_b": 0.0},
            {"margin": 2.0, "error": 1.0},
        ),
        ControlCandidate(
            "adaptive-choice",
            {"response": 1.0},
            {"channel_a": 0.7, "channel_b": 0.2},
            {"margin": 3.0, "error": 0.1},
            required_measurements=("response",),
        ),
    )


def test_changing_plant_adapts_program_but_safety_has_precedence():
    coordinator = _coordinator()
    candidates = _candidates()

    # No rank yet: confidence floor rejects the adaptive choice, so the
    # deterministic safe fallback is published.
    first = coordinator.allocate_and_publish(candidates, published_action=0)
    assert first.allocation.selected.identity == "safe-choice"
    assert first.allocation.feasible
    normal = coordinator.fast_step(FastObservation(0, 0, {"margin": 2.0}))
    assert normal.decision.mode == "normal"
    assert normal.decision.program.name == "safe-choice"

    # Two independent probes identify both command directions.  The receipts
    # are generated from a changed plant (the second direction reverses sign),
    # yet all outcomes remain deterministic and rank-aware.
    coordinator.ingest_sample(IdentificationSample(1, {"channel_a": 1.0, "channel_b": 0.0}, {"response": 2.0}))
    coordinator.ingest_sample(IdentificationSample(2, {"channel_a": 0.0, "channel_b": 1.0}, {"response": -1.0}))
    assert coordinator.identifier.estimate("response").rank == 2

    adapted = coordinator.allocate_and_publish(candidates, published_action=0)
    assert adapted.allocation.selected.identity == "adaptive-choice"
    assert adapted.publication_receipt.accepted
    adopted = coordinator.fast_step(FastObservation(1, 1, {"margin": 2.0}))
    assert adopted.decision.program.name == "adaptive-choice"
    assert adopted.commands == {"channel_a": 1.0, "channel_b": 0.0}

    # A safety projection overrides the accepted slow program atomically.  The
    # reflex command is encoded, and the adaptive program resumes afterwards.
    reflex = coordinator.fast_step(
        FastObservation(2, 2, {"margin": 2.0}, projected_margins={"margin": 0.5})
    )
    assert reflex.decision.mode == "reflex"
    assert reflex.decision.program.name == "reflex"
    assert reflex.commands == {"channel_a": -1.0, "channel_b": -1.0}


def test_snapshot_restore_replays_encoder_and_slow_fast_state():
    coordinator = _coordinator()
    coordinator.allocate_and_publish(_candidates(), published_action=0)
    coordinator.fast_step(FastObservation(0, 0, {"margin": 2.0}))
    coordinator.ingest_sample(IdentificationSample(1, {"channel_a": 1.0, "channel_b": 0.0}, {"response": 2.0}))
    snapshot = coordinator.snapshot()

    left = coordinator.fast_step(FastObservation(1, 1, {"margin": 2.0}))
    coordinator.restore(snapshot)
    right = coordinator.fast_step(FastObservation(1, 1, {"margin": 2.0}))
    assert left == right


def test_same_changing_plant_trace_is_reproducible():
    def run():
        coordinator = _coordinator()
        candidates = _candidates()
        before = coordinator.allocate_and_publish(candidates, published_action=0)
        first = coordinator.fast_step(FastObservation(0, 0, {"margin": 2.0}))
        coordinator.ingest_sample(IdentificationSample(1, {"channel_a": 1.0, "channel_b": 0.0}, {"response": 2.0}))
        coordinator.ingest_sample(IdentificationSample(2, {"channel_a": 0.0, "channel_b": 1.0}, {"response": -1.0}))
        after = coordinator.allocate_and_publish(candidates, published_action=0)
        second = coordinator.fast_step(FastObservation(1, 1, {"margin": 2.0}))
        return (
            before.allocation.selected.identity,
            first.commands,
            after.allocation.selected.identity,
            second.commands,
            coordinator.identifier.estimate("response"),
        )

    assert run() == run()
