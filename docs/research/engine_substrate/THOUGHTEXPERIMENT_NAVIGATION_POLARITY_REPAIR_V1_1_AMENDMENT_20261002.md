# Navigation polarity repair v1.1 amendment — NodeID metadata serialization

The initial v1 lock was created successfully, but its first worker failed before task scoring. The runner attempted `int(axis)` on a PyO3 `NodeID`, which does not support direct integer conversion. No v1 raw capture was written; the v1 lock and runner are retained as the failed attempt.

V1.1 changes only diagnostic metadata serialization from integer conversion to string conversion. The task, fault, candidate generation, residual cue, held-out states, native rule execution, and gates are unchanged. A new runner, analyzer, lock, and raw-output path are used; v1.1 captures cannot overwrite v1 artifacts. The failed worker is not included in v1.1 results.

- [Original preregistration](THOUGHTEXPERIMENT_NAVIGATION_POLARITY_REPAIR_V1_PREREG_20261002.md)
- [Failed v1 runner](../../../evaluation/substrate_capability/thoughtexperiment_navigation_polarity_repair_v1.py)
- [Failed v1 lock](../../../evaluation/substrate_capability/thoughtexperiment_navigation_polarity_repair_v1_lock_20261002.json)
