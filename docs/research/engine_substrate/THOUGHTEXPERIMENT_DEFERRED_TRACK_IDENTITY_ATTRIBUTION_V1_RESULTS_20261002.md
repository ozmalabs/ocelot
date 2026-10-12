# Thoughtexperiment deferred TrackIdentity attribution v1 results

All gates pass across three fresh source-locked workers. Ordinary, attributed, and exact-snapshot runs agree on progress-budget status, progress count, and passes. The observer reports one `deferred=true` event per worker, attributed to `trans_frame_identity_assignment`; it covers the five previous/current percept nodes changed by the exact oracle. The independent `trace_direct_control` appears only as `deferred=false`. Every event target is included in the aggregate report, all exact changed nodes/edges are covered, and there are no dropped events.

The 3-step progress budget deliberately allows one between-pass queue drain and then stops. The task queues TrackIdentity repeatedly, so all runs end at `progress_budget_reached`; this is not evidence of fixed-point termination or a complete task cycle. The event shows that producer identity can survive one deferred queue/drain path. It does not identify binding identity or attribute keys, and it does not establish causal uniqueness when multiple rules can write the same facts.

After the locked dev-extension capture, the sanctioned release build installed the same source change into the workspace extension. Its provenance check reports no stale sources, and the same capped fixture reproduced the deferred event and exact changed-node coverage. The reported v1 worker capture and fingerprints remain those of the isolated extension recorded in the source lock.

Other deferred families—rule edits, rule patches, framebuffer samples, and net collapses—still lack producer attribution. Duplicate patch requests would need multi-origin provenance rather than an arbitrary first-writer label. Target-blind diagnosis remains unmeasured.

## Artifacts

- [Preregistration](THOUGHTEXPERIMENT_DEFERRED_TRACK_IDENTITY_ATTRIBUTION_V1_PREREG_20261002.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_deferred_track_identity_attribution_v1.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_thoughtexperiment_deferred_track_identity_attribution_v1.py)
- [Source lock](../../../evaluation/substrate_capability/thoughtexperiment_deferred_track_identity_attribution_v1_lock_20261002.json)
- [Raw capture](../../../evaluation/reports/thoughtexperiment_deferred_track_identity_attribution_v1_20261002.json)
- [Analysis](../../../evaluation/reports/thoughtexperiment_deferred_track_identity_attribution_v1_analysis_20261002.json)
