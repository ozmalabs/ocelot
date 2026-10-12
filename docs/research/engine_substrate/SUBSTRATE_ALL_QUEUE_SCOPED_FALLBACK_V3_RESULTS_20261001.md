# Order-sensitive scoped/full continuation v3 results

Date: 2026-10-01

## Outcome

The preregistered order-sensitive continuation selects the same final `selected_mid` in all 27 workers. The selection is a shared-sink last-match write over the `handled_mid` bindings, guarded by a one-shot `probe_done` marker so the probe converges. Thus the edge-vector ordering differences from v2 did not change the result of this specific matcher-driven continuation.

The strict exact graph-wire gate still fails in 18/27 workers (all R>1), so the analyzer reports 309/327 checks. A post-hoc canonical state comparison confirms identical node arrays and edge-fact multisets in 27/27; exact wire equality is 9/27. All five deferred queue counts, distinct handled/verified edge counts, target/frame outcomes, fixed-point reports, and order-sensitive selected-node equality pass. The v2 observation that some `handled_mid` entries are stored in a different relative order remains true; however, the runtime match traversal selected the same final node in every measured cell.

This result narrows, but does not eliminate, the concern about insertion ordering. It tests one native rule-matcher consumer. Any external iterator or a different join order may observe a different order. No general order-insensitivity claim follows.

## Artifacts

- [Preregistration](SUBSTRATE_ALL_QUEUE_SCOPED_FALLBACK_V3_PREREG_20261001.md)
- [Amendment / pilot disclosure](SUBSTRATE_ALL_QUEUE_SCOPED_FALLBACK_V3_1_AMENDMENT_20261001.md)
- [Runner](../../../scripts/substrate_all_queue_scoped_fallback_v3.py)
- [Strict analyzer](../../../scripts/analyze_substrate_all_queue_scoped_fallback_v3.py) — 309/327 because exact wire parity remains false in 18 cells.
- [State/order analyzer](../../../scripts/analyze_substrate_all_queue_scoped_fallback_v3_state_order.py) — canonical facts equal 27/27; exact wire equality 9/27.
- [Source/native lock](../../../evaluation/substrate_capability/all_queue_scoped_fallback_v3_lock_20261001.json)
- [Raw workers](../../../evaluation/reports/all_queue_scoped_fallback_v3_workers_20261001.json)
- [Strict analysis](../../../evaluation/reports/all_queue_scoped_fallback_v3_analysis_20261001.json)
- [State/order analysis](../../../evaluation/reports/all_queue_scoped_fallback_v3_state_order_20261001.json)

The captured worker inputs remain stable before and after execution. The strict exact-order failure is retained rather than normalized out.

## Next gate

The v3 matcher traversal produced equal selections despite edge insertion-order differences. Next inspect which APIs enumerate `TypedGraph` edges in insertion order versus indexed/node order, then add a consumer whose observable result is known to depend on that exact API ordering. Separately exercise writes that invalidate or remove later bindings from the same snapshot, with exact full/scoped graph and residual comparisons.
