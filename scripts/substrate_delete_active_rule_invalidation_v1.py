#!/usr/bin/env python3
"""Paired active-rule refresh probe after public node deletion."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python"), str(ROOT / "scripts")]
from substrate_rs import _native  # noqa: E402
from domains.engine_provenance import build_is_stale  # noqa: E402
from substrate_run_manifest import capture_run_manifest, finish_console_capture, start_console_capture  # noqa: E402

PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_DELETE_ACTIVE_RULE_INVALIDATION_V1_PREREG_20260928.md"
AMENDMENT = ROOT / "docs/research/engine_substrate/SUBSTRATE_DELETE_ACTIVE_RULE_INVALIDATION_V1_1_AMENDMENT_20260928.md"
LOCK = ROOT / "evaluation/substrate_capability/delete_active_rule_invalidation_v1_1_lock_20260928.json"
RAW = ROOT / "evaluation/reports/substrate_delete_active_rule_invalidation_v1_1_20260928.json"
RUN_ID = "substrate-delete-active-rule-invalidation-v1-1-20260928"
FILES = (
    "scripts/substrate_delete_active_rule_invalidation_v1.py",
    "scripts/analyze_substrate_delete_active_rule_invalidation_v1.py",
    "scripts/substrate_run_manifest.py",
    "domains/engine_provenance.py",
    "docs/research/engine_substrate/SUBSTRATE_DELETE_ACTIVE_RULE_INVALIDATION_V1_PREREG_20260928.md",
    "docs/research/engine_substrate/SUBSTRATE_DELETE_ACTIVE_RULE_INVALIDATION_V1_1_AMENDMENT_20260928.md",
    "runners/dsl/src/graph.rs", "runners/dsl/src/substrate.rs", "runners/dsl/src/py.rs",
    "runners/dsl/src/scale_audit.rs", "runners/dsl/python/substrate_rs/__init__.py",
    "runners/dsl/python/substrate_rs/_native.build.json", "runners/dsl/Cargo.toml", "runners/dsl/Cargo.lock",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprint() -> dict:
    native = Path(_native.__file__).resolve()
    return {"commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "files": {p: sha(ROOT / p) for p in FILES}, "native_path": str(native),
            "native_sha256": sha(native), "native_build_stale": build_is_stale(str(ROOT))}


def one_arm(precise: bool) -> dict:
    s = _native.Substrate()
    root = s.add_node("Root", {})
    target = s.add_node("Target", {})
    doomed = s.add_node("Doomed", {})
    s.add_edge_unchecked(root, "trigger", target, {})
    s.add_edge_unchecked(root, "watched", doomed, {})
    term = {"type": "Count", "source": {"type": "Edges", "node": {"type": "Var", "name": "x"}, "edge_type": "watched"}}
    rule_idx = s.add_rule({"name": "delete_invalidation_reader", "match": [["x", "trigger", "y"]],
                           "effects": [["set_attr", "y", "watched_count", {"__term__": term}]]})
    s.set_precise_dirty(precise)
    access = next(row for row in s.rule_access_sets() if row[0] == rule_idx)
    s.scale_audit_reset(); s.scale_audit_set_enabled(True)
    started = time.perf_counter_ns()
    initial_report = dict(s.run_rules_report(100, False))
    initial_wall = time.perf_counter_ns() - started
    initial_metrics = dict(s.scale_audit_snapshot())
    initial_value = s.node(target)["attrs"].get("watched_count")
    s.scale_audit_reset()
    removed = s.remove_node(doomed)
    started = time.perf_counter_ns()
    delete_report = dict(s.run_rules_report(100, False))
    settle_wall = time.perf_counter_ns() - started
    settle_metrics = dict(s.scale_audit_snapshot())
    final_value = s.node(target)["attrs"].get("watched_count")
    graph = s.graph_to_dict()
    s.scale_audit_set_enabled(False)
    return {"precise_dirty": precise, "rule_access": list(access), "initial_report": initial_report,
            "initial_wall_ns": initial_wall, "initial_metrics": initial_metrics, "initial_value": initial_value,
            "node_removed": removed, "delete_settle_report": delete_report, "delete_settle_wall_ns": settle_wall,
            "delete_settle_metrics": settle_metrics, "final_value": final_value,
            "independent_watched_count": sum(e["type"] == "watched" and e["src"] == root.value for e in graph["edges"]),
            "target_present": any(n["id"] == target.value for n in graph["nodes"]),
            "doomed_absent": all(n["id"] != doomed.value for n in graph["nodes"]),
            "remaining_edges": graph["edges"]}


def worker(rep: int) -> dict:
    before = fingerprint()
    default = one_arm(False)
    precise = one_arm(True)
    after = fingerprint()
    return {"replicate": rep, "pid": os.getpid(), "before": before, "after": after,
            "default": default, "precise": precise}


def main() -> int:
    if sys.argv[1:] == ["--lock"]:
        fp = fingerprint()
        if fp["native_build_stale"]: raise SystemExit("native build is stale")
        LOCK.parent.mkdir(parents=True, exist_ok=True); LOCK.write_text(json.dumps(fp, indent=2, sort_keys=True) + "\n")
        print(LOCK); return 0
    if len(sys.argv) == 3 and sys.argv[1] == "--worker":
        print(json.dumps(worker(int(sys.argv[2])), sort_keys=True)); return 0
    before = fingerprint()
    if before["native_build_stale"] or not LOCK.exists() or json.loads(LOCK.read_text()) != before:
        raise SystemExit("missing/stale source lock or native build")
    started = datetime.now(timezone.utc).isoformat(); log = start_console_capture(RUN_ID)
    env = dict(os.environ); env["PYTHONPATH"] = os.pathsep.join((str(ROOT), str(ROOT / "runners/dsl/python"), str(ROOT / "scripts"), env.get("PYTHONPATH", "")))
    rows = []
    for rep in range(3):
        cp = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker", str(rep)], cwd=ROOT,
                            env=env, text=True, capture_output=True, check=True)
        rows.append(json.loads(cp.stdout))
    after = fingerprint()
    checks = {"three_fresh_workers": len(rows) == 3 and len({r["pid"] for r in rows}) == 3,
              "source_lock_stable": before == after and all(r["before"] == before == r["after"] for r in rows),
              "native_build_fresh": not before["native_build_stale"],
              "expected_access_declaration": all(r[k]["rule_access"][3] == ["edge:trigger", "edge:watched"] and r[k]["rule_access"][4] == ["edge:watched"] for r in rows for k in ("default", "precise")),
              "initial_fixed_points": all(r[k]["initial_report"]["status"] == "fixed_point" and r[k]["initial_value"] == 1 for r in rows for k in ("default", "precise")),
              "post_delete_terminal_graph_oracle": all(r[k]["node_removed"] and r[k]["delete_settle_report"]["status"] == "fixed_point" and r[k]["independent_watched_count"] == 0 and r[k]["target_present"] and r[k]["doomed_absent"] for r in rows for k in ("default", "precise")),
              "both_modes_refresh_after_fix": all(r["default"]["final_value"] == 0 and r["precise"]["final_value"] == 0 for r in rows),
              "both_modes_reenumerate_reader": all(r[k]["delete_settle_metrics"].get("rule_enumerations", 0) >= 1 for r in rows for k in ("default", "precise"))}
    log_ref = finish_console_capture(log)
    manifest = capture_run_manifest(run_id=RUN_ID, runner="scripts/substrate_delete_active_rule_invalidation_v1.py",
        protocol_files=(str(PROTOCOL.relative_to(ROOT)), str(AMENDMENT.relative_to(ROOT)), str(LOCK.relative_to(ROOT))),
        source_files=tuple(p for p in FILES if p.startswith("runners/")) + ("scripts/substrate_run_manifest.py", "domains/engine_provenance.py"),
        analysis_files=("scripts/analyze_substrate_delete_active_rule_invalidation_v1.py",), started_utc=started,
        exit_status=0 if all(checks.values()) else 1, stdout_stderr_capture=log_ref)
    raw = {"schema_version": 1, "run_id": RUN_ID, "locked_inputs": before, "post_run_inputs": after,
           "checks": checks, "all_checks_pass": all(checks.values()), "runs": rows, "run_manifest": manifest,
           "claim_boundary": "One active typed-Edges reader under default and precise dirty modes after public node deletion; v1 pre-fix stale behavior is retained in separate artifacts."}
    RAW.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks": checks, "all_checks_pass": raw["all_checks_pass"], "raw": str(RAW.relative_to(ROOT))}, indent=2))
    return 0 if raw["all_checks_pass"] else 1


if __name__ == "__main__": raise SystemExit(main())
