# Conversational Thought-Manifold & Utterance Generation Progress Tracker

**Document Path:** `docs/research/psychology_affect/CONVERSATIONAL_MANIFOLD_PROGRESS_TRACKER.md`  
**Parent Plan:** [`CONVERSATIONAL_MANIFOLD_EXECUTION_PLAN.md`](CONVERSATIONAL_MANIFOLD_EXECUTION_PLAN.md)  
**Status:** Historical execution record; current cognition/communication acceptance is tracked in [`CONVERSATIONAL_MANIFOLD_COGNITION_UPGRADE_TRACKER.md`](CONVERSATIONAL_MANIFOLD_COGNITION_UPGRADE_TRACKER.md), which remains blocked on measured evidence coverage
**Target:** Minimally sufficient, ongoing conversational capability for the Jabberwock agent on Ocelot substrate, with explicit diagnostic errors instead of dismissive fallback acknowledgements.

**Current handoff (2026-09-27):** Earlier phase labels record implementation
increments, not full cognitive acceptance. Latest contrastive-correction Phase
8 replay has **66/74** graph-authoritative dispositions, **50** substantive
receipt-backed releases, **15** explicit errors, **9** authorized silent
events, and zero unclassified silence. Grounding remains **21/50 TP**, precision
**1.00**, recall **0.42**, F1 **0.592**, with zero false positives. Phase 4
remains **0/0/0** complete/eligible/promoted tuples. The active-tree replay
latency is **91.28/171.01/197.74 ms** median/p95/max, with **12/74** above
150 ms; the strict bound remains open and this run-to-run variation is not
attributed to a local change. `correction_world` selects native
`defer` and releases a correction acknowledgment through a graph-backed
receipt. Eight events still lack native disposition authority. Comparative
release remains blocked at provenance, with human reference classes absent.
Causal request intent is not causal evidence and cannot authorize an answer.
The active connected profile now passes two independent 74-event replays with
identical semantic observations, max latency **134.05/143.29 ms**, and peak RSS
**100,593,664/100,687,872 bytes**; full-boot latency and strict memory gates
remain open. No `noted` fallback is accepted. Latest report:
[`current active-tree replay`](../../../evaluation/reports/phase8_corpus_report_20260927_active_tree_replay_v1.json).

---

## 1. Phase Status Matrix

| Phase | Description | Target Files | Status | Lead / Assignee |
|---|---|---|---|---|
| **Phase 1** | Dual-Process Turn Gating in `converse()` | `substrate/world_adapter.py` | 🟢 Implemented / isolated gate passed | Subagent (`conversational-turn-gating-agent`) |
| **Phase 2** | Method Unification & Aliasing | `substrate/world_adapter.py` | 🟢 Implemented / isolated gate passed | Subagent (`conversational-turn-gating-agent`) |
| **Phase 3** | Condensed Inner Speech Trajectory | `domains/train_of_thought.py`, `domains/self_dialogue.py` | 🟢 Implemented / focused gate passed | Current agent |
| **Phase 4** | Active Routing to `LanguageProduction` | `substrate/world_adapter.py`, `domains/conversation_action.py` | 🟢 Implemented / focused gate passed | Current agent |
| **Phase 5** | Output-Null Gate & Floor Holding | `domains/conceptualizer.py`, `domains/conversation_action.py` | 🟢 Implemented / focused gate passed | Current agent |
| **Phase 6** | Settle-Back & Internalization ($MB \rightarrow MF$) | `substrate/world_adapter.py`, `seeds/motor_decision_collapse.json` | 🟢 Implemented / focused gate passed | Current agent |
| **Phase 7** | Native Rust Migration (`CLAUDE.md` Compliance) | `runners/dsl/src/cognitive_cycle.rs`, `runners/dsl/src/substrate.rs`, `runners/dsl/src/py.rs` | 🟢 Implemented / focused native tests passed | Current agent |
| **Phase 8** | Live Cognitive Action & Repair Dispatch | `substrate/world_adapter.py`, `domains/conversation_action.py` | 🟢 Implemented / focused gates passed | Current agent |

---

## 2. Invariants & Strict Constraints Checklist

- [x] **Zero LLM at Runtime (`donkey=0`):** No external teacher API calls during live conversational turns.
- [ ] **Substrate Graph Residence:** Phase 1/2 writes decision-state nodes, but full graph-residence compliance is not yet verified.
- [ ] **Discrete Quanta:** Native `TrajectoryControlState` width feedback is integer/clamped and compile-verified; end-to-end conversational enforcement is not yet verified.
- [ ] **Latency Bounds:** Target remains fast path $<50\text{ ms}$ and thought manifold path $<150\text{ ms}$; not measured.
- [ ] **Memory Budget:** Target remains RSS resident memory $<100\text{ MB}$; not measured.
- [x] **No Dismissive Failure Surface:** `noted` is forbidden as a fallback/output surface; failed response generation returns `ERROR: no communicative response could be generated.`

---

## 3. Verification Gates Status

| Gate | Verification Objective | Test Target | Status |
|---|---|---|---|
| **Gate 1** | Multi-turn continuity ($\ge 5$ statements without dismissive fallback output) | `tests/test_utterance_conversation_unification.py` | 🟢 Passed |
| **Gate 2** | Method parity & aliasing (`converse` $\equiv$ `utterance`, `utterance_for`) | `tests/test_utterance_conversation_unification.py` | 🟢 Passed |
| **Gate 3** | Native deliberation trace (`DeliberationExecutionTrace`/`Settlement` $\rightarrow$ `Committed`) | `tests/test_deliberative_production.py` | 🟢 Implemented; focused verification pending |
| **Gate 4** | Pre-articulatory parse-back (100% semantic recoverability) | `tests/test_grammar_inversion.py` | 🟢 Passed (6 focused passes) |
| **Gate 5** | Regression baseline safety | Existing test suite (`test_relations_render_migrated`, `test_conversation_reply_migrated`, `test_intent_migrated`, `test_conceptualized_converse`) | 🔴 Failed: 48 passed, 3 failed |

**Verification note:** The older `ThoughtSegment -> Committed` label was
replaced by the live native `DeliberationExecutionTrace`/settlement contract;
the test now verifies the same-goal evidence before monitor-cleared release.
Gate 4 is present and passed using the existing grammar-owned
produce/comprehend round trip and self-target monitor.

---

## 4. Execution Log

### 2026-09-25 — Native social-address reply release

- Added a graph-minted acknowledgment plan for the native
  `addressed_attention_request` disposition and routed its reply through the
  conversation-social production gate. The fixed-corpus `social_address`
  observation now releases `understood` with a graph-backed production receipt;
  focused native disposition tests pass **3/3**. This is a narrow social
  production success, not general answer generation.
- Fresh Phase 8 report:
  `evaluation/reports/phase8_corpus_report_20260925_social_reply_release.json`.
  The 74-event corpus retains 47 authoritative dispositions, force exact
  48/74 (0.649), and grounding TP17/FP0/FN33/TN24 (precision 1.00, recall
  0.34, F1 0.507). `correction_route` still fails closed at the error floor.
- Fresh Phase 7 profile:
  `evaluation/reports/phase7_profile_resource_20260925_social_reply_release.json`.
  All 74 events complete with no errors and equal deterministic replay. Peak
  conversation RSS is 108,523,520 bytes, boot/event growth 82,452,480 bytes,
  max event latency 1,203.7 ms, total 6,102.1 ms. Growth bounds pass; the
  absolute RSS bound and latency target fail.
- The Phase 8 ledger still has no small-LLM capability scores, but two full
  compatible raw runs already exist:
  `evaluation/reports/phase8_small_llm_gemma3_4b_cpu_event_context_v5_history8_seed42_20260925.json`
  and the corresponding `seed43` report. Both contain 74/74 cases, CPU-only
  (`num_gpu=0`) Gemma 3 4B, context/history8 inputs, and zero collection
  failures. The raw audit
  `evaluation/reports/phase8_raw_reference_audit_20260925_v5_event_context_history8.json`
  remains incomplete (small LLM is the only complete reference class; ELIZA,
  modern LLM, and both human classes are missing). Across the two runs, exact
  response text agrees on 74/74 cases. Seed 42 measured a mean request latency
  of 4.34 s, p95 6.23 s, max 6.55 s, and 11.66 generated tokens/s. These are
  raw reproducibility/resource observations, not cognition scores. Remaining
  gates include grounding/cognition coverage, broader and causal production,
  resource targets, Phase 4 complete evidence/promotion, and comparative
  annotation/adjudication.

### 2026-09-25 — Graph-selected correction receipt

- Added `communication_correction_reply`: it mints a reply only for the
  native `assertion_or_correction` / `defer` / `update_common_ground` state
  with `corrective_discourse_response` basis and typed correction relation.
  The selected `correction_receipt` surface says “I understand the correction.”
  It does not claim execution. The reply remains graph-linked to the inbound
  correction and must pass its own `conversation_correction_graph` production
  receipt.
- The full language-neutral evidence/arbitration module passes **16/16** (the
  focused three-case disposition selection also passes). Full Phase 8 report
  `evaluation/reports/phase8_corpus_report_20260925_correction_reply.json`
  confirms `correction_route` and `social_address` release, while preserving
  47/74 authoritative dispositions, force exact 48/74 (0.649), and grounding
  TP17/FP0/FN33/TN24 (precision 1.00, recall 0.34, F1 0.507). The gate remains
  blocked; Phase 4 still has zero complete tuples/promotions. The two prior
  authoritative mismatches are unchanged.
- Fresh Phase 7 profile
  `evaluation/reports/phase7_profile_resource_20260925_correction_reply.json`
  has 74/74 events, no errors, equal deterministic replay, 108,621,824-byte
  peak RSS, 82,608,128-byte boot/event growth, 1,203.8 ms max event latency,
  and 6,195.0 ms total latency. Growth bounds pass; absolute RSS and latency
  targets fail. Resource acceptance remains open.

Resource-tail inspection of that Phase 7 profile shows a concentrated
`info_unknown` outlier: **1,203.8 ms**, versus 66.7 ms median and 115.2 ms
p95 across the same events. The v5 Phase 8 observation for `info_unknown`
measured **2,434.5 ms** and ended at the explicit error surface. The profile
records first-use `http_transport`/acronym modules, but that is not enough to
attribute the entire delay to I/O; the next resource increment should measure
the request/dispatch phases separately before changing retrieval policy.

Phase 7 now records per-event elapsed time at the existing synchronous
`_dispatch_pending_io` boundary, separately from the cognition replay fields.
This measures the current dispatch path without changing which graph requests
are fulfilled or introducing a new answer policy. The focused resource-shape
test passes (**1/1**). The fresh all-74 profile
`evaluation/reports/phase7_profile_resource_20260925_dispatch_instrumented.json`
is deterministic (74/74, equal replay, no errors), but peaks at 108,310,528
bytes and 1,507.9 ms, so absolute RSS and max-latency gates remain failed.
For `info_unknown`, the one synchronous pending-I/O dispatch call took
1,378.2 ms of the 1,507.9 ms event, localizing most of this observed tail to
the current dispatch boundary without implying retrieval should be removed.

An isolated daemon async-host-action run,
`evaluation/reports/phase7_daemon_ingress_info_unknown_async_20260925.json`,
completed one search action without timeout: ingress max 30.9 ms, native-cycle
max 3.5 ms, completion max 1,290.9 ms, peak RSS 87,162,880 bytes, and all
listed operational bounds passed. This is not a
cognition/answer pass: disposition authority count is **0**, the `blorf`
search ended `no verified candidate`, and the reply receipt was withheld as
not recoverable. Record it only as evidence that the daemon route can drain
this async request within the resource envelope; the production/cognition
gates remain open.

The v5 raw-reference audit was regenerated with repeated seeded runs at
`evaluation/reports/phase8_raw_reference_audit_20260925_v5_seeded_repeats.json`.
It now has two complete raw reference classes (small LLM and modern LLM),
three missing classes (ELIZA and both human classes), and
`score_interpretation_performed=false`. Qwen 3.5 9B CPU seed 43 is complete
(74/74, zero collection failures, `num_gpu=0`); its raw text matches seed 42
on all 74 cases. Its mean latency is 35.399 s, p95 47.215 s, maximum 48.764 s,
and generation rate 4.18 tokens/s. This is reproducibility/resource evidence,
not a capability score; human annotation and comparative adjudication remain
open.

### 2026-09-25 — Causal retrieval candidate boundary hardening

- Hardened the daemon-owner staging boundary for external Wikidata causal
  candidates. In addition to request/token/query checks, candidates must now
  have a source label that exactly matches the requested topic under the
  retrieval normalization, a bounded well-formed statement ID, and bounded,
  typed citation records (`P854` HTTPS URLs or `P248` entity IDs). Unknown
  citation properties, malformed references, and oversized fields fail
  closed. Staged candidates remain `candidate_unverified` with
  `authority=none`; this change does not create causal edges or answer
  authority.
- Verification: `tests/test_causal_retrieval.py` passes **7/7** and
  `git diff --check` passes. Native source-identity binding, supported causal
  evidence materialization, production release, and corpus-level retrieval
  remain open.

### 2026-09-25 — Matched-profile target-run binding

- `phase8_corpus_runner` now accepts explicit v4 and v5 protocol IDs for live
  reports and blocked scaffolds. A v5 target report identifies its profile,
  marks memory/learning as not comparable, and excludes the v4-only ELIZA
  scorecard rather than silently mixing profiles. Unknown profiles fail
  closed.
- V5 scaffold tests and a live one-event v5 smoke test pass (**6 targeted
  profile checks** across the runner suite). A full 74-event target v5 report
  `evaluation/reports/phase8_corpus_report_20260925_v5_graph_context_target.json`
  completed in 62.3 s, with native replay metrics unchanged from v4 (47/74
  authoritative dispositions; force 48/74; grounding F1 0.507). Its profile
  explicitly excludes memory/learning and the v4-only ELIZA scorecard. The
  release gate remains blocked; a matching protocol ID does not settle the
  persistent graph-history versus bounded transcript-history mismatch.

### 2026-09-25 — Modern LLM v5 raw reference

- CPU-only Qwen 3.5 9B seed 42 completed all 74 v5 event-context/history-8
  prompts with zero collection failures. Raw request latency: mean 35.51 s,
  p95 46.25 s, max 46.90 s; 5,451 generated tokens at 4.19 tokens/s. These
  are hardware/runtime observations, not capability measurements.
- The updated v5 raw audit marks small LLM complete (2 complete Gemma runs)
  and modern LLM incomplete (1/2 required Qwen runs); ELIZA and both human
  references are missing. Blinded annotations are also missing, and the
  target/reference v5 inputs still require a memory-parity review.
- The second modern-LLM run (Qwen 3.5 9B, CPU-only, seed 43) is now in progress
  with the same v5 prompt profile and inference budget. The modern-LLM class
  stays incomplete until the same 74 cases finish without collection failures.

### 2026-09-25 — Comparative raw-run audit hardening

- The Phase 8 reference contract requires repeated seeded observations for
  small and modern LLMs, but the raw audit previously accepted a single full
  run as `complete_raw`. The auditor and CLI now accept repeated runs for a
  system, bind each independently to the selected protocol/corpus, and require
  two complete runs for both LLM classes. A partial seed or protocol mismatch
  keeps that class `incomplete_raw`; raw outputs remain unscored.
- Focused audit tests pass **5/5**, including protocol parity, duplicate and
  failed cases, repeated-run minima, and fail-closed behavior. The current
  v5 corpus has two complete CPU-only Gemma 3 4B runs; the modern-LLM v5 run is
  in progress. ELIZA v5 and both human references remain absent; the target
  still lacks a matched v5 report and blind annotations.

### 2026-09-22 — Explicit Failure Surface Invariant
- Replaced the canonical minimal fallback surface with `ERROR: no communicative response could be generated.`
- Added final output guards so exact `noted` and generic acknowledgements on non-social turns cannot escape from graph or legacy reply paths.
- Preserved ordinary acknowledgements for genuine social acts; unresolved routing, goal-minting, and grounding failures remain cognition work rather than being hidden by conversation wording.
- Updated gap-report and reply-flag seed responses to remove fixed `Noted` prefixes.

### 2026-09-22 — Initialization & Dispatch
- Authored canonical master plan: `docs/research/psychology_affect/CONVERSATIONAL_MANIFOLD_EXECUTION_PLAN.md`.
- Consolidated motor/control system cross-domain principles (3-tier latency sheets, motor decision collapse, output-null preparation, efference copy forward modeling, structural envelopes, symmetric discrete quanta).
- Integrated method unification and aliasing architecture into the canonical plan.
- Initialized this progress tracking document (`CONVERSATIONAL_MANIFOLD_PROGRESS_TRACKER.md`).
- **Dispatched Subagent:** Launched `conversational-turn-gating-agent` to execute Phase 1 (Dual-Process Turn Gating in `WorldAdapter.converse()`) and Phase 2 (Method Unification and Aliasing on `WorldAdapter`).

### 2026-09-22 — Phase 1 & Phase 2 Execution Completed
- **Phase 1 (Dual-Process Turn Gating in `WorldAdapter.converse()`):**
  - Implemented `_deliberate_turn_continuation` on `WorldAdapter`. When a declarative statement arrives, the system extracts concept mentions, performs plural/suffix reduction, looks up graph presence, and evaluates active continuation options:
    1. Direct/taught facts (`_fact_for`).
    2. Transitive inference via `train_of_thought.transitive_ancestors` and `self_dialogue.self_answer`.
    3. Concept-held frames (`self_dialogue.held_frames_for_topic`).
    4. Residual stance transitions (`train_of_thought.residual_stance`).
    5. Active follow-up inquiries.
  - Implemented `_record_conversation_decision` utilizing `motor_decision_collapse` semantics, stamping `ConversationDecisionState` nodes with candidate token, residual, and deeper_enabled into the Rust substrate.
  - Prevented premature conversation termination on declarative statements; ungrounded input now exposes an explicit diagnostic error rather than a dismissive fallback.
  - Ensured all fast reflex social acts (`_SOCIAL_ACTS`) continue responding appropriately.
- **Phase 2 (Method Unification and Aliasing on `WorldAdapter`):**
  - Added class-level alias `WorldAdapter.utterance = WorldAdapter.converse` ensuring byte-identical invocation between both entry points.
  - Verified `WorldAdapter.add_inbound` cleanly delegates to `receive_utterance(text, speech_act=self.classify_speech_act(text), speaker=speaker)`.
  - Unified `utterance_for(meaning)` to handle both graph NodeIDs and relational/goal dictionaries, routing communicative goal frames to the language generation pipeline (`full_text_for`) and relational meanings to graph RenderRules, aliasing `WorldAdapter._render_node = WorldAdapter.utterance_for`.
  - Fixed pre-existing failure in `test_no_python_decision_in_the_wiring` (`tests/test_conceptualized_converse.py`) by ensuring explicit `"answer"`, `"inform"`, and `"request"` force kinds are invoked appropriately.
- **Verification & Acceptance:**
  - Created test battery `tests/test_utterance_conversation_unification.py` testing method parity, alias equivalence, and multi-turn dialogue continuity across 5 consecutive non-question statements without floor drops (`5/5 passed in 2.73s`).
  - Ran regression suite:
    - `tests/test_relations_render_migrated.py` (`12/12 passed in 0.68s`).
    - `tests/test_conversation_reply_migrated.py` (`6/6 passed in 0.49s`).
    - `tests/test_intent_migrated.py` (`27/27 passed in 1.41s`).
    - `tests/test_conceptualized_converse.py`: `test_no_python_decision_in_the_wiring`, `test_formed_intent_in_live_answer_path`, and `test_monitor_gates_a_revision_on_the_live_agent` passing cleanly.
  - Dedicated Phase 1/2 verification passed: `tests/test_utterance_conversation_unification.py` (`5 passed in 3.28s`), including zero-LLM assertions (`donkey=0`).
  - Broader regression rerun: `48 passed, 3 failed in 149.91s`.
  - Failures in `tests/test_conceptualized_converse.py`: ask-back punctuation/intent expectation, audience-dependent delivery, and ungrounded rich-prose fallback. These are unresolved regressions; Gate 5 is not accepted.
  - Phase 6 now persists candidate `DecisionOption` values and applies the seeded internalization gain; native Rust scheduling and full scalar-collapse integration remain Phase 7 work.
  - Latency (`<50 ms` / `<150 ms`), RSS (`<100 MB`), native Rust scheduling, and full graph-residence compliance were not measured by the available verification run and remain unverified rather than confirmed.

### 2026-09-22 — Phase 3 Execution Completed
- Added graph-native `held_graph_frame_for_topic()` traversal with explicit concept paths and graph-derived recovery sets.
- Added `realize=False` mode to `self_answer()` for intermediate hops; direct callers retain the existing realized-answer default.
- Updated `run_inner_conversation()` so intermediate turns do not invoke `realize_goal_clause()` or parse-back; only the collapsed final turn is realized and monitored.
- Added `tests/test_condensed_inner_speech.py` covering one-final-realization behavior and graph-only path reporting.
- Phase 3 verification: focused tests passed (`7 passed in 3.67s` with the Phase 1/2 suite).
- Nearby compatibility suite: `48 passed, 9 failed`; failures remain in existing reference/conversation routing and ask-back behavior, not the Phase 3 focused tests. Gate 5 remains failed.

### 2026-09-22 — Phase 4 Execution Completed
- Added `WorldAdapter._realize_frame_reply()` as the active semantic-frame production path.
- Audience conditioning now runs through `audience_driven_production.select_utterance()` before grammar realization; the selected rung and realization trace are retained in `_last_frame_realization`.
- Final clause realization runs through `predictive_reading.realize_goal_clause()` and the grounded `LanguageProduction` producer, preserving grammar-owned SVO order and FunctionWord insertion.
- Added `conversation_action.realize_frame_reply()` as the shared mechanical bridge for conversation-action callers.
- Updated goal-frame `utterance_for()` routing to use the active frame path while preserving graph RenderRules for relational/node meanings.
- Added `tests/test_active_frame_production.py` covering audience selection, grammar realization, FunctionWord output, and entry-point parity.
- Phase 1–4 focused verification: `21 passed in 4.87s`.
- Full Gate 5 remains failed from the previously recorded compatibility regressions; no claim of full-suite recovery is made by this phase.

### 2026-09-22 — Phase 5 Execution Completed
- Extended `conceptualizer.scan_and_monitor()` with an output-null candidate path that scores the candidate through `self_target_monitor.score_self_target()` and writes graph-resident `OutputNullCandidate`, `Verdict`, and `Committed` records.
- Added a bounded one-repair pass to `_realize_frame_reply()`; unrecoverable candidates remain uncommitted and are not returned as overt replies.
- Added register-shaped floor holders through `conversation_action.floor_holding_reply()` and wired deep continuation branches to emit them while deliberation is enabled.
- Added `tests/test_output_null_gate.py` covering successful commitment, bounded repair withholding, and floor holding.
- Phase 1–5 focused verification: `12 passed in 4.96s`.
- Full Gate 5 remains failed from the previously recorded compatibility regressions; no claim of full-suite recovery is made by this phase.

### 2026-09-22 — Phase 6 Execution Completed
- Replaced the audit-only conversation decision stamp with persistent `DecisionOption` records keyed by candidate token.
- Applied the seeded `internalization_gain` and `settle_tolerance` policy when available, with the same defaults for minimal adapters that do not load the motor seed.
- Each settled turn now records fast value, grounded value, learned value, residual, settle mode, and experience count on `ConversationDecisionState`; winning options increment `decision_experience_count` and update `learned_value` toward `grounded_value`.
- Added `tests/test_conversation_settle_back.py` covering repeated internalization and deep-to-shallow transition.
- Phase 1–6 focused verification: `14 passed in 5.09s`.
- Full Gate 5 remains failed from the previously recorded compatibility regressions; native Rust migration remains Phase 7.

### 2026-09-22 — Phase 7 Execution Completed
- Changed the public PyO3 `tick()` boundary from the legacy `GraphThenStruct` plan to `CyclePlan::Default`, allowing an enabled graph `DualProcessPolicy` to select the native hard-first System-1/System-2 schedule.
- Added native `Substrate::apply_trajectory_control()` for graph-resident `TrajectoryControlState` nodes. Integer deviation thresholds drive `tangent_width += widen_step` or `tangent_width -= narrow_step`, with graph-authored min/max clamping and persisted previous-width, adjustment, and epoch fields.
- Integrated the controller into the native cycle trace after graph/struct settlement or the hard-real-time System-1 phase, so feedback is not a Python-side decision.
- Added Rust tests for quantized widening/narrowing and for the hard-sheet-before-feedback ordering.
- Verification: `cargo check --lib` and `cargo check --tests` passed (with existing workspace warnings). Using the repository `.venv` Python 3.13 interpreter plus its library link path, `cargo test cognitive_cycle::tests --lib` passed (`9 passed, 0 failed; 826 filtered out`).
- Full Gate 5 remains failed from the previously recorded compatibility regressions. Latency, RSS, and full end-to-end conversational graph-residence measurements remain unverified.

### 2026-09-22 — Phase 8 Execution Completed
- Connected the live `WorldAdapter.converse()` loop to the existing graph-produced comprehension/action faculty.
- Instruction turns now dispatch to `conversation_action.act_on_instruction()`, minting `report_self` and `describe_scene` goals and using the agent's held faculties for content.
- Frontier/untyped gaps now dispatch to `conversation_action.ask_back()`, recording a clarification Message with `responds_to`, `expects_response`, and the actual trouble source.
- Action/repair results take precedence over topic readback; a faculty failure still falls through to the explicit error invariant rather than `noted`.
- Focused verification: 5 conversation-loop gates passed, 2 conceptualizer/action gates passed, and 2 honest fallback gates passed. Broader regression remains failing in legacy topic grounding, register fallback, and stale expectations of the forbidden `noted` surface.

### 2026-09-24 — Substrate reuse and architecture audit

- Re-audited the current implementation before continuing. Existing
  `DiscourseStore`, `DiscourseState`/`CommonGround`, goal binding,
  `ThoughtManifold`/Phase 4A, gap learning, production gates, and native cycle
  scheduling remain the authorities; no parallel conversation store or
  candidate scorer is warranted.
- Corrected stale planning language: the goal-binding helper already exists in
  `conversation_action._bind_goal_to_inbound()` and is tested. It must not be
  recreated under `discourse_state`.
- Identified the actual missing cognition seam: a structured proposition and
  epistemic-commitment lifecycle connecting neutral semantic evidence,
  attribution, evidence status, common-ground uptake/challenge, and
  situation-model consequences. Parse structure, lexical Concepts, action
  authorization, and reply text are not substitutes.
- Confirmed that the live ingress is still English-shaped and structurally
  turn-oriented. The next architecture increment must accept neutral
  semantic/semiotic event evidence and allow non-turn events to update or
  defer cognition without requiring a reply.
- Local `.venv` reuse-boundary battery: **39 passed in 12:31**. This does not
  close the broader Phase 2/4/5/6/7/8 gates.

### 2026-09-24 — Phase 2Q neutral event and proposition transport

- Added `WorldAdapter.ingest_semantic_event(...)` for language-adapted,
  non-turn semantic evidence. It writes the existing interpretation and
  discourse-event records without creating a `Message`, invoking the text
  parser, or selecting a reply.
- Added the explicit neutral proposition bridge in
  `domains/proposition_commitment.py`. It records proposition content,
  evidence, argument roles, attribution, and source-event provenance only when
  the adapter supplies the complete neutral evidence schema.
- Unsupported, parse-only, lexical, or surface-derived evidence remains
  ungrounded and graph-unchanged. Proposed propositions are not silently
  accepted into common ground.
- Unknown semantic force now raises an explicit evidence error rather than
  defaulting to assertion.
- `.venv` verification: integrated proposition/ingress battery **11 passed in
  109.62s**; the existing reuse-boundary battery remains **39 passed in
  12:31**. Native uptake/challenge and situation-model consequence remain
  pending.
- Added the self-load-only native proposition lifecycle seed with explicit
  accept/challenge/suspend/retract transitions and no proposed retraction.
  Native lifecycle verification: **4 passed in 62.96s**. The subsequent Phase
  2R entry records the verified consequence projection; no consequence was
  inferred from lifecycle status alone.

### 2026-09-24 — Phase 2R accepted-proposition situation projection

- Added a mechanical `apply_situation_consequence()` seam that reuses
  `situation_model_reader.ingest_predication()` and its native inference rules.
- It requires explicit accepted uptake, affirmative polarity, proposition
  provenance, and complete neutral agent/object roles. It rejects status-only,
  negated, challenged, suspended, retracted, parse-only, and underspecified
  propositions; replay is idempotent.
- The resulting `SituationModelConsequence` is labeled as an accepted-common-
  ground projection, not external truth.
- Verification: proposition/lifecycle/consequence battery **12 passed in
  111.11s**; the complete non-turn ingress → proposition → native uptake →
  situation-model chain adds **5 passed in 81.02s**. The existing situation
model wire suite passes **9 tests in 2.50s**; Python compilation, JSON
validation, and `git diff --check` pass.

### 2026-09-24 — Phase 2S extension and Phase 3B scoped CommonGround

- Added the Phase 2S lifecycle/boundary coverage module with accepted-to-
  retracted history, failed retraction, conflicting replay, malformed
  multi-referent evidence, ambiguous/no-world/contradicted frames, and
  turn-mode invariance. Focused verification: **11 passed in 190.47s**.
- Tightened the proposition-to-situation adapter to require the existing
  situation-model reader's typed `change_of_state` result before creating a
  consequence node. Accepted properties, statives, and generic events now
  fail closed.
- Corrected the CommonGround authority so event claim deltas resolve to the
  addressed participant's existing scoped ledger instead of always selecting
  the first ledger on the discourse state. No parallel ledger or proposition
  lifecycle was introduced.
- Phase 3 stress assertions now verify separated claims for distinct
  addressees. The dependent local `.venv` battery is **35 passed in 462.52s**;
  compilation, JSON validation, and `git diff --check` pass.
- A compatibility audit ran **38 targeted tests in 132.61s**. Scope is
  recipient-relative rather than `(speaker, addressee)` pair-relative by
  design; existing shared-ledger and explicit proposition-handle behavior is
  preserved.

### 2026-09-24 — Phase 4P proposition-consequence boundary

- Added a focused native-boundary suite proving that an accepted situation
  consequence does not itself mint a thought or deliberative candidate.
- Incomplete authored Phase 4 evidence is rejected; a complete tuple is
  transported once with proposition → consequence → evidence provenance, and
  native rules retain selection authority.
- Local `.venv` verification: **4 passed in 67.74s**. This does not claim
  production deliberations or corpus-level Phase 4 completion; the fixed
  corpus still has no complete upstream Phase 4 tuple observations.

### 2026-09-24 — Phase 6P receipt-backed semantic recoverability measurement

- Added an evaluation-only receipt classifier using existing production-gate
  records. It reports recoverable receipts, explicit/withheld outcomes,
  released semantic mismatches, and missing authoritative evidence without
  treating replies or trace flags as semantic evidence.
- Focused `.venv` test: **17 passed in 3.83s** including production-gate
  idempotence and semantic-intent/state separation. Existing 74-event
  `phase6o` readback: **31** receipt-semantic recoverable, **34**
  explicit/error or withheld, **9** receipt-semantic mismatches, **0** missing;
  **74/74** events measured. Runtime state remains a separate diagnostic with
  47 adapter-observation mismatches.
- This closes a measurement gap only. Semantic recoverability exit remains
  open pending adjudication/correction of the mismatched receipt dimensions.

### 2026-09-24 — Phase 2T supported event-to-commitment overlay

- Added an independent seven-case / nine-step overlay keyed to existing Phase
  0 event IDs. The 74-event corpus remains byte-for-byte unchanged.
- The overlay measures event identity, proposition materialization, explicit
  native uptake/status, proposition and consequence provenance, typed
  situation-model projection, and fail-closed negatives. It uses no reply
  evidence and makes no external-truth claim.
- Local `.venv` verification: **3 passed in 121.50s**. Results: 9/9 event
  identities, materialization/status/consequence accuracy all **1.0**, five
  proposition-provenance cases, one consequence-provenance case, and four
  fail-closed negatives.

### 2026-09-24 — Phase 7K neutral semantic-event envelope

- Added an evaluation-only replay/resource profile for challenged, accepted
  typed-consequence, and malformed neutral events. It records graph growth,
  latency, RSS, proposition/CommonGround/consequence readback, no-message,
  no-turn, no-reply, malformed-evidence, and fresh-graph replay invariants.
- Local `.venv` verification: **4 passed in 45.41s**. Native lifecycle and
  situation-model readback remain graph authorities; the profile labels the
  post-ingress drain separately because the public ingress does not expose the
  internal arbitration call's step trace.

### 2026-09-24 — Phase 6Q receipt semantics correction

- Corrected the Phase 6 measurement boundary: receipt `semantic_intent` is
  communicative/action content, not cognitive disposition. It no longer gets
  compared directly to corpus `expected_state`.
- Added a graph-commitment idempotence guard so repeated release of the same
  selected commitment does not mint duplicate released receipts. Production
  gate regression: **12 passed**; receipt-recoverability plus gate battery:
  **17 passed in 3.83s**.
- Recomputed `phase6o`: 31 receipt-semantic recoverable, 34 explicit/withheld,
  9 receipt-semantic mismatches (force 4, multiplicity 5), 0 missing. The 47
  runtime-state mismatches are now explicitly diagnostic and require separate
  cognition/ontology adjudication; they are not silently treated as receipt
  semantics.

### 2026-09-24 — Phase 2S isolated proposition/commitment measurement

- Added a separate four-case neutral proposition overlay rather than adding
  unsupported events to the fixed 74-event corpus. The existing grounding
  precision/recall denominator and recall claim are unchanged.
- Added `evaluation/proposition_commitment_measurement.py` and its test. Each
  case uses a fresh graph, explicit self-load-only lifecycle loading, and
  asynchronous neutral ingress. The report measures commitment status,
  consequence projection, and evidence provenance independently of replies.
- Results: commitment status accuracy **1.0**, consequence projection accuracy
  **1.0**, provenance complete **4/4**, supported consequences **1/4**.
  Accepted uptake projects `drop(john, glass)` into the existing situation
  model; challenged, suspended, and negated propositions do not.
- `.venv` combined verification: **24 passed in 252.68s**. This closes only
  the isolated measurement gate. The next coverage increment is retraction,
  contradiction, multi-referent, ambiguous, and no-world proposition cases;
  no Phase 4 candidate promotion is authorized without its complete native
  evidence tuple.

### 2026-09-24 — Phase 5H/5I production recurrence evidence audit

- Reused the existing Phase 5 recurrence adapter and native gap authorities;
  no conversation-specific learning ledger or text-derived identity was added.
- Replaying `question_unknown` with the same and a distinct event identifier
  did not produce two graph-native observations for one stable gap identity.
  The fixed communication corpus also lacks explicit
  `gap_identity`/`learning_stage`/`verification_status` observations.
- Production recurrence and learning claims remain unavailable by design.
  Local `.venv` verification of the recurrence adapter and Phase 5A–5G
  authorities: **17 passed in 141.70s**. The next increment requires a
  separately authored, provenance-bearing learning fixture.

### 2026-09-24 — Phase 4Q auditable deliberation integration failures

- The live Phase 4 bridge now records a graph-resident
  `CognitiveIntegrationDiagnostic` when mechanical evidence transport fails,
  linked to the inbound message and discourse event. It remains fail-closed:
  no candidate, selection, or surface fallback is created by the diagnostic.
- The diagnostic is idempotent for the same message/event and preserves native
  Phase 4A authority. Local `.venv` verification: **11 passed in 188.53s**.

### 2026-09-24 — Phase 6Q runtime cognitive-state evidence separation

- Phase 8 observations now distinguish cognitive state, evidence source,
  authority, evidence availability, and release state. Interpretation readback
  is not treated as native disposition authority, and receipt semantic intent
  is not compared to cognitive state.
- Pre-fix 74-event report: 20 graph goal-lifecycle readbacks, 54
  interpretation readbacks, 29 receipt-semantic recoverable, 38
  explicit/withheld, 7 released semantic mismatches, 0 missing, and 47
  separate runtime-state mismatches.
- After the cognition-owned pronoun-target correction and typed authority
  readback correction, the final report is 30 receipt-semantic recoverable,
  38 explicit/withheld, 6 released semantic mismatches, 0 missing, and 45
  runtime-state mismatches. The final adjudication split is 29 state matches,
  38 disposition-authority gaps, and 7 genuine graph-state mismatches.
- Full `.venv` Phase 8/receipt battery: **23 passed in 377.24s**; focused
  Phase 6Q tests: **8 passed**.

### 2026-09-24 — Phase 6Q runtime-state adjudication split

- Added the evaluation-only runtime-state adjudication overlay. It classifies
  mismatches by evidence authority and never uses reply text or receipt
  semantic intent as cognitive-state evidence.
- The fresh Phase 6Q artifact contains 27 state matches, 38
  `disposition_authority_missing` cases, and 9 genuine
  `graph_cognitive_state_mismatch` cases. The nine graph-backed cases are the
  next cognition-owned investigation set; the 38 authority gaps require a
  native disposition readback contract before they can be scored.
- Local `.venv` verification: **2 passed in 0.14s**.

### 2026-09-24 — Phase 6R typed overlap/partial-event metadata

- Preserved adapter-provided `interaction_relation` and `literal_form` on
  graph-resident `DiscourseEvent` payloads. This is transport evidence only;
  it does not choose a defer/repair/reply outcome.
- Phase 8 corpus transport now supplies the typed fields, and live graph
  readback is verified for a fragment/overlap event.
- Local `.venv` verification: **3 passed in 52.95s**.

### 2026-09-24 — Phase 6S native typed partial-event disposition

- Reused the existing graph-native `communication_intent_arbitration` seed to
  consume typed `overlap`/`fragment` evidence. The native interpretation now
  records `cognitive_disposition=defer` and
  `arbitration_basis=typed_overlap_partial_event`; no reply or turn boundary
  is authored by this rule.
- Fresh replay: **35/74 state matches**, **39** runtime mismatches, split into
  **37** missing disposition-authority cases and **2** graph-owned mismatches
  (`question_followup`, `error_empty`). Receipt semantics remain **30**
  recoverable, **38** explicit/withheld, **6** released mismatches, **0**
  missing. The report is
  `evaluation/reports/phase8_corpus_report_20260924_phase6q.json`.
- `.venv` verification: **29 focused tests passed in 566.43s**; full corpus
  replay completed with **74/74** observations.

### 2026-09-24 — Phase 7L production-shaped communication envelope

- Added a bounded live communication profile over eight existing corpus events.
  It measures structural graph readback, typed overlap/non-turn preservation,
  explicit error presence, replay determinism, RSS growth, and elapsed time;
  surface text is not used as semantics and turn-taking is not required.
- Result: **8/8** observations, **377 nodes / 11,697 edges** added,
  **30,740.9 ms** elapsed, **132,919,296 bytes** total RSS growth; cold start
  accounts for **123,744,256 bytes** and the remaining events add
  **9,175,040 bytes**. Replay is deterministic and steady-state growth is
  bounded, but cold-start memory and latency remain open.
- Local `.venv`: **3 tests passed in 92.95s**.

### 2026-09-24 — Phase 5J explicit production-shaped learning observations

- Added a separately authored typed learning fixture with four observations,
  two stable opaque gap identities, and explicit learning-stage/verification
  metadata. Existing native recurrence and assessment rules own the result.
- Native readback: two `GapRecurrence` nodes at count **2**, two
  `GapLearningAssessment` nodes at `human_review`, and zero auto-promotions.
- `.venv` verification: **14 Phase 5 tests passed in 46.12s**.

### 2026-09-24 — Phase 5K verified repair and supervised promotion closure

- Added native failed-repair and verified-retry evidence to the typed fixture.
  One explicitly approved identity promoted; the other remained at human
  review. Failed repair was visible for both and no identity auto-promoted.
- `.venv`: **14 Phase 5 tests passed in 46.04s**.

### 2026-09-24 — Phase 5L communication-event learning observation ingress

- Added a language-neutral `learning_observation` event-context transport to
  the live communication boundary. Native `gap_awareness` now authors the
  existing `SelfConcern` with stable identity, learning-stage,
  verification-status, and message provenance.
- No surface repetition, Python learning ledger, or automatic promotion was
  introduced. Full Phase 5 verification: **15 tests passed in 69.59s**.
- Impact/priority measurement remains open for the next increment.

### 2026-09-24 — Phase 5M live recurrence impact and priority

- Two live communication events with one explicit stable identity produced a
  single native recurrence at count **2** and priority **≥2.0**.
- The assessment remained `human_review` with `auto_promoted=0.0`; identity
  and recurrence were not inferred from surface repetition.
- `.venv`: **5 fixture tests passed in 52.96s**.

### 2026-09-24 — Phase 5N competing communication-event learning identities

- Two explicit live identities with recurrence counts **2** and **3** retained
  identity-local native priorities and assessments.
- Both remained human-gated with zero automatic promotion; no cross-identity
  transfer occurred.
- `.venv`: **6 fixture tests passed in 89.07s**.

### 2026-09-24 — Phase 5O explicit corpus learning overlay

- Added a separate six-event, explicitly annotated overlay keyed to existing
  corpus IDs. The original 74-event corpus remains unchanged and does not gain
  inferred learning metadata.
- Reused live `learning_observation` ingress and native recurrence/assessment
  authorities. Three opaque overlay identities each reached native recurrence
  count **2** and priority **2**, with identity-local state and no automatic
  promotion.
- Report: `evaluation/reports/phase5_corpus_learning_overlay_report_20260924.json`.
- `.venv`: **3 overlay tests passed**; existing Phase 5 corpus contract battery
  **5 passed**.

### 2026-09-24 — Phase 6T receipt mismatch authority audit

- Added a receipt-level audit distinguishing three single-receipt force
  mismatches, two identical duplicate releases, and one competing semantic
  release pair across the current 74-event report.
- Recoverability counts remain 30 receipt-backed, 38 explicit/withheld, six
  released mismatches, and zero missing. No receipt was selected or rewritten;
  reply text and trace flags were excluded as evidence.
- `.venv`: **1 focused audit test passed**. Runtime authority correction remains
  the next Phase 6 increment.

### 2026-09-24 — Phase 6T runtime receipt idempotence

- Added inbound-message-scoped idempotence to the existing production gate for
  identical semantic releases. Competing semantic events remain distinct and
  are not collapsed by a surface heuristic.
- Fresh 74-event replay reduced receipt mismatches from six to four: 32
  recoverable, 38 explicit/withheld, four released mismatches, zero missing.
- The remaining four are three single-receipt force mismatches and one
  competing semantic release pair. The stale `Move it now.` action expectation
  was corrected to the graph-owned unresolved-reference repair state; no action
  was released without an antecedent.
- Phase 6A/6T focused verification: **25 tests passed**.

### 2026-09-24 — Phase 6U native partial-event defer/release correction

- Native typed overlap+fragment defer now prevents an adapter ask-back repair
  surface from being released. The event remains graph-deferred and fails
  closed with the explicit error floor when no candidate is available.
- Fresh 74-event readback: **31** recoverable, **42** explicit/withheld, **1**
  competing released semantic mismatch, **0** missing.
- `.venv`: **20 Phase 6/live-bridge tests passed**.

### 2026-09-24 — Phase 6V authoritative topic-release correction

- Audited the final `question_ack` mismatch to a legacy receipt emitted by
  `answer_about()` during topic retrieval, before the authoritative
  conversation-information release. Added a graph-evidence-only
  `release=False` path for the live topic fulfiller; direct legacy callers
  retain receipt-producing default behavior.
- Fresh 74-event replay: **32** receipt-semantic recoverable, **42**
  explicit/withheld, **0** released semantic mismatches, **0** missing.
- Reports:
  `evaluation/reports/phase8_corpus_report_20260924_phase6v.json` and
  `evaluation/reports/phase6_receipt_mismatch_audit_20260924_phase6v.json`.
- Focused legacy/information/idempotence verification: **13 passed**.
- The next remaining Phase 6 work is runtime-state authority adjudication;
  this is not a conversation-wording problem.

### 2026-09-24 — Phase 6W runtime-state authority adjudication

> Historical pre-scoring-correction result. The 37/37 equality count below
> treated label equality as a match before checking authority; use the
> authority-scored correction recorded later in this tracker.

- Reused the existing runtime-state adjudicator against the current Phase 8
  observation schema; no reply text, receipt semantic, or surface fallback is
  used as cognitive-state evidence.
- All **74/74** diagnostics are present: **35** matches, **37**
  `disposition_authority_missing` cases, and **2** graph-owned mismatches:
  `question_followup` and `error_empty`.
- Report:
  `evaluation/reports/phase6_runtime_state_adjudication_20260924_phase6v.json`.
  The first mismatch lacks the prior discourse context assumed by its isolated
  corpus label; the second lacks typed explicit-uncertainty evidence and is
  currently routed through a topic goal. No wording-only repair was made.
- `.venv`: **3 runtime-state adjudication tests passed**.

### 2026-09-24 — Phase 7M neutral semantic-ingress authority binding

- Reviewed the existing neutral `ingest_semantic_event()` path and confirmed
  that Python only materializes supplied semantic evidence before the native
  `communication_intent_arbitration` rule set runs. No new parser, classifier,
  reply path, or cognition store was added.
- Added the exact authority binding and provenance to
  `evaluation/native_authority_audit.py`; the audit now reports **10 bound**
  and **172 unbound** cycle/task calls.
- Reused the Phase 7K semantic-event envelope as the evidence source.
- `.venv`: **12 focused Phase 7/6 tests passed**.
- Phase 7 performance/resource exit remains open: the existing cold envelope
  is still over the documented RSS/latency budget and requires substrate-level
  profiling before optimization.

### 2026-09-24 — Phase 7N production-envelope substrate cost profile

- Added diagnostic-only boot/per-event timing, RSS-delta, and graph-delta
  fields to the existing Phase 7L envelope; semantic replay equality remains
  structural and excludes timing/resource noise.
- Profile report:
  `evaluation/reports/phase7_production_envelope_20260924_phase7n.json`.
  Boot: **16,360 ms**. First information event: **11,693 ms** and
  **116,801,536 bytes** RSS. Subsequent events: **713–3,221 ms**; steady-state
  growth: **10,231,808 bytes**. Replay: deterministic.
- The dominant first-event graph allocation is **10,755** mechanical
  `knows_concept` edges from the existing referent-resolution backfill. This
  is a substrate index/materialization cost, not a conversation wording or
  route policy problem. No optimization was applied without an equivalence
  design.
- `.venv`: **4 production-envelope tests passed**.

### 2026-09-24 — Phase 8H raw-reference integrity audit

- Added an evaluation-only audit for raw baseline envelopes. It validates the
  fixed protocol, 74 case IDs, duplicate/unknown/missing cases, collection
  failures, and scorecard availability without interpreting response text.
- Existing ELIZA-floor, Gemma 4B, and Qwen 9B runs are each **74/74** and
  failure-free. Base-human and advanced-human runs are explicitly missing.
- Report:
  `evaluation/reports/phase8_raw_reference_audit_20260924_phase8h.json`.
  Result: **3 complete_raw, 2 missing; incomplete**. No baseline score was
  inferred; the release gate remains blocked.
- `.venv`: **2 raw-reference audit tests passed**.

### 2026-09-24 — Phase 6X explicit-uncertainty error disposition

- Typed `explicit_uncertainty` evidence now reaches the graph-resident
  interpretation and native arbitration authors `error/error` state with
  explicit uncertainty provenance.
- The generic repair/action bridge is withheld for that native error state;
  the canonical explicit error is emitted.
- Focused `.venv`: **2 tests passed**. Full-corpus confirmation remains
  pending; `question_followup` remains a separate discourse-context issue.
- Targeted `error_empty` corpus replay now matches expected `error` state;
  report: `evaluation/reports/phase6_explicit_uncertainty_20260924_phase6x.json`.
- Phase 6X focused exit is **green**; the broader Phase 6W audit remains open
  on the separate `question_followup` discourse-context mismatch.

### 2026-09-24 — post-checkpoint state reconciliation

- Reconciled this tracker with the cognition-upgrade tracker and the current
  worktree. Phase 7O indexed referent equivalence is verified; the complete
  native-authority inventory is **183 bound / 0 unbound / 183 total**.
- Phase 7P is closed as a measured boundary, not as a budget pass: selective
  `sak_kind_*` readback preserves native arbitration and replay equality, while
  cold RSS/latency remain above the nominal envelope. A parity-breaking prefix
  execution prototype was rejected and removed.
- Phase 8H raw-reference integrity is measured but incomplete: ELIZA floor,
  small LLM, and modern LLM are case-complete; base-human and advanced-human
  references are unavailable. Comparative release therefore remains blocked.
- The next implementation work must target cognition/resource evidence, not
  wording: resolve or explicitly overlay the unsupported `question_followup`
  causal context, and continue substrate-level allocation work without
  changing native authority or introducing a turn-state machine.

### 2026-09-24 — Phase 6X correction and Phase 6W replay closure

- The first full replay showed that generic `explicit_uncertainty` was too
  broad: it incorrectly converted ordinary defer/repair events to error.
- Narrowed native error arbitration to distinct typed `explicit_failure`;
  ordinary uncertainty remains repair/defer evidence. The `error_empty` case
  now carries `explicit_failure` and produces the canonical explicit error.
- Focused local `.venv`: **3 tests passed**. Corrected full replay:
  **36/74** state matches, **37** missing disposition-authority cases, and
  **1** graph-owned mismatch (`question_followup`). `error_empty` matches.
- Report:
  `evaluation/reports/phase6_explicit_failure_20260924_phase6x_corrected.json`.
- Phase 6W is now adjudicated rather than patched: `question_followup` lacks
  typed causal world evidence, so its remaining mismatch belongs to the
  world-model/fixture boundary, not conversation surface behavior.

### 2026-09-24 — Post-regression cognition boundary verification

- The broader communication/native/language-neutral gate initially exposed
  three failures. They were corrected without surface-output changes:
  the new evidence kind is now admitted by the corpus contract, optional
  uncertainty is accepted for neutral semantic providers, and the existing
  self-account faculty exposes typed grounding evidence for account requests.
- Focused recovery battery: **25 passed**.
- Fresh 74-event replay remains deterministic at **36 matches / 38 mismatches**;
  the mismatch count did not regress. `question_followup` remains the sole
  graph-owned mismatch after authority adjudication; `error_empty` remains a
  native `error` match.
- Final replay report:
  `evaluation/reports/phase8_corpus_report_20260924_postregression.json`.

### 2026-09-24 — Phase 7P bounded exit verification

- Re-ran selective native kind readback, indexed referent equivalence,
  production-envelope, and semantic-event envelope tests: **11 passed**.
- Native `sak_kind_*` authority and replay equality remain intact. The measured
  cold RSS overage is explicitly attributed to substrate runtime cold
  allocation in `phase7_kind_readback_20260924_phase7p.json`; no Python
  classifier or surface workaround was introduced.
- Phase 7P bounded exit is **green with a measured resource exception**;
  broader Phase 7 production resource status remains yellow.

### 2026-09-24 — Phase 7P selective native kind-rule readback

- Added and installed the native `Substrate.export_rules_prefix(prefix)` API;
  `_graph_kind_for()` now reads only active `sak_kind_*` rules.
- Local binary rebuilt and API test passed (**1 passed**). Native authority and
  replay determinism were preserved.
- `direct_action` kind-bridge cost improved from **3,918.8 ms / 106,143,744
  bytes** to about **1,705 ms / 73,453,568 bytes**; event latency improved
  from **9,193.4 ms** to **6,813.0 ms**.
- Report: `evaluation/reports/phase7_kind_readback_20260924_phase7p.json`.
- Cold RSS remains **109,969,408 bytes**, so Phase 7 resource closure remains
  open at the substrate warm-up/runtime layer.

### 2026-09-24 — Phase 7P queued: native kind-rule warm-up/readback

- Stage tracing found the dominant cold allocation in `_graph_kind_for()`:
  complete held-rule serialization for native `sak_kind_*` arbitration.
- Replaced the separate seed-presence export scan with a resident graph Rule
  scan, removing roughly **2.2 s / 31 MB** of first-turn overhead without
  changing authority.
- Remaining export cost is roughly **3.9 s / 106 MB**. Next work is selective
  native readback or explicit boot warm-up; replacing native arbitration with
  Python classification is out of scope.

### 2026-09-24 — Phase 7O substrate integration and reinvention audit

- Added `CONVERSATIONAL_MANIFOLD_SUBSTRATE_INTEGRATION_AUDIT_20260924.md`.
- Mapped the remaining communication needs to existing substrate authorities:
  the native Concept index, communication-intent rules, discourse state,
  reflective faculties, topic goals/HeldAnswer, production receipts, typed
  partial-event arbitration, and existing deliberation evidence faculties.
- Confirmed that no new referent store, turn-state machine, self-report
  generator, release ledger, or deliberation scorer should be introduced.
- Bounded ordinary referent ingress now reuses the native Concept.name index;
  self/meta reflection retains its explicit full-vocabulary requirement.
- Corrected a read-off precedence defect that let the graph honest-floor reply
  shadow a valid graph-grounded self-organisation result. This is a cognition
  integration fix, not a wording workaround.
- `.venv`: indexed ingress and compatibility regressions **3 passed**; native
  authority/raw-reference audit battery **7 passed**.
- Status: **yellow**. Indexed equivalence/resource profiling and remaining
  adapter authority classification are still open.

#### Phase 7O increment — 2026-09-24

- Indexed ordinary ingress is now tested against a full-ledger reference:
  native referent resolution is equivalent, with bounded graph materialization.
- The existing conversation-action scene `run_rules` readback is now bound in
  the native-authority audit as evidence-only materialization.
- Authority audit: **11 bound / 171 unbound / 182 total**; unbound calls remain
  visible review debt rather than being reclassified.
- `.venv`: **2 indexed-equivalence tests** and **6 authority tests** passed.
- The optimized ordinary-event envelope remained replay-deterministic, but a
  cold probe measured **11,186 ms** and **110,010,368 bytes** RSS growth for
  only **342** event-added edges. Phase 7 resource closure remains open at the
  substrate runtime/warm-up layer; no surface conversation workaround was
  applied.

### 2026-09-24 — Pre-continuation substrate integration audit

- Re-ran the substrate integration audit before advancing the plan. The
  machine-readable record is
  `evaluation/reports/substrate_integration_audit_20260924.json`.
- The focused local `.venv` battery passed **7 tests**. Current native
  authority inventory: **11 bound / 171 unbound / 182 total**. Phase 4 has
  **0 complete** and **0 near-match** candidate tuples; no deliberation fields
  may be inferred from neighboring faculties.
- Reuse authorities were confirmed: `DiscourseStore`/Concept index for
  referents, `DiscourseState`/events for continuity, native communication
  arbitration for force/disposition, existing Goal lifecycle, ThoughtManifold
  and gap faculties for evidence, and `ProductionGateReceipt` for release.
  No parallel referent store, classifier, turn machine, scorer, learning
  ledger, or receipt type is permitted.
- Direct replay showed that `question_followup` retains the prior `gate` topic,
  but the graph contains no typed closure event or causal relation explaining
  why it closed. This is a world-model evidence gap or over-strong fixture
  label, not a reason to add a lexical follow-up rule. The next gate is to add
  typed causal setup only if that capability is intended, otherwise revise the
  expected disposition to repair/unknown.

### 2026-09-24 — Solo alignment review and conceptualizer authority continuation

- Reviewed the current project against the cognition-first, language-agnostic,
  non-inherently-turn-based objective and the substrate integration audit.
- The review identified a concrete authority defect rather than a conversation
  wording issue: the output-null candidate path still chose commit in Python
  after self-target monitoring.
- Migrated that branch to the native
  `conceptualizer_output_candidate_commit` rule. The existing evidence
  computation is retained; only graph-native recoverability now creates the
  `Committed` node.
- `.venv` verification: **36 focused gate/conceptualizer tests passed** and
  **2 native-authority tests passed**. Authority census: **14 bound / 169
  unbound / 183 total**.
- Status remains **yellow/review-required**. The next work should continue the
  same bounded audit-and-bind sequence, prioritizing existing cognitive
  faculties and avoiding new conversation-specific classifiers or turn state.

### 2026-09-24 — Curiosity-topic native settlement binding

- Integrated the existing learning-progress curiosity faculty into the native
  authority audit. `maintain_topic_interest` now records a graph receipt after
  the existing `learning_progress_curiosity` and `curiosity_topic_selection`
  rules settle.
- No new conversational classifier, turn state, scorer, or decision path was
  introduced. The adapter still only measures lexical unknowns and writes
  sensor inputs.
- Verification: authority-focused tests passed; the full curiosity suite was
  **5 passed, 1 failed**. The failure is the suite's pre-existing dirty-tree
  guard for `runners/dsl/src/py.rs`, which remains modified by earlier native
  substrate work and is outside this increment.
- Authority audit now reports **15 bound / 168 unbound / 183 total**. Continue
  with bounded native-faculty integration; do not treat this as phase closure.

### 2026-09-24 — Cognitive-cycle native boundary binding

- Bound the existing `WorldAdapter.cognitive_tick` native schedule without
  claiming authority for its Python reflex callbacks. The cycle now emits a
  `NativeCognitiveCycleReceipt` identifying `cognitive_legacy` and its native
  step count.
- `.venv` focused verification: **3 passed**; `git diff --check` passed.
- Authority audit now reports **16 bound / 167 unbound / 183 total**. The
  project remains yellow/review-required and the remaining work continues with
  bounded, evidence-producing integrations.

### 2026-09-24 — Master-cycle native boundary binding

- Bound the existing `master_legacy` schedule inside `WorldAdapter.master_tick`
  and recorded a separate native-cycle receipt. The surrounding reflex,
  thread, and concurrency work remains explicitly outside the native claim.
- `.venv` focused verification: **4 passed**; `git diff --check` passed.
- Authority audit now reports **17 bound / 166 unbound / 183 total**. Continue
  the phase-by-phase audit; no phase closure is claimed.

### 2026-09-24 — Live-loop native-cycle delegation review

- Reviewed the two live-world adapters' fallback `cognitive_tick` calls and
  bound them only as delegations to the verified native cognitive schedule.
  The surrounding world-action gate and orchestration remain separately
  classified rather than being silently promoted.
- `.venv` focused verification: **5 passed**; `git diff --check` passed.
- Authority audit now reports **19 bound / 164 unbound / 183 total**. Continue
  with the remaining explicit findings and resource measurements.

### 2026-09-24 — Actor-goal settlement authority binding

- Bound the existing actor-goal annotator's native settlement boundary and
  added an inspectable `NativeActorGoalReceipt`. Structural fact extraction
  remains adapter-side; actor-goal/codebook outcomes remain native.
- `.venv` verification: **11 actor-goal tests passed** and **3 focused
  authority tests passed**; `git diff --check` passed.
- Authority audit now reports **20 bound / 163 unbound / 183 total**. Continue
  the migration audit without treating the increment as overall completion.

### 2026-09-24 — Disclaimer-candidate settlement authority binding

- Bound the existing disclaimer candidate annotator to its native codebook
  settlement and added a provenance receipt. No surface-level conversational
  classifier or Python semantic decision was introduced.
- `.venv` verification: **7 disclaimer/conflict tests passed** and **3 focused
  authority tests passed**; `git diff --check` passed.
- Authority audit now reports **21 bound / 162 unbound / 183 total**. Continue
  through the remaining documented authority increments and resource gates.

### 2026-09-24 — Action-pair settlement authority binding

- Bound the existing action-pair annotator to its native codebook settlement and
  added a provenance receipt. Structural pair enumeration remains adapter-side;
  temporal conflict interpretation remains native.
- Focused `.venv` authority verification: **3 passed**. The full temporal
  regression was stopped after 7:52 at 100% CPU after reporting three failures;
  those failures concern existing seed/fixture/coverage behavior, not the new
  receipt boundary, and must remain visible for later repair.
- Authority audit now reports **22 bound / 161 unbound / 183 total**. The goal
  remains active and Phase 7 is not closed.

### 2026-09-24 — Temporal regression data-quality correction

- Repaired stale persisted opposing-pair notes in `seeds/taught.json` and made
  the temporal seed-audit helper tolerate list-shaped manifests.
- These are data/test-integrity corrections, not conversation-surface changes.
  The isolated temporal tests still exceeded the practical runtime envelope
  and were interrupted before completion; the temporal regression remains open.

### 2026-09-24 — Epistemic assessment authority binding

- Bound the two native settlement passes in `assess_epistemic_lean` and added
  an inspectable epistemic assessment receipt. Detection, structural forcing,
  and confidence-band decisions remain graph-native; Python remains an
  orchestration/readback layer.
- Exact `.venv` verification: **1 receipt test passed in 3.22s**. A broader
  mixed command reached **31 passed in 300.85s** before interruption due to
  slow suite selection; no broad green claim is made.
- Authority audit now reports **24 bound / 159 unbound / 183 total**. Continue
  the remaining bounded migrations and resource gates.

### 2026-09-24 — Actor self-authoring execution boundary

- Bound the native execution step after actor-goal method synthesis and added
  an authoring provenance receipt. The authoring faculties and semantic rule
  contents remain agent/native-owned; Python only sequences and records the
  boundary.
- `.venv` exact verification: **1 passed in 3.34s**; `git diff --check` passed.
- Authority audit now reports **25 bound / 158 unbound / 183 total**. Continue
  the remaining phase work; no overall completion is claimed.

### 2026-09-24 — Meaning-inference slot authority binding

- Bound the existing predication-slot meaning-inference settlement to its
  native selectional rules and recorded a provenance receipt. No language-
  specific conversational shortcut was introduced.
- `.venv` exact verification: **1 passed in 5.26s**; `git diff --check` passed.
- Authority audit now reports **26 bound / 157 unbound / 183 total**. Continue
  the remaining documented work.

### 2026-09-24 — Definitional-inference fact authority binding

- Bound predication-fact settlement to the existing native definitional rules
  and recorded a provenance receipt. The change preserves language-processing
  cognition and adds no surface conversational shortcut.
- `.venv` exact verification: **1 passed in 5.29s**; `git diff --check` passed.
- Authority audit now reports **27 bound / 156 unbound / 183 total**. Continue
  the remaining phase work.

### 2026-09-24 — Morphological-inference authority binding

- Bound morphological candidate settlement to the existing native morphology
  rules and recorded a provenance receipt. Python remains structural candidate
  enumeration; no language-specific conversational shortcut was introduced.
- `.venv` exact verification: **1 passed in 5.23s**; `git diff --check` passed.
- Authority audit now reports **28 bound / 155 unbound / 183 total**. Continue
  the remaining documented work.

### 2026-09-24 — Relational-signature inference authority binding

- Bound relational-signature aggregation to the existing native structural-
  analogy rules and recorded a provenance receipt. No surface language shortcut
  or Python semantic transfer was introduced.
- `.venv` exact verification: **1 passed in 5.37s**; `git diff --check` passed.
- Authority audit now reports **29 bound / 154 unbound / 183 total**. Continue
  the remaining phase work.

### 2026-09-24 — Recount scene realization authority binding

- Bound recount scene materialization's native realization boundary and added a
  provenance receipt. The change preserves graph-native event/residual
  decisions and does not add conversational surface logic.
- `.venv` exact verification: **1 passed in 3.38s**; `git diff --check` passed.
- Authority audit now reports **30 bound / 153 unbound / 183 total**. Continue
  the remaining phase work.

### 2026-09-24 — Passive and intent-signal analysis authority binding

- Bound passive-role and intent-signal analysis to their existing native rules
  and recorded separate provenance receipts. No surface conversational rule was
  added; structural discourse evidence remains the source.
- `.venv` exact verification: **1 passed in 5.17s**; `git diff --check` passed.
- Authority audit now reports **32 bound / 151 unbound / 183 total**. Continue
  the remaining phase work.

### 2026-09-24 — Relational-noun analysis authority binding

- Bound `media_analysis.annotate_relational_noun` to the existing native
  relational-noun/unsaid-role settlement rules. Python remains a mechanical
  nominal-evidence writer; native graph rules retain interpretation and
  residual-question settlement.
- Added and verified a native provenance receipt with no Python outcome
  selection.
- `.venv` exact verification: **1 passed in 5.20s**; `git diff --check` passed.
- Authority audit now reports **33 bound / 150 unbound / 183 total**. Continue
  the remaining phase work; no overall completion is claimed.

### 2026-09-24 — Recount reasoning authority binding

- Bound the recount faculty's instruction-to-reasoning native execution and
  added a provenance receipt. Parsing, scene projection, and realization were
  not reimplemented or reclassified as conversation logic.
- `.venv` focused receipt verification: **1 passed in 0.35s**; `git diff
  --check` passed. A full recount integration attempt exceeded the bounded
  90-second observation window and remains unverified.
- Authority audit now reports **34 bound / 149 unbound / 183 total**. Continue
  the remaining phase work; no overall completion is claimed.

### 2026-09-24 — Recount analysis reasoning authority binding

- Bound the analysis-layer recount reasoning pass to its existing native rules
  and recorded a separate provenance receipt. No new conversation scorer,
  language shortcut, or duplicate realization path was introduced.
- `.venv` focused verification: **2 passed in 0.36s**; `git diff --check`
  passed.
- Authority audit now reports **35 bound / 148 unbound / 183 total**. Continue
  the remaining phase work; no overall completion is claimed.

### 2026-09-24 — Recount analysis-scene authority binding

- Bound analysis-scene projection's native realization pass and added explicit
  provenance. The projector remains type-blind mechanical graph materialization;
  no new surface conversational logic was introduced.
- `.venv` focused verification: **3 passed in 0.46s**; `git diff --check`
  passed.
- Authority audit now reports **36 bound / 147 unbound / 183 total**. Continue
  the remaining phase work; no overall completion is claimed.

### 2026-09-24 — Conceptualizer candidate-settlement authority binding

- Bound the conceptualizer's candidate-monitor native commit pass and added
  provenance. Self-target coverage remains evidence; Python does not select
  the cognitive commit result.
- `.venv` focused verification: **1 passed in 0.39s**; `git diff --check`
  passed.
- Authority audit now reports **37 bound / 146 unbound / 183 total**. Continue
  the remaining phase work; no overall completion is claimed.

### 2026-09-24 — Information-commitment authority binding

- Bound the existing information-commitment native gate and recorded its
  wait/refine/commit decision provenance. External approval remains a distinct
  post-selection authorization step.
- `.venv` exact verification: **1 passed in 0.21s**; `git diff --check`
  passed.
- Authority audit now reports **38 bound / 145 unbound / 183 total**. Continue
  the remaining phase work; no overall completion is claimed.

### 2026-09-24 — Situation-model predication authority binding

- Bound all `situation_model_reader.ingest_predication` native fixpoint passes
  and recorded per-pass provenance. Entity/event/index materialization remains
  mechanical; native rules retain state and inference decisions.
- `.venv` exact verification: **1 passed in 2.17s**; `git diff --check`
  passed.
- Authority audit now reports **42 bound / 141 unbound / 183 total**. Continue
  the remaining phase work; no overall completion is claimed.

### 2026-09-24 — Inference-generation relation authority binding

- Bound the existing native fixpoint following `part_of` relation materialization
  and recorded provenance. No duplicate inference mechanism was introduced.
- `.venv` exact verification: **1 passed in 0.35s**; `git diff --check`
  passed.
- Authority audit now reports **43 bound / 140 unbound / 183 total**. Continue
  the remaining phase work; no overall completion is claimed.

### 2026-09-24 — Disambiguation authority binding

- Bound coherence re-decoding and metonymic re-decoding to their existing
  native coercion rules, with separate provenance receipts. No Python semantic
  re-binding or language-specific conversational shortcut was added.
- `.venv` exact verification: **1 passed in 2.22s**; `git diff --check` passed.
- Authority audit now reports **45 bound / 138 unbound / 183 total**. Continue
  the remaining phase work; no overall completion is claimed.

### 2026-09-24 — Reflective concern-decode authority binding

- Bound concern decoding to the existing native shape-decode loop and recorded
  provenance. Python remains observation ingress/readback; no surface-level
  conversation path was added.
- `.venv` exact verification: **1 passed in 0.33s**; `git diff --check` passed.
- Authority audit now reports **46 bound / 137 unbound / 183 total**. Continue
  the remaining phase work; no overall completion is claimed.

### 2026-09-24 — Reflective role/correspondence authority binding

- Bound relation-cue role checking and structural correspondence settlement to
  their existing native rules, with separate provenance receipts. No duplicate
  learning or conversation mechanism was introduced.
- `.venv` focused verification: **2 passed in 32.37s**; `git diff --check`
  passed.
- Authority audit now reports **48 bound / 135 unbound / 183 total**. Continue
  the remaining phase work; no overall completion is claimed.

### 2026-09-24 — Reading-drive native-cycle delegation

- Bound the reading-drive steady-state loop as delegation to the existing
  native cognitive cycle. Python remains a bounded observer and does not choose
  stage outcomes.
- `.venv` exact verification: **1 passed in 3.31s**; `git diff --check` passed.
- Authority audit now reports **49 bound / 134 unbound / 183 total**. Continue
  the remaining phase work; no overall completion is claimed.

### 2026-09-24 — Cognitive rule-frame authority binding

- Bound private rule-document reading, situation observation, prediction
  commitment, and drafting to existing native rule settlements, with separate
  provenance receipts. World action remains an explicit later boundary.
- `.venv` exact verification: **1 passed in 2.09s**; `git diff --check` passed.
- Authority audit now reports **53 bound / 130 unbound / 183 total**. Continue
  the remaining phase work; no overall completion is claimed.

### 2026-09-24 — Capability-graph authority binding

- Bound capability fixpoint settlement to the existing native rules and added
  provenance. Python remains graph construction/readback; no duplicate
  competence scorer was introduced.
- `.venv` exact verification: **1 passed in 0.24s**; `git diff --check` passed.
- Authority audit now reports **54 bound / 129 unbound / 183 total**. Continue
  the remaining phase work; no overall completion is claimed.

### 2026-09-24 — Autonomous-discovery authority binding

- Bound native discovery settlement and placed its receipt on the native
  substrate, preserving the adapter's closed-write safety boundary.
- `.venv` corpus verification: **8 passed in 0.34s**; `git diff --check`
  passed.
- Authority audit now reports **55 bound / 128 unbound / 183 total**. Continue
  the remaining phase work; no overall completion is claimed.

### 2026-09-24 — Analogical correspondence authority binding

- Bound pair, directional, and legacy safety correspondence passes to existing
  native analogical rules, with provenance receipts. No Python analogical
  scorer or conversation shortcut was introduced.
- `.venv` exact verification: **1 passed in 16.46s**; `git diff --check`
  passed.
- Authority audit now reports **58 bound / 125 unbound / 183 total**. Continue
  the remaining phase work; no overall completion is claimed.

### 2026-09-24 — Procedural referent authority binding

- Bound procedural referent resolution and scratch retirement to their existing
  native rules, with per-pass provenance receipts. No unrelated content can be
  promoted by the cross-check itself.
- `.venv` exact verification: **1 passed in 16.67s**; `git diff --check`
  passed.
- Authority audit now reports **60 bound / 123 unbound / 183 total**. Continue
  the remaining phase work; no overall completion is claimed.

### 2026-09-24 — Analogy-search authority binding

- Bound analogy observation and crystallization to existing native rules, with
  separate provenance receipts. No Python analogy scorer or surface shortcut
  was introduced.
- `.venv` exact verification: **1 passed in 0.28s**; `git diff --check` passed.
- Authority audit now reports **62 bound / 121 unbound / 183 total**. Continue
  the remaining phase work; no overall completion is claimed.

### 2026-09-24 — Predictive-reading native-cycle delegation

- Bound predictive reading and adaptive dwell as delegation to the existing
  native cycle. Python remains stage setup/readback; no conversational surface
  logic was introduced.
- `.venv` focused verification: **2 passed in 7.30s**; `git diff --check`
  passed.
- Authority audit now reports **64 bound / 119 unbound / 183 total**. Continue
  the remaining phase work; no overall completion is claimed.

### 2026-09-24 — Cross-text residual re-decode authority binding

- Bound residual re-decode to the existing native `sd_redecode` rule and added
  provenance. Python remains feature/axis materialization and readback.
- `.venv` exact verification: **1 passed in 2.15s**; `git diff --check` passed.
- Authority audit now reports **65 bound / 118 unbound / 183 total**. Continue
  the remaining phase work; no overall completion is claimed.

### 2026-09-24 — Reasoning/CAN correspondence authority binding

- Bound reasoning/CAN correspondence settlement to the existing native rules
  and recorded provenance. Python remains mechanical name-token preparation.
- `.venv` exact verification: **1 passed in 0.35s**; `git diff --check` passed.
- Authority audit now reports **66 bound / 117 unbound / 183 total**. Continue
  the remaining phase work; no overall completion is claimed.

### 2026-09-24 — AST-to-rule authority binding

- Bound AST expression/body term composition to existing native AST-to-term
  rules, with separate provenance receipts. Python remains AST ingress/readback.
- `.venv` exact verification: **1 passed in 1.73s**; `git diff --check` passed.
- Authority audit now reports **68 bound / 115 unbound / 183 total**. Continue
  the remaining phase work; no overall completion is claimed.

### 2026-09-24 — Faculty-autogenesis authority binding

- Bound the native faculty discovery pass and recorded provenance. Python
  remains evidence serialization/synthesis I/O; native rules retain lifecycle
  and escalation decisions.
- `.venv` exact verification: **1 passed in 0.82s**; `git diff --check` passed.
- Authority audit now reports **69 bound / 114 unbound / 183 total**. Continue
  the remaining phase work; no overall completion is claimed.

### 2026-09-24 — Minting-train segment authority binding

- Bound minting-train segment fixpoints to existing native rules and added
  per-segment provenance receipts. Python remains bounded traversal/evidence
  preparation.
- `.venv` focused verification: **3 passed in 0.27s**; `git diff --check`
  passed.
- Authority audit now reports **70 bound / 113 unbound / 183 total**. Continue
  the remaining phase work; no overall completion is claimed.

### 2026-09-24 — Solver-dispatch settlement authority binding

- Bound solver CAN-network settlement and goal-resolution dispatch to the
  existing native rules, with typed provenance receipts. Python remains
  mechanical scheduling/evidence preparation and readback.
- `.venv` focused verification: **22 passed in 34.54s** for
  `test_solver_dispatch_migrated.py` and `test_solver_nl_adapter.py`.
- The separate CAN growth test still fails at its pre-existing assertion
  (`grown=False`) with the receipt change absent as well; this remains an
  open substrate baseline issue.
- Authority audit now reports **73 bound / 110 unbound / 183 total**.
  Continue the remaining phase work; no overall completion is claimed.

### 2026-09-24 — Fallback-report classification authority binding

- Bound fallback-report classification to the existing native vocabulary rules
  and recorded typed provenance. Python remains counter transcription; no
  conversational fallback behavior was added.
- `.venv` focused verification: **3 passed in 0.50s**; `git diff --check`
  passed.
- Authority audit now reports **74 bound / 109 unbound / 183 total**.
  Continue the remaining phase work; no overall completion is claimed.

### 2026-09-24 — Affect-coordinate readback authority binding

- Bound prosody's affect-coordinate readback to the existing native modulator
  rules and recorded provenance. No Python valence/arousal computation or
  surface-level conversation fix was introduced.
- Focused affect behavior passed. The suite's separate `.so` MD5 discipline
  check remains red (`8d3229dddcdb1781a17626eaab428c88` versus its canonical
  hash), an existing native-binary state issue.
- Authority audit now reports **75 bound / 108 unbound / 183 total**.
  Continue the remaining phase work; no overall completion is claimed.

### 2026-09-24 — Upload-text cognitive-pump delegation

- Bound upload-text stage pumping to the already-bound native cognitive cycle;
  no new turn-based or surface conversational behavior was introduced.
- `.venv` test invocation was explicitly skipped because optional `cv2` is not
  installed (`1 skipped in 0.27s`).
- Authority audit now reports **76 bound / 107 unbound / 183 total**.
  Continue the remaining phase work; no overall completion is claimed.

### 2026-09-24 — Foveal salience authority binding

- Bound foveal salience resolution to the substrate's existing
  `ArgminUnique` rule and recorded provenance. The no-Python-selection
  invariant remains intact.
- Verification was blocked at collection by the engine-provenance guard:
  the native binary is stale against 18 newer Rust sources. The guard was
  correctly respected rather than bypassed.
- Authority audit now reports **77 bound / 106 unbound / 183 total**.
  Continue the remaining phase work; no overall completion is claimed.

### 2026-09-24 — Problem-shape observation authority binding

- Bound structural problem-shape observation to its existing native decode and
  growth rules, with typed provenance. Python remains structural ingress.
- `.venv` focused verification: **3 passed, 5 deselected in 18.33s**;
  `git diff --check` passed.
- Authority audit now reports **78 bound / 105 unbound / 183 total**.
  Continue the remaining phase work; no overall completion is claimed.

### 2026-09-24 — Meta-shape observation authority binding

- Bound meta-shape observation to the existing native recurrence/growth rules
  with typed provenance. Python remains signature ingress.
- `.venv` focused verification: **14 passed in 0.83s**; `git diff --check`
  passed.
- Authority audit now reports **79 bound / 104 unbound / 183 total**.
  Continue the remaining phase work; no overall completion is claimed.

### 2026-09-24 — Rule-dispute settlement authority binding

- Bound the integrated dispute/self-worth/emotion pipeline to its existing
  native rules with typed provenance; no surface conversational shortcut was
  introduced.
- `.venv` focused verification: **2 passed in 0.23s**; `git diff --check`
  passed.
- Authority audit now reports **80 bound / 103 unbound / 183 total**.
  Continue the remaining phase work; no overall completion is claimed.

### 2026-09-24 — Equation isolation authority binding

- Bound equation isolation to its existing native rewrite rules with typed
  provenance. Python remains equation construction/readback.
- `.venv` focused verification: **4 passed in 0.22s**; `git diff --check`
  passed.
- Authority audit now reports **81 bound / 102 unbound / 183 total**.
  Continue the remaining phase work; no overall completion is claimed.

### 2026-09-24 — Spatial-belief observation authority binding

- Bound spatial-belief observation ingestion to its existing native rules with
  typed provenance; no communication-layer shortcut was introduced.
- Doom integration verification was unavailable because optional `vizdoom` is
  missing, and the selected per-area suite had no matching spatial test.
- Authority audit now reports **82 bound / 101 unbound / 183 total**.
  Continue the remaining phase work; no overall completion is claimed.

### 2026-09-24 — Disposition trait settlement authority binding

- Bound trait relaxation, live pull, and crystallization to native disposition
  dynamics with typed provenance. No conversational surface workaround was
  added.
- `.venv` focused verification: **5 passed, 25 deselected in 0.59s**;
  `git diff --check` passed.
- Authority audit now reports **85 bound / 98 unbound / 183 total**.
  Continue the remaining phase work; no overall completion is claimed.

### 2026-09-24 — Frame-weight settlement authority binding

- Bound quantum and pooled frame-weight updates to existing native rules with
  typed provenance; no language or conversational shortcut was introduced.
- `.venv` focused verification: **3 passed, 12 deselected in 0.41s**;
  `git diff --check` passed.
- Authority audit now reports **87 bound / 96 unbound / 183 total**.
  Continue the remaining phase work; no overall completion is claimed.

### 2026-09-24 — Trait-modulator bridge authority binding

- Bound the trait/modulator bridge's initialization, bidirectional transfer,
  crystallization, and homeostatic paths to existing native rules with typed
  provenance. No surface-level conversation logic was introduced.
- `.venv` focused verification: **17 passed, 12 deselected in 1.52s**;
  `git diff --check` passed.
- Authority audit now reports **94 bound / 89 unbound / 183 total**.
  Continue the remaining phase work; no overall completion is claimed.

### 2026-09-24 — Self-worth CAN bridge authority binding

- Bound self-worth resident, incident, domain-projection, consequence, and
  peer-comparison paths to existing native CAN rules with typed provenance.
- Corrected receipt placement after a dirty-tracking regression: receipts now
  enter before the fixpoint, preserving the tested no-op behavior.
- `.venv` focused verification: **26 passed in 0.61s**; `git diff --check`
  passed.
- Authority audit now reports **101 bound / 82 unbound / 183 total**.
  Continue the remaining phase work; no overall completion is claimed.

### 2026-09-24 — Native reading-rule validation binding

- Bound all seven `read_method_draft.validate_by_running` native execution
  passes with provenance. Python remains validation harness mechanics.
- The related code-growth test remains red at upstream faculty routing before
  validation is reached (`no attached world/faculty`); no bypass was used.
- Authority audit now reports **108 bound / 75 unbound / 183 total**.
  Continue the remaining phase work; no overall completion is claimed.

### 2026-09-24 — Hate-attribution authority binding

- Bound understanding and hate-incident native settlement passes with typed
  provenance, preserving fixpoint cleanliness.
- `.venv` focused verification: **19 passed in 0.62s**; `git diff --check`
  passed.
- Authority audit now reports **111 bound / 72 unbound / 183 total**.
  Continue the remaining phase work; no overall completion is claimed.

### 2026-09-24 — Spatial-sense authority binding

- Bound quanta flood and spatial navigation settlement to existing native
  rules, preserving convergence scheduling and graph-owned action selection.
- `.venv` focused verification: **8 passed in 0.32s**; compilation and
  `git diff --check` passed.
- Authority audit now reports **117 bound / 66 unbound / 183 total**.
  Continue the remaining phase work; no overall completion is claimed.

### 2026-09-24 — Ink-decoding authority binding

- Bound ink lattice, refinement, and writer settlement to existing native
  rules with typed provenance; the no-Python-selection invariant remains
  intact.
- `.venv` focused verification: **5 passed, 29 deselected in 0.54s**;
  compilation and `git diff --check` passed.
- Authority audit now reports **121 bound / 62 unbound / 183 total**.
  Continue the remaining phase work; no overall completion is claimed.

### 2026-09-24 — Program-synthesis authority binding

- Bound program order-lattice decoding and synthesis pumping to existing native
  rules with typed provenance; Python remains dispatch/readback.
- `.venv` focused verification: **3 passed in 0.32s**; `git diff --check`
  passed.
- Authority audit now reports **125 bound / 58 unbound / 183 total**.
  Continue the remaining phase work; no overall completion is claimed.

### 2026-09-24 — Two-eye super-resolution authority binding

- Bound retinal sampling and fusion to existing native task/rule execution with
  typed provenance; no communication-layer behavior was added.
- `.venv` focused verification: **13 passed, 4 deselected in 0.65s**;
  `git diff --check` passed.
- Authority audit now reports **129 bound / 54 unbound / 183 total**.
  Continue the remaining phase work; no overall completion is claimed.

### 2026-09-24 — Affect/social evidence authority binding

- Bound trust, self-efficacy, shared arousal, and envy evidence settlement to
  existing native rules with typed provenance.
- `.venv` focused verification: **30 passed in 0.74s**; `git diff --check`
  passed.
- Authority audit now reports **134 bound / 49 unbound / 183 total**.
  Continue the remaining phase work; no overall completion is claimed.

### 2026-09-24 — Sensory-selection authority binding

- Bound sensory kernel/discrimination, feature cue selection, and modality
  training to existing native rules with typed provenance.
- `.venv` focused verification: **2 passed in 0.77s**; compilation and
  `git diff --check` passed.
- Authority audit now reports **138 bound / 45 unbound / 183 total**.
  Continue the remaining phase work; no overall completion is claimed.

### 2026-09-24 — 2-D vision task authority binding

- Bound 2-D retinal sampling and vision convolution task execution to existing
  native task/rule paths with typed provenance.
- `.venv` focused verification: **9 passed in 0.45s**; broader vision tests
  remain dependency-limited because `cv2` is unavailable.
- Authority audit now reports **141 bound / 42 unbound / 183 total**.
  Continue the remaining phase work; no overall completion is claimed.

### 2026-09-24 — World-adapter photon authority binding

- Bound both photon-sheet native task/rule passes to existing native execution
  with typed provenance; Python remains sensor ingress/readback.
- Compilation and `git diff --check` passed. Interactive verification remains
  unavailable because optional `vizdoom` is missing.
- Authority audit now reports **145 bound / 38 unbound / 183 total**.
  Continue the remaining phase work; no overall completion is claimed.

### 2026-09-24 — Program-chunk growth authority binding

- Bound program-chunk native fixpoint pumping to existing rules with typed
  provenance.
- `.venv` focused verification: **1 passed, 10 deselected in 0.27s**;
  compilation and `git diff --check` passed.
- Authority audit now reports **147 bound / 36 unbound / 183 total**.
  Continue the remaining phase work; no overall completion is claimed.

### 2026-09-24 — Grounding and appraisal guard authority binding

- Bound whisper grounding, trait-anxiety classification, Enigma admissibility,
  and salience ticking to existing native execution with typed/auditable
  boundaries.
- Salience receipt mutation was removed after it altered existing behavior;
  the native delegation remains. Its tale-agency test is still a baseline
  failure. Whisper/trait/Enigma focused tests produced **25 passes**; the
  native-binary MD5 discipline check remains red.
- Authority audit now reports **151 bound / 32 unbound / 183 total**.
  Continue the remaining phase work; no overall completion is claimed.

### 2026-09-24 — Lifted-rule and extension authority binding

- Bound lifted-rule fixpoint execution and substrate-extension verification to
  native boundaries, retaining delegation-only behavior where receipts altered
  existing verifier semantics.
- Substrate-extension suite produced **16 passes and 3 baseline failures**;
  teacher-dispatch verification is unavailable because `requests` is missing.
- Authority audit now reports **153 bound / 30 unbound / 183 total**.
  Continue the remaining phase work; no overall completion is claimed.

### 2026-09-24 — World identity/enactment authority binding

- Bound control enactment, cross-frame identity, identity-seam growth, and
  verdict comparison to existing native rules with typed provenance.
- Cross-frame `.venv` verification: **12 passed, 5 skipped in 1.24s**;
  identity-seam collection remains blocked by the stale-engine guard.
- Authority audit now reports **157 bound / 26 unbound / 183 total**.
  Continue the remaining phase work; no overall completion is claimed.

### 2026-09-24 — Affective world-model authority binding

- Bound frustration observation, mood stepping, and harvest/spite settlement to
  existing native rules with typed provenance.
- Focused `.venv` verification completed successfully; `git diff --check`
  passed.
- Authority audit now reports **160 bound / 23 unbound / 183 total**.
  Continue the remaining phase work; no overall completion is claimed.

### 2026-09-24 — World-discovery authority binding

- Bound falling-order, Galileo fall, push-mass, and physics/lever settlement to
  existing native rules with typed provenance.
- Physics/Galileo `.venv` verification: **11 passed in 1.16s**; falling/mass
  verification remains blocked by the stale-engine guard.
- Authority audit now reports **165 bound / 18 unbound / 183 total**.
  Continue the remaining phase work; no overall completion is claimed.

### 2026-09-24 — Perception/world-model authority binding

- Bound Achieve, agnosia, allocentric view, Bigville disposition/register, and
  Marshmallow delay native fixpoint paths with typed provenance.
- Focused `.venv` verification: Bigville disposition **8 passed**, Bigville
  register **10 passed**, allocentric view **19 passed**, and Marshmallow **7
  behavioral passes**. The native-binary canonical-hash checks remain red for
  the Marshmallow and spite suites; this is an artifact/provenance blocker,
  not a conversational behavior result.
- Authority audit now reports **171 bound / 12 unbound / 183 total**. The
  remaining findings are Doom paths, Harvest world, and invariant comparator;
  continue with explicit dependency/stale-engine handling and no completion
  claim yet.

### 2026-09-24 — Complete native authority census

- Classified the remaining Harvest, invariant-comparator, and Doom native
  cycle calls as explicit delegation/readback boundaries; Python does not
  select their cognitive outcomes.
- Focused `.venv` verification: Harvest **6 behavioral passes**, invariant
  comparator **22 passed / 4 skipped**, Doom allocentric **9 passed / 1
  skipped**, dual-process **10 passed**, predictive priors **9 passed / 1
  skipped**, and operate/texture **16 passed**. Known native-binary artifact
  discipline checks remain red in Harvest/Doom emotion suites.
- Authority audit now reports **183 bound / 0 unbound / 183 total** with
  status `clean`. This closes the static authority-inventory gate only; no
  overall phase or project completion is claimed.

### 2026-09-24 — Existing-faculty comprehension routing correction

- Routed the already-selected `satisfiable` and `honest_no_world` comprehension
  dispatch paths through their existing conversation-action faculties. The
  satisfiable self-report result now retains its graph-minted goal so the
  production bridge can release the selected answer; no new cognition or
  surface-only exception was added.
- Replaced the stale `noted` assertion with the mandated explicit diagnostic
  error for the still-unresolved plain statement case.
- `.venv`: `tests/test_comprehension_robustness.py` **9 passed**;
  `tests/test_conversation_loop.py`,
  `tests/test_utterance_conversation_unification.py`,
  `tests/test_output_null_gate.py`, and
  `tests/test_phase6a_production_gate.py` **33 passed**. The handoff's named
  `tests/test_phase6_production_gate.py` is absent from this checkout and was
  not counted as run.
- Phase 4 complete-tuple generation, Phase 7 resource envelope, and Phase 8H
  human-reference gates remain open; this routing correction does not close
  them.

### 2026-09-24 — Phase 7P cold comprehension stage attribution

- Split the kind bridge profile by stage. Cold `kind_signals` measured
  **1,607.6 ms / 66,531,328 bytes**; warm `kind_signals` measured **0.37 ms / 0
  bytes**. Native selective rule export measured **0.28 ms / 0 bytes**, and
  isolated native scratch-rule classification measured **0.70 ms / 397,312
  bytes**.
- The first `WordNet.synsets` lookup measured **1,635.7 ms / 61,702,144
  bytes**, identifying the lazy reference load as the main cold parser
  allocation. The selective native readback is not the remaining multi-second
  cost.
- One diagnostic warm-up moved **1,552.5 ms / 53,657,600 bytes** into boot.
  The first information-question event still took **13,289.3 ms**, added
  **46,931,968 bytes**, and materialized **11,172 graph edges**. No default
  warm-up was added because the full-replay and total boot-plus-event budget
  remains unmeasured.
- This refines Phase 7 attribution only; the resource exit remains open.

### 2026-09-24 — Stream seed manifests during boot

- `load_all_seeds()` now reads compact seed identity/dependency metadata to
  compute the same topological order, then reads each full manifest as it is
  installed. Generated overrides and `self_load_only` behavior are preserved.
- Full-corpus equivalence check: **734/734** seed IDs, dependency metadata,
  and topological order match the former full-manifest reader. Boot loaded
  **723 seeds** and yielded **24,750 nodes / 11,088 edges**.
- Instrumented full-boot RSS growth decreased from **1,549,680,640** to
  **1,457,979,392 bytes** (about **91.7 MB**). Indexing used **38,842,368
  bytes** versus **637,952,000 bytes** while parsing and retaining every full
  manifest. Boot time was **17.89 s** in this run, about **1.16 s** above the
  prior instrumented boot; native seed/rule installation remains the larger
  allocation and Phase 7 remains open.
- Verification: seed-loader **4 passed**, comprehension and conversation
  loops **21 passed**, and Phase 7 envelope **4 passed**. The envelope now
  reports boot RSS and total boot-plus-event growth, with opt-in WordNet
  prewarm measurement; no production warm-up was enabled.

### 2026-09-24 — Seed connectivity pre-pass

- Extended the compact boot index with category, microtheory, capability,
  declared node-type, named-content, and grouping keys. The map remains in
  memory through boot while full manifests are streamed; load behavior is
  unchanged.
- Inventory: **734 loadable seeds**, **515 explicit dependency edges**,
  **23 missing dependency references**, and **95 `self_load_only` manifests**.
  Dependency-only weak components give **344 groups**, including one
  **269-seed** component; connected components therefore cannot be treated as
  topic load groups. Explicit typed content links are needed before the map can
  safely select lazy loads.
- Full-corpus dependency metadata and topological ordering remain equivalent;
  seed-loader tests: **4 passed**. Selective loading is not enabled. Next:
  identify content providers/reference links and an invariant conversational
  core, then test lazy selection against full-boot graph/cognition equivalence.
- Added a non-production selector to the cached index: exact seed IDs,
  group-key matches, and exact declared content-key providers expand through
  `depends_on` and return in topo order; unresolved IDs/keys are reported.
  Corpus inventory finds **16,122 content keys** (15,538 with one provider,
  584 ambiguous) and **485 grouping keys** across 432 seeds. Ambiguous content
  resolves conservatively to every provider. Focused seed-loader tests remain
  **4 passed**; no production load policy changed.
- Tightened the selector's completeness report: the pre-pass records absent
  dependency IDs and selection results list missing dependencies inside the
  chosen closure. The full corpus has **23** such references, which the legacy
  full-boot topo loader skips; selective loading now makes them visible for
  audit instead of silently implying closure completeness. Seed-loader suite
  passed after the change: **4 passed**.

### 2026-09-24 — Resolve seed content connections in the pre-pass

- Extended the map across both native typed manifest edges and the legacy
  name-based `relations`/parent links that `load_all_seeds()` resolves after
  installation. Typed edge providers become load-before constraints; named
  relation endpoints expand the selected closure but do not reorder the
  post-load relation pass. Current full-boot order remains unchanged.
- Corpus audit: **141 typed refs** and **420 name/parent refs**; **134** refs
  have multiple seed providers. They produce **207 distinct seed-provider
  links** across **137 seeds**, of which **7** are typed load-before links.
  There is **1 unresolved named endpoint** (`code_authoring`) in addition to
  the **23** unresolved `depends_on` entries. Current typed-ref shapes are
  supported exactly (type-only or string `name`/`id`); richer shapes are
  reported unresolved rather than guessed.
- A dependency-plus-content weak-component pass yields **232 groups**, but
  still has a **379-seed** largest component. Whole-component loading is too
  coarse. Anchor selection is more precise: selecting `conversation_reply`
  yields **6 seeds** with no unresolved links; this is a candidate seed
  closure, not yet proof that the whole conversational runtime can operate on
  that subset.
- Initial uncached pre-pass measurement: about **2.2 s / 66.7 MB** RSS growth;
  the ID/dependency-only index had measured about **38.8 MB**. Full-boot
  behavior remained unchanged while content connectivity was audited.

### 2026-09-24 — Candidate conversation profile and core-only arbitration

- Derived a diagnostic profile from the 17 frozen cognition seeds plus the
  current `WorldAdapter._ensure_comprehension_seeds()` faculties. Connection
  expansion selected **59 seeds** from **45 roots** with no unresolved
  dependency/content references.
- The initial profile omitted `communication_intent_arbitration`; on the
  eight-event Phase 7 trace this left the overlap event without the graph-owned
  `defer` disposition even though other route/error outcomes matched. Added
  that existing native faculty to the core-only on-demand comprehension path
  and added a regression that starts from `WorldAdapter()` without a full
  seed boot. The native `arbitrate_typed_overlap_fragment_as_defer` rule now
  produces the expected `defer`/`typed_overlap_partial_event` evidence.
- After the addition, all **8/8 stable structural observations** matched the
  full-seed run and neither run reported event exceptions. Candidate boot
  graph: **1,825 nodes / 1,301 edges** vs full boot **24,750 / 11,088**; the
  reduced graph is not itself proof of cognition equivalence beyond this
  corpus. The focused live bridge + conversation-loop suite passed: **20
  tests**.
- A fresh-process candidate run included the full-corpus pre-pass, selection,
  and the 8-event trace: **4.33 s boot**, **103,755,776 bytes boot RSS growth**,
  **184,586,240 bytes event growth**, and **288,342,016 bytes combined**.
  Boot alone narrowly fits the 100 MiB threshold; the combined envelope does
  not. Resource acceptance remains open, and the profile has not replaced full
  boot in production.

### 2026-09-24 — Persist and validate the seed connectivity map

- Added a per-user temporary cache for the derived index. Cache validity uses a
  SHA-256 digest over the ordered source paths and bytes for all **830** seed
  manifests (about **288 MB**), plus a schema version and payload digest. The
  hash streams files without retaining them; writes use a temporary file and
  atomic replacement. Any content edit invalidates the entry even if file size
  and timestamp are preserved. Cache write/read failures fall back to building
  the map, so this remains an optimization only.
- Cache correctness test: repeated read reuses the map; a same-size manifest
  ID edit with its original mtime restored invalidates and rebuilds it. Seed
  loader suite: **5 passed**.
- Full-map cache miss: **2,305 ms / 69,672,960 bytes** RSS growth; serialized
  cache **749,322 bytes**. Warm lookup: **207 ms** in this environment. A
  fresh-process 8-event selected-profile run using the warm full-corpus cache
  booted in **2.53 s**, with **89,554,944 bytes boot RSS growth**. Events added
  **195,031,040 bytes**, for **284,585,984 bytes combined**: faster and lower
  boot RSS, but still over the 100 MiB boot-plus-event gate. Full boot remains
  the production default.

### 2026-09-24 — Reattribute the core-only event RSS spike

- A fresh-process core-only reproduction measured `WorldAdapter()` at about
  **40.7 MB RSS** before the first kind-signal read. `_graph_kind_for()` took
  **1,731 ms** in `kind_signals()`; a complete one-event run grew RSS by
  **235.4 MB**. Its seed check took **26.7 ms / 221 KB**, native isolated
  kind-rule classification **0.4 ms / 397 KB**, and the second seed check had
  no measurable allocation.
- Instrumenting the inner signal path attributed about **200.9 MB / 1,802 ms**
  to `_recognise_regions()` called by `_strip_politeness()`. The cost was in
  `_is_dictionary_word()`'s calls to NLTK `wordnet.synsets()` (the first token
  alone added **165.7 MB / 1,738 ms**); the subsequent `parse_with_gaps()`
  added about **2.8 MB / 0.9 ms**. This explains why the earlier standalone
  `parse_with_gaps()` probe substantially under-measured the live path.
- Correction to the preceding provisional attribution: grouping the entire
  `_graph_kind_for()` frame made its RSS look like native kind-rule work. This
  finer trace shows native seed checks and rule classification are not the
  source of this reproduced spike. The dominant resource target is the cold
  dictionary-membership lookup in politeness recognition.
- Replaced only that boolean lookup with a temporary, digest-keyed SQLite
  index built from WordNet's lemma and exception files. Queries apply NLTK's
  own morphology substitutions and exception precedence; when the corpus or
  index is unavailable, the existing NLTK reader remains the fallback. A
  76-form direct comparison against `bool(wordnet.synsets(token))` had no
  mismatches; focused index/morphology tests passed **2/2**.
- With the index, a fresh core-only `kind_signals()` probe measured **160.6 ms
  / 35,749,888 bytes**, versus the preceding trace's **1,802 ms / 200,859,648
  bytes** for politeness recognition. A complete one-question core-only event
  added **92,983,296 bytes** and took **2,195 ms**. These are bounded probes,
  not the 59-seed 8-event production envelope; combined boot-plus-event and
  full replay resource acceptance remain open.
- Verification: new membership tests **2 passed**; recognition tests **11
  passed** with the existing AST audit deselected (it flags pre-existing
  `re` usage in `comprehend_text.py`). The broader speech-act/comprehension
  slice ran for **641 s** before interruption: **15 passed**, and the same
  three documented fixture/seed parity failures occurred (`Focus on...`,
  instruction content, and stale rule-count expectation). The full slice is
  not claimed green; native authority remains unchanged.

### 2026-09-24 — Reuse cached rule provenance and remeasure connected boot

- Extended the content-hashed pre-pass cache with the exact `rule name -> seed
  id` provenance map. The map covers native `rules` and graph `Rule` nodes,
  including `self_load_only` manifests, while generated manifests retain the
  loader's effective override semantics. A 830-manifest comparison against the
  former full scan matched exactly: **3,915 names**, no missing names or
  provider differences, identical SHA-256 map digest
  `822f07fe9a8fa69d281203a9c8808128382dd057f7504087f76b6c2481a62d55`.
- `domains.self_model` now reads that cached provenance map rather than
  reparsing every seed manifest. The cache payload digest covers the added
  map, and a focused regression clears the in-memory map before a cache hit to
  verify that it is restored from persisted data. Seed loader suite: **8
  passed**.
- Fresh-process connected profile (warm, source-validated cache): **45 roots
  -> 59 seeds**, no unresolved dependencies/content refs, **697 ms** selection
  and boot, **66,523,136 bytes boot RSS growth**; the eight Phase 7 events took
  **1,467 ms**, added **37,498,880 bytes**, and had no exceptions. Combined
  growth was **104,022,016 bytes (99.2 MiB)**, below the 100 MiB/104,857,600
  byte bound by about **0.8 MiB** in this run. This is a narrow pass, not a
  robust resource margin; the profile remains opt-in and full boot remains the
  production default. Structural full-boot parity previously measured 8/8
  stable observations; rerun parity/resource checks after any profile or
  cognition changes. The combined seed-loader, live-discourse-bridge, and
  conversation-loop regressions passed **28 tests in 312.75 s**; `git diff
  --check` was clean.

### 2026-09-24 — Attribute full-boot native installation growth

- A fresh full-corpus boot instrumented each native
  `load_seed_manifest()` call: **723** install calls, **24,750 nodes / 11,088
  edges**, and **1,441,230,848 bytes** total RSS growth. The largest single
  call was `embodied_motor_program`: **478,089,216 bytes** RSS growth for one
  68 MB source manifest containing 51 executable rules. Next largest calls
  were `embodied_adaptation` (**38,162,432 bytes**), `aerial_adaptation`
  (**33,320,960 bytes**), and `humanoid_adaptation` (**24,436,736 bytes**).
- The dominant install is an unrelated, heavy faculty for the tested
  conversation profile, which selects 59 seeds without it. This supports
  connection-based profile loading as the route to bounded conversational
  boot, but does not close the full-boot/runtime resource gate: native rule
  installation itself is the main allocation boundary and full boot remains
  over the declared envelope. Do not drop or split this seed globally without
  rule/graph equivalence evidence; profile-specific omission is only valid
  when the requested connected closure proves it unnecessary.
- Added the opt-in `load_conversation_seed_profile()` helper, centralizing the
  45 conversation/core anchors while leaving closure, grouping, completeness,
  and ordering to the cached index. Its regression confirms the expected
  59-seed complete closure excludes `embodied_motor_program`; seed-loader suite
  now passes **9 tests**. The helper requires an otherwise empty adapter and
  has not replaced general full boot.
- Made the Phase 7 production-envelope harness accept the conversation seed
  profile while retaining the full-corpus profile as its default, and added
  direct full-vs-connected structural observation/replay parity. The Phase 7
  profile plus self-organisation/introspection readers passed **28 tests in
  196.86 s**.
- The first parity run exposed a full `export_rules()` call in live Phase 4
  seed detection; it now uses native `export_rules_prefix("cm4a_")` with a
  compatibility fallback. The first-event profile allocation dropped from
  about **34 MiB** to about **25 MiB** after also extracting the exact
  graph-derived self-organisation reader into a light shared module, avoiding
  import of the unrelated reflective-faculty stack on that route. The
  audience-aware renderer and reply-intent monitor remain in place.
- Fresh harness replay after these changes: **728 ms boot**, **46,321,664
  bytes boot growth**, **1,474 ms event latency**, **77,340,672 bytes combined
  growth**, deterministic replay, **0 errors**, and all resource assertions
  true (about **26 MiB** below the 100 MiB combined bound). This is one
  candidate-profile measurement, not full boot: the separately instrumented
  full-corpus path still grows **1,441,230,848 bytes** and remains open.

### 2026-09-24 — Correct unsupported causal follow-up expectation

- `question_followup` keeps cognitive goal `learn` but now expects action
  `repair`: its replay can identify the prior gate topic, but contains no
  closure event or causal graph relation from which to learn why it closed.
  Added an annotation rationale and regression; no runtime rule or behavior
  changed. Phase 0/runtime-adjudication checks: **11 passed**.
- Fresh 74-event report:
  `evaluation/reports/phase8_corpus_report_20260924_phase6w_adjudicated.json`.
  This pre-correction report attributed `repair` to graph-resident goal
  lifecycle and counted **37** label-equality matches. The corrected report
  identifies interpretation-only authority; see the authority-scored entry
  below for valid counts. Its release is still error/withheld, so production repair remains incomplete. Phase 8 release
  remains blocked by unavailable human references and unmeasured
  memory/learning/cost dimensions. Latest grounding: precision **1.00**,
  recall **0.44**, F1 **0.611**.
### 2026-09-24 — Phase 6W authority-scored correction

- Corrected a second measurement boundary: Phase 8 had still scored inferred
  state labels as action/repair/calibration outcomes despite the adjudicator
  identifying missing disposition authority. Raw label matches remain visible
  diagnostically, while outcome matches require graph/native disposition
  readback; unauthorized rows are excluded from those metric denominators
  with authority coverage noted.
- The corrected adjudication of the authority-corrected run is **8**
  authoritative matches, **66** authority gaps, **0** graph-owned mismatches.
  This supersedes the earlier 37/37 split, which treated matching labels as
  validated before disposition authority was checked.
- Focused regression selection: **9 passed**. Fresh replacement report
  `evaluation/reports/phase8_corpus_report_20260924_phase6w_authority_scored.json`
  records disposition-grade authority for **8/74** observations and **29**
  matching labels without authority. Action is unavailable (0/9 eligible),
  repair unavailable (0/16 eligible), and calibration is 1.00 over 8/49
  authoritative cases. `question_followup` reads `repair` diagnostically but
  is not a disposition match. Release remains blocked. Earlier 37/37 report
  claims are superseded for outcome scoring.
- Source audit found native dispositions currently authored for typed
  overlap/fragment defer and explicit-failure error, but not ordinary
  instruction/ask-back action or repair. Next is a graph-evidence design for
  native action/repair settlement with negative controls; route labels, reply
  text, and evaluator inferences remain non-authoritative.

### 2026-09-24 — Phase 6X event-bound graph commitment readback

- `reply_turn_trace` now reports event-bound action Goals and the linked
  clarification first-pair-part (direct `responds_to`, expected response,
  clarification speech act). The evaluator recognizes only those graph
  commitments; unbound Goals and unlinked repair surfaces remain unauthorized.
- Focused checks passed: **4** metadata authority tests and **2** action/repair
  graph integration tests. Fresh Phase 8 report:
  `evaluation/reports/phase8_corpus_report_20260924_phase6x_graph_commitments.json`.
- Audit: **26/74** authoritative observations, **20** matches, **6**
  graph-owned mismatches, **48** authority gaps. Action **1.00** (n=5, 5/9
  authority coverage), repair **0.667** (n=9, 9/16), calibration **0.714**
  (n=21, 21/49). Six mismatches expose runtime behavior requiring
  investigation: `action_world_unknown`, `action_referent`,
  `blocked_reference`, `partial_stream`, `fragment_question`, and
  `defer_permission`. The comparative release gate remains blocked.

### 2026-09-24 — Phase 6Y native action/repair disposition correction

- Native rules now author repair from typed unresolved imperative dependencies
  and defer for typed uncertain non-turn continuation fragments. The English
  adapter emits neutral deferred-condition evidence for a temporal connector
  with a following typed predicate; negative control “Look after the child”
  does not defer. Native disposition now takes precedence over adapter-side
  blocked hints.
- Targeted checks: **7 passed** across native uncertainty, continuation, and
  disposition precedence; temporal evidence controls **3 passed**. Earlier
  event-bound action/repair integration checks passed **2/2**.
- Fresh 74-event report:
  `evaluation/reports/phase8_corpus_report_20260924_phase6y_native_action_repair.json`.
  Authority is **26/74** (48 gaps); runtime-state audit is **25 matches, 1
  graph-owned mismatch**. Action **1.00** (n=5; 5/9 authority coverage),
  repair **1.00** (n=9; 9/16), calibration **0.952** (n=21; 21/49). The one
  mismatch is `unavailable_world` (expected blocked, observed native repair).
  Release remains blocked; this closes only the in-progress Phase 6Y increment.

### 2026-09-24 — Phase 6Z native world/reference disposition split

- The English adapter distinguishes a missing perceptual scene from an
  unresolved locative referent: “behind you” carries typed missing-world
  support, while “over there” remains an unresolved deictic reference on the
  instruction path. Native arbitration assigns `blocked` and `repair`
  respectively; the generic uncertainty rule no longer overrides missing
  world support.
- Focused adapter/native checks passed **2/2**; full 74-event report:
  `evaluation/reports/phase8_corpus_report_20260924_phase6z_native_world_block.json`.
  Audit: **28 authoritative matches, 0 graph-owned mismatches, 46 authority
  gaps**. `unavailable_world` is native blocked and `blocked_reference` is
  native repair.
- Action **1.00** (n=5; coverage 5/9), repair **1.00** (n=9; 9/16), and
  calibration **1.00** (n=23; 23/49). Release remains blocked due to remaining
  authority coverage and other comparative/production gates.

### 2026-09-24 — Phase 6Z routing regression verification and answer/learn audit

- Resumed from the Phase 6Z report without changing cognition/evaluation code.
  The pending comprehension routing/failure-surface regression suite passes:
  `tests/test_comprehension_robustness.py` **9 passed**.
- The available production/integration slice passes **32 tests** across
  conversation loop, utterance unification, output-null, and Phase 6A
  production gates. The older handoff names a missing
  `test_phase6_production_gate.py`; reran the extant equivalent slice instead.
- Answer/learning audit is still open: the 12 answer gaps include social acts,
  grounded topic answers, and cases where an error/withheld surface is paired
  with a generic answer receipt; the four learning cases do not expose an
  event-bound graph learning settlement in the current report trace. Receipt
  semantics and reply text remain insufficient to promote any of these to
  disposition authority. No authority/scoring changes were made; the Phase 8
  report remains the Phase 6Z baseline at 28/74 authoritative matches, release
  blocked.

### 2026-09-24 — Phase 6Z answer commitment evidence and guarded replay

- Added graph-readback evidence for event-bound supported topic answers (Goal,
  agent-held `HeldAnswer`, and linked supported `TopicGroundingEvidence`) and
  directly linked graph answer Messages on compatible responses. The readback
  rejects absent causal support and unresolved grounding; production receipts
  and reply text alone never authorize disposition. Learning still requires an
  explicit graph settlement, not just a learning-intent label.
- Verification: authority metadata positive/negative controls **2 passed**;
  supported held-answer graph test **1 passed**; unresolved `question_weather`
  single-event control remained unauthorized. The comprehension robustness
  suite passed **9/9**, and the available conversation/production slice passed
  **32/32**. `git diff --check`, Python compilation, and seed JSON validation
  pass.
- Fresh full replay:
  `evaluation/reports/phase8_corpus_report_20260924_phase6zc_interpretation_grounding_guard.json`
  (SHA256 `77e2a2d8d5877f09670ce4ee08dfeb5f219e34f8d67ef368f6dc4bfde04220e6`).
  Of 74 events, **34** have disposition authority: **33 matches**, **1
  graph-owned mismatch**, and **10** matching labels remain unauthorized. The
  40 authority gaps are defer 14, answer 7, repair 7, act 4, blocked 3, error
  2, learn 3. Answer coverage is 5/12. Learning coverage is 1/4; `info_explanation`
  is a true mismatch (the graph commits to answer while the annotation expects
  learn). Phase 8 remains blocked at provenance; human references are
  unavailable, and resource/cognition exit gates remain open.

### 2026-09-24 — Phase 6ZD diagnostic error is not a semantic release

- Hardened `production_gate.release_if_gated()` so the canonical explicit
  diagnostic error cannot be recorded as a successful semantic release.
  `tests/test_phase6a_production_gate.py`: **13 passed**.
- Refreshed 74-event report:
  `evaluation/reports/phase8_corpus_report_20260924_phase6zd_error_surface_gate.json`
  (SHA256 `915cfedba34b4e9687080f2f6d577558570cabbfe23e29a713ec4fba4ceeb711`).
  Both `info_explanation` and `question_weather` still surface the explicit
  diagnostic error, but their `answer_question` production receipts are now
  withheld with `diagnostic_error_surface_not_a_release`. Runtime disposition
  evidence is unchanged: **34/74 authoritative**, **33 matches**, one genuine
  graph-owned mismatch (`info_explanation` expected learn, graph-selected
  answer), **10** label matches without authority. Release remains blocked at
  provenance with the human references unavailable.

### 2026-09-24 — Phase 6ZE native repair for unsupported causal questions

- Graph interpretation now carries `relation_support` derived from typed
  `relation_focus` and the existing causal graph. Native arbitration chooses
  `repair` for a reason-focused information request with no causal path.
  Answer commitment/readback and answer release use the same support check for
  explicit and anaphoric reason queries.
- Negative/positive graph integration test:
  `test_explicit_reason_question_requires_a_graph_causal_relation` passes.
  No causal edge yields native `repair` with no answer commitment; an existing
  causal edge is accepted. Combined action-evidence and Phase 6A production
  suites: **26 passed**.
- Fresh full report:
  `evaluation/reports/phase8_corpus_report_20260924_phase6ze_native_causal_repair.json`
  (SHA256 `f09e14fd66da4269aa7bea8c86d05501688639902f3f41d674d481d5b145f264`).
  **35/74** observations are authoritative: **34 matches**, **1 graph-owned
  mismatch**, **9** label matches without authority, and **39** authority gaps.
  `question_followup` now has native repair authority and matches; `info_explanation`
  has native repair authority against its expected learn state, pending
  independent state-contract adjudication. Authority-backed action, repair,
  and calibration scores are **1.00** with coverage 5/9, 10/16, and 24/49.
  Comparative release remains blocked at provenance; resource and cognition
  gates remain open.

### 2026-09-25 — Native non-turn defer gates outbound release

- A focused current-source Phase 8 run found `partial_stream` was assigned a
  native `defer` disposition but still received an ask-back surface from the
  action faculty. The live bridge now returns no outbound reply for a
  graph-selected `defer` on a typed `interaction_mode=non_turn`,
  `literal_form=fragment` event, while preserving event binding and the
  cognition trace. Turn-compatible overlap keeps its existing explicit-error
  behavior.
- Current-source Phase 8 single-event replay now records `partial_stream` as
  native-authoritative `defer` with `release_status=unavailable` and empty
  reply. Partial-event plus explicit-uncertainty tests: **8 passed**; adjacent
  conversation/unification/output-null/Phase 6A production slice: **33
  passed**. The checked-in prior 74-event report predates this change and is
  not evidence for the updated release boundary; full replay remains required.
- The connected seed pre-pass/cache contract was independently revalidated:
  **7 focused boot/profile tests passed**. Overall Phase 6 cognition,
  production, Phase 7 resource, and Phase 8H comparative gates remain open.

### 2026-09-25 — Phase 8 full replay after non-turn defer release

- Fresh 74-event report:
  `evaluation/reports/phase8_corpus_report_20260925_phase6zf_nonturn_defer_release.json`
  (SHA256 `d11461f8dcb721e57b226bfc324f2aa72488d80bad239fab95692ebd3134d308`).
  It confirms `partial_stream` is native-authoritative `defer` with no release.
- The no-reply semantics correctly change downstream discourse: turns that
  previously received spurious ask-back/error surfaces no longer inject those
  surfaces into subsequent events. This replay has **34/74 authoritative
  dispositions**, **32 authoritative matches**, **2 authoritative mismatches**,
  and **9** label matches without authority; compared with the prior 6ZE replay
  (35/74, 34 matches, one mismatch), authority/match totals decreased. The new
  mismatch `action_world_unknown` is graph-bound as `act` although the corpus
  expects repair; `question_ack` lost its prior answer authority in the
  changed discourse sequence. These are real remaining cognition issues, not
  grounds to restore forced replies to typed non-turn events.
- Phase 8 remains blocked at comparative provenance (human reference data
  unavailable); cognition, production, resource, and comparative acceptance
  gates remain open. This increment does not close any release gate.

### 2026-09-25 — Phase 6ZH repair disposition controls action release

- The 6ZG replay showed that native arbitration selected `repair` for
  “Activate the unknown console” but the imperative bridge still committed an
  event-bound action goal. The bridge now routes a native repair disposition
  through the existing clarification faculty before the generic action
  faculty. It does not infer uncertainty from surface wording.
- Fresh full replay:
  `evaluation/reports/phase8_corpus_report_20260925_phase6zh_repair_release_alignment.json`
  (SHA256 `ff23cbc085019a649959f07144b93cd56d9cca49d5d5280541871f3d8effd13e3`).
  `action_world_unknown` is now native-authoritative repair with an ask-back
  and matches its expected state. Whole-corpus coverage is **36/74
  authoritative**, **34 matches**, **2 mismatches**, and **9** label matches
  without authority. Remaining authoritative mismatches are `info_explanation`
  (repair vs learn) and `response_no` (repair vs defer). The gate remains
  blocked at provenance; no cognition, resource, production, or comparative
  exit criterion is claimed closed.
- The typed-gap/arbitration and partial-event controls passed **9 tests**;
  the focused repair-release plus unresolved-anaphora controls passed **3**.

### 2026-09-25 — Audit of the two remaining authoritative corpus mismatches

- Reviewed the fixed-corpus and Phase 8 contracts before changing either the
  graph policy or the reference labels. `response_no` is annotated
  `literal_form=imperative`, `communicative_force=refusal`,
  `interaction_relation=response`, and `expected_state=defer`, but Phase 8
  injects `instruction` from literal form; the live parse then reads
  `do:No(hold)` and routes to repair. The event does not currently provide a
  typed refusal/countermand semantic record or a bound preceding-action
  reference from which native cognition could distinguish refusal from an
  action request.
- `info_explanation` is annotated partially grounded because `alarm` resolves,
  but its requested cause has no graph path. The native repair is supported by
  the available evidence; the expected `learn` state is not justified by an
  event-bound causal source or user-supplied explanation. Neither mismatch is
  safe to “fix” by forcing the current label into graph disposition.
- The Phase 0 contract calls its labels independent but does not specify
  case-level adjudication rules; the Phase 8A plan explicitly calls for those
  rules and repeated baseline observations. Keep both as open reference/
  evidence-contract cases pending independent adjudication; do not count
  label changes as cognition improvement. The 6ZH full replay remains the
  measured runtime report.

### 2026-09-25 — Content-connected profile parity and current resource sample

- The source-validated seed pre-pass accepts upstream content keys, resolves
  all matching providers plus their typed/content dependencies, and loads the
  selected group before event processing. A fresh deterministic 8-event
  full-vs-connected report using 17 keys from the cached content index is
  structurally equal **8/8**, with a complete **72-seed** closure, zero errors,
  and no semantic use of reply text:
  `evaluation/reports/phase7_seed_profile_parity_20260925_connected_content_closure8.json`
  (SHA256 `666be21a67ad1bc197366fce36d656dd0d760956e0cc46199766e94c2c9a4403`).
  The focused content-closure/event-time-load tests pass **3/3**; the boot/cache
  selection checks earlier in this turn pass **7/7**. This verifies the
  connected pre-pass/cache for the named bounded workload, not all content.
- Fresh replay of the same 8-event conversation profile is deterministic and
  error-free, with max turn latency **70.21 ms**, peak RSS **86,712,320 bytes**,
  boot+event RSS growth **60,833,792 bytes**, and all resource assertions true:
  `evaluation/reports/phase7_profile_resource_20260925_phase6zh_conversation.json`
  (SHA256 `3ffba007b176738d28168d66a90cccd4e1d084f44f7342e568a0fe54acaad745`).
  Social/action reflex samples are <50 ms; the slowest question sample is under
  the 150 ms deliberation bound. This closes only the named profile's current
  resource sample.
- An all-74 static-anchor comparison without content keys matched only **6/74**;
  that broader diagnostic is not the named production profile and confirms
  that the bounded connected profile must not be advertised as full-corpus
  seed parity. Broad 74-event cost, cognition, production, and comparative
  gates remain open.
- A raw-token content pre-pass across all 74 events was also audited without
  mutating graph state: 98 exact content keys would select 107 seeds, but the
  closure is incomplete because the ordinary token `signal` selects
  `operating_systems`, whose declared chain reaches
  `compiler_theory -> llvm_passes -> llvm_ir` (missing). This is why
  event-content keys must come from a semantic/upstream candidate producer and
  be resolved through the cached dependency/group map, rather than treating
  every surface token as a seed request. The pre-pass fails closed before
  loading an incomplete closure.

### 2026-09-25 — Production-gate and comparative-scaffold verification

- Re-ran the canonical deliberation→monitored commitment, output-null, and
  grammar-inversion battery: **6 passed**. This verifies native settlement
  precedes a monitor-cleared commit on an explicitly complete evidence tuple;
  it does not supply live complete tuples in the fixed 74-event replay, whose
  Phase 4 audit still reports zero complete tuples/promotions.
- Re-ran `tests/test_phase8a_comparative_release_gate.py`: **7 passed**. The
  gate correctly remains blocked when human/model scorecards are unavailable;
  scaffold correctness is not comparative evidence. No human reference
  observations or full live-cognition evidence were added in this increment.

### 2026-09-25 — Phase 1 speech-act parity recheck

- Fresh `.venv/bin/pytest -q tests/test_speech_act_parity_migrated.py` run:
  **4 passed, 2 failed** in 54.43s. Scratch rule parity, corpus breadth,
  manifest round-trip, and related controls pass; exact live-path parity and
  frozen parser-signal parity do not.
- Live mismatches cover eight utterance cases: four typed action-target
  differences (`look left`, `move north`, indirect account requests, and
  compound instruction), the current verb parse of `Focus on the reading
  work.`, the target extraction in `Promote the first concern.`, and
  missing-world routing for `What is in the image?`. One parser signal differs
  for the Focus example. These outcomes intersect newer typed grounding and
  action-target behavior, so the old snapshot alone cannot determine which
  side is correct.
- No runtime or fixture change was made. Keep Phase 1 open for case-level
  adjudication; do not restore old parser outcomes or update the frozen
  expected values solely to make parity green.

### 2026-09-25 — Phase 7 asynchronous retrieval boundary recheck

- Fresh daemon lifecycle regressions for requested SearchRequest, GroundRequest,
  and DetailRequest work pass **5/5**. They verify workers consume request
  snapshots without holding `AGENT_LOCK`, pending work is resumed and committed
  by the graph owner, specific grounding supersedes the generic search on
  success, failed specific grounding releases the generic fallback, and
  interrupted work is requeued after restart. Agent-authored keep-alive and
  bounded same-origin concurrency checks pass **2/2**.
- This verifies the daemon path only. `WorldAdapter.converse()` and the Phase 8
  direct evaluator still fulfill remote work synchronously; no updated 74-event
  resource replay was run here. The direct-path turn-latency and extended RSS
  gates remain open, and no Phase 7 exit is claimed.

### 2026-09-25 — State-local discourse event chronology

- `domains.discourse_state.record_event()` now links each `DiscourseEvent` to
  its immediate predecessor within the same `DiscourseState` using
  `follows_event`, and keeps an indexed `last_event_id` projection. Recovery
  checks that the cached handle is still a `DiscourseEvent` belonging to that
  state; otherwise it resolves the predecessor from that state's existing
  indexed event history. No disposition or reply policy was added.
- Sequence/legacy-handle isolation tests: **2 passed**. After the handle guard,
  the Phase 8 runner tests plus these tests pass **24/24**; the live deliberation
  bridge plus Phase 0 contract plus sequence tests passed **20/20** before the
  guard's final hardening.
- Fresh full-corpus report:
  `evaluation/reports/phase8_corpus_report_20260925_phase3_predecessor_events.json`
  (SHA256 `260dc808c34985c458e85ff5daab9e42031535cae1ba411d97550e31023def45`).
  It records **74/74** observations and a deterministic Phase 4 audit; all
  scorecard metrics and every event's observed disposition/authority are
  identical to the Phase 6ZH baseline. Phase 4 still has **0** evidence sources
  and complete tuples; comparative release remains blocked for provenance.
- This was a semantic non-regression replay, not a resource pass: direct
  full-corpus runtime was **78.63 s**, and full replay RSS/latency criteria were
  not separately measured. Resource, cognition coverage, production, and
  human-reference gates remain open.

### 2026-09-25 — Phase 4S live held-path partial evidence projection

- The live Phase 4 bridge now reuses `self_dialogue.held_graph_frame_for_topic`
  only for an event-bound `answer_topic` goal. When the existing graph contains
  the returned `Concept -causal_influence-> Concept` path, the adapter records
  `grounding=1.0` as binary held-path presence, with source faculty, topic/fact
  node links, goal/event provenance, and an explicit path description. It is
  attached under `has_partial_evidence`, not any candidate-bearing relation;
  expected value, residual cost, consequence, and novelty remain absent.
- The synthetic live-path regression verifies the Phase 4 audit sees exactly
  that one grounding dimension while native deliberation remains
  `no_candidate`, with zero candidates/promotions. Partial-audit plus live
  bridge batteries pass **16/16**.
- Fresh 74-event report:
  `evaluation/reports/phase8_corpus_report_20260925_phase4s_held_path_reuse.json`
  (SHA256 `84c2c6cd1b694f0d975139a6c29936ccb1cdb20980d7f1a8b39ea7005fe51c8f`).
  All **74** event dispositions/authority flags and all scorecard metrics match
  the 6ZH replay; the audit remains deterministic with **0** observed event-
  linked source paths, **0** complete tuples, and **0** promotions. No current
  corpus answer-topic goal exposes this specific held `causal_influence` path,
  so the synthetic source is not counted as corpus coverage. Release remains
  blocked at provenance.
- Direct full-corpus wall time was **79.72 s**; RSS/latency were not separately
  measured. This projection does not close cognition coverage, resource,
  production, or comparative-human gates.

### 2026-09-25 — Connected seed prepass handoff status

- The requested non-lazy, connectivity-based loading direction is partly in
  place: the seed index/cache resolves typed content keys to providers and
  dependency closure before graph mutation, and selective loading can slice
  lexical content. The conversation profile still receives its content keys
  manually; an upstream, language-neutral producer for those candidate keys is
  not implemented.
- Do not derive keys from every raw input token. The previous all-corpus probe
  selected unrelated providers (including `operating_systems` for `signal`)
  and failed dependency closure at `llvm_ir`. The remaining bounded work is to
  produce semantically typed candidate keys before the single initial load,
  then verify closure, profile parity, and resource effects. No such producer
  or new verification was completed in this continuation.
- Conversational work remains in progress: Phase 4 corpus evidence is still
  empty, comparative release is blocked at provenance, and cognition,
  production, and resource acceptance gates remain open. The engine-substrate
  plan pivot is therefore not yet due.
- A fresh eight-event connected-profile run with no manually supplied content
  keys completes without errors at 86,679,552 bytes RSS and 60,821,504 bytes
  boot-plus-event growth. Comparing its structural observations to the
  established 17-key connected-profile report shows differences on **6/8**
  events, including direct-action grounding and interpreted-instruction
  structure. Report:
  `evaluation/reports/phase7_profile_resource_20260925_conversation_no_content_keys.json`.
  Empty keys therefore do not preserve current profile behavior; semantic
  candidate production (or equivalent evidence-backed scoping) remains required.

### 2026-09-25 — Reuse validated seed map during boot-time self-modeling

- The connected-loader profile previously called the source-validating seed
  index a second time when `ensure_self_model()` built rule provenance. The
  loader now passes the already validated rule-name map through to that
  mechanical mirror. Standalone self-model refreshes still use the original
  source-validated lookup, and seed source hashing/cache invalidation behavior
  is unchanged.
- Added a regression that counts source-digest passes during boot; it verifies
  one pass, with the same validated map reused. Seed-loader and self-model
  focused suites pass **24/24**.
- Fresh 17-key connected-profile measurement:
  `evaluation/reports/phase7_profile_resource_20260925_conversation_validated_rule_index_17keys.json`.
  It replays deterministically with **70.89 ms** maximum event latency,
  **87,232,512 bytes** absolute RSS, and **469.2 ms** boot. Full-vs-connected
  structural parity remains **8/8** with no mismatches in
  `evaluation/reports/phase7_seed_profile_parity_20260925_validated_rule_index_17keys.json`.
  This is a bounded eight-event profile result, not a full-corpus resource
  pass; automatic semantic content-key production remains open.

### 2026-09-25 — Native disposition for complete social turns

- Full-corpus traces showed that five complete social events already released
  social production while native arbitration left them at `defer`; an explicit
  typed overlap fragment correctly used `defer`. Added a language-neutral
  native rule for `evidence_force=social_action` on `interaction_mode=
  turn_compatible`, excluding literal fragments. It selects `answer` and
  `coordinate_socially`; the dedicated overlap rule retains `defer` and
  `clarify_or_defer`.
- Controls for a complete semantic social event and overlap-fragment defer pass
  **2/2**. The fixed Phase 8 corpus replay is
  `evaluation/reports/phase8_corpus_report_20260925_phase6zj_turn_compatible_social.json`.
  Native disposition authority rose from **36/74** to **40/74**; authoritative
  label matches rose from **34** to **37**, while mismatches rose from **2**
  to **3**. The additional mismatch is `acknowledgement` (native answer vs
  reference defer): the current language adapter maps its social-form input to
  generic `social_action`, so its typed evidence cannot yet distinguish
  acknowledgment. Do not encode that reference label into runtime routing;
  keep the case open for adapter/evidence-contract adjudication.
- `info_explanation` and `response_no` remain graph-owned mismatches. Phase 4
  remains at zero complete tuples/promotions, and comparative release remains
  blocked at provenance. This increment does not close the cognition,
  production, resource, or comparative-evaluation gates.

### 2026-09-25 — Signal-derived speech-act input and typed acknowledgment/refusal

- The Phase 8 evaluator had mapped corpus `literal_form` directly to a runtime
  `speech_act`, making a reference parse annotation part of the SUT input. It
  now calls the same signal-boundary classifier as `WorldAdapter` ingress. A
  regression supplies deliberately contradictory `literal_form` values and
  verifies that only `signal` determines the speech-act input.
- The English adapter now emits neutral `acknowledgement` evidence for a
  standalone positive acknowledgment and `refusal` for a bare negative or a
  negative countermand followed by a recognized directive. A negative
  correction with non-imperative content remains a statement; this avoids the
  overbroad intermediate rule that had labeled `correction_uncertain` refusal.
  `communication_evidence.v1` carries both categories, and native rules own
  their `defer` dispositions. “Yes, proceed” remains an action request.
- Signal-boundary, neutral-force, native-rule, social-turn, and fragment
  controls pass (**4/4** after the countermand refinement; the preceding
  combined adapter/social set passed **5/5**). Fresh full Phase 8 replay:
  `evaluation/reports/phase8_corpus_report_20260925_phase6zn_countermand_refinement.json`.
  It contains **74/74** events, **38/74** disposition-authoritative observations,
  **37** authoritative label matches, **1** mismatch (`info_explanation`), and
  **8** label matches without authority. `acknowledgement` and `response_no`
  now have graph-native `defer`; “Yes, proceed” is graph-native `act`;
  `correction_uncertain` remains unauthoritative rather than being forced into
  a disposition. The evaluation release gate remains blocked at provenance,
  Phase 4 still has **0** complete tuples/promotions, and no resource pass is
  claimed.
- The previous 6ZJ full-corpus result is superseded: its runner used
  annotation-derived speech-act inputs. Keep that report as an audit trail,
  not as current acceptance evidence.

### 2026-09-25 — Held topic-answer paths enter Phase 4 reuse audit

- Live `answer_topic` goals now reuse supported `HeldAnswer` paths and their
  attached `TopicGroundingEvidence` as event/goal-bound partial grounding
  sources. They are not candidates, do not mint concepts, and do not authorize
  promotion; absent evidence still leaves native `no_candidate` intact.
- Focused live-bridge and partial-evidence audit tests pass **7/7**.
- Fresh 74-event replay:
  `evaluation/reports/phase8_corpus_report_20260925_phase4t_held_answer_grounding.json`.
  It records **5** grounding-only `topic_grounding` sources across
  `question_followup`, `question_response`, `question_ack`, `info_status`, and
  `overlap_offer`; there are **0** complete tuples, eligible promotions, or
  actual promotions. Expected value, residual cost, consequence, and novelty
  remain absent from every source. Deterministic readback holds.
- This advances partial-source reuse coverage only. It does not close the Phase
  4 upstream evidence, cognition, production, resource, or comparative-release
  gates.

### 2026-09-25 — Fresh 74-event connected-profile resource recheck

- Re-ran all **74** fixed corpus events under the connected conversation
  profile with the previously documented **17** content keys. The selection is
  complete (**72** seeds) and has **0** errors, but the wider sustained replay
  does not meet the bounded resource envelope: peak RSS **135,720,960 bytes**,
  conversation growth **109,563,904 bytes**, and maximum event latency
  **5,824.4 ms**. The absolute RSS and growth assertions fail. Report:
  `evaluation/reports/phase7_profile_resource_20260925_full74_connected_17keys_recheck.json`.
- The largest latency outlier is `overlap_offer` (**5,824 ms**), followed by
  `question_response` (**2,084 ms**). `question_unavailable` adds
  **28,844,032 bytes** while lazily importing the `pyarrow`/Wikipedia module
  stack and takes **1,895 ms**. The import is concrete attribution for that
  event; it does not explain the other latency outliers.
- Corrected Phase 7 status to distinguish the passing eight-event profile
  from the failing full-corpus replay. Corrected `--event-id` help: comparison
  mode defaults to the full corpus, but `--profile-run` defaults to its named
  eight-event slice, so a full-corpus profile run must supply all event IDs.
- Next work is to remove or schedule event-time external-source loading/I/O
  without bypassing graph/native routing, and separately profile graph-growth
  cost at `overlap_offer`/`question_response`. This recheck does not close the
  resource, cognition, production, or comparative-evaluation gates.
- Isolated fresh-process controls show the same three corpus records are not
  intrinsically slow: `overlap_offer` **42.1 ms / 69.5 MB peak**,
  `question_response` **39.3 ms / 70.1 MB**, and `question_unavailable`
  **66.7 ms / 81.6 MB**, each with one event and zero errors. The last case
  imported no new modules in isolation. The multi-second / 28.8 MB costs
  therefore arise from preceding conversational state and its selected live
  paths, not from the event labels alone. Controls:
  `evaluation/reports/phase7_profile_resource_20260925_isolated_overlap_offer.json`,
  `evaluation/reports/phase7_profile_resource_20260925_isolated_question_response.json`,
  and `evaluation/reports/phase7_profile_resource_20260925_isolated_question_unavailable.json`.
- Replayed the exact corpus prefix through event 14, including the `gate`
  HeldAnswer setup. Before `question_unavailable`, two graph-owned requests
  were still `requested`: `GroundRequest`/`SearchRequest` for `quorplezap the
  door` and `please—`. That turn then took **2,304.6 ms** and left those older
  requests `failed`/`done` with one retrieved answer. This confirms the
  dispatcher drains a graph-global backlog synchronously on a later turn;
  request completion time is being charged to whichever subsequent event
  happens to invoke it. The production daemon already has an async host-action
  queue for these request types, so integrate the direct conversation path
  with that queue (or measure the daemon ingress path) rather than attributing
  old-request I/O to current-event cognition.

### 2026-09-25 — Shared cognition evidence on daemon text ingress

- `ingest_turn()` previously wrote the inbound message and parse but omitted
  the `CommunicationInterpretation` and `DiscourseEvent` materialization used
  by `converse()`. Added one shared, mechanical boundary helper for both paths;
  it transports adapter-selected comprehension and explicit ingress metadata,
  while native rules still own disposition and lifecycle. The daemon text path
  does not receive Phase 0 reference force/goal/literal-form annotations.
- Added a signal-only native-arbitration regression for a non-turn overlap
  fragment. The focused control and daemon-ingress evaluation test pass **2/2**;
  the broader live-bridge and conversation-loop suites pass **25/25**.
- Added `evaluation/phase7_daemon_ingress_envelope.py` and measured the full
  corpus in the actual connected profile plus daemon scheduler quantum:
  `evaluation/reports/phase7_daemon_ingress_20260925_full74.json`. It records
  **74/74** interpretations, **10/74** dispositions, **34/74** replies ready,
  **40** turns still pending, **12** pending GroundRequests, and **15** pending
  SearchRequests. Maximum ingress latency is **33.55 ms**, maximum first
  native cycle **30.02 ms**, but peak RSS is **106,381,312 bytes** and exceeds
  the 100 MiB limit. Host-action dispatch and external I/O are intentionally
  excluded; this is not a complete production-loop or reply-release pass.
- A second independent process produced the identical canonical observation
  hash, `deda9e294f12cfa932f7abd72914db80153a811dbbc128cad8ff5bd1406ab330`,
  while measuring **106,360,832 bytes** RSS peak. The asynchronous ingress
  boundary is now observable and evidence-complete, but disposition/reply
  parity, host-action completion, absolute resource closure, and all other
  project acceptance gates remain open.
- Final handoff check: removed an unused report-local pending map and replaced
  dynamic `sys` lookup with a normal import; report counts and independent
  replay hash remain unchanged. The report runner compiles and the scoped
  `git diff --check` is clean. Exact next step: close daemon native disposition
  and reply-release gaps, then run host-action completion and resource checks;
  do not treat the ingress benchmark as a production pass.

### 2026-09-25 — Refusal force preserved under an imperative parse

- Interpretation construction now preserves typed refusal force even when
  comprehension selects an imperative/instruction parse; native rules still
  select disposition. The live refusal regression and language-neutral
  evidence suite passed **7/7**, and a fresh 74-event Phase 8 run increased
  native disposition authority from 36/74 to **38/74**. `response_no` now
  selects authoritative `defer`; its released surface remains the diagnostic
  error. The full report is
  `evaluation/reports/phase8_corpus_report_20260925_refusal_force_precedence.json`.
- One authoritative mismatch remains (`info_explanation`: expected `learn`,
  observed `repair`). Comparative release remains blocked at provenance; this
  increment does not close production, resource, or overall cognition gates.

### 2026-09-25 — Reason questions route missing causes to learning

- Changed the native rule for a non-anaphoric reason request with missing
  causal support from repair to `learn` / `answer_or_learn`; added a separate
  anaphoric-reason repair rule to prevent topic-name retrieval from being
  mistaken for a causal answer. Live tests pass **2/2**.
- The fresh full-corpus report
  `evaluation/reports/phase8_corpus_report_20260925_reason_request_learning_guarded.json`
  has **38/74** authoritative dispositions and **zero authoritative
  mismatches**. `info_explanation` selects native `learn`,
  `question_followup` native `repair`, and `response_no` native `defer`.
  Replies for all three remain the explicit error surface; the learn goal is
  not yet fulfilled by retrieval/release. Comparative provenance, remaining
  disposition coverage, production, resource, and overall acceptance remain
  open.

### 2026-09-25 — Audit existing retrieval against causal learning

- Confirmed the existing `GroundRequest` worker/commit contract is phrase
  grounding: the supported aspect is `made_of`, remote results are summaries,
  and owner commit writes a phrase `HeldAnswer`. It does not produce or verify
  a typed causal relation and cannot create the `causal_influence` evidence
  required by reason-answer release. Reusing it for native `learn` would risk
  treating topic relevance as causal support.
- The execution plan now marks the safe next seam as a dedicated
  language-neutral causal request/candidate pipeline with provenance,
  graph-free retrieval, owner-thread validation, and native relation
  verification. Unstructured retrieval must remain unresolved/error rather
  than authorize release. No acceptance gate is claimed closed.

### 2026-09-25 — Remove Wikipedia/parquet import from unavailable-grounding path

- Resource evidence showed `question_unavailable` imported `pyarrow` and the
  Wikipedia stack even though `/home/matt/ozma/data/wikipedia` was absent.
  Lookup subject normalization is now in lightweight `question_subject.py`;
  grammar/dictionary/trope/LLVM teachers use it without importing the wiki
  backend. `_ground_local` also waits to import `wiki_teacher` until an attached
  or available local teacher exists. A regression forbids both wiki imports
  for a missing snapshot.
- Grounding/fetch/wiki/dictionary/grammar verification: **82 passed, 2
  skipped**. Fresh full 74-event connected report
  `evaluation/reports/phase7_profile_resource_20260925_full74_lazy_wiki_recheck2.json`
  contains no pyarrow/wikipedia import on `question_unavailable`; peak RSS is
  **109,096,960 bytes** (down **26,624,000 bytes**), and boot/event growth is
  **82,894,848 bytes**. Absolute RSS remains over budget by **4,239,360 bytes**;
  worst latency remains **5,261 ms**. Phase 7 is not closed.

### 2026-09-25 — Record residual SearchRequest state in completed daemon profiles

- Both ordered full 74-event daemon-completion profiles
  (`phase7_daemon_completion_20260925_verified.json` and its replay) leave
  **7 SearchRequests** in `requested`, despite **0** pending host actions and
  **0** host-action I/O futures. Canonical chat-observation hashes match, but
  this does not establish that these requests are correctly terminal.
- The current profile records only the pending count, not request identities,
  source/goal provenance, or associated host-action history. No scheduler
  change is justified from that evidence alone. Leave this lifecycle question
  open for a provenance-instrumented follow-up; the broader cognition,
  production, resource, and comparative gates also remain open.

### 2026-09-25 — Resolve generic-search fallback after specific grounding miss

- Request-level diagnostics showed all seven residual `SearchRequest`s had a
  linked completed `search` host action, no search-I/O token, and no terminal
  evidence. The graph-selected generic action was being consumed by its
  higher-precedence specific-grounding attempt; the seed's mint-once guard then
  correctly prevented a second host action for the same request.
- Kept graph authority intact by having that already-selected `search` action
  carry out its generic fallback when same-query specific grounding honestly
  misses. Retrieval workers remain graph-free; owner-thread commits still
  validate request identity/token and native candidate verification still
  decides whether search evidence is supported. Added a seed-generated
  miss→fallback regression that failed before the fix and now passes.
- Focused daemon/retrieval controls: **7 passed**. Fresh full profile
  `evaluation/reports/phase7_daemon_completion_20260925_fallback_recheck.json`
  completed **53** topic-grounding HTTP calls and now has **0** requested
  SearchRequests / **0** requested GroundRequests (previously 7 / 0), **39**
  reply-ready turns, **35** pending turns, no host I/O backlog, and no drain
  timeout. Peak RSS is **110,223,360 bytes**; the <100 MiB gate remains open.
  This closes only the identified retrieval-lifecycle defect; cognition,
  production, latency/resource, comparative-human/provenance, and overall
  acceptance remain open.

### 2026-09-25 — Distinguish selected adjacency acts from completed replies

- Synchronous method-parity, deliberative-production, and grammar-inversion
  controls pass **8/8**; the separate full daemon profile still has only
  **39/74** text replies. Report v4
  `evaluation/reports/phase7_daemon_completion_20260925_reply_lifecycle_audit.json`
  shows **31** no-text acknowledgment candidates, **2** no-text greeting/grant
  candidates, and **2** no-candidate defer events. The graph renderer can
  realize acknowledgment as “I heard you.”, but the synchronous path treats
  that backchannel as intermediate and continues cognition; the daemon must
  not count it as substantive completion. The next production seam is
  graph-native reply expectation/terminality plus authorized realization.

### 2026-09-25 — Release graph-selected social replies in async daemon

- Added an owner-thread bridge that reads the incoming speech act from the
  graph, then renders and gates only a graph-selected social reply through the
  existing `conversation_social_graph` ProductionGate. The validated text is
  attached to that same graph reply Message. Ordinary statement acknowledgments
  remain intermediate and unreleased.
- Greeting and thanks regressions verify one graph-linked reply and exactly one
  released receipt per event. A fresh full profile records **42/74** replies,
  **32** pending turns, zero requested SearchRequests, and **111,341,568 bytes**
  peak RSS. Both social turns have exactly one individually scoped released
  receipt. Report:
  `evaluation/reports/phase7_daemon_completion_20260925_social_receipt_scoped.json`.
  The remaining 32 turns comprise 29 textless acknowledgment candidates, two
  no-candidate defer events, and one textless `grant` candidate. Resource and
  broader cognition/production/comparative gates remain open.

### 2026-09-25 — Remove corpus parse-label leakage from Phase 8

- The Phase 8 runner classified speech acts from the signal but also passed the
  independent corpus `literal_form` reference label into `WorldAdapter` as
  runtime evidence. Removed that field from the SUT call. The selected
  language-adapter parse now emits partial-event evidence only for a terminal
  unresolved parser gap accompanied by an explicit continuation/ellipsis
  boundary; the social-act path records its boundary from the inbound Message
  text without treating OOV complete words as fragments.
- Added regressions showing a deliberately wrong `declarative` label cannot
  override parser-derived fragments, nor can a `fragment` reference label make
  complete “hello” a fragment. Focused pre-correction suite passed **36/36**;
  after the social-path correction its focused regression passed **1/1**.
  Python compilation and `git diff --check` pass.
- Fresh full report
  `evaluation/reports/phase8_corpus_report_20260925_parser_fragment_evidence.json`
  records **41/74** force matches, **38/74** native disposition authority,
  **35/38** authoritative state matches, and three mismatches
  (`action_world_unknown`, `blocked_reference`, `action_referent`). The
  previously mislabeled `fragment_social` is now an authoritative defer match.
  `correction_uncertain` remains without disposition authority; resource,
  production, Phase 4, and comparative gates remain open.

### 2026-09-25 — Restore parser-backed native repair authority without force conflation

- The Phase 8 mismatches traced to the adapter leaving `literal_form` blank
  after correctly removing the corpus reference label. The selected language
  parse now emits imperative/interrogative/declarative form; parser gap plus a
  terminal continuation boundary emits fragment. Native action/reference
  arbitration consequently sees the same typed input contract in the corpus
  harness as in production, without reference-label leakage.
- Added a native disposition for uncertain non-turn continuation of
  common-ground content. Action-dependency and uncertain-correction rules
  preserve the selected communicative force while recording repair as the
  independent cognitive disposition. Native basis-finalization rules retain
  the specific repair rationale after generic force arbitration.
- Targeted action-repair, parser/reference-boundary, and uncertain-correction
  regressions pass **4/4**; JSON validation, Python compilation, and diff
  checks pass. Fresh 74-event report
  `evaluation/reports/phase8_corpus_report_20260925_parser_fragment_evidence.json`
  records **42/74** force matches and **39/39** matching authoritative
  dispositions, with **0** authoritative mismatches. Repair authority covers
  **11/16** expected repair cases; act authority covers **5/9**. Grounding is
  **0.34** on 50 grounded/partially-grounded cases. Learning, memory, and
  normalized cost measures remain unavailable, and the release gate remains
  blocked; resource, production, Phase 4, and comparative gates are open.

### 2026-09-25 — Extend native repair dispositions for unresolved non-turn events

- Added neutral graph rules for explicitly uncertain unresolved non-turn
  information requests, unresolved communication frontiers, and repair
  responses. The rules preserve information force and represent repair as a
  separate native disposition. A turn-compatible unresolved information
  request remains eligible for answer/learning; a graph-reported missing
  permission authority remains blocked.
- Full language-neutral evidence-arbitration module passed **8/8**; seed JSON
  validation passes. Fresh full report
  `evaluation/reports/phase8_corpus_report_20260925_parser_fragment_evidence.json`
  records **44/44** graph-authoritative state matches and zero authoritative
  mismatches. Native disposition authority is now **15/16** expected repairs
  and **5/9** expected actions. The unresolved lexical/reference questions
  and explicit repair-response events now have native repair authority.
- The report still records only **42/74** force matches, grounding **0.34/50**,
  and the release gate as blocked. `offer_unknown` remains without native
  disposition authority; question/weather learning, async production, resource,
  Phase 4, memory/learning/cost, and comparative-evaluation gates remain open.

### 2026-09-25 — Close current bounded repair-authority check

- Inspected the remaining `offer_unknown` event and current neutral evidence
  boundary. The runtime parse is a declarative assertion (`I can examine the
  blorf.`); the corpus's `offer` label is reference-only and is not passed into
  the system. Existing typed modal evidence supports permission/action
  questions, not declarative ability/offer acts. No graph-native semantic frame
  presently licenses converting this assertion into an offer, so adding a rule
  from the fixture label would reintroduce reference leakage. Leave this case
  explicitly unresolved pending a language-adapter/graph semantic signal.
- The last verified full report remains
  `evaluation/reports/phase8_corpus_report_20260925_parser_fragment_evidence.json`:
  42/74 force matches, 44/44 graph-authoritative dispositions matched, zero
  authoritative mismatches, native repair authority 15/16, native action
  authority 5/9, and grounding 0.34/50. The release gate remains blocked; no
  cognition implementation change was justified by this bounded check.

### 2026-09-25 — Revalidate Phase 4 evidence-source boundary

- Re-read the canonical Phase 4R contract and inspected current evidence
  producers. `self_dialogue` supplies held graph paths; `global_workspace`
  supplies salience quanta; `audience.novelty` supplies recipient-relative
  known/new classification; and `future_option_risk` assesses future-manifold
  residual/safety bounds. These values are not interchangeable with the
  missing expected-value, consequence, cost, or Phase 4 novelty dimensions,
  and the producers do not currently emit a complete event/goal-bound tuple.
  The integration must therefore remain fail-closed; no cross-faculty value
  synthesis is supported by current evidence.
- The machine-readable Phase 4T corpus audit remains the authoritative runtime
  check: **5** event-bound grounding-only records, **0** complete tuples,
  **0** eligible/actual promotions, deterministic replay. The focused
  static-source audit passes **2/2** tests. This confirms the next actionable
  work is adding independently authorized, provenance-bound dimension evidence
  at its owning faculties, not relaxing the Phase 4 bridge.

### 2026-09-25 — Reprofile connected corpus and attribute synchronous latency

- Fresh full 74-event connected-profile replay with repeat verification:
  `evaluation/reports/phase7_profile_resource_20260925_full74_goal_continuation_recheck.json`.
  Replay was deterministic, seed selection complete, and error-free; connected
  absolute RSS peaked at **109,457,408 bytes** (fails 100 MiB), while boot+event
  growth was **83,529,728 bytes** (passes the growth bound). Worst latency was
  **5,353.3 ms** at `overlap_offer`.
- A focused cumulative profile of the full-prefix `overlap_offer` call measured
  **4.97 s** in `WorldAdapter.converse`; **4.83 s** was synchronous HTTP/TLS
  response reading from 23 calls to `topic_grounding._http_get`, under
  `_dispatch_pending_io` (`scan_and_ingest_detail`, `topic_detail`,
  `ground_topic`, and `scan_and_sync_ground`). This matches the full replay and
  explains why the isolated event is fast: it has no accumulated graph requests.
- No bounded-time workaround was applied because skipping/capping those reads
  would alter grounded-answer behavior. The safe resource/latency seam is to
  route direct-path retrieval through the established daemon pattern: worker
  thread performs immutable external reads; graph writes, validation, and
  request completion remain on the owner thread. Until that boundary is shared
  or unified, Phase 7 latency and absolute RSS acceptance remain open.

### 2026-09-25 — Prevent topic grounding on native partial-event deferrals

- The latency attribution exposed a cognition error upstream of I/O: partial
  utterance fragments minted `answer_topic` goals, so their placeholder parse
  strings (`check the—`, `no wait—`, `could—`) were sent to external topic
  grounding. Added graph-rule guards keyed to the Message's existing typed
  `has_interpretation -> literal_form=fragment` evidence for direct topic,
  tracked-topic, document-span, and shadow-pronoun routes. Complete questions
  continue through their ordinary native route; no adapter-language condition
  or corpus reference label was added.
- Added a regression for parser-derived `I could—`: native disposition is
  `defer`, with no answer-topic goal or requested GroundRequest/SearchRequest.
  The complete topic-route suite passed **14/14**. A broader run of topic
  tracking/span/pronoun suites was intentionally interrupted after **7 passed**
  because it had run over five minutes; it produced no failures before
  interruption and is not counted as complete verification.
- Fresh deterministic 74-event connected replay
  `evaluation/reports/phase7_profile_resource_20260925_full74_fragment_route_guard.json`
  has **0 errors**, complete 72-seed selection, **109,518,848-byte** peak RSS,
  **83,480,576-byte** boot+event growth, and **1,420.8 ms** worst latency
  (down from **5,353.3 ms** on the immediately prior report). All **8/8**
  parser-classified fragment observations have **zero** answer-topic goals.
  RSS still exceeds 100 MiB and latency remains above target.
- Fresh Phase 8 replay
  `evaluation/reports/phase8_corpus_report_20260925_fragment_route_guard.json`
  has 74 events, **42/74** force matches, **44/44** graph-authoritative
  disposition matches, zero authoritative mismatches, repair authority
  **15/16**, action authority **5/9**, and grounding precision **0.941** /
  recall **0.32**. Release remains blocked; the partial-route correction does
  not close production, Phase 4, memory/learning/cost, or comparative gates.
- `git diff --check` and JSON parsing of all four changed route seeds pass.

### 2026-09-25 — Scope synchronous retrieval to the current graph goal

- A targeted trace at `question_unavailable` found that its graph disposition
  was `blocked` and it had no answer-topic goal, yet the direct adapter drained
  a stale `GroundRequest` for `quorplezap the door`, its generic search fallback,
  and a `DetailRequest` for `gate` from earlier turns. Added optional request-ID
  filters to search, phrase-grounding, and detail scanners. The live
  `WorldAdapter.converse()` path now fulfils only GroundRequest/SearchRequest
  nodes belonging to its current graph-selected answer-topic goal; detail is
  fetched only for the matching topic on a graph-marked topic follow-up.
  Blocked/repair/defer/error turns perform no unrelated network dispatch, while
  no-argument scanner and daemon callers retain their previous batch behavior.
- Added an integration regression proving a graph-blocked “What is beyond the
  wall?” turn leaves unrelated requested ground/search/detail nodes pending
  and does not invoke any scanner. That test passed **1/1**. Current-topic
  search minting, referent-linked evidence, and generic fallback controls pass
  **3/3**. A separate current-topic regression confirms the graph-selected
  `moon` grounding request is fulfilled, produces the held answer, and leaves
  unrelated search, grounding, and detail requests pending (**1/1**).
- Fresh deterministic connected 74-event profile
  `evaluation/reports/phase7_profile_resource_20260925_full74_request_scoped.json`:
  **108,597,248-byte** peak RSS (down **921,600 bytes** from the immediately
  prior fragment-guard profile), **82,513,920-byte** boot+event growth, and
  **1,719.9 ms** worst event (`question_response`). Replay is deterministic,
  all 74 events completed with zero errors, and growth remains bounded; absolute
  RSS and latency still fail acceptance.
- Fresh Phase 8 report
  `evaluation/reports/phase8_corpus_report_20260925_turn_scoped_retrieval.json`
  preserves **42/74** force matches, **44/44** matching graph-authoritative
  dispositions, zero authoritative mismatches, repair authority **15/16**,
  action authority **5/9**, and grounding precision **0.941**, recall **0.32**.
  Release remains blocked; comparative human references, Phase 4 evidence,
  production parity, resource, and learning/memory/cost gates remain open.

### 2026-09-25 — Avoid duplicate search when a held answer exists

- The request-scoped profile showed `question_response` spending **1,719.9 ms**
  on a repeat search despite an already-supported held answer. Updated the
  graph-native `topic_search` rule to require absence of a matching
  `HeldAnswer`, consistent with `topic_sync_ground`; added regression coverage
  that a held answer does not mint a duplicate `SearchRequest`. The focused
  held-answer and normal request-minting tests passed **2/2**.
- Fresh deterministic resource replay
  `evaluation/reports/phase7_profile_resource_20260925_full74_no_duplicate_search.json`
  completed all **74** events with zero errors. Peak RSS is **106,082,304
  bytes**, boot+event growth **80,158,720 bytes**, and worst latency **814.3
  ms** (`question_ack`). The held-answer `question_response` now takes **67.9
  ms**, confirming the duplicate retrieval was removed. Absolute RSS remains
  over the 100 MiB bound and worst-event latency remains above 150 ms.
- The remaining worst event is a genuine unheld-topic lookup, not stale queued
  work; optimizing or deferring it requires a separately verified retrieval
  boundary and is not part of this closed increment. No release gate is closed
  by this change; current Phase 8 evidence and other open gates remain as above.

### 2026-09-25 — Align causal-question regression with native disposition

- A focused rerun exposed a stale test assertion expecting `repair` for a
  well-formed, non-anaphoric reason question with missing causal support. The
  current graph-native arbitration correctly selects `learn` / `answer_or_learn`;
  missing causal evidence still prevents an answer commitment. Updated the
  regression to assert that contract rather than reverting the cognition rule.
- The causal-question structural positive control and the
  language-neutral unresolved-information eligibility test pass **2/2**.
  This closes the stale-test inconsistency only; causal retrieval/commit remains
  absent, so the answer, production, and release gates remain open.

### 2026-09-25 — Mint graph-owned causal retrieval intent

- Implemented `seeds/communication_causal_retrieval.json`, depending on native
  intent arbitration. For an event-linked, non-anaphoric reason interpretation
  that native arbitration marked `learn` with missing relation support, it
  mints one `CausalRetrievalRequest` bound to the interpretation and inbound
  event, using that message's graph-selected `comp_know_concept`. Its neutral
  schema records an `incoming_cause` lookup and `authority: none`; the rule
  does not fetch, assert a causal edge, or permit answer release. A held causal
  relation suppresses request creation.
- The focused regression verifies dependency loading, request schema/topic,
  event and interpretation links, mint-once behavior under another native rule
  pass, no answer commitment while the request is pending, and no request for
  the already-supported positive control: **1 passed**. Seed JSON parsing and
  scoped `git diff --check` pass.
- This supplies only the graph-owned request half of the documented causal
  retrieval boundary. No worker/candidate/provenance/owner-commit path exists
  yet; `info_explanation` must remain an explicit error, and cognition,
  production, resource, comparative, and release gates remain open.
- Fresh deterministic connected-profile replay
  `evaluation/reports/phase7_causal_retrieval_request_profile_recheck.json`
  passes its eight-event envelope: complete 64-seed closure, zero errors,
  identical replay, **86,573,056-byte** peak RSS, **60,575,744-byte**
  boot+event growth, and **68.97 ms** maximum event latency. This is the
  bounded slice only; the 74-event absolute RSS/latency failures recorded above
  remain open.
- Fresh full-corpus Phase 8 replay
  `evaluation/reports/phase8_corpus_report_20260925_causal_request_intent.json`
  completes **74/74** events with zero errors. It retains **44/44**
  authoritative disposition matches and zero authoritative mismatches; 2
  label matches still lack authority, repair authority is **15/16**, action
  authority **5/9**, and grounding precision/recall are **0.941/0.32**.
  Comparative baselines are unavailable and the release gate remains blocked.

### 2026-09-25 — Add typed causal candidate retrieval and owner staging

- Added `domains/causal_retrieval.py`: immutable retrieval calls Wikidata's
  structured P828 `has cause` property, retains entity IDs, statement rank,
  and reference snaks, and returns data only. It excludes deprecated and
  uncited claims; it does not parse article summaries or access the graph.
- Extended the daemon-only graph scheduler with a `causal_retrieval` action.
  Its worker runs outside the graph lock; completion checks the exact request
  status, topic, and I/O token before staging `CausalRetrievalCandidate` nodes
  on the graph owner. Restart/token-mismatch and malformed/unreferenced
  payloads fail closed. Candidate staging does not add `causal_influence`,
  `HeldAnswer`, or any answer authority.
- New unit coverage exercises source shaping, citation/rank filtering, stale
  token rejection, owner-thread staging, and no causal-edge/answer mutation.
  The live-source smoke retrieved four cited P828 candidates for “malaria”;
  this confirms transport and shape only, not topic identity or answerability.
- The new graph dispatch rule is authored in
  `scripts/build_cognitive_scheduler_seed.py` and regenerated into the
  self-load-only scheduler manifest, so daemon boot—not ordinary offline graph
  boot—installs its host action. Causal retrieval/request/profile integration
  tests pass **6/6**; the complete host-action supervisor suite passes **14/14**.
- Remaining safety boundary: native graph verification must still resolve the
  Wikidata entity to the graph-selected referent, account for event-specific
  causal questions, and mint typed supported evidence before production can
  answer. “Alarm” topic-level causes cannot be treated as the particular cause
  of a specific alarm event. Resource, comparative, and broader cognition gates
  remain open.
- Fresh 65-seed eight-event connected-profile replay
  `evaluation/reports/phase7_causal_retrieval_candidate_profile_recheck.json`
  passes determinism and bounded-profile assertions: **87,601,152-byte** peak
  RSS, **61,562,880-byte** boot+event growth, **67.2 ms** worst event, and zero
  errors. The refreshed 74-event, 17-content-key replay
  `evaluation/reports/phase7_profile_resource_20260925_causal_retrieval_full74.json`
  is deterministic with zero errors but still fails absolute RSS at
  **106,123,264 bytes** and worst latency at **1,082.1 ms**.
- Current full Phase 8 report
  `evaluation/reports/phase8_corpus_report_20260925_causal_candidates.json`
  again covers **74/74** events with zero errors, **44/44** authoritative
  disposition matches and zero authoritative mismatches; 2 labels still lack
  authority. Repair authority is **15/16**, action authority **5/9**, grounding
  precision/recall **0.941/0.32**, and the release gate remains blocked.

### 2026-09-25 — Bind causal requests to the resolved graph referent

- Tightened the request rule to require a `Message -> Mention -> Concept`
  referent matching the message's graph-selected `comp_know_concept`, and link
  the resulting `CausalRetrievalRequest` to that actual `Concept` using
  `about_topic`. The request still carries a display/query label for retrieval,
  but downstream cognition now has an explicit graph identity anchor. The
  focused reason-question test confirms the linked node is the graph-resolved
  `alarm` Concept; no candidate/answer authority was added.
- Added a fail-closed native regression: a reason interpretation with only a
  copied topic string and no graph-resolved Concept referent mints no causal
  retrieval request. The retrieval/commit and missing-referent suite passes
  **4/4**.
- Refreshed full Phase 8 report
  `evaluation/reports/phase8_corpus_report_20260925_causal_topic_link.json`:
  **74/74** observations, zero execution errors, **44/44** authoritative
  dispositions match, zero authoritative mismatches, 2 non-authoritative label
  matches, grounding precision/recall **0.941/0.32**. `info_explanation`
  remains native `learn` with no answer commitment; comparative and release
  gates remain blocked.
- Reprofiled the complete connected workload with the bound request
  (`evaluation/reports/phase7_profile_resource_20260925_causal_topic_link_full74.json`):
  73 selected seeds, 74 events, deterministic replay, zero errors,
  **106,110,976-byte** peak RSS, **80,240,640-byte** boot+event growth, and
  **812.4 ms** worst event. Growth passes, while the absolute 100 MiB ceiling
  and 150 ms worst-event target still fail.

### 2026-09-25 — Close event-specific causal-source check

- Checked the existing local ConceptNet English slab for `Causes` relations
  on `alarm`, `fire alarm`, and `alarm trigger`. The only match was the generic
  `alarm -> danger` edge; the two more specific terms had no `Causes` result.
- This commonsense edge is topic-level prior, not evidence that it caused a
  particular alarm event. It therefore does not satisfy the `info_explanation`
  event-specific causal-evidence requirement and was not connected to answer
  release. Current causal retrieval remains candidate-only until native graph
  evidence binds a cause to the queried event.
- This closes the bounded source check only. Phase 8 stays blocked on
  provenance/grounding and release; the full 74-event resource profile remains
  over the absolute RSS and latency limits, and comparative references remain
  unavailable. The overall project goal remains active.

### 2026-09-25 — Defer daemon remote grounding to async host actions

- A fresh connected-profile diagnostic attributed **812.4 ms** in the
  `question_ack` turn to synchronous retrieval/HTTP imports, far above the
  150 ms thought-manifold target. Daemon turns already have a graph-selected
  asynchronous search/ground host-action path, so `DaemonState` now marks its
  adapter as async-I/O-only: the in-turn topic probe may use held/local
  evidence but disables live web fallback, and `_dispatch_pending_io()` leaves
  remote requests for the daemon scheduler. Standalone `WorldAdapter` behavior
  is unchanged.
- The full topic-grounding and action/defer focused suite passed **44 passed,
  1 skipped** (445.68 s). A fresh one-event daemon host-action replay
  `evaluation/reports/phase7_daemon_ingress_20260925_question_ack_async_remote.json`
  completes `question_ack` with a graph-linked supported answer: **34.84 ms**
  ingress, **3.55 ms** native cycle, **738.03 ms** async host-completion
  latency, **86,085,632-byte** RSS peak, four external topic-grounding HTTP
  requests, **2/2** host actions complete, and zero pending turns/actions or
  execution errors. The remote wait is outside the synchronous ingress budget;
  this is a one-event mechanism check, not an async SLA or corpus-level
  resource pass.
- The fresh 74-event extension
  `evaluation/reports/phase7_daemon_ingress_20260925_async_remote_full74.json`
  confirms the async boundary across all inputs: **74/74** interpretations,
  **32.12 ms** maximum ingress, **29.98 ms** maximum native cycle, and zero
  runtime errors. It completes **40/74** turns; **34** remain pending after
  the drain, despite all **20/20** selected host actions completing. RSS peaks
  at **111,276,032 bytes** and max completion latency is **1,785.2 ms**; both
  absolute memory and full-turn completion gates fail. Relative to the earlier
  42-reply characterization, the two lost reply-present events are
  `overlap_correction` and `overlap_offer`, whose native observations now
  retain `literal_form=fragment` and correctly avoid releasing text for the
  incomplete overlap. They are not counted as regressions without evidence
  that these fragments require a reply.
- The sync connected 74-event profile still fails its absolute RSS and
  latency gates; the existing 74-event daemon profile still has incomplete
  reply coverage and exceeds the absolute RSS limit. Phase 4 corpus evidence,
  async full-corpus parity, Phase 8 comparative provenance, and overall
  cognition/production/resource acceptance remain open.

### 2026-09-25 — Graph-native terminality for textless adjacency candidates

- The report's new graph-only `Intent -> expects_response` readback separated
  pending turns into **32** that expected a reply and **2** with no expected
  response. Of the 32 expected turns, **31** had only a textless
  `acknowledgment` candidate and one had a textless `grant`; the adapter could
  not release either act as a substantive surface. The other two were
  deliberate no-response/defer cases, not missing replies.
- Fixed `conversation_honest_floor` (seed v1.3.0): a textless expected
  acknowledgment or grant no longer blocks the existing graph-minted explicit
  error floor. It preserves the textless act as an intermediate candidate and
  creates a separate floor Message with the diagnostic error. The synchronous
  full-turn test now checks one text-bearing final floor plus the retained
  intermediate candidate.
- Added graph-derived reply expectation/terminality readback to
  `WorldAdapter`; daemon owner-thread processing removes pending state only
  when a graph reply exists or an Intent is represented with no
  `expects_response` edge. The HTTP turn route returns
  `no_response_expected`; the socket poll uses a transport status token. No
  reply surface is fabricated for a graph-declared no-response event.
- Full async 74-event report
  `evaluation/reports/phase7_daemon_ingress_20260925_reply_terminal_complete_full74.json`:
  **74/74** terminal outcomes (**72** graph replies, **2** no-response
  terminals), **0** pending turns or host requests, zero execution errors,
  **20** host actions completed, **30.80 ms** ingress max, **15.76 ms** native
  cycle max, **1,461.7 ms** maximum async completion, and **112,496,640-byte**
  RSS peak. Ingress/native budgets and turn-liveness accounting pass; the
  absolute RSS limit still fails. Two expected responses that had previously
  stuck now terminate through the native error floor; the two no-response
  turns remain silent and explicitly classified.
- Verification: daemon ingress + HTTP/debug suites **12 passed**; focused
  full-turn compatibility regression **1 passed**; `git diff --check` and both
  report/seed JSON validations pass. Phase 4 corpus evidence, broader async
  production/authority parity, sync-path resource gates, and Phase 8 comparative
  provenance remain open.

### 2026-09-25 — Full-corpus connected-profile content coverage audit

- Compared full and connected profiles across all 74 Phase 0 events with the
  existing 17-key lexical selection used by the eight-event resource profile.
  Both runs completed with zero errors and the connected seed closure was
  complete, but only **18/74** structural observations matched. The 17 keys
  are not full-corpus coverage; the first event (`standalone_assertion`)
  differed only in mention referents because `sky` and `blue` were absent.
- A one-event controlled comparison supplying the existing lexical keys
  `the`, `sky`, and `blue` restores **1/1** parity with complete closure. This
  does not validate full 74-event parity. Passing every raw token is not the
  remedy: the global provider selector can select unrelated seed families and
  has previously produced incomplete closure. The outstanding loader task is
  a language-neutral typed content-key/scoping producer, followed by a proper
  all-74 parity/resource run. No code or seed policy was changed in this audit.

### 2026-09-25 — Scoped typed seed content references

- The cached pre-pass now indexes named entries by node type and name and
  exposes `scoped_content_refs={seed_id: [{"type": ..., "name": ...}]}` through
  `load_all_seeds` and the conversation profile. Scoped requests add only the
  named seed plus its dependency closure, and validate the reference before
  graph mutation. When that seed declares `selective_content_keys`, retained
  nodes are sliced by exact type/name. Legacy flat `content_keys` selection is
  unchanged; an unresolved scoped ref fails the completeness check.
- Regressions verify same-name providers in an unrelated seed are not selected,
  unresolved refs fail closed, and full-vs-connected `standalone_assertion`
  parity is restored when both lexical and relevant colour concepts are named.
  Seed-loader suite: **13 passed**; scoped single-event parity: **1 passed**;
  existing eight-event profile parity: **1 test, 8/8 events passed**. Python
  compilation and `git diff --check` pass.
- The typed scoping API is now present, but its evidence producer is not: no
  graph-grounded language-neutral stage yet emits these seed-scoped content
  refs. Full-corpus connected parity and resource acceptance remain open.

### 2026-09-25 — Audit typed lexical candidate closure

- A read-only prototype used only event-signal tokens that exactly occur in
  `learned_lexicon`, then queried the cached index for typed `Concept/name`
  providers. It found 81 keys from 145 unique surface words; 16 keys had
  multiple provider seeds. Provider roots plus closure total 95 seeds.
- `signal` illustrates the unresolved sense problem: global typed-name matching
  selects `operating_systems -> compiler_theory -> llvm_passes`, whose
  dependency `llvm_ir` is missing. Type filtering therefore does not make raw
  lexical keys a safe load plan. No selection policy was changed. The content
  producer must be graph-grounded and source/sense-scoped before the existing
  typed loader boundary can be activated; full-corpus parity and resource
  verification remain open.

### 2026-09-25 — Resource recheck after seed-index v4

- Fresh CLI report for the existing eight-event 17-key connected profile
  `evaluation/reports/phase7_profile_resource_20260925_conversation_seed_index_v4_17key_recheck.json`:
  73 selected seeds, complete closure, zero errors, **87,015,424-byte** RSS,
  **60,903,424-byte** boot+event growth, and **76.4 ms** maximum event. The
  bounded eight-event resource assertions pass.
- Fresh 74-event report
  `evaluation/reports/phase7_profile_resource_20260925_full74_seed_index_v4_17key_recheck.json`:
  73 selected seeds, complete closure, zero errors, **108,240,896-byte** RSS,
  **82,116,608-byte** boot+event growth, and **1,367.5 ms** worst event
  (`question_ack`). Absolute RSS is 3,383,296 bytes over 100 MiB; latency is
  above 150 ms. Both runs use legacy flat 17-key selection, not scoped refs;
  they do not establish full-corpus parity or typed-ref resource effect.

### 2026-09-25 — Guarded action arbitration and reason-scope evidence

- Native action arbitration was narrowed after a full-corpus mismatch audit:
  typed future conditions defer, while continuation/partial-grounding action
  rules are constrained and standalone deferral is no longer blanket. Focused
  controls pass 9/9. The guarded Phase 8 report
  `evaluation/reports/phase8_corpus_report_20260925_action_arbitration_guarded.json`
  preserves 47/74 authoritative dispositions; only `question_ack` and the
  documented `action_check` discrepancy remain mismatched.
- Phase 7 was reprofiled after these changes:
  `evaluation/reports/phase7_profile_resource_20260925_action_arbitration_guarded.json`.
  Replay is deterministic with no errors; peak RSS is 109,662,208 bytes,
  boot/event growth 83,533,824 bytes, and maximum event latency 1,206.2 ms.
  Growth bounds pass; absolute RSS and latency targets fail.
- Causal retrieval now filters fuzzy Wikidata labels, and neutral
  `relation_scope` is carried through text and semantic-event ingress. Native
  topic-level retrieval requires `conceptual_general`; event-specific past
  questions do not dispatch it. Focused scope tests pass 5/5. The fresh Phase
  8 report `evaluation/reports/phase8_corpus_report_20260925_reason_scope_neutral.json`
  retains 47/74 authority, 48/74 force, and grounding F1 .507 with the same
  two authoritative mismatches. `info_explanation` still produces no answer;
  event-scoped causal evidence and answer release remain open.
- Broad retrieval/grounding/action lifecycle validation passes **61 passed,
  1 skipped**. Production quality, full-corpus connected-profile parity,
  resource envelope, Phase 4 complete evidence, and comparative-human/provenance
  gates remain open.

### 2026-09-25 — Native gap-awareness disposition guard

- `gap_awareness.note_unhandled_instruction_gap` is now linked to the native
  interpretation for its message and suppressed for `defer`, `answer`,
  `repair`, `blocked`, `error`, and `learn`. This prevents parser kind plus an
  unhandled outcome from overriding native communication cognition.
- Focused correction/social/deferred regressions pass **3/3** and assert the
  false action-gap surface and same-event SelfConcern are absent. The full
  Phase 8 report
  `evaluation/reports/phase8_corpus_report_20260925_gap_disposition_guarded.json`
  preserves 47/74 authoritative dispositions and only the existing
  `question_ack` and `action_check` mismatches. Correction/social now fail
  closed at the explicit error floor; production realization is still open.
- Phase 7 report
  `evaluation/reports/phase7_profile_resource_20260925_gap_disposition_guarded.json`
  has deterministic replay/no errors, 107,094,016-byte peak RSS,
  80,953,344-byte growth, and 1,462.1 ms max latency. RSS and latency fail.
- The dedicated gap-awareness run has **13 passed, 1 failed**: the
  `moon` topic-answer outcome is unresolved. This test does not exercise the
  changed instruction-gap predicate; causality/baseline is not established.
  Production, topic grounding, resource, Phase 4, connected-profile parity,
  and comparative gates remain open.

### 2026-09-25 — Native identity-bound causal request dispatch

- Added `communication_causal_identity_binding` as a separate seed without
  changing the current `communication_causal_retrieval` source contents. The
  native rule binds an already-minted event/topic request only when that graph topic
  has a typed `ExternalIdentityEvidence` node marked verified; it copies the
  provider entity ID and links the identity node to the request. Conversation
  profile closure includes this seed.
- The daemon now refuses to launch causal retrieval without the bound ID and
  retrieves the entity directly rather than selecting one from a text search.
  Returned labels must still exactly match the graph topic, and owner commit
  requires the result ID to equal the request's bound ID. Identity-status
  candidates do not bind; a verified identity does. Focused causal/daemon
  integration set passes **9 passed, 31 deselected**; both causal seed JSON
  files parse and `git diff --check` passes.
- This is a fail-closed identity-binding seam, not an identity-acquisition
  result. No provider currently mints independently verified identity
  evidence for the corpus; no external cause endpoint identity is bound, no
  candidate is promoted into `causal_influence`, and no answer is released.
  Event-scoped causal support and production remain open.
- Integrity note: the current causal-retrieval seed SHA256 is
  `5d0fcfb6745e1737e29c55dd1071aa77c13f68cef58032a6451dfd934324beb0`, which
  differs from the historical corpus-lock entry
  `fb3445828dae97b6aad46d646a914788f055d71a1cb56ec1c8388c586ba07cc8` in
  `problem_shape_eventized_rule_order_seed_corpus_lock_v1_7_20260925.json`.
  The current source and historical lock therefore do not match; no historical
  lock was rewritten by this increment.
- Full v5 replay
  `evaluation/reports/phase8_corpus_report_20260925_identity_bound_causal_request.json`
  completed 74/74 events with the release gate blocked and no errors. It
  preserves 47/74 authoritative dispositions, force exact 48/74, grounding
  TP17/FP0/FN33/TN24 (F1 .507), and zero Phase 4 complete tuples/promotions.
  `info_explanation` remains native `learn` with no answer commitment and the
  explicit error floor.
- Full connected resource profile
  `evaluation/reports/phase7_profile_resource_20260925_identity_bound_causal_request.json`
  selected all 68 seeds including the new identity-binding seed; 74/74 replay
  is equal with zero errors. Peak RSS is 107,393,024 bytes, boot/event growth
  81,244,160 bytes, and maximum event latency 1,218.9 ms. Growth assertions
  pass; the absolute RSS and event-latency bounds remain open/failing. No
  corpus answer or resource gate is claimed closed.

### 2026-09-25 — Cited causal claim evidence staging (not relation promotion)

- Added a separate native evidence seed. A candidate is eligible only after
  owner-thread schema/citation validation, native binding of the effect to the
  request's verified identity, and an existing graph concept for the cause
  with its own verified identity. Native execution mints a
  `CausalClaimEvidence` node linked to the candidate, request, effect, and
  cause; it records the cited P828 source claim. It deliberately does **not**
  add a `causal_influence` edge or authorize answer production. This avoids
  reopening the generic topic-summary path for a why-question.
- The regression withholds the claim node while the cause identity is merely a
  candidate, then verifies the evidence node appears after that identity is
  marked verified, with citation provenance retained and no canonical causal
  edge or reply authority. Focused retrieval/daemon/profile suite passes
  **11 passed, 43 deselected**. The named conversation profile includes both
  new seeds and loads 69 seeds; its closure regression passes.
- Final-state Phase 8 report
  `evaluation/reports/phase8_corpus_report_20260925_causal_claim_evidence.json`
  completed 74 events with no errors, 47/74 authoritative dispositions,
  force exact 48/74, grounding TP17/FP0/FN33/TN24 (F1 .507), zero Phase 4
  complete tuples/promotions, and blocked release. `info_explanation` remains
  `learn` with no commitment and the explicit error floor.
- Final-state Phase 7 report
  `evaluation/reports/phase7_profile_resource_20260925_causal_claim_evidence.json`
  selects 69 seeds and confirms equal deterministic replay/no errors. Peak RSS
  is 107,540,480 bytes, growth 81,383,424 bytes, maximum event latency
  1,205.2 ms, and total latency 6,094.2 ms. Growth bounds pass; absolute RSS
  and latency remain open/failing. External identity acquisition, decision
  from a cited claim to a graph causal fact, language-neutral causal answer
  realization, and all broader release gates remain open.

### 2026-09-25 — Protocol-aware v5 reference audit

- The v5 SUT contract excludes the v4-only ELIZA scorecard because the ELIZA
  adapter has no event-context/history input profile. The raw audit had still
  reported ELIZA as `missing`, conflating profile incompatibility with an
  uncollected applicable reference. Added a protocol-specific
  `not_comparable` classification without changing the five-class comparative
  release contract or accepting v4 ELIZA evidence as v5.
- Regenerated
  `evaluation/reports/phase8_raw_reference_audit_20260925_v5_protocol_aware.json`:
  two complete raw classes (Gemma small LLM and Qwen modern LLM), one
  not-comparable class (ELIZA), two missing human classes, and
  `score_interpretation_performed=false`. The overall audit remains
  `incomplete`; the release still needs a matched ELIZA protocol or an explicit
  protocol amendment, human references, and blinded annotation.
- Focused raw-audit tests pass **6/6**, including the v5 exclusion case. This
  corrects evidence classification; it does not relax or close the comparative
  acceptance gate. A complete v4 ELIZA run is explicitly rejected as evidence
  for this v5 row.

### 2026-09-25 — v5 audit input-profile integrity

- Tightened raw-reference completeness so a v5 `protocol_id` alone cannot
  certify comparability. Each v5 reference must declare the
  `event_context_v5_history8` input profile; small and modern LLM runs must
  additionally declare an eight-turn session-history limit. Human classes
  also require the v5 event-context profile.
- Added a fail-closed regression for a modern-LLM run mislabeled with the v5
  protocol but declaring the isolated-signal v4 profile. The focused audit
  suite passes **7/7**.
- Regenerated
  `evaluation/reports/phase8_raw_reference_audit_20260925_v5_protocol_aware.json`:
  two complete raw LLM classes, ELIZA `not_comparable`, and two missing human
  classes. Overall status remains `incomplete`, with
  `score_interpretation_performed=false`. The provenance guard strengthens
  classification but does not close the human/blinded comparative gate.

### 2026-09-25 — Defer topic-gap judgment until retrieval settles

- Reproduced the known gap-awareness failure: the Moon topic could receive a
  supported retrieved answer while its goal still said `outcome=unresolved`.
  The adapter had recorded the miss before its graph-minted retrieval finished,
  allowing a nested native comprehension to file a false knowledge gap.
- Topic outcomes now remain `pending` while their linked/exact-topic grounding
  requests are active. Once turn-scoped I/O settles, the adapter records
  `resolved` only with supported graph-held topic evidence; settled misses
  remain `unresolved` and eligible for the existing native gap rule. This
  changes outcome timing, not gap classification authority.
- `tests/test_gap_awareness_migrated.py`: **9 passed**, including successful
  resolution, forced retrieval miss, self-account controls, and explicit gap
  report. Python compile and `git diff --check` pass.
- Full v5 Phase 8 report
  `evaluation/reports/phase8_corpus_report_20260925_topic_outcome_lifecycle.json`:
  74 events, zero errors, 47/74 authoritative dispositions, grounding F1 .507,
  zero Phase 4 complete tuples/promotions, release blocked. Full connected
  Phase 7 report
  `evaluation/reports/phase7_profile_resource_20260925_topic_outcome_lifecycle.json`:
  deterministic equal replay, zero errors, 107,487,232-byte peak RSS,
  81,453,056-byte boot/event growth, and 1,215.8-ms maximum event latency.
  Growth limits pass; absolute RSS/latency, production, cognition coverage,
  and comparative gates remain open.

### 2026-09-25 — Typed standalone-assertion defer

- A broad declarative-force arbitration attempt overcaptured offer, refusal,
  social-closing, learning-report, and error events. It was narrowed and its
  temporary broad-rule reports removed rather than retaining false native
  dispositions.
- The language adapter now emits neutral `statement_act=assertion` evidence
  only for parses whose predicate is typed as a copula. Native standalone
  non-turn defer requires this evidence, assertion/correction force, and
  standalone/non-turn context. A force-only synthetic control remains
  unclassified; the turn-compatible contrast remains unaffected.
- Full language-neutral arbitration suite: **21 passed**. Full v5 Phase 8
  report `evaluation/reports/phase8_corpus_report_20260925_typed_standalone_assertion_defer.json`:
  74 events, zero errors, native authority **49/74** (up from 47/74), no prior
  authoritative dispositions lost, both targeted assertions match defer.
  Grounding F1 .507 and Phase 4 complete tuples/promotions zero; release
  remains blocked. Their production is still an explicit error because the
  graph expected acknowledgement but no supported acknowledgement surface was
  available at the time; the subsequent graph-owned receipt is recorded below.
- Full connected Phase 7 report
  `evaluation/reports/phase7_profile_resource_20260925_typed_standalone_assertion_defer.json`:
  deterministic equal replay, zero errors, 107,675,648-byte peak RSS,
  81,518,592-byte boot/event growth, 1,209.8-ms max event latency. Growth
  bounds pass; absolute RSS/latency, production, grounding recall, Phase 4,
  and comparative gates remain open.

### 2026-09-25 — Native receipt for deferred standalone assertions

The typed standalone/non-turn assertion disposition now mints a separate
graph-owned `neutral_receipt` acknowledgment. The adapter only releases that
marked graph reply through Phase 6 with semantic intent
`acknowledge_receipt_without_endorsement`; it does not assert proposition
acceptance or action execution. The focused end-to-end test passes and confirms
one native reply plus one released production receipt. Full language-neutral
tests pass **21/21**. Fresh full v5 Phase 8 report
`evaluation/reports/phase8_corpus_report_20260925_typed_standalone_assertion_neutral_receipt.json`
confirms both target assertions released, zero event errors, 49/74 authoritative
dispositions, grounding F1 .507, and zero Phase 4 promotions; release remains
blocked by open cognition and comparative criteria. Fresh connected 74-event
Phase 7 report
`evaluation/reports/phase7_profile_resource_20260925_typed_standalone_assertion_neutral_receipt.json`
is replay-equal/error-free with 107,917,312-byte peak RSS, 81,883,136-byte
boot/event growth, and 1,207.9-ms max event latency; absolute resource gates
remain open.

### 2026-09-25 — Async error terminality and remaining pending turns

The honest-floor rule labels its diagnostic as `terminal_outcome=explicit_error`.
Daemon lifecycle/readback exposes it with `status=error`, clears the transport
pending entry after completion, and does not count it as a released production
reply or ordinary chat-history answer. Phase 7 now reports completion statuses
and exact pending event identities. Daemon-debug tests pass **6/6**; the HTTP
status regression passes.

Fresh full async 74-event replay
`evaluation/reports/phase7_daemon_ingress_20260925_typed_receipt_error_terminal_final.json`:
60 explicit errors, 7 released replies, 2 no-response terminals, and 5 pending
turns. The two standalone assertions have released neutral receipts. Max ingress
is 37.5 ms, max native cycle 25.3 ms, and peak RSS 105,721,856 bytes (absolute
bound still fails). Pending events are `info_status`, `info_unknown`,
`info_reference`, `error_empty`, and `action_referent`. Four have graph text
but lack async production-release bridges; `info_unknown` has an expected but
textless answer. Other cognition, production, RSS, retrieval, Phase 4, and
comparative gates remain open.

Final current-code rechecks: fresh v5 Phase 8 report
`evaluation/reports/phase8_corpus_report_20260925_typed_receipt_error_terminal.json`
still blocks overall release while preserving both released non-endorsement
receipts (49/74 authoritative dispositions, F1 .507, zero Phase 4 promotions).
Fresh synchronous connected Phase 7 report
`evaluation/reports/phase7_profile_resource_20260925_typed_receipt_error_terminal.json`
is replay-equal/error-free; peak RSS 108,519,424 bytes and maximum event
latency 1,221.7 ms leave absolute resource gates open; growth bounds pass.

### 2026-09-25 — Async daemon receipt release and readback

The actual daemon completion path now dispatches only the typed standalone,
correction, or social receipt releasers. Graph polling returns a receipt only
when its ProductionGateReceipt is released and binds that exact reply to the
inbound turn; a subsequent honest-floor node cannot shadow that authorized
reply. The Phase 7 daemon harness carries v5 event context as well. Focused
daemon/debug and synchronous receipt tests pass **6/6**. The standalone-only
daemon report records 32.6-ms ingress, 2.6-ms native/completion latency, and
83,738,624-byte peak RSS, with a released receipt. The full 74-event report
releases both standalone receipts and reaches 41.4-ms max ingress / 21.7-ms
max native cycle, but remains at 109,150,208-byte RSS, 35/74 authoritative
dispositions, and one pending turn. Absolute resource and full cognition gates
remain open.

### 2026-09-26 — Current canonical and comparative recheck

The fixed-tree conversational continuity, method-aliasing, production,
grammar, and Phase 4 bridge battery passes **77/77**. The full comparative
runner/audit/release test set passes **49/49**; the v5 context-boundary ELIZA
adapter tests pass **8/8**. ELIZA now receives a v5 input envelope containing
transport metadata, held-answer setup, and up to eight prior turns, but its
deterministic lexical policy remains stateless and only provenance is scored.
The raw audit has complete reference records for ELIZA **1/1**, Gemma **2/2**,
and Qwen **2/2**; base and advanced human references are still missing, so no
score interpretation occurs and comparative release remains blocked.

The fresh v5 SUT report preserves all 74 event outcomes and includes ELIZA
raw provenance 74/74. It measures median/p95/max synchronous latency
**130.34/200.92/221.63 ms**, with 27/74 events over 150 ms. The current
connected-profile deterministic replay passes all RSS assertions at
**99,127,296 bytes**, with complete closure, no errors, replay equality, and
120.01 ms max event latency. Full-boot latency remains open. Phase 4 remains
at three grounding-only evidence sources and zero complete tuples/promotions;
human annotation/adjudication, broader cognitive evidence, and production
acceptance remain open.

### 2026-09-26 — Phase 4 audit adjacency path

A fresh cProfile attributed 28.36 s of 57.59 profiled seconds to the Phase 4
post-turn evidence audit, which scanned every graph node for each of the 74
events. Replacing that scan with incoming/outgoing adjacency reads for the same
four explicit event-link relations preserves the boundary and passed the
partial-evidence audit tests **6/6**, including all relations in both
directions. Full v5 report generation fell from **23.08 s** to **10.05 s**.
The event outcomes, dispositions, release labels, observed states, Phase 4
records, and 55/74 authoritative count are unchanged. Current SUT turn
latency remains noncompliant (median/p95/max **140.02/192.95/257.90 ms**,
31/74 over 150 ms). The connected 74-event deterministic replay is outcome-
equal/error-free at **99,131,392 bytes**, with every RSS assertion passing and
109.96 ms maximum turn latency. This improves evaluation cost and resource
replay but does not close full-boot latency, Phase 4 evidence, production,
comparative-human, or cognition gates.

### 2026-09-26 — Connected-profile resource gate restored

The isolated P0-A guard import had been pulling its whole evaluator package
initializer into ordinary conversation turns, including broker/manifest and
cryptography dependencies. Lazy package exports remove that unintended import
while preserving `from evaluation.p0a import ...` compatibility. The focused
import regression passes and the P0-A evaluation suite passes **144 passed,
17 skipped**.

Three fresh 74-event conversation-profile runs pass all resource assertions and
the 150 ms max-event threshold at **102,604,800**, **102,449,152**, and
**102,502,400 bytes** peak RSS; the last is deterministic replay-equal. All
remain under the 100 MiB cap, with roughly 2.1 MiB headroom. Fresh structural
parity remains 74/74 with zero errors and complete selection. Full-boot latency,
broader cognition/production authority, Phase 4 tuple completeness, and
comparative-human acceptance remain open.

The refreshed v5 raw audit confirms three complete raw reference classes
(ELIZA 1/1, small LLM 2/2, modern LLM 2/2) and two missing human classes; it
performs no score interpretation
([audit](../../../evaluation/reports/phase8_raw_reference_audit_20260926_lazy_p0a_import_v1.json)).

### 2026-09-26 — Failed standalone topic retrieval now selects native repair

The unresolved standalone `info_unknown` case now transitions to repair only
after its same-event topic retrieval fails without verified support. The
existing ask-back faculty and production gate release a clarification focused
on the graph-selected topic, with no unsupported answer. The full v5 replay
changes only this event; native-authoritative disposition count rises **55→56**
([report](../../../evaluation/reports/phase8_corpus_report_20260926_failed_topic_repair_v2_event_context_v5.json)).
Full-vs-connected parity stays 74/74 and the connected deterministic replay
still passes resource/latency bounds. Full-boot latency, grounding F1 **0.438**,
Phase 4 tuple completeness **0/3**, broader cognition/production, and comparative
human references remain open.

The current full v5 target recheck after the import fix
([report](../../../evaluation/reports/phase8_corpus_report_20260926_lazy_p0a_import_v1_event_context_v5.json))
confirms the other open gates: authority **55/74**; grounding recall **0.28**,
F1 **0.438**; Phase 4 has 3 grounding-only sources and 0 complete tuples or
promotions; full-boot median/p95/max latency **129.53/211.60/224.29 ms** with
26 turns over 150 ms. The comparative raw audit still lacks human references
and does not interpret scores; it remains blocked.

### 2026-09-26 — Live conceptualizer release-boundary audit

A focused code-path audit found that most substantive `converse()` branches call
`_form_reply_intent_for_text()` but do not use its `Committed` readback as their
outbound authority. Fault injection made that distinction observable, but did
not by itself prove unauthorized release: the self-organisation answer still
passed its independent graph-selected `ProductionGateReceipt` and reflective
evidence path. Other classes similarly have dedicated action, topic,
comprehension, repair, or social release seams; generic legacy/meta/continuation
branches still need a complete authority inventory. The verified finding is
therefore architectural: conceptualizer monitoring is not a universal live
release gate, while some reply classes have separate graph-native production
authority. Do not replace those stronger typed receipts with a word-token
conceptualizer result.

Next bounded increment: finish the per-class inventory of selection evidence,
release gate, commitment identity, and final surface source; then close the
largest substantive reply class still lacking graph-linked release evidence,
with positive and fail-closed controls. Preserve explicit diagnostic errors
and existing graph-selected action/repair receipts. No behavior or acceptance
score changed in this audit. Full-boot latency, broader cognition/production,
Phase 4 tuple completeness, and comparative-human references remain open.
The final focused regression batch (`test_conceptualized_converse.py` plus
`test_phase6_information_production_bridge.py`) reports **17 passed, 2
failed**: the Borogove and weather retrieval controls both returned the
diagnostic error; the existing tracker records Borogove's upstream
`SearchRequest` DNS failure, and the weather retrieval is likewise
network-dependent in this restricted run. `git diff --check` was clean for
the project documents at that verification point.

The release-seam inventory from `WorldAdapter.converse()` is now bounded:

| Reply class | Current release authority | Audit result |
| --- | --- | --- |
| Conversation action / ask-back | Selected action Goal or clarification Message plus `conversation_action_graph` receipt | Typed and event-bound |
| Causal/topic repair | Native repair selection plus graph-selected repair production receipt | Typed and event-bound |
| Grounded topic answer | Event-bound answer-topic/HeldAnswer, supported TopicGroundingEvidence, and information receipt | Typed and evidence-bound |
| Comprehension, instruction, reference, capability, question response | Dedicated graph readback seam and production receipt | Separate typed seams; retain individually |
| Reflective self-organisation | Native faculty/disposition, supported ReflectiveAnswerEvidence, answer Message, and reflective receipt | Typed and evidence-bound; remains valid when conceptualizer is unavailable |
| Social/correction/acknowledgement | Graph-selected Message plus social/correction production gate | Typed by class |
| Unresolved information / explicit errors / non-turn defer | Withheld information receipt, explicit diagnostic surface, or silence | Correctly non-substantive; not an answer-release gap |
| Legacy meta answer (not self-organisation), generic non-social outbound Message | Surface can flow to `_finish_turn_reply()` without a uniform event-bound production receipt | Release-authority audit target |
| Deliberative continuation/floor holder | `_deliberate_turn_continuation()` selects among direct/transitive/relation/follow-up paths in Python, and the selected prose is returned directly; `_record_conversation_decision()` records a state after that choice but is not its native authority | Confirmed violation of graph/native decision invariant; migrate selection to graph-authored candidate/settlement before treating the trace as authority |

The highest-priority cognition increment is the Python continuation selector:
make candidate discovery mechanical, move the continuation choice into
graph-authored arbitration/settlement, and bind the selected candidate to the
released surface and production receipt. The repository already has the
native `conversation_deliberation_phase4a` valuation/collapse/trace rules and
`domains.conversation_deliberation` evidence materializer; the live continuation
currently does not submit its candidates through that path. Instead,
`_record_conversation_decision()` assigns the candidate token and numeric value
after the Python ladder has returned a winner. Prefer adapting the existing
Phase 4A boundary to carry candidate kind, grounding provenance, and the
evidence-derived surface, rather than creating a parallel selector. Then audit the remaining legacy
meta/generic branches and add positive exact-surface plus missing-commitment
controls per class. The typed authorities above must remain independent of the
token-derived conceptualizer, whose current content extraction is not a
semantic frame.

### 2026-09-26 — Direct factual continuation enters native Phase 4A collapse

The bounded direct-fact family in `_deliberate_turn_continuation()` now
materializes every matching held `knows_fact` relation as an output-null
candidate. The candidate surface is rendered from that graph relation; the
source relation is linked as evidence. A seed-authored Phase 4A rule assigns
the family policy value, and the existing native scorer/Argmax creates the
selected candidate. The adapter releases only the selected candidate's exact
surface after structural parse-back, with the released `ProductionGateReceipt`
pointing to that same candidate. Missing native policy fails closed. The scan
does not issue external retrieval for each alternative. Direct facts are
proposed when an event concept matches either relation endpoint.

The discourse-state materializer now accepts the specific active goal being
audited; the live bridge no longer cross-links one deliberation to multiple
event goals while looping over them. The reflective-answer trace reader also
recognizes the already-validated seed-inventory support path through the
`Agent` index, in addition to direct `Microtheory` support.

Verification: Phase 4A/live native-authority, reflective-answer trace,
five-turn continuity, settle-back, and Phase 0 contracts pass **36/36**. A
fresh 74-event Phase 8 v5 run is event-for-event identical in reply,
disposition, and release status to the pre-change report: authority **56/74**,
grounding F1 **0.438**, and Phase 4 complete tuples/promotions **0/0**. Fresh
full-vs-connected parity using the validated graph-reference pre-pass is
**74/74**, zero errors. The independent connected 74-event replay is
deterministic and complete with all RSS assertions passing, **98,058,240-byte**
peak RSS and **106.35 ms** maximum event latency. The incorrect initial parity
run without the required graph-reference pre-pass was discarded as
non-comparable.

This closes only the direct held-fact continuation slice. Transitive relation,
held-frame, residual-stance, follow-up inquiry, and floor-holding selection
remain on the Python path; broader cognition and production, full-boot latency,
Phase 4 tuple completeness, and comparative-human evaluation remain open.

### 2026-09-26 — Continuation families consolidated into native Phase 4A

The continuation proposal stage now submits direct held facts, transitive
facts/relations/frames, direct relation neighbors, held frames, residual
stance frames/facts/inquiries, and co-mentioned follow-up inquiries together
to the existing Phase 4A candidate ledger. Python performs graph-grounded
candidate discovery and surface realization; authored Phase 4A rules value
candidate families, and native scoring/Argmax records the selected candidate
and rejected alternatives. Release is fail-closed unless native policy
valuation, current-epoch selection trace, structural parse-back, and the exact
selected-candidate production receipt are all present.

The focused Phase 4A/live-authority/continuity/reflection/settle-back/Phase 0
batch passes **41/41**. The new transitive test provides competing grounded
paths and verifies native loser rejection and exact winner-to-receipt
identity. Fresh Phase 8 v5 reports **56/74** authoritative dispositions,
grounding recall **0.28** and F1 **0.438**, and **0** complete Phase 4 evidence
tuples/promotions; the broad quality gates therefore remain open. The fresh
74-event connected replay is deterministic, complete, error-free, and passes
all resource assertions (**98,357,248-byte** peak RSS; **114.35 ms** maximum
event). Fresh full-vs-connected comparison using the validated graph-reference
pre-pass is **74/74**, with zero mismatches or errors. Reports:
[Phase 8 corpus](../../../evaluation/reports/phase8_corpus_report_20260926_native_continuation_all_families_v1_event_context_v5.json),
[connected replay](../../../evaluation/reports/phase7_profile_resource_20260926_native_continuation_all_families_v1_conversation_replay.json),
[profile parity](../../../evaluation/reports/phase7_seed_profile_parity_20260926_native_continuation_all_families_v1_graph_ref_full74.json).

This closes the listed continuation-family selector migration, not the wider
conversational cognition/production objective. Surface rendering remains
adapter-authored English; full-boot latency, semantic grounding quality,
Phase 4 tuple completeness, matched human/small-LLM references, and remaining
generic legacy release seams are still open.

### 2026-09-26 — Cache exact reflexive RuleSummary lookups

A full-run profile found that `_detect_reflexive_rule()` repeatedly scanned
graph-resident `RuleSummary` nodes for exact name/keyword matches: 32 calls
accounted for **0.984 s** cumulative in the instrumented run. Added a lazily
built exact-match index on the adapter. It persists across turns and is
invalidated by `ensure_rule_provenance()` before any supported summary refresh;
matching semantics, ambiguity ordering, and honest no-match behavior remain
unchanged.

The focused self-model/comprehension/conversation compatibility suite passes
**73/73**, and Phase 8's per-event reply/state/release/grounding/authority
fields are unchanged. One fresh full v5 run measures **124.97/186.87/221.79
ms** median/p95/max, with **20/74** turns over 150 ms, versus the immediately
preceding unindexed run's **141.56/198.32/240.44 ms** and **30/74** over. This
single comparison is encouraging but not a robust latency closure; full-boot
latency remains open. Fresh connected replay is deterministic and complete,
with zero errors, all resource assertions passing, **99,749,888-byte** peak
RSS and **111.23 ms** max event. Validated-reference profile parity is
**74/74**, zero mismatches/errors. Reports:
[full corpus](../../../evaluation/reports/phase8_corpus_report_20260926_rule_summary_persistent_index_v1_event_context_v5.json),
[connected replay](../../../evaluation/reports/phase7_profile_resource_20260926_rule_summary_persistent_index_v1_conversation_replay.json),
[profile parity](../../../evaluation/reports/phase7_seed_profile_parity_20260926_rule_summary_persistent_index_v1_graph_ref_full74.json).

This is a bounded lookup optimization, not a cognition-quality improvement.
Grounding recall remains **0.28** (F1 **0.438**), Phase 4 complete tuples /
promotions remain **0/0**, authority coverage is **56/74**, and full-boot
latency, broader production, comparative human/small-LLM evidence, and other
open acceptance gates remain active.

### 2026-09-26 — Enforce approved Phase 4 evidence source types

The Phase 4 partial-evidence audit previously marked any complete five-field
record as promotion-eligible, although the substrate tuple audit and Phase 4P
boundary authorize only `ThoughtManifold` sources. Eligibility now requires
both a complete existing tuple and an approved source type. A complete tuple
from an `AudienceModel` is explicitly recorded as complete but ineligible;
no dimensions are filled and the audit still never selects/promotes a
candidate.

Phase 4 partial/source/live-deliberation regressions pass **24/24**. A fresh
Phase 8 v5 run continues to report **3** grounding-only evidence sources,
**0** complete tuples/promotions, and **0** promotion-eligible tuples;
authority, grounding, and reply outcomes are unchanged at **56/74**, recall
**0.28** / F1 **0.438**. This closes an audit-authority correctness defect,
not the underlying tuple-generation gate. No authorized complete tuple source
exists in the current 74-event run. Report:
[Phase 8 corpus](../../../evaluation/reports/phase8_corpus_report_20260926_phase4_authorized_sources_v1_event_context_v5.json).

### 2026-09-27 — Keep continuation family priors distinct from Phase 4 tuples

Live continuation proposals previously supplied zeroes for residual cost,
consequence, and novelty despite having no measurements for those dimensions.
They now use an explicit `authored_family_prior` valuation mode: those fields
remain absent, seed-authored family rules provide only expected-value priors,
and a separate native rule scores that prior for native Argmax. The generic
five-dimension scorer is restricted to complete Phase 4 tuples. Unknown
families fail closed; default materialization still rejects incomplete tuples.
Family-prior valuation rules are additionally mode-guarded, so they cannot
overwrite `expected_value` on a complete tuple. The focused Phase 4A/source
audit batch passes **31/31**, including a measured-tuple non-overwrite
negative control. Fresh Phase 8 v5 remains deterministic with authority
**56/74**, grounding precision/recall/F1 **1.00/0.28/0.438**, and **0**
complete/eligible/promoted tuples. Median/p95/max live latency is
**129.32/186.01/244.35 ms** (**21/74** over 150 ms). Two complete v5 raw runs
exist for Gemma 3 4B and Qwen 3.5 9B, but capability scorecards await blinded
annotation; both human reference classes remain missing. This removes
fabricated measurements but is not a Phase 4 tuple
producer or gate closure. Report:
[Phase 8 corpus](../../../evaluation/reports/phase8_corpus_report_20260927_prior_mode_isolation_v1.json).

### 2026-09-27 — Gate native instruction-gap reports before release

The native note_unhandled_instruction_gap rule already minted the
graph-authored reply and linked it to the inbound message, but omitted the
typed route consumed by the existing instruction release bridge. Three
substantive replies therefore escaped with no ProductionGateReceipt. The
rule now stamps self_improvement_route=filed_concern; the adapter performs
the delayed mechanical outcome pass, reads the same native reply, and releases
it only after structural readback of the reported gap and topic. Its receipt
records semantic_event=gap, semantic_intent=inform—not execution of the
requested action.

The Phase 6A production suite passes **17/17**. Fresh Phase 8 v5 has **43**
released substantive non-error replies and seven withheld diagnostic-error
receipts; the three formerly unreceipted instruction-gap reports each now
have exactly one released receipt bound to the same graph message and surface.
Other cases without receipts are explicit errors or deliberate silence.
Dispositions, grounding, and tuple
counts remain unchanged (authority **56/74**, grounding F1 **0.438**, Phase 4
complete/eligible/promoted **0/0/0**). Latency remains open at
**132.60/179.17/216.56 ms** median/p95/max, **24/74** over 150 ms. Report:
[Phase 8 corpus](../../../evaluation/reports/phase8_corpus_report_20260927_instruction_gap_receipt_v1.json).

The Phase 8 runner now includes a machine-readable production-release audit.
It requires an exact released receipt for every nonempty, non-diagnostic
surface and separately counts explicit errors and silence. The contract test
passes; the fresh v2 replay reports **43/43** substantive surfaces released,
seven explicit-error receipts withheld, 25 explicit errors, and six silent
events, with no unreleased substantive surfaces. Outcomes and cognition
metrics remain unchanged; latency remains open at
**138.10/201.86/234.07 ms** median/p95/max, **24/74** over. Report:
[Phase 8 corpus](../../../evaluation/reports/phase8_corpus_report_20260927_instruction_gap_receipt_v2.json).

### 2026-09-27 — Make the four-way grounding source audit replayable

The Phase 2 evaluator previously raised on the live, orthogonal status
authority_missing. It now classifies that *grounding observation* as unknown
when no referent path exists; permission authority remains separately recorded.
Phase 8 embeds the four-way source audit only for a validated fixed-corpus
run, and reports custom corpora as unavailable rather than forcing mismatched
denominators. The Phase 2/reference test batch passes **36/36**; the focused
Phase 8 integration and authority-missing tests pass **2/2**.

The updated 74-event source audit yields the same referent precision/recall/F1
**1.00/0.28/0.438**: **14/50** true positives and **36** false negatives,
with zero false positives. False-negative categories are
**14** declared-discourse-state paths, **11** declared graph paths, and
**11** surface/uncertainty-only cases; no unsupported event is promoted. The
next cognition step must supply actual event-linked graph evidence for those
categories or preserve the conservative unresolved result—corpus labels are
not runtime evidence. The audit is recorded in:
[Phase 8 grounding-source report](../../../evaluation/reports/phase8_corpus_report_20260927_grounding_source_audit_v1.json).

### 2026-09-27 — Scope audit for discourse-reference grounding

Following the source audit, traced the 14 discourse-state annotation misses
through `WorldAdapter._record_live_discourse_state`, the language-adapter
binding check, and `ReferenceResolutionEvidence`. The current binding check
accepts a graph-global `CurrentTopic` plus any in-focus `DiscourseReferent`;
neither is tied to the current event's `DiscourseState`/addressee. The legacy
reference evidence records a turn and surface but is not linked to a live
`DiscourseEvent`. This is not enough provenance to promote the annotated
misses, so no grounding or runtime behavior was changed. Phase 2U is added to
the execution plan: carry event scope to reference support, require same-scope
or event-linked evidence, and add positive plus cross-scope negative controls.
The fixed-corpus result remains **14/50** true positives, **36** false
negatives, zero false positives (F1 **0.438**).

### 2026-09-27 — Event-scoped discourse-reference seam

Phase 2U now passes live ingress scope (`DiscourseState`, speaker, and
addressee) into language adaptation. Anaphoric support requires a prior
grounded `DiscourseEvent.topic` in that same state and participant direction;
global `CurrentTopic`/referent salience no longer suffices. The Phase 2 source
classifier now recognizes only this scoped path (in addition to existing
held-answer/reference paths). Positive same-scope, unscoped, wrong speaker,
wrong addressee, and other-conversation controls pass. The complete Phase 2
measurement/reference batch passes **36/36**. An initial combined
language-neutral run exposed one fixture-only addressee assertion; after the
fixture correction, the standalone arbitration suite passes **33/33**. Fresh
Phase 8 v5 remains at **14/50** grounded referent true positives, zero false
positives (F1 **0.438**); therefore the 14 declared discourse-state corpus
misses remain unsupported and Phase 2U is not closed. Authority remains
**56/74**, Phase 4 complete/eligible/promoted **0/0/0**, substantive receipts
**43/43**, and latency **131.28/191.13/206.86 ms** median/p95/max
(**23/74** over 150 ms). Comparative evaluation remains blocked on
provenance/reference evidence. Report:
[Phase 8 event-scoped reference replay](../../../evaluation/reports/phase8_corpus_report_20260927_event_scoped_reference_v1.json).

The first replay exposed an ingress-ordering mismatch: before parsing, the
recipient helper selected the current interlocutor because the `received`
edge had not yet been written; the later discourse-event writer correctly
treated an inbound `Message` as addressed to the agent. Scope derivation now
uses the inbound Message origin, matching the event writer. This corrected
run resolves five same-scope discourse references, including
`question_followup`; grounding is **18/50** (precision **1.00**, recall
**0.36**, F1 **0.529**), with zero false positives. Full Phase 2
measurement/reference tests pass **36/36**, and the positive plus four
unscoped/cross-scope negative controls pass. Other gates remain open: authority
**56/74**, Phase 4 complete/eligible/promoted **0/0/0**, substantive receipts
**44/44**, latency **134.12/192.82/216.68 ms** median/p95/max (**27/74**
over 150 ms), and comparative status blocked at provenance. The 14
discourse-state misses are not all explained by this seam; Phase 2U remains
open. Report:
[Phase 8 event-scoped reference v2](../../../evaluation/reports/phase8_corpus_report_20260927_event_scoped_reference_v2.json).

The pre-parse scope lookup is now read-only: it reuses an existing
`DiscourseState` and returns no binding scope on the first event, leaving
state/common-ground creation to the normal event writer. A regression verifies
that the pre-pass creates no discourse nodes. The combined Phase 2
measurement/reference and language-neutral arbitration batch passes **70/70**.
Fresh v3 Phase 8 preserves **18/50** grounded referent cases (precision
**1.00**, recall **0.36**, F1 **0.529**) and five scoped reference paths, with
zero false positives; all 74 events complete without errors and all
substantive replies have receipts (**44/44**). Latency is **141.67/199.50/
226.41 ms** median/p95/max (**31/74** above 150 ms); no resource improvement
is claimed. The source audit's ten declared graph-path misses still have no
verified runtime evidence, so they remain unresolved. Authority **56/74**,
Phase 4 **0/0/0**, and comparative provenance remain open. Report:
[Phase 8 event-scoped reference v3](../../../evaluation/reports/phase8_corpus_report_20260927_event_scoped_reference_v3.json).

#### Phase 8A blinded output adjudication packet — 2026-09-27

Correction before annotation: Gemma seed outputs are exact matches (74/74),
but Qwen seed outputs match on only 1/74 cases. The v2 protocol and packet
retain the two Qwen seeds as distinct anonymous tracks and collapse only the
exact Gemma duplicate. Packet: 74 cases, five tracks/case, 370 unscored rows;
private key remains in `/tmp`. Builder regressions pass **2/2**. This is not a
score or a closed comparison: independent ratings, human classes, and
comparable memory/learning/provenance/cost evidence remain missing.

#### Phase 2T overlay measurement — 2026-09-27

Persisted the independent seven-case event-to-commitment overlay report at
[`proposition_event_commitment_measurement_20260927_phase2t.json`](../../../evaluation/reports/proposition_event_commitment_measurement_20260927_phase2t.json).
The report hashes its overlay and Phase 0 ID-registry inputs; it records 9/9
event identities, 1.00 materialization/status/consequence accuracy, 5/7
proposition provenance links, the expected supported consequence with
provenance, and 4/4 negative cases failing closed. Three focused tests pass.
This is isolated lifecycle evidence only: explicit typed uptake is injected
by the harness; autonomous live uptake, full-corpus grounding, and the broader
cognition gate remain open.

#### Phase 3B addressed common-ground proposition binding — 2026-09-27

Live neutral proposition ingress now links each materialized claim to the
existing discourse common-ground ledger for its addressed participant (or the
shared ledger when genuinely unaddressed). A two-addressee/same-conversation
regression verifies strict claim separation. Native goal-lifecycle test events
now carry their exact Goal identity. Proposition bridge plus Phase 3 exit
tests pass **14/14**. This closes only the addressee-ledger binding seam; it
does not change fixed-corpus grounding scores or establish world truth.

#### Full-boot latency call-path audit — 2026-09-27

A cProfile diagnostic across five slow corpus events attributes cumulative
work to 35 native rule calls (**0.198 s**), 90,958 native node readbacks
(**0.259 s**), 93,233 adapter-facade calls (**0.420 s**), and the
conceptualizer reply pipeline (**0.231 s**). These are profiler totals, not
latency estimates. A trial removing the subsequent-round native pass broke
commit/revision tests and the no-Python-decision audit; it was reverted. The
unchanged focused suite passes **11/11**. Preserve the native boundaries; next
measure their internal work or mechanical graph-readback cost.

#### Current-code connected-profile refresh — 2026-09-27

Fresh full-vs-connected structural parity is **74/74**, with zero errors and
complete 99-seed selection. Two independent all-event connected processes
pass resource assertions at **102,395,904** and **102,400,000-byte** peak RSS;
maximum latency is **136.72** and **142.18 ms**. A deterministic replay is
equal at **102,506,496-byte** peak and **149.96 ms** max. All are below the
100-MiB/150-ms bounds, but replay latency has only 0.04-ms headroom. Full-boot
latency remains open; the graph-ref plan still reports four unprovided refs.
See the current-v1 parity and three resource reports linked in the execution
plan.

#### Typed discourse-force adapter boundary audit — 2026-09-27

`tests/test_language_neutral_evidence_arbitration.py`,
`tests/test_live_discourse_deliberation_bridge.py`, and
`tests/test_phase8_corpus_runner.py` pass **77/77**. Native typed-force
arbitration is covered; corpus `offer` and `refusal` still arrive without
adapter force typing, and `social_question` is parsed only as an information
request. These are unresolved adapter-evidence gaps; no corpus labels or
surface-word rules were added. See the execution plan for scope and next work.

#### Execution-plan continuation-status correction — 2026-09-27

A current-source audit found the plan's executive section still describing the
pre-migration Python selector even though the later 2026-09-26 tracker entry
documents the complete candidate-family migration. The implementation now
proposes those families mechanically, with native Phase 4A valuation/collapse
and fail-closed selected-candidate release. The executive section now marks
the older diagnosis as superseded and keeps the actual remaining gates open:
zero complete Phase 4 tuples/promotions in the latest Phase 8 measurement,
legacy response authority, latency, production, and comparative evaluation.

#### Phase 4 upstream evidence-source audit — 2026-09-27

The latest Phase 8 v3 contains three event-bound partial-evidence records,
each with grounding only and none eligible for promotion. The live bridge
requires all five source dimensions before admitting a candidate. A source
inspection of the cognition domains found Phase 4 tuple consumers but no
conversation-specific upstream producers for expected value, residual cost,
or tuple novelty. Existing audience residual, future-option risk, and accepted
situation-change APIs have distinct semantics and are not silently recast as
Phase 4 fields. This changes the next implementation target: add/validate
candidate-specific upstream valuation evidence before extending the bridge.
The focused partial-evidence/native-deliberation suites pass **29/29**,
confirming that incomplete tuples remain ineligible; no new Phase 4 tuple is
claimed from this audit.

#### Conversation DecisionOption settle-back audit — 2026-09-27

`_record_conversation_decision()` uses a Python token-to-constant map for
`grounded_value`, counts each invocation as an experience, and performs
settle-back/depth calculation in the adapter. It has no production call sites;
only tests call it. The values are neither observed outcomes nor independent
expected-value evidence and must not enter Phase 4. Any live reactivation needs
native transition rules plus a provenance-bearing outcome/valuation source.
The legacy settle-back and Phase 4 boundary tests pass **3/3**; this confirms
current behavior and non-promotion, not valid outcome learning.

#### Outbound-message history lookup optimization — 2026-09-27

Added a maintained `Message.from` index for outbound history queries while
preserving node-ID ordering and live suppression reads. The conversation
reply/full-turn/loop tests pass **26/26**. A fresh 74-event v5 report is
outcome-identical to the preceding current report (reply, state, force, and
release status), with zero errors. cProfile counts: native-facade `invoke`
calls **1,837,130 -> 1,655,882** (-**9.9%**); total function calls -**3.3%**.
The report measures **121.32/202.65/218.71 ms** median/p95/max with
**19/74** over the 150-ms limit; authority remains **56/74**, grounding F1
**0.529**, and Phase 4 tuples/promotions **0/0**. This reduces historical
readback cost but leaves the full-boot latency/cognition gates open. Report:
[`Phase 8 v5 outbound-index run`](../../../evaluation/reports/phase8_corpus_report_20260927_outbound_message_index_v1.json).
The connected-profile replay also passes all resource assertions and is
deterministic (**102,371,328-byte** peak RSS, **119.17 ms** maximum event);
full-vs-connected parity is **74/74**, zero errors/mismatches. See the
[resource report](../../../evaluation/reports/phase7_profile_resource_20260927_outbound_message_index_conversation.json)
and [parity report](../../../evaluation/reports/phase7_seed_profile_parity_20260927_outbound_message_index_full74.json).

#### Indexed semantic Concept lookup — 2026-09-27

Replaced the per-question full Concept scan for modal semantic evidence with
the existing indexed lookup. The focused comprehension/neutral-arbitration
suite passes **73/73**. Compared with the immediately preceding indexed
outbound-history profile: graph-node reads **1,478,570 -> 845,755** (-**42.8%**),
adapter facade calls **1,655,882 -> 1,023,090** (-**38.2%**), and total
profiled function calls **32,944,552 -> 27,882,298** (-**15.4%**). The fresh
Phase 8 v5 report is event-outcome-identical, 74/74 with zero errors. It reports
**105.64/185.86/208.18 ms** median/p95/max, **10/74** over 150 ms, authority
**56/74**, grounding F1 **0.529**, and Phase 4 tuples/promotions **0/0**. The
connected replay passes resource assertions and is deterministic at
**102,449,152-byte** peak RSS and **125.11 ms** maximum; full-vs-connected
parity is **74/74**. Full-boot latency, cognition, Phase 4, production quality,
and comparative gates remain open. See the execution plan's linked reports.

#### Indexed self-dialogue Concept lookup — 2026-09-27

`self_dialogue._find_concept()` now uses the live exact-name Concept index
where supported and keeps the generic scan fallback. Focused tests pass
**25/25**; Phase 8 substantive outcomes match the prior indexed run across all
74 events with no errors. Current full-boot latency is **107.31/180.98/233.43
ms** median/p95/max (**11/74** over 150 ms), so that gate remains open. The
connected replay is deterministic, meets RSS bounds (**102,522,880 bytes**),
and has **111.60 ms** max event latency; full-vs-connected parity is **74/74**.
See the execution plan for report links.

#### Typed modal offer/refusal evidence — 2026-09-27

The English adapter now projects graph-backed first-person ability/inability
action frames to neutral `social_action`/`refusal` evidence; offer evidence
requires an existing target Concept. Focused tests pass **3/3**. Phase 8
authority coverage rises **56/74 -> 59/74** from force corrections on
`refusal`, `refusal_action`, and `offer_inspect`; the unsupported-target
`offer` stays unpromoted. No reply surface changes. Refusal dispositions and
offer production remain unresolved; grounding and
Phase 4 metrics are unchanged. Full-boot latency remains open
(**109.49/168.22/192.05 ms**, **12/74** over 150 ms), and the latest connected
max event is **154.65 ms** despite RSS/parity passes. The broader parity batch
has two open speech-act fixture failures (77 passed, 2 failed); see the
execution plan and linked evidence.

#### RuleSummary unchanged-body refresh fast path — 2026-09-27

The rule mirror now checks an exported-body hash before recomputing structural
summaries. The full self-model suite passes **15/15**; regression coverage
proves unchanged rules bypass tree walks while authored edits still remirror.
This improves repeated refreshes only; first materialization remains costly
(the preceding cProfile measured **6.78 s** in the first provenance pass), so
no latency gain is claimed. A fresh Phase 8 replay preserves all prior event
outcomes with zero errors. Latency remains over target (**110.84/173.35/206.86
ms**, **14/74** over 150 ms), authority is **59/74**, grounding F1 **0.529**,
and Phase 4 remains **0/0**. See the execution plan's replay link.

#### Current connected/full-profile revalidation — 2026-09-27

Fresh all-74-event connected-profile replay on the current worktree is
deterministic, error-free, and selection-complete; peak RSS is **102,645,760
bytes**, max turn latency **139.96 ms**, and all resource assertions pass.
Current full-vs-connected structural parity is **74/74** with zero mismatches.
The corresponding full-seed Phase 8 v5 replay is still blocked at
**109.70/177.17/232.37 ms** median/p95/max (**12/74** over 150 ms), grounding
F1 **0.507**, authority **59/74**, and **0/0** complete/eligible Phase 4
tuples. Full-boot latency, cognition/Phase 4, production quality, and human
comparative gates remain open. See the canonical execution plan's linked
replay artifacts.

#### Selected relation provenance transported to the graph — 2026-09-27

The adapter now preserves the selected parse's relation slots and POS/role
tags on `CommunicationInterpretation` as unverified provenance, filling the
existing predicate/object fields only when dispatch fields are absent. After
native comprehension, it projects only already-created Mention-to-Concept
links onto their parsed relation roles; lexical links do not imply world
instances. The full grounding/reference suite passes **37/37**; fresh Phase 8
has **0/74** event-outcome mismatches and no grounding promotion. Updated
connected replay is deterministic/error-free over **74/74**, selection-
complete, with **102,850,560-byte** peak RSS and **127.47 ms** max turn;
full-vs-connected parity is **74/74**, zero mismatches. Full-seed latency is
**106.68/173.79/211.80 ms**, **13/74** over 150 ms. This is a graph-
observability increment, not cognition-gate closure; release gates remain open.
See the canonical plan for linked reports.

#### Relation-role mention ambiguity guard — 2026-09-27

Relation-role Concept readback now requires a unique Mention for the parsed
surface within that message. Repeated/homographic surfaces are left unlinked
until occurrence-level provenance exists, avoiding cross-occurrence Concept
projection. Focused regression checks pass **3/3**; this does not change
grounding, replies, or capability scores. Phase 4, production, full-boot
latency, and comparative gates remain open. See the canonical execution plan.

#### Direct parse provenance on live discourse events — 2026-09-27

Live text `DiscourseEvent` records now link directly to the exact
`CommunicationInterpretation` already linked to their message. This aligns
live event graphs with semantic-event ingress and gives native event-scoped
retrieval an identity path without surface rebinding. The relation stays
`selected_parse_unverified`; this adds neither grounding nor world-truth
authority. Focused relation/event checks pass **3/3**. Corpus and release
outcomes have not been rerun; Phase 4, production, latency, and comparative
gates remain open. See the canonical execution plan.

#### Phase 6 test contract refresh for unsupported/non-turn information — 2026-09-27

Updated three stale assertions to match the graph-selected runtime contract:
an unsupported weather question with no provider remains an explicit error;
a `blocked` non-turn world question closes silently; and an unrelated held
answer cannot leak across either event. Turn-compatible native causal repair
still must pass its production receipt. The causal-retrieval, Phase 6
information-production, and unresolved-world bridge batch passes **27/27**.
This changes only regression expectations for established fail-closed behavior;
it adds no corpus capability or score. See the canonical execution plan.

#### Full-corpus check of event-linked parse provenance — 2026-09-27

Fresh Phase 8 v5 completed **74/74** events after the live event-to-
interpretation link. Relative to the preceding relation-projection run, the
74 observations are identical for reply, disposition, grounding status/path,
authority, and release status (**0/74** changes). Grounding is still
**17/50** (F1 **0.507**), authority **59/74**, and Phase 4 **0/0/0**
complete/eligible/promoted tuples. Full-run latency is **103.55/181.18/200.97
ms** median/p95/max, so the full-boot latency gate remains open. The three
previous candidate-grounded cases stay fail-closed because the event parse
edge supplies no missing referent, readiness, or permission evidence. Report
and case audit are linked from the canonical execution plan.

#### Event-bound attributed recall of a prior utterance — 2026-09-27

Added `communication_reported_content_recall`, selected by the connected
conversation profile. The English adapter contributes unique WordNet
morphology (`reports` -> `report`) and links the predicate to a unique
existing lexical Concept; the native rule compares normalized predicate
identity and exact subject/object relation slots. A reply is eligible only
for an immediately preceding same-speaker event with a selected,
unverified assertion/correction parse and matching relation structure. It
quotes the bounded source message as “Earlier, you said: …”;
`ReportedContentEvidence` records `attributed_source_utterance`, and
`grounding_status` remains `unresolved`. Production readback verifies the
event/message/evidence chain and issues a distinct receipt, without asserting
that the reported proposition is true.

Focused WordNet, Phase 6 production-bridge, and connected-profile tests pass
**20/20**. The fresh v5 Phase 8 replay completed **74/74**. Relative to the
event-interpretation-link report, exactly one observation changed:
`question_source` moved from repair/error to attributed answer/released reply;
the other **73/74** preserved reply, cognitive state, grounding, authority,
and release status. Authority is now **60/74**; grounding remains **17/50**
(precision **1.00**, recall **0.34**, F1 **0.507**), Phase 4 remains **0/0/0**
complete/eligible/promoted tuples, and the comparative release gate remains
blocked. This is narrow event-scoped utterance recall, not factual recall or
general cognition closure. Human comparison, Phase 4, latency, resource,
production-quality, learning/memory/cost gates remain open. Report:
[`reported-content-recall Phase 8`](../../../evaluation/reports/phase8_corpus_report_20260927_reported_content_recall_v1.json).

#### Connected-profile resource and full/connected parity recheck — 2026-09-27

The current 74-event connected conversation profile resolves its seed closure,
has zero errors, and deterministically replays. Its measured conversation
peak RSS is **100,319,232 bytes**, max turn latency **125.35 ms**, and
boot/event RSS growth **73,527,296 bytes**; the connected-profile resource
assertions pass. A fresh full-boot graph-reference pre-pass followed by the
matched comparison reports **74/74** matched events, zero structural
mismatches, complete connected selection, and zero errors. The initial
comparison without graph-reference replay was not valid parity evidence; it
omitted live graph-derived lexical references and has not been used for this
result. This closes only the current connected-profile bounded replay/parity
check. Full-boot latency/RSS, resource stability across repeated independent
runs, comparative human/LLM adjudication, Phase 4, and broader cognition and
production gates remain open. Reports:
[`connected resource replay`](../../../evaluation/reports/phase7_profile_resource_20260927_reported_content_recall_full74.json),
[`graph-reference full pre-pass`](../../../evaluation/reports/phase7_full_graph_refs_20260927_reported_content_recall_full74.json),
[`matched full/connected parity`](../../../evaluation/reports/phase7_seed_profile_parity_20260927_reported_content_recall_graph_refs_full74.json).

#### Revalidate attributed-recall release against source parse — 2026-09-27

Hardened `_release_reported_content_recall` to re-check the exact current and
source interpretation links, unverified selected relation schemas, shared
predicate/subject roles, source object, evidence relation/subject/content
fields, unresolved grounding status, adjacent same-speaker events, and exact
quoted source text before issuing a receipt. A tampered-evidence test confirms
the gate returns the explicit error and releases no receipt; positive and
relation/subject mismatch controls remain green (**4/4** focused reported-
content checks). The fresh Phase 8 replay has **0/74** changed reply,
cognitive-state, grounding, authority, or release outcomes relative to the
prior reported-content replay: the attributed `question_source` answer remains
released and unresolved, while the other cases remain unchanged. Authority
stays **60/74**, grounding F1 **0.507**, Phase 4 **0/0/0**, and the comparative
gate remains blocked. Report:
[`hardened reported-content Phase 8`](../../../evaluation/reports/phase8_corpus_report_20260927_reported_content_recall_readback_hardened_v1.json).

#### Graph-selected standalone farewell adjacency — 2026-09-27

The English boundary classifier now recognizes explicit farewell formulas and
the narrow complete cue “I am leaving now” as typed `farewell`; a longer
departure plan and a question remain statement/question controls. Added the
`farewell -> farewell` adjacency and a native arbitration rule that answers
only a non-turn standalone event already typed as `farewell`, leaving both
the cognition ontology and reply choice language-neutral. The ordinary
conversation reply faculty mints the second pair part, and the social
production gate releases it. Social production plus language-neutral
arbitration tests pass **46/46**. Fresh Phase 8 changes only `social_goodbye`:
error/assertion/unreleased becomes a native authoritative social answer with
a released receipt. Authority rises **60/74 -> 61/74**; grounding rises
**17/50 -> 18/50** with precision **1.00**, recall **0.36**, F1 **0.529** and
zero false positives. Phase 4 remains **0/0/0** and comparative acceptance
remains blocked. Refreshed connected 74-event resource replay is deterministic
with complete selection, **100,384,768-byte** peak RSS, **114.85-ms** max turn,
and **73,580,544-byte** boot/event growth. Matched full/connected replay has
**74/74** equality and no structural mismatches. Reports:
[`standalone farewell Phase 8`](../../../evaluation/reports/phase8_corpus_report_20260927_standalone_farewell_v1.json),
[`standalone farewell connected resources`](../../../evaluation/reports/phase7_profile_resource_20260927_standalone_farewell_full74.json),
[`standalone farewell full/connected parity`](../../../evaluation/reports/phase7_seed_profile_parity_20260927_standalone_farewell_full74.json).

#### Refresh blinded comparison artifact to current target — 2026-09-27

The current standalone-farewell Phase 8 target is now paired in a blinded
unscored annotation packet with the existing protocol-matched ELIZA, two
Gemma 3 4B, and two Qwen 3.5 9B runs. The packet covers **74 cases / 370
responses**, hides corpus labels and system names, randomizes per-case aliases,
and leaves all score fields empty; the provenance key is stored separately in
`/tmp`. Packet/raw-audit tests pass **10/10**. Human references remain missing
for both classes and no score interpretation has been performed, so this is
an annotation handoff, not comparative capability evidence. Artifact:
[`standalone-farewell blinded packet`](../../../evaluation/reports/phase8_blinded_output_packet_20260927_standalone_farewell_v1.json).

#### Typed ability-offer acceptance through graph adjacency — 2026-09-27

Implemented the bounded first-person ability-offer path. The boundary now
types an inbound offer as the existing graph `offer` act only when the
versioned selected parse has first-person ability-offer evidence and resolves
exactly one held Concept target. Native arbitration selects a social answer;
the existing `offer -> acceptance` graph adjacency and production receipt
control the released response. No execution authority is added. The
unresolved-target negative control remains a statement and produces no social
release. Focused tests pass **11/11**.

The latest Phase 8 target differs from standalone farewell in exactly two
cases (`offer`, `offer_inspect`): both now have released acceptance replies,
with `offer` also moving from error to authoritative answer. Totals are
**62/74** authoritative dispositions and **47** substantive releases;
grounding remains **18/50**, precision **1.00**, recall **0.36**, F1 **0.529**.
Phase 4 remains **0/0/0**. The connected resource replay completes with
**100,417,536-byte** peak RSS; independent max-turn readings of **151.17 ms**
and **114.51 ms** leave stable sub-150-ms latency unproven. Matched
full/connected parity is **74/74** with zero mismatches. A refreshed blinded
packet contains **74 cases / 370 unscored rows**; human-reference classes are
still missing and comparative acceptance is blocked. See the typed-offer
reports linked in the execution plan above.

#### Connected-profile latency tail attribution — 2026-09-27

Inspected each event sample in both independent connected 74-event profiles.
The **151.17-ms** maximum is `correction_world` with only **0.252 ms** of
instrumented external dispatch; the same event measured **97.95 ms** in the
repeat profile. The repeat's maximum is `error_signal` at **114.51 ms**.
This points away from remote retrieval as the cause but does not distinguish
in-process work from host scheduling or establish a reliable tail bound. RSS
assertions remain green at **100,417,536 bytes**, and profile parity is
**74/74**. Social production, language-neutral arbitration, and Phase 4
partial-evidence audit tests pass **55/55**. Stable latency, Phase 4 tuple
authorship, and comparative-human gates remain open.

#### Third independent connected resource sample — 2026-09-27

Ran the current 74-event conversation profile in a fresh process using the
validated graph-reference pre-pass. Selection completed with zero runtime
errors; peak RSS was **103,014,400 bytes**, within the 100 MiB bound, and
boot/event growth was **74,850,304 bytes**. Maximum turn latency was
**129.88 ms** (`error_signal`), making three independent maxima
**151.17/114.51/129.88 ms**. The first run's `correction_world` outlier remains
the sole threshold exceedance; its instrumented external dispatch was 0.252 ms
and it repeated at 97.95 ms. Stable latency acceptance remains open. The graph
pre-pass has complete provider scope but reports one expected unprovided
`Concept:blorf` reference in `offer_unknown`; connected seed selection still
completes without loading an unrelated provider. Artifact:
[`third connected resource sample`](../../../evaluation/reports/phase7_profile_resource_20260927_graph_offer_acceptance_third_full74.json).

#### Phase 4 live source-authority enforcement — 2026-09-27

The live bridge now admits a complete Phase 4 tuple only from a
`ThoughtManifold`-typed source, matching the approved-source contract in the
partial evidence audit. Previously any event-linked node with the five
numeric keys could be copied into a candidate, even if it was a generic
Concept or Relation. Positive coverage uses an explicit manifold source; a
complete tuple on a generic Concept remains native `no_candidate`. The
Phase 4 evidence-generation, partial-audit, and live-authority suites pass
**16/16**; live bridge plus continuation-selector regression subset passes
**29/29** (8 deselected).

The fresh 74-event Phase 8 replay is unchanged at **62/74** authoritative
dispositions and **47** substantive releases. Its only three Phase 4 sources
remain `topic_grounding`-owned and grounding-only; complete, eligible, and
promoted tuples are **0/0/0**. This closes the type-boundary mismatch but
does not close upstream cognition. Report:
[`Phase 8 source-authority recheck`](../../../evaluation/reports/phase8_corpus_report_20260927_phase4_source_authority_v1.json).

#### Diagnostic-only monitor bypass and connected resource recheck — 2026-09-27

The canonical `ERROR: no communicative response could be generated.` surface
is now excluded from communicative-intent/self-monitor parsing because it is a
diagnostic terminal, not an utterance. The exact-surface guard leaves
substantive answers, repairs, and noncanonical refusals on the existing
production path; a focused test verifies no intent is created for the
diagnostic. cProfile samples changed from **55** to **41** calls of
`conceptualize_reply()` and from **2.576 s** to **1.826 s** cumulative time.
The diagnostic test plus two normal-intent tests pass **3/3**; conversation
loop, migrated full-turn, and Phase 6A production gates pass **36/36**.

The new Phase 8 corpus report is unchanged in behavior: **62/74** authoritative
dispositions, **47** substantive releases, Phase 4 **0/0/0**; comparative
acceptance remains blocked. Three independent current-code connected
74-event profiles have max turns **113.05/142.09/99.70 ms**, RSS peaks
**102,748,160/102,891,520/102,842,368 bytes**, complete selection, zero errors,
and all resource assertions passing. Matched full/connected parity is
**74/74**, zero mismatches. The two remaining `test_conceptualized_converse`
failures were separately reproduced at this snapshot: audience-designed scene
description produced an unsupported-faculty ask-back, and the expected
`borogove` held answer was not available offline. The scene precedence issue
is fixed below; the retrieval-dependent assertion was made deterministic in a
later entry. Full-boot resources and reflex-specific bounds remain open.
Reports are linked in the execution plan.

#### Preserve selected scene-description faculty precedence — 2026-09-27

The reproduced scene-description failure was a precedence bug: a graph-authored
instruction response was released before the typed
`selected_self_account_faculty` evidence could reach the existing
`act_on_instruction` faculty; a later filed-concern gap check could also
override its result. The adapter now defers those two graph reply releases only
when that faculty is explicitly selected (and releases the later gap surface
only when no action faculty returned). This does not classify scene requests,
author language, or weaken the graph’s fallback for unsupported instructions.
The audience-designed scene regression now passes; adjacent Phase 6A
production and conversation-loop tests pass. In their combined run, **31
passed and 1 failed**: the remaining failure is the separate `borogove`
retrieval assertion. No held article is present in the seeds and the attempted
external retrieval fails on unavailable DNS. The test’s grounded-source
assumption is now isolated from this production/rendering regression by an
offline teacher fixture; see the follow-up below. Production acceptance is
still open.

#### Deterministic teacher evidence for rich-prose production regression — 2026-09-27

The rich-prose production test previously assumed a live Borogove lookup would
succeed, despite this environment's unavailable DNS and the absence of a
seeded article. It now injects a deterministic supported answer through the
existing `ground_topic` / `learn_from_teacher` boundary and still verifies the
released response plus its HeldAnswer grounding evidence. This retains the
production test's real graph/receipt/rendering path while leaving live source
retrieval to the dedicated topic-grounding suite. The rich-prose test and full
topic-grounding suite pass **32 passed, 1 skipped**. The skipped case and live
network retrieval remain unverified in this offline environment; broader
production acceptance remains open.

#### Audit authored HeldAnswer reachability — 2026-09-27

Booted `vision_science` contains ten authored `HeldAnswer` nodes, but they
carry only the `source: vision_science:1.0` provenance string: no
`grounding_referent`, `grounding_status`, `grounding_evidence_path`, or
`TopicGroundingEvidence`, and no `agent -holds_answer-> HeldAnswer` edges.
The current readback contract correctly rejects them (`_has_topic_grounding_evidence("vision") == False`,
`answer_about("vision") is None`); a live "What do you know about vision?"
therefore answers that it holds nothing despite the authored source content.
This is a real seeded-knowledge integration gap, distinct from unavailable
external retrieval. The free-form `source` string alone is not sufficient to
upgrade trust. The follow-up below carries explicit typed seed provenance into
the existing native topic-answer contract and verifies the unsupported-answer
control remains fail-closed.

#### Typed provenance and native release for authored vision answers — 2026-09-27

`seeds/vision_science.json` is now version **1.1.0**. Its ten authored
HeldAnswers explicitly identify `grounding_referent`, `grounding_status`, and
the seed-version evidence path; each has a typed `TopicGroundingEvidence`
node/`grounded_by` edge and an `agent -holds_answer-> HeldAnswer` edge. This
uses the authored seed as provenance rather than promoting a free-form source
label in runtime code. A live "What do you know about vision?" returns the
seeded text without external retrieval, resolves the `answer_topic` goal, and
records a recoverable `conversation_information_graph` production receipt.
The regression checks all of those facts; poisoned same-topic evidence remains
rejected. The authored-answer regression, scene-description regression,
poisoned-answer control, Phase 6 information-production suite, and seed suite
pass **33/33**.

The full `tests/test_topic_grounding_migrated.py` plus
`tests/test_phase2_grounding_reference_evidence.py` run also passes **69
passed, 1 skipped** on the updated full seed boot, so the new source edges do
not weaken the retrieval/referrer fail-closed controls.

Fresh Phase 8 remains behaviorally unchanged: **62/74** authoritative
dispositions, **47** substantive releases, grounded referent **18/50** (P=1.00,
R=0.36, F1=0.529), unrelated-answer violations **0**, Phase 4 **0/0/0**;
comparative release remains blocked at provenance. Current artifacts:
[`Phase 8 seed-grounding report`](../../../evaluation/reports/phase8_corpus_report_20260927_vision_seed_grounding_v1.json),
[`connected resource replay`](../../../evaluation/reports/phase7_connected_resource_20260927_vision_seed_grounding_v1.json),
[`full/connected parity`](../../../evaluation/reports/phase7_full_connected_parity_20260927_vision_seed_grounding_v1.json),
and [`graph-reference pre-pass`](../../../evaluation/reports/phase7_graph_reference_prepass_20260927_vision_seed_grounding_v1.json).
Connected selection and replay are complete/deterministic; its max turn is
**103.31 ms**, RSS peak **102,821,888 bytes**, and boot/event growth
**74,723,328 bytes**, with all resource assertions passing. Full/connected
parity is **74/74**, zero mismatches. Full-boot resources, the broader Phase 8
cognition/production gates, and comparative acceptance remain open.

#### Typed ability-offer follow-up — 2026-09-27

The follow-up separates offer force from target eligibility and blocks
acceptance-shaped fallback output when native cognition selects repair or
non-turn defer. The unknown-target offer now releases a graph-selected
clarification; incomplete non-turn offers have no response expectation or
surface. Phase 6 social production tests pass **10/10**. Phase 8 v5 now records
**52/74** exact force matches, **64/74** authoritative dispositions, and
complete receipt-backed substantive release (**48/48**, zero regressions).
Grounding is unchanged (**18/50**, F1=0.529), Phase 4 remains **0/0/0**, and
comparison is still blocked at provenance. Full language-neutral regression
coverage passes **39/39** after narrowing the guard. See the
[`canonical execution plan`](CONVERSATIONAL_MANIFOLD_EXECUTION_PLAN.md) and
[`typed-offer report`](../../../evaluation/reports/phase8_corpus_report_20260927_typed_offer_repair_v2.json).

#### Connected conversation daemon mode and current resource refresh — 2026-09-27

The daemon now exposes `--seeds conversation`, backed by the validated cached
dependency/content pre-pass and fail-closed selection. It preserves `full` as
the default and `chat` as a separate smoke profile. Daemon wiring and closure
tests pass **3/3**; the Phase 7 production-envelope module passes **20/20**.
Three independent current-code connected runs cover all 74 events without
errors: peak event latency **128.35–137.15 ms**, RSS **102.90–103.04 MB**, all
under the 150 ms / 100 MiB caps. Full/connected replay matches **74/74**.
An explicit full boot still exceeds strict limits (1.44 GB boot peak,
374.6 MB after events, 204.57 ms max event), so only the connected runtime
profile currently meets the resource contract. See the
[`canonical plan`](CONVERSATIONAL_MANIFOLD_EXECUTION_PLAN.md) for reports and
remaining gates.

#### Nonunderstanding report routed through native repair — 2026-09-27

The parsed first-person nonunderstanding report (“I did not understand that.”)
now transports typed repair evidence and reaches the graph-selected
clarification path. Its receipt-backed reply is “Might I ask which part was
unclear?”; third-person and positive controls do not inherit the repair act.
Focused Phase 6 and language-neutral transport checks pass **12/12**, and the
targeted end-to-end control passes. Fresh Phase 8 increases native-authoritative
dispositions to **65/74** and substantive receipt-backed releases to **49/49**,
with zero regressions. Force exact remains **52/74**, grounding **18/50**
(P=1.00, R=0.36, F1=0.529), and Phase 4 **0/0/0**; comparison remains blocked
at provenance.

Three current-code connected 74-event profiles pass all resource assertions:
peak RSS **103,055,360–103,104,512 bytes**, max event latency **116.81–135.87
ms**, complete selection and zero errors. Full/connected parity is **74/74**.
Current full boot still fails strict limits: **347,041,792-byte** boot/event
RSS growth, **373,854,208-byte** post-run RSS, and **197.71 ms** max event
latency. Reports:
[`nonunderstanding Phase 8`](../../../evaluation/reports/phase8_corpus_report_20260927_nonunderstanding_repair_v1.json),
[`connected run 1`](../../../evaluation/reports/phase7_profile_resource_20260927_nonunderstanding_repair_run1.json),
[`connected run 2`](../../../evaluation/reports/phase7_profile_resource_20260927_nonunderstanding_repair_run2.json),
[`connected run 3`](../../../evaluation/reports/phase7_profile_resource_20260927_nonunderstanding_repair_run3.json),
[`full boot`](../../../evaluation/reports/phase7_profile_resource_20260927_nonunderstanding_repair_fullboot.json),
and [`full/connected parity`](../../../evaluation/reports/phase7_full_connected_parity_20260927_nonunderstanding_repair.json).

#### Supplemental teacher-learning and delayed-memory probe — 2026-09-27

The frozen Phase 8 corpus does not exercise learning or repeated memory, so a
separate deterministic probe now checks pre-learning absence, typed teacher
grounding, receipt-backed answer release, persistence across an unrelated
turn, and delayed recall from the same `HeldAnswer`/`TopicGroundingEvidence`
pair. The pilot reports learning **1/1** and memory **1/1**; its end-to-end
test passes **1/1**. It is a mechanism check, not a population estimate, and
has no matched reference-model run. The frozen corpus scorecard remains
unchanged and the broad learning, memory, and comparative gates remain open.
See [`supplemental probe`](../../../evaluation/reports/phase8_memory_learning_probe_20260927_v1.json).

#### Blinded packet refreshed for current target — 2026-09-27

Rebuilt the unscored comparative packet from the current nonunderstanding
repair target and matched v5 reference runs. It covers **74 cases / 370
responses**, hides case labels and system names, randomizes aliases per case,
and has no scores filled in. Raw provenance is complete for ELIZA (**1/1**),
Gemma 4B (**2/2**), and Qwen 9B (**2/2**); base/advanced-human references are
still missing and score interpretation remains false. Comparative acceptance
is not closed. See [`current blinded packet`](../../../evaluation/reports/phase8_blinded_output_packet_20260927_nonunderstanding_repair_v1.json);
the private alias key is held under `/tmp` and not included in the packet.

#### Connected profile made the fresh-boot daemon default — 2026-09-27

Fresh daemon boots now default to the validated `conversation` connected
closure; `--seeds full` remains the explicit all-seed mode, `chat` remains the
smoke profile, and checkpoint-resume behavior is unchanged. This operational
change follows the measured envelope: a fresh 74-event conversation-profile
run completes selection with zero errors, passes every resource assertion,
and records **121.84 ms** max event latency, **103,063,552-byte** post-run RSS,
and **74,895,360-byte** boot/event growth. Focused default/closure tests pass
**3/3**. A real fresh `--once` launch without `--seeds` confirms the parser
selects `conversation` and loads the complete **71/71** connected seeds before
checkpointing. Full-boot acceptance remains open; this closes the
deployment-path mismatch, not the explicit full-profile gate. Report:
[`default connected resource run`](../../../evaluation/reports/phase7_profile_resource_20260927_connected_default_v1.json).
The async social bridge now releases the graph-selected `acceptance` for a
typed ability offer only under its native answer interpretation, through the
existing production gate. Its daemon regression and synchronous/unresolved
controls pass. The prior low-level honest-floor test had stopped before the
daemon release dispatcher even though cognition had selected a typed-offer
answer. It now verifies the complete async lifecycle, released social receipt,
and absence of action-execution receipts. The daemon-debug module is **17
passed, 1 failed**, with the remaining HTTP test unable to bind a socket under
this restricted runner (`PermissionError`).

#### Typed offer target contributes grounded referent evidence — 2026-09-27

The Phase 2 readback now grounds a typed first-person ability offer only when
its content-role action object resolves to an exact substantive graph Concept
and the adapter's independent offer-target evidence says `concept_available`.
This is evidence transport, not grounding from offer wording; the unresolved
target negative control remains unresolved. Fresh history-aware Phase 8
grounding moves **18/50→20/50** TP, **0** false positives, precision **1.00**,
recall **0.36→0.40**, F1 **0.529→0.571**. Both new true positives are the
supported gate/sensor offers; unknown `blorf` stays unresolved. Report:
[`offer grounding replay`](../../../evaluation/reports/phase8_corpus_report_20260927_typed_offer_grounding_v1.json).

#### Connected-profile envelope after grounding update — 2026-09-27

Three new independent fresh-process replays of all **74** events on the current
code complete seed selection, return zero errors, and pass every connected
resource assertion. Maximum event latency is **107.23/135.58/146.81 ms**;
peak RSS is **102,416,384/102,539,264/102,363,136 bytes**. The first run also
verifies replay determinism. This keeps the connected production path within
the measured 100 MiB / 150 ms envelope; full-boot and reflex-specific limits
remain open. Artifacts are linked from the canonical execution plan.

#### Multi-topic memory and learning evidence — 2026-09-27

The target-only supplemental probe now covers five distinct opaque topics,
not one. Each was absent before teaching; all were stored as separate typed,
grounded HeldAnswers; and all were answered again after five interleaved
retrievals plus two unrelated turns. Learning is **5/5**, delayed memory
**5/5**, with per-topic held-answer/evidence identity preserved and separate
release receipts. The test passes **1/1**. This does not provide a reference
model or population estimate; comparative learning/memory acceptance remains
open. Artifact: [`multi-topic probe`](../../../evaluation/reports/phase8_memory_learning_probe_20260927_multitopic_v2.json).

#### Blinded dual-rater intake and adjudication audit — 2026-09-27

The packet-bound rater utility now verifies both complete annotation files,
distinct rater IDs, five allowed score categories, required evidence notes,
and exact packet identity. It reports per-dimension nominal agreement and
Cohen's kappa; disputed rows remain unscored until a distinct adjudicator
resolves them. The tool does not read output text or the private alias key.
Its tests and the packet generator pass **6/6**. Blank 370-row forms for two
blind raters were generated from the current packet; target outputs in that
packet exactly match the fresh current replay (**74/74**). This remains
infrastructure only: no reviewed scoring rubric, rater responses, or
adjudication is yet present. See the Phase 8A evaluation note.

#### Current connected envelope and comparative intake — 2026-09-27

A fresh-process conversation-profile replay completes seed selection for all
74 events without errors. Boot-plus-event RSS growth is **73,814,016 bytes**,
peak RSS **100,511,744 bytes**, and maximum event latency **128.85 ms**; all
connected-profile resource assertions pass. This is current connected-mode
evidence, not full-boot or reflex-specific closure. Artifact:
[`fresh connected run`](../../../evaluation/reports/phase7_profile_resource_20260927_goal_resume_conversation.json).

The current raw v5 audit now has complete collection for ELIZA (1/1), small
LLM (2/2), and modern LLM (2/2); human reference classes are still missing
(0/1 each). Blinded packet/adjudication/raw-audit tests pass **20/20**. A
five-dimension response-rating rubric proposal has been drafted for external
approval; it is not approved, no annotations have been collected, and no
comparative capability result is claimed. The release gate remains blocked.

#### Connected common-object seed and grounding increment — 2026-09-27

The connected conversation seed closure now includes a curated WordNet-backed
`pump` concept before dialogue begins. The continuation is candidate-grounded
and selects the native `act` disposition, while the output correctly reports
that no execution faculty exists; unknown `blorf` stays unresolved. The
action-evidence suite passes **36/36**. Fresh Phase 8 grounding is **21/50 TP**,
**29 FN**, **0 FP** (precision **1.00**, recall **0.42**, F1 **0.592**), up one
TP without a false positive. A 74-event connected resource replay completes
with bounded RSS and full seed selection, but maximum latency is **183.23 ms**
on `info_unknown`, so the 150 ms limit is not met in this sample and needs
remeasurement. Authority remains **65/74**; Phase 4 tuple/promotion remains
**0/0**; comparative and release gates remain open. See the artifacts linked
in the execution plan.

#### Phase 7 instruction-route and parity expectation recheck — 2026-09-27

Reconciled stale regression expectations with current runtime evidence. The
unresolved connected `direct_action` retains an event-bound instruction goal
and releases only the honest `goal_only` response (no attached execution
faculty); it does not become grounded or executed. The scoped eight-event
profile comparison matches **5/8**, with only three `turn`-field differences.
Updated the tests; `tests/test_phase7_production_envelope.py` passes **20/20**.
The independent 74-event run remains over the latency ceiling (**167.26 ms**
maximum on `correction_world`) despite complete seed selection and passing RSS
assertions. The connected 150 ms latency gate is not closed. Profile artifact
and details are linked in the execution plan.

#### Full-seed v5 current-tree baseline — 2026-09-27

The current fixed 74-event Phase 8 replay measures **147.91/280.15/334.16 ms**
median/p95/max, with **36/74** turns over 150 ms. Grounding remains **21/50
TP**, **0 FP** (F1 **0.592**); authority is **65/74**; production has **49**
substantive releases, **16** explicit errors, and **9** authorized no-reply
slots; Phase 4 remains **0/0/0**. Comparative release is blocked at
provenance. A trace of the slow `social_address` event measured 344 ms under
profiling; its conceptualizer receipt shows three passes over two rounds. All
seven `run_rules` calls are attributed to those three passes, three full-graph
`comprehend()` passes, and one isolated scratch-graph speech-act classifier.
Six calls sweep the live graph, and none has been proven redundant. The
full-seed latency gate remains open. [Current report](../../../evaluation/reports/phase8_corpus_report_20260927_resume_live_tree_v1.json).

#### Provider-backed lexical prepass and loader API — 2026-09-27

The earlier no-content-key connected replay is not a full-vs-connected parity
test: it matched only **3/74** events because the connected closure omitted
lexical providers needed by typed routes. A signal-derived candidate set,
filtered against the cached seed content-provider index, selected **101** known
keys and their **116-seed** dependency closure. Full-vs-connected structural
parity is **74/74**, with no errors and no surface-text semantics. Two
independent connected resource runs select the same closure and agree
semantically; peak RSS is **103,522,304 / 103,436,288 bytes** (within the
100 MiB bound, narrow headroom), while maximum latency is **156.32 / 159.30
ms** (over the 150 ms bound). Full boot remains far beyond the memory limit.

Implemented the reusable `content_candidates` path in `load_all_seeds()` and
`load_conversation_seed_profile()`: candidates are resolved against the same
cached provider index used for closure selection; provider hits drive exact
selective content loading, while OOV candidates are reported separately and
do not invalidate closure. Explicit `content_keys` retain strict behavior.
The regression test proves exact provider slicing, dependency closure, and OOV
retention. This makes the prepass mechanism reusable, but does **not** yet
connect a runtime language adapter to candidate generation or close the
latency/full-boot gates. See [resolved-key parity](../../../evaluation/reports/phase7_seed_profile_parity_20260927_active_tree_resolved_lexical_prepass.json)
and [resource run 1](../../../evaluation/reports/phase7_profile_resource_20260927_active_tree_resolved_prepass_v1.json).

#### Ingress-shared candidate generation closes connected latency — 2026-09-27

Replaced the manually tokenized candidate experiment with candidate
generation that calls the same mechanical mention tokenizer as live message
ingress. The tokenizer supplies lexical candidates only; the cached seed
provider map filters them, and native graph rules retain all referent,
interpretation, and disposition authority. Corpus labels are not read. The
full Phase 0 comparison is **74/74 structurally equal**, with zero errors,
complete selection, and no surface-text semantics. The pre-pass considered
**150** candidate forms, resolved **99** provider-backed forms, retained **51**
OOV forms as unresolved, and selected the **116-seed** connected closure.

Two independent fresh-process 74-event runs completed with zero errors and
identical semantic observation digests across both runs and the comparison.
Peak RSS was **103,415,808 / 103,383,040 bytes** (under the 100 MiB ceiling,
with narrow headroom); maximum turn latency was **132.64 / 123.43 ms**, now
within the 150 ms bound. All connected resource assertions pass. This supersedes
the preceding manually tokenized prepass result (**156.32 / 159.30 ms**); using
the exact ingress tokenizer both removes that latency miss and makes candidate
generation reproducible. It does not close the separate full-boot RSS failure
or cognition, production, Phase 4, authority, and human-comparison gates.
The 150 candidates are aggregated over the fixed replay batch before profile
boot; this verifies a connected corpus prepass, not yet incremental candidate
resolution for an open-ended daemon conversation.
Verification: `tests/test_phase7_production_envelope.py` passes **21/21**;
`tests/test_seed_loader_quiet_boot_migrated.py` passes **18/18**; ingress-token
equivalence and the simplified eight-event/full-profile parity regression also
pass. The first Phase 7 run caught two historical under-provisioned
expectations; those now assert provider-grounded parity without conflating it
with execution authority.
Artifacts: [full-vs-connected parity](../../../evaluation/reports/phase7_seed_profile_parity_20260927_ingress_candidate_prepass_v1.json),
[resource run 1](../../../evaluation/reports/phase7_profile_resource_20260927_ingress_candidate_prepass_v1.json),
[independent repeat](../../../evaluation/reports/phase7_profile_resource_20260927_ingress_candidate_prepass_repeat2.json).

#### Current connected resource envelope — 2026-09-27

The ordinary interpreter run remains above the 100-MiB absolute RSS cap.
After moving optional transport imports to their I/O paths, a reproducible
host-specific profile using `PYTHONMALLOC=malloc`, `MALLOC_ARENA_MAX=1`, and
`MALLOC_TRIM_THRESHOLD_=32768` passes all resource assertions on glibc 2.39:
two fresh 74-event runs select all 96 seeds with zero errors, exact semantic
observation parity, peaks **104,517,632 / 104,321,024 bytes**, and maximum
turn latencies **114.78 / 140.41 ms**. Loader and Phase 7 suites pass **46/46**
under the same environment. This closes connected-corpus resources on this
host/configuration only; portability and full-boot memory remain open. The
cognition, production/authority, Phase 4, and comparative-evaluation gates
remain open. Detailed constraints and artifacts are in the
[execution plan](CONVERSATIONAL_MANIFOLD_EXECUTION_PLAN.md).

#### Graph-typed communicative failure — 2026-09-27

Preserved the seed concept `kind` field and made semantic concept lookup prefer
typed duplicates over earlier thin lexical nodes. The adapter now emits
`communication_failure` only when a typed speech-function subject occurs with
a graph-typed deficiency predicate; native arbitration maps the evidence to
`error`. The ordinary inability negative control remains unclassified. Tests
pass **98/98** across the focused adapter, neutral arbitration, and Phase 8
audit/packet modules. A fresh 74-event replay raises native disposition
authority **67/74→68/74**; the `error_signal` case now has authoritative
`error`. Grounding remains **21/50 TP, 29 FN, 0 FP**, and the release gate is
still blocked. Report:
[typed-failure replay](../../../evaluation/reports/phase8_corpus_report_20260927_typed_failure_v1.json).

#### Continuation assertion disposition — 2026-09-28

Native communication arbitration now defers adapter-typed assertions in a
turn-compatible continuation slot without endorsing proposition content. The
language-neutral arbitration and adapter suites pass **79/79**. Fresh Phase 8
replay confirms `continuation_answer` is `defer` with native graph readback;
authority coverage rises **68/74→69/74**. Five non-authoritative cases remain.
Grounding remains **21/50 TP, 29 FN, 0 FP** and the release gate stays blocked.
See the [replay](../../../evaluation/reports/phase8_corpus_report_20260928_continuation_disposition_v1.json)
and [implementation notes](CONVERSATIONAL_MANIFOLD_EXECUTION_PLAN.md).

#### Turn-compatible missing-authority readback — 2026-09-27

The fixed `info_choice` event is now graph-authoritatively `blocked` when its
typed request carries explicit missing authority, rather than an unclassified
error disposition. The production boundary still withholds its unsupported
recommendation. Phase 6/Phase 2/Phase 8 suites pass **58/58**; fresh 74-event
authority coverage rises **66/74→67/74**. Expected-answer mismatch, grounding,
production, Phase 4, and comparative gates remain open. See the
[current Phase 8 report](../../../evaluation/reports/phase8_corpus_report_20260927_missing_authority_readback_v1.json)
and [execution plan](CONVERSATIONAL_MANIFOLD_EXECUTION_PLAN.md).
Fresh full/connected replay is **74/74** equal, zero errors or mismatches; the
connected resource profile also passes at **104,423,424-byte** peak RSS and
**128.46 ms** max latency under the documented glibc settings. Reports:
[parity](../../../evaluation/reports/phase7_seed_profile_parity_20260927_missing_authority_rule_v1.json),
[resource](../../../evaluation/reports/phase7_profile_resource_20260927_missing_authority_rule_v1.json).

#### Attributed-source cognition evidence — 2026-09-27

Added a separate graph-resident evidence path for successfully released
reported-content recall. The Phase 8 trace identifies the verified source
message/event chain while retaining `grounding_status=unresolved`, preventing
attributed speech from being treated as world truth. Focused production,
Phase 2, and Phase 8 tests pass **57/57**; the fixed 74-event replay verifies
the `question_source` path, with grounding F1 unchanged at **0.592**. The
cognition/grounding, production/authority, Phase 4, and comparative gates
remain open. Details and fresh evidence:
[Phase 8 report](../../../evaluation/reports/phase8_corpus_report_20260927_reported_source_path_v1.json),
[execution plan](CONVERSATIONAL_MANIFOLD_EXECUTION_PLAN.md).

#### Graph-typed communicative failure — 2026-09-27

Preserved the seed concept `kind` field and made semantic concept lookup prefer
typed duplicates over earlier thin lexical nodes. The adapter now emits
`communication_failure` only when a typed speech-function subject occurs with
a graph-typed deficiency predicate; native arbitration maps the evidence to
`error`. The ordinary inability negative control remains unclassified. Tests
pass **98/98** across the focused adapter, neutral arbitration, and Phase 8
audit/packet modules. A fresh 74-event replay raises native disposition
authority **67/74→68/74**; the `error_signal` case now has authoritative
`error`. Grounding remains **21/50 TP, 29 FN, 0 FP**, and the release gate is
still blocked. Report:
[typed-failure replay](../../../evaluation/reports/phase8_corpus_report_20260927_typed_failure_v1.json).

#### Typed action availability — 2026-09-28

Added graph-typed availability semantics for action states and a native
response-slot rule that blocks a negatively available action without surface
phrase matching. The language adapter requires both a typed dynamic-action
subject and a typed availability-state predicate; a signal-state control stays
unclassified. The adapter and language-neutral arbitration modules pass
**80/80**. Fresh Phase 8 replay makes `refusal_unknown` graph-authoritatively
`blocked`; coverage rises **69/74→70/74**. Four unresolved cases remain, and
grounding/Phase 4 gates are unchanged. See the
[report](../../../evaluation/reports/phase8_corpus_report_20260928_action_availability_v1.json)
and [execution record](CONVERSATIONAL_MANIFOLD_EXECUTION_PLAN.md).

The post-change connected-profile resource repeat also passes on the documented
glibc configuration: two independent 74-event runs select the same 96-seed
closure, produce identical stable observations with zero errors, and measure
peak RSS **104,067,072 / 104,275,968 bytes** and max event latency
**133.85 / 137.23 ms**. This is host/configuration-specific, not full-boot
proof. Reports:
[run 1](../../../evaluation/reports/phase7_profile_resource_20260928_action_availability_run1.json),
[run 2](../../../evaluation/reports/phase7_profile_resource_20260928_action_availability_run2.json).

The explicit full-seed profile was also measured with the same host settings:
zero event errors, but **1,411,518,464-byte** peak RSS, **424,574,976-byte**
post-run RSS, **397,328,384-byte** boot/event growth, and **201.65 ms** maximum
event latency. RSS peaked by the end of the **13.73 s** full boot; graph size
was **24,858→27,911** nodes. This confirms that the connected-profile pass does
not close the full-boot gate; seed materialization is the next resource target.
See the [full-boot report](../../../evaluation/reports/phase7_profile_resource_20260928_action_availability_fullboot.json).

The full language-neutral arbitration module passes **44/44**. Native
arbitration now defers unresolved action requests in non-turn response slots.
The new rule changes only `response_yes`: route-derived
`act` is replaced by graph-authoritative `defer`, raising authority
**70/74→71/74** and reducing matched-but-unauthoritative states to **0**. This
is fail-closed behavior, but the fixture expects `act`, so state agreement is
now **66/74**; do not describe it as an accuracy improvement. Three cases still
lack native disposition authority. See the [replay](../../../evaluation/reports/phase8_corpus_report_20260928_unresolved_response_action_v1.json)
and [rule record](CONVERSATIONAL_MANIFOLD_EXECUTION_PLAN.md).

The connected-profile envelope was repeated after the rule on the exact
current tree: identical stable observations, zero errors, complete same
96-seed selection, and all assertions pass. The two independent 74-event runs
measured **104,300,544 / 104,161,280 bytes** peak RSS and **134.78 / 126.73 ms**
max event latency. The full-boot memory result remains open. Reports:
[run 1](../../../evaluation/reports/phase7_profile_resource_20260928_response_action_run1.json),
[run 2](../../../evaluation/reports/phase7_profile_resource_20260928_response_action_run2.json).

#### Uncertain selected-information gap — 2026-09-28

The adapter now transports graph-typed epistemic uncertainty on a selected
information gap into the authoritative communication interpretation, and
native arbitration creates a source-constrained learning request for a
turn-compatible response. The bridge fix was needed because the adapter had
emitted uncertainty evidence but the graph record previously retained only an
ingress uncertainty flag. Focused adapter/arbitration tests pass **2/2**. A
fresh 74-event replay makes `learn_uncertain` authoritatively `learn` and binds
an `InformationLearningRequest` to the event and the typed `reading` topic;
retrieval was not executed and answer authority remains `none`. Coverage rises
**71/74→72/74**, fixture-state agreement **66/74→67/74**. Grounding remains
**21/50 TP, 29 FN, 0 FP**; production and Phase 4 counts are unchanged. Two
cases lack native disposition authority: `social_question` and `learn_result`.
The release gate remains blocked, including full-boot resources and human
comparative evaluation. See the [fresh replay](../../../evaluation/reports/phase8_corpus_report_20260928_uncertain_learning_gap_v2.json)
and [execution record](CONVERSATIONAL_MANIFOLD_EXECUTION_PLAN.md).

The exact current tree was also rerun twice through the 74-event connected
conversation profile. Both runs selected the complete closure, had zero event
errors, and passed every configured resource assertion. Peak RSS was
**104,300,544 / 104,423,424 bytes** and maximum event latency was
**106.35 / 114.79 ms**. This confirms the bounded conversation profile under
the documented glibc allocator settings; the separate full-seed boot still
exceeds its strict resource envelope. Reports:
[run 1](../../../evaluation/reports/phase7_profile_resource_20260928_uncertain_bridge_run1.json),
[run 2](../../../evaluation/reports/phase7_profile_resource_20260928_uncertain_bridge_run2.json).

The complete affected adapter/arbitration suites pass **82/82** on this tree
(`tests/test_action_evidence_and_defer.py` and
`tests/test_language_neutral_evidence_arbitration.py`, 596.88 s). The local
Ollama executable is installed, but the sandbox cannot connect to its API at
`127.0.0.1:11434`, so no new model run was collected. Existing protocol-matched
v5 LLM observations remain available as raw, unscored references; comparative
scores remain unavailable rather than inferred.

#### Current-tree profile parity and blinded packet refresh — 2026-09-28

The fresh full-vs-connected 74-event profile comparison is structurally equal
**74/74**, with zero errors in both profiles and complete connected seed
selection. Surface text is not used as semantics and graph identity IDs are
excluded from equality. Report:
[profile parity](../../../evaluation/reports/phase7_seed_profile_parity_20260928_uncertain_bridge_v1.json).

The latest v5 target replay was then bound to the existing complete raw ELIZA,
Gemma 3 4B CPU (two seeds), and Qwen 3.5 9B CPU (two seeds) outputs in a fresh
blinded packet: **74 cases / 370 responses**, randomized per-case aliases,
no corpus/system labels, and no scores. Packet-bound A/B templates each have
370 empty annotation rows and share the packet SHA-256. The private alias key
is only in `/tmp`. This refresh makes the latest target response set
annotation-ready; human references, approved rubric, ratings, and adjudication
remain missing. Artifacts:
[packet](../../../evaluation/reports/phase8_blinded_output_packet_20260928_uncertain_bridge_v1.json),
[rater A](../../../evaluation/reports/phase8_blinded_rater_template_20260928_uncertain_bridge_a.json),
[rater B](../../../evaluation/reports/phase8_blinded_rater_template_20260928_uncertain_bridge_b.json).

The protocol-aware raw-reference audit was refreshed against those same five
v5 files: ELIZA **1/1**, small LLM **2/2**, modern LLM **2/2**, and both human
classes **0/1**. It reports **3 complete raw classes / 2 missing**, performs no
score interpretation, and remains `incomplete`. Artifact:
[raw-reference audit](../../../evaluation/reports/phase8_raw_reference_audit_20260928_uncertain_bridge_v1.json).

The comparative evaluation record now also captures the extant protocol-v5
Gemma 3 4B CPU request timings and the target's synchronous adapter timing as
raw cost observations. They use different measurement boundaries (full
generation request vs. adapter call excluding post-turn audit), so no
efficiency or capability comparison is inferred. Target median/p95/max is
88.59/164.32/203.80 ms (5/74 over 150 ms); CPU Gemma mean request time is
4.34/4.29 s across its two 74-case seeds. This does not close cost scoring,
human-reference comparison, full-boot resource, or production-latency gates.
See the [comparative evaluation record](CONVERSATIONAL_MANIFOLD_PHASE8A_COMPARATIVE_EVALUATION.md#raw-operational-cost-observations--2026-09-28).

Latest cognition increment: embedded finite propositions now remain distinct
selected-but-unverified graph relations, with concept links only from unique
event mentions. `learn_result` receives native `defer` and an acknowledgment
without endorsement; its fixture still expects `learn`, so the cognition case
remains disputed and ungrounded. Graph-typed epistemic-modality evidence also
restores native repair for `correction_uncertain`. Current full replay:
authority **72/74**; unresolved `info_choice` and `social_question`; **50**
substantive releases, **14** explicit errors, **10** authorized silent slots;
grounding **21 TP / 29 FN / 0 FP**; Phase 4 **0/0/0**. Synchronous call latency
is median/p95/max **104.03/180.47/207.81 ms**, with **15/74** over 150 ms, so
the production-latency gate remains open. See the
[execution record](CONVERSATIONAL_MANIFOLD_EXECUTION_PLAN.md#embedded-proposition-capture-and-parser-regression-repair--2026-09-28)
and [fresh replay](../../../evaluation/reports/phase8_corpus_report_20260928_embedded_relation_capture_v6.json).
On the exact current tree, the 74-event connected profile also passed all
resource assertions with complete seed selection, zero errors, deterministic
replay, 104,161,280-byte peak RSS, 77,004,800-byte boot/event RSS growth, and
118.34-ms maximum event latency. Full-seed boot remains above 1.4 GB; the
separate Phase 8 synchronous-call p95/max latency still exceeds 150 ms. See
the [connected-profile rerun](../../../evaluation/reports/phase7_profile_resource_20260928_embedded_relation_capture_v1.json).
The final affected action/defer and language-neutral arbitration regression
pair passes **82/82** on this tree (596.42 s); no outstanding failure remains
from the parser-adjustment suite.

#### Polar action-topic routing — 2026-09-28

The parsed relation for “Should we use the north route?” was correct
(`use(we, route)`), but generic question-topic selection chose the actor
(`we`) and dispatched `ask_world:we`. Polar verb frames with a direct object
now select that object as the lookup topic while preserving the actor and
predicate in the relation. Focused parser/router tests pass **5/5**. A live
connected-profile turn now targets `route`, but still yields no communicative
response; the event has no native cognitive disposition and no decision
authority. This fixes topic selection only; it does not authorize a route
recommendation. `info_choice` remains an open cognition/release gate, and the
latest full-corpus counts above predate this local routing change. The next
work is to establish a graph-backed, event-scoped disposition for advice or
decision requests, or an honest defer, without treating lexical concept
grounding as decision authority.

#### Typed decision-authority capture — 2026-09-28

The current graph already types `should` as a modal of obligation/expectation,
but the adapter previously only treated permission-style modal concepts as
authority evidence. It now recognizes a typed obligation/expectation modal in
an actor–action question frame and records neutral authority-request evidence.
Native arbitration consumes the resulting event-scoped `authority_status`,
not the English token or the route concept: it selects `blocked` with
`missing_permission_authority` while the route referent remains
`candidate_grounded`. No recommendation is released. The companion permission
case remains blocked; its object now reads `candidate_grounded`, independently
of missing authority. Focused regressions pass **7/7**.

The fresh full Phase 8 v5 replay reports disposition authority **73/74**;
`info_choice` is now authoritative but still mismatches its expected `answer`
state and retains a withheld diagnostic error surface. `social_question` is
the remaining non-authoritative cognition event. Grounding is **22 TP / 28 FN
/ 0 FP** (F1 **0.611**), substantive releases **50**, explicit errors **14**,
authorized silent slots **10**, and Phase 4 source/complete-tuple/promotion
counts **3/0/0**. Synchronous latency is median/p95/max
**90.26/167.80/198.35 ms** (**12/74** over 150 ms), so that production gate is
still open. Comparative evaluation remains provenance-blocked. Evidence:
[typed-decision-authority replay](../../../evaluation/reports/phase8_corpus_report_20260928_typed_decision_authority_v1.json).

#### Unresolved turn-compatible question disposition — 2026-09-28

The other former authority gap, `social_question`, had a complete interrogative
frame, `authority_status=not_applicable`, and unresolved grounding, but no
graph-linked predicate Concept for the specific learning-request rule. A
language-neutral native fallback now selects `repair` for complete
turn-compatible information requests only when grounding is unresolved, no
anaphor is active, and no disposition has already been chosen. It does not
mint an answer commitment. The matched test passes, including a preceding
route-decision turn; seed JSON validates and `git diff --check` is clean.

Fresh 74-event Phase 8 replay now has authoritative disposition coverage
**74/74** with zero label matches lacking authority. `social_question` reads
native `repair`, while the fixture expects `answer`; it remains unresolved and
its current output is still a withheld diagnostic error. Grounding and
production remain **22 TP / 28 FN / 0 FP (F1 0.611)** and **50 releases / 14
errors / 10 authorized silences**; Phase 4 remains **3 sources / 0 complete
tuples / 0 promotions**. Latency is median/p95/max
**88.07/175.21/203.47 ms**, **12/74** over 150 ms. Evidence:
[unresolved-information Phase 8 replay](../../../evaluation/reports/phase8_corpus_report_20260928_unknown_info_repair_v1.json).
The exact-tree 74-event connected-profile resource/replay rerun also passes
all configured assertions: complete seed selection, zero event errors,
deterministic replay, **104,255,488-byte** peak RSS,
**77,078,528-byte** boot/event RSS growth, and **130.05-ms** maximum event
latency. This is connected-profile evidence only; the separate full-seed boot
memory gate remains open. Report:
[connected-profile rerun](../../../evaluation/reports/phase7_profile_resource_20260928_unknown_info_repair_v1.json).

#### Context-grounding clarification release — 2026-09-28

The native repair for `social_question` previously fell through to the
diagnostic error because the production bridge only rendered repairs with a
specific lexical/reference focus. A register-aware `inquire_context` surface
and a route guarded by the native
`unresolved_turn_compatible_information_request` basis now produce a
clarification (“Might I ask what information would ground an answer?”) through
the existing action production gate. It makes no readiness claim and creates
no answer commitment. The focused end-to-end arbitration/production test
passes and verifies a released turn-bound receipt.

The fresh Phase 8 v5 replay preserves native repair and unresolved grounding,
but moves `social_question` from an error to a released clarification.
Disposition authority remains **74/74**, releases/errors/silent slots are
**51/13/10**, grounding **22 TP / 28 FN / 0 FP (F1 0.611)**, Phase 4
**3 sources / 0 complete tuples / 0 promotions**, and latency is median/p95/max
**90.22/174.29/192.44 ms** (**10/74** over 150 ms). The exact-tree connected
resource profile passes every configured assertion with deterministic replay,
complete selection, zero errors, **104,075,264-byte** peak RSS,
**76,832,768-byte** boot/event growth, and **135.53-ms** max event latency.
Full-seed memory, p95 latency, `info_choice` release, Phase 4 promotion, and
human comparison remain open. Reports:
[Phase 8 replay](../../../evaluation/reports/phase8_corpus_report_20260928_contextual_repair_release_v1.json),
[connected resource replay](../../../evaluation/reports/phase7_profile_resource_20260928_contextual_repair_release_v1.json).

#### Decision-context clarification and bounded cognition advance — 2026-09-28

The first blocked-decision clarification attempt exposed a scheduler-ordering
gap: the response bridge read `cognitive_disposition` before native
authority arbitration had completed its bounded quantum. The adapter now
advances at most two graph quanta for typed decision-recommendation requests,
re-reading the interpretation after each; no disposition is inferred by the
adapter. Once native cognition selects `blocked` with missing authority, a
register-aware question asks what information should guide the decision.
`info_choice` remains blocked and has no answer commitment, but now receives
a released clarification receipt. `social_question` likewise retains native
repair and its released grounding clarification. Targeted blocked-authority,
permission, and repair tests pass; the focused route test verifies the
clarification speech act and absence of an answer commitment.

Fresh Phase 8 replay: native authority **74/74**; replies/errors/authorized
silence **52/12/10**; both `info_choice` and `social_question` are released
clarifications whose expected `answer` labels remain mismatched. Grounding is
**21 TP / 29 FN / 0 FP (F1 0.592)** because `info_choice` now correctly reads
`authority_missing` rather than treating the route Concept as decision
evidence. Phase 4 remains **3/0/0**. Latency is median/p95/max
**93.96/179.92/187.74 ms**, with **9/74** above 150 ms. The exact-tree
connected resource/replay run passes all configured assertions: complete
selection, zero errors, deterministic replay, **104,128,512-byte** peak RSS,
**76,939,264-byte** boot/event growth, and **147.17-ms** maximum event
latency. Full-seed boot, p95 latency, Phase 4 promotions, and human comparative
evaluation remain open. Evidence:
[Phase 8](../../../evaluation/reports/phase8_corpus_report_20260928_decision_context_release_v1.json),
[connected profile](../../../evaluation/reports/phase7_profile_resource_20260928_decision_context_release_v1.json).

#### Deferred response-slot closure — 2026-09-28

Two native `defer` events in a turn-compatible continuation/overlap boundary
were incorrectly emitted as diagnostic errors. They now close silently when
the graph-selected state is `defer` and the interaction is a continuation or
an overlapping fragment. Non-turn deferred instructions still use their
deferred-action production path; regression coverage confirms the deferred
hatch instruction retains its released response. Phase 8 accounting now
recognizes these silences only from authoritative disposition plus interaction
relation/form. Focused tests pass **5/5** across the no-reply evaluator, the
two new turn-boundary cases, and the deferred-action control.

Latest full replay: dispositions **74/74**; **51** released substantive
replies, **10** explicit errors, **13** authorized silences, **0** unclassified
silences; grounding **21 TP / 29 FN / 0 FP (F1 0.592)**; Phase 4 **3/0/0**.
Latency median/p95/max is **98.17/158.77/206.51 ms**, with **10/74** over
150 ms. The connected-profile resource rerun passes all assertions with
deterministic replay, complete seed selection, zero errors,
**104,026,112-byte** peak RSS, **76,857,344-byte** boot/event growth, and
**122.25-ms** maximum event latency. Full-seed memory, max/p95 production
latency, response-label agreement, Phase 4 promotions, and human comparison
remain open. Reports:
[Phase 8 v4](../../../evaluation/reports/phase8_corpus_report_20260928_deferred_turn_silence_v4.json),
[connected resource profile](../../../evaluation/reports/phase7_profile_resource_20260928_deferred_turn_silence_v1.json).

#### Unanswered learning-request clarification and exact-tree recheck — 2026-09-28

When native cognition selects `learn` for a turn-compatible interrogative but
has no grounded answer topic, production now asks what information or context
would ground an answer. The surface is routed through the existing
clarification production gate and does not repeat the unsupported topic or
create an answer commitment. The focused learning-clarification test and the
deferred-silence/release-accounting tests pass (**3/3**).

Fresh Phase 8 v5 replay: native disposition authority **74/74** with no label
matches lacking authority; **53** released substantive replies, **8** explicit
errors, **13** authorized silences, and **0** unclassified silences. Grounding
is **21 TP / 29 FN / 0 FP (F1 0.592)**; Phase 4 remains **3 source events / 0
complete tuples / 0 promotions**. Latency median/p95/max is
**96.28/169.87/191.20 ms**, with **9/74** over 150 ms. `learn_uncertain`
remains an unresolved declarative learning event and is intentionally not
silently converted into the interrogative clarification route. Reports:
[Phase 8 replay](../../../evaluation/reports/phase8_corpus_report_20260928_learning_context_clarification_resume_v2.json).

Two independent exact-tree connected-profile runs select the complete seed
closure and replay identically with zero event errors. Boot/event RSS growth
is bounded (**80,257,024 / 80,281,600 bytes**) and maximum event latency is
**116.58 / 135.99 ms**. However, absolute connected-profile peak RSS is
**107,012,096 / 107,053,056 bytes**, above the configured bound in both runs;
the connected absolute-memory assertion therefore fails. Full-boot memory,
production p95/max latency, fixture agreement, Phase 4 promotion, and
human/small-LLM comparative evidence remain open. Reports:
[resource run 1](../../../evaluation/reports/phase7_profile_resource_20260928_learning_context_clarification_resume_v1.json),
[resource run 2](../../../evaluation/reports/phase7_profile_resource_20260928_learning_context_clarification_resume_v2.json).

#### Current-tree comparative packet refresh — 2026-09-28

Rebuilt the unscored blinded output packet from the fresh target replay and
the existing v5-matched ELIZA, two Gemma 3 4B CPU, and two Qwen 3.5 9B runs.
It contains **74 cases / 370 response tracks**. Direct join through the
separate private key verifies target response identity at **74/74**; the two
blank rater forms bind to the same packet digest. Packet, adjudication, and
raw-reference tests pass **20/20**. The refreshed audit records three complete
reference classes (ELIZA **1/1**, small LLM **2/2**, modern LLM **2/2**) and
both human classes missing. This is freshness/integrity evidence only, not a
capability result. Human sessions, approved rubric anchors, dual independent
ratings, and adjudication remain required. Artifacts:
[packet](../../../evaluation/reports/phase8_blinded_output_packet_20260928_learning_context_clarification_v1.json),
[audit](../../../evaluation/reports/phase8_raw_reference_audit_20260928_learning_context_clarification_v1.json),
[rater A](../../../evaluation/reports/phase8_blinded_rater_template_20260928_learning_context_clarification_a.json),
[rater B](../../../evaluation/reports/phase8_blinded_rater_template_20260928_learning_context_clarification_b.json).

#### Graph-selected missing-world context inquiry — 2026-09-28

The graph-native rule already selects `blocked` with
`arbitration_basis=missing_world_information_request` when an information
request lacks required world support. For a turn-compatible interrogative,
the adapter now renders a source/context inquiry through the existing
clarification faculty and production gate; it neither changes native
disposition nor claims a world fact. A focused test verifies the released
repair receipt, unresolved grounding, blocked disposition, and absence of an
answer commitment. Feature-focused tests pass **2/2**; the stale corpus test
contract was corrected to account for both event-bound learning requests
(`question_weather` and `learn_uncertain`) and the updated contract plus both
feature tests pass **3/3**.
The complete Phase 8 corpus-runner suite subsequently passes **31/31**.

Fresh Phase 8: authority **74/74**; releases/errors/authorized silence/
unclassified silence **54/7/13/0**; fixture state agreement **67/74**;
grounding **21/29/0 (F1 0.592)**; Phase 4 **3 sources / 0 complete tuples / 0
promotions**. Latency is **95.81/167.95/184.01 ms** median/p95/max (**12/74**
over 150 ms). `info_world` is now a released clarification while remaining
native `blocked` and ungrounded. Connected-profile replay is deterministic,
has complete selection and zero errors, but the absolute RSS check fails at
**107,048,960 bytes** and maximum event latency is **152.13 ms**. Other RSS
growth assertions pass. Evidence:
[Phase 8](../../../evaluation/reports/phase8_corpus_report_20260928_missing_world_clarification_v1.json),
[connected profile](../../../evaluation/reports/phase7_profile_resource_20260928_missing_world_clarification_v1.json).

The comparative packet and forms were regenerated after this output changed;
the current target joins **74/74** and the raw audit retains three complete
model/ELIZA reference classes with human classes missing:
[packet](../../../evaluation/reports/phase8_blinded_output_packet_20260928_missing_world_clarification_v1.json),
[rater A](../../../evaluation/reports/phase8_blinded_rater_template_20260928_missing_world_clarification_a.json),
[rater B](../../../evaluation/reports/phase8_blinded_rater_template_20260928_missing_world_clarification_b.json).

#### Declarative selected-learning clarification — 2026-09-28

An explicit native `InformationLearningRequest` with unselected source and no
answer authority now also supports a context inquiry when native cognition
selects `learn` for a declarative uncertainty report in a response slot. This
covers `learn_uncertain` without relying on the language adapter's wording or
overwritten general interpretation attrs, and without making retrieval an
answer. Its graph disposition remains `learn`; the clarification is released
as a production-gated repair. Focused learning-clarification tests pass **2/2**.

Fresh Phase 8: dispositions **74/74** authoritative; fixture agreement
**67/74**; **55** released substantive replies, **6** explicit errors, **13**
authorized silences, **0** unclassified; grounding **21/29/0 (F1 0.592)**;
Phase 4 **3 sources / 0 complete tuples / 0 promotions**. Phase 8 latency is
**101.05/167.48/183.89 ms** median/p95/max (**7/74** above 150 ms). The
connected profile is deterministic, complete, and error-free, with max event
latency **147.48 ms** and boot/event growth **80,523,264 bytes**; absolute peak
RSS **107,429,888 bytes** still fails the 100 MiB limit. Full Phase 8 plus
packet/audit/adjudication tests pass **51/51**; `git diff --check` is clean.

The blinded packet was refreshed once more against this exact target and
joins **74/74**; both forms bind to one digest. Human responses/ratings and an
approved rubric remain missing:
[Phase 8](../../../evaluation/reports/phase8_corpus_report_20260928_uncertainty_context_clarification_v1.json),
[resource profile](../../../evaluation/reports/phase7_profile_resource_20260928_uncertainty_context_clarification_v1.json),
[packet](../../../evaluation/reports/phase8_blinded_output_packet_20260928_uncertainty_context_clarification_v1.json),
[rater A](../../../evaluation/reports/phase8_blinded_rater_template_20260928_uncertainty_context_clarification_a.json),
[rater B](../../../evaluation/reports/phase8_blinded_rater_template_20260928_uncertainty_context_clarification_b.json).

The event-bound learning-request predicate now reads the message's incoming
`for_event` adjacency rather than scanning every request node. An exact-tree
repeat confirms no change to any reply, disposition, release, force, or
grounding outcome across 74 cases. The repeated Phase 8 metrics are
**101.33/158.41/182.38 ms** median/p95/max (**12/74** over 150 ms) with
**55/6/13/0** releases/errors/authorized silences/unclassified. The second
connected-profile run is deterministic and complete with zero errors, **123.41
ms** max event latency and **80,224,256-byte** boot/event growth, but absolute
peak RSS still exceeds the 100 MiB gate at **107,139,072 bytes** (first run:
**107,429,888 bytes**). The current blinded packet was rebuilt against the
exact second replay and target joins remain **74/74**. Reports:
[Phase 8 repeat](../../../evaluation/reports/phase8_corpus_report_20260928_uncertainty_context_clarification_v2.json),
[resource repeat](../../../evaluation/reports/phase7_profile_resource_20260928_uncertainty_context_clarification_v2.json),
[current packet](../../../evaluation/reports/phase8_blinded_output_packet_20260928_uncertainty_context_clarification_v2.json).

#### Fresh-process RSS gate separation and prewarm experiment — 2026-09-28

A single connected-profile run in its own fresh process confirms the absolute
RSS failure is not just cumulative retention from the deterministic-repeat
harness: peak **106,942,464 bytes** exceeds the 100 MiB limit, despite complete
selection, zero errors, **147.22 ms** max event latency, and bounded RSS growth.
I tested an evidence-derived runtime preload closure (remove 20 modules not
imported in the 74-event workload; add its five late imports). It preserved all
74 stable observations but increased absolute peak to **108,150,784 / 108,331,008
bytes** across two fresh processes. That unsuccessful tuning was reverted; the
65-module profile list remains unchanged. This rules out simple prewarm-list
trimming as the memory fix. Evidence:
[fresh single run](../../../evaluation/reports/phase7_profile_resource_20260928_uncertainty_context_clarification_single_v1.json),
[trim experiment 1](../../../evaluation/reports/phase7_profile_resource_20260928_runtime_prewarm_trim_v1.json),
[trim experiment 2](../../../evaluation/reports/phase7_profile_resource_20260928_runtime_prewarm_trim_v2.json).

#### Allocator-envelope revalidation against the resumed tree — 2026-09-28

Re-ran the exact full 74-event connected profile in three independent fresh
processes with `PYTHONMALLOC=malloc`, `MALLOC_ARENA_MAX=1`, and
`MALLOC_TRIM_THRESHOLD_=32768`, applied before interpreter startup. All three
selected the complete same **96-seed** closure, returned zero errors, and
produced byte-identical observation structures. Peak RSS was **104,099,840 /
104,198,144 / 103,956,480 bytes** (all below the **104,857,600-byte** ceiling).
Maximum event latency was **151.56 / 125.32 / 137.63 ms**; therefore the strict
150-ms bound is not repeatably met, and this allocator-specific configuration
does not close the paired production envelope. The first-run tail event was
`assertion_source`; no new modules were imported during it, so this is not a
late-import/prepass gap. Treat the allocator result as host-specific evidence,
not a portable production fix. Reports:
[run 1](../../../evaluation/reports/phase7_profile_resource_20260928_resume_malloc_trim32k_v1.json),
[run 2](../../../evaluation/reports/phase7_profile_resource_20260928_resume_malloc_trim32k_v2.json),
[run 3](../../../evaluation/reports/phase7_profile_resource_20260928_resume_malloc_trim32k_v3.json).

#### `assertion_source` latency attribution — 2026-09-28

A diagnostic `cProfile` scoped to the `assertion_source` `converse()` call
completed the full 74-event connected run with complete selection and zero
errors. Profiling overhead makes its **110 ms** call duration diagnostic only,
not an acceptance latency. The largest cumulative paths were reply-intent
formulation through `conceptualize_reply` / `run_pipeline` (**68 ms**), native
rule evaluation (**38 ms**, six calls), and utterance decoding (**22 ms**).
Observation readback and pending host-I/O dispatch are not on this critical
path (the uninstrumented resource reports measured about **2 ms** readback and
**0.06 ms** dispatch for the outlier event). This narrows follow-up to
stage-level profiling within conceptualizer/parse work; there is not yet
evidence supporting omission, reduced quanta, or bypass of any graph-authority
step. Diagnostic profile was not used as resource acceptance evidence.

#### Re-read settled non-turn blocked disposition before information release — 2026-09-28

The full corpus showed `blocked_permission` finishing with native
`blocked/missing_permission_authority` but still returning an explicit error
and creating a withheld production receipt. The original early blocked check
ran before the bounded native schedule had settled this state; subsequent
unresolved-information handling then replaced the no-turn outcome with the
generic error. The adapter now re-reads only the graph-resident disposition at
that later release boundary. If and only if it is now `blocked` and
`interaction_mode=non_turn`, it suppresses the pending graph surface and
returns the already-authorized no-reply. It does not infer permission or
create a replacement response.

The isolated permission query remains an explicit error when native
disposition is still absent. The corpus-context regression establishes the
settled blocked outcome; the isolated fail-closed regression remains intact.
The targeted integration and Phase 4/source suites pass **73/73**. Two fresh
Phase 8 v5 replays are semantically identical: dispositions **74/74**
authoritative; released substantive replies **55**, explicit errors **5**
(down from 6), authorized silences **14** (up from 13), unclassified silences
**0**, and withheld-error receipts **0**. `blocked_permission` is the sole
semantic change; grounding remains **21/29/0 (F1 0.592)** and Phase 4 remains
**3 sources / 0 complete tuples / 0 promotions**. Reports:
[Phase 8 replay 1](../../../evaluation/reports/phase8_corpus_report_20260928_settled_nonturn_block_closure_v1.json),
[Phase 8 replay 2](../../../evaluation/reports/phase8_corpus_report_20260928_settled_nonturn_block_closure_v2.json).

The refreshed blinded packet joins the current target at **74/74**; both
blank rater forms contain **370** rows, share a digest, and retain no scores.
Human references/ratings remain unavailable:
[packet](../../../evaluation/reports/phase8_blinded_output_packet_20260928_settled_nonturn_block_closure_v1.json),
[rater A](../../../evaluation/reports/phase8_blinded_rater_template_20260928_settled_nonturn_block_closure_v1_a.json),
[rater B](../../../evaluation/reports/phase8_blinded_rater_template_20260928_settled_nonturn_block_closure_v1_b.json).

Three independent allocator-configured 74-event connected runs all pass RSS
at **104,013,824 / 104,341,504 / 104,206,336 bytes** and retain complete
96-seed selection with zero errors. Maximum latency is **140.41 / 157.15 /
112.43 ms**; one run exceeds 150 ms, so the combined resource envelope remains
open. Evidence:
[resource run 1](../../../evaluation/reports/phase7_profile_resource_20260928_settled_nonturn_block_closure_v1.json),
[resource run 2](../../../evaluation/reports/phase7_profile_resource_20260928_settled_nonturn_block_closure_v2.json),
[resource run 3](../../../evaluation/reports/phase7_profile_resource_20260928_settled_nonturn_block_closure_v3.json).

#### Current-tree Phase 1 speech-parity recheck — 2026-09-28

Re-ran `.venv/bin/pytest -q tests/test_speech_act_parity_migrated.py` against
the resumed tree: **4 passed, 2 failed**. The native scratch-rule parity and
rule canonicalization checks pass. The live-output check differs on
`Pursue the flurble gap.` (parsed target is the full phrase rather than the
historical `gap`), `You hold rules, yes?` (current `frontier`, historical
`honest_capability`), and `Which rule fired last?` (current `frontier`,
historical `know`). The signal snapshot also differs on eight modal-polar
questions (`Can`/`Could`/`Should`): current parse evidence types the leading
token as function/auxiliary, while the old capture says content/verb. These
are not accepted changes: the capture remains historical evidence, and the
current expectation requires review. The separate live steering suite passes
**11/11**, including the ambiguous unknown-target case, so the `Pursue`
snapshot mismatch does not establish a live steering regression. Keep Phase 1
parity open until each delta is adjudicated and independently covered; do not
edit the frozen capture or silently bless new output. Search of current
substrate/domain code found no graph-resident last-rule-firing record to
support the historical introspection expectation, so that path remains an
actual capability gap rather than a wording change.

#### Current-tree Phase 4 source and lifecycle verification — 2026-09-28

Re-ran the live tuple/materialization/audit regression slice: **32 passed**;
the manifest tuple-source suite also passes **2/2**. A direct audit of the
current seed tree reports **0 exact** and **0 near-match** records, with
`ThoughtManifold` as the sole approved complete-tuple source type. Live
coverage tests confirm that the adapter rejects incomplete tuples and
generic-Concept lookalikes, preserves explicit native `no_candidate`, and
does not select outcomes in Python. This validates the fail-closed boundary,
not Phase 4 completion: the full-corpus source remains **3 partial / 0
complete / 0 promoted**. Advance only when an upstream graph-native faculty
authors candidate-specific evidence for all five dimensions, or when a
specific new native evidence contract is authorized and defined; do not
derive those values from labels or unrelated faculties.

#### Current comparative packet integrity recheck — 2026-09-28

The latest settled-nonturn Phase 8 target has **74/74** authoritative
dispositions, **55** substantive releases, **5** explicit errors, **14**
authorized silences, and zero unclassified silences. Its blinded packet has
**74 cases / 370 score rows**. Recomputed canonical packet digest
`6bcec06abd1c0e0a3092a4598703c71a452a92245aafaba8772b478fe0baa22a` matches
both distinct blank rater forms. The raw-reference, release-gate, and packet
test slice passes **23/23**. This confirms artifact integrity only: both human
classes, rubric approval, ratings, and adjudication are still missing. Details
are in the [comparative evaluation record](CONVERSATIONAL_MANIFOLD_PHASE8A_COMPARATIVE_EVALUATION.md#current-protocol-v5-packet-after-settled-non-turn-correction--2026-09-28).

#### Current installed-service boundary recheck — 2026-09-28

`systemd-analyze verify deploy/jabberwock.service` exits successfully. The
checked-in unit selects `--seeds conversation`, a separate conversation
checkpoint directory, and `--strict-seed-profile-checkpoints`. The live
boundary remains unverified: both `systemctl --user show` and `cat` fail with
`Failed to connect to bus: Operation not permitted`; no `jabberwock_daemon.py`
process is visible in this shell. Do not infer activation or checkpoint
migration from valid unit syntax. Installed-service acceptance remains open
for a runtime environment where the user's systemd bus is accessible.

#### Multi-act interpretation scoring correction — 2026-09-28

The fixed-corpus `social_question` annotation explicitly says both its greeting
and polar information question are true, with `expected_state` retained only
as a legacy scalar projection. Phase 8 already audited co-acts separately,
but the headline interpretation score still compared just the scalar force.
Updated the score contract: events with an explicit `communicative_acts` list
now require an exact match of every graph-resident `(act_type, force)` pair;
unannotated events keep the prior scalar/alias comparison. This changes only
evaluation, not runtime inputs or cognition. Regression coverage verifies that
both acts are required and that scalar behavior is retained. The full Phase 8
runner suite passes **40/40**. A fresh sealed-prepass run on `social_question`
scores interpretation **1/1**, exposes both expected acts exactly, and
releases both expected response components (`greeting`, `repair`). Broader
corpus comparison figures have not yet been regenerated under this corrected
metric; the historical saved reports therefore remain historical evidence.

#### Full-corpus interpretation re-score — 2026-09-28

Re-ran the 74-event Phase 8 v4 corpus in memory under the corrected
multi-label contract. Interpretation is **54/74 (0.730; 95% CI
0.629–0.831)**, one above the prior scalar-only 53/74 because
`social_question` now receives credit only after both graph act/force pairs
match. Its co-act audit is **1/1**, both expected response components release,
and production accounting is **54/54** substantive releases plus **15/15**
authorized silences, with none unclassified. Phase 4 remains **3 partial / 0
complete / 0 promoted**. Synchronous turn latency in this run is
**89.53/172.32/209.93 ms** median/p95/max (**11/74** above 150 ms); this sample
does not close the timing gate. The Phase 8 runner and comparative artifact
regression slice passes **67/67**. No refreshed report was written due to the
14-GiB reports directory; existing JSON remains explicitly historical under
the scalar-only contract.

#### Phase 1 modal-signal delta adjudication — 2026-09-28

Re-ran `tests/test_speech_act_parity_migrated.py`: **4 passed / 2 failed**.
The eight signal mismatches all concern clause-initial English modal
auxiliaries (`Can`, `Could`, `Would`, `Should`): current grammar evidence
classifies them as function/auxiliary, while the frozen pre-migration capture
records content/verb. Added explicit per-utterance adjudications in the live
parity test; the frozen JSON capture remains unchanged. The signal-parity test
then passes **1/1**. This is an evidence-contract correction, not a cognition
behavior change. The end-to-end test still has three unadjudicated live
deltas: target-span content for `Pursue the flurble gap.`, and route differences
for `You hold rules, yes?` and `Which rule fired last?`. Do not bless these
without semantic/source review; Phase 1 parity remains open.

#### Hybrid connected content pre-pass — 2026-09-28

The operator-supplied content manifest used to preload its connected closure
and then disable all later content loading. Changed the default to preserve
both behaviors: manifest groups are installed before the first turn; novel
content continues through the validated, cached provider/dependency index and
only its connected seed closure is loaded. `sealed: true` explicitly retains
offline fixed-workload behavior. The canonical manifest digest binds this mode
into checkpoints. The regression covers preloaded `valley`, dynamically loaded
`sensor` and `signal`, checkpoint resume, unprovided-key no-mutation, and
explicit sealed refusal; focused tests now pass **10/10**, including migration
of a digest-matched old sealed checkpoint into the hybrid default while
unrelated digest mismatches still fail closed. The surrounding daemon-debug
and seed-loader battery reported **57 passed / 1 sandbox failure** before the
migration test was added; its HTTP listener cannot bind localhost (`EPERM`).
The service still uses the incremental profile without an operator manifest,
and live service activation remains inaccessible from this environment.

An in-memory sealed Phase 8 control on the same 74 events preloaded **96**
connected seeds, preserved the corrected interpretation score (**54/74**),
authority (**74/74**), production (**54 releases / 15 authorized silences**),
and compound audit (**1/1**), with peak RSS **109,654,016 bytes**. Latency was
**70.09/131.28/176.12 ms** median/p95/max (**2/74** over 150 ms). The sample
supports eager connected loading for known content but does not close max-turn
latency or establish unseen-content completeness.

The Phase 8 full-corpus parity test now includes a fourth
`conversation_hybrid_prepass` profile: all signal-derived connected content is
preloaded, with dynamic provider resolution still enabled. Full, sealed,
hybrid, and incremental profiles match exactly on semantic observations and
production receipt payloads. The full Phase 8 runner suite passes **40/40**.
A fresh hybrid run loads **96** seeds for **150**
lexical candidates and preserves interpretation **54/74**, authority **74/74**,
production **54 released / 15 authorized-silent**, and complete compound-act
evidence. RSS is **112,726,016 bytes**; latency is **73.85/135.51/151.86 ms**
median/p95/max (**1/74** over 150 ms). This is close to, but not yet a pass on,
the strict latency ceiling and covers only the known fixed workload.

#### Phase 1 target-span repair — 2026-09-28

Traced `Pursue the flurble gap.` to an English POS precedence bug: graph
metadata describing `gap` as a deficiency/modality cue had been overriding its
determiner-headed noun context and erased the action object. `_pos_token` now
consults that modal metadata only where the left syntactic context permits an
auxiliary; inside a noun phrase, context selects the nominal reading. The graph
now retains object head `gap` and the full object NP `flurble gap`; the
instruction still clarifies and creates no request concern. Focused grammar +
steering controls pass **4/4**, and the complete contextual-disambiguation
suite passes **7/7**. The steering test excludes only the independently known
first-turn `boot_integrity` concern, matching the gap-awareness contract.

The Phase 1 suite is now **5 passed / 1 failed**; its sole failing test reports
two live-route deltas: `You hold rules, yes?` (`frontier` vs historical
`honest_capability`) and `Which rule fired last?` (`frontier` vs `know` in the
full parity replay). The modal signal deltas are explicitly adjudicated and
pass; the `Pursue` content delta is gone. Do not bless the remaining routes
without source and context adjudication. No last-rule-firing graph record is
currently established, so the second case may still be a genuine introspection
capability gap.

#### Phase 1 remaining-route source trace — 2026-09-28

A fresh isolated replay localizes both deltas without changing runtime
behavior. `You hold rules, yes?` composes as a polar relation (`You` / `hold` /
`rules`) and the mechanical topic read is `rules`; the generic self-capability
predicate deliberately rejects questions with an external object, so
comprehension falls through to `frontier`. The historical `honest_capability`
label is not grounded by a current capability record for `hold` or by a
verified inventory-answer contract, so it remains unadjudicated.

`Which rule fired last?` currently composes `rule` as subject and `last` as the
object of `fired`; dispatch chooses topic `rule`, while the separate topic
facts report `last`. This loses the event-selection/time relation in the
current parse. A `know` route is only a query handoff, not proof that the
requested firing history is held: downstream topic release requires an
event-bound causal relation plus a supported `HeldAnswer` and
`TopicGroundingEvidence`. No graph-resident last-rule-firing event record has
been established. Keep both deltas open; the defects are localized to
possession/inventory grounding for the first example and event-time selection
parsing/evidence for the second. Phase 1 remains open.

#### Graph-authorized unresolved topic clarification — 2026-09-28

The graph already routed object-bearing self questions to an event-bound
`answer_topic` goal and authored an explicit unresolved-topic clarification,
but the generic Python `frontier` information gate withheld that graph reply
and could replace it with the empty error floor. Added a separate production
contract for this negative disposition: the same-turn topic goal must be
`outcome=unresolved`, the inbound must carry `topic_replied`, the exact surface
must be a graph Message linked to that turn, and no same-topic search/ground
request may still be active. Only then is the topic-specific clarification
released with a `conversation_topic_unresolved_graph` receipt; this does not
authorize a positive answer or weaken the existing grounding gate. The
object-bearing-polar regression now checks the unresolved goal and released
receipt, and the full topic-route module passes **15/15**. A neighboring
fragment test was corrected to expect silence for its explicit overlapping,
turn-compatible `defer` disposition (rather than the contradictory error
surface assertion). Phase 1 route parity remains open: this fixes production
of the graph-selected miss, not the unresolved possession/inventory or
event-time-selection interpretations above.

An end-to-end probe of the two parity utterances sharpens those open defects.
`You hold rules, yes?` receives the unresolved-topic wording “I don't hold
anything about rules yet” even though the booted graph contains **2,322**
`Rule` nodes and **2,389** `RuleSummary` nodes. The graph has abundant rule
inventory, but the possession proposition is not connected to it; this is a
real false-negative self-report, not merely a legacy route-label difference.
`Which rule fired last?` yields the canonical error floor, with no answer-topic
goal and no answer commitment. The generic rule summaries describe what rules
do, not firing chronology; no graph-resident rule-firing event history was
found. Keep Phase 1 open: the first case needs grounded inventory relation
support, while the second needs both temporal-selection parsing and an event
history evidence source before it can answer.

#### Object-bearing polar relation clarification — 2026-09-28

Preserved both halves of the hybrid content model: the seed/dependency
pre-pass caches connectedness and preloads known connected groups, while
validated provider lookup can still load newly encountered connected groups
on demand. These are complementary stages, not competing loading strategies.

For object-bearing self-polar questions, changed the comprehension handoff
from `frontier` to the graph's topic/capability arbitration path. A fresh
`Can you play chess?` trace now creates the `chess` topic goal, records
`missing_polar_relation_support`, and selects repair. The graph-linked
clarification is released through the production gate with no answer
commitment. Updated the regression to check this native relation-repair
contract instead of the obsolete unresolved-topic surface; the focused test
passes. The first full route run found one stale test expectation that the
goal explicitly store `outcome=unresolved`; the actual graph leaves it active
without a resolved outcome. The regression now checks that the goal is not
resolved and validates the graph-linked clarification receipt, request act,
and absence of answer commitment. After that correction, the full topic-route
module passes **15/15**. Phase 1 remains open, and the separate
inventory and event-history evidence gaps are unchanged.

A second fresh end-to-end probe confirms the same safe outcome for
`You hold rules, yes?`: despite **2,322** held `Rule` nodes, the graph selects
`missing_polar_relation_support` and releases a clarification rather than
claiming “I don't hold anything about rules.” Added a regression that checks
the graph's repair disposition, released clarification receipt, and absence
of any answer commitment. That focused regression passes. This prevents the
false-negative self-report, but does not yet establish positive inventory
relation evidence; the legacy `honest_capability` parity delta remains open.
The refreshed `Which rule fired last?` still falls to the error floor with no
answer goal or commitment. Grep and runtime inspection find no durable
graph-resident rule-firing chronology to select from. The expanded route
module, including the new regression, passes **16/16**. Phase 1 remains open:
positive possession/inventory evidence and event-history parsing + source are
still missing.

The broad speech-act live-parity replay exposed three additional route deltas
from this generic handoff. Source review confirmed that “Would you kindly open
the door?” is a polite action request, not an object-topic inquiry; the
handoff excludes recognized politeness markers so that path retains its prior
action/frontier handling. The replay
now reports only three route mismatches: `You hold rules, yes?` (intentionally
repaired rather than claiming unsupported positive capability), `Have you
seen the report?` (the graph asks for relation grounding rather than making
an unsupported memory claim), and `Which rule fired last?` (still unhandled;
its parse loses event-time selection and no firing-history source exists).
The parity test remains failing on those three cases; they are not being
blessed as blanket overrides. All non-route layers in that battery pass.

#### Re-adjudication of object-polar parity — 2026-09-28

The safe relation repairs for `You hold rules, yes?` and `Have you seen the
report?` are now explicit, reviewed live-route overrides. The report-memory
case has an added focused regression and passes individually. After these
adjudications, the live speech-act parity replay has one remaining mismatch:
`Which rule fired last?`. That selection parse loses event-time information,
and the graph has no durable rule-firing history source; it remains open and
is not overridden. The prior full **16/16** topic-route result predates the
report-memory regression, which has only been run individually so far.

#### Preserve topic + capability evidence in object-bearing polar turns — 2026-09-28

A too-broad exclusion for typed authority requests caused `Can you play
chess?` to bypass native relation arbitration and regress to the topic-miss
surface. Removed that exclusion: the external object/topic and capability
question remain together in the handoff, and the graph decides whether either
relation has support. Keep only the recognized-politeness exclusion needed to
avoid routing “Would you kindly open the door?” as a topic query. The speech
act parity suite now passes **5/6**; its sole remaining mismatch is
`Which rule fired last?`. In the same targeted run, the chess relation-repair
test passes. The complete topic-route module passes **17/17**, including the
updated chess relation test and report-memory clarification test. Broader
project gates remain open.

#### Event-time selection repair without history claims — 2026-09-29

Repaired the parse for selection questions with a clause-final adverb after
the selected nominal's predicate: “Which rule fired last?” now retains `rule`
as the selected subject, `fired` as predicate, and `last` as an adverbial
event-time modifier rather than a direct object. The comprehension adapter
preserves event-specific scope and an unresolved-selection signal; native
`communication_intent_arbitration` selects
`missing_event_history_support`. The release path asks for grounding context
instead of asking the user to define the known word “rule,” and it makes no
answer commitment. The focused end-to-end test passes; the full speech-act
parity suite now passes **6/6**, eliminating the prior dispatch-path mismatch.
This is repair behavior, not an answer: a durable rule-firing history source
is still absent, so the query cannot yet identify an actual last-fired rule.
The expanded topic-route module, including this regression, is being rerun.

The expanded full topic-route module rerun completed successfully: **18/18**.
This validates delivery of graph-selected repair for the new event-time
selection path, but does not close the missing rule-execution history source.

#### Combined topic-route and speech-act parity refresh — 2026-09-29

The source-current combined rerun of
`.venv/bin/pytest -q tests/test_topic_route_selfheal_migrated.py
tests/test_speech_act_parity_migrated.py` passes **30/30** in **331.00 s**.
This independently revalidates the selected repairs and the 6/6 speech-act
parity cases. The conversation-scoped `RuleFiringHistory` ledger and tested
English positive answer route are present; multilingual generalization and
broader Phase 1 parity remain open. Broad production, grounding, Phase 4,
comparative, and latency gates also remain open. Conversational cognition and
functional-substrate establishment remain concurrent tracks with separate
criteria; the substrate Stage 0 review is still 25/65 mapped test paths and
Stage 2 remains open.

#### Phase 1 neutral-arbitration test expectation correction — 2026-09-29

The combined frozen Phase 1 adjudication/compound-act/neutral-arbitration
batch now passes **67/67** in **703.65 s**. The first run exposed an older test
expecting generic unresolved-information provenance for “Good morning, are we
ready?” despite ordered greeting + polar-question evidence and the more
specific native missing-relation basis. Updated only that test's name and
basis/surface expectation; corpus annotations and runtime rules are unchanged.
This source-current verification closes this selected test-batch discrepancy,
not broad language generalization, all live-turn classes, or overall
acceptance. Async parity, production, resource repeatability, comparative, and
functional-substrate gates remain open and concurrent.

#### Sourced hatch referent grounding — 2026-09-29

Added the WordNet 3.0 `hatch.n.03` Concept to the common-object seed and
verified that connected-profile loading exposes it as referent evidence
without implying a physical hatch instance or action-execution capability.
The focused action/defer and grounding-reference tests pass **77/77**. A
source-current 74-event Phase 8 replay completed with no runtime errors;
grounding improved from 21 TP / 29 FN to **23 TP / 27 FN**, with zero false
positives (F1 **0.630**). Peak RSS was **123,532 KiB**; latency was 46.73 ms
median and 94.39 ms p95, with no event over 150 ms. The action-sequence reply
surface changed and remains a production-quality caveat; cognition state did
not change. Comparative references/ratings remain unavailable, Phase 4 has
no eligible completions, and release remains blocked. The conversational
cognition and functional-substrate tracks remain concurrent, with separate
criteria; this increment does not advance or substitute for substrate
establishment.

#### Definite-phrase preservation on the graph instruction route — 2026-09-29

The hatch-grounding update routed the compound instruction through the native
graph floor, whose normalized target omitted “the” in its English reply.
Recorded the parsed action-target phrase separately as `comp_object_surface`;
the native Goal continues to store the normalized `comp_content`. Focused
adapter/route tests pass **3/3**. The full Phase 8 replay covers 74/74 events,
has zero errors, and is identical to the preceding hatch run on cognitive
state, grounding, release disposition/status, and reply presence; it now says
“close the south gate,” “check the pressure,” and “open the hatch,” while
the Goal objects remain normalized. Grounding remains **23/50 referent true
positives**, **27 false negatives**, and zero false positives. Phase 7 verifies deterministic
replay, full seed selection, zero errors, all resource assertions, and **113.8
MB** peak RSS; maximum event time is **120.72 ms**. Phase 4 and comparative
acceptance remain open, as do broader production and repeated strict-latency
gates. The conversational and functional-substrate workstreams remain
concurrent and independently gated.

#### Current-source instruction-rule regression closure — 2026-09-29

The first complete rerun found a regression in the separate read/comprehend
rule because it had been switched to the new action-target surface attribute.
Restored its normalized content readback; only the native world-action floor
uses the parsed surface phrase. The action-evidence and instruction modules
now pass **50/50**, including the read-rule regression and action surface
cases. Source-current Phase 8 covers 74/74 events with zero errors and exact
parity to the prior surface run on state, grounding, release status, and reply
presence. It records **23 TP / 27 FN / 0 FP** grounding (F1 **0.630**),
**54/15/0** substantive/authorized-silent/unclassified production outcomes,
and Phase 4 **0 complete / 0 promoted**. One event is over the 150-ms limit
(median/p95/max **47.60/99.44/153.87 ms**), so repeated latency acceptance is
still open. The current connected Phase 7 replay verifies determinism, all
resource assertions, no errors, and **113.86 MB** peak RSS; maximum event
latency is **141.20 ms**. Comparative evidence remains blocked on references
and ratings. Functional-substrate establishment remains a concurrent,
separately gated workstream.

#### Current-protocol blinded comparison packet refresh — 2026-09-29

Replayed the corrected source under v5 event-context/history-8 and refreshed
the blinded five-system packet. It binds current target outputs against
protocol-matched existing ELIZA, Gemma 3 4B CPU (two exact-repeat runs), and
Qwen 3.5 9B CPU (two seeded runs), with **74 cases / 370 response rows** and
no exposed system names or corpus labels. Two separate blank rater forms were
generated. The raw-reference audit confirms **3 reference classes complete
raw / 2 human classes missing**, with scoring disabled. Packet/adjudication/
raw-audit tests pass **20/20**. The v5 target retains **23/27/0 TP/FN/FP**
grounding, **54/15/0** substantive/authorized-silent/unclassified production,
Phase 4 **0 complete / 0 promoted**, and **51.13/95.96/129.01 ms** median/p95/
max latency (**0/74** over 150 ms on this replay; not repeatability proof).
Comparative release remains blocked pending approved rubric, human sessions,
independent annotations, and adjudication. No new LLM inference or score was
claimed. Evidence: [v5 target](../../../evaluation/reports/phase8_corpus_report_20260929_hatch_surface_v5_v1.json),
[blind packet](../../../evaluation/reports/phase8_blinded_output_packet_20260929_hatch_surface_v5.json),
[R1](../../../evaluation/reports/phase8_blinded_rater_template_20260929_hatch_surface_v5_r1.json),
[R2](../../../evaluation/reports/phase8_blinded_rater_template_20260929_hatch_surface_v5_r2.json),
and [raw audit](../../../evaluation/reports/phase8_raw_reference_audit_20260929_hatch_surface_v5.json).
The functional-substrate workstream remains concurrent and independently
gated.

#### Current-source connected-profile latency gate — 2026-09-29

Four independent full-corpus v5 `conversation_corpus_prepass` runs now meet
the **<150 ms** per-event bound with maxima **129.01, 143.24, 126.01, and
125.21 ms**; all have 74/74 events, zero errors, and identical normalized
outcomes and replies. This closes strict latency repeatability for the fixed
connected profile only; full-seed/service startup and arbitrary future inputs
are not established by these runs. Phase 7 verifies deterministic replay,
complete selection, all six RSS assertions, no errors, and **113,860,608 bytes**
peak RSS (**below 150 MiB**) with **141.20 ms** maximum event latency.
Grounding remains **23 TP / 27 FN / 0 FP**, Phase 4 has **0 complete / 0
promoted**, and comparative acceptance still needs human references/ratings
and adjudication. Broader production and full-boot gates remain open. The
conversational and functional-substrate tracks remain concurrently active.
