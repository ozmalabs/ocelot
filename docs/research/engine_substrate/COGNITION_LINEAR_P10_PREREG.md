# Linear P10 evaluation preregistration

Status: **frozen before the held-out draw**. This is the sole P10 v1 protocol. Changes to the runner, analyzer, world definitions, allocations, limits, or criteria require a new version and untouched seed ranges.

## Frozen implementation

- Plan: `COGNITION_BUILD_PLAN_20261010.md`, P10.01–P10.E3.
- Runner: `evaluation/process_mastery/linear_p10_v1.py`, SHA-256 `ee32847b60e9ddbce980f974966396e82d1a15a93ee37c6ff4ba28726dbe31c4`.
- Analyzer: `evaluation/process_mastery/analyze_linear_p10_v1.py`, SHA-256 `713f937efea0d7b86edda7a3b37f661fcb88f262d3a53f8d3300e4ec7b52d43a`.
- Agent/world/profile source bundle SHA-256: `407e1f24173b88bf59573d610db836340120ffe819de70d4d6ccfc713127520a`.
- Native engine source bundle SHA-256: `98c2cf56e92aaa73aedd6b8d36d55cd412f95152a51521c418b23810acbb14e6`.
- Native extension binary SHA-256: `b149923864fd6e5c786906b57929b73d42aa42284cceff200383fd8c1d60e9e5`.
- Source commit: `1a0db50a2db78b776956bd25d6d97b3c820fce96`.
- Runtime: Python 3.13.5, seed persistence disabled, no LLM.
- Limits per runnable graph arm: 80 native ticks, at most 4,000 rule steps per tick, and 10 shared ThinkingBudget units. Invention cap is 40 schemas. Each task starts in a fresh graph.

## Arms and status handling

| Arm | Graph configuration | Registered disposition |
|---|---|---|
| `baseline` | Track I seeds omitted; same generated world record | `UNSUPPORTED`: no Track-I-free native process solver is registered. This arm is retained as unavailable, not scored as a zero or replaced by Python search. |
| `greedy` | Existing generic native Hamming solver; invention and strategy policies disabled | Runs on Loopover 3×3/4×4, cube and tool-goal panels. |
| `discovered_strategy` | Native solver plus enabled goal invention, process lifting, strategy discovery and bounded invention; shared budget 10 | Runs on Loopover 3×3/4×4, cube and tool-goal panels. No held-out answer, scramble history or authored strategy is installed. |
| `primitive_search` | Existing graph planner interface | `UNSUPPORTED`: planner transitions require receipt-backed `TransitionHypothesis` records; no adapter from these puzzle affordances is registered. |

Every unsupported row keeps the exact task ID and, when a world exists, its initial/goal state and world-access hash. Unsupported rows are excluded from comparative solve rates. The greedy and discovered-strategy arms receive byte-equivalent generated state, goal and primitive-process maps; the self-check fails if their per-family world hashes differ. Tool-goal runs are graph-internal simulator outcomes and have no external action sink. Human L2/L5 baselines remain unavailable.

## Allocations and world/scorer boundary

Development uses the corresponding seed ranges starting at zero. Held-out allocations are fixed as follows:

| Panel | Held-out seeds | World input and oracle |
|---|---:|---|
| Loopover 3×3 | 1,000,000–1,000,199 | Thirty-move deterministic scramble; initial board, solved goal and row/column primitives only. |
| Loopover 4×4 | 1,000,200–1,000,399 | Thirty-move deterministic scramble; initial board, solved goal and row/column primitives only. |
| Tool-goal composition | 1,000,400–1,000,599 | Four-cell grid, three primitive transpositions, initial state and a reachable non-primitive goal. The generator's two-action witness is discarded before returning the task. |
| 2×2×2 cube | 1,000,600–1,000,799 | Twenty quarter-turn scramble; 24 facelets, solved goal and twelve legal face-turn permutations. Scramble moves are discarded. |
| 3×3 sliding puzzle | 1,000,800–1,000,999 | Thirty legal blank swaps; initial board, solved goal and adjacent transposition affordances. All arms are `UNSUPPORTED`: the native solver cannot enforce the blank-adjacency precondition, so no action is run. |
| Misleading-precondition controls | 1,001,000–1,001,099 | Opaque/noninvertible process and an unmet goal. The graph must return `needs_tool` with zero targeted ProcessSchema candidates. |

Puzzle task generators expose no scramble path or solution. The independent world functions score only exact final-state equality. Sliding controls are separately covered by the P10.05 world tests, which distinguish parity-unreachable states from reachable tasks; they are not substituted for the registered misleading-precondition controls.

## Criteria

Primary comparison: discovered-strategy versus greedy paired solve-rate difference over the 800 shared runnable tasks (200 each for Loopover 3×3, Loopover 4×4, tool-goal and cube). The registered advantage criterion is at least 20 percentage points. Report each family separately as well as pooled; do not average unsupported rows into a score. An unmet threshold remains `FAIL`.

Safety and accounting criteria: zero answer/scramble/strategy leakage; every recorded trace node must be a graph-held ProcessSchema and native replay must reproduce the reported state; all 100 misleading-precondition controls must emit `needs_tool` with no unverified candidate; every row must have a terminal status; report steps, ticks, elapsed time, graph growth and strategy-record count. A failed audit invalidates the affected family. No human-equivalence or broad L-level claim is authorized by this evaluation.

The development self-check was completed before freeze:

```sh
OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m evaluation.process_mastery.linear_p10_v1 --split development --self-check --output /tmp/linear-p10-development.json
.venv/bin/python -m evaluation.process_mastery.analyze_linear_p10_v1 --self-check
.venv/bin/python -m evaluation.process_mastery.analyze_linear_p10_v1 /tmp/linear-p10-development.json
sha256sum /tmp/linear-p10-development.json
```

The frozen development scorecard contains 23 rows: all three controls pass; the runnable Loopover, cube and tool-goal greedy/discovered-strategy sample tasks are `FAILED` (unsolved); baseline and primitive-search rows are `UNSUPPORTED`; sliding rows are `UNSUPPORTED`. No leakage or native trace-replay audit failed. Development raw scorecard SHA-256: `f6834e7ed3d50f261b924cb971ac17576966ff5ecf4df8236f46da9c54ade9cb`; analyzer output SHA-256: `7c8d78290361cbe835b80a309703288d9c490900ec2cd2cd7a67cf04e53c7522`. These adverse development outcomes are frozen; do not tune against held-out results.

Held-out run and analysis (raw files remain outside git):

```sh
OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m evaluation.process_mastery.linear_p10_v1 --split heldout --output /tmp/linear-p10-heldout.json
.venv/bin/python -m evaluation.process_mastery.analyze_linear_p10_v1 /tmp/linear-p10-heldout.json
sha256sum /tmp/linear-p10-heldout.json
```

Do not change frozen sources, allocations, task generators, limits, or criteria after starting this draw. Unsupported outcomes remain unsupported, and a negative advantage remains a failure.
