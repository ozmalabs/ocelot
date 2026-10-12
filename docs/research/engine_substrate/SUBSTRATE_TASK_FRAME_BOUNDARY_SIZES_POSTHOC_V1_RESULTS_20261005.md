# Task-frame boundary sizes: post-hoc census v1

## Measurement

A post-hoc, deterministic reanalysis of the source-locked typed-interaction capture derives per-frame node counts, shared-membership nodes, distinct external graph-node neighbors, crossing edge incidences, and incidences to unassigned counterpart nodes. It covers the same 78 snapshots across Bigville dynamic-link (63), connected conversation (12), and discourse connected-task (3), yielding 6,363 frame instances. Every graph's reconstructed labeled-node count and typed-edge occurrence count matches the parent capture; the script reports zero errors.

| Family | Frame instances | Frame nodes, median | Shared-membership nodes, median | Distinct external graph nodes, median / p90 / max | Crossing edge incidences, median / p90 / max | Unassigned endpoint incidences, median |
|---|---:|---:|---:|---:|---:|---:|
| Bigville dynamic-link | 6,300 | 5 | 0 | 2 / 3 / 100 | 7 / 9 / 203 | 5 |
| Connected conversation | 54 | 9 | 4 | 27 / 47 / 47 | 63 / 123 / 123 | 14 |
| Discourse connected task | 9 | 11 | 4 | 19 / 25 / 25 | 36 / 50 / 50 | 12 |

## Interpretation and limits

Under these runtime ownership annotations, Bigville’s typical small frame has a small number of external graph-node neighbors, but the maximum reaches 100 and every frame has unassigned-endpoint incidence. The conversation and discourse frames have substantially larger coarse boundaries: median external neighbor counts are three to five times frame size, and four of nine or eleven nodes are shared across memberships. This weighs against assuming that every annotated task frame is separated by a small state-graph boundary.

These are **graph-node** boundaries derived from edge endpoints. They are not factor-variable interfaces, separator-state products, rule read/write scopes, or learned frames. Bigville captures are generated dynamic-link cases, and the conversation/discourse captures are selected tasks with runtime annotations. This does not estimate natural-task prevalence or prove inference is intractable. It identifies a concrete next test: map typed rule/factor scopes onto these same boundaries and determine whether the apparent external nodes are actually task-relevant information channels.

## Reproduction

Run `python3 evaluation/substrate_capability/posthoc_task_frame_boundary_sizes_v1.py`. The source data are the [typed interaction capture](../../../evaluation/reports/substrate_typed_frame_interaction_census_v1_20261003.json); the deterministic derived output is [here](../../../evaluation/reports/task_frame_boundary_sizes_posthoc_v1_20261005.json), with the [analysis script](../../../evaluation/substrate_capability/posthoc_task_frame_boundary_sizes_v1.py).
