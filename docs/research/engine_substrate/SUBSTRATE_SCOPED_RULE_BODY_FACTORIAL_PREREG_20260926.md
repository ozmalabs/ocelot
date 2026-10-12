# Scoped rule body factorial preregistration

**ID:** `SUBSTRATE_SCOPED_RULE_BODY_FACTORIAL_20260926`  
**Question:** does scoped no-match latency grow with match-pattern size, effect-vector size, or both? The preceding combined contrast could not separate these components.

## Locked design

- Active rules `{64, 256, 512}`; five fresh fixtures per cell; 30 timed calls per fixture after one warm-up; audit off; randomized cell order within repeat.
- Factor A, match edges per rule: `{1, 8}` unique absent edge types, all disconnected. Factor B, effects per rule: `{1, 8}` harmless `SetAttr` effects. Full 2×2 cross at each active count (12 cells per repeat, 60 captured cells).
- Fixed two-node Microtheory graph, scope, API (`run_rules_scoped`), cap, and environment. No tombstones in this probe. Record wall/process CPU time, exact active/slot counts, graph projection, and audit counters.
- Require zero progress, unchanged graph, exact rule count, zero candidate and Term work, zero audit counters, current build, and complete protocol/runner/source/native hashes. Timing is descriptive and does not alone prove a clone-only causal effect.

## Analysis and interpretation

For each active count report medians and p10/p90. Compute paired factorial contrasts: eight-vs-one edge at each effect count, eight-vs-one effect at each edge count, and their interaction. Pattern-size cost can include matcher traversal/setup; effect-size cost is more directly consistent with copied rule payload but may include other rule-body processing. Neither is an exact allocation or clone-time measure.

## Decision gate

If effect count scales material cost independently of edge count, add a narrowly scoped native diagnostic separating snapshot clone time from matching time before proposing reuse. If edge count dominates, optimize or profile the scoped matcher. If both contribute, prototype only after direct component evidence and design mutation invalidation around all rule-store writes. Preserve rule order, stable original indices, tombstones, and rule self-modification semantics. No natural-task scale claim follows.
