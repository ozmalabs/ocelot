# Live runtime closure counter capture v1 preregistration

Date: 2026-10-04

## Question

Measure native per-rule matcher work during actual production-route conversation requests and check that scale-audit collection preserves task outputs and graph state.

## Design

Use the existing source-locked live frame worker and its fixed two-request prompt pair. Run three fresh workers with native scale audit disabled and three with it enabled (six total). Each request gets a fresh counter reset; audit is enabled only during `WorldAdapter.converse`. Counter arm assignment is paired by replicate. Capture request outputs, graph digests, runtime RuleUID access rows, observed RuleUID-to-native-definition mappings, scale-audit global/per-rule/clause/edge rows, and source fingerprints. Retain the full graph and native rule export for rep 0 in each mode. Preserve extraction failures and unmapped UIDs.

## Gates

Require source/build/input lock stability in parent and every worker; identical prompt schedules and request/task outputs across audit modes and replicates; matching semantic graph digests; two observations per worker; runtime access UID mapping against same-request native definitions with zero missing UIDs; zero audit-off counters; and audit-on counter attribution/conservation: no ambiguous metadata IDs, no unattributed candidate/Term counts, per-rule candidate pairs equal global candidate enumerations, per-rule candidate tests and clause rows conserve global tests, edge candidate rows conserve per-rule candidate pairs, and global candidate path and first/repeat partitions conserve. Do not interpret request timings as audit overhead: the counter hook also exports definitions and joins observed runtime RuleUIDs to hashes. Instrumentation overhead has a separate controlled measurement.

## Claim boundary

This is a six-worker selected production-route conversation panel. It measures counters on rules exercised by two prompts and does not establish natural conversation prevalence, exhaustive counter coverage, exact replay of arbitrary dialogue states, cheap-cut discovery, or general task capability.
