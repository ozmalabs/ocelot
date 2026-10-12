# Recursive self-improvement, tranche 10: results (2026-10-08)

Follows the [tranche 9 results](RECURSIVE_SELF_IMPROVEMENT_TRANCHE9_RESULTS_20261008.md).

## Summary

| Item | Result |
|---|---|
| **Grain-quantised knob steps** (opt-in `step_mode: "grain"`) | **Done.** A knob steps to the next distinct value the signal it gates actually took, not a fixed 0.1. On the real judge both directions were supported and adopted: "too eagerly" 1→3 (reforms 5→3) and then "too rarely" 3→2 (3→5). The fixed-step arm was inconclusive on all 6 attempts. |
| Stale-retry race (found by the probe) | **Fixed.** `irr_cancel_stale_retry` clears a retry mark once a family judge turns the provisional verdict into "supported". Before the fix the agent tore down and re-promoted an already-adopted concern, which left the next concern with no experiment. |
| **Preregistered credit gate v3, new sentence frames** ([prereg](SUBSTRATE_VARIATION_CREDIT_REAL_JUDGE_V3_PREREG_20261008.md)) | **PASS on all four gates.** No credit 0/11 handled in 33 experiments; per-trial credit 8/11 in 20; credit plus the tranche-9 policy 10/11 in 17. 0 false adoptions. |
| Tranche-9 policy promoted to default | **Done, by the preregistered rule** (G2–G4 held in both v2 and v3). `variation_credit` v1.2.0: `credit_internal_exempt=1`, `exclude_inconclusive=1`. |
| Malformed boot seeds (11) | **Diagnosed; load behaviour unchanged** (see §5). |
| Regression | **0 new failures** across 179 files, with the promoted default in place. |

## 1. Grain-quantised knob steps

`domains/reflective_faculty.py` adds two pieces:

- **`_knob_gated_signal(native, knob_attr)`.** Structurally finds the unique comparison in the active rules whose bound reads the knob, possibly scaled inside `Times`, and returns the signal attribute on the other side.
  - `reform_residual_threshold` → `(Gte, residual_marker_count)`
  - `reform_swallowed_threshold` → `(Gte, swallowed_ratio)`
- **`_grain_step(values, op, t, direction)`.** Works on the distinct observed values of that signal.
  - `decrease_fires` moves the gate just past the lowest value that currently fires.
  - `increase_fires` moves it onto the highest value that does not currently fire.
  - All comparisons are exact.
  - **Degenerate guard:** the new gate must still separate the observed values, with at least one firing and one not. Otherwise the builder abstains with the reason; it never steps to a gate that fires on everything or on nothing.

Configuration:
- The step is opt-in through `VariationOp{knob_edit}.step_mode == "grain"`.
- `grain_signal_types` (`["SentenceParse"]`) is inert data in `seeds/variation_ops.json` v1.12.0, emitted by `scripts/gen_knob_grain_attrs.py`. The generator chain is idempotent.

This is approximation by quantisation, not tolerance: the threshold moves only to values in the observed frame.

Tests:
- `test_grain_step_is_exact_and_guards_degenerate_gates`. It includes the tranche-9 case: on the {0, 0.5} grain, "too rarely" has no separating step, so the builder abstains.
- `test_knob_gated_signal_found_structurally`
- `test_grain_mode_builder_steps_onto_observed_values`

### Real-judge probe

Runner: `knob_grain_probe_v2.py`. Report: `knob_grain_probe_v2_staleretry_20261008.json`. The v1 report is kept; see §2.

Setup:
- Corpus: 5 list sentences plus 2 simple ones. The values of `residual_marker_count` were measured beforehand as {0, 2, 3, 4, 5} and are disclosed in the runner.
- Concerns, filed in sequence on one agent: "…list sentences too eagerly…", then "…too rarely…".
- Retries are the agent's own.

| Arm | Concern | Attempts | Verdict | Held threshold |
|---|---|---|---|---|
| fixed (0.1 step) | eager | residual 1→1.1 (5→5), reply_ablation, eviction 2→2.1 (5→5) | inconclusive ×3 | 1.0 |
| fixed (0.1 step) | rare | residual 1→0.9, eviction 2→1.9, swallowed 0.5→0.4 (all 5→5) | inconclusive ×3 | 1.0 |
| grain | eager | residual 1→3 (5→3 reforms) | **supported, adopted** | 3.0 |
| grain | rare | residual 3→2 (3→5 reforms) | **supported, adopted** | 2.0 |

In the grain arm the agent corrected itself in both directions: the second concern undid part of the first adoption, landing on the grain point the concern asked for. Caveat: n=1 per arm, and the corpus was chosen so the signal has headroom.

## 2. Stale-retry race

Probe v1 (`knob_grain_probe_v1_20261008.json`, kept): in the grain arm, the "rare" concern authored no experiment.

Diagnosis:
- The generic judge writes a provisional "inconclusive".
- `irr_request_retry` marks a retry in the same fixpoint.
- The knob family judge then overrides the verdict to "supported".
- The daemon executed the stale mark: it tore down and re-promoted the adopted "eager" concern, and the duplicate author rules for the two concerns cancelled each other.

Fix: `seeds/instruction_repair_retry.json` v1.2.0, emitted by `scripts/gen_instruction_repair_retry_seed.py`, adds `irr_cancel_stale_retry`. Once a concern has a supported experiment, it clears the pending mark and restores the retry count. Test: `test_stale_retry_mark_is_cleared_when_a_family_judge_supports`. Probe v2 is the rerun after the fix.

## 3. Credit gate v3 (preregistered, new sentence frames)

Runner: `variation_credit_real_judge_v3.py`. Reports: six part files plus `variation_credit_real_judge_v3_gate_20261008.json`.

The frames:
- F1: "Please <verb> the notes."
- F2: "Could you <verb> the report?"

These frames were feasibility-checked with one verb each; the other verbs were not pre-checked. `tally` failed to file a gap under F1 in every arm and was skipped, as the prereg allows.

| Arm | Handled | Experiments | False adoptions |
|---|---|---|---|
| A, no credit | 0/11 | 33 | 0 |
| B, per-trial credit | 8/11 | 20 | 0 |
| C, credit + tranche-9 policy | **10/11** | **17** | 0 |

All four gates hold: G1 (B > A), G2 (C ≥ B), G3 (C ≤ B experiments) and G4.

B's misses:
- `index` (F1) and `redact` (F2) are both the tranche-8 failure pattern: a refuted `comprehend_text` route sent B back to `reply_ablation`. C recovered both.
- `sort` (F1).

The miss shared by B and C is `sort`:
- `cue_route_pick` abstains for it, so the `cue_set_edit` experiment carries an empty delta and is inconclusive.
- `sort` is held as a Concept in `mbpp_request_cues` and `learned_lexicon`; why the pick abstains has not been pinned down.
- C stops after 3 experiments. B spent all 3 attempts on empty `cue_set_edit` deltas, because only route-carrying trials are exempt and empty ones are charged normally.

### Promotion

The preregistered rule held: G2–G4 passed in both v2 and v3. `seeds/variation_credit.json` v1.2.0 (`scripts/gen_variation_credit_seed.py`) now ships `credit_internal_exempt=1` and `exclude_inconclusive=1` by default. The pre-promotion copy is at `/tmp/pfv14/vc.pre_t9.json`.

Tests:
- `test_tranche9_policy_is_the_seed_default`
- The two tranche-9 tests now set the policy off explicitly to show the per-trial behaviour.

The promotion is conditional on the regression in §6.

## 4. Totals across the three real-verdict credit gates

| | Problems | Handled | Experiments |
|---|---|---|---|
| No credit (tranche 8 OFF, v2 A, v3 A) | 28 | 0 | 84 |
| Per-trial credit (tranche 8 ON, v2 B, v3 B) | 28 | 23 | 50 |
| Credit + tranche-9 policy (v2 C, v3 C) | 23 | 22 | 35 |

There were 0 false adoptions in any credit arm. Each (arm, stream) is a single deterministic run.

## 5. Malformed boot seeds (diagnosis only)

All 11 fail on every full boot, are unchanged from the initial import, and were not changed here.

- **8 hand seeds have nodes without `local_id`:** acoustic_cue_vocab (11/11 nodes), character_tom (2/2), reading_constructions (13/74), conceptual_categories (1/36; a `{"comment": …}` pseudo-node), cue_investigator (1/1), named_compound_heads (9/9), reading_skeleton (2/2), vision_change (1/1).
  - Several are read directly by their domain modules, for example `reading_collapse._CODEBOOK_SEED` and `phase_composer_language_rules`.
  - So the native boot-time load failing does not mean the data is unused. Adding `local_id`s would newly install those nodes at boot, which is a behaviour change.
- **3 `seeds/generated/qwen3_reaped_*` files are LLM-harvest fragments, not manifests.** Their edges are `{subject, relation, object, trust}`, and they are written by `scripts/llm_harvest_*`. The loader globs `seeds/generated/*.json`, so they are picked up by accident.
  - Fix options: move them out of `generated/`, or have the loader skip non-manifest files.

Both changes alter what loads at boot, so neither is made without your confirmation.

## 6. Regression

Scope: `/tmp/pfv14/t8scope.txt`, 179 files, against `pf_t9.failed`. This run includes the promoted policy default.

**0 new failures.** The failing set is identical to tranche 9 (92 tests, all pre-existing). `test_residual_promote` timed out, as it has in every tranche. The promotion therefore stands.

The seeds the probes could write to (`comprehend_instruction`, `experiment_conclusions`) were byte-identical after every run.

## Next

- Diagnose `cue_route_pick` abstaining for `sort`, and make an empty-delta experiment either not authored or not charged.
- Grain steps as the default for `knob_edit`: preregister a promotion run on an independent corpus.
- A mixed-kind credit gate: instruction, reported, knob and shape concerns on one agent.
- With your confirmation, repair the 11 seeds.
