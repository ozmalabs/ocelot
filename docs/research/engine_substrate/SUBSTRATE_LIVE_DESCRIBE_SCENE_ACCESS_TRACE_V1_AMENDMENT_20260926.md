# Live `describe_scene` access trace v1 amendment (2026-09-26)

## Purpose and scope

Replay the existing three-worker concurrent `describe_scene` boundary probe with the native access trace enabled only around the two serialized requests. Preserve the same generated scene, deliberate A/B overlap, full graph capture, owned-node definitions, lifecycle gates, and baseline reply. This provides one task-level crosswalk between concrete rule-attributed engine events and the complete typed-edge cuts.

## Measurements and gates

For each fresh worker, reset the default-off trace after seed loading, enable immediately before request A, disable after both worker threads join, and snapshot before post-run projection work. Record each aggregated event's stable rule UID/name, event kind, concrete node/peer, resource, count, distinct row count, and dropped count. Intersect concrete node/peer IDs with each task's owned set. Retain the original three-worker, thread, serialization, lifecycle, event-order, reply, source-stability, and boundary-repeat gates. Require zero dropped trace rows for an interpretable capture; repeated trace counts are descriptive, not an exact semantic parity requirement.

## Interpretation limits

The trace is explicitly partial: current instrumentation omits specialized graph-scan paths and some host-side accesses/mutations. A missing event is not evidence of no dependency. Counts include accesses by both requests and any native rule work reached within the traced interval; they do not by themselves attribute events to a specific user turn. This does not measure trace overhead, partitioned closure, scheduler wakeups, natural-task prevalence, or speedup. Preserve the static `rule_access_sets()` projection as a separate conservative diagnostic.

## Reproduction

Run `scripts/substrate_live_describe_scene_access_trace_v1.py --lock`, freeze the resulting lock at `evaluation/substrate_capability/live_describe_scene_access_trace_v1_lock_20260926.json`, then run the script normally. It launches three fresh worker processes and writes the raw and analyzed reports under `evaluation/reports/`.
