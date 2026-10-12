# Conversation task-scope parity pilot v1.4 preregistration

Date: 2026-10-04

## Question

Does the exact-state result from the v1.2 conversation scope pilot reproduce with a complete direct source lock, and how much scheduler/rule work does its conservative global resweep perform relative to monolithic closure?

## Workload

Reuse v1.2's four authored cases: concurrent goals at 2, 4, and 8 task frames, plus the 4-frame common-ground stress case. Run three fresh workers. Compare each monolithic closure checkpoint with the globally reswept task-scope implementation. Task-frame roots and unchecked ownership annotations remain measurement scaffolding inserted symmetrically in both arms.

## Added measurement

At each closure checkpoint, disable concrete access-row tracing and enable the native all-scope operation-work tracer. Retain each work row's graph scope, operation ID, RuleUID, event kind, subject, and work units. Reset between checkpoints. Capture monolithic and partition-sweep closure identically. Keep existing scale counters and per-scope quiescence records.

The scoped closure path has its own full-sweep loop, separate from the monolithic dirty-bit scheduler. The native recorder therefore adds explicit event kinds for scoped fixpoint passes, attempted active-rule slots, and rules that made progress. These events use distinct names from monolithic scheduler slots; the comparison reports them as scoped-loop work, not as equivalent scheduler operations.

## Gates

1. Provenance-current native engine; source lock covers runner, analyzer, panel, workload/seed inputs, native extension/build manifest, and `term.rs`, `rewrite.rs`, `substrate.rs`, `graph.rs`, `access_trace.rs`, and `py.rs`.
2. Three fresh workers cover exactly the 2/4/8-goal cases and common-ground stress case; lock is stable before/after.
3. Final graph, every checkpoint graph, goal states, and common-ground facts match monolithic closure; all closures reach fixed points.
4. Every partition scope has a quiescence record with zero progress and no deferred effects; notification completeness remains reported verbatim.
5. Work-trace drop count is zero. Work rows are captured on both arms; report operation counts, event-kind units, RuleUID-zero work, and graph-scope totals. Scoped rows include scoped pass, rule-attempt, and progressing-rule events; monolithic rows retain native scheduler detail. No work amount is inferred from timing.
6. Independent analyzer recomputes case matrix, graph digests, equality flags, operation-work summaries, and gates from the retained capture.

## Interpretation boundary

This measures explicit ownership scopes and exhaustive resweeping on one authored conversation family. It does not establish learned frames, complete dependency recall, semantic factorization, natural-task prevalence, or speedup. Work events quantify selected scoped-loop and monolithic scheduler work; concrete graph-read tracing remains partial.
