# P4 TermArena retention results

**Status:** the P4 temporary reflected-IR path no longer grows the substrate's logical TermArena for the sampled helper and route operations.

## Results

On the known reverse-string task, both prog_synthesis._eval_ir_on and prog_retrieval._eval_ir preserved the arena length at 4,465 nodes while returning the expected held-out output and restoring graph node count. After the P4 route, cumulative batches of 1/10/100 temporary five-node IRs were tested under root-only deletion and ownership-aware deletion.

| Cycles | Root-only graph growth | Safe graph growth | Arena growth in either arm |
|---:|---:|---:|---:|
| 1 | 4 nodes / 316 JSON bytes | 0 / 0 | 0 |
| 10 | 40 / 3,160 bytes | 0 / 0 | 0 |
| 100 | 400 / 31,600 bytes | 0 / 0 | 0 |

All seven revealed and held-out task rows passed after the lifecycle loops. The route construction was retrieved-exemplar, so this is not induction evidence. The result shows why graph cleanup and arena retention must be measured separately: truncation at graph materialization bounds AST entries for both cleanup controls, while only ownership-aware cleanup prevents graph-node accumulation.

The read-only term_arena_len() reports logical TermArena nodes, not vector capacity or RSS. Evidence covers one task and one five-node IR; it does not establish memory behavior across P4 task families, concurrent operations, arena capacity release, or all graph-materialization paths.

## Source ownership audit

The audited persistent TermIdx owners include grammar productions (where_ and weight), ConceptResolver, and ShapeCache keyed directly by TermIdx. evaluate, search, and relax_to_fixpoint already truncate temporary parse suffixes. In contrast, shape_of_term and add_shape_node_for_term cache by TermIdx and cannot be truncated without coordinated cache handling. add_term_subgraph and reflex stimulus loading only convert the parsed AST into durable graph nodes and do not retain the TermIdx; these are the paths changed to roll back the temporary arena suffix. This is a focused source census, not proof that every native/Python parse path has been classified.

Protocol: [P4 arena follow-up](SUBSTRATE_P4_TERM_ARENA_RETENTION_PREREG_20260925.md). Raw record: [P4 arena report](../../../evaluation/reports/substrate_p4_term_arena_retention_20260925.json). The API's local rollback edge cases are covered by [native rollback results](SUBSTRATE_TERM_ARENA_ROLLBACK_RESULTS.md).
