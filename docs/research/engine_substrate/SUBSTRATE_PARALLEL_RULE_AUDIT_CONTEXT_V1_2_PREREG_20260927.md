# Parallel matcher rule-audit context v1.2 preregistration

Date: 2026-09-27 local
Status: preregistered before rebuilding and recapturing

## Question

Does namespaced rule identity, matcher-verified attribution, unattributed-work accounting, and complete context cleanup produce conserved per-rule/per-clause counts without changing task results?

## Intervention

Tag graph-resident Rule node IDs into a separate audit namespace; register each dispatched matcher's identity, name, and arity; verify name and arity at each candidate-test site; count identity or clause mismatches as globally unattributed; and clear the active context at every rule-attempt boundary. Keep Rayon rebinding unwind-safe. Do not change matching, partitioning, candidate enumeration, effects, scheduling, or reply behavior. These interventions affect only opt-in audit attribution.

## Workload and repeats

Run the exact two-request `describe_scene` concurrent fixture from request-cost capture v1 in three fresh processes, with current-source/native fingerprints locked after the intervention is built. Preserve the same task input, scene, forced serialization, and all previous schedule, goal identity/lifecycle, pause, final graph, and reply gates. Compare normalized final semantic graph digest and reply pair with the v1 valid raw capture. Request A's reply gate is expected to remain failed; that does not exclude the work measurement.

## Required gates

1. Three fresh PIDs; all worker-start, worker-finish, and post-run source/native fingerprints equal the saved lock.
2. Every prior schedule, distinct goal identity, lifecycle, pause, thread-join, and semantic graph gate passes; final graph digests equal request-cost v1.
3. Replies reproduce across the three workers and remain classified against the existing exact baseline.
4. For each request, per-rule and per-clause attributed candidate counts each sum exactly to `cand_tested - cand_tested_unattributed`; attributed plus unattributed equals global `cand_tested`.
5. Every candidate-producing audit ID maps to native matcher metadata captured from the actual rule dispatch.
6. Every recorded clause position is less than native metadata match arity; graph-rule IDs are disjoint from substrate RuleIdx IDs.
7. Candidate totals, arity shares, and named-rule rankings reproduce exactly across the three workers.
8. Immediately post-reset, candidate-work counters are zero and per-rule/per-clause tables are empty.

## Interpretation boundary

Passing these gates validates the audit attribution path for the measured serial and Rayon workloads in this fixture. It does not establish natural workload prevalence, cheap-cut locality, polynomial scaling, general matcher correctness, uninstrumented latency, or a passing request-A capability result. Any mismatch is reported as a failed attribution gate; global totals may still be reported only if their own source and conservation gates pass.

## Artifacts

A v1.2 worker, driver, analyzer, source/native lock, raw worker capture, analysis, and result note use distinct paths so v1 evidence remains immutable. The result note records any amendment and points back to the v1 source attribution finding.
