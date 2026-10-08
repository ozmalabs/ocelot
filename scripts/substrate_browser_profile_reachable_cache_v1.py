#!/usr/bin/env python3
"""Run the browser cache comparison through the normally booted WorldAdapter profile."""
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
from substrate.world_adapter import WorldAdapter
from domains.engine_provenance import build_is_stale
from substrate_run_manifest import capture_run_manifest, finish_console_capture, start_console_capture
from substrate_rs import _native

SEED_IDS = ("decision_core", "learning_core", "perception_core", "region_grouping", "browser_affordance_reach")
SIZES = (2, 8, 32, 128)
BRANCHES = (1, 4)
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_BROWSER_PROFILE_REACHABLE_CACHE_V1_PREREG_20260928.md"
LOCK = ROOT / "evaluation/substrate_capability/browser_profile_reachable_cache_v1_lock_20260928.json"
RAW = ROOT / "evaluation/reports/substrate_browser_profile_reachable_cache_v1_20260928.json"
RUN_ID = "substrate-browser-profile-reachable-cache-v1-20260928"
BASE_FILES = (
    "scripts/substrate_browser_profile_reachable_cache_v1.py",
    "scripts/analyze_substrate_browser_profile_reachable_cache_v1.py",
    "scripts/substrate_run_manifest.py",
    "domains/engine_provenance.py",
    "substrate/boot_core.py",
    "substrate/seed_loader.py",
    "substrate/world_adapter.py",
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


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def profile_seed_files() -> tuple[str, ...]:
    pending = list(SEED_IDS)
    seen: set[str] = set()
    while pending:
        seed_id = pending.pop()
        if seed_id in seen:
            continue
        seen.add(seed_id)
        path = ROOT / "seeds" / f"{seed_id}.json"
        if not path.is_file():
            raise FileNotFoundError(path)
        manifest = json.loads(path.read_text())
        pending.extend(str(x) for x in manifest.get("depends_on", ()))
    return tuple(f"seeds/{sid}.json" for sid in sorted(seen))


def files() -> tuple[str, ...]:
    return BASE_FILES + profile_seed_files() + (str(PROTOCOL.relative_to(ROOT)),)


def fingerprint() -> dict:
    native = Path(_native.__file__).resolve()
    return {"commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "files": {p: sha(ROOT / p) for p in files()}, "native_path": str(native),
        "native_sha256": sha(native), "native_build_stale": build_is_stale(str(ROOT))}


def make_profile(cache: bool, n: int, branches: int) -> tuple[WorldAdapter, object, list[object]]:
    adapter = WorldAdapter(seeds=SEED_IDS, shadow_read=False, deep_ingest=False)
    adapter.inner.set_reachable_cache(cache)
    session = adapter.s.add_node("WorldInstance", {"world_type": "Session", "id": "synthetic_session"})
    wrappers = [adapter.s.add_node("WorldInstance", {"world_type": "Element", "id": f"nav_{i}", "present": 1.0}) for i in range(branches)]
    for wrapper in wrappers:
        adapter.inner.add_edge_unchecked(session, "contains", wrapper, {})
    affordances = []
    for i in range(n):
        leaf = adapter.s.add_node("WorldInstance", {"world_type": "Element", "id": f"el_{i}", "present": 1.0, "tag": "a", "text": f"Synthetic affordance {i}"})
        affordance = adapter.s.add_node("Affordance", {"world_id": f"aff_{i}", "kind": "navigate"})
        adapter.inner.add_edge_unchecked(wrappers[i % branches], "contains", leaf, {})
        adapter.inner.add_edge_unchecked(leaf, "affords", affordance, {})
        affordances.append(affordance)
    return adapter, session, affordances


def run_arm(n: int, branches: int, cache: bool) -> dict:
    adapter, session, affordances = make_profile(cache, n, branches)
    loaded_rule_names = sorted(row[1] for row in adapter.inner.rule_access_sets())
    adapter.inner.scale_audit_reset()
    adapter.inner.scale_audit_set_enabled(True)
    adapter.inner.runtime_access_trace_reset()
    adapter.inner.runtime_access_trace_set_enabled(True)
    started = time.perf_counter_ns()
    tick_steps = adapter.tick()
    wall_ns = time.perf_counter_ns() - started
    adapter.inner.runtime_access_trace_set_enabled(False)
    trace, dropped = adapter.inner.runtime_access_trace_snapshot()
    units = {str(k): int(v) for k, v in dict(adapter.inner.scale_audit_snapshot()).items()}
    adapter.inner.scale_audit_set_enabled(False)
    graph = adapter.inner.graph_to_dict()
    mirror_count = sum(adapter.inner.has_edge(session, "has_affordance", aff) for aff in affordances)
    # A second untouched normal-profile tick is the terminal no-progress probe.
    terminal_steps = adapter.tick()
    terminal_graph = adapter.inner.graph_to_dict()
    try:
        adapter.close()
    except Exception:
        pass
    return {"cache": cache, "loaded_rule_names": loaded_rule_names, "tick_steps": int(tick_steps),
        "terminal_tick_steps": int(terminal_steps), "wall_ns": wall_ns,
        "trace": [list(row) for row in trace], "trace_dropped": int(dropped),
        "units": units, "graph": graph, "terminal_graph": terminal_graph,
        "mirror_count": mirror_count, "expected_mirror_count": n}


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
    expected_rule_names = {rule["name"] for rel in profile_seed_files() for rule in json.loads((ROOT / rel).read_text()).get("rules", [])}
    checks = {
        "complete_24_worker_factorial": len(rows) == 24 and all(sum(r["n"] == n and r["branches"] == b for r in rows) == 3 for n in SIZES for b in BRANCHES),
        "unique_workers_and_counterbalanced_arms": len({r["pid"] for r in rows}) == 24 and all(r["arm_order"] == (["false", "true"] if r["replicate"] % 2 == 0 else ["true", "false"]) for r in rows),
        "stable_profile_source_lock": initial == final and all(r["before"] == initial == r["after"] for r in rows),
        "fresh_native_build": not initial["native_build_stale"],
        "loaded_profile_rules_match_manifest": all(set(r["arms"][k]["loaded_rule_names"]) == expected_rule_names for r in rows for k in ("false", "true")),
        "tick_steps_and_exact_graph_parity": all(r["arms"]["false"]["tick_steps"] == r["arms"]["true"]["tick_steps"] and r["arms"]["false"]["graph"] == r["arms"]["true"]["graph"] and r["arms"]["false"]["terminal_graph"] == r["arms"]["true"]["terminal_graph"] for r in rows),
        "expected_mirrors_and_terminal_noop": all(r["arms"][k]["mirror_count"] == r["n"] and r["arms"][k]["terminal_tick_steps"] == 0 for r in rows for k in ("false", "true")),
        "access_trace_parity_and_no_drops": all(r["arms"]["false"]["trace"] == r["arms"]["true"]["trace"] and r["arms"]["false"]["trace_dropped"] == r["arms"]["true"]["trace_dropped"] == 0 for r in rows),
        "matcher_work_parity": all(all(r["arms"]["false"]["units"].get(key, 0) == r["arms"]["true"]["units"].get(key, 0) for key in ("cand_tested", "where_evals", "rule_enumerations")) for r in rows),
        "positive_nonincreasing_reachable_work": all(r["arms"]["false"]["units"].get("term_unit:ReachableFrom", 0) > 0 and r["arms"]["true"]["units"].get("term_unit:ReachableFrom", 0) > 0 and r["arms"]["true"]["units"].get("term_unit:ReachableFrom", 0) <= r["arms"]["false"]["units"].get("term_unit:ReachableFrom", 0) for r in rows),
    }
    logref = finish_console_capture(log)
    source_files = tuple(p for p in files() if p.startswith(("runners/", "substrate/", "worlds/", "seeds/"))) + ("scripts/substrate_run_manifest.py", "domains/engine_provenance.py")
    manifest = capture_run_manifest(run_id=RUN_ID, runner="scripts/substrate_browser_profile_reachable_cache_v1.py",
        protocol_files=(str(PROTOCOL.relative_to(ROOT)), str(LOCK.relative_to(ROOT))), source_files=source_files,
        analysis_files=("scripts/analyze_substrate_browser_profile_reachable_cache_v1.py",), started_utc=started,
        exit_status=0 if all(checks.values()) else 1, stdout_stderr_capture=logref)
    raw = {"schema_version": 1, "run_id": RUN_ID, "locked_inputs": initial, "post_run_inputs": final,
        "checks": checks, "all_checks_pass": all(checks.values()), "runs": rows,
        "profile_seed_ids": list(SEED_IDS), "run_manifest": manifest,
        "claim_boundary": "Normal five-seed WorldAdapter profile tick over synthetic DOM-shaped records; Chromium/browser launch was not used and live-page prevalence or end-to-end browser latency is not claimed."}
    RAW.parent.mkdir(parents=True, exist_ok=True)
    RAW.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks": checks, "all_checks_pass": raw["all_checks_pass"], "raw": str(RAW.relative_to(ROOT))}, indent=2))
    return 0 if raw["all_checks_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
