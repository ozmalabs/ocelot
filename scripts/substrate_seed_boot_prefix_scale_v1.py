#!/usr/bin/env python3
"""Unprofiled full seed-loader prefix size envelope."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python"), str(ROOT / "scripts")]
LOCK = ROOT / "evaluation/substrate_capability/seed_boot_prefix_scale_lock_20260925.json"
CORPUS = ROOT / "evaluation/substrate_capability/problem_shape_eventized_rule_order_seed_corpus_lock_v1_7_20260925.json"
PREREG = ROOT / "docs/research/engine_substrate/SUBSTRATE_SEED_BOOT_PREFIX_SCALE_PREREG_20260925.md"
OUT = ROOT / "evaluation/reports/substrate_seed_boot_prefix_scale_v1_20260925.json"
PART = ROOT / "evaluation/reports/substrate_seed_boot_prefix_scale_v1_partial_20260925.json"
SOURCES = [
    "scripts/substrate_problem_shape_rule_order_seed_transform_v1_4.py",
    "scripts/substrate_problem_shape_rule_order_preservation_v1_7.py",
    "substrate/boot_all.py", "substrate/world_adapter.py", "substrate/seed_loader.py",
    "domains/self_model.py",
    "runners/dsl/python/substrate_rs/_native.abi3.so",
    "runners/dsl/python/substrate_rs/_native.build.json",
    "evaluation/substrate_capability/problem_shape_eventized_rule_order_seed_corpus_lock_v1_7_20260925.json",
]
SIZE_POINTS = [128, 256, 512, 737]
CHILD = """
import hashlib,json,resource,sys,time
from substrate.world_adapter import WorldAdapter
from substrate.boot_all import load_all_seeds
from substrate_rs import _native
w0,c0=time.perf_counter_ns(),time.process_time_ns();a=WorldAdapter(seeds=());r=load_all_seeds(a,seed_dir=sys.argv[1]);wall=time.perf_counter_ns()-w0;cpu=time.process_time_ns()-c0
def h(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
rules=sorted((x for x in a.inner.rule_access_sets() if x[2]),key=lambda x:int(x[0]));names=[str(x[1]) for x in rules]
print(json.dumps({'wall_ns':wall,'cpu_ns':cpu,'peak_rss_native_units':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'report':r,'node_count':a.inner.node_count(),'edge_count':a.inner.edge_count(),'graph_sha256':h(a.inner.graph_to_dict()),'grammar_sha256':h(a.inner.grammar_to_json()),'rule_store_sha256':h(a.inner.export_rules()),'rule_access_sha256':h(a.inner.rule_access_sets()),'active_rule_count':len(names),'rule_order':names,'rule_order_sha256':h(names),'process_id':__import__('os').getpid()}))
"""


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_hashes() -> dict[str, str]:
    return {rel: sha(ROOT / rel) for rel in SOURCES}


def build_full_snapshot():
    import importlib.util
    path = ROOT / "scripts/substrate_problem_shape_rule_order_seed_transform_v1_4.py"
    spec = importlib.util.spec_from_file_location("seed_transform_v14", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module.build()


def make_prefixes(full_seed: Path, expected_count: int) -> tuple[dict, list[str]]:
    from substrate.boot_all import _build_seed_index, _topo_order, _read_seed_index
    index, paths = _build_seed_index(str(full_seed))
    full_order = _topo_order(index)
    if len(full_order) != expected_count:
        raise RuntimeError(f"expected {expected_count} topological seed IDs, found {len(full_order)}")
    temp = Path(tempfile.mkdtemp(prefix="ocelot_seed_boot_prefix_scale_v1_"))
    subsets = {}
    manifests = []
    for size in SIZE_POINTS:
        order = full_order[:size]
        seed_dir = temp / f"n{size}"
        seed_dir.mkdir()
        rels = set()
        if size == len(full_order):
            rels.update(p.relative_to(full_seed) for p in full_seed.rglob("*.json"))
        else:
            for sid in order:
                rels.add(Path(paths[sid]).relative_to(full_seed))
        for rel in sorted(rels):
            src = full_seed / rel
            dst = seed_dir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            if not dst.exists():
                shutil.copyfile(src, dst)
                dst.chmod(0o444)
        for directory in sorted((p for p in seed_dir.rglob("*") if p.is_dir()), key=lambda p: len(p.parts), reverse=True):
            directory.chmod(0o555)
        seed_dir.chmod(0o555)
        subset_index, _ = _read_seed_index(str(seed_dir))
        subset_order = _topo_order(subset_index)
        if subset_order != order:
            raise RuntimeError(f"N={size}: selected manifests do not retain the full-order prefix")
        file_rows = [(p.relative_to(seed_dir).as_posix(), sha(p)) for p in sorted(seed_dir.rglob("*.json"))]
        subsets[str(size)] = {"seed_dir": str(seed_dir), "seed_id_count": len(subset_index),
                              "manifest_file_count": len(file_rows), "order": order,
                              "subset_digest": hashlib.sha256(json.dumps(file_rows, separators=(",", ":")).encode()).hexdigest()}
        manifests.extend((str(size), sid, str(paths[sid])) for sid in order)
    return {"temp_root": str(temp), "full_seed_dir": str(full_seed), "full_seed_id_count": len(full_order),
            "full_physical_manifest_count": len(list(full_seed.rglob("*.json"))),
            "full_order_sha256": hashlib.sha256(json.dumps(full_order, separators=(",", ":")).encode()).hexdigest(),
            "subsets": subsets}, full_order


def run_worker(seed_dir: str, mode: str) -> tuple[dict, dict]:
    from substrate.boot_all import _read_seed_index, _seed_index_cache_path
    cache = Path(_seed_index_cache_path(seed_dir))
    if mode == "cold":
        cache.unlink(missing_ok=True)
        before = None
    else:
        _read_seed_index(seed_dir)
        before = sha(cache)
    env = {**os.environ, "PYTHONHASHSEED": "0",
           "PYTHONPATH": f"{ROOT}:{ROOT / 'runners/dsl/python'}:{ROOT / 'scripts'}"}
    proc = subprocess.run([sys.executable, "-c", CHILD, seed_dir], cwd=ROOT,
                          env=env, capture_output=True, text=True, timeout=900)
    if proc.returncode:
        raise RuntimeError(f"{mode} scale boot failed: {proc.stderr[-2000:]}")
    row = json.loads(proc.stdout.strip().splitlines()[-1])
    after = sha(cache)
    if before is not None and before != after:
        raise RuntimeError("warm cache changed during load")
    return row, {"before": before, "after": after}


def main() -> int:
    lock = json.loads(LOCK.read_text())
    if sha(PREREG) != lock["preregistration_sha256"] or sha(Path(__file__)) != lock["runner_sha256"]:
        raise SystemExit("preregistration or runner hash mismatch")
    if source_hashes() != lock["sources"]:
        raise SystemExit("source/build lock mismatch")
    from substrate_problem_shape_rule_order_preservation_v1_7 import seed_corpus_digest
    corpus = json.loads(CORPUS.read_text())
    if corpus["corpus_digest"] != lock["ordered_corpus_digest"] or seed_corpus_digest() != lock["ordered_corpus_digest"]:
        raise SystemExit("ordered source corpus digest mismatch")
    env = {**os.environ, "PYTHONPATH": f"{ROOT}:{ROOT / 'runners/dsl/python'}:{ROOT / 'scripts'}"}
    stale = subprocess.check_output([sys.executable, "-c",
        "from domains.engine_provenance import build_is_stale;print('\\n'.join(build_is_stale('.')))"],
        cwd=ROOT, env=env, text=True).strip()
    if stale:
        raise SystemExit(f"native build stale: {stale}")
    if OUT.exists() or PART.exists():
        raise SystemExit("refusing to overwrite prior scale result/checkpoint")
    full = build_full_snapshot()
    if full["source_corpus_digest"] != lock["canonical_source_digest"]:
        raise SystemExit("canonical source corpus digest mismatch")
    base = Path(full["baseline_seed_dir"])
    for item in corpus["manifests"]:
        if sha(base / item["path"]) != item["sha256"]:
            raise SystemExit(f"baseline snapshot differs from corpus lock: {item['path']}")
    snapshot, _ = make_prefixes(base, lock["full_index_seed_count"])
    arms = []
    for size, data in snapshot["subsets"].items():
        order = [("cold", 1), ("warm", 1), ("warm", 2), ("cold", 2)]
        for mode, replicate in order:
            row, cache = run_worker(data["seed_dir"], mode)
            arm = {"requested_size": int(size), "replicate": replicate,
                   "cache_mode": mode, "cache": cache, "worker": row}
            arms.append(arm)
            PART.write_text(json.dumps({"snapshot": snapshot, "arms": arms}, indent=2, sort_keys=True) + "\n")
            print(json.dumps({"size": int(size), "replicate": replicate, "mode": mode,
                              "wall_ns": row["wall_ns"], "nodes": row["node_count"],
                              "edges": row["edge_count"], "rules": row["active_rule_count"]}), flush=True)
    state_keys = ("report", "node_count", "edge_count", "graph_sha256", "grammar_sha256",
                  "rule_store_sha256", "rule_access_sha256", "active_rule_count", "rule_order", "rule_order_sha256")
    parity = {}
    for size in SIZE_POINTS:
        rows = [a["worker"] for a in arms if a["requested_size"] == size]
        fps = [{key: row[key] for key in state_keys} for row in rows]
        parity[str(size)] = len(rows) == 4 and all(fp == fps[0] for fp in fps)
    if source_hashes() != lock["sources"] or sha(Path(__file__)) != lock["runner_sha256"]:
        raise RuntimeError("locked inputs changed during scale run")
    result = {"schema_version": 1, "probe_id": "seed-boot-prefix-scale-v1-20260925",
              "runner_sha256": sha(Path(__file__)), "lock_sha256": sha(LOCK),
              "source_hashes_after": source_hashes(), "snapshot": snapshot,
              "arms": arms, "state_parity_by_size": parity,
              "all_state_parity": all(parity.values()),
              "unique_processes": len({a["worker"]["process_id"] for a in arms}) == 16,
              "interpretation": "Exploratory nested prefix scale envelope on one authored corpus; each size has two cold and two warm fresh processes; no asymptotic or cross-corpus claim."}
    result["all_gates_pass"] = result["all_state_parity"] and result["unique_processes"]
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    PART.unlink(missing_ok=True)
    shutil.rmtree(snapshot["temp_root"], ignore_errors=True)
    print(json.dumps({"all_gates_pass": result["all_gates_pass"],
                      "state_parity_by_size": parity, "output": str(OUT)}))
    return 0 if result["all_gates_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
