#!/usr/bin/env python3
"""Audit-enabled work attribution for full-seed GenInfer training closures."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER = Path(__file__).resolve()
V1 = ROOT / "evaluation/substrate_capability/substrate_geninfer_fullseed_scaling_v1.py"
ANALYZER = ROOT / "evaluation/substrate_capability/analyze_substrate_geninfer_training_work_profile_v1.py"
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_GENINFER_TRAINING_WORK_PROFILE_V1_PREREG_20261006.md"
BASE = Path("/tmp/ocelot_geninfer_training_work_v1")
TREE = BASE / "tree"
OUT = ROOT / "evaluation/reports/substrate_geninfer_training_work_profile_v1_20261006.json"
sys.path.insert(0, str(ROOT))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def prepare(binary):
    from domains.engine_provenance import build_is_stale, record_build
    source = Path(binary).resolve()
    if not source.is_file():
        raise SystemExit(f"missing 64-shard native binary: {source}")
    (TREE / "runners/dsl/src").mkdir(parents=True, exist_ok=True)
    shutil.copytree(ROOT / "runners/dsl/src", TREE / "runners/dsl/src", dirs_exist_ok=True)
    package = TREE / "runners/dsl/python/substrate_rs"
    package.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ROOT / "runners/dsl/python/substrate_rs", package, dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("_native.abi3.so", "_native.build.json"))
    for filename in ("Cargo.toml", "Cargo.lock"):
        shutil.copy2(ROOT / "runners/dsl" / filename, TREE / "runners/dsl" / filename)
    native = package / "_native.abi3.so"
    shutil.copy2(source, native)
    record = record_build(str(TREE))
    stale = build_is_stale(str(TREE))
    if record is None or stale:
        raise RuntimeError(f"overlay build record invalid: {stale}")
    print(json.dumps({"native": str(native), "sha256": sha(native), "stale": stale}))


def cases():
    return [
        {"id": f"positive_n{n}_b5_r{rep}", "kind": "positive", "n": n, "bound": 5, "repeat": rep}
        for n in (4, 16, 64) for rep in (1, 2, 3)
    ]


def load_overlay():
    package = TREE / "runners/dsl/python/substrate_rs"
    spec = importlib.util.spec_from_file_location("substrate_rs", package / "__init__.py",
                                                   submodule_search_locations=[str(package)])
    module = importlib.util.module_from_spec(spec)
    sys.modules["substrate_rs"] = module
    spec.loader.exec_module(module)
    native_path = (package / "_native.abi3.so").resolve()
    if Path(module._native.__file__).resolve() != native_path:
        raise RuntimeError("wrong engine loaded")
    sys.path[:0] = [str(ROOT / "runners/dsl/python"), str(ROOT)]
    return module._native, native_path


def audited_observe(bench, native_module):
    def observe(sub, agent, native, signature, key):
        attrs = {
            "signature": signature, "key": ["fullseed_scaling", key],
            "status": "decoded", "residual": signature,
            "decoded_epoch": sub.node(agent)["attrs"].get("codebook_epoch") or 0.0,
            "dim_types": bench.DIM_TYPES,
        }
        obs = sub.add_node("Observation", attrs)
        sub.add_edge(agent, "observed", obs)
        nodes0 = len(list(sub.nodes()))
        edges0 = sub.edge_count()
        rss0 = bench.rss_kib()
        native_module.Substrate.scale_audit_reset()
        native_module.Substrate.scale_audit_set_enabled(True)
        cpu0 = time.process_time_ns()
        t0 = time.perf_counter_ns()
        try:
            work = int(native.run_rules())
        finally:
            native_module.Substrate.scale_audit_set_enabled(False)
        wall = time.perf_counter_ns() - t0
        cpu = time.process_time_ns() - cpu0
        rss1 = bench.rss_kib()
        counters = {str(k): int(v) for k, v in dict(native_module.Substrate.scale_audit_snapshot()).items()}
        result = {
            "status": sub.node(obs)["attrs"].get("status"),
            "covered_by": sub.node(obs)["attrs"].get("covered_by"),
            "residual": sub.node(obs)["attrs"].get("residual"),
            "transform_receipts": bench.receipts(sub, obs),
            "closure_work": work, "closure_wall_ns": wall, "closure_cpu_ns": cpu,
            "hwm_before_kib": rss0, "hwm_after_kib": rss1, "hwm_delta_kib": max(0, rss1-rss0),
            "nodes_before": nodes0, "nodes_after": len(list(sub.nodes())), "edges_after": sub.edge_count(),
            "gen_infer_counters": {k: v for k, v in counters.items() if k.startswith("gen_infer_")},
            "term_audit_counters": {k: v for k, v in counters.items()
                                    if k in ("term_units_total", "term_evals_total",
                                             "term_unit:GenInfer", "term_eval:GenInfer")},
            "scale_audit_enabled": True,
        }
        return obs, result
    bench.observe = observe


def worker(case):
    native_module, native_path = load_overlay()
    spec = importlib.util.spec_from_file_location("geninfer_v1", V1)
    bench = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bench)
    from domains.engine_provenance import build_is_stale
    bench.build_is_stale = lambda _: build_is_stale(str(TREE))
    audited_observe(bench, native_module)
    bench.LOCK = BASE / "worker_lock.json"
    bench.LOCK.write_text(json.dumps({"sources": bench.frozen(), "cases": [case]}))
    result = bench.run_case(case)
    if result["source_before"]["native_path"] != str(native_path):
        raise RuntimeError("capture points to unexpected engine")
    if result["source_before"] != result["source_after"] or not result["source_stable"]:
        raise RuntimeError("source drift during profile worker")
    print(json.dumps(result, sort_keys=True))


def main():
    if len(sys.argv) == 3 and sys.argv[1] == "--prepare":
        prepare(sys.argv[2]); return
    if len(sys.argv) == 3 and sys.argv[1] == "--worker":
        worker(json.loads(sys.argv[2])); return
    if sys.argv[1:] != ["--run"]:
        raise SystemExit("usage: --prepare 64_SHARD_SO | --run | --worker CASE_JSON")
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    native = TREE / "runners/dsl/python/substrate_rs/_native.abi3.so"
    record = TREE / "runners/dsl/python/substrate_rs/_native.build.json"
    if not native.is_file() or not record.is_file():
        raise SystemExit("prepare the current-source 64-shard overlay first")
    env = dict(os.environ)
    env.setdefault("OZMA_NO_LLM", "1")
    env.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
    rows = []
    for case in cases():
        proc = subprocess.run([sys.executable, str(RUNNER), "--worker", json.dumps(case)], cwd=ROOT,
                              env=env, text=True, capture_output=True, timeout=300)
        if proc.returncode:
            raise RuntimeError(f"worker {case['id']} failed: {proc.stderr}")
        rows.append(json.loads(proc.stdout))
    payload = {
        "schema": "GenInferTrainingWorkProfileV1Results",
        "captured_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "host": platform.platform(), "runner_sha256": sha(RUNNER),
        "protocol_sha256": sha(PROTOCOL), "analyzer_sha256": sha(ANALYZER),
        "v1_runner_sha256": sha(V1), "case_spec": cases(), "worker_count": len(rows),
        "source_stable": all(row["source_stable"] for row in rows),
        "source_sha256_by_worker": [row["source_before"]["source_sha256"] for row in rows],
        "cases": rows,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "worker_count": len(rows), "source_stable": payload["source_stable"]}))


if __name__ == "__main__":
    main()
