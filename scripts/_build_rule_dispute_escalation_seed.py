"""One-off authoring script that EMITS seeds/rule_dispute_escalation.json.

Not agent runtime -- a tool script (CLAUDE.md's `tools/*` precedent). Builds
the Term-tree JSON by hand-nested dicts, mirroring
scripts/_build_can_register_quantization_seed.py's own builder shape and
calling convention exactly (Var/Lit/Attr/... helpers, term_effect/lit_effect,
a DisputeContext->has_signal->RuleDisputeSignal production/match pair byte-
identical in SHAPE to that seed's RegisterProfile->observed_band->
RegisterObservation).

See docs/research/engine_substrate/RULE_DISPUTE_ESCALATION_PREREG.md for the
full registered design this script implements.

Run: python3 scripts/_build_rule_dispute_escalation_seed.py > seeds/rule_dispute_escalation.json
"""
import json


# --------------------------------------------------------------------- #
# Term-tree builders (mirrors _build_can_register_quantization_seed.py)
# --------------------------------------------------------------------- #
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


def PlusT(items):
    return {"type": "Plus", "items": items}


def MinusT(a, b):
    return {"type": "Minus", "a": a, "b": b}


def TimesT(items):
    return {"type": "Times", "items": items}


def DivT(a, b):
    return {"type": "Div", "a": a, "b": b}


def AbsT(arg):
    return {"type": "Abs", "arg": arg}


def LetT(name, value, body):
    return {"type": "Let", "name": name, "value": value, "body": body}


def ArgminT(source, var_name, value):
    return {"type": "Argmin", "source": source, "var_name": var_name, "value": value}


def NodesOfType(node_type):
    return {"type": "NodesOfType", "node_type": node_type}


def Neighbours(node, edge_type):
    return {"type": "Neighbours", "node": node, "edge_type": edge_type}


def SumT(source, var_name, value):
    return {"type": "Sum", "source": source, "var_name": var_name, "value": value}


def term_effect(node, key, term):
    return ["set_attr", node, key, {"__term__": term}]


def lit_effect(node, key, value):
    return ["set_attr", node, key, value]


# --------------------------------------------------------------------- #
# Shared sub-expressions -- PREREG Sec2. `closeness` and `pressure` are
# each re-derived from scratch inside every effect that needs them (same
# no-cross-effect-read-your-own-write discipline the register rung's
# builder already documents and follows).
# --------------------------------------------------------------------- #
def _closeness_term(ctx_var="ctx"):
    """closeness = band_code / 5.0 -- PREREG Sec2's documented, un-fitted
    normalization. band_code=-1 (rival) yields closeness=-0.2, deliberately
    BELOW the band_code=0 (stranger) floor of 0.0 -- PREREG Prediction 5's
    floor-sanity check depends on this NOT being clamped to 0."""
    return DivT(Attr(Var(ctx_var), "band_code"), Lit(5.0))


def _audience_term(ctx_var="ctx"):
    """PREREG Sec3b (Rung 2): sum, over each PRESENT witness, of
    audience_gain*(1-witness.closeness) -- each witness contributes their
    OWN suppression (closeness to whichever disputant they'd regulate,
    Sbarra & Hazan 2008 coregulation), not the dyad's. An anonymous witness
    (closeness=0.0) contributes audience_gain*(1-0)=audience_gain, so N
    anonymous witnesses reproduce Rung 1's witnesses=N case exactly --
    generalization, not a behavior change for the already-tested cases."""
    ctx = Var(ctx_var)
    witness = Var("witness")
    return SumT(
        source=Neighbours(ctx, "has_witness"),
        var_name="witness",
        value=TimesT([
            Attr(ctx, "audience_gain"),
            MinusT(Lit(1.0), Attr(witness, "closeness")),
        ]),
    )


def _pressure_term(ctx_var="ctx"):
    """pressure = issue_severity + audience_term - closeness -- PREREG
    Sec2/Sec3b's registered composition. The dyad's own closeness still
    suppresses pressure directly (the two disputants' own relationship);
    each witness separately suppresses via their OWN closeness inside
    _audience_term, the load-bearing Rung 2 generalization."""
    ctx = Var(ctx_var)
    closeness = _closeness_term(ctx_var)
    return MinusT(
        PlusT([Attr(ctx, "issue_severity"), _audience_term(ctx_var)]),
        closeness,
    )


def _outcome_term(ctx_var="ctx"):
    return LetT(
        "pressure", _pressure_term(ctx_var),
        Attr(
            ArgminT(
                source=NodesOfType("DisputeOutcomeAnchor"),
                var_name="anchor",
                value=AbsT(MinusT(Var("pressure"), Attr(Var("anchor"), "canonical_value"))),
            ),
            "label",
        ),
    )


# --------------------------------------------------------------------- #
# The rule
# --------------------------------------------------------------------- #
def rule_decide_outcome():
    sig = Var("sig")
    where = AndT([
        Eq(Attr(sig, "status"), Lit("pending")),
    ])
    return {
        "name": "rd_decide_outcome",
        "comment": (
            "PREREG Sec2: composes a scalar 'pressure' from issue_severity "
            "(how starkly a claim contradicts the resident's own document-"
            "grounded HeldRule reading), closeness (band_code/5.0, reusing "
            "bigville's already-built band_code/tie_strength plumbing "
            "verbatim -- bigville commit 1b79a0f), and witnesses (bystander "
            "count, a bare integer -- who else is in the room), then "
            "classifies against a 2-entry DisputeOutcomeAnchor codebook "
            "(defuse/escalate) via Argmin nearest-point decode -- the SAME "
            "compose-then-Argmin-classify shape can_register_decode_band "
            "already established (seeds/can_register_quantization.json), "
            "reused here for a different composed quantity. ALL arithmetic "
            "(Div/Times/Minus/Plus/Abs/Let/Argmin/Attr/Var/Lit/Eq/And) is "
            "pre-existing Term vocabulary -- zero new Rust. The escalate-"
            "vs-defuse DECISION is this Rule's own Argmin call, not Python."
        ),
        "match_type": "RuleDisputeSignal",
        "match": [
            ["ctx", "has_signal", "sig"],
        ],
        "where": where,
        "effects": [
            term_effect("sig", "closeness", _closeness_term("ctx")),
            term_effect("sig", "pressure", _pressure_term("ctx")),
            term_effect("sig", "outcome", _outcome_term("ctx")),
            lit_effect("sig", "status", "decided"),
        ],
    }


# --------------------------------------------------------------------- #
# DisputeOutcomeAnchor codebook -- PREREG Sec2, byte-identical shape to
# RegisterLabelAnchor (2 fixed anchors instead of 3; no continuous-math
# authoring step is needed here, unlike BandAffinityAnchor's one-time Exp
# computation, since neither anchor value is a saturating curve).
# --------------------------------------------------------------------- #
def dispute_outcome_anchor_nodes():
    labels = [("defuse", -1.0), ("escalate", 1.0)]
    out = []
    for i, (label, canonical_value) in enumerate(labels, start=1):
        out.append({
            "local_id": i,
            "type": "DisputeOutcomeAnchor",
            "attrs": {"label": label, "canonical_value": canonical_value},
        })
    return out


NODES = dispute_outcome_anchor_nodes()

SEED = {
    "id": "rule_dispute_escalation",
    "version": "1.1.0",
    "depends_on": [],
    "self_load_only": True,
    "description": (
        "Composes a dyadic rule-dispute's issue severity, relationship "
        "closeness (band_code/tie_strength, reusing bigville's already-"
        "built plumbing verbatim -- commit 1b79a0f), and bystander/witness "
        "count into a scalar 'pressure', classified via Argmin nearest-"
        "point decode against a 2-entry DisputeOutcomeAnchor codebook "
        "(defuse/escalate) -- the SAME compose-then-Argmin-classify shape "
        "seeds/can_register_quantization.json already established, reused "
        "here rather than reinvented (RULE_DISPUTE_ESCALATION_PREREG.md "
        "Sec1's own SHAPES-not-numbers justification). The load-bearing "
        "design choice is the (1-closeness) interaction term: audience "
        "presence amplifies escalation (Felson 1982, 'Impression "
        "Management and the Escalation of Aggression and Violence'), but "
        "closeness SUPPRESSES that amplification rather than merely "
        "offsetting it additively (Coleman, Deutsch & Marcus, Handbook of "
        "Conflict Resolution -- established cooperative-norm relationships "
        "actively resist destructive escalation) -- the same interaction-"
        "effect shape Giles' Communication Accommodation Theory already "
        "gave this session's register/style work (convergence in-group, "
        "divergence out-group). Zero new Rust Terms -- Div/Times/Minus/"
        "Plus/Abs/Let/Argmin/Attr/Var/Lit/Eq/And all pre-existed. v1.1.0 "
        "(Rung 2, PREREG Sec3b) generalizes the bare 'witnesses' count into "
        "WitnessPresence nodes, each carrying its OWN closeness to "
        "whichever disputant they'd regulate (Sbarra & Hazan 2008, "
        "coregulation) -- audience_gain*(1-witness.closeness), summed via "
        "the pre-existing Sum/Neighbours Terms, not a new principle; an "
        "anonymous witness (closeness=0.0) reproduces Rung 1's per-witness "
        "contribution exactly. See RULE_DISPUTE_ESCALATION_PREREG.md / "
        "_RESULTS.md."
    ),
    "nodes": NODES,
    "edges": [],
    "productions": [
        {
            "src": {"type": "DisputeContext", "var": "ctx"},
            "edge_type": "has_signal",
            "tgt": {"type": "RuleDisputeSignal", "var": "sig"},
            "where": None,
            "weight": {"type": "Lit", "value": 1.0},
            "provenance": "rule_dispute_escalation",
        },
        {
            "src": {"type": "DisputeContext", "var": "ctx"},
            "edge_type": "has_witness",
            "tgt": {"type": "WitnessPresence", "var": "witness"},
            "where": None,
            "weight": {"type": "Lit", "value": 1.0},
            "provenance": "rule_dispute_escalation",
        },
    ],
    "concepts": [
        {
            "name": "rule_dispute_escalation",
            "definition": (
                "A tabletop rules disagreement's outcome (defuse or "
                "escalate into an argument) is a scalar composition of "
                "issue severity, dyadic closeness, and audience size, "
                "classified via Argmin nearest-point decode against a held "
                "2-entry outcome codebook -- the register-quantization "
                "rung's compose-then-classify shape, applied to a "
                "conflict-pressure quantity instead of a communication-"
                "style quantity."
            ),
            "why": (
                "The user asked for a testable scenario where two Bigville "
                "board-game residents disagree about a rule, and the "
                "disagreement either defuses or escalates depending on the "
                "nature of the issue, the two people, and who else is in "
                "the room -- RULE_DISPUTE_ESCALATION_PREREG.md."
            ),
        },
    ],
    "exclusions": [],
    "rules": [
        rule_decide_outcome(),
    ],
}

print(json.dumps(SEED, indent=1))
