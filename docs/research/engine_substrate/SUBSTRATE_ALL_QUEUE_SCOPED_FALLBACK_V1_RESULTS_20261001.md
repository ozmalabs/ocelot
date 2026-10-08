# Unified five-family scoped and fallback queue work v1 results

Date: 2026-10-01; current-source result after amendment v1.1.

## Outcome

The repaired scoped path now matches the default full closure on the preregistered workload. A 27-worker source/native-locked factorial across `R={1,8,32}` writers, `M={1,4,16}` join multiplicities, and three fresh processes per cell passes all 300 semantic and work-accounting checks. Full closure and scoped-plus-global-fallback produce byte-for-byte equal graph dictionaries in every cell. Scoped-only reports pending deferred work and does not claim settlement.

All five queue families reconcile with independent scale-audit counters. Scoped execution enqueues every expected item for each binding; fallback drains the pending items without re-enqueueing. RulePatch remains one item per writer through deduplication, while rule edits, framebuffer samples, TrackIdentity, and NetCollapse scale as `R×M`. Every phase's operation-work trace has zero dropped rows and exact queue-family reconciliation.

The first pre-fix capture exposed an important bug: scoped non-batch execution stopped after the first progressing binding, while the live scheduler drained all distinct bindings. That caused queue loss and different NetCollapse results at `M>1`. The source fix now snapshots the scoped binding set, deduplicates canonical bindings, applies all of them in order, and avoids reusing graph-dependent evaluation cache entries during the mutation fold. The failure and evidence-preservation limitation are recorded in [amendment v1.1](SUBSTRATE_ALL_QUEUE_SCOPED_FALLBACK_V1_1_AMENDMENT_20261001.md).

## Reproducibility and artifacts

The 27 workers have stable source/native fingerprints before and after execution. The source lock includes the rebuilt native extension SHA-256 `fdddfdfa9c9b56135b93360fa12f1d5616648eefe82b4eb9e384ead1fe113da6`. The analyzer passes `300/300` checks. Preserved v1.1 artifacts:

- [Preregistration](SUBSTRATE_ALL_QUEUE_SCOPED_FALLBACK_V1_PREREG_20261001.md)
- [Amendment](SUBSTRATE_ALL_QUEUE_SCOPED_FALLBACK_V1_1_AMENDMENT_20261001.md)
- [Engine change](../../../runners/dsl/src/rewrite.rs)
- [Runner](../../../scripts/substrate_all_queue_scoped_fallback_v1.py)
- [Analyzer](../../../scripts/analyze_substrate_all_queue_scoped_fallback_v1.py)
- [Source/native lock](../../../evaluation/substrate_capability/all_queue_scoped_fallback_v1_1_lock_20261001.json)
- [Raw workers](../../../evaluation/reports/all_queue_scoped_fallback_v1_1_workers_20261001.json)
- [Analysis](../../../evaluation/reports/all_queue_scoped_fallback_v1_1_analysis_20261001.json)

## Limits and next gate

This shows exact scoped/fallback parity for one authored positive-join pattern and one direct-owner scope shape; it is not a general scope-completeness proof or natural-task result. The per-rule binding fold now follows the live scheduler for this path, but rules whose writes affect later bindings, cross-frame matches, projection deduplication, deletion behavior, and mixed scope ownership need dedicated parity coverage. Next test distinct per-binding mutation targets and interactions between multiple active rules, then run existing scope consumers against full-closure oracles before using this path for frame partitioning.
