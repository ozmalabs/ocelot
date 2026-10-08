# Vision global-fold versus scoped-fold work scaling preregistration

Date: 2026-09-25. Benchmark-only variants; authored seed and production code remain unchanged.

## Question
How does measured native settlement work scale with the number of units when the authored global `NodesOfType(SUnit)` fold is retained, compared with a mathematically equivalent `Neighbours(Retina, has_sunit)` fold on one Retina-owned sheet?

## Workload and procedure
Build lateral-free degenerate sheets with connectivity 8 at side lengths 2, 4, 8, and 16 (N=4, 16, 64, 256). Use three fixed seeds per size: 4101, 7301, and 10703. For each seed/size, create fresh global and Retina-scoped arms, counterbalanced in execution order by seed index. Install an identical deterministic random afferent vector and reset `act`/`act_next` identically. Keep only the selected `st_settle` rule and `st_commit`; invoke native `run_rules` with a fixed 1,024 application budget. Collect progress applications, wall time, terminal activations, equation residual, node/edge counts, and provenance. The measured region excludes graph construction and initialization.

The benchmark is a truncated-work envelope: a budget exit is not convergence. Report per-size medians and every raw replicate; do not extrapolate an asymptotic class from four sizes. The primary work comparison is native progress applications and elapsed time for paired equivalent states. Require paired shape and progress parity. Compare terminal arrays with exact equality and an independently recomputed equation residual; if floating-point order causes a difference, retain and quantify it.

## Limits
The two variants differ only in source population for the `st_settle` global mean; this is not a comparison of a production frame scheduler. It measures one authored vision rule, not natural-task locality prevalence, full inference, learning, or task quality. Three seeds are repeated initializations of the same generated workload family, not independent ecological samples. A fixed application cap bounds runtime and does not show fixed-point behavior.
