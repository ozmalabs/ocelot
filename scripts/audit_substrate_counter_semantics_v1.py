#!/usr/bin/env python3
"""Source-linked inventory of runtime counters and access/work trace semantics.

This is a source audit, not a dynamic calibration or runtime completeness claim.
It anchors counter definitions and call sites so later workload captures can
state which equations are justified and which work remains outside them.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "evaluation/reports/substrate_counter_semantics_v1_20260928.json"
SOURCES = {
    "scale_audit": ROOT / "runners/dsl/src/scale_audit.rs",
    "rewrite": ROOT / "runners/dsl/src/rewrite.rs",
    "access_trace": ROOT / "runners/dsl/src/access_trace.rs",
    "term": ROOT / "runners/dsl/src/term.rs",
    "world_adapter": ROOT / "substrate/world_adapter.py",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def anchor(path_key: str, needle: str) -> dict[str, object]:
    lines = SOURCES[path_key].read_text().splitlines()
    hits = [i for i, line in enumerate(lines, 1) if needle in line]
    if not hits:
        raise ValueError(f"missing source anchor {path_key}:{needle!r}")
    return {"path": str(SOURCES[path_key].relative_to(ROOT)),
            "line": hits[0], "anchor": needle}


COUNTERS = [
    {
        "name": "candidate_pairs_enumerated",
        "meaning": "Pairs materialized by one match-edge expansion, classified by local/hinted/full-scan path; candidates may later fail bound checks.",
        "equation": "sum(candidates(n,path))",
        "not_equivalent_to": ["candidate_tests", "successful bindings", "unique graph edges"],
        "anchors": [anchor("scale_audit", "pub fn candidates("),
                    anchor("rewrite", "crate::scale_audit::candidates(candidates.len() as u64, cand_path);")],
    },
    {
        "name": "candidate_tests",
        "meaning": "One increment per pair entering the extend_each candidate loop, before bound-source/target rejection.",
        "equation": "candidate_tests = candidate_loop_iterations",
        "not_equivalent_to": ["successful pattern_edge events", "Term evaluations", "full graph accesses"],
        "anchors": [anchor("scale_audit", "pub fn cand_tested("),
                    anchor("rewrite", "crate::scale_audit::cand_tested(i, rule.name.0, rule.match_edges.len());")],
    },
    {
        "name": "bound_rejections",
        "meaning": "Subset of candidate-loop iterations rejected by already-bound endpoint equality checks.",
        "equation": "bound_rejections <= candidate_tests",
        "not_equivalent_to": ["all failed matches", "where rejections"],
        "anchors": [anchor("scale_audit", "pub fn cand_reject_bound()"),
                    anchor("rewrite", "crate::scale_audit::cand_reject_bound();")],
    },
    {
        "name": "where_evaluations",
        "meaning": "Calls to a where expression or an unpruned conjunct, counted after boolean evaluation; pushdown evaluations use a separate counter.",
        "equation": "where_evaluations = interpreted/JIT whole-where and remaining-conjunct evaluations",
        "not_equivalent_to": ["candidate_tests", "all predicate work", "pushdown evaluations"],
        "anchors": [anchor("scale_audit", "pub fn where_eval(passed: bool)"),
                    anchor("rewrite", "crate::scale_audit::where_eval(ok);")],
    },
    {
        "name": "successful_bindings",
        "meaning": "A match leaf after distinct-variable and where checks; cloned-binding counts are recorded on the cold-path consumer, not as a general matcher identity count.",
        "equation": "leaf_visits = successful match leaves reaching the visitor",
        "not_equivalent_to": ["candidate_tests", "rule firings", "effects committed"],
        "anchors": [anchor("rewrite", "crate::scale_audit::leaf_visit();"),
                    anchor("rewrite", "crate::scale_audit::binding_cloned();")],
    },
    {
        "name": "scheduler_work",
        "meaning": "Monolithic run_rules scheduler slot counts: external poll, fixed-point probe, dirty-vector scan, and selected-rule count. Work events are emitted outside RuleUID attribution.",
        "equation": "work_trace[kind 20..23] = scheduler_plan_completed arguments",
        "not_equivalent_to": ["rule matcher work", "host adapter work", "all scheduler work in the process"],
        "anchors": [anchor("scale_audit", "pub fn scheduler_plan_completed("),
                    anchor("scale_audit", "crate::access_trace::note_work(20,"),
                    anchor("access_trace", "pub struct WorkEvent")],
    },
    {
        "name": "deferred_queue_work",
        "meaning": "Recognized enqueue counts and between-pass drain batches/items; drained items include stale or rejected records.",
        "equation": "enqueue_total and drained_item_total are separate; equality is not guaranteed across pending queues or early exits",
        "not_equivalent_to": ["host callbacks", "all post-rule effects", "successful mutations"],
        "anchors": [anchor("scale_audit", "pub fn deferred_queue_enqueued("),
                    anchor("scale_audit", "pub fn deferred_queue_drained(")],
    },
    {
        "name": "concrete_access_events",
        "meaning": "Selected access/effect rows with concrete graph identities; successful match-edge rows occur only after a complete successful binding.",
        "equation": "no exact equation to candidate_tests; candidate rejects and failed edge identities are not represented by successful pattern_edge rows",
        "not_equivalent_to": ["complete dynamic dependency set", "candidate_tests", "all Term/helper graph reads"],
        "anchors": [anchor("rewrite", "crate::access_trace::note(1, src.0, edge.edge_type.0, tgt.0)"),
                    anchor("access_trace", "pub const NO_ID: u32 = u32::MAX;")],
    },
    {
        "name": "host_callback_work",
        "meaning": "UseTool dispatch crosses into a registered Python callback; callback reads, writes, and external effects are not native concrete graph-access events.",
        "equation": "requires an explicit host-side invocation/result counter; no equation is available from native access rows alone",
        "not_equivalent_to": ["graph mutations", "rule progress", "native trace event count"],
        "anchors": [anchor("term", "crate::tools::call_tool(name, &arg_vals, ctx.interner)")],
    },
]


def main() -> None:
    payload = {
        "schema_version": 1,
        "run_id": OUT.stem,
        "claim_boundary": "Source-linked counter semantics and justified counter distinctions; no dynamic calibration, runtime coverage percentage, or completeness claim.",
        "source_sha256": {key: sha(path) for key, path in SOURCES.items()},
        "counters": COUNTERS,
        "uncovered_cost_classes": [
            "host callbacks and callback-internal reads/writes",
            "adapter/boot work outside the captured run_rules operation",
            "failed matcher identities and rejected-edge dependencies",
            "some specialized Term scans and helper-mediated graph reads",
            "unchanged SetAttrIfDifferent old-value reads",
            "post-rule effects without a recognized deferred-queue hook",
        ],
        "next_dynamic_gate": "Use controlled graphs with independently known candidate, where, binding, scheduler-slot, queue, and callback counts; verify each counter separately, include negative/no-op/rejected controls, and capture uninstrumented semantic parity. Keep host/scheduler totals outside RuleUID traces.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT), "counter_classes": len(COUNTERS),
                      "source_sha256": payload["source_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
