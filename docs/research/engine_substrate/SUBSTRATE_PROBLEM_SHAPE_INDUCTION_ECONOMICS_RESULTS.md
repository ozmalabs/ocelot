# ProblemShape induction economics diagnostic results

**Date:** 2026-09-25  
**Evidence grade:** one measured, authored pathway envelope; not a prevalence estimate.  
**Preregistration:** [`SUBSTRATE_PROBLEM_SHAPE_INDUCTION_ECONOMICS_PREREG_20260925.md`](SUBSTRATE_PROBLEM_SHAPE_INDUCTION_ECONOMICS_PREREG_20260925.md) (with v1.1 per-rule attribution amendment)  
**Runner:** [`substrate_problem_shape_induction_economics.py`](../../../scripts/substrate_problem_shape_induction_economics.py)  
**Raw report:** [`substrate_problem_shape_induction_economics_20260925.json`](../../../evaluation/reports/substrate_problem_shape_induction_economics_20260925.json)

## Outcomes

All ten expected initial statuses matched, exactly one `ProblemShape` was minted, and the first decompose residual re-decoded to `ps_has_bound=yes` after codebook growth. Two observations arrived as residuals; after recurrence and re-decode, one remained residual: the held-out-in-sequence CAN-to-deduction singleton. The six seeded-recognition cases (three deduction and three Bigville CAN exact goals) all recognized without minting. This is a stateful demonstration sequence, so `2/10` residual arrivals and `1/10` mints are not estimates of natural-task rates.

Per-rule counters are attributed to the five exact `ProblemShape` rules (`ps_decode`, `ps_recognize`, `ps_residual`, `ps_mint`, `ps_redecode`), not all loaded rules. For the first six recognized observations, candidate pairs rose exactly `7, 14, 21, 28, 35, 42`; per-observation term evaluations rose `71, 110, 149, 188, 227, 266`. This shows the current full rule closure revisits a growing observation population on this sequence. It suggests quadratic cumulative work over repeated observations in this fixed workload, but six points do not establish a general asymptotic law.

| Observation stage | Initial status | Final status | Mint delta | ProblemShape candidate pairs | ProblemShape term evaluations | Instrumented observe wall time |
|---|---|---|---:|---:|---:|---:|
| Deduction recognition 1–3 | recognized | recognized | 0 | 7 / 14 / 21 | 71 / 110 / 149 | 11.90–13.05 ms |
| CAN exact recognition 1–3 | recognized | recognized | 0 | 28 / 35 / 42 | 188 / 227 / 266 | 12.15–12.81 ms |
| First decomposition observation | residual | recognized after later mint | 0 | 56 | 389 | 12.36 ms |
| Recurrence / mint | recognized in the same closure | recognized | 1 | 96 | 1,235 | 16.34 ms |
| Third decomposition observation | recognized | recognized | 0 | 63 | 390 | 13.10 ms |
| CAN-to-deduction singleton | residual | residual | 0 | 80 | 539 | 12.56 ms |

These wall times include full rule closure and instrumentation; they are descriptive for this machine and run. Median observe wall time was 12.46 ms, maximum 16.34 ms. Full seed boot took 14.84 s and the worker's process high-water RSS was 1.792 GB. That RSS includes Python, the native extension, and all loaded seeds; it is not an incremental learner-memory measure. Whole-engine candidate enumeration totaled 84,605 across observations, while the five ProblemShape rules accounted for 442 candidate pairs. This separation matters: most of the measured closure work belongs to other active seed rules.

## Claim boundary and follow-up

This fills one E2 gap with residual transitions, one mint, re-decode, attributed candidate/term work, and a cost tail. It does not estimate natural residual frequency, false-mint precision across labeled tasks, reuse across independent episodes, held-out generalization, or acquisition cost across domains. The next measurement should repeat the frozen protocol over separate task families and process instances, vary observation-population size while holding task mix fixed, and include a no-ProblemShape or frozen-codebook control to isolate the incremental cost of this subsystem from full-seed closure.
