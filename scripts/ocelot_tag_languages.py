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
# every cached entry.
TAGS_SCHEMA_VERSION = 1

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


def _python_tags(source: str) -> list[dict[str, Any]]:
    """Python tags via the stdlib AST fast path.

    This is the only Python extractor in the tree; ``ocelot_repo_map`` delegates
    here. It returns class/function definitions plus loaded names and
    attributes. It avoids paying a tree-sitter parse per Python file while the
    repo map indexes thousands of them.
    """
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return []
    out: list[dict[str, Any]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.ClassDef)):
            out.append({"name": node.name, "kind": "def",
                        "detail": ("definition.class"
                                   if isinstance(node, ast.ClassDef)
                                   else "definition.function"),
                        "line": int(getattr(node, "lineno", 1))})
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            out.append({"name": node.id, "kind": "ref",
                        "detail": "reference.name",
                        "line": int(getattr(node, "lineno", 1))})
        elif isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load):
            out.append({"name": node.attr, "kind": "ref",
                        "detail": "reference.attribute",
                        "line": int(getattr(node, "lineno", 1))})
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
        out: list[dict[str, Any]] = []
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
            for node in captures.get("name", []):
                name = node.text.decode("utf-8", errors="replace")
                if not name:
                    continue
                out.append({
                    "name": name,
                    "kind": kind,
                    "detail": kind_capture,
                    "line": int(node.start_point[0]) + 1,
                })
        return out, None
    except Exception as exc:
        return [], f"{type(exc).__name__}: {exc}"


def extract_tags(path: str | Path, source: str) -> list[dict[str, Any]]:
    """Definitions and references for one file.

    Returns ``[{name, kind: "def"|"ref", detail, line}]`` where ``detail`` is
    the query capture (for example ``definition.function`` or
    ``reference.call``) and ``line`` is 1-based.

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
