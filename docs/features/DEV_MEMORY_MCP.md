# Dev memory MCP — Ocelot as the coding agent's memory

**Status:** A-integration v0 (2026-11-14). This is the "addable now" track:
an existing coding agent (OpenCode, Claude Code, Cursor, any MCP client) uses
Ocelot as a **repo memory and citation source**, without waiting for the
full LLM-proposer loop (track B). Ocelot does not decide what to change; the
agent does. Ocelot answers structural questions and keeps a shared journal of
decisions and verification receipts.

**Not agent runtime.** This is a separate dev tool. It never boots the agent,
never mutates the agent substrate, and does not import the seed/rule runtime.
The graph it serves is a snapshot of the checkout, built by
`scripts/ocelot_dev_memory.py`.

## Why a graph instead of embeddings

Development questions are usually typed and relational:

- Which tests cover this seed?
- Which rules does this seed ship?
- Which files import this module?
- What changed recently near this symbol?
- Which docs describe this subsystem?
- Which known failures touch this test?

Those are edge traversals and exact-name lookups, not fuzzy similarity.
The snapshot is also inspectable and diffable: every answer can point at a
file, a line range, or a node id.

## Build the snapshot

```bash
cd /applications/data/projects/ocelot
.venv/bin/python -m scripts.ocelot_dev_memory build
```

The default output is `var/ocelot_dev_graph.json` (gitignored). A full build
of the current tree (including `scripts/`) takes ~90 s and produces ~137k
nodes / ~416k edges; `--no-scripts` roughly halves that. Options:

```bash
--root PATH          # another checkout
--out PATH           # another snapshot path
--docs features|all|none
--no-git             # skip the 200-commit history
--no-scripts         # skip scripts/*.py
--git-limit N
```

What is indexed:

- Python/Rust/Lua source under `runners/dsl/src`, `domains`, `domains_rs`,
  `worlds`, `substrate`, `tools`, `scripts`
- `tests/test_*.py` (Test nodes, module imports, literal path/seed mentions)
- `seeds/*.json` (manifest, dependency closure, rules/concepts/reflexes/
  microtheories/other seed-node types)
- `docs/features/*.md`, `docs/CODE_MAP.md`, `docs/SEED_DEVELOPMENT.md`,
  `docs/SCIENCE_RESEARCH.md`, root `README.md` / `CLAUDE.md` /
  `VISION_PROTOCOL.md` / `HISTORY.md` / `RESULTS.local.md`
  (`--docs all` adds all of `docs/**/*.md`)
- `results/failure_baseline.json` (known failures, linked to exact tests)
- the last 200 git commits (Commit → File edges)

Seed references are linked from both test files and ordinary source files:
`File -mentions_seed-> Seed` and `Test -mentions_seed-> Seed`. `dev_seed`
therefore answers "which code loads this seed?" as well as "which tests
exercise it?". It also returns the transitive `depends_on_closure`, not just
the direct dependencies.

The snapshot is a snapshot. Rebuild it after structural changes (new seeds,
new test modules, renamed files). A build is deterministic apart from
`generated_at` and the current git head.

## Query from the CLI

```bash
# What context should I read for this task?
.venv/bin/python -m scripts.ocelot_dev_memory context \
    "add a rule to gap awareness"

# Structural questions
.venv/bin/python -m scripts.ocelot_dev_memory search "shape decode"
.venv/bin/python -m scripts.ocelot_dev_memory file domains/teach.py
.venv/bin/python -m scripts.ocelot_dev_memory symbol teach
.venv/bin/python -m scripts.ocelot_dev_memory seed shape_decode_loop
.venv/bin/python -m scripts.ocelot_dev_memory rule note_reported_gap
.venv/bin/python -m scripts.ocelot_dev_memory tests seeds/gap_awareness.json
.venv/bin/python -m scripts.ocelot_dev_memory outline domains/teach.py
.venv/bin/python -m scripts.ocelot_dev_memory brief --task "add a seed rule"
.venv/bin/python -m scripts.ocelot_dev_memory changed
.venv/bin/python -m scripts.ocelot_dev_memory stats
```

`context` is the high-value command: it anchors on identifiers named in the
task (e.g. "gap awareness" → `gap_awareness`), then fills with the most
specific graph matches. Each item carries a file path, a line range, a source
snippet, a "why", and the node's immediate neighbours. It is a reading list
with citations, not a plan.

Record what you tried:

```bash
.venv/bin/python -m scripts.ocelot_dev_memory record \
    --kind verification \
    --task "gap awareness rule" \
    --summary "pytest tests/test_gap_awareness_migrated.py -q" \
    --file seeds/gap_awareness.json \
    --commandline "pytest tests/test_gap_awareness_migrated.py -q" \
    --exit-code 0

.venv/bin/python -m scripts.ocelot_dev_memory recent -n 10
```

The journal is `var/ocelot_dev_journal.jsonl`, append-only and shared by every
agent using the checkout. It is not a source of truth; it is a receipt log.

## Wire it into OpenCode (V2)

Add the server to the project's `opencode.jsonc` under `mcp.servers`:

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "servers": {
      "ocelot-dev-memory": {
        "type": "local",
        "command": [
          "/applications/data/projects/ocelot/.venv/bin/python",
          "-m",
          "scripts.ocelot_dev_memory_mcp"
        ],
        "cwd": "/applications/data/projects/ocelot",
        "environment": {
          "OCELOT_DEV_DUMP": "/applications/data/projects/ocelot/var/ocelot_dev_graph.json",
          "OCELOT_DEV_JOURNAL": "/applications/data/projects/ocelot/var/ocelot_dev_journal.jsonl"
        }
      }
    }
  }
}
```

OpenCode V2 groups MCP tools under Code Mode by default; the tools appear as
`tools.ocelot_dev_memory.dev_context(...)` and so on. Set `"codemode": false`
on the server if you want them on the native tool list. Use `"disabled": true`
to keep the config without connecting.

The CLI is the lower-tech fallback and works with any agent that can run a
shell command:

```bash
opencode mcp add ocelot-dev-memory --cwd /applications/data/projects/ocelot -- \
  /applications/data/projects/ocelot/.venv/bin/python -m scripts.ocelot_dev_memory_mcp
```

For this checkout there is already a gitignored project-local
`.opencode/opencode.json` with that server configured, so the tools are
available in the current OpenCode session after the config is read. In Code
Mode they are called as
`tools["ocelot-dev-memory"].dev_context(...)`. Editing the server source does
not restart an already-connected process; save the config (or reconnect the
server from `/mcps`) to pick up a code change.

The server is stdlib-only: it does **not** require the `mcp` Python package
(and it speaks the newline-delimited MCP stdio framing, with a
Content-Length fallback for LSP-style clients).

## Wire it into Claude Code

`.mcp.json` in the project root:

```json
{
  "mcpServers": {
    "ocelot-dev-memory": {
      "command": "/applications/data/projects/ocelot/.venv/bin/python",
      "args": ["-m", "scripts.ocelot_dev_memory_mcp"],
      "cwd": "/applications/data/projects/ocelot",
      "env": {
        "OCELOT_DEV_DUMP": "/applications/data/projects/ocelot/var/ocelot_dev_graph.json",
        "OCELOT_DEV_JOURNAL": "/applications/data/projects/ocelot/var/ocelot_dev_journal.jsonl"
      }
    }
  }
}
```

## MCP tools

| Tool | Use it when |
|---|---|
| `dev_context` | Starting a task. Returns a cited reading list. |
| `dev_search` | You know a name/path but not where it lives. |
| `dev_file` | Before editing a file: symbols, tests, imports, docs, failures, commits. |
| `dev_symbol` | Before editing a function/class: snippet, file, tests. |
| `dev_outline` | Signatures/docstrings/imports/test names, no bodies — cheap pre-load. |
| `dev_brief` | Pre-loaded repo brief; optional task context pack. |
| `dev_repo_map` | Ranked, token-budgeted repo map (tree-sitter tags + PageRank). |
| `dev_impact` | Transitive dependents of a file over the reference graph. |
| `dev_architecture` | Hubs, cycles, coupling, modules, dead-code hints. |
| `dev_scip` | Import a SCIP JSON export into normalized records/edges. |
| `dev_code_search` | BM25 + graph-PageRank lexical search. |
| `dev_symbol_callers` | Who calls a symbol (syntactic graph, with confidences). `precise=true` confirms direct callers with LSP. |
| `dev_symbol_callees` | What a symbol calls (syntactic graph). |
| `dev_symbol_graph_impact` | Transitive callers grouped by file: what breaks if the symbol changes. |
| `dev_symbol_resolve` | Turn a name or `path::qualname` into definition ids. |
| `dev_lsp_status` | LSP server availability (no server start). |
| `dev_definition` / `dev_references` | Compiler-accurate navigation at a position. |
| `dev_callers` / `dev_callees` | LSP call hierarchy. |
| `dev_symbol_impact` | Resolved references grouped by file. |
| `dev_rename_preview` | LSP workspace edit preview; never writes. |
| `dev_diagnostics` | Push diagnostics for a file. |
| `dev_hover` / `dev_document_symbols` | Type/docs and symbol hierarchy. |
| `dev_ast` | Python AST paths + spans for generic node edits. |
| `dev_edit` | Apply a semantic edit script (preview by default; an applied write returns LSP diagnostics for the file). |
| `dev_seed` | Before editing a seed: version, deps, rules/concepts, tests, docs. |
| `dev_rule` | Before editing a rule: its seed, file, and current body. |
| `dev_tests` | Before/after a change: the scoped gate. |
| `dev_node` | Expand an id from a previous result. |
| `dev_neighbours` | Walk dependency/seed/test/doc edges. |
| `dev_graph_query` | Run a raw substrate DSL Term (read-only) over the snapshot. |
| `dev_stats` | Check snapshot freshness/histograms. |
| `dev_changed` | Working-tree changes, linked to graph files. |
| `dev_record` | Append a decision/verification receipt. |
| `dev_session_start` | Start a replayable Task→Plan→Step→Edit→Verify graph. |
| `dev_session_record` | Append `plan` / `step` / `attempt` / `edit` / `verification` / `decision`. |
| `dev_session_state` | Session graph snapshot + next action. |
| `dev_session_next` | Next workflow action + reason. |
| `dev_session_finish` | Close the session. |
| `dev_session_list` | List persisted sessions. |
| `dev_recent` | Read the shared journal. |

All tools are read-only except `dev_edit` (structured transaction, preview by
default, backup on apply) and `dev_record` (one JSONL line). There is no shell
execution, no raw patch application, and no network access in the server. Running tests/builds stays with the coding agent (it already has
a shell and a permission model).

## The self-development loop this enables

1. **Orient**: `dev_context("fix the stale reply rule in gap_awareness")`.
   Read the returned seed, rule and test snippets.
2. **Scope the gate**: `dev_tests("seeds/gap_awareness.json")`, then run the
   scoped `pytest` yourself.
3. **Change**: edit the seed/rule/adapter.
4. **Verify**: run the scoped test again. If it passes, optionally run the
   broader slice the `dev_file` view lists.
5. **Record**: `dev_record(kind="verification", ...)` with the exact command
   and exit code.
6. **Rebuild** the snapshot if the change added/renamed files, seeds or tests.

This is deliberately the *outer loop* only. Track B will move the proposal
step into Ocelot's CEGIS loop (LLM proposes, `ProgEval`/tests decide, accepted
edits become graph constructions). A is the bridge that makes the current
agent better immediately, and the data it records is the raw material for B.

## Repo-map evaluation (measured)

The map is evaluated as a retrieval instrument, not an end-to-end coding
benchmark. `evaluation/repo_map/tasks.json` holds 21 explicit tasks with
hand-authored expected files; the harness runs baseline, `dev_context`,
`dev_repo_map`, and both, at 500/900/1500-token budgets.

Real-repo mean recall@budget (21 tasks, deterministic fingerprint
`ae5b33c2…`):

| Budget | baseline | dev_context | dev_repo_map | both |
|---:|---:|---:|---:|---:|
| 500 | 0.000 | 0.103 | **0.401** | **0.464** |
| 900 | 0.000 | 0.119 | **0.409** | **0.488** |
| 1500 | 0.040 | 0.218 | **0.623** | **0.675** |

The map is the strongest single arm; the union adds recall at roughly 2×
tokens. `repo-map-eval` runs the harness (full run ~10 minutes; `--limit` for a
subset). See [`REPO_MAP_EVAL.md`](REPO_MAP_EVAL.md) and
`evaluation/repo_map/RESULTS.md`.

## Repo map and impact

The repo map is the Aider/RepoGraph-style layer built on tree-sitter tags:

- Python tags come from the stdlib AST (fast); Rust/Lua tags come from each
  grammar's own `queries/tags.scm`.
- Files are nodes; a reference edge points from a referencing file to the file
  defining the symbol. Generic/high-fan-out identifiers are capped so the graph
  stays usable.
- Personalized PageRank ranks files for the task; task-named seeds/files from
  the dev graph become focus files; tests are down-weighted.
- The render is token-budgeted in three tiers: full outlines for the hottest
  files, public symbols for the middle, a listing for the tail.

```text
dev_repo_map("shape decode loop", 900)
→ reflective_faculty.py full outline
→ runners/dsl/src/shape_decode.rs full outline
→ ...middle-tier symbols and listing within budget
```

`dev_impact(file, depth)` walks the reverse reference graph and reports
transitive dependents. The tag cache is content-hash incremental (`mtime+size`
fast path, hash on change), so only changed files are re-parsed.

The full landscape comparison, including what we adopted and what remains
(LSP/SCIP, symbol-level call graphs, hybrid semantic search), is in
[`GRAPH_CODING_LANDSCAPE.md`](GRAPH_CODING_LANDSCAPE.md).

## LSP bridge (compiler-accurate)

`dev_definition`, `dev_references`, `dev_callers`, `dev_callees`,
`dev_symbol_impact`, `dev_rename_preview`, `dev_diagnostics`, `dev_hover` and
`dev_document_symbols` use a real language server over stdio JSON-RPC. Positions
are LSP-native 0-based lines/UTF-16 characters.

- Python: `.venv/bin/pyright-langserver --stdio` (live definition smoke passed).
- Rust: `rust-analyzer` (the binary is present but the rustup component is
  missing in this environment; status reports honestly).
- C/C++: `clangd`; TypeScript: `typescript-language-server` if installed.
- `dev_rename_preview` is review-only. Applying a rename still goes through the
  semantic edit transaction.
- When a server is absent or a query fails, the result is `ok:false` with a
  reason; file-level `dev_impact` / `dev_repo_map` remain the fallback.
- Diagnostics are push-based; `published:false` means nothing arrived, not
  necessarily clean.

Line and character arguments of the position tools are 0-based LSP positions.
Line numbers that `dev_symbol*` and `dev_file` return are 1-based, so subtract 1
before you pass one to a position tool.

See [`LSP_BRIDGE.md`](LSP_BRIDGE.md).

## Symbol graph and precise mode

`dev_symbol_callers`, `dev_symbol_callees`, `dev_symbol_graph_impact` and
`dev_symbol_resolve` answer symbol questions from the tag cache, using
`scripts/ocelot_symbol_graph.py` (design and limits in
[`SYMBOL_GRAPH.md`](SYMBOL_GRAPH.md)). The cache is `var/ocelot_dev_tags.json`
in the process root and is refreshed on each call. The graph is syntactic: each
reference resolves locally, through a `from X import name` binding, or by a
unique global name, and each edge carries a confidence. There is no type
inference.

`symbol` takes `path::qualname`, a qualname such as `Class.method`, or a bare
name. A name that matches several definitions returns the candidate ids under
`ambiguous` (for `dev_symbol_resolve`, under `matches`).

`precise=true` on `dev_symbol_callers` and `dev_symbol_graph_impact` asks the
language server for the target's references, at the target definition's name
(`PRECISE_TIMEOUT` 20 s). Then:

- each depth-1 row gets `lsp_confirmed`: `true` when a reference falls inside
  that caller's line span, `false` when none does, and `null` for deeper rows
  (not checked);
- references outside every depth-1 row are listed under `lsp_only` with the
  innermost enclosing symbol (`<module>` at module level), line 1-based;
- `precision` reports what happened: `{"lsp": "used", "server", "references",
  "confirmed", "unconfirmed", "lsp_only"}`, `{"lsp": "unavailable: ..."}` when no
  server is installed (the server is not started just to check; the rows are
  the syntactic ones), or `{"lsp": "error: ..."}` when the query failed.

An `import alpha` statement is a reference to `alpha`. The server reports it, so
it appears in `lsp_only` under `<module>`. It is not a call.

Example (live pyright, two-file temp project in which `domains/b.py` imports and
calls `alpha` from `domains/a.py`; the `stats`, `tag_cache` and `timings` keys
are omitted):

```json
{"jsonrpc": "2.0", "id": 7, "method": "tools/call",
 "params": {"name": "dev_symbol_callers",
            "arguments": {"symbol": "domains/a.py::alpha", "precise": true}}}
```

```json
{"ok": true, "op": "callers", "symbol": "domains/a.py::alpha", "depth": 1,
 "results": [{"id": "domains/b.py::use", "file": "domains/b.py",
              "qualname": "use", "depth": 1, "resolution": "import",
              "confidence": 1.0, "lsp_confirmed": true}],
 "lsp_only": [{"id": "domains/b.py::<module>", "file": "domains/b.py",
               "line": 1, "qualname": "<module>"}],
 "precision": {"lsp": "used", "server": "pyright-langserver", "references": 2,
               "confirmed": 1, "unconfirmed": 0, "lsp_only": 1}}
```

Precise mode is only as complete as the server's workspace index. On the Ocelot
worktree (about 6,800 indexed files), pyright returned 2 references for
`scripts/ocelot_repo_map.py::update_tag_cache` against 18 syntactic callers, so
16 rows came back `lsp_confirmed: false`. A later query in the same process
returned the same 2, and a third timed out after 20 s. Read `false` as "the
server did not confirm this", not "this is not a caller".

## Post-edit diagnostics

`dev_edit` with `apply=true` now waits for the language server's push
diagnostics for the edited file and returns them under `diagnostics`:
`{"ok", "count", "errors", "warnings", "published", "items", "server"}`. Each
item has its 0-based `line` and a 1-based `line1`; `items` holds the first 20.
The LSP client sends `didChange` when the file's hash differs from the last
hash it saw, so the diagnostics describe the new content. The journal `edit`
entry stores the counts without `items`.

- `diagnostics=false` skips the step: `{"skipped": "diagnostics=false"}`.
- No language server: `{"skipped": "unavailable: ..."}`. The edit still applies.
- A failed query: `{"error": "..."}`. The edit still applies.
- Preview (`apply=false`) never runs diagnostics, and the key is absent.
- `published: false` means the server sent nothing within 8 s, so the counts are
  not evidence of a clean file.

## Lexical hybrid search

`dev_code_search(query)` runs BM25 over paths, symbol names and source lines,
then reranks the lexical candidates with repo-map PageRank via reciprocal rank
fusion (RRF, k=60). It is the no-embedding half of hybrid retrieval: use it to
find candidate files, then `dev_context`/`dev_repo_map` to expand and LSP/SCIP
for precise navigation. The CLI is `code-search QUERY`.

## SCIP import

`dev_scip(path)` accepts a SCIP JSON export (`scip print --json`), normalizes
definitions/references/roles/ranges, and returns repo-map-compatible edges plus
per-file counts. A real `.scip` protobuf is accepted only when `protobuf` +
`scip_pb2` are importable; otherwise the tool refuses honestly. See
[`SCIP_IMPORT.md`](SCIP_IMPORT.md).

## Architecture summary

`dev_architecture(top)` reads the same reference graph and reports hubs
(PageRank/in-degree), cycles (Tarjan SCCs), coupling, module boundaries,
dead-code candidates (a heuristic) and the test/source ratio. It is
deterministic, file-level and syntactic; use LSP/SCIP for compiler-accurate
answers. The CLI is `architecture --top N`.

## Dev session graph (LangGraph-like)

The dev session is a **replayable receipt graph**, not an executor. It records
what the agent did — Task, Plan, Step, Attempt, Edit, Verification, Decision —
and reads the next action from a declarative table
(`scripts/dev_session_workflow.json`). It never edits files or runs tests.

```
Session -has_task-> Task
Session -has_plan-> Plan
Session -has_step-> Step
Step    -attempt-> Attempt
Attempt -edit-> Edit
Attempt -verification-> Verification
Session -decision-> Decision
```

Typical loop:

```text
dev_session_start("fix gap_awareness")
→ next: orient

dev_session_record(sid, "plan", {steps: ["read rule", "fix seed"]})
→ next: plan_step

dev_session_record(sid, "step")
→ next: act

dev_session_record(sid, "edit", {files: ["seeds/gap_awareness.json"]})
→ next: verify

dev_session_record(sid, "verification",
                   {passed: true, command: "pytest ...", exit_code: 0})
→ next: plan_step / finish
```

A failed verification yields `diagnose` until `max_attempts` is reached, then
`blocked`. `dev_session_state` returns the graph and derived facts; `finish`
closes it with an outcome. Sessions live at
`var/ocelot_dev_sessions/<id>.json` and are written atomically. The CLI mirrors
the tools: `session-start`, `session-record`, `session-state`, `session-next`,
`session-finish`, `session-list`.

## Editing is a graph operation, not a diff

A diff is a lossy text rendering of a semantic change. The canonical edit is
an **op list against graph targets**; `diff_view` is emitted only so a human
can review it. The edit layer refuses a raw `diff`/`patch` input outright.

### The lossless structure already exists in the substrate

This is not a new code model. The substrate already has the pieces:

| Piece | What it provides |
|---|---|
| `domains/ts_ingest.py` | Rust/Lua `CstNode` graph; leaves carry exact `text`; `TableWalker.flat_text(root)` reconstructs the source. Comments/whitespace are leaves, so the CST is byte-exact. |
| `domains/py_cst_ingest.py` | The Python twin (added 2026-11-14): `tokenize` token leaves + explicit `trivia` leaves, ingested as `CstNode` under `child` edges. `flat_text` round-trips byte-for-byte, comments included. |
| `domains/ast_to_term.py` | The semantic `AstNode` overlay. It now also carries `lineno`/`col_offset`/`end_lineno`/`end_col_offset` (additive), so a semantic target has a span. |
| `domains/ast_term_rules.py` | AST→Term correspondence expressed as graph rules; not a Python emitter. |
| `domains/render_python.py` + `prog_*` | Hub-IR renderer and `ProgEval`; the path for graph-only edits once the IR covers the construct. |
| `scripts/ocelot_lossless.py` | The edit-side bridge: token/trivia or line leaves, `render()` concatenates them, `replace()` would edit a leaf range. Every adapter asserts the leaf structure round-trips the source before editing. |

The point: **the CST owns every byte; the AST owns the addresses.** A leaf
outside the edited span is returned untouched — comments, blank lines,
indentation, trailing spaces and line endings included.

### Python: anything the AST supports

`dev_ast` returns the AST graph for a file as structural paths with types,
line spans and previews. Paths are the edit targets:

```text
body[3]                  the 4th top-level statement (a FunctionDef)
body[3].body[1]          its 2nd body statement (a Return)
body[3].body[1].value    the returned expression
body[3].args.args[1]     the 2nd positional argument
body[3].decorator_list[0] its first decorator
```

Generic node ops (any Python construct the AST parses):

| Op | Target | Effect |
|---|---|---|
| `replace_node` | AST path | replace that node's exact span |
| `insert_before_node` / `insert_after_node` | AST path | insert before/after; statements are re-indented |
| `delete_node` | AST path | delete a statement or a list element (comma cleanup); required single fields are refused |
| `wrap_node` | AST path | expression: prefix/suffix; statement: a block prefix ending in `:` and optional suffix |

Semantic sugar (same transaction, shorter scripts):

| Op | Target | Effect |
|---|---|---|
| `replace_symbol` | symbol qualname | replace the whole definition, decorators included |
| `replace_body` | symbol qualname | replace the body; the tool re-applies the body indent |
| `insert_import` | file | add `import x` / `from x import y` after the last import |
| `delete_symbol` | symbol qualname | delete the definition (and one trailing blank line) |
| `insert_before_symbol` / `insert_after_symbol` | symbol qualname | insert text at the symbol anchor |
| `replace_span` | line/col span | replace an explicit span |
| `rename_symbol` | symbol qualname | lexical NAME-token rename in the file, count reported |

### Python: hub-IR-authored replacements

Where the replacement is *authored code*, the replacement itself can be a hub
`Prog*` Term-JSON tree. The existing graph renderer
(`domains/render_python.render_ir` over the `RenderRule` seed) produces the
Python surface, and the result is spliced into the target's lossless CST span.
Comments/trivia outside the span survive; comments inside a replaced body were
part of what was replaced.

| Op | Target | Effect |
|---|---|---|
| `replace_expression_ir` | AST path | render a `Prog*` expression term into that span |
| `replace_body_ir` | function/method path | render a list of `Prog*` statements into the body |
| `replace_function_ir` | function path | render the whole function body/signature surface |
| `fallback_check` | target/term | read-only coverage probe: `ok:false` + `blockers` means use the CST path |

IR intent is explicit (`"engine": "ir"`) or implied by an `*_ir` op. If the
renderer cannot spell a construct, the adapter returns `ok:false` with a
populated `blockers` list and leaves the file untouched; the dispatcher can
then use the CST path. No partial render, no silent text fallback. See
[`IR_EDIT.md`](IR_EDIT.md).

### Markdown: sections are the graph

`dev_ast` is Python-specific; Markdown addresses are headings. `dev_edit`
dispatches `.md`/`.markdown` to the section adapter:

| Op | Target | Effect |
|---|---|---|
| `replace_section` | section title/path | replace heading + body + nested subsections |
| `replace_section_body` | section title/path | replace direct body, keep heading |
| `append_to_section` | section title/path | append at the end of the whole section |
| `insert_section_before` / `insert_section_after` | section title/path | insert a new section |
| `delete_section` | section title/path | delete the whole section |
| `replace_frontmatter` | file | replace/insert the leading `---` block |
| `replace_span` | line/col span | explicit span |

### JSON: document paths

`.json` dispatches to a **span-preserving** path adapter. A seed manifest is a
document tree; only the target value is re-rendered, so long descriptions,
key order and indentation elsewhere are byte-identical.

| Op | Path example | Effect |
|---|---|---|
| `set` | `["version"]` | set a scalar/object value |
| `merge` | `["nodes", 0, "attrs"]` | set each key of an object |
| `append` | `["nodes"]` / `["rules"]` | append to an array |
| `delete` | `["nodes", 1]` | delete an element/key |
| `replace_span` | line/col | explicit span |

### Rust/Lua: `CstNode` subtree edits

`.rs`/`.lua` dispatch to the lossless `CstNode` graph from
`domains/ts_ingest.py`. Paths are child positions (`child[2].child[0]`);
leaves carry exact text, so comments/whitespace outside the target survive.
The real backend uses `tree-sitter` + the language grammar (installed in this
`.venv`); when those are absent, the caller can supply a synthetic nested CST
via `cst_graph` (the same graph contract, caller as world adapter), or the edit
is refused honestly.

Reproduce the environment with:

```bash
.venv/bin/pip install -r requirements-dev.txt
```

(`tree-sitter`, `tree-sitter-python`, `tree-sitter-rust`, `tree-sitter-lua`).

| Op | Target | Effect |
|---|---|---|
| `replace_node` | CST path | replace a subtree's flat text |
| `insert_before_node` / `insert_after_node` | CST path | insert raw text |
| `delete_node` | CST path | delete a subtree (conservative blank-line cleanup) |
| `wrap_node` | CST path | prefix + subtree + suffix |
| `replace_span` | char/byte/line span | explicit span |

No symbol/definition addressing yet; CST paths plus `base_sha256` are the
stable address. See [`CST_EDIT.md`](CST_EDIT.md).

### Format dispatch

| Format | Adapter | Status |
|---|---|---|
| `.py` | AST paths + lossless Python CST; hub-IR-authored replacements via `*_ir` / `engine:"ir"` | v0 |
| `.md` / `.markdown` | section graph + line leaves | v0 |
| `.json` | document paths + span-preserving leaves | v0 |
| `.rs` / `.lua` | `ts_ingest` `CstNode` graph | v0 CST ops; tree-sitter backend or a supplied synthetic graph |
| `.yaml` / `.toml` / others | — | refused rather than falling back to a text patch |

Adding a format means adding a parser + renderer for that format's block graph
and sharing the transaction contract. It does not add a new text-patch
convention.

Example script (preview by default):

```json
{
  "file": "domains/teach.py",
  "base_sha256": "<optional optimistic-concurrency check>",
  "ops": [
    {"op": "replace_node",
     "target": "body[12].body[1].value",
     "text": "_teach_impl(agent, type_, attrs)"}
  ]
}
```

CLI:

```bash
# preview: no write, returns changes + diff_view + before/after hashes
.venv/bin/python -m scripts.ocelot_dev_memory ast domains/teach.py
.venv/bin/python -m scripts.ocelot_dev_memory edit \
    --file domains/teach.py --script /tmp/edit.json

# apply: atomic write, backup under var/ocelot_dev_edits/backups,
# append an `edit` entry to the journal
.venv/bin/python -m scripts.ocelot_dev_memory edit \
    --file domains/teach.py --script /tmp/edit.json --apply
```

Safety properties:

- **Preview first.** `apply=false` is the default; nothing is written.
- **Stale-base refusal.** Pass `base_sha256` (returned by `dev_file` or a
  previous preview) and the edit refuses if the file changed.
- **Parse gate.** Python results must `ast.parse`/`compile`; Markdown must
  have balanced fences; JSON must parse; a broken edit never reaches disk.
- **Lossless gate.** The leaf structure must reconstruct the source exactly
  before the edit; leaves outside the edit are byte-identical after it.
- **Atomic write + backup.** The original goes to
  `var/ocelot_dev_edits/backups/<ts>_<sha>_<name>`; the new text is written to
  a temp file and `os.replace`d.
- **Path safety.** The resolved path must stay under the repo root.
- **Recorded transaction.** The journal entry contains the op list, before/after
  hashes, backup path, and task label. The snapshot is marked stale; rebuild
  after the transaction.

What remains for the full graph-only edit path: route the generic AST ops
through the hub IR (`Prog*` + Rust `Render` rules) where the IR covers the
construct, and wire the existing `ts_ingest` CST for Rust/Lua. The current
layer is honest: semantic targets in, lossless CST out, diff as a view.

## Honest limits (v0)

- **Snapshot, not live.** Rebuild after structural changes; the snapshot does
  not watch the filesystem.
- **Imports + literal mentions, not a full call graph.** `File -imports-> File`
  and `Test -tests_module-> File` are resolved mechanically. There is no
  type-aware call graph or reference index yet.
- **Test coverage is a link, not a guarantee.** A test is linked when it
  imports the module, mentions a repo path, or mentions `seeds/<id>.json`.
  Direct symbol-mention matching is a text heuristic when the symbol name is
  distinctive.
- **Docs default to `docs/features` + root docs** to keep the build fast.
  Use `--docs all` when you need the research archive.
- **Seed items include every typed node in a manifest**, including large
  lexical/qualia tables. This is why the snapshot is ~137k nodes. If that
  becomes slow, add a `--seed-item-types` filter; do not hand-edit the dump.
- **Edit adapters are v0.** Python has symbol + generic AST-node ops; Markdown
  has section ops; JSON has path ops. Rust/Lua have the `ts_ingest` `CstNode`
  parser but no edit adapter yet. YAML/TOML/other formats are refused rather
  than silently patched. Rename is lexical and reported as such; scope-aware
  rename is a later graph pass.
- **Symbol graph is syntactic.** Callers and callees come from name, import and
  local-scope resolution only. `obj.method()` resolves by name, under the name
  rules. Dynamic dispatch, `getattr` and star re-exports are not followed. Tags are not extracted from a
  file that starts with a UTF-8 BOM (observed with tree-sitter), so such a file
  has no symbols in the graph.
- **Precise mode is only as complete as the language server.** See the note in
  *Symbol graph and precise mode*.
- **No `symbol-impact` CLI for the symbol graph.** `python -m
  scripts.ocelot_dev_memory symbol-impact` is the existing LSP call-impact verb.
  Use the MCP tool `dev_symbol_graph_impact`, or `symbol-callers` / `symbol-callees`
  on the CLI.
- **No LLM in the server.** It is deterministic and offline. The LLM is the
  coding agent's business; this surface only gives it better input.
- **No evaluation yet.** The next measurement is the A-vs-baseline ablation:
  same task, same model, with/without `dev_context`, compare success,
  regressions, tokens and latency. Until that is measured, this is a
  convenience, not a claim.

## Source

- `scripts/ocelot_dev_memory.py` — builder, query layer, CLI.
- `scripts/ocelot_dev_memory_mcp.py` — stdlib MCP stdio server.
- `scripts/ocelot_code_edit.py` — graph-addressed Python edit algebra
  (symbol + generic AST node ops, preview/apply, parse gate, backup).
- `scripts/ocelot_ir_edit.py` — hub-IR-authored Python replacements rendered
  by `domains/render_python`, spliced into the lossless CST.
- `scripts/ocelot_cst_edit.py` — Rust/Lua `CstNode` subtree edits (tree-sitter
  backend or a caller-supplied synthetic graph).
- `scripts/ocelot_repo_map.py` — tree-sitter tags, reference graph, personalized
  PageRank, token-budgeted repo map, and impact queries.
- `scripts/ocelot_repo_map_eval.py` + `evaluation/repo_map/` — the retrieval
  evaluation harness, explicit task set, and measured results.
- `scripts/ocelot_architecture.py` — deterministic hubs/cycles/coupling/
  dead-code/test-ratio report over the same graph.
- `scripts/ocelot_scip_import.py` — SCIP JSON normalization and repo-map edges.
- `scripts/ocelot_code_search.py` — BM25 + graph-PageRank lexical search.
- `scripts/ocelot_lsp.py` — stdio LSP client, server registry, diagnostics
  cache, symbol impact and rename preview.
- `scripts/ocelot_markdown_edit.py`, `scripts/ocelot_json_edit.py` — the
  Markdown section and JSON path adapters.
- `scripts/ocelot_edit.py` — format dispatcher.
- `scripts/ocelot_lossless.py` — the leaf/trivia bridge shared by adapters.
- `scripts/ocelot_dev_session.py` + `scripts/dev_session_workflow.json` — the
  replayable dev-session graph and its declarative transition table
  ([`DEV_SESSION.md`](DEV_SESSION.md)).
- `domains/py_cst_ingest.py` — Python `CstNode`/trivia ingestion, the twin of
  `domains/ts_ingest.py`; `flat_text` is byte-exact.
- `tests/test_dev_memory_migrated.py` — synthetic-repo gate.
- `docs/research/engine_substrate/GRAPH_INTERROGATE.md` — the read-only graph
  interrogation precedent this reuses (`GraphInterrogator` / DSL evaluator).
