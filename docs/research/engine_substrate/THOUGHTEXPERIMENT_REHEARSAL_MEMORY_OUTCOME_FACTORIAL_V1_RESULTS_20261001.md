# Thoughtexperiment rehearsal memory outcome factorial v1 — results

**Result:** 6/6 preregistered gates pass across 24 fresh processes.

Both arms run the established self-correction operation on matched high-node-count graphs. The positive candidate converges; the first nonmatching candidate does not. Memory sampling is current PSS/RSS every 10 ms during branch prediction and residual readout; timings remain instrumented and descriptive.

| Nodes | Candidate | Backend | Baseline PSS | Peak PSS | Peak ΔPSS | Peak ΔPrivate Dirty | Converges |
|---:|---|---|---:|---:|---:|---:|---:|
| 100,000 | `dedup_identity_fix` | `native_full_copy_scoped` | 69.3 MiB | 167.6 MiB | 98.33 MiB | 97.27 MiB | 3/3 |
| 100,000 | `dedup_identity_fix` | `native_shared_graph_pages_scoped` | 69.3 MiB | 79.5 MiB | 10.16 MiB | 9.10 MiB | 3/3 |
| 100,000 | `first nonmatching default` | `native_full_copy_scoped` | 69.3 MiB | 167.6 MiB | 98.29 MiB | 97.23 MiB | 0/3 |
| 100,000 | `first nonmatching default` | `native_shared_graph_pages_scoped` | 69.3 MiB | 78.1 MiB | 8.74 MiB | 7.68 MiB | 0/3 |
| 200,000 | `dedup_identity_fix` | `native_full_copy_scoped` | 101.1 MiB | 291.9 MiB | 190.75 MiB | 189.69 MiB | 3/3 |
| 200,000 | `dedup_identity_fix` | `native_shared_graph_pages_scoped` | 100.1 MiB | 114.6 MiB | 14.51 MiB | 13.45 MiB | 3/3 |
| 200,000 | `first nonmatching default` | `native_full_copy_scoped` | 100.1 MiB | 290.9 MiB | 190.76 MiB | 189.70 MiB | 0/3 |
| 200,000 | `first nonmatching default` | `native_shared_graph_pages_scoped` | 100.1 MiB | 113.9 MiB | 13.80 MiB | 12.74 MiB | 0/3 |

This is a controlled comparison within one synthetic shape-decoding correction family. The negative arm is one candidate, not a distribution of failed experiments. The sampler can miss brief peaks; no timing claim is made. See the preceding positive-only [active rehearsal memory panel](THOUGHTEXPERIMENT_ACTIVE_REHEARSAL_MEMORY_V1_RESULTS_20261001.md) for the validated input/rule preservation amendment and retained initial diagnostic.

## Artifacts

- [Preregistration](THOUGHTEXPERIMENT_REHEARSAL_MEMORY_OUTCOME_FACTORIAL_V1_PREREG_20261001.md)
- [Pre-run lock](../../../evaluation/substrate_capability/thoughtexperiment_rehearsal_memory_outcome_factorial_v1_lock_20261001.json)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_rehearsal_memory_outcome_factorial_v1.py)
- [Raw capture](../../../evaluation/reports/thoughtexperiment_rehearsal_memory_outcome_factorial_v1_raw_20261001.json)
