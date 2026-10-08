# Anaphora join-order replay v1.1 amendment

Date: 2026-09-28 local

## Trigger

A single-worker exploratory setup run (`permutation=0123`, `replicate=0`) executed the frozen two-turn task. The `it` Mention resolved only to `question`, while the resulting Intent contained both `answer` and `question` in `about_concept`. This matches the existing test's membership oracle (`question` is present); the v1 runner's draft exact-list expectation was too strict because it treated the statement predicate/head as an invalid extra concept.

## Change

The task gate now requires: the second message has an Intent; its `it` Mention resolves exactly to `question`; and `question` is present among that Intent's `about_concept` nodes. Other `about_concept` values are recorded and not rejected. This corrects the independent oracle to the task contract already used by `tests/test_intent_migrated.py`; it does not change the task, seed, pattern, order schedule, worker count, source path, or candidate-work metric.

The pilot terminal report was `fixed_point` with zero terminal progress after six second-turn progress steps. Audit-on closure time for this worker was 140,880 ns. Its raw output was emitted by the exploratory worker command before the amended raw-capture harness existed; this v1.1 note preserves the relevant observation, and the confirmatory run will recapture every worker with stdout/stderr hashes. The pilot is not pooled into the confirmatory analysis.

## Locking

The preregistration, v1.1 amendment, runner, analyzer, selected seed dependency closure, test input, Rust matcher/audit sources, native extension, and build manifest are all included in the refreshed source/native lock. Any further changes invalidate the lock and require another amendment before the confirmatory run.
