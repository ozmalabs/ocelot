# Live conversation task-graph harvest v1 results

Date: 2026-10-03  
Protocol: [harvest preregistration](SUBSTRATE_LIVE_CONVERSATION_TASK_GRAPH_HARVEST_V1_PREREG_20261003.md)  
Runner: [source-locked graph runner](../../../evaluation/substrate_capability/live_conversation_task_graph_harvest_v1.py)  
Original analyzer (runtime import defect preserved): [v1 analyzer](../../../evaluation/substrate_capability/analyze_live_conversation_task_graph_harvest_v1.py)  
Amended analyzer: [v1.1 independent analyzer](../../../evaluation/substrate_capability/analyze_live_conversation_task_graph_harvest_v1_1.py)  
Analyzer amendment: [v1.1 note](SUBSTRATE_LIVE_CONVERSATION_TASK_GRAPH_HARVEST_V1_1_AMENDMENT_20261003.md)  
Source lock: [locked inputs](../../../evaluation/substrate_capability/live_conversation_task_graph_harvest_v1_lock_20261003.json)  
Capture: [compressed JSONL graph capture](../../../evaluation/reports/live_conversation_task_graph_harvest_v1_20261003.jsonl.gz)  
Analysis: [v1.1 structural and task analysis](../../../evaluation/reports/live_conversation_task_graph_harvest_v1_1_analysis_20261003.json)

## Integrity and outcomes

Ten fresh workers (two per prompt) completed with zero process errors. The runner and independent analyzer verify current source-lock stability, all ten graph snapshots, unique PIDs, and exact graph-digest equality between replicates for every condition. The corrected analyzer independently reconstructs ownership from raw graph relations; all gates pass. The first analyzer failed before producing output because it omitted an import for its summary statistic. Its source and capture lock remain unchanged; the separately hashed v1.1 analyzer fixes only that analysis defect.

The independently recomputed task oracle passes 6/10 requests: held self-knowledge, self-report action, and unknown-word clarification pass twice each. Scene description and concern authoring fail twice each. On the current source, scene description selects `self_report` rather than `describe_scene`; this differs from the older panel result, so the two captures must not be pooled as if source or behavior were stationary.

## Graph and ownership result

| Prompt route | Median nodes / edges | Task-owned nodes | Owned / total Goals | Boundary incidences / distinct incident boundary nodes | Contract pass |
|---|---:|---:|---:|---:|---:|
| Scene description | 25,216 / 11,722 | 5 | 1 / 6 | 40 / 26 | 0/2 |
| Held self-knowledge | 25,036 / 11,445 | 1 | 0 / 1 | 17 / 16 | 2/2 |
| Self-report action | 25,055 / 11,504 | 5 | 1 / 2 | 38 / 24 | 2/2 |
| Unknown-word clarification | 25,047 / 11,471 | 1 | 0 / 1 | 22 / 21 | 2/2 |
| Concern authoring | 25,056 / 11,524 | 1 | 0 / 1 | 31 / 30 | 0/2 |

The analyzer creates one request frame per isolated prompt, using the inbound Message as root, Goal-to-Message `comprehends` identity, and explicit `for_goal`/`origin_event` links for lifecycle events. Only two of five conditions contain any Goal assignable by this strict rule, and one of those has the wrong task Goal kind for its failed prompt. Goal-owner coverage is 0% in three routes and 50% in self-report; scene description has 1/6 Goals linked, but its task oracle fails. Each graph therefore has one frame and an interaction-treewidth value of zero. The zero cross-frame edge count is structurally guaranteed by this single-prompt design and is not evidence of natural cheap cuts.

These are large full-seed graphs dominated by runtime/lexical substrate: the assigned task frame has only one or five nodes among roughly 25,000 total. It has 16–30 distinct unowned nodes directly incident to those owned nodes. This is an auditable structural observation, but it does not establish factorization, scheduler locality, or natural-task prevalence. Many unowned nodes are unrelated seed/runtime state rather than a shared separator, so total unowned-node count must not be interpreted as boundary width.

## Next gate

Before attempting multi-frame inference claims, resolve the ownership-coverage gap: inspect how each live Goal is linked to its inbound Message on current source, then preregister a second rule using only explicit runtime identity edges if such a relation exists. Next capture several turns in one process so multiple request frames can coexist, retaining the original strict owner rule and reporting added identities separately. Use non-sensitive, consented or repository-authored sequences; this panel is not a natural conversation corpus.
