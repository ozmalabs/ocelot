# Gate Q0 (agent-labelled) and P1: judge v2 (2026-10-10)

This covers gate Q0 and phase P1 of [the open-ended self-improvement plan](OPEN_ENDED_SELF_IMPROVEMENT_PLAN_20261010.md).

## Gate Q0: the labels came from agents, not humans

The preregistration asked for **human** labels. At the user's direction, the 409-item held-out sheet (`evaluation/labels/reply_quality_heldout_v1.csv`, local only) was labelled by **four blind sub-agent labellers** instead.

How the labelling was set up:
- Each labeller got about a quarter of the rows.
- Each saw the context, inbound turn, reply and reference next turn.
- Each got the label definitions from the preregistration and was told not to read any other file: no machine scores, no criteria, no code.
- 100 items were labelled twice so labeller agreement could be measured.
- Every row records `labeller=agent:blind-subagent-k` and a short note.

Results (`evaluation/substrate_capability/reply_quality_agreement_v1.py`):

| Measure | Result |
|---|---|
| Labeller vs labeller, 100 overlapping items | 98 agree, κ 0.96 |
| ReplyQuality v1 vs agent labels, κ (gate Q0a, ≥ 0.6) | 0.937, pass |
| Precision of machine "inappropriate" (gate Q0b, ≥ 0.8) | 0.996, pass |
| Labelled items (gate Q0c, ≥ 200) | 409, pass |

How to read this:
- **Agent labels are not human labels.** The gate measures agreement with an independent LLM labeller working from the same written definitions. The definitions and the machine criteria were both written by the plan's author, so some of the agreement is shared framing, not independent validation. A human-labelled split is still needed before treating ReplyQuality as more than this.
- **The sheet is dominated by template replies.** Statement→receipt (146), statement→error (100), statement→goal-take (46) and question→none (34) together are 326 of 409 items. On those classes the machine and the labellers agree on every item, so the gate is easy on them.
- **The informative classes are small, and the machine disagrees on them:**
  - question→definition: 0 of 3 agree (machine 1, labellers 0);
  - question→clarification: 3 of 5;
  - statement→clarification: 5 of 9;
  - greetings answered to a statement or question: 0 of 3.

  By the preregistration, any criteria revision must be made on a separate split. These items are not used to tune anything.

## P1: judge v2

**What changed**
- **Fix scoring** (`scripts/convo_child_run.score_probes`, the child's scorer, now a testable function):
  - A changed flagged turn counts as a fix only if the new reply's ReplyQuality is at least acceptable-minimal. Otherwise it is a broken fix, for example a receipt given to a question. The child reports `quality_vetoed_fixes`.
  - An unflagged turn counts as `repaired` only if its quality did not fall. Otherwise it is a regression.
- **Literal form wiring:** the child passes each turn's own `literal_form` (from its communication interpretation) to ReplyQuality.
  - Before this, "Condense the data." scored as a statement, and the honest imperative goal-take reply scored 0.
  - This was found when `test_refuted_route_is_excluded_and_the_retry_genuinely_repairs` turned refuted. The criteria are unchanged: `literal_form` is an existing input of the measure that no caller had been passing.
- **Adoption veto:** `seeds/adoption_safety.json` v1.2.0 (`scripts/gen_adoption_quality_veto.py`) adds `adopt_denied_on_quality_drop`. It denies adoption when the child reports `quality_drops > 0` or `quality_delta < 0`. An Experiment with no quality report is left alone.
- **Frozen seed:** `adoption_safety` is added to `boot_all._FROZEN_SEED_IDS` and `seeds/frozen_core_manifest.json` (as is `improvement_integrity`, which the manifest had been missing since tranche 19). The loop cannot ablate or vary the gate it is judged by.
  - Plan §6 lists approving this frozen veto as a human decision. It was implemented under the user's "continue with the next tranche" instruction and is flagged here for review.

## Gate J1

Both tranche-24 arms were re-run on 120 persona turns (`endemic_rsi_daemon_v1.py persona shadow 120`, with and without `ERSI_REOPEN=0`):

| Criterion | Result |
|---|---|
| Receipt-to-question variant denied | Shown at unit level: the child scores it as a broken fix, and the veto denies a quality drop (`tests/test_judge_v2_migrated.py`). Not run as a dispatched end-to-end experiment. |
| Statement-receipt adoptions still adopted | Yes. The same 3 adoptions as tranche 24: the deep-reader correction, the generalisation and the chained generalisation. The same 7 experiments with the same outcomes. |
| error/none still below the noreopen arm | 25 vs 44. The tranche-24 arms gave the same 25 vs 44. |
| 0 regressions | No adopted experiment was vetoed for regressions or a quality drop. Each adoption's `quality_drops` is 0, with `quality_delta` +0.29 / +0.12 / +0.12. |

Post-run ReplyQuality is 0.733 with reopen and 0.583 without; the fresh boot scores 0.183.

Judge v2 changes nothing in these runs, because none of the adopted fixes lowers reply quality. What it closes is the path where a later family adopts a receipt for a question, or any change that makes a reply worse.

## Regression

Targeted scope: 28 files covering every adoption, family, integrity, dispatch and composer test, plus judge v2 and the frozen core. Nothing fails that did not already fail on the repaired-engine baseline. Two tests needed updates:
- a seed-content pin (adoption_safety now has 3 rules);
- the imperative case above, which was fixed by the literal-form wiring rather than by changing the test.

## Next

P2, concern supply v2: the interlocutor's next turn as the signal for a reply-quality concern. Per the plan, self-promotion of `reply_quality` concerns is enabled now that judge v2 exists.
