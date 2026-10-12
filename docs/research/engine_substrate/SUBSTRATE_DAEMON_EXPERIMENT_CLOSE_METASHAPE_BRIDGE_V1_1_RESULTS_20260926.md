# Daemon experiment-close → MetaShape bridge v1.1 results (2026-09-26)

## Replicated behavior

A fresh process with the source-locked two-seed growth profile reproduced the v1 status/residual pattern. The daemon's `_close_tick` marked both graph-ready Experiments taught and emitted two `ShapeObservation` nodes. Both observations were labeled `recognized`; both retained residual predicates `axis_tag` and `topic`. The growth rules minted exactly one new MetaShape with support 2. The close action took 1.72 ms in this single small capture. All six preregistered replication gates pass.

This confirms the bridge from a daemon close action to recurrence-based symbolic minting for this controlled fixture. It also confirms an important status-semantic detail: `recognized` can coexist with residual relations that feed minting. The minted abstraction may be a useful summary of held experiment-result structure, but its value has not been tested; axis and topic variation were deliberately authored. No independent validity of the two `supported` outcomes is implied.

## Capability boundary

The daemon has at least two distinct evidence routes:

- The general graph-selected `teacher` route writes `TeacherEvidence` and candidate nodes; it does not call `teach()`.
- The graph-selected `close` route calls `reflective_faculty.close_experiment_loop`; ready experiment conclusions and eligible adoptions are passed through `teach()`, which observes their shape and may trigger MetaShape recurrence/mint rules.

Ordinary repeated statement turns in the separate public-conversation probe generated no `ShapeObservation` or `MetaShape` delta. Thus the demonstrated learning path is gated by experiment conclusions/adoptions, rather than general conversation comprehension on that fixture.

## Evidence and reproduction

- V1 initial preregistration and criterion miss: [v1 results](SUBSTRATE_DAEMON_EXPERIMENT_CLOSE_METASHAPE_BRIDGE_V1_RESULTS_20260926.md)
- Replication amendment: [v1.1 amendment](SUBSTRATE_DAEMON_EXPERIMENT_CLOSE_METASHAPE_BRIDGE_V1_1_AMENDMENT_20260926.md)
- Lock: [source and fixed inputs](../../../evaluation/substrate_capability/daemon_experiment_close_metashape_bridge_v1_1_lock_20260926.json)
- Runner: [v1.1 close-action probe](../../../scripts/substrate_daemon_experiment_close_metashape_bridge_v1_1.py)
- Analyzer: [replication gates](../../../scripts/analyze_substrate_daemon_experiment_close_metashape_bridge_v1_1.py)
- Raw: [capture](../../../evaluation/reports/substrate_daemon_experiment_close_metashape_bridge_v1_1_20260926.json)
- Analysis: [gate summary](../../../evaluation/reports/substrate_daemon_experiment_close_metashape_bridge_v1_1_analysis_20260926.json)
