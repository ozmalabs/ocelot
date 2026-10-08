# Term external-dependency probe v1 results

Date: 2026-09-28

## Results

Three fresh workers completed all six preregistered cells; the independent analyzer passes 15 checks, including source/native lock equality, child command/stream hashes, unique PIDs, zero trace drops, and identical outcomes across workers.

- **`ReadFile`:** `alpha` and `beta` file contents become their corresponding graph values. The rule declares only `edge:trigger` as a read and has `reads_any=false`; traces show the pattern edge and result write but no file-read event. A missing file writes `None`. This confirms that filesystem contents are invisible to the graph access set and current trace. An external file change has no declared dependency by which the graph scheduler could be notified; this is an inference from the captured access schema and source behavior, not a separately exercised live-file update schedule.
- **Registered `UseTool`:** the rule declares `reads_any=true`. Each one-match settle makes two Python callback invocations and two successful native fire-count increments, while producing one graph progress step. The trace records two `term_tool_dispatch` events. This reveals callback re-execution during the no-progress settle pass in this fixture; callback side effects can therefore exceed graph progress.
- **Trace and missing-handler controls:** disabling tracing leaves callback count, result, and progress unchanged and emits no rows. An absent handler still emits two dispatch events but makes zero successful callback/fire increments and writes the `Int(0)` fallback.

The repeated callback finding matters to the operating-cost and effect model: rule firing counts alone understate host callback work in this workload, and externally effectful handlers need an idempotency or deduplication contract. The exact two-call count is fixture-specific; it is not a general bound.

## Claim boundary

This is a synthetic one-rule result, not a natural workload estimate, security/containment evaluation, or complete access-trace audit. `UseTool`'s wildcard protects graph scheduling conservatively, but it does not record handler-internal resource accesses. `ReadFile` is deliberately not a graph wildcard because file contents are not graph resources; incremental rule execution cannot infer filesystem changes from `RuleKey` alone. `ProgCallExtern` is not dynamically exercised here because the current Program IR uses the in-engine native oracle whitelist.

## Reproduction

The protocol, source/native lock, three-worker runner, and independent analysis are linked here: [preregistration](SUBSTRATE_TERM_EXTERNAL_DEPENDENCY_PROBE_V1_PREREG_20260928.md), [lock](../../../evaluation/substrate_capability/term_external_dependency_probe_v1_lock_20260928.json), [runner](../../../scripts/substrate_term_external_dependency_probe_v1.py), [raw capture](../../../evaluation/reports/term_external_dependency_probe_v1_20260928.json), [analyzer](../../../scripts/analyze_term_external_dependency_probe_v1.py), and [analysis](../../../evaluation/reports/term_external_dependency_probe_v1_analysis_20260928.json).
