#!/usr/bin/env python3
"""ABUSIVE-DYNAMICS U0 -- GENUINE INTENT: AN ARGMAX-SELECTED CONCEALMENT,
SCORED AGAINST A DECLARED GOAL (block 307000). The positive-control rung of
the "unintentional / no-deliberate-deception" companion dimension
(`docs/research/bigville/ABUSIVE_RELATIONSHIPS_UNINTENTIONAL_SCOPING.md`,
Part E, "### U0").

Authoring tool ONLY: it EMITS `seeds/abusive_u0_intent.json` (graph data) --
no agent decisions, no rule engine, no graph state. See
`docs/research/bigville/ABUSIVE_U0_INTENT_PREREG.md` for the full design
rationale. In brief, this seed:

  1. DELETES N1's `n1_abuser_stated_charm` (the unconditional broadcast,
     `seeds/abusive_n1_credibility_loop.json`) by NOT loading N1's seed file
     at all -- instead RESTATING N1's other three rules byte-identically
     (`u0_victim_entrainment`, `u0_network_credibility_stated`,
     `u0_network_credibility_private`), the SAME convention N1 itself used
     when it restated R2's/R3's dyad rule rather than depending on their seed
     files ("R3 restated R2's own rule rather than depending on it"). This
     is a DELIBERATE DEVIATION from the task brief's suggestion to
     `depends_on: ["abusive_n1_credibility_loop", ...]` directly -- see the
     prereg's own "composition note" for why: depending on N1's seed file
     directly would load `n1_abuser_stated_charm` ALONGSIDE this rung's own
     presentation-choice rule, both unconditionally writing
     `AffectiveState.stated_charm` every tick from DIFFERENT formulas, which
     is not a stable composition (two rules racing to decide the same attr
     every `run_rules()` sweep does not reach a fixpoint). Self-contained
     restatement is the only clean way to REPLACE (not augment) N1's one
     rule, matching Part E's own falsification-bar language ("each rung
     replaces (not augments) N1's one deliberate-construct rule").
  2. REPLACES it with the SAME `Argmax`-over-two-candidate-`Appraisal`s
     template `seeds/abusive_r4_learned_helplessness.json` and
     `seeds/marshmallow_delay.json` (block 240000) already use
     (`mm_appraise_wait`/`take` -> `em_happiness`/`em_fulfilment_value`/
     `em_total_value` (block 204000's `core_emotions`, UNMODIFIED) ->
     `mm_choose`), reused verbatim: `u0_appraise_charm` /
     `u0_appraise_true_state` value the two candidates
     (`present_charm`/`present_true_state`); `u0_choose` is the Argmax
     (structurally IDENTICAL to `mm_choose`/`r4_choose`); `u0_apply_
     presentation_choice` copies the winning candidate's `action` onto
     `AffectiveState.stated_charm` -- the SAME attr N1's own rule wrote,
     preserving the interface every downstream rule/adapter reads.

  `present_charm`:      individual_benefit = concealment_benefit (constant)
                         individual_cost   = 0
  `present_true_state`: individual_benefit = honesty_benefit (constant)
                         individual_cost   = suspicion_cost_scale * frustration
                         (SCALES WITH the abuser's TRUE, already-existing
                         `frustration` attr -- 242000's own, unmodified)

`concealment_benefit`/`honesty_benefit`/`suspicion_cost_scale` are DECLARED
CONSTANTS (graph data, picked via pilot and frozen), the SAME convention as
N1's own `instability_discount_weight` / R4's `attempt_cost`. NO reward/
punishment token: the Argmax computes a VALUE COMPARISON between two
candidate presentations, structurally identical to R4's `r4_choose` /
marshmallow's `mm_choose`, both already gated clean on Part D.2 -- see the
prereg's own audit note.

NO Rust, NO new Term -- every Term below (Plus/Minus/Times/IfThenElse/Attr/
Var/Lit/Eq/Lt/Gt/And/Argmax/Neighbours) is already in the engine and already
used by `snap_frustration.json` / `arousal_window_coreg.json` /
`core_emotions.json` / `abusive_r4_learned_helplessness.json` /
`marshmallow_delay.json` / `abusive_n1_credibility_loop.json`.

Run:  python3 scripts/abusive_u0_intent_seed_build.py
"""
from __future__ import annotations

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, "seeds", "abusive_u0_intent.json")


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


def gt(a, b):
    return {"type": "Gt", "a": a, "b": b}


def and_(*items):
    return {"type": "And", "items": list(items)}


def ite(cond, then, other):
    return {"type": "IfThenElse", "cond": cond, "then": then, "other": other}


def neighbours(node, edge_type):
    return {"type": "Neighbours", "node": var(node), "edge_type": edge_type, "any_type": False}


def argmax(source, var_name, value):
    return {"type": "Argmax", "source": source, "var_name": var_name, "value": value}


def term(t):
    return {"__term__": t}


HARD = "hard_realtime"


def rule(name, order, match, where, effects):
    return {"name": name, "area": "retina", "order": order,
            "latency_class": HARD, "match": match, "where": where,
            "effects": effects}


# --------------------------------------------------------- 1. dyad entrainment
# BYTE-IDENTICAL formula to N1's n1_victim_entrainment (itself byte-identical
# to R2's r2_victim_entrainment_via_frustration / R3's
# r3_victim_entrainment_solo), restated here self-contained -- U0 does not
# depend_on abusive_n1_credibility_loop's seed file (see module docstring).
u0_frustration_term = term(
    minus(
        plus(attr("vaff", "arousal"),
             times(attr("vaff", "k_co"), minus(attr("aaff", "arousal"), attr("vaff", "arousal"))),
             times(attr("vaff", "k_self"), minus(attr("vaff", "setpoint"), attr("vaff", "arousal")))),
        attr("vaff", "setpoint")))

u0_victim_entrainment = rule(
    "u0_victim_entrainment", 8,
    [["victim", "has_affective_state", "vaff"],
     ["victim", "attended_by", "abuser"],
     ["abuser", "has_affective_state", "aaff"]],
    and_(lt(attr("vaff", "pcr_epoch"), attr("vaff", "tick_epoch")),
         eq(attr("aaff", "is_abuser"), lit(1.0))),
    [["set_attr", "vaff", "frustration", u0_frustration_term],
     ["set_attr", "vaff", "pcr_epoch", term(attr("vaff", "tick_epoch"))]])

# --------------------------------------- 2. the genuine-intent Argmax choice
# THE TWO CANDIDATES. present_charm: individual_benefit = concealment_benefit
# (constant), individual_cost = 0 -- concealment is structurally COST-FREE to
# attempt, its only downside is the honesty candidate's foregone value.
# present_true_state: individual_benefit = honesty_benefit (constant),
# individual_cost = suspicion_cost_scale * frustration -- THE cost of being
# honest rises with how much there genuinely is to conceal (the abuser's OWN
# true, already-existing frustration, 242000's unmodified attr). This is the
# signature that makes concealment-selection correlate with frustration --
# N1's original unconditional broadcast could not, by construction, produce
# this correlation (it never read frustration at all).
u0_appraise_charm = rule(
    "u0_appraise_charm", 2,
    [["hub", "has_emotion_params", "ep"],
     ["hub", "has_presentation_decision", "dec"],
     ["hub", "has_candidate", "c"]],
    and_(eq(attr("ep", "enabled"), lit(1.0)),
         eq(attr("c", "action"), lit(1.0))),
    [["set_attr", "c", "individual_benefit", term(attr("dec", "concealment_benefit"))],
     ["set_attr", "c", "individual_cost", term(lit(0.0))]])

u0_appraise_true_state = rule(
    "u0_appraise_true_state", 2,
    [["hub", "has_emotion_params", "ep"],
     ["hub", "has_presentation_decision", "dec"],
     ["hub", "has_affective_state", "aaff"],
     ["hub", "has_candidate", "c"]],
    and_(eq(attr("ep", "enabled"), lit(1.0)),
         eq(attr("c", "action"), lit(0.0))),
    [["set_attr", "c", "individual_benefit", term(attr("dec", "honesty_benefit"))],
     ["set_attr", "c", "individual_cost",
      term(times(attr("dec", "suspicion_cost_scale"), attr("aaff", "frustration")))]])

# THE DECISION. Identical Argmax structure to mm_choose/r4_choose:
# chosen_action = the action of whichever candidate Appraisal has the
# greatest total_value (happiness + fulfilment_value, computed by
# core_emotions em_happiness/em_total_value, UNMODIFIED, from the
# individual_benefit/individual_cost the appraise rules set above). This is
# a VALUE COMPARISON between two candidates, NOT a reward applied to the
# agent for its choice -- the SAME mechanism R4's r4_choose / marshmallow's
# mm_choose already use and have already been source-audited clean.
u0_choose = rule(
    "u0_choose", 20,
    [["hub", "has_emotion_params", "ep"],
     ["hub", "has_presentation_decision", "dec"]],
    eq(attr("ep", "enabled"), lit(1.0)),
    [["set_attr", "dec", "chosen_action",
      term({"type": "Attr",
            "node": argmax(neighbours("hub", "has_candidate"), "c",
                            attr("c", "total_value")),
            "key": "action"})]])

# THE PRESENTATION. Copies the winning candidate's action onto
# AffectiveState.stated_charm -- the SAME attr N1's n1_abuser_stated_charm
# wrote, so every downstream rule/adapter (u0_network_credibility_stated/
# _private, and the world adapter's seen_charm bookkeeping) is UNCHANGED
# from N1's own convention; only HOW stated_charm is decided differs.
u0_apply_presentation_choice = rule(
    "u0_apply_presentation_choice", 21,
    [["hub", "has_emotion_params", "ep"],
     ["hub", "has_presentation_decision", "dec"],
     ["hub", "has_affective_state", "aaff"]],
    eq(attr("ep", "enabled"), lit(1.0)),
    [["set_attr", "aaff", "stated_charm", term(attr("dec", "chosen_action"))]])

# -------------------------------------------------- 3/4. network credibility
# BYTE-IDENTICAL restatement of N1's n1_network_credibility_stated/_private
# (see seeds/abusive_n1_credibility_loop.json) -- untouched formula, renamed
# only for this seed's own provenance.
cred_victim_term_full = minus(
    times(attr("nn", "claim_weight"), attr("nn", "seen_victim_claim")),
    times(attr("nn", "instability_discount_weight"), attr("nn", "seen_victim_unstable")))

cred_abuser_term_stated = times(attr("nn", "charm_weight"), attr("nn", "seen_charm"))

u0_network_credibility_stated = rule(
    "u0_network_credibility_stated", 40,
    [["net", "has_member", "nn"]],
    eq(attr("nn", "observes_private"), lit(0.0)),
    [["set_attr", "nn", "cred_abuser", term(cred_abuser_term_stated)],
     ["set_attr", "nn", "cred_victim", term(cred_victim_term_full)],
     ["set_attr", "nn", "belief_gap", term(minus(cred_abuser_term_stated, cred_victim_term_full))]])

cred_abuser_term_private = minus(lit(0.0), times(attr("nn", "harm_discount_weight"), attr("nn", "seen_harm_direct")))

u0_network_credibility_private = rule(
    "u0_network_credibility_private", 40,
    [["net", "has_member", "nn"]],
    eq(attr("nn", "observes_private"), lit(1.0)),
    [["set_attr", "nn", "cred_abuser", term(cred_abuser_term_private)],
     ["set_attr", "nn", "cred_victim", term(cred_victim_term_full)],
     ["set_attr", "nn", "belief_gap", term(minus(cred_abuser_term_private, cred_victim_term_full))]])

RULES = [u0_victim_entrainment,
         u0_appraise_charm, u0_appraise_true_state, u0_choose, u0_apply_presentation_choice,
         u0_network_credibility_stated, u0_network_credibility_private]

PRODUCTIONS = [
    {
        "provenance": "abusive_u0_intent:victim_attended_by_abuser",
        "src": {"type": "Agent", "var": "victim"},
        "edge_type": "attended_by",
        "tgt": {"type": "Agent", "var": "abuser"}
    },
    {
        "provenance": "abusive_u0_intent:network_has_member",
        "src": {"type": "Network", "var": "net"},
        "edge_type": "has_member",
        "tgt": {"type": "NetworkNode", "var": "nn"}
    },
    {
        "provenance": "abusive_u0_intent:node_observes_stated",
        "src": {"type": "NetworkNode", "var": "nn"},
        "edge_type": "observes_stated",
        "tgt": {"type": "Agent", "var": "abuser"}
    },
    {
        "provenance": "abusive_u0_intent:node_observes_held",
        "src": {"type": "NetworkNode", "var": "nn"},
        "edge_type": "observes_held",
        "tgt": {"type": "Agent", "var": "abuser"}
    },
    {
        "provenance": "abusive_u0_intent:node_observes_victim",
        "src": {"type": "NetworkNode", "var": "nn"},
        "edge_type": "observes_victim",
        "tgt": {"type": "Agent", "var": "victim"}
    },
    {
        "provenance": "abusive_u0_intent:hub_has_emotion_params",
        "src": {"type": "EmotionHub", "var": "hub"},
        "edge_type": "has_emotion_params",
        "tgt": {"type": "HeldEmotionParams", "var": "ep"}
    },
    {
        "provenance": "abusive_u0_intent:hub_has_presentation_decision",
        "src": {"type": "EmotionHub", "var": "hub"},
        "edge_type": "has_presentation_decision",
        "tgt": {"type": "PresentationDecision", "var": "dec"}
    },
    {
        "provenance": "abusive_u0_intent:hub_has_affective_state",
        "src": {"type": "EmotionHub", "var": "hub"},
        "edge_type": "has_affective_state",
        "tgt": {"type": "AffectiveState", "var": "aaff"}
    },
    {
        "provenance": "abusive_u0_intent:hub_has_appraisal",
        "src": {"type": "EmotionHub", "var": "hub"},
        "edge_type": "has_appraisal",
        "tgt": {"type": "Appraisal", "var": "c"}
    },
    {
        "provenance": "abusive_u0_intent:hub_has_candidate",
        "src": {"type": "EmotionHub", "var": "hub"},
        "edge_type": "has_candidate",
        "tgt": {"type": "Appraisal", "var": "c"}
    },
]

SEED = {
    "id": "abusive_u0_intent",
    "version": "1.0.0",
    "depends_on": ["snap_frustration", "arousal_window_coreg", "core_emotions"],
    "self_load_only": True,
    "area": "retina",
    "description": (
        "ABUSIVE-DYNAMICS U0 -- GENUINE INTENT: AN ARGMAX-SELECTED "
        "CONCEALMENT, SCORED AGAINST A DECLARED GOAL (block 307000). The "
        "positive-control rung of the unintentional/no-deliberate-deception "
        "companion dimension "
        "(ABUSIVE_RELATIONSHIPS_UNINTENTIONAL_SCOPING.md Part E, U0). "
        "DELETES N1's n1_abuser_stated_charm (the unconditional broadcast) "
        "by self-contained restatement of N1's OTHER three rules "
        "(u0_victim_entrainment, u0_network_credibility_stated/_private -- "
        "byte-identical formulas, N1's seed file is NOT depended on, so "
        "n1_abuser_stated_charm never loads -- the only clean way to "
        "REPLACE rather than augment it; two rules unconditionally racing "
        "to set the same attr every tick would not reach a fixpoint). "
        "REPLACES it with the SAME Argmax-over-two-candidate-Appraisals "
        "template abusive_r4_learned_helplessness.json/marshmallow_delay.json "
        "(block 240000) already use: u0_appraise_charm/u0_appraise_true_state "
        "value two candidates (present_charm: individual_benefit="
        "concealment_benefit const, individual_cost=0; present_true_state: "
        "individual_benefit=honesty_benefit const, individual_cost="
        "suspicion_cost_scale*frustration -- SCALES WITH the abuser's TRUE, "
        "already-existing frustration, 242000's own unmodified attr). "
        "em_happiness/em_total_value (core_emotions, block 204000, "
        "UNMODIFIED) score both; u0_choose is the Argmax (structurally "
        "IDENTICAL to r4_choose/mm_choose -- a VALUE COMPARISON between two "
        "candidates, NOT a reward applied to the agent); "
        "u0_apply_presentation_choice copies the winner's action onto "
        "AffectiveState.stated_charm, the SAME attr N1's rule wrote, so "
        "every downstream rule/adapter is unchanged. The signature this "
        "produces: stated_charm selection correlates with frustration "
        "(concealment gets selected more often exactly when there is more "
        "to conceal, because honesty's cost scales with true harm) -- N1's "
        "unconditional broadcast could not produce this correlation, by "
        "construction, since it never read frustration at all. NO Rust, NO "
        "new Term. self_load_only, default-OFF."
    ),
    "microtheory": {
        "name": "genuine_intent_concealment_choice",
        "description": (
            "A genuinely intentional concealment is an Argmax over two "
            "candidate presentations (charm, truth) scored against a "
            "declared benefit -- the SAME value-economy mechanism the "
            "marshmallow/R4 lines already use for a delay-of-gratification "
            "or an escape-attempt choice, applied here to a presentation "
            "choice. The cost of honesty scales with the true harm level, "
            "so the Argmax's own selection tracks how much there is to "
            "conceal -- a readable, glass-box marker of calculated "
            "concealment, distinct from a reactive or context-driven "
            "presentation gap."
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
