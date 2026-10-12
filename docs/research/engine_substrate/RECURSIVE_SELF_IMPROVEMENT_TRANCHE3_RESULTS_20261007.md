# Recursive self-improvement, tranche 3: results (2026-10-07)

Follows the [tranche 2 results](RECURSIVE_SELF_IMPROVEMENT_TRANCHE2_RESULTS_20261007.md).

## Summary

| Item | Result |
|---|---|
| Promote → author path | **Fixed.** A flagged concern now mints exactly one conversation Experiment from the agent's own author rule. `test_flag_promote_experiment_judge_adopt_closes` passes. |
| Self-authored chain feeds credit | **Works, end to end, one example.** Every step after the human promote now runs without host-minted records: flag, promote, the agent's own author rule, a real child replay (45 s), the agent's own judge (supported, adopt_ready), then a credit derived from that verdict. |
| Grain ladder for held generators, held-out | **Confirmed (preregistered).** On disjoint Omniglot evaluation alphabets, jittered drawings are recognised 60/100 versus 0/100 without the ladder (95% CI 50–70%), with 0/100 false recognitions across characters (upper bound 3.6%). A different person's drawing of the same character: 29/100 versus 0/100. |
| Chunk retention, sparse stream | **Capacity must exceed churn.** With 10% recurrence, capacity 16 keeps recall 4/4 at 22% of unbounded probe work. Capacities 8 and 4 lose one task. |
| Real-judge adoption gate | **Not run: it cannot discriminate yet.** In production, each conversation concern kind has one eligible variation family, two for `instruction`. Credit therefore has nothing to choose between. |

## Promote → author: the bug and the fix

Commit `3529fe4d` removed two guards from the experiment author rule built by `_compose_experiment_rule`: the concern's own `capability_keys`, and requiring `"test"` in `residual_predicates`. The aim was to let it act as a standing consumer of later residuals. Two problems followed:

1. **The daemon scrubbed the rule.** `_scrub_stale_author_rules` still treats an author rule without those guards as stale and removes it. That leaves a promoted conversation concern with no author rule.
2. **The ARC consumer took the axis.** The unguarded standing rule `standing_self_improvement` (an ARC rule) bound the promoted conversation axis first, minted a `navigate` experiment, and `_cancel_unscoped_experiments` then cancelled that. The conversation concern never got an Experiment.

Fix:

- **Conversation-replay family only.** Its author rule is scoped again to its own concern, because its delta is concern-specific. The scope uses list membership (`In(key, capability_keys)`), not list `Eq`. A rule literal list round-trips as a Tuple while the axis attribute is a List, so `Eq` was always false; this was found during the fix.
- **All other author rules.** The Python composer and both branches of `seeds/composer_experiment_graph.json` (v1.1.0) now refuse axes whose `residual_predicates` contain `replay`. Only a replay experiment can test those axes. The standing-consumer intent of `3529fe4d` is otherwise kept.
- **Test change.** `tests/capability/minting/test_recurrence_control.py` was updated for the new exclusion. It still asserts the standing consumer has no `"test"` restriction.

`test_agent_authors_new_rule_end_to_end` now passes the author, dispatch, judge, adopt and teach steps. It still fails at its last step, which is independent of the experiment machinery:

- A fresh full-seed agent with the adopted `condense → comprehend_text` route Concept replies "ERROR: no communicative response could be generated." The graph did produce a reply, "I read it and modeled it internally. It says: data", but the production gate refuses it because the surface lacks the event word.
- The child replay judged that same change as "flagged turn changed", i.e. fixed. **So the judge counts a change as a fix even when the new reply is a refused or error surface.** This is a judge weakness, not a credit-rule one.

## Held-out grain confirmation

[Preregistration](SUBSTRATE_DIMINFER_GRAIN_HELDOUT_V1_PREREG_20261007.md), [report](../../../evaluation/reports/diminfer_grain_heldout_v1_20261007.json).

Setup: 20 evaluation alphabets × 5 held maps; drawer 1 is the base. Recognition means `recognized_transformed` with the base as `covered_by`.

| condition | off | ladder `[0,1,2]` | ladder grains |
|---|---:|---:|---|
| exact | 100 | 100 | all 0 |
| jitter ±0.35 cell | 0 | 60 | 1: 10, 2: 50 |
| different drawer | 0 | 29 | 1: 5, 2: 24 |
| cross-character | 0 | 0 | — |

All three gates (H1–H3) pass. Median closure is 2.3 ms off and 3.6 ms with the ladder.

This supports making `dim_grains=[0,1,2]` the default on vision routes that use the held generator codebook. That change is not made here.

## Sparse retention

[Report](../../../evaluation/reports/chunk_retention_sparse_v1_20261007.json).

The stream had 120 episodes. Each recurring task appeared once or twice, 6 recurring episodes in total; the rest were one-off distractors. Each episode presents a length-2 prefix and then a length-3 target.

| arm | recall | live chunks | probe candidates |
|---|---:|---:|---:|
| unbounded | 4/4 | 50 | 8,406 |
| capacity 16 | 4/4 | 16 | 1,878 |
| capacity 8 | 3/4 | 8 | 1,014 |
| capacity 4 | 3/4 | 4 | 678 |

Capacity has to exceed the number of distractor chunks minted between a task's recurrences. On the tranche 2 dense stream, capacity 4 was enough; here 16 is needed. A fixed capacity is not a sufficient policy for real streams.

## Real-judge gate: why it was not run

I checked eligible families by refuting each pick in turn (`variation_pick` with the production conversation heads):

| concern kind | families offered, in order |
|---|---|
| reply_fix | reply_ablation |
| performance | reply_ablation |
| comprehension | reply_ablation |
| instruction | cue_set_edit, reply_ablation |

With one family per kind, outcome credit cannot change which family is tried. A 12 × 30 real-judge adoption gate would therefore measure nothing about the credit rule, at about 5–10 hours of child time per arm.

The other families (`knob_edit`, `rule_literal_edit`, `datum_feedback_rule`, `shape_mint`, `structural_edit`, `threshold_shift`) exist, but their cue heads (`bound`, `ruleliteral`, `datumfeedback`, `shapemint`, `structure`, `gradient`) are never added to a promoted conversation concern's relations.

The prerequisite for a real-judge credit gate is a promote step that gives a concern more than one applicable family. The credit rule itself is ready: the self-authored chain above shows it consuming a real verdict.

## Regression

Each test file ran in its own process with a 30-minute timeout. The single batched run had timed out at 84%.

- **Tranche 1–2 scope (93 files):** 1,038 passed, 39 failed. All 39 failures are in the tranche 1 baseline set, so no new failures. One baseline failure now passes: `test_comprehension_self_optimisation_migrated.py::test_exhausted_experiments_trail_surfaces_in_status`.
- **15 additional files touching the composer and promote path:** run both with this tranche's three edits and with them reverted.
  - No new failures.
  - Five tests that failed with the edits reverted now pass: `test_flag_promote_experiment_judge_adopt_closes`, `test_reply_fix_experiment_subcase_reaches_the_genuine_composer_untouched`, and three parametrisations of `test_instruction_performance_comprehension_never_reach_the_generic_fallback`.
  - `test_residual_promote_migrated.py` timed out after two tests in both runs.
  - The 9 `test_experiment_composer_graph.py` failures predate this tranche. They fail identically with the edits reverted.
- The full `-k migrated` suite was not run.

## Next

1. **Fix the replay judge.** Count a flagged turn as fixed only if the new reply passes the production gate, not merely if it changed.
2. **Give promoted concerns more than one applicable family.** Emit the cue heads for the other variation families when the concern's evidence supports them. Then run the real-judge credit gate (budget about 5–10 hours of child time per arm).
3. **Make the held-generator grain ladder a vision-route default,** now that it is confirmed on held-out drawings, and check it on the live vision tests.
4. **Replace fixed chunk capacity with a recurrence-aware rule,** for example retiring chunks by time since last use against observed recurrence intervals. Measure it on the sparse stream.
