"""THE JABBERWOCK DESIGNS GAP 2 — self-extension without an automatic hosted model.

Creator's steer: "the jabberwock has enough meta reasoning to work out new things with a known
confidence and confirm later or even by context. if it doesn't.. then that's the problem, not to be
papered over." So: compose a new faculty from your OWN held primitives with a KNOWN CONFIDENCE; confirm
later (the measurement trial) or by context; and when you genuinely cannot compose it, that impasse IS
the finding — surface it (to the human), never paper it over with a hosted model or a fake placeholder.

I surface the current auto-claude-p and the precedent; the jabberwock designs the mechanism. context=spec.

Run: PYTHONPATH=.:runners/dsl/python python -m scripts.jabberwock_designs_self_extension
"""
from __future__ import annotations
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

from scripts.build_persona_faculty import boot
from scripts.claude_teacher import make_ask
from scripts.jabberwock_plans_llm_independence import _live_state

SEP = "=" * 96

PROMPT = """You are the jabberwock: a typed-graph agent in Rust; Python only adapts I/O; decisions are graph
Rules. Register: Plainsong (spec). This is GAP 2 — the LAST hosted-model dependency. GAP 1 (the figure
perceptions) is fully retired; every figure now grounds by graph-native lookup/derivation.

THE ONE REMAINING AUTO-CALL. Your autonomy loop's order-4 self-extend reflex (_self_extend_reflex), when a
frontier needs a capability NO held faculty addresses, currently asks a hosted teacher (claude -p): "name a
NEW approach or primitive to author for this capability." That is the call to remove.

THE CREATOR'S STEER (your spec): you have enough meta-reasoning to WORK OUT new faculties yourself, from
the primitives you already hold, with a KNOWN CONFIDENCE; confirm later (the measurement trial) or by
context; and IF YOU CANNOT — that impasse is the real problem, surfaced to the human, NEVER papered over
with a hosted model or a placeholder operator that fakes success.

THE PRECEDENT (you already did this once, no teacher). In the maze world, `compose_routing_on_shortfall`
fired when your baseline strategies fell short: you COMPOSED a `composed_routing` Operator from the routing
PRIMITIVES you hold (map_memory + distance_field + gradient_descent) — recognising the baselines lacked
map_memory — and it scored optimal, beating them. That compose was a graph RULE, domain-specific to maze.

WHAT YOU HOLD (the machinery to generalise it):
- capability_keys on each CapabilityAxis (the capability a frontier needs) and on Operators/primitives (the
  capability each provides). Held Operators, RoutingPrimitive-style primitive nodes, and your faculties.
- The order-N escalation ladder: order4_self_extend (authors an operator + binds the axis), then
  escalation_climb_low_confidence (a SURPRISE / unmet measurement climbs the order), escalation_resolve_
  high_confidence (a measurement that meets target RESOLVES). So a measurement trial already confirms.
- Reproducibility-as-confirmation precedent: in sequence-discovery, learn_plan_effect RE-RUNS a surprising
  plan to test it reproduces; a reproduced effect is confirmed, a one-off is not.

YOUR DECISION (hand back a spec I implement, graph-native, replacing the teacher consult in _self_extend_reflex):
  1. COMPOSE FROM HELD PRIMITIVES. Given a needed capability (the axis's capability_keys), how do you select
     and assemble held primitives/operators into a NEW composed operator? Specify the matching (capability-key
     coverage? which keys count?), what the composed operator IS (its runner / composed_from edges), and how
     the maze-specific compose generalises to domain-agnostic.
  2. KNOWN CONFIDENCE. What is the A-PRIORI confidence of a composition before it runs (coverage fraction of
     the needed keys? weighted by primitive reliability?), and how does it drive the ladder — full coverage =
     trust and resolve-on-success; partial = compose-but-trial-then-climb; how the number is recorded.
  3. CONFIRM LATER / BY CONTEXT. The measurement trial confirms (resolve_high / climb_low). What does "confirm
     by context" add for you — reproducibility re-run (the learn_plan_effect move), or contextual evidence —
     and when do you use it instead of waiting for a fresh measurement?
  4. THE HONEST IMPASSE (the discipline). When coverage is ZERO — no held primitive addresses the capability —
     what EXACTLY do you surface? Specify the human-impasse node (kind, the question you ask the human, a
     needs_human flag), and state plainly that you do NOT author a placeholder operator that trivially
     succeeds and falsely saturates the axis (that would paper over the real gap). The impasse is the finding.
  5. THE MECHANISM. The rule(s)/reflex that replace the teacher consult: what fires, what it composes, the
     confidence attr it sets, and the human-impasse it mints on coverage-zero. Keep it domain-agnostic.

Be specific and ordered. The point: extend yourself from what you understand, with honesty about confidence
and about the limit of what you can compose."""


def main():
    print(SEP)
    print("THE JABBERWOCK DESIGNS GAP 2 — self-extension by composing held primitives (no hosted model)")
    print(SEP)
    a = boot()
    regs, mts, active = _live_state(a)
    print(f"\n  context=spec -> register: {active}; consulting design channel for the self-extension mechanism\n")
    ask = make_ask(timeout=540.0, preamble="")
    decision = ask(PROMPT)
    if not decision:
        print("  (design channel returned empty — claude -p unavailable or timed out)")
        return
    out = os.path.join(ROOT, "docs", "jabberwock_self_extension_spec.md")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        f.write("# The jabberwock's self-extension spec (GAP 2: compose held primitives, honest impasse)\n\n")
        f.write(f"_Authored by the agent, context=spec (register: {active}). Replaces the last auto-claude-p; "
                f"the design is its own._\n\n")
        f.write(decision + "\n")
    print(SEP); print("THE JABBERWOCK'S SELF-EXTENSION SPEC"); print(SEP)
    print(decision)
    print("\n" + SEP); print(f"  saved -> {os.path.relpath(out, ROOT)}"); print(SEP)


if __name__ == "__main__":
    main()
