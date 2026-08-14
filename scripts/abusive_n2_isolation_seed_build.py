#!/usr/bin/env python3
"""ABUSIVE-DYNAMICS N2 -- ISOLATION AS AN ACTIVE PROCESS (support edges
severed over time), seed builder (block 301000).

Authoring tool ONLY: it EMITS `seeds/abusive_n2_isolation.json` (graph data)
-- no agent decisions, no rule engine, no graph state. See
`docs/research/bigville/ABUSIVE_N2_ISOLATION_PREREG.md` for the full design
rationale. In brief, N2 composes TWO already-built substrates -- N1's
credibility-asymmetry loop (`abusive_n1_credibility_loop`, block 298000,
UNMODIFIED, riding `snap_frustration`/`arousal_window_coreg` in turn,
UNMODIFIED) supplies the abuser/victim dyad AND the per-`NetworkNode`
`belief_gap` read-off -- N2 reuses that mechanism DIRECTLY (`depends_on`),
never reimplementing credibility dynamics -- with exactly TWO new rules
riding TWO independent, coupled severing drivers (ABUSIVE_RELATIONSHIPS_
NETWORK.md Part B3 / Part E N2):

  1. `n2_abuser_active_sever` -- the ABUSER-DRIVEN driver (A3, Stark): the
     abuser actively severs the victim's `support_edge` to a given
     `NetworkNode` once that node's pre-assigned (mechanical, world-adapter-
     set-once) `sever_at_tick` schedule has arrived, PROVIDED the arm's
     `isolation_tactic_on` switch is armed. The schedule (WHICH node, WHEN)
     is mechanical per-node setup identical in kind to N1's own
     `observes_private = 1.0 if i==0 else 0.0` per-node setup -- assigned
     ONCE at construction, never a live decision; the RULE decides whether
     to act on it (whether the tactic is armed) and performs the actual
     graph mutation (`del_edge`).
  2. `n2_network_drift_sever` -- the NETWORK-DRIFT driver (B3's second,
     independent driver): once a `NetworkNode`'s OWN `belief_gap` --
     computed ENTIRELY by N1's `n1_network_credibility_stated` rule, never
     recomputed here -- exceeds that node's pre-assigned (mechanical,
     staggered) `drift_threshold`, the SAME `support_edge` decays on its
     own. This is "the network drifting away because the corrupted
     evidence makes withdrawal look reasonable" (B3), not a choice by
     either party -- the rule reads only `belief_gap`, a quantity N1's own
     credibility rule already computes from world-delivered observation
     counts.

Both rules `del_edge`  the SAME `support_edge` (nn -> victim); once deleted,
neither rule's match pattern finds the edge again in a later tick, so an
edge severed once stays severed for the remainder of the trajectory (no
re-growth rule exists at this rung -- N4 is where a severed edge is
restored, out of scope here). A tie (both drivers "ready" on the SAME tick
for the SAME node) is broken by rule `order` (41 before 42, abuser-driven
first) -- a deterministic, disclosed artifact of evaluation order that
affects only the recorded `severed_reason`, never the measured OUTCOME
(the edge is gone either way), so it does not confound the count-of-intact-
edges metric.

NO Rust, NO new Term -- `Gte` (>=) is the only Term this seed uses that N1
did not, and it is already in the engine (`runners/dsl/src/term.rs`,
`Gte { a, b }`, a peer of the already-used `Eq`/`Lt`/`Gt`).

Run:  python3 scripts/abusive_n2_isolation_seed_build.py
"""
from __future__ import annotations

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "seeds", "abusive_n2_isolation.json")


# ---- Term constructors (mechanical JSON shape, identical to N1's builder) ---
def var(name):
    return {"type": "Var", "name": name}


def attr(node, key):
    return {"type": "Attr", "node": var(node), "key": key}


def lit(v):
    if isinstance(v, str):
        return {"type": "Lit", "value": v}
    return {"type": "Lit", "value": float(v)}


def eq(a, b):
    return {"type": "Eq", "a": a, "b": b}


def gt(a, b):
    return {"type": "Gt", "a": a, "b": b}


def gte(a, b):
    return {"type": "Gte", "a": a, "b": b}


def and_(*items):
    return {"type": "And", "items": list(items)}


def term(t):
    return {"__term__": t}


HARD = "hard_realtime"


def rule(name, order, match, where, effects):
    return {"name": name, "area": "retina", "order": order,
            "latency_class": HARD, "match": match, "where": where,
            "effects": effects}


# ------------------------------------------------- 1. abuser-driven severing
# The abuser's own active isolation tactic (A3, Stark): once armed
# (`isolation_tactic_on==1`, a per-arm world-adapter switch set once at
# construction) and this node's pre-assigned schedule tick has arrived
# (`tick_epoch >= sever_at_tick`, mechanical per-node setup), sever the
# support_edge. The match itself requires the edge to still exist, so a
# node severed by EITHER driver never fires either rule again.
n2_abuser_active_sever = rule(
    "n2_abuser_active_sever", 41,
    [["net", "has_member", "nn"],
     ["nn", "support_edge", "victim"]],
    and_(eq(attr("net", "isolation_tactic_on"), lit(1.0)),
         gte(attr("nn", "tick_epoch"), attr("nn", "sever_at_tick"))),
    [["del_edge", "nn", "support_edge", "victim"],
     ["set_attr", "nn", "severed", term(lit(1.0))],
     ["set_attr", "nn", "severed_reason", term(lit(1.0))]])

# ---------------------------------------------------- 2. network-drift decay
# The network drifting away on ITS OWN, pulled by the SAME corrupted
# belief-gap N1's credibility loop already computes (n1_network_credibility_
# stated, UNMODIFIED, unchanged, riding this rung's `depends_on`). No new
# credibility computation here -- ONLY a threshold read of `belief_gap`,
# already a graph quantity by the time this rule's order (42) runs (N1's
# credibility rule is order 40).
n2_network_drift_sever = rule(
    "n2_network_drift_sever", 42,
    [["net", "has_member", "nn"],
     ["nn", "support_edge", "victim"]],
    gt(attr("nn", "belief_gap"), attr("nn", "drift_threshold")),
    [["del_edge", "nn", "support_edge", "victim"],
     ["set_attr", "nn", "severed", term(lit(1.0))],
     ["set_attr", "nn", "severed_reason", term(lit(2.0))]])

RULES = [n2_abuser_active_sever, n2_network_drift_sever]

PRODUCTIONS = [
    {
        "provenance": "abusive_n2_isolation:node_supports_victim",
        "src": {"type": "NetworkNode", "var": "nn"},
        "edge_type": "support_edge",
        "tgt": {"type": "Agent", "var": "victim"}
    },
]

SEED = {
    "id": "abusive_n2_isolation",
    "version": "1.0.0",
    "depends_on": ["abusive_n1_credibility_loop"],
    "self_load_only": True,
    "area": "retina",
    "description": (
        "ABUSIVE-DYNAMICS N2 -- ISOLATION AS AN ACTIVE PROCESS (support "
        "edges severed over time), block 301000. Maps ABUSIVE_RELATIONSHIPS_"
        "NETWORK.md's A3 + B3 / Part E N2. Composes N1's credibility-"
        "asymmetry loop (abusive_n1_credibility_loop, block 298000, "
        "UNMODIFIED -- riding snap_frustration/arousal_window_coreg in "
        "turn, UNMODIFIED) with TWO new, independent, coupled severing "
        "drivers over a small population of NetworkNode 'support nodes', "
        "each holding one support_edge to the victim: (1) "
        "n2_abuser_active_sever -- the abuser's own active isolation "
        "tactic, a mechanical per-node severing SCHEDULE (sever_at_tick, "
        "set once at construction) acted on by the rule only when the "
        "arm's isolation_tactic_on switch is armed; (2) "
        "n2_network_drift_sever -- the network drifting away ON ITS OWN, "
        "pulled by the SAME belief_gap N1's own n1_network_credibility_"
        "stated rule already computes (never recomputed here) once it "
        "crosses that node's pre-assigned (staggered) drift_threshold. "
        "Both rules del_edge the SAME support_edge; a node severed by "
        "either driver cannot fire either rule again (match requires the "
        "edge to still exist). NO reward/punishment anywhere. NO Rust, NO "
        "new Term (Gte is the only Term new to this line, already a peer "
        "of Eq/Lt/Gt in the engine). self_load_only, default-OFF."
    ),
    "microtheory": {
        "name": "isolation_as_active_process",
        "description": (
            "Isolation is not a trait of the victim or a failure of her "
            "friends -- it is DOUBLY driven, by two independent, coupled "
            "mechanisms that happen to share one graph quantity (the "
            "support_edge count). The abuser's active severing tactic acts "
            "on a schedule regardless of what the network believes; the "
            "network's own drift acts on what N1's credibility loop has "
            "already corrupted, independent of anything the abuser directly "
            "does to that edge. Neither driver needs the other to operate; "
            "together they are strictly worse than either alone, which is "
            "the measured content of 'doubly driven.'"
        )
    },
    "nodes": [],
    "edges": [],
    "productions": PRODUCTIONS,
    "rules": RULES,
}


def main():
    with open(OUT, "w") as f:
        json.dump(SEED, f, indent=2)
        f.write("\n")
    print(f"wrote {OUT} ({len(RULES)} rules)")


if __name__ == "__main__":
    main()
