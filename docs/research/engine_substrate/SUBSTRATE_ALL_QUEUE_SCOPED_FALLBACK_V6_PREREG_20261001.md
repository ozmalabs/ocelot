# Scoped/full snapshot drain with cross-binding where invalidation v6 preregistration

Date: 2026-10-01

## Question

When a rule snapshots several bindings whose where-clause is initially true, does scoped closure apply every distinct snapshot binding if an earlier binding changes a later binding's where-clause truth before its effects are applied?

## Design

Reuse the five-queue cyclic workload with R={1,8,32}, M={1,4,16}, and three fresh worker processes per cell. Each `JoinMiddle` starts with `eligible=true`; the writer rule's where clause requires that attribute to remain true. For M=4/16, binding j first sets its successor's `eligible=false`, then deletes that successor's unique `right_i` driver edge. M=1 is a single-binding control which changes its own attribute. All effects follow the engine's binding snapshot. The dependent verifier and all five deferred effect families remain enabled.

Compare direct full closure, scoped-only closure, and scoped-plus-global-fallback using separate identical fixtures. The semantic check asks whether all R×M snapshotted bindings contribute their handled/verifier output despite later predicate or structural invalidation, and whether full and fallback canonical graph facts agree. Exact graph wire order and selection metadata are descriptive.

## Expected invariants

- All initially eligible middle nodes receive the first-effect update; final eligible count is zero in each arm.
- Full and scoped-plus-fallback reach fixed point and have equal canonical node/edge facts.
- Settled arms have R×M handled and verified edges, R `seen_i` edges, 4R frame cells, zero remaining `right_i` edges and trigger edges.
- Queue totals and operation traces reconcile as preregistered in prior five-family probes; scoped-only reports pending deferred work and fallback drains it.
- Source/native fingerprints are stable; raw captures are retained separately.

## Limits

This is one cyclic match shape and one attribute-based `Eq(Attr(mid, eligible), true)` predicate. It does not establish semantics for arbitrary nested predicates, external callbacks, node deletion, cross-frame scopes, or natural tasks. M=1 is not a cross-binding test. No asymptotic or general scope-completeness claim follows.
