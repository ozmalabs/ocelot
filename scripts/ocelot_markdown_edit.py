"""ocelot_markdown_edit — graph-addressed structural edits for Markdown.

The Markdown twin of `ocelot_code_edit.py`. The canonical change is a list of
semantic operations against the document's block graph (sections, bodies,
frontmatter, spans), not a text diff. A diff is emitted only as `diff_view`.

Markdown block model (v0):

    Frontmatter?  (a leading `--- ... ---` block)
    Section       (a heading line + its direct body + nested subsections)
      body        (paragraphs / lists / tables / fenced code, kept as text)
      Section...  (nested headings)

Operations target a section by title (`"Honest limits"` or
`"## Honest limits"`) or by a heading path (`["Editing", "Formats"]`). The
renderer preserves the text outside the edited spans exactly; this is a
span-preserving structural editor, not a Markdown re-formatter.

Ops:
    replace_section        replace heading + body + nested subsections
    replace_section_body   replace direct body, keep the heading
    append_to_section      append at the end of the whole section
    insert_section_before  insert a new section before the target
    insert_section_after   insert a new section after the target
    delete_section         remove the whole section
    replace_frontmatter    replace (or insert) the leading frontmatter block
    replace_span           replace an explicit line/col span

A raw diff/patch input is refused. All text carried by an op is opaque
Markdown; the editor validates fence parity and section structure, not prose.
"""
from __future__ import annotations

import difflib
import re
from dataclasses import dataclass
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

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
_FENCE_RE = re.compile(r"^\s*(```|~~~)")


@dataclass
class Section:
    level: int
    title: str
    start: int          # char offset of the heading line start
    heading_end: int    # char offset just after the heading line
    body_end: int       # before the next heading of ANY level
    section_end: int    # before the next heading of level <= this one
    start_line: int
    end_line: int


def _line_offsets(source: str) -> list[int]:
    offsets = [0]
    for i, ch in enumerate(source):
        if ch == "\n":
            offsets.append(i + 1)
    return offsets


def _offset(offsets: list[int], lineno: int, col: int) -> int:
    return offsets[max(0, lineno - 1)] + max(0, col)


def _line_end(offsets: list[int], lineno: int, n: int) -> int:
    return offsets[lineno] if lineno < len(offsets) else n


def headings(source: str) -> list[Section]:
    """All headings outside fenced code blocks, with their section spans."""
    offsets = _line_offsets(source)
    n = len(source)
    raw: list[dict[str, Any]] = []
    in_fence = False
    fence = ""
    for i, line in enumerate(source.splitlines(keepends=True), start=1):
        m = _FENCE_RE.match(line)
        if m:
            token = m.group(1)
            if not in_fence:
                in_fence, fence = True, token
            elif token == fence:
                in_fence, fence = False, ""
            continue
        if in_fence:
            continue
        hm = _HEADING_RE.match(line.rstrip("\n"))
        if not hm:
            continue
        raw.append({
            "level": len(hm.group(1)),
            "title": hm.group(2).strip(),
            "start": offsets[i - 1],
            "heading_end": _line_end(offsets, i, n),
            "start_line": i,
            "end_line": i,
        })
    out: list[Section] = []
    for idx, h in enumerate(raw):
        body_end = raw[idx + 1]["start"] if idx + 1 < len(raw) else n
        section_end = n
        for nxt in raw[idx + 1:]:
            if nxt["level"] <= h["level"]:
                section_end = nxt["start"]
                break
        out.append(Section(h["level"], h["title"], h["start"],
                           h["heading_end"], body_end, section_end,
                           h["start_line"], h["end_line"]))
    return out


def outline_markdown(source: str, *, max_headings: int = 60) -> dict[str, Any]:
    hs = headings(source)
    lines = [f"# markdown outline ({len(hs)} headings)"]
    for h in hs:
        lines.append(f"{'  ' * (h.level - 1)}{'#' * h.level} {h.title}"
                     f"  # L{h.start_line}")
    # Fenced-code languages, a useful cheap signal for docs.
    langs: list[str] = []
    for line in source.splitlines():
        m = _FENCE_RE.match(line)
        if m:
            rest = line.strip()[3:].strip()
            if rest and rest not in langs:
                langs.append(rest)
    if langs:
        lines.append("code blocks: " + ", ".join(langs[:12]))
    text = "\n".join(lines[:max_headings + 2])
    return {"path": "", "lines": "outline", "text": text,
            "kind": "markdown", "estimated_tokens": max(1, len(text) // 4)}


def _find_section(source: str, op: dict[str, Any]) -> Section:
    hs = headings(source)
    path = op.get("path")
    if isinstance(path, list) and path:
        wanted = [str(p).strip().lstrip("#").strip().lower() for p in path]
        cur: Section | None = None
        for want in wanted:
            candidates = [h for h in hs
                          if h.title.lower() == want
                          and (cur is None or
                               (cur.start < h.start < cur.section_end
                                and h.level > cur.level))]
            if not candidates:
                raise CodeEditError(
                    f"no heading path match {path!r}; available: "
                    + ", ".join(h.title for h in hs[:20]))
            cur = candidates[0]
        assert cur is not None
        return cur
    target = str(op.get("section") or "").strip()
    if not target:
        raise CodeEditError("section op needs `section` or `path`")
    norm = target.lstrip("#").strip().lower()
    matches = [h for h in hs if h.title.lower() == norm]
    if not matches:
        raise CodeEditError(
            f"no section {target!r}; available: "
            + ", ".join(h.title for h in hs[:20]))
    if len(matches) > 1:
        raise CodeEditError(
            f"section {target!r} is ambiguous; use `path` with a heading "
            f"ancestor, or a fuller heading")
    return matches[0]


def _ensure_blank(text: str) -> str:
    if not text:
        return ""
    return text if text.endswith("\n") else text + "\n"


def _section_block(level: int, title: str, body: str) -> str:
    title = title.strip()
    if not title:
        raise CodeEditError("new section needs a non-empty title")
    body = (body or "").strip("\n")
    return f"{'#' * max(1, min(6, int(level)))} {title}\n\n{body}\n\n"


def _apply_ops(source: str, ops: list[dict[str, Any]],
               newline: str = "\n") -> tuple[str, list[dict[str, Any]]]:
    edits: list[tuple[int, int, str, dict[str, Any]]] = []
    changes: list[dict[str, Any]] = []

    for op in ops:
        if not isinstance(op, dict):
            raise CodeEditError("each op must be an object")
        kind = str(op.get("op") or "").strip()
        if kind == "replace_section":
            s = _find_section(source, op)
            text = _ensure_blank(str(op.get("text") or ""))
            if not text.lstrip().startswith("#"):
                raise CodeEditError(
                    "replace_section text must include the heading (start with #); "
                    "use replace_section_body to keep the heading")
            edits.append((s.start, s.section_end, text, op))
            changes.append({"op": kind, "section": s.title,
                            "lines": [s.start_line, s.end_line],
                            "summary": "replace whole section"})
        elif kind == "replace_section_body":
            s = _find_section(source, op)
            body = str(op.get("text") or "").strip("\n")
            rendered = (body + "\n") if body else ""
            edits.append((s.heading_end, s.body_end, rendered, op))
            changes.append({"op": kind, "section": s.title,
                            "summary": "replace section body"})
        elif kind == "append_to_section":
            s = _find_section(source, op)
            body = str(op.get("text") or "").strip("\n")
            if not body:
                continue
            rendered = ("\n" if source[s.section_end - 1:s.section_end] != "\n" else "") \
                + body + "\n"
            edits.append((s.section_end, s.section_end, rendered, op))
            changes.append({"op": kind, "section": s.title,
                            "summary": "append to section"})
        elif kind in ("insert_section_before", "insert_section_after"):
            s = _find_section(source, op)
            level = int(op.get("level") or s.level)
            block = _section_block(level, str(op.get("title") or ""),
                                   str(op.get("text") or ""))
            at = s.start if kind == "insert_section_before" else s.section_end
            edits.append((at, at, block, op))
            changes.append({"op": kind, "section": s.title,
                            "summary": f"insert section {op.get('title')!r}"})
        elif kind == "delete_section":
            s = _find_section(source, op)
            edits.append((s.start, s.section_end, "", op))
            changes.append({"op": kind, "section": s.title,
                            "lines": [s.start_line, s.end_line],
                            "summary": "delete section"})
        elif kind == "replace_frontmatter":
            body = str(op.get("text") or "").strip("\n")
            rendered = f"---\n{body}\n---\n" if body else ""
            if source.startswith("---\n"):
                end = source.find("\n---", 4)
                if end < 0:
                    raise CodeEditError("frontmatter is not closed")
                end += len("\n---")
                if source[end:end + 1] == "\n":
                    end += 1
                edits.append((0, end, rendered, op))
            else:
                if source and not source.startswith("\n"):
                    rendered += "\n"
                edits.append((0, 0, rendered, op))
            changes.append({"op": kind, "summary": "replace frontmatter"})
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
                f"unknown markdown op {kind!r}; supported: replace_section, "
                f"replace_section_body, append_to_section, "
                f"insert_section_before, insert_section_after, "
                f"delete_section, replace_frontmatter, replace_span")

    edits.sort(key=lambda e: (e[0], e[1]), reverse=True)
    last_start = None
    for start, end, text, _op in edits:
        if last_start is not None and end > last_start:
            raise CodeEditError("overlapping markdown edits in one script")
        last_start = start
    from scripts.ocelot_lossless import LosslessText
    doc = LosslessText.from_lines(source)
    for start, end, text, _op in edits:
        doc.replace(start, end, normalize_newlines(text, newline))
    return doc.render(), changes


def apply_markdown_edit_script(root: str | Path, script: dict[str, Any], *,
                               write: bool = False) -> dict[str, Any]:
    if not isinstance(script, dict):
        raise CodeEditError("edit script must be an object")
    for key in FORBIDDEN_SCRIPT_KEYS:
        if key in script:
            raise CodeEditError(
                f"raw {key!r} input is refused: send semantic ops over document "
                f"sections; a diff is only an output view")
    root = Path(root).resolve()
    file = str(script.get("file") or "").strip()
    if not file:
        raise CodeEditError("edit script needs file")
    path = (root / file).resolve()
    try:
        path.relative_to(root)
    except ValueError as e:
        raise CodeEditError("file escapes the repo root") from e
    if path.suffix.lower() not in (".md", ".markdown"):
        raise CodeEditError("markdown adapter only handles .md/.markdown")
    src = read_source(root, file, suffixes=(".md", ".markdown"),
                      max_bytes=MAX_SOURCE_BYTES, error_cls=CodeEditError)
    source = src.text
    base_sha = src.sha256
    check_base(src, script.get("base_sha256"), CodeEditError)
    ops = script.get("ops")
    if not isinstance(ops, list) or not ops:
        raise CodeEditError("edit script needs a non-empty ops list")

    new_source, changes = _apply_ops(source, ops, newline=src.newline)
    # Markdown is permissive, but an unclosed fence is a structural break.
    fences = sum(1 for line in new_source.splitlines()
                 if _FENCE_RE.match(line))
    if fences % 2:
        raise CodeEditError("edit would leave an unclosed fenced code block")
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
        "format": "markdown",
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
