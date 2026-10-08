# Native graph storage scale v1.1 capture correction

Date: 2026-09-28, before the confirmatory rerun.

The first v1.1 capture completed all eight scheduled workers (two each at 10k, 100k, 1M, and 10M nodes). Every worker had exact node/edge counts, passed sampled reads, and matched the source lock. The parent nevertheless marked the run failed because two copied v1 aggregate assertions still expected six workers and six unique PIDs. This is a runner gate defect, not a workload or worker failure. Preserve the original raw, summary, and lock as attempt 1; do not count it as a passing v1.1 run.

The corrected runner and independent analyzer now require eight workers and eight distinct PIDs. No workload, size, measurement, order, or semantic gate changes. The confirmatory rerun receives a fresh lock that hashes this correction and the corrected runner/analyzer. Attempt-1 measurements remain descriptive; only the new locked rerun determines the result.
