# Frame topology cost attribution: scoped audit repaired and profiled

**Protocol:** [`SUBSTRATE_FRAME_TOPOLOGY_COST_ATTRIBUTION_PREREG_20260926.md`](SUBSTRATE_FRAME_TOPOLOGY_COST_ATTRIBUTION_PREREG_20260926.md)  
**v1.0 failed-gate capture:** [`substrate_frame_topology_cost_attribution_v1_0_scope_audit_gap_20260926.json`](../../../evaluation/reports/substrate_frame_topology_cost_attribution_v1_0_scope_audit_gap_20260926.json)  
**v1.1 confirmatory capture:** [`substrate_frame_topology_cost_attribution_v1_1_20260926.json`](../../../evaluation/reports/substrate_frame_topology_cost_attribution_v1_1_20260926.json)  
**Independent analysis:** [`substrate_frame_topology_cost_attribution_v1_1_analysis_20260926.json`](../../../evaluation/reports/substrate_frame_topology_cost_attribution_v1_1_analysis_20260926.json)  
**Runner:** [`substrate_frame_topology_cost_attribution_v1.py`](../../../scripts/substrate_frame_topology_cost_attribution_v1.py)

## Result

The v1.0 30 N=64 event/full pairs reached semantic parity, but scoped per-rule rows were absent in every phase. That failed-gate capture, exact runner, native binary, and pre-change Rust source snapshot remain archived. The source snapshot's aggregate Rust fingerprint independently reproduces the captured fingerprint.

The v1.1 amendment carries each active rule's original vector slot into the scoped runner and establishes/clears the native per-rule audit context for each rule attempt. The fixture tombstones slot 1 and reinstalls `propagate_off` at slot 4, so the active indices are `{0,2,3,4}`. Across 30 amended N=64 pairs, semantic parity, empty-queue settlement, fixed points, exact original-index/name mapping, and candidate/where/Term counter conservation all pass. The global audit rows now equal the sum of per-rule rows for each phase.

## Attributed work

Median combined-phase candidate pairs by rule, ten paired repetitions per topology:

| Topology | Rule | Event candidates | Full candidates | Event/full |
|---|---|---:|---:|---:|
| Chain | propagate on | 32,130 | 8,064 | 3.98× |
| Chain | propagate off | 20,097 | 8,001 | 2.51× |
| Chain | observe on | 447 | 8,256 | 0.05× |
| Chain | observe off | 383 | 8,192 | 0.05× |
| Binary tree | propagate on | 32,130 | 882 | 36.43× |
| Binary tree | propagate off | 20,097 | 819 | 24.54× |
| Binary tree | observe on | 447 | 960 | 0.47× |
| Binary tree | observe off | 383 | 896 | 0.43× |
| Star | propagate on | 32,130 | 252 | 127.50× |
| Star | propagate off | 20,097 | 189 | 106.33× |
| Star | observe on | 447 | 320 | 1.40× |
| Star | observe off | 383 | 256 | 1.50× |

The majority of the excess event work is in repeated propagation-rule matching, and that gap grows strongly as the topology becomes shallower. Observation rules cost less in the scoped arm for the chain/tree, where full closure revisits them over multiple passes. The v1.1 runner moves `propagate_off` after the observation rules to create an inactive slot without changing the rule set; therefore its absolute totals are not a direct replacement for the original-order topology-scale totals. Event/full ratios within v1.1 remain matched because both arms use the same rule order.

The scoped accounting change is audit-only: rule-attempt identity brackets matching/effects, and no rewrite or scheduling branch reads the audit mode. It remains necessary to measure audit-on/off state parity directly before treating per-rule timing as low-overhead. The separate empty/no-match scoped-call benchmark is still needed to quantify per-call rule-list/setup time; no clone cost is inferred from the attribution table.
