# Interleaved two-goal conversation owner-wakeup probe v2

**Question:** does native affected-Microtheory reporting preserve incremental full-closure state when a connected discourse has multiple origin frames, multiple interlocutors, and an interleaved observation/assertion sequence?

**Fixture:** `phase3_common_ground_stress.v1`, ten events. Assign four caller-declared operational frames: frame 0 owns origin request 0 and its Goal; frame 1 owns observation 1, assertion 2, origin request 3 and its Goal; frame 2 owns selections/execution/results 4–6; frame 3 owns operations 7–9. Shared discourse state, common-ground ledgers, and interlocutors remain boundary nodes. Each origin receives a downstream receipt sentinel rule, wholly matched within its owner frame.

## Arms and frozen outcomes

Run three fresh processes with identical incremental materialization:

1. **Full:** after each event, run global closure to fixed point.
2. **Owner queue:** seed the current event frame; run native scoped delta reports and enqueue all reported caller frames until the queue empties.
3. **Omitted owner wakeup:** seed only the current event frame and ignore reported remote owners; perform one final global closure as recovery.

Compare complete graph digests, goal states/provenance, origin receipts, and common-ground state at every checkpoint. The owner queue must match full closure throughout. Suppression is expected to leave origin receipts stale after the first result event (fixture event 6); final global recovery must restore exact graph parity. Record full reports, counters, wall/CPU time, and peak RSS. Any unmapped owner, budget/deferred exit, or parity mismatch fails its gate.

## Semantic boundary

The seed lifecycle rules transition goals based on event kind and temporal order. They do not match action/result events to a goal by addressee or task identity. The fixture's authored conversational intent therefore does not itself define the native transition oracle. This probe measures schedule parity against global closure and records the native rule's resulting goal provenance; it must not be described as demonstrating correct multi-goal action assignment.

## Limits

This is one authored fixture, a manual frame partition, and a caller-side queue. It does not estimate natural conversation locality, prove automatic scheduling, or claim a timing advantage. Preserve any semantic discrepancy between fixture intent and native full closure as a substrate capability gap rather than repairing it in the harness.
