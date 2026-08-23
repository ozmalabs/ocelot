"""Mechanical PyBullet boundary for an articulated humanoid body.

The adapter exposes an opaque tonic command plus one positive and negative
joint-position twitch for every revolute joint discovered in the body asset.
It can enact a graph-authored bundle of non-conflicting twitches for a
graph-authored number of physics frames. It owns only simulator wiring, tonic
joint servos, force-pulse injection, and raw sensing. Action composition,
timing, consequence learning, balance control, and fall judgment remain
graph-native.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
from typing import Any, Iterable
from xml.etree import ElementTree as _ElementTree

import numpy as _np

from domains.sensorimotor_transducer import (
    SensorimotorSensorConfiguration,
    SensorimotorTransducer,
)

try:
    import pybullet as _bullet
    import pybullet_data as _bullet_data
except ModuleNotFoundError:
    _bullet = None
    _bullet_data = None


HUMANOID_ASSET = "mjcf/humanoid.xml"


def _floats(values: Iterable[float]) -> tuple[float, ...]:
    return tuple(float(value) for value in values)


def _triple(values: Iterable[float], *, field: str) -> tuple[float, float, float]:
    result = _floats(values)
    if len(result) != 3 or not all(math.isfinite(value) for value in result):
        raise ValueError(f"{field} must contain three finite values")
    return result


@dataclass(frozen=True)
class HumanoidBodyConfiguration:
    """Declared mechanical parameters for the development body."""

    time_step: float
    gravity_acceleration: float
    action_frames: int
    settling_frames: int
    joint_twitch_radians: float
    maximum_joint_force: float
    position_gain: float
    velocity_gain: float
    initial_base_quarter_turns: tuple[int, int, int] = (0, 0, 0)
    asset: str = HUMANOID_ASSET

    def __post_init__(self) -> None:
        for field in (
            "time_step",
            "gravity_acceleration",
            "joint_twitch_radians",
            "maximum_joint_force",
            "position_gain",
            "velocity_gain",
        ):
            value = getattr(self, field)
            if not math.isfinite(value) or value <= 0.0:
                raise ValueError(f"{field} must be finite and positive")
        for field in ("action_frames", "settling_frames"):
            value = getattr(self, field)
            if (
                isinstance(value, bool)
                or not isinstance(value, int)
                or value < 1
            ):
                raise ValueError(f"{field} must be a positive integer")
        if (
            len(self.initial_base_quarter_turns) != 3
            or any(
                isinstance(value, bool) or not isinstance(value, int)
                for value in self.initial_base_quarter_turns
            )
        ):
            raise ValueError(
                "initial_base_quarter_turns must contain three integers"
            )
        if not isinstance(self.asset, str) or not self.asset.endswith(".xml"):
            raise ValueError("asset must name a PyBullet MJCF XML resource")


class PyBulletHumanoidWorld:
    """Deterministic full-body humanoid with opaque joint-twitch authority."""

    def __init__(
        self,
        configuration: HumanoidBodyConfiguration,
        *,
        seed: int = 0,
        sensor_configuration: SensorimotorSensorConfiguration | None = None,
    ) -> None:
        if _bullet is None or _bullet_data is None:
            raise RuntimeError(
                "PyBullet is required; install requirements-robot.txt"
            )
        self.configuration = configuration
        self.seed = int(seed)
        self._sensor = SensorimotorTransducer(
            sample_period_seconds=configuration.time_step,
            configuration=sensor_configuration,
            seed=self.seed,
        )
        self._client = _bullet.connect(_bullet.DIRECT)
        if self._client < 0:
            raise RuntimeError("PyBullet DIRECT connection failed")
        self._body: int | None = None
        self._body_mass = 0.0
        self._body_length_scale = 0.0
        self._ground_bodies: tuple[int, ...] = ()
        self._joint_indices: tuple[int, ...] = ()
        self._joint_force_limits: tuple[float, ...] = ()
        self._support_link_indices: tuple[int, ...] = ()
        self._last_motor_reference_positions: tuple[float, ...] = ()
        self._last_motor_reference_kind = "current_sensed_configuration"
        self._last_motor_target_positions: tuple[float, ...] = ()
        self._last_motor_command_displacements: tuple[float, ...] = ()
        self._token_to_twitch: dict[str, tuple[int, float] | None] = {}
        self._step_index = 0
        self._sensor.reset()
        self._action_index = 0
        self._last_tokens: tuple[str, ...] = ()
        self._last_supplied_energy_joules = 0.0
        self._last_absorbed_energy_joules = 0.0
        self._last_peak_actuator_power_watts = 0.0
        self._last_peak_contact_force_newtons = 0.0
        self._last_contact_normal_impulse_newton_seconds = 0.0
        self._last_caregiver_support_applied = False
        self._last_caregiver_support_scale = 0.0
        self._last_caregiver_support_impulse_newton_seconds = 0.0
        self._last_caregiver_support_force_world = (0.0, 0.0, 0.0)
        self._last_caregiver_support_torque_world = (0.0, 0.0, 0.0)
        # PER-FRAME VERTICAL TRACE. `_advance` appends the base link's height
        # once per integration frame; `reset` clears it. Pure measurement of a
        # quantity the simulator already holds — there is no policy here and
        # nothing reads it but `observe`.
        self._base_height_trace: list[float] = []
        self.reset()

    def __enter__(self) -> "PyBulletHumanoidWorld":
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()

    def close(self) -> None:
        """Release the private Bullet client."""
        if self._client >= 0:
            if _bullet.isConnected(self._client):
                _bullet.disconnect(self._client)
            self._client = -1
        self._body = None
        self._body_mass = 0.0
        self._body_length_scale = 0.0
        self._ground_bodies = ()
        self._joint_indices = ()
        self._joint_force_limits = ()
        self._support_link_indices = ()
        self._last_motor_reference_positions = ()
        self._last_motor_reference_kind = "current_sensed_configuration"
        self._last_motor_target_positions = ()
        self._last_motor_command_displacements = ()
        self._last_caregiver_support_applied = False
        self._last_caregiver_support_scale = 0.0
        self._last_caregiver_support_impulse_newton_seconds = 0.0
        self._last_caregiver_support_force_world = (0.0, 0.0, 0.0)
        self._last_caregiver_support_torque_world = (0.0, 0.0, 0.0)
        self._token_to_twitch = {}

    def reset(
        self,
        *,
        initial_base_quarter_turns: tuple[int, int, int] | None = None,
    ) -> dict[str, Any]:
        """Recreate and settle the humanoid in its sensed load configuration."""
        self._require_open()
        self._sensor.reset()
        configuration = self.configuration
        _bullet.resetSimulation(physicsClientId=self._client)
        _bullet.setAdditionalSearchPath(
            _bullet_data.getDataPath(),
            physicsClientId=self._client,
        )
        _bullet.setPhysicsEngineParameter(
            fixedTimeStep=configuration.time_step,
            numSolverIterations=50,
            deterministicOverlappingPairs=1,
            physicsClientId=self._client,
        )
        _bullet.setTimeStep(
            configuration.time_step,
            physicsClientId=self._client,
        )
        _bullet.setGravity(
            0.0,
            0.0,
            -configuration.gravity_acceleration,
            physicsClientId=self._client,
        )
        bodies = tuple(
            int(body)
            for body in _bullet.loadMJCF(
                configuration.asset,
                physicsClientId=self._client,
            )
        )
        if not bodies:
            raise RuntimeError("humanoid MJCF produced no bodies")
        self._body = bodies[-1]
        self._ground_bodies = bodies[:-1]
        if not self._ground_bodies:
            ground = int(_bullet.loadURDF(
                "plane.urdf",
                physicsClientId=self._client,
            ))
            self._ground_bodies = (ground,)
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
        self._joint_indices = tuple(
            joint_index
            for joint_index in range(
                _bullet.getNumJoints(
                    self._body,
                    physicsClientId=self._client,
                )
            )
            if _bullet.getJointInfo(
                self._body,
                joint_index,
                physicsClientId=self._client,
            )[2]
            == _bullet.JOINT_REVOLUTE
        )
        self._joint_force_limits = self._compute_joint_force_limits()
        path_lengths: dict[int, float] = {-1: 0.0}
        parent_indices: dict[int, int] = {}
        for link_index in range(_bullet.getNumJoints(
            self._body,
            physicsClientId=self._client,
        )):
            joint_info = _bullet.getJointInfo(
                self._body,
                link_index,
                physicsClientId=self._client,
            )
            parent_index = int(joint_info[16])
            parent_indices[link_index] = parent_index
            offset = _np.asarray(joint_info[14], dtype=float)
            path_lengths[link_index] = (
                path_lengths.get(parent_index, 0.0)
                + float(_np.linalg.norm(offset))
            )
        self._body_length_scale = max(path_lengths.values())
        if not self._body_length_scale > 0.0:
            raise RuntimeError("humanoid body has no measurable link extent")
        parents = set(parent_indices.values())
        terminal_links = [
            link_index for link_index in parent_indices
            if link_index not in parents
        ]
        distal_links = sorted(
            terminal_links,
            key=lambda link_index: (-path_lengths[link_index], link_index),
        )
        if len(distal_links) < 2:
            raise RuntimeError("humanoid body has fewer than two distal links")
        self._support_link_indices = tuple(sorted(distal_links[:2]))
        self._last_motor_reference_positions = ()
        self._last_motor_reference_kind = "current_sensed_configuration"
        self._last_motor_target_positions = ()
        self._last_motor_command_displacements = ()
        self._token_to_twitch = {"humanoid_actuator_000": None}
        for joint_ordinal in range(len(self._joint_indices)):
            for direction_ordinal, direction in enumerate((1.0, -1.0)):
                token_ordinal = 1 + joint_ordinal * 2 + direction_ordinal
                self._token_to_twitch[
                    f"humanoid_actuator_{token_ordinal:03d}"
                ] = (joint_ordinal, direction)
        self._step_index = 0
        self._action_index = 0
        self._last_tokens = ()
        self._last_supplied_energy_joules = 0.0
        self._last_absorbed_energy_joules = 0.0
        self._last_peak_actuator_power_watts = 0.0
        self._last_peak_contact_force_newtons = 0.0
        self._last_contact_normal_impulse_newton_seconds = 0.0
        self._last_caregiver_support_applied = False
        self._last_caregiver_support_scale = 0.0
        self._last_caregiver_support_impulse_newton_seconds = 0.0
        self._last_caregiver_support_force_world = (0.0, 0.0, 0.0)
        self._last_caregiver_support_torque_world = (0.0, 0.0, 0.0)
        self._write_twitches(())
        self._apply_declared_initial_fixture(initial_base_quarter_turns)
        # A reset opens a new trial, so its per-frame vertical trace starts
        # empty. The settling advance below is the body's own drop onto the
        # floor and is part of that trace: it is what the body DID, measured,
        # not a scenario anything chose.
        self._base_height_trace = []
        self._advance(configuration.settling_frames, measure_energy=False)
        self._last_supplied_energy_joules = 0.0
        self._last_absorbed_energy_joules = 0.0
        self._last_peak_actuator_power_watts = 0.0
        self._last_peak_contact_force_newtons = 0.0
        self._last_contact_normal_impulse_newton_seconds = 0.0
        _bullet.resetBaseVelocity(
            self._body,
            linearVelocity=(0.0, 0.0, 0.0),
            angularVelocity=(0.0, 0.0, 0.0),
            physicsClientId=self._client,
        )
        # A reset is a quiet experimental fixture, not a return to a hidden
        # canonical posture.  Preserve every joint's situated angle after
        # settling while arresting residual simulator motion, just as the
        # base velocity above is arrested.  Calibration can therefore test
        # effectors relative to the body configuration it actually occupies.
        for joint_index in self._joint_indices:
            joint_state = _bullet.getJointState(
                self._body,
                joint_index,
                physicsClientId=self._client,
            )
            _bullet.resetJointState(
                self._body,
                joint_index,
                targetValue=float(joint_state[0]),
                targetVelocity=0.0,
                physicsClientId=self._client,
            )
        _bullet.performCollisionDetection(physicsClientId=self._client)
        self._step_index = 0
        return self.observe()

    def _apply_declared_initial_fixture(
        self,
        quarter_turns: tuple[int, int, int] | None = None,
    ) -> None:
        """Place the held body in a declared orientation without naming a pose."""
        assert self._body is not None
        if quarter_turns is None:
            quarter_turns = self.configuration.initial_base_quarter_turns
        if (
            len(quarter_turns) != 3
            or any(isinstance(value, bool) or not isinstance(value, int)
                   for value in quarter_turns)
        ):
            raise ValueError("quarter-turn fixture must contain three integers")
        if quarter_turns == (0, 0, 0):
            return
        position, _ = _bullet.getBasePositionAndOrientation(
            self._body,
            physicsClientId=self._client,
        )
        orientation = _bullet.getQuaternionFromEuler(tuple(
            value * math.pi / 2 for value in quarter_turns
        ))
        _bullet.resetBasePositionAndOrientation(
            self._body,
            position,
            orientation,
            physicsClientId=self._client,
        )
        _bullet.performCollisionDetection(physicsClientId=self._client)
        minimum_z = min(
            float(_bullet.getAABB(
                self._body,
                link_index,
                physicsClientId=self._client,
            )[0][2])
            for link_index in range(-1, _bullet.getNumJoints(
                self._body,
                physicsClientId=self._client,
            ))
        )
        clearance = (
            self.configuration.gravity_acceleration
            * self.configuration.time_step
            * self.configuration.time_step
        )
        _bullet.resetBasePositionAndOrientation(
            self._body,
            (
                float(position[0]),
                float(position[1]),
                float(position[2]) - minimum_z + clearance,
            ),
            orientation,
            physicsClientId=self._client,
        )
        _bullet.resetBaseVelocity(
            self._body,
            linearVelocity=(0.0, 0.0, 0.0),
            angularVelocity=(0.0, 0.0, 0.0),
            physicsClientId=self._client,
        )

    def _travel_bounds(self, joint_ordinal: int) -> tuple[float, float, float]:
        """Return `(lower, upper, position)` in radians for one joint ordinal.

        Pure sensor read. `getJointInfo[8]`/`[9]` are the asset's own declared
        travel; `getJointState[0]` is where the joint is now.
        """
        assert self._body is not None
        joint_index = self._joint_indices[joint_ordinal]
        info = _bullet.getJointInfo(
            self._body,
            joint_index,
            physicsClientId=self._client,
        )
        position = float(_bullet.getJointState(
            self._body,
            joint_index,
            physicsClientId=self._client,
        )[0])
        return float(info[8]), float(info[9]), position

    def _declared_actuator_gears(self) -> dict[int, float]:
        """Return `{joint_ordinal: declared gear}` read from the body ASSET.

        THE LAST UNIFORM AUTHORITY, AND THE ASSET NEVER AGREED WITH IT.
        `declared_joint_force_units` was one config constant across all 43
        affordance tokens, so the graph could distinguish demand but never
        differential authority BETWEEN joints -- and with the declared authority
        equal everywhere, `elb_carrier_path_authority` reduced to `min(x, x)`
        and the settle could not tell any two members of the body apart.

        `getJointInfo[10]` (maximum force) is 0.0 on every joint here because
        the MJCF declares no per-joint limit, which is what made this look
        unfixable from the asset. It is not: MuJoCo declares actuator authority
        in the `<actuator>` block instead, as a per-motor `gear`, and this body
        spans 100 / 200 / 400 / 600 across its 21 joints. PyBullet's loader does
        not surface it, so the number was sitting in the file the world already
        loads -- the same shape of boundary discard as `twitch[1]`,
        `maximum_joint_force` and `parent_for_joint` before it.

        Joined on the JOINT NAME, which is the only key both sides share. The
        name never crosses into the graph: it is used here and discarded, and
        what is published is an ordinal and a magnitude.
        """
        assert self._body is not None
        path = Path(_bullet_data.getDataPath()) / self.configuration.asset
        try:
            root = _ElementTree.parse(path).getroot()
        except (OSError, _ElementTree.ParseError):
            return {}
        gear_for_name: dict[str, float] = {}
        for motor in root.iter("motor"):
            joint_name = motor.get("joint")
            gear = motor.get("gear")
            if not joint_name or gear is None:
                continue
            try:
                # MuJoCo's gear may be a vector; the scalar case is the first
                # component and the only one this body uses.
                gear_for_name[joint_name] = abs(float(gear.split()[0]))
            except (TypeError, ValueError):
                continue
        if not gear_for_name:
            return {}
        gears: dict[int, float] = {}
        for ordinal, joint_index in enumerate(self._joint_indices):
            name = _bullet.getJointInfo(
                self._body,
                joint_index,
                physicsClientId=self._client,
            )[1]
            if isinstance(name, bytes):
                name = name.decode("utf-8", "replace")
            if name in gear_for_name:
                gears[ordinal] = gear_for_name[name]
        return gears

    def _compute_joint_force_limits(self) -> tuple[float, ...]:
        """Per-joint force limits in the asset's OWN declared ratio.

        `configuration.maximum_joint_force` stops being a flat value across
        every joint and becomes the anchor for the WEAKEST one, with the rest
        scaled by the asset's gear:

            force_j = maximum_joint_force x gear_j / min(gear)

        So a body configured at 100 keeps 100 on its weakest actuators and
        gains the asset's own 2x / 4x / 6x elsewhere, rather than flying every
        joint as though it were the same motor.

        AND THE BODY MUST ACTUALLY FLY BY IT. Publishing the gear while
        continuing to cap every joint identically would be strictly worse than
        the uniform constant it replaces: the graph would reason about
        differential authority THE SIMULATED BODY DOES NOT HAVE. PyBullet's MJCF
        loader ignores the `<actuator>` block entirely -- which is exactly why
        `getJointInfo[10]` reads 0.0 -- so nothing applies this ratio unless
        `_write_twitches` does.

        Falls back to the flat configured value when the asset declares no
        gears, so a body without an `<actuator>` block behaves exactly as
        before.
        """
        count = len(self._joint_indices)
        flat = tuple([float(self.configuration.maximum_joint_force)] * count)
        gears = self._declared_actuator_gears()
        if len(gears) != count or not gears:
            return flat
        smallest = min(gears.values())
        if not smallest > 0.0:
            return flat
        return tuple(
            float(self.configuration.maximum_joint_force)
            * gears[ordinal] / smallest
            for ordinal in range(count)
        )

    def _applied_joint_torque(self, joint_ordinal: int) -> float:
        """Return the motor torque this joint applied on the last step.

        `getJointState[3]`. Pure sensor read. The 6-axis `reaction_forces`
        channel next to it stays identically zero on this body because joint
        force-torque sensors are never enabled, so this is the ONLY load
        channel the asset offers.
        """
        assert self._body is not None
        return float(_bullet.getJointState(
            self._body,
            self._joint_indices[joint_ordinal],
            physicsClientId=self._client,
        )[3])

    def actuator_options(self) -> tuple[dict[str, Any], ...]:
        """Return stable opaque tokens, host-only joint wiring, and the two
        DECLARED authority magnitudes this option is flown by.

        `twitch[1]` -- the per-action displacement this token commands -- was
        computed here and discarded, so the graph could read
        `specified_maximum_position_change_per_action` (7,196 rule reads) and
        `maximum_joint_force` from nothing at all. A criterion that divides by
        an authority nobody publishes is unsatisfiable, and through the
        `Plus[Attr, Lit 0]` idiom it reads as a division against zero rather
        than as a missing declaration.

        Both are DECLARED, not measured -- they are configuration this body
        flies by, and the F-16 pattern requires that provenance travel with
        them so a declared bound is never confusable with an observed one.
        They stay opaque: a magnitude and a force limit, with no claim about
        what the actuator does.

        THE TRAVEL THE BODY ALREADY OBEYS. `_write_twitches` has clamped every
        command to this joint's declared `lower`/`upper` since it was written,
        so a twitch commanded at a stop delivers less displacement than it
        declares -- the declared authority is ALREADY a lie at the stop, and the
        graph has never been told. Two more boundary values of exactly the shape
        of the three above:

          * `declared_travel_span` -- `upper - lower`, the asset's own
            configuration, DECLARED.
          * `command_direction_travel_headroom` -- how much travel remains in
            THIS token's own command direction, MEASURED (it moves as the body
            moves).

        POLARITY STAYS OPAQUE. `_directed_local_effector_relations` leaves
        command polarity to graph-side consequence-driven synthesis, and this
        keeps that: the graph learns how far this token can still go, never
        which way "further" points. Publish the quantity, not the label.

        WHICH DIRECTION IS LOADED. Headroom alone does not say whether the
        travel it names is the travel the load is spending. A joint resting on
        its stop is braced against a load pushing INTO that stop and completely
        compliant to one pushing away from it -- the same posture, opposite
        readings -- so `command_direction_load` publishes the component of the
        load along THIS token's command direction, floored at zero. A token
        reporting a positive load is the one whose headroom the load is
        consuming; a token reporting zero is not the one bearing it.

        MEASURED, THEN NEGATED. The datum is the actuator's own applied torque.
        Under a held position the external load is its negation, so the load
        pushes the joint the way the motor is resisting. That negation is an
        INFERENCE (it is exact only quasi-statically), and the transducer flags
        it as one -- a measured torque must not launder itself into a measured
        load.

        Polarity stays opaque here too: the graph learns that this token is
        bearing load and how much, never which way the load points.

        The tonic option gets NONE of them. It names no joint and commands no
        displacement, so its headroom is undefined -- and a headroom of zero
        means "at the stop", the most consequential possible misreading here.
        Absent, not zero.
        """
        options: list[dict[str, Any]] = []
        for token, twitch in self._token_to_twitch.items():
            option: dict[str, Any] = {
                "token": token,
                "vector": twitch,
                "actuator_group": (
                    float(twitch[0]) if twitch is not None else -1.0
                ),
                "tonic_default": float(twitch is None),
                "declared_position_change": (
                    abs(float(twitch[1])) if twitch is not None else 0.0
                ),
                # THE PER-ACTUATOR limit this token is flown by -- the
                # asset's own gear ratio anchored at the configured value,
                # not one constant standing in for 43 different motors.
                "declared_joint_force": (
                    self._joint_force_limits[int(twitch[0])]
                    if twitch is not None
                    and int(twitch[0]) < len(self._joint_force_limits)
                    else float(self.configuration.maximum_joint_force)
                ),
                "declared_travel_span": None,
                "command_direction_travel_headroom": None,
                "command_direction_load": None,
            }
            if twitch is not None and self._body is not None:
                direction = 1.0 if float(twitch[1]) >= 0.0 else -1.0
                lower, upper, position = self._travel_bounds(int(twitch[0]))
                if lower <= upper:
                    option["declared_travel_span"] = upper - lower
                    option["command_direction_travel_headroom"] = max(
                        0.0,
                        (upper - position) if direction >= 0.0
                        else (position - lower),
                    )
                # The load is the negation of the actuator's own effort, then
                # projected onto this token's command direction and floored:
                # exactly one of a joint's two tokens can report a load.
                torque = self._applied_joint_torque(int(twitch[0]))
                option["command_direction_load"] = max(
                    0.0, -torque * direction)
            options.append(option)
        return tuple(options)

    def body_shape_signature(self) -> tuple[tuple[Any, ...], ...]:
        """Return a name-free integer relation system for body morphology.

        This is a mechanical sensor boundary, not a body classifier.  Joint
        names and the source asset never cross it.  The graph's existing
        ShapeDecode machinery decides whether the resulting relation system
        is a held body shape.
        """
        self._require_open()
        assert self._body is not None
        joint_count = _bullet.getNumJoints(
            self._body,
            physicsClientId=self._client,
        )
        relations: list[tuple[Any, ...]] = [
            (
                "body",
                int(joint_count),
                int(len(self._joint_indices)),
                int(len(self._support_link_indices)),
            )
        ]
        for joint_index in range(joint_count):
            info = _bullet.getJointInfo(
                self._body,
                joint_index,
                physicsClientId=self._client,
            )
            relations.append((
                "link",
                int(joint_index),
                int(info[16]),
                int(info[2]),
            ))
        for ordinal, joint_index in enumerate(self._joint_indices):
            info = _bullet.getJointInfo(
                self._body,
                joint_index,
                physicsClientId=self._client,
            )
            axis = tuple(float(value) for value in info[13])
            axis_ratios = tuple(
                integer
                for value in axis
                for integer in value.as_integer_ratio()
            )
            relations.append((
                "actuator",
                int(ordinal),
                int(joint_index),
                *axis_ratios,
            ))
        for support_ordinal, link_index in enumerate(
            self._support_link_indices
        ):
            relations.append((
                "support",
                int(support_ordinal),
                int(link_index),
            ))
        return tuple(relations)

    def body_capability_signature(self) -> tuple[tuple[Any, ...], ...]:
        """Return aggregate morphology motifs suitable for partial transfer.

        ``body_shape_signature`` intentionally identifies an exact mechanical
        body.  Developmental abilities need a second, coarser relation system:
        rolling or distributed support learned by one body may be a useful
        search prior for another body with overlapping articulation, branching
        and actuation motifs.  This boundary only counts name-free mechanical
        relations; ShapeDecode decides whether overlap is useful.
        """
        self._require_open()
        assert self._body is not None
        joint_count = _bullet.getNumJoints(
            self._body,
            physicsClientId=self._client,
        )
        parent_indices: dict[int, int] = {}
        child_counts = {-1: 0}
        depths = {-1: 0}
        joint_type_counts: dict[int, int] = {}
        axis_class_counts: dict[tuple[int, int, int], int] = {}
        for joint_index in range(joint_count):
            info = _bullet.getJointInfo(
                self._body,
                joint_index,
                physicsClientId=self._client,
            )
            parent_index = int(info[16])
            parent_indices[joint_index] = parent_index
            child_counts[parent_index] = child_counts.get(parent_index, 0) + 1
            child_counts.setdefault(joint_index, 0)
            depths[joint_index] = depths.get(parent_index, 0) + 1
            joint_type = int(info[2])
            joint_type_counts[joint_type] = (
                joint_type_counts.get(joint_type, 0) + 1
            )
            if joint_index in self._joint_indices:
                axis_class = tuple(
                    0 if abs(float(value)) < 0.5
                    else (1 if float(value) > 0.0 else -1)
                    for value in info[13]
                )
                axis_class_counts[axis_class] = (
                    axis_class_counts.get(axis_class, 0) + 1
                )
        terminal_count = sum(
            child_counts.get(joint_index, 0) == 0
            for joint_index in range(joint_count)
        )
        branch_histogram: dict[int, int] = {}
        for child_count in child_counts.values():
            branch_histogram[child_count] = (
                branch_histogram.get(child_count, 0) + 1
            )
        return (
            ("articulated_body", int(bool(self._joint_indices))),
            ("link_count", int(joint_count + 1)),
            ("actuator_count", int(len(self._joint_indices))),
            ("terminal_count", int(terminal_count)),
            ("maximum_chain_order", int(max(depths.values()))),
            (
                "distal_support_channel_count",
                int(len(self._support_link_indices)),
            ),
            *(
                ("branch_degree_count", int(degree), int(count))
                for degree, count in sorted(branch_histogram.items())
            ),
            *(
                ("joint_type_count", int(kind), int(count))
                for kind, count in sorted(joint_type_counts.items())
            ),
            *(
                ("actuator_axis_class_count", *axis, int(count))
                for axis, count in sorted(axis_class_counts.items())
            ),
        )

    def apply(self, token: str) -> dict[str, Any]:
        """Apply one externally selected opaque actuator token."""
        return self.step(token)

    def step(
        self,
        tokens: str | Iterable[str],
        *,
        frames: int | None = None,
        weights: dict[str, float] | None = None,
        reference_positions: Iterable[float] | None = None,
        caregiver_protective_support: bool = False,
        caregiver_support_scale: float | None = None,
        caregiver_manifold_residual: Iterable[float] | None = None,
        caregiver_manifold_decisive_tick: float | None = None,
    ) -> dict[str, Any]:
        """Enact a graph-selected motor bundle and optional external support.

        Caregiver support is an exafferent world intervention. Its graph-
        authored scale applies that fraction of one body-weight during the held
        child action, changing the consequence without changing the selected
        motor command or receiving child agency credit.
        """
        self._require_open()
        selected = (tokens,) if isinstance(tokens, str) else tuple(tokens)
        if not selected:
            raise ValueError("humanoid actuator bundle must not be empty")
        selected = tuple(dict.fromkeys(selected))
        twitches = []
        occupied_groups: set[int] = set()
        weights = {} if weights is None else dict(weights)
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
                        "tonic command cannot be combined with joint twitches: "
                        f"{selected!r}"
                    )
                continue
            joint_ordinal, _direction = twitch
            if joint_ordinal in occupied_groups:
                raise ValueError(
                    "humanoid actuator bundle contains conflicting joint "
                    f"group {joint_ordinal}: {selected!r}"
                )
            occupied_groups.add(joint_ordinal)
            weight = float(weights.get(token, 1.0))
            if weight == 0.0:
                continue
            twitches.append((joint_ordinal, _direction * weight))
        hold_frames = (
            self.configuration.action_frames if frames is None else frames
        )
        if (
            isinstance(hold_frames, bool)
            or not isinstance(hold_frames, int)
            or hold_frames < 1
        ):
            raise ValueError("frames must be a positive integer")
        self._write_twitches(
            twitches,
            reference_positions=reference_positions,
        )
        if not isinstance(caregiver_protective_support, bool):
            raise ValueError("caregiver_protective_support must be boolean")
        if caregiver_support_scale is None:
            caregiver_support_scale = (
                1.0 if caregiver_protective_support else 0.0
            )
        if (
            isinstance(caregiver_support_scale, bool)
            or not math.isfinite(caregiver_support_scale)
            or not 0.0 <= caregiver_support_scale <= 1.0
        ):
            raise ValueError("caregiver_support_scale must be within [0, 1]")
        if not caregiver_protective_support and caregiver_support_scale != 0.0:
            raise ValueError("caregiver support scale requires authorization")
        signed_residual = None
        if caregiver_manifold_residual is not None:
            signed_residual = tuple(float(value) for value in caregiver_manifold_residual)
            if len(signed_residual) != 7 or not all(
                math.isfinite(value) for value in signed_residual
            ):
                raise ValueError(
                    "caregiver_manifold_residual must contain seven finite values"
                )
            if not caregiver_protective_support and any(signed_residual):
                raise ValueError("caregiver manifold residual requires authorization")
        if caregiver_manifold_decisive_tick is not None and (
            isinstance(caregiver_manifold_decisive_tick, bool)
            or not math.isfinite(caregiver_manifold_decisive_tick)
            or caregiver_manifold_decisive_tick < 0.0
        ):
            raise ValueError("caregiver manifold decisive tick must be finite and nonnegative")
        support_applied = caregiver_protective_support and (
            caregiver_support_scale > 0.0
            and (signed_residual is None or any(signed_residual))
        )
        self._last_caregiver_support_applied = support_applied
        self._last_caregiver_support_scale = caregiver_support_scale
        self._last_caregiver_support_impulse_newton_seconds = 0.0
        self._last_caregiver_support_force_world = (0.0, 0.0, 0.0)
        self._last_caregiver_support_torque_world = (0.0, 0.0, 0.0)
        if support_applied:
            assert self._body is not None
            body_weight = self._body_mass * self.configuration.gravity_acceleration
            if signed_residual is None:
                support_frames = hold_frames
                force = (0.0, 0.0, body_weight * caregiver_support_scale)
                torque = (0.0, 0.0, 0.0)
            else:
                support_frames = min(
                    hold_frames,
                    max(1, math.ceil(caregiver_manifold_decisive_tick or hold_frames)),
                )
                duration = self.configuration.time_step * support_frames
                dzx, dzy, dwx, dwy, dvx, dvy, dvz = signed_residual
                raw_force = (
                    -self._body_mass * dvx / duration,
                    -self._body_mass * dvy / duration,
                    -self._body_mass * dvz / duration,
                )
                inertia = self._body_mass * self._body_length_scale ** 2
                raw_torque = (
                    -inertia * dwx / duration + 2.0 * inertia * dzy / duration ** 2,
                    -inertia * dwy / duration - 2.0 * inertia * dzx / duration ** 2,
                    0.0,
                )
                def _capped(vector, limit):
                    magnitude = math.sqrt(sum(value * value for value in vector))
                    factor = min(1.0, limit / magnitude) if magnitude > 0.0 else 0.0
                    return tuple(value * factor for value in vector)
                force = _capped(raw_force, body_weight * caregiver_support_scale)
                torque = _capped(
                    raw_torque,
                    body_weight * self._body_length_scale * caregiver_support_scale,
                )
            self._last_caregiver_support_force_world = force
            self._last_caregiver_support_torque_world = torque
            for _ in range(support_frames):
                position, _orientation = _bullet.getBasePositionAndOrientation(
                    self._body,
                    physicsClientId=self._client,
                )
                _bullet.applyExternalForce(
                    self._body,
                    -1,
                    forceObj=force,
                    posObj=position,
                    flags=_bullet.WORLD_FRAME,
                    physicsClientId=self._client,
                )
                _bullet.applyExternalTorque(
                    self._body,
                    -1,
                    torqueObj=torque,
                    flags=_bullet.WORLD_FRAME,
                    physicsClientId=self._client,
                )
                self._advance(1)
            if support_frames < hold_frames:
                self._advance(hold_frames - support_frames)
            self._last_caregiver_support_impulse_newton_seconds = (
                math.sqrt(sum(value * value for value in force))
                * self.configuration.time_step
                * support_frames
            )
        else:
            self._advance(hold_frames)
        self._action_index += 1
        self._last_tokens = selected
        return self.observe()

    def hold_tonic(self, frames: int) -> dict[str, Any]:
        """Hold the body's currently sensed configuration for a fixed horizon."""
        self._require_open()
        if isinstance(frames, bool) or not isinstance(frames, int) or frames < 1:
            raise ValueError("frames must be a positive integer")
        self._write_twitches(())
        self._advance(frames)
        self._last_tokens = ("humanoid_actuator_000",)
        return self.observe()

    def scaffold_joint_cycle(self, joint_ordinal: int) -> dict[str, Any]:
        """Mechanically cycle one joint without claiming motor agency."""
        self._require_open()
        if (
            isinstance(joint_ordinal, bool)
            or not isinstance(joint_ordinal, int)
            or not 0 <= joint_ordinal < len(self._joint_indices)
        ):
            raise ValueError("joint_ordinal is outside the articulated body")
        reference = tuple(
            float(state[0])
            for state in _bullet.getJointStates(
                self._body,
                self._joint_indices,
                physicsClientId=self._client,
            )
        )
        frames = self.configuration.action_frames
        observed_shapes = [tuple(
            round(value / self.configuration.joint_twitch_radians)
            for value in reference
        )]
        self._write_twitches(
            ((joint_ordinal, 1.0),),
            reference_positions=reference,
        )
        self._advance(frames, measure_energy=False)
        observed_shapes.append(tuple(
            round(float(state[0]) / self.configuration.joint_twitch_radians)
            for state in _bullet.getJointStates(
                self._body,
                self._joint_indices,
                physicsClientId=self._client,
            )
        ))
        self._write_twitches(
            ((joint_ordinal, -1.0),),
            reference_positions=reference,
        )
        self._advance(frames, measure_energy=False)
        observed_shapes.append(tuple(
            round(float(state[0]) / self.configuration.joint_twitch_radians)
            for state in _bullet.getJointStates(
                self._body,
                self._joint_indices,
                physicsClientId=self._client,
            )
        ))
        self._write_twitches((), reference_positions=reference)
        self._advance(frames, measure_energy=False)
        self._last_tokens = ()
        self._last_supplied_energy_joules = 0.0
        self._last_absorbed_energy_joules = 0.0
        self._last_peak_actuator_power_watts = 0.0
        observation = self.observe()
        final_shape = tuple(
            round(float(state[0]) / self.configuration.joint_twitch_radians)
            for state in _bullet.getJointStates(
                self._body,
                self._joint_indices,
                physicsClientId=self._client,
            )
        )
        observed_shapes.append(final_shape)
        initial_shape, positive_shape, negative_shape, returned_shape = (
            observed_shapes
        )
        observation["scaffold_configuration_changed"] = int(
            len(set(observed_shapes)) > 1
        )
        observation["scaffold_configuration_trajectory"] = tuple(
            observed_shapes
        )
        observation["scaffold_positive_excursion_units"] = int(
            positive_shape[joint_ordinal] - initial_shape[joint_ordinal]
        )
        observation["scaffold_negative_excursion_units"] = int(
            negative_shape[joint_ordinal] - initial_shape[joint_ordinal]
        )
        observation["scaffold_return_residual_units"] = int(
            returned_shape[joint_ordinal] - initial_shape[joint_ordinal]
        )
        observation["scaffold_coupled_channel_count"] = sum(
            any(shape[index] != initial_shape[index]
                for shape in observed_shapes[1:])
            for index in range(len(initial_shape))
            if index != joint_ordinal
        )
        return observation

    def scaffold_body_bounce(self) -> dict[str, Any]:
        """Apply one body-scaled external load wave without an efference copy."""
        self._require_open()
        assert self._body is not None
        before_position, _ = _bullet.getBasePositionAndOrientation(
            self._body,
            physicsClientId=self._client,
        )
        before_observation = self.observe()
        support_count = max(1, len(self._support_link_indices))
        weight = self._body_mass * self.configuration.gravity_acceleration
        upward_force = weight + weight / support_count
        frames = self.configuration.action_frames
        for _ in range(frames):
            position, _ = _bullet.getBasePositionAndOrientation(
                self._body,
                physicsClientId=self._client,
            )
            _bullet.applyExternalForce(
                self._body,
                -1,
                forceObj=(0.0, 0.0, upward_force),
                posObj=position,
                flags=_bullet.WORLD_FRAME,
                physicsClientId=self._client,
            )
            self._advance(1, measure_energy=False)
        self._write_twitches(())
        self._advance(frames, measure_energy=False)
        self._last_tokens = ()
        self._last_supplied_energy_joules = 0.0
        self._last_absorbed_energy_joules = 0.0
        self._last_peak_actuator_power_watts = 0.0
        observation = self.observe()
        observation["scaffold_load_changed"] = int(
            tuple(observation["base_position"]) != tuple(before_position)
        )
        vertical_delta = float(observation["base_position"][2]) - float(
            before_position[2]
        )
        observation["scaffold_vertical_direction"] = (
            int(vertical_delta > 0.0) - int(vertical_delta < 0.0)
        )
        observation["scaffold_support_count_before"] = len(
            before_observation["support_contact_forces"]
        )
        observation["scaffold_support_count_after"] = len(
            observation["support_contact_forces"]
        )
        observation["scaffold_support_count_change"] = int(
            observation["scaffold_support_count_after"]
            - observation["scaffold_support_count_before"]
        )
        return observation

    def apply_force_pulse(
        self,
        force_xyz: Iterable[float],
        *,
        frames: int = 1,
    ) -> dict[str, Any]:
        """Apply a declared world-frame base force for a fixed frame count."""
        self._require_open()
        force = _triple(force_xyz, field="force_xyz")
        if isinstance(frames, bool) or not isinstance(frames, int) or frames < 1:
            raise ValueError("frames must be a positive integer")
        assert self._body is not None
        for _ in range(frames):
            position, _ = _bullet.getBasePositionAndOrientation(
                self._body,
                physicsClientId=self._client,
            )
            _bullet.applyExternalForce(
                self._body,
                -1,
                forceObj=force,
                posObj=position,
                flags=_bullet.WORLD_FRAME,
                physicsClientId=self._client,
            )
            self._advance(1)
        return self.observe()

    def observe(self) -> dict[str, Any]:
        """Return raw base, joint, and contact sensor state."""
        self._require_open()
        assert self._body is not None
        position, orientation = _bullet.getBasePositionAndOrientation(
            self._body,
            physicsClientId=self._client,
        )
        linear_velocity, angular_velocity = _bullet.getBaseVelocity(
            self._body,
            physicsClientId=self._client,
        )
        joint_states = _bullet.getJointStates(
            self._body,
            self._joint_indices,
            physicsClientId=self._client,
        )
        contacts = _bullet.getContactPoints(
            bodyA=self._body,
            physicsClientId=self._client,
        )
        link_states = tuple(
            _bullet.getLinkState(
                self._body,
                link_index,
                computeLinkVelocity=1,
                physicsClientId=self._client,
            )
            for link_index in range(
                _bullet.getNumJoints(
                    self._body,
                    physicsClientId=self._client,
                )
            )
        )
        base_mass = float(
            _bullet.getDynamicsInfo(
                self._body,
                -1,
                physicsClientId=self._client,
            )[0]
        )
        link_masses = tuple(
            float(
                _bullet.getDynamicsInfo(
                    self._body,
                    link_index,
                    physicsClientId=self._client,
                )[0]
            )
            for link_index in range(len(link_states))
        )
        mass_positions = (
            (base_mass, _np.asarray(position, dtype=float)),
            *(
                (
                    mass,
                    _np.asarray(state[0], dtype=float),
                )
                for mass, state in zip(link_masses, link_states)
            ),
        )
        centre_of_mass = sum(
            mass * link_position
            for mass, link_position in mass_positions
        ) / max(self._body_mass, _np.finfo(float).eps)
        mass_velocities = (
            (
                base_mass,
                _np.asarray(position, dtype=float),
                _np.asarray(linear_velocity, dtype=float),
                _np.asarray(angular_velocity, dtype=float),
                _np.asarray(orientation, dtype=float),
                -1,
            ),
            *(
                (
                    mass,
                    _np.asarray(state[0], dtype=float),
                    _np.asarray(state[6], dtype=float),
                    _np.asarray(state[7], dtype=float),
                    _np.asarray(state[1], dtype=float),
                    link_index,
                )
                for link_index, (mass, state) in enumerate(
                    zip(link_masses, link_states)
                )
            ),
        )
        linear_momentum = sum(
            mass * velocity
            for mass, _position, velocity, _angular, _orientation, _index
            in mass_velocities
        )
        angular_momentum = _np.zeros(3, dtype=float)
        for (
            mass,
            link_position,
            velocity,
            link_angular_velocity,
            link_orientation,
            link_index,
        ) in mass_velocities:
            angular_momentum += _np.cross(
                link_position - centre_of_mass,
                mass * velocity,
            )
            local_inertia = _np.asarray(
                _bullet.getDynamicsInfo(
                    self._body,
                    link_index,
                    physicsClientId=self._client,
                )[2],
                dtype=float,
            )
            rotation = _np.asarray(
                _bullet.getMatrixFromQuaternion(link_orientation),
                dtype=float,
            ).reshape(3, 3)
            world_inertia = rotation @ _np.diag(local_inertia) @ rotation.T
            angular_momentum += world_inertia @ link_angular_velocity
        support_forces = {
            link_index: 0.0 for link_index in self._support_link_indices
        }
        whole_body_support: dict[int, dict[str, Any]] = {}
        for contact in contacts:
            link_index = int(contact[3])
            if link_index in support_forces:
                support_forces[link_index] += max(0.0, float(contact[9]))
            if int(contact[2]) not in self._ground_bodies:
                continue
            force = max(0.0, float(contact[9]))
            if force <= 0.0:
                continue
            row = whole_body_support.setdefault(link_index, {
                "normal_force": 0.0,
                "weighted_position": _np.zeros(3, dtype=float),
            })
            row["normal_force"] += force
            row["weighted_position"] += (
                force * _np.asarray(contact[5], dtype=float)
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
            "simulator": "pybullet",
            "asset": self.configuration.asset,
            "seed": self.seed,
            "body_mass": self._body_mass,
            "body_length_scale": self._body_length_scale,
            "body_capability_signature": self.body_capability_signature(),
            "gravity_acceleration": self.configuration.gravity_acceleration,
            "step_index": self._step_index,
            "sim_time": self._step_index * self.configuration.time_step,
            "body_id": self._body,
            "base_position": _floats(position),
            # The per-frame vertical trace for the trial in progress, oldest
            # first. Transport only: the boundary decides nothing about what a
            # descent means.
            "base_height_trace": tuple(self._base_height_trace),
            "base_orientation_xyzw": _floats(orientation),
            "base_linear_velocity": _floats(linear_velocity),
            "base_angular_velocity": _floats(angular_velocity),
            "whole_body_centre_of_mass": _floats(centre_of_mass),
            "whole_body_linear_momentum": _floats(linear_momentum),
            "whole_body_angular_momentum": _floats(angular_momentum),
            "links": tuple(
                {
                    "index": link_index,
                    "mass": link_masses[link_index],
                    "centre_of_mass_position": _floats(state[0]),
                    "centre_of_mass_orientation_xyzw": _floats(state[1]),
                    "link_frame_position": _floats(state[4]),
                    "link_frame_orientation_xyzw": _floats(state[5]),
                    "linear_velocity": _floats(state[6]),
                    "angular_velocity": _floats(state[7]),
                }
                for link_index, state in enumerate(link_states)
            ),
            "joints": tuple(
                {
                    "ordinal": ordinal,
                    "index": joint_index,
                    "position": float(state[0]),
                    "velocity": float(state[1]),
                    "reaction_forces": _floats(state[2]),
                    "applied_torque": float(state[3]),
                    "lower_limit": float(
                        _bullet.getJointInfo(
                            self._body,
                            joint_index,
                            physicsClientId=self._client,
                        )[8]
                    ),
                    "upper_limit": float(
                        _bullet.getJointInfo(
                            self._body,
                            joint_index,
                            physicsClientId=self._client,
                        )[9]
                    ),
                    "maximum_force": float(
                        _bullet.getJointInfo(
                            self._body,
                            joint_index,
                            physicsClientId=self._client,
                        )[10]
                    ),
                    "maximum_velocity": float(
                        _bullet.getJointInfo(
                            self._body,
                            joint_index,
                            physicsClientId=self._client,
                        )[11]
                    ),
                }
                for ordinal, (joint_index, state) in enumerate(
                    zip(self._joint_indices, joint_states)
                )
            ),
            "contacts": tuple(
                {
                    "body_a": int(contact[1]),
                    "body_b": int(contact[2]),
                    "link_a": int(contact[3]),
                    "link_b": int(contact[4]),
                    "position_on_a": _floats(contact[5]),
                    "position_on_b": _floats(contact[6]),
                    "normal_on_b": _floats(contact[7]),
                    "distance": float(contact[8]),
                    "normal_force": float(contact[9]),
                    "normal_impulse": (
                        float(contact[9]) * self.configuration.time_step
                    ),
                    "lateral_friction_1": float(contact[10]),
                    "lateral_direction_1": _floats(contact[11]),
                    "lateral_friction_2": float(contact[12]),
                    "lateral_direction_2": _floats(contact[13]),
                }
                for contact in contacts
            ),
            "support_contact_forces": tuple(
                {
                    "ordinal": ordinal,
                    "link_index": link_index,
                    "normal_force": support_forces[link_index],
                    "world_position": _floats(
                        _bullet.getLinkState(
                            self._body,
                            link_index,
                            physicsClientId=self._client,
                        )[4]
                    ),
                }
                for ordinal, link_index in enumerate(
                    self._support_link_indices
                )
            ),
            "whole_body_support_contacts": tuple(
                {
                    "ordinal": ordinal,
                    "link_index": link_index,
                    "normal_force": float(row["normal_force"]),
                    "world_position": _floats(
                        row["weighted_position"] / row["normal_force"]
                    ),
                }
                for ordinal, (link_index, row) in enumerate(
                    sorted(whole_body_support.items())
                )
            ),
            "supplied_energy_joules": self._last_supplied_energy_joules,
            "absorbed_energy_joules": self._last_absorbed_energy_joules,
            "peak_actuator_power_watts": self._last_peak_actuator_power_watts,
            "peak_contact_force_newtons": (
                self._last_peak_contact_force_newtons
            ),
            # Instantaneous total, not a peak over the action: the sum of
            # normal-force magnitudes over every contact point involving this
            # body at THIS snapshot. Zero when no contact is reported.
            "contact_force_newtons": float(sum(
                max(0.0, float(contact[9])) for contact in contacts
            )),
            "contact_normal_impulse_newton_seconds": (
                self._last_contact_normal_impulse_newton_seconds
            ),
            "caregiver_protective_support_applied": int(
                self._last_caregiver_support_applied
            ),
            "caregiver_support_scale": self._last_caregiver_support_scale,
            "caregiver_support_impulse_newton_seconds": (
                self._last_caregiver_support_impulse_newton_seconds
            ),
            "caregiver_support_force_world": self._last_caregiver_support_force_world,
            "caregiver_support_torque_world": self._last_caregiver_support_torque_world,
            "last_actuator_token": (
                self._last_tokens[0] if len(self._last_tokens) == 1 else None
            ),
            "last_actuator_tokens": self._last_tokens,
            "motor_reference_kind": self._last_motor_reference_kind,
            "motor_reference_positions": self._last_motor_reference_positions,
            "motor_target_positions": self._last_motor_target_positions,
            "motor_command_displacements": (
                self._last_motor_command_displacements
            ),
            "motor_configuration_shape": tuple(
                round(
                    float(state[0])
                    / self.configuration.joint_twitch_radians
                )
                for state in joint_states
            ),
            "actuator_activation_seconds": self.configuration.time_step,
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
                0.9,
            ),
            distance=4.0,
            yaw=38.0,
            pitch=-10.0,
            roll=0.0,
            upAxisIndex=2,
        )
        projection = _bullet.computeProjectionMatrixFOV(
            fov=48.0,
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

    def _write_twitches(
        self,
        twitches: Iterable[tuple[int, float]],
        *,
        reference_positions: Iterable[float] | None = None,
    ) -> None:
        assert self._body is not None
        joint_states = _bullet.getJointStates(
            self._body,
            self._joint_indices,
            physicsClientId=self._client,
        )
        if reference_positions is None:
            references = [float(state[0]) for state in joint_states]
            reference_kind = "current_sensed_configuration"
        else:
            references = [float(value) for value in reference_positions]
            if len(references) != len(self._joint_indices):
                raise ValueError(
                    "motor reference must contain one position per joint"
                )
            if not all(math.isfinite(value) for value in references):
                raise ValueError("motor reference positions must be finite")
            reference_kind = "graph_situated_fixation"
        targets = list(references)
        for twitch in twitches:
            joint_ordinal, direction = twitch
            target = references[joint_ordinal] + (
                direction * self.configuration.joint_twitch_radians
            )
            joint_info = _bullet.getJointInfo(
                self._body,
                self._joint_indices[joint_ordinal],
                physicsClientId=self._client,
            )
            lower_limit = float(joint_info[8])
            upper_limit = float(joint_info[9])
            if lower_limit <= upper_limit:
                target = min(upper_limit, max(lower_limit, target))
            targets[joint_ordinal] = target
        self._last_motor_reference_positions = tuple(references)
        self._last_motor_reference_kind = reference_kind
        self._last_motor_target_positions = tuple(targets)
        self._last_motor_command_displacements = tuple(
            target - reference
            for reference, target in zip(references, targets)
        )
        joint_count = len(self._joint_indices)
        _bullet.setJointMotorControlArray(
            self._body,
            self._joint_indices,
            _bullet.POSITION_CONTROL,
            targetPositions=targets,
            forces=(
                self._joint_force_limits
                if len(self._joint_force_limits) == joint_count
                else (self.configuration.maximum_joint_force,) * joint_count
            ),
            positionGains=(self.configuration.position_gain,) * joint_count,
            velocityGains=(self.configuration.velocity_gain,) * joint_count,
            physicsClientId=self._client,
        )

    def _advance(self, frames: int, *, measure_energy: bool = True) -> None:
        supplied = 0.0
        absorbed = 0.0
        peak_power = 0.0
        peak_contact_force = 0.0
        contact_normal_impulse = 0.0
        for _ in range(frames):
            _bullet.stepSimulation(physicsClientId=self._client)
            # THE VERTICAL TRACE IS MEASURED ON EVERY FRAME, including the
            # unmeasured-energy settling frames — the settle IS the body's drop
            # and is exactly the approach a forward projection would read.
            # Recorded before the energy branch so no accounting flag can
            # silently blind the channel.
            if self._body is not None:
                trace_position, _trace_orientation = (
                    _bullet.getBasePositionAndOrientation(
                        self._body, physicsClientId=self._client
                    )
                )
                self._base_height_trace.append(float(trace_position[2]))
            if not measure_energy:
                continue
            contacts = _bullet.getContactPoints(
                bodyA=self._body,
                physicsClientId=self._client,
            )
            frame_contact_force = sum(
                max(0.0, float(contact[9])) for contact in contacts
            )
            peak_contact_force = max(
                peak_contact_force,
                frame_contact_force,
            )
            contact_normal_impulse += (
                frame_contact_force * self.configuration.time_step
            )
            joint_states = _bullet.getJointStates(
                self._body,
                self._joint_indices,
                physicsClientId=self._client,
            )
            signed_power = tuple(
                float(state[1]) * float(state[3])
                for state in joint_states
            )
            supplied_power = sum(max(0.0, value) for value in signed_power)
            absorbed_power = sum(max(0.0, -value) for value in signed_power)
            supplied += supplied_power * self.configuration.time_step
            absorbed += absorbed_power * self.configuration.time_step
            peak_power = max(peak_power, supplied_power + absorbed_power)
        self._last_supplied_energy_joules = supplied
        self._last_absorbed_energy_joules = absorbed
        self._last_peak_actuator_power_watts = peak_power
        self._last_peak_contact_force_newtons = peak_contact_force
        self._last_contact_normal_impulse_newton_seconds = (
            contact_normal_impulse
        )
        self._step_index += frames

    def _require_open(self) -> None:
        if self._client < 0 or not _bullet.isConnected(self._client):
            raise RuntimeError("PyBulletHumanoidWorld is closed")


__all__ = [
    "HUMANOID_ASSET",
    "HumanoidBodyConfiguration",
    "PyBulletHumanoidWorld",
]
