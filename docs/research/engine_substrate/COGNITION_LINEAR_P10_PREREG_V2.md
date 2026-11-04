# Linear P10 evaluation preregistration — V2 correction

Status: **frozen before the V2 held-out draw**. V2 supersedes V1 for the P10 comparison and uses untouched task ranges. V1 remains preserved as an invalidated run; its result is not pooled with V2.

## V1 invalidation record

The V1 held-out runner disabled `ProcessSchemaPolicy` in both runnable arms. `add_domain` therefore installed world source nodes but did not attach primitive schemas to their ProcessDomain; all 1,600 rows marked `greedy` or `discovered_strategy` had zero process steps and empty traces. V1 cannot answer the registered comparison. Its raw scorecard and analyzer hashes are retained: `db3767818b4d1149c2381354721762cb89a1947affc650fdf63d166445c0e217` and `eef45f361840a55d6bc17bc535824ab72dcf37d4bedd064c5e7da1287926c713`. No V1 seed is reused. The correction enables `ProcessSchemaPolicy` and adds a self-check that every supported arm installs the exact primitive affordance count before scoring.

## Frozen V2 implementation

- Plan: `COGNITION_BUILD_PLAN_20261010.md`, P10.01–P10.E3.
- Runner: `evaluation/process_mastery/linear_p10_v2.py`, SHA-256 `58bde4d96d109e68891b0ffd1ad9a01651841c016adf900536a3c280049f2a41`.
- Analyzer: `evaluation/process_mastery/analyze_linear_p10_v2.py`, SHA-256 `63754c428c912b939e22a958c2e39acd501959f2a43b89f6bb51dd2338a20a5b`.
- Agent/world/profile source bundle SHA-256: `21e3722b6ae56702fbe1ee68a599eed3f4b94ffd516b85e69e7ee7539f6544ea`.
- Native engine source bundle SHA-256: `98c2cf56e92aaa73aedd6b8d36d55cd412f95152a51521c418b23810acbb14e6`.
- Native extension binary SHA-256: `b149923864fd6e5c786906b57929b73d42aa42284cceff200383fd8c1d60e9e5`.
- Source commit: `94d400e621ae25d32583c79f12c35b34de4c577e`.
- Runtime: Python 3.13.5, seed persistence disabled, no LLM.
- Per runnable task: 20 native ticks, at most 1,000 rule steps per tick, 10 shared ThinkingBudget units.

`greedy` runs the existing generic native solver with ProcessSchemaPolicy enabled and invention/strategy policies disabled. `discovered_strategy` enables the native solver, schema views, targeted goal invention, and strategy discovery; the invention policy remains disabled until the approved targeted rung temporarily enables it. Process-family lifting is covered by its frozen mechanism tests but is not activated in these single-domain task arms because the runner supplies no paired source families from which to lift. All stored strategies still require exact context and current epochs.

The Track-I-free baseline is `UNSUPPORTED` because no native solver is registered without Track I. Primitive search is `UNSUPPORTED` because the planner needs receipt-backed TransitionHypothesis transitions, with no adapter from these affordances. Sliding remains `UNSUPPORTED` because the solver cannot enforce blank-adjacency preconditions. Tool-goal runs are graph-internal simulator outcomes, not external action receipts. These rows are retained and excluded from comparative solve rates.

## Fresh allocations and criteria

| Panel | Development allocation | V2 held-out allocation |
|---|---:|---:|
| Loopover 3×3 | 2,000,000–2,000,199 | 3,000,000–3,000,199 |
| Loopover 4×4 | 2,000,200–2,000,399 | 3,000,200–3,000,399 |
| Tool-goal composition | 2,000,400–2,000,599 | 3,000,400–3,000,599 |
| 2×2×2 cube | 2,000,600–2,000,799 | 3,000,600–3,000,799 |
| 3×3 sliding | 2,000,800–2,000,999 | 3,000,800–3,000,999 |
| Misleading-precondition controls | 2,001,000–2,001,099 | 3,001,000–3,001,099 |

All task definitions and scoring rules match V1: 30-move Loopover scrambles, two-action four-cell tool goals with the witness sequence discarded, 20-turn cube scrambles with the scramble discarded, and 30-move sliding scrambles. The agent receives only initial state, goal and declared primitive affordances. Every row reports a world-access hash. For supported runnable arms, the self-check verifies the same hash across arms, exact held-schema installation, absence of answer/scramble fields, and native replay of every trace to the reported state.

Primary comparison remains the paired discovered-strategy versus greedy solve-rate difference over 800 runnable tasks (200 each for Loopover 3×3/4×4, tool-goal and cube). The registered advantage criterion is at least 20 percentage points. Report each family separately and pooled. Any lower gain is `FAIL`. All 100 controls must return `needs_tool` with zero targeted candidates. Report steps, ticks, elapsed time, graph growth, strategy count, trace integrity and input exposure. Per-process allocator memory and boot-only time are unavailable in the harness; elapsed time includes world construction, graph boot and ticking. Human L2/L5 baselines remain unavailable.

V2 development self-check, completed before freeze:

```sh
OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m evaluation.process_mastery.linear_p10_v2 --split development --self-check --output /tmp/linear-p10-v2-development.json
.venv/bin/python -m evaluation.process_mastery.analyze_linear_p10_v2 --self-check
.venv/bin/python -m evaluation.process_mastery.analyze_linear_p10_v2 /tmp/linear-p10-v2-development.json
sha256sum /tmp/linear-p10-v2-development.json
```

The 23 development rows show: tool-goal greedy 1/1 and discovered-strategy 1/1 solved; Loopover and cube greedy/discovered sample tasks unsolved; 3/3 misleading-precondition controls pass; baseline/primitive-search/sliding are explicit `UNSUPPORTED`; all supported rows confirm primitive installation and zero trace/input audit failures. Raw development scorecard SHA-256: `1514550d2df274cd6223370c1a2f500643b4ac6b461674c843c3b6a6729ab75f`; analysis SHA-256: `1369affe8e78488c11017c06eef172a328bb47cca05f013c21c5bb3bd3fb5065`. These outcomes are frozen before V2 held-out execution.

Held-out execution (raw outputs remain outside git):

```sh
OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m evaluation.process_mastery.linear_p10_v2 --split heldout --output /tmp/linear-p10-v2-heldout.json
.venv/bin/python -m evaluation.process_mastery.analyze_linear_p10_v2 /tmp/linear-p10-v2-heldout.json
sha256sum /tmp/linear-p10-v2-heldout.json
```

No source, world, limit, allocation, or criterion may change after this draw starts. Unsupported outcomes remain unsupported and failed advantage criteria remain failures.
