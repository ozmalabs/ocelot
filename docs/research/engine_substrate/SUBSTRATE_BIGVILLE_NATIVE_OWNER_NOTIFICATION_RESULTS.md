# Bigville native owner-notification replay results

## Result

The locked three-topology, three-replicate replay passed all seven gates across 27 fresh-process workers. At every checkpoint, full and native-event settlement reached an independently measured zero residual; their projected state and field values were exactly equal. Native scoped settlement reported complete in all event checkpoints, with neither pending deferred effects nor progress-cap exits. The omission sensitivity arm produced positive residual after both link insertion (1–3) and the authored-evidence update (6–8), then later returned to zero when subsequent mutations seeded settlement. This supports the owner-notification path on this authored workload.

The runtime partitioner reconstructed 100 components of five Concepts in every worker. The event arm used the native affected-Microtheory IDs to enqueue runtime frames, while the known host mutation endpoints still supplied initial seeds. It did not discover or rebuild the partition.

## Work and cost

Across the nine topology/replicate pairs, event settlement used 354–454 queue turns, compared with 1,100–1,300 turns for full round-robin closure summed across the same seven checkpoints. By topology, event turns were 454 vs 1,200 for ring, 354 vs 1,100 for star, and 401–417 vs 1,200–1,300 for seeded random links. Median summed settlement wall time was 29.0 ms event vs 43.4 ms full for ring, 25.2 ms vs 33.8 ms for star, and 24.5 ms vs 42.9 ms for seeded random links. These are small-run harness timings, not a scaling law; startup, mutation work, Python orchestration, and native calls contribute.

The omission arm's residual at the link-insertion checkpoint confirms that its harness policy suppresses more than the evidence notification. The v1.1 amendment records this before the locked run. The result therefore treats that arm only as a broad missing-notification sensitivity control and does not attribute the evidence-stage residual solely to the evidence seed.

## Reproduction and limits

- Protocol: [`SUBSTRATE_BIGVILLE_NATIVE_OWNER_NOTIFICATION_PREREG_20260925.md`](SUBSTRATE_BIGVILLE_NATIVE_OWNER_NOTIFICATION_PREREG_20260925.md)
- Amendment: [`SUBSTRATE_BIGVILLE_NATIVE_OWNER_NOTIFICATION_V1_1_AMENDMENT_20260925.md`](SUBSTRATE_BIGVILLE_NATIVE_OWNER_NOTIFICATION_V1_1_AMENDMENT_20260925.md)
- Runner: [`substrate_bigville_native_owner_notification.py`](../../../scripts/substrate_bigville_native_owner_notification.py)
- Lock: [`bigville_native_owner_notification_lock_20260925.json`](../../../evaluation/substrate_capability/bigville_native_owner_notification_lock_20260925.json)
- Raw report: [`substrate_bigville_native_owner_notification_20260925.json`](../../../evaluation/reports/substrate_bigville_native_owner_notification_20260925.json)

This is an authored CAN simulation with injected cross-resident links. Frame construction is still external to the native substrate; host code knows the endpoint frames for initial mutation seeds. The experiment does not establish natural frame locality, arbitrary rule/effect coverage, automatic partition maintenance, deferred-effect processing, or general scheduler correctness. Native per-Microtheory notification is not yet a dependency-component scheduler. No general complexity or commodity-scale claim follows from this run.
