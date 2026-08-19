"""Mechanical PyBullet trial boundary for graph-selected humanoid work.

This is deliberately narrower than the historical humanoid runners.  It has
no motor policy, pose policy, reset policy, goal interpretation, or learning
state.  The Rust graph must already have selected one
``EmbodiedExternalTrialRequest`` and attached its exact program, pose
affordance, and reset scenario.  This module only translates that selected
graph data into the existing PyBullet body API, then quantizes the resulting
physical measurements back into integer evidence.

All real values stay at the simulator boundary.  Every attribute written to
the substrate is an integer (apart from descriptive strings), so the graph's
in-frame cognition remains integer-native.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from domains.pybullet_humanoid_world import (
    HUMANOID_ASSET,
    HumanoidBodyConfiguration,
    PyBulletHumanoidWorld,
)


# These are interface units, not cognitive preferences.  They define the
# one-way continuous-simulator -> integer-graph measurement representation.
# A future body adapter can expose different declared units without changing
# any graph policy.
_MINIMUM_ACTUATION_FRAMES = 1
_SIMULATOR_WEIGHT_SCALE_UNITS = 1
_MINIMUM_NONZERO_WEIGHT_UNITS = 1
_DISPLACEMENT_UNITS_PER_METRE = 1000
_ENERGY_UNITS_PER_JOULE = 1000
_LOAD_UNITS_PER_NEWTON = 1
# Joint travel is an ANGLE and needs its own declared scale.  It must not
# borrow `_DISPLACEMENT_UNITS_PER_METRE`: that scale already carries
# `declared_position_change`, which is a dimensionless direction FRACTION
# (`abs(twitch[1])` = 1.0 -> 1000 units) whose physical size is
# `joint_twitch_radians`, not a metre and not a radian.  Quantities on the two
# scales are not comparable and nothing may `Max` one against the other.
_ANGLE_UNITS_PER_RADIAN = 1000
# Joint load is a TORQUE and needs its own declared scale for the same reason
# travel does. Measured range on this body standing: 0.001 to 10.4 N*m, so a
# milli-newton-metre unit keeps the small readings from quantising to nothing
# -- and a joint whose load rounds to zero is correctly read as bearing none.
_TORQUE_UNITS_PER_NEWTON_METRE = 1000
# The simulator's code for a RIGID (welded) joint. A link joined this way moves
# exactly with its parent, so carriage passes THROUGH it unchanged -- which is
# what makes the ancestor walk in `_carried_by_effector_relations` a fact about
# the body rather than an approximation. Any other unactuated joint (a free
# hinge, say) genuinely DECOUPLES and must break the chain instead.
_RIGID_JOINT_TYPE = 4


def _require_integer(attrs: dict[str, Any], key: str, *, minimum: int | None = None) -> int:
    value = attrs.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise RuntimeError(f"graph-selected humanoid program requires integer {key!r}")
    if minimum is not None and value < minimum:
        raise RuntimeError(
            f"graph-selected humanoid program requires {key!r} >= {minimum}"
        )
    return value


def _one_neighbour(adapter, source, edge_type: str, expected_type: str):
    """Read one graph-authored boundary reference without selecting among it."""
    matches = list(adapter.inner.neighbours(source, edge_type))
    if len(matches) != 1:
        raise RuntimeError(
            f"selected embodied trial requires exactly one {edge_type!r}; got {len(matches)}"
        )
    target = matches[0]
    node = adapter.s.node(target)
    if node["type"] != expected_type:
        raise RuntimeError(
            f"selected {edge_type!r} must be {expected_type}, got {node['type']!r}"
        )
    return target


def _integer_sequence(value: Any, *, key: str) -> tuple[int, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, (tuple, list)):
        raise RuntimeError(f"graph-selected humanoid program requires sequence {key!r}")
    result = tuple(value)
    if not result or any(isinstance(item, bool) or not isinstance(item, int) for item in result):
        raise RuntimeError(f"graph-selected humanoid program requires integer {key!r}")
    return result


def _token_sequence(value: Any) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, (tuple, list)):
        raise RuntimeError("graph-selected humanoid program requires simulator_tokens")
    tokens = tuple(value)
    if not tokens or any(not isinstance(token, str) or not token for token in tokens):
        raise RuntimeError("graph-selected humanoid program has invalid simulator_tokens")
    return tokens


def _find_channel(adapter, name: str):
    """Mechanical graph lookup of a declared channel by name.

    The transducer holds no state — it is a frozen dataclass and the graph is
    the source of truth — so the channel minted at attach is found here rather
    than cached on the instance.
    """
    for effector in adapter.s.nodes("EmbodiedEffector"):
        for channel in adapter.inner.neighbours(effector, "has_sensed_channel"):
            if adapter.s.node(channel)["attrs"].get("channel") == name:
                return channel
    return None


def _support_topology(observation) -> tuple[int, ...]:
    """The SET of body links in ground contact, as sorted link indices.

    Support topology is WHICH contacts exist, not how hard they push:
    `peak_contact_force_newtons` answers the second question and cannot answer
    the first. `whole_body_support_contacts` is the world's own ground-contact
    report (the protocol's `all_tactile_contacts_plus_legacy_distal_pair`),
    unlike `support_contact_forces`, which is a FIXED-LENGTH pair over two
    legacy distal links and whose length is therefore always 2 whatever the
    body is touching.

    Pure extraction: it reads what the simulator already computed and sorts it
    so the same topology always compares equal. It decides nothing about what a
    change of topology means.
    """
    rows = observation.get("whole_body_support_contacts")
    if not isinstance(rows, (tuple, list)):
        return ()
    links = []
    for row in rows:
        if isinstance(row, dict) and row.get("link_index") is not None:
            links.append(int(row["link_index"]))
    return tuple(sorted(set(links)))


def _quantize(value: float, units_per_external_unit: int) -> int:
    """Cross the continuous simulator -> integer graph boundary once."""
    return int(round(float(value) * units_per_external_unit))


# Declared interface resolution for the per-frame vertical stream, in the same
# class as `_DISPLACEMENT_UNITS_PER_METRE`: how many samples of a trial's trace
# cross the boundary, and how they are spaced.  Deliberately spread ACROSS the
# whole trace rather than taken from one end, so the boundary never chooses
# which part of a trajectory the graph gets to see.  A minimum of three is
# forced by the projection itself (a second difference needs three samples);
# below that the stream is honestly unprojectable rather than padded.
_VERTICAL_STREAM_SAMPLES = 8


def _stream_samples(trace) -> tuple[float, ...]:
    """Even, order-preserving subsample of one trial's per-frame trace.

    Mechanical decimation, nothing else: it selects EVENLY over the whole
    trace and always retains the final frame, so the samples are the body's
    own trajectory at a coarser rate and the most recent state is never
    dropped.  It smooths nothing, extrapolates nothing, and drops no interval
    preferentially.
    """
    values = [float(v) for v in trace]
    if len(values) <= _VERTICAL_STREAM_SAMPLES:
        return tuple(values)
    last = len(values) - 1
    indices = sorted({
        round(last * ordinal / (_VERTICAL_STREAM_SAMPLES - 1))
        for ordinal in range(_VERTICAL_STREAM_SAMPLES)
    })
    return tuple(values[index] for index in indices)


def _carried_by_effector_relations(
    body_shape_relations: list[list[Any]],
) -> tuple[tuple[int, int], ...]:
    """Return `(child_channel, parent_channel)` pairs — DIRECTION PRESERVED.

    `_directed_local_effector_relations` below computes exactly this parent
    relation and then destroys it: `tuple(sorted((channel, parent_channel)))`
    collapses child-and-parent into one unordered pair, which it re-emits
    symmetrically. So the graph could see that two channels are mechanically
    ADJACENT but never which one CARRIES the other, and a body whose effectors
    are a tree was published as a flat set of 21 peer joint groups.

    DEPENDENT EFFECTORS ARE NOT PEERS. Measured on the desk trials
    (2026-08-07): in every condition the elbow deflected 0.000 while the
    shoulder deflected 0.726 rad. The forearm is a rigid pendulum carried by
    the shoulder, so yielding the hand is something only the SHOULDER can do —
    the hand's own actuator is irrelevant to whether the hand gives. Authority
    is inherited down the chain: releasing a parent releases everything distal
    to it, and releasing a child does nothing about the parent carrying it.
    A flat peer model cannot express that, and cannot attribute a distal
    displacement to the joint that caused it.

    This is morphology sensing, exactly as the symmetric version is: the host
    reports which declared link carries which, and nothing here decides what a
    limb is. The graph derives chains from these edges on its own terms.

    CARRIAGE PASSES THROUGH A WELD. The first version mapped a joint's parent
    LINK straight to a channel and gave up when that link was not itself an
    actuated joint -- so any rigidly-welded intermediate SEVERED the chain.
    Measured on the MJCF humanoid (2026-08-07): 12 of its 33 links are FIXED and
    they sit between actuated joints throughout, which cost NINE of eighteen
    carriage edges and left FIVE of twenty-one joint groups outside every chain
    -- including both joints that stand on their travel stop, the exact case the
    authority work exists to describe. They reached no limb and therefore no
    settle at all.

    A rigid weld moves exactly with its parent, so a joint beyond one is carried
    by the nearest ACTUATED ancestor and the walk is a fact about the body, not
    an approximation. The walk stops at anything else: an unactuated joint that
    is NOT rigid (a free hinge) genuinely decouples, and treating it as
    transparent would claim a carriage relation the mechanism does not provide.
    A joint whose walk reaches the base without finding an actuated ancestor is
    a true root and correctly gets no edge.
    """
    joint_for_channel: dict[int, int] = {}
    parent_for_joint: dict[int, int] = {}
    rigid_joint: dict[int, bool] = {}
    for relation in body_shape_relations:
        if not relation:
            continue
        if relation[0] == "link" and len(relation) >= 3:
            joint, parent = relation[1:3]
            if (isinstance(joint, int) and not isinstance(joint, bool)
                    and isinstance(parent, int) and not isinstance(parent, bool)):
                parent_for_joint[joint] = parent
                # The type rides along at index 3 when the signature carries it.
                # Absent, nothing is assumed rigid and the behaviour collapses
                # to the original direct-parent lookup rather than inventing
                # carriage the signature never reported.
                if len(relation) >= 4 and isinstance(relation[3], int):
                    rigid_joint[joint] = relation[3] == _RIGID_JOINT_TYPE
        elif relation[0] == "actuator" and len(relation) >= 3:
            channel, joint = relation[1:3]
            if (isinstance(channel, int) and not isinstance(channel, bool)
                    and isinstance(joint, int) and not isinstance(joint, bool)):
                joint_for_channel[channel] = joint
    channel_for_joint = {joint: channel for channel, joint in joint_for_channel.items()}

    def carrying_channel(joint: int) -> int | None:
        """Nearest actuated ancestor, walking through rigid welds only."""
        seen: set[int] = set()
        current = parent_for_joint.get(joint)
        while (current is not None and current >= 0 and current not in seen):
            seen.add(current)
            if current in channel_for_joint:
                return channel_for_joint[current]
            if not rigid_joint.get(current, False):
                return None
            current = parent_for_joint.get(current)
        return None

    return tuple(sorted(
        (channel, parent_channel)
        for channel, joint in joint_for_channel.items()
        for parent_channel in (carrying_channel(joint),)
        if parent_channel is not None and parent_channel != channel
    ))


def _directed_local_effector_relations(
    body_shape_relations: list[list[Any]],
) -> tuple[tuple[int, int], ...]:
    """Return mechanically adjacent actuator *channels* in both directions.

    This is morphology sensing, not a motor proposal: a relation exists only
    where the declared link tree joins two actuated joints.  In particular it
    never takes an all-pairs product of exposed commands.  Command polarity
    remains opaque and is deliberately left to graph-side consequence-driven
    synthesis.
    """
    joint_for_channel: dict[int, int] = {}
    parent_for_joint: dict[int, int] = {}
    for relation in body_shape_relations:
        if not relation:
            continue
        if relation[0] == "link" and len(relation) >= 3:
            joint, parent = relation[1:3]
            if (isinstance(joint, int) and not isinstance(joint, bool)
                    and isinstance(parent, int) and not isinstance(parent, bool)):
                parent_for_joint[joint] = parent
        elif relation[0] == "actuator" and len(relation) >= 3:
            channel, joint = relation[1:3]
            if (isinstance(channel, int) and not isinstance(channel, bool)
                    and isinstance(joint, int) and not isinstance(joint, bool)):
                joint_for_channel[channel] = joint

    channel_for_joint = {joint: channel for channel, joint in joint_for_channel.items()}
    undirected = {
        tuple(sorted((channel, parent_channel)))
        for channel, joint in joint_for_channel.items()
        for parent_channel in (channel_for_joint.get(parent_for_joint.get(joint)),)
        if parent_channel is not None and parent_channel != channel
    }
    return tuple(
        pair
        for left, right in sorted(undirected)
        for pair in ((left, right), (right, left))
    )


@dataclass(frozen=True)
class PyBulletHumanoidTrialTransducer:
    """Own one opaque PyBullet body and enact exact graph-selected trials."""

    configuration: HumanoidBodyConfiguration
    seed: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "world",
            PyBulletHumanoidWorld(self.configuration, seed=int(self.seed)),
        )

    @classmethod
    def for_attached_world(
        cls,
        configuration: HumanoidBodyConfiguration,
        world: PyBulletHumanoidWorld,
        *,
        seed: int = 0,
    ) -> "PyBulletHumanoidTrialTransducer":
        """Bind the transducer to an already-owned simulator world.

        The caller retains lifecycle ownership. This is the analysis-by-
        synthesis path used when a runner already has the one physical world;
        it must not fork a second simulator merely to publish body facts.
        """
        attached = object.__new__(cls)
        object.__setattr__(attached, "configuration", configuration)
        object.__setattr__(attached, "seed", int(seed))
        object.__setattr__(attached, "world", world)
        return attached

    @classmethod
    def from_protocol(
        cls,
        protocol_path: str | Path,
        *,
        seed: int | None = None,
    ) -> "PyBulletHumanoidTrialTransducer":
        """Construct simulator wiring from an external protocol file.

        The protocol describes host mechanics, not graph policy.  Per-trial
        action duration remains mandatory graph data and is passed explicitly
        to ``world.step`` below.
        """
        path = Path(protocol_path)
        try:
            protocol = json.loads(path.read_text(encoding="utf-8"))
        except OSError as exc:
            raise RuntimeError(f"cannot read humanoid PyBullet protocol {path}: {exc}") from exc
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"invalid humanoid PyBullet protocol {path}: {exc}") from exc
        try:
            body = protocol["body"]
            configuration = HumanoidBodyConfiguration(
                time_step=float(body["time_step_seconds"]),
                gravity_acceleration=float(body["gravity_acceleration"]),
                # The graph-selected program must supply simulator_frames;
                # this value is only the underlying API's unused fallback.
                action_frames=1,
                settling_frames=int(body["initial_settling_frames"]),
                joint_twitch_radians=float(body["joint_twitch_radians"]),
                maximum_joint_force=float(body["maximum_joint_force"]),
                position_gain=float(body["position_gain"]),
                velocity_gain=float(body["velocity_gain"]),
                initial_base_quarter_turns=tuple(
                    int(value)
                    for value in body.get("initial_base_quarter_turns", (0, 0, 0))
                ),
                asset=str(protocol.get("asset", HUMANOID_ASSET)),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise RuntimeError(
                f"invalid humanoid PyBullet mechanics in {path}: {exc}"
            ) from exc
        protocol_seed = protocol.get("seed", 0) if seed is None else seed
        if isinstance(protocol_seed, bool) or not isinstance(protocol_seed, int):
            raise RuntimeError("humanoid PyBullet seed must be an integer")
        return cls(configuration=configuration, seed=protocol_seed)

    def close(self) -> None:
        """Release the body; daemon lifecycle owns this mechanical resource."""
        self.world.close()

    def publish_body_world_capabilities(self, adapter) -> None:
        """Mechanically publish this attached body's raw grounded facts.

        This is deliberately an *ingest* operation.  It does not inspect the
        graph, decide whether a body is usable, select an actuator/program, or
        create the higher-level body schema, world, pose affordance, episode,
        goal, or reset scenario.  ``embodied_body_ingest`` owns those graph
        decisions.  Simulator quantities are reduced to opaque strings and
        integer observations at this boundary.
        """
        raw_shape = [list(relation) for relation in self.world.body_shape_signature()]
        raw_capability = [
            list(relation) for relation in self.world.body_capability_signature()
        ]
        if any(
            isinstance(value, float)
            for relation in (*raw_shape, *raw_capability)
            for value in relation
        ):
            raise RuntimeError("PyBullet body observation leaked a float into cognition")
        if (not raw_shape or len(raw_shape[0]) != 4 or raw_shape[0][0] != "body"):
            raise RuntimeError("PyBullet humanoid body observation has no body relation")
        _body_marker, joint_count, actuator_joint_count, support_channel_count = raw_shape[0]
        if any(
            isinstance(value, bool) or not isinstance(value, int)
            for value in (joint_count, actuator_joint_count, support_channel_count)
        ):
            raise RuntimeError("PyBullet humanoid body relation is not integer-native")

        actuator_options = self.world.actuator_options()
        # Attachment order is a mechanical fact: count the retained external
        # attachment events and publish the next integer.  It is neither a
        # cognitive clock nor a body-selection policy; graph rules consume it
        # to distinguish a newly attached world from retained memories.
        prior_ordinals = []
        for prior in adapter.s.nodes("EmbodiedSimulatorConnection"):
            value = adapter.s.node(prior)["attrs"].get("attachment_event_ordinal")
            if isinstance(value, int) and not isinstance(value, bool) and value > 0:
                prior_ordinals.append(value)
        attachment_event_ordinal = (max(prior_ordinals) if prior_ordinals else 0) + 1
        connection = adapter.s.add_node("EmbodiedSimulatorConnection", {
            "status": "connected",
            "adapter_kind": "pybullet_humanoid",
            "connection_identity": "pybullet_humanoid_trial_transducer",
            # This is the first observed attachment event for this particular
            # simulator resource, not an age, pose, or policy clock.
            "attachment_event_ordinal": attachment_event_ordinal,
            "body_identity": str(self.configuration.asset),
            "seed": int(self.seed),
            "grounded": 1,
            "integer_native": 1,
            "output_authority": 0,
        })
        raw_body = adapter.s.add_node("EmbodiedRawBodyObservation", {
            "observation_status": "observed",
            # The body schema's morphology epoch is grounded in this event,
            # rather than manufactured as an ungrounded default by graph
            # policy.  A later body observation can carry a later ordinal.
            "observation_event_ordinal": attachment_event_ordinal,
            "body_identity": str(self.configuration.asset),
            "body_class": "articulated_humanoid",
            "joint_count": joint_count,
            "actuator_count": int(len(actuator_options)),
            "actuated_joint_count": actuator_joint_count,
            "support_channel_count": support_channel_count,
            "body_shape_relations": raw_shape,
            "body_capability_relations": raw_capability,
            "grounded": 1,
            "integer_native": 1,
            "output_authority": 0,
        })
        reset = adapter.s.add_node("EmbodiedWorldCapability", {
            "capability_kind": "reset_to_declared_fixture", "available": 1,
            "grounded": 1, "integer_native": 1, "output_authority": 0,
        })
        pose_fixture = adapter.s.add_node("EmbodiedWorldCapability", {
            "capability_kind": "declared_pose_fixture", "available": 1,
            "grounded": 1, "integer_native": 1, "output_authority": 0,
        })
        physical_trial = adapter.s.add_node("EmbodiedWorldCapability", {
            "capability_kind": "grounded_physical_trial", "available": 1,
            "grounded": 1, "integer_native": 1, "output_authority": 0,
        })
        raw_motor_interface = adapter.s.add_node("EmbodiedRawMotorInterface", {
            "minimum_actuation_frames": _MINIMUM_ACTUATION_FRAMES,
            # This is deliberately named as an observation bound, not an
            # actuator time constant. The simulator already declares how many
            # integration frames it needs to settle a reset fixture; an
            # uninterrupted exploratory observation must not exceed that
            # mechanically declared convergence horizon.
            "maximum_observation_horizon_frames": int(self.configuration.settling_frames),
            "simulator_weight_scale_units": _SIMULATOR_WEIGHT_SCALE_UNITS,
            "minimum_nonzero_weight_units": _MINIMUM_NONZERO_WEIGHT_UNITS,
            "displacement_units_per_metre": _DISPLACEMENT_UNITS_PER_METRE,
            "energy_units_per_joule": _ENERGY_UNITS_PER_JOULE,
            "load_units_per_newton": _LOAD_UNITS_PER_NEWTON,
            "angle_units_per_radian": _ANGLE_UNITS_PER_RADIAN,
            "torque_units_per_newton_metre": _TORQUE_UNITS_PER_NEWTON_METRE,
            "maximum_joint_force_units": _quantize(
                self.configuration.maximum_joint_force, _LOAD_UNITS_PER_NEWTON
            ),
            "maximum_actuator_bundle_members": int(len(actuator_options)),
            "grounded": 1, "integer_native": 1, "output_authority": 0,
        })
        fixture = tuple(int(value) for value in self.configuration.initial_base_quarter_turns)
        raw_reset_fixture = adapter.s.add_node("EmbodiedRawResetFixture", {
            "fixture_kind": "declared_initial_base_quarter_turns",
            "fixture_event_ordinal": 1,
            "fixture_quarter_turn_x": fixture[0],
            "fixture_quarter_turn_y": fixture[1],
            "fixture_quarter_turn_z": fixture[2],
            "available": 1,
            "grounded": 1,
            "integer_native": 1,
            "output_authority": 0,
        })

        native = adapter.inner
        native.add_edge_unchecked(
            adapter.agent, "has_embodied_simulator_connection", connection
        )
        native.add_edge_unchecked(
            connection, "observes_embodied_raw_body", raw_body
        )
        for capability in (reset, pose_fixture, physical_trial):
            native.add_edge_unchecked(
                connection, "has_embodied_world_capability", capability
            )
        native.add_edge_unchecked(
            connection, "has_embodied_raw_motor_interface", raw_motor_interface
        )
        native.add_edge_unchecked(
            connection, "has_embodied_raw_reset_fixture", raw_reset_fixture
        )
        # THE WHOLE-BODY SENSED CHANNELS.  Peak contact force and vertical
        # displacement are body-level measurements rather than per-actuator
        # ones, so they hang
        # off one whole-body effector.  Declaring them here is what makes them
        # capable of SURPRISE at all: an undeclared channel is dark, a dark
        # channel can never contradict an expectation nor be projected to a
        # crossing, and an effector that cannot surprise can never be rescued.
        #
        # Mechanical throughout: this declares WHICH quantities are observed
        # and mints the nodes to carry them.  It reads no graph state and makes
        # no decision about what any reading means.
        body_effector = adapter.s.add_node("EmbodiedEffector", {
            "effector_identity": "whole_body",
            "body_identity": str(self.configuration.asset),
            # Costs and relevance are the graph's to author, not the adapter's.
            # Left unset deliberately: an unpriced option must not read as free.
            "grounded": 1,
            "integer_native": 1,
            "output_authority": 0,
        })
        native.add_edge_unchecked(
            connection, "has_embodied_effector", body_effector
        )
        # NO INSTANCE STATE: this transducer is a frozen dataclass, and the
        # graph is the source of truth anyway. The channels are looked up from
        # the graph when an observation is published.
        # THE ADAPTER DECLARES ITS OWN MEASUREMENT STEP. Only the boundary that
        # owns the units knows how coarsely it samples, so the quantum is
        # published here rather than assumed by a rule. Each of these channels
        # is quantized onto the integer lattice by `_quantize`, so its step is
        # one unit — but that is now a STATED property of the channel, and a
        # future sensor that resolves only to five units says five and stops
        # reporting four units of disagreement as news. The resolution the
        # value was quantized with travels alongside as provenance: it is what
        # one unit MEANS in the world, which the graph never needs and an
        # auditor always does.
        for name, damage_units, predictor_kind, units_per_external_unit in (
            ("contact_force", 1, "peak_load", _LOAD_UNITS_PER_NEWTON),
            # NAMED FOR THE QUANTITY IT ACTUALLY CARRIES. The program predicts
            # a vertical DELTA (`predicted_vertical_units`), so the channel it
            # is compared against must be a delta too. It was called
            # `base_height` and published an absolute altitude, which made the
            # discrepancy read as the body's height on every single trial.
            ("base_vertical_delta", 1, "vertical", _DISPLACEMENT_UNITS_PER_METRE),
            # THE APPROACH CHANNEL: absolute base height above the world floor,
            # sampled per frame within a trial. It carries NO predictor — no
            # issued command predicts an altitude — so route (a) can never fire
            # on it, which is an honest statement rather than a gap. What it
            # DOES carry is a stream, and a stream is what a forward projection
            # (route (b)) reads: the frame origin of a height is the ground.
            ("base_height_above_ground", 1, None, _DISPLACEMENT_UNITS_PER_METRE),
        ):
            channel = adapter.s.add_node("SensedChannel", {
                "channel": name,
                # Which of the program's declared predictions covers this
                # channel. A channel with no predictor cannot be expected, and
                # therefore cannot be surprised — stated, not silent. Left
                # ABSENT (not "none") where there is none, so the guard that
                # reads it distinguishes "no predictor" from a named one
                # instead of matching a sentinel string.
                **({} if predictor_kind is None
                   else {"predictor_kind": predictor_kind}),
                "declared_units": 0,
                "tolerance_units": 1,
                # One step of the integer lattice this channel is quantized
                # onto: a discrepancy smaller than this is not a discrepancy.
                "quantum_units": 1,
                "quantum_units_per_external_unit": int(units_per_external_unit),
                "damage_units": damage_units,
                "predict_horizon_units": 8,
                "grounded": 1,
                "integer_native": 1,
                "output_authority": 0,
            })
            native.add_edge_unchecked(
                body_effector, "has_sensed_channel", channel
            )
        for axis in range(3):
            for sign in (-1, 1):
                projection = adapter.s.add_node("EmbodiedRawMeasurementProjection", {
                    "projection_kind": "cartesian_displacement",
                    "axis": axis,
                    "sign": sign,
                    "available": 1,
                    "grounded": 1,
                    "integer_native": 1,
                    "output_authority": 0,
                })
                native.add_edge_unchecked(
                    raw_motor_interface,
                    "has_embodied_raw_measurement_projection",
                    projection,
                )
        affordances_by_group: dict[int, list[Any]] = {}
        for ordinal, option in enumerate(actuator_options):
            token = option.get("token")
            if not isinstance(token, str) or not token:
                raise RuntimeError("PyBullet humanoid exposes an invalid opaque actuator token")
            # ``actuator_options`` is simulator I/O and currently reports
            # these booleans/groups as floats.  Quantisation occurs here,
            # before any value reaches the graph; their meanings remain
            # opaque to cognition.
            tonic_default = int(round(float(option.get("tonic_default", 0.0))))
            group = int(round(float(option.get("actuator_group", -1.0))))
            # THE DECLARED AUTHORITY THIS OPTION IS FLOWN BY. Quantised at the
            # boundary like everything else here; `*_measured = 0` because both
            # are CONFIGURATION, never observation. The F-16 pattern
            # (`state_remaining_fuel_kg_measured`, `channel_reserve_measured`)
            # requires the provenance to travel with the number so a declared
            # bound cannot be mistaken for a measured one -- and an achievability
            # ratio is only meaningful against a bound something actually wrote.
            # The SAME module scales this transducer publishes on the raw
            # interface, so a declared bound and a measured reading are in one
            # unit system and an achievability ratio between them is meaningful.
            declared_change = _quantize(
                float(option.get("declared_position_change", 0.0)),
                _DISPLACEMENT_UNITS_PER_METRE,
            )
            declared_force = _quantize(
                float(option.get("declared_joint_force", 0.0)),
                _LOAD_UNITS_PER_NEWTON,
            )
            affordance_attrs: dict[str, Any] = {
                "opaque_token": token,
                "ordinal": int(ordinal),
                "opaque_group_ordinal": group,
                "tonic_default": tonic_default,
                "specified_maximum_position_change_per_action": declared_change,
                "specified_maximum_position_change_per_action_measured": 0,
                "declared_joint_force_units": declared_force,
                "declared_joint_force_units_measured": 0,
                "simulator_max_occurrences": 1,
                "simulator_conflict_group_enforced": int(group >= 0),
                "available": 1,
                "grounded": 1,
                "integer_native": 1,
                "output_authority": 0,
            }
            # THE TRAVEL THE HOST HAS BEEN CLAMPING TO ALL ALONG. Span is the
            # asset's declared configuration; headroom is where the joint stands
            # against it right now, and moves as the body moves -- so their
            # provenance flags DIFFER, which is the whole point of carrying them.
            # Both are ABSENT rather than zero when the option names no joint:
            # a headroom of zero means "at the stop", and reading an undefined
            # channel as that would hand a tonic hold full structural authority.
            span = option.get("declared_travel_span")
            headroom = option.get("command_direction_travel_headroom")
            if span is not None:
                affordance_attrs["declared_joint_travel_span_units"] = _quantize(
                    float(span), _ANGLE_UNITS_PER_RADIAN
                )
                affordance_attrs["declared_joint_travel_span_units_measured"] = 0
            if headroom is not None:
                affordance_attrs[
                    "command_direction_travel_headroom_units"
                ] = _quantize(float(headroom), _ANGLE_UNITS_PER_RADIAN)
                affordance_attrs[
                    "command_direction_travel_headroom_units_measured"
                ] = 1
            # WHICH DIRECTION IS LOADED. Headroom says how much travel this
            # token has; this says whether the load is spending it. INFERRED,
            # not measured: the datum is the actuator's own applied torque and
            # the load is its negation, which holds exactly only quasi-
            # statically. A measured torque must not launder itself into a
            # measured load, so the provenance says which it is.
            load = option.get("command_direction_load")
            if load is not None:
                affordance_attrs["command_direction_load_units"] = _quantize(
                    float(load), _TORQUE_UNITS_PER_NEWTON_METRE
                )
                affordance_attrs["command_direction_load_units_measured"] = 0
                affordance_attrs["command_direction_load_units_inferred"] = 1
            affordance = adapter.s.add_node(
                "EmbodiedOpaqueActuatorAffordance", affordance_attrs
            )
            native.add_edge_unchecked(
                raw_body, "has_opaque_embodied_actuator_affordance", affordance
            )
            if group >= 0:
                affordances_by_group.setdefault(group, []).append(affordance)

        # Publish only the body-tree's direct actuator-channel adjacencies.
        # They are possible local composition sites, not action choices: the
        # graph later needs a grounded singleton consequence before it can
        # instantiate an exact two-effector bundle at one of these sites.
        for relation_ordinal, (source_group, target_group) in enumerate(
            _directed_local_effector_relations(raw_shape)
        ):
            if source_group not in affordances_by_group or target_group not in affordances_by_group:
                continue
            relation = adapter.s.add_node("EmbodiedRawEffectorTopologyRelation", {
                "relation_kind": "directed_mechanical_link_adjacency",
                "relation_ordinal": int(relation_ordinal),
                "source_group_ordinal": int(source_group),
                "target_group_ordinal": int(target_group),
                "mechanical_path_length": 1,
                "grounded": 1,
                "integer_native": 1,
                "output_authority": 0,
            })
            native.add_edge_unchecked(
                raw_body, "has_embodied_raw_effector_topology_relation", relation
            )

        # THE TREE, WITH ITS DIRECTION INTACT. The adjacency published above is
        # symmetric by construction; these edges say which channel CARRIES
        # which. Both tokens of a child group are carried by both tokens of its
        # parent group, because carriage is a fact about the mechanical link and
        # not about command polarity, which stays opaque here as everywhere else.
        for child_group, parent_group in _carried_by_effector_relations(raw_shape):
            for child in affordances_by_group.get(child_group, ()):
                for parent in affordances_by_group.get(parent_group, ()):
                    native.add_edge_unchecked(child, "carried_by", parent)

    def __call__(self, adapter, selected_source) -> None:
        """Enact *only* the supplied request and publish its measured evidence."""
        if not adapter.inner.has_node(selected_source):
            raise RuntimeError("selected embodied trial source is no longer live")
        request_node = adapter.s.node(selected_source)
        request_attrs = request_node["attrs"]
        if request_node["type"] != "EmbodiedExternalTrialRequest":
            raise RuntimeError("selected embodied trial source is not an external trial request")
        if request_attrs.get("status") != "requested":
            raise RuntimeError("selected embodied trial request is not requested")

        program = _one_neighbour(
            adapter, selected_source, "enacts_embodied_motor_program", "EmbodiedMotorProgram"
        )
        pose = _one_neighbour(
            adapter, selected_source, "uses_embodied_pose_affordance", "EmbodiedPoseAffordance"
        )
        scenario = _one_neighbour(
            adapter, selected_source, "uses_embodied_reset_scenario", "EmbodiedResetScenario"
        )
        goal = _one_neighbour(adapter, selected_source, "pursues_goal", "Goal")
        program_attrs = adapter.s.node(program)["attrs"]
        pose_attrs = adapter.s.node(pose)["attrs"]
        scenario_attrs = adapter.s.node(scenario)["attrs"]

        if _require_integer(program_attrs, "integer_native") != 1:
            raise RuntimeError("selected humanoid motor program is not integer-native")
        if _require_integer(pose_attrs, "enabled") != 1:
            raise RuntimeError("selected humanoid pose affordance is not enabled")
        tokens = _token_sequence(program_attrs.get("simulator_tokens"))
        if len(set(tokens)) != len(tokens):
            raise RuntimeError("simulator_tokens must name each opaque actuator at most once")
        weight_units = _integer_sequence(
            program_attrs.get("simulator_weight_units"), key="simulator_weight_units"
        )
        if len(tokens) != len(weight_units):
            raise RuntimeError("simulator_tokens and simulator_weight_units differ in length")
        weight_scale = _require_integer(
            program_attrs, "simulator_weight_scale_units", minimum=1
        )
        frames = _require_integer(program_attrs, "simulator_frames", minimum=1)
        displacement_scale = _require_integer(
            program_attrs, "displacement_units_per_metre", minimum=1
        )
        energy_scale = _require_integer(
            program_attrs, "energy_units_per_joule", minimum=1
        )
        load_scale = _require_integer(
            program_attrs, "load_units_per_newton", minimum=1
        )
        fixture = tuple(
            _require_integer(scenario_attrs, f"fixture_quarter_turn_{axis}")
            for axis in ("x", "y", "z")
        )

        # This is the complete world-side enactment: the scenario and opaque
        # program are graph-owned; Python does not choose or reinterpret them.
        before = self.world.reset(initial_base_quarter_turns=fixture)
        weights = {
            token: weight / weight_scale
            for token, weight in zip(tokens, weight_units)
        }
        after = self.world.step(tokens, frames=frames, weights=weights)
        before_configuration = tuple(int(value) for value in before["motor_configuration_shape"])
        after_configuration = tuple(int(value) for value in after["motor_configuration_shape"])
        if len(before_configuration) != len(after_configuration):
            raise RuntimeError("simulator changed proprioceptive configuration dimensionality")
        proprioceptive_delta = tuple(
            after_value - before_value
            for before_value, after_value in zip(before_configuration, after_configuration)
        )
        support_before = _support_topology(before)
        support_after = _support_topology(after)
        displacement = tuple(
            _quantize(
                float(after["base_position"][axis]) - float(before["base_position"][axis]),
                displacement_scale,
            )
            for axis in range(3)
        )
        # Trial order is a mechanical fact, counted exactly as the attachment
        # ordinal above is: the next integer after the retained trial records.
        # It is what lets the graph SCOPE a stream to one trial — every trial
        # begins with a reset, so samples from different trials are not one
        # trajectory and must never be projected as one.
        prior_trials = []
        for prior in adapter.s.nodes("EmbodiedExternalTrialEvidence"):
            value = adapter.s.node(prior)["attrs"].get("trial_ordinal")
            if isinstance(value, int) and not isinstance(value, bool) and value > 0:
                prior_trials.append(value)
        trial_ordinal = (max(prior_trials) if prior_trials else 0) + 1
        evidence = adapter.s.add_node("EmbodiedExternalTrialEvidence", {
            "trial_ordinal": trial_ordinal,
            "grounded": 1,
            "integer_native": 1,
            "output_authority": 0,
            "energy_cost_units": _quantize(
                max(0.0, float(after["supplied_energy_joules"])), energy_scale
            ),
            "peak_load_units": _quantize(
                max(0.0, float(after["peak_contact_force_newtons"])), load_scale
            ),
            # A trial physically observes the whole base-position vector.
            # Direction/goal scoring is deliberately deferred to graph policy;
            # this adapter must not choose one axis or repeat the same action
            # once per possible reading of that vector.
            "base_displacement_x_units": displacement[0],
            "base_displacement_y_units": displacement[1],
            "base_displacement_z_units": displacement[2],
            # Base translation is not a sufficient movement sensor: a joint
            # twitch can be real while the body's base remains still.  The
            # opaque ordered configuration delta crosses the boundary once;
            # graph policy evaluates its consequence.
            "proprioceptive_configuration_delta_units": list(proprioceptive_delta),
            "proprioceptive_configuration_observed": 1,
            # SUPPORT TOPOLOGY: which links touch the ground, before and after.
            # Published as the MEASUREMENT (the link sets and their sizes); the
            # graph decides what a change of them means, exactly as it decides
            # `development_configuration_changed` from the proprioceptive norm.
            # `support_contact_observed` is the provenance flag: it distinguishes
            # "the topology did not change" from "the topology was not read",
            # which are different facts and whose conflation is what made stage
            # 0 unsatisfiable for thirteen hours.
            "support_contact_links_before": list(support_before),
            "support_contact_links_after": list(support_after),
            "support_contact_count_before": len(support_before),
            "support_contact_count_after": len(support_after),
            "support_contact_observed": 1,
            "measurement_frame_count": frames,
            "reset_quarter_turn_x": fixture[0],
            "reset_quarter_turn_y": fixture[1],
            "reset_quarter_turn_z": fixture[2],
            "simulator_step_before": int(before["step_index"]),
            "simulator_step_after": int(after["step_index"]),
        })
        # Preserve exact provenance instead of projecting it into a Python
        # summary.  The graph can inspect the request, program, pose, scenario
        # and goal that produced this physical observation directly.
        native = adapter.inner
        native.add_edge_unchecked(
            selected_source, "has_grounded_external_trial_evidence", evidence
        )
        native.add_edge_unchecked(evidence, "evidence_for_embodied_trial_request", selected_source)
        native.add_edge_unchecked(evidence, "measures_embodied_motor_program", program)
        native.add_edge_unchecked(evidence, "under_embodied_pose_affordance", pose)
        native.add_edge_unchecked(evidence, "from_embodied_reset_scenario", scenario)
        native.add_edge_unchecked(evidence, "measures_goal", goal)

        # PUBLISH THE SENSED CHANNELS.  One observation per declared channel
        # per trial, quantized at the boundary exactly as the evidence above
        # is.  Pure transport: the adapter does not compare these to anything,
        # does not decide whether a reading is surprising, and does not touch
        # any effector's authority.  Surprise, promotion and the collapse are
        # all graph-side.
        for name, raw in (
            ("contact_force",
             _quantize(max(0.0, float(after["peak_contact_force_newtons"])), load_scale)),
            # THE VERTICAL CHANNEL CARRIES A DELTA, NOT AN ALTITUDE.  The
            # program's `predicted_vertical_units` is a predicted CHANGE in
            # height, so publishing an absolute base height here made every
            # trial report a discrepancy the size of the body's altitude —
            # fake surprise on a channel that had not moved.  `displacement[2]`
            # is the same quantity the evidence node already publishes as
            # `base_displacement_z_units`, quantized on the same scale, so the
            # observation and the expectation are finally the same quantity.
            ("base_vertical_delta", displacement[2]),
        ):
            channel = _find_channel(adapter, name)
            if channel is None:
                continue
            observation = adapter.s.add_node("ChannelObservation", {
                "channel": name,
                "value_units": raw,
                "simulator_step": int(after["step_index"]),
                "trial_ordinal": trial_ordinal,
                "grounded": 1,
                "integer_native": 1,
                "output_authority": 0,
            })
            native.add_edge_unchecked(
                channel, "has_channel_observation", observation
            )
            # Provenance only: WHICH program produced this reading. The graph
            # decides what to expect from it; the adapter predicts nothing.
            native.add_edge_unchecked(
                observation, "observed_under_motor_program", program
            )

        # PUBLISH THE APPROACH STREAM.  A projection needs a SEQUENCE, not a
        # scalar, so the trial's per-frame vertical trace crosses the boundary
        # as one observation per retained sample, oldest first, all tagged with
        # this trial's ordinal.  Sampling stride and count are declared
        # interface resolution — the same class of constant as
        # `_DISPLACEMENT_UNITS_PER_METRE` — and are NOT a choice about which
        # part of the trajectory is interesting: the samples are taken across
        # the whole trace, so a body that settled reports a settled stream and
        # a body still descending reports a descent.  The adapter still
        # compares nothing and predicts nothing.
        height_channel = _find_channel(adapter, "base_height_above_ground")
        trace = after.get("base_height_trace")
        if height_channel is not None and isinstance(trace, (tuple, list)) and trace:
            for ordinal, sample in enumerate(_stream_samples(trace)):
                observation = adapter.s.add_node("ChannelObservation", {
                    "channel": "base_height_above_ground",
                    "value_units": _quantize(float(sample), displacement_scale),
                    "simulator_step": int(after["step_index"]),
                    "trial_ordinal": trial_ordinal,
                    "stream_ordinal": int(ordinal),
                    "grounded": 1,
                    "integer_native": 1,
                    "output_authority": 0,
                })
                native.add_edge_unchecked(
                    height_channel, "has_channel_observation", observation
                )
                native.add_edge_unchecked(
                    observation, "observed_under_motor_program", program
                )


__all__ = ["PyBulletHumanoidTrialTransducer"]
