"""Mechanical gym-pybullet-drones boundary for graph-native flight.

The simulator owns rigid-body dynamics and the Crazyflie's low-level velocity
controller. This adapter maps stable opaque tokens to controller inputs,
advances fixed-step physics, and returns raw sensors. It contains no action
selection, reward, learning, goal judgment, or flight policy.
"""
from __future__ import annotations

import contextlib
from dataclasses import dataclass
import io
import math
from typing import Any, Final, Iterable
import warnings

from domains.sensorimotor_transducer import (
    SensorimotorSensorConfiguration,
    SensorimotorTransducer,
)

try:
    import numpy as _np
    import pybullet as _bullet
    from gym_pybullet_drones.envs.VelocityAviary import VelocityAviary
    from gym_pybullet_drones.utils.enums import DroneModel, Physics
except ModuleNotFoundError:  # Keep installations without drone extras importable.
    _np = None
    _bullet = None
    VelocityAviary = None
    DroneModel = None
    Physics = None


SIMULATOR_NAME: Final = "gym-pybullet-drones"
SIMULATOR_COMMIT: Final = "e712698a05a80728b06572819dcf044596707754"
PHYSICS_FREQUENCY_HZ: Final = 240
CONTROL_FREQUENCY_HZ: Final = 60
ACTION_DURATION_SECONDS: Final = 0.5
INITIAL_POSITION: Final = (0.0, 0.0, 0.25)
YAW_COMMAND_RATE_RADIANS_PER_SECOND: Final = 0.25

# A body-independent, deliberately unlabelled velocity-command alphabet.
# The fourth slot is the simulator's normalized speed request. Only this
# mechanical adapter sees the vectors; the graph receives the tokens.
_BASE_COMMAND_VECTORS: Final[tuple[tuple[float, float, float, float], ...]] = (
    (0.0, 0.0, 0.0, 0.0),
    (1.0, 0.0, 0.0, 1.0),
    (-1.0, 0.0, 0.0, 1.0),
    (0.0, 1.0, 0.0, 1.0),
    (0.0, -1.0, 0.0, 1.0),
    (0.0, 0.0, 1.0, 1.0),
    (0.0, 0.0, -1.0, 1.0),
)
_YAW_COMMAND_VECTORS: Final = (
    (0.0, 0.0, 1.0, 0.0),
    (0.0, 0.0, -1.0, 0.0),
)
AERIAL_ACTUATOR_COUNT: Final = len(_BASE_COMMAND_VECTORS)
AERIAL_YAW_ACTUATOR_COUNT: Final = len(_YAW_COMMAND_VECTORS)


@dataclass(frozen=True)
class AerialMechanicalCondition:
    """Hidden abrupt motor-speed retention applied during an action sequence."""

    onset_action: int
    motor_rpm_retention: tuple[float, float, float, float]

    def __post_init__(self) -> None:
        if (
            isinstance(self.onset_action, bool)
            or not isinstance(self.onset_action, int)
            or self.onset_action < 0
        ):
            raise ValueError("onset_action must be a non-negative integer")
        if len(self.motor_rpm_retention) != 4 or not all(
            math.isfinite(value) and 0.0 <= value <= 1.0
            for value in self.motor_rpm_retention
        ):
            raise ValueError(
                "motor_rpm_retention must contain four values from zero to one"
            )


@dataclass(frozen=True)
class AerialPropellerCondition:
    """Hidden averaged aerodynamic loss from a damaged propeller."""

    onset_action: int
    thrust_retention: tuple[float, float, float, float]
    torque_retention: tuple[float, float, float, float]

    def __post_init__(self) -> None:
        if (
            isinstance(self.onset_action, bool)
            or not isinstance(self.onset_action, int)
            or self.onset_action < 0
        ):
            raise ValueError("onset_action must be a non-negative integer")
        for field, values in (
            ("thrust_retention", self.thrust_retention),
            ("torque_retention", self.torque_retention),
        ):
            if len(values) != 4 or not all(
                math.isfinite(value) and 0.0 <= value <= 1.0
                for value in values
            ):
                raise ValueError(
                    f"{field} must contain four values from zero to one"
                )


class _FaultableVelocityAviary(VelocityAviary if VelocityAviary else object):
    """Simulator extension for independent motor and propeller failures."""

    def __init__(self, *args, **kwargs) -> None:
        self._motor_rpm_retention = (
            _np.ones(4, dtype=float) if _np is not None else None
        )
        self._prop_thrust_retention = (
            _np.ones(4, dtype=float) if _np is not None else None
        )
        self._prop_torque_retention = (
            _np.ones(4, dtype=float) if _np is not None else None
        )
        self._direct_rpm_command = None
        super().__init__(*args, **kwargs)

    def _set_motor_rpm_retention(
        self,
        retention: tuple[float, float, float, float],
    ) -> None:
        self._motor_rpm_retention = _np.asarray(retention, dtype=float)

    def _set_propeller_retention(
        self,
        thrust: tuple[float, float, float, float],
        torque: tuple[float, float, float, float],
    ) -> None:
        self._prop_thrust_retention = _np.asarray(thrust, dtype=float)
        self._prop_torque_retention = _np.asarray(torque, dtype=float)

    def _set_direct_rpm_command(self, rpm) -> None:
        self._direct_rpm_command = (
            None if rpm is None else _np.asarray(rpm, dtype=float)
        )

    def _preprocessAction(self, action):
        if self._direct_rpm_command is not None:
            return (
                _np.tile(self._direct_rpm_command, (self.NUM_DRONES, 1))
                * self._motor_rpm_retention
            )
        rpm = _np.zeros((self.NUM_DRONES, 4))
        for drone_index in range(action.shape[0]):
            state = self._getDroneStateVector(drone_index)
            command = action[drone_index]
            yaw_command = (
                command[0] == 0.0
                and command[1] == 0.0
                and command[3] == 0.0
                and abs(command[2]) == 1.0
            )
            if yaw_command:
                yaw_rate = (
                    float(command[2]) * YAW_COMMAND_RATE_RADIANS_PER_SECOND
                )
                target_velocity = _np.zeros(3)
                target_yaw = state[9] + yaw_rate * self.CTRL_TIMESTEP
                target_rates = _np.asarray([0.0, 0.0, yaw_rate])
            else:
                velocity = command[0:3]
                magnitude = _np.linalg.norm(velocity)
                direction = velocity / magnitude if magnitude != 0.0 else velocity
                target_velocity = (
                    self.SPEED_LIMIT * abs(command[3]) * direction
                )
                target_yaw = state[9]
                target_rates = _np.zeros(3)
            rpm[drone_index], _, _ = self.ctrl[drone_index].computeControl(
                control_timestep=self.CTRL_TIMESTEP,
                cur_pos=state[0:3],
                cur_quat=state[3:7],
                cur_vel=state[10:13],
                cur_ang_vel=state[13:16],
                target_pos=state[0:3],
                target_rpy=_np.asarray([0.0, 0.0, target_yaw]),
                target_vel=target_velocity,
                target_rpy_rates=target_rates,
            )
        return rpm * self._motor_rpm_retention

    def _physics(self, rpm, nth_drone):
        """Apply per-propeller aerodynamic effectiveness at unchanged RPM."""
        forces = _np.asarray(rpm**2) * self.KF * self._prop_thrust_retention
        torques = _np.asarray(rpm**2) * self.KM * self._prop_torque_retention
        if self.DRONE_MODEL == DroneModel.RACE:
            torques = -torques
        yaw_torque = -torques[0] + torques[1] - torques[2] + torques[3]
        for propeller, force in enumerate(forces):
            _bullet.applyExternalForce(
                self.DRONE_IDS[nth_drone],
                propeller,
                forceObj=[0, 0, force],
                posObj=[0, 0, 0],
                flags=_bullet.LINK_FRAME,
                physicsClientId=self.CLIENT,
            )
        _bullet.applyExternalTorque(
            self.DRONE_IDS[nth_drone],
            4,
            torqueObj=[0, 0, yaw_torque],
            flags=_bullet.LINK_FRAME,
            physicsClientId=self.CLIENT,
        )


def _triple(values: Iterable[float], *, field: str) -> tuple[float, float, float]:
    result = tuple(float(value) for value in values)
    if len(result) != 3 or not all(math.isfinite(value) for value in result):
        raise ValueError(f"{field} must contain three finite numbers")
    return result


def _floats(values: Iterable[float]) -> tuple[float, ...]:
    return tuple(float(value) for value in values)


class GymPyBulletDroneWorld:
    """Deterministic single-Crazyflie world with opaque high-level actuators."""

    def __init__(
        self,
        *,
        seed: int = 0,
        goal: Iterable[float] = (0.75, 0.75, 1.0),
        initial_position: Iterable[float] = INITIAL_POSITION,
        action_duration_seconds: float = ACTION_DURATION_SECONDS,
        mechanical_condition: AerialMechanicalCondition | None = None,
        propeller_condition: AerialPropellerCondition | None = None,
        enable_yaw_actuators: bool = False,
        enable_direct_motor_actuators: bool = False,
        sensor_configuration: SensorimotorSensorConfiguration | None = None,
    ) -> None:
        if (
            _np is None
            or _bullet is None
            or VelocityAviary is None
            or DroneModel is None
            or Physics is None
        ):
            raise RuntimeError(
                "gym-pybullet-drones is required; install requirements-drone.txt"
            )
        if (
            not math.isfinite(action_duration_seconds)
            or action_duration_seconds <= 0.0
        ):
            raise ValueError("action_duration_seconds must be finite and positive")
        self.seed = int(seed)
        self.goal_position = _triple(goal, field="goal")
        self.initial_position = _triple(initial_position, field="initial_position")
        self.action_duration_seconds = float(action_duration_seconds)
        self._sensor = SensorimotorTransducer(
            sample_period_seconds=1.0 / CONTROL_FREQUENCY_HZ,
            configuration=sensor_configuration,
            seed=self.seed,
        )
        self._mechanical_condition = mechanical_condition
        self._propeller_condition = propeller_condition
        self._direct_motor_authority_enabled = bool(
            enable_direct_motor_actuators
        )
        command_vectors = (
            _BASE_COMMAND_VECTORS + _YAW_COMMAND_VECTORS
            if enable_yaw_actuators
            else _BASE_COMMAND_VECTORS
        )
        self._token_to_vector = {
            f"flight_actuator_{index:03d}": vector
            for index, vector in enumerate(command_vectors)
        }
        self._control_steps = round(
            self.action_duration_seconds * CONTROL_FREQUENCY_HZ
        )
        if self._control_steps < 1:
            raise ValueError("action duration is shorter than one control tick")
        self._environment = None
        self._observation = None
        self._step_index = 0
        self._sensor.reset()
        self._sim_time_seconds = 0.0
        self._action_index = 0
        self._last_token: str | None = None
        self._last_vector: tuple[float, float, float, float] | None = None
        self._last_supplied_energy_joules = 0.0
        self._last_peak_actuator_power_watts = 0.0
        self.reset()

    def __enter__(self) -> "GymPyBulletDroneWorld":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def close(self) -> None:
        """Release the simulator's private Bullet client."""
        if self._environment is not None:
            self._environment.close()
            self._environment = None
        self._observation = None

    def actuator_options(self) -> tuple[dict[str, Any], ...]:
        """Return stable opaque tokens and host-only mechanical vectors."""
        return tuple(
            {
                "token": token,
                "vector": vector,
                "effector_commands": tuple(enumerate(vector)),
            }
            for token, vector in self._token_to_vector.items()
        )

    def body_parameters(self) -> dict[str, float]:
        """Expose measured body constants needed for graph-authored control."""
        self._require_open()
        return {
            "body_mass": float(self._environment.M),
            "body_arm_length": float(self._environment.L),
            "motor_thrust_coefficient": float(self._environment.KF),
            "maximum_motor_rpm": float(self._environment.MAX_RPM),
            "gravity_acceleration": float(self._environment.G),
        }

    def set_goal(self, goal: Iterable[float]) -> dict[str, Any]:
        """Change the external target without changing vehicle state."""
        self.goal_position = _triple(goal, field="goal")
        return self.observe()

    def reset(self, *, goal: Iterable[float] | None = None) -> dict[str, Any]:
        """Recreate the official Crazyflie world and return raw state."""
        if goal is not None:
            self.goal_position = _triple(goal, field="goal")
        self.close()
        initial_xyzs = _np.asarray([self.initial_position], dtype=float)
        # BaseAviary prints immutable URDF constants on construction. They are
        # not sensor data, so keep the experiment trace machine-readable.
        with (
            contextlib.redirect_stdout(io.StringIO()),
            warnings.catch_warnings(),
        ):
            warnings.filterwarnings(
                "ignore",
                message=r".*Box (low|high)'s precision lowered.*",
                category=UserWarning,
            )
            self._environment = _FaultableVelocityAviary(
                drone_model=DroneModel.CF2X,
                num_drones=1,
                initial_xyzs=initial_xyzs,
                physics=Physics.PYB,
                pyb_freq=PHYSICS_FREQUENCY_HZ,
                ctrl_freq=CONTROL_FREQUENCY_HZ,
                gui=False,
                record=False,
                obstacles=False,
                user_debug_gui=False,
            )
            self._observation, _info = self._environment.reset(seed=self.seed)
        self._step_index = 0
        self._sensor.reset()
        self._sim_time_seconds = 0.0
        self._action_index = 0
        self._control_steps = round(
            self.action_duration_seconds * CONTROL_FREQUENCY_HZ
        )
        self._last_token = None
        self._last_vector = None
        self._last_supplied_energy_joules = 0.0
        self._last_peak_actuator_power_watts = 0.0
        return self.observe()

    def apply(self, token: str) -> dict[str, Any]:
        """Apply one graph-selected token."""
        return self.step(token)

    def step(self, token: str) -> dict[str, Any]:
        """Transduce one opaque token and advance a fixed physical duration."""
        return self._step_token(token, control_steps=self._control_steps)

    def step_control_tick(self, token: str) -> dict[str, Any]:
        """Transduce one opaque token for one low-level control tick."""
        return self._step_token(token, control_steps=1)

    def set_control_frequency(self, frequency_hz: int) -> None:
        """Set a mechanically valid control cadence up to the physics rate."""
        self._require_open()
        if (
            isinstance(frequency_hz, bool)
            or not isinstance(frequency_hz, int)
            or frequency_hz <= 0
            or frequency_hz > self._environment.PYB_FREQ
            or self._environment.PYB_FREQ % frequency_hz != 0
        ):
            raise ValueError(
                "frequency_hz must be a positive integer divisor of the "
                "simulator physics frequency"
            )
        self._environment.CTRL_FREQ = frequency_hz
        self._environment.PYB_STEPS_PER_CTRL = (
            self._environment.PYB_FREQ // frequency_hz
        )
        self._environment.CTRL_TIMESTEP = 1.0 / frequency_hz
        self._control_steps = round(
            self.action_duration_seconds * frequency_hz
        )

    def _step_token(self, token: str, *, control_steps: int) -> dict[str, Any]:
        self._require_open()
        try:
            vector = self._token_to_vector[token]
        except (KeyError, TypeError) as exc:
            raise ValueError(f"unknown flight actuator token: {token!r}") from exc
        action = _np.asarray([vector], dtype=_np.float32)
        self._apply_current_conditions()
        self._environment._set_direct_rpm_command(None)
        supplied_energy = 0.0
        peak_power = 0.0
        for _ in range(control_steps):
            self._observation, _reward, _terminated, _truncated, _info = (
                self._environment.step(action)
            )
            rpm = _np.asarray(self._observation[0][16:20], dtype=float)
            angular_speed = rpm * (2.0 * math.pi / 60.0)
            shaft_power = float(_np.sum(
                self._environment.KM * rpm**2 * angular_speed
            ))
            supplied_energy += (
                shaft_power / self._environment.CTRL_FREQ
            )
            peak_power = max(peak_power, shaft_power)
        self._last_supplied_energy_joules = supplied_energy
        self._last_peak_actuator_power_watts = peak_power
        self._step_index += control_steps
        self._sim_time_seconds += (
            control_steps / self._environment.CTRL_FREQ
        )
        self._action_index += 1
        self._last_token = token
        self._last_vector = vector
        return self.observe()

    def step_motor_rpm(
        self,
        rpm: Iterable[float],
        *,
        command_token: str = "graph_direct_motor_command",
    ) -> dict[str, Any]:
        """Apply graph-authored raw motor RPM for one control tick."""
        self._require_open()
        if not self._direct_motor_authority_enabled:
            raise RuntimeError("direct motor authority is not enabled")
        command = _floats(rpm)
        if (
            len(command) != 4
            or not all(
                math.isfinite(value)
                and 0.0 <= value <= self._environment.MAX_RPM
                for value in command
            )
        ):
            raise ValueError(
                "rpm must contain four finite values within simulator limits"
            )
        if not isinstance(command_token, str) or not command_token:
            raise ValueError("command_token must be a non-empty string")
        self._apply_current_conditions()
        self._environment._set_direct_rpm_command(command)
        action = _np.zeros((1, 4), dtype=_np.float32)
        self._observation, _reward, _terminated, _truncated, _info = (
            self._environment.step(action)
        )
        observed_rpm = _np.asarray(
            self._observation[0][16:20],
            dtype=float,
        )
        angular_speed = observed_rpm * (2.0 * math.pi / 60.0)
        shaft_power = float(_np.sum(
            self._environment.KM * observed_rpm**2 * angular_speed
        ))
        self._last_supplied_energy_joules = (
            shaft_power / self._environment.CTRL_FREQ
        )
        self._last_peak_actuator_power_watts = shaft_power
        self._step_index += 1
        self._sim_time_seconds += 1.0 / self._environment.CTRL_FREQ
        self._action_index += 1
        self._last_token = command_token
        self._last_vector = command
        return self.observe()

    def _apply_current_conditions(self) -> None:
        condition = self._mechanical_condition
        if condition is not None and self._action_index >= condition.onset_action:
            self._environment._set_motor_rpm_retention(
                condition.motor_rpm_retention
            )
        propeller = self._propeller_condition
        if (
            propeller is not None
            and self._action_index >= propeller.onset_action
        ):
            self._environment._set_propeller_retention(
                propeller.thrust_retention,
                propeller.torque_retention,
            )

    def observe(self) -> dict[str, Any]:
        """Read raw pose, velocity, motor, contact, and target state."""
        self._require_open()
        state = self._observation[0]
        drone_id = int(self._environment.DRONE_IDS[0])
        contacts = _bullet.getContactPoints(
            bodyA=drone_id,
            physicsClientId=self._environment.CLIENT,
        )
        contact_force_newtons = sum(
            max(0.0, float(contact[9])) for contact in contacts
        )
        sensor_sample = self._sensor.sample(
            position=state[0:3],
            orientation_xyzw=state[3:7],
            linear_velocity=state[10:13],
            angular_velocity=state[13:16],
            contact_count=float(len(contacts)),
            sample_id=self._step_index,
        )
        return {
            "simulator": SIMULATOR_NAME,
            "simulator_commit": SIMULATOR_COMMIT,
            "seed": self.seed,
            "step_index": self._step_index,
            "sim_time": self._sim_time_seconds,
            "body_id": drone_id,
            "base_position": _floats(state[0:3]),
            "base_orientation_xyzw": _floats(state[3:7]),
            "base_linear_velocity": _floats(state[10:13]),
            "base_angular_velocity": _floats(state[13:16]),
            "motor_rpm": _floats(state[16:20]),
            "supplied_energy_joules": self._last_supplied_energy_joules,
            "absorbed_energy_joules": 0.0,
            "peak_actuator_power_watts": self._last_peak_actuator_power_watts,
            "contact_count": len(contacts),
            "contact_force_newtons": contact_force_newtons,
            "goal_position": self.goal_position,
            "last_actuator_token": self._last_token,
            "last_actuator_vector": self._last_vector,
            "actuator_activation_seconds": 1.0 / CONTROL_FREQUENCY_HZ,
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
        observation = self.observe()
        position = observation["base_position"]
        view = _bullet.computeViewMatrixFromYawPitchRoll(
            cameraTargetPosition=(
                float(position[0]),
                float(position[1]),
                max(0.35, float(position[2])),
            ),
            distance=2.3,
            yaw=38.0,
            pitch=-18.0,
            roll=0.0,
            upAxisIndex=2,
        )
        projection = _bullet.computeProjectionMatrixFOV(
            fov=48.0,
            aspect=float(width) / float(height),
            nearVal=0.03,
            farVal=100.0,
        )
        image = _bullet.getCameraImage(
            width,
            height,
            viewMatrix=view,
            projectionMatrix=projection,
            renderer=_bullet.ER_TINY_RENDERER,
            physicsClientId=self._environment.CLIENT,
        )
        return _np.asarray(image[2], dtype=_np.uint8).reshape(
            height,
            width,
            4,
        )[..., :3]

    def _require_open(self) -> None:
        if self._environment is None or self._observation is None:
            raise RuntimeError("GymPyBulletDroneWorld is closed")


__all__ = [
    "ACTION_DURATION_SECONDS",
    "AERIAL_ACTUATOR_COUNT",
    "AERIAL_YAW_ACTUATOR_COUNT",
    "AerialMechanicalCondition",
    "AerialPropellerCondition",
    "CONTROL_FREQUENCY_HZ",
    "GymPyBulletDroneWorld",
    "INITIAL_POSITION",
    "PHYSICS_FREQUENCY_HZ",
    "SIMULATOR_COMMIT",
    "SIMULATOR_NAME",
    "YAW_COMMAND_RATE_RADIANS_PER_SECOND",
]
