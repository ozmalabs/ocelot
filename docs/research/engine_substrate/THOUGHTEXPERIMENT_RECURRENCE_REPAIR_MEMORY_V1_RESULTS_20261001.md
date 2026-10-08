# Thoughtexperiment recurrence repair memory v1 — results

**Result:** 6/6 preregistered gates pass across 12 fresh processes (three per size/backend cell). Each process repaired the injected single-guard defect in an isolated branch, emitted exactly one offer, reached a zero-progress fixed point, and preserved the primary graph, rules, and revision. Full-copy and shared-page backends had matching closure outcomes.

## Sampled memory during repair rehearsal

Median peak increase over each process baseline; MiB (Linux `smaps_rollup`, sampled every 10 ms):

| Graph nodes | Branch backend | ΔPSS | ΔRSS | ΔPrivate Dirty | Median rehearsal time |
|---:|---|---:|---:|---:|---:|
| 100,000 | native eager full copy | 32.11 | 32.11 | 31.30 | 56.2 ms |
| 100,000 | native shared graph pages | 2.68 | 2.68 | 1.87 | 5.0 ms |
| 200,000 | native eager full copy | 62.94 | 62.94 | 62.13 | 108.2 ms |
| 200,000 | native shared graph pages | 4.05 | 4.05 | 3.23 | 6.1 ms |

At 100k nodes, sampled peak ΔPSS was 32.11 MiB for full copy and 2.68 MiB for shared pages; at 200k it was 62.94 MiB and 4.05 MiB. In this recurrence task, the shared-page branch used about 12× and 15.5× less incremental PSS, respectively. The measured interval includes branch creation, rule replacement, five bounded native closure sweeps, oracle checks, and branch release. Times are instrumented and descriptive only.

The sampler recorded only 3–5 observations per run because the operations completed quickly; its 10 ms cadence can miss transient peaks. The graph is synthetic linked noise plus a single authored recurrence candidate on one Linux host. This establishes a memory advantage for this task shape, not a general throughput claim, natural-task prevalence, concurrent serving behavior, or autonomous repair discovery.

## Artifacts

- [Preregistration](THOUGHTEXPERIMENT_RECURRENCE_REPAIR_MEMORY_V1_PREREG_20261001.md)
- [Pre-run lock](../../../evaluation/substrate_capability/thoughtexperiment_recurrence_repair_memory_v1_lock_20261001.json)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_recurrence_repair_memory_v1.py)
- [Raw capture](../../../evaluation/reports/thoughtexperiment_recurrence_repair_memory_v1_raw_20261001.json)
