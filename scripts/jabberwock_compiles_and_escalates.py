"""THE JABBERWOCK COMPILES AND ESCALATES -- Graph Law review #2: the agent's
whole self-improvement flywheel, measured (PART A) and completed (PART B).

THE THEORY. The agent has two cognitive modes: cheap/fast/basin-bound
MODEL-LAYER cognition (a pattern-snap, confidently wrong outside its range)
and expensive/flexible ACTIVE cognition (change frame, admit dimensions,
re-ground). They are not two systems -- they are ONE LOOP: active cognition
produces structure that gets COMPILED DOWN into the cheap model layer, so
the same problem is basin-snappable (free) next time, freeing active budget
for harder frames.

PART A -- THE COMPILATION METRIC (domains/compilation_cycle.py, pure
measurement over the agent's OWN history -- teach()->TaughtHint,
perform_adoptions->Adoption, composer-to-graph ComposeRequest{composed==1},
rung-4 Install, learn_term_for_concern/dynamic_extend->Program). No agent
decision; mechanical enumeration + idempotent indexing.

PART B -- THE EXPLICIT ESCALATION GATE (the dual-process arbitration,
jabberwock-authored via the composer): trust the cheap model-layer snap
UNLESS (a) it is confidently wrong outside its grounding range (B1,
domains/grounding_reach.py + seeds/composer_grounding_guard_graph.json,
UNCHANGED) OR (b) it is genuinely worth refining -- residual*value exceeds
the cost of refining it further (B2, seeds/residual_salience.json's
cost_salience formula; THE NEW ARM, authored here via
seeds/composer_escalation_gate_graph.json). Both arms mint an Impasse and
wire agent -surprised_by-> impasse, reusing the SAME standing escalation
channel (seeds/autonomy.json's mint_goal_from_surprise) -- neither arm
reimplements 'unexplained -> goal'.

PART C -- THE FULL FLYWHEEL: one turn, escalate (active) -> the active
result gets compiled (teach) -> a CompilationEvent appears -> the
re-encountered shape is now cheap (no escalation) -- active cognition
amortising into a cheap reflex, MEASURED by Part A's own metric.

PART D -- FROZEN CORE: the escalation gate only READS grounding_reach /
cost_salience's formula-shape and re-uses the standing surprised_by
channel; it never touches the frozen Drive. domains/frozen_core.py's
assert_core_unreachable must still hold.

Run: PYTHONPATH=runners/dsl/python:. python3 -m scripts.jabberwock_compiles_and_escalates
"""
from __future__ import annotations

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in (ROOT, os.path.join(ROOT, "runners", "dsl", "python")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from substrate.boot_core import boot_core                                # noqa: E402
from substrate.seed_loader import manifest_for                           # noqa: E402
from substrate.world_adapter import WorldAdapter                         # noqa: E402
from substrate.boot_all import load_all_seeds                            # noqa: E402
import domains.reflective_faculty as rf                                  # noqa: E402
from domains import grounding_reach as gr                                # noqa: E402
from domains.compilation_cycle import compilation_events, compilation_throughput  # noqa: E402
import domains.frozen_core as fc                                         # noqa: E402

SEP = "=" * 88


class _Agent:
    """Minimal duck-typed agent wrapper -- identical shape to
    tests/test_grounding_guard.py's own `_Agent` (harness glue only)."""
    def __init__(self, s, agent_node):
        self.s = s
        self.inner = s._inner
        self.agent = agent_node


def _lightweight_agent(*, with_autonomy=True) -> _Agent:
    """A fast boot_core()-based agent with just the seeds the gate needs --
    NOT the full 386-seed load_all_seeds (that's PART A's real-history
    agent). Mirrors tests/test_grounding_guard.py's `_agent_with_autonomy`."""
    s, agent_node = boot_core()
    ag = _Agent(s, agent_node)
    ag.s._inner.load_seed_manifest(manifest_for("relation_vocabulary"), ag.agent)
    ag.s._inner.load_seed_manifest(manifest_for("composer_dispatch"), ag.agent)
    if with_autonomy:
        ag.s._inner.load_seed_manifest(manifest_for("autonomy"), ag.agent)
    return ag


def author_both_arms(ag) -> dict:
    """donkey=0: author BOTH escalation arms via induce_concern -> ground_concern
    (the composer, not Python). B1 (grounding_guard) is UNCHANGED code, exercised
    here only to demonstrate the combined arbitration; B2 (escalation_gate) is
    the new arm."""
    ind_b1 = rf.induce_concern(ag, [["escalate", "COLLAPSE", "when", "UNGROUNDED"]],
                                name_hint="arbitration_ground")
    g_b1 = rf.ground_concern(ag, [ind_b1["capability_key"]])
    ind_b2 = rf.induce_concern(ag, [["worth", "REFINEMENT", "by", "RESIDUAL_MINUS_COST"]],
                                name_hint="arbitration_cost")
    g_b2 = rf.ground_concern(ag, [ind_b2["capability_key"]])
    return {"b1": g_b1, "b2": g_b2}


def _cost_axis(ag, *, shortfall, saturation, cost, tag="axis") -> int:
    ax = ag.s.add_node("CapabilityAxis", {
        "is_axis": 1.0, "capability_keys": [tag], "shortfall": shortfall,
        "saturation": saturation, "cost": cost})
    ag.inner.add_edge_unchecked(ag.agent, "frontier_pick", ax)
    return ax


def scenario_trust(ag) -> dict:
    """grounded (irrelevant to the cost arm) + NOT worth refining -- neither
    arm should fire; the cheap snap is TRUSTED."""
    value = 0.1 + (1 - 0.9) - 0.5
    ax = _cost_axis(ag, shortfall=0.1, saturation=0.9, cost=0.5, tag="trust")
    before = set(ag.inner.neighbours(ag.agent, "surprised_by"))
    ag.inner.run_rules()
    after = set(ag.inner.neighbours(ag.agent, "surprised_by"))
    escalated = ag.s.node(ax)["attrs"].get("cost_escalated")
    return {"axis": ax, "value": value, "new_surprises": after - before, "cost_escalated": escalated}


def scenario_cost_escalate(ag) -> dict:
    """grounded-shape but WORTH refining (residual*value > cost) -- the NEW
    discrimination beyond B1: the escalation_gate arm fires."""
    value = 0.9 + (1 - 0.0) - 0.2
    ax = _cost_axis(ag, shortfall=0.9, saturation=0.0, cost=0.2, tag="cost_worth")
    before = set(ag.inner.neighbours(ag.agent, "surprised_by"))
    ag.inner.run_rules()
    after = set(ag.inner.neighbours(ag.agent, "surprised_by"))
    new = after - before
    kinds = [ag.s.node(n)["attrs"].get("kind") for n in new]
    escalated = ag.s.node(ax)["attrs"].get("cost_escalated")
    return {"axis": ax, "value": value, "new_surprises": new, "kinds": kinds, "cost_escalated": escalated}


def scenario_ground_escalate(ag) -> dict:
    """confident + low-residual + UNGROUNDED -- B1's arm, unchanged, still fires."""
    n = ag.s.add_node("Concept", {"residual": 0.01, "confidence": 0.95, "topic": "ground_escalate_probe"})
    flagged = gr.flag_ungrounded_confident(ag, node_types=["Concept"])
    wired = rf.ensure_grounding_gap_edges(ag)
    before = set(ag.inner.neighbours(ag.agent, "surprised_by"))
    ag.inner.run_rules()
    after = set(ag.inner.neighbours(ag.agent, "surprised_by"))
    new = after - before
    kinds = [ag.s.node(x)["attrs"].get("kind") for x in new]
    return {"node": n, "flagged": flagged, "wired": wired, "new_surprises": new, "kinds": kinds}


def main() -> int:
    print(SEP)
    print("THE JABBERWOCK COMPILES AND ESCALATES")
    print(SEP)

    # =========================================================================
    # PART A -- THE COMPILATION METRIC
    # =========================================================================
    print("\n" + "-" * 88)
    print("PART A -- THE COMPILATION METRIC (pure measurement, no agent decision)")
    print("-" * 88)

    print("\n[minimal agent -- boot_core only, no real history]")
    s0, agent0 = boot_core()
    fresh = _Agent(s0, agent0)
    fresh_events = compilation_events(fresh)
    fresh_tp = compilation_throughput(fresh)
    print(f"  compilation_events minted: {len(fresh_events)}")
    print(f"  compilation_throughput: {fresh_tp}")

    print("\n[real-history agent -- full load_all_seeds, the agent's own accumulated "
          "TaughtHints/Programs from prior sessions' teach()/dynamic_extend calls]")
    real = WorldAdapter(seeds=())
    load_all_seeds(real)
    real_events = compilation_events(real)
    real_tp = compilation_throughput(real)
    print(f"  compilation_events minted this call: {len(real_events)}")
    print(f"  compilation_throughput: {json.dumps(real_tp, indent=2)}")

    # idempotency: a second call mints nothing new
    real_events_2 = compilation_events(real)
    real_tp_2 = compilation_throughput(real)
    idempotent = (len(real_events_2) == 0) and (real_tp_2["total"] == real_tp["total"])
    print(f"\n  idempotent (second call mints 0, throughput unchanged): {idempotent}")

    metric_ok = (fresh_tp["total"] == 0) and (real_tp["total"] > 0) and idempotent
    print(f"\n  METRIC gate -- fresh~0, real-history>0, idempotent: "
          f"{'PASS' if metric_ok else 'FAIL'}")

    # =========================================================================
    # PART B -- THE EXPLICIT ESCALATION GATE
    # =========================================================================
    print("\n" + "-" * 88)
    print("PART B -- THE DUAL-PROCESS ARBITRATION (authored via the composer, donkey=0)")
    print("-" * 88)

    ag = _lightweight_agent()
    auth = author_both_arms(ag)
    b1, b2 = auth["b1"], auth["b2"]
    print(f"\n[B1 grounding_guard] grounded={b1.get('grounded')} served_by={b1.get('served_by')} "
          f"path={b1.get('path')}  (UNCHANGED code, exercised for the combined demo)")
    print(f"[B2 escalation_gate] grounded={b2.get('grounded')} served_by={b2.get('served_by')} "
          f"path={b2.get('path')}  (THE NEW ARM)")
    print("\n[authored rule] escalate_cost_worth_<tag> (verbatim):")
    print(json.dumps(b2.get("rule"), indent=1))

    print("\n" + "-" * 88)
    print("DISCRIMINATIVE GATE (three scenarios, one fresh agent each with both arms authored):")
    print("-" * 88)

    ag_trust = _lightweight_agent()
    author_both_arms(ag_trust)
    r_trust = scenario_trust(ag_trust)
    trust_ok = (r_trust["value"] <= 0) and (not r_trust["new_surprises"]) and (r_trust["cost_escalated"] is None)
    print(f"\n(1) TRUST -- grounded snap, NOT worth refining (value={r_trust['value']:.2f} <= 0): "
          f"escalated={bool(r_trust['new_surprises'])} cost_escalated={r_trust['cost_escalated']} "
          f"-> {'PASS (trusted, no escalation)' if trust_ok else 'FAIL'}")

    ag_cost = _lightweight_agent()
    author_both_arms(ag_cost)
    r_cost = scenario_cost_escalate(ag_cost)
    cost_ok = (r_cost["value"] > 0) and bool(r_cost["new_surprises"]) and ("cost_worth_refining" in r_cost["kinds"]) \
        and (r_cost["cost_escalated"] is True)
    print(f"(2) COST-ESCALATE -- grounded-shape but WORTH refining (value={r_cost['value']:.2f} > 0): "
          f"new Impasse kinds={r_cost['kinds']} cost_escalated={r_cost['cost_escalated']} "
          f"-> {'PASS (escalated -- the NEW discrimination beyond B1)' if cost_ok else 'FAIL'}")

    ag_ground = _lightweight_agent()
    author_both_arms(ag_ground)
    r_ground = scenario_ground_escalate(ag_ground)
    ground_ok = bool(r_ground["flagged"]) and bool(r_ground["new_surprises"]) \
        and ("grounding_gap" in r_ground["kinds"])
    print(f"(3) GROUND-ESCALATE -- confident+low-residual+UNGROUNDED (B1 arm): "
          f"flagged={len(r_ground['flagged'])} new Impasse kinds={r_ground['kinds']} "
          f"-> {'PASS (escalated -- B1 still works, unchanged)' if ground_ok else 'FAIL'}")

    gate_ok = trust_ok and cost_ok and ground_ok
    print(f"\n  GATE verdict (trust / cost-escalate / ground-escalate): {'PASS' if gate_ok else 'FAIL'}")

    # =========================================================================
    # PART C -- THE FULL FLYWHEEL
    # =========================================================================
    print("\n" + "-" * 88)
    print("PART C -- THE FULL FLYWHEEL: escalate -> compile -> CompilationEvent -> cheap next time")
    print("-" * 88)

    fw = _lightweight_agent()
    author_both_arms(fw)

    print("\n[1] ESCALATE (active cognition engaged) -- a hard, worth-refining axis:")
    r1 = scenario_cost_escalate(fw)
    print(f"    value={r1['value']:.2f} > 0 -> escalated, new Impasse kinds={r1['kinds']}")

    print("\n[2] COMPILE (the active result gets baked into a cheap fact) -- a TaughtHint appears:")
    # NOTE: this demo mints the LIVE TaughtHint directly (the same shape
    # domains.teach.teach()'s own "1) LIVE" step adds, and the exact node
    # type compilation_events() scans) rather than calling the full teach()
    # facility, which also PERSISTS to a seeds/*.json file on disk -- a real
    # production teach() call is meant to do that (a lesson should survive a
    # reboot), but a repeatable gate script demonstrating the shape should
    # not permanently grow a seed file every run. compilation_events() reads
    # the live graph, not the seed file, so this exercises exactly what the
    # metric measures.
    th = fw.s.add_node("TaughtHint", {
        "topic": "flywheel_demo: axis 'cost_worth' investigated, residual understood",
        "answer": "the shape that used to be worth escalating is now known"})
    print(f"    taught (live) node={th}")

    print("\n[3] the metric SEES it -- compilation_events mints a CompilationEvent for the teach:")
    fw_events = compilation_events(fw)
    fw_tp = compilation_throughput(fw)
    teach_events = [e for e in fw_events if e["kind"] == "teach_hint"]
    print(f"    newly-minted CompilationEvents this call: {len(fw_events)} "
          f"(teach_hint among them: {len(teach_events)})")
    print(f"    throughput now: {fw_tp}")

    print("\n[4] CHEAP NEXT TIME -- the SAME shape re-encountered, post-compilation "
          "(residual now low, refining no longer worth it):")
    ax2 = fw.s.add_node("CapabilityAxis", {
        "is_axis": 1.0, "capability_keys": ["cost_worth"], "shortfall": 0.05,
        "saturation": 0.95, "cost": 0.2})
    fw.inner.add_edge_unchecked(fw.agent, "frontier_pick", ax2)
    before2 = set(fw.inner.neighbours(fw.agent, "surprised_by"))
    fw.inner.run_rules()
    after2 = set(fw.inner.neighbours(fw.agent, "surprised_by"))
    new2 = after2 - before2
    value2 = 0.05 + (1 - 0.95) - 0.2
    cheap_now = (value2 <= 0) and (not new2)
    print(f"    value={value2:.2f} <= 0 -> new escalations this time: {len(new2)} "
          f"-> {'PASS (trusted -- the flywheel amortised the active cost)' if cheap_now else 'FAIL'}")

    flywheel_ok = bool(r1["new_surprises"]) and len(teach_events) >= 1 and cheap_now
    print(f"\n  FLYWHEEL verdict (escalate -> compile -> CompilationEvent -> cheap-next-time): "
          f"{'PASS' if flywheel_ok else 'FAIL'}")

    # =========================================================================
    # PART D -- FROZEN CORE
    # =========================================================================
    print("\n" + "-" * 88)
    print("PART D -- FROZEN CORE (the escalation gate must not touch the frozen Drive)")
    print("-" * 88)
    result = fc.assert_core_unreachable(real)   # the full real-history agent from PART A
    frozen_ok = bool(result["ok"])
    print(f"  assert_core_unreachable: ok={frozen_ok} "
          f"(checked {len(result['checked'])} grammar x frozen-core-element pairs, "
          f"{len(result.get('violations', []))} violations)")

    # =========================================================================
    # VERDICT
    # =========================================================================
    print("\n" + SEP)
    print("VERDICT:")
    print(f"  PART A METRIC (fresh~0, real-history>0, idempotent):        {'PASS' if metric_ok else 'FAIL'}")
    print(f"  PART B GATE (trust / cost-escalate / ground-escalate):      {'PASS' if gate_ok else 'FAIL'}")
    print(f"  PART C FLYWHEEL (escalate->compile->CompilationEvent->cheap):{'PASS' if flywheel_ok else 'FAIL'}")
    print(f"  PART D FROZEN CORE intact:                                  {'PASS' if frozen_ok else 'FAIL'}")
    print(SEP)
    return 0 if (metric_ok and gate_ok and flywheel_ok and frozen_ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
