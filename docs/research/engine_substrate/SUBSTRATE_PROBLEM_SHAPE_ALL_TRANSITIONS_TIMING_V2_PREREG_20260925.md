# ProblemShape all-transition eventization paired timing v2

**Status:** preregistered exploratory timing extension; semantic results remain scoped to the authored workload.

## Question and workload

Does the all-transition ProblemShape event/index candidate change observe-path wall time on the locked N=8 recurrent-residual sequence, relative to the ordinary full-closure baseline, when repeated in fresh paired processes with balanced randomized arm order? This extends the earlier six-pair timing pilot; it does not vary task mix or size.

## Procedure

Run 12 baseline/candidate pairs, each arm in a fresh subprocess and each worker required to pass its existing exact status, mint, support/index, fixed-point, and read-back checks. Pair order is balanced (six baseline-first and six candidate-first); pair execution order is shuffled using Python `random.Random(20260925)`. Each worker uses N=8, `recurrent_residual`, and dynamic codebook mode for baseline; candidate uses the all-transition event/index path. Preserve all pairs, failures, worker PIDs, elapsed wall/CPU totals, per-rule counters, host index/event maintenance, and process RSS. Do not discard outliers or change the default path.

The lock pins this preregistration, runner, earlier pair runner and analysis, baseline/candidate workers, baseline population raw, relevant seeds, ProblemShape/task-constructor sources, native extension/build manifest, and Cargo lock. Require a current native build before any worker starts. Record pair-level candidate/baseline ratios and paired bootstrap intervals over the 12 pairs; treat timing as exploratory.

## Interpretation

The fixed workload and N=8 do not establish a scaling law, natural-task locality, or a substrate-wide speedup. The experiment tests repeatability and precision of the measured timing effect for one authored sequence. Candidate state and every semantic invariant remain a gate; no performance result can compensate for a semantic mismatch. Allocation-level native memory, persistence/rebuild, concurrency, rollback under injected failure, other task mixes, and larger N remain outside scope.
