#!/usr/bin/env python3
"""Outcome-blind AST frame selector for the CPython stat predicate panel."""
import ast
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/python_stdlib_3_13_5/stat.py"
V2_FRAME = ROOT / "evaluation/reports/stacks_string_prediction_frame_v2_20260927.json"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _body_without_docstring(fn):
    body = fn.body
    if (body and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)):
        return body[1:]
    return body


def candidates():
    raw = SOURCE.read_bytes()
    text = raw.decode("utf-8")
    tree = ast.parse(text)
    constants = {}
    functions = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if (isinstance(target, ast.Name) and isinstance(node.value, ast.Constant)
                    and type(node.value.value) is int):
                constants[target.id] = node.value.value
        elif isinstance(node, ast.FunctionDef):
            functions[node.name] = node

    mask_fn = functions.get("S_IFMT")
    if mask_fn is None:
        raise ValueError("S_IFMT helper is absent")
    mask_body = _body_without_docstring(mask_fn)
    if len(mask_body) != 1 or not isinstance(mask_body[0], ast.Return):
        raise ValueError("S_IFMT is outside the preregistered oracle fragment")
    mask_expr = mask_body[0].value
    if not (isinstance(mask_expr, ast.BinOp) and isinstance(mask_expr.op, ast.BitAnd)
            and isinstance(mask_expr.left, ast.Name) and mask_expr.left.id == "mode"
            and isinstance(mask_expr.right, ast.Constant)
            and type(mask_expr.right.value) is int):
        raise ValueError("S_IFMT source does not match the independent oracle contract")
    type_mask = mask_expr.right.value

    rows = []
    for fn in functions.values():
        body = _body_without_docstring(fn)
        if len(fn.args.args) != 1 or fn.args.vararg or fn.args.kwarg or fn.args.kwonlyargs:
            continue
        if len(body) != 1 or not isinstance(body[0], ast.Return):
            continue
        value = body[0].value
        if not (isinstance(value, ast.Compare) and len(value.ops) == 1
                and isinstance(value.ops[0], ast.Eq) and len(value.comparators) == 1
                and isinstance(value.left, ast.Call) and not value.left.keywords
                and len(value.left.args) == 1 and isinstance(value.left.func, ast.Name)
                and value.left.func.id == "S_IFMT"
                and isinstance(value.left.args[0], ast.Name)
                and value.left.args[0].id == fn.args.args[0].arg
                and isinstance(value.comparators[0], ast.Name)):
            continue
        constant_name = value.comparators[0].id
        if constant_name not in constants:
            continue
        segment = ast.get_source_segment(text, fn)
        rows.append({
            "file": SOURCE.relative_to(ROOT).as_posix(),
            "module_sha256": sha(raw),
            "function": fn.name,
            "line": fn.lineno,
            "argument": fn.args.args[0].arg,
            "function_sha256": sha(segment.encode("utf-8")),
            "type_constant": constant_name,
            "type_value": constants[constant_name],
            "type_mask": type_mask,
        })
    rows.sort(key=lambda row: row["function"])
    masks = [row["type_value"] for row in rows]
    for index, row in enumerate(rows):
        k = row["type_value"]
        other = masks[(index + 1) % len(masks)]
        modes = [0, k, k | 0o755, other | 0o640, 0o7777]
        row["input_cases"] = [{row["argument"]: mode} for mode in modes]
    return rows


def positive_control():
    import json
    return json.loads(V2_FRAME.read_text(encoding="utf-8"))["positive_control"]


if __name__ == "__main__":
    print(f"candidates={len(candidates())}")
