"""Changing-curvature figure-eight gymkhana mechanics and geometry receipts."""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any

from domains.full_racing_world import FullRacingWorld, RacingPlantConfig
from domains.trajectory_geometry import preview_receipt


@dataclass(frozen=True)
class GymkhanaPlantConfig(RacingPlantConfig):
    track_width_m: float = 14.0
    dry_grip: float = 1.22
    wet_grip: float = 1.22
    offtrack_grip: float = 0.72
    peak_engine_force_n: float = 15_000.0
    peak_brake_force_n: float = 24_000.0
    front_drive_force_fraction: float = 0.30
    front_brake_force_fraction: float = 0.58
    rear_tyre_grip_scale: float = 0.84
    combined_slip_coupling: float = 1.0
    smooth_tyre_saturation: bool = True
    combined_slip_transition_exponent: float = 8.0
    physics_hz: float = 500.0
    control_hz: float = 100.0
    centerline_samples: int = 3072
    near_lookahead_m: float = 5.0
    middle_lookahead_m: float = 12.0
    far_lookahead_m: float = 24.0


class GymkhanaDrivingWorld(FullRacingWorld):
    """A continuous slalom/figure-eight path with sign-changing curvature."""

    backend = "deterministic_gymkhana_driving_plant"

    def __init__(
        self,
        *,
        seed: int = 0,
        config: GymkhanaPlantConfig | None = None,
    ) -> None:
        super().__init__(
            seed=seed,
            config=config or GymkhanaPlantConfig(),
            opponent_count=0,
        )

    def _build_track(self) -> None:
        """Sample a Gerono figure eight with a superposed slalom harmonic."""
        points: list[tuple[float, float]] = []
        sample_count = self.config.centerline_samples
        for index in range(sample_count):
            phase = 2.0 * math.pi * index / sample_count
            x = 62.0 * math.sin(phase)
            y = (
                31.0 * math.sin(phase) * math.cos(phase)
                + 3.2 * math.sin(5.0 * phase)
            )
            points.append((x, y))
        self._install_sampled_track(points)

    def _install_sampled_track(
        self, points: list[tuple[float, float]]
    ) -> None:
        sample_count = len(points)
        cumulative = [0.0]
        for index, point in enumerate(points):
            following = points[(index + 1) % sample_count]
            cumulative.append(
                cumulative[-1]
                + math.hypot(following[0] - point[0], following[1] - point[1])
            )
        headings: list[float] = []
        segment_lengths: list[float] = []
        for index in range(sample_count):
            previous = points[(index - 1) % sample_count]
            following = points[(index + 1) % sample_count]
            headings.append(math.atan2(
                following[1] - previous[1],
                following[0] - previous[0],
            ))
            segment_lengths.append(cumulative[index + 1] - cumulative[index])
        curvatures: list[float] = []
        for index in range(sample_count):
            heading_delta = (
                headings[(index + 1) % sample_count]
                - headings[(index - 1) % sample_count]
                + math.pi
            ) % (2.0 * math.pi) - math.pi
            distance = (
                segment_lengths[(index - 1) % sample_count]
                + segment_lengths[index]
            )
            curvatures.append(heading_delta / max(distance, 1e-9))
        self._points = points
        self._cumulative = cumulative
        self._headings = headings
        self._curvatures = curvatures
        self._segment_lengths = segment_lengths
        self.track_length_m = cumulative[-1]

    def _preview(self, distance_m: float):
        index = self._index_ahead(distance_m)
        target_x, target_y = self._points[index]
        return preview_receipt(
            observer_x_m=self.x,
            observer_y_m=self.y,
            observer_yaw_rad=self.yaw,
            target_x_m=target_x,
            target_y_m=target_y,
            target_heading_rad=self._headings[index],
        )

    def observe(self) -> dict[str, Any]:
        observation = super().observe()
        near = self._preview(self.config.near_lookahead_m)
        middle = self._preview(self.config.middle_lookahead_m)
        far = self._preview(self.config.far_lookahead_m)
        phase = 2.0 * math.pi * self.progress_m / self.track_length_m
        observation.update({
            "gymkhana_path_phase_rad": phase,
            "gymkhana_path_length_m": self.track_length_m,
            "gymkhana_path_lateral_error_m": observation["track_lateral_m"],
            "gymkhana_tangent_heading_error_rad": observation[
                "track_heading_error_rad"
            ],
            "gymkhana_path_curvature_now_inv_m": observation[
                "track_curvature_now_inv_m"
            ],
            "gymkhana_path_curvature_near_inv_m": observation[
                "track_curvature_near_inv_m"
            ],
            "gymkhana_path_curvature_middle_inv_m": observation[
                "track_curvature_middle_inv_m"
            ],
            "gymkhana_path_curvature_far_inv_m": observation[
                "track_curvature_far_inv_m"
            ],
            "gymkhana_path_curvature_envelope_inv_m": max(
                observation["track_curvature_envelope_near_inv_m"],
                observation["track_curvature_envelope_middle_inv_m"],
                observation["track_curvature_envelope_far_inv_m"],
            ),
            "gymkhana_preview_near_lateral_m": near.lateral_m,
            "gymkhana_preview_near_bearing_rad": near.bearing_error_rad,
            "gymkhana_preview_near_heading_error_rad": near.heading_error_rad,
            "gymkhana_preview_middle_lateral_m": middle.lateral_m,
            "gymkhana_preview_middle_bearing_rad": middle.bearing_error_rad,
            "gymkhana_preview_middle_heading_error_rad": (
                middle.heading_error_rad
            ),
            "gymkhana_preview_far_lateral_m": far.lateral_m,
            "gymkhana_preview_far_bearing_rad": far.bearing_error_rad,
            "gymkhana_preview_far_heading_error_rad": far.heading_error_rad,
        })
        return observation


__all__ = ["GymkhanaDrivingWorld", "GymkhanaPlantConfig"]
