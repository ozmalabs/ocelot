# Scoped notification fanout scale preregistration

**Lock date:** 2026-09-26, before scale captures.  
**Question:** As the number of frames depending on one newly minted node grows, do scoped mutation reports continue to notify every dependent owner, does event-queue settlement preserve full closure, and how do observed work and latency scale over this generated workload?

## Workload and locked sizes

For each frame count `N ∈ {2,4,8,16,32,64}`, create N Microtheories, each owning one Concept. Frame A has a one-shot trigger; each remaining frame has state 0 and `linked=false`. A-scoped rules mint one A-owned node, connect it by a `causal_influence` edge to each non-A frame's Concept, and consume the trigger. Owner-local rules set each target state to 1 while its influence edge exists and back to 0 after deletion. The deletion intervention sets a request on the minted node; an A-scoped rule deletes it, removing all incident cross-frame edges. The event queue starts each external intervention at A and thereafter enqueues every reported owner. An omission control drops the highest-ID non-A owner notification during birth settlement.

Run five fresh paired repetitions per size for full native closure and event-queue settlement, plus five omission controls per size. Lock the native artifact and source fingerprints in raw evidence. Record operation progress steps, scoped report turns, enqueues, elapsed wall time, fixed-point/cap/deferred status, exact owner sets, target state vectors, minted-node/edge projections, and per-arm hashes. Timing is descriptive; no timing superiority is required.

## Required gates

1. Across reports from each event birth settlement, the union of affected owners is exactly all N Microtheories, and the same holds for deletion.
2. Each event arm reaches an empty queue without a progress cap or deferred work.
3. Birth and deletion projections match full closure exactly in every repeat at every N.
4. Full closure reports fixed points after both interventions.
5. Each omitted-notification control leaves its deliberately omitted target stale and differs from the full birth projection.
6. Source, protocol, build, and native artifact fingerprints are internally consistent.

## Claim boundary

This is a generated star-fanout workload with one concept per frame, not a natural task distribution or arbitrary graph topology. It measures owner-notification/queue behavior as fanout grows; it does not prove general tractability, scheduler completeness, sparse-cut prevalence, or a speed advantage over full closure. The one omitted-owner ablation tests sensitivity at one deterministic leaf per scale.

## Reproduction

```sh
PYTHONPATH=runners/dsl/python:. python3 scripts/substrate_scoped_notification_fanout_scale_v1.py
python3 scripts/analyze_substrate_scoped_notification_fanout_scale_v1.py
```
