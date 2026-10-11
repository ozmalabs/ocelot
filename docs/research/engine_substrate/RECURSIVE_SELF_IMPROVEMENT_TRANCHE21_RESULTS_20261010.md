# Recursive self-improvement, tranche 21: results (2026-10-10)

Follows [tranche 20](RECURSIVE_SELF_IMPROVEMENT_TRANCHE20_RESULTS_20261010.md). That tranche showed endemic RSI in a harness. This tranche asks whether it happens on the path production actually runs: the daemon boots the `conversation` seed profile, turns arrive through `ingest_turn` and graph release, and host work runs only when the graph's scheduler requests it.

## Summary

| Item | Result |
|---|---|
| **Correction to tranche 20** | **Its gains do not reach production.** The tranche-20 harness and the replay judge call `converse(text, speech_act=…)`. Production does not. On the production path the 51 natural requests are already answered: 49 by honest goal-taking ("I took on the goal to bake the cake, but I have no attached world/faculty…"), with **0 gaps filed**. The `converse()` path files a gap for the same turns, and tranche 20 fixed exactly that divergence. |
| The production profile lacked the loop | The daemon's `conversation` profile (74 seeds) had none of `self_promotion`, `variation_ops`, `self_optimisation`, `instruction_repair_retry`, `adoption_safety`, `improvement_integrity`, `conversation_experiment` or `comprehension_health`. They are **now anchors** (82 seeds). RSS is 184.2 MiB and ingress 19 ms; the envelope still passes. |
| Composer misroute | **Found and fixed.** A self-filed `comprehension` concern ("comprehension classified this as 'instruction' but the deep reader heard 'statement'…") grounds `comprehend` (priority 1) from its own content. It went to the comprehension composer, which minted an inert rule and authored no experiment. `composer_dispatch` v1.2.0 now gives the `replay` head priority 0.5, so a concern already routed to the experiment pipeline is not re-routed. |
| Dispatch ingest stall | **Found and fixed.** The scheduler requests `dispatch` only for a `requested` Experiment. Once the child runs, nothing requests its ingestion, so the loop stalled for good. `_dispatch_tick` now keeps its request alive (deferred) while a child is running. |
| **Production endemic RSI, measured** | **Not yet.** 120 natural persona_chat turns went through the production loop with shadow read on. Of the replies, 66 were error or none, 29 were spurious goal-takes ("I took on the goal to lot the fun") and 25 other. The agent filed 16 concerns (14 knowledge, 1 comprehension, 1 performance), self-promoted 1 and ran 1 experiment (reply_ablation, **refuted**), with 0 adoptions. |

## 1. The correction, in detail

There are two production-relevant turn paths in `substrate/world_adapter.py`:
- **`converse()`.** Used by tests, the tranche-20 harness, and every replay inside `scripts/convo_child_run.py`. The native `note_unhandled_instruction_gap` floor files a gap for an unsupported imperative.
- **`ingest_turn` → tick → `release_graph_selected_response`.** Used by the daemon (HTTP and socket). Native arbitration selects `act`, and `release_graph_selected_action_faculty_reply` runs `conversation_action.act_on_instruction`, which mints a Goal and replies honestly.

Measured (`evaluation/substrate_capability/endemic_rsi_daemon_v1.py requests shadow`, `evaluation/reports/endemic_rsi_daemon_v1_requests_shadow_n51_20261010.json`):

| Path | Gap filed | Goal-take | Other |
|---|---|---|---|
| `converse(…, "request")` (tranche 20, fresh boot) | 47 | 0 | 4 |
| production (daemon loop, conversation profile) | **0** | **49** | 2 |

Consequences:
- **Tranche 20 measured a real self-improvement loop on a real path,** but not the path the daemon runs. Its claims stand for that path. The "45/47 fixed" did not change what a daemon user sees.
- **The replay judge (`convo_child_run`) judges experiments with `converse()`.** It therefore validates behaviour on the non-production path. A variant that helps production but not `converse()`, or the reverse, is mis-judged.

## 2. What production natural conversation actually exposes

`endemic_rsi_daemon_v1.py persona shadow 120` reproduces, in process, the daemon's own tick-loop body and graph-requested host-action executor. It makes no direct hook calls. Results are in `evaluation/reports/endemic_rsi_daemon_v1_persona_shadow_n120_20261010.json`.

| | Count |
|---|---|
| Turns | 120 (User 1, persona_chat_20) |
| Reply was the error floor, or there was none | **66** |
| Spurious goal-take (a statement read as an action request) | **29** |
| Other (social reply, wiki answer, clarification) | 25 |
| SelfConcerns filed | 16: 14 knowledge, 1 comprehension (recurring shallow/deep divergence), 1 performance |
| Self-promoted | 1 (the comprehension concern) |
| Host actions the scheduler requested | steer 1, concern 1, dispatch 1, search 20, detail 7, teacher 5 |
| Experiments | 1: `reply_ablation`, refuted |
| Adoptions | 0 |
| Turns that changed between a fresh boot and the post-run agent (production retest) | 3 (from knowledge learning, not adoption) |

The loop now runs end to end in production: self-filed → self-promoted → composed → dispatched → ingested → judged. But it has nothing it can fix:
- **Supply.** Natural conversation yields 1 experiment-eligible concern in 120 turns. The 66 error turns and 29 spurious goal-takes, the agent's real failures, file no concern at all.
- **Fit.** No variation family can produce a reply where there is none. They can route a verb, move a knob, shift a literal or ablate a rule. The one family that applied (reply ablation) was correctly refuted.

## 3. Changes

- `substrate/boot_profiles.py`: `CONVERSATION_SELF_IMPROVEMENT_ANCHORS` are added to the conversation profile. These are the seven loop seeds plus `comprehension_health`.
- `seeds/composer_dispatch.json` v1.2.0 (`scripts/gen_composer_replay_priority.py`): `replay` → experiment at priority 0.5.
- `scripts/jabberwock_daemon.py`: `_dispatch_tick` defers its host action while a child is running.
- `evaluation/substrate_capability/endemic_rsi_daemon_v1.py`: the production-path measurement harness.
- `tests/test_production_self_improvement_migrated.py` (3 tests, passing): profile contents, composer pick, dispatch deferral.

## 4. Regression

Scope: the tranche-20 scope plus every test that touches the boot profiles, the dispatch tick or `composer_dispatch` (347 files), compared against `pf_t20.failed`.

- **Fixed (1, by the composer fix):** `test_ground_concern_six_kinds_migrated::test_instruction_performance_comprehension_never_reach_the_generic_fallback[comprehension-…]`. It is a long-standing failure: a comprehension concern reached the generic composer fallback. The 3 steering tests the tranche-20 commit had already fixed also show as fixed against the uncommitted `pf_t20` baseline.
- **Test premise (1):** `test_phase8_corpus_runner::test_trace_dimensions_are_declared_for_the_full_corpus_observation_contract` pinned the conversation profile's seed counts. The new anchors take initial from 74 to 83 and loaded from 96 to 105; incremental is unchanged at 22. Updated; the file's 41 tests pass.
- **Not new (6):** the `test_code_curriculum_migrated` failures fail identically in tranches 16–19, including with this tranche's sources reverted. Tranche 20's run of that file hit the 1800 s timeout before pytest printed its summary, so its `FAILED` lines were missing from `pf_t20.failed`. They are not caused by this tranche.
- **Flaky (1):** `test_nobel_leak_gone_and_incoherence_caught`, pre-existing since tranche 11.
- The same 6 timeouts as before. The divergence fixture was restored.
- **Envelope:** peak 184.2 MiB (cap 200), ingress 19 ms, all assertions True.

## Next (in order)

1. **Judge on the production path.** `convo_child_run` should replay probes through `ingest_turn` → tick → release, so the improver validates exactly what production does. Without this, a self-improvement can be real in replay and invisible in production.
2. **File concerns from the agent's own failures.** An explicit-error terminal outcome, or a spurious goal-take that shadow read disagrees with, should become an experiment-eligible concern. The graph already records `terminal_outcome=explicit_error`.
3. **A family that can add a reply,** for example routing an unanswered turn kind to an existing faculty, the reply-side twin of `cue_set_edit`. Then rerun the preregistered endemic gates on the production path.
