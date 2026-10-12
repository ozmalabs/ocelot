# Scoped/full snapshot drain with cross-binding edge deletion v5.1 preregistration

Date: 2026-10-01

## Question

Does scoped all-binding drain preserve full-closure outcomes when a matched binding deletes the unique driver edge of another binding that was already captured in the same match snapshot?

## Design

Reuse the R×M five-queue, distinct-write, verifier workload. For M=4 and M=16, construct M middles in a directed cycle; each middle has a `right_i` edge to the shared target and a `next_i` edge to its successor. Each snapshotted binding first deletes the successor's unique `right_i` edge, invalidating a later binding's match driver. M=1 is explicitly a single-binding control: omit the next edge and delete its own right edge. The matcher requires distinct bindings for distinct pattern variables, so a one-node self-loop would produce zero matches and is not used. The shared trigger deletion remains a separate common-edge control.

Compare direct full closure, scoped-only closure, and scoped-plus-global-fallback on independent fixtures with R={1,8,32}, M={1,4,16}, and three fresh-process replicates. Retain all five deferred queues and the dependent verifier rule. Do not use edge-order or serialization-tail assumptions as semantic oracles.

## Expected invariants

- Full and scoped-plus-fallback settle at fixed point and have equal canonical node/edge facts. Exact graph-wire equality is recorded separately because slab reuse may change serialization order.
- Each settled arm has R×M handled and verified edges, R target `seen_i` edges, 4R frame cells, zero remaining `right_i` edges, and zero trigger edges.
- Exactly R×M unique right-driver deletions and R trigger deletions occur (R×(M+1) rule-effect edge deletes).
- All five queue families retain expected totals: RulePatch R by shared-patch deduplication; the other families R×M. Scoped-only leaves these effects pending; fallback drains them without additional writer enqueues.
- Matcher continuation's selected NodeID is descriptive only. Runtime edge arrays are retained raw; no selection-equals-serialized-tail condition is asserted.
- Every operation-work queue trace reconciles with scale-audit counters with zero dropped rows; source/native fingerprints remain stable.

## Limits

This tests stale snapshotted bindings after cross-binding deletion in one cyclic relation shape. It does not cover node deletion, writes changing where-term truth, deletion of a rule's entire shared driver, arbitrary graph scopes, or natural-task prevalence. M=1 does not test cross-binding deletion. This is not a broad scope-completeness or asymptotic result.
