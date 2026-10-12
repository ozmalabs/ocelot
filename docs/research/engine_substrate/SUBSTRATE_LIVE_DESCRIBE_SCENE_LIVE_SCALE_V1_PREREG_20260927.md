# Live describe-scene membership-scale v1 preregistration

Date: 2026-09-27

## Question

How do complete live-route candidate/Term counts, selected native accesses, latency, and peak RSS change when the loaded full-seed graph receives additional irrelevant Concept memberships?

## Workload and factors

Use the source-locked serial full-seed `describe what you see` route. Keep the exact three-Percept Scene, prompt, speaker, seed set, and every loaded/authored rule fixed. Add noise-only Concepts to one dedicated Microtheory before the measured request. Sweep 0, 1,024, and 4,096 added Concept membership edges; use two fresh-process replicates per size and paired audited/uninstrumented arms per replicate (12 workers total). Each noise Concept has a unique `tractability_noise_concept_NNNN` name and `kind=noise`; no recognition target label or Holds fact is added.

No rule is tombstoned. Scene attachment and noise construction are outside the request interval and reported separately from the full `converse` work. Whole-graph input sizes, candidate/Term counters, per-rule/per-clause breakdowns, access-trace aggregates, wall/CPU, and process high-water RSS are recorded. Trace node identifiers are not retained; rows are aggregated by native rule UID, operation kind, and resource while preserving exact count conservation.

## Gates

1. Twelve fresh workers, two audited/control pairs per cell, unique PIDs, exact source/native locks at start/end/post-run.
2. Every cell preserves the exact expected public description and resolved request Goal (`selection → execution → action_result`).
3. Audited and uninstrumented arms match per pair on reply, Goal projection, and semantic whole-graph digest.
4. Candidate totals reconcile with unattributed counts and per-rule/per-clause rows; Term totals reconcile with explicit unattributed counts and variant counters; ambiguous rule IDs have no per-rule rows.
5. Audited access traces have zero dropped events and aggregate rows sum to the native event total; uninstrumented arms have no audit/trace output.
6. Both replicates at each size reproduce exactly in discrete work profiles. Wall time and RSS are reported descriptively and are not gates on an asymptotic claim.
7. Added Concepts receive no classification edges and do not alter the expected output. Any semantic change censors that size cell as a controlled distractor sweep.

## Interpretation boundary

A passing sweep is evidence about one live full-seed route and one vocabulary-membership axis. It is not a natural task distribution, learned-frame/cheap-cut test, task-size sweep, or general capability result. Compare full-request candidate work and Term work separately from access events, wall/CPU, and peak RSS. The known missing graph-visible outbound Message is recorded as a separate behavior observation.

## Reproduction

Generate the source lock with `PYTHONPATH=runners/dsl/python:. python3 scripts/substrate_live_describe_scene_live_scale_v1.py --lock`; store its `locked_inputs` object at the declared lock path. Run with `PYTHONPATH=runners/dsl/python:.:scripts`, `OZMA_NO_LLM=1`, and `OZMA_SEED_PERSIST_DISABLED=1`. Use the independent analyzer linked from the result.
