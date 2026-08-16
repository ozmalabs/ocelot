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


def PickUniqueT(source):
    return {"type": "PickUnique", "source": source}


def TimesT(items):
    return {"type": "Times", "items": items}


def Gt(a, b):
    return {"type": "Gt", "a": a, "b": b}


def term_effect(node, key, term):
    return ["set_attr", node, key, {"__term__": term}]


def add_node_effect(var_name, node_type, attrs):
    return ["add_node", var_name, node_type, attrs]


def add_edge_effect(src, edge_type, tgt):
    return ["add_edge", src, edge_type, tgt]


# --------------------------------------------------------------------- #
# witness_judgment -- UNCHANGED, still keyed to the dispute's own escalate/
# defuse outcome (a genuinely different, correctly-external signal: what
# OTHERS perceive, not the agent's own attribution -- ATTRIBUTION_LOCUS_AS_
# RESIDUAL_PREREG.md Sec2).
# --------------------------------------------------------------------- #
def _is_escalate(sig_var="sig"):
    return Eq(Attr(Var(sig_var), "outcome"), Lit("escalate"))


def _witness_judgment_term(sig_var="sig"):
    return IfThenElse(_is_escalate(sig_var), Lit("violated"), Lit("met"))


# --------------------------------------------------------------------- #
# attribution_locus -- ATTRIBUTION_LOCUS_AS_RESIDUAL_PREREG.md Sec2: the
# residual between the incident's own implied signal and the agent's held
# SelfPattern (0 or 1 optional edge from ctx). No SelfPattern -> circumstance
# (nothing to confirm or contradict). Signs agree (confirms the pattern) ->
# global_self. Signs disagree (contradicts the pattern) -> specific_act.
# --------------------------------------------------------------------- #
def _incident_signal_term(ctx_var="ctx"):
    """standard_met is unconditionally 0.0 on THIS bridge (PREREG Sec1's
    unchanged premise: a dispute existing at all means the claim-holder was
    wrong), so the incident signal is the matching literal -1.0 -- a
    dispute's own DisputeContext carries no standard_met attr of its own
    (that only ever exists on the MINTED SelfConsciousContext), so this is
    not read from the graph. Prediction 4's hubristic/authentic-pride
    mirror on the standard_met=True side is a different caller/context
    entirely (SelfPattern's own sign-agreement logic already generalizes to
    it), not this bridge's own -1.0 premise."""
    return Lit(-1.0)


def _has_self_pattern_term(ctx_var="ctx"):
    return CountT(Neighbours(Var(ctx_var), "has_self_pattern"))


def _held_self_worth_term(ctx_var="ctx"):
    return Attr(
        PickUniqueT(Neighbours(Var(ctx_var), "has_self_pattern")),
        "held_self_worth",
    )


def _attribution_locus_term(ctx_var="ctx"):
    confirms = Gt(
        TimesT([_held_self_worth_term(ctx_var), _incident_signal_term(ctx_var)]),
        Lit(0.0),
    )
    return IfThenElse(
        Eq(_has_self_pattern_term(ctx_var), Lit(0)),
        Lit("circumstance"),
        IfThenElse(confirms, Lit("global_self"), Lit("specific_act")),
    )


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
            "PREREG.md Sec2). attribution_locus is now a RESIDUAL "
            "(ATTRIBUTION_LOCUS_AS_RESIDUAL_PREREG.md Sec2): the incident's "
            "own implied signal vs the agent's held SelfPattern -- no "
            "pattern -> circumstance, signs agree (confirms the pattern) -> "
            "global_self, signs disagree (contradicts it) -> specific_act. "
            "witness_judgment stays keyed to the dispute's OWN escalate/"
            "defuse outcome -- a genuinely different, correctly-external "
            "signal (what OTHERS perceive), not the agent's own "
            "attribution. Guarded by a bridged_to dedup edge so re-running "
            "run_rules() does not double-mint (PREREG prediction 5)."
        ),
        "match_type": "RuleDisputeSignal",
        "match": [
            ["ctx", "has_signal", "sig"],
        ],
        "where": where,
        "effects": [
            add_node_effect("sc_ctx", "SelfConsciousContext", {
                "standard_met": 0.0,
                "attribution_locus": {"__term__": _attribution_locus_term("ctx")},
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
    "version": "1.1.0",
    "depends_on": ["rule_dispute_escalation", "self_conscious_emotions"],
    "self_load_only": True,
    "description": (
        "Bridges a decided rule dispute (seeds/rule_dispute_escalation.json) "
        "to a self-conscious-emotion appraisal (seeds/self_conscious_"
        "emotions.json) for the claim-holder who was wrong, WITHOUT editing "
        "either seed -- strictly additive. standard_met is unconditionally "
        "0.0 -- a dispute existing at all means the claim-holder was wrong. "
        "v1.1.0 (ATTRIBUTION_LOCUS_AS_RESIDUAL_PREREG.md): attribution_locus "
        "is now a RESIDUAL, not a hand-picked lookup from the dispute "
        "outcome -- the incident's own implied signal (-1.0, standard "
        "violated) compared against the agent's held SelfPattern (0 or 1 "
        "optional edge): no pattern -> circumstance (Miller 1996's "
        "embarrassment mode, correctly recovered for first-time incidents); "
        "signs agree (confirms the pattern) -> global_self (Abramson, "
        "Seligman & Teasdale 1978's depressive attributional style); signs "
        "disagree (contradicts it) -> specific_act (Miller & Ross 1975's "
        "self-serving bias). witness_judgment stays keyed to the dispute's "
        "OWN escalate/defuse outcome (Tangney & Dearing 2002) -- a "
        "genuinely different, correctly-external signal (what OTHERS "
        "perceive), unchanged. Zero new Rust Terms -- Eq/And/IfThenElse/"
        "Count/Neighbours/PickUnique/Times/Gt/Attr/Var/Lit all pre-existed; "
        "add_node/add_edge rule effects mirror seeds/gap_awareness.json's "
        "own mint-on-decision idiom exactly. See "
        "RULE_DISPUTE_SELF_CONSCIOUS_BRIDGE_PREREG.md / _RESULTS.md and "
        "ATTRIBUTION_LOCUS_AS_RESIDUAL_PREREG.md / _RESULTS.md."
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
        {
            "src": {"type": "DisputeContext", "var": "ctx"},
            "edge_type": "has_self_pattern",
            "tgt": {"type": "SelfPattern", "var": "pattern"},
            "where": None,
            "weight": {"type": "Lit", "value": 1.0},
            "provenance": "rule_dispute_self_conscious_bridge",
        },
    ],
    "concepts": [
        {
            "name": "rule_dispute_self_conscious_bridge",
            "definition": (
                "A rules dispute's claim-holder experiences shame, guilt, "
                "or embarrassment depending on whether the incident "
                "confirms or contradicts their own held self-pattern (a "
                "residual, not a lookup from the dispute outcome) -- while "
                "who ELSE believes a violation occurred (witness_judgment) "
                "stays keyed to the dispute's own escalate/defuse outcome, "
                "a genuinely separate signal."
            ),
            "why": (
                "The user asked to wire the self-conscious-emotions "
                "mechanism live off the rule-dispute escalation outcome, "
                "then to wire attribution_locus itself as a residual, "
                "mirroring issue_severity's own fix. "
                "RULE_DISPUTE_SELF_CONSCIOUS_BRIDGE_PREREG.md, "
                "ATTRIBUTION_LOCUS_AS_RESIDUAL_PREREG.md."
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
