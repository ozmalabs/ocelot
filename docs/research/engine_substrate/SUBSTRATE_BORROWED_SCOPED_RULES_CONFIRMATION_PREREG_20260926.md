# Borrowed scoped-rule path confirmation preregistration

**ID:** `SUBSTRATE_BORROWED_SCOPED_RULES_CONFIRMATION_20260926`  
**Treatment:** scoped closure builds the ordered active `(original_slot, &RewriteRule)` reference vector directly from the live rule store and mutably borrows only disjoint Substrate fields. It no longer clones rule bodies or retains a snapshot cache. This avoids invalidation requirements while preserving stable slot labels.

## Locked confirmation

1. **No-match active-count sweep:** reuse the existing no-op fixture/API matrix and gates at rule counts `{0,1,4,16,64,256,512}`, both global audit modes, and scoped basic/report plus full report. Capture to new v2 paths (do not overwrite the pre-treatment v1 record). Seven repeats, same fixed graph, warmed before timing.
2. **Topology settlement:** rerun the five-repeat chain/tree/star, N={8,16,32,64} event/full matched matrix plus omitted-notification ablation. Capture to new v2 paths (do not overwrite the pre-treatment record). Preserve parity, exact owner notification, omission sensitivity, fixed points, and counters.
3. **Mutation/index attribution control:** rerun active/tombstoned slot attribution with original-slot per-rule counters; tombstone slot 1 and preserve live indices `{0,2,3,4}`. Capture to new v2 paths. Require state parity, active-index correctness, and additive counter conservation.

All captures must include locked runner/protocol/source/native hashes, current build provenance, and independent analysis. Timings are paired/descriptive and must be reported separately from semantic gates. This is a code-path confirmation on generated workloads; it does not establish natural frame locality or broad production speedup.

## Interpretation gate

Attribute changes only to the borrowed-rule implementation if semantic projections, progress, notifications, original indices, and counter totals match the pre-treatment definitions. Report no-op latency deltas by active count/API/audit mode and topology counters/timings against the prior raw data; do not infer an asymptotic gain from the single fixture family.
