# Conversation task-scope parity pilot v1 method

Date: 2026-10-03
Status: exploratory native-engine parity pilot; not a partition-safety or speedup result.

## Question

Can the current Microtheory-scoped rule runner reproduce monolithic closure on a small connected-conversation workload if task event/goal ownership is made explicit and every frame is conservatively reswept?

## Design

The runner reuses the v1.3 connected-conversation builder for the authored `concurrent_goals` case with two concurrent goals. It executes three fresh worker processes. Within each worker it builds separate fresh worlds for the monolithic and scoped arms. Each world gets two task roots from the loaded conversation seed. As each task event and goal appears, the runner adds a `has_concept` membership edge from its task root in both arms before closure. The same annotations therefore occur in the paired initial states; the monolithic arm simply ignores scope during closure.

The scoped arm calls `run_rules_scoped` for both roots in a complete sweep and repeats sweeps until both scopes report zero progress. It then calls `run_rules_scoped_delta_report` on each root at quiescence; any additional progress or pending deferred effect fails the run. Repeating all scopes is a conservative global notification policy, not an optimized dirty-frame scheduler. The runner compares every checkpoint graph digest, the final graph digest, and goal statuses. It source-locks the runner, independent analyzer, v1.3 task builder, discourse materializer, seed, fixtures, native binary/build manifest, and relevant Rust sources.

The per-frame membership annotations are inserted with the unchecked edge primitive because the current conversation seed does not admit task-specific Microtheory ownership edges through ordinary vocabulary validation. Both arms receive identical annotations. This is an experimental ownership encoding and a relevant integration gap; it is not a production frame-discovery path.

## Admission and claim boundary

Admit only if three distinct worker PIDs run under stable locked inputs; all three final graph digests match between arms; all checkpoint digests and goal statuses match; all closures reach fixed point; every scope has no deferred work and no progress during its quiescence check; and an independent analyzer reproduces the comparisons. Any mismatch or unresolved queue makes the pilot fail or inconclusive.

This pilot measures one authored two-frame family, with one goal count, on one host. It does not test common-ground stress, four/eight-frame cases, arbitrary hyperedge boundaries, frame discovery, dynamic ownership changes, scope notification completeness in general, or natural-task prevalence. The full-graph matcher still runs for each scope call; the pilot does not demonstrate computational factorization. Timing is descriptive and includes many scoped calls plus mutation-report checks, so the result is not a fair speed comparison.

## Reproduction

```sh
python3 evaluation/substrate_capability/conversation_task_scope_parity_pilot_v1.py --lock
python3 evaluation/substrate_capability/conversation_task_scope_parity_pilot_v1.py
python3 evaluation/substrate_capability/analyze_conversation_task_scope_parity_pilot_v1.py
```

The original source-stability-check failure is preserved at [`failure capture`](../../../evaluation/reports/conversation_task_scope_parity_pilot_v1_source_stability_failure_20261003.json); see the [results](SUBSTRATE_CONVERSATION_TASK_SCOPE_PARITY_PILOT_V1_RESULTS_20261003.md) for its correction and final outcome.

V1.1 adds independently analyzed per-scope quiescence records without changing the workload or sweep policy. Reproduce that confirmation with:

```sh
python3 evaluation/substrate_capability/conversation_task_scope_parity_pilot_v1_1.py --lock
python3 evaluation/substrate_capability/conversation_task_scope_parity_pilot_v1_1.py
python3 evaluation/substrate_capability/analyze_conversation_task_scope_parity_pilot_v1_1.py
```

See the [v1.1 amendment](SUBSTRATE_CONVERSATION_TASK_SCOPE_PARITY_PILOT_V1_1_AMENDMENT_20261003.md).

V1.2 extends the case matrix to 2/4/8 concurrent goals and the four-frame common-ground stress scenario. It creates one Microtheory node per task frame and records the exact quiescence report for every frame at every checkpoint. Reproduce that exploratory extension with:

```sh
python3 evaluation/substrate_capability/conversation_task_scope_parity_pilot_v1_2.py --lock
python3 evaluation/substrate_capability/conversation_task_scope_parity_pilot_v1_2.py
python3 evaluation/substrate_capability/analyze_conversation_task_scope_parity_pilot_v1_2.py
```

The capture's free-text claim boundary has a three-frame wording error; the actual locked design contains 2-, 4-, and 8-frame concurrent-goal cases plus a 4-frame common-ground stress case. See the [v1.2 amendment](SUBSTRATE_CONVERSATION_TASK_SCOPE_PARITY_PILOT_V1_2_AMENDMENT_20261003.md) and [results](SUBSTRATE_CONVERSATION_TASK_SCOPE_PARITY_PILOT_V1_2_RESULTS_20261003.md).

V1.5 repeats the four-case matrix under three scope visitation orders, with three fresh workers per order. The monolithic arm remains the exact closure reference; the scoped arm changes only the order in which all task scopes are swept. Reproduce with:

```sh
python3 evaluation/substrate_capability/conversation_task_scope_parity_pilot_v1_5.py --lock
python3 evaluation/substrate_capability/conversation_task_scope_parity_pilot_v1_5.py
python3 evaluation/substrate_capability/analyze_conversation_task_scope_parity_pilot_v1_5.py
```

The [v1.5 results](SUBSTRATE_CONVERSATION_TASK_SCOPE_ORDER_PARITY_V1_5_RESULTS_20261003.md) report state parity and work separately for each visitation order.
