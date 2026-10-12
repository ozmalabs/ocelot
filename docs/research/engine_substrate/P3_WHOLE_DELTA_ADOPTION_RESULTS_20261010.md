# P3: one generic whole-delta adoption path, the integrity gap, and declared witnesses (2026-10-10)

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

## P3b: declared witnesses and one generic judge

**What changed** (`seeds/self_optimisation.json` v1.7.0, generated by `scripts/gen_witness_judge.py`):

- **Before:** five family judges, for performance, knob, rule literal, datum feedback and shape mint. All five had the same shape:
  - any regression refutes;
  - otherwise, if the variant's measure moved the family's way, the trial is supported;
  - if the measure is unchanged, it is inconclusive;
  - if it moved the other way, it is refuted.
- **Now:** a SeedDelta *declares* its witness, and one rule, `judge_declared_witness_outcome`, reads the declaration. The declaration has four parts:
  - `witness_kind`: latency, reforms, rule_witness_fires, interlocutor_belief or classified_parties;
  - `witness_direction`;
  - `witness_control_attr` and `witness_control_on`;
  - `witness_variant_attr`.
- **Family-to-witness mapping:** this is graph data. There is one `declare_witness_<family>` rule per family marker, and each writes the declaration only when the delta has none yet.
  - They are ordered so a family witness takes precedence over the performance objective. Under the old judges, the family judge ran after the performance judge and overwrote its verdict.
  - A delta that declares its own witness needs no family marker. This is what P4's FamilyPrograms will produce.
- **Child probes** (`scripts/convo_child_run.py`): the child now measures what `witness_kind` names, passed across by `_seed_delta_of`. If the delta reached the child before its declaration rule ran, the child falls back to the family markers, which give the same mapping.
  - Node-attr deltas are now applied whenever the delta has them, independently of the reforms probe.
- **Judged flags:** the per-family `*_judged` flags are replaced by `witness_judged`. I updated the readers: the reset list in `experiment_dispatch.restart`, and four test assertions that now check `witness_judged`. One test pinned the old rule name, and I updated that pin too.

**Parity**
- **Verdict matrix:** `tests/test_witness_judge_migrated.py` runs 141 cases. It compares the new rules against the five v1.6.0 judges, frozen in `tests/fixtures/family_judges_self_optimisation_v1_6_0.json`. The cases cover:
  - every family;
  - every direction value, including an absent direction;
  - regressions of 0, 2 and none;
  - variant greater than, equal to and less than control;
  - a missing control or variant;
  - the deep-reader exemption;
  - knob plus performance objective together.

  All 141 give the same outcome as the frozen judges, and the matrix produces every verdict (it is not vacuous).
- **Targeted regression:** I re-ran the same 27 files. Nothing fails that did not already fail in the P3a run, apart from the rule-name pin above, which I updated.
- **Production run** (120 persona turns): identical to the conversation-turn-ring run:
  - every first-pass reply and every post-run retest reply;
  - the 3 adoptions, the 7 experiments with their outcomes, and the reopen.

  This also confirms that the four first-pass differences in the P3a run were network timing.

**Engine-adjacent fix.** `_NATIVE_SUBSTRATE_LOCKS_GUARD` in `substrate/world_adapter.py` is now an `RLock`.
- A facade's `__del__` takes this guard. A garbage collection triggered inside a `with` block on the guard runs that `__del__` on the same thread, so a plain `Lock` deadlocked.
- Observed: the 30th `WorldAdapter(seeds=())` in a test process hung in `__init__` → `__del__`. The hang was intermittent. With the fix, the test passed in 4 of 4 runs.

## Not done yet

- The composer's `mark_adopt_ready_*` rule does not accept a `whole_delta` yet. That belongs with P4, whose FamilyPrograms will mint whole deltas that declare their own witness.
- The family markers remain on deltas because the declaration rules and the child fallback read them. They can be retired once every builder declares its witness directly (P4).
