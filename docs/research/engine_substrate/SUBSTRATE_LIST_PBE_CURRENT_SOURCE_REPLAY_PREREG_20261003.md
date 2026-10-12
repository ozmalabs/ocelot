# List PBE current-source replay preregistration

Date: 2026-10-03

## Purpose

Re-run the frozen 30-task list-PBE composition suite against the current P4 adapters, native extension, and engine sources to establish whether the 2026-09-25 result remains behaviorally stable after source drift. This is a diagnostic replay of an already inspected suite, not new-task or confirmatory capability evidence.

## Frozen procedure

Preserve the original fixture, task order, three arms (main, frozen codebook/bigram ablation, and fresh-substrate main replication), candidate policy, 200,000-candidate ceiling, held-out rows, and arm ordering. Lock this protocol, wrapper, benchmark, analyzer, fixture/generator, P4 runner/adapters, relevant seeds, native synthesizer, extension/build manifest, and Cargo lock before execution. Require a fresh native build. Write to new current-source report/analysis paths without replacing prior raw evidence. Compare task-level outcomes, status, construction, and held-out output against the prior amended report. Independently re-evaluate stored accepted IRs on every held-out row.

## Claim boundary

A matching result means measured behavior is stable for these source/build changes on this 30-task suite. It does not estimate natural task prevalence, source-independent validity, or general string/list capability. A mismatch requires task-level diagnosis; it cannot be attributed to one source change without a controlled source ablation.
