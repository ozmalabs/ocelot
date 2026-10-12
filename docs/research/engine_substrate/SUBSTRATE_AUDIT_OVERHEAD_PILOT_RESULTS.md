# Scale-audit overhead pilot results

**Status:** repeated paired pilot; descriptive only, not an inferential overhead estimate.

## Question and method

Does enabling the process-global scale audit materially change native closure runtime on these synthetic cases, while preserving exact outcomes?

The harness ran each topology/size/replicate/mode in a fresh worker. For each input, audit-on and audit-off order alternated across the five replicates. Every pair used the same generated input, rules, build, and max-step cap. The sweep covers paths and banded DAGs at n=32, 64, 96, and complete DAGs at n=32, 64: eight cases, five pairs per case, 80 workers total.

Audit-on records candidate, leaf, and effect counters. Audit-off records those metrics as null. The analysis script validates pairwise equality of semantic outcomes, final edge counts, and progress-step counts before reporting median, range, and paired ratios.

Raw data: [sparse cases](../../../evaluation/reports/substrate_closure_audit_overhead_20260924.json), [dense cases](../../../evaluation/reports/substrate_closure_audit_overhead_dense_20260924.json). Reproducible summary: [summary JSON](../../../evaluation/reports/substrate_closure_audit_overhead_summary_20260924.json). Analysis source: [summarizer](../../../scripts/summarize_substrate_audit_overhead.py).

## Results

All 80 workers returned exact closure and settled. Every paired input had identical success status, quality, exactness, terminal reason, final edge count, expected edge count, and progress-step count.

| Topology | Nodes | Repeats | Audit on median wall time | Audit off median wall time | Median paired on/off ratio | Audit on range | Audit off range |
|---|---:|---:|---:|---:|---:|---:|---:|
| Path | 32 | 5 | 0.278 ms | 0.264 ms | 1.052 | 0.273–0.292 ms | 0.251–0.293 ms |
| Path | 64 | 5 | 0.979 ms | 0.964 ms | 1.016 | 0.948–0.993 ms | 0.930–1.004 ms |
| Path | 96 | 5 | 2.236 ms | 2.232 ms | 1.002 | 2.211–2.720 ms | 2.207–2.687 ms |
| Banded DAG | 32 | 5 | 0.367 ms | 0.368 ms | 0.988 | 0.359–0.379 ms | 0.366–0.389 ms |
| Banded DAG | 64 | 5 | 1.430 ms | 1.349 ms | 1.028 | 1.376–1.689 ms | 1.317–1.396 ms |
| Banded DAG | 96 | 5 | 3.077 ms | 3.099 ms | 0.987 | 2.977–3.120 ms | 2.971–3.162 ms |
| Complete DAG | 32 | 5 | 3.561 ms | 3.705 ms | 0.961 | 3.517–4.040 ms | 3.431–4.177 ms |
| Complete DAG | 64 | 5 | 32.449 ms | 32.052 ms | 1.002 | 30.596–33.277 ms | 31.920–33.205 ms |

Ratios vary in direction and lie near 1; several on/off ranges overlap. Five replicates are too few to distinguish a small instrumentation effect from runtime noise. Do not describe this as zero overhead or use the observed medians as a correction factor.

The per-worker peak-RSS increment over the post-import high-water baseline was also recorded. Median audit-on/off increments (MB) were: path n=32, 2.16/2.16; n=64, 2.36/2.16; n=96, 2.36/2.36; banded DAG n=32, 2.16/2.16; n=64, 2.36/2.16; n=96, 2.56/2.56; complete DAG n=32, 3.82/3.84; n=64, 16.87/16.96. RSS is page-quantized high-water memory, so these small on/off differences are descriptive and do not show a consistent collection cost.

## Interpretation limits

Both conditions use the same instrumented native binary. Audit-off disables counter updates, but the instrumented sites still execute their enabled-flag check. This experiment estimates the incremental cost of enabled counter collection over the disabled audit path. It does not measure the dormant instrumentation floor versus a build with those sites removed.

The timings cover the run_rules call only; worker startup and graph construction are excluded from the timed interval. Each worker's peak RSS includes interpreter/import/native-extension startup and is not an isolated rule-run allocation measure. The benchmark has five repeats per condition but only one machine and one synthetic rule family.

## Next gate

1. Improve timing sensitivity (longer workloads, controlled CPU pinning, more repeats, or calibrated batches) and run on a reference CPU with variance reporting.
2. Compare disabled instrumentation against a build with scale-audit sites compiled out to estimate dormant overhead.
3. Keep audit-on/off semantic parity as a required invariant for every measured family.
4. Repeat the resource baseline separately; do not infer graph memory from these worker RSS values.

These outcomes satisfy the plan's initial overhead-pilot gate for this closure family only. They do not satisfy the broader instrumentation-overhead or tractability gates.
