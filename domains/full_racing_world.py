"""Deterministic full-race vehicle dynamics behind a policy-free I/O boundary.

The world owns geometry, opponents, damage injection, and physical integration.
It deliberately contains no racing line, target-speed, recovery, overtaking, or
control policy.  Those decisions are graph-native in ``racing_cognition``.

The plant is a load-sensitive dynamic bicycle model with a friction ellipse,
longitudinal load transfer, speed-dependent aerodynamics, thermal tyre/brake
state, wear, fuel use, off-track terrain, collisions, wet surface zones, and
independently degraded steering/braking/power/aerodynamic authority.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import random
from typing import Any, Iterable


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def _wrap_angle(value: float) -> float:
    return (value + math.pi) % (2.0 * math.pi) - math.pi


@dataclass(frozen=True)
class RacingPlantConfig:
    """Named physical and numerical assumptions for the benchmark plant."""

    mass_kg: float = 1180.0
    yaw_inertia_kg_m2: float = 1650.0
    wheelbase_m: float = 2.62
    cg_to_front_m: float = 1.12
    cg_height_m: float = 0.47
    track_width_m: float = 12.0
    car_length_m: float = 4.55
    car_width_m: float = 1.88
    wheel_track_m: float = 1.62
    max_steer_rad: float = 0.58
    cornering_stiffness_front_n_rad: float = 92000.0
    cornering_stiffness_rear_n_rad: float = 104000.0
    peak_engine_force_n: float = 9200.0
    peak_brake_force_n: float = 19000.0
    front_drive_force_fraction: float = 0.4
    front_brake_force_fraction: float = 0.61
    combined_slip_coupling: float = 0.0
    smooth_tyre_saturation: bool = False
    combined_slip_transition_exponent: float = 8.0
    longitudinal_wear_rate_per_utilization_m: float = 0.0000008
    rolling_resistance: float = 0.014
    drag_area_m2: float = 0.72
    base_lift_area_m2: float = -1.45
    active_lift_area_m2: float = -2.2
    air_density_kg_m3: float = 1.225
    gravity_m_s2: float = 9.80665
    dry_grip: float = 1.35
    wet_grip: float = 0.72
    offtrack_grip: float = 0.58
    front_tyre_grip_scale: float = 1.0
    rear_tyre_grip_scale: float = 1.0
    fuel_capacity_l: float = 52.0
    fuel_energy_density_j_l: float = 34_200_000.0
    combustion_efficiency: float = 0.29
    idle_fuel_rate_l_s: float = 0.00045
    physics_hz: float = 250.0
    control_hz: float = 50.0
    centerline_samples: int = 2048
    near_lookahead_m: float = 18.0
    middle_lookahead_m: float = 55.0
    far_lookahead_m: float = 110.0
    race_laps: int = 4
    pit_entry_length_m: float = 72.0
    pit_speed_limit_m_s: float = 13.0
    pit_service_duration_s: float = 5.0


@dataclass(frozen=True)
class RacingDamage:
    """A hidden, abrupt physical change applied during a race."""

    onset_s: float
    steering_retention: float = 1.0
    power_retention: float = 1.0
    front_brake_retention: float = 1.0
    rear_brake_retention: float = 1.0
    aero_retention: float = 1.0
    yaw_bias_nm: float = 0.0


@dataclass
class _Opponent:
    progress_m: float
    speed_m_s: float
    lateral_m: float
    phase: float


class FullRacingWorld:
    """A closed-circuit multi-car race with exact continuous action receipts."""

    ACTION_FIELDS = (
        "steering",
        "throttle",
        "brake",
        "drive_front_left",
        "drive_front_right",
        "drive_rear_left",
        "drive_rear_right",
        "brake_front_left",
        "brake_front_right",
        "brake_rear_left",
        "brake_rear_right",
        "front_wing",
        "rear_wing",
        "gear",
        "pit_request",
    )

    def __init__(
        self,
        *,
        seed: int = 0,
        config: RacingPlantConfig | None = None,
        damage: RacingDamage | None = None,
        opponent_count: int = 3,
    ) -> None:
        self.config = config or RacingPlantConfig()
        if self.config.control_hz > self.config.physics_hz:
            raise ValueError("control_hz cannot exceed physics_hz")
        ratio = self.config.physics_hz / self.config.control_hz
        if not math.isclose(ratio, round(ratio), rel_tol=0.0, abs_tol=1e-9):
            raise ValueError("physics_hz/control_hz must be integral")
        self._substeps = int(round(ratio))
        self._dt = 1.0 / self.config.physics_hz
        self._rng = random.Random(seed)
        self._damage = damage
        self._opponent_count = opponent_count
        self._build_track()
        self.reset()

    def _build_track(self) -> None:
        """Sample a smooth asymmetric circuit and its differential geometry."""
        sample_count = self.config.centerline_samples
        points: list[tuple[float, float]] = []
        for index in range(sample_count):
            phase = 2.0 * math.pi * index / sample_count
            # Named harmonic circuit construction, not a driving policy.
            x = (
                185.0 * math.cos(phase)
                + 26.0 * math.cos(3.0 * phase)
                - 11.0 * math.sin(5.0 * phase)
            )
            y = (
                122.0 * math.sin(phase)
                + 19.0 * math.sin(2.0 * phase)
                + 8.0 * math.cos(4.0 * phase)
            )
            points.append((x, y))

        cumulative = [0.0]
        for index in range(sample_count):
            x0, y0 = points[index]
            x1, y1 = points[(index + 1) % sample_count]
            cumulative.append(cumulative[-1] + math.hypot(x1 - x0, y1 - y0))
        self.track_length_m = cumulative[-1]
        headings: list[float] = []
        curvatures: list[float] = []
        segment_lengths: list[float] = []
        for index in range(sample_count):
            previous = points[(index - 1) % sample_count]
            following = points[(index + 1) % sample_count]
            heading = math.atan2(
                following[1] - previous[1],
                following[0] - previous[0],
            )
            headings.append(heading)
            segment_length = cumulative[index + 1] - cumulative[index]
            segment_lengths.append(segment_length)
        for index in range(sample_count):
            heading_delta = _wrap_angle(
                headings[(index + 1) % sample_count]
                - headings[(index - 1) % sample_count]
            )
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

    def reset(self) -> dict[str, Any]:
        start_index = 0
        self.x, self.y = self._points[start_index]
        self.yaw = self._headings[start_index]
        self.unwrapped_yaw = self.yaw
        self.vx = 4.0
        self.vy = 0.0
        self.yaw_rate = 0.0
        self.progress_m = 0.0
        self._previous_progress_m = 0.0
        self.laps = 0
        self.time_s = 0.0
        self.fuel_l = self.config.fuel_capacity_l
        self.damage = 0.0
        self.tyre_temperature_c = [72.0] * 4
        self.tyre_condition = [1.0] * 4
        self.brake_temperature_c = [110.0] * 4
        self.offtrack_time_s = 0.0
        self.collisions = 0
        self.pit_stops = 0
        self._pit_service_remaining_s = 0.0
        self._pit_serviced_this_visit = False
        self._last_collision_time = -math.inf
        self._track_index = start_index
        self._last_action = {
            "steering": 0.0,
            "throttle": 0.0,
            "brake": 0.0,
            "drive_front_left": 0.0,
            "drive_front_right": 0.0,
            "drive_rear_left": 0.0,
            "drive_rear_right": 0.0,
            "brake_front_left": 0.0,
            "brake_front_right": 0.0,
            "brake_rear_left": 0.0,
            "brake_rear_right": 0.0,
            "front_wing": 0.0,
            "rear_wing": 0.0,
            "gear": 1,
            "pit_request": 0,
        }
        self._opponents = [
            _Opponent(
                progress_m=(42.0 + 61.0 * ordinal) % self.track_length_m,
                speed_m_s=29.0 + 2.5 * (ordinal % 3),
                lateral_m=(-1.8, 0.0, 1.6)[ordinal % 3],
                phase=self._rng.uniform(0.0, 2.0 * math.pi),
            )
            for ordinal in range(self._opponent_count)
        ]
        self._last_forces = {
            "lateral_accel_m_s2": 0.0,
            "longitudinal_accel_m_s2": 0.0,
            "front_slip_rad": 0.0,
            "rear_slip_rad": 0.0,
            "front_normal_load_n": self.config.mass_kg
            * self.config.gravity_m_s2
            * 0.5,
            "rear_normal_load_n": self.config.mass_kg
            * self.config.gravity_m_s2
            * 0.5,
            "front_left_longitudinal_force_n": 0.0,
            "front_right_longitudinal_force_n": 0.0,
            "rear_left_longitudinal_force_n": 0.0,
            "rear_right_longitudinal_force_n": 0.0,
            "differential_yaw_moment_nm": 0.0,
        }
        return self.observe()

    def _index_ahead(self, distance_m: float) -> int:
        target = (self.progress_m + distance_m) % self.track_length_m
        low = 0
        high = len(self._cumulative) - 1
        while low + 1 < high:
            middle = (low + high) // 2
            if self._cumulative[middle] <= target:
                low = middle
            else:
                high = middle
        return low % len(self._points)

    def _curvature_envelope_ahead(
        self,
        start_distance_m: float,
        end_distance_m: float,
    ) -> float:
        """Return the largest absolute sampled curvature in a sensory arc."""
        start_index = self._index_ahead(start_distance_m)
        end_index = self._index_ahead(end_distance_m)
        values: list[float] = []
        index = start_index
        while True:
            values.append(abs(self._curvatures[index]))
            if index == end_index:
                break
            index = (index + 1) % len(self._curvatures)
        return max(values, default=0.0)

    def _project_to_track(self) -> tuple[int, float]:
        """Project locally; physics continuity makes a global policy unnecessary."""
        sample_count = len(self._points)
        search_radius = max(8, sample_count // 96)
        candidates: Iterable[int] = (
            (self._track_index + offset) % sample_count
            for offset in range(-search_radius, search_radius + 1)
        )
        index = min(
            candidates,
            key=lambda candidate: (
                (self.x - self._points[candidate][0]) ** 2
                + (self.y - self._points[candidate][1]) ** 2
            ),
        )
        center_x, center_y = self._points[index]
        heading = self._headings[index]
        normal_x = -math.sin(heading)
        normal_y = math.cos(heading)
        lateral = (
            (self.x - center_x) * normal_x
            + (self.y - center_y) * normal_y
        )
        self._track_index = index
        self.progress_m = self._cumulative[index]
        return index, lateral

    def _surface_grip(self, progress_m: float, lateral_m: float) -> float:
        phase = progress_m / self.track_length_m
        wet = (
            0.18 <= phase <= 0.29
            or 0.63 <= phase <= 0.71
        )
        on_track = abs(lateral_m) <= self.config.track_width_m * 0.5
        if not on_track:
            return self.config.offtrack_grip
        return self.config.wet_grip if wet else self.config.dry_grip

    def _damage_authority(self) -> RacingDamage:
        if self._damage is None or self.time_s < self._damage.onset_s:
            return RacingDamage(onset_s=math.inf)
        return self._damage

    def _opponent_pose(
        self,
        opponent: _Opponent,
    ) -> tuple[float, float, float]:
        saved_progress = self.progress_m
        self.progress_m = opponent.progress_m
        index = self._index_ahead(0.0)
        self.progress_m = saved_progress
        center_x, center_y = self._points[index]
        heading = self._headings[index]
        x = center_x - math.sin(heading) * opponent.lateral_m
        y = center_y + math.cos(heading) * opponent.lateral_m
        return x, y, heading

    def _advance_opponents(self) -> None:
        for opponent in self._opponents:
            curvature = abs(self._curvatures[self._index_for_progress(
                opponent.progress_m
            )])
            geometric_limit = math.sqrt(
                self.config.dry_grip
                * self.config.gravity_m_s2
                / max(curvature, 1.0 / 220.0)
            )
            nominal = opponent.speed_m_s + 1.3 * math.sin(
                self.time_s * 0.19 + opponent.phase
            )
            speed = min(nominal, geometric_limit * 0.88)
            opponent.progress_m = (
                opponent.progress_m + max(8.0, speed) * self._dt
            ) % self.track_length_m

    def _index_for_progress(self, progress_m: float) -> int:
        saved = self.progress_m
        self.progress_m = progress_m
        index = self._index_ahead(0.0)
        self.progress_m = saved
        return index

    def _integrate(self, action: dict[str, float | int]) -> None:
        config = self.config
        index, lateral_m = self._project_to_track()
        grip = self._surface_grip(self.progress_m, lateral_m)
        authority = self._damage_authority()

        steering = float(action["steering"])
        steering *= config.max_steer_rad * authority.steering_retention
        throttle = float(action["throttle"]) * authority.power_retention
        brake = float(action["brake"])
        wheel_drive_commands = [
            float(action["drive_front_left"]) * authority.power_retention,
            float(action["drive_front_right"]) * authority.power_retention,
            float(action["drive_rear_left"]) * authority.power_retention,
            float(action["drive_rear_right"]) * authority.power_retention,
        ]
        wheel_brake_commands = [
            float(action["brake_front_left"])
            * authority.front_brake_retention,
            float(action["brake_front_right"])
            * authority.front_brake_retention,
            float(action["brake_rear_left"])
            * authority.rear_brake_retention,
            float(action["brake_rear_right"])
            * authority.rear_brake_retention,
        ]
        front_wing = float(action["front_wing"]) * authority.aero_retention
        rear_wing = float(action["rear_wing"]) * authority.aero_retention
        speed = max(0.0, math.hypot(self.vx, self.vy))
        pit_request = bool(action["pit_request"])
        in_pit_entry = (
            self.progress_m <= config.pit_entry_length_m
            or self.progress_m >= (
                self.track_length_m - config.pit_entry_length_m * 0.35
            )
        )
        if not in_pit_entry:
            self._pit_serviced_this_visit = False
        if (
            pit_request
            and in_pit_entry
            and speed <= config.pit_speed_limit_m_s
            and self._pit_service_remaining_s <= 0.0
            and not self._pit_serviced_this_visit
        ):
            self._pit_service_remaining_s = config.pit_service_duration_s
            self.pit_stops += 1
            self._pit_serviced_this_visit = True
        if self._pit_service_remaining_s > 0.0:
            throttle = 0.0
            brake = 1.0
            wheel_drive_commands = [0.0] * 4
            wheel_brake_commands = [1.0] * 4
            self._pit_service_remaining_s = max(
                0.0,
                self._pit_service_remaining_s - self._dt,
            )
            if self._pit_service_remaining_s == 0.0:
                self.fuel_l = config.fuel_capacity_l
                self.tyre_condition = [1.0] * 4
                self.tyre_temperature_c = [78.0] * 4
                self.damage *= 0.35

        dynamic_pressure = 0.5 * config.air_density_kg_m3 * speed * speed
        drag = dynamic_pressure * config.drag_area_m2
        downforce = -dynamic_pressure * (
            config.base_lift_area_m2
            + config.active_lift_area_m2 * 0.5 * (front_wing + rear_wing)
        )
        weight = config.mass_kg * config.gravity_m_s2
        static_front_fraction = (
            config.wheelbase_m - config.cg_to_front_m
        ) / config.wheelbase_m
        estimated_longitudinal = self._last_forces[
            "longitudinal_accel_m_s2"
        ]
        transfer = (
            config.mass_kg
            * estimated_longitudinal
            * config.cg_height_m
            / config.wheelbase_m
        )
        aero_front_fraction = _clamp(
            0.5 + 0.22 * (front_wing - rear_wing),
            0.25,
            0.75,
        )
        front_load = max(
            weight * static_front_fraction
            - transfer
            + downforce * aero_front_fraction,
            weight * 0.12,
        )
        rear_load = max(
            weight * (1.0 - static_front_fraction)
            + transfer
            + downforce * (1.0 - aero_front_fraction),
            weight * 0.12,
        )

        velocity_floor = 1.5
        front_slip = steering - math.atan2(
            self.vy + config.cg_to_front_m * self.yaw_rate,
            max(abs(self.vx), velocity_floor),
        )
        rear_arm = config.wheelbase_m - config.cg_to_front_m
        rear_slip = -math.atan2(
            self.vy - rear_arm * self.yaw_rate,
            max(abs(self.vx), velocity_floor),
        )
        tyre_health_front = sum(self.tyre_condition[:2]) * 0.5
        tyre_health_rear = sum(self.tyre_condition[2:]) * 0.5
        front_capacity = (
            grip
            * config.front_tyre_grip_scale
            * tyre_health_front
            * front_load
        )
        rear_capacity = (
            grip
            * config.rear_tyre_grip_scale
            * tyre_health_rear
            * rear_load
        )
        if config.smooth_tyre_saturation:
            front_lateral = front_capacity * math.tanh(
                config.cornering_stiffness_front_n_rad
                * front_slip
                / max(front_capacity, 1.0)
            )
            rear_lateral = rear_capacity * math.tanh(
                config.cornering_stiffness_rear_n_rad
                * rear_slip
                / max(rear_capacity, 1.0)
            )
        else:
            front_lateral = _clamp(
                config.cornering_stiffness_front_n_rad * front_slip,
                -front_capacity,
                front_capacity,
            )
            rear_lateral = _clamp(
                config.cornering_stiffness_rear_n_rad * rear_slip,
                -rear_capacity,
                rear_capacity,
            )

        gear = max(1, int(action["gear"]))
        gear_force_factor = _clamp(1.2 - 0.075 * (gear - 1), 0.62, 1.2)
        front_drive_fraction = config.front_drive_force_fraction
        rear_drive_fraction = 1.0 - front_drive_fraction
        front_brake_fraction = config.front_brake_force_fraction
        rear_brake_fraction = 1.0 - front_brake_fraction
        normal_loads = [
            front_load * 0.5,
            front_load * 0.5,
            rear_load * 0.5,
            rear_load * 0.5,
        ]
        lateral_forces = [
            front_lateral * 0.5,
            front_lateral * 0.5,
            rear_lateral * 0.5,
            rear_lateral * 0.5,
        ]
        drive_force_fractions = [
            front_drive_fraction * 0.5,
            front_drive_fraction * 0.5,
            rear_drive_fraction * 0.5,
            rear_drive_fraction * 0.5,
        ]
        brake_force_fractions = [
            front_brake_fraction * 0.5,
            front_brake_fraction * 0.5,
            rear_brake_fraction * 0.5,
            rear_brake_fraction * 0.5,
        ]
        wheel_force_capacities: list[float] = []
        wheel_drive_forces: list[float] = []
        wheel_brake_forces: list[float] = []
        wheel_longitudinal_forces: list[float] = []
        wheel_lateral_forces: list[float] = []
        for wheel in range(4):
            axle_grip_scale = (
                config.front_tyre_grip_scale
                if wheel < 2
                else config.rear_tyre_grip_scale
            )
            capacity = (
                grip
                * axle_grip_scale
                * self.tyre_condition[wheel]
                * normal_loads[wheel]
            )
            longitudinal_capacity = math.sqrt(max(
                0.0,
                capacity * capacity - lateral_forces[wheel] ** 2,
            ))
            drive_force = (
                wheel_drive_commands[wheel]
                * config.peak_engine_force_n
                * drive_force_fractions[wheel]
                * gear_force_factor
            )
            brake_force = (
                wheel_brake_commands[wheel]
                * config.peak_brake_force_n
                * brake_force_fractions[wheel]
            )
            requested_longitudinal = drive_force - brake_force
            combined_force = math.hypot(
                requested_longitudinal,
                lateral_forces[wheel],
            )
            if config.smooth_tyre_saturation:
                transition_exponent = max(
                    2.0,
                    config.combined_slip_transition_exponent,
                )
                normalized_force = combined_force / max(capacity, 1.0)
                combined_scale = (
                    1.0 + normalized_force ** transition_exponent
                ) ** (-1.0 / transition_exponent)
            else:
                combined_scale = min(
                    1.0,
                    capacity / max(combined_force, 1.0),
                )
            coupled_longitudinal = requested_longitudinal * combined_scale
            coupled_lateral = lateral_forces[wheel] * combined_scale
            legacy_longitudinal = _clamp(
                requested_longitudinal,
                -longitudinal_capacity,
                longitudinal_capacity,
            )
            coupling = _clamp(config.combined_slip_coupling, 0.0, 1.0)
            wheel_force_capacities.append(capacity)
            wheel_drive_forces.append(drive_force)
            wheel_brake_forces.append(brake_force)
            wheel_longitudinal_forces.append(
                legacy_longitudinal
                + coupling * (coupled_longitudinal - legacy_longitudinal)
            )
            wheel_lateral_forces.append(
                lateral_forces[wheel]
                + coupling * (coupled_lateral - lateral_forces[wheel])
            )
        front_lateral = sum(wheel_lateral_forces[:2])
        rear_lateral = sum(wheel_lateral_forces[2:])
        front_long = sum(wheel_longitudinal_forces[:2])
        rear_long = sum(wheel_longitudinal_forces[2:])
        differential_yaw_moment = (
            (
                wheel_longitudinal_forces[1]
                + wheel_longitudinal_forces[3]
                - wheel_longitudinal_forces[0]
                - wheel_longitudinal_forces[2]
            )
            * config.wheel_track_m
            * 0.5
        )
        rolling = (
            config.rolling_resistance * weight
            * (2.8 if abs(lateral_m) > config.track_width_m * 0.5 else 1.0)
        )
        resistance_sign = 1.0 if self.vx >= 0.0 else -1.0
        longitudinal_force = (
            front_long * math.cos(steering)
            + rear_long
            - (drag + rolling) * resistance_sign
        )
        lateral_force = front_lateral * math.cos(steering) + rear_lateral
        longitudinal_accel = (
            longitudinal_force / config.mass_kg
            + self.vy * self.yaw_rate
        )
        lateral_accel = (
            lateral_force / config.mass_kg
            - self.vx * self.yaw_rate
        )
        yaw_accel = (
            config.cg_to_front_m * front_lateral * math.cos(steering)
            - rear_arm * rear_lateral
            + differential_yaw_moment
            + authority.yaw_bias_nm
            + dynamic_pressure * 0.08 * (rear_wing - front_wing)
        ) / config.yaw_inertia_kg_m2

        proposed_vx = max(
            -3.0,
            self.vx + longitudinal_accel * self._dt,
        )
        if (
            self.vx >= 0.0
            and proposed_vx < 0.0
            and sum(wheel_drive_commands) <= 1e-9
        ):
            proposed_vx = 0.0
        self.vx = proposed_vx
        self.vy += lateral_accel * self._dt
        self.yaw_rate += yaw_accel * self._dt
        self.unwrapped_yaw += self.yaw_rate * self._dt
        self.yaw = _wrap_angle(self.yaw + self.yaw_rate * self._dt)
        world_vx = self.vx * math.cos(self.yaw) - self.vy * math.sin(self.yaw)
        world_vy = self.vx * math.sin(self.yaw) + self.vy * math.cos(self.yaw)
        self.x += world_vx * self._dt
        self.y += world_vy * self._dt

        slip_energy = (
            abs(front_lateral * front_slip)
            + abs(rear_lateral * rear_slip)
        ) * speed
        for wheel in range(4):
            axle_slip = abs(front_slip if wheel < 2 else rear_slip)
            longitudinal_utilization = (
                abs(wheel_longitudinal_forces[wheel])
                / max(wheel_force_capacities[wheel], 1.0)
            )
            self.tyre_temperature_c[wheel] += (
                0.0000022 * slip_energy
                - 0.025 * (self.tyre_temperature_c[wheel] - 78.0)
            ) * self._dt
            thermal_penalty = max(
                0.0,
                abs(self.tyre_temperature_c[wheel] - 92.0) - 18.0,
            )
            wear_rate = (
                0.0000026 * axle_slip * speed
                + 0.00000011 * thermal_penalty
                + config.longitudinal_wear_rate_per_utilization_m
                * longitudinal_utilization
                * speed
            )
            self.tyre_condition[wheel] = max(
                0.25,
                self.tyre_condition[wheel] - wear_rate * self._dt,
            )
            self.brake_temperature_c[wheel] += (
                0.000014 * wheel_brake_forces[wheel] * speed
                - 0.055 * (self.brake_temperature_c[wheel] - 95.0)
            ) * self._dt
        drive_force = sum(wheel_drive_forces)
        fuel_rate_l_s = (
            max(0.0, drive_force * speed)
            / (
                config.fuel_energy_density_j_l
                * config.combustion_efficiency
            )
            + config.idle_fuel_rate_l_s * max(throttle, 0.08)
        )
        self.fuel_l = max(0.0, self.fuel_l - fuel_rate_l_s * self._dt)
        if abs(lateral_m) > config.track_width_m * 0.5:
            self.offtrack_time_s += self._dt
            self.damage += max(0.0, speed - 18.0) * 0.0015 * self._dt

        self._advance_opponents()
        for opponent in self._opponents:
            other_x, other_y, _ = self._opponent_pose(opponent)
            collision_radius = 0.5 * math.hypot(
                config.car_length_m,
                config.car_width_m,
            )
            if (
                math.hypot(self.x - other_x, self.y - other_y)
                < collision_radius
                and self.time_s - self._last_collision_time > 0.5
            ):
                self.collisions += 1
                self._last_collision_time = self.time_s
                self.damage += max(1.0, speed * 0.12)
                self.vx *= 0.72
                self.vy *= 0.45
                self.yaw_rate *= 0.6

        self.time_s += self._dt
        self._last_forces = {
            # An IMU senses specific lateral force, while ``lateral_accel`` is
            # the body-frame velocity derivative after the rotating-frame
            # correction.
            "lateral_accel_m_s2": lateral_force / config.mass_kg,
            "longitudinal_accel_m_s2": longitudinal_accel,
            "front_slip_rad": front_slip,
            "rear_slip_rad": rear_slip,
            "front_normal_load_n": front_load,
            "rear_normal_load_n": rear_load,
            "front_left_longitudinal_force_n": wheel_longitudinal_forces[0],
            "front_right_longitudinal_force_n": wheel_longitudinal_forces[1],
            "rear_left_longitudinal_force_n": wheel_longitudinal_forces[2],
            "rear_right_longitudinal_force_n": wheel_longitudinal_forces[3],
            "differential_yaw_moment_nm": differential_yaw_moment,
        }

    def step(self, action: dict[str, float | int]) -> dict[str, Any]:
        missing = set(self.ACTION_FIELDS) - set(action)
        if missing:
            raise ValueError(f"racing action is missing {sorted(missing)}")
        normalized: dict[str, float | int] = {
            "steering": _clamp(float(action["steering"]), -1.0, 1.0),
            "throttle": _clamp(float(action["throttle"]), 0.0, 1.0),
            "brake": _clamp(float(action["brake"]), 0.0, 1.0),
            "drive_front_left": _clamp(
                float(action["drive_front_left"]), 0.0, 1.0
            ),
            "drive_front_right": _clamp(
                float(action["drive_front_right"]), 0.0, 1.0
            ),
            "drive_rear_left": _clamp(
                float(action["drive_rear_left"]), 0.0, 1.0
            ),
            "drive_rear_right": _clamp(
                float(action["drive_rear_right"]), 0.0, 1.0
            ),
            "brake_front_left": _clamp(
                float(action["brake_front_left"]), 0.0, 1.0
            ),
            "brake_front_right": _clamp(
                float(action["brake_front_right"]), 0.0, 1.0
            ),
            "brake_rear_left": _clamp(
                float(action["brake_rear_left"]), 0.0, 1.0
            ),
            "brake_rear_right": _clamp(
                float(action["brake_rear_right"]), 0.0, 1.0
            ),
            "front_wing": _clamp(float(action["front_wing"]), 0.0, 1.0),
            "rear_wing": _clamp(float(action["rear_wing"]), 0.0, 1.0),
            "gear": max(1, min(8, int(round(float(action["gear"]))))),
            "pit_request": int(bool(action["pit_request"])),
        }
        if normalized["throttle"] and normalized["brake"]:
            raise ValueError("throttle and brake commands must be exclusive")
        for axle, side in (
            ("front", "left"),
            ("front", "right"),
            ("rear", "left"),
            ("rear", "right"),
        ):
            if (
                normalized[f"drive_{axle}_{side}"]
                and normalized[f"brake_{axle}_{side}"]
            ):
                raise ValueError(
                    f"{axle}-{side} wheel drive and brake must be exclusive"
                )
        self._last_action = normalized
        previous_progress = self.progress_m
        for _ in range(self._substeps):
            self._integrate(normalized)
        self._project_to_track()
        if (
            previous_progress > self.track_length_m * 0.8
            and self.progress_m < self.track_length_m * 0.2
            and self.vx > 0.0
        ):
            self.laps += 1
        self._previous_progress_m = previous_progress
        return self.observe()

    def observe(self) -> dict[str, Any]:
        index, lateral_m = self._project_to_track()
        heading_error = _wrap_angle(self._headings[index] - self.yaw)
        speed = math.hypot(self.vx, self.vy)
        slip_angle = math.atan2(self.vy, max(abs(self.vx), 1e-9))
        grip = self._surface_grip(self.progress_m, lateral_m)
        nearest_gap = self.track_length_m
        nearest_lateral = 0.0
        nearest_speed = speed
        nearest_closing = 0.0
        for opponent in self._opponents:
            forward_gap = (
                opponent.progress_m - self.progress_m
            ) % self.track_length_m
            if forward_gap < nearest_gap:
                nearest_gap = forward_gap
                nearest_lateral = opponent.lateral_m - lateral_m
                nearest_speed = opponent.speed_m_s
                nearest_closing = speed - opponent.speed_m_s
        engine_rpm = _clamp(
            900.0 + max(self.vx, 0.0) * (300.0 - 30.0 * (
                int(self._last_action["gear"]) - 1
            )),
            850.0,
            8600.0,
        )
        authority = self._damage_authority()
        total_distance = self.config.race_laps * self.track_length_m
        completed_distance = self.laps * self.track_length_m + self.progress_m
        return {
            "time_s": self.time_s,
            "x_m": self.x,
            "y_m": self.y,
            "yaw_rad": self.yaw,
            "unwrapped_yaw_rad": self.unwrapped_yaw,
            "speed_m_s": speed,
            "body_vx_m_s": self.vx,
            "body_vy_m_s": self.vy,
            "yaw_rate_rad_s": self.yaw_rate,
            "slip_angle_rad": slip_angle,
            "longitudinal_accel_m_s2": self._last_forces[
                "longitudinal_accel_m_s2"
            ],
            "lateral_accel_m_s2": self._last_forces[
                "lateral_accel_m_s2"
            ],
            "track_progress_m": self.progress_m,
            "track_length_m": self.track_length_m,
            "track_lateral_m": lateral_m,
            "track_half_width_m": self.config.track_width_m * 0.5,
            "track_heading_error_rad": heading_error,
            "track_curvature_now_inv_m": self._curvatures[index],
            "track_curvature_near_inv_m": self._curvatures[
                self._index_ahead(self.config.near_lookahead_m)
            ],
            "track_curvature_middle_inv_m": self._curvatures[
                self._index_ahead(self.config.middle_lookahead_m)
            ],
            "track_curvature_far_inv_m": self._curvatures[
                self._index_ahead(self.config.far_lookahead_m)
            ],
            "track_curvature_envelope_near_inv_m": (
                self._curvature_envelope_ahead(
                    0.0,
                    self.config.near_lookahead_m,
                )
            ),
            "track_curvature_envelope_middle_inv_m": (
                self._curvature_envelope_ahead(
                    self.config.near_lookahead_m,
                    self.config.middle_lookahead_m,
                )
            ),
            "track_curvature_envelope_far_inv_m": (
                self._curvature_envelope_ahead(
                    self.config.middle_lookahead_m,
                    self.config.far_lookahead_m,
                )
            ),
            "surface_grip": grip,
            "surface_wet": float(grip == self.config.wet_grip),
            "front_slip_rad": self._last_forces["front_slip_rad"],
            "rear_slip_rad": self._last_forces["rear_slip_rad"],
            "front_normal_load_n": self._last_forces[
                "front_normal_load_n"
            ],
            "rear_normal_load_n": self._last_forces[
                "rear_normal_load_n"
            ],
            "front_left_longitudinal_force_n": self._last_forces[
                "front_left_longitudinal_force_n"
            ],
            "front_right_longitudinal_force_n": self._last_forces[
                "front_right_longitudinal_force_n"
            ],
            "rear_left_longitudinal_force_n": self._last_forces[
                "rear_left_longitudinal_force_n"
            ],
            "rear_right_longitudinal_force_n": self._last_forces[
                "rear_right_longitudinal_force_n"
            ],
            "differential_yaw_moment_nm": self._last_forces[
                "differential_yaw_moment_nm"
            ],
            "tyre_temperature_mean_c": sum(self.tyre_temperature_c) / 4.0,
            "tyre_condition_mean": sum(self.tyre_condition) / 4.0,
            "brake_temperature_mean_c": sum(self.brake_temperature_c) / 4.0,
            "fuel_l": self.fuel_l,
            "damage": self.damage,
            "laps": self.laps,
            "race_total_laps": self.config.race_laps,
            "race_total_distance_m": total_distance,
            "race_remaining_distance_m": max(
                0.0,
                total_distance - completed_distance,
            ),
            "offtrack_time_s": self.offtrack_time_s,
            "collisions": self.collisions,
            "pit_stops": self.pit_stops,
            "pit_service_active": float(self._pit_service_remaining_s > 0.0),
            "nearest_opponent_ahead_m": nearest_gap,
            "nearest_opponent_lateral_m": nearest_lateral,
            "nearest_opponent_speed_m_s": nearest_speed,
            "nearest_opponent_closing_m_s": nearest_closing,
            "engine_rpm": engine_rpm,
            "gear": int(self._last_action["gear"]),
            "damage_active": float(
                self._damage is not None
                and self.time_s >= self._damage.onset_s
            ),
            # Physical receipt fields expose the plant change for evaluation,
            # not to the graph runner's sensed-state projection.
            "receipt_steering_retention": authority.steering_retention,
            "receipt_power_retention": authority.power_retention,
            "receipt_front_brake_retention": authority.front_brake_retention,
            "receipt_rear_brake_retention": authority.rear_brake_retention,
            "receipt_aero_retention": authority.aero_retention,
            "last_action": dict(self._last_action),
        }


__all__ = [
    "FullRacingWorld",
    "RacingDamage",
    "RacingPlantConfig",
]
