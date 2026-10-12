# External predicate effect compensation probe v1 — results

All eight gates pass across three fresh, source-locked workers and three effect strategies. At initial revision r0 (resource value 0), no positive effect is present. Revision r1 returns 1 and commits the positive effect. Changing the r1 file back to 0 without changing graph state causes zero callback invocations in every arm; the committed effect remains unchanged. Advancing the graph revision to r2 causes the predicate to run against value 0.

The final states distinguish the correction strategies:

| Strategy | After r1 positive | After r2 negative | Engine behavior |
|---|---|---|---|
| `sticky_attr` | `accepted=1` | `accepted=1` | Positive effect persists; no inverse rule exists |
| `compensating_attr` | `accepted=1` | `accepted=0` | Authored false-case rule uses `set_attr_if_different` |
| `retractable_edge` | `accepted` edge exists | edge removed | Authored false-case rule uses `del_edge` |

The engine re-evaluates after an explicit graph revision, but does not maintain truth of earlier conclusions automatically. Compensation is an explicit rule-design obligation. Source inspection finds `SetAttrIfDifferent` and `DelEdge` effect support but no `DelAttr` effect; when absence matters, an edge can be deleted, while an attribute must use an explicit negative/tombstone value or another representation.

This is one predicate binding and a fixed transition sequence. It establishes that explicit compensators work for these cases, not generic truth maintenance, rule-order independence, retraction of arbitrary effects, or automatic resource watchers.

Artifacts: [preregistration](SUBSTRATE_EXTERNAL_EFFECT_COMPENSATION_PROBE_V1_PREREG_20260928.md), [runner](../../../scripts/substrate_external_effect_compensation_probe_v1.py), [analyzer](../../../scripts/analyze_external_effect_compensation_probe_v1.py), [raw capture](../../../evaluation/reports/external_effect_compensation_probe_v1_20260928.json), [lock](../../../evaluation/substrate_capability/external_effect_compensation_probe_v1_lock_20260928.json), [analysis](../../../evaluation/reports/external_effect_compensation_probe_v1_analysis_20260928.json).
