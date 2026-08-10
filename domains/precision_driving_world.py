"""Precision-driving plant and course instrumentation.

The vehicle dynamics remain those of :mod:`full_racing_world`.  This module
only supplies a wide skid pad and exact geometric receipts for a commanded
course.  It does not select manoeuvre phases or calculate actuator commands.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any

from domains.full_racing_world import (
    FullRacingWorld,
    RacingPlantConfig,
    _wrap_angle,
)
from domains.trajectory_geometry import preview_receipt


@dataclass(frozen=True)
class PrecisionDrivingPlantConfig(RacingPlantConfig):
    """Named assumptions for low-speed, combined-slip precision manoeuvres."""

    track_width_m: float = 160.0
    dry_grip: float = 1.18
    offtrack_grip: float = 1.18
    peak_engine_force_n: float = 15_000.0
    peak_brake_force_n: float = 24_000.0
    front_drive_force_fraction: float = 0.30
    front_brake_force_fraction: float = 0.58
    rear_tyre_grip_scale: float = 0.82
    combined_slip_coupling: float = 1.0
    smooth_tyre_saturation: bool = True
    combined_slip_transition_exponent: float = 8.0
    physics_hz: float = 500.0
    control_hz: float = 100.0
    preview_near_m: float = 6.0
    preview_middle_m: float = 14.0
    preview_far_m: float = 28.0


@dataclass(frozen=True)
class PrecisionCourse:
    """Externally declared geometry; cognition decides how to traverse it."""

    name: str
    direction: float
    radius_m: float


PRECISION_COURSES = {
    "drift_left": PrecisionCourse("drift_left", 1.0, 34.0),
    "drift_right": PrecisionCourse("drift_right", -1.0, 34.0),
    "donut_left": PrecisionCourse("donut_left", 1.0, 8.5),
    "donut_right": PrecisionCourse("donut_right", -1.0, 8.5),
}


class PrecisionDrivingWorld(FullRacingWorld):
    """Wide skid-pad world exposing target-circle geometry as observations."""

    backend = "deterministic_precision_driving_plant"

    def __init__(
        self,
        *,
        course: str = "drift_left",
        seed: int = 0,
        config: PrecisionDrivingPlantConfig | None = None,
    ) -> None:
        if course not in PRECISION_COURSES:
            raise ValueError(
                f"unknown precision course {course!r}; "
                f"expected one of {sorted(PRECISION_COURSES)}"
            )
        self.course = PRECISION_COURSES[course]
        super().__init__(
            seed=seed,
            config=config or PrecisionDrivingPlantConfig(),
            opponent_count=0,
        )

    def reset(self) -> dict[str, Any]:
        observation = super().reset()
        self._precision_start_x = self.x
        self._precision_start_y = self.y
        self._precision_start_yaw = self.unwrapped_yaw
        heading = self.yaw
        left_x = -math.sin(heading)
        left_y = math.cos(heading)
        self._course_center_x = (
            self.x + left_x * self.course.direction * self.course.radius_m
        )
        self._course_center_y = (
            self.y + left_y * self.course.direction * self.course.radius_m
        )
        self._course_start_radial_heading = math.atan2(
            self.y - self._course_center_y,
            self.x - self._course_center_x,
        )
        return self.observe()

    def _preview_receipt(
        self,
        radial_heading: float,
        lookahead_m: float,
    ) -> tuple[float, float, float]:
        """Return body-frame lateral, bearing, and tangent-heading errors."""
        target_radial_heading = (
            radial_heading
            + self.course.direction * lookahead_m / self.course.radius_m
        )
        target_x = (
            self._course_center_x
            + self.course.radius_m * math.cos(target_radial_heading)
        )
        target_y = (
            self._course_center_y
            + self.course.radius_m * math.sin(target_radial_heading)
        )
        tangent_heading = (
            target_radial_heading
            + self.course.direction * math.pi * 0.5
        )
        receipt = preview_receipt(
            observer_x_m=self.x,
            observer_y_m=self.y,
            observer_yaw_rad=self.yaw,
            target_x_m=target_x,
            target_y_m=target_y,
            target_heading_rad=tangent_heading,
        )
        return (
            receipt.lateral_m,
            receipt.bearing_error_rad,
            receipt.heading_error_rad,
        )

    def observe(self) -> dict[str, Any]:
        observation = super().observe()
        if not hasattr(self, "_course_center_x"):
            return observation
        center_dx = self.x - self._course_center_x
        center_dy = self.y - self._course_center_y
        radial_distance = math.hypot(center_dx, center_dy)
        radial_heading = math.atan2(center_dy, center_dx)
        tangent_heading = radial_heading + self.course.direction * math.pi * 0.5
        path_phase = (
            self.course.direction
            * (radial_heading - self._course_start_radial_heading)
        ) % (2.0 * math.pi)
        near = self._preview_receipt(
            radial_heading,
            self.config.preview_near_m,
        )
        middle = self._preview_receipt(
            radial_heading,
            self.config.preview_middle_m,
        )
        far = self._preview_receipt(
            radial_heading,
            self.config.preview_far_m,
        )
        observation.update({
            "precision_course_name": self.course.name,
            "precision_course_direction": self.course.direction,
            "precision_course_radius_m": self.course.radius_m,
            "precision_radial_error_m": radial_distance - self.course.radius_m,
            "precision_tangent_heading_error_rad": _wrap_angle(
                tangent_heading - self.yaw
            ),
            "precision_angular_travel_rad": (
                self.course.direction
                * (self.unwrapped_yaw - self._precision_start_yaw)
            ),
            "precision_path_phase_rad": path_phase,
            "precision_path_length_m": (
                2.0 * math.pi * self.course.radius_m
            ),
            "precision_path_lateral_error_m": (
                self.course.direction
                * (radial_distance - self.course.radius_m)
            ),
            "precision_path_curvature_now_inv_m": (
                self.course.direction / self.course.radius_m
            ),
            "precision_path_curvature_near_inv_m": (
                self.course.direction / self.course.radius_m
            ),
            "precision_path_curvature_middle_inv_m": (
                self.course.direction / self.course.radius_m
            ),
            "precision_path_curvature_far_inv_m": (
                self.course.direction / self.course.radius_m
            ),
            "precision_path_curvature_envelope_inv_m": (
                1.0 / self.course.radius_m
            ),
            "precision_preview_near_lateral_m": near[0],
            "precision_preview_near_bearing_rad": near[1],
            "precision_preview_near_heading_error_rad": near[2],
            "precision_preview_middle_lateral_m": middle[0],
            "precision_preview_middle_bearing_rad": middle[1],
            "precision_preview_middle_heading_error_rad": middle[2],
            "precision_preview_far_lateral_m": far[0],
            "precision_preview_far_bearing_rad": far[1],
            "precision_preview_far_heading_error_rad": far[2],
            "precision_displacement_m": math.hypot(
                self.x - self._precision_start_x,
                self.y - self._precision_start_y,
            ),
        })
        return observation
