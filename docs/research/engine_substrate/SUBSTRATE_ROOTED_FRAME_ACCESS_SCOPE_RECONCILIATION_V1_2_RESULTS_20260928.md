# Rooted-frame access-scope reconciliation v1.2 results

Date: 2026-09-28

## Result

The source repair adds `ShapeDecode` to the conservative graph-reading Term cases in `collect_term_reads()`. The rebuilt native engine sets `reads_any=true` for observed `sd_decode` rule UID 303 while preserving its explicit finite keys and match edge. This closes the v1.1 observed discrepancy: the independent analyzer finds zero static resource mismatches for both prompts in all three workers. The six capture-integrity gates pass: three fresh workers, stable start/end/post source locks, task/semantic parity against the accepted v1.1 panel, exact corrected trace parity across workers, zero dropped events with weighted-count conservation, and foreign-substrate isolation.

The corrected trace records 332,816 weighted events / 56,942 distinct rows for `report your organisation` and 79,888 / 15,593 for `describe who you are` in the first replicate. Concrete dependency pairs are 219 and 39, with zero observed pairs outside the static projection. Counter equations remain descriptive and are not conserved in the first prompt; the v1.1 source-boundary warning still applies. The conservative wildcard declaration can increase rule wake-ups, so this local correctness repair says nothing yet about runtime cost or the precision of static dependency sets.

## Interpretation and next work

This closes the observed ShapeDecode operation-scope gap. The next [Term access-dependency audit](SUBSTRATE_TERM_ACCESS_DEPENDENCY_AUDIT_V1_RESULTS_20260928.md) extended the source review and measured small deterministic operation-count deltas for this prompt pair. Neither result proves complete declarations across the Term language or full trace coverage. Generate the full Term/evaluator/helper crosswalk, extend cost measurements to distinct task families and scales, then resume task-boundary and ownership-blind cut measurements. Calibrate scale counters before making any per-frame cost claim.

Artifacts: [v1.2 preregistration](SUBSTRATE_ROOTED_FRAME_ACCESS_SCOPE_RECONCILIATION_V1_2_PREREG_20260928.md), [runner](../../../scripts/substrate_rooted_frame_access_scope_reconciliation_v1_2.py), [independent analyzer](../../../scripts/analyze_rooted_frame_access_scope_reconciliation_v1_2.py), [lock](../../../evaluation/substrate_capability/rooted_frame_access_scope_reconciliation_v1_2_lock_20260928.json), [raw capture](../../../evaluation/reports/rooted_frame_access_scope_reconciliation_v1_2_20260928.json), [analysis](../../../evaluation/reports/rooted_frame_access_scope_reconciliation_v1_2_analysis_20260928.json).
