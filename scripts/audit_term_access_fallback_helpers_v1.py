#!/usr/bin/env python3
"""Triage helper-linked Terms that use the generic child-walk fallback.

This source scan records narrow lexical evidence only. It does not prove the
absence of indirect graph or host dependencies.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "evaluation/reports/term_access_dependency_coverage_v1_20260928.json"
OUT = ROOT / "evaluation/reports/term_access_fallback_helper_review_v1_20260928.json"
GRAPH_MARKER = re.compile(r"\bctx\.graph\b|\bgraph\.(?:node|nodes|nodes_of_type|nodes_where|edge|edges|out_edges|in_edges|neighbours|edge_idx|iter_nodes)\b")


def source_fn(source: str, name: str) -> tuple[str, int] | None:
    pattern = re.compile(rf"(?m)^(?:pub(?:\([^)]*\))?\s+)?fn\s+{re.escape(name)}\s*\(")
    match = pattern.search(source)
    if not match:
        return None
    # Function braces are balanced while ignoring quoted strings and comments
    # only approximately; retain lexical-only status in the output contract.
    brace = source.find("{", match.end())
    depth = 0
    end = None
    for i in range(brace, len(source)):
        if source[i] == "{":
            depth += 1
        elif source[i] == "}":
            depth -= 1
            if depth == 0:
                end = i + 1
                break
    if end is None:
        return None
    return source[match.start():end], source[:match.start()].count("\n") + 1


def main() -> None:
    inventory = json.loads(INVENTORY.read_text())
    rows = [r for r in inventory["rows"]
            if r["access_class"] == "generic_children_fallback" and r["evaluator_helpers"]]
    term_source = (ROOT / "runners/dsl/src/term.rs").read_text()
    evidence = {h["path"]: h for h in inventory["helper_evidence"]}
    reviewed = []
    for row in rows:
        helpers = []
        for path in row["evaluator_helpers"]:
            prior = evidence.get(path, {})
            rel = prior.get("source_path")
            if not rel:
                helpers.append({"path": path, "source_found": False})
                continue
            src_path = ROOT / rel
            source = src_path.read_text()
            name = path.split("::")[-1]
            found = source_fn(source, name)
            if not found:
                helpers.append({"path": path, "source_found": False, "source_path": rel})
                continue
            body, line = found
            helpers.append({
                "path": path,
                "source_found": True,
                "source_path": rel,
                "source_line": line,
                "source_sha256": hashlib.sha256(body.encode()).hexdigest(),
                "lexical_graph_access_marker": bool(GRAPH_MARKER.search(body)),
                "evaluates_child_terms": bool(re.search(r"\bevaluate\s*\(\s*arena", body)),
                "reads_interner": bool(re.search(r"ctx\.interner", body)),
                "reads_derived_registry": bool(re.search(r"ctx\.derived_ops", body)),
            })
        arm = re.search(rf"(?m)^        TermNode::{re.escape(row['variant'])}\b", term_source)
        reviewed.append({
            "variant": row["variant"],
            "term_line": row["enum_line"],
            "evaluator_arm_line": row["evaluator_arm_line"],
            "access_class": row["access_class"],
            "evaluator_arm_found": bool(arm),
            "helper_evidence": helpers,
        })
    report = {
        "audit_id": "term_access_fallback_helper_review_v1_20260928",
        "source_inputs": {
            "crosswalk": str(INVENTORY.relative_to(ROOT)),
            "crosswalk_sha256": hashlib.sha256(INVENTORY.read_bytes()).hexdigest(),
        },
        "counts": {
            "generic_fallback_variants": sum(r["access_class"] == "generic_children_fallback" for r in inventory["rows"]),
            "helper_linked_fallback_variants": len(reviewed),
            "helper_paths": sum(len(r["helper_evidence"]) for r in reviewed),
            "source_found_paths": sum(h.get("source_found", False) for r in reviewed for h in r["helper_evidence"]),
            "lexical_graph_markers": sum(h.get("lexical_graph_access_marker", False) for r in reviewed for h in r["helper_evidence"]),
            "helpers_evaluating_child_terms": sum(h.get("evaluates_child_terms", False) for r in reviewed for h in r["helper_evidence"]),
            "helpers_reading_interner": sum(h.get("reads_interner", False) for r in reviewed for h in r["helper_evidence"]),
            "helpers_reading_derived_registry": sum(h.get("reads_derived_registry", False) for r in reviewed for h in r["helper_evidence"]),
        },
        "claim_boundary": "Triage only for the 21 helper-linked generic-fallback variants. Lexical source spans and markers do not prove absence of indirect graph, host, macro, or callback dependencies; most variants in the 191-row fallback group are not covered by this review. Child Terms evaluated inside helpers still depend on correct recursive child enumeration.",
        "rows": reviewed,
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), **report["counts"]}, sort_keys=True))


if __name__ == "__main__":
    main()
