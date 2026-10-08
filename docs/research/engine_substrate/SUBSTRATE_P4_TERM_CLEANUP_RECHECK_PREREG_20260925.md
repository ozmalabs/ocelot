# P4 reflected Term cleanup recheck preregistration

**Question.** After integrating native ownership-aware cleanup into temporary P4 evaluation helpers, do those helpers preserve outputs without retaining graph nodes, and does the API stop the measured 1/10/100-cycle graph growth?

## Workload and controls

Use the previously measured `contrast_reverse_string_01` task and its unchanged P4 standard route. After obtaining the accepted IR, exercise `domains.prog_synthesis._eval_ir_on` and `domains.prog_retrieval._eval_ir` on a held-out input and require expected output, successful ProgEval halt, and unchanged whole-Substrate node count. On that same fresh substrate, measure the legacy `add_term_subgraph` + `remove_node(root)` baseline and the new `add_term_subgraph` + `remove_term_subgraph(root)` cleanup at cumulative 1, 10, and 100 cycles. Record graph node count, compact whole-graph JSON bytes, wall/CPU time, and current RSS at each point. Finally rerun all seven task rows through ProgEval and require exact parity.

## Gate and limits

Pass only if both integrated temporary helpers preserve expected output and node count, legacy cycles reproduce positive retained-node growth, native cleanup cycles have zero retained-node or graph-byte growth, and all seven rows still pass. The acquisition route remains exemplar retrieval rather than induction. This probe measures one short Term and a generated task; it does not establish memory savings on large IRs, concurrent references, TermArena compaction, or natural task prevalence.
