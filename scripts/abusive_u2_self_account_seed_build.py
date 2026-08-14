#!/usr/bin/env python3
"""ABUSIVE-DYNAMICS U2 -- SELF-SERVING SELF-ACCOUNT, SINCERELY HELD, NO
STATED-VS-HELD SPLIT, seed builder (block 306000).

Authoring tool ONLY: it EMITS `seeds/abusive_u2_self_account.json` (graph
data) -- no agent decisions, no rule engine, no graph state. See
`docs/research/bigville/ABUSIVE_U2_SELF_ACCOUNT_PREREG.md` for the full
design rationale. In brief: DELETES N1's `n1_abuser_stated_charm` (the
unconditional stated!=held broadcast) and replaces it with ONE rule computing
`SelfAccount.magnitude` from the abuser's own true `frustration` (block
242000, unmodified) via a declared `minimization_discount` constant --
`magnitude = minimization_discount * frustration`. There is NO second,
separately-tracked "true" value the abuser is hiding: `SelfAccount.magnitude`
IS what the abuser sincerely believes happened, computed once, held once, and
reported SINCERELY to the network (this is Bandura's moral disengagement /
Henning & Holdford's minimization / Baumeister's self-serving narrative
construction -- A1/A2/A6 of the scoping doc -- composed as ONE declared
discount, never a goal-evaluated selection among candidate narratives; there
is no Argmax, no Appraisal, no choice mechanism anywhere in this rung).

Self-contained restatement, matching U0's/U1's own established precedent:
`u2_victim_entrainment` is BYTE-IDENTICAL to N1's `n1_victim_entrainment`.
`u2_network_credibility` replaces BOTH of N1's credibility rules with ONE
unconditional rule reading each NetworkNode's `seen_mild`/`seen_severe`
observation counts.

THE ANALYTICAL-BIAS HAZARD FOUND AND FIXED BEFORE THIS SEED WAS LOCKED
(the SAME class of hazard U1's own prereg found and fixed, reported per the
"shapes, not numbers" / "report every finding" standing rule): a REWARD-ONLY
`cred_abuser` (only accumulate credit when the self-account reads "mild",
literally N1's own `charm_weight*seen_charm` shape) makes `cred_abuser >= 0`
BY CONSTRUCTION for every arm, regardless of `minimization_discount`. Because
`cred_victim` is, under this dyad's own instability-discount term
(`instability_discount_weight * seen_victim_unstable`, N1's own unmodified
formula), STRUCTURALLY very negative once the victim dysregulates (the SAME
dyad every U-line rung reuses), `belief_gap = cred_abuser - cred_victim >=
0 - cred_victim = -cred_victim`, a LARGE POSITIVE floor, for EVERY value of
`minimization_discount`, including the ZERO-DISCOUNT control -- making the
scoping doc's own falsification bar for that control ("must show the
belief-gap NOT favouring the abuser") STRUCTURALLY UNREACHABLE, independent
of any empirical dynamics, exactly the shape of hazard U1's own prereg
disclosed for its own `cred_abuser`. The fix, the SAME minimal correction
U1 already established: `cred_abuser` is a SIGNED balance --
`charm_weight * (seen_mild - seen_severe)` -- so a "severe" reading, when it
occurs, costs the abuser's credibility exactly what a "mild" reading earns.
This makes the zero-discount control's belief-gap a genuine, non-guaranteed
empirical question (Sec. 3 of the prereg reports the pilot that located an
operating point where it separates, and the confirmatory run reports whether
it held).

`seen_mild`/`seen_severe` are WORLD-ADAPTER-accumulated (mechanical per-tick
delivery of an observed graph fact -- `SelfAccount.magnitude` vs the abuser's
own `recover_floor`, snap_frustration's own already-existing "still
genuinely elevated" threshold, reused verbatim rather than inventing a new
cutoff -- never a Python decision), credited on EVERY tick (U2 has no phase
schedule, no context-gating of any kind -- the self-account is reported
continuously, the same way N1's own stated_charm was).

NO Rust, NO new Term -- every Term below (Plus/Minus/Times/IfThenElse/Attr/
Var/Lit/Eq/Lt/And) is already in the engine and already used by
`snap_frustration.json` / `arousal_window_coreg.json` /
`abusive_n1_credibility_loop.json` / `abusive_u1_context_affect.json`.

Run:  python3 scripts/abusive_u2_self_account_seed_build.py
"""
from __future__ import annotations

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "seeds", "abusive_u2_self_account.json")


# ---- Term constructors (mechanical JSON shape, identical to N1's/U0's/U1's own)
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
# STATIC per-trajectory topology choice, matching N1's BASELINE exactly.
u2_frustration_term = term(
    minus(
        plus(attr("vaff", "arousal"),
             times(attr("vaff", "k_co"), minus(attr("aaff", "arousal"), attr("vaff", "arousal"))),
             times(attr("vaff", "k_self"), minus(attr("vaff", "setpoint"), attr("vaff", "arousal")))),
        attr("vaff", "setpoint")))

u2_victim_entrainment = rule(
    "u2_victim_entrainment", 8,
    [["victim", "has_affective_state", "vaff"],
     ["victim", "attended_by", "abuser"],
     ["abuser", "has_affective_state", "aaff"]],
    and_(lt(attr("vaff", "pcr_epoch"), attr("vaff", "tick_epoch")),
         eq(attr("aaff", "is_abuser"), lit(1.0))),
    [["set_attr", "vaff", "frustration", u2_frustration_term],
     ["set_attr", "vaff", "pcr_epoch", term(attr("vaff", "tick_epoch"))]])

# ---------------------------------------------- 2. the self-account rule -----
# SelfAccount.magnitude = minimization_discount * frustration -- ONE genuinely
# held, genuinely (possibly) distorted value, computed fresh every tick from
# the abuser's OWN true frustration (242000, unmodified). There is no second
# node anywhere holding an undiscounted "true" copy for the network to be
# denied -- this rule computes the ONE value the abuser holds and sincerely
# reports. minimization_discount is a declared, frozen constant (matching
# N1's own instability_discount_weight / U0's concealment_benefit
# convention) -- never learned, never agent-chosen.
u2_self_account = rule(
    "u2_self_account", 21,
    [["abuser", "has_self_account", "sa"],
     ["abuser", "has_affective_state", "aaff"]],
    eq(attr("aaff", "is_abuser"), lit(1.0)),
    [["set_attr", "sa", "magnitude",
      term(times(attr("sa", "minimization_discount"), attr("aaff", "frustration")))]])

# -------------------------------------------- 3. the ONE credibility rule ----
# NO stated/held split, NO insider/outsider split -- every NetworkNode reads
# the SAME sincere self-account. cred_abuser is a SIGNED balance
# (charm_weight * (seen_mild - seen_severe)) -- see this file's own
# provenance note above for why a reward-only formula (N1's own shape,
# literally) makes the zero-discount control's falsification bar
# structurally unreachable, and why the signed balance is the minimal fix
# (the SAME fix U1's own prereg already established for the SAME class of
# hazard). cred_victim is IDENTICAL to N1's/U1's own formula, unmodified.
cred_victim_term = minus(
    times(attr("nn", "claim_weight"), attr("nn", "seen_victim_claim")),
    times(attr("nn", "instability_discount_weight"), attr("nn", "seen_victim_unstable")))

cred_abuser_term = times(
    attr("nn", "charm_weight"),
    minus(attr("nn", "seen_mild"), attr("nn", "seen_severe")))

u2_network_credibility = rule(
    "u2_network_credibility", 40,
    [["net", "has_member", "nn"]],
    eq(attr("nn", "credibility_on"), lit(1.0)),
    [["set_attr", "nn", "cred_abuser", term(cred_abuser_term)],
     ["set_attr", "nn", "cred_victim", term(cred_victim_term)],
     ["set_attr", "nn", "belief_gap", term(minus(cred_abuser_term, cred_victim_term))]])

RULES = [u2_victim_entrainment, u2_self_account, u2_network_credibility]

PRODUCTIONS = [
    {
        "provenance": "abusive_u2_self_account:victim_attended_by_abuser",
        "src": {"type": "Agent", "var": "victim"},
        "edge_type": "attended_by",
        "tgt": {"type": "Agent", "var": "abuser"}
    },
    {
        "provenance": "abusive_u2_self_account:abuser_has_self_account",
        "src": {"type": "Agent", "var": "abuser"},
        "edge_type": "has_self_account",
        "tgt": {"type": "SelfAccount", "var": "sa"}
    },
    {
        "provenance": "abusive_u2_self_account:network_has_member",
        "src": {"type": "Network", "var": "net"},
        "edge_type": "has_member",
        "tgt": {"type": "NetworkNode", "var": "nn"}
    },
    {
        "provenance": "abusive_u2_self_account:node_observes_self_account",
        "src": {"type": "NetworkNode", "var": "nn"},
        "edge_type": "observes_self_account",
        "tgt": {"type": "Agent", "var": "abuser"}
    },
    {
        "provenance": "abusive_u2_self_account:node_observes_victim",
        "src": {"type": "NetworkNode", "var": "nn"},
        "edge_type": "observes_victim",
        "tgt": {"type": "Agent", "var": "victim"}
    },
]

SEED = {
    "id": "abusive_u2_self_account",
    "version": "1.0.0",
    "depends_on": ["snap_frustration", "arousal_window_coreg"],
    "self_load_only": True,
    "area": "retina",
    "description": (
        "ABUSIVE-DYNAMICS U2 -- SELF-SERVING SELF-ACCOUNT, SINCERELY HELD, "
        "NO STATED-VS-HELD SPLIT (block 306000). The last rung of the "
        "unintentional/no-deliberate-deception companion dimension "
        "(ABUSIVE_RELATIONSHIPS_UNINTENTIONAL_SCOPING.md Part E, U2). "
        "DELETES N1's n1_abuser_stated_charm and replaces it with ONE rule "
        "computing SelfAccount.magnitude = minimization_discount * "
        "frustration -- a SINGLE, genuinely held, genuinely (possibly) "
        "distorted account the abuser sincerely reports; no second 'true' "
        "value is tracked separately and hidden. Self-contained restatement "
        "matching U0's/U1's own precedent: u2_victim_entrainment is "
        "BYTE-IDENTICAL to N1's n1_victim_entrainment; u2_network_"
        "credibility replaces both of N1's credibility rules with ONE "
        "unconditional rule computing cred_abuser as a SIGNED balance "
        "(charm_weight*(seen_mild-seen_severe)) rather than N1's "
        "reward-only count -- a signed balance is REQUIRED, not stylistic: "
        "a reward-only formula makes cred_abuser>=0 by construction for "
        "every arm, and because cred_victim is structurally very negative "
        "once the victim dysregulates (the same dyad every U-line rung "
        "reuses), belief_gap=cred_abuser-cred_victim would be guaranteed "
        "positive for EVERY minimization_discount value including the "
        "zero-discount control -- the SAME class of hazard U1's own prereg "
        "found and fixed for its own cred_abuser, found here before this "
        "seed was locked. seen_mild/seen_severe are WORLD-ADAPTER-"
        "accumulated (mechanical per-tick delivery of SelfAccount.magnitude "
        "vs the abuser's own recover_floor -- snap_frustration's own "
        "already-existing 'still genuinely elevated' threshold, reused "
        "verbatim, never a Python decision), credited on EVERY tick (U2 has "
        "no phase schedule, no context-gating of any kind). NO reward/"
        "punishment anywhere. NO Rust, NO new Term (Plus/Minus/Times/"
        "IfThenElse/Attr/Var/Lit/Eq/Lt/And only, all already used by "
        "snap_frustration/arousal_window_coreg/abusive_n1_credibility_loop/"
        "abusive_u1_context_affect). self_load_only, default-OFF."
    ),
    "microtheory": {
        "name": "self_serving_self_account_sincerely_held",
        "description": (
            "The abuser's calm account of what happened is not a lie -- it "
            "is the ONE value his own self-account mechanism computes, "
            "discounted from his own true frustration by a fixed, "
            "undirected factor. There is no second node holding what he "
            "'really' believes for the network to be denied access to; the "
            "discounted value IS his belief, sincerely reported. A network "
            "that hears a mild account from a genuinely minimizing abuser "
            "is not being deceived by a strategist -- it is hearing exactly "
            "what he holds, distorted by the SAME self-serving mechanism "
            "Bandura's moral disengagement and Baumeister's self-serving "
            "narrative construction document as common and undirected, not "
            "a chosen narrative selected to manage anyone's impression."
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
