"""One-off authoring script that EMITS
seeds/dispute_severity_from_beliefs.json.

Not agent runtime -- a tool script (CLAUDE.md's `tools/*` precedent).
Strictly additive over seeds/rule_dispute_escalation.json -- that seed is
NOT edited. Mirrors the two-rule bridge shape
scripts/_build_rule_dispute_self_conscious_bridge_seed.py already
established (a context-mint rule + a per-witness carry-over rule).

See docs/research/psychology_affect/DISPUTE_SEVERITY_AS_RESIDUAL_PREREG.md
for the full registered design.

Run: python3 scripts/_build_dispute_severity_from_beliefs_seed.py > seeds/dispute_severity_from_beliefs.json
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


def MinusT(a, b):
    return {"type": "Minus", "a": a, "b": b}


def Lt(a, b):
    return {"type": "Lt", "a": a, "b": b}


def StructSimT(a, b):
    return {"type": "StructSim", "a": a, "b": b}


def Neighbours(node, edge_type):
    return {"type": "Neighbours", "node": node, "edge_type": edge_type}


def CountT(source):
    return {"type": "Count", "source": source}


def add_node_effect(var_name, node_type, attrs):
    return ["add_node", var_name, node_type, attrs]


def add_edge_effect(src, edge_type, tgt):
    return ["add_edge", src, edge_type, tgt]


# --------------------------------------------------------------------- #
# issue_severity = 1 - StructSim(claim.pred, truth.pred) -- PREREG Sec1,
# confirmed empirically before registering (StructSim's own position-wise
# atom comparison over predication tuples, pre-existing Term).
# --------------------------------------------------------------------- #
def _issue_severity_term(bd_var="bd"):
    bd = Var(bd_var)
    claims = Var("claims")
    truth = Var("truth")
    return MinusT(
        Lit(1.0),
        StructSimT(Attr(claims, "pred"), Attr(truth, "pred")),
    )


# --------------------------------------------------------------------- #
# Rule 1: a BeliefDisagreement mints a DisputeContext with a COMPUTED
# issue_severity, reusing rule_dispute_escalation's OWN has_signal
# production for the RuleDisputeSignal unchanged.
# --------------------------------------------------------------------- #
def rule_severity_from_beliefs():
    bd, claims, truth = Var("bd"), Var("claims"), Var("truth")
    where = AndT([
        Eq(CountT(Neighbours(bd, "bridged_to")), Lit(0)),
        # A genuine residual must exist -- "a dispute is the residual
        # between two held beliefs" (user). Two IDENTICAL beliefs
        # (StructSim=1.0) mint no dispute at all: found live, not assumed
        # -- issue_severity=0.0 alone does NOT floor the downstream
        # pressure formula at <=0 (audience/closeness terms are additive
        # and independent of severity), so without this gate a genuinely
        # non-existent disagreement could still "escalate" on ambient
        # stranger/audience pressure alone. Gating on the residual itself,
        # here, is the correct fix -- rule_dispute_escalation.json's own
        # tested pressure formula is untouched.
        Lt(StructSimT(Attr(claims, "pred"), Attr(truth, "pred")), Lit(1.0)),
    ])
    return {
        "name": "severity_from_belief_disagreement",
        "comment": (
            "PREREG Sec1-2: issue_severity is COMPUTED as 1-StructSim(claim."
            "pred, truth.pred) -- the residual between two held beliefs -- "
            "not a caller-supplied scalar. Fires ONLY when a genuine "
            "residual exists (StructSim<1.0) -- identical beliefs mint no "
            "dispute at all, corrected live after finding severity=0.0 does "
            "NOT structurally floor the downstream pressure formula (PREREG "
            "prediction 1, revised). Mints a fresh DisputeContext (band_"
            "code/audience_gain copied from the BeliefDisagreement wrapper, "
            "genuinely external social-context data, PREREG Sec4) plus its "
            "own RuleDisputeSignal via rule_dispute_escalation's UNCHANGED "
            "has_signal production. Zero new Rust -- Minus/StructSim/Lt/"
            "Count/Neighbours/Attr/Var/Lit/Eq/And all pre-existed. Guarded "
            "by a bridged_to dedup edge, mirroring seeds/rule_dispute_self_"
            "conscious_bridge.json's own idiom exactly."
        ),
        "match_type": "BeliefDisagreement",
        "match": [
            ["bd", "claims", "claims"],
            ["bd", "truth", "truth"],
        ],
        "where": where,
        "effects": [
            add_node_effect("ctx", "DisputeContext", {
                "issue_severity": {"__term__": _issue_severity_term("bd")},
                "band_code": {"__term__": Attr(bd, "band_code")},
                "audience_gain": {"__term__": Attr(bd, "audience_gain")},
            }),
            add_node_effect("sig", "RuleDisputeSignal", {"status": "pending"}),
            add_edge_effect("ctx", "has_signal", "sig"),
            add_edge_effect("bd", "bridged_to", "ctx"),
        ],
    }


# --------------------------------------------------------------------- #
# Rule 2: each witness on the BeliefDisagreement carries over to the newly
# minted DisputeContext -- mirrors the dispute->self-conscious bridge's own
# per-witness rule exactly.
# --------------------------------------------------------------------- #
def rule_carry_over_witnesses():
    bd, wp, ctx = Var("bd"), Var("wp"), Var("ctx")
    where = AndT([
        Eq(CountT(Neighbours(wp, "mirrored_as")), Lit(0)),
    ])
    return {
        "name": "carry_over_belief_disagreement_witnesses",
        "comment": (
            "PREREG Sec2: each WitnessPresence already on the "
            "BeliefDisagreement mints a corresponding WitnessPresence on "
            "the newly minted DisputeContext, closeness copied unchanged -- "
            "the SAME node type reused (WitnessPresence is rule_dispute_"
            "escalation's own audience primitive; this rung does not "
            "reinterpret it). Guarded by a mirrored_as dedup edge per "
            "witness."
        ),
        "match_type": "WitnessPresence",
        "match": [
            ["bd", "has_witness", "wp"],
            ["bd", "bridged_to", "ctx"],
        ],
        "where": where,
        "effects": [
            add_node_effect("wp2", "WitnessPresence", {
                "closeness": {"__term__": Attr(wp, "closeness")},
            }),
            add_edge_effect("ctx", "has_witness", "wp2"),
            add_edge_effect("wp", "mirrored_as", "wp2"),
        ],
    }


# --------------------------------------------------------------------- #
# Rule 3: an OPTIONAL SelfPattern on the BeliefDisagreement carries over to
# the newly minted DisputeContext -- mirrors rule_carry_over_witnesses
# exactly. WIRE_IN_PREREG.md: closes the gap that stopped the full chain
# from composing -- without this, a DisputeContext minted BY this seed
# (rather than hand-built by a caller) had nowhere for
# rule_dispute_self_conscious_bridge.json's own has_self_pattern edge to
# attach.
# --------------------------------------------------------------------- #
def rule_carry_over_self_pattern():
    bd, pattern, ctx = Var("bd"), Var("pattern"), Var("ctx")
    where = AndT([
        Eq(CountT(Neighbours(pattern, "mirrored_as")), Lit(0)),
    ])
    return {
        "name": "carry_over_belief_disagreement_self_pattern",
        "comment": (
            "WIRE_IN_PREREG.md: a SelfPattern already on the "
            "BeliefDisagreement (0 or 1, optional, mirrors rule_dispute_"
            "self_conscious_bridge.json's own has_self_pattern shape "
            "exactly) carries over to the newly minted DisputeContext, "
            "held_self_worth copied unchanged -- the SAME node type reused "
            "(SelfPattern is the self-conscious bridge's own primitive; "
            "this rung does not reinterpret it). Guarded by a mirrored_as "
            "dedup edge."
        ),
        "match_type": "SelfPattern",
        "match": [
            ["bd", "has_self_pattern", "pattern"],
            ["bd", "bridged_to", "ctx"],
        ],
        "where": where,
        "effects": [
            add_node_effect("pattern2", "SelfPattern", {
                "held_self_worth": {"__term__": Attr(pattern, "held_self_worth")},
            }),
            add_edge_effect("ctx", "has_self_pattern", "pattern2"),
            add_edge_effect("pattern", "mirrored_as", "pattern2"),
        ],
    }


SEED = {
    "id": "dispute_severity_from_beliefs",
    "version": "1.1.0",
    "depends_on": ["rule_dispute_escalation"],
    "self_load_only": True,
    "description": (
        "issue_severity, computed: 1-StructSim(claim.pred, truth.pred) -- "
        "the residual between what a disputant claims and what the "
        "rulebook-grounded ground truth actually says -- replacing "
        "rule_dispute_escalation.json's own caller-supplied scalar with a "
        "genuinely derived value, per the user's own diagnosis ('a dispute "
        "is the residual between two held beliefs') and CLAUDE.md's "
        "SHAPES-NOT-NUMBERS rule (a hand-set scalar knob is unpaid debt). "
        "Strictly additive: rule_dispute_escalation.json is NOT edited, "
        "reused via its own unchanged has_signal production. Fires ONLY "
        "when a genuine residual exists (StructSim<1.0) -- identical "
        "beliefs mint no dispute at all, a live correction after finding "
        "severity=0.0 does not structurally floor the downstream pressure "
        "formula (ambient audience/closeness terms are independent of "
        "severity). Zero new Rust "
        "-- StructSim, like every other Term this arc has used, "
        "pre-existed (runners/dsl/src/term.rs::struct_sim_value), "
        "confirmed by direct probe before registering (PREREG Sec1: 0.667 "
        "similarity / 0.333 residual on a one-slot contradiction, 1.0/0.0 "
        "on identical predications) rather than assumed. v1.1.0 "
        "(WIRE_IN_PREREG.md): an optional SelfPattern on the "
        "BeliefDisagreement now carries over to the minted DisputeContext, "
        "mirroring witness carry-over exactly -- closes the gap that "
        "stopped this seed and rule_dispute_self_conscious_bridge.json "
        "from composing end to end when a dispute originates from raw "
        "beliefs rather than a hand-built DisputeContext. See "
        "DISPUTE_SEVERITY_AS_RESIDUAL_PREREG.md / _RESULTS.md and "
        "WIRE_IN_PREREG.md."
    ),
    "nodes": [],
    "edges": [],
    "productions": [
        {
            "src": {"type": "BeliefDisagreement", "var": "bd"},
            "edge_type": "claims",
            "tgt": {"type": "HeldBelief", "var": "claims"},
            "where": None,
            "weight": {"type": "Lit", "value": 1.0},
            "provenance": "dispute_severity_from_beliefs",
        },
        {
            "src": {"type": "BeliefDisagreement", "var": "bd"},
            "edge_type": "truth",
            "tgt": {"type": "HeldBelief", "var": "truth"},
            "where": None,
            "weight": {"type": "Lit", "value": 1.0},
            "provenance": "dispute_severity_from_beliefs",
        },
        {
            "src": {"type": "BeliefDisagreement", "var": "bd"},
            "edge_type": "has_witness",
            "tgt": {"type": "WitnessPresence", "var": "wp"},
            "where": None,
            "weight": {"type": "Lit", "value": 1.0},
            "provenance": "dispute_severity_from_beliefs",
        },
        {
            "src": {"type": "BeliefDisagreement", "var": "bd"},
            "edge_type": "bridged_to",
            "tgt": {"type": "DisputeContext", "var": "ctx"},
            "where": None,
            "weight": {"type": "Lit", "value": 1.0},
            "provenance": "dispute_severity_from_beliefs",
        },
        {
            "src": {"type": "WitnessPresence", "var": "wp"},
            "edge_type": "mirrored_as",
            "tgt": {"type": "WitnessPresence", "var": "wp2"},
            "where": None,
            "weight": {"type": "Lit", "value": 1.0},
            "provenance": "dispute_severity_from_beliefs",
        },
        {
            "src": {"type": "BeliefDisagreement", "var": "bd"},
            "edge_type": "has_self_pattern",
            "tgt": {"type": "SelfPattern", "var": "pattern"},
            "where": None,
            "weight": {"type": "Lit", "value": 1.0},
            "provenance": "dispute_severity_from_beliefs",
        },
        {
            "src": {"type": "DisputeContext", "var": "ctx"},
            "edge_type": "has_self_pattern",
            "tgt": {"type": "SelfPattern", "var": "pattern2"},
            "where": None,
            "weight": {"type": "Lit", "value": 1.0},
            "provenance": "dispute_severity_from_beliefs",
        },
        {
            "src": {"type": "SelfPattern", "var": "pattern"},
            "edge_type": "mirrored_as",
            "tgt": {"type": "SelfPattern", "var": "pattern2"},
            "where": None,
            "weight": {"type": "Lit", "value": 1.0},
            "provenance": "dispute_severity_from_beliefs",
        },
    ],
    "concepts": [
        {
            "name": "dispute_severity_as_residual",
            "definition": (
                "A rule dispute's issue_severity is the structural residual "
                "between a disputant's claimed belief and the rulebook-"
                "grounded ground truth -- 1 minus their StructSim similarity "
                "-- not a hand-set scalar. Two identical beliefs produce "
                "zero severity structurally; a partial contradiction "
                "produces a graded, measured residual."
            ),
            "why": (
                "User: 'A dispute is the residual between two held "
                "beliefs' -- a direct correction of "
                "rule_dispute_escalation.json's own hand-picked "
                "issue_severity input. DISPUTE_SEVERITY_AS_RESIDUAL_"
                "PREREG.md."
            ),
        },
    ],
    "exclusions": [],
    "rules": [
        rule_severity_from_beliefs(),
        rule_carry_over_witnesses(),
        rule_carry_over_self_pattern(),
    ],
}

print(json.dumps(SEED, indent=1))
