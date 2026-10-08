# Thoughtexperiment candidate branch scaling v2 results

## Outcome and integrity

The source-locked factorial capture and independent analysis pass all 54 cells:
two background topologies × three background sizes × three task apertures ×
three separator widths. It uses 162 fresh worker processes, yielding 972
timed no-op/candidate branch episodes plus 162 separate instrumented audit
probes. Every timed pair returns `true` for the live rule and `false` for the
threshold candidate. Graph digest, graph size, active rule UID/revision/hash,
and source lock remain identical before and after branch batches.

The audit probes confirm the manipulation is real. Across widths 1, 8, and 32,
the actual boundary degree equals the configured width. The per-rule audit
reconciles with process totals, and `Exists` examines exactly `width ×
evaluation_count` neighbors; the positive witness is inserted last. This
closes the v1 issue where a disconnected background did not exercise a task
frame boundary.

## Factor-slice medians

Each entry below is a median of per-cell medians pooled equally over the other
factor levels. Times are wall-clock milliseconds; timing probes are
uninstrumented. Instrumented probes are excluded.

| Varied factor | Level | Candidate fork | Candidate install | Task-frame build | Boundary-edge build | No-op closure | Candidate closure |
|---|---:|---:|---:|---:|---:|---:|---:|
| Background nodes | 128 | 0.053 | 0.219 | 0.054 | 0.021 | 0.253 | 0.206 |
|  | 1,024 | 0.048 | 0.243 | 0.043 | 0.020 | 0.245 | 0.178 |
|  | 8,192 | 0.048 | 0.253 | 0.081 | 0.034 | 0.245 | 0.185 |
| Aperture nodes | 2 | 0.046 | 0.219 | 0.031 | 0.027 | 0.204 | 0.173 |
|  | 8 | 0.051 | 0.237 | 0.054 | 0.022 | 0.252 | 0.212 |
|  | 32 | 0.053 | 0.288 | 0.129 | 0.024 | 0.263 | 0.194 |
| Separator edges | 1 | 0.047 | 0.238 | 0.056 | 0.011 | 0.240 | 0.188 |
|  | 8 | 0.050 | 0.237 | 0.049 | 0.025 | 0.250 | 0.195 |
|  | 32 | 0.051 | 0.246 | 0.055 | 0.061 | 0.252 | 0.190 |

Path and binary-tree background medians are similar: candidate closure is
0.193/0.187 ms and fork is 48.7/51.4 μs, respectively. Task-frame
construction rises with aperture (31 to 129 μs from 2 to 32 nodes), and
boundary-edge construction rises with width (11 to 61 μs from 1 to 32 edges).
Closure wall time is noisy and shows no reliable monotonic trend across these
small fixtures, even though the audit confirms that the `Exists` term's
examined-neighbor work grows exactly with separator width. This separates a
verified operation-count increase from an unproven latency increase.

## Interpretation and limits

The result supports three bounded claims: shared-page fork remains around
50 μs over these background sizes/topologies; task-frame construction responds
to aperture; and explicit boundary scans incur work proportional to the
registered separator width. It does not prove that natural task graphs admit
small separators, that total inference is polynomial in a hierarchy, or that
closure latency is independent of these factors. The workload is authored,
one rule family, one host, and at most 8,192 decoys / 32 task nodes / 32
crossing edges. RSS snapshots are diagnostic only. Next sample real task
graphs prospectively, estimate boundary-width distributions without seeing
outcomes, and repeat the scaling panel on a workload-derived topology and a
second host.

## Reproduction artifacts

- [Preregistration](THOUGHTEXPERIMENT_CANDIDATE_BRANCH_SCALING_V2_PREREG_20261005.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_candidate_branch_scaling_v2.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_thoughtexperiment_candidate_branch_scaling_v2.py)
- [Fixture](../../../evaluation/substrate_capability/thoughtexperiment_candidate_branch_scaling_v2_fixture_20261005.json)
- [Source lock](../../../evaluation/substrate_capability/thoughtexperiment_candidate_branch_scaling_v2_lock_20261005.json)
- [Capture](../../../evaluation/reports/thoughtexperiment_candidate_branch_scaling_v2_20261005.json)
- [Independent analysis](../../../evaluation/reports/thoughtexperiment_candidate_branch_scaling_v2_analysis_20261005.json)
