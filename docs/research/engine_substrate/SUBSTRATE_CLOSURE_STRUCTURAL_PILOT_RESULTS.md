# Closure structural pilot results

**Status:** exploratory harness viability result; not a confirmatory benchmark or scaling claim.

## Question

After fixing the recursive same-type cursor bug, does the native rule runner compute the intended closure and reach a settled state on more than one graph structure?

## Method

The pilot invokes the native PyO3 `Substrate.run_rules` path with two graph-authored rules: `link-link -> reach` and `reach-link -> reach`. The generated directed acyclic graph families are paths (construction-known treewidth 1), banded DAGs with edges i→i+1 and i→i+2 (construction-known treewidth at most 2), and complete DAGs (treewidth n−1). Each family was run at n=6, 10, and 14. The independent Python oracle counts ordered node pairs connected by at least one path of length two or more, matching the rule semantics even when a direct shortcut edge also exists. A one-step follow-up probes whether work remains.

Raw manifest and records: [structural pilot JSON](../../../evaluation/reports/substrate_closure_structural_pilot_20260924.json). The earlier failure is preserved in [initial pilot results](SUBSTRATE_CLOSURE_PILOT_RESULTS.md); the cursor diagnosis/fix is documented in [recheck results](SUBSTRATE_CLOSURE_PILOT_RECHECK_RESULTS.md).

## Results

| Topology | Nodes | Input links | Expected reach edges | Actual reach edges | Progress steps | Candidate pairs | Leaf visits | Wall time | Outcome |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Path | 6 | 5 | 10 | 10 | 4 | 19 | 10 | 0.047 ms | Exact, settled |
| Path | 10 | 9 | 36 | 36 | 8 | 53 | 36 | 0.034 ms | Exact, settled |
| Path | 14 | 13 | 78 | 78 | 12 | 103 | 78 | 0.055 ms | Exact, settled |
| Banded DAG | 6 | 9 | 10 | 10 | 2 | 39 | 21 | 0.020 ms | Exact, settled |
| Banded DAG | 10 | 17 | 36 | 36 | 4 | 115 | 77 | 0.042 ms | Exact, settled |
| Banded DAG | 14 | 25 | 78 | 78 | 6 | 223 | 165 | 0.075 ms | Exact, settled |
| Complete DAG | 6 | 15 | 10 | 10 | 1 | 55 | 30 | 0.030 ms | Exact, settled |
| Complete DAG | 10 | 45 | 36 | 36 | 1 | 285 | 204 | 0.094 ms | Exact, settled |
| Complete DAG | 14 | 91 | 78 | 78 | 1 | 819 | 650 | 0.221 ms | Exact, settled |

All nine records report exact edge counts and a zero-work terminal probe. Candidate and leaf work rises with denser structures at the same node count; complete-DAG work is substantially higher than path work. At these tiny sizes, timing is dominated by measurement noise and startup/runtime overhead; do not fit or extrapolate a scaling law.

## Limits and next work

This pilot validates semantic agreement and the measurement path across two sparse low-width families and one dense, high-treewidth control. It does not test rule diversity, fresh-node minting, repeated independent worker memory, host orchestration, or large sizes. Peak RSS remains a process high-water mark shared across instances in the worker, so the manifest must not be read as per-instance memory. Treewidth is recorded from the construction, not computed by a general decomposition algorithm. The harness itself now accepts `--topologies path banded_dag complete_dag`; the original pre-fix and path-only outputs remain preserved separately.

Next: add isolated per-instance resource capture (prefer subprocess workers), audit candidate counters against a small explicit trace, then freeze and preregister a broader closure workload before making any tractability claim.
