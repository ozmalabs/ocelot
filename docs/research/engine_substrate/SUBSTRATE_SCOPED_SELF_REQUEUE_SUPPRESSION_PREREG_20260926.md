# Scoped self-requeue suppression preregistration (2026-09-26)

## Question

Can event-driven scoped settlement avoid a redundant self-requeue after a
scoped call has already saturated that owner's current rule set, without
missing work when the call changes the owner's one-hop `has_concept` set?

## Intervention

Compare the verified notification queue with an experimental queue policy that
retains every reported notification except a notification to the current owner
when the exact owner set is identical immediately before and after the scoped
call. Define owner set as the owner Microtheory plus its direct
`has_concept` neighbors, matching `mt_owned_nodes`. If the owner disappears,
changes type, or the owned-node set changes, preserve the self-requeue. Do not
alter native matching, rule ordering, graph writes, remote notifications, or
full-closure execution. Record reported notifications separately from enqueues
so this is suppression of a queue action, not falsification of the observer.

## Workloads and controls

Replay chain, binary-tree, and star fixtures at 8/16/32/64 frames with five
paired repetitions, comparing current baseline raw evidence to the intervention
on the same source/build. Keep both birth and deletion phases and all prior
fallback controls. Add two focused controls: (1) an owner-stable local state
update must suppress the self-enqueue while preserving every other notification;
(2) an ownership-changing rule that inserts a `has_concept` edge during local
execution must retain the self-enqueue, allow the newly owned node to be
processed, and reach the full-closure oracle.

Supplemental delayed-writer adversary: frame A's first scoped turn enables a
B-local rule; B's turn then writes to A after A has left the queue. Suppression
must still enqueue A from B's later non-self notification, yielding turn order
A→B→A and exact parity with baseline and monolithic closure. This specifically
checks that self suppression is not a permanent dirty-frame suppression.

## Gates

1. Baseline capture, preregistration, runner, native extension, Rust source,
   and build fingerprints are current and explicitly recorded.
2. In every scale repetition, owner sets are snapshotted from actual graph
   membership before and after each scoped invocation.
3. The intervention suppresses a self enqueue iff the owner survives and the
   one-hop ownership set is unchanged; no other notification is omitted.
4. Both phases settle within the existing cap with no deferred effects and
   exact full-closure projection parity; cross-owner notifications are
   identical to baseline.
5. The ownership-changing control requeues and processes the new member;
   stable control suppresses only the expected redundant requeue.
6. In the delayed-writer control, the suppressed run visits A→B→A and its
   final projection matches both baseline scoped settlement and monolithic
   closure.
7. Independent analysis recomputes notification, enqueue, suppression,
   candidate, and term counts from per-turn records and verifies source hashes.
8. Report effect on turns/candidate and term work, and paired repeated timing.
   A speedup is not assumed; regressions or parity failures are retained.

## Interpretation limits

This is an opt-in Python queue-policy experiment over synthetic fixtures. It
does not authorize default scheduler changes, prove useful natural-task
locality, or justify notification coalescing across owners. Passing establishes
only this guarded self-requeue policy on the tested rule/ownership envelope.

## Outputs

Raw: `evaluation/reports/substrate_scoped_self_requeue_suppression_v1_20260926.json`.
Independent analysis: same basename with `_analysis.json`. Runner and analyzer:
`scripts/substrate_scoped_self_requeue_suppression_v1.py` and
`scripts/analyze_substrate_scoped_self_requeue_suppression_v1.py`.
