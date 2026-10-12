# Conversation turn ring: the reading aperture applied to turns (2026-10-10)

## What changed

Conversation history now uses the same system as reading. The reading ring
keeps N traces in a buffer at a given aperture. Older traces drop out of the
buffer, and the reader carries on from what they contributed. The
conversation now works the same way.

- **Ring (N).** The last N concluded interlocutor turns stay attended through
  the `agent received m` edge. N comes from the same held
  `reading_derive_trace_capacity` Program. It reads new `turn_capacity_*`
  attrs on the conversational `ApertureBudget` row: base 8, min 4, max 16,
  widen_step 4 (`seeds/reading_aperture.json` v1.3.0,
  `domains/reading_norms.effective_turn_capacity`).
- **Eviction.** `domains/conversation_aperture.enforce_turn_buffer` is the
  mechanical twin of `reading_scope.enforce_trace_buffer`. It runs from
  `WorldAdapter.record_turn_outcome` and evicts the turn with the lowest
  salience, and among equal salience the oldest.
  - An evicted turn swaps `received` for `agent remembers m`. Its
    interpretations swap `holds_interpretation` for
    `remembers_interpretation`.
  - Message nodes, their attributes and `interprets` edges are kept, so
    `read_corpus`, `about_message` and the judges are unaffected.
- **Salience and widening.** The graph decides both
  (`seeds/conversation_turn_ring.json` v1.0.0).
  - `turn_salience_from_outcome` takes its weights from the held
    TurnRingPolicy: unanswered 1.0, reader disagreement 0.5, other 0.0. It is
    written only after a turn has been folded into every shape that applies
    to it. A turn without salience is never evicted.
  - `conversation_widen_turn_capacity_once` is rung 1 of the reading overflow
    ladder. An eviction at or above the held threshold (1.0) widens the ring
    once.
- **Conceptual tier (the M aperture).** Each shape-owning seed folds an
  attended turn into a per-class `TurnShape`, using `has_member`,
  `member_of`, and `first_member` (the oldest member). The history rules read
  the shape, not every Message:
  - `unanswered_gap` v2.0.0: `tally_unanswered_class`,
    `mark_unanswered_shape_first_member`, `note_unanswered_turn`.
  - `comprehension_health` v1.1.0: `tally_divergence_class`,
    `mark_divergence_shape_first_member`,
    `note_recurring_speech_act_divergence`.
  - The concern, its content and its `about_message` target are the same as
    before. Only where the class count and the oldest member are read from
    has changed.
- **Latency rule.** "m is the newest shadow-read turn" used to scan every
  Message. It is now `m.shadow_seq == agent.latest_shadow_seq`, a datum the
  adapter writes next to the counter.
- **Integrity.** `TurnShape`, `TurnRing` and `TurnRingPolicy` were added to
  `improvement_integrity` `protected_node_types`, because they feed concern
  intake.

Rules fire in load order within a pass. The ring seed loads before the shape
seeds, so each shape seed marks its own `first_member` directly after its
tally. One bounded pass can then fold a turn, mark the shape and file the
concern. An earlier draft used a generic first-member rule in the ring seed.
That draft needed an extra pass and failed
`test_recurring_divergence_files_exactly_one_comprehension_concern`.

## Results

| Measure | HEAD | Ring |
|---|---|---|
| Reply differences, 150-turn offline session (`long_session_run_v1.py 150 25 --offline`) | — | 0 of 150 (also re-checked after the first-member move) |
| s/turn at turn 150 (unloaded machine) | 0.775 | 0.666 |
| Rule time per turn at turn 150 (`long_session_cost_v1.py`) | 0.49 s | 0.25 s |

Production 120-turn run (`ERSI_LABEL=ring`), ring only:
- 325 s in total;
- the same 3 adoptions as T24, including the chained adoption and the reopen;
- error/none replies after the run: 25 (fresh: 70);
- ReplyQuality 0.733 vs 0.183.

## What still grows

These costs are not bounded by the ring:
- **Message-anchored rules.** `escalate_unparsed_clauses`,
  `arbitrate_supported_event_bound_topic_goal_answer` and the `intent.json`
  `rule_intent_*` rules match through `m has_speech_act` and
  `m has_mention`, not through `received`.
- **The ingest and reading path.** `_shadow_read_turn`, `run_reading_flow`,
  `prepass_conversation_turn` / `load_conversation_content_candidates`,
  `install_word_links` and `gc.collect`.

Bounding both by the attended ring is the natural next step.

## Regression (targeted, 36 files)

The ring caused these failures, all now fixed:
- **Recurring divergence test.** Fixed by the first-member ordering above.
- **Latency test.** Premise update: the test now sets `latest_shadow_seq`
  next to the hand-made message's `shadow_seq`, as the adapter does.

These tests also fail at HEAD (`b1b36353`, after the Equilibrium-stack
merge):
- `test_residual_closure_migrated::test_knob_adoption_vetoed_on_regressions`
- `test_composer_capability_migrated::test_datum_feedback_adoption_vetoed_on_regressions`
- `test_rule_literal_variation_migrated::test_judge_rule_literal_outcome_matrix`
- `test_comprehension_self_optimisation_migrated::test_exhausted_experiments_trail_surfaces_in_status`

The knob-adoption and exhausted-trail tests were re-run at `fb3baf7f`, just
before the merge, and pass there. The other two passed in the long-session
regression run on that same commit. The veto tests fail because `a.tick()`
no longer reaches `adopt_denied_on_regression`, although `inner.run_rules()`
does. In the exhausted-trail test, `_concern_tick` mints no Experiment.
Neither is caused by the ring. Both are left to the owner of the merge.
