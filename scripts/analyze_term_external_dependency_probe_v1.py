#!/usr/bin/env python3
"""Independent outcome and provenance checks for external dependency probe v1."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import copy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/term_external_dependency_probe_v1_20260928.json"
LOCK = ROOT / "evaluation/substrate_capability/term_external_dependency_probe_v1_lock_20260928.json"
OUT = ROOT / "evaluation/reports/term_external_dependency_probe_v1_analysis_20260928.json"
SOURCE_PATHS = (
    "runners/dsl/src/term.rs", "runners/dsl/src/rewrite.rs", "runners/dsl/src/py.rs",
    "runners/dsl/src/tools.rs", "runners/dsl/src/prog_eval.rs",
    "runners/dsl/python/substrate_rs/__init__.py",
    "scripts/substrate_term_external_dependency_probe_v1.py",
    "scripts/analyze_term_external_dependency_probe_v1.py",
    "docs/research/engine_substrate/SUBSTRATE_TERM_EXTERNAL_DEPENDENCY_PROBE_V1_PREREG_20260928.md",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def current_inputs() -> dict:
    # Resolve the actual extension selected by the active Python import path.
    sys.path[:0] = [str(ROOT / "runners/dsl/python")]
    import substrate_rs._native as native
    ext_path = Path(native.__file__).resolve()
    return {
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "source_sha256": {name: sha(ROOT / name) for name in SOURCE_PATHS},
        "native_extension_path": str(ext_path),
        "native_extension_sha256": sha(ext_path),
        "native_build_manifest_sha256": sha(ROOT / "runners/dsl/python/substrate_rs/_native.build.json"),
    }


def result(cell: dict):
    nodes = cell["graph"]["nodes"]
    for node in nodes:
        if node["id"] == 1:
            return node.get("attrs", {}).get("result", "__missing__")
    return "__node_missing__"


def text_result(cell: dict):
    value = result(cell)
    if isinstance(value, dict) and value.get("kind") == "text":
        return bytes.fromhex(value["payload"]).decode("utf-8")
    return None


def dispatch_count(cell: dict) -> int:
    return sum(int(row[-1]) for row in cell["trace_rows"] if row[1] == "term_tool_dispatch")


def main() -> None:
    raw = json.loads(RAW.read_text())
    lock = json.loads(LOCK.read_text())
    runs = raw["runs"]
    def child_stream_matches(run: dict) -> bool:
        child = run.get("child_process", {})
        payload = copy.deepcopy(run)
        payload.pop("child_process", None)
        encoded = (json.dumps(payload, sort_keys=True) + "\n").encode()
        return (
            child.get("return_code") == 0
            and child.get("stdout_sha256") == hashlib.sha256(encoded).hexdigest()
            and child.get("stderr_sha256") == hashlib.sha256(b"").hexdigest()
            and len(child.get("argv", [])) == 4
        )
    names = {c["name"] for run in runs for c in run["cells"]}
    cells = {name: [c for run in runs for c in run["cells"] if c["name"] == name] for name in names}
    checks = {
        "three_unique_fresh_workers": len(runs) == 3 and len({r["pid"] for r in runs}) == 3,
        "worker_inputs_match_lock": all(r["started_inputs"] == lock["locked_inputs"] for r in runs),
        "child_commands_and_stream_hashes_verify": all(child_stream_matches(r) for r in runs),
        "current_sources_match_lock": current_inputs() == lock["locked_inputs"] == raw["locked_inputs"],
        "expected_six_cells_each_worker": all(len(r["cells"]) == 6 for r in runs),
        "file_content_changes_output_without_static_graph_dependency": all(
            text_result(c) == expected
            and c["static_access"]["reads"] == ["edge:trigger"]
            and not c["static_access"]["reads_any"]
            for expected, key in (("alpha", "file_alpha"), ("beta", "file_beta"))
            for c in cells.get(key, [])
        ),
        "file_cells_have_no_file_trace_event": all(
            not any("file" in str(row[1]).lower() for row in c["trace_rows"])
            for key in ("file_alpha", "file_beta", "file_missing") for c in cells.get(key, [])
        ),
        "missing_file_returns_none": all(result(c) is None for c in cells.get("file_missing", [])),
        "tool_static_scope_is_wildcard": all(c["static_access"]["reads_any"] for key in ("tool_traced", "tool_untraced", "tool_missing") for c in cells.get(key, [])),
        "registered_tool_fires_twice_and_result_is_stable": all(
            c["callback_invocations"] == c["native_fire_delta"] == 2
            and text_result(c) == "fixed-result" and c["progress"] == 1
            for key in ("tool_traced", "tool_untraced") for c in cells.get(key, [])
        ),
        "tool_dispatch_trace_matches_callbacks": all(dispatch_count(c) == 2 for c in cells.get("tool_traced", [])),
        "disabled_trace_preserves_calls_and_suppresses_rows": all(
            c["callback_invocations"] == 2 and not c["trace_rows"] for c in cells.get("tool_untraced", [])
        ),
        "missing_handler_fallback_and_dispatch_trace": all(
            c["callback_invocations"] == 0 and c["native_fire_delta"] == 0
            and result(c) == 0 and dispatch_count(c) == 2
            for c in cells.get("tool_missing", [])
        ),
        "no_trace_rows_dropped": all(c["trace_dropped"] == 0 for run in runs for c in run["cells"]),
        "all_cells_progress_once": all(c["progress"] == 1 for run in runs for c in run["cells"]),
    }
    report = {
        "analysis_id": "term_external_dependency_probe_v1_analysis_20260928",
        "raw_sha256": sha(RAW), "lock_sha256": sha(LOCK),
        "checks": checks,
        "summary": {
            "workers": len(runs),
            "cells": len(runs[0]["cells"]) if runs else 0,
            "registered_tool_callback_invocations": [c["callback_invocations"] for c in cells.get("tool_traced", [])],
            "registered_tool_dispatch_event_counts": [dispatch_count(c) for c in cells.get("tool_traced", [])],
            "file_alpha_result": [text_result(c) for c in cells.get("file_alpha", [])],
            "file_beta_result": [text_result(c) for c in cells.get("file_beta", [])],
        },
        "claim_boundary": "The checks validate only the preregistered synthetic fixtures. They do not establish containment, safety, natural callback frequency, or complete access-trace coverage.",
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks": checks, "output": str(OUT.relative_to(ROOT))}, sort_keys=True))
    if not all(checks.values()):
        raise SystemExit("external dependency probe analysis failed")


if __name__ == "__main__":
    main()
