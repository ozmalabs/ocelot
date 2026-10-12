# Live conversation multi-turn frame scaling v1 results

Date: 2026-10-03  
Protocol: [preregistration](SUBSTRATE_LIVE_CONVERSATION_MULTITURN_FRAME_SCALE_V1_PREREG_20261003.md)  
Amendment: [v1.1 digest comparison](SUBSTRATE_LIVE_CONVERSATION_MULTITURN_FRAME_SCALE_V1_1_AMENDMENT_20261003.md)

## Result

The fixed schedule completed 12 unique fresh workers: N=1, 2, 4, and 8 identical sequential `report your organisation` turns, three workers per N. All workers exited successfully, emitted a complete record, and matched the locked source before and after execution. The independent v1.1 analysis passes all per-turn identity and route contracts, exact three-replicate semantic graph comparisons, and frame reconstruction. The original v1 raw-digest gate is retained as failed at N=2, 4, and 8 because fresh-process graphs differ in `SystemModel.attrs.runtime_s` and `ts`; the amended analyzer excludes only those two generated timing fields and preserves every raw graph digest.

| Turns | Median nodes | Median edges | Owned frame nodes | Incident boundary nodes | Direct cross-frame edges | Frame interaction edges | Exact interaction treewidth | Median peak RSS |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 25,055 | 11,504 | 6 | 24 | 0 | 0 | 0 | 1,721.2 MiB |
| 2 | 25,105 | 11,634 | 12 | 42 | 1 | 1 | 1 | 1,721.6 MiB |
| 4 | 25,203 | 11,894 | 24 | 78 | 3 | 6 | 3 | 1,721.0 MiB |
| 8 | 25,399 | 12,414 | 48 | 150 | 7 | 28 | 7 | 1,721.4 MiB |

Each request creates one distinct resolved `report_self` Goal explicitly linked to its own inbound Message; all 45 (sum of N over the 12 workers) per-turn route contracts pass. The frame contains six owned nodes per turn. The boundary-mediated interaction graph becomes complete: at N=8, 13 shared unowned boundary nodes connect every pair among eight frames, even though there are only seven directly cross-owned edges. Therefore this route is evidence of persistent task identity, but evidence against cheap-cut locality under the current ownership rule. It shows why direct cross-frame edge count alone understates coupling.

Median peak RSS remains around 1.72 GiB across N, because the measurement includes full-seed boot and the ~25k-node base graph; this is not an estimate of per-frame memory. First-turn latency is about 327–355 ms. Later turns are mostly about 130–160 ms, with a few outliers. The workers run serially, so these timings do not measure parallel frame execution.

## Interpretation and next gate

The route's task/frame ownership is measurable and reproducible after normalizing two generated timing fields. Its interaction width grows linearly through eight repeated turns, so this result does not support the cheap-cut tractability hypothesis for this workload. The workload repeats one self-report action, allowing persistent discourse state to connect turns; this is not a representative natural conversation sample and does not show that semantically distinct tasks have the same topology.

Next, preregister a small panel of semantically distinct multi-turn sequences (including independent requests, dependent follow-ups, and cross-topic turns), with explicit task oracles and the same identity-based ownership rules. Include a no-prior-conversation baseline and report both direct edges and boundary-induced interaction width. This separates intentional continuity from unwanted global coupling and avoids claiming natural-task prevalence from one repeated prompt.

Artifacts: [raw capture](../../../evaluation/reports/live_conversation_multiturn_frame_scale_v1_20261003.jsonl.gz), [original v1 analysis, raw-digest gate failure](../../../evaluation/reports/live_conversation_multiturn_frame_scale_v1_analysis_20261003.json), [v1.1 semantic analysis](../../../evaluation/reports/live_conversation_multiturn_frame_scale_v1_1_analysis_20261003.json), [runner](../../../evaluation/substrate_capability/live_conversation_multiturn_frame_scale_v1.py), [v1.1 analyzer](../../../evaluation/substrate_capability/analyze_live_conversation_multiturn_frame_scale_v1_1.py), and [source lock](../../../evaluation/substrate_capability/live_conversation_multiturn_frame_scale_v1_lock_20261003.json).
