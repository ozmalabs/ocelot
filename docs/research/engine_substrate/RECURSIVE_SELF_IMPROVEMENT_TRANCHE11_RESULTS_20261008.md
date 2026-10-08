# Recursive self-improvement, tranche 11: results (2026-10-08)

Follows the [tranche 10 results](RECURSIVE_SELF_IMPROVEMENT_TRANCHE10_RESULTS_20261008.md).

## Summary

| Item | Result |
|---|---|
| Domain data moved out of `seeds/` | **Done.** 7 files read directly by domain modules → `domain_data/`; 1 file with no reader → `domain_data/orphaned/`; 5 Qwen3 LLM-harvest fragments → `domain_data/llm_harvest/`. A full boot now loads 730/730 seeds with **0 anomalies** and assesses itself `healthy` (it was `compromised`, with 11 failed seeds, on every boot). |
| Empty-delta experiments | **Fixed.** An experiment whose builder abstained is closed `abstained` before dispatch: no child replay, no credit, and the family is excluded for that concern. `sort` now costs 0 replays (it cost 3 in tranche 10). |
| Why `sort` abstains | **Diagnosed.** "sort" shares no character bigram with any of the 23 route-carrying Concepts. With `explore_unscored` (opt-in) the agent repairs it (`comprehend_text` refuted → `world_action` supported). |
| Grain-step promotion, v1 ([prereg](SUBSTRATE_KNOB_GRAIN_PROMOTION_V1_PREREG_20261008.md)) | **Passed only vacuously; not acted on.** The regression corpus scored 0 in both arms, which exposed two knob-retry defects. |
| Grain-step promotion, v2 ([prereg](SUBSTRATE_KNOB_GRAIN_PROMOTION_V2_PREREG_20261008.md)) | **Failed Q1, as predicted in the prereg.** Grain is better on 2 of 3 corpora (4/4 against 0/2), but loses the tranche-7 success on K2. Grain steps **stay opt-in**. |
| Knob retries | **Fixed.** `knob_edit` is now `retry_internal`, so the family is not dropped after one knob. Grain mode now falls back to the next-ranked knob. |
| Credit is not loaded on production boots | **Found; needs a decision** (§6). |
| Regression | **0 failures attributable to tranche 11** after 2 test updates (both premises changed by this tranche) across 221 files. |

## 1. Domain data relocation

The rule applied: a file read directly by a domain module is domain data, not a seed.

| File | Destination | Reader |
|---|---|---|
| reading_constructions | `domain_data/` | `reading_collapse.ensure_codebook` (also situation_model_reader, character_tom, propositional_deduction, discourse_coherence) |
| conceptual_categories | `domain_data/` | `phase_composer_language_rules`, `sense_selection_rules` |
| character_tom | `domain_data/` | `character_tom` |
| named_compound_heads | `domain_data/` | `cognitive_disambiguation` |
| vision_change | `domain_data/` | `wave_world._CHANGE_SEED` |
| acoustic_cue_vocab, cue_investigator | `domain_data/` | `scripts/jabberwock_grounds_acoustic_cue.py`, `scripts/jabberwock_binds_cue_investigator.py` |
| reading_skeleton | `domain_data/orphaned/` | none in the tree; kept, not loaded |
| qwen3_reaped_{knowledge, knowledge_scaled, isa_full, relations}, qwen3_relation_calibration | `domain_data/llm_harvest/` | `scripts/llm_harvest_*`, `llm_calibrate_relations`, two `tests/test_qwen3_*`, the llm_taxonomy evaluation |

Changes made:
- Path references were rewritten mechanically in 45 Python files: domains, scripts, tests and evaluation, including docstrings.
- Three dynamic-path readers were fixed by hand: `tests/test_codebook_partition_migrated.py`, `scripts/codebook_partition_probe.py`, `scripts/jabberwock_reads_arc_agi_site.py`.
- `story_boundary`, `coherence_relations` and `event_role_frames` declared `depends_on: ["reading_constructions"]`, a dependency that was never satisfiable because the file never loaded as a seed. It is now `domain_data_requires`.
- `domain_data/README.md` documents all of the above.

Historical docs and capture lock files keep their old paths, because they are records. A backup of the moved files is at `/tmp/pfv14/t11_backup/pre_move.tgz`.

Boot after the move:
- `load_all_seeds`: total 730, loaded 730, failed 0;
- `BootSeedAnomaly`: none;
- `BootCycle.integrity = healthy`;
- no `boot_integrity` SelfConcern;
- an ordinary turn is unchanged ("What do you know about the moon?").

## 2. Empty-delta experiments

`_compose_experiment_rule` now stamps `variant_abstained=1` (plus the builder's `abstain_wall`) on the delta in two cases:
- the picked family's builder abstained;
- a conversation concern has no eligible family left.

Supporting seed changes:

| Seed | Change |
|---|---|
| `self_optimisation` v1.4.0 | New rule `close_abstained_variant` (`scripts/gen_abstain_close_rule.py`) closes such an experiment `done` / `abstained` before dispatch. Credit counts only supported, refuted and inconclusive outcomes, so it is never charged. |
| `variation_ops` v1.13.0 | The pick excludes a family that abstained for this concern. |
| `instruction_repair_retry` v1.3.0 | Counts `abstained` as non-supported, so the agent's own retry moves on. |

Measured on "Please sort the notes.", with the agent's own retries:
- `cue_set_edit` abstained, then `reply_ablation` abstained, then no family remained.
- **0 child replays**; tranche 10 spent 3 on empty deltas.
- The gap stays filed honestly.
- With `cue_set_edit.explore_unscored=1`: `comprehend_text` refuted → `world_action` supported, and the parent then handles the turn.

Tests:
- `test_abstained_variant_is_closed_uncredited_and_excluded` (graph level);
- `test_abstained_cue_variant_is_never_dispatched` (full boot).

## 3. Grain-step promotion

### v1

Corpora: K1, independent list sentences; K2, the tranche-7 corpus.

| Corpus | grain supported | fixed supported |
|---|---|---|
| K1 | 2/2 | 0 |
| K2 | 0 | 0 |

The rule passed, but K2 was vacuous: it measured nothing. Two defects caused that:
- **Fixed arm.** The default `exclude_inconclusive` dropped the whole `knob_edit` family after one inconclusive knob, before the builder's per-knob exclusion could try another. The tranche-7 success had needed the third knob.
- **Grain arm.** The builder abstained as soon as the top-ranked knob had no separating step, without trying the next one.

Fixes (`variation_ops` v1.14.0 and the builder):
- `knob_edit` is `retry_internal`; a trial that names a `knob_attr` counts as carrying an internal alternative, exactly like a `cue_route`.
- Grain mode walks the ranked knob candidates.

v1's verdict was not acted on, and a v2 was preregistered with a non-vacuity gate (Q4).

### v2

Corpora: K1, K2, and K3 (the tranche-10 corpus).

| Corpus | fixed: supported (experiments) | grain: supported (experiments) |
|---|---|---|
| K1 | 0/2 (3; eviction, residual and swallowed all inconclusive) | **2/2** (2): residual 1→3 (6→4), then 3→2 (4→6) |
| K2 | **1/1** (2): swallowed 0.5→0.6 (1→0) on the second knob | 0/1 (0): every knob abstains |
| K3 | 0/2 (3) | **2/2** (2) |

| Gate | Condition | Result |
|---|---|---|
| Q1 | grain ≥ fixed on every corpus | **FAIL** (K2) |
| Q2 | grain > fixed on at least one corpus | pass |
| Q3 | no false adoption in grain | pass |
| Q4 | K2 not vacuous | pass |

Verdict: **grain stays opt-in.**

This was the conflict the prereg named in advance. On K2 the signal took only {0, 0.5}. The degenerate guard refuses a gate that fires on none of the observed values, yet that is exactly the fixed step's supported adoption: turning reform off for this corpus, with no reply regressions.

Whether "fire on nothing observed" should count as a legitimate end of the grain is a design question. It is reported, not tuned after the fact.

Not verified: in the fixed arm of K1 and K3 the "rare" concern authored no requested experiment. This is likely because the first concern's three inconclusive knob trials pushed the pick, via credit, onto a family that abstained, and the runner stops when nothing is `requested`. It does not change Q1.

## 4. Knob retry fixes

Both fixes come from §3. The tests passing after them:
- the knob, grain, credit and abstain tests in `tests/test_variation_credit_migrated.py` and `tests/test_agent_authors_new_rule_migrated.py` (22);
- `test_new_seeds_canon_round_trip_and_reconcile_churn_free`.

## 5. Generated seeds

`seeds/generated/` now holds only agent-authored graph data, as its README says: `lead`, `measure_prediction`, `predict_linear`, `predict_observable_linear` and `self_heartbeat_predictor`.

## 6. Finding: outcome credit is not loaded on production boots

`seeds/variation_credit.json` is `self_load_only`, so `load_all_seeds` skips it. On a normal boot there is no `VariationPolicy` node and no credit rules: the pick runs on raw priority, without exclusion and without learning. Every credit gate (tranches 1–10) loaded it explicitly, so the real-verdict credit results hold where the seed is loaded, which is not the daemon's default boot. The tranche-10 "promotion to default" therefore only changes agents that load the seed.

For this reason, the tranche-11 abstain-close rule was placed in `self_optimisation`, which does load on every boot.

Loading `variation_credit` by default would change pick behaviour on every boot. That needs your confirmation.

## 7. Regression

Scope: 221 files, `/tmp/pfv14/t11scope.txt`. That is tranche 10's 179 files plus 42 that touch the moved files, the boot index or boot metacognition. The baseline is `pf_t10.failed` plus the 42 new files measured on the tranche-11 tree before the pick and abstain changes. One test in that set needed a path fix.

There were three new failures, all resolved:

| Test | Cause | Resolution |
|---|---|---|
| `test_agent_authors_new_rule_migrated::test_agent_requests_its_own_retry_and_stops_at_the_bound` | Its third attempt now ends `abstained` before dispatch: both pooled routes are excluded for the verb. The test expected a third requested experiment. | Updated to assert the abstain close and the unchanged bound (`retry_count == 2`). Passes. |
| `test_self_gaps_surfacing_migrated::test_converse_surfaces_boot_integrity_gap_when_full_boot_is_incomplete` | It relied on the shipped boot being broken, which it no longer is. | It now constructs an incomplete boot (a second boot cycle over one invalid manifest) and checks that the gap is surfaced. Passes. |
| `test_cognitive_disambiguation::test_nobel_leak_gone_and_incoherence_caught` | Pre-existing: it also fails with the moved files restored to `seeds/`. It had been missing from the baseline because the baseline run of that file timed out. | Not a tranche-11 regression. |

Fixed: `test_codebook_partition_migrated::test_coherence_codebook_must_stay_its_own_node_type`, after its path fix.

`test_residual_promote` timed out, as it has in every tranche. The seeds the probes could write to were byte-identical after every run.

## Next

- **Your decision:** load `variation_credit` on production boots (§6).
- The grain degenerate guard against "fire on nothing observed" (§3): needs a principled rule. One candidate: allow a gate at the grain's end when the concern's direction asks for it and the paired control replay shows no regressions.
- A mixed-kind credit gate (instruction, reported, knob and shape concerns on one agent), carried over from tranche 10.
- Route proposal for verbs with no bigram overlap (`sort`): whether to make `explore_unscored` the default, under a preregistered gate.
