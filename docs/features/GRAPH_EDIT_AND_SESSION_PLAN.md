# Graph edit + dev-session plan (2026-11-14)

**Status: LANDED (2026-11-14).** All three workstreams are implemented and
integrated. Combined scoped gate: **99 passed, 1 skipped** (the skipped test is
the real tree-sitter backend; `tree_sitter` is absent from `.venv`). Live MCP
smoke: hub-IR Python preview, synthetic Rust `CstNode` preview, and a full
session `orient → plan_step → act → verify → diagnose → finish`.

| Workstream | Landed | Evidence |
|---|---|---|
| A — Rust/Lua CST | `scripts/ocelot_cst_edit.py` | 20 passed, 1 skipped |
| B — Python hub IR | `scripts/ocelot_ir_edit.py` | 32 passed |
| C — dev session | `scripts/ocelot_dev_session.py` + workflow JSON | 11 passed |
| Integration | dispatcher, MCP, CLI, docs | combined 99 passed |

Remaining honest gap: install `tree_sitter` + `tree_sitter_rust`/`tree_sitter_lua`
to exercise the real Rust/Lua parse/re-parse path; until then a caller-supplied
synthetic `cst_graph` is required for those formats.

**Goal.** Finish the graph-native development layer:

1. **Rust/Lua edits through `CstNode`** — reuse `domains/ts_ingest.py`, not a
   new parser. Semantic ops target CST subtrees/leaves; `flat_text` renders.
2. **Python edits through the hub IR** — authored replacements are `Prog*`
   terms rendered by the existing graph renderer (`domains/render_python.py`),
   then spliced into the lossless Python CST. CST fallback remains for
   constructs the IR does not cover.
3. **LangGraph-style dev session graph** — a replayable task state graph
   (Task → Plan → Step → Attempt → Edit → Verification → Decision), with
   declarative transitions, persistence and checkpoint/rollback semantics.

Each workstream is a new module + tests + feature note. Integration into the
shared dispatcher, MCP server, CLI and docs happens centrally after all three
land.

## Non-goals / invariants

- This is dev tooling, not the agent runtime. No Python agent decisions in the
  live substrate; no changes to `runners/dsl/` or seed semantics.
- The canonical edit is a **semantic op list**; a unified diff is only a view.
  Raw `diff`/`patch` input stays refused.
- The lossless contract stays binding: the original file must round-trip
  byte-for-byte from the leaf structure; leaves outside an edit are
  byte-identical.
- Preview by default (`apply=false`); apply writes atomically, backs up under
  `var/ocelot_dev_edits/backups/`, and returns before/after SHA-256.
- Scoped tests only (`.venv/bin/python -m pytest tests/test_<workstream>_migrated.py -q`).
  Do not run the full migrated suite.

## Shared edit result contract

Every adapter returns the same shape (all fields required):

```json
{
  "ok": true,
  "file": "domains/foo.py",
  "applied": false,
  "format": "python|markdown|json|rust|lua",
  "base_sha256": "...",
  "new_sha256": "...",
  "before": {"lines": 10, "sha256": "..."},
  "after": {"lines": 10, "sha256": "..."},
  "ops": [ ... ],
  "changes": [ {"op": "...", "summary": "..."} ],
  "diff_view": "...",
  "diff_note": "a unified diff is a rendered view; the op list is canonical",
  "backup": null,
  "lossless": {"roundtrip": true, ...},
  "graph_stale": false
}
```

Errors raise `scripts.ocelot_code_edit.CodeEditError` (or a subclass) with a
specific reason. Refusals are honest: no silent text-patch fallback.

## Workstream A — Rust/Lua CST edits

**Owner files (only these):**
- `scripts/ocelot_cst_edit.py`
- `tests/test_cst_edit_migrated.py`
- `docs/features/CST_EDIT.md`

**Reuse:** `domains/ts_ingest.py` (`ingest_source`, `CstNode` attrs, `child`
edges, `TableWalker.flat_text`). Tree-sitter may be absent from `.venv`; the
adapter must accept a synthetic `CstNode` graph in tests and use
`ingest_source` only when the grammar imports.

**CST addressing.**
- A path is child indices from the root: `child[2].child[0]`.
- Each node's range is computed by walking its leaves in `child_index` order.
- Leaves carry exact `text`; interior text is the concatenation of children.

**Ops (v0):**
- `replace_node` — path, `text` (replace subtree's flat text)
- `insert_before_node` / `insert_after_node` — path, `text`
- `delete_node` — path (delete subtree; remove one adjacent blank line for
  statement-like nodes if safe)
- `wrap_node` — path, `prefix`, `suffix` (raw CST text; no indentation magic)
- `replace_span` — byte/char span fallback

**Validation:** reconstruct `old_source` from the CST and assert it equals the
input (`lossless.roundtrip`); apply edits bottom-up; re-parse with tree-sitter
when available (skip that check honestly when the grammar is absent); result
must be valid UTF-8.

**Acceptance tests:** synthetic CST round-trip; replace/insert/delete/wrap;
preview vs apply; backup; stale base; raw diff refusal; path escape refusal;
comments/whitespace outside the target preserved.

## Workstream B — Python hub-IR-native replacements

**Owner files (only these):**
- `scripts/ocelot_ir_edit.py`
- `tests/test_ir_edit_migrated.py`
- `docs/features/IR_EDIT.md`

**Reuse:** `domains/prog_ir_emit.emit_prog_ir` (Python AST/function → hub IR),
`domains/render_python.render_ir` / `render_program` (hub IR → Python), and
`domains/prog_eval`/`ProgEval` where useful. Do not modify the hub IR or Rust.

**Model.** The replacement text is authored as `Prog*` Term-JSON, rendered by
the existing graph renderer, then spliced into the file's lossless CST span.
This is the IR-native path for *authored* code; comments inside the replaced
span are not invented (they were replaced), comments outside are preserved.
Unsupported IR returns `{"ok": false, "blockers": [...]}`; no partial emit.

**Ops (v0):**
- `replace_expression_ir` — target AST path (e.g. `body[3].body[1].value`),
  `term` (hub IR expression)
- `replace_body_ir` — target function/method AST path, `stmts` (list of hub IR
  statements)
- `replace_function_ir` — target function AST path, `stmts`/`term` + optional
  `args`
- `fallback_check` — report whether a construct is IR-renderable (for the
  dispatcher/CST fallback decision)

**Acceptance tests:** a simple `Plus`/`Return` expression renders and splices;
comments before/after the span survive; blocked construct reports blockers;
invalid IR reports an error; preview/apply/backup/stale/raw-diff refusals.

## Workstream C — Dev-session graph (LangGraph-like)

**Owner files (only these):**
- `scripts/ocelot_dev_session.py`
- `scripts/dev_session_workflow.json`
- `tests/test_dev_session_migrated.py`
- `docs/features/DEV_SESSION.md`

**Model.** A session is a typed graph persisted under
`var/ocelot_dev_sessions/<session_id>.json`:

```
Session -has_task-> Task
Session -has_step-> Step
Step -attempt-> Attempt
Attempt -edit-> Edit
Attempt -verification-> Verification
Step -next-> Step
Session -decision-> Decision
```

Transitions are **data** (`dev_session_workflow.json`), not Python branching:

- no plan → `orient`
- plan, no step → `plan_step`
- step, no edit → `act`
- edit, no verification → `verify`
- verification failed and attempts < max → `diagnose` (then `act`)
- verification passed and more steps → `plan_step`
- all steps passed → `finish`
- explicit human gate → `approve` / `wait`

The evaluator is a mechanical table lookup over recorded facts; it returns the
next action and the reason. It must not execute edits or tests.

**API (target):**
- `DevSession.start(task, *, max_attempts=3, path=...) -> session`
- `DevSession.record(kind, **fields) -> node`
- `DevSession.state() -> graph summary`
- `DevSession.next() -> {action, reason, step_id?}`
- `DevSession.finish(outcome)`
- `load_session(id)`, `list_sessions()`
- CLI-friendly JSON only; no prints.

**Acceptance tests:** start → orient; record plan → plan_step; record edit →
verify; failed verification → diagnose; pass → next step; max attempts →
blocked; persistence reload; unknown transition is honest; ids stable.

## Integration (central, after workstreams)

1. `scripts/ocelot_edit.py` dispatches `.rs`/`.lua` to `ocelot_cst_edit` and
   `.py` ops with `engine: "ir"` to `ocelot_ir_edit`; default `.py` stays CST.
2. `scripts/ocelot_dev_memory_mcp.py` adds `dev_session_*` tools and a
   `dev_cst`/`dev_session` view; `scripts/ocelot_dev_memory.py` gets the CLI.
3. Docs: `DEV_MEMORY_MCP.md` gets the three new sections and the format table.
4. Rebuild the dev snapshot, restart the MCP server, run the combined scoped
   gate, record a verification and a decision in the journal.

## Risks

- Tree-sitter may be unavailable in `.venv`; synthetic-graph tests keep A
  honest, and the parser path is exercised only where the import exists.
- Hub IR coverage is partial; B must report blockers and the dispatcher must
  fall back to CST, never silently mis-render.
- Session graph persistence must be atomic (temp + replace) and must not hold
  agent state; it is a dev receipt graph.
- Concurrent workstreams must not edit shared files; integration is central.
