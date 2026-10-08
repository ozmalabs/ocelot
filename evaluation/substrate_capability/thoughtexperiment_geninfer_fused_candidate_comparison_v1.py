#!/usr/bin/env python3
"""Paired baseline/fused GenInfer candidate-validation comparison."""
from __future__ import annotations

import hashlib
import importlib.util
import itertools
import json
import os
import platform
import random
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER = Path(__file__).resolve()
ANALYZER = ROOT / "evaluation/substrate_capability/analyze_geninfer_fused_candidate_comparison_v1.py"
PROTOCOL = ROOT / "docs/research/engine_substrate/GENINFER_FUSED_CANDIDATE_COMPARISON_V1_PREREG_20261006.md"
FULLSEED = ROOT / "evaluation/substrate_capability/substrate_geninfer_fullseed_scaling_v1.py"
BASE_PROFILE = ROOT / "evaluation/substrate_capability/substrate_geninfer_training_work_profile_v1.py"
NONLINEAR = ROOT / "scripts/substrate_nonlinear_dimension_induction_v1_5.py"
SOURCES = [
    "domains/engine_provenance.py", "domains/reflective_faculty.py",
    "substrate/boot_core.py", "substrate/seed_loader.py",
    "runners/dsl/src/shape_decode.rs", "runners/dsl/src/term.rs",
    "runners/dsl/src/graph.rs", "runners/dsl/src/substrate.rs",
    "runners/dsl/src/rewrite.rs", "runners/dsl/src/py.rs",
    "runners/dsl/src/persist.rs", "runners/dsl/src/grammar.rs",
    "runners/dsl/src/sym.rs", "runners/dsl/src/lib.rs",
    "runners/dsl/src/scale_audit.rs", "runners/dsl/Cargo.toml",
    "runners/dsl/Cargo.lock", "runners/dsl/python/substrate_rs/__init__.py",
    "runners/dsl/python/substrate_rs/_native.build.json",
    "docs/research/engine_substrate/SUBSTRATE_NONLINEAR_DIMENSION_INDUCTION_V1_3_PREREG_20261005.md",
]
BASE = Path("/tmp/ocelot_geninfer_fused_candidate_v1")
OVERLAYS = {name: BASE / name / "tree" for name in ("baseline", "fused")}
OUT = ROOT / "evaluation/reports/geninfer_fused_candidate_comparison_v1_20261006.json"
sys.path.insert(0, str(ROOT))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def matrix_fit(source, wanted, bound):
    tgt = {r[1]: (r[2], r[3]) for r in wanted}
    bmap = {r[1]: (r[2], r[3]) for r in source}
    mins = (min(x for x, _ in bmap.values()), min(y for _, y in bmap.values()))
    for m in itertools.product(range(-bound, bound + 1), repeat=4):
        if m == (1, 0, 0, 1):
            continue
        if all(tgt.get(i) == (m[0] * (x - mins[0]) + m[1] * (y - mins[1]),
                              m[2] * (x - mins[0]) + m[3] * (y - mins[1]))
               for i, (x, y) in bmap.items()):
            return list(m)
    return None


def module_at(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def prepare(binary_paths):
    from domains.engine_provenance import build_is_stale, record_build
    for variant, binary in zip(("baseline", "fused"), binary_paths):
        source = Path(binary).resolve()
        if not source.is_file():
            raise SystemExit(f"missing {variant} engine binary: {source}")
        tree = OVERLAYS[variant]
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
            raise RuntimeError(f"{variant}: invalid overlay build record {stale}")
        print(json.dumps({"variant": variant, "native": str(native), "sha256": sha(native), "stale": stale}))


def case_spec():
    fullseed = [
        {"family": "fullseed_linear", "id": f"positive_n{n}_b{bound}_r{rep}",
         "kind": "positive", "n": n, "bound": bound, "repeat": rep}
        for n in (4, 64) for bound in (3, 5, 7) for rep in (1, 2, 3)
    ]
    # Recreate the preregistered fixture without importing its top-level engine
    # preamble: that guard intentionally rejects the stale canonical extension.
    dt = ["pred", "id", "coord:r", "coord:c", "val"]
    train = [(0, 0), (1, 0), (0, 1), (1, 1), (0, 2), (1, 2)]
    transfer = [(0, 0), (2, 0), (0, 2), (2, 2), (1, 3), (3, 3)]
    families = {"linear": lambda x, y: (x + y, 2 * y),
                "coupled_quadratic": lambda x, y: (x + x * y, y + x * x)}
    def base(points, shape):
        return [["cell", f"{shape}:{i}", x, y, "red"] for i, (x, y) in enumerate(points)]
    def target(points, family, shape):
        return [["cell", f"{shape}:{i}", *families[family](x, y), "red"]
                for i, (x, y) in enumerate(points)]
    nonlinear_lock = {"cases": []}
    for family in families:
        for replicate in range(2):
            training_base = base(train, f"train{replicate}")
            training_target = target(train, family, f"train{replicate}")
            transfer_base = base(transfer, f"transfer{replicate}")
            transfer_target = target(transfer, family, f"transfer{replicate}")
            bound = max(max(abs(row[2]), abs(row[3])) for row in training_base + training_target)
            nonlinear_lock["cases"].append({"family": family, "replicate": replicate,
                "training_base": training_base, "training_target": training_target,
                "transfer_base": transfer_base, "transfer_target": transfer_target,
                "matrix_bound": bound,
                "any_exact_linear_fit": matrix_fit(training_base, training_target, bound) is not None,
                "dim_types": dt})
    nonlinear = [
        {"family": "nonlinear_transfer", "id": f"{case['family']}_r{case['replicate']}",
         "kind": "nonlinear", "case": case}
        for case in nonlinear_lock["cases"]
        if case["family"] in ("linear", "coupled_quadratic") and case["replicate"] in (0, 1)
    ]
    return fullseed + nonlinear


def load_engine(variant):
    tree = OVERLAYS[variant]
    package = tree / "runners/dsl/python/substrate_rs"
    spec = importlib.util.spec_from_file_location("substrate_rs", package / "__init__.py",
                                                   submodule_search_locations=[str(package)])
    module = importlib.util.module_from_spec(spec)
    sys.modules["substrate_rs"] = module
    spec.loader.exec_module(module)
    native_path = (package / "_native.abi3.so").resolve()
    if Path(module._native.__file__).resolve() != native_path:
        raise RuntimeError("selected overlay did not load")
    sys.path[:0] = [str(ROOT / "runners/dsl/python"), str(ROOT)]
    return module._native, native_path, tree


def run_fullseed(case, audit_enabled, native_module, tree):
    bench = module_at("fullseed_v1", FULLSEED)
    from domains.engine_provenance import build_is_stale
    bench.build_is_stale = lambda _: build_is_stale(str(tree))
    bench.LOCK = tree / f"worker_lock_{os.getpid()}.json"

    def observe(sub, agent, native, signature, key):
        attrs = {"signature": signature, "key": ["fullseed_scaling", key],
                 "status": "decoded", "residual": signature,
                 "decoded_epoch": sub.node(agent)["attrs"].get("codebook_epoch") or 0.0,
                 "dim_types": bench.DIM_TYPES}
        obs = sub.add_node("Observation", attrs)
        sub.add_edge(agent, "observed", obs)
        nodes0 = len(list(sub.nodes())); edges0 = sub.edge_count(); rss0 = bench.rss_kib()
        native_module.Substrate.scale_audit_reset()
        native_module.Substrate.scale_audit_set_enabled(audit_enabled)
        cpu0 = time.process_time_ns(); t0 = time.perf_counter_ns()
        try:
            work = int(native.run_rules())
        finally:
            native_module.Substrate.scale_audit_set_enabled(False)
        wall = time.perf_counter_ns() - t0; cpu = time.process_time_ns() - cpu0; rss1 = bench.rss_kib()
        counters = {str(k): int(v) for k, v in dict(native_module.Substrate.scale_audit_snapshot()).items()} if audit_enabled else {}
        return obs, {
            "status": sub.node(obs)["attrs"].get("status"),
            "covered_by": sub.node(obs)["attrs"].get("covered_by"),
            "residual": sub.node(obs)["attrs"].get("residual"),
            "transform_receipts": bench.receipts(sub, obs), "closure_work": work,
            "closure_wall_ns": wall, "closure_cpu_ns": cpu, "hwm_delta_kib": max(0, rss1-rss0),
            "nodes_before": nodes0, "nodes_after": len(list(sub.nodes())), "edges_after": sub.edge_count(),
            "gen_infer_counters": {k: v for k, v in counters.items() if k.startswith("gen_infer_")},
            "term_audit_counters": {k: v for k, v in counters.items()
                                    if k in ("term_units_total", "term_evals_total", "term_unit:GenInfer", "term_eval:GenInfer")},
            "audit_enabled": audit_enabled,
        }
    bench.observe = observe
    bench.LOCK.write_text(json.dumps({"sources": bench.frozen(), "cases": [case]}))
    return bench.run_case(case)


def run_nonlinear(case, audit_enabled, native_module):
    fullseed_helpers = module_at("fullseed_helpers", FULLSEED)
    from substrate.boot_core import boot_core
    from domains import reflective_faculty as rf
    dim_types = case["dim_types"]
    sub, agent = boot_core()
    native = rf._native_eval2(sub)
    rf._ensure_shape_decode_loop(sub, native, agent)
    sub.set_attr(agent, "gen_infer_enabled", 1.0)
    sub.add_node("ShapeSignature", {"name": "training_base", "signature": json.dumps(case["training_base"]),
                                    "kind": "faculty", "faculty": "training_base", "dim_types": dim_types})
    sub.add_node("ShapeSignature", {"name": "transfer_base", "signature": json.dumps(case["transfer_base"]),
                                    "kind": "faculty", "faculty": "transfer_base", "dim_types": dim_types})
    def generators(graph):
        return [{"name": graph.node(n)["attrs"].get("name"),
                 "kind": graph.node(n)["attrs"].get("kind"),
                 "matrix": graph.node(n)["attrs"].get("matrix"),
                 "coord_dims": graph.node(n)["attrs"].get("coord_dims")}
                for n in graph.nodes("DimensionGenerator")]
    initial = generators(sub)
    events = []
    for stage, signature in (("train", case["training_target"]), ("transfer", case["transfer_target"])):
        obs = sub.add_node("Observation", {"signature": signature,
            "key": ["fused_candidate_compare", case["family"], str(case["replicate"]), stage],
            "status": "decoded", "residual": signature,
            "decoded_epoch": sub.node(agent)["attrs"].get("codebook_epoch") or 0.0,
            "dim_types": dim_types})
        sub.add_edge(agent, "observed", obs)
        before_quanta = len(list(sub.nodes("CapabilityAxis")))
        native_module.Substrate.scale_audit_reset()
        native_module.Substrate.scale_audit_set_enabled(audit_enabled)
        cpu0 = time.process_time_ns(); t0 = time.perf_counter_ns()
        try:
            work = int(native.run_rules())
        finally:
            native_module.Substrate.scale_audit_set_enabled(False)
        wall = time.perf_counter_ns() - t0; cpu = time.process_time_ns() - cpu0
        counters = {str(k): int(v) for k, v in dict(native_module.Substrate.scale_audit_snapshot()).items()} if audit_enabled else {}
        events.append({"stage": stage, "status": sub.node(obs)["attrs"].get("status"),
            "covered_by": sub.node(obs)["attrs"].get("covered_by"),
            "residual": sub.node(obs)["attrs"].get("residual"),
            "transform_receipts": fullseed_helpers.receipts(sub, obs),
            "quanta_added": len(list(sub.nodes("CapabilityAxis"))) - before_quanta,
            "generators": generators(sub), "closure_work": work,
            "closure_wall_ns": wall, "closure_cpu_ns": cpu,
            "gen_infer_counters": {k: v for k, v in counters.items() if k.startswith("gen_infer_")},
            "term_audit_counters": {k: v for k, v in counters.items()
                if k in ("term_units_total", "term_evals_total", "term_unit:GenInfer", "term_eval:GenInfer")}})
    return {"family": case["family"], "replicate": case["replicate"], "events": events,
        "initial_generators": initial, "final_generators": generators(sub),
        "training_expected_matrix": matrix_fit(case["training_base"], case["training_target"], case["matrix_bound"]),
        "audit_enabled": audit_enabled}


def worker(variant, task, audit_enabled):
    native_module, native_path, tree = load_engine(variant)
    if task["kind"] == "positive":
        result = run_fullseed(task, audit_enabled, native_module, tree)
        semantic = {key: result.get(key) for key in (
            "case", "matrix", "target_acquired_during_training", "training_acquired_generator_names",
            "training_quanta_added", "training_oracle_exact_match", "heldout_exact_match",
            "corrupted_heldout_exact_match", "initial_linear_generators", "linear_generators_after_all")}
        phases = {name: result[name] for name in ("train", "heldout", "corrupted_heldout")}
        source_before, source_after = result["source_before"], result["source_after"]
        stable = result["source_stable"]
    else:
        fixture = task["case"]
        result = run_nonlinear(fixture, audit_enabled, native_module)
        semantic = {key: result.get(key) for key in ("family", "replicate", "initial_generators", "final_generators", "training_expected_matrix")}
        phases = {event["stage"]: event for event in result["events"]}
        from domains.engine_provenance import rust_source_hashes
        source_before = {"source_sha256": rust_source_hashes(str(ROOT)), "native_path": str(native_path), "native_sha256": sha(native_path)}
        source_after = {"source_sha256": rust_source_hashes(str(ROOT)), "native_path": str(native_path), "native_sha256": sha(native_path)}
        stable = source_before == source_after
    if Path(native_module.__file__).resolve() != native_path:
        raise RuntimeError("native package provenance changed")
    print(json.dumps({"pid": os.getpid(), "variant": variant, "task": task,
        "audit_enabled": audit_enabled, "native_path": str(native_path), "native_sha256": sha(native_path),
        "source_before": source_before, "source_after": source_after, "source_stable": stable,
        "semantic": semantic, "phases": phases}, sort_keys=True))


def main():
    if len(sys.argv) == 4 and sys.argv[1] == "--prepare":
        prepare(sys.argv[2:4]); return
    if len(sys.argv) == 5 and sys.argv[1] == "--worker":
        worker(sys.argv[2], json.loads(sys.argv[3]), sys.argv[4] == "audit"); return
    if sys.argv[1:] != ["--run"]:
        raise SystemExit("usage: --prepare BASELINE_SO FUSED_SO | --run | --worker VARIANT TASK_JSON audit|off")
    if OUT.exists():
        raise SystemExit(f"refusing to overwrite {OUT}")
    for tree in OVERLAYS.values():
        native = tree / "runners/dsl/python/substrate_rs/_native.abi3.so"
        record = native.with_name("_native.build.json")
        if not native.is_file() or not record.is_file():
            raise SystemExit("prepare both source-matched engine overlays first")
    tasks = case_spec()
    pairs = [(task, audit) for task in tasks for audit in (False, True)]
    random.Random(20261006).shuffle(pairs)
    env = dict(os.environ); env.setdefault("OZMA_NO_LLM", "1"); env.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
    rows = []
    for pair_index, (task, audit) in enumerate(pairs):
        variants = ("baseline", "fused") if pair_index % 2 == 0 else ("fused", "baseline")
        for variant in variants:
            proc = subprocess.run([sys.executable, str(RUNNER), "--worker", variant, json.dumps(task),
                                   "audit" if audit else "off"], cwd=ROOT, env=env,
                                  text=True, capture_output=True, timeout=600)
            if proc.returncode:
                raise RuntimeError(f"{variant}/{task['id']}/audit={audit} failed: {proc.stderr}")
            rows.append(json.loads(proc.stdout))
    payload = {"schema": "GenInferFusedCandidateComparisonV1Results",
        "captured_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "host": platform.platform(),
        "runner_sha256": sha(RUNNER), "analyzer_sha256": sha(ANALYZER),
        "protocol_sha256": sha(PROTOCOL), "fullseed_runner_sha256": sha(FULLSEED),
        "base_profile_sha256": sha(BASE_PROFILE), "nonlinear_runner_sha256": sha(NONLINEAR),
        "source_paths": SOURCES, "case_spec": tasks, "worker_count": len(rows),
        "source_stable": all(row["source_stable"] for row in rows), "workers": rows}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(OUT.relative_to(ROOT)), "worker_count": len(rows),
                      "source_stable": payload["source_stable"]}))


if __name__ == "__main__":
    main()
