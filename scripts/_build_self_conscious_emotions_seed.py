"""One-off authoring script that EMITS seeds/self_conscious_emotions.json.

Not agent runtime -- a tool script (CLAUDE.md's `tools/*` precedent). Builds
the Term-tree JSON by hand-nested dicts, mirroring
scripts/_build_rule_dispute_escalation_seed.py's own builder shape.

See docs/research/psychology_affect/SELF_CONSCIOUS_EMOTIONS_PREREG.md for
the full registered design this script implements.

Run: python3 scripts/_build_self_conscious_emotions_seed.py > seeds/self_conscious_emotions.json
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


def LetT(name, value, body):
    return {"type": "Let", "name": name, "value": value, "body": body}


def Neighbours(node, edge_type):
    return {"type": "Neighbours", "node": node, "edge_type": edge_type}


def ExistsT(source, var_name, predicate):
    return {"type": "Exists", "source": source, "var_name": var_name, "predicate": predicate}


def term_effect(node, key, term):
    return ["set_attr", node, key, {"__term__": term}]


def lit_effect(node, key, value):
    return ["set_attr", node, key, value]


# --------------------------------------------------------------------- #
# perceived_violation = Exists(witnesses, judgment == "violated") --
# PREREG Sec2/Sec3 prediction 5: reads WITNESS BELIEF, not ground truth
# (standard_met) -- the second-order-belief primitive this rung adds.
# --------------------------------------------------------------------- #
def _perceived_violation_term(ctx_var="ctx"):
    witness = Var("witness")
    return ExistsT(
        source=Neighbours(Var(ctx_var), "has_witness_belief"),
        var_name="witness",
        predicate=Eq(Attr(witness, "judgment"), Lit("violated")),
    )


def _emotion_term(ctx_var="ctx"):
    """PREREG Sec2's registered classification table -- a categorical
    lookup, not a scalar quantization, so IfThenElse (not Argmin-over-
    codebook) is the correct existing primitive here."""
    ctx = Var(ctx_var)
    locus = Attr(ctx, "attribution_locus")
    standard_met = Eq(Attr(ctx, "standard_met"), Lit(1.0))
    return LetT(
        "perceived_violation", _perceived_violation_term(ctx_var),
        IfThenElse(
            Eq(locus, Lit("circumstance")),
            IfThenElse(Var("perceived_violation"), Lit("embarrassment"), Lit("none")),
            IfThenElse(
                Eq(locus, Lit("global_self")),
                IfThenElse(standard_met, Lit("hubristic_pride"), Lit("shame")),
                # specific_act (the only remaining registered locus value)
                IfThenElse(standard_met, Lit("authentic_pride"), Lit("guilt")),
            ),
        ),
    )


# --------------------------------------------------------------------- #
# The rule
# --------------------------------------------------------------------- #
def rule_decide_emotion():
    sig = Var("sig")
    where = AndT([
        Eq(Attr(sig, "status"), Lit("pending")),
    ])
    return {
        "name": "sc_decide_emotion",
        "comment": (
            "PREREG Sec2-3: classifies a self-conscious episode into "
            "{hubristic_pride, authentic_pride, shame, guilt, embarrassment, "
            "none} from (standard_met, attribution_locus, perceived_"
            "violation). standard_met (the agent's OWN ground truth) drives "
            "the shame/guilt/pride axis regardless of exposure (Tangney, "
            "Miller, Flicker & Barlow 1996: shame/guilt are NOT reliably "
            "audience-dependent). perceived_violation -- Exists over "
            "WitnessBelief.judgment, which may DIVERGE from standard_met -- "
            "drives embarrassment specifically, gated to the circumstance-"
            "attributed cell only (Miller 1996: embarrassment attributes to "
            "circumstance/involuntary exposure, not a moral standard "
            "violation; Tangney et al. 1996: embarrassment IS reliably "
            "audience-dependent, the one cell this design gates on "
            "exposure). Pride bifurcates the same way shame/guilt do "
            "(Tracy & Robins 2007): global_self attribution -> hubristic, "
            "specific_act attribution -> authentic. attribution_locus is "
            "CATEGORICAL (Lewis 1971's three-way split), not a continuous "
            "scalar, so this is a genuine lookup table (IfThenElse), not a "
            "misapplied Argmin-over-codebook quantization. Zero new Rust -- "
            "Eq/And/IfThenElse/Let/Exists/Neighbours/Attr/Var/Lit all "
            "pre-existed. The emotion DECISION is this Rule's own nested "
            "IfThenElse, not Python."
        ),
        "match_type": "SelfConsciousSignal",
        "match": [
            ["ctx", "has_appraisal", "sig"],
        ],
        "where": where,
        "effects": [
            term_effect("sig", "perceived_violation", _perceived_violation_term("ctx")),
            term_effect("sig", "emotion", _emotion_term("ctx")),
            lit_effect("sig", "status", "decided"),
        ],
    }


SEED = {
    "id": "self_conscious_emotions",
    "version": "1.0.0",
    "depends_on": [],
    "self_load_only": True,
    "description": (
        "Classifies a self-conscious episode (did the agent, by its own "
        "knowledge, meet a Standard; what attribution locus applies; did "
        "any witness form a belief -- possibly diverging from ground truth "
        "-- that the standard was violated) into {hubristic_pride, "
        "authentic_pride, shame, guilt, embarrassment, none}, per the "
        "Lewis (1971) / Tracy & Robins (2004, 2007) / Miller (1996) / "
        "Tangney, Miller, Flicker & Barlow (1996) appraisal literature -- "
        "SELF_CONSCIOUS_EMOTIONS_PREREG.md. Reuses the "
        "SmEntity-belief_world nested-belief SHAPE domains/character_tom.py "
        "already established (a witness's belief about the agent is a node "
        "structurally distinct from ground truth), applied to a NEW, "
        "live-encounter trigger (WitnessBelief nodes minted mechanically, "
        "not via NLP attitude-sentence parsing) and NEW, reflexively "
        "self-directed content (a witness's judgment of the APPRAISING "
        "agent). standard_met drives the shame/guilt/pride axis regardless "
        "of exposure (Tangney et al. 1996); perceived_violation -- read "
        "from witness belief, which may diverge from standard_met -- "
        "drives embarrassment specifically, gated to the "
        "circumstance-attributed cell (Miller 1996). Zero new Rust Terms."
    ),
    "nodes": [],
    "edges": [],
    "productions": [
        {
            "src": {"type": "SelfConsciousContext", "var": "ctx"},
            "edge_type": "has_appraisal",
            "tgt": {"type": "SelfConsciousSignal", "var": "sig"},
            "where": None,
            "weight": {"type": "Lit", "value": 1.0},
            "provenance": "self_conscious_emotions",
        },
        {
            "src": {"type": "SelfConsciousContext", "var": "ctx"},
            "edge_type": "has_witness_belief",
            "tgt": {"type": "WitnessBelief", "var": "witness"},
            "where": None,
            "weight": {"type": "Lit", "value": 1.0},
            "provenance": "self_conscious_emotions",
        },
    ],
    "concepts": [
        {
            "name": "self_conscious_emotion_appraisal",
            "definition": (
                "A self-conscious emotion (pride/shame/guilt/embarrassment) "
                "is a categorical function of standard-compliance, "
                "attribution locus (global-self / specific-act / "
                "circumstance), and perceived (not necessarily actual) "
                "social exposure -- distinct emotions for the same outcome "
                "depending on WHERE the cause is attributed, and one "
                "specific cell (circumstance) gated on whether any witness "
                "believes a violation occurred, independent of whether one "
                "actually did."
            ),
            "why": (
                "The user asked whether CAN/PSI can produce embarrassment "
                "'and otherwise' -- a research pass found three missing "
                "primitives (reflexive second-order belief, a violable "
                "Standard, attribution-locus classification); this seed "
                "supplies all three. SELF_CONSCIOUS_EMOTIONS_PREREG.md."
            ),
        },
    ],
    "exclusions": [],
    "rules": [
        rule_decide_emotion(),
    ],
}

print(json.dumps(SEED, indent=1))
