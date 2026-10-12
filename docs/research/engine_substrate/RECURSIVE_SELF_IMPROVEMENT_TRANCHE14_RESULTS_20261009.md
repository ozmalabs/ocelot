# Recursive self-improvement, tranche 14: results (2026-10-09)

Follows the [tranche 13 results](RECURSIVE_SELF_IMPROVEMENT_TRANCHE13_RESULTS_20261009.md).

## Summary

| Item | Result |
|---|---|
| The tranche-13 `alphabetise` miss | **Diagnosed and fixed.** Steering promoted the wrong concern. "Work on the alphabetise data gap." picked an older shadow-read `comprehension` concern that quotes an earlier steer turn and shares only the word "data". `conversation_steering` v1.2.0 now promotes the concern with the most matched words (ties: oldest). |
| **Mixed-kind credit gate v2** ([prereg](SUBSTRATE_VARIATION_CREDIT_MIXED_KIND_V2_PREREG_20261009.md)) | **PASS on all four gates.** With a misordered family that really dispatches, credit cut the reported kind from 8 replays to 5 (both 4/4 handled) and left the instruction kind unchanged (4/4 in 6). It moved both later reported first picks to the working family, with 0 false adoptions. |
| `rule_literal_edit` proposed variants it could never adopt | **Found by the gate and fixed.** It picked the agent's own runtime `author_experiment_from_residual_*` rule, which has no seed provenance, so the adoption gate would always deny it; with exclusion off it re-proposed the same literal 3 times. It now proposes only adoptable rules and skips rules already tried for the concern. |
| Self-filed concern census v2 | **Natural conversation still yields almost no experiment concerns.** On 258 persona-chat turns: 35 concerns with shadow read off, 38 with it on. 1 and 2 respectively take the experiment pipeline, all others are `knowledge`. Boot-integrity spam is gone (11 in tranche 5). |
| Regression | **0 new failures** across 219 files, compared against the same files with this tranche's two source changes reverted. |

## 1. The `alphabetise` miss

Diagnosis: `/tmp/pfv14/alpha_diag.py` replayed the tranche-13 C arm up to stream position 6.

| Step | Observed |
|---|---|
| Floor | "I understood that as an instruction to alphabetise 'data', but I hold no faculty for it yet…" — the gap is filed. |
| Steer | "Promoting: comprehension classified this as 'instruction' but the deep reader heard 'statement' (recurring; e.g. "Work on the condense data gap.")" |
| Promoted concern | kind `comprehension`, filed by shadow read after the recurring steer phrasing |
| Its author rule | `comprehend_describe_directive_…`, not an experiment author, so no experiment was ever requested |
| Alphabetise concern | still `noted` |

Cause: `steer_promote_concern` chose `Argmin(node id)` among noted concerns that share **any one** non-stop word with the turn. The older comprehension concern shares "data" because it quotes a steer turn.

Fix: `seeds/conversation_steering.json` v1.2.0, emitted by `scripts/gen_steer_best_match.py` (idempotent).
- The rule now computes `MaxOver` of the exact count of the turn's non-stop mention words found in each candidate's content.
- It promotes the oldest candidate with that maximum.
- When only one candidate matches, the result is the same as before.

Test: `test_nl_steering_migrated::test_steer_promotes_the_best_matching_concern_not_the_oldest`. It fails against v1.1.0 and passes against v1.2.0; the other 11 tests in the file pass.

This only showed up with shadow read on. The v1–v3 credit gates ran without it, and the tranche-13 gate was the first stream long enough for the divergence concern to be filed.

## 2. Mixed-kind credit gate v2

The design was changed from v1 so that the wrong prior has a real cost:
- The reported concerns also name "hardcoded … floor". That makes `rule_literal_edit` eligible, and it **builds** a variant (checked by builder calls before the prereg).
- `rule_literal_edit.priority = 8`, ahead of `knob_edit` (15).
- The instruction kind keeps its held order and serves as the cross-kind check.
- Three arms isolate credit from the exclusion policy.

| Arm | Instruction handled (experiments) | Reported handled (experiments) | Later reported first pick = `knob_edit` | False adoptions |
|---|---|---|---|---|
| A: no credit, no exclusion | 4/4 (6) | **0/4 (12)**: `rule_literal_edit` three times per concern | 0/2 | 0 |
| B: exclusion, no credit | 4/4 (6) | 4/4 (8): `rule_literal_edit` inconclusive, then `knob_edit` supported, every concern | 0/2 | 0 |
| C: credit + exclusion | 4/4 (6) | **4/4 (5)**: `rule_literal_edit` once (concern 1), then `knob_edit` first on concerns 3, 5, 7 | **2/2** | 0 |

| Gate | Condition | Result |
|---|---|---|
| G1 | C saves replays on reported: 5 < 8, handled 4 ≥ 4 | pass |
| G2 | no cross-kind harm on instruction: 4 ≥ 4, 6 ≤ 6 | pass |
| G3 | 0 false adoptions in B and C | pass |
| G4 | C's later reported first picks are both `knob_edit` | pass |

What this shows:
- **Exclusion alone** recovers the reported kind (A → B: 0/4 → 4/4) but pays one wasted replay per concern.
- **Credit** removes that recurring waste after the first trial (B → C: 8 → 5 experiments), without touching the instruction kind.
- **Credit is keyed per kind and did not leak across kinds.** The instruction stream is identical in all three arms.

This is the first real-verdict demonstration that credit saves replays on a mixed stream. It addresses the tranche-13 finding that credit's value had become ordering only. Caveat: one deterministic stream per arm, 4 concerns per kind.

The steering fix in §1 is in every arm, and `alphabetise` is now handled in all three.

## 3. `rule_literal_edit` fixes

In every arm, the misordered family's variant edited a literal in `author_experiment_from_residual_promoted_self_concern_25606`. That is the agent's own runtime-authored experiment-author rule for concern 1 (condense).
- It has no seed provenance, so `_rule_denylisted` would deny adopting it.
- A replay of conversation turns cannot observe it anyway, so it was always inconclusive.
- With `exclude_inconclusive` off (arm A), the builder re-proposed the same literal three times per concern.

Fix in `_compose_rule_literal_variant`:
- **Adoptable only.** A candidate needs a `from_seed` whose `SeedSummary.skippable == 1`, the same condition the adoption gate checks. The builder no longer proposes a variant it could never adopt.
- **Tried exclusion.** A rule already judged refuted or inconclusive for this concern under this family is skipped. This is the twin of the tranche-7 knob exclusion.

On the same concern the pick now goes to an adoptable seed rule (`steer_promote_concern`).

Test: `test_rule_literal_pick_is_adoptable_and_skips_tried_rules`. All 18 tests in `test_rule_literal_variation_migrated.py` pass.

The gate in §2 ran **before** this fix. Its arms A and B counts include the waste the fix removes. The gate's conclusion, that credit saves replays, does not depend on which rule the misordered family edits.

## 4. Census v2

Runner: `evaluation/substrate_capability/self_filed_concern_census_v2.py`, with the same corpus as v1 (persona_chat_20, User 1, 258 turns).

| Arm | Concerns | By kind | Experiment pipeline |
|---|---|---|---|
| v1 (tranche 5) | 46 | 34 knowledge, 11 boot_integrity, 1 instruction | 1 |
| v2, shadow off | 35 | 34 knowledge, 1 instruction | 1 |
| v2, shadow on | 38 | 36 knowledge, 1 instruction, 1 performance | 2 |

The only change since tranche 5 is that boot-integrity concerns are gone (tranches 8 and 11). The `performance` concern is the shadow-latency gap. Everything the self-improvement loop has been measured on still comes from steered or reported concerns, not from natural conversation. Knowledge gaps route to `comprehend_first`, which is the learning path, not self-modification, and that is correct.

## 5. Regression

The scratch area from earlier tranches (`/tmp/pfv14`: the scope list, runner and baseline failure sets) was gone at the start of this tranche, so the regression was rebuilt.

**Scope.** 219 test files, selected by keyword: any test referencing `reflective_faculty`, `variation_*`, `experiment_dispatch`, `convo_child_run`, `jabberwock_daemon`, `shadow_read`, the seeds changed in tranches 6–14, `interlocutor_model`, `reading_drive`, `domain_data`, `knob_edit` or `cue_set_edit`. This is close to, but not the same as, the 221-file scope of tranches 11–13.

**Baseline.** A first baseline from a clean `git worktree` of HEAD was discarded. It showed 393 failures, because untracked data the tests read (`results/`, `data/`, and so on) is not in a worktree. Instead:
1. ran the scope on the tranche-14 tree (150 failures in 59 files);
2. temporarily restored the two changed source files (`domains/reflective_faculty.py`, `seeds/conversation_steering.json`) to HEAD;
3. reran those 59 files.

**Result: 0 new failures.** The comparison first flagged 9 tests. They were artefacts of the HEAD rerun hitting the 1800 s per-file timeout:
- 7 failed in the HEAD rerun before the timeout, mapped from pytest progress output to collected test order: 3 in `test_curriculum_study_migrated`, 3 in `test_ground_concern_six_kinds_migrated`, and `test_nobel_leak_gone…`, which has been pre-existing since tranche 11.
- The remaining 2 (`test_nl_surface_what_blocks_your_learning_nonempty` and the `comprehension` case of `test_instruction_performance_comprehension_never_reach_the_generic_fallback`) were run on their own on both trees. **They fail identically on HEAD.**

`test_autonomous_cycle` timed out on both trees. The run rewrote `tests/fixtures/comprehension_divergence/divergence.json` (latency values only), and it was restored. The seeds the probes could write to were byte-identical after every run.

## Next

- **Natural concern supply.** Natural conversation yields 1–2 experiment-pipeline concerns per 258 turns. Find which self-observations could become reported-kind concerns, for example reform rates or repeated gap floors, without hand-filed text.
- **Protect the agent's own pipeline rules** from every variation family, not only `rule_literal_edit`. Self-authored per-concern rules are not adoptable and cannot be observed by the replay.
- Reproduce gate v2 on a second stream order.
