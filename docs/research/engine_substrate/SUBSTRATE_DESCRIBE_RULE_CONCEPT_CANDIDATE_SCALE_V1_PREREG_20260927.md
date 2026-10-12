# Describe-rule Concept candidate scaling v1 preregistration (2026-09-27)

## Question

The source-locked live trace attributes its dominant `name` reads to three graph rules in `scripts/arc_self_report.py::build_describe_faculty`. Each joins `Scene.has_percept` with `Microtheory.has_concept`, then checks Concept `name` and `Holds`. With the task input fixed, how do native candidate and Term counts grow as the Microtheory's irrelevant Concept population grows?

## Workload and schedule

Run 15 fresh worker processes: distractor Concept counts `N ∈ {0, 64, 256, 1,024, 4,096}`, three replicates per size. Use an isolated `WorldAdapter(seeds=())`, one Microtheory, one Scene, and three Percepts with fixed kinds `meter`, `static`, and `mover`. Install the three exact recognition rule structures and names from `build_describe_faculty` for `a_counter`, `a_thing_that_stays_put`, and `a_thing_that_moves_itself`. Define those three Holds predicates as exact equality checks on the Percept's `kind`; add exactly one target Concept per label. Fill the remainder of the Microtheory with unique named distractor Concepts with no matching Holds definition. Keep all three positive target Concepts and Percepts fixed across sizes.

Enable the native global/per-rule scale audit only around full closure. Record selected per-rule candidate-pair/Term counts, wall/CPU and peak RSS, fixed-point status, recognized `Percept is_a Concept` edges, and all source/native hashes. The worker gate requires the exact three expected classifications and no classification to distractor concepts. The fixed schedule and graph construction live in the runner.

## Gates

- 15 distinct worker PIDs; three replicates per size; source/native inputs stable and equal to the registered lock before/after each worker.
- All rules resolve to fixed point with no budget exhaustion.
- Exact output parity at every size: one `is_a` classification per Percept, paired to its matching target Concept; no distractor classification.
- Candidate-pair and Term counts are reported by rule and size; monotonicity and growth ratios are analyzed rather than assumed. No latency threshold is a pass condition.
- Every worker record is retained; a missing cell or source/build mismatch invalidates scaling inference.

## Interpretation limits

This isolates the dominant rule motif and its candidate-domain sensitivity. It is not the complete live describe faculty: only three of six recognizers are included, and downstream self-report, induction, other rules, and full-seed graph interactions are absent. Distractors are synthetic and deliberately negative; the sweep does not establish natural vocabulary distributions, task prevalence, or end-to-end conversation speed. The three `Holds` definitions are controlled exact kind predicates, not a fidelity claim about all six full concepts. Candidate counters are instrumented engine work, not uninstrumented latency or a theorem for arbitrary rules.
