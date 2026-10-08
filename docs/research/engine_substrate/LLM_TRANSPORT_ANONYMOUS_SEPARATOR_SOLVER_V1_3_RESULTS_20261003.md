# LLM transport anonymous-separator solver v1.3 results

The three-worker v1.3 capture and independent analysis pass every gate across 60 cells. In each worker, one graph-only search over anonymous node IDs finds both minimum 8-variable separators on the connected K₈,₈ topology. Its exact node/edge signature remains identical across all 20 held-out/control cells, so the proposal is reused 19 times. The solver executes one deterministic minimum separator per cell. Every returned state matches monolithic JT energy and target signs exactly and passes direct rescoring; learned accuracy is 0.800 and shuffled accuracy 0.413.

Median generic conditioned-solver time is 212.37 ms (learned) and 212.00 ms (shuffled), compared with 532.63–532.73 ms for monolithic JT. The one topology search takes a median 311.49 ms per worker, or 15.57 ms per cell when spread over 20 identical-topology cases. Total measured structural-route batch time is 4.60–4.71 s versus 10.57–10.63 s for monolithic JT, a median 2.28× batch advantage. In contrast, v1.2's per-cell search and solving both separators took 738 ms per cell and was slower than JT. Exact signature caching and avoiding redundant candidate solves close that measured gap on this repeated workload.

This is direct evidence that anonymous graph-only proposals can feed a generic exact solver and be reused safely when the exact topology signature matches. The graph remains one fixed authored K₈,₈ family from one model transition, so the experiment does not show that natural tasks commonly have reusable small separators or that exhaustive search scales. Next test varied independently sourced graph families, measure signature and separator reuse under genuine structural variation, and include an optimized monolithic baseline.

## Reproducibility artifacts

- [Base protocol](LLM_TRANSPORT_ANONYMOUS_SEPARATOR_SOLVER_V1_PREREG_20261002.md), [factor-precompute amendment](LLM_TRANSPORT_ANONYMOUS_SEPARATOR_SOLVER_V1_1_AMENDMENT_20261002.md), [component-set correction](LLM_TRANSPORT_ANONYMOUS_SEPARATOR_SOLVER_V1_2_AMENDMENT_20261002.md), and [cache/selection amendment](LLM_TRANSPORT_ANONYMOUS_SEPARATOR_SOLVER_V1_3_AMENDMENT_20261003.md)
- [Runner](../../../evaluation/substrate_capability/llm_transport_anonymous_separator_solver_v1.py)
- [Independent analyzer](../../../evaluation/substrate_capability/analyze_llm_transport_anonymous_separator_solver_v1.py)
- [Source lock](../../../evaluation/substrate_capability/llm_transport_anonymous_separator_solver_v1_3_lock_20261003.json)
- [Raw capture](../../../evaluation/reports/llm_transport_anonymous_separator_solver_v1_3_20261003.json)
- [Analysis](../../../evaluation/reports/llm_transport_anonymous_separator_solver_v1_3_analysis_20261003.json)
- [Uncached v1.2 comparison](LLM_TRANSPORT_ANONYMOUS_SEPARATOR_SOLVER_V1_2_RESULTS_20261002.md)
