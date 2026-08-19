"""Generic online control-effectiveness identification.

This module is deliberately plant- and controller-independent.  It estimates a
local linear map from commanded effectors to observed output-axis deltas::

    observed_delta[axis] ~= sum(effectiveness[axis, effector] * command[effector])

The estimator is useful at a world/receipt boundary: a simulator or physical
adapter supplies command values and measured deltas, while an agent remains
responsible for deciding what to command.  Compound commands are supported;
the regressors are the complete command vector, so attribution is based on the
joint design rather than assigning every receipt to every effector.

Determinism is an explicit contract.  Samples are accepted in strictly
increasing ``sample_id`` order, names are always projected into the configured
tuples, and all loops use those tuples' order.  Forgetting, prior covariance,
rank tolerance, and excitation bounds are declared configuration.  Missing or
unchanged axes do not update (or forget) their own state.

The module has no vehicle-specific assumptions, safety policy, or action logic.
``EffectivenessReceiptAdapter`` is the narrow adapter contract for callers
whose receipts are not already mappings.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Generic, Iterable, Mapping, Protocol, Sequence, TypeVar


ReceiptT = TypeVar("ReceiptT")


class EffectivenessReceiptAdapter(Protocol[ReceiptT]):
    """Adapter contract for turning a domain receipt into identification data.

    ``observed_deltas`` must return changes measured over the same interval as
    ``command_values``.  It may return only axes that were observed or changed;
    omitted axes are intentionally not updated.  The adapter must not make
    control decisions or reorder values.
    """

    def command_values(self, receipt: ReceiptT) -> Mapping[str, float]: ...

    def observed_deltas(self, receipt: ReceiptT) -> Mapping[str, float]: ...


def _finite(value: object, field: str) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{field} must be finite, not bool")
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{field} must be finite") from exc
    if not math.isfinite(result):
        raise ValueError(f"{field} must be finite")
    return result


def _names(values: Iterable[str], field: str) -> tuple[str, ...]:
    result = tuple(values)
    if not result or any(not isinstance(value, str) or not value for value in result):
        raise ValueError(f"{field} must contain non-empty names")
    if len(set(result)) != len(result):
        raise ValueError(f"{field} must not contain duplicate names")
    return result


def _matrix(rows: int, cols: int, value: float = 0.0) -> list[list[float]]:
    return [[float(value) for _ in range(cols)] for _ in range(rows)]


def _outer(vector: Sequence[float]) -> list[list[float]]:
    return [[a * b for b in vector] for a in vector]


def _mat_vec(matrix: Sequence[Sequence[float]], vector: Sequence[float]) -> list[float]:
    return [sum(row[j] * vector[j] for j in range(len(vector))) for row in matrix]


def _dot(left: Sequence[float], right: Sequence[float]) -> float:
    return sum(a * b for a, b in zip(left, right))


def _rref_rank_and_pivots(
    matrix: Sequence[Sequence[float]],
    tolerance: float,
) -> tuple[int, tuple[int, ...]]:
    """Return deterministic row-reduction rank and pivot columns.

    The matrices here are small command Gram matrices.  A fixed first-pivot
    policy is preferable to a backend-dependent eigensolver for replayable
    excitation suggestions.
    """
    work = [list(row) for row in matrix]
    if not work or not work[0]:
        return 0, ()
    rows, cols = len(work), len(work[0])
    rank = 0
    pivots: list[int] = []
    for column in range(cols):
        pivot = next(
            (row for row in range(rank, rows) if abs(work[row][column]) > tolerance),
            None,
        )
        if pivot is None:
            continue
        work[rank], work[pivot] = work[pivot], work[rank]
        scale = work[rank][column]
        work[rank] = [value / scale for value in work[rank]]
        for row in range(rows):
            if row == rank:
                continue
            factor = work[row][column]
            if abs(factor) <= tolerance:
                continue
            work[row] = [
                value - factor * pivot_value
                for value, pivot_value in zip(work[row], work[rank])
            ]
        pivots.append(column)
        rank += 1
        if rank == rows:
            break
    return rank, tuple(pivots)


@dataclass(frozen=True)
class IdentificationConfiguration:
    """Numerical and bounded-excitation policy for the estimator.

    ``forgetting_factor`` is standard RLS lambda.  A value of 1.0 gives a
    stationary least-squares estimate; lower values track a changing local
    plant.  ``prior_precision`` sets the isotropic prior covariance to
    ``1 / prior_precision``.  Excitation bounds are per-effector command
    magnitudes and are descriptive limits for proposed probes, not commands.
    """

    forgetting_factor: float = 1.0
    prior_precision: float = 1.0
    rank_tolerance: float = 1e-9
    excitation_bounds: Mapping[str, float] | float = 1.0

    def __post_init__(self) -> None:
        if not math.isfinite(self.forgetting_factor) or not 0.0 < self.forgetting_factor <= 1.0:
            raise ValueError("forgetting_factor must be in (0, 1]")
        if not math.isfinite(self.prior_precision) or self.prior_precision <= 0.0:
            raise ValueError("prior_precision must be finite and positive")
        if not math.isfinite(self.rank_tolerance) or self.rank_tolerance <= 0.0:
            raise ValueError("rank_tolerance must be finite and positive")
        if isinstance(self.excitation_bounds, Mapping):
            for name, value in self.excitation_bounds.items():
                if not isinstance(name, str) or not name:
                    raise ValueError("excitation bound names must be non-empty strings")
                if not math.isfinite(float(value)) or float(value) <= 0.0:
                    raise ValueError("excitation bounds must be finite and positive")
        elif not math.isfinite(float(self.excitation_bounds)) or float(self.excitation_bounds) <= 0.0:
            raise ValueError("excitation_bounds must be finite and positive")


@dataclass(frozen=True)
class IdentificationSample:
    """A command/receipt pair in the adapter-neutral representation."""

    sample_id: int
    command_values: Mapping[str, float]
    observed_deltas: Mapping[str, float]
    changed_axes: tuple[str, ...] | None = None


@dataclass(frozen=True)
class AxisEffectivenessEstimate:
    """Posterior estimate and quality metrics for one observed output axis."""

    axis: str
    effectors: tuple[str, ...]
    coefficients: tuple[float, ...]
    covariance: tuple[tuple[float, ...], ...]
    rank: int
    identifiable: bool
    observed_samples: int
    informative_samples: int
    uncertainty: float
    confidence: float
    residual_rms: float | None

    @property
    def coefficient_map(self) -> dict[str, float]:
        return dict(zip(self.effectors, self.coefficients))


@dataclass(frozen=True)
class ExcitationNeed:
    """A bounded information request, not an action or controller decision."""

    axis: str
    rank: int
    required_rank: int
    missing_effectors: tuple[str, ...]
    candidate_commands: tuple[tuple[float, ...], ...]
    bounds: tuple[float, ...]
    reason: str


class ControlEffectivenessIdentifier:
    """Deterministic per-axis RLS estimator for compound control receipts."""

    def __init__(
        self,
        effectors: Iterable[str],
        axes: Iterable[str],
        *,
        configuration: IdentificationConfiguration | None = None,
    ) -> None:
        self.effectors = _names(effectors, "effectors")
        self.axes = _names(axes, "axes")
        self.configuration = configuration or IdentificationConfiguration()
        self._n = len(self.effectors)
        self._prior_covariance = 1.0 / self.configuration.prior_precision
        self._coefficients = {
            axis: [0.0] * self._n for axis in self.axes
        }
        self._covariance = {
            axis: [
                [self._prior_covariance if i == j else 0.0 for j in range(self._n)]
                for i in range(self._n)
            ]
            for axis in self.axes
        }
        self._information = {
            axis: _matrix(self._n, self._n) for axis in self.axes
        }
        self._observed_samples = {axis: 0 for axis in self.axes}
        self._informative_samples = {axis: 0 for axis in self.axes}
        self._residual_energy = {axis: 0.0 for axis in self.axes}
        self._residual_weight = {axis: 0.0 for axis in self.axes}
        self._last_sample_id: int | None = None

    def reset(self) -> None:
        """Return to the declared prior while preserving configuration."""
        self.__init__(self.effectors, self.axes, configuration=self.configuration)

    def _commands(self, values: Mapping[str, float] | Sequence[float]) -> list[float]:
        if isinstance(values, Mapping):
            unknown = set(values) - set(self.effectors)
            if unknown:
                raise ValueError(f"unknown effector names: {sorted(unknown)!r}")
            if any(name not in values for name in self.effectors):
                missing = [name for name in self.effectors if name not in values]
                raise ValueError(f"missing effector values: {missing!r}")
            return [_finite(values[name], f"command {name}") for name in self.effectors]
        result = [_finite(value, "command") for value in values]
        if len(result) != self._n:
            raise ValueError(f"command sequence must contain {self._n} values")
        return result

    def _observations(
        self,
        values: Mapping[str, float] | Sequence[float],
        changed_axes: Iterable[str] | None,
    ) -> dict[str, float]:
        if isinstance(values, Mapping):
            unknown = set(values) - set(self.axes)
            if unknown:
                raise ValueError(f"unknown axis names: {sorted(unknown)!r}")
            result = {
                axis: _finite(values[axis], f"observed delta {axis}")
                for axis in self.axes
                if axis in values
            }
        else:
            sequence = [_finite(value, "observed delta") for value in values]
            if len(sequence) != len(self.axes):
                raise ValueError(f"observed sequence must contain {len(self.axes)} values")
            result = dict(zip(self.axes, sequence))
        if changed_axes is None:
            return result
        selected = tuple(changed_axes)
        if len(set(selected)) != len(selected) or any(axis not in self.axes for axis in selected):
            raise ValueError("changed_axes must contain unique configured axis names")
        return {axis: result[axis] for axis in selected if axis in result}

    def update(
        self,
        sample: IdentificationSample,
    ) -> tuple[str, ...]:
        """Consume one sample and return axes actually updated.

        ``sample_id`` makes chronological ordering and duplicate replay errors
        explicit.  A zero command is accepted as a receipt but is not an
        informative regressor.  Axes omitted from ``observed_deltas`` or
        excluded by ``changed_axes`` are untouched, including their forgetting
        state.
        """
        if isinstance(sample.sample_id, bool) or not isinstance(sample.sample_id, int):
            raise ValueError("sample_id must be an integer")
        if self._last_sample_id is not None and sample.sample_id <= self._last_sample_id:
            raise ValueError("sample_id must increase strictly")
        commands = self._commands(sample.command_values)
        observations = self._observations(sample.observed_deltas, sample.changed_axes)
        self._last_sample_id = sample.sample_id
        informative = any(abs(value) > self.configuration.rank_tolerance for value in commands)
        updated: list[str] = []
        for axis in self.axes:
            if axis not in observations:
                continue
            updated.append(axis)
            self._observed_samples[axis] += 1
            if not informative:
                continue
            self._informative_samples[axis] += 1
            lam = self.configuration.forgetting_factor
            prior_p = self._covariance[axis]
            prior_coefficients = self._coefficients[axis]
            px = _mat_vec(prior_p, commands)
            denominator = lam + _dot(commands, px)
            gain = [value / denominator for value in px]
            prediction = _dot(prior_coefficients, commands)
            error = observations[axis] - prediction
            self._coefficients[axis] = [
                coefficient + gain[j] * error
                for j, coefficient in enumerate(prior_coefficients)
            ]
            self._covariance[axis] = [
                [
                    (prior_p[i][j] - gain[i] * px[j]) / lam
                    for j in range(self._n)
                ]
                for i in range(self._n)
            ]
            # Roundoff can make a covariance microscopically asymmetric or
            # negative on its diagonal.  Symmetrisation is deterministic and
            # keeps quality metrics meaningful without hiding real uncertainty.
            covariance = self._covariance[axis]
            for i in range(self._n):
                covariance[i][i] = max(0.0, covariance[i][i])
                for j in range(i):
                    value = 0.5 * (covariance[i][j] + covariance[j][i])
                    covariance[i][j] = value
                    covariance[j][i] = value
            information = self._information[axis]
            contribution = _outer(commands)
            self._information[axis] = [
                [lam * information[i][j] + contribution[i][j] for j in range(self._n)]
                for i in range(self._n)
            ]
            self._residual_energy[axis] = lam * self._residual_energy[axis] + error * error
            self._residual_weight[axis] = lam * self._residual_weight[axis] + 1.0
        return tuple(updated)

    def update_from_receipt(
        self,
        sample_id: int,
        receipt: ReceiptT,
        adapter: EffectivenessReceiptAdapter[ReceiptT],
        *,
        changed_axes: Iterable[str] | None = None,
    ) -> tuple[str, ...]:
        """Apply the explicit adapter contract to one domain receipt."""
        return self.update(
            IdentificationSample(
                sample_id=sample_id,
                command_values=adapter.command_values(receipt),
                observed_deltas=adapter.observed_deltas(receipt),
                changed_axes=None if changed_axes is None else tuple(changed_axes),
            )
        )

    def estimate(self, axis: str) -> AxisEffectivenessEstimate:
        """Return a snapshot for one configured axis."""
        if axis not in self.axes:
            raise KeyError(axis)
        rank, _ = _rref_rank_and_pivots(
            self._information[axis], self.configuration.rank_tolerance
        )
        covariance = tuple(tuple(row) for row in self._covariance[axis])
        normalized_variance = sum(covariance[i][i] for i in range(self._n))
        normalized_variance /= self._n * self._prior_covariance
        uncertainty = math.sqrt(max(0.0, normalized_variance))
        coverage = rank / self._n
        confidence = max(0.0, min(1.0, coverage / (1.0 + uncertainty)))
        residual_rms = None
        if self._residual_weight[axis] > 0.0:
            residual_rms = math.sqrt(
                max(0.0, self._residual_energy[axis] / self._residual_weight[axis])
            )
        return AxisEffectivenessEstimate(
            axis=axis,
            effectors=self.effectors,
            coefficients=tuple(self._coefficients[axis]),
            covariance=covariance,
            rank=rank,
            identifiable=rank == self._n,
            observed_samples=self._observed_samples[axis],
            informative_samples=self._informative_samples[axis],
            uncertainty=uncertainty,
            confidence=confidence,
            residual_rms=residual_rms,
        )

    def estimates(self) -> tuple[AxisEffectivenessEstimate, ...]:
        """Return all axis estimates in configured order."""
        return tuple(self.estimate(axis) for axis in self.axes)

    def _bound(self, effector: str) -> float:
        bounds = self.configuration.excitation_bounds
        if isinstance(bounds, Mapping):
            if effector not in bounds:
                raise ValueError(f"missing excitation bound for {effector!r}")
            return _finite(bounds[effector], f"excitation bound {effector}")
        return _finite(bounds, "excitation bound")

    def excitation_needs(self, axis: str) -> ExcitationNeed | None:
        """Describe bounded probes needed to make one axis identifiable.

        Candidates are positive one-effector basis commands for deterministic
        free columns of the information matrix.  They are suggestions for an
        external experiment scheduler; this class never executes or ranks them.
        ``None`` means the axis is full-rank, so no rank-based excitation need
        is reported.
        """
        estimate = self.estimate(axis)
        if estimate.identifiable:
            return None
        rank, pivots = _rref_rank_and_pivots(
            self._information[axis], self.configuration.rank_tolerance
        )
        free = tuple(index for index in range(self._n) if index not in pivots)
        bounds = tuple(self._bound(effector) for effector in self.effectors)
        candidates = []
        for index in free:
            command = [0.0] * self._n
            command[index] = bounds[index]
            candidates.append(tuple(command))
        return ExcitationNeed(
            axis=axis,
            rank=rank,
            required_rank=self._n,
            missing_effectors=tuple(self.effectors[index] for index in free),
            candidate_commands=tuple(candidates),
            bounds=bounds,
            reason="rank-deficient command information; collect receipts for the listed bounded probes",
        )
