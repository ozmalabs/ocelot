# Scoped node lifecycle notification result

**Protocol:** [`SUBSTRATE_SCOPED_NODE_LIFECYCLE_PREREG_20260926.md`](SUBSTRATE_SCOPED_NODE_LIFECYCLE_PREREG_20260926.md)  
**Raw capture:** [`substrate_scoped_node_lifecycle_probe_v1_20260926.json`](../../../evaluation/reports/substrate_scoped_node_lifecycle_probe_v1_20260926.json)  
**Independent analysis:** [`substrate_scoped_node_lifecycle_probe_v1_20260926_analysis.json`](../../../evaluation/reports/substrate_scoped_node_lifecycle_probe_v1_20260926_analysis.json)

## Result

All nine runner gates and all eight independent analysis gates passed on native artifact `24073a9be8433613adb245804a1e4714a07ba9960b6d3fe501942540170c4ed6`.

In the two-frame fixture, a scoped A rule minted an A-owned Concept and a directed influence edge into B. The native report identified exactly owners A and B. Consuming those notifications let B's rule set its state to 1; the final event-queue projection matched monolithic closure. A second intervention deleted the minted node and its incident cross-frame edge. Again the write report identified A and B, B's retract rule set its state back to 0, and the event result matched full closure. Both queue settlements ended with an empty queue and no deferred effects or progress-cap hit. The independent analyzer also verified the raw evidence's protocol, runner, Rust-source, binding, and native binary hashes.

The negative control omitted the initial external A-frame seed. No rule ran, no node was minted, and its state differed from the full-closure reference. This confirms a boundary of the tested contract: mutation reports can notify dependent owners after a scoped rule writes, while the caller still has to seed the frame containing an external intervention.

## Scope of the evidence

This establishes owner notification and queue consumption for one controlled two-frame node-birth/deletion mechanism, including ownership-edge mutation and incident-edge removal. It does not establish general scheduling correctness, automatic discovery of external mutation sources, root-frame deletion/repartitioning, arbitrary deferred effects, or natural-task prevalence. No Rust engine changes were needed; this is measurement of the existing native contract.

## Reproduction

```sh
PYTHONPATH=runners/dsl/python:. python3 scripts/substrate_scoped_node_lifecycle_probe_v1.py
python3 scripts/analyze_substrate_scoped_node_lifecycle_probe_v1.py
```
