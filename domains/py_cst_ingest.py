"""py_cst_ingest — the Python twin of `ts_ingest`: a LOSSLESS CstNode graph.

`ts_ingest.ingest_source` already gives Rust/Lua a concrete-syntax graph:
every CST node is a `CstNode`, leaves carry their exact `text`, and
`TableWalker.flat_text(root)` reconstructs the source. Python had only the
semantic `ast_to_term.ingest_ast` overlay, which cannot recreate comments,
blank lines or trailing whitespace.

This module fills that gap with the same `CstNode` contract. Python's
`tokenize` gives the lossless leaves; the gaps between tokens are explicit
`trivia` leaves. The root is a `module` node whose children are those leaves in
document order, so `flat_text` is byte-for-byte the original source.

This is a WORLD ADAPTER (mechanical translation only, CLAUDE.md): it parses an
opaque external form (Python source) into graph nodes. It makes no decisions.

Semantic targets remain the `AstNode` graph (`ast_to_term.ingest_ast`), which
now carries `lineno`/`col_offset`/`end_lineno`/`end_col_offset` so a later edit
can map an AST node onto its CST leaf range. The `CstNode` graph is the byte
owner; the `AstNode` graph is the addressing layer.
"""
from __future__ import annotations

import io
import tokenize
from typing import Any

from domains.ts_ingest import open_cst_productions


def _line_offsets(source: str) -> list[int]:
    offsets = [0]
    for i, ch in enumerate(source):
        if ch == "\n":
            offsets.append(i + 1)
    return offsets


def _offset(offsets: list[int], lineno: int, col: int, n: int) -> int:
    if lineno - 1 >= len(offsets):
        return n
    return offsets[max(0, lineno - 1)] + max(0, col)


def python_cst_leaves(source: str) -> list[dict[str, Any]]:
    """Token + trivia leaves in document order. Rendering the `text` fields in
    order is the original source, byte for byte."""
    offsets = _line_offsets(source)
    leaves: list[dict[str, Any]] = []
    prev_end = 0
    try:
        tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
    except (tokenize.TokenError, IndentationError) as e:
        raise ValueError(f"cannot tokenize Python source: {e}") from e
    for tok in tokens:
        start = _offset(offsets, tok.start[0], tok.start[1], len(source))
        end = _offset(offsets, tok.end[0], tok.end[1], len(source))
        if start > prev_end:
            leaves.append({
                "kind": "trivia", "text": source[prev_end:start],
                "start": prev_end, "end": start,
                "line": tok.start[0], "col": tok.start[1],
                "named": False, "field": "", "child_index": len(leaves),
            })
        text = source[start:end]
        if text:
            leaves.append({
                "kind": tokenize.tok_name[tok.type],
                "text": text, "start": start, "end": end,
                "line": tok.start[0], "col": tok.start[1],
                "named": tok.type not in (tokenize.NL, tokenize.NEWLINE,
                                          tokenize.INDENT, tokenize.DEDENT,
                                          tokenize.ENDMARKER),
                "field": "", "child_index": len(leaves),
            })
        prev_end = max(prev_end, end)
    if prev_end < len(source):
        leaves.append({
            "kind": "trivia", "text": source[prev_end:],
            "start": prev_end, "end": len(source),
            "line": source.count("\n", 0, prev_end) + 1,
            "col": 0, "named": False, "field": "",
            "child_index": len(leaves),
        })
    return leaves


def flat_text(leaves: list[dict[str, Any]]) -> str:
    return "".join(str(leaf.get("text", "")) for leaf in leaves)


def ingest_source(substrate, source: str, *, root_label: str = "") -> dict[str, Any]:
    """Ingest Python source as a lossless `CstNode` graph under `child` edges.

    Returns {"root": NodeID, "n_nodes": int, "language": "python"}.
    """
    leaves = python_cst_leaves(source)
    open_cst_productions(substrate)
    inner = getattr(substrate, "_inner", substrate)
    attrs: dict[str, Any] = {
        "kind": "module", "field": "", "child_index": -1,
        "named": True, "origin": "world_adapter_py_cst", "language": "python",
    }
    if root_label:
        attrs["module"] = root_label
    root = substrate.add_node("CstNode", attrs)
    for leaf in leaves:
        attrs = {
            "kind": leaf["kind"],
            "field": "",
            "child_index": leaf["child_index"],
            "named": bool(leaf["named"]),
            "text": leaf["text"],
            "start": leaf["start"],
            "end": leaf["end"],
            "line": leaf["line"],
            "col": leaf["col"],
            "origin": "world_adapter_py_cst",
            "language": "python",
        }
        if root_label:
            attrs["module"] = root_label
        nid = substrate.add_node("CstNode", attrs)
        try:
            inner.add_edge_unchecked(root, "child", nid)
        except AttributeError:
            substrate.add_edge(root, "child", nid)
    return {"root": root, "n_nodes": len(leaves) + 1, "language": "python"}
