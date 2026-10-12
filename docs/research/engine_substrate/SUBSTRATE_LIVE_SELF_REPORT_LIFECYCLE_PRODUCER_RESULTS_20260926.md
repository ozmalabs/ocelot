# Live held self-report lifecycle producer results

## Confirmatory v1.1 capture

Three fresh full-seed processes each handled two identical `report your organisation` instruction turns in one live conversation. Every turn took the `self_report` route, returned a non-empty organisation-bearing response, minted exactly one `source=conversation`, `kind=report_self`, `self_target=self_organisation` Goal, and linked that Goal to its own inbound Message and DiscourseEvent. Within each run, Message, event, and Goal IDs were distinct across turns and both events had the same recipient. The producer record shape repeated across all three processes.

All semantic gates passed. The discourse state held exactly two `instruction` events and zero `selection`, `execution`, and `action_result` events. No lifecycle transition or `for_goal` edge was present. Thus this path demonstrates actual held-faculty routing and per-turn origin provenance, while confirming that the discourse lifecycle stream does not record that route's selection, execution, or outcome. The response is observable output but not a durable execution receipt.

Median full-seed boot was 13.32 s; median per-turn time was 2.21 s. These three-run timings are descriptive and not scaling evidence.

## Source-drift attempt disclosure

The initial v1 capture passed route and semantic gates, but independent analysis found that `world_adapter.py` had changed after lock creation and before capture completion. Its raw data and failing analysis are retained at the v1 paths listed below. That run is not confirmatory and was not pooled. Amendment v1.1 added worker-start, worker-end, and post-run source fingerprints; all matched the new lock for the confirmatory capture.

## Artifacts

- Base protocol: [`SUBSTRATE_LIVE_SELF_REPORT_LIFECYCLE_PRODUCER_PREREG_20260926.md`](SUBSTRATE_LIVE_SELF_REPORT_LIFECYCLE_PRODUCER_PREREG_20260926.md)
- Source-drift amendment: [`SUBSTRATE_LIVE_SELF_REPORT_LIFECYCLE_PRODUCER_V1_1_AMENDMENT_20260926.md`](SUBSTRATE_LIVE_SELF_REPORT_LIFECYCLE_PRODUCER_V1_1_AMENDMENT_20260926.md)
- Runner: [`substrate_live_self_report_lifecycle_producer_v1.py`](../../../scripts/substrate_live_self_report_lifecycle_producer_v1.py)
- Independent analyzer: [`analyze_substrate_live_self_report_lifecycle_producer_v1.py`](../../../scripts/analyze_substrate_live_self_report_lifecycle_producer_v1.py)
- Confirmatory lock: [`live_self_report_lifecycle_producer_v1_1_lock_20260926.json`](../../../evaluation/substrate_capability/live_self_report_lifecycle_producer_v1_1_lock_20260926.json)
- Confirmatory raw capture: [`substrate_live_self_report_lifecycle_producer_v1_1_20260926.json`](../../../evaluation/reports/substrate_live_self_report_lifecycle_producer_v1_1_20260926.json)
- Confirmatory independent analysis: [`substrate_live_self_report_lifecycle_producer_v1_1_analysis_20260926.json`](../../../evaluation/reports/substrate_live_self_report_lifecycle_producer_v1_1_analysis_20260926.json)
- Preserved v1 source-drift raw capture: [`substrate_live_self_report_lifecycle_producer_v1_20260926.json`](../../../evaluation/reports/substrate_live_self_report_lifecycle_producer_v1_20260926.json)
- Preserved v1 failed source audit: [`substrate_live_self_report_lifecycle_producer_v1_analysis_20260926.json`](../../../evaluation/reports/substrate_live_self_report_lifecycle_producer_v1_analysis_20260926.json)
