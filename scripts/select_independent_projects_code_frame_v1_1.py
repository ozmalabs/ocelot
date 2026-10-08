#!/usr/bin/env python3
"""Outcome-blind diverse-project function selector for licensed Python sources."""
from __future__ import annotations
import ast, hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "data/independent_python_projects_v1_1"
PROJECT_PREFIX = b"ocelot-independent-project-v1\0"
FRAME = ROOT / "evaluation/substrate_capability/independent_projects_code_panel_v1_1_frame_20260928.json"
FUNCTION_PREFIX = b"ocelot-independent-function-v1\0"
INPUTS = [-3, -1, 0, 1, 2, 3, 7, 16, 64]
PAIRS = [(-3,-1),(-1,-3),(0,1),(1,0),(2,3),(3,2),(7,16),(16,7),(64,3)]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def docless(body):
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
        return body[1:]
    return body


def required_positional(fn):
    args = fn.args
    return (not args.posonlyargs and not args.kwonlyargs and not args.vararg and not args.kwarg
            and not args.defaults and not any(x is not None for x in args.kw_defaults)
            and bool(args.args))


def module_index(tree):
    functions = {}
    duplicate_functions = set()
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            if node.name in functions:
                duplicate_functions.add(node.name)
            functions[node.name] = node
    counts = {}
    bad = set()
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name) and isinstance(node.value, ast.Constant) and type(node.value.value) is int:
            counts.setdefault(node.targets[0].id, []).append(node.value.value)
            continue
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and isinstance(node.value, ast.Constant) and type(node.value.value) is int:
            counts.setdefault(node.target.id, []).append(node.value.value)
            continue
        for child in ast.walk(node):
            if isinstance(child, ast.Name) and isinstance(child.ctx, (ast.Store, ast.Del)):
                bad.add(child.id)
            elif isinstance(child, ast.alias):
                bad.add(child.asname or child.name.split('.', 1)[0])
    constants = {name: values[0] for name, values in counts.items() if len(values) == 1 and name not in bad}
    ambiguous = set(counts) - set(constants) | bad
    return functions, duplicate_functions, constants, ambiguous


def inspect_expression(expr, env_names, functions, duplicate_functions, constants, ambiguous, stack, depth):
    if isinstance(expr, ast.Constant):
        return (type(expr.value) is int, False)
    if isinstance(expr, ast.Name):
        name = expr.id
        if name in env_names:
            return True, False
        if name in constants and name not in ambiguous:
            return True, False
        return False, False
    if isinstance(expr, ast.BinOp) and type(expr.op) in (ast.Add, ast.Sub, ast.Mult, ast.BitAnd, ast.BitOr, ast.BitXor):
        a, ba = inspect_expression(expr.left, env_names, functions, duplicate_functions, constants, ambiguous, stack, depth)
        b, bb = inspect_expression(expr.right, env_names, functions, duplicate_functions, constants, ambiguous, stack, depth)
        return a and b, True
    if isinstance(expr, ast.UnaryOp) and type(expr.op) in (ast.USub, ast.Not):
        return inspect_expression(expr.operand, env_names, functions, duplicate_functions, constants, ambiguous, stack, depth)
    if isinstance(expr, ast.Compare) and len(expr.ops) == 1 and len(expr.comparators) == 1 and type(expr.ops[0]) in (ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE):
        a, ba = inspect_expression(expr.left, env_names, functions, duplicate_functions, constants, ambiguous, stack, depth)
        b, bb = inspect_expression(expr.comparators[0], env_names, functions, duplicate_functions, constants, ambiguous, stack, depth)
        return a and b, True
    if isinstance(expr, ast.Call) and isinstance(expr.func, ast.Name) and not expr.keywords:
        name = expr.func.id
        fn = functions.get(name)
        if fn is None or name in duplicate_functions or name in stack or depth >= 4:
            return False, False
        if fn.decorator_list or not required_positional(fn) or len(expr.args) != len(fn.args.args):
            return False, False
        body = docless(fn.body)
        if len(body) != 1 or not isinstance(body[0], ast.Return) or body[0].value is None:
            return False, False
        ok_args = True
        bit_args = False
        for arg in expr.args:
            ok, bit = inspect_expression(arg, env_names, functions, duplicate_functions, constants, ambiguous, stack, depth)
            ok_args &= ok
            bit_args |= bit
        helper_env = {x.arg for x in fn.args.args}
        helper_ok, helper_bit = inspect_expression(body[0].value, helper_env, functions, duplicate_functions, constants, ambiguous, stack | {name}, depth + 1)
        return ok_args and helper_ok, bit_args or helper_bit
    return False, False


def candidate_functions(project, filename, data, text):
    tree = ast.parse(text, filename=filename)
    functions, duplicates, constants, ambiguous = module_index(tree)
    out = []
    for fn in tree.body:
        if not isinstance(fn, ast.FunctionDef) or fn.name in duplicates or fn.decorator_list:
            continue
        if not required_positional(fn) or len(fn.args.args) not in (1, 2):
            continue
        body = docless(fn.body)
        if len(body) != 1 or not isinstance(body[0], ast.Return) or body[0].value is None:
            continue
        ok, has_bitwise = inspect_expression(body[0].value, {arg.arg for arg in fn.args.args}, functions, duplicates, constants, ambiguous, set(), 0)
        if not ok or not has_bitwise:
            continue
        segment = ast.get_source_segment(text, fn)
        if not segment:
            continue
        out.append({"project": project, "file": filename, "function": fn.name, "line": fn.lineno,
                    "arguments": [arg.arg for arg in fn.args.args], "module_sha256": sha(data),
                    "function_sha256": sha(segment.encode("utf-8")),
                    "input_cases": ([{fn.args.args[0].arg: v} for v in INPUTS] if len(fn.args.args) == 1 else [{fn.args.args[0].arg: pair[0], fn.args.args[1].arg: pair[1]} for pair in PAIRS])})
    return out


def build_frame():
    manifest_path = SNAPSHOT / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    files = []
    all_candidates = []
    for project in sorted(manifest["projects"], key=lambda x: x["normalized_name"]):
        root = SNAPSHOT / project["normalized_name"] / "source"
        for path in sorted(root.rglob("*.py")):
            data = path.read_bytes()
            rel = path.relative_to(root).as_posix()
            file_key = project["normalized_name"] + "/" + rel
            files.append({"project": project["normalized_name"], "path": rel, "sha256": sha(data)})
            all_candidates.extend(candidate_functions(project["normalized_name"], rel, data, data.decode("utf-8")))
    all_candidates.sort(key=lambda row: (sha(FUNCTION_PREFIX + row["project"].encode() + b"\0" + row["file"].encode() + b"\0" + row["function"].encode() + b"\0" + str(row["line"]).encode()), row["project"], row["file"], row["function"], row["line"]))
    representatives = {}
    for row in all_candidates:
        representatives.setdefault(row["project"], row)
    project_rows = sorted(representatives.values(), key=lambda row: (sha(PROJECT_PREFIX + row["project"].encode()), row["project"]))
    return {"schema": "independent-projects-code-frame-v1.1", "snapshot_manifest_sha256": sha(manifest_path.read_bytes()),
            "project_inventory": [{"name":p["name"],"normalized_name":p["normalized_name"],"version":p["version"],"license_id":p["license_id"],"python_file_count":p["python_file_count"],"license_file_count":p["license_file_count"]} for p in manifest["projects"]],
            "files": files, "eligible_project_count": len(manifest["projects"]),
            "projects_with_eligible_functions": len(representatives), "eligible_function_count": len(all_candidates),
            "eligible_functions": all_candidates, "project_representatives": project_rows,
            "selected": project_rows[:24], "selected_project_count": min(24,len(project_rows))}


if __name__ == "__main__":
    FRAME.parent.mkdir(parents=True, exist_ok=True)
    frame = build_frame()
    FRAME.write_text(json.dumps(frame, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"frame": FRAME.relative_to(ROOT).as_posix(),
                      "file_count": len(frame["files"]),
                      "eligible_project_count": frame["eligible_project_count"],
                      "projects_with_eligible_functions": frame["projects_with_eligible_functions"],
                      "eligible_function_count": frame["eligible_function_count"],
                      "selected_project_count": frame["selected_project_count"]}, indent=2))
