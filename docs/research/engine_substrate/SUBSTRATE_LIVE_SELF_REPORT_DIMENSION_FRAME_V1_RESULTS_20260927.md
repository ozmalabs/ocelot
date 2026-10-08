# Live self-report task-dimension frame scale v1

Date: 2026-09-27

## Question and intervention

This source-locked live route varies the number of held self-organisation dimensions, rather than adding semantically unrelated vocabulary. In fresh full-seed workers, the harness replaces the Agent's cached area inventory with 4, 8, 12, 16, or 24 controlled area names. Each dimension has one Microtheory, one Concept, one `has_concept` edge, and one `holds_area` edge to the shared Agent root. All seeded rules stay active. Two replicates per size ran both untraced and audited, for 20 workers. A v1.1 preregistration amendment preserves concrete native trace node IDs for frame/root-touch analysis.

The synthetic frame definition is supplied by the harness. This measures the live route operating over an explicit task frame and its public reporting capability; it does not test whether the substrate discovers this frame.

## Capability result

All 16 corrected independent gates pass. Each request took the `self_report` route and resolved one Goal through selection, execution, and action result. Audited/untraced pairs have exact reply, Goal, graph digest, and graph-size parity. The structured reflective result carries every supplied area in order. The user-facing surface emits only the first 12.

| Held dimensions | Dimensions in structured reflection | Dimensions in reply | Coverage |
|---:|---:|---:|---:|
| 4 | 4 | 4 | 100% |
| 8 | 8 | 8 | 100% |
| 12 | 12 | 12 | 100% |
| 16 | 16 | 12 | 75% |
| 24 | 24 | 12 | 50% |

This is a direct task-output capability gap: the internal faculty retains the larger inventory, while `_surface_self_state` deliberately truncates the prose list at 12. This result does not determine whether the cap is appropriate for natural dialogue, but it identifies a concrete boundary the general capability panel should track.

## Structural and engine work

The explicit aggregate frame has 2N owned nodes, N internal `has_concept` edges, N boundary incidences, and one unique external node (the shared Agent root). Its simple graph is a set of paths of length two attached to that root, so its constructed width is 1. This small separator is a property of the intervention's topology, not learned locality in the engine. It demonstrates the measurement fields on a known frame and does not prove the engine factors work through it.

| Dimensions | Graph nodes | Graph edges | Candidate tests | Term evaluations | Selected access events | Frame-node access events | Frame share of selected trace | Untraced wall median | Untraced peak RSS median |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 4 | 24,996 | 11,477 | 66,050 | 716,033 | 333,117 | 88 | 0.026% | 347 ms | 1.673 GiB |
| 8 | 25,004 | 11,485 | 66,082 | 716,385 | 333,205 | 176 | 0.053% | 330 ms | 1.673 GiB |
| 12 | 25,012 | 11,493 | 66,114 | 716,737 | 333,293 | 264 | 0.079% | 331 ms | 1.673 GiB |
| 16 | 25,020 | 11,501 | 66,146 | 717,089 | 333,381 | 352 | 0.106% | 345 ms | 1.673 GiB |
| 24 | 25,036 | 11,517 | 66,210 | 717,793 | 333,557 | 528 | 0.158% | 345 ms | 1.673 GiB |

From 4 through 24 dimensions, each added dimension contributes exactly 8 candidate tests, 88 Term evaluations, and 22 selected access events. All measured candidate and Term growth is attributed to `curiosity_targets_ambivalent_nodes`; other measured rules do not change over this axis. The audited work profiles and semantic graph repeat exactly by size. Candidate/Term totals reconcile with unique per-rule/per-clause and Term-kind totals; ambiguous IDs are not assigned unique attribution. Trace rows have zero drops.

The amended trace places 22 selected access events per dimension on the supplied Microtheory/Concept nodes. Across the selected full-request trace these are only 0.026% to 0.158% of events over the tested sizes. The shared Agent root is touched in 3,726 selected events at every size. This is a concrete mismatch between a compact harness-declared frame and the selected access surface: most measured engine activity does not touch the area nodes. It does not show those accesses are irrelevant or unnecessary; instrumentation covers selected sites and specialized operations remain partial.

The frame-touching trace events are attributed to `time_infer_mint` (18 per dimension: 16 attribute reads, one pattern-edge read, and one attribute write) and `resolve_slang_variant` (4 per dimension, effect type-candidate reads). In contrast, the native candidate/Term counters attribute all aggregate growth to `curiosity_targets_ambivalent_nodes`. These are distinct instrumentation surfaces, not a reconciled causal decomposition. The discrepancy is now a concrete instrumentation/engine gap: per-rule work growth does not line up with the rules whose selected accesses touch the added task-frame nodes. The trace has blind spots, so neither attribution should be treated as complete.

The timing medians are nonmonotone, and only two repetitions per arm and cell were captured. Peak RSS is dominated by the 25k-node seeded substrate and stays near 1.673 GiB; the sweep cannot resolve per-dimension memory cost at this granularity. Treat these as finite controlled work counts, not an asymptotic or commodity-scale timing result.

## Analysis correction

The first offline analyzer draft compared timing and RSS observations as part of exact repeatability, so it rejected repeated work because elapsed resources naturally differed. The corrected independent analyzer checks deterministic counters, trace totals, graph sizes, and semantic digests while reporting resources separately. The full 20-worker schedule was rerun under a refreshed lock that includes the final runner, analyzer, and v1.1 amendment. The reported capture is that source-stable rerun; all 16 corrected checks pass.

## Interpretation and next work

This study adds one independently authored live route with both a task-relevant input-size axis and an explicit graph cut. It shows exact linear measured work for this small axis, as well as a response-coverage cap at 12. Because the harness authored the ownership relation, the result does not validate `hyp:cheap-cut`, natural frame frequency, or inference/matcher factorization. Next compare these declared frames with the runtime reads and writes that actually drive the route, then repeat the task-quality/width comparison on an independently sourced family. Continue separate Rung 3/4 induction measurements; this experiment does not address those gaps.

## Artifacts

- [Preregistration](SUBSTRATE_LIVE_SELF_REPORT_DIMENSION_FRAME_V1_PREREG_20260927.md)
- [Node-level trace amendment](SUBSTRATE_LIVE_SELF_REPORT_DIMENSION_FRAME_V1_1_AMENDMENT_20260927.md)
- [Runner](../../../scripts/substrate_live_self_report_dimension_frame_v1.py)
- [Independent analyzer](../../../scripts/analyze_substrate_live_self_report_dimension_frame_v1.py)
- [Source lock](../../../evaluation/substrate_capability/live_self_report_dimension_frame_v1_lock_20260927.json)
- [Driver report](../../../evaluation/reports/live_self_report_dimension_frame_v1_20260927.json)
- [Analysis](../../../evaluation/reports/live_self_report_dimension_frame_v1_analysis_20260927.json)
- [Raw workers](../../../evaluation/reports/live_self_report_dimension_frame_v1_workers_raw_20260927.json)
