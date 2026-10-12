# Conversation task-scope local-pattern matcher v1.6 results

Date: 2026-10-03

## Scope and method

This is an exploratory implementation evaluation, not a preregistered speedup study. It adds a guarded multi-edge ownership-seeded matcher for graphs with no prior edge deletions. For each owned node and each pattern variable with a matching incident edge, the runner prebinds that variable, enumerates extensions, retains bindings touching the scope, deduplicates them, and restores the original recursive match order by sorting on the matched `EdgeIdx` sequence. Once any edge deletion has occurred, it uses the prior full matcher and ownership filter. The matcher path has its own counter.

The unchanged v1.5 workload runs in nine fresh workers across ascending, descending, and outside-in frame orders. Each worker compares monolithic closure with scoped trace-off and trace-on closure over four authored cases. Inputs include the new matcher/audit sources, analyzer, runner, and rebuilt native engine in the lock.

## Results

All nine worker and source-stability gates pass. Independent analysis passes with zero errors: 36/36 final graphs and 594/594 checkpoint graphs match; goal states and trace-on/off state match throughout. The new local-pattern path is exercised 8,520 times. The scoped fallback is still exercised 26,400 times, primarily after the first edge deletion disables the guarded ordering path.

| Measure | Monolithic | Scoped v1.5 | Scoped v1.6 | v1.6 ratio |
|---|---:|---:|---:|---:|
| Candidate visits | 18,072 | 164,985 (9.13×) | 170,853 (9.45×) | 9.45× |
| Term evaluations | 51,552 | 575,808 (11.17×) | 654,438 (12.69×) | 12.69× |

Candidate work rises 3.6% and Term work rises 13.7% from v1.5. The implementation therefore preserves measured state but does not improve measured work on this workload. Additional seed traversals and trace callbacks add work; only part of scoped execution reaches the new path before deletion forces fallback.

The observed trace multiplicity in the traced arm is 173,640, versus 153,564 in v1.5. The new matcher re-enumerates successful patterns, so trace multiplicity is matcher-visit instrumentation, not a count of unique graph accesses. It must not be interpreted as increased semantic access.

## Interpretation and next measurement

The exact parity result supports this ordering reconstruction for the tested deletion-free segments and cases. It does not prove correctness for every graph layout, deletion/reuse history, rule pattern, or effect sequence. The guarded fallback preserves the old behavior where the ordering precondition is not established.

The v1.6 path is not ready for adoption as a performance optimization. V1.7's per-rule counters show all measured candidate/Term work belongs to the four discourse lifecycle rules; resolve, select, execute, and fail contribute 46,467/44,547/44,247/35,592 candidate visits respectively. This still does not separate local-pattern from fallback work or closure epochs. Next add path-by-rule/epoch attribution, then compare all-variable seeding, a semantically justified single-anchor seed, and full fallback under a preregistered gate requiring exact states and lower candidate and Term work. Do not claim wall-time speedup without a separately controlled timing study. See [v1.7 cost attribution](SUBSTRATE_CONVERSATION_TASK_SCOPE_COST_ATTRIBUTION_V1_7_RESULTS_20261003.md).

## Provenance

- Runner: [conversation_task_scope_parity_pilot_v1_6.py](../../../evaluation/substrate_capability/conversation_task_scope_parity_pilot_v1_6.py)
- Independent analyzer: [analyze_conversation_task_scope_parity_pilot_v1_6.py](../../../evaluation/substrate_capability/analyze_conversation_task_scope_parity_pilot_v1_6.py)
- Source lock: [v1.6 lock](../../../evaluation/substrate_capability/conversation_task_scope_parity_pilot_v1_6_lock_20261003.json)
- Capture: [v1.6 capture](../../../evaluation/reports/conversation_task_scope_parity_pilot_v1_6_20261003.json)
- Analysis: [v1.6 analysis](../../../evaluation/reports/conversation_task_scope_parity_pilot_v1_6_analysis_20261003.json)
- Prior baseline: [v1.5 order-parity results](SUBSTRATE_CONVERSATION_TASK_SCOPE_ORDER_PARITY_V1_5_RESULTS_20261003.md)
