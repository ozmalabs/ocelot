#!/usr/bin/env python3
"""Independent analyzer for stateful callback order/replay probe v1.3."""
from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "evaluation/reports/term_external_dependency_probe_v1_3_20260928.json"
LOCK = ROOT / "evaluation/substrate_capability/term_external_dependency_probe_v1_3_lock_20260928.json"
OUT = ROOT / "evaluation/reports/term_external_dependency_probe_v1_3_analysis_20260928.json"
SOURCE_PATHS = (
    "runners/dsl/src/term.rs", "runners/dsl/src/rewrite.rs", "runners/dsl/src/py.rs",
    "runners/dsl/src/tools.rs", "runners/dsl/python/substrate_rs/__init__.py",
    "scripts/substrate_term_external_dependency_probe_v1_3.py",
    "scripts/analyze_term_external_dependency_probe_v1_3.py",
    "docs/research/engine_substrate/SUBSTRATE_TERM_EXTERNAL_DEPENDENCY_PROBE_V1_3_PREREG_20260928.md",
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


def dispatch_by_rule(settle: dict) -> dict[int, int]:
    result: dict[int, int] = {}
    for row in settle["trace_rows"]:
        if row[1] == "term_tool_dispatch":
            uid = int(row[0])
            result[uid] = result.get(uid, 0) + int(row[-1])
    return result


def target_attrs(settle: dict) -> dict:
    node = next((n for n in settle["graph"]["nodes"] if n["id"] == 1), {})
    return node.get("attrs", {})


def stable_signature(schedule: dict) -> str:
    normalized = copy.deepcopy(schedule)
    for rule in normalized["rules"]:
        rule.pop("rule_uid", None)
        rule.pop("rule_idx", None)
    for settle_key in ("first_settle", "second_settle_after_external_state_reset"):
        settle = normalized[settle_key]
        settle["trace_rows"] = [row[1:] for row in settle["trace_rows"]]
    return json.dumps(normalized, sort_keys=True)


def schedule_gate(schedule: dict, order: list[str]) -> bool:
    if schedule["insertion_order"] != order:
        return False
    records = schedule["rules"]
    if [r["name"] for r in records] != order or any(r["reads"] != ["edge:trigger"] or not r["reads_any"] for r in records):
        return False
    first, second = schedule["first_settle"], schedule["second_settle_after_external_state_reset"]
    first_uids = [int(r["rule_uid"]) for r in records]
    if first["callback_log"] != [
        {"arg": "payload", "return": True},
        {"arg": "payload", "return": False},
        {"arg": "payload", "return": False},
    ]:
        return False
    if first["progress"] != 1 or first["native_fire_delta"] != 3 or first["trace_dropped"] != 0:
        return False
    if dispatch_by_rule(first) != {first_uids[0]: 2, first_uids[1]: 1}:
        return False
    attrs = target_attrs(first)
    if attrs != {order[0]: 1}:
        return False
    if second["progress"] != 0 or second["callback_log"] or second["native_fire_delta"] != 0:
        return False
    if second["trace_rows"] or second["trace_dropped"] != 0 or second["graph"] != first["graph"]:
        return False
    return True


def main() -> None:
    raw = json.loads(RAW.read_text())
    lock = json.loads(LOCK.read_text())
    runs = raw["runs"]
    schedules = [s for r in runs for s in r["schedules"]]
    by_order = {
        "rule_a_then_b": [s for s in schedules if s["insertion_order"] == ["rule_a", "rule_b"]],
        "rule_b_then_a": [s for s in schedules if s["insertion_order"] == ["rule_b", "rule_a"]],
    }

    def child_hashes_ok(run: dict) -> bool:
        meta = run.get("child_process", {})
        copy_run = copy.deepcopy(run)
        copy_run.pop("child_process", None)
        stream = (json.dumps(copy_run, sort_keys=True) + "\n").encode()
        return (meta.get("return_code") == 0
                and meta.get("stdout_sha256") == hashlib.sha256(stream).hexdigest()
                and meta.get("stderr_sha256") == hashlib.sha256(b"").hexdigest())

    checks = {
        "three_unique_fresh_workers": len(runs) == 3 and len({r["pid"] for r in runs}) == 3,
        "worker_inputs_match_lock": all(r["started_inputs"] == lock["locked_inputs"] for r in runs),
        "current_inputs_match_lock_and_raw": current_inputs() == lock["locked_inputs"] == raw["locked_inputs"],
        "child_commands_and_stream_hashes_verify": all(child_hashes_ok(r) for r in runs),
        "two_orders_per_worker": all(len(r["schedules"]) == 2 for r in runs),
        "a_then_b_schedule_matches_frozen_outcome": len(by_order["rule_a_then_b"]) == 3 and all(schedule_gate(s, ["rule_a", "rule_b"]) for s in by_order["rule_a_then_b"]),
        "b_then_a_schedule_matches_frozen_outcome": len(by_order["rule_b_then_a"]) == 3 and all(schedule_gate(s, ["rule_b", "rule_a"]) for s in by_order["rule_b_then_a"]),
        "rule_order_selects_winning_marker": all(target_attrs(s["first_settle"]) == {"rule_a": 1} for s in by_order["rule_a_then_b"]) and all(target_attrs(s["first_settle"]) == {"rule_b": 1} for s in by_order["rule_b_then_a"]),
        "within_schedule_results_replicate": all(len({stable_signature(s) for s in group}) == 1 for group in by_order.values()),
        "no_trace_drops": all(s[k]["trace_dropped"] == 0 for s in schedules for k in ("first_settle", "second_settle_after_external_state_reset")),
    }
    report = {
        "analysis_id": "term_external_dependency_probe_v1_3_analysis_20260928",
        "raw_sha256": sha(RAW), "lock_sha256": sha(LOCK),
        "checks": checks,
        "summary": {
            "rule_a_first_winner": [target_attrs(s["first_settle"]) for s in by_order["rule_a_then_b"]],
            "rule_b_first_winner": [target_attrs(s["first_settle"]) for s in by_order["rule_b_then_a"]],
            "first_settle_call_counts": [len(s["first_settle"]["callback_log"]) for s in schedules],
            "second_settle_call_counts_after_external_reset": [len(s["second_settle_after_external_state_reset"]["callback_log"]) for s in schedules],
        },
        "claim_boundary": "The result covers only this two-rule shared callback fixture and replay schedule; it does not establish general scheduler ordering or external-effect semantics.",
    }
    OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks": checks, "summary": report["summary"], "output": str(OUT.relative_to(ROOT))}, sort_keys=True))
    if not all(checks.values()):
        raise SystemExit("v1.3 external dependency analysis failed")


if __name__ == "__main__":
    main()
