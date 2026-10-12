#!/usr/bin/env python3
"""WP2 emitter: OUTCOME-CREDITED VARIATION POLICY (improve the improver).

RECURSIVE_SELF_IMPROVEMENT_PLAN_20261006.md WP2.

1. Revises `variation_pick` in seeds/variation_ops.json (v1.5.0). The Program
   reads an OPTIONAL `VariationPolicy` node. With no such node the pick is
   byte-identical to v1.4.0 (Argmin of raw `priority`). With one:
     * `exclude_refuted == 1` -- an op whose experiment for THIS concern key was
       already judged `refuted` is ineligible (first-order: do not retry a
       family that failed on the same problem);
     * `use_credit == 1` -- each op's priority is scaled by its outcome history
       for the concern's KIND: factor = 2*(trials - supports + 1)/(trials + 2)
       (Laplace-smoothed failure odds; 1 with no history, <1 after supports,
       >1 after failures). This is the second-order loop: outcomes of earlier
       improvement attempts change how later improvement attempts are chosen.
2. Emits seeds/variation_credit.json: the VariationPolicy node and two graph
   rules that turn judged Experiments into VariationCredit{op, kind, trials,
   supports} -- trials/supports are DERIVED counts over credited deltas, so
   concurrent firings cannot race.

Credit attribution needs the experiment's delta to carry `variation_op` and
`concern_key`; reflective_faculty._compose_experiment_rule stamps both
mechanically from the Program's verdict.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OPS = ROOT / "seeds/variation_ops.json"
OUT = ROOT / "seeds/variation_credit.json"


def V(n): return {"type": "Var", "name": n}
def A(n, k): return {"type": "Attr", "node": V(n), "key": k}
def L(v): return {"type": "Lit", "value": v}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def Not(a): return {"type": "Not", "arg": a}
def And(*xs): return {"type": "And", "items": list(xs)}
def Or(*xs): return {"type": "Or", "items": list(xs)}
def Ite(c, t, o): return {"type": "IfThenElse", "cond": c, "then": t, "other": o}
def Let(n, v, b): return {"type": "Let", "name": n, "value": v, "body": b}
def first(node_type, var, pred): return {"type": "Argmin", "source": {"type": "Filter", "source": {"type": "NodesOfType", "node_type": node_type}, "var_name": var, "predicate": pred}, "var_name": var, "value": L(0), "default": None}
def T(t): return {"__term__": t}


ELIGIBLE_V14 = None  # filled from the existing Program


def revised_pick(old):
    """Wrap the v1.4.0 body: same Let scnode/kind, same eligibility filter, plus
    policy-gated exclusion and credit scaling."""
    assert old["type"] == "Let" and old["name"] == "scnode"
    kind_let = old["body"]
    assert kind_let["type"] == "Let" and kind_let["name"] == "kind"
    pick = kind_let["body"]                       # Attr(name, Argmin(Filter(VariationOp,...), priority))
    argmin = pick["node"]
    filt = argmin["source"]
    elig = filt["predicate"]
    is_on = lambda key: And(Not(Eq(V("vpolicy"), L(None))), Eq({"type": "Attr", "node": V("vpolicy"), "key": key}, L(1)))
    # A family with its OWN internal retry (VariationOp.retry_internal == 1,
    # e.g. cue_set_edit's route-level exclusion) is excluded only by a refuted
    # trial that carried no internal alternative (no cue_route): while it still
    # proposes untried routes, refuting one route must not drop the family
    # (tranche 5: family-level exclusion pre-empted the next route).
    # v1.14.0 (tranche 11): knob_edit is retry_internal too (its internal
    # alternatives are the other held knobs, excluded per knob by the builder);
    # a trial carried an internal alternative if it named a cue_route OR a knob_attr.
    exhausted = Or(Not(Eq(A("v", "retry_internal"), L(1))),
                   And(Eq(A("rd", "cue_route"), L(None)), Eq(A("rd", "knob_attr"), L(None))))
    refuted_here = {"type": "Exists", "source": {"type": "NodesOfType", "node_type": "SeedDelta"}, "var_name": "rd",
                    "predicate": And(Eq(A("rd", "concern_key"), V("key")),
                                     Eq(A("rd", "variation_op"), A("v", "name")),
                                     Eq(A("rd", "judged_outcome"), L("refuted")),
                                     exhausted)}
    # v1.11.0 (tranche 9, opt-in VariationPolicy.exclude_inconclusive == 1):
    # an inconclusive verdict for THIS concern excludes the family too (same
    # retry_internal exemption) -- the tranche-8 credit-off arm spent every
    # retry on a family that was only ever inconclusive.
    inconclusive_here = {"type": "Exists", "source": {"type": "NodesOfType", "node_type": "SeedDelta"}, "var_name": "rd",
                         "predicate": And(Eq(A("rd", "concern_key"), V("key")),
                                          Eq(A("rd", "variation_op"), A("v", "name")),
                                          Eq(A("rd", "judged_outcome"), L("inconclusive")),
                                          exhausted)}
    abstained_here = {"type": "Exists", "source": {"type": "NodesOfType", "node_type": "SeedDelta"}, "var_name": "rd",
                      "predicate": And(Eq(A("rd", "concern_key"), V("key")),
                                       Eq(A("rd", "variation_op"), A("v", "name")),
                                       Eq(A("rd", "variant_abstained"), L(1.0)))}
    new_filter = dict(filt, predicate=And(elig, Or(Not(is_on("exclude_refuted")), Not(refuted_here)),
                                          Or(Not(is_on("exclude_inconclusive")), Not(inconclusive_here)),
                                          Not(abstained_here)))
    credit = first("VariationCredit", "vc", And(Eq(A("vc", "op"), A("x", "name")), Eq(A("vc", "kind"), V("kind"))))
    # v1.11.0 (tranche 9, opt-in VariationPolicy.credit_internal_exempt == 1):
    # a retry_internal family is not charged, in THIS concern's pick, for its
    # own non-supported trials on this concern that carried an internal
    # alternative (cue_route) -- the family is still working through its
    # internal alternatives (route exclusion), so those trials are not yet
    # evidence that the family fails on the problem. Credit stays per trial
    # for every other concern. (Tranche 8: a refuted comprehend_text route
    # inflated cue_set_edit's factor and the retry left the family before
    # world_action was tried.)
    own_open = {"type": "Count", "source": {"type": "Filter", "source": {"type": "NodesOfType", "node_type": "SeedDelta"},
                "var_name": "od", "predicate": And(Eq(A("od", "concern_key"), V("key")),
                                                   Eq(A("od", "variation_op"), A("x", "name")),
                                                   Eq(A("od", "credited"), L(1)),
                                                   Not(Eq(A("od", "judged_outcome"), L("supported"))),
                                                   Or(Not(Eq(A("od", "cue_route"), L(None))),
                                                      Not(Eq(A("od", "knob_attr"), L(None)))),
                                                   Eq(A("x", "retry_internal"), L(1)))}}
    exempt = Ite(is_on("credit_internal_exempt"), own_open, L(0))
    tr = {"type": "Minus", "a": Ite(Eq(A("vcr", "trials"), L(None)), L(0), A("vcr", "trials")), "b": exempt}
    su = Ite(Eq(A("vcr", "supports"), L(None)), L(0), A("vcr", "supports"))
    factor = Let("vcr", credit, Ite(Eq(V("vcr"), L(None)), L(1.0),
                 {"type": "Div", "a": {"type": "Times", "items": [L(2.0), {"type": "Plus", "items": [{"type": "Minus", "a": tr, "b": su}, L(1.0)]}]},
                  "b": {"type": "Plus", "items": [tr, L(2.0)]}}))
    value = Ite(is_on("use_credit"), {"type": "Times", "items": [A("x", "priority"), factor]}, A("x", "priority"))
    new_argmin = dict(argmin, source=new_filter, value=value)
    new_pick = dict(pick, node=new_argmin)
    policy = first("VariationPolicy", "vp", L(True))
    return dict(old, body=dict(kind_let, body=Let("vpolicy", policy, new_pick)))


KIND = {"type": "Attr", "key": "kind", "node": first("StandingConcern", "sc", Eq(A("sc", "name"), A("delta", "concern_key")))}
KIND_OR_EMPTY = Let("ck", KIND, Ite(Eq(V("ck"), L(None)), L(""), V("ck")))
CREDIT = {
    "name": "vc_credit_judged_experiment",
    "comment": "A judged Experiment (outcome supported/refuted/inconclusive, sequenced after the judge by matching its 'analysed' edge -- see self_optimisation's engine note) whose delta names the variation family that produced it is credited, once, to VariationCredit{op, kind} for the concern's SelfConcern kind. The delta records the verdict it was credited with.",
    "match": [["exp", "has_delta", "delta"], ["exp", "analysed", "run"]],
    "where": And(Not(Eq(A("delta", "variation_op"), L(None))),
                 {"type": "In", "member": A("exp", "outcome"), "container": L(["supported", "refuted", "inconclusive"])},
                 Not(Eq(A("delta", "credited"), L(1)))),
    "effects": [
        ["add_node_if_absent", "cr", "VariationCredit", {"op": T(A("delta", "variation_op")), "kind": T(KIND_OR_EMPTY)}],
        ["add_edge", "delta", "credited_to", "cr"],
        ["set_attr", "delta", "judged_outcome", T(A("exp", "outcome"))],
        ["set_attr", "delta", "credited", 1],
    ],
}
# v1.1.0 RECENCY: each credit is stamped with a global sequence number (the
# count of deltas credited before it), and trials/supports count only the
# last `VariationPolicy.window` credits of that (op, kind). No window attr ->
# all credits (v1.0.0 semantics). A family that stopped working is therefore
# forgotten after `window` fresh trials instead of after its whole history.
SEQ = {"type": "Count", "source": {"type": "Filter", "source": {"type": "NodesOfType", "node_type": "SeedDelta"},
                                   "var_name": "q", "predicate": Eq(A("q", "credited"), L(1))}}
CREDIT["effects"].insert(2, ["set_attr", "delta", "credit_seq", T(SEQ)])
IN_CR = {"type": "InNeighbours", "node": V("cr"), "edge_type": "credited_to"}
WINDOW = {"type": "Attr", "key": "window", "node": first("VariationPolicy", "wp", L(True))}
NEWER = {"type": "Count", "source": {"type": "FilterList", "source": IN_CR, "var_name": "e",
                                     "predicate": {"type": "Gt", "a": A("e", "credit_seq"), "b": A("d", "credit_seq")}}}
IN_WIN = Let("win", WINDOW, {"type": "FilterList", "source": IN_CR, "var_name": "d",
                             "predicate": Or(Eq(V("win"), L(None)), {"type": "Lt", "a": NEWER, "b": V("win")})})
N_TRIALS = {"type": "Count", "source": IN_WIN}
N_SUPPORTS = {"type": "Count", "source": {"type": "FilterList", "source": IN_WIN, "var_name": "s",
                                          "predicate": Eq(A("s", "judged_outcome"), L("supported"))}}
REFRESH = {
    "name": "vc_refresh_credit_counts",
    "comment": "trials/supports are DERIVED from the credited deltas, recomputed when they differ -- idempotent and order-independent.",
    "match": [["delta", "credited_to", "cr"]],
    "where": Or(Not(Eq(A("cr", "trials"), N_TRIALS)), Not(Eq(A("cr", "supports"), N_SUPPORTS))),
    "effects": [["set_attr", "cr", "trials", T(N_TRIALS)], ["set_attr", "cr", "supports", T(N_SUPPORTS)]],
}


# (Tranche 11: emitted into seeds/self_optimisation.json by
# scripts/gen_abstain_close_rule.py, not here -- variation_credit is
# self_load_only, so a rule here would not run on a production boot.)
# An experiment whose delta carries `variant_abstained`
# (the picked builder honestly abstained, so the delta is empty) is closed
# BEFORE dispatch: status 'done', outcome 'abstained'. It is never replayed
# and never credited (vc_credit_judged_experiment only credits
# supported/refuted/inconclusive); the pick excludes the family for this
# concern (variation_ops v1.13.0), so a retry tries another family.
CLOSE_ABSTAINED = {
    "name": "vc_close_abstained_variant",
    "comment": "An empty (abstained) variant is closed without dispatch or credit -- measured tranche 10: 'sort' spent 3 real child replays on empty cue_set_edit deltas.",
    "match": [["exp", "has_delta", "delta"]],
    "where": And(Eq(A("delta", "variant_abstained"), L(1.0)),
                 {"type": "In", "member": A("exp", "status"), "container": L(["requested", "counterfactual_requested"])}),
    "effects": [["set_attr", "exp", "status", "done"], ["set_attr", "exp", "outcome", "abstained"],
                ["set_attr", "delta", "judged_outcome", "abstained"]],
}


BASE_PICK = json.loads(next(n for n in json.load(open(Path(__file__).resolve().parent / "variation_pick_v1_4_base.json"))["nodes"]
                            if n["type"] == "Program" and n["attrs"]["name"] == "variation_pick")["attrs"]["program"])


def main():
    text = OPS.read_text()
    ops = json.loads(text)
    prog_node = next(n for n in ops["nodes"] if n["type"] == "Program" and n["attrs"]["name"] == "variation_pick")
    cur = json.loads(prog_node["attrs"]["program"])
    if True:   # always rebuild the credit wrapper from the stored v1.4.0 base
        cur = BASE_PICK
        prog_node["attrs"]["program"] = json.dumps(revised_pick(cur))
        ops["version"] = max(ops["version"], "1.8.0", key=lambda v: tuple(map(int, v.split("."))))
        for n in ops["nodes"]:
            if n["type"] == "VariationOp" and n["attrs"].get("name") in ("cue_set_edit", "knob_edit"):
                n["attrs"]["retry_internal"] = 1
        ops["version"] = max(ops["version"], "1.11.0", key=lambda v: tuple(map(int, v.split("."))))
        ops["version"] = max(ops["version"], "1.14.0", key=lambda v: tuple(map(int, v.split("."))))
        if "v1.14.0 (2026-10-08" not in ops["description"]:
            ops["description"] += (" v1.14.0 (2026-10-08, tranche 11): knob_edit is retry_internal (its internal alternatives"
                                   " are the other held knobs); a trial naming a knob_attr counts as carrying an internal"
                                   " alternative for exclude_* / credit_internal_exempt, exactly like a cue_route.")
        if "v1.13.0 (2026-10-08" not in ops["description"]:
            ops["description"] += (" v1.13.0 (2026-10-08, tranche 11): a family whose builder abstained for this concern"
                                   " (SeedDelta.variant_abstained) is not picked again for it -- an empty delta is not a trial.")
        if "v1.11.0 (2026-10-08" not in ops["description"]:
            ops["description"] += (" v1.11.0 (2026-10-08, tranche 9): two OPT-IN VariationPolicy attrs."
                                   " exclude_inconclusive==1 also drops a family judged inconclusive for this concern;"
                                   " credit_internal_exempt==1 does not charge a retry_internal family, in this concern's"
                                   " pick, for its own non-supported trials on this concern that carried an internal"
                                   " alternative (cue_route). Absent -> unchanged.")
        if "v1.8.0" not in ops["description"]:
            ops["description"] += (" v1.8.0 (2026-10-07, tranche 5): exclude_refuted spares a retry_internal family"
                                   " (cue_set_edit) while its refuted trials still carried an internal alternative (cue_route).")
        if "v1.5.0 (2026-10-06" not in ops["description"]: ops["description"] += (" v1.5.0 (2026-10-06, RECURSIVE_SELF_IMPROVEMENT_PLAN WP2): variation_pick reads an OPTIONAL"
                               " VariationPolicy node (seeds/variation_credit.json). Absent -> byte-identical choice."
                               " exclude_refuted==1 drops a family already refuted for this concern; use_credit==1 scales"
                               " priority by the family's Laplace-smoothed failure odds 2(t-s+1)/(t+2) for the concern's kind"
                               " (VariationCredit, derived from judged Experiments) -- the improver's choice learns from its own outcomes.")
        OPS.write_text(json.dumps(ops, indent=1, ensure_ascii=False) + ("\n" if text.endswith("\n") else ""))
    seed = {"id": "variation_credit", "version": "1.2.0",
        "self_load_only": True, "depends_on": ["variation_ops"],
            "description": __doc__,
            "nodes": [{"local_id": 0, "type": "VariationPolicy",
                       "attrs": {"name": "outcome_credited_variation", "exclude_refuted": 1, "use_credit": 1,
                                 # v1.2.0 (tranche 10): promoted to default by the preregistered rule in
                                 # SUBSTRATE_VARIATION_CREDIT_REAL_JUDGE_V3_PREREG_20261008.md (G2-G4 held in v2 and v3).
                                 "credit_internal_exempt": 1, "exclude_inconclusive": 1}}],  # window: opt-in; v1.1 panel found window=4 no better at adaptation and worse at retention
            "edges": [],
            "productions": [{"provenance": "seed:variation_credit:credited_to", "src": {"type": "SeedDelta", "var": "delta"},
                             "edge_type": "credited_to", "tgt": {"type": "VariationCredit", "var": "cr"}}],
            "rules": [CREDIT, REFRESH]}
    OUT.write_text(json.dumps(seed, indent=1, ensure_ascii=True) + "\n")
    print("wrote", OUT.relative_to(ROOT), "and", OPS.relative_to(ROOT), ops["version"])


if __name__ == "__main__":
    main()
