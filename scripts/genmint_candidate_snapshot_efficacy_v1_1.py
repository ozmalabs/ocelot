#!/usr/bin/env python3
"""Compare an isolated GenMint candidate snapshot with frozen controls."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import random
import resource
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python"), str(ROOT / "scripts")]
from domains.engine_provenance import engine_preamble, provenance_line, rust_source_fingerprint
engine_preamble()
from substrate.boot_core import boot_core
from domains import reflective_faculty as rf
from substrate_rs import _native
import genmint_matrix_family_reuse_probe_v3 as fixtures
import genmint_process_restart_reuse_v1 as reuse

LOCK = ROOT / "evaluation/substrate_capability/genmint_candidate_snapshot_efficacy_v1_1_lock_20261001.json"
OUT = ROOT / "evaluation/reports/genmint_candidate_snapshot_efficacy_v1_1_20261001.json"
MATRICES = ("prior_matrix", "shearA", "shearB")
LAYOUTS = ("adjacent_01", "opposite_03")
REPS = 5
SEED = 20260930
NEGATIVE_POINTS = (
    ((0, 0), (1, 2), (3, 1), (2, 5)),
    ((1, 4), (4, 0), (6, 3), (2, 7)),
    ((3, 2), (7, 1), (0, 6), (5, 4)),
    ((2, 1), (5, 7), (1, 3), (7, 4)),
    ((6, 0), (2, 4), (7, 5), (1, 1)),
    ((4, 6), (0, 2), (3, 7), (6, 5)),
    ((5, 3), (1, 6), (4, 1), (0, 7)),
    ((7, 2), (3, 5), (6, 1), (2, 0)),
)
SOURCES = (
    "scripts/genmint_candidate_snapshot_efficacy_v1_1.py",
    "scripts/analyze_genmint_candidate_snapshot_efficacy_v1_1.py",
    "scripts/genmint_process_restart_reuse_v1.py",
    "scripts/genmint_matrix_family_reuse_probe_v3.py",
    "docs/research/engine_substrate/SUBSTRATE_OFFLINE_CANDIDATE_SNAPSHOT_EFFICACY_V1_1_PREREG_20261001.md",
    "seeds/shape_decode_loop.json",
    "domains/reflective_faculty.py",
    "domains/engine_provenance.py",
    "substrate/boot_core.py",
    "runners/dsl/src/shape_decode.rs",
    "runners/dsl/src/term.rs",
    "runners/dsl/src/py.rs",
    "runners/dsl/src/substrate.rs",
    "runners/dsl/src/graph.rs",
    "runners/dsl/src/persist.rs",
    "runners/dsl/python/substrate_rs/__init__.py",
    "runners/dsl/python/substrate_rs/_native.build.json",
)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def state_digest(substrate) -> str:
    native = rf._native_eval2(substrate)
    grammar = native.grammar_to_json()
    if isinstance(grammar, str):
        grammar = json.loads(grammar)
    state = {
        "graph": native.graph_to_dict(),
        "grammar": grammar,
        "rules": native.export_rules(),
    }
    return hashlib.sha256(json.dumps(state, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


def lock_payload() -> dict:
    native_path = Path(_native.__file__).resolve()
    return {
        "schema_version": 1,
        "source_sha256": {name: sha(ROOT / name) for name in SOURCES},
        "native_path": str(native_path),
        "native_sha256": sha(native_path),
        "native_build_manifest_sha256": sha(ROOT / "runners/dsl/python/substrate_rs/_native.build.json"),
        "rust_source_fingerprint": rust_source_fingerprint(str(ROOT)),
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "design": {
            "matrices": MATRICES,
            "layouts": LAYOUTS,
            "repetitions": REPS,
            "heldout_count": len(fixtures.HELDOUT),
            "negative_points": NEGATIVE_POINTS,
            "schedule_seed": SEED,
            "arms": ["candidate_shared_pages", "candidate_reusable_snapshot", "candidate_eager_oracle", "frozen", "exposure_without_consolidation"],
        },
    }


def row_data(matrix_name: str, layout_name: str):
    matrix = fixtures.MAPS[matrix_name]
    p0 = set(fixtures.LAYOUTS[layout_name])
    base, target = [], []
    for i, (r, c) in enumerate(fixtures.POINTS):
        b, y = fixtures.make_row("p0" if i in p0 else "p1", r, c, matrix)
        base.append(b)
        target.append(y)
    return matrix, sorted(p0), base, target


def acquire_training(substrate, agent, enabled: bool, matrix_name: str, layout_name: str, rep: int, arm: str):
    native = rf._native_eval2(substrate)
    if enabled:
        substrate.set_attr(agent, "gen_infer_enabled", 1.0)
    else:
        substrate.set_attr(agent, "gen_infer_enabled", 0.0)
    matrix, p0, base, target = row_data(matrix_name, layout_name)
    substrate.add_node("ShapeSignature", {
        "name": f"candidate_train_{matrix_name}_{layout_name}",
        "signature": json.dumps(base), "kind": "faculty",
        "faculty": f"candidate_train_{matrix_name}_{layout_name}", "dim_types": fixtures.DT,
    })
    epoch = substrate.node(agent)["attrs"].get("codebook_epoch") or 0.0
    obs = substrate.add_node("Observation", {
        "signature": target,
        "key": ["candidate_snapshot_v1", matrix_name, layout_name, str(rep), arm, "train"],
        "status": "decoded", "residual": target, "decoded_epoch": epoch,
        "dim_types": fixtures.DT,
    })
    substrate.add_edge(agent, "observed", obs)
    before = fixtures.linear_gens(substrate)
    started = time.perf_counter()
    native.run_rules()
    elapsed = time.perf_counter() - started
    after = fixtures.linear_gens(substrate)
    attrs = substrate.node(obs)["attrs"]
    acquired = [g for g in after if g["matrix"] == matrix and g["name"] not in {x["name"] for x in before}]
    return {
        "matrix": matrix, "p0_indices": p0, "base": base, "target": target,
        "status": attrs.get("status"), "residual": attrs.get("residual"),
        "transforms": fixtures.transform_records(substrate, obs),
        "generators_before": before, "generators_after": after,
        "acquired_expected_generator": acquired[0] if len(acquired) == 1 else None,
        "closure_wall_s": elapsed,
    }


def predict_linear(base: list[list], generator: dict, transforms: list[dict]) -> list[list]:
    a, b, c, d = generator["matrix"]
    min_r = min(row[1] for row in base)
    min_c = min(row[2] for row in base)
    predicted = [[row[0], a * (row[1] - min_r) + b * (row[2] - min_c),
                  c * (row[1] - min_r) + d * (row[2] - min_c), row[3]] for row in base]
    residuals = (transforms[0].get("transforms") if transforms else []) or []
    for residual in residuals:
        for row in predicted:
            if residual.get("pred") is not None and residual["pred"] != row[0]:
                continue
            dim = residual.get("dim")
            if residual.get("kind") == "shift" and dim in (1, 2):
                row[dim] += residual.get("delta", 0)
            elif residual.get("kind") == "subst" and row[3] == residual.get("from"):
                row[3] = residual.get("to")
    return predicted


def negative_tasks(substrate, agent, native, matrix_name: str, layout_name: str, rep: int, arm: str):
    rows = []
    existing = fixtures.linear_gens(substrate)
    closure_wall = closure_cpu = 0.0
    for ti, coords in enumerate(NEGATIVE_POINTS):
        base = [[f"neg{ti}_{j}", r, c, "red"] for j, (r, c) in enumerate(coords)]
        target = [[row[0], row[1] * row[1] + row[2], row[1] - row[2] * row[2], row[3]] for row in base]
        name = f"negative_{ti}_{matrix_name}_{layout_name}"
        substrate.add_node("ShapeSignature", {
            "name": name, "signature": json.dumps(base), "kind": "faculty",
            "faculty": name, "dim_types": fixtures.DT,
        })
        epoch = substrate.node(agent)["attrs"].get("codebook_epoch") or 0.0
        obs = substrate.add_node("Observation", {
            "signature": target,
            "key": ["candidate_snapshot_v1", matrix_name, layout_name, str(rep), arm, "negative", str(ti)],
            "status": "decoded", "residual": target, "decoded_epoch": epoch,
            "dim_types": fixtures.DT,
        })
        substrate.add_edge(agent, "observed", obs)
        axes_before = {str(n) for n in substrate.nodes("CapabilityAxis")}
        wall_start, cpu_start = time.perf_counter(), time.process_time()
        native.run_rules()
        closure_wall += time.perf_counter() - wall_start
        closure_cpu += time.process_time() - cpu_start
        attrs = substrate.node(obs)["attrs"]
        transforms = fixtures.transform_records(substrate, obs)
        selected = next((t.get("generator") for t in transforms if t.get("generator")), None)
        generator = next((g for g in fixtures.linear_gens(substrate) if g["name"] == selected), None)
        independent = predict_linear(base, generator, transforms) if generator else []
        accepted = attrs.get("status") in {"transformed", "recognized_transformed", "covered", "accepted"}
        minted_axes = sorted(str(n) for n in substrate.nodes("CapabilityAxis") if str(n) not in axes_before)
        rows.append({
            "task_index": ti, "base": base, "target": target,
            "status": attrs.get("status"), "residual": attrs.get("residual"),
            "transforms": transforms, "selected_generator": selected,
            "independent_predictions": independent,
            "accepted": accepted,
            "independent_exact_target_match": bool(generator and independent == target),
            "false_accept": bool(accepted and (not generator or independent != target)),
            "minted_axes": minted_axes,
            "novelty_status_unadjudicated": attrs.get("status") == "minted" and selected is None,
        })
    final_gens = fixtures.linear_gens(substrate)
    return (rows, [g for g in final_gens if g["name"] not in {x["name"] for x in existing}],
            closure_wall, closure_cpu)


def evaluate_branch(source, backend: str, agent_id: int, matrix_name: str, layout_name: str,
                    rep: int, expected_gen: dict | None, reusable_snapshot=None):
    evaluation_started = time.perf_counter()
    evaluation_cpu_started = time.process_time()
    source_digest_before = state_digest(source)
    fork_started = time.perf_counter()
    branch = (reusable_snapshot.fork() if backend == "reusable_snapshot" else
              source.fork_shared_graph_pages_experiment() if backend == "shared_graph_pages" else
              source.fork_full_copy_experiment())
    fork_s = time.perf_counter() - fork_started
    native = rf._native_eval2(branch)
    agent = agent_id
    branch.set_attr(agent, "gen_infer_enabled", 0.0)
    results, positive_wall, positive_cpu = reuse.apply(
        branch, agent, native, matrix_name, layout_name, rep, False, expected_gen,
    )
    negatives, new_gens, negative_wall, negative_cpu = negative_tasks(
        branch, agent, native, matrix_name, layout_name, rep, "candidate_validation")
    return {
        "backend": backend,
        "fork_wall_s": fork_s,
        "positive_closure_wall_s": positive_wall,
        "positive_closure_cpu_s": positive_cpu,
        "negative_closure_wall_s": negative_wall,
        "negative_closure_cpu_s": negative_cpu,
        "branch_evaluation_wall_s": time.perf_counter() - evaluation_started,
        "branch_evaluation_cpu_s": time.process_time() - evaluation_cpu_started,
        "positive": results,
        "negative": negatives,
        "new_generators_during_evaluation": new_gens,
        "final_digest": state_digest(branch),
        "source_digest_before": source_digest_before,
        "source_unchanged": state_digest(source) == source_digest_before,
    }


def worker(matrix_name: str, layout_name: str, rep: int) -> dict:
    start = time.perf_counter()
    cpu = time.process_time()
    baseline, root_agent = boot_core()
    root_native = rf._native_eval2(baseline)
    rf._ensure_shape_decode_loop(baseline, root_native, root_agent)
    root_agent_id = root_agent
    baseline_digest = state_digest(baseline)
    out = {"matrix_name": matrix_name, "layout": layout_name, "replicate": rep,
           "pid": os.getpid(), "baseline_digest": baseline_digest}

    # Candidate training uses shared graph pages; this is a learning workload
    # for CoW semantics, with eager-copy evaluation retained as the oracle.
    t = time.perf_counter()
    candidate = baseline.fork_shared_graph_pages_experiment()
    out["candidate_fork_wall_s"] = time.perf_counter() - t
    candidate_agent = root_agent_id
    candidate_train = acquire_training(candidate, candidate_agent, True, matrix_name, layout_name, rep, "candidate")
    out["candidate_train"] = candidate_train
    candidate_digest = state_digest(candidate)
    out["candidate_snapshot_digest"] = candidate_digest
    reusable = candidate.snapshot()
    out["reusable_snapshot"] = {"id": reusable.id, "backend": reusable.backend, "source_revision": list(reusable.source_revision)}
    out["candidate_acquired"] = candidate_train["acquired_expected_generator"] is not None

    # Frozen control starts from the same pre-training primary revision.
    t = time.perf_counter()
    frozen = baseline.fork_full_copy_experiment()
    out["frozen_fork_wall_s"] = time.perf_counter() - t
    out["frozen"] = evaluate_branch(frozen, "eager", root_agent_id, matrix_name, layout_name, rep, None)

    # Exposure control sees the identical examples with the learner disabled.
    t = time.perf_counter()
    exposure = baseline.fork_full_copy_experiment()
    out["exposure_fork_wall_s"] = time.perf_counter() - t
    exposure_agent = root_agent_id
    out["exposure_train"] = acquire_training(exposure, exposure_agent, False, matrix_name, layout_name, rep, "exposure")
    out["exposure"] = evaluate_branch(exposure, "eager", root_agent_id, matrix_name, layout_name, rep, None)

    # Evaluate two children from the immutable trained candidate snapshot.
    out["candidate_eager"] = evaluate_branch(candidate, "eager", root_agent_id, matrix_name, layout_name, rep,
                                               candidate_train["acquired_expected_generator"])
    out["candidate_shared"] = evaluate_branch(candidate, "shared_graph_pages", root_agent_id, matrix_name, layout_name, rep,
                                                candidate_train["acquired_expected_generator"])
    out["candidate_reusable"] = evaluate_branch(candidate, "reusable_snapshot", root_agent_id, matrix_name, layout_name, rep,
                                                   candidate_train["acquired_expected_generator"], reusable)
    out["isolation"] = {
        "primary_unchanged": state_digest(baseline) == baseline_digest,
        "primary_digest_after": state_digest(baseline),
        "candidate_snapshot_unchanged_after_evaluation": state_digest(candidate) == candidate_digest,
        "candidate_snapshot_digest_after": state_digest(candidate),
        "candidate_branch_isolated_from_primary": candidate_digest != baseline_digest,
        "frozen_source_unchanged": out["frozen"]["source_unchanged"],
        "exposure_source_unchanged": out["exposure"]["source_unchanged"],
        "reusable_source_unchanged": out["candidate_reusable"]["source_unchanged"],
        "reusable_snapshot_contract": reusable.backend == "shared_graph_pages" and tuple(reusable.source_revision) == tuple(candidate.experiment_graph_rule_revision()),
    }
    out["elapsed_wall_s"] = time.perf_counter() - start
    out["elapsed_cpu_s"] = time.process_time() - cpu
    out["peak_rss_kib"] = int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lock", action="store_true")
    args = parser.parse_args()
    lock = json.loads(json.dumps(lock_payload()))
    if args.lock:
        print(json.dumps(lock, indent=2, sort_keys=True))
        return
    if not LOCK.exists() or json.loads(LOCK.read_text()) != lock:
        raise SystemExit("source lock missing or stale; capture --lock output before running")
    env = dict(os.environ)
    env["PYTHONPATH"] = f"{ROOT}:{ROOT / 'runners/dsl/python'}:{ROOT / 'scripts'}:{env.get('PYTHONPATH', '')}"
    stale = subprocess.check_output(
        [sys.executable, "-c", "from domains.engine_provenance import build_is_stale; print('\\n'.join(build_is_stale('.')))"] ,
        cwd=ROOT, env=env, text=True,
    ).strip()
    if stale:
        raise SystemExit("native build stale:\n" + stale)
    cells = [(m, l, rep) for rep in range(1, REPS + 1) for m in MATRICES for l in LAYOUTS]
    rng = random.Random(SEED)
    rng.shuffle(cells)
    schedule = [list(cell) for cell in cells]
    rows = []
    started = time.perf_counter()
    for matrix_name, layout_name, rep in cells:
        try:
            row = worker(matrix_name, layout_name, rep)
            row["worker_error"] = None
        except Exception as exc:  # retain every cell, including implementation errors
            row = {"matrix_name": matrix_name, "layout": layout_name, "replicate": rep,
                   "pid": os.getpid(), "worker_error": f"{type(exc).__name__}: {exc}"}
        rows.append(row)
        print(f"cell={len(rows)}/{len(cells)} {matrix_name}/{layout_name}/r{rep} acquired={row.get('candidate_acquired')} error={row.get('worker_error')}", flush=True)
    raw = {
        "protocol": "SUBSTRATE_OFFLINE_CANDIDATE_SNAPSHOT_EFFICACY_V1_1",
        "locked_inputs": lock,
        "lock_sha256": sha(LOCK),
        "engine": provenance_line(),
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "environment": {"python": sys.version, "platform": platform.platform()},
        "schedule": schedule,
        "workers": rows,
        "worker_count": len(rows),
        "worker_failures": [row for row in rows if row.get("worker_error")],
        "parent_elapsed_s": time.perf_counter() - started,
        "native": {"path": str(Path(_native.__file__).resolve()), "sha256": sha(Path(_native.__file__).resolve())},
        "claim_boundary": "local authored 2-D linear-generator candidate efficacy and reusable shared-graph-page snapshot/fork integration parity on a GenMint candidate-evaluation consumer; not project-held evaluation, formal P3, broad transfer, or vLLM evidence",
    }
    OUT.write_text(json.dumps(raw, indent=2, sort_keys=True, default=str) + "\n")
    print(json.dumps({"output": str(OUT), "workers": len(rows), "failures": len(raw["worker_failures"]),
                      "elapsed_s": raw["parent_elapsed_s"]}, indent=2))


if __name__ == "__main__":
    main()
