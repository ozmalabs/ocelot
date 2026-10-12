# P3a: one generic whole-delta adoption path, and the integrity gap (2026-10-10)

This is phase P3 of `OPEN_ENDED_SELF_IMPROVEMENT_PLAN_20261010.md`, first part. P3 does not depend on gate Q0 (the human labels), so it can go ahead now.

## What changed

**One adoption path.**
- Every family's fold-back is the same five operations on the parent:
  - tombstone named rules;
  - install rules;
  - set node attributes, finding the node by a key attribute;
  - add nodes, optionally `teach()`-ing them into a seed;
  - remove Concepts.
- `domains/reflective_faculty._adopt_whole_delta` applies a *plan* made of these five lists. It writes the full prior state onto the Adoption as `prior_state`:
  - each removed rule's exact JSON;
  - each added rule's name;
  - each edited attribute's observed old value;
  - each added node's id;
  - each removed Concept's attributes.
- `_revert_whole_delta` undoes exactly what `prior_state` records, for any family.
- The family branches are now thin translations of their delta into a plan (`_adoption_plan`). Family markers are checked in the old branch order. Each family keeps its old Adoption attributes, return keys and TaughtHint wording.
- A delta with no family marker but `whole_delta=1.0` is adopted as written.
- Adoption records minted before P3 (they have no `prior_state`) are still reverted by the old per-family code, now in `_revert_adoption_legacy`.

**Revert bugs fixed.** Each is covered by a test in `tests/test_whole_delta_adoption_migrated.py`.
- A `disposition_generalise` adoption stored no original state, so it could not be reverted.
- A `deep_reader_correct` revert looked up its comma-joined list of added rules as a single rule name. The original rule came back, but every added rule stayed live.
- A reverted Experiment still carried `adopt_ready`, so the next `perform_adoptions` pass re-adopted it. Revert now sets `adoption_reverted` on the Experiment, and `perform_adoptions` skips it.

**Integrity gap closed.** The shared module is `domains/delta_integrity.py`.
- The gate now reads the whole delta:
  - each removed rule must pass `_rule_denylisted`;
  - an added rule may not name a `protected_node_types` type;
  - a node-attribute edit or a node addition may not target a protected type.
- Before, only rules were checked, and only in some branches. In the parent and the child alike:
  - a knob delta could rewrite a `VariationPolicy`;
  - a shape-mint delta could teach any node type.
- Node-level edits of `RuleSummary` and `SeedSummary` are also refused. These are not loop machinery, but their `skippable` flags are the adoption gate's own evidence, so a delta that edits them could open the gate it is judged by.
  - This is a host-side refusal. The held `protected_node_types` list is unchanged, because editing that list is a human decision.
- In the child, `apply_node_attr_delta` and `apply_concept_delta` (`scripts/arc_child_run.py`, shared by both child runners) drop refused items. The conversation child reports `integrity_refused`, and ingest copies it onto the Experiment.
- Added rules are still trialled in the child and denied only at adoption. This is unchanged.

## Gate G3

| Criterion | Result |
|---|---|
| A constructed knob delta targeting `VariationPolicy` is denied | Denied at adoption, policy unchanged, no Adoption minted. The child appliers refuse it too. (`test_knob_delta_targeting_variation_policy_is_denied`, `test_child_appliers_refuse_loop_and_provenance_types`) |
| Every existing family test passes | No new failures in a targeted regression of 26 files: every adoption, revert, family, integrity, dispatch and composer test file. Every failure in the run is also on an earlier baseline failure list or fails the same way at HEAD. |
| The tranche 22–24 production run reproduces its adoptions exactly | Yes, against the conversation-turn-ring run, 120 persona turns (details below). |

Production run detail, comparing the ring run with the P3 run:
- **Adoptions:** the same 3, with the same rules removed and added: the deep-reader correction, the generalisation, and the chained generalisation.
- **Experiments:** the same 7, each with the same family and outcome.
- **Reopen:** the same reopen.
- **Post-run retest:** the same classes (other 88 / error-or-none 25 / goal-take 7).
- **ReplyQuality:** 0.733 (post-run) vs 0.183 (fresh), in both runs.
- **Fresh-boot retest:** identical replies.
- **Differences:** four first-pass turns (62, 67, 70, 75) timed out in the P3 run. Each is a question routed to online topic search. Turns 62 and 67 had a search answer in the ring run, and turns 70 and 75 had the error surface. In the post-run retest, turns 70 and 75 show an empty reply instead of the error surface. That changes no class.
  - These turns are network-bound, and nothing in P3 touches that path.

New tests in `tests/test_whole_delta_adoption_migrated.py` (8, all pass):
- `VariationPolicy` knob denied;
- child appliers refuse loop and provenance types;
- protected node addition denied;
- `SeedSummary` edit denied;
- generalise adoption reverts and is not re-adopted;
- deep-reader revert removes every added rule;
- full whole-delta round trip (rules, attributes, Concepts added and removed);
- a stale plan changes nothing.

## Not done yet (P3b)

- **Declared witnesses with one generic judge.** The five family judges in `seeds/self_optimisation.json` (performance, knob, rule literal, datum feedback, shape mint) should become `{witness_kind, direction}` on the delta, read by one judge. The child's per-family probe flags should go the same way. That is a seed rewrite with its own parity gate: the same verdicts on every recorded experiment.
- **Composer adopt-ready rule.** The composer's `mark_adopt_ready_*` rule does not yet accept a `whole_delta`. Until it does, only the hand-minted or test path can make such a delta adopt-ready. P4's FamilyPrograms will mint whole deltas, so this belongs there.
