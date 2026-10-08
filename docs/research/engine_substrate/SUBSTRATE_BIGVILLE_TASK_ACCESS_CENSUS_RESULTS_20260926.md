# Bigville task-derived runtime access census results

**Run:** 2026-09-26. **Grade:** diagnostic workload result; not confirmatory. The Bigville cast and CAN path have prior use, and the trigger was selected after an initial no-op at resident 0. The corrected capture uses resident 40, which makes the native update rule progress.

## Result

The live graph contained 500 owned Concept nodes in 100 five-node Microtheory frames, with 1,000 directed causal edges and no cross-frame causal edges. Exact brute-force elimination gives treewidth 2 for each five-node component. On the resident-40 evidence update, full closure and caller-notified one-frame settlement both made five progress steps and produced identical full graph digests; an independently recomputed CAN oracle found zero residuals. The instrumented and uninstrumented one-frame runs also had identical full graph digests.

The one-frame arm enumerated 30 candidate pairs and 1,831 Term evaluations, compared with 1,025 pairs and 46,147 Terms under monolithic round-robin closure. That is 97.1% fewer candidate pairs and 96.0% fewer Term evaluations for this disconnected workload. One fresh-process timing per arm measured 3.81 ms for full settlement and 0.199 ms for uninstrumented one-frame settlement. Including graph plus partition setup, observed setup-plus-one-settlement was 56.81 ms full and 55.16 ms event. The apparent 1.65 ms difference is smaller than the 1.96 ms setup-time difference between those arms; with one worker per arm it does not resolve an end-to-end cost benefit. These timings are descriptive only: one update per arm is too little to estimate variance or amortisation.

The tracing arm observed 601 access events (596 reads and five writes), all attributed to frame 40; no event was dropped and no observed read/write edge crossed a frame. However, the rule's static access summary still has `reads_any=true`. The access trace is partial, so the observations support only this exercised execution. They do not prove that future firings or other effects have no cross-frame dependencies.

Construction plus live partition derivation took 52.7–55.0 ms per worker; the separately timed map materialization was about 0.20 ms. This setup is much larger than a single settlement call. The three setup values vary by more than 2 ms and are not a paired estimate. Peak process RSS was about 311 MiB and includes the Python/native process floor. The study does not measure repeated updates, topology changes, dynamic boundary maintenance, or an independently selected task distribution.

## Gate checks

All 12 runner gates and all 12 independent analyzer gates passed. The raw runner record retains full node/frame membership, the 1,000 directed dependency edges, static read/write declarations, concrete traced events, per-arm timings and counters, graph digests, and environment/build provenance.

This is a positive result for caller-supplied owner scheduling on one disconnected authored workload. It strengthens evidence that sparse task partitions can reduce repeated closure work when the owner map is already known. It does not pass Phase C2/C3: the partition is fixed and derived from the existing Bigville builder, the trace carries an access wildcard, and no boundary-aware native scheduler or construction-inclusive speed benefit is shown.

## Artifacts

- [Preregistration](SUBSTRATE_BIGVILLE_TASK_ACCESS_CENSUS_PREREG_20260926.md)
- [Runner](../../../scripts/substrate_bigville_task_access_census_v1.py)
- [Independent analyzer](../../../scripts/analyze_substrate_bigville_task_access_census_v1.py)
- [Input lock](../../../evaluation/substrate_capability/bigville_task_access_census_lock_20260926.json)
- [Raw report](../../../evaluation/reports/substrate_bigville_task_access_census_v1_20260926.json)
- [Analysis](../../../evaluation/reports/substrate_bigville_task_access_census_v1_analysis_20260926.json)
