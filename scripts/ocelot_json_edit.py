"""ocelot_json_edit — span-preserving, graph-addressed edits for JSON documents.

JSON is a document tree, so the semantic edit targets a **path** (`["nodes", 3,
"attrs", "name"]`) and the adapter replaces only that value's span. The rest of
the file — key order, indentation, long descriptions, surrounding formatting —
is left byte-identical. This is the format-adapter contract from
`ocelot_edit.py`: semantic ops in, transaction out, diff only as a view.

Why not `json.load` + `json.dumps` the whole file? Because a seed manifest is a
large, hand-influenced document; re-rendering it would churn thousands of lines
for a one-value change. This adapter parses JSON with spans, so the edit is
local and the diff view is honest.

Ops:
    set       path, value           replace the value at path
    merge     path, value(object)   set each key of an object at path
    append    path, value           append to the array at path
    delete    path                  delete the value/key at path
    replace_span start_line,start_col,end_line,end_col,text

Path elements are object keys (strings) or array indices (integers).
"""
from __future__ import annotations

import difflib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from scripts.ocelot_code_edit import (
    CodeEditError,
    FORBIDDEN_SCRIPT_KEYS,
    MAX_SOURCE_BYTES,
)
from scripts.ocelot_edit_txn import (
    check_base,
    encode_text,
    normalize_newlines,
    read_source,
    sha256_bytes,
    write_source,
)
from scripts.ocelot_lossless import LosslessText

_NEWLINE_NAMES = {"\n": "lf", "\r\n": "crlf", "\r": "cr"}

_NUMBER_RE = re.compile(r"-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?")


@dataclass
class JNode:
    kind: str
    start: int
    end: int
    value: Any = None
    members: list[dict[str, Any]] = field(default_factory=list)  # object
    items: list["JNode"] = field(default_factory=list)           # array


class _Parser:
    def __init__(self, text: str):
        self.text = text
        self.i = 0
        self.n = len(text)

    def _ws(self) -> None:
        while self.i < self.n and self.text[self.i] in " \t\r\n":
            self.i += 1

    def parse(self) -> JNode:
        self._ws()
        node = self._value()
        self._ws()
        if self.i != self.n:
            raise CodeEditError(f"trailing JSON content at {self.i}")
        return node

    def _value(self) -> JNode:
        self._ws()
        if self.i >= self.n:
            raise CodeEditError("unexpected end of JSON")
        ch = self.text[self.i]
        if ch == "{":
            return self._object()
        if ch == "[":
            return self._array()
        if ch == '"':
            return self._string()
        if self.text.startswith("true", self.i):
            self.i += 4
            return JNode("true", self.i - 4, self.i, True)
        if self.text.startswith("false", self.i):
            self.i += 5
            return JNode("false", self.i - 5, self.i, False)
        if self.text.startswith("null", self.i):
            self.i += 4
            return JNode("null", self.i - 4, self.i, None)
        m = _NUMBER_RE.match(self.text, self.i)
        if m:
            self.i = m.end()
            raw = m.group(0)
            return JNode("number", m.start(), m.end(),
                         float(raw) if any(c in raw for c in ".eE") else int(raw))
        raise CodeEditError(f"bad JSON value at {self.i}")

    def _string(self) -> JNode:
        start = self.i
        try:
            value, end = json.decoder.scanstring(self.text, self.i + 1)
        except ValueError as e:
            raise CodeEditError(f"bad JSON string at {start}: {e}") from e
        self.i = end
        return JNode("string", start, end, value)

    def _object(self) -> JNode:
        start = self.i
        self.i += 1
        members: list[dict[str, Any]] = []
        self._ws()
        if self.i < self.n and self.text[self.i] == "}":
            self.i += 1
            return JNode("object", start, self.i, {}, members, [])
        while True:
            self._ws()
            key_start = self.i
            key_node = self._string()
            key = key_node.value
            self._ws()
            if self.i >= self.n or self.text[self.i] != ":":
                raise CodeEditError(f"expected ':' after JSON key at {self.i}")
            self.i += 1
            self._ws()
            val = self._value()
            members.append({"key": key, "key_start": key_start,
                            "value": val})
            self._ws()
            if self.i < self.n and self.text[self.i] == ",":
                self.i += 1
                continue
            if self.i < self.n and self.text[self.i] == "}":
                self.i += 1
                break
            raise CodeEditError(f"expected ',' or '}}' at {self.i}")
        return JNode("object", start, self.i,
                     {m["key"]: m["value"].value for m in members},
                     members, [])

    def _array(self) -> JNode:
        start = self.i
        self.i += 1
        items: list[JNode] = []
        self._ws()
        if self.i < self.n and self.text[self.i] == "]":
            self.i += 1
            return JNode("array", start, self.i, [], [], items)
        while True:
            items.append(self._value())
            self._ws()
            if self.i < self.n and self.text[self.i] == ",":
                self.i += 1
                continue
            if self.i < self.n and self.text[self.i] == "]":
                self.i += 1
                break
            raise CodeEditError(f"expected ',' or ']' at {self.i}")
        return JNode("array", start, self.i,
                     [i.value for i in items], [], items)


def _get(node: JNode, path: list[Any]) -> JNode:
    cur = node
    for part in path:
        if cur.kind == "object":
            for m in cur.members:
                if m["key"] == part:
                    cur = m["value"]
                    break
            else:
                raise CodeEditError(f"no JSON key {part!r} at path {path!r}")
        elif cur.kind == "array":
            if not isinstance(part, int) or part < 0 or part >= len(cur.items):
                raise CodeEditError(f"bad JSON index {part!r} at path {path!r}")
            cur = cur.items[part]
        else:
            raise CodeEditError(f"cannot descend into {cur.kind} at {part!r}")
    return cur


def _line_offsets(text: str) -> list[int]:
    out = [0]
    for i, ch in enumerate(text):
        if ch == "\n":
            out.append(i + 1)
    return out


def _offset(offsets: list[int], lineno: int, col: int) -> int:
    return offsets[max(0, lineno - 1)] + max(0, col)


def _indent_unit(text: str) -> str:
    for line in text.splitlines()[1:]:
        stripped = line.lstrip(" \t")
        if stripped and len(stripped) != len(line):
            return line[:len(line) - len(stripped)]
    return "  "


def _base_indent(text: str, at: int) -> str:
    start = text.rfind("\n", 0, at) + 1
    line = text[start:at]
    return line[:len(line) - len(line.lstrip(" \t"))]


def _render(value: Any, unit: str, base: str) -> str:
    body = json.dumps(value, indent=unit, ensure_ascii=False)
    if "\n" not in body:
        return body
    return body.replace("\n", "\n" + base)


def _apply_ops(source: str, ops: list[dict[str, Any]],
               newline: str = "\n") -> tuple[str, list[dict[str, Any]]]:
    root = _Parser(source).parse()
    unit = _indent_unit(source)
    edits: list[tuple[int, int, str, dict[str, Any]]] = []
    changes: list[dict[str, Any]] = []

    for op in ops:
        if not isinstance(op, dict):
            raise CodeEditError("each op must be an object")
        kind = str(op.get("op") or "").strip()
        path = op.get("path")
        if kind != "replace_span" and not isinstance(path, list):
            raise CodeEditError(f"{kind}: path must be a list")
        if kind == "set":
            target = _get(root, path)
            base = _base_indent(source, target.start)
            text = _render(op.get("value"), unit, base)
            edits.append((target.start, target.end, text, op))
            changes.append({"op": kind, "path": path,
                            "summary": f"set {len(text)} chars"})
        elif kind == "merge":
            target = _get(root, path)
            if target.kind != "object":
                raise CodeEditError("merge target must be an object")
            value = op.get("value")
            if not isinstance(value, dict):
                raise CodeEditError("merge value must be an object")
            for k, v in value.items():
                member = next((m for m in target.members if m["key"] == k), None)
                if member is not None:
                    node = member["value"]
                    base = _base_indent(source, node.start)
                    edits.append((node.start, node.end,
                                  _render(v, unit, base), op))
                else:
                    # Insert before the closing brace.
                    if target.members:
                        at = target.members[-1]["value"].end
                        base = _base_indent(source, target.members[-1]["key_start"])
                        text = (",\n" + base + json.dumps(k) + ": "
                                + _render(v, unit, base))
                    else:
                        at = target.start + 1
                        base = _base_indent(source, target.start) + unit
                        text = ("\n" + base + json.dumps(k) + ": "
                                + _render(v, unit, base) + "\n"
                                + _base_indent(source, target.start))
                    edits.append((at, at, text, op))
            changes.append({"op": kind, "path": path,
                            "summary": f"merge keys {sorted(value)}"})
        elif kind == "append":
            target = _get(root, path)
            if target.kind != "array":
                raise CodeEditError("append target must be an array")
            base = (_base_indent(source, target.items[-1].start)
                    if target.items else
                    _base_indent(source, target.start) + unit)
            text = _render(op.get("value"), unit, base)
            if target.items:
                at = target.items[-1].end
                insert = ",\n" + base + text
            else:
                at = target.start + 1
                parent = _base_indent(source, target.start)
                insert = "\n" + base + text + "\n" + parent
            edits.append((at, at, insert, op))
            changes.append({"op": kind, "path": path,
                            "summary": "append array item"})
        elif kind == "delete":
            if not path:
                raise CodeEditError("delete needs a non-empty path")
            parent_path, last = path[:-1], path[-1]
            parent = _get(root, parent_path)
            if parent.kind == "array":
                idx = int(last)
                if idx < 0 or idx >= len(parent.items):
                    raise CodeEditError(f"bad array index {idx}")
                item = parent.items[idx]
                if idx > 0:
                    start = parent.items[idx - 1].end
                    end = item.end
                    text = ""
                elif len(parent.items) > 1:
                    start = item.start
                    end = parent.items[1].start
                    text = ""
                else:
                    start, end, text = item.start, item.end, ""
                edits.append((start, end, text, op))
            elif parent.kind == "object":
                for i, m in enumerate(parent.members):
                    if m["key"] != last:
                        continue
                    if i > 0:
                        start = parent.members[i - 1]["value"].end
                        end = m["value"].end
                    elif len(parent.members) > 1:
                        start = m["key_start"]
                        end = parent.members[1]["key_start"]
                    else:
                        start = m["key_start"]
                        end = m["value"].end
                    edits.append((start, end, "", op))
                    break
                else:
                    raise CodeEditError(f"no JSON key {last!r}")
            else:
                raise CodeEditError("delete parent must be object/array")
            changes.append({"op": kind, "path": path, "summary": "delete"})
        elif kind == "replace_span":
            offsets = _line_offsets(source)
            try:
                start = _offset(offsets, int(op["start_line"]),
                                int(op.get("start_col", 0)))
                end = _offset(offsets, int(op["end_line"]),
                              int(op.get("end_col", 0)))
            except (KeyError, TypeError, ValueError) as e:
                raise CodeEditError(
                    "replace_span needs start_line/start_col/end_line/end_col") from e
            if start < 0 or end < start or end > len(source):
                raise CodeEditError("replace_span out of range")
            edits.append((start, end, str(op.get("text") or ""), op))
            changes.append({"op": kind, "summary": f"replace {start}:{end}"})
        else:
            raise CodeEditError(
                f"unknown JSON op {kind!r}; supported: set, merge, append, "
                f"delete, replace_span")

    edits.sort(key=lambda e: (e[0], e[1]), reverse=True)
    last_start = None
    for start, end, text, _op in edits:
        if last_start is not None and end > last_start:
            raise CodeEditError("overlapping JSON edits in one script")
        last_start = start
    from scripts.ocelot_lossless import LosslessText
    doc = LosslessText.from_lines(source)
    for start, end, text, _op in edits:
        doc.replace(start, end, normalize_newlines(text, newline))
    return doc.render(), changes


def apply_json_edit_script(root: str | Path, script: dict[str, Any], *,
                           write: bool = False) -> dict[str, Any]:
    if not isinstance(script, dict):
        raise CodeEditError("edit script must be an object")
    for key in FORBIDDEN_SCRIPT_KEYS:
        if key in script:
            raise CodeEditError(
                f"raw {key!r} input is refused: send semantic path ops; a diff "
                f"is only an output view")
    root = Path(root).resolve()
    file = str(script.get("file") or "").strip()
    if not file:
        raise CodeEditError("edit script needs file")
    path = (root / file).resolve()
    try:
        path.relative_to(root)
    except ValueError as e:
        raise CodeEditError("file escapes the repo root") from e
    if path.suffix.lower() != ".json":
        raise CodeEditError("json adapter only handles .json")
    src = read_source(root, file, suffixes=(".json",),
                      max_bytes=MAX_SOURCE_BYTES, error_cls=CodeEditError)
    source = src.text
    base_sha = src.sha256
    check_base(src, script.get("base_sha256"), CodeEditError)
    ops = script.get("ops")
    if not isinstance(ops, list) or not ops:
        raise CodeEditError("edit script needs a non-empty ops list")

    new_source, changes = _apply_ops(source, ops, newline=src.newline)
    try:
        parsed = json.loads(new_source)
    except json.JSONDecodeError as e:
        raise CodeEditError(f"edit would produce invalid JSON: {e}") from e
    if isinstance(parsed, dict) and "id" in parsed and "version" in parsed:
        if not str(parsed.get("id") or "").strip():
            raise CodeEditError("seed manifest id became empty")
    new_sha = sha256_bytes(encode_text(src, new_source))

    diff_lines = list(difflib.unified_diff(
        source.splitlines(keepends=True),
        new_source.splitlines(keepends=True),
        fromfile=f"a/{file}", tofile=f"b/{file}",
    ))
    applied = False
    backup = None
    if write:
        backup = write_source(root, src, new_source, error_cls=CodeEditError)
        applied = True

    return {
        "ok": True,
        "file": file,
        "applied": applied,
        "format": "json",
        "base_sha256": base_sha,
        "new_sha256": new_sha,
        "before": {"lines": len(source.splitlines()), "sha256": base_sha},
        "after": {"lines": len(new_source.splitlines()), "sha256": new_sha},
        "ops": ops,
        "changes": changes,
        "diff_view": "".join(diff_lines[:400]),
        "diff_note": ("a unified diff is a rendered view for humans; the "
                      "canonical record is the op list above"),
        "backup": str(backup) if backup else None,
        "newline": _NEWLINE_NAMES[src.newline],
        "bom": src.bom,
        "lossless": {
            "line_leaves": True,
            "roundtrip": LosslessText.from_lines(source).render() == source,
        },
        "graph_stale": bool(applied),
    }


def outline_json(source: str, *, max_items: int = 40) -> dict[str, Any]:
    """A compact JSON document outline: top-level shape + seed manifest keys."""
    try:
        obj = json.loads(source)
    except json.JSONDecodeError as e:
        return {"path": "", "lines": "outline",
                "text": f"invalid JSON: {e}", "kind": "json",
                "estimated_tokens": 8}
    lines: list[str] = ["# json outline"]
    if isinstance(obj, dict):
        for k in list(obj)[:max_items]:
            v = obj[k]
            if isinstance(v, list):
                lines.append(f"- {k}: list[{len(v)}]")
                if v and isinstance(v[0], dict):
                    keys = ", ".join(list(v[0])[:8])
                    lines.append(f"    first item keys: {keys}")
            elif isinstance(v, dict):
                lines.append(f"- {k}: object{{{', '.join(list(v)[:8])}}}")
            else:
                text = str(v)
                lines.append(f"- {k}: {text[:120]}")
    elif isinstance(obj, list):
        lines.append(f"- list[{len(obj)}]")
    text = "\n".join(lines)
    return {"path": "", "lines": "outline", "text": text, "kind": "json",
            "estimated_tokens": max(1, len(text) // 4)}
