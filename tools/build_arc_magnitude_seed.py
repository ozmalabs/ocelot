#!/usr/bin/env python3
"""EMIT `seeds/arc_magnitude.json` — CONSTRAINTS, ORDER-N VALUE, THE LADDER.

`tools/*` are one-off AUTHORING scripts that EMIT seed manifests (CLAUDE.md:
"deletable; not agent runtime").  Nothing here runs at agent time and nothing
here decides anything about a live graph: it assembles JSON.

WHY A BUILDER AND NOT A HAND-WRITTEN SEED — and the reason is sharper here than
it was for `arc_goals`.  MG2's bar is *"order-N differs from order-1 ON THE
SHIPPED GRAPH"*.  A comparison like that is worthless if the two value terms
were written independently, because then the difference could be anywhere.  So
`VALUE_N` is **LIFTED PROGRAMMATICALLY out of `seeds/arc_goals.json`** —
`ag_select_margin`'s own `arc_sel_runner_up_value` effect, which is exactly
`VALUE(V("h"))` — and modified by exactly two mechanical edits:

  (1) the single `Attr(_, "headroom_n")` becomes `Attr(_, "orderN_headroom_n")`
  (2) a scope charge is SUBTRACTED on the outside

`test_mg2_VALUE_N_is_ag_selects_OWN_value_term_with_ONE_substitution`
re-derives the lift and diffs, so order-1 and order-N are provably the same
term read two ways — the A7 control requirement (*a control must be shown
capable of detecting the difference it is used to rule out*) satisfied by
construction rather than by assertion.

THE SEED CONTAINS NO ATTRITION NUMBER.  `ArcAttritionKey` nodes carry a name,
an artifact and two dotted paths and NOTHING ELSE; `domains/
arc_magnitude_ingest.resolve_attrition_keys` opens the file and writes
`numerator_n`/`denominator_n`; `mg_attrition_factor` computes the ratio in a
Term.  NO ATTRITION NUMBER IS STORED AS A VALUE anywhere in the emitted seed —
`test_mg2_THE_SEED_CONTAINS_NO_ATTRITION_NUMBER` walks every `ArcAttritionKey`
attr and asserts its numeric list is EMPTY.  (The figures do appear inside
explanatory `_why` prose, which is the citation, not the input.)

Run:  python tools/build_arc_magnitude_seed.py         (writes the seed)
      python tools/build_arc_magnitude_seed.py --check (fails if out of date)
"""
from __future__ import annotations

import copy
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEEDS = os.path.join(ROOT, "seeds")
ARC_GOALS_SEED = os.path.join(SEEDS, "arc_goals.json")
OUT = os.path.join(SEEDS, "arc_magnitude.json")


# --------------------------------------------------------------------------- #
#  Term constructors — mechanical JSON assembly (arc_goals' own set).
# --------------------------------------------------------------------------- #
def V(name):
    return {"type": "Var", "name": name}


def L(value):
    return {"type": "Lit", "value": value}


def A(node, key):
    return {"type": "Attr", "node": node, "key": key}


def NOT(x):
    return {"type": "Not", "arg": x}


def AND(*items):
    return {"type": "And", "items": list(items)}


def OR(*items):
    return {"type": "Or", "items": list(items)}


def EQ(a, b):
    return {"type": "Eq", "a": a, "b": b}


def GT(a, b):
    return {"type": "Gt", "a": a, "b": b}


def LT(a, b):
    return {"type": "Lt", "a": a, "b": b}


def NEIGH(node, edge_type):
    return {"type": "Neighbours", "node": node, "edge_type": edge_type,
            "any_type": False}


def NOT_(node_type):
    return {"type": "NodesOfType", "node_type": node_type}


def FILT(source, var_name, predicate):
    return {"type": "Filter", "source": source, "var_name": var_name,
            "predicate": predicate}


def EXISTS(source, var_name, predicate):
    return {"type": "Exists", "source": source, "var_name": var_name,
            "predicate": predicate}


def COUNT(source):
    return {"type": "Count", "source": source}


def SUM(source, var_name, value):
    return {"type": "Sum", "source": source, "var_name": var_name,
            "value": value}


def ARGMIN(source, var_name, value, default=None):
    return {"type": "Argmin", "source": source, "var_name": var_name,
            "value": value, "default": default}


def ARGMAX(source, var_name, value, default=None):
    return {"type": "Argmax", "source": source, "var_name": var_name,
            "value": value, "default": default}


def MAXOVER(source, var_name, value, default=None):
    return {"type": "MaxOver", "source": source, "var_name": var_name,
            "value": value, "default": default}


def MINOVER(source, var_name, value, default=None):
    return {"type": "MinOver", "source": source, "var_name": var_name,
            "value": value, "default": default}


def TIMES(*items):
    return {"type": "Times", "items": list(items)}


def PLUS(*items):
    return {"type": "Plus", "items": list(items)}


def MINUS(a, b):
    return {"type": "Minus", "a": a, "b": b}


def DIV(a, b):
    return {"type": "Div", "a": a, "b": b}


def POW(a, b):
    return {"type": "Pow", "a": a, "b": b}


def ITE(cond, then, other):
    return {"type": "IfThenElse", "cond": cond, "then": then, "other": other}


def SCAT(*parts):
    return {"type": "StringConcat", "parts": list(parts)}


def STR(term):
    """Number -> string.  MEASURED HAZARD, inherited and re-verified here:
    `StringConcat` SILENTLY DROPS numeric parts, so every measured number in a
    question's text goes through `ToJsonString` first."""
    return {"type": "ToJsonString", "value": term}


def T(term):
    return {"__term__": term}


def ONE_OF(source, var_name):
    return ARGMIN(source, var_name, L(0), None)


def NUM(term, default=0.0):
    """COALESCE.  THE SINGLE MOST EXPENSIVE HAZARD IN THIS TREE.

    MEASURED on this engine, and each of these silently produces a WRONG
    ANSWER rather than an error:

        Lt(null, 0.0)      -> True    a missing attr sorts BELOW any number
        Gt(8.0, null)      -> True    ... and any number sorts ABOVE it
        Times(2.0, null)   -> 2.0     null is the MULTIPLICATIVE IDENTITY
        Div(5.0, null)     -> 0.0

    `Times(x, null) == x` is the one that would have quietly broken MG2: an
    unresolved attrition factor would have made the projection contribute its
    UNDISCOUNTED increment — i.e. an unmeasured projection would have been
    valued HIGHER than a measured one, which is precisely the failure A9
    registers as *"an authored projection is unbounded in the dangerous
    direction."*  Every arithmetic read of a possibly-absent attr in this file
    goes through NUM.
    """
    return ITE(EQ(term, L(None)), L(default), term)


# --------------------------------------------------------------------------- #
#  THE LIFT — `ag_select`'s own POOL and VALUE, out of the shipped seed.
# --------------------------------------------------------------------------- #
def _arc_goals_rule(name):
    with open(ARC_GOALS_SEED) as fh:
        d = json.load(fh)
    for r in d["rules"]:
        if r["name"] == name:
            return r
    raise SystemExit("no such rule in seeds/arc_goals.json: " + name)


def _rename_var(tree, old, new):
    tree = copy.deepcopy(tree)

    def walk(o):
        if isinstance(o, dict):
            if o.get("type") == "Var" and o.get("name") == old:
                o["name"] = new
            if o.get("var_name") == old:
                o["var_name"] = new
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(tree)
    return tree


def _subst_cand(tree, node_term):
    tree = copy.deepcopy(tree)

    def walk(o):
        if isinstance(o, dict):
            for k, v in list(o.items()):
                if isinstance(v, dict) and v.get("type") == "Var" \
                        and v.get("name") == "__CAND__":
                    o[k] = copy.deepcopy(node_term)
                else:
                    walk(v)
        elif isinstance(o, list):
            for i, v in enumerate(o):
                if isinstance(v, dict) and v.get("type") == "Var" \
                        and v.get("name") == "__CAND__":
                    o[i] = copy.deepcopy(node_term)
                else:
                    walk(v)

    walk(tree)
    return tree


def _lift_value():
    """`ag_select_margin`'s `arc_sel_runner_up_value` effect IS `VALUE(V("h"))`
    — a standalone value term over one candidate, which is exactly what is
    wanted.  (`ag_select`'s own copy is wrapped in a MaxOver over the pool.)"""
    r = _arc_goals_rule("ag_select_margin")
    for e in r["effects"]:
        if e[0] == "set_attr" and e[2] == "arc_sel_runner_up_value":
            return _rename_var(e[3]["__term__"], "h", "__CAND__")
    raise SystemExit("ag_select_margin no longer writes arc_sel_runner_up_value")


def _lift_pool():
    """`ag_select`'s `arc_sel_value` effect is `MaxOver(POOL, g2, VALUE)`; its
    `source` IS the pool Filter, lifted so `mg_select` ranks THE SAME POOL."""
    r = _arc_goals_rule("ag_select")
    for e in r["effects"]:
        if e[0] == "set_attr" and e[2] == "arc_sel_value":
            t = e[3]["__term__"]
            assert t["type"] == "MaxOver", t["type"]
            return copy.deepcopy(t["source"])
    raise SystemExit("ag_select no longer writes arc_sel_value")


_VALUE_1_T = _lift_value()
_POOL_T = _lift_pool()


def _swap_headroom(tree):
    """EDIT (1) of exactly two: the single `Attr(_, "headroom_n")` becomes
    `Attr(_, "orderN_headroom_n")`.  Asserted to hit EXACTLY ONCE — an edit
    that silently hits zero sites is this tree's signature failure (an unknown
    field name is a SILENT NO-OP, not an error)."""
    tree = copy.deepcopy(tree)
    hits = [0]

    def walk(o):
        if isinstance(o, dict):
            if o.get("type") == "Attr" and o.get("key") == "headroom_n":
                o["key"] = "orderN_headroom_n"
                hits[0] += 1
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(tree)
    if hits[0] != 1:
        raise SystemExit("expected exactly ONE headroom_n site, found %d"
                         % hits[0])
    return tree


def VALUE_1(node_term):
    """`ag_select`'s order-1 value, verbatim, at any node."""
    return _subst_cand(_VALUE_1_T, node_term)


def VALUE_N(node_term):
    """The SAME term with `headroom_n` -> `orderN_headroom_n`, minus the scope
    charge.  EDIT (2) of exactly two.

    The scope charge is a WEIGHT, not a veto: an out-of-scope goal is CHARGED
    and stays in the pool, exactly as a refuted goal is.  A9's framing
    correction is the reason — *"do not add a guard where a term is missing"*;
    scope was a missing input, so it lands as a term in the collapse.
    """
    return MINUS(
        _subst_cand(_swap_headroom(_VALUE_1_T), node_term),
        TIMES(MPOL("w_out_of_scope"),
              NUM(A(node_term, "out_of_scope"), 0.0)))


def POOL_AS(var):
    return _rename_var(_POOL_T, "g2", var)


# --------------------------------------------------------------------------- #
#  Policy / constraint reads — graph data, never literals in a rule.
# --------------------------------------------------------------------------- #
def MPOL(key):
    return A(ARGMIN(NOT_("ArcMagPolicy"), "mp", A(V("mp"), "priority"), None),
             key)


def MEASURE_EPOCH():
    """The measurement epoch as the STRING it is stored as — the SAME
    `ResidualFact{name:'arc_measure_epoch'}` `gr_condition_lapse`'s
    `fact_equals` branch already reads, so an unconditioned constraint and an
    unmeasured projection both expire through the EXISTING machinery."""
    return A(ARGMIN(FILT(NOT_("ResidualFact"), "mef",
                         EQ(A(V("mef"), "name"), L("arc_measure_epoch"))),
                    "mef2", L(0), None), "value")


def _live_constraints(kind, var="lc"):
    """Constraints of one kind whose condition CURRENTLY HOLDS.

    `stale` is written by `gr_condition_lapse` / `gr_condition_hold` — the
    EXISTING lapse machinery, matching on the `holds_under` EDGE with no type
    restriction on its left var, which is why an `ArcConstraint` lapses through
    it with ZERO NEW MECHANISM.  Verified live, both directions, before this
    seed was written."""
    return FILT(NOT_("ArcConstraint"), var,
                AND(EQ(A(V(var), "ckind"), L(kind)),
                    NOT(EQ(A(V(var), "stale"), L(1.0)))))


def HORIZON_GROSS():
    """The held horizon, or null when the graph has never been told one.

    NULL IS LOAD-BEARING AND MUST NOT BE COALESCED HERE: *"no horizon has been
    stated"* and *"the horizon is zero"* are different facts.  The first is the
    ignorance MG1's ask exists to resolve; the second would mean nothing fits.
    Coalescing them is how a graph that has never been asked would silently
    read as one on an impossible deadline."""
    return A(ARGMIN(_live_constraints("horizon"), "hc2",
                    A(V("hc2"), "priority"), None), "horizon_units")


def COMPETING_UNITS():
    """Competing requirements CONSUME the horizon rather than charging goals.

    A9 lists *competing requirements* alongside scope and horizon.  Modelling
    them as a second charge would have been a second knob; modelling them as
    claims on the SAME measured budget makes them reprice every goal through
    the channel that already exists, and keeps the ladder's ratio honest — a
    goal is not smaller because someone else is busy, the budget is."""
    return SUM(_live_constraints("competing", "cc"), "cc",
               NUM(A(V("cc"), "competing_units"), 0.0))


def HORIZON_NET():
    """gross - competing, propagating NULL when no horizon is held."""
    return ITE(EQ(HORIZON_GROSS(), L(None)), L(None),
               MINUS(NUM(HORIZON_GROSS(), 0.0), COMPETING_UNITS()))


def NO_HORIZON():
    return EQ(HORIZON_GROSS(), L(None))


# --------------------------------------------------------------------------- #
#  THE ATTRITION FACTORS — read, never authored.
# --------------------------------------------------------------------------- #
def FACTOR(name):
    """A RESOLVED attrition key's factor, or null.

    `resolved` is written by the adapter from whether the artifact path walked;
    an unresolved key has NO `factor` at all, so this returns null and every
    caller coalesces it to 0.0 — an unmeasured projection is worth NOTHING, not
    its undiscounted increment.
    """
    return A(ARGMIN(FILT(NOT_("ArcAttritionKey"), "ak",
                         AND(EQ(A(V("ak"), "name"), L(name)),
                             EQ(A(V("ak"), "resolved"), L(1.0)))),
                    "ak2", L(0), None), "factor")


def ATTRITION_MEASURED():
    """Both factors resolved.  This is the condition MG2 turns on."""
    return AND(NOT(EQ(FACTOR("inventory_to_strict_reach"), L(None))),
               NOT(EQ(FACTOR("reach_to_conversion"), L(None))))


# --------------------------------------------------------------------------- #
#  NODES
# --------------------------------------------------------------------------- #
def _nodes():
    n = []
    n.append({"local_id": 3000, "type": "ArcMagPolicy", "attrs": {
        "name": "default_arc_magnitude_policy",
        "priority": 1,
        "w_out_of_scope": 25.0,
        "_w_out_of_scope_is_AUTHORED": (
            "AUTHORED policy on a node, tunable as graph data without touching "
            "a rule -- the RESIDUAL_SCALE=100 / w_unsignatured precedent. It is "
            "a WEIGHT, not a veto: an out-of-scope goal stays in the pool and "
            "can still win on merit, which is the whole point of A9's framing "
            "correction. Gated two-position (it can flip the outcome in both "
            "directions); no principled value."),
        "_THE_RUNG_THRESHOLDS_ARE_NOT_HERE": (
            "DELIBERATELY. MG3 registers that thresholds are RATIOS against the "
            "MEASURED horizon and never authored constants, because an authored "
            "cutoff is gameable exactly the way cost_bits is. The only number in "
            "mg_rung is 1.0, and 1.0 is not a tuning knob -- it is what 'fits' "
            "MEANS once cost and horizon are in the same measured unit "
            "(operator units, from arc6_structural_ceiling.json::bundles.n_units). "
            "There is no small_ratio and no huge_ratio to tune."),
    }})

    for lid, name, desc in (
        (3010, "horizon",
         "the budget, in the SAME MEASURED UNIT the tier ladder's cost is "
         "denominated in (operator units). A goal is not 'too expensive' in "
         "the abstract -- it is correct at twelve months and wrong at two "
         "weeks, and without this term every goal is priced in a vacuum."),
        (3011, "scope",
         "which seams are in scope. An out-of-scope goal is CHARGED "
         "w_out_of_scope and stays in the pool -- a weight, not a filter."),
        (3012, "competing",
         "a competing requirement CONSUMES the horizon (HORIZON_NET = gross - "
         "sum of competing), so it reprices every goal through the channel "
         "that already exists rather than adding a second knob."),
    ):
        n.append({"local_id": lid, "type": "ArcConstraintKind",
                  "attrs": {"name": name, "description": desc}})

    # THE ATTRITION KEYS.  NAME + ARTIFACT + TWO PATHS.  NO NUMBERS.
    for lid, name, role, art, num, den, why in (
        (3020, "inventory_to_strict_reach", "size_reach",
         "results/arc6_structural_ceiling.json",
         "strict_reach.witness_and_in_budget_ids|len",
         "ceilings.honest_B0_zero_new_termnode.n",
         "DISCOUNT ONE OF THE TWO THE ARTIFACT ITSELF NAMES. "
         "arc6_structural_ceiling.json::inventory_ceiling_is_not_reach says in "
         "its own words: 'the honest expected CONVERSION for a bundle is its "
         "inventory count discounted twice -- once by size/reach, once by the "
         "S4 pass-rate prior'. This is the first: of the 10 ids B0's inventory "
         "covers, only those with a WITNESS INSIDE THE ENUMERATOR'S OWN BUDGET "
         "are reachable at all."),
        (3021, "reach_to_conversion", "per_order",
         "results/arc6_structural_ceiling.json",
         "s4_reach_vs_conversion_prior.s4_fully_correct_pass",
         "s4_reach_vs_conversion_prior.s4_moved_off_enumerate_failed",
         "DISCOUNT TWO. arc-4 S4 moved 25 tasks off `gapped:enumerate_failed` "
         "and only 8 were fully correct -- the same corpus, the same "
         "enumerator, the same protocol. THIS IS THE PER-ORDER FACTOR: reaching "
         "order k+1 requires order k to have CONVERTED first, so it compounds "
         "once per order. It is also the number the prereg's own HS1 bar was "
         "derived from (10 x 0.32 = ~3.2 expected), which returned 0 -- see the "
         "calibration record."),
        (3022, "seam_a_honest_vs_cherry_picked",
         "granularity_calibration_NOT_USED_AS_AN_ORDER",
         "results/arc6_a_ceiling.json",
         "ceilings.honest_all_families.n",
         "ceilings.cherry_picked_concept.n",
         "READ AND REPORTED, DELIBERATELY NOT USED AS AN ORDER FACTOR. Seam A's "
         "5/8/14/27/60 is a GRANULARITY ladder, not an UNLOCK ladder: it "
         "inflates by renaming the same move at finer grain, and the prereg's "
         "own standing rule says 'in an import seam audit the NAMING; in a "
         "structural seam audit the PRICE'. Feeding a naming ladder into an "
         "order sum would be counting the same tasks four times. Recorded here "
         "so that declining to use it is visible rather than silent."),
    ):
        n.append({"local_id": lid, "type": "ArcAttritionKey", "attrs": {
            "name": name, "order_role": role, "evidence_artifact": art,
            "numerator_path": num, "denominator_path": den, "_why": why,
            "_NO_NUMBER_IS_STORED_HERE": (
                "numerator_n / denominator_n / resolved are written by "
                "domains/arc_magnitude_ingest.resolve_attrition_keys from the "
                "artifact at the paths above, and `factor` is computed by "
                "mg_attrition_factor as Div(numerator_n, denominator_n). If the "
                "path does not walk, `resolved` is 0.0 and the factor is NULL -- "
                "which every consumer coalesces to 0.0, so an unmeasured "
                "projection is worth NOTHING rather than its undiscounted "
                "increment."),
        }})
    return n


def _edges():
    return [{"src": {"local": 3000}, "tgt": {"local": lid},
             "type": "has_attrition_key", "attrs": {}}
            for lid in (3020, 3021, 3022)] + \
           [{"src": {"local": 3000}, "tgt": {"local": lid},
             "type": "has_constraint_kind", "attrs": {}}
            for lid in (3010, 3011, 3012)]


def _productions():
    p = [("ArcMagPolicy", "has_attrition_key", "ArcAttritionKey"),
         ("ArcMagPolicy", "has_constraint_kind", "ArcConstraintKind"),
         ("ArcTierLadder", "has_tier", "ArcTier"),
         ("ArcGoal", "has_projection", "ArcProjection"),
         ("ArcProjection", "holds_under", "ResidualCondition"),
         ("ArcConstraint", "holds_under", "ResidualCondition"),
         ("ArcAgenda", "has_constraint", "ArcConstraint"),
         ("ArcAgenda", "asked_constraints", "ArcConstraintQuestion"),
         ("ArcConstraintQuestion", "answered_by", "Message"),
         ("Message", "responds_to", "ArcConstraintQuestion")]
    return [{"provenance": "seed:arc_magnitude:%s-%d" % (et, i),
             "src": {"type": s, "var": "s"}, "edge_type": et,
             "tgt": {"type": t, "var": "t"}}
            for i, (s, et, t) in enumerate(p)]


# --------------------------------------------------------------------------- #
#  RULES — MG2: the attrition factor and the tier survivals.
# --------------------------------------------------------------------------- #
MHUB = [["mpol", "has_attrition_key", "ak"]]


def _r_attrition_factor():
    return {
        "name": "mg_attrition_factor",
        "comment": (
            "MG2. THE FACTOR IS COMPUTED, NOT STORED. The adapter writes only "
            "numerator_n and denominator_n -- the literal contents of a named "
            "artifact at a named dotted path -- and this rule divides them. "
            "There is no attrition number anywhere in seeds/arc_magnitude.json, "
            "which is the strongest available form of A9's 'READ not authored': "
            "not a number with a citation next to it, but no number at all. "
            "Guarded on `resolved`, so an artifact whose path did not walk "
            "leaves `factor` ABSENT rather than 0.0 -- and absent is what the "
            "expiry lane keys on, because 'we could not measure it' and 'we "
            "measured zero' must not collapse into the same fact."),
        "batch": True,
        "match": MHUB,
        "where": AND(
            EQ(A(V("ak"), "resolved"), L(1.0)),
            NOT(EQ(A(V("ak"), "numerator_n"), L(None))),
            NOT(EQ(A(V("ak"), "denominator_n"), L(None))),
            GT(NUM(A(V("ak"), "denominator_n"), 0.0), L(0.0)),
            EQ(A(V("ak"), "factor"), L(None)),
        ),
        "effects": [
            ["set_attr", "ak", "factor",
             T(DIV(A(V("ak"), "numerator_n"), A(V("ak"), "denominator_n")))],
        ],
    }


def _survival(order_term):
    """survival(k) = 1                       for k = 1
                   = f_size * f_pass^(k-1)   for k >= 2

    ORDER 1 IS NOT DISCOUNTED, AND THAT IS THE DESIGN. Order 1 is MEASURED
    HEADROOM -- the same kind of number every other goal's `headroom_n` already
    is -- so discounting it here and not there would make the two readings
    incomparable and would silently rescale every goal rather than reprice the
    one with a ladder. ORDERS >= 2 ARE PROJECTIONS: they are only reachable if
    the order below them CONVERTED, so each compounds one more `reach_to_
    conversion` on top of the one-off `inventory_to_strict_reach` size discount
    the artifact names. Every factor is a Div of two artifact-read numbers.
    """
    return ITE(EQ(order_term, L(1.0)), L(1.0),
               TIMES(NUM(FACTOR("inventory_to_strict_reach"), 0.0),
                     POW(NUM(FACTOR("reach_to_conversion"), 0.0),
                         MINUS(order_term, L(1.0)))))


def _r_tier_survival():
    return {
        "name": "mg_tier_survival",
        "comment": (
            "MG2. Stamps each measured tier with its survival factor so the "
            "order sum can read it, and so the discount is AUDITABLE PER TIER "
            "rather than buried inside one expression. Re-armed whenever the "
            "factors change (guarded on the stamped survival differing from the "
            "computed one would churn; guarded on ABSENCE plus a resolved "
            "factor is the terminating form)."),
        "batch": True,
        "match": [["lad", "has_tier", "t"]],
        "where": AND(
            EQ(A(V("t"), "survival"), L(None)),
            OR(EQ(A(V("t"), "order"), L(1.0)), ATTRITION_MEASURED()),
        ),
        "effects": [
            ["set_attr", "t", "survival", T(_survival(A(V("t"), "order")))],
            ["set_attr", "t", "expected_conversion_n",
             T(TIMES(NUM(A(V("t"), "increment_n"), 0.0),
                     _survival(A(V("t"), "order"))))],
        ],
    }


def _r_tier_in_horizon():
    return {
        "name": "mg_tier_in_horizon",
        "comment": (
            "MG1/MG3. THE HORIZON TRUNCATES THE ORDER SUM. A tier whose "
            "CUMULATIVE cost exceeds the net horizon is not buyable, so it "
            "contributes nothing -- which is how ONE horizon answer reprices "
            "the whole pool instead of returning the single bit an approve/deny "
            "gate would. Cumulative, not marginal, because the ladder's tiers "
            "are NESTED (B1 CONTAINS B0's eight units); charging the marginal "
            "cost would price a tier as if the ones below it were free. "
            "MEASURED HAZARD, and it is why NO_HORIZON is checked FIRST: "
            "Gt(8.0, null) is TRUE on this engine, so a graph that had never "
            "been told a horizon would have read as one on an impossible "
            "deadline and truncated every tier to nothing."),
        "batch": True,
        "match": [["lad", "has_tier", "t"]],
        "where": AND(
            NOT(EQ(A(V("t"), "cum_cost_units"), L(None))),
        ),
        "effects": [
            ["set_attr", "t", "in_horizon",
             T(ITE(NO_HORIZON(), L(1.0),
                   ITE(GT(NUM(A(V("t"), "cum_cost_units"), 0.0),
                          NUM(HORIZON_NET(), 0.0)), L(0.0), L(1.0))))],
            ["set_attr", "t", "horizon_net_at_stamp",
             T(ITE(NO_HORIZON(), L(-1.0), NUM(HORIZON_NET(), 0.0)))],
        ],
    }


# --------------------------------------------------------------------------- #
#  RULES — MG2: the projection, and its expiry.
# --------------------------------------------------------------------------- #
def _tiers_of(gvar="g", var="t2"):
    return FILT(NOT_("ArcTier"), var,
                EQ(A(V(var), "ladder_key"), A(V(gvar), "proposed_seam")))


def _has_ladder(gvar="g"):
    return AND(NOT(EQ(A(V(gvar), "proposed_seam"), L(None))),
               EXISTS(_tiers_of(gvar, "t3"), "t3", L(True)))


def _r_projection_measured():
    return {
        "name": "mg_projection_mint_measured",
        "comment": (
            "MG2. A PROJECTION IS A CLAIM AND THEREFORE CARRIES A CONDITION. "
            "A goal with a measured tier ladder gets ONE ArcProjection whose "
            "holds_under condition is fact_equals(arc6_structural_ceiling_"
            "present == '1') -- so it lapses through gr_condition_lapse THE "
            "MOMENT ITS EVIDENCE ARTIFACT CHANGES, and not before. Same node "
            "type, same edge, same rule as the six measured ceilings: ZERO NEW "
            "LAPSE MACHINERY, which is MG1's registered constraint applied to "
            "MG2's projection. The mirror (mg_projection_mint_unmeasured) is "
            "this rule's guard with ATTRITION_MEASURED negated, so exactly one "
            "of the pair fires."),
        "batch": True,
        "match": [["agenda", "has_arc_goal", "g"]],
        "where": AND(
            _has_ladder(),
            EQ(COUNT(NEIGH(V("g"), "has_projection")), L(0)),
            ATTRITION_MEASURED(),
        ),
        "effects": [
            ["add_node", "pr", "ArcProjection", {
                "agid": T(A(V("g"), "agid")),
                "basis": "measured_attrition",
                "stale": 0.0,
                "evidence_artifact": "results/arc6_structural_ceiling.json",
                "_why": ("both attrition factors resolved from artifact paths, "
                         "so this projection has a measured basis and survives "
                         "until that artifact changes."),
            }],
            ["add_node", "pcond", "ResidualCondition", {
                "rid": T(SCAT(L("arc.projection."), A(V("g"), "agid"))),
                "ckind": "fact_equals",
                "filter_value": "arc6_structural_ceiling_present",
                "expected_str": "1",
                "why": ("the attrition factors are quoted from this artifact; "
                        "if it changes the projection must be re-read, not "
                        "re-used."),
            }],
            ["add_edge", "pr", "holds_under", "pcond"],
            ["add_edge", "g", "has_projection", "pr"],
        ],
    }


def _r_projection_unmeasured():
    return {
        "name": "mg_projection_mint_unmeasured",
        "comment": (
            "MG2's REGISTERED BAR, MADE MECHANICAL: *a projection with no "
            "measured basis must default-expire at the next epoch, exactly as "
            "an unconditioned human answer does.* Its condition is "
            "fact_equals(arc_measure_epoch == <epoch at mint>) -- the SAME "
            "default ag_reply_mints_testimony_unconditioned uses, on the same "
            "ResidualFact, consumed by the same gr_condition_lapse branch. "
            "Angluin's zero-bits result made mechanical, applied to the agent's "
            "OWN projections rather than to a human's answer: a projection that "
            "cannot name what it rests on is worth one epoch. This is the lane "
            "that keeps an authored projection from being 'unbounded in the "
            "dangerous direction' -- it does not forbid one, it makes it decay."),
        "batch": True,
        "match": [["agenda", "has_arc_goal", "g"]],
        "where": AND(
            _has_ladder(),
            EQ(COUNT(NEIGH(V("g"), "has_projection")), L(0)),
            NOT(ATTRITION_MEASURED()),
        ),
        "effects": [
            ["add_node", "pr", "ArcProjection", {
                "agid": T(A(V("g"), "agid")),
                "basis": "NO_MEASURED_BASIS",
                "stale": 0.0,
                "_why": ("an attrition path did not walk, so this projection "
                         "rests on nothing measured and expires at the next "
                         "measurement epoch."),
            }],
            ["add_node", "pcond", "ResidualCondition", {
                "rid": T(SCAT(L("arc.projection."), A(V("g"), "agid"))),
                "ckind": "fact_equals",
                "filter_value": "arc_measure_epoch",
                "expected_str": T(MEASURE_EPOCH()),
                "why": ("no measured basis, so it expires at the next "
                        "measurement epoch -- an unconditioned projection is "
                        "worth one epoch."),
            }],
            ["add_edge", "pr", "holds_under", "pcond"],
            ["add_edge", "g", "has_projection", "pr"],
        ],
    }


def _live_projection(gvar="g"):
    return EXISTS(NEIGH(V(gvar), "has_projection"), "pr2",
                  NOT(EQ(A(V("pr2"), "stale"), L(1.0))))


# --------------------------------------------------------------------------- #
#  RULES — MG2: the order-N headroom itself.
# --------------------------------------------------------------------------- #
def _order_n_sum(gvar="g"):
    """Sum over the goal's OWN measured tiers, truncated by the horizon."""
    return SUM(FILT(_tiers_of(gvar, "t4"), "t5",
                    EQ(NUM(A(V("t5"), "in_horizon"), 0.0), L(1.0))),
               "t5",
               TIMES(NUM(A(V("t5"), "increment_n"), 0.0),
                     NUM(A(V("t5"), "survival"), 0.0)))


def _r_goal_order_n():
    return {
        "name": "mg_goal_order_n",
        "comment": (
            "MG2, THE HEADLINE. A goal with a MEASURED TIER LADDER is valued at "
            "the horizon-truncated sum of its per-order increments, each "
            "discounted by its own measured survival -- not at its top tier's "
            "paper inventory. On the shipped graph this is the difference "
            "between 42 (B3's inventory, i.e. every task the ladder would ever "
            "cover, credited in full and at once) and ~13.6 (B0's 10 measured "
            "directly, plus 16/6/10 discounted by the attrition the artifacts "
            "record). The order-1 reading was ALREADY a projection -- it just "
            "had no attrition on it, which is exactly the unbounded direction "
            "A9 names. REQUIRES A NON-STALE PROJECTION: once the projection "
            "lapses, mg_goal_order_n_default takes over and the goal falls back "
            "to its order-1 headroom, which is what 'default-expire' MEANS here."),
        "batch": True,
        "match": [["agenda", "has_arc_goal", "g"]],
        "where": AND(
            _has_ladder(),
            _live_projection(),
        ),
        "effects": [
            ["set_attr", "g", "orderN_headroom_n", T(_order_n_sum())],
            ["set_attr", "g", "order_n_basis", "measured_tier_ladder"],
            ["set_attr", "g", "order_n_orders_counted",
             T(COUNT(FILT(_tiers_of("g", "t6"), "t7",
                          EQ(NUM(A(V("t7"), "in_horizon"), 0.0), L(1.0)))))],
        ],
    }


def _is_decomposition_child(gvar="g"):
    """A16/MG4. TRUE for a goal minted BY decomposition (`mg_decompose`,
    `seeds/arc_decompose.json`), which stamps `parent_agid` on every child it
    mints and on NOTHING else in this tree. ADDITIVE AND INERT ON EVERY
    EXISTING SCENE: no goal on the shipped graph carries `parent_agid`, so
    this predicate is False everywhere MG1-3/5 already measured, and the
    guard below changes NOTHING there."""
    return NOT(EQ(A(V(gvar), "parent_agid"), L(None)))


def _r_goal_order_n_default():
    return {
        "name": "mg_goal_order_n_default",
        "comment": (
            "A9, VERBATIM: *'Re-measurement's order-1 value IS its total value "
            "(completing it unlocks nothing).'* A goal with no measured ladder "
            "-- or whose projection has EXPIRED -- has no orders above 1, so "
            "its order-N headroom IS its order-1 headroom. This is not a "
            "fallback for missing data; it is the correct answer for a goal "
            "that unlocks nothing, and it is why order-N reprices SOME goals "
            "and not others rather than rescaling all of them uniformly. Guard "
            "is mg_goal_order_n's with the ladder/projection items negated, so "
            "exactly one of the pair fires.\n"
            "A16/MG4 ADDITION, ADDITIVE AND INERT ON EVERY EXISTING SCENE: this "
            "rule is ALSO excluded for a decomposition CHILD (parent_agid set). "
            "Without the exclusion, this rule would unconditionally recompute "
            "ANY laddered-orphan goal's orderN_headroom_n FROM ITS RAW "
            "headroom_n every fixpoint pass -- a decomposition child has no "
            "proposed_seam (deliberately, MG4 6.2(1)), so _has_ladder(child) is "
            "False and this rule's ORIGINAL guard alone would match it, "
            "silently overwriting mg_child_order_n's discounted "
            "headroom_n*tier_survival back to the undiscounted headroom_n -- "
            "precisely the order-1-credit inflation trap MG4 6.2(4) names. No "
            "goal on the shipped graph carries parent_agid, so this exclusion "
            "is False (inert) on every scene MG1-3/5 already measured."),
        "batch": True,
        "match": [["agenda", "has_arc_goal", "g"]],
        "where": AND(OR(NOT(_has_ladder()), NOT(_live_projection())),
                     NOT(_is_decomposition_child())),
        "effects": [
            ["set_attr", "g", "orderN_headroom_n",
             T(NUM(A(V("g"), "headroom_n"), 0.0))],
            ["set_attr", "g", "order_n_basis",
             T(ITE(_has_ladder(), L("projection_expired_fell_back_to_order_1"),
                   L("no_ladder_order_1_IS_total_value")))],
            ["set_attr", "g", "order_n_orders_counted", 1.0],
        ],
    }


# --------------------------------------------------------------------------- #
#  RULES — MG3: the magnitude ladder.
# --------------------------------------------------------------------------- #
def _cost_total(gvar="g"):
    return ITE(_has_ladder(gvar),
               MAXOVER(_tiers_of(gvar, "tc"), "tc",
                       NUM(A(V("tc"), "cum_cost_units"), 0.0), L(0.0)),
               NUM(A(V(gvar), "cost_bits"), 0.0))


def _cost_first(gvar="g"):
    return ITE(_has_ladder(gvar),
               MINOVER(_tiers_of(gvar, "tf"), "tf",
                       NUM(A(V("tf"), "cum_cost_units"), 0.0), L(0.0)),
               NUM(A(V(gvar), "cost_bits"), 0.0))


def _r_rung():
    ratio = DIV(_cost_total(), NUM(HORIZON_NET(), 0.0))
    ratio_first = DIV(_cost_first(), NUM(HORIZON_NET(), 0.0))
    return {
        "name": "mg_rung",
        "comment": (
            "MG3. THE LADDER ROUTES BY RATIO AND THERE IS NO AUTHORED CUTOFF. "
            "r = cost_total / horizon_net, r_first = cost_of_the_smallest_"
            "measured_increment / horizon_net, both in OPERATOR UNITS -- the "
            "unit arc6_structural_ceiling.json::bundles.n_units is denominated "
            "in, which is why the two sides of the ratio are commensurable "
            "without a conversion anyone chose.\n"
            "  r <= 1                    ABSORB     the whole goal fits; execute, do not ask\n"
            "  r > 1 and r_first <= 1    BALANCE    part of it fits; compete in the collapse\n"
            "  r_first > 1               PUSH_BACK  not even the smallest measured\n"
            "                                       increment fits -> ask for scope AND decompose\n"
            "THE ONLY NUMBER HERE IS 1.0, AND 1.0 IS NOT A KNOB -- it is what "
            "'fits' means once both sides are in the same measured unit. There "
            "is no small_ratio and no huge_ratio to tune, which is the "
            "difference between this and cost_bits. NO_HORIZON is a FOURTH "
            "outcome and is checked first, both because Gt(x, null) is TRUE on "
            "this engine and because 'we have not been told' is a real state "
            "that must not masquerade as 'it fits' -- it is precisely the state "
            "mg_ask_constraints exists to leave."),
        "batch": True,
        "match": [["agenda", "has_arc_goal", "g"]],
        "where": L(True),
        "effects": [
            ["set_attr", "g", "magnitude_ratio",
             T(ITE(NO_HORIZON(), L(-1.0), ratio))],
            ["set_attr", "g", "magnitude_ratio_first_tier",
             T(ITE(NO_HORIZON(), L(-1.0), ratio_first))],
            ["set_attr", "g", "magnitude_cost_units", T(_cost_total())],
            ["set_attr", "g", "magnitude_rung",
             T(ITE(NO_HORIZON(), L("unknown_no_horizon"),
                   ITE(GT(ratio, L(1.0)),
                       ITE(GT(ratio_first, L(1.0)),
                           L("push_back"), L("balance")),
                       L("absorb"))))],
            ["set_attr", "g", "decompose_required",
             T(ITE(NO_HORIZON(), L(0.0),
                   ITE(GT(ratio_first, L(1.0)), L(1.0), L(0.0))))],
            ["set_attr", "g", "decompose_ladder_key",
             T(A(V("g"), "proposed_seam"))],
        ],
    }


# --------------------------------------------------------------------------- #
#  RULES — MG1: scope as a charge.
# --------------------------------------------------------------------------- #
def _in_scope(gvar="g"):
    return EXISTS(_live_constraints("scope", "sc"), "sc",
                  EQ(A(V("sc"), "scope_seam"), A(V(gvar), "sig_seam")))


def _any_scope_held():
    return EXISTS(_live_constraints("scope", "sa"), "sa", L(True))


def _r_scope_charge():
    return {
        "name": "mg_scope_charge",
        "comment": (
            "MG1. Scope lands as a CHARGE, never as a filter. If any non-stale "
            "scope constraint is held and this goal's sig_seam is not among "
            "them, it is charged w_out_of_scope inside VALUE_N -- it stays in "
            "the pool and can still win. A9's framing correction is the whole "
            "reason: three guards were proposed and all three were a missing "
            "input dressed as a hazard. Scope is a missing INPUT, so it is a "
            "TERM. Note the guard reads sig_seam and NOT proposed_seam: an "
            "unsignatured goal is illegible to scope exactly as it is illegible "
            "to every residual, and it already pays w_unsignatured for that in "
            "the lifted order-1 term."),
        "batch": True,
        "match": [["agenda", "has_arc_goal", "g"]],
        "where": AND(_any_scope_held(), NOT(_in_scope())),
        "effects": [["set_attr", "g", "out_of_scope", 1.0]],
    }


def _r_scope_clear():
    return {
        "name": "mg_scope_clear",
        "comment": (
            "THE OTHER DIRECTION, AND IT IS REQUIRED. gr_condition_lapse is "
            "deliberately not latched, so a scope constraint CAN come back and "
            "CAN go away; a one-way charge would be a second un-lapsable claim "
            "-- the exact defect gr_condition_hold exists to prevent. Clears to "
            "0.0 EXPLICITLY rather than unsetting, because this engine has no "
            "unset_attr and a null would sort BELOW any number in any later "
            "comparison (measured: Lt(null, 0.0) is TRUE). AND IT STAMPS THE "
            "0.0 ON A NEVER-CHARGED GOAL TOO, guarding on Not(Eq(_, 0.0)) "
            "rather than on Eq(_, 1.0): 'in scope' and 'never looked at' would "
            "otherwise be the same absent attr, and this tree has already lost "
            "a deferred claim to exactly that conflation. Terminates -- once "
            "0.0 is stamped the guard is false."),
        "batch": True,
        "match": [["agenda", "has_arc_goal", "g"]],
        "where": AND(
            NOT(EQ(A(V("g"), "out_of_scope"), L(0.0))),
            OR(NOT(_any_scope_held()), _in_scope()),
        ),
        "effects": [["set_attr", "g", "out_of_scope", 0.0]],
    }


# --------------------------------------------------------------------------- #
#  RULES — MG2/MG3: the order-N collapse.  ag_select's twin, one term swapped.
# --------------------------------------------------------------------------- #
MG_WINNER = ARGMAX(POOL_AS("mg2"), "mg2", VALUE_N(V("mg2")), None)


def _r_mg_select():
    return {
        "name": "mg_select",
        "comment": (
            "MG2/MG3, THE ORDER-N COLLAPSE. ag_select's twin over THE SAME "
            "POOL, machine-lifted from seeds/arc_goals.json, ranking by the "
            "SAME VALUE TERM with exactly one Attr key swapped (headroom_n -> "
            "orderN_headroom_n) and the scope charge subtracted. That is what "
            "makes 'order-N differs from order-1 on the shipped graph' a "
            "MEASUREMENT rather than a comparison of two things someone wrote "
            "separately: the same instrument reads the same nodes twice, and "
            "the only thing that changed is the term under test. A7's rule -- a "
            "control must be shown capable of detecting the difference it is "
            "used to rule out -- is satisfied structurally here, because the "
            "two readings are the same expression. Stamps mg_* alongside "
            "ag_select's arc_sel_*, so BOTH orderings are readable off one "
            "graph at one time and neither has to be re-derived."),
        "batch": True,
        "match": [["agenda", "uses_policy", "pol"]],
        "where": EXISTS(POOL_AS("mgx"), "mgx", L(True)),
        "effects": [
            ["set_attr", "agenda", "mg_sel_agid", T(A(MG_WINNER, "agid"))],
            ["set_attr", "agenda", "mg_sel_value",
             T(MAXOVER(POOL_AS("mg2"), "mg2", VALUE_N(V("mg2")), None))],
            ["set_attr", "agenda", "mg_horizon_net",
             T(ITE(NO_HORIZON(), L(-1.0), NUM(HORIZON_NET(), 0.0)))],
            ["set_attr", "agenda", "mg_horizon_gross",
             T(ITE(NO_HORIZON(), L(-1.0), NUM(HORIZON_GROSS(), 0.0)))],
        ],
    }


def _r_mg_select_audit():
    return {
        "name": "mg_select_audit",
        "comment": (
            "The audit stamp, binding the winner by its OWN stamped agid rather "
            "than re-deriving it -- ag_select_audit's shape and its reason: if "
            "this rule and mg_select ever disagreed about who won, the audit "
            "would be describing a different ranking from the one that fired."),
        "batch": True,
        "match": [["agenda", "uses_policy", "pol"],
                  ["agenda", "has_arc_goal", "g"]],
        "where": EQ(A(V("g"), "agid"), A(V("agenda"), "mg_sel_agid")),
        "effects": [
            ["set_attr", "agenda", "mg_sel_orderN_headroom_n",
             T(A(V("g"), "orderN_headroom_n"))],
            ["set_attr", "agenda", "mg_sel_order1_headroom_n",
             T(A(V("g"), "headroom_n"))],
            ["set_attr", "agenda", "mg_sel_rung",
             T(A(V("g"), "magnitude_rung"))],
            ["set_attr", "agenda", "mg_sel_order_n_basis",
             T(A(V("g"), "order_n_basis"))],
            ["set_attr", "agenda", "mg_sel_value_order1",
             T(VALUE_1(V("g")))],
        ],
    }


def _r_mg_select_runner_up():
    pool2 = FILT(POOL_AS("mg4"), "mg3",
                 NOT(EQ(A(V("mg3"), "agid"), A(V("agenda"), "mg_sel_agid"))))
    return {
        "name": "mg_select_runner_up",
        "comment": (
            "THE ORDER-N MARGIN. Split out for ag_select_runner_up's two "
            "measured reasons: deriving the winner inside the runner-up's own "
            "pool predicate embeds the whole lifted VALUE subtree once per use "
            "AND evaluates it once per pool element (that took arc_goals' seed "
            "to 2.4 MB), and this engine has NO RULE ORDERING, so the "
            "dependency mg_select -> mg_select_runner_up has to be a GUARD "
            "CHAIN keyed on the previous rule's stamp."),
        "batch": True,
        "match": [["agenda", "uses_policy", "pol"]],
        "where": AND(
            NOT(EQ(A(V("agenda"), "mg_sel_agid"), L(None))),
            EXISTS(pool2, "mg5", L(True)),
        ),
        "effects": [
            ["set_attr", "agenda", "mg_sel_runner_up_agid",
             T(A(ARGMAX(pool2, "mg5", VALUE_N(V("mg5")), None), "agid"))],
        ],
    }


def _r_mg_select_margin():
    return {
        "name": "mg_select_margin",
        "comment": (
            "The order-N margin itself, with the runner-up bound by its stamped "
            "agid. Reported next to ag_select's own arc_sel_margin so the "
            "repricing is readable as a NUMBER, not just as a reordering: on "
            "the shipped graph the two collapses disagree about the WINNER, and "
            "the margin is what says by how much."),
        "batch": True,
        "match": [["agenda", "uses_policy", "pol"],
                  ["agenda", "has_arc_goal", "mh"]],
        "where": EQ(A(V("mh"), "agid"), A(V("agenda"), "mg_sel_runner_up_agid")),
        "effects": [
            ["set_attr", "agenda", "mg_sel_runner_up_value",
             T(VALUE_N(V("mh")))],
            ["set_attr", "agenda", "mg_sel_margin",
             T(MINUS(A(V("agenda"), "mg_sel_value"), VALUE_N(V("mh"))))],
        ],
    }


# --------------------------------------------------------------------------- #
#  RULES — MG1: the ask for constraints, and the reply.
# --------------------------------------------------------------------------- #
def _r_ask_constraints():
    return {
        "name": "mg_ask_constraints",
        "comment": (
            "MG1. THE ASK IS FOR THE CONSTRAINT, NOT FOR APPROVAL, AND THAT IS "
            "THE ARGUMENT. A per-goal approval returns ONE BIT about ONE goal; "
            "ONE horizon answer reprices EVERY goal that has a ladder, because "
            "the horizon truncates the order sum. That asymmetry is the reason "
            "to ask constraints rather than permissions, and it is measured in "
            "results/arc6_magnitude.json rather than argued.\n"
            "TRIGGER IS T2 IGNORANCE, matching AG-4's discrimination: fire when "
            "NO horizon constraint currently holds. The distinction that "
            "matters is ignorance vs refutation -- a horizon that is held and "
            "CURRENT means the graph has been told and is not ignorant, so it "
            "does not ask; a horizon that has LAPSED means its reason is gone "
            "and asking again is correct, which falls out of _live_constraints "
            "reading `stale` rather than mere existence. RATE BOUND: one open "
            "question per measurement epoch, re-entry gated on NEW MEASUREMENT "
            "and never on graph churn (the codebook_epoch form).\n"
            "EVERY NUMBER IN THE TEXT GOES THROUGH ToJsonString: StringConcat "
            "SILENTLY DROPS numeric parts, which would have produced a question "
            "that looked fine and said nothing."),
        "batch": True,
        "match": [["agenda", "uses_policy", "pol"]],
        "where": AND(
            NO_HORIZON(),
            NOT(EXISTS(NOT_("ArcConstraintQuestion"), "q0",
                       EQ(A(V("q0"), "asked_epoch"), MEASURE_EPOCH()))),
            EXISTS(POOL_AS("mgq"), "mgq", L(True)),
        ),
        "effects": [
            ["add_node", "cq", "ArcConstraintQuestion", {
                "asked_epoch": T(MEASURE_EPOCH()),
                "answered": 0.0,
                "status": "open",
                "n_goals_in_pool": T(COUNT(POOL_AS("mgn"))),
                "trigger": "T2_ignorance_no_horizon_constraint_holds",
            }],
            ["add_node", "creply", "Message", {
                "from": "agent",
                "kind": "arc_constraint_question",
                "text": T(SCAT(
                    L("I am ranking "),
                    STR(COUNT(POOL_AS("mgc"))),
                    L(" arc goals and I hold NO horizon, so I am pricing every "
                      "one of them in a vacuum. My largest candidate carries a "
                      "MEASURED tier ladder costing "),
                    STR(MAXOVER(NOT_("ArcTier"), "tq",
                                NUM(A(V("tq"), "cum_cost_units"), 0.0), L(0.0))),
                    L(" operator units end to end, with its smallest buyable "
                      "increment at "),
                    STR(MINOVER(NOT_("ArcTier"), "tr",
                                NUM(A(V("tr"), "cum_cost_units"), 0.0), L(0.0))),
                    L(". I am not asking you to approve a goal -- that would "
                      "return one bit about one goal. WHAT IS THE HORIZON, in "
                      "those same units? One answer reprices all of them, "
                      "because a horizon truncates how far down a ladder I can "
                      "buy. Name a checkable condition with it, so the answer "
                      "can lapse when its reason does; without one it expires "
                      "at my next measurement epoch."),
                )),
            }],
            ["add_edge", "agenda", "asked_constraints", "cq"],
            ["add_edge", "cq", "answered_by", "creply"],
        ],
    }


def _constraint_attrs():
    return {
        "ckind": T(A(V("m"), "con_kind")),
        "horizon_units": T(A(V("m"), "con_horizon_units")),
        "scope_seam": T(A(V("m"), "con_scope_seam")),
        "competing_units": T(A(V("m"), "con_competing_units")),
        "priority": 1.0,
        "stale": 0.0,
        "evidence_kind": "utterance",
        "_never_parsed": (
            "the ckind and the numbers come from the con_* attrs the world "
            "adapter wrote, never from the reply text. A string-derived "
            "constraint is Seam C at arc grain."),
    }


def _creply_guard(conditioned):
    base = [
        EQ({"type": "TypeOf", "node": V("q")}, L("ArcConstraintQuestion")),
        NOT(EQ(A(V("q"), "answered"), L(1.0))),
        NOT(EQ(A(V("m"), "from"), L("agent"))),
        NOT(EQ(A(V("m"), "con_kind"), L(None))),
    ]
    base.append(NOT(EQ(A(V("m"), "cond_kind"), L(None))) if conditioned
                else EQ(A(V("m"), "cond_kind"), L(None)))
    return AND(*base)


def _r_constraint_conditioned():
    return {
        "name": "mg_constraint_from_reply_conditioned",
        "comment": (
            "MG1's CORE: A CONSTRAINT IS A CONDITIONED FACT, THROUGH THE "
            "EXISTING MACHINERY. The reply mints an ArcConstraint with a "
            "holds_under edge to a ResidualCondition -- and gr_condition_lapse "
            "/ gr_condition_hold match on the holds_under EDGE with NO TYPE "
            "RESTRICTION on their left var, so they lapse and restore an "
            "ArcConstraint verbatim. ZERO NEW LAPSE MECHANISM, which is exactly "
            "what MG1 registers. Verified live before this seed was written: an "
            "ArcConstraint with a fact_equals condition goes stale when the fact "
            "mismatches and comes back when it matches again. This branch is the "
            "one where the reply NAMED A CHECKABLE REASON, so the horizon "
            "survives until that reason is falsified -- a deadline that cannot "
            "lapse is a lie with a long half-life, and a horizon is the most "
            "load-bearing claim in the whole collapse."),
        "batch": True,
        "match": [["m", "responds_to", "q"]],
        "where": _creply_guard(True),
        "effects": [
            ["add_node", "kon", "ArcConstraint", _constraint_attrs()],
            ["add_node", "kcond", "ResidualCondition", {
                "rid": T(SCAT(L("arc.constraint."), A(V("m"), "con_kind"))),
                "ckind": T(A(V("m"), "cond_kind")),
                "filter_value": T(A(V("m"), "cond_filter_value")),
                "expected_str": T(A(V("m"), "cond_expected_str")),
                "expected": T(A(V("m"), "cond_expected")),
                "why": "named by the reply -- a reason that can be falsified",
            }],
            ["add_edge", "kon", "holds_under", "kcond"],
            ["set_attr", "q", "answered", 1.0],
            ["set_attr", "q", "status", "answered_conditioned"],
        ],
    }


def _r_constraint_unconditioned():
    return {
        "name": "mg_constraint_from_reply_unconditioned",
        "comment": (
            "THE DEFAULT CONDITION, AND IT IS THE POINT. A constraint answer "
            "naming no checkable reason gets fact_equals(arc_measure_epoch == "
            "<epoch at reply>), so IT EXPIRES AT THE NEXT MEASUREMENT EPOCH and "
            "the pool reverts to being priced in a vacuum -- visibly, through "
            "mg_rung's 'unknown_no_horizon', rather than silently continuing to "
            "use a stale deadline. Guard is the conditioned rule's with the "
            "cond_kind item NEGATED, so exactly one of the pair fires."),
        "batch": True,
        "match": [["m", "responds_to", "q"]],
        "where": _creply_guard(False),
        "effects": [
            ["add_node", "kon", "ArcConstraint", _constraint_attrs()],
            ["add_node", "kcond", "ResidualCondition", {
                "rid": T(SCAT(L("arc.constraint."), A(V("m"), "con_kind"))),
                "ckind": "fact_equals",
                "filter_value": "arc_measure_epoch",
                "expected_str": T(MEASURE_EPOCH()),
                "why": ("the reply named no checkable reason, so this "
                        "constraint expires at the next measurement epoch."),
            }],
            ["add_edge", "kon", "holds_under", "kcond"],
            ["set_attr", "q", "answered", 1.0],
            ["set_attr", "q", "status", "answered_unconditioned"],
        ],
    }


def _rules():
    return [
        _r_attrition_factor(),
        _r_tier_survival(),
        _r_tier_in_horizon(),
        _r_projection_measured(),
        _r_projection_unmeasured(),
        _r_goal_order_n(),
        _r_goal_order_n_default(),
        _r_rung(),
        _r_scope_charge(),
        _r_scope_clear(),
        _r_mg_select(),
        _r_mg_select_audit(),
        _r_mg_select_runner_up(),
        _r_mg_select_margin(),
        _r_ask_constraints(),
        _r_constraint_conditioned(),
        _r_constraint_unconditioned(),
    ]


def build():
    return {
        "_GENERATED_BY": "tools/build_arc_magnitude_seed.py",
        "_REGENERATION_IS_GATED_BYTE_IDENTICAL": (
            "tests/test_arc_magnitude_migrated.py::test_mg5_the_seed_"
            "regenerates_byte_identically re-runs this builder and diffs. "
            "VALUE_N is LIFTED from seeds/arc_goals.json at build time, so if "
            "ag_select ever changes this seed goes out of date LOUDLY instead "
            "of silently ranking by a value term that no longer matches the one "
            "it claims to be a reading of."),
        "self_load_only": True,
        "_SELF_LOAD_ONLY_RATIONALE": (
            "substrate/boot_all.py::_read_seeds GLOBS seeds/*.json and installs "
            "every match at boot, so a file here is live in EVERY agent in the "
            "tree the moment it lands. seeds/arc_goals.json ships "
            "self_load_only for that reason and this seed DEPENDS ON IT, so "
            "shipping this one globbed would activate a chain whose base is "
            "deliberately gated. REMOVING THIS KEY IS THE TREE-WIDE ACTIVATION "
            "and needs the paired sweep A5 requires."),
        "id": "arc_magnitude",
        "version": "1.1.0",
        "depends_on": ["goal_residuals", "arc_goals"],
        "description": (
            "CONSTRAINTS, ORDER-N PROJECTED VALUE, AND THE MAGNITUDE LADDER "
            "(MG1-MG3). seeds/arc_goals.json ranks arc goals by ABSOLUTE "
            "HEADROOM IN TASKS -- a SPOT valuation, priced in a vacuum. Three "
            "terms were missing and A9 registers all three as missing INPUTS "
            "rather than hazards needing guards. (1) CONSTRAINTS: horizon, "
            "scope and competing requirements land as ArcConstraint nodes with "
            "holds_under -> ResidualCondition, so gr_condition_lapse / "
            "gr_condition_hold lapse and restore them VERBATIM -- zero new "
            "lapse machinery -- and the ask requests them under T2 IGNORANCE. "
            "(2) ORDER-N VALUE: a goal carrying a MEASURED TIER LADDER is worth "
            "the horizon-truncated sum of its per-order increments, each "
            "discounted by attrition factors READ FROM RESULTS ARTIFACTS at "
            "named dotted paths -- there is NO attrition number in this file. A "
            "projection with no measured basis carries a fact_equals("
            "arc_measure_epoch) condition and EXPIRES at the next epoch. "
            "(3) THE LADDER: small absorb / medium balance / huge push back, "
            "routed by RATIOS against the measured horizon with no authored "
            "cutoff anywhere. "
            "v1.1.0 (A16/MG4): mg_goal_order_n_default gains ONE additive "
            "exclusion (a goal carrying parent_agid -- a decomposition child, "
            "seeds/arc_decompose.json) so the generic order-N fallback cannot "
            "silently overwrite a child's own discounted orderN_headroom_n "
            "back to its undiscounted headroom_n. INERT ON EVERY EXISTING "
            "SCENE: no goal on the shipped graph carries parent_agid. "
            "Decomposition ITSELF (mg_decompose, the child mint, the terminal "
            "status) lives in the SEPARATE seeds/arc_decompose.json, not here "
            "-- this seed still only sets decompose_required and names the "
            "measured ladder a split would use."),
        "microtheory": {
            "name": "arc_goal_magnitude",
            "description": (
                "A goal is not expensive in the abstract -- it is correct at "
                "twelve months and wrong at two weeks. A horizon is a "
                "conditioned fact that lapses like any other measurement; a "
                "projection beyond order 1 is a claim that must name the "
                "artifact it rests on or expire; and how big something is is a "
                "RATIO against a measured budget, never a number someone "
                "chose."),
        },
        "nodes": _nodes(),
        "edges": _edges(),
        "productions": _productions(),
        "rules": _rules(),
    }


def main(argv):
    text = json.dumps(build(), indent=2, sort_keys=False) + "\n"
    if "--check" in argv:
        cur = open(OUT).read() if os.path.exists(OUT) else ""
        if cur != text:
            print("seeds/arc_magnitude.json is OUT OF DATE", file=sys.stderr)
            return 1
        print("seeds/arc_magnitude.json is up to date")
        return 0
    with open(OUT, "w") as fh:
        fh.write(text)
    print("wrote", OUT, "(%d bytes)" % len(text))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
