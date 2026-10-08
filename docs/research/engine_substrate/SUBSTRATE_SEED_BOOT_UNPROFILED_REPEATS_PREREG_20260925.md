# Unprofiled seed boot repeat preregistration

Date: 2026-09-25  
Status: locked six-process startup envelope

## Question

What is the repeat-to-repeat cold/warm `WorldAdapter` plus full `load_all_seeds` wall/CPU startup envelope on the frozen 833-manifest corpus, without cProfile instrumentation?

## Design

- Six distinct processes load the immutable V1.7 baseline snapshot in fixed order: cold, warm, warm, cold, cold, warm (three observations per cache state).
- A cold worker starts with its seed-index cache removed; a warm worker starts after the cache is built and hashed. Warm workers must leave cache bytes unchanged.
- Each worker starts wall/CPU timers before `WorldAdapter(seeds=())` construction and stops after `load_all_seeds`. Imports are outside the measured interval. No domain task runs in this startup-only probe.
- Record full graph/grammar/rule/access/order/load-report fingerprints. Require all six boot states to match and every manifest to match the corpus lock.
- Report individual points and medians; timing is descriptive for this host and one corpus. No cold/warm speedup claim is allowed from this sample.

## Claim boundary

This is a six-process startup microbenchmark, not a CPU scaling curve, natural-workload benchmark, or evidence that boot-time self-model work can be removed. Further scaling requires multiple corpus sizes and hardware/resource attribution.
