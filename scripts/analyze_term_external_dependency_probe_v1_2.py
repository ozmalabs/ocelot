#!/usr/bin/env python3
"""Independent analyzer for the v1.2 predicate/nesting callback probe."""
from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/term_external_dependency_probe_v1_2_20260928.json"
LOCK = ROOT / "evaluation/substrate_capability/term_external_dependency_probe_v1_2_lock_20260928.json"
OUT = ROOT / "evaluation/reports/term_external_dependency_probe_v1_2_analysis_20260928.json"
SOURCE_PATHS = (
    "runners/dsl/src/term.rs", "runners/dsl/src/rewrite.rs", "runners/dsl/src/py.rs",
    "runners/dsl/src/tools.rs", "runners/dsl/python/substrate_rs/__init__.py",
    "scripts/substrate_term_external_dependency_probe_v1_2.py",
    "scripts/analyze_term_external_dependency_probe_v1_2.py",
    "docs/research/engine_substrate/SUBSTRATE_TERM_EXTERNAL_DEPENDENCY_PROBE_V1_2_PREREG_20260928.md",
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


def dispatch_by_rule(cell: dict) -> dict[int, int]:
    out: dict[int, int] = {}
    for row in cell["trace_rows"]:
        if row[1] == "term_tool_dispatch":
            uid = int(row[0])
            out[uid] = out.get(uid, 0) + int(row[-1])
    return out


def target_attrs(cell: dict) -> dict:
    node = next((n for n in cell["graph"]["nodes"] if n["id"] == 1), {})
    return node.get("attrs", {})


def cell_signature(cell: dict) -> str:
    normalized = copy.deepcopy(cell)
    for rule in normalized["rules"]:
        rule.pop("rule_uid", None)
        rule.pop("rule_idx", None)
    normalized["trace_rows"] = [row[1:] for row in normalized["trace_rows"]]
    return json.dumps(normalized, sort_keys=True)


def main() -> None:
    raw = json.loads(RAW.read_text())
    lock = json.loads(LOCK.read_text())
    runs = raw["runs"]
    cells = {name: [c for run in runs for c in run["cells"] if c["name"] == name]
             for name in ("direct_true", "short_circuit_before", "short_circuit_after", "two_rules", "stateful_predicate")}

    def exact_cell(name: str, calls: list[dict], progress: int, markers: dict[str, int], rule_calls: list[int]) -> bool:
        matches = cells[name]
        for c in matches:
            uids = [int(r["rule_uid"]) for r in c["rules"]]
            attrs = target_attrs(c)
            if c["callback_log"] != calls or c["progress"] != progress:
                return False
            if c["native_fire_delta"] != len(calls) or c["callback_invocations"] != len(calls):
                return False
            if any(attrs.get(k) != v for k, v in markers.items()):
                return False
            if any((k in attrs) for k in ("marker_0", "marker_1") if k not in markers):
                return False
            dispatch = dispatch_by_rule(c)
            if [dispatch.get(uid, 0) for uid in uids] != rule_calls:
                return False
            if c["trace_dropped"] != 0 or any(not r["static_access"]["reads_any"] for r in c["rules"]):
                return False
        return len(matches) == 3

    expected_fixed = [{"arg": "payload", "return": True}, {"arg": "payload", "return": True}]
    checks = {
        "three_unique_fresh_workers": len(runs) == 3 and len({r["pid"] for r in runs}) == 3,
        "worker_inputs_match_lock": all(r["started_inputs"] == lock["locked_inputs"] for r in runs),
        "current_inputs_match_lock_and_raw": current_inputs() == lock["locked_inputs"] == raw["locked_inputs"],
        "child_command_stream_hashes_verify": all(
            r.get("child_process", {}).get("return_code") == 0
            and r["child_process"].get("stderr_sha256") == hashlib.sha256(b"").hexdigest()
            and r["child_process"].get("stdout_sha256") == hashlib.sha256((json.dumps({k: v for k, v in r.items() if k != "child_process"}, sort_keys=True) + "\n").encode()).hexdigest()
            for r in runs
        ),
        "five_cells_per_worker": all(len(r["cells"]) == 5 for r in runs),
        "direct_predicate_matches_frozen_behavior": exact_cell("direct_true", expected_fixed, 1, {"marker_0": 1}, [2]),
        "false_before_callback_short_circuits": exact_cell("short_circuit_before", [], 0, {}, [0]),
        "false_after_callback_runs_then_rejects": exact_cell("short_circuit_after", [{"arg": "payload", "return": True}], 0, {}, [1]),
        "two_rules_have_per_rule_callback_counts": exact_cell("two_rules", expected_fixed * 2, 2, {"marker_0": 1, "marker_1": 1}, [2, 2]),
        "stateful_predicate_keeps_first_true_effect": exact_cell("stateful_predicate", [{"arg": "payload", "return": True}, {"arg": "payload", "return": False}], 1, {"marker_0": 1}, [2]),
        "outcomes_replicate_exactly_across_workers": all(
            len({cell_signature(c) for c in cells[name]}) == 1 for name in cells
        ),
    }
    summary = {}
    for name, samples in cells.items():
        summary[name] = {
            "callback_returns": [[x["return"] for x in c["callback_log"]] for c in samples],
            "callback_invocations": [c["callback_invocations"] for c in samples],
            "dispatch_by_rule_uid": [dispatch_by_rule(c) for c in samples],
            "progress": [c["progress"] for c in samples],
            "final_target_attrs": [target_attrs(c) for c in samples],
        }
    report = {
        "analysis_id": "term_external_dependency_probe_v1_2_analysis_20260928",
        "raw_sha256": sha(RAW), "lock_sha256": sha(LOCK),
        "checks": checks, "summary": summary,
        "claim_boundary": "Confirms only these short-circuit, one-binding and two-rule fixtures; no general callback or side-effect semantics claim.",
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks": checks, "summary": summary, "output": str(OUT.relative_to(ROOT))}, sort_keys=True))
    if not all(checks.values()):
        raise SystemExit("v1.2 external dependency analysis failed")


if __name__ == "__main__":
    main()
