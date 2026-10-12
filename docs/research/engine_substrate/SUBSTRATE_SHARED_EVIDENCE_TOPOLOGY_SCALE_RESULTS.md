# Shared evidence topology and scale results

## Semantic result

The locked 108-worker study passed all gates across path, star, and balanced binary tree topologies at N=8/16/32/64. All 36 full/scoped pairs matched expected local state at each of six checkpoints: baseline, edge insertion plus activation, active value update, explicit deactivation/retraction plus edge deletion, re-insertion at a new value, and a second retraction/deletion. All 36 omitted-boundary controls left exactly the two selected boundary outputs stale at activation, update, and re-activation; other outputs matched. The independent audit verified all locked source hashes and the complete report matrix.

## Work and timing

Work counters are identical across all three topologies at each size. Each topology has N−1 evidence boundaries and the same two native rules; degree distribution changes which scopes own the boundary but not the number of matched facts in this workload.

| Frames | Full candidate pairs | Scoped candidate pairs | Full Term evaluations | Scoped Term evaluations |
|---:|---:|---:|---:|---:|
| 8 | 238 | 3,612 | 2,058 | 29,904 |
| 16 | 510 | 15,900 | 4,410 | 131,760 |
| 32 | 1,054 | 66,588 | 9,114 | 552,048 |
| 64 | 2,142 | 272,412 | 18,522 | 2,258,928 |

The scoped candidate count approximately quadruples per doubling, while the full candidate count approximately doubles. That is the measured work envelope of repeatedly invoking this generic scope API over this rule family; it is not a theorem about all scoped schedulers. At N=64, total median wall times over six checkpoints were:

| Topology | Full | Scoped | Scoped/full |
|---|---:|---:|---:|
| Path | 0.935 ms | 69.188 ms | 74.0× |
| Star | 0.780 ms | 65.145 ms | 83.5× |
| Binary tree | 0.767 ms | 65.367 ms | 85.2× |

The star’s high degree did not raise the audited matching work over path or tree. This is consistent with the current API doing repeated broad match enumeration and filtering bindings by scope. Wall time is environment-specific and based on three process replicates; operation counters provide the stronger result. At N=64, frame-scoped closure is semantically correct but substantially more expensive under this schedule.

## Limits and next experiment

The benchmark uses two authored rules, fixed connected topologies, N≤64, and caller-selected round-robin visits. Retraction sets the evidence inactive, lets the explicit reset rule run, then removes support edges; it does not test truth maintenance from edge deletion alone. It is not natural workload prevalence, automatic notification, GALS, or a general asymptotic result. Next test dynamic topology with crossing edge insertion/deletion and randomized connected graphs, then compare per-rule incremental scheduling against full closure under the same mutations. The omitted-notification controls must remain.

Artifacts: [preregistration](SUBSTRATE_SHARED_EVIDENCE_TOPOLOGY_SCALE_PREREG_20260925.md), [runner](../../../scripts/substrate_shared_evidence_topology_scale.py), [independent audit](../../../scripts/analyze_substrate_shared_evidence_topology_scale.py), [raw report](../../../evaluation/reports/substrate_shared_evidence_topology_scale_20260925.json), and [lock](../../../evaluation/substrate_capability/shared_evidence_topology_scale_lock_20260925.json).
