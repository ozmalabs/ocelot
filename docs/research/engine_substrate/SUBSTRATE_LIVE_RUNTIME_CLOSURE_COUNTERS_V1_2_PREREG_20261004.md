# Live runtime closure counter capture v1.2 preregistration

Date: 2026-10-04

The v1 and v1.1 attempts produced no usable captures. Both child dispatchers matched a bare `--worker` argument although the parent passes replicate and mode values, causing children to re-enter the parent path. V1.2 fixes the worker argument dispatch. V1's redundant access-trace snapshot has also been removed: runtime UIDs will be resolved from the single access trace collected by the inherited worker against the post-request rule exports.

## Design

Use the current-source live frame worker and its fixed two-request prompt pair. Run three fresh workers with native scale audit disabled and three enabled (six workers), paired by replicate. Reset counters before each request and enable the scale audit only during `WorldAdapter.converse`. Capture request outputs, graph digests, inherited runtime RuleUID access rows, compact hashes/names for rules exported after each request, and global/per-rule/clause/edge counter rows. Retain the full graph and native rule export for rep 0 in the audit-on arm. Preserve worker failures, dropped traces, and unmapped UIDs. Request timings are not interpreted as counter overhead: the hook adds per-request rule export, and the synthetic paired panel separately measures instrumentation overhead.

## Gates

Require parent and worker source/build locks; complete 3×2 design; two prompts per run; identical paired task outcomes and semantic graph digests across audit modes; repeated graph semantics across workers; complete same-request RuleUID-to-definition mapping with zero missing UIDs; zero audit-off counters; and audit-on counter attribution/conservation: no ambiguous metadata IDs, no unattributed candidate/Term counts, per-rule candidate pairs equal global enumerations, per-rule tests and clause rows conserve global tests, edge candidate rows conserve per-rule pairs, and candidate-path and first/repeat partitions conserve global enumeration.

## Claim boundary

This is a selected six-worker, two-request production-route panel. It measures counters for rules exercised by these prompts, not natural conversation prevalence, all matcher paths, frame discovery, or general task capability.
