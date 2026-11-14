"""ocelot_dev_memory — a mechanical repo-memory index + query layer for coding agents.

DEV TOOLING, NOT AGENT RUNTIME. This module builds a *separate* graph snapshot
of a source checkout (files, symbols, tests, seeds, rules, docs, git history,
known failures) and answers read-only questions over it. It never boots the
agent, never mutates the agent substrate, and never decides what a coding agent
should do. The external coding agent (OpenCode, Claude Code, ...) is the
decider; Ocelot is the memory and the citation source.

Why a graph and not an embeddings index: the useful development questions are
typed and relational — "which tests cover this seed?", "which rules does this
seed ship?", "which files import this module?", "what changed recently near
this symbol?". Those are edge traversals, not fuzzy similarity. The snapshot is
also stable, inspectable and diffable.

Graph shape (all node/edge types are ordinary typed-graph data):

    Repo -contains-> File
    File -defines-> Symbol | Seed | Doc | Test
    File -imports-> File
    File -has_test-> Test
    Test -tests_module-> File
    Test -mentions_file-> File
    Test -mentions_seed-> Seed
    Seed -depends_on-> Seed
    Seed -contains-> Rule | Concept | Reflex | Microtheory | <seed node type>
    Seed -defined_in-> File
    Doc -documents-> File | Seed
    Commit -changes-> File
    Failure -refers_to-> Test
    Failure -in_file-> File

Usage:

    # build (or refresh) the snapshot
    .venv/bin/python -m scripts.ocelot_dev_memory build

    # query
    .venv/bin/python -m scripts.ocelot_dev_memory search "shape decode"
    .venv/bin/python -m scripts.ocelot_dev_memory symbol compose_design_for_goal
    .venv/bin/python -m scripts.ocelot_dev_memory tests seeds/shape_decode_loop.json
    .venv/bin/python -m scripts.ocelot_dev_memory context "add a new seed rule"
    .venv/bin/python -m scripts.ocelot_dev_memory record --kind decision \
        --task "..." --summary "..." --file domains/teach.py

The same surface is exposed over MCP by `scripts/ocelot_dev_memory_mcp.py`.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DUMP = ROOT / "var" / "ocelot_dev_graph.json"
DEFAULT_JOURNAL = ROOT / "var" / "ocelot_dev_journal.jsonl"

# Files larger than this are indexed by path/name only; their content is not
# parsed. A repo map should stay fast and should never hang on a generated blob.
MAX_PARSE_BYTES = 2 * 1024 * 1024

# Directories that are never part of the development surface.
SKIP_PARTS = {
    ".git", ".venv", ".venv-jsbsim-f16", "__pycache__", ".pytest_cache",
    ".mypy_cache", ".ruff_cache", "node_modules", "target", "build",
    ".worktrees", ".claude", "data", "var", "runs", "recordings",
    "scratch_rr", "scratchpad3", ".bigtmp", "vizdoom",
}

SOURCE_DIRS = (
    "runners/dsl/src",
    "runners/dsl/tests",
    "domains",
    "domains_rs",
    "worlds",
    "substrate",
    "tools",
    "scripts",
)

DOC_GLOBS = (
    "docs/features/*.md",
    "docs/CODE_MAP.md",
    "docs/SEED_DEVELOPMENT.md",
    "docs/SCIENCE_RESEARCH.md",
    "docs/research/engine_substrate/GRAPH_INTERROGATE.md",
    "README.md",
    "CLAUDE.md",
    "VISION_PROTOCOL.md",
    "HISTORY.md",
    "RESULTS.local.md",
)

ALL_DOC_GLOBS = ("docs/**/*.md",) + DOC_GLOBS

# Words that describe the ACT of a development task rather than its subject.
# They are still matched, but they do not earn "specific term" weight.
_GENERIC_QUERY_TOKENS = {
    "add", "new", "make", "use", "used", "using", "fix", "update", "change",
    "create", "implement", "write", "remove", "delete", "refactor", "move",
    "rename", "support", "allow", "enable", "disable", "improve", "better",
    "issue", "bug", "problem", "work", "need", "want", "help", "like",
    "added", "existing", "current", "proper", "correct", "simple",
}

_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "how",
    "in", "is", "it", "of", "on", "or", "that", "the", "this", "to", "with",
    "what", "when", "where", "which", "who", "why", "do", "does", "can",
    "should", "would", "could", "i", "we", "you", "my", "our", "your",
}

_PATH_RE = re.compile(
    r"(?<![\w./-])((?:runners|domains|domains_rs|worlds|substrate|scripts|tools|"
    r"tests|seeds|docs|evaluation|benchmarks)/[A-Za-z0-9_./-]+)"
)
_SEED_PATH_RE = re.compile(r"seeds/([A-Za-z0-9_.-]+)\.json")
_TEST_NAME_RE = re.compile(r"^test_[A-Za-z0-9_]+$")

# LSP wait for `symbol_graph(precise=True)` reference queries, in seconds.
PRECISE_TIMEOUT = 20.0
# LSP wait for the push diagnostics that follow an applied `edit`, in seconds.
POST_EDIT_DIAG_TIMEOUT = 8.0
# Diagnostic items kept in the post-edit result. The counts cover all of them.
DIAG_ITEM_LIMIT = 20
_DEF_KEYWORD_RE = re.compile(r"\b(?:def|class)\b")


def _utf16_col(line_text: str, char_index: int) -> int:
    """LSP character offset (UTF-16 code units) of a Python str index."""
    return len(line_text[:char_index].encode("utf-16-le")) // 2


def _name_utf16_col(line_text: str, name: str) -> int | None:
    """UTF-16 column of the definition name on a def/class line.

    The search starts at the ``def``/``class`` keyword when the line has one,
    so a name that also appears earlier on the line is not picked.
    """
    kw = _DEF_KEYWORD_RE.search(line_text)
    start = kw.end() if kw else 0
    hit = re.compile(rf"(?<![A-Za-z0-9_]){re.escape(name)}(?![A-Za-z0-9_])"
                     ).search(line_text, start)
    return None if hit is None else _utf16_col(line_text, hit.start())


def _read_text(path: Path, *, limit: int = MAX_PARSE_BYTES) -> str | None:
    try:
        if path.stat().st_size > limit:
            return None
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def _rel(root: Path, path: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _skipped(rel: str) -> bool:
    return any(part in SKIP_PARTS for part in rel.split("/"))


def _first_line(text: str | None) -> str:
    if not text:
        return ""
    for line in text.strip().splitlines():
        line = line.strip()
        if line:
            return line[:240]
    return ""


def _tokens(text: str) -> list[str]:
    raw = re.findall(r"[A-Za-z0-9_./-]+", (text or "").lower())
    return [t for t in raw if len(t) > 1 and t not in _STOPWORDS]


_CAMEL_RE = re.compile(r"([a-z0-9])([A-Z])")
_WORD_RE = re.compile(r"[A-Za-z0-9]+")


def _word_tokens(text: str) -> list[str]:
    """Split an identifier/path/title into lowercase word tokens.

    `_shape_decode_agent` -> shape, decode, agent; `shapeDecode` -> shape,
    decode; `test_a15_added_rules` -> test, a15, added, rules.
    """
    spaced = _CAMEL_RE.sub(r"\1 \2", str(text or ""))
    return [t.lower() for t in _WORD_RE.findall(spaced)]


def _stem(token: str) -> str:
    """A deliberately tiny plural stem; not a linguistic claim."""
    t = token.lower()
    if len(t) > 4 and t.endswith("ies"):
        return t[:-3] + "y"
    if len(t) > 3 and t.endswith("s") and not t.endswith("ss"):
        return t[:-1]
    return t


# --------------------------------------------------------------------------- #
# graph builder
# --------------------------------------------------------------------------- #
@dataclass
class Builder:
    nodes: list[dict[str, Any]] = field(default_factory=list)
    edges: list[dict[str, Any]] = field(default_factory=list)
    _by_key: dict[tuple, int] = field(default_factory=dict)
    _edge_keys: set[tuple[int, str, int]] = field(default_factory=set)
    _next: int = 0

    def node(self, type_name: str, attrs: dict[str, Any] | None = None,
             *, key: tuple | None = None) -> int:
        if key is not None and key in self._by_key:
            return self._by_key[key]
        nid = self._next
        self._next += 1
        self.nodes.append({"id": nid, "type": type_name,
                           "attrs": dict(attrs or {})})
        if key is not None:
            self._by_key[key] = nid
        return nid

    def edge(self, src: int | None, type_name: str, tgt: int | None,
             attrs: dict[str, Any] | None = None) -> None:
        if src is None or tgt is None:
            return
        key = (int(src), type_name, int(tgt))
        if key in self._edge_keys:
            return
        self._edge_keys.add(key)
        self.edges.append({"src": int(src), "type": type_name,
                           "tgt": int(tgt), "attrs": dict(attrs or {})})

    def to_dict(self) -> dict[str, Any]:
        return {"nodes": self.nodes, "edges": self.edges,
                "next_id": self._next}

    def count(self, type_name: str) -> int:
        return sum(1 for n in self.nodes if n["type"] == type_name)


# --------------------------------------------------------------------------- #
# parsers (mechanical translation only)
# --------------------------------------------------------------------------- #
@dataclass
class PyParse:
    symbols: list[dict[str, Any]] = field(default_factory=list)
    imports: list[dict[str, Any]] = field(default_factory=list)
    tests: list[dict[str, Any]] = field(default_factory=list)
    module_doc: str = ""
    source: str = ""


def _python_parse(path: Path) -> PyParse | None:
    src = _read_text(path)
    if src is None:
        return None
    # A UTF-8 byte order mark is not Python source; ast.parse rejects it.
    # Stripping it leaves every line number unchanged.
    if src.startswith("\ufeff"):
        src = src[1:]
    try:
        tree = ast.parse(src)
    except (SyntaxError, ValueError):
        return None

    out = PyParse(module_doc=_first_line(ast.get_docstring(tree)), source=src)

    def decorators(n: ast.AST) -> list[str]:
        got = []
        for d in getattr(n, "decorator_list", []) or []:
            try:
                got.append(ast.unparse(d)[:120])
            except Exception:
                pass
        return got

    def add_symbol(n: ast.AST, prefix: str, *, in_test_class: bool) -> None:
        name = getattr(n, "name", "")
        qual = f"{prefix}.{name}" if prefix else name
        if isinstance(n, ast.ClassDef):
            kind = "class"
        elif isinstance(n, ast.AsyncFunctionDef):
            kind = "async_function"
        else:
            kind = "function"
        doc = _first_line(ast.get_docstring(n)) if hasattr(n, "body") else ""
        args: list[str] = []
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
            try:
                args = [a.arg for a in n.args.args]
            except Exception:
                args = []
        returns = ""
        if getattr(n, "returns", None) is not None:
            try:
                returns = ast.unparse(n.returns)[:100]
            except Exception:
                returns = ""
        bases: list[str] = []
        if isinstance(n, ast.ClassDef):
            for b in n.bases:
                try:
                    bases.append(ast.unparse(b)[:100])
                except Exception:
                    pass
        rec = {
            "name": name,
            "qualname": qual,
            "kind": kind,
            "start_line": int(getattr(n, "lineno", 1) or 1),
            "end_line": int(getattr(n, "end_lineno", getattr(n, "lineno", 1)) or 1),
            "doc": doc,
            "decorators": decorators(n),
            "args": args,
            "returns": returns,
            "bases": bases,
        }
        out.symbols.append(rec)
        is_test = (name.startswith("test_") and
                   (prefix == "" or in_test_class))
        if is_test:
            out.tests.append(dict(rec))

    def walk(body: Iterable[ast.AST], prefix: str = "",
             in_test_class: bool = False) -> None:
        for n in body:
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef,
                              ast.ClassDef)):
                add_symbol(n, prefix, in_test_class=in_test_class)
                q = f"{prefix}.{n.name}" if prefix else n.name
                child_test = in_test_class or (
                    isinstance(n, ast.ClassDef) and n.name.startswith("Test"))
                walk(n.body, q, in_test_class=child_test)
            else:
                # Keep looking inside non-definition statements for imports
                # and nested definitions (e.g. an if TYPE_CHECKING block).
                for child in ast.iter_child_nodes(n):
                    walk([child], prefix, in_test_class=in_test_class)

    # Module body: definitions plus module-level imports.
    walk(tree.body)
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            out.imports.append({
                "module": "", "level": 0,
                "names": [a.name for a in n.names],
            })
        elif isinstance(n, ast.ImportFrom):
            out.imports.append({
                "module": n.module or "", "level": int(n.level or 0),
                "names": [a.name for a in n.names],
            })
    return out


_RUST_SYM_RE = re.compile(
    r"^\s*(?:pub(?:\([^)]*\))?\s+)?"
    r"(?:async\s+|unsafe\s+|const\s+|extern\s+\"[^\"]+\"\s+)*"
    r"(fn|struct|enum|trait|impl|mod|type|const|static)\s+"
    r"([A-Za-z_][A-Za-z0-9_]*)"
)
_RUST_MOD_RE = re.compile(r"^\s*(?:pub\s+)?mod\s+([A-Za-z_][A-Za-z0-9_]*)\s*;")


def _rust_parse(path: Path) -> dict[str, Any] | None:
    src = _read_text(path)
    if src is None:
        return None
    symbols: list[dict[str, Any]] = []
    mods: list[str] = []
    for i, line in enumerate(src.splitlines(), start=1):
        m = _RUST_SYM_RE.match(line)
        if m:
            kind, name = m.group(1), m.group(2)
            if kind == "impl":
                # Keep the impl head as the name so `impl Foo` is searchable.
                name = line.strip()[len("impl"):].strip()[:120]
            symbols.append({
                "name": name.split()[0] if name else kind,
                "qualname": name or kind,
                "kind": kind,
                "start_line": i,
                "end_line": i,
                "doc": "",
                "decorators": [],
                "args": [],
            })
        mm = _RUST_MOD_RE.match(line)
        if mm:
            mods.append(mm.group(1))
    return {"symbols": symbols, "mods": mods, "source": src}


def _resolve_import(root: Path, rel_file: str, imp: dict[str, Any]) -> str | None:
    module = imp.get("module") or ""
    level = int(imp.get("level") or 0)
    parts = [p for p in module.split(".") if p]
    if level > 0:
        base = Path(rel_file).parent
        for _ in range(level - 1):
            base = base.parent
        candidates = [base.joinpath(*parts).with_suffix(".py"),
                      base.joinpath(*parts, "__init__.py")]
    else:
        if not parts:
            return None
        candidates = [Path(*parts).with_suffix(".py"),
                      Path(*parts, "__init__.py")]
    search_roots = [root, root / "runners" / "dsl" / "python"]
    for base in search_roots:
        for cand in candidates:
            p = (base / cand)
            try:
                if p.is_file():
                    return p.resolve().relative_to(root.resolve()).as_posix()
            except (OSError, ValueError):
                continue
    return None


def _seed_items(d: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten the several seed container shapes into SeedItem records."""
    items: list[dict[str, Any]] = []

    for i, node in enumerate(d.get("nodes") or []):
        if not isinstance(node, dict):
            continue
        attrs = node.get("attrs") or {}
        typ = str(node.get("type") or "SeedItem")
        name = str(attrs.get("name") or attrs.get("id") or
                   f"{typ}#{node.get('local_id', i)}")
        items.append({"type": typ, "name": name, "attrs": dict(attrs),
                      "local_id": node.get("local_id", i), "container": "nodes"})

    for i, rule in enumerate(d.get("rules") or []):
        if isinstance(rule, dict):
            name = str(rule.get("name") or f"rule#{i}")
            items.append({"type": "Rule", "name": name, "attrs": {},
                          "local_id": i, "container": "rules",
                          "where_type": (rule.get("where") or {}).get("type", "")})
        elif isinstance(rule, str):
            items.append({"type": "Rule", "name": rule, "attrs": {},
                          "local_id": i, "container": "rules"})

    for i, concept in enumerate(d.get("concepts") or []):
        if isinstance(concept, dict):
            name = str(concept.get("name") or concept.get("id") or f"concept#{i}")
            attrs = {k: v for k, v in concept.items()
                     if isinstance(v, (str, int, float, bool))}
        else:
            name = str(concept)
            attrs = {}
        items.append({"type": "Concept", "name": name, "attrs": attrs,
                      "local_id": i, "container": "concepts"})

    for i, prod in enumerate(d.get("productions") or []):
        name = f"production#{i}"
        attrs: dict[str, Any] = {}
        if isinstance(prod, dict):
            name = str(prod.get("provenance") or prod.get("name") or name)
            attrs = {"src": str(prod.get("src", ""))[:200],
                     "edge_type": str(prod.get("edge_type", "")),
                     "tgt": str(prod.get("tgt", ""))[:200]}
        elif isinstance(prod, (list, tuple)):
            attrs = {"src": str(prod[0])[:200] if len(prod) > 0 else "",
                     "edge_type": str(prod[1]) if len(prod) > 1 else "",
                     "tgt": str(prod[2])[:200] if len(prod) > 2 else ""}
        items.append({"type": "Production", "name": name, "attrs": attrs,
                      "local_id": i, "container": "productions"})

    mt = d.get("microtheory")
    if isinstance(mt, dict):
        items.append({"type": "Microtheory",
                      "name": str(mt.get("name") or "microtheory"),
                      "attrs": {"description": str(mt.get("description", ""))[:1000]},
                      "local_id": 0, "container": "microtheory"})

    for i, reflex in enumerate(d.get("reflexes") or []):
        name = (str(reflex.get("name") or f"reflex#{i}")
                if isinstance(reflex, dict) else str(reflex))
        items.append({"type": "Reflex", "name": name, "attrs": {},
                      "local_id": i, "container": "reflexes"})

    for i, goal in enumerate(d.get("goals") or []):
        name = (str(goal.get("name") or f"goal#{i}")
                if isinstance(goal, dict) else str(goal))
        items.append({"type": "GoalSpec", "name": name, "attrs": {},
                      "local_id": i, "container": "goals"})

    return items


# --------------------------------------------------------------------------- #
# build
# --------------------------------------------------------------------------- #
def _iter_paths(root: Path, rel_dir: str, suffixes: tuple[str, ...],
                *, path_filter=None) -> Iterable[Path]:
    base = root / rel_dir
    if not base.exists():
        return
    for p in sorted(base.rglob("*")):
        if not p.is_file() or p.suffix not in suffixes:
            continue
        try:
            rel = _rel(root, p)
        except ValueError:
            continue
        if _skipped(rel):
            continue
        if path_filter is not None and not path_filter(rel):
            continue
        yield p


def build_index(root: str | Path = ROOT, out: str | Path = DEFAULT_DUMP,
                *, include_docs: str = "features", include_git: bool = True,
                include_scripts: bool = True,
                git_limit: int = 200) -> dict[str, Any]:
    """Build the dev-memory graph and write it to `out`.

    `include_docs`: "features" (default), "all", or "none".
    Returns the graph dict plus a small build report.
    """
    root = Path(root).resolve()
    out = Path(out)
    b = Builder()
    t0 = time.time()

    repo = b.node("Repo", {
        "name": root.name,
        "root": str(root),
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
    })
    files: dict[str, int] = {}

    def file_node(rel: str, *, indexed: bool = True) -> int:
        if rel in files:
            return files[rel]
        p = root / rel
        lang = p.suffix.lstrip(".").lower() or "unknown"
        attrs: dict[str, Any] = {
            "name": rel,
            "path": rel,
            "language": lang,
            "indexed": 1 if indexed else 0,
        }
        try:
            if p.exists():
                attrs["size"] = int(p.stat().st_size)
        except OSError:
            pass
        nid = b.node("File", attrs, key=("file", rel))
        files[rel] = nid
        b.edge(repo, "contains", nid)
        return nid

    # Test->seed mentions are resolved after the seed manifests are loaded
    # (a test file can mention a seed that appears later in the walk).
    pending_test_seed: list[tuple[int, str]] = []
    pending_file_seed: list[tuple[int, str]] = []

    # -- source / test / script files ------------------------------------- #
    src_dirs = list(SOURCE_DIRS)
    if not include_scripts:
        src_dirs = [d for d in src_dirs if d != "scripts"]
    py_files: list[tuple[str, int, PyParse]] = []
    for rel_dir in src_dirs:
        for p in _iter_paths(root, rel_dir, (".py", ".rs", ".lua")):
            rel = _rel(root, p)
            fid = file_node(rel)
            if p.suffix == ".py":
                parsed = _python_parse(p)
                if parsed is None:
                    continue
                py_files.append((rel, fid, parsed))
                if parsed.module_doc:
                    b.nodes[fid]["attrs"]["doc"] = parsed.module_doc
                for sym in parsed.symbols:
                    sid = b.node("Symbol", {
                        "name": sym["name"],
                        "qualname": sym["qualname"],
                        "kind": sym["kind"],
                        "file": rel,
                        "start_line": sym["start_line"],
                        "end_line": sym["end_line"],
                        "doc": sym["doc"],
                        "decorators": sym["decorators"],
                        "args": sym["args"],
                        "returns": sym.get("returns", ""),
                        "bases": sym.get("bases", []),
                    }, key=("symbol", rel, sym["qualname"]))
                    b.edge(fid, "defines", sid)
                    b.edge(sid, "defined_in", fid)
                    if "." in sym["qualname"]:
                        parent_q = sym["qualname"].rsplit(".", 1)[0]
                        parent = b._by_key.get(("symbol", rel, parent_q))
                        if parent is not None:
                            b.edge(parent, "contains_symbol", sid)
                for imp in parsed.imports:
                    target = _resolve_import(root, rel, imp)
                    if target:
                        b.edge(fid, "imports", file_node(target))
                for seed_id in set(_SEED_PATH_RE.findall(parsed.source or "")):
                    pending_file_seed.append((fid, seed_id))
            elif p.suffix == ".rs":
                parsed = _rust_parse(p)
                if parsed is None:
                    continue
                for sym in parsed["symbols"]:
                    sid = b.node("Symbol", {
                        "name": sym["name"],
                        "qualname": sym["qualname"],
                        "kind": sym["kind"],
                        "file": rel,
                        "start_line": sym["start_line"],
                        "end_line": sym["end_line"],
                        "doc": "",
                        "decorators": [],
                        "args": [],
                    }, key=("symbol", rel, f"rust:{sym['start_line']}:{sym['qualname']}"))
                    b.edge(fid, "defines", sid)
                    b.edge(sid, "defined_in", fid)
                for mod in parsed["mods"]:
                    target = (Path(rel).parent / f"{mod}.rs").as_posix()
                    if (root / target).is_file():
                        b.edge(fid, "imports", file_node(target))
                for seed_id in set(_SEED_PATH_RE.findall(parsed.get("source") or "")):
                    pending_file_seed.append((fid, seed_id))

    # -- tests ------------------------------------------------------------- #
    for p in _iter_paths(root, "tests", (".py",),
                         path_filter=lambda r: Path(r).name.startswith("test_")):
        rel = _rel(root, p)
        fid = file_node(rel)
        parsed = _python_parse(p)
        if parsed is None:
            continue
        py_files.append((rel, fid, parsed))
        if parsed.module_doc:
            b.nodes[fid]["attrs"]["doc"] = parsed.module_doc
        for sym in parsed.symbols:
            # Test functions get a Test node below; do not duplicate them as
            # Symbols. Helper functions/classes in a test module stay Symbols.
            if (sym["name"].startswith("test_")
                    and sym["kind"] in ("function", "async_function")):
                continue
            sid = b.node("Symbol", {
                "name": sym["name"],
                "qualname": sym["qualname"],
                "kind": sym["kind"],
                "file": rel,
                "start_line": sym["start_line"],
                "end_line": sym["end_line"],
                "doc": sym["doc"],
                "decorators": sym["decorators"],
                "args": sym["args"],
                "returns": sym.get("returns", ""),
                "bases": sym.get("bases", []),
            }, key=("symbol", rel, sym["qualname"]))
            b.edge(fid, "defines", sid)
            b.edge(sid, "defined_in", fid)
        for imp in parsed.imports:
            target = _resolve_import(root, rel, imp)
            if target:
                b.edge(fid, "imports", file_node(target))
        for test in parsed.tests:
            tid = b.node("Test", {
                "name": test["name"],
                "qualname": test["qualname"],
                "file": rel,
                "start_line": test["start_line"],
                "end_line": test["end_line"],
                "doc": test["doc"],
            }, key=("test", rel, test["qualname"]))
            b.edge(fid, "has_test", tid)
            b.edge(tid, "tested_by_file", fid)
            if test["doc"]:
                b.nodes[tid]["attrs"]["doc"] = test["doc"]
        # Test-file -> module links (imports) and literal path / seed mentions.
        src = _read_text(p) or ""
        seen_mods: set[int] = set()
        for imp in parsed.imports:
            target = _resolve_import(root, rel, imp)
            if not target:
                continue
            target_nid = file_node(target)
            for test in parsed.tests:
                tid = b._by_key.get(("test", rel, test["qualname"]))
                if tid is not None and target_nid not in seen_mods:
                    b.edge(tid, "tests_module", target_nid)
            seen_mods.add(target_nid)
        for path_match in _PATH_RE.findall(src):
            target = path_match.rstrip(".,);:")
            if (root / target).is_file():
                target_nid = file_node(target)
                for test in parsed.tests:
                    tid = b._by_key.get(("test", rel, test["qualname"]))
                    if tid is not None:
                        b.edge(tid, "mentions_file", target_nid)
        for seed_id in set(_SEED_PATH_RE.findall(src)):
            pending_file_seed.append((fid, seed_id))
            for test in parsed.tests:
                tid = b._by_key.get(("test", rel, test["qualname"]))
                if tid is not None:
                    pending_test_seed.append((tid, seed_id))

    # -- seeds ------------------------------------------------------------- #
    seed_dir = root / "seeds"
    seed_paths = sorted(seed_dir.glob("*.json")) if seed_dir.exists() else []
    seed_docs: list[tuple[str, Any]] = []
    for p in seed_paths:
        try:
            d = json.loads(p.read_text(encoding="utf-8", errors="replace"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(d, dict):
            continue
        seed_docs.append((_rel(root, p), d))
        seed_id = str(d.get("id") or p.stem)
        rel = _rel(root, p)
        fid = file_node(rel)
        sid = b.node("Seed", {
            "name": seed_id,
            "id": seed_id,
            "version": str(d.get("version", "")),
            "path": rel,
            "description": str(d.get("description", ""))[:1000],
            "depends_on": list(d.get("depends_on") or []),
        }, key=("seed", seed_id))
        # A dependency may have created a stub before the real manifest was
        # visited. Upgrade it in place; never leave a stub when the real seed
        # is present.
        seed_attrs = b.nodes[sid]["attrs"]
        if seed_attrs.get("stub"):
            seed_attrs.update({
                "name": seed_id,
                "id": seed_id,
                "version": str(d.get("version", "")),
                "path": rel,
                "description": str(d.get("description", ""))[:1000],
                "depends_on": list(d.get("depends_on") or []),
            })
            seed_attrs.pop("stub", None)
        b.edge(fid, "defines", sid)
        b.edge(sid, "defined_in", fid)
        b.edge(repo, "has_seed", sid)
        for dep in d.get("depends_on") or []:
            dep = str(dep)
            dep_nid = b._by_key.get(("seed", dep))
            if dep_nid is None:
                dep_nid = b.node("Seed", {
                    "name": dep, "id": dep, "version": "", "path": "",
                    "description": "", "depends_on": [], "stub": 1,
                }, key=("seed", dep))
            b.edge(sid, "depends_on", dep_nid)
        for item in _seed_items(d):
            inode = b.node(item["type"], {
                "name": item["name"],
                "seed": seed_id,
                "container": item["container"],
                "local_id": item["local_id"],
                **item["attrs"],
            }, key=("seed_item", seed_id, item["type"], item["name"]))
            b.edge(sid, "contains", inode)
            b.edge(inode, "in_seed", sid)
            b.edge(inode, "defined_in", fid)

    for fid, seed_id in pending_file_seed:
        seed_nid = b._by_key.get(("seed", seed_id))
        if seed_nid is not None:
            b.edge(fid, "mentions_seed", seed_nid)
    for tid, seed_id in pending_test_seed:
        seed_nid = b._by_key.get(("seed", seed_id))
        if seed_nid is not None:
            b.edge(tid, "mentions_seed", seed_nid)

    # -- docs -------------------------------------------------------------- #
    doc_paths: list[Path] = []
    if include_docs != "none":
        globs = ALL_DOC_GLOBS if include_docs == "all" else DOC_GLOBS
        seen_docs: set[str] = set()
        for pattern in globs:
            for p in root.glob(pattern):
                if not p.is_file() or p.suffix.lower() != ".md":
                    continue
                rel = _rel(root, p)
                if rel in seen_docs or _skipped(rel):
                    continue
                seen_docs.add(rel)
                doc_paths.append(p)
    for p in sorted(doc_paths):
        rel = _rel(root, p)
        text = _read_text(p, limit=1_000_000) or ""
        title = ""
        for line in text.splitlines()[:50]:
            if line.startswith("#"):
                title = line.lstrip("#").strip()[:200]
                break
        did = b.node("Doc", {
            "name": rel,
            "path": rel,
            "title": title,
            "kind": ("features" if "/features/" in rel else
                     "research" if "/research/" in rel else "root"),
        }, key=("doc", rel))
        b.edge(repo, "has_doc", did)
        # A doc is also an ordinary file: make it addressable by dev_file /
        # dev_changed and give it the same defines/defined_in symmetry as a
        # seed or source file.
        dfid = file_node(rel)
        b.edge(dfid, "defines", did)
        b.edge(did, "defined_in", dfid)
        for path_match in _PATH_RE.findall(text):
            target = path_match.rstrip(".,);:`'\"")
            if (root / target).is_file():
                b.edge(did, "documents", file_node(target))
        for seed_id in set(_SEED_PATH_RE.findall(text)):
            seed_nid = b._by_key.get(("seed", seed_id))
            if seed_nid is not None:
                b.edge(did, "documents", seed_nid)

    # -- checkout head ------------------------------------------------------ #
    # Recorded on its own (not only from the history walk below) so the
    # snapshot can always be checked for staleness, and a git failure is
    # recorded instead of being swallowed.
    try:
        rev = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"],
                             capture_output=True, text=True, timeout=30,
                             check=False)
        if rev.returncode == 0 and rev.stdout.strip():
            b.nodes[repo]["attrs"]["head"] = rev.stdout.strip()
        else:
            b.nodes[repo]["attrs"]["head_error"] = (
                rev.stderr.strip()[:300] or f"git exited {rev.returncode}")
    except (OSError, subprocess.SubprocessError) as exc:
        b.nodes[repo]["attrs"]["head_error"] = f"{type(exc).__name__}: {exc}"[:300]

    # -- git history -------------------------------------------------------- #
    if include_git:
        try:
            proc = subprocess.run(
                ["git", "-C", str(root), "log", f"-n{int(git_limit)}",
                 "--date=short", "--pretty=format:__COMMIT__%H%x09%ad%x09%s",
                 "--name-only"],
                capture_output=True, text=True, timeout=60, check=False,
            )
            commits: list[dict[str, Any]] = []
            cur: dict[str, Any] | None = None
            for line in (proc.stdout or "").splitlines():
                if line.startswith("__COMMIT__"):
                    head = line[len("__COMMIT__"):]
                    parts = head.split("\t", 2)
                    cur = {"hash": parts[0], "date": parts[1] if len(parts) > 1 else "",
                           "subject": parts[2] if len(parts) > 2 else "",
                           "files": []}
                    commits.append(cur)
                elif line.strip() and cur is not None:
                    cur["files"].append(line.strip())
            for c in commits:
                cid = b.node("Commit", {
                    "name": c["hash"][:12],
                    "hash": c["hash"],
                    "date": c["date"],
                    "subject": c["subject"],
                }, key=("commit", c["hash"]))
                for f in c["files"]:
                    rel = f.strip()
                    if not rel or _skipped(rel):
                        continue
                    fid = file_node(rel, indexed=False)
                    b.edge(cid, "changes", fid)
            if commits:
                b.nodes[repo]["attrs"].setdefault("head", commits[0]["hash"])
                b.nodes[repo]["attrs"]["head_date"] = commits[0]["date"]
                b.edge(repo, "head", b._by_key[("commit", commits[0]["hash"])])
        except (OSError, subprocess.SubprocessError):
            pass

    # -- known failures ----------------------------------------------------- #
    baseline = root / "results" / "failure_baseline.json"
    try:
        fb = json.loads(baseline.read_text(encoding="utf-8"))
        entries = fb.get("entries") if isinstance(fb, dict) else None
        for e in entries or []:
            if not isinstance(e, dict):
                continue
            node_id = str(e.get("node") or "")
            fpath = str(e.get("file") or "")
            fid = file_node(fpath, indexed=False) if fpath else None
            fail = b.node("Failure", {
                "name": node_id,
                "node": node_id,
                "file": fpath,
                "kind": str(e.get("kind", "")),
                "message": str(e.get("message", ""))[:1000],
                "class": str(e.get("class", "")),
                "last_green_commit": str(e.get("last_green_commit", "")),
            }, key=("failure", node_id))
            b.edge(repo, "has_failure", fail)
            if fid is not None:
                b.edge(fid, "has_failure", fail)
                b.edge(fail, "in_file", fid)
            # Exact test-node match: file::test_name (class methods included).
            test_name = node_id.rsplit("::", 1)[-1] if "::" in node_id else ""
            if fpath and test_name:
                tid = b._by_key.get(("test", fpath, test_name))
                if tid is None:
                    for key, nid in list(b._by_key.items()):
                        if (len(key) == 3 and key[0] == "test"
                                and key[1] == fpath
                                and str(key[2]).endswith(test_name)):
                            tid = nid
                            break
                if tid is not None:
                    b.edge(fail, "refers_to", tid)
    except (OSError, json.JSONDecodeError):
        pass

    # -- repo summary ------------------------------------------------------- #
    b.nodes[repo]["attrs"].update({
        "files": b.count("File"),
        "symbols": b.count("Symbol"),
        "tests": b.count("Test"),
        "seeds": b.count("Seed"),
        "docs": b.count("Doc"),
        "commits": b.count("Commit"),
        "failures": b.count("Failure"),
    })
    digest, digest_err = _tree_digest(root)
    if digest is not None:
        b.nodes[repo]["attrs"]["tree_digest"] = digest
    else:
        b.nodes[repo]["attrs"]["tree_digest_error"] = digest_err or "unknown"

    graph = b.to_dict()
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(out.suffix + ".tmp")
    tmp.write_text(json.dumps(graph, sort_keys=True))
    tmp.replace(out)
    return {
        "out": str(out),
        "nodes": len(graph["nodes"]),
        "edges": len(graph["edges"]),
        "types": _histogram(n["type"] for n in graph["nodes"]),
        "edge_types": _histogram(e["type"] for e in graph["edges"]),
        "seconds": round(time.time() - t0, 2),
        "root": str(root),
    }


def _histogram(values: Iterable[str]) -> dict[str, int]:
    from collections import Counter
    return dict(Counter(values).most_common())


def _strict_bool(value: Any, name: str) -> bool:
    """A boolean from a script dict. Accepts bools and the strings "true" or
    "false" (case-insensitive). Anything else is an error, not a truthy value."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str) and value.lower() in ("true", "false"):
        return value.lower() == "true"
    raise ValueError(f"{name} must be a boolean")


def _tree_digest(root: Path) -> tuple[str | None, str | None]:
    """(digest, error) for the working tree under `root`.

    The digest is sha256 over `git diff HEAD` (tracked content changes), a NUL,
    and for each untracked file under SOURCE_DIRS (sorted by git): its path, a
    NUL, then its size and sha256 of its bytes. Untracked files larger than
    MAX_PARSE_BYTES contribute path, size and mtime_ns instead. Untracked files
    that cannot be read contribute path and "unreadable".
    """
    try:
        diff = subprocess.run(
            ["git", "-C", str(root), "diff", "HEAD", "--no-color",
             "--no-ext-diff"],
            capture_output=True, timeout=60, check=False)
        untracked = subprocess.run(
            ["git", "-C", str(root), "ls-files", "-z", "--others",
             "--exclude-standard", "--", *SOURCE_DIRS],
            capture_output=True, timeout=60, check=False)
    except (OSError, subprocess.SubprocessError) as e:
        return None, str(e)
    if diff.returncode != 0 or untracked.returncode != 0:
        err = (diff.stderr or untracked.stderr or b"git failed").decode(
            "utf-8", errors="replace").strip()
        return None, err
    h = hashlib.sha256()
    h.update(diff.stdout)
    h.update(b"\0")
    for raw in untracked.stdout.split(b"\0"):
        if not raw:
            continue
        h.update(raw)
        h.update(b"\0")
        path = root / raw.decode("utf-8", errors="surrogateescape")
        try:
            st = path.stat()
            if st.st_size > MAX_PARSE_BYTES:
                h.update(f"big:{st.st_size}:{st.st_mtime_ns}".encode())
            else:
                data = path.read_bytes()
                h.update(f"{len(data)}:".encode())
                h.update(hashlib.sha256(data).hexdigest().encode())
        except OSError:
            h.update(b"unreadable")
        h.update(b"\0")
    return h.hexdigest(), None


# --------------------------------------------------------------------------- #
# query layer
# --------------------------------------------------------------------------- #
@dataclass
class DevMemory:
    dump: Path = DEFAULT_DUMP
    journal: Path = DEFAULT_JOURNAL
    # Process root the tools act on. None means the root recorded in the
    # snapshot. Set it when the server runs in a worktree other than the one
    # the snapshot was built from.
    root: Path | None = None

    def __post_init__(self) -> None:
        self.dump = Path(self.dump)
        self.journal = Path(self.journal)
        if self.root is not None:
            self.root = Path(self.root)
        if not self.dump.exists():
            raise FileNotFoundError(
                f"no dev-memory snapshot at {self.dump}; run "
                f"`python -m scripts.ocelot_dev_memory build` first")
        self.raw = json.loads(self.dump.read_text(encoding="utf-8"))
        self.nodes = {int(n["id"]): n for n in self.raw.get("nodes", [])}
        self.edges = self.raw.get("edges", [])
        self._out: dict[int, list[dict[str, Any]]] = {}
        self._in: dict[int, list[dict[str, Any]]] = {}
        for e in self.edges:
            s, t = int(e["src"]), int(e["tgt"])
            self._out.setdefault(s, []).append(e)
            self._in.setdefault(t, []).append(e)
        # Keyed by (rel, st_mtime_ns, st_size) so a file changed on disk is
        # read again.
        self._text_cache: dict[tuple[str, int, int], str] = {}
        self._staleness_memo: tuple[float, dict[str, Any]] | None = None
        self._gi = None
        # Token document frequency over labels, used only to weight a search
        # hit by how distinctive its matched words are. This is a mechanical
        # retrieval heuristic, not an agent decision.
        self._df: dict[str, int] = {}
        for nid in self.nodes:
            for t in set(_stem(x) for x in _word_tokens(self.label(nid))):
                self._df[t] = self._df.get(t, 0) + 1
        self._n_labels = max(1, len(self.nodes))
        # Exact normalized-name index for task anchors (seed/file/rule/doc/
        # test), so `context` does not scan every node for every phrasing.
        self._anchor_index: dict[str, list[tuple[int, int]]] = {}
        for typ, prio in (("Seed", 0), ("File", 1), ("Rule", 2),
                          ("Doc", 3), ("Test", 4)):
            for nid in self._nodes_of(typ):
                attrs = (self.node(nid) or {}).get("attrs", {})
                names = [attrs.get("id"), attrs.get("name"),
                         attrs.get("path"), attrs.get("title")]
                if typ == "File":
                    for name in list(names):
                        if isinstance(name, str):
                            names.append(str(Path(name).stem))
                for name in names:
                    if not isinstance(name, str) or not name:
                        continue
                    norm = "_".join(_word_tokens(name))
                    if len(norm) >= 4:
                        self._anchor_index.setdefault(norm, []).append((prio, nid))
        for k in self._anchor_index:
            self._anchor_index[k].sort()

    # -- graph helpers ------------------------------------------------------ #
    @property
    def gi(self):
        """The READ-ONLY GraphInterrogator over the same snapshot, created
        lazily so CLI commands that only need the raw dict stay light."""
        if self._gi is None:
            from scripts.graph_interrogate import GraphInterrogator
            self._gi = GraphInterrogator.from_dump(str(self.dump))
        return self._gi

    def node(self, nid: int) -> dict[str, Any] | None:
        return self.nodes.get(int(nid))

    def label(self, nid: int) -> str:
        n = self.node(nid) or {}
        attrs = n.get("attrs") or {}
        for k in ("name", "path", "title", "qualname", "id", "node", "message"):
            v = attrs.get(k)
            if isinstance(v, str) and v.strip():
                v = v.strip()
                return v if len(v) <= 100 else v[:97] + "..."
        return n.get("type", "?")

    def view(self, nid: int) -> dict[str, Any]:
        n = self.node(nid) or {}
        return {"id": int(nid), "type": n.get("type", "?"),
                "label": self.label(nid)}

    def related(self, nid: int, *, limit: int = 12) -> dict[str, list[dict[str, Any]]]:
        out: dict[str, list[dict[str, Any]]] = {}
        for e in self._out.get(int(nid), []):
            out.setdefault(e["type"], []).append(self.view(int(e["tgt"])))
        for e in self._in.get(int(nid), []):
            out.setdefault("<" + e["type"], []).append(self.view(int(e["src"])))
        for k in out:
            out[k] = out[k][:limit]
        return out

    def _nodes_of(self, type_name: str) -> list[int]:
        return [nid for nid, n in self.nodes.items() if n["type"] == type_name]

    def _neighbours(self, nid: int, edge_type: str, *,
                    incoming: bool = False) -> list[int]:
        if incoming:
            return [int(e["src"]) for e in self._in.get(int(nid), [])
                    if e["type"] == edge_type]
        return [int(e["tgt"]) for e in self._out.get(int(nid), [])
                if e["type"] == edge_type]

    # -- search ------------------------------------------------------------- #
    def _idf(self, token: str) -> float:
        df = self._df.get(_stem(token), 0)
        return math.log((self._n_labels + 1) / (df + 1)) + 1.0

    def search(self, text: str, *, types: list[str] | None = None,
               limit: int = 20) -> list[dict[str, Any]]:
        q = (text or "").strip().lower()
        if not q:
            return []
        toks = _tokens(q)
        wanted = set(types) if types else None
        scored: list[tuple[float, int]] = []
        for nid, n in self.nodes.items():
            if wanted is not None and n["type"] not in wanted:
                continue
            attrs = n.get("attrs") or {}
            label = self.label(nid).lower()
            label_toks = {_stem(x) for x in _word_tokens(label)}
            qstem = [_stem(t) for t in toks]
            matched = [t for t in qstem if t in label_toks]
            coverage = len(matched) / max(1, len(qstem))
            idf_sum = sum(self._idf(t) for t in matched)
            score = 0.0
            if label == q:
                score += 100
            elif q in label:
                score += 25
            score += 10.0 * idf_sum + 18.0 * coverage
            if not matched:
                hay = " ".join(
                    str(v).lower() for v in attrs.values()
                    if isinstance(v, (str, int, float, bool))
                )
                if q in hay:
                    score += 15
                else:
                    hmatched = [t for t in qstem if t in hay]
                    if hmatched:
                        hcov = len(hmatched) / max(1, len(qstem))
                        score += 4.0 * sum(self._idf(t) for t in hmatched) \
                                 + 8.0 * hcov
            if score <= 0:
                continue
            # Dev-memory intent: a task phrased around seeds/rules/tests/docs
            # should surface those node classes ahead of a generic helper whose
            # name happens to contain one of the words.
            priority = {"Seed": 6, "Rule": 5, "File": 4, "Test": 3, "Doc": 3,
                        "Symbol": 2, "Commit": 1, "Failure": 2}.get(
                            n["type"], 0)
            if "seed" in qstem and n["type"] == "Seed":
                priority += 10
            if "rule" in qstem and n["type"] == "Rule":
                priority += 8
            if "test" in qstem and n["type"] == "Test":
                priority += 4
            if "doc" in qstem and n["type"] == "Doc":
                priority += 4
            scored.append((score + priority, nid))
        scored.sort(key=lambda x: (-x[0], self.label(x[1]).lower()))
        return [self.view(nid) for _, nid in scored[:limit]]

    # -- snippets ----------------------------------------------------------- #
    def _read(self, rel: str) -> str:
        p = Path(self.raw_repo_root) / rel
        try:
            st = p.stat()
        except OSError:
            return ""
        key = (rel, st.st_mtime_ns, st.st_size)
        if key not in self._text_cache:
            # Drop older versions of this file before caching the new one.
            for old in [k for k in self._text_cache if k[0] == rel]:
                del self._text_cache[old]
            self._text_cache[key] = _read_text(p, limit=1_000_000) or ""
        return self._text_cache[key]

    def _drop_cached(self, rel: str) -> None:
        for k in [k for k in self._text_cache if k[0] == rel]:
            del self._text_cache[k]

    @property
    def raw_repo_root(self) -> str:
        if self.root is not None:
            return str(Path(self.root).resolve())
        for nid in self._nodes_of("Repo"):
            return str(self.nodes[nid]["attrs"].get("root") or ".")
        return "."

    def _file_for(self, nid: int) -> str | None:
        n = self.node(nid) or {}
        attrs = n.get("attrs") or {}
        if n.get("type") == "File":
            return attrs.get("path")
        if attrs.get("file"):
            return str(attrs["file"])
        for p in self._neighbours(nid, "defined_in"):
            if (self.node(p) or {}).get("type") == "File":
                return self.label(p)
        return None

    def snippet(self, nid: int, *, max_lines: int = 60) -> dict[str, Any]:
        n = self.node(nid) or {}
        attrs = n.get("attrs") or {}
        typ = n.get("type")
        rel = self._file_for(nid)
        if typ == "Seed":
            return self._seed_snippet(attrs, max_lines=max_lines)
        if typ == "Rule" or (attrs.get("seed") and typ not in ("Seed", "File")):
            return self._rule_snippet(attrs, max_lines=max_lines)
        if typ in ("Failure",):
            return {"path": attrs.get("file", ""), "lines": "",
                    "text": attrs.get("message", "")}
        if typ in ("Commit",):
            return {"path": "", "lines": "",
                    "text": f"{attrs.get('hash', '')} {attrs.get('date', '')}\n"
                            f"{attrs.get('subject', '')}"}
        if typ == "Doc":
            rel = attrs.get("path") or rel
        if not rel:
            return {"path": "", "lines": "", "text": ""}
        text = self._read(str(rel))
        lines = text.splitlines()
        if typ in ("Symbol", "Test"):
            start = max(1, int(attrs.get("start_line") or 1) - 2)
            end = min(len(lines), int(attrs.get("end_line") or start) + 1)
            end = min(end, start + max_lines - 1)
        else:
            # JSON/manifest and markdown lines can be very long; keep the
            # context pack small and let the agent read the file if it needs
            # the whole body.
            if str(rel).endswith(".json"):
                max_lines = min(max_lines, 12)
            elif str(rel).endswith((".md", ".rst", ".txt")):
                max_lines = min(max_lines, 25)
            start, end = 1, min(len(lines), max_lines)
        chunk = "\n".join(lines[start - 1:end])
        if len(chunk) > 4000:
            chunk = chunk[:4000] + "\n... (truncated; read the file for the rest)"
        return {"path": str(rel), "lines": f"{start}-{end}", "text": chunk}

    def _estimate_tokens(self, text: str) -> int:
        """A stable rough estimate for context budgeting (~4 chars/token).
        It is labelled as an estimate everywhere; no tokenizer dependency."""
        return max(1, len(text or "") // 4)

    def _symbol_signature(self, attrs: dict[str, Any],
                          *, indent: str = "") -> str:
        decs = [d for d in (attrs.get("decorators") or []) if isinstance(d, str)]
        lines = [f"{indent}@{d}" for d in decs[:3]]
        kind = str(attrs.get("kind") or "function")
        name = str(attrs.get("name") or "?")
        if kind == "class":
            bases = [b for b in (attrs.get("bases") or []) if isinstance(b, str)]
            head = f"{indent}class {name}"
            if bases:
                head += f"({', '.join(bases)})"
            head += ":"
        else:
            args = [a for a in (attrs.get("args") or []) if isinstance(a, str)]
            ret = str(attrs.get("returns") or "")
            prefix = "async def" if kind == "async_function" else "def"
            head = f"{indent}{prefix} {name}({', '.join(args)})"
            if ret:
                head += f" -> {ret}"
            head += ":"
        lines.append(head)
        doc = str(attrs.get("doc") or "")
        if doc:
            lines.append(f'{indent}    """{doc}"""')
        return "\n".join(lines)

    def _signature_head(self, attrs: dict[str, Any], *,
                        indent: str = "") -> str:
        lines = self._symbol_signature(attrs, indent=indent).splitlines()
        for line in lines:
            st = line.strip()
            if st.startswith(("def ", "async def ", "class ")):
                return line
        return lines[-1] if lines else f"{indent}def ?(...):"

    def _symbol_outline(self, nid: int) -> dict[str, Any]:
        attrs = (self.node(nid) or {}).get("attrs", {})
        text = self._symbol_signature(attrs)
        # A class outline lists its direct methods; a function outline stops at
        # the signature. This is the "signatures, not bodies" view.
        if attrs.get("kind") == "class":
            methods = []
            for child in self._neighbours(nid, "contains_symbol"):
                ca = (self.node(child) or {}).get("attrs", {})
                if ca.get("kind") not in ("function", "async_function"):
                    continue
                line = self._signature_head(ca, indent="    ")
                methods.append(f"{line}  # L{ca.get('start_line')}")
            if methods:
                text += "\n" + "\n".join(methods[:12])
        rel = self._file_for(nid) or ""
        return {"path": rel,
                "lines": f"{attrs.get('start_line')}-{attrs.get('end_line')}",
                "text": text, "kind": "symbol",
                "estimated_tokens": self._estimate_tokens(text)}

    def _file_outline(self, nid: int, *, max_lines: int = 40) -> dict[str, Any]:
        attrs = (self.node(nid) or {}).get("attrs", {})
        rel = str(attrs.get("path") or "")
        lines: list[str] = [f"# {rel} ({attrs.get('language', '?')})"]
        doc = str(attrs.get("doc") or "")
        if doc:
            lines.append(f"# {doc}")
        imports = self._neighbours(nid, "imports")
        if imports:
            names = [self.label(x) for x in imports[:10]]
            lines.append("imports: " + ", ".join(names))
        syms = [x for x in self._neighbours(nid, "defines")
                if (self.node(x) or {}).get("type") == "Symbol"]
        syms.sort(key=lambda x: int((self.node(x) or {}).get("attrs", {}).get("start_line") or 0))
        for x in syms[:24]:
            a = (self.node(x) or {}).get("attrs", {})
            lines.append(self._signature_head(a) +
                         f"  # L{a.get('start_line')}")
        tests = [x for x in self._neighbours(nid, "has_test")]
        if tests:
            names = [self.label(x) for x in tests[:16]]
            lines.append("tests: " + ", ".join(names))
        text = "\n".join(lines[:max_lines])
        return {"path": rel, "lines": "outline", "text": text,
                "kind": "file", "estimated_tokens": self._estimate_tokens(text)}

    def _doc_outline(self, nid: int) -> dict[str, Any]:
        attrs = (self.node(nid) or {}).get("attrs", {})
        rel = str(attrs.get("path") or "")
        text = self._read(rel)
        out: list[str] = []
        title = str(attrs.get("title") or "")
        if title:
            out.append(f"# {title}")
        headings = [ln for ln in text.splitlines() if ln.startswith("#")]
        out.extend(headings[:10])
        # First prose paragraph after the title.
        para: list[str] = []
        for ln in text.splitlines()[1:]:
            st = ln.strip()
            if not st or st.startswith("#"):
                if para:
                    break
                continue
            para.append(st)
            if len(para) >= 6:
                break
        if para:
            out.append("")
            out.extend(para)
        body = "\n".join(out)
        return {"path": rel, "lines": "outline", "text": body,
                "kind": "doc", "estimated_tokens": self._estimate_tokens(body)}

    def outline(self, nid: int) -> dict[str, Any]:
        """A compact structural view: signatures/docstrings/headings, no bodies.
        Use for context; edit the real file, never this view."""
        typ = (self.node(nid) or {}).get("type")
        if typ == "Symbol":
            return self._symbol_outline(nid)
        if typ == "File":
            return self._file_outline(nid)
        if typ == "Test":
            a = (self.node(nid) or {}).get("attrs", {})
            text = f"def {a.get('name')}(...)  # L{a.get('start_line')}"
            if a.get("doc"):
                text += f'\n    """{a.get("doc")}"""'
            return {"path": str(a.get("file") or ""), "lines": "outline",
                    "text": text, "kind": "test",
                    "estimated_tokens": self._estimate_tokens(text)}
        if typ == "Seed":
            return self._seed_snippet((self.node(nid) or {}).get("attrs", {}))
        if typ == "Doc":
            return self._doc_outline(nid)
        return self.snippet(nid)

    def outline_target(self, target: str) -> dict[str, Any]:
        """Resolve a file/symbol/seed/doc and return its outline."""
        t = (target or "").strip()
        if t.lower().endswith((".md", ".markdown", ".json")):
            root = Path(self.raw_repo_root).resolve()
            p = (root / t).resolve()
            try:
                p.relative_to(root)
            except ValueError:
                return {"ok": False, "error": "path escapes the repo root"}
            if p.is_file():
                text = _read_text(p, limit=1_000_000) or ""
                if t.lower().endswith(".json"):
                    from scripts.ocelot_json_edit import outline_json
                    out = outline_json(text)
                else:
                    from scripts.ocelot_markdown_edit import outline_markdown
                    out = outline_markdown(text)
                out["path"] = t
                return {"ok": True, "target": t, **out}
        fnode = self._file_node(t)
        if fnode is not None:
            return {"ok": True, "target": t, **self.outline(fnode)}
        for nid in self._symbol_nodes(t):
            return {"ok": True, "target": t, **self.outline(nid)}
        seed = self._seed_node(t)
        if seed is not None:
            return {"ok": True, "target": t, **self.outline(seed)}
        for nid in self._nodes_of("Doc"):
            if (self.node(nid) or {}).get("attrs", {}).get("path") == t:
                return {"ok": True, "target": t, **self.outline(nid)}
        return {"ok": False, "error": f"no file/symbol/seed/doc matching {t!r}"}

    def _seed_snippet(self, attrs: dict[str, Any], *,
                      max_lines: int = 60) -> dict[str, Any]:
        rel = str(attrs.get("path") or "")
        if not rel:
            return {"path": "", "lines": "", "text": ""}
        try:
            d = json.loads((Path(self.raw_repo_root) / rel).read_text(
                encoding="utf-8", errors="replace"))
        except (OSError, json.JSONDecodeError):
            return {"path": rel, "lines": "", "text": ""}
        lines = [
            f"seed {d.get('id')} v{d.get('version')}",
            f"depends_on: {', '.join(map(str, d.get('depends_on') or []))}",
            f"description: {str(d.get('description', ''))[:300]}",
        ]
        for key in ("nodes", "rules", "concepts", "productions", "reflexes",
                    "goals"):
            items = d.get(key) or []
            if not items:
                continue
            names = []
            for it in items:
                if isinstance(it, str):
                    names.append(it)
                elif isinstance(it, dict):
                    attrs = it.get("attrs") if isinstance(it.get("attrs"), dict) else {}
                    names.append(str(attrs.get("name") or it.get("name")
                                     or it.get("type") or "?"))
                elif isinstance(it, (list, tuple)):
                    names.append(str(it[1]) if len(it) > 1 else "?")
            lines.append(f"{key} ({len(items)}): {', '.join(names[:25])}")
        return {"path": rel, "lines": "", "text": "\n".join(lines[:max_lines])}

    def _rule_snippet(self, attrs: dict[str, Any], *,
                      max_lines: int = 80) -> dict[str, Any]:
        seed_id = str(attrs.get("seed") or "")
        name = str(attrs.get("name") or "")
        sid = self._seed_node(seed_id)
        if sid is None or not name:
            return {"path": "", "lines": "", "text": ""}
        rel = str((self.node(sid) or {}).get("attrs", {}).get("path") or "")
        try:
            d = json.loads((Path(self.raw_repo_root) / rel).read_text(
                encoding="utf-8", errors="replace"))
        except (OSError, json.JSONDecodeError):
            return {"path": rel, "lines": "", "text": ""}
        for key in ("rules", "nodes", "reflexes", "concepts", "productions"):
            for item in d.get(key) or []:
                if not isinstance(item, dict):
                    continue
                item_name = item.get("name")
                if item_name is None and isinstance(item.get("attrs"), dict):
                    item_name = item["attrs"].get("name")
                if item_name != name:
                    continue
                body = json.dumps(item, indent=1, sort_keys=True)
                return {"path": rel, "lines": "",
                        "text": "\n".join(body.splitlines()[:max_lines])}
        mt = d.get("microtheory")
        if isinstance(mt, dict) and mt.get("name") == name:
            body = json.dumps(mt, indent=1, sort_keys=True)
            return {"path": rel, "lines": "",
                    "text": "\n".join(body.splitlines()[:max_lines])}
        return {"path": rel, "lines": "", "text": ""}

    # -- resolvers ---------------------------------------------------------- #
    def _file_node(self, path: str) -> int | None:
        p = (path or "").strip().lstrip("./")
        if not p:
            return None
        exact = [nid for nid in self._nodes_of("File")
                 if (self.node(nid) or {}).get("attrs", {}).get("path") == p]
        if exact:
            return exact[0]
        suffix = [nid for nid in self._nodes_of("File")
                  if str((self.node(nid) or {}).get("attrs", {}).get("path", "")).endswith(p)]
        return suffix[0] if len(suffix) == 1 else None

    def _symbol_nodes(self, name: str) -> list[int]:
        q = (name or "").strip()
        exact = [nid for nid in self._nodes_of("Symbol")
                 if (self.node(nid) or {}).get("attrs", {}).get("qualname") == q]
        if exact:
            return exact
        exact_name = [nid for nid in self._nodes_of("Symbol")
                      if (self.node(nid) or {}).get("attrs", {}).get("name") == q]
        if exact_name:
            return exact_name
        return [nid for nid in self._nodes_of("Symbol")
                if q and q in str((self.node(nid) or {}).get("attrs", {}).get("qualname", ""))]

    def _seed_node(self, seed_id: str) -> int | None:
        for nid in self._nodes_of("Seed"):
            if (self.node(nid) or {}).get("attrs", {}).get("id") == seed_id:
                return nid
        return None

    # -- detail views ------------------------------------------------------- #
    def _edge_closure(self, nid: int, edge: str, *,
                      max_depth: int = 8) -> list[dict[str, Any]]:
        seen = {int(nid)}
        out: list[int] = []
        frontier = [(int(nid), 0)]
        while frontier:
            cur, depth = frontier.pop(0)
            if depth >= max_depth:
                continue
            for nxt in self._neighbours(cur, edge):
                if nxt in seen:
                    continue
                seen.add(nxt)
                out.append(nxt)
                frontier.append((nxt, depth + 1))
        return [self.view(x) for x in out]

    def file(self, path: str) -> dict[str, Any]:
        nid = self._file_node(path)
        if nid is None:
            return {"ok": False, "error": f"no File node for {path!r}"}
        return {"ok": True, "node": self.view(nid),
                "attrs": (self.node(nid) or {}).get("attrs", {}),
                "symbols": [self.view(x) for x in
                            self._neighbours(nid, "defines")
                            if (self.node(x) or {}).get("type") == "Symbol"],
                "tests": [self.view(x) for x in
                          self._incoming_unique(nid, ("tests_module", "mentions_file"))],
                "imports": [self.view(x) for x in self._neighbours(nid, "imports")],
                "imported_by": [self.view(x) for x in
                                self._neighbours(nid, "imports", incoming=True)],
                "docs": [self.view(x) for x in
                         self._neighbours(nid, "documents", incoming=True)],
                "failures": [self.view(x) for x in self._neighbours(nid, "has_failure")],
                "commits": [self.view(x) for x in
                            self._neighbours(nid, "changes", incoming=True)][:10],
                "related": self.related(nid)}

    def _incoming_unique(self, nid: int, edge_types: tuple[str, ...]) -> list[int]:
        seen: list[int] = []
        for et in edge_types:
            for x in self._neighbours(nid, et, incoming=True):
                if x not in seen:
                    seen.append(x)
        return seen

    def symbol(self, name: str) -> dict[str, Any]:
        nids = self._symbol_nodes(name)
        if not nids:
            return {"ok": False, "error": f"no Symbol node matching {name!r}"}
        out = []
        for nid in nids[:8]:
            attrs = (self.node(nid) or {}).get("attrs", {})
            rel = self._file_for(nid)
            tests = []
            if rel:
                rel_nid = self._file_node(rel)
                if rel_nid is not None:
                    cand = self._incoming_unique(rel_nid, ("tests_module", "mentions_file"))
                    sym_name = str(attrs.get("name", ""))
                    # Prefer tests whose source actually mentions this symbol;
                    # fall back to the module's test set when none do.
                    narrowed = []
                    if len(sym_name) >= 3:
                        for x in cand:
                            tf = str((self.node(x) or {}).get("attrs", {}).get("file", ""))
                            if tf and sym_name in self._read(tf):
                                narrowed.append(x)
                    tests = [self.view(x) for x in (narrowed or cand)]
            out.append({
                "node": self.view(nid),
                "attrs": attrs,
                "file": rel,
                "snippet": self.snippet(nid),
                "tests": tests,
                "related": self.related(nid),
            })
        return {"ok": True, "matches": out}

    def seed(self, seed_id: str) -> dict[str, Any]:
        nid = self._seed_node(seed_id)
        if nid is None:
            return {"ok": False, "error": f"no Seed node for {seed_id!r}"}
        items = [self.view(x) for x in self._neighbours(nid, "contains")]
        return {"ok": True, "node": self.view(nid),
                "attrs": (self.node(nid) or {}).get("attrs", {}),
                "depends_on": [self.view(x) for x in self._neighbours(nid, "depends_on")],
                "depends_on_closure": self._edge_closure(nid, "depends_on"),
                "dependents": [self.view(x) for x in
                               self._neighbours(nid, "depends_on", incoming=True)],
                "items": items,
                "tests": [self.view(x) for x in
                          self._neighbours(nid, "mentions_seed", incoming=True)
                          if (self.node(x) or {}).get("type") == "Test"],
                "files": [self.view(x) for x in
                          self._neighbours(nid, "mentions_seed", incoming=True)
                          if (self.node(x) or {}).get("type") == "File"
                          and not str((self.node(x) or {}).get("attrs", {}).get("path", ""))
                          .startswith("tests/")],
                "docs": [self.view(x) for x in
                         self._neighbours(nid, "documents", incoming=True)],
                "snippet": self._seed_snippet((self.node(nid) or {}).get("attrs", {}))}

    def rule(self, name: str) -> dict[str, Any]:
        nids = [nid for nid in self._nodes_of("Rule")
                if (self.node(nid) or {}).get("attrs", {}).get("name") == name]
        if not nids:
            nids = [nid for nid in self._nodes_of("Rule")
                    if name in str((self.node(nid) or {}).get("attrs", {}).get("name", ""))]
        if not nids:
            return {"ok": False, "error": f"no Rule node matching {name!r}"}
        out = []
        for nid in nids[:10]:
            attrs = (self.node(nid) or {}).get("attrs", {})
            out.append({"node": self.view(nid), "attrs": attrs,
                        "seed": self.seed(str(attrs.get("seed", "")))
                        if attrs.get("seed") else None,
                        "snippet": self._rule_snippet(attrs)})
        return {"ok": True, "matches": out}

    def tests_for(self, target: str) -> dict[str, Any]:
        t = (target or "").strip()
        fnode = self._file_node(t)
        snodes = self._symbol_nodes(t) if fnode is None else []
        seed = self._seed_node(t) if (fnode is None and not snodes) else None
        if fnode is None and not snodes and seed is None:
            return {"ok": False, "error": f"no file/symbol/seed matching {t!r}"}
        found: dict[int, str] = {}
        if fnode is not None:
            for x in self._incoming_unique(fnode, ("tests_module", "mentions_file")):
                found[x] = "module or path mention"
            for x in self._neighbours(fnode, "has_test"):
                found[x] = "test lives in this file"
        if seed is not None:
            for x in self._neighbours(seed, "mentions_seed", incoming=True):
                found[x] = "test mentions this seed"
        for s in snodes:
            rel = self._file_for(s)
            if rel:
                rel_nid = self._file_node(rel)
                if rel_nid is not None:
                    for x in self._incoming_unique(rel_nid,
                                                   ("tests_module", "mentions_file")):
                        found.setdefault(x, "test imports the symbol's module")
                # Direct name mention in a test file is a cheap, mechanical
                # link; do it only for tests already touching the module or
                # the repo's test files when the symbol is distinctive.
                sym_name = str((self.node(s) or {}).get("attrs", {}).get("name", ""))
                if len(sym_name) >= 4:
                    for x in self._nodes_of("Test"):
                        test_file = str((self.node(x) or {}).get("attrs", {}).get("file", ""))
                        if not test_file:
                            continue
                        if sym_name in self._read(test_file):
                            found.setdefault(x, f"test source mentions {sym_name!r}")
        out = []
        for tid, why in found.items():
            attrs = (self.node(tid) or {}).get("attrs", {})
            out.append({"test": self.view(tid), "why": why,
                        "file": attrs.get("file"),
                        "line": attrs.get("start_line"),
                        "failures": [self.view(f) for f in
                                     self._neighbours(tid, "refers_to", incoming=True)]})
        return {"ok": True, "target": t, "tests": out}

    def _anchor_nodes(self, task: str) -> list[int]:
        """Exact-ish anchors named in a task, before fuzzy search.

        A task like "add a rule to gap awareness" names the seed
        `gap_awareness`; finding it by name is more useful than ranking every
        helper whose identifier contains "awareness". This is a mechanical
        phrase-to-identifier normalisation, not a semantic decision.
        """
        words = _word_tokens(task)
        phrases: list[str] = []
        # Multi-word phrases are the useful anchors ("gap awareness" ->
        # gap_awareness). A single word is allowed only when it is long and
        # not a generic task verb.
        for n in range(2, min(5, len(words)) + 1):
            for i in range(0, len(words) - n + 1):
                phrase = "_".join(words[i:i + n])
                if len(phrase) >= 4:
                    phrases.append(phrase)
        for w in words:
            if w in _GENERIC_QUERY_TOKENS:
                continue
            if len(w) >= 6 or w in self._anchor_index:
                phrases.append(w)
        # Prefer longer phrases; a full identifier beats its parts.
        phrases = list(dict.fromkeys(sorted(phrases, key=len, reverse=True)))
        found: list[int] = []
        # Symbols are deliberately not anchors: "seed rule" should anchor the
        # seed, not every helper named *_seed_rule*. Use dev_symbol/search for
        # an explicitly named function.
        for phrase in phrases:
            for _prio, nid in self._anchor_index.get(phrase, []):
                if nid not in found:
                    found.append(nid)
            if len(found) >= 6:
                break
        return found

    def _compact_attrs(self, nid: int) -> dict[str, Any]:
        """A token-frugal attr projection for context packs (detail commands
        still return the full attrs)."""
        n = self.node(nid) or {}
        a = n.get("attrs") or {}
        typ = n.get("type")
        keys = {
            "Symbol": ("name", "qualname", "kind", "file", "start_line",
                       "end_line", "doc"),
            "Test": ("name", "qualname", "file", "start_line", "end_line"),
            "File": ("path", "language", "size", "doc"),
            "Seed": ("id", "version", "path", "description"),
            "Rule": ("name", "seed", "container"),
            "Doc": ("path", "title", "kind"),
            "Failure": ("node", "file", "kind", "class", "message"),
            "Commit": ("hash", "date", "subject"),
        }.get(typ, ("name", "id", "seed", "kind"))
        out: dict[str, Any] = {}
        for k in keys:
            if k not in a:
                continue
            v = a[k]
            if isinstance(v, str) and len(v) > (300 if k in ("description", "doc", "message") else 160):
                v = v[:300 if k in ("description", "doc", "message") else 160] + "..."
            if isinstance(v, (str, int, float, bool)) or v is None:
                out[k] = v
        return out

    def context(self, task: str, *, max_items: int = 8,
                max_chars: int = 24000, mode: str = "auto",
                budget_tokens: int = 6000) -> dict[str, Any]:
        anchors = self._anchor_nodes(task)
        hits = [{"id": nid, "type": (self.node(nid) or {}).get("type", "?"),
                 "label": self.label(nid), "why": "named in task"}
                for nid in anchors]
        # If a seed itself is anchored, its manifest File is the same content;
        # keep the Seed summary and drop the raw-JSON duplicate.
        seed_paths = {
            (self.node(nid) or {}).get("attrs", {}).get("path")
            for nid in anchors
            if (self.node(nid) or {}).get("type") == "Seed"
        }
        hits = [h for h in hits
                if not (h["type"] == "File"
                        and (self.node(h["id"]) or {}).get("attrs", {}).get("path")
                        in seed_paths)]
        # A named seed's own contents are the most useful "existing pattern"
        # context for a seed/rule task: show the rules and concepts already in
        # that manifest before generic name matches elsewhere.
        expanded: list[dict[str, Any]] = []
        for nid in anchors:
            if (self.node(nid) or {}).get("type") != "Seed":
                continue
            for child in self._neighbours(nid, "contains"):
                ctype = (self.node(child) or {}).get("type", "?")
                if ctype not in ("Rule", "Concept", "Reflex", "Microtheory",
                                 "ShapeSignature", "Dimensions", "Frame"):
                    continue
                expanded.append({"id": child, "type": ctype,
                                 "label": self.label(child),
                                 "why": f"contained in seed {self.label(nid)}"})
        # A named file's own public definitions and tests are the next most
        # useful reads: "fix code_writing_cortex" should surface the class,
        # not a random helper elsewhere whose name shares a word.
        want = set(_tokens(task))
        for nid in anchors:
            if (self.node(nid) or {}).get("type") != "File":
                continue
            syms = []
            for child in self._neighbours(nid, "defines"):
                if (self.node(child) or {}).get("type") != "Symbol":
                    continue
                attrs = (self.node(child) or {}).get("attrs", {})
                name = str(attrs.get("name", ""))
                label_toks = {_stem(x) for x in _word_tokens(name)}
                hits_count = len(label_toks & want)
                kind = str(attrs.get("kind", ""))
                if kind != "class" and not hits_count and name.startswith("_"):
                    continue
                syms.append((0 if hits_count else 1,
                             0 if kind == "class" else 1,
                             -len(label_toks & want), name.lower(), child))
            syms.sort()
            for *_, child in syms[:3]:
                expanded.append({"id": child, "type": "Symbol",
                                 "label": self.label(child),
                                 "why": f"defined in {self.label(nid)}"})
            tests = self._incoming_unique(nid, ("tests_module", "mentions_file"))
            for child in tests[:2]:
                if (self.node(child) or {}).get("type") == "Test":
                    expanded.append({"id": child, "type": "Test",
                                     "label": self.label(child),
                                     "why": f"tests {self.label(nid)}"})
        # If the task says "rule", show the seed's rules first; if it says
        # "concept", show concepts first. This is task-word order, not a
        # judgement about what the agent should change.
        order = {"Rule": 0 if "rule" in want else 2,
                 "Concept": 0 if "concept" in want else 1,
                 "Symbol": 2, "Test": 3, "Reflex": 3, "Microtheory": 4,
                 "ShapeSignature": 5, "Dimensions": 5, "Frame": 5}
        # Stable sort by type only: within a type, keep the seed's own item
        # order and the per-file class-first symbol order.
        expanded.sort(key=lambda h: order.get(h["type"], 9))
        hits.extend(expanded)
        seen_ids = {x["id"] for x in hits}
        for h in self.search(task, limit=max_items * 5):
            if h["id"] not in seen_ids:
                hits.append(h)
                seen_ids.add(h["id"])
        picked: list[dict[str, Any]] = []
        total_tokens = 0
        per_type: dict[str, int] = {}
        type_caps = {"Seed": 2, "File": 3, "Rule": 3, "Doc": 2, "Test": 1,
                     "Symbol": 2, "Concept": 2}
        for h in hits:
            if len(picked) >= max_items:
                break
            typ = h["type"]
            if per_type.get(typ, 0) >= type_caps.get(typ, 1):
                continue
            per_type[typ] = per_type.get(typ, 0) + 1
            nid = int(h["id"])
            # `auto` gives the first two anchors the full body and compresses
            # the rest to signatures/headings; `outline` compresses everything.
            # A minified view is for READING — the file on disk stays the
            # source of truth (we never write this text back).
            use_outline = (mode == "outline"
                           or (mode == "auto" and len(picked) >= 2))
            snap = self.outline(nid) if use_outline else self.snippet(nid)
            text = snap.get("text", "")
            item_cap = min(max_chars, 6000)
            if len(text) > item_cap:
                text = text[:item_cap] + "\n... (truncated)"
                snap["text"] = text
            est = int(snap.get("estimated_tokens")
                      or self._estimate_tokens(text))
            if picked and total_tokens + est > budget_tokens:
                break
            snap["estimated_tokens"] = est
            picked.append({
                "node": h,
                "why": h.get("why", f"{h['type']} label matched the task"),
                "attrs": self._compact_attrs(nid),
                "snippet": snap,
                "related": self.related(nid, limit=4),
            })
            total_tokens += est
            max_chars -= len(text)
            if max_chars <= 0:
                break
        repo = {}
        for nid in self._nodes_of("Repo"):
            repo = self.view(nid) | {"attrs": (self.node(nid) or {}).get("attrs", {})}
        changed = self.changed(limit=20)
        return {"task": task, "repo": repo, "items": picked,
                "changed": (changed.get("files") if changed.get("ok") else []),
                "budget": {"mode": mode, "budget_tokens": int(budget_tokens),
                           "estimated_tokens": total_tokens,
                           "items": len(picked)},
                "journal": self.journal_recent(5),
                "snapshot": self.staleness()}

    def _build_commands(self) -> list[str]:
        """Mechanical extraction of build/test commands from the root docs."""
        seen: list[str] = []
        keys = ("pytest", "maturin", "cargo test", "engine_build.sh",
                "cargo build", "python -m pytest")
        for rel in ("README.md", "CLAUDE.md", "docs/CODE_MAP.md"):
            p = Path(self.raw_repo_root) / rel
            text = _read_text(p, limit=500_000) or ""
            in_fence = False
            for line in text.splitlines():
                raw = line.strip()
                if raw.startswith("```"):
                    in_fence = not in_fence
                    continue
                if not (in_fence or raw.startswith("$ ")):
                    continue
                st = raw.lstrip("$ ").strip()
                if not st or len(st) > 160:
                    continue
                low = st.lower()
                if not any(k in low for k in keys):
                    continue
                if st.startswith(("#", "-", "*")):
                    continue
                if st not in seen:
                    seen.append(st)
                if len(seen) >= 10:
                    return seen
        return seen

    def brief(self, task: str | None = None, *, budget_tokens: int = 4000,
              write: bool = False) -> dict[str, Any]:
        """A compact, pre-loaded repo brief: layout, commands, key docs,
        recent history, working tree, known failures, and an optional task
        context pack. Deterministic and citation-backed."""
        repo = {}
        for nid in self._nodes_of("Repo"):
            repo = (self.node(nid) or {}).get("attrs", {})
        dirs: dict[str, int] = {}
        langs: dict[str, int] = {}
        for nid in self._nodes_of("File"):
            path = str((self.node(nid) or {}).get("attrs", {}).get("path", ""))
            if not path:
                continue
            head = path.split("/", 1)[0]
            if head and not head.startswith("."):
                dirs[head] = dirs.get(head, 0) + 1
            lang = str((self.node(nid) or {}).get("attrs", {}).get("language", ""))
            if lang:
                langs[lang] = langs.get(lang, 0) + 1
        top_dirs = sorted(dirs.items(), key=lambda kv: (-kv[1], kv[0]))[:12]
        top_langs = sorted(langs.items(), key=lambda kv: (-kv[1], kv[0]))[:8]

        key_paths = ("README.md", "CLAUDE.md", "docs/CODE_MAP.md",
                     "docs/SEED_DEVELOPMENT.md", "docs/SCIENCE_RESEARCH.md",
                     "VISION_PROTOCOL.md")
        key_docs = []
        for nid in self._nodes_of("Doc"):
            a = (self.node(nid) or {}).get("attrs", {})
            if a.get("path") in key_paths:
                key_docs.append({"path": a.get("path"),
                                 "title": a.get("title", "")})
        key_docs.sort(key=lambda d: key_paths.index(d["path"]))
        feature_docs = []
        for nid in self._nodes_of("Doc"):
            a = (self.node(nid) or {}).get("attrs", {})
            if str(a.get("path", "")).startswith("docs/features/"):
                feature_docs.append({"path": a.get("path"),
                                     "title": a.get("title", "")})
        feature_docs.sort(key=lambda d: d["path"])
        key_docs.extend(feature_docs[:12])

        commits = []
        for nid in self._nodes_of("Commit"):
            a = (self.node(nid) or {}).get("attrs", {})
            commits.append({"hash": a.get("hash", "")[:12],
                            "date": a.get("date", ""),
                            "subject": a.get("subject", "")})
        commits.sort(key=lambda c: (c["date"], c["hash"]), reverse=True)

        failures: dict[str, int] = {}
        for nid in self._nodes_of("Failure"):
            f = str((self.node(nid) or {}).get("attrs", {}).get("file", ""))
            if f:
                failures[f] = failures.get(f, 0) + 1
        top_failures = sorted(failures.items(), key=lambda kv: (-kv[1], kv[0]))[:8]

        changed = self.changed(limit=25)
        changed_files = changed.get("files", []) if changed.get("ok") else []
        commands = self._build_commands()

        lines = ["# Ocelot repo brief", ""]
        lines.append(f"repo: {repo.get('name', '?')}  head: {repo.get('head', '?')[:12]}  "
                     f"snapshot: {repo.get('generated_at', '?')}")
        snapshot = self.staleness()
        if snapshot["stale"]:
            lines.append(
                f"WARNING: snapshot is stale (snapshot "
                f"{(snapshot['snapshot_head'] or '?')[:12]} vs HEAD "
                f"{(snapshot['head'] or '?')[:12]}); rebuild with "
                f"`python -m scripts.ocelot_dev_memory build`")
        lines.append(f"files: {repo.get('files', '?')}  symbols: {repo.get('symbols', '?')}  "
                     f"tests: {repo.get('tests', '?')}  seeds: {repo.get('seeds', '?')}")
        lines.append("")
        lines.append("## Layout")
        for name, n in top_dirs:
            lines.append(f"- {name}/ ({n} files)")
        if top_langs:
            lines.append("languages: " + ", ".join(f"{k} {v}" for k, v in top_langs))
        lines.append("")
        lines.append("## Build / test commands (extracted from root docs)")
        for c in commands:
            lines.append(f"- `{c}`")
        lines.append("")
        lines.append("## Key docs")
        for d in key_docs:
            lines.append(f"- {d['path']}" + (f" — {d['title']}" if d.get("title") else ""))
        lines.append("")
        lines.append("## Recent commits")
        for c in commits[:10]:
            lines.append(f"- {c['hash']} {c['date']} {c['subject']}")
        lines.append("")
        lines.append("## Working tree")
        if changed_files:
            for c in changed_files[:20]:
                lines.append(f"- {c.get('status', '?')} {c.get('path', '?')}")
        else:
            lines.append("- clean (or not a git checkout)")
        lines.append("")
        lines.append("## Known failures (failure_baseline.json)")
        if top_failures:
            for f, n in top_failures:
                lines.append(f"- {f}: {n}")
        else:
            lines.append("- none loaded")
        if task:
            ctx = self.context(task, mode="auto", max_items=6,
                               budget_tokens=budget_tokens)
            lines.append("")
            lines.append(f"## Task context: {task}")
            for item in ctx.get("items", []):
                snap = item.get("snippet", {})
                lines.append("")
                lines.append(f"### {item['node']['type']} {item['node']['label']}")
                lines.append(f"why: {item.get('why')}")
                if snap.get("path"):
                    lines.append(f"path: {snap['path']}"
                                 + (f" ({snap['lines']})" if snap.get("lines") else ""))
                if snap.get("text"):
                    lines.append("```")
                    lines.append(snap["text"])
                    lines.append("```")
            lines.append("")
            lines.append("budget: " + json.dumps(ctx.get("budget", {})))
        text = "\n".join(lines).strip() + "\n"
        out_path = None
        if write:
            out_path = str(Path(self.dump).parent / "ocelot_dev_brief.md")
            Path(out_path).write_text(text, encoding="utf-8")
        return {"ok": True, "markdown": text, "path": out_path,
                "repo": repo,
                "commands": commands,
                "key_docs": key_docs,
                "changed": changed_files,
                "snapshot": snapshot,
                "estimated_tokens": self._estimate_tokens(text)}

    def stats(self) -> dict[str, Any]:
        types = _histogram(n["type"] for n in self.nodes.values())
        edges = _histogram(e["type"] for e in self.edges)
        repo = {}
        for nid in self._nodes_of("Repo"):
            repo = (self.node(nid) or {}).get("attrs", {})
        return {"ok": True, "types": types, "edge_types": edges,
                "repo": repo, "nodes": len(self.nodes),
                "edges": len(self.edges), "dump": str(self.dump)}

    def changed(self, *, include_all: bool = False,
                limit: int = 200) -> dict[str, Any]:
        """Working-tree changes from `git status --porcelain` (mechanical).

        By default only development-relevant paths are returned: generated
        results, evaluation runs, corpora and scratch trees are noise for a
        coding task. Pass `include_all` for the raw `git status` set."""
        root = self.raw_repo_root
        try:
            proc = subprocess.run(
                ["git", "-C", root, "status", "--porcelain", "-uall"],
                capture_output=True, text=True, timeout=30, check=False)
        except (OSError, subprocess.SubprocessError) as e:
            return {"ok": False, "error": str(e),
                    "snapshot": self.staleness()}
        if proc.returncode != 0:
            return {"ok": False,
                    "error": (proc.stderr or "git status failed").strip(),
                    "snapshot": self.staleness()}
        files = []
        for line in (proc.stdout or "").splitlines():
            if len(line) < 4:
                continue
            status = line[:2].strip() or "?"
            path = line[3:].strip()
            if " -> " in path:
                path = path.split(" -> ", 1)[1]
            if not include_all and any(
                    path.startswith(prefix) for prefix in (
                        "results/", "evaluation/", "runs/", "var/",
                        "recordings/", "data/", "domain_data/",
                        "semantic-review/", "drafts/", "papers/",
                        "benchmarks/", "seeds/acquired/", "seeds/generated/",
                        "__pycache__/", ".pytest_cache/")):
                continue
            nid = self._file_node(path)
            rec: dict[str, Any] = {"status": status, "path": path,
                                   "in_graph": nid is not None}
            if nid is not None:
                rec["node"] = self.view(nid)
            files.append(rec)
            if len(files) >= int(limit):
                break
        return {"ok": True, "files": files, "n": len(files),
                "include_all": include_all, "limit": int(limit),
                "snapshot": self.staleness()}

    _STALENESS_TTL_S = 5.0

    def staleness(self) -> dict[str, Any]:
        """Whether the snapshot still describes this checkout.

        Compares the snapshot's recorded root and HEAD with the process root
        and `git rev-parse HEAD` now. One git call; memoised for a few seconds.
        """
        now = time.monotonic()
        memo = self._staleness_memo
        if memo is not None and now - memo[0] < self._STALENESS_TTL_S:
            return dict(memo[1])
        repo: dict[str, Any] = {}
        for nid in self._nodes_of("Repo"):
            repo = (self.node(nid) or {}).get("attrs", {})
        snapshot_root = repo.get("root")
        root = self.raw_repo_root
        root_mismatch = bool(snapshot_root) and (
            Path(str(snapshot_root)).resolve() != Path(root).resolve())
        head: str | None = None
        try:
            proc = subprocess.run(
                ["git", "-C", root, "rev-parse", "HEAD"],
                capture_output=True, text=True, timeout=10, check=False)
            if proc.returncode == 0 and proc.stdout.strip():
                head = proc.stdout.strip()
        except (OSError, subprocess.SubprocessError):
            head = None
        snapshot_head = repo.get("head") or None
        # A checkout with a known HEAD and a snapshot without one cannot be
        # verified, so it counts as stale (`snapshot_head != head`).
        # The working tree is compared by digest (see `_tree_digest`). Older
        # snapshots without a digest are not judged on it.
        snapshot_tree = repo.get("tree_digest") or None
        tree_now, _tree_err = _tree_digest(Path(root))
        tree_changed = bool(snapshot_tree and tree_now
                            and snapshot_tree != tree_now)
        stale = bool(root_mismatch or (head and snapshot_head != head)
                     or tree_changed)
        result: dict[str, Any] = {
            "snapshot_root": snapshot_root,
            "root": root,
            "root_mismatch": root_mismatch,
            "snapshot_head": snapshot_head,
            "head": head,
            "tree_changed": tree_changed,
            "stale": stale,
            "generated_at": repo.get("generated_at"),
        }
        self._staleness_memo = (now, result)
        return dict(result)

    def _tag_cache(self) -> Path:
        """The tag cache under the process root. Index tools pass this so a
        worktree does not write into the script checkout's `var/`."""
        return Path(self.raw_repo_root).resolve() / "var" / "ocelot_dev_tags.json"

    def repo_map(self, task: str = "", *, budget_tokens: int = 1500,
                 focus_files: Iterable[str] | None = None,
                 force_refresh: bool = False,
                 scip_path: str | None = None) -> dict[str, Any]:
        """Ranked, token-budgeted repo map (tree-sitter tags + PageRank).

        Task-named seeds/files/symbols from the dev graph become focus files,
        so a seed task surfaces the source files that mention it rather than
        only same-named symbols.
        """
        from scripts.ocelot_repo_map import repo_map as _repo_map
        focus = list(focus_files or [])
        if not focus:
            for nid in self._anchor_nodes(task):
                n = self.node(nid) or {}
                a = n.get("attrs") or {}
                typ = n.get("type")
                if typ == "File" and a.get("path"):
                    focus.append(str(a["path"]))
                elif typ == "Symbol" and a.get("file"):
                    focus.append(str(a["file"]))
                elif typ == "Seed":
                    # A seed manifest is not source. The useful focus files are
                    # the source/tests that mention (load or exercise) it.
                    for f in self._neighbours(nid, "mentions_seed",
                                              incoming=True):
                        if (self.node(f) or {}).get("type") == "File":
                            path = str((self.node(f) or {}).get("attrs", {}).get("path", ""))
                            if path:
                                focus.append(path)
                elif typ in ("Rule", "Concept", "Reflex"):
                    for sid in self._neighbours(nid, "in_seed"):
                        for f in self._neighbours(sid, "mentions_seed",
                                                  incoming=True):
                            if (self.node(f) or {}).get("type") == "File":
                                path = str((self.node(f) or {}).get("attrs", {}).get("path", ""))
                                if path:
                                    focus.append(path)
        return _repo_map(self.raw_repo_root, task=task,
                         budget_tokens=budget_tokens,
                         focus_files=focus,
                         force_refresh=force_refresh,
                         cache_path=self._tag_cache(),
                         scip_path=self._scip_arg(scip_path))

    def _scip_arg(self, scip_path: str | None) -> str | None:
        """Resolve a SCIP export relative to the repo root and require it to
        stay inside that root."""
        if not scip_path:
            return None
        root = Path(self.raw_repo_root).resolve()
        p = Path(scip_path)
        if not p.is_absolute():
            p = root / p
        p = p.resolve()
        if not p.is_relative_to(root):
            raise ValueError("scip_path escapes the repo root")
        if not p.is_file():
            raise ValueError(f"no such SCIP index: {scip_path}")
        return str(p)

    def impact(self, file: str, *, depth: int = 2,
               scip_path: str | None = None) -> dict[str, Any]:
        from scripts.ocelot_repo_map import impact as _impact
        return _impact(self.raw_repo_root, file=file, depth=depth,
                       cache_path=self._tag_cache(),
                       scip_path=self._scip_arg(scip_path))

    # -- symbol graph (syntactic; optional LSP refinement) ----------------- #
    def symbol_graph(self, op: str, symbol: str, *, depth: int | None = None,
                     min_confidence: float = 0.0,
                     precise: bool = False) -> dict[str, Any]:
        """Symbol callers, callees, impact or resolve over the tag cache.

        Rows come from `scripts.ocelot_symbol_graph` and are syntactic (see
        docs/features/SYMBOL_GRAPH.md). With `precise=True` and op `callers`
        or `impact`, the target's LSP references refine the depth-1 rows and
        list references the syntactic graph missed. Lines in the result are
        1-based.
        """
        from scripts.ocelot_repo_map import update_tag_cache
        from scripts.ocelot_symbol_graph import (
            DEFAULT_DEPTH, OPS, build_symbol_graph, callers, callees,
            resolve_symbol, symbol_impact)
        if op not in OPS:
            return {"ok": False, "error": f"unknown op: {op}"}
        root = Path(self.raw_repo_root).resolve()
        cache_file = root / "var" / "ocelot_dev_tags.json"
        # The same steps as `symbol_query`, kept in one process so the target
        # definition is available for the LSP position without a second load
        # of the tag cache.
        t0 = time.perf_counter()
        cache, tag_stats = update_tag_cache(root, cache_path=cache_file)
        t1 = time.perf_counter()
        graph = build_symbol_graph(cache)
        t2 = time.perf_counter()
        hops = DEFAULT_DEPTH.get(op) if depth is None else depth
        if op == "resolve":
            matches = resolve_symbol(graph, symbol)
            result: dict[str, Any] = (
                {"ok": True, "op": "resolve", "symbol": symbol,
                 "matches": matches} if matches
                else {"ok": False, "error": f"unknown symbol: {symbol}"})
        elif op == "callers":
            result = callers(graph, symbol, hops, min_confidence)
        elif op == "callees":
            result = callees(graph, symbol, hops, min_confidence)
        else:
            result = symbol_impact(graph, symbol, hops, min_confidence)
        t3 = time.perf_counter()
        result.update({
            "root": str(root),
            "cache": str(cache_file),
            "stats": graph["stats"],
            "tag_cache": {key: tag_stats[key] for key in
                          ("files", "parsed", "reused", "failed", "errors",
                           "cached_files")},
            "timings": {"update_seconds": round(t1 - t0, 4),
                        "build_seconds": round(t2 - t1, 4),
                        "query_seconds": round(t3 - t2, 4)},
        })
        if precise:
            if op not in ("callers", "impact"):
                result["precision"] = {
                    "lsp": f"not applicable: precise applies to callers and impact, not {op}"}
            elif not result.get("ok"):
                result["precision"] = {
                    "lsp": "not run: symbol did not resolve to one definition"}
            else:
                self._refine_with_lsp(result, graph, root)
        return result

    def _refine_with_lsp(self, result: dict[str, Any], graph: dict[str, Any],
                         root: Path) -> None:
        """Mark depth-1 rows with LSP-confirmed references (in place)."""
        from scripts.ocelot_lsp import detect_language, server_candidates
        target = graph["nodes"][result["symbol"]]
        rel = target["file"]
        lang = detect_language(rel)
        if lang is None:
            result["precision"] = {
                "lsp": f"unavailable: no LSP language for {rel!r}"}
            return
        candidates = server_candidates(lang, root)
        ready = [c for c in candidates if c["available"]]
        if not ready:
            tried = ", ".join(c["name"] for c in candidates) or "none registered"
            result["precision"] = {
                "lsp": f"unavailable: no {lang} language server found "
                       f"(tried: {tried})"}
            return
        server = ready[0]["name"]
        lines = self._read(rel).split("\n")
        def_line = lines[target["line"] - 1] if 0 < target["line"] <= len(lines) else ""
        character = _name_utf16_col(def_line, target["name"])
        if character is None:
            result["precision"] = {
                "lsp": "error: definition name not found on its line"}
            return
        refs = self.lsp_references(rel, target["line"] - 1, character,
                                   timeout=PRECISE_TIMEOUT)
        if not refs.get("ok"):
            result["precision"] = {
                "lsp": f"error: {refs.get('error') or 'references failed'}"}
            return
        # (path, 1-based line) for each LSP reference.
        locations = [(str(loc.get("path") or ""), int(loc.get("line") or 0) + 1)
                     for loc in refs.get("locations") or []]
        by_file: dict[str, list[tuple[str, dict[str, Any]]]] = {}
        for nid, node in graph["nodes"].items():
            by_file.setdefault(node["file"], []).append((nid, node))

        def innermost(path: str, line1: int) -> tuple[str, str]:
            spans = [(nid, node) for nid, node in by_file.get(path, [])
                     if node["line"] <= line1 <= node["end_line"]]
            if not spans:
                return f"{path}::<module>", "<module>"
            nid, node = max(spans, key=lambda s: (
                s[1]["line"], -(s[1]["end_line"] - s[1]["line"])))
            return nid, node["qualname"]

        depth1 = [row for row in result["results"] if row["depth"] == 1]
        covered: set[tuple[str, int]] = set()
        for row in result["results"]:
            if row["depth"] != 1:
                row["lsp_confirmed"] = None
                continue
            node = graph["nodes"][row["id"]]
            inside = {loc for loc in locations if loc[0] == row["file"]
                      and node["line"] <= loc[1] <= node["end_line"]}
            covered |= inside
            row["lsp_confirmed"] = bool(inside)
        only: dict[tuple[str, str, int], dict[str, Any]] = {}
        for path, line1 in sorted(set(locations)):
            if (path, line1) in covered:
                continue
            nid, qualname = innermost(path, line1)
            only[(nid, path, line1)] = {"id": nid, "file": path,
                                        "line": line1, "qualname": qualname}
        lsp_only = [only[key] for key in sorted(only)]
        confirmed = sum(1 for row in depth1 if row["lsp_confirmed"])
        result["lsp_only"] = lsp_only
        result["precision"] = {
            "lsp": "used", "server": server,
            "references": len(locations),
            "confirmed": confirmed,
            "unconfirmed": len(depth1) - confirmed,
            "lsp_only": len(lsp_only),
        }

    # -- LSP bridge (compiler-accurate; lazy server) ---------------------- #
    def _lsp_client(self, file: str, language: str | None = None,
                    command: str | None = None):
        from scripts.ocelot_lsp import detect_language, get_client
        lang = language or detect_language(file)
        if not lang:
            return None, {"ok": False,
                          "error": f"no LSP language for {file!r}"}
        return get_client(self.raw_repo_root, lang, command), None

    def lsp_status(self) -> dict[str, Any]:
        from scripts.ocelot_lsp import available_servers
        return available_servers(self.raw_repo_root)

    def lsp_definition(self, file: str, line: int, character: int,
                       *, language: str | None = None,
                       command: str | None = None) -> dict[str, Any]:
        client, err = self._lsp_client(file, language, command)
        return err or client.definition(file, line, character)

    def lsp_references(self, file: str, line: int, character: int,
                       *, language: str | None = None,
                       command: str | None = None,
                       timeout: float | None = None) -> dict[str, Any]:
        client, err = self._lsp_client(file, language, command)
        return err or client.references(file, line, character,
                                        timeout=timeout)

    def lsp_diagnostics(self, file: str, *, language: str | None = None,
                        command: str | None = None,
                        timeout: float | None = None) -> dict[str, Any]:
        client, err = self._lsp_client(file, language, command)
        return err or client.diagnostics(file, timeout=timeout)

    def lsp_callers(self, file: str, line: int, character: int,
                    *, language: str | None = None,
                    command: str | None = None) -> dict[str, Any]:
        client, err = self._lsp_client(file, language, command)
        return err or client.incoming_calls(file, line, character)

    def lsp_callees(self, file: str, line: int, character: int,
                    *, language: str | None = None,
                    command: str | None = None) -> dict[str, Any]:
        client, err = self._lsp_client(file, language, command)
        return err or client.outgoing_calls(file, line, character)

    def lsp_symbol_impact(self, file: str, line: int, character: int,
                          *, language: str | None = None,
                          command: str | None = None) -> dict[str, Any]:
        client, err = self._lsp_client(file, language, command)
        return err or client.symbol_impact(file, line, character)

    def lsp_rename_preview(self, file: str, line: int, character: int,
                           new_name: str, *, language: str | None = None,
                           command: str | None = None) -> dict[str, Any]:
        client, err = self._lsp_client(file, language, command)
        return err or client.rename_preview(file, line, character, new_name)

    def lsp_hover(self, file: str, line: int, character: int,
                  *, language: str | None = None,
                  command: str | None = None) -> dict[str, Any]:
        client, err = self._lsp_client(file, language, command)
        return err or client.hover(file, line, character)

    def lsp_document_symbols(self, file: str, *, language: str | None = None,
                             command: str | None = None) -> dict[str, Any]:
        client, err = self._lsp_client(file, language, command)
        return err or client.document_symbols(file)

    def repo_map_eval(self, *, tasks_path: str | None = None,
                      budgets: str = "500,900,1500",
                      arms: str = "baseline,dev_context,dev_repo_map,both",
                      limit: int | None = None) -> dict[str, Any]:
        from scripts.ocelot_repo_map_eval import DEFAULT_TASKS, evaluate
        return evaluate(self.raw_repo_root,
                        tasks_path=tasks_path or DEFAULT_TASKS,
                        budgets=budgets, arms=arms, limit=limit,
                        memory_path=self.dump)

    def code_search(self, query: str, *, limit: int = 20,
                    include_snippet: bool = True) -> dict[str, Any]:
        from scripts.ocelot_code_search import code_search as _search
        return _search(self.raw_repo_root, query, limit=limit,
                       cache_path=self._tag_cache(),
                       include_snippet=include_snippet)

    def scip(self, path: str, *, summary_only: bool = False) -> dict[str, Any]:
        """Import a SCIP JSON export (or a real .scip when bindings exist)."""
        from scripts.ocelot_scip_import import (
            load_scip, scip_file_summary, scip_import)
        root = Path(self.raw_repo_root).resolve()
        p = (root / path).resolve()
        try:
            p.relative_to(root)
        except ValueError:
            raise ValueError("path escapes the repo root")
        if not p.is_file():
            raise ValueError(f"no such SCIP index: {path}")
        if summary_only:
            index = load_scip(p, root=root)
            return scip_file_summary(index, root=root)
        return scip_import(p, root=root)

    def architecture(self, *, top: int = 15) -> dict[str, Any]:
        from scripts.ocelot_architecture import architecture_report
        return architecture_report(self.raw_repo_root, top=top,
                                   cache_path=self._tag_cache())

    def ast(self, file: str, *, node: str | None = None,
            max_nodes: int = 200) -> dict[str, Any]:
        """The Python AST graph for a file: structural paths + spans.

        Paths are the addresses generic `replace_node`/`insert_*_node`/
        `delete_node`/`wrap_node` ops target. The AST overlay is semantic; the
        bytes live in the lossless CstNode/trivia structure.
        """
        from scripts.ocelot_code_edit import ast_outline
        root = Path(self.raw_repo_root).resolve()
        p = (root / file).resolve()
        try:
            p.relative_to(root)
        except ValueError:
            raise ValueError("path escapes the repo root")
        if p.suffix != ".py" or not p.is_file():
            raise ValueError(f"not a Python file in the repo: {file}")
        out = ast_outline(p.read_text(encoding="utf-8"),
                          target=node, max_nodes=max_nodes)
        out["file"] = file
        return {"ok": True, **out}

    def edit(self, script: dict[str, Any], *,
             task: str | None = None,
             diagnostics: bool = False) -> dict[str, Any]:
        """Apply a graph-addressed edit script and journal the transaction.

        The script is the canonical change; `diff_view` is only a rendering.
        A raw diff/patch input is refused by the edit layer. After an applied
        write, `diagnostics=True` waits up to POST_EDIT_DIAG_TIMEOUT seconds for
        the LSP server's push diagnostics on the edited file and attaches them
        under `result["diagnostics"]`. The journal entry is written before that
        wait and records `"diagnostics": "requested"` or `"skipped"`."""
        from scripts.ocelot_edit import apply_edit_script
        write = _strict_bool(script.get("apply", False), "apply")
        result = apply_edit_script(self.raw_repo_root, script, write=write)
        if result.get("applied"):
            file_rel = str(script.get("file", result.get("file", "")))
            self._drop_cached(file_rel)
            entry = self.journal_append(
                "edit",
                task or f"edit {result.get('file', '?')}",
                f"{len(script.get('ops', []))} ops; "
                f"{result['before']['lines']} -> {result['after']['lines']} lines; "
                f"sha {result['new_sha256'][:12]}",
                files=[result.get("file")],
                ops=script.get("ops"),
                base_sha256=result.get("base_sha256"),
                new_sha256=result.get("new_sha256"),
                backup=result.get("backup"),
                diagnostics="requested" if diagnostics else "skipped",
            )
            result["journaled"] = entry
            result["diagnostics"] = self._post_edit_diagnostics(
                file_rel, enabled=diagnostics)
        return result

    def _post_edit_diagnostics(self, file: str, *,
                               enabled: bool) -> dict[str, Any]:
        """Push diagnostics for a just-written file, or why there are none.

        The LSP client sends didChange when the file's sha differs from the
        last one it saw, then waits for the server's publish. Failures are
        recorded here and never raised, so they cannot fail the edit."""
        if not enabled:
            return {"skipped": "diagnostics=false"}
        from scripts.ocelot_lsp import detect_language, server_candidates
        try:
            lang = detect_language(file)
            if not lang:
                return {"skipped": f"no LSP language for {file!r}"}
            ready = [c for c in server_candidates(lang, self.raw_repo_root)
                     if c["available"]]
            if not ready:
                return {"skipped": f"unavailable: no {lang} language server found"}
            res = self.lsp_diagnostics(file, timeout=POST_EDIT_DIAG_TIMEOUT)
        except Exception as e:  # noqa: BLE001 - recorded, not raised
            return {"error": f"{type(e).__name__}: {e}"}
        if not res.get("ok"):
            return {"error": str(res.get("error") or "diagnostics failed")}
        items = res.get("diagnostics") or []
        errors = sum(1 for d in items if d.get("severity") == 1)
        published = bool(res.get("published"))
        # "unknown": the wait ended without a publish, so nothing is known.
        # "warnings" covers any published non-error item (severity 2-4).
        if errors:
            verdict = "errors"
        elif not published:
            verdict = "unknown"
        elif not items:
            verdict = "clean"
        else:
            verdict = "warnings"
        return {
            "ok": True,
            "verdict": verdict,
            "count": len(items),
            "errors": errors,
            "warnings": sum(1 for d in items if d.get("severity") == 2),
            "published": published,
            "items": [{**d, "line1": int(d.get("line") or 0) + 1}
                      for d in items[:DIAG_ITEM_LIMIT]],
            "server": ready[0]["name"],
        }

    # -- journal ------------------------------------------------------------ #
    def journal_append(self, kind: str, task: str, summary: str,
                       **fields: Any) -> dict[str, Any]:
        entry = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "kind": str(kind),
            "task": str(task),
            "summary": str(summary),
            **{k: v for k, v in fields.items() if v is not None},
        }
        self.journal.parent.mkdir(parents=True, exist_ok=True)
        with self.journal.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, sort_keys=True) + "\n")
        return entry

    def journal_recent(self, n: int = 20) -> list[dict[str, Any]]:
        if not self.journal.exists():
            return []
        try:
            lines = self.journal.read_text(encoding="utf-8",
                                           errors="replace").splitlines()
        except OSError:
            return []
        out = []
        for line in lines[-max(0, int(n)):]:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return out


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def _print(obj: Any, *, pretty: bool) -> None:
    if pretty:
        print(json.dumps(obj, indent=2, sort_keys=False))
    else:
        print(json.dumps(obj, sort_keys=False))


def _cmd_build(args: argparse.Namespace) -> int:
    report = build_index(args.root, args.out or args.dump,
                         include_docs=args.docs,
                         include_git=not args.no_git,
                         include_scripts=not args.no_scripts,
                         git_limit=args.git_limit)
    _print(report, pretty=args.pretty)
    return 0


def _cmd_query(args: argparse.Namespace, mem: DevMemory) -> int:
    cmd = args.command
    if cmd == "search":
        out = {"query": args.text,
               "results": mem.search(args.text, types=args.types,
                                     limit=args.limit)}
    elif cmd == "show":
        n = mem.node(args.id)
        if n is None:
            out = {"ok": False, "error": f"no node {args.id}"}
        else:
            out = {"ok": True, "node": mem.view(args.id),
                   "attrs": n.get("attrs", {}),
                   "snippet": mem.snippet(args.id),
                   "related": mem.related(args.id)}
    elif cmd == "neighbours":
        out = {"ok": True, "node": mem.view(args.id),
               "neighbours": mem.related(args.id)}
        if args.edge:
            out["filtered"] = {
                "out": [mem.view(int(e["tgt"])) for e in
                        mem._out.get(args.id, []) if e["type"] == args.edge],
                "in": [mem.view(int(e["src"])) for e in
                       mem._in.get(args.id, []) if e["type"] == args.edge],
            }
    elif cmd == "file":
        out = mem.file(args.path)
    elif cmd == "symbol":
        out = mem.symbol(args.name)
    elif cmd == "seed":
        out = mem.seed(args.seed_id)
    elif cmd == "rule":
        out = mem.rule(args.name)
    elif cmd == "tests":
        out = mem.tests_for(args.target)
    elif cmd == "context":
        out = mem.context(args.task, max_items=args.max_items,
                          mode=args.mode,
                          budget_tokens=args.budget_tokens)
    elif cmd == "outline":
        out = mem.outline_target(args.target)
    elif cmd == "brief":
        out = mem.brief(args.task, budget_tokens=args.budget_tokens,
                        write=args.write)
    elif cmd == "ast":
        out = mem.ast(args.file, node=args.node, max_nodes=args.max_nodes)
    elif cmd == "repo-map":
        out = mem.repo_map(args.task, budget_tokens=args.budget_tokens,
                           focus_files=args.focus_file or None,
                           force_refresh=args.force,
                           scip_path=args.scip)
    elif cmd == "impact":
        out = mem.impact(args.file, depth=args.depth,
                         scip_path=args.scip)
    elif cmd == "architecture":
        out = mem.architecture(top=args.top)
    elif cmd == "scip":
        out = mem.scip(args.path, summary_only=args.summary_only)
    elif cmd == "code-search":
        out = mem.code_search(args.query, limit=args.limit,
                              include_snippet=not args.no_snippet)
    elif cmd == "lsp-status":
        out = mem.lsp_status()
    elif cmd in ("definition", "references", "callers", "callees",
                 "symbol-impact", "hover", "rename-preview",
                 "diagnostics", "document-symbols"):
        try:
            lang = getattr(args, "language", None)
            if cmd == "definition":
                out = mem.lsp_definition(args.file, args.line,
                                         args.character, language=lang)
            elif cmd == "references":
                out = mem.lsp_references(args.file, args.line,
                                         args.character, language=lang)
            elif cmd == "callers":
                out = mem.lsp_callers(args.file, args.line,
                                      args.character, language=lang)
            elif cmd == "callees":
                out = mem.lsp_callees(args.file, args.line,
                                      args.character, language=lang)
            elif cmd == "symbol-impact":
                out = mem.lsp_symbol_impact(args.file, args.line,
                                            args.character, language=lang)
            elif cmd == "hover":
                out = mem.lsp_hover(args.file, args.line,
                                    args.character, language=lang)
            elif cmd == "rename-preview":
                out = mem.lsp_rename_preview(args.file, args.line,
                                             args.character, args.new_name,
                                             language=lang)
            elif cmd == "diagnostics":
                out = mem.lsp_diagnostics(args.file, language=lang)
            elif cmd == "document-symbols":
                out = mem.lsp_document_symbols(args.file, language=lang)
        except Exception as e:  # noqa: BLE001 - CLI reports honestly
            out = {"ok": False, "error": f"{type(e).__name__}: {e}"}
    elif cmd.startswith("session-"):
        from scripts.ocelot_dev_session import (
            DevSession, list_sessions, load_session)
        try:
            if cmd == "session-start":
                sess = DevSession.start(args.task,
                                        max_attempts=args.max_attempts,
                                        root=mem.raw_repo_root)
                out = {"ok": True, "state": sess.state(),
                       "next": sess.next_action()}
            elif cmd == "session-record":
                fields = json.loads(args.fields or "{}")
                if not isinstance(fields, dict):
                    raise ValueError("--fields must be a JSON object")
                sess = load_session(args.session_id, root=mem.raw_repo_root)
                node = sess.record(args.kind, **fields)
                out = {"ok": True, "node": node,
                       "next": sess.next_action()}
            elif cmd == "session-state":
                out = load_session(args.session_id,
                                   root=mem.raw_repo_root).state()
            elif cmd == "session-next":
                sess = load_session(args.session_id, root=mem.raw_repo_root)
                out = {"ok": True, "next": sess.next_action()}
            elif cmd == "session-finish":
                sess = load_session(args.session_id, root=mem.raw_repo_root)
                out = sess.finish(args.outcome)
            elif cmd == "session-list":
                out = {"ok": True,
                       "sessions": list_sessions(root=mem.raw_repo_root)}
            else:
                raise ValueError(f"unknown session command {cmd!r}")
        except Exception as e:  # noqa: BLE001 - CLI boundary reports honestly
            out = {"ok": False, "error": f"{type(e).__name__}: {e}"}
    elif cmd.startswith("symbol-"):
        # `symbol-impact` is the LSP verb; the symbol-graph one is
        # `symbol-graph-impact`.
        op = cmd.split("-", 1)[1]
        if op == "graph-impact":
            op = "impact"
        out = mem.symbol_graph(op, args.symbol,
                               depth=getattr(args, "depth", None),
                               min_confidence=getattr(args, "min_confidence", 0.0),
                               precise=getattr(args, "precise", False))
    elif cmd == "edit":
        if args.script:
            script = json.loads(Path(args.script).read_text(encoding="utf-8"))
        elif args.ops_json:
            script = {"ops": json.loads(args.ops_json)}
        else:
            raise SystemExit("edit needs --script or --ops-json")
        script["file"] = args.file
        if args.apply:
            script["apply"] = True
        out = mem.edit(script, task=args.task,
                       diagnostics=args.diagnostics)
    elif cmd == "stats":
        out = mem.stats()
    elif cmd == "changed":
        out = mem.changed(include_all=args.all, limit=args.limit)
    elif cmd == "recent":
        out = {"ok": True, "entries": mem.journal_recent(args.n)}
    elif cmd == "record":
        out = {"ok": True, "entry": mem.journal_append(
            args.kind, args.task, args.summary,
            files=args.file or [], command=args.commandline,
            exit_code=args.exit_code)}
    else:
        raise SystemExit(f"unknown command {cmd!r}")
    _print(out, pretty=args.pretty)
    return 0 if out.get("ok", True) else 1


def _cmd_repo_map_eval(args: argparse.Namespace, mem: DevMemory) -> int:
    report = mem.repo_map_eval(tasks_path=args.tasks_path,
                               budgets=args.budgets, arms=args.arms,
                               limit=args.limit)
    if args.json:
        _print(report, pretty=args.pretty)
    else:
        print(report["markdown"])
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--dump", default=str(DEFAULT_DUMP),
                   help="dev-memory snapshot path")
    p.add_argument("--journal", default=str(DEFAULT_JOURNAL),
                   help="decision/verification journal path")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--pretty", action="store_true",
                        help="indent JSON output")
    # The checkout the query tools act on. Same default as the MCP server.
    common.add_argument("--root", default=(
        os.environ.get("OCELOT_DEV_ROOT") or str(ROOT)),
        help="checkout the tools act on (default: OCELOT_DEV_ROOT or this repo)")
    # `build` has its own --root (the tree to index), so it does not get the
    # query-side option.
    build_common = argparse.ArgumentParser(add_help=False)
    build_common.add_argument("--pretty", action="store_true",
                              help="indent JSON output")
    sub = p.add_subparsers(dest="command", required=True)

    b = sub.add_parser("build", help="build/refresh the snapshot",
                       parents=[build_common])
    b.add_argument("--root", default=str(ROOT))
    b.add_argument("--out", default=None)
    b.add_argument("--docs", choices=("features", "all", "none"),
                   default="features")
    b.add_argument("--no-git", action="store_true")
    b.add_argument("--no-scripts", action="store_true")
    b.add_argument("--git-limit", type=int, default=200)
    b.set_defaults(func=_cmd_build, needs_mem=False)

    s = sub.add_parser("search", help="find nodes by name/path/title",
                   parents=[common])
    s.add_argument("text")
    s.add_argument("--type", dest="types", action="append",
                   choices=("File", "Symbol", "Test", "Seed", "Rule", "Doc",
                            "Commit", "Failure", "Repo"))
    s.add_argument("--limit", type=int, default=20)

    sh = sub.add_parser("show", help="show one node by id", parents=[common])
    sh.add_argument("id", type=int)

    nb = sub.add_parser("neighbours", help="show a node's edges",
                   parents=[common])
    nb.add_argument("id", type=int)
    nb.add_argument("--edge", default=None)

    f = sub.add_parser("file", help="file details", parents=[common])
    f.add_argument("path")

    sy = sub.add_parser("symbol", help="symbol details", parents=[common])
    sy.add_argument("name")

    sd = sub.add_parser("seed", help="seed details", parents=[common])
    sd.add_argument("seed_id")

    r = sub.add_parser("rule", help="rule details", parents=[common])
    r.add_argument("name")

    t = sub.add_parser("tests", help="tests covering a file/symbol/seed",
                   parents=[common])
    t.add_argument("target")

    c = sub.add_parser("context", help="build a cited context pack for a task",
                   parents=[common])
    c.add_argument("task")
    c.add_argument("--max-items", type=int, default=8)
    c.add_argument("--mode", choices=("auto", "outline", "full"),
                   default="auto",
                   help="auto: full top anchors, outlines for the rest")
    c.add_argument("--budget-tokens", type=int, default=6000)

    ol = sub.add_parser("outline", help="signatures/headings, no bodies",
                        parents=[common])
    ol.add_argument("target")
    ol.set_defaults(func=_cmd_query, needs_mem=True)

    br = sub.add_parser("brief", help="pre-loaded repo brief",
                        parents=[common])
    br.add_argument("--task", default=None)
    br.add_argument("--budget-tokens", type=int, default=4000)
    br.add_argument("--write", action="store_true",
                    help="write var/ocelot_dev_brief.md")
    br.set_defaults(func=_cmd_query, needs_mem=True)

    rm = sub.add_parser("repo-map",
                        help="ranked, token-budgeted repo map",
                        parents=[common])
    rm.add_argument("task", nargs="?", default="")
    rm.add_argument("--budget-tokens", type=int, default=1500)
    rm.add_argument("--focus-file", action="append")
    rm.add_argument("--force", action="store_true")
    rm.add_argument("--scip", default=None,
                    help="optional SCIP JSON export to add precise edges")
    rm.set_defaults(func=_cmd_query, needs_mem=True)

    ls = sub.add_parser("lsp-status", parents=[common],
                        help="LSP server availability")
    ls.set_defaults(func=_cmd_query, needs_mem=True)

    for _name in ("definition", "references", "callers", "callees",
                  "symbol-impact", "hover"):
        _p = sub.add_parser(_name, parents=[common],
                            help=f"LSP {_name} at FILE LINE CHARACTER (0-based)")
        _p.add_argument("file")
        _p.add_argument("line", type=int)
        _p.add_argument("character", type=int)
        _p.add_argument("--language", default=None)
        _p.set_defaults(func=_cmd_query, needs_mem=True)

    _rp = sub.add_parser("rename-preview", parents=[common],
                         help="LSP rename preview (review-only)")
    _rp.add_argument("file")
    _rp.add_argument("line", type=int)
    _rp.add_argument("character", type=int)
    _rp.add_argument("new_name")
    _rp.add_argument("--language", default=None)
    _rp.set_defaults(func=_cmd_query, needs_mem=True)

    for _name in ("diagnostics", "document-symbols"):
        _p = sub.add_parser(_name, parents=[common],
                            help=f"LSP {_name} for FILE")
        _p.add_argument("file")
        _p.add_argument("--language", default=None)
        _p.set_defaults(func=_cmd_query, needs_mem=True)

    for _name in ("symbol-callers", "symbol-callees", "symbol-graph-impact",
                  "symbol-resolve"):
        _p = sub.add_parser(_name, parents=[common],
                            help=f"symbol graph {_name.split('-', 1)[1]} "
                                 "(syntactic; lines 1-based)")
        _p.add_argument("symbol",
                        help='"path::qualname", a qualname, or a bare name')
        if _name != "symbol-resolve":
            _p.add_argument("--depth", type=int, default=None,
                            help="hops (callers/callees 1, impact 3)")
            _p.add_argument("--min-confidence", type=float, default=0.0)
        if _name in ("symbol-callers", "symbol-graph-impact"):
            _p.add_argument("--precise", action="store_true",
                            help="confirm direct callers with LSP references")
        _p.set_defaults(func=_cmd_query, needs_mem=True)

    rme = sub.add_parser("repo-map-eval", parents=[common],
                         help="deterministic repo-map retrieval evaluation")
    rme.add_argument("--tasks", dest="tasks_path", default=None)
    rme.add_argument("--budgets", default="500,900,1500")
    rme.add_argument("--arms",
                     default="baseline,dev_context,dev_repo_map,both")
    rme.add_argument("--limit", type=int, default=None)
    rme.add_argument("--json", action="store_true")
    rme.set_defaults(func=_cmd_repo_map_eval, needs_mem=True)

    cs = sub.add_parser("code-search", parents=[common],
                        help="lexical BM25 + graph PageRank search")
    cs.add_argument("query")
    cs.add_argument("--limit", type=int, default=20)
    cs.add_argument("--no-snippet", action="store_true")
    cs.set_defaults(func=_cmd_query, needs_mem=True)

    sc = sub.add_parser("scip", parents=[common],
                        help="import a SCIP JSON export")
    sc.add_argument("path")
    sc.add_argument("--summary-only", action="store_true")
    sc.set_defaults(func=_cmd_query, needs_mem=True)

    ar = sub.add_parser("architecture", parents=[common],
                        help="deterministic architecture summary")
    ar.add_argument("--top", type=int, default=15)
    ar.set_defaults(func=_cmd_query, needs_mem=True)

    im = sub.add_parser("impact", help="transitive dependents of a file",
                        parents=[common])
    im.add_argument("file")
    im.add_argument("--depth", type=int, default=2)
    im.add_argument("--scip", default=None,
                    help="optional SCIP JSON export to add precise edges")
    im.set_defaults(func=_cmd_query, needs_mem=True)

    astp = sub.add_parser("ast", help="the Python AST graph (paths + spans)",
                          parents=[common])
    astp.add_argument("file")
    astp.add_argument("--node", default=None,
                      help="show only this AST path's subtree")
    astp.add_argument("--max-nodes", type=int, default=200)
    astp.set_defaults(func=_cmd_query, needs_mem=True)

    ed = sub.add_parser("edit",
                        help="graph-addressed structural edit (diff is only a view)",
                        parents=[common])
    ed.add_argument("--file", required=True)
    ed.add_argument("--script", default=None,
                    help="JSON {file, base_sha256?, ops: [...]} (file overridden)")
    ed.add_argument("--ops-json", default=None,
                    help="inline JSON array of ops")
    ed.add_argument("--apply", action="store_true")
    ed.add_argument("--task", default=None,
                    help="journal task label")
    ed.add_argument("--diagnostics", action="store_true",
                    help="after --apply, wait up to 8 s for LSP diagnostics")
    ed.set_defaults(func=_cmd_query, needs_mem=True)

    st = sub.add_parser("stats", help="snapshot histograms", parents=[common])
    st.set_defaults(func=_cmd_query, needs_mem=True)

    rec = sub.add_parser("record", help="append a decision/verification entry",
                   parents=[common])
    rec.add_argument("--kind", choices=("decision", "verification"),
                     default="decision")
    rec.add_argument("--task", required=True)
    rec.add_argument("--summary", required=True)
    rec.add_argument("--file", action="append")
    rec.add_argument("--commandline", default=None)
    rec.add_argument("--exit-code", type=int, default=None)
    rec.set_defaults(func=_cmd_query, needs_mem=True)

    ch = sub.add_parser("changed", help="working-tree changes",
                        parents=[common])
    ch.add_argument("--all", action="store_true",
                    help="include generated/eval/corpus paths")
    ch.add_argument("--limit", type=int, default=200)
    ch.set_defaults(func=_cmd_query, needs_mem=True)

    ss = sub.add_parser("session-start", parents=[common],
                        help="start a dev-session graph")
    ss.add_argument("task")
    ss.add_argument("--max-attempts", type=int, default=3)
    ss.set_defaults(func=_cmd_query, needs_mem=True)

    sr = sub.add_parser("session-record", parents=[common],
                        help="append a session node")
    sr.add_argument("session_id")
    sr.add_argument("kind", choices=("plan", "step", "attempt", "edit",
                                     "verification", "decision"))
    sr.add_argument("--fields", default="{}",
                    help="JSON object of fields")
    sr.set_defaults(func=_cmd_query, needs_mem=True)

    sst = sub.add_parser("session-state", parents=[common],
                         help="session graph snapshot")
    sst.add_argument("session_id")
    sst.set_defaults(func=_cmd_query, needs_mem=True)

    sn = sub.add_parser("session-next", parents=[common],
                        help="next workflow action")
    sn.add_argument("session_id")
    sn.set_defaults(func=_cmd_query, needs_mem=True)

    sf = sub.add_parser("session-finish", parents=[common],
                        help="close a session")
    sf.add_argument("session_id")
    sf.add_argument("outcome")
    sf.set_defaults(func=_cmd_query, needs_mem=True)

    sl = sub.add_parser("session-list", parents=[common],
                        help="list sessions")
    sl.set_defaults(func=_cmd_query, needs_mem=True)

    recent = sub.add_parser("recent", help="recent journal entries",
                   parents=[common])
    recent.add_argument("-n", type=int, default=20)
    recent.set_defaults(func=_cmd_query, needs_mem=True)

    for name in ("search", "show", "neighbours", "file", "symbol", "seed",
                 "rule", "tests", "context", "outline", "brief", "repo-map",
                 "impact", "architecture", "scip", "code-search", "ast",
                 "edit", "changed", "session-start", "session-record",
                 "session-state", "session-next", "session-finish",
                 "session-list"):
        sub.choices[name].set_defaults(func=_cmd_query, needs_mem=True)

    args = p.parse_args(argv)
    try:
        if not getattr(args, "needs_mem", True):
            return args.func(args)
        mem = DevMemory(Path(args.dump), Path(args.journal),
                        root=Path(args.root))
        return args.func(args, mem)
    finally:
        try:
            from scripts.ocelot_lsp import close_all
            close_all()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
