# Matched frame-topology scale results

**Protocol:** [`SUBSTRATE_FRAME_TOPOLOGY_MATCHED_SCALE_PREREG_20260926.md`](SUBSTRATE_FRAME_TOPOLOGY_MATCHED_SCALE_PREREG_20260926.md)  
**Raw capture:** [`substrate_frame_topology_matched_scale_v1_20260926.json`](../../../evaluation/reports/substrate_frame_topology_matched_scale_v1_20260926.json)  
**Independent analysis:** [`substrate_frame_topology_matched_scale_v1_20260926_analysis.json`](../../../evaluation/reports/substrate_frame_topology_matched_scale_v1_20260926_analysis.json)  
**Runner:** [`substrate_frame_topology_matched_scale_v1.py`](../../../scripts/substrate_frame_topology_matched_scale_v1.py)

## Gate result

All 480 independently recomputed checks passed across 60 paired runs (three topologies × four sizes × five repetitions), plus one omitted-leaf ablation per pair. Each topology at each size has N frames, N Concepts, N−1 directed dependency edges, and the same four rules. Event scheduling matched full state after activation and retraction, all changed frames were notified, all queues settled, and the omitted leaf's local observation remained stale as required. Counter and build fingerprints are present.

## Measured work ratios

Medians are over five instrumented paired runs. Candidate and Term evaluation ratios compare the sum of activation and retraction counters; wall-time ratios compare instrumented closure/settlement time. Timings are descriptive and instrumentation was enabled in both arms.

| Topology | Frames | Event candidates | Full candidates | Candidate ratio | Term-evaluation ratio | Event/full time |
|---|---:|---:|---:|---:|---:|---:|
| Chain | 8 | 907 | 465 | 1.95× | 1.96× | 2.44× |
| Chain | 16 | 3,731 | 1,953 | 1.91× | 1.91× | 2.23× |
| Chain | 32 | 15,139 | 8,001 | 1.89× | 1.89× | 1.99× |
| Chain | 64 | 60,995 | 32,385 | 1.88× | 1.88× | 1.90× |
| Binary tree | 8 | 907 | 225 | 4.03× | 4.05× | 4.19× |
| Binary tree | 16 | 3,731 | 589 | 6.33× | 6.39× | 6.42× |
| Binary tree | 32 | 15,139 | 1,449 | 10.45× | 10.54× | 9.96× |
| Binary tree | 64 | 60,995 | 3,429 | 17.79× | 17.96× | 16.57× |
| Star | 8 | 907 | 105 | 8.64× | 8.45× | 6.32× |
| Star | 16 | 3,731 | 217 | 17.19× | 16.82× | 11.91× |
| Star | 32 | 15,139 | 441 | 34.33× | 33.60× | 23.71× |
| Star | 64 | 60,995 | 889 | 68.61× | 67.17× | 46.89× |

At fixed N, event-work counters are effectively identical across the three shapes, while full-closure work falls sharply from chain to tree to star. At N=64, event scheduling enumerates 60,995 candidates on every topology; full closure enumerates 32,385 on the chain, 3,429 on the tree, and 889 on the star. Event turns are 4N in this implementation. For the star, full closure can propagate in one shallow wave, while the scoped worker still visits every frame and repeatedly invokes scoped matching. Thus, the current scoped API fails to exploit the shallow dependency depth that makes the star easy for full closure. This is direct evidence against treating small separators or correct owner notifications as sufficient for an efficiency claim.

## Interpretation and limits

The probe supports exact scheduler semantics for this generated propagation family and exposes a topology-sensitive cost gap. It does not prove that scoped execution is always slower: the chain's ratio narrows to 1.88× in candidate work at N=64. Nor does it establish natural graph topology distributions, high-N asymptotics, or cost with instrumentation disabled. Candidate counters are enumerated matcher work, not machine instructions. The next engine question is to reduce repeated per-frame scans or batch scopes, then rerun this locked matrix; the structural question remains whether partitions learned from actual tasks have separators and depths resembling these fixtures.

## Reproduction

```sh
PYTHONPATH=runners/dsl/python:. python3 scripts/substrate_frame_topology_matched_scale_v1.py
python3 scripts/analyze_substrate_frame_topology_matched_scale_v1.py
```
