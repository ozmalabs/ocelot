# Parallel matcher rule-audit context v1.1 preregistration

Date: 2026-09-27 local
Status: preregistered before rebuilding and recapturing

## Question

Does explicitly rebinding the active RuleIdx inside each Rayon batch-matcher partition restore valid per-rule and match-clause candidate attribution without changing task results?

## Intervention

Capture the current thread's active RuleIdx before Rayon dispatch. On each Rayon worker, set that index for the duration of its matcher partition and restore the worker's previous thread-local context afterward, including on unwind. Do not change matching, partitioning, candidate enumeration, effects, scheduling, or reply behavior. The intervention affects only opt-in per-rule/per-clause audit attribution.

## Workload and repeats

Run the exact two-request `describe_scene` concurrent fixture from request-cost capture v1 in three fresh processes, with current-source/native fingerprints locked after the intervention is built. Preserve the same task input, scene, forced serialization, and all previous schedule, goal identity/lifecycle, pause, final graph, and reply gates. Compare normalized final semantic graph digest and reply pair with the v1 valid raw capture. Request A's reply gate is expected to remain failed; that does not exclude the work measurement.

## Required gates

1. Three fresh PIDs; all worker-start, worker-finish, and post-run source/native fingerprints equal the saved lock.
2. Every prior schedule, distinct goal identity, lifecycle, pause, thread-join, and semantic graph gate passes; final graph digests equal request-cost v1.
3. Replies reproduce across the three workers and remain classified against the existing exact baseline.
4. For each request, per-rule candidate counts and per-clause candidate counts each sum exactly to global native `cand_tested`.
5. Every candidate-producing RuleIdx maps to the request's event-time installed pattern table.
6. Every recorded clause position is less than that pattern's match arity; no cross-rule or stale-worker clause positions are permitted.
7. Candidate totals, arity shares, and named-rule rankings reproduce exactly across the three workers.
8. Immediately post-reset, candidate-work counters are zero and per-rule/per-clause tables are empty.

## Interpretation boundary

Passing these gates validates the audit attribution path for the measured serial and Rayon workloads in this fixture. It does not establish natural workload prevalence, cheap-cut locality, polynomial scaling, general matcher correctness, uninstrumented latency, or a passing request-A capability result. Any mismatch is reported as a failed attribution gate; global totals may still be reported only if their own source and conservation gates pass.

## Artifacts

A v1.1 worker, driver, analyzer, source/native lock, raw worker capture, analysis, and result note use distinct paths so v1 evidence remains immutable. The result note records any amendment and points back to the v1 source attribution finding.
