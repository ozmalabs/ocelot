#!/usr/bin/env python3
"""ABUSIVE-DYNAMICS N3 -- BELIEF PROPAGATION OF THE ABUSER'S LIES (social
contagion; a truth-anchor halts it), seed builder (block 304000).

Authoring tool ONLY: it EMITS `seeds/abusive_n3_belief_propagation.json`
(graph data) -- no agent decisions, no rule engine, no graph state. See
`docs/research/bigville/ABUSIVE_N3_BELIEF_PROPAGATION_PREREG.md` for the full
design rationale. In brief, N3 composes N1's credibility-asymmetry loop
(`abusive_n1_credibility_loop`, block 298000, UNMODIFIED -- riding
`snap_frustration`/`arousal_window_coreg` in turn, UNMODIFIED) with exactly
ONE new rule, `n3_peer_belief_update`, that propagates `belief_gap` from a
NetworkNode to its PEERS over a NEW `peer_of` edge type -- neighbour-to-
neighbour belief update, the genuinely new content this rung adds (N1's own
nodes are, by its own "Honest residuals", "five INDEPENDENT observers...no
neighbour-to-neighbour update" -- this rung is exactly that missing piece).

`n3_peer_belief_update` moves a node's `belief_gap` toward the MEAN of its
`peer_of`-neighbours' `belief_gap` (a leaky consensus pull, the SAME shape as
`n1_victim_entrainment`'s `k_co*(other.arousal - self.arousal)` pull, reused
not invented -- `Neighbours`/`Sum`/`Count`/`Div` compute the mean over
however many peers a node has, ENTIRELY in-graph, no new Rust). The rule
fires once per external tick (an epoch guard, `peer_epoch < tick_epoch`,
reused from `n1_victim_entrainment`'s own `pcr_epoch`/`tick_epoch` pattern)
and is ORDERED (35) to run BEFORE N1's credibility rules (order 40) within
the same `run_rules()` fixpoint: a node that ALSO has a direct observation
edge to the abuser (`observes_stated`/`observes_held`) has its `belief_gap`
RECOMPUTED from that direct evidence immediately afterward, in the SAME
pass, overwriting whatever the peer pull just wrote -- so a node's own
direct observation always has the final word for that tick, and a node with
NO direct observation edge (never matched by N1's credibility rules at all)
keeps whatever the peer pull computed. This single ordering fact is what
lets the SAME `peer_of` topology serve both arms (anchor / no-anchor) without
a topology change: the truth-anchor arm's ONLY difference is that one
indirect node ALSO carries an `observes_held` edge + `observes_private=1.0`
(reusing N1's OWN `n1_network_credibility_private` rule, UNMODIFIED, to pin
that node's belief every tick regardless of what its peers believe).

NO Rust, NO new Term (`Neighbours`/`Sum`/`Count`/`Div` are all already used
elsewhere in the tree, e.g. `bigville_council_gov.json`'s `cm_private_
decision`; `Plus`/`Minus`/`Times`/`Attr`/`Var`/`Lit`/`Lt` are already used by
`n1_victim_entrainment`/`n1_abuser_stated_charm`).

Run:  python3 scripts/abusive_n3_belief_propagation_seed_build.py
"""
from __future__ import annotations

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "seeds", "abusive_n3_belief_propagation.json")


# ---- Term constructors (mechanical JSON shape, identical to N1's/N2's builder)
def var(name):
    return {"type": "Var", "name": name}


def attr(node, key):
    return {"type": "Attr", "node": var(node), "key": key}


def lit(v):
    if isinstance(v, str):
        return {"type": "Lit", "value": v}
    return {"type": "Lit", "value": float(v)}


def lt(a, b):
    return {"type": "Lt", "a": a, "b": b}


def plus(*items):
    return {"type": "Plus", "items": list(items)}


def minus(a, b):
    return {"type": "Minus", "a": a, "b": b}


def times(*items):
    return {"type": "Times", "items": list(items)}


def div(a, b):
    return {"type": "Div", "a": a, "b": b}


def neighbours(node, edge_type):
    return {"type": "Neighbours", "node": var(node), "edge_type": edge_type, "any_type": False}


def count(source):
    return {"type": "Count", "source": source}


def sum_over(source, var_name, value):
    return {"type": "Sum", "source": source, "var_name": var_name, "value": value}


def term(t):
    return {"__term__": t}


HARD = "hard_realtime"


def rule(name, order, match, where, effects):
    return {"name": name, "area": "retina", "order": order,
            "latency_class": HARD, "match": match, "where": where,
            "effects": effects}


# --------------------------------------------------- neighbour-to-neighbour
# n3_peer_belief_update: the genuinely new content of N3 (ABUSIVE_
# RELATIONSHIPS_NETWORK.md B4 -- "each network node updates its reputation
# belief from its neighbours' beliefs"). A node with at least one outgoing
# `peer_of` edge pulls its `belief_gap` toward the MEAN of its peers'
# `belief_gap`, at rate `peer_pull_rate` (a per-node constant, the SAME
# leaky-pull SHAPE as n1_victim_entrainment's k_co term -- reused, not a new
# knob family). Fires once per external tick (peer_epoch < tick_epoch guard,
# n1_victim_entrainment's own pcr_epoch/tick_epoch pattern) and is ordered
# (35) strictly BEFORE N1's credibility rules (order 40), so a node that ALSO
# observes the abuser directly gets its belief_gap OVERWRITTEN by that direct
# evidence later in the SAME pass -- direct observation always has the final
# word; peer contagion is what's left for a node with NO direct evidence.
_avg_peer_belief = div(
    sum_over(neighbours("nn", "peer_of"), "pp", attr("pp", "belief_gap")),
    count(neighbours("nn", "peer_of")))

n3_peer_belief_update = rule(
    "n3_peer_belief_update", 35,
    [["net", "has_member", "nn"],
     ["nn", "peer_of", "pp0"]],
    lt(attr("nn", "peer_epoch"), attr("nn", "tick_epoch")),
    [["set_attr", "nn", "belief_gap",
      term(plus(attr("nn", "belief_gap"),
                times(attr("nn", "peer_pull_rate"),
                      minus(_avg_peer_belief, attr("nn", "belief_gap")))))],
     ["set_attr", "nn", "peer_epoch", term(attr("nn", "tick_epoch"))]])

RULES = [n3_peer_belief_update]

PRODUCTIONS = [
    {
        "provenance": "abusive_n3_belief_propagation:node_peer_of_node",
        "src": {"type": "NetworkNode", "var": "nn"},
        "edge_type": "peer_of",
        "tgt": {"type": "NetworkNode", "var": "pp"}
    },
]

SEED = {
    "id": "abusive_n3_belief_propagation",
    "version": "1.0.0",
    "depends_on": ["abusive_n1_credibility_loop"],
    "self_load_only": True,
    "area": "retina",
    "description": (
        "ABUSIVE-DYNAMICS N3 -- BELIEF PROPAGATION OF THE ABUSER'S LIES "
        "(social contagion; a truth-anchor halts it), block 304000. Maps "
        "ABUSIVE_RELATIONSHIPS_NETWORK.md's A1/A8/A9 + B4 / Part E N3. "
        "Composes N1's credibility-asymmetry loop (abusive_n1_credibility_"
        "loop, block 298000, UNMODIFIED -- riding snap_frustration/arousal_"
        "window_coreg in turn, UNMODIFIED) with exactly ONE new rule, "
        "n3_peer_belief_update, that propagates belief_gap over a NEW "
        "peer_of edge type -- a node with no direct observation edge to the "
        "abuser forms its belief ENTIRELY from the mean of its peers' "
        "belief_gap (Neighbours/Sum/Count/Div, in-graph, no new Rust), a "
        "leaky pull toward the peer mean at rate peer_pull_rate (the SAME "
        "shape as n1_victim_entrainment's k_co pull, reused). Ordered "
        "(order 35) strictly BEFORE N1's credibility rules (order 40) so a "
        "node that ALSO observes the abuser directly (observes_stated/"
        "observes_held) has that direct evidence OVERWRITE the peer pull in "
        "the SAME run_rules() pass -- direct observation always wins; peer "
        "contagion is what is left for a node with none. The SAME peer_of "
        "topology serves BOTH the anchor and no-anchor arms: the anchor arm "
        "additionally gives ONE indirect node an observes_held edge + "
        "observes_private=1.0 (reusing N1's OWN n1_network_credibility_"
        "private rule, UNMODIFIED, to pin that node's belief every tick to "
        "the uncorrupted, victim-favouring formula regardless of what its "
        "peers believe). NO reward/punishment anywhere. NO Rust, NO new Term "
        "(Neighbours/Sum/Count/Div are all already used elsewhere in the "
        "tree, e.g. bigville_council_gov.json's cm_private_decision). "
        "self_load_only, default-OFF."
    ),
    "microtheory": {
        "name": "belief_propagation_contagion",
        "description": (
            "A network node with NO direct line to the abuser is not "
            "forming an independent judgement -- it has no evidence of its "
            "own to judge FROM. Its belief is entirely a leaky average of "
            "what its peers already believe, which is itself either direct "
            "(corrupted) observation or ANOTHER peer average one hop "
            "further out. A consensus that traces back through this chain "
            "to one corrupted root is a contagion, not N independent "
            "corroborations, even though every single hop is an ordinary, "
            "locally-rational leaky pull toward what one's neighbours "
            "believe. A truth-anchor works by giving one node in the chain "
            "a belief that is NOT a function of its peers at all -- pinned "
            "by a direct, uncorrupted observation -- so the chain has a "
            "point where the contagion's own logic (trust what's around "
            "you) stops reproducing the corruption."
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
