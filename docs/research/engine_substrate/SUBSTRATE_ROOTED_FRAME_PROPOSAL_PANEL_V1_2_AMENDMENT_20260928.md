# Rooted frame-proposal panel v1.2 amendment (2026-09-28)

## Reason and repair

V1.1 attempt 1 passed the capture gates, including nonempty request traces, zero dropped trace keys, count conservation, stable source locks, and semantic parity with v1. Its independent analyzer failed because a zero-count trace category was omitted by one representation and serialized explicitly as zero by the other. The raw run and failed analyzer output are preserved as attempt 1 and excluded from confirmatory results.

The independent analyzer now normalizes absent integer count fields to zero and independently verifies the trace-to-candidate projection against raw event rows. This correction was checked against the preserved attempt 1 capture; all 11 independent gates pass on that diagnostic record. No runner behavior, task selection, BFS proposal, trace scope, primary metric, or gate changed.

## Rerun

Use a fresh lock covering this amendment and the corrected analyzer, then run three new workers. The accepted v1 state-only capture remains the semantic baseline. Attempt 1 remains diagnostic and is not pooled with the fresh v1.1 confirmatory result.
