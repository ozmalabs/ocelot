# Preregistration: verified forest ordering with generic fallback

**Question.** Does a graph-theoretic forest check safely select leaf elimination for forests and preserve the current min-fill behavior for cyclic inputs, while retaining exact MAP on cases admitted by the existing width-4 gate?

**Frozen workload.** Run 66 isolated worker cases: three replicates over paths, balanced binary trees, cycles, ladders, and seeded sparse-random path-plus-chord graphs at n=32/64/128/256; plus cliques at n=8/12. Build each factor graph as a native Substrate Microtheory, extract it through the current CAN extractor, then run union-find cycle detection. If and only if the graph is a forest, construct a leaf-elimination order; otherwise reuse the already-computed generic min-fill order. The benchmark runs exact MAP for both orders only when min-fill upper bound is at most four; over-gate cases are counted as refused and are not sent to the solver.

**Primary measures.** Extraction parity, forest detector result, min-fill and selected order widths, candidate exact-gate status, detector/order/MAP timings, paired exact energy where admitted, and per-family records. The comparison includes the forest check and any selected-order construction; the fallback reuses the already computed min-fill order.

**Pass criteria.** All positive forest controls are detected; every cyclic family control is rejected; the guarded gate decision equals the min-fill gate; every admitted paired MAP result agrees in energy and bag width; all predeclared replicates complete. No speed threshold is required.

**Scope.** This measures a benchmark-level dispatch policy on generated topologies. It does not implement a production API or establish that natural workload graphs are forests. Forest structure is certified by union-find over the complete extracted edge set; cycles must fall back to min-fill.
