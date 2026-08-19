"""Deterministic feasible-objective allocation for generic control systems.

This module is a decision boundary, not a plant model and not a controller for
any particular vehicle.  A caller supplies:

* declared objectives (with an explicit lexicographic priority and direction),
* safety/viability constraints,
* measured effectiveness/controllability evidence and confidence, and
* candidate equilibria or control programs with forecast metrics.

The allocator first removes candidates that violate hard constraints.  It then
chooses lexicographically by (1) safety/viability margin, (2) confidence and
controllability, (3) the caller's remaining objective tiers, and finally the
stable candidate identity.  There is no scalar utility and no random tie
breaking.  If no candidate is feasible, the least-violating candidate is
returned as an explicitly marked fallback (or allocation can be made strict).

The names of objectives, state variables, effectors, and metrics are all
caller-provided.  ``source`` is an interface choice, not a domain vocabulary:
``metrics`` reads a candidate forecast, ``controllability`` combines a
candidate's predicted channel values with measured evidence, ``evidence``
reads a measured value directly, and ``variation`` derives a generic L1 change
in a program's numeric command rows.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Any, Iterable, Literal, Mapping, Protocol, Sequence


Direction = Literal["minimize", "maximize"]
ValueSource = Literal["metrics", "controllability", "evidence", "variation"]


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


def _names(values: Iterable[str], field_name: str) -> tuple[str, ...]:
    result = tuple(values)
    if any(not isinstance(value, str) or not value for value in result):
        raise ValueError(f"{field_name} must contain non-empty names")
    if len(set(result)) != len(result):
        raise ValueError(f"{field_name} must not contain duplicate names")
    return result


@dataclass(frozen=True)
class DeclaredObjective:
    """One lexicographic objective declared by the caller.

    Lower ``priority`` is considered first.  Ties in priority are resolved by
    ``ordinal`` and then ``name``; this makes the result independent of mapping
    or candidate insertion order.  ``tolerance`` creates an explicit bucket
    for insignificant numeric differences.
    """

    name: str
    priority: int
    direction: Direction = "minimize"
    metric: str | None = None
    source: ValueSource = "metrics"
    ordinal: int = 0
    tolerance: float = 0.0

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name:
            raise ValueError("objective name must be a non-empty string")
        if isinstance(self.priority, bool) or not isinstance(self.priority, int):
            raise ValueError("objective priority must be an integer")
        if isinstance(self.ordinal, bool) or not isinstance(self.ordinal, int):
            raise ValueError("objective ordinal must be an integer")
        if self.direction not in ("minimize", "maximize"):
            raise ValueError("objective direction must be minimize or maximize")
        if self.source not in ("metrics", "controllability", "evidence", "variation"):
            raise ValueError(f"unknown objective source: {self.source!r}")
        if self.metric is None and self.source == "metrics":
            # The common case is an objective whose name is also the forecast
            # metric.  Keeping this default makes declarations concise while
            # retaining an explicit metric in the frozen value object.
            object.__setattr__(self, "metric", self.name)
        if self.source not in ("variation",) and (
            not isinstance(self.metric, str) or not self.metric
        ):
            raise ValueError("objective metric must be a non-empty string")
        if self.source == "variation" and self.metric is not None and not self.metric:
            raise ValueError("variation metric must be non-empty when supplied")
        if _finite(self.tolerance, "objective tolerance") < 0.0:
            raise ValueError("objective tolerance must be non-negative")

    @property
    def key(self) -> tuple[int, int, str]:
        return (self.priority, self.ordinal, self.name)


# Short alias is useful at adapters without weakening the descriptive public
# name used in documentation.
Objective = DeclaredObjective


@dataclass(frozen=True)
class ViabilityConstraint:
    """A scalar hard/soft bound on a generic forecast or measured value."""

    name: str
    metric: str
    lower: float | None = None
    upper: float | None = None
    source: Literal["metrics", "evidence"] = "metrics"
    hard: bool = True
    ordinal: int = 0
    tolerance: float = 0.0
    scale: float = 1.0

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name:
            raise ValueError("constraint name must be a non-empty string")
        if not isinstance(self.metric, str) or not self.metric:
            raise ValueError("constraint metric must be a non-empty string")
        if self.lower is None and self.upper is None:
            raise ValueError("constraint needs a lower or upper bound")
        if self.lower is not None:
            _finite(self.lower, "constraint lower")
        if self.upper is not None:
            _finite(self.upper, "constraint upper")
        if self.lower is not None and self.upper is not None and self.lower > self.upper:
            raise ValueError("constraint lower must not exceed upper")
        if self.source not in ("metrics", "evidence"):
            raise ValueError("constraint source must be metrics or evidence")
        if isinstance(self.ordinal, bool) or not isinstance(self.ordinal, int):
            raise ValueError("constraint ordinal must be an integer")
        if _finite(self.tolerance, "constraint tolerance") < 0.0:
            raise ValueError("constraint tolerance must be non-negative")
        if _finite(self.scale, "constraint scale") <= 0.0:
            raise ValueError("constraint scale must be positive")

    @property
    def key(self) -> tuple[int, str]:
        return (self.ordinal, self.name)

    def violation(self, value: float) -> float:
        """Return normalized positive violation, or zero inside the bound."""
        value = _finite(value, f"constraint value {self.name}")
        lower_gap = 0.0 if self.lower is None else self.lower - value - self.tolerance
        upper_gap = 0.0 if self.upper is None else value - self.upper - self.tolerance
        return max(0.0, lower_gap, upper_gap) / self.scale

    def margin(self, value: float) -> float:
        """Return normalized distance to the nearest declared boundary."""
        value = _finite(value, f"constraint value {self.name}")
        margins = []
        if self.lower is not None:
            margins.append(value - self.lower)
        if self.upper is not None:
            margins.append(self.upper - value)
        return min(margins) / self.scale


@dataclass(frozen=True)
class ControllabilityMeasure:
    """Measured effectiveness for one generic channel and its confidence."""

    value: float
    confidence: float

    def __post_init__(self) -> None:
        _finite(self.value, "controllability value")
        confidence = _finite(self.confidence, "controllability confidence")
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("controllability confidence must be in [0, 1]")


@dataclass(frozen=True)
class ControllabilityEvidence:
    """Measured effectiveness and confidence supplied by an estimator."""

    measurements: Mapping[str, ControllabilityMeasure]

    def __post_init__(self) -> None:
        if not isinstance(self.measurements, Mapping):
            raise ValueError("measurements must be a mapping")
        for key, value in self.measurements.items():
            if not isinstance(key, str) or not key:
                raise ValueError("measurement names must be non-empty strings")
            if not isinstance(value, ControllabilityMeasure):
                raise ValueError("measurements must contain ControllabilityMeasure values")

    def measure(self, name: str) -> ControllabilityMeasure:
        try:
            return self.measurements[name]
        except KeyError as exc:
            raise ValueError(f"missing controllability measurement: {name!r}") from exc


@dataclass(frozen=True)
class ControlCandidate:
    """Forecast equilibrium/program and its caller-declared scalar metrics."""

    identity: str
    equilibrium: Mapping[str, float]
    program: Any = None
    metrics: Mapping[str, float] = field(default_factory=dict)
    controllability: Mapping[str, float] = field(default_factory=dict)
    required_measurements: tuple[str, ...] = ()
    control_variation: float | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.identity, str) or not self.identity:
            raise ValueError("candidate identity must be a non-empty string")
        if not isinstance(self.equilibrium, Mapping):
            raise ValueError("equilibrium must be a mapping")
        for key, value in self.equilibrium.items():
            if not isinstance(key, str) or not key:
                raise ValueError("equilibrium names must be non-empty strings")
            _finite(value, f"equilibrium {key}")
        for group_name, group in (("metrics", self.metrics), ("controllability", self.controllability)):
            if not isinstance(group, Mapping):
                raise ValueError(f"candidate {group_name} must be a mapping")
            for key, value in group.items():
                if not isinstance(key, str) or not key:
                    raise ValueError(f"candidate {group_name} names must be non-empty strings")
                _finite(value, f"candidate {group_name} {key}")
        names = _names(self.required_measurements, "required_measurements")
        object.__setattr__(self, "required_measurements", names)
        if self.control_variation is not None and _finite(self.control_variation, "control_variation") < 0.0:
            raise ValueError("control_variation must be non-negative")


@dataclass(frozen=True)
class CandidateAssessment:
    candidate: ControlCandidate
    feasible: bool
    hard_violations: tuple[float, ...]
    safety_margins: tuple[float, ...]
    soft_violations: tuple[float, ...]
    confidence_deficits: tuple[float, ...]
    objective_values: tuple[float, ...]
    rank_key: tuple[Any, ...]
    diagnostics: tuple[str, ...] = ()


@dataclass(frozen=True)
class AllocationResult:
    selected: ControlCandidate
    assessment: CandidateAssessment
    ranked: tuple[CandidateAssessment, ...]
    used_infeasible_fallback: bool
    contract_version: str = "feasible_objective_allocator.v1"

    @property
    def feasible(self) -> bool:
        return self.assessment.feasible

    def as_dict(self) -> dict[str, Any]:
        """Stable, adapter-friendly decision receipt (program remains opaque)."""
        return {
            "contract_version": self.contract_version,
            "selected_identity": self.selected.identity,
            "feasible": self.feasible,
            "used_infeasible_fallback": self.used_infeasible_fallback,
            "hard_violations": self.assessment.hard_violations,
            "safety_margins": self.assessment.safety_margins,
            "soft_violations": self.assessment.soft_violations,
            "confidence_deficits": self.assessment.confidence_deficits,
            "objective_values": self.assessment.objective_values,
            "diagnostics": self.assessment.diagnostics,
        }


class CandidateForecastAdapter(Protocol):
    """Narrow integration contract for graph/world adapters.

    Adapters translate domain state into immutable candidates; the allocator
    never reads a graph, simulator, actuator, or vehicle-specific state.
    """

    def forecast_candidates(self, state: Any) -> Iterable[ControlCandidate]: ...


def _program_variation(program: Any) -> float:
    """Deterministically compute L1 variation for numeric command rows."""
    if program is None:
        return 0.0
    if isinstance(program, Mapping):
        rows: list[Any] = [program]
    else:
        try:
            rows = list(program)
        except TypeError as exc:
            raise ValueError("program must be a mapping or sequence of numeric rows") from exc
    if len(rows) < 2:
        return 0.0

    def row_values(row: Any) -> tuple[float, ...]:
        if isinstance(row, Mapping):
            keys = sorted(row)
            return tuple(_finite(row[key], f"program value {key}") for key in keys)
        try:
            return tuple(_finite(value, "program value") for value in row)
        except TypeError as exc:
            raise ValueError("program rows must be mappings or numeric sequences") from exc

    canonical = [row_values(row) for row in rows]
    width = len(canonical[0])
    if any(len(row) != width for row in canonical):
        raise ValueError("program rows must have equal width")
    return sum(
        abs(current - previous)
        for previous, current in zip(canonical, canonical[1:])
        for previous, current in zip(previous, current)
    )


class FeasibleObjectiveAllocator:
    """Fixed-order lexicographic allocator with no hidden state or RNG."""

    def __init__(
        self,
        objectives: Iterable[DeclaredObjective],
        constraints: Iterable[ViabilityConstraint] = (),
        *,
        confidence_floor: float = 0.0,
        strict: bool = False,
    ) -> None:
        self.objectives = tuple(objectives)
        self.constraints = tuple(constraints)
        if not self.objectives:
            raise ValueError("at least one objective is required")
        if len({objective.name for objective in self.objectives}) != len(self.objectives):
            raise ValueError("objective names must be unique")
        if len({constraint.name for constraint in self.constraints}) != len(self.constraints):
            raise ValueError("constraint names must be unique")
        self.objectives = tuple(sorted(self.objectives, key=lambda item: item.key))
        self.constraints = tuple(sorted(self.constraints, key=lambda item: item.key))
        floor = _finite(confidence_floor, "confidence_floor")
        if not 0.0 <= floor <= 1.0:
            raise ValueError("confidence_floor must be in [0, 1]")
        self.confidence_floor = floor
        self.strict = bool(strict)

    @staticmethod
    def _objective_score(value: float, objective: DeclaredObjective) -> float:
        tolerance = float(objective.tolerance)
        if tolerance:
            value = round(value / tolerance) * tolerance
        return value if objective.direction == "minimize" else -value

    @staticmethod
    def _source_value(
        candidate: ControlCandidate,
        objective: DeclaredObjective,
        evidence: ControllabilityEvidence,
    ) -> float:
        if objective.source == "metrics":
            assert objective.metric is not None
            try:
                return _finite(candidate.metrics[objective.metric], f"candidate metric {objective.metric}")
            except KeyError as exc:
                raise ValueError(
                    f"candidate {candidate.identity!r} is missing metric {objective.metric!r}"
                ) from exc
        if objective.source == "evidence":
            assert objective.metric is not None
            return evidence.measure(objective.metric).value
        if objective.source == "variation":
            if candidate.control_variation is not None:
                return float(candidate.control_variation)
            return _program_variation(candidate.program)
        # ``controllability`` is a predicted channel value weighted by its
        # measured effectiveness and confidence.  A metric names one channel;
        # omitting it aggregates all explicitly declared candidate channels.
        channels = (
            (objective.metric,)
            if objective.metric is not None
            else tuple(sorted(candidate.controllability))
        )
        if not channels:
            raise ValueError(f"candidate {candidate.identity!r} has no controllability channels")
        weighted = []
        for channel in channels:
            if channel not in candidate.controllability:
                raise ValueError(
                    f"candidate {candidate.identity!r} is missing controllability {channel!r}"
                )
            measure = evidence.measure(channel)
            weighted.append(candidate.controllability[channel] * measure.value * measure.confidence)
        return sum(weighted) / len(weighted)

    def _assess(
        self,
        candidate: ControlCandidate,
        evidence: ControllabilityEvidence,
    ) -> CandidateAssessment:
        hard: list[float] = []
        safety_margins: list[float] = []
        soft: list[float] = []
        for constraint in self.constraints:
            if constraint.source == "metrics":
                try:
                    value = candidate.metrics[constraint.metric]
                except KeyError as exc:
                    raise ValueError(
                        f"candidate {candidate.identity!r} is missing constraint metric {constraint.metric!r}"
                    ) from exc
            else:
                value = evidence.measure(constraint.metric).value
            violation = constraint.violation(value)
            if constraint.hard:
                hard.append(violation)
                safety_margins.append(constraint.margin(value))
            else:
                soft.append(violation)

        deficits = []
        diagnostics = []
        for name in candidate.required_measurements:
            measure = evidence.measure(name)
            deficit = max(0.0, self.confidence_floor - measure.confidence)
            deficits.append(deficit)
            if deficit:
                diagnostics.append(f"confidence below floor for {name}")

        objective_values = tuple(
            self._objective_score(
                self._source_value(candidate, objective, evidence), objective
            )
            for objective in self.objectives
        )
        feasible = not any(hard) and not any(deficits)
        # The first components are hard safety margins; then evidence quality;
        # then soft bounds; then the declared objective lexicographic vector.
        # Candidate identity is the final deterministic tie-break.
        rank_key = (
            tuple(hard),
            tuple(-margin for margin in safety_margins),
            tuple(deficits),
            tuple(soft),
            objective_values,
            candidate.identity,
        )
        return CandidateAssessment(
            candidate=candidate,
            feasible=feasible,
            hard_violations=tuple(hard),
            safety_margins=tuple(safety_margins),
            soft_violations=tuple(soft),
            confidence_deficits=tuple(deficits),
            objective_values=objective_values,
            rank_key=rank_key,
            diagnostics=tuple(diagnostics),
        )

    def allocate(
        self,
        candidates: Iterable[ControlCandidate],
        evidence: ControllabilityEvidence,
    ) -> AllocationResult:
        """Select one candidate and return the complete deterministic receipt."""
        candidates = tuple(candidates)
        if not candidates:
            raise ValueError("at least one candidate is required")
        if len({candidate.identity for candidate in candidates}) != len(candidates):
            raise ValueError("candidate identities must be unique")
        assessments = tuple(self._assess(candidate, evidence) for candidate in candidates)
        feasible = tuple(item for item in assessments if item.feasible)
        if self.strict and not feasible:
            raise ValueError("no feasible candidate satisfies the declared constraints")
        # Keep rejected candidates in the receipt for auditability, while the
        # leading feasibility bit ensures they can never outrank a feasible
        # candidate.  If none are feasible, the same ordering becomes the
        # deterministic least-violating fallback policy.
        ranked = tuple(sorted(
            assessments,
            key=lambda item: (0 if item.feasible else 1, item.rank_key),
        ))
        selected = ranked[0]
        return AllocationResult(
            selected=selected.candidate,
            assessment=selected,
            ranked=ranked,
            used_infeasible_fallback=not bool(feasible),
        )


def allocate_feasible_objective(
    candidates: Iterable[ControlCandidate],
    objectives: Iterable[DeclaredObjective],
    constraints: Iterable[ViabilityConstraint],
    evidence: ControllabilityEvidence,
    *,
    confidence_floor: float = 0.0,
    strict: bool = False,
) -> AllocationResult:
    """Functional adapter for callers that do not need a reusable allocator."""
    return FeasibleObjectiveAllocator(
        objectives,
        constraints,
        confidence_floor=confidence_floor,
        strict=strict,
    ).allocate(candidates, evidence)


__all__ = [
    "AllocationResult",
    "CandidateAssessment",
    "CandidateForecastAdapter",
    "ControllabilityEvidence",
    "ControllabilityMeasure",
    "ControlCandidate",
    "DeclaredObjective",
    "FeasibleObjectiveAllocator",
    "Objective",
    "ViabilityConstraint",
    "allocate_feasible_objective",
]
