# Orientation response under global and root-scoped settle rules

**Run:** 2026-09-25. **Evidence:** paired native full-rescan orientation pilot with independent audit. No production seed or engine source was changed.

## Instrument finding
The initial four-phase pilot used the existing `complex_cells.present` path, which writes stimulus attrs and calls default `tick`. It produced zero tuning in every unit and arm. That raw result is preserved and is not treated as task-quality evidence.

A same-fixture diagnostic replayed one 0-degree frame. Default `tick` returned zero progress. Native full-rescan `run_rules_report(200000, detect_cycles=True)` then evaluated the unchanged graph, reached `repeated_graph_state` in 107 progress applications/102 passes on the 3×3 seed, and yielded positive act and rate. A separate source/runtime probe found an enabled DualProcessPolicy routing default tick to `hard_realtime`, while the vision rules are untagged. The observation therefore supports a plan/rule-class mismatch, not a missing attr-notification defect. The amended pilot duplicates the established stimulus writes and uses full-rescan closure per frame; it records fixed-point/repeated-state statuses for every presentation. See [`SUBSTRATE_VISION_DEFAULT_TICK_LATENCY_FILTER_RESULTS.md`](SUBSTRATE_VISION_DEFAULT_TICK_LATENCY_FILTER_RESULTS.md).

## Paired orientation results
The amended run uses 12 orientations and four phases on two paired single-sheet seeds. Global and Retina-root-scoped variants had exactly equal tuning arrays (maximum absolute delta 0) and equal mean OSI for each seed:

| Sheet | Seed | Global OSI | Root-scoped OSI | Diagnostic sweep time, global/root-scoped |
|---|---:|---:|---:|---:|
| 3×3 | 20260925 | 0.01318 | 0.01318 | 1.62 / 1.62 s |
| 4×4 | 20260926 | 0.01760 | 0.01760 | 4.25 / 4.30 s |

These OSI values are low and do not establish useful selectivity. Timing is from two pilot pairs and supports no speedup claim. The actual orientation path remains an informative matched workload, but its default tick latency-class routing is a gap requiring investigation.

## Evidence and limits
- [`v1 pilot protocol`](SUBSTRATE_VISION_SETTLE_ORIENTATION_SCOPE_PILOT_PREREG_20260925.md), [`v1.1 amendment`](SUBSTRATE_VISION_SETTLE_ORIENTATION_SCOPE_PILOT_V1_1_AMENDMENT_20260925.md)
- [`v1 runner`](../../../scripts/substrate_vision_settle_orientation_scope_pilot.py), [`corrected runner`](../../../scripts/substrate_vision_settle_orientation_scope_pilot_v1_1.py), [`independent analyzer`](../../../scripts/analyze_substrate_vision_settle_orientation_scope_pilot_v1_1.py)
- [`v1 raw zero-response record`](../../../evaluation/reports/substrate_vision_settle_orientation_scope_pilot_20260925.json)
- [`v1.1 raw`](../../../evaluation/reports/substrate_vision_settle_orientation_scope_pilot_v1_1_20260925.json), [`analysis`](../../../evaluation/reports/substrate_vision_settle_orientation_scope_pilot_v1_1_analysis_20260925.json), [`lock`](../../../evaluation/substrate_capability/vision_settle_orientation_scope_pilot_v1_1_lock_20260925.json)

Four phases are pilot resolution only; this is not the existing K=16 confirmation. The benchmark uses full-rescan closure, not ordinary tick, because the instrument diagnostic showed default tick makes zero progress after direct writes. The full sheet uses random initial weights without the rung-8 development/adaptation protocol. Multi-sheet task outcomes, learning, K=16 quality, and speed remain unmeasured.

## Next gate
Benchmark-tag the vision rules with `hard_realtime` in a cloned manifest and compare default tick to full-rescan closure, checking state/response/status parity. The current result shows the enabled dual-process plan filters the untagged vision rules; it does not establish an attr-notification defect. Separately, only after the response path is valid, run calibrated K=16 orientation scoring and the development/adaptation controls before making capability or seed-semantic claims.
