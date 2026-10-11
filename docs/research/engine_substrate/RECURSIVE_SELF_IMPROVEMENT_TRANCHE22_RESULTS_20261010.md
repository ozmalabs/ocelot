# Recursive self-improvement, tranche 22: results (2026-10-10)

Follows [tranche 21](RECURSIVE_SELF_IMPROVEMENT_TRANCHE21_RESULTS_20261010.md). That tranche found that the agent's self-improvement loop ran in production but could fix nothing. Its commonest natural failure, a turn answered by the error floor, filed no concern, and no variation family could add a reply. This tranche closes both gaps and makes the replay judge use the production path.

## Summary

| Item | Result |
|---|---|
| **Endemic RSI on the production path** ([prereg](SUBSTRATE_ENDEMIC_RSI_PRODUCTION_V1_PREREG_20261010.md)) | **PASS on P1–P4.** 120 unaltered natural persona_chat turns ran through the daemon's own loop (conversation profile, ingest → graph release, graph-scheduled host actions), with no human. The agent filed 5 unanswered-turn classes, promoted 6 concerns itself and ran 6 experiments: 1 supported, 4 abstained (honestly), 1 refuted. It **adopted 1 fix**. On the production retest, errors fell from **60 to 44** (16 turns error → reply, 0 turns worse). The `off` arm adopted nothing (3 turns error → reply, from knowledge learning). |
| What it learned | It generalised its own neutral-receipt disposition from response-position assertions to statements that are not responses. "That would be fun!", "My favorite album is Dark Side of the Moon." and similar turns were answered with the error floor; they are now answered "got it" (17 first-pass turns in the on arm). |
| Supply | New `seeds/unanswered_gap.json`. A recurring (≥2) unanswered turn class, keyed by its evidence signature, files one `SelfConcern{kind:'unanswered'}`. Self-promotion is now eligible for it (`self_promotion` v1.2.0). |
| Fit | New `disposition_generalise` family (`variation_ops` v1.19.0). It makes add-only copies of a held arbitration rule and its reply rule, with exactly one non-identity guard relaxed to the failing turn's evidence. It abstains when no held pair is one guard away. |
| Judge on the production path | `convo_child_run` now replays through `ingest_turn` → tick → release when the parent is a daemon (`delta.parent_turn_path`). Error-floor turns are kept as probes. An unflagged turn whose error floor the variant answers is scored **repaired**, not as a regression. |
| Four more production defects fixed | See §2. |
| Regression | Targeted only (§4): 61 files touching the changed code. 0 attributable failures; 2 test premises updated. |

## 1. Production run (preregistered)

Harness: `evaluation/substrate_capability/endemic_rsi_daemon_v1.py persona shadow 120`. The on arm ran with defaults; the off arm set `SelfPromotionPolicy.enabled = 0`. Reports are in `evaluation/reports/endemic_rsi_daemon_v1_persona_shadow_n120_{t22,off}_20261010.json`.

| Arm | Concerns (unanswered / knowledge / other) | Self-promoted | Experiments | Adoptions | Retest errors, fresh → post-run | Turns error → reply | Turns worse |
|---|---|---|---|---|---|---|---|
| on | 5 / 13 / 2 | 6 | generalise: 1 supported, 4 abstained; reply_ablation: 1 refuted | **1** | **60 → 44** | **16** | **0** |
| off | 5 / 12 / 2 | 0 | 0 | 0 | 66 → 63 | 3 | 0 |

| Gate | Result |
|---|---|
| P1 endemic fix: ≥1 adoption and fewer errors post-run than fresh | pass (1 adoption; 44 < 60) |
| P2 no harm: no turn from reply to error | pass (0) |
| P3 attribution: off arm 0 adoptions | pass (3 error → reply from knowledge learning, reported) |
| P4 integrity: 0 machinery adoptions | pass (both adopted rules are conversation arbitration/reply rules) |

The adoption is `defer_response_assertion_without_proposition_uptake__interaction_relation_none_generalised` plus `reply_to_deferred_response_assertion__interaction_relation_none_generalised`. The replay judged it on the production path: flagged turn fixed, 0 regressions, the other same-class turns repaired.

**Honest caveats.**
- **Fresh-boot baselines differ between arms** (60 vs 66 errors) on the same 120 turns. Fourteen turns differ in both directions, so a fresh boot in a long-lived process is not deterministic. The 16 error → reply transitions are within one arm, comparing that arm's own fresh and post-run retests. The attributable change is the 17 first-pass turns that became "got it" after the adoption; the off arm has none.
- **The fix is modest.** A non-endorsing acknowledgement ("got it") replaces the error floor for self-disclosing statements. It is an honest receipt, not engagement with what was said.
- **4 of 5 unanswered classes abstained.** Interrogatives, and statements misread as action requests, have no held pair one guard away. The other 44 error turns remain.
- **This is one stream, one run per arm.**

## 2. Production defects found and fixed along the way

1. **`close` was never scheduled.** The scheduler's demand rule tested `conclusion_ready > 0`, but the judge rules write `True`, and the native `Gt(True, 0)` is False. So in production no experiment was ever taught or adopted. `cognitive_scheduler` v1.0.2 accepts `== True` (`scripts/gen_scheduler_close_guard.py`). Existing checkpoints keep the old rule body, because the scheduler is install-if-missing.
2. **"Unanswered" was read from an error-candidate message.** A goal-take turn also carries a suppressed error-candidate reply. The daemon now records each completed turn's terminal status as `Message.turn_outcome` (`WorldAdapter.record_turn_outcome`), and the rule reads that.
3. **Two concerns were filed per class in one pass.** Only the oldest unanswered message of a class now files.
4. **The replay scorer counted a repaired unanswered turn as a regression.** This turned a real fix (score +1 −1) into "inconclusive". It is now scored repaired (0).

In addition, the release predicate (`_native_standalone_assertion_receipt_selected`) now also accepts a receipt that the graph selected with `receipt_selected_by_rule`. Without this, no rule-level generalisation could ever be released.

## 3. Recursion

Generalised rules (`*_generalised`) are themselves candidates for the family. A class two guards away from a held pair can be fixed in two adoptions: the first creates a sibling one guard closer. This run produced one adoption, so the chain is possible but **not yet observed**.

## 4. Regression (targeted, per the user's direction not to run the full scope)

Scope: 61 test files that reference the changed code: convo_child_run, experiment dispatch, adoptions, the scheduler, boot profiles, release, variation_ops, self-promotion and ingest. Compared against `pf_t21.failed`.

- **0 attributable failures.**
- `test_arc_goals_migrated::test_ag5…` failed in the parallel run because ARC tests move `seeds/program_synthesis.json` during their own run. It passes when run alone.
- `test_arc_executor_migrated::test_ex1…` fails alone too. It asserts `git show HEAD:results/arc6_verdict_before.json`, and `results/` is untracked, so it is environmental and unrelated.
- `test_verb_self_repair_migrated` has a collection error (`requests` is not installed), as it did in tranche 21.
- **Premises updated:** `test_phase8_corpus_runner` profile seed counts (84/106, +`unanswered_gap`); 41 tests pass.
- **New tests:** `tests/test_unanswered_generalise_migrated.py`, 4 tests passing. They cover one concern per recurring class, the generalised pair answering the class on the production path without changing others, the boolean close guard, and the replay corpus keeping error-floor turns.
- **Envelope:** RSS 186.2 MiB (cap 200), ingress 20.7 ms, all assertions True.

## Next

- **More classes:** the interrogative unanswered classes, for example "What kind of games do you like to play?" (persona questions). These need a family that routes a question kind to an existing faculty (honest self-account, ask-back).
- **Statements misread as action requests** (29 goal-takes), using the comprehension divergence concern: a deep-reader veto with a receipt.
- **A long run to observe chained generalisation** (recursion), and a second stream.
- **A determinism check** of fresh-boot baselines in a long-lived process.
