# Native runtime access-trace smoke measurement

**Run date:** 2026-09-25  
**Evidence grade:** instrumentation smoke measurement  
**Status:** the opt-in trace emits the expected concrete events and enabled/disabled closure has exact graph and progress parity on the controlled fixture.

## Instrumentation surface

The default-off native trace is implemented in [`access_trace.rs`](../../../runners/dsl/src/access_trace.rs) and exposed through the `PySubstrate.runtime_access_trace_*` methods in [`py.rs`](../../../runners/dsl/src/py.rs). It groups counts by stable `RuleUid`, event kind, concrete node/edge IDs, and resource name. It has a cap of 250,000 distinct event keys; overflow is explicit in the snapshot. The current event families are successful pattern-edge bindings, interpreted `Attr` and `TypeOf` reads, and selected effect writes/deletes/mints plus the `AddNodeIfAbsent` type scan.

## Paired fixture

[`substrate_runtime_access_trace_smoke_v1.py`](../../../scripts/substrate_runtime_access_trace_smoke_v1.py) runs a one-edge reader rule twice, with tracing enabled and disabled. The rule has a `where`-clause `Attr` read, an effect-value `Attr` read, a `SetAttr`, and an `AddEdge`. Both arms use the same graph/rule fixture. The runner requires exact final graph and progress parity, terminal zero progress in both arms, the expected trace kinds under the correct UID, no events in the disabled arm, and no dropped events.

All nine checks passed. The traced arm returned four aggregated rows: one pattern edge (`TraceRoot --trigger--> TraceTarget`), two reads of the root's `watched` attr (where and effect value), one target `observed` attr write, and one derived-edge upsert. The untraced arm returned zero events. Raw rows and source/build hashes are in [`substrate_runtime_access_trace_smoke_v1_20260925.json`](../../../evaluation/reports/substrate_runtime_access_trace_smoke_v1_20260925.json). The engine was built through [`engine_build.sh`](../../../scripts/engine_build.sh), which regenerated and checked the native build record.

## Limits and next gate

This verifies plumbing and semantic parity on one small rule. It does not measure trace overhead, event-cap behavior, CAN/conversation workload coverage, or locality. It is not a complete runtime access log: JIT predicates, aggregate/traversal Term footprints, several effect kinds, external host mutations, and some specialized runner paths are not covered. The trace is process-global, so measurement workers must isolate one substrate at a time. An event's absence is not proof of dependency absence. Next add coverage counters for instrumented versus omitted operation families, then run bounded tracing on CAN and conversation alongside untraced twins and the existing static `rule_access_sets()` projection.

The repository-wide `cargo fmt --check` reports formatting differences across many pre-existing unrelated Rust files; none were mass-formatted as part of this probe.
