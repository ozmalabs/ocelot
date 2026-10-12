# Discourse goal/action association guard diagnostic v3

**Question:** does a minimal shared-addressee guard on native goal lifecycle rules restore the authored two-goal event assignment, and does the candidate preserve exact owner-queue closure on the same connected workload?

**Exploratory disclosure:** an unlocked one-process feasibility check found that adding matching `goal -> for_addressee -> recipient` and `event -> to_addressee -> recipient` pattern edges to the select/execute/resolve rules yields the fixture's intended sequences. This is discovery evidence only. The present locked capture is the confirmatory mechanism comparison for this one fixture, not a claim that addressee equality is the correct general goal-identity policy.

## Frozen input and arms

Use `phase3_common_ground_stress.v1`, incrementally materialized as in the v2 owner-wakeup probe, with four caller-declared event-phase frames. Fresh-process arms:

1. **Baseline full:** current seed lifecycle rules, global closure after each event.
2. **Guarded full:** tombstone the three current lifecycle rules, install copies with two additional match edges: `goal -> for_addressee -> recipient` and `event -> to_addressee -> recipient`, then run global closure after each event.
3. **Guarded owner queue:** same guarded rules; seed the current event frame and follow reported `affected_microtheories` until quiescent.
4. **Guarded omitted wakeup:** same guarded rules; seed only the current event frame and ignore remote owners, then perform one global closure after the final checkpoint.

Per checkpoint record exact graph digest, goal state and transition-event provenance, origin receipt state, common-ground state, closure/queue reports, candidate/term counters, wall/CPU time, and peak RSS. Full closure is the scheduling oracle. Fixture task oracles are origin 0 transitions `[4,5,6]` and origin 3 transitions `[7,8,9]`. The guarded full and owner arms must meet these; baseline is expected to reproduce the previously measured temporal-only misassociation. Guarded owner must equal guarded full at every checkpoint. Omission must leave receipts stale at their remote result checkpoint and final global recovery must restore exact parity.

## Interpretation limits

Addressee equality is only a candidate association key; it may be ambiguous when one addressee has concurrent goals. This is not a production rule change, a general task-identity solution, or a scheduler performance estimate. Preserve cost and semantic results separately. One authored fixture cannot establish general goal semantics or conversation locality.

## Amendment 1 — result-event checkpoint mapping

The initial runner gate incorrectly required notifications to both origin frames at event 6. The frozen candidate task assignment has goal 0 resolve at event 6 and goal 3 resolve at event 9. Preserve the initial failed raw capture as a harness-gate failure; correct only the expected frame/event pairs to `(0,6)` and `(1,9)`, and require each corresponding omitted-wakeup receipt to be stale at its own result checkpoint. Inputs, arms, candidate rule, and task oracle are unchanged. The corrected runner source and regenerated lock identify the amended capture.
