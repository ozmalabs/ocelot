# Recursive self-improvement, tranche 5: results (2026-10-07)

Follows the [tranche 4 results](RECURSIVE_SELF_IMPROVEMENT_TRANCHE4_RESULTS_20261007.md).

## Summary

| Item | Result |
|---|---|
| Genuine self-repair under the corrected judge | **Demonstrated.** A refuted route is excluded and the next attempt tries a different one. On a real-judge panel of 6 unrouted instruction verbs, the agent repaired **5/6** through its own author rule, the real child replay, the corrected judge and adoption. In each case the parent then handles the instruction. **0 false adoptions.** |
| A bug the panel exposed | **Fixed.** Repeating an unhandled instruction gave the error surface instead of a reply. This also made every paired-control replay of an instruction turn an error, which the judge could not tell apart from a delta-caused break. |
| Census of the agent's own concerns | **Experiment concerns are rare.** 258 natural persona-chat turns filed 46 concerns: 34 knowledge, 11 boot-integrity, 1 instruction. Only the 1 instruction concern takes the experiment pipeline. So the multi-family credit gate has almost no natural input yet. |
| Degenerate guard refinement | **Not changed (analysis).** Every recognition the guard removed was a filled-block collapse. Removing it would admit 3/437 cross-character false matches on degenerate goals, against 0/3,363 on non-degenerate ones. |
| Bound on protected chunks | **Pass.** `gen_chunk_protect_capacity=6` keeps 4/4 recall after a task shift, with 8 live chunks instead of 21 and probe work of 1,014 instead of 2,621. A bound of 4 loses one task. |

All new runtime switches are opt-in except two corrections:

- **Repeated-instruction reply:** a new `gap_awareness` rule.
- **Route exclusion:** `cue_route_pick` now skips routes already refuted or inconclusive for the verb.

## 1. Genuine self-repair

Five changes were needed to get a retry to work end to end:

1. **Route exclusion.** `seeds/variation_ops.json` v1.6.0 / v1.9.0: `cue_route_pick` joins `SeedDelta{cue_concept_added, cue_route}` to its Experiment's outcome and excludes a route judged `refuted` or `inconclusive` for that verb (`scripts/gen_cue_route_exclusion.py`).
2. **Re-promote could not mint a fresh axis.** The sd loop's novelty guard treated the retired axis, which still carried the same `capability_keys`, as the concern already surfaced. Teardown in `jabberwock_daemon._tear_down_promoted_pipeline` now re-keys retired axes (`<key>#retired_<id>`, with the old keys kept as `retired_capability_keys`).
3. **Builders read the retired StandingConcern.** The five variant builders found it first by name. They now prefer the live one.
4. **Credit's `exclude_refuted` dropped `cue_set_edit` after one refuted route,** even though it still had untried routes. A `VariationOp.retry_internal` attribute (set on `cue_set_edit`) now exempts a family while its refuted trials still carried an internal alternative (`variation_ops` v1.8.0).
5. **The judge counts a broken flagged reply as the delta's doing only if the paired control reply is not broken** (`scripts/convo_child_run.py`).

The new test `test_refuted_route_is_excluded_and_the_retry_genuinely_repairs` runs this sequence and passes:

- first route `comprehend_text` → refuted;
- human-gated re-promote → `world_action` → supported → adopted;
- the parent then handles "Condense the data."

### Real-judge panel

[Report](../../../evaluation/reports/real_judge_repair_panel_v1_1_20261007.json). Setup: one fresh full-seed agent per verb, the human promotes once, then up to 3 self-authored attempts, re-promoting after a non-supported verdict.

| verb | attempts (route → verdict) | parent handles it after |
|---|---|---|
| condense | comprehend_text → inconclusive; world_action → supported | yes |
| summarise | no route proposed ×3 → inconclusive | no |
| tabulate | world_action → supported | yes |
| shorten | comprehend_text → inconclusive; world_action → supported | yes |
| alphabetise | world_action → supported | yes |
| paraphrase | world_action → supported | yes |

- **`summarise`:** it is already routed (`self_report`, in `conversation_self_reply`) but still unhandled, so a cue edit has nothing to change. Another family would be needed.
- **Exploration arm:** the run with `explore_unscored` gave the same 5/6 ([report](../../../evaluation/reports/real_judge_repair_panel_v1_1_explore_20261007.json)).
- **Earlier attempts:**
  - `v1a` ran before fixes 4–5 and gave 3/6 ([report](../../../evaluation/reports/real_judge_repair_panel_v1a_20261007.json)).
  - A run between the two was killed. It was running with seed persistence on and had taught three adopted Concepts into `seeds/comprehend_instruction.json` and 14 records into `seeds/experiment_conclusions.json`. Both were removed or restored, and v1.1 sets `OZMA_SEED_PERSIST_DISABLED`.
  - The seed files were confirmed byte-identical before and after v1.1.

The verdicts are real: a child process replays the recorded corpus under the corrected judge. The panel is still small. Each verb gets one concern, the human promote is scripted, and the verbs are hand-picked.

## 2. Repeated unhandled instruction

On a fresh agent, saying "Condense the data." twice gave first "…filed it as a gap", then "ERROR: no communicative response could be generated." The gap rule correctly dedups the SelfConcern, but that also suppressed its reply.

`seeds/gap_awareness.json` v1.9.0 adds `reply_known_instruction_gap`: the same guards, but it fires when the concern already exists, files nothing, and replies "…that gap is already filed for me to work on." It is inserted textually to keep the hand-authored file intact (`scripts/gen_repeat_instruction_gap_rule.py`).

## 3. Census

[Report](../../../evaluation/reports/self_filed_concern_census_v1_20261007.json). No deployed daemon history exists on this host (`~/.jabberwock` is absent), so the census uses concerns the agent files itself over `persona_chat_20`.

- 46 concerns: 34 knowledge, 11 boot-integrity, 1 instruction.
- Only the instruction concern enters the experiment pipeline. It offers cue_set_edit then reply_ablation at both the 4-word and 12-word windows.
- The other families need *reported* concerns, i.e. a human or the agent naming a deficiency, which casual conversation does not produce.

## 4. Degenerate guard

[Analysis](../../../evaluation/reports/degenerate_guard_analysis_v1_20261007.json).

- All 15 different-drawer recognitions the guard removed (29 → 14) were coarse goals that filled their own bounding box: 8 cells as 1×8 at grain 1, 12 cells as 3×4 at grain 2.
- Across all pairs of different characters × held maps × grains 1–2, degenerate coarse goals falsely matched another character 3/437 times; non-degenerate ones 0/3,363.
- The planned refinement (refuse only when the base is non-degenerate) would not have recovered these cases: the matched base is degenerate too. The guard stays as it is.

## 5. Bounding protected chunks

`shape_decode_loop` v1.17.0 adds `agent.gen_chunk_protect_capacity = Q`: beyond Q protected chunks, the least-used then oldest is retired. [Report](../../../evaluation/reports/chunk_protect_bound_v1_20261007.json).

Stream: 300 episodes; phase A has 8 recurring tasks, phase B a different 4. Phase-B tasks were probed afterwards.

| arm | phase-B recall | live chunks | probe candidates |
|---|---:|---:|---:|
| protect 2 + cap 4 | 4/4 | 21 | 2,621 |
| + protect cap 6 | 4/4 | 8 | 1,014 |
| + protect cap 4 | 3/4 | 8 | 1,014 |

The seed still has 22 comparators, all classified non-bound. The audit tests are unchanged.

## Regression

Each of 136 test files ran in its own process. 66 failed, the same set as at the end of tranche 4: no new failures, and none of the earlier failures changed state. `test_residual_promote_migrated.py` timed out, as in every run. The full suite was not run.

## Next

1. **Run the multi-family real-judge credit gate on reported concerns.** The census shows natural conversation yields almost no experiment-pipeline concerns, so the gate needs a source of reported deficiencies.
2. **Give `summarise`-type gaps (already routed, still unhandled) a family that can change them.** For example, a route-replacement cue edit that overrides an existing route.
3. **Make the repair loop's retry agent-initiated.** It is currently a human-gated re-promote; the next step is a graph rule that re-promotes a refuted instruction concern while untried routes remain.
