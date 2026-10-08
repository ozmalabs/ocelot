# Live dynamic helper work capture v1.4 preregistration

Date: 2026-10-05

## Question

Do the new native helper counters record nonzero, rule-attributed internal work on the same two-request live route used by the v1.3 rule-scope capture, reproducibly across fresh workers?

## Protocol

Use the v1.3 prompt pair, task fixture, worker construction, rule export, access trace, lifecycle checks, and three fresh process replicates. Build the extension from the current Rust source with `scripts/engine_build.sh --lib-only`; record the engine provenance. Freeze this protocol, runner, analyzer, v1.3 source inputs and historical outputs, native extension, and build record in a separate v1.4 lock. The v1.3 raw archive and lock remain immutable.

The native work event tuple is `(operation_id, rule_uid, kind, helper_family_id, work_units)`. Count helper events by kind and helper family, preserving rule UID. The captured work includes helper entry counts, codebook and relation-cue population visits, selected-node attribute counts, successfully parsed parts, helper search-loop work, scored ShapeDecode parts, recursively decoded graph Term nodes, Join render-rule candidates, and generator population visits.

## Gates

Require three distinct fresh worker PIDs, stable source/build inputs before and after each worker, the same two prompts and lifecycle outcomes, matching graph semantic digests and runtime trace signatures across workers, every observed runtime RuleUID mapped to its request's post-request rule export, zero dropped access/work events, at least one helper invocation, and at least one internal helper work unit. Report totals and per-rule/per-family counts. A passed capture demonstrates counter activity and reproducibility on this route only; it does not establish locality, frame attribution, natural-task prevalence, parity against an uninstrumented run, or a complexity bound.

## Reproduction

```sh
scripts/engine_build.sh --lib-only
python3 scripts/substrate_live_helper_work_capture_v1_4.py --lock
python3 scripts/substrate_live_helper_work_capture_v1_4.py
python3 scripts/analyze_live_helper_work_capture_v1_4.py
```

The lock must be written only after the protocol, runner, analyzer, and native extension are final. Any edit requires a new lock before capture.
