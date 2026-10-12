# Scoped self-requeue suppression results

**Protocol:** [`SUBSTRATE_SCOPED_SELF_REQUEUE_SUPPRESSION_PREREG_20260926.md`](SUBSTRATE_SCOPED_SELF_REQUEUE_SUPPRESSION_PREREG_20260926.md)  
**Raw capture:** [`substrate_scoped_self_requeue_suppression_v1_20260926.json`](../../../evaluation/reports/substrate_scoped_self_requeue_suppression_v1_20260926.json)  
**Independent analysis:** [`substrate_scoped_self_requeue_suppression_v1_20260926_analysis.json`](../../../evaluation/reports/substrate_scoped_self_requeue_suppression_v1_20260926_analysis.json)  
**Runner / analyzer:** [`substrate_scoped_self_requeue_suppression_v1.py`](../../../scripts/substrate_scoped_self_requeue_suppression_v1.py), [`analyze_substrate_scoped_self_requeue_suppression_v1.py`](../../../scripts/analyze_substrate_scoped_self_requeue_suppression_v1.py)

## Gate result

All 60 paired topology/size/repeat cases pass source integrity, exact
full-closure projection parity, owner-notification preservation, no-cap/no-
deferred-work checks, and independent per-turn counter conservation. The
stable-owner rule suppresses only self-enqueues and preserves every non-self
notification. A separate actual membership-change control inserts a new
`has_concept` member, retains the self-requeue, processes the new member, and
matches the full-closure oracle.

A delayed-writer adversary also passes: A enables a B-local rule; B then writes
back to A after A's first turn. The guarded run visits A→B→A and matches both
baseline scoped settlement and monolithic closure. This shows the guard is
per-invocation: it does not suppress a later notification from another owner.

## Scale effect

Each value is the median per transition across five repeats; birth and deletion
phases are both included in the parity gates. The baseline is the
contemporaneous, independently revalidated attribution capture.

| Topology, 64 frames | Baseline turns | Guarded turns | Candidate tests, baseline → guarded | Term evaluations, baseline → guarded | Guarded/baseline time |
|---|---:|---:|---:|---:|---:|
| Chain | 128 | 64 | 1,295.5 → 915.5 | 9,257.5 → 6,597.5 | 0.62× |
| Binary tree | 128 | 64 | 1,387 → 1,007 | 9,959 → 7,299 | 0.62× |
| Star | 128 | 64 | 7,061.5 → 6,681.5 | 53,463.5 → 50,803.5 | 0.76× |

The policy removes one redundant confirmation turn per stable owner and
eliminates no-progress turns in this workload. Candidate/Term work falls by
about 29% on chain, 27% on tree, and 5% on star: high-fanout cost is mostly
non-self matching and is not fixed by this intervention. Timing is descriptive
for this synthetic host/workload; wall timings vary between captures even under exact work parity, so these
ratios are descriptive and work counters remain the stronger comparison.

## Interpretation and next gate

This validates a guarded queue policy only in the experiment harness, with
single-hop ownership snapshots and the tested rule families. It is not enabled
in the default native or daemon scheduler and does not demonstrate natural
frame locality. Next, verify whether an equivalent owner-saturation contract
exists in a real scoped caller; if so, preregister a call-site integration
behind an opt-in path with dynamic-boundary, deletion/reuse, deferred-effect,
ordering, and rollback controls. Otherwise keep the result as a measured
synthetic optimization and move on to the next Stage 0/1/2 open gate rather
than generalizing it.

## Reproduction

```sh
PYTHONPATH=runners/dsl/python:. python3 scripts/substrate_scoped_self_requeue_suppression_v1.py
python3 scripts/analyze_substrate_scoped_self_requeue_suppression_v1.py
```
