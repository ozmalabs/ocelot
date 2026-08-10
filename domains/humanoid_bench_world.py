"""Thin mechanical boundary for the official MuJoCo HumanoidBench.

The boundary deliberately bypasses HumanoidBench's fixed ten-frame task step:
the graph supplies the physics-frame horizon and an opaque compatible actuator
bundle. HumanoidBench still owns its model, task reset, reward, and termination
definitions. No benchmark policy or anatomical actuator name is exposed to
the graph.
"""
from __future__ import annotations

import importlib
import math
from pathlib import Path
import sys
from typing import Any, Iterable

import numpy as np

from domains.pybullet_humanoid_world import HumanoidBodyConfiguration
from domains.sensorimotor_transducer import (
    SensorimotorSensorConfiguration,
    SensorimotorTransducer,
)


class HumanoidBenchWorld:
    """Mechanical normalized-position authority over a HumanoidBench robot."""

    def __init__(
        self,
        configuration: HumanoidBodyConfiguration,
        *,
        simulator_root: Path,
        environment_id: str,
        seed: int = 0,
        render_mode: str | None = None,
        sensor_configuration: SensorimotorSensorConfiguration | None = None,
    ) -> None:
        root = simulator_root.resolve()
        if not (root / "humanoid_bench" / "__init__.py").is_file():
            raise RuntimeError(
                f"HumanoidBench package not found under {root}"
            )
        if str(root) not in sys.path:
            sys.path.insert(0, str(root))
        try:
            gym = importlib.import_module("gymnasium")
            importlib.import_module("humanoid_bench")
            self._mujoco = importlib.import_module("mujoco")
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "HumanoidBench requires mujoco and dm_control"
            ) from exc

        self.configuration = configuration
        self.simulator_root = root
        self.environment_id = environment_id
        self.seed = int(seed)
        self._sensor = SensorimotorTransducer(
            sample_period_seconds=configuration.time_step,
            configuration=sensor_configuration,
            seed=self.seed,
        )
        self._env = gym.make(
            environment_id,
            render_mode=render_mode,
            randomness=0,
        )
        self._world = self._env.unwrapped
        if not math.isclose(
            float(self._world.model.opt.timestep),
            configuration.time_step,
            rel_tol=0.0,
            abs_tol=1e-12,
        ):
            raise ValueError(
                "protocol physics time step does not match HumanoidBench"
            )
        self._joint_ids = tuple(
            int(row[0]) for row in self._world.model.actuator_trnid
        )
        self._token_to_twitch: dict[
            str, tuple[int, float] | None
        ] = {"humanoid_actuator_000": None}
        for ordinal in range(len(self._joint_ids)):
            for direction_ordinal, direction in enumerate((1.0, -1.0)):
                token_ordinal = 1 + ordinal * 2 + direction_ordinal
                self._token_to_twitch[
                    f"humanoid_actuator_{token_ordinal:03d}"
                ] = (ordinal, direction)
        self._support_body_ids: tuple[int, ...] = ()
        self._step_index = 0
        self._action_index = 0
        self._last_tokens: tuple[str, ...] = ()
        self._last_motor_reference_positions: tuple[float, ...] = ()
        self._last_motor_reference_kind = "current_sensed_configuration"
        self._last_motor_target_positions: tuple[float, ...] = ()
        self._last_motor_command_displacements: tuple[float, ...] = ()
        self._last_supplied_energy_joules = 0.0
        self._last_absorbed_energy_joules = 0.0
        self._last_peak_actuator_power_watts = 0.0
        self._last_peak_contact_force_newtons = 0.0
        self._last_contact_normal_impulse_newton_seconds = 0.0
        self._last_reward = 0.0
        self._last_reward_info: dict[str, float] = {}
        self._last_terminated = False
        self._renderer = None
        self._render_camera = None
        self.reset()

    def __enter__(self) -> "HumanoidBenchWorld":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def close(self) -> None:
        if self._renderer is not None:
            self._renderer.close()
            self._renderer = None
        self._render_camera = None
        self._env.close()

    def reset(self) -> dict[str, Any]:
        self._env.reset(seed=self.seed)
        self._sensor.reset()
        self._mujoco.mj_forward(self._world.model, self._world.data)
        self._support_body_ids = self._discover_support_bodies()
        if len(self._support_body_ids) != 2:
            raise RuntimeError(
                "expected two load-bearing HumanoidBench support bodies, "
                f"found {len(self._support_body_ids)}"
            )
        self._step_index = 0
        self._action_index = 0
        self._last_tokens = ()
        self._last_motor_reference_positions = ()
        self._last_motor_reference_kind = "current_sensed_configuration"
        self._last_motor_target_positions = ()
        self._last_motor_command_displacements = ()
        self._last_supplied_energy_joules = 0.0
        self._last_absorbed_energy_joules = 0.0
        self._last_peak_actuator_power_watts = 0.0
        self._last_peak_contact_force_newtons = 0.0
        self._last_contact_normal_impulse_newton_seconds = 0.0
        self._last_reward = 0.0
        self._last_reward_info = {}
        self._last_terminated = False
        return self.observe()

    def actuator_options(self) -> tuple[dict[str, Any], ...]:
        return tuple(
            {
                "token": token,
                "vector": twitch,
                "actuator_group": (
                    float(twitch[0]) if twitch is not None else -1.0
                ),
                "tonic_default": float(twitch is None),
            }
            for token, twitch in self._token_to_twitch.items()
        )

    def body_shape_signature(self) -> tuple[tuple[Any, ...], ...]:
        """Expose the same name-free integer morphology relations as Bullet."""
        model = self._world.model
        relations: list[tuple[Any, ...]] = [
            (
                "body",
                int(model.nbody),
                int(len(self._joint_ids)),
                int(len(self._support_body_ids)),
            )
        ]
        for body_id in range(1, int(model.nbody)):
            relations.append((
                "link",
                int(body_id),
                int(model.body_parentid[body_id]),
            ))
        for ordinal, joint_id in enumerate(self._joint_ids):
            body_id = int(model.jnt_bodyid[joint_id])
            axis = tuple(float(value) for value in model.jnt_axis[joint_id])
            axis_ratios = tuple(
                integer
                for value in axis
                for integer in value.as_integer_ratio()
            )
            relations.append((
                "actuator",
                int(ordinal),
                int(body_id),
                *axis_ratios,
            ))
        for support_ordinal, body_id in enumerate(self._support_body_ids):
            relations.append((
                "support",
                int(support_ordinal),
                int(body_id),
            ))
        return tuple(relations)

    def step(
        self,
        tokens: str | Iterable[str],
        *,
        frames: int | None = None,
        weights: dict[str, float] | None = None,
        reference_positions: Iterable[float] | None = None,
    ) -> dict[str, Any]:
        """Transduce one graph-selected bundle around a situated reference."""
        selected = (tokens,) if isinstance(tokens, str) else tuple(tokens)
        if not selected:
            raise ValueError("humanoid actuator bundle must not be empty")
        selected = tuple(dict.fromkeys(selected))
        weights = {} if weights is None else dict(weights)
        if reference_positions is None:
            references = np.array([
                self._world.data.qpos[
                    int(self._world.model.jnt_qposadr[joint_id])
                ]
                for joint_id in self._joint_ids
            ], dtype=np.float64)
            reference_kind = "current_sensed_configuration"
        else:
            references = np.asarray(
                tuple(float(value) for value in reference_positions),
                dtype=np.float64,
            )
            if references.shape != (len(self._joint_ids),):
                raise ValueError(
                    "motor reference must contain one position per joint"
                )
            if not np.all(np.isfinite(references)):
                raise ValueError("motor reference positions must be finite")
            reference_kind = "graph_situated_fixation"
        targets = references.copy()
        occupied: set[int] = set()
        for token in selected:
            try:
                twitch = self._token_to_twitch[token]
            except (KeyError, TypeError) as exc:
                raise ValueError(
                    f"unknown humanoid actuator token: {token!r}"
                ) from exc
            if twitch is None:
                if len(selected) != 1:
                    raise ValueError(
                        "tonic command cannot be combined with joint twitches"
                    )
                continue
            ordinal, direction = twitch
            if ordinal in occupied:
                raise ValueError(
                    "humanoid actuator bundle contains conflicting joint "
                    f"group {ordinal}"
                )
            occupied.add(ordinal)
            weight = float(weights.get(token, 1.0))
            if not math.isfinite(weight):
                raise ValueError("motor weights must be finite")
            if weight == 0.0:
                continue
            targets[ordinal] += (
                direction * weight
                * self.configuration.joint_twitch_radians
            )
        targets = np.clip(
            targets,
            self._world.action_low,
            self._world.action_high,
        )
        hold_frames = (
            self.configuration.action_frames if frames is None else frames
        )
        self._validate_frames(hold_frames)
        self._last_motor_reference_positions = tuple(
            float(value) for value in references
        )
        self._last_motor_reference_kind = reference_kind
        self._last_motor_target_positions = tuple(
            float(value) for value in targets
        )
        self._last_motor_command_displacements = tuple(
            float(target - reference)
            for reference, target in zip(references, targets)
        )
        self._advance_control(targets, hold_frames)
        self._action_index += 1
        self._last_tokens = selected
        self._read_benchmark_assessment()
        return self.observe()

    def hold_tonic(self, frames: int) -> dict[str, Any]:
        return self.step("humanoid_actuator_000", frames=frames)

    def apply_force_pulse(
        self,
        force_xyz: Iterable[float],
        *,
        frames: int = 1,
    ) -> dict[str, Any]:
        force = tuple(float(value) for value in force_xyz)
        if len(force) != 3 or not all(math.isfinite(v) for v in force):
            raise ValueError("force_xyz must contain three finite values")
        self._validate_frames(frames)
        root_body = int(self._world.model.jnt_bodyid[0])
        tonic = np.array([
            self._world.data.qpos[
                int(self._world.model.jnt_qposadr[joint_id])
            ]
            for joint_id in self._joint_ids
        ], dtype=np.float64)
        tonic = np.clip(
            tonic,
            self._world.action_low,
            self._world.action_high,
        )
        for _ in range(frames):
            self._world.data.xfrc_applied[root_body, :3] = force
            self._world.do_simulation(tonic, 1)
            self._world.data.xfrc_applied[root_body, :3] = 0.0
        self._step_index += frames
        self._read_benchmark_assessment()
        return self.observe()

    def observe(self) -> dict[str, Any]:
        data = self._world.data
        model = self._world.model
        qpos = data.qpos
        qvel = data.qvel
        support_force = {
            body_id: 0.0 for body_id in self._support_body_ids
        }
        # Instantaneous total: the sum of normal-force magnitudes over every
        # contact in the scene at THIS snapshot. This model contains a single
        # robot (body_id 0 is the world), so every reported contact involves
        # this body. Not a peak over the action, and not thresholded.
        total_contact_force = 0.0
        for contact_index in range(data.ncon):
            contact = data.contact[contact_index]
            body_ids = (
                int(model.geom_bodyid[contact.geom1]),
                int(model.geom_bodyid[contact.geom2]),
            )
            force = np.zeros(6, dtype=np.float64)
            self._mujoco.mj_contactForce(
                model,
                data,
                contact_index,
                force,
            )
            total_contact_force += max(0.0, float(force[0]))
            for body_id in body_ids:
                if body_id in support_force:
                    support_force[body_id] += max(0.0, float(force[0]))
        joints = []
        for ordinal, joint_id in enumerate(self._joint_ids):
            qpos_address = int(model.jnt_qposadr[joint_id])
            dof_address = int(model.jnt_dofadr[joint_id])
            joints.append({
                "ordinal": ordinal,
                "index": joint_id,
                "position": float(qpos[qpos_address]),
                "velocity": float(qvel[dof_address]),
                "reaction_forces": (),
                "applied_torque": float(data.actuator_force[ordinal]),
            })
        qw, qx, qy, qz = (float(value) for value in qpos[3:7])
        sensor_sample = self._sensor.sample(
            position=qpos[:3],
            orientation_xyzw=(qx, qy, qz, qw),
            linear_velocity=qvel[:3],
            angular_velocity=qvel[3:6],
            contact_count=float(data.ncon),
            sample_id=self._step_index,
        )
        return {
            "simulator": "humanoid_bench_mujoco",
            "asset": self.environment_id,
            "benchmark_revision": self._benchmark_revision(),
            "seed": self.seed,
            "body_mass": float(self._mujoco.mj_getTotalmass(model)),
            "gravity_acceleration": abs(float(model.opt.gravity[2])),
            "step_index": self._step_index,
            "sim_time": self._step_index * float(model.opt.timestep),
            "control_integration_frames": int(self._world.frame_skip),
            "base_position": tuple(float(value) for value in qpos[:3]),
            "base_orientation_xyzw": (qx, qy, qz, qw),
            "base_linear_velocity": tuple(
                float(value) for value in qvel[:3]
            ),
            "base_angular_velocity": tuple(
                float(value) for value in qvel[3:6]
            ),
            "joints": tuple(joints),
            "contacts": (),
            "support_contact_forces": tuple(
                {
                    "ordinal": ordinal,
                    "link_index": body_id,
                    "normal_force": support_force[body_id],
                    "world_position": tuple(
                        float(value) for value in data.xpos[body_id]
                    ),
                }
                for ordinal, body_id in enumerate(self._support_body_ids)
            ),
            "last_actuator_token": (
                self._last_tokens[0] if len(self._last_tokens) == 1 else None
            ),
            "last_actuator_tokens": self._last_tokens,
            "supplied_energy_joules": self._last_supplied_energy_joules,
            "absorbed_energy_joules": self._last_absorbed_energy_joules,
            "peak_actuator_power_watts": (
                self._last_peak_actuator_power_watts
            ),
            "peak_contact_force_newtons": (
                self._last_peak_contact_force_newtons
            ),
            "contact_force_newtons": float(total_contact_force),
            "contact_normal_impulse_newton_seconds": (
                self._last_contact_normal_impulse_newton_seconds
            ),
            "motor_reference_positions": self._last_motor_reference_positions,
            "motor_reference_kind": self._last_motor_reference_kind,
            "motor_target_positions": self._last_motor_target_positions,
            "motor_command_displacements": (
                self._last_motor_command_displacements
            ),
            "motor_configuration_shape": tuple(
                round(
                    float(joint["position"])
                    / self.configuration.joint_twitch_radians
                )
                for joint in joints
            ),
            "actuator_activation_seconds": self.configuration.time_step,
            "benchmark_reward": self._last_reward,
            "benchmark_reward_info": dict(self._last_reward_info),
            "benchmark_terminated": self._last_terminated,
            **sensor_sample,
        }

    def _advance_control(self, control: np.ndarray, frames: int) -> None:
        """Advance raw MuJoCo control while measuring mechanical receipts."""
        supplied = 0.0
        absorbed = 0.0
        peak_power = 0.0
        peak_contact_force = 0.0
        contact_normal_impulse = 0.0
        time_step = self.configuration.time_step
        for _ in range(frames):
            self._world.do_simulation(control, 1)
            signed_power = tuple(
                float(self._world.data.qvel[
                    int(self._world.model.jnt_dofadr[joint_id])
                ]) * float(self._world.data.actuator_force[ordinal])
                for ordinal, joint_id in enumerate(self._joint_ids)
            )
            supplied_power = sum(max(0.0, value) for value in signed_power)
            absorbed_power = sum(max(0.0, -value) for value in signed_power)
            supplied += supplied_power * time_step
            absorbed += absorbed_power * time_step
            peak_power = max(peak_power, supplied_power + absorbed_power)
            frame_contact_force = 0.0
            for contact_index in range(self._world.data.ncon):
                force = np.zeros(6, dtype=np.float64)
                self._mujoco.mj_contactForce(
                    self._world.model,
                    self._world.data,
                    contact_index,
                    force,
                )
                frame_contact_force += max(0.0, float(force[0]))
            peak_contact_force = max(
                peak_contact_force,
                frame_contact_force,
            )
            contact_normal_impulse += frame_contact_force * time_step
        self._last_supplied_energy_joules = supplied
        self._last_absorbed_energy_joules = absorbed
        self._last_peak_actuator_power_watts = peak_power
        self._last_peak_contact_force_newtons = peak_contact_force
        self._last_contact_normal_impulse_newton_seconds = (
            contact_normal_impulse
        )
        self._step_index += frames

    def _render_rgb_array(
        self,
        *,
        width: int = 960,
        height: int = 540,
    ) -> Any:
        """Render through MuJoCo without the benchmark's policy wrappers."""
        if width < 1 or height < 1:
            raise ValueError("render dimensions must be positive")
        # The official H1 XML declares a 256-pixel offscreen framebuffer.
        # Presentation tooling scales this image after rendering.
        render_width = min(width, 256)
        render_height = min(height, max(1, round(
            render_width * height / width
        )))
        requested_size = (render_width, render_height)
        if self._renderer is not None and (
            self._renderer.width,
            self._renderer.height,
        ) != requested_size:
            self._renderer.close()
            self._renderer = None
        if self._renderer is None:
            self._renderer = self._mujoco.Renderer(
                self._world.model,
                height=render_height,
                width=render_width,
            )
            self._render_camera = self._mujoco.MjvCamera()
            self._mujoco.mjv_defaultCamera(self._render_camera)
            self._render_camera.type = self._mujoco.mjtCamera.mjCAMERA_FREE
            self._render_camera.distance = 3.4
            self._render_camera.azimuth = 135.0
            self._render_camera.elevation = -10.0
        base_position = self._world.data.qpos[:3]
        self._render_camera.lookat[:] = (
            float(base_position[0]),
            float(base_position[1]),
            max(0.8, float(base_position[2])),
        )
        self._renderer.update_scene(
            self._world.data,
            camera=self._render_camera,
        )
        return self._renderer.render()[..., :3]

    def _discover_support_bodies(self) -> tuple[int, ...]:
        model = self._world.model
        data = self._world.data
        loads: dict[int, float] = {}
        for contact_index in range(data.ncon):
            contact = data.contact[contact_index]
            force = np.zeros(6, dtype=np.float64)
            self._mujoco.mj_contactForce(
                model,
                data,
                contact_index,
                force,
            )
            for geom_id in (contact.geom1, contact.geom2):
                body_id = int(model.geom_bodyid[geom_id])
                if body_id != 0:
                    loads[body_id] = (
                        loads.get(body_id, 0.0)
                        + max(0.0, float(force[0]))
                    )
        return tuple(sorted(
            body_id for body_id, load in loads.items() if load > 0.0
        ))

    def _read_benchmark_assessment(self) -> None:
        reward, info = self._world.task.get_reward()
        terminated, terminated_info = self._world.task.get_terminated()
        self._last_reward = float(reward)
        self._last_reward_info = {
            key: float(value)
            for key, value in {**info, **terminated_info}.items()
        }
        self._last_terminated = bool(terminated)

    def _benchmark_revision(self) -> str:
        head = self.simulator_root / ".git" / "HEAD"
        if not head.is_file():
            return "unknown"
        value = head.read_text(encoding="utf-8").strip()
        if value.startswith("ref: "):
            ref = self.simulator_root / ".git" / value[5:]
            if ref.is_file():
                return ref.read_text(encoding="utf-8").strip()
        return value

    @staticmethod
    def _validate_frames(frames: int) -> None:
        if isinstance(frames, bool) or not isinstance(frames, int) or frames < 1:
            raise ValueError("frames must be a positive integer")


__all__ = ["HumanoidBenchWorld"]
