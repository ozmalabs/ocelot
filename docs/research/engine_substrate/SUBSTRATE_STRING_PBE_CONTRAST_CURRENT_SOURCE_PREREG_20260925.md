# Current-source replication of string PBE contrast pilot

**Status:** diagnostic source-drift replication; not a new or blinded task evaluation.

## Question

Do the previously observed P4 outcome patterns on the frozen 18-task contrast suite persist against the current synthesis/retrieval adapters and native extension? Preserve the original task, arms, four revealed/three held-out rows, and per-goal 500,000-candidate ceiling exactly.

## Procedure

Run the original contrast benchmark implementation without changing its task, scoring, route order, or policies. A wrapper redirects output to a new report and checks a new hash lock before calling the benchmark. Lock the wrapper, original benchmark and analyzer, fixture generator and fixture, original preregistration, shared benchmark protocol, P4 runner/adapters, relevant seeds, native synthesizer, extension/build manifest, and Cargo lock. Verify native build freshness before execution. Keep the original report and analysis intact. The four arms remain main, retrieval bypass, retrieval bypass plus the registered escalation, and main replay.

The tasks and results have already been inspected. Treat this as a source-current replication useful for detecting implementation drift, not as confirmatory task evidence. Preserve the independent fixture audit and compare current-source outcomes with the original raw report after execution.

## Interpretation limits

This estimates no new-task generalization or natural task prevalence. A match would show outcome stability across the specifically changed source/build versions, not source-independent validity. A mismatch would require task-level diagnosis before attributing it to any single source change. It does not test unseen operators or minting.
