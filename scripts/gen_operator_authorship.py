#!/usr/bin/env python3
"""Emit seeds/operator_authorship.json (plan P5, 2026-10-10): OPERATOR
AUTHORSHIP, propose-only.

The agent proposes NEW variation families by bounded mutation of the families
it holds as Programs (seeds/family_programs.json). The grammar is data:

  * OperatorAuthorshipPolicy -- enabled, propose_only, k_fix (concerns a
    candidate must fix), max_candidates, max_size (mutations per candidate),
    bank_max_quality (a held-out turn joins the bank when its production
    ReplyQuality datum is at most this);
  * FamilyMutation{program, site, values} -- a parameter site of a held
    FamilyProgram (its `parameter_sites` attr names the path) and the values
    the proposer may set it to. A candidate is a set of (site, value) edits on
    one program, applied with the engine's EditAt; candidates are enumerated in
    MDL order (fewest edits first) by domains/operator_authorship.py.

Meta-evaluation (mechanical, domains/operator_authorship.py): each candidate
builds its deltas for every bank turn, each delta is replayed by the
conversation child (scripts/convo_child_run.py, judge v2) with the bank turns
flagged, and the measurements are written onto a FamilyProposal node. The
rules below DECIDE: a candidate qualifies only if it fixed at least k_fix bank
turns, did no harm (0 regressions, 0 broken fixes, 0 quality drops in every
replay), and fixed at least one class no held family fixes. Propose-only: a
qualifying proposal is marked install_blocked -- installing an agent-authored
VariationOp needs the narrow improvement_integrity exception, a human
decision (plan P5).

This seed is frozen (substrate/boot_all._FROZEN_SEED_IDS) and its node types
are protected (seeds/improvement_integrity.json), so the loop cannot vary how
a new family is judged. Idempotent.
"""
import json
from pathlib import Path

P = Path(__file__).resolve().parents[1] / "seeds/operator_authorship.json"


def V(n): return {"type": "Var", "name": n}
def L(v): return {"type": "Lit", "value": v}
def A(n, k): return {"type": "Attr", "node": V(n), "key": k}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def Gt(a, b): return {"type": "Gt", "a": a, "b": b}
def Gte(a, b): return {"type": "Gte", "a": a, "b": b}
def Not(x): return {"type": "Not", "arg": x}
def And(*xs): return {"type": "And", "items": list(xs)}
def Or(*xs): return {"type": "Or", "items": list(xs)}


MATCH = [["agent", "has_operator_authorship_policy", "pol"], ["pol", "has_family_proposal", "p"]]
MEASURED = And(Eq(A("p", "status"), L("measured")), Eq(A("p", "verdict"), L(None)))

rules = [
    {"name": "family_proposal_held_baseline",
     "comment": "A size-0 candidate is a held family, measured on the same bank as the baseline for novelty.",
     "match": MATCH,
     "where": And(MEASURED, Eq(A("p", "size"), L(0))),
     "effects": [["set_attr", "p", "verdict", "held_baseline"]]},
    {"name": "family_proposal_qualifies",
     "comment": "Gate A5a's criterion as data: >= k_fix bank turns fixed, zero harm in every replay, and a fixed "
                "class no held family fixes.",
     "match": MATCH,
     "where": And(MEASURED, Gt(A("p", "size"), L(0)), Eq(A("pol", "enabled"), L(1)),
                  Gte(A("p", "fixed"), A("pol", "k_fix")), Eq(A("p", "harm"), L(0)),
                  Gt(A("p", "novel_fixed"), L(0))),
     "effects": [["set_attr", "p", "verdict", "qualifies"], ["set_attr", "p", "qualifies", 1]]},
    {"name": "family_proposal_does_not_qualify",
     "comment": "Any one of: too few fixes, any harm, or nothing a held family does not already fix.",
     "match": MATCH,
     "where": And(MEASURED, Gt(A("p", "size"), L(0)),
                  Or(Gt(A("pol", "k_fix"), A("p", "fixed")), Gt(A("p", "harm"), L(0)),
                     Eq(A("p", "novel_fixed"), L(0)))),
     "effects": [["set_attr", "p", "verdict", "does_not_qualify"], ["set_attr", "p", "qualifies", 0]]},
    {"name": "family_proposal_propose_only",
     "comment": "Propose-only: installing an agent-authored VariationOp needs the human-approved "
                "improvement_integrity exception (plan P5).",
     "match": MATCH,
     "where": And(Eq(A("p", "verdict"), L("qualifies")), Eq(A("pol", "propose_only"), L(1)),
                  Not(Eq(A("p", "install_blocked"), L(1)))),
     "effects": [["set_attr", "p", "install_blocked", 1],
                 ["set_attr", "p", "install_blocked_reason",
                  "propose-only: an agent-authored variation family is installed only after a human adds the "
                  "narrow operator_authorship exception to improvement_integrity"]]},
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
    "name": "operator_authorship", "enabled": 1, "propose_only": 1, "k_fix": 2, "max_candidates": 12,
    "max_size": 2, "bank_max_quality": 0.0,
    "description": "Agent-held policy for proposing new variation families (plan P5): how many bank turns a "
                   "candidate must fix, how many candidates and edits per candidate, which held-out turns form "
                   "the bank. Propose-only until a human decides."}}]
edges = [{"src": {"role": "agent_root"}, "type": "has_operator_authorship_policy", "tgt": {"local": 0}, "attrs": {}}]
for k, (prog, site, values, why) in enumerate(MUTATIONS, start=1):
    nodes.append({"local_id": k, "type": "FamilyMutation", "attrs": {
        "program": prog, "site": site, "values": json.dumps(values), "description": why}})
    edges.append({"src": {"local": 0}, "type": "has_family_mutation", "tgt": {"local": k}, "attrs": {}})

seed = {
    "id": "operator_authorship",
    "version": "1.0.0",
    "depends_on": [],
    "description": __doc__,
    "nodes": nodes,
    "edges": edges,
    "productions": [],
    "rules": rules,
}
P.write_text(json.dumps(seed, indent=1, ensure_ascii=True) + "\n")
print("operator_authorship", seed["version"], len(MUTATIONS), "mutation sites", len(rules), "rules")
