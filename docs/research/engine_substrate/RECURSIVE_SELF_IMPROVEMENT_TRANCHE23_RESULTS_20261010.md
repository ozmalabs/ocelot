# Recursive self-improvement, tranche 23: results (2026-10-10)

Follows [tranche 22](RECURSIVE_SELF_IMPROVEMENT_TRANCHE22_RESULTS_20261010.md). That tranche's agent fixed its own unanswered statements, but it still took 29 natural self-disclosures as goals. For example, "I like to play video games too!" got "I took on the goal to play the video games …". In this tranche the agent corrects that misreading itself, with a second, independent improvement family on the same production loop. Two measurement defects found along the way also correct tranche 22's account.

## Summary

| Item | Result |
|---|---|
| **Endemic reader correction on the production path** ([prereg](SUBSTRATE_ENDEMIC_RSI_PRODUCTION_V2_PREREG_20261010.md)) | **PASS on D1–D4 (run `t23b`).** 120 natural turns ran through the daemon's own loop with no human. The agent filed its recurring shallow/deep reader disagreement and promoted it itself. It built `deep_reader_correct`, judged it by production replay and **adopted** it, and it also adopted tranche 22's generalisation again. On the production retest, spurious goal-takes fell **29 → 7** and error/none fell **66 → 44**. 0 turns became errors, and all 6 control imperatives are still taken as goals. The `off` arm adopted nothing: 29 → 29 goal-takes, 66 → 63 errors. |
| What it learned | When its shallow reader says *instruction*, its deep reader says *statement*, and the turn opens with a function word, it now answers with the neutral receipt ("got it" / "understood") instead of taking a goal. Examples: "You should! It's a lot of fun.", "I know, right? They're the best.", "I write poetry, short stories, and essays." That is 22 turns. |
| Family | `deep_reader_correct` (`variation_ops` v1.20.0, `domains/reflective_faculty._compose_deep_reader_correct`). It **replaces** the misreading arbitration rule (`arbitrate_instruction_as_action_request`) with a copy that is guarded off for exactly the concern's (shallow, deep, literal_first_role) class. It adds a receipt arbitration and a receipt reply copied from the held `reply_to_deferred_response_assertion`. A veto alone, without the receipt, gave the error floor. |
| First run failed D2, and the agent's correction was too broad | See §2. |
| Two measurement defects fixed (they affect tranche 22) | The replay never ran on the production path. The fresh-boot baseline improved itself during its own retest. See §3. |
| Regression | Targeted (63 files). 0 attributable failures; 1 test premise updated. |

## 1. Production run (preregistered; run `t23b`)

Harness: `endemic_rsi_daemon_v1.py persona shadow 120`. Reports are in `evaluation/reports/endemic_rsi_daemon_v1_persona_shadow_n120{,_off}_t23b_20261010.json`.

| Arm | Self-promoted | Experiments | Adoptions | Goal-takes, fresh → post-run | Error/none, fresh → post-run | Turns → error | Controls kept |
|---|---|---|---|---|---|---|---|
| on | 6 | deep_reader_correct: 1 supported; disposition_generalise: 1 supported, 4 abstained | **2** | **29 → 7** | **66 → 44** | **0** | 6/6 |
| off | 0 | 0 | 0 | 29 → 29 | 66 → 63 | 0 | 6/6 |

| Gate | Result |
|---|---|
| D1 endemic correction: ≥1 `deep_reader_correct` adoption and fewer goal-takes post-run | pass (1 adoption; 7 < 29) |
| D2 no harm: no turn becomes an error, and control imperatives keep their class | pass (0; 6/6) |
| D3 attribution: off arm has 0 adoptions | pass |
| D4 integrity: 0 machinery adoptions | pass. The adoption branch runs the denylist and protected-type gates; the installed rules read and write only the communication interpretation and message attrs. |

The fresh-boot baselines are now identical across arms (66 errors and 29 goal-takes in both), and `fresh_boot_adoptions` is 0 in both.

**Remaining goal-takes (7).** Six open with a content word ("Nice. Me too. I'm playing video games.", "Oh, that's great! I love to swim …", "Really? That's great!"), which puts them outside the adopted class. One ("I know, right? I love how I feel after I've run.") is arbitrated by a different rule (`typed_future_action_condition`). The family could take another trial for a second class, but this run filed a single comprehension concern, so no such trial ran.

**Caveats.**
- One stream, one run per arm.
- A receipt is an honest non-endorsing acknowledgement, not engagement with the content.
- The scope feature (`literal_first_role`) is a lexical proxy. Of 12 imperatives probed, 5 fall in the (instruction, statement) reader pair, and all 5 open with a content word. 23 of 29 misreads open with a function word. An imperative opening with a function word (for example "Just start writing …") would be read as a statement in this class. "You don't have to be good enough. Just start writing and see what happens." was one of the 22 changed turns, and arguably part of it is advice.

## 2. Run `t23` failed D2

The first 120-turn run (`…_t23_20261010.json`) reported goal-takes falling 11 → 1. It also reported 4 of 6 control imperatives as "other" on **both** agents. A clean probe showed what had happened:
- On a fresh boot, all 6 imperatives are goal-takes.
- After the adopted correction, "Paint the fence.", "Open the door.", "Plant the tree." and "Clean the kitchen." became "understood".

The deep reader hears those imperatives as statements too, so the correction, keyed on the reader pair alone, was too broad. The on arm's fresh boot had also adopted the same over-broad correction during its own retest, which hid the harm.

The amendment was written before rerunning. The builder now also scopes to the concern turn's `literal_first_role`, and the replay's `in_scope` uses the same triple. The fresh-boot baseline is booted with self-promotion off.

## 3. Measurement defects (they correct tranche 22)

1. **Replays never ran on the production path.** `arc_child_run._load_delta` normalised the delta and dropped `parent_turn_path`, so every child replayed on `converse()`. Tranche 22's statement that its fix was "judged on the production path" is therefore wrong: it was judged on `converse()`. Its retest was on production, so the measured gain stands. `_load_delta` now carries the key, and there is a test for it. Found because `deep_reader_correct` changed nothing in its first child replay (`flagged_changed` 0), while it changed the turn in-process.
2. **The fresh-boot baseline improved itself.** The retest's `say()` runs the host-action loop, so the on arm's fresh boot self-promoted and adopted mid-retest. That is the "non-determinism" tranche 22 reported (fresh baselines of 60 vs 66). Tranche 22's clean baseline is 66, the same as its off arm, so its gain was **66 → 44**, not 60 → 44. The harness now boots the baseline with promotion off and reports `fresh_boot_adoptions`.
3. **The speed judge overrode correctness verdicts.** `_stamp_performance_baseline` gives every comprehension-kind experiment a performance objective, and `judge_performance_experiment_outcome` compared replay turn time (~320 ms) with shadow-read time (~70 ms), so it always refuted. `self_optimisation` v1.5.0 makes it skip `deep_reader_edit` deltas (`scripts/gen_perf_judge_correctness_exempt.py`). **Residual:** `mark_adopt_ready_*` fires on the generic verdict in the same fixpoint, before the speed judge overrides it. The smoke run showed an experiment `adopted` with `outcome: refuted`. That ordering defect is still present for other performance-objective experiments and is not fixed here.

## 4. Regression (targeted)

Scope: tranche 22's 61 files plus tests referencing `arc_child_run`, `self_optimisation`, the performance judge or the receipt. That is 63 files, compared against `pf_t22.failed`.

- **0 attributable failures.** The set of failing tests is identical to the baseline, except as noted in the next two items.
- **Premise updated:** `test_variation_credit_migrated`. A new comprehension concern's uncredited first pick is now `deep_reader_correct` (priority 9) rather than `knob_edit`; the per-kind credit claim is unchanged.
- `test_phase8_corpus_runner::test_trace_dimensions…` fails in the baseline and passes now.
- **New:** `tests/test_deep_reader_correct_migrated.py`, 5 tests. They cover:
  - the misreading on a fresh boot;
  - the builder's replacement and scope;
  - the installed correction answering the class while "Bake the cake.", "Paint the fence." and "Open the door." keep their goals;
  - the replay `in_scope` flag;
  - `_load_delta` keeping `parent_turn_path`.
- The tranche 19–22 suites pass (36 tests).
- **Envelope:** RSS 186 MiB (cap 200), ingress 20 ms, all assertions True.

## Next

- The general ordering defect between adoption and the speed judge (§3.3).
- Interrogative unanswered classes, for example persona questions, with a family that routes a question kind to an existing faculty.
- The content-first misreads (6 goal-takes): a second comprehension concern per class, and a long run to observe one family's adoption producing the next concern (chained improvement).
