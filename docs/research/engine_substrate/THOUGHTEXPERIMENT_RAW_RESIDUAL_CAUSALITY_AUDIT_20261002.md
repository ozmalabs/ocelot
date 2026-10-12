# Thoughtexperiment raw-residual causality audit — 2026-10-02

## Finding

The current native observability is not sufficient to diagnose a task-relevant residual from graph changes without caller-supplied target information.

- `RuleRunReport.last_progress_rule` identifies only the last rule that made progress during a settlement call. It does not identify all firings or their writes.
- `RuleStateTraceEvent` records selected numeric attributes on caller-selected nodes after a named rule fires. The caller must already know which rules, nodes, and attributes to watch; edges and general typed values are not included.
- `RuleGraphDeltaReport` records conservative node and edge mutation targets over the complete settlement call. It does not associate a mutation with a rule firing, preserve before/after values for each firing, or distinguish causative writes from no-op mutable accesses.
- The full snapshot-delta path is an aggregate before/after graph oracle. It is useful for correctness checks but cannot restore event-level causality.

Together these APIs can answer “which rule last progressed?”, “did this selected scalar change after this named rule?”, and “what graph locations may have been touched during settlement?” They cannot answer “which rule caused this unexpected edge or attribute, and which minimal residual should be returned from an isolated experiment?” Existing task-specific access traces do not close this gap: they are caller-instrumented resource observations and do not provide a generic, per-firing write-to-rule record.

## Remaining instrumentation and learning gates

Extend the current trace, if downstream diagnosis requires it, with match/binding identity (or a stable digest), field-level node-write keys, and before/after fact state. Deferred effects drained between rule attempts must be attributed to their originating invocation or explicitly marked deferred/unknown. Preserve truncation reporting and keep the default execution path unchanged.

The direct-write subset has passed the source-locked v1 reconciliation panel on add/set/delete and overlapping no-op fixtures. Next add deferred-effect fixtures and repeated-key/value attribution, then run a target-blind thoughtexperiment: supply only the task observation, expected outcome class, and isolated branch, and measure whether the substrate can identify the responsible rule/site and produce a useful residual without a supplied target rule, edit cue, or oracle-derived label. Include misleading correlated writes, multiple plausible rules, and abstention controls.

This is an instrumentation and learning gate, not yet evidence that causal attribution alone solves diagnosis. Per-firing tracing can expose the evidence needed for diagnosis; the substrate must still select explanations and operators from that evidence.

## Implementation increment

`run_rules_delta_report` now enables a bounded (100,000-event) per-invocation write-target trace. Each event reports the rule name, whether the attempt progressed, and deduplicated node/edge targets touched through graph mutation hooks. The existing aggregate report remains available in the same call. Event overflow is explicit. The ordinary runner does not enable the observer.

A rebuilt temporary Python extension and source-locked 3-process benchmark pass paired exact-delta reconciliation on mixed direct writes and overlapping/no-op writers. All three report fixed-point, progress, and pass parity; event targets cover exact changed nodes/edges; aggregate targets cover event targets; no events are dropped. Both overlap writers and a no-progress attempt appear in every worker. See [v1 results](THOUGHTEXPERIMENT_RULE_WRITE_ATTRIBUTION_V1_RESULTS_20261002.md).

The source changes are now installed in the workspace's normal release extension using `scripts/engine_build.sh`; the build record was refreshed and `build_is_stale('.')` returns no stale sources. Both fixtures were rechecked against that installed extension and retained exact-delta coverage and settlement parity.

The event schema remains deliberately incomplete: it does not include binding identity, per-fact before/after values, attribute keys for node writes, or proof that a listed producer was causally necessary. Deferred origins are now recorded across all five known queue families. Deduplicated RulePatch requests include an `origin_rules` set so the observer does not collapse multiple submitters into a single claimed cause. In the direct-write fixtures, median trace overhead was 1.48× and 1.61× ordinary closure; later queue probes validate semantics but do not measure instrumentation overhead. The trace identifies candidate rule-to-location links, not the causal explanation or minimal residual.

## Deferred queue origin increment

Source-locked panels now cover all five known deferred queues: RuleEdit, RulePatch, FbSample, NetCollapse, and TrackIdentity. RuleEdit separately verifies the live rule-store definition; RulePatch preserves a multi-producer set through deduplication; the other three reconcile graph targets to exact snapshot deltas. Each family has a bounded preregistered fixture; this is not a proof of global write causality, binding identity, attribute-key/value provenance, or target-blind diagnosis. See [TrackIdentity](THOUGHTEXPERIMENT_DEFERRED_TRACK_IDENTITY_ATTRIBUTION_V1_RESULTS_20261002.md), [NetCollapse](THOUGHTEXPERIMENT_DEFERRED_NET_COLLAPSE_ATTRIBUTION_V1_RESULTS_20261002.md), [RuleEdit](THOUGHTEXPERIMENT_DEFERRED_RULE_EDIT_ATTRIBUTION_V1_1_RESULTS_20261002.md), [FbSample](THOUGHTEXPERIMENT_DEFERRED_FB_SAMPLE_ATTRIBUTION_V1_RESULTS_20261002.md), and [RulePatch](THOUGHTEXPERIMENT_DEFERRED_RULE_PATCH_ATTRIBUTION_V1_RESULTS_20261002.md).

The action-geometry cue derivation and branch-isolation follow-up show the next boundary. A host-authored decoder maps opposite actions to a held operator; when this runs in a snapshot branch, exact primary graph/rule isolation holds and a single residual node returns the candidate. It still supplies the diagnosis mapping itself. The target-blind evaluation remains open: remove this mapping, give only raw task observation and graph/write evidence, and require the system to select or abstain among misleading correlated causes without a target name, edit cue, or oracle label. See [branch-isolation results](RESIDUAL_TO_COMPOSER_BRANCH_ISOLATION_V1_RESULTS_20261002.md).

## Source evidence

- Native report and event declarations: `runners/dsl/src/substrate.rs` (`RuleRunReport`, `RuleStateTraceEvent`, `RuleGraphDeltaReport`).
- Rule-state trace implementation: `Substrate::record_rule_state_trace` and `Substrate::tick_with_rule_state_trace` in `runners/dsl/src/substrate.rs`.
- Aggregate mutation observer: `Substrate::run_rules_delta_report` in `runners/dsl/src/substrate.rs` and graph mutation logging in `runners/dsl/src/graph.rs`.
- Current residual-to-cue result: [results](RESIDUAL_TO_COMPOSER_CUE_DERIVATION_V1_RESULTS_20261002.md). Its cue derivation is authored and its target selection is still supplied by the task workflow.
