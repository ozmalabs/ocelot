#!/usr/bin/env python3
"""Lexically census generic-fallback evaluator arms without crate helpers."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "evaluation/reports/term_access_dependency_coverage_v1_20260928.json"
TERM = ROOT / "runners/dsl/src/term.rs"
OUT = ROOT / "evaluation/reports/term_access_fallback_unlinked_v1_20260928.json"
MARKERS = {
    "graph_api": re.compile(r"\bctx\.graph\b|\bgraph\.(?:node|nodes|nodes_of_type|nodes_where|edge|edges|out_edges|in_edges|neighbours|edge_idx|iter_nodes)\b"),
    "host_io_or_callback": re.compile(r"std::(?:fs|process|net)::|Python::with_gil|\bcall_tool\b"),
    "trace_site": re.compile(r"access_trace::note\s*\(|access_trace::note_(?:out|in)_edges\s*\("),
    "dynamic_eval_context": re.compile(r"ctx\.(?:derived_ops|concepts|tools|external)\b"),
}


def main() -> None:
    inv = json.loads(INVENTORY.read_text())
    path = TERM
    source = path.read_text()
    eval_start = source.index("pub fn evaluate(")
    eval_end = source.index("fn python_repr(", eval_start)
    body = source[eval_start:eval_end]
    body_lines = body.splitlines()
    arm_starts = [i for i, line in enumerate(body_lines) if re.match(r"^        TermNode::[A-Za-z0-9_]+", line)]
    unlinked = [r for r in inv["rows"] if r["access_class"] == "generic_children_fallback" and not r["evaluator_helpers"]]
    rows = []
    for item in unlinked:
        index = item["evaluator_arm_line"] - (source[:eval_start].count("\n") + 1)
        following = next((i for i in arm_starts if i > index), len(body_lines))
        arm = "\n".join(body_lines[index:following])
        markers = {key: bool(pattern.search(arm)) for key, pattern in MARKERS.items()}
        rows.append({
            "variant": item["variant"],
            "evaluator_arm_line": item["evaluator_arm_line"],
            "source_sha256": hashlib.sha256(arm.encode()).hexdigest(),
            "lexical_markers": markers,
            "recursive_evaluate_calls": len(re.findall(r"\bevaluate\s*\(\s*arena", arm)),
            "external_boundary_class": item["external_dependency"],
        })
    report = {
        "audit_id": "term_access_fallback_unlinked_v1_20260928",
        "input_crosswalk_sha256": hashlib.sha256(INVENTORY.read_bytes()).hexdigest(),
        "source_sha256": hashlib.sha256(source.encode()).hexdigest(),
        "counts": {
            "generic_fallback_variants_without_detected_crate_helpers": len(rows),
            "variants_with_graph_api_marker": sum(r["lexical_markers"]["graph_api"] for r in rows),
            "variants_with_host_io_or_callback_marker": sum(r["lexical_markers"]["host_io_or_callback"] for r in rows),
            "variants_with_trace_marker": sum(r["lexical_markers"]["trace_site"] for r in rows),
            "variants_with_dynamic_eval_context_marker": sum(r["lexical_markers"]["dynamic_eval_context"] for r in rows),
            "variants_with_recursive_evaluate_call": sum(r["recursive_evaluate_calls"] > 0 for r in rows),
        },
        "claim_boundary": "Lexical census of source spans selected by the v1 crosswalk. It detects only the listed spellings and does not prove graph purity, effect purity, complete child enumeration, or absence of indirect calls, aliases, macros, function pointers, or host state. Rows are triage evidence, not a sound call graph.",
        "rows": rows,
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), **report["counts"]}, sort_keys=True))


if __name__ == "__main__":
    main()
