# Generated Euler Active Query v1.1 Amendment

The v1 run completed under its original lock and remains preserved. Review after capture found that it recorded query counts and internal prediction counts but did not time the oracle calls or all policy decision work. This makes the query-count comparison insufficient for a total-cost conclusion.

Version 1.1 repeats the same anchors, candidate pools, independent holdouts, grammar, query policies, random seeds, and stop rule. It adds wall and CPU timing for each oracle response, training-label oracle work, and complete per-round decision computation for each policy. The amendment does not change the hypothesis pool or selection rules. Both captures are retained; v1.1 is the cost-complete result used for timing comparisons.

The v1.1 runner, analyzer, lock, raw capture, and analysis are independently source-locked under the `substrate_generated_euler_active_query_v1_1_20260930` stem.
