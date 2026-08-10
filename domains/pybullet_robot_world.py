"""Mechanical PyBullet boundary for graph-native embodied adaptation.

This module deliberately knows only hardware wiring and simulator I/O.  It
accepts an opaque actuator token, advances fixed-step physics, and returns raw
measurements.  Action selection, actuator interpretation, state prediction,
learning, reward, and navigation all belong to the Rust/graph agent.

The bundled bodies intentionally expose the same two-dimensional command
alphabet even though the dimensions connect to different mechanisms:

* R2-D2 and Husky: two independently driven wheel groups.
* Racecar: wheel drive and steering hinge position.

Neither those meanings nor directional labels are exposed in the actuator
tokens.  A fresh agent must discover their consequences from observations.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any, Final, Iterable, Sequence

import numpy as _np

from domains.sensorimotor_transducer import (
    SensorimotorSensorConfiguration,
    SensorimotorTransducer,
)

try:
    import pybullet as _bullet
    import pybullet_data as _bullet_data
except ModuleNotFoundError:  # Keep non-robot installations importable.
    _bullet = None
    _bullet_data = None


@dataclass(frozen=True)
class _BodyHardware:
    """Immutable host-side wiring for one physical body."""

    urdf: str
    base_height: float
    mechanism: str
    channel_a_joints: tuple[int, ...]
    channel_b_joints: tuple[int, ...]
    velocity_scale: float
    maximum_force: float
    steering_scale: float = 0.0
    load_sensor_links: tuple[int, ...] = ()
    aerodynamic_hardware: "_AerodynamicHardware | None" = None


@dataclass(frozen=True)
class _AerodynamicHardware:
    """Mechanical constants for independently actuated aerodynamic surfaces.

    The constants are expressed relative to body weight and a reference flow
    speed so the plant scales with randomized mass.  They are simulator
    mechanics, never actuator semantics exposed to the graph.
    """

    surface_points_body: tuple[tuple[float, float, float], ...]
    reference_flow_speed: float = 4.0
    downforce_weight_fraction_at_reference: float = 0.45
    drag_weight_fraction_at_reference: float = 0.08
    airbrake_drag_multiplier: float = 2.0
    actuator_power_watts_per_surface: float = 2.0


@dataclass(frozen=True)
class AerodynamicCondition:
    """Hidden damage or wear schedule for aerodynamic effectors."""

    onset_action: int
    abrupt_retention: tuple[float, ...]
    wear_per_use: tuple[float, ...] = ()
    minimum_retention: float = 0.0

    def __post_init__(self) -> None:
        if (
            isinstance(self.onset_action, bool)
            or not isinstance(self.onset_action, int)
            or self.onset_action < 0
        ):
            raise ValueError("onset_action must be a non-negative integer")
        if not self.abrupt_retention:
            raise ValueError("abrupt_retention must contain at least one surface")
        if not all(
            math.isfinite(value) and 0.0 <= value <= 1.0
            for value in self.abrupt_retention
        ):
            raise ValueError(
                "abrupt_retention values must be finite and between zero and one"
            )
        if self.wear_per_use and len(self.wear_per_use) != len(
            self.abrupt_retention
        ):
            raise ValueError(
                "wear_per_use must be empty or match abrupt_retention"
            )
        if not all(
            math.isfinite(value) and value >= 0.0
            for value in self.wear_per_use
        ):
            raise ValueError("wear_per_use values must be finite and non-negative")
        if (
            not math.isfinite(self.minimum_retention)
            or not 0.0 <= self.minimum_retention <= 1.0
        ):
            raise ValueError("minimum_retention must be between zero and one")


@dataclass(frozen=True)
class MechanicalCondition:
    """Host-side actuator damage/wear schedule hidden from observations.

    ``abrupt_retention`` is applied from ``onset_action`` onward. Progressive
    wear then reduces each channel once per unit of absolute requested command,
    down to ``minimum_retention``. The graph receives the requested opaque
    token and raw body response, never these values or the effective vector.
    """

    onset_action: int
    abrupt_retention: tuple[float, float] = (1.0, 1.0)
    wear_per_use: tuple[float, float] = (0.0, 0.0)
    minimum_retention: float = 0.2

    def __post_init__(self) -> None:
        if (
            isinstance(self.onset_action, bool)
            or not isinstance(self.onset_action, int)
            or self.onset_action < 0
        ):
            raise ValueError("onset_action must be a non-negative integer")
        for field, values in (
            ("abrupt_retention", self.abrupt_retention),
            ("wear_per_use", self.wear_per_use),
        ):
            if len(values) != 2 or not all(math.isfinite(value) for value in values):
                raise ValueError(f"{field} must contain two finite numbers")
        if not all(0.0 <= value <= 1.0 for value in self.abrupt_retention):
            raise ValueError("abrupt_retention values must be between zero and one")
        if not all(value >= 0.0 for value in self.wear_per_use):
            raise ValueError("wear_per_use values must be non-negative")
        if (
            not math.isfinite(self.minimum_retention)
            or not 0.0 <= self.minimum_retention <= 1.0
        ):
            raise ValueError("minimum_retention must be between zero and one")


@dataclass(frozen=True)
class MechanicalRandomization:
    """Fixed hidden dynamics parameters for one experimental world."""

    base_mass_scale: float = 1.0
    lateral_friction: float = 0.8
    rolling_friction: float = 0.0
    motor_force_scale: float = 1.0

    def __post_init__(self) -> None:
        for field in ("base_mass_scale", "lateral_friction", "motor_force_scale"):
            value = getattr(self, field)
            if not math.isfinite(value) or value <= 0.0:
                raise ValueError(f"{field} must be finite and positive")
        if not math.isfinite(self.rolling_friction) or self.rolling_friction < 0.0:
            raise ValueError("rolling_friction must be finite and non-negative")


_HARDWARE: Final[dict[str, _BodyHardware]] = {
    "r2d2": _BodyHardware(
        urdf="r2d2.urdf",
        base_height=0.5,
        mechanism="independent_velocity",
        channel_a_joints=(6, 7),
        channel_b_joints=(2, 3),
        velocity_scale=8.0,
        maximum_force=30.0,
    ),
    "husky": _BodyHardware(
        urdf="husky/husky.urdf",
        base_height=0.2,
        mechanism="independent_velocity",
        channel_a_joints=(2, 4),
        channel_b_joints=(3, 5),
        velocity_scale=8.0,
        maximum_force=60.0,
    ),
    "racecar": _BodyHardware(
        urdf="racecar/racecar.urdf",
        base_height=0.2,
        mechanism="velocity_and_position",
        channel_a_joints=(2, 3),
        channel_b_joints=(4, 6),
        velocity_scale=20.0,
        maximum_force=20.0,
        steering_scale=0.45,
        load_sensor_links=(5, 7, 2, 3),
    ),
    "racecar_active_aero": _BodyHardware(
        urdf="racecar/racecar.urdf",
        base_height=0.2,
        mechanism="velocity_and_position",
        channel_a_joints=(2, 3),
        channel_b_joints=(4, 6),
        velocity_scale=20.0,
        maximum_force=20.0,
        steering_scale=0.45,
        load_sensor_links=(5, 7, 2, 3),
        aerodynamic_hardware=_AerodynamicHardware(
            # Front-left, front-right, rear-left, rear-right. The graph sees
            # four independent opaque effector groups, not these locations.
            surface_points_body=(
                (0.16, 0.10, 0.06),
                (0.16, -0.10, 0.06),
                (-0.16, 0.10, 0.08),
                (-0.16, -0.10, 0.08),
            ),
        ),
    ),
}

# Scalar-token compatibility bodies used by the original ground experiment.
# Factorized bodies have a different graph/output contract and are enumerated
# separately so callers cannot accidentally route them through that runner.
FACTORIZED_MORPHOLOGIES: Final[tuple[str, ...]] = tuple(
    name
    for name, hardware in _HARDWARE.items()
    if hardware.aerodynamic_hardware is not None
)
MORPHOLOGIES: Final[tuple[str, ...]] = tuple(
    name for name in _HARDWARE if name not in FACTORIZED_MORPHOLOGIES
)
AERODYNAMIC_SURFACE_COUNT: Final[int] = len(
    _HARDWARE["racecar_active_aero"].aerodynamic_hardware.surface_points_body
)

# A common, deliberately unlabelled command lattice.  Token order is stable so
# graph state can persist an empirical action model without importing Python
# implementation details.
_ACTUATOR_VECTORS: Final[tuple[tuple[float, float], ...]] = (
    (0.0, 0.0),
    (1.0, 0.0),
    (-1.0, 0.0),
    (0.0, 1.0),
    (0.0, -1.0),
    (1.0, 1.0),
    (1.0, -1.0),
    (-1.0, 1.0),
    (-1.0, -1.0),
)
_TOKEN_TO_VECTOR: Final[dict[str, tuple[float, float]]] = {
    f"actuator_{index:03d}": vector
    for index, vector in enumerate(_ACTUATOR_VECTORS)
}

def _factorized_token_map(
    hardware: _BodyHardware,
) -> dict[str, tuple[int, float]]:
    """Derive primitives without materializing their Cartesian product."""
    aerodynamic = hardware.aerodynamic_hardware
    if aerodynamic is None:
        return {}
    group_count = len((
        hardware.channel_a_joints,
        hardware.channel_b_joints,
    )) + len(aerodynamic.surface_points_body)
    commands = (
        (group, command)
        for group in range(group_count)
        for command in (-1.0, 0.0, 1.0)
    )
    return {
        f"effector_{ordinal:03d}": command
        for ordinal, command in enumerate(commands)
    }


def _triple(values: Iterable[float], *, field: str) -> tuple[float, float, float]:
    result = tuple(float(value) for value in values)
    if len(result) != 3 or not all(math.isfinite(value) for value in result):
        raise ValueError(f"{field} must contain three finite numbers")
    return result


def _floats(values: Iterable[float]) -> tuple[float, ...]:
    return tuple(float(value) for value in values)


class PyBulletRobotWorld:
    """A deterministic, headless, fixed-step robot world.

    The object holds simulation state only.  ``apply`` is an actuator boundary,
    not an agent loop: the caller supplies one opaque token and receives the
    resulting sensor sample.
    """

    def __init__(
        self,
        morphology: str,
        *,
        time_step: float = 1.0 / 120.0,
        control_steps: int = 24,
        seed: int = 0,
        goal: Iterable[float] = (3.0, 0.0, 0.0),
        mechanical_condition: MechanicalCondition | None = None,
        aerodynamic_condition: AerodynamicCondition | None = None,
        mechanical_randomization: MechanicalRandomization | None = None,
        sensor_configuration: SensorimotorSensorConfiguration | None = None,
    ) -> None:
        if _bullet is None or _bullet_data is None:
            raise RuntimeError(
                "PyBullet is required for the robot world; install requirements-robot.txt"
            )
        if morphology not in _HARDWARE:
            choices = ", ".join(_HARDWARE)
            raise ValueError(f"unknown morphology {morphology!r}; expected one of {choices}")
        if not math.isfinite(time_step) or time_step <= 0.0:
            raise ValueError("time_step must be finite and positive")
        if (
            isinstance(control_steps, bool)
            or not isinstance(control_steps, int)
            or control_steps < 1
        ):
            raise ValueError("control_steps must be a positive integer")

        self.morphology = morphology
        self.time_step = float(time_step)
        self.control_steps = control_steps
        self.seed = int(seed)
        self.goal_position = _triple(goal, field="goal")
        self._mechanical_condition = mechanical_condition
        self._aerodynamic_condition = aerodynamic_condition
        self._mechanical_randomization = (
            mechanical_randomization or MechanicalRandomization()
        )
        self._sensor = SensorimotorTransducer(
            sample_period_seconds=self.time_step,
            configuration=sensor_configuration,
            seed=self.seed,
        )
        self._hardware = _HARDWARE[morphology]
        self._factorized_token_to_command = _factorized_token_map(
            self._hardware
        )
        self._client = _bullet.connect(_bullet.DIRECT)
        if self._client < 0:
            raise RuntimeError("PyBullet DIRECT connection failed")
        self._body: int | None = None
        self._body_mass = 0.0
        self._plane: int | None = None
        self._movable_joints: tuple[int, ...] = ()
        self._step_index = 0
        self._sensor.reset()
        self._action_index = 0
        self._wear_use = [0.0, 0.0]
        surface_count = len(
            self._hardware.aerodynamic_hardware.surface_points_body
        ) if self._hardware.aerodynamic_hardware is not None else 0
        if (
            aerodynamic_condition is not None
            and len(aerodynamic_condition.abrupt_retention) != surface_count
        ):
            raise ValueError(
                "aerodynamic_condition surface count does not match the body"
            )
        self._aerodynamic_wear_use = [0.0] * surface_count
        self._aerodynamic_commands = [0.0] * surface_count
        self._last_program_tokens: tuple[str, ...] = ()
        self._last_aerodynamic_dissipation_joules = 0.0
        self._last_aerodynamic_actuator_energy_joules = 0.0
        self._last_mean_wheel_normal_loads = (0.0, 0.0, 0.0, 0.0)
        self._last_mean_external_normal_force_newtons = 0.0
        self._last_token: str | None = None
        self._last_vector: tuple[float, float] | None = None
        self._last_supplied_energy_joules = 0.0
        self._last_absorbed_energy_joules = 0.0
        self._last_peak_actuator_power_watts = 0.0
        self.reset()

    def __enter__(self) -> "PyBulletRobotWorld":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def close(self) -> None:
        """Release the private Bullet client.  Safe to call more than once."""
        if self._client >= 0:
            if _bullet.isConnected(self._client):
                _bullet.disconnect(self._client)
            self._client = -1
        self._body = None
        self._body_mass = 0.0
        self._plane = None
        self._movable_joints = ()

    def actuator_options(self) -> tuple[dict[str, Any], ...]:
        """Return the stable opaque command alphabet and its raw vectors."""
        if self._hardware.aerodynamic_hardware is not None:
            return tuple(
                {
                    "token": token,
                    "group_ordinal": float(group),
                    "activation_magnitude": abs(float(_command)),
                    "effector_commands": ((int(group), float(_command)),),
                    "semantics": "unknown",
                }
                for token, (group, _command) in
                self._factorized_token_to_command.items()
            )
        return tuple(
            {
                "token": token,
                "vector": vector,
                "effector_commands": tuple(enumerate(vector)),
            }
            for token, vector in _TOKEN_TO_VECTOR.items()
        )

    def set_goal(self, goal: Iterable[float]) -> dict[str, Any]:
        """Change the external target without resetting body or graph state."""
        self.goal_position = _triple(goal, field="goal")
        return self.observe()

    def reset(self, *, goal: Iterable[float] | None = None) -> dict[str, Any]:
        """Recreate this morphology and return its initial raw observation."""
        self._require_open()
        self._sensor.reset()
        if goal is not None:
            self.goal_position = _triple(goal, field="goal")

        _bullet.resetSimulation(physicsClientId=self._client)
        _bullet.setPhysicsEngineParameter(
            fixedTimeStep=self.time_step,
            numSolverIterations=50,
            deterministicOverlappingPairs=1,
            physicsClientId=self._client,
        )
        _bullet.setAdditionalSearchPath(
            _bullet_data.getDataPath(), physicsClientId=self._client
        )
        _bullet.setGravity(0.0, 0.0, -9.81, physicsClientId=self._client)
        _bullet.setTimeStep(self.time_step, physicsClientId=self._client)

        self._plane = _bullet.loadURDF("plane.urdf", physicsClientId=self._client)
        self._body = _bullet.loadURDF(
            self._hardware.urdf,
            basePosition=(0.0, 0.0, self._hardware.base_height),
            baseOrientation=(0.0, 0.0, 0.0, 1.0),
            useFixedBase=False,
            physicsClientId=self._client,
        )
        self._movable_joints = tuple(
            joint_index
            for joint_index in range(
                _bullet.getNumJoints(self._body, physicsClientId=self._client)
            )
            if _bullet.getJointInfo(
                self._body, joint_index, physicsClientId=self._client
            )[2]
            != _bullet.JOINT_FIXED
        )
        base_mass = _bullet.getDynamicsInfo(
            self._body, -1, physicsClientId=self._client
        )[0]
        randomization = self._mechanical_randomization
        _bullet.changeDynamics(
            self._body,
            -1,
            mass=float(base_mass) * randomization.base_mass_scale,
            lateralFriction=randomization.lateral_friction,
            rollingFriction=randomization.rolling_friction,
            physicsClientId=self._client,
        )
        for link_index in range(
            _bullet.getNumJoints(self._body, physicsClientId=self._client)
        ):
            _bullet.changeDynamics(
                self._body,
                link_index,
                lateralFriction=randomization.lateral_friction,
                rollingFriction=randomization.rolling_friction,
                physicsClientId=self._client,
            )
        self._body_mass = sum(
            float(
                _bullet.getDynamicsInfo(
                    self._body,
                    link_index,
                    physicsClientId=self._client,
                )[0]
            )
            for link_index in range(
                -1,
                _bullet.getNumJoints(
                    self._body,
                    physicsClientId=self._client,
                ),
            )
        )
        self._release_motors()

        # Mechanical settling is outside the measured episode.  It prevents the
        # first graph-issued action from learning the effect of initial freefall.
        for _ in range(120):
            _bullet.stepSimulation(physicsClientId=self._client)
        _bullet.resetBaseVelocity(
            self._body,
            linearVelocity=(0.0, 0.0, 0.0),
            angularVelocity=(0.0, 0.0, 0.0),
            physicsClientId=self._client,
        )
        for joint_index in self._movable_joints:
            _bullet.resetJointState(
                self._body,
                joint_index,
                targetValue=0.0,
                targetVelocity=0.0,
                physicsClientId=self._client,
            )
        self._release_motors()
        self._step_index = 0
        self._action_index = 0
        self._wear_use = [0.0, 0.0]
        self._aerodynamic_wear_use = [
            0.0
        ] * len(self._aerodynamic_wear_use)
        self._aerodynamic_commands = [
            0.0
        ] * len(self._aerodynamic_commands)
        self._last_token = None
        self._last_vector = None
        self._last_program_tokens = ()
        self._last_supplied_energy_joules = 0.0
        self._last_absorbed_energy_joules = 0.0
        self._last_peak_actuator_power_watts = 0.0
        self._last_aerodynamic_dissipation_joules = 0.0
        self._last_aerodynamic_actuator_energy_joules = 0.0
        self._last_mean_wheel_normal_loads = (0.0, 0.0, 0.0, 0.0)
        self._last_mean_external_normal_force_newtons = 0.0
        return self.observe()

    def apply(self, token: str, *, steps: int | None = None) -> dict[str, Any]:
        """Apply one externally selected opaque token and advance physics."""
        return self.step(token, frames=steps)

    def step(self, token: str, *, frames: int | None = None) -> dict[str, Any]:
        """Transduce one opaque token and advance a fixed number of frames."""
        self._require_open()
        if self._hardware.aerodynamic_hardware is not None:
            return self.step_program((token,), frames=frames)
        try:
            vector = _TOKEN_TO_VECTOR[token]
        except (KeyError, TypeError) as exc:
            raise ValueError(f"unknown actuator token: {token!r}") from exc
        count = self.control_steps if frames is None else frames
        if isinstance(count, bool) or not isinstance(count, int) or count < 1:
            raise ValueError("frames must be a positive integer")

        effective_vector = self._conditioned_vector(vector)
        self._write_actuators(effective_vector)
        supplied = 0.0
        absorbed = 0.0
        peak_power = 0.0
        for _ in range(count):
            _bullet.stepSimulation(physicsClientId=self._client)
            states = _bullet.getJointStates(
                self._body,
                self._movable_joints,
                physicsClientId=self._client,
            )
            signed_power = tuple(
                float(state[1]) * float(state[3])
                for state in states
            )
            supplied_power = sum(max(0.0, value) for value in signed_power)
            absorbed_power = sum(max(0.0, -value) for value in signed_power)
            supplied += supplied_power * self.time_step
            absorbed += absorbed_power * self.time_step
            peak_power = max(peak_power, supplied_power + absorbed_power)
        self._last_supplied_energy_joules = supplied
        self._last_absorbed_energy_joules = absorbed
        self._last_peak_actuator_power_watts = peak_power
        self._step_index += count
        self._action_index += 1
        self._last_token = token
        self._last_vector = vector
        self._last_program_tokens = (token,)
        return self.observe()

    def step_program(
        self,
        tokens: Sequence[str],
        *,
        frames: int | None = None,
    ) -> dict[str, Any]:
        """Apply one graph-authored factorized motor program.

        Program construction and member selection belong to the graph. This
        boundary only validates that the received opaque tokens address
        independent hardware groups and translates them into simulator I/O.
        """
        self._require_open()
        if isinstance(tokens, (str, bytes)) or not tokens:
            raise ValueError(
                "a factorized motor program must contain opaque tokens"
            )
        program_tokens = tuple(tokens)
        if self._hardware.aerodynamic_hardware is None:
            if len(program_tokens) != 1:
                raise ValueError(
                    "non-factorized bodies accept exactly one actuator token"
                )
            return self.step(program_tokens[0], frames=frames)
        count = self.control_steps if frames is None else frames
        if isinstance(count, bool) or not isinstance(count, int) or count < 1:
            raise ValueError("frames must be a positive integer")
        group_count = len({
            group
            for group, _command in self._factorized_token_to_command.values()
        })
        commands = [0.0] * group_count
        seen_groups: set[int] = set()
        for token in program_tokens:
            try:
                group, command = self._factorized_token_to_command[token]
            except (KeyError, TypeError) as exc:
                raise ValueError(f"unknown factorized actuator token: {token!r}") from exc
            if group in seen_groups:
                raise ValueError(
                    "a motor program may command each effector group at most once"
                )
            seen_groups.add(group)
            commands[group] = command

        wheel_vector = self._conditioned_vector(
            (commands[0], commands[1])
        )
        self._aerodynamic_commands = list(
            self._conditioned_aerodynamic_commands(commands[2:])
        )
        self._write_actuators(wheel_vector)
        supplied = 0.0
        absorbed = 0.0
        peak_power = 0.0
        aerodynamic_dissipation = 0.0
        aerodynamic_actuator_energy = 0.0
        load_sums = [0.0, 0.0, 0.0, 0.0]
        external_normal_force_sum = 0.0
        wheel_links = self._hardware.load_sensor_links
        for _ in range(count):
            (
                drag_power,
                actuator_power,
                external_normal_force,
            ) = self._apply_aerodynamic_forces()
            external_normal_force_sum += external_normal_force
            _bullet.stepSimulation(physicsClientId=self._client)
            contacts = _bullet.getContactPoints(
                bodyA=self._body,
                physicsClientId=self._client,
            )
            for load_index, link_index in enumerate(wheel_links):
                load_sums[load_index] += sum(
                    max(0.0, float(contact[9]))
                    for contact in contacts
                    if int(contact[3]) == link_index
                )
            states = _bullet.getJointStates(
                self._body,
                self._movable_joints,
                physicsClientId=self._client,
            )
            signed_power = tuple(
                float(state[1]) * float(state[3])
                for state in states
            )
            supplied_power = (
                sum(max(0.0, value) for value in signed_power)
                + actuator_power
            )
            absorbed_power = sum(max(0.0, -value) for value in signed_power)
            supplied += supplied_power * self.time_step
            absorbed += absorbed_power * self.time_step
            aerodynamic_dissipation += drag_power * self.time_step
            aerodynamic_actuator_energy += actuator_power * self.time_step
            peak_power = max(
                peak_power,
                supplied_power + absorbed_power + drag_power,
            )
        self._last_supplied_energy_joules = supplied
        self._last_absorbed_energy_joules = absorbed
        self._last_peak_actuator_power_watts = peak_power
        self._last_aerodynamic_dissipation_joules = aerodynamic_dissipation
        self._last_aerodynamic_actuator_energy_joules = (
            aerodynamic_actuator_energy
        )
        self._last_mean_wheel_normal_loads = tuple(
            load / count for load in load_sums
        )
        self._last_mean_external_normal_force_newtons = (
            external_normal_force_sum / count
        )
        self._step_index += count
        self._action_index += 1
        self._last_token = (
            program_tokens[0] if len(program_tokens) == 1 else None
        )
        self._last_vector = wheel_vector
        self._last_program_tokens = program_tokens
        return self.observe()

    def observe(self) -> dict[str, Any]:
        """Read raw body, joint, contact, and target state without judgement."""
        self._require_open()
        assert self._body is not None
        position, orientation = _bullet.getBasePositionAndOrientation(
            self._body, physicsClientId=self._client
        )
        linear_velocity, angular_velocity = _bullet.getBaseVelocity(
            self._body, physicsClientId=self._client
        )
        joint_states = _bullet.getJointStates(
            self._body,
            tuple(range(_bullet.getNumJoints(self._body, physicsClientId=self._client))),
            physicsClientId=self._client,
        )
        contacts = _bullet.getContactPoints(
            bodyA=self._body, physicsClientId=self._client
        )
        instantaneous_wheel_normal_loads = tuple(
            sum(
                max(0.0, float(contact[9]))
                for contact in contacts
                if int(contact[3]) == link_index
            )
            for link_index in self._hardware.load_sensor_links
        )
        wheel_normal_loads = (
            self._last_mean_wheel_normal_loads
            if self._hardware.aerodynamic_hardware is not None
            and self._step_index > 0
            else instantaneous_wheel_normal_loads
        )
        sensor_sample = self._sensor.sample(
            position=position,
            orientation_xyzw=orientation,
            linear_velocity=linear_velocity,
            angular_velocity=angular_velocity,
            contact_count=float(len(contacts)),
            sample_id=self._step_index,
        )
        return {
            "morphology": self.morphology,
            "seed": self.seed,
            "body_mass": self._body_mass,
            "gravity_acceleration": 9.81,
            "step_index": self._step_index,
            "sim_time": self._step_index * self.time_step,
            "body_id": self._body,
            "base_position": _floats(position),
            "base_orientation_xyzw": _floats(orientation),
            "base_linear_velocity": _floats(linear_velocity),
            "base_angular_velocity": _floats(angular_velocity),
            "joints": tuple(
                {
                    "index": index,
                    "position": float(state[0]),
                    "velocity": float(state[1]),
                    "reaction_forces": _floats(state[2]),
                    "applied_torque": float(state[3]),
                }
                for index, state in enumerate(joint_states)
            ),
            "contacts": tuple(self._contact_observation(contact) for contact in contacts),
            "supplied_energy_joules": self._last_supplied_energy_joules,
            "absorbed_energy_joules": self._last_absorbed_energy_joules,
            "peak_actuator_power_watts": self._last_peak_actuator_power_watts,
            "aerodynamic_dissipation_joules": (
                self._last_aerodynamic_dissipation_joules
            ),
            "aerodynamic_actuator_energy_joules": (
                self._last_aerodynamic_actuator_energy_joules
            ),
            "wheel_normal_loads": wheel_normal_loads,
            "external_normal_force_newtons": (
                self._last_mean_external_normal_force_newtons
            ),
            # Instantaneous total: the sum of normal-force magnitudes over
            # every contact point involving this body at THIS snapshot (not
            # a peak, not thresholded). Distinct from
            # external_normal_force_newtons above, which is mean aerodynamic
            # downforce, not a measured contact force.
            "contact_force_newtons": float(sum(
                max(0.0, float(contact[9])) for contact in contacts
            )),
            "goal_position": self.goal_position,
            "last_actuator_token": self._last_token,
            "last_motor_program_tokens": self._last_program_tokens,
            "last_actuator_vector": self._last_vector,
            "actuator_activation_seconds": self.time_step,
            **sensor_sample,
        }

    def _render_rgb_array(
        self,
        *,
        width: int = 960,
        height: int = 540,
    ) -> Any:
        """Render a read-only chase-camera frame for presentation tooling."""
        self._require_open()
        if width < 1 or height < 1:
            raise ValueError("render dimensions must be positive")
        assert self._body is not None
        position, _orientation = _bullet.getBasePositionAndOrientation(
            self._body,
            physicsClientId=self._client,
        )
        view = _bullet.computeViewMatrixFromYawPitchRoll(
            cameraTargetPosition=(
                float(position[0]),
                float(position[1]),
                max(0.25, float(position[2])),
            ),
            distance=3.4 if self.morphology == "r2d2" else 4.2,
            yaw=42.0,
            pitch=-24.0,
            roll=0.0,
            upAxisIndex=2,
        )
        projection = _bullet.computeProjectionMatrixFOV(
            fov=52.0,
            aspect=float(width) / float(height),
            nearVal=0.05,
            farVal=100.0,
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
            height,
            width,
            4,
        )[..., :3]

    def _require_open(self) -> None:
        if self._client < 0 or not _bullet.isConnected(self._client):
            raise RuntimeError("PyBulletRobotWorld is closed")

    def _release_motors(self) -> None:
        assert self._body is not None
        if self._movable_joints:
            _bullet.setJointMotorControlArray(
                self._body,
                self._movable_joints,
                _bullet.VELOCITY_CONTROL,
                targetVelocities=(0.0,) * len(self._movable_joints),
                forces=(0.0,) * len(self._movable_joints),
                physicsClientId=self._client,
            )

    def _conditioned_vector(
        self, requested: tuple[float, float]
    ) -> tuple[float, float]:
        condition = self._mechanical_condition
        if condition is None or self._action_index < condition.onset_action:
            return requested

        effective = []
        for channel, command in enumerate(requested):
            self._wear_use[channel] += abs(command)
            wear_retention = max(
                condition.minimum_retention,
                1.0 - condition.wear_per_use[channel] * self._wear_use[channel],
            )
            effective.append(
                command
                * condition.abrupt_retention[channel]
                * wear_retention
            )
        return float(effective[0]), float(effective[1])

    def _conditioned_aerodynamic_commands(
        self,
        requested: Sequence[float],
    ) -> tuple[float, ...]:
        condition = self._aerodynamic_condition
        if condition is None or self._action_index < condition.onset_action:
            return tuple(float(command) for command in requested)
        wear = condition.wear_per_use or (0.0,) * len(requested)
        effective = []
        for surface, command in enumerate(requested):
            self._aerodynamic_wear_use[surface] += abs(command)
            retention = max(
                condition.minimum_retention,
                1.0 - wear[surface] * self._aerodynamic_wear_use[surface],
            )
            effective.append(
                float(command)
                * condition.abrupt_retention[surface]
                * retention
            )
        return tuple(effective)

    def _apply_aerodynamic_forces(self) -> tuple[float, float, float]:
        """Apply hidden flow-conditioned forces and return raw power receipts."""
        hardware = self._hardware.aerodynamic_hardware
        if hardware is None or not any(self._aerodynamic_commands):
            return 0.0, 0.0, 0.0
        assert self._body is not None
        position, orientation = _bullet.getBasePositionAndOrientation(
            self._body,
            physicsClientId=self._client,
        )
        velocity, _angular_velocity = _bullet.getBaseVelocity(
            self._body,
            physicsClientId=self._client,
        )
        rotation = _np.asarray(
            _bullet.getMatrixFromQuaternion(orientation),
            dtype=float,
        ).reshape(3, 3)
        horizontal_velocity = _np.asarray(
            (float(velocity[0]), float(velocity[1]), 0.0),
            dtype=float,
        )
        flow_speed = float(_np.linalg.norm(horizontal_velocity))
        if flow_speed <= 0.0:
            return (
                0.0,
                sum(abs(command) for command in self._aerodynamic_commands)
                * hardware.actuator_power_watts_per_surface,
                0.0,
            )
        flow_scale = (
            flow_speed / hardware.reference_flow_speed
        ) ** 2
        weight = self._body_mass * 9.81
        body_down = -(rotation @ _np.asarray((0.0, 0.0, 1.0)))
        drag_direction = -horizontal_velocity / flow_speed
        drag_power = 0.0
        total_downforce = 0.0
        for point_body, command in zip(
            hardware.surface_points_body,
            self._aerodynamic_commands,
        ):
            downforce_command = max(0.0, command)
            airbrake_command = max(0.0, -command)
            downforce = (
                weight
                * hardware.downforce_weight_fraction_at_reference
                * flow_scale
                * downforce_command
            )
            drag = (
                weight
                * hardware.drag_weight_fraction_at_reference
                * flow_scale
                * (
                    downforce_command
                    + hardware.airbrake_drag_multiplier * airbrake_command
                )
            )
            force = body_down * downforce + drag_direction * drag
            point_world = (
                _np.asarray(position, dtype=float)
                + rotation @ _np.asarray(point_body, dtype=float)
            )
            _bullet.applyExternalForce(
                self._body,
                -1,
                forceObj=tuple(float(value) for value in force),
                posObj=tuple(float(value) for value in point_world),
                flags=_bullet.WORLD_FRAME,
                physicsClientId=self._client,
            )
            drag_power += drag * flow_speed
            total_downforce += downforce
        actuator_power = (
            sum(abs(command) for command in self._aerodynamic_commands)
            * hardware.actuator_power_watts_per_surface
        )
        return drag_power, actuator_power, total_downforce

    def _write_actuators(self, vector: tuple[float, float]) -> None:
        assert self._body is not None
        hardware = self._hardware
        if hardware.mechanism == "independent_velocity":
            for joints, command in (
                (hardware.channel_a_joints, vector[0]),
                (hardware.channel_b_joints, vector[1]),
            ):
                _bullet.setJointMotorControlArray(
                    self._body,
                    joints,
                    _bullet.VELOCITY_CONTROL,
                    targetVelocities=(command * hardware.velocity_scale,) * len(joints),
                    forces=(
                        hardware.maximum_force
                        * self._mechanical_randomization.motor_force_scale,
                    )
                    * len(joints),
                    physicsClientId=self._client,
                )
            return

        # The only other immutable hardware schema is drive velocity plus hinge
        # position.  This branch translates vector slots to motor controller I/O;
        # it does not attach behavioural meaning to either slot.
        _bullet.setJointMotorControlArray(
            self._body,
            hardware.channel_a_joints,
            _bullet.VELOCITY_CONTROL,
            targetVelocities=(vector[0] * hardware.velocity_scale,)
            * len(hardware.channel_a_joints),
            forces=(
                hardware.maximum_force
                * self._mechanical_randomization.motor_force_scale,
            )
            * len(hardware.channel_a_joints),
            physicsClientId=self._client,
        )
        _bullet.setJointMotorControlArray(
            self._body,
            hardware.channel_b_joints,
            _bullet.POSITION_CONTROL,
            targetPositions=(vector[1] * hardware.steering_scale,)
            * len(hardware.channel_b_joints),
            forces=(
                hardware.maximum_force
                * self._mechanical_randomization.motor_force_scale,
            )
            * len(hardware.channel_b_joints),
            physicsClientId=self._client,
        )

    @staticmethod
    def _contact_observation(contact: tuple[Any, ...]) -> dict[str, Any]:
        return {
            "body_a": int(contact[1]),
            "body_b": int(contact[2]),
            "link_a": int(contact[3]),
            "link_b": int(contact[4]),
            "position_a": _floats(contact[5]),
            "position_b": _floats(contact[6]),
            "normal_on_b": _floats(contact[7]),
            "distance": float(contact[8]),
            "normal_force": float(contact[9]),
            "lateral_friction_1": float(contact[10]),
            "lateral_direction_1": _floats(contact[11]),
            "lateral_friction_2": float(contact[12]),
            "lateral_direction_2": _floats(contact[13]),
        }


__all__ = [
    "AERODYNAMIC_SURFACE_COUNT",
    "AerodynamicCondition",
    "FACTORIZED_MORPHOLOGIES",
    "MORPHOLOGIES",
    "MechanicalCondition",
    "MechanicalRandomization",
    "PyBulletRobotWorld",
]
