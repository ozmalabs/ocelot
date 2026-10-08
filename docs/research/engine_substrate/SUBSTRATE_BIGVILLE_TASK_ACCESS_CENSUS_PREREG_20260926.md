# Bigville task-derived runtime access census (diagnostic)

**Status:** pre-run diagnostic. **Workload:** the existing authored 100-resident Bigville CAN cast, loaded into one shared native substrate using the established builder and `can_native_update_3state` rule. **Question:** on one resident evidence update, what runtime frame ownership and concrete native accesses are observed, and does enabling the partial access tracer preserve the event-scheduled graph result?

This workload was used in earlier partition studies. The first diagnostic trigger (resident 0) caused zero rule firings; that exploratory raw capture was overwritten when the runner was corrected and is not available as a retained artifact. Resident 40 is used because the existing replay reports nonzero settlement for that resident. This is post-hoc trigger selection, so the corrected run is still a diagnostic capture, not an independent task-family replication or confirmatory evidence for natural-task locality.

## Frozen procedure

Run three fresh-process arms on the same frozen cast and CAN rule seed: (1) monolithic full closure, tracing off; (2) caller-notified settlement of the affected resident frame, tracing off; (3) the same caller-notified settlement, tracing on. Apply the same authored external-evidence mutation to resident position 40 in each arm. Use the existing live-graph ownership derivation (`has_concept`) and causal-adjacency component derivation. Capture full graph-state digests, node/frame membership, dependency edges, runtime event records with frame attribution, event drops, progress/candidate/Term counters, wall/CPU time, and peak RSS.

The trace is known to be partial. Runtime events may establish observed reads/writes and cross-frame accesses; absent events do not establish absent dependencies. The engine's existing full run and the monolithic arm remain the semantic reference. No engine or scheduler behavior is changed. No speed claim is part of this diagnostic.

## Checks

- The emitted frame partition must be derived from live `has_concept` and causal adjacency and cover every target CAN Concept exactly once.
- The three arms must reach the full closure cap and have identical final graph-state digests.
- The event arm's independently recomputed CAN residual count must be zero.
- The event and traced-event arms must both make at least one rule progress step; a no-op is reported but cannot serve as the substantive trigger.
- Tracing must emit at least one runtime event, have no dropped events, and have the same final graph digest as its untraced event arm.
- The output must label the runtime event model as partial and retain raw event rows and concrete frame attribution.

Failure of a check is reported as diagnostic counterevidence. This one workload cannot pass C2/C3 or establish general frame locality.
