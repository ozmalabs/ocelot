#!/usr/bin/env python3
"""Static inventory of public TypedGraph mutable methods and revision/journal hooks.

This checks source wiring only. It is not a dynamic mutation-coverage proof.
"""
from __future__ import annotations
import hashlib, json, re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "runners/dsl/src/graph.rs"
OUT = ROOT / "evaluation/reports/thoughtexperiment_tracked_mutations_v1_20261004.json"
EXPECTED = {
    "clear_experiment_observers": "observer_control",
    "declare_attr_index": "derived_index",
    "begin_mutation_log": "journal_control",
    "enable_rule_write_attribution": "journal_control",
    "begin_rule_write_event": "journal_control",
    "begin_rule_write_event_origins": "journal_control",
    "finish_rule_write_event": "journal_control",
    "begin_experiment_delta_log": "journal_control",
    "checkpoint_experiment_delta_log": "journal_control",
    "finish_mutation_log": "journal_control",
    "set_focus_edge_scope": "revision_tracked_scope",
    "node_mut": "semantic_node_write",
    "insert_node": "semantic_node_write",
    "insert_edge": "semantic_edge_write",
    "delete_edge": "semantic_edge_write",
    "delete_edges_batch": "semantic_edge_write",
    "edge_attrs_mut": "semantic_edge_write",
    "delete_node": "semantic_node_write",
    "set_node_attr": "semantic_node_write",
    "remove_node_attr": "semantic_node_write",
    "set_node_type": "semantic_node_write",
    "restore_node": "semantic_node_write",
    "restore_edge": "semantic_edge_write",
}
HOOKS = {
    "node_mut": ("bump_mutation_version", "log_node_mutation"),
    "insert_node": ("bump_mutation_version", "log_node_added"),
    "insert_edge": ("bump_mutation_version", "log_edge_before", "log_edge_mutation"),
    "delete_edge": ("bump_mutation_version", "log_edge_before", "log_edge_mutation"),
    "delete_edges_batch": ("bump_mutation_version", "log_edge_before", "log_edge_mutation"),
    "edge_attrs_mut": ("bump_mutation_version", "log_edge_before", "log_edge_mutation"),
    "delete_node": ("bump_mutation_version", "log_node_mutation", "delete_edges_batch"),
    "set_node_attr": ("node_mut",),
    "remove_node_attr": ("node_mut",),
    "set_node_type": ("node_mut",),
    "restore_node": ("bump_mutation_version", "log_node_mutation", "log_node_added"),
    "restore_edge": ("insert_edge",),
    "set_focus_edge_scope": ("bump_mutation_version",),
}
def sha(p: Path) -> str: return hashlib.sha256(p.read_bytes()).hexdigest()
def main() -> int:
    source = SOURCE.read_text()
    start = source.index("impl TypedGraph {")
    end = source.index("\nimpl Default for TypedGraph", start)
    block = source[start:end]
    matches = list(re.finditer(r"(?m)^\s{4}pub(?:\([^)]*\))?\s+fn\s+(\w+)\s*\(", block))
    rows = []
    for i, m in enumerate(matches):
        seg = block[m.start():matches[i + 1].start() if i + 1 < len(matches) else len(block)]
        body_start = seg.find("{")
        signature = seg[:body_start if body_start >= 0 else min(len(seg), 1200)]
        if "&mut self" not in signature:
            continue
        name = m.group(1); cls = EXPECTED.get(name, "unclassified")
        required = HOOKS.get(name, ())
        rows.append({"method": name, "class": cls, "line": source[:start + m.start()].count("\n") + 1,
                     "required_hooks": list(required), "present_hooks": [h for h in required if h in seg],
                     "hooks_complete": all(h in seg for h in required)})
    observed = {r["method"]: r["class"] for r in rows}
    errors = []
    if observed != EXPECTED:
        errors.append({"expected": EXPECTED, "observed": observed})
    incomplete = [r["method"] for r in rows if not r["hooks_complete"]]
    if incomplete: errors.append({"incomplete_hook_methods": incomplete})
    result = {"schema": "ThoughtexperimentTrackedMutationsV1", "passed": not errors,
              "scope": "Public TypedGraph methods whose signatures take &mut self, within the main impl block.",
              "source": str(SOURCE.relative_to(ROOT)), "source_sha256": sha(SOURCE),
              "audit_script_sha256": sha(Path(__file__)), "method_count": len(rows),
              "class_counts": {c: sum(r["class"] == c for r in rows) for c in sorted(set(r["class"] for r in rows))},
              "rows": rows, "errors": errors,
              "claim_boundary": "Static source wiring audit only. It does not execute every path, cover unsafe aliasing, concurrency, interior mutation, or prove completeness beyond the enumerated public method list."}
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"passed": result["passed"], "method_count": len(rows), "class_counts": result["class_counts"], "errors": errors, "source_sha256": result["source_sha256"]}, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1
if __name__ == "__main__": raise SystemExit(main())
