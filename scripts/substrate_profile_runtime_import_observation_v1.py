#!/usr/bin/env python3
"""Observe declared conversation-profile preloads in fresh locked processes."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_PROFILE_RUNTIME_IMPORT_OBSERVATION_V1_PREREG_20260928.md"
INVENTORY = ROOT / "evaluation/substrate_capability/python_source_coverage_audit_v1_1_20260928.json"
LOCK = ROOT / "evaluation/substrate_capability/profile_runtime_import_observation_v1_lock_20260928.json"
RAW = ROOT / "evaluation/reports/profile_runtime_import_observation_v1_20260928.json"
ANALYZER = ROOT / "scripts/analyze_substrate_profile_runtime_import_observation_v1.py"
RUNNER = ROOT / "scripts/substrate_profile_runtime_import_observation_v1.py"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def current_inputs() -> dict:
    inventory = json.loads(INVENTORY.read_text())
    source_hashes = {row["path"]: sha(ROOT / row["path"]) for row in inventory["files"]}
    seed_hashes = {rel: sha(ROOT / rel) for rel in inventory["seed_manifest_hashes"]}
    from substrate_rs import _native
    from domains.engine_provenance import build_is_stale, rust_source_fingerprint

    stale = build_is_stale(str(ROOT))
    if stale:
        raise SystemExit(f"native extension is stale against Rust source: {stale[:5]}")
    native = Path(_native.__file__).resolve()
    direct = (PROTOCOL, INVENTORY, RUNNER, ANALYZER,
              ROOT / "substrate/boot_profiles.py", ROOT / "substrate/boot_all.py",
              ROOT / "substrate/world_adapter.py", ROOT / "runners/dsl/python/substrate_rs/_native.build.json")
    return {
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "protocol_sha256": sha(PROTOCOL), "inventory_sha256": sha(INVENTORY),
        "direct_source_sha256": {str(p.relative_to(ROOT)): sha(p) for p in direct},
        "python_source_sha256": source_hashes, "seed_manifest_sha256": seed_hashes,
        "native_extension_sha256": sha(native),
        "native_build_manifest_sha256": sha(ROOT / "runners/dsl/python/substrate_rs/_native.build.json"),
        "native_rust_source_fingerprint": rust_source_fingerprint(str(ROOT)),
        "python": sys.version, "platform": platform.platform(),
    }


def worker(replicate: int) -> dict:
    started_inputs = current_inputs()
    frozen = json.loads(LOCK.read_text())
    if started_inputs != frozen:
        raise SystemExit("worker source/native fingerprint differs from lock")

    from substrate.world_adapter import WorldAdapter
    from substrate.boot_profiles import CONVERSATION_RUNTIME_MODULES, load_conversation_seed_profile
    import importlib
    import resource

    adapter = WorldAdapter(seeds=())
    profile_declared = list(CONVERSATION_RUNTIME_MODULES)
    before = {name for name in sys.modules if name.startswith("domains.")}
    calls = []
    original_import_module = importlib.import_module

    def observed_import(name, package=None):
        t0 = time.perf_counter_ns()
        module = original_import_module(name, package)
        calls.append({"requested": name, "package": package,
                      "resolved": getattr(module, "__name__", None),
                      "elapsed_ns": time.perf_counter_ns() - t0})
        return module

    importlib.import_module = observed_import
    started_ns = time.perf_counter_ns()
    try:
        report = load_conversation_seed_profile(adapter)
        elapsed_ns = time.perf_counter_ns() - started_ns
    finally:
        importlib.import_module = original_import_module
    after = {name for name in sys.modules if name.startswith("domains.")}
    newly = after - before
    loaded_seed_ids = sorted(str(x) for x in (
        report.get("order") or (report.get("selection") or {}).get("selected_seed_ids") or []))
    graph = adapter.s.graph_to_dict()
    module_files = {}
    for name in profile_declared:
        module = sys.modules.get(name)
        module_files[name] = str(Path(module.__file__).resolve().relative_to(ROOT)) if module and getattr(module, "__file__", None) else None
    result = {
        "replicate": replicate, "pid": os.getpid(),
        "worker_started_inputs": started_inputs,
        "profile_status": {"selection_complete": report.get("selection_complete"),
                           "failed_count": len(report.get("failed") or []),
                           "failed": report.get("failed") or []},
        "loaded_seed_ids": loaded_seed_ids,
        "profile_declared_modules": profile_declared,
        "profile_report_modules_warmed": report.get("runtime_modules_warmed") or [],
        "import_calls": calls,
        "modules_loaded_before_profile": sorted(before),
        "new_domains_modules": sorted(newly),
        "profile_module_files": module_files,
        "node_count": len(graph.get("nodes", [])), "edge_count": len(graph.get("edges", [])),
        "profile_wall_ns": elapsed_ns,
        "peak_rss_bytes": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024),
    }
    result["worker_finished_inputs"] = current_inputs()
    adapter.close()
    return result


def main() -> None:
    mode = sys.argv[1:2]
    if mode and mode[0] == "--worker":
        print(json.dumps(worker(int(sys.argv[2])), sort_keys=True, default=str))
        return
    if mode == ["--lock"]:
        if LOCK.exists() or RAW.exists():
            raise SystemExit("refusing to overwrite lock/raw")
        frozen = current_inputs()
        LOCK.parent.mkdir(parents=True, exist_ok=True)
        LOCK.write_text(json.dumps(frozen, indent=2, sort_keys=True) + "\n")
        print(LOCK)
        return
    if RAW.exists():
        raise SystemExit("refusing to overwrite raw capture")
    locked = current_inputs()
    if not LOCK.is_file() or json.loads(LOCK.read_text()) != locked:
        raise SystemExit("missing or stale source/native lock")
    env = dict(os.environ)
    env.setdefault("OZMA_NO_LLM", "1")
    env.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
    runs = []
    status = "complete"
    error = None
    for replicate in range(3):
        try:
            cp = subprocess.run([sys.executable, str(RUNNER), "--worker", str(replicate)],
                                cwd=ROOT, env=env, text=True, capture_output=True, check=True)
            record = json.loads(cp.stdout)
            runs.append(record)
            print(f"replicate={replicate} seeds={len(record['loaded_seed_ids'])} imports={len(record['import_calls'])}", flush=True)
            if record["worker_started_inputs"] != locked or record["worker_finished_inputs"] != locked:
                status, error = "censored_source_drift", "worker fingerprint changed"
                break
        except Exception as exc:  # preserve a completed prefix and error evidence
            status, error = "censored_worker_error", f"{type(exc).__name__}: {exc}"
            break
    post = current_inputs()
    if post != locked and status == "complete":
        status, error = "censored_source_drift", "top-level fingerprint changed"
    raw = {"schema_version": 1, "run_id": "profile-runtime-import-observation-v1-20260928",
           "capture_status": status, "started_utc": datetime.now(timezone.utc).isoformat(),
           "locked_inputs": locked, "post_run_inputs": post, "runs": runs, "capture_error": error}
    RAW.parent.mkdir(parents=True, exist_ok=True)
    RAW.write_text(json.dumps(raw, indent=2, sort_keys=True, default=str) + "\n")
    print(json.dumps({"capture_status": status, "workers": len(runs), "raw": str(RAW.relative_to(ROOT))}, indent=2))
    if status != "complete" or len(runs) != 3:
        raise SystemExit("capture censored; prefix preserved")


if __name__ == "__main__":
    main()
