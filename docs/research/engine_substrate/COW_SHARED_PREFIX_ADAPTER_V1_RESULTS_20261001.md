# Shared-prefix adapter compatibility probe v1 results

The source-locked synthetic adapter completed **30 measured fresh workers** across three background graph sizes, two snapshot paths, and five repetitions per cell. The public-default snapshot and eager-copy control match exactly on all semantic receipt fields. Every worker passes all seven gates: stale revision-token rejection before branch creation, sibling isolation, sibling survival after cancellation, clean later forks, reuse after cancellation, and zero active request/block handles after cancellation.

| Background nodes | Backend | Publish (ms) | Fork two requests (ms) | PSS delta with two requests live (MiB) | PSS delta after all requests cancelled (MiB) |
|---:|---|---:|---:|---:|---:|
| 0 | public default | 0.033 | 0.073 | 0.129 | 0.168 |
| 0 | eager copy | 0.059 | 0.097 | 0.141 | 0.180 |
| 1,000 | public default | 0.041 | 0.063 | 0.184 | 0.227 |
| 1,000 | eager copy | 0.268 | 0.513 | 0.457 | 0.492 |
| 10,000 | public default | 0.085 | 0.105 | 0.250 | 0.293 |
| 10,000 | eager copy | 2.711 | 5.563 | 3.059 | 1.738 |

Timing is descriptive for this one-host, small synthetic consumer. The 10k fork and PSS differences are consistent with snapshot sharing avoiding repeated full-graph copies, but this probe is not a serving benchmark and is not used to claim a universal speedup. After all requests are cancelled, the adapter's live request and continuation-block accounting is zero in every worker. Process PSS does not return to baseline consistently; allocator retention and the process-wide nature of `smaps_rollup` make it unsuitable as an object-level reclamation proof.

The result establishes a shared-prefix-shaped consumer can use the public snapshot/fork lifecycle without knowing the backend, while preserving the published prefix across divergent continuations, cancellation, and later forks. It does **not** establish compatibility with vLLM, model KV-block ownership/layout, concurrent cancellation, scheduler behavior, token throughput, serving memory efficiency, or real-time guarantees. The adapter is sequential and synthetic; those remain separate gates.

## Reproduction artifacts

- [Preregistration](COW_SHARED_PREFIX_ADAPTER_V1_PREREG_20261001.md)
- [Runner](../../../evaluation/substrate_capability/cow_shared_prefix_adapter_v1.py)
- [Independent analyzer](../../../scripts/analyze_cow_shared_prefix_adapter_v1.py)
- [Raw source-locked capture](../../../evaluation/reports/cow_shared_prefix_adapter_v1.json)
- [Analysis](../../../evaluation/reports/cow_shared_prefix_adapter_v1_analysis.json)
