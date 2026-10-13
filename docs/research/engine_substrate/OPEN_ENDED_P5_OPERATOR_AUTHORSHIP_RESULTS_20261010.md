# P5: operator authorship, propose-only (2026-10-10)

This is phase P5 of [the open-ended self-improvement plan](OPEN_ENDED_SELF_IMPROVEMENT_PLAN_20261010.md). It is the first P5 tranche and runs in propose-only mode: nothing the agent authors is installed.

**Gate A5a is not met.** On two held-out banks, no agent-composed family qualified. The reasons are specific and are listed under "What the banks show".

## What changed

**Parameter sites on the held families.** `scripts/gen_family_programs.py` now opens each FamilyProgram with Let-bound Lits. The paths of these Lits are recorded in the new `parameter_sites` attr (`seeds/family_programs.json` v1.1.0). With the defaults, the programs are the held families:
- `family_disposition_generalise` has two sites:
  - `p_max_miss` (default 1): the most guards it may relax. Every missed guard is relaxed through a Fold.
  - `p_source_role` (default `arbitration`): which rule it copies. `realiser` copies the reply rule that realises the turn's own arbitration basis, instead of the arbitration rule.
  - Within the family, candidates are now ordered by fewest relaxed guards, then by name. With one allowed miss this is exactly the old name order.
- `family_deep_reader_correct` has one site, `p_held_reply`: the held reply rule whose effects realise the receipt.

**`seeds/operator_authorship.json`** (from `scripts/gen_operator_authorship.py`) holds the grammar and the decision:
- `OperatorAuthorshipPolicy{k_fix:2, max_candidates:12, max_size:2, bank_max_quality:0, propose_only:1}`;
- three `FamilyMutation{program, site, values}` nodes;
- four rules that decide each measured `FamilyProposal`:
  - `held_baseline`;
  - `qualifies`: at least k_fix fixes, 0 harm, and at least one fixed class that no held family fixes;
  - `does_not_qualify`;
  - `install_blocked`, set on a qualifying proposal while propose-only holds.

The seed is in `_FROZEN_SEED_IDS` and in the manifest. Its three node types are added to `improvement_integrity` `protected_node_types`, which is flagged for human review like the earlier additions. The seed is also added to the conversation self-improvement anchors.

**`domains/operator_authorship.py`** (mechanical):
- It enumerates candidates in MDL order: the held programs, then single edits, then pairs on one program.
- It applies edits with the engine's `EditAt`.
- It runs a candidate on a bank turn through the production concern context: SelfConcern → StandingConcern, then `_family_program_env`.
- It mints `FamilyProposal` nodes for the rules to decide.

**Child runner.** A delta may now set `flagged_turn_ids` (`scripts/convo_child_run.py`, passed through `arc_child_run._load_delta`):
- exactly those turns are flagged;
- a flagged turn that got no reply is still a probe, with recorded reply `''`;
- the result adds per-turn `flagged_outcomes` and `quality_drop_turns`.

Without the option, nothing changes.

## Gate A5a

**Harness.** `evaluation/substrate_capability/operator_authorship_a5a_v1.py <n> <parallel> <bank>` runs these steps:
1. **Stream.** A fresh boot (promotion off) answers 80 held-out turns offline on the production path.
2. **Bank.** The bank is every turn the agent's own production datum scored 0 (`reply_quality_score`). Each turn is classed by `reply_quality_reason`.
3. **Deltas.** Each of the 7 candidates (2 held + 5 authored) builds its delta on every bank turn.
4. **Replays.** Each distinct delta is replayed once by the conversation child (judge v2, production path, snapshot boot), with every bank turn flagged.
5. **Measures.**
   - A bank turn counts as fixed by a candidate when one of the candidate's replays scores it `fixed`.
   - Harm is the sum of regressions, broken fixes and quality drops over all of the candidate's replays.

**Banks.**
- Bank 1 is the project's held-out stream (persona_chat_20 dialogues 10–19).
- It held no short-agreement turn of the kind the realiser site targets, so a second bank was added: persona_chat_50 dialogues 20–29, which nothing in the project had used before.
- Both results are reported. Neither bank was rerun.

| | Bank 1 (54 turns, 33 replays) | Bank 2 (60 turns, 63 replays) |
|---|---|---|
| Bank classes | statement→error 39, statement→goal_take 7, question→error 6, question→none 1, statement→none 1 | statement→error 31, statement→goal_take 14, question→error 7, imperative→none 3, statement→none 2, question→none 1, greeting→error 1, question→receipt 1 |
| held generalise | fixed 16 (statement→error, question→error), harm 10 | fixed 16 (statement→error, greeting→error), harm 15 |
| held deep reader | fixed 12 (statement→error, statement→goal_take), harm 0 | fixed 19 (+ imperative→none), harm 0 |
| `p_max_miss=2` | fixed 17, novel question→none, **harm 24** | fixed 18, novel question→error and question→none, **harm 31** |
| `p_source_role=realiser` | built on 0 turns | built on 2 turns, fixed 0, harm 0 |
| `p_max_miss=2 + realiser` | built on 0 | the same as realiser |
| deep reader, `p_held_reply=typed_acknowledgement` | fixed 0, harm 52 | fixed 3, harm 113 |
| deep reader, `p_held_reply=unavailable_action` | the same as held (12, harm 0), not novel | the same as held (19, harm 0), not novel |
| **Qualified** | none | none |

Reports: `evaluation/reports/operator_authorship_a5a_v1_n80_20261010.json` and `..._p50_20_29_n80_20261010.json`, local only.

## What the banks show

1. **Short agreements cannot be credited by the replay.**
   - The realiser variant works. Installed, it answers "Yes, I do." after "Yeah, it's the best.", which is pinned in the tests.
   - On bank 2 it built for both of its target turns, "Exactly." and "Yeah, it's a lot of fun. …". These are `typed_acknowledgement` turns whose reply rule misses only on `interaction_relation` (`''` against `response`).
   - In the paired control replay, those turns are *already* answered ("got it"). The production failure depends on conversational state that the snapshot replay does not reproduce.
   - The judge therefore correctly credits the delta with nothing.
   - The same effect shows on statement turns: several production errors are answered by the control replay.
2. **Interrogatives need a faculty, not an operator.**
   - The only route in the grammar that reached question classes was the two-guard relaxation of the anaphoric-reason repair. It "fixed" "Do you have any pets?" with "What event or evidence would help establish what caused it to close?", and "What's it like to save someone's life?" with "what's 'What's'?".
   - ReplyQuality scores any clarification as 1 for a question, so judge v2 counts both as fixes.
   - The family failed only because of harm elsewhere, not because these replies were recognised as bad. This is the receipt ceiling the plan names (§5), with one difference: here the ceiling is a clarification, not a receipt.
   - This is a ReplyQuality gap. Fixing it is a criterion change, which is P6 or a human decision. Judges are frozen.
3. **The family-level criterion is stricter than any held generalise family meets.**
   - The held `disposition_generalise` does harm 10 and 15 on the two banks. Its `language_social_act_evidence` relaxation of the attention-request arbitration turns answered statements into errors.
   - In production this costs nothing, because each such delta is refuted by its own L0 replay.
   - Under "0 harm on every bank concern", only the deep reader is clean. Whether a family's harm should count before or after L0 filtering is a design question for the human. The criterion was left as preregistered.
4. **Kind-routing mutations cannot show novelty on this bank by construction.**
   - The bank applies every family to every bank turn, so the P4 doc's suggested first target cannot add a novel class. That target was gating `deep_reader_correct` by a different `requires_kind` (reply_quality concerns about statement→goal_take).
   - The held deep reader already fixes goal_take turns there.
   - The value of such a mutation is in production routing, which only A5b can measure.

## Verification

- **Parity.** With the defaults, the parametrised programs are the held families:
  - `family_program_parity_v1.py 40 persona`: 41 + 41 cases equal, 17 + 11 built;
  - the three family test files: 15 passed.
- **New tests.** `tests/test_operator_authorship_migrated.py` (6 tests):
  - the seed is frozen and protected, and every mutation names a declared site;
  - enumeration follows MDL order and the caps;
  - default edits are the identity;
  - fewer relaxed guards win;
  - the realiser variant answers a short agreement once installed;
  - the rules decide each verdict and block install.
- **Regression.** The targeted scope (36 files: the P4 scope plus the new tests) has 23 failing tests, all in the pre-existing baseline list. There are no new failures. The frozen-core manifest drift those tests report predates this change: `program_self_modification` and `core_seed_ids`. The new id is in both lists.

**Not verified:**
- the cost of a production run with the seed loaded. The seed holds rules over FamilyProposal nodes only, and none exist in a normal run.
- Rust tests: the engine source did not change.

**Observed, not fixed here.** `arc_child_run._load_delta` drops the P3b `witness_kind` key. The child therefore always uses its fallback marker mapping. This is harmless today because the two mappings are the same. Fixed in P5b.

**Superseded the same day:** the human decision to allow installation, with a relative criterion, is in [P5b](OPEN_ENDED_P5B_AUTHORED_FAMILY_INSTALL_RESULTS_20261010.md).

## Next

- A5a could be met by a candidate that reaches a class no held family fixes, without harm. These data point at three things outside the operator grammar:
  - a replay that reproduces the production state of context-dependent failures (short agreements);
  - an honest self-account faculty for preference questions;
  - a ReplyQuality criterion that does not credit irrelevant clarifications.
- The last of these is a P6 criterion proposal.
- The human decisions are unchanged:
  - the narrow `operator_authorship` exception;
  - review of the protected-type additions;
  - in addition, whether family harm is counted before or after L0 filtering.
