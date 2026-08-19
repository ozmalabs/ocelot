"""Generic deterministic two-timescale safety/reflex supervisor.

The supervisor is an adapter-neutral boundary between a fast action loop and a
slower model/program publisher.  It deliberately knows nothing about a plant,
actuator names, failure modes, or vehicle axes.  A caller supplies:

* timestamped :class:`FastObservation` values and declared margin constraints;
* a last-known-safe :class:`Program`; and
* optionally, validated/versioned :class:`SlowPublication` values.

Slow publications are *proposals*, never an implicit authority.  They are
validated against the declared constraints and active program version, then
adopted only at the next accepted fast-loop boundary.  Safety decisions use
integer action indices and a bounded reflex budget; no wall clock is consulted.
This makes a stream of observations and publications replayable by another
runtime or a test harness.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import copy
import math
from typing import Any, Literal, Mapping


ConstraintKind = Literal["avoid", "envelope"]


def _finite(value: object, field_name: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{field_name} must be finite, not bool")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field_name} must be finite") from exc
    if not math.isfinite(result):
        raise ValueError(f"{field_name} must be finite")
    return result


def _name(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


@dataclass(frozen=True)
class ConstraintSpec:
    """A named, generic safety margin.

    ``minimum_margin`` is the hard boundary.  ``trigger_margin`` may be set
    above it to trigger a reflex before the hard boundary is reached.  The
    ``kind`` is descriptive and allows callers to distinguish an avoid
    distance from an envelope headroom without making the supervisor plant-
    specific.
    """

    name: str
    kind: ConstraintKind
    minimum_margin: float = 0.0
    trigger_margin: float | None = None

    def __post_init__(self) -> None:
        _name(self.name, "constraint name")
        if self.kind not in ("avoid", "envelope"):
            raise ValueError("constraint kind must be 'avoid' or 'envelope'")
        minimum = _finite(self.minimum_margin, "minimum_margin")
        trigger = minimum if self.trigger_margin is None else _finite(
            self.trigger_margin, "trigger_margin"
        )
        if trigger < minimum:
            raise ValueError("trigger_margin must be >= minimum_margin")
        object.__setattr__(self, "minimum_margin", minimum)
        object.__setattr__(self, "trigger_margin", trigger)


@dataclass(frozen=True)
class Program:
    """Opaque command/program data owned by the caller.

    The supervisor deep-copies this payload at ingress and egress so a caller
    cannot mutate an active program after it has been adopted.
    """

    name: str
    payload: Any

    def __post_init__(self) -> None:
        _name(self.name, "program name")


@dataclass(frozen=True)
class FastObservation:
    """One fast-loop sample, ordered by deterministic action count."""

    action_index: int
    timestamp: int
    margins: Mapping[str, float]
    projected_margins: Mapping[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if isinstance(self.action_index, bool) or not isinstance(self.action_index, int):
            raise ValueError("action_index must be an integer")
        if self.action_index < 0:
            raise ValueError("action_index must be non-negative")
        if isinstance(self.timestamp, bool) or not isinstance(self.timestamp, int):
            raise ValueError("timestamp must be an integer")
        for name, value in self.margins.items():
            _name(name, "margin name")
            _finite(value, f"margin {name!r}")
        for name, value in self.projected_margins.items():
            _name(name, "projected margin name")
            _finite(value, f"projected margin {name!r}")


@dataclass(frozen=True)
class SlowPublication:
    """A versioned slow-loop program proposal.

    ``validated`` and ``validation_digest`` are explicit publisher evidence;
    the supervisor still performs its own structural, version, age, and margin
    checks.  ``base_version`` prevents a publication computed from an obsolete
    active program from replacing a newer one.
    """

    publication_id: str
    version: int
    base_version: int
    published_action: int
    program: Program
    validated: bool
    validation_digest: str
    predicted_margins: Mapping[str, float]

    def __post_init__(self) -> None:
        _name(self.publication_id, "publication_id")
        for value, field_name in (
            (self.version, "version"),
            (self.base_version, "base_version"),
            (self.published_action, "published_action"),
        ):
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError(f"{field_name} must be an integer")
        if self.version <= 0:
            raise ValueError("version must be positive")
        if self.base_version < 0 or self.published_action < 0:
            raise ValueError("base_version and published_action must be non-negative")
        if not isinstance(self.validated, bool):
            raise ValueError("validated must be bool")
        if not isinstance(self.validation_digest, str):
            raise ValueError("validation_digest must be a string")
        for name, value in self.predicted_margins.items():
            _name(name, "predicted margin name")
            _finite(value, f"predicted margin {name!r}")


@dataclass(frozen=True)
class PublicationReceipt:
    accepted: bool
    reason: str
    pending_version: int | None
    active_version: int


@dataclass(frozen=True)
class SafetyEvent:
    """A bounded reflex trigger emitted at a fast-loop boundary."""

    event_index: int
    action_index: int
    constraint: str
    kind: ConstraintKind
    current_margin: float
    projected_margin: float
    trigger_margin: float
    remaining_actions: int


@dataclass(frozen=True)
class SupervisorDecision:
    accepted: bool
    action_index: int
    reason: str
    mode: Literal["normal", "reflex", "hold", "rejected"]
    program: Program
    active_version: int
    reflex_remaining: int
    event: SafetyEvent | None = None


class SafetySupervisor:
    """Deterministic fast-loop safety gate with an optional slow publisher.

    ``reflex_action_limit`` bounds each reflex episode and
    ``max_reflex_events`` bounds the total number of episodes.  All expiry and
    freshness checks are expressed in action counts, not elapsed wall time.
    """

    def __init__(
        self,
        constraints: tuple[ConstraintSpec, ...],
        safe_program: Program,
        *,
        reflex_program: Program | None = None,
        reflex_action_limit: int = 3,
        max_reflex_events: int = 8,
        max_publication_age_actions: int = 32,
    ) -> None:
        if not constraints:
            raise ValueError("at least one constraint is required")
        if len({constraint.name for constraint in constraints}) != len(constraints):
            raise ValueError("constraint names must be unique")
        if isinstance(reflex_action_limit, bool) or not isinstance(reflex_action_limit, int):
            raise ValueError("reflex_action_limit must be an integer")
        if reflex_action_limit <= 0:
            raise ValueError("reflex_action_limit must be positive")
        if isinstance(max_reflex_events, bool) or not isinstance(max_reflex_events, int):
            raise ValueError("max_reflex_events must be an integer")
        if max_reflex_events < 0:
            raise ValueError("max_reflex_events must be non-negative")
        if isinstance(max_publication_age_actions, bool) or not isinstance(
            max_publication_age_actions, int
        ):
            raise ValueError("max_publication_age_actions must be an integer")
        if max_publication_age_actions < 0:
            raise ValueError("max_publication_age_actions must be non-negative")

        self._constraints = tuple(constraints)
        self._constraint_by_name = {constraint.name: constraint for constraint in constraints}
        self._safe_program = copy.deepcopy(safe_program)
        self._reflex_program = copy.deepcopy(reflex_program or safe_program)
        self._active_program = copy.deepcopy(safe_program)
        self._active_version = 0
        self._pending: SlowPublication | None = None
        self._last_publication_version = 0
        self._last_action = -1
        self._last_timestamp: int | None = None
        self._reflex_remaining = 0
        self._reflex_events = 0
        self._reflex_action_limit = reflex_action_limit
        self._max_reflex_events = max_reflex_events
        self._max_publication_age_actions = max_publication_age_actions

    @property
    def active_version(self) -> int:
        return self._active_version

    @property
    def constraint_names(self) -> tuple[str, ...]:
        """Return declared safety names in their fixed evaluation order.

        This is an adapter-facing view for generic coordinators.  It exposes
        no vehicle semantics and returns an immutable tuple so callers cannot
        alter the supervisor's safety contract.
        """

        return tuple(constraint.name for constraint in self._constraints)

    @property
    def last_action(self) -> int:
        return self._last_action

    @property
    def reflex_events(self) -> int:
        return self._reflex_events

    @property
    def active_program(self) -> Program:
        return copy.deepcopy(self._active_program)

    @property
    def pending_publication(self) -> SlowPublication | None:
        return copy.deepcopy(self._pending)

    def submit(self, publication: SlowPublication) -> PublicationReceipt:
        """Queue a publication if it is structurally and semantically valid.

        Queueing is not adoption.  A queued publication becomes active only at
        the next accepted :meth:`step`, making replacement atomic with respect
        to the fast loop.
        """

        reason = self._publication_rejection_reason(publication)
        if reason is not None:
            return PublicationReceipt(False, reason, self._pending_version(), self._active_version)

        pending = self._pending
        if pending is not None:
            # Version is authoritative; publication_id is a deterministic tie
            # break for two same-version candidates.
            if (publication.version, publication.publication_id) <= (
                pending.version,
                pending.publication_id,
            ):
                return PublicationReceipt(
                    False, "publication superseded by pending candidate", pending.version, self._active_version
                )
        self._pending = copy.deepcopy(publication)
        self._last_publication_version = max(self._last_publication_version, publication.version)
        return PublicationReceipt(True, "queued for next fast-loop boundary", publication.version, self._active_version)

    def _pending_version(self) -> int | None:
        return None if self._pending is None else self._pending.version

    def _publication_rejection_reason(self, publication: SlowPublication) -> str | None:
        if not isinstance(publication, SlowPublication):
            return "publication has invalid type"
        if not publication.validated:
            return "publication is not validated"
        if not publication.validation_digest.strip():
            return "publication has no validation digest"
        if publication.version <= self._active_version:
            return "publication version is stale"
        if publication.version <= self._last_publication_version:
            return "publication version is stale"
        if publication.base_version != self._active_version:
            return "publication base version is stale"
        if self._last_action >= 0 and publication.published_action > self._last_action:
            return "publication is from the future"
        if self._last_action >= 0 and self._last_action - publication.published_action > self._max_publication_age_actions:
            return "publication is too old"
        expected = set(self._constraint_by_name)
        actual = set(publication.predicted_margins)
        if actual != expected:
            return "publication margins do not match declared constraints"
        for constraint in self._constraints:
            predicted = _finite(
                publication.predicted_margins[constraint.name],
                f"predicted margin {constraint.name!r}",
            )
            if predicted < constraint.trigger_margin:  # type: ignore[operator]
                return f"publication fails constraint {constraint.name!r}"
        return None

    def _observation_rejection_reason(self, observation: FastObservation) -> str | None:
        if not isinstance(observation, FastObservation):
            return "observation has invalid type"
        expected = set(self._constraint_by_name)
        actual = set(observation.margins)
        if not expected.issubset(actual):
            return "observation omits a declared constraint margin"
        if observation.action_index != self._last_action + 1:
            return "action index is not the next fast-loop action"
        if self._last_timestamp is not None and observation.timestamp < self._last_timestamp:
            return "observation timestamp is stale"
        return None

    def _adopt_pending(self) -> None:
        pending = self._pending
        if pending is None:
            return
        # The base version can become stale only if another adoption happened;
        # retaining this guard makes the atomic boundary explicit.
        if pending.base_version != self._active_version:
            self._pending = None
            return
        self._active_program = copy.deepcopy(pending.program)
        # A publication is admitted only after the same checks that establish
        # it as safe.  Once adopted it is therefore the new last-known-safe
        # fallback if a later reflex budget is exhausted.
        self._safe_program = copy.deepcopy(pending.program)
        self._active_version = pending.version
        self._pending = None

    def step(self, observation: FastObservation) -> SupervisorDecision:
        """Consume one fast observation and choose exactly one program.

        Rejected observations do not mutate supervisor state and return the
        current active program.  Accepted observations first adopt a valid
        pending publication, then evaluate constraints, then apply/reflex for
        this action.  This fixed order is part of the replay contract.
        """

        reason = self._observation_rejection_reason(observation)
        if reason is not None:
            return SupervisorDecision(
                False,
                getattr(observation, "action_index", self._last_action),
                reason,
                "rejected",
                copy.deepcopy(self._active_program),
                self._active_version,
                self._reflex_remaining,
            )

        self._adopt_pending()
        self._last_action = observation.action_index
        self._last_timestamp = observation.timestamp

        exhausted: list[tuple[ConstraintSpec, float, float]] = []
        for constraint in self._constraints:
            current = _finite(observation.margins[constraint.name], f"margin {constraint.name!r}")
            projected = _finite(
                observation.projected_margins.get(constraint.name, current),
                f"projected margin {constraint.name!r}",
            )
            if current <= constraint.trigger_margin or projected <= constraint.trigger_margin:  # type: ignore[operator]
                exhausted.append((constraint, current, projected))

        event: SafetyEvent | None = None
        if self._reflex_remaining > 0:
            self._reflex_remaining -= 1
            return SupervisorDecision(
                True,
                observation.action_index,
                "bounded reflex action",
                "reflex",
                copy.deepcopy(self._reflex_program),
                self._active_version,
                self._reflex_remaining,
            )

        if exhausted and self._reflex_events < self._max_reflex_events:
            constraint, current, projected = exhausted[0]
            self._reflex_events += 1
            self._reflex_remaining = self._reflex_action_limit - 1
            event = SafetyEvent(
                self._reflex_events,
                observation.action_index,
                constraint.name,
                constraint.kind,
                current,
                projected,
                constraint.trigger_margin,  # type: ignore[arg-type]
                self._reflex_remaining,
            )
            return SupervisorDecision(
                True,
                observation.action_index,
                "projected margin exhausted",
                "reflex",
                copy.deepcopy(self._reflex_program),
                self._active_version,
                self._reflex_remaining,
                event,
            )

        if exhausted:
            return SupervisorDecision(
                True,
                observation.action_index,
                "reflex budget exhausted; holding last safe program",
                "hold",
                copy.deepcopy(self._safe_program),
                self._active_version,
                0,
            )

        return SupervisorDecision(
            True,
            observation.action_index,
            "active program",
            "normal",
            copy.deepcopy(self._active_program),
            self._active_version,
            0,
        )


__all__ = [
    "ConstraintKind",
    "ConstraintSpec",
    "FastObservation",
    "Program",
    "PublicationReceipt",
    "SafetyEvent",
    "SafetySupervisor",
    "SlowPublication",
    "SupervisorDecision",
]
