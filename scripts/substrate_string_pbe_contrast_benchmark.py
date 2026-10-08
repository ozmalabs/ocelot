#!/usr/bin/env python3
"""Contrast retrieval, no-retrieval search, and candidate escalation in P4."""
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
FIXTURE = ROOT / "tests/fixtures/substrate_string_pbe_contrast/tasks.json"
OUT = ROOT / "evaluation/reports/substrate_string_pbe_contrast_20260925.json"
ARMS = ("main", "no_retrieval", "no_retrieval_escalated", "main_replay")
ESCALATED_CANDIDATES = 500_000


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_no_retrieval(sub, agent, task, *, escalated: bool):
    """Bypass only the retrieval ladder, then run the unchanged P4 pump."""
    examples = [(r["inputs"], r["expected"]) for r in task["example_rows"]]
    psy.ensure_program_synthesis(sub, sub._inner, agent)
    message = psy.ingest_spec(sub, agent, task["request_text"], examples,
                              name=task["id"])
    # Run native rules only until the top-level Goal is minted at the retrieval
    # gate; the first host retrieval verb has not run at this point.
    sub._inner.run_rules(400000)
    goals = [g for g in sub.in_neighbours(message, "about_message")
             if sub.node(g)["attrs"].get("kind") == "synth_program"]
    if len(goals) != 1:
        raise RuntimeError(f"expected one top-level goal, got {len(goals)}")
    goal = goals[0]
    status = sub.node(goal)["attrs"].get("status")
    if status != "retrieve_pending":
        raise RuntimeError(f"retrieval bypass expected retrieve_pending, got {status!r}")
    sub.set_attr(goal, "ps_ablation_no_retrieval", 1.0)
    if escalated:
        sub.set_attr(goal, "ps_enum_candidate_budget", float(ESCALATED_CANDIDATES))
    # This single rule-owned status datum skips retrieval while retaining the
    # ordinary codebook, descent, exact, enumeration and verification route.
    sub.set_attr(goal, "status", "pending")
    psy.pump(sub, agent)
    return psy.read_goal(sub, goal)


def run_case(task: dict, arm: str) -> dict:
    boot_start = time.perf_counter_ns()
    sub, agent = p4.boot(frozen=False)
    boot_ns = time.perf_counter_ns() - boot_start
    route_start = time.perf_counter_ns()
    if arm in ("no_retrieval", "no_retrieval_escalated"):
        result = run_no_retrieval(
            sub, agent, task, escalated=(arm == "no_retrieval_escalated"))
    else:
        examples = [(r["inputs"], r["expected"]) for r in task["example_rows"]]
        result = psy.synthesize_from_request(
            sub, agent, task["request_text"], examples, name=task["id"])
    route_ns = time.perf_counter_ns() - route_start
    scored = p4._build_row(sub, {**task, "stratum": task["family"]},
                           result, arm=arm)
    return {
        **scored, "family": task["family"], "boot_ns": boot_ns,
        "route_ns": route_ns,
        "ablation_no_retrieval": arm.startswith("no_retrieval"),
        "readback": {
            "construction": result.get("construction"),
            "rungs": result.get("rungs"),
            "retrieval": result.get("retrieval"),
            "enumerate": result.get("enumerate"),
            "enumerate_outcome": result.get("enumerate_outcome"),
            "gap_reason": result.get("gap_reason"),
        },
    }


def fingerprint(rows: list[dict]) -> str:
    body = [{"task_id": r["task_id"], "outcome": r["outcome"],
             "status": r["status"], "construction": r["construction"],
             "readback": r["readback"], "holdout": r.get("holdout")}
            for r in rows]
    return hashlib.sha256(json.dumps(body, sort_keys=True,
                                    separators=(",", ":")).encode()).hexdigest()


def summarize(rows: list[dict]) -> dict:
    n = len(rows)
    outcomes = Counter(r["outcome"] for r in rows)
    return {
        "n": n,
        "exact_holdout_pass": sum(r["outcome"] == "accepted_holdout_ok" for r in rows),
        "accepted": sum(r["status"] == "accepted" for r in rows),
        "accepted_holdout_fail": sum(r["outcome"] == "accepted_holdout_fail" for r in rows),
        "outcome_counts": dict(sorted(outcomes.items())),
        "enumerated": sum(bool((r.get("readback", {}).get("enumerate") or {}).get("tested"))
                           for r in rows),
        "tested_candidates": sum(int((r.get("readback", {}).get("enumerate") or {}).get("tested") or 0)
                                 for r in rows),
        "candidate_budget_requests": dict(Counter(str(
            (r.get("readback", {}).get("enumerate") or {}).get("requested_candidate_budget"))
            for r in rows if r.get("readback", {}).get("enumerate_outcome"))),
        "boot_seconds_sum": sum(r["boot_ns"] for r in rows) / 1e9,
        "route_seconds_sum": sum(r["route_ns"] for r in rows) / 1e9,
    }


def paired_bootstrap(tasks, by_arm, draws=10000):
    strata = {}
    for t in tasks:
        strata.setdefault(t["family"], []).append(t["id"])
    rng = random.Random(20260925)
    values = []
    for _ in range(draws):
        diff = n = 0
        for ids in strata.values():
            for task_id in (rng.choice(ids) for _ in ids):
                diff += int(by_arm["main"][task_id]["outcome"] == "accepted_holdout_ok")
                diff -= int(by_arm["no_retrieval"][task_id]["outcome"] == "accepted_holdout_ok")
                n += 1
        values.append(diff / n)
    values.sort()
    return {"draws": draws, "seed": 20260925,
            "stratification": "six registered task families",
            "percentile_95_interval": [values[int(.025 * draws)],
                                        values[min(draws - 1, int(.975 * draws))]]}


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
    started = time.perf_counter()
    cpu_before = resource.getrusage(resource.RUSAGE_SELF)
    rows = {arm: [] for arm in ARMS}
    for i, task in enumerate(suite["tasks"]):
        if i % 2 == 0:
            order = ARMS
        else:
            order = ("no_retrieval", "main", "main_replay", "no_retrieval_escalated")
        for arm in order:
            rows[arm].append(run_case(task, arm))
    by_arm = {arm: {r["task_id"]: r for r in items} for arm, items in rows.items()}
    paired = Counter()
    for t in suite["tasks"]:
        a = by_arm["main"][t["id"]]["outcome"] == "accepted_holdout_ok"
        b = by_arm["no_retrieval"][t["id"]]["outcome"] == "accepted_holdout_ok"
        paired["both_pass" if a and b else "main_only" if a else
               "no_retrieval_only" if b else "neither"] += 1
    main_sig = fingerprint(rows["main"])
    replay_sig = fingerprint(rows["main_replay"])
    category = {}
    for arm in ARMS:
        category[arm] = {family: summarize([r for r in rows[arm] if r["family"] == family])
                         for family in sorted({t["family"] for t in suite["tasks"]})}
    usage = resource.getrusage(resource.RUSAGE_SELF)
    extension = Path(_native.__file__).resolve()
    source_paths = {
        "harness": Path(__file__).resolve(),
        "task_generator": ROOT / "tests/fixtures/substrate_string_pbe_contrast/build_tasks.py",
        "fixture": FIXTURE,
        "preregistration": ROOT / "docs/research/engine_substrate/SUBSTRATE_STRING_PBE_CONTRAST_PREREG_20260925.md",
        "benchmark_protocol": ROOT / "docs/research/engine_substrate/SUBSTRATE_BENCHMARK_PROTOCOL.md",
        "p4_runner": ROOT / "scripts/prog_synthesis_battery.py",
        "p4_adapter": ROOT / "domains/prog_synthesis.py",
        "retrieval_adapter": ROOT / "domains/prog_retrieval.py",
        "codebook_adapter": ROOT / "domains/code_writing.py",
        "p4_seed": ROOT / "seeds/program_synthesis.json",
        "retrieval_seed": ROOT / "seeds/mbpp_exemplars.json",
        "codebook_seed": ROOT / "seeds/code_write_constructions.json",
        "native_synthesizer": ROOT / "runners/dsl/src/synth_enumerate.rs",
        "native_extension": extension,
        "native_build_manifest": ROOT / "runners/dsl/python/substrate_rs/_native.build.json",
        "cargo_lock": ROOT / "runners/dsl/Cargo.lock",
    }
    payload = {
        "schema_version": 1,
        "run_id": "substrate-string-pbe-contrast-20260925-v1",
        "run_state": "prelocked_contrastive_pilot",
        "protocol_version": "string-pbe-contrast-v1",
        "design": {"task_count": len(suite["tasks"]), "revealed": 4, "held_out": 3,
                   "arms": list(ARMS), "escalated_candidate_budget": ESCALATED_CANDIDATES,
                   "arm_order": "main/no_retrieval/no_retrieval_escalated/main_replay on even ordinals; no_retrieval/main/main_replay/no_retrieval_escalated on odd"},
        "summary": {
            "arms": {arm: summarize(items) for arm, items in rows.items()},
            "paired_main_vs_no_retrieval": dict(sorted(paired.items())),
            "paired_pass_rate_difference_main_minus_no_retrieval": (
                summarize(rows["main"])["exact_holdout_pass"] -
                summarize(rows["no_retrieval"])["exact_holdout_pass"]
            ) / len(suite["tasks"]),
            "paired_bootstrap_95": paired_bootstrap(suite["tasks"], by_arm),
            "category_summary": category,
            "main_fingerprint": main_sig,
            "main_replay_fingerprint": replay_sig,
            "main_replay_exact_match": main_sig == replay_sig,
            "wall_seconds": time.perf_counter() - started,
            "parent_peak_rss_kib": usage.ru_maxrss,
            "parent_user_cpu_seconds": usage.ru_utime - cpu_before.ru_utime,
            "parent_system_cpu_seconds": usage.ru_stime - cpu_before.ru_stime,
        },
        "environment": {"python": sys.version, "platform": platform.platform(),
                        "controls": {k: os.environ.get(k) for k in
                                     ("OZMA_NO_LLM", "OZMA_SEED_PERSIST_DISABLED", "PYTHONHASHSEED")}},
        "provenance": {"commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                       "dirty_worktree": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()),
                       "native_extension_path": str(extension),
                       "sha256": {name: sha(path) for name, path in source_paths.items()},
                       "command": "PYTHONPATH=runners/dsl/python:.:scripts OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 python3 scripts/substrate_string_pbe_contrast_benchmark.py"},
        "cases": rows,
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n",
                   encoding="utf-8")
    print(json.dumps({"output": str(OUT), "summary": payload["summary"]}, indent=2))


if __name__ == "__main__":
    main()
