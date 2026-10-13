# P5b: the agent installs the families it authors, on a relative criterion (2026-10-10)

This follows [P5 (propose-only)](OPEN_ENDED_P5_OPERATOR_AUTHORSHIP_RESULTS_20261010.md), phase P5 of [the open-ended self-improvement plan](OPEN_ENDED_SELF_IMPROVEMENT_PLAN_20261010.md).

**The human decision (2026-10-10).** Allow the agent to install the families it authors. Harm elsewhere means a family needs balance, change or a residual somewhere else, not rejection. Everything is a tradeoff, and nothing is protected by an absolute.

**Outcome:**
- The agent authored a family that is its own held `disposition_generalise` with the harmful branch removed. On the two held-out banks it fixes the same 32 turns as its parent, with harm 0 against 25. A graph rule installed it.
- In a production run on a third held-out stream, the installed family was picked first and adopted twice, with 0 quality drops and 0 machinery adoptions.
- **Gate A5b is not met.** The counterfactual arm, with authorship off, reached exactly the same adoptions through the parent. The harmful branch the authored family removes never came up on that stream's concerns.

## What changed

**The criterion is relative** (`seeds/operator_authorship.json` v1.1.0, rules only):
- `net = fixed − harm_weight × harm` (harm_weight 1).
- A candidate qualifies when all of these hold:
  - it fixes at least `k_fix` (2) bank turns;
  - its net is positive;
  - its net beats the held family it came from, on the same banks, by at least `min_gain` (1).
- The P5 rule "0 harm and a novel class" is gone. A duplicate of its parent has gain 0, so it does not qualify.

**Change where it harms: refinement.**
- A new parameter site, `p_exclude_sources`, is added to both FamilyPrograms (`seeds/family_programs.json` v1.2.0). With the default `[]` they are still the held families, and the parity tests pass.
- After round 1, any candidate whose source rules did net harm gets a refined twin that excludes those sources. Net harm means the source's deltas' fixes minus their harm, summed over both banks, is below zero. The twin is measured the same way.

**Installation is a rule, `family_proposal_install`.** It installs the best qualifying candidate per program: highest net first, then MDL rank. It creates two nodes:
- a `FamilyProgram` holding the edited Term;
- a `VariationOp{provenance:'agent_authored', probation:1}`. This op copies its parent's `family`, cue heads, `requires_kind` and keywords. Its priority is the parent's priority minus `priority_offset` (0.5): it measured the better tradeoff, so it is tried first, and the parent stays as the fallback.

All computed values are `__term__` effect arguments read from the measured `FamilyProposal`.

**The residual is moved, not erased (`family_proposal_files_residual`).**
- Two kinds of turn are filed as `SelfConcern{kind:'family_residual'}`:
  - every bank turn the installed family harmed;
  - every bank turn left to a source it excludes.
- These concerns are not yet promotable, so no family is assigned to them. The next step is to decide which family should get them.

**Probation is judged by the family's own trials.**
- After `probation_trials` (3) judged experiments with the op as `variation_op`, one of two rules fires:
  - a support rate below `probation_min_rate` (0.34) retires it: `cue_head:'retired'`, so `variation_pick` no longer sees it and the parent takes over;
  - otherwise it leaves probation.
- This is counted here from Experiment outcomes because `variation_credit` is `self_load_only` and does not run on the production profile.

**Integrity.**
- `ImprovementIntegrity.authorship_exception` records the decision. VariationOp and FamilyProgram nodes may be *created* by this frozen install rule, and only from a measured proposal.
- A SeedDelta still may not add or edit any protected type. Judges and concern filers stay outside the loop's reach.

**Wiring.**
- `_compose_experiment_rule` now dispatches the generalise and deep-reader branches on the op's `family` (`_variation_op_family`), so an authored op builds and adopts exactly as its parent does. Every other op is unchanged.
- The child records `regressed_turns`.
- `_load_delta` now passes `witness_kind` through. This fixes the P5 observation; the fallback mapping it replaces was the same.

## Meta-evaluation: two banks together

`evaluation/substrate_capability/operator_authorship_meta_v2.py 80 4` uses the two P5 banks: 54 turns from persona_chat_20 dialogues 10–19 and 60 from persona_chat_50 dialogues 20–29. Identical deltas share one replay (one build tag), which gave 35 child replays in total.

| Candidate | Fixed (b1+b2) | Harm | Net | Gain over parent | Verdict |
|---|---|---|---|---|---|
| held generalise | 16+16 | 25 | 7 | | baseline |
| held deep reader | 12+19 | 0 | 31 | | baseline |
| generalise `p_max_miss=2` | 17+18 | 55 | −20 | −27 | no |
| generalise `realiser` (and the pair) | 0 | 0 | 0 | −7 | no |
| deep reader `held_reply=typed_ack` | 0+3 | 25 | −22 | −53 | no |
| deep reader `held_reply=unavailable_action` | 12+19 | 0 | 31 | 0 | no (same as parent) |
| **generalise, exclude `arbitrate_addressed_attention_request_as_social_act`** | **16+16** | **0** | **32** | **25** | **qualifies, installed** |
| generalise `p_max_miss=2`, exclude attention-request and unavailable-action | 17+18 | 26 | 9 | 2 | qualifies, not installed (lower net) |
| deep reader typed_ack, exclude `arbitrate_instruction_as_action_request` | 0+3 | 0 | 3 | −28 | no |

In the held generalise family, the attention-request source has net −25: 14 broken fixes plus quality drops, with no fixes. `defer_response_assertion_without_proposition_uptake` has +31. The refinement removed exactly that branch.

The installed family's residual is 10 + 18 turns: the turns that branch targeted, now filed as the agent's own concerns.

The relative ranking also kept out a candidate I would not want installed. The `max_miss=2` refinement qualifies (gain 2), but much of its extra "fixing" is the irrelevant-clarification answers P5 found ("Do you have any pets?" → "What event or evidence would help establish what caused it to close?"). These score 1 under ReplyQuality, and its net is lower than the installed family's. That is luck of the ranking, not a criterion that recognises them. The ReplyQuality gap is still open.

The meta run installed at parent priority + 0.5. Afterwards the rule was changed to parent − 0.5, the relative version above, and the A5b arm installed from the same measurements under the new rule.

## Gate A5b: production, held-out stream

Setup:
- `endemic_rsi_daemon_v1.py persona50_30_39 shadow 120` runs 115 turns of persona_chat_50 dialogues 30–39, a stream not used before, with promotion on.
- The authored arm adds `ERSI_AUTHORED=<meta report>`: the measured proposals are minted into the boot and the rules install from them.
- The counterfactual arm is the same run without that setting.

| | Authored arm | Counterfactual (authorship off) |
|---|---|---|
| Installed at boot | `authored_disposition_generalise_ccf0657d`, priority 8.5 | none |
| Experiments | authored: 2 supported (adopted), 6 abstained; deep_reader_correct: 1 supported (adopted); reply_ablation: 1 inconclusive | disposition_generalise: 2 supported (adopted), 6 abstained; deep_reader_correct: 1 supported (adopted); reply_ablation: 1 inconclusive |
| Adopted rules | the generalisation and the chained generalisation of `defer_response_assertion_…`, plus the deep-reader correction | identical |
| Post-run retest (ReplyQuality mean / error-or-none) | 0.6435 / 29 | 0.6435 / 29 |
| Fresh boot | 0.2783 / 64 | 0.2783 / 64 |
| Quality drops / machinery adoptions | 2 / 0 | 2 / 0 |
| Authored op after the run | probation 1, not retired (2 judged trials, below the 3 needed) | — |

The 2 retest quality drops are the same turns in both arms (two preference questions), so neither is attributable to the authored family. 2 of the 115 post-run retest replies differ in text between the arms, with equal scores.

**A5b is not met.**
- The authored family worked as wired: it was picked ahead of its parent, built, was judged by judge v2 and was adopted through the parent's path, with no harm.
- But it fixed nothing the parent could not. On this stream every unanswered concern either took the parent's good branch or abstained under both families (6 abstentions each).
- The authored family's value is avoided harm on concerns that would reach the attention-request branch, and none arose here.
- What it changes in production is cost and risk, not reach. On the banks, the parent would have spent trials on the refuted branch where the authored family does not.

## Verification

- **Parity.** The parametrised programs with defaults are the held families: 21 tests pass across the family, generalise, deep-reader and authorship files.
- **`tests/test_operator_authorship_migrated.py`** (8 tests). New in P5b:
  - the relative verdict matrix: harm weighed, beating the parent, one install per program;
  - installed wiring and priority;
  - the residual concern filed once;
  - probation retire and graduate;
  - the exclusion site changes the source.
- **Smoke run.** An 8-turn smoke run of the meta script installed end to end on both banks.
- **Regression.** The targeted scope is in the commit message.

**Not verified:**
- whether a retired family's turns are then picked up by the parent in production. Retirement never triggered in a real run.
- any effect of the `family_residual` concerns on the loop. They are filed but not promotable.

## What's next

- **Route the residual.** `family_residual` concerns name turns that a branch of a family harms. They are the natural input for the next family, or for a faculty, as with the P5 interrogatives. They should become promotable, and which family gets them should be a pick.
- **Make L0 adoption relative too.** It still uses absolute vetoes: `adoption_safety` denies any regression and any quality drop. Applying "everything relative" there means weighing a trial's fixes against its harm. That changes what production adopts, so I have not done it without your go-ahead.
- **Fix the ReplyQuality clarification gap** (P6). Irrelevant clarifications score as acceptable. The agent labels disagree among themselves on these items (5 off-topic clarifications to questions: 2 labelled 0, 3 labelled 1), so changing the criterion needs new labels, not a code edit.
