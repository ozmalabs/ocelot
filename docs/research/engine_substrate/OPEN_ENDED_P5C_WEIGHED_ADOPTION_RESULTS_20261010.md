# P5c: adoption is weighed, and a regression is relative to the frame (2026-10-10)

This follows [P5b](OPEN_ENDED_P5B_AUTHORED_FAMILY_INSTALL_RESULTS_20261010.md) and is part of [the open-ended self-improvement plan](OPEN_ENDED_SELF_IMPROVEMENT_PLAN_20261010.md).

**The human decision (2026-10-10):**
- Everything is weighed.
- "Regression" is only relative to the frame. In some cases it is simple; in many it is more complex.

**Outcome:**
- The L0 adoption gate no longer holds absolute vetoes. A changed reply is a regression only if it is worse in the frame it is measured in.
- On two production streams, the weighed gate and the old absolute gate made identical adoptions. Every production trial was either clean or clearly worse, and none had a lateral change. The change is correct but inert there.

## What changed

**The child reports a change in its frame** (`scripts/convo_child_run.score_probes`). An unflagged turn whose reply changed against the paired control is classed as one of three:
- **Regression.** It is worse: its ReplyQuality fell, or a working turn now fails. A turn that now fails counts even when both replies score 0; this is the simple case.
- **`improved_change`.** Its quality rose.
- **`lateral_change`.** Same quality, different text. The frame cannot tell these apart, so the change is an uncertainty, not a verdict.

`changed_unflagged` keeps the pre-P5c regression count, so old and new can be compared.

The score is unchanged in form: fixes, minus broken fixes, minus regressions. Before, a lateral change cost −1; now it costs nothing here. The ingest step copies `flagged_changed`, `lateral_changes` and `improved_changes` onto the Experiment.

**Adoption is weighed** (`seeds/adoption_safety.json` v1.3.0, from `scripts/gen_weighed_adoption.py`).
- The exchange rates are data: `AdoptionWeighing{fix_weight 1.0, gain_weight 0.5, harm_weight 1.5, lateral_weight 0.25, min_net 1.0}`.
- The weighed net is:
  `1.0 × fixes + 0.5 × improved − 1.5 × (regressions + broken fixes) − 0.25 × lateral`
- `adopt_weighed_net` records the net on every trial the child reported. It is computed when the child's report is ingested, as the old regression veto was, so it cannot race `perform_adoptions`.
- `adopt_denied_on_weighed_net` denies a trial whose net is below `min_net`.
- `adopt_denied_on_regression` and `adopt_denied_on_quality_drop` are removed.
- `adopt_denied_on_overridden_verdict` stays. It checks that the final verdict is still `supported`; it is not a harm rule.

**Declared-witness families are weighed by their own judge** (`seeds/self_optimisation.json` v1.8.0, `judge_declared_witness_outcome`). These are the knob, rule-literal, datum-feedback, shape-mint and performance families.
- The measure moving the declared way counts as one fix.
- The trial is supported only if the same weighed net reaches `min_net`. If harm outweighs the move, it is refuted.
- With no `AdoptionWeighing` held, the v1.7.0 rule applies (any regression refutes), so the P3b verdict matrix is unchanged on a bare graph.

**The weights are a choice, held as data.** A turn made worse costs 1.5 fixes, because harm to a working turn should count for more than failing to fix a broken one. A lateral change costs a quarter, for the frame's blindness. Both are protected seed data, inside the frozen `adoption_safety` seed.

## Production: weighed vs absolute, same streams

Both arms ran `endemic_rsi_daemon_v1.py <stream> shadow 120` with the P5b authored family installed (`ERSI_AUTHORED`).
- **Weighed arm:** this commit.
- **Absolute arm:** the P5b commit `5c74ec4a`, run from a git worktree. The engine is identical.

**Preregistered:**
- **W1:** the weighed gate admits at least one adoption the absolute gate denies.
- **W2:** post-run reply quality is no lower, and to_error turns are no more.
- **W3:** 0 machinery adoptions.

| Stream | Arm | Adoptions | Post-run quality mean | Error/none post-run | to_error | Supported but not adopted |
|---|---|---|---|---|---|---|
| persona (dialogues 0–, 120 turns) | weighed | deep-reader correction, generalisation, chained generalisation | 0.6917 | 30 | 1 | 0 |
| | absolute | the same three | 0.6917 | 30 | 3 | 0 |
| persona50_40_49 (unused before) | weighed | the same three | 0.700 | 21 | 0 | 0 |
| | absolute | the same three | 0.700 | 21 | 0 | 0 |

The child reports in the weighed arms cover 8 trials. Six were clean: one fix each, no unflagged change. Two were `reply_ablation` trials with 2 and 3 unflagged changes, all worse in the quality frame. Both arms refuted them. There were 0 lateral and 0 improved changes.

**Gate results:**
- **W1: not met.** No trial in either stream was in the region where weighing differs.
- **W2: met.** Quality means are identical. The to_error difference on persona (1 against 3) is between fresh-boot retests, which this change does not touch.
- **W3: met.**

The weighing matters for trials that fix something while moving other turns sideways or making a few worse. On the P5 banks those were the held families' harmful branches, which harm far more than they fix. In these production streams such trials did not occur.

## Verification

- **Unit tests** (`tests/test_judge_v2_migrated.py`): the weighed adoption matrix and the frame classification:
  - the same quality is lateral;
  - a higher quality is an improvement;
  - a working turn now failing is a regression even when both score 0.
- **`tests/test_witness_judge_migrated.py`:** the 141-case parity matrix still holds on a bare graph, and a new weighed case was added.
- **End to end** (`tests/test_adoption_safety_migrated.py`): an identity-rule replacement fixes 1 flagged turn and moves 2 unflagged turns laterally. It is judged supported with a weighed net of 0.5, is denied, and the denial is readable over natural language.
- `tests/test_adoption_overridden_verdict_migrated.py` now follows production order: the witness is declared when the experiment is minted, before the child's report arrives.
- **Regression scope:** see the commit message.

## Not done

- **Only one frame is measured.** The only frame is ReplyQuality plus the error floor. "More complex" frames could resolve a lateral change instead of pricing it:
  - the interlocutor's next turn (P2's reply-feedback datum);
  - the concern's own scope;
  - topic continuity.
  That is the natural next step: a lateral change becomes a question for another frame.
- **Other absolutes remain.** These are still absolute:
  - the integrity gate (a delta may not touch protected types);
  - the provenance denylist;
  - judge v2's "a fix below acceptable-minimal is a broken fix".
  These are about who may change what, and what counts as a fix, not about weighing harm. I left them.
- **The weights are not learned.** The exchange rates are set by hand. A trial's later fate (reverted adoptions, interlocutor feedback) could calibrate them, which is a P6-style criterion proposal.
