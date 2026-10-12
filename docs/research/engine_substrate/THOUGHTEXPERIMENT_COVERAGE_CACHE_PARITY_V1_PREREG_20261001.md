# Thoughtexperiment coverage-index cache parity v1 preregistration

## Question

Does supplying one precomputed coverage-keyword set to `synthesize_gaps` preserve the exact result of the default recomputation path for a fixed graph and fixed harvested shape library? Is the fixed graph unchanged by either call with `record=False`?

## Procedure

- Run three fresh full-seed workers.
- In each worker, select the three candidates from the source-locked discovery scan: `diffusion_model_vision`, `variational_autoencoder`, and `vision_language_model`.
- Resolve the default harvested shape library and coverage-keyword index once. For each postulate, run `synthesize_gaps(max_order=1, prune=True, record=False, shapes=shapes)` and repeat with the same explicit shape list and `covered_keywords=covered`.
- Compare the complete returned gap lists, not only keys/counts. Canonicalize and hash the semantic graph before and after all six calls in each worker.
- Record per-call elapsed time descriptively, worker PIDs, boot outcomes, and before/after source and top-level seed fingerprints.

## Gates

Pass only if three distinct workers boot the same held postulates; all three complete gap-list pairs are exactly equal per worker; the complete canonical graph digest is unchanged; and all source fingerprints are stable. Timing is descriptive and does not establish an asymptotic speedup. This checks batch-index reuse only; it does not test the freshness invariant when the graph or implementation surface changes.

The experiment is a direct substrate-behavior comparison, not a unit-test suite. It makes no capability novelty or utility claim. See the [results](THOUGHTEXPERIMENT_COVERAGE_CACHE_PARITY_V1_RESULTS_20261001.md), [runner](../../../evaluation/substrate_capability/thoughtexperiment_coverage_cache_parity_v1.py), and [raw capture](../../../evaluation/reports/thoughtexperiment_coverage_cache_parity_v1_raw_20261001.json).
