# Scoped multi-frame dependency notification preregistration

**Lock date:** 2026-09-26, before the diagnostic capture.  
**Question:** When a scoped rule mints one owned node with dependencies into two other frames, do mutation reports notify all three owners, and does queue-driven settlement match monolithic closure through birth and deletion?

## Fixture

Create three Microtheories A, B, C, each with one owned Concept. A's Concept has a one-shot trigger. B and C each start with state 0. A rule mints one A-owned Concept, adds one `causal_influence` edge from it to B's Concept and another to C's Concept, and consumes A's trigger. B and C each have local up/down rules that set their state to 1 iff an incoming influence edge exists and otherwise return state to 0. A deletion-requested minted node is deleted through an A-scoped rule that matches its A ownership plus its dependency into B; native node deletion must also remove the dependency into C and notify C.

## Arms and fixed gates

Run fresh-substrate full-closure and native event-queue arms. Starting only with the externally changed A frame, the event queue processes scoped reports and queues every reported owner until quiescence. Also run an omitted-initial-seed control. Required gates: (1) birth reports the exact owner set `{A,B,C}`; (2) deletion reports the exact owner set `{A,B,C}`, including C whose incident edge is removed transitively by node deletion; (3) both queue stages settle without cap/deferred work; (4) both event projections match full closure for minted-node existence, ownership, both dependency edges, consumed trigger, and B/C states; (5) full arms report fixed points; (6) omitted initial seed fails to mint and diverges from the full birth projection. IDs are deterministic within each fresh instance. Timing and operation counters are descriptive only.

## Claim boundary

This is a three-frame controlled test of a node with two distinct cross-frame dependencies and deletion with multiple incident external edges. It does not establish arbitrary-degree notification completeness, dynamic frame-root deletion/repartitioning, host-side source discovery, general scheduler correctness, or natural-workload tractability.

## Reproduction

```sh
PYTHONPATH=runners/dsl/python:. python3 scripts/substrate_scoped_multi_frame_dependency_probe_v1.py
python3 scripts/analyze_substrate_scoped_multi_frame_dependency_probe_v1.py
```
