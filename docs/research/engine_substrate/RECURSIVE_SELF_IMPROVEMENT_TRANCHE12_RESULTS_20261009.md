# Recursive self-improvement, tranche 12: results (2026-10-09)

Follows the [tranche 11 results](RECURSIVE_SELF_IMPROVEMENT_TRANCHE11_RESULTS_20261008.md). At the start of this tranche, tranches 1–11 were committed and pushed (`80d6a584`, `7aa67b08`). The `variation_credit` boot default is left unchanged, per instruction.

## Summary

| Item | Result |
|---|---|
| Grain-end step (exact frame quantum) | **Done.** When no knob has an interior separating step, the gate moves one exact quantum past the observed frame. The quantum is the rational GCD of the observed value gaps. |
| **Grain promotion v3** ([prereg](SUBSTRATE_KNOB_GRAIN_PROMOTION_V3_PREREG_20261009.md)) | **PASS on all four gates.** Grain handled 5/5 concerns in 5 experiments; fixed handled 1/5 in 8. Grain now also recovers the tranche-7 K2 case (0.5→1.0). **Promoted: `knob_edit` defaults to `step_mode="grain"`, `grain_end=1`** (`variation_ops` v1.15.0). |
| **`explore_unscored` promotion** ([prereg](SUBSTRATE_EXPLORE_UNSCORED_PROMOTION_V1_PREREG_20261009.md)) | **PASS on all four gates** (v1.1 clean rerun). Zero-overlap verbs: 6/6 with explore against 0/6 without. Overlap verbs: unchanged at 6/6, in 7 experiments each. **Promoted: `cue_set_edit.explore_unscored=1`** (`variation_ops` v1.16.0). |
| Disk-full incident | The root filesystem filled during the explore v1 run, from child run directories in `/tmp`. `seeds/experiment_conclusions.json` was truncated to empty; it was restored from HEAD and verified against the guard copy. The v1 result is kept, and a clean v1.1 rerun matched it exactly. Runners now delete their child run directories. |
| Regression | **0 failures attributable to tranche 12** after 2 test updates (fixed-step tests pinned) across 221 files; 4 earlier failures now pass. |

## 1. Grain-end step

Two new functions in `domains/reflective_faculty.py`:
- **`_frame_quantum(values)`** computes the exact GCD of the gaps between distinct values, using `fractions.Fraction` from the floats' exact binary values. For {0, 0.5} it is ½; for {0, 2, 3, 5} it is 1.
- **`_grain_end_step(values, op, t, direction)`** places the gate one quantum past the frame. For a `Gte` gate:
  - "too eagerly" (`decrease_fires`) → `max + q`, which fires on none of the observed values;
  - "too rarely" (`increase_fires`) → `min`, which fires on all of them.

The builder offers a grain-end step only when `grain_end == 1` **and** every ranked candidate knob has been refused an interior step. The new gate is on the frame's own lattice, so this is exact quantisation, not a tolerance, and the paired control replay still judges it.

Test: `test_frame_quantum_and_grain_end_are_exact`.

## 2. Grain promotion v3

The design is v2's with one change: the grain arm sets `grain_end=1`.

| Corpus | fixed: supported (experiments) | grain: supported (experiments) |
|---|---|---|
| K1 (independent list sentences) | 0/2 (3) | 2/2 (2): residual 1→3, then 3→2 |
| K2 (tranche-7 corpus) | 1/1 (2): swallowed 0.5→0.6 on the second knob | **1/1 (1)**: swallowed 0.5→1.0 (grain end, reforms 1→0) |
| K3 (tranche-10 corpus) | 0/2 (3) | 2/2 (2) |

All four gates hold: Q1 (grain ≥ fixed on every corpus), Q2, Q3 (0 false adoptions) and Q4 (K2 is not vacuous). The defaults were promoted by the preregistered rule.

Tests:
- `test_grain_is_the_knob_edit_default`;
- the fixed-step tests now set `step_mode="fixed"` explicitly.

## 3. `explore_unscored` promotion

Setup:
- the production default boot, with no `variation_credit`;
- the frame "Please <verb> the notes.";
- the agent's own retries.

Streams:
- Z, verbs with zero bigram overlap with any route Concept: sort, tag, trim, dub, snip, sift;
- O, verbs with overlap of at least 1: mend, buff, flag, sum, fold, group.

| Arm | Z handled (experiments) | O handled (experiments) | False adoptions |
|---|---|---|---|
| default | 0/6 (0, every attempt abstained before dispatch) | 6/6 (7) | 0 |
| explore | **6/6** (12) | 6/6 (7) | 0 |

On Z, explore follows the same pattern for every verb: `comprehend_text` refuted, then `world_action` supported. On O it changes nothing.

All four gates hold: E1, E2, E3, and E4 (explore uses at most 2 extra experiments on O).

The run history:
- v1 produced the same numbers, but it ran during the disk-full event and its `default_Z` part was first written by a crashed attempt.
- v1.1 is the clean rerun, and the promotion is based on it.
- Both v1 and v1.1 reports are kept.

Tests:
- `test_explore_unscored_is_the_cue_set_edit_default`;
- `test_cue_variant_abstains_honestly` and `test_abstained_cue_variant_is_never_dispatched` now turn `explore_unscored` off explicitly to pin the abstain path; case 3b of the former covers it on.

## 4. Disk-full incident

The child runner writes a `final_graph.json` of several GB per experiment. By this tranche, `/tmp` held 126 GB of run directories, and the root filesystem filled during explore v1.

Damage found:
- `seeds/experiment_conclusions.json` was truncated to 0 bytes. It was restored from HEAD, which is byte-identical to the pre-run guard copy.
- No other tracked file changed.

Remediation:
- old run directories were deleted (105 GB freed);
- the explore runner now removes its run directory when it finishes.

## 5. Regression

Scope: 221 files (`/tmp/pfv14/t11scope.txt`), compared against `pf_t11.failed`.

- **2 new failures**, both premise changes caused by the grain default:
  - `test_residual_closure_migrated::test_compose_knob_variant_picks_named_knob_and_abstains`
  - `test_rule_literal_variation_migrated::test_knob_edit_pick_and_compose_unaffected`

  Both assert the fixed 0.1 step on an agent that has heard no turns, so there is no observed frame and grain correctly abstains. Both now pin `step_mode="fixed"` and pass.
- **4 fixed relative to tranche 11:** the two tranche-11 premise updates, plus `test_arc_decompose…ar17` and `test_tom_meta_shape…no_prior_seed_was_edited`, which both check a clean tree and pass now that tranches 1–11 are committed.
- The run rewrote `tests/fixtures/comprehension_divergence/divergence.json` (latency values only). It was restored with `git checkout`.
- `test_residual_promote` timed out, as in every tranche.

## Next

- A mixed-kind credit gate: instruction, reported, knob and shape concerns on one agent with `variation_credit` loaded, in a lab boot only, since the production default stays unchanged.
- Child-runner storage: have `convo_child_run` write `final_graph.json` only when adoption needs it, rather than always.
- The grain step's signal source (`grain_signal_types`) is a fixed list (`SentenceParse`). Derive it structurally from the gating rule's match pattern.
