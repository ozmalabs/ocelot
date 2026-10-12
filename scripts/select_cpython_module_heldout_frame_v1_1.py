#!/usr/bin/env python3
"""Outcome-blind hash selector for CPython 3.13.5 held-out module panel v1."""
from __future__ import annotations
import ast, hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORPUS = ROOT / "data/cpython_lib_3_13_5"
FRAME = ROOT / "evaluation/substrate_capability/code_module_heldout_panel_v1_1_frame_20260928.json"
MODULE_PREFIX = b"CPython3.13.5-module-heldout-v1\0"
FUNCTION_PREFIX = b"CPython3.13.5-function-heldout-v1\0"
INPUTS = [-1, 0, 1, 63, 64, 65, 127, 128, 255]


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
    if isinstance(expr, ast.BinOp) and type(expr.op) in (ast.BitAnd, ast.BitOr, ast.BitXor):
        a, ba = inspect_expression(expr.left, env_names, functions, duplicate_functions, constants, ambiguous, stack, depth)
        b, bb = inspect_expression(expr.right, env_names, functions, duplicate_functions, constants, ambiguous, stack, depth)
        return a and b, ba or bb or True
    if isinstance(expr, ast.UnaryOp) and type(expr.op) in (ast.USub, ast.Not):
        return inspect_expression(expr.operand, env_names, functions, duplicate_functions, constants, ambiguous, stack, depth)
    if isinstance(expr, ast.Compare) and len(expr.ops) == 1 and len(expr.comparators) == 1 and type(expr.ops[0]) in (ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE):
        a, ba = inspect_expression(expr.left, env_names, functions, duplicate_functions, constants, ambiguous, stack, depth)
        b, bb = inspect_expression(expr.comparators[0], env_names, functions, duplicate_functions, constants, ambiguous, stack, depth)
        return a and b, ba or bb
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
                    "input_cases": ([{fn.args.args[0].arg: v} for v in INPUTS] if len(fn.args.args) == 1 else [{fn.args.args[0].arg: pair[0], fn.args.args[1].arg: pair[1]} for pair in [(-1,0),(0,-1),(0,1),(1,0),(63,64),(64,63),(64,65),(65,64),(255,128)]])})
    return out


def build_frame():
    files = sorted(CORPUS.glob("*.py"))
    inventory = [{"name": p.name, "sha256": sha(p.read_bytes())} for p in files]
    eligible = [p for p in files if p.name != "stat.py" and not p.name.startswith("__")]
    ranked = sorted(eligible, key=lambda p: (sha(MODULE_PREFIX + p.name.encode()), p.name))[:153]
    selected_modules = []
    candidates = []
    for path in ranked:
        data = path.read_bytes()
        text = data.decode("utf-8")
        rows = candidate_functions(path.name, data, text)
        selected_modules.append({"name": path.name, "sha256": sha(data), "eligible_function_count": len(rows)})
        candidates.extend(rows)
    candidates.sort(key=lambda row: (sha(FUNCTION_PREFIX + row["file"].encode() + b"\0" + row["function"].encode() + b"\0" + str(row["line"]).encode()), row["file"], row["function"], row["line"]))
    return {"schema": "code-module-heldout-frame-v1.1", "corpus": "CPython 3.13.5 top-level Lib Python files; stat.py excluded",
            "corpus_inventory": inventory, "corpus_license_sha256": sha((CORPUS / "LICENSE.txt").read_bytes()),
            "module_sample": selected_modules, "eligible_functions": candidates, "eligible_function_count": len(candidates),
            "selected": candidates[:24], "selected_function_count": min(24, len(candidates))}


if __name__ == "__main__":
    FRAME.parent.mkdir(parents=True, exist_ok=True)
    frame = build_frame()
    FRAME.write_text(json.dumps(frame, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"frame": FRAME.relative_to(ROOT).as_posix(),
                      "module_count": len(frame["module_sample"]),
                      "eligible_function_count": frame["eligible_function_count"],
                      "selected_function_count": frame["selected_function_count"]}, indent=2))
