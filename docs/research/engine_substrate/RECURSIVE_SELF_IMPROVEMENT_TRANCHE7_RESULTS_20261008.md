# Recursive self-improvement, tranche 7: results (2026-10-08)

Follows the [tranche 6 results](RECURSIVE_SELF_IMPROVEMENT_TRANCHE6_RESULTS_20261008.md).

## Summary

| Item | Result |
|---|---|
| Content-conditioned instruction routes | **Done.** A route Concept can carry `route_object_scope:"other"`. It then claims "<verb> the data" but not "<verb> yourself". Every cue edit is now proposed scoped this way. |
| Real-judge panel v1.4 (8 cases, two of them guarded) | **8/8 repaired, 0 false adoptions, 2/2 guarded self turns preserved byte-for-byte.** In tranche 6 the guarded `summarise` case was correctly declined. It is now repaired. |
| Shadow read was dead (pre-existing bug) | **Fixed.** `reading_drive._LAAdapter` lacked the adapter lock, so every shadow read of a chat turn raised and was swallowed as `shadow_error=1.0`. All `shadow_read`-gated per-turn modelling depended on it: reform marks, interlocutor corrections, document-topic span. |
| `datum_feedback` authored no experiment | **Fixed.** A routing cause in the composer, plus the dead shadow read. Real judge: **supported and adopted** (n=1). |
| `knob_edit` inconclusive | **Fixed.** A knob-sensitive corpus, knob exclusion on retry, and opt-in agent retry for reported concerns. Real judge: the third attempt was **supported and adopted** (n=1). |
| `shape_mint` empty delta | **Diagnosed, not fixed.** No party in any corpus tried falls below the shape-fit floor, so there is no poor-fit datum to mint from. |
| Multi-family credit on real verdicts | **Feasibility only.** One reported concern accrued `knob_edit` [2 trials, 1 support] and `reply_ablation` [1, 0] from real verdicts. This is not a gate. |
| Regression | **0 new failures** in the 136-file scope. Across 37 widened files, 1 failure was attributable to tranche 7 (a vacuous ablation test, now fixed). 13 baseline failures in those files now pass. |

## 1. Content-conditioned routes

`seeds/comprehend_instruction.json` v2.4.0 and `seeds/instruction_understanding.json` v1.1.0 are emitted by `scripts/gen_content_conditioned_route.py`, which is idempotent and regenerates byte-identically from the pre-tranche files. The rules changed are the two route-claiming rules (`comprehend_read_instruction`, `instruction_world_action_floor`) and `iu_mint_candidate_interpretation`.

Each of these rules now accepts a verb Concept only if one of these holds:
- it is not scoped `route_object_scope:"other"`; or
- no mention of the message refers to `yourself`/`yourselves`.

That is the same self-reference test that `conversation_self_reply.instruction_self_report_identity` uses. If the attribute is absent the route is unconditioned, so every held verb behaves as before.

`instruction_understanding` also had to be scoped. Without that, a scoped `world_action` Concept still minted an `interpreted_instruction` Goal for "Summarise yourself.". The measured symptom: the self reply shrank from the full self-report to "I am Jabberwock.".

`_compose_cue_variant` now proposes every route with `route_object_scope:"other"`. The delta carries `cue_route_scope`, and adoption teaches the same scoped attributes it tested.

Test (`test_content_conditioned_route_keeps_self_object_on_self_report`):
- "Summarise yourself." is byte-identical before and after the scoped Concept is added.
- "Summarise the data." leaves the gap floor.

`test_cue_builder_proposes_scoped_route` covers the cue builder.

## 2. Real-judge panel v1.4

Runner: `evaluation/substrate_capability/real_judge_repair_panel_v1_4.py`. Report: `evaluation/reports/real_judge_repair_panel_v1_4_conditioned_20261008.json`. Retries are agent-initiated, with no human retry.

| Case | Attempts | Final |
|---|---|---|
| condense | comprehend_text refuted → world_action supported | handled |
| summarise | world_action supported | handled |
| summarise + guard "Summarise yourself." | world_action supported | handled, guard preserved |
| condense + guard "Summarise yourself." | comprehend_text refuted → world_action supported | handled, guard preserved |
| tabulate, alphabetise, paraphrase | world_action supported | handled |
| shorten | comprehend_text refuted → world_action supported | handled |

The result is 8/8 repaired with 0 false adoptions; 5 of 8 cases succeeded on the first attempt. Guard checked for both guarded cases: the reply after adoption equals the reply before adoption.

The guarded seed files (`comprehend_instruction.json`, `experiment_conclusions.json`) were byte-identical after the run.

## 3. Shadow-read fix (pre-existing correctness bug)

`domains/reading_drive._LAAdapter` skips `WorldAdapter.__init__`. Serialized adapter methods such as `register_reflex_response` take `self._conversation_lock`, so `run_reading_flow` raised `AttributeError` on every chat turn. `_shadow_read_turn` swallowed the error and set `shadow_error=1.0`.

The fix mints the lock in `_LAAdapter.__init__`, following the `_QDAdapter` precedent. After the fix:
- reform marks occur on garden-path turns;
- `self_report_contradiction_count` accrues on "Your moon answer is wrong.";
- `shadow_doc_topic` is set.

Test: `test_shadow_read_runs_on_a_chat_turn`.

The fix exposed two latent problems:
- **Paired-control unfairness in the child judge.** The first shadow read in a process pays about 1.8 s of warm-up. The control replay ran first, which inflated `control_shadow_ms` roughly tenfold (1085 ms against 89 ms). `convo_child_run._warm_reading_path` now does one throwaway shadow read before either replay. After the fix, control and variant measured 89 ms against 89 ms.
- **Tests that held only because shadow reads were dead.**
  - `test_topic_span::test_ablating_the_rule_reverts...` passed vacuously. Its ablation is now held by disabling the probe-rule self-heal for the turn.
  - `test_comprehension_self_optimisation::test_exhausted_experiments_trail...` hand-added a concern that the agent now files itself, so the hand-added duplicate was retired. The test now uses the agent's own concern, with an unmeetable 1 ms baseline.

## 4. Non-cue families on reported concerns

Probes:
- `reported_family_probe_v2.py`: shadow read plus reform-eliciting turns.
- `reported_family_probe_v3.py`: v2 plus correction turns.
- `knob_retry_probe_v1.py`.

All run with `OZMA_SEED_PERSIST_DISABLED=1` and n=1 per text.

### datum_feedback

**Cause 1: composer routing.** The concern "you trust that speaker too much…" grounded heads {adopt, communicate, datumfeedback, judge, replay, send, test}. `communicate` (priority 5) outranks `experiment` (priority 8). Its RelationCue keyword `speak` substring-matches "speaker", so the concern went to `compose_communicate_rule`.

Fix: `seeds/composer_dispatch.json` v1.1.0 adds `ComposerCue{replay → experiment, priority 4.5}`, emitted by `scripts/gen_composer_replay_cue.py`. A `replay` head is grounded only by the conversation-experiment bundle. Test: `test_replay_head_routes_reported_concern_to_experiment`.

**Cause 2: no witness.** With the experiment authored (v2), the verdict was inconclusive with belief 0.5 against 0.5, because no corpus turn produced a contradiction datum. That datum is recorded only under shadow read (§3).

Result (v3, with correction turns): **supported, adopted, regressions 0**.

### knob_edit

v2 had reform-eliciting turns, and the child replays recorded 1 reform mark against 1. The knob moved, but the verdict was still inconclusive.

Diagnosis:
- Every `reform_*_threshold` key ties at a word overlap of 2 with "reform … threshold".
- The first key in the tie, `reform_residual_threshold`, gates `residual_marker_count`, which was 0 on every parse.
- The reform that fired came through `swallowed_ratio` (0.5 ≥ 0.5).

Fixes:
- `_compose_knob_variant` excludes knobs that this concern's own experiments have already judged refuted or inconclusive. This mirrors the `cue_route_pick` exclusion. Test: `test_knob_builder_excludes_knobs_already_tried`.
- `seeds/instruction_repair_retry.json` v1.1.0 turns the concern kinds into policy data (`concern_kinds`, default `["instruction"]`, so behaviour is unchanged). The probe opts its own agent in with `"reported"`.

Result (`knob_retry_probe_v1_20261008.json`), with every retry requested by the agent:

| Attempt | Family | Knob | Reforms (control → variant) | Verdict |
|---|---|---|---|---|
| 1 | knob_edit | `reform_eviction_threshold` 2.0→2.1 | 1→1 | inconclusive |
| 2 | reply_ablation | — | — | inconclusive |
| 3 | knob_edit | `reform_swallowed_threshold` 0.5→0.6 | 1→0 | **supported, adopted** |

After adoption, the parent re-heard the corpus with 0 reform marks and no reply changed.

The values compared are exact. The swallowed ratio is a fraction (1/2), and the threshold is compared exactly at its held grain; no tolerance was added.

### shape_mint

The empty delta is honest. `_record_shape_fit` never records a poor fit, because every party tried decodes at a fit of 3–4 out of 4 against `terse_imperative`. The parties tried were greeting, self-report, slang, all-caps and correction turns, and `_SHAPE_FIT_MIN = 2`. The held shape codebook covers every party seen, so there is no poor-fit datum to mint from. This needs either a corpus with a genuinely atypical party or a finer shape grain. That is not done here.

## 5. Regression

- **Core scope:** `/tmp/pfv14/t4scope.txt`, 136 files, compared against `pf_t6.failed`. No tranche-7 failures. 8 tests that failed in tranche 6 now pass. The one apparent newcomer, `test_exhausted_experiments_trail...`, is the latent shadow-read case in §3, and it now passes.
- **Widened scope:** 37 more files that use `shadow_read`, deep ingest, `instruction_understanding` or `composer_dispatch`. These had no prior baseline, so one was measured by temporarily restoring the pre-tranche-7 seeds and `reading_drive.py` (`pf_t7base`). Only one failure was attributable to tranche 7, the topic-span ablation test, now fixed. 13 baseline failures now pass, including `test_multiword_topic_answers_from_the_document_bridge` and 5 `test_cortices_tick` tests.
- **Child-dispatch files rerun after the warm-up change:** 11 files. No failures relative to tranche 6 plus the widened baseline.

## Next

- `shape_mint`: an atypical-party corpus, or a finer shape grain, so a poor-fit datum exists.
- A multi-family credit gate on real verdicts. The retry loop now interleaves families on reported concerns (§4). Run it across several reported concerns with a preregistered gate.
- Knob step direction and grain: the step is fixed at +0.1 in a fixed direction. Read the polarity from the concern, and step at the grain of the knob's own observable (counts against ratios).
- The boot-integrity SelfConcern spam: about 11 near-identical `boot_integrity` concerns per boot were observed. Investigate them.
