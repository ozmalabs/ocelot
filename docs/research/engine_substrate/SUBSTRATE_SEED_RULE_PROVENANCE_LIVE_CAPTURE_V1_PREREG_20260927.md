# Seed-to-native-rule provenance capture v1 preregistration (2026-09-27)

## Question

Which loaded seed installed each native rule UID exercised by a successful current-source live describe-scene run?

## Method

On a fresh current-source adapter, temporarily wrap the instance's Python-visible `load_seed_manifest` call to record `rule_count()` immediately before and after each seed manifest load. Restore the original method after boot and record the seed-boot terminal rule index. Attach the standard scene and record the scene-attachment terminal rule index. Wrap lazy `_ensure_describe` and `_conceptualize_scene_lines` calls to record per-thread native rule counts before/after faculty and conceptualizer construction. Run two simultaneous describe-scene calls with native access tracing enabled only across the calls, then read the final native rule index/name/UID table. Assign each UID in a seed load interval to that seed; separately classify bootstrap rules, scene-attachment additions, lazy faculty rules, conceptualizer rules, and any remaining conversation-time additions. Join observed UIDs to per-rule access counts. Also capture the boot report and failures.

The wrapper observes loader calls but does not alter manifests or native rule logic. It adds diagnostic reads and is not used for timing. Any overlapping/inconsistent ranges, source drift, incomplete trace, or UID/name mismatch invalidates the provenance join. Dynamic post-boot rules remain explicitly unassigned.

## Gates and limits

- Source/native closure equals v2.4 and remains unchanged during capture.
- Per-seed rule index intervals are monotone, non-overlapping, and cover each appended native rule index exactly once.
- UID/name mapping covers each traced native rule after requests complete.
- Seed-installed ranges end at the post-boot rule count; scene and request-time additions remain separately attributed by phase.
- Report unassigned traced UIDs and boot failures rather than inferring their seed.

This maps native rule table provenance and observed counts for one live fixture on the newly locked source. It does not reproduce v2.4's older source or imply every installed rule is necessary; seed removal still requires ablation and held-out capability tests.

## Artifacts

[Runner](../../../scripts/substrate_seed_rule_provenance_live_capture_v1.py), [lock](../../../evaluation/substrate_capability/seed_rule_provenance_live_capture_v1_lock_20260927.json), [capture](../../../evaluation/reports/seed_rule_provenance_live_capture_v1_20260927.json), [analysis](../../../evaluation/reports/seed_rule_provenance_live_capture_v1_analysis_20260927.json).
