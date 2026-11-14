"""ocelot_tag_languages — multi-language definition/reference tags.

Workstream D of the advanced coding-agent plan. This module is a registry of
tree-sitter tag backends: one entry per supported file suffix, each naming the
grammar module, the language factory inside it, and the grammar's own
``queries/tags.scm``.

The API is deliberately uniform with ``ocelot_repo_map.extract_tags`` so the
central integrator can swap the three-language table for this registry without
changing the tag-cache or graph code:

    from scripts.ocelot_tag_languages import LANGUAGES, extract_tags
    entry = LANGUAGES[".rs"]          # {language, module, tags_query, factory, backend}
    tags = extract_tags("x.rs", source)

Python keeps the stdlib-AST fast path (the same definitions/references as
``ocelot_repo_map``); every other language uses its installed grammar's
``queries/tags.scm``. The registry does not require a grammar import at module
import time, so a missing optional grammar degrades to an empty tag list rather
than breaking the caller. ``backend_status`` reports exactly what is available
and which capture classes the shipped query provides.

DEV TOOLING, NOT AGENT RUNTIME. Tags are syntactic hints for the repo map; they
are not scope-resolved and they never edit code.
"""
from __future__ import annotations

import ast
import hashlib
import importlib
import json
from functools import lru_cache
from pathlib import Path
from typing import Any, NamedTuple

__all__ = [
    "LANGUAGES",
    "TAGS_SCHEMA_VERSION",
    "language_for",
    "extract_tags",
    "extract_tags_status",
    "extractor_fingerprint",
    "available_languages",
    "backend_status",
]

# Bump whenever extraction output changes for any suffix. Tag caches key on
# extractor_fingerprint(), which includes this number, so a bump invalidates
# every cached entry. v3: Python sources with a leading UTF-8 BOM now produce
# tags (v2 returned none, and the empty result was cached).
TAGS_SCHEMA_VERSION = 3

# Every grammar package inspected for this registry keeps its upstream tag
# query at <package>/queries/tags.scm.
_TAGS_QUERY = "queries/tags.scm"


def _entry(language: str, module: str, factory: str, *,
           backend: str = "tree-sitter") -> dict[str, Any]:
    """One registry value. The four required fields are always present."""
    return {
        "language": language,
        "module": module,
        "tags_query": _TAGS_QUERY,
        "factory": factory,
        "backend": backend,
    }


# suffix -> backend spec. The TypeScript package exposes two factories:
# ``language_typescript`` (plain TS) and ``language_tsx`` (TSX/JSX). JavaScript
# uses the TSX factory because it is the JS+JSX superset; plain .js parses
# there too. C++ and C each expose a single ``language`` factory.
LANGUAGES: dict[str, dict[str, Any]] = {
    ".py": _entry("python", "tree_sitter_python", "language",
                  backend="python-ast"),
    ".rs": _entry("rust", "tree_sitter_rust", "language"),
    ".lua": _entry("lua", "tree_sitter_lua", "language"),
    ".ts": _entry("typescript", "tree_sitter_typescript",
                  "language_typescript"),
    ".tsx": _entry("tsx", "tree_sitter_typescript", "language_tsx"),
    ".js": _entry("javascript", "tree_sitter_typescript", "language_tsx"),
    ".jsx": _entry("javascript", "tree_sitter_typescript", "language_tsx"),
    ".go": _entry("go", "tree_sitter_go", "language"),
    ".java": _entry("java", "tree_sitter_java", "language"),
    ".c": _entry("c", "tree_sitter_c", "language"),
    ".h": _entry("c", "tree_sitter_c", "language"),
    ".cpp": _entry("cpp", "tree_sitter_cpp", "language"),
    ".cc": _entry("cpp", "tree_sitter_cpp", "language"),
    ".cxx": _entry("cpp", "tree_sitter_cpp", "language"),
    ".hpp": _entry("cpp", "tree_sitter_cpp", "language"),
}


def language_for(path: str | Path) -> dict[str, Any] | None:
    """Registry entry for a path's suffix, or None for an unknown suffix.

    The lookup is suffix-only (the file need not exist), so callers can use it
    on virtual paths or before reading anything from disk.
    """
    return LANGUAGES.get(Path(path).suffix.lower())


def _entry_for(language_or_suffix: str) -> dict[str, Any] | None:
    """Accept a language label ("rust") or a suffix (".rs")."""
    key = str(language_or_suffix).strip().lower()
    if key in LANGUAGES:
        return LANGUAGES[key]
    for suffix in sorted(LANGUAGES):
        entry = LANGUAGES[suffix]
        if entry["language"] == key:
            return entry
    return None


class _TreeSitterBackend(NamedTuple):
    language: Any
    query: Any
    query_path: Path
    definitions: bool
    references: bool


def _query_path(module: Any, query_rel: str) -> Path:
    base = getattr(module, "__file__", None)
    if not base:
        raise FileNotFoundError(
            f"{getattr(module, '__name__', module)!r} has no package path")
    path = Path(base).resolve().parent / query_rel
    if not path.is_file():
        raise FileNotFoundError(
            f"{getattr(module, '__name__', module)}: missing {query_rel}")
    return path


@lru_cache(maxsize=None)
def _load_tree_sitter_backend(module_name: str, factory_name: str,
                              query_rel: str) -> _TreeSitterBackend:
    """Import a grammar, build its Language and compile tags.scm once.

    Cached per (module, factory, query path). Query compilation is the
    expensive part; Parser objects are cheap and stay per-call so separate
    callers cannot share parser state.
    """
    from tree_sitter import Language, Query

    module = importlib.import_module(module_name)
    factory = getattr(module, factory_name)
    language = Language(factory())
    query_path = _query_path(module, query_rel)
    text = query_path.read_text(encoding="utf-8")
    query = Query(language, text)
    return _TreeSitterBackend(
        language=language,
        query=query,
        query_path=query_path,
        definitions="@definition." in text,
        references="@reference." in text,
    )


_PY_DEF_NODES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)


def _python_import_tags(node: ast.AST, scope: str) -> list[dict[str, Any]]:
    """Import tags for one Import/ImportFrom node, one per bound name.

    ``import a.b`` binds ``a`` (imported ``a.b``); ``import a.b as c`` binds
    ``c``. ``from . import x as y`` binds ``y`` with level 1 and module "".
    Star imports bind no name and are not tagged.
    """
    line = int(getattr(node, "lineno", 1))
    out: list[dict[str, Any]] = []
    if isinstance(node, ast.Import):
        for alias in node.names:
            bound = alias.asname or alias.name.split(".")[0]
            out.append({"name": bound, "kind": "import",
                        "detail": "import.module", "line": line,
                        "module": alias.name, "level": 0,
                        "imported": alias.name, "scope": scope})
    elif isinstance(node, ast.ImportFrom):
        for alias in node.names:
            if alias.name == "*":
                continue
            out.append({"name": alias.asname or alias.name, "kind": "import",
                        "detail": "import.from", "line": line,
                        "module": node.module or "",
                        "level": int(node.level or 0),
                        "imported": alias.name, "scope": scope})
    return out


def _python_tags(source: str) -> list[dict[str, Any]]:
    """Python tags via the stdlib AST: defs, refs and imports with scope.

    This is the only Python extractor in the tree; ``ocelot_repo_map`` delegates
    here. Definitions carry ``qualname`` (the dotted chain of enclosing defs plus
    the name) and ``end_line``. Loads carry ``scope``, the qualname of the
    innermost enclosing def ("" at module level). The set of
    ``(name, kind, detail, line)`` tuples is the same as a plain ``ast.walk``
    over Name/Attribute loads and def nodes.

    Decorators, default values, annotations, bases and keywords belong to the
    enclosing scope; only the def body is inside the new scope. The walk uses
    an explicit stack, so deeply nested expressions cannot hit the recursion
    limit, and the output is in source (pre-order) order.
    """
    # ast.parse rejects U+FEFF as a non-printable character. One leading BOM
    # is dropped; line numbers are unchanged because it sits on line 1.
    if source.startswith("\ufeff"):
        source = source[1:]
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return []
    out: list[dict[str, Any]] = []
    stack: list[tuple[ast.AST, tuple[str, ...]]] = [(tree, ())]
    while stack:
        node, qual = stack.pop()
        if isinstance(node, _PY_DEF_NODES):
            inner = qual + (node.name,)
            is_class = isinstance(node, ast.ClassDef)
            line = int(getattr(node, "lineno", 1))
            out.append({"name": node.name, "kind": "def",
                        "detail": ("definition.class" if is_class
                                   else "definition.function"),
                        "line": line,
                        "end_line": int(getattr(node, "end_lineno", None)
                                        or line),
                        "qualname": ".".join(inner)})
            outer: list[ast.AST] = [*node.decorator_list,
                                    *getattr(node, "type_params", [])]
            if is_class:
                outer += [*node.bases, *node.keywords]
            else:
                outer.append(node.args)
                if node.returns is not None:
                    outer.append(node.returns)
            children = [(c, qual) for c in outer]
            children += [(c, inner) for c in node.body]
        else:
            scope = ".".join(qual)
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                out.append({"name": node.id, "kind": "ref",
                            "detail": "reference.name",
                            "line": int(getattr(node, "lineno", 1)),
                            "scope": scope})
            elif (isinstance(node, ast.Attribute)
                  and isinstance(node.ctx, ast.Load)):
                out.append({"name": node.attr, "kind": "ref",
                            "detail": "reference.attribute",
                            "line": int(getattr(node, "lineno", 1)),
                            "scope": scope})
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                out.extend(_python_import_tags(node, scope))
            children = [(c, qual) for c in ast.iter_child_nodes(node)]
        stack.extend(reversed(children))
    return out


class _Span(NamedTuple):
    """One tree-sitter capture, with byte offsets for nesting."""
    name: str
    kind: str
    detail: str
    line: int
    name_start: int
    def_start: int
    def_end: int
    end_line: int


def _nest_tree_sitter_tags(spans: list[_Span]) -> list[dict[str, Any]]:
    """Attach ``qualname`` to defs and ``scope`` to refs, in O(n log n).

    A def encloses another def when its definition node's byte range contains
    the inner def's start. A ref belongs to the innermost def whose definition
    node contains the ref's name. Events are sorted by position (defs before
    refs at the same position, outer defs before inner ones); a stack of open
    defs gives the innermost enclosing def in amortised constant time.

    Duplicate defs (same definition node, name node and name) are emitted once.
    Output is in source order (by name position), so it does not depend on the
    order in which tree-sitter groups query patterns.
    """
    events: list[tuple[int, int, int, int]] = []
    seen_defs: set[tuple[int, int, int, str]] = set()
    emit = [True] * len(spans)
    for i, span in enumerate(spans):
        if span.kind == "def":
            key = (span.def_start, span.def_end, span.name_start, span.name)
            if key in seen_defs:
                emit[i] = False
                continue
            seen_defs.add(key)
            events.append((span.def_start, 0, -span.def_end, i))
        else:
            events.append((span.name_start, 1, 0, i))
    events.sort()
    qualname: dict[int, str] = {}
    scope_of: dict[int, str] = {}
    open_defs: list[int] = []
    for pos, order, _tie, i in events:
        while open_defs and spans[open_defs[-1]].def_end <= pos:
            open_defs.pop()
        parent = qualname[open_defs[-1]] if open_defs else ""
        if order == 0:
            name = spans[i].name
            qualname[i] = f"{parent}.{name}" if parent else name
            open_defs.append(i)
        else:
            scope_of[i] = parent
    out: list[dict[str, Any]] = []
    for i in sorted(range(len(spans)), key=lambda k: (spans[k].name_start, k)):
        span = spans[i]
        if not emit[i]:
            continue
        if span.kind == "def":
            out.append({"name": span.name, "kind": "def",
                        "detail": span.detail, "line": span.line,
                        "end_line": span.end_line,
                        "qualname": qualname[i]})
        else:
            out.append({"name": span.name, "kind": "ref",
                        "detail": span.detail, "line": span.line,
                        "scope": scope_of[i]})
    return out


def extract_tags_status(path: str | Path,
                        source: str) -> tuple[list[dict[str, Any]], str | None]:
    """Tags for one file plus an explicit backend error, if any.

    Returns ``(tags, None)`` on success, including a genuine "no tags" answer:
    an unknown suffix, or Python source that does not parse. Returns
    ``([], error_text)`` when the grammar import, query compile or parse
    raised. Callers that cache results must not store the error case.
    """
    entry = language_for(path)
    if entry is None:
        return [], None
    if entry["backend"] == "python-ast":
        return _python_tags(source), None
    try:
        from tree_sitter import Parser, QueryCursor

        backend = _load_tree_sitter_backend(
            entry["module"], entry["factory"], entry["tags_query"])
        parser = Parser(backend.language)
        tree = parser.parse(source.encode("utf-8"))
        cursor = QueryCursor(backend.query)
        spans: list[_Span] = []
        # tree-sitter 0.26: matches() yields
        # (pattern_index, {capture_name: [Node, ...]}).
        for _pattern_index, captures in cursor.matches(tree.root_node):
            kind_capture = next(
                (key for key in captures
                 if key.startswith(("definition.", "reference."))),
                None)
            if not kind_capture:
                continue
            kind = "def" if kind_capture.startswith("definition.") else "ref"
            def_nodes = captures.get(kind_capture) or []
            for node in captures.get("name", []):
                name = node.text.decode("utf-8", errors="replace")
                if not name:
                    continue
                # Refs and defs without a definition node fall back to the
                # name node's own range; nesting then uses the name only.
                outer = def_nodes[0] if (kind == "def" and def_nodes) else node
                spans.append(_Span(
                    name=name,
                    kind=kind,
                    detail=kind_capture,
                    line=int(node.start_point[0]) + 1,
                    name_start=int(node.start_byte),
                    def_start=int(outer.start_byte),
                    def_end=int(outer.end_byte),
                    end_line=int(outer.end_point[0]) + 1,
                ))
        return _nest_tree_sitter_tags(spans), None
    except Exception as exc:
        return [], f"{type(exc).__name__}: {exc}"


def extract_tags(path: str | Path, source: str) -> list[dict[str, Any]]:
    """Definitions, references and (Python) imports for one file.

    Defs are ``{name, kind: "def", detail, line, end_line, qualname}``. Refs
    are ``{name, kind: "ref", detail, line, scope}``. Python import bindings
    are ``{name, kind: "import", detail: "import.module"|"import.from", line,
    module, level, imported, scope}``. ``detail`` is the query capture (for
    example ``definition.function`` or ``reference.call``) and ``line`` is
    1-based. ``qualname`` and ``scope`` are dotted enclosing-def chains, "" at
    module level. Output is in source order.

    Unknown suffixes, missing grammars, missing/uncompilable tag queries and
    malformed source all return ``[]``: one bad file must not kill a repo-wide
    index. Use :func:`backend_status` to distinguish "no tags here" from
    "backend unavailable", or :func:`extract_tags_status` for the error text.
    """
    tags, _error = extract_tags_status(path, source)
    return tags


def _suffix_key(path_or_suffix: str | Path) -> str:
    """Lower-case suffix for a path, or a suffix string passed through.

    ``Path(".py").suffix`` is empty (a dotfile name), so a bare suffix is
    detected by its leading dot before falling back to ``Path.suffix``.
    """
    text = str(path_or_suffix)
    if text.startswith(".") and "/" not in text and "\\" not in text:
        return text.lower()
    return Path(text).suffix.lower()


def _distribution_version(module: str) -> str | None:
    """Installed grammar distribution version, trying both package spellings."""
    from importlib.metadata import PackageNotFoundError, version

    for name in (module, module.replace("_", "-")):
        try:
            return version(name)
        except PackageNotFoundError:
            continue
    return None


def _tags_query_sha(module: str, tags_query: str) -> str | None:
    """sha256 of the grammar's tags.scm bytes, or None if it cannot be read."""
    try:
        package = importlib.import_module(module)
        return hashlib.sha256(
            _query_path(package, tags_query).read_bytes()).hexdigest()
    except Exception:
        return None


@lru_cache(maxsize=None)
def _fingerprint_for_suffix(suffix: str) -> str:
    entry = LANGUAGES.get(suffix)
    if entry is None:
        payload: list[Any] = [TAGS_SCHEMA_VERSION, None]
    else:
        backend = entry["backend"]
        module = entry["module"]
        query_sha = (None if backend == "python-ast"
                     else _tags_query_sha(module, entry["tags_query"]))
        payload = [TAGS_SCHEMA_VERSION, backend, module,
                   _distribution_version(module), query_sha,
                   entry["language"]]
    return hashlib.sha256(json.dumps(payload).encode("utf-8")).hexdigest()


def extractor_fingerprint(path_or_suffix: str | Path) -> str:
    """Stable sha256 identifying the extractor that produces tags for a suffix.

    Covers the schema version, backend, grammar module, grammar distribution
    version and the tags.scm bytes. Unknown suffixes get a fingerprint of the
    schema version alone. Memoised per suffix; clear with
    ``_fingerprint_for_suffix.cache_clear()`` after changing the schema
    constant in a test.
    """
    return _fingerprint_for_suffix(_suffix_key(path_or_suffix))


def available_languages() -> list[str]:
    """Language labels whose grammar + tags query load successfully.

    Python is available whenever the stdlib is (its AST path needs no grammar).
    Sorted and de-duplicated; extension labels such as ``javascript`` appear
    once even though they cover both .js and .jsx.
    """
    labels = sorted({entry["language"] for entry in LANGUAGES.values()})
    return [label for label in labels if backend_status(label)["available"]]


def backend_status(language: str) -> dict[str, Any]:
    """Describe one backend honestly, without raising.

    ``language`` may be a label (``"rust"``) or a suffix (``".rs"``). The
    result reports availability, the resolved tags.scm path, whether the
    shipped query actually contains definition/reference captures, and any
    import/compile error.
    """
    entry = _entry_for(language)
    if entry is None:
        return {
            "language": str(language),
            "available": False,
            "backend": None,
            "module": None,
            "factory": None,
            "tags_query": None,
            "definitions": False,
            "references": False,
            "suffixes": [],
            "error": f"unknown language or suffix: {language!r}",
        }
    suffixes = sorted(
        suffix for suffix, candidate in LANGUAGES.items()
        if candidate["language"] == entry["language"])
    result: dict[str, Any] = {
        "language": entry["language"],
        "available": False,
        "backend": entry["backend"],
        "module": entry["module"],
        "factory": entry["factory"],
        "tags_query": None,
        "definitions": False,
        "references": False,
        "suffixes": suffixes,
        "error": None,
    }
    if entry["backend"] == "python-ast":
        # The AST path works without tree_sitter_python; still surface the
        # grammar's query path when it is installed so diagnostics are useful.
        result["available"] = True
        result["definitions"] = True
        result["references"] = True
        try:
            module = importlib.import_module(entry["module"])
            result["tags_query"] = str(
                _query_path(module, entry["tags_query"]))
        except Exception:
            pass
        return result
    try:
        backend = _load_tree_sitter_backend(
            entry["module"], entry["factory"], entry["tags_query"])
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
        return result
    result.update({
        "available": True,
        "tags_query": str(backend.query_path),
        "definitions": backend.definitions,
        "references": backend.references,
    })
    return result
