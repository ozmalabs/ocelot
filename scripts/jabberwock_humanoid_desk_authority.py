#!/usr/bin/env python3
"""THE DESK GATE — does the SAME rule set release the hand or drive through it,
with only the goal changed?

EFFECTOR_AUTHORITY_COLLAPSE_PREREG.md gate 1 (Desk), gate 3 (not zero), gate 4
(no scalar). Registered before this file existed.

The loop is: measure both authority allocations physically -> publish each as a
Pareto candidate with FOUR SEPARATE AXES -> let relational dominance prune,
goal-blind -> let the goal choose which single axis is read -> read back which
regime was adopted. The physics is identical across the two goals. Only
`goal_instrument_group_ordinal` differs, and it is a property of the goal, not
of the arm.

What is NOT here, deliberately: any read of "did a collision occur". The axes
are shortfalls against declared authority, meaningful with no desk in the world.
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
from substrate.world_adapter import WorldAdapter                # noqa: E402
from substrate.seed_loader import manifest_for                  # noqa: E402

ABDOMEN_Z = 0
RIGHT_ARM_JOINTS = (23, 24, 26)
TURN_TARGET = 0.70
DESK_XYZ, DESK_HALF = (0.30, -0.28, 1.20), (0.14, 0.10, 0.08)

# Declared authority, in the same units the transducer publishes (the body's own
# configuration, not a constant invented here).
DECLARED_TURN_AUTHORITY = 700     # milliradians of commanded torso displacement
DECLARED_ARM_AUTHORITY = 700      # the arm may be asked for as much
TORSO_GROUP, ARM_GROUP = 0, 1


def trial(arm_authority_units, *, desk=True, frames=600):
    """One physical trial at a given ARM AUTHORITY. Returns measured axes."""
    cfg = HumanoidBodyConfiguration(
        time_step=1 / 240, gravity_acceleration=9.81, action_frames=24,
        settling_frames=480, joint_twitch_radians=0.15,
        maximum_joint_force=100.0, position_gain=0.3, velocity_gain=1.0)
    w = PyBulletHumanoidWorld(cfg, seed=0)
    cid, body = w._client, w._body
    if desk:
        shape = p.createCollisionShape(p.GEOM_BOX, halfExtents=list(DESK_HALF),
                                       physicsClientId=cid)
        obstacle = p.createMultiBody(baseMass=0.0, baseCollisionShapeIndex=shape,
                                     basePosition=list(DESK_XYZ),
                                     physicsClientId=cid)
    else:
        obstacle = None
    hold = {j: p.getJointState(body, j, physicsClientId=cid)[0]
            for j in RIGHT_ARM_JOINTS}
    arm_force = arm_authority_units / 10.0        # units -> newtons at the boundary
    peak = 0.0
    for f in range(frames):
        frac = min(1.0, f / (frames * 0.5))
        p.setJointMotorControl2(body, ABDOMEN_Z, p.POSITION_CONTROL,
                                targetPosition=TURN_TARGET * frac, force=150.0,
                                positionGain=0.4, physicsClientId=cid)
        for j, tgt in hold.items():
            p.setJointMotorControl2(body, j, p.POSITION_CONTROL,
                                    targetPosition=tgt, force=arm_force,
                                    positionGain=0.4, physicsClientId=cid)
        p.stepSimulation(physicsClientId=cid)
        if obstacle is not None:
            pts = p.getContactPoints(bodyA=body, bodyB=obstacle,
                                     physicsClientId=cid)
            if pts:
                peak = max(peak, max(float(c[9]) for c in pts))
    yaw = p.getJointState(body, ABDOMEN_Z, physicsClientId=cid)[0]
    arm_dev = max(abs(p.getJointState(body, j, physicsClientId=cid)[0] - hold[j])
                  for j in RIGHT_ARM_JOINTS)
    base_z = p.getBasePositionAndOrientation(body, physicsClientId=cid)[0][2]
    w.close()

    return {
        "turn_achieved": int(round(yaw * 1000)),
        "arm_held": int(round((1.0 - min(1.0, arm_dev / 1.0))
                              * DECLARED_ARM_AUTHORITY)),
        "peak": int(round(peak)),
        "base_z": int(round(base_z * 1000)),
        "raw": {"yaw": round(yaw, 3), "arm_dev": round(arm_dev, 3),
                "peak_N": round(peak, 1), "base_z": round(base_z, 3)},
    }


def axes(measured, *, demanded_turn, demanded_reach):
    """SHORTFALL AGAINST WHAT WAS DEMANDED, signed so higher is better.

    A shortfall presupposes a demand. Scoring "the arm stayed where it was" as an
    achievement when the goal never asked the arm for anything asserts an
    objective that does not exist -- and it is what let the option that throws
    the body to the floor survive dominance on the first run of this gate, by
    being perfect at something nobody wanted.

    DEMAND IS NOT PRIORITY, and only priority is goal-blind-forbidden. Dominance
    stays blind to which axis will be READ; it cannot be blind to what was
    ASKED, because an unasked objective is not an objective. The F-16 evaluates
    its corners against the current reference for the same reason.
    """
    return {
        0: -max(0, demanded_turn - measured["turn_achieved"]),
        1: -max(0, demanded_reach - measured["arm_held"]),
        2: -measured["peak"],
        3: measured["base_z"],
        "raw": measured["raw"],
    }


def decide(axes_by_candidate, goal_instrument_group):
    """Publish the candidates and let the GRAPH choose. No Python decision."""
    a = WorldAdapter()
    for seed in ("cognitive_pareto", "effector_authority_axis"):
        a.inner.load_seed_manifest(manifest_for(seed), a.agent)
    E = a.inner.add_edge_unchecked
    profile = a.s.add_node("ParetoProfile", {
        "dimension_count": 4, "arm_group_ordinal": ARM_GROUP,
        "status": "open", "integer_native": 1})
    E(a.agent, "has_effector_authority_profile", profile)
    goal = a.s.add_node("Goal", {
        "goal_instrument_group_ordinal": goal_instrument_group,
        "integer_native": 1})
    E(profile, "deliberates_for_goal", goal)
    for identity, axes in axes_by_candidate.items():
        cand = a.s.add_node("ParetoCandidate", {
            "identity": identity, "dominated": 0, "verified": 1,
            "arm_authority_units": axes["arm_authority_units"],
            "integer_native": 1})
        E(profile, "has_pareto_candidate", cand)
        for ordinal in range(4):
            pv = a.s.add_node("ParetoValue", {
                "dimension_ordinal": ordinal, "signed_value": axes[ordinal],
                "verified": 1, "integer_native": 1})
            E(cand, "has_pareto_value", pv)
    a.inner.run_rules()
    attrs = a.s.node(profile)["attrs"]
    dominated = {a.s.node(c)["attrs"]["identity"]: a.s.node(c)["attrs"].get("dominated")
                 for c in a.inner.neighbours(profile, "has_pareto_candidate")}
    return attrs.get("adopted_regime"), attrs.get("priority_axis_ordinal"), dominated


GOALS = (
    # label, instrument group, demanded turn, demanded reach
    ("turn", TORSO_GROUP, DECLARED_TURN_AUTHORITY, 0),
    ("reach_through", ARM_GROUP, 0, DECLARED_ARM_AUTHORITY),
)


def main() -> int:
    print("=== physical trials (identical physics, two authority allocations) ===")
    measured = {"hold_arm": trial(1200), "yield_arm": trial(20)}
    authority = {"hold_arm": 1200, "yield_arm": 20}
    for name, m in measured.items():
        print(f"  {name:10s} {m['raw']}")

    print("\n=== the graph decides — ONLY the goal differs ===")
    report = {}
    for label, group, dturn, dreach in GOALS:
        candidates = {}
        for name, m in measured.items():
            a = axes(m, demanded_turn=dturn, demanded_reach=dreach)
            a["arm_authority_units"] = authority[name]
            candidates[name] = a
        regime, axis, dominated = decide(candidates, group)
        print(f"  goal={label:14s} demand(turn={dturn},reach={dreach}) "
              f"priority_axis={axis}  adopted={regime!r}")
        for name, a in candidates.items():
            print(f"      {name:10s} axes=({a[0]},{a[1]},{a[2]},{a[3]}) "
                  f"dominated={dominated[name]}")
        report[label] = {
            "adopted": regime, "priority_axis": axis, "dominated": dominated,
            "axes": {n: {str(i): a[i] for i in range(4)}
                     for n, a in candidates.items()},
        }

    out = ROOT / "results" / "desk_authority_gate.json"
    out.write_text(json.dumps(
        {"measured": {k: v["raw"] for k, v in measured.items()},
         "decisions": report}, indent=1) + "\n", encoding="utf-8")
    print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
