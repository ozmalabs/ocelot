# Two-sheet current-source vision scale extension v2.4 results

## Result

The extension completed 144 isolated cells across six sizes, three seeds, two fold scopes, two B-sheet states, and audit counters off/on. The independent analyzer passes all nine gates: every registered cell exists, each worker matches the source lock, the reconstructed aggregate is complete, audit-on/off outputs and progress match exactly, the equation oracle is within 1e-12, counter totals reconcile, the global cross-sheet effect and scoped independence hold, no worker hits its cap, and timing/RSS measurements are present.

| Side per sheet | Total SUnits | Direct aggregate inputs per output (global / scoped) | Total Term evaluations (global / scoped) | Counter-off median closure wall (global / scoped) | Median peak RSS |
|---:|---:|---:|---:|---:|---:|
| 16 | 512 | 512 / 256 | 1,080,352 / 557,088 | 24.85 / 11.39 ms | 52 MiB |
| 32 | 2,048 | 2,048 / 1,024 | 16,907,296 / 8,522,784 | 0.410 / 0.180 s | 82 MiB |
| 64 | 8,192 | 8,192 / 4,096 | 268,961,824 / 134,760,480 | 6.297 / 2.786 s | 207 MiB |

From 2,048 to 8,192 units, total Term evaluations grow about 15.9× in both scopes as the input size grows 4×. Counter-off wall time grows about 15.4×. This is consistent with quadratic work for this rule's per-output mean over its full aggregate scope. Root scoping approximately halves the total evaluation count and runtime, but it does not make the cost linear: each sheet still has a whole-sheet mean, so each output depends on all SUnits in its own sheet. The effective aggregate scope is all 8,192 units globally versus 4,096 units per scoped output. These are source-defined read scopes, not exact treewidth bounds; auxiliary aggregate nodes could factor the computation differently.

The separate `term_unit:NodesOfType` counter records 134,225,920 global visits versus 8,192 scoped visits at the largest size. That very large ratio is specific to that counter, which does not count items returned by the scoped `Neighbours` source. Total Term-evaluation counts and counter-off wall time are more comparable here. Enabling audit counters costs about 3.1× global and 3.4× scoped at size 64, so counter-on time is excluded from engine latency comparisons.

Peak RSS reaches about 207 MiB per isolated process at 8,192 SUnits. It includes Python startup and fixture construction. The measured one-rule closure takes about 6.3 s global and 2.8 s scoped on this host. This is a useful within-family scale point, not evidence about arbitrary rule sets, natural-task prevalence, or 10⁷–10⁸-node graphs.

## Aggregation note

All 144 independently locked worker files completed and passed their source checks. The master runner had a stale hardcoded completion count of 96, returned nonzero, and did not write its aggregate. The [reconciliation script](../../../scripts/aggregate_substrate_vision_two_sheet_current_source_scale_v2_4.py) rebuilt the aggregate from the exact expected worker IDs and validated each worker's source-lock hash. The analyzer separately verifies this reconciliation metadata. The cell measurements were not changed.

## Reproduction artifacts

- Protocol: [v2.4 preregistration](SUBSTRATE_VISION_TWO_SHEET_CURRENT_SOURCE_SCALE_V2_4_PREREG_20260927.md)
- Runner, aggregator, and analyzer: [scale runner](../../../scripts/substrate_vision_two_sheet_current_source_scale_v2_4.py), [aggregate reconciliation](../../../scripts/aggregate_substrate_vision_two_sheet_current_source_scale_v2_4.py), [independent analysis](../../../scripts/analyze_substrate_vision_two_sheet_current_source_scale_v2_4.py)
- Raw report and isolated cells: [aggregate](../../../evaluation/reports/vision_two_sheet_current_source_scale_v2_4_20260927.json), `evaluation/reports/vision_two_sheet_current_source_scale_v2_4_cells/`
- Analysis and source lock: [analysis](../../../evaluation/reports/vision_two_sheet_current_source_scale_v2_4_analysis_20260927.json), [lock](../../../evaluation/substrate_capability/vision_two_sheet_current_source_scale_v2_4_lock_20260927.json)
