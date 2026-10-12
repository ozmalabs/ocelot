# CAN bounded-width strip profile preregistration

**Question.** Across binary grid strips of fixed height h and increasing length, does runtime extraction preserve the generated model, exact junction-tree MAP agree with an independent transfer-matrix oracle, and measured cost grow with length and separator width as expected for bounded-width inference?

## Generator and oracle

Generate rectangular strips with h rows and m columns. Variables have deterministic seeded unary weights; pair factors connect vertical neighbors within columns and horizontal neighbors across columns. All states are binary {-1,+1}. Extract each model through can_network_from_mt and require exact factor parity.

The independent oracle performs dynamic programming over all 2^h column assignments and all predecessor/current pairs at each transition. It is structurally independent of junction-tree inference. The column-major elimination sequence is also measured against generic min-fill; both must yield maximum bag size h+1 and exact MAP energy equal to the oracle.

## Locked sweep

Run three fresh-process replicates for heights h=1,2,3,4,5 and lengths m=16,32,64,128. Measure extraction, min-fill ordering, exact junction-tree MAP using min-fill, exact MAP using column-major order, Python traced inference allocation, process peak RSS, and oracle operation count. Require min-fill induced width h, bag size h+1, exact extraction, and oracle agreement for both orders.

Lock the generator/runner, inference and treewidth sources, preregistration, native artifact, and native build record before execution. Results characterize this synthetic strip family only; they do not establish natural-task locality or frame discovery.
