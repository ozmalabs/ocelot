#!/usr/bin/env python3
"""Cache hit/miss and payload telemetry on the loaded BrowserWorld profile."""
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
import substrate_browser_profile_reachable_cache_v1 as base
from domains.engine_provenance import build_is_stale
from substrate_run_manifest import capture_run_manifest, finish_console_capture, start_console_capture
from substrate_rs import _native

PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_BROWSER_PROFILE_REACHABLE_CACHE_V1_2_PREREG_20260928.md"
LOCK = ROOT / "evaluation/substrate_capability/browser_profile_reachable_cache_v1_2_lock_20260928.json"
RAW = ROOT / "evaluation/reports/substrate_browser_profile_reachable_cache_v1_2_20260928.json"
RUN_ID = "substrate-browser-profile-reachable-cache-v1-2-20260928"
EXTRA_FILES = (
    "scripts/substrate_browser_profile_reachable_cache_v1_2.py",
    "scripts/analyze_substrate_browser_profile_reachable_cache_v1_2.py",
    str(PROTOCOL.relative_to(ROOT)),
    "runners/dsl/src/value.rs",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fingerprint() -> dict:
    current = base.fingerprint()
    current["telemetry_files"] = {p: sha(ROOT / p) for p in EXTRA_FILES}
    current["native_build_stale"] = build_is_stale(str(ROOT))
    native = Path(_native.__file__).resolve()
    current["native_path"] = str(native)
    current["native_sha256"] = sha(native)
    return current


def run_arm(n: int, branches: int, cache: bool, audit: bool) -> dict:
    adapter, session, affordances = base.make_profile(cache, n, branches)
    loaded_rule_names = sorted(row[1] for row in adapter.inner.rule_access_sets())
    adapter.inner.reachable_cache_stats_reset()
    adapter.inner.scale_audit_set_enabled(audit)
    adapter.inner.runtime_access_trace_reset()
    adapter.inner.runtime_access_trace_set_enabled(audit)
    if audit:
        adapter.inner.scale_audit_reset()
    started = time.perf_counter_ns()
    tick_steps = adapter.tick()
    wall_ns = time.perf_counter_ns() - started
    adapter.inner.runtime_access_trace_set_enabled(False)
    trace, dropped = adapter.inner.runtime_access_trace_snapshot() if audit else ([], 0)
    units = {str(k): int(v) for k, v in dict(adapter.inner.scale_audit_snapshot()).items()} if audit else {}
    cache_stats = {str(k): int(v) for k, v in dict(adapter.inner.reachable_cache_stats()).items()}
    adapter.inner.scale_audit_set_enabled(False)
    graph = adapter.inner.graph_to_dict()
    mirror_count = sum(adapter.inner.has_edge(session, "has_affordance", aff) for aff in affordances)
    terminal_steps = adapter.tick()
    terminal_graph = adapter.inner.graph_to_dict()
    try:
        adapter.close()
    except Exception:
        pass
    return {"cache": cache, "audit": audit, "loaded_rule_names": loaded_rule_names, "tick_steps": int(tick_steps),
        "terminal_tick_steps": int(terminal_steps), "wall_ns": wall_ns,
        "trace": [list(row) for row in trace], "trace_dropped": int(dropped),
        "units": units, "cache_stats": cache_stats, "graph": graph, "terminal_graph": terminal_graph,
        "mirror_count": mirror_count, "expected_mirror_count": n}


def worker(n: int, branches: int, replicate: int) -> dict:
    before = fingerprint()
    order = [False, True] if replicate % 2 == 0 else [True, False]
    audit_order = [True, False] if replicate % 2 == 0 else [False, True]
    arms = {}
    for cache in order:
        arms[str(cache).lower()] = {str(audit).lower(): run_arm(n, branches, cache, audit) for audit in audit_order}
    after = fingerprint()
    return {"n": n, "branches": branches, "replicate": replicate, "pid": os.getpid(),
        "arm_order": [str(x).lower() for x in order], "audit_order": [str(x).lower() for x in audit_order], "before": before, "after": after, "arms": arms}


def arm(row: dict, cache: bool, audit: bool) -> dict:
    return row["arms"][str(cache).lower()][str(audit).lower()]


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
        for n in base.SIZES:
            for branches in base.BRANCHES:
                for replicate in range(3):
                    cp = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--worker", str(n), str(branches), str(replicate)], cwd=ROOT, env=env, text=True, capture_output=True, check=True)
                    rows.append(json.loads(cp.stdout))
    except Exception:
        finish_console_capture(log)
        raise
    final = fingerprint()
    flat_arms = [(row, cache, audit, arm(row, cache, audit))
        for row in rows for cache in (False, True) for audit in (True, False)]
    def semantic_tuple(result):
        return (result["graph"], result["terminal_graph"], result["tick_steps"],
            result["terminal_tick_steps"], result["mirror_count"])

    checks = {
        "complete_24_worker_factorial": len(rows) == 24 and all(sum(r["n"] == n and r["branches"] == b for r in rows) == 3 for n in base.SIZES for b in base.BRANCHES),
        "unique_workers_and_counterbalanced_orders": len({r["pid"] for r in rows}) == 24 and all(r["arm_order"] == (["false", "true"] if r["replicate"] % 2 == 0 else ["true", "false"]) and r["audit_order"] == (["true", "false"] if r["replicate"] % 2 == 0 else ["false", "true"]) for r in rows),
        "stable_source_and_native_lock": initial == final and all(r["before"] == initial == r["after"] for r in rows),
        "fresh_native_build": not initial["native_build_stale"],
        "loaded_profile_rules_match_manifests": all(set(a["loaded_rule_names"]) == {rule["name"] for rel in base.profile_seed_files() for rule in json.loads((ROOT / rel).read_text()).get("rules", [])} for _, _, _, a in flat_arms),
        "all_four_semantic_outcomes_match": all(len({json.dumps(semantic_tuple(arm(r, cache, audit)), sort_keys=True) for cache in (False, True) for audit in (True, False)}) == 1 and all(arm(r, cache, audit)["terminal_tick_steps"] == 0 for cache in (False, True) for audit in (True, False)) for r in rows),
        "audit_trace_and_matcher_parity": all(arm(r, False, True)["trace"] == arm(r, True, True)["trace"] and arm(r, False, True)["trace_dropped"] == arm(r, True, True)["trace_dropped"] == 0 and all(arm(r, False, True)["units"].get(k, 0) == arm(r, True, True)["units"].get(k, 0) for k in ("cand_tested", "where_evals", "rule_enumerations")) for r in rows),
        "disabled_cache_zero_stats_in_all_modes": all(not any(a["cache_stats"].get(k, 0) for k in ("hits", "misses", "entries", "peak_entries", "estimated_payload_bytes", "peak_estimated_payload_bytes")) for _, cache, _, a in flat_arms if not cache),
        "enabled_cache_activity_in_all_modes": all(a["cache_stats"].get("hits", 0) > 0 and a["cache_stats"].get("misses", 0) > 0 and a["cache_stats"].get("peak_entries", 0) > 0 and a["cache_stats"].get("peak_estimated_payload_bytes", 0) > 0 for _, cache, _, a in flat_arms if cache),
        "audit_counts_cover_all_reachability_evaluations": all(arm(r, True, True)["cache_stats"]["hits"] + arm(r, True, True)["cache_stats"]["misses"] == arm(r, True, True)["units"].get("term_eval:ReachableFrom", 0) for r in rows),
        "quiet_and_audit_cache_counts_match": all(arm(r, cache, False)["cache_stats"]["hits"] == arm(r, cache, True)["cache_stats"]["hits"] and arm(r, cache, False)["cache_stats"]["misses"] == arm(r, cache, True)["cache_stats"]["misses"] for r in rows for cache in (False, True)),
        "payload_current_bounded_by_peak": all(a["cache_stats"].get("estimated_payload_bytes", 0) <= a["cache_stats"].get("peak_estimated_payload_bytes", 0) and a["cache_stats"].get("entries", 0) <= a["cache_stats"].get("peak_entries", 0) for _, _, _, a in flat_arms),
        "positive_nonincreasing_audit_traversal_work": all(arm(r, False, True)["units"].get("term_unit:ReachableFrom", 0) >= arm(r, True, True)["units"].get("term_unit:ReachableFrom", 0) > 0 for r in rows),
    }
    logref = finish_console_capture(log)
    source_files = tuple(p for p in base.files() + EXTRA_FILES if p.startswith(("runners/", "substrate/", "worlds/", "seeds/"))) + ("scripts/substrate_run_manifest.py", "domains/engine_provenance.py")
    manifest = capture_run_manifest(run_id=RUN_ID, runner="scripts/substrate_browser_profile_reachable_cache_v1_2.py",
        protocol_files=(str(PROTOCOL.relative_to(ROOT)), str(LOCK.relative_to(ROOT))), source_files=source_files,
        analysis_files=("scripts/analyze_substrate_browser_profile_reachable_cache_v1_2.py",), started_utc=started,
        exit_status=0 if all(checks.values()) else 1, stdout_stderr_capture=logref)
    raw = {"schema_version": 1, "run_id": RUN_ID, "locked_inputs": initial, "post_run_inputs": final,
        "checks": checks, "all_checks_pass": all(checks.values()), "runs": rows,
        "profile_seed_ids": list(base.SEED_IDS), "run_manifest": manifest,
        "claim_boundary": "Cache telemetry during ordinary five-seed WorldAdapter profile ticks over synthetic DOM-shaped records. Payload bytes are an estimate excluding map buckets/allocator overhead; no Chromium or live-page prevalence claim."}
    RAW.parent.mkdir(parents=True, exist_ok=True)
    RAW.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks": checks, "all_checks_pass": raw["all_checks_pass"], "raw": str(RAW.relative_to(ROOT))}, indent=2))
    return 0 if raw["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
