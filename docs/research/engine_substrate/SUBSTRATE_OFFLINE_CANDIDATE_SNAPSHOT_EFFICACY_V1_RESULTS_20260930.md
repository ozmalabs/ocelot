# Offline candidate-snapshot efficacy v1 results

## Result

The amended source-locked panel completed 30/30 fresh workers (six matrix/layout cells × five replicates), with no worker failures. The independent analyzer passes all 15 integrity, reconstruction, isolation, and eager/graph-page semantic parity checks.

The candidate learner acquired the intended `DimensionGenerator` in 25/30 workers. Every acquired candidate transferred exactly on all 16 held-out geometries, and every one of those 400 calls routed through the training-acquired generator. The five misses were all `shearB × adjacent_01`; they produced no exact held-out transfer. Thus the candidate arm scored 400/480 (83.3%) over all cells, with 100% transfer conditional on successful acquisition. Frozen and equal-exposure/no-consolidation controls each scored 0/480. The paired candidate-minus-control difference is 83.3 percentage points on mean and 100 points on the median cell/replicate; five acquisition-miss pairs are ties. This supports a causal role for the acquired object within this fixed authored family, not broad learning generality.

On 240 nonlinear negative evaluations, there were no false acceptances and no new `DimensionGenerator` mints. Every negative call nevertheless produced an unadjudicated novelty signal (`status=minted`/`CapabilityAxis`); the experiment has no independent oracle for whether those axes are appropriate discoveries, so they are not labeled false or correct mints. This is a material open measurement, not a clean negative result for Rung 3.

The primary graph and each source snapshot remained unchanged during branch evaluation. Candidate eager-copy and shared-graph-page CoW children have exact parity on positive and negative task status, residual, transform, generator route, predicted output, and novelty signal. All 30 workers pass these checks. This is semantic CoW evidence within a learned-snapshot workload; no general API or performance claim follows.

## Cost

Medians across workers: candidate training closure 5.33 ms; candidate shared-page training fork 0.44 ms; candidate validation branch 198.0 ms eager and 192.7 ms shared pages. Frozen and exposure validation branches take 133.6 ms and 138.5 ms. Candidate positive and negative rule-closure costs are 41.2 ms and 118.9 ms eager, versus 41.3 ms and 121.6 ms on shared pages. The negative-task path is materially more expensive than positive transfer, partly because it repeatedly creates novelty signals. Median worker wall time for boot, all branches, and digest checks is 1.13 s; median peak RSS is 57,964 KiB.

The shared-page validation median is about 2.7% below eager copy in this one-host run, but the experiment was designed for semantic parity and did not preregister a performance superiority test. Treat this timing as descriptive only. The data do show that applying a learned object is not “near zero cost” in this workload: validation dominates the 5.3 ms acquisition closure, and negative novelty processing is the largest measured component. Eager and CoW branch setup itself is sub-millisecond at this fixture size.

## Limits

This is a source-visible, generated 2-D integer-linear family with six training cells and fixed geometries; repeated workers quantify runtime/task-cell consistency, not a broad task distribution. The negative tasks are hand-authored nonlinear transformations, not a representative false-mint sample. The frozen control has no preexisting target generator, and the exposure control disables GenInfer; no reset-memory condition or forgetting measure is included. The capture is not project-held, independently custodied, formal P3-E1 evidence, natural-task transfer, self-directed experiment selection, open-ended self-improvement, or vLLM compatibility. No candidate state is adopted.

## Artifacts and reproduction

- [Preregistration and amendments](SUBSTRATE_OFFLINE_CANDIDATE_SNAPSHOT_EFFICACY_V1_PREREG_20260930.md)
- [Runner](../../../scripts/genmint_candidate_snapshot_efficacy_v1.py)
- [Independent analyzer](../../../scripts/analyze_genmint_candidate_snapshot_efficacy_v1.py)
- [Confirmatory source/native lock](../../../evaluation/substrate_capability/genmint_candidate_snapshot_efficacy_v1_lock_20260930.json)
- [Confirmatory raw capture](../../../evaluation/reports/genmint_candidate_snapshot_efficacy_v1_20260930.json)
- [Independent analysis](../../../evaluation/reports/genmint_candidate_snapshot_efficacy_v1_analysis_20260930.json)
- [Initial capture before the cost amendment](../../../evaluation/reports/genmint_candidate_snapshot_efficacy_v1_initial_pilot_20260930.json)
- [Initial analysis](../../../evaluation/reports/genmint_candidate_snapshot_efficacy_v1_initial_pilot_analysis_20260930.json)
- [Initial lock](../../../evaluation/substrate_capability/genmint_candidate_snapshot_efficacy_v1_initial_pilot_lock_20260930.json)

Reproduce from the repository root with `python3 scripts/genmint_candidate_snapshot_efficacy_v1.py --lock` (compare with the checked-in lock), `python3 scripts/genmint_candidate_snapshot_efficacy_v1.py`, then `python3 scripts/analyze_genmint_candidate_snapshot_efficacy_v1.py`. The analyzer reports all invalid/missing cells and exits nonzero when an integrity check fails.
