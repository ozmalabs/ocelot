# Generated-pool active query versus iterative resynthesis v1.3 amendment

The v1.2 capture completed 12 workers and passed its semantic/source analyzer, but it used one process per task/arm. Its timings are a pilot and do not support stable cost comparisons.

Confirmatory replay: repeat every task/arm cell five times in fresh child processes. Each repetition is a matched block containing all four arms for all three tasks; randomize worker order within each block using the preregistered seed plus the repetition index. Keep each worker's generated-pool and synthesis budgets, input sets, formulas, and correctness gates unchanged. Record both internal worker timing and parent-observed process wall time. Summarize medians and paired ratios across blocks; query/correctness outcomes remain per-cell and must be exact. Do not discard failed workers or timed-out pools. The v1.2 pilot and its capture remain preserved.
