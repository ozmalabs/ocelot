#!/usr/bin/env python3
"""Generate the opt-in P25 persistent learned-effect consolidation rule."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "seeds" / "persistent_consolidation.json"
AREA = "persistent_consolidation"


def V(name): return {"type": "Var", "name": name}
def L(value): return {"type": "Lit", "value": value}
def A(node, key): return {"type": "Attr", "node": V(node), "key": key}
def T(value): return {"__term__": value}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def Gt(a, b): return {"type": "Gt", "a": a, "b": b}
def Lt(a, b): return {"type": "Lt", "a": a, "b": b}
def And(*items): return {"type": "And", "items": list(items)}
def Not(arg): return {"type": "Not", "arg": arg}
def N(node, edge):
    return {"type": "Neighbours", "node": V(node), "edge_type": edge,
            "any_type": False}
def Exists(source, name, predicate):
    return {"type": "Exists", "source": source, "var_name": name,
            "predicate": predicate}
def Concat(*items): return {"type": "StringConcat", "parts": list(items)}


def build_seed():
    relations = [
        ("Agent", "has_persistent_consolidation_policy", "PersistentConsolidationPolicy"),
        ("Agent", "has_persistent_consolidation_work", "PersistentConsolidationWork"),
        ("Agent", "has_process_induction_hypothesis", "ProcessInductionHypothesis"),
        ("ProcessInductionHypothesis", "supported_by_transition", "TransitionObservation"),
        ("Agent", "has_persistent_learned_summary", "PersistentLearnedSummary"),
        ("PersistentLearnedSummary", "has_consolidation_witness", "TransitionObservation"),
        ("PersistentLearnedSummary", "projects_to_process_hypothesis", "ProcessInductionHypothesis"),
        ("ProcessInductionHypothesis", "supported_by_persistent_summary", "PersistentLearnedSummary"),
        ("Agent", "has_thinking_budget", "ThinkingBudget"),
    ]

    def persistent_hypothesis_attrs(hyp):
        keys = ("owner_id", "action_kind", "object_type", "feature_key",
                "before_value", "after_value", "source_epoch", "model_epoch",
                "frame_epoch", "support_count", "counterexample_count", "law_kind")
        attrs = {key: T(A(hyp, key)) for key in keys}
        attrs.update({"hypothesis_key": T(Concat(L("persistent:"), A(hyp, "hypothesis_key"))),
                      "status": "candidate", "persistent_summary": True,
                      "consolidation_verified": True})
        return attrs

    rule = {
        "name": "pc_consolidate_verified_effect_on_same_learner",
        "area": AREA, "order": 1, "latency_class": "background", "batch": False,
        "comment": "Persist a verified native effect summary with two independent witnesses; do not consolidate disputed or interrupted work.",
        "match": [
            ["ag", "has_persistent_consolidation_policy", "pol"],
            ["ag", "has_persistent_consolidation_work", "work"],
            ["ag", "has_process_induction_hypothesis", "hyp"],
            ["hyp", "supported_by_transition", "first"],
            ["hyp", "supported_by_transition", "second"],
            ["ag", "has_thinking_budget", "budget"],
        ],
        "where": And(
            Eq(A("pol", "enabled"), L(1.0)),
            Eq(A("work", "status"), L("requested")),
            Eq(A("work", "interrupted"), L(False)),
            Eq(A("work", "foreground_demand"), L(False)),
            Eq(A("hyp", "status"), L("candidate")),
            Gt(A("hyp", "support_count"), L(1.0)),
            Eq(A("hyp", "counterexample_count"), L(0.0)),
            Eq(A("first", "owner_id"), A("hyp", "owner_id")),
            Eq(A("second", "owner_id"), A("hyp", "owner_id")),
            Not(Eq(A("first", "event_id"), A("second", "event_id"))),
            Lt(A("first", "event_id"), A("second", "event_id")),
            Eq(A("first", "action_kind"), A("hyp", "action_kind")),
            Eq(A("second", "action_kind"), A("hyp", "action_kind")),
            Eq(A("first", "after_value"), A("hyp", "after_value")),
            Eq(A("second", "after_value"), A("hyp", "after_value")),
            Gt(A("budget", "remaining"), L(0.0)),
            Not(Exists(N("ag", "has_persistent_learned_summary"), "old",
                       Eq(A("old", "source_hypothesis_key"), A("hyp", "hypothesis_key")))),
        ),
        "effects": [
            ["add_node", "summary", "PersistentLearnedSummary", {
                "summary_id": T(Concat(L("persistent-summary:"), A("hyp", "hypothesis_key"))),
                "source_hypothesis_key": T(A("hyp", "hypothesis_key")),
                "owner_id": T(A("hyp", "owner_id")),
                "action_kind": T(A("hyp", "action_kind")),
                "object_type": T(A("hyp", "object_type")),
                "feature_key": T(A("hyp", "feature_key")),
                "before_value": T(A("hyp", "before_value")),
                "after_value": T(A("hyp", "after_value")),
                "source_epoch": T(A("hyp", "source_epoch")),
                "model_epoch": T(A("hyp", "model_epoch")),
                "frame_epoch": T(A("hyp", "frame_epoch")),
                "support_count": T(A("hyp", "support_count")),
                "counterexample_count": T(A("hyp", "counterexample_count")),
                "witness_event_1": T(A("first", "event_id")),
                "witness_event_2": T(A("second", "event_id")),
                "serialized_bytes": 0.0,
                "summary_charge_status": "pending_mechanical_measurement",
                "status": "verified",
                "decoder_kind": "native_process_induction_hypothesis",
                "exceptions_retained": T(L(True)),
            }],
            ["add_node", "persistent_hyp", "ProcessInductionHypothesis",
             persistent_hypothesis_attrs("hyp")],
            ["add_node", "summary_item", "LearningMemoryItem", {
                "item_id": T(Concat(L("persistent-summary:"), A("hyp", "hypothesis_key"))),
                "content_class": "persistent_summary",
                "charged_bytes": 0.0,
                "retention_priority": T(A("pol", "summary_priority")),
                "payload": None, "protection_class": "ordinary",
                "availability": "awaiting_charge",
            }],
            ["add_edge", "ag", "has_persistent_learned_summary", "summary", {}],
            ["add_edge", "ag", "has_learning_memory_item", "summary_item", {}],
            ["add_edge", "summary", "has_consolidation_witness", "first", {}],
            ["add_edge", "summary", "has_consolidation_witness", "second", {}],
            ["add_edge", "summary", "projects_to_process_hypothesis", "persistent_hyp", {}],
            ["add_edge", "persistent_hyp", "supported_by_persistent_summary", "summary", {}],
            ["add_edge", "ag", "has_process_induction_hypothesis", "persistent_hyp", {}],
            ["set_attr", "hyp", "status", "consolidated_source"],
            ["set_attr", "hyp", "persistent_summary_id",
             T(Concat(L("persistent-summary:"), A("hyp", "hypothesis_key")))],
            ["set_attr", "hyp", "consolidation_verified", T(L(True))],
            ["set_attr", "work", "status", "completed"],
            ["set_attr", "work", "completed_summary_id",
             T(Concat(L("persistent-summary:"), A("hyp", "hypothesis_key")))],
            ["set_attr", "budget", "remaining",
             T({"type": "Minus", "a": A("budget", "remaining"),
                "b": A("pol", "work_cost")})],
        ],
    }
    return {
        "id": "persistent_consolidation", "version": "1.0.0",
        "depends_on": ["target_learning", "learning_memory_budget"],
        "self_load_only": True, "area": AREA,
        "description": "Opt-in, once-owned consolidation of verified native learned effects onto the persistent learner.",
        "microtheory": {"name": AREA,
                        "description": "Retain learned process structure and witnesses on the same native learner."},
        "nodes": [{"local_id": 0, "type": "PersistentConsolidationPolicy", "attrs": {
            "name": "persistent_consolidation_policy", "enabled": 0.0,
            "work_cost": 1.0,
            "summary_priority": 100.0,
        }}],
        "edges": [{"src": {"role": "agent_root"},
                    "type": "has_persistent_consolidation_policy",
                    "tgt": {"local": 0}, "attrs": {}}],
        "productions": [{"provenance": f"seed:{AREA}:{edge}:{src}:{tgt}",
                         "src": {"type": src, "var": "src"}, "edge_type": edge,
                         "tgt": {"type": tgt, "var": "tgt"}}
                        for src, edge, tgt in relations],
        "rules": [rule],
    }


def main():
    OUT.write_text(json.dumps(build_seed(), indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
