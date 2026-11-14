"""test_tag_languages_migrated — Workstream D tag registry tests.

Each installed grammar is exercised with a snippet chosen from the capture
classes its own ``queries/tags.scm`` actually declares. Two upstream gaps are
reported rather than papered over:

* C and C++ ship definition-only tags.scm; the reference assertion is skipped.
* The TypeScript package's tags.scm has no ordinary ``function_declaration`` /
  ``class_declaration`` patterns, so JavaScript has no definition captures;
  the JavaScript definition assertion is skipped.

A genuinely missing grammar package (import or tags query failure) also skips
the affected language instead of failing the registry.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from scripts import ocelot_tag_languages as tag_languages
from scripts.ocelot_tag_languages import (
    LANGUAGES,
    available_languages,
    backend_status,
    extract_tags,
    language_for,
)

EXPECTED_SUFFIXES = {
    ".py", ".rs", ".lua",
    ".ts", ".tsx", ".js", ".jsx",
    ".go", ".java",
    ".c", ".h", ".cpp", ".cc", ".cxx", ".hpp",
}

EXPECTED_LANGUAGE = {
    ".py": "python",
    ".rs": "rust",
    ".lua": "lua",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".js": "javascript",
    ".jsx": "javascript",
    ".go": "go",
    ".java": "java",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".hpp": "cpp",
}

# label, suffix, snippet, expected definition + detail, expected reference +
# detail. ``None`` means the shipped query has no such capture class.
CASES = [
    {
        "label": "python",
        "suffix": ".py",
        "source": ("class Alpha:\n"
                   "    def beta(self, value):\n"
                   "        return helper(value)\n"),
        "definition": "Alpha",
        "definition_detail": "definition.class",
        "reference": "helper",
        "reference_detail": "reference.name",
    },
    {
        "label": "rust",
        "suffix": ".rs",
        "source": ("fn alpha(x: i32) -> i32 { beta(x) }\n"
                   "struct Gamma { v: i32 }\n"),
        "definition": "alpha",
        "definition_detail": "definition.function",
        "reference": "beta",
        "reference_detail": "reference.call",
    },
    {
        "label": "lua",
        "suffix": ".lua",
        "source": ("function alpha(x)\n"
                   "  return beta(x)\n"
                   "end\n"),
        "definition": "alpha",
        "definition_detail": "definition.function",
        "reference": "beta",
        "reference_detail": "reference.call",
    },
    {
        "label": "typescript",
        "suffix": ".ts",
        "source": ("interface Alpha { value: number }\n"
                   "const item: Alpha = new Beta();\n"),
        "definition": "Alpha",
        "definition_detail": "definition.interface",
        "reference": "Beta",
        "reference_detail": "reference.class",
    },
    {
        "label": "tsx",
        "suffix": ".tsx",
        "source": ("interface Alpha { value: number }\n"
                   "const item: Alpha = new Beta();\n"),
        "definition": "Alpha",
        "definition_detail": "definition.interface",
        "reference": "Beta",
        "reference_detail": "reference.class",
    },
    {
        "label": "javascript",
        "suffix": ".js",
        "source": ("export function alpha(x) { return new Beta(); }\n"
                   "class Gamma {}\n"),
        # Upstream tree_sitter_typescript tags.scm has no function_declaration
        # or class_declaration pattern; only TS signatures/interfaces/modules.
        "definition": None,
        "definition_detail": None,
        "reference": "Beta",
        "reference_detail": "reference.class",
    },
    {
        "label": "go",
        "suffix": ".go",
        "source": ("package main\n"
                   "\n"
                   "func Alpha(x int) int { return beta(x) }\n"
                   "type Gamma struct { V int }\n"),
        "definition": "Alpha",
        "definition_detail": "definition.function",
        "reference": "beta",
        "reference_detail": "reference.call",
    },
    {
        "label": "java",
        "suffix": ".java",
        "source": "class Alpha { int beta(int x) { return gamma(x); } }\n",
        "definition": "Alpha",
        "definition_detail": "definition.class",
        "reference": "gamma",
        "reference_detail": "reference.call",
    },
    {
        "label": "c",
        "suffix": ".c",
        "source": ("int alpha(int x) { return beta(x); }\n"
                   "struct Gamma { int v; };\n"),
        "definition": "alpha",
        "definition_detail": "definition.function",
        # tree_sitter_c tags.scm is definition-only.
        "reference": None,
        "reference_detail": None,
    },
    {
        "label": "cpp",
        "suffix": ".cpp",
        "source": ("int alpha(int x) { return beta(x); }\n"
                   "class Gamma { public: int v; };\n"),
        "definition": "alpha",
        "definition_detail": "definition.function",
        # tree_sitter_cpp tags.scm is definition-only.
        "reference": None,
        "reference_detail": None,
    },
]

CASE_IDS = [case["label"] for case in CASES]


def _skip_if_unavailable(label: str) -> dict:
    status = backend_status(label)
    if not status["available"]:
        pytest.skip(f"{label} backend unavailable: {status['error']}")
    return status


def _defs(tags: list[dict]) -> set[str]:
    return {tag["name"] for tag in tags if tag["kind"] == "def"}


def _refs(tags: list[dict]) -> set[str]:
    return {tag["name"] for tag in tags if tag["kind"] == "ref"}


def test_extension_registry_mapping() -> None:
    assert set(LANGUAGES) == EXPECTED_SUFFIXES
    assert set(EXPECTED_LANGUAGE) == EXPECTED_SUFFIXES
    factories = {"language", "language_typescript", "language_tsx"}
    backends = {"tree-sitter", "python-ast"}
    for suffix, label in EXPECTED_LANGUAGE.items():
        entry = LANGUAGES[suffix]
        assert entry["language"] == label
        assert entry["module"].startswith("tree_sitter_")
        assert entry["tags_query"] == "queries/tags.scm"
        assert entry["factory"] in factories
        assert entry["backend"] in backends
    assert LANGUAGES[".py"]["backend"] == "python-ast"
    assert LANGUAGES[".rs"]["backend"] == "tree-sitter"
    # The TypeScript package exposes two language functions; TSX/JSX must use
    # the TSX factory or JSX fails to parse.
    assert LANGUAGES[".ts"]["factory"] == "language_typescript"
    assert LANGUAGES[".tsx"]["factory"] == "language_tsx"
    assert LANGUAGES[".js"]["factory"] == "language_tsx"
    assert LANGUAGES[".jsx"]["factory"] == "language_tsx"
    assert LANGUAGES[".js"]["module"] == "tree_sitter_typescript"
    assert LANGUAGES[".jsx"]["module"] == "tree_sitter_typescript"
    assert {LANGUAGES[s]["module"] for s in (".c", ".h")} == {"tree_sitter_c"}
    assert {LANGUAGES[s]["module"]
            for s in (".cpp", ".cc", ".cxx", ".hpp")} == {"tree_sitter_cpp"}


def test_language_for_is_suffix_based_and_case_insensitive() -> None:
    assert language_for("src/main.RS")["language"] == "rust"
    assert language_for(Path("a.tsx"))["language"] == "tsx"
    assert language_for("header.h")["language"] == "c"
    assert language_for("header.hpp")["language"] == "cpp"
    assert language_for("Makefile") is None
    assert language_for("notes.txt") is None


def test_available_languages_are_sorted_unique_and_usable() -> None:
    languages = available_languages()
    assert languages == sorted(languages)
    assert len(languages) == len(set(languages))
    assert "python" in languages
    labels = {entry["language"] for entry in LANGUAGES.values()}
    assert set(languages) <= labels
    for label in languages:
        status = backend_status(label)
        assert status["available"] is True
        assert status["error"] is None


def test_backend_status_unknown_language_is_honest() -> None:
    status = backend_status("brainfuck")
    assert status["available"] is False
    assert status["module"] is None
    assert "unknown language" in status["error"]


@pytest.mark.parametrize("label,definitions,references", [
    ("python", True, True),
    ("rust", True, True),
    ("lua", True, True),
    ("typescript", True, True),
    ("tsx", True, True),
    ("javascript", True, True),
    ("go", True, True),
    ("java", True, True),
    ("c", True, False),
    ("cpp", True, False),
])
def test_backend_status_reports_capture_classes(
        label: str, definitions: bool, references: bool) -> None:
    status = _skip_if_unavailable(label)
    assert status["definitions"] is definitions
    assert status["references"] is references
    assert status["suffixes"]
    if status["tags_query"] is not None:
        query = Path(status["tags_query"])
        assert query.is_file()
        assert query.name == "tags.scm"


@pytest.mark.parametrize("case", CASES, ids=CASE_IDS)
def test_definition_per_grammar(case: dict) -> None:
    _skip_if_unavailable(case["label"])
    if case["definition"] is None:
        pytest.skip(
            f"{case['label']}: upstream tags.scm declares no definition "
            "capture for this snippet's declaration form")
    tags = extract_tags("sample" + case["suffix"], case["source"])
    matches = [tag for tag in tags
               if tag["kind"] == "def" and tag["name"] == case["definition"]]
    assert matches, f"missing definition {case['definition']!r}: {tags}"
    assert any(tag["detail"] == case["definition_detail"] for tag in matches)
    assert all(tag["line"] >= 1 for tag in matches)


@pytest.mark.parametrize("case", CASES, ids=CASE_IDS)
def test_reference_per_grammar(case: dict) -> None:
    status = _skip_if_unavailable(case["label"])
    if case["reference"] is None:
        assert status["references"] is False
        pytest.skip(
            f"{case['label']}: upstream tags.scm has no reference captures")
    tags = extract_tags("sample" + case["suffix"], case["source"])
    matches = [tag for tag in tags
               if tag["kind"] == "ref" and tag["name"] == case["reference"]]
    assert matches, f"missing reference {case['reference']!r}: {tags}"
    assert any(tag["detail"] == case["reference_detail"] for tag in matches)
    assert all(tag["line"] >= 1 for tag in matches)


def test_tag_dict_shape_and_determinism() -> None:
    source = "def alpha(x):\n    return helper(x)\n"
    first = extract_tags("x.py", source)
    second = extract_tags("x.py", source)
    assert first == second
    assert first
    required = {
        "def": {"name", "kind", "detail", "line", "end_line", "qualname"},
        "ref": {"name", "kind", "detail", "line", "scope"},
        "import": {"name", "kind", "detail", "line", "module", "level",
                   "imported", "scope"},
    }
    for tag in first:
        assert tag["kind"] in required
        assert set(tag) == required[tag["kind"]]
        assert isinstance(tag["name"], str) and tag["name"]
        assert isinstance(tag["detail"], str) and tag["detail"]
        assert isinstance(tag["line"], int) and tag["line"] >= 1


def test_python_fast_path_matches_ocelot_repo_map() -> None:
    # Imported lazily: the registry must not depend on the repo map module.
    from scripts.ocelot_repo_map import extract_tags as repo_map_tags

    source = (
        "import helper\n"
        "\n"
        "class Alpha:\n"
        "    def beta(self, value):\n"
        "        return helper.run(value)\n"
        "\n"
        "def gamma():\n"
        "    return Alpha()\n"
    )
    assert extract_tags("x.py", source) == repo_map_tags("x.py", source)


def test_python_syntax_error_and_unknown_suffix_return_empty() -> None:
    assert extract_tags("x.py", "def broken(:\n") == []
    assert extract_tags("x.txt", "def alpha():\n    return 1\n") == []


def test_js_jsx_and_tsx_parse_jsx_with_tsx_factory() -> None:
    source = "const node = <Widget prop={new Thing()} />;\n"
    for suffix, label in ((".js", "javascript"), (".jsx", "javascript"),
                          (".tsx", "tsx")):
        _skip_if_unavailable(label)
        tags = extract_tags("component" + suffix, source)
        assert any(tag["kind"] == "ref" and tag["name"] == "Thing"
                   for tag in tags), tags


def test_c_family_suffix_aliases_extract_definitions() -> None:
    assert "alpha" in _defs(extract_tags(
        "x.h", "int alpha(int x) { return beta(x); }\n"))
    for suffix in (".cpp", ".cc", ".cxx", ".hpp"):
        assert "Gamma" in _defs(extract_tags(
            "x" + suffix, "class Gamma { public: int v; };\n"))


def test_missing_backend_degrades_honestly(monkeypatch) -> None:
    def unavailable(*_args, **_kwargs):
        raise ImportError("grammar not installed")

    monkeypatch.setattr(tag_languages, "_load_tree_sitter_backend",
                        unavailable)
    assert extract_tags("x.rs", "fn alpha() {}\n") == []
    status = backend_status("rust")
    assert status["available"] is False
    assert "ImportError" in status["error"]
    assert "rust" not in available_languages()
    # Python's AST path does not need a tree-sitter grammar.
    assert "python" in available_languages()


def test_extract_tags_status_reports_backend_error(monkeypatch) -> None:
    def broken_loader(*_args):
        raise RuntimeError("no grammar")

    monkeypatch.setattr(tag_languages, "_load_tree_sitter_backend",
                        broken_loader)
    tags, error = tag_languages.extract_tags_status("x.rs", "fn alpha() {}\n")
    assert tags == []
    assert error == "RuntimeError: no grammar"
    assert tag_languages.extract_tags("x.rs", "fn alpha() {}\n") == []


def test_extract_tags_status_distinguishes_genuine_empty_results() -> None:
    assert tag_languages.extract_tags_status("x.py", "def broken(:\n") == ([],
                                                                          None)
    assert tag_languages.extract_tags_status("x.txt", "def a():\n") == ([],
                                                                         None)


def test_extractor_fingerprint_is_stable_and_tracks_schema(monkeypatch) -> None:
    cache_clear = tag_languages._fingerprint_for_suffix.cache_clear
    cache_clear()
    try:
        first = tag_languages.extractor_fingerprint("x.rs")
        assert tag_languages.extractor_fingerprint("y/z.rs") == first
        assert tag_languages.extractor_fingerprint(".rs") == first
        assert tag_languages.extractor_fingerprint("x.rs") == first
        assert tag_languages.extractor_fingerprint("x.py") != first
        monkeypatch.setattr(tag_languages, "TAGS_SCHEMA_VERSION",
                            tag_languages.TAGS_SCHEMA_VERSION + 1)
        cache_clear()
        assert tag_languages.extractor_fingerprint("x.rs") != first
    finally:
        monkeypatch.undo()
        cache_clear()
    assert tag_languages.extractor_fingerprint("x.rs") == first


# ---------------------------------------------------------------------------
# Schema v2: qualname/scope/end_line and Python import tags (W2-C).
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[1]


def _base_python_tags(source: str) -> list[dict]:
    """Oracle: the pre-v2 ``_python_tags`` copied verbatim from f88fcfda.

    ``git show f88fcfda:scripts/ocelot_tag_languages.py`` holds the original.
    Kept inline so the test does not depend on git history.
    """
    import ast

    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return []
    out: list[dict] = []
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


REAL_PY_FILES = [
    "scripts/ocelot_repo_map.py",
    "scripts/ocelot_code_edit.py",
    "substrate/seed_loader.py",
    "domains/ts_ingest.py",
    "tests/test_repo_map_migrated.py",
    "scripts/ocelot_tag_languages.py",
]


def _def_ref_tuples(tags: list[dict]) -> list[tuple]:
    return [(t["name"], t["kind"], t["detail"], t["line"])
            for t in tags if t["kind"] in {"def", "ref"}]


@pytest.mark.parametrize("rel", REAL_PY_FILES)
def test_python_def_ref_tuples_match_base_extractor(rel: str) -> None:
    from collections import Counter

    source = (REPO_ROOT / rel).read_text(encoding="utf-8")
    base = _def_ref_tuples(_base_python_tags(source))
    new = _def_ref_tuples(extract_tags(rel, source))
    assert set(base) == set(new)
    assert Counter(base) == Counter(new)
    assert base, "fixture file produced no tags"


def test_python_qualname_and_scope_nested_class_and_function() -> None:
    source = (
        "class Outer:\n"                        # 1
        "    class Inner:\n"                    # 2
        "        def method(self):\n"           # 3
        "            return helper(self)\n"     # 4
        "\n"                                    # 5
        "def f():\n"                            # 6
        "    def inner():\n"                    # 7
        "        return g()\n"                  # 8
        "    return inner\n"                    # 9
        "\n"                                    # 10
        "top_value = h()\n"                     # 11
    )
    tags = extract_tags("pkg/mod.py", source)
    defs = {t["qualname"]: t for t in tags if t["kind"] == "def"}
    assert set(defs) == {"Outer", "Outer.Inner", "Outer.Inner.method",
                         "f", "f.inner"}
    assert defs["Outer.Inner.method"]["line"] == 3
    assert defs["Outer.Inner.method"]["end_line"] == 4
    assert defs["f.inner"]["end_line"] == 8
    refs = {t["name"]: t["scope"] for t in tags if t["kind"] == "ref"}
    assert refs["helper"] == "Outer.Inner.method"
    assert refs["g"] == "f.inner"
    assert refs["h"] == ""
    # Decorators and default values sit in the enclosing scope, not the body.
    deco = extract_tags("x.py", "@wrap\ndef f(a=dflt):\n    return a\n")
    refs_deco = {t["name"]: t["scope"] for t in deco if t["kind"] == "ref"}
    assert refs_deco["wrap"] == ""
    assert refs_deco["dflt"] == ""
    assert refs_deco["a"] == "f"


def test_python_import_tags_cover_all_four_forms() -> None:
    source = (
        "import a.b\n"
        "import a.b as c\n"
        "from .m import x as y\n"
        "from pkg.mod import helper\n"
        "def run():\n"
        "    from ..deep import z\n"
    )
    imports = [t for t in extract_tags("pkg/use.py", source)
               if t["kind"] == "import"]
    by_name = {t["name"]: t for t in imports}
    assert set(by_name) == {"a", "c", "y", "helper", "z"}
    assert by_name["a"] == {"name": "a", "kind": "import",
                            "detail": "import.module", "line": 1,
                            "module": "a.b", "level": 0,
                            "imported": "a.b", "scope": ""}
    assert by_name["c"]["module"] == "a.b"
    assert by_name["c"]["imported"] == "a.b"
    assert by_name["c"]["detail"] == "import.module"
    assert by_name["y"] == {"name": "y", "kind": "import",
                            "detail": "import.from", "line": 3,
                            "module": "m", "level": 1,
                            "imported": "x", "scope": ""}
    assert by_name["helper"]["module"] == "pkg.mod"
    assert by_name["helper"]["level"] == 0
    assert by_name["helper"]["imported"] == "helper"
    assert by_name["z"]["module"] == "deep"
    assert by_name["z"]["level"] == 2
    assert by_name["z"]["scope"] == "run"


def test_python_star_import_is_not_tagged() -> None:
    assert [t for t in extract_tags("x.py", "from pkg import *\n")
            if t["kind"] == "import"] == []


def test_rust_method_in_mod_gets_qualname_and_call_scope() -> None:
    source = (
        "mod outer {\n"
        "    fn inner_fn() { helper(1); }\n"
        "}\n"
        "fn top() { g(); }\n"
    )
    tags = extract_tags("x.rs", source)
    defs = {t["name"]: t for t in tags if t["kind"] == "def"}
    assert defs["outer"]["qualname"] == "outer"
    assert defs["inner_fn"]["qualname"] == "outer.inner_fn"
    assert defs["inner_fn"]["end_line"] == 2
    assert defs["top"]["qualname"] == "top"
    refs = {t["name"]: t["scope"] for t in tags if t["kind"] == "ref"}
    assert refs["helper"] == "outer.inner_fn"
    assert refs["g"] == "top"


def test_java_method_inside_class_nests_under_class() -> None:
    # Java is used for the nesting check because its tags.scm captures both
    # the class and its methods. Go's method_declaration is not nested under a
    # type, and TypeScript captures no ordinary class_declaration.
    source = ("class Alpha {\n"
              "  int beta(int x) { return gamma(x); }\n"
              "}\n")
    tags = extract_tags("Alpha.java", source)
    defs = {t["name"]: t for t in tags if t["kind"] == "def"}
    assert defs["Alpha"]["qualname"] == "Alpha"
    assert defs["beta"]["qualname"] == "Alpha.beta"
    assert defs["beta"]["end_line"] == 2
    refs = {t["name"]: t["scope"] for t in tags if t["kind"] == "ref"}
    assert refs["gamma"] == "Alpha.beta"


def test_tree_sitter_tags_are_in_source_order_and_deterministic() -> None:
    source = ("fn a() { b(); }\n"
              "fn c() { d(); }\n")
    first = extract_tags("x.rs", source)
    assert first == extract_tags("x.rs", source)
    lines = [t["line"] for t in first]
    assert lines == sorted(lines)
    assert all(t.get("end_line", t["line"]) >= t["line"] for t in first)


def test_python_bom_source_yields_the_same_tags() -> None:
    source = "import os\n\ndef alpha(x):\n    return helper(x)\n"
    plain = extract_tags("x.py", source)
    assert plain
    assert extract_tags("x.py", "\ufeff" + source) == plain
    assert tag_languages.TAGS_SCHEMA_VERSION == 3
