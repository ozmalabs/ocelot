# Bigville dynamic-link cut capture: min-fill grouping loses authored locality

**Date:** 2026-09-26. This is a source-current generated-topology structural
capture, not a natural-task prevalence or candidate-executor speed result.

## Capture validity

Nine fresh workers (three each for ring, star, and seeded random-connected
links) captured seven checkpoints per worker. The independent analyzer passes
all current source/build locks and independently reconstructs all 63 graph
digests, residuals, min-fill orders/widths, mutation counts and weights, and
partition metrics. Each checkpoint settles under the established repeated
all-owner Microtheory sweep and has zero independent CAN residual. Candidate
partitions refuse before scoped calls because the active rule declares
`reads_any=true`.

## Structural result at full link insertion

The authored components have five concepts each. Sorted native-ID grouping
recovers those components exactly on this builder's stable allocation order.
The deterministic min-fill elimination order is useful for a width bound but
its contiguous five-node groups do not recover frame membership:

| Topology | Cross-frame directed causal edges, authored / balanced-ID / min-fill | Within-authored node pairs retained by min-fill | Min-fill width bound |
|---|---:|---:|---:|
| Ring (100 links) | 200 / 200 / 680 | 40.0% | 2 |
| Star (99 links) | 198 / 198 / 592 | 60.4% | 2 |
| Random connected (100 links) | 200 / 200 / 642 | 49.7% | 2 |

All partitions have equal frame sizes by construction. The min-fill induced
width bound stays 2 in these controls, while min-fill-based contiguous groups
create roughly 3.0–3.4 times as many cross-frame causal edges as authored or
balanced-ID groups. Thus a low-width elimination ordering is not itself a
good partition assignment. On these inputs, stable native IDs already encode
the authored components; this is a property of the builder, not a general
recommendation to group by ID.

Across all mutation checkpoints, including the ten-resident evidence update,
retraction, reweight, reinsertion, and full removal, all-owner closure reaches
an independently checked zero-residual state. Partition reconstruction takes
about 127–205 ms median wall time per checkpoint for this Python diagnostic
(roughly the same CPU time), excluding substrate build and closure. These are
construction costs for this implementation, not an asymptotic or commodity
CPU estimate.

## Claim boundary

This capture does not execute balanced-ID or min-fill groups. They correctly
refuse on wildcard rule reads, so no partitioned parity, omitted-notification
sensitivity, or speed claim follows. A prior locked dynamic-link experiment
separately compared caller-driven authored-owner queues with full owner-sweep
closure and an omitted-evidence notification control; its results are not
merged into this capture's fresh-worker counts. The dialogue cut remains a
shared-state refusal case until an oracle-preserving mutation seam exists.

The first capture attempt used the unscoped `run_rules_report` API and failed
independent residuals on connected graphs. It is preserved. The accepted
runner uses the pre-existing Bigville benchmark's all-owner sweep. A first
analyzer attempt also had a checkpoint index error in the expected weights;
it is preserved with the corrected accepted analysis.

## Artifacts

- Protocol: [`SUBSTRATE_BIGVILLE_DYNAMIC_LINK_CUT_CAPTURE_V1_PREREG_20260926.md`](SUBSTRATE_BIGVILLE_DYNAMIC_LINK_CUT_CAPTURE_V1_PREREG_20260926.md)
- Runner: [`substrate_bigville_dynamic_link_cut_capture_v1.py`](../../../scripts/substrate_bigville_dynamic_link_cut_capture_v1.py)
- Independent analyzer: [`analyze_substrate_bigville_dynamic_link_cut_capture_v1.py`](../../../scripts/analyze_substrate_bigville_dynamic_link_cut_capture_v1.py)
- Input lock: [`bigville_dynamic_link_cut_capture_v1_lock_20260926.json`](../../../evaluation/substrate_capability/bigville_dynamic_link_cut_capture_v1_lock_20260926.json)
- Raw capture: [`substrate_bigville_dynamic_link_cut_capture_v1_20260926.json`](../../../evaluation/reports/substrate_bigville_dynamic_link_cut_capture_v1_20260926.json)
- Independent analysis: [`substrate_bigville_dynamic_link_cut_capture_v1_analysis_20260926.json`](../../../evaluation/reports/substrate_bigville_dynamic_link_cut_capture_v1_analysis_20260926.json)
- Preserved first runner attempts: [global-closure residual failure](../../../evaluation/reports/substrate_bigville_dynamic_link_cut_capture_v1_residual_failure_20260926.json), [first raw capture](../../../evaluation/reports/substrate_bigville_dynamic_link_cut_capture_v1_first_attempt_20260926.json)
- Preserved analyzer attempt: [checkpoint weight-index failure](../../../evaluation/reports/substrate_bigville_dynamic_link_cut_capture_v1_analyzer_attempt_stage_index_20260926.json)
