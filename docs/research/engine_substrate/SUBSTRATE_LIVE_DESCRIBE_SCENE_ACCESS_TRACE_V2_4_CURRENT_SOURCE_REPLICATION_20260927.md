# Live describe-scene v2.4 current-source replication

Date: 2026-09-27

## Purpose

The existing v2.4 capture predated a change to `substrate/world_adapter.py`. This replication refreshed the source lock and reran the same three-pair traced/untraced fixture against the current file (SHA-256 `517cec9914d600ca4572fbc96436f5319f6d60d2ef3f0903ee921c25d7b9cb12`). The native extension and build manifest are unchanged.

## Result

All six workers passed the driver and independent analysis gates: three distinct traced/untraced pairs, source stability at worker start/end and post-run, completed thread and Goal lifecycles, exact paired semantic and whole-graph parity, complete request trace intervals, and zero dropped events. All runs ended with 25,201 nodes and 11,848 edges and the same semantic graph digest. The traced and untraced arms therefore agree on this fixture's final graph and public replies.

The full-route native access trace repeats exactly in all three workers: request A has 1,140,892 selected events and request B has 997,848, with zero drops. These are selected access events, not a complete count of all engine operations. The trace projections still have 35/32 boundary incidences and 20/18 unique external nodes for A/B; the small owned induced-width bound of 2 does not establish a small cut or factorization.

Three separately audited Goal-bound producer closures per request give the following exact candidate and Term totals in every traced worker:

| Request | Candidate tests | Term evaluations |
|---|---:|---:|
| A | 139,279 | 722,488 |
| B | 198,600 | 966,170 |

These totals cover the event-producer closure intervals, not every rule execution across the entire `converse` request. They should not be presented as whole-route matcher totals. In addition, public reply text still fails to match any graph-visible outbound Message in each traced arm; public/graph output alignment remains a capability gap even though paired arms are equivalent.

Uninstrumented request-A wall medians are 12.679 s and CPU medians 12.595 s; request-B wall medians are 0.833 s and CPU medians 0.416 s, under this concurrent schedule. Boot median is 13.047 s. Traced medians are higher, so traced latency is not baseline cost. These are fixture-specific timings, not service-time estimates or scaling curves.

## Interpretation

This upgrades reproducibility of the prior live-route capture to the current `world_adapter.py` source. It confirms substantial stable full-route selected access activity while exact final graph and response parity hold across tracing modes. It does not show that the measured request frames are local: most accesses touch none of the currently classified task nodes, inputs, or rule-produced descendants, and the dynamic dependency projection is incomplete. Nor does it prove the candidate/Term totals for the entire request because the producer hook only brackets the three Goal-event closure calls.

The next tractability step is to extend attribution over the full `converse` call, preserving the current paired parity gates, and reconcile every native closure interval with the whole-request trace. In parallel, resolve why the public reply lacks a corresponding graph-visible outbound Message; output alignment is a behavioral correctness issue, not just a tractability cost.

## Artifacts

- [Original preregistration](SUBSTRATE_LIVE_DESCRIBE_SCENE_ACCESS_TRACE_V2_4_PREREG_20260927.md)
- [Runner](../../../scripts/substrate_live_describe_scene_access_trace_v2_4.py)
- [Current source lock](../../../evaluation/substrate_capability/live_describe_scene_access_trace_v2_4_lock_20260927.json)
- [Current capture](../../../evaluation/reports/substrate_live_describe_scene_access_trace_v2_4_20260927.json)
- [Raw workers](../../../evaluation/reports/substrate_live_describe_scene_access_trace_v2_4_workers_raw_20260927.json)
- [Independent analysis](../../../evaluation/reports/substrate_live_describe_scene_access_trace_v2_4_analysis_20260927.json)
- [Boundary-touch analysis](../../../evaluation/reports/substrate_live_describe_scene_access_trace_v2_4_boundary_touch_v1_20260927.json)
- [Ownership/descendant analysis](../../../evaluation/reports/substrate_live_describe_scene_access_trace_v2_4_rule_descendants_v1_1_20260927.json)
