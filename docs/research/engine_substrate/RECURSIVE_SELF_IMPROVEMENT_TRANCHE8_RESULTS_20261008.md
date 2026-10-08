# Recursive self-improvement, tranche 8: results (2026-10-08)

Follows the [tranche 7 results](RECURSIVE_SELF_IMPROVEMENT_TRANCHE7_RESULTS_20261008.md).

## Summary

| Item | Result |
|---|---|
| **Preregistered real-verdict variation-credit gate** ([prereg](SUBSTRATE_VARIATION_CREDIT_REAL_JUDGE_V1_PREREG_20261008.md)) | **PASS.** Credit on: 4/5 gaps handled in 10 experiments. Credit off: 0/5 in 15. 0 false adoptions. This is the first time credit learned from real child-replay verdicts has steered the agent's choice of improvement method. n=1 stream per arm. |
| `shape_mint` | **Supported and adopted** on the real judge (n=1). This needed an atypical party in the corpus and a corrected child witness. The first run, with the old witness, came back inconclusive; that report is kept. |
| `knob_edit` polarity | **Done.** The step direction comes from the concern ("too rarely" vs "too eagerly") and is read against the agent's held direction lexicon. The judge now checks the move against the direction the concern asked for. |
| Duplicate boot-integrity concerns | **Fixed.** One SelfConcern per compromised boot, supported by every anomaly. Previously there were 11 per full boot, 10 of them retired as duplicates. |
| Regression | **0 failures attributable to tranche 8** across 179 files. 2 tests that failed in tranche 7 now pass. |

## 1. Real-verdict variation-credit gate

Runner: `evaluation/substrate_capability/variation_credit_real_judge_v1.py`. Report: `evaluation/reports/variation_credit_real_judge_v1_20261008.json`.

Design, as preregistered:
- One agent per arm handles 5 instruction gaps in order (condense, tabulate, shorten, alphabetise, paraphrase).
- The prior is deliberately misordered: `reply_ablation.priority` is set to 8, which beats `cue_set_edit` at 10.
- Retries are the agent's own, with at most 3 experiments per gap.
- The arms differ only in `VariationPolicy.use_credit`.

| Arm | Experiments | Handled | First pick `cue_set_edit` | False adoptions |
|---|---|---|---|---|
| OFF | 15 | 0/5 | 0/5 | 0 |
| ON | 10 | 4/5 | 3/5 | 0 |

All three gate conditions hold: G1 (handled ON ≥ OFF), G2 (fewer experiments ON) and G3 (no false adoption ON).

How the ON arm behaved:
- `reply_ablation` was inconclusive on every attempt in both arms (19/19).
- With credit on, its failure odds rose: credit reached `reply_ablation|instruction` [4 trials, 0 supports] and `cue_set_edit|instruction` [6, 4]. From the third gap onwards, `cue_set_edit` was picked first.
- The OFF arm never left the misordered prior. `exclude_refuted` does not drop a family that is only inconclusive, so OFF spent every attempt on `reply_ablation`.

The miss (condense, ON arm):
- `cue_set_edit` tried `comprehend_text` and it was refuted (1 regression).
- That refutation raised `cue_set_edit`'s credit factor above `reply_ablation`'s at that point, so the third attempt went back to `reply_ablation`.
- The retry bound then ran out before `world_action` was tried.

So credit is coarse: it is per family and kind, and it does not know that `cue_set_edit` still had an untried internal route. This is a finding, not a gate failure.

Caveat: n=1 stream per arm, 5 verbs from one template. The result shows that credit from real verdicts can steer the pick; it is not an effect size.

## 2. shape_mint

Two things were missing.

**A poor-fit datum.** The corpus had none. Every party tried earlier fit `terse_imperative` or `technical_precise` at 3–4 of 4 dimensions. A casual + medium + ornate + agitated party, for example "yeah nah, this whole conversation is kinda ridiculous!!", fits no held shape (fit 0), so `poor_fit_streak` grows and the builder mints a `learned_casual_medium_ornate_agitated_*` InterlocutorShape. Probe: `reported_family_probe_v4.py`, with this party prepended to the v3 corpus.

**A witness that can move.** The first run (`reported_family_probe_v4_atypical_20261008.json`, kept) came back inconclusive, with control 4 and variant 4. The old witness `_active_interlocutor_shape_fit` had two problems:
- it read the fit of whichever party was active in the snapshot, which was a typical party at fit 4 in both passes;
- it read the control before its replay.

The new witness, `convo_child_run._classified_party_count`, counts the modelled parties that fit some held shape at the `_SHAPE_FIT_MIN` floor. It does not depend on which party is active, and it is read after each pass's replay.

Rerun (`reported_family_probe_v4b_atypical_witness_20261008.json`): 2 → 4 classified parties, 0 regressions, **supported and adopted**.

Test: `test_shape_mint_witness_counts_classified_parties`.

Change of measure, stated plainly: the witness moved from the active party's fit to a count of classified parties after the inconclusive run. The new witness is what the family claims to improve ("parties fit a shape"), and it is measured identically in both passes. Even so, it was chosen after a null.

## 3. knob_edit polarity

- **Builder.** `_compose_knob_variant` scores the concern's words against `direction_lexicon_more` and `direction_lexicon_fewer`. These lists are held on the `rule_literal_edit` VariationOp and are agent-editable. If "more" wins, the direction is `increase_fires` and the threshold is lowered. Otherwise the direction is `decrease_fires` and the threshold is raised, the pre-tranche-8 default, which is also kept on a tie. The delta carries `knob_direction`.
- **Judge.** `seeds/self_optimisation.json` v1.3.0, emitted by `scripts/gen_knob_direction_judge.py`.
  - For `increase_fires`, more reform marks counts as support and fewer counts as a refutation.
  - If the direction is absent or `decrease_fires`, the judge behaves as before.
  - A tie is inconclusive, and any regression refutes.

Tests:
- `test_knob_direction_follows_concern_polarity`: "too eagerly" raises the knob and "too rarely" lowers it.
- `test_knob_judge_is_direction_aware`: four verdict cases, including the legacy case with no direction.

This was not run on the real judge with a "too rarely" corpus in this tranche.

## 4. Boot-integrity duplicates

`seeds/boot_metacognition.json` v1.1.0, emitted by `scripts/gen_boot_metacognition_once.py`.

**Cause.** `assess_compromised_boot` matched once per anomaly (`[cycle has_seed_anomaly anomaly]`). A boot with N failed seeds therefore produced N bindings in one rule pass, and the `Exists(SelfConcern)` dedup guard was read before any of them landed, so N concerns were minted.

**Fix.** Both assessment rules now match only the cycle and require an anomaly in the where clause. `bind_boot_anomaly_evidence`, unchanged, still links every anomaly.

**Result.** A full boot now has 1 `boot_integrity` concern with 11 pieces of `supported_by` evidence. Test: `test_many_failed_seeds_file_one_concern_with_all_evidence`, which fails against v1.0.0 and passes against v1.1.0.

Still open, and not fixed: the 11 anomalies are real. 8 seeds have nodes missing `local_id` (acoustic_cue_vocab, character_tom, reading_constructions, conceptual_categories, cue_investigator, named_compound_heads, reading_skeleton, vision_change). 3 qwen3_reaped seeds fail with "seed ref must be an object". These fail on every full boot.

## 5. Regression

The scope is `/tmp/pfv14/t8scope.txt`: tranche 7's 173 files plus 6 that use boot metacognition, shape or self-gaps. The comparison baseline is `pf_t7.failed`.

- 0 new failures in the tranche-7 scope; 2 tests that failed in tranche 7 now pass.
- One failure appeared in a newly added file, `test_instruction_gap_migrated::test_covered_read_instruction_is_handled_no_gap` ("Read this: …" returns the unknown-word reply). It still fails with every tranche-7 and tranche-8 seed reverted and with the `_LAAdapter` lock reverted, so it is pre-existing. It had never been in scope before.
- `test_residual_promote` timed out, as it did in earlier tranches.

The seeds the probes could write to (`comprehend_instruction`, `experiment_conclusions`) were byte-identical after every run.

## Next

- **Credit granularity.** Credit `cue_set_edit` per route, or exempt a `retry_internal` family from credit inflation while it still has untried internal alternatives. That would recover the condense miss.
- Treat repeated **inconclusive** results like refutations for exclusion; this is what kept the OFF arm stuck.
- Rerun the gate with more streams and verbs from more than one template.
- A real-judge "too rarely" knob probe.
- Repair the 11 malformed seeds that fail on every boot. The agent now files one honest concern about them.
