#!/usr/bin/env python3
"""AST inventory of direct induce_concern callers and key-hint forms."""
from __future__ import annotations

import ast
import collections
import hashlib
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROOTS = ("domains", "scripts", "substrate", "worlds", "evaluation", "tests")
OUT = ROOT / "evaluation/reports/induce_concern_key_census_v1.json"
PATTERN = r"induce_concern\("


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def candidates() -> list[str]:
    proc = subprocess.run(
        ["rg", "-l", PATTERN, *ROOTS, "--glob", "*.py"],
        cwd=ROOT, text=True, capture_output=True, check=True,
    )
    return sorted(line for line in proc.stdout.splitlines() if line)


def direct_calls(path: str) -> tuple[list[dict], str | None]:
    full = ROOT / path
    source = full.read_text(errors="replace")
    try:
        tree = ast.parse(source, filename=path)
    except SyntaxError as exc:
        return [], f"{exc.msg} at line {exc.lineno}"

    aliases = {"induce_concern"}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.endswith("reflective_faculty"):
            for alias in node.names:
                if alias.name == "induce_concern":
                    aliases.add(alias.asname or alias.name)

    parents = {child: node for node in ast.walk(tree) for child in ast.iter_child_nodes(node)}
    rows = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        function = node.func
        if isinstance(function, ast.Name) and function.id in aliases:
            call_form = "imported_name"
        elif isinstance(function, ast.Attribute) and function.attr == "induce_concern":
            call_form = "attribute"
        else:
            continue

        kw = next((item.value for item in node.keywords if item.arg == "name_hint"), None)
        if kw is None:
            hint_kind, hint_source = "omitted", None
        elif isinstance(kw, ast.Constant) and isinstance(kw.value, str):
            hint_kind, hint_source = "literal_string", kw.value
        elif isinstance(kw, ast.Constant) and kw.value is None:
            hint_kind, hint_source = "explicit_none", "None"
        else:
            hint_kind, hint_source = "expression", ast.unparse(kw)

        parent = node
        while parent in parents and not isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)):
            parent = parents[parent]
        rows.append({
            "file": path,
            "line": node.lineno,
            "caller": getattr(parent, "name", "<module>"),
            "call_form": call_form,
            "name_hint_kind": hint_kind,
            "name_hint_source": hint_source,
        })
    return rows, None


def main() -> None:
    paths = candidates()
    rows, errors = [], []
    for path in paths:
        found, error = direct_calls(path)
        rows.extend(found)
        if error:
            errors.append({"file": path, "error": error})
    rows.sort(key=lambda row: (row["file"], row["line"]))

    by_root: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    files_by_root: dict[str, set[str]] = collections.defaultdict(set)
    for row in rows:
        root = row["file"].split("/", 1)[0]
        by_root[root][row["name_hint_kind"]] += 1
        files_by_root[root].add(row["file"])
    summary = {
        "candidate_python_files": len(paths),
        "ast_call_sites": len(rows),
        "ast_callsite_files": len({row["file"] for row in rows}),
        "hint_policy_counts": dict(collections.Counter(row["name_hint_kind"] for row in rows)),
        "by_root": {
            root: {"files": len(files_by_root[root]), **dict(by_root[root])}
            for root in sorted(by_root)
        },
        "parse_errors": errors,
    }
    output = {
        "schema_version": 1,
        "git_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                    text=True, capture_output=True,
                                    check=True).stdout.strip(),
        "roots": list(ROOTS),
        "candidate_file_hashes": {path: file_digest(ROOT / path) for path in paths},
        "summary": summary,
        "call_sites": rows,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
