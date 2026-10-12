# Active thoughtexperiment rehearsal memory v1 — preregistration

**Date:** 2026-10-01  
**Question:** What additional process RSS/PSS is resident while the substrate runs an actual corrective thoughtexperiment at 100k and 200k unrelated graph nodes, and how does it differ between scoped native deep-copy and scoped shared-graph-page branches?

## Design

Use the established source-locked positive correction fixture (`sd_mint_quantum` with the known `dedup_identity_fix`) at 100,000 and 200,000 unrelated nodes. For each size and each backend (`native_full_copy_scoped`, `native_shared_graph_pages_scoped`), run three fresh processes with no warmup. After fixture construction, sample baseline Linux `smaps_rollup`, then run `imagine_and_check_convergence` with horizon 3, two imagination steps, and the existing three-observation one-hop focus. A background sampler records maximum RSS/PSS and private/shared clean/dirty pages while this call executes; operation duration is recorded but is secondary because the sampler adds instrumentation overhead.

The worker then verifies positive convergence, unchanged rewrite rules, unchanged noise-graph attributes, and unchanged source observation values. A pre-run lock captures the runner, Python task helper, relevant substrate/engine sources, native extension and build record. Backend order alternates within each size.

## Gates

- Six fresh-process cells with stable source/native provenance and full raw samples.
- Both backends converge on the same positive correction with matching residual/output signatures at each size.
- Every worker preserves the rewrite-rule store, noise graph, and source observation values.
- Report baseline and peak-current RSS/PSS plus peak-minus-baseline deltas, including negative or near-zero deltas.

## Interpretation limits

`smaps_rollup` is sampled every 10 ms and may miss brief peaks. The sampler perturbs CPU scheduling; operation timings are descriptive only. This is one authored task, one host, and one synthetic linked noise graph. It does not measure kernel peak RSS, high-concurrency throughput, or natural-task memory distribution. It measures a real predictive rehearsal, not broad inference or a production action loop.
