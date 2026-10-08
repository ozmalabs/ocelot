# ProblemShape solver-family transfer v1.1 amendment (2026-09-27)

The v1 full-seed transfer panel passed on its locked snapshot, but final comparison against the live worktree found two subsequent source changes: `substrate/boot_all.py` now interns seed-index values and releases selected caches, and `substrate/boot_profiles.py` changed alongside it. Because this panel's outcome includes full-seed initialization and process memory, rerun the unchanged v1 schedule on a read-only snapshot containing the updated files. No task, resident index, oracle, or outcome threshold changes.

The v1 capture's outcomes have been inspected. V1.1 is a source-current replication, not a new confirmatory sample. Capture the complete pre/post runtime lock once; all snapshot inputs are read-only during its two-worker schedule. Report any change in boot, memory, solver completion, or ProblemShape transitions rather than assuming semantic parity.
