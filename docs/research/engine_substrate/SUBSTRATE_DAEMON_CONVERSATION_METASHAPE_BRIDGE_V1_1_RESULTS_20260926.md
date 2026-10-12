# Daemon conversation → MetaShape bridge v1.1 results (2026-09-26)

## Result

One source-locked fresh full-profile adapter loaded 729 of 740 selected seed manifests, with the same 11 failures documented in the daemon activation census. The probe then sent four fixed ordinary statements through `WorldAdapter.converse`: two novel relational claims, each repeated once. Across all four turns, the graph gained zero `ShapeObservation`, `MetaShape`, `TaughtHint`, and `TeacherEvidence` nodes. All turns returned a reply; the seed-persistence guard was active. The full profile's shape loop and MetaShape growth availability is established independently by [daemon activation census v2](SUBSTRATE_INDUCTION_DAEMON_ACTIVATION_CENSUS_V2_RESULTS_20260926.md).

This is direct negative reachability evidence for this conversation route and fixture: ordinary statement processing did not feed the MetaShape growth path, even though full boot had its rules available. It does not show that no other daemon action invokes `teach()` or that all conversational utterances behave the same way.

## Timing

Without Python call tracing, full boot took 12.21 s in this one capture. Turn latencies were 254.7, 85.8, 77.1, and 76.3 ms. The first turn includes warm-up effects; these are single-process descriptive measurements, not a stable cost distribution. The earlier v1 call-traced times (10–17 s/turn) are instrumentation-contaminated and explicitly excluded.

## Reproduction

- Protocol: [v1 preregistration](SUBSTRATE_DAEMON_CONVERSATION_METASHAPE_BRIDGE_PREREG_20260926.md)
- Amendment: [v1.1 removal of call tracing](SUBSTRATE_DAEMON_CONVERSATION_METASHAPE_BRIDGE_V1_1_AMENDMENT_20260926.md)
- Source/input lock: [JSON](../../../evaluation/substrate_capability/daemon_conversation_metashape_bridge_v1_1_lock_20260926.json)
- Runner: [v1.1 runner](../../../scripts/substrate_daemon_conversation_metashape_bridge_v1_1.py)
- Analyzer: [gate analyzer](../../../scripts/analyze_substrate_daemon_conversation_metashape_bridge_v1_1.py)
- Raw capture: [JSON](../../../evaluation/reports/substrate_daemon_conversation_metashape_bridge_v1_1_20260926.json)
- Gate summary: [analysis JSON](../../../evaluation/reports/substrate_daemon_conversation_metashape_bridge_v1_1_analysis_20260926.json)
