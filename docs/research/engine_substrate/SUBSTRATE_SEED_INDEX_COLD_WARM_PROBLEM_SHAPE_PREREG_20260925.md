# Seed-index cold/warm ProblemShape parity probe preregistration

Date: 2026-09-25  
Status: locked before execution; exploratory workload-level reproducibility check

## Question

Does the repaired seed-index cache produce the same order-sensitive ProblemShape task outcomes and measured engine work when each fresh worker loads an empty cache versus a previously built cache?

## Locked design

- Use the immutable baseline seed snapshot from the V1.7 seed-corpus transformation, derived from the currently locked 833-file corpus. Verify both the V1.7 ordered manifest-hash digest and the transformer's canonical sorted-path digest; these use different row orderings and are recorded separately in the lock.
- Run the current `substrate_problem_shape_population_scale.worker` at N=32 for `recognition` and `recurrent_residual`, in four fresh processes: cold and warm cache for each mix.
- Cold means remove the snapshot's cache immediately before the worker. Warm means build the cache first, verify its bytes, then launch the worker. For each case, verify the cache bytes do not change during the worker.
- Hold Python hash seed at 0. Record source/build/corpus hashes, complete seed-load and active-rule order, ProblemShape rule positions, task status/mint outcomes, fixed-point outcomes, and operation counters.
- Compare cold versus warm projections exactly within each mix, excluding elapsed/CPU time, process ID, and RSS. Timing is descriptive only and is not a pass criterion.
- Require each worker's own semantic and fixed-point checks to pass. Any mismatch is a failed gate and must be retained with both raw worker records.

## Claim boundary

This tests loader-state parity on two authored N=32 workloads and one frozen corpus. It does not establish broad domain parity, natural-task locality, performance improvement, or tractability of induction/minting. No code or seed edits are permitted during the run.

## Frozen inputs

Hashes are recorded in [`lock JSON`](../../../evaluation/substrate_capability/seed_index_cold_warm_problem_shape_lock_20260925.json). The source lock includes the corpus transformation and digest helpers, loader, task worker/helpers, domain modules, native extension and build manifest. Both seed-corpus digests must match before snapshot creation and the source-manifest digest must still match after all four workers.
