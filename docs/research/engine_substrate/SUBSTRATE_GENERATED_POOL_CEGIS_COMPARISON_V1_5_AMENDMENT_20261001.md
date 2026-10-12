# Generated-pool active query versus iterative resynthesis v1.5 amendment

The v1.4 five-block replay randomized execution order but reused the same seeded-random query order in each replicate. It therefore measures timing repeatability for one random policy draw, not variation across random query orders.

For v1.5, set the random-pool seed to `20261001 + 100 * task_index + replicate`, yielding five predeclared distinct random orders per task. Entropy and fixed-first remain deterministic; all workload, size, timeout, source, timing, and correctness gates are unchanged. Preserve v1.4 raw results. Report random-policy outcomes and cost by replicate, not only pooled medians.
