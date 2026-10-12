# Live runtime rule-set census v1 — results (2026-10-04)

## Result

The preregistered offline census passes its integrity and accounting gates on replicate 0, audit-on, from the v1.6 live capture. It retains all 2,357 baseline rule definitions and classifies each against the existing finite-key insertion checker: 2 accepted, 15 rejected, and 2,340 explicitly outside the checker schema because they have a non-null `where` term. The accepted rules are `select_operator` (RuleUID 2) and `bind_role` (RuleUID 3); both have zero attributed candidate-pair, candidate-test, and Term work in both captured requests.

For `report your organisation`, the 74,742 candidate pairs and 74,534 tests partition into 74,138/74,138 for baseline definitions, 37/37 for six primary-store post-export rules without bodies, and 567/359 across secondary stores without exported bodies. Of 805,415 Term evaluations, 803,519 are attributed to baseline definitions, 156 to those primary-store rules, 1,595 to secondary-store rules, and 145 to direct host `Substrate.evaluate` calls. For `describe who you are`, the 36,082 candidate pairs and 36,072 tests partition into 35,928/35,928 baseline, 93/93 primary post-export, and 61/51 secondary; of 374,222 Term evaluations, 373,461 are baseline, 371 primary post-export, 256 secondary, and 134 direct host calls. Unattributed no-rule and ambiguous Term counts are zero in both.

## Coverage and limits

The first request's identity snapshot crosswalks all 2,357 baseline definitions. The second crosswalks 2,344; 13 baseline definitions are absent from that snapshot and are explicitly marked unobserved for that request. Their zero-filled work fields are not evidence of zero execution. Six post-export primary-store rule identities per request and 18/14 secondary-store identities have no full definition bodies in this capture. The primary store is uniquely identified by exact local-index, name, and match-arity crosswalk for each prompt.

This static checker classification uses the final captured graph as its reference and is not a replay or a termination proof. The two admitted rules had no measured work on this selected authored route, so the result does not show that the finite-key fragment accounts for productive live closure. It is one full-seed, two-request route; it does not estimate natural workload frequency, hidden-rule termination, frame locality prevalence, or general tractability.

## Reproduction

- Preregistration: [protocol](SUBSTRATE_LIVE_RUNTIME_RULESET_CENSUS_V1_PREREG_20261004.md)
- Runner: [live runtime census](../../../evaluation/substrate_capability/live_runtime_ruleset_census_v1.py)
- Independent analyzer: [census analyzer](../../../evaluation/substrate_capability/analyze_live_runtime_ruleset_census_v1.py)
- Source lock: [locked inputs](../../../evaluation/substrate_capability/live_runtime_ruleset_census_v1_lock_20261004.json)
- Profile: [machine-readable census](../../../evaluation/reports/live_runtime_ruleset_census_v1_20261004.json)
- Independent analysis: [analysis output](../../../evaluation/reports/live_runtime_ruleset_census_v1_analysis_20261004.json)
- Parent runtime capture and analysis: [v1.6 results](SUBSTRATE_LIVE_RUNTIME_CLOSURE_COUNTERS_V1_6_RESULTS_20261004.md)

The runner locks the protocol, runner, analyzer, finite-key checker, and v1.6 capture/lock/analysis. It refuses a stale lock. Reproduce from the repository root with `python3 evaluation/substrate_capability/live_runtime_ruleset_census_v1.py`, then run `python3 evaluation/substrate_capability/analyze_live_runtime_ruleset_census_v1.py`.

## Next measurement

The next closure measurement should execute exported runtime rule definitions against their captured pre-request graph, preserving rule conditions, insertion order, and hidden-rule boundaries, then compare the native closure result and work counters with the original live route where observable. First resolve the 13 missing second-prompt identities and determine whether the capture can export post-boot and secondary-store bodies. If exact replay cannot be reconstructed, retain this result as an overlap/coverage census and sample a new runtime capture with those exports added; do not infer natural-task frame structure from the current graph alone.
