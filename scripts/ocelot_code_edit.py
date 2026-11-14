"""ocelot_code_edit — graph-addressed structural edits for Python source.

THE MODEL. The canonical change is an **edit script**: semantic operations
against a file's definition graph (replace a symbol, replace a function body,
insert an import, rename a symbol, delete a symbol, ...). A unified diff is
only a rendered VIEW for humans. The tool does not accept a raw diff/patch as
input; editing by text-patch is the thing this module exists to replace.

What is graph-addressed here:

  * the target is a `Symbol` node from the repo graph (qualified name), not a
    line range the caller guessed;
  * the operation names the semantic effect (`replace_body`, `insert_import`,
    `rename_symbol`, ...), not "swap these characters";
  * the result records before/after content hashes, the affected graph node,
    and the operation list — a replayable transaction;
  * the diff is emitted at the end, explicitly labelled `diff_view`.

This is still a mechanical host-side applier (per CLAUDE.md): it parses source
into an AST, resolves spans, applies the semantic edit, and writes the result.
The DECISION (which symbol, which operation) belongs to the graph/agent. The
longer-term path is to make the edit algebra itself a set of Rust DSL Terms
over the hub IR (the `Prog*`/`RenderRule` machinery), so the agent can edit the
code graph without a text round-trip at all. This module is the first,
honest step: graph targets in, graph-recorded transaction out.

Python only for v0. Rust/CST editing is deliberately refused rather than
half-done; the Rust path belongs with the existing tree-sitter/hub-IR readers.
"""
from __future__ import annotations

import ast
import difflib
import hashlib
import json
import os
import re
import shutil
import textwrap
import time
import tokenize
from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from typing import Any

MAX_SOURCE_BYTES = 2 * 1024 * 1024
FORBIDDEN_SCRIPT_KEYS = ("diff", "patch", "unified_diff", "hunk")


class CodeEditError(ValueError):
    """A refused edit: bad target, stale base, non-Python file, raw diff, ..."""


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass
class SymbolSpan:
    name: str
    qualname: str
    kind: str
    start: int
    end: int
    start_line: int
    end_line: int
    body_start: int
    body_end: int
    body_indent: str
    indent: str
    node: ast.AST


def _line_offsets(source: str) -> list[int]:
    offsets = [0]
    for i, ch in enumerate(source):
        if ch == "\n":
            offsets.append(i + 1)
    return offsets


def _offset(offsets: list[int], lineno: int, col: int) -> int:
    return offsets[max(0, lineno - 1)] + max(0, col)


def _line_end_offset(offsets: list[int], lineno: int, source_len: int) -> int:
    if lineno < len(offsets):
        return offsets[lineno]
    return source_len


def _indent_at(source: str, offsets: list[int], lineno: int) -> str:
    start = offsets[max(0, lineno - 1)]
    end = source.find("\n", start)
    line = source[start:end if end >= 0 else len(source)]
    return line[:len(line) - len(line.lstrip(" \t"))]


def _decorator_start(node: ast.AST, offsets: list[int], source_len: int) -> int:
    decorators = getattr(node, "decorator_list", None) or []
    if decorators:
        first = decorators[0]
        line = getattr(first, "lineno", getattr(node, "lineno", 1))
        return offsets[max(0, line - 1)]
    return offsets[max(0, getattr(node, "lineno", 1) - 1)]


def symbol_table(source: str) -> dict[str, SymbolSpan]:
    """Every function/class definition in the source, addressed by qualname.

    The span includes leading decorators and the full body. `body_start` is the
    first body statement's line start; `body_end` is the end of the last body
    statement's line. These are the targets a graph edit names.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        raise CodeEditError(f"source does not parse: {e}") from e
    offsets = _line_offsets(source)
    n = len(source)
    out: dict[str, SymbolSpan] = {}

    def walk(body: list[ast.AST], prefix: str = "") -> None:
        for node in body:
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                                     ast.ClassDef)):
                continue
            name = node.name
            qual = f"{prefix}.{name}" if prefix else name
            if isinstance(node, ast.ClassDef):
                kind = "class"
            elif isinstance(node, ast.AsyncFunctionDef):
                kind = "async_function"
            else:
                kind = "function"
            start = _decorator_start(node, offsets, n)
            end_line = int(getattr(node, "end_lineno", node.lineno) or node.lineno)
            end = _line_end_offset(offsets, end_line, n)
            indent = _indent_at(source, offsets, node.lineno)
            body = node.body or []
            if body:
                first = body[0]
                last = body[-1]
                body_start = offsets[max(0, int(getattr(first, "lineno", node.lineno)) - 1)]
                body_end = _line_end_offset(
                    offsets, int(getattr(last, "end_lineno", last.lineno) or last.lineno), n)
                body_indent = _indent_at(source, offsets,
                                         int(getattr(first, "lineno", node.lineno)))
            else:
                body_start = start
                body_end = end
                body_indent = indent + "    "
            out[qual] = SymbolSpan(name, qual, kind, start, end,
                                   int(node.lineno), end_line,
                                   body_start, body_end, body_indent,
                                   indent, node)
            walk(node.body, qual)

    walk(tree.body)
    return out


def _char_col(line: str, byte_col: int) -> int:
    """AST col offsets are UTF-8 byte offsets; convert to a character column."""
    if byte_col <= 0:
        return 0
    raw = line.encode("utf-8")
    return len(raw[:byte_col].decode("utf-8", errors="ignore"))


def _node_span(source: str, offsets: list[int], node: ast.AST) -> tuple[int, int]:
    line = int(getattr(node, "lineno", 1) or 1)
    col = int(getattr(node, "col_offset", 0) or 0)
    end_line = int(getattr(node, "end_lineno", line) or line)
    end_col = int(getattr(node, "end_col_offset", col) or col)
    start_line_text = source[offsets[max(0, line - 1)]:
                              (offsets[line] if line < len(offsets) else len(source))]
    end_line_text = source[offsets[max(0, end_line - 1)]:
                            (offsets[end_line] if end_line < len(offsets) else len(source))]
    start = offsets[max(0, line - 1)] + _char_col(start_line_text, col)
    end = offsets[max(0, end_line - 1)] + _char_col(end_line_text, end_col)
    return start, min(end, len(source))


@dataclass
class AstSpan:
    path: str
    node_type: str
    start: int
    end: int
    start_line: int
    end_line: int
    parent: str | None
    field: str
    index: int | None
    is_stmt: bool
    child_count: int
    list_lengths: dict[str, int]
    preview: str


def ast_node_table(source: str) -> dict[str, AstSpan]:
    """Every AST node, addressed by a structural path from the module root.

    Paths are the graph addresses: `body[3].body[0].value` is the return value
    of the fourth top-level statement. The path is stable for one base version;
    pair an edit with `base_sha256` to guarantee the caller saw that version.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        raise CodeEditError(f"source does not parse: {e}") from e
    offsets = _line_offsets(source)
    out: dict[str, AstSpan] = {}

    def walk(node: ast.AST, path: str, parent: str | None,
             field: str, index: int | None) -> None:
        start, end = _node_span(source, offsets, node)
        start_line = int(getattr(node, "lineno", 1) or 1)
        # A decorated definition is one editable unit: its span starts at the
        # first decorator, so replacing/deleting it cannot orphan the decorator.
        decorators = getattr(node, "decorator_list", None) or []
        if decorators:
            start = _decorator_start(node, offsets, len(source))
            start_line = int(getattr(decorators[0], "lineno", start_line)
                             or start_line)
        lists: dict[str, int] = {}
        children = 0
        for name, value in ast.iter_fields(node):
            if isinstance(value, ast.AST):
                child_path = f"{path}.{name}" if path else name
                walk(value, child_path, path, name, None)
                children += 1
            elif isinstance(value, list):
                lists[name] = len(value)
                for i, item in enumerate(value):
                    if isinstance(item, ast.AST):
                        child_path = (f"{path}.{name}[{i}]" if path
                                      else f"{name}[{i}]")
                        walk(item, child_path, path, name, i)
                        children += 1
        raw = source[start:end]
        preview = raw.splitlines()[0][:160] if raw else ""
        out[path] = AstSpan(
            path=path, node_type=type(node).__name__,
            start=start, end=end,
            start_line=start_line,
            end_line=int(getattr(node, "end_lineno",
                                 getattr(node, "lineno", 1)) or 1),
            parent=parent, field=field, index=index,
            is_stmt=isinstance(node, ast.stmt),
            child_count=children, list_lengths=lists, preview=preview,
        )

    walk(tree, "", None, "", None)
    return out


def ast_outline(source: str, *, target: str | None = None,
                max_nodes: int = 200) -> dict[str, Any]:
    table = ast_node_table(source)
    if target is not None:
        if target not in table:
            raise CodeEditError(f"no AST node at path {target!r}")
        root_path = target
    else:
        root_path = ""
    children: dict[str, list[AstSpan]] = {}
    for rec in table.values():
        if rec.parent is not None:
            children.setdefault(rec.parent, []).append(rec)
    for key in children:
        children[key].sort(key=lambda r: (r.start, r.path))

    lines: list[str] = []

    def emit(path: str, depth: int) -> None:
        if len(lines) >= max_nodes:
            return
        rec = table[path]
        span = f"L{rec.start_line}"
        if rec.end_line != rec.start_line:
            span += f"-{rec.end_line}"
        preview = rec.preview.strip()
        if len(preview) > 100:
            preview = preview[:97] + "..."
        lines.append(f"{'  ' * min(depth, 20)}{rec.path or '<Module>'} : "
                     f"{rec.node_type} {span}"
                     + (f"  | {preview}" if preview else ""))
        for child in children.get(path, []):
            if len(lines) >= max_nodes:
                return
            emit(child.path, depth + 1)

    emit(root_path, 0)
    text = "\n".join(lines)
    return {"path": "", "lines": "ast", "text": text, "kind": "ast",
            "n_nodes": len(table), "estimated_tokens": max(1, len(text) // 4)}

def _module_insert_offset(source: str, tree: ast.Module,
                          offsets: list[int]) -> int:
    """After the last top-level import; else after the docstring; else 0."""
    imports = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]
    if imports:
        last = imports[-1]
        return _line_end_offset(offsets,
                                int(getattr(last, "end_lineno", last.lineno) or last.lineno),
                                len(source))
    if tree.body and isinstance(tree.body[0], ast.Expr):
        first = tree.body[0]
        if isinstance(getattr(first, "value", None), ast.Constant) \
                and isinstance(first.value.value, str):
            return _line_end_offset(offsets,
                                    int(getattr(first, "end_lineno", first.lineno)
                                        or first.lineno), len(source))
    return 0


def _import_text(op: dict[str, Any]) -> str:
    module = str(op.get("module") or "").strip()
    names = [str(x).strip() for x in (op.get("names") or []) if str(x).strip()]
    if not module and not names:
        raise CodeEditError("insert_import needs module and/or names")
    if names:
        return f"from {module} import {', '.join(names)}\n" if module \
            else f"import {', '.join(names)}\n"
    return f"import {module}\n"


def _ensure_newline(text: str) -> str:
    return text if not text or text.endswith("\n") else text + "\n"


def _replace_span(source: str, start: int, end: int, text: str) -> str:
    return source[:start] + text + source[end:]


def _rename_edits(source: str, old: str, new: str) -> tuple[list[tuple[int, int, str]], int]:
    """Lexical NAME-token rename edits within one file. Deliberately reported
    as lexical; scope-aware rename is a later graph pass."""
    if not old.isidentifier() or not new.isidentifier():
        raise CodeEditError("rename needs identifier names")
    edits: list[tuple[int, int, str]] = []
    offsets = _line_offsets(source)
    try:
        for tok in tokenize.generate_tokens(StringIO(source).readline):
            if tok.type == tokenize.NAME and tok.string == old:
                edits.append((_offset(offsets, tok.start[0], tok.start[1]),
                              _offset(offsets, tok.end[0], tok.end[1]), new))
    except (tokenize.TokenError, IndentationError) as e:
        raise CodeEditError(f"cannot tokenize source: {e}") from e
    return edits, len(edits)


def _apply_ops(source: str, ops: list[dict[str, Any]]) -> tuple[str, list[dict[str, Any]]]:
    tree = ast.parse(source)
    symbols = symbol_table(source)
    offsets = _line_offsets(source)
    edits: list[tuple[int, int, str, dict[str, Any]]] = []
    changes: list[dict[str, Any]] = []
    ast_table: dict[str, AstSpan] | None = None

    def ast_at(op: dict[str, Any]) -> AstSpan:
        nonlocal ast_table
        if ast_table is None:
            ast_table = ast_node_table(source)
        target = op.get("target")
        if isinstance(target, dict):
            target = target.get("path") or target.get("node_id")
        target = str(target or "").strip()
        if not target:
            raise CodeEditError(f"{op.get('op')}: missing target AST path")
        rec = ast_table.get(target)
        if rec is None:
            available = ", ".join(list(ast_table)[:30])
            raise CodeEditError(
                f"{op.get('op')}: no AST node at path {target!r}; "
                f"available (first 30): {available}")
        return rec

    def statement_line_span(rec: AstSpan) -> tuple[int, int]:
        start = offsets[max(0, rec.start_line - 1)]
        end = _line_end_offset(offsets, rec.end_line, len(source))
        return start, end

    def siblings(rec: AstSpan) -> list[AstSpan]:
        if ast_table is None or rec.parent is None or rec.index is None:
            return []
        return sorted(
            [r for r in ast_table.values()
             if r.parent == rec.parent and r.field == rec.field],
            key=lambda r: (r.index if r.index is not None else -1))

    def sym(op: dict[str, Any]) -> SymbolSpan:
        name = str(op.get("symbol") or op.get("qualname") or "").strip()
        if not name:
            raise CodeEditError(f"{op.get('op')}: missing symbol")
        if name not in symbols:
            available = ", ".join(sorted(symbols)[:20])
            raise CodeEditError(
                f"{op.get('op')}: no symbol {name!r} in this file; "
                f"available: {available}")
        return symbols[name]

    for op in ops:
        if not isinstance(op, dict):
            raise CodeEditError("each op must be an object")
        kind = str(op.get("op") or "").strip()
        if kind == "replace_symbol":
            s = sym(op)
            text = _ensure_newline(str(op.get("text") or ""))
            if not text.strip():
                text = ""
            edits.append((s.start, s.end, text, op))
            changes.append({"op": kind, "symbol": s.qualname,
                            "lines": [s.start_line, s.end_line],
                            "summary": "replace definition"})
        elif kind == "replace_body":
            s = sym(op)
            body = textwrap.dedent(str(op.get("text") or "")).strip("\n")
            if not body.strip():
                body = "pass"
            indent = s.body_indent or (s.indent + "    ")
            rendered = "\n".join(
                (indent + line) if line.strip() else ""
                for line in body.splitlines()
            ) + "\n"
            edits.append((s.body_start, s.body_end, rendered, op))
            changes.append({"op": kind, "symbol": s.qualname,
                            "lines": [s.start_line, s.end_line],
                            "summary": "replace function/class body"})
        elif kind == "insert_import":
            text = _import_text(op)
            if text.strip() and text.strip() in source:
                changes.append({"op": kind, "summary": "already present; skipped"})
                continue
            at = _module_insert_offset(source, tree, offsets)
            if at > 0 and source[at - 1] != "\n":
                text = "\n" + text
            if at < len(source) and source[at:at + 1] not in ("", "\n"):
                text = text + "\n"
            edits.append((at, at, text, op))
            changes.append({"op": kind, "summary": text.strip()})
        elif kind == "delete_symbol":
            s = sym(op)
            # Also consume one trailing blank line, so deleting a function does
            # not silently accumulate whitespace.
            end = s.end
            while end < len(source) and source[end:end + 1] == "\n":
                end += 1
                break
            edits.append((s.start, end, "", op))
            changes.append({"op": kind, "symbol": s.qualname,
                            "lines": [s.start_line, s.end_line],
                            "summary": "delete definition"})
        elif kind in ("insert_before_symbol", "insert_after_symbol"):
            s = sym(op)
            text = _ensure_newline(str(op.get("text") or ""))
            at = s.start if kind == "insert_before_symbol" else s.end
            if kind == "insert_after_symbol" and at > 0 and source[at - 1] != "\n":
                text = "\n" + text
            edits.append((at, at, text, op))
            changes.append({"op": kind, "symbol": s.qualname,
                            "summary": "insert text at symbol anchor"})
        elif kind == "replace_node":
            rec = ast_at(op)
            text = str(op.get("text") or "")
            if not text:
                raise CodeEditError(
                    "replace_node with empty text is refused; use delete_node")
            edits.append((rec.start, rec.end, text, op))
            changes.append({"op": kind, "target": rec.path,
                            "type": rec.node_type,
                            "summary": "replace AST node"})
        elif kind in ("insert_before_node", "insert_after_node"):
            rec = ast_at(op)
            text = str(op.get("text") or "")
            if not text:
                raise CodeEditError(f"{kind}: empty text")
            if rec.is_stmt:
                start, end = statement_line_span(rec)
                indent = source[start:rec.start]
                body = textwrap.dedent(text).strip("\n")
                indented = "\n".join(
                    (indent + line) if line.strip() else ""
                    for line in body.splitlines()) + "\n"
                at = start if kind == "insert_before_node" else end
                edits.append((at, at, indented, op))
            else:
                at = rec.start if kind == "insert_before_node" else rec.end
                edits.append((at, at, text, op))
            changes.append({"op": kind, "target": rec.path,
                            "type": rec.node_type,
                            "summary": "insert at AST node"})
        elif kind == "delete_node":
            rec = ast_at(op)
            if rec.is_stmt:
                start, end = statement_line_span(rec)
                parent = ast_table.get(rec.parent) if (ast_table and rec.parent) else None
                only = bool(parent and rec.field in
                            ("body", "orelse", "finalbody")
                            and parent.list_lengths.get(rec.field) == 1)
                if only:
                    indent = source[start:rec.start]
                    edits.append((start, end, indent + "pass\n", op))
                else:
                    edits.append((start, end, "", op))
            else:
                if rec.parent is None or rec.index is None:
                    raise CodeEditError(
                        "delete_node on a required field is refused; use "
                        "replace_node with a valid placeholder")
                sibs = siblings(rec)
                if len(sibs) > 1:
                    if rec.index > 0:
                        prev = sibs[rec.index - 1]
                        edits.append((prev.end, rec.end, "", op))
                    else:
                        nxt = sibs[1]
                        edits.append((rec.start, nxt.start, "", op))
                else:
                    edits.append((rec.start, rec.end, "", op))
            changes.append({"op": kind, "target": rec.path,
                            "type": rec.node_type,
                            "summary": "delete AST node"})
        elif kind == "wrap_node":
            rec = ast_at(op)
            prefix = str(op.get("prefix") or "")
            suffix = str(op.get("suffix") or "")
            if not prefix and not suffix:
                raise CodeEditError("wrap_node needs prefix and/or suffix")
            if rec.is_stmt:
                if not prefix.rstrip().endswith(":"):
                    raise CodeEditError(
                        "wrap_node on a statement needs a block prefix ending "
                        "with ':' (e.g. 'if cond:')")
                start, end = statement_line_span(rec)
                indent = source[start:rec.start]
                old = source[start:end]
                body = textwrap.indent(textwrap.dedent(old), "    ")
                rendered = indent + prefix.rstrip() + "\n" + body
                if suffix:
                    rendered += indent + suffix.strip() + "\n"
                edits.append((start, end, rendered, op))
            else:
                old = source[rec.start:rec.end]
                edits.append((rec.start, rec.end, prefix + old + suffix, op))
            changes.append({"op": kind, "target": rec.path,
                            "type": rec.node_type,
                            "summary": "wrap AST node"})
        elif kind == "replace_span":
            try:
                start = _offset(offsets, int(op["start_line"]), int(op.get("start_col", 0)))
                end = _offset(offsets, int(op["end_line"]), int(op.get("end_col", 0)))
            except (KeyError, TypeError, ValueError) as e:
                raise CodeEditError(
                    "replace_span needs start_line/start_col/end_line/end_col") from e
            if start < 0 or end < start or end > len(source):
                raise CodeEditError("replace_span out of range")
            text = _ensure_newline(str(op.get("text") or ""))
            edits.append((start, end, text, op))
            changes.append({"op": kind, "summary": f"replace {start}:{end}"})
        elif kind == "rename_symbol":
            s = sym(op)
            new = str(op.get("new_name") or "").strip()
            if not new:
                raise CodeEditError("rename_symbol needs new_name")
            if len(ops) != 1:
                raise CodeEditError(
                    "rename_symbol must be the only op in a script (v0 is "
                    "lexical; combine renames separately)")
            rename_edits, count = _rename_edits(source, s.name, new)
            for st, en, txt in rename_edits:
                edits.append((st, en, txt, op))
            changes.append({"op": kind, "symbol": s.qualname,
                            "summary": f"renamed {s.name!r} -> {new!r} "
                                       f"({count} lexical NAME occurrences)"})
        else:
            raise CodeEditError(
                f"unknown op {kind!r}; supported: replace_symbol, "
                f"replace_body, insert_import, delete_symbol, "
                f"insert_before_symbol, insert_after_symbol, replace_span, "
                f"rename_symbol")

    # Apply bottom-up so earlier offsets stay valid. Refuse overlapping edits:
    # an ambiguous transaction is a bug, not a merge strategy.
    edits.sort(key=lambda e: (e[0], e[1]), reverse=True)
    last_start = None
    for start, end, text, _op in edits:
        if last_start is not None and end > last_start:
            raise CodeEditError("overlapping edits in one script")
        last_start = start
    # The canonical text is the lossless Python CST bridge
    # (`domains.py_cst_ingest` -> `CstNode`/`flat_text`). Applying edits to the
    # leaf structure preserves every comment/trivia leaf outside the spans.
    from scripts.ocelot_lossless import LosslessText
    doc = LosslessText.from_python(source)
    for start, end, text, _op in edits:
        doc.replace(start, end, text)
    return doc.render(), changes


def apply_edit_script(root: str | Path, script: dict[str, Any], *,
                      write: bool = False) -> dict[str, Any]:
    """Validate and optionally apply a graph-addressed edit script.

    `write=False` (default) is a pure preview. `write=True` backs up the
    original, writes atomically, and returns the backup path. The caller
    (normally the dev-memory MCP server) records the transaction in the
    journal.
    """
    if not isinstance(script, dict):
        raise CodeEditError("edit script must be an object")
    for key in FORBIDDEN_SCRIPT_KEYS:
        if key in script:
            raise CodeEditError(
                f"raw {key!r} input is refused: send semantic ops over graph "
                f"targets; a diff is only an output view")
    root = Path(root).resolve()
    file = str(script.get("file") or "").strip()
    if not file:
        raise CodeEditError("edit script needs file")
    path = (root / file).resolve()
    try:
        path.relative_to(root)
    except ValueError as e:
        raise CodeEditError("file escapes the repo root") from e
    if path.suffix != ".py":
        raise CodeEditError("v0 edits Python (.py) only; the Rust path uses "
                            "the hub-IR/tree-sitter readers")
    if not path.is_file():
        raise CodeEditError(f"no such file: {file}")
    if path.stat().st_size > MAX_SOURCE_BYTES:
        raise CodeEditError(f"file exceeds {MAX_SOURCE_BYTES} bytes")

    source = path.read_text(encoding="utf-8")
    base_sha = sha256_text(source)
    expected = script.get("base_sha256")
    if expected and str(expected) != base_sha:
        raise CodeEditError(
            f"stale base: file sha256 is {base_sha}, script expected {expected}")
    ops = script.get("ops")
    if not isinstance(ops, list) or not ops:
        raise CodeEditError("edit script needs a non-empty ops list")

    new_source, changes = _apply_ops(source, ops)
    try:
        ast.parse(new_source)
        compile(new_source, str(path), "exec")
    except (SyntaxError, ValueError) as e:
        raise CodeEditError(f"edit would not parse: {e}") from e
    new_sha = sha256_text(new_source)

    diff_lines = list(difflib.unified_diff(
        source.splitlines(keepends=True),
        new_source.splitlines(keepends=True),
        fromfile=f"a/{file}", tofile=f"b/{file}",
    ))
    diff_view = "".join(diff_lines[:400])
    applied = False
    backup = None
    if write:
        backup_dir = root / "var" / "ocelot_dev_edits" / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup = backup_dir / (
            f"{time.strftime('%Y%m%d-%H%M%S')}_{base_sha[:12]}_{path.name}")
        shutil.copy2(path, backup)
        tmp = path.with_name(path.name + ".ocelot_tmp")
        tmp.write_text(new_source, encoding="utf-8")
        try:
            os.chmod(tmp, path.stat().st_mode)
            os.replace(tmp, path)
        finally:
            if tmp.exists():
                try:
                    tmp.unlink()
                except OSError:
                    pass
        applied = True

    return {
        "ok": True,
        "file": file,
        "applied": applied,
        "base_sha256": base_sha,
        "new_sha256": new_sha,
        "before": {"lines": len(source.splitlines()), "sha256": base_sha},
        "after": {"lines": len(new_source.splitlines()), "sha256": new_sha},
        "ops": ops,
        "changes": changes,
        "diff_view": diff_view,
        "diff_note": ("a unified diff is a rendered view for humans; the "
                      "canonical record is the op list above"),
        "backup": str(backup) if backup else None,
        "lossless": {"python_cst": True, "roundtrip": True},
        "graph_stale": bool(applied),
    }


# --------------------------------------------------------------------------- #
# CLI (used by the dev-memory module; also runnable standalone)
# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> int:
    import argparse
    p = argparse.ArgumentParser(description="graph-addressed Python edits")
    p.add_argument("--root", default=str(Path(__file__).resolve().parent.parent))
    p.add_argument("--script", required=True,
                   help="JSON file: {file, base_sha256?, ops: [...]}")
    p.add_argument("--apply", action="store_true")
    p.add_argument("--pretty", action="store_true")
    a = p.parse_args(argv)
    script = json.loads(Path(a.script).read_text(encoding="utf-8"))
    try:
        result = apply_edit_script(a.root, script, write=a.apply)
    except CodeEditError as e:
        print(json.dumps({"ok": False, "error": str(e)},
                         indent=2 if a.pretty else None))
        return 1
    print(json.dumps(result, indent=2 if a.pretty else None))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
