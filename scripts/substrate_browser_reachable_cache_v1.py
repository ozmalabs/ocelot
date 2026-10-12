#!/usr/bin/env python3
"""Source-authored BrowserWorld affordance rule cache panel (no browser/network)."""
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

PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_BROWSER_REACHABLE_CACHE_V1_PREREG_20260928.md"
SEED = ROOT / "seeds/browser_affordance_reach.json"
LOCK = ROOT / "evaluation/substrate_capability/browser_reachable_cache_v1_lock_20260928.json"
RAW = ROOT / "evaluation/reports/substrate_browser_reachable_cache_v1_20260928.json"
RUN_ID = "substrate-browser-reachable-cache-v1-20260928"
FILES = (
    "scripts/substrate_browser_reachable_cache_v1.py",
    "scripts/analyze_substrate_browser_reachable_cache_v1.py",
    "scripts/substrate_run_manifest.py",
    "domains/engine_provenance.py",
    str(PROTOCOL.relative_to(ROOT)),
    str(SEED.relative_to(ROOT)),
    "worlds/browser.py",
    "runners/dsl/src/term.rs",
    "runners/dsl/src/substrate.rs",
    "runners/dsl/src/py.rs",
    "runners/dsl/src/rewrite.rs",
    "runners/dsl/src/graph.rs",
    "runners/dsl/src/scale_audit.rs",
    "runners/dsl/python/substrate_rs/_native.build.json",
    "runners/dsl/Cargo.toml",
    "runners/dsl/Cargo.lock",
)
SIZES = (2, 8, 32, 128)
BRANCHES = (1, 4)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprint() -> dict:
    native = Path(_native.__file__).resolve()
    return {"commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "files": {p: sha(ROOT / p) for p in FILES}, "native_path": str(native),
            "native_sha256": sha(native), "native_build_stale": build_is_stale(str(ROOT))}


def run_arm(n: int, branches: int, cache: bool) -> dict:
    g = _native.Substrate()
    g.set_reachable_cache(cache)
    seed = json.loads(SEED.read_text())
    for rule in seed["rules"]:
        g.add_rule(rule)
    session = g.add_node("WorldInstance", {"world_type": "Session"})
    wrappers = [g.add_node("WorldInstance", {"world_type": "Element", "present": 1.0}) for _ in range(branches)]
    for wrapper in wrappers:
        g.add_edge_unchecked(session, "contains", wrapper, {})
    affordances = []
    for i in range(n):
        leaf = g.add_node("WorldInstance", {"world_type": "Element", "present": 1.0})
        affordance = g.add_node("Affordance", {"world_id": f"aff_{i}"})
        g.add_edge_unchecked(wrappers[i % branches], "contains", leaf, {})
        g.add_edge_unchecked(leaf, "affords", affordance, {})
        affordances.append(affordance)
    g.scale_audit_reset()
    g.scale_audit_set_enabled(True)
    g.runtime_access_trace_reset()
    g.runtime_access_trace_set_enabled(True)
    started = time.perf_counter_ns()
    report = dict(g.run_rules_report(1_000_000, False))
    wall_ns = time.perf_counter_ns() - started
    g.runtime_access_trace_set_enabled(False)
    trace, dropped = g.runtime_access_trace_snapshot()
    units = {str(k): int(v) for k, v in dict(g.scale_audit_snapshot()).items()}
    g.scale_audit_set_enabled(False)
    graph = g.graph_to_dict()
    mirror_count = sum(g.has_edge(session, "has_affordance", affordance) for affordance in affordances)
    return {"cache": cache, "report": report, "wall_ns": wall_ns, "trace": [list(row) for row in trace],
            "trace_dropped": int(dropped), "units": units, "graph": graph, "mirror_count": mirror_count,
            "expected_mirror_count": n,
            "graph_sha256": hashlib.sha256(json.dumps(graph, sort_keys=True, separators=(",", ":")).encode()).hexdigest()}


def worker(n: int, branches: int, replicate: int) -> dict:
    before = fingerprint()
    order = [False, True] if replicate % 2 == 0 else [True, False]
    arms = {str(cache).lower(): run_arm(n, branches, cache) for cache in order}
    after = fingerprint()
    return {"n": n, "branches": branches, "replicate": replicate, "pid": os.getpid(),
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
            for branches in BRANCHES:
                for replicate in range(3):
                    cp = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker", str(n), str(branches), str(replicate)], cwd=ROOT, env=env, text=True, capture_output=True, check=True)
                    rows.append(json.loads(cp.stdout))
    except Exception:
        finish_console_capture(log)
        raise
    final = fingerprint()
    checks = {
        "complete_24_worker_factorial": len(rows) == 24 and all(sum(r["n"] == n and r["branches"] == b for r in rows) == 3 for n in SIZES for b in BRANCHES),
        "unique_fresh_processes": len({r["pid"] for r in rows}) == 24,
        "counterbalanced_order": all(r["arm_order"] == (["false", "true"] if r["replicate"] % 2 == 0 else ["true", "false"]) for r in rows),
        "stable_source_seed_and_native_lock": initial == final and all(r["before"] == initial == r["after"] for r in rows),
        "fresh_native_build": not initial["native_build_stale"],
        "both_rules_reach_fixed_point": all(r["arms"][k]["report"]["status"] == "fixed_point" for r in rows for k in ("false", "true")),
        "all_authored_mirror_edges_present": all(r["arms"][k]["mirror_count"] == r["n"] == r["arms"][k]["expected_mirror_count"] for r in rows for k in ("false", "true")),
        "exact_graph_progress_and_trace_parity": all(r["arms"]["false"]["graph"] == r["arms"]["true"]["graph"] and r["arms"]["false"]["report"]["progress_steps"] == r["arms"]["true"]["report"]["progress_steps"] and r["arms"]["false"]["trace"] == r["arms"]["true"]["trace"] and r["arms"]["false"]["trace_dropped"] == r["arms"]["true"]["trace_dropped"] == 0 for r in rows),
        "matcher_work_parity": all(all(r["arms"]["false"]["units"].get(key, 0) == r["arms"]["true"]["units"].get(key, 0) for key in ("cand_tested", "where_evals", "rule_enumerations")) for r in rows),
        "positive_nonincreasing_traversal_work": all(r["arms"]["false"]["units"].get("term_unit:ReachableFrom", 0) > 0 and r["arms"]["true"]["units"].get("term_unit:ReachableFrom", 0) > 0 and r["arms"]["true"]["units"].get("term_unit:ReachableFrom", 0) <= r["arms"]["false"]["units"].get("term_unit:ReachableFrom", 0) for r in rows),
    }
    logref = finish_console_capture(log)
    manifest = capture_run_manifest(run_id=RUN_ID, runner="scripts/substrate_browser_reachable_cache_v1.py",
        protocol_files=(str(PROTOCOL.relative_to(ROOT)), str(LOCK.relative_to(ROOT))),
        source_files=tuple(p for p in FILES if p.startswith("runners/")) + (str(SEED.relative_to(ROOT)), "worlds/browser.py", "scripts/substrate_run_manifest.py", "domains/engine_provenance.py"),
        analysis_files=("scripts/analyze_substrate_browser_reachable_cache_v1.py",), started_utc=started,
        exit_status=0 if all(checks.values()) else 1, stdout_stderr_capture=logref)
    raw = {"schema_version": 1, "run_id": RUN_ID, "locked_inputs": initial, "post_run_inputs": final,
           "checks": checks, "all_checks_pass": all(checks.values()), "runs": rows,
           "run_manifest": manifest,
           "claim_boundary": "The source-authored browser_affordance_reach seed rules on DOM-shaped synthetic graphs. No browser process, live page, network, end-to-end latency, or natural-page prevalence claim."}
    RAW.parent.mkdir(parents=True, exist_ok=True)
    RAW.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks": checks, "all_checks_pass": raw["all_checks_pass"], "raw": str(RAW.relative_to(ROOT))}, indent=2))
    return 0 if raw["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
