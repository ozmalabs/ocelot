# Live runtime closure counter capture v1.1 preregistration

Date: 2026-10-04

The v1 worker was stopped after its bounded diagnostic exceeded three minutes without output. It requested a duplicate access-trace snapshot inside an inherited worker that already collects that trace; no capture was completed. V1.1 maps the single inherited trace snapshot against per-request native rule exports instead.

## Design

Use the current-source live frame worker and its fixed two-request prompt pair. Run three fresh workers with scale audit disabled and three with it enabled (six total), paired by replicate. Reset counters before each request and enable the scale audit only during `WorldAdapter.converse`. Capture request outputs, graph digests, the inherited runtime RuleUID access rows, compact hashes/names for rules exported after each request, and global/per-rule/clause/edge counter rows. Retain the full graph and native rule export for rep 0 in the audit-on arm. Preserve worker failures, dropped traces, and unmapped UIDs. Request timing is not interpreted as audit overhead because rule exports and UID mapping add work; use the separate synthetic paired overhead estimate.

## Gates

Require parent and worker source/build locks; the full 3×2 schedule; two prompts per run; unchanged per-replicate task contract and semantic graph digest across audit modes; repeated graph semantics across workers; complete same-request runtime UID-to-definition mapping with zero missing UIDs; zero audit-off counters; and audit-on counter attribution/conservation: no ambiguous metadata IDs, no unattributed candidate/Term counts, per-rule pairs equal global enumerations, per-rule tests and clause rows conserve global tests, edge candidate counts conserve per-rule pairs, and candidate path and first/repeat partitions conserve global enumeration.

## Claim boundary

This is a selected six-worker, two-request production-route panel. It measures counters on rules exercised by these prompts, not natural conversation prevalence, all matcher paths, frame discovery, or general task capability.
