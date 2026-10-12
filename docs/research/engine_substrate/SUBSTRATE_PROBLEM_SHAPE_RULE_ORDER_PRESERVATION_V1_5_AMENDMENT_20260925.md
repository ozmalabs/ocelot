# Amendment V1.5: same-corpus three-arm rule-placement control

Date: 2026-09-25

V1.4 showed that original-slot eventization preserves all non-ProblemShape per-rule counters, but the earlier append-order attribution used a different, mutable corpus. V1.5 directly compares three arms from the same content-addressed immutable seed snapshot: (1) baseline; (2) eventized rules that tombstone their five original rules and append replacements; and (3) eventized rules transformed in place at the five original seed slots. All arms use identical non-ProblemShape seed bytes, workload order, N=32 task mix, and Python hash seed.

For each mix, six triads run in randomized order, with each of the six arm permutations used once. Each triad must match final/initial observation statuses and per-step mint counts across all arms. Seed-loaded ordered rule names, failed seed IDs, and ProblemShape positions must match before any treatment. The pre-observation order gate requires the in-place arm to match baseline exactly, and the appended arm to equal the baseline sequence with the five target rules removed and then appended in the prescribed decode/recognize/residual/mint/redecode order. This confirms both treatment manipulations directly. Final rule order is recorded as an outcome.

All workers emit per-rule candidate, Term, where, enumeration, graph-write, and Term-unit counters. Paired timing is secondary and reported with the full six-pair range and median; no timing benefit is inferred if intervals cross parity. Snapshot byte hashes are verified before and after each process, and the immutable baseline snapshot is checked against the 831-file corpus lock.

This is a narrow mechanism isolation study on two authored workloads. It does not test natural-task locality, larger N, general closure complexity, or learning capability.
