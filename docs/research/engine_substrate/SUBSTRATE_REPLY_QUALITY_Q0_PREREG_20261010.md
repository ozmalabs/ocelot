# ReplyQuality v1, gate Q0: preregistration (2026-10-10, plan P0)

Part of [the open-ended self-improvement plan](OPEN_ENDED_SELF_IMPROVEMENT_PLAN_20261010.md).

## Claim under test

ReplyQuality v1 (`domains/reply_quality.py`, criteria `domains/reply_quality_criteria_v1.json`) agrees with human judgement about whether a reply fits the turn it answers well enough to gate adoptions (P1). It is a surface proxy, not a judgement:
- the inbound's act (greeting, question, imperative, statement);
- whether a question is addressed to the agent;
- the reply's class (none, error, receipt, goal-take, clarification, definition, first-person content, other content);
- topical overlap.

## Data

**Held-out turns:** persona_chat_20 dialogues 10–19, both speakers' seats. The production stream uses only User 1 of dialogues 0–9.

**Replies** come from two agents:
- a fresh conversation boot;
- the agent after the 120-turn production stream with self-improvement on.

There are unique (inbound, reply) pairs, written in shuffled order to `evaluation/labels/reply_quality_heldout_v1.csv` (`evaluation/substrate_capability/reply_quality_label_set_v1.py`). The labeller sees the context (previous two turns), the inbound, the reply and the real next turn. They never see the machine score.

**Labels:**
- **2, appropriate:** a reasonable conversational reply to this turn.
- **1, acceptable-minimal:** honest but thin, for example a bare acknowledgement of a statement, a clarification request, or an honest "I can't".
- **0, inappropriate:** an error, no reply, a non-answer to a question, a misread (e.g. taking a statement as a goal), or an off-topic definition.

## Gate

`evaluation/substrate_capability/reply_quality_agreement_v1.py`:

| Gate | Condition |
|---|---|
| Q0a | Cohen's κ (unweighted, 3 classes) ≥ 0.6 between human labels and v1 scores |
| Q0b | Precision of v1 "inappropriate" against human "inappropriate" ≥ 0.8 |
| Q0c | At least 200 labelled items |

If Q0 fails, the criteria are revised on a **separate** labelled split before any judge uses them. The criteria are never tuned on the items that measure them.

## What it does not claim

v1 cannot tell whether a first-person reply actually answers the question asked, or whether content is true. The confusion matrix by machine class (`by_machine_class`) shows where it misleads.
