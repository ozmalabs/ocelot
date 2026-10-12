#!/usr/bin/env python3
"""Outcome-blind census selector for the Stacks Project Python helpers."""
from __future__ import annotations
import ast, hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/stacks/repo/scripts"
FILES = sorted(DATA.glob("*.py"))

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def candidates():
    rows = []
    for path in FILES:
        raw = path.read_bytes()
        text = raw.decode("utf-8")
        tree = ast.parse(text, filename=path.name)
        for node in tree.body:
            if isinstance(node, ast.FunctionDef):
                segment = ast.get_source_segment(text, node)
                rows.append({"file": path.relative_to(ROOT).as_posix(),
                             "module_sha256": sha(raw), "line": node.lineno,
                             "function": node.name,
                             "function_sha256": sha(segment.encode("utf-8"))})
    return rows

if __name__ == "__main__":
    rows = candidates()
    print(json.dumps({"schema_version": 1, "corpus": "stacks-project-scripts",
                      "candidate_count": len(rows), "selected": rows},
                     indent=2, sort_keys=True))
