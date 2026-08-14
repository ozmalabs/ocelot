#!/usr/bin/env python3
"""ABUSIVE-DYNAMICS N1 -- THE TWO-FACED ABUSER + THE CREDIBILITY-ASYMMETRY
LOOP, seed builder (block 298000).

Authoring tool ONLY: it EMITS `seeds/abusive_n1_credibility_loop.json` (graph
data) -- no agent decisions, no rule engine, no graph state. See
`docs/research/bigville/ABUSIVE_N1_CREDIBILITY_LOOP_PREREG.md` for the full
design rationale. In brief, this seed composes TWO already-built substrates,
adding exactly FOUR new rules:

  1. `n1_victim_entrainment` -- the dyad half. BYTE-IDENTICAL formula to R2's
     own `r2_victim_entrainment_via_frustration` / R3's
     `r3_victim_entrainment_solo` (block 286000/289000, restated here
     self-contained, riding `snap_frustration` (242000) + `arousal_window_coreg`
     (239000) UNMODIFIED, exactly as R3 restated R2's own rule rather than
     depending on a sibling rung's seed file). This is the victim's
     dysregulation symptom state (window/arousal) -- the OBSERVABLE the
     network's belief-update reads as "presents unstable."
  2. `n1_abuser_stated_charm` -- the SECOND audience (B1 of
     ABUSIVE_RELATIONSHIPS_NETWORK.md): the 234000 `stated!=held` atom,
     restated in the SAME shape `bigville_drama_social.json`'s
     `bd_john_public_face` (block 245000) already uses for exactly this
     purpose ("the 234000 readable stated!=held deception atom pointed at an
     AUDIENCE"). Under `deception_on`, the abuser STATES charm
     (`stated_charm=1`) regardless of its HELD state (whether `frustration`
     is presently above `recover_floor` -- `snap_frustration`'s own,
     unmodified threshold for "still genuinely elevated"; `in_snap`/
     `snapped` were found, empirically, to be transient WITHIN one
     `run_rules()` fixpoint pass at these frozen constants, so this rule
     reads the persistent `frustration`/`recover_floor` comparison
     instead); with the split collapsed (`deception_on=0`) the stated face
     reveals the held state truthfully. The abuser's held-intent-toward-the-
     victim (harm/control) is `snap_frustration`'s own, unmodified,
     already-gated mechanism -- no new rule needed for that half; the
     victim-facing "honeymoon" is `snap_frustration`'s own unmodified
     discharge/recover phase (the abuser's arousal relaxing after a snap),
     already built, reused unchanged.
  3/4. `n1_network_credibility_stated` / `n1_network_credibility_private` --
     the multi-node reputation belief-update surface. Modelled DIRECTLY on
     `bigville_drama_social.json`'s `bd_villager_backs` (block 245000,
     explicitly named there as "the abuse-line A5/B2 credibility asymmetry"),
     which already answers OPEN QUESTION #1 of ABUSIVE_RELATIONSHIPS_NETWORK.md
     ("is a multi-node reputation-belief-update surface already materialised?"
     -- YES, `bd_villager_backs` IS one, at block 245000). N1's version
     computes, per NetworkNode: `cred_abuser` from the abuser's STATED-FACE
     observation count (charm, UNDISCOUNTED -- A4/A7 himpathy: a charming
     public face is read at face value) and `cred_victim` from the victim's
     claim count MINUS an INSTABILITY-keyed discount (A5's corroborated
     nuance, stated precisely: NOT "distress -> disbelief" but "presentation
     read as unstable/incoherent/disproportionate -> discount" -- the
     discount term is `instability_discount_weight * seen_victim_unstable`,
     driven by the victim's OWN `dysregulated` observable from rule 1, never
     by the victim's raw arousal level or by the victim simply being upset).
     ONE network node (the private-face-control's "insider", `observes_
     private=1`) instead reads the abuser's TRUE held state directly
     (`seen_harm_direct`, accumulated from `frustration > recover_floor` --
     an UNCORRUPTED observable) and its `cred_abuser` term is NEGATIVE in that count instead
     of positive -- the mechanical construction of the private-face failable
     control (ABUSIVE_RELATIONSHIPS_NETWORK.md N1's own text: "a network node
     with a direct edge to the abuser's held-intent"). `belief_gap =
     cred_abuser - cred_victim` is the headline metric.

`charm_weight == claim_weight` (both 1.0) is a DELIBERATE, disclosed choice:
NO a priori credibility prior is baked in favouring the abuser (himpathy, A7,
is represented only insofar as the charm observation goes UNDISCOUNTED while
the claim is discounted -- not via an extra thumb-on-the-scale constant). The
ENTIRE belief-gap asymmetry in the baseline arm falls out of the
instability-keyed discount alone -- the stronger, more falsifiable form of
the claim.

The observation COUNTS (`seen_charm`/`seen_harm_direct`/`seen_victim_claim`/
`seen_victim_unstable`) are WORLD-ADAPTER-accumulated (mechanical per-tick
delivery of an observed graph fact), exactly matching `bd_villager_backs`'s
own precedent ("the observation counts are adapter-accumulated (mechanical);
the DECISION is this rule"). The DECISION -- what a node believes given what
it observed -- is entirely these two rules.

NO Rust, NO new Term -- every Term below (Plus/Minus/Times/IfThenElse/Attr/
Var/Lit/Eq/Lt/And) is already in the engine and already used by
`snap_frustration.json` / `arousal_window_coreg.json` /
`bigville_drama_social.json`.

Run:  python3 scripts/abusive_n1_credibility_loop_seed_build.py
"""
from __future__ import annotations

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "seeds", "abusive_n1_credibility_loop.json")


# ---- Term constructors (mechanical JSON shape, identical to prior rungs) -----
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


def ite(cond, then, other):
    return {"type": "IfThenElse", "cond": cond, "then": then, "other": other}


def gt(a, b):
    return {"type": "Gt", "a": a, "b": b}


def term(t):
    return {"__term__": t}


HARD = "hard_realtime"


def rule(name, order, match, where, effects):
    return {"name": name, "area": "retina", "order": order,
            "latency_class": HARD, "match": match, "where": where,
            "effects": effects}


# --------------------------------------------------------- 1. dyad entrainment
# BYTE-IDENTICAL formula to R2's r2_victim_entrainment_via_frustration / R3's
# r3_victim_entrainment_solo: one coreg pull (abuser) + one selfreg pull,
# combined off the tick-start arousal, written to `frustration` so
# snap_arousal_track (unmodified, order 5) commits it to `arousal`. No
# has_outside_regulator gating -- N1 has no outside-regulator arm; the
# non-dysregulated-victim control simply omits the attended_by edge (mechanical
# world-adapter topology choice, no rule needed for that half).
n1_frustration_term = term(
    minus(
        plus(attr("vaff", "arousal"),
             times(attr("vaff", "k_co"), minus(attr("aaff", "arousal"), attr("vaff", "arousal"))),
             times(attr("vaff", "k_self"), minus(attr("vaff", "setpoint"), attr("vaff", "arousal")))),
        attr("vaff", "setpoint")))

n1_victim_entrainment = rule(
    "n1_victim_entrainment", 8,
    [["victim", "has_affective_state", "vaff"],
     ["victim", "attended_by", "abuser"],
     ["abuser", "has_affective_state", "aaff"]],
    and_(lt(attr("vaff", "pcr_epoch"), attr("vaff", "tick_epoch")),
         eq(attr("aaff", "is_abuser"), lit(1.0))),
    [["set_attr", "vaff", "frustration", n1_frustration_term],
     ["set_attr", "vaff", "pcr_epoch", term(attr("vaff", "tick_epoch"))]])

# ------------------------------------------------- 2. the second audience ----
# THE PUBLIC FACE (234000 stated!=held with an audience, restated in
# bd_john_public_face's own shape): under deception_on, the abuser STATES
# charm regardless of its HELD state (frustration > recover_floor,
# snap_frustration's own, unmodified "still genuinely elevated" threshold).
# With the split collapsed, the stated face reveals the held state. The
# DECEPTION is the readable gap frustration>recover_floor & stated_charm=1.
n1_stated_charm_term = term(
    ite(eq(attr("aaff", "deception_on"), lit(1.0)),
        lit(1.0),
        ite(gt(attr("aaff", "frustration"), attr("aaff", "recover_floor")),
            lit(0.0), lit(1.0))))

n1_abuser_stated_charm = rule(
    "n1_abuser_stated_charm", 21,
    [["abuser", "has_affective_state", "aaff"]],
    eq(attr("aaff", "is_abuser"), lit(1.0)),
    [["set_attr", "aaff", "stated_charm", n1_stated_charm_term]])

# -------------------------------------------------- 3/4. network credibility
# THE CREDIBILITY DECISION (abuse-line A5/B2 asymmetry, modelled directly on
# bd_villager_backs). cred_abuser (stated-observing node) = charm_weight *
# seen_charm (the charming public face, UNDISCOUNTED). cred_victim (both node
# kinds) = claim_weight*seen_victim_claim - instability_discount_weight *
# seen_victim_unstable (the victim's TRUE claim, DISCOUNTED by the observed
# INSTABILITY count -- not by raw distress, A5's corroborated nuance).
# belief_gap = cred_abuser - cred_victim. The observation counts are
# adapter-accumulated (mechanical); the DECISION is these two rules.
cred_victim_term_full = minus(
    times(attr("nn", "claim_weight"), attr("nn", "seen_victim_claim")),
    times(attr("nn", "instability_discount_weight"), attr("nn", "seen_victim_unstable")))

# -- stated-observing node (baseline arm + private-face-control's outsiders +
#    non-dysregulated-control's nodes): cred_abuser from the STATED face only.
cred_abuser_term_stated = times(attr("nn", "charm_weight"), attr("nn", "seen_charm"))

n1_network_credibility_stated = rule(
    "n1_network_credibility_stated", 40,
    [["net", "has_member", "nn"]],
    eq(attr("nn", "observes_private"), lit(0.0)),
    [["set_attr", "nn", "cred_abuser", term(cred_abuser_term_stated)],
     ["set_attr", "nn", "cred_victim", term(cred_victim_term_full)],
     ["set_attr", "nn", "belief_gap", term(minus(cred_abuser_term_stated, cred_victim_term_full))]])

# -- private-face node (the failable control: a DIRECT edge to the abuser's
#    held state, e.g. observes_held -> abuser's AffectiveState): cred_abuser
#    from the TRUE held-harm count (frustration>recover_floor ticks), NEGATIVE -- an
#    uncorrupted observable should NOT reward the abuser's credibility.
cred_abuser_term_private = minus(lit(0.0), times(attr("nn", "harm_discount_weight"), attr("nn", "seen_harm_direct")))

n1_network_credibility_private = rule(
    "n1_network_credibility_private", 40,
    [["net", "has_member", "nn"]],
    eq(attr("nn", "observes_private"), lit(1.0)),
    [["set_attr", "nn", "cred_abuser", term(cred_abuser_term_private)],
     ["set_attr", "nn", "cred_victim", term(cred_victim_term_full)],
     ["set_attr", "nn", "belief_gap", term(minus(cred_abuser_term_private, cred_victim_term_full))]])

RULES = [n1_victim_entrainment, n1_abuser_stated_charm,
         n1_network_credibility_stated, n1_network_credibility_private]

PRODUCTIONS = [
    {
        "provenance": "abusive_n1_credibility_loop:victim_attended_by_abuser",
        "src": {"type": "Agent", "var": "victim"},
        "edge_type": "attended_by",
        "tgt": {"type": "Agent", "var": "abuser"}
    },
    {
        "provenance": "abusive_n1_credibility_loop:network_has_member",
        "src": {"type": "Network", "var": "net"},
        "edge_type": "has_member",
        "tgt": {"type": "NetworkNode", "var": "nn"}
    },
    {
        "provenance": "abusive_n1_credibility_loop:node_observes_stated",
        "src": {"type": "NetworkNode", "var": "nn"},
        "edge_type": "observes_stated",
        "tgt": {"type": "Agent", "var": "abuser"}
    },
    {
        "provenance": "abusive_n1_credibility_loop:node_observes_held",
        "src": {"type": "NetworkNode", "var": "nn"},
        "edge_type": "observes_held",
        "tgt": {"type": "Agent", "var": "abuser"}
    },
    {
        "provenance": "abusive_n1_credibility_loop:node_observes_victim",
        "src": {"type": "NetworkNode", "var": "nn"},
        "edge_type": "observes_victim",
        "tgt": {"type": "Agent", "var": "victim"}
    },
]

SEED = {
    "id": "abusive_n1_credibility_loop",
    "version": "1.0.0",
    "depends_on": ["snap_frustration", "arousal_window_coreg"],
    "self_load_only": True,
    "area": "retina",
    "description": (
        "ABUSIVE-DYNAMICS N1 -- THE TWO-FACED ABUSER + THE CREDIBILITY-"
        "ASYMMETRY LOOP (block 298000). The NETWORK dimension's headline "
        "rung (ABUSIVE_RELATIONSHIPS_NETWORK.md Part E, N1), composing TWO "
        "already-built substrates: (i) the dyad line's abuser "
        "(snap_frustration, block 242000, UNMODIFIED) + victim "
        "(arousal_window_coreg, block 239000, UNMODIFIED) entrainment, "
        "restated byte-identically from R2/R3's own established formula "
        "(n1_victim_entrainment); (ii) the 234000 stated!=held readable-"
        "deception atom pointed at a SECOND audience (n1_abuser_stated_"
        "charm), restated in the exact shape bigville_drama_social.json's "
        "bd_john_public_face (block 245000) already established for "
        "precisely this purpose, and the multi-node reputation belief-"
        "update surface bigville_drama_social.json's bd_villager_backs "
        "(also block 245000) already established -- ANSWERING OPEN "
        "QUESTION #1 of ABUSIVE_RELATIONSHIPS_NETWORK.md (a multi-node "
        "reputation-belief-update surface already exists, at block "
        "245000; N1 reuses its RULE SHAPE, self-contained, rather than "
        "depending on a sibling demo's seed). n1_network_credibility_"
        "stated/private compute, per NetworkNode, cred_abuser (the "
        "abuser's charming public face, UNDISCOUNTED -- A4/A7 himpathy) "
        "and cred_victim (the victim's claim, DISCOUNTED by the OBSERVED "
        "INSTABILITY count -- A5's corroborated nuance: presentation READ "
        "AS unstable is discounted, never raw distress itself). ONE "
        "network node (observes_private=1, the failable private-face "
        "control) reads the abuser's TRUE held state directly instead of "
        "its stated face, and its cred_abuser term is NEGATIVE in that "
        "count -- an uncorrupted observable does not reward the abuser. "
        "charm_weight==claim_weight==1.0 (disclosed: no a priori prior "
        "tilt is baked in; the entire baseline belief-gap falls out of "
        "the instability-keyed discount alone). Observation counts "
        "(seen_charm/seen_harm_direct/seen_victim_claim/seen_victim_"
        "unstable) are WORLD-ADAPTER-accumulated (mechanical per-tick "
        "delivery of an observed graph fact -- victim.dysregulated, "
        "abuser.stated_charm, abuser.frustration/recover_floor -- never a "
        "Python decision), "
        "exactly matching bd_villager_backs' own precedent. NO reward/"
        "punishment anywhere. NO Rust, NO new Term (Plus/Minus/Times/"
        "IfThenElse/Attr/Var/Lit/Eq/Lt/And only, all already used by "
        "snap_frustration/arousal_window_coreg/bigville_drama_social). "
        "self_load_only, default-OFF."
    ),
    "microtheory": {
        "name": "credibility_asymmetry_loop",
        "description": (
            "The credibility-asymmetry loop is not a new mechanism -- it is "
            "R2/R3's own abuser/victim dyad, feeding its dysregulation "
            "symptom (never its cause) into bigville_drama_social's own "
            "credibility-comparison rule shape as the discount term. A "
            "network node reads only what is observable to it (a stated "
            "face, a presentation); its belief tracks those observables "
            "faithfully. The loop's cruelty is not a flaw in the network's "
            "inference -- it is what CORRUPTED observables produce when "
            "fed into a mechanism that is otherwise doing correct Bayesian "
            "bookkeeping."
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
