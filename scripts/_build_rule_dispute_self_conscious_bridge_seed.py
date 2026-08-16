"""One-off authoring script that EMITS
seeds/rule_dispute_self_conscious_bridge.json.

Not agent runtime -- a tool script (CLAUDE.md's `tools/*` precedent). Bridges
two prior, independently-tested rungs (seeds/rule_dispute_escalation.json,
seeds/self_conscious_emotions.json) WITHOUT editing either -- strictly
additive, mirrors the builder shape of both.

See docs/research/psychology_affect/
RULE_DISPUTE_SELF_CONSCIOUS_BRIDGE_PREREG.md for the full registered design.

Run: python3 scripts/_build_rule_dispute_self_conscious_bridge_seed.py > seeds/rule_dispute_self_conscious_bridge.json
"""
import json


def Var(name):
    return {"type": "Var", "name": name}


def Lit(value):
    return {"type": "Lit", "value": value}


def Attr(node, key):
    return {"type": "Attr", "node": node, "key": key}


def Eq(a, b):
    return {"type": "Eq", "a": a, "b": b}


def AndT(items):
    return {"type": "And", "items": items}


def IfThenElse(cond, then, other):
    return {"type": "IfThenElse", "cond": cond, "then": then, "other": other}


def Neighbours(node, edge_type):
    return {"type": "Neighbours", "node": node, "edge_type": edge_type}


def CountT(source):
    return {"type": "Count", "source": source}


def term_effect(node, key, term):
    return ["set_attr", node, key, {"__term__": term}]


def add_node_effect(var_name, node_type, attrs):
    return ["add_node", var_name, node_type, attrs]


def add_edge_effect(src, edge_type, tgt):
    return ["add_edge", src, edge_type, tgt]


# --------------------------------------------------------------------- #
# outcome -> (attribution_locus, witness_judgment) -- PREREG Sec1's
# registered Tangney & Dearing (2002) mapping: HOW a correction is
# delivered (hostile/confrontational vs calm) shapes whether it is
# internalized as global-self or specific-act attribution.
# --------------------------------------------------------------------- #
def _is_escalate(sig_var="sig"):
    return Eq(Attr(Var(sig_var), "outcome"), Lit("escalate"))


def _attribution_locus_term(sig_var="sig"):
    return IfThenElse(_is_escalate(sig_var), Lit("global_self"), Lit("specific_act"))


def _witness_judgment_term(sig_var="sig"):
    return IfThenElse(_is_escalate(sig_var), Lit("violated"), Lit("met"))


# --------------------------------------------------------------------- #
# Rule 1: a decided RuleDisputeSignal mints a SelfConsciousContext for the
# claim-holder (standard_met=0.0 unconditionally -- PREREG Sec1: a dispute
# existing at all means someone was wrong about the rule).
# --------------------------------------------------------------------- #
def rule_bridge_context():
    ctx, sig = Var("ctx"), Var("sig")
    where = AndT([
        Eq(Attr(sig, "status"), Lit("decided")),
        Eq(CountT(Neighbours(ctx, "bridged_to")), Lit(0)),
    ])
    return {
        "name": "bridge_dispute_to_self_conscious_context",
        "comment": (
            "PREREG Sec1: a decided RuleDisputeSignal mints a "
            "SelfConsciousContext for the claim-holder -- standard_met=0.0 "
            "unconditionally (the dispute's own premise is that this "
            "party was wrong about the rule, RULE_DISPUTE_ESCALATION_"
            "PREREG.md Sec2). attribution_locus and witness_judgment are "
            "both derived from the SAME outcome-keyed mapping (Tangney & "
            "Dearing 2002: a hostile/confrontational correction (escalate) "
            "reads as global-self attribution; a calm one (defuse) reads "
            "as specific-act) -- not two independent decisions. Guarded by "
            "a bridged_to dedup edge so re-running run_rules() does not "
            "double-mint (PREREG prediction 5)."
        ),
        "match_type": "RuleDisputeSignal",
        "match": [
            ["ctx", "has_signal", "sig"],
        ],
        "where": where,
        "effects": [
            add_node_effect("sc_ctx", "SelfConsciousContext", {
                "standard_met": 0.0,
                "attribution_locus": {"__term__": _attribution_locus_term("sig")},
                "witness_judgment": {"__term__": _witness_judgment_term("sig")},
            }),
            add_node_effect("sc_sig", "SelfConsciousSignal", {"status": "pending"}),
            add_edge_effect("sc_ctx", "has_appraisal", "sc_sig"),
            add_edge_effect("ctx", "bridged_to", "sc_ctx"),
        ],
    }


# --------------------------------------------------------------------- #
# Rule 2: each of the dispute's own witnesses mints a corresponding
# WitnessBelief on the new SelfConsciousContext -- PREREG Sec1/prediction 4:
# witness count is carried over exactly.
# --------------------------------------------------------------------- #
def rule_bridge_witness():
    ctx, wp, sc_ctx = Var("ctx"), Var("wp"), Var("sc_ctx")
    where = AndT([
        Eq(CountT(Neighbours(wp, "mirrored_as")), Lit(0)),
    ])
    return {
        "name": "bridge_dispute_witness_to_self_conscious_witness",
        "comment": (
            "PREREG Sec1/prediction 4: each WitnessPresence already on the "
            "dispute's DisputeContext mints a corresponding WitnessBelief "
            "on the bridged SelfConsciousContext, judgment taken from the "
            "SAME witness_judgment Rule 1 already derived (not re-derived "
            "here) -- an escalated (public, confrontational) dispute reads "
            "to onlookers as a clear violation; a defused one does not. "
            "Guarded by a mirrored_as dedup edge per witness (PREREG "
            "prediction 5)."
        ),
        "match_type": "WitnessPresence",
        "match": [
            ["ctx", "has_witness", "wp"],
            ["ctx", "bridged_to", "sc_ctx"],
        ],
        "where": where,
        "effects": [
            add_node_effect("wb", "WitnessBelief", {
                "judgment": {"__term__": Attr(sc_ctx, "witness_judgment")},
            }),
            add_edge_effect("sc_ctx", "has_witness_belief", "wb"),
            add_edge_effect("wp", "mirrored_as", "wb"),
        ],
    }


SEED = {
    "id": "rule_dispute_self_conscious_bridge",
    "version": "1.0.0",
    "depends_on": ["rule_dispute_escalation", "self_conscious_emotions"],
    "self_load_only": True,
    "description": (
        "Bridges a decided rule dispute (seeds/rule_dispute_escalation.json) "
        "to a self-conscious-emotion appraisal (seeds/self_conscious_"
        "emotions.json) for the claim-holder who was wrong, WITHOUT editing "
        "either seed -- strictly additive. The dispute's escalate/defuse "
        "outcome IS the correction style (Tangney & Dearing 2002: hostile/"
        "confrontational vs calm), which sets attribution_locus (global_"
        "self vs specific_act) and, identically, each carried-over "
        "witness's judgment. standard_met is unconditionally 0.0 -- a "
        "dispute existing at all means the claim-holder was wrong. This "
        "bridge structurally never produces attribution_locus=circumstance, "
        "so it never produces embarrassment -- a genuine rules dispute is "
        "an attributable epistemic error, not a circumstantial mishap "
        "(PREREG Sec1's registered scope boundary, prediction 3). Zero new "
        "Rust Terms -- Eq/And/IfThenElse/Count/Neighbours/Attr/Var/Lit all "
        "pre-existed; add_node/add_edge rule effects mirror seeds/"
        "gap_awareness.json's own mint-on-decision idiom exactly. See "
        "RULE_DISPUTE_SELF_CONSCIOUS_BRIDGE_PREREG.md / _RESULTS.md."
    ),
    "nodes": [],
    "edges": [],
    "productions": [
        {
            "src": {"type": "DisputeContext", "var": "ctx"},
            "edge_type": "bridged_to",
            "tgt": {"type": "SelfConsciousContext", "var": "sc_ctx"},
            "where": None,
            "weight": {"type": "Lit", "value": 1.0},
            "provenance": "rule_dispute_self_conscious_bridge",
        },
        {
            "src": {"type": "WitnessPresence", "var": "wp"},
            "edge_type": "mirrored_as",
            "tgt": {"type": "WitnessBelief", "var": "wb"},
            "where": None,
            "weight": {"type": "Lit", "value": 1.0},
            "provenance": "rule_dispute_self_conscious_bridge",
        },
    ],
    "concepts": [
        {
            "name": "rule_dispute_self_conscious_bridge",
            "definition": (
                "A rules dispute's escalate/defuse outcome IS a correction "
                "style (hostile/confrontational vs calm), which mechanically "
                "determines the self-conscious emotion the disputant who "
                "was wrong experiences -- shame from an escalated "
                "confrontation, guilt from a defused correction -- via the "
                "same attribution-locus mechanism the self-conscious-"
                "emotions rung already established, never a bespoke third "
                "decision."
            ),
            "why": (
                "The user asked to wire the self-conscious-emotions "
                "mechanism live off the rule-dispute escalation outcome, "
                "the follow-on both prior RESULTS docs named. "
                "RULE_DISPUTE_SELF_CONSCIOUS_BRIDGE_PREREG.md."
            ),
        },
    ],
    "exclusions": [],
    "rules": [
        rule_bridge_context(),
        rule_bridge_witness(),
    ],
}

print(json.dumps(SEED, indent=1))
