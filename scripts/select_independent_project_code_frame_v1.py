#!/usr/bin/env python3
"""Outcome-blind function selector for an independent licensed Python project."""
from __future__ import annotations
import ast, hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "data/independent_python_project_v1/source"
PROJECT = ROOT / "data/independent_python_project_v1"
FRAME = ROOT / "evaluation/substrate_capability/independent_project_code_panel_v1_frame_20260928.json"
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


def candidate_functions(filename, data, text):
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
        out.append({"file": filename, "function": fn.name, "line": fn.lineno,
                    "arguments": [arg.arg for arg in fn.args.args], "module_sha256": sha(data),
                    "function_sha256": sha(segment.encode("utf-8")),
                    "input_cases": ([{fn.args.args[0].arg: v} for v in INPUTS] if len(fn.args.args) == 1 else [{fn.args.args[0].arg: pair[0], fn.args.args[1].arg: pair[1]} for pair in PAIRS])})
    return out


def build_frame():
    manifest = json.loads((PROJECT / "manifest.json").read_text(encoding="utf-8"))
    files = sorted(CORPUS.rglob("*.py"))
    all_candidates = []
    file_inventory = []
    for path in files:
        data = path.read_bytes()
        rel = path.relative_to(CORPUS).as_posix()
        file_inventory.append({"path": rel, "sha256": sha(data)})
        rows = candidate_functions(rel, data, data.decode("utf-8"))
        all_candidates.extend(rows)
    all_candidates.sort(key=lambda row: (sha(FUNCTION_PREFIX + row["file"].encode() + b"\0" + row["function"].encode() + b"\0" + str(row["line"]).encode()), row["file"], row["function"], row["line"]))
    return {"schema": "independent-project-code-frame-v1", "project": manifest["selected_distribution"],
            "project_snapshot_manifest_sha256": sha((PROJECT / "manifest.json").read_bytes()),
            "files": file_inventory, "eligible_function_count": len(all_candidates),
            "eligible_functions": all_candidates, "selected": all_candidates[:24],
            "selected_function_count": min(24, len(all_candidates))}


if __name__ == "__main__":
    FRAME.parent.mkdir(parents=True, exist_ok=True)
    frame = build_frame()
    FRAME.write_text(json.dumps(frame, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"frame": FRAME.relative_to(ROOT).as_posix(),
                      "file_count": len(frame["files"]),
                      "eligible_function_count": frame["eligible_function_count"],
                      "selected_function_count": frame["selected_function_count"]}, indent=2))
