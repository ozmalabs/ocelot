#!/usr/bin/env python3
"""Measure the lazy prediction matrix over query depth and survivor fraction."""
from __future__ import annotations
import hashlib, json, math, os, platform, random, resource, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER = Path(__file__).resolve()
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_CONTRACT_QUERY_LAZY_MATRIX_CROSSOVER_V1_PREREG_20261002.md"
ANALYZER = ROOT / "evaluation/substrate_capability/analyze_substrate_query_lazy_matrix_crossover_v1.py"
LOCK = ROOT / "evaluation/substrate_capability/substrate_contract_query_lazy_matrix_crossover_v1_lock_20261002.json"
RAW = ROOT / "evaluation/reports/substrate_contract_query_lazy_matrix_crossover_v1_raw_20261002.json"
REPS = 3
SEED = 20261106
CASES = [("h128_m0", 128, 28, 0), ("h128_m4", 128, 28, 4), ("h128_m7", 128, 28, 7),
         ("h512_m0", 512, 36, 0), ("h512_m4", 512, 36, 4), ("h512_m9", 512, 36, 9)]
ACTIVE = ("domains/contract_query.py", "runners/dsl/src/term.rs", "runners/dsl/src/py.rs",
          "runners/dsl/python/substrate_rs/__init__.py", "runners/dsl/python/substrate_rs/_native.build.json")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def active_hashes() -> dict:
    sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
    import substrate_rs as sr
    hashes = {name: sha(ROOT / name) for name in ACTIVE}
    hashes["native"] = sha(Path(sr._native.__file__).resolve())
    return hashes


def term_for(index: int, bits: int) -> dict:
    var = {"type": "Var", "name": "x"}
    term = var
    for bit, point in reversed(list(enumerate(range(-bits, 0)))):
        term = {"type": "IfThenElse", "cond": {"type": "Eq", "a": var, "b": {"type": "Lit", "value": point}},
                "then": {"type": "Lit", "value": 10 * ((index >> bit) & 1)}, "other": term}
    return term


def oracle(index: int, bits: int, x: int) -> int:
    for bit, point in enumerate(range(-bits, 0)):
        if x == point:
            return 10 * ((index >> bit) & 1)
    return x


def make_case(name: str, h: int, n: int, m: int) -> dict:
    bits = int(math.log2(h))
    inputs = list(range(-bits, 0)) + list(range(1, n - bits + 1))
    target = h // 3
    observations = [{"inputs": {"x": 0}, "expected": 0}]
    observations.extend({"inputs": {"x": x}, "expected": oracle(target, bits, x)}
                        for x in range(-bits, -bits + m))
    return {"name": name, "H": h, "N": n, "K": bits, "m": m, "target_id": f"h{target}",
            "hypotheses": [{"id": f"h{i}", "term": term_for(i, bits)} for i in range(h)],
            "candidate_inputs": [{"x": x} for x in inputs], "initial_observations": observations}


def payload() -> dict:
    files = (RUNNER, ANALYZER, PROTOCOL)
    return {"schema": "SubstrateContractQueryLazyMatrixCrossoverV1Lock",
            "files": {str(path.relative_to(ROOT)): sha(path) for path in files},
            "active": active_hashes(), "git_head": subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "design": {"cases": [make_case(*case) for case in CASES], "repetitions": REPS,
                       "seed": SEED, "arms": ["uncached", "lazy_matrix"],
                       "target_id_not_passed_to_selector": True}}


def run_sequence(arm: str, case: dict, counted, matrix=None, misspec=False) -> dict:
    from domains.contract_query import select_discriminating_input, select_discriminating_input_batched
    obs = list(case["initial_observations"])
    history = []
    target = int(case["target_id"][1:])
    for _ in range(case["K"] + 1):
        if arm == "lazy_matrix":
            result = select_discriminating_input_batched(counted, case["hypotheses"],
                                                         case["candidate_inputs"], obs, matrix)
        else:
            result = select_discriminating_input(counted, case["hypotheses"],
                                                 case["candidate_inputs"], obs)
        if not result.get("ok"):
            terminal = result
            break
        x = result["query"]["x"]
        label = oracle(target, case["K"], x)
        if misspec and x == 999:
            label += 100
        history.append({"query": result["query"], "entropy_bits": result["entropy_bits"],
                        "partition_count": result["partition_count"],
                        "survivors_before": result["surviving_hypotheses"],
                        "predictions": result["predictions"], "oracle_output": label})
        obs.append({"inputs": result["query"], "expected": label})
    else:
        terminal = {"ok": True, "reason": "query budget exhausted"}
    return {"history": history, "terminal": terminal}


def worker(case_name: str, rep: int, arm: str) -> dict:
    os.environ.setdefault("OZMA_NO_LLM", "1")
    lock = json.loads(LOCK.read_text())
    before = active_hashes()
    if before != lock["active"]:
        raise RuntimeError("source/native hash differs from lock")
    import substrate_rs as sr
    from domains.contract_query import TermPredictionMatrix
    native = sr.Substrate()._inner
    case = next(row for row in lock["design"]["cases"] if row["name"] == case_name)
    target, bits = int(case["target_id"][1:]), case["K"]
    for i, hypothesis in enumerate(case["hypotheses"]):
        for x in (-bits, 0, 1, bits, 999):
            if native.evaluate(hypothesis["term"], {"x": x}) != oracle(i, bits, x):
                raise RuntimeError("native Term differs from closed-form oracle")
    calls = 0

    def counted(term, env):
        nonlocal calls
        calls += 1
        return native.evaluate(term, env)

    matrix = TermPredictionMatrix(counted, case["hypotheses"], case["candidate_inputs"]) if arm == "lazy_matrix" else None
    started = time.perf_counter_ns()
    main = run_sequence(arm, case, counted, matrix)
    elapsed = time.perf_counter_ns() - started
    main_calls = calls
    misspec = run_sequence(arm, case, counted, matrix, misspec=True)
    misspec_calls = calls - main_calls
    after = active_hashes()
    return {"kind": "worker", "case": case_name, "rep": rep, "arm": arm, "pid": os.getpid(),
            "before": before, "after": after, "source_stable": before == after,
            "main": main, "main_calls": main_calls, "elapsed_ns": elapsed,
            "matrix_cells": matrix.cells if matrix else 0,
            "matrix_bytes_approx": matrix.approximate_bytes if matrix else 0,
            "misspecification": misspec, "misspecification_calls": misspec_calls,
            "heldout": {"x": 999, "finite_prediction": oracle(target, bits, 999),
                        "oracle_output": oracle(target, bits, 999) + 100},
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
        raise SystemExit("refusing to overwrite capture")
    schedule = [(name, rep, arm) for name, _, _, _ in CASES for rep in range(1, REPS + 1)
                for arm in ("uncached", "lazy_matrix")]
    random.Random(SEED).shuffle(schedule)
    env = dict(os.environ, OZMA_NO_LLM="1")
    env["PYTHONPATH"] = f"{ROOT}:{ROOT / 'runners/dsl/python'}:{env.get('PYTHONPATH', '')}"
    workers = []
    start = time.perf_counter()
    for index, (case, rep, arm) in enumerate(schedule, 1):
        proc = subprocess.run([sys.executable, str(RUNNER), "--worker", case, str(rep), arm],
                              cwd=ROOT, env=env, text=True, capture_output=True, timeout=240)
        row = json.loads(proc.stdout.strip().splitlines()[-1]) if proc.returncode == 0 else {
            "kind": "worker_error", "case": case, "rep": rep, "arm": arm, "error": proc.stderr[-4000:]}
        workers.append(row)
        print(f"{index}/{len(schedule)} {case} r={rep} {arm}: {row['kind']}", flush=True)
    post = payload()
    RAW.write_text(json.dumps({"schema": "SubstrateContractQueryLazyMatrixCrossoverV1Capture",
                               "lock": current, "post_lock": post, "workers": workers,
                               "schedule": [{"case": c, "rep": r, "arm": a} for c, r, a in schedule],
                               "elapsed_seconds": time.perf_counter() - start,
                               "environment": {"python": sys.version, "platform": platform.platform()}},
                              indent=2, sort_keys=True, default=str) + "\n")
    print(json.dumps({"raw": str(RAW.relative_to(ROOT)), "workers": len(workers),
                      "errors": sum(row.get("kind") != "worker" for row in workers), "stable": current == post}))
    return 0


if __name__ == "__main__":
    if len(sys.argv) == 5 and sys.argv[1] == "--worker":
        print(json.dumps(worker(sys.argv[2], int(sys.argv[3]), sys.argv[4]), sort_keys=True, default=str))
    else:
        raise SystemExit(main())
