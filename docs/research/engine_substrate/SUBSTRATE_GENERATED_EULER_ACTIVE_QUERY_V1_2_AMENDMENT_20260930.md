# Generated Euler Active Query v1.2 Amendment

The v1.1 measurement found that iterative entropy reduced oracle calls but its repeated native term evaluations cost about ten times more local decision compute than fixed order. Version 1.2 adds an immutable `QueryRankingIndex` that evaluates each hypothesis/query pair once and reuses cached values for successive entropy ranks and filtering.

The anchors, candidate family, holdouts, grammar, seeds, oracle, and stopping rule remain identical to v1.1. The new comparison includes both the uncached entropy baseline and cached entropy. The cache's one-time construction wall/CPU cost, matrix prediction count, approximate retained Python heap size, per-round cache reads, and end-to-end decision-plus-oracle cost are recorded. The cache is treated as task-local state; its build cost is charged to the cached policy. No v1 or v1.1 capture is overwritten.
