# Graph/tree coding-agent landscape — comparison and adopted features

**Date:** 2026-11-14. **Scope:** graph- and tree-based code retrieval,
navigation, editing and orchestration for LLM coding agents. The goal is not a
literature review; it is a gap analysis against the Ocelot dev-memory/edit
layer, with the features we can actually adopt.

> Claims below are the sources' own reported results, not independent
> reproductions. Where a number is vendor-reported it is marked **(vendor)**.

## The landscape in one table

| System / project | Core mechanism | Graph granularity | How the agent uses it | Reported result |
|---|---|---|---|---|
| **Aider repo map** ([docs](https://aider.chat/docs/repomap.html), [design](https://aider.chat/2023/10/22/repomap.html)) | tree-sitter `tags.scm` defs/refs; file graph; personalized PageRank; token budget (~1k default) | file + symbol | repo map injected into every prompt; model asks for files by path | Widely used; no controlled benchmark in the post |
| **RepoGraph** ([ICLR 2025](https://proceedings.iclr.cc/paper_files/paper/2025/file/4a4a3c197deac042461c677219efd36c-Paper-Conference.pdf)) | line-level def/ref graph; ego-graph retrieval | line | plug-in context for agent/procedural frameworks | **+32.8% relative** SWE-bench success (paper) |
| **CodexGraph** ([NAACL 2025](https://aclanthology.org/2025.naacl-long.7.pdf)) | static-analysis symbol graph (MODULE/CLASS/FUNCTION; CONTAINS/INHERITS/USES); LLM writes graph queries | symbol | agent queries a graph DB (Cypher) to navigate | Competitive on CrossCodeEval/SWE-bench/EvoCodeBench |
| **GraphCoder** ([ASE 2024](https://www.computer.org/csdl/proceedings-article/ase/2024/124800a570/22gEw1E3YfC)) | code context graph (control/data dependence); coarse-to-fine retrieval | statement | retrieval for repo-level completion | **+6.06 EM** code match (paper) |
| **LocAgent** ([ACL 2025](https://aclanthology.org/2025.acl-long.426.pdf)) | directed heterogeneous graph; multi-hop localization tools | file/class/function | LLM agent localizes code via graph search | up to **92.7%** file-level localization (paper) |
| **CrossCoder** ([EMNLP 2026](https://aclanthology.org/2026.findings-emnlp.433.pdf)) | unified graph over repo + external library entities; planning + multi-hop expansion | entity/repo | retrieval for generation with dependency versions | up to **+6.3% pass@1** (paper) |
| **Codebase-Memory** ([arXiv 2603.27277](https://arxiv.org/abs/2603.27277)) | tree-sitter knowledge graph via MCP; 66 languages; call graph, impact, community detection | file/symbol/call | MCP tools for code exploration | **83%** answer quality vs 92% file-exploration, **10× fewer tokens**, **2.1× fewer tool calls** (paper) |
| **arbor** ([GitHub](https://github.com/nikita-voronoy/arbor)) | tree-sitter symbol graph; 14 MCP tools; content-hash incremental | symbol | boot/skeleton/compact maps, callers, impact, search | 1M LOC → ~500 lines context; sub-second reindex (vendor) |
| **context-link** ([GitHub](https://github.com/context-link-mcp/context-link)) | language-agnostic tree-sitter; semantic scout + structural extraction + memory notes | symbol | MCP context gateway | token reduction (vendor) |
| **ckg** ([GitHub](https://github.com/ajankurjain/central-code-knowledge-graph)) | multi-repo Neo4j property graph; incremental ingest; optional LSP pass | file/class/function | REST/GraphQL/MCP; architecture maps | multi-repo model (vendor) |
| **Sourcegraph + SCIP** ([docs](https://sourcegraph.com/docs/code-navigation/precise-code-navigation), [SCIP](https://sourcegraph.com/blog/announcing-scip)) | compiler-accurate index (SCIP) for definitions/references, cross-repo | symbol (precise) | MCP server; code search, navigation, diffs | **+0.259 reward** on 400K–2M LOC, **30% cheaper / 38% faster** agents (vendor) |
| **Cursor indexing** ([design](https://cursor.com/blog/secure-codebase-indexing)) | Merkle tree sync; AST chunks ~500 tokens; embeddings; hybrid semantic + regex | chunk | codebase search/context | **+12.5%** answer accuracy from semantic search (vendor) |
| **LSP bridges** (Claude Code plugins, [mcpls](https://github.com/bug-ops/mcpls), [structural-lsp](https://github.com/jbr/structural-lsp)) | language servers: diagnostics, definition, references, rename, call hierarchy | symbol (compiler-grade) | MCP/LSP tools; diagnostics after every edit | IDE-grade navigation inside agents (vendor) |
| **CodeRAG-Bench** ([paper](https://arxiv.org/abs/2406.14497)) | benchmark of retrievers/generators; repo-level tasks | chunk | evaluates RAG for code | retrieval helps, but retrievers often miss; 200–800-token chunks best |
| **DyRetriever** ([arXiv 2608.01927](https://arxiv.org/html/2608.01927)) | on-demand partial dependency graph; LLM multi-hop validation | function | retrieval for repo generation | **+25.63% / +59.73%** Pass@1 on CoderEval/DevEval; 7.4× faster than static graphs (paper) |

## What Ocelot already has

| Capability | Where |
|---|---|
| Typed graph memory; typed edges; CoW branches | `runners/dsl/`, `scripts/ocelot_dev_memory.py` |
| Repo snapshot: files, symbols, tests, seeds, rules, docs, git, failures | `scripts/ocelot_dev_memory.py` |
| Lossless Python CST (token + trivia) | `domains/py_cst_ingest.py`, `scripts/ocelot_lossless.py` |
| Lossless Rust/Lua `CstNode` (tree-sitter; now with trivia) | `domains/ts_ingest.py`, `scripts/ocelot_cst_edit.py` |
| Semantic AST-node + symbol edit ops; diff only a view | `scripts/ocelot_code_edit.py` |
| Hub-IR-authored replacements rendered by graph rules | `scripts/ocelot_ir_edit.py`, `domains/render_python.py` |
| Markdown section and JSON path edits | `scripts/ocelot_markdown_edit.py`, `scripts/ocelot_json_edit.py` |
| Replayable dev-session graph (LangGraph-like) | `scripts/ocelot_dev_session.py` |
| MCP tools, CLI, journal receipts | `scripts/ocelot_dev_memory_mcp.py` |

## What was adopted from the landscape (landed 2026-11-14)

1. **Tree-sitter tags + ranked repo map** — `scripts/ocelot_repo_map.py`.
   - Python tags use the stdlib AST fast path; Rust/Lua use the grammar's own
     `queries/tags.scm`.
   - File graph `referencer -> definer`; personalized PageRank; task terms are
     inverse-frequency weighted; tests are down-weighted; task-named seeds/
     files from the dev graph become focus files.
   - Three-tier token-budgeted render: full outlines for hot files, public
     symbols for the middle, listing for the tail.
   - MCP: `dev_repo_map`; CLI: `repo-map`.
2. **Impact/dependent queries** — `dev_impact` / `impact`.
   - Reverse reference graph, transitive dependents, direct dependencies.
   - This is the file-level version of arbor/codegraph `impact` and
     Codebase-Memory's blast radius.
3. **Content-hash incremental tag cache** — `update_tag_cache`.
   - `mtime+size` fast path; content hash on change; a Merkle-like root hash
     over the file set; only changed files re-parsed.
   - This is the Cursor/arbor sync idea without embeddings or a server.
4. **Tree-sitter lossless CST fix** — `domains/ts_ingest.py`.
   - Added opt-in explicit `trivia` leaves so `flat_text` is byte-for-byte the
     source; the existing correspondence walkers keep their old child indices
     by default.
5. **MCP/CLI surface** — `dev_repo_map`, `dev_impact`; `repo-map`, `impact`.

## Gap analysis: what the leaders have that we do not

| Gap | Best source | Why it matters | Effort |
|---|---|---|---|
| **Compiler-accurate definitions/references** | Sourcegraph SCIP, LSP bridges | tree-sitter is syntactic; same-named symbols and dynamic dispatch produce false edges | medium: LSP client + pyright/rust-analyzer |
| **Diagnostics after edits** | Claude Code LSP, mcpls | catches type/import errors without running a build | medium: LSP client + diagnostics pass |
| **Symbol-level call graph** | Codebase-Memory, arbor, codegraph | file-level impact is too coarse for a safe refactor | medium: LSP call hierarchy or tree-sitter resolution |
| **Cross-repo / external library graph** | CrossCoder, Sourcegraph | version-specific API usage is a real failure mode | high: dependency graph + library signatures |
| **Semantic/vector hybrid search** | Cursor, CodeRAG-Bench | finds conceptually related code that grep/graph misses | medium: embed chunks; local model optional |
| **Merkle directory tree + shared index reuse** | Cursor | multi-user/multi-machine index sync and fast cold start | high: server/state layer |
| **Multi-language breadth** | tree-sitter, Codebase-Memory | current tags: Python/Rust/Lua; repo has more | low–medium: add grammars + tags.scm |
| **Community/architecture summaries** | Codebase-Memory, ckg | cycles, hubs, coupling, god modules | medium: graph metrics + `dev_brief` section |
| **Agentic graph query language** | CodexGraph | raw DSL is powerful but not a compact navigation API | low: `dev_code_query` (callers/callees/path/impact) |
| **Semantic edit algebra at IR grain** | Ocelot (unique) | we already have it; leaders mostly use text edits | maintain and measure |
| **Lossless CST editing** | Ocelot (unique) | byte-preserving comments/trivia; diff only a view | maintain |
| **Dev-session graph** | LangGraph-like; leaders mostly transcripts | replayable state, retries, human gates | measure |

## What to implement next, in priority order

**P0 — LSP bridge (largest accuracy gain).**
- `scripts/ocelot_lsp.py`: stdio JSON-RPC client for pyright/pylsp and
  rust-analyzer; start one server per language, reuse across calls.
- MCP tools: `dev_definition`, `dev_references`, `dev_diagnostics`,
  `dev_call_hierarchy`, `dev_rename` (preview/apply through the existing edit
  transaction).
- Fallback honestly when the server is absent (tree-sitter tags / `rg`).
- Adoption source: Claude Code code-intelligence plugins, mcpls, structural-lsp.

**P0 — Symbol-level impact.**
- Use LSP `textDocument/references` / `callHierarchy` to replace the current
  file-level reference edges with resolved symbol edges.
- Keep the tree-sitter graph as the fast/fallback path.

**P1 — Evaluate the repo map.**
- Same task, same model, four arms: no map, `dev_context`, `dev_repo_map`,
  `dev_context + dev_repo_map`.
- Metrics: task success, regressions, input tokens, tool calls, latency.
- This is the only honest way to claim the map helps; Aider/RepoGraph numbers
  do not transfer automatically.

**P1 — SCIP import.**
- Ingest a `.scip` index when present; map symbols to `Symbol` nodes and
  references to edges; this gives compiler-accurate cross-repo navigation
  without running a language server per query.
- Adoption source: Sourcegraph SCIP.

**P2 — Hybrid semantic search (optional).**
- Chunk on AST/CST boundaries (~200–800 tokens); embed with a local model;
  combine with graph rank via reciprocal rank fusion.
- Cursor reports +12.5% answer accuracy from semantic search; CodeRAG-Bench
  shows retrieval helps but is hard. Keep it optional and measured.

**P2 — Multi-language tags.**
- Add grammars/tags for TypeScript/Go/Java/C/C++ and let `ocelot_repo_map`
  pick them up. The generic tag-cache/graph code already supports it.

**P3 — Architecture summaries.**
- Cycles, hub symbols, coupling, dead-code candidates in `dev_brief`.
- Adoption source: ckg, Codebase-Memory, arbor.

**P3 — Merkle directory tree / shared index reuse.**
- The current cache has a content-hash root; add per-directory hashes and a
  simhash for cross-checkout reuse. Only needed if indexing moves off-box.

## What not to copy

- **Embedding-only retrieval as the primary context.** Cursor/CodeRAG show it
  helps, but it is weaker than graph navigation for “who calls this / what
  breaks if I change it”.
- **A separate database service** (Neo4j/Postgres) for a single-checkout dev
  agent. Our snapshot + cache is sufficient; add a server only for multi-repo.
- **Full file dumps as context.** The repo map + `dev_context` + outlines are
  cheaper and more structured.
- **Text-patch editing.** Keep the op-list/canonical transaction; diffs remain
  a view.

## Honest limits of the new repo map

- Python references are AST name/attribute uses, not scope-resolved; Rust/Lua
  references come from grammar tags, not rust-analyzer. Cross-file edges are
  heuristic and capped (generic identifiers and high-fan-out names are
  skipped) to avoid a 15M-edge explosion.
- The tag cache is content-hash incremental, but the first full index is still
  ~1 minute on this tree; subsequent calls are seconds.
- The map is task-weighted but not evaluated against a baseline yet.
- The reference graph is file-level; symbol-level impact needs LSP/SCIP.
- No external library graph yet.

## Sources

- Aider repo map: <https://aider.chat/docs/repomap.html>,
  <https://aider.chat/2023/10/22/repomap.html>
- RepoGraph: <https://proceedings.iclr.cc/paper_files/paper/2025/file/4a4a3c197deac042461c677219efd36c-Paper-Conference.pdf>
- CodexGraph: <https://aclanthology.org/2025.naacl-long.7.pdf>
- GraphCoder: <https://www.computer.org/csdl/proceedings-article/ase/2024/124800a570/22gEw1E3YfC>
- LocAgent: <https://aclanthology.org/2025.acl-long.426.pdf>
- CrossCoder: <https://aclanthology.org/2026.findings-emnlp.433.pdf>
- Codebase-Memory: <https://arxiv.org/abs/2603.27277>
- CodeRAG-Bench: <https://arxiv.org/abs/2406.14497>
- DyRetriever: <https://arxiv.org/html/2608.01927>
- Sourcegraph SCIP: <https://sourcegraph.com/docs/code-navigation/precise-code-navigation>,
  <https://sourcegraph.com/blog/announcing-scip>
- Cursor indexing: <https://cursor.com/blog/secure-codebase-indexing>
- Cursor semantic search: <https://cursor.com/en-US/blog/semsearch>
- Claude Code LSP plugins: <https://code.claude.com/docs/en/plugins/code-intelligence>
- mcpls: <https://github.com/bug-ops/mcpls>
- structural-lsp: <https://github.com/jbr/structural-lsp>
- arbor: <https://github.com/nikita-voronoy/arbor>
- context-link: <https://github.com/context-link-mcp/context-link>
- ckg: <https://github.com/ajankurjain/central-code-knowledge-graph>
