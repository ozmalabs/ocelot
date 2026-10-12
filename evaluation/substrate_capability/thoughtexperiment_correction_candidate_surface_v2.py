#!/usr/bin/env python3
"""Fresh-process, source-locked inventory of default correction candidates."""
from __future__ import annotations
import hashlib, importlib.util, json, os, platform, subprocess, sys, time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER = Path(__file__).resolve()
PROTOCOL = ROOT / "docs/research/engine_substrate/THOUGHTEXPERIMENT_CORRECTION_CANDIDATE_SURFACE_V2_PREREG_20261002.md"
ANALYZER = ROOT / "evaluation/substrate_capability/analyze_thoughtexperiment_correction_candidate_surface_v2.py"
LOCK = ROOT / "evaluation/substrate_capability/thoughtexperiment_correction_candidate_surface_v2_lock_20261002.json"
RAW = ROOT / "evaluation/reports/thoughtexperiment_correction_candidate_surface_v2_raw_20261002.json"
PREVIOUS = ROOT / "evaluation/reports/thoughtexperiment_correction_candidate_surface_v1_raw_20261001.json"
SOURCES = (
    "domains/self_correction.py", "domains/edit_ops.py",
    "evaluation/substrate_capability/thoughtexperiment_self_correction_copy_comparison_v1.py",
    "substrate/boot_core.py", "domains/engine_provenance.py",
    "runners/dsl/src/py.rs", "runners/dsl/src/substrate.rs",
    "runners/dsl/Cargo.toml", "runners/dsl/Cargo.lock",
    "runners/dsl/python/substrate_rs/__init__.py",
)
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def frozen() -> dict:
    from substrate_rs import _native
    paths = (*[ROOT / p for p in SOURCES], RUNNER, PROTOCOL, ANALYZER)
    return {str(p.relative_to(ROOT)): sha(p) for p in paths} | {
        "loaded_native_binary": sha(Path(_native.__file__).resolve())
    }


def inventory_worker(index: int) -> dict:
    from evaluation.substrate_capability.thoughtexperiment_self_correction_copy_comparison_v1 import make_fixture
    from domains.self_correction import _default_candidates
    substrate, native, *_ = make_fixture(0)
    before_graph = native.graph_to_dict()
    before_rules = native.export_rules()
    active_rules = [r for r in before_rules if r.get("active", True)]
    inventory = []
    for rule in active_rules:
        candidates = _default_candidates(native, rule["name"])
        inventory.append({
            "target_rule": rule["name"],
            "candidate_labels": [str(c.get("label", "")) for c in candidates],
            "candidate_count": len(candidates),
            "task_shaped_labels": [str(c.get("label", "")) for c in candidates
                                   if c.get("label") == "dedup_identity_fix"],
        })
    after_graph = native.graph_to_dict()
    after_rules = native.export_rules()
    return {
        "pid": os.getpid(), "worker_index": index,
        "inventory": inventory,
        "active_rule_count": len(active_rules),
        "candidate_count": sum(row["candidate_count"] for row in inventory),
        "read_only": before_graph == after_graph and before_rules == after_rules,
        "source_hashes": {name: sha(ROOT / name) for name in SOURCES},
    }


def main() -> int:
    if sys.argv[1:2] == ["--worker"]:
        print(json.dumps(inventory_worker(int(sys.argv[2])), sort_keys=True, separators=(",", ":")))
        return 0
    if sys.argv[1:] == ["--lock"]:
        if LOCK.exists() or RAW.exists():
            raise SystemExit("refusing to overwrite lock or raw capture")
        from domains.engine_provenance import build_is_stale, rust_source_fingerprint
        stale = build_is_stale(str(ROOT))
        if stale:
            raise SystemExit("stale native engine: " + "; ".join(stale))
        LOCK.write_text(json.dumps({
            "schema": "ThoughtexperimentCorrectionCandidateSurfaceV2Lock",
            "sources": frozen(), "semantic_engine": rust_source_fingerprint(str(ROOT)),
            "workers": 3,
        }, indent=2, sort_keys=True) + "\n")
        print(LOCK.relative_to(ROOT))
        return 0
    if LOCK.exists() is False:
        raise SystemExit("missing pre-capture lock; run with --lock first")
    if RAW.exists():
        raise SystemExit("raw capture exists; refusing overwrite")
    lock = json.loads(LOCK.read_text())
    from domains.engine_provenance import build_is_stale, rust_source_fingerprint
    stale = build_is_stale(str(ROOT))
    if stale:
        raise SystemExit("stale native engine: " + "; ".join(stale))
    before = frozen()
    if before != lock["sources"]:
        raise SystemExit("source drift from pre-capture lock")
    env = {**os.environ,
           "PYTHONPATH": f"{ROOT / 'runners/dsl/python'}:{ROOT}"}
    rows = []
    for index in range(3):
        proc = subprocess.run([sys.executable, str(RUNNER), "--worker", str(index)],
                              cwd=ROOT, env=env, text=True, capture_output=True, check=True)
        rows.append(json.loads(proc.stdout.strip().splitlines()[-1]))
    after = frozen()
    if before != after:
        raise SystemExit("source drift during candidate inventory")
    previous = json.loads(PREVIOUS.read_text())
    capture = {
        "schema": "ThoughtexperimentCorrectionCandidateSurfaceV2Capture",
        "captured_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "host": {"platform": platform.platform(), "machine": platform.machine(),
                 "python": sys.version.split()[0]},
        "lock": lock, "source_before": before, "source_after": after,
        "semantic_engine": rust_source_fingerprint(str(ROOT)),
        "workers": rows,
        "previous_inventory": previous["workers"][0]["inventory"],
        "current_inventory": rows[0]["inventory"],
    }
    RAW.parent.mkdir(parents=True, exist_ok=True)
    RAW.write_text(json.dumps(capture, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"workers": len(rows), "rules": rows[0]["active_rule_count"],
                      "candidates": rows[0]["candidate_count"],
                      "raw": str(RAW.relative_to(ROOT))}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
