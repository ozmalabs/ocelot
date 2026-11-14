"""ocelot_lossless — the byte-for-byte leaf structure under every format.

The edit layer must be able to recreate the original file exactly, including
comments, blank lines, indentation, trailing spaces and line endings. A semantic
AST alone cannot do that. This module supplies the missing layer:

    source <-> ordered leaves

A leaf is a small text fragment (a token, a gap/trivia run, a line). Rendering
is `"".join(leaf.text)` — no formatter, no normalisation. Edits replace a range
of leaves and insert one new leaf; every leaf outside the edit is byte-
identical. The original source is always recoverable from the structure alone.

Python uses a token-graph reader (`tokenize`) so code leaves are tokens and
comments/whitespace are explicit trivia leaves. Markdown and JSON can use line
leaves (their block/token metadata lives beside the leaves); both round-trip
exactly. A format adapter that cannot round-trip its source must refuse to edit.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


class LosslessError(ValueError):
    pass


@dataclass
class Leaf:
    kind: str
    text: str


class LosslessText:
    """An ordered leaf sequence whose render is the exact source text."""

    def __init__(self, leaves: Iterable[Leaf], source: str | None = None):
        self.leaves = list(leaves)
        self._source = source if source is not None else self.render()
        if source is not None and self.render() != source:
            raise LosslessError("leaf structure does not round-trip the source")

    # -- constructors ------------------------------------------------------ #
    @classmethod
    def from_lines(cls, source: str) -> "LosslessText":
        lines = source.splitlines(keepends=True)
        return cls([Leaf("line", line) for line in lines], source)

    @classmethod
    def from_python(cls, source: str) -> "LosslessText":
        """The Python bridge to `domains.py_cst_ingest.python_cst_leaves` /
        `ts_ingest`'s `CstNode` + `flat_text` contract: token leaves plus
        explicit trivia leaves, in document order."""
        from domains.py_cst_ingest import python_cst_leaves
        try:
            records = python_cst_leaves(source)
        except ValueError as e:
            raise LosslessError(str(e)) from e
        return cls([Leaf(r["kind"], r["text"]) for r in records], source)

    # -- rendering --------------------------------------------------------- #
    def render(self) -> str:
        return "".join(leaf.text for leaf in self.leaves)

    def __len__(self) -> int:
        return sum(len(leaf.text) for leaf in self.leaves)

    # -- edits ------------------------------------------------------------- #
    def replace(self, start: int, end: int, text: str) -> None:
        """Replace source range [start,end) with `text`, preserving all leaves
        outside the range. Insertions are `start == end`."""
        total = len(self)
        if start < 0 or end < start or end > total:
            raise LosslessError(f"range {start}:{end} outside 0:{total}")
        out: list[Leaf] = []
        pos = 0
        inserted = False
        for leaf in self.leaves:
            lstart = pos
            lend = pos + len(leaf.text)
            pos = lend
            # Entirely before the edit.
            if lend <= start and not (start == end == lend):
                out.append(leaf)
                continue
            # Entirely after the edit.
            if lstart >= end and not (start == end == lstart):
                if not inserted:
                    if text:
                        out.append(Leaf("replacement", text))
                    inserted = True
                out.append(leaf)
                continue
            # Overlap (or boundary insertion).
            if lstart < start:
                out.append(Leaf(leaf.kind, leaf.text[:start - lstart]))
            if not inserted:
                if text:
                    out.append(Leaf("replacement", text))
                inserted = True
            if lend > end:
                out.append(Leaf(leaf.kind, leaf.text[end - lstart:]))
        if not inserted:
            if text:
                out.append(Leaf("replacement", text))
        self.leaves = out
        self._source = self.render()

    def insert(self, at: int, text: str) -> None:
        self.replace(at, at, text)

    def delete(self, start: int, end: int) -> None:
        self.replace(start, end, "")

    def cst_records(self) -> list[dict[str, object]]:
        """The current leaves in the same shape `py_cst_ingest` emits."""
        out: list[dict[str, object]] = []
        pos = 0
        for leaf in self.leaves:
            out.append({"kind": leaf.kind, "text": leaf.text,
                        "start": pos, "end": pos + len(leaf.text),
                        "child_index": len(out)})
            pos += len(leaf.text)
        return out

    def stats(self) -> dict[str, int]:
        kinds: dict[str, int] = {}
        for leaf in self.leaves:
            kinds[leaf.kind] = kinds.get(leaf.kind, 0) + 1
        return {"leaves": len(self.leaves), "chars": len(self), **kinds}


def python_roundtrip(source: str) -> bool:
    try:
        return LosslessText.from_python(source).render() == source
    except LosslessError:
        return False


def text_roundtrip(source: str) -> bool:
    return LosslessText.from_lines(source).render() == source
