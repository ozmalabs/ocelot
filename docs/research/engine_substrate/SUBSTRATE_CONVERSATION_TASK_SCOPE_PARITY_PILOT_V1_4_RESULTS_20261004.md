# Conversation task-scope parity pilot v1.4 results

Date: 2026-10-04  
Status: exploratory, source-locked capture; independent analysis passes.

## Question and method

V1.3 showed that scoped closure had operation markers but no scoped-loop details. Source review found that scoped closure uses a separate full-sweep loop in `rewrite.rs`; the monolithic scheduler hooks in `substrate.rs` cannot describe its rule scans. V1.4 adds a scoped operation boundary around `run_rules_scoped` and separate native work event kinds for scoped passes, active-rule attempts, and progressing rules. These are explicitly distinct from monolithic scheduler slots. The experiment otherwise repeats the same authored cases and parity protocol.

The provenance-current engine is `4c22274eee66`. The three-worker capture passes all nine runner gates. Independent analysis passes with no errors, verifies the complete direct source lock (including `term.rs`), 12/12 paired cases, 198/198 checkpoint pairs, no work-trace drops, and the expected scoped event kinds. The partition scopes still reach zero-progress quiescence with no deferred effects.

## Work measurements

The following work totals are aggregated across three fresh workers. Search counters are directly comparable across closure modes; scoped-loop event kinds and monolithic scheduler event kinds describe different algorithms and should not be ratioed to each other.

| Goals | Candidate pairs: monolithic / scoped | Term evaluations: monolithic / scoped | Scoped passes | Scoped rule attempts | Scoped progressing rules |
|---:|---:|---:|---:|---:|---:|
| 2 | 357 / 1,107 | 1,212 / 4,041 | 144 | 540 | 18 |
| 4 | 1,158 / 6,750 | 3,480 / 23,526 | 528 | 2,040 | 36 |
| 8 | 4,092 / 46,140 | 11,184 / 156,444 | 2,016 | 7,920 | 72 |

At eight goals, global resweeping performs 11.28× as many candidate pairs and 13.99× as many Term evaluations as monolithic closure. The new scoped event rows make its loop structure visible: 2,016 passes and 7,920 active-rule attempts across three workers. They do not include binding counts; candidate and Term counters remain the common work measures.

## Interpretation and next work

The new trace closes the instrumentation asymmetry for loop/pass and rule-attempt counts. It does not make the two scheduling strategies equivalent, nor does it reduce the measured excess search work. Exact-state parity is established only for explicit, symmetrically annotated scopes on the authored conversation fixtures. Learned partition discovery, dependency completeness, coupled cross-frame changes, natural-task prevalence, and speedup remain unestablished.

Next extend the work accounting to scoped matching branches and binding filtering, then derive scope candidates from runtime activation and dependency traces without injected ownership annotations. Include cross-frame/shared-state mutation controls and charge partition discovery plus closure. Expand to independent task families before making a general locality claim.

Artifacts: [preregistration](SUBSTRATE_CONVERSATION_TASK_SCOPE_PARITY_PILOT_V1_4_PREREG_20261004.md), [runner](../../../evaluation/substrate_capability/conversation_task_scope_parity_pilot_v1_4.py), [analyzer](../../../evaluation/substrate_capability/analyze_conversation_task_scope_parity_pilot_v1_4.py), [source lock](../../../evaluation/substrate_capability/conversation_task_scope_parity_pilot_v1_4_lock_20261004.json), [capture](../../../evaluation/reports/conversation_task_scope_parity_pilot_v1_4_20261004.json), and [independent analysis](../../../evaluation/reports/conversation_task_scope_parity_pilot_v1_4_analysis_20261004.json).
