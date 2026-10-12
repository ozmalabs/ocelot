# Candidate-cohort streaming probe v1

## Question

Does registering each generated term immediately reduce complete-pool synthesis cost or temporary Python allocation while preserving the eager generator's candidate order and outputs?

## Arms and workloads

The eager arm preserves the existing implementation: construct every term at one size, then register candidates in order. The streaming arm registers each term as it is generated. Both use the same bottom-up grammar, size/operator/child order, examples, probe environments, observational-equivalence key, and candidate limit. Streaming is opt-in; this probe does not change the default.

Use the same three authored task adapters as the generated-pool scale ladder: triangular, square, and Euler. Cross four frozen size ceilings per task with probe-prefix sizes 0/1/3/6/10; collect two paired repetitions per cell (120 paired cells). Randomize eager/streaming execution order within each worker and randomize schedule order. Use an eight-second synthesis timeout, solution limit 10,000, disabled saturation, fixed operators/constants, and held-out target-support measurement after each arm.

## Measures and gates

Capture both arms' halt reason, pool size, terms explored, distinct-signature count, ordered behavior signatures, held-out target support, wall/CPU time, and `tracemalloc` peak during synthesis. The primary semantic gate is exact equality of halt reason, pool size, explored/distinct counts, ordered signatures, and target-support count for each pair. Report paired timing and Python allocation ratios by task/size/probe; do not claim Rust/native allocation coverage because `tracemalloc` observes Python allocations only. Keep timeouts and mismatches as failures.

This is a bounded synthetic implementation comparison with two repeats, not a complexity theorem, natural-task prevalence estimate, or memory profile of native allocations. It specifically tests whether eliminating same-size cohort materialization changes cost without changing the bounded pool.

## Reproduction

Create `evaluation/substrate_capability/substrate_generator_streaming_probe_v1_20261001_lock.json` with `python3 scripts/substrate_generator_streaming_probe_v1.py --lock`, run `python3 scripts/substrate_generator_streaming_probe_v1.py`, then run `python3 scripts/analyze_substrate_generator_streaming_probe_v1.py`.
