# Repo-map retrieval evaluation

- Root: `/applications/data/projects/ocelot`
- Tasks: 21 (`/applications/data/projects/ocelot/evaluation/repo_map/tasks.json`)
- Source-file universe: 6826
- Budgets: 500, 900, 1500 tokens
- Arms: baseline, dev_context, dev_repo_map, both
- Deterministic fingerprint: `ae5b33c23fa204249e54921f5204c7970d9e107c0e00784810a7a0e2c32340f4`
- Wall time: 575.838 s

## Aggregate metrics

| Budget | Arm | Tasks | Mean recall@budget | Mean precision | Mean files | Mean tokens | Mean s | Cache parsed | Cache reused |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 500 | baseline | 21 | 0.000 | 0.000 | 70.0 | 496 | 0.00 | 0 | 0 |
| 500 | dev_context | 21 | 0.103 | 0.214 | 1.3 | 474 | 1.66 | 0 | 0 |
| 500 | dev_repo_map | 21 | 0.401 | 0.191 | 4.8 | 469 | 9.38 | 6841 | 136505 |
| 500 | both | 21 | 0.464 | 0.192 | 6.0 | 943 | 11.04 | 6841 | 136505 |
| 900 | baseline | 21 | 0.000 | 0.000 | 127.0 | 893 | 0.00 | 0 | 0 |
| 900 | dev_context | 21 | 0.119 | 0.155 | 2.2 | 663 | 1.61 | 0 | 0 |
| 900 | dev_repo_map | 21 | 0.409 | 0.221 | 4.5 | 861 | 6.49 | 17 | 143329 |
| 900 | both | 21 | 0.488 | 0.190 | 6.6 | 1524 | 8.11 | 17 | 143329 |
| 1500 | baseline | 21 | 0.040 | 0.000 | 205.0 | 1498 | 0.00 | 0 | 0 |
| 1500 | dev_context | 21 | 0.218 | 0.132 | 4.5 | 1246 | 1.82 | 0 | 0 |
| 1500 | dev_repo_map | 21 | 0.623 | 0.066 | 24.7 | 1491 | 6.32 | 14 | 143332 |
| 1500 | both | 21 | 0.675 | 0.063 | 28.2 | 2737 | 8.14 | 14 | 143332 |

## Recall by task

### 500 tokens

| Task | baseline | dev_context | dev_repo_map | both |
|---|---:|---:|---:|---:|
| repo-map-three-tier-render | 0.00 | 0.00 | 0.00 | 0.00 |
| repo-map-tag-cache | 0.00 | 0.00 | 0.00 | 0.00 |
| repo-map-reference-pagerank | 0.00 | 0.00 | 1.00 | 1.00 |
| dev-memory-mcp-repo-map | 0.00 | 0.00 | 1.00 | 1.00 |
| dev-context-pack | 0.00 | 0.00 | 0.00 | 0.00 |
| code-edit-op-list | 0.00 | 0.00 | 0.00 | 0.00 |
| ir-edit-render-python | 0.00 | 0.00 | 0.67 | 0.67 |
| rust-cst-trivia | 0.00 | 0.00 | 0.67 | 0.67 |
| python-cst-lossless | 0.00 | 0.33 | 1.00 | 1.00 |
| markdown-section-edit | 0.00 | 0.00 | 0.50 | 0.50 |
| json-path-edit | 0.00 | 0.00 | 0.00 | 0.00 |
| pyo3-one-line-handoffs | 0.00 | 0.50 | 1.00 | 1.00 |
| term-variant-grammar | 0.00 | 0.33 | 0.00 | 0.33 |
| rule-fixpoint-rewrite | 0.00 | 0.00 | 0.50 | 0.50 |
| seed-loader-topological | 0.00 | 0.50 | 0.00 | 0.50 |
| gap-awareness-unhandled-instruction | 0.00 | 0.00 | 0.25 | 0.25 |
| shape-decode-reading-collapse | 0.00 | 0.00 | 0.33 | 0.33 |
| core-emotions-weighted-contribution | 0.00 | 0.00 | 0.33 | 0.33 |
| conversation-action-goal-binding | 0.00 | 0.50 | 0.00 | 0.50 |
| dev-session-replay | 0.00 | 0.00 | 0.50 | 0.50 |
| frozen-core-boot-invariant | 0.00 | 0.00 | 0.67 | 0.67 |

### 900 tokens

| Task | baseline | dev_context | dev_repo_map | both |
|---|---:|---:|---:|---:|
| repo-map-three-tier-render | 0.00 | 0.00 | 0.00 | 0.00 |
| repo-map-tag-cache | 0.00 | 0.00 | 0.00 | 0.00 |
| repo-map-reference-pagerank | 0.00 | 0.00 | 1.00 | 1.00 |
| dev-memory-mcp-repo-map | 0.00 | 0.00 | 1.00 | 1.00 |
| dev-context-pack | 0.00 | 0.00 | 0.00 | 0.00 |
| code-edit-op-list | 0.00 | 0.00 | 0.00 | 0.00 |
| ir-edit-render-python | 0.00 | 0.00 | 0.67 | 0.67 |
| rust-cst-trivia | 0.00 | 0.00 | 0.67 | 0.67 |
| python-cst-lossless | 0.00 | 0.67 | 0.67 | 1.00 |
| markdown-section-edit | 0.00 | 0.00 | 0.50 | 0.50 |
| json-path-edit | 0.00 | 0.00 | 0.50 | 0.50 |
| pyo3-one-line-handoffs | 0.00 | 0.50 | 1.00 | 1.00 |
| term-variant-grammar | 0.00 | 0.33 | 0.00 | 0.33 |
| rule-fixpoint-rewrite | 0.00 | 0.00 | 0.50 | 0.50 |
| seed-loader-topological | 0.00 | 0.50 | 0.00 | 0.50 |
| gap-awareness-unhandled-instruction | 0.00 | 0.00 | 0.25 | 0.25 |
| shape-decode-reading-collapse | 0.00 | 0.00 | 0.33 | 0.33 |
| core-emotions-weighted-contribution | 0.00 | 0.00 | 0.33 | 0.33 |
| conversation-action-goal-binding | 0.00 | 0.50 | 0.00 | 0.50 |
| dev-session-replay | 0.00 | 0.00 | 0.50 | 0.50 |
| frozen-core-boot-invariant | 0.00 | 0.00 | 0.67 | 0.67 |

### 1500 tokens

| Task | baseline | dev_context | dev_repo_map | both |
|---|---:|---:|---:|---:|
| repo-map-three-tier-render | 0.00 | 0.00 | 1.00 | 1.00 |
| repo-map-tag-cache | 0.00 | 0.00 | 0.50 | 0.50 |
| repo-map-reference-pagerank | 0.00 | 0.00 | 1.00 | 1.00 |
| dev-memory-mcp-repo-map | 0.00 | 0.00 | 1.00 | 1.00 |
| dev-context-pack | 0.00 | 0.00 | 0.00 | 0.00 |
| code-edit-op-list | 0.00 | 0.00 | 0.33 | 0.33 |
| ir-edit-render-python | 0.00 | 0.00 | 0.67 | 0.67 |
| rust-cst-trivia | 0.00 | 0.00 | 1.00 | 1.00 |
| python-cst-lossless | 0.00 | 0.67 | 1.00 | 1.00 |
| markdown-section-edit | 0.00 | 0.00 | 0.50 | 0.50 |
| json-path-edit | 0.00 | 0.00 | 0.50 | 0.50 |
| pyo3-one-line-handoffs | 0.00 | 0.50 | 1.00 | 1.00 |
| term-variant-grammar | 0.00 | 0.67 | 1.00 | 1.00 |
| rule-fixpoint-rewrite | 0.00 | 0.50 | 0.50 | 0.50 |
| seed-loader-topological | 0.00 | 0.50 | 0.50 | 1.00 |
| gap-awareness-unhandled-instruction | 0.00 | 0.25 | 0.25 | 0.50 |
| shape-decode-reading-collapse | 0.00 | 0.33 | 0.33 | 0.33 |
| core-emotions-weighted-contribution | 0.33 | 0.00 | 0.33 | 0.33 |
| conversation-action-goal-binding | 0.50 | 0.50 | 0.50 | 0.50 |
| dev-session-replay | 0.00 | 0.00 | 0.50 | 0.50 |
| frozen-core-boot-invariant | 0.00 | 0.67 | 0.67 | 1.00 |

## Task set

| Task | Expected files | Notes |
|---|---|---|
| repo-map-three-tier-render | `scripts/ocelot_repo_map.py` | Three-tier render and token budget live in repo_map() in scripts/ocelot_repo_map.py. |
| repo-map-tag-cache | `scripts/ocelot_repo_map.py`<br>`tests/test_repo_map_migrated.py` | update_tag_cache() implements the mtime/size fast path and sha256 fallback; test_incremental_cache asserts parsed/reused counts. |
| repo-map-reference-pagerank | `scripts/ocelot_repo_map.py` | build_reference_graph(), _task_relevance(), and personalized_pagerank() are in scripts/ocelot_repo_map.py. |
| dev-memory-mcp-repo-map | `scripts/ocelot_dev_memory_mcp.py`<br>`scripts/ocelot_dev_memory.py` | Tool declarations and dispatch are in scripts/ocelot_dev_memory_mcp.py; DevMemory.context/repo_map/impact are in scripts/ocelot_dev_memory.py. |
| dev-context-pack | `scripts/ocelot_dev_memory.py`<br>`tests/test_dev_memory_migrated.py` | Context pack assembly is DevMemory.context(); tests/test_dev_memory_migrated.py covers anchors, snippets, and budget trimming. |
| code-edit-op-list | `scripts/ocelot_code_edit.py`<br>`scripts/ocelot_edit.py`<br>`tests/test_code_edit_migrated.py` | scripts/ocelot_code_edit.py owns the semantic op list; scripts/ocelot_edit.py is the format-dispatching transaction entry point; test_code_edit_migrated.py is the gate. |
| ir-edit-render-python | `scripts/ocelot_ir_edit.py`<br>`domains/render_python.py`<br>`tests/test_ir_edit_migrated.py` | The IR adapter is scripts/ocelot_ir_edit.py, the render rules/walker are domains/render_python.py, and tests/test_ir_edit_migrated.py gates the splice. |
| rust-cst-trivia | `domains/ts_ingest.py`<br>`scripts/ocelot_cst_edit.py`<br>`tests/test_cst_edit_migrated.py` | domains/ts_ingest.py builds the CstNode graph with optional trivia; scripts/ocelot_cst_edit.py edits it; test_cst_edit_migrated.py asserts losslessness. |
| python-cst-lossless | `domains/py_cst_ingest.py`<br>`scripts/ocelot_lossless.py`<br>`tests/test_py_cst_ingest_migrated.py` | Python token/trivia ingest is domains/py_cst_ingest.py, its editing/render helper is scripts/ocelot_lossless.py, and the gate is tests/test_py_cst_ingest_migrated.py. |
| markdown-section-edit | `scripts/ocelot_markdown_edit.py`<br>`tests/test_markdown_edit_migrated.py` | Section operations live in scripts/ocelot_markdown_edit.py and are covered by tests/test_markdown_edit_migrated.py. |
| json-path-edit | `scripts/ocelot_json_edit.py`<br>`tests/test_json_edit_migrated.py` | Span-preserving JSON path operations live in scripts/ocelot_json_edit.py and are covered by tests/test_json_edit_migrated.py. |
| pyo3-one-line-handoffs | `runners/dsl/src/py.rs`<br>`runners/dsl/src/substrate.rs` | CLAUDE.md's binding rule names runners/dsl/src/py.rs as the handoff surface; the implementation calls live in runners/dsl/src/substrate.rs. |
| term-variant-grammar | `runners/dsl/src/term.rs`<br>`runners/dsl/src/grammar.rs`<br>`runners/dsl/src/checker.rs` | Term variants are defined in term.rs and parsed/checked by grammar.rs and checker.rs. |
| rule-fixpoint-rewrite | `runners/dsl/src/rewrite.rs`<br>`runners/dsl/src/graph_rules.rs` | The fixpoint loop is runners/dsl/src/rewrite.rs; rule matching/application is runners/dsl/src/graph_rules.rs. |
| seed-loader-topological | `substrate/seed_loader.py`<br>`tests/test_seed_loader_quiet_boot_migrated.py` | substrate/seed_loader.py resolves the manifest dependency closure; tests/test_seed_loader_quiet_boot_migrated.py covers quiet boot/loading behavior. |
| gap-awareness-unhandled-instruction | `substrate/world_adapter.py`<br>`domains/rule_signature.py`<br>`domains/solver_dispatch.py`<br>`tests/test_instruction_gap_migrated.py` | These source files contain literal seeds/gap_awareness.json references (rg -n 'seeds/gap_awareness\.json' on scripts/tools/substrate/tests/domains): world_adapter.py, rule_signature.py, solver_dispatch.py, and the instruction-gap gate. |
| shape-decode-reading-collapse | `domains/reading_collapse.py`<br>`domains/trope_theme.py`<br>`tests/test_sd_gen_rearm_tie_parity_migrated.py` | domains/reading_collapse.py and domains/trope_theme.py cite seeds/shape_decode_loop.json in their docstrings; the sd re-arm parity gate covers the sd loop behavior. |
| core-emotions-weighted-contribution | `domains/core_emotions_weight.py`<br>`substrate/boot_profiles.py`<br>`tests/test_core_emotions_migrated.py` | domains/core_emotions_weight.py is the shared quantization helper for seeds/core_emotions.json; substrate/boot_profiles.py lists core_emotions in the boot profile; test_core_emotions_migrated.py is the integer gate. |
| conversation-action-goal-binding | `domains/conversation_action.py`<br>`tests/test_conversation_action_goal_binding.py` | domains/conversation_action.py translates comprehension into an ACT/ASK-BACK and mints the Goal; the named gate asserts the binding. |
| dev-session-replay | `scripts/ocelot_dev_session.py`<br>`tests/test_dev_session_migrated.py` | scripts/ocelot_dev_session.py owns the replayable dev-session graph; tests/test_dev_session_migrated.py covers checkpoint/replay transitions. |
| frozen-core-boot-invariant | `substrate/boot_all.py`<br>`domains/frozen_core.py`<br>`tests/test_frozen_core_invariant.py` | substrate/boot_all.py enforces the frozen-seed refusal, domains/frozen_core.py defines the frozen set/closure, and tests/test_frozen_core_invariant.py is the gate. |

## Reading these numbers

- This is a **retrieval instrument**, not an end-to-end coding benchmark: it measures whether known-relevant files are selected, not whether an agent completes a change.
- `baseline` is a sorted-path file-listing control, not a semantic retriever.
- Token estimates are each module's own ~4-chars/token heuristic. Cache counts apply only to repo-map arms.
- `both` is the literal union of the two retrievers run at the same budget; its token cost and latency are the sum of the components, so its budget is per component (up to 2x the nominal budget). Compare it as a cost/recall trade-off, not as an equal-token arm.
- Ground truth is frozen in the task JSON. Re-run the scoped tests after moving or renaming an expected file.
