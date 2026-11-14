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

Edit ordering. Every op's edits are applied bottom-up against the base text.
Two inserts at the same offset land in op order (the first op's text comes
first). An insert at X and a replacement that starts at X always put the
insert before the replaced text, whichever op came first.
"""
from __future__ import annotations

import ast
import difflib
import hashlib
import json
import re
import textwrap
import tokenize
from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from typing import Any

from scripts.ocelot_edit_txn import (
    check_base,
    detect_newline,
    encode_text,
    normalize_newlines,
    read_source,
    sha256_bytes,
    write_source,
)
from scripts.ocelot_lossless import python_roundtrip

MAX_SOURCE_BYTES = 2 * 1024 * 1024
FORBIDDEN_SCRIPT_KEYS = ("diff", "patch", "unified_diff", "hunk")
_NEWLINE_NAMES = {"\n": "lf", "\r\n": "crlf", "\r": "cr"}
_CODING_RE = re.compile(r"^[ \t\f]*#.*?coding[:=][ \t]*([-\w.]+)")


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
    # True when the body sits on the header line (`def f(self): return 1`).
    inline_body: bool = False


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
            inline = False
            if body:
                first = body[0]
                last = body[-1]
                first_line = int(getattr(first, "lineno", node.lineno))
                line_start = offsets[max(0, first_line - 1)]
                body_end = _line_end_offset(
                    offsets, int(getattr(last, "end_lineno", last.lineno) or last.lineno), n)
                first_start = _node_span(source, offsets, first)[0]
                if source[line_start:first_start].strip():
                    # One-line compound statement (`def f(self): return 1`).
                    # The span starts after the header colon, so the header
                    # survives a body replacement.
                    inline = True
                    colon = first_start - 1
                    while colon > 0 and source[colon] in " \t":
                        colon -= 1
                    if source[colon] != ":":
                        raise CodeEditError(
                            f"cannot locate the header colon of {qual!r}")
                    body_start = colon + 1
                    body_indent = indent + "    "
                else:
                    body_start = line_start
                    body_indent = _indent_at(source, offsets, first_line)
            else:
                body_start = start
                body_end = end
                body_indent = indent + "    "
            out[qual] = SymbolSpan(name, qual, kind, start, end,
                                   int(node.lineno), end_line,
                                   body_start, body_end, body_indent,
                                   indent, node, inline)
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
    # False for nodes with no lineno/end_lineno (operators, ctx, arguments,
    # comprehensions). Such nodes keep their path but cannot be edited.
    located: bool = True


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
        located = (getattr(node, "lineno", None) is not None
                   and getattr(node, "end_lineno", None) is not None)
        out[path] = AstSpan(
            path=path, node_type=type(node).__name__,
            start=start, end=end,
            start_line=start_line,
            end_line=int(getattr(node, "end_lineno",
                                 getattr(node, "lineno", 1)) or 1),
            parent=parent, field=field, index=index,
            is_stmt=isinstance(node, ast.stmt),
            child_count=children, list_lengths=lists, preview=preview,
            located=located,
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
        span = f"L{rec.start_line}" if rec.located else "(no location)"
        if rec.located and rec.end_line != rec.start_line:
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

def _is_docstring(stmt: ast.AST) -> bool:
    return (isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Constant)
            and isinstance(stmt.value.value, str))


def _module_insert_offset(source: str, tree: ast.Module,
                          offsets: list[int]) -> int:
    """Where a new top-level import goes.

    1. After the last import of the leading import block (the imports before
       the first statement that is neither an import nor the docstring).
    2. Else after the module docstring.
    3. Else after the shebang and/or encoding-cookie lines at the top.
    4. Else at offset 0.
    """
    n = len(source)
    last_import: ast.stmt | None = None
    for idx, stmt in enumerate(tree.body):
        if isinstance(stmt, (ast.Import, ast.ImportFrom)):
            last_import = stmt
            continue
        if idx == 0 and _is_docstring(stmt):
            continue
        break
    if last_import is not None:
        return _line_end_offset(
            offsets, int(getattr(last_import, "end_lineno", last_import.lineno)
                         or last_import.lineno), n)
    if tree.body and _is_docstring(tree.body[0]):
        first = tree.body[0]
        return _line_end_offset(
            offsets, int(getattr(first, "end_lineno", first.lineno) or first.lineno), n)
    # Leading shebang and/or encoding cookie, in that order, on lines 1-2.
    k = 0
    for i, line in enumerate(source.split("\n", 2)[:2]):
        if i == k and (line.startswith("#!") or _CODING_RE.match(line)):
            k += 1
        else:
            break
    return _line_end_offset(offsets, k, n) if k else 0


def _import_key(stmt: ast.stmt, alias: ast.alias) -> tuple[Any, ...]:
    if isinstance(stmt, ast.Import):
        return ("import", alias.name, alias.asname)
    return ("from", int(stmt.level or 0), stmt.module or "",
            alias.name, alias.asname)


def _alias_text(alias: ast.alias) -> str:
    return alias.name + (f" as {alias.asname}" if alias.asname else "")


def _present_import_keys(source: str) -> set[tuple[Any, ...]]:
    """Keys of every module-level import binding in `source` (AST, not text)."""
    present: set[tuple[Any, ...]] = set()
    for stmt in ast.parse(source).body:
        if isinstance(stmt, (ast.Import, ast.ImportFrom)):
            present.update(_import_key(stmt, a) for a in stmt.names)
    return present


def _missing_import_text(text: str, present: set[tuple[Any, ...]]) -> str:
    """The part of `text` (one import statement) whose bindings are not in
    `present`. Empty when everything is present.

    `present` is updated in place, so two ops in one script that import the
    same name insert it once. Presence is decided on the AST, so comments and
    substrings do not count.
    """
    try:
        wanted = ast.parse(text).body
    except SyntaxError as e:
        raise CodeEditError(f"insert_import text does not parse: {e}") from e
    lines: list[str] = []
    for stmt in wanted:
        if not isinstance(stmt, (ast.Import, ast.ImportFrom)):
            raise CodeEditError("insert_import text must be an import")
        missing = []
        for alias in stmt.names:
            key = _import_key(stmt, alias)
            if key not in present:
                present.add(key)
                missing.append(alias)
        if not missing:
            continue
        items = ", ".join(_alias_text(a) for a in missing)
        if isinstance(stmt, ast.Import):
            lines.append(f"import {items}\n")
        else:
            module = "." * int(stmt.level or 0) + (stmt.module or "")
            lines.append(f"from {module} import {items}\n")
    return "".join(lines)



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


_FUNC_NODES = (ast.FunctionDef, ast.AsyncFunctionDef)
_COMP_NODES = (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)


class _Scope:
    """One Python name scope: module, class body, function/lambda or comprehension.

    `bound` holds names the scope binds locally. `globals_` and `nonlocals`
    hold names declared with those statements; `local` is what the scope
    binds for itself.
    """

    def __init__(self, kind: str, node: ast.AST | None, parent: "_Scope | None"):
        self.kind = kind
        self.node = node
        self.parent = parent
        self.bound: set[str] = set()
        self.globals_: set[str] = set()
        self.nonlocals: set[str] = set()
        self.local: set[str] = set()
        self.first_param: str | None = None


class _ScopeIndex:
    """Scopes of one module tree, and the scope each name-like node sits in.

    Resolution follows Python rules in the simple form: a name is looked up
    innermost scope first; class bodies are visible only to themselves, not to
    the functions nested in them; `global` sends a name to the module scope.
    """

    def __init__(self, tree: ast.Module):
        self.module = _Scope("module", tree, None)
        self.home: dict[int, _Scope] = {}           # def/class node -> scope holding it
        self.own: dict[int, _Scope] = {}            # def/class node -> its own scope
        self.names: list[tuple[ast.Name, _Scope]] = []
        self.attrs: list[tuple[ast.Attribute, _Scope]] = []
        self.keywords: list[tuple[ast.keyword, _Scope]] = []
        self.args: list[tuple[ast.arg, bool]] = []  # (arg, is keyword-only)
        self.decls: list[tuple[ast.stmt, _Scope]] = []  # global / nonlocal
        self.scopes: list[_Scope] = [self.module]
        for stmt in tree.body:
            self._visit(stmt, self.module)
        for scope in self.scopes:
            scope.local = scope.bound - scope.globals_ - scope.nonlocals

    def _new(self, kind: str, node: ast.AST, parent: _Scope) -> _Scope:
        scope = _Scope(kind, node, parent)
        self.scopes.append(scope)
        self.own[id(node)] = scope
        return scope

    def _bind_args(self, args: ast.arguments, scope: _Scope) -> None:
        positional = list(args.posonlyargs) + list(args.args)
        scope.first_param = positional[0].arg if positional else None
        kwonly = {id(a) for a in args.kwonlyargs}
        extra = [a for a in (args.vararg, args.kwarg) if a is not None]
        for a in positional + list(args.kwonlyargs) + extra:
            scope.bound.add(a.arg)
            self.args.append((a, id(a) in kwonly))

    def _visit_outer_parts(self, args: ast.arguments, scope: _Scope) -> None:
        all_args = (list(args.posonlyargs) + list(args.args) + list(args.kwonlyargs)
                    + [a for a in (args.vararg, args.kwarg) if a is not None])
        parts = [d for d in list(args.defaults) + list(args.kw_defaults) if d is not None]
        parts += [a.annotation for a in all_args if a.annotation is not None]
        for part in parts:
            self._visit(part, scope)

    def _visit(self, node: ast.AST, scope: _Scope) -> None:
        if isinstance(node, _FUNC_NODES):
            scope.bound.add(node.name)
            self.home[id(node)] = scope
            for dec in node.decorator_list:
                self._visit(dec, scope)
            self._visit_outer_parts(node.args, scope)
            if node.returns is not None:
                self._visit(node.returns, scope)
            inner = self._new("function", node, scope)
            self._bind_args(node.args, inner)
            for stmt in node.body:
                self._visit(stmt, inner)
            return
        if isinstance(node, ast.Lambda):
            self._visit_outer_parts(node.args, scope)
            inner = self._new("function", node, scope)
            self._bind_args(node.args, inner)
            self._visit(node.body, inner)
            return
        if isinstance(node, ast.ClassDef):
            scope.bound.add(node.name)
            self.home[id(node)] = scope
            for dec in node.decorator_list:
                self._visit(dec, scope)
            for base in node.bases:
                self._visit(base, scope)
            for kw in node.keywords:
                self._visit(kw, scope)
            inner = self._new("class", node, scope)
            for stmt in node.body:
                self._visit(stmt, inner)
            return
        if isinstance(node, _COMP_NODES):
            gens = node.generators
            self._visit(gens[0].iter, scope)
            inner = self._new("comp", node, scope)
            for i, gen in enumerate(gens):
                if i:
                    self._visit(gen.iter, inner)
                self._visit(gen.target, inner)
                for cond in gen.ifs:
                    self._visit(cond, inner)
            if isinstance(node, ast.DictComp):
                self._visit(node.key, inner)
                self._visit(node.value, inner)
            else:
                self._visit(node.elt, inner)
            return
        if isinstance(node, ast.Name):
            self.names.append((node, scope))
            if isinstance(node.ctx, (ast.Store, ast.Del)):
                scope.bound.add(node.id)
            return
        if isinstance(node, ast.NamedExpr):
            self._visit(node.value, scope)
            target_scope = scope
            while target_scope.kind == "comp" and target_scope.parent is not None:
                target_scope = target_scope.parent
            target_scope.bound.add(node.target.id)
            self.names.append((node.target, target_scope))
            return
        if isinstance(node, ast.Attribute):
            self.attrs.append((node, scope))
            self._visit(node.value, scope)
            return
        if isinstance(node, ast.keyword):
            self.keywords.append((node, scope))
            self._visit(node.value, scope)
            return
        if isinstance(node, (ast.Global, ast.Nonlocal)):
            if isinstance(node, ast.Global):
                scope.globals_.update(node.names)
            else:
                scope.nonlocals.update(node.names)
            self.decls.append((node, scope))
            return
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            for alias in node.names:
                bound = alias.asname or alias.name.split(".")[0]
                if bound != "*":
                    scope.bound.add(bound)
            return
        if isinstance(node, ast.ExceptHandler) and node.name:
            scope.bound.add(node.name)
        kind = type(node).__name__
        if kind in ("MatchAs", "MatchStar") and getattr(node, "name", None):
            scope.bound.add(node.name)
        if kind == "MatchMapping" and getattr(node, "rest", None):
            scope.bound.add(node.rest)
        for child in ast.iter_child_nodes(node):
            self._visit(child, scope)

    def resolve(self, name: str, scope: _Scope) -> _Scope | None:
        """The scope whose binding `name` refers to when used in `scope`."""
        s: _Scope | None = scope
        first = True
        while s is not None:
            if first or s.kind != "class":
                if name in s.globals_:
                    return self.module
                if name in s.local:
                    return s
            first = False
            s = s.parent
        return None


def _rename_edits(source: str, tree: ast.Module, old: str, new: str,
                  def_line: int
                  ) -> tuple[list[tuple[int, int, str]], list[list[int]], list[dict[str, Any]]]:
    """Scope-aware rename of the definition at `def_line` named `old`.

    Renames the definition's name token, every name that resolves to the
    definition's binding scope, and for a method also `self.f` / `cls.f` inside
    its class and `A.f` where `A` is the class. Other attributes, keyword
    arguments, parameters and names bound elsewhere are left alone and listed in
    `skipped`. Returns the edits, the `[line, col]` of each renamed token, and
    the skipped tokens (col is a 0-based character column).
    """
    if not old.isidentifier() or not new.isidentifier():
        raise CodeEditError("rename needs identifier names")
    target = None
    for node in ast.walk(tree):
        if isinstance(node, _FUNC_NODES + (ast.ClassDef,)) and node.name == old \
                and node.lineno == def_line:
            target = node
            break
    if target is None:
        raise CodeEditError(f"rename_symbol: no definition of {old!r} at line {def_line}")
    offsets = _line_offsets(source)
    try:
        toks = list(tokenize.generate_tokens(StringIO(source).readline))
    except (tokenize.TokenError, IndentationError) as e:
        raise CodeEditError(f"cannot tokenize source: {e}") from e
    name_at: dict[int, tokenize.TokenInfo] = {}   # start offset -> NAME token
    end_to_start: dict[int, int] = {}              # end offset -> start offset
    for tok in toks:
        if tok.type == tokenize.NAME:
            start = _offset(offsets, tok.start[0], tok.start[1])
            name_at[start] = tok
            end_to_start[_offset(offsets, tok.end[0], tok.end[1])] = start

    def name_token(start: int, end: int | None = None, where: str = "") -> int:
        """Start offset of the NAME token named `old` at `start` (or ending at
        `end`). Refuses when the AST position has no matching token, so a
        rename never leaves a stale reference behind."""
        if end is not None:
            start = end_to_start.get(end, -1)
        tok = name_at.get(start)
        if tok is None or tok.string != old:
            line = source.count("\n", 0, start) + 1
            raise CodeEditError(
                f"rename_symbol: {where or 'occurrence'} at line {line} has no "
                f"matching NAME token; refusing rather than leave a stale reference")
        return start

    idx = _ScopeIndex(tree)
    home = idx.home.get(id(target))
    if home is None:
        raise CodeEditError(f"rename_symbol: cannot find the scope of {old!r}")

    renamed: dict[int, None] = {}
    reasons: dict[int, str] = {}

    # (a) the definition's own name: the NAME token right after `def`/`class`.
    keyword_seen = False
    for i, tok in enumerate(toks):
        if tok.type == tokenize.NAME and tok.string in ("def", "class") \
                and tok.start[0] == def_line:
            nxt = toks[i + 1]
            if nxt.type == tokenize.NAME and nxt.string == old:
                renamed[_offset(offsets, nxt.start[0], nxt.start[1])] = None
                keyword_seen = True
            break
    if not keyword_seen:
        raise CodeEditError(f"rename_symbol: cannot find the name token of {old!r}")

    # (b) names that resolve to the definition's binding scope.
    for node, scope in idx.names:
        if node.id != old:
            continue
        if idx.resolve(old, scope) is home:
            start, _end = _node_span(source, offsets, node)
            renamed[name_token(start, where="name")] = None

    # (c) methods: self.f / cls.f in the class, and A.f for the class A.
    is_method = home.kind == "class"
    for node, scope in idx.attrs:
        if node.attr != old:
            continue
        _start, end = _node_span(source, offsets, node)
        attr_start = end_to_start.get(end, -1)
        hit = False
        if is_method and isinstance(node.value, ast.Name):
            base = node.value.id
            if base == home.node.name:
                hit = idx.resolve(base, scope) is home.parent
            else:
                owner = idx.resolve(base, scope)
                hit = (owner is not None and owner.kind == "function"
                       and owner.parent is home and owner.first_param == base)
        if hit:
            renamed[name_token(attr_start, where="attribute")] = None
        else:
            reasons[attr_start] = "attribute"

    # Keyword arguments and parameters named `old`.
    for node, _scope in idx.keywords:
        if node.arg == old:
            reasons[_node_span(source, offsets, node)[0]] = "keyword"
    for arg, kwonly in idx.args:
        if arg.arg == old:
            reasons[_node_span(source, offsets, arg)[0]] = (
                "keyword" if kwonly else "shadowed")

    # global / nonlocal declarations that name the target.
    for stmt, scope in idx.decls:
        if isinstance(stmt, ast.Global):
            target_scope = idx.module
        else:
            target_scope = idx.resolve(old, scope.parent) if scope.parent else None
        s_start, s_end = _node_span(source, offsets, stmt)
        for start, tok in name_at.items():
            if s_start <= start < s_end and tok.string == old and target_scope is home:
                renamed[name_token(start, where="declaration")] = None

    edits: list[tuple[int, int, str]] = []
    where: list[list[int]] = []
    for start in sorted(renamed):
        tok = name_at[start]
        edits.append((start, _offset(offsets, tok.end[0], tok.end[1]), new))
        where.append([tok.start[0], tok.start[1]])
    skipped: list[dict[str, Any]] = []
    for start in sorted(name_at):
        tok = name_at[start]
        if tok.string != old or start in renamed:
            continue
        skipped.append({"line": tok.start[0], "col": tok.start[1],
                        "reason": reasons.get(start, "shadowed")})
    return edits, where, skipped


def _owns_its_lines(source: str, offsets: list[int], rec: AstSpan) -> bool:
    """True when nothing but indentation precedes the statement on its first
    line, and nothing but whitespace or a comment follows it on its last line.
    Deleting or re-indenting such a statement cannot touch other code."""
    head = source[offsets[max(0, rec.start_line - 1)]:rec.start]
    tail_end = offsets[rec.end_line] if rec.end_line < len(offsets) else len(source)
    tail = source[rec.end:tail_end].strip()
    return not head.strip() and (tail == "" or tail.startswith("#"))


def _string_spans(source: str, offsets: list[int]) -> list[tuple[int, int]]:
    """Source offsets of every string literal token (f-strings included)."""
    spans: list[tuple[int, int]] = []
    fstring_start = getattr(tokenize, "FSTRING_START", None)
    fstring_end = getattr(tokenize, "FSTRING_END", None)
    open_fstrings: list[int] = []
    try:
        for tok in tokenize.generate_tokens(StringIO(source).readline):
            if tok.type == tokenize.STRING:
                spans.append((_offset(offsets, *tok.start),
                              _offset(offsets, *tok.end)))
            elif fstring_start is not None and tok.type == fstring_start:
                open_fstrings.append(_offset(offsets, *tok.start))
            elif fstring_end is not None and tok.type == fstring_end:
                spans.append((open_fstrings.pop(),
                              _offset(offsets, *tok.end)))
    except (tokenize.TokenError, IndentationError) as e:
        raise CodeEditError(f"cannot tokenize source: {e}") from e
    return spans


def _indent_statement_lines(source: str, start: int, end: int,
                            spans: list[tuple[int, int]],
                            pad: str = "    ") -> str:
    """Prefix `pad` to each non-blank line of source[start:end] (whole lines).
    A line whose start offset lies strictly inside a string literal is copied
    unchanged, so the string value does not change."""
    parts: list[str] = []
    pos = start
    while pos < end:
        nl = source.find("\n", pos)
        line_end = len(source) if nl < 0 else nl + 1
        line = source[pos:line_end]
        inside = any(a < pos < b for a, b in spans)
        if not inside and line.strip():
            line = pad + line
        parts.append(line)
        pos = line_end
    return "".join(parts)


def _apply_ops(source: str, ops: list[dict[str, Any]],
               newline: str | None = None) -> tuple[str, list[dict[str, Any]]]:
    if newline is None:
        newline = detect_newline(source)
    tree = ast.parse(source)
    symbols = symbol_table(source)
    offsets = _line_offsets(source)
    edits: list[tuple[int, int, str, dict[str, Any]]] = []
    changes: list[dict[str, Any]] = []
    ast_table: dict[str, AstSpan] | None = None
    # Bindings already present, updated as each insert_import is accepted, so
    # two ops in one script that import the same name insert it once.
    present_imports = _present_import_keys(source)

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
        if not rec.located:
            raise CodeEditError(
                f"{op.get('op')}: AST node {target!r} ({rec.node_type}) has no "
                f"source location; target an enclosing node")
        return rec

    def require_owned_lines(rec: AstSpan, kind: str) -> None:
        if rec.is_stmt and not _owns_its_lines(source, offsets, rec):
            raise CodeEditError(
                f"{kind}: statement {rec.path!r} shares a line with other code "
                f"(e.g. 'a = 1; b = 2' or 'if x: y'); split the line first or "
                f"use replace_span")

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
            if s.inline_body:
                rendered = "\n" + rendered
            edits.append((s.body_start, s.body_end, rendered, op))
            changes.append({"op": kind, "symbol": s.qualname,
                            "lines": [s.start_line, s.end_line],
                            "summary": "replace function/class body"})
        elif kind == "insert_import":
            text = _import_text(op)
            missing = _missing_import_text(text, present_imports)
            if not missing:
                changes.append({"op": kind, "summary": "already present; skipped"})
                continue
            at = _module_insert_offset(source, tree, offsets)
            if at > 0 and source[at - 1] != "\n":
                missing = "\n" + missing
            # One blank line after the new import when code follows directly.
            # A following line ending means a blank line already exists.
            nxt = source[at:at + 1]
            if nxt and nxt not in ("\n", "\r"):
                missing = missing + "\n"
            edits.append((at, at, missing, op))
            changes.append({"op": kind, "summary": missing.strip()})
        elif kind == "delete_symbol":
            s = sym(op)
            # Also consume one trailing blank line, so deleting a function does
            # not silently accumulate whitespace. CRLF-aware via `newline`.
            end = s.end
            if source.startswith(newline, end):
                end += len(newline)
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
                require_owned_lines(rec, kind)
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
                require_owned_lines(rec, kind)
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
                require_owned_lines(rec, kind)
                start, end = statement_line_span(rec)
                indent = source[start:rec.start]
                # Re-indent whole lines; lines that start inside a string
                # literal are copied as they are, so string values survive.
                body = _indent_statement_lines(
                    source, start, end, _string_spans(source, offsets))
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
            text = str(op.get("text") or "")
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
            same_name = sorted(q for q, d in symbols.items() if d.name == s.name)
            if len(same_name) > 1:
                raise CodeEditError(
                    f"rename_symbol: {s.name!r} is defined {len(same_name)} times "
                    f"in this file ({', '.join(same_name)}); a lexical rename "
                    f"would change all of them. Use dev_rename_preview (LSP) or "
                    f"rename one with replace_symbol")
            rename_edits, where, skipped = _rename_edits(
                source, tree, s.name, new, s.start_line)
            for st, en, txt in rename_edits:
                edits.append((st, en, txt, op))
            changes.append({"op": kind, "symbol": s.qualname,
                            "occurrences": where, "skipped": skipped,
                            "summary": f"renamed {s.name!r} -> {new!r} "
                                       f"({len(where)} occurrences in scope; "
                                       f"{len(skipped)} same-name tokens left "
                                       f"unchanged)"})
        else:
            raise CodeEditError(
                f"unknown op {kind!r}; supported: replace_symbol, "
                f"replace_body, insert_import, delete_symbol, "
                f"insert_before_symbol, insert_after_symbol, replace_span, "
                f"rename_symbol")

    # Apply bottom-up so earlier offsets stay valid. Refuse overlapping edits:
    # an ambiguous transaction is a bug, not a merge strategy.
    # Edits are appended in op order, so list position is the op index. At one
    # (start, end) the later op is applied first, which leaves the earlier op's
    # text in front in the output (E7).
    order = sorted(range(len(edits)),
                   key=lambda i: (edits[i][0], edits[i][1], i), reverse=True)
    edits = [edits[i] for i in order]
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
        doc.replace(start, end, normalize_newlines(text, newline))
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
    src = read_source(root, file, suffixes=(".py",),
                      max_bytes=MAX_SOURCE_BYTES, error_cls=CodeEditError)
    source = src.text
    base_sha = src.sha256
    check_base(src, script.get("base_sha256"), CodeEditError)
    ops = script.get("ops")
    if not isinstance(ops, list) or not ops:
        raise CodeEditError("edit script needs a non-empty ops list")

    new_source, changes = _apply_ops(source, ops, newline=src.newline)
    try:
        ast.parse(new_source)
        compile(new_source, str(path), "exec")
    except (SyntaxError, ValueError) as e:
        raise CodeEditError(f"edit would not parse: {e}") from e
    new_sha = sha256_bytes(encode_text(src, new_source))

    diff_lines = list(difflib.unified_diff(
        source.splitlines(keepends=True),
        new_source.splitlines(keepends=True),
        fromfile=f"a/{file}", tofile=f"b/{file}",
    ))
    diff_view = "".join(diff_lines[:400])
    applied = False
    backup = None
    if write:
        backup = write_source(root, src, new_source, error_cls=CodeEditError)
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
        "newline": _NEWLINE_NAMES[src.newline],
        "bom": src.bom,
        "lossless": {"python_cst": True,
                     "roundtrip": python_roundtrip(source)},
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
