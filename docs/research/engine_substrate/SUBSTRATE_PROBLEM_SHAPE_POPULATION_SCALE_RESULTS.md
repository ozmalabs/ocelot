# ProblemShape observation-population scale and frozen-codebook results

**Date:** 2026-09-25  
**Evidence grade:** 12-cell mechanism envelope across distinct processes; task families are project-authored.  
**Preregistration:** [`SUBSTRATE_PROBLEM_SHAPE_POPULATION_SCALE_PREREG_20260925.md`](SUBSTRATE_PROBLEM_SHAPE_POPULATION_SCALE_PREREG_20260925.md) with v1.1 PID-audit amendment  
**Runner:** [`substrate_problem_shape_population_scale.py`](../../../scripts/substrate_problem_shape_population_scale.py)  
**Analyzer:** [`analyze_substrate_problem_shape_population_scale.py`](../../../scripts/analyze_substrate_problem_shape_population_scale.py)  
**Raw report:** [`substrate_problem_shape_population_scale_20260925.json`](../../../evaluation/reports/substrate_problem_shape_population_scale_20260925.json)  
**Analysis:** [`substrate_problem_shape_population_scale_analysis_20260925.json`](../../../evaluation/reports/substrate_problem_shape_population_scale_analysis_20260925.json)  
**Lock:** [`problem_shape_population_scale_lock_20260925.json`](../../../evaluation/substrate_capability/problem_shape_population_scale_lock_20260925.json)

## Gate outcome

All 12 workers passed their expected-status, mint-count, fixed-point, and native-control checks. The raw report contains 12 distinct PIDs, confirming one fresh process per factorial cell. Each worker loaded the complete seed set; setup took roughly 15 seconds and peak process RSS was about 1.79 GB, including the runtime and seeds. Per-rule counters isolate the five ProblemShape rules from the much larger full-engine closure.

In the recognition-only mix, both codebook modes recognized every task and minted nothing. Yet active `ps_mint` performed a triangular number of candidate-pair checks over the growing observation population:

| Observations N | Active `ps_mint` candidate pairs | `ps_mint` term evaluations | Total ProblemShape candidate pairs, dynamic | Frozen-codebook total |
|---:|---:|---:|---:|---:|
| 2 | 3 | 15 | 21 | 18 |
| 4 | 10 | 50 | 70 | 60 |
| 8 | 36 | 180 | 252 | 216 |

At each N, the per-observation active-mint counts were exactly `1..N`, totaling `N(N+1)/2`; each candidate pair caused five term evaluations in these cells. The frozen-codebook control removed exactly those candidate pairs and term evaluations from the otherwise identical recognition workers. Thus this implementation pays quadratic cumulative candidate work for repeated recurrence checks even when no mint occurs. This identifies a specific cost in `ps_mint`'s graph rule, not a general complexity result for the substrate.

Per-rule attribution narrows the optimization target. At N=8 on the recognition stream, `ps_mint` accounts for 36 of 252 ProblemShape candidate pairs (14.3%) and 180 of 1,660 ProblemShape term evaluations (10.8%). `ps_decode` and `ps_recognize` each account for 72 candidates; `ps_residual` and `ps_redecode` each account for 36. The same candidate-pair share (14.3%) holds at N=2 and N=4; `ps_mint` accounts for 8.3% and 9.7% of term evaluations. An index for the recurrence rule alone therefore has a measured upper bound of modest benefit on this stream. Avoiding the broader repeated scan requires event-driven rule inputs across the observation state transitions, while retaining a one-time/global re-decode path when the codebook actually changes.

In the recurrent-residual mix, dynamic mode minted exactly once at every size, re-decoded the first residual, and recognized every observation by the end. The frozen control minted zero and left every observation residual. ProblemShape candidate totals for dynamic/frozen were 32/21 at N=2, 81/70 at N=4, and 263/252 at N=8; corresponding term totals were 490/171, 841/514, and 2,011/1,716. The extra dynamic work includes recurrence support evaluation, the mint, codebook epoch growth, re-decode, and subsequent recognition. Dynamic mint-rule candidate pairs were 5, 12, and 38; frozen controls were zero.

## Interpretation and next work

The experiment substantiates two parts of the induction economics profile: a recurrent shape mints once and is reused within this task stream, while the recurrence guard itself has a measured quadratic cumulative candidate cost on recognized observations. It does not estimate how often real workloads produce residuals, whether one mint is correct across independent tasks, or whether the cost curve transfers to a different rule/codebook design. The frozen condition is a controlled tombstone ablation through the native public API, not a deployed configuration.

Next, prototype an event-driven observation-state queue for all five transition rules (`ps_decode`, `ps_recognize`, `ps_residual`, `ps_mint`, `ps_redecode`), plus keyed support lookup for recurrence. Compare the candidate index alone with the full event-driven variant so the limited ceiling is measured directly. Require exact observation statuses, mint count/support, codebook epoch, rollback and replay parity at larger N and with interleaved task families. Do not change the default rules until the full-closure baseline and an independent incremental oracle are compared under a preregistered protocol.
