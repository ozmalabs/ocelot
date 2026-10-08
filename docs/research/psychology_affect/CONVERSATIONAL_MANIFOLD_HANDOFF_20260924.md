# Conversational Manifold Cognition Upgrade — Handoff

Date: 2026-09-24  
Workspace: `/home/matt/ozmadev/ocelot`

## Resume prompt

Continue the conversational manifold cognition upgrade from this handoff. Work
phase-by-phase from the canonical execution plan and use the repository `.venv`
for verification. Preserve the cognition-first, language-agnostic,
non-inherently-turn-based architecture. Do not solve cognition failures with
surface conversation wording. Python remains a mechanical world/semantic
boundary; graph/native rules remain authoritative for cognition and outcomes.

First inspect this file, the execution plan, both progress trackers, `git
status`, and the last commit. Verify the unverified changes listed below before
doing further work. Commit bounded work regularly with detailed messages.

## Current verified state

- Last completed commit before this handoff:
  `10e2220c test: reconcile conversational cognition evidence`.
- Earlier correction commit:
  `47114424 fix: reject unverified kind fast path`.
- The rejected `run_rules_prefix` native optimization is removed from source
  and the installed native extension was rebuilt from restored source.
- Native authority audit: **183 bound / 0 unbound / 183 total**, clean.
- Indexed referent equivalence/compatibility battery: **10 passed** in the local
  `.venv` (`tests/test_concept_indexed_referent_ingress.py`,
  `tests/test_canonical_discourse_referent_seam.py`,
  `tests/test_conversational_intent_arbitration.py`, and
  `tests/test_conversation_intent_arbitration_measurement.py`).
- Conversation loop, aliasing, and output-null gates: **20 passed**.
- Speech parity remains at the known baseline: **7 passed, 3 pre-existing
  failures** (fixture/seed drift around instruction content, `Focus on...`, and
  the additional speech-act seed rule); the rejected optimization did not add
  those failures.
- Phase 8H raw-reference audit is incomplete by design: ELIZA floor, small LLM,
  and modern LLM are case-complete; base-human and advanced-human references
  are missing. Comparative release remains blocked.
- Production envelope remains over the nominal resource budget: cold RSS and
  latency are substrate/runtime allocation issues, not conversation-surface
  issues. The dominant measured first-event cost is the native kind-rule
  selective readback/serialization boundary and cold substrate allocation.
- `noted` is forbidden as a conversational fallback. The canonical failure
  surface is exactly:
  `ERROR: no communicative response could be generated.`

## Verification completed after handoff

The user requested an immediate stop after the following patch was applied but
before tests were rerun:

- `domains/conversation_action.py`: `satisfiable_reply()` now returns the
  graph-minted goal in its result for rule/self-organisation answers.
- `substrate/world_adapter.py`: the existing conversation-action bridge now
  invokes the existing `satisfiable_reply()` and `honest_no_world_reply()`
  faculties for their already-selected comprehension dispatch paths, and the
  release bridge accepts those existing routes.
- `tests/test_comprehension_robustness.py`: the stale statement assertion was
  changed from `noted` to the mandated explicit diagnostic error.

These changes repaired two cognition-routing regressions:
`Name one of your rules.` and `Describe what you perceive.` were reaching
existing faculties but falling through to the generic error because the live
bridge only invoked action handling for `instruction` kinds. They must be
committed separately when requested; this handoff does not claim a commit.

- `.venv/bin/pytest -q tests/test_comprehension_robustness.py`: **9 passed**.
- Focused conversation/production slice (`test_conversation_loop.py`,
  `test_utterance_conversation_unification.py`, `test_output_null_gate.py`,
  `test_phase6a_production_gate.py`): **33 passed**.
- The originally named `tests/test_phase6_production_gate.py` does not exist in
  this checkout and was omitted; no tests were run for that path.
- `git diff --check` passed for the relevant project/status paths.

The next cognition work is not part of this bounded routing increment. The
Phase 1 speech-act parity discrepancy, Phase 7 resource envelope, substantive
Phase 6 gaps, and Phase 8H human-reference gate remain open.

## Immediate next actions

1. (Completed) Run:

   ```bash
   source .venv/bin/activate
   pytest -q tests/test_comprehension_robustness.py
   ```

2. (Completed) Run the focused regression slice covering conversation gates and the changed
   production boundary:

   ```bash
   pytest -q \
     tests/test_conversation_loop.py \
     tests/test_utterance_conversation_unification.py \
     tests/test_output_null_gate.py \
     tests/test_phase6_production_gate.py \
     tests/test_phase6a_production_gate.py
   ```

3. (Completed) Focused checks are green and `git diff --check` passed. The
   routing patch remains uncommitted; do not include unrelated worktree edits.

4. (Completed) Reconcile the progress tracker after verification. The tracker must retain
   the distinction between completed authority/equivalence gates and open
   resource/comparative-human gates.

5. Continue with the next documented cognition/resource increment. Do not mark
   the overall objective complete while the resource envelope, substantive
   Phase 6 cognition gaps, and human comparative references remain open.

## Resume checkpoint — 2026-09-27

The “P, not Q” contrastive correction increment is implemented in
`domains/comprehend_text.py`. The adapter retains an English-adapter typed
`not` operator in language evidence and marks a comma-delimited negative
alternative as correction; ordinary negation remains a negative control.
`tests/test_language_neutral_evidence_arbitration.py` passes **6/6**. Fresh
full-seed artifact:
[`contrastive-correction replay`](../../../evaluation/reports/phase8_corpus_report_20260927_contrastive_correction_v1.json).
It improves native authority **65→66/74** and substantive receipt-backed
replies **49→50**: `correction_world` now selects native `defer` and releases
a graph-backed correction acknowledgment. Eight events still lack native
disposition authority; grounding remains 21/50 TP, Phase 4 remains 0/0/0, and
comparative release is blocked at provenance. Replay latency is
92.97/167.54/193.14 ms median/p95/max (10 events exceed 150 ms); do not
attribute its run-to-run change to this localized parser correction.

Before more cognition edits, review the execution plan, cognition tracker, and
progress tracker. Preserve unrelated dirty worktree state. The overall goal
remains active and unaccepted.

## Latest bounded work at stop — 2026-09-25

Daemon host-action retrieval has now been extended from generic `SearchRequest`
to specific `GroundRequest` fulfillment. Remote grounding/detail retrieval is
staged on the bounded worker pool using immutable request values; graph writes,
candidate selection, receipts, and request completion remain on the daemon
owner thread. A successful specific grounding supersedes duplicate generic
search work; a miss/error leaves the generic fallback available. Interrupted
work is requeued on restart. Focused async success/fallback, composition
precedence, restart recovery, graph-lock availability, and pending-to-commit
controls are recorded in the cognition tracker; the relevant suites passed,
and `py_compile`/`git diff --check` passed.

The seed-generated integration exposed and fixed a liveness mismatch: the
native supervisor minted one generic SearchRequest host action while a
same-query specific GroundRequest remained requested. The daemon had deferred
the generic action awaiting a separate specific-source action that never came.
The selected generic action now stages the specific request first. FIFO
owner-thread commit order also prevents completion timing from changing shared
discourse focus. Async success/fallback/restart/owner-commit and seed-generated
completion tests pass; the broad grounding/supervisor suite was **34 passed,
1 skipped**, and the current targeted lifecycle/profile battery passes **8/8**.

Two fresh external-retrieval 74-event daemon profiles (35 topic-grounding HTTP
requests each) have identical canonical chat-observation SHA256
`75cd5d4e365b48250ee270559967e1a531c29991f97484de4952adf3a3dc119d`. They
record 32 host actions drained, 37/74 replies, 37 pending turns, 10/74
authoritative dispositions, zero runtime errors, 3.160 s maximum completed
turn latency, and 111,398,912-byte peak RSS. Follow-up detail receipt outcomes
differed across the two external runs (one vs. three failures), so the matching
chat projection does not establish identical host histories. Host work drains,
but reply and cognition coverage and the 100 MiB memory gate fail. The next cognition seam
is graph-native event terminality versus reply expectation, followed by
graph-authorized text realization. The direct `WorldAdapter.converse()` path
remains synchronous; the prior direct-path sample is also over budget
(109,096,960-byte peak RSS; 5,261-ms worst event). Comparative-human/provenance
and broader cognition, production, and resource gates remain open; do not
claim overall completion.

## Files and constraints

- Canonical plan:
  `docs/research/psychology_affect/CONVERSATIONAL_MANIFOLD_EXECUTION_PLAN.md`
- Main cognition tracker:
  `docs/research/psychology_affect/CONVERSATIONAL_MANIFOLD_COGNITION_UPGRADE_TRACKER.md`
- Progress tracker:
  `docs/research/psychology_affect/CONVERSATIONAL_MANIFOLD_PROGRESS_TRACKER.md`
- Use `/home/matt/ozmadev/ocelot/.venv/bin/python` and
  `/home/matt/ozmadev/ocelot/.venv/bin/pytest` explicitly when needed.
- Rust rebuilds, if required, run from `runners/dsl` after sourcing the
  absolute root `.venv`; do not accept a parity-breaking optimization.
- There are many unrelated untracked P5, attestation, semantic-review, and
deployment artifacts. Do not stage secrets, credentials, or unrelated work.

## Current continuation status — 2026-09-28

The latest full Phase 8 replay is
`evaluation/reports/phase8_corpus_report_20260928_learning_context_clarification_resume_v2.json`.
Native disposition authority is **74/74**, with **53** released replies, **8**
explicit errors, and **13** authorized silences. Grounding is **21 TP / 29 FN /
0 FP (F1 0.592)**; Phase 4 promotion remains **0**. The turn-compatible
unanswered-learning clarification is now released without answer commitment.
`learn_uncertain` remains an explicit declarative learning case with no safe
released response. Two deterministic connected-profile resource reports are
available, but both exceed the absolute RSS bound at **107,012,096 / 107,053,056
bytes**; full-boot memory, production p95/max latency, fixture agreement,
Phase 4 promotion, and comparative evaluation remain open. Continue from the
latest entries in `CONVERSATIONAL_MANIFOLD_EXECUTION_PLAN.md` and
`CONVERSATIONAL_MANIFOLD_PROGRESS_TRACKER.md`; do not claim overall completion.

The blinded v5 packet has since been refreshed to the latest target replay:
`evaluation/reports/phase8_blinded_output_packet_20260928_learning_context_clarification_v1.json`.
The current target matches it **74/74**. The refreshed raw audit has complete
ELIZA/small-LLM/modern-LLM raw classes, but both human classes remain missing;
no score interpretation has occurred. Packet, rater forms, and audit are
linked in `CONVERSATIONAL_MANIFOLD_PHASE8A_COMPARATIVE_EVALUATION.md`.

Latest follow-up: native `blocked` for missing world support now yields a
production-gated context inquiry when the event has a compatible response
slot; current Phase 8 is **54 released / 7 errors / 13 authorized silences**.
The exact-tree connected profile is deterministic but exceeds absolute RSS
(**107,048,960 bytes**) and max-event latency (**152.13 ms**). The current
target packet is
`evaluation/reports/phase8_blinded_output_packet_20260928_missing_world_clarification_v1.json`;
it joins to the target at **74/74**, while both human reference classes remain
missing.

The latest continuation also releases a context clarification for the
declarative `learn_uncertain` event only because an event-bound native learning
request explicitly has an unselected source and no answer authority. Current
Phase 8 is **55 replies / 6 errors / 13 authorized silences**, authority
**74/74**; the complete Phase 8 plus comparative-artifact tests pass **51/51**.
Latest replay and current blinded packet:
`evaluation/reports/phase8_corpus_report_20260928_uncertainty_context_clarification_v1.json`,
`evaluation/reports/phase8_blinded_output_packet_20260928_uncertainty_context_clarification_v1.json`.
The connected profile still exceeds the absolute RSS cap (**107,429,888 bytes**),
Phase 4 has **0** complete tuples/promotions, and comparative human scoring is
still uncollected; keep the project goal active.

For current status, use the latest exact-tree replay and packet (the previous
v1 replay was semantically identical):
`evaluation/reports/phase8_corpus_report_20260928_uncertainty_context_clarification_v2.json`,
`evaluation/reports/phase8_blinded_output_packet_20260928_uncertainty_context_clarification_v2.json`.
The packet joins **74/74**. The second connected-profile run is deterministic
and under the latency target, but absolute RSS remains above 100 MiB at
**107,139,072 bytes**. The cognition/Phase 4 and human comparative gates remain
open.

Resource follow-up: an independent single-run fresh-process profile confirms
absolute RSS remains over the 100 MiB cap (**106,942,464 bytes**) with max
event latency **147.22 ms**. A runtime-prewarm trim experiment was semantically
equivalent but increased RSS and has been reverted. See
`evaluation/reports/phase7_profile_resource_20260928_uncertainty_context_clarification_single_v1.json`
and the latest entries in the progress tracker and canonical execution plan.
