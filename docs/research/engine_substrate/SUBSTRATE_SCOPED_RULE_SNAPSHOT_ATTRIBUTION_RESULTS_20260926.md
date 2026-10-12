# Scoped rule snapshot attribution results

**Protocol:** [`SUBSTRATE_SCOPED_RULE_SNAPSHOT_ATTRIBUTION_PREREG_20260926.md`](SUBSTRATE_SCOPED_RULE_SNAPSHOT_ATTRIBUTION_PREREG_20260926.md)  
**Runner:** [`substrate_scoped_rule_snapshot_attribution_v1.py`](../../../scripts/substrate_scoped_rule_snapshot_attribution_v1.py)  
**Independent analysis:** [`substrate_scoped_rule_snapshot_attribution_v1_20260926_analysis.json`](../../../evaluation/reports/substrate_scoped_rule_snapshot_attribution_v1_20260926_analysis.json)

All 60 cells (three active counts × two tombstone counts × two rule shapes × five repeats) pass the independent integrity and semantic gates. There are no candidate or Term evaluations, calls make zero progress, active and total slot counts match the fixture, and graph projections remain unchanged.

At fixed active count, adding an equal number of tombstoned slots shows no stable latency increase: median deltas are between −3.2 and +12.2 μs/call, generally within the broad repeat ranges. These data do not support tombstone-slot scanning as a dominant cost at 64–512 active rules.

The large shape (eight disconnected absent match edges and eight effects per rule) is slower than the small shape (one edge and one effect) by 4.3, 28.0, and 63.9 μs/call at 64, 256, and 512 active rules. This implicates active rule-body processing, but the contrast changes match-pattern and effect payload together and includes matching setup. It cannot quantify `RewriteRule::clone` alone. No cache or cursor implementation has yet been justified by a clone-only estimate.

**Next gate:** a preregistered factorial contrast varying match-edge count and effect count independently at fixed active/slot counts, followed by direct component profiling or a narrow clone-only native diagnostic if the effect-payload axis scales. Preserve active order, tombstone behavior, mutation visibility, and original slot attribution in any later optimization. This synthetic no-match result does not establish the same cost profile for production rule distributions.
