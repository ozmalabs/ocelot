#!/usr/bin/env python3
"""Measure direct native SynthEnumerate on the frozen list-PBE pilot suite."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import platform
import resource
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/substrate_list_pbe/tasks.json"
OUT = ROOT / "evaluation/reports/substrate_list_pbe_pilot_20260925.json"
MAX_SIZE = 15
MAX_CANDIDATES = 200_000
DECLARED_OPS = [
    "Plus", "Times", "Minus", "Div", "Min", "Max", "Abs", "Neg", "Gt", "Lt", "Eq", "IfThenElse", "Mod",
    "Len", "SumList", "MaxList", "MinList", "MaxLenOver", "MinLenOver", "First", "LastElem", "JoinList",
    "FilterList", "MapList", "ProdList", "ConcatList", "ArgMaxLenOver", "Reverse",
]
DECLARED_CONSTS = [-1, 0, 1, 2, 3]
ARMS = ("typed_default", "fixed_declared_list_grammar")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def wilson(k: int, n: int) -> list[float]:
    if not n:
        return [0.0, 1.0]
    z = 1.959963984540054
    p = k / n
    den = 1 + z * z / n
    center = (p + z * z / (2 * n)) / den
    half = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / den
    return [max(0.0, center - half), min(1.0, center + half)]


def wire_examples(rows: list[dict]) -> list[dict]:
    from domains.prog_synthesis import _wire_rows
    return _wire_rows([{"inputs": dict(r["inputs"]), "output": r["output"]} for r in rows])


def run_one(task: dict, arm: str) -> dict:
    from substrate_rs import Substrate

    s = Substrate()
    examples = wire_examples(task["revealed"])
    spec = {
        "type": "SynthEnumerate",
        "examples": {"type": "Lit", "value": examples},
        "ops": {"type": "Lit", "value": DECLARED_OPS} if arm != "typed_default" else None,
        "consts": {"type": "Lit", "value": DECLARED_CONSTS} if arm != "typed_default" else None,
        "exclude": None, "max_size": MAX_SIZE,
        "max_candidates": MAX_CANDIDATES, "saturate_k": 0, "field": "",
    }
    start = time.perf_counter_ns()
    result = s._inner.evaluate(spec, {})
    search_ns = time.perf_counter_ns() - start
    row = {
        "task_id": task["task_id"], "category": task["category"], "arm": arm,
        "found": bool(result.get("found")), "halt_reason": result.get("halt_reason"),
        "tested_candidates": result.get("tested"), "distinct_candidates": result.get("distinct"),
        "size": result.get("size"), "term_str": result.get("term_str"),
        "search_wall_ns": search_ns,
    }
    if not result.get("found"):
        row["outcome"] = "not_found:" + str(result.get("halt_reason"))
        row["heldout"] = None
        return row
    term = json.loads(result["term"])
    check_start = time.perf_counter_ns()
    checks = []
    for example in task["held_out"]:
        try:
            got = s._inner.evaluate(term, dict(example["inputs"]))
            equal = got == example["output"]
            checks.append({"inputs": example["inputs"], "expected": example["output"],
                           "got": got, "exact_match": bool(equal)})
        except Exception as exc:  # reporting the evaluator boundary is part of the measure
            checks.append({"inputs": example["inputs"], "expected": example["output"],
                           "got": None, "exact_match": False,
                           "eval_exception": type(exc).__name__})
    row["holdout_check_wall_ns"] = time.perf_counter_ns() - check_start
    row["heldout"] = {"n": len(checks), "n_ok": sum(c["exact_match"] for c in checks),
                      "all_ok": bool(checks) and all(c["exact_match"] for c in checks),
                      "rows": checks}
    row["outcome"] = "pass" if row["heldout"]["all_ok"] else "found_but_holdout_fail"
    row["term_json"] = term
    return row


def summarize(rows: list[dict], task_count: int) -> dict:
    outcomes = Counter(r["outcome"] for r in rows)
    passed = sum(r["outcome"] == "pass" for r in rows)
    candidates = [int(r["tested_candidates"] or 0) for r in rows]
    times = sorted(int(r["search_wall_ns"]) for r in rows)
    return {
        "n": len(rows), "pass_count": passed, "pass_rate": passed / task_count,
        "descriptive_wilson_95_interval": wilson(passed, task_count),
        "outcome_counts": dict(sorted(outcomes.items())),
        "found_count": sum(bool(r["found"]) for r in rows),
        "heldout_false_accept_count": outcomes["found_but_holdout_fail"],
        "tested_candidates_total": sum(candidates),
        "tested_candidates_median": sorted(candidates)[len(candidates) // 2],
        "search_wall_ms_total": sum(times) / 1e6,
        "search_wall_ms_median": times[len(times) // 2] / 1e6,
        "search_wall_ms_max": max(times, default=0) / 1e6,
    }


def main() -> None:
    from substrate_rs import _native
    generator_path = ROOT / "tests/fixtures/substrate_list_pbe/build_tasks.py"
    spec = importlib.util.spec_from_file_location("substrate_list_pbe_build_tasks", generator_path)
    if spec is None or spec.loader is None:
        raise SystemExit("cannot load frozen task generator")
    generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generator)
    build = generator.build

    fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))
    if fixture != build():
        raise SystemExit("frozen fixture does not match its reference generator")
    parent_start = time.perf_counter()
    parent_before = resource.getrusage(resource.RUSAGE_SELF)
    child_before = resource.getrusage(resource.RUSAGE_CHILDREN)

    arms: dict[str, list[dict]] = {name: [] for name in ARMS}
    for index, task in enumerate(fixture["tasks"]):
        order = ARMS if index % 2 == 0 else tuple(reversed(ARMS))
        for arm in order:
            arms[arm].append(run_one(task, arm))

    wall_seconds = time.perf_counter() - parent_start
    parent_after = resource.getrusage(resource.RUSAGE_SELF)
    child_after = resource.getrusage(resource.RUSAGE_CHILDREN)
    by_arm = {name: {r["task_id"]: r for r in rows} for name, rows in arms.items()}
    left, right = by_arm[ARMS[0]], by_arm[ARMS[1]]
    paired = {"both_pass": [], "typed_default_only": [], "declared_only": [], "neither_pass": []}
    for task_id in sorted(left):
        a = left[task_id]["outcome"] == "pass"
        b = right[task_id]["outcome"] == "pass"
        key = "both_pass" if a and b else "typed_default_only" if a else "declared_only" if b else "neither_pass"
        paired[key].append(task_id)

    category_summaries = {}
    for arm, rows in arms.items():
        category_summaries[arm] = {
            category: summarize([r for r in rows if r["category"] == category],
                                sum(t["category"] == category for t in fixture["tasks"]))
            for category in sorted({t["category"] for t in fixture["tasks"]})
        }
    extension = Path(_native.__file__).resolve()
    source_paths = {
        "harness": Path(__file__).resolve(),
        "fixture": FIXTURE,
        "task_generator": ROOT / "tests/fixtures/substrate_list_pbe/build_tasks.py",
        "synthesizer": ROOT / "runners/dsl/src/synth_enumerate.rs",
        "value_codec": ROOT / "runners/dsl/src/persist.rs",
        "pbe_wire_owner": ROOT / "domains/prog_synthesis.py",
        "native_extension": extension,
        "native_build_manifest": ROOT / "runners/dsl/python/substrate_rs/_native.build.json",
        "cargo_lock": ROOT / "runners/dsl/Cargo.lock",
        "preregistration": ROOT / "docs/research/engine_substrate/SUBSTRATE_LIST_PBE_PREREG_20260925.md",
        "benchmark_protocol": ROOT / "docs/research/engine_substrate/SUBSTRATE_BENCHMARK_PROTOCOL.md",
    }
    payload = {
        "schema_version": 1,
        "run_id": "substrate-list-pbe-pilot-20260925",
        "run_state": "pilot_frozen_before_outcomes",
        "protocol_version": "list-pbe-v1",
        "scope": "direct native SynthEnumerate; one fresh substrate per task/arm; exact held-out comparison; no language prompt or cross-task memory",
        "claim_boundary": "Synthetic integer-list synthesis mechanism envelope only. Does not measure full P4 residual routing, concept minting/adoption, task prevalence, or general transfer.",
        "budget": {"max_size": MAX_SIZE, "max_candidates": MAX_CANDIDATES},
        "declared_grammar": {"ops": DECLARED_OPS, "consts": DECLARED_CONSTS},
        "task_categories": {name: sum(t["category"] == name for t in fixture["tasks"])
                            for name in sorted({t["category"] for t in fixture["tasks"]})},
        "task_count": fixture["task_count"],
        "arm_summaries": {arm: summarize(rows, fixture["task_count"]) for arm, rows in arms.items()},
        "paired_task_outcomes": paired,
        "category_summaries": category_summaries,
        "resource": {
            "wall_seconds": wall_seconds,
            "parent_peak_rss_kib": parent_after.ru_maxrss,
            "parent_user_cpu_seconds": parent_after.ru_utime - parent_before.ru_utime,
            "parent_system_cpu_seconds": parent_after.ru_stime - parent_before.ru_stime,
            "child_max_rss_kib_linux_ru_maxrss": child_after.ru_maxrss,
            "child_user_cpu_seconds": child_after.ru_utime - child_before.ru_utime,
            "child_system_cpu_seconds": child_after.ru_stime - child_before.ru_stime,
        },
        "environment": {"python": sys.version, "platform": platform.platform(),
                        "controls": {k: os.environ.get(k) for k in
                                     ("OZMA_NO_LLM", "OZMA_SEED_PERSIST_DISABLED", "PYTHONHASHSEED")}},
        "provenance": {
            "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "dirty_worktree": bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip()),
            "native_extension_path": str(extension), "native_extension_sha256": sha(extension),
            "source_sha256": {name: sha(path) for name, path in source_paths.items()},
            "command": "PYTHONPATH=runners/dsl/python:. OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 python3 scripts/substrate_list_pbe_pilot.py",
        },
        "cases": arms,
    }
    OUT.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUT), "wall_seconds": wall_seconds,
                      "arm_summaries": payload["arm_summaries"],
                      "paired_task_outcomes": {k: len(v) for k, v in paired.items()},
                      "resource": payload["resource"],
                      "native_extension_sha256": payload["provenance"]["native_extension_sha256"]}, indent=2))


if __name__ == "__main__":
    main()
