#!/usr/bin/env python3
"""Partial-domain and mixed-operator coverage for the Term prediction matrix."""
from __future__ import annotations
import hashlib, json, os, platform, random, resource, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER = Path(__file__).resolve()
PROTOCOL = ROOT / "docs/research/engine_substrate/SUBSTRATE_CONTRACT_QUERY_BATCHED_PARTIAL_DOMAIN_V1_1_AMENDMENT_20261002.md"
ANALYZER = ROOT / "evaluation/substrate_capability/analyze_substrate_query_batched_partial_domain_v1_1.py"
LOCK = ROOT / "evaluation/substrate_capability/substrate_contract_query_batched_partial_domain_v1_1_lock_20261002.json"
RAW = ROOT / "evaluation/reports/substrate_contract_query_batched_partial_domain_v1_1_raw_20261002.json"
REPS = 2
SEED = 20261105
ACTIVE = ("domains/contract_query.py", "runners/dsl/src/term.rs", "runners/dsl/src/py.rs",
          "runners/dsl/python/substrate_rs/__init__.py", "runners/dsl/python/substrate_rs/_native.build.json")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def active_hashes() -> dict:
    sys.path[:0] = [str(ROOT), str(ROOT / "runners/dsl/python")]
    import substrate_rs as sr
    result = {name: sha(ROOT / name) for name in ACTIVE}
    result["native"] = sha(Path(sr._native.__file__).resolve())
    return result


def var(name: str) -> dict:
    return {"type": "Var", "name": name}


def lit(value: int) -> dict:
    return {"type": "Lit", "value": value}


def hypotheses() -> list[dict]:
    x, y = var("x"), var("y")
    return [
        {"id": "h0", "term": x},
        {"id": "h1", "term": {"type": "Plus", "items": [x, lit(1)]}},
        {"id": "h2", "term": {"type": "Minus", "a": x, "b": lit(1)}},
        {"id": "h3", "term": {"type": "Times", "items": [x, lit(2)]}},
        {"id": "h4", "term": {"type": "Abs", "arg": x}},
        {"id": "h5", "term": {"type": "Mod", "a": x, "b": lit(3)}},
        {"id": "h6", "term": {"type": "Div", "a": x, "b": lit(2)}},
        {"id": "h7", "term": {"type": "Plus", "items": [x, y]}},
    ]


def oracle(index: int, env: dict):
    x = env["x"]
    y = env.get("y", 0)
    return [lambda: x, lambda: x + 1, lambda: x - 1, lambda: x * 2,
            lambda: abs(x), lambda: x % 3, lambda: x / 2, lambda: x + y][index]()


def inputs() -> list[dict]:
    result = []
    for x in range(-5, 6):
        result.append({"x": x})
        for y in (-2, 0, 3):
            result.append({"x": x, "y": y})
    return result


def design() -> dict:
    return {"hypotheses": hypotheses(), "candidate_inputs": inputs(),
            "initial_observations": [{"inputs": {"x": 0, "y": 1}, "expected_by_target": True}],
            "targets": list(range(8)), "repetitions": REPS, "seed": SEED,
            "arms": ["uncached", "matrix"], "target_not_passed_to_selector": True}


def payload() -> dict:
    files = (RUNNER, ANALYZER, PROTOCOL)
    return {"schema": "SubstrateContractQueryBatchedPartialDomainV1_1Lock",
            "files": {str(path.relative_to(ROOT)): sha(path) for path in files},
            "active": active_hashes(),
            "git_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
            "design": design()}


def worker(target: int, rep: int, arm: str) -> dict:
    os.environ.setdefault("OZMA_NO_LLM", "1")
    lock = json.loads(LOCK.read_text())
    before = active_hashes()
    if before != lock["active"]:
        raise RuntimeError("active source/native differs from lock")
    import substrate_rs as sr
    from domains.contract_query import (TermPredictionMatrix, select_discriminating_input,
                                        select_discriminating_input_batched)
    native = sr.Substrate()._inner
    hs = lock["design"]["hypotheses"]
    grid = lock["design"]["candidate_inputs"]
    initial = lock["design"]["initial_observations"][0]["inputs"]
    initial_expected = oracle(target, initial)
    obs = [{"inputs": initial, "expected": initial_expected}]
    # Independent closed-form check covers every hypothesis on complete and partial rows.
    for i, h in enumerate(hs):
        for env in [*grid, initial]:
            actual, expected = native.evaluate(h["term"], env), oracle(i, env)
            if type(actual) is not type(expected) or actual != expected:
                raise RuntimeError(f"native/closed-form mismatch h{i} {env}: {actual!r} != {expected!r}")
    calls = 0

    def counted(term, env):
        nonlocal calls
        calls += 1
        return native.evaluate(term, env)

    matrix = TermPredictionMatrix(counted, hs, grid) if arm == "matrix" else None
    started = time.perf_counter_ns()
    history = []
    for _ in range(len(hs) + 1):
        if arm == "matrix":
            result = select_discriminating_input_batched(counted, hs, grid, obs, matrix)
        else:
            result = select_discriminating_input(counted, hs, grid, obs)
        if not result.get("ok"):
            terminal = result
            break
        env = result["query"]
        label = oracle(target, env)
        history.append({"query": env, "entropy_bits": result["entropy_bits"],
                        "partition_count": result["partition_count"],
                        "survivors_before": result["surviving_hypotheses"],
                        "predictions": result["predictions"], "oracle_output": label})
        obs.append({"inputs": env, "expected": label})
    else:
        terminal = {"ok": True, "reason": "query budget exhausted"}
    elapsed = time.perf_counter_ns() - started

    unsupported_calls = 0

    def unsupported_evaluate(term, env):
        nonlocal unsupported_calls
        unsupported_calls += 1
        return 0

    unsupported = select_discriminating_input_batched(
        unsupported_evaluate,
        [{"id": "left", "term": {"type": "Holds", "concept": "left"}},
         {"id": "right", "term": {"type": "Holds", "concept": "right"}}],
        [{"x": 1}], [])
    after = active_hashes()
    return {"kind": "worker", "target": target, "rep": rep, "arm": arm, "pid": os.getpid(),
            "before": before, "after": after, "source_stable": before == after,
            "history": history, "terminal": terminal, "native_calls": calls,
            "elapsed_ns": elapsed, "matrix_cells": matrix.cells if matrix else 0,
            "matrix_bytes_approx": matrix.approximate_bytes if matrix else 0,
            "selected_partial_count": sum("y" not in row["query"] for row in history),
            "unsupported_control": {"result": unsupported, "evaluator_calls": unsupported_calls},
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
    schedule = [(target, rep, arm) for target in range(8) for rep in range(1, REPS + 1)
                for arm in ("uncached", "matrix")]
    random.Random(SEED).shuffle(schedule)
    env = dict(os.environ, OZMA_NO_LLM="1")
    env["PYTHONPATH"] = f"{ROOT}:{ROOT / 'runners/dsl/python'}:{env.get('PYTHONPATH', '')}"
    rows = []
    start = time.perf_counter()
    for index, (target, rep, arm) in enumerate(schedule, 1):
        proc = subprocess.run([sys.executable, str(RUNNER), "--worker", str(target), str(rep), arm],
                              cwd=ROOT, env=env, text=True, capture_output=True, timeout=120)
        row = json.loads(proc.stdout.strip().splitlines()[-1]) if proc.returncode == 0 else {
            "kind": "worker_error", "target": target, "rep": rep, "arm": arm, "error": proc.stderr[-4000:]}
        rows.append(row)
        print(f"{index}/{len(schedule)} target={target} rep={rep} {arm}: {row['kind']}", flush=True)
    post = payload()
    RAW.write_text(json.dumps({"schema": "SubstrateContractQueryBatchedPartialDomainV1_1Capture",
                               "lock": current, "post_lock": post, "workers": rows,
                               "schedule": [{"target": t, "rep": r, "arm": a} for t, r, a in schedule],
                               "elapsed_seconds": time.perf_counter() - start,
                               "environment": {"python": sys.version, "platform": platform.platform()}},
                              indent=2, sort_keys=True, default=str) + "\n")
    print(json.dumps({"raw": str(RAW.relative_to(ROOT)), "workers": len(rows),
                      "errors": sum(row.get("kind") != "worker" for row in rows), "stable": current == post}))
    return 0


if __name__ == "__main__":
    if len(sys.argv) == 5 and sys.argv[1] == "--worker":
        print(json.dumps(worker(int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]), sort_keys=True, default=str))
    else:
        raise SystemExit(main())
