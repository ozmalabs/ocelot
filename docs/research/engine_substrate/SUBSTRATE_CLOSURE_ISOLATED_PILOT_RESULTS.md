# Isolated closure pilot and counter reconciliation

**Status:** exploratory instrumentation result; not a confirmatory benchmark or scaling claim.

## Method

The closure harness now starts one fresh Python process per topology/size instance. Native extension startup and graph construction are included in per-worker peak RSS, while the reported rule-run wall and CPU intervals exclude process launch and graph construction. The worker uses the same independent reachability oracle and one-step terminal probe as the structural pilot.

Raw manifest: [isolated pilot JSON](../../../evaluation/reports/substrate_closure_isolated_pilot_20260924.json). Prior structural results and scope: [structural pilot report](SUBSTRATE_CLOSURE_STRUCTURAL_PILOT_RESULTS.md).

## Semantic and counter results

All nine instances (path, banded DAG, complete DAG at n=6, 10, and 14) matched the oracle and settled. The following candidate-counter identities held in every instance:

- scan + local + hinted enumeration = total enumeration;
- first + repeat enumeration = total enumeration;
- tested candidates = enumerated candidates.

Candidate totals match the prior shared-process pilot: path 19/53/103, banded DAG 39/115/223, and complete DAG 55/285/819 at n=6/10/14. The new native rule-effect AddEdge-attempt counter reports path 10/36/78, banded DAG 21/77/165, and complete DAG 30/204/650. Every attempt count is at least the committed edge-growth delta; the excess on DAGs counts idempotent duplicate insertion attempts from multiple derivations.

## Resource observations

Per-worker peak RSS ranged from 25,559,040 to 26,148,864 bytes. This is a process high-water mark including interpreter, imports, native extension, and the small graph; at these sizes it is dominated by fixed process/runtime cost and is not a useful graph-memory slope. The worker isolation makes the metric instance-scoped, but larger graph sizes and baseline subtraction are still required to estimate incremental memory.

The measured rule-run wall times remain sub-millisecond for these tiny cases. They are not stable enough to support extrapolation.

## Instrumentation finding

For every instance, graph_writes was zero while the authoritative live edge delta was positive. Source inspection shows graph_writes is explicitly scoped to mutations via the Python boundary, so zero is expected for this native execution path; the function has PyO3 call sites. The native AddEdge attempt counter counts attempts rather than only committed inserts. Follow-up instrumentation now also covers native node insertion/deletion, attribute setting, DelEdge, and ReplaceValue mutation arms, with API-level coverage in [the effect mutation audit test](../../../tests/test_rule_effect_mutation_audit_migrated.py). These counters have different attempt/commit semantics; use graph-state deltas for committed growth and do not sum them as one unit without normalization.

## Next gate

Before a broad mutation-cost claim, add counter-coverage for the remaining rule-effect mutation families and reconcile attempts/commits with state deltas. Then run repeated larger isolated sweeps with an explicit memory baseline, preserve the dense control, and preregister the primary scaling metrics and thresholds.
