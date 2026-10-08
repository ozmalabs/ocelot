# Frame-locality capture reanalysis v1 (2026-09-28)

## Purpose and scope

This offline audit maps three existing source-locked live task-boundary captures onto the [frame-locality measurement contract](SUBSTRATE_FRAME_LOCALITY_MEASUREMENT_CONTRACT_V1_20260928.md). It does not rerun the substrate, discover frames, or estimate cheap-cut prevalence. The frame ownership remains protocol-declared.

The analyzer reads the held-topic v1.6, self-report task-boundary v2.1, and concurrent `describe_scene` boundary v1 result records. It extracts frame size, internal typed-edge count, crossing typed-edge incidences, distinct external nodes, available aggregate edge/node-type histograms, owned-induced-width upper bound, and whole-graph size where present. It records each input report's SHA-256 and checks that each worker's recorded start/end input-lock structures are equal.

## Results

| Live task family | Frame records | Frame node counts | Internal edges | Crossing incidences | Distinct external nodes | Owned induced-width upper bound | Replicate signatures |
|---|---:|---:|---:|---:|---:|---:|---|
| Held-topic answers | 21 (7 turns × 3 workers) | 10–13 | 10–13 | 39–46 | 26–30 | 1–2 | Identical across workers for all seven turn positions |
| Self-report | 6 (2 turns × 3 workers) | 3 or 8 | 2 or 16 | 18–36 | 15–19 | 1–2 | Identical across workers for both turn positions |
| Concurrent `describe_scene` | 6 (2 requests × 3 workers) | 6 or 7 | 11 or 12 | 32–35 | 18–20 | 2 | Identical across workers for both request positions |

All three records pass the recorded per-worker start/end input-lock equality check. The extractor also confirms exact replication of its reported structural signature within each task/turn position. This is a reproducibility check over the result records, not an independent rerun or revalidation of the original runner/analyzer gates.

## Contract field audit

Recoverable from these reports are runtime-node frame sizes, complete direct typed-edge cuts for the declared node sets, incidence counts, counts of distinct external nodes, aggregate type histograms, and some induced-width upper bounds on the owned node subgraph. Endpoint IDs appear in edge lists, but the reports do not preserve a complete endpoint-to-node-type mapping for each external endpoint.

The records do not contain task-relevant state-variable/attribute interfaces or finite domain sizes, a complete operation/factor dependency graph, decomposition width for such an operation graph, or partition discovery/maintenance cost. Therefore the contract's interface cardinality (k_i), domain product (q_i), and operation-graph width cannot be recovered from these artifacts. An owned-node induced width is not a substitute for them.

## Interpretation and next gate

The existing three-family census is repeatable at the level of declared graph-node cuts. The cuts are sizeable relative to their owned projections, and the edge/node histograms show why incidence count and unique external-node count must remain distinct. This does not establish whether the operational interface is small: many external nodes could expose only a small variable interface, or the same node boundary could mediate many task-relevant dependencies.

The next capture must retain node IDs with type and relevant attribute/domain metadata, preserve factor/rule dependency scopes and access coverage, and time partition discovery separately from execution. It should use independently selected task checkpoints and an ownership proposal that does not receive the protocol-declared frame as an input. Before that capture, the current artifacts should be retained as the declared-boundary baseline, not counted as evidence of learned cheap cuts.

## Reproduction and artifacts

- Analyzer: [`analyze_frame_locality_capture_crosswalk_v1.py`](../../../scripts/analyze_frame_locality_capture_crosswalk_v1.py)
- Machine-readable output: [`frame_locality_contract_reanalysis_v1_20260928.json`](../../../evaluation/reports/frame_locality_contract_reanalysis_v1_20260928.json)
- Input: [held-topic v1.6 report](../../../evaluation/reports/substrate_live_held_topic_evidence_v1_6_20260926.json)
- Input: [self-report boundary v2.1 report](../../../evaluation/reports/substrate_live_self_report_task_boundary_v2_1_20260927.json)
- Input: [concurrent scene boundary v1 report](../../../evaluation/reports/substrate_live_describe_scene_boundary_v1_20260926.json)

Run from the repository root with `python3 scripts/analyze_frame_locality_capture_crosswalk_v1.py`.
