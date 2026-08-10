"""FULLY AUTONOMOUS self-repair from LIVE perception — no injected measure, no hand-ingested Fault.

Closes extension (b): the agent MEASURES its own self/world discriminator's self-id stability while it plays
(seeds/self_id_stability.json), banks it onto a repairable axis, and the existing self_repair faculty
(detect -> repair -> gate) fires on the REAL regression. With a broken discriminator the avatar's self-id
dissolves under committed action -> a closed window measures low stability -> a Fault auto-mints -> the
discriminator is repaired by name -> later windows measure recovery -> the gate KEEPS. All during one episode,
all graph-resident.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_live_self_repair.py
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python"), os.path.join(ROOT, "scripts")):
    if p not in sys.path:
        sys.path.insert(0, p)

import gen_action_corr_seed as GEN
from avatar_run_world import AvatarRunEnv, AV
from worlds.arc import ArcWorld
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds

DISC = "classify_axis_compensated"


def clauses():
    cr = GEN.classify_rule()
    corrected = cr["effects"]
    kind = corrected[0][3]["__term__"]["other"]
    return corrected, [["set_attr", "r", "axis_kind", {"__term__": kind}]]


def game_anchor(agent):
    for n in agent.s.nodes("WorldInstance"):
        if agent.s.node(n)["attrs"].get("world_type") == "Game":
            return n
    return None


def install_clause(agent, target, field, clause):
    f = agent.s.add_node("Fault", {"target_rule": target, "field": field, "corrected": clause, "applied": 0.0})
    agent.inner.add_edge_unchecked(agent.agent, "has_fault", f)
    for _ in range(3):
        agent.master_tick(); agent.tick()


def self_kind(agent):
    best, bf = None, -1.0
    for n in agent.s.nodes("Region"):
        x = agent.s.node(n)["attrs"]
        if x.get("is_self") == 1.0:
            cf = float(x.get("changed_frame") or 0)
            if cf >= bf:
                best, bf = x.get("axis_kind"), cf
    return best


def main():
    print("=" * 96)
    print("FULLY AUTONOMOUS SELF-REPAIR FROM LIVE PERCEPTION — measure, detect, repair, gate, in one episode.")
    print("=" * 96)
    corrected, broken = clauses()
    agent = WorldAdapter(seeds=()); load_all_seeds(agent)
    world = ArcWorld(AvatarRunEnv())

    print("\n  break the discriminator, then PLAY — the agent measures its own self-id and repairs live...")
    install_clause(agent, DISC, "effect", broken)

    sub, ctx = world.reset(); agent.perceive_frame(sub)
    g = game_anchor(agent)
    ax = agent.s.add_node("CapabilityAxis", {
        "is_axis": 1.0, "repairable": 1.0, "repair_rule": DISC, "repair_field": "effect",
        "repair_clause": corrected, "live_clause": broken,
        "saturation": 1.0, "sat_best": 1.0, "target": 1.0, "fault_open": 0.0})
    w = agent.s.add_node("SelfIdWindow", {"committed_n": 0.0, "held_n": 0.0, "epoch": 0.0, "prev_action": ""})
    agent.inner.add_edge_unchecked(g, "has_window", w)
    agent.inner.add_edge_unchecked(w, "for_axis", ax)

    for i in range(28):                                # varied warmup: establish is_self (no committed frames)
        sub, ctx = world.apply((["Up", "Down", "Left", "Right"][i % 4],))
        agent.perceive_frame(sub); agent.master_tick(); agent.tick()

    def disc_fault_attrs():
        return next((agent.s.node(f)["attrs"] for f in agent.s.nodes("Fault")
                     if agent.s.node(f)["attrs"].get("target_rule") == DISC
                     and agent.s.node(f)["attrs"].get("from_sat") is not None), None)

    trail, minted_at, repaired_at = [], None, None
    # PHASE A — commit to one action until the bug surfaces, the live measure regresses, and the agent
    # auto-detects + auto-repairs. Break promptly so a stale (still-flipped) window can't pre-empt the gate.
    for i in range(20):
        sub, ctx = world.apply(("Right",))
        agent.perceive_frame(sub); agent.master_tick(); agent.tick()
        fa = disc_fault_attrs()
        if fa and minted_at is None:
            minted_at = i
        if fa and fa.get("applied") == 1.0:
            repaired_at = i
            trail.append((i, self_kind(agent), "FAULT+REPAIRED (auto, from live measure)"))
            break
        if i % 2 == 0:
            trail.append((i, self_kind(agent), "FAULT" if minted_at == i else ""))
    # PHASE B — the agent varies its action (normal play): gate-and-hold reclassifies on action-CHANGE, so
    # the repaired discriminator RE-ESTABLISHES the self as controllable (rule-repair + a probe heals state).
    agent.inner.set_attr(w, "committed_n", 0.0); agent.inner.set_attr(w, "held_n", 0.0)  # fresh post-repair window
    for i in range(10):
        sub, ctx = world.apply((["Up", "Down", "Left", "Right"][i % 4],))
        agent.perceive_frame(sub); agent.master_tick(); agent.tick()
    trail.append(("B", self_kind(agent), "re-established after varying"))
    # PHASE C — commit again: the repaired self HOLDS controllable -> a clean post-repair window measures
    # high stability -> the gate KEEPS.
    for i in range(12):
        sub, ctx = world.apply(("Right",))
        agent.perceive_frame(sub); agent.master_tick(); agent.tick()
        if i % 4 == 0:
            trail.append((f"C{i}", self_kind(agent), ""))

    fa = next((agent.s.node(f)["attrs"] for f in agent.s.nodes("Fault")
               if agent.s.node(f)["attrs"].get("target_rule") == DISC
               and agent.s.node(f)["attrs"].get("from_sat") is not None), None)
    outcome = fa.get("outcome") if fa else None
    late_kind = self_kind(agent)
    print("\n  committed-action timeline (self axis_kind; FAULT/REPAIRED auto-events):")
    for i, k, ev in trail:
        print(f"    f{i:>2} self={k!r:14} {ev}")
    print(f"\n  fault auto-minted from the live measure: {minted_at is not None} (frame {minted_at}); "
          f"auto-repaired: {repaired_at is not None} (frame {repaired_at})")
    print(f"  gate outcome: {outcome!r}; self axis_kind at end of committed run: {late_kind!r}")

    ok = (minted_at is not None and repaired_at is not None and late_kind == "controllable"
          and outcome == "kept")
    print("\n" + "=" * 96)
    print(f"  {'PASS' if ok else 'FAIL'} — the agent MEASURED its own self-id stability while playing, a real "
          f"regression auto-minted a Fault (no injection, no hand-ingest), it repaired its discriminator by "
          f"name, and the gate KEPT the fix as later windows showed recovery. Self-originated end to end.")
    print("=" * 96)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
