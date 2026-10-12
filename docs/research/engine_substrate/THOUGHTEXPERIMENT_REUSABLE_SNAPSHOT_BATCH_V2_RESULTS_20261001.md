# Thoughtexperiment reusable snapshot batch v2 results

## Gates

The expanded live-harness panel contains six backend × size comparisons, 30 measured batch trials, 30 matched standalone trials, and 10 exact cross-backend block comparisons. At each size, eager full-copy, direct shared-graph-page, and reusable-snapshot rows pass the positive/negative candidate controls, exact candidate order, nested prediction/residual parity, and primary graph/rule revision checks. The existing runner aborted on any semantic disagreement; an independent analyzer rechecks all six comparisons, each of the five measured blocks, every positive/negative control, and source/binary/engine fingerprints.

## End-to-end batch cost

Times are medians in milliseconds, five measured randomized blocks after one warmup. `Batch` computes the baseline once and evaluates six candidate branches; `standalone` recomputes the baseline per candidate.

| Graph scale | Backend | Batch | Standalone | Standalone / batch |
|---:|---|---:|---:|---:|
| +10k | eager full copy | 508 | 797 | 1.57× |
| +10k | shared graph pages | 422 | 640 | 1.52× |
| +10k | reusable snapshot | 436 | 624 | 1.43× |
| +50k | eager full copy | 768 | 1,498 | 1.95× |
| +50k | shared graph pages | 420 | 614 | 1.46× |
| +50k | reusable snapshot | 423 | 640 | 1.51× |

At +50k the two shared-page paths are effectively tied in aggregate; direct pages win 3/5 paired batch blocks and 4/5 standalone blocks. At +10k direct pages win 3/5 in both modes. The reusable API therefore has no demonstrated throughput advantage over direct shared-page forks. Relative to eager full copies, both shared-page paths substantially lower batch cost at +50k in this fixture. Reusable snapshot capture itself costs about 0.28 ms median at both sizes.

The phase profile explains where the comparison lands. At +50k, the median per-candidate outer branch setup is about 18.9 ms eager, 7.0 ms direct shared pages, and 6.8 ms reusable; prediction remains roughly 83/44/45 ms respectively. At +10k, setup is about 9.8/6.6/6.7 ms and prediction about 52/44/44 ms. These components include harness operations around branch creation and are not a pure native fork microbenchmark.

## Residual receipt and remaining measurement gap

For every candidate at both sizes and in all three backends, the returned `conclusions` and `derived_only` deltas contain **zero changed nodes and zero changed edges**. Positive/negative prediction behavior still passes: `dedup_identity_fix` converges and the guarded negative candidate does not. Thus this authored Thoughtexperiment case measures candidate rule variation and prediction over a large shared base, but its graph residual receipt does not exercise nonempty branch writeback. These exact changed-object counts cannot stand in for all mutation attempts, cloned pages, rule-store edits, or touched memory locations.

The next full-harness gate should add a productive candidate fixture with at least one deterministic graph fact derived in the branch and returned in its residual. Require a nonempty residual, eager/direct/reusable exact parity, primary isolation, and later-fork isolation; then measure the cost of sparse residual extraction and any explicit adoption into the primary as separate operations. Do not infer writeback performance from this zero-residual panel.

## Scope

The fixture is one authored correction family, one host, and five measured blocks; timing order is randomized within the process, so blocks share allocator and thermal history. It measures six sequential branches, not concurrent request serving, cancellation, bounded reclamation, or model KV-block reuse. A vLLM-style shared-prefix adapter remains a separate compatibility target with its own ownership and lifecycle contract.

## Reproduction artifacts

- [Preregistration](THOUGHTEXPERIMENT_REUSABLE_SNAPSHOT_BATCH_V2_PREREG_20261001.md)
- [Existing fixed-revision benchmark runner and command](../../../evaluation/substrate_capability/thoughtexperiment_fixed_revision_six_candidate_batch_v1.py)
- [Independent analyzer](../../../scripts/analyze_thoughtexperiment_reusable_snapshot_batch_v2.py)
- [Compressed source-captured raw panel](../../../evaluation/reports/thoughtexperiment_reusable_snapshot_batch_v2.json.gz)
- [Analysis](../../../evaluation/reports/thoughtexperiment_reusable_snapshot_batch_v2_analysis.json)
