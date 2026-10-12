# Live runtime closure counter capture v1.3 preregistration

Date: 2026-10-04

No prior live counter attempt produced a usable capture. V1/v1.1 passed worker arguments that their dispatcher did not recognize, causing child re-entry. V1.2 ran all six workers successfully but referenced the prompt list on the wrong imported module and failed before writing the archive. V1.3 fixes prompt lookup and durably appends each worker record before starting the next. It retains v1.2's single-trace UID mapping; it does not take a second access-trace snapshot.

## Design

Use the existing current-source live frame worker and fixed two-request prompt pair. Run three fresh workers with native scale audit disabled and three enabled (six workers), paired by replicate. Reset counters per request, enable scale audit only during `WorldAdapter.converse`, and capture request outputs, graph digests, inherited runtime RuleUID access rows, compact hashes/names for post-request native rule exports, and global/per-rule/clause/edge counter rows. Retain the full graph and native rule export for rep 0 in the audit-on arm. Append each worker durably to a partial JSONL capture before continuing; produce the compressed aggregate only after the complete schedule. Preserve worker failures, dropped traces, and unmapped UIDs. Do not interpret conversation timings as counter overhead; rule export adds unpaired work.

## Gates

Require a current source/build lock; complete crossed design and two prompts per worker; paired task contract and semantic graph digests identical across counter modes; semantic digest stable across workers; complete same-request UID-to-definition mapping with zero missing UIDs; zero audit-off counters; and audit-on attribution/conservation: unambiguous metadata IDs, zero unattributed candidate/Term events, per-rule candidate pairs equal global enumerations, per-rule candidate tests and clauses conserve global tests, edge candidate rows conserve per-rule pairs, and candidate-path and first/repeat counters conserve global enumeration.

## Claim boundary

Six selected workers over two authored prompts measure rules exercised on this production route. No claim about natural conversation prevalence, universal instrumentation coverage, frame discovery, or general task capability follows.
