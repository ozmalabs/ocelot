# Bidirectional edge-identity guard proposals v1.1 — amendment

The v1 pilot outcomes are retained as exploratory evidence. Its analysis did not capture the full held-out scoring duration for recurrence, so it does not satisfy the preregistered cost accounting gate.

Version 1.1 reruns the same locked tasks, candidate generator, worker count, repeats, selection procedure, and correctness gates. It adds wall-clock nanoseconds for context/setup and candidate generation, composition, every training or held-out episode (including recurrence), source controls, selector and control decisions, and total per-worker execution. These are diagnostic timings from sequential local runs, not claims of stable CPU benchmarking. The v1 preregistration remains unchanged; this amendment and the v1.1 runner/analyzer are frozen into a new source lock before capture.

No correctness threshold or task input changes. The additional timing fields close an instrumentation gap only.
