# Conversation scoped owner-wakeup and boundary fallback probe

**Question:** can the existing native Microtheory-scoped settlement and write-owner report preserve an incrementally growing, connected conversation graph when task frames are assigned by event phase? Does it wake a downstream consumer in a different owner frame after a goal lifecycle write?

**Grade:** new authored-task diagnostic. The ten-event fixture was used in prior mechanism tests; this experiment adds a frozen four-frame operational partition and one native consumer rule as an explicit downstream sentinel. It is not a representative-task estimate, learned partition, production scheduler, or general GALS result.

## Frozen frame and consumer definition

Assign frame 0 to request event 0 and its Goal; frame 1 to selection/execution/result events 1–3; frame 2 to unsolicited assertion 4, question 5, and its Goal; frame 3 to selection/execution/result/epistemic-limit events 6–9. Add one Microtheory owner per frame and `has_concept` membership for each owned event and goal. The DiscourseState, CommonGround nodes, speakers, and other nodes remain shared boundary nodes.

Install a native sentinel rule matching `Goal -> originated_in -> DiscourseEvent`; when a Goal's lifecycle is `resolved` and the origin's `resolution_receipt` is 0, set the origin receipt to 1. Initialize the receipt to 0 on origin events. The rule therefore has a binding wholly owned by the origin frame and must run after a lifecycle change in a different event frame. The ordinary discourse goal rules remain unchanged.

## Arms

Run three fresh processes with identical incremental graph construction and task inputs:

1. **Full:** after each event, run ordinary global closure to fixed point.
2. **Owner queue:** seed the newly inserted event's frame; run `run_rules_scoped_delta_report`; enqueue other frame owners returned by its native write report until the queue is empty.
3. **Omitted owner wakeup:** seed only the new event's frame and ignore reported remote owners; after the final checkpoint, run ordinary global closure once as an explicit recovery.

Keep the full arm as oracle. At every event checkpoint compare exact graph digest, goal transitions, common-ground state, and receipts. Record frame setup, host event insertion, scope calls, native writes/owners, queue operations, progress/candidate/Term counters, wall/CPU time, and peak RSS. The omitted arm must become observably stale after a remote lifecycle write and the final full recovery must restore exact parity.

## Stop conditions and limits

Any incomplete scoped report, budget exit, deferred effect, unmapped owner ID, semantic mismatch in the owner-queue arm, or missing omission/recovery effect fails its corresponding gate. The external frame-to-Microtheory construction and queue are caller-side; this tests a route built from existing native APIs and not an automatic engine scheduler. Costs are for one task and must include frame annotation and queue work. Do not generalize timing or frame locality from this fixture.
