# ProblemShape eventization global rule attribution

**Status:** preregistered exploratory repeated paired evaluation.

## Question

At N=32, which native rules and global scale-audit counters change when all-transition eventization is enabled, on recognition-only and recurrent-residual observation streams? Do the per-rule work counts remain stable across fresh paired processes?

## Design

Run six baseline/candidate fresh-process pairs per workload (12 pairs, 24 unique processes): `recognition` and `recurrent_residual`, N=32, dynamic codebook. Balance order independently within each workload (three baseline-first and three candidate-first) and shuffle with a fixed RNG seed. Every worker must pass its built-in fixed-point/status/mint checks. Paired initial/final statuses and per-step mint deltas must match.

The worker readbacks preserve full per-rule scale-audit rows as well as existing ProblemShape-filtered counters and global totals. Aggregate `candidate_pairs`, `term_evaluations`, and other reported native audit metrics by rule. Report global audit totals separately from ProblemShape-only totals. Record paired observation timing, all worker records, PIDs, boot, RSS, and execution order. No result changes the default path.

The lock pins this protocol, runner, baseline/candidate workers and attribution helpers, baseline data, task sources/seeds, native extension/build manifest, and Cargo lock. Require current engine provenance before execution.

## Interpretation limits

This measures two authored workloads at one size, not natural task prevalence or substrate-wide performance. Repeated processes estimate operational variability but do not establish asymptotic complexity. Per-rule audit counts attribute counted evaluator operations, not all runtime cost. Timing is exploratory. Any mismatch invalidates paired comparisons for that pair.
