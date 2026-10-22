#!/usr/bin/env python3
"""Native evidence-bound grouping of complete observed two-step episodes."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "seeds" / "observed_sequence_learning.json"
AREA = "observed_sequence_learning"


def V(n): return {"type": "Var", "name": n}
def L(v): return {"type": "Lit", "value": v}
def A(n, k): return {"type": "Attr", "node": V(n), "key": k}
def T(v): return {"__term__": v}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def And(*xs): return {"type": "And", "items": list(xs)}
def Not(x): return {"type": "Not", "arg": x}
def Lt(a, b): return {"type": "Lt", "a": a, "b": b}
def Count(src): return {"type": "Count", "source": src}
def N(n, edge): return {"type": "Neighbours", "node": V(n), "edge_type": edge,
                         "any_type": False}
def Exists(source, name, predicate):
    return {"type": "Exists", "source": source, "var_name": name,
            "predicate": predicate}
def Nth(items, index): return {"type": "Nth", "items": items, "index": index}
def Concat(*xs): return {"type": "StringConcat", "parts": list(xs)}


def build_seed():
    relations = [
        ("Agent", "has_observed_sequence_learning_policy", "ObservedSequenceLearningPolicy"),
        ("Agent", "has_social_episode", "SocialEpisode"),
        ("Agent", "has_process_schema", "ProcessSchema"),
        ("Agent", "has_observed_sequence_candidate", "ObservedProcessSequenceCandidate"),
        ("ObservedProcessSequenceCandidate", "from_social_episode", "SocialEpisode"),
        ("ObservedProcessSequenceCandidate", "uses_first_primitive", "ProcessSchema"),
        ("ObservedProcessSequenceCandidate", "uses_second_primitive", "ProcessSchema"),
        ("Agent", "has_thinking_budget_request", "ThinkingBudgetRequest"),
        ("ThinkingBudgetRequest", "draws_on_thinking_budget", "ThinkingBudget"),
        ("ObservedProcessSequenceCandidate", "has_verification", "ObservedSequenceVerification"),
    ]
    rule = {
        "name": "osl_candidate_from_complete_incidental_two_step_episode",
        "area": AREA, "order": 1, "latency_class": "soft_realtime", "batch": False,
        "match": [
            ["ag", "has_observed_sequence_learning_policy", "pol"],
            ["ag", "has_social_episode", "episode"],
            ["ag", "has_process_schema", "first"],
            ["ag", "has_process_schema", "second"],
            ["ag", "has_thinking_budget_request", "request"],
            ["request", "draws_on_thinking_budget", "budget"],
        ],
        "where": And(
            Eq(A("pol", "enabled"), L(1.0)),
            Eq(A("episode", "status"), L("observed")),
            Eq(A("episode", "source_kind"), L("witnessed_interaction")),
            Eq(A("episode", "observation_status"), L("complete")),
            Not(Eq(A("episode", "actor_id"), A("episode", "owner_id"))),
            Eq(Count(Nth(A("episode", "action_sequence"), 1)), L(2)),
            Eq(Nth(Nth(A("episode", "action_sequence"), 1), 0), A("first", "operator")),
            Eq(Nth(Nth(A("episode", "action_sequence"), 1), 1), A("second", "operator")),
            Eq(A("first", "status"), L("active")),
            Eq(A("second", "status"), L("active")),
            Eq(A("first", "model_epoch"), A("episode", "model_epoch")),
            Eq(A("second", "model_epoch"), A("episode", "model_epoch")),
            Eq(A("first", "source_epoch"), A("episode", "source_epoch")),
            Eq(A("second", "source_epoch"), A("episode", "source_epoch")),
            Eq(A("first", "frame_epoch"), A("episode", "frame_epoch")),
            Eq(A("second", "frame_epoch"), A("episode", "frame_epoch")),
            Eq(A("request", "requester_kind"), L("observed_sequence_learning")),
            Eq(A("request", "episode_id"), A("episode", "episode_id")),
            Eq(A("request", "source_epoch"), A("episode", "source_epoch")),
            Eq(A("request", "status"), L("approved")),
            Not(Eq(A("request", "debited_epoch"), L(None))),
            Lt(Count(N("ag", "has_observed_sequence_candidate")),
               A("pol", "max_candidates")),
            Not(Exists(N("ag", "has_observed_sequence_candidate"), "old",
                       Eq(A("old", "episode_id"), A("episode", "episode_id")))),
        ),
        "effects": [
            ["add_node", "candidate", "ObservedProcessSequenceCandidate", {
                "candidate_id": T(Concat(L("observed-sequence:"),
                                         A("episode", "episode_id"))),
                "episode_id": T(A("episode", "episode_id")),
                "owner_id": T(A("episode", "owner_id")),
                "actor_id": T(A("episode", "actor_id")),
                "source_epoch": T(A("episode", "source_epoch")),
                "model_epoch": T(A("episode", "model_epoch")),
                "frame_epoch": T(A("episode", "frame_epoch")),
                "step_count": 2.0,
                "action_sequence": T(A("episode", "action_sequence")),
                "status": "unverified_candidate",
                "provenance": "ordered_incidental_action_observations",
                "source_ast_included": False, "teacher_marker_used": False,
                "actor_outcome_is_own_trial": False}],
            ["add_edge", "ag", "has_observed_sequence_candidate", "candidate", {}],
            ["add_edge", "candidate", "from_social_episode", "episode", {}],
            ["add_edge", "candidate", "uses_first_primitive", "first", {}],
            ["add_edge", "candidate", "uses_second_primitive", "second", {}],
            ["set_attr", "request", "terminal_status", "completed"],
        ],
    }
    return {
        "id": "observed_sequence_learning", "version": "1.0.0",
        "depends_on": ["process_schema", "thinking_budget"],
        "self_load_only": True, "area": AREA,
        "description": "P20 native grouping of complete incidental two-step action observations into an unverified candidate.",
        "microtheory": {"name": AREA,
                        "description": "An observed sequence is candidate evidence, never own grounding or verified effect."},
        "nodes": [{"local_id": 0, "type": "ObservedSequenceLearningPolicy", "attrs": {
            "name": "observed_sequence_learning_policy", "enabled": 0.0,
            "max_candidates": 16.0}}],
        "edges": [{"src": {"role": "agent_root"},
                   "type": "has_observed_sequence_learning_policy",
                   "tgt": {"local": 0}, "attrs": {}}],
        "productions": [{"provenance": f"seed:{AREA}:{edge}:{src}:{tgt}",
                         "src": {"type": src, "var": "src"},
                         "edge_type": edge, "tgt": {"type": tgt, "var": "tgt"}}
                        for src, edge, tgt in relations],
        "rules": [rule],
    }


if __name__ == "__main__":
    OUT.write_text(json.dumps(build_seed(), indent=2) + "\n", encoding="utf-8")
    print(OUT)
