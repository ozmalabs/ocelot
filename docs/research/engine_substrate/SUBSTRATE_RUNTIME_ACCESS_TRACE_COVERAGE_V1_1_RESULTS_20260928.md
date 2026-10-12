# Native runtime access-trace coverage audit v1.1 results

Date: 2026-09-28

## Current-source replay

The v1 source audit no longer ran against the current `access_trace.rs`: its expected UID-only guard had been replaced by a scope-aware guard, and its fixed output path would overwrite the historical v1 capture. The runner now accepts `--output`, anchors the current rule/scope guard, and retains the old output path only as its default. The current-source replay was written to a separate v1.1 artifact.

The source-hashed audit finds 237 `TermNode` variants, 18 declared trace event kinds, and eight trace-coverage findings. The enum counter now includes the underscore in `Vec_`; the previous regular expression counted 236. Six source files are hashed in the report (`access_trace.rs`, `term.rs`, `shape_decode.rs`, `rewrite.rs`, `jit.rs`, and `world_adapter.py`). This is an inventory refresh, not a dynamic recall or coverage-percentage result.

The rule-scoped trace now rejects events when the current rule UID is zero, the current scope is zero, or the scope differs from the active scope. The audit accordingly reports scope identity as part of the attribution boundary. Its existing findings continue to separate partial instrumentation (including successful matcher bindings and selected Term reads) from known omissions: host callbacks, unchanged `SetAttrIfDifferent` reads, failed candidate identities, scheduler/out-of-rule work, and post-rule queued effects. Some omission paths have bounded falsifier probes, but no workload-wide trace-recall estimate or complete host/scheduler attribution exists.

## Next gate

Use a task capture that counts total matcher and scheduler work independently of trace rows, explicitly accounts for host callbacks and post-rule effects, and reports no-ID and excluded-class totals. Reconcile these with static access scopes before projecting candidate frames. Continue to treat the 237-variant Term crosswalk as mechanical/source review with lexical limits, not proof that generic child-walk Terms or the full runtime access path are graph-pure.

## Reproduction

```sh
python3 scripts/substrate_runtime_access_trace_coverage_audit_v1.py --output evaluation/reports/substrate_runtime_access_trace_coverage_v1_1_20260928.json
```

Artifacts: [runner](../../../scripts/substrate_runtime_access_trace_coverage_audit_v1.py), [source-hashed report](../../../evaluation/reports/substrate_runtime_access_trace_coverage_v1_1_20260928.json), [Term access crosswalk](../../../evaluation/reports/term_access_dependency_coverage_v1_20260928.json), and [runtime trace coverage audit v1](SUBSTRATE_RUNTIME_ACCESS_TRACE_COVERAGE_AUDIT_V1_RESULTS_20260926.md).
