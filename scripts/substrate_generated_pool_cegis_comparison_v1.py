#!/usr/bin/env python3
"""Compare bounded generated-pool query policies with iterative MDL resynthesis."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import random
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts"), str(ROOT / "runners/dsl/python")]
os.environ.setdefault("OZMA_NO_LLM", "1")
os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")

from domains.engine_provenance import engine_preamble, engine_provenance, rust_source_fingerprint
engine_preamble()
from domains.generator import synthesize
from domains.query_selection import QueryRankingIndex
from substrate_rs import _native
import cegis_faculty_on_sum_of_n as tri
import jabberwock_closes_the_euler_tie as euler

STEM = "substrate_generated_pool_cegis_comparison_v1_5_20261001"
LOCK = ROOT / f"evaluation/substrate_capability/{STEM}_lock.json"
RAW = ROOT / f"evaluation/reports/{STEM}_raw.json"
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_GENERATED_POOL_CEGIS_COMPARISON_V1_PREREG_20261001.md"
AMENDMENT = ROOT / "docs/research/engine_substrate/SUBSTRATE_GENERATED_POOL_CEGIS_COMPARISON_V1_1_AMENDMENT_20261001.md"
AMENDMENT_2 = ROOT / "docs/research/engine_substrate/SUBSTRATE_GENERATED_POOL_CEGIS_COMPARISON_V1_2_AMENDMENT_20261001.md"
AMENDMENT_3 = ROOT / "docs/research/engine_substrate/SUBSTRATE_GENERATED_POOL_CEGIS_COMPARISON_V1_3_AMENDMENT_20261001.md"
AMENDMENT_4 = ROOT / "docs/research/engine_substrate/SUBSTRATE_GENERATED_POOL_CEGIS_COMPARISON_V1_4_AMENDMENT_20261001.md"
AMENDMENT_5 = ROOT / "docs/research/engine_substrate/SUBSTRATE_GENERATED_POOL_CEGIS_COMPARISON_V1_5_AMENDMENT_20261001.md"
SOURCE_PATHS = (
    "domains/generator.py", "domains/query_selection.py", "domains/engine_provenance.py",
    "scripts/cegis_faculty_on_sum_of_n.py", "scripts/jabberwock_closes_the_euler_tie.py",
    "scripts/substrate_generated_pool_cegis_comparison_v1.py",
    "scripts/analyze_substrate_generated_pool_cegis_comparison_v1.py",
    "docs/research/engine_substrate/SUBSTRATE_GENERATED_POOL_CEGIS_COMPARISON_V1_PREREG_20261001.md",
    "docs/research/engine_substrate/SUBSTRATE_GENERATED_POOL_CEGIS_COMPARISON_V1_1_AMENDMENT_20261001.md",
    "docs/research/engine_substrate/SUBSTRATE_GENERATED_POOL_CEGIS_COMPARISON_V1_2_AMENDMENT_20261001.md",
    "docs/research/engine_substrate/SUBSTRATE_GENERATED_POOL_CEGIS_COMPARISON_V1_3_AMENDMENT_20261001.md",
    "docs/research/engine_substrate/SUBSTRATE_GENERATED_POOL_CEGIS_COMPARISON_V1_4_AMENDMENT_20261001.md",
    "docs/research/engine_substrate/SUBSTRATE_GENERATED_POOL_CEGIS_COMPARISON_V1_5_AMENDMENT_20261001.md",
)
OPS = ("Plus", "Times", "Minus", "Div")
CONSTS = (0, 1, 2, -1)
MAX_SIZE_BY_TASK = {"triangular": 7, "square": 5, "euler": 5}
POOL_TIMEOUT_S = 30.0
POOL_LIMIT = 10000
SEED = 20261001
ARMS = ("mdl_cegis", "entropy_pool", "first_pool", "random_pool")


def digest(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def lock_payload() -> dict:
    native = Path(_native.__file__).resolve()
    return {
        "schema_version": 1,
        "sources": {name: digest(ROOT / name) for name in SOURCE_PATHS},
        "native_extension": {"path": str(native), "sha256": digest(native)},
        "native_build_manifest_sha256": digest(ROOT / "runners/dsl/python/substrate_rs/_native.build.json"),
        "engine_provenance": engine_provenance(),
        "rust_source_fingerprint": rust_source_fingerprint(str(ROOT)),
        "commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "design": {
            "tasks": ["triangular", "square", "euler"], "arms": list(ARMS),
            "ops": list(OPS), "constants": list(CONSTS), "max_size_by_task": MAX_SIZE_BY_TASK,
            "pool_timeout_s": POOL_TIMEOUT_S, "pool_limit": POOL_LIMIT,
            "include_output_constants": False, "seed": SEED, "repetitions": 5,
            "worker_order": "randomized across all task/arm cells within each repetition",
            "learner_wall_cost": "synthesis + selection/prediction/filter + labeled training/query oracle wall time",
            "evaluator_checks_separate": True,
            "random_seed": "20261001 + 100 * task_index + replicate",
        },
    }


def make_tasks(substrate):
    triangle_oracle = tri.make_oracle(substrate)
    euler_oracle = euler._make_labeller(substrate)

    def triangle_describe(n):
        return {"n": float(n)}

    def square_describe(n):
        return {"x": float(n)}

    def square_oracle(n):
        return int(n) * int(n)

    def euler_describe(value):
        return euler.describe(value)

    return {
        "triangular": {
            "describe": triangle_describe, "oracle": triangle_oracle,
            "knowns": [("n1", 1), ("n2", 2)],
            "candidates": [(f"n{n}", n) for n in (0, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12)],
            "heldout": [(f"n{n}", n) for n in (13, 17, 23, 31)],
            "max_size": MAX_SIZE_BY_TASK["triangular"],
        },
        "square": {
            "describe": square_describe, "oracle": square_oracle,
            "knowns": [("x1", 1), ("x2", 2)],
            "candidates": [(f"x{n}", n) for n in (-4, -3, -2, -1, 0, 3, 4, 5, 6, 7)],
            "heldout": [(f"x{n}", n) for n in (8, 11, 13, 19)],
            "max_size": MAX_SIZE_BY_TASK["square"],
        },
        "euler": {
            "describe": euler_describe, "oracle": euler_oracle,
            "knowns": [("point", [[0]]), ("edge", [[0, 1]]),
                       ("triangle", [[0, 1, 2]])],
            "candidates": list(euler._family()),
            "heldout": [
                ("pentagon-loop", [[0, 1], [1, 2], [2, 3], [3, 4], [4, 0]]),
                ("two-hollow-triangles", [[0, 1], [1, 2], [0, 2], [3, 4], [4, 5], [3, 5]]),
                ("two-filled-triangles", [[0, 1, 2], [3, 4, 5]]),
                ("two-loops-one-vertex", [[0, 1], [1, 2], [2, 3], [3, 0],
                                           [0, 4], [4, 5], [5, 6], [6, 0]]),
                ("three-triangle-chain", [[0, 1, 2], [1, 2, 3], [2, 3, 4]]),
                ("two-tetra-boundaries", [list(c) for c in __import__("itertools").combinations(range(4), 3)] +
                 [list(c) for c in __import__("itertools").combinations(range(4, 8), 3)]),
            ],
            "max_size": MAX_SIZE_BY_TASK["euler"],
        },
    }


def equal(left, right) -> bool:
    try:
        return abs(float(left) - float(right)) <= 1e-9
    except (TypeError, ValueError):
        return left == right


def approx_heap(value, seen=None) -> int:
    if seen is None:
        seen = set()
    identity = id(value)
    if identity in seen:
        return 0
    seen.add(identity)
    size = sys.getsizeof(value)
    if isinstance(value, dict):
        size += sum(approx_heap(k, seen) + approx_heap(v, seen) for k, v in value.items())
    elif isinstance(value, (list, tuple, set, frozenset)):
        size += sum(approx_heap(item, seen) for item in value)
    return size


def call_oracle(task, value, counters):
    start, cpu = time.perf_counter(), time.process_time()
    answer = task["oracle"](value)
    counters["oracle_wall_s"] += time.perf_counter() - start
    counters["oracle_cpu_s"] += time.process_time() - cpu
    counters["oracle_calls"] += 1
    return answer


def synthesize_for(task, substrate, rows, counters, *, collect=False):
    wall, cpu = time.perf_counter(), time.process_time()
    examples = [(task["describe"](value), label) for _, value, label in rows]
    kwargs = dict(ops=OPS, consts=CONSTS, max_size=task["max_size"],
                  timeout_s=POOL_TIMEOUT_S, include_output_constants=False)
    if collect:
        kwargs.update(probe_envs=[task["describe"](value) for _, value in task["candidates"]],
                      max_solutions=POOL_LIMIT, saturate_k=999999)
    result = synthesize(substrate, examples, **kwargs)
    counters["synthesis_wall_s"] += time.perf_counter() - wall
    counters["synthesis_cpu_s"] += time.process_time() - cpu
    counters["terms_explored"] += result.get("explored", 0)
    return result


def run_mdl(task, task_name, substrate):
    counters = {"oracle_calls": 0, "oracle_wall_s": 0.0, "oracle_cpu_s": 0.0,
                "synthesis_wall_s": 0.0, "synthesis_cpu_s": 0.0, "terms_explored": 0,
                "selection_wall_s": 0.0, "selection_cpu_s": 0.0,
                "evaluation_wall_s": 0.0, "evaluation_cpu_s": 0.0}
    rows = [(name, value, call_oracle(task, value, counters))
            for name, value in task["knowns"]]
    used = {name for name, _, _ in rows}
    remaining = [(name, value) for name, value in task["candidates"]]
    query_log = []
    fit = False
    converged = False
    stop_reason = "round_limit"
    for round_index in range(16):
        result = synthesize_for(task, substrate, rows, counters)
        if not result.get("fits") or result.get("term") is None:
            stop_reason = result.get("halt_reason", "no_fit")
            break
        fit = True
        found = None
        for name, value in remaining:
            select_start, select_cpu = time.perf_counter(), time.process_time()
            prediction = result["term"].evaluate(task["describe"](value), substrate)
            counters["selection_wall_s"] += time.perf_counter() - select_start
            counters["selection_cpu_s"] += time.process_time() - select_cpu
            answer = call_oracle(task, value, counters)
            query_log.append({"name": name, "prediction": prediction, "answer": answer,
                              "is_counterexample": not equal(prediction, answer)})
            if not equal(prediction, answer):
                found = (name, value, answer)
                break
        if found is None:
            converged, stop_reason = True, "family_converged"
            final_term, final_term_str = result["term"], result.get("term_str")
            break
        name, value, answer = found
        rows.append((name, value, answer))
        used.add(name)
        remaining = [(nm, inp) for nm, inp in remaining if nm != name]
    else:
        result = None
    final_term = locals().get("final_term", result.get("term") if result else None)
    final_term_str = locals().get("final_term_str", result.get("term_str") if result else None)
    held = []
    eval_wall, eval_cpu = time.perf_counter(), time.process_time()
    for name, value in task["heldout"]:
        answer = task["oracle"](value)
        prediction = final_term.evaluate(task["describe"](value), substrate) if final_term else None
        held.append({"name": name, "prediction": prediction, "answer": answer,
                     "correct": final_term is not None and equal(prediction, answer)})
    counters["evaluation_wall_s"] += time.perf_counter() - eval_wall
    counters["evaluation_cpu_s"] += time.process_time() - eval_cpu
    return {"task": task_name, "arm": "mdl_cegis", "fit": fit,
            "converged": converged, "stop_reason": stop_reason,
            "final_term": final_term_str, "query_log": query_log,
            "training_rows": [name for name, _, _ in rows], "heldout": held,
            "heldout_exact": bool(held) and all(item["correct"] for item in held),
            "counters": counters}


def run_pool(task, task_name, arm, substrate):
    counters = {"oracle_calls": 0, "oracle_wall_s": 0.0, "oracle_cpu_s": 0.0,
                "synthesis_wall_s": 0.0, "synthesis_cpu_s": 0.0, "terms_explored": 0,
                "selection_wall_s": 0.0, "selection_cpu_s": 0.0,
                "evaluation_wall_s": 0.0, "evaluation_cpu_s": 0.0}
    rows = [(name, value, call_oracle(task, value, counters))
            for name, value in task["knowns"]]
    result = synthesize_for(task, substrate, rows, counters, collect=True)
    terms = [item["term"] for item in result.get("hypotheses", [])]
    pool_complete = result.get("halt_reason") == "max_size"
    target_supported = False
    eval_wall, eval_cpu = time.perf_counter(), time.process_time()
    if terms:
        target_supported = any(all(equal(term.evaluate(task["describe"](value), substrate),
                                   task["oracle"](value))
                                   for _, value in task["heldout"]) for term in terms)
    counters["evaluation_wall_s"] += time.perf_counter() - eval_wall
    counters["evaluation_cpu_s"] += time.process_time() - eval_cpu
    if not pool_complete or not terms:
        return {"task": task_name, "arm": arm, "pool_complete": pool_complete,
                "pool_halt_reason": result.get("halt_reason"), "pool_size": len(terms),
                "target_supported_on_heldout": target_supported,
                "stop_reason": "incomplete_pool_or_empty", "query_log": [], "heldout": [],
                "heldout_exact": False, "counters": counters,
                "solution_limit": POOL_LIMIT}

    active = list(range(len(terms)))
    remaining = list(range(len(task["candidates"])))
    rng = random.Random(SEED + 100 * list(("triangular", "square", "euler")).index(task_name)
                        + int(os.environ.get("OZMA_TRIAL_REPLICATE", "0")))
    if arm == "random_pool":
        rng.shuffle(remaining)
    index = None
    index_build_wall_s = index_build_cpu_s = 0.0
    index_heap = 0
    if arm == "entropy_pool":
        start, cpu = time.perf_counter(), time.process_time()
        index = QueryRankingIndex(substrate, terms, task["describe"], task["candidates"])
        index_build_wall_s, index_build_cpu_s = time.perf_counter() - start, time.process_time() - cpu
        index_heap = approx_heap((index._values, index._keys))
        counters["selection_wall_s"] += index_build_wall_s
        counters["selection_cpu_s"] += index_build_cpu_s

    query_log = []
    while len(active) > 1 and remaining:
        start, cpu = time.perf_counter(), time.process_time()
        if arm == "entropy_pool":
            ranked = index.rank(active, remaining)
            chosen = ranked[0]["candidate_index"]
        else:
            chosen = remaining[0]
        counters["selection_wall_s"] += time.perf_counter() - start
        counters["selection_cpu_s"] += time.process_time() - cpu
        name, value = task["candidates"][chosen]
        answer = call_oracle(task, value, counters)
        before = len(active)
        filter_start, filter_cpu = time.perf_counter(), time.process_time()
        if index is not None:
            active = index.filter(active, chosen, answer)
            predictions = [index._values[i][chosen] for i in range(len(terms))]
        else:
            predictions = [terms[i].evaluate(task["describe"](value), substrate) for i in active]
            active = [i for i, prediction in zip(active, predictions) if equal(prediction, answer)]
        counters["selection_wall_s"] += time.perf_counter() - filter_start
        counters["selection_cpu_s"] += time.process_time() - filter_cpu
        query_log.append({"name": name, "answer": answer, "survivors_before": before,
                          "survivors_after": len(active)})
        remaining.remove(chosen)
    held = []
    eval_wall, eval_cpu = time.perf_counter(), time.process_time()
    for name, value in task["heldout"]:
        answer = task["oracle"](value)
        predictions = [terms[i].evaluate(task["describe"](value), substrate) for i in active]
        held.append({"name": name, "answer": answer,
                     "all_survivors_correct": bool(predictions) and all(equal(p, answer) for p in predictions),
                     "survivor_predictions": predictions})
    counters["evaluation_wall_s"] += time.perf_counter() - eval_wall
    counters["evaluation_cpu_s"] += time.process_time() - eval_cpu
    heldout_exact = bool(active) and all(item["all_survivors_correct"] for item in held)
    return {"task": task_name, "arm": arm, "pool_complete": pool_complete,
            "pool_halt_reason": result.get("halt_reason"), "pool_size": len(terms),
            "target_supported_on_heldout": target_supported,
            "stop_reason": "singleton" if len(active) == 1 else "query_exhausted",
            "final_survivor_count": len(active),
            "query_log": query_log, "heldout": held, "heldout_exact": heldout_exact,
            "index_build_wall_s": index_build_wall_s,
            "index_build_cpu_s": index_build_cpu_s,
            "index_heap_estimate_bytes": index_heap,
            "counters": counters, "solution_limit": POOL_LIMIT}


def worker(task_name, arm, replicate):
    os.environ["OZMA_TRIAL_REPLICATE"] = str(replicate)
    setup_start, setup_cpu = time.perf_counter(), time.process_time()
    substrate = _native.Substrate()
    task = make_tasks(substrate)[task_name]
    setup_wall = time.perf_counter() - setup_start
    setup_cpu_s = time.process_time() - setup_cpu
    start, cpu = time.perf_counter(), time.process_time()
    row = run_mdl(task, task_name, substrate) if arm == "mdl_cegis" else run_pool(task, task_name, arm, substrate)
    row["worker_wall_s"] = time.perf_counter() - start
    row["worker_cpu_s"] = time.process_time() - cpu
    row["replicate"] = replicate
    row["task_setup_wall_s"] = setup_wall
    row["task_setup_cpu_s"] = setup_cpu_s
    row["host"] = {"machine": platform.machine(), "platform": platform.platform(), "python": sys.version.split()[0]}
    row["source_lock_sha256"] = digest(LOCK)
    return row


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lock", action="store_true")
    parser.add_argument("--worker", nargs=3, metavar=("TASK", "ARM", "REPLICATE"))
    args = parser.parse_args()
    lock = lock_payload()
    if args.lock:
        print(json.dumps(lock, indent=2, sort_keys=True))
        return
    if not LOCK.is_file() or json.loads(LOCK.read_text()) != lock:
        raise SystemExit("source lock is absent or stale")
    if args.worker:
        task_name, arm, replicate_text = args.worker
        replicate = int(replicate_text)
        if task_name not in ("triangular", "square", "euler") or arm not in ARMS:
            raise SystemExit("unknown worker task or arm")
        print(json.dumps(worker(task_name, arm, replicate), sort_keys=True))
        return
    if RAW.exists():
        raise SystemExit(f"refusing to overwrite {RAW}")
    schedule = []
    for replicate in range(5):
        block = [(task, arm, replicate) for task in ("triangular", "square", "euler") for arm in ARMS]
        random.Random(SEED + replicate).shuffle(block)
        schedule.extend(block)
    rows = []
    for task_name, arm, replicate in schedule:
        cmd = [sys.executable, str(Path(__file__).resolve()), "--worker", task_name, arm, str(replicate)]
        process_start = time.perf_counter()
        try:
            completed = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True,
                                       timeout=POOL_TIMEOUT_S * 10)
        except subprocess.TimeoutExpired as exc:
            out_tail = exc.stdout or ""
            if isinstance(out_tail, bytes):
                out_tail = out_tail.decode(errors="replace")
            rows.append({"task": task_name, "arm": arm, "replicate": replicate, "worker_error": "parent_timeout",
                         "parent_subprocess_wall_s": time.perf_counter() - process_start,
                         "stdout_tail": out_tail[-2000:]})
            continue
        process_wall = time.perf_counter() - process_start
        if completed.returncode != 0:
            rows.append({"task": task_name, "arm": arm, "replicate": replicate, "worker_error": completed.stderr[-4000:],
                         "returncode": completed.returncode, "parent_subprocess_wall_s": process_wall})
            continue
        lines = [line for line in completed.stdout.splitlines() if line.strip().startswith("{")]
        if not lines:
            rows.append({"task": task_name, "arm": arm, "replicate": replicate, "worker_error": "no JSON output",
                         "stdout_tail": completed.stdout[-2000:],
                         "parent_subprocess_wall_s": process_wall})
            continue
        row = json.loads(lines[-1])
        row["parent_subprocess_wall_s"] = process_wall
        rows.append(row)
    capture = {
        "schema": "GeneratedPoolCegisComparisonV1", "lock": lock,
        "host": {"machine": platform.machine(), "platform": platform.platform(), "python": sys.version.split()[0]},
        "schedule": schedule, "comparisons": rows,
        "capture_complete": len(rows) == len(schedule) and all("worker_error" not in row for row in rows),
    }
    RAW.parent.mkdir(parents=True, exist_ok=True)
    RAW.write_text(json.dumps(capture, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"capture": str(RAW.relative_to(ROOT)), "rows": len(rows),
                      "capture_complete": capture["capture_complete"]}, indent=2))


if __name__ == "__main__":
    main()
