"""Planar thrust-vectoring jet mechanics for attitude/trajectory experiments.

The plant deliberately owns only mechanics.  It accepts three continuous
effector commands and reports inertial motion, body-relative airflow, and
loads.  Target generation and control remain graph-native.

Unlike the conventional fixed-wing research plant, the drag model remains
defined for reverse body-relative airflow.  That makes a complete yaw
pirouette an honest momentum-and-authority experiment rather than an
extrapolation of a small-angle wing model.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any


def _clamp(value: float, lower: float, upper: float) -> float:
    return min(max(value, lower), upper)


@dataclass(frozen=True)
class VectoringJetConfig:
    mass_kg: float = 7_500.0
    yaw_inertia_kg_m2: float = 52_000.0
    air_density_kg_m3: float = 1.112
    axial_drag_area_m2: float = 8.0
    lateral_drag_area_m2: float = 19.0
    maximum_axial_thrust_n: float = 180_000.0
    maximum_lateral_vector_force_n: float = 250_000.0
    maximum_yaw_moment_nm: float = 900_000.0
    yaw_rate_damping_nm_per_rad_s: float = 80_000.0
    physics_hz: float = 500.0
    control_hz: float = 100.0
    initial_forward_speed_m_s: float = 80.0


class VectoringJetWorld:
    """Horizontal six-axis slice with unwrapped yaw and vectoring authority."""

    ACTION_FIELDS = ("throttle", "lateral_vector", "yaw_vector")
    backend = "deterministic_vectoring_jet_plant"

    def __init__(self, config: VectoringJetConfig | None = None) -> None:
        self.config = config or VectoringJetConfig()
        ratio = self.config.physics_hz / self.config.control_hz
        if not math.isclose(ratio, round(ratio), abs_tol=1e-9):
            raise ValueError("physics_hz/control_hz must be integral")
        self._substeps = int(round(ratio))
        self._dt = 1.0 / self.config.physics_hz
        self.reset()

    def reset(self) -> dict[str, Any]:
        self.x_m = 0.0
        self.y_m = 0.0
        self.vx_m_s = self.config.initial_forward_speed_m_s
        self.vy_m_s = 0.0
        self.unwrapped_yaw_rad = 0.0
        self.yaw_rate_rad_s = 0.0
        self.time_s = 0.0
        self._last_action = {field: 0.0 for field in self.ACTION_FIELDS}
        self._last_body_velocity = (
            self.config.initial_forward_speed_m_s,
            0.0,
        )
        self._last_acceleration = (0.0, 0.0)
        self._last_dynamic_pressure_pa = 0.0
        self._last_yaw_moment_nm = 0.0
        return self.observe()

    def _integrate(self, action: dict[str, float]) -> None:
        config = self.config
        yaw = self.unwrapped_yaw_rad
        cosine = math.cos(yaw)
        sine = math.sin(yaw)
        body_vx = cosine * self.vx_m_s + sine * self.vy_m_s
        body_vy = -sine * self.vx_m_s + cosine * self.vy_m_s
        speed_squared = body_vx * body_vx + body_vy * body_vy
        dynamic_pressure = 0.5 * config.air_density_kg_m3 * speed_squared

        axial_drag = (
            0.5
            * config.air_density_kg_m3
            * config.axial_drag_area_m2
            * body_vx
            * abs(body_vx)
        )
        lateral_drag = (
            0.5
            * config.air_density_kg_m3
            * config.lateral_drag_area_m2
            * body_vy
            * abs(body_vy)
        )
        body_force_x = (
            action["throttle"] * config.maximum_axial_thrust_n
            - axial_drag
        )
        body_force_y = (
            action["lateral_vector"]
            * config.maximum_lateral_vector_force_n
            - lateral_drag
        )
        world_force_x = cosine * body_force_x - sine * body_force_y
        world_force_y = sine * body_force_x + cosine * body_force_y
        acceleration_x = world_force_x / config.mass_kg
        acceleration_y = world_force_y / config.mass_kg
        self.vx_m_s += acceleration_x * self._dt
        self.vy_m_s += acceleration_y * self._dt
        self.x_m += self.vx_m_s * self._dt
        self.y_m += self.vy_m_s * self._dt

        yaw_moment = (
            action["yaw_vector"] * config.maximum_yaw_moment_nm
            - config.yaw_rate_damping_nm_per_rad_s * self.yaw_rate_rad_s
        )
        self.yaw_rate_rad_s += (
            yaw_moment / config.yaw_inertia_kg_m2
        ) * self._dt
        self.unwrapped_yaw_rad += self.yaw_rate_rad_s * self._dt
        self.time_s += self._dt
        self._last_body_velocity = (body_vx, body_vy)
        self._last_acceleration = (acceleration_x, acceleration_y)
        self._last_dynamic_pressure_pa = dynamic_pressure
        self._last_yaw_moment_nm = yaw_moment

    def step(self, action: dict[str, float]) -> dict[str, Any]:
        missing = set(self.ACTION_FIELDS) - set(action)
        if missing:
            raise ValueError(f"vectoring-jet action is missing {sorted(missing)}")
        normalized = {
            "throttle": _clamp(float(action["throttle"]), 0.0, 1.0),
            "lateral_vector": _clamp(
                float(action["lateral_vector"]), -1.0, 1.0
            ),
            "yaw_vector": _clamp(float(action["yaw_vector"]), -1.0, 1.0),
        }
        self._last_action = normalized
        for _ in range(self._substeps):
            self._integrate(normalized)
        return self.observe()

    def observe(self) -> dict[str, Any]:
        speed = math.hypot(self.vx_m_s, self.vy_m_s)
        velocity_heading = math.atan2(self.vy_m_s, self.vx_m_s)
        return {
            "time_s": self.time_s,
            "x_m": self.x_m,
            "y_m": self.y_m,
            "vx_m_s": self.vx_m_s,
            "vy_m_s": self.vy_m_s,
            "speed_m_s": speed,
            "velocity_heading_rad": velocity_heading,
            "body_vx_m_s": self._last_body_velocity[0],
            "body_vy_m_s": self._last_body_velocity[1],
            "unwrapped_yaw_rad": self.unwrapped_yaw_rad,
            "yaw_rad": math.atan2(
                math.sin(self.unwrapped_yaw_rad),
                math.cos(self.unwrapped_yaw_rad),
            ),
            "yaw_rate_rad_s": self.yaw_rate_rad_s,
            "acceleration_x_m_s2": self._last_acceleration[0],
            "acceleration_y_m_s2": self._last_acceleration[1],
            "dynamic_pressure_pa": self._last_dynamic_pressure_pa,
            "yaw_moment_nm": self._last_yaw_moment_nm,
            "last_action": dict(self._last_action),
        }


__all__ = ["VectoringJetConfig", "VectoringJetWorld"]
