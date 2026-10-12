# Describe-scene combined measurement-hooks diagnostic v1 (2026-09-27)

## Question

Do the three v2.3 measurement hooks, combined but with native access tracing and schedule barriers disabled, disrupt ordinary concurrent describe-scene requests?

## Method and gates

Use two simultaneous requests on one adapter and a source lock captured immediately before and after. Enable the observed lock proxy with tracing disabled, the goal-event audit wrapper without pausing callbacks, and the nested public lock used for turn-output readback. Require both worker threads to join, source lock stability, two expected public replies, one resolved Goal per inbound, and producer events for selection, execution, and action result. This is a diagnostic of hook interaction only; it does not establish access-trace correctness or identify the v2.3 driver failure.

## Result

The locked run passes: both replies describe the fixture, source inputs remain stable, both request-bound Goals resolve, and six expected producer events are captured. See [report](../../../evaluation/reports/describe_scene_measurement_hooks_combined_diagnostic_v1_20260927.json) and [runner](../../../scripts/substrate_describe_scene_measurement_hooks_combined_diagnostic_v1.py).
