"""ocelot_cst_edit — graph-addressed structural edits for Rust/Lua source.

DEV TOOLING, NOT AGENT RUNTIME. This module is the Rust/Lua arm of the edit
layer: it edits a file by naming **CST nodes** in the `CstNode` graph produced
by `domains/ts_ingest.py`, not by accepting a text patch. The canonical record
of a change is the semantic op list; `diff_view` is only a rendered view for
humans. Raw `diff`/`patch` input is refused, exactly as in the Python, JSON and
Markdown adapters.

The graph contract is already in the substrate:

  * every CST node is a `CstNode` with `kind`, `field`, `child_index`, `named`;
  * leaves (nodes with no children) carry their exact source `text`;
  * an interior node's text is the concatenation of its children's text;
  * a node's source range is computed by walking its leaves in
    `child_index` order.

A path is a sequence of child positions from the root:

    child[2].child[0]

Each `child[N]` selects the N-th child after sorting by `child_index`. Because
the leaves partition the file byte-for-byte, editing a subtree's range leaves
every other leaf untouched (comments, blank lines, indentation, trailing
spaces and line endings included).

When tree-sitter and the Rust/Lua grammar are importable, the graph comes from
`domains.ts_ingest.ingest_source`. Without them, the adapter also accepts a
**synthetic** `CstNode`
graph supplied by the caller in `script["cst_graph"]` (a nested text tree, a
serialized node/edge graph, or a `CstGraph` instance). The tests use that path;
it is not a fake parser, it is the same graph contract with the caller as the
world adapter.

Ops (v0):

    replace_node          path, text
    insert_before_node    path, text
    insert_after_node     path, text
    delete_node           path
    wrap_node             path, prefix, suffix
    replace_span          char/byte/line span, text

Transaction: preview by default; `write=True` backs up under
`var/ocelot_dev_edits/backups/`, writes atomically, and returns before/after
SHA-256. Refusals raise `scripts.ocelot_code_edit.CodeEditError` (via
`CstEditError`); there is no silent text-patch fallback.
"""
from __future__ import annotations

import difflib
import importlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from scripts.ocelot_code_edit import (
    FORBIDDEN_SCRIPT_KEYS,
    MAX_SOURCE_BYTES,
    CodeEditError,
)
from scripts.ocelot_edit_txn import (
    check_base,
    encode_text,
    normalize_newlines,
    read_source,
    sha256_bytes,
    write_source,
)
from scripts.ocelot_lossless import Leaf, LosslessError, LosslessText

_NEWLINE_NAMES = {"\n": "lf", "\r\n": "crlf", "\r": "cr"}

# Mirrors domains.ts_ingest._GRAMMARS. Kept here so this module can report an
# honest backend status without importing tree_sitter at module import time.
_GRAMMAR_MODULES = {
    "rust": "tree_sitter_rust",
    "lua": "tree_sitter_lua",
}

# `child[2]`, `children[2]` and `[2]` all name the same child position.
_PATH_SEGMENT_RE = re.compile(r"^(?:child|children)?\[(\d+)\]$")

# Kinds that look like whole statements/items. `delete_node` uses this only to
# decide whether it is safe to consume the line's indentation and one trailing
# blank line; it is a formatting heuristic, not a parse decision.
_STATEMENT_KINDS = frozenset({
    "attribute_item",
    "break_statement",
    "class_definition",
    "const_item",
    "declaration",
    "do_statement",
    "empty_statement",
    "enum_item",
    "expression_statement",
    "for_statement",
    "foreign_mod_item",
    "function",
    "function_declaration",
    "function_definition",
    "function_item",
    "goto_statement",
    "if_statement",
    "impl_item",
    "inner_attribute_item",
    "item",
    "label_statement",
    "let_declaration",
    "local_function",
    "local_variable_declaration",
    "mod_item",
    "repeat_statement",
    "return_expression",
    "return_statement",
    "statement",
    "static_item",
    "struct_item",
    "trait_item",
    "type_item",
    "use_declaration",
    "variable_declaration",
    "while_statement",
})
_STATEMENT_SUFFIXES = ("_declaration", "_definition", "_item", "_statement")


class CstEditError(CodeEditError):
    """A refused CST edit: bad path, stale base, bad graph, raw diff, ..."""


# --------------------------------------------------------------------------- #
# CST graph: a small read-only view over CstNode attrs + child edges.
# --------------------------------------------------------------------------- #
@dataclass
class _Edit:
    start: int
    end: int
    text: str
    target: str


class CstGraph:
    """A read-only `CstNode` graph rooted at one node.

    The graph can be built from a live substrate (the `ts_ingest` path), from a
    nested text tree (the synthetic/test path), or from a serialized
    node/edge dict. Only the `child` edge is used; `child_index` orders
    siblings, exactly as `TableWalker.children` does in `domains/ts_ingest.py`.
    """

    def __init__(self, root: Any, nodes: dict[Any, dict[str, Any]],
                 children: dict[Any, Iterable[Any]] | None = None):
        self.root = root
        self._nodes: dict[Any, dict[str, Any]] = {
            nid: dict(attrs) for nid, attrs in nodes.items()
        }
        if root not in self._nodes:
            raise CstEditError(f"CST root {root!r} is not in the graph")
        raw_children: dict[Any, list[Any]] = {
            nid: list(kids) for nid, kids in (children or {}).items()
        }
        for parent, kids in raw_children.items():
            if parent not in self._nodes:
                raise CstEditError(
                    f"CST child edge parent {parent!r} is not in the graph")
            for child in kids:
                if child not in self._nodes:
                    raise CstEditError(
                        f"CST child edge target {child!r} is not in the graph")
        self._children: dict[Any, list[Any]] = {}
        for nid in self._nodes:
            kids = raw_children.get(nid, [])
            self._children[nid] = self._ordered(nid, kids)
        self._ranges: dict[Any, tuple[int, int]] | None = None
        self._leaves: list[dict[str, Any]] | None = None

    # ---- construction ----------------------------------------------------- #
    def _ordered(self, parent: Any, kids: list[Any]) -> list[Any]:
        decorated: list[tuple[int, Any]] = []
        seen: set[int] = set()
        for position, child in enumerate(kids):
            attrs = self._nodes[child]
            index = attrs.get("child_index")
            if index is None:
                index = position
            try:
                index = int(index)
            except (TypeError, ValueError) as e:
                raise CstEditError(
                    f"CST child_index {attrs.get('child_index')!r} on "
                    f"{child!r} is not an integer") from e
            if index in seen:
                raise CstEditError(
                    f"duplicate child_index {index} under CST node {parent!r}")
            seen.add(index)
            decorated.append((index, child))
        decorated.sort(key=lambda item: item[0])
        if [index for index, _ in decorated] != list(range(len(kids))):
            raise CstEditError(
                f"CST children of {parent!r} do not have contiguous "
                f"child_index values: {[i for i, _ in decorated]}")
        return [child for _, child in decorated]

    @classmethod
    def from_substrate(cls, substrate: Any, root: Any) -> "CstGraph":
        """Wrap a live substrate's `CstNode`/`child` graph from `root`."""
        nodes: dict[Any, dict[str, Any]] = {}
        children: dict[Any, list[Any]] = {}
        active: set[Any] = set()

        def walk(nid: Any) -> None:
            if nid in nodes:
                return
            if nid in active:
                raise CstEditError(f"cycle in CST child edges at {nid!r}")
            info = substrate.node(nid)
            if not info:
                raise CstEditError(f"CST node {nid!r} is not in the substrate")
            active.add(nid)
            nodes[nid] = dict(info.get("attrs") or {})
            kids = list(substrate.neighbours(nid, "child"))
            children[nid] = kids
            for child in kids:
                walk(child)
            active.remove(nid)

        walk(root)
        return cls(root, nodes, children)

    @classmethod
    def from_nested(cls, nested: dict[str, Any]) -> "CstGraph":
        """Build a graph from a nested text tree.

        Shape (all keys except `kind`/`text` are optional):

            {"kind": "source_file", "children": [
                {"kind": "whitespace", "text": "  "},
                {"kind": "identifier", "text": "x"},
            ]}

        Leaves MUST carry `text`; interior nodes MUST NOT (their text is the
        concatenation of their children). This is the test/offline path.
        """
        if not isinstance(nested, dict):
            raise CstEditError("nested CST must be an object")
        nodes: dict[int, dict[str, Any]] = {}
        children: dict[int, list[int]] = {}
        counter = 0

        def build(obj: dict[str, Any], position: int) -> int:
            nonlocal counter
            if not isinstance(obj, dict):
                raise CstEditError("each nested CST node must be an object")
            kind = obj.get("kind")
            if not isinstance(kind, str) or not kind:
                raise CstEditError("each nested CST node needs a non-empty kind")
            nid = counter
            counter += 1
            attrs: dict[str, Any] = {
                key: value
                for key, value in obj.items()
                if key not in ("children", "id")
            }
            attrs.setdefault("field", "")
            attrs.setdefault("child_index", position)
            attrs.setdefault("named", True)
            attrs.setdefault("origin", "synthetic_cst")
            kids = obj.get("children", [])
            if kids is None:
                kids = []
            if not isinstance(kids, list):
                raise CstEditError(
                    f"nested CST node {kind!r} children must be a list")
            if kids:
                if "text" in attrs:
                    raise CstEditError(
                        f"interior CST node {kind!r} carries text; leaves only")
                nodes[nid] = attrs
                children[nid] = [build(child, i)
                                 for i, child in enumerate(kids)]
            else:
                if "text" not in attrs:
                    raise CstEditError(
                        f"synthetic CST leaf {kind!r} must carry text")
                if not isinstance(attrs["text"], str):
                    raise CstEditError(
                        f"synthetic CST leaf {kind!r} text must be a string")
                nodes[nid] = attrs
                children[nid] = []
            return nid

        root = build(nested, -1)
        return cls(root, nodes, children)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CstGraph":
        """Accept a nested tree or a serialized node/edge graph.

        Serialized shape:

            {"root": 0,
             "nodes": [{"id": 0, "attrs": {...}, "children": [1, 2]}, ...],
             "edges": [{"src": 0, "type": "child", "tgt": 1}, ...]}

        `nodes` may also be an id -> attrs mapping. `edges` wins over inline
        `children` when both are present.
        """
        if not isinstance(data, dict):
            raise CstEditError("cst_graph must be an object or CstGraph")
        if "nodes" not in data:
            return cls.from_nested(data)

        raw_nodes = data.get("nodes")
        nodes: dict[Any, dict[str, Any]] = {}
        inline_children: dict[Any, list[Any]] = {}
        if isinstance(raw_nodes, dict):
            for nid, attrs in raw_nodes.items():
                if not isinstance(attrs, dict):
                    raise CstEditError(f"CST node {nid!r} attrs must be an object")
                nodes[nid] = dict(attrs.get("attrs", attrs))
        elif isinstance(raw_nodes, list):
            for item in raw_nodes:
                if not isinstance(item, dict):
                    raise CstEditError("serialized CST nodes must be objects")
                if "id" not in item:
                    raise CstEditError("serialized CST node needs an id")
                nid = item["id"]
                attrs = item.get("attrs")
                if attrs is None:
                    attrs = {
                        key: value
                        for key, value in item.items()
                        if key not in ("id", "type", "children", "attrs")
                    }
                if not isinstance(attrs, dict):
                    raise CstEditError(f"CST node {nid!r} attrs must be an object")
                nodes[nid] = dict(attrs)
                if "children" in item:
                    inline_children[nid] = list(item["children"])
        else:
            raise CstEditError("serialized CST nodes must be a list or object")

        edges = data.get("edges") or []
        if edges:
            edge_children: dict[Any, list[Any]] = {}
            for edge in edges:
                if not isinstance(edge, dict):
                    raise CstEditError("serialized CST edges must be objects")
                if edge.get("type") != "child":
                    continue
                edge_children.setdefault(edge.get("src"), []).append(
                    edge.get("tgt"))
            inline_children = edge_children

        root = data.get("root")
        if root is None:
            targets = {
                child
                for kids in inline_children.values()
                for child in kids
            }
            candidates = [nid for nid in nodes if nid not in targets]
            if len(candidates) != 1:
                raise CstEditError(
                    "serialized CST needs an explicit root (or exactly one "
                    "unparented node)")
            root = candidates[0]
        return cls(root, nodes, inline_children)

    # ---- mechanical reads ------------------------------------------------- #
    def attrs(self, nid: Any) -> dict[str, Any]:
        return self._nodes[nid]

    def kind(self, nid: Any) -> str:
        return str(self._nodes[nid].get("kind") or "")

    def children(self, nid: Any) -> list[Any]:
        return list(self._children[nid])

    @property
    def node_count(self) -> int:
        return len(self._nodes)

    @property
    def leaf_count(self) -> int:
        self._index()
        return len(self._leaves or [])

    def _index(self) -> None:
        if self._ranges is not None:
            return
        ranges: dict[Any, tuple[int, int]] = {}
        leaves: list[dict[str, Any]] = []
        cursor = 0
        active: set[Any] = set()

        def walk(nid: Any) -> None:
            nonlocal cursor
            if nid in active:
                raise CstEditError(f"cycle in CST child edges at {nid!r}")
            active.add(nid)
            attrs = self._nodes[nid]
            kids = self._children[nid]
            if kids:
                if "text" in attrs:
                    raise CstEditError(
                        f"interior CST node {nid!r} ({attrs.get('kind')!r}) "
                        f"carries text; leaves only")
                start = cursor
                for child in kids:
                    walk(child)
                end = cursor
            else:
                text = attrs.get("text")
                if not isinstance(text, str):
                    raise CstEditError(
                        f"CST leaf {nid!r} ({attrs.get('kind')!r}) has no text")
                start = cursor
                cursor += len(text)
                end = cursor
                leaves.append({
                    "kind": str(attrs.get("kind") or "leaf"),
                    "text": text,
                    "start": start,
                    "end": end,
                    "child_index": len(leaves),
                })
            ranges[nid] = (start, end)
            active.remove(nid)

        walk(self.root)
        if len(ranges) != len(self._nodes):
            unreachable = [nid for nid in self._nodes if nid not in ranges]
            raise CstEditError(
                f"CST graph has unreachable nodes: {unreachable[:8]!r}")
        self._ranges = ranges
        self._leaves = leaves

    def ranges(self) -> dict[Any, tuple[int, int]]:
        self._index()
        assert self._ranges is not None
        return self._ranges

    def leaf_records(self) -> list[dict[str, Any]]:
        self._index()
        assert self._leaves is not None
        return list(self._leaves)

    def flat_text(self, nid: Any) -> str:
        """The `TableWalker.flat_text` identity over this local index."""
        if self._children[nid]:
            return "".join(self.flat_text(child)
                           for child in self._children[nid])
        return str(self._nodes[nid]["text"])

    def render(self) -> str:
        return "".join(str(leaf["text"]) for leaf in self.leaf_records())


def cst_graph_from_nested(nested: dict[str, Any]) -> CstGraph:
    """The test/caller helper: a `CstGraph` from a nested text tree.

    This is the synthetic `CstNode` path used when the tree-sitter grammars are
    absent from the environment; see `CstGraph.from_nested` for the shape.
    """
    return CstGraph.from_nested(nested)


def parse_cst_path(path: str) -> list[int]:
    """Parse `child[2].child[0]` into child positions from the root.

    `""`, `"."`, `"root"` and `"$"` address the root node.
    """
    text = str(path or "").strip()
    if text in ("", ".", "root", "$"):
        return []
    for prefix in ("root.", "$."):
        if text.startswith(prefix):
            text = text[len(prefix):]
            break
    out: list[int] = []
    for part in text.split("."):
        match = _PATH_SEGMENT_RE.match(part.strip())
        if match is None:
            raise CstEditError(
                f"bad CST path {path!r}: each segment must look like "
                f"child[N]")
        out.append(int(match.group(1)))
    return out


# --------------------------------------------------------------------------- #
# tree-sitter availability / parsing
# --------------------------------------------------------------------------- #
def _backend_status(language: str) -> dict[str, Any]:
    """Report whether the real tree-sitter ingestion path can run here."""
    status: dict[str, Any] = {
        "language": language,
        "available": False,
        "reason": "",
        "grammar": _GRAMMAR_MODULES.get(language, ""),
    }
    module = _GRAMMAR_MODULES.get(language)
    if module is None:
        status["reason"] = (
            f"no tree-sitter grammar registered for {language!r} "
            f"(have: {sorted(_GRAMMAR_MODULES)})")
        return status
    try:
        import tree_sitter  # noqa: F401
    except Exception as e:  # noqa: BLE001 — absence is an expected environment
        status["reason"] = f"tree_sitter is not importable: {e}"
        return status
    try:
        importlib.import_module(module)
    except Exception as e:  # noqa: BLE001
        status["reason"] = f"{module} grammar is not importable: {e}"
        return status
    try:
        from substrate_rs import Substrate  # noqa: F401
    except Exception as e:  # noqa: BLE001
        status["reason"] = f"substrate_rs is not importable: {e}"
        return status
    status["available"] = True
    return status


def tree_sitter_available(language: str) -> bool:
    """True when the real parse/ingest path (tree_sitter + grammar + substrate)
    is importable for `language`. The synthetic CST path works regardless."""
    return bool(_backend_status(language).get("available"))


def cst_backend_status(language: str) -> dict[str, Any]:
    """Public, honest backend report for the dispatcher or a CLI."""
    return _backend_status(language)


def _make_parser(language: str) -> tuple[Any | None, str]:
    """Construct a `tree_sitter.Parser` for `language`; (None, reason) if not."""
    module = _GRAMMAR_MODULES.get(language)
    if module is None:
        return None, f"no grammar registered for {language!r}"
    try:
        from tree_sitter import Language, Parser
        grammar = importlib.import_module(module)
        return Parser(Language(grammar.language())), ""
    except Exception as e:  # noqa: BLE001
        return None, f"tree-sitter parser unavailable: {e}"


def _parse_graph(source: str, language: str) -> CstGraph:
    """Ingest `source` through `domains.ts_ingest.ingest_source`."""
    try:
        from substrate_rs import Substrate
        from domains.ts_ingest import ingest_source
    except Exception as e:  # noqa: BLE001
        raise CstEditError(
            f"cannot import the tree-sitter ingestion path for {language}: {e}"
        ) from e
    try:
        substrate = Substrate()
        info = ingest_source(substrate, source, language,
                             include_trivia=True)
    except Exception as e:  # noqa: BLE001
        raise CstEditError(
            f"tree-sitter ingestion failed for {language}: {e}") from e
    return CstGraph.from_substrate(substrate, info["root"])


def _reparse_status(source: str, language: str) -> dict[str, Any]:
    """Re-parse edited source; report honestly when the grammar is absent."""
    parser, reason = _make_parser(language)
    if parser is None:
        return {"checked": False, "ok": None, "reason": reason}
    try:
        tree = parser.parse(source.encode("utf-8"))
        has_error = bool(tree.root_node.has_error)
    except Exception as e:  # noqa: BLE001
        return {"checked": False, "ok": None,
                "reason": f"tree-sitter re-parse failed: {e}"}
    return {
        "checked": True,
        "ok": not has_error,
        "reason": "" if not has_error else "tree-sitter reported ERROR nodes",
    }


def _coerce_graph(value: Any) -> CstGraph:
    if isinstance(value, CstGraph):
        return value
    if isinstance(value, dict):
        if "substrate" in value:
            substrate = value.get("substrate")
            root = value.get("root")
            if substrate is None or root is None:
                raise CstEditError(
                    "cst_graph substrate form needs 'substrate' and 'root'")
            return CstGraph.from_substrate(substrate, root)
        return CstGraph.from_dict(value)
    raise CstEditError(
        "cst_graph must be a CstGraph, a nested object, or a serialized "
        "node/edge object")


# --------------------------------------------------------------------------- #
# spans and edits
# --------------------------------------------------------------------------- #
def _line_offsets(source: str) -> list[int]:
    offsets = [0]
    for i, ch in enumerate(source):
        if ch == "\n":
            offsets.append(i + 1)
    return offsets


def _span_offsets(source: str, op: dict[str, Any]) -> tuple[int, int]:
    """Resolve `replace_span` offsets: chars, UTF-8 bytes, or line/col."""
    char_start = op.get("start")
    if char_start is None:
        char_start = op.get("char_start")
    char_end = op.get("end")
    if char_end is None:
        char_end = op.get("char_end")
    byte_start = op.get("start_byte")
    if byte_start is None:
        byte_start = op.get("byte_start")
    byte_end = op.get("end_byte")
    if byte_end is None:
        byte_end = op.get("byte_end")
    if char_start is not None or char_end is not None:
        if char_start is None or char_end is None:
            raise CstEditError("replace_span needs both start and end")
        try:
            start, end = int(char_start), int(char_end)
        except (TypeError, ValueError) as e:
            raise CstEditError("replace_span start/end must be integers") from e
    elif byte_start is not None or byte_end is not None:
        if byte_start is None or byte_end is None:
            raise CstEditError(
                "replace_span needs both start_byte and end_byte")
        try:
            first, last = int(byte_start), int(byte_end)
        except (TypeError, ValueError) as e:
            raise CstEditError(
                "replace_span start_byte/end_byte must be integers") from e
        raw = source.encode("utf-8")
        if first < 0 or last < first or last > len(raw):
            raise CstEditError("replace_span byte range out of range")
        try:
            start = len(raw[:first].decode("utf-8"))
            end = len(raw[:last].decode("utf-8"))
        except UnicodeDecodeError as e:
            raise CstEditError(
                "replace_span byte offsets are not on UTF-8 character "
                "boundaries") from e
    elif "start_line" in op or "end_line" in op:
        if "start_line" not in op or "end_line" not in op:
            raise CstEditError(
                "replace_span needs start_line and end_line")
        offsets = _line_offsets(source)
        try:
            start_line = int(op["start_line"])
            end_line = int(op["end_line"])
            start_col = int(op.get("start_col", 0))
            end_col = int(op.get("end_col", 0))
        except (TypeError, ValueError) as e:
            raise CstEditError(
                "replace_span line/col values must be integers") from e
        if not (1 <= start_line <= len(offsets)
                and 1 <= end_line <= len(offsets)):
            raise CstEditError("replace_span line out of range")

        def column_at(line: int, col: int) -> int:
            if col < 0:
                raise CstEditError("replace_span col out of range")
            line_start = offsets[line - 1]
            line_end = offsets[line] if line < len(offsets) else len(source)
            if line_start + col > line_end:
                raise CstEditError("replace_span col out of range")
            return line_start + col

        start = column_at(start_line, start_col)
        end = column_at(end_line, end_col)
    else:
        raise CstEditError(
            "replace_span needs start/end (chars), start_byte/end_byte "
            "(UTF-8), or start_line/start_col/end_line/end_col")
    if start < 0 or end < start or end > len(source):
        raise CstEditError("replace_span out of range")
    return start, end


def _op_text(op: dict[str, Any], kind: str) -> str:
    if "text" not in op:
        raise CstEditError(f"{kind}: missing text")
    value = op["text"]
    if not isinstance(value, str):
        raise CstEditError(f"{kind}: text must be a string")
    return value


def _resolve_node(graph: CstGraph, path: str,
                  op_name: str) -> Any:
    """Resolve a child-index path to a node id, with an honest error."""
    indices = parse_cst_path(path)
    nid = graph.root
    for depth, index in enumerate(indices):
        kids = graph.children(nid)
        if index >= len(kids):
            at = ".".join(f"child[{i}]" for i in indices[:depth]) or "root"
            available = ", ".join(
                f"child[{i}]={graph.kind(child)}"
                for i, child in enumerate(kids)
            ) or "<leaf>"
            raise CstEditError(
                f"{op_name}: no CST node at path {path!r}; at {at} "
                f"available: {available}")
        nid = kids[index]
    return nid


def _is_statement_like(kind: str) -> bool:
    k = kind.lower()
    return k in _STATEMENT_KINDS or k.endswith(_STATEMENT_SUFFIXES)


def _delete_range(source: str, start: int, end: int,
                  kind: str) -> tuple[int, int, str]:
    """Delete a subtree; for statement-like nodes consume the line and one
    trailing blank line when that is unambiguously safe.

    Returns (start, end, note). The heuristic never touches a line that carries
    another token or comment: if the target does not own its line, the plain
    subtree range is used and `note` is empty.
    """
    if not _is_statement_like(kind):
        return start, end, ""
    line_start = source.rfind("\n", 0, start) + 1
    if source[line_start:start].strip():
        return start, end, ""
    new_start = line_start
    line_end = source.find("\n", end)
    if line_end == -1:
        if source[end:].strip():
            return start, end, ""
        new_end = len(source)
    else:
        if source[end:line_end].strip():
            return start, end, ""
        new_end = line_end + 1

    # Consume one trailing blank line, the same rule the Python adapter uses
    # for delete_symbol. Consuming a leading blank line too would make two
    # adjacent statement deletions fight over the same whitespace.
    if new_end < len(source):
        next_nl = source.find("\n", new_end)
        next_end = len(source) if next_nl == -1 else next_nl + 1
        if source[new_end:next_end].strip() == "":
            return new_start, next_end, "whole line + one trailing blank line"
    return new_start, new_end, "whole line"


def _overlaps(a: _Edit, b: _Edit) -> bool:
    if a.start == a.end and b.start == b.end:
        return a.start == b.start
    if a.start == a.end:
        return b.start <= a.start <= b.end
    if b.start == b.end:
        return a.start <= b.start <= a.end
    return max(a.start, b.start) < min(a.end, b.end)


def _check_overlaps(edits: list[_Edit]) -> None:
    for i, first in enumerate(edits):
        for second in edits[i + 1:]:
            if _overlaps(first, second):
                raise CstEditError(
                    f"overlapping CST edits in one script: "
                    f"{first.target!r} {first.start}:{first.end} and "
                    f"{second.target!r} {second.start}:{second.end}")


def _node_span(graph: CstGraph, source: str,
               nid: Any) -> tuple[int, int, str]:
    start, end = graph.ranges()[nid]
    text = source[start:end]
    rendered = graph.flat_text(nid)
    if text != rendered:
        raise CstEditError(
            f"internal CST range mismatch at {graph.kind(nid)!r}: "
            f"{start}:{end} is not its leaf text")
    return start, end, text


def _apply_ops(source: str, graph: CstGraph,
               ops: list[dict[str, Any]],
               newline: str = "\n") -> tuple[str, list[dict[str, Any]]]:
    old_source = graph.render()
    if old_source != source:
        limit = min(len(old_source), len(source))
        first = next((i for i in range(limit)
                      if old_source[i] != source[i]), limit)
        raise CstEditError(
            f"CST does not round-trip the file: reconstructed "
            f"{len(old_source)} chars, file has {len(source)}; first "
            f"difference at char {first}")

    edits: list[_Edit] = []
    changes: list[dict[str, Any]] = []

    node_ops = ("replace_node", "insert_before_node", "insert_after_node",
                "delete_node", "wrap_node")
    for op in ops:
        if not isinstance(op, dict):
            raise CstEditError("each op must be an object")
        kind = str(op.get("op") or "").strip()
        if kind not in node_ops and kind != "replace_span":
            raise CstEditError(
                f"unknown CST op {kind!r}; supported: replace_node, "
                f"insert_before_node, insert_after_node, delete_node, "
                f"wrap_node, replace_span")
        raw_path = op.get("path")
        if raw_path is None:
            raw_path = op.get("target")
        if kind in node_ops:
            if raw_path is None:
                raise CstEditError(f"{kind}: missing CST path")
            path = str(raw_path)
            nid = _resolve_node(graph, path, kind)
            node_kind = graph.kind(nid)
            start, end, old_text = _node_span(graph, source, nid)

        if kind == "replace_node":
            text = _op_text(op, kind)
            if not text:
                raise CstEditError(
                    "replace_node with empty text is refused; use delete_node")
            edits.append(_Edit(start, end, text, path))
            changes.append({
                "op": kind, "path": path, "node_kind": node_kind,
                "summary": f"replace CST node ({node_kind})",
            })
        elif kind in ("insert_before_node", "insert_after_node"):
            text = _op_text(op, kind)
            if not text:
                raise CstEditError(f"{kind}: empty text")
            at = start if kind == "insert_before_node" else end
            edits.append(_Edit(at, at, text, path))
            where = "before" if kind == "insert_before_node" else "after"
            changes.append({
                "op": kind, "path": path, "node_kind": node_kind,
                "summary": f"insert {where} CST node ({node_kind})",
            })
        elif kind == "delete_node":
            if nid == graph.root:
                raise CstEditError(
                    "delete_node on the CST root is refused; replace the "
                    "root or delete a child node")
            del_start, del_end, note = _delete_range(
                source, start, end, node_kind)
            edits.append(_Edit(del_start, del_end, "", path))
            summary = "delete CST node"
            if note:
                summary += f" ({note})"
            changes.append({
                "op": kind, "path": path, "node_kind": node_kind,
                "summary": f"{summary}: {node_kind}",
            })
        elif kind == "wrap_node":
            prefix = op.get("prefix", "")
            suffix = op.get("suffix", "")
            if not isinstance(prefix, str) or not isinstance(suffix, str):
                raise CstEditError(
                    "wrap_node: prefix and suffix must be strings")
            if not prefix and not suffix:
                raise CstEditError(
                    "wrap_node needs prefix and/or suffix")
            edits.append(_Edit(start, end, prefix + old_text + suffix, path))
            changes.append({
                "op": kind, "path": path, "node_kind": node_kind,
                "summary": f"wrap CST node ({node_kind})",
            })
        elif kind == "replace_span":
            span_start, span_end = _span_offsets(source, op)
            text = _op_text(op, kind)
            edits.append(_Edit(span_start, span_end, text, "span"))
            changes.append({
                "op": kind,
                "summary": f"replace span {span_start}:{span_end}",
            })
        else:
            raise CstEditError(
                f"unknown CST op {kind!r}; supported: replace_node, "
                f"insert_before_node, insert_after_node, delete_node, "
                f"wrap_node, replace_span")

    _check_overlaps(edits)

    # Apply bottom-up through the shared lossless leaf structure. Every leaf
    # outside an edit is preserved byte-for-byte; overlapping leaves are split
    # only at the edit boundary.
    try:
        doc = LosslessText(
            [Leaf(str(record["kind"]), str(record["text"]))
             for record in graph.leaf_records()],
            source,
        )
    except LosslessError as e:
        raise CstEditError(
            f"CST leaf structure does not round-trip the source: {e}") from e
    for edit in sorted(edits, key=lambda e: (e.start, e.end), reverse=True):
        try:
            doc.replace(edit.start, edit.end,
                        normalize_newlines(edit.text, newline))
        except LosslessError as e:
            raise CstEditError(f"cannot apply CST edit: {e}") from e
    return doc.render(), changes


# --------------------------------------------------------------------------- #
# transaction entry point
# --------------------------------------------------------------------------- #
def apply_cst_edit_script(root: str | Path, script: dict[str, Any], *,
                          write: bool = False) -> dict[str, Any]:
    """Validate and optionally apply a graph-addressed Rust/Lua CST edit.

    `write=False` (default) is a pure preview. `write=True` backs up the
    original under `var/ocelot_dev_edits/backups/`, writes atomically, and
    reports the transaction. See the module docstring for the op list and the
    synthetic `cst_graph` key used when tree-sitter is absent.
    """
    if not isinstance(script, dict):
        raise CstEditError("edit script must be an object")
    for key in FORBIDDEN_SCRIPT_KEYS:
        if key in script:
            raise CstEditError(
                f"raw {key!r} input is refused: send semantic CST ops over "
                f"graph targets; a diff is only an output view")

    root_path = Path(root).resolve()
    file = str(script.get("file") or "").strip()
    if not file:
        raise CstEditError("edit script needs file")
    path = (root_path / file).resolve()
    try:
        path.relative_to(root_path)
    except ValueError as e:
        raise CstEditError("file escapes the repo root") from e
    suffix = path.suffix.lower()
    if suffix not in (".rs", ".lua"):
        raise CstEditError(
            f"cst adapter only edits .rs/.lua; got {suffix or '<no suffix>'!r}")
    language = "rust" if suffix == ".rs" else "lua"
    declared = script.get("language")
    if (declared is not None and str(declared).strip()
            and str(declared).lower() != language):
        raise CstEditError(
            f"language {declared!r} does not match file suffix {suffix!r}")
    src = read_source(root_path, file, suffixes=(".rs", ".lua"),
                      max_bytes=MAX_SOURCE_BYTES, error_cls=CstEditError)
    source = src.text
    base_sha = src.sha256
    check_base(src, script.get("base_sha256"), CstEditError)
    ops = script.get("ops")
    if not isinstance(ops, list) or not ops:
        raise CstEditError("edit script needs a non-empty ops list")

    supplied = None
    for key in ("cst_graph", "cst", "synthetic_cst"):
        if script.get(key) is not None:
            supplied = script[key]
            break
    if supplied is not None:
        graph = _coerce_graph(supplied)
        backend = ("substrate" if isinstance(supplied, dict)
                   and "substrate" in supplied else "synthetic")
    else:
        status = _backend_status(language)
        if not status["available"]:
            raise CstEditError(
                f"tree_sitter backend unavailable for {language}: "
                f"{status['reason']}. Supply a synthetic CstNode graph as "
                f"script['cst_graph'] (nested text tree) or use preview-only "
                f"outside the parser environment.")
        graph = _parse_graph(source, language)
        backend = "tree_sitter"

    new_source, changes = _apply_ops(source, graph, ops, newline=src.newline)
    try:
        new_source.encode("utf-8")
    except UnicodeEncodeError as e:
        raise CstEditError(f"edited source is not valid UTF-8: {e}") from e
    reparse = _reparse_status(new_source, language)
    # The parse check is binding on apply. A preview still returns the rendered
    # view and records an ERROR parse honestly in lossless.reparse.
    if write and reparse["checked"] and not reparse["ok"]:
        raise CstEditError(
            f"edit would not parse as {language}: {reparse['reason']}")
    if write and not reparse["checked"]:
        raise CstEditError(
            f"cannot validate the edited source: tree-sitter backend "
            f"unavailable for {language}; preview only")

    new_sha = sha256_bytes(encode_text(src, new_source))
    diff_lines = list(difflib.unified_diff(
        source.splitlines(keepends=True),
        new_source.splitlines(keepends=True),
        fromfile=f"a/{file}", tofile=f"b/{file}",
    ))

    applied = False
    backup = None
    if write:
        backup = write_source(root_path, src, new_source,
                              error_cls=CstEditError)
        applied = True

    return {
        "ok": True,
        "file": file,
        "applied": applied,
        "format": language,
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
            "roundtrip": graph.render() == source,
            "language": language,
            "cst_backend": backend,
            "nodes": graph.node_count,
            "leaves": graph.leaf_count,
            "reparse": reparse,
        },
        "graph_stale": bool(applied),
    }


__all__ = [
    "CstEditError",
    "CstGraph",
    "apply_cst_edit_script",
    "cst_backend_status",
    "cst_graph_from_nested",
    "parse_cst_path",
    "tree_sitter_available",
]
