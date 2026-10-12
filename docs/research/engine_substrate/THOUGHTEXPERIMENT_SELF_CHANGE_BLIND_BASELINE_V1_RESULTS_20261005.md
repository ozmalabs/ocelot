# Graph-native blind self-change baseline v1 results

All independent gates pass across three fresh workers and 21 case executions. For each case, the runner replaced the descriptive case ID with an opaque identifier and passed the graph only observed signals, common candidate-clause representations, and later candidate/no-op/placebo measurements. The runner did not import the test module's hidden expected-family mapping.

The native graph rules generated and scored candidate families as follows:

| Outcome | Per worker | Total |
|---|---:|---:|
| Select a proof-admissible family in the five single-candidate cases | 5/5 | 15/15 |
| Select the minimum-MDL family when two candidates pass | 1/1 | 3/3 |
| Reject all candidates and issue `no_causally_supported_patch` abort | 1/1 | 3/3 |

In the ambiguous case, the relation candidate has higher measured gain (31 vs 29), but both clear the no-op/placebo margins and other proof checks. The graph selector chooses `threshold_adjustment` at MDL cost 1 over `relation_addition` at cost 3. The correlation-only control yields no admissible candidates under the seed's strict >5 margins over both controls, and the graph emits an abort after the evidence batch closes. Independent analysis recalculates admissibility from the recorded measurements and thresholds rather than trusting runner labels.

Median time for the graph's evidence-selection tick is 0.090 ms (range 0.066–0.186 ms over 21 calls). This excludes boot, FaultProbe interpretation/candidate minting, generation of candidate clauses, and external acquisition of measurements. The five ordinary cases expose only one candidate each; the two-candidate ambiguous case is the only minimality competition. Thus the result establishes a small graph-native selection/proof/abstention path, not broad hypothesis search.

The policy is not passed an expected family or corrective answer. However, the harness supplies the candidate representations and measured outcomes, and the task family is authored around the five seed hypothesis families. The run does not test candidate invention, causal measurement acquisition, correctness against external task behavior, target UID binding to a live rule, RulePatch adoption, restart survival, or self-improvement. It is a measured baseline for the learning stage, not evidence that rung-three induction is solved.

## Reproduction artifacts

- [Preregistration](THOUGHTEXPERIMENT_SELF_CHANGE_BLIND_BASELINE_V1_PREREG_20261005.md)
- [Runner](../../../evaluation/substrate_capability/thoughtexperiment_self_change_blind_baseline_v1.py)
- [Analyzer](../../../evaluation/substrate_capability/analyze_thoughtexperiment_self_change_blind_baseline_v1.py)
- [Source lock](../../../evaluation/substrate_capability/thoughtexperiment_self_change_blind_baseline_v1_lock_20261005.json)
- [Capture](../../../evaluation/reports/thoughtexperiment_self_change_blind_baseline_v1_20261005.json)
- [Analysis](../../../evaluation/reports/thoughtexperiment_self_change_blind_baseline_v1_analysis_20261005.json)
