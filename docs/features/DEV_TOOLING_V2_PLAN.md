# Dev tooling v2 — hardening, faster/precise navigation, honest evaluation

**Date:** 2026-11-14. **Base:** `7afb2318` (graph-native coding-agent layer).
**Integration branch:** `dt/v2` (worktree `.worktrees/dt-v2`).
**Scope:** dev tooling under `scripts/`, `evaluation/`, `docs/features/`,
`tests/test_*_migrated.py`. Nothing here is agent runtime: no changes under
`runners/dsl/`, `seeds/`, `substrate/` or `domains/` (except where a task
names `domains/ts_ingest.py` / `domains/py_cst_ingest.py` explicitly).

This plan executes the review of `7afb2318` and closes the gap against the
retrieval/navigation leaders (Serena, codebase-memory-mcp, Claude Code LSP
plugins, Sourcegraph MCP, Aider repo map).

## Findings being fixed (IDs used by the task briefs)

### Edit layer
- **E1** Python/JSON/Markdown adapters read with `read_text` → CRLF becomes LF
  on write; `base_sha256` is over newline-translated text (IR/CST hash bytes).
- **E2** IR adapter splices LF text into CRLF files (mixed endings).
- **E3** AST nodes without `lineno` (operators, `ctx`, `comprehension`,
  `arguments`, `alias`, `keyword` without location) get span 0:0.
- **E4** Statement ops (`delete_node`, `insert_*_node`, `wrap_node`) are
  whole-line and damage other statements on the same line (`a = 1; b = 2`).
- **E5** `replace_body` on a one-line def (`def f(self): return 1`) destroys
  the def header.
- **E6** `wrap_node` re-indents multi-line string contents.
- **E7** Same-offset inserts land in reverse op order (JSON merge, Markdown
  append, multiple `insert_import`).
- **E8** Python `replace_span` always appends a newline.
- **E9** `insert_import` dedups by substring and inserts above shebang /
  encoding line.
- **E10** `rename_symbol` renames every NAME token with that name in the
  file, across unrelated classes, silently.
- **E11** Transaction drift: fixed tmp name, no fsync, one-second backup
  names collide, no re-check of the file between read and replace (TOCTOU),
  backup copied after the read; five copy-pasted write blocks.
- **E12** BOM / non-UTF-8 files raise bare `SyntaxError`/`UnicodeDecodeError`.
- **E13** CST adapter writes without syntax validation when tree-sitter is
  unavailable; stale "no tree_sitter" docstring.

### MCP / integration
- **M1** A blank stdin line ends the MCP server (`_read_message` → `None`).
- **M2** Batches, bare strings, non-object `params`, and exceptions in
  `resources/read` crash the server; parse errors get no -32700 reply.
- **M3** `bool("false") is True`: `apply`, `write`, `force_refresh`,
  `include_snippet`, `all` accept strings.
- **M4** Every tool uses the snapshot's baked-in `Repo.attrs.root`, not the
  process root; in a worktree, `dev_edit apply` writes the main checkout.
- **M5** LSP `_path` accepts absolute/`../` paths and sends file content to the
  server; `scip_path` in repo_map/impact is not contained.
- **M6** LSP `_ensure_open` holds `_state_lock` across a blocking pipe write
  that the reader thread needs the same lock to drain (deadlock risk).
- **M7** Snapshot staleness is never detected (snapshot head `5e401a11` vs
  HEAD `7afb2318`); `_text_cache` never invalidated after edits.
- **M8** Unknown tool returns -32601 (MCP uses -32602 for invalid params);
  `additionalProperties:false` never enforced.

### Retrieval / cache
- **R1** Tag-cache fast path uses whole-second `int(st_mtime)` + size: a
  same-second same-size edit serves stale tags.
- **R2** No extractor/grammar fingerprint in the cache; backend failures are
  cached as `[]` forever.
- **R3** Repo map is not deterministic across processes: edges are built by
  iterating a `set` and truncated at `MAX_EDGES`/300 candidates.
- **R4** Subset calls (`files=[...]`) prune the shared cache down to the
  subset (observed: `var/ocelot_dev_tags.json` is 2 KB on main right now).
- **R5** mtime refreshes on a sha match are never saved.
- **R6** Personalized PageRank leaks mass at dangling nodes, fixed 30
  iterations, no tolerance.
- **R7** code_search RRF gives the query-independent PageRank prior the same
  weight as BM25, so hubs override relevance; ties get distinct ranks.
- **R8** Every repo_map call reloads the whole JSON cache, rebuilds the graph,
  runs `_task_relevance` twice; ~6 s warm, ~60 s cold.
- **R9** Duplicate `_python_tags` in `ocelot_repo_map.py` and
  `ocelot_tag_languages.py`.

### Evaluation
- **V1** 13/21 task prompts name an expected file's stem.
- **V2** 8/21 tasks are about the dev tooling itself.
- **V3** dev_context arm ran on a stale snapshot without the new files.
- **V4** Baseline is a sorted path listing; `code_search` was never an arm.
- **V5** Listing-tier path lines count as hits; tier is ignored in scoring.
- **V6** Retrieval-only; no end-to-end task-success comparison.

## Competitive gap being closed

| Leader | What they have | v2 answer |
|---|---|---|
| codebase-memory-mcp | persistent graph, sub-ms queries, call graph, impact | warm in-process index + graph memo, parallel cold index, symbol-level call graph and impact (W1-C, W2-B, W2-C) |
| Serena | LSP-precise symbol targets and symbol edits | scope-aware symbols + import-aware resolution; optional LSP refinement of callers/impact (W2-C, W3-B) |
| Claude Code LSP plugins | diagnostics after every edit, no extra tool call | `dev_edit apply` returns versioned post-edit diagnostics when a server is available (W3-B) |
| Aider repo map | deterministic, cached, task-personalised | determinism + correct PPR + cache correctness (W1-C) |
| Studies (arXiv 2611.07286, 2610.33958) | retrieval gains often do not move task success | leakage-free eval with fair baselines + an end-to-end harness (W3-A, W3-C) |

Deliberately still out of scope: embeddings, multi-repo/cross-service graph,
a database server.

## Performance targets (measured on this tree, warm = second call in-process)

| Operation | Now | Target |
|---|---|---|
| `repo_map` warm | ~6.3 s | ≤ 1.0 s |
| `code_search` warm | n/a (PageRank per query) | ≤ 0.5 s |
| `impact` warm | ~6 s | ≤ 0.3 s |
| symbol callers/impact warm | n/a | ≤ 0.3 s |
| cold full index (4 workers) | ~60 s | ≤ 30 s |

## Waves, tasks and write scopes

Each task runs in its own worktree on its own branch cut from `dt/v2`, by the
`ocelot-substrate-executor` agent. Write scopes inside a wave are disjoint.
The supervisor merges each wave into `dt/v2`, runs the combined gate, then
cuts the next wave.

Shared rules for every task:
- Dev tooling, not agent runtime: CLAUDE.md's runtime rules about Python
  decisions, integer frames and scalar knobs do not apply to these modules.
  The constants named in a design are specified, not invented.
- Preview by default; no silent writes. No new third-party dependencies
  (stdlib + already-installed tree-sitter/pyright only).
- Python: `/applications/data/projects/ocelot/.venv/bin/python`. Tests:
  `COLUMNS=250 <py> -m pytest -q -p no:cacheprovider --confcutdir=<wt> <files>`.
- Never commit; never touch files outside the write scope.

### Wave 1 — correctness (parallel)

**W1-A Edit transaction core** — fixes E1, E2, E11, E12, E13 (I/O half).
Scope: new `scripts/ocelot_edit_txn.py`; the read/write/hash/backup parts of
`scripts/ocelot_code_edit.py` (`apply_edit_script` only), `ocelot_json_edit.py`,
`ocelot_markdown_edit.py`, `ocelot_cst_edit.py`, `ocelot_ir_edit.py`
(`_load_python_file`, `_write_atomic`, `_plan_body`/`_plan_function` newline
only); new `tests/test_edit_txn_migrated.py`; additive tests in
`test_json_edit_migrated.py`, `test_markdown_edit_migrated.py`,
`test_ir_edit_migrated.py`, `test_cst_edit_migrated.py`.

**W1-B MCP and LSP hardening** — fixes M1–M8.
Scope: `scripts/ocelot_dev_memory_mcp.py`, `scripts/ocelot_lsp.py`, the
`DevMemory` root/staleness/bool/scip parts of `scripts/ocelot_dev_memory.py`;
new `tests/test_dev_memory_mcp_migrated.py`; additive tests in
`test_lsp_migrated.py`, `test_dev_memory_migrated.py`.

**W1-C Index correctness and determinism** — fixes R1–R6, R9.
Scope: `scripts/ocelot_repo_map.py`, `scripts/ocelot_tag_languages.py`,
`scripts/ocelot_architecture.py` (only to stop its subset call pruning),
`tests/test_repo_map_migrated.py`, `tests/test_tag_languages_migrated.py`.

### Wave 2 — precise and fast navigation (parallel)

**W2-A Python op semantics** — fixes E3–E10.
Scope: `_apply_ops` and helpers in `scripts/ocelot_code_edit.py`,
`scripts/ocelot_lossless.py`, `tests/test_code_edit_migrated.py`.

**W2-B Warm index and fused search** — fixes R7, R8.
Scope: `scripts/ocelot_repo_map.py`, `scripts/ocelot_code_search.py`,
`tests/test_repo_map_migrated.py`, `tests/test_code_search_migrated.py`, new
`scripts/ocelot_index_bench.py`.

**W2-C Symbol graph** — symbol-level defs/refs with enclosing scope,
import-aware resolution, callers/callees/impact.
Scope: `scripts/ocelot_tag_languages.py`, new `scripts/ocelot_symbol_graph.py`,
new `tests/test_symbol_graph_migrated.py`, additive tests in
`test_tag_languages_migrated.py`, new `docs/features/SYMBOL_GRAPH.md`.

### Wave 3 — integration and evaluation (parallel)

**W3-A Evaluation v2** — fixes V1–V5.
Scope: `scripts/ocelot_repo_map_eval.py`, new `evaluation/repo_map/tasks_v2.json`,
`evaluation/repo_map/RESULTS_V2.md`, `docs/features/REPO_MAP_EVAL.md`,
`tests/test_repo_map_eval_migrated.py`.

**W3-B Navigation and diagnostics wiring** — symbol tools + post-edit
diagnostics + optional LSP refinement in MCP/CLI.
Scope: `scripts/ocelot_dev_memory.py`, `scripts/ocelot_dev_memory_mcp.py`,
`docs/features/DEV_MEMORY_MCP.md`, `docs/CODE_MAP.md`,
`tests/test_dev_memory_migrated.py`, `tests/test_dev_memory_mcp_migrated.py`.

**W3-C End-to-end harness** — fixes V6 (harness only).
Scope: new `scripts/ocelot_agent_eval.py`, new `evaluation/agent_e2e/`, new
`tests/test_agent_eval_migrated.py`, new `docs/features/AGENT_E2E_EVAL.md`.
A live run spends hosted-model tokens and needs explicit user approval; the
task ships the harness, a fake driver and a dry run only.

### Wave 4 — supervisor
Merge, combined gate, refresh the snapshot, run eval v2 for real, run the
performance bench, semantic review of `7afb2318..dt/v2`, fix review blockers,
update `GRAPH_CODING_LANDSCAPE.md` status and record results here.

## Status (2026-11-15)

| Task | State | Evidence |
|---|---|---|
| W1-A | done | shared edit transaction; CRLF/BOM/TOCTOU/backup tests |
| W1-B | done | MCP transport + arg validation tests; LSP containment/lock tests |
| W1-C | done | cache racy-window, fingerprint, subset, determinism, PPR tests |
| W2-A | done | 19 op-semantics tests, each failing on the pre-change base |
| W2-B | done | output identical to base; memo, parallel==serial tests |
| W2-C | done | tag schema v2/v3; symbol graph tests; 6/6 spot-checked real callers |
| W3-A | done | `evaluation/repo_map/RESULTS_V2.md` (fingerprint `c745f6d2…`, seed-stable) |
| W3-B | done | symbol MCP/CLI tools, precise mode, opt-in post-edit diagnostics |
| W3-C | done (harness only) | validation 7/7; fake 7/7 both arms; noop 0/7; **no live run** |
| W3-D | done | scandir walk + persisted search term cache, results identical to base |
| W4 | done | semantic review (3 blockers, 9 further issues) fixed; final gate 412 passed, 6 skipped |

## Results

**Performance** (final `dt/v2`, this machine, `scripts/ocelot_index_bench.py`):

| Operation | Before (`7afb2318`) | After | Target |
|---|---|---|---|
| cold full index (4 workers) | ~60–100 s | 22.0 s | ≤ 30 s |
| `repo_map` warm | ~6.3 s | 0.24 s | ≤ 1.0 s |
| `code_search` warm | per-query PageRank, first call ~70–90 s | 0.25–0.29 s | ≤ 0.5 s |
| `code_search` first call, new process, warm side cache | n/a | 9.6 s | ≤ 10 s |
| `impact` warm | ~6 s | 0.16–0.18 s | ≤ 0.3 s |
| symbol callers/impact query | n/a | < 2 ms (graph memo hit) | ≤ 0.3 s |

**Retrieval (eval v2, 30 leakage-free tasks, recall / content-tier recall):**

| Arm | 500 | 900 | 1500 |
|---|---:|---:|---:|
| dev_repo_map | 0.28 / 0.28 | 0.25 / 0.25 | 0.47 / 0.38 |
| grep | 0.70 / 0.00 | 0.83 / 0.00 | 0.90 / 0.00 |
| code_search | 0.72 / 0.72 | 0.82 / 0.82 | 0.93 / 0.93 |

The repo map does not win once task text stops naming files; `code_search`
(BM25 + weighted graph prior) is the strongest retriever and the one that
shows code. The tasks were written after reading the target code, which
favours lexical arms; treat this as directional (30 tasks, one run).

**End-to-end:** the break/fix harness is validated (fake driver 7/7, noop 0/7)
but no hosted-model run has been made. A pilot is 7 tasks × 2 arms = 14
sessions and needs explicit approval and a cost ceiling.

**Open items:** live agent pilot. Fixed in `dt-w5-fixes`: `_python_parse`
strips a leading BOM (snapshot Symbol nodes exist for BOM files); untracked
source-file content is part of the staleness digest; the agent-eval task base
is `aef842ba` (was `a6df57f0`).
