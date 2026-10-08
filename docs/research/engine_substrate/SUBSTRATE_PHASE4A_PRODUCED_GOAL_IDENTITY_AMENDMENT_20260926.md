# Phase 4A produced Goal identity probe amendment (2026-09-26)

The first attempted capture was invalid and produced no report. The worker command has five `sys.argv` elements (script, `--worker`, size, replicate, arm), while the initial dispatch guard expected four. Workers therefore re-entered the scheduler instead of executing a cell, recursively spawning schedules. The process tree was stopped when this was diagnosed; no timing or correctness observations from that attempt are retained.

Correction: require exactly five arguments for worker dispatch. The workload, arms, sizes, replication count, semantic gates, and metrics are unchanged. The corrected runner and this amendment are included in the refreshed lock. The complete 18-worker schedule will be captured from the start and independently audited.
