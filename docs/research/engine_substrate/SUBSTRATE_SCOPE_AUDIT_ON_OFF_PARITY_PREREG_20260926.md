# Scoped audit on/off semantic parity preregistration

**Lock date:** 2026-09-26, before capture.  
**Question:** Does the repaired global/per-rule scale audit change scoped or full-closure semantics, notification coverage, or fixed-point status on the N=64 topology propagation workload?

## Design

Reuse `substrate_frame_topology_matched_scale_v1.py`'s exact chain, binary-tree, and star fixtures at N=64 and its four rules. Run five fresh repetitions per topology in four arms: event queue audit-off/on and monolithic closure audit-off/on. Toggle only native `scale_audit_set_enabled`; per-rule mode remains disabled. Each arm starts from a fresh identical fixture, activates root state 1, settles and projects, resets root to 0, settles and projects. Alternate the four-arm order across repetitions. Keep mutation report generation enabled in both event arms.

Record complete state projections at both checkpoints, event owner sets, fixed-point/empty-queue status, global audit snapshots, wall/cpu durations, source/native/build hashes. Instrumented counters are expected to be zero when audit is off and nonzero when audit is on. Timing is descriptive.

## Gates

1. For each topology/repeat, event audit-on and audit-off projections match at both checkpoints; full audit-on/off projections also match.
2. Event and full projections match within each audit mode at both checkpoints.
3. Event queues settle and cover all changed owners; full arms reach fixed points, in both audit modes.
4. Audit-off counter snapshots are all zero; audit-on work counters are nonzero; per-rule mode is disabled.
5. Graph/rule counts and source/native/build hashes match the locked fixture/build.

## Claim boundary

This validates audit-mode state semantics on one fixed generated propagation family and three topologies at N=64. It is not a proof of instrumentation transparency for every Term/effect, and timing does not estimate general audit overhead.

## Reproduction

```sh
PYTHONPATH=runners/dsl/python:. python3 scripts/substrate_scope_audit_on_off_parity_v1.py
python3 scripts/analyze_substrate_scope_audit_on_off_parity_v1.py
```
