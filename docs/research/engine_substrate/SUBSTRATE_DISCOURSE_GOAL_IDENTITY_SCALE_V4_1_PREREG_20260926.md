# Explicit goal-link scale extension v4.1

**Question:** do task-oracle parity and exact owner-notification closure persist when the same explicit-goal identity workload grows from 8 to 64 concurrent goals, and how do operation counts scale?

## Frozen workload

This is a separately locked scale extension of v4, not a replacement for its 2/4/8 capture. Use `phase3_same_addressee_concurrent_goals_scale.v1.1` at N=16, 32, and 64. Preserve the construction and `for_goal` annotations exactly: create all same-addressee origins/goals first, then three task-linked events per goal; goal i's expected transition indices are `[N+3*i,N+3*i+1,N+3*i+2]`. Use one origin frame and one operation frame per goal.

## Arms

Run five arms per size, 15 fresh processes total: temporal-only full closure; recipient-only guarded full closure; explicit-link guarded full closure; explicit-link owner queue following affected owners; and explicit-link omitted-owner control with final full recovery. Use the same source code and rule transformations as v4, except for the preregistered size input. Do not change native rules.

For each size require: all global arms reach fixed points; temporal and recipient-only controls fail the task oracle; explicit full and explicit owner queue match the exact task oracle; owner queue graph digests match full closure at every checkpoint; all origin owners receive remote result notifications; omitted owner wakeups produce stale receipts; recovery restores exact graph state; scoped calls have no budget/deferred exit. Record candidate pairs, Terms, progress, queue turns, wall/CPU time, frame setup, and peak RSS by arm. Independently recompute counters and semantic gates. Timings are descriptive single runs.

## Interpretation limits

This extension measures a generated same-addressee task family and harness-provided identity edges. It is not an independent task family, production identity protocol, empirical natural workload, formal complexity proof, or useful-scale capability claim. Interpret RSS with the interpreter/native import floor in view. No extrapolation beyond N=64.

## Amendment policy

Keep N=16/32/64 fixed. Preserve any failing worker or gate output and correct only a verified harness defect under a dated amendment. Do not tune limits or semantics after inspecting outcome data.
