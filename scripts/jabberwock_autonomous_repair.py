"""AUTONOMOUS, GATED self-repair — the jabberwock detects its OWN regression, repairs, and keeps-or-reverts.

The three polish faculties (seeds/self_repair.json) close the loop with NO hand-ingested Fault and NO Python
decision: a regression on a repairable CapabilityAxis auto-mints a Fault; a graph rule rewrites the named
live rule via set_rule_clause (snapshotting off the axis shadow); an effect-gate keeps or reverts on the next
post-repair measure.

  KEEP path (on the REAL discriminator): break classify_axis_compensated -> bank a regression measure ->
    fault_detect_regression auto-mints a Fault carrying the gate-and-hold clause -> repair_apply rewrites the
    discriminator -> the avatar's self-id now survives committed action -> a good post-repair measure -> the
    gate KEEPS.
  REVERT path (synthetic): a bad repair_clause that doesn't lift the measure -> the gate REVERTS to the
    snapshot, restoring the original rule.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_autonomous_repair.py
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import gen_action_corr_seed as GEN
from stage2_phi_world import AvatarDeathEnv4, AV
from worlds.arc import ArcWorld
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds

DISC = "classify_axis_compensated"


def clauses():
    cr = GEN.classify_rule()
    corrected = cr["effects"]                              # gate-and-hold (the fix)
    kind = corrected[0][3]["__term__"]["other"]           # ungated classification (the bug)
    broken = [["set_attr", "r", "axis_kind", {"__term__": kind}]]
    return corrected, broken


def settle(agent, n=4):
    for _ in range(n):
        agent.master_tick(); agent.tick()


def install_clause(agent, target, field, clause):
    """Mechanical: set a rule's clause once via the repair faculty (used here only to BREAK the discriminator
    for the demo — the agent's autonomous loop does the real repair)."""
    f = agent.s.add_node("Fault", {"target_rule": target, "field": field, "corrected": clause, "applied": 0.0})
    agent.inner.add_edge_unchecked(agent.agent, "has_fault", f)
    settle(agent)


def bank(agent, ax, measured, post_repair=0.0):
    """Bank a capability measure onto an axis (drives the investigation_loop bank rule -> saturation)."""
    mc = agent.s.add_node("MeasuredCapability", {"measured": float(measured), "target": 1.0,
                                                 "metric": "self_id_stability", "post_repair": float(post_repair)})
    agent.inner.add_edge_unchecked(mc, "measures_axis", ax)
    settle(agent)
    return mc


def avatar_kind(agent):
    best, best_f = None, -1.0
    for n in agent.s.nodes("Region"):
        x = agent.s.node(n)["attrs"]
        if x.get("is_ground") != 1.0 and int(x.get("rvalue") or 0) == AV:
            cf = float(x.get("changed_frame") or 0)
            if cf >= best_f:
                best, best_f = x.get("axis_kind"), cf
    return best


def self_persists(agent, world):
    sub, ctx = world.reset(); agent.perceive_frame(sub)
    for i in range(28):
        sub, ctx = world.apply((["Up", "Down", "Left", "Right"][i % 4],))
        agent.perceive_frame(sub); agent.master_tick(); agent.tick()
    est = avatar_kind(agent) == "controllable"
    held = True
    for _ in range(8):
        sub, ctx = world.apply(("Right",))
        agent.perceive_frame(sub); agent.master_tick(); agent.tick()
        held = held and (avatar_kind(agent) == "controllable")
    return est, held


def main():
    print("=" * 96)
    print("AUTONOMOUS GATED SELF-REPAIR — the jabberwock detects its own regression and repairs itself.")
    print("=" * 96)
    corrected, broken = clauses()
    agent = WorldAdapter(seeds=()); load_all_seeds(agent)
    world = ArcWorld(AvatarDeathEnv4())

    # --- KEEP path on the real discriminator -----------------------------------------------------------
    def disc_fault():
        fs = [f for f in agent.s.nodes("Fault")
              if agent.s.node(f)["attrs"].get("target_rule") == DISC
              and agent.s.node(f)["attrs"].get("from_sat") is not None]
        return agent.s.node(fs[0])["attrs"] if fs else None

    print("\n  break the discriminator (ungated), then let the agent NOTICE + repair it autonomously...")
    install_clause(agent, DISC, "effect", broken)
    _, held_broken = self_persists(agent, world)

    ax = agent.s.add_node("CapabilityAxis", {
        "is_axis": 1.0, "repairable": 1.0, "repair_rule": DISC, "repair_field": "effect",
        "repair_clause": corrected, "live_clause": broken,
        "saturation": 1.0, "sat_best": 1.0, "target": 1.0, "fault_open": 0.0})
    bank(agent, ax, 0.2)                          # a regression measure -> fault_detect should auto-fire
    fa = disc_fault()
    minted = fa is not None
    applied = minted and fa.get("applied") == 1.0
    bank(agent, ax, 1.0, post_repair=1.0)        # a good post-repair measure -> the gate should KEEP
    fa = disc_fault()
    outcome = fa.get("outcome") if fa else None
    fopen = agent.s.node(ax)["attrs"].get("fault_open")
    print(f"      regression banked -> fault auto-minted: {minted}; repair auto-applied: {applied}")
    print(f"      gate outcome on good post-repair measure: {outcome!r}; fault_open cleared: {fopen == 0.0}")
    _, held_fixed = self_persists(agent, world)   # behaviour after the autonomous repair
    print(f"      self dissolves while broken: {not held_broken}; persists after autonomous repair: {held_fixed}")
    keep_ok = (not held_broken) and minted and applied and held_fixed and outcome == "kept"

    # --- REVERT path (synthetic): a bad fix that doesn't lift -> the gate rolls it back -----------------
    print("\n  REVERT branch: a repair that does NOT lift the measure is rolled back to the snapshot...")
    g = agent.s.add_node("Anchor", {}); pr = agent.s.add_node("Probe", {})
    agent.inner.add_edge_unchecked(g, "has_probe", pr)
    good = [["set_attr", "p", "out", {"__term__": {"type": "Lit", "value": "good"}}]]
    bad = [["set_attr", "p", "out", {"__term__": {"type": "Lit", "value": "bad"}}]]
    agent.inner.add_rule({"name": "R_probe", "match": [["g", "has_probe", "p"]],
                          "where": {"type": "Lit", "value": True}, "effects": good})
    settle(agent)
    ax2 = agent.s.add_node("CapabilityAxis", {
        "is_axis": 1.0, "repairable": 1.0, "repair_rule": "R_probe", "repair_field": "effect",
        "repair_clause": bad, "live_clause": good,
        "saturation": 1.0, "sat_best": 1.0, "target": 1.0, "fault_open": 0.0})
    bank(agent, ax2, 0.2)                         # regress -> detect -> repair installs the BAD clause
    f2 = [f for f in agent.s.nodes("Fault")
          if agent.s.node(f)["attrs"].get("target_rule") == "R_probe"]
    bank(agent, ax2, 0.2, post_repair=1.0)       # post-repair measure still low -> gate must REVERT
    agent.inner.set_attr(pr, "out", None); settle(agent)
    out_after = agent.s.node(pr)["attrs"].get("out")
    outcome2 = agent.s.node(f2[0])["attrs"].get("outcome") if f2 else None
    print(f"      bad fix installed then gate outcome: {outcome2!r}; probe restored to original: {out_after == 'good'}")
    revert_ok = outcome2 == "reverted" and out_after == "good"

    ok = keep_ok and revert_ok
    print("\n" + "=" * 96)
    print(f"  {'PASS' if ok else 'FAIL'} — the agent autonomously DETECTED a regression (no hand-ingested "
          f"Fault), repaired the named rule via set_rule_clause, and the effect-gate KEPT a fix that lifted "
          f"the measure and REVERTED one that didn't. Self-originated, gated, graph-native — regress -> "
          f"detect -> repair -> keep/revert.")
    print("=" * 96)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
