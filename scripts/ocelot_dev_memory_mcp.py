"""ocelot_dev_memory_mcp — stdio MCP server over the dev-memory snapshot.

This is the "A" integration surface: an existing coding agent (OpenCode,
Claude Code, Cursor, any MCP client) gets Ocelot's repo memory as tools, while
Ocelot stays the memory and citation source. The agent decides; the tools only
answer structural questions and record decisions/verification receipts.

It is deliberately stdlib-only (no `mcp` package dependency) and READ-ONLY over
the graph, with one small append-only journal for decisions and verifications.
The graph itself is built by `scripts/ocelot_dev_memory.py`.

Run (stdio):

    .venv/bin/python -m scripts.ocelot_dev_memory_mcp

Environment:
    OCELOT_DEV_DUMP     snapshot path (default var/ocelot_dev_graph.json)
    OCELOT_DEV_JOURNAL  journal path  (default var/ocelot_dev_journal.jsonl)
    OCELOT_DEV_AUTOBUILD  "1" to build the snapshot on first start if absent
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Callable

from scripts.ocelot_dev_memory import (
    DEFAULT_DUMP,
    DEFAULT_JOURNAL,
    DevMemory,
    build_index,
)

SERVER_NAME = "ocelot-dev-memory"
SERVER_VERSION = "0.1.0"
PROTOCOL_VERSION = "2024-11-05"


# --------------------------------------------------------------------------- #
# tool schemas
# --------------------------------------------------------------------------- #
def _schema(props: dict[str, Any], required: list[str] | None = None) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": props,
        "required": required or [],
        "additionalProperties": False,
    }


_TOOLS: list[dict[str, Any]] = [
    {
        "name": "dev_context",
        "description": (
            "Build a cited context pack for a development task. Use this FIRST "
            "when starting a task in this repo: it returns the relevant seed / "
            "rule / file / symbol / test / doc nodes with file paths and line "
            "ranges, so you can read the actual source rather than guess. The "
            "pack is selected mechanically from the repo graph; it is not a "
            "decision about what to change."),
        "inputSchema": _schema({
            "task": {"type": "string",
                     "description": "Natural-language task or question."},
            "max_items": {"type": "integer", "default": 8,
                          "description": "Maximum context items (default 8)."},
            "mode": {"type": "string", "enum": ["auto", "outline", "full"],
                     "default": "auto",
                     "description": "auto: full top anchors, outlines for the rest."},
            "budget_tokens": {"type": "integer", "default": 6000,
                              "description": "Estimated token budget."},
        }, ["task"]),
    },
    {
        "name": "dev_brief",
        "description": (
            "Pre-load a compact repo brief: layout, build/test commands, key "
            "docs, recent commits, working-tree changes, known failures, and "
            "(optionally) a task context pack. Call it once at session start "
            "or when you need cheap orientation without reading many files."),
        "inputSchema": _schema({
            "task": {"type": "string",
                     "description": "Optional task to append as a context pack."},
            "budget_tokens": {"type": "integer", "default": 4000},
            "write": {"type": "boolean", "default": False,
                      "description": "Write var/ocelot_dev_brief.md too."},
        }),
    },
    {
        "name": "dev_repo_map",
        "description": (
            "Ranked, token-budgeted repo map (tree-sitter tags + personalized "
            "PageRank). Use it when you need the shape of the codebase rather "
            "than full snippets: full outlines for the hottest files, public "
            "symbols for the middle, a listing for the tail. Task-named seeds/"
            "files become focus files."),
        "inputSchema": _schema({
            "task": {"type": "string", "default": ""},
            "budget_tokens": {"type": "integer", "default": 1500},
            "focus_files": {"type": "array", "items": {"type": "string"}},
            "force_refresh": {"type": "boolean", "default": False},
            "scip_path": {"type": "string",
                          "description": "Optional SCIP JSON export for precise edges."},
        }),
    },
    {
        "name": "dev_impact",
        "description": (
            "Transitive dependents of a file over the tree-sitter reference "
            "graph (who references symbols defined here). Use before changing "
            "a widely used module."),
        "inputSchema": _schema({
            "file": {"type": "string"},
            "depth": {"type": "integer", "default": 2},
            "scip_path": {"type": "string"},
        }, ["file"]),
    },
    {
        "name": "dev_architecture",
        "description": (
            "Deterministic architecture summary: hubs, reference cycles "
            "(Tarjan SCC), coupling, module boundaries, dead-code candidates "
            "(heuristic) and test/source ratio. File-level and syntactic; use "
            "LSP/SCIP for compiler-accurate answers."),
        "inputSchema": _schema({
            "top": {"type": "integer", "default": 15},
        }),
    },
    {
        "name": "dev_code_search",
        "description": (
            "Lexical hybrid code search: BM25 over paths/symbols/source lines, "
            "reranked by repo-map PageRank via reciprocal rank fusion. Use it "
            "to locate candidates, then dev_context/dev_repo_map to expand and "
            "LSP/SCIP for precise navigation."),
        "inputSchema": _schema({
            "query": {"type": "string"},
            "limit": {"type": "integer", "default": 20},
            "include_snippet": {"type": "boolean", "default": True},
        }, ["query"]),
    },
    {
        "name": "dev_scip",
        "description": (
            "Import a SCIP JSON export (from `scip print --json`) and return "
            "normalized definitions/references, repo-map edges and per-file "
            "counts. Real .scip protobuf requires protobuf + scip_pb2; absent "
            "bindings are refused honestly."),
        "inputSchema": _schema({
            "path": {"type": "string"},
            "summary_only": {"type": "boolean", "default": False},
        }, ["path"]),
    },
    {
        "name": "dev_search",
        "description": (
            "Search the repo graph by name/path/title/description. Returns "
            "node ids, types and labels. Use dev_file/dev_symbol/dev_seed for "
            "details, or dev_node for attrs and edges."),
        "inputSchema": _schema({
            "text": {"type": "string"},
            "types": {"type": "array", "items": {"type": "string"},
                      "description": "Optional type filter, e.g. ['Seed','Rule']."},
            "limit": {"type": "integer", "default": 20},
        }, ["text"]),
    },
    {
        "name": "dev_file",
        "description": (
            "Everything the graph knows about one file: symbols, tests, "
            "imports/imported_by, docs, known failures and recent commits."),
        "inputSchema": _schema({
            "path": {"type": "string",
                     "description": "Repo-relative path, e.g. domains/teach.py."},
        }, ["path"]),
    },
    {
        "name": "dev_symbol",
        "description": (
            "Find a function/class/struct/enum by name or qualname. Returns "
            "its file, line range, docstring, source snippet, tests and graph "
            "neighbours."),
        "inputSchema": _schema({
            "name": {"type": "string",
                     "description": "Exact or partial symbol name."},
        }, ["name"]),
    },
    {
        "name": "dev_outline",
        "description": (
            "Compact structural view of a file/symbol/seed/doc: signatures, "
            "docstring first lines, imports and test names, with line "
            "citations and no bodies. Use it to pre-load context cheaply; "
            "edit the real file, never this view."),
        "inputSchema": _schema({
            "target": {"type": "string",
                       "description": "File path, symbol, seed id, or doc path."},
        }, ["target"]),
    },
    {
        "name": "dev_ast",
        "description": (
            "The Python AST graph for a file: structural paths "
            "(e.g. body[3].body[0].value), node types, line spans and "
            "previews. Use these paths as `target` for generic replace_node / "
            "insert_before_node / insert_after_node / delete_node / "
            "wrap_node ops."),
        "inputSchema": _schema({
            "file": {"type": "string", "description": "Repo-relative .py file."},
            "node": {"type": "string",
                     "description": "Optional AST path to show as a subtree."},
            "max_nodes": {"type": "integer", "default": 200},
        }, ["file"]),
    },
    {
        "name": "dev_edit",
        "description": (
            "Apply a GRAPH-ADDRESSED edit script. The ops are semantic, not a "
            "text diff: Python (replace_symbol, replace_body, insert_import, "
            "replace_node, insert_before_node, insert_after_node, delete_node, "
            "wrap_node, ...), Markdown (section ops), JSON (path ops). Preview "
            "by default; "
            "set apply=true to write atomically (with a backup and journal "
            "entry). A raw diff/patch is refused; `diff_view` is output only."),
        "inputSchema": _schema({
            "file": {"type": "string",
                     "description": "Repo-relative .py, .md, .json, .rs or .lua path."},
            "ops": {"type": "array", "items": {"type": "object"},
                    "description": "Ordered semantic operations."},
            "apply": {"type": "boolean", "default": False},
            "base_sha256": {"type": "string",
                            "description": "Optional optimistic-concurrency check."},
            "cst_graph": {"type": "object",
                          "description": "Optional synthetic/post-parsed CstNode graph for .rs/.lua when tree-sitter is unavailable."},
            "task": {"type": "string",
                     "description": "Optional journal task label."},
        }, ["file", "ops"]),
    },
    {
        "name": "dev_tests",
        "description": (
            "Tests covering a file, symbol or seed. Use before changing a "
            "module/seed to know the scoped gate, and after a change to record "
            "the verification command with dev_record."),
        "inputSchema": _schema({
            "target": {"type": "string",
                       "description": "File path, symbol name, or seed id."},
        }, ["target"]),
    },
    {
        "name": "dev_seed",
        "description": (
            "A seed's manifest: version, description, dependency closure, "
            "the rules/concepts/reflexes it ships, tests that mention it, and "
            "docs that document it."),
        "inputSchema": _schema({
            "seed_id": {"type": "string",
                        "description": "Seed id, e.g. gap_awareness."},
        }, ["seed_id"]),
    },
    {
        "name": "dev_rule",
        "description": (
            "Find a seed rule by name and show its seed, file and rule body. "
            "Use this before editing a rule so you see the existing match / "
            "where / effects rather than re-deriving them."),
        "inputSchema": _schema({
            "name": {"type": "string"},
        }, ["name"]),
    },
    {
        "name": "dev_node",
        "description": (
            "Show one graph node by integer id: type, attrs, source snippet "
            "and grouped neighbours. Ids come from dev_search/dev_context."),
        "inputSchema": _schema({
            "id": {"type": "integer"},
            "include_snippet": {"type": "boolean", "default": True},
        }, ["id"]),
    },
    {
        "name": "dev_neighbours",
        "description": (
            "Out- and in-neighbours of a node, grouped by edge type. Useful "
            "for dependency/seed/test/doc expansion."),
        "inputSchema": _schema({
            "id": {"type": "integer"},
            "edge": {"type": "string",
                     "description": "Optional edge type filter."},
        }, ["id"]),
    },
    {
        "name": "dev_graph_query",
        "description": (
            "Evaluate a substrate DSL Term-tree against the snapshot on the "
            "substrate's own evaluator (read-only). Pass either `term` (wire "
            "dict) or `match` ('TYPE where attr OP value [and ...]')."),
        "inputSchema": _schema({
            "term": {"type": "object"},
            "match": {"type": "string"},
        }),
    },
    {
        "name": "dev_stats",
        "description": "Snapshot histograms and repo summary.",
        "inputSchema": _schema({}),
    },
    {
        "name": "dev_changed",
        "description": (
            "Working-tree changes from `git status --porcelain`, with graph "
            "links for changed files. Use it to see what the current session "
            "has touched, and whether the snapshot is stale."),
        "inputSchema": _schema({
            "all": {"type": "boolean", "default": False,
                    "description": "Include generated/eval/corpus paths."},
            "limit": {"type": "integer", "default": 200},
        }),
    },
    {
        "name": "dev_record",
        "description": (
            "Append a decision or verification receipt to the shared dev "
            "journal. Use it after a scoped test/build command so the next "
            "agent/session can see what was tried and what passed."),
        "inputSchema": _schema({
            "kind": {"type": "string", "enum": ["decision", "verification"],
                     "default": "decision"},
            "task": {"type": "string"},
            "summary": {"type": "string"},
            "files": {"type": "array", "items": {"type": "string"}},
            "command": {"type": "string"},
            "exit_code": {"type": "integer"},
        }, ["task", "summary"]),
    },
    {
        "name": "dev_session_start",
        "description": (
            "Start a replayable dev-session graph (Task -> Plan -> Step -> "
            "Attempt -> Edit -> Verification -> Decision). Returns the new "
            "session id, state and the workflow's next action. This records "
            "facts only; it does not edit files or run tests."),
        "inputSchema": _schema({
            "task": {"type": "string"},
            "max_attempts": {"type": "integer", "default": 3},
        }, ["task"]),
    },
    {
        "name": "dev_session_record",
        "description": (
            "Append one typed node to a dev session. Kinds: plan, step, "
            "attempt, edit, verification, decision. Returns the new node and "
            "the next workflow action."),
        "inputSchema": _schema({
            "session_id": {"type": "string"},
            "kind": {"type": "string",
                     "enum": ["plan", "step", "attempt", "edit",
                              "verification", "decision"]},
            "fields": {"type": "object"},
        }, ["session_id", "kind"]),
    },
    {
        "name": "dev_session_state",
        "description": "The session graph snapshot plus the next action.",
        "inputSchema": _schema({
            "session_id": {"type": "string"},
        }, ["session_id"]),
    },
    {
        "name": "dev_session_next",
        "description": "The next workflow action and its reason.",
        "inputSchema": _schema({
            "session_id": {"type": "string"},
        }, ["session_id"]),
    },
    {
        "name": "dev_session_finish",
        "description": "Close a dev session with an outcome.",
        "inputSchema": _schema({
            "session_id": {"type": "string"},
            "outcome": {"type": "string"},
        }, ["session_id", "outcome"]),
    },
    {
        "name": "dev_session_list",
        "description": "List persisted dev sessions.",
        "inputSchema": _schema({}),
    },
    {
        "name": "dev_recent",
        "description": "Recent dev-journal entries (decisions/verifications).",
        "inputSchema": _schema({
            "n": {"type": "integer", "default": 20},
        }),
    },
]


# LSP tools are appended here to keep the base tool table readable.
def _lsp_pos_schema(*, new_name: bool = False) -> dict[str, Any]:
    props = {
        "file": {"type": "string"},
        "line": {"type": "integer",
                 "description": "0-based line (LSP-native)."},
        "character": {"type": "integer",
                      "description": "0-based UTF-16 character (LSP-native)."},
        "language": {"type": "string"},
    }
    if new_name:
        props["new_name"] = {"type": "string"}
    return _schema(props, ["file", "line", "character"] +
                   (["new_name"] if new_name else []))


_TOOLS.extend([
    {
        "name": "dev_lsp_status",
        "description": "LSP server availability for this checkout (does not start servers).",
        "inputSchema": _schema({}),
    },
    {
        "name": "dev_definition",
        "description": "Compiler-accurate definition at a position via LSP.",
        "inputSchema": _lsp_pos_schema(),
    },
    {
        "name": "dev_references",
        "description": "Compiler-accurate references at a position via LSP.",
        "inputSchema": _lsp_pos_schema(),
    },
    {
        "name": "dev_callers",
        "description": "Incoming calls (callers) at a symbol position via LSP.",
        "inputSchema": _lsp_pos_schema(),
    },
    {
        "name": "dev_callees",
        "description": "Outgoing calls (callees) at a symbol position via LSP.",
        "inputSchema": _lsp_pos_schema(),
    },
    {
        "name": "dev_symbol_impact",
        "description": "Resolved references grouped by file for a symbol position via LSP.",
        "inputSchema": _lsp_pos_schema(),
    },
    {
        "name": "dev_rename_preview",
        "description": "LSP rename preview (review-only; never writes).",
        "inputSchema": _lsp_pos_schema(new_name=True),
    },
    {
        "name": "dev_diagnostics",
        "description": "LSP push diagnostics for a file (published issues only).",
        "inputSchema": _schema({
            "file": {"type": "string"},
            "language": {"type": "string"},
        }, ["file"]),
    },
    {
        "name": "dev_hover",
        "description": "LSP hover/type/documentation at a position.",
        "inputSchema": _lsp_pos_schema(),
    },
    {
        "name": "dev_document_symbols",
        "description": "LSP document symbol hierarchy for a file.",
        "inputSchema": _schema({
            "file": {"type": "string"},
            "language": {"type": "string"},
        }, ["file"]),
    },
])


# --------------------------------------------------------------------------- #
# dispatch
# --------------------------------------------------------------------------- #
class DevMemoryServer:
    def __init__(self, memory: DevMemory):
        self.mem = memory
        self._handlers: dict[str, Callable[[dict[str, Any]], Any]] = {
            "dev_context": self._context,
            "dev_brief": self._brief,
            "dev_repo_map": self._repo_map,
            "dev_impact": self._impact,
            "dev_architecture": self._architecture,
            "dev_scip": self._scip,
            "dev_code_search": self._code_search,
            "dev_lsp_status": self._lsp_status,
            "dev_definition": self._lsp_definition,
            "dev_references": self._lsp_references,
            "dev_callers": self._lsp_callers,
            "dev_callees": self._lsp_callees,
            "dev_symbol_impact": self._lsp_symbol_impact,
            "dev_rename_preview": self._lsp_rename_preview,
            "dev_diagnostics": self._lsp_diagnostics,
            "dev_hover": self._lsp_hover,
            "dev_document_symbols": self._lsp_document_symbols,
            "dev_search": self._search,
            "dev_file": self._file,
            "dev_symbol": self._symbol,
            "dev_outline": self._outline,
            "dev_ast": self._ast,
            "dev_edit": self._edit,
            "dev_tests": self._tests,
            "dev_seed": self._seed,
            "dev_rule": self._rule,
            "dev_node": self._node,
            "dev_neighbours": self._neighbours,
            "dev_graph_query": self._graph_query,
            "dev_stats": self._stats,
            "dev_changed": self._changed,
            "dev_record": self._record,
            "dev_session_start": self._session_start,
            "dev_session_record": self._session_record,
            "dev_session_state": self._session_state,
            "dev_session_next": self._session_next,
            "dev_session_finish": self._session_finish,
            "dev_session_list": self._session_list,
            "dev_recent": self._recent,
        }

    # -- tool implementations --------------------------------------------- #
    def _context(self, a: dict[str, Any]) -> Any:
        return self.mem.context(str(a["task"]),
                                max_items=int(a.get("max_items", 8)),
                                mode=str(a.get("mode", "auto")),
                                budget_tokens=int(a.get("budget_tokens", 6000)))

    def _brief(self, a: dict[str, Any]) -> Any:
        return self.mem.brief(a.get("task"),
                              budget_tokens=int(a.get("budget_tokens", 4000)),
                              write=bool(a.get("write", False)))

    def _repo_map(self, a: dict[str, Any]) -> Any:
        return self.mem.repo_map(str(a.get("task") or ""),
                                 budget_tokens=int(a.get("budget_tokens", 1500)),
                                 focus_files=a.get("focus_files"),
                                 force_refresh=bool(a.get("force_refresh", False)),
                                 scip_path=a.get("scip_path"))

    def _code_search(self, a: dict[str, Any]) -> Any:
        return self.mem.code_search(str(a["query"]),
                                    limit=int(a.get("limit", 20)),
                                    include_snippet=bool(a.get("include_snippet", True)))

    def _scip(self, a: dict[str, Any]) -> Any:
        return self.mem.scip(str(a["path"]),
                             summary_only=bool(a.get("summary_only", False)))

    def _architecture(self, a: dict[str, Any]) -> Any:
        return self.mem.architecture(top=int(a.get("top", 15)))

    def _impact(self, a: dict[str, Any]) -> Any:
        return self.mem.impact(str(a["file"]),
                               depth=int(a.get("depth", 2)),
                               scip_path=a.get("scip_path"))

    def _outline(self, a: dict[str, Any]) -> Any:
        return self.mem.outline_target(str(a["target"]))

    def _search(self, a: dict[str, Any]) -> Any:
        return {"query": a["text"],
                "results": self.mem.search(str(a["text"]),
                                           types=a.get("types"),
                                           limit=int(a.get("limit", 20)))}

    def _file(self, a: dict[str, Any]) -> Any:
        return self.mem.file(str(a["path"]))

    def _symbol(self, a: dict[str, Any]) -> Any:
        return self.mem.symbol(str(a["name"]))

    def _ast(self, a: dict[str, Any]) -> Any:
        return self.mem.ast(str(a["file"]), node=a.get("node"),
                            max_nodes=int(a.get("max_nodes", 200)))

    def _edit(self, a: dict[str, Any]) -> Any:
        script = {
            "file": a["file"],
            "ops": a["ops"],
            "apply": bool(a.get("apply", False)),
        }
        if a.get("base_sha256"):
            script["base_sha256"] = a["base_sha256"]
        if a.get("cst_graph") is not None:
            script["cst_graph"] = a["cst_graph"]
        return self.mem.edit(script, task=a.get("task"))

    def _tests(self, a: dict[str, Any]) -> Any:
        return self.mem.tests_for(str(a["target"]))

    def _seed(self, a: dict[str, Any]) -> Any:
        return self.mem.seed(str(a["seed_id"]))

    def _rule(self, a: dict[str, Any]) -> Any:
        return self.mem.rule(str(a["name"]))

    def _node(self, a: dict[str, Any]) -> Any:
        nid = int(a["id"])
        n = self.mem.node(nid)
        if n is None:
            return {"ok": False, "error": f"no node {nid}"}
        out: dict[str, Any] = {
            "ok": True, "node": self.mem.view(nid),
            "attrs": n.get("attrs", {}),
            "related": self.mem.related(nid),
        }
        if a.get("include_snippet", True):
            out["snippet"] = self.mem.snippet(nid)
        return out

    def _neighbours(self, a: dict[str, Any]) -> Any:
        nid = int(a["id"])
        if self.mem.node(nid) is None:
            return {"ok": False, "error": f"no node {nid}"}
        out: dict[str, Any] = {"ok": True, "node": self.mem.view(nid),
                               "neighbours": self.mem.related(nid)}
        edge = a.get("edge")
        if edge:
            out["filtered"] = {
                "out": [self.mem.view(int(e["tgt"])) for e in
                        self.mem._out.get(nid, []) if e["type"] == edge],
                "in": [self.mem.view(int(e["src"])) for e in
                       self.mem._in.get(nid, []) if e["type"] == edge],
            }
        return out

    def _graph_query(self, a: dict[str, Any]) -> Any:
        if bool(a.get("term")) == bool(a.get("match")):
            return {"ok": False,
                    "error": "pass exactly one of term= or match="}
        return self.mem.gi.graph_query(term=a.get("term"),
                                       match=a.get("match"))

    def _stats(self, _a: dict[str, Any]) -> Any:
        return self.mem.stats()

    def _changed(self, a: dict[str, Any]) -> Any:
        return self.mem.changed(include_all=bool(a.get("all", False)),
                                limit=int(a.get("limit", 200)))

    def _lsp_status(self, _a: dict[str, Any]) -> Any:
        return self.mem.lsp_status()

    def _lsp_definition(self, a: dict[str, Any]) -> Any:
        return self.mem.lsp_definition(str(a["file"]), int(a["line"]),
                                       int(a["character"]),
                                       language=a.get("language"))

    def _lsp_references(self, a: dict[str, Any]) -> Any:
        return self.mem.lsp_references(str(a["file"]), int(a["line"]),
                                       int(a["character"]),
                                       language=a.get("language"))

    def _lsp_callers(self, a: dict[str, Any]) -> Any:
        return self.mem.lsp_callers(str(a["file"]), int(a["line"]),
                                    int(a["character"]),
                                    language=a.get("language"))

    def _lsp_callees(self, a: dict[str, Any]) -> Any:
        return self.mem.lsp_callees(str(a["file"]), int(a["line"]),
                                    int(a["character"]),
                                    language=a.get("language"))

    def _lsp_symbol_impact(self, a: dict[str, Any]) -> Any:
        return self.mem.lsp_symbol_impact(str(a["file"]), int(a["line"]),
                                          int(a["character"]),
                                          language=a.get("language"))

    def _lsp_rename_preview(self, a: dict[str, Any]) -> Any:
        return self.mem.lsp_rename_preview(str(a["file"]), int(a["line"]),
                                           int(a["character"]),
                                           str(a["new_name"]),
                                           language=a.get("language"))

    def _lsp_diagnostics(self, a: dict[str, Any]) -> Any:
        return self.mem.lsp_diagnostics(str(a["file"]),
                                        language=a.get("language"))

    def _lsp_hover(self, a: dict[str, Any]) -> Any:
        return self.mem.lsp_hover(str(a["file"]), int(a["line"]),
                                  int(a["character"]),
                                  language=a.get("language"))

    def _lsp_document_symbols(self, a: dict[str, Any]) -> Any:
        return self.mem.lsp_document_symbols(str(a["file"]),
                                             language=a.get("language"))

    def _session_start(self, a: dict[str, Any]) -> Any:
        from scripts.ocelot_dev_session import DevSession
        sess = DevSession.start(str(a["task"]),
                                max_attempts=int(a.get("max_attempts", 3)),
                                root=self.mem.raw_repo_root)
        return {"ok": True, "state": sess.state(),
                "next": sess.next_action()}

    def _session_record(self, a: dict[str, Any]) -> Any:
        from scripts.ocelot_dev_session import load_session
        fields = a.get("fields") or {}
        if not isinstance(fields, dict):
            raise ValueError("fields must be an object")
        sess = load_session(str(a["session_id"]),
                            root=self.mem.raw_repo_root)
        node = sess.record(str(a["kind"]), **fields)
        return {"ok": True, "node": node, "next": sess.next_action()}

    def _session_state(self, a: dict[str, Any]) -> Any:
        from scripts.ocelot_dev_session import load_session
        sess = load_session(str(a["session_id"]),
                            root=self.mem.raw_repo_root)
        return {"ok": True, "state": sess.state(),
                "next": sess.next_action()}

    def _session_next(self, a: dict[str, Any]) -> Any:
        from scripts.ocelot_dev_session import load_session
        sess = load_session(str(a["session_id"]),
                            root=self.mem.raw_repo_root)
        return {"ok": True, "next": sess.next_action()}

    def _session_finish(self, a: dict[str, Any]) -> Any:
        from scripts.ocelot_dev_session import load_session
        sess = load_session(str(a["session_id"]),
                            root=self.mem.raw_repo_root)
        return {"ok": True, "state": sess.finish(str(a["outcome"]))}

    def _session_list(self, _a: dict[str, Any]) -> Any:
        from scripts.ocelot_dev_session import list_sessions
        return {"ok": True,
                "sessions": list_sessions(root=self.mem.raw_repo_root)}

    def _record(self, a: dict[str, Any]) -> Any:
        return {"ok": True, "entry": self.mem.journal_append(
            str(a.get("kind", "decision")), str(a["task"]),
            str(a["summary"]), files=a.get("files"),
            command=a.get("command"), exit_code=a.get("exit_code"))}

    def _recent(self, a: dict[str, Any]) -> Any:
        return {"ok": True, "entries": self.mem.journal_recent(int(a.get("n", 20)))}

    # -- JSON-RPC ---------------------------------------------------------- #
    def handle(self, msg: dict[str, Any]) -> dict[str, Any] | None:
        method = msg.get("method", "")
        msg_id = msg.get("id")
        params = msg.get("params") or {}
        if method == "initialize":
            return self._ok(msg_id, {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            })
        if method == "notifications/initialized":
            return None
        if method == "ping":
            return self._ok(msg_id, {})
        if method == "tools/list":
            return self._ok(msg_id, {"tools": _TOOLS})
        if method == "resources/list":
            return self._ok(msg_id, {"resources": [{
                "uri": "ocelot://brief",
                "name": "Ocelot repo brief",
                "description": "Compact repo layout, commands, docs, history and changes.",
                "mimeType": "text/markdown",
            }]})
        if method == "resources/templates/list":
            return self._ok(msg_id, {"resourceTemplates": []})
        if method == "resources/read":
            uri = str(params.get("uri", ""))
            if uri == "ocelot://brief":
                brief = self.mem.brief()
                return self._ok(msg_id, {"contents": [{
                    "uri": uri,
                    "mimeType": "text/markdown",
                    "text": brief["markdown"],
                }]})
            return self._err(msg_id, -32602, f"unknown resource {uri!r}")
        if method == "tools/call":
            name = str(params.get("name", ""))
            args = params.get("arguments") or {}
            handler = self._handlers.get(name)
            if handler is None:
                return self._err(msg_id, -32601, f"unknown tool {name!r}")
            try:
                result = handler(args)
                text = json.dumps(result, sort_keys=False)
                return self._ok(msg_id, {
                    "content": [{"type": "text", "text": text}],
                    "isError": False,
                })
            except Exception as e:  # noqa: BLE001 - surfaced to the client
                return self._ok(msg_id, {
                    "content": [{"type": "text",
                                 "text": f"{type(e).__name__}: {e}"}],
                    "isError": True,
                })
        return self._err(msg_id, -32601, f"method not found: {method}")

    @staticmethod
    def _ok(msg_id: Any, result: Any) -> dict[str, Any]:
        return {"jsonrpc": "2.0", "id": msg_id, "result": result}

    @staticmethod
    def _err(msg_id: Any, code: int, message: str) -> dict[str, Any]:
        return {"jsonrpc": "2.0", "id": msg_id,
                "error": {"code": code, "message": message}}


# --------------------------------------------------------------------------- #
# stdio transport (newline-delimited spec framing + LSP-style fallback)
# --------------------------------------------------------------------------- #
def _read_message(stream) -> tuple[dict[str, Any] | None, str]:
    line = stream.readline()
    if not line:
        return None, "newline"
    if line.lower().startswith(b"content-length:"):
        try:
            length = int(line.split(b":", 1)[1].strip())
        except ValueError:
            return None, "content-length"
        # consume headers until the blank line
        while True:
            h = stream.readline()
            if not h or h in (b"\r\n", b"\n"):
                break
        body = stream.read(length)
        return json.loads(body.decode("utf-8")), "content-length"
    text = line.decode("utf-8", errors="replace").strip()
    if not text:
        return None, "newline"
    return json.loads(text), "newline"


def _write_message(stream, msg: dict[str, Any], framing: str) -> None:
    body = json.dumps(msg, ensure_ascii=False).encode("utf-8")
    if framing == "content-length":
        stream.write(f"Content-Length: {len(body)}\r\n\r\n".encode())
        stream.write(body)
    else:
        stream.write(body + b"\n")
    stream.flush()


def serve(server: DevMemoryServer) -> int:
    inp = sys.stdin.buffer
    out = sys.stdout.buffer
    framing = "newline"
    while True:
        try:
            msg, framing = _read_message(inp)
        except (json.JSONDecodeError, ValueError) as e:
            print(f"[{SERVER_NAME}] bad message: {e}", file=sys.stderr)
            continue
        if msg is None:
            break
        if "id" not in msg:
            # notification: handle, never reply
            server.handle(msg)
            continue
        response = server.handle(msg)
        if response is not None:
            _write_message(out, response, framing)
    return 0


def _load_memory(args: argparse.Namespace) -> DevMemory:
    dump = Path(args.dump)
    if not dump.exists():
        if args.autobuild or os.environ.get("OCELOT_DEV_AUTOBUILD") == "1":
            print(f"[{SERVER_NAME}] building {dump} ...", file=sys.stderr)
            build_index(args.root, dump, include_docs="features",
                        include_git=True, include_scripts=True)
        else:
            raise SystemExit(
                f"no dev-memory snapshot at {dump}; run "
                f"`python -m scripts.ocelot_dev_memory build` first "
                f"(or pass --autobuild)")
    return DevMemory(dump, Path(args.journal))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--dump", default=os.environ.get("OCELOT_DEV_DUMP",
                                                    str(DEFAULT_DUMP)))
    p.add_argument("--journal", default=os.environ.get("OCELOT_DEV_JOURNAL",
                                                       str(DEFAULT_JOURNAL)))
    p.add_argument("--root", default=str(Path(__file__).resolve().parent.parent))
    p.add_argument("--autobuild", action="store_true")
    args = p.parse_args(argv)
    mem = _load_memory(args)
    try:
        return serve(DevMemoryServer(mem))
    finally:
        try:
            from scripts.ocelot_lsp import close_all
            close_all()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())
