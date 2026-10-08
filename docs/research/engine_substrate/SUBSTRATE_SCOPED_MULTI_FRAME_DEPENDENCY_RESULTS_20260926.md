# Scoped multi-frame dependency notification results

**Protocol:** [initial preregistration](SUBSTRATE_SCOPED_MULTI_FRAME_DEPENDENCY_PREREG_20260926.md) and [v1.1 amendment](SUBSTRATE_SCOPED_MULTI_FRAME_DEPENDENCY_V1_1_AMENDMENT_20260926.md)  
**Confirmatory raw capture:** [`substrate_scoped_multi_frame_dependency_probe_v1_20260926.json`](../../../evaluation/reports/substrate_scoped_multi_frame_dependency_probe_v1_20260926.json)  
**Independent analysis:** [`substrate_scoped_multi_frame_dependency_probe_v1_20260926_analysis.json`](../../../evaluation/reports/substrate_scoped_multi_frame_dependency_probe_v1_20260926_analysis.json)  
**Preserved failed pilot:** [`pilot raw`](../../../evaluation/reports/substrate_scoped_multi_frame_dependency_probe_v1_20260926_pilot_failure.json), [exact pilot runner](../../../scripts/archive/substrate_scoped_multi_frame_dependency_probe_v1_0_failed.py)

## Confirmatory result

All ten independent confirmatory gates passed on the locked native binary. The scoped A rule minted one owned node with dependencies into both B and C. The native birth report named exactly `{A,B,C}`; processing the notifications set both downstream states to 1 and matched monolithic closure. Deleting the node through A removed both cross-frame edges, notified exactly `{A,B,C}` (including C, whose dependency was incident to the deleted node), reset both downstream states to 0, and again matched full closure. Both event settlements reached empty queues without a cap hit or deferred work. The omitted-seed control remained unminted and differed from full closure.

The first pilot failed event/full parity because the untyped B and C target variables admitted swapped bindings: full closure minted two bridges, whereas one scoped pass minted one. That failed capture and its exact runner source are retained. The v1.1 amendment adds explicit immutable frame-role guards to remove only that fixture ambiguity; it changed no success gates or scheduling policy. This is a useful harness finding as well as a corrected measurement.

## Boundary

This strengthens the lifecycle result from one cross-frame dependency to two distinct dependent frames and verifies cascading incident-edge removal. It does not establish completeness for arbitrary dependency degree, frame-root deletion/repartitioning, external source discovery, arbitrary effects, general scheduler correctness, or natural-task prevalence. No native implementation change was needed.

## Reproduction

```sh
PYTHONPATH=runners/dsl/python:. python3 scripts/substrate_scoped_multi_frame_dependency_probe_v1.py
python3 scripts/analyze_substrate_scoped_multi_frame_dependency_probe_v1.py
```
