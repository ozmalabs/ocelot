#!/usr/bin/env python3
"""Paired full-seed GenInfer closure capture on 64- and 512-shard engines.

The variant extensions are temporary overlays produced by the protocol. This
runner preloads the selected package before importing the V1 workload, which
otherwise prepends the canonical extension path.
"""
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
sys.path.insert(0, str(ROOT))
V1 = ROOT / "evaluation/substrate_capability/substrate_geninfer_fullseed_scaling_v1.py"
ANALYZER = ROOT / "evaluation/substrate_capability/analyze_substrate_geninfer_cow_shard_closure_v1.py"
BASE = Path("/tmp/ocelot_fullseed_cow_shards_v10")
OUT = ROOT / "evaluation/reports/substrate_geninfer_cow_shard_closure_v1_20261006.json"
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_GENINFER_COW_SHARD_CLOSURE_V1_PREREG_20261006.md"
VARIANTS = {"64": BASE / "shards64/tree", "512": BASE / "shards512/tree"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cases():
    out = []
    for n in (4, 16, 64):
        for rep in (1, 2, 3):
            out.append({"id": f"positive_n{n}_b5_r{rep}", "kind": "positive", "n": n, "bound": 5, "repeat": rep})
    for kind in ("disabled", "predicate_corrupt"):
        for rep in (1, 2, 3):
            out.append({"id": f"{kind}_n8_b5_r{rep}", "kind": kind, "n": 8, "bound": 5, "repeat": rep})
    return out


def load_variant(tree: Path):
    pkg = tree / "runners/dsl/python/substrate_rs"
    native = (pkg / "_native.abi3.so").resolve()
    spec = importlib.util.spec_from_file_location("substrate_rs", pkg / "__init__.py", submodule_search_locations=[str(pkg)])
    module = importlib.util.module_from_spec(spec)
    sys.modules["substrate_rs"] = module
    spec.loader.exec_module(module)
    if Path(module._native.__file__).resolve() != native:
        raise RuntimeError(f"wrong engine loaded: {module._native.__file__}")
    sys.path[:0] = [str(ROOT / "runners/dsl/python"), str(ROOT)]
    return native


def worker(variant: str, case: dict):
    tree = VARIANTS[variant]
    native = load_variant(tree)
    spec = importlib.util.spec_from_file_location("geninfer_v1", V1)
    bench = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bench)
    from domains.engine_provenance import build_is_stale
    bench.build_is_stale = lambda _: build_is_stale(str(tree))
    bench.LOCK = BASE / f"shards{variant}" / "worker_lock.json"
    bench.LOCK.write_text(json.dumps({"sources": bench.frozen(), "cases": [case]}))
    result = bench.run_case(case)
    if result["source_before"]["native_path"] != str(native):
        raise RuntimeError("result provenance does not name selected variant")
    if result["source_before"] != result["source_after"] or not result["source_stable"]:
        raise RuntimeError("source drift during case")
    print(json.dumps(result, sort_keys=True))


def prepare(binary_paths):
    from domains.engine_provenance import build_is_stale, record_build
    for variant, binary in zip(("64", "512"), binary_paths):
        source = Path(binary).resolve()
        if not source.is_file():
            raise SystemExit(f"missing {variant}-shard binary: {source}")
        tree = VARIANTS[variant]
        (tree / "runners/dsl/src").mkdir(parents=True, exist_ok=True)
        shutil.copytree(ROOT / "runners/dsl/src", tree / "runners/dsl/src", dirs_exist_ok=True)
        package = tree / "runners/dsl/python/substrate_rs"
        package.mkdir(parents=True, exist_ok=True)
        shutil.copytree(ROOT / "runners/dsl/python/substrate_rs", package, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("_native.abi3.so", "_native.build.json"))
        for filename in ("Cargo.toml", "Cargo.lock"):
            shutil.copy2(ROOT / "runners/dsl" / filename, tree / "runners/dsl" / filename)
        native = package / "_native.abi3.so"
        shutil.copy2(source, native)
        record = record_build(str(tree))
        stale = build_is_stale(str(tree))
        if record is None or stale:
            raise RuntimeError(f"invalid {variant}-shard build record: {stale}")
        print(json.dumps({"variant": variant, "native": str(native), "sha256": sha(native), "stale": stale}))


def main():
    if len(sys.argv) == 4 and sys.argv[1] == "--prepare":
        prepare(sys.argv[2:])
        return
    if len(sys.argv) == 4 and sys.argv[1] == "--worker":
        worker(sys.argv[2], json.loads(sys.argv[3]))
        return
    if sys.argv[1:] != ["--run"]:
        raise SystemExit("usage: --prepare BINARY64 BINARY512 | --run | --worker VARIANT CASE_JSON")
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    for variant, tree in VARIANTS.items():
        native = tree / "runners/dsl/python/substrate_rs/_native.abi3.so"
        record = tree / "runners/dsl/python/substrate_rs/_native.build.json"
        if not native.is_file() or not record.is_file():
            raise SystemExit(f"missing prepared {variant}-shard overlay at {tree}")
    cs = cases()
    env = dict(os.environ)
    env.setdefault("OZMA_NO_LLM", "1")
    env.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
    rows = []
    for index, case in enumerate(cs):
        order = ("64", "512") if index % 2 == 0 else ("512", "64")
        for variant in order:
            proc = subprocess.run([sys.executable, str(RUNNER), "--worker", variant, json.dumps(case)],
                                  cwd=ROOT, env=env, text=True, capture_output=True, timeout=300)
            if proc.returncode:
                raise RuntimeError(f"worker failed for {variant}/{case['id']}: {proc.stderr}")
            row = json.loads(proc.stdout)
            row["variant"] = variant
            row["pair_order"] = list(order)
            rows.append(row)
    payload = {
        "schema": "GenInferCowShardClosureV1Results",
        "captured_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "host": platform.platform(),
        "protocol_sha256": sha(PROTOCOL),
        "runner_sha256": sha(RUNNER),
        "v1_runner_sha256": sha(V1),
        "analyzer_sha256": sha(ANALYZER),
        "case_spec": cs,
        "case_count": len(cs),
        "worker_count": len(rows),
        "source_stable": all(row["source_stable"] for row in rows),
        "source_sha256_by_worker": [row["source_before"]["source_sha256"] for row in rows],
        "cases": rows,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "worker_count": len(rows), "source_stable": payload["source_stable"]}))


if __name__ == "__main__":
    main()
