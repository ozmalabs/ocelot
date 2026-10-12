# Full-sheet scoping comparison v1.1 amendment

Date: 2026-09-25. This corrects the execution driver, preserving v1's preregistration, runner, and raw cap-hit output.

V1 used repeated `apply_rule_once` calls. That API applies a single matching binding and returns whether a match was applied; it is not the batch sweep driver. Repeating it on `st_settle` can repeatedly apply the first binding and is not valid Jacobi execution. Therefore v1's cap-hit results do not measure the registered full-sheet dynamics.

V1.1 retains the same paired anatomy, seeds, afferent field construction, and global/root-scoped variants. It now tombstones every rule except the selected `st_settle` variant and `st_commit`, then uses native `run_rules(CAP)` so the engine's batch handling and fixpoint accounting are exercised. The same completeness, shape, paired-state, paired-progress-count and root-membership predictions apply. Record cap exits as cap exits; do not interpret them as termination. Exact residual behavior is inspected independently after the run. No production manifest or source is modified.
