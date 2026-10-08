# ProblemShape all-transition eventization results

**Status:** all six semantic cells pass; measured rule-work reduction is substantial in this authored workload, while wall-time evidence is mixed and exploratory. No production seed/default path changed.

## Protocol

The candidate emits a pending-decode event at observation creation; `ps_decode` consumes it and emits a decoded event; `ps_recognize` and `ps_residual` consume decoded events; residual emits a mint-candidate event; and `ps_mint` uses that event plus the per-key support index. `ps_redecode` intentionally retains its scan across all observations when a codebook epoch changes, then clears stale transition events and emits pending-decode events again. This global invalidation is necessary to re-evaluate held-basis recognitions after minting.

The protocol is [`SUBSTRATE_PROBLEM_SHAPE_ALL_TRANSITIONS_PREREG_20260925.md`](SUBSTRATE_PROBLEM_SHAPE_ALL_TRANSITIONS_PREREG_20260925.md). Six fresh processes ran the locked N=2/4/8 recognition and recurrent-residual cells against the dynamic baseline workers. All final statuses, initial status trajectories, one-mint behavior, minted key/support-at-mint, codebook epoch, fixed point, index support, one index link per observation, and distinct PIDs passed. Raw output is [`substrate_problem_shape_all_transitions_20260925.json`](../../../evaluation/reports/substrate_problem_shape_all_transitions_20260925.json); the hash-checking analysis is [`analyze_substrate_problem_shape_all_transitions.py`](../../../scripts/analyze_substrate_problem_shape_all_transitions.py) and [`analysis JSON`](../../../evaluation/reports/substrate_problem_shape_all_transitions_analysis_20260925.json).

## Results

| N / workload | Candidate pairs baseline → eventized | Term evaluations baseline → eventized | Wall-time delta | Host index/event maintenance |
|---|---:|---:|---:|---:|
| 2 recognition | 21 → 7 (−66.7%) | 181 → 115 (−36.5%) | −2.5% | 70 μs |
| 2 recurrent | 32 → 21 (−34.4%) | 490 → 357 (−27.1%) | −0.3% | 68 μs |
| 4 recognition | 70 → 18 (−74.3%) | 518 → 274 (−47.1%) | −5.4% | 131 μs |
| 4 recurrent | 81 → 32 (−60.5%) | 841 → 530 (−37.0%) | +4.8% | 151 μs |
| 8 recognition | 252 → 52 (−79.4%) | 1,660 → 724 (−56.4%) | +3.3% | 282 μs |
| 8 recurrent | 263 → 66 (−74.9%) | 2,011 → 1,008 (−49.9%) | −7.2% | 277 μs |

At N=8 recurrence, per-rule candidate pairs are: decode 74→10, recognize 74→10, residual 39→2, mint 38→6, and re-decode remains 38→38. Re-decode Term evaluations also remain 438 in both arms. Thus the reduction is concentrated in ordinary lifecycle stages; the codebook invalidation pass remains linear in the observation population in this workload.

The earlier residual-event/index variant reduced total Term evaluations by about 12% at N=8 recurrence. Eventizing the other transition inputs increases the measured reduction to about 50%. This establishes that global `observed_problem` match driving was a major source of candidate work in these rules, but does not show all of that work translated to wall time. Wall differences vary from −7.2% to +4.8% across single-run cells. Host index/event maintenance is under 0.3 ms per worker, while full observation work is around 25–115 ms. Repeated randomized pairs are required before attributing a wall-time effect.

## Limits and next work

This is a six-cell, fixed-order authored workload, not a broad natural-task sample. The result excludes large memory regimes and does not test persistent index reconstruction, concurrency, rollback, long-lived stale events, or codebook-mint bursts at large N. The index is host-maintained and therefore remains a prototype. Next run randomized paired repetitions for the all-transition candidate, then test persistence/rebuild and mutation/replay invariants. Broader capability measurements and natural task distributions remain necessary for the substrate-wide tractability goal.

## Balanced randomized paired timing

The first three-pair timing sample had candidate-first order in every pair and is retained as unbalanced exploratory evidence. A follow-up used six fresh-process pairs with three baseline-first and three candidate-first orders. All 12 workers passed semantic checks and had distinct PIDs. Candidate/baseline time ratios were 1.095, 0.867, 0.856, 0.930, 0.903, and 0.970; the median ratio is 0.917 (8.3% lower), with a wide range from 14.5% lower to 9.5% higher. Five of six pairs were faster. The direction favors the eventized candidate, but the range is wide and the six-pair sample is too small for a stable performance claim.

The raw coordinator report has `all_checks_pass: false` because a copied final predicate still demanded three pairs after the amended protocol ran six. Every pair's `complete` and semantic flags are true, all 12 PIDs are unique, and order balance is 3/3. The raw artifact is unmodified and preserved. Independent raw validation is implemented in [`analyze_substrate_problem_shape_all_transitions_paired_timing_v1_1.py`](../../../scripts/analyze_substrate_problem_shape_all_transitions_paired_timing_v1_1.py), with summary in [`paired analysis JSON`](../../../evaluation/reports/substrate_problem_shape_all_transitions_paired_timing_v1_1_analysis_20260925.json); the correction is documented in [V1.2 amendment](SUBSTRATE_PROBLEM_SHAPE_ALL_TRANSITIONS_PAIRED_TIMING_V1_2_AMENDMENT_20260925.md). The exact coordinator hash is recorded after execution because it was omitted from the pre-run lock; treat the independent validation as a transparent adjudication of the six preregistered worker-level conditions, not a clean coordinator pass.

Next, expand paired repetitions and task-sequence variants, then measure index rebuild/persistence, rollback, concurrent ingestion, and larger observation populations. The global re-decode scan and natural-task event locality remain central open questions.
