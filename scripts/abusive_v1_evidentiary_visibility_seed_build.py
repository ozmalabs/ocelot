#!/usr/bin/env python3
"""ABUSIVE-DYNAMICS V1 -- EVIDENTIARY VISIBILITY: DOES A DISCRETE,
VICTIM-INDEPENDENT INCIDENT TRACE PROTECT CREDIBILITY A PURELY DIFFUSE
PATTERN CANNOT EARN? -- seed builder (block 364000).

Authoring tool ONLY: it EMITS `seeds/abusive_v1_evidentiary_visibility.json`
(graph data) -- no agent decisions, no rule engine, no graph state. See
`docs/research/bigville/ABUSIVE_V1_EVIDENTIARY_VISIBILITY_PREREG.md` for the
full design rationale, and `docs/research/bigville/
ABUSIVE_RELATIONSHIPS_VISIBILITY_SCOPING.md` (Part B) for the mechanism
spec this seed builds EXACTLY.

V1 does NOT `depends_on` N1's own seed (`abusive_n1_credibility_loop`) --
it restates N1's own `n1_victim_entrainment` rule byte-identically as its
own `v1_victim_entrainment`, matching R3's own precedent of reading a
sibling rung's rule shape without depending on its file. Exactly TWO new
rules -- the smallest rule count in this entire line:

  1. `v1_victim_entrainment` -- a byte-identical restatement of N1's own
     `n1_victim_entrainment` (itself a byte-identical restatement of R2's
     `r2_victim_entrainment_via_frustration` / R3's
     `r3_victim_entrainment_solo`). Rides `snap_frustration` (block 242000)
     + `arousal_window_coreg` (block 239000), BOTH UNMODIFIED.
  2. `v1_network_credibility_incident_aware` -- ONE shared rule for the
     network's belief-update, serving BOTH of V1's arms (the ONLY
     difference between arms is whether the world adapter ever delivers a
     nonzero `seen_incident` -- Sec. B3 of the scoping doc):

         cred_abuser = charm_weight * seen_charm
                       - incident_discount_weight * seen_incident
         cred_victim = claim_weight * seen_victim_claim
                       - instability_discount_weight * seen_victim_unstable   (UNCHANGED from N1)
         belief_gap  = cred_abuser - cred_victim

     `seen_incident` is a NEW NetworkNode observation count, discounting
     the ABUSER's credibility term (never boosting the victim's claim
     term) -- a deliberate, load-bearing design choice (scoping doc Part
     B2 / Part F "Smuggled Premise 4"): a discrete incident trace is
     direct evidence AGAINST the abuser's conduct, not evidence that the
     victim is a more believable narrator. `cred_victim`'s own formula is
     reused byte-for-byte, unmodified, from N1.

V1 does NOT restate N1's own `n1_abuser_stated_charm` rule. That rule,
under `deception_on=1` (fixed ON in every one of N1's own arms), always
evaluates its `IfThenElse` to the `then` branch -- `stated_charm=1.0`
UNCONDITIONALLY, regardless of any other state (confirmed by reading the
rule directly, not assumed). Since V1 has only ONE dyad topology (no
private-face-control arm, no non-dysregulated-control arm -- V1's dyad is
byte-identical to N1's own BASELINE in both of V1's arms), this
computation is a STRUCTURAL CONSTANT at V1's own operating point, so V1's
world adapter delivers `seen_charm += 1.0` directly, every tick, as a
mechanical world fact (matching `seen_victim_claim`'s own already-
established constant-delivery precedent in N1) -- numerically
BYTE-IDENTICAL to what the restated rule would have produced, with one
fewer rule. This keeps V1's own new-rule count at exactly two, per Part E
of the scoping doc.

NO Rust, NO new Term -- every Term below (Plus/Minus/Times/Attr/Var/Lit/
Eq/Lt/And) is already in the engine and already used by
`snap_frustration.json` / `arousal_window_coreg.json` /
`abusive_n1_credibility_loop.json`.

Run:  python3 scripts/abusive_v1_evidentiary_visibility_seed_build.py
"""
from __future__ import annotations

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "seeds", "abusive_v1_evidentiary_visibility.json")


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


def term(t):
    return {"__term__": t}


HARD = "hard_realtime"


def rule(name, order, match, where, effects):
    return {"name": name, "area": "retina", "order": order,
            "latency_class": HARD, "match": match, "where": where,
            "effects": effects}


# --------------------------------------------------------- 1. dyad entrainment
# BYTE-IDENTICAL restatement of N1's own n1_victim_entrainment (itself a
# byte-identical restatement of R2's/R3's own formula): one coreg pull
# (abuser) + one selfreg pull, combined off the tick-start arousal, written
# to `frustration` so snap_arousal_track (unmodified, order 5) commits it to
# `arousal`. No has_outside_regulator gating -- V1 has no outside-regulator
# arm, matching N1's own scope exactly.
v1_frustration_term = term(
    minus(
        plus(attr("vaff", "arousal"),
             times(attr("vaff", "k_co"), minus(attr("aaff", "arousal"), attr("vaff", "arousal"))),
             times(attr("vaff", "k_self"), minus(attr("vaff", "setpoint"), attr("vaff", "arousal")))),
        attr("vaff", "setpoint")))

v1_victim_entrainment = rule(
    "v1_victim_entrainment", 8,
    [["victim", "has_affective_state", "vaff"],
     ["victim", "attended_by", "abuser"],
     ["abuser", "has_affective_state", "aaff"]],
    and_(lt(attr("vaff", "pcr_epoch"), attr("vaff", "tick_epoch")),
         eq(attr("aaff", "is_abuser"), lit(1.0))),
    [["set_attr", "vaff", "frustration", v1_frustration_term],
     ["set_attr", "vaff", "pcr_epoch", term(attr("vaff", "tick_epoch"))]])

# -------------------------------------------------- 2. network credibility ----
# THE INCIDENT-AWARE CREDIBILITY DECISION (scoping doc Part B2). ONE shared
# rule for every ordinary NetworkNode, serving BOTH of V1's arms -- the ONLY
# difference between arms is whether the world adapter ever delivers a
# nonzero seen_incident (Part B3). cred_victim is UNCHANGED from N1's own
# formula; cred_abuser gains ONE new discount term keyed on seen_incident,
# a discrete, victim-independent observable -- direct evidence AGAINST the
# abuser's conduct, never evidence FOR the victim's own claim (Part B2 /
# Part F Smuggled Premise 4 -- a deliberate, load-bearing design choice, not
# simplified away).
cred_victim_term = minus(
    times(attr("nn", "claim_weight"), attr("nn", "seen_victim_claim")),
    times(attr("nn", "instability_discount_weight"), attr("nn", "seen_victim_unstable")))

cred_abuser_term = minus(
    times(attr("nn", "charm_weight"), attr("nn", "seen_charm")),
    times(attr("nn", "incident_discount_weight"), attr("nn", "seen_incident")))

# where: Eq(1.0, 1.0) -- an "always match, no discriminating condition"
# `where` (V1 has no observes_private-style split, so every ordinary node
# takes the SAME formula). NOT `where: None` -- an engine finding surfaced
# while building this rule (documented in the prereg): a rule with a NULL
# `where` fires correctly on the FIRST full run_rules() pass but is not
# re-triggered by the engine's incremental dirty-tracking on a SUBSEQUENT
# attribute change (confirmed directly against the real graph: a `where:
# None` rule's effects go stale after a `set_attr` that only the rule's
# EFFECTS, not a `where` clause, reads). A trivially-true `where` restores
# correct incremental re-firing. This is an ALREADY-ESTABLISHED idiom in
# this codebase for exactly this situation
# (`seeds/bigville_loud_comm.json`'s `lo_choose_loudness` rule uses the
# identical `Eq(Lit(1.0), Lit(1.0))` shape), not a new pattern invented here.
v1_network_credibility_incident_aware = rule(
    "v1_network_credibility_incident_aware", 40,
    [["net", "has_member", "nn"]],
    eq(lit(1.0), lit(1.0)),
    [["set_attr", "nn", "cred_abuser", term(cred_abuser_term)],
     ["set_attr", "nn", "cred_victim", term(cred_victim_term)],
     ["set_attr", "nn", "belief_gap", term(minus(cred_abuser_term, cred_victim_term))]])

RULES = [v1_victim_entrainment, v1_network_credibility_incident_aware]

PRODUCTIONS = [
    {
        "provenance": "abusive_v1_evidentiary_visibility:victim_attended_by_abuser",
        "src": {"type": "Agent", "var": "victim"},
        "edge_type": "attended_by",
        "tgt": {"type": "Agent", "var": "abuser"}
    },
    {
        "provenance": "abusive_v1_evidentiary_visibility:network_has_member",
        "src": {"type": "Network", "var": "net"},
        "edge_type": "has_member",
        "tgt": {"type": "NetworkNode", "var": "nn"}
    },
    {
        "provenance": "abusive_v1_evidentiary_visibility:node_observes_stated",
        "src": {"type": "NetworkNode", "var": "nn"},
        "edge_type": "observes_stated",
        "tgt": {"type": "Agent", "var": "abuser"}
    },
    {
        "provenance": "abusive_v1_evidentiary_visibility:node_observes_victim",
        "src": {"type": "NetworkNode", "var": "nn"},
        "edge_type": "observes_victim",
        "tgt": {"type": "Agent", "var": "victim"}
    },
]

SEED = {
    "id": "abusive_v1_evidentiary_visibility",
    "version": "1.0.0",
    "depends_on": ["snap_frustration", "arousal_window_coreg"],
    "self_load_only": True,
    "area": "retina",
    "description": (
        "ABUSIVE-DYNAMICS V1 -- EVIDENTIARY VISIBILITY (block 364000). Does "
        "a discrete, victim-independent incident trace protect credibility "
        "a purely diffuse pattern cannot earn? (ABUSIVE_RELATIONSHIPS_"
        "VISIBILITY_SCOPING.md Part E, V1). Composes N1's own dyad "
        "(snap_frustration block 242000 + arousal_window_coreg block "
        "239000, BOTH UNMODIFIED) via a byte-identical restatement of N1's "
        "own n1_victim_entrainment rule (v1_victim_entrainment) -- N1's own "
        "seed (abusive_n1_credibility_loop) is READ for this rule's SHAPE, "
        "never depended on or edited, matching R3's own convention against "
        "R2. v1_network_credibility_incident_aware extends N1's own "
        "credibility-comparison rule SHAPE by exactly one new discount "
        "term: cred_abuser = charm_weight*seen_charm - "
        "incident_discount_weight*seen_incident (a NEW, discrete, "
        "victim-independent observable -- direct evidence AGAINST the "
        "abuser's conduct, deliberately wired to discount the ABUSER's "
        "credibility term rather than boost the VICTIM's claim term -- "
        "conflating 'there is evidence of what he did' with 'she is more "
        "believable' would smuggle back the exact victim-credibility "
        "framing this line dissolves). cred_victim is UNCHANGED from N1's "
        "own formula (claim_weight*seen_victim_claim - "
        "instability_discount_weight*seen_victim_unstable). ONE shared rule "
        "serves BOTH of V1's arms (INCIDENT_VISIBLE / INCIDENT_INVISIBLE) "
        "-- the only difference between arms is whether the world adapter "
        "ever delivers a nonzero seen_incident, mechanically, under the "
        "SAME counter-DELTA-observer idiom R3's own r3_prior_track_narrow/"
        "_widen already established (wot.narrow_count > wot.pn_last_narrow) "
        "-- never a read of the transient in_snap/snapped flags (N1's own "
        "Sec. 2.1 finding). seen_charm is delivered as a mechanical "
        "constant (+=1.0/tick) rather than restating N1's own "
        "n1_abuser_stated_charm rule, because that rule, under "
        "deception_on=1 (fixed ON in every one of N1's own arms), always "
        "evaluates to stated_charm=1.0 unconditionally -- a structural "
        "constant at V1's own single-dyad operating point, reproduced "
        "byte-identically without the extra rule. "
        "v1_network_credibility_incident_aware's own `where` is a "
        "trivially-true Eq(1.0,1.0) (matching bigville_loud_comm.json's "
        "lo_choose_loudness idiom), not `where: None` -- an engine finding "
        "surfaced while building this rule: a null-where rule fires on the "
        "first full run_rules() pass but is not re-triggered by the "
        "engine's incremental dirty-tracking on a subsequent attribute "
        "change (confirmed directly against the real graph). NO reward/punishment "
        "anywhere. NO Rust, NO new Term (Plus/Minus/Times/Attr/Var/Lit/Eq/"
        "Lt/And only, all already used by snap_frustration/"
        "arousal_window_coreg/abusive_n1_credibility_loop). "
        "self_load_only, default-OFF."
    ),
    "microtheory": {
        "name": "evidentiary_visibility",
        "description": (
            "A network node's belief tracks only what evidence reaches it. "
            "The credibility-asymmetry loop N1 already validated does not "
            "change; what changes is whether ONE more channel of evidence "
            "-- a discrete, victim-independent trace of the abuser's own "
            "conduct -- ever reaches the network at all. The loop's cruelty "
            "in the diffuse-only case is not that the network judges "
            "unfairly; it is that a purely diffuse pattern of harm "
            "structurally produces no evidence of the kind an "
            "incident-shaped credibility rule can act on."
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
