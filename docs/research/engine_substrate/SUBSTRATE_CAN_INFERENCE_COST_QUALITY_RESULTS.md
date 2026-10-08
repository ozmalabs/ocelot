# Current-source CAN inference cost and quality envelope

**Run date:** 2026-09-25  
**Raw artifact:** [`can_inference_cost_quality_envelope_20260925.json`](../../../evaluation/reports/can_inference_cost_quality_envelope_20260925.json)  
**Runner:** [`can_inference_cost_quality_envelope.py`](../../../scripts/can_inference_cost_quality_envelope.py)

## Question and protocol

This paired microbenchmark asks whether the current exact and approximate CAN inference paths return the right state on the same small graph snapshots, and separates their measured work. It generated 24 deterministic 3-state Ising/CAN instances: path, cycle, complete, and seeded sparse-random topologies; 5, 7, and 9 nodes; two replicates per cell. Each case used the current graph extractor and solver modules. The exact path was evaluated directly and through the integrated width gate (bound 4); max-product loopy BP ran for at most 40 rounds at epsilon 1e-7. Native discrete relaxation used the production CAN update seeds and 20 restarts with a case-derived deterministic RNG seed, on a separate copy of each graph. An independent exhaustive enumerator checked all 3^n assignments and an independently coded objective was compared with native `mt_energy`. BP/exact calls were noncommitting; the relaxation mutation was isolated and its extracted input energy network was checked before and after.

The runner records separate nanosecond timings for extraction, min-fill width, standalone triangulation, triangulation inside junction-tree MAP, message/backtracking, total exact MAP, integrated gated exact call, exhaustive enumeration, BP, seed loading, multi-start relaxation, and the terminal stability probe. It also records Python `tracemalloc` peak for the relaxation call. These are in-process microbenchmark timings from one host/run, with no warmup protocol; `tracemalloc` excludes native Rust allocations and is not process peak RSS. Treat timings as descriptive, not stable service-level estimates.

## Results

- **Exact answer quality:** junction-tree MAP equalled exhaustive MAP on all 24 directly evaluated cases, including the four above the integrated gate. Native energy matched the independent objective on all 24. All noncommitting calls preserved graph state.
- **Width gate:** integrated exact was attempted in 16/24 cases with measured min-fill bound at most 4 and refused in 8/24 cases above 4. The four complete-graph instances at n=7/9 were all refused; the separate direct exact calls demonstrate why width gating matters, not a supported operating point. The configured width predicate matched every attempt/refusal.
- **BP:** 20/24 runs converged. One converged run had a nonzero MAP energy gap (0.5), directly showing convergence does not guarantee the optimum. All four n=9 complete cases failed to converge, with gaps 1.5–3.5. Other nonconverged cases had gaps 0 or 0.5. Thus convergence and answer quality are distinct measures.
- **Native multi-start relaxation:** all 24 cases produced 20 candidates, preserved the input unary/pairwise network, and passed a zero-progress terminal fixed-point probe. Its selected state matched exhaustive MAP in 11/24 cases; the median gap was 0.25 and maximum 3.0. BP matched the optimum in 19/24 cases on this same set, with median gap 0 and maximum 3.5. Per case, BP had a smaller gap in 9, multi-start in 3, and they tied in 12. The native chooser minimizes `mt_frustration_given_state`; the benchmark independently scores selected states by the MAP energy objective. This small sample does not establish general ranking between methods.
- **Cost by topology:** median exact MAP time was about 0.09–0.69 ms for n=5, 0.11–8.45 ms for n=7, and 0.14–79.13 ms for n=9. At n=9, bounded-width paths/cycles were 0.14/0.35 ms, while complete graphs (width bound 8) took 79.13 ms in the direct ungated diagnostic. The integrated gate itself remained below 1.46 ms across the measured cells. BP medians were approximately 3.9–13.9 ms at n=5, 4.4–159 ms at n=7, and 6.7–620 ms at n=9. Exhaustive enumeration medians rose from roughly 0.5–0.8 ms at n=5 to 65–155 ms at n=9.
- **Multi-start cost:** median relaxation time was 4.89 ms at n=5, 7.97 ms at n=7, and 12.87 ms at n=9 for 20 restarts; median CAN-seed load setup was about 2.86 ms overall. Median Python-traced peak was about 5.2 KiB; this excludes Rust/native allocations and substrate process memory. The terminal probe median was 0.057 ms.
- **Extraction and width:** graph extraction medians ranged from about 0.08–0.33 ms over these cases; min-fill width from about 0.024–0.106 ms. These measurements do not include frame discovery or semantic validation of a partition.

## Interpretation and limits

This is current-source evidence that the exact implementation and objective agree on small synthetic snapshots, that its configured width refusal is active, and that both approximate methods can return suboptimal states; BP can also fail to converge. Multi-start states in this particular benchmark pass a terminal fixed-point check, but local stability does not imply global optimality. The direct exact calls above the integrated width gate are diagnostic only; they must not be read as recommending ungated execution.

The benchmark has only 24 synthetic instances, three state values, sizes through nine nodes, one host, one parameterization, and no natural task graphs. It does not validate frame locality, factorization across a learned hierarchy, exact inference at useful large scale, marginal accuracy, native allocation/process memory, or end-to-end application latency. The sparse-random samples vary in edge count and width by replicate. The timings cannot support a commodity-CPU scale claim.

## Next measurement

Expand seeded ensembles and graph sizes, add marginal-quality checks and process-level memory/allocation measurement, and test larger bounded-width versus high-width families. Then connect the paired protocol to runtime-derived dependency graphs and compare monolithic with boundary-preserving partitioned execution on identical workloads. Keep answer quality, convergence, refusal, stability, and resource use as separate outcomes.
