# Explicit goal-link association scale probe v4

**Question:** does explicit operation-event-to-Goal identity preserve independent same-addressee goal lifecycles under native closure, and can the caller owner queue preserve that state as concurrent task count increases?

## Frozen workload

Use `phase3_same_addressee_concurrent_goals_scale.v1` at 2, 4, and 8 goals. Create all origin request events and Goals first. Then, for each goal in order, create one `selection`, one `execution`, and one `action_result` event. All Goals share one addressee. Every operation event carries an explicit `for_goal` edge to its intended Goal. Its event-phase owner frame differs from the goal-origin frame. Create one Microtheory per origin and one per operation sequence; the shared discourse state, recipient, and event history are boundary nodes.

For Goal i at goal count N, the intended transition-event indices are `[N+3*i, N+3*i+1, N+3*i+2]` (zero-based event indices). Every origin receipt starts at 0 and becomes 1 after the linked goal resolves.

## Arms

Run one fresh process per arm and size (15 workers total):

1. **Temporal-only full:** current seed lifecycle rules; global closure after each event.
2. **Recipient-guarded full:** benchmark-only copies of the lifecycle rules require matching goal/event addressee; all recipients are shared.
3. **Explicit-link full:** benchmark-only copies require an `event -> for_goal -> goal` pattern edge.
4. **Explicit-link owner queue:** same rules; seed the newly inserted frame and process native affected-owner notifications to queue quiescence.
5. **Explicit-link omitted wakeup:** same rules; ignore remote owner notifications, then run full closure once after the final checkpoint.

Compare exact graph digests at every checkpoint for explicit-link owner queue against explicit-link full. The explicit-link full and owner arms must match the expected transition/receipt oracle. Temporal and recipient guards are diagnostic controls; the recipient guard is expected not to disambiguate tasks. Omission must become stale after remote goal updates and final global closure must restore exact graph parity. Record progress, candidates, Terms, scoped turns, notifications, wall/CPU, setup, and peak RSS. Timings are descriptive across this small scale sweep.

## Candidate identity contract and limits

The `for_goal` edge is benchmark-supplied task identity, not a claim that current production event producers emit it. The candidate only tests whether the native rewrite engine can consume explicit identity without losing scoped parity. Same-addressee ambiguity is deliberately held constant. Three sizes and one generated task family do not establish asymptotic complexity, natural conversation frequency, production integration, or a general task representation.

## Exploratory disclosure

The prior v3 probe tested a shared-addressee guard on two different recipients; it did not test explicit goal-link matching or the same-addressee case. This v4 identity mechanism and scale workload are preregistered before execution.
