# Vision multi-frame scope scale v2.5.1 results

## Result

The 184-worker source-locked capture passes all 14 independent analysis checks: 180 registered factorial cells and four omission diagnostics, unique PIDs, unchanged source/native fingerprints, exact independent equations, exact counter-on/off output and graph-size parity, complete owner membership in clean cells, counter conservation, repeated work profiles, and no budget exits. Maximum workload is three frames × 2,304 SUnits = 6,912 SUnits. Equation residual is exactly zero in every clean and omission cell.

The captured task is one `st_settle` rule applied to disjoint declared frame roots. The target frame has deterministic random afferents and initial activation 1; sibling frames have zero afferents and initial activation 1 (equal control) or 0 (contrasting control). The global rule pools every SUnit; the scoped clone pools only SUnits attached to the matched root. The analyzer scores each output against both the global and per-frame equation, so it reports semantics and work separately.

## Work by frame size and sibling count

The table gives medians across three fresh seeds for the contrasting-state cells. `N` is SUnits per frame; total SUnits include the target and sibling frames. Counter-off wall time is descriptive. `NodesOfType` items are one specific Term-source counter, not a total-work measure.

| Side | Siblings | Total SUnits | Scope | Candidate tests | Term evaluations | `NodesOfType` items | Closure median (s) | Peak RSS median (MiB) |
|---:|---:|---:|---|---:|---:|---:|---:|---:|
| 16 | 0 | 256 | Global | 256 | 274,432 | 131,328 | 0.0235 | 53.4 |
| 16 | 0 | 256 | Root-scoped | 256 | 274,944 | 256 | 0.0223 | 45.3 |
| 16 | 1 | 512 | Global | 512 | 1,073,152 | 524,800 | 0.0896 | 48.9 |
| 16 | 1 | 512 | Root-scoped | 512 | 549,888 | 512 | 0.0449 | 48.4 |
| 16 | 2 | 768 | Global | 768 | 2,396,160 | 1,180,416 | 0.2013 | 52.0 |
| 16 | 2 | 768 | Root-scoped | 768 | 824,832 | 768 | 0.0668 | 52.0 |
| 32 | 0 | 1,024 | Global | 1,024 | 4,243,968 | 2,098,176 | 0.3726 | 55.1 |
| 32 | 0 | 1,024 | Root-scoped | 1,024 | 4,246,016 | 1,024 | 0.3345 | 55.5 |
| 32 | 1 | 2,048 | Global | 2,048 | 16,876,544 | 8,390,656 | 1.4191 | 68.6 |
| 32 | 1 | 2,048 | Root-scoped | 2,048 | 8,492,032 | 2,048 | 0.6667 | 68.1 |
| 32 | 2 | 3,072 | Global | 3,072 | 37,897,728 | 18,877,440 | 3.1038 | 81.2 |
| 32 | 2 | 3,072 | Root-scoped | 3,072 | 12,738,048 | 3,072 | 1.0019 | 81.1 |
| 48 | 0 | 2,304 | Global | 2,304 | 21,345,792 | 10,619,136 | 1.7684 | 71.5 |
| 48 | 0 | 2,304 | Root-scoped | 2,304 | 21,350,400 | 2,304 | 1.7168 | 72.1 |
| 48 | 1 | 4,608 | Global | 4,608 | 85,158,912 | 42,471,936 | 7.0524 | 101.4 |
| 48 | 1 | 4,608 | Root-scoped | 4,608 | 42,700,800 | 4,608 | 3.4035 | 101.7 |
| 48 | 2 | 6,912 | Global | 6,912 | 191,439,360 | 95,558,400 | 15.7844 | 130.8 |
| 48 | 2 | 6,912 | Root-scoped | 6,912 | 64,051,200 | 6,912 | 5.1716 | 131.1 |

Candidate tests equal the total number of owner-bound SUnit outputs in both scopes. The rule-body rewrite does not reduce pattern-binding enumeration; the change is in the population each output reads. At three frames, root scoping reduces Term evaluations by about 3× relative to global aggregation. For side 48, this is 191.4M versus 64.1M Term evaluations and 15.78 versus 5.17 seconds. Root scoping does not remove the dense within-frame aggregate: at one frame, global and scoped Term totals and latency are nearly equal. The observed pattern is consistent with global work growing with total population per output, while root-scoped work repeats a frame-sized aggregate independently per frame. It is an exact result for this one rule and these graph fixtures, not a general complexity theorem.

Equal-state siblings are a control: because every SUnit begins at activation 1, global competition has the same mean as the target-only frame, and target outputs equal the no-sibling case. Contrasting zero-state siblings change the global target output; root-scoped target output remains exactly invariant to sibling count and state. Thus global aggregation transmits sibling state across declared frames, while the root-scoped clone preserves the independently computed frame equation in this fixture.

In the omission diagnostic, one target SUnit remains in the graph with its lattice edges but loses its `has_sunit` owner edge. The expected coverage check detects that it is not updated. The unowned SUnit remains in the global `NodesOfType(SUnit)` population, so the global count formula uses all typed SUnits but only owner-bound output bindings; the scoped `Neighbours` population excludes it. The diagnostic therefore exposes a real ownership-sensitive difference instead of silently treating the declared root membership as complete.

## Censored initial capture and analysis correction

The first v2.5 capture is retained but excluded: a native extension rebuild changed the build manifest and loaded binary during execution, and one of 184 workers observed the new fingerprints. Its equations, audit/control parity, and attribution reconcile, but the source/native gate and engine provenance fail. The v2.5.1 run took two matching lock probes after that rebuild and passed all per-worker and post-run fingerprint checks.

The initial analyzer also applied a clean-run `NodesOfType` closed form to the omission controls. V2.5.1 uses `M × (2T + 1)` for global aggregation, with M owner-bound outputs and T total SUnits, and M for the scoped `NodesOfType` count. The exact initial analyzer and initial analysis output remain preserved under v2.5 names; the corrected analyzer was included in the v2.5.1 lock before its capture.

## Limits and next gate

This is a second workload family after the full-seed `describe_scene` factorial and the prior two-sheet visual scale study. It establishes exact route-specific cost and sibling-state transfer for a synthetic settling rule with declared roots. It does not execute image ingestion or visual learning, discover frames, establish that natural tasks follow these boundaries, or prove a generic root-scoped execution policy safe. The `NodesOfType` counter understates scoped population work because this instrumentation does not count result cardinality for its `Neighbours` replacement. Timing uses three fresh processes per cell and remains descriptive.

Next, evaluate global and frame-scoped settlement through the production visual pipeline with image ingestion and iterative update phases, independent task-level outputs, and owner-edge omission/contamination controls. Measure the cost and accuracy of obtaining the frame partition separately from applying it. Do not count protocol-supplied roots as learned cheap cuts.

## Reproduction artifacts

- Original design: [v2.5 preregistration](SUBSTRATE_VISION_MULTI_FRAME_SCOPE_SCALE_V2_5_PREREG_20260929.md).
- Source-drift and analyzer correction: [v2.5.1 amendment](SUBSTRATE_VISION_MULTI_FRAME_SCOPE_SCALE_V2_5_1_AMENDMENT_20260929.md).
- Runner: [v2.5.1 capture](../../../scripts/substrate_vision_multi_frame_scope_scale_v2_5_1.py); analyzer: [v2.5.1 independent analysis](../../../scripts/analyze_substrate_vision_multi_frame_scope_scale_v2_5_1.py).
- Lock: [v2.5.1 source/native lock](../../../evaluation/substrate_capability/vision_multi_frame_scope_scale_v2_5_1_lock_20260929.json).
- Reports: [driver](../../../evaluation/reports/vision_multi_frame_scope_scale_v2_5_1_20260929.json), [raw workers](../../../evaluation/reports/vision_multi_frame_scope_scale_v2_5_1_workers_raw_20260929.json), [independent analysis](../../../evaluation/reports/vision_multi_frame_scope_scale_v2_5_1_analysis_20260929.json).
- Censored v2.5 artifacts and cell outputs are retained with their original versioned names; see also [exact locked analyzer source](../../../scripts/analyze_substrate_vision_multi_frame_scope_scale_v2_5_locked_source.py) and [initial analysis](../../../evaluation/reports/vision_multi_frame_scope_scale_v2_5_analysis_initial_mixed_native_capture_20260929.json).

To reproduce, create the source lock with `PYTHONPATH=runners/dsl/python:. OZMA_NO_LLM=1 OZMA_SEED_PERSIST_DISABLED=1 python3 scripts/substrate_vision_multi_frame_scope_scale_v2_5_1.py --lock`, run the same command without `--lock`, then invoke `PYTHONPATH=runners/dsl/python:. python3 scripts/analyze_substrate_vision_multi_frame_scope_scale_v2_5_1.py`. The capture includes 180 factorial workers and four deliberate omission diagnostics.
