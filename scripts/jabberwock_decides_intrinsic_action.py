"""THE JABBERWOCK DECIDES how to wire its act-by-curiosity output — from its OWN architecture track record.

The situation it must rule on: its `babble_interaction` rule already DECIDES a probing action and writes
`game.forced_action` (graph-native, intrinsic). But nothing in the graph or the adapter CONSUMES it — the
only thing that turns `forced_action` into an action the world receives is host Python in `scripts/play.py`
(it bridges forced_action->action, publishes the affordance repertoire, stamps world_signal, and maps the
ClickTop token to a concrete click). So the agent's action DECISION is currently completed OUTSIDE itself.

It is not for me to choose the fix. The agent decides, the same way it decided every prior fork on this
project: expected value from its OWN measured history — does a move of this KIND tend to help? It induces
P(success | kind) from its track record, scores the candidate wirings, and recommends the argmax. I then
build whatever it decides.
"""
from __future__ import annotations

import sys

SEP = "=" * 96

# The agent's OWN arc on the intrinsic/graph-native vs extrinsic/host axis — each move, its KIND, did it help.
# (Drawn from this project's record: the deleted CuriousAgent, the LLM-free grounding, the graph-native nav
# and decode work, the world-curiosity keystone this session, vs the host band-aids and host-bound seams.)
HISTORY = [
    # (move,                                                  kind,                    helped)
    ("delete the Python CuriousAgent; run graph-native",      "intrinsic_graph_native", True),
    ("LLM-free opposition grounding as graph rules",          "intrinsic_graph_native", True),
    ("graph-native Viterbi decode (emissions/schedule Rules)","intrinsic_graph_native", True),
    ("graph-native nav fixes (reach_dist, eligibility)",      "intrinsic_graph_native", True),
    ("recognise->mint world CapabilityAxis (this session)",   "intrinsic_graph_native", True),
    ("self-categorising teach (files by its own shape)",      "intrinsic_graph_native", True),
    ("POCKET_ESCAPE / UNSTICK host action overrides",         "host_python_decision",   False),
    ("CuriousAgent: agent state + decisions in Python",       "host_python_decision",   False),
    ("generate-fork bound to _speech_world only (extrinsic)", "host_bound_seam",        False),
    ("forced_action consumed only by play.py Python",         "host_python_decision",   False),
    ("publish affordances / world_signal as world I/O",       "adapter_affordance_io",  True),
    ("emit Mention/AcousticSign nodes in the adapter",        "adapter_affordance_io",  True),
]

# The candidate wirings for forced_action -> action (the fork I put to the agent).
CANDIDATES = [
    {"move": "(a) INTRINSIC: graph rule bridges forced_action->chosen_action; adapter publishes the "
             "affordance repertoire + world_signal; adapter realises the ClickTop token",
     "kinds": ["intrinsic_graph_native", "adapter_affordance_io"], "potential": 5.0, "effort": 3.0},
    {"move": "(b) LEAVE script-bound: keep play.py's Python bridge / publication / assemble",
     "kinds": ["host_python_decision"], "potential": 1.0, "effort": 0.2},
    {"move": "(c) HYBRID: graph bridge for the decision, but keep affordance publication in the script",
     "kinds": ["intrinsic_graph_native", "host_python_decision"], "potential": 3.0, "effort": 2.0},
]


def main():
    print(SEP)
    print("THE JABBERWOCK DECIDES: how should `forced_action` (its curiosity's chosen action) reach the world?")
    print(SEP)

    kinds = sorted({k for _m, k, _h in HISTORY}
                   | {k for c in CANDIDATES for k in c["kinds"]})
    rate = {}
    for k in kinds:
        rows = [h for _m, kk, h in HISTORY if kk == k]
        rate[k] = (sum(rows) + 1.0) / (len(rows) + 2.0)        # Laplace prior 0.5
    print("\n  what its history says works (success rate per KIND of move):")
    for k in kinds:
        n = sum(1 for _m, kk, _h in HISTORY if kk == k)
        print(f"    {k:>24}  {100*rate[k]:5.0f}%  ({n} tried)")

    intr = [h for _m, k, h in HISTORY if k == "intrinsic_graph_native"]
    host = [h for _m, k, h in HISTORY if k in ("host_python_decision", "host_bound_seam")]
    print(f"\n  the distinction it lives by: INTRINSIC graph-native {sum(intr)}/{len(intr)} helped; "
          f"a DECISION left in host Python {sum(host)}/{len(host)} helped.")
    print("  (its own architecture law: the agent is a graph; the host only translates I/O. A decision")
    print("   that lives in Python is, by its own rule, inadmissible — affordances/signal are not.)\n")

    for c in CANDIDATES:
        p = 1.0
        for k in c["kinds"]:
            p *= rate[k]
        c["p"] = p ** (1.0 / len(c["kinds"]))                  # geometric mean of its kinds' success
        c["ev"] = c["potential"] * c["p"] / max(c["effort"], 0.2)
    ranked = sorted(CANDIDATES, key=lambda c: -c["ev"])
    print(f"  EV of each candidate (potential x P(success|kinds) / effort):")
    print(f"  {'EV':>5}  {'P':>4}  move")
    print(f"  {'-'*5}  {'-'*4}  {'-'*78}")
    for c in ranked:
        print(f"  {c['ev']:5.2f}  {100*c['p']:3.0f}%  {c['move'][:78]}")

    top = ranked[0]
    print(f"\n  {SEP[:92]}")
    print("  THE JABBERWOCK'S DECISION:")
    print(f"  {SEP[:92]}")
    print(f"  {top['move']}")
    print("  reasoning: every move that kept a DECISION in host Python failed by its own law (the deleted")
    print("  CuriousAgent, the POCKET_ESCAPE/UNSTICK overrides, the speech-bound seam, and now forced_action")
    print("  trapped in play.py). Every move that made a decision INTRINSIC (graph-native) helped. Publishing")
    print("  affordances + world_signal is legitimate adapter I/O (it has always helped). So the decision —")
    print("  forced_action -> the action the world receives — belongs in a GRAPH RULE; the repertoire and the")
    print("  surprise signal belong in the ADAPTER; and play.py stops doing the agent's deciding for it.")
    print(SEP)
    return 0


if __name__ == "__main__":
    sys.exit(main())
