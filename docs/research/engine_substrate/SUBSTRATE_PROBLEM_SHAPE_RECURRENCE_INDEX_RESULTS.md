# ProblemShape recurrence event/index prototype results

**Status:** all six semantic cells pass; performance effects are exploratory and timing is inconclusive. No default path or production seed changed.

## Protocol and provenance

The candidate variant was preregistered in [`SUBSTRATE_PROBLEM_SHAPE_RECURRENCE_INDEX_PREREG_20260925.md`](SUBSTRATE_PROBLEM_SHAPE_RECURRENCE_INDEX_PREREG_20260925.md), with amendments [V1.1](SUBSTRATE_PROBLEM_SHAPE_RECURRENCE_INDEX_V1_1_AMENDMENT_20260925.md), [V1.2](SUBSTRATE_PROBLEM_SHAPE_RECURRENCE_INDEX_V1_2_AMENDMENT_20260925.md), [V1.3](SUBSTRATE_PROBLEM_SHAPE_RECURRENCE_INDEX_V1_3_AMENDMENT_20260925.md), [V1.4](SUBSTRATE_PROBLEM_SHAPE_RECURRENCE_INDEX_V1_4_AMENDMENT_20260925.md), and [V1.5](SUBSTRATE_PROBLEM_SHAPE_RECURRENCE_INDEX_V1_5_AMENDMENT_20260925.md). The lock pins the runner, native binary, workload seeds, baseline raw report, and amendment hashes. Six fresh processes ran N=2/4/8 × recognition/recurrent-residual. The baseline values come from the dynamic cells in [`SUBSTRATE_PROBLEM_SHAPE_POPULATION_SCALE_RESULTS.md`](SUBSTRATE_PROBLEM_SHAPE_POPULATION_SCALE_RESULTS.md).

Primary raw data: [`substrate_problem_shape_recurrence_index_20260925.json`](../../../evaluation/reports/substrate_problem_shape_recurrence_index_20260925.json). Reproducible comparison: [`analyze_substrate_problem_shape_recurrence_index.py`](../../../scripts/analyze_substrate_problem_shape_recurrence_index.py), output [`analysis JSON`](../../../evaluation/reports/substrate_problem_shape_recurrence_index_analysis_20260925.json). Earlier readback and timing-boundary diagnostics are retained as [`initial readback diagnostic`](../../../evaluation/reports/substrate_problem_shape_recurrence_index_v1_initial_readback_diagnostic_20260925.json), [`semantics-only run`](../../../evaluation/reports/substrate_problem_shape_recurrence_index_semantic_v1_3_20260925.json), and [`instrumentation-timing diagnostic`](../../../evaluation/reports/substrate_problem_shape_recurrence_index_timing_boundary_diagnostic_v1_4_20260925.json). Their mistaken acceptance/timing interpretations are superseded here and described in the amendments.

## Semantic result

All six workers passed: initial and final observation statuses, one mint only in recurrence workloads, mint-time support snapshot, codebook epoch, exact independent per-key support counts, one index link per observation, fixed-point state, and distinct process IDs. In recurrence workloads, observation 1 is residual at its own settle point and becomes recognized after later recurrence mints a shape; the minted shape stores support 2 while the separate index tracks the final population support N. This matches the baseline lifecycle.

Two early diagnostics falsely suggested a semantic problem. The first compared stale per-observation snapshots instead of refreshing final statuses after the full sequence. The next acceptance check expected the minted shape's immutable mint-time support to equal final population size. V1.1/V1.3 corrected those checks; neither was a behavior change to the treatment. A separate V1.4 timer included scale-counter decoding while the baseline timer did not; V1.5 corrected the boundary. The preserved diagnostic artifacts are not valid performance comparisons.

## Work and cost

Percentages compare one treatment worker with the already-locked baseline cell. Negative work deltas mean fewer operations. Wall-time changes are single-run differences, not paired repeated estimates.

| N / workload | `ps_mint` pairs baseline → prototype | `ps_mint` term evaluations baseline → prototype | All ProblemShape candidate pairs Δ | All ProblemShape term evaluations Δ | Observation wall time Δ | Host index maintenance |
|---|---:|---:|---:|---:|---:|---:|
| 2 recognition | 3 → 0 | 15 → 0 | −14.3% | −8.3% | +9.9% | 60 μs |
| 2 recurrent | 5 → 6 | 193 → 116 | +3.1% | −15.7% | −2.8% | 54 μs |
| 4 recognition | 10 → 0 | 50 → 0 | −14.3% | −9.7% | +4.7% | 114 μs |
| 4 recurrent | 12 → 6 | 228 → 116 | −7.4% | −13.3% | −4.5% | 101 μs |
| 8 recognition | 36 → 0 | 180 → 0 | −14.3% | −10.8% | −6.9% | 199 μs |
| 8 recurrent | 38 → 6 | 358 → 116 | −12.2% | −12.0% | +2.7% | 198 μs |

The candidate driver removes the `ps_mint` match work on recognition-only observations and sharply reduces its term work for N=4/8 recurrence. It does not reduce every total candidate count: N=2 recurrence adds one pair. Across all six cells, total ProblemShape term evaluations fall 8–16%, while matched wall time ranges from 6.9% faster to 9.9% slower. With one process per cell and no randomized repeated pairing, timing establishes neither improvement nor regression. Host index maintenance is measured at roughly 54–199 μs per cell; its fraction of total observation time is small in these workloads, but larger graphs, persistence, concurrency, rollback, and rebuild cost were not exercised.

## Interpretation and next step

This is evidence that a graph-resident support bucket plus a residual event can preserve canonical re-decode behavior in this small fixed workload and reduce `ps_mint`'s share of repeated rule work. It does not establish an overall scaling win: the other four ProblemShape rule match paths remain globally driven, and some of the overall work reduction may be counter/dispatch-path specific. The measured N=8 total-work reduction is modest relative to the remaining work.

Next, run randomized paired repetitions of the six cells with timer boundaries fixed, then prototype eventization of the other four rules as a separate variant. Before any default-path discussion, add index rebuild/persistence, concurrent observation, and rollback checks, and measure larger observation populations. The protocol amendments and preserved diagnostic runs remain part of the evidence record.

## Randomized N=8 timing follow-up

A separate preregistered run compared three fresh-process baseline/candidate pairs in fixed-seed randomized order. All six workers passed semantic checks. Candidate/baseline observation-time ratios were 0.929, 1.032, and 0.950; the median is 0.950 (about 5.0% lower), with pair differences from 7.1% lower to 3.2% higher. Two pairs were faster and one slower. This is weak exploratory evidence of a small benefit at this one workload, not a reliable speedup estimate. The result is sensitive to process-level variation and remains underpowered.

Each candidate repeated the same 231 ProblemShape candidate pairs and 1,769 Term evaluations; index maintenance was 197–201 μs over the eight-observation workload. In the locked baseline N=8 recurrence cell, `ps_mint` alone accounted for 38 candidate pairs and 358 Term evaluations versus 6 and 116 in the candidate. Other ProblemShape paths still account for most residual total work. Raw pairs are in [`paired timing JSON`](../../../evaluation/reports/substrate_problem_shape_recurrence_index_paired_timing_20260925.json), with reproducible summary in [`paired analysis JSON`](../../../evaluation/reports/substrate_problem_shape_recurrence_index_paired_timing_analysis_20260925.json); protocol and lock are [`paired timing preregistration`](SUBSTRATE_PROBLEM_SHAPE_RECURRENCE_INDEX_PAIRED_TIMING_PREREG_20260925.md) and `evaluation/substrate_capability/problem_shape_recurrence_index_paired_timing_lock_20260925.json`.

Next, increase paired repetitions and include randomized sequence/corpus variants before making any timing claim. In parallel, a separate preregistered prototype should eventize the remaining ProblemShape rules; it must preserve codebook-wide re-decode after mint and independently verify every final observation. Persistence/rebuild, concurrency, rollback, and larger scale remain open.
