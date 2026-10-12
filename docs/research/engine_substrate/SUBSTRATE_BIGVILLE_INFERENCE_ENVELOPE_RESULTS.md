# Bigville authored CAN inference envelope

**Run date:** 2026-09-25  
**Runner:** [`can_bigville_inference_envelope.py`](../../../scripts/can_bigville_inference_envelope.py)  
**Raw report:** [`can_bigville_inference_envelope_20260925.json`](../../../evaluation/reports/can_bigville_inference_envelope_20260925.json)

## Scope and protocol

This run moves the exact/BP/native-relaxation comparison from generated graph topologies to the project's authored, parameterized Bigville workload. It constructs each of the 100 deterministic residents in `seeds/bigville_cast100.json` through `worlds.bigville_can_beliefs`, applies the authored shared scenario evidence, and runs over the resulting five-concept Microtheory. Each network has five undirected coupling pairs (ten directed CAN edges) and a min-fill width upper bound of 2. The Microtheory is explicitly set to 3-state mode and the authored native CAN update seeds are loaded for the relaxation path.

For every resident, junction-tree MAP and max-product loopy BP are compared against a separately coded exhaustive enumerator over all 3^5 = 243 states and a separately coded energy function. Native multi-start relaxation uses 20 deterministic, resident-specific initializations. It mutates the same resident graph only after exact/BP measurements; the extracted unary fields, coupling values, and edge set are checked against their pre-relaxation values. A zero-progress native settle is used as the terminal fixed-point probe. The run records component timings and Python `tracemalloc` peak during relaxation; that allocation figure omits Rust allocations and process RSS.

The cast is authored deterministic simulation data, not an independently sampled real population or external natural-world dataset. Scenario response quality is not independently labeled by this benchmark; energy optimality is only an optimization criterion.

## Results

- **Coverage and exactness:** all 100 resident networks were extracted as 5 nodes/5 undirected pairs with width upper bound 2. Exact junction-tree MAP matched independent exhaustive MAP on 100/100 cases. Native energy matched the independent objective on all relaxation states.
- **BP:** max-product BP converged in 35/100 cases and returned a MAP state in 37/100. Median energy gap was 1.602; some nonconverged runs nevertheless returned an optimum, so convergence status and answer quality are separate outcomes. The low width bound alone did not ensure BP convergence.
- **Native multi-start relaxation:** all 100 calls returned 20 candidates, passed the terminal fixed-point probe, and preserved the original unary/pairwise model. The chosen state was globally optimal in 16/100 cases; median energy gap was 0.274. This method chooses by native frustration, while this report scores its output by the exact energy objective. Stability is not a global-optimality guarantee.
- **Median component cost:** graph extraction 0.086 ms; min-fill width 0.024 ms; junction-tree MAP 0.111 ms; exhaustive oracle 0.558 ms; BP 35.0 ms; native seed loading 2.82 ms; 20-start relaxation 5.19 ms; terminal probe 0.046 ms. Median Python-traced peak during the relaxation call was 4,958 bytes. These are one-run, in-process medians; BP cost includes the solver's bounded iterations and no process/native memory measure is included.

## Interpretation

This is useful evidence that the exact inference path is cheap and correct on one current authored five-node workload family, while two available approximate paths can settle or converge without matching the global energy optimum. It also shows that low treewidth makes exact junction-tree inference feasible here, but does not imply that loopy BP converges. The native multi-start run is stable across this cast but frequently remains above the MAP energy.

The workload uses the same five-node topology for all residents, so this does not test topology variation, frame discovery, cross-frame factorization, or useful-scale graph growth. The cast is deterministic project simulation data. No claim follows about natural task distributions, decision quality, general capability, CPU scaling, or production latency. Python allocation tracing does not estimate native memory.

## Next measurement

Use runtime-derived CAN snapshots whose topology and fields arise from authored rule execution, compare inference before and after evidence/update ticks, and retain an independent energy oracle. Then test broader topology/size families, record process-level memory and native allocation, and evaluate marginal calibration separately from MAP energy. Preserve explicit width refusal and report solver answer quality independently from convergence and fixed-point status.
