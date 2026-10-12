# Recursive self-improvement, tranche 24: results (2026-10-10)

Follows [tranche 23](RECURSIVE_SELF_IMPROVEMENT_TRANCHE23_RESULTS_20261010.md). Until now, each adoption was an independent fix. This tranche shows the first **chained** self-improvement on the production path. One of the agent's own adoptions made a previously unfixable class fixable. The agent noticed that its repertoire had changed, reopened the concern it had given up on, and fixed it by generalising from the rule it had itself adopted.

## Summary

| Item | Result |
|---|---|
| **Chained endemic RSI** ([prereg](SUBSTRATE_ENDEMIC_RSI_CHAINED_V1_PREREG_20261010.md)) | **PASS on C1–C5.** On 120 natural turns with no human, the agent reopened concern 24965 after an adoption. It then adopted `…__interaction_relation_none_generalised__language_statement_act_none_generalised`, a generalisation of its own earlier generalisation. Post-run errors were **25** against **44** in the identical arm without reopening. |
| Overall (on arm) | Errors fell **66 → 25** and spurious goal-takes fell **29 → 7** against the fresh boot. 0 turns got worse, and all 6 control imperatives were unchanged. There were 3 adoptions: the reader correction, the generalisation, and the generalisation of that generalisation. |
| What made it possible | Four graph changes (§2) give the agent a "decision opening" rule for its own improver. A verdict of "abstained" stands until the agent's repertoire changes, and then the agent asks again. |
| Two defects fixed along the way | The reopen fired twice in one epoch, and the newest two builders read a re-promoted concern's retired StandingConcern (§3). |
| Regression | Targeted (85 files); 0 attributable failures. |

## 1. Production run (preregistered)

Harness: `endemic_rsi_daemon_v1.py persona shadow 120`, `ERSI_LABEL=t24`. Reports are in `evaluation/reports/endemic_rsi_daemon_v1_persona_shadow_n120{,_noreopen,_off}_t24_20261010.json`.

| Arm | Adoptions | Reopened | Error/none, fresh → post-run | Goal-takes, fresh → post-run | Turns → error | Controls kept |
|---|---|---|---|---|---|---|
| on | **3** (1 chained) | 1 | **66 → 25** | 29 → 7 | 0 | 6/6 |
| noreopen (`max_reopens` = 0) | 2 | 0 | 66 → 44 | 29 → 7 | 0 | 6/6 |
| off (no self-promotion) | 0 | 0 | 66 → 63 | 29 → 29 | 0 | 6/6 |

| Gate | Result |
|---|---|
| C1 chain: a reopened concern fixed by generalising an earlier adoption's rule | pass (concern 24965; source `defer_response_assertion_without_proposition_uptake__interaction_relation_none_generalised`) |
| C2 gain over no-chain | pass (25 < 44) |
| C3 no harm | pass (0 → error; 6/6 controls) |
| C4 attribution | pass (off: 0 adoptions; noreopen: 0 reopens) |
| C5 integrity | pass (all adopted rules are conversation arbitration/reply rules; the adoption branch's protected-type gate applies) |

**The chain, step by step** (on arm):
1. The agent files an unanswered class (statements, no relation, act `assertion`). It generalises the held response-assertion receipt pair by relaxing `interaction_relation`, and adopts it (experiment #25219).
2. A second class (the same, but with no `language_statement_act`, 19 turns) was filed earlier. Its first trial abstained, because no held pair was one guard away.
3. After step 1's adoption, `irr_reopen_on_new_capability` marks that concern for retry. The scheduler requests `concern`, and the executor re-promotes it.
4. `disposition_generalise` now finds the rule adopted in step 1 one guard away (`language_statement_act`). The production replay supports the trial, and the agent adopts it (#25336).

The `noreopen` arm reproduces steps 1 and 2 exactly, but never step 3. Its post-run errors are 44, matching tranche 23. The 19-turn difference between the arms is exactly that class. Examples: "I like to watch movies and TV shows.", "Me too.", "I agree. I like to keep myself busy.", "I loved Frozen 2! I saw it twice in theaters."

**Caveats.**
- The chained fix is the same kind as tranche 22's, a neutral receipt ("got it") in place of the error floor. It is an honest acknowledgement, not engagement with the content.
- **Chain depth is 2.** A deeper chain would need another class that sits one guard from the second-order rule.
- One stream, one run per arm.
- **25 errors remain.** 16 are interrogative in form, for example "What's your favorite book?", "What do you do for work?" and "I know, right?"; no held pair is near them. 7 are short agreements ("Yeah, it's the best.", "Yes, I do."). 2 are statements whose evidence force is `repair_or_defer`.

## 2. Changes (`scripts/gen_reopen_on_new_capability.py`)

1. **`self_optimisation` v1.6.0:** `close_abstained_variant` stamps `SeedDelta.abstain_epoch`, the count of Adoptions at abstention (the agent's repertoire epoch).
2. **`variation_ops` v1.21.0:** an abstention excludes its family for that concern only at its own epoch. An unstamped abstention still excludes, so old graphs behave as before.
3. **`instruction_repair_retry` v1.4.0:** `irr_reopen_on_new_capability` marks `retry_requested` on a promoted concern of a kind listed in `reopen_kinds` (default `unanswered`, `comprehension`) when all of these hold:
   - every one of its experiments abstained;
   - every abstention is at an older epoch;
   - it is not already reopened at this epoch;
   - `reopen_count` < `max_reopens` (2).

   This is paper 02c's decision-opening grammar applied to the improver itself. The standing verdict is retained until a represented change in the conditions that produced it.
4. **`cognitive_scheduler` v1.0.3:** `supervise_requested_retry` (+ `_rearm`) requests the `concern` host action while a SelfConcern carries `retry_requested`, with at most one concern request in flight. Before this, an agent retry executed in production only if another concern happened to be pending. Tranche 6's instruction retries had the same gap.

## 3. Defects found in the smoke runs

- **The reopen fired twice in one epoch.** After the first reopen, the retired StandingConcern's abstained delta was still stamped at the old epoch, and the new trial abstained before it was recorded. The rule now records `reopened_at_epoch` and fires at most once per epoch.
- **The re-promoted concern's builder read a retired StandingConcern.** `_compose_disposition_generalise` and `_compose_deep_reader_correct` took the first StandingConcern with the concern's name, which after a re-promotion is the retired one without a `promoted_to` edge. They abstained with "names no turn". Both now use `_live_standing_for_key`, the same rule the older builders already applied (tranche 5).

## 4. Regression (targeted)

Scope: 85 files. These are tranche 23's 63 files plus tests referencing the retry policy, the scheduler, `variation_pick` or abstention, and the new tests.
- **0 attributable failures** against the tranche-22/23 baselines.
- Three groups not in the earlier baseline lists were checked:
  - `test_code_writing_migrated` (14) fails identically on a clean worktree of HEAD;
  - `test_code_growth_migrated` (6) is in the tranche-21 baseline;
  - `test_cut_mint_policy_migrated` (3) fails with `fatal: bad revision '17cb3f3d'`, because its pinned commits are absent from this clone.
- **New:** `tests/test_reopen_on_new_capability_migrated.py`, 4 tests. They cover:
  - no reopen while the repertoire is unchanged, a reopen once an Adoption exists, and at most one reopen per epoch;
  - a judged concern is never reopened;
  - the scheduler requests `concern` for a marked retry;
  - the seed contents;
  - the live-StandingConcern lookup.
- **Envelope:** RSS 186.5 MiB (cap 200), ingress 27.4 ms, all assertions True.

## Next

- Interrogatives (16 of the 25 remaining errors). These need a family that routes a question kind to an existing faculty, such as an honest self-account or an ask-back. A receipt is the wrong answer to a question.
- Short agreements (7).
- A longer or second stream, to see whether chains deeper than 2 occur naturally.
