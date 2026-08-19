"""Validated, graph-owned evidence for recoverable learning decisions.

The safety context is deliberately generic.  A body, flight controller, or
other plant can publish the same contract when it has a reachable recovery
operation.  The risk gate may relax its preservation triangle only after this
evidence has been verified; a host-side boolean is not sufficient.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Mapping


def _nonnegative(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite non-negative number")
    result = float(value)
    if not math.isfinite(result) or result < 0.0:
        raise ValueError(f"{name} must be a finite non-negative number")
    return result


@dataclass(frozen=True)
class LearningSafetyContext:
    """Evidence that a learning excursion remains recoverable.

    ``verified`` is intentionally separate from the component facts.  The
    graph can retain an incomplete context for diagnostics, but relaxation is
    only active when the graph has verified at least one reachable recovery
    path (reset or effective protective support).
    """

    verified: bool
    reset_reachable: bool
    reset_cost_units: float
    protective_support_available: bool
    protective_support_effectiveness: float
    recovery_path_count: int = 0
    required_horizon_units: int = 1
    minimum_width_relaxation: float = 0.0
    information_loss_allowance: float = 0.0

    def __post_init__(self) -> None:
        if not isinstance(self.verified, bool):
            raise ValueError("verified must be boolean")
        if not isinstance(self.reset_reachable, bool):
            raise ValueError("reset_reachable must be boolean")
        if not isinstance(self.protective_support_available, bool):
            raise ValueError("protective_support_available must be boolean")
        object.__setattr__(
            self, "reset_cost_units", _nonnegative(self.reset_cost_units, "reset_cost_units")
        )
        effectiveness = _nonnegative(
            self.protective_support_effectiveness,
            "protective_support_effectiveness",
        )
        if effectiveness > 1.0:
            raise ValueError("protective_support_effectiveness must be at most one")
        object.__setattr__(self, "protective_support_effectiveness", effectiveness)
        if isinstance(self.recovery_path_count, bool) or not isinstance(self.recovery_path_count, int):
            raise ValueError("recovery_path_count must be a non-negative int")
        if self.recovery_path_count < 0:
            raise ValueError("recovery_path_count must be a non-negative int")
        if isinstance(self.required_horizon_units, bool) or not isinstance(self.required_horizon_units, int):
            raise ValueError("required_horizon_units must be a positive int")
        if self.required_horizon_units < 1:
            raise ValueError("required_horizon_units must be a positive int")
        object.__setattr__(
            self, "minimum_width_relaxation",
            _nonnegative(self.minimum_width_relaxation, "minimum_width_relaxation"),
        )
        object.__setattr__(
            self, "information_loss_allowance",
            _nonnegative(self.information_loss_allowance, "information_loss_allowance"),
        )

    @property
    def recoverable(self) -> bool:
        return bool(
            self.reset_reachable
            or (
                self.protective_support_available
                and self.protective_support_effectiveness > 0.0
            )
        )

    @property
    def active(self) -> bool:
        return self.verified and self.recoverable

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "LearningSafetyContext":
        if not isinstance(value, Mapping):
            raise ValueError("learning safety context must be a mapping")
        allowed = {
            "verified", "reset_reachable", "reset_cost_units",
            "protective_support_available", "protective_support_effectiveness",
            "recovery_path_count", "required_horizon_units",
            "minimum_width_relaxation", "information_loss_allowance",
        }
        unknown = set(value) - allowed
        if unknown:
            raise ValueError(f"learning safety context has unknown keys: {sorted(unknown)!r}")
        required = allowed - {"recovery_path_count"}
        missing = required - set(value)
        if missing:
            raise ValueError(f"learning safety context missing keys: {sorted(missing)!r}")
        return cls(**value)

    def as_mapping(self) -> dict[str, Any]:
        return {
            "verified": self.verified,
            "reset_reachable": self.reset_reachable,
            "reset_cost_units": self.reset_cost_units,
            "protective_support_available": self.protective_support_available,
            "protective_support_effectiveness": self.protective_support_effectiveness,
            "recovery_path_count": self.recovery_path_count,
            "required_horizon_units": self.required_horizon_units,
            "minimum_width_relaxation": self.minimum_width_relaxation,
            "information_loss_allowance": self.information_loss_allowance,
        }


__all__ = ["LearningSafetyContext"]
