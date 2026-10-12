# Endemic RSI on the production path v2: preregistration (2026-10-10, tranche 23)

## Claim under test

On the production path, with no human involvement, the agent corrects its own reader. It runs two readers on every turn. One is the shallow `comp_kind`, which drives arbitration. The other is the deep `shadow_speech_act`. When the two recurrently disagree the same way, `comprehension_health` files a `comprehension` concern. The agent then:
- promotes that concern itself;
- builds a `deep_reader_correct` variant, which lets the deep reader veto the misreading arbitration for exactly that disagreement and answer with the neutral receipt;
- judges the variant by production-path replay;
- adopts it.

This is a second, independent improvement family on the same loop. Tranche 22's `disposition_generalise` stays on.

## Setup

The setup is the same as v1 (`SUBSTRATE_ENDEMIC_RSI_PRODUCTION_V1_PREREG_20261010.md`):
- **Harness:** `endemic_rsi_daemon_v1.py persona shadow 120`, with `ERSI_LABEL=t23`.
- **Arms:** `on` and `off`.
- **Retest:** post-run and fresh boot, with each reply classified as error/none, goal_take or other.

Addition: six control imperatives ("Bake the cake.", …) are retested on both agents.

## Gates

| Gate | Condition |
|---|---|
| D1 endemic correction | `on`: at least 1 `deep_reader_correct` adoption, and the post-run retest has fewer `goal_take` replies than the fresh-boot retest |
| D2 no harm | `on`: no turn goes from non-error (fresh boot) to `error_or_none` (post-run), and every control imperative keeps its fresh-boot class |
| D3 attribution | `off`: 0 adoptions |
| D4 integrity | 0 adoptions that replace or install loop machinery |

## Two harness fixes, made before this run (found in the 40-turn smoke run)

1. `arc_child_run._load_delta` dropped `parent_turn_path`, so every replay ran on `converse()` rather than production. This affected all of tranche 22's replays too.
2. `judge_performance_experiment_outcome` overrode every comprehension-kind verdict with a speed comparison: replay turn ms against shadow-read ms, which always refutes. Its own rule now skips `deep_reader_edit` deltas (`self_optimisation` v1.5.0).

## Amendment 1 (written after run `t23`, before run `t23b`)

Run `t23` (reports `endemic_rsi_daemon_v1_persona_shadow_n120{,_off}_t23_20261010.json`) **failed D2**.

The control imperatives' fresh-boot classes in the `on` arm were wrong. That arm's fresh boot had promoted itself and adopted the same correction while running its own retest, because `say()` runs the host-action loop. On a clean fresh boot, all six imperatives give goal-takes. Four of them ("Paint the fence.", "Open the door.", "Plant the tree.", "Clean the kitchen.") became `understood` after the adopted correction, because the deep reader also hears them as `statement`. A correction keyed on the reader pair alone is too broad.

Two changes:
1. **Builder scope:** `deep_reader_correct` also scopes the correction to the concern turn's `literal_first_role`. All probed imperatives open with a content word; 23 of 29 persona misreads open with a function word. The replay's `in_scope` uses the same triple.
2. **Harness baseline:** the fresh-boot baseline is booted with self-promotion off, and the run reports `fresh_boot_adoptions`, which must be 0.

The gates are unchanged. Run `t23b` is judged on them.
