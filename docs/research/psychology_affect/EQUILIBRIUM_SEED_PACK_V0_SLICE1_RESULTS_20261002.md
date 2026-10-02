# Equilibrium seed pack v0, slice 1 (classifier sidecar) — RESULTS

**Date:** 2026-10-02. Worktree `.worktrees/t3-sidecar`, branch `t3/classifier-sidecar` @ `e2f240fc` plus **uncommitted** files (listed in §5). Registered design: [`EQUILIBRIUM_SEED_PACK_V0_PREREG_20261002.md`](EQUILIBRIUM_SEED_PACK_V0_PREREG_20261002.md) (still a DRAFT, not frozen, and not edited here). Design: [`EQUILIBRIUM_SEED_PACK_V0_DESIGN_20261002.md`](EQUILIBRIUM_SEED_PACK_V0_DESIGN_20261002.md). Because the PREREG is not frozen, nothing below is a confirmatory result. It is a systems smoke slice run on synthetic data only. No corpus was read and `OZMA_NO_LLM=1` was set throughout.

**HEADLINE.**
1. In the one shipped frozen mode (fork per batch), the base was unchanged after 10,000 synthetic messages sent in 100-message batches. `source_revision` and the strong digest were both identical, and no file was written outside the tmp dir (checked with strace). This matches PREREG prediction 1 for that mode.
2. Throughput at concurrency 1 was **1,659 msgs/s** over loopback HTTP and 1,698 msgs/s in-process. That is below the 4,000 msgs/s pool target. Peak RSS was **82.2 MiB**, against a 384 MB target. F1 (frozen-reload) was **not built or measured**, so prediction 2 is **untested**.
3. Prediction 3 (pattern-label quality) is **untested**. No pattern label has rules, and all are `disabled`.

## 1. What was built

* `services/equilibrium_classifier/server.py` is a stdlib `ThreadingHTTPServer`.
  * The host is fixed to `127.0.0.1`, and any other `--host` exits with code 2. The port defaults to 8790; only `--port`/`EQ_SIDECAR_PORT` can change it.
  * It exits with code 2 unless `OZMA_NO_LLM == "1"`.
* Endpoints: `GET /healthz`, `GET /v1/info`, `POST /v1/classify` and `POST /v1/discourse`. The last one returns 501 in v0.
* Wire shapes follow the **Equilibrium worker client** (`equilibrium_worker/classify.py`), not design §4.1, wherever the two differ (see §4).
* Fork per batch works like this:
  * `boot()` and the pack load run once, then `snap = base.snapshot()`.
  * Each request does `branch = snap.fork()`, then `classify(branch, …)`, then drops the branch.
  * After every batch, `snap.source_revision == rev0` is checked. A mismatch returns 503 `base_drift` and the process exits.
  * The strong digest is `sha256(json(graph_to_dict(base), sort_keys))`. It is computed at boot, every 1,000 batches and on every `/healthz`.
* The server decides no labels. It validates the request, forks, calls the adapter, and converts the read-out types.

## 2. Measured (actual runs, synthetic messages, AMD Ryzen 9 5900X, 24 threads)

| Measurement | Result |
|---|---|
| Phase 9 exit: 10,000 msgs in 100 batches | `source_revision` `[915, 62, 25]` before and after. Strong digest `9d2a45f4de5b35c4…` at boot and after replay (re-digested at batch 100 by `/healthz`). Worktree tree-state diff: empty. strace: no write, create, rename or unlink outside tmp (the trace was confirmed live and the parser was negative-controlled). |
| Periodic strong check (in-process, 1,000 single-msg batches) | Ran at batch 1,000, digest equal to boot. |
| Drift injection (fake snapshot whose revision moves) | `BaseDrift` raised, `/healthz` reports false, later batches refused. |
| Throughput, HTTP, c=1, batch 100, 10k msgs (after 1k warm-up) | **1,659 msgs/s**. Wall 6.03 s, batch p50 59.2 ms, p95 75.4 ms. |
| Throughput, in-process, c=1, batch 100 | 1,698 msgs/s |
| Per-100-msg batch breakdown (in-process) | Ingest 36.8 ms, of which `kind_signals` speech-act parsing is 29.5 ms. `run_rules` 18.5 ms. Read-out 0.4 ms. `fork()` 0.113 ms. |
| Peak RSS (server `VmHWM`) | 43.8 MiB after boot, **82.2 MiB** after 11k msgs |
| Boot to first healthy `/healthz` | 0.21 s (server's own boot log: 0.08 s) |

Fix found during the run: the first HTTP measurement was **983 msgs/s**, with p50 at 100.9 ms. The roughly 40 ms per-batch gap was Nagle plus delayed ACK, because headers and body went out as two writes on a keep-alive connection. Setting `disable_nagle_algorithm = True` brought HTTP throughput up to in-process speed. Only the fixed number is reported above as the result.

## 3. Predictions vs. outcomes (PREREG draft)

| PREREG item | Prediction | Outcome |
|---|---|---|
| Headline 1 / M "Base unchanged" | Identical after a 10k replay, no files outside tmpfs | **Confirmed for fork mode only.** F1 and F2 were not shipped. The run used a pytest tmp dir as TMPDIR/cwd, not tmpfs. |
| Headline 2 | F1 < 4,000 msgs/s on one host. Fork faster than F1 per batch. | **Untested.** F1 was not implemented. Fork at c=1 is also below 4,000 (1,659). |
| M throughput at c = 1, 2, 4, N, with median and p95 | Measure all of them | **Only c=1 measured.** Classification is serialised by a process lock, and Python threads would not parallelise the rule pass anyway. Scaling must come from more processes, and that was not measured. |
| M memory | F1 with c ≥ 3 exceeds 384 MB | **Untested** (no F1). Fork c=1 is 82.2 MiB. |
| Headline 3 / Q / F (label quality, fairness strata) | Sealioning and goalpost shifting reach the §Q bar | **Untested.** There was no corpus, no annotators and no pattern rules, and all `pat.*` labels are `disabled`. |
| D (length-matched synthetic messages) | Lengths drawn from the train distribution | **Deviation.** The messages are template-generated with no length matching, because no corpus access was allowed. |

## 4. Decisions and contract deviations

* **The client contract wins over design §4.1.**
  * Requests are `{"messages":[{"id","text","reply_to"}]}`, with optional `taxonomy_version`. A mismatched `taxonomy_version` returns 409.
  * Responses are `{"ok","provenance","labels":[{"id","speech_act"?,"substantive_markers","deescalation","rule_ids"}]}`.
  * `author_ref`, `ts`, `reactions`, `context`, `traces` and `trace_ref` are not accepted or emitted, so validation is closed.
* **Rule ids on the wire** are `<rule name>:<pack version>`, for example `eq.msg.speech_act.sak_question:0.1.0`. The client's code pattern rejects `@`, so `:` replaces it.
* **`deescalation`** is a shadow boolean in the pack. On the wire it becomes `1.0` if a cue rule fired and `0.0` otherwise, because the client wants a float and rejects bools. That `0.0` means "no v0 cue fired". It does not mean "measured not deescalating".
* **`speech_act`** is emitted only when exactly one speech-act value fired. Otherwise the field is omitted rather than chosen in Python. The current rules are mutually exclusive on `sak_kind`, so the omission only occurs when no rule fires.
* **`/v1/info`** reports `seed_pack_sha256`, plus `seed_pack_digest` with the same value under the key the client reads.
  * The digest is sha256 over the sorted `seeds/equilibrium_*.json` files, each contributing `name NUL bytes NUL`.
  * It also reports `mode: "fork_per_batch"`, as the brief specifies (the design said `"frozen-fork"`), and `no_llm: true`.
  * `ocelot_tree_dirty` is `true` today, so `ocelot_commit` does not by itself identify the pack. The pack sha does.
* **Errors** use `{"ok":false,"error":{code,message,retryable}}`. Messages carry field paths only. A canary string sent through every error path never appears in any response.
* **Body handling:** the body cap is 1 MiB. A missing, invalid or oversize Content-Length, or a chunked body, returns 413 and closes the connection.
* **Nothing is logged** from requests (`log_message` is a no-op), and nothing is persisted.

## 5. Cross-check against the real Equilibrium client

`equilibrium_worker.classify.OcelotClassifier` (run with `uv run --frozen` from `/home/matt/ozmadev/equilibrium`, read-only) was pointed at `http://127.0.0.1:8790`:
* `healthy()` returned True, `describe()` succeeded, and `ClassifierGate(expected_taxonomy="eq-tax-0.1.0").refresh()` returned True, with `classifier_version=eq-tax-0.1.0+e2f240fcd737`.
* 3 synthetic messages were classified and parsed by the client without `invalid_reply`.
* The Equilibrium repo's `git status --porcelain` hash was unchanged afterwards.

## 6. Nulls and limits

* `reply_to` is validated but unused, because v0 has no discourse-relation rules.
* `domains`, `valence`, `hostility` and `person_targeting` are never emitted.
* Directive detection is weak. The `wikt_pos_en` lexicon is missing in this worktree (carried over from slice 1, open there).
* `tests/test_speech_act_parity_migrated.py` has 3 failures. The previous stage showed they fail identically with the equilibrium seeds removed, so they are not caused by this slice. I did not re-verify that in this stage.
* `services/p5_r0_evaluator/tests/test_service.py` fails at collection on this branch with `ModuleNotFoundError: services.p5_r0_evaluator.input_builder`. That is unrelated, and it was not run.
* There is no tick-budget detection yet: `run_rules(10_000)` exhausting its budget is not surfaced as 504 `tick_budget`.
* There is no concurrency semaphore or 429.
* There is no auth. That is acceptable only because the bind is loopback-only (design OQ-6).

## 7. Files (all uncommitted, this slice)

* `services/equilibrium_classifier/__init__.py`, `services/equilibrium_classifier/server.py`
* `tests/test_equilibrium_classifier_service.py` (37 tests)
* This document.

Run: `OZMA_NO_LLM=1 python3 services/equilibrium_classifier/server.py`. Tests: `OZMA_NO_LLM=1 python3 -m pytest tests/test_equilibrium_classifier_service.py -q -s -p no:cacheprovider`.
