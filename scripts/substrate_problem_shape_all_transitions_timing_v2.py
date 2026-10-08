#!/usr/bin/env python3
"""Twelve balanced fresh-process pairs for ProblemShape eventization timing."""
from __future__ import annotations

import hashlib
import json
import math
import os
import platform
import random
import statistics
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREREG = ROOT / "docs/research/engine_substrate/SUBSTRATE_PROBLEM_SHAPE_ALL_TRANSITIONS_TIMING_V2_PREREG_20260925.md"
AMENDMENT = ROOT / "docs/research/engine_substrate/SUBSTRATE_PROBLEM_SHAPE_ALL_TRANSITIONS_TIMING_V2_1_AMENDMENT_20260925.md"
LOCK = ROOT / "evaluation/substrate_capability/problem_shape_all_transitions_timing_v2_lock_20260925.json"
BASE_RUNNER = ROOT / "scripts/substrate_problem_shape_population_scale.py"
CAND_RUNNER = ROOT / "scripts/substrate_problem_shape_all_transitions.py"
PAIR_RUNNER_V1 = ROOT / "scripts/substrate_problem_shape_all_transitions_paired_timing.py"
PAIR_ANALYZER_V1 = ROOT / "scripts/analyze_substrate_problem_shape_all_transitions_paired_timing_v1_1.py"
BASE_RAW = ROOT / "evaluation/reports/substrate_problem_shape_population_scale_20260925.json"
SEEDS = [ROOT / "seeds/problem_shape_growth.json", ROOT / "seeds/shape_decode_loop.json",
         ROOT / "seeds/bigville_cast100.json"]
OUT = ROOT / "evaluation/reports/substrate_problem_shape_all_transitions_timing_v2_20260925.json"
PARTIAL = ROOT / "evaluation/reports/substrate_problem_shape_all_transitions_timing_v2_partial_20260925.json"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def locked_inputs():
    return {
        "preregistration_sha256": PREREG,
        "execution_amendment_sha256": AMENDMENT,
        "runner_sha256": Path(__file__).resolve(),
        "baseline_runner_sha256": BASE_RUNNER,
        "candidate_runner_sha256": CAND_RUNNER,
        "prior_pair_runner_sha256": PAIR_RUNNER_V1,
        "prior_pair_analyzer_sha256": PAIR_ANALYZER_V1,
        "baseline_raw_sha256": BASE_RAW,
        "problem_shape_source_sha256": ROOT / "domains/problem_shape.py",
        "solver_dispatch_source_sha256": ROOT / "domains/solver_dispatch.py",
        "decomposition_source_sha256": ROOT / "domains/problem_decomposition.py",
        "bigville_source_sha256": ROOT / "worlds/bigville_can_beliefs.py",
        "problem_shape_seed_sha256": SEEDS[0],
        "shape_decode_seed_sha256": SEEDS[1],
        "cast_seed_sha256": SEEDS[2],
        "native_sha256": ROOT / "runners/dsl/python/substrate_rs/_native.abi3.so",
        "build_manifest_sha256": ROOT / "runners/dsl/python/substrate_rs/_native.build.json",
        "cargo_lock_sha256": ROOT / "runners/dsl/Cargo.lock",
    }


def worker_summary(arm: str, raw: dict) -> dict:
    if not raw.get("all_checks_pass"):
        raise RuntimeError(f"{arm} worker failed semantic gate: {raw.get('checks')}")
    rows = raw["records"]
    if arm == "baseline":
        wall = [int(r["wall_time_ns"]) for r in rows]
        cpu = [int(r["cpu_time_ns"]) for r in rows]
        metric = "full_closure_observe"
    else:
        wall = [int(r["treatment_observation_wall_ns"]) for r in rows]
        cpu = [int(r["treatment_observation_cpu_ns"]) for r in rows]
        metric = "eventized_observe_including_host_index_event_maintenance"
    return {
        "arm": arm, "process_id": raw["process_id"],
        "all_checks_pass": raw["all_checks_pass"],
        "boot_wall_ns": int(raw.get("full_seed_boot_wall_ns", 0)),
        "boot_cpu_ns": int(raw.get("full_seed_boot_cpu_ns", 0)),
        "peak_rss_bytes": int(raw.get("peak_rss_bytes", raw.get("process_peak_rss_bytes", 0))),
        "observation_metric": metric,
        "observation_wall_ns_total": sum(wall),
        "observation_cpu_ns_total": sum(cpu),
        "observation_wall_ns_by_step": wall,
        "observation_cpu_ns_by_step": cpu,
        "task_status_initial": [r.get("observation_status_initial") for r in rows],
        "task_status_final": [r.get("observation_status_final") for r in rows],
        "mints_by_step": [int(r.get("mint_count_delta", 0)) for r in rows],
        "problem_shape_candidate_pairs_total": int(raw.get("problem_shape_candidate_pairs_total", 0)),
        "problem_shape_term_evaluations_total": int(raw.get("problem_shape_term_evaluations_total", 0)),
        "ps_mint_candidate_pairs_total": int(raw.get("ps_mint_candidate_pairs_total", 0)),
        "ps_mint_term_evaluations_total": int(raw.get("ps_mint_term_evaluations_total", 0)),
        "host_index_maintenance_ns_total": int(raw.get("host_index_maintenance_ns_total", 0)),
        "variant": raw.get("variant", raw.get("codebook_mode")),
    }


def percentile(values, frac):
    vals = sorted(values)
    return vals[min(len(vals) - 1, int(frac * len(vals)))]


def main() -> int:
    if len(sys.argv) != 1:
        raise SystemExit("usage: python3 scripts/substrate_problem_shape_all_transitions_timing_v2.py")
    frozen = json.loads(LOCK.read_text())
    inputs = locked_inputs()
    actual_hashes = {key: sha(path) for key, path in inputs.items()}
    if frozen != actual_hashes:
        raise SystemExit("ProblemShape timing v2 lock mismatch")
    env = {**os.environ, "PYTHONPATH": f"{ROOT}:{ROOT / 'runners/dsl/python'}:{ROOT / 'scripts'}"}
    stale = subprocess.check_output(
        [sys.executable, "-c", "from domains.engine_provenance import build_is_stale; print('\\n'.join(build_is_stale('.')) )"],
        cwd=ROOT, env=env, text=True).strip()
    if stale:
        raise SystemExit(f"native build stale:\n{stale}")

    rng = random.Random(20260925)
    if PARTIAL.exists():
        raise SystemExit(f"refusing to overwrite prior checkpoint: {PARTIAL}")
    orders = [["baseline", "candidate"] for _ in range(6)] + [["candidate", "baseline"] for _ in range(6)]
    rng.shuffle(orders)
    pairs = []
    processes = []
    for pair_index, order in enumerate(orders, start=1):
        arms = {}
        for arm in order:
            if arm == "baseline":
                cmd = [sys.executable, str(BASE_RUNNER), "--worker-size", "8",
                       "--worker-mix", "recurrent_residual", "--worker-codebook", "dynamic"]
            else:
                cmd = [sys.executable, str(CAND_RUNNER), "--worker-size", "8",
                       "--worker-mix", "recurrent_residual"]
            proc = subprocess.run(cmd, cwd=ROOT, env=env, text=True, capture_output=True,
                                  timeout=240)
            if proc.returncode:
                raise RuntimeError(f"pair {pair_index} {arm} worker failed: {proc.stdout[-2000:]} {proc.stderr[-2000:]}")
            record = json.loads(proc.stdout.strip().splitlines()[-1])
            summary = worker_summary(arm, record)
            if summary["process_id"] in processes:
                raise RuntimeError("duplicate worker PID; expected a new process for every arm")
            processes.append(summary["process_id"])
            arms[arm] = summary
        base = arms["baseline"]; cand = arms["candidate"]
        pairs.append({
            "pair": pair_index, "execution_order": order, "arms": arms,
            "complete": True,
            "semantic_parity": base["task_status_initial"] == cand["task_status_initial"]
                and base["task_status_final"] == cand["task_status_final"]
                and base["mints_by_step"] == cand["mints_by_step"]
                and base["all_checks_pass"] and cand["all_checks_pass"],
            "wall_ratio_candidate_over_baseline": cand["observation_wall_ns_total"] / base["observation_wall_ns_total"],
            "cpu_ratio_candidate_over_baseline": cand["observation_cpu_ns_total"] / base["observation_cpu_ns_total"],
            "wall_delta_ns_candidate_minus_baseline": cand["observation_wall_ns_total"] - base["observation_wall_ns_total"],
            "cpu_delta_ns_candidate_minus_baseline": cand["observation_cpu_ns_total"] - base["observation_cpu_ns_total"],
        })
        print(json.dumps({"pair": pair_index, "order": order,
                          "semantic_parity": pairs[-1]["semantic_parity"],
                          "wall_ratio": pairs[-1]["wall_ratio_candidate_over_baseline"]}), flush=True)
        checkpoint = {
            "schema_version": 1, "run_id": "problem-shape-all-transitions-timing-v2-checkpoint",
            "completed_pairs": pairs,
            "unique_process_ids_so_far": len(processes) == len(set(processes)),
            "locked_inputs": actual_hashes,
            "lock_sha256": sha(LOCK),
        }
        partial_tmp = PARTIAL.with_suffix(".tmp")
        partial_tmp.write_text(json.dumps(checkpoint, indent=2, sort_keys=True) + "\n")
        partial_tmp.replace(PARTIAL)

    ratios = [p["wall_ratio_candidate_over_baseline"] for p in pairs]
    deltas = [p["wall_delta_ns_candidate_minus_baseline"] for p in pairs]
    bootstrapped = []
    for _ in range(20000):
        sample = [rng.choice(pairs) for _ in pairs]
        bootstrapped.append(statistics.median(x["wall_ratio_candidate_over_baseline"] for x in sample))
    bootstrapped.sort()
    result = {
        "schema_version": 1,
        "run_id": "problem-shape-all-transitions-timing-v2-20260925",
        "run_state": "locked_exploratory_repeated_paired_timing",
        "design": {"pairs": len(pairs), "workers": len(processes), "N": 8,
                   "mix": "recurrent_residual", "codebook_mode": "dynamic",
                   "order_counts": {"baseline_first": sum(p["execution_order"][0] == "baseline" for p in pairs),
                                    "candidate_first": sum(p["execution_order"][0] == "candidate" for p in pairs)},
                   "rng_seed": 20260925},
        "summary": {
            "all_pairs_semantically_valid": all(p["semantic_parity"] for p in pairs),
            "unique_process_ids": len(processes) == len(set(processes)) == 24,
            "candidate_faster_pair_count": sum(r < 1 for r in ratios),
            "candidate_wall_ratio_median": statistics.median(ratios),
            "candidate_wall_ratio_mean": statistics.mean(ratios),
            "candidate_wall_ratio_range": [min(ratios), max(ratios)],
            "median_wall_ratio_pair_bootstrap_95": [percentile(bootstrapped, .025), percentile(bootstrapped, .975)],
            "median_wall_delta_ns": statistics.median(deltas),
            "candidate_cpu_ratio_median": statistics.median(p["cpu_ratio_candidate_over_baseline"] for p in pairs),
        },
        "pairs": pairs,
        "provenance": {
            "locked_inputs": actual_hashes, "lock_sha256": sha(LOCK),
            "native_sha256": sha(inputs["native_sha256"]),
            "build_manifest_sha256": sha(inputs["build_manifest_sha256"]),
            "python": sys.version, "platform": platform.platform(),
            "logical_cpu_count": os.cpu_count(),
            "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "dirty_worktree": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()),
        },
        "interpretation_limit": "12 fresh-process pairs on one N=8 authored recurrent-residual workload; exploratory timing only, not a scaling or substrate-wide performance claim",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    PARTIAL.unlink(missing_ok=True)
    passed = result["summary"]["all_pairs_semantically_valid"] and result["summary"]["unique_process_ids"] and result["design"]["order_counts"] == {"baseline_first": 6, "candidate_first": 6}
    print(json.dumps({"all_gates_pass": passed, "output": str(OUT), "summary": result["summary"]}, sort_keys=True))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
