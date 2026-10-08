# Grounded concern-dispatch probe v1.3 results

**Run:** 2026-09-28; four unique fresh full-seed processes, two per condition.  
**Protocol:** [v1.3 preregistration](SUBSTRATE_GROUNDED_CONCERN_DISPATCH_V1_3_PREREG_20260928.md).  
**Evidence:** [raw capture](../../../evaluation/reports/grounded_concern_dispatch_v1_3_20260928.json), [independent analysis](../../../evaluation/reports/grounded_concern_dispatch_v1_3_analysis_20260928.json), [source/input lock](../../../evaluation/substrate_capability/grounded_concern_dispatch_v1_3_lock_20260928.json), [runner](../../../scripts/substrate_grounded_concern_dispatch_v1_3.py), [analyzer](../../../scripts/analyze_substrate_grounded_concern_dispatch_v1_3.py).

## Result

All 14 independent integrity and semantic gates pass. Every worker has stable source/runtime inputs, loads 731 seeds with 11 reported boot failures, and records zero teacher calls.

| Condition | Route | Outcome | Rule delta | Median task wall time |
|---|---|---|---:|---:|
| Preconstructed `compare` instruction with the authored comparison text | `concern_authored` (2/2) | Same signature in both workers: `[['pairwise','PARTS'], ['judge','TRIAL','by','RESULT']]`; new concern minted and grounded as `experiment_rule` | 1 | 2.579 s |
| `walk` instruction with “Walk to the door.” | `goal_only` (2/2) | No concern object; action-space limit is reported honestly | 0 | 0.743 ms |

Task timing starts at `act_on_instruction` and excludes full-seed boot. Positive timing includes lazy setup and execution of the concern induction/grounding path; it does not isolate individual internal operations. These four observations are descriptive, not a stable performance estimate.

## Interpretation and limits

This confirms that the current action/faculty path, given a constructed concern-framing instruction, invokes concern induction and grounding and returns the same teacher-free concern signature in both workers. The natural-language panel fails before this point: it produces no goal and makes no action call. This gives separate evidence for downstream grounded concern induction and the unresolved text-to-dispatch route.

V1.0 is retained as a partial serialization failure because native `NodeID` values were not JSON serializable. V1.1 captured positive outputs but its control retained concern verbs in the raw text, so it cannot establish a control contrast. V1.2 captured the intended contrasting inputs, but a protocol body discrepancy means it is exploratory, not confirmatory; see [capture amendment](SUBSTRATE_GROUNDED_CONCERN_DISPATCH_V1_2_CAPTURE_AMENDMENT_20260928.md). V1.3 locks the exact prompts in the protocol and runner and is the confirmatory result.

This remains one manually constructed representation and one authored signature. It does not establish that the concern is correct for a real trial, general induction, transfer, natural-language comprehension, or prevalence. Next, construct a grounded trial state with an independent semantic oracle and test whether the generated `experiment_rule` judges that state correctly.
