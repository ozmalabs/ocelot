#!/usr/bin/env python3
"""Triage capability-map test links for direct callable-name exercise.

This is intentionally a static, lexical audit. A callable-name match is only
a candidate invocation (aliases, dispatch, fixtures, and runtime reachability
need manual review); no match does not imply a test is irrelevant.
"""
from __future__ import annotations

import ast
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAP = ROOT / "evaluation/substrate_capability/capability_map.json"
OUT = ROOT / "evaluation/reports/substrate_test_reference_triage_20260928.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def call_names(path: Path) -> tuple[set[str], str | None]:
    try:
        tree = ast.parse(path.read_text(errors="replace"), filename=str(path))
    except (OSError, SyntaxError) as exc:
        return set(), f"{type(exc).__name__}: {exc}"
    names = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        function = node.func
        if isinstance(function, ast.Attribute):
            names.add(function.attr)
        elif isinstance(function, ast.Name):
            names.add(function.id)
    return names, None


def build() -> dict:
    capability_map = json.loads(MAP.read_text())
    rows = []
    for capability in capability_map["capabilities"]:
        audit = capability.get("entrypoint_audit", {})
        audited_names = sorted({
            entry["symbol"].split("::")[-1]
            for group in ("normal_entrypoints", "alternate_entrypoints")
            for entry in audit.get(group, [])
            if entry.get("symbol")
        })
        tests = []
        for ref in capability.get("test_refs", []):
            path = (ROOT / "docs/research/engine_substrate" / ref).resolve()
            names, error = call_names(path)
            tests.append({
                "ref": ref,
                "sha256": sha256(path) if path.is_file() else None,
                "exists": path.is_file(),
                "parse_error": error,
                "candidate_direct_callable_names": sorted(names.intersection(audited_names)),
                "audited_callable_names": audited_names,
            })
        rows.append({
            "capability_id": capability["id"],
            "tests": tests,
            "candidate_direct_call_file_count": sum(
                bool(test["candidate_direct_callable_names"]) for test in tests),
            "linked_test_file_count": len(tests),
        })
    return {
        "schema": "substrate_test_reference_triage.v1",
        "method": "Python AST call-name intersection against audited callable leaf names",
        "claim_boundary": (
            "Triage only: name matches do not prove that the call reaches the "
            "named substrate path; no match does not prove irrelevance. "
            "Manual test-to-path review remains required."),
        "capability_map_sha256": sha256(MAP),
        "capability_count": len(rows),
        "linked_test_file_count": sum(row["linked_test_file_count"] for row in rows),
        "candidate_direct_call_file_count": sum(
            row["candidate_direct_call_file_count"] for row in rows),
        "capabilities": rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=OUT,
        help="report destination (defaults to the historical 2026-09-28 path)")
    args = parser.parse_args()
    report = build()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "report": str(args.output.resolve().relative_to(ROOT)),
        "capabilities": report["capability_count"],
        "linked_test_files": report["linked_test_file_count"],
        "candidate_direct_call_files": report["candidate_direct_call_file_count"],
        "claim_boundary": report["claim_boundary"],
    }, indent=2))


if __name__ == "__main__":
    main()
