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


def DivT(a, b):
    return {"type": "Div", "a": a, "b": b}


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


def _arousal_level_term(pat_var="pat"):
    return Attr(PickUniqueT(Neighbours(Var(pat_var), "tracks_arousal")), "level")


def _streak_increment_term(pat_var="pat"):
    # HATE_STABILITY_AROUSAL_COUPLING_PREREG.md Sec2: 1 + arousal_level,
    # read BEFORE this incident's own arousal update (Python applies that
    # update AFTER run_rules(), the same read-before/update-after
    # convention every prior coupling in this arc uses). At level==0 this
    # is exactly 1 -- a strict generalization of the pre-coupling +1,
    # never a redefinition of the cold-start case.
    return PlusT([Lit(1.0), _arousal_level_term(pat_var)])


def _retained_fraction_term(pat_var="pat"):
    # HATE_RESET_RESENTMENT_COUPLING_PREREG.md Sec2: level/(1+level) --
    # at level==0 this is exactly 0 (a full reset, byte-identical to the
    # pre-coupling Lit(0) branch); elevated arousal retains a strictly
    # positive fraction of the pre-exception streak -- the resentment
    # residue. Same X/(1+X) shape family as the threshold-lowering term,
    # same arousal_level read.
    level = _arousal_level_term(pat_var)
    return DivT(level, PlusT([Lit(1.0), level]))


def _residue_term(pat_var="pat"):
    return TimesT([Attr(Var(pat_var), "confirm_streak"), _retained_fraction_term(pat_var)])


def _new_streak_term(pat_var="pat", ir_var="ir"):
    is_global = Eq(_attribution_locus_term(pat_var, ir_var), Lit("global_other"))
    return IfThenElse(
        is_global,
        PlusT([Attr(Var(pat_var), "confirm_streak"), _streak_increment_term(pat_var)]),
        _residue_term(pat_var),
    )


def _new_resentment_debt_term(pat_var="pat", ir_var="ir"):
    # HATE_RESENTMENT_PASSION_COUPLING_PREREG.md Sec2: every specific_act
    # residue ALSO adds to a monotonically-accumulating resentment_debt
    # ledger (never decremented -- McCullough, Fincham & Tsang 2003:
    # unforgiveness does not fade with time the way ordinary arousal
    # does). Zero contribution on global_other (no exception occurred).
    is_global = Eq(_attribution_locus_term(pat_var, ir_var), Lit("global_other"))
    increment = IfThenElse(is_global, Lit(0.0), _residue_term(pat_var))
    return PlusT([Attr(Var(pat_var), "resentment_debt"), increment])


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
            "confirm_streak increments by 1+arousal_level on global_other "
            "(HATE_STABILITY_AROUSAL_COUPLING_PREREG.md Sec2 -- an aroused "
            "confirming incident counts for MORE than one confirmation "
            "unit, read via tracks_arousal BEFORE this incident's own "
            "update; 0 arousal is exactly the pre-coupling +1), otherwise "
            "MULTIPLIES by arousal_level/(1+arousal_level) (HATE_RESET_"
            "RESENTMENT_COUPLING_PREREG.md Sec2 -- the resentment residue: "
            "at 0 arousal this is an exact full reset to 0, unchanged; "
            "elevated arousal retains a fraction of the pre-exception "
            "streak instead of fully clearing it, per Bodenhausen 1993's "
            "finding that aroused judgment discounts disconfirming "
            "evidence) -- that SAME residue also ACCUMULATES into "
            "resentment_debt, a never-decremented ledger (HATE_"
            "RESENTMENT_PASSION_COUPLING_PREREG.md Sec2 -- McCullough, "
            "Fincham & Tsang 2003: unforgiveness does not fade with time "
            "the way arousal does). Guarded by status pending->appraised "
            "so re-running run_rules() does not "
            "double-derive."
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
            # resentment_debt's own residue read MUST come before
            # confirm_streak's effect below overwrites confirm_streak --
            # effects apply progressively within one rule firing (the
            # same order-dependent-read affordance the identity_field
            # Plus-1 precedent elsewhere in this codebase already relies
            # on), so this order is load-bearing, not cosmetic.
            term_effect("pat", "resentment_debt", _new_resentment_debt_term("pat", "ir")),
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
def _effective_threshold_term(pat_var="pat"):
    # HATE_THRESHOLD_LOWER_BOUND_COUPLING_PREREG.md Sec2:
    # HATE_STABILITY_THRESHOLD / (1+arousal_level) -- at level==0 this is
    # exactly the base constant; elevated arousal LOWERS the bar. No new
    # floor constant: shared_arousal's own bounded fixed-point dynamics
    # (level converges to intensity/(1-decay), never unbounded) already
    # keep this from collapsing to 0.
    return DivT(Lit(float(HATE_STABILITY_THRESHOLD)),
                PlusT([Lit(1.0), _arousal_level_term(pat_var)]))


def _controllability_term(pat_var="pat"):
    return Attr(PickUniqueT(Neighbours(Var(pat_var), "tracks_controllability")), "external_field")


def _consequence_route_term(pat_var="pat"):
    # HATE_PITY_TOM_UNDERSTANDING_PREREG.md Sec2: Weiner 1980/1985 --
    # controllable (or unknown, Ross 1977's Fundamental Attribution Error
    # default) -> removal; understood-uncontrollable -> pity. The SAME
    # moment crystallization fires, no new timing point.
    return IfThenElse(Gte(_controllability_term(pat_var), Lit(0.0)), Lit("removal"), Lit("pity"))


def rule_crystallize_hate():
    pat = Var("pat")
    where = AndT([
        Gte(Attr(pat, "confirm_streak"), _effective_threshold_term("pat")),
        Eq(Attr(pat, "crystallized"), Lit(0.0)),
    ])
    return {
        "name": "crystallize_hate",
        "comment": (
            "HATE_ATTRIBUTION_PREREG.md Sec2/prediction 5: crystallization "
            "requires the STABILITY THRESHOLD, not the first global_other "
            "confirmation -- Sternberg 2003's decision/commitment "
            "component requires a pattern held over TIME, not a single "
            "outburst. HATE_THRESHOLD_LOWER_BOUND_COUPLING_PREREG.md Sec2: "
            "the gate now compares confirm_streak against an EFFECTIVE "
            "threshold, HATE_STABILITY_THRESHOLD/(1+arousal_level) (== the "
            "base constant %d at zero arousal, LOWER when aroused -- "
            "Slovic et al. 2007's affect heuristic: strong affect needs "
            "less accumulated evidence before a judgment is treated as "
            "settled), read via the SAME tracks_arousal edge derive_hate_"
            "attribution already reads. HATE_PITY_TOM_UNDERSTANDING_"
            "PREREG.md Sec2: the minted Hate node ALSO carries "
            "consequence_route ('removal'/'pity'), Weiner's third "
            "attribution dimension (controllability) read via the "
            "resident's own ToM belief about the target "
            "(tracks_controllability) -- >=0 (controllable, or no "
            "understanding at all, Ross 1977's default) routes removal; "
            "understood-uncontrollable routes pity. Fires exactly once "
            "per TargetPattern (crystallized==0.0 guard)." % HATE_STABILITY_THRESHOLD
        ),
        "match_type": "TargetPattern",
        "match": [["mt", "has_target_pattern", "pat"]],
        "where": where,
        "effects": [
            term_effect("pat", "crystallized", Lit(1.0)),
            add_node_effect("hate", "Hate", {
                "target": {"__term__": Attr(pat, "target")},
                "consequence_route": {"__term__": _consequence_route_term("pat")},
            }),
            add_edge_effect("pat", "has_hate", "hate"),
        ],
    }


SEED = {
    "id": "hate_attribution",
    "version": "1.6.0",
    "depends_on": ["shared_arousal"],
    "self_load_only": True,
    "description": (
        "Generalizes ATTRIBUTION_LOCUS_AS_RESIDUAL_PREREG.md's self-"
        "directed residual outward -- a held pattern about ANOTHER agent "
        "(their regard_for Concept's own live state) instead of oneself. "
        "Adds a stability gate (Sternberg 2003's decision/commitment "
        "component: confirm_streak >= an effective threshold, base %d "
        "confirmation UNITS at zero arousal) before a Hate marker "
        "crystallizes, and gates a motivational removal_desire_for "
        "consequence (Fischer, Halperin, Canetti & Jasini 2018's "
        "elimination goal) behind that gate, not behind any single angry "
        "appraisal. v1.1.0 (HATE_PASSION_COUPLING_PREREG.md) tracks the "
        "SAME shared TargetArousal pool shared_arousal.json already built "
        "(Sternberg's passion component) and couples the crystallizing "
        "incident's removal_desire_for alpha to it. v1.2.0 (HATE_"
        "STABILITY_AROUSAL_COUPLING_PREREG.md) additionally scales each "
        "confirming incident's own contribution to confirm_streak by "
        "1+arousal_level (Slovic, Finucane, Peters & MacGregor 2007's "
        "affect heuristic: a more arousing confirming incident reads as "
        "MORE representative of a stable pattern). v1.3.0 (HATE_THRESHOLD_"
        "LOWER_BOUND_COUPLING_PREREG.md) additionally lowers the "
        "EFFECTIVE threshold itself under arousal (base_threshold/"
        "(1+arousal_level), the SAME affect-heuristic citation's second "
        "claim: strong affect needs less accumulated evidence before a "
        "judgment is treated as settled) -- two independent, additive "
        "channels by which passion accelerates crystallization, neither "
        "replacing the other. v1.4.0 (HATE_RESET_RESENTMENT_COUPLING_"
        "PREREG.md) couples the specific_act RESET too -- instead of an "
        "unconditional wipe to 0, confirm_streak is multiplied by "
        "arousal_level/(1+arousal_level) (0 at zero arousal, an exact "
        "full reset; a positive fraction retained when aroused, per "
        "Bodenhausen 1993 -- aroused judgment discounts disconfirming "
        "evidence). This retained residue IS this arc's operationalization "
        "of resentment: a grievance that persists past a genuine "
        "disconfirming act because the act was processed under the same "
        "arousal the grievance itself produced. v1.5.0 (HATE_RESENTMENT_"
        "PASSION_COUPLING_PREREG.md) additionally accumulates that SAME "
        "residue into resentment_debt, a never-decremented ledger "
        "(McCullough, Fincham & Tsang 2003 -- unforgiveness does not fade "
        "with time the way arousal does), and amplifies the crystallizing "
        "incident's removal_desire_for alpha by BOTH arousal AND "
        "resentment_debt multiplicatively: base_alpha*(1+arousal_level)*"
        "(1+resentment_debt) -- a target whose grievance was repeatedly "
        "discounted-not-forgotten reacts more strongly once hate finally "
        "crystallizes than an identical target with no such history. "
        "v1.6.0 (HATE_PITY_TOM_UNDERSTANDING_PREREG.md) adds Weiner's "
        "THIRD attribution dimension, controllability -- a new "
        "controllability_for:<target> Concept IS the resident's Theory-"
        "of-Mind belief about the target (mint_target_concept reused "
        "again, tracked via tracks_controllability), evidenced by "
        "record_understanding_incident. crystallize_hate now ALSO writes "
        "consequence_route ('removal'/'pity') onto the minted Hate node "
        ">=0 controllability (or none at all, Ross 1977's Fundamental "
        "Attribution Error default) routes the crystallizing incident's "
        "evidence to removal_desire_for as before; understood-"
        "uncontrollable routes it to a new pity_for:<target> Concept "
        "instead -- mutually exclusive, unamplified by arousal or "
        "resentment_debt (pity is not a passion channel). See "
        "HATE_ATTRIBUTION_PREREG.md / _RESULTS.md, HATE_PASSION_COUPLING_"
        "PREREG.md / _RESULTS.md, HATE_STABILITY_AROUSAL_COUPLING_PREREG."
        "md / _RESULTS.md, HATE_THRESHOLD_LOWER_BOUND_COUPLING_PREREG.md "
        "/ _RESULTS.md, HATE_RESET_RESENTMENT_COUPLING_PREREG.md / "
        "_RESULTS.md, HATE_RESENTMENT_PASSION_COUPLING_PREREG.md / "
        "_RESULTS.md, HATE_PITY_TOM_UNDERSTANDING_PREREG.md / _RESULTS.md."
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
            "edge_type": "tracks_pity",
            "tgt": {"type": "Concept", "var": "c"},
            "where": None,
            "weight": Lit(1.0),
            "provenance": "hate_attribution",
        },
        {
            "src": {"type": "TargetPattern", "var": "pat"},
            "edge_type": "tracks_controllability",
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
