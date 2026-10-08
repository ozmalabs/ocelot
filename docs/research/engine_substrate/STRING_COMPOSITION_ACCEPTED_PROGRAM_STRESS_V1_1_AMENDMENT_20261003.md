# Accepted string-program stress v1.1 analysis amendment

Date: 2026-10-03, before recapture.

The original stress capture stores only per-program accuracy, which cannot show how quickly a validation sample detects a known incorrect accepted program. Amend the capture to retain the correctness bit for each of the 50 independently generated rows in deterministic generation order. Re-run the same source-locked scoring protocol with no change to tasks, programs, seeds, or evaluator. Report the cumulative fraction of accepted artifacts with at least one observed error at prefix sizes 1, 2, 3, 5, 10, 20, and 50, plus the largest first-error index among programs that fail at least once. This prefix curve is retrospective calibration against known benchmark oracles; it does not establish a production-safe validation threshold because the sample is synthetic and selected programs are not independent.
