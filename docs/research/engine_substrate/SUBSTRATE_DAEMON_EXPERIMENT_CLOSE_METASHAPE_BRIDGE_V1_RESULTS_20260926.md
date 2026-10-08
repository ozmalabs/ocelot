# Daemon experiment-close → MetaShape bridge v1 results (2026-09-26)

## Preregistered outcome

The capture loaded the two-seed dependency closure with no failures, closed both graph-ready Experiments, added two ShapeObservations, and minted one MetaShape with support 2. The preregistered status-order gate required `residual → recognized`; the observed statuses were `recognized → recognized`, so the preregistered gate correctly fails. Both observations nevertheless retain residual relations for the differing `axis_tag` and `topic` fields. Do not reinterpret this v1 result as an admitted pass.

This mismatch reveals that observation status `recognized` does not mean “no residual”: the decode record can recognize a held pattern while preserving varying relations, and the recurrence rules can mint from those residuals. V1.1 separately preregistered an exact fresh-process replication of that observed pattern; see [v1.1 results](SUBSTRATE_DAEMON_EXPERIMENT_CLOSE_METASHAPE_BRIDGE_V1_1_RESULTS_20260926.md).

## Evidence

- Protocol: [preregistration](SUBSTRATE_DAEMON_EXPERIMENT_CLOSE_METASHAPE_BRIDGE_PREREG_20260926.md)
- Runner: [daemon close-action probe](../../../scripts/substrate_daemon_experiment_close_metashape_bridge_v1.py)
- Analyzer: [preregistered-gate analysis](../../../scripts/analyze_substrate_daemon_experiment_close_metashape_bridge_v1.py)
- Lock: [source and inputs](../../../evaluation/substrate_capability/daemon_experiment_close_metashape_bridge_v1_lock_20260926.json)
- Raw: [capture](../../../evaluation/reports/substrate_daemon_experiment_close_metashape_bridge_v1_20260926.json)
- Analysis: [gate summary](../../../evaluation/reports/substrate_daemon_experiment_close_metashape_bridge_v1_analysis_20260926.json)
