# Repo-map retrieval evaluation

**Status:** landed 2026-11-14 (Workstream B of
[`ADVANCED_CODING_AGENT_PLAN.md`](ADVANCED_CODING_AGENT_PLAN.md)).
**Files:** `scripts/ocelot_repo_map_eval.py`,
`tests/test_repo_map_eval_migrated.py`,
`evaluation/repo_map/tasks.json`, this document, and the generated
[`evaluation/repo_map/RESULTS.md`](../../evaluation/repo_map/RESULTS.md).

This is a **deterministic, offline retrieval instrument** for the repo map. It
answers a narrow question: for a fixed task and token budget, which files do
the retrieval arms select, and how many of the explicitly known-relevant files
do they recover? It does not run an LLM, call the network, or edit source.

It is not an end-to-end coding benchmark. File recall is a prerequisite for a
coding agent, not evidence that the agent completes the change correctly.

## Task set

`evaluation/repo_map/tasks.json` contains 21 tasks. Every entry has:

```json
{
  "id": "repo-map-tag-cache",
  "task": "Make the repo-map tag cache reuse unchanged files and reparse only changed content using content hashes.",
  "expected_files": ["scripts/ocelot_repo_map.py", "tests/test_repo_map_migrated.py"],
  "notes": "How this ground truth was derived."
}
```

### Construction method

Ground truth was **curated at authoring time from repository facts**, then
frozen in the JSON:

- module docstrings and primary implementations (for example
  `scripts/ocelot_repo_map.py` for the three-tier render, tag cache, and
  PageRank);
- literal `seeds/<id>.json` references found with targeted ripgrep over
  `scripts/`, `tools/`, `substrate/`, `tests/`, `domains/`, `runners/`, and
  `worlds/` (for example `rg -n 'seeds/gap_awareness\.json' ...`), followed by
  selecting the implementation and gate sites rather than every incidental
  mention;
- the matching `tests/test_*_migrated.py` gates where the task is a behavior
  change;
- the `docs/CODE_MAP.md` role descriptions and top-level module boundaries.

The harness **never** re-derives `expected_files` from seeds, symbols, source
text, or retrieval results. At load time it only:

1. validates that each path is repository-relative and that the file exists;
2. reports any expected file that is outside the indexed source-file universe
   (the repo map indexes `.py`, `.rs`, `.lua` under its `SOURCE_DIRS`).

This validation catches drift after a move or rename. It is not inference; the
expected list is already fixed in the JSON. The task set deliberately keeps
only source files as ground truth, because the baseline listing and
`dev_repo_map` cannot select docs, manifests, or generated data.

The set covers the dev-tooling layer (repo map, dev memory, edit adapters),
the Rust substrate (`term`, `grammar`, `checker`, `rewrite`, PyO3), seed
loading/boot behavior, and a few seed-driven domain rules. It is intentionally
small and curated, not a random sample of the 6,800+ indexed source files.

To add a task, add the explicit paths and a note describing the evidence, then
re-run the scoped tests. Do not derive expected files inside the harness.

## Arms

Each task is evaluated at **500, 900, and 1500 tokens** in four arms:

| Arm | What is selected | Token cost |
|---|---|---|
| `baseline` | First source files by globally sorted path, rendered as a plain listing | Listing characters / 4 |
| `dev_context` | Files from `DevMemory.context(task, budget_tokens=...)` items and snippets | `budget.estimated_tokens` |
| `dev_repo_map` | Files from `repo_map(root, task=..., budget_tokens=...)` | `estimated_tokens` |
| `both` | Literal union: context files first, then map files not already present | Sum of the two component estimates |

`dev_context` and `dev_repo_map` are executed once per `(task, budget)`.
`both` reuses those two results, so its latency and token cost are the sum of
the components. **The budget is applied to each retrieval component, not to
the union**; `both` can therefore cost up to 2x the nominal budget. This is
reported honestly rather than hidden by trimming one side.

The baseline is a control, not a semantic retriever. Its path-prefix ordering
means it has near-zero recall for most tasks, which is the expected control
result and makes the map/context lift visible.

## Metrics

For each run:

- **recall** = `|expected ∩ selected| / |expected|`
- **precision** = `|expected ∩ selected| / |selected|`
- **selected_count** = unique files in the arm's file set
- **estimated_tokens** = the arm's own ~4-chars/token estimate
- **elapsed_seconds** = retrieval wall time for that arm/component
- **cache parsed / reused** = repo-map tag-cache counters (not applicable to
  baseline and context; `both` reports its map component)

The aggregate table reports the mean of each metric per `(budget, arm)`,
plus totals for cache parsed/reused, the number of runs within budget, and the
number of tasks with recall 1.0. `mean_recall_at_budget` is the mean file
recall at that budget.

Because the benchmark is small, treat differences as a regression signal, not
as statistical evidence.

## CLI

Prerequisites:

- a dev-memory snapshot at `<root>/var/ocelot_dev_graph.json`
  (`.venv/bin/python -m scripts.ocelot_dev_memory build`), needed by the
  context and both arms;
- a writable tag-cache path. The default is
  `<root>/var/ocelot_repo_map_eval_tags.json`.

Run the full set:

```bash
.venv/bin/python -m scripts.ocelot_repo_map_eval \
  --tasks evaluation/repo_map/tasks.json \
  --json-out /tmp/opencode/repo_map_eval.json \
  --markdown-out evaluation/repo_map/RESULTS.md
```

Useful options:

```text
--root PATH          repository to evaluate (default: this checkout)
--tasks PATH         explicit task JSON
--budgets 500,900    token budgets (default: 500,900,1500)
--arms ...           subset of baseline,dev_context,dev_repo_map,both
--cache PATH         repo-map tag cache
--memory PATH        dev-memory snapshot
--limit N            first N tasks only, for a quick smoke run
--json-out PATH      write the full JSON report
--markdown-out PATH  write the human report
--json               print JSON instead of markdown when no path is given
```

If neither output path is given, the markdown report is printed. A quick
run that needs no dev-memory snapshot:

```bash
.venv/bin/python -m scripts.ocelot_repo_map_eval \
  --tasks evaluation/repo_map/tasks.json --budgets 500 \
  --arms baseline,dev_repo_map --limit 5
```

The JSON report contains `tasks`, `runs`, `aggregates`,
`deterministic_fingerprint`, `total_elapsed_seconds`, the arm descriptions,
and the selected files/hits/misses per run.

## Determinism

- Source files are globally sorted; tasks keep their JSON order; budgets are
  sorted and de-duplicated; arms use the canonical
  `baseline, dev_context, dev_repo_map, both` order.
- No LLM, embeddings, network, or wall-clock-dependent selection is involved.
- `deterministic_fingerprint` hashes the task/budget/arm/file/recall/
  precision/token projection. It excludes elapsed time and cache
  parsed/reused counts, which legitimately vary with cache warmth and machine
  load. The scoped test runs the same fixture twice with separate caches and
  asserts equal fingerprints.
- Running with a warm cache can change the parsed/reused counters and latency,
  but not the selected file sets or the fingerprint.

## Tests

```bash
.venv/bin/python -m pytest tests/test_repo_map_eval_migrated.py -q
```

The tests build a tiny fixture repository and a tiny dev-memory snapshot. They
assert: explicit tasks load; the ranked map puts the task-named file first and
recall is 1.0; per-component budgets are respected; every arm is labelled;
the union/both cost is reported correctly; the baseline is a budgeted path
prefix; markdown labels every arm/task; missing ground-truth files fail loudly;
and two runs have the same deterministic fingerprint. There is no real-repo,
network, or LLM dependency.

## Result on this checkout (2026-11-14)

21 tasks, 252 runs, 6,826 indexed source files. Wall time 575.8 s (includes
cold/index cost); fingerprint
`ae5b33c23fa204249e54921f5204c7970d9e107c0e00784810a7a0e2c32340f4`.

| Budget | Arm | Mean recall@budget | Mean precision | Mean files | Mean tokens |
|---:|---|---:|---:|---:|---:|
| 500 | baseline | 0.000 | 0.000 | 70.0 | 496 |
| 500 | dev_context | 0.103 | 0.214 | 1.3 | 474 |
| 500 | dev_repo_map | **0.401** | 0.191 | 4.8 | 469 |
| 500 | both | **0.464** | 0.192 | 6.0 | 944 |
| 900 | baseline | 0.000 | 0.000 | 127.0 | 893 |
| 900 | dev_context | 0.119 | 0.155 | 2.2 | 663 |
| 900 | dev_repo_map | **0.409** | 0.221 | 4.5 | 861 |
| 900 | both | **0.488** | 0.190 | 6.6 | 1,524 |
| 1500 | baseline | 0.040 | 0.000 | 205.0 | 1,498 |
| 1500 | dev_context | 0.218 | 0.132 | 4.5 | 1,246 |
| 1500 | dev_repo_map | **0.623** | 0.066 | 24.7 | 1,491 |
| 1500 | both | **0.675** | 0.063 | 28.2 | 2,737 |

Reading the result:

- The map has a large recall lift over the path-prefix control at every
  budget, and the steepest gain is at 1500 tokens (0.040 → 0.623).
- Context is cheap and precise at small budgets but selects few files; its
  recall rises slowly with budget.
- The union adds only ~0.05–0.07 recall over the map alone at 500/900 and
  costs roughly twice the tokens. At 1500 the union gain is ~0.05 for ~1.8x
  tokens. On this set it is a cost/recall trade-off, not a free win.
- Map precision falls at 1500 because the renderer admits ~25 files per task.
  File recall is the primary metric here; precision matters more when the
  retrieved context is injected into a model prompt.
- Some tasks remain at 0.0 recall even at 1500 (for example
  `dev-context-pack`), and some are only recovered at the largest budget.
  The task text does not always contain the exact identifier or path token;
  these misses are reported rather than tuned away.
- Cache parsed/reused counts in `RESULTS.md` are summed over runs and reflect
  the shared cache warming up; they are not unique-file counts.

Full per-task numbers are in
[`evaluation/repo_map/RESULTS.md`](../../evaluation/repo_map/RESULTS.md).

## Integration notes

The harness is intentionally standalone and makes **no edits to shared
files** (`ocelot_repo_map.py`, `ocelot_dev_memory*.py`, MCP docs, code map,
requirements, or `.opencode/`). It exposes a plain Python API:

```python
from scripts.ocelot_repo_map_eval import evaluate
report = evaluate(root, tasks_path=..., budgets=[500, 900, 1500])
report["aggregates"]
report["deterministic_fingerprint"]
```

Suggested central-integrator wiring, if desired:

- CLI verb `repo-map-eval` (or a documented standalone command) delegating to
  `main()`;
- an optional MCP tool `dev_repo_map_eval` that accepts `tasks`, `budgets`,
  `arms`, and `limit` and returns the aggregate rows + fingerprint (not the
  full per-run JSON by default);
- do **not** put a full evaluation on an agent hot path: the real-repo run is
  minutes long and touches the 200 MB-class tag cache. Default MCP use should
  be `limit`-bounded or restricted to `baseline,dev_repo_map`.

## Limitations

- **Retrieval instrument, not an end-to-end coding benchmark.** It measures
  whether known files are selected. It does not measure edit correctness, test
  pass rate, regressions, tool calls, or answer quality.
- **Manual/frozen ground truth.** Twenty-one curated tasks are enough to catch
  obvious retrieval regressions, not to establish general superiority. The
  set is biased toward dev tooling, the Rust substrate, and seed/boot paths.
- **Source-only ground truth.** The repo map indexes `.py/.rs/.lua` under its
  source directories. Docs, seed JSON, and generated data are excluded from
  expected files. A context item that points at a seed manifest is a selected
  file but not a hit; this is visible in precision.
- **Heuristic tokens.** All estimates are ~4 characters/token, not a real
  tokenizer. They are consistent across arms but not exact model tokens.
- **`both` is a 2x-budget union.** Its budget applies per component. Do not
  compare it as an equal-token arm without normalizing cost.
- **Syntactic, file-level retrieval.** Repo-map edges are tree-sitter/AST
  heuristics, not LSP/SCIP-resolved. High recall does not prove the selected
  file is the semantically right edit site.
- **Cache and timing variability.** Cache counters and elapsed seconds depend
  on cache warmth and machine load. The deterministic fingerprint intentionally
  excludes them.
- **Fixture tests prove harness mechanics, not retrieval quality.** The
  fixture is tiny; the real-repo result above is the retrieval evidence.
