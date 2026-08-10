"""Energy-accounting longitudinal helicopter world for autorotation studies.

The world owns mechanics, not policy.  It accepts stable opaque actuator
tokens and returns ordinary instrument and inertial observations.  In
particular, an engine failure is never reported as a flag: the graph must infer
it from the disappearance of shaft power and the resulting rotor response.

This is deliberately a compact research plant rather than a type-certified
flight model.  Its important causal structure is explicit and auditable:

* a freewheel clutch prevents a failed engine from braking the rotor;
* the main rotor has finite rotational inertia;
* upward flow through the disc can add rotor energy;
* collective trades rotor energy for thrust;
* cyclic tilts the disc and permits a flare to exchange forward momentum for
  lift and rotor inflow.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Iterable


SIMULATOR_NAME = "jabberwock_energy_accounting_helicopter"
PHYSICS_FREQUENCY_HZ = 240
CONTROL_FREQUENCY_HZ = 20


@dataclass(frozen=True)
class HelicopterParameters:
    """Mechanically meaningful plant constants.

    Defaults are representative of a light turbine helicopter.  They are not
    intended to reproduce one named airframe.
    """

    mass_kg: float = 650.0
    rotor_radius_m: float = 5.4
    rotor_inertia_kg_m2: float = 1_050.0
    nominal_rotor_speed_rad_s: float = 42.0
    minimum_rotor_speed_fraction: float = 0.78
    maximum_rotor_speed_fraction: float = 1.08
    maximum_engine_power_watts: float = 420_000.0
    profile_drag_power_watts: float = 42_000.0
    collective_drag_power_watts: float = 310_000.0
    autorotation_power_coefficient: float = 74_000.0
    fuselage_drag_area_m2: float = 1.45
    pitch_inertia_kg_m2: float = 2_200.0
    cyclic_pitch_acceleration_rad_s2: float = 1.55
    pitch_damping_per_second: float = 1.9
    maximum_disc_tilt_radians: float = math.radians(32.0)
    maximum_safe_touchdown_vertical_speed_m_s: float = 2.5
    maximum_safe_touchdown_horizontal_speed_m_s: float = 8.0
    maximum_safe_touchdown_pitch_radians: float = math.radians(18.0)
    gravity_m_s2: float = 9.80665

    def __post_init__(self) -> None:
        for name, value in vars(self).items():
            if not math.isfinite(value) or value <= 0.0:
                raise ValueError(f"{name} must be finite and positive")
        if self.minimum_rotor_speed_fraction >= self.maximum_rotor_speed_fraction:
            raise ValueError("minimum rotor speed must be below maximum")


@dataclass(frozen=True)
class EngineFailureCondition:
    """Hidden loss of engine torque after a physical time."""

    onset_seconds: float = 1.0
    retained_power_fraction: float = 0.0

    def __post_init__(self) -> None:
        if not math.isfinite(self.onset_seconds) or self.onset_seconds < 0.0:
            raise ValueError("onset_seconds must be finite and non-negative")
        if (
            not math.isfinite(self.retained_power_fraction)
            or not 0.0 <= self.retained_power_fraction <= 1.0
        ):
            raise ValueError("retained_power_fraction must be from zero to one")


def _finite_pair(values: Iterable[float], *, field: str) -> tuple[float, float]:
    pair = tuple(float(value) for value in values)
    if len(pair) != 2 or not all(math.isfinite(value) for value in pair):
        raise ValueError(f"{field} must contain two finite values")
    return pair


def _clamp(value: float, lower: float, upper: float) -> float:
    return min(max(value, lower), upper)


class TraditionalHelicopterWorld:
    """Deterministic 2-D helicopter plant with opaque pilot controls."""

    COLLECTIVE_LEVELS = (0.08, 0.24, 0.40, 0.56, 0.72)
    CYCLIC_LEVELS = (-1.0, 0.0, 1.0)

    def __init__(
        self,
        *,
        parameters: HelicopterParameters | None = None,
        failure: EngineFailureCondition | None = None,
        initial_position: Iterable[float] = (0.0, 60.0),
        initial_velocity: Iterable[float] = (18.0, 0.0),
        action_duration_seconds: float = 0.2,
    ) -> None:
        self.parameters = parameters or HelicopterParameters()
        self.failure = failure or EngineFailureCondition()
        self.initial_position = _finite_pair(
            initial_position, field="initial_position"
        )
        self.initial_velocity = _finite_pair(
            initial_velocity, field="initial_velocity"
        )
        if self.initial_position[1] <= 0.0:
            raise ValueError("initial altitude must be positive")
        if (
            not math.isfinite(action_duration_seconds)
            or action_duration_seconds <= 0.0
        ):
            raise ValueError("action_duration_seconds must be positive")
        control_steps = action_duration_seconds * CONTROL_FREQUENCY_HZ
        if not math.isclose(control_steps, round(control_steps)):
            raise ValueError(
                "action duration must contain an integer number of control ticks"
            )
        self.action_duration_seconds = float(action_duration_seconds)
        vectors = (
            (collective, cyclic)
            for collective in self.COLLECTIVE_LEVELS
            for cyclic in self.CYCLIC_LEVELS
        )
        self._token_to_vector = {
            f"helicopter_actuator_{ordinal:03d}": vector
            for ordinal, vector in enumerate(vectors)
        }
        self.reset()

    def __enter__(self) -> "TraditionalHelicopterWorld":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def close(self) -> None:
        """Match the external-world lifecycle; this plant owns no OS resource."""

    def actuator_options(self) -> tuple[dict[str, Any], ...]:
        """Return opaque tokens plus host-only mechanical vectors."""
        return tuple(
            {"token": token, "vector": vector}
            for token, vector in self._token_to_vector.items()
        )

    def body_parameters(self) -> dict[str, float]:
        """Return measured constants, never failure state or action semantics."""
        p = self.parameters
        return {
            "body_mass": p.mass_kg,
            "rotor_inertia": p.rotor_inertia_kg_m2,
            "nominal_rotor_speed": p.nominal_rotor_speed_rad_s,
            "minimum_rotor_speed": (
                p.minimum_rotor_speed_fraction
                * p.nominal_rotor_speed_rad_s
            ),
            "maximum_rotor_speed": (
                p.maximum_rotor_speed_fraction
                * p.nominal_rotor_speed_rad_s
            ),
            "gravity_acceleration": p.gravity_m_s2,
            "maximum_safe_touchdown_vertical_speed": (
                p.maximum_safe_touchdown_vertical_speed_m_s
            ),
            "maximum_safe_touchdown_horizontal_speed": (
                p.maximum_safe_touchdown_horizontal_speed_m_s
            ),
            "maximum_safe_touchdown_pitch": (
                p.maximum_safe_touchdown_pitch_radians
            ),
        }

    def reset(
        self,
        *,
        initial_position: Iterable[float] | None = None,
        initial_velocity: Iterable[float] | None = None,
    ) -> dict[str, Any]:
        """Reset physical state while retaining airframe and failure schedule."""
        position = (
            self.initial_position
            if initial_position is None
            else _finite_pair(initial_position, field="initial_position")
        )
        velocity = (
            self.initial_velocity
            if initial_velocity is None
            else _finite_pair(initial_velocity, field="initial_velocity")
        )
        if position[1] <= 0.0:
            raise ValueError("initial altitude must be positive")
        self._x, self._z = position
        self._vx, self._vz = velocity
        self._pitch = 0.0
        self._pitch_rate = 0.0
        self._rotor_speed = self.parameters.nominal_rotor_speed_rad_s
        self._sim_time = 0.0
        self._step_index = 0
        self._action_index = 0
        self._landed = False
        self._last_token: str | None = None
        self._last_vector: tuple[float, float] | None = None
        self._last_supplied_energy = 0.0
        self._last_recovered_energy = 0.0
        self._last_absorbed_energy = 0.0
        self._last_peak_power = 0.0
        self._touchdown_vertical_speed: float | None = None
        self._touchdown_horizontal_speed: float | None = None
        self._touchdown_pitch: float | None = None
        return self.observe()

    def apply(self, token: str) -> dict[str, Any]:
        return self.step(token)

    def step(self, token: str) -> dict[str, Any]:
        """Apply one opaque command for the configured physical duration."""
        try:
            collective, cyclic = self._token_to_vector[token]
        except (KeyError, TypeError) as exc:
            raise ValueError(f"unknown helicopter actuator token: {token!r}") from exc
        physics_steps = round(
            self.action_duration_seconds * PHYSICS_FREQUENCY_HZ
        )
        supplied = 0.0
        recovered = 0.0
        absorbed = 0.0
        peak_power = 0.0
        for _ in range(physics_steps):
            if self._landed:
                break
            energies = self._integrate(collective, cyclic)
            supplied += energies["supplied"]
            recovered += energies["recovered"]
            absorbed += energies["absorbed"]
            peak_power = max(peak_power, energies["peak_power"])
        self._last_supplied_energy = supplied
        self._last_recovered_energy = recovered
        self._last_absorbed_energy = absorbed
        self._last_peak_power = peak_power
        self._action_index += 1
        self._last_token = token
        self._last_vector = (collective, cyclic)
        return self.observe()

    def _integrate(self, collective: float, cyclic: float) -> dict[str, float]:
        p = self.parameters
        dt = 1.0 / PHYSICS_FREQUENCY_HZ
        rotor_fraction = max(self._rotor_speed / p.nominal_rotor_speed_rad_s, 0.0)

        # Cyclic controls disc attitude through a damped second-order response.
        pitch_acceleration = (
            cyclic * p.cyclic_pitch_acceleration_rad_s2
            - p.pitch_damping_per_second * self._pitch_rate
            - 0.7 * self._pitch
        )
        self._pitch_rate += pitch_acceleration * dt
        self._pitch += self._pitch_rate * dt
        self._pitch = _clamp(
            self._pitch,
            -p.maximum_disc_tilt_radians,
            p.maximum_disc_tilt_radians,
        )

        normal_x = -math.sin(self._pitch)
        normal_z = math.cos(self._pitch)
        upward_disc_flow = max(
            0.0,
            -(self._vx * normal_x + self._vz * normal_z),
        )
        recovered_power = (
            p.autorotation_power_coefficient
            * upward_disc_flow
            * max(0.0, 0.82 - collective)
            * rotor_fraction
        )
        aerodynamic_loss_power = (
            p.profile_drag_power_watts * rotor_fraction**3
            + p.collective_drag_power_watts
            * collective**2
            * rotor_fraction**3
        )

        failure_active = self._sim_time >= self.failure.onset_seconds
        retained_power = (
            self.failure.retained_power_fraction if failure_active else 1.0
        )
        governor_error = max(0.0, 1.0 - rotor_fraction)
        engine_power = retained_power * min(
            p.maximum_engine_power_watts,
            aerodynamic_loss_power
            + p.maximum_engine_power_watts * 4.0 * governor_error,
        )
        net_rotor_power = (
            engine_power + recovered_power - aerodynamic_loss_power
        )
        rotor_energy = max(
            0.0,
            0.5 * p.rotor_inertia_kg_m2 * self._rotor_speed**2
            + net_rotor_power * dt,
        )
        self._rotor_speed = math.sqrt(
            2.0 * rotor_energy / p.rotor_inertia_kg_m2
        )
        self._rotor_speed = min(
            self._rotor_speed,
            p.maximum_rotor_speed_fraction * p.nominal_rotor_speed_rad_s,
        )
        rotor_fraction = self._rotor_speed / p.nominal_rotor_speed_rad_s

        # Collective trades rotor energy for lift.  The small zero-pitch term
        # captures profile/induced lift still present at minimum collective.
        # The middle collective detent is the nominal hover setting.  Keeping
        # reserve above it is essential: an autorotating rotor must be able to
        # convert stored angular momentum into a short lift impulse.
        hover_denominator = 0.40 + 0.08
        thrust = (
            p.mass_kg
            * p.gravity_m_s2
            * ((collective + 0.08) / hover_denominator)
            * rotor_fraction**2
        )
        relative_speed = math.hypot(self._vx, self._vz)
        drag = (
            0.5
            * 1.225
            * p.fuselage_drag_area_m2
            * relative_speed
        )
        ax = (
            thrust * normal_x
            - drag * self._vx
        ) / p.mass_kg
        az = (
            thrust * normal_z
            - p.mass_kg * p.gravity_m_s2
            - drag * self._vz
        ) / p.mass_kg
        self._vx += ax * dt
        self._vz += az * dt
        self._x += self._vx * dt
        self._z += self._vz * dt
        self._sim_time += dt
        self._step_index += 1

        absorbed = 0.0
        if self._z <= 0.0:
            self._touchdown_vertical_speed = self._vz
            self._touchdown_horizontal_speed = self._vx
            self._touchdown_pitch = self._pitch
            absorbed = 0.5 * p.mass_kg * (
                self._vx**2 + self._vz**2
            )
            self._z = 0.0
            self._vx = 0.0
            self._vz = 0.0
            self._pitch_rate = 0.0
            self._landed = True
        return {
            "supplied": engine_power * dt,
            "recovered": recovered_power * dt,
            "absorbed": absorbed,
            "peak_power": max(engine_power, recovered_power),
        }

    def observe(self) -> dict[str, Any]:
        """Return instrument-like state without a failure indicator."""
        p = self.parameters
        rotor_fraction = self._rotor_speed / p.nominal_rotor_speed_rad_s
        rotor_energy = 0.5 * p.rotor_inertia_kg_m2 * self._rotor_speed**2
        potential_energy = p.mass_kg * p.gravity_m_s2 * self._z
        translational_energy = 0.5 * p.mass_kg * (
            self._vx**2 + self._vz**2
        )
        safe_touchdown = (
            self._landed
            and abs(self._touchdown_vertical_speed or 0.0)
            <= p.maximum_safe_touchdown_vertical_speed_m_s
            and abs(self._touchdown_horizontal_speed or 0.0)
            <= p.maximum_safe_touchdown_horizontal_speed_m_s
            and abs(self._touchdown_pitch or 0.0)
            <= p.maximum_safe_touchdown_pitch_radians
            and rotor_fraction >= self.parameters.minimum_rotor_speed_fraction
        )
        return {
            "simulator": SIMULATOR_NAME,
            "step_index": self._step_index,
            "sim_time": self._sim_time,
            "base_position": (self._x, 0.0, self._z),
            "base_orientation_rpy": (0.0, self._pitch, 0.0),
            "base_linear_velocity": (self._vx, 0.0, self._vz),
            "base_angular_velocity": (0.0, self._pitch_rate, 0.0),
            "rotor_speed_rad_s": self._rotor_speed,
            "rotor_speed_fraction": rotor_fraction,
            "rotor_kinetic_energy_joules": rotor_energy,
            "potential_energy_joules": potential_energy,
            "translational_energy_joules": translational_energy,
            "supplied_energy_joules": self._last_supplied_energy,
            "recovered_energy_joules": self._last_recovered_energy,
            "absorbed_energy_joules": self._last_absorbed_energy,
            "peak_actuator_power_watts": self._last_peak_power,
            "contact_count": int(self._landed),
            "landed": self._landed,
            "safe_touchdown": safe_touchdown,
            "touchdown_vertical_speed": self._touchdown_vertical_speed,
            "touchdown_horizontal_speed": self._touchdown_horizontal_speed,
            "touchdown_pitch_radians": self._touchdown_pitch,
            "last_actuator_token": self._last_token,
            "actuator_activation_seconds": self.action_duration_seconds,
        }


__all__ = [
    "CONTROL_FREQUENCY_HZ",
    "EngineFailureCondition",
    "HelicopterParameters",
    "PHYSICS_FREQUENCY_HZ",
    "SIMULATOR_NAME",
    "TraditionalHelicopterWorld",
]
