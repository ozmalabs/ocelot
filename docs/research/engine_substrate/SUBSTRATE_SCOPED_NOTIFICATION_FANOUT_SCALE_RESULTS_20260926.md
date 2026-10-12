# Scoped notification fanout scale results

**Protocol:** [`SUBSTRATE_SCOPED_NOTIFICATION_FANOUT_SCALE_PREREG_20260926.md`](SUBSTRATE_SCOPED_NOTIFICATION_FANOUT_SCALE_PREREG_20260926.md)  
**Raw capture:** [`substrate_scoped_notification_fanout_scale_v1_20260926.json`](../../../evaluation/reports/substrate_scoped_notification_fanout_scale_v1_20260926.json)  
**Independent analysis:** [`substrate_scoped_notification_fanout_scale_v1_20260926_analysis.json`](../../../evaluation/reports/substrate_scoped_notification_fanout_scale_v1_20260926_analysis.json)  
**Runner:** [`substrate_scoped_notification_fanout_scale_v1.py`](../../../scripts/substrate_scoped_notification_fanout_scale_v1.py)

## Semantic result

All 240 repeat-level checks passed across 30 paired event/full runs and 30 omitted-leaf controls. At every size from 2 to 64 frames, reports covered exactly all frame owners for birth and deletion; event settlement matched full-closure projections, and all deliberately omitted leaves remained stale. All event queues settled without cap or deferred effects. Artifact and native-build fingerprints matched.

## Measured scale

Five fresh repetitions per size; medians shown. Times are milliseconds for one generated instance on the captured host. They are descriptive microbenchmarks, not commodity-hardware projections.

| Frames | Event queue ms | Full closure ms | Event/full | Event progress steps | Full progress steps | Scoped report turns |
|---:|---:|---:|---:|---:|---:|---:|
| 2 | 0.152 | 0.083 | 1.83× | 5 | 5 | 8 |
| 4 | 0.253 | 0.104 | 2.43× | 11 | 5 | 16 |
| 8 | 0.521 | 0.161 | 3.23× | 23 | 5 | 32 |
| 16 | 1.204 | 0.238 | 5.06× | 47 | 5 | 64 |
| 32 | 3.069 | 0.390 | 7.88× | 95 | 5 | 128 |
| 64 | 9.445 | 0.724 | 13.05× | 191 | 5 | 256 |

The event queue was semantically exact but slower at every tested size. From 2 to 64 frames, its median time rose about 62× and its scoped report turns rose 32×; full-closure median time rose about 8.7×. This generated fanout workload exposes repeated per-frame settlement/report overhead: correct owner routing alone does not make partitioned execution cheaper. Progress-step counts are engine report counters, not a complete measure of candidate enumeration or CPU instructions.

## Interpretation and next gate

This is an intentionally high-fanout star, and the graph is tiny (at most 129 nodes plus ownership/dependency edges). It cannot establish natural workload cost, cache behavior, or an asymptotic bound. It does falsify any blanket inference that scoped event scheduling wins merely because frame notifications are complete. The next scaling work should contrast sparse/local, bounded-separator, and high-fanout topologies at matched node/rule counts, with candidate/evaluation counters and repeated timing. Then validate partitions generated from the structural census rather than hand-authored ownership.

## Reproduction

```sh
PYTHONPATH=runners/dsl/python:. python3 scripts/substrate_scoped_notification_fanout_scale_v1.py
python3 scripts/analyze_substrate_scoped_notification_fanout_scale_v1.py
```
