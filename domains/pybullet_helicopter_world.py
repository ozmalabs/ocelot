"""Six-degree-of-freedom traditional-helicopter autorotation world.

Bullet owns rigid-body translation, quaternion attitude, angular momentum, and
contact.  This adapter adds an explicit main-rotor energy state, freewheeling
engine coupling, airflow-driven rotor recovery, pilot-control forces/torques,
wind, and bounded disturbances.  It contains no controller or learning logic.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Iterable

from domains.traditional_helicopter_world import (
    EngineFailureCondition,
    HelicopterParameters,
)

try:
    import numpy as _np
    import pybullet as _bullet
except ImportError:  # pragma: no cover - exercised by dependency error path
    _np = None
    _bullet = None


SIMULATOR_NAME = "pybullet_six_dof_energy_accounting_helicopter"
PHYSICS_FREQUENCY_HZ = 240
CONTROL_FREQUENCY_HZ = 20


@dataclass(frozen=True)
class HelicopterDisturbance:
    """Hidden, time-bounded external wrench in world coordinates."""

    onset_seconds: float
    duration_seconds: float
    force_newtons_xyz: tuple[float, float, float] = (0.0, 0.0, 0.0)
    torque_newton_metres_xyz: tuple[float, float, float] = (0.0, 0.0, 0.0)

    def __post_init__(self) -> None:
        if not math.isfinite(self.onset_seconds) or self.onset_seconds < 0.0:
            raise ValueError("onset_seconds must be finite and non-negative")
        if not math.isfinite(self.duration_seconds) or self.duration_seconds <= 0:
            raise ValueError("duration_seconds must be finite and positive")
        for field, values in (
            ("force_newtons_xyz", self.force_newtons_xyz),
            ("torque_newton_metres_xyz", self.torque_newton_metres_xyz),
        ):
            if len(values) != 3 or not all(math.isfinite(v) for v in values):
                raise ValueError(f"{field} must contain three finite values")


def _triple(values: Iterable[float], *, field: str) -> tuple[float, float, float]:
    result = tuple(float(value) for value in values)
    if len(result) != 3 or not all(math.isfinite(value) for value in result):
        raise ValueError(f"{field} must contain three finite values")
    return result


def _clamp(value: float, lower: float, upper: float) -> float:
    return min(max(value, lower), upper)


class PyBulletHelicopterWorld:
    """A simple auditable 6-DoF helicopter with opaque combined controls."""

    COLLECTIVE_LEVELS = (0.24, 0.40, 0.68)
    CYCLIC_LONGITUDINAL_LEVELS = (-1.0, 0.0, 1.0)
    CYCLIC_LATERAL_LEVELS = (-1.0, 0.0, 1.0)
    PEDAL_LEVELS = (-1.0, 0.0, 1.0)

    _FUSELAGE_HALF_EXTENTS = (1.8, 0.72, 0.48)
    _MAXIMUM_DISC_TILT_RADIANS = math.radians(7.0)
    _ANGULAR_DAMPING_NM_PER_RAD_S = (2_400.0, 2_400.0, 1_200.0)
    _CYCLIC_CONTROL_TORQUE_NM = 360.0
    _PEDAL_TORQUE_NM = 720.0
    _COLLECTIVE_YAW_COUPLING_NM = 340.0
    _AIR_DENSITY_KG_M3 = 1.225

    def __init__(
        self,
        *,
        parameters: HelicopterParameters | None = None,
        failure: EngineFailureCondition | None = None,
        initial_position: Iterable[float] = (0.0, 0.0, 100.0),
        initial_velocity: Iterable[float] = (18.0, 0.0, 0.0),
        initial_orientation_rpy: Iterable[float] = (0.0, 0.0, 0.0),
        initial_angular_velocity: Iterable[float] = (0.0, 0.0, 0.0),
        wind_velocity: Iterable[float] = (0.0, 0.0, 0.0),
        disturbance: HelicopterDisturbance | None = None,
        action_duration_seconds: float = 0.1,
    ) -> None:
        if _np is None or _bullet is None:
            raise RuntimeError("pybullet and numpy are required")
        self.parameters = parameters or HelicopterParameters()
        self.failure = failure or EngineFailureCondition()
        self.initial_position = _triple(
            initial_position, field="initial_position"
        )
        self.initial_velocity = _triple(
            initial_velocity, field="initial_velocity"
        )
        self.initial_orientation_rpy = _triple(
            initial_orientation_rpy, field="initial_orientation_rpy"
        )
        self.initial_angular_velocity = _triple(
            initial_angular_velocity, field="initial_angular_velocity"
        )
        self.wind_velocity = _triple(wind_velocity, field="wind_velocity")
        self.disturbance = disturbance
        if self.initial_position[2] <= 0.0:
            raise ValueError("initial altitude must be positive")
        if (
            not math.isfinite(action_duration_seconds)
            or action_duration_seconds <= 0.0
        ):
            raise ValueError("action_duration_seconds must be positive")
        self.action_duration_seconds = float(action_duration_seconds)
        self._physics_steps_per_action = round(
            action_duration_seconds * PHYSICS_FREQUENCY_HZ
        )
        if not math.isclose(
            self._physics_steps_per_action,
            action_duration_seconds * PHYSICS_FREQUENCY_HZ,
        ):
            raise ValueError(
                "action duration must contain an integer number of physics ticks"
            )
        vectors = (
            (collective, longitudinal, lateral, pedal)
            for collective in self.COLLECTIVE_LEVELS
            for longitudinal in self.CYCLIC_LONGITUDINAL_LEVELS
            for lateral in self.CYCLIC_LATERAL_LEVELS
            for pedal in self.PEDAL_LEVELS
        )
        self._token_to_vector = {
            f"helicopter_3d_actuator_{ordinal:03d}": vector
            for ordinal, vector in enumerate(vectors)
        }
        self._client = _bullet.connect(_bullet.DIRECT)
        _bullet.setPhysicsEngineParameter(
            fixedTimeStep=1.0 / PHYSICS_FREQUENCY_HZ,
            numSubSteps=1,
            physicsClientId=self._client,
        )
        _bullet.setGravity(
            0.0,
            0.0,
            -self.parameters.gravity_m_s2,
            physicsClientId=self._client,
        )
        self._ground_id = self._create_ground()
        self._body_id = self._create_body()
        self.reset()

    def __enter__(self) -> "PyBulletHelicopterWorld":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def _create_ground(self) -> int:
        collision = _bullet.createCollisionShape(
            _bullet.GEOM_PLANE,
            physicsClientId=self._client,
        )
        return int(_bullet.createMultiBody(
            baseMass=0.0,
            baseCollisionShapeIndex=collision,
            physicsClientId=self._client,
        ))

    def _create_body(self) -> int:
        collision = _bullet.createCollisionShape(
            _bullet.GEOM_BOX,
            halfExtents=self._FUSELAGE_HALF_EXTENTS,
            physicsClientId=self._client,
        )
        visual = _bullet.createVisualShape(
            _bullet.GEOM_BOX,
            halfExtents=self._FUSELAGE_HALF_EXTENTS,
            rgbaColor=(0.12, 0.24, 0.30, 1.0),
            physicsClientId=self._client,
        )
        body = int(_bullet.createMultiBody(
            baseMass=self.parameters.mass_kg,
            baseCollisionShapeIndex=collision,
            baseVisualShapeIndex=visual,
            basePosition=(0.0, 0.0, 1.0),
            physicsClientId=self._client,
        ))
        _bullet.changeDynamics(
            body,
            -1,
            linearDamping=0.0,
            angularDamping=0.0,
            lateralFriction=0.8,
            restitution=0.0,
            physicsClientId=self._client,
        )
        return body

    def close(self) -> None:
        if self._client is not None:
            _bullet.disconnect(self._client)
            self._client = None

    def actuator_options(self) -> tuple[dict[str, Any], ...]:
        return tuple(
            {"token": token, "vector": vector}
            for token, vector in self._token_to_vector.items()
        )

    def body_parameters(self) -> dict[str, float]:
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
            "maximum_safe_touchdown_lateral_speed": (
                p.maximum_safe_touchdown_horizontal_speed_m_s
            ),
            "maximum_safe_touchdown_pitch": (
                p.maximum_safe_touchdown_pitch_radians
            ),
            "maximum_safe_touchdown_roll": (
                p.maximum_safe_touchdown_pitch_radians
            ),
        }

    def reset(
        self,
        *,
        initial_position: Iterable[float] | None = None,
        initial_velocity: Iterable[float] | None = None,
        initial_orientation_rpy: Iterable[float] | None = None,
        initial_angular_velocity: Iterable[float] | None = None,
    ) -> dict[str, Any]:
        position = (
            self.initial_position
            if initial_position is None
            else _triple(initial_position, field="initial_position")
        )
        velocity = (
            self.initial_velocity
            if initial_velocity is None
            else _triple(initial_velocity, field="initial_velocity")
        )
        orientation_rpy = (
            self.initial_orientation_rpy
            if initial_orientation_rpy is None
            else _triple(
                initial_orientation_rpy, field="initial_orientation_rpy"
            )
        )
        angular_velocity = (
            self.initial_angular_velocity
            if initial_angular_velocity is None
            else _triple(
                initial_angular_velocity, field="initial_angular_velocity"
            )
        )
        if position[2] <= 0.0:
            raise ValueError("initial altitude must be positive")
        centre_position = (
            position[0],
            position[1],
            position[2] + self._FUSELAGE_HALF_EXTENTS[2],
        )
        quaternion = _bullet.getQuaternionFromEuler(orientation_rpy)
        _bullet.resetBasePositionAndOrientation(
            self._body_id,
            centre_position,
            quaternion,
            physicsClientId=self._client,
        )
        _bullet.resetBaseVelocity(
            self._body_id,
            linearVelocity=velocity,
            angularVelocity=angular_velocity,
            physicsClientId=self._client,
        )
        self._rotor_speed = self.parameters.nominal_rotor_speed_rad_s
        self._sim_time = 0.0
        self._step_index = 0
        self._action_index = 0
        self._landed = False
        self._last_token: str | None = None
        self._last_vector: tuple[float, float, float, float] | None = None
        self._last_supplied_energy = 0.0
        self._last_recovered_energy = 0.0
        self._last_absorbed_energy = 0.0
        self._last_peak_power = 0.0
        self._touchdown_velocity: tuple[float, float, float] | None = None
        self._touchdown_rpy: tuple[float, float, float] | None = None
        self._touchdown_rotor_fraction: float | None = None
        return self.observe()

    def apply(self, token: str) -> dict[str, Any]:
        return self.step(token)

    def step(self, token: str) -> dict[str, Any]:
        try:
            command = self._token_to_vector[token]
        except (KeyError, TypeError) as exc:
            raise ValueError(
                f"unknown 3-D helicopter actuator token: {token!r}"
            ) from exc
        supplied = 0.0
        recovered = 0.0
        absorbed = 0.0
        peak_power = 0.0
        for _ in range(self._physics_steps_per_action):
            if self._landed:
                break
            energies = self._integrate(command)
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
        self._last_vector = command
        return self.observe()

    def _integrate(
        self,
        command: tuple[float, float, float, float],
    ) -> dict[str, float]:
        p = self.parameters
        dt = 1.0 / PHYSICS_FREQUENCY_HZ
        collective, cyclic_longitudinal, cyclic_lateral, pedal = command
        position, quaternion = _bullet.getBasePositionAndOrientation(
            self._body_id,
            physicsClientId=self._client,
        )
        velocity, angular_velocity = _bullet.getBaseVelocity(
            self._body_id,
            physicsClientId=self._client,
        )
        matrix = _bullet.getMatrixFromQuaternion(quaternion)
        body_x = _np.asarray((matrix[0], matrix[3], matrix[6]), dtype=float)
        body_y = _np.asarray((matrix[1], matrix[4], matrix[7]), dtype=float)
        body_z = _np.asarray((matrix[2], matrix[5], matrix[8]), dtype=float)
        disc_normal = (
            body_z
            - cyclic_longitudinal
            * math.sin(self._MAXIMUM_DISC_TILT_RADIANS)
            * body_x
            + cyclic_lateral
            * math.sin(self._MAXIMUM_DISC_TILT_RADIANS)
            * body_y
        )
        disc_normal /= _np.linalg.norm(disc_normal)
        relative_velocity = (
            _np.asarray(velocity, dtype=float)
            - _np.asarray(self.wind_velocity, dtype=float)
        )
        rotor_fraction = max(
            self._rotor_speed / p.nominal_rotor_speed_rad_s,
            0.0,
        )
        upward_disc_flow = max(
            0.0,
            -float(_np.dot(relative_velocity, disc_normal)),
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
        rotor_energy = max(
            0.0,
            0.5 * p.rotor_inertia_kg_m2 * self._rotor_speed**2
            + (
                engine_power + recovered_power - aerodynamic_loss_power
            ) * dt,
        )
        self._rotor_speed = min(
            math.sqrt(2.0 * rotor_energy / p.rotor_inertia_kg_m2),
            p.maximum_rotor_speed_fraction * p.nominal_rotor_speed_rad_s,
        )
        rotor_fraction = self._rotor_speed / p.nominal_rotor_speed_rad_s
        thrust = (
            p.mass_kg
            * p.gravity_m_s2
            * ((collective + 0.08) / (0.40 + 0.08))
            * rotor_fraction**2
        )
        thrust_force = thrust * disc_normal
        _bullet.applyExternalForce(
            self._body_id,
            -1,
            forceObj=thrust_force,
            posObj=position,
            flags=_bullet.WORLD_FRAME,
            physicsClientId=self._client,
        )

        speed = float(_np.linalg.norm(relative_velocity))
        drag_force = (
            -0.5
            * self._AIR_DENSITY_KG_M3
            * p.fuselage_drag_area_m2
            * speed
            * relative_velocity
        )
        _bullet.applyExternalForce(
            self._body_id,
            -1,
            forceObj=drag_force,
            posObj=position,
            flags=_bullet.WORLD_FRAME,
            physicsClientId=self._client,
        )
        angular_velocity_array = _np.asarray(angular_velocity, dtype=float)
        body_rates = (
            float(_np.dot(angular_velocity_array, body_x)),
            float(_np.dot(angular_velocity_array, body_y)),
            float(_np.dot(angular_velocity_array, body_z)),
        )
        damping_torque = (
            -self._ANGULAR_DAMPING_NM_PER_RAD_S[0] * body_rates[0] * body_x
            - self._ANGULAR_DAMPING_NM_PER_RAD_S[1] * body_rates[1] * body_y
            - self._ANGULAR_DAMPING_NM_PER_RAD_S[2] * body_rates[2] * body_z
        )
        yaw_torque = (
            pedal * self._PEDAL_TORQUE_NM
            - (collective - 0.40) * self._COLLECTIVE_YAW_COUPLING_NM
        )
        control_torque = (
            damping_torque
            + cyclic_lateral * self._CYCLIC_CONTROL_TORQUE_NM * body_x
            - cyclic_longitudinal
            * self._CYCLIC_CONTROL_TORQUE_NM
            * body_y
            + yaw_torque * body_z
        )
        _bullet.applyExternalTorque(
            self._body_id,
            -1,
            torqueObj=control_torque,
            flags=_bullet.WORLD_FRAME,
            physicsClientId=self._client,
        )

        disturbance = self.disturbance
        if (
            disturbance is not None
            and disturbance.onset_seconds
            <= self._sim_time
            < disturbance.onset_seconds + disturbance.duration_seconds
        ):
            _bullet.applyExternalForce(
                self._body_id,
                -1,
                forceObj=disturbance.force_newtons_xyz,
                posObj=position,
                flags=_bullet.WORLD_FRAME,
                physicsClientId=self._client,
            )
            _bullet.applyExternalTorque(
                self._body_id,
                -1,
                torqueObj=disturbance.torque_newton_metres_xyz,
                flags=_bullet.WORLD_FRAME,
                physicsClientId=self._client,
            )

        pre_contact_velocity = tuple(float(value) for value in velocity)
        pre_contact_rpy = tuple(
            float(value) for value in _bullet.getEulerFromQuaternion(quaternion)
        )
        _bullet.stepSimulation(physicsClientId=self._client)
        self._sim_time += dt
        self._step_index += 1
        contacts = _bullet.getContactPoints(
            bodyA=self._body_id,
            bodyB=self._ground_id,
            physicsClientId=self._client,
        )
        absorbed = 0.0
        if contacts:
            self._touchdown_velocity = pre_contact_velocity
            self._touchdown_rpy = pre_contact_rpy
            self._touchdown_rotor_fraction = rotor_fraction
            absorbed = 0.5 * p.mass_kg * sum(
                component**2 for component in pre_contact_velocity
            )
            self._landed = True
            _bullet.resetBaseVelocity(
                self._body_id,
                linearVelocity=(0.0, 0.0, 0.0),
                angularVelocity=(0.0, 0.0, 0.0),
                physicsClientId=self._client,
            )
        return {
            "supplied": engine_power * dt,
            "recovered": recovered_power * dt,
            "absorbed": absorbed,
            "peak_power": max(engine_power, recovered_power),
        }

    def observe(self) -> dict[str, Any]:
        position, quaternion = _bullet.getBasePositionAndOrientation(
            self._body_id,
            physicsClientId=self._client,
        )
        velocity, angular_velocity = _bullet.getBaseVelocity(
            self._body_id,
            physicsClientId=self._client,
        )
        rpy = tuple(
            float(value) for value in _bullet.getEulerFromQuaternion(quaternion)
        )
        altitude = max(
            0.0,
            float(position[2]) - self._FUSELAGE_HALF_EXTENTS[2],
        )
        p = self.parameters
        rotor_fraction = self._rotor_speed / p.nominal_rotor_speed_rad_s
        touchdown_velocity = self._touchdown_velocity or (0.0, 0.0, 0.0)
        touchdown_rpy = self._touchdown_rpy or (0.0, 0.0, 0.0)
        touchdown_rotor_fraction = (
            self._touchdown_rotor_fraction
            if self._touchdown_rotor_fraction is not None
            else rotor_fraction
        )
        safe_touchdown = (
            self._landed
            and abs(touchdown_velocity[2])
            <= p.maximum_safe_touchdown_vertical_speed_m_s
            and abs(touchdown_velocity[0])
            <= p.maximum_safe_touchdown_horizontal_speed_m_s
            and abs(touchdown_velocity[1])
            <= p.maximum_safe_touchdown_horizontal_speed_m_s
            and abs(touchdown_rpy[0])
            <= p.maximum_safe_touchdown_pitch_radians
            and abs(touchdown_rpy[1])
            <= p.maximum_safe_touchdown_pitch_radians
            and touchdown_rotor_fraction >= p.minimum_rotor_speed_fraction
        )
        rotor_energy = 0.5 * p.rotor_inertia_kg_m2 * self._rotor_speed**2
        translational_energy = 0.5 * p.mass_kg * sum(
            float(component) ** 2 for component in velocity
        )
        contacts = _bullet.getContactPoints(
            bodyA=self._body_id,
            bodyB=self._ground_id,
            physicsClientId=self._client,
        )
        contact_force_newtons = sum(
            max(0.0, float(contact[9])) for contact in contacts
        )
        return {
            "simulator": SIMULATOR_NAME,
            "step_index": self._step_index,
            "sim_time": self._sim_time,
            "body_id": self._body_id,
            "base_position": (
                float(position[0]),
                float(position[1]),
                altitude,
            ),
            "base_orientation_xyzw": tuple(float(v) for v in quaternion),
            "base_orientation_rpy": rpy,
            "base_linear_velocity": tuple(float(v) for v in velocity),
            "base_angular_velocity": tuple(float(v) for v in angular_velocity),
            "rotor_speed_rad_s": self._rotor_speed,
            "rotor_speed_fraction": rotor_fraction,
            "rotor_kinetic_energy_joules": rotor_energy,
            "potential_energy_joules": (
                p.mass_kg * p.gravity_m_s2 * altitude
            ),
            "translational_energy_joules": translational_energy,
            "supplied_energy_joules": self._last_supplied_energy,
            "recovered_energy_joules": self._last_recovered_energy,
            "absorbed_energy_joules": self._last_absorbed_energy,
            "peak_actuator_power_watts": self._last_peak_power,
            "contact_count": int(self._landed),
            "contact_force_newtons": contact_force_newtons,
            "landed": self._landed,
            "safe_touchdown": safe_touchdown,
            "touchdown_velocity": self._touchdown_velocity,
            "touchdown_rpy": self._touchdown_rpy,
            "touchdown_rotor_fraction": self._touchdown_rotor_fraction,
            "last_actuator_token": self._last_token,
            "actuator_activation_seconds": self.action_duration_seconds,
        }

    def _render_rgb_array(
        self,
        *,
        width: int = 960,
        height: int = 540,
    ) -> Any:
        position = self.observe()["base_position"]
        view = _bullet.computeViewMatrixFromYawPitchRoll(
            cameraTargetPosition=position,
            distance=18.0,
            yaw=38.0,
            pitch=-18.0,
            roll=0.0,
            upAxisIndex=2,
        )
        projection = _bullet.computeProjectionMatrixFOV(
            fov=48.0,
            aspect=float(width) / float(height),
            nearVal=0.1,
            farVal=500.0,
        )
        image = _bullet.getCameraImage(
            width,
            height,
            viewMatrix=view,
            projectionMatrix=projection,
            renderer=_bullet.ER_TINY_RENDERER,
            physicsClientId=self._client,
        )
        return _np.asarray(image[2], dtype=_np.uint8).reshape(
            height, width, 4
        )[..., :3]


__all__ = [
    "CONTROL_FREQUENCY_HZ",
    "HelicopterDisturbance",
    "PHYSICS_FREQUENCY_HZ",
    "PyBulletHelicopterWorld",
    "SIMULATOR_NAME",
]
