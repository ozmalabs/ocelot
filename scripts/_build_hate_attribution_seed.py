"""One-off authoring script that EMITS seeds/hate_attribution.json.

Not agent runtime -- a tool script (CLAUDE.md's `tools/*` precedent).
Generalizes ATTRIBUTION_LOCUS_AS_RESIDUAL_PREREG.md's self-directed
residual outward (a held pattern about ANOTHER agent instead of oneself),
adds a stability gate (Sternberg 2003's decision/commitment component)
and a motivational consequence (Fischer, Halperin, Canetti & Jasini
2018's elimination goal) gated behind it. See docs/research/
psychology_affect/HATE_ATTRIBUTION_PREREG.md for the full registered
design.

Run: python3 scripts/_build_hate_attribution_seed.py > seeds/hate_attribution.json
"""
import json

HATE_STABILITY_THRESHOLD = 3


def Var(name):
    return {"type": "Var", "name": name}


def Lit(value):
    return {"type": "Lit", "value": value}


def Attr(node, key):
    return {"type": "Attr", "node": node, "key": key}


def Eq(a, b):
    return {"type": "Eq", "a": a, "b": b}


def Gt(a, b):
    return {"type": "Gt", "a": a, "b": b}


def Gte(a, b):
    return {"type": "Gte", "a": a, "b": b}


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


def PlusT(items):
    return {"type": "Plus", "items": items}


def term_effect(node, key, term):
    return ["set_attr", node, key, {"__term__": term}]


def add_node_effect(var_name, node_type, attrs):
    return ["add_node", var_name, node_type, attrs]


def add_edge_effect(src, edge_type, tgt):
    return ["add_edge", src, edge_type, tgt]


# --------------------------------------------------------------------- #
# The residual -- HATE_ATTRIBUTION_PREREG.md Sec2, ATTRIBUTION_LOCUS_AS_
# RESIDUAL_PREREG.md's own mechanism generalized outward, held_regard now
# LIVE-WIRED to the tracked regard_for Concept's own `state` instead of
# supplied data (that PREREG's own deferred scope note, attempted here).
# --------------------------------------------------------------------- #
def _held_regard_term(pat_var="pat"):
    # external_field (the continuous evidence accumulator), NOT the
    # discrete relaxed `state` -- the ~0.366-at-temperature-1.5 discrete
    # threshold this arc already found (SELF_COMPLEXITY_COUPLING_RESULTS.
    # md) means `state` can sit at exactly 0.0 for several incidents in a
    # row even while real evidence is accumulating, which would silently
    # misread every one of those incidents as "no held pattern yet" /
    # "disagrees" instead of tracking the agent's actual accumulating
    # impression. external_field has no such floor.
    return Attr(PickUniqueT(Neighbours(Var(pat_var), "tracks_concept")), "external_field")


def _incident_signal_term(ir_var="ir"):
    return Attr(Var(ir_var), "signal")


def _is_first_term(pat_var="pat"):
    return Eq(Attr(Var(pat_var), "incident_count"), Lit(0))


def _confirms_term(pat_var="pat", ir_var="ir"):
    return Gt(
        TimesT([_held_regard_term(pat_var), _incident_signal_term(ir_var)]),
        Lit(0.0),
    )


def _attribution_locus_term(pat_var="pat", ir_var="ir"):
    return IfThenElse(
        _is_first_term(pat_var),
        Lit("first_encounter"),
        IfThenElse(_confirms_term(pat_var, ir_var), Lit("global_other"), Lit("specific_act")),
    )


def _new_streak_term(pat_var="pat", ir_var="ir"):
    is_global = Eq(_attribution_locus_term(pat_var, ir_var), Lit("global_other"))
    return IfThenElse(
        is_global,
        PlusT([Attr(Var(pat_var), "confirm_streak"), Lit(1)]),
        Lit(0),
    )


# --------------------------------------------------------------------- #
# Rule 1: a pending IncidentReport derives its attribution_locus, updates
# the tracked TargetPattern's incident_count + confirm_streak. Guarded by
# status=="pending" -> "appraised" so re-running run_rules() does not
# double-derive.
# --------------------------------------------------------------------- #
def rule_derive_attribution():
    ir, pat = Var("ir"), Var("pat")
    where = Eq(Attr(ir, "status"), Lit("pending"))
    return {
        "name": "derive_hate_attribution",
        "comment": (
            "HATE_ATTRIBUTION_PREREG.md Sec2: attribution_locus is a "
            "RESIDUAL between the incident's own signal and the LIVE "
            "regard_for Concept's state (via tracks_concept) -- no prior "
            "incident -> first_encounter (hate cannot form on a first "
            "impression), signs agree (confirms the held pattern) -> "
            "global_other, signs disagree (an exception) -> specific_act. "
            "confirm_streak increments on global_other, resets to 0 "
            "otherwise (a single exception breaks the pattern -- "
            "prediction 4). Guarded by status pending->appraised so "
            "re-running run_rules() does not double-derive."
        ),
        "match_type": "IncidentReport",
        "match": [
            ["mt", "has_incident_report", "ir"],
            ["ir", "about_pattern", "pat"],
        ],
        "where": where,
        "effects": [
            add_node_effect("appraisal", "HateAppraisal", {
                "attribution_locus": {"__term__": _attribution_locus_term("pat", "ir")},
            }),
            add_edge_effect("ir", "has_appraisal", "appraisal"),
            term_effect("pat", "confirm_streak", _new_streak_term("pat", "ir")),
            term_effect("pat", "incident_count",
                        PlusT([Attr(Var("pat"), "incident_count"), Lit(1)])),
            term_effect("ir", "status", Lit("appraised")),
        ],
    }


# --------------------------------------------------------------------- #
# Rule 2: crystallization -- Sternberg 2003's decision/commitment
# component made concrete. Fires ONCE (guarded by crystallized==0.0) when
# confirm_streak crosses HATE_STABILITY_THRESHOLD.
# --------------------------------------------------------------------- #
def rule_crystallize_hate():
    pat = Var("pat")
    where = AndT([
        Gte(Attr(pat, "confirm_streak"), Lit(HATE_STABILITY_THRESHOLD)),
        Eq(Attr(pat, "crystallized"), Lit(0.0)),
    ])
    return {
        "name": "crystallize_hate",
        "comment": (
            "HATE_ATTRIBUTION_PREREG.md Sec2/prediction 5: crystallization "
            "requires the STABILITY THRESHOLD (confirm_streak >= %d), not "
            "the first global_other confirmation -- Sternberg 2003's "
            "decision/commitment component requires a pattern held over "
            "TIME, not a single outburst. Fires exactly once per "
            "TargetPattern (crystallized==0.0 guard)." % HATE_STABILITY_THRESHOLD
        ),
        "match_type": "TargetPattern",
        "match": [["mt", "has_target_pattern", "pat"]],
        "where": where,
        "effects": [
            term_effect("pat", "crystallized", Lit(1.0)),
            add_node_effect("hate", "Hate", {
                "target": {"__term__": Attr(pat, "target")},
            }),
            add_edge_effect("pat", "has_hate", "hate"),
        ],
    }


SEED = {
    "id": "hate_attribution",
    "version": "1.1.0",
    "depends_on": ["shared_arousal"],
    "self_load_only": True,
    "description": (
        "Generalizes ATTRIBUTION_LOCUS_AS_RESIDUAL_PREREG.md's self-"
        "directed residual outward -- a held pattern about ANOTHER agent "
        "(their regard_for Concept's own live state) instead of oneself. "
        "Adds a stability gate (Sternberg 2003's decision/commitment "
        "component: confirm_streak >= %d) before a Hate marker crystallizes, "
        "and gates a motivational removal_desire_for consequence (Fischer, "
        "Halperin, Canetti & Jasini 2018's elimination goal) behind that "
        "gate, not behind any single angry appraisal. v1.1.0 "
        "(HATE_PASSION_COUPLING_PREREG.md) tracks the SAME shared "
        "TargetArousal pool shared_arousal.json already built (Sternberg's "
        "passion component) and couples the crystallizing incident's "
        "removal_desire_for alpha to it. See HATE_ATTRIBUTION_PREREG.md / "
        "_RESULTS.md, HATE_PASSION_COUPLING_PREREG.md / _RESULTS.md."
        % HATE_STABILITY_THRESHOLD
    ),
    "nodes": [],
    "edges": [],
    "productions": [
        {
            "src": {"type": "Microtheory", "var": "mt"},
            "edge_type": "has_target_pattern",
            "tgt": {"type": "TargetPattern", "var": "pat"},
            "where": None,
            "weight": Lit(1.0),
            "provenance": "hate_attribution",
        },
        {
            "src": {"type": "Microtheory", "var": "mt"},
            "edge_type": "has_incident_report",
            "tgt": {"type": "IncidentReport", "var": "ir"},
            "where": None,
            "weight": Lit(1.0),
            "provenance": "hate_attribution",
        },
        {
            "src": {"type": "IncidentReport", "var": "ir"},
            "edge_type": "about_pattern",
            "tgt": {"type": "TargetPattern", "var": "pat"},
            "where": None,
            "weight": Lit(1.0),
            "provenance": "hate_attribution",
        },
        {
            "src": {"type": "IncidentReport", "var": "ir"},
            "edge_type": "has_appraisal",
            "tgt": {"type": "HateAppraisal", "var": "appraisal"},
            "where": None,
            "weight": Lit(1.0),
            "provenance": "hate_attribution",
        },
        {
            "src": {"type": "TargetPattern", "var": "pat"},
            "edge_type": "has_hate",
            "tgt": {"type": "Hate", "var": "hate"},
            "where": None,
            "weight": Lit(1.0),
            "provenance": "hate_attribution",
        },
        {
            "src": {"type": "TargetPattern", "var": "pat"},
            "edge_type": "tracks_concept",
            "tgt": {"type": "Concept", "var": "c"},
            "where": None,
            "weight": Lit(1.0),
            "provenance": "hate_attribution",
        },
        {
            "src": {"type": "TargetPattern", "var": "pat"},
            "edge_type": "tracks_removal_desire",
            "tgt": {"type": "Concept", "var": "c"},
            "where": None,
            "weight": Lit(1.0),
            "provenance": "hate_attribution",
        },
        {
            "src": {"type": "TargetPattern", "var": "pat"},
            "edge_type": "tracks_arousal",
            "tgt": {"type": "TargetArousal", "var": "arousal"},
            "where": None,
            "weight": Lit(1.0),
            "provenance": "hate_attribution",
        },
    ],
    "rules": [
        rule_derive_attribution(),
        rule_crystallize_hate(),
    ],
    "concepts": [
        {
            "name": "hate_attribution",
            "definition": (
                "Hate is a global+stable negative attribution about "
                "ANOTHER agent, structurally identical to the self-"
                "directed global_self/shame attribution but pointed "
                "outward, gated by a stability requirement (a pattern "
                "held over repeated incidents, not a single outburst) "
                "before it crystallizes and motivates a distinct "
                "removal/elimination goal."
            ),
            "why": (
                "User: 'build the hate attribution mechanism next' -- "
                "following the earlier 'can an agent hate another agent' "
                "discussion. HATE_ATTRIBUTION_PREREG.md."
            ),
        },
    ],
    "exclusions": [],
}

print(json.dumps(SEED, indent=1))
