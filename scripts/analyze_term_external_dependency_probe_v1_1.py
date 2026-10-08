#!/usr/bin/env python3
"""Independent analysis of the external dependency cardinality panel."""
from __future__ import annotations

import copy
import hashlib
import json
import statistics
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/term_external_dependency_probe_v1_1_20260928.json"
LOCK = ROOT / "evaluation/substrate_capability/term_external_dependency_probe_v1_1_lock_20260928.json"
OUT = ROOT / "evaluation/reports/term_external_dependency_probe_v1_1_analysis_20260928.json"
SOURCE_PATHS = (
    "runners/dsl/src/term.rs", "runners/dsl/src/rewrite.rs", "runners/dsl/src/py.rs",
    "runners/dsl/src/tools.rs", "runners/dsl/src/prog_eval.rs",
    "runners/dsl/python/substrate_rs/__init__.py",
    "scripts/substrate_term_external_dependency_probe_v1_1.py",
    "scripts/analyze_term_external_dependency_probe_v1_1.py",
    "docs/research/engine_substrate/SUBSTRATE_TERM_EXTERNAL_DEPENDENCY_PROBE_V1_1_PREREG_20260928.md",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def current_inputs() -> dict:
    sys.path[:0] = [str(ROOT / "runners/dsl/python")]
    import substrate_rs._native as native
    ext = Path(native.__file__).resolve()
    return {
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "source_sha256": {name: sha(ROOT / name) for name in SOURCE_PATHS},
        "native_extension_path": str(ext),
        "native_extension_sha256": sha(ext),
        "native_build_manifest_sha256": sha(ROOT / "runners/dsl/python/substrate_rs/_native.build.json"),
    }


def dispatch_count(cell: dict) -> int:
    return sum(int(row[-1]) for row in cell["trace_rows"] if row[1] == "term_tool_dispatch")


def result_for_target(cell: dict, target_id: int):
    node = next((n for n in cell["graph"]["nodes"] if n["id"] == target_id), None)
    return None if node is None else node.get("attrs", {})


def normalized_graph(cell: dict) -> dict:
    return cell["graph"]


def main() -> None:
    raw = json.loads(RAW.read_text())
    lock = json.loads(LOCK.read_text())
    runs = raw["runs"]
    all_cells = [cell for run in runs for cell in run["cells"]]
    by_key = {(c0, p0): [c for c in all_cells if (c["cardinality"], c["effect_position"]) == (c0, p0)]
              for c0 in (1, 2, 4) for p0 in ("first", "last")}

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

    checks = {
        "three_unique_fresh_workers": len(runs) == 3 and len({r["pid"] for r in runs}) == 3,
        "worker_inputs_match_lock": all(r["started_inputs"] == lock["locked_inputs"] for r in runs),
        "current_inputs_match_lock_and_raw": current_inputs() == lock["locked_inputs"] == raw["locked_inputs"],
        "child_command_and_stream_hashes_verify": all(child_stream_matches(r) for r in runs),
        "six_cells_per_worker": all(len(r["cells"]) == 6 for r in runs),
        "all_cardinality_position_cells_present": len(by_key) == 6 and all(len(v) == 3 for v in by_key.values()),
        "all_rules_have_trigger_read_and_wildcard": all(c["static_access"]["reads"] == ["edge:trigger"] and c["static_access"]["reads_any"] for c in all_cells),
        "callback_native_fire_trace_counts_conserve": all(c["callback_invocations"] == c["native_fire_delta"] == dispatch_count(c) for c in all_cells),
        "no_trace_rows_dropped": all(c["trace_dropped"] == 0 for c in all_cells),
        "callback_arguments_match_invocation_count": all(c["callback_args"] == ["payload"] * c["callback_invocations"] for c in all_cells),
        "positive_progress_and_elapsed_samples": all(c["progress"] > 0 and c["elapsed_ns"] > 0 for c in all_cells),
        "each_target_has_both_expected_values": all(
            all((attrs := result_for_target(c, target_id)).get("tool_result", {}).get("kind") == "text"
                and bytes.fromhex(attrs["tool_result"]["payload"]).decode("utf-8") == "fixed-result"
                and attrs.get("marker") == 1
                for target_id in c["target_ids"])
            and len(c["target_ids"]) == c["cardinality"]
            for c in all_cells
        ),
        "within_cell_worker_outcomes_replicate": all(
            len({(c["callback_invocations"], c["native_fire_delta"], dispatch_count(c), c["progress"], json.dumps(normalized_graph(c), sort_keys=True)) for c in samples}) == 1
            for samples in by_key.values()
        ),
        "effect_order_preserves_terminal_graph_per_cardinality": all(
            json.dumps(by_key[(m, "first")][i]["graph"], sort_keys=True) == json.dumps(by_key[(m, "last")][i]["graph"], sort_keys=True)
            for m in (1, 2, 4) for i in range(3)
        ),
    }
    summary = {}
    for (m, position), samples in by_key.items():
        summary[f"M={m},position={position}"] = {
            "callback_invocations": [c["callback_invocations"] for c in samples],
            "dispatch_events": [dispatch_count(c) for c in samples],
            "progress": [c["progress"] for c in samples],
            "elapsed_ns": [c["elapsed_ns"] for c in samples],
            "elapsed_ns_median_descriptive": statistics.median(c["elapsed_ns"] for c in samples),
            "calls_per_binding": [c["callback_invocations"] / m for c in samples],
        }
    report = {
        "analysis_id": "term_external_dependency_probe_v1_1_analysis_20260928",
        "raw_sha256": sha(RAW), "lock_sha256": sha(LOCK),
        "checks": checks,
        "summary_by_cell": summary,
        "claim_boundary": "Replication and mechanism accounting for six synthetic cells. Timing is descriptive, and observed callback scaling does not establish a general complexity bound or natural workload economics.",
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks": checks, "summary_by_cell": summary, "output": str(OUT.relative_to(ROOT))}, sort_keys=True))
    if not all(checks.values()):
        raise SystemExit("v1.1 external dependency analysis failed")


if __name__ == "__main__":
    main()
