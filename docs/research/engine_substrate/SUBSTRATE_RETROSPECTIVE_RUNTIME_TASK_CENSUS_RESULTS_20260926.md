# Retrospective runtime task graph and rule-work census (2026-09-26)

## Scope

This is a retrospective reanalysis of the existing [connected discourse task census](SUBSTRATE_DISCOURSE_CONNECTED_TASK_CENSUS_RESULTS_20260926.md), not a new runtime capture. It independently recomputes graph structure and aggregates the recorded native counters for the same ten-event fixture in three arms (plain, trace, repeat). The three arms are repeated executions of one authored task, not three independent tasks.

The original lock and raw report agree, and the input fixture and rule seed are recoverable from the recorded commit. The original run had a dirty worktree: the materializer and `py.rs` source are not recoverable at their locked hashes from the commit or current tree, and the native binary hash also differs from the current binary. Those source gaps are recorded in the analysis output. Consequently, this report audits the stored graph/counter evidence but cannot claim a full source-identical runtime reproduction.

## Structural findings

Each arm has the same graph digest: 261 nodes and 235 directed edges. The full graph is mostly low-degree: weak-degree median 1, p90 4, p95 6, maximum 35. The maximum-degree node is an unframed `Lexicon`; the next highest are global Agent, Interlocutor, and DiscourseState nodes. This shows why whole-graph degree alone is a poor proxy for task-frame width: global vocabulary and discourse infrastructure dominate the tail.

The fixture assigns 12 event/goal nodes to three frames of sizes 5, 1, and 6. Their owned induced subgraphs contain 7 and 8 internal edges in the nonempty frames. Two directed `follows_event` edges cross between frames. Forty graph edges connect frame-owned nodes to unowned boundary nodes, split 17/4/19 across the three frames. The projected frame-interaction graph has reported exact treewidth 2. This is a single fixture-derived decomposition, not a general partition guarantee.

## Recorded native work

Each arm records 135 candidate-pair visits and 558 Term evaluations over ten event checkpoints. Per-rule totals are:

| Active rule | Candidate pairs | Term evaluations |
|---|---:|---:|
| `discourse_goal_select` | 44 | 182 |
| `discourse_goal_execute` | 45 | 186 |
| `discourse_goal_resolve` | 46 | 190 |

Attribution by event frame is 36 candidates / 150 Terms for frame 0, 3 / 12 for frame 1, and 96 / 396 for frame 2. These are counts from the captured trace, not CPU instruction counts. All three active historical rules use three positive triple patterns over four variables. This historical seed schema predates the current explicit Goal-identity guard; the work must not be read as a measurement of the current seed rules.

## Interpretation

This historical task fixture is structurally sparse overall, but contains global high-degree nodes and a small task-frame interaction width alongside nontrivial boundary incidence. The measured closure work is modest for this ten-event run and grows across its event sequence; the evidence does not establish linear cost in events, a runtime advantage from frame locality, natural task prevalence, or behavior on independently authored conversations.

The result refines the next gate: preserve the distinction between whole substrate graph, task-owned subgraph, and frame-boundary graph. Future task-derived measurements should report all three, bind active rule schemas to the exact captured source version, and include independent task families. The next fresh replication should use the current Goal-identity rules and lock a clean source tree plus native build artifact before capturing.

## Reproduction artifacts

- Retrospective protocol and limitations: [protocol](SUBSTRATE_RETROSPECTIVE_RUNTIME_TASK_CENSUS_PREREG_20260926.md)
- Analyzer: [`analyze_substrate_retrospective_runtime_task_census_v1.py`](../../../scripts/analyze_substrate_retrospective_runtime_task_census_v1.py)
- Raw source capture: [connected task census](../../../evaluation/reports/substrate_discourse_connected_task_census_v1_20260926.json)
- Original input lock: [lock JSON](../../../evaluation/substrate_capability/discourse_connected_task_census_lock_20260926.json)
- Independent structural/work audit: [analysis JSON](../../../evaluation/reports/substrate_retrospective_runtime_task_census_v1_20260926.json)
