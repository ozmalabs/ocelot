#!/usr/bin/env python3
"""Generate the domain-independent Pareto and goal-audit faculty.

Pareto dominance is not a motor policy. It is a general counterexample test:
given an incumbent goal/choice and several complete, verified alternatives,
does another point improve at least one objective without worsening any? If
so, the incumbent is falsified relative to the declared objective basis.

The faculty does not scalarize, choose among incomparable alternatives, or
silently replace a goal. It emits a GoalRevisionRequest carrying the concrete
dominating alternative. All cognitive quantities are integer quanta.
"""
from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def V(name): return {"type": "Var", "name": name}
def L(value): return {"type": "Lit", "value": value}
def A(var, key): return {"type": "Attr", "node": V(var), "key": key}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def And(*items): return {"type": "And", "items": list(items)}
def Or(*items): return {"type": "Or", "items": list(items)}
def Not(arg): return {"type": "Not", "arg": arg}
def Neighbours(var, edge): return {
    "type": "Neighbours", "node": V(var), "edge_type": edge,
}
def Filter(source, var, predicate): return {
    "type": "Filter", "source": source, "var_name": var,
    "predicate": predicate,
}
def Exists(source, var, predicate): return {
    "type": "Exists", "source": source, "var_name": var,
    "predicate": predicate,
}
def Count(source): return {"type": "Count", "source": source}


def recognize_dominance_rule(
    *,
    name: str = "cp_recognize_relational_dominance",
    candidate_edge: str = "has_pareto_candidate",
    value_edge: str = "has_pareto_value",
    dominates_edge: str = "dominates_pareto_candidate",
    dominated_by_edge: str = "is_dominated_by_pareto_candidate",
) -> dict:
    dominance = {
        "type": "ParetoDominates",
        "candidate": V("candidate"),
        "alternative": V("alternative"),
        "dimension_count": A("profile", "dimension_count"),
        "value_edge": value_edge,
        "measure_edge": "measures_goal",
        "dimension_key": "dimension_ordinal",
        "verified_key": "verified",
        "signed_value_key": "signed_value",
    }
    known = Neighbours("candidate", dominated_by_edge)
    return {
        "name": name,
        "area": "cognitive_pareto",
        "latency_class": "soft_realtime",
        "comment": "Find a concrete counterexample to a candidate without "
        "collapsing incomparable objectives into a scalar.",
        "match": [
            ["profile", candidate_edge, "candidate"],
            ["profile", candidate_edge, "alternative"],
        ],
        "where": And(
            # Completed profiles and profiles belonging to a detached
            # embodiment are immutable history. Their explicit lifecycle fact
            # prevents global System-2 passes from re-proving old frontiers.
            Not(Or(
                Eq(A("profile", "pareto_suspended"), L(1)),
                Eq(A("profile", "status"), L("continued")),
                Eq(A("profile", "status"), L("replan_required")),
                Eq(A("profile", "status"), L("selected")),
            )),
            Not(Eq(V("candidate"), V("alternative"))),
            # Dominance is a counterexample.  Once a completed pass has found
            # at least one witness, later cycles need not re-scan this candidate:
            # more dominators cannot change frontier membership or goal audit.
            Eq(Count(known), L(0)),
            dominance,
        ),
        "effects": [
            ["add_edge", "alternative", dominates_edge, "candidate"],
            ["add_edge", "candidate", dominated_by_edge, "alternative"],
            ["set_attr", "candidate", "dominated", 1],
        ],
    }


def retract_stale_dominance_rule(
    *,
    name: str = "cp_retract_stale_relational_dominance",
    candidate_edge: str = "has_pareto_candidate",
    value_edge: str = "has_pareto_value",
    dominates_edge: str = "dominates_pareto_candidate",
    dominated_by_edge: str = "is_dominated_by_pareto_candidate",
) -> dict:
    """A DERIVED RELATION MUST NOT OUTLIVE ITS PREMISE.

    `cp_recognize_relational_dominance` records "alternative dominates
    candidate" as a permanent edge and then declines to re-scan the candidate,
    on the stated reasoning that "more dominators cannot change frontier
    membership". That reasoning is exactly right for an IMMUTABLE frontier and
    exactly wrong for a MUTATING one: a learning frontier's candidates have
    their Pareto values rewritten by every receipt, so a counterexample proved
    against old values is cached against new ones forever.

    Measured consequence, on a live grounded humanoid: the motor frontier's
    dominance edges accumulate monotonically until EVERY candidate carries at
    least one, at which point `Count(is_dominated) == 0` is false for all of
    them, no motor program can be selected, and trial production stops dead.
    Reproduced at 48-52 trials on three separate runs, and it is the ceiling
    every run in this line has hit, including the original 13-hour one:
    43 of 43 candidates dominated, dominator counts 7 to 42, none at zero.
    A finite non-empty set under a strict partial order ALWAYS has a maximal
    element, so an empty frontier is never a fact about the candidates -- it is
    proof that the relation being read is stale.

    This rule is the exact negation of the recognition predicate, over the same
    `ParetoDominates` Term with the same parameters, so it withdraws precisely
    what recognition would no longer assert -- no guard is widened and no
    frontier membership is invented. It carries the same area and latency class
    as recognition deliberately: a correction that ran in a different pass from
    the claim it corrects would leave windows where the claim stands unchecked.
    """
    dominance = {
        "type": "ParetoDominates",
        "candidate": V("candidate"),
        "alternative": V("alternative"),
        "dimension_count": A("profile", "dimension_count"),
        "value_edge": value_edge,
        "measure_edge": "measures_goal",
        "dimension_key": "dimension_ordinal",
        "verified_key": "verified",
        "signed_value_key": "signed_value",
    }
    return {
        "name": name,
        "area": "cognitive_pareto",
        "latency_class": "soft_realtime",
        "comment": "Withdraw a dominance counterexample that its own values no "
        "longer support. Recognition caches a witness and stops re-scanning, "
        "which is sound only while the candidates are immutable; on a learning "
        "frontier the cache empties the frontier and halts selection.",
        "match": [
            ["profile", candidate_edge, "candidate"],
            ["profile", candidate_edge, "alternative"],
            ["candidate", dominated_by_edge, "alternative"],
        ],
        "where": And(
            # Completed / detached profiles are immutable history, exactly as
            # recognition treats them. History is not re-tested and not edited.
            Not(Or(
                Eq(A("profile", "pareto_suspended"), L(1)),
                Eq(A("profile", "status"), L("continued")),
                Eq(A("profile", "status"), L("replan_required")),
                Eq(A("profile", "status"), L("selected")),
            )),
            Not(Eq(V("candidate"), V("alternative"))),
            # THE PREMISE, RE-TESTED. Retract iff the claim is no longer true.
            Not(dominance),
        ),
        "effects": [
            ["del_edge", "candidate", dominated_by_edge, "alternative"],
            ["del_edge", "alternative", dominates_edge, "candidate"],
        ],
    }


def settle_dominated_flag_rule(
    *,
    name: str = "cp_settle_dominated_flag_from_surviving_counterexamples",
    candidate_edge: str = "has_pareto_candidate",
    dominated_by_edge: str = "is_dominated_by_pareto_candidate",
) -> dict:
    """The `dominated` attribute is a CACHE of the edge set, so it is restated
    from the edges rather than latched.

    Recognition sets it to 1 and nothing ever cleared it -- the same defect as
    the edges, in attribute form. Leaving a retracted candidate flagged
    `dominated: 1` would keep it off the frontier by a stale attribute after
    the stale edge had been withdrawn, which is the identical failure one layer
    down.

    UNCONDITIONAL, because `Count` over `Neighbours` is an aggregate and this
    tree has measured that aggregates read as their identity inside a `where`
    while being correct in an effect. It does not need a guard: it is a pure
    function of the edge set, so re-firing rewrites the same value and the
    fixpoint terminates.
    """
    return {
        "name": name,
        "area": "cognitive_pareto",
        "latency_class": "soft_realtime",
        "comment": "Restate `dominated` from the surviving counterexamples so "
        "the flag cannot outlive the edges it summarises.",
        "match": [["profile", candidate_edge, "candidate"]],
        "where": L(True),
        "effects": [
            ["set_attr", "candidate", "dominated", {"__term__": {
                "type": "IfThenElse",
                "cond": {"type": "Gt",
                         "a": Count(Neighbours("candidate", dominated_by_edge)),
                         "b": L(0)},
                "then": L(1),
                "other": L(0),
            }}],
        ],
    }


def request_goal_revision_rule() -> dict:
    existing = Filter(
        Neighbours("profile", "has_goal_revision_request"),
        "request",
        Exists(
            Neighbours("request", "proposed_by_pareto_candidate"),
            "known_alternative",
            Eq(V("known_alternative"), V("alternative")),
        ),
    )
    return {
        "name": "cp_falsify_dominated_incumbent_goal",
        "area": "cognitive_pareto",
        "latency_class": "soft_realtime",
        "comment": "A dominating alternative is evidence that the incumbent "
        "goal is wrong relative to its own objective basis. Request revision; "
        "never silently replace the goal.",
        "match": [
            ["profile", "audits_goal", "goal"],
            ["profile", "has_incumbent_pareto_candidate", "incumbent"],
            ["incumbent", "is_dominated_by_pareto_candidate", "alternative"],
        ],
        "where": Not(Exists(existing, "known_request", L(True))),
        "effects": [
            ["add_node", "request", "GoalRevisionRequest", {
                "status": "requested",
                "reason": "pareto_counterexample",
                "verified": 1,
            }],
            ["add_edge", "profile", "has_goal_revision_request", "request"],
            ["add_edge", "request", "about_goal", "goal"],
            ["add_edge", "request", "proposed_by_pareto_candidate", "alternative"],
            ["set_attr", "goal", "pareto_status", "dominated"],
        ],
    }


def manifest() -> dict:
    productions = [
        ("profile_candidate", "ParetoProfile", "has_pareto_candidate", "ParetoCandidate"),
        ("profile_dimension", "ParetoProfile", "has_pareto_dimension", "ParetoDimension"),
        ("candidate_value", "ParetoCandidate", "has_pareto_value", "ParetoValue"),
        ("value_dimension", "ParetoValue", "measures_pareto_dimension", "ParetoDimension"),
        ("value_goal", "ParetoValue", "measures_goal", "Goal"),
        ("dominance", "ParetoCandidate", "dominates_pareto_candidate", "ParetoCandidate"),
        ("dominated_by", "ParetoCandidate", "is_dominated_by_pareto_candidate", "ParetoCandidate"),
        ("audit_goal", "ParetoProfile", "audits_goal", "Goal"),
        ("incumbent", "ParetoProfile", "has_incumbent_pareto_candidate", "ParetoCandidate"),
        ("revision", "ParetoProfile", "has_goal_revision_request", "GoalRevisionRequest"),
        ("revision_goal", "GoalRevisionRequest", "about_goal", "Goal"),
        ("revision_candidate", "GoalRevisionRequest", "proposed_by_pareto_candidate", "ParetoCandidate"),
    ]
    return {
        "id": "cognitive_pareto",
        "version": "1.2.0",
        "depends_on": [],
        "area": "cognitive_pareto",
        "latency_class": "soft_realtime",
        "description": "Domain-independent relational Pareto comparison by "
        "declared ordinal or graph-identified Goal dimension, plus "
        "counterexample-based goal revision with integer-native cognition.",
        "nodes": [],
        "edges": [],
        "productions": [
            {
                "provenance": f"cognitive_pareto:{name}",
                "src": {"type": src, "var": "src"},
                "edge_type": edge,
                "tgt": {"type": tgt, "var": "tgt"},
            }
            for name, src, edge, tgt in productions
        ],
        "rules": [recognize_dominance_rule(), retract_stale_dominance_rule(),
                  settle_dominated_flag_rule(), request_goal_revision_rule()],
    }


def main() -> int:
    output = ROOT / "seeds" / "cognitive_pareto.json"
    output.write_text(json.dumps(manifest(), indent=1) + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
