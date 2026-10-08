# Held-topic runtime interface trace v1.2 preregistration (2026-10-01)

## Motivation and implementation

The v1.1 capture identified 252 observed effect-time reads of attributes written by `SetAttrIfDifferent` that were absent from `Rule::read_set`. Update `derive_access` so `SetAttrIfDifferent` declares its key as both read and written, rebuild the optimized native extension from the current Rust source, and repeat the same seven-turn, three-fresh-worker held-topic capture. This is a focused repair plus confirmatory measurement; retain v1 and v1.1 artifacts unchanged.

The runner must load the rebuilt native package through `SUBSTRATE_NATIVE_PACKAGE`; lock the Python runner, analyzer, protocol, base task sources, and actual loaded native extension hash. Capture all eight `rule_access_sets()` fields and refresh the declaration map at each turn boundary. Preserve per-event resources, event kinds, worker freshness, dropped counts, task-quality oracle, and frame/interface fields from v1.1.

## Analysis and gates

For each mapped runtime read/write event, compare its concrete `attr:`, `edge:`, or `type:` key with the per-rule declaration and corresponding wildcard flag. Report explicit, conservative-wildcard, and uncovered observations separately. Report index queries lacking a concrete resource key separately. Require the classifications to account for all mapped observations, all observed rules to resolve, zero dropped trace events, stable locked inputs, seven turns in each of three fresh workers, exact trace/interface aggregate reconciliation, and repeated structural/runtime signatures. A zero-uncovered result is the target for the corrected effect; any remaining undercoverage fails dependency completeness and must be listed by rule, event kind, and resource. Keep task quality independent: the known “Can you tell me about copper?” clarification is expected to remain a failure under the current task source.

## Interpretation limits

This is a dynamic workload audit, not proof over unexecuted branches or all effect types. Wildcard access remains conservative and cannot establish bounded frame locality. Runtime hooks omit host work outside their coverage. No partitioned execution or tractability claim follows from a successful metadata reconciliation alone.
