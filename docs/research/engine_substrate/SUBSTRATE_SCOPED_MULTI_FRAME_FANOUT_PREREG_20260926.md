# Scoped multi-frame fanout diagnostic preregistration

**Lock date:** 2026-09-26, before execution. **Question:** does native owner notification and event-queue settlement remain complete as one minted node depends on increasing numbers of independently owned frames?

## Fixed design

For fanout `k ∈ {2,4,8,16}`, construct one source frame A and k target frames, each with one stateful Concept. A one-shot A rule mints one bridge and adds a distinct influence edge to each target Concept. A local target rule sets state to 1 iff an incoming influence exists. A deletion request causes A to delete the bridge; node deletion removes all k influence edges. Run the native notification queue and monolithic full-closure oracle on fresh identical fixtures.

Gates per k: exact notification owner set `{A,T1…Tk}` at birth and deletion; event queue termination without cap/deferred effects; exact projected parity with full closure at both stages; fixed-point full-closure reports; all k dependencies present after birth and absent after deletion. For each target owner, separately suppress that owner's birth notification and require the event projection to diverge from the oracle. Omission cases are sensitivity controls, not scheduler-failure claims.

Record source/native hashes, work counters, queue turns and latency descriptively. This bounded synthetic sweep does not establish arbitrary effect correctness, partition discovery, natural-task prevalence, or asymptotic complexity.

## Reproduction

```sh
PYTHONPATH=runners/dsl/python:. python3 scripts/substrate_scoped_multi_frame_fanout_probe_v1.py
```
