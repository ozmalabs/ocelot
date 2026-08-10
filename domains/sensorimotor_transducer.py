"""Mechanical delayed/noisy sensor boundary for embodied simulators.

The transducer is part of the world, not the agent.  It samples physical state,
adds declared measurement noise, and publishes a delayed sample with explicit
variance and latency.  Fusion, prediction, action and learning remain graph
Rules in the Rust substrate.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import math
import random
from typing import Iterable


def _vector(values: Iterable[float], *, field: str) -> tuple[float, float, float]:
    result = tuple(float(value) for value in values)
    if len(result) != 3 or not all(math.isfinite(value) for value in result):
        raise ValueError(f"{field} must contain three finite values")
    return result


def _quaternion(
    values: Iterable[float],
    *,
    field: str,
) -> tuple[float, float, float, float]:
    result = tuple(float(value) for value in values)
    if len(result) != 4 or not all(math.isfinite(value) for value in result):
        raise ValueError(f"{field} must contain four finite values")
    norm = math.sqrt(sum(value * value for value in result))
    if norm == 0.0:
        raise ValueError(f"{field} must have non-zero magnitude")
    return tuple(value / norm for value in result)


@dataclass(frozen=True)
class SensorimotorSensorConfiguration:
    """Declared physical sensor properties for a simulated body."""

    position_noise_std: float = 0.0
    orientation_noise_std: float = 0.0
    velocity_noise_std: float = 0.0
    angular_noise_std: float = 0.0
    contact_noise_std: float = 0.0
    latency_samples: int = 0

    def __post_init__(self) -> None:
        for field in (
            "position_noise_std",
            "orientation_noise_std",
            "velocity_noise_std",
            "angular_noise_std",
            "contact_noise_std",
        ):
            value = getattr(self, field)
            if not math.isfinite(value) or value < 0.0:
                raise ValueError(f"{field} must be finite and non-negative")
        if (
            isinstance(self.latency_samples, bool)
            or not isinstance(self.latency_samples, int)
            or self.latency_samples < 0
        ):
            raise ValueError("latency_samples must be a non-negative integer")


class SensorimotorTransducer:
    """Sample, perturb and delay raw mechanical state."""

    def __init__(
        self,
        *,
        sample_period_seconds: float,
        configuration: SensorimotorSensorConfiguration | None = None,
        seed: int = 0,
    ) -> None:
        if (
            not math.isfinite(sample_period_seconds)
            or sample_period_seconds <= 0.0
        ):
            raise ValueError("sample_period_seconds must be finite and positive")
        self.sample_period_seconds = float(sample_period_seconds)
        self.configuration = (
            configuration or SensorimotorSensorConfiguration()
        )
        self._rng = random.Random(int(seed))
        self._history: deque[dict] = deque(
            maxlen=self.configuration.latency_samples + 1
        )
        self._last_sample_id: int | None = None
        self._last_output: dict | None = None

    def reset(self) -> None:
        self._history.clear()
        self._last_sample_id = None
        self._last_output = None

    def _noisy(
        self,
        values: tuple[float, float, float],
        std: float,
    ) -> tuple[float, float, float]:
        if std == 0.0:
            return values
        return tuple(value + self._rng.gauss(0.0, std) for value in values)

    def _noisy_orientation(
        self,
        values: tuple[float, float, float, float],
        std: float,
    ) -> tuple[float, float, float, float]:
        if std == 0.0:
            return values
        return _quaternion(
            (
                value + self._rng.gauss(0.0, std)
                for value in values
            ),
            field="noisy orientation",
        )

    def sample(
        self,
        *,
        position: Iterable[float],
        orientation_xyzw: Iterable[float] = (0.0, 0.0, 0.0, 1.0),
        linear_velocity: Iterable[float],
        angular_velocity: Iterable[float],
        contact_count: float,
        sample_id: int,
    ) -> dict:
        if self._last_sample_id == int(sample_id):
            assert self._last_output is not None
            return dict(self._last_output)
        configuration = self.configuration
        physical = {
            "sensed_base_position": self._noisy(
                _vector(position, field="position"),
                configuration.position_noise_std,
            ),
            "sensed_base_orientation_xyzw": self._noisy_orientation(
                _quaternion(
                    orientation_xyzw,
                    field="orientation_xyzw",
                ),
                configuration.orientation_noise_std,
            ),
            "sensed_base_linear_velocity": self._noisy(
                _vector(linear_velocity, field="linear_velocity"),
                configuration.velocity_noise_std,
            ),
            "sensed_base_angular_velocity": self._noisy(
                _vector(angular_velocity, field="angular_velocity"),
                configuration.angular_noise_std,
            ),
            "sensed_contact_count": max(
                0.0,
                float(contact_count)
                + (
                    self._rng.gauss(0.0, configuration.contact_noise_std)
                    if configuration.contact_noise_std > 0.0
                    else 0.0
                ),
            ),
        }
        self._history.append(physical)
        delayed = self._history[0]
        result = {
            **delayed,
            "sensor_position_variance": (
                configuration.position_noise_std**2
            ),
            "sensor_orientation_variance": (
                configuration.orientation_noise_std**2
            ),
            "sensor_velocity_variance": (
                configuration.velocity_noise_std**2
            ),
            "sensor_angular_variance": (
                configuration.angular_noise_std**2
            ),
            "sensor_contact_variance": (
                configuration.contact_noise_std**2
            ),
            "sensor_sample_period_seconds": self.sample_period_seconds,
            "sensor_latency_seconds": (
                configuration.latency_samples * self.sample_period_seconds
            ),
            "sensor_requires_inference": float(
                configuration.latency_samples > 0
                or configuration.position_noise_std > 0.0
                or configuration.orientation_noise_std > 0.0
                or configuration.velocity_noise_std > 0.0
                or configuration.angular_noise_std > 0.0
                or configuration.contact_noise_std > 0.0
            ),
            "has_sensor_sample": 1.0,
        }
        self._last_sample_id = int(sample_id)
        self._last_output = result
        return dict(result)


def sensed_vector(observation: dict, channel: str) -> tuple[float, float, float]:
    """Read one declared sensor vector, with legacy raw-world fallback."""
    keys = {
        "position": ("sensed_base_position", "base_position"),
        "linear_velocity": (
            "sensed_base_linear_velocity",
            "base_linear_velocity",
        ),
        "angular_velocity": (
            "sensed_base_angular_velocity",
            "base_angular_velocity",
        ),
    }
    try:
        sensed_key, raw_key = keys[channel]
    except KeyError as exc:
        raise ValueError(f"unknown sensor channel {channel!r}") from exc
    return _vector(
        observation.get(sensed_key, observation[raw_key]),
        field=channel,
    )


def sensed_orientation(
    observation: dict,
) -> tuple[float, float, float, float]:
    """Read the delayed vestibular pose sample with legacy raw fallback."""
    return _quaternion(
        observation.get(
            "sensed_base_orientation_xyzw",
            observation["base_orientation_xyzw"],
        ),
        field="orientation",
    )


def sensor_receipt_attrs(before: dict, after: dict) -> dict[str, float]:
    """Flatten two physical sensor samples onto a graph receipt."""
    result: dict[str, float] = {
        "has_sensor_sample": float(after.get("has_sensor_sample", 0.0)),
        "sensor_position_variance": float(
            after.get("sensor_position_variance", 0.0)
        ),
        "sensor_orientation_variance": float(
            after.get("sensor_orientation_variance", 0.0)
        ),
        "sensor_velocity_variance": float(
            after.get("sensor_velocity_variance", 0.0)
        ),
        "sensor_angular_variance": float(
            after.get("sensor_angular_variance", 0.0)
        ),
        "sensor_contact_variance": float(
            after.get("sensor_contact_variance", 0.0)
        ),
        "sensor_sample_period_seconds": float(
            after.get("sensor_sample_period_seconds", 0.0)
        ),
        "sensor_latency_seconds": float(
            after.get("sensor_latency_seconds", 0.0)
        ),
        "sensor_requires_inference": float(
            after.get("sensor_requires_inference", 0.0)
        ),
        "actuator_activation_seconds": float(
            after.get("actuator_activation_seconds", 0.0)
        ),
        "sensed_pre_contact_count": float(
            before.get(
                "sensed_contact_count",
                before.get("contact_count", len(before.get("contacts", ()))),
            )
        ),
        "sensed_contact_count": float(
            after.get(
                "sensed_contact_count",
                after.get("contact_count", len(after.get("contacts", ()))),
            )
        ),
    }
    for prefix, sample in (("pre", before), ("post", after)):
        position = sensed_vector(sample, "position")
        linear = sensed_vector(sample, "linear_velocity")
        angular = sensed_vector(sample, "angular_velocity")
        for ordinal, axis in enumerate(("x", "y", "z")):
            result[f"sensed_{prefix}_{axis}"] = position[ordinal]
            result[f"sensed_{prefix}_v{axis}"] = linear[ordinal]
            result[f"sensed_{prefix}_w{axis}"] = angular[ordinal]
    return result


__all__ = [
    "SensorimotorSensorConfiguration",
    "SensorimotorTransducer",
    "sensed_orientation",
    "sensed_vector",
    "sensor_receipt_attrs",
]
