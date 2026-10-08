# Scoped notification and requeue attribution results

**Protocol:** [`SUBSTRATE_SCOPED_NOTIFICATION_REQUEUE_ATTRIBUTION_PREREG_20260926.md`](SUBSTRATE_SCOPED_NOTIFICATION_REQUEUE_ATTRIBUTION_PREREG_20260926.md)  
**Raw capture:** [`substrate_scoped_notification_requeue_attribution_v1_20260926.json`](../../../evaluation/reports/substrate_scoped_notification_requeue_attribution_v1_20260926.json)  
**Independent analysis:** [`substrate_scoped_notification_requeue_attribution_v1_20260926_analysis.json`](../../../evaluation/reports/substrate_scoped_notification_requeue_attribution_v1_20260926_analysis.json)  
**Runner / analyzer:** [`substrate_scoped_notification_requeue_attribution_v1.py`](../../../scripts/substrate_scoped_notification_requeue_attribution_v1.py), [`analyze_substrate_scoped_notification_requeue_attribution_v1.py`](../../../scripts/analyze_substrate_scoped_notification_requeue_attribution_v1.py)

## Gate result

The independent analyzer passes all source/build fingerprints, all runner
aggregates against raw turn records, and all semantic gates in the preregistered
chain, binary-tree, and star matrix (8/16/32/64 frames; five repetitions;
birth and deletion phases). Event settlement matches full-closure projection;
there are no cap hits or deferred effects. Focused controls also confirm that
multi-edge and deleted-edge cases use their declared fallback and that
order-sensitive scoped matching agrees with the fallback oracle.

## Attribution

| Topology, 64 frames | Median turns | No-progress turns | Self-requeues | Duplicate suppressions | Candidate tests | Term evaluations | Max queue depth |
|---|---:|---:|---:|---:|---:|---:|---:|
| Chain | 256 | 128 | 128 | 0 | 2,591 | 18,515 | 2 |
| Binary tree | 256 | 128 | 128 | 0 | 2,774 | 19,918 | 48 |
| Star | 256 | 128 | 128 | 0 | 14,123 | 106,927 | 64 |

Across each topology/size cell, median no-progress turns equal self-requeues,
and duplicate suppression is zero. Notifications per turn approach one as
frame count grows (0.992 at 64 frames); the notification queue itself is not
spending these runs on duplicate suppression. The star has about 5.45x the
candidate tests and 5.78x the term evaluations of the chain at 64 frames,
while the tree remains close to the chain. This localizes the observed cost to
the repeated owner-turn/matching work plus high-fanout star topology, rather
than duplicate enqueues. It does not establish which batching or scheduling
change would preserve semantics.

## Interpretation and next experiment

This generated fixture attributes current scheduler work; it is not evidence
that authored or natural task frames have these topologies. The next
optimization must be an explicit intervention against the repeat owner-turn
and star-fanout work, preregistered with exact event/full state parity,
notification and ordering checks, and the current fallback controls. Do not
infer batching safety from this attribution alone.

## Reproduction

```sh
PYTHONPATH=runners/dsl/python:. python3 scripts/substrate_scoped_notification_requeue_attribution_v1.py
python3 scripts/analyze_substrate_scoped_notification_requeue_attribution_v1.py
```
