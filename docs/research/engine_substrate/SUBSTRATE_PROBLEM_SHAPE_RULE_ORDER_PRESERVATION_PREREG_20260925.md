# ProblemShape eventization with original rule positions preserved

**Status:** preregistered order-confound experiment.

## Hypothesis

The event/index treatment replaces the five original ProblemShape rules by tombstoning them and appending variants at the end of the rule vector. The default runner evaluates dirty rules in insertion order. The all-rule audit shows unchanged enumeration counts but increased candidate expansions in six unrelated rules. Hypothesis: moving ProblemShape rules later in the schedule changes intermediate graph visibility and contributes to those expansions.

## Design

At N=32, compare ordinary baseline closure with the same event/index rule bodies loaded into the original five ProblemShape seed slots. Preserve the production-install time and observation workload. Use six fresh-process pairs each for recognition-only and recurrent-residual (24 workers), with three baseline-first and three candidate-first per workload and a fixed shuffled schedule. The candidate seed corpus differs only in those five rule bodies; new rules stay in the original list positions. Assert the five active ProblemShape rule indices are identical to baseline, worker fixed points and expected statuses/mint outcomes pass, and paired per-step transitions match.

Preserve complete per-step all-rule counters, global work totals, timing, RSS, worker PIDs, and order. Compare per-rule candidate pairs and Terms against baseline and the previous appended-rule eventization result. No change to the default runtime or seed corpus is made.

The lock pins this protocol, runner, candidate seed transformer, worker helpers, full seed-manifest corpus digest, task sources, native extension/build manifest, Cargo lock, and prior appended-rule result used as context.

## Interpretation

If the additional candidate-pair work disappears with positions preserved, the result supports rule movement as a contributor (not necessarily the only cause). If it persists, inspect relation populations and matcher join state next. Timing remains exploratory; six pairs per mix cannot establish small runtime effects. Exact task equivalence and complete per-rule counts are required before comparing work.
