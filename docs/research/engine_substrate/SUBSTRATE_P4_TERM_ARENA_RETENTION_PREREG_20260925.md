# P4 reflected Term arena retention follow-up preregistration

**Question.** After TermArena rollback is added to `add_term_subgraph`, do the actual P4 synthesis/retrieval evaluation helpers and repeated IR materialization avoid persistent AST growth, independently of graph-node cleanup policy?

## Procedure

Use the previously specified known reverse-string P4 task and fixture, but treat this as a lifecycle confirmation, not new learning evidence. On a fresh P4 adapter, record `term_arena_len()` before and after each temporary evaluation helper. Then at cumulative 1/10/100 IR cycles, run the same five-node IR through root-only deletion and ownership-aware deletion in separate cumulative batches, recording graph-node/JSON and TermArena deltas, timing, and RSS. Require both cleanup modes to show zero TermArena growth because rollback is attached to graph materialization; require root-only control to continue showing graph retention and ownership-aware cleanup to return graph/JSON to baseline. Recheck all seven task rows after the loops.

The native extension hash, changed source, P4 fixture/adapter sources, preregistration, and runner are locked before execution. This is one known P4 route and one fixed IR; retrieval remains the construction route and no induction/generalization claim is made.

## Interpretation boundary

`term_arena_len` is logical AST node count, not allocated capacity or RSS. The probe does not establish safe reclamation for persistent grammar/concept `TermIdx` owners, `shape_of_term` cache entries, reflex migration/persistence semantics, arena fragmentation, concurrent use, or realistic task distributions. Ordinary `pytest` is not part of this evaluation run.
