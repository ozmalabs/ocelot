#!/usr/bin/env python3
"""Independent candidate reconstruction, safe oracle and scorer."""
from __future__ import annotations
import ast, hashlib, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/python_stdlib_3_13_5/stat.py"
TPDATA = ROOT / "data/think_python_2e"
FRAME = ROOT / "evaluation/reports/stdlib_stat_prediction_frame_v1_20260927.json"
RAW = ROOT / "evaluation/reports/stdlib_stat_prediction_panel_v1_1_20260927.json"
BASE_RAW = ROOT / "evaluation/reports/stdlib_stat_prediction_panel_v1_20260927.json"
BASE_ANALYSIS = ROOT / "evaluation/reports/stdlib_stat_prediction_panel_v1_analysis_20260927.json"
BASE_FRAME = ROOT / "evaluation/reports/stdlib_stat_prediction_frame_v1_20260927.json"
BASE_LOCK = ROOT / "evaluation/substrate_capability/stdlib_stat_prediction_panel_v1_lock_20260927.json"
BASE_HASHES = {"raw": "0a45d7f3df52630995ca62ed7f3fafe3c419a5983f7f888c26baaf288a77da98",
               "analysis": "1b9b71713dd905056a1c0282e72409d4e823e5b8c0f3d567115fd3b0162a4589",
               "frame": "d1538bb1dec48de2ef8d89252f1afd4f9e8159a0e9768688b29945b1ac5d8bc0",
               "lock": "446445c9fbefe80a9b0137fbd167e23344a4280b5151786bf189148de46ac03c"}
V2_RAW = ROOT / "evaluation/reports/stacks_string_prediction_panel_v2_20260927.json"
V2_ANALYSIS = ROOT / "evaluation/reports/stacks_string_prediction_panel_v2_analysis_20260927.json"
V2_FRAME = ROOT / "evaluation/reports/stacks_string_prediction_frame_v2_20260927.json"
V2_HASHES = {"raw": "abe5421e4c67a25372ba67b3330a4af8b8a2119d0416b9e55df6305e0ebba1d9",
             "analysis": "f374eeaa12b8050ab4eb041ab0b845741badc5335182a530b1b5d42d4f13e93e",
             "frame": "5a0f2b31d30835ab44e664dc61a238ee5d76b32b5370b0750e66f394edbb8927"}
BLOCK = re.compile(r"```(?:python)?\s*\n(.*?)\n```", re.S | re.I)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def _body_without_docstring(fn):
    body = fn.body
    if (body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)):
        return body[1:]
    return body


def independently_reconstruct_candidates():
    data = SOURCE.read_bytes()
    text = data.decode("utf-8")
    module = ast.parse(text)
    constants, functions = {}, {}
    for item in module.body:
        if isinstance(item, ast.Assign) and len(item.targets) == 1:
            if (isinstance(item.targets[0], ast.Name) and isinstance(item.value, ast.Constant)
                    and type(item.value.value) is int):
                constants[item.targets[0].id] = item.value.value
        elif isinstance(item, ast.FunctionDef):
            functions[item.name] = item
    mask_fn = functions["S_IFMT"]
    mask_body = _body_without_docstring(mask_fn)
    mask_value = mask_body[0].value
    if not (len(mask_body) == 1 and isinstance(mask_body[0], ast.Return)
            and isinstance(mask_value, ast.BinOp) and isinstance(mask_value.op, ast.BitAnd)
            and isinstance(mask_value.left, ast.Name) and mask_value.left.id == "mode"
            and isinstance(mask_value.right, ast.Constant) and type(mask_value.right.value) is int):
        raise ValueError("independent oracle rejected S_IFMT implementation")
    mask = mask_value.right.value
    result = []
    for fn in functions.values():
        body = _body_without_docstring(fn)
        if len(fn.args.args) != 1 or fn.args.vararg or fn.args.kwarg or fn.args.kwonlyargs:
            continue
        if len(body) != 1 or not isinstance(body[0], ast.Return):
            continue
        expr = body[0].value
        if not (isinstance(expr, ast.Compare) and len(expr.ops) == 1 and isinstance(expr.ops[0], ast.Eq)
                and len(expr.comparators) == 1 and isinstance(expr.left, ast.Call)
                and isinstance(expr.left.func, ast.Name) and expr.left.func.id == "S_IFMT"
                and len(expr.left.args) == 1 and not expr.left.keywords
                and isinstance(expr.left.args[0], ast.Name) and expr.left.args[0].id == fn.args.args[0].arg
                and isinstance(expr.comparators[0], ast.Name)):
            continue
        kname = expr.comparators[0].id
        if kname not in constants:
            continue
        fn_src = ast.get_source_segment(text, fn)
        result.append({"file": SOURCE.relative_to(ROOT).as_posix(), "module_sha256": sha(data),
                       "function": fn.name, "line": fn.lineno, "argument": fn.args.args[0].arg,
                       "function_sha256": sha(fn_src.encode()), "type_constant": kname,
                       "type_value": constants[kname], "type_mask": mask})
    result.sort(key=lambda x: x["function"])
    vals = [x["type_value"] for x in result]
    for i, row in enumerate(result):
        k = row["type_value"]
        other = vals[(i + 1) % len(vals)]
        row["input_cases"] = [{row["argument"]: mode} for mode in (0, k, k | 0o755, other | 0o640, 0o7777)]
    return result


def reconstruct_control():
    frame = json.loads(V2_FRAME.read_text(encoding="utf-8"))
    return frame["positive_control"]


class ReturnValue(Exception):
    def __init__(self, value):
        self.value = value


def control_oracle(source, function, args):
    module = ast.parse(source)
    fn = next(node for node in module.body if isinstance(node, ast.FunctionDef) and node.name == function)
    env = dict(args)

    def evaluate(node):
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Name):
            return env[node.id]
        if isinstance(node, ast.BinOp) and type(node.op) is ast.Mod:
            return evaluate(node.left) % evaluate(node.right)
        if isinstance(node, ast.Compare) and len(node.ops) == 1:
            left, right = evaluate(node.left), evaluate(node.comparators[0])
            if type(node.ops[0]) is ast.Eq:
                return left == right
            if type(node.ops[0]) is ast.Lt:
                return left < right
        raise TypeError("positive-control oracle rejected AST node " + type(node).__name__)

    for statement in fn.body:
        if (isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Constant)
                and isinstance(statement.value.value, str)):
            continue
        if isinstance(statement, ast.Return):
            raise ReturnValue(evaluate(statement.value))
        raise TypeError("positive-control oracle rejected statement " + type(statement).__name__)
    return None


def exact_schedule(run, tasks):
    calls = run.get("calls", [])
    if len(calls) != len(tasks):
        return False
    for call, (corpus, fi, ci, row, source, expected_file_hash) in zip(calls, tasks):
        fn_sha = row.get("function_sha256", row.get("source_sha256"))
        module_sha = row.get("module_sha256", row.get("file_sha256"))
        if (call["corpus"], call["function_index"], call["case_index"], call["function_sha256_expected"],
            call["module_sha256_expected"], call["source_sha256_observed"], call["args"]) != (
                corpus, fi, ci, fn_sha, module_sha, sha(source.encode("utf-8")), row["input_cases"][ci]):
            return False
        if expected_file_hash != module_sha:
            return False
    return True


def main():
    selected = independently_reconstruct_candidates()
    control = reconstruct_control()
    frame = json.loads(FRAME.read_text(encoding="utf-8"))
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    base_raw = json.loads(BASE_RAW.read_text(encoding="utf-8"))
    base_analysis = json.loads(BASE_ANALYSIS.read_text(encoding="utf-8"))
    base_frame = json.loads(BASE_FRAME.read_text(encoding="utf-8"))
    base_lock = json.loads(BASE_LOCK.read_text(encoding="utf-8"))
    runs, manifest = raw.get("runs", []), raw.get("run_manifest", {})
    capture = manifest.get("stdout_stderr_capture") or {}
    log_path = ROOT / capture.get("path", "__missing__")
    log = log_path.read_bytes() if log_path.is_file() else b""
    ref_hashes = {"raw": sha(V2_RAW.read_bytes()), "analysis": sha(V2_ANALYSIS.read_bytes()), "frame": sha(V2_FRAME.read_bytes())}
    ref_raw, ref_analysis = json.loads(V2_RAW.read_text()), json.loads(V2_ANALYSIS.read_text())
    base_hashes = {"raw": sha(BASE_RAW.read_bytes()), "analysis": sha(BASE_ANALYSIS.read_bytes()),
                   "frame": sha(BASE_FRAME.read_bytes()), "lock": sha(BASE_LOCK.read_bytes())}
    runtime_groups = ("domains", "substrate", "worlds", "seeds", "native_python", "rust")
    runtime_diffs = sorted(
        path
        for group in runtime_groups
        for path in set(base_raw["locked_inputs"]["source_trees"][group])
                    | set(raw["locked_inputs"]["source_trees"][group])
        if base_raw["locked_inputs"]["source_trees"][group].get(path)
        != raw["locked_inputs"]["source_trees"][group].get(path))
    tasks, oracle_errors = [], []
    all_rows = [("stat", row) for row in selected] + [("positive_control", control)]
    for fi, (corpus, row) in enumerate(all_rows):
        if corpus == "stat":
            source = SOURCE.read_text(encoding="utf-8")
            for ci, args in enumerate(row["input_cases"]):
                expected = {"type": "bool", "value": (args[row["argument"]] & row["type_mask"]) == row["type_value"]}
                tasks.append((corpus, fi, ci, row, source, row["module_sha256"], expected, None))
        else:
            source = list(BLOCK.finditer((TPDATA / row["chapter"]).read_text(encoding="utf-8")))[row["block_index"]].group(1)
            for ci, args in enumerate(row["input_cases"]):
                try:
                    try:
                        value = control_oracle(source, row["function"], args)
                    except ReturnValue as result:
                        value = result.value
                    tasks.append((corpus, fi, ci, row, source, row["file_sha256"],
                                  {"type": type(value).__name__, "value": value}, None))
                except Exception as exc:
                    tasks.append((corpus, fi, ci, row, source, row["file_sha256"], None, type(exc).__name__))
                    oracle_errors.append(type(exc).__name__)

    checks = {
        "seven_ast_selected_file_predicates": len(selected) == 7 and [x["function"] for x in selected] == ["S_ISBLK", "S_ISCHR", "S_ISDIR", "S_ISFIFO", "S_ISLNK", "S_ISREG", "S_ISSOCK"],
        "independent_frame_reconstruction": frame.get("selected") == selected and frame.get("candidate_count") == len(selected) and frame.get("positive_control") == control,
        "thirty_five_primary_and_two_control_cases": len(tasks) == 37 and sum(t[0] == "stat" for t in tasks) == 35 and sum(t[0] == "positive_control" for t in tasks) == 2,
        "oracle_error_free": not oracle_errors,
        "two_fresh_workers": len(runs) == 2 and len({r.get("pid") for r in runs}) == 2,
        "source_locks_stable": raw.get("post_run_inputs") == raw.get("locked_inputs") and all(r.get("source_stable") and r.get("locked_inputs_before") == raw.get("locked_inputs") == r.get("locked_inputs_after") for r in runs),
        "complete_worker_schedule": all(len(r.get("calls", [])) == len(tasks) for r in runs),
        "source_and_case_hashes_exact": all(exact_schedule(run, [(t[0], t[1], t[2], t[3], t[4], t[5]) for t in tasks]) for run in runs),
        "shared_manifest_console_valid": manifest.get("manifest_schema") == "substrate-run-manifest-v1" and manifest.get("exit_status") == 0 and bool(log) and len(log) == capture.get("bytes") and sha(log) == capture.get("sha256") and all(f"completed=worker{i} rc=0".encode() in log for i in (0, 1)),
        "frozen_control_reference_valid": ref_hashes == V2_HASHES and ref_raw.get("integrity_pass") and ref_analysis.get("pass"),
        "frozen_v1_baseline_valid": base_hashes == BASE_HASHES and base_raw.get("integrity_pass")
            and base_analysis.get("pass") and base_lock.get("locked_inputs") == base_raw.get("locked_inputs")
            and all(w.get("primary_exact_correct") == 0 and w.get("primary_predictions") == 0
                    and w.get("positive_control_correct") == 2
                    for w in base_analysis.get("summary", {}).get("workers", [])),
        "candidate_locks_frozen_v1_artifacts": raw.get("locked_inputs", {}).get("baseline_v1_artifacts") == BASE_HASHES,
        "same_frozen_task_frame": frame == base_frame and frame.get("selected") == selected
            and frame.get("positive_control") == control,
        "runtime_source_delta_matches_amendment": runtime_diffs == ["domains/ast_to_term.py", "domains/code_reading.py", "domains/comprehend_text.py", "substrate/boot_all.py"]
            and raw["locked_inputs"]["native_extension_sha256"] == base_raw["locked_inputs"]["native_extension_sha256"],
        "corpus_source_and_control_inputs_frozen": raw["locked_inputs"]["source_trees"]["stdlib_stat_corpus"].get("data/python_stdlib_3_13_5/stat.py") == "f76eaa7f02d6ef4a8c3c3e82cae34ed72870b643b8c94937a34c697d1e9d6ca2"
            and raw["locked_inputs"]["source_trees"]["think_python_control"] == base_raw["locked_inputs"]["source_trees"]["think_python_control"],
        "workers_succeeded": all(r.get("worker_returncode") == 0 and r.get("boot", {}).get("loaded", 0) > 0 for r in runs),
    }
    summaries = []
    for run in runs:
        by_case = {(call["function_index"], call["case_index"]): call for call in run.get("calls", [])}
        scored = []
        for task in tasks:
            corpus, fi, ci, row, _source, _file_hash, expected, oracle_error = task
            call = by_case[(fi, ci)]
            correct = oracle_error is None and not call["abstained"] and call["prediction"] == expected
            scored.append({"corpus": corpus, "function": row["function"], "case_index": ci,
                           "expected": expected, "prediction": call["prediction"], "abstained": call["abstained"],
                           "error_type": call["error_type"], "correct": correct, "oracle_error": oracle_error,
                           "wall_ns": call["wall_ns"], "cpu_ns": call["cpu_ns"],
                           "receipt_delta": call["receipt_delta"],
                           "minted_observation_count": sum(bool(o["minted_axis_ids"]) for o in call["new_observations"])})
        primary = [x for x in scored if x["corpus"] == "stat"]
        controls = [x for x in scored if x["corpus"] == "positive_control"]
        predicted = [x for x in primary if not x["abstained"]]
        timing = sorted(c["wall_ns"] for c in run["calls"])
        cpu_timing = sorted(c["cpu_ns"] for c in run["calls"])
        summaries.append({"replicate": run.get("replicate"), "primary_cases": len(primary),
                          "primary_exact_correct": sum(x["correct"] for x in primary),
                          "primary_predictions": len(predicted), "primary_abstentions": len(primary) - len(predicted),
                          "primary_wrong_returns": sum(not x["abstained"] and not x["correct"] for x in primary),
                          "positive_control_correct": sum(x["correct"] for x in controls),
                          "receipt_count": sum(c["receipt_delta"] for c in run["calls"]),
                          "minted_observation_count": sum(sum(bool(o["minted_axis_ids"]) for o in c["new_observations"]) for c in run["calls"]),
                          "median_wall_ns": timing[len(timing) // 2], "p95_wall_ns": timing[int(.95 * len(timing))],
                          "median_cpu_ns": cpu_timing[len(cpu_timing) // 2],
                          "p95_cpu_ns": cpu_timing[int(.95 * len(cpu_timing))],
                          "boot_loaded": run["boot"]["loaded"], "boot_total": run["boot"]["total"],
                          "boot_failures": len(run["boot"]["failed"]), "peak_rss_bytes": run["runtime"]["peak_rss_bytes"],
                          "case_results": scored})
    checks["worker_outcome_parity"] = len(summaries) == 2 and [(x["prediction"], x["error_type"]) for x in summaries[0]["case_results"]] == [(x["prediction"], x["error_type"]) for x in summaries[1]["case_results"]]
    checks["positive_controls_pass"] = all(x["positive_control_correct"] == 2 for x in summaries)
    checks["candidate_exact_35_of_35"] = all(x["primary_exact_correct"] == 35 and x["primary_predictions"] == 35 for x in summaries)
    checks["no_wrong_candidate_outputs"] = all(x["primary_wrong_returns"] == 0 for x in summaries)
    result = {"checks": checks, "pass": all(checks.values()),
              "summary": {"candidate_count": len(selected), "primary_case_count": 35,
                          "positive_control_case_count": 2, "oracle_errors": oracle_errors,
                          "frozen_v1_artifact_hashes": base_hashes,
                          "candidate_runtime_source_diffs_from_v1": runtime_diffs,
                          "source_reference_hashes": ref_hashes,
                          "claim_boundary": raw.get("claim_boundary"), "workers": summaries}}
    print(json.dumps(result, indent=2, sort_keys=True))
    if not result["pass"]:
        raise SystemExit("CPython stat prediction analysis failed")


if __name__ == "__main__":
    main()
