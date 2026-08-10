#!/usr/bin/env python3
"""EMIT `seeds/arc_goals.json` — ARC-GRAIN GOAL MINTING (AG-1..AG-4).

`tools/*` are one-off AUTHORING scripts that EMIT seed manifests (CLAUDE.md:
"deletable; not agent runtime").  Nothing here runs at agent time and nothing
here decides anything about a live graph: it assembles JSON.

WHY A BUILDER AND NOT A HAND-WRITTEN SEED.  The design
(`PROGRAM_SYNTHESIS_ARC6_ARC_GOALS_DESIGN.md` §6.1) requires the residual
PENALTY sub-term to be reused *verbatim* — "copied character for character" —
from `gr_move_penalty`.  Hand-copying a 400-line Term subtree is exactly how a
misspelled field name becomes a silent no-op (`children_of` treats an unknown
`clauses` key on an `And` as an EMPTY conjunction returning True).  So the
subtree is LIFTED PROGRAMMATICALLY out of `seeds/goal_residuals.json` and
alpha-renamed; `test_arc_goals_migrated.py` re-derives the lift and asserts the
shipped seed is byte-identical to a fresh build.

Run:  python tools/build_arc_goals_seed.py         (writes seeds/arc_goals.json)
      python tools/build_arc_goals_seed.py --check (fails if out of date)
"""
from __future__ import annotations

import copy
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEEDS = os.path.join(ROOT, "seeds")
RESIDUAL_SEED = os.path.join(SEEDS, "goal_residuals.json")
OUT = os.path.join(SEEDS, "arc_goals.json")


# --------------------------------------------------------------------------- #
#  Term constructors — mechanical JSON assembly.
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


def ARGMIN(source, var_name, value, default=None):
    return {"type": "Argmin", "source": source, "var_name": var_name,
            "value": value, "default": default}


def ARGMAX(source, var_name, value, default=None):
    return {"type": "Argmax", "source": source, "var_name": var_name,
            "value": value, "default": default}


def MAXOVER(source, var_name, value, default=None):
    return {"type": "MaxOver", "source": source, "var_name": var_name,
            "value": value, "default": default}


def TIMES(*items):
    return {"type": "Times", "items": list(items)}


def PLUS(*items):
    return {"type": "Plus", "items": list(items)}


def MINUS(a, b):
    return {"type": "Minus", "a": a, "b": b}


def ITE(cond, then, other):
    return {"type": "IfThenElse", "cond": cond, "then": then, "other": other}


def SCAT(*parts):
    return {"type": "StringConcat", "parts": list(parts)}


def STR(term):
    """Number -> string.  MEASURED: `StringConcat` SILENTLY DROPS numeric
    parts (`'f= i='` for two numeric attrs), so every measured number in the
    question text goes through `ToJsonString` first."""
    return {"type": "ToJsonString", "value": term}


def T(term):
    """`{"__term__": ...}` effect wrapper."""
    return {"__term__": term}


# The one Argmin idiom this tree uses to mean "exactly one element of a fixed
# snapshot" (gap_awareness::retire_duplicate_gap).
def ONE_OF(source, var_name):
    return ARGMIN(source, var_name, L(0), None)


# --------------------------------------------------------------------------- #
#  THE LIFT — `gr_move_penalty`'s PENALTY subtree, taken from the shipped seed.
# --------------------------------------------------------------------------- #
def _residual_rule(name):
    with open(RESIDUAL_SEED) as fh:
        d = json.load(fh)
    for r in d["rules"]:
        if r["name"] == name:
            return r
    raise SystemExit("no such rule in seeds/goal_residuals.json: " + name)


def _rename_var(tree, old, new):
    tree = copy.deepcopy(tree)

    def walk(o):
        if isinstance(o, dict):
            if o.get("type") == "Var" and o.get("name") == old:
                o["name"] = new
            for k in ("var_name",):
                if o.get(k) == old:
                    o[k] = new
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    walk(tree)
    return tree


def _lift_penalty():
    """Return (EXISTS_MATCH_template, PENALTY_template).

    Both are lifted from `gr_move_penalty`'s own effect, with the candidate var
    `mc` renamed to the sentinel `__CAND__` and the residual-side var `grr`
    renamed to `agrr` (so a nested use never shadows an outer `grr`).
    """
    r = _residual_rule("gr_move_penalty")
    eff = None
    for e in r["effects"]:
        if e[0] == "set_attr" and e[2] == "residual_penalty":
            eff = e[3]
            break
    if eff is None:
        raise SystemExit("gr_move_penalty no longer writes residual_penalty")
    penalty = eff["__term__"]
    assert penalty["type"] == "IfThenElse", penalty["type"]
    penalty = _rename_var(penalty, "mc", "__CAND__")
    penalty = _rename_var(penalty, "grr", "agrr")
    exists_match = copy.deepcopy(penalty["cond"])
    assert exists_match["type"] == "Exists", exists_match["type"]
    return exists_match, penalty


_EXISTS_MATCH_T, _PENALTY_T = _lift_penalty()


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


def EXISTS_MATCH(node_term):
    """`gr_move_penalty`'s own Exists predicate, applied to any node carrying
    `sig_*`.  THIS IS THE IGNORANCE/REFUTATION DISCRIMINATOR (design §7.1 T2):
    negated, it says *nothing is held either way*."""
    return _subst_cand(_EXISTS_MATCH_T, node_term)


def PENALTY(node_term):
    """The verbatim residual penalty, at arc grain."""
    return _subst_cand(_PENALTY_T, node_term)


# --------------------------------------------------------------------------- #
#  Policy reads — graph data, not literals in a rule.
# --------------------------------------------------------------------------- #
def POL(key):
    return A(ARGMIN(NOT_("ArcGoalPolicy"), "apol",
                    A(V("apol"), "priority"), None), key)


def ASKPOL(key):
    return A(ARGMIN(NOT_("ArcAskPolicy"), "aask",
                    A(V("aask"), "priority"), None), key)


def TESTPOL(key):
    return A(ARGMIN(NOT_("TestimonyPolicy"), "atp",
                    A(V("atp"), "priority"), None), key)


def MEASURE_EPOCH():
    """The measurement epoch, read as the STRING it is stored as.

    It lives as `ResidualFact{name:'arc_measure_epoch'}` — the SAME node type
    `gr_condition_lapse`'s `fact_equals` branch already reads — so an
    unconditioned testimony residual expires through the EXISTING lapse
    machinery with zero new mechanism (design §7.3).  Kept as a string
    throughout: `Eq` then never straddles the float/str boundary.
    """
    return A(ARGMIN(FILT(NOT_("ResidualFact"), "aef",
                         EQ(A(V("aef"), "name"), L("arc_measure_epoch"))),
                    "aef2", L(0), None), "value")


# --------------------------------------------------------------------------- #
#  THE VALUE — design §6.2.  ABSOLUTE HEADROOM, NOT THE DIMENSIONLESS RATIO.
# --------------------------------------------------------------------------- #
def VALUE(node_term):
    """value(g) = w_headroom*headroom_n*reach_class_factor
                - w_residual*PENALTY(g) - w_mdl*novelty_bits
                - w_cost*cost_bits   - w_unsig*[no sig_seam]

    `headroom_n` is IN TASKS (denominator_n - honest_n).  The residual weight
    formula is a DIMENSIONLESS RATIO — right for a penalty, wrong as a value,
    because it ranks `row_verdict` (denominator 15) equal to `ir_retarget`
    (257).  Same measured numbers, different reading.
    """
    return MINUS(
        TIMES(POL("w_headroom"),
              A(node_term, "headroom_n"),
              A(node_term, "reach_class_factor")),
        PLUS(
            TIMES(POL("w_residual"), PENALTY(node_term)),
            TIMES(POL("w_mdl"), A(node_term, "novelty_bits")),
            TIMES(POL("w_cost"), A(node_term, "cost_bits")),
            TIMES(POL("w_unsignatured"),
                  ITE(EQ(A(node_term, "sig_seam"), L(None)), L(1.0), L(0.0))),
        ))


def POOL(agenda_var="agenda"):
    """Pool membership — and NOTHING ELSE — is a Filter.  No residual, no
    novelty, no cost appears here: that is the weight/veto line, structural."""
    return FILT(NEIGH(V(agenda_var), "has_arc_goal"), "g2",
                AND(NOT(EQ(A(V("g2"), "status"), L("retired"))),
                    NOT(EQ(A(V("g2"), "status"), L("settled"))),
                    GT(A(V("g2"), "headroom_n"), L(0.0))))


def POOL_AS(var):
    """The same pool, with the Filter variable renamed (a nested Argmax may
    not reuse the outer one's binder name)."""
    return _rename_var(POOL(), "g2", var)


WINNER = ARGMAX(POOL(), "g2", VALUE(V("g2")), None)


def RUNNER_UP():
    """Top-2 = Argmax over the pool with the winner EXCLUDED BY ITS STAMPED
    `agid`, not by re-deriving the winner inside the predicate.

    Re-deriving it is what a naive reading writes, and it is quadratic in the
    VALUE term: the winner's whole Argmax (which contains the lifted PENALTY)
    would be evaluated once per pool element AND embedded once per use, which
    took the emitted seed to 2.4 MB.  Reading the stamp instead makes the
    rung's ORDER explicit -- `ag_select_runner_up` requires `arc_sel_agid` to
    be present, which is the guard-chain form this engine uses everywhere in
    place of rule ordering.
    """
    pool2 = FILT(POOL_AS("g4"), "g3",
                 NOT(EQ(A(V("g3"), "agid"), A(V("agenda"), "arc_sel_agid"))))
    return ARGMAX(pool2, "g5", VALUE(V("g5")), None)


def REGION(node_term):
    return ITE(EQ(A(node_term, "sig_seam"), L(None)),
               A(node_term, "agid"), A(node_term, "sig_seam"))


# --------------------------------------------------------------------------- #
#  NODES
# --------------------------------------------------------------------------- #
def _nodes():
    n = []
    n.append({"local_id": 2000, "type": "ArcGoalPolicy", "attrs": {
        "name": "default_arc_goal_policy",
        "priority": 1,
        "w_headroom": 1.0,
        "w_residual": 1.0,
        "w_mdl": 4.0,
        "w_cost": 1.0,
        "w_unsignatured": 25.0,
        "tie_break": "insertion_order_stable",
        "_authored_not_measured": (
            "w_* are AUTHORED policy, tunable as graph data without touching a "
            "rule -- the RESIDUAL_SCALE=100 precedent."),
        "_tie_break_is_MEASURED_not_lexical": (
            "The design asked for an explicitly pinned tie-break (agid lexical "
            "or minted_epoch) rather than an inherited one. MEASURED: this "
            "engine's Argmax returns the FIRST-INSERTED node under a tie, "
            "stably across repeated evaluation. A LEXICAL tie-break is NOT "
            "expressible with the shipped Term set -- there is no string "
            "ordering primitive and `sorted`-on-strings is a known-unfixed "
            "defect in this tree -- so the honest pin is the measured one, "
            "gated by re-running the same graph state and by rebuilding the "
            "same scene in insertion order. Recorded as a residual, not as a "
            "solved requirement."),
        "_w_unsignatured_rationale": (
            "An ArcGoal with no sig_seam cannot be matched by ANY GoalResidual "
            "(the lifted matcher requires a non-null sig_seam), so it escapes "
            "every refutation the agent holds. Without a cost, the cheapest way "
            "for the loop to evade its own evidence is to mint everything "
            "unsignatured. UNMEASURED beyond its two-position gate."),
    }})

    n.append({"local_id": 2001, "type": "ArcAskPolicy", "attrs": {
        "name": "default_arc_ask_policy",
        "priority": 1,
        "margin_threshold": 5.0,
        "max_open_questions": 1.0,
        "_rationale": (
            "The ask is a CANDIDATE IN THE SAME COLLAPSE, not a gate. "
            "margin_threshold is cascade_pick's Lt(margin, threshold) "
            "escalate-or-stay shape (seeds/escalation_rungs.json)."),
    }})

    n.append({"local_id": 2002, "type": "TestimonyPolicy", "attrs": {
        "name": "default_testimony_policy",
        "priority": 1,
        "factor": 0.5,
        "scale": 100.0,
        "default_condition_kind": "fact_equals",
        "default_condition_fact": "arc_measure_epoch",
        "_rationale": (
            "A human answer becomes a GoalResidual with evidence_kind='utterance' "
            "so gr_condition_lapse/gr_condition_hold apply VERBATIM -- zero new "
            "lapse machinery. Testimony is not measurement, so reach_class_factor "
            "is replaced by this AUTHORED factor; and an answer naming no "
            "checkable condition gets fact_equals(arc_measure_epoch == <epoch at "
            "reply>), i.e. IT EXPIRES AT THE NEXT MEASUREMENT EPOCH. Angluin's "
            "zero-bits result made mechanical."),
    }})

    for lid, kind, req, extra, desc in (
        (2003, "residual_stale", 1.0, {},
         "A GoalResidual whose condition has lapsed no longer describes the "
         "world and must be re-made before it may be used again. FIRES ON A "
         "CLEAN BOOT on engine 8311d4356082: the value layer distinguishes list "
         "from tuple, which falsifies value_layer_list_eq_tuple=='1' and lapses "
         "arc6.verdict.row_verdict_seed_only."),
        (2004, "residual_blocker", 1.0, {},
         "A residual's MEASURED BLOCKER SPLIT, not its reach_class. reach_class "
         "alone is measured nearly inert: all six residuals are "
         "operator_blocked and dimension_vs_operator.missing_dimension_ids == "
         "[]. One level finer IS usable -- seam A carries budget 7 / "
         "missing_dimension 4 / missing_structural_primitive 42 over the "
         "live-unreached 53, read graph-natively via "
         "DictGet(FromJsonString(reach_class_counts)). And "
         "missing_structural_primitive is NOT a sig_seam token, so this source "
         "FORCES the vocabulary question rather than dodging it."),
        (2005, "not_ingested", 0.0, {},
         "domains/goal_residual_ingest.DELIBERATELY_NOT_INGESTED -- four claims "
         "left out of the residual seed for having no measured source. Each is a "
         "measurement that does not exist yet. ALSO THE DESIGNED PROBE for the "
         "cheap-goal-convergence failure mode: these are the cheapest goals "
         "available, so if the collapse converges on them the value term is "
         "wrong, and that is OBSERVABLE."),
        (2006, "self_concern", 0.0, {"mints_unsignatured": 1.0},
         "The existing gap spine files SelfConcern{status:'noted'} with "
         "free-text content. Routed in, but the content is NEVER parsed into a "
         "signature -- that is Seam C's failure exactly. A SelfConcern-sourced "
         "ArcGoal is minted with NO sig_* attrs, so it can be pursued but cannot "
         "be matched by any residual -- and pays w_unsignatured for that."),
    ):
        n.append({"local_id": lid, "type": "ArcMintSource",
                  "attrs": dict({"kind": kind, "requires_evidence": req,
                                 "description": desc}, **extra)})

    n.append({"local_id": 2007, "type": "SeamAliasTable", "attrs": {
        "name": "sig_seam_aliases",
        "n_aliases": 0.0,
        "_rationale": (
            "RUNG 2 of the vocabulary ladder is 'the token is in the existing "
            "basis'. The basis map is a table of AUTHORED SeamAlias{token, "
            "alias_of} nodes -- NEVER string similarity. It ships EMPTY: "
            "specificity is an authored, auditable, COUNTABLE property."),
    }})

    n.append({"local_id": 2010, "type": "ArcAgenda", "attrs": {
        "name": "arc6",
        "arc_vocab_epoch": 0.0,
        "_hub_rationale": (
            "The arc goal pool needs a hub a rule can bind. The Agent node is "
            "created by whichever adapter booted, so a seed cannot ship an edge "
            "to it; this node CAN be shipped with its edges, and every arc rule "
            "binds it by matching agenda -uses_policy-> pol. Nothing about it is "
            "a decision -- it is the pool's identity."),
    }})

    # The blocker vocabulary — AUTHORED names, matching the keys the measured
    # `reach_class_counts` payload actually carries.  The counts are NOT here:
    # they are read live off the residual.
    for lid, name in ((2020, "budget"),
                      (2021, "missing_dimension"),
                      (2022, "missing_structural_primitive")):
        n.append({"local_id": lid, "type": "ArcBlockerKey", "attrs": {
            "name": name,
            "_note": ("a KEY, not a count. The count is read from the "
                      "residual's own measured reach_class_counts payload."),
        }})

    # §4.3 — the four DELIBERATELY_NOT_INGESTED claims, verbatim, as the
    # cheap-goal probe.  denominator/headroom are 1 task each: they are
    # measurements that do not exist yet, not reach.
    claims = (
        (2030, "arc6.claim.seam_b_signature_39_of_257",
         "results/arc6_bc_ceiling.json", "ceiling_b_extract_function",
         "only 39/257 tasks have the f(int)->int signature seam B's grammar "
         "can emit; 218 (85%) are excluded before semantics apply"),
        (2031, "arc6.claim.seam_d_verbatim_35_of_36",
         "results/arc6_d_loo.json", "_README",
         "35 of 36 seam-D atoms carried a verbatim prompt substring and "
         "cue-matched only their own task"),
        (2032, "arc6.claim.tier0_hs1_0_of_10",
         "results/arc6_tier0.json", "_README",
         "HS1 failed 0 of 10 converted (tier 0)"),
        (2033, "arc6.claim.valuelayer_supersedes_row_verdict",
         "results/arc6_valuelayer.json", "arms.C_minus_B.pass_gained",
         "the row-verdict null is superseded -- arm C converted 12 more ids"),
    )
    for lid, cid, art, path, claim in claims:
        n.append({"local_id": lid, "type": "ArcSourceClaim", "attrs": {
            "claim_id": cid, "evidence_artifact": art, "evidence_path": path,
            "claim": claim, "denominator_n": 1.0, "headroom_n": 1.0,
            "cost_bits": 1.0,
            "_note": ("quoted verbatim from "
                      "domains/goal_residual_ingest.DELIBERATELY_NOT_INGESTED"),
        }})
    return n


def _edges():
    e = [{"src": {"local": 2010}, "tgt": {"local": 2000},
          "type": "uses_policy", "attrs": {}}]
    for lid in (2020, 2021, 2022):
        e.append({"src": {"local": 2010}, "tgt": {"local": lid},
                  "type": "has_blocker_key", "attrs": {}})
    for lid in (2030, 2031, 2032, 2033):
        e.append({"src": {"local": 2010}, "tgt": {"local": lid},
                  "type": "has_source_claim", "attrs": {}})
    return e


def _productions():
    p = [("ArcAgenda", "uses_policy", "ArcGoalPolicy"),
         ("ArcAgenda", "has_blocker_key", "ArcBlockerKey"),
         ("ArcAgenda", "has_source_claim", "ArcSourceClaim"),
         ("ArcAgenda", "has_arc_goal", "ArcGoal"),
         ("ArcAgenda", "sent", "Message"),
         ("ArcGoal", "mint_source", "GoalResidual"),
         ("ArcGoal", "mint_source", "ArcSourceClaim"),
         ("ArcGoal", "mint_source", "SelfConcern"),
         ("ArcGoal", "holds_under", "ResidualCondition"),
         ("ArcGoal", "vocab_minted", "SignatureVocab"),
         ("GoalResidual", "remeasure_goal", "ArcGoal"),
         ("ArcSourceClaim", "claim_goal", "ArcGoal"),
         ("SelfConcern", "concern_goal", "ArcGoal"),
         ("ArcQuestion", "asked_about", "ArcGoal"),
         ("ArcQuestion", "answered_by", "Message"),
         ("Message", "responds_to", "ArcQuestion"),
         ("GoalResidual", "holds_under", "ResidualCondition")]
    return [{"provenance": "seed:arc_goals:%s-%d" % (et, i),
             "src": {"type": s, "var": "s"}, "edge_type": et,
             "tgt": {"type": t, "var": "t"}}
            for i, (s, et, t) in enumerate(p)]


# --------------------------------------------------------------------------- #
#  RULES
# --------------------------------------------------------------------------- #
HUB = [["agenda", "uses_policy", "pol"]]


def _r_mint_remeasure():
    """AG-1, mint source `residual_stale`."""
    eligible = FILT(NOT_("GoalResidual"), "r2",
                    AND(EQ(A(V("r2"), "stale"), L(1.0)),
                        EQ(COUNT(NEIGH(V("r2"), "remeasure_goal")), L(0))))
    return {
        "name": "ag_mint_remeasure",
        "comment": (
            "AG-1, MINT SOURCE 'residual_stale'. A GoalResidual whose condition "
            "has lapsed mints ONE ArcGoal{kind:'re_measure'} carrying the "
            "residual's own signature and its MEASURED headroom in tasks. "
            "Mint-once via the 'remeasure_goal' edge (a MONOTONE latch -- this "
            "engine has no remove_edge). TWO SERIALIZERS, both load-bearing for "
            "DIFFERENT reasons: (a) the residual must BE the Argmin survivor "
            "over the eligible snapshot, because this engine applies effects "
            "against PRE-EFFECT reads, so two stale residuals in one pass would "
            "otherwise both mint; (b) the CONDITION must likewise be the Argmin "
            "survivor over this residual's own holds_under neighbours, because "
            "seam C has TWO conditions and the edge latch cannot help -- both "
            "bindings are collected before either effect applies. "
            "THE ANNIHILATION CHECK: this goal carries its SOURCE's signature, "
            "which would normally mean the source charges it its own full "
            "weight and mint and penalty cancel. It survives because the "
            "matcher's Exists requires Not(Eq(stale,1)) -- A STALE RESIDUAL "
            "CHARGES NOTHING. The existing matcher is correct for this case BY "
            "CONSTRUCTION, and ag_remeasure_retire handles the other direction."),
        "batch": True,
        "match": HUB + [["r", "holds_under", "c"]],
        "where": AND(
            EQ(A(V("r"), "stale"), L(1.0)),
            EQ(COUNT(NEIGH(V("r"), "remeasure_goal")), L(0)),
            EQ(V("r"), ONE_OF(eligible, "r3")),
            EQ(V("c"), ONE_OF(NEIGH(V("r"), "holds_under"), "c2")),
        ),
        "effects": [
            ["add_node", "g", "ArcGoal", {
                "agid": T(SCAT(L("arc.remeasure."), A(V("r"), "rid"))),
                "kind": "re_measure",
                "source_kind": "residual_stale",
                "sig_seam": T(A(V("r"), "sig_seam")),
                "sig_lever": T(A(V("r"), "sig_lever")),
                "sig_target": T(A(V("r"), "sig_target")),
                "reach_class": T(A(V("r"), "reach_class")),
                "reach_class_factor": T(A(V("r"), "reach_class_factor")),
                "denominator_n": T(A(V("r"), "denominator_n")),
                "headroom_n": T(MINUS(A(V("r"), "denominator_n"),
                                      A(V("r"), "ceiling_honest_n"))),
                "evidence_artifact": T(A(V("r"), "evidence_artifact")),
                "evidence_path": T(A(V("c"), "filter_value")),
                "novelty_bits": 0.0,
                "cost_bits": 0.0,
                "status": "minted",
                "vocab_checked": 1.0,
                "vocab_explained": 1.0,
                "dim_checked": 1.0,
                "_vocab_explained_note": (
                    "a re-measure goal reuses its source's already-held "
                    "signature, so the vocabulary ladder is satisfied at rung 1 "
                    "by construction and never reaches the mint."),
            }],
            ["add_edge", "g", "mint_source", "r"],
            ["add_edge", "r", "remeasure_goal", "g"],
            ["add_edge", "agenda", "has_arc_goal", "g"],
        ],
    }


def _r_remeasure_retire():
    return {
        "name": "ag_remeasure_retire",
        "comment": (
            "THE OTHER DIRECTION, and it is REQUIRED, not a nicety. "
            "gr_condition_lapse/gr_condition_hold are deliberately NOT latched, "
            "so a residual that lapsed CAN COME BACK. When it does, the "
            "re-measure goal it spawned is (a) obsolete and (b) suddenly charged "
            "its own source's full weight. Relying on the weight alone would "
            "leave a dead goal sitting in the pool forever. NOT a veto: retiring "
            "an obsolete re-measurement removes a request whose REASON has gone; "
            "it does not suppress a goal on the strength of evidence."),
        "batch": True,
        "match": [["r", "remeasure_goal", "g"]],
        "where": AND(
            NOT(EQ(A(V("r"), "stale"), L(1.0))),
            NOT(EQ(A(V("g"), "status"), L("retired"))),
        ),
        "effects": [
            ["set_attr", "g", "status", "retired"],
            ["set_attr", "g", "retired_because",
             "source_residual_no_longer_stale"],
        ],
    }


def _r_mint_blocker():
    """AG-1, mint source `residual_blocker` — the MEASURED split."""
    count_of = {"type": "DictGet",
                "dict": {"type": "FromJsonString",
                         "text": A(V("r"), "reach_class_counts")},
                "key": A(V("bk"), "name")}
    return {
        "name": "ag_mint_blocker",
        "comment": (
            "AG-1, MINT SOURCE 'residual_blocker' -- FROM THE MEASURED BLOCKER "
            "SPLIT, NOT FROM reach_class. Measured, reach_class alone is nearly "
            "inert: all six residuals are operator_blocked and "
            "missing_dimension_ids == [], so the missing_dimension branch would "
            "mint NOTHING and the operator_blocked branch six 'rebuild the seam "
            "we just killed' goals. One level finer IS usable and is already on "
            "the node: seam A's reach_class_counts payload, read graph-natively "
            "with DictGet(FromJsonString(...)) -- no Python parse. "
            "'Supply the structural primitive that blocks 42 tasks' is a "
            "DIFFERENT goal with a DIFFERENT signature from 'rebuild seam A', so "
            "there is no annihilation. And the blocker names are NOT sig_seam "
            "tokens, so this source FORCES the vocabulary ladder (AG-3) on real "
            "measured data rather than on a fixture. headroom_n IS the measured "
            "count -- in tasks. Mint-once by (source_kind, proposed_seam, rid) "
            "dedup rather than an edge latch, because ONE residual mints THREE "
            "goals and an edge latch on the residual would stop after the first."),
        "batch": True,
        "match": HUB + [["agenda", "has_blocker_key", "bk"], ["r", "holds_under", "c"]],
        "where": AND(
            NOT(EQ(A(V("r"), "reach_class_counts"), L(None))),
            NOT(EQ(A(V("r"), "stale"), L(1.0))),
            GT(count_of, L(0)),
            NOT(EXISTS(NOT_("ArcGoal"), "gd",
                       AND(EQ(A(V("gd"), "source_kind"), L("residual_blocker")),
                           EQ(A(V("gd"), "proposed_seam"), A(V("bk"), "name")),
                           EQ(A(V("gd"), "source_rid"), A(V("r"), "rid"))))),
            EQ(V("c"), ONE_OF(NEIGH(V("r"), "holds_under"), "c2")),
            # one mint per pass — the pcon_mint serializer, keyed on the
            # (residual, blocker) pair so the fixpoint drains them one at a time
            # and each new goal is visible to the next pass's dedup.
            EQ(V("bk"), ONE_OF(FILT(NEIGH(V("agenda"), "has_blocker_key"), "bk2",
                                    NOT(EXISTS(NOT_("ArcGoal"), "gd2",
                                               AND(EQ(A(V("gd2"), "source_kind"),
                                                      L("residual_blocker")),
                                                   EQ(A(V("gd2"), "proposed_seam"),
                                                      A(V("bk2"), "name")),
                                                   EQ(A(V("gd2"), "source_rid"),
                                                      A(V("r"), "rid")))))),
                              "bk3")),
        ),
        "effects": [
            ["add_node", "g", "ArcGoal", {
                "agid": T(SCAT(L("arc.supply."), A(V("r"), "rid"), L("."),
                               A(V("bk"), "name"))),
                "kind": "supply_blocker",
                "source_kind": "residual_blocker",
                "source_rid": T(A(V("r"), "rid")),
                "proposed_seam": T(A(V("bk"), "name")),
                "sig_lever": T(A(V("r"), "sig_lever")),
                "sig_target": T(A(V("r"), "sig_target")),
                "reach_class": T(A(V("bk"), "name")),
                "reach_class_factor": 1.0,
                "denominator_n": T(A(V("r"), "denominator_n")),
                "headroom_n": T(count_of),
                "evidence_artifact": T(A(V("r"), "evidence_artifact")),
                "evidence_path": "reach_class_counts",
                "novelty_bits": 0.0,
                "cost_bits": 0.0,
                "status": "minted",
            }],
            ["add_edge", "g", "mint_source", "r"],
            ["add_edge", "agenda", "has_arc_goal", "g"],
        ],
    }


def _r_mint_source_claim():
    return {
        "name": "ag_mint_source_claim",
        "comment": (
            "AG-1, MINT SOURCE 'not_ingested' (design §4.3) -- cheap, honest, "
            "small, AND THE DESIGNED ANTI-GOODHART PROBE. Each of the four "
            "DELIBERATELY_NOT_INGESTED claims is a measurement that does not "
            "exist yet, i.e. exactly a goal, whose success criterion is "
            "unambiguous (a dotted path resolves). They are also the CHEAPEST "
            "goals available, so IF THE COLLAPSE CONVERGES ON THEM THE VALUE "
            "TERM IS WRONG -- and that is observable rather than argued. "
            "They are minted UNSIGNATURED (no sig_seam) and therefore pay "
            "w_unsignatured, which is what keeps a 1-task claim from outranking "
            "a 42-task blocker."),
        "batch": True,
        "match": HUB + [["agenda", "has_source_claim", "sc"]],
        "where": AND(
            EQ(COUNT(NEIGH(V("sc"), "claim_goal")), L(0)),
        ),
        "effects": [
            ["add_node", "g", "ArcGoal", {
                "agid": T(A(V("sc"), "claim_id")),
                "kind": "source_claim",
                "source_kind": "not_ingested",
                "reach_class_factor": 1.0,
                "denominator_n": T(A(V("sc"), "denominator_n")),
                "headroom_n": T(A(V("sc"), "headroom_n")),
                "evidence_artifact": T(A(V("sc"), "evidence_artifact")),
                "evidence_path": T(A(V("sc"), "evidence_path")),
                "novelty_bits": 0.0,
                "cost_bits": T(A(V("sc"), "cost_bits")),
                "status": "minted",
                "vocab_checked": 1.0,
                "vocab_explained": 1.0,
                "dim_checked": 1.0,
            }],
            ["add_edge", "g", "mint_source", "sc"],
            ["add_edge", "sc", "claim_goal", "g"],
            ["add_edge", "agenda", "has_arc_goal", "g"],
        ],
    }


def _r_mint_self_concern():
    return {
        "name": "ag_mint_self_concern",
        "comment": (
            "AG-1, MINT SOURCE 'self_concern' (design §4.4) -- ADMITTED AT A "
            "COST. The existing gap spine files SelfConcern{status:'noted'} with "
            "free-text content; routing it in is right, it is the tree's own "
            "'the agent finds its own gaps' channel. WHAT MUST NOT HAPPEN is "
            "parsing that free text into a signature -- Seam C's failure exactly "
            "(the relation_all keyword variant 'recognised' 245 of 257 tasks; "
            "the cue set matched 'turn' inside 'reTURNs'). So the goal is minted "
            "WITH NO sig_* ATTRS AT ALL. It can be pursued (unsignatured "
            "candidates are charged 0.0 by the matcher, measured) but cannot be "
            "matched by any residual -- and it pays w_unsignatured for that "
            "illegibility. Being illegible to the evidence layer is a COST, not "
            "a free pass."),
        "batch": True,
        "match": HUB + [["ag", "has_self_concern", "sc"]],
        "where": AND(
            EQ(COUNT(NEIGH(V("sc"), "concern_goal")), L(0)),
            NOT(EQ(A(V("sc"), "status"), L("retired"))),
        ),
        "effects": [
            ["add_node", "g", "ArcGoal", {
                "agid": T(SCAT(L("arc.concern."), A(V("sc"), "content"))),
                "kind": "reported",
                "source_kind": "self_concern",
                "reach_class_factor": 1.0,
                "denominator_n": 1.0,
                "headroom_n": 1.0,
                "novelty_bits": 0.0,
                "cost_bits": 0.0,
                "status": "minted",
                "vocab_checked": 1.0,
                "vocab_explained": 1.0,
                "dim_checked": 1.0,
                "_unsignatured": (
                    "no sig_* attrs, deliberately -- free text is never parsed "
                    "into a signature."),
            }],
            ["add_edge", "g", "mint_source", "sc"],
            ["add_edge", "sc", "concern_goal", "g"],
            ["add_edge", "agenda", "has_arc_goal", "g"],
        ],
    }


# ---- AG-3: the vocabulary ladder --------------------------------------- #
def _vocab_held(gvar="g"):
    return EXISTS(NOT_("SignatureVocab"), "v",
                  AND(EQ(A(V("v"), "dim"), L("sig_seam")),
                      EQ(A(V("v"), "token"), A(V(gvar), "proposed_seam"))))


def _r_vocab_recognize():
    return {
        "name": "ag_vocab_recognize",
        "comment": (
            "VOCABULARY LADDER RUNG 1 -- EXACT RECOGNISE (the sd_recognize "
            "twin). The proposed token IS a held SignatureVocab{dim:'sig_seam'}: "
            "adopt it, and the ladder terminates here. Sets vocab_checked AND "
            "vocab_explained ATOMICALLY, so no deeper rung can ever see "
            "checked-without-the-look-having-happened. This engine has no rule "
            "ordering -- THE OCCAM ORDER IS THE GUARD CHAIN."),
        "batch": True,
        "match": [["agenda", "has_arc_goal", "g"]],
        "where": AND(
            NOT(EQ(A(V("g"), "vocab_checked"), L(1.0))),
            NOT(EQ(A(V("g"), "proposed_seam"), L(None))),
            _vocab_held(),
        ),
        "effects": [
            ["set_attr", "g", "sig_seam", T(A(V("g"), "proposed_seam"))],
            ["set_attr", "g", "vocab_checked", 1.0],
            ["set_attr", "g", "vocab_explained", 1.0],
            ["set_attr", "g", "novelty_bits", 0.0],
        ],
    }


def _r_vocab_alias():
    alias = ONE_OF(FILT(NOT_("SeamAlias"), "a2",
                        EQ(A(V("a2"), "token"), A(V("g"), "proposed_seam"))),
                   "a3")
    return {
        "name": "ag_vocab_alias",
        "comment": (
            "VOCABULARY LADDER RUNG 2 -- IN THE EXISTING BASIS (the "
            "sd_transform_decode twin). The proposed token is a held "
            "SeamAlias{token, alias_of}: adopt alias_of. THE ALIAS TABLE IS "
            "AUTHORED GRAPH DATA AND SHIPS EMPTY -- never string similarity, "
            "never substring overlap. An alias that must be written down is "
            "countable and auditable; an alias inferred from characters is "
            "Seam C's 245-of-257."),
        "batch": True,
        "match": [["agenda", "has_arc_goal", "g"]],
        "where": AND(
            NOT(EQ(A(V("g"), "vocab_checked"), L(1.0))),
            NOT(EQ(A(V("g"), "proposed_seam"), L(None))),
            NOT(_vocab_held()),
            EXISTS(NOT_("SeamAlias"), "a",
                   EQ(A(V("a"), "token"), A(V("g"), "proposed_seam"))),
        ),
        "effects": [
            ["set_attr", "g", "sig_seam", T(A(alias, "alias_of"))],
            ["set_attr", "g", "vocab_checked", 1.0],
            ["set_attr", "g", "vocab_explained", 1.0],
            ["set_attr", "g", "novelty_bits", 1.0],
        ],
    }


def _r_dim_check_mark():
    return {
        "name": "ag_dim_check_mark",
        "comment": (
            "RESILIENCE MARKER for the DEFERRED rung 3 (infer a new signature "
            "DIMENSION, not a new token in an existing one), copied from "
            "sd_dim_check_mark and required for the same MEASURED reason: the "
            "seed loader drops a rule WHOLESALE the moment any effect references "
            "an unknown Term, so an unlanded rung-3 rule would never install, "
            "dim_checked would NEVER be set, and ag_vocab_mint's guard would be "
            "permanently unsatisfiable -- deadlocking the mint for EVERY goal. "
            "Term-FREE twin: guard identical to the rung-3 rule's own, effect a "
            "plain literal. Deferring rung 3 lowers the closed-vocabulary "
            "ceiling from DIMENSIONS to TOKENS; it does not remove it."),
        "batch": True,
        "match": [["agenda", "has_arc_goal", "g"]],
        "where": AND(
            NOT(EQ(A(V("g"), "vocab_checked"), L(1.0))),
            NOT(EQ(A(V("g"), "dim_checked"), L(1.0))),
            NOT(EQ(A(V("g"), "proposed_seam"), L(None))),
        ),
        "effects": [["set_attr", "g", "dim_checked", 1.0]],
    }


def _mint_eligible():
    return FILT(NOT_("ArcGoal"), "g2",
                AND(NOT(EQ(A(V("g2"), "vocab_explained"), L(1.0))),
                    EQ(A(V("g2"), "dim_checked"), L(1.0)),
                    NOT(EQ(A(V("g2"), "proposed_seam"), L(None))),
                    NOT(EQ(A(V("g2"), "evidence_artifact"), L(None))),
                    NOT(EQ(A(V("g2"), "evidence_path"), L(None))),
                    EQ(COUNT(NEIGH(V("g2"), "vocab_minted")), L(0))))


def _r_vocab_mint():
    return {
        "name": "ag_vocab_mint",
        "comment": (
            "VOCABULARY LADDER RUNG 4 -- MINT (the sd_mint_quantum twin). THREE "
            "BOUNDS, NONE OF THEM A VETO. (1) PROVENANCE: the goal must carry a "
            "non-null evidence_artifact AND evidence_path, so a token can only "
            "be minted if it was QUOTED FROM A MEASURED ARTIFACT. No "
            "measurement, no token. THIS IS THE REAL BOUND -- the vocabulary "
            "grows only as fast as measurement grows -- and it is the "
            "anti-Seam-D guard (a per-task token would need a per-task artifact "
            "path). (2) MINT-ONCE + DEDUP: the vocab_minted edge latch, plus a "
            "(dim, token)-KEYED Not(Exists) rather than sd_mint_generator's "
            "one-per-boot form, plus the pcon_mint Argmin ONE-MINT-PER-PASS "
            "serializer -- without which two unrecognised tokens in one pass "
            "both mint, because effects apply against PRE-EFFECT reads. "
            "(3) NOVELTY IS PRICED, NOT FORBIDDEN: novelty_bits enters ag_select "
            "as -w_mdl*novelty_bits. A goal that needs a new word must OUT-EARN "
            "its novelty. Bumps arc_vocab_epoch so ag_revocab re-arms every "
            "unexplained goal -- the codebook_epoch shape."),
        "batch": True,
        "match": [["agenda", "has_arc_goal", "g"]],
        "where": AND(
            NOT(EQ(A(V("g"), "vocab_explained"), L(1.0))),
            EQ(A(V("g"), "dim_checked"), L(1.0)),
            NOT(EQ(A(V("g"), "dim_explained"), L(1.0))),
            NOT(EQ(A(V("g"), "proposed_seam"), L(None))),
            NOT(EQ(A(V("g"), "evidence_artifact"), L(None))),
            NOT(EQ(A(V("g"), "evidence_path"), L(None))),
            EQ(COUNT(NEIGH(V("g"), "vocab_minted")), L(0)),
            NOT(_vocab_held()),
            EQ(V("g"), ONE_OF(_mint_eligible(), "g3")),
        ),
        "effects": [
            ["add_node", "v", "SignatureVocab", {
                "dim": "sig_seam",
                "token": T(A(V("g"), "proposed_seam")),
                "minted": 1.0,
                "provenance": "arc_goal_mint",
                "evidence_artifact": T(A(V("g"), "evidence_artifact")),
                "evidence_path": T(A(V("g"), "evidence_path")),
            }],
            ["add_edge", "g", "vocab_minted", "v"],
            ["set_attr", "g", "sig_seam", T(A(V("g"), "proposed_seam"))],
            ["set_attr", "g", "vocab_checked", 1.0],
            ["set_attr", "g", "vocab_explained", 1.0],
            ["set_attr", "g", "novelty_bits", 8.0],
            ["set_attr", "agenda", "arc_vocab_epoch",
             T(PLUS(A(V("agenda"), "arc_vocab_epoch"), L(1)))],
        ],
    }


def _r_vocab_refuse():
    return {
        "name": "ag_vocab_refuse",
        "comment": (
            "THE MIRROR of ag_vocab_mint (the sd_dedup_existing pattern): a goal "
            "that reaches the mint point WITHOUT a resolving artifact path is "
            "REFUSED and reaches a TERMINAL status, so it neither re-scans every "
            "tick nor falls through to a 'did not resolve' read-back. Its guard "
            "is ag_vocab_mint's with the provenance items NEGATED, so exactly "
            "one of the pair fires. The refusal is LEGIBLE: the goal keeps "
            "proposed_seam and gains vocab_refused_because, so 'the agent wanted "
            "a word it could not source' is a readable fact and a candidate ASK "
            "region -- not a silent drop."),
        "batch": True,
        "match": [["agenda", "has_arc_goal", "g"]],
        "where": AND(
            NOT(EQ(A(V("g"), "vocab_explained"), L(1.0))),
            EQ(A(V("g"), "dim_checked"), L(1.0)),
            NOT(EQ(A(V("g"), "proposed_seam"), L(None))),
            NOT(EQ(A(V("g"), "status"), L("unsourced"))),
            OR(EQ(A(V("g"), "evidence_artifact"), L(None)),
               EQ(A(V("g"), "evidence_path"), L(None))),
        ),
        "effects": [
            ["set_attr", "g", "vocab_checked", 1.0],
            ["set_attr", "g", "vocab_refused_because",
             "no_measured_artifact_path_for_the_proposed_token"],
            ["set_attr", "g", "status", "unsourced"],
        ],
    }


def _r_revocab():
    return {
        "name": "ag_revocab",
        "comment": (
            "CLOSES THE VOCABULARY LOOP (the sd_redecode twin). A goal whose "
            "decoded_vocab_epoch is behind the agenda's arc_vocab_epoch re-arms "
            "and re-runs the ladder -- a token minted for one goal may be the "
            "EXACT recognition another goal needed, which is the whole point of "
            "a SHARED vocabulary. Clears the flags back to 0 EXPLICITLY, because "
            "this engine has no unset_attr and 0 is falsy for the Not(Eq(_,1)) "
            "guards. Scoped to goals that still have an unexplained "
            "proposed_seam, so a goal whose ladder already terminated is not "
            "churned every epoch (the sd_redecode asymmetry, deliberately NOT "
            "copied). dim_checked IS cleared -- the deferred rung 3 must get a "
            "fresh look once the vocabulary has grown."),
        "batch": True,
        "match": [["agenda", "has_arc_goal", "g"]],
        "where": AND(
            NOT(EQ(A(V("g"), "status"), L("retired"))),
            NOT(EQ(A(V("g"), "proposed_seam"), L(None))),
            NOT(EQ(A(V("g"), "vocab_explained"), L(1.0))),
            # MEASURED HAZARD: `Lt(null, 0.0)` is TRUE in this engine -- a
            # MISSING attr sorts BELOW any number. Read literally, this guard
            # re-armed EVERY never-decoded goal on the very first pass, which
            # cleared `dim_explained` and so ERASED the deferred rung 3's claim
            # before rung 4 looked at it -- an Occam-order violation caused by a
            # null, not by a rule. Coalescing to 0.0 says what was meant: re-arm
            # only when the vocabulary has GROWN since this goal last decoded.
            LT(ITE(EQ(A(V("g"), "decoded_vocab_epoch"), L(None)), L(0.0),
                   A(V("g"), "decoded_vocab_epoch")),
               A(V("agenda"), "arc_vocab_epoch")),
        ),
        "effects": [
            ["set_attr", "g", "decoded_vocab_epoch",
             T(A(V("agenda"), "arc_vocab_epoch"))],
            ["set_attr", "g", "vocab_checked", 0.0],
            ["set_attr", "g", "vocab_explained", 0.0],
            ["set_attr", "g", "dim_checked", 0.0],
            ["set_attr", "g", "dim_explained", 0.0],
        ],
    }


# ---- AG-2: the collapse ------------------------------------------------- #
def _r_select():
    return {
        "name": "ag_select",
        "comment": (
            "AG-2, THE ARC-GRAIN WEIGHTED COLLAPSE. ps_move_select's RULE FORM "
            "at gap_priority's GRAIN, stated as a NEW selector rather than "
            "pretending otherwise. Argmax over every ArcGoal on the agenda that "
            "is BOTH un-terminal AND has strictly positive headroom (the "
            "earns-its-keep gate, ps_move_select's gap>0 twin), by "
            "value = w_headroom*headroom_n*reach_class_factor "
            "- w_residual*PENALTY(g) - w_mdl*novelty_bits - w_cost*cost_bits "
            "- w_unsignatured*[no sig_seam]. "
            "THE POOL/WEIGHT LINE IS THE WHOLE DESIGN: retirement and headroom>0 "
            "are Filter predicates; EVERY PIECE OF EVIDENCE (residual penalty, "
            "novelty price, illegibility cost) is inside the Argmax VALUE and "
            "appears in NO where and in NO Argmax source. That is the difference "
            "between a weight and a veto, made STRUCTURAL rather than promised. "
            "VALUE USES ABSOLUTE HEADROOM (denominator_n - honest_n, IN TASKS), "
            "NOT the residual weight's dimensionless ratio: the ratio is right "
            "for a PENALTY (how completely did this fail?) and WRONG as a VALUE, "
            "because it ranks row_verdict (denominator 15) EQUAL TO ir_retarget "
            "(257). PENALTY is gr_move_penalty's own subtree, lifted "
            "programmatically and alpha-renamed -- it is pure attr-equality over "
            "sig_seam/sig_lever/sig_target with residual-side wildcards, it "
            "never reads SignatureVocab and never reads the edge type, so it "
            "transfers to any node carrying sig_* UNCHANGED. But gr_move_penalty "
            "MATCHES ON THE has_move_candidate EDGE, so this rule is its own "
            "TWIN, not a reuse: the goal-residual doc's 'grain-agnostic' claim is "
            "true of the PREDICATE, not of the RULE. Computed INLINE, never read "
            "from an attr, so selection can never depend on whether an audit "
            "stamp has been written yet in the fixpoint."),
        "batch": True,
        "match": HUB,
        "where": AND(
            EXISTS(POOL(), "ggx", L(True)),
        ),
        "effects": [
            ["set_attr", "agenda", "arc_sel_agid", T(A(WINNER, "agid"))],
            ["set_attr", "agenda", "arc_sel_value",
             T(MAXOVER(POOL(), "g2", VALUE(V("g2")), None))],
        ],
    }


def _r_select_audit():
    return {
        "name": "ag_select_audit",
        "comment": (
            "THE AUDIT STAMP -- the ps_move_sel_* shape, so the selection is "
            "READABLE. Binds the winner by its own stamped agid rather than "
            "re-deriving it, which is both the cheap form and the honest one: "
            "if this rule and ag_select ever disagreed about who won, the "
            "audit would be describing a different ranking from the one that "
            "fired (the ps_move_select five-expression precedent, inverted -- "
            "there the SAME Argmax is substituted into every expression; here "
            "the winner is named ONCE and every stamp reads that name). "
            "arc_sel_residual_penalty is the lifted PENALTY evaluated on the "
            "WINNER: a non-zero value here is the visible proof that a charged "
            "goal can still win, which is what makes the residual a weight and "
            "not a veto."),
        "batch": True,
        "match": HUB + [["agenda", "has_arc_goal", "g"]],
        "where": AND(
            EQ(A(V("g"), "agid"), A(V("agenda"), "arc_sel_agid")),
        ),
        "effects": [
            ["set_attr", "agenda", "arc_sel_residual_penalty",
             T(PENALTY(V("g")))],
            ["set_attr", "agenda", "arc_sel_headroom_n",
             T(A(V("g"), "headroom_n"))],
            ["set_attr", "agenda", "arc_sel_denominator_n",
             T(A(V("g"), "denominator_n"))],
            ["set_attr", "agenda", "arc_sel_source_kind",
             T(A(V("g"), "source_kind"))],
        ],
    }


def _r_select_runner_up():
    return {
        "name": "ag_select_runner_up",
        "comment": (
            "THE MARGIN, which AG-4's T1 trigger is defined in terms of. Split "
            "out of ag_select for TWO reasons, both real. (1) SIZE: deriving the "
            "winner inside the runner-up's own pool predicate embeds the whole "
            "PENALTY subtree once per use and evaluates it once per pool "
            "element -- it took the emitted seed to 2.4 MB. Excluding the winner "
            "by its STAMPED agid is the same set, computed once. (2) ORDER: this "
            "engine has NO rule ordering, so the dependency ag_select -> "
            "ag_select_runner_up -> ag_ask has to be a GUARD CHAIN, and a guard "
            "that reads arc_sel_agid is that chain made explicit rather than "
            "hoped for. The margin is the ONLY thing AG-4 needs from the "
            "ranking, and it is stamped, so ag_ask never re-ranks."),
        "batch": True,
        "match": HUB,
        "where": AND(
            NOT(EQ(A(V("agenda"), "arc_sel_agid"), L(None))),
            EXISTS(FILT(POOL_AS("g6"), "g7",
                        NOT(EQ(A(V("g7"), "agid"),
                               A(V("agenda"), "arc_sel_agid")))),
                   "g8", L(True)),
        ),
        "effects": [
            ["set_attr", "agenda", "arc_sel_runner_up_agid",
             T(A(RUNNER_UP(), "agid"))],
        ],
    }


def _r_select_margin():
    return {
        "name": "ag_select_margin",
        "comment": (
            "THE MARGIN ITSELF, with the runner-up bound by its stamped agid. "
            "Same reason as ag_select_audit: substituting the runner-up's whole "
            "Argmax into every slot of VALUE embeds the PENALTY subtree six "
            "times over and re-evaluates it per pool element. AG-4's T1 reads "
            "THIS number, and nothing else re-ranks."),
        "batch": True,
        "match": HUB + [["agenda", "has_arc_goal", "h"]],
        "where": AND(
            EQ(A(V("h"), "agid"), A(V("agenda"), "arc_sel_runner_up_agid")),
        ),
        "effects": [
            ["set_attr", "agenda", "arc_sel_runner_up_value",
             T(VALUE(V("h")))],
            ["set_attr", "agenda", "arc_sel_margin",
             T(MINUS(A(V("agenda"), "arc_sel_value"), VALUE(V("h"))))],
        ],
    }


# ---- AG-4: the ask ------------------------------------------------------ #
def _r_ask():
    tie = LT(A(V("agenda"), "arc_sel_margin"), ASKPOL("margin_threshold"))
    return {
        "name": "ag_ask",
        "comment": (
            "AG-4. THE ASK IS A CANDIDATE IN THE SAME COLLAPSE, NOT A GATE. This "
            "arc's own plan records the theorem: 'excluding a candidate yields "
            "ZERO BITS (Mitchell; Angluin's L*)'. An approve/deny gate is "
            "structurally a rejection with no counterexample -- ~1 bit and no "
            "reason. A QUESTION is the request for the counterexample. "
            "TRIGGER, all live graph reads: T1 the top two values are within "
            "ArcAskPolicy.margin_threshold (cascade_pick's Lt(margin,threshold) "
            "shape); T2 -- THE ONE THAT MATTERS -- Not(Exists(matching non-stale "
            "GoalResidual)) for BOTH tied candidates, i.e. IGNORANCE, NOT "
            "REFUTATION. Tied under refutation the evidence is already held and "
            "a human answer would be WEAKER than the ceiling on the node, so DO "
            "NOT ASK; tied under ignorance nothing is held either way, so ASK. "
            "That distinction is the SAME Exists term gr_move_penalty computes, "
            "NEGATED, so it costs nothing new. RATE BOUND: one open ArcQuestion "
            "per region per measurement epoch -- re-entry gated on NEW "
            "MEASUREMENT, never on graph churn (the codebook_epoch form). "
            "THE ASK NEVER BLOCKS A MINT: it writes no goal attr and touches no "
            "vocabulary guard; blocking is what makes a gate."),
        "batch": True,
        "match": HUB + [["agenda", "has_arc_goal", "g"],
                        ["agenda", "has_arc_goal", "h"]],
        "where": AND(
            # THE TWO TIED CANDIDATES, BOUND BY ag_select's OWN STAMPS -- the
            # ask never re-ranks, so it can never disagree with the collapse it
            # is asking about.
            EQ(A(V("g"), "agid"), A(V("agenda"), "arc_sel_agid")),
            EQ(A(V("h"), "agid"), A(V("agenda"), "arc_sel_runner_up_agid")),
            tie,
            NOT(EXISTS_MATCH(V("g"))),
            NOT(EXISTS_MATCH(V("h"))),
            NOT(EXISTS(NOT_("ArcQuestion"), "q0",
                       AND(EQ(A(V("q0"), "region"), REGION(V("g"))),
                           EQ(A(V("q0"), "asked_epoch"), MEASURE_EPOCH())))),
        ),
        "effects": [
            ["add_node", "q", "ArcQuestion", {
                "region": T(REGION(V("g"))),
                "region_seam": T(A(V("g"), "sig_seam")),
                "region_lever": T(A(V("g"), "sig_lever")),
                "region_target": T(A(V("g"), "sig_target")),
                "agid_a": T(A(V("g"), "agid")),
                "agid_b": T(A(V("h"), "agid")),
                "asked_epoch": T(MEASURE_EPOCH()),
                "answered": 0.0,
                "status": "open",
            }],
            ["add_edge", "q", "asked_about", "g"],
            ["add_node", "reply", "Message", {
                "from": "agent",
                "kind": "arc_question",
                "text": T(SCAT(
                    L("I hold two arc goals I cannot separate. (A) "),
                    A(V("g"), "agid"),
                    L(" -- headroom "),
                    STR(A(V("g"), "headroom_n")),
                    L(" of "),
                    STR(A(V("g"), "denominator_n")),
                    L(" tasks. (B) "),
                    A(V("h"), "agid"),
                    L(" -- headroom "),
                    STR(A(V("h"), "headroom_n")),
                    L(" of "),
                    STR(A(V("h"), "denominator_n")),
                    L(" tasks. Their values differ by only "),
                    STR(A(V("agenda"), "arc_sel_margin")),
                    L(". I hold NO non-stale measurement covering either, so I "
                      "am not re-litigating a ceiling -- I do not know. "
                      "What would have to change for one of these to be worth "
                      "trying? Name a checkable condition, so your answer can "
                      "lapse when its reason does."),
                )),
            }],
            ["add_edge", "agenda", "sent", "reply"],
            ["add_edge", "q", "answered_by", "reply"],
        ],
    }


def _testimony_residual(gvar="q"):
    return {
        "rid": T(SCAT(L("arc.testimony."), A(V(gvar), "region"))),
        "sig_seam": T(A(V(gvar), "region_seam")),
        "sig_lever": T(A(V(gvar), "region_lever")),
        "sig_target": T(A(V(gvar), "region_target")),
        "evidence_kind": "utterance",
        "reach_class": "testimony",
        "reach_class_factor": T(TESTPOL("factor")),
        "ceiling_honest_n": 0.0,
        "denominator_n": 1.0,
        "weight": T(TIMES(TESTPOL("scale"), TESTPOL("factor"))),
        "weight_formula": "TestimonyPolicy.scale * TestimonyPolicy.factor "
                          "(AUTHORED -- testimony is not measurement)",
        "stale": 0.0,
        "_never_parsed": (
            "sig_* come from the QUESTION's region, never from the reply text. "
            "A string-derived signature is Seam C at arc grain."),
    }


def _reply_guard(conditioned):
    base = [
        EQ({"type": "TypeOf", "node": V("q")}, L("ArcQuestion")),
        NOT(EQ(A(V("q"), "answered"), L(1.0))),
        NOT(EQ(A(V("m"), "from"), L("agent"))),
    ]
    if conditioned:
        base.append(NOT(EQ(A(V("m"), "cond_kind"), L(None))))
    else:
        base.append(EQ(A(V("m"), "cond_kind"), L(None)))
    return AND(*base)


def _r_reply_conditioned():
    return {
        "name": "ag_reply_mints_testimony_conditioned",
        "comment": (
            "THE REPLY IS EVIDENCE, NOT SCRIPTURE. An interlocutor Message "
            "responding to an ArcQuestion mints a GoalResidual -- THE SAME NODE "
            "TYPE AS THE SIX MEASURED CEILINGS -- with evidence_kind='utterance' "
            "and a holds_under edge to a ResidualCondition, so gr_condition_lapse "
            "/ gr_condition_hold apply VERBATIM and ZERO NEW LAPSE MACHINERY "
            "EXISTS. Two things differ from a measured residual, both honest: "
            "the weight uses TestimonyPolicy.factor in place of "
            "reach_class_factor (testimony is not measurement, declared "
            "authored); and this branch is the one where THE REPLY NAMED A "
            "CHECKABLE REASON -- one of the three existing ckinds -- so that "
            "becomes the condition and the answer survives until its reason is "
            "falsified. The reply's structured condition fields are written by "
            "the world adapter as MECHANICAL TRANSLATION of an external form "
            "(the comp_topic precedent); the reply text is never parsed into a "
            "signature."),
        "batch": True,
        "match": [["m", "responds_to", "q"]],
        "where": _reply_guard(True),
        "effects": [
            ["add_node", "tr", "GoalResidual", _testimony_residual()],
            ["add_node", "cond", "ResidualCondition", {
                "rid": T(SCAT(L("arc.testimony."), A(V("q"), "region"))),
                "ckind": T(A(V("m"), "cond_kind")),
                "filter_value": T(A(V("m"), "cond_filter_value")),
                "expected_str": T(A(V("m"), "cond_expected_str")),
                "expected": T(A(V("m"), "cond_expected")),
                "why": "named by the reply -- a reason that can be falsified",
            }],
            ["add_edge", "tr", "holds_under", "cond"],
            ["add_edge", "q", "answered_by", "m"],
            ["set_attr", "q", "answered", 1.0],
            ["set_attr", "q", "status", "answered_conditioned"],
        ],
    }


def _r_reply_unconditioned():
    return {
        "name": "ag_reply_mints_testimony_unconditioned",
        "comment": (
            "THE DEFAULT CONDITION, AND IT IS THE POINT. A reply that names no "
            "checkable reason gets fact_equals(arc_measure_epoch == <epoch at "
            "reply>) -- SO IT EXPIRES AT THE NEXT MEASUREMENT EPOCH. That is "
            "Angluin's zero-bits result made mechanical: an answer with no "
            "counterexample carries ~0 bits and lasts one epoch; an answer "
            "carrying a reason persists until its reason is falsified. It is "
            "also the goal-residual doc's own rule -- 'a residual that cannot "
            "lapse is a lie with a long half-life' -- applied to the ONE source "
            "of residuals that has never been subject to it. The epoch is read "
            "as the STRING the ResidualFact stores, so the existing fact_equals "
            "branch of gr_condition_lapse consumes it unmodified. Guard is the "
            "conditioned rule's with the cond_kind item NEGATED, so exactly one "
            "of the pair fires."),
        "batch": True,
        "match": [["m", "responds_to", "q"]],
        "where": _reply_guard(False),
        "effects": [
            ["add_node", "tr", "GoalResidual", _testimony_residual()],
            ["add_node", "cond", "ResidualCondition", {
                "rid": T(SCAT(L("arc.testimony."), A(V("q"), "region"))),
                "ckind": "fact_equals",
                "filter_value": "arc_measure_epoch",
                "expected_str": T(MEASURE_EPOCH()),
                "why": ("the reply named no checkable reason, so it expires at "
                        "the next measurement epoch -- an unconditioned answer "
                        "is worth one epoch."),
            }],
            ["add_edge", "tr", "holds_under", "cond"],
            ["add_edge", "q", "answered_by", "m"],
            ["set_attr", "q", "answered", 1.0],
            ["set_attr", "q", "status", "answered_unconditioned"],
        ],
    }


def _r_question_retire():
    return {
        "name": "ag_question_retire",
        "comment": (
            "An UNANSWERED question must retire (the note_experiments_exhausted "
            "/ elaboration_exhausted pattern) so it neither blocks nor "
            "accumulates -- and an unanswered question is itself DATA: it says "
            "the loop ran without input. Retirement is by MEASUREMENT EPOCH, not "
            "by tick count, so it is monotone in information rather than in "
            "time."),
        "batch": True,
        "match": [["q", "asked_about", "g"]],
        "where": AND(
            NOT(EQ(A(V("q"), "answered"), L(1.0))),
            EQ(A(V("q"), "status"), L("open")),
            NOT(EQ(A(V("q"), "asked_epoch"), MEASURE_EPOCH())),
        ),
        "effects": [
            ["set_attr", "q", "status", "unanswered_lapsed"],
        ],
    }


def _rules():
    return [
        _r_mint_remeasure(),
        _r_remeasure_retire(),
        _r_mint_blocker(),
        _r_mint_source_claim(),
        _r_mint_self_concern(),
        _r_vocab_recognize(),
        _r_vocab_alias(),
        _r_dim_check_mark(),
        _r_vocab_mint(),
        _r_vocab_refuse(),
        _r_revocab(),
        _r_select(),
        _r_select_audit(),
        _r_select_runner_up(),
        _r_select_margin(),
        _r_ask(),
        _r_reply_conditioned(),
        _r_reply_unconditioned(),
        _r_question_retire(),
    ]


def build():
    return {
        "_GENERATED_BY": "tools/build_arc_goals_seed.py",
        "_REGENERATION_IS_GATED_BYTE_IDENTICAL": (
            "tests/test_arc_goals_migrated.py::test_ag6_the_seed_regenerates_"
            "byte_identically re-runs this builder and diffs. The PENALTY "
            "subtree is LIFTED from seeds/goal_residuals.json at build time, so "
            "if gr_move_penalty ever changes this seed goes out of date LOUDLY "
            "instead of silently diverging from the rule it claims to copy."),
        "self_load_only": True,
        "_SELF_LOAD_ONLY_RATIONALE": (
            "substrate/boot_all.py::_read_seeds GLOBS seeds/*.json and installs "
            "every match at boot -- so a file here is live in EVERY agent in the "
            "tree the moment it lands, and phase 2 is not a tree-wide-sweep rung. "
            "`self_load_only` is honoured by _read_seeds (it skips the manifest) "
            "while seed_loader.manifest_for reads it by path, so the seed is "
            "SELF-LOADED by whoever asks for it. This is the design's own §11 "
            "'safer for a first landing' route (the "
            "reading_collapse::_ensure_role_decode_loop precedent), chosen "
            "deliberately over the registry edit. REMOVING THIS KEY IS THE "
            "TREE-WIDE ACTIVATION and needs the paired sweep A5 requires."),
        "id": "arc_goals",
        "version": "1.0.0",
        "depends_on": ["goal_residuals"],
        "description": (
            "ARC-GRAIN GOALS AS GRAPH DATA -- the positive to "
            "seeds/goal_residuals.json's negative. The six GoalResiduals hold "
            "arc-6's measured refutations; nothing in this tree held an OPEN "
            "goal above one task, so the residuals had nothing to steer and were "
            "inert BY CONSTRUCTION (results/arc6_goal_residuals.json -> "
            "GR1_collapse_live.unsignatured_candidates == {A: 0.0, B: 0.0}). "
            "This seed mints ArcGoal nodes from MEASURED sources (a STALE "
            "ceiling; a residual's MEASURED BLOCKER SPLIT; the four claims with "
            "no measured source; the agent's own SelfConcerns), extends the "
            "closed sig_seam vocabulary by the sd loop's own Occam ladder, ranks "
            "them in a weighted collapse whose value is ABSOLUTE HEADROOM IN "
            "TASKS, and ASKS -- under ignorance, never under refutation -- when "
            "the collapse is underdetermined. Every decision is a Rule or a "
            "Term. AG-5 (the executor: winner -> run -> artifact -> re-ingest -> "
            "epoch bump) is DELIBERATELY NOT HERE: without it this is a planning "
            "layer with no hands, and that is said rather than implied."),
        "microtheory": {
            "name": "arc_goal_minting",
            "description": (
                "Arc planning as graph data. A ceiling that has gone stale is a "
                "re-measurement goal; a measured blocker is a supply-the-blocker "
                "goal; an unrecognised blocker name is a vocabulary mint. A "
                "refutation the agent holds is a WEIGHT on the goal, never a "
                "veto -- pursuing an unreachable goal is how residuals get made; "
                "being confidently wrong where the residual is already held is "
                "not."),
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
            print("seeds/arc_goals.json is OUT OF DATE", file=sys.stderr)
            return 1
        print("seeds/arc_goals.json is up to date")
        return 0
    with open(OUT, "w") as fh:
        fh.write(text)
    print("wrote", OUT, "(%d bytes)" % len(text))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
