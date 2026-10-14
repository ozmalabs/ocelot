#!/usr/bin/env python3
"""Emit seeds/criterion_proposals.json (plan P6, 2026-10-10): the agent
proposes changes to its reply-quality criterion; a human adopts.

CriterionPolicy holds the bar a proposal must clear on HELD-OUT labels (the
odd-dialogue TEST split; the even DEV split only chooses candidates). The
measurements are written by domains/criterion_proposals.py; these rules
DECIDE:
  * recommended: TEST kappa gain >= min_gain, TEST precision of the machine 0
    >= min_precision0, and a positive DEV gain (chosen on DEV, confirmed on
    TEST);
  * goodhart_rejected: it raises loop_success (the mean score the criterion
    gives the agent's own recent replies -- what the loop would count as
    progress) without raising TEST agreement;
  * not_recommended: anything else.
A recommended proposal waits for a human (status awaiting_human); a human's
decision (domains/criterion_proposals.decide) moves it to approved or
denied. Nothing here edits the criterion: the plan keeps criterion adoption
human-only (I1: no level is judged by a criterion it can modify). Frozen
(substrate/boot_all._FROZEN_SEED_IDS); its types are protected. Idempotent.
"""
import json
from pathlib import Path

P = Path(__file__).resolve().parents[1] / "seeds/criterion_proposals.json"


def V(n): return {"type": "Var", "name": n}
def L(v): return {"type": "Lit", "value": v}
def A(n, k): return {"type": "Attr", "node": V(n), "key": k}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def Gt(a, b): return {"type": "Gt", "a": a, "b": b}
def Gte(a, b): return {"type": "Gte", "a": a, "b": b}
def Not(x): return {"type": "Not", "arg": x}
def And(*xs): return {"type": "And", "items": list(xs)}
def Or(*xs): return {"type": "Or", "items": list(xs)}
def NN(x): return Not(Eq(x, L(None)))


MATCH = [["agent", "has_criterion_policy", "pol"], ["pol", "has_criterion_proposal", "p"]]
UNDECIDED = And(Eq(A("p", "status"), L("measured")), Eq(A("p", "verdict"), L(None)), Eq(A("pol", "enabled"), L(1)),
                NN(A("p", "test_gain")), NN(A("p", "dev_gain")))
RECOMMEND = And(Gte(A("p", "test_gain"), A("pol", "min_gain")), Gt(A("p", "dev_gain"), L(0)),
                NN(A("p", "test_precision0")), Gte(A("p", "test_precision0"), A("pol", "min_precision0")))
GOODHART = And(Gt(A("p", "success_delta"), L(0)), Not(Gt(A("p", "test_gain"), L(0))))

def Lt(a, b): return {"type": "Lt", "a": a, "b": b}
def Minus(a, b): return {"type": "Minus", "a": a, "b": b}
def Abs(x): return {"type": "IfThenElse", "cond": Lt(x, L(0)), "then": Minus(L(0), x), "other": x}


# MDL among the recommended: the largest held-out gain, then the fewest edits,
# then the smallest change to what the loop would count as progress
BETTER = And(Eq(A("o", "verdict"), L("recommended")), Not(Eq(A("o", "candidate"), A("p", "candidate"))), Or(
    Gt(A("o", "test_gain"), A("p", "test_gain")),
    And(Eq(A("o", "test_gain"), A("p", "test_gain")), Lt(A("o", "size"), A("p", "size"))),
    And(Eq(A("o", "test_gain"), A("p", "test_gain")), Eq(A("o", "size"), A("p", "size")),
        Lt(Abs(A("o", "success_delta")), Abs(A("p", "success_delta")))),
    And(Eq(A("o", "test_gain"), A("p", "test_gain")), Eq(A("o", "size"), A("p", "size")),
        Eq(Abs(A("o", "success_delta")), Abs(A("p", "success_delta"))),
        Lt(A("o", "rank"), A("p", "rank")))))

rules = [
    {"name": "criterion_proposal_recommended",
     "comment": "Chosen on DEV, confirmed on held-out TEST labels, without losing precision on what it calls bad.",
     "match": MATCH, "where": And(UNDECIDED, RECOMMEND),
     "effects": [["set_attr", "p", "verdict", "recommended"], ["set_attr", "p", "status", "awaiting_human"]]},
    {"name": "criterion_proposal_goodhart_rejected",
     "comment": "Raises what the loop would count as progress without raising agreement with held-out labels: "
                "the measurement rejects it.",
     "match": MATCH, "where": And(UNDECIDED, Not(RECOMMEND), GOODHART),
     "effects": [["set_attr", "p", "verdict", "goodhart_rejected"], ["set_attr", "p", "status", "closed"]]},
    {"name": "criterion_proposal_not_recommended",
     "match": MATCH, "where": And(UNDECIDED, Not(RECOMMEND), Not(GOODHART)),
     "effects": [["set_attr", "p", "verdict", "not_recommended"], ["set_attr", "p", "status", "closed"]]},
    {"name": "criterion_proposal_preferred",
     "comment": "The one recommended proposal put to the human first (MDL order); the others stay awaiting.",
     "match": MATCH,
     "where": And(Eq(A("p", "verdict"), L("recommended")), Not(Eq(A("p", "preferred"), L(1))),
                  Not({"type": "Exists", "source": {"type": "NodesOfType", "node_type": "CriterionProposal"},
                       "var_name": "o", "predicate": BETTER})),
     "effects": [["set_attr", "p", "preferred", 1]]},
    {"name": "criterion_proposal_human_decided",
     "comment": "Adoption is human-only: only a recorded human decision moves an awaiting proposal.",
     "match": MATCH,
     "where": And(Eq(A("p", "status"), L("awaiting_human")), NN(A("p", "human_decision"))),
     "effects": [["set_attr", "p", "status", {"__term__": A("p", "human_decision")}]]},
]

nodes = [{"local_id": 0, "type": "CriterionPolicy", "attrs": {
    "name": "reply_quality_criterion", "enabled": 1, "min_gain": 0.005, "min_precision0": 0.8, "top_k": 5,
    "description": "The bar a proposed change to the reply-quality criterion must clear on held-out labels "
                   "(plan P6). Adoption is a human decision."}}]
edges = [{"src": {"role": "agent_root"}, "type": "has_criterion_policy", "tgt": {"local": 0}, "attrs": {}}]

seed = {"id": "criterion_proposals", "version": "1.0.0", "depends_on": [], "description": __doc__,
        "nodes": nodes, "edges": edges, "productions": [], "rules": rules}
P.write_text(json.dumps(seed, indent=1, ensure_ascii=True) + "\n")
print("criterion_proposals", seed["version"], len(rules), "rules")
