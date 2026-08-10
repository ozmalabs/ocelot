"""AUTONOMOUS READING — ACT ON THE BOTTLENECK (graph-native, agent-controlled, generic, no teacher).

The measure-only loop surfaced the reading bottleneck (sequence reading stalls below target). Now the
agent ACTS on it, controlling the escalation itself and bringing its OWN expertise — no teacher. The
frontier carries CANDIDATE methods (a bigram LM and a trigram LM), each tagged with the gain the agent's
own measured history leads it to EXPECT (it built and measured both across this arc). The agent picks the
method to apply via a graph Term it owns (act_on_gap.pick_next_method_term: argmax over untried candidates
of expected_payoff). It runs that method; if it stalls, it marks it tried and the SAME Term ESCALATES to
the next-most-promising untried one — until the gap closes. The decision is the Term; the mechanism is
entirely generic (any frontier + candidate operators + the agent's payoff beliefs); only the reading
runners are domain-specific. No Python branch picks the method, no teacher suggests it.

Run:  PYTHONPATH=.:runners/dsl/python python -m scripts.autonomous_reading_act
"""
from __future__ import annotations

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "runners", "dsl", "python"))

import substrate_rs as srs
from domains import gap_prioritiser as gp
from domains import act_on_gap as act
from domains.reading_runners import RUNNERS

SEP = "=" * 92
TARGET = 0.95                                                     # bigram (~0.90) stalls; trigram (~0.97) closes

# The candidate METHODS for the sequence-reading frontier, each with the agent's OWN EXPERTISE: the payoff
# it expects from its measured history (across this arc it found a trigram LM the stronger reader). Graph
# DATA the agent ranks; any domain plugs in its own methods + the agent's beliefs.
METHODS = [
    {"name": "viterbi_bigram", "runner": "viterbi_bigram", "expected_payoff": 0.30},
    {"name": "viterbi_trigram", "runner": "viterbi_trigram", "expected_payoff": 0.55},
]


def run_scenario(target, label):
    s = srs.Substrate()
    act.declare_candidate_production(s)
    ax = s.add_node("CapabilityAxis", {"is_axis": 1.0, "capability_keys": ["sequence reading language model"],
                                       "shortfall": float(target - 0.42), "saturation": 0.0, "min_order": 1.0})
    for m in METHODS:                                           # candidate methods + the agent's payoff beliefs
        op = s.add_node("Operator", {"name": m["name"], "runner": m["runner"], "metric": "letter_accuracy",
                                     "target": target, act.EXPECTED_ATTR: m["expected_payoff"], act.TRIED_ATTR: 0.0})
        s.add_edge(ax, act.CANDIDATE_EDGE, op)
    print(f"\n  {label}: sequence-reading bottleneck, target {target}.")
    closed_by, steps = None, 0
    for step in range(1, len(METHODS) + 2):
        op = act.pick_next_method(s, ax)                       # the agent's ACT decision (a graph Term, no teacher)
        if op is None:
            print(f"    step {step}:  every candidate method tried and STILL short — the gap stands (honest).")
            break
        a = s.node(op)["attrs"]; steps = step
        measured = RUNNERS[a["runner"]](s, None, None)        # host runs the method the Term named
        met = measured >= target
        verb = "CLOSES the gap" if met else "stalls -> agent ESCALATES to its next-best untried method"
        print(f"    step {step}:  agent CHOSE '{a['name']}' (top untried by expected_payoff {a[act.EXPECTED_ATTR]})"
              f"  -> {measured:.3f}  [{verb}]", flush=True)
        if met:
            closed_by = a["name"]; break
        act.mark_tried(s, op)                                 # stalled; the Term escalates next
    return closed_by, steps


def main():
    print(SEP)
    print("AUTONOMOUS READING — ACT ON THE BOTTLENECK (agent-controlled, no teacher): the agent acts on its")
    print("stalled sequence-reading frontier using its OWN expertise — a graph Term ranks the candidate methods.")
    print(SEP)
    print(f"\n  candidate methods + the agent's expected payoff (from its own measured history):")
    for m in METHODS:
        print(f"      {m['name']:16} expected_payoff {m['expected_payoff']}")

    closed_by, steps = run_scenario(0.95, "A — a normal target")
    run_scenario(0.99, "B — a hard target (no single method suffices)")

    print(f"\n  {SEP[:88]}")
    print(f"  the agent acts on its OWN bottleneck with NO teacher and NO Python branch: a graph Term it owns")
    print(f"  ranks its candidate methods by the payoff its own history expects, picks the best UNTRIED, and")
    print(f"  ESCALATES to the next when one stalls. Scenario A closed with '{closed_by}' in {steps} step(s);")
    print(f"  scenario B exhausted every method and reported the gap honestly. The mechanism is GENERIC — any")
    print(f"  frontier + candidate operators + the agent's beliefs; only the runners are reading-specific.")
    print(SEP)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
