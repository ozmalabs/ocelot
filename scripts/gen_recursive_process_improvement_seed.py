#!/usr/bin/env python3
"""Generate the P15.04 persistent, approval-gated operator generation lifecycle."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "seeds" / "recursive_process_improvement.json"
AREA = "memory_consolidation"


def V(n): return {"type": "Var", "name": n}
def A(n, k): return {"type": "Attr", "node": V(n), "key": k}
def L(v): return {"type": "Lit", "value": v}
def Eq(a, b): return {"type": "Eq", "a": a, "b": b}
def And(*xs): return {"type": "And", "items": list(xs)}
def Or(*xs): return {"type": "Or", "items": list(xs)}
def Not(x): return {"type": "Not", "arg": x}
def Gt(a, b): return {"type": "Gt", "a": a, "b": b}
def Lt(a, b): return {"type": "Lt", "a": a, "b": b}
def N(n, e): return {"type": "Neighbours", "node": V(n), "edge_type": e, "any_type": False}
def Count(src): return {"type": "Count", "source": src}
def Exists(src, var, pred): return {"type": "Exists", "source": src, "var_name": var, "predicate": pred}
def Concat(*xs): return {"type": "StringConcat", "parts": list(xs)}
def T(x): return {"__term__": x}


def build():
    seed = json.loads((ROOT / "seeds/invention_operator_authorship.json").read_text())
    rels = [
        ("Agent", "has_recursive_improvement_policy", "RecursiveProcessImprovementPolicy"),
        ("Agent", "has_process_generation", "RecursiveProcessGeneration"),
        ("Agent", "has_recursive_generation_request", "ThinkingBudgetRequest"),
        ("RecursiveProcessGeneration", "funded_by_generation_request", "ThinkingBudgetRequest"),
        ("RecursiveProcessGeneration", "parent_generation", "RecursiveProcessGeneration"),
        ("RecursiveProcessGeneration", "generation_candidate", "CandidateOperator"),
        ("RecursiveProcessGeneration", "generation_operator", "InventionOperator"),
        ("RecursiveProcessGeneration", "has_generation_audit", "GenerationInvariantAudit"),
        ("RecursiveProcessGeneration", "rollback_to_generation", "RecursiveProcessGeneration"),
    ]
    seed["id"] = "recursive_process_improvement"
    seed["version"] = "1.0.0"
    seed["depends_on"] = ["invention_operator_authorship"]
    seed["area"] = AREA
    seed["description"] = "P15.04: graph-owned recursive operator generations with immutable ancestry, scoped approval, shared generation work ceilings and recorded rollback."
    seed["nodes"] = [{"local_id": 0, "type": "RecursiveProcessImprovementPolicy", "attrs": {
        "name": "recursive_process_improvement_policy", "enabled": 0.0,
        "max_generations": 3.0, "generation_work_cap": 100000.0,
        "frozen_criteria_digest": "pmb-v1-frozen-criteria", "human_gate": 1.0,
    }}, {"local_id": 1, "type": "RecursiveProcessGeneration", "attrs": {
        "generation_id": "generation-0", "generation_index": 0.0,
        "operator_digest": "held:commutator", "status": "frozen_ancestor",
        "arm": "frozen_ancestor", "human_authored_operator_count": 0.0,
        "budget_initial": 100000.0, "budget_remaining": 100000.0,
        "cumulative_work": 0.0, "autonomy_claim": "valid",
    }}]
    seed["edges"] = [
        {"src": {"role": "agent_root"}, "type": "has_recursive_improvement_policy", "tgt": {"local": 0}, "attrs": {}},
        {"src": {"role": "agent_root"}, "type": "has_process_generation", "tgt": {"local": 1}, "attrs": {}},
    ]
    seed["productions"] += [{"provenance": f"seed:rpi:{edge}:{src}:{dst}",
        "src": {"type": src, "var": "src"}, "edge_type": edge,
        "tgt": {"type": dst, "var": "tgt"}} for src, edge, dst in rels]

    policy = ["agent", "has_recursive_improvement_policy", "pol"]
    candidate = ["agent", "has_candidate_operator", "c"]
    generation = ["agent", "has_process_generation", "g"]
    seed["rules"].append({"name": "rpi_reserve_one_shared_generation_budget", "area": AREA,
        "order": 23, "latency_class": "hard_realtime", "batch": False,
        "comment": "Reserve one complete generation ceiling from the single shared ThinkingBudget before creating generation state.",
        "match": [policy, candidate, ["agent", "has_thinking_budget", "budget"]],
        "where": And(Eq(A("pol", "enabled"), L(1.0)),
            Eq(A("budget", "enabled"), L(1.0)),
            Eq(A("c", "status"), L("awaiting_human")),
            Eq(A("c", "authoring"), L("native_graph_rule")),
            Not(Exists(N("agent", "has_recursive_generation_request"), "old",
                       Eq(A("old", "source_key"), A("c", "name"))))),
        "effects": [["add_node", "request", "ThinkingBudgetRequest", {
                "requester_kind": "recursive_process_generation",
                "source_key": T(A("c", "name")), "operation_id": T(A("c", "name")),
                "source_epoch": 0.0, "requested_epoch": 0.0, "deadline_epoch": 1.0,
                "cost": T(A("pol", "generation_work_cap")), "status": "pending"}],
            ["add_edge", "agent", "has_thinking_budget_request", "request", {}],
            ["add_edge", "agent", "has_recursive_generation_request", "request", {}],
            ["add_edge", "request", "draws_on_thinking_budget", "budget", {}]]})
    # Record every qualified candidate as a pending immutable child generation.
    seed["rules"].append({"name": "rpi_record_candidate_generation_before_approval", "area": AREA,
        "order": 24, "latency_class": "background", "batch": False,
        "comment": "Bind a graph-authored, development-qualified candidate to one immutable child generation before the human gate.",
        "match": [policy, candidate, generation,
                  ["agent", "has_recursive_generation_request", "request"],
                  ["request", "draws_on_thinking_budget", "budget"]],
        "where": And(Eq(A("pol", "enabled"), L(1.0)),
            Eq(A("c", "status"), L("awaiting_human")),
            Eq(A("c", "authoring"), L("native_graph_rule")),
            Eq(A("c", "criteria_digest"), A("pol", "frozen_criteria_digest")),
            Eq(A("request", "status"), L("approved")),
            Eq(A("request", "source_key"), A("c", "name")),
            Eq(A("g", "status"), L("frozen_ancestor")),
            Lt(Count(N("agent", "has_process_generation")), A("pol", "max_generations")),
            Not(Exists(N("agent", "has_process_generation"), "old",
                Eq(A("old", "candidate_name"), A("c", "name"))))),
        "effects": [
            ["add_node", "child", "RecursiveProcessGeneration", {
                "generation_id": T(Concat(L("generation:"), A("c", "name"))),
                "generation_index": 1.0, "candidate_name": T(A("c", "name")),
                "operator_digest": T(A("c", "name")), "status": "pending_approval",
                "arm": "full_system", "human_authored_operator_count": 0.0,
                "budget_initial": T(A("request", "cost")),
                "budget_remaining": T(A("request", "cost")),
                "cumulative_work": T(A("c", "candidate_work")),
                "autonomy_claim": "valid", "criteria_digest": T(A("c", "criteria_digest")),
            }],
            ["add_edge", "agent", "has_process_generation", "child", {}],
            ["add_edge", "child", "parent_generation", "g", {}],
            ["add_edge", "child", "generation_candidate", "c", {}],
            ["add_edge", "child", "funded_by_generation_request", "request", {}],
        ]})
    # Approval remains governed solely by the existing P14 graph rule. This rule records its result.
    seed["rules"].append({"name": "rpi_activate_only_approved_generation", "area": AREA,
        "order": 35, "latency_class": "background", "batch": False,
        "comment": "An approved P14 operator promotion activates its matching child generation while retaining frozen ancestry.",
        "match": [policy, ["agent", "has_invention_operator", "op"],
                  ["op", "derived_from_candidate", "c"], generation,
                  ["g", "generation_candidate", "c"]],
        "where": And(Eq(A("pol", "enabled"), L(1.0)),
            Eq(A("g", "status"), L("pending_approval")),
            Eq(A("op", "approval_kind"), L("human")),
            Eq(A("op", "provenance"), L("agent_authored_graph_data")),
            Eq(A("c", "authoring"), L("native_graph_rule")),
            Eq(A("c", "status"), L("promoted"))),
        "effects": [["add_edge", "g", "generation_operator", "op", {}],
                    ["set_attr", "g", "status", "active"],
                    ["set_attr", "g", "active_operator", T(A("op", "name"))]]})
    seed["rules"].append({"name": "rpi_suspend_operator_without_funded_generation", "area": AREA,
        "order": 36, "latency_class": "hard_realtime", "batch": False,
        "comment": "An operator cannot remain active if its generation could not reserve the shared work ceiling.",
        "match": [policy, ["agent", "has_invention_operator", "op"],
                  ["op", "derived_from_candidate", "c"]],
        "where": And(Eq(A("pol", "enabled"), L(1.0)),
            Eq(A("op", "status"), L("active")),
            Eq(A("op", "approval_kind"), L("human")),
            Not(Exists(N("agent", "has_process_generation"), "g",
                        Eq(A("g", "candidate_name"), A("c", "name"))))),
        "effects": [["set_attr", "op", "status", "suspended"],
                    ["set_attr", "c", "status", "rejected"],
                    ["set_attr", "c", "verdict", "generation_budget_not_reserved"]]})
    # Any failed proof/adoption/grounding/action audit terminally rolls the lineage back.
    seed["rules"].append({"name": "rpi_rollback_failed_generation_to_verified_ancestor", "area": AREA,
        "order": 40, "latency_class": "hard_realtime", "batch": False,
        "comment": "Record invariant failure, suspend the child operator and reactivate its direct frozen ancestor.",
        "match": [policy, generation, ["g", "has_generation_audit", "audit"],
                  ["g", "parent_generation", "parent"],
                  ["g", "generation_operator", "op"]],
        "where": And(Eq(A("pol", "enabled"), L(1.0)),
            Eq(A("g", "status"), L("active")),
            Or(Eq(A("audit", "status"), L("failed")),
               Eq(A("audit", "proof_binding"), L(False)),
               Eq(A("audit", "adoption_valid"), L(False)),
               Eq(A("audit", "grounding_valid"), L(False)),
               Eq(A("audit", "action_safe"), L(False)))),
        "effects": [["set_attr", "g", "status", "rolled_back"],
                    ["set_attr", "g", "terminal_reason", "zero_tolerance_invariant_failure"],
                    ["set_attr", "g", "autonomy_claim", "invalid"],
                    ["set_attr", "op", "status", "suspended"],
                    ["add_edge", "g", "rollback_to_generation", "parent", {}],
                    ["set_attr", "parent", "status", "active"],
                    ["set_attr", "parent", "active_operator", T(A("parent", "operator_digest"))]]})
    # Human edits in candidate/operator state invalidate autonomy claims and never become active generation data.
    seed["rules"].append({"name": "rpi_invalidate_human_edited_generation_claim", "area": AREA,
        "order": 41, "latency_class": "hard_realtime", "batch": False,
        "match": [policy, generation, ["g", "generation_candidate", "c"]],
        "where": And(Eq(A("pol", "enabled"), L(1.0)),
            Eq(A("g", "autonomy_claim"), L("valid")),
            Not(Eq(A("c", "authoring"), L("native_graph_rule")))),
        "effects": [["set_attr", "g", "autonomy_claim", "invalid"],
                    ["set_attr", "g", "status", "rejected_human_edit"]]})
    return seed


def main():
    OUT.write_text(json.dumps(build(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
