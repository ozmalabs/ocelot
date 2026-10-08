#!/usr/bin/env python3
"""Fresh-process population sweep for ProblemShape induction economics."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python"), str(ROOT / "scripts")]
from substrate_problem_shape_induction_economics import observe_measure, pump, sha, rss_bytes  # noqa: E402

PREREG = ROOT / "docs/research/engine_substrate/SUBSTRATE_PROBLEM_SHAPE_POPULATION_SCALE_PREREG_20260925.md"
LOCK = ROOT / "evaluation/substrate_capability/problem_shape_population_scale_lock_20260925.json"
SIZES = [2, 4, 8]
MIXES = ["recognition", "recurrent_residual"]
CODEBOOK_MODES = ["dynamic", "frozen"]
STATEMENTS = ["if X is a fish, X can swim", "if X is a bird, X can fly",
              "if X is a dog, X can bark", "if X is a bee, X can pollinate"]


def worker(size: int, mix: str, codebook_mode: str, seed_dir: str | None = None) -> dict:
    from substrate.world_adapter import WorldAdapter
    from substrate.boot_all import load_all_seeds
    from substrate_rs import _native
    from domains import solver_dispatch as sd
    from domains import problem_decomposition as pdec
    from worlds import bigville_can_beliefs as bcb

    boot_wall0, boot_cpu0 = time.perf_counter_ns(), time.process_time_ns()
    agent = WorldAdapter(seeds=())
    load_report = load_all_seeds(agent, seed_dir=seed_dir)
    seed_rule_rows = sorted((row for row in agent.inner.rule_access_sets() if row[2]), key=lambda row: int(row[0]))
    seed_rule_names = [str(row[1]) for row in seed_rule_rows]
    seed_rule_order_sha256 = hashlib.sha256(json.dumps(seed_rule_names, separators=(",", ":")).encode()).hexdigest()
    seed_ps_positions = {str(row[1]): int(row[0]) for row in seed_rule_rows if row[1] in {"ps_decode", "ps_recognize", "ps_residual", "ps_mint", "ps_redecode"}}
    agent.register_reflex_response("question_pursue", lambda ag: ag._question_pursue_advance())
    agent.wire_question_faculty(dict(sd.SOLVE_RESOLVER_FUNCTIONS))
    boot_wall_ns, boot_cpu_ns = time.perf_counter_ns() - boot_wall0, time.process_time_ns() - boot_cpu0
    s, native, Native = agent.s, agent.inner, _native.Substrate

    access_rows = native.rule_access_sets()
    mint_rule_ids = [int(row[0]) for row in access_rows if row[1] == "ps_mint" and row[2]]
    removed = False
    if codebook_mode == "frozen":
        if len(mint_rule_ids) != 1:
            raise RuntimeError(f"expected one live ps_mint rule, found {mint_rule_ids}")
        removed = bool(native.remove_rule(mint_rule_ids[0]))
        if not removed:
            raise RuntimeError("native remove_rule did not tombstone ps_mint")

    # Keep a common substrate baseline across task mixes: three real solved
    # deduction schemas are always present, but only the recurrence mix uses
    # them to create decomposition candidates.
    scaffolding = []
    for statement in STATEMENTS[:3]:
        goal = sd.mint_solve_deduction_goal(agent, statement)
        resolution = pump(agent, goal)
        if resolution["status"] != "resolved":
            raise RuntimeError(f"scaffold goal failed: {resolution}")
        scaffolding.append(goal)

    pre_observe_rows = sorted((row for row in native.rule_access_sets() if row[2]), key=lambda row: int(row[0]))
    pre_observe_names = [str(row[1]) for row in pre_observe_rows]
    pre_observe_rule_order_sha256 = hashlib.sha256(json.dumps(pre_observe_names, separators=(",", ":")).encode()).hexdigest()
    pre_observe_ps_positions = {str(row[1]): int(row[0]) for row in pre_observe_rows if row[1] in {"ps_decode", "ps_recognize", "ps_residual", "ps_mint", "ps_redecode"}}
    Native.scale_audit_set_enabled(True)
    Native.scale_audit_set_per_rule_enabled(True)
    records: list[dict] = []
    resolution_records: list[dict] = []

    def process_goal(goal, label: str) -> None:
        resolution_records.append({"label": label, **pump(agent, goal)})
        records.append(observe_measure(agent, goal, label, Native))

    if mix == "recognition":
        bcb.install_productions(native)
        residents = json.loads((ROOT / "seeds/bigville_cast100.json").read_text())["residents"]
        for i in range(size):
            if i % 2 == 0:
                statement = STATEMENTS[(i // 2) % len(STATEMENTS)]
                process_goal(sd.mint_solve_deduction_goal(agent, statement), f"deduction_{i + 1}")
            else:
                built = bcb.build_resident_can_mt(native, residents[i])
                bcb.apply_scenario_evidence(native, built["concepts"])
                native.set_attr(built["mt_node"], "discrete_mode", "3state")
                native.set_attr(built["mt_node"], "can_tick", 0)
                process_goal(sd.mint_solve_can_exact_goal(agent, built["mt_node"]), f"can_exact_{i + 1}")
    elif mix == "recurrent_residual":
        schemas = [sd._solve_caps(agent)[g]["result"]["node"] for g in scaffolding]
        shared = pdec.project_deduction_shared_attr(s, schemas)
        complete = pdec.project_deduction_complete(s, schemas)
        for i in range(size):
            if i == 0:
                candidates, bound = [shared, complete], 1
            elif i == 1:
                candidates, bound = [complete], 0
            else:
                candidates, bound = [shared], 5 + i
            goal = sd.mint_solve_decompose_goal(agent, candidates, bound=bound)
            process_goal(goal, f"decompose_{i + 1}")
    else:
        raise ValueError(f"unsupported mix: {mix}")

    for row in records:
        oid = row["observation_id"]
        attrs = s.node(_native.NodeID(oid))["attrs"]
        row["observation_status_final"] = attrs.get("status")
        row["covered_by_final"] = attrs.get("covered_by")

    Native.scale_audit_set_enabled(False)
    Native.scale_audit_set_per_rule_enabled(False)
    mints = sum(row["mint_count_delta"] for row in records)
    if mix == "recognition":
        expected_initial = ["recognized"] * size
        expected_final = ["recognized"] * size
        expected_mints = 0
    elif codebook_mode == "dynamic":
        expected_initial = ["residual"] + ["recognized"] * (size - 1)
        expected_final = ["recognized"] * size
        expected_mints = 1
    else:
        expected_initial = ["residual"] * size
        expected_final = ["residual"] * size
        expected_mints = 0
    initial_match = [r["observation_status_initial"] for r in records] == expected_initial
    final_match = [r["observation_status_final"] for r in records] == expected_final
    all_fixed = all(r["post_observe_settle_report"]["status"] == "fixed_point" for r in records)
    codebook_shape_count = len(s.nodes("ProblemShape"))
    ps_candidates = sum(r["problem_shape_candidate_pairs"] for r in records)
    ps_terms = sum(r["problem_shape_term_evaluations"] for r in records)
    active_rule_rows = sorted((row for row in native.rule_access_sets() if row[2]), key=lambda row: int(row[0]))
    active_rule_order = [str(row[1]) for row in active_rule_rows]
    active_rule_order_sha256 = hashlib.sha256(json.dumps(active_rule_order, separators=(",", ":")).encode()).hexdigest()
    active_rule_positions = {str(row[1]): int(row[0]) for row in active_rule_rows
                             if row[1] in {"ps_decode", "ps_recognize", "ps_residual", "ps_mint", "ps_redecode"}}
    final_rule_order_sha256 = active_rule_order_sha256
    return {
        "seed_rule_order_sha256": seed_rule_order_sha256,
        "seed_rule_names": seed_rule_names,
        "seed_problem_shape_rule_positions": seed_ps_positions,
        "pre_observation_rule_names": pre_observe_names,
        "pre_observation_rule_order_sha256": pre_observe_rule_order_sha256,
        "pre_observation_problem_shape_rule_positions": pre_observe_ps_positions,
        "final_rule_order_sha256": final_rule_order_sha256,
        "seed_load_order": load_report.get("order", []),
        "seed_load_failed_ids": [str(row) for row in load_report.get("failed", [])],
        "seed_load_failure_count": len(load_report.get("failed", [])),
        "active_problem_shape_rule_positions": active_rule_positions,
        "active_rule_order_sha256": active_rule_order_sha256,
        "worker_id": f"N{size}-{mix}-{codebook_mode}", "population_size": size,
        "process_id": os.getpid(),
        "task_mix": mix, "codebook_mode": codebook_mode,
        "frozen_mint_rule_removed": removed, "mint_rule_ids": mint_rule_ids,
        "full_seed_boot_wall_ns": boot_wall_ns, "full_seed_boot_cpu_ns": boot_cpu_ns,
        "peak_rss_bytes": rss_bytes(), "scaffolding_goal_count": len(scaffolding),
        "goal_resolution_costs": resolution_records, "records": records,
        "final_codebook_shape_count": codebook_shape_count,
        "total_mints": mints,
        "problem_shape_candidate_pairs_total": ps_candidates,
        "problem_shape_term_evaluations_total": ps_terms,
        "cumulative_candidate_work_by_prefix": [sum(r["problem_shape_candidate_pairs"] for r in records[:i])
                                                   for i in range(1, len(records) + 1)],
        "checks": {"expected_initial_statuses": initial_match, "expected_final_statuses": final_match,
                   "expected_mint_count": mints == expected_mints,
                   "all_runs_report_fixed_point": all_fixed,
                   "frozen_condition_actually_disabled_mint": (removed if codebook_mode == "frozen" else not removed)},
        "all_checks_pass": initial_match and final_match and mints == expected_mints and all_fixed and
                           (removed if codebook_mode == "frozen" else not removed),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", type=Path)
    ap.add_argument("--worker-size", type=int, choices=SIZES, help=argparse.SUPPRESS)
    ap.add_argument("--worker-mix", choices=MIXES, help=argparse.SUPPRESS)
    ap.add_argument("--worker-codebook", choices=CODEBOOK_MODES, help=argparse.SUPPRESS)
    args = ap.parse_args()
    if args.worker_size is not None:
        if not args.worker_mix or not args.worker_codebook:
            ap.error("worker mode needs --worker-mix and --worker-codebook")
        record = worker(args.worker_size, args.worker_mix, args.worker_codebook)
        print(json.dumps(record, sort_keys=True))
        return 0 if record["all_checks_pass"] else 2
    if args.output is None:
        ap.error("--output is required in aggregate mode")

    env = {**os.environ, "PYTHONPATH": f"{ROOT}:{ROOT / 'runners/dsl/python'}:{ROOT / 'scripts'}"}
    stale = subprocess.check_output(
        [sys.executable, "-c", "from domains.engine_provenance import build_is_stale; print('\\n'.join(build_is_stale('.')))"],
        cwd=ROOT, env=env, text=True).strip()
    if stale:
        raise SystemExit(f"native build is stale:\n{stale}")
    lock = json.loads(LOCK.read_text())
    locked = {
        "preregistration_sha256": sha(PREREG),
        "runner_sha256": sha(Path(__file__)),
        "native_sha256": sha(ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so"),
        "seed_hashes": {p.name: sha(p) for p in [ROOT / "seeds/problem_shape_growth.json",
                                                   ROOT / "seeds/shape_decode_loop.json",
                                                   ROOT / "seeds/bigville_cast100.json"]},
        "configuration": {"sizes": SIZES, "mixes": MIXES, "codebook_modes": CODEBOOK_MODES,
                           "fresh_process_per_cell": True},
    }
    if any(lock.get(k) != v for k, v in locked.items()):
        raise SystemExit("preregistered source/config/native lock mismatch")

    records = []
    started = time.time_ns()
    for size in SIZES:
        for mix in MIXES:
            for mode in CODEBOOK_MODES:
                proc = subprocess.run(
                    [sys.executable, str(Path(__file__).resolve()), "--worker-size", str(size),
                     "--worker-mix", mix, "--worker-codebook", mode],
                    cwd=ROOT, env=env, text=True, capture_output=True, timeout=120)
                if proc.returncode:
                    raise RuntimeError(f"worker failed {size}/{mix}/{mode}:\n{proc.stdout}\n{proc.stderr}")
                record = json.loads(proc.stdout)
                if not record["all_checks_pass"]:
                    raise RuntimeError(f"worker acceptance failure: {record['worker_id']}")
                record["worker_stderr"] = proc.stderr
                records.append(record)
                print(json.dumps({"completed": record["worker_id"], "checks": record["checks"]}), flush=True)
    unique_worker_processes = len({r["process_id"] for r in records}) == len(records)
    if not unique_worker_processes:
        raise RuntimeError("worker process IDs are not unique; separate-process gate failed")
    result = {
        "schema_version": 1, "run_id": f"problem-shape-pop-scale-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}",
        "preregistration": {"path": str(PREREG.relative_to(ROOT)), "sha256": sha(PREREG)},
        "lock": {"path": str(LOCK.relative_to(ROOT)), "sha256": sha(LOCK)},
        "source_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "dirty_tree": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()),
        "runner_sha256": sha(Path(__file__)),
        "native_sha256": sha(ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so"),
        "build_record_sha256": sha(ROOT / "runners/dsl/python/substrate_rs/_native.build.json"),
        "seed_hashes": {p.name: sha(p) for p in [ROOT / "seeds/problem_shape_growth.json",
                                                   ROOT / "seeds/shape_decode_loop.json",
                                                   ROOT / "seeds/bigville_cast100.json"]},
        "environment": {"python": sys.version, "platform": platform.platform(), "logical_cpu_count": os.cpu_count()},
        "configuration": {"sizes": SIZES, "mixes": MIXES, "codebook_modes": CODEBOOK_MODES,
                           "worker_count": len(records), "fresh_process_per_cell": True},
        "started_unix_ns": started, "finished_unix_ns": time.time_ns(),
        "records": records, "unique_worker_processes": unique_worker_processes,
        "all_checks_pass": all(r["all_checks_pass"] for r in records) and unique_worker_processes,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"all_checks_pass": result["all_checks_pass"], "workers": len(records)}, sort_keys=True))
    return 0 if result["all_checks_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
