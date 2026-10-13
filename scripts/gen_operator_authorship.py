#!/usr/bin/env python3
"""Emit seeds/operator_authorship.json (plan P5, 2026-10-10): OPERATOR
AUTHORSHIP -- the agent proposes, judges and installs its own variation
families.

The agent proposes NEW variation families by bounded mutation of the families
it holds as Programs (seeds/family_programs.json). The grammar is data:

  * OperatorAuthorshipPolicy -- enabled, propose_only, k_fix, harm_weight,
    min_gain, max_candidates, max_size, bank_max_quality, and the probation
    knobs (priority_offset, probation_trials, probation_min_rate);
  * FamilyMutation{program, site, values} -- a parameter site of a held
    FamilyProgram (its `parameter_sites` attr names the path) and the values
    the proposer may set it to. A candidate is a set of (site, value) edits on
    one program, applied with the engine's EditAt, enumerated in MDL order
    (fewest edits first) by domains/operator_authorship.py. A REFINEMENT
    (v1.1.0) adds `p_exclude_sources`: the source rules whose own deltas did
    net harm on the bank -- the family is changed where it does harm rather
    than rejected whole.

Meta-evaluation (mechanical, domains/operator_authorship.py +
evaluation/substrate_capability/operator_authorship_meta_v2.py): each
candidate builds its deltas for every bank turn, each delta is replayed by the
conversation child (judge v2) with the bank turns flagged, and the
measurements land on a FamilyProposal node. The rules below DECIDE.

v1.1.0 (2026-10-10, P5b -- the human decision): installation is allowed, and
the criterion is RELATIVE, not absolute. Nothing is protected by a zero:
  * net = fixed - harm_weight * harm;
  * a candidate qualifies when it fixes at least k_fix bank turns, its net is
    positive, and it improves on the held family it was derived from by at
    least min_gain (net - parent_net) -- a better tradeoff than its parent,
    not a harm-free one;
  * the best qualifying candidate per program (highest net, then MDL rank) is
    INSTALLED by a rule: a FamilyProgram holding its edited Term and a
    VariationOp{provenance:'agent_authored', probation:1} with its parent's
    family, cue heads and concern kind, at the parent's priority minus
    priority_offset -- it measured the better tradeoff, so it is tried first
    and the parent remains the fallback;
  * the harm it still does is not hidden: every turn it harmed on the bank,
    and every bank turn left to a source it excludes, is filed as a
    SelfConcern{kind:'family_residual'} -- the residual is moved, not erased;
  * on probation the family is judged by its own L0 trials: after
    probation_trials judged experiments, a support rate below
    probation_min_rate retires it (cue_head 'retired', so variation_pick no
    longer sees it and the parent takes over); at or above it, it graduates
    (probation 0).

This seed is frozen (substrate/boot_all._FROZEN_SEED_IDS) and its node types
are protected (seeds/improvement_integrity.json): a delta cannot install or
edit a family; only these rules can, and only on measured proposals. That is
the narrow exception recorded on ImprovementIntegrity.authorship_exception.
Idempotent.
"""
import json
from pathlib import Path

P = Path(__file__).resolve().parents[1] / "seeds/operator_authorship.json"


def V(n): return {"type": "Var", "name": n}
def L(v): return {"type": "Lit", "value": v}
def A(n, k): return {"type": "Attr", "node": V(n) if isinstance(n, str) else n, "key": k}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def Gt(a, b): return {"type": "Gt", "a": a, "b": b}
def Gte(a, b): return {"type": "Gte", "a": a, "b": b}
def Lt(a, b): return {"type": "Lt", "a": a, "b": b}
def Not(x): return {"type": "Not", "arg": x}
def And(*xs): return {"type": "And", "items": list(xs)}
def Or(*xs): return {"type": "Or", "items": list(xs)}
def NN(x): return Not(Eq(x, L(None)))
def Minus(a, b): return {"type": "Minus", "a": a, "b": b}
def Plus(*xs): return {"type": "Plus", "items": list(xs)}
def Times(*xs): return {"type": "Times", "items": list(xs)}
def Div(a, b): return {"type": "Div", "a": a, "b": b}
def Count(s): return {"type": "Count", "source": s}
def Nodes(t): return {"type": "NodesOfType", "node_type": t}
def Filter(src, var, pred): return {"type": "Filter", "source": src, "var_name": var, "predicate": pred}
def Exists(src, var, pred): return {"type": "Exists", "source": src, "var_name": var, "predicate": pred}
def First(t, var, pred): return {"type": "Argmin", "source": Filter(Nodes(t), var, pred), "var_name": "_x",
                                 "value": L(0), "default": None}
def InNb(n, e): return {"type": "InNeighbours", "node": n, "edge_type": e}
def T(term): return {"__term__": term}
def SC(*parts): return {"type": "StringConcat", "parts": [L(x) if isinstance(x, str) else x for x in parts]}


MATCH = [["agent", "has_operator_authorship_policy", "pol"], ["pol", "has_family_proposal", "p"]]
MEASURED = Eq(A("p", "status"), L("measured"))
UNDECIDED = And(MEASURED, Eq(A("p", "verdict"), L(None)), NN(A("p", "net")))
# the held proposal of the same program on the same bank set: the parent
PARENT_P = First("FamilyProposal", "q", And(Eq(A("q", "program"), A("p", "program")), Eq(A("q", "size"), L(0)),
                                            Eq(A("q", "bank_set"), A("p", "bank_set"))))
PARENT_NET = A(PARENT_P, "net")
GAIN = Minus(A("p", "net"), PARENT_NET)
QUALIFIES = And(Gte(A("p", "fixed"), A("pol", "k_fix")), Gt(A("p", "net"), L(0)),
                Gte(GAIN, A("pol", "min_gain")))
# the parent VariationOp (by name) the authored op inherits its wiring from
PARENT_OP = First("VariationOp", "v", Eq(A("v", "name"), A("p", "parent_op")))
OTHER_BETTER = Exists(Nodes("FamilyProposal"), "o", And(
    Eq(A("o", "verdict"), L("qualifies")), Eq(A("o", "program"), A("p", "program")),
    Eq(A("o", "bank_set"), A("p", "bank_set")),
    Or(Gt(A("o", "net"), A("p", "net")),
       And(Eq(A("o", "net"), A("p", "net")), Lt(A("o", "mdl_rank"), A("p", "mdl_rank"))))))


def judged(op, outcomes):
    """Count of this op's SeedDeltas whose Experiment was judged one of `outcomes`."""
    return Count(Filter(Nodes("SeedDelta"), "d", And(
        Eq(A("d", "variation_op"), A(op, "name")),
        Exists(InNb(V("d"), "has_delta"), "x", {"type": "In", "member": A("x", "outcome"),
                                                "container": L(outcomes)}))))


TRIALS = judged("op", ["supported", "refuted", "inconclusive"])
SUPPORTS = judged("op", ["supported"])
PROBATION_DUE = And(Eq(A("op", "probation"), L(1)), Not(Eq(A("op", "retired"), L(1))),
                    Gte(TRIALS, A("pol", "probation_trials")))
RATE = Div(Times(SUPPORTS, L(1.0)), TRIALS)

rules = [
    {"name": "family_proposal_net",
     "comment": "v1.1.0: net = fixed - harm_weight * harm. Harm is a cost to weigh, not a veto.",
     "match": MATCH,
     "where": And(MEASURED, Eq(A("p", "net"), L(None))),
     "effects": [["set_attr", "p", "net", T(Minus(A("p", "fixed"), Times(A("p", "harm"), A("pol", "harm_weight"))))]]},
    {"name": "family_proposal_held_baseline",
     "comment": "A size-0 candidate is a held family, measured on the same banks: the parent a candidate must beat.",
     "match": MATCH,
     "where": And(UNDECIDED, Eq(A("p", "size"), L(0))),
     "effects": [["set_attr", "p", "verdict", "held_baseline"]]},
    {"name": "family_proposal_qualifies",
     "comment": "v1.1.0, relative: >= k_fix fixes, positive net, and a net at least min_gain above the parent's.",
     "match": MATCH,
     "where": And(UNDECIDED, Gt(A("p", "size"), L(0)), Eq(A("pol", "enabled"), L(1)), NN(PARENT_NET), QUALIFIES),
     "effects": [["set_attr", "p", "verdict", "qualifies"], ["set_attr", "p", "qualifies", 1],
                 ["set_attr", "p", "gain", T(GAIN)]]},
    {"name": "family_proposal_does_not_qualify",
     "comment": "Too few fixes, a non-positive net, or no better a tradeoff than the parent.",
     "match": MATCH,
     "where": And(UNDECIDED, Gt(A("p", "size"), L(0)), NN(PARENT_NET), Not(QUALIFIES)),
     "effects": [["set_attr", "p", "verdict", "does_not_qualify"], ["set_attr", "p", "qualifies", 0],
                 ["set_attr", "p", "gain", T(GAIN)]]},
    {"name": "family_proposal_propose_only",
     "comment": "While the policy is propose-only, a qualifying proposal is recorded and not installed.",
     "match": MATCH,
     "where": And(Eq(A("p", "verdict"), L("qualifies")), Eq(A("pol", "propose_only"), L(1)),
                  Not(Eq(A("p", "install_blocked"), L(1)))),
     "effects": [["set_attr", "p", "install_blocked", 1],
                 ["set_attr", "p", "install_blocked_reason", "the operator-authorship policy is propose-only"]]},
    {"name": "family_proposal_install",
     "comment": "v1.1.0: the best qualifying candidate of a program (highest net, then MDL rank) is installed as a "
                "FamilyProgram + VariationOp on probation, wired as its parent family.",
     "match": MATCH,
     "where": And(Eq(A("p", "verdict"), L("qualifies")), Eq(A("pol", "propose_only"), L(0)),
                  Eq(A("pol", "enabled"), L(1)), Not(Eq(A("p", "installed"), L(1))), Not(OTHER_BETTER),
                  NN(PARENT_OP), NN(A("p", "program_json")),
                  Not(Exists(Nodes("VariationOp"), "w", Eq(A("w", "name"), A("p", "op_name"))))),
     "effects": [
         ["add_node", "fp", "FamilyProgram", {
             "name": T(A("p", "family_name")), "program": T(A("p", "program_json")),
             "parameter_sites": T(A(First("FamilyProgram", "f", Eq(A("f", "name"), A("p", "program"))),
                                    "parameter_sites")),
             "kind": "variation_family_builder", "provenance": "agent_authored",
             "parent_program": T(A("p", "program")), "edits": T(A("p", "edits")),
             "description": T(SC("agent-authored (operator_authorship): ", A("p", "program"), " with ",
                                 A("p", "edits")))}],
         ["add_node", "op", "VariationOp", {
             "name": T(A("p", "op_name")), "builder_program": T(A("p", "family_name")),
             "family": T(A(PARENT_OP, "family")),
             # relative: it measured a better tradeoff than its parent on the same banks, so it is tried
             # first; the parent stays as the fallback, and its own trials can retire it
             "priority": T(Minus(A(PARENT_OP, "priority"), A("pol", "priority_offset"))),
             "cue_head": T(A(PARENT_OP, "cue_head")), "also_head": T(A(PARENT_OP, "also_head")),
             "requires_kind": T(A(PARENT_OP, "requires_kind")),
             "keywords_text": T(A(PARENT_OP, "keywords_text")),
             "provenance": "agent_authored", "probation": 1, "parent_op": T(A("p", "parent_op"))}],
         ["add_edge", "p", "installed_as", "op"],
         ["add_edge", "p", "installed_program", "fp"],
         ["add_edge", "pol", "installed_family", "op"],
         ["set_attr", "p", "installed", 1]]},
    {"name": "family_proposal_files_residual",
     "comment": "v1.1.0: what an installed family still harms, or leaves to a source it excludes, is filed as the "
                "agent's own concern -- the residual moves elsewhere; it is not erased.",
     "match": MATCH + [["p", "residual_turn", "m"]],
     "where": And(Eq(A("p", "installed"), L(1)),
                  Not(Exists(InNb(V("m"), "about_message"), "c", And(
                      Eq(A("c", "kind"), L("family_residual")), Eq(A("c", "family"), A("p", "op_name")))))),
     "effects": [
         ["add_node", "rc", "SelfConcern", {
             "status": "noted", "source": "operator_authorship", "kind": "family_residual",
             "family": T(A("p", "op_name")),
             "content": T(SC("the authored family ", A("p", "op_name"),
                             " trades this turn away (harmed or excluded on its bank)"))}],
         ["add_edge", "agent", "has_self_concern", "rc"],
         ["add_edge", "rc", "about_message", "m"]]},
    {"name": "authored_family_retires_on_credit",
     "comment": "v1.1.0: on probation, a family whose own judged trials support at a rate below probation_min_rate "
                "is retired (variation_pick never selects cue_head 'retired').",
     "match": [["agent", "has_operator_authorship_policy", "pol"], ["pol", "installed_family", "op"]],
     "where": And(PROBATION_DUE, Lt(RATE, A("pol", "probation_min_rate"))),
     "effects": [["set_attr", "op", "retired", 1], ["set_attr", "op", "retired_cue_head", T(A("op", "cue_head"))],
                 ["set_attr", "op", "cue_head", "retired"],
                 ["set_attr", "op", "retired_reason",
                  T(SC("probation: support rate below the policy's minimum over its judged trials"))]]},
    {"name": "authored_family_graduates_on_credit",
     "comment": "v1.1.0: at or above the rate over its judged trials it leaves probation.",
     "match": [["agent", "has_operator_authorship_policy", "pol"], ["pol", "installed_family", "op"]],
     "where": And(PROBATION_DUE, Gte(RATE, A("pol", "probation_min_rate"))),
     "effects": [["set_attr", "op", "probation", 0]]},
]

MUTATIONS = [
    ("family_disposition_generalise", "p_max_miss", [2],
     "relax two guards instead of one"),
    ("family_disposition_generalise", "p_source_role", ["realiser"],
     "choose the source rule by a different criterion: the reply rule that realises the turn's own basis"),
    ("family_deep_reader_correct", "p_held_reply",
     ["reply_to_deferred_typed_response_acknowledgement", "reply_to_blocked_unavailable_action_response"],
     "realise the deep-reader receipt with a different held neutral-receipt reply rule"),
]

nodes = [{"local_id": 0, "type": "OperatorAuthorshipPolicy", "attrs": {
    "name": "operator_authorship", "enabled": 1, "propose_only": 0, "k_fix": 2, "harm_weight": 1.0,
    "min_gain": 1, "max_candidates": 12, "max_size": 2, "bank_max_quality": 0.0, "refine": 1,
    "priority_offset": 0.5, "probation_trials": 3, "probation_min_rate": 0.34,
    "description": "Agent-held policy for authoring variation families (plan P5): the bank, the candidate caps, "
                   "the relative criterion (net = fixed - harm_weight * harm, beating the parent by min_gain), "
                   "and probation. propose_only 0 since the human decision of 2026-10-10."}}]
edges = [{"src": {"role": "agent_root"}, "type": "has_operator_authorship_policy", "tgt": {"local": 0}, "attrs": {}}]
for k, (prog, site, values, why) in enumerate(MUTATIONS, start=1):
    nodes.append({"local_id": k, "type": "FamilyMutation", "attrs": {
        "program": prog, "site": site, "values": json.dumps(values), "description": why}})
    edges.append({"src": {"local": 0}, "type": "has_family_mutation", "tgt": {"local": k}, "attrs": {}})

seed = {
    "id": "operator_authorship",
    "version": "1.1.0",
    "depends_on": [],
    "description": __doc__,
    "nodes": nodes,
    "edges": edges,
    "productions": [],
    "rules": rules,
}
P.write_text(json.dumps(seed, indent=1, ensure_ascii=True) + "\n")
print("operator_authorship", seed["version"], len(MUTATIONS), "mutation sites", len(rules), "rules")
