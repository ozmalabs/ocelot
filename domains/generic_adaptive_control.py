"""Generic deterministic adaptive-control coordinator.

This module composes the adapter-neutral control faculties in this package.  It
is intentionally not a vehicle controller: channel, axis, objective, program,
and safety names are supplied by the caller.  The coordinator owns the
ordering boundary between a slow decision loop and a fast action loop:

* chronological command/receipt samples update online effectiveness;
* caller-provided candidate programs are allocated against measured evidence;
* an accepted slow choice is queued for atomic adoption by the fast safety
  supervisor; and
* the safety-selected continuous command is converted to the caller's fixed
  command alphabet.

The coordinator has no random state and no wall-clock dependencies.  A
``CoordinatorSnapshot`` captures the composed state, allowing a branch or
replay to continue from exactly the same point.
"""

from __future__ import annotations

from dataclasses import dataclass
import copy
import hashlib
import json
from typing import Any, Callable, Generic, Iterable, Mapping, Protocol, TypeVar

from .control_effectiveness_identification import (
    ControlEffectivenessIdentifier,
    EffectivenessReceiptAdapter,
    IdentificationSample,
)
from .feasible_objective_allocator import (
    AllocationResult,
    ControllabilityEvidence,
    ControllabilityMeasure,
    ControlCandidate,
    FeasibleObjectiveAllocator,
)
from .temporal_command_encoder import (
    TemporalCommandEncoder,
    TemporalEncoderSnapshot,
)
from .two_timescale_safety_supervisor import (
    FastObservation,
    Program,
    PublicationReceipt,
    SafetySupervisor,
    SlowPublication,
    SupervisorDecision,
)


ReceiptT = TypeVar("ReceiptT")


class CandidateMarginAdapter(Protocol):
    """Translate a caller candidate into supervisor margin names.

    The adapter is the only bridge between candidate forecasts and safety
    constraints.  It prevents the coordinator from acquiring plant-specific
    semantics.  A simple adapter can return ``candidate.metrics`` when those
    metrics already use the supervisor's opaque constraint names.
    """

    def predicted_margins(self, candidate: ControlCandidate) -> Mapping[str, float]: ...


@dataclass(frozen=True)
class SlowChoice:
    """The complete, auditable result of one slow allocation attempt."""

    allocation: AllocationResult
    publication: SlowPublication | None
    publication_receipt: PublicationReceipt


@dataclass(frozen=True)
class CoordinatorStep:
    """One fast action decision and its alphabet-encoded output."""

    decision: SupervisorDecision
    commands: Mapping[str, float]


@dataclass(frozen=True)
class CoordinatorSnapshot:
    """Opaque-in-value, copy-safe state for deterministic branching/replay.

    The nested mappings contain implementation state from the three composed
    faculties.  They are deliberately kept as Python values because programs
    are opaque caller payloads and cannot in general be JSON encoded.  The
    snapshot is still detached from the live coordinator and can be persisted
    by a caller that has a serialization format for its program payloads.
    """

    identifier_state: Mapping[str, object]
    supervisor_state: Mapping[str, object]
    encoder_snapshot: TemporalEncoderSnapshot
    samples: tuple[IdentificationSample, ...]
    publication_counter: int

    def to_dict(self) -> dict[str, object]:
        """Return the scalar/replay portion in a JSON-friendly shape.

        Opaque program payloads are intentionally omitted; callers that need a
        byte stream should serialize ``snapshot()`` with their own payload
        codec rather than accidentally inventing domain semantics here.
        """

        return {
            "encoder": self.encoder_snapshot.to_dict(),
            "sample_ids": tuple(sample.sample_id for sample in self.samples),
            "publication_counter": self.publication_counter,
        }


def _digest(identity: str, version: int, base_version: int,
            predicted_margins: Mapping[str, float]) -> str:
    """Build a stable publication digest without hashing opaque payloads."""

    payload = {
        "base_version": base_version,
        "identity": identity,
        "predicted_margins": {
            str(name): float(predicted_margins[name])
            for name in sorted(predicted_margins)
        },
        "version": version,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                          allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class GenericAdaptiveControlCoordinator(Generic[ReceiptT]):
    """Compose generic identification, allocation, safety, and encoding.

    ``identifier``, ``allocator``, ``supervisor``, and ``encoder`` are owned by
    the coordinator after construction.  Callers may therefore use their
    public read-only results, but should mutate state through this boundary so
    the snapshot/replay stream remains complete.
    """

    def __init__(
        self,
        identifier: ControlEffectivenessIdentifier,
        allocator: FeasibleObjectiveAllocator,
        supervisor: SafetySupervisor,
        encoder: TemporalCommandEncoder,
        *,
        margin_adapter: CandidateMarginAdapter | Callable[[ControlCandidate], Mapping[str, float]] | None = None,
    ) -> None:
        if not isinstance(identifier, ControlEffectivenessIdentifier):
            raise TypeError("identifier must be ControlEffectivenessIdentifier")
        if not isinstance(allocator, FeasibleObjectiveAllocator):
            raise TypeError("allocator must be FeasibleObjectiveAllocator")
        if not isinstance(supervisor, SafetySupervisor):
            raise TypeError("supervisor must be SafetySupervisor")
        if not isinstance(encoder, TemporalCommandEncoder):
            raise TypeError("encoder must be TemporalCommandEncoder")
        self.identifier = identifier
        self.allocator = allocator
        self.supervisor = supervisor
        self.encoder = encoder
        self.margin_adapter = margin_adapter
        self._samples: list[IdentificationSample] = []
        self._publication_counter = 0

    @property
    def samples(self) -> tuple[IdentificationSample, ...]:
        """Chronological samples accepted by the identifier."""

        return tuple(copy.deepcopy(self._samples))

    def ingest_sample(self, sample: IdentificationSample) -> tuple[str, ...]:
        """Ingest one already-adapted chronological command/receipt delta."""

        updated = self.identifier.update(sample)
        self._samples.append(copy.deepcopy(sample))
        return updated

    def ingest_receipt(
        self,
        sample_id: int,
        receipt: ReceiptT,
        adapter: EffectivenessReceiptAdapter[ReceiptT],
        *,
        changed_axes: Iterable[str] | None = None,
    ) -> tuple[str, ...]:
        """Use a narrow receipt adapter, preserving the caller's sample order."""

        sample = IdentificationSample(
            sample_id=sample_id,
            command_values=copy.deepcopy(adapter.command_values(receipt)),
            observed_deltas=copy.deepcopy(adapter.observed_deltas(receipt)),
            changed_axes=None if changed_axes is None else tuple(changed_axes),
        )
        return self.ingest_sample(sample)

    def evidence(self) -> ControllabilityEvidence:
        """Convert estimates into allocator evidence, including rank quality.

        The estimate's maximum coefficient magnitude is a generic effectiveness
        value.  Confidence is deliberately discounted again when rank is
        deficient, so a partially identified axis cannot satisfy a caller's
        confidence floor merely because one direction happened to be measured.
        Axis names remain opaque and are passed through unchanged.
        """

        measurements: dict[str, ControllabilityMeasure] = {}
        width = len(self.identifier.effectors)
        for estimate in self.identifier.estimates():
            value = max((abs(coefficient) for coefficient in estimate.coefficients), default=0.0)
            rank_fraction = estimate.rank / width
            confidence = max(0.0, min(1.0, estimate.confidence * rank_fraction))
            measurements[estimate.axis] = ControllabilityMeasure(value, confidence)
        return ControllabilityEvidence(measurements)

    def _candidate_margins(self, candidate: ControlCandidate) -> Mapping[str, float]:
        adapter = self.margin_adapter
        if adapter is None:
            # This fallback is intentionally a structural convention only:
            # metrics use the same opaque names as supervisor constraints.
            names = self.supervisor.constraint_names
            return {name: candidate.metrics[name] for name in names}
        if callable(adapter):
            margins = adapter(candidate)
        else:
            margins = adapter.predicted_margins(candidate)
        return dict(margins)

    def allocate_and_publish(
        self,
        candidates: Iterable[ControlCandidate],
        *,
        published_action: int | None = None,
    ) -> SlowChoice:
        """Allocate a slow candidate and queue it for an atomic fast boundary.

        Infeasible allocator fallbacks are returned for auditability but are
        not marked validated, so the safety supervisor cannot adopt them.
        """

        allocation = self.allocator.allocate(tuple(candidates), self.evidence())
        selected = allocation.selected
        if published_action is None:
            published_action = max(0, self.supervisor.last_action)
        if isinstance(published_action, bool) or not isinstance(published_action, int) or published_action < 0:
            raise ValueError("published_action must be a non-negative integer")

        self._publication_counter += 1
        version = max(self._publication_counter, self.supervisor.active_version + 1)
        self._publication_counter = version
        predicted = dict(self._candidate_margins(selected))
        payload = selected.program
        program = payload if isinstance(payload, Program) else Program(selected.identity, copy.deepcopy(payload))
        publication = SlowPublication(
            publication_id=f"selection-{version}-{selected.identity}",
            version=version,
            base_version=self.supervisor.active_version,
            published_action=published_action,
            program=program,
            validated=allocation.feasible and not allocation.used_infeasible_fallback,
            validation_digest=_digest(selected.identity, version, self.supervisor.active_version, predicted),
            predicted_margins=predicted,
        )
        receipt = self.supervisor.submit(publication)
        if not receipt.accepted:
            # Preserve the exact publication in the audit result, even when a
            # caller attempted to publish from a stale fast-loop boundary.
            return SlowChoice(allocation, publication, receipt)
        return SlowChoice(allocation, publication, receipt)

    def fast_step(self, observation: FastObservation) -> CoordinatorStep:
        """Run the fast safety decision and encode its continuous payload."""

        decision = self.supervisor.step(observation)
        payload = decision.program.payload
        if not isinstance(payload, Mapping):
            raise TypeError("accepted program payload must map channel names to continuous requests")
        commands = self.encoder.encode(payload)
        return CoordinatorStep(decision=decision, commands=commands)

    # Descriptive aliases keep graph adapters free to use either the protocol
    # vocabulary (``select``/``step``) or the explicit loop vocabulary used by
    # this module, without introducing a second implementation path.
    select_and_publish = allocate_and_publish
    step = fast_step

    def snapshot(self) -> CoordinatorSnapshot:
        """Capture detached composed state for replay or branching."""

        return CoordinatorSnapshot(
            identifier_state=copy.deepcopy(self.identifier.__dict__),
            supervisor_state=copy.deepcopy(self.supervisor.__dict__),
            encoder_snapshot=self.encoder.snapshot(),
            samples=tuple(copy.deepcopy(self._samples)),
            publication_counter=self._publication_counter,
        )

    def restore(self, snapshot: CoordinatorSnapshot) -> None:
        """Restore a snapshot made by this coordinator configuration."""

        if not isinstance(snapshot, CoordinatorSnapshot):
            raise TypeError("snapshot must be CoordinatorSnapshot")
        if tuple(snapshot.identifier_state.get("effectors", ())) != self.identifier.effectors:
            raise ValueError("snapshot identifier effectors do not match")
        if tuple(snapshot.identifier_state.get("axes", ())) != self.identifier.axes:
            raise ValueError("snapshot identifier axes do not match")
        self.identifier.__dict__.clear()
        self.identifier.__dict__.update(copy.deepcopy(dict(snapshot.identifier_state)))
        self.supervisor.__dict__.clear()
        self.supervisor.__dict__.update(copy.deepcopy(dict(snapshot.supervisor_state)))
        self.encoder.restore(snapshot.encoder_snapshot)
        self._samples = list(copy.deepcopy(snapshot.samples))
        self._publication_counter = snapshot.publication_counter


__all__ = [
    "CandidateMarginAdapter",
    "CoordinatorSnapshot",
    "CoordinatorStep",
    "GenericAdaptiveControlCoordinator",
    "SlowChoice",
]
