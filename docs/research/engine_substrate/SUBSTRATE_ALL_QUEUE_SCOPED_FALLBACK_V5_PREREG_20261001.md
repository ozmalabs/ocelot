# Scoped/full snapshot drain with cross-binding edge deletion v5 preregistration

Date: 2026-10-01

## Question

Does the scoped all-binding drain preserve full-closure outcomes when each matched binding deletes the unique driver edge of a different binding that was already captured in the same match snapshot?

## Design

Reuse the R×M five-queue, distinct-write, verifier workload. For each writer, construct M middles in a cycle. Each middle has its normal `right_i` edge to the shared target and one `next_i` edge to its successor. Extend the writer pattern with the successor binding. As its first effect, each binding deletes the successor's unique `right_i` edge. Thus every match set is collected before mutation, and the first applied binding invalidates the edge supporting a later snapshotted binding. The cycle ensures every `right_i` edge is targeted exactly once, including the M=1 self-loop case. The shared trigger deletion remains as a separate common-edge control.

Compare direct full closure, scoped-only closure, and scoped-plus-global-fallback on independent identical fixtures with R={1,8,32}, M={1,4,16}, and three fresh-process replicates. Retain the order-sensitive matcher continuation from v4, all five deferred queues, and the dependent verifier rule. No edge sorting or normalization is used in runtime execution.

## Expected invariants

- Full and scoped-plus-fallback settle at fixed point and have equal canonical node/edge facts; report strict graph-wire equality separately because slab reuse may change serialization order.
- Each settled arm has R×M handled and verified edges, R target `seen_i` edges, 4R frame cells, zero remaining `right_i` cycle edges, and zero trigger edges.
- Exactly R×M right-driver deletions and R trigger deletions occur (R×(M+1) actual rule-effect edge deletes).
- All five queue families retain the expected totals: RulePatch R by shared-patch deduplication; the other families R×M. Scoped-only leaves these effects pending; fallback drains them without additional writer enqueues.
- The order-sensitive selected NodeID and per-arm edge arrays are recorded, not sorted; the result is descriptive and not used to hide graph-state mismatches.
- Every operation-work queue trace reconciles with scale-audit counters and has zero dropped rows; source/native fingerprints remain stable.

## Limits

This directly tests stale snapshotted bindings after cross-binding deletion in one cyclic relation shape. It does not cover node deletion, writes changing where-term truth, deletion of a rule's entire shared driver, arbitrary graph scopes, or natural-task prevalence. Exact facts and scheduler semantics are evaluated for this fixture only.
