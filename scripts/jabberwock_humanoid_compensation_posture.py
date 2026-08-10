#!/usr/bin/env python3
"""THE POSTURE GATE — does spending travel BEFORE the event change what arrives?

`EFFECTOR_COMPENSATION_PREREG.md` gates 1, 2 and 7, measured on the live body.

WHY NOT THE DESK. The desk gate's two candidates differ in commanded FORCE and
share a pose, so they share their travel headroom exactly — the compensation
axis is constant across them and cannot discriminate. That is a property of the
instrument, not of the axis. The contrast this axis answers to is POSTURAL:
identical goal, identical declared force, different travel in hand.

Which is also why this is the walking case. Standing cheaply on a joint at its
stop and absorbing a footfall on one with travel in hand are the same knob at
two settings, so the landing is where the knob shows.

NOTHING HERE NAMES A JOINT. The braced set is found by ASKING THE BOUNDARY which
tokens publish zero headroom, and flexing those. On this body that finds the
knee pair; on another body it would find whatever that body stands on. A joint
name anywhere below would make the result about this asset.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from domains.engine_provenance import engine_preamble           # noqa: E402
engine_preamble()

import pybullet as p                                            # noqa: E402
from domains.pybullet_humanoid_world import (                   # noqa: E402
    HumanoidBodyConfiguration, PyBulletHumanoidWorld)
from substrate.seed_loader import manifest_for                  # noqa: E402
from substrate.world_adapter import WorldAdapter                # noqa: E402

ANGLE_UNITS_PER_RADIAN = 1000
TORQUE_UNITS_PER_NEWTON_METRE = 1000
DECLARED_CHANGE = 1000

# The declared drop: how far clear of the ground the body is released, in
# metres. Identical for both conditions and measured from the body's own lowest
# point, so a shorter posture does not fall a shorter distance.
DROP_CLEARANCE = 0.12
HOLD_FORCE = 100.0
FRAMES = 400

# Axis ordinals. Signed so higher is always better, as `ParetoDominates` needs.
#
# The ordinals are NOT arbitrary: `eaa_choose_priority_axis_from_goal` (the desk
# seed, unmodified) reads axis 1 when the goal's instrument matches the
# profile's declared group and axis 0 otherwise. So a goal that declares itself
# about the loaded group prioritises DAMAGE, and any other goal prioritises
# POSTURE. That is the whole of the goal's entry into this, and it is the same
# two-stage separation the desk gate holds: dominance first and goal-blind, then
# one declared axis read off the survivors.
AXIS_POSTURE = 0        # +retained base height
AXIS_DAMAGE = 1         # -peak support load
# COMPENSATION IS NEVER A PRIORITY AXIS. Reserve is not an objective — no goal
# asks for travel in hand. It enters dominance only, where it can rescue a
# candidate that is otherwise tied, and is never read as the thing being
# maximised.
AXIS_COMPENSATION = 2   # +travel still in hand at the moment of the decision
DIMENSION_COUNT = 3

# Travel SPENT before the event, in radians, on whichever joints the boundary
# reports standing against a stop. A sweep rather than a pair: with two points
# a lower peak and a lost posture are inseparable, and the question this gate
# exists to answer is whether the peak falls BEFORE the posture does.
FLEX_SWEEP = (0.0, 0.05, 0.10, 0.20, 0.30, 0.45, 0.60)


def _config():
    return HumanoidBodyConfiguration(
        time_step=1 / 240, gravity_acceleration=9.81, action_frames=24,
        settling_frames=480, joint_twitch_radians=0.15,
        maximum_joint_force=HOLD_FORCE, position_gain=0.3, velocity_gain=1.0)


def braced_groups(world):
    """Ask the BOUNDARY which joints are standing against a stop.

    Zero headroom in some command direction. No name, no ordinal chosen by
    hand — whatever this body happens to stand on.

    QUANTISED FIRST, and this is not a detail: the raw float headroom of a joint
    resting on its stop is a few parts in 1e17, not 0.0, so an exact float
    comparison finds NOTHING and every condition below silently becomes the
    same trial. Zero means zero at the declared resolution the graph actually
    reads — the same `round(x * ANGLE_UNITS_PER_RADIAN)` the transducer
    publishes through.
    """
    groups = set()
    for option in world.actuator_options():
        headroom = option.get("command_direction_travel_headroom")
        if headroom is None:
            continue
        if round(headroom * ANGLE_UNITS_PER_RADIAN) == 0:
            groups.add(int(option["actuator_group"]))
    return tuple(sorted(groups))


def group_headroom_units(world, groups):
    """Travel in hand on `groups`: the smallest headroom any of their tokens
    still publishes. Standing on a stop reads 0; flexed away from it reads how
    far it moved."""
    if not groups:
        return 0
    return min(
        round(option["command_direction_travel_headroom"]
              * ANGLE_UNITS_PER_RADIAN)
        for option in world.actuator_options()
        if option.get("command_direction_travel_headroom") is not None
        and int(option["actuator_group"]) in groups
    )


def _lowest_point(body, cid):
    return min(
        float(p.getAABB(body, link, physicsClientId=cid)[0][2])
        for link in range(-1, p.getNumJoints(body, physicsClientId=cid))
    )


def trial(flex_radians):
    """One drop. `flex_radians` is travel SPENT before the event, in the
    direction that has headroom, on the joints found to be at a stop."""
    world = PyBulletHumanoidWorld(_config(), seed=0)
    cid, body = world._client, world._body
    groups = braced_groups(world)

    # Spend the headroom. The direction with travel in hand is the one whose
    # limit is further from where the joint stands; read from the joint's own
    # declared bounds, never from a name.
    for group in groups:
        lower, upper, position = world._travel_bounds(group)
        index = world._joint_indices[group]
        target = (position - flex_radians
                  if (position - lower) > (upper - position)
                  else position + flex_radians)
        target = min(upper, max(lower, target))
        p.resetJointState(body, index, targetValue=target,
                          targetVelocity=0.0, physicsClientId=cid)

    # Release from the SAME clearance in both conditions, measured from the
    # body's own lowest point so a shorter posture does not fall less far.
    p.performCollisionDetection(physicsClientId=cid)
    position_xyz, orientation = p.getBasePositionAndOrientation(
        body, physicsClientId=cid)
    lowest = _lowest_point(body, cid)
    p.resetBasePositionAndOrientation(
        body,
        (float(position_xyz[0]), float(position_xyz[1]),
         float(position_xyz[2]) - lowest + DROP_CLEARANCE),
        orientation, physicsClientId=cid)
    p.resetBaseVelocity(body, linearVelocity=(0.0, 0.0, 0.0),
                        angularVelocity=(0.0, 0.0, 0.0), physicsClientId=cid)

    # Capacity is read AT THE MOMENT OF THE DECISION — before the event, which
    # is the only time a decision could use it.
    capacity_units = group_headroom_units(world, groups)

    hold = {index: p.getJointState(body, index, physicsClientId=cid)[0]
            for index in world._joint_indices}
    peak = 0.0
    for _ in range(FRAMES):
        for index, target in hold.items():
            p.setJointMotorControl2(
                body, index, p.POSITION_CONTROL, targetPosition=target,
                force=HOLD_FORCE, positionGain=0.4, physicsClientId=cid)
        p.stepSimulation(physicsClientId=cid)
        contacts = p.getContactPoints(bodyA=body, physicsClientId=cid)
        if contacts:
            peak = max(peak, sum(float(c[9]) for c in contacts))
    base_z = p.getBasePositionAndOrientation(body, physicsClientId=cid)[0][2]
    world.close()
    return {
        "flex_radians": round(flex_radians, 3),
        "braced_groups": list(groups),
        "capacity_units": int(capacity_units),
        "peak_N": round(peak, 1),
        "base_z": round(base_z, 3),
        "peak": int(round(peak)),
        "base_z_units": int(round(base_z * 1000)),
    }


def derived_readings():
    """Gates 1 and 2 on the LIVE body: what the graph derives from the standing
    boundary, through the seeded rules, with nothing hand-fed."""
    world = PyBulletHumanoidWorld(_config(), seed=0)
    adapter = WorldAdapter()
    for seed in ("effector_compensation", "effector_limbs"):
        adapter.inner.load_seed_manifest(manifest_for(seed), adapter.agent)
    body = adapter.s.add_node("EmbodiedRawBody", {
        "grounded": 1, "integer_native": 1, "output_authority": 0})
    nodes = {}
    for ordinal, option in enumerate(world.actuator_options()):
        attrs = {
            "opaque_token": option["token"],
            "opaque_group_ordinal": int(option["actuator_group"]),
            "specified_maximum_position_change_per_action": (
                round(option["declared_position_change"] * 1000)),
            "specified_maximum_position_change_per_action_measured": 0,
            # THE PER-ACTUATOR AUTHORITY, mirroring the transducer's bind. The
            # settle's `min` chain reads this; without it nothing fires at all.
            "declared_joint_force_units": round(
                option["declared_joint_force"]),
            "declared_joint_force_units_measured": 0,
            "available": 1, "grounded": 1, "integer_native": 1,
            "output_authority": 0,
        }
        span = option.get("declared_travel_span")
        headroom = option.get("command_direction_travel_headroom")
        if span is not None:
            attrs["declared_joint_travel_span_units"] = round(
                span * ANGLE_UNITS_PER_RADIAN)
            attrs["declared_joint_travel_span_units_measured"] = 0
        if headroom is not None:
            attrs["command_direction_travel_headroom_units"] = round(
                headroom * ANGLE_UNITS_PER_RADIAN)
            attrs["command_direction_travel_headroom_units_measured"] = 1
        load = option.get("command_direction_load")
        if load is not None:
            attrs["command_direction_load_units"] = round(
                load * TORQUE_UNITS_PER_NEWTON_METRE)
            attrs["command_direction_load_units_measured"] = 0
            attrs["command_direction_load_units_inferred"] = 1
        node = adapter.s.add_node("EmbodiedOpaqueActuatorAffordance", attrs)
        adapter.inner.add_edge_unchecked(
            body, "has_opaque_embodied_actuator_affordance", node)
        nodes[ordinal] = node
    adapter.inner.run_rules()

    readings = []
    for ordinal, node in nodes.items():
        attrs = adapter.s.node(node)["attrs"]
        readings.append({
            "ordinal": ordinal,
            "group": attrs.get("opaque_group_ordinal"),
            "alignment": attrs.get("structural_alignment_authority_units"),
            "capacity": attrs.get("plastic_compensation_capacity_units"),
            "load": attrs.get("command_direction_load_units"),
            "bearing_load": attrs.get("bearing_load"),
            "loaded_alignment": attrs.get(
                "loaded_structural_alignment_authority_units"),
            "loaded_capacity": attrs.get(
                "loaded_compensation_capacity_units"),
        })
    world.close()
    return readings


def settle_readings():
    """RE-MEASURE THE SETTLE on the live body, with real carriage chains.

    `elb_settle_effective_authority_over_reaction_paths` v1.2.0 reads the LOADED
    alignment, not the capability one. This builds the standing body exactly as
    the transducer's bind does — every affordance, every published channel, and
    the directed `carried_by` tree — then runs the limb seed over it and reads
    each member's effective authority back.

    The three cases that matter are all present in one pose without staging any
    of them: members at a stop bearing load, members at a stop bearing nothing,
    and members with travel in hand.
    """
    from domains.pybullet_humanoid_trial_transducer import (
        _carried_by_effector_relations)

    world = PyBulletHumanoidWorld(_config(), seed=0)
    adapter = WorldAdapter()
    for seed in ("effector_compensation", "effector_limbs"):
        adapter.inner.load_seed_manifest(manifest_for(seed), adapter.agent)
    body = adapter.s.add_node("EmbodiedRawBody", {
        "grounded": 1, "integer_native": 1, "output_authority": 0})

    by_group: dict[int, list] = {}
    nodes = []
    for option in world.actuator_options():
        group = int(option["actuator_group"])
        attrs = {
            "opaque_token": option["token"],
            "opaque_group_ordinal": group,
            "specified_maximum_position_change_per_action": (
                round(option["declared_position_change"] * 1000)),
            "specified_maximum_position_change_per_action_measured": 0,
            # THE PER-ACTUATOR AUTHORITY, mirroring the transducer's bind. The
            # settle's `min` chain reads this; without it nothing fires at all.
            "declared_joint_force_units": round(
                option["declared_joint_force"]),
            "declared_joint_force_units_measured": 0,
            "available": 1, "grounded": 1, "integer_native": 1,
            "output_authority": 0,
        }
        for key, scale, source in (
            ("declared_joint_travel_span_units", ANGLE_UNITS_PER_RADIAN,
             "declared_travel_span"),
            ("command_direction_travel_headroom_units",
             ANGLE_UNITS_PER_RADIAN, "command_direction_travel_headroom"),
            ("command_direction_load_units", TORQUE_UNITS_PER_NEWTON_METRE,
             "command_direction_load"),
        ):
            value = option.get(source)
            if value is not None:
                attrs[key] = round(value * scale)
        node = adapter.s.add_node("EmbodiedOpaqueActuatorAffordance", attrs)
        adapter.inner.add_edge_unchecked(
            body, "has_opaque_embodied_actuator_affordance", node)
        nodes.append((group, node))
        if group >= 0:
            by_group.setdefault(group, []).append(node)

    # THE TREE, exactly as the transducer publishes it.
    raw_shape = [list(row) for row in world.body_shape_signature()]
    for child_group, parent_group in _carried_by_effector_relations(raw_shape):
        for child in by_group.get(child_group, ()):
            for parent in by_group.get(parent_group, ()):
                adapter.inner.add_edge_unchecked(child, "carried_by", parent)
    adapter.inner.run_rules()

    limbs = adapter.s.nodes("EmbodiedLimb")
    rows = []
    for group, node in nodes:
        attrs = adapter.s.node(node)["attrs"]
        rows.append({
            "group": group,
            "depth": attrs.get("limb_chain_depth"),
            "headroom": attrs.get("command_direction_travel_headroom_units"),
            "load": attrs.get("command_direction_load_units"),
            "capability_alignment": attrs.get(
                "structural_alignment_authority_units"),
            "loaded_alignment": attrs.get(
                "loaded_structural_alignment_authority_units"),
            "carrier_path": attrs.get("carrier_path_authority_units"),
            "effective": attrs.get("effective_authority_units"),
        })
    world.close()
    return len(limbs), rows


def decide(candidates, *, goal_instrument_group, loaded_group):
    """Publish the candidates and let the GRAPH choose. No Python decision."""
    adapter = WorldAdapter()
    for seed in ("cognitive_pareto", "effector_authority_axis"):
        adapter.inner.load_seed_manifest(manifest_for(seed), adapter.agent)
    edge = adapter.inner.add_edge_unchecked
    profile = adapter.s.add_node("ParetoProfile", {
        "dimension_count": DIMENSION_COUNT,
        "arm_group_ordinal": loaded_group,
        "status": "open", "integer_native": 1})
    edge(adapter.agent, "has_effector_authority_profile", profile)
    goal = adapter.s.add_node("Goal", {
        "goal_instrument_group_ordinal": goal_instrument_group,
        "integer_native": 1})
    edge(profile, "deliberates_for_goal", goal)
    for identity, axes in candidates.items():
        candidate = adapter.s.add_node("ParetoCandidate", {
            "identity": identity, "dominated": 0, "verified": 1,
            "integer_native": 1})
        edge(profile, "has_pareto_candidate", candidate)
        for ordinal in range(DIMENSION_COUNT):
            value = adapter.s.add_node("ParetoValue", {
                "dimension_ordinal": ordinal, "signed_value": axes[ordinal],
                "verified": 1, "integer_native": 1})
            edge(candidate, "has_pareto_value", value)
    adapter.inner.run_rules()
    attrs = adapter.s.node(profile)["attrs"]
    dominated = {
        adapter.s.node(c)["attrs"]["identity"]:
            adapter.s.node(c)["attrs"].get("dominated")
        for c in adapter.inner.neighbours(profile, "has_pareto_candidate")
    }
    return (attrs.get("adopted_regime"),
            attrs.get("priority_axis_ordinal"), dominated)


def main() -> int:
    print("=== what the graph DERIVES from the standing boundary ===")
    readings = derived_readings()
    at_stop = [r for r in readings if r["capacity"] == 0]
    print(f"  tokens deriving both readings : "
          f"{sum(1 for r in readings if r['alignment'] is not None)}"
          f" of {len(readings)}")
    print(f"  tokens at a stop (capacity 0)  : "
          f"{[r['group'] for r in at_stop]}")
    for reading in at_stop:
        print(f"      group {reading['group']:>2}  alignment="
              f"{reading['alignment']}  capacity={reading['capacity']}")

    print("\n=== the settle, re-measured on real carriage chains ===")
    limb_count, settle = settle_readings()
    members = [r for r in settle if r["depth"] is not None]
    orphans = [r for r in members if r["effective"] is None]
    reached = [r for r in members if r["loaded_alignment"] is not None]
    print(f"  limbs={limb_count}  members={len(members)} of {len(settle)} tokens")
    print(f"  members whose loaded alignment reached the settle : "
          f"{len(reached)}")
    print(f"  members with a depth but NO effective authority    : "
          f"{len(orphans)}")
    groups = sorted({r['group'] for r in settle if r['group'] >= 0})
    member_groups = sorted({r['group'] for r in members})
    print(f"  groups in NO carriage chain                        : "
          f"{[g for g in groups if g not in member_groups]}")
    effective = sorted({r['effective'] for r in members
                        if r['effective'] is not None})
    print(f"  distinct effective authorities across all members  : {effective}")

    print("\n=== flex sweep (identical clearance, identical hold force) ===")
    print(f"  {'flex':>5} {'capacity':>9} {'peak N':>10} {'base z':>8}")
    sweep = [trial(flex) for flex in FLEX_SWEEP]
    for row in sweep:
        print(f"  {row['flex_radians']:>5} {row['capacity_units']:>9} "
              f"{row['peak_N']:>10} {row['base_z']:>8}")

    # THE TWO CANDIDATES ARE READ OFF THE SWEEP, NOT CHOSEN BY HAND: the
    # standing posture, and the largest flex that still holds the body up
    # (base height within a tenth of standing). If no flex holds, that IS the
    # finding and the comparison is reported as confounded rather than made.
    standing = sweep[0]
    upright = [row for row in sweep[1:]
               if row["base_z"] >= standing["base_z"] - 0.10]
    confounded = not upright
    compliant = (upright[-1] if upright else sweep[-1])

    print(f"\n  standing base z = {standing['base_z']}; "
          f"flexes still upright = "
          f"{[r['flex_radians'] for r in upright] or 'NONE'}")
    if confounded:
        print("  CONFOUNDED: no flex holds the body up, so a lower peak "
              "cannot be attributed to absorption rather than collapse.")

    measured = {"braced": standing, "compliant": compliant}
    candidates = {
        name: {
            AXIS_POSTURE: row["base_z_units"],
            AXIS_DAMAGE: -row["peak"],
            AXIS_COMPENSATION: row["capacity_units"],
        }
        for name, row in measured.items()
    }

    print("\n=== the graph decides — ONLY the goal differs ===")
    loaded_group = (standing["braced_groups"] or [-1])[0]
    decisions = {}
    for label, instrument in (("stay_upright", loaded_group + 1),
                              ("limit_transmitted_load", loaded_group)):
        adopted, axis, dominated = decide(
            candidates, goal_instrument_group=instrument,
            loaded_group=loaded_group)
        decisions[label] = {"adopted": adopted, "priority_axis": axis,
                            "dominated": dominated}
        print(f"  goal={label:22s} priority_axis={axis}  adopted={adopted!r}")
        for name, axes in candidates.items():
            print(f"      {name:10s} axes=("
                  f"{axes[AXIS_POSTURE]},{axes[AXIS_DAMAGE]},"
                  f"{axes[AXIS_COMPENSATION]})  dominated={dominated[name]}")

    out = ROOT / "results" / "compensation_posture_gate.json"
    out.write_text(json.dumps({
        "derived": readings,
        "settle": {"limbs": limb_count, "members": settle},
        "sweep": sweep,
        "confounded": confounded,
        "candidates": {n: {str(k): v for k, v in a.items()}
                       for n, a in candidates.items()},
        "decisions": decisions,
    }, indent=1) + "\n", encoding="utf-8")
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
