#!/usr/bin/env python3
"""Generate the embodied-Pareto compatibility vocabulary.

The cognitive operation now lives in ``cognitive_pareto``. Existing motor
seeds still publish ``EmbodiedPareto*`` nodes and edges, so this seed maps that
legacy interface onto the general graph relations and projects conclusions
back. Its legacy route is instantiated from the general rule builder; it owns
no independent dominance, scalarization, or goal-selection logic.
"""
from __future__ import annotations

import json
from pathlib import Path

from scripts.gen_cognitive_pareto_seed import recognize_dominance_rule


ROOT = Path(__file__).resolve().parents[1]


def V(name): return {"type": "Var", "name": name}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def Not(arg): return {"type": "Not", "arg": arg}
def Neighbours(var, edge): return {
    "type": "Neighbours", "node": V(var), "edge_type": edge,
}
def Exists(source, var, predicate): return {
    "type": "Exists", "source": source, "var_name": var,
    "predicate": predicate,
}


def bridge_profile_candidate_rule() -> dict:
    known = Neighbours("profile", "has_pareto_candidate")
    return {
        "name": "epp_bridge_candidate_to_cognitive_pareto",
        "area": "cognitive_pareto",
        "latency_class": "soft_realtime",
        "match": [["profile", "has_embodied_pareto_candidate", "candidate"]],
        "where": Not(Exists(known, "known", Eq(V("known"), V("candidate")))),
        "effects": [["add_edge", "profile", "has_pareto_candidate", "candidate"]],
    }


def bridge_candidate_value_rule() -> dict:
    known = Neighbours("candidate", "has_pareto_value")
    return {
        "name": "epp_bridge_value_to_cognitive_pareto",
        "area": "cognitive_pareto",
        "latency_class": "soft_realtime",
        "match": [["candidate", "has_embodied_pareto_value", "value"]],
        "where": Not(Exists(known, "known", Eq(V("known"), V("value")))),
        "effects": [["add_edge", "candidate", "has_pareto_value", "value"]],
    }


def project_dominance_rule() -> dict:
    known = Neighbours("candidate", "is_dominated_by_embodied_candidate")
    return {
        "name": "epp_project_general_dominance_to_legacy_interface",
        "area": "cognitive_pareto",
        "latency_class": "soft_realtime",
        "match": [["candidate", "is_dominated_by_pareto_candidate", "alternative"]],
        "where": Not(Exists(known, "known", Eq(V("known"), V("alternative")))),
        "effects": [
            ["add_edge", "alternative", "dominates_embodied_pareto_candidate", "candidate"],
            ["add_edge", "candidate", "is_dominated_by_embodied_candidate", "alternative"],
        ],
    }


def manifest() -> dict:
    productions = [
        ("candidate", "EmbodiedParetoProfile", "has_embodied_pareto_candidate", "EmbodiedParetoCandidate"),
        ("value", "EmbodiedParetoCandidate", "has_embodied_pareto_value", "EmbodiedParetoValue"),
        ("dominance", "EmbodiedParetoCandidate", "dominates_embodied_pareto_candidate", "EmbodiedParetoCandidate"),
        ("dominated_by", "EmbodiedParetoCandidate", "is_dominated_by_embodied_candidate", "EmbodiedParetoCandidate"),
    ]
    return {
        "id": "embodied_pareto_profile",
        "version": "2.0.0",
        "depends_on": ["cognitive_pareto"],
        "area": "compatibility",
        "latency_class": "soft_realtime",
        "description": "Compatibility mapping from legacy embodied Pareto "
        "vocabulary to the general cognitive Pareto and goal-audit faculty.",
        "nodes": [],
        "edges": [],
        "productions": [
            {
                "provenance": f"embodied_pareto_profile:{name}",
                "src": {"type": src, "var": "src"},
                "edge_type": edge,
                "tgt": {"type": tgt, "var": "tgt"},
            }
            for name, src, edge, tgt in productions
        ],
        "rules": [
            recognize_dominance_rule(
                name="epp_route_legacy_relations_through_cognitive_pareto",
                candidate_edge="has_embodied_pareto_candidate",
                value_edge="has_embodied_pareto_value",
                dominates_edge="dominates_embodied_pareto_candidate",
                dominated_by_edge="is_dominated_by_embodied_candidate",
            ),
            bridge_profile_candidate_rule(),
            bridge_candidate_value_rule(),
            project_dominance_rule(),
        ],
    }


def main() -> int:
    output = ROOT / "seeds" / "embodied_pareto_profile.json"
    output.write_text(json.dumps(manifest(), indent=1) + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
