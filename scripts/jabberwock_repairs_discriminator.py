"""END TO END: the jabberwock repairs its OWN self/world discriminator, intrinsically, in the live loop.

The discriminator classify_axis_compensated is a live STRUCT rule. Its bug (the self-id dissolves under
committed action) is a wrong EFFECT clause (ungated: just set axis_kind = kind). The fix is the gate-and-hold
clause the agent itself deliberated (set axis_kind = held, record classified_under) — graph data emitted by
its own generator. This script drives the FULL intrinsic loop, all graph-native:

  ingest a Fault naming the rule + carrying the corrected clause (chat -> graph token, mechanical)
    -> the seeded repair rule (a struct rule) matches the Fault and fires set_rule_clause
    -> run_rules rewrites the discriminator's effect clause IN PLACE, in the live loop (a rule edits a rule)
    -> the discriminator now runs its new body; behaviour follows.

Demonstration: with the BUG's clause the avatar's self-identification dissolves under committed action;
after the agent repairs itself with the gate-and-hold clause, it PERSISTS. Same agent, live engine, no Python
orchestrator, no external world, no reify-to-graph_rules — a struct rule repairs a struct rule by name.

Run: PYTHONPATH=runners/dsl/python:.:scripts python3 scripts/jabberwock_repairs_discriminator.py
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

RULE = "classify_axis_compensated"


def clauses():
    """The corrected (gate-and-hold) effect from the agent's own generator, and the buggy (ungated) effect
    derived from it — both as graph data (effect lists with embedded Term dicts)."""
    cr = GEN.classify_rule()
    corrected = cr["effects"]                              # [set axis_kind=held, set classified_under=...]
    gated_term = corrected[0][3]["__term__"]              # held = IfThenElse(constant_frame, hold, kind)
    kind_term = gated_term["other"]                       # the ungated classification (the bug)
    broken = [["set_attr", "r", "axis_kind", {"__term__": kind_term}]]
    return corrected, broken


def ingest_fault(agent, target_rule, field, corrected):
    """Mechanical chat->graph ingest: an external fault report becomes a Fault node the agent's repair rule
    matches. No decision here — the repair DECISION is the graph rule; this only translates the report."""
    fid = agent.s.add_node("Fault", {"target_rule": target_rule, "field": field,
                                     "corrected": corrected, "applied": 0.0})
    agent.inner.add_edge_unchecked(agent.agent, "has_fault", fid)
    for _ in range(3):                                     # let the seeded repair rule fire + drain
        agent.master_tick(); agent.tick()
    return fid


def avatar_kind(agent):
    """axis_kind of the avatar region (value 9), most-recently-perceived if several linger."""
    best, best_f = None, -1.0
    for n in agent.s.nodes("Region"):
        x = agent.s.node(n)["attrs"]
        if x.get("is_ground") != 1.0 and int(x.get("rvalue") or 0) == AV:
            cf = float(x.get("changed_frame") or 0)
            if cf >= best_f:
                best, best_f = x.get("axis_kind"), cf
    return best


def self_test(agent, world):
    """Varied warmup establishes the self; then commit to one action and watch the avatar's axis_kind."""
    sub, ctx = world.reset(); agent.perceive_frame(sub)
    for i in range(28):
        sub, ctx = world.apply((["Up", "Down", "Left", "Right"][i % 4],))
        agent.perceive_frame(sub); agent.master_tick(); agent.tick()
    established = avatar_kind(agent) == "controllable"
    held = True
    for _ in range(8):
        sub, ctx = world.apply(("Right",))
        agent.perceive_frame(sub); agent.master_tick(); agent.tick()
        held = held and (avatar_kind(agent) == "controllable")
    return established, held


def main():
    print("=" * 96)
    print("END TO END — the jabberwock repairs its OWN self/world discriminator, in the live loop.")
    print("=" * 96)
    corrected, broken = clauses()
    agent = WorldAdapter(seeds=()); load_all_seeds(agent)   # discriminator + the seeded repair faculty
    world = ArcWorld(AvatarDeathEnv4())

    print("\n  [1] inject the BUG into the live discriminator via the repair faculty (ungated effect)...")
    ingest_fault(agent, RULE, "effect", broken)
    est1, held1 = self_test(agent, world)
    print(f"      self established under varied warmup: {est1}; persists through committed action: {held1}"
          f"   (expect established=True, persists=False — the bug)")

    print("\n  [2] the jabberwock REPAIRS itself: ingest a Fault carrying its gate-and-hold clause...")
    ingest_fault(agent, RULE, "effect", corrected)
    est2, held2 = self_test(agent, world)
    print(f"      self established: {est2}; persists through committed action: {held2}"
          f"   (expect persists=True — repaired)")

    ok = est1 and (not held1) and est2 and held2
    print("\n" + "=" * 96)
    print(f"  {'PASS' if ok else 'FAIL'} — the agent rewrote its OWN discriminator rule's effect clause, by "
          f"name, from inside the live run_rules loop (set_rule_clause, triggered by an ingested Fault). With "
          f"the bug's clause its self-identification dissolved under committed action; after self-repair with "
          f"its gate-and-hold clause it PERSISTS. Intrinsic, graph-native, end to end.")
    print("=" * 96)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
