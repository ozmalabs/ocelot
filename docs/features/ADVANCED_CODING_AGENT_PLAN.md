# Advanced coding-agent layer — execution plan (2026-11-14)

**Status: LANDED (2026-11-14).** All six wave-2 workstreams are implemented
and integrated. Combined scoped gate: **191 passed, 6 skipped** (2 live LSP
tests, 3 upstream tag-query gaps, 1 synthetic-fallback control).

| Workstream | Landed | Evidence |
|---|---|---|
| A — LSP bridge | `scripts/ocelot_lsp.py` | 14 passed, 2 skipped; live pyright 15 passed, 1 skipped |
| B — repo-map eval | `scripts/ocelot_repo_map_eval.py` + `evaluation/repo_map/` | 7 passed; 21-task real run |
| C — SCIP import | `scripts/ocelot_scip_import.py` | 8 passed |
| D — multi-language tags | `scripts/ocelot_tag_languages.py` | 37 passed, 3 skipped |
| E — architecture | `scripts/ocelot_architecture.py` | 14 passed |
| F — lexical hybrid search | `scripts/ocelot_code_search.py` | 7 passed |
| Integration | MCP/CLI/docs | combined 191 passed |

Live LSP smoke: pyright definition, references, symbol impact, callers and
rename preview all returned correctly on a two-function file.
`rust-analyzer` is present as a rustup shim but its component is missing, so
the Rust live test skips honestly. `typescript-language-server` is absent.
Embeddings and a shared multi-user Merkle index remain deferred.

**Goal.** Execute the P0/P1/P2/P3 steps from
[`GRAPH_CODING_LANDSCAPE.md`](GRAPH_CODING_LANDSCAPE.md):

1. compiler-accurate code intelligence (LSP);
2. symbol-level impact;
3. repo-map evaluation;
4. SCIP ingestion;
5. multi-language tags;
6. architecture summaries;
7. a lexical hybrid code search (the no-embedding half of hybrid retrieval).

Embeddings and a multi-user Merkle index server are deliberately deferred;
both need a model/server and are not prerequisites for better local context.

**Environment.** `tree-sitter` 0.26.1 and grammars for Python/Rust/Lua/
TypeScript/Go/Java/C/C++ are installed; `pyright` is in `.venv/bin`;
`rust-analyzer` and `clangd` are on PATH.

## Shared rules

- Dev tooling, not agent runtime. No changes under `runners/dsl/` or seeds.
- Canonical edits stay semantic op lists; diffs are views.
- Preview by default; no silent writes.
- Scoped tests only. `.venv/bin/python -m pytest tests/test_<x>_migrated.py -q`.
- Do not edit shared integration files:
  `scripts/ocelot_repo_map.py`, `scripts/ocelot_dev_memory.py`,
  `scripts/ocelot_dev_memory_mcp.py`, `docs/features/DEV_MEMORY_MCP.md`,
  `docs/CODE_MAP.md`, `requirements-dev.txt`, `.opencode/`.
  The central integrator wires the modules.
- Do not commit. Report exact tests, APIs, dependencies and limitations.

## Workstream A — LSP bridge + symbol impact

**Owns:** `scripts/ocelot_lsp.py`, `tests/test_lsp_migrated.py`,
`docs/features/LSP_BRIDGE.md`.

**API:** `LSPClient(root, language, command=None)`, `definition`,
`references`, `document_symbols`, `hover`, `diagnostics`,
`prepare_call_hierarchy`, `incoming_calls`, `outgoing_calls`,
`rename_preview`, `symbol_impact`, `server_status`.

- stdio JSON-RPC 2.0 with Content-Length framing; one server per language,
  lazy start, explicit close.
- Registry: Python `pyright-langserver --stdio` (fallback `pylsp`), Rust
  `rust-analyzer`, C/C++ `clangd`, TypeScript `typescript-language-server`.
- `initialize` with root URI + capabilities; `textDocument/didOpen` before
  requests.
- Diagnostics cache from `textDocument/publishDiagnostics`.
- Honest refusal when a server binary is absent.
- Tests: fake stdio LSP server (subprocess) for initialize/definition/
  references/diagnostics/call hierarchy; symbol impact groups references by
  file; rename preview does not write. Live rust-analyzer test optional/skip.

## Workstream B — repo-map evaluation

**Owns:** `scripts/ocelot_repo_map_eval.py`,
`tests/test_repo_map_eval_migrated.py`, `docs/features/REPO_MAP_EVAL.md`,
`evaluation/repo_map/tasks.json`.

- Build a small reproducible task set from repo facts (seeds/rules/files) with
  expected files. Ground truth must be explicit in the JSON, not inferred at
  eval time.
- Arms: no-map baseline file listing, `dev_context` file set, `dev_repo_map`
  file set, both. Budgets 500/900/1500 tokens.
- Metrics: file recall@budget, precision, tokens, selected files, latency.
- Output JSON + markdown; deterministic.
- Tests on a fixture graph; no network, no LLM.

## Workstream C — SCIP ingestion

**Owns:** `scripts/ocelot_scip_import.py`,
`tests/test_scip_import_migrated.py`, `docs/features/SCIP_IMPORT.md`.

- Support a documented **SCIP JSON export** first (documents, occurrences,
  symbols, roles, ranges); convert to normalized symbol/reference records and
  repo-map-compatible edges.
- Optional `.scip` protobuf path only when `scip_pb2` is importable; otherwise
  refuse honestly (no protobuf dependency installed).
- Path normalization, dedup, role filtering (definition/reference), symbol
  parsing; tests with a JSON fixture and a synthetic graph/report.

## Workstream D — multi-language tags

**Owns:** `scripts/ocelot_tag_languages.py`,
`tests/test_tag_languages_migrated.py`, `docs/features/TAG_LANGUAGES.md`.

- Registry for Python/Rust/Lua/TypeScript/TSX/JavaScript/Go/Java/C/C++.
- Use each grammar's `queries/tags.scm`; extract definitions/references.
- Python may stay on the AST fast path; the registry must expose a uniform
  `extract_tags(path, source)`.
- Tests for each installed grammar; skip missing grammars honestly.
- No edits to `ocelot_repo_map.py`; the integrator merges the registry.

## Workstream E — architecture summaries

**Owns:** `scripts/ocelot_architecture.py`,
`tests/test_architecture_migrated.py`,
`docs/features/ARCHITECTURE_SUMMARIES.md`.

- Build on `ocelot_repo_map.update_tag_cache` + `build_reference_graph`.
- Report: top hubs (in-degree/PageRank), cycles (Tarjan SCC), coupling
  (in/out degree), module boundaries (top-level dirs), dead-code candidates
  (no inbound references), test-to-source ratio.
- JSON + markdown; deterministic; tests with a fixture cycle/hub.
- Honest limits: syntactic, file-level, no external libraries.

## Workstream F — lexical hybrid code search

**Owns:** `scripts/ocelot_code_search.py`,
`tests/test_code_search_migrated.py`,
`docs/features/CODE_SEARCH.md`.

- No embeddings/deps: BM25 over symbol names, file paths, and source lines;
  fuse with repo-map PageRank via reciprocal rank fusion.
- `code_search(root, query, limit=20)` returns ranked files/symbols + snippets.
- Tests: fixture query hits a symbol/doc comment; fusion ordering; empty query;
  deterministic.
- This is the lexical half of hybrid retrieval; embeddings are deferred.

## Integration (central, after agents)

1. Wire LSP, SCIP, search, architecture into `ocelot_dev_memory.py` wrappers,
   MCP tools (`dev_definition`, `dev_references`, `dev_diagnostics`,
   `dev_callers`, `dev_callees`, `dev_rename_preview`, `dev_scip`,
   `dev_code_search`, `dev_architecture`) and CLI verbs.
2. Merge `ocelot_tag_languages` into `ocelot_repo_map` (keep Python AST).
3. Update `requirements-dev.txt` with installed grammars/pyright.
4. Rebuild the snapshot/tag cache; restart MCP; run the combined scoped gate.
5. Record verification + decision in the dev journal.

## Risks

- LSP servers are slow/cold-start and may need project config; keep timeouts
  and honest refusal.
- Fake-server tests prove protocol correctness, not server compatibility; live
  rust-analyzer/pyright is a separate smoke test.
- SCIP protobuf is not available; JSON export is the supported path now.
- Repo-map eval ground truth is manual/fixture-based; it is a retrieval
  instrument, not an end-to-end coding benchmark.
- Multi-language tags are syntactic; LSP/SCIP remains the precise layer.
