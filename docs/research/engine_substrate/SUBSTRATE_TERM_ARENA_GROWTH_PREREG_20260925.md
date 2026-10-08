# Reflected Term arena growth preregistration

**Question.** Does ownership-aware graph cleanup reclaim the AST nodes allocated while temporary reflected Terms are parsed, or does the substrate's TermArena retain them across repeated cleanup cycles?

## Procedure

Use the same fixed four-node `Cat(Lit, Reverse(Var))` Term JSON as the ownership probe. In a Rust harness with a fresh `Substrate`, record initial graph and arena counts, then at cumulative 1, 10, 100, and 1,000 cycles parse JSON with `term_from_json`, reflect with `term_to_subgraph`, and clean the graph root with `remove_term_subgraph`. Record TermArena length, graph node count, child Term graph count, and elapsed time at each checkpoint. Run a separate fresh substrate with root-only `remove_node` as a graph-retention control. No graph or arena compaction is expected by the operation under study.

Use only the Rust library APIs to inspect `Substrate.terms.len()`; this avoids adding a new public diagnostics method. The example source and protocol are content-locked before execution. The run records compiler version, source hashes, and output JSON. This is an evaluation harness, not a test suite.

## Interpretation boundary

Arena node count establishes logical AST retention, not allocator capacity or RSS. The fixed tree cannot establish growth by realistic IR size, varied branching, failure-path parsing, or arena-compaction benefit/cost. Timing is descriptive only and includes parsing, reflection, and cleanup.
