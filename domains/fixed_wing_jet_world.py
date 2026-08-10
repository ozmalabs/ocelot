"""Deterministic six-degree-of-freedom fixed-wing jet research plant.

The plant owns mechanics only.  It exposes factorized opaque command tokens and
raw inertial, airflow, load, power and energy receipts.  It contains no reward,
controller, phase classifier, action selection, learning or damage diagnosis.

This is deliberately an auditable mechanism model rather than a certification
flight model.  It includes the causal features needed by the experiment:
body-relative airflow, lift/drag and departure, coupled surface forces/moments,
first-order jet spool dynamics, asymmetric thrust, wind, and hidden effector
loss.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Iterable, Sequence


PHYSICS_FREQUENCY_HZ = 400
CONTROL_FREQUENCY_HZ = 100
EFFECTOR_GROUP_COUNT = 7
COMMAND_LEVELS = (-1.0, 0.0, 1.0)


def _clamp(value: float, lower: float, upper: float) -> float:
    return min(max(value, lower), upper)


def _triple(values: Iterable[float], *, name: str) -> tuple[float, float, float]:
    result = tuple(float(value) for value in values)
    if len(result) != 3 or not all(math.isfinite(value) for value in result):
        raise ValueError(f"{name} must contain three finite values")
    return result


@dataclass(frozen=True)
class FixedWingParameters:
    mass_kg: float = 7_500.0
    wing_area_m2: float = 27.9
    span_m: float = 9.8
    chord_m: float = 3.1
    roll_inertia_kg_m2: float = 13_000.0
    pitch_inertia_kg_m2: float = 45_000.0
    yaw_inertia_kg_m2: float = 52_000.0
    maximum_engine_thrust_newtons: float = 12_000.0
    engine_spool_seconds: float = 0.85
    zero_lift_drag: float = 0.025
    induced_drag_factor: float = 0.075
    lift_offset: float = 0.64
    lift_slope_per_radian: float = 4.6
    departure_angle_radians: float = math.radians(17.0)
    roll_surface_gain: float = 0.015
    pitch_surface_gain: float = 0.08
    yaw_surface_gain: float = 0.08
    gravity_m_s2: float = 9.80665
    air_density_kg_m3: float = 1.112

    def __post_init__(self) -> None:
        for name, value in vars(self).items():
            if not math.isfinite(value) or value <= 0.0:
                raise ValueError(f"{name} must be finite and positive")


@dataclass(frozen=True)
class FixedWingDamageCondition:
    """Hidden multiplicative authority loss beginning at an action boundary."""

    onset_action: int
    retained_authority: tuple[float, ...]

    def __post_init__(self) -> None:
        if (
            isinstance(self.onset_action, bool)
            or not isinstance(self.onset_action, int)
            or self.onset_action < 0
        ):
            raise ValueError("onset_action must be a non-negative integer")
        if len(self.retained_authority) != EFFECTOR_GROUP_COUNT or not all(
            math.isfinite(value) and 0.0 <= value <= 1.0
            for value in self.retained_authority
        ):
            raise ValueError(
                "retained_authority must contain one value per effector group"
            )


def _rotation(
    roll: float,
    pitch: float,
    yaw: float,
) -> tuple[tuple[float, float, float], ...]:
    cr, sr = math.cos(roll), math.sin(roll)
    cp, sp = math.cos(pitch), math.sin(pitch)
    cy, sy = math.cos(yaw), math.sin(yaw)
    return (
        (cy * cp, cy * sp * sr - sy * cr, cy * sp * cr + sy * sr),
        (sy * cp, sy * sp * sr + cy * cr, sy * sp * cr - cy * sr),
        (-sp, cp * sr, cp * cr),
    )


def _body_to_world(
    vector: Sequence[float],
    rotation: tuple[tuple[float, float, float], ...],
) -> tuple[float, float, float]:
    return tuple(
        sum(rotation[row][column] * vector[column] for column in range(3))
        for row in range(3)
    )


def _world_to_body(
    vector: Sequence[float],
    rotation: tuple[tuple[float, float, float], ...],
) -> tuple[float, float, float]:
    return tuple(
        sum(rotation[row][column] * vector[row] for row in range(3))
        for column in range(3)
    )


def _quaternion(
    roll: float,
    pitch: float,
    yaw: float,
) -> tuple[float, float, float, float]:
    cr, sr = math.cos(roll / 2.0), math.sin(roll / 2.0)
    cp, sp = math.cos(pitch / 2.0), math.sin(pitch / 2.0)
    cy, sy = math.cos(yaw / 2.0), math.sin(yaw / 2.0)
    return (
        sr * cp * cy - cr * sp * sy,
        cr * sp * cy + sr * cp * sy,
        cr * cp * sy - sr * sp * cy,
        cr * cp * cy + sr * sp * sy,
    )


class FixedWingJetWorld:
    """A factorized opaque-effector fixed-wing plant."""

    effector_group_count = EFFECTOR_GROUP_COUNT

    def __init__(
        self,
        *,
        parameters: FixedWingParameters | None = None,
        wind_velocity: Iterable[float] = (0.0, 0.0, 0.0),
        damage: FixedWingDamageCondition | None = None,
        action_duration_seconds: float = 0.04,
        initial_altitude_m: float = 1_000.0,
        initial_airspeed_m_s: float = 86.0,
    ) -> None:
        self.parameters = parameters or FixedWingParameters()
        self.wind_velocity = _triple(wind_velocity, name="wind_velocity")
        self.damage = damage
        if (
            not math.isfinite(action_duration_seconds)
            or action_duration_seconds <= 0.0
        ):
            raise ValueError("action_duration_seconds must be positive")
        steps = action_duration_seconds * PHYSICS_FREQUENCY_HZ
        if not math.isclose(steps, round(steps)):
            raise ValueError("action duration must contain whole physics steps")
        if initial_altitude_m <= 0.0 or initial_airspeed_m_s <= 0.0:
            raise ValueError("initial altitude and airspeed must be positive")
        self.action_duration_seconds = float(action_duration_seconds)
        self.physics_steps = round(steps)
        self.initial_altitude_m = float(initial_altitude_m)
        self.initial_airspeed_m_s = float(initial_airspeed_m_s)
        self._token_to_command = {
            f"jet_effector_{ordinal:03d}": (group, command)
            for ordinal, (group, command) in enumerate(
                (group, command)
                for group in range(EFFECTOR_GROUP_COUNT)
                for command in COMMAND_LEVELS
            )
        }
        self.reset()

    def __enter__(self) -> "FixedWingJetWorld":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def close(self) -> None:
        """Match external simulator lifecycles; this plant owns no resource."""

    def actuator_options(self) -> tuple[dict[str, Any], ...]:
        options = []
        for token, (group, command) in self._token_to_command.items():
            loads = self._specified_action_loads(group, command)
            options.append({
                "token": token,
                "group_ordinal": float(group),
                "activation_magnitude": abs(command),
                "command": command,
                **{f"specified_{key}": value for key, value in loads.items()},
            })
        return tuple(options)

    def _specified_action_loads(
        self,
        group: int,
        command: float,
    ) -> dict[str, float]:
        """Return conservative offline design-analysis bounds for one command."""
        active = abs(command)
        engine = active if group in (0, 1) else 0.0
        roll_surface = active if group in (2, 3) else 0.0
        pitch_surface = active if group == 4 else 0.0
        yaw_surface = active if group == 5 else 0.0
        drag_surface = active if group == 6 else 0.0
        peak_force_increment = (
            45_000.0 * roll_surface
            + 35_000.0 * pitch_surface
            + 20_000.0 * yaw_surface
            + 30_000.0 * drag_surface
        )
        return {
            "forward": 0.20 * engine + 0.08 * drag_surface,
            "lateral": 0.10 * yaw_surface,
            "vertical": 0.10 * (roll_surface + pitch_surface),
            "roll": 0.08 * roll_surface,
            "pitch": 0.07 * pitch_surface,
            "turn": 0.08 * (yaw_surface + engine),
            "normal_load": 0.65 * (roll_surface + pitch_surface),
            "peak_force": peak_force_increment,
            "impulse": peak_force_increment * self.action_duration_seconds,
            "impact_energy": 0.0,
            "thermal_load": 500_000.0 * engine,
            "dynamic_pressure": 0.0,
            "roll_moment": 50_000.0 * roll_surface,
            "pitch_moment": 80_000.0 * pitch_surface,
            "yaw_moment": 60_000.0 * (yaw_surface + engine),
            "heat_flux": 0.0,
            "skin_temperature": 0.0,
        }

    def structural_components(self) -> tuple[dict[str, Any], ...]:
        """Return trusted design/inspection facts, not learned failure probes."""
        common = {
            "specification_confidence": 0.98,
            "fatigue_damage_per_second_at_limit": 1.0 / 18_000.0,
            "allowable_forward": 1.20,
            "load_fraction_forward": 1.0,
            "allowable_lateral": 0.75,
            "load_fraction_lateral": 1.0,
            "allowable_vertical": 0.75,
            "load_fraction_vertical": 1.0,
            "allowable_roll": 0.55,
            "load_fraction_roll": 1.0,
            "allowable_pitch": 0.45,
            "load_fraction_pitch": 1.0,
            "allowable_turn": 0.50,
            "load_fraction_turn": 1.0,
            "allowable_normal_load": 6.0,
            "load_fraction_normal_load": 1.0,
            "allowable_peak_force": 540_000.0,
            "load_fraction_peak_force": 1.0,
            "allowable_impulse": 32_000.0,
            "load_fraction_impulse": 1.0,
            "allowable_impact_energy": 1_200_000.0,
            "load_fraction_impact_energy": 1.0,
            "allowable_thermal_load": 12_000_000.0,
            "load_fraction_thermal_load": 1.0,
            "allowable_dynamic_pressure": 120_000.0,
            "load_fraction_dynamic_pressure": 1.0,
            "allowable_roll_moment": 300_000.0,
            "load_fraction_roll_moment": 1.0,
            "allowable_pitch_moment": 400_000.0,
            "load_fraction_pitch_moment": 1.0,
            "allowable_yaw_moment": 300_000.0,
            "load_fraction_yaw_moment": 1.0,
            "allowable_heat_flux": 100_000.0,
            "load_fraction_heat_flux": 1.0,
            "allowable_skin_temperature": 800.0,
            "load_fraction_skin_temperature": 1.0,
        }
        wing = {
            **common,
            "component_code": "structure_000",
            "material_code": "material_000",
        }
        tail = {
            **common,
            "component_code": "structure_001",
            "material_code": "material_001",
            "allowable_pitch": 0.36,
            "load_fraction_pitch": 0.85,
            "allowable_turn": 0.38,
            "load_fraction_turn": 0.85,
        }
        fuselage = {
            **common,
            "component_code": "structure_002",
            "material_code": "material_002",
            "allowable_impact_energy": 900_000.0,
        }
        return (wing, tail, fuselage)

    def reset(self) -> dict[str, Any]:
        self._position = [0.0, 0.0, self.initial_altitude_m]
        self._velocity = [self.initial_airspeed_m_s, 0.0, 0.0]
        self._attitude = [0.0, 0.0, 0.0]
        self._rates = [0.0, 0.0, 0.0]
        self._engine_state = [0.35, 0.35]
        self._commands = [0.0] * EFFECTOR_GROUP_COUNT
        self._action_index = 0
        self._sim_time = 0.0
        self._last_tokens: tuple[str, ...] = ()
        self._last_input_energy = 0.0
        self._last_dissipated_energy = 0.0
        self._last_normal_load = 1.0
        self._last_dynamic_pressure = 0.0
        self._last_alpha = 0.0
        self._last_beta = 0.0
        self._last_peak_force = 0.0
        self._last_impulse = 0.0
        self._last_impact_energy = 0.0
        self._last_moments = [0.0, 0.0, 0.0]
        self._last_skin_temperature = 288.15
        return self.observe()

    def _authority(self) -> tuple[float, ...]:
        if self.damage is None or self._action_index < self.damage.onset_action:
            return (1.0,) * EFFECTOR_GROUP_COUNT
        return self.damage.retained_authority

    def step_program(self, tokens: Sequence[str]) -> dict[str, Any]:
        if isinstance(tokens, (str, bytes)) or not tokens:
            raise ValueError("a motor program must contain opaque tokens")
        commands = [0.0] * EFFECTOR_GROUP_COUNT
        seen: set[int] = set()
        for token in tokens:
            try:
                group, command = self._token_to_command[token]
            except (KeyError, TypeError) as exc:
                raise ValueError(f"unknown fixed-wing token: {token!r}") from exc
            if group in seen:
                raise ValueError("a motor program may command each group once")
            seen.add(group)
            commands[group] = command
        authority = self._authority()
        self._commands = [
            command * authority[group]
            for group, command in enumerate(commands)
        ]
        input_energy = 0.0
        dissipated_energy = 0.0
        peak_force = 0.0
        impulse = 0.0
        peak_moments = [0.0, 0.0, 0.0]
        for _ in range(self.physics_steps):
            supplied, dissipated, force, moments = self._integrate()
            input_energy += supplied
            dissipated_energy += dissipated
            peak_force = max(peak_force, force)
            impulse += force / PHYSICS_FREQUENCY_HZ
            peak_moments = [
                max(existing, abs(value))
                for existing, value in zip(peak_moments, moments)
            ]
        self._last_tokens = tuple(tokens)
        self._last_input_energy = input_energy
        self._last_dissipated_energy = dissipated_energy
        self._last_peak_force = peak_force
        self._last_impulse = impulse
        self._last_moments = peak_moments
        self._action_index += 1
        return self.observe()

    def _integrate(
        self,
    ) -> tuple[float, float, float, tuple[float, float, float]]:
        p = self.parameters
        dt = 1.0 / PHYSICS_FREQUENCY_HZ
        roll, pitch, yaw = self._attitude
        rotation = _rotation(roll, pitch, yaw)
        relative_world = tuple(
            self._velocity[index] - self.wind_velocity[index]
            for index in range(3)
        )
        u, v, w = _world_to_body(relative_world, rotation)
        speed = max(0.1, math.sqrt(u * u + v * v + w * w))
        alpha = math.atan2(-w, max(0.1, u))
        beta = math.asin(_clamp(v / speed, -1.0, 1.0))
        qbar = 0.5 * p.air_density_kg_m3 * speed * speed
        departure_ratio = abs(alpha) / p.departure_angle_radians
        departure_gain = 1.0 if departure_ratio <= 1.0 else max(
            0.12,
            1.0 - 0.72 * (departure_ratio - 1.0),
        )
        lift_coefficient = (
            p.lift_offset + p.lift_slope_per_radian * alpha
        ) * departure_gain

        throttle_targets = [
            _clamp(0.35 + 0.35 * self._commands[index], 0.0, 1.0)
            for index in (0, 1)
        ]
        for index, target in enumerate(throttle_targets):
            self._engine_state[index] += (
                target - self._engine_state[index]
            ) * dt / p.engine_spool_seconds
        thrusts = [
            state * p.maximum_engine_thrust_newtons
            for state in self._engine_state
        ]
        left_surface, right_surface = self._commands[2], self._commands[3]
        pitch_surface, yaw_surface = self._commands[4], self._commands[5]
        drag_surface = self._commands[6]
        differential_lift = qbar * p.wing_area_m2 * p.roll_surface_gain
        left_lift = differential_lift * left_surface
        right_lift = differential_lift * right_surface
        lift = qbar * p.wing_area_m2 * lift_coefficient + left_lift + right_lift
        drag_coefficient = (
            p.zero_lift_drag
            + p.induced_drag_factor * lift_coefficient * lift_coefficient
            + 0.035 * abs(drag_surface)
        )
        drag = qbar * p.wing_area_m2 * drag_coefficient
        side_force = -qbar * p.wing_area_m2 * 0.55 * beta
        body_force = (
            thrusts[0] + thrusts[1] - drag,
            side_force,
            lift,
        )
        world_force = _body_to_world(body_force, rotation)
        acceleration = (
            world_force[0] / p.mass_kg,
            world_force[1] / p.mass_kg,
            world_force[2] / p.mass_kg - p.gravity_m_s2,
        )
        for index in range(3):
            self._velocity[index] += acceleration[index] * dt
            self._position[index] += self._velocity[index] * dt

        roll_moment = (
            (right_lift - left_lift) * p.span_m * 0.42
            - 30_000.0 * self._rates[0]
        )
        pitch_moment = (
            qbar * p.wing_area_m2 * p.chord_m
            * (
                p.pitch_surface_gain * pitch_surface
                - 0.22 * alpha
                - 0.52 * self._rates[1]
            )
        )
        yaw_moment = (
            qbar * p.wing_area_m2 * p.span_m
            * (
                p.yaw_surface_gain * yaw_surface
                - 0.20 * beta
                - 0.38 * self._rates[2]
            )
            + (thrusts[1] - thrusts[0]) * p.span_m * 0.18
        )
        angular_acceleration = (
            roll_moment / p.roll_inertia_kg_m2,
            pitch_moment / p.pitch_inertia_kg_m2,
            yaw_moment / p.yaw_inertia_kg_m2,
        )
        for index in range(3):
            self._rates[index] += angular_acceleration[index] * dt
        body_p, body_q, body_r = self._rates
        cos_pitch = max(0.05, abs(math.cos(pitch)))
        self._attitude[0] += (
            body_p
            + math.sin(roll) * math.tan(pitch) * body_q
            + math.cos(roll) * math.tan(pitch) * body_r
        ) * dt
        self._attitude[1] += (
            math.cos(roll) * body_q - math.sin(roll) * body_r
        ) * dt
        self._attitude[2] += (
            math.sin(roll) / cos_pitch * body_q
            + math.cos(roll) / cos_pitch * body_r
        ) * dt
        self._attitude[1] = _clamp(
            self._attitude[1],
            -math.radians(80.0),
            math.radians(80.0),
        )
        self._position[2] = max(0.0, self._position[2])
        self._sim_time += dt
        self._last_normal_load = lift / (p.mass_kg * p.gravity_m_s2)
        self._last_dynamic_pressure = qbar
        self._last_alpha = alpha
        self._last_beta = beta
        self._last_skin_temperature = (
            288.15 + 0.9 * speed * speed / (2.0 * 1_004.0)
        )
        supplied_power = sum(thrusts) * max(0.0, u)
        dissipated_power = drag * speed
        force_magnitude = math.sqrt(sum(value * value for value in body_force))
        return (
            supplied_power * dt,
            dissipated_power * dt,
            force_magnitude,
            (roll_moment, pitch_moment, yaw_moment),
        )

    def observe(self) -> dict[str, Any]:
        rotation = _rotation(*self._attitude)
        relative_world = tuple(
            self._velocity[index] - self.wind_velocity[index]
            for index in range(3)
        )
        body_velocity = _world_to_body(relative_world, rotation)
        return {
            "position": tuple(self._position),
            "base_position": tuple(self._position),
            "orientation_xyzw": _quaternion(*self._attitude),
            "base_orientation_xyzw": _quaternion(*self._attitude),
            "linear_velocity": tuple(self._velocity),
            "body_air_velocity": body_velocity,
            "body_angular_velocity": tuple(self._rates),
            "engine_power_state": tuple(self._engine_state),
            # THE PROPULSION LEDGER'S RATE CEILING, published at last.  These
            # two numbers were already declared by `FixedWingParameters` and
            # were never handed to the graph, so every consumer of this plant
            # was free to read thrust as unbounded power.  Copying them out is
            # mechanical: the total installed thrust across the declared
            # engines, and the mass it has to accelerate.  This plant models no
            # fuel, so it publishes NO remaining-stock key at all -- that
            # absence is first-class and the consumer's own held bound stands
            # in for it.
            "maximum_engine_thrust_newtons": (
                len(self._engine_state)
                * self.parameters.maximum_engine_thrust_newtons
            ),
            "vehicle_mass_kg": self.parameters.mass_kg,
            "normal_load_factor": self._last_normal_load,
            "dynamic_pressure_pascals": self._last_dynamic_pressure,
            "angle_of_attack_radians": self._last_alpha,
            "sideslip_radians": self._last_beta,
            "input_energy_joules": self._last_input_energy,
            "aerodynamic_dissipation_joules": self._last_dissipated_energy,
            "peak_force_newtons": self._last_peak_force,
            "impulse_newton_seconds": self._last_impulse,
            "impact_energy_joules": self._last_impact_energy,
            "thermal_load_joules": 0.4 * self._last_input_energy,
            "roll_moment_newton_metres": self._last_moments[0],
            "pitch_moment_newton_metres": self._last_moments[1],
            "yaw_moment_newton_metres": self._last_moments[2],
            "heat_flux_watts_per_square_metre": 0.0,
            "skin_temperature_kelvin": self._last_skin_temperature,
            "observed_damage_fraction": 0.0,
            "last_motor_program_tokens": self._last_tokens,
            "sim_time_seconds": self._sim_time,
            "action_index": self._action_index,
            "ground_contact": float(self._position[2] <= 0.0),
        }


__all__ = [
    "COMMAND_LEVELS",
    "CONTROL_FREQUENCY_HZ",
    "EFFECTOR_GROUP_COUNT",
    "FixedWingDamageCondition",
    "FixedWingJetWorld",
    "FixedWingParameters",
    "PHYSICS_FREQUENCY_HZ",
]
