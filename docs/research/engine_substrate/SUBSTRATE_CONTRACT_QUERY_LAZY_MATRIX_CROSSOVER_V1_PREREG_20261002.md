# Contract-query lazy matrix crossover v1 — preregistration

## Question

For the current survivor-first lazy matrix implementation, how do hypothesis count and initial survivor fraction affect end-to-end selection cost, evaluator calls, and memory relative to the uncached selector?

## Panel

Compare uncached `select_discriminating_input` with `select_discriminating_input_batched` plus one reusable `TermPredictionMatrix` per sequence. Use binary-coded pure Terms at H=128 (K=7, N=28) and H=512 (K=9, N=36). For each H, run with m=0, m=4, and m=K initial bit-distinguishing observations, plus one neutral x=0 observation. These cells leave H, H/16, and 1 survivors, respectively, and require K, K−4, or zero further queries. The same target (`h(H/3)`), Term family, candidate grid, observations, native evaluator, and labels are used in each paired arm. Run three fresh repetitions per cell and randomized arm order for 36 workers. The target ID is analysis-only and is never passed to either selector.

Each worker also runs the known off-grid misspecification control on the m=0 data: the external target agrees with its selected finite hypothesis on every candidate input but differs at x=999. Both arms should return the same singleton and expose the held-out disagreement.

## Gates, decision rule, and measurements

Require stable pre/post source and native hashes; exact paired query, entropy, prediction, label, terminal, and survivor parity; independent closed-form checks and tie-break recomputation; exact initial survivor counts; correct cached cell/evaluator-call accounting; and equal false-singleton behavior. Report median paired wall time, native calls, approximate matrix bytes, and peak RSS by H and initial survivor fraction.

The matrix remains opt-in. A scale-use recommendation requires at least 1.25× median speedup in both H values at m=0 and m=4, no more than 2× peak RSS, and exact semantic gates; the m=K cells are the early-exit control and may be slower in wall time but must not compute candidate predictions after singleton detection. The result is limited to this finite binary-coded Term family and one host.

## Artifacts

- Runner: `evaluation/substrate_capability/substrate_contract_query_lazy_matrix_crossover_v1.py`
- Analyzer: `evaluation/substrate_capability/analyze_substrate_query_lazy_matrix_crossover_v1.py`
- The runner creates an immutable pre-run lock and raw capture under `evaluation/substrate_capability/` and `evaluation/reports/`.
