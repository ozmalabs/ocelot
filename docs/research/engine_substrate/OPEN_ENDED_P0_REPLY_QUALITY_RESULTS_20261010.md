# Open-ended self-improvement P0: ReplyQuality v1 results (2026-10-10)

Phase P0 of the [plan](OPEN_ENDED_SELF_IMPROVEMENT_PLAN_20261010.md). Preregistration: [gate Q0](SUBSTRATE_REPLY_QUALITY_Q0_PREREG_20261010.md).

## Summary

| Item | Result |
|---|---|
| Measure | `domains/reply_quality.py` with criteria held as data (`domains/reply_quality_criteria_v1.json`, v1.1.0). It is **report-only**: computed in the child replay (result fields and Experiment attributes `quality_*`) and in the production harness, and it gates nothing. |
| Gate Q0 (agreement with human labels) | **Not yet run. It needs the human labels.** The sheet is built: 409 unique held-out (inbound, reply) pairs in `evaluation/labels/reply_quality_heldout_v1.csv`. |
| How much of tranches 22–24's improvement is real (machine measure, unvalidated) | Of the 64 turns the adoptions changed in the 120-turn production stream, 63 went from inappropriate to acceptable-minimal: errors and goal-takes became "got it". **1 became appropriate. 0 got worse.** |
| Transfer to unseen dialogues | On 269 held-out turns (dialogues 10–19), installing the agent's 3 adopted changes raised the mean score from **0.156 to 0.658**: 135 turns improved, 0 got worse. Every gain was a receipt replacing an error, a goal-take or nothing. |
| Questions | After self-improvement, 0 of 33 production questions get an appropriate reply. 16 are minimal and 17 inappropriate. |
| A production defect found | On one long session, per-turn time grows from 0.5 s to 75 s over 200 turns (§3). |

## 1. The measure

**Inbound class:** greeting, question, imperative or statement. A rhetorical tag ("I know, right?") is not a question.

**Reply class:** none, error, pending, goal-take, deferred, honest not-knowing (gap floor), receipt, greeting, clarification, definition, first-person content or other content.

**Score:**
- **2, appropriate:** a greeting answered by a greeting; on-topic content; a first-person answer to a question addressed to the agent.
- **1, acceptable-minimal:** a receipt to a statement; a clarification; honest not-knowing; a goal-take for a real imperative; an off-topic or definitional reply.
- **0, inappropriate:** error or none; a receipt or goal-take in answer to a question; a goal-take for a statement.

**Criteria v1.1.0** fixed three defects, all found on the production stream (dialogues 0–9) before any held-out labels existed:
- a first-person token deep inside a quoted encyclopaedia passage made the reply "about the agent";
- "I don't hold anything about X" was not recognised as honest not-knowing;
- "I know, right?" counted as a question.

**Limits:** v1 cannot check that a first-person reply answers *this* question, or that content is true. Q0's per-class agreement will show where that misleads.

## 2. Tranches 22–24 scored (report-only)

**Production stream** (`endemic_rsi_daemon_v1_persona_shadow_n120_p0_20261010.json`, rescored with v1.1 in `….quality.json`). It is the tranche-24 configuration with 3 adoptions. Errors fell 66 → 25 and goal-takes 29 → 7, reproducing tranche 24.

| | Mean | Appropriate | Minimal | Inappropriate |
|---|---|---|---|---|
| Fresh boot | 0.217 | 5 | 16 | 99 |
| After self-improvement | 0.733 | 5 | 78 | 37 |
| The 64 changed turns, before | 0.031 | 1 | 0 | 63 |
| The 64 changed turns, after | 1.000 | 1 | 62 | 1 |

Transitions on the changed turns:
- statement: error → receipt (34);
- statement: goal-take → receipt (22);
- statement: none → receipt (3);
- question: none → definition (2);
- question: error → receipt (1);
- question: none → honest not-knowing (1).

**Child replays:** the three supported experiments' own replay reported `quality_delta` +0.29, +0.12 and +0.12, with 0 quality drops.

**What this says (if Q0 validates the measure):** the loop's adoptions so far are real but shallow. They turn inappropriate replies into honest minimal ones and never make a turn worse, but they almost never produce an appropriate reply. The old judge's blind spot ("got it" answering a question counts as a fix) occurred in 1 of 64 changed turns. That is small, and it is the case judge v2 (P1) will deny.

## 3. Long-session slowdown (new finding, not yet investigated)

Building the label sheet on one agent session, per-turn time grew with session length:

| Turns into the session | Mean seconds per turn |
|---|---|
| 1–25 | 0.5 |
| 51–75 | 3.9 |
| 101–125 | 7.0 |
| 151–175 | 19.3 |
| 176–200 | 34.2 |
| 201–225 | 74.7 |

The growth is superlinear. The production daemon would degrade the same way in a long conversation. The builder was changed to use a fresh boot per dialogue seat.

Candidate cause, untested: rules that `Count` over all `Message` nodes for every new message. One example is tranche 22's `note_unanswered_turn` recurrence count, which makes each turn O(n), so a session costs O(n²). This needs a measured diagnosis before any fix.

## 4. Labelling (human step, required for Q0)

`evaluation/labels/reply_quality_heldout_v1.csv`:
- 409 unique pairs, from held-out dialogues 10–19 in both speaker seats;
- the agent's replies on a fresh boot (269) and with its adopted changes installed (269), of which 129 pairs are shared;
- columns: context, inbound, reply, the real next turn, and a blank `label`.

The machine scores live only in the `.meta.json`. On these items the machine distribution is 0: 335, 1: 187, 2: 16, counting each agent's items separately. That is heavily skewed, so κ will be sensitive to the inappropriate/minimal boundary, which is exactly the boundary P1 gates on.

To score: fill `label` with 2, 1 or 0, then run `evaluation/substrate_capability/reply_quality_agreement_v1.py`. The gate needs at least 200 labelled items, κ ≥ 0.6, and precision ≥ 0.8 for machine "inappropriate".

## 5. Regression

Targeted, 13 files: the replay, ingest, self-improvement, adoption and variation families. 0 new failures against the baselines. New tests: `tests/test_reply_quality_migrated.py` (14).
