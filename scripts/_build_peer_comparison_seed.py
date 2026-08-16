"""One-off authoring script that EMITS seeds/peer_comparison.json.

Not agent runtime -- a tool script (CLAUDE.md's `tools/*` precedent).
Strictly additive over the CAN network's own Concept nodes -- nothing in
worlds/bigville_can_beliefs.py or seeds/can_native_reimplementation.json
is edited.

See docs/research/psychology_affect/RELATIVE_SELF_WORTH_PREREG.md for the
full registered design. Reuses seeds/can_native_reimplementation.json's
Coactivation-style Laplace-smoothed log-odds formula VERBATIM
(LOGODDS_GENERATOR_PREREG.md Sec2) -- not a new formula.

Run: python3 scripts/_build_peer_comparison_seed.py > seeds/peer_comparison.json
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


def Neighbours(node, edge_type):
    return {"type": "Neighbours", "node": node, "edge_type": edge_type}


def FilterT(source, var_name, predicate):
    return {"type": "Filter", "source": source, "var_name": var_name, "predicate": predicate}


def CountT(source):
    return {"type": "Count", "source": source}


def PlusT(items):
    return {"type": "Plus", "items": items}


def MinusT(a, b):
    return {"type": "Minus", "a": a, "b": b}


def DivT(a, b):
    return {"type": "Div", "a": a, "b": b}


def LogT(arg):
    return {"type": "Log", "arg": arg}


def NotT(arg):
    return {"type": "Not", "arg": arg}


def term_effect(node, key, term):
    return ["set_attr", node, key, {"__term__": term}]


# --------------------------------------------------------------------- #
# peer_log_odds = ln((confirm+1)/(disconfirm+1)) -- LOGODDS_GENERATOR_
# PREREG.md's own registered formula, reused verbatim (PREREG Sec1).
# --------------------------------------------------------------------- #
def _peer_confirm_term(ctx_var="ctx"):
    obs = Var("obs")
    return CountT(FilterT(
        Neighbours(Var(ctx_var), "has_observation"), "obs",
        Eq(Attr(obs, "outcome"), Lit("did_well")),
    ))


def _peer_disconfirm_term(ctx_var="ctx"):
    obs = Var("obs")
    return CountT(FilterT(
        Neighbours(Var(ctx_var), "has_observation"), "obs",
        Eq(Attr(obs, "outcome"), Lit("did_poorly")),
    ))


def _peer_log_odds_term(ctx_var="ctx"):
    return LogT(DivT(
        PlusT([_peer_confirm_term(ctx_var), Lit(1)]),
        PlusT([_peer_disconfirm_term(ctx_var), Lit(1)]),
    ))


def _relative_self_worth_term(concept_var="concept", ctx_var="ctx"):
    return MinusT(Attr(Var(concept_var), "state"), _peer_log_odds_term(ctx_var))


# --------------------------------------------------------------------- #
# The rule -- a STABLE-FIXPOINT recompute (mirrors can_native_update_
# 3state's own "refire only while stale" idiom, PREREG Sec2): fires
# whenever the computed value differs from the stored one, so it responds
# live to BOTH new peer observations AND the domain Concept's own state
# changing (from record_incident_outcome), not a one-shot mint.
# --------------------------------------------------------------------- #
def rule_compute_relative_self_worth():
    concept, ctx = Var("concept"), Var("ctx")
    where = NotT(Eq(
        Attr(concept, "relative_self_worth"),
        _relative_self_worth_term("concept", "ctx"),
    ))
    return {
        "name": "compute_relative_self_worth",
        "comment": (
            "PREREG Sec2: relative_self_worth = domain_concept.state - "
            "peer_log_odds, peer_log_odds computed via the SAME Laplace-"
            "smoothed formula LOGODDS_GENERATOR_PREREG.md already "
            "registered (ln((confirm+1)/(disconfirm+1))) -- zero "
            "observations yields a genuinely neutral 0.0 (Festinger's "
            "'fictional midpoint', constructed via the Laplace +1 on each "
            "side, not asserted as a constant). A stable-fixpoint recompute "
            "(Not(Eq(stored, computed)) guard, mirroring can_native_"
            "update_3state's own idiom) -- refires whenever EITHER new "
            "peer observations arrive OR the domain Concept's own state "
            "changes (record_incident_outcome, unchanged), so self-worth "
            "genuinely can drop from a shifted comparison baseline with "
            "zero change to the resident's own track record (the user's "
            "own registered claim, PREREG Sec3 prediction 3). Zero new "
            "Rust -- Log/Div/Plus/Minus/Count/Filter/Neighbours/Attr/Var/"
            "Lit/Eq/Not all pre-existed."
        ),
        "match_type": "Concept",
        "match": [
            ["concept", "has_peer_comparison", "ctx"],
        ],
        "where": where,
        "effects": [
            term_effect("concept", "relative_self_worth", _relative_self_worth_term("concept", "ctx")),
        ],
    }


SEED = {
    "id": "peer_comparison",
    "version": "1.0.0",
    "depends_on": ["can_native_reimplementation"],
    "self_load_only": True,
    "description": (
        "Social comparison as a log-weighted evidence channel, SEPARATE "
        "from a resident's own incident history: relative_self_worth = "
        "domain_concept.state - peer_log_odds, where peer_log_odds is the "
        "SAME Laplace-smoothed log-odds formula LOGODDS_GENERATOR_PREREG.md "
        "already registered, applied to accumulated PeerObservation counts "
        "instead of Coactivation counts. Per the user's own diagnosis: 'you "
        "measure yourself by what you observe - this is a massive problem "
        "now in the social media era where you see the highlight reels of "
        "other people, so you feel less by comparison' (Chou & Edge 2012; "
        "Vogel et al. 2014) and 'your self worth can drop without dropping "
        "- if you assume the standard person is better - your self worth "
        "just dropped' (Stouffer et al. 1949, relative deprivation; "
        "Festinger 1954, social comparison). Zero real observations yields "
        "a genuinely neutral 0.0 fictional midpoint (the Laplace +1 IS "
        "'making it up' when nothing real exists), not a hand-picked "
        "constant. Strictly additive over the CAN network's own Concept "
        "nodes -- can_native_reimplementation.json is NOT edited. See "
        "RELATIVE_SELF_WORTH_PREREG.md / _RESULTS.md."
    ),
    "nodes": [],
    "edges": [],
    "productions": [
        {
            "src": {"type": "Concept", "var": "concept"},
            "edge_type": "has_peer_comparison",
            "tgt": {"type": "PeerComparisonContext", "var": "ctx"},
            "where": None,
            "weight": {"type": "Lit", "value": 1.0},
            "provenance": "peer_comparison",
        },
        {
            "src": {"type": "PeerComparisonContext", "var": "ctx"},
            "edge_type": "has_observation",
            "tgt": {"type": "PeerObservation", "var": "obs"},
            "where": None,
            "weight": {"type": "Lit", "value": 1.0},
            "provenance": "peer_comparison",
        },
    ],
    "concepts": [
        {
            "name": "relative_self_worth_via_social_comparison",
            "definition": (
                "Felt self-worth is comparative, not absolute: it is one's "
                "own track record MINUS a log-odds baseline constructed "
                "from observations of others, which is itself constructed "
                "from nothing (a genuinely neutral, invented midpoint) when "
                "no real observations exist, and can become severely "
                "skewed when the observation channel itself is biased "
                "(social media's 'highlight reel' effect) -- moving the "
                "baseline moves felt self-worth even with zero change to "
                "one's own actual competence or track record."
            ),
            "why": (
                "User: three corrections in sequence -- weights must be "
                "log-scaled against a constructed (not hand-picked) "
                "midpoint, weighted to other real nodes (social "
                "comparison), and self-worth can drop purely from the "
                "comparison baseline shifting. RELATIVE_SELF_WORTH_"
                "PREREG.md."
            ),
        },
    ],
    "exclusions": [],
    "rules": [
        rule_compute_relative_self_worth(),
    ],
}

print(json.dumps(SEED, indent=1))
