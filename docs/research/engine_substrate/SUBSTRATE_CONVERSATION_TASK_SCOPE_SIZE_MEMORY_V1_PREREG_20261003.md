# Conversation scoped-matcher size and memory v1 preregistration

Date: 2026-10-03  
Status: preregistered before implementation and capture.  
Prior evidence: [degree-skew/partial-decoy v2.2](SUBSTRATE_CONVERSATION_TASK_SCOPE_DEGREE_SELECTIVITY_V2_2_RESULTS_20261003.md)

## Question

How do graph size, peak process memory, wall time, and native matcher work scale as irrelevant high-degree shared-Event decoys increase, and does declared-anchor matching retain exact semantics against verified full fallback and monolithic closure?

## Locked workload

Use the v2.2 `concurrent_goals`, two-goal panel and its `shared_event_complete` decoy constructor. Each decoy adds one lifecycle-ineligible Goal, linked to the single shared decoy Event; all decoys share that Event, with one state-to-event edge. Sweep decoy counts 0, 256, 1,024, 4,096, and 16,384. Keep task events, goals, rule set, ownership, closure schedule, and decoy construction otherwise fixed. Run each size in nine fresh processes: three scope orders (ascending, descending, outside-in) crossed with three replicates. Each worker runs one size only, preventing prior size cases from accumulating into the memory high-water mark.

The four arms are monolithic, declared-anchor, verified full fallback (anchor metadata removed from both loader and boot-core lookup), and traced declared-anchor. The trace arm is retained to preserve the existing instrumentation audit but is excluded from primary wall-time and memory scaling conclusions because tracing adds overhead. Capture per checkpoint node/edge count, candidate pairs, term evaluations, wall time, closure status, final/checkpoint graph digests, and process maximum resident set size. Record hardware/runtime/source identities and the exact constructed graph profile.

## Gates and analysis

- Source lock matches pre/post execution; all 45 workers have unique PIDs and the locked size/order/replicate assignment.
- Require exact checkpoint and final graph equality for monolithic, anchor, fallback, and anchor-trace arms, plus equal lifecycle statuses and fixed-point closure.
- Verify fallback uses full matcher calls and has zero declared-anchor attempts and proof rejections; require anchor path exercised at every nonzero/zero aligned size.
- Independently reconstruct case coverage and sum per-checkpoint native work and graph dimensions. Report Candidate/Term counts and ratios to monolithic and fallback; do not hide nonmonotonicity.
- Report process `ru_maxrss` as a process high-water measurement for one size worker. It includes interpreter, graph construction, retained capture data, and instrumentation; it is not a per-arm allocation measurement. Report wall time as descriptive and keep traced runs out of primary timing comparisons.
- Treat this authored panel as controlled synthetic scaling only. It cannot establish natural degree distributions, learned frame validity, or general tractability. If the largest cell exceeds the worker timeout or memory budget, preserve the failure and report the reached boundary; do not silently reduce the schedule.
