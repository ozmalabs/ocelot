#!/usr/bin/env python3
"""Paired full-P4 vs frozen-layer benchmark on a newly frozen string suite."""
from __future__ import annotations

import hashlib
import json
import os
import platform
import random
import resource
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/substrate_string_pbe/tasks.json"
OUT = ROOT / "evaluation/reports/substrate_string_pbe_transfer_pilot_20260926.json"
ARMS = ("main", "frozen", "main_replication")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def percentile(values, q):
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(q * len(ordered)))] if ordered else None


def summarize(rows: list[dict]) -> dict:
    n = len(rows)
    passed = sum(r["outcome"] == "accepted_holdout_ok" for r in rows)
    accepted = sum(r["status"] == "accepted" for r in rows)
    false_accept = sum(r["outcome"] == "accepted_holdout_fail" for r in rows)
    outcomes = Counter(r["outcome"] for r in rows)
    return {
        "n": n, "exact_holdout_pass": passed, "exact_holdout_rate": passed / n if n else None,
        "descriptive_wilson_95_interval": p4.wilson(passed, n)["ci95"] if n else [None, None],
        "accepted": accepted, "accepted_holdout_fail": false_accept,
        "outcome_counts": dict(sorted(outcomes.items())),
        "enumerated": sum(bool(r.get("readback", {}).get("enumerate_outcome")) for r in rows),
        "candidate_count_total": sum(int(((r.get("readback", {}).get("enumerate") or {}).get("tested") or 0)) for r in rows),
        "boot_ms_total": sum(r["boot_ns"] for r in rows) / 1e6,
        "route_ms_total": sum(r["route_ns"] for r in rows) / 1e6,
        "route_ms_median": percentile([r["route_ns"] / 1e6 for r in rows], .5),
        "route_ms_p90": percentile([r["route_ns"] / 1e6 for r in rows], .9),
        "route_ms_max": max((r["route_ns"] for r in rows), default=0) / 1e6,
    }


def run_case(task: dict, arm: str) -> dict:
    boot_start = time.perf_counter_ns()
    sub, agent = p4.boot(frozen=(arm == "frozen"))
    boot_ns = time.perf_counter_ns() - boot_start
    examples = [(row["inputs"], row["expected"]) for row in task["example_rows"]]
    route_start = time.perf_counter_ns()
    result = psy.synthesize_from_request(
        sub, agent, task["request_text"], examples, name=task["id"])
    route_ns = time.perf_counter_ns() - route_start
    # The shared P4 scorer uses the historical `stratum` field name;
    # translate the new fixture's registered `family` field explicitly.
    score_task = {**task, "stratum": task["family"]}
    scored = p4._build_row(sub, score_task, result, arm=arm)
    return {
        **scored, "family": task["family"], "boot_ns": boot_ns, "route_ns": route_ns,
        "readback": {
            "construction": result.get("construction"), "rungs": result.get("rungs"),
            "retrieval": result.get("retrieval"), "exact": result.get("exact"),
            "enumerate": result.get("enumerate"), "enumerate_outcome": result.get("enumerate_outcome"),
            "descend_kind": result.get("descend_kind"), "residual_tokens": result.get("residual_tokens"),
            "gap_reason": result.get("gap_reason"),
        },
    }


def outcome_fingerprint(rows: list[dict]) -> str:
    chosen = [{"task_id": r["task_id"], "outcome": r["outcome"], "status": r["status"],
               "construction": r["construction"], "readback": r["readback"],
               "holdout": r.get("holdout")} for r in rows]
    return hashlib.sha256(json.dumps(chosen, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def stratified_paired_bootstrap(tasks, by_arm, draws=10000):
    """Percentile interval for the paired rate difference, stratified by family."""
    strata = {}
    for task in tasks:
        strata.setdefault(task["family"], []).append(task["id"])
    obs = []
    rng = random.Random(20260925)
    for _ in range(draws):
        successes = 0
        n = 0
        for ids in strata.values():
            sampled = [rng.choice(ids) for _ in ids]
            for task_id in sampled:
                successes += int(by_arm["main"][task_id]["outcome"] == "accepted_holdout_ok")
                successes -= int(by_arm["frozen"][task_id]["outcome"] == "accepted_holdout_ok")
                n += 1
        obs.append(successes / n)
    obs.sort()
    return {"draws": draws, "seed": 20260925, "stratification": "six registered task families",
            "percentile_95_interval": [obs[int(.025 * draws)], obs[min(draws - 1, int(.975 * draws))]]}


def main() -> None:
    global p4, psy
    os.environ.setdefault("OZMA_NO_LLM", "1")
    os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
    sys.path[:0] = [str(ROOT), str(ROOT / "scripts"), str(ROOT / "runners/dsl/python")]
    import prog_synthesis_battery as p4_module
    from domains import prog_synthesis as psy_module
    from substrate_rs import _native
    p4, psy = p4_module, psy_module

    suite = json.loads(FIXTURE.read_text(encoding="utf-8"))
    start = time.perf_counter()
    cpu_before = resource.getrusage(resource.RUSAGE_SELF)
    rows = {arm: [] for arm in ARMS}
    for i, task in enumerate(suite["tasks"]):
        # The paired order is balanced and frozen: odd ids run frozen first.
        order = ("main", "frozen", "main_replication") if i % 2 == 0 else (
            "frozen", "main", "main_replication")
        for arm in order:
            rows[arm].append(run_case(task, arm))

    by_arm = {arm: {r["task_id"]: r for r in items} for arm, items in rows.items()}
    paired = Counter()
    for task in suite["tasks"]:
        main_ok = by_arm["main"][task["id"]]["outcome"] == "accepted_holdout_ok"
        frozen_ok = by_arm["frozen"][task["id"]]["outcome"] == "accepted_holdout_ok"
        paired["both_pass" if main_ok and frozen_ok else "main_only" if main_ok else
               "frozen_only" if frozen_ok else "neither"] += 1
    main_pass = sum(r["outcome"] == "accepted_holdout_ok" for r in rows["main"])
    frozen_pass = sum(r["outcome"] == "accepted_holdout_ok" for r in rows["frozen"])
    paired_difference = {"main_minus_frozen": (main_pass - frozen_pass) / len(suite["tasks"]),
                         "task_count": len(suite["tasks"]),
                         "descriptive_stratified_paired_bootstrap_95": stratified_paired_bootstrap(
                             suite["tasks"], by_arm)}

    main_sig = outcome_fingerprint(rows["main"])
    replay_sig = outcome_fingerprint(rows["main_replication"])
    usage = resource.getrusage(resource.RUSAGE_SELF)
    extension = Path(_native.__file__).resolve()
    source_paths = {
        "harness": Path(__file__).resolve(),
        "task_generator": ROOT / "tests/fixtures/substrate_string_pbe/build_tasks.py",
        "fixture": FIXTURE,
        "preregistration": ROOT / "docs/research/engine_substrate/SUBSTRATE_STRING_PBE_TRANSFER_PILOT_PREREG_20260926.md",
        "benchmark_protocol": ROOT / "docs/research/engine_substrate/SUBSTRATE_BENCHMARK_PROTOCOL.md",
        "p4_runner": ROOT / "scripts/prog_synthesis_battery.py",
        "p4_adapter": ROOT / "domains/prog_synthesis.py",
        "p4_seed": ROOT / "seeds/program_synthesis.json",
        "native_synthesizer": ROOT / "runners/dsl/src/synth_enumerate.rs",
        "native_extension": extension,
        "native_build_manifest": ROOT / "runners/dsl/python/substrate_rs/_native.build.json",
        "cargo_lock": ROOT / "runners/dsl/Cargo.lock",
    }
    category_summary = {}
    for arm in ARMS:
        category_summary[arm] = {
            family: summarize([r for r in rows[arm] if r["family"] == family])
            for family in sorted({t["family"] for t in suite["tasks"]})
        }
    payload = {
        "schema_version": 1,
        "run_id": "substrate-string-pbe-transfer-20260926-v1",
        "run_state": "pilot_new_task_family",
        "protocol_version": "string-pbe-transfer-v1",
        "claim_boundary": "Paired P4 full vs frozen learned-layer arm on one generated 24-task string suite. This does not estimate natural task prevalence, general-domain capability, or unrestricted learning.",
        "design": {"task_count": len(suite["tasks"]), "examples": {"revealed": 4, "held_out": 3},
                   "arms": list(ARMS), "main_replication": "same main condition rerun per task on a fresh substrate",
                   "arm_order": "main/frozen/main_replication on even task ordinals; frozen/main/main_replication on odd"},
        "summary": {"arms": {arm: summarize(items) for arm, items in rows.items()},
                    "paired_main_vs_frozen": dict(sorted(paired.items())),
                    "paired_pass_rate_difference": paired_difference,
                    "main_outcome_fingerprint": main_sig,
                    "main_replication_outcome_fingerprint": replay_sig,
                    "main_replay_exact_match": main_sig == replay_sig,
                    "category_summary": category_summary,
                    "wall_seconds": time.perf_counter() - start,
                    "parent_peak_rss_kib": usage.ru_maxrss,
                    "parent_user_cpu_seconds": usage.ru_utime - cpu_before.ru_utime,
                    "parent_system_cpu_seconds": usage.ru_stime - cpu_before.ru_stime},
        "environment": {"python": sys.version, "platform": platform.platform(),
                        "controls": {k: os.environ.get(k) for k in
                                     ("OZMA_NO_LLM", "OZMA_SEED_PERSIST_DISABLED", "PYTHONHASHSEED")}},
        "provenance": {"commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                       "dirty_worktree": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()),
                       "native_extension_path": str(extension),
                       "sha256": {name: sha(path) for name, path in source_paths.items()},
                       "command": "PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 python3 scripts/substrate_string_pbe_transfer_pilot.py"},
        "cases": rows,
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUT), "summary": payload["summary"]}, indent=2))


if __name__ == "__main__":
    main()
