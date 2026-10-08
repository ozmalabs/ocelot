#!/usr/bin/env python3
"""Fresh-process, source-locked paired panel for ReachableFrom query reuse."""
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
from substrate_rs import _native
from domains.engine_provenance import build_is_stale
from substrate_run_manifest import capture_run_manifest, finish_console_capture, start_console_capture

PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_REACHABLE_FROM_CACHE_V1_PREREG_20260928.md"
LOCK = ROOT / "evaluation/substrate_capability/reachable_from_cache_v1_lock_20260928.json"
RAW = ROOT / "evaluation/reports/substrate_reachable_from_cache_v1_20260928.json"
RUN_ID = "substrate-reachable-from-cache-v1-20260928"
FILES = (
    "scripts/substrate_reachable_from_cache_v1.py",
    "scripts/analyze_substrate_reachable_from_cache_v1.py",
    "scripts/substrate_run_manifest.py",
    "domains/engine_provenance.py",
    str(PROTOCOL.relative_to(ROOT)),
    "runners/dsl/src/term.rs",
    "runners/dsl/src/substrate.rs",
    "runners/dsl/src/py.rs",
    "runners/dsl/src/graph.rs",
    "runners/dsl/src/scale_audit.rs",
    "runners/dsl/python/substrate_rs/_native.build.json",
    "runners/dsl/Cargo.toml",
    "runners/dsl/Cargo.lock",
)
SIZES = (32, 128, 512)
READERS = (1, 16, 64)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprint() -> dict:
    native = Path(_native.__file__).resolve()
    return {
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "files": {p: sha(ROOT / p) for p in FILES},
        "native_path": str(native),
        "native_sha256": sha(native),
        "native_build_stale": build_is_stale(str(ROOT)),
    }


def query(edge: str = "block") -> dict:
    return {"type": "Count", "source": {"type": "ReachableFrom", "node": {"type": "Var", "name": "x"}, "edge_type": edge}}


def build(cache: bool, n: int, readers: int, target_count: int = 0):
    g = _native.Substrate()
    g.set_reachable_cache(cache)
    root = g.add_node("Root", {})
    slots = [g.add_node("Slot", {}) for _ in range(n)]
    blockers = [g.add_node("Blocker", {}) for _ in range(n)]
    for slot in slots:
        g.add_edge_unchecked(root, "slot", slot, {})
    for blocker in blockers:
        g.add_edge_unchecked(root, "block", blocker, {})
    where = {"type": "Eq", "a": query(), "b": {"type": "Lit", "value": target_count}}
    for i in range(readers):
        g.add_rule({"name": f"reachable_cache_reader_{i}", "match": [["x", "slot", "y"]], "where": where, "effects": [["set_attr", "y", f"opened_{i}", 1]]})
    return g, root, slots


def audit_run(g):
    g.scale_audit_reset()
    g.scale_audit_set_enabled(True)
    g.runtime_access_trace_reset()
    g.runtime_access_trace_set_enabled(True)
    started = time.perf_counter_ns()
    report = dict(g.run_rules_report(1_000_000, False))
    elapsed = time.perf_counter_ns() - started
    g.runtime_access_trace_set_enabled(False)
    trace, dropped = g.runtime_access_trace_snapshot()
    units = {str(k): int(v) for k, v in dict(g.scale_audit_snapshot()).items()}
    g.scale_audit_set_enabled(False)
    return report, elapsed, [list(row) for row in trace], int(dropped), units


def scale_arm(n: int, readers: int, cache: bool) -> dict:
    g, _root, _slots = build(cache, n, readers)
    report, wall_ns, trace, trace_dropped, units = audit_run(g)
    graph = g.graph_to_dict()
    return {"cache": cache, "report": report, "wall_ns": wall_ns, "trace": trace,
            "trace_dropped": trace_dropped, "units": units, "graph": graph,
            "graph_sha256": hashlib.sha256(json.dumps(graph, sort_keys=True, separators=(",", ":")).encode()).hexdigest()}


def mutation_control(cache: bool, n: int = 8) -> dict:
    g, root, slots = build(cache, n, 1, target_count=n + 1)
    before = dict(g.run_rules_report(100_000, False))
    before_open = sum(bool(g.node(s)["attrs"]) for s in slots)
    extra = g.add_node("Blocker", {})
    g.add_edge_unchecked(root, "block", extra, {})
    after, wall_ns, _trace, dropped, units = audit_run(g)
    after_open = sum(bool(g.node(s)["attrs"]) for s in slots)
    return {"cache": cache, "before": before, "before_open": before_open, "after": after,
            "after_open": after_open, "wall_ns": wall_ns, "trace_dropped": dropped,
            "units": units, "graph": g.graph_to_dict()}


def worker(n: int, readers: int, replicate: int) -> dict:
    before = fingerprint()
    order = [False, True] if replicate % 2 == 0 else [True, False]
    arms = {str(cache).lower(): scale_arm(n, readers, cache) for cache in order}
    after = fingerprint()
    return {"n": n, "readers": readers, "replicate": replicate, "pid": os.getpid(),
            "arm_order": [str(x).lower() for x in order], "before": before, "after": after, "arms": arms}


def main() -> int:
    if sys.argv[1:] == ["--lock"]:
        fp = fingerprint()
        if fp["native_build_stale"]:
            raise SystemExit("native build is stale")
        LOCK.parent.mkdir(parents=True, exist_ok=True)
        LOCK.write_text(json.dumps(fp, indent=2, sort_keys=True) + "\n")
        print(LOCK)
        return 0
    if len(sys.argv) == 5 and sys.argv[1] == "--worker":
        print(json.dumps(worker(int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])), sort_keys=True))
        return 0
    initial = fingerprint()
    if initial["native_build_stale"] or not LOCK.exists() or json.loads(LOCK.read_text()) != initial:
        raise SystemExit("missing/stale source lock or native build")
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join((str(ROOT), str(ROOT / "runners/dsl/python"), str(ROOT / "scripts"), env.get("PYTHONPATH", "")))
    started = datetime.now(timezone.utc).isoformat()
    log = start_console_capture(RUN_ID)
    rows = []
    try:
        for n in SIZES:
            for readers in READERS:
                for replicate in range(3):
                    cp = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker", str(n), str(readers), str(replicate)], cwd=ROOT, env=env, text=True, capture_output=True, check=True)
                    rows.append(json.loads(cp.stdout))
        mutation = {str(cache).lower(): mutation_control(cache) for cache in (False, True)}
    except Exception:
        finish_console_capture(log)
        raise
    final = fingerprint()
    checks = {
        "complete_27_cell_replications": len(rows) == 27 and all(sum(r["n"] == n and r["readers"] == readers for r in rows) == 3 for n in SIZES for readers in READERS),
        "unique_fresh_workers": len({r["pid"] for r in rows}) == 27,
        "counterbalanced_arm_order": all(r["arm_order"] == (["false", "true"] if r["replicate"] % 2 == 0 else ["true", "false"]) for r in rows),
        "stable_source_lock": initial == final and all(r["before"] == initial == r["after"] for r in rows),
        "fresh_native_build": not initial["native_build_stale"],
        "all_fixed_point": all(r["arms"][k]["report"]["status"] == "fixed_point" for r in rows for k in ("false", "true")),
        "exact_graph_parity": all(r["arms"]["false"]["graph"] == r["arms"]["true"]["graph"] for r in rows),
        "exact_access_trace_parity": all(r["arms"]["false"]["trace"] == r["arms"]["true"]["trace"] and r["arms"]["false"]["trace_dropped"] == r["arms"]["true"]["trace_dropped"] == 0 for r in rows),
        "expected_site_work_counts": all(r["arms"]["false"]["units"].get("term_unit:ReachableFrom", 0) == r["n"] ** 2 * r["readers"] and r["arms"]["true"]["units"].get("term_unit:ReachableFrom", 0) == r["n"] for r in rows),
        "mutation_invalidation_semantics": all(mutation[k]["before"]["status"] == "fixed_point" and mutation[k]["before_open"] == 0 and mutation[k]["after"]["status"] == "fixed_point" and mutation[k]["after_open"] == 8 and mutation[k]["units"].get("term_unit:ReachableFrom", 0) > 0 for k in ("false", "true")) and mutation["false"]["graph"] == mutation["true"]["graph"],
    }
    logref = finish_console_capture(log)
    manifest = capture_run_manifest(run_id=RUN_ID, runner="scripts/substrate_reachable_from_cache_v1.py",
        protocol_files=(str(PROTOCOL.relative_to(ROOT)), str(LOCK.relative_to(ROOT))),
        source_files=tuple(p for p in FILES if p.startswith("runners/")) + ("scripts/substrate_run_manifest.py", "domains/engine_provenance.py"),
        analysis_files=("scripts/analyze_substrate_reachable_from_cache_v1.py",), started_utc=started,
        exit_status=0 if all(checks.values()) else 1, stdout_stderr_capture=logref)
    raw = {"schema_version": 1, "run_id": RUN_ID, "locked_inputs": initial, "post_run_inputs": final,
           "checks": checks, "all_checks_pass": all(checks.values()), "runs": rows,
           "mutation_control": mutation, "run_manifest": manifest,
           "claim_boundary": "Constructed typed-star same-graph repeated ReachableFrom query panel and explicit edge-mutation freshness control; no natural-workload prevalence or general scaling claim."}
    RAW.parent.mkdir(parents=True, exist_ok=True)
    RAW.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks": checks, "all_checks_pass": raw["all_checks_pass"], "raw": str(RAW.relative_to(ROOT))}, indent=2))
    return 0 if raw["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
