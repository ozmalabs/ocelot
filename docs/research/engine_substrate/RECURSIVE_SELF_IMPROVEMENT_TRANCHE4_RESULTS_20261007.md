# Recursive self-improvement, tranche 4: results (2026-10-07)

Follows the [tranche 3 results](RECURSIVE_SELF_IMPROVEMENT_TRANCHE3_RESULTS_20261007.md).

## Summary

| Item | Result |
|---|---|
| Replay judge needs a real reply | **Done.** A flagged turn changed into an empty reply, the adapter's error surface, or a probe exception is now a *broken fix*. It scores −1 and counts as a regression for the adoption veto. Both of the earlier end-to-end "fixes" turn out to be broken, and the agent now refuses to adopt them. |
| More than one family per promoted concern | **Improved.** Promotion now keeps 12 content words instead of 4. Concerns offering at least two variation families rose from 3/9 to 7/9 on a fixed probe set. `knob_edit` and `shape_mint` become reachable. |
| Grain ladder as a vision-route default | **Done, with a guard.** A new `vision_grain_policy` seed sets `dim_grains=[0,1,2]` on the four vision routes. A Rust guard refuses coarse explanations of degenerate collapses. Across 35 vision test files there are no new failures; held-out recognition is 50/100 jittered and 14/100 different-drawer, with 0/100 false recognitions. |
| Recurrence-aware chunk retention | **Pass on 3 streams.** Protecting chunks used ≥ 2 times and capping only the rest kept every recurring task on sparse, dense and a second sparse stream. It used 23–41% of the unbounded probe work. A cap of 4 on its own lost a task on two of the three streams. |

## 1. Judge

In `scripts/convo_child_run.py`, a flagged probe whose variant reply is empty, equals `_CONVERSATION_ERROR_SURFACE`, or raised is a `broken_fix`: −1 instead of +1. `domains/experiment_dispatch.py` carries `broken_fixes` onto the Run and adds it to the Experiment's `regressions`, so `adoption_safety`'s veto also applies.

This changes the outcome of both end-to-end tests:

- **`test_flag_promote_experiment_judge_adopt_closes`.** Ablating `reply_self_identity` does not fix "What are you?". It turns the reply into the error surface, which a fresh agent reproduces directly. The experiment is now refuted, nothing is adopted, and the parent keeps "I am Jabberwock." The test now asserts this.
- **`test_agent_authors_new_rule_end_to_end`.** The `cue_route_pick` route for "condense" is `comprehend_text`, which errors on an instruction turn; `world_action` would have handled it. The cue edit is refuted and not taught. The test now passes on either outcome, provided the judge's verdict matches the reply.

Earlier tranches showed real child verdicts of "supported". Those came from this judge weakness: the measured fixes were broken. **No real conversation self-repair has yet been shown to succeed under the corrected judge.** The next real-judge work should start by finding a concern whose fix is genuine. One candidate is the `condense` cue routed to `world_action`, which handles the instruction (checked directly).

## 2. Multi-family promotion

`scripts/jabberwock_daemon.py` sets `_PROMOTE_CUE_WORDS = 12` for the conversation bundle; it was hard-coded to 4. Every content word becomes TARGET text that the held RelationCue lexicon grounds, so cutting at four words dropped the cues that make other families applicable.

Families offered when each pick is refuted in turn, for 9 fixed concern texts:

| concern | before (4 words) | after (12 words) |
|---|---|---|
| identity reply wrong (reply_fix) | reply_ablation | reply_ablation |
| condense data (instruction) | cue_set_edit, reply_ablation | same |
| hardcoded floor (reported) | rule_literal_edit | same |
| trust/recalibrate (reported) | datum_feedback_rule, reply_ablation | same |
| persona/profile shape (reported) | reply_ablation | **shape_mint**, reply_ablation |
| reform threshold too low (reported) | reply_ablation | **knob_edit**, reply_ablation |
| latency exceeds threshold (performance) | reply_ablation | **knob_edit**, reply_ablation |
| question/statement divergence (comprehension) | reply_ablation | reply_ablation |
| structural edit of rule shape (reported) | reply_ablation, structural_edit | **shape_mint**, reply_ablation, structural_edit |

These are authored concern texts. Real flagged concerns still need a census.

## 3. Grain ladder as a vision-route default

- **Policy seed.** `seeds/vision_grain_policy.json` (`self_load_only`): a graph rule copies `VisionGrainPolicy.dim_grains=[0,1,2]` onto the agent unless `dim_grains` is already set.
- **Routes.** `reflective_faculty._ensure_vision_grain_policy` loads it. It is wired into `crossframe_world`, `verdict_comparator_world`, `invariant_comparator_world` and `sdloop_vision.ingest`.
- **First run broke two tests.**
  - `test_scrambled_support_mints_every_time`: scrambled support was recognised at a coarse grain.
  - `test_three_novel_shapes_one_graph_mint_distinctly_bounded_growth`: a tiny novel shape collapsed onto a held one.
- **Cause.** Coarse-graining a sparse or small set yields a solid block or fewer than 3 cells. Every D4 map fixes those, so they match anything of the same size.
- **Fix.** `shape_decode.rs::coarse_degenerate`: at grain > 0, a goal with fewer than 3 relations, or one that fills its own bounding box, gets no coarse explanation. This applies to both DimInfer and GenInfer.
- **Result.** Across 35 vision test files (`test_vision*`, agnosia, ink, sdloop, crossframe, comparators, codebook-axis and others), failures are identical with and without the change: 5 before, 5 after.

Re-measured on the preregistered held-out panel ([v1.1 report](../../../evaluation/reports/diminfer_grain_heldout_v1_1_degenerate_guard_20261007.json)). Same data and gates; the only change is the guard:

| condition | off | ladder (tranche 3) | ladder + guard |
|---|---:|---:|---:|
| exact | 100 | 100 | 100 |
| jitter | 0 | 60 | 50 (CI 40–60%) |
| different drawer | 0 | 29 | 14 |
| cross-character | 0 | 0 | 0 |

All gates still pass. The guard costs some true recognitions in exchange for the false ones it removes in live routes.

## 4. Recurrence-aware chunk retention

`shape_decode_loop` v1.16.0 adds `agent.gen_chunk_protect_uses = P`. A chunk used P or more times has recurred and is never retired, and `gen_chunk_capacity` bounds only the chunks that have not yet recurred. Without P the behaviour is unchanged. [Report](../../../evaluation/reports/chunk_retention_recurrence_v1_20261007.json).

Recall of recurring tasks / probe candidates (median):

| stream | unbounded | cap 4 | cap 8 | protect 2 + cap 4 | protect 2 + cap 8 |
|---|---|---|---|---|---|
| sparse (120 episodes, 10% recurring) | 2/2 · 8,406 | 1/2 · 678 | 1/2 · 1,014 | **2/2 · 2,268** | 2/2 · 3,828 |
| dense (40 episodes, 50%) | 3/3 · 3,484 | 2/3 · 678 | 3/3 · 1,014 | **3/3 · 1,414** | 3/3 · 2,268 |
| sparse, second seed | 3/3 · 9,204 | 3/3 · 678 | 3/3 · 1,014 | **3/3 · 2,134** | 3/3 · 4,006 |

Protected chunks still accumulate (12–19 live with protect 2 + cap 4), so long-run growth is bounded by how many tasks recur, not by a fixed number.

Two corrections made during regression:

- The first form of the protect test used `Lt`. That broke the seed-audit tests that pin `shape_decode_loop` to no bound-like comparator, so it was rewritten as `Min(uses, P) == P`. The results are identical: the first capture is kept as `chunk_retention_recurrence_v1a_lt_20261007.json`, and every non-timing field matches.
- `test_adoption_safety_migrated.py` used the `reply_self_identity` ablation as its example of a delta that "changes the reply". Under the corrected judge that is a broken fix. Its two delta fixtures now add a replacement identity rule with a different, non-error reply, so the veto mechanism is still tested on a genuine change.

## Regression

Every file ran in its own process with a 30-minute timeout: 136 test files, the union of the tranche 1–3 scopes and the 35 vision files.

- 1,645 passed, 66 failed.
- Every failure is in the earlier baselines. No new failures.
- 5 previously failing tests now pass, including `test_agent_authors_new_rule_end_to_end`.
- `test_residual_promote_migrated.py` still times out, as in every earlier run.
- The full `-k migrated` suite was not run.

## Engine and flags

- Default engine rebuilt from current source. The only new Rust is `coarse_degenerate`.
- New runtime switches:
  - `agent.gen_chunk_protect_uses` (absent → v1.13.0 behaviour)
  - `seeds/vision_grain_policy.json` (loaded only by vision routes)
- Changed behaviour:
  - The replay judge's broken-fix scoring is new default behaviour.
  - Promotion keeping 12 content words is a default change on the conversation promote path.

## Next

1. **Find one genuine conversation self-repair under the corrected judge, then run the real-judge credit gate on concerns that now offer several families.** One candidate is the `condense` cue routed to `world_action`, which handles it directly. Teach `cue_route_pick` that `world_action` is the route for instructions, or let the experiment try more than one route.
2. **Census real flagged concerns.** Measure how many offer two or more families after the 12-word change.
3. **Recover the different-drawer recognitions the degenerate guard removed (29 → 14).** For example, only refuse when the goal is degenerate and the base is not.
4. **Bound protected-chunk growth** for long streams, e.g. decay of `uses`.
