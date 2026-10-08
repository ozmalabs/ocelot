# Live describe-scene whole-request audit v1 preregistration

Date: 2026-09-27

## Question

Can native candidate and Term work be attributed over the complete live `converse` call, rather than only its three Goal-event producer closures, while preserving exact output and final-graph behavior?

## Design

Run three fresh-process pairs on the current full-seed source and native build. Each worker cold-boots the same seeds, attaches the same three-Percept Scene, and makes one `describe what you see` instruction request. The audited arm resets and enables global/per-rule matcher counters and runtime access tracing immediately before the entire `converse` call; it disables and snapshots all three immediately after. The paired control runs the identical request with all instrumentation off. Run order is fixed within each pair; pairs use randomized arm launch order. No request runs concurrently with another.

Record full-graph semantic digest and node/edge counts, public reply, Goal lifecycle projection, candidate and Term totals, per-rule/per-clause attribution, matcher metadata, access-trace totals by rule/resource, and wall/CPU time. Semantic graph hashing excludes only the volatile `SystemModel.ts` and `SystemModel.runtime_s` fields, matching v2.4.

## Gates

1. Three distinct audited and three distinct control PIDs; current source/native fingerprints stable at worker start/end and after capture.
2. Every worker reaches exactly one request Goal with resolved `selection → execution → action_result` lifecycle and the expected public description.
3. Each pair has exact public reply, lifecycle projection, and whole-graph semantic digest equality.
4. Audited candidate totals reconcile as `cand_tested = attributed + unattributed`; per-rule and per-clause candidate sums equal attributed work; metadata IDs and clause arities validate; Term totals reconcile globally, per-rule, and by Term kind.
5. Access tracing has no dropped events, and its total equals the sum of its rows. The access trace is a complementary operation view; do not equate access events with candidate tests.
6. Report uninstrumented and audited wall/CPU separately. Do not use instrumented timings as baseline cost.

Any failed gate censors the corresponding claim. A passing run estimates complete measured native matcher work for this one serial live route, not natural-workload prevalence, learned frame locality, generalization, or scaling.

## Reproduction

Run `python3 scripts/substrate_live_describe_scene_whole_request_audit_v1.py --lock` with `PYTHONPATH=runners/dsl/python:.`, save the emitted `locked_inputs` object to the declared lock, then run the script with `PYTHONPATH=runners/dsl/python:.:scripts`, `OZMA_NO_LLM=1`, and `OZMA_SEED_PERSIST_DISABLED=1`. Analyze with the independent analyzer linked from the result report.
