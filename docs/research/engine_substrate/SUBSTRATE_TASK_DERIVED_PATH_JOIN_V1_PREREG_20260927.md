# Task-authored three-edge path join replay v1 preregistration

Date: 2026-09-27 local

## Question

Does authored edge order change native candidate work for a distinct task-family rule with a three-edge path topology, and does the current seed rule still derive its commit effects exactly when the input contains disconnected relation decoys?

## Rule and fixture

Use `self_change_reasoning.json::sc_canary_requests_commit` without changing its where clause or effects. Its match is the path `SelfChange -selected_patch→ RulePatch -has_canary→ Canary -has_canary_evidence→ CanaryEvidence`. Build `M={1,8,32}` independent positive paths sharing the SelfChange source. For `D/M={0,4}`, add D isolated decoys to each relation type, giving every relation the same global cardinality while creating no additional complete paths. Populate patch/canary/evidence attributes to satisfy the authored rule’s actual guards. Vary all six authored permutations of the three match clauses; run three fresh-process repeats per cell (108 workers total).

Each worker runs plain and audit-on twins. The audit arm records exact native candidate tests by installed clause and per-rule counters. The existing effects create Commit nodes/edges, queue/apply the patch operation, and update canary/patch/self-change state. A separate expected-output oracle checks M commits and commit edges, exact transition attributes on the M positive paths, unchanged decoys, and fixed-point completion. Compare normalized graphs across orderings because minted node identifiers can depend on match iteration order.

## Admission gates

- 108 unique `(M,D/M,authored permutation,replicate)` fresh workers with stable source/native inputs.
- Plain/audit normalized graph and closure-report parity within each worker.
- Every worker reaches fixed point without progress-budget overshoot and exactly M true-path commits/commit edges.
- All M positive canaries become passed, their patches become transaction-queued, the source reaches commit-ready, and decoys remain unchanged.
- Target-rule clause candidate tests conserve to target-rule candidate tests at every worker; read back the installed edge order.
- For each graph setting, normalized terminal state is invariant across all six authored orders and repeats.

## Scope boundary

This is one real self-change policy rule over a controlled task-shaped graph, with disconnected synthetic decoys and an independent effect oracle. It tests a path topology distinct from the cyclic common-ground rule. It does not establish real production-state prevalence, general order optimization, or uninstrumented speed. Report the current rule’s extra effect and per-match costs separately from candidate tests.
