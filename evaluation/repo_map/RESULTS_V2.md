# Repo-map retrieval evaluation

- Root: `/applications/data/projects/ocelot/.worktrees/dt-w3a-eval-v2`
- Tasks: 30 (`/applications/data/projects/ocelot/.worktrees/dt-w3a-eval-v2/evaluation/repo_map/tasks_v2.json`)
- Source-file universe: 6805
- Budgets: 500, 900, 1500 tokens
- Arms: baseline, dev_context, dev_repo_map, both, grep, code_search
- Dev-memory snapshot: stale=False (snapshot head `a6df57f0d4b594564d993495d6d38a1b1be3170f`, HEAD `a6df57f0d4b594564d993495d6d38a1b1be3170f`, root mismatch False, allow_stale=False)
- Deterministic fingerprint: `c745f6d2fdee953bcc472cb1ada8b031141469e979596a347f5a41ea34e786d8`
- Wall time: 329.232 s

## Aggregate metrics

| Budget | Arm | Tasks | Mean recall@budget | Mean recall (content tier) | Mean precision | Mean files | Mean content files | Mean tokens | Mean s | Cache parsed | Cache reused |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 500 | baseline | 30 | 0.000 | 0.000 | 0.000 | 70.0 | 0.0 | 496 | 0.00 | 0 | 0 |
| 500 | dev_context | 30 | 0.017 | 0.017 | 0.008 | 1.6 | 1.4 | 503 | 1.57 | 0 | 0 |
| 500 | dev_repo_map | 30 | 0.283 | 0.283 | 0.079 | 3.4 | 3.4 | 466 | 0.26 | 0 | 204150 |
| 500 | both | 30 | 0.283 | 0.283 | 0.052 | 4.9 | 4.8 | 970 | 1.83 | 0 | 204150 |
| 500 | grep | 30 | 0.700 | 0.000 | 0.012 | 61.5 | 0.0 | 496 | 1.17 | 0 | 0 |
| 500 | code_search | 30 | 0.717 | 0.717 | 0.045 | 17.4 | 17.4 | 484 | 4.33 | 0 | 0 |
| 900 | baseline | 30 | 0.000 | 0.000 | 0.000 | 127.0 | 0.0 | 893 | 0.00 | 0 | 0 |
| 900 | dev_context | 30 | 0.083 | 0.083 | 0.018 | 3.1 | 2.8 | 722 | 1.49 | 0 | 0 |
| 900 | dev_repo_map | 30 | 0.250 | 0.250 | 0.059 | 4.0 | 4.0 | 847 | 0.27 | 0 | 204150 |
| 900 | both | 30 | 0.283 | 0.283 | 0.038 | 6.9 | 6.6 | 1569 | 1.77 | 0 | 204150 |
| 900 | grep | 30 | 0.833 | 0.000 | 0.008 | 108.9 | 0.0 | 896 | 1.17 | 0 | 0 |
| 900 | code_search | 30 | 0.817 | 0.817 | 0.028 | 31.5 | 31.5 | 888 | 4.33 | 0 | 0 |
| 1500 | baseline | 30 | 0.067 | 0.000 | 0.000 | 205.0 | 0.0 | 1498 | 0.00 | 0 | 0 |
| 1500 | dev_context | 30 | 0.083 | 0.083 | 0.016 | 4.4 | 4.0 | 1063 | 1.50 | 0 | 0 |
| 1500 | dev_repo_map | 30 | 0.467 | 0.383 | 0.026 | 20.5 | 11.8 | 1488 | 0.26 | 0 | 204150 |
| 1500 | both | 30 | 0.467 | 0.383 | 0.022 | 24.4 | 15.3 | 2551 | 1.76 | 0 | 204150 |
| 1500 | grep | 30 | 0.900 | 0.000 | 0.005 | 177.7 | 0.0 | 1496 | 1.17 | 0 | 0 |
| 1500 | code_search | 30 | 0.933 | 0.933 | 0.020 | 49.5 | 49.5 | 1408 | 4.33 | 0 | 0 |

## Recall by task

Each cell is `recall (recall_content)`.

### 500 tokens

| Task | baseline | dev_context | dev_repo_map | both | grep | code_search |
|---|---:|---:|---:|---:|---:|---:|
| repo-map-same-second-tag-cache | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 1.00 (0.00) | 1.00 (1.00) |
| json-manifest-value-edit | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 1.00 (0.00) | 1.00 (1.00) |
| markdown-section-replace | 0.00 (0.00) | 0.00 (0.00) | 1.00 (1.00) | 1.00 (1.00) | 1.00 (0.00) | 1.00 (1.00) |
| dev-context-budget-stop | 0.00 (0.00) | 0.00 (0.00) | 1.00 (1.00) | 1.00 (1.00) | 1.00 (0.00) | 1.00 (1.00) |
| pagerank-tie-order | 0.00 (0.00) | 0.00 (0.00) | 1.00 (1.00) | 1.00 (1.00) | 1.00 (0.00) | 1.00 (1.00) |
| code-search-matched-terms | 0.00 (0.00) | 0.00 (0.00) | 1.00 (1.00) | 1.00 (1.00) | 1.00 (0.00) | 1.00 (1.00) |
| dev-session-replay | 0.00 (0.00) | 0.00 (0.00) | 1.00 (1.00) | 1.00 (1.00) | 1.00 (0.00) | 0.00 (0.00) |
| symbol-graph-import-resolution | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 1.00 (0.00) | 1.00 (1.00) |
| cow-branch-isolation | 0.00 (0.00) | 0.00 (0.00) | 1.00 (1.00) | 1.00 (1.00) | 1.00 (0.00) | 1.00 (1.00) |
| rule-run-stopping-point | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 1.00 (0.00) | 0.00 (0.00) |
| edge-refusal-reason | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 1.00 (1.00) |
| reflex-skip-report | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) |
| residual-decoder-parity | 0.00 (0.00) | 0.00 (0.00) | 1.00 (1.00) | 1.00 (1.00) | 1.00 (0.00) | 1.00 (1.00) |
| run-rules-report-cycle-flag | 0.00 (0.00) | 0.00 (0.00) | 1.00 (1.00) | 1.00 (1.00) | 1.00 (0.00) | 1.00 (1.00) |
| eq-variant-operands | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 1.00 (0.00) | 0.00 (0.00) |
| persist-value-roundtrip | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) |
| rule-json-roundtrip | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 1.00 (0.00) | 0.00 (0.00) |
| boot-dependency-order | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 1.00 (0.00) | 1.00 (1.00) |
| frozen-core-manifest-check | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 1.00 (0.00) | 1.00 (1.00) |
| boot-profile-closure | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 1.00 (0.00) | 1.00 (1.00) |
| core-emotions-integer-contribution | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 1.00 (1.00) |
| conversation-action-goal-binding | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) |
| solver-exhausted-gap | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 1.00 (1.00) |
| reading-mints-quantum-rules | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 1.00 (0.00) | 1.00 (1.00) |
| term-variant-regeneration | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.50 (0.50) |
| ts-trivia-leaves | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 1.00 (0.00) | 1.00 (1.00) |
| python-cst-lossless-leaves | 0.00 (0.00) | 0.50 (0.50) | 0.50 (0.50) | 0.50 (0.50) | 1.00 (0.00) | 1.00 (1.00) |
| persistence-node-ids | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 1.00 (1.00) |
| admissibility-check-no-bypass | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) |
| grid-game-frames-to-cells | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 1.00 (0.00) | 1.00 (1.00) |

### 900 tokens

| Task | baseline | dev_context | dev_repo_map | both | grep | code_search |
|---|---:|---:|---:|---:|---:|---:|
| repo-map-same-second-tag-cache | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 1.00 (0.00) | 1.00 (1.00) |
| json-manifest-value-edit | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 1.00 (0.00) | 1.00 (1.00) |
| markdown-section-replace | 0.00 (0.00) | 1.00 (1.00) | 1.00 (1.00) | 1.00 (1.00) | 1.00 (0.00) | 1.00 (1.00) |
| dev-context-budget-stop | 0.00 (0.00) | 0.00 (0.00) | 1.00 (1.00) | 1.00 (1.00) | 1.00 (0.00) | 1.00 (1.00) |
| pagerank-tie-order | 0.00 (0.00) | 0.00 (0.00) | 1.00 (1.00) | 1.00 (1.00) | 1.00 (0.00) | 1.00 (1.00) |
| code-search-matched-terms | 0.00 (0.00) | 0.00 (0.00) | 1.00 (1.00) | 1.00 (1.00) | 1.00 (0.00) | 1.00 (1.00) |
| dev-session-replay | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 1.00 (0.00) | 1.00 (1.00) |
| symbol-graph-import-resolution | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 1.00 (0.00) | 1.00 (1.00) |
| cow-branch-isolation | 0.00 (0.00) | 0.00 (0.00) | 1.00 (1.00) | 1.00 (1.00) | 1.00 (0.00) | 1.00 (1.00) |
| rule-run-stopping-point | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 1.00 (0.00) | 0.00 (0.00) |
| edge-refusal-reason | 0.00 (0.00) | 1.00 (1.00) | 0.00 (0.00) | 1.00 (1.00) | 1.00 (0.00) | 1.00 (1.00) |
| reflex-skip-report | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) |
| residual-decoder-parity | 0.00 (0.00) | 0.00 (0.00) | 1.00 (1.00) | 1.00 (1.00) | 1.00 (0.00) | 1.00 (1.00) |
| run-rules-report-cycle-flag | 0.00 (0.00) | 0.00 (0.00) | 1.00 (1.00) | 1.00 (1.00) | 1.00 (0.00) | 1.00 (1.00) |
| eq-variant-operands | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 1.00 (0.00) | 1.00 (1.00) |
| persist-value-roundtrip | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 1.00 (0.00) | 0.00 (0.00) |
| rule-json-roundtrip | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 1.00 (0.00) | 0.00 (0.00) |
| boot-dependency-order | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 1.00 (0.00) | 1.00 (1.00) |
| frozen-core-manifest-check | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 1.00 (0.00) | 1.00 (1.00) |
| boot-profile-closure | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 1.00 (0.00) | 1.00 (1.00) |
| core-emotions-integer-contribution | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 1.00 (0.00) | 1.00 (1.00) |
| conversation-action-goal-binding | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) |
| solver-exhausted-gap | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 1.00 (0.00) | 1.00 (1.00) |
| reading-mints-quantum-rules | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 1.00 (0.00) | 1.00 (1.00) |
| term-variant-regeneration | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.50 (0.50) |
| ts-trivia-leaves | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 1.00 (0.00) | 1.00 (1.00) |
| python-cst-lossless-leaves | 0.00 (0.00) | 0.50 (0.50) | 0.50 (0.50) | 0.50 (0.50) | 1.00 (0.00) | 1.00 (1.00) |
| persistence-node-ids | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 1.00 (1.00) |
| admissibility-check-no-bypass | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 1.00 (1.00) |
| grid-game-frames-to-cells | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 1.00 (0.00) | 1.00 (1.00) |

### 1500 tokens

| Task | baseline | dev_context | dev_repo_map | both | grep | code_search |
|---|---:|---:|---:|---:|---:|---:|
| repo-map-same-second-tag-cache | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 1.00 (0.00) | 1.00 (1.00) |
| json-manifest-value-edit | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 1.00 (0.00) | 1.00 (1.00) |
| markdown-section-replace | 0.00 (0.00) | 1.00 (1.00) | 1.00 (1.00) | 1.00 (1.00) | 1.00 (0.00) | 1.00 (1.00) |
| dev-context-budget-stop | 0.00 (0.00) | 0.00 (0.00) | 1.00 (1.00) | 1.00 (1.00) | 1.00 (0.00) | 1.00 (1.00) |
| pagerank-tie-order | 0.00 (0.00) | 0.00 (0.00) | 1.00 (1.00) | 1.00 (1.00) | 1.00 (0.00) | 1.00 (1.00) |
| code-search-matched-terms | 0.00 (0.00) | 0.00 (0.00) | 1.00 (1.00) | 1.00 (1.00) | 1.00 (0.00) | 1.00 (1.00) |
| dev-session-replay | 0.00 (0.00) | 0.00 (0.00) | 1.00 (1.00) | 1.00 (1.00) | 1.00 (0.00) | 1.00 (1.00) |
| symbol-graph-import-resolution | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 1.00 (0.00) | 1.00 (1.00) |
| cow-branch-isolation | 0.00 (0.00) | 0.00 (0.00) | 1.00 (1.00) | 1.00 (1.00) | 1.00 (0.00) | 1.00 (1.00) |
| rule-run-stopping-point | 0.00 (0.00) | 0.00 (0.00) | 1.00 (1.00) | 1.00 (1.00) | 1.00 (0.00) | 1.00 (1.00) |
| edge-refusal-reason | 0.00 (0.00) | 1.00 (1.00) | 1.00 (1.00) | 1.00 (1.00) | 1.00 (0.00) | 1.00 (1.00) |
| reflex-skip-report | 0.00 (0.00) | 0.00 (0.00) | 1.00 (0.00) | 1.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) |
| residual-decoder-parity | 0.00 (0.00) | 0.00 (0.00) | 1.00 (1.00) | 1.00 (1.00) | 1.00 (0.00) | 1.00 (1.00) |
| run-rules-report-cycle-flag | 0.00 (0.00) | 0.00 (0.00) | 1.00 (1.00) | 1.00 (1.00) | 1.00 (0.00) | 1.00 (1.00) |
| eq-variant-operands | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 1.00 (0.00) | 1.00 (1.00) |
| persist-value-roundtrip | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 1.00 (0.00) | 0.00 (0.00) |
| rule-json-roundtrip | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 1.00 (0.00) | 1.00 (1.00) |
| boot-dependency-order | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 1.00 (0.00) | 1.00 (1.00) |
| frozen-core-manifest-check | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 1.00 (0.00) | 1.00 (1.00) |
| boot-profile-closure | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 1.00 (0.00) | 1.00 (1.00) |
| core-emotions-integer-contribution | 1.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 1.00 (0.00) | 1.00 (1.00) |
| conversation-action-goal-binding | 1.00 (0.00) | 0.00 (0.00) | 1.00 (0.00) | 1.00 (0.00) | 1.00 (0.00) | 1.00 (1.00) |
| solver-exhausted-gap | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 1.00 (0.00) | 1.00 (1.00) |
| reading-mints-quantum-rules | 0.00 (0.00) | 0.00 (0.00) | 1.00 (1.00) | 1.00 (1.00) | 1.00 (0.00) | 1.00 (1.00) |
| term-variant-regeneration | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 1.00 (1.00) |
| ts-trivia-leaves | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 1.00 (0.00) | 1.00 (1.00) |
| python-cst-lossless-leaves | 0.00 (0.00) | 0.50 (0.50) | 1.00 (0.50) | 1.00 (0.50) | 1.00 (0.00) | 1.00 (1.00) |
| persistence-node-ids | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 1.00 (0.00) | 1.00 (1.00) |
| admissibility-check-no-bypass | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 1.00 (1.00) |
| grid-game-frames-to-cells | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 0.00 (0.00) | 1.00 (0.00) | 1.00 (1.00) |

## Task set

| Task | Style | Area | Expected files | Notes |
|---|---|---|---|---|
| repo-map-same-second-tag-cache | symptom | dev_tooling | `scripts/ocelot_repo_map.py` | Freshness check for cached tags and the racy-timestamp window. |
| json-manifest-value-edit | symptom | dev_tooling | `scripts/ocelot_json_edit.py` | Span-preserving JSON value replacement. |
| markdown-section-replace | symptom | dev_tooling | `scripts/ocelot_markdown_edit.py` | Section replacement operations on Markdown blocks. |
| dev-context-budget-stop | identifier | dev_tooling | `scripts/ocelot_dev_memory.py` | Budget loop of the context pack. |
| pagerank-tie-order | identifier | dev_tooling | `scripts/ocelot_repo_map.py` | Personalized PageRank over the candidate subgraph. |
| code-search-matched-terms | identifier | dev_tooling | `scripts/ocelot_code_search.py` | BM25 plus PageRank fusion and result rendering. |
| dev-session-replay | symptom | dev_tooling | `scripts/ocelot_dev_session.py` | Replayable dev-session state graph. |
| symbol-graph-import-resolution | symptom | dev_tooling | `scripts/ocelot_symbol_graph.py` | Import-aware symbol resolution levels. |
| cow-branch-isolation | symptom | rust_engine | `runners/dsl/src/cow_paged_vec.rs` | Copy-on-write paged vector for snapshot forks. |
| rule-run-stopping-point | symptom | rust_engine | `runners/dsl/src/rewrite.rs` | Fixed-point runner over rule passes. |
| edge-refusal-reason | symptom | rust_engine | `runners/dsl/src/checker.rs` | Type-1 and Type-2 failure modes of the admissibility check. |
| reflex-skip-report | symptom | rust_engine | `runners/dsl/src/seed_manifest.rs` | Load summary counts and skipped-reflex reasons. |
| residual-decoder-parity | symptom | rust_engine | `runners/dsl/src/shape_decode.rs` | Parity contract with the Python composer and its tie-break. |
| run-rules-report-cycle-flag | identifier | rust_engine | `runners/dsl/src/substrate.rs` | Rule-run report with cycle detection. |
| eq-variant-operands | identifier | rust_engine | `runners/dsl/src/term.rs` | Evaluator arm for the equality node. |
| persist-value-roundtrip | symptom | rust_engine | `runners/dsl/src/persist.rs` | Value encoding and decoding for saved graphs. |
| rule-json-roundtrip | symptom | rust_engine | `runners/dsl/src/rule_json.rs` | Rule wire format serialisation and parsing. |
| boot-dependency-order | symptom | seeds_boot | `substrate/boot_all.py` | Dependency ordering of the full seed boot. |
| frozen-core-manifest-check | symptom | seeds_boot | `domains/frozen_core.py` | Safety-invariant frozen set cross-checked with a pinned manifest. |
| boot-profile-closure | symptom | seeds_boot | `substrate/boot_profiles.py` | Connected-seed profiles and closure validation. |
| core-emotions-integer-contribution | symptom | domains | `domains/core_emotions_weight.py` | Integer lattice quantisation for the core emotions rule. |
| conversation-action-goal-binding | symptom | domains | `domains/conversation_action.py` | Turns an accepted conversational intent into a minted goal. |
| solver-exhausted-gap | symptom | domains | `domains/solver_dispatch.py` | Solver outcomes recorded as gap keys. |
| reading-mints-quantum-rules | symptom | domains | `domains/reading_collapse.py` | Reading collapse onto the sd loop rules. |
| term-variant-regeneration | symptom | worlds_or_tools | `tools/gen_term_variants.py`<br>`runners/dsl/src/term_variants.rs` | Generator and generated index for the TermNode enum. |
| ts-trivia-leaves | symptom | domains | `domains/ts_ingest.py` | Lossless mode inserts trivia leaves for byte gaps. |
| python-cst-lossless-leaves | symptom | domains | `domains/py_cst_ingest.py`<br>`scripts/ocelot_lossless.py` | Token and trivia leaves under every format. |
| persistence-node-ids | symptom | substrate | `substrate/persistence.py` | Graph save and load that preserves node ids. |
| admissibility-check-no-bypass | symptom | substrate | `substrate/checker.py` | Consistency checker in front of every edge write. |
| grid-game-frames-to-cells | symptom | worlds_or_tools | `worlds/arc.py` | Frame to substrate mutation adapter for the grid game. |

## Reading these numbers

- This is a **retrieval instrument**, not an end-to-end coding benchmark: it measures whether known-relevant files are selected, not whether an agent completes a change.
- `baseline` is a sorted-path file-listing control, not a semantic retriever. `grep` is a lexical control: it counts distinct task words found in each file's text.
- `recall` counts a hit at any tier. `recall_content` counts only hits whose file the arm showed as code (code_search snippet, dev_context item with snippet text, or repo-map `full`/`outline` tier). A listing-tier hit tells the reader the path exists, not what it contains.
- Token estimates are each module's own ~4-chars/token heuristic. Cache counts apply only to repo-map arms.
- `both` is the literal union of the two retrievers run at the same budget; its token cost and latency are the sum of the components, so its budget is per component (up to 2x the nominal budget). Compare it as a cost/recall trade-off, not as an equal-token arm.
- `code_search` runs once per task; its elapsed time is the same call's time at every budget.
- Ground truth is frozen in the task JSON. Re-run the scoped tests after moving or renaming an expected file.
