# Live self-report task-variant capture v1.8 (2026-09-26)

## Result

V1.8 uses the same full-source closure as v1.7 and runs three fresh workers. Each worker completes `report your organisation` through the live self-report path: the Goal target is `self_organisation`, the Goal owns its origin Message/event, selection→execution→result events are all bound, and the Goal resolves and closes. The worker then receives `describe who you are`. That turn returns a nonempty reply, but has no `communication_route` value, no Goal, and no lifecycle events. The expected self-report lifecycle is absent in all three workers.

All five pre-existing identity controls (correct link, omitted link, swapped link, duplicate result, faculty failure) pass in every run. The full seed/Python source closure, native artifact, and start/end/post-run fingerprints remain stable. The first prompt's helper work reproduces exactly; the second prompt produces zero lifecycle helper calls because dispatch stops before that producer.

## Analysis lineage

The original v1.8 independent analyzer is preserved as the lock-listed analyzer, but it did not handle a missing Goal object and raised while inspecting the reproduced shortfall. A separate diagnostic analyzer handles the expected `None` case and passes 11 evidence-integrity, first-turn, work-conservation, control, and replicated-shortfall checks. Thus the capture and analysis are valid, while the requested two-target capability gate fails: only the organization prompt reaches the live self-report lifecycle.

## Interpretation and limits

The result distinguishes the lifecycle writer from the language-to-action dispatch path. Goal identity and native transitions pass for the first task, and the existing explicit-link controls still pass. The second prompt does not exercise those rules because it emits no self-report Goal/event sequence. A follow-up diagnostic later captured the selected comprehension: `describe who you are` is a question routed through a held meta table, not a self-report instruction. Thus the absent action lifecycle is a route-selection expectation mismatch, not evidence that self-identity answering is unavailable. A source-locked paraphrase probe found direct question/meta and action/self-report routes; see [route probe v1](SUBSTRATE_LIVE_SELF_IDENTITY_ROUTE_PROBE_V1_RESULTS_20260926.md). The action phrasings also create a second unresolved, target-less `report_self` Goal, which needs producer attribution.

This is one organization request plus one self-identity request in a fixed order on the same live adapter. It is not a prevalence, quality, or general-language understanding estimate. Counter totals from the first prompt must not be attributed to the second.

## Artifacts

- Amendment: [v1.8 task pair and expected targets](SUBSTRATE_LIVE_SELF_REPORT_LIFECYCLE_IDENTITY_V1_8_AMENDMENT_20260926.md)
- Runner: [`substrate_live_self_report_lifecycle_identity_integration_v1_8.py`](../../../scripts/substrate_live_self_report_lifecycle_identity_integration_v1_8.py)
- Lock: [full source lock](../../../evaluation/substrate_capability/live_self_report_lifecycle_identity_integration_v1_8_lock_20260926.json)
- Raw capture: [three workers and five controls](../../../evaluation/reports/substrate_live_self_report_lifecycle_identity_integration_v1_8_20260926.json)
- Preserved original analyzer: [`analyze_substrate_live_self_report_lifecycle_identity_integration_v1_8.py`](../../../scripts/analyze_substrate_live_self_report_lifecycle_identity_integration_v1_8.py)
- Diagnostic analyzer and replicated-outcome audit: [`analyze_substrate_live_self_report_lifecycle_identity_integration_v1_8_diagnostic.py`](../../../scripts/analyze_substrate_live_self_report_lifecycle_identity_integration_v1_8_diagnostic.py), [analysis JSON](../../../evaluation/reports/substrate_live_self_report_lifecycle_identity_integration_v1_8_diagnostic_analysis_20260926.json)
