#!/usr/bin/env python3
"""ABUSIVE-DYNAMICS U1 -- CONTEXT-DEPENDENT AFFECT, NO DECEPTION NODE AT ALL,
seed builder (block 310000).

Authoring tool ONLY: it EMITS `seeds/abusive_u1_context_affect.json` (graph
data) -- no agent decisions, no rule engine, no graph state. See
`docs/research/bigville/ABUSIVE_U1_CONTEXT_AFFECT_PREREG.md` for the full
design rationale. In brief: DELETES N1's `n1_abuser_stated_charm` (the
unconditional stated!=held broadcast) with NO REPLACEMENT DIVERGENCE NODE AT
ALL -- U1 has no `stated_charm`, no `deception_on`, no second face. Network
nodes observe the abuser's SAME true `frustration` value the private-face
insider already reads in N1 (`observes_held`), for EVERY node -- the only
question is WHICH TICKS that observation is credited on.

Self-contained restatement, matching U0's OWN established precedent (U0's own
provenance note: "the clean resolution, matching N1's OWN established
convention exactly ... self-contained restates N1's other ... rules ...
rather than depending on a sibling rung's seed file"). U1 restates N1's dyad
rule byte-identically (`u1_victim_entrainment`) and replaces
`n1_abuser_stated_charm` + `n1_network_credibility_stated`/`_private` with
exactly ONE new rule, `u1_network_credibility` -- unconditional across all
network nodes (there is no insider/outsider, stated/held split in U1 at all;
every node reads the SAME true state).

THE ONE DESIGN FINDING THAT SHAPED THE RULE (reported per the "shapes, not
numbers" / "report every finding" standing rule): a REWARD-ONLY accumulator
(count calm observations, ignore elevated ones -- N1's own `seen_charm`
formula, literally) is ANALYTICALLY GUARANTEED to bias the ALWAYS-OBSERVED
control's belief-gap upward relative to the CONTEXT-GATED arm's, never
downward -- observing on STRICTLY MORE ticks can only add non-negative reward
credit under a reward-only scheme, so the always-observed arm's raw calm-count
is a superset sum of the context-gated arm's and is guaranteed >=, making the
prereg's own falsification bar ("the always-observed arm must show the
belief-gap NOT favouring the abuser to the same degree") STRUCTURALLY
UNFALSIFIABLE in the wrong direction, independent of any empirical dynamics.
Piloted directly against the real graph (off-block seed 90000) BEFORE writing
this seed, confirmed exactly as predicted (a reward-only pilot construction
produced always-observed > context-gated, backwards). The fix: `cred_abuser`
is a SIGNED balance -- `charm_weight * (seen_charm - seen_elevated)` -- so an
elevated observation, when it IS witnessed, costs the abuser's credibility
exactly as much as a calm observation earns it. This is not a new invented
asymmetry; it is the MINIMAL correction that makes "observe the abuser's
actual frustration value directly" (as opposed to N1's one-sided BROADCAST)
an HONEST, unbiased sampling of a value that is sometimes high and sometimes
low, rather than a one-way ratchet that rewards exposure regardless of what
was actually seen.

`seen_charm`/`seen_elevated` are WORLD-ADAPTER-accumulated (mechanical
per-tick delivery of an observed graph fact -- abuser.frustration vs
recover_floor -- never a Python decision, exactly matching N1's own
`seen_harm_direct` precedent), gated on a MECHANICAL, PRE-DETERMINED per-tick
PHASE SCHEDULE (dyad-phase ticks: the tension trickle is armed, the SAME
world-delivered fact class R2/R3/N1 already use; network-phase ticks: the
trickle is NOT armed, and `snap_frustration`'s own unmodified LEAK constant
(242000, UNCHANGED) genuinely decays frustration toward baseline) -- a
counter-driven schedule, never a graph-state read, matching R1-R5's own
event-schedule convention. The CONTEXT_GATED arm credits observations ONLY on
network-phase ticks; the ALWAYS_OBSERVED arm (the failable control) credits
every tick regardless of phase. `attended_by` (the victim's dyad coupling)
stays STATIC across the whole trajectory (matching N1's BASELINE exactly,
`u1_victim_entrainment` unmodified) -- ONLY the trickle-arming / observation
window differs per phase, resolving PREREG's own Open Question #1 (see the
prereg for the full resolution).

NO Rust, NO new Term -- every Term below (Plus/Minus/Times/IfThenElse/Attr/
Var/Lit/Eq/Lt/And) is already in the engine and already used by
`snap_frustration.json` / `arousal_window_coreg.json` /
`abusive_n1_credibility_loop.json`.

Run:  python3 scripts/abusive_u1_context_affect_seed_build.py
"""
from __future__ import annotations

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "seeds", "abusive_u1_context_affect.json")


# ---- Term constructors (mechanical JSON shape, identical to N1's/U0's own) --
def var(name):
    return {"type": "Var", "name": name}


def attr(node, key):
    return {"type": "Attr", "node": var(node), "key": key}


def lit(v):
    if isinstance(v, str):
        return {"type": "Lit", "value": v}
    return {"type": "Lit", "value": float(v)}


def plus(*items):
    return {"type": "Plus", "items": list(items)}


def times(*items):
    return {"type": "Times", "items": list(items)}


def minus(a, b):
    return {"type": "Minus", "a": a, "b": b}


def eq(a, b):
    return {"type": "Eq", "a": a, "b": b}


def lt(a, b):
    return {"type": "Lt", "a": a, "b": b}


def and_(*items):
    return {"type": "And", "items": list(items)}


def term(t):
    return {"__term__": t}


HARD = "hard_realtime"


def rule(name, order, match, where, effects):
    return {"name": name, "area": "retina", "order": order,
            "latency_class": HARD, "match": match, "where": where,
            "effects": effects}


# --------------------------------------------------------- 1. dyad entrainment
# BYTE-IDENTICAL restatement of N1's n1_victim_entrainment (itself a
# byte-identical restatement of R2's/R3's own formula). attended_by is a
# STATIC per-trajectory topology choice (matching N1's BASELINE convention
# exactly) -- U1 does not toggle this edge; the phase schedule that
# distinguishes "dyad-coupled" from "network-context" ticks lives entirely in
# the WORLD ADAPTER's trickle-arming schedule (see prereg Sec. 2's resolution
# of Open Question #1), never in this rule.
u1_frustration_term = term(
    minus(
        plus(attr("vaff", "arousal"),
             times(attr("vaff", "k_co"), minus(attr("aaff", "arousal"), attr("vaff", "arousal"))),
             times(attr("vaff", "k_self"), minus(attr("vaff", "setpoint"), attr("vaff", "arousal")))),
        attr("vaff", "setpoint")))

u1_victim_entrainment = rule(
    "u1_victim_entrainment", 8,
    [["victim", "has_affective_state", "vaff"],
     ["victim", "attended_by", "abuser"],
     ["abuser", "has_affective_state", "aaff"]],
    and_(lt(attr("vaff", "pcr_epoch"), attr("vaff", "tick_epoch")),
         eq(attr("aaff", "is_abuser"), lit(1.0))),
    [["set_attr", "vaff", "frustration", u1_frustration_term],
     ["set_attr", "vaff", "pcr_epoch", term(attr("vaff", "tick_epoch"))]])

# -------------------------------------------- 2. the ONE credibility rule ----
# NO stated/held split -- every NetworkNode reads the SAME true state
# (observes_held, world-topology only; the rule itself reads nn's own local
# attrs, matching N1's own pattern). cred_abuser is a SIGNED balance
# (charm_weight * (seen_charm - seen_elevated)) -- see this file's own
# provenance note above for why a reward-only formula (N1's own shape,
# literally) is analytically guaranteed to bias the ALWAYS_OBSERVED control
# in the WRONG direction, and why the signed balance is the minimal fix.
# cred_victim is IDENTICAL to N1's own formula, unmodified.
cred_victim_term = minus(
    times(attr("nn", "claim_weight"), attr("nn", "seen_victim_claim")),
    times(attr("nn", "instability_discount_weight"), attr("nn", "seen_victim_unstable")))

cred_abuser_term = times(
    attr("nn", "charm_weight"),
    minus(attr("nn", "seen_charm"), attr("nn", "seen_elevated")))

u1_network_credibility = rule(
    "u1_network_credibility", 40,
    [["net", "has_member", "nn"]],
    eq(attr("nn", "credibility_on"), lit(1.0)),
    [["set_attr", "nn", "cred_abuser", term(cred_abuser_term)],
     ["set_attr", "nn", "cred_victim", term(cred_victim_term)],
     ["set_attr", "nn", "belief_gap", term(minus(cred_abuser_term, cred_victim_term))]])

RULES = [u1_victim_entrainment, u1_network_credibility]

PRODUCTIONS = [
    {
        "provenance": "abusive_u1_context_affect:victim_attended_by_abuser",
        "src": {"type": "Agent", "var": "victim"},
        "edge_type": "attended_by",
        "tgt": {"type": "Agent", "var": "abuser"}
    },
    {
        "provenance": "abusive_u1_context_affect:network_has_member",
        "src": {"type": "Network", "var": "net"},
        "edge_type": "has_member",
        "tgt": {"type": "NetworkNode", "var": "nn"}
    },
    {
        "provenance": "abusive_u1_context_affect:node_observes_held",
        "src": {"type": "NetworkNode", "var": "nn"},
        "edge_type": "observes_held",
        "tgt": {"type": "Agent", "var": "abuser"}
    },
    {
        "provenance": "abusive_u1_context_affect:node_observes_victim",
        "src": {"type": "NetworkNode", "var": "nn"},
        "edge_type": "observes_victim",
        "tgt": {"type": "Agent", "var": "victim"}
    },
]

SEED = {
    "id": "abusive_u1_context_affect",
    "version": "1.0.0",
    "depends_on": ["snap_frustration", "arousal_window_coreg"],
    "self_load_only": True,
    "area": "retina",
    "description": (
        "ABUSIVE-DYNAMICS U1 -- CONTEXT-DEPENDENT AFFECT, NO DECEPTION NODE "
        "AT ALL (block 310000). The sharpest no-intent rung of the "
        "unintentional/no-deliberate-deception companion dimension "
        "(ABUSIVE_RELATIONSHIPS_UNINTENTIONAL_SCOPING.md Part E, U1). "
        "DELETES N1's n1_abuser_stated_charm (the unconditional stated!=held "
        "broadcast) WITH NO REPLACEMENT DIVERGENCE NODE -- every network "
        "node reads the abuser's SAME true frustration value (observes_held, "
        "N1's own edge type, universal here, no stated/held split at all). "
        "Self-contained restatement matching U0's own precedent: "
        "u1_victim_entrainment is BYTE-IDENTICAL to N1's n1_victim_"
        "entrainment; u1_network_credibility REPLACES both of N1's "
        "credibility rules with ONE unconditional rule computing "
        "cred_abuser as a SIGNED balance (charm_weight*(seen_charm-"
        "seen_elevated)) rather than N1's reward-only count -- a signed "
        "balance is REQUIRED, not stylistic: piloted directly against the "
        "real graph, a reward-only formula (N1's own shape) analytically "
        "GUARANTEES the always-observed control's belief-gap is >= the "
        "context-gated arm's (observing more ticks can only add reward "
        "under a reward-only scheme), making the prereg's own failable "
        "control structurally unfalsifiable in the wrong direction "
        "independent of any empirical dynamics -- the signed balance fixes "
        "this by letting an elevated observation cost exactly what a calm "
        "one earns. seen_charm/seen_elevated are WORLD-ADAPTER-accumulated "
        "(mechanical per-tick delivery of frustration<=recover_floor or "
        ">recover_floor, never a Python decision), gated on a MECHANICAL, "
        "PRE-DETERMINED phase schedule (dyad-phase ticks: trickle armed; "
        "network-phase ticks: trickle NOT armed, snap_frustration's own "
        "unmodified LEAK genuinely decays frustration) -- a counter-driven "
        "schedule, never a graph-state read. attended_by stays STATIC "
        "across the whole trajectory (matching N1's BASELINE exactly). NO "
        "reward/punishment anywhere. NO Rust, NO new Term (Plus/Minus/"
        "Times/IfThenElse/Attr/Var/Lit/Eq/Lt/And only, all already used by "
        "snap_frustration/arousal_window_coreg/abusive_n1_credibility_"
        "loop). self_load_only, default-OFF."
    ),
    "microtheory": {
        "name": "context_dependent_affect_no_deception",
        "description": (
            "The abuser's calm face around the network is not a face at "
            "all -- there is no second, authored presentation anywhere in "
            "this construction. It is the SAME single frustration value "
            "R2/R3/N1's own leaky-integrate-fire mechanism already "
            "computes, sampled at a genuinely different moment: high "
            "while the relationship's own tension trickle is active, "
            "decaying via the mechanism's own LEAK constant once it is "
            "not. A network that happens to look only during the calm "
            "moments sees a calm abuser not because he presented one, but "
            "because that is when it looked."
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
