#!/usr/bin/env python3
"""Independent replay and integrity checks for generated grid/misspecification v1."""
from __future__ import annotations
import hashlib, itertools, json, math, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(Path(__file__).resolve().parent), str(ROOT), str(ROOT / "scripts"), str(ROOT / "runners/dsl/python")]
LOCK = ROOT / "evaluation/substrate_capability/substrate_contract_query_generated_grid_misspec_v1_lock_20261002.json"
RAW = ROOT / "evaluation/reports/substrate_contract_query_generated_grid_misspec_v1_raw_20261002.json"
OUT = ROOT / "evaluation/reports/substrate_contract_query_generated_grid_misspec_v1_analysis_20261002.json"


def oracle(task: str, value) -> float:
    if task in ("cubic_deep", "cubic_sparse"):
        return float(int(value) ** 3)
    if task == "absolute_value":
        return float(abs(int(value)))
    faces = set()
    for maximal_face in value:
        vertices = tuple(sorted(maximal_face))
        for size in range(1, len(vertices) + 1):
            faces.update(itertools.combinations(vertices, size))
    return float(sum((-1) ** (len(face) - 1) for face in faces))


def evaluate(term: dict, env: dict) -> float:
    op = term.get("type")
    if op == "Var":
        return float(env[term["name"]])
    if op == "Lit":
        return float(term["value"])
    args = [evaluate(child, env) for child in term.get("items", [])]
    # Native Term serialization currently represents each binary operation
    # with a/b fields; tolerate the args form only if serialization changes.
    if not args:
        args = [evaluate(term[key], env) for key in ("a", "b")]
    if op == "Plus": return args[0] + args[1]
    if op == "Minus": return args[0] - args[1]
    if op == "Times": return args[0] * args[1]
    if op == "Div": return 0.0 if args[1] == 0 else args[0] / args[1]
    raise ValueError(f"unsupported operator {op!r}")


def digest(terms: list[dict]) -> str:
    return hashlib.sha256(json.dumps(terms, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def check_sequence(task_name: str, task: dict, terms: list[dict], outcome: dict) -> list[str]:
    errors = []
    ids = [f"p{i}" for i in range(len(terms))]
    survivors = list(range(len(terms)))
    observations = list(task["knowns"])
    # Independent numeric interpretation of every initial observation.
    for row in observations:
        if row["answer"] != oracle(task_name, row["value"]): errors.append("known oracle label mismatch")
        survivors = [i for i in survivors if evaluate(terms[i], row["env"]) == float(row["answer"])]
    used = {json.dumps(row["env"], sort_keys=True, separators=(",", ":")) for row in observations}
    for step in outcome["history"]:
        if len(survivors) < 2:
            errors.append("query emitted after fewer than two survivors")
            break
        scored = []
        for index, row in enumerate(task["candidates"]):
            key = json.dumps(row["env"], sort_keys=True, separators=(",", ":"))
            if key in used: continue
            vals = [evaluate(terms[i], row["env"]) for i in survivors]
            counts = {}
            for value in vals: counts[value] = counts.get(value, 0) + 1
            entropy = -sum((n / len(vals)) * math.log2(n / len(vals)) for n in counts.values() if n)
            scored.append((entropy, -index, row, vals, len(counts)))
        if not scored:
            errors.append("history continues after candidate exhaustion")
            break
        entropy, _, expected, vals, partitions = max(scored, key=lambda item: (item[0], item[1]))
        if step["query"] != expected["env"] or step["name"] != expected["name"]: errors.append("query choice differs from independent replay")
        if abs(step["entropy_bits"] - entropy) > 1e-12: errors.append("entropy differs from independent replay")
        if step["partition_count"] != partitions: errors.append("partition count differs from independent replay")
        expected_ids = [ids[i] for i in survivors]
        if step["survivors_before"] != expected_ids: errors.append("survivor set differs before query")
        recorded_predictions = [(p["hypothesis"], float(p["output"])) for p in step["predictions"]]
        if recorded_predictions != list(zip(expected_ids, vals)): errors.append("predictions differ from independent replay")
        if step["oracle_output"] != oracle(task_name, expected["value"]): errors.append("query oracle label mismatch")
        survivors = [i for i, value in zip(survivors, vals) if value == float(step["oracle_output"])]
        observations.append({"env": expected["env"], "value": expected["value"], "answer": step["oracle_output"]})
        used.add(json.dumps(expected["env"], sort_keys=True, separators=(",", ":")))
    if outcome["survivor_ids"] != [ids[i] for i in survivors]: errors.append("final survivor set differs from replay")
    if outcome["final_survivor_count"] != len(survivors): errors.append("final survivor count differs from replay")
    for row in task["heldout"]:
        if row["answer"] != oracle(task_name, row["value"]): errors.append("held-out oracle label mismatch")
        predictions = [evaluate(terms[i], row["env"]) for i in survivors]
        if outcome["heldout_exact"] and any(value != float(row["answer"]) for value in predictions): errors.append("held-out exactness claim invalid")
        if outcome["heldout"].count({"name": row["name"], "answer": float(row["answer"]), "predictions": predictions,
                                     "all_correct": bool(predictions) and all(value == float(row["answer"]) for value in predictions)}) != 1:
            errors.append("held-out predictions differ from independent replay")
    return errors


def main() -> int:
    lock = json.loads(LOCK.read_text())
    capture = json.loads(RAW.read_text())
    errors = []
    import substrate_contract_query_generated_grid_misspec_v1 as runner
    if runner.payload() != lock: errors.append("current source/native state differs from frozen lock")
    if capture["lock"] != lock: errors.append("capture lock mismatch")
    if capture["post_lock"] != lock: errors.append("post-run source lock mismatch")
    workers = capture["workers"]
    if len(workers) != 9 or any(row.get("kind") != "worker" for row in workers): errors.append("worker completion gate failed")
    seen = set()
    summaries = {}
    for worker in workers:
        key = (worker.get("task"), worker.get("rep"))
        if key in seen: errors.append("duplicate worker identity")
        seen.add(key)
        if not worker.get("source_stable"): errors.append("source changed during worker")
        if worker.get("before") != lock["active"] or worker.get("after") != lock["active"]:
            errors.append("worker source/native hash differs from frozen lock")
        task_name = worker["task"]
        task = lock["design"]["tasks"][task_name]
        terms = worker["pool"]["term_dicts"]
        if not worker["pool"]["complete"] or not terms: errors.append(f"incomplete or empty pool: {key}")
        if digest(terms) != worker["pool"]["pool_hash"]: errors.append(f"pool hash mismatch: {key}")
        if task_name == "cubic_deep" and len(terms) < 2: errors.append(f"deep cubic pool is not query-bearing: {key}")
        support = any(all(abs(evaluate(term, row["env"]) - float(row["answer"])) <= 1e-9 for row in task["heldout"]) for term in terms)
        if support != worker["pool"]["target_supported_heldout"]: errors.append(f"target support record mismatch: {key}")
        if task_name.startswith("cubic_") and not support: errors.append(f"cubic target absent from held-out support: {key}")
        for term in terms:
            for row in task["knowns"] + task["candidates"] + task["heldout"]:
                native_check = evaluate(term, row["env"])
                if not math.isfinite(native_check): errors.append(f"nonfinite generated term prediction: {key}")
        for arm, outcome in worker["outcomes"].items():
            errors.extend(f"{key}/{arm}: {error}" for error in check_sequence(task_name, task, terms, outcome))
            if arm == "lazy_matrix" and outcome["matrix_cells"] != outcome["counters"]["selector_native_calls"]:
                errors.append(f"matrix-cell/evaluation-call mismatch: {key}")
        a, b = (worker["outcomes"][name] for name in ("uncached", "lazy_matrix"))
        for field in ("history", "terminal", "survivor_ids", "final_survivor_count", "heldout", "heldout_exact"):
            if a[field] != b[field]: errors.append(f"paired semantic parity failure: {key}/{field}")
        if task_name.startswith("cubic_") and (not a["heldout_exact"] or not b["heldout_exact"]): errors.append(f"cubic survivor held-out exactness failed: {key}")
        
        summaries.setdefault(task_name, []).append({"rep": worker["rep"], "pool_size": len(terms),
            "pool_wall_s": worker["pool"]["synthesis_wall_seconds"],
            "uncached": a["counters"], "lazy_matrix": b["counters"],
            "matrix_cells": b["matrix_cells"], "heldout_exact": b["heldout_exact"]})
    analysis = {"schema": "SubstrateContractQueryGeneratedGridMisspecV1Analysis",
                "workers": len(workers), "error_count": len(errors), "errors": errors,
                "task_summaries": summaries,
                "interpretation": "Generated-pool selector evidence under probe-grid and grammar misspecification contrasts; finite authored tasks only."}
    OUT.write_text(json.dumps(analysis, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"analysis": str(OUT.relative_to(ROOT)), "workers": len(workers), "errors": len(errors), "checks_pass": not errors}, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__": raise SystemExit(main())
