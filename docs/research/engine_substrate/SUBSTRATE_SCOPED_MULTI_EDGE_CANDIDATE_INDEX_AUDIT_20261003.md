# Scoped multi-edge candidate-index audit — 2026-10-03

## Measured bottleneck

The v1.4 source-locked pilot records 11,640 calls through `ScopedMatchPath::FullFallback`, zero `LocalOwnedEdge`, and zero `MicrotheorySeed`. Its four active discourse lifecycle rules each have four match edges. The current fast paths in `match_rule_each_for_scope` are explicitly single-edge cases; otherwise the scoped runner calls `match_rule_each` over the full graph and filters completed bindings with `binding_touches_scope`. The corresponding measured workload uses 9.34× as many candidate visits and 11.18× as many Term evaluations as monolithic closure.

## Available anchor and missing representation

Each discourse rule records `match_type: Goal`, and every lifecycle rule pattern includes a `goal` variable. `RewriteRule.match_type` currently documents a typed driver only for a single match edge, where the target variable is unambiguous. For a multi-edge rule the IR has no explicit association between a type and its anchor variable. A safe scoped candidate path therefore needs explicit metadata such as an anchor variable/type pair, or a sound inference rule with equivalent validation. Hard-coding the variable name `goal` would make the optimization specific to this seed rather than a general scope contract.

`match_rule_each_with_initial` accepts an initial binding and begins expanding the existing match-edge sequence from its first edge. This gives a plausible implementation seam: seed the declared anchor with owned candidates, collect and deduplicate complete bindings, then preserve the global match/effect order. However, seeding owned values can change enumeration order, and effects may be order-sensitive. Exact final closure parity on the current fixture is insufficient proof of ordered equivalence.

## Required proof and measurements

Before enabling the path, prove or gate on all of the following:

1. Every full binding that survives the scope filter binds the declared anchor to an owned node. Otherwise seed every eligible owned variable or fall back to full matching.
2. The scoped candidate path returns the same distinct binding set and the same effect-application order as full matching, including duplicate edge patterns and injectivity checks.
3. Seeded matching never omits a binding when a dependency crosses task frames, a shared node changes, a task gains or loses ownership, or an edge is deleted and reused.
4. The path falls back conservatively when metadata is absent, stale, ambiguous, or contradicted by observed access.
5. Exact graph, lifecycle, and closure-status parity holds under reversed task/frame order, common-ground/addressee stress, high-coupling and omitted-dependency controls, and dynamic ownership/deletion/reuse.

Measure candidate visits, Term evaluations, rule/matcher path counts, interface construction, owner updates, notification/requeue work, and wall/CPU/memory separately. Compare against both current monolithic closure and current full-fallback scoped closure; report cost only after semantic gates pass.

## Decision

The evidence supports a concrete optimization hypothesis, not an implementation claim. The current scoped API applies ownership filtering too late to reduce multi-edge candidate enumeration for this task family. The next engine experiment should first add an explicit, validated scope anchor to rule metadata and an opt-in seeded multi-edge matcher, while preserving the existing fallback. Keep this behind exact-order and cross-frame negative controls; do not make it the default based on the current parity-only pilot.

## Provenance

- [Measured v1.4 results](SUBSTRATE_CONVERSATION_TASK_SCOPE_PARITY_PILOT_V1_4_RESULTS_20261003.md)
- [Corrected v1.4.1 analysis](../../../evaluation/reports/conversation_task_scope_parity_pilot_v1_4_1_analysis_20261003.json)
- [`match_rule_each_for_scope` and `scoped_mt_seed`](../../../runners/dsl/src/rewrite.rs)
- [Rule metadata schema](../../../runners/dsl/src/rewrite.rs)
- [Conversation rule seed](../../../seeds/conversation_discourse_state.json)
