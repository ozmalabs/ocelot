#!/usr/bin/env python3
"""Independent replay of the post-selection adequacy gate capture."""
from __future__ import annotations
import importlib.util, itertools, json, math, sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(Path(__file__).resolve().parent), str(ROOT), str(ROOT / "runners/dsl/python")]
LOCK = ROOT / "evaluation/substrate_capability/substrate_contract_query_independent_adequacy_gate_v1_lock_20261002.json"
RAW = ROOT / "evaluation/reports/substrate_contract_query_independent_adequacy_gate_v1_raw_20261002.json"
OUT = ROOT / "evaluation/reports/substrate_contract_query_independent_adequacy_gate_v1_analysis_20261002.json"
BUDGETS = (0, 1, 2, 4)
INPUTS = {
    "generated_pool": ROOT / "evaluation/reports/substrate_contract_query_generated_pool_transfer_v1_raw_20261002.json",
    "cubic_transfer": ROOT / "evaluation/reports/substrate_contract_query_generated_cubic_transfer_v1_raw_20261002.json",
    "grid_misspec": ROOT / "evaluation/reports/substrate_contract_query_generated_grid_misspec_v1_raw_20261002.json",
    "cubic_alias": ROOT / "evaluation/reports/substrate_contract_query_generated_cubic_alias_v1_raw_20261002.json",
}


def evaluate(term: dict, env: dict) -> float:
    op = term.get("type")
    if op == "Var": return float(env[term["name"]])
    if op == "Lit": return float(term["value"])
    args = [evaluate(value, env) for value in term.get("items", [])]
    if not args: args = [evaluate(term[key], env) for key in ("a", "b")]
    if op == "Plus": return sum(args)
    if op == "Minus": return args[0] - args[1]
    if op == "Times": return math.prod(args)
    if op == "Div": return 0.0 if args[1] == 0 else args[0] / args[1]
    raise ValueError(f"unsupported Term operator {op!r}")


def label(task: str, env: dict) -> float:
    if task == "triangular":
        n = int(env["n"]); return float(n * (n + 1) // 2)
    if task == "square": return float(int(env["x"]) ** 2)
    if task in ("cubic", "cubic_deep", "cubic_sparse", "cubic_alias"):
        return float(int(env["x"]) ** 3)
    if task == "absolute_value": return float(abs(int(env["x"])))
    # The Euler audit environments are independently constructed counts; the
    # closure label is checked by the full task descriptor below.
    return float(env["V"] - env["E"] + env["F"])


def euler_descriptor(faces):
    closure = set()
    for face in faces:
        vertices = tuple(sorted(face))
        for size in range(1, len(vertices) + 1): closure.update(itertools.combinations(vertices, size))
    counts = [sum(len(face) == dimension + 1 for face in closure) for dimension in range(3)]
    env = {"V": counts[0], "E": counts[1], "F": counts[2], "ncells": len(faces),
           "maxface": max((len(face) for face in faces), default=0)}
    return env, float(sum((-1) ** dimension * count for dimension, count in enumerate(counts)))


def expected_euler_rows() -> dict:
    cases = {
        "path-5": [[0, 1], [1, 2], [2, 3], [3, 4]],
        "cycle-7": [[0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [5, 6], [6, 0]],
        "two-triangles-sharing-vertex": [[0, 1, 2], [0, 3, 4]],
        "three-triangles-sharing-vertex": [[0, 1, 2], [0, 3, 4], [0, 5, 6]],
    }
    return {name: euler_descriptor(faces) for name, faces in cases.items()}


def main() -> int:
    lock, capture = json.loads(LOCK.read_text()), json.loads(RAW.read_text())
    errors = []
    import substrate_contract_query_independent_adequacy_gate_v1 as runner
    if runner.payload() != lock: errors.append("current source/native/parent inputs differ from lock")
    if capture["lock"] != lock or capture["post_lock"] != lock: errors.append("capture lock mismatch")
    if capture["before"] != lock["active"] or capture["after"] != lock["active"]: errors.append("capture source/native hashes differ")
    cases = capture["cases"]
    if len(cases) != 24: errors.append(f"expected 24 locked worker cases, found {len(cases)}")
    seen = set()
    summary = defaultdict(lambda: defaultdict(lambda: {"accepted": 0, "rejected": 0, "refused_empty": 0,
                                                          "false_accept": 0, "false_refusal": 0,
                                                          "total": 0, "native_calls": 0, "wall_seconds": 0.0}))
    euler_rows = expected_euler_rows()
    for case in cases:
        key = (case["capture"], case["task"], case["rep"])
        if key in seen: errors.append(f"duplicate case {key}")
        seen.add(key)
        task = case["task"]
        parent = json.loads(INPUTS[case["capture"]].read_text())
        acquisition = parent["lock"]["design"]["tasks"][task]
        used_envs = {json.dumps(row["env"], sort_keys=True, separators=(",", ":"))
                     for field in ("knowns", "candidates", "heldout") for row in acquisition[field]}
        if any(json.dumps(row["env"], sort_keys=True, separators=(",", ":")) in used_envs
               for row in case["audit_rows"]):
            errors.append(f"audit descriptor is not fresh: {key}")
        if task == "euler":
            expected_rows = [{"name": name, "env": env, "answer": answer} for name, (env, answer) in euler_rows.items()]
            if case["audit_rows"] != expected_rows: errors.append(f"Euler audit descriptors/labels mismatch: {key}")
        rows = case["audit_rows"]
        expected_row_count = 0 if case["term"] is None else 4
        if len(rows) != expected_row_count: errors.append(f"wrong audit panel size: {key}")
        for row in rows:
            expected_label = row["answer"] if task == "euler" else label(task, row["env"])
            if abs(float(expected_label) - float(row["answer"])) > 1e-9: errors.append(f"audit oracle mismatch: {key}/{row['name']}")
        model_correct_on_panel = (case["term"] is not None and
                                  all(abs(evaluate(case["term"], row["env"]) - float(row["answer"])) <= 1e-9 for row in rows))
        if case["initially_empty"] != (case["term"] is None): errors.append(f"empty-model marker mismatch: {key}")
        for budget in BUDGETS:
            name = str(budget)
            measured = case["budgets"].get(name)
            if measured is None: errors.append(f"missing budget {budget}: {key}"); continue
            stats = summary[task][name]; stats["total"] += 1
            if case["term"] is None:
                if measured["status"] != "refused_empty" or measured["native_calls"] != 0:
                    errors.append(f"empty pool was not preserved as refusal: {key}/{budget}")
                stats["refused_empty"] += 1
                continue
            expected_predictions = []
            for row in rows[:budget]:
                value = evaluate(case["term"], row["env"])
                expected_predictions.append({"name": row["name"], "native_prediction": value,
                                             "answer": float(row["answer"])})
            if measured["predictions"] != expected_predictions: errors.append(f"native/Python prediction or log mismatch: {key}/{budget}")
            should_accept = all(abs(row["native_prediction"] - row["answer"]) <= 1e-9 for row in expected_predictions)
            expected_status = "accepted" if should_accept else "rejected"
            if measured["status"] != expected_status: errors.append(f"gate status mismatch: {key}/{budget}")
            if measured["native_calls"] != budget: errors.append(f"wrong audit call count: {key}/{budget}")
            stats[expected_status] += 1
            stats["native_calls"] += budget
            stats["wall_seconds"] += measured["wall_seconds"]
            if should_accept and not model_correct_on_panel: stats["false_accept"] += 1
            if not should_accept and model_correct_on_panel: stats["false_refusal"] += 1
    analysis = {"schema": "SubstrateContractQueryIndependentAdequacyGateV1Analysis",
                "cases": len(cases), "error_count": len(errors), "errors": errors,
                "task_budget_summary": {task: {budget: values for budget, values in budgets.items()}
                                        for task, budgets in summary.items()},
                "interpretation": "Finite-panel post-selection validation costs one native Term evaluation per audit row; observed error rates are control-panel counts, not natural-task prevalence."}
    OUT.write_text(json.dumps(analysis, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"analysis": str(OUT.relative_to(ROOT)), "cases": len(cases), "errors": len(errors), "checks_pass": not errors}, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__": raise SystemExit(main())
