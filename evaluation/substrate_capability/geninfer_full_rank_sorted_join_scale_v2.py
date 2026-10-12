#!/usr/bin/env python3
"""Paired native GenInfer probe for the experimental full-rank matrix path."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import resource
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER = Path(__file__).resolve()
ANALYZER = ROOT / "evaluation/substrate_capability/analyze_geninfer_full_rank_sorted_join_scale_v2.py"
PROTOCOL = ROOT / "docs/research/engine_substrate/GENINFER_FULL_RANK_SORTED_JOIN_SCALE_V2_PREREG_20261006.md"
BASE = Path("/tmp/ocelot_geninfer_fullrank_sorted_join_scale_v2")
VARIANTS = ("nested", "sorted")
OUT = ROOT / "evaluation/reports/geninfer_full_rank_sorted_join_scale_v2_20261006.json"
sys.path.insert(0, str(ROOT))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def prepare(baseline, solver):
    from domains.engine_provenance import build_is_stale, record_build
    for variant, source in zip(VARIANTS, (baseline, solver)):
        tree = BASE / variant / "tree"
        if tree.exists():
            raise SystemExit(f"refusing to overwrite prepared overlay: {tree}")
        (tree / "runners/dsl/src").mkdir(parents=True)
        shutil.copytree(ROOT / "runners/dsl/src", tree / "runners/dsl/src", dirs_exist_ok=True)
        package = tree / "runners/dsl/python/substrate_rs"
        package.mkdir(parents=True)
        shutil.copy2(ROOT / "runners/dsl/python/substrate_rs/__init__.py", package / "__init__.py")
        shutil.copy2(ROOT / "runners/dsl/Cargo.toml", tree / "runners/dsl/Cargo.toml")
        shutil.copy2(ROOT / "runners/dsl/Cargo.lock", tree / "runners/dsl/Cargo.lock")
        native = package / "_native.abi3.so"
        shutil.copy2(source, native)
        record_build(str(tree))
        stale = build_is_stale(str(tree))
        if stale:
            raise RuntimeError(f"{variant} overlay is stale: {stale}")
        print(json.dumps({"variant": variant, "native_sha256": sha(native), "stale": stale}))


def cases():
    fixtures = [("shear_cycle", "positive"), ("reflection", "positive"),
                ("shear", "positive"), ("rank_deficient", "rank_deficient"),
                ("nonlinear", "nonlinear"), ("ambiguous_identity", "ambiguous_id")]
    return [{"id": f"{name}_n{n}_r{rep}", "family": name, "dimension": 3,
             "kind": kind, "matrix_case": name if kind == "positive" else "default",
             "relation_count": n, "replicate": rep}
            for n in (8, 32, 128, 512, 2048) for name, kind in fixtures for rep in range(2)]


def load_native(variant):
    tree = BASE / variant / "tree"
    package = tree / "runners/dsl/python/substrate_rs"
    spec = __import__("importlib.util", fromlist=["spec_from_file_location"]).spec_from_file_location(
        "substrate_rs", package / "__init__.py", submodule_search_locations=[str(package)])
    module = __import__("importlib.util", fromlist=["module_from_spec"]).module_from_spec(spec)
    sys.modules["substrate_rs"] = module
    spec.loader.exec_module(module)
    path = (package / "_native.abi3.so").resolve()
    if Path(module._native.__file__).resolve() != path:
        raise RuntimeError("selected binary was not loaded")
    sys.path[:0] = [str(ROOT / "runners/dsl/python"), str(ROOT)]
    return module._native, path, tree


def matrix_for(d, case):
    if d == 1:
        return [[-1]]
    if d == 2:
        return [[1, 1], [0, 2]]
    return {
        "default": [[1, 1, 0], [0, 1, 1], [1, 0, 1]],
        "shear_cycle": [[1, 1, 0], [0, 1, 1], [1, 0, 1]],
        "reflection": [[0, 1, 0], [1, 0, 0], [0, 0, -1]],
        "shear": [[1, 2, 0], [0, 1, 1], [0, 0, 1]],
    }[case["matrix_case"]]


def points_for(d, count):
    points = [[0] * d, *[[int(i == j) for i in range(d)] for j in range(d)],
              [1] * d, [2 if i % 2 == 0 else 1 for i in range(d)]]
    index = 1
    while len(points) < count:
        points.append([index, (index * index + 3 * index) % 37,
                       (index * 7 + index * index) % 41][:d])
        index += 1
    return points[:count]


def apply(matrix, point):
    return [sum(v * point[j] for j, v in enumerate(row)) for row in matrix]


def rows(points, dim, prefix, kind):
    out = []
    for i, point in enumerate(points):
        coords = list(point)
        if kind == "nonlinear" and dim == 3:
            coords[2] += point[0] * point[1]
        identity = f"{prefix}:0" if kind == "ambiguous_id" else f"{prefix}:{i}"
        out.append(["cell", identity, *coords, "red"])
    return out


def generator_rows(sub):
    result = []
    for node in sub.nodes("DimensionGenerator"):
        attrs = sub.node(node)["attrs"]
        if attrs.get("kind") == "linear":
            result.append({k: attrs.get(k) for k in ("name", "kind", "matrix", "coord_dims")})
    return result


def receipts(sub, observation):
    result = []
    for node in sub.neighbours(observation, "has_transform"):
        attrs = sub.node(node)["attrs"]
        result.append({k: attrs.get(k) for k in ("source", "generator", "generators", "base", "dim", "dims", "k", "ks", "transforms") if k in attrs})
    return result


def worker(variant, case, audit):
    native_module, native_path, tree = load_native(variant)
    from substrate.boot_core import boot_core
    from domains import reflective_faculty as rf
    from domains.engine_provenance import rust_source_hashes
    d = case["dimension"]
    matrix = matrix_for(d, case)
    dim_types = ["pred", "id", *[f"coord:{i}" for i in range(d)], "val"]
    train_points = points_for(d, case["relation_count"])
    if case["kind"] == "rank_deficient":
        train_points = [[i, (i * i + 3 * i) % 37, 0] for i in range(case["relation_count"])]
    identity_kind = "ambiguous_id" if case["kind"] == "ambiguous_id" else "positive"
    train_base = rows(train_points, d, "train", identity_kind)
    train_target = rows([apply(matrix, p) for p in train_points], d, "train", case["kind"])
    if case["kind"] == "rank_deficient":
        held_points = [[i % 3, (2 * i) % 4, 0] for i in range(d + 2)]
    else:
        held_points = [[2 + i, (i + 1) % 3, (2 * i) % 4][:d] for i in range(d + 2)]
    held_base = rows(held_points, d, "held", identity_kind)
    held_target = rows([apply(matrix, p) for p in held_points], d, "held", case["kind"])
    sub, agent = boot_core()
    native = rf._native_eval2(sub)
    rf._ensure_shape_decode_loop(sub, native, agent)
    sub.set_attr(agent, "gen_infer_enabled", 1.0)
    sub.add_node("ShapeSignature", {"name": "training_base", "signature": json.dumps(train_base),
        "kind": "faculty", "faculty": "full_rank_training", "dim_types": dim_types})
    sub.add_node("ShapeSignature", {"name": "heldout_base", "signature": json.dumps(held_base),
        "kind": "faculty", "faculty": "full_rank_heldout", "dim_types": dim_types})
    initial_generators = generator_rows(sub)
    before_sources = rust_source_hashes(str(ROOT))
    phases = {}
    for stage, signature in (("train", train_target), ("heldout", held_target)):
        obs = sub.add_node("Observation", {"signature": signature,
            "key": ["full_rank_matrix_native_v1_1", case["id"], stage],
            "status": "decoded", "residual": signature,
            "decoded_epoch": sub.node(agent)["attrs"].get("codebook_epoch") or 0.0,
            "dim_types": dim_types})
        sub.add_edge(agent, "observed", obs)
        native_module.Substrate.scale_audit_reset()
        native_module.Substrate.scale_audit_set_enabled(audit)
        t0 = time.perf_counter_ns(); cpu0 = time.process_time_ns()
        try:
            closure_work = int(native.run_rules())
        finally:
            native_module.Substrate.scale_audit_set_enabled(False)
        wall = time.perf_counter_ns() - t0; cpu = time.process_time_ns() - cpu0
        counters = dict(native_module.Substrate.scale_audit_snapshot()) if audit else {}
        attrs = sub.node(obs)["attrs"]
        phases[stage] = {"status": attrs.get("status"), "covered_by": attrs.get("covered_by"),
            "residual": attrs.get("residual"), "receipts": receipts(sub, obs),
            "closure_work": closure_work, "wall_ns": wall, "cpu_ns": cpu,
            "generators": generator_rows(sub),
            "full_rank_counters": {k: int(v) for k, v in counters.items()
                if k.startswith("gen_infer_full_rank_")}}
    after_sources = rust_source_hashes(str(ROOT))
    return {"variant": variant, "case": case, "audit": audit,
        "native_path": str(native_path), "native_sha256": sha(native_path),
        "source_before": before_sources, "source_after": after_sources,
        "source_stable": before_sources == after_sources,
        "expected_matrix": matrix, "training_oracle_exact": train_target == rows(
            [apply(matrix, p) for p in train_points], d, "train", identity_kind),
        "initial_generators": initial_generators,
        "phases": phases, "final_generators": generator_rows(sub),
        "process_maxrss_platform_units": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)}


def main():
    args = sys.argv[1:]
    if len(args) == 3 and args[0] == "--prepare":
        prepare(*args[1:]); return
    if len(args) == 4 and args[0] == "--worker":
        print(json.dumps(worker(args[1], json.loads(args[2]), args[3] == "audit"), sort_keys=True)); return
    if args != ["--run"]:
        raise SystemExit("usage: --prepare BASELINE_SO SOLVER_SO | --worker VARIANT CASE_JSON audit|off | --run")
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    tasks = cases()
    workers = []
    env = dict(os.environ)
    env.setdefault("OZMA_NO_LLM", "1"); env.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
    for case_index, case in enumerate(tasks):
        for audit_index, audit in enumerate((False, True)):
            variant_order = VARIANTS if (case_index + audit_index) % 2 == 0 else tuple(reversed(VARIANTS))
            for variant in variant_order:
                proc = subprocess.run([sys.executable, str(RUNNER), "--worker", variant,
                    json.dumps(case), "audit" if audit else "off"], cwd=ROOT, env=env,
                    text=True, capture_output=True, timeout=600)
                if proc.returncode:
                    raise RuntimeError(f"{variant}/{case['id']}/audit={audit}: {proc.stderr}")
                workers.append(json.loads(proc.stdout))
    payload = {"schema": "GenInferFullRankSortedJoinScaleV2",
        "captured_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "host": platform.platform(), "runner_sha256": sha(RUNNER),
        "analyzer_sha256": sha(ANALYZER), "protocol_sha256": sha(PROTOCOL),
        "case_spec": tasks, "worker_count": len(workers), "workers": workers}
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": OUT.relative_to(ROOT).as_posix(), "worker_count": len(workers)}))


if __name__ == "__main__":
    main()
