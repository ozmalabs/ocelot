#!/usr/bin/env python3
"""Compare uncached and lazy query selection on substrate-generated Terms."""
from __future__ import annotations
import hashlib, itertools, json, math, os, platform, random, resource, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts"), str(ROOT / "runners/dsl/python")]
os.environ.setdefault("OZMA_NO_LLM", "1")
RUNNER = Path(__file__).resolve()
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_CONTRACT_QUERY_GENERATED_CUBIC_TRANSFER_V1_PREREG_20261002.md"
ANALYZER = ROOT / "evaluation/substrate_capability/analyze_substrate_query_generated_cubic_transfer_v1.py"
LOCK = ROOT / "evaluation/substrate_capability/substrate_contract_query_generated_cubic_transfer_v1_lock_20261002.json"
RAW = ROOT / "evaluation/reports/substrate_contract_query_generated_cubic_transfer_v1_raw_20261002.json"
REPS = 3
SEED = 20261107
OPS = ("Plus", "Times", "Minus", "Div")
CONSTS = (0, 1, 2, -1)
MAX_SIZE = {"cubic": 5}
TIMEOUT_S = 30.0
POOL_LIMIT = 10000
ACTIVE = ("domains/contract_query.py", "domains/generator.py", "domains/query_selection.py",
          "domains/engine_provenance.py",
          "runners/dsl/src/term.rs", "runners/dsl/src/py.rs",
          "runners/dsl/python/substrate_rs/__init__.py", "runners/dsl/python/substrate_rs/_native.build.json",
           )


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def active_hashes() -> dict:
    sys.path[:0] = [str(ROOT / "runners/dsl/python"), str(ROOT)]
    import substrate_rs as sr
    result = {name: sha(ROOT / name) for name in ACTIVE}
    result["native"] = sha(Path(sr._native.__file__).resolve())
    return result


def task_specs() -> dict:
    def describe(value):
        return {"x": float(value)}
    def oracle(value):
        return float(int(value) ** 3)
    spec = {
        "knowns": [("x0", 0), ("x1", 1)],
        "candidates": [(f"x{n}", n) for n in (-4, -3, -2, 2, 3, 4, 5, 6, 7, 8, 9)],
        "heldout": [(f"x{n}", n) for n in (10, 12, 15, 19, 23)],
    }
    return {"cubic": {
        "knowns": [{"name": label, "value": value, "env": describe(value), "answer": oracle(value)}
                   for label, value in spec["knowns"]],
        "candidates": [{"name": label, "value": value, "env": describe(value), "answer": oracle(value)}
                       for label, value in spec["candidates"]],
        "heldout": [{"name": label, "value": value, "env": describe(value), "answer": oracle(value)}
                    for label, value in spec["heldout"]], "max_size": MAX_SIZE["cubic"]}}


def payload() -> dict:
    files = (RUNNER, ANALYZER, PROTOCOL)
    return {"schema": "SubstrateContractQueryGeneratedCubicTransferV1Lock",
            "files": {str(path.relative_to(ROOT)): sha(path) for path in files},
            "active": active_hashes(),
            "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "design": {"tasks": task_specs(), "repetitions": REPS, "seed": SEED,
                       "ops": list(OPS), "constants": list(CONSTS), "max_size_by_task": MAX_SIZE,
                       "timeout_seconds": TIMEOUT_S, "pool_limit": POOL_LIMIT,
                       "include_output_constants": False, "target_passed_to_selector": False}}


def eval_term(term: dict, env: dict, native):
    value = native.evaluate(term, env)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"generated hypothesis returned nonnumeric value {value!r}")
    return float(value)


def select_sequence(arm: str, native, task: dict, term_dicts: list[dict], counters: dict) -> dict:
    from domains.contract_query import TermPredictionMatrix, select_discriminating_input, select_discriminating_input_batched
    hypotheses = [{"id": f"p{index}", "term": term} for index, term in enumerate(term_dicts)]
    candidates = [row["env"] for row in task["candidates"]]
    answer_by_env = {}
    name_by_env = {}
    for row in task["candidates"]:
        key = json.dumps(row["env"], sort_keys=True, separators=(",", ":"))
        answer_by_env.setdefault(key, float(row["answer"]))
        name_by_env.setdefault(key, row["name"])
    observations = [{"inputs": row["env"], "expected": float(row["answer"])} for row in task["knowns"]]
    calls = 0

    def counted(term, env):
        nonlocal calls
        calls += 1
        return eval_term(term, env, native)

    matrix = TermPredictionMatrix(counted, hypotheses, candidates) if arm == "lazy_matrix" and len(hypotheses) > 1 else None
    start_wall, start_cpu = time.perf_counter(), time.process_time()
    history = []
    for _ in range(len(hypotheses) + 1):
        if len(hypotheses) < 2:
            terminal = {"ok": False, "reason": "generated pool already singleton", "surviving_hypotheses": [hypotheses[0]["id"]] if hypotheses else []}
            break
        if arm == "lazy_matrix":
            selected = select_discriminating_input_batched(counted, hypotheses, candidates, observations, matrix)
        else:
            selected = select_discriminating_input(counted, hypotheses, candidates, observations)
        if not selected.get("ok"):
            terminal = selected
            break
        env = selected["query"]
        key = json.dumps(env, sort_keys=True, separators=(",", ":"))
        if key not in answer_by_env:
            raise RuntimeError("selector returned an environment outside the locked candidate family")
        answer = answer_by_env[key]
        history.append({"query": env, "name": name_by_env[key], "entropy_bits": selected["entropy_bits"],
                        "partition_count": selected["partition_count"],
                        "survivors_before": selected["surviving_hypotheses"],
                        "predictions": selected["predictions"], "oracle_output": answer})
        observations.append({"inputs": env, "expected": answer})
        counters["oracle_calls"] += 1
    else:
        terminal = {"ok": True, "reason": "query budget exhausted"}
    elapsed_wall, elapsed_cpu = time.perf_counter() - start_wall, time.process_time() - start_cpu
    survivor_ids = terminal.get("surviving_hypotheses", [])
    heldout = []
    for row in task["heldout"]:
        predictions = [eval_term(term_dicts[int(hypothesis_id[1:])], row["env"], native)
                       for hypothesis_id in survivor_ids]
        heldout.append({"name": row["name"], "answer": float(row["answer"]), "predictions": predictions,
                        "all_correct": bool(predictions) and all(abs(value - float(row["answer"])) <= 1e-9 for value in predictions)})
    counters["selector_native_calls"] = calls
    counters["selector_wall_seconds"] = elapsed_wall
    counters["selector_cpu_seconds"] = elapsed_cpu
    return {"history": history, "terminal": terminal, "survivor_ids": survivor_ids,
            "final_survivor_count": len(survivor_ids), "heldout": heldout,
            "heldout_exact": bool(heldout) and all(row["all_correct"] for row in heldout),
            "matrix_cells": matrix.cells if matrix else 0,
            "matrix_approximate_bytes": matrix.approximate_bytes if matrix else 0,
            "counters": counters}


def worker(task_name: str, rep: int) -> dict:
    os.environ.setdefault("OZMA_SEED_PERSIST_DISABLED", "1")
    lock = json.loads(LOCK.read_text())
    before = active_hashes()
    if before != lock["active"]:
        raise RuntimeError("active source/native hash differs from lock")
    from substrate_rs import _native
    from domains.engine_provenance import engine_preamble
    engine_preamble()
    from domains.generator import synthesize
    substrate = _native.Substrate()
    native = substrate
    task = dict(lock["design"]["tasks"][task_name])
    task["task_name"] = task_name
    examples = [(row["env"], float(row["answer"])) for row in task["knowns"]]
    probe_envs = [row["env"] for row in task["candidates"]]
    start_wall, start_cpu = time.perf_counter(), time.process_time()
    pool = synthesize(substrate, examples, ops=OPS, consts=CONSTS, max_size=task["max_size"],
                      timeout_s=TIMEOUT_S, include_output_constants=False,
                      probe_envs=probe_envs, max_solutions=POOL_LIMIT, saturate_k=999999)
    synthesis_wall, synthesis_cpu = time.perf_counter() - start_wall, time.process_time() - start_cpu
    term_dicts = [item["term"].to_dict() for item in pool.get("hypotheses", [])]
    pool_hash = hashlib.sha256(json.dumps(term_dicts, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    for term in term_dicts:
        allowed = {"Var", "Lit", "Plus", "Times", "Minus", "Div"}
        def walk(node):
            if isinstance(node, dict):
                op = node.get("type")
                if op is not None and op not in allowed:
                    raise RuntimeError(f"generated pool contains unsupported Term operator {op}")
                for child in node.values():
                    walk(child)
            elif isinstance(node, (list, tuple)):
                for child in node:
                    walk(child)
        walk(term)
    pool_complete = pool.get("halt_reason") == "max_size"
    # Oracle support is independently checked by the locked term interpreter.
    supported = False
    for term in term_dicts:
        if all(abs(eval_term(term, row["env"], native) - float(row["answer"])) <= 1e-9
               for row in task["heldout"]):
            supported = True
            break
    outcomes = {}
    for arm in ("uncached", "lazy_matrix"):
        counters = {"oracle_calls": 0}
        if len(term_dicts) < 2:
            singleton_heldout = []
            for heldout_row in task["heldout"]:
                prediction = eval_term(term_dicts[0], heldout_row["env"], native) if term_dicts else None
                singleton_heldout.append({"name": heldout_row["name"], "answer": float(heldout_row["answer"]),
                                          "predictions": [] if not term_dicts else [prediction],
                                          "all_correct": bool(term_dicts) and abs(prediction - float(heldout_row["answer"])) <= 1e-9})
            outcomes[arm] = {"history": [], "terminal": {"ok": False, "reason": "generated pool already singleton",
                                                            "surviving_hypotheses": ["p0"] if term_dicts else []},
                             "survivor_ids": ["p0"] if term_dicts else [], "final_survivor_count": len(term_dicts),
                             "heldout": singleton_heldout,
                             "heldout_exact": bool(singleton_heldout) and all(row["all_correct"] for row in singleton_heldout),
                             "matrix_cells": 0,
                             "matrix_approximate_bytes": 0,
                             "counters": {"selector_native_calls": 0, "selector_wall_seconds": 0.0,
                                          "selector_cpu_seconds": 0.0}}
        else:
            outcomes[arm] = select_sequence(arm, native, task, term_dicts, counters)
    after = active_hashes()
    return {"kind": "worker", "task": task_name, "rep": rep, "pid": os.getpid(),
            "before": before, "after": after, "source_stable": before == after,
            "pool": {"complete": pool_complete, "halt_reason": pool.get("halt_reason"),
                     "size": len(term_dicts), "terms_explored": pool.get("explored"),
                     "pool_hash": pool_hash, "target_supported_heldout": supported,
                     "synthesis_wall_seconds": synthesis_wall, "synthesis_cpu_seconds": synthesis_cpu,
                     "term_dicts": term_dicts},
            "outcomes": outcomes, "host": {"platform": platform.platform(), "python": sys.version.split()[0]},
            "peak_rss_bytes": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * 1024}


def main() -> int:
    if sys.argv[1:] == ["--lock"]:
        if LOCK.exists() or RAW.exists():
            raise SystemExit("refusing to overwrite lock or capture")
        LOCK.write_text(json.dumps(payload(), indent=2, sort_keys=True) + "\n")
        print(LOCK.relative_to(ROOT))
        return 0
    current = payload()
    if not LOCK.exists() or json.loads(LOCK.read_text()) != current:
        raise SystemExit("missing or stale source lock")
    if RAW.exists():
        raise SystemExit("refusing to overwrite raw capture")
    schedule = [("cubic", rep) for rep in range(1, REPS + 1)]
    random.Random(SEED).shuffle(schedule)
    env = dict(os.environ, OZMA_NO_LLM="1", OZMA_SEED_PERSIST_DISABLED="1")
    env["PYTHONPATH"] = f"{ROOT}:{ROOT / 'scripts'}:{ROOT / 'runners/dsl/python'}:{env.get('PYTHONPATH', '')}"
    rows = []
    start = time.perf_counter()
    for index, (task, rep) in enumerate(schedule, 1):
        proc = subprocess.run([sys.executable, str(RUNNER), "--worker", task, str(rep)],
                              cwd=ROOT, env=env, text=True, capture_output=True, timeout=360)
        row = json.loads(proc.stdout.strip().splitlines()[-1]) if proc.returncode == 0 else {
            "kind": "worker_error", "task": task, "rep": rep, "error": proc.stderr[-5000:]}
        rows.append(row)
        print(f"{index}/{len(schedule)} {task} r={rep}: {row['kind']}", flush=True)
    post = payload()
    RAW.write_text(json.dumps({"schema": "SubstrateContractQueryGeneratedCubicTransferV1Capture",
                               "lock": current, "post_lock": post, "schedule": schedule,
                               "workers": rows, "elapsed_seconds": time.perf_counter() - start,
                               "environment": {"python": sys.version, "platform": platform.platform()}},
                              indent=2, sort_keys=True, default=str) + "\n")
    print(json.dumps({"raw": str(RAW.relative_to(ROOT)), "workers": len(rows),
                      "errors": sum(row.get("kind") != "worker" for row in rows), "stable": current == post}))
    return 0


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "--worker":
        print(json.dumps(worker(sys.argv[2], int(sys.argv[3])), sort_keys=True, default=str))
    else:
        raise SystemExit(main())
