# Recursive self-improvement, tranche 6: results (2026-10-08)

Follows the [tranche 5 results](RECURSIVE_SELF_IMPROVEMENT_TRANCHE5_RESULTS_20261007.md).

## Summary

| Item | Result |
|---|---|
| Agent-initiated retry | **Done.** A graph rule requests the retry and the daemon hook carries it out, bounded by a policy node. The real-judge panel now runs with **no human retry**. |
| Route override for verbs already routed but unhandled | **Done.** A filed instruction gap now counts as evidence that the held route fails. `summarise` is repaired. When the override would break another use of the verb, the judge declines it. |
| Real-judge panel, agent-initiated (7 cases) | **6/7 genuinely repaired, 0 false adoptions.** The one non-repair is correct behaviour: every available route would break "Summarise yourself.", so after 3 attempts the agent stopped and kept its working reply. |
| Two measurement flaws found and fixed | (1) The judge credited a reply that changed only because of replay state. (2) The repeated-gap reply was read back as `handled`. |
| Non-cue families on reported concerns (real judge) | **Feasibility.** `knob_edit` builds and dispatches a real variant, judged inconclusive (no observable change). `shape_mint` authors an empty delta. `datum_feedback` authors no experiment. A "hardcoded floor" report goes to comprehend-first. |

## 1. Agent-initiated retry

New seed `seeds/instruction_repair_retry.json`, loaded in full-corpus boots, with policy node `InstructionRetryPolicy{enabled:1, max_retries:2}`.

The rule `irr_request_retry` marks a promoted instruction SelfConcern `retry_requested=1` and increments `retry_count` when all of these hold:
- its own experiments have produced more refuted or inconclusive verdicts than retries already requested;
- none is supported;
- none is still pending;
- `retry_count` is below the bound.

`jabberwock_daemon._execute_requested_retries` runs at the top of `_concern_tick`. For each marked concern it does the existing teardown and re-promote, then clears the mark. A human repromote clears any pending graph request.

The retry asks the same held route pick, which excludes routes already refuted or inconclusive. So each retry tries a new route, and when none remain the builder abstains and the loop stops.

Test: `test_agent_requests_its_own_retry_and_stops_at_the_bound` (refuted → retry 1; inconclusive → retry 2; refuted → no further retry).

## 2. Route override

`seeds/variation_ops.json` v1.10.0. `cue_route_pick` used to abstain whenever the verb already had a route. It now abstains only if the verb is routed **and** no instruction gap has been filed for it. The candidate pool already excludes the verb's own Concept, so an override always proposes a different pooled route. The replay experiment then validates it like any other cue edit.

Measured:
- `summarise` was routed to `self_report`, yet "Summarise the data." was unhandled. Adding a `world_action` route handles it.
- The same change turns "Summarise yourself." into a no-world action reply. The judge only catches that if the corpus contains such a turn, so the panel includes a guarded case.

## 3. Real-judge panel, agent-initiated

[Report](../../../evaluation/reports/real_judge_repair_panel_v1_3_agent_retry_20261008.json). Setup: one fresh full-seed agent per case; the human promotes once; up to 4 attempts; every retry requested by the agent's own rule. Seed files were confirmed untouched (`OZMA_SEED_PERSIST_DISABLED`).

| case | attempts (route → verdict, agent requested a retry?) | outcome |
|---|---|---|
| condense | comprehend_text → refuted (yes); world_action → supported | repaired |
| summarise | world_action → supported (override) | repaired |
| summarise + guard turn "Summarise yourself." | world_action → inconclusive (yes); no route → inconclusive (yes); no route → inconclusive (bound reached) | not repaired; guard reply preserved |
| tabulate | world_action → supported | repaired |
| shorten | comprehend_text → refuted (yes); world_action → supported | repaired |
| alphabetise | world_action → supported | repaired |
| paraphrase | world_action → supported | repaired |

The guarded case is the system working as intended. The only pooled route that fixes the flagged turn regresses an unflagged one. The verdict is inconclusive, nothing is adopted, retries exhaust within the bound, and "Summarise yourself." is unchanged. A route keyed on the verb alone cannot express "summarise the data → world_action, summarise yourself → self_report". That needs a content-conditioned route, which no current family offers.

### Measurement flaws found in this tranche

The first run ([v1.2](../../../evaluation/reports/real_judge_repair_panel_v1_2_agent_retry_20261008.json)) reported 7/7. That was wrong, because of two flaws that combined:

1. **Flagged-turn baseline.** A flagged turn was "fixed" when the variant differed from the recorded reply. On retry the recorded reply was the first-time "filed it as a gap"; replay state made both control and variant say "already filed". A no-op delta, where the builder abstained, therefore scored supported. Fix in `scripts/convo_child_run.py`: a fix must also differ from the paired control replay.
2. **Outcome readback.** The repeated-gap reply (tranche 5's `reply_known_instruction_gap`) sets `comprehended`, and `_record_instruction_outcome` read that as `handled`. Fix in `substrate/world_adapter.py`: a turn claimed only by a gap rule (`instruction_gap_noted`) is unhandled. The panel's success criterion also now excludes gap replies.

Only the guarded case changed between v1.2 and v1.3 (7 → 6). Rechecking the v1.1 panel against the stricter criterion leaves its 5/6 unchanged.

## 4. Non-cue families on reported concerns

[Report](../../../evaluation/reports/reported_family_probe_v1_20261008.json). This ran before the flagged-baseline fix, but no supported verdicts appear in it.

| reported text | pipeline | family | variant | real verdict |
|---|---|---|---|---|
| reform the topic too eagerly, threshold too low | experiment | knob_edit | built (set_node_attrs on a held knob) | inconclusive |
| persona treated the same, profile shape | experiment | shape_mint | **empty delta** (builder built nothing) | inconclusive |
| trust that speaker too much, recalibrate | experiment | — | no experiment authored | — |
| reply to greetings is a hardcoded floor | comprehend_first | — | — | — |

The non-cue families are not yet real-judge-ready:
- **`knob_edit`:** works mechanically, but the corpus has no turn whose reply depends on the knob.
- **`shape_mint`:** needs party features the probe corpus doesn't create.
- **`datum_feedback`:** never authors an experiment.

A multi-family credit gate on real verdicts is therefore still blocked. It needs these builders to produce effective variants, and corpora containing the turns they affect.

## Regression

Same 136-file scope. 66 failures, identical to the end of tranche 5: no new failures, no changes. `test_residual_promote_migrated.py` timed out, as in every run.

## Next

1. **Content-conditioned routes:** a cue edit keyed on verb + object class, so a verb's two uses can route differently. The guarded summarise case is the test.
2. **Make the non-cue builders effective,** with corpora containing the turns they affect: `knob_edit` with a reform-sensitive turn, `shape_mint` with party features, and `datum_feedback` authoring at all.
3. **Run the multi-family credit gate on real verdicts** once at least two families can be supported for the same concern kind.
