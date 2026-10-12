#!/usr/bin/env python3
"""Outcome-blind selector for Think Python function-reading examples.

Only chapter/block identifiers and content hashes are written; the source
book's code examples are not copied into the frame artifact.
"""
from __future__ import annotations
import ast, hashlib, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data/think_python_2e"
OUT = ROOT / "evaluation/reports/thinkpython_code_rung_frame_v1_20260927.json"
BLOCK = re.compile(r"```(?:python)?\s*\n(.*?)\n```", re.S | re.I)

def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def candidates():
    rows = []
    for path in sorted(DATA.glob("ch*.txt")):
        content = path.read_text(encoding="utf-8")
        for block_no, match in enumerate(BLOCK.finditer(content)):
            source = match.group(1)
            try:
                tree = ast.parse(source)
            except SyntaxError:
                continue
            functions = [n.name for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
            if not functions:
                continue
            ident = [path.name, block_no]
            rows.append({"id": ident, "chapter": path.name, "block_index": block_no,
                         "source_sha256": sha(source.encode("utf-8")),
                         "selection_rank": sha(json.dumps(ident, separators=(",", ":")).encode()),
                         "function_count": len(functions), "selected_function": functions[0]})
    return rows

def main():
    rows = sorted(candidates(), key=lambda r: (r["selection_rank"], r["chapter"], r["block_index"]))
    frame = {"schema_version": 1, "source": "Think Python 2e fenced Python examples",
             "selection_rule": "valid Python fenced blocks with at least one top-level function; rank by SHA256(compact JSON [chapter, block_index]); first 64",
             "candidate_count": len(rows), "sample_size": 64, "selected": rows[:64]}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(frame, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"frame": OUT.relative_to(ROOT).as_posix(), "candidate_count": len(rows),
                      "selected": len(frame["selected"]), "frame_sha256": sha(OUT.read_bytes())}, indent=2))

if __name__ == "__main__": main()
