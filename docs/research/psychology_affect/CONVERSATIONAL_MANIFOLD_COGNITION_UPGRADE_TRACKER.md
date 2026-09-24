# Conversational Manifold Cognition Upgrade Tracker

**Parent plan:** [`CONVERSATIONAL_MANIFOLD_COGNITION_UPGRADE_PLAN.md`](CONVERSATIONAL_MANIFOLD_COGNITION_UPGRADE_PLAN.md)  
**Related implementation:** [`CONVERSATIONAL_MANIFOLD_EXECUTION_PLAN.md`](CONVERSATIONAL_MANIFOLD_EXECUTION_PLAN.md)  
**Status:** Active incremental implementation; exit evidence remains incomplete.  
**Invariants:** `noted` is never a failure surface. A failed cognitive/dispatch path must expose `ERROR: no communicative response could be generated.` The cognition/arbitration layer must be language-agnostic; language-specific modules may provide evidence but may not define the cognitive ontology.

## 1. Current baseline snapshot

| Dimension | Evidence | Current status |
|---|---|---|
| Runtime teacher/LLM use | `donkey=0` assertions and native tests | 🟢 Verified in focused paths |
| Action/repair dispatch | `tests/test_conversation_loop.py` | 🟢 12/12 passed after Phase 8 bridge |
| Turn-compatible continuity and API parity | `tests/test_utterance_conversation_unification.py` | 🟢 Focused gate passed |
| Self-report / scene description | Conversation-loop and conceptualizer gates | 🟢 Focused gates passed |
| Explicit failure surface | Conversation and speech grounding tests | 🟢 Verified |
| Topic grounding precision | Topic/reference evidence plus unrelated-answer regression | 🟡 Precision 1.00, recall 0.46, F1 0.630; zero false-positive grounding remains verified, but recall is below acceptance |
| Register/common-ground cognition | Discourse lifecycle seam and production receipts | 🟡 Phase 3/6 increments; full integration remains |
| Deliberation trace completeness | Thought-manifold provenance, rejection, settle-back, and Phase 4P proposition boundary traces | 🟡 Evidence-materialization and Phase 4P boundary pass; live corpus still lacks complete upstream tuples and selected candidates |
| Parse-back coverage | Production receipts and Phase 6P/6Q receipt-backed recoverability measurement | 🟡 Final post-fix 74/74 measured: 32 receipt-semantic recoverable, 42 explicit-error/withheld, 0 receipt-semantic mismatches, 0 missing; runtime state remains a separate diagnostic |
| Latency / RSS / graph residence | Native profiles through extended dialogue/high ambiguity/graph growth | 🟡 Phase 7L replay is deterministic; cold 8-event growth is 123,744,256 bytes and steady-state growth is 9,175,040 bytes over 30,740.9 ms |
| Baseline comparison | 74-event SUT report; deterministic ELIZA-floor raw run; complete local Gemma 4B and Qwen 9B raw runs; human adjudication unavailable | 🟡 Raw LLM collections exist, but capability adjudication and release gate remain blocked |
| Science-grounded annotation | Independent force/goal/grounding labels plus held-out probes | 🟡 Phase 1 evidence exists; corpus expansion still required |
| Language-agnostic cognition | Neutral evidence boundary plus live Spanish/Japanese integration | 🟢 Phase 1 gate passed; broader language coverage remains |

## 2. Phase status matrix

| Phase | Objective | Primary locations | Status | Acceptance evidence |
|---|---|---|---|---|
| 0 | Evaluation contract and failure taxonomy | `tests/`, `evaluation/`, `docs/` | 🟡 Phase 0C conditional candidate/lifecycle contract | Versioned 74-event corpus, deterministic trace assertions, and explicit Phase 4 cross-reference for observed candidate traces; external baseline report and full-corpus candidate observations remain |
| 1 | Canonical comprehension and intent arbitration | `domains/comprehend_text.py`, `substrate/world_adapter.py`, seeds | 🟢 Acceptance gates pass; broader corpus remains useful | ≥95% corpus agreement; conflict traces; language-neutral evidence |
| 2 | Grounding, reference, and epistemic state | topic routing, retrieval, gap seeds | 🟡 Phase 2I authority/grounding separation | Topic/reference evidence paths, discourse referent state, and 74-event measurement; latest binary SUT rerun has 0 false positives (precision 1.00), recall 0.46, and F1 0.630 |
| 3 | Discourse state and goal lifecycle | conversation state, goal seeds, interlocutor model | 🟢 Exit slices plus asynchronous common-ground stress pass | Mixed-act, multi-addressee, interleaved-goal, and zero-reply event stress pass |
| 4 | Deliberative candidate generation and arbitration | thought manifold, decision collapse, native cycle | 🟡 Phase 4 evidence-materialization and 4P boundary pass | Four original plus five held-out families, explicit graph evidence transport, native provenance/rejection/settlement, and Phase 4P boundary; live corpus still has no selected candidates |
| 5 | Learning, gap closure, and self-correction | gap awareness, self-concern, correction model | 🟡 Phase 5O explicit corpus overlay | Six explicitly annotated event observations reuse live ingress; three identity-local native recurrences are measured; the unannotated base corpus remains correctly unavailable for learning claims |
| 6 | Cognitively gated production release | conceptualizer, audience, production, parse-back | 🟡 Phase 6V authoritative topic-release correction; runtime state diagnostics remain separate | Fresh 74/74 measured; 32 receipt-semantic recoverable, 42 explicit-error/withheld, 0 receipt-semantic mismatches, 0 missing; runtime state diagnostics remain separate |
| 7 | Native integration and performance envelope | Rust substrate/cycle, adapter boundary | 🟡 Phase 7N substrate cost profile; performance/resource exit remains open | Native profiles plus graph-authored Phase 3–6 workloads and an 8-event live communication envelope have replay/resource evidence; neutral semantic ingress is bound and the first-event graph-index cost is isolated |
| 8 | Comparative evaluation and release gate | `evaluation/`, `docs/` | 🟡 Phase 8H raw-reference integrity audit | Versioned 74-event SUT report, 74 raw ELIZA observations, 74 raw Gemma 4B observations, and 74 raw Qwen 9B observations are verified case-bound; capability dimensions remain unavailable pending blinded adjudication; human references remain unavailable; gate blocked |

## 3. Immediate execution queue

1. **Phase 4 upstream cognition:** Preserve explicit `no_candidate` until an existing faculty supplies the complete live tuple. Phase 4R measured zero complete or near-match tuples in the 74-event corpus; no evidence may be inferred from adjacent faculties.
2. **Phase 6W:** Adjudication is complete. The remaining `question_followup` mismatch lacks typed causal world evidence; add that event only if the benchmark intends to test causal learning, or revise its isolated expected disposition to `repair`/`unknown`. Do not add a conversation rule.
3. **Phase 7 resource envelope:** Phase 7O indexed-ingress equivalence and Phase 7P selective kind-rule readback are complete, but cold RSS and latency remain over budget. The `run_rules_prefix` optimization was rejected for semantic drift and memory cost; a further change needs a substrate/runtime target and held-rule parity evidence.
4. **Phase 8I:** Independently adjudicate existing raw runs and collect base/advanced human references with provenance before publishing scores.

No wording-only repair is permitted for these items.

## 4A. Audit of remaining exit evidence — 2026-09-23

This audit separates implemented bounded slices from evidence still required by
the phase exit criteria. Counts below are repository `.venv` runs, not inferred
coverage from filenames or fixture size.

| Area | Verified current evidence | Still missing | Bounded next increment |
|---|---|---|---|
| Phase 2 | Runtime correction plus focused regressions are green; latest 74-event SUT rerun has 0 false-grounding violations, precision 1.00, recall 0.46, F1 0.630 | Conservative recall and supported event-to-commitment corpus coverage | Phase 2T neutral overlay keyed to existing events; do not alter the grounding denominator |
| Phase 4 | Combined live-manifold lifecycle suite passes: 27 tests; Phase 4P boundary adds 4 tests; native collapse, rejection, execution, settle-back, and bounded counterfactual traces are present | Production-corpus replay and complete upstream tuples | Identify an existing faculty that can author complete five-field evidence; no promotion by proposition or situation state |
| Phase 5 | A–F recurrence/promotion suite passes: 27 tests; 24 opaque identities/72 events, visible failed repair, explicit review, promotion, and retirement | Broader production-corpus recurrence and impact/priority measurement | Phase 5G verifies six heterogeneous families, priorities 2–7, monotonic growth, stable identities, route transfer, failed repair, and no cross-identity promotion; next is production-corpus recurrence |
| Phase 6 | Focused production/readback/output-null/QA gate passes; Phase 6Q final post-fix receipt readback covers 74/74 events | 6 receipt-semantic mismatches, 45 runtime-state diagnostics, and audience-state evidence | Correct receipt force/multiplicity causes and adjudicate graph state separately; 30 recoverable, 38 explicit/withheld, 6 mismatches, 0 missing |
| Phase 7 | Seven native measurement tests pass; extended dialogue, high ambiguity, graph growth, replay, authority, latency, RSS, and graph residence are measured | Native authority for remaining comprehension/discourse/learning decisions and production-scale resource envelope | Phase 7K neutral semantic-event envelope; current audit is 172 unbound and 10 explicitly bound calls |
| Phase 8 | SUT, ELIZA-floor, small-LLM, and modern-LLM raw observations exist for all 74 events; release gate is correctly blocked | Human references and adjudicated capability scores remain unavailable; raw LLM runs are not scores | Independently adjudicate existing raw runs, collect base/advanced human references with provenance, and add repeated trials, confidence intervals, and a separate memory/learning/cost corpus |

Recommended execution order is Phase 4Q complete tuple authorship, Phase 5
production recurrence, Phase 6Q semantic mismatch correction, Phase 7K
production-envelope follow-up, and Phase 8 adjudication. Phase 2T and the
initial Phase 7K envelope are verified bounded increments. No
baseline score may be fabricated from raw observations or a protocol scaffold.

### 4E. Substrate integration audit — 2026-09-23

The architecture audit is recorded in
[`CONVERSATIONAL_MANIFOLD_SUBSTRATE_INTEGRATION_AUDIT_20260923.md`](CONVERSATIONAL_MANIFOLD_SUBSTRATE_INTEGRATION_AUDIT_20260923.md).
It found that the substrate already provides the authoritative primitives for
messages/events, intents, goals, reference/common ground, thought manifolds,
residual learning, production gates, and native collapse. No new Rust or
substrate API is required.

The audit also found two integration corrections that must precede more Phase 4
work:

- conversation action goals are minted through the existing `has_goal` path but
  are not consistently linked with `Goal -comprehends-> Message`; the live
  deliberation binder therefore sees no eligible goal;
- `conversation.py`, `reference_resolution.py`, `discourse_state.py`, and
  `world_adapter.py` currently expose overlapping common-ground/referent
  writers. The canonical referent store must be reused, with `DiscourseState`
  retaining event-local lifecycle and delta state rather than minting parallel
  identities.

The current live binder is therefore not acceptance evidence for Phase 4. The
next increment is goal/event binding and referent-store consolidation, followed
by a corpus replay requiring event-justified (not universal) deliberation
traces. No source implementation was changed during this audit.

### 4F. Goal/event and live deliberation integration — 2026-09-23

- Added idempotent `Goal -comprehends-> Message` binding and `origin_turn_id`
  provenance to the conversation action boundary. Focused verification:
  **3 passed**.
- Added the live event/goal bridge correction: action/repair early-return paths
  now bind before release; actual `sent_by`/addressee graph provenance is used;
  grounding is read from `CommunicationInterpretation`; unresolved parsed topics
  are not promoted to grounded current topics; and the Phase 4 seed is loaded
  once rather than on every event.
- Empty event-linked deliberations now use the existing native
  `generated_from_discourse_state` contract and settle to explicit
  `status="no_candidate"` with `candidate_trace_complete=1.0`, without
  fabricated candidate evidence.
- Focused live bridge plus production/goal regressions: **19 passed**.
- The 74-event replay now records **74/74** cognition traces and **28**
  event-justified complete deliberation traces (all explicit `no_candidate` in
  the current corpus); no selected-candidate traces are present because the
  live path still lacks evidence-bearing manifold candidates. This is progress
  in observability, not Phase 4 completion.
- Added the Phase 4 manifest to the seed registry so full boot and incremental
  live boot have the same native deliberation vocabulary.

### 4G. Canonical referent ownership — 2026-09-23

- Added `DiscourseConceptProvider` and idempotent
  `DiscourseStore.ensure_referent()`.
- `WorldAdapter` now lazily retains one canonical `DiscourseStore`; `CurrentTopic`
  remains a compatibility/focus projection and no longer mints a new referent
  on every projection.
- Repeated topic projection and save/load rehydration tests pass: **2 focused
  tests**, plus one legacy compatibility test.
- `CommonGround` remains participant-relative claim state; it is not treated as
  a second referent-identity owner.

### 4H. Verification boundary and known legacy conflicts — 2026-09-23

The broader reference/topic regression battery produced **41 passed, 6 failed**
after the integration. The failures fall into two categories: legacy tests
expecting the retired `I don't hold that.` surface, and a fake-grounder test
whose stale surface does not match the later graph-held answer. The explicit
error invariant and production gate are intentionally preserved; these failures
require specification/test-fixture reconciliation, not a wording fallback or
an unrelated-answer release. They are not counted as Phase 2/6 acceptance.

The next cognitive increment remains Phase 4 evidence generation: convert
existing train-of-thought/grounded relation evidence into native candidate
nodes, then let the Phase 4A native collapse select or reject it. Do not create
synthetic candidates merely to turn the current `no_candidate` traces green.

### 4I. Evidence-bearing candidate materialization — 2026-09-23

- Added a mechanical `conversation_deliberation` boundary that materializes
  candidates only from explicit graph evidence. It supports active discourse
  goals with linked evidence, repair/residual stance evidence, and live
  `ThoughtManifold` evidence relations, while preserving source provenance.
- A lifecycle `Goal` without numeric cognitive evidence is not promoted. A
  goal may use an explicitly linked `supported_by` evidence node; no policy
  defaults are copied onto the goal and no language or reply text is used as
  evidence.
- Native Phase 4A rules remain authoritative for valuation, Argmax collapse,
  rejection, execution, settlement, and counterfactual credit. The materializer
  performs no ordering, scoring, selection, or fallback surface generation.
- Local `.venv` verification: focused Phase 4/live-bridge/action battery
  **32 passed**; `py_compile` and `git diff --check` passed.
- This closes the bounded evidence-transport seam, not the live production
  candidate-generation gate. The 74-event corpus still needs a real
  graph-resident train-of-thought/grounded-relation source before selected
  candidate traces can be claimed.

### Phase 4J — Legacy decision-option authority boundary — 2026-09-23

- Audited the existing `ConversationDecisionState`/`DecisionOption` records
  against the Phase 4A candidate schema. They expose fast/learned/grounded
  values and residual/deep metadata, but no declared `consequence` or
  `novelty` evidence mapping.
- Direct promotion would infer missing evidence and create a competing
  authority, so it is explicitly rejected. The live bridge remains
  evidence-only and settles to native `no_candidate` until a faculty supplies
  the complete Phase 4 tuple.
- Added an executable boundary regression; it passed with the focused Phase 4
  suite. No synthetic candidate or surface fallback was introduced.

### Phase 4K — Native deliberation readback diagnostics — 2026-09-23

- Added an evaluation-only `deliberation_readback` summary to the Phase 8 SUT
  observations. It records whether native deliberation trace data exists,
  native statuses and candidate sources, candidate count, selection count, and
  settlement count.
- Missing trace data remains `unavailable`; a native `no_candidate` trace is
  reported as measured with zero candidates. The evaluator never infers a
  candidate from a goal, reply, or surface string.
- Live inspection confirms the current 74-event corpus has no complete upstream
  Phase 4A evidence tuple for ordinary communication events. This increment
  improves the evidence boundary and observability; it does not manufacture
  candidates or claim Phase 4 completion.
- Local `.venv` verification: Phase 8 corpus-runner battery **11 passed in
  374.24s**; compilation and diff checks passed.

### Phase 4K — Pre-continuation substrate reinvention audit — 2026-09-23

- Re-audited the current substrate before beginning another phase. The audit is
  recorded in
  [`CONVERSATIONAL_MANIFOLD_SUBSTRATE_INTEGRATION_AUDIT_20260923.md`](CONVERSATIONAL_MANIFOLD_SUBSTRATE_INTEGRATION_AUDIT_20260923.md).
- Confirmed reusable authorities for referents/centering, gap recurrence and
  acquisition, graph-prioritized learning, thought-manifold evidence, native
  deliberation, production/readback gates, native cycle execution, and neutral
  communication evidence. No new substrate API or parallel conversation
  cognition store is justified.
- Confirmed the two active boundaries: `DiscourseStore` owns referent identity
  while `DiscourseState`/`CommonGround` retain event-local lifecycle and claims;
  legacy `DecisionOption` records are not promoted into Phase 4A without the
  missing `consequence` and `novelty` evidence dimensions.
- Remaining work is evidence/integration work: production-corpus recurrence,
  complete live manifold evidence, native-authority audit debt, and authorized
  external baselines. No defaults or surface-level substitutes may be added to
  make these gates appear complete.

### Phase 4L — Global Phase 4 tuple availability audit — 2026-09-23

- Added `evaluation/phase4_substrate_tuple_audit.py` and executable tests that
  scan seed-manifest node records for the complete tuple
  (`grounding`, `expected_value`, `residual_cost`, `consequence`, `novelty`).
- The audit found no complete seed-record tuple. `dual_process_core` is a
  reusable arbitration substrate and a near-match, but it lacks the complete
  Phase 4 evidence contract and is not promoted by inference.
- `ThoughtManifold` remains the only approved source type for a complete live
  tuple. This closes the reinvention audit increment without claiming that a
  live manifold generator exists.

### 4B. Phase 6/8 corpus transport correction — 2026-09-23

- Corrected `evaluation/phase8_corpus_runner.py` so corpus events labelled
  `imperative`, `compound_imperative`, or
  `imperative_with_politeness_marker` enter the runtime as `instruction`
  evidence. The runner had been downgrading them to `statement`, losing an
  input-level cognitive signal before native comprehension ran.
- Added a regression in `tests/test_phase8_corpus_runner.py` for that mapping.
  Local `.venv` verification: the Phase 8/manifest replay battery passed
  **16 tests** in 5m23s; the focused Phase 6 bridge battery passed **29 tests**.
- Refreshed `evaluation/reports/phase8_corpus_report_20260923.json`. The live
  manifest diagnostic is now **ready**, with **74/74** cognition traces, **40**
  released receipts, **34** explicit errors, and **74/74** accepted coverage.
- Grounded held-answer release and event-scoped permission evidence were
  implemented; authority precedence now prevents later referent refresh from
  overwriting `authority_missing`. Binary grounding remains precision **1.00**,
  recall **0.38**, F1 **0.551**, with zero false-grounding positives. The
  canonical error surface remains the only unresolved-release surface.
- The corpus semantic-state comparison still has **60/74** mismatches. This
  is the substantive Phase 6 bottleneck: manifest coverage proves that every
  event has a graph-backed release/error/trace, not that the selected state or
  answer relation is correct. The next cognition increment must reduce these
  mismatches by improving state arbitration and relation-specific evidence,
  not by adding conversational wording.

### 4C. Native input-force evidence increment — 2026-09-23

- Added `sak_input_kind` as graph-resident evidence when an upstream language
  adapter supplies `instruction`/`request` force. The native speech-act rules
  consume that evidence before ambiguous POS/wh cues, without adding an
  English verb inventory or using reply text as evidence.
- Added `tests/test_native_instruction_input_evidence.py` covering bare,
  compound, and conditional imperative forms plus a question non-regression.
  Local `.venv` focused verification: **4 passed**; the combined native and
  Phase 6 production battery passed **33 tests**.
- The replay at this earlier increment measured **42** released receipts,
  **31** explicit errors, **73/74** accepted substantive coverage, and one
  uncovered event: `blocked_permission`. A later authority-precedence fix
  brought the current replay to **42** receipts, **32** errors, and **74/74**.
  `action_sequence` now has a graph-backed action receipt. Grounding remains
  precision **1.00**, recall **0.42**, F1 **0.592** at that increment; the
  current binary replay is precision **1.00**, recall **0.38**, F1 **0.551**.
- The full `test_comprehension_cutover_migrated.py` rerun was not completed:
  after installing missing `.venv` dependency `nltk`, it reached 1 test in
  10m48s and was stopped at the existing slow boot path. This is an
  environment/runtime verification limitation, not counted as a passing gate.

### 4D. Permission/authority fail-closed increment — 2026-09-23

- Added graph-resident permission evidence derived from semantic Concept
  attributes and action-role relations. A request with no
  `PermissionDecision`, `AuthorityDecision`, or `PermissionEvidence` is marked
  `authority_missing`; it cannot fall through to an unrelated interlocutor
  self-report.
- The unresolved information production gate now evaluates authority-missing
  requests and emits the canonical explicit error with a withheld receipt.
- Added a focused regression for `Can I access the sealed room?`; the Phase 6
  information bridge suite passes **8 tests**. The latest corpus replay now
  records the canonical error and withheld receipt for `blocked_permission`,
  bringing the manifest to **74/74** accepted events.

## 4. Per-phase execution record

### Phase 1 — Initial increment completed

- Start: 2026-09-22
- Added graph-resident `CommunicationInterpretation{schema:'communication_interpretation.v1'}` records for every live communication event, including selected kind, dispatch path, intent, focus, predicate/object, gap count, native kind, conflict status, and interaction mode.
- Linked each interpretation to its inbound `Message` with `has_interpretation` and `interprets`, and to the agent with `holds_interpretation`.
- Kept the comprehension result as the selected interpretation while retaining native speech-act output as evidence; disagreement is recorded as `kind_conflict`, not silently discarded.
- Added `tests/test_conversational_intent_arbitration.py` covering instruction selection, frontier-gap evidence, native/comprehension conflict retention, and non-turn interaction mode: **4 passed**.
- Existing action/repair regression subset after the change: **4 passed**.
- Added non-turn-mode coverage through the compatible `converse(..., context={"interaction_mode": "streaming_observation"})` boundary; the record remains event-based and does not require turn alternation.
- Added separate graph fields for literal mood/evidence, communicative-force hypothesis, cognitive-goal hypothesis, grounding status, and parse/native evidence provenance. These are recorded hypotheses, not yet adjudicated human labels.
- Remaining work: build the fixed Phase 0 corpus, measure native/front-end agreement, classify conflicts, and promote only a measured arbitration policy to authoritative dispatch.
- Measurement completed: [Phase 1 intent arbitration report](CONVERSATIONAL_MANIFOLD_PHASE1_INTENT_ARBITRATION_MEASUREMENT.md) records 93.8% kind agreement, below the 95% acceptance target.
- Added a science-grounded annotation contract: literal form, communicative force, cognitive goal, grounding status, interaction relation, and evidence are separate labels.
- The current disagreement classes are provisional; indirect information request, assertion/report, compound event, and parser/classifier error must be distinguished before arbitration policy is promoted.
- Expanded `tests/fixtures/comprehension_divergence/phase1_adjudications.json` to **20** independently adjudicated events, adding direct information/action requests, ordinary assertions, unresolved action requests, and social coordination.
- Adjudication verification: **3 tests passed** (JSON/schema coverage, independent force/form separation, and raw corpus measurement).
- Added graph-native `seeds/communication_intent_arbitration.json`; runtime arbitration matches all ten adjudicated force/goal labels, including indirect requests and the declarative gap-report correction.
- Expanded runtime route measurement before the action-evidence upgrade was **19/20 (95.0%)** with one false action route. After the upgrade it is **20/20 (100.0%)**, with false action, false answer, and false repair all at **0**.
- Added canonical action/account evidence in `domains/comprehend_text.py`: a recognized politeness-prefixed clause can use the held verb-head faculty when primary POS is misleading, and reporting/enumeration force survives POS-lattice fragmentation, while native speech-act evidence remains separately auditable.
- Replaced graph arbitration's English predicate/path matching with `communication_evidence.v1`: the language adapter emits neutral force/goal evidence, and graph rules consume only the evidence schema. English-specific markers and POS/order assumptions remain confined to the current English evidence provider and are not part of the cognitive ontology.
- Added `tests/test_language_neutral_evidence_arbitration.py`, where a synthetic semantic adapter drives all five force/goal classes without English words, POS, mood, or dispatch-path fields.
- Added `domains/communication_evidence.py` and Spanish/Japanese semantic-frame variation coverage in `tests/test_language_neutral_variation.py`; the unchanged graph rules pass both languages through the neutral evidence boundary.
- Installed `pyarrow` into the repository `.venv` and enabled the live `LanguageWorld` text-to-frame integration test; Spanish and Japanese frames now cross the neutral evidence boundary successfully.
- Runtime adjudication and expanded-metric gate: **4 tests passed**; existing conversation-loop regression: **12 passed**.
- Added held-out `tests/fixtures/comprehension_divergence/phase1_generalization.json` covering information requests, action requests, repair/defer, assertion/common-ground update, and social coordination.
- Added parser-gap arbitration so unresolved lexical gaps become `repair_or_defer` while ordinary declaratives with non-gap grounding imperfections remain assertions.
- Held-out generalization gate: **1 passed**; combined Phase 1 focused suite (adjudication, runtime interpretation, and generalization): **8 passed**.
- Phase 1 exit evidence: 20/20 force/goal agreement, zero false action/answer/repair routes, neutral synthetic-provider coverage, and live Spanish/Japanese LanguageWorld integration.
- Next phase: begin Phase 2 grounding/reference/epistemic-state work; retain the Phase 1 route and language-variation batteries as regression gates.

### Phase 2 — Initial increment completed

- Start: 2026-09-22
- Added durable `TopicGroundingEvidence` records for persisted `HeldAnswer` data, with explicit referent, support status, source, and evidence path.
- Added compact evidence fields to `HeldAnswer` so graph topic-reply arbitration can require a referent match, supported status, and non-empty evidence path before setting `Goal.outcome='resolved'`.
- Added `_has_topic_grounding_evidence` as a mechanical readback guard for the synchronous fulfiller; unsupported/legacy candidates fall through to the honest unresolved outcome.
- Fixed a cognition-level arbitration conflict: when a follow-up is both generically instructional and graph-routed to an answer topic, the specific grounded topic goal takes precedence.
- Added `test_topic_resolution_requires_referent_linked_evidence`, which poisons a same-key candidate and verifies that unrelated content is not returned as a resolved answer.
- Focused verification: topic tracking suite **6 passed, 1 skipped**; evidence regression **1 passed**; the initial combined run exposed and then fixed the instruction-vs-topic arbitration conflict.
- Remaining work: tighten the unresolved rule's evidence predicate, add multi-referent/coreference and retrieval-candidate coverage, and measure grounding precision/recall across the Phase 0 corpus.

### Phase 0 — Evaluation contract

- Owner: unassigned
- Start: 2026-09-22
- Evidence: versioned 74-event labelled corpus, stratified coverage metadata, deterministic event-trace validator, and non-turn/turn-compatible trace tests. The live trace gate checks neutral evidence, force/goal hypotheses, grounding/gap evidence, intent, goals, mentions, concerns, parse evidence, and reply provenance.
- Blockers: baseline scores and complete candidate-generation traces require later runtime/evaluation phases
- Next action: retain this corpus as the Phase 0 regression substrate; do not treat fixture labels as runtime accuracy until a later measured harness adjudicates them

### Phase 1 — Intent arbitration

- Owner: unassigned
- Start: 2026-09-22
- Evidence: graph-resident interpretation, science-grounded adjudication fixture, seeded force/goal arbitration policy, and held-out generalization fixture
- Blockers: none for the current exit criteria; broader adjudication and compound-event coverage remain future hardening
- Next action: maintain as regression gate; expand compound-event and language-neutral adjudication coverage

### Phase 2 — Grounding and epistemic state

- Owner: unassigned
- Start: 2026-09-22
- Evidence: `TopicGroundingEvidence`, `HeldAnswer` referent/status/path fields, graph reply gate, synchronous fulfiller guard, and unrelated-answer regression
- Blockers: live SUT grounding precision/recall is low and the unrelated-answer gate has violations; broader retrieval/reference coverage remains
- Next action: use the measured false-grounding cases to tighten cognition-level grounding arbitration without treating a reply as evidence

### Phase 6A — Cognitively gated production release

- Start: 2026-09-22
- Added `domains/production_gate.py` as a bounded release seam for the existing
  parse-back/output-null monitor. A surface is released only when its selected
  semantic frame has an event, intent, and content role, the monitor verdict is
  recoverable, and a committed monitor node exists.
- Successful releases now leave a graph-resident `ProductionGateReceipt` linked
  to the committed record, carrying the released surface, semantic content,
  parse-back mode, coverage, and recoverability. Missing evidence remains
  buffered for the existing one-repair attempt and then the explicit error
  floor; no acknowledgement or `noted` fallback is introduced.
- Every gate attempt now leaves a receipt: `released` for complete evidence or
  `withheld` with explicit reasons for empty output, forbidden fallback,
  missing semantics, failed parse-back, or missing commitment. The production
  path uses the same seam for recoverable and output-null candidates.
- Added `tests/test_phase6a_production_gate.py`: release evidence contract,
  missing-evidence withholding, forbidden-fallback rejection, live frame-
  production receipt coverage, and two-attempt output-null audit coverage.
- Focused verification with the repository `.venv`: Phase 6A plus output-null
  suite **10 passed**; adjacent active-frame production regression included in
  the combined run **12 passed**. `py_compile` and `git diff --check` pass.
- Added a bounded legacy fact-readback gate: the existing structural renderer's
  relation, subject, and object must survive deterministic parse-back before a
  `ProductionGateReceipt` can release the answer. A two-case semantic corpus
  covers `is_a(graph, structure)` and `uses(process, data)`; forced parse-back
  failure withholds output and preserves the explicit error floor.
- Verification with the repository `.venv`: Phase 6 production gate,
  output-null, and legacy-readback suite **12 passed**; the adjacent QA,
  relation-rendering, and conversation-unification regressions were **32
  passed, 1 stale noted assertion deselected**. JSON validation, `py_compile`,
  and `git diff --check` pass.
- Expanded the fixed semantic production corpus from two facts to ten
  substantive binary-relation readbacks, covering unmarked, marked, taxonomy,
  containment, optimisation, support, observation, mapping, and ownership
  relations. Added end-to-end `answer_question` traversal assertions and
  receipt-count/release-status checks, so direct retrieval and the legacy QA
  route are both covered by the same production gate.
- Closed the cached-readback bypass found during audit: `answer_question` now
  re-runs graph-resident fact answers through `answer_about` and retains the
  comprehension cache only as fallback for non-fact learned answers. The
  two-pass corpus test records **20/20 released receipts** for 10 facts,
  proving repeat reads do not evade parse-back evidence.
- Verification with the repository `.venv`: Phase 6 gate, legacy corpus,
  output-null, and QA tests **20 passed**; adjacent relation-render and
  conversation-unification regressions also pass below. No `noted` surface is
  released; failed evidence remains withheld and reaches the explicit error
  floor through the existing caller.
- Extended the legacy readback battery across the substantive question faculty:
  `what is`, `what's`, and `what are` routes all re-enter the same
  semantic parse-back/release gate for every fixed-corpus fact. Added a routed
  parse-back failure regression proving that question readback produces a
  withheld receipt rather than a released or `noted` surface.
- Local verification for this increment: Phase 6 production/readback,
  output-null, and QA tests **24 passed**. The adjacent regression command
  reported **35 passed, 1 skipped, 3 failures**; all three failures are stale
  assertions expecting the forbidden `noted` acknowledgment in
  `tests/test_full_turn_migrated.py`. JSON validation, `py_compile`, and
  `git diff --check` passed.
- This bounded Phase 6D increment covers the remaining overt legacy QA forms;
  computational faculties such as predicate evaluation and `answer_within`
  remain cognition results rather than overt production surfaces and are not
  incorrectly routed through a conversation release gate.
- Remaining work: broaden the corpus beyond the bounded binary-relation
  family and audit any additional legacy faculties that emit substantive
  surfaces; this increment does not claim full G6.1 acceptance.
- Remaining work: extend the same receipt/release gate to every other
  substantive legacy readback path and establish the larger fixed production
  corpus required for G6.1; this increment does not claim full Phase 6
  acceptance.

### Phase 6E — Legacy readback path audit and taught-answer gate

- Audited the repository's substantive legacy surface readers. The actual
  routes are direct `WorldAdapter.answer_about`, the fact branch of
  `WorldAdapter.answer_question`, the live question branch of
  `WorldAdapter.converse`, and the taught-capability fallback inside
  `answer_about`. `answer_predicate` and `reason.answer_within` return boolean
  or numeric cognition results rather than overt surfaces and are therefore
  excluded from a production utterance release corpus. Frame production via
  `_realize_frame_reply` already has its own Phase 6 gate.
- Closed the remaining cached-readback bypass: taught answers now use the same
  `legacy_structural_readback` parse-back and `ProductionGateReceipt` release
  seam as graph-resident facts. A topic whose selected referent is not
  recoverable is withheld; a plural topic may recover through its deterministic
  singular structural form (for example `volcanoes` / `volcano`).
- Expanded the semantic relation corpus from 10 to 14 binary cases and added
  path-level tests for direct, question-front-end, live-conversation, taught,
  and forced-failure routes. Explicit error behavior remains observable and no
  `noted` surface can be released.
- Phase 6E local verification: repository `.venv` focused Phase 6 suite **27
  passed in 16.43s** (`test_phase6a_legacy_readback.py`,
  `test_phase6a_production_gate.py`, `test_output_null_gate.py`, and
  `test_qa_migrated.py`). The adjacent topic/self-healing command reached
  **6 passed** before being stopped at 180s in the pre-existing slow
  `self_model.py` path; it was not a Phase 6 failure and the full repository
  suite was not run. The 14-case JSON corpus, Phase 6 Python compilation, and
  relevant-file `git diff --check` all pass. G6.1 remains yellow until the
  full production corpus and every additional substantive surface faculty are
  covered.

### Phase 5A — Gap identity and verified self-correction

- Start: 2026-09-22
- Added `seeds/gap_identity.json` with graph-native `gap_identity.v1`
  canonical identities that preserve cognitive kind, source, content, and
  originating turn/goal provenance. Message-linked concerns use the message
  turn; unresolved topic goals now retain the originating event id as a
  mechanical datum before `gap_awareness` decides whether to file a gap.
- Narrowed legacy duplicate retirement to the cognitive identity components
  already available at filing time (kind/source/content), so same-text gaps
  with different cognitive kinds are not silently collapsed. The canonical
  identity remains metadata for later recurrence, prioritisation, promotion,
  verification, and retirement; it does not make a learning decision.
- Added graph-native correction verification with immutable original concern
  content, `CorrectionRecord` provenance, corrected level-2 `RouteModel`, and
  visible failed-correction state.
- Verification with the repository `.venv`: gap identity suite **2 passed**;
  legacy gap dedup/retirement regressions **2 passed**; human-gated promotion
  and seed reconciliation checks **2 passed**. JSON validation, Python
  compilation, and `git diff --check` also pass. No Python-side canonicalisation
  or learning decision logic was added.
- Remaining work: connect identity to recurrence/prioritisation and verify the
  repaired route through the broader promotion and future-conversation loop;
  the full 15-test gap/promotion battery remains resource-heavy and was not
  used as Phase 5A exit evidence in this increment.

### Phase 5B — Identity recurrence and future-route application

- Added `seeds/gap_learning_phase5b.json`, keeping recurrence as graph state
  keyed by `gap_identity`: one `GapRecurrence` node records recurrence count
  and priority for an identity, so repeated historical occurrences do not mint
  duplicate recurrence records.
- Connected verified `RouteModel` provenance to the matching recurrence node;
  a later `Goal` carrying the same identity is routed through the learned route
  exactly once. The original concern remains historical evidence and no second
  active concern is required for route application.
- Added `tests/test_gap_learning_phase5b.py` covering verified-route transfer,
  identity-keyed recurrence/priority, and no duplicate concern for the future
  route case.
- Verification with the repository `.venv`: Phase 5B focused suite **2 passed
  in 0.21s**; the existing Phase 5A identity/correction slice remained green
  (**4 passed** in the combined run before the Phase 5B test correction).
- Phase 5 remains partial: broader promotion, recurrence across real
  conversation/task events, and the resource-heavy full gap/promotion battery
  remain outside this bounded increment.

### Phase 5C — Recurrence pressure and supervised promotion assessment

- Added `seeds/gap_learning_phase5c.json`, a graph-native assessment seam that
  connects a recurrent `GapRecurrence` to one `GapLearningAssessment` once its
  recurrence count reaches two. The assessment preserves recurrence evidence,
  records failed-repair count, and marks the case `human_review`; it never
  auto-promotes, closes the concern, or rewrites its content.
- Added `tests/test_gap_learning_phase5c.py` with a failed-repair battery and an
  eight-identity resource-heavy replay. The tests verify visible failed
  `CorrectionRecord` state, stable identity recurrence, no duplicate concern
  for the repeated route, one assessment per identity, and idempotent replay.
- Verification with the repository `.venv`: Phase 5C **2 passed in 0.22s**;
  the combined Phase 5A/5B/5C focused battery **8 passed**. JSON validation,
  Python compilation, and `git diff --check` also pass.
- Remaining work: exercise the assessment through the broader real
  conversation/task promotion pipeline and the full resource-heavy gap/
  promotion corpus; human-gated promotion remains intentionally separate from
  this graph assessment.

### Phase 5D — Actual recurrence, review, repair, verification, and decision

- Added `seeds/gap_learning_phase5d.json`, which opens one graph-resident
  `HumanReview` for a recurrent `GapLearningAssessment`, records failed repair
  attempts as durable `FailedRepairRecord` evidence, and requires an explicit
  human `approve` or `retire` decision before changing recurrence state.
- Verified repair creates a `RepairVerification` only after explicit approval;
  promotion and retirement both record `human_review` authority. No rule
  automatically closes a concern, promotes a route, or retires a recurrence.
- Added `tests/test_gap_learning_phase5d.py` covering task recurrence through
  review, failed repair visibility, verified promotion, and explicit retirement.
- Verification with the repository `.venv`: Phase 5D **3 passed**; the full
  Phase 5A/5B/5C/5D focused battery **11 passed**. JSON validation, Python
  compilation, and `git diff --check` passed.
- Phase 5 remains partial: broader real conversation/task promotion and
  resource-heavy end-to-end coverage remain.

### Phase 5E — Real conversation ingress and repeated-task decision coverage

- Added `tests/test_gap_learning_phase5e.py`. One test drives the live
  `WorldAdapter.converse()` unresolved-topic path and verifies that its
  graph-resident `SelfConcern` carries a `gap_identity.v1` origin turn before
  an explicit call to the existing human promotion gate creates a pending
  `StandingConcern`; `converse()` does not promote it automatically.
- The second test runs two historical task stages under one opaque stable task
  identity, then drives recurrence → human review → failed repair → verified
  retry. Failed repair remains graph-visible and the assessment remains
  `human_review` until explicit `approve`; a separate repeated task reaches
  `retired` only after explicit `retire`.
- Local `.venv` verification: Phase 5E **2 passed in 44.22s**. The broader
  Phase 5A–E battery remains the follow-up verification for this increment.
- Phase 5 remains partial: production-scale conversation/task corpus coverage
  and broader promotion-resource stress are still open.

### Phase 5F — Production-shaped recurrence and promotion stress

- Added a bounded production-shaped corpus of 24 opaque task identities and 72
  historical conversation/task events. Each identity is observed through
  conversation, task attempt, and retry stages, with one failed correction
  evidence node. Recurrence is keyed by graph identity rather than surface
  language.
- Verified one `GapRecurrence`, one `GapLearningAssessment`, one visible
  `FailedRepairRecord`, and one pending human review per identity. All 24
  assessments reach the recurrence threshold and remain `human_review` with
  `auto_promoted=0`; no standing
  concern, automatic promotion, or automatic closure is created.
- Verified that one explicit human approval promotes only its selected
  identity and one separate explicit human retirement retires only its
  selected identity; replay does not alter the remaining assessments.
- Local `.venv` verification: Phase 5F **1 passed in 0.25s**; the current
  combined Phase 5A–F battery **27 passed in 15.60s**. The five Phase 5 seed manifests
  parsed successfully, `py_compile` passed, and scoped `git diff --check`
  passed.

### Phase 0 — Expanded evaluation contract slice

- Start: 2026-09-22
- Expanded `communication_event_corpus.v1` in `tests/fixtures/conversational_manifold/phase0_events.json` to 74 independently labelled events spanning non-turn and turn-compatible modes, standalone/continuation/overlap/response relations, all declared force/goal/grounding/state strata, and expected cognitive states.
- Added `evaluation/conversational_manifold_phase0.py` for deterministic schema validation and event-trace contract assertions.
- Added coverage metadata and validation for the planned 60–100 corpus and its trace dimensions: interpretation, intent, goal lifecycle, mention/referent, topic, self-concern, parse evidence, and reply provenance.
- Extended `tests/test_phase0_evaluation_contract.py`: corpus independence/validation checks plus live event-based trace assertions for streaming, asynchronous, and unsolicited interaction modes. Assertions inspect neutral graph evidence, grounding/gap fields, graph interpretation/provenance, and `donkey=0`; they do not snapshot surface wording.
- Added [Phase 0 evaluation contract](CONVERSATIONAL_MANIFOLD_PHASE0_EVALUATION_CONTRACT.md).
- Verification: Phase 0 focused suite and dependent Phase 8 corpus-loading tests pass with the repository `.venv` command.
- Added a conditional candidate/lifecycle cross-reference to the native Phase 4 contract (`seeds/conversation_deliberation_phase4a.json`) and a validator for observed source, candidate count, lifecycle completion, and resolved settle-back evidence. The fixed 74-event corpus carries no synthetic candidate records; events without an actual deliberation remain untraced rather than being mislabeled `no_candidate`.
- Verification: the Phase 0 suite now covers the conditional cross-reference and observed Phase 4 lifecycle shape; full candidate generation remains governed by the Phase 4 native tests.

### Phase 3 — Exit slice

- Start: 2026-09-22
- Added `domains/discourse_state.py` with a graph-resident `DiscourseState` schema, event records, goal origin/addressee/evidence links, guarded lifecycle transitions, and explicit fulfilled/deferred/error expectation closure.
- Added `seeds/conversation_discourse_state.json` as the vocabulary manifest; no Phase 2 topic files or broad world-adapter code were changed.
- Added `tests/test_discourse_state_phase3a.py`: idempotent state/event residence, proposed→selected→executing→resolved lifecycle with no orphaned active goal, invalid-transition rejection, and defer/error-compatible expectation closure.
- Verification: local `.venv` command `PYTHONPATH=runners/dsl/python:. .venv/bin/python -m pytest -q --tb=short tests/test_discourse_state_phase3a.py` => **4 passed**; JSON validation, Python compilation, and `git diff --check` also pass.
- Added `ensure_common_ground` with graph-resident `CommonGround{schema:'common_ground.v1'}` revision/claim state, participant/addressee links, and event contribution edges.
- Extended discourse-state integration so events retain speaker/addressee identity and goals inherit the state's conversational addressee when one is established.
- Added `tests/fixtures/conversational_manifold/phase3_mixed_act_dialogue.json`, a ten-event mixed-act sequence spanning request, selection, execution, result, assertion, question, and explicit epistemic repair/defer.
- Added `tests/test_discourse_state_phase3_exit.py`: ten-event state/common-ground/addressee assertions and native seed-loaded goal lifecycle execution.
- Added `conversation_discourse_state` seed registration and three native rules for proposed→selected→executing→resolved transitions, with transition-event provenance and closed-goal linkage.
- Verification with the repository `.venv`: Phase 3A plus exit suite **7 passed**; JSON validation, Python compilation, and `git diff --check` pass.
- Phase 3 exit slice is complete. Remaining future hardening is longer dialogue stress, richer interlocutor models, and native handling of blocked/repaired/abandoned branches; these are outside this bounded exit scope.

### Phase 3 — Common-ground/addressee stress increment

- Added `phase3_common_ground_stress.json` and a bounded ten-event stress test
  with two addressees, interleaved goals, observations, assertions, native
  selections/executions/results, and zero reply events.
- Tightened `record_event` so every event recipient is incorporated into the
  graph-resident common-ground participant ledger, including the agent as an
  event recipient. This preserves event-level address without making the
  discourse model turn-dependent.
- Verified both goals can be advanced and closed over mixed communication
  events while unrelated observation/assertion events remain in the event
  stream; no reply event is synthesized or required.
- Verification: local `.venv` Phase 3A plus exit suite, including the new
  stress fixture, passed **9 tests**. JSON validation, Python compilation,
  and `git diff --check` passed.

### Phase 7A — Native cycle measurement and replay determinism

- Start: 2026-09-22
- Added evaluation-only `evaluation/native_cycle_measurement.py`; it constructs a
  graph-authored native transition, runs a bounded Rust `default` cycle, and
  records native reports, graph node/edge residence, wall latency, and peak RSS.
- Added `tests/test_native_cycle_measurement.py`: bounded measurement, native
  graph-authored transition, and fresh-process-equivalent replay comparison.
- Added [Phase 7A measurement protocol](CONVERSATIONAL_MANIFOLD_PHASE7A_NATIVE_MEASUREMENT.md).
- Local `.venv` verification: focused native measurement plus existing cycle
  regressions **11 passed**; `py_compile` and `git diff --check` pass.
- Local measurement (`8` measured cycles, `1` warm-up): median latency **0.080875
  ms**, min/max **0.077741/0.104111 ms**, graph residence **11 nodes / 9 edges**,
  peak RSS **23,519,232 bytes**, replay determinism **true**. The measured
  cycles were settled (`0` additional steps after warm-up); the no-warm-up test
  confirms the native transition takes one step.
- Added bounded `fast`, `deep`, `recovery`, and `long_dialogue` native
  measurement profiles. The profiles assert fixed native step/graph ceilings,
  replay equality, and graph residence without Python-side selection logic.
- Local `.venv` verification: profile/replay suite **3 passed**; exact
  eight-cycle measurements were replay-equal for all four profiles. Profile
  residence: fast **11/9**, deep **34/32**, recovery **22/20**, and
  long-dialogue **42/40** nodes/edges. Warm-up-free native steps were fast
  **1**, deep **1**, recovery **2**, and long-dialogue **1**; later cycles settle
  to zero. Workload-size and graph-residence measures carry the
  depth/dialogue scaling without overstating cycle-step counts.
- The bounded Phase 7 performance-envelope increment is complete. Phase 7
  remains 🟡 because native-authority coverage for remaining cognitive
  decisions and broader resource envelopes are still open.

### Phase 8A — Comparative evaluation and release-gate scaffold

- Start: 2026-09-22
- Added the evaluation-only `comparative_cognition_evaluation.v1` contract in
  `evaluation/comparative_release_gate.py`.
- Fixed the reference classes to `eliza_floor`, `small_llm`, `modern_llm`,
  `base_human`, and `advanced_human`; fixed the cognition dimensions to
  interpretation, grounding, action, repair, memory, learning, calibration,
  provenance, and cost.
- Required scorecards to carry all dimensions, sample count, confidence
  interval, raw-metric description, and evidence references. Overlapping
  intervals are reported as `indeterminate`; missing evidence blocks release.
- Added five focused scaffold tests. Local `.venv` verification:
  `tests/test_phase8a_comparative_release_gate.py` => **5 passed**.
- Added [Phase 8A comparative evaluation protocol](CONVERSATIONAL_MANIFOLD_PHASE8A_COMPARATIVE_EVALUATION.md).
- No runtime cognition or Phase 2–7 implementation files were edited.
- Remaining work: bind the contract to the fixed corpus, collect real repeated
  baseline observations, publish confidence intervals/failure slices, and
  produce the dated G8.1 comparison report.

### Phase 4A — Deliberative candidate generation/arbitration audit

- Start: 2026-09-22
- Added `domains/conversation_deliberation.py` as a mechanical evidence boundary. It materializes an explicit candidate ledger but performs no ranking, selection, or fallback choice.
- Added `seeds/conversation_deliberation_phase4a.json`: native rules score grounded candidates, collapse through graph `Argmax`, trace the selected candidate, reject unsupported and outcompeted candidates, and expose `no_candidate` when no grounded candidate remains.
- Added `tests/test_conversation_deliberation_phase4a.py` covering winner/rejection traces, explicit no-candidate state, and an adapter audit forbidding Python ranking calls.
- Verification: local `.venv` Phase 4A suite => **3 passed**; JSON validation, Python compilation, and `git diff --check` pass.
- Boundary: this is not full Phase 4 acceptance. Candidate generation is supplied as evidence-bearing input, and live thought-manifold integration, counterfactual credit, and settle-back trace coverage remain open.

- Phase 4 bounded integration: added `materialize_from_thought_manifold(...)`, a real graph-resident `ThoughtManifold -> proposes_candidate` source seam. The adapter copies evidence and provenance only; native rules still score and collapse candidates. Added native execution and resolved settle-back trace rules, including explicit rejection provenance for unsupported proposals. Local `.venv` Phase 4 suite => **5 passed**. Full thought-manifold generation and counterfactual credit assignment remain open.

- Phase 4C bounded counterfactual trace: added native `cm4b_credit_grounded_rejected_alternatives`. After a grounded selected candidate resolves, each grounded alternative rejected by native collapse receives one graph-resident `CounterfactualCredit` node containing the selected/alternative IDs, observed winner outcome, score margin, and negative alternative credit. Unsupported candidates are excluded, and the trace is explicitly marked `unexecuted_alternative`; no counterfactual outcome is represented as observed fact. Local `.venv` Phase 4 suite => **6 passed**. Full manifold candidate generation and repeated-task credit validation remain open.
- Phase 4D bounded graph-state candidate generation: added `materialize_from_discourse_state(...)`, which derives evidence-bearing proposals directly from graph-resident active goals, linked residual stance/repair nodes, and unresolved residual state. It records source provenance while leaving valuation, native collapse, rejection, and counterfactual credit to the seeded rules. An empty cognitive evidence set now reaches an explicit native `no_candidate` state rather than requiring an externally supplied candidate list. Focused local `.venv` Phase 4 deliberation/settle-back suite => **10 passed**. Remaining Phase 4 work: broader live thought-manifold generation and repeated-task credit validation.

- Phase 4E bounded live-manifold generation: added `materialize_from_live_thought_manifold(...)`, which derives proposals from four distinct graph-native evidence relations (`has_goal_evidence`, `has_repair_evidence`, `has_stance_evidence`, and `has_residual_evidence`). The boundary preserves source relation/provenance and transports only pre-existing numeric evidence; native rules remain authoritative for scoring, collapse, rejection, execution, settle-back, and empty-evidence `no_candidate`. The adapter has an AST regression forbidding Python outcome-selection calls. Local `.venv` Phase 4 deliberation/settle-back suite => **14 passed**. Remaining Phase 4 work: repeated-task counterfactual-credit validation.
- Phase 4E repeated-task counterfactual validation: replayed four graph-native thought-manifold tasks through the same native valuation, execution, settle-back, and counterfactual-credit path. Each replay preserved grounded winner evidence, recorded exactly one grounded rejected alternative, produced stable credit/margin, and remained idempotent across additional native settling. Python supplied only graph evidence and observed outcomes; it did not select candidates. Local `.venv` Phase 4 suite => **11 passed**. Remaining Phase 4 work: broader live-manifold/task-family coverage beyond this bounded replay.
- Phase 4F task-family lifecycle validation: exercised live graph-manifold generation for action, repair, social, and information evidence. Each family preserved source-relation provenance, native winner collapse, unsupported and outcompeted rejection traces, resolved execution/settle-back, and exactly one grounded rejected-alternative counterfactual trace with positive winner margin and negative alternative credit. The family matrix changes only cognitive evidence kind/relation; it introduces no language or reply-text shortcut and performs no Python selection. Local `.venv` Phase 4 task-family, deliberation, and settle-back suites => **22 passed** (including 4 family cases). Remaining Phase 4 work: broader task-family/manifold corpus coverage.

### Phase 2B — Reference evidence boundary

- Added `domains/reference_resolution.py` with graph-resident
  `ReferenceResolutionEvidence`, explicit `supported`/`unknown` status, and
  evidence paths for resolved and unresolved references.
- Verification: local focused reference suite **5 passed**.
- Connected retrieval candidate selection to the referent-evidence boundary:
  requests carry explicit supported/unknown referent status and evidence path;
  candidates carry per-referent coverage and native selection requires complete
  supported coverage. Multi-referent requests therefore cannot resolve from a
  partial candidate, and unknown/unresolved references remain unknown.
- Retrieval remains a cognition input: it writes `SearchCandidate`,
  `RetrievalEvidence`, and `HeldAnswer` data but never creates a
  `CommunicationInterpretation` or `Message` and never claims a communication
  event.
- Added Phase 2 coverage for compound referents, unresolved coreference, and a
  resolved discourse referent handed to retrieval explicitly. Local `.venv`
  verification: **9 Phase 2 evidence tests passed**; the existing topic suite
  remains a separate regression gate.
- Remaining work: broader retrieval/reference corpus and grounding
  precision/recall measurement across the Phase 0 corpus.

### Phase 2D — Fixed-corpus grounding precision/recall measurement

- Added the evaluation-only `phase2_grounding_measurement` adapter over all 74
  Phase 0 events. It uses four explicit language-neutral labels: `referent`,
  `coreference`, `unknown`, and `contradiction`.
- `grounded` and `partially_grounded` are annotated as `referent`;
  `unresolved_reference` as `coreference`; `unknown` and `unavailable_world`
  as `unknown`; and `contradicted` as `contradiction`. Runtime labels are
  derived only from grounding evidence, never from reply text or answer shape.
- The report includes expected/observed counts, a four-by-four confusion
  matrix, per-label precision/recall/F1, macro metrics, and an explicit
  unrelated-answer-resolution violation list. A non-referent event observed
  as referent is a failure even when a reply is present.
- Fixed-corpus contract verification: **3 tests passed**. Identity replay
  measurement is 100% precision/recall/F1 across all four labels; the poisoned
  unknown case produces one referent false positive, one unknown false
  negative, and one unrelated-answer-resolution violation.
- Historical pre-correction live SUT result over 74 events: expected labels were referent **50**,
  coreference **6**, unknown **16**, contradiction **2**; observed labels were
  referent **33** and coreference **41**. Per-label precision/recall/F1 were
  referent **0.6364/0.4200/0.5060**, coreference **0/0/0**, unknown **0/0/0**,
  and contradiction **0/0/0**. Macro precision/recall/F1 were
  **0.1591/0.1050/0.1265**. The unrelated-answer-resolution gate recorded
  **12 violations** (`unresolved_reference`, `unavailable_world`,
  `question_weather`, `question_unavailable`, `action_pronoun`,
  `repair_clarify`, `action_world_unknown`, `info_unknown`, `info_world`,
  `info_reference`, `blocked_reference`, `action_referent`). This is a
  measured SUT failure, not a passing result.
- Latest binary live SUT rerun over 74 events: true positive **19**, false
  positive **0**, false negative **31**, true negative **24**, giving precision
  **1.0000**, recall **0.3800**, and F1 **0.5507**. The authority and
  anaphora guards preserve the zero-false-positive boundary.
- Remaining work: broader retrieval/reference/task corpus coverage, recall
  recovery, semantic answer-quality scoring, and live multi-context
  precision/recall beyond the fixed 74-event run.

### Phase 2E — Runtime false-grounding correction

- Replaced the interpretation record's unconditional `candidate_grounded`
  default with a graph-evidence predicate. External topic support now requires
  a held-answer/topic-grounding path or an explicitly resolved referent path;
  unresolved references, unavailable-world requests, unknown topics, and
  unsupported/contradictory parses remain `unresolved` with an empty grounding
  evidence path. Self/faculty routes retain their separate selected-faculty
  evidence, and retrieval remains non-claiming.
- Added a post-retrieval graph refresh so a newly persisted, referent-linked
  `HeldAnswer` can promote the interpretation only after its evidence exists;
  reply text alone cannot promote it.
- Added bounded runtime regressions for the prior false-grounding classes plus
  legitimate held-answer behavior and the three targeted cases. Local `.venv`
  verification: **20 Phase 2 reference/measurement tests passed**, including
  **3 focused regressions**. The post-fix 74-event SUT rerun records **0 false
  positives** (precision **1.0000**) but remains conservative at recall
  **0.3800** (TP 19, FN 31); Phase 2 therefore remains yellow pending recall
  recovery and the four-label post-fix measurement.
- Added provenance-first false-negative categorisation without promoting
  declared paths to evidence. The historical pre-exposure analysis identified
  **16** declared graph paths, **14** declared discourse-state paths, and **9**
  surface/uncertainty-only cases as unverified. The current corpus report now
  exposes **15** verified grounded paths: **8** selected graph faculties and
  **7** `Concept.referent` paths. Recall work remains gated on actual graph
  links rather than labels or reply text.

### Phase 2F — Discourse referent and authority-state increment — 2026-09-23

- Grounded topic readback now writes an explicit `CurrentTopic` paired with an
  in-focus `DiscourseReferent`; later anaphoric comprehension may use that
  state only when the graph binding is present. A direct follow-up probe
  resolved to the grounded `know` path while correctly withholding an answer
  when no causal fact was available.
- Held answers without an `answer_topic` Goal now use the matching
  graph-resident `HeldAnswer` as the production commitment. The `gate` probe
  released `The gate is open.` with a `conversation_information_graph`
  receipt; arbitrary dictionary/source text is not accepted as a substitute.
- Permission evidence is event-scoped. An unrelated authority decision in the
  live graph cannot authorize a new request; missing request-linked authority
  remains `authority_missing` and must fail closed.
- Anaphoric questions now pass through the same production boundary: a bound
  pronoun is not sufficient evidence for a new causal/relational answer, and a
  lexical HeldAnswer for the pronoun cannot escape as an unrelated response.
- Verification: `.venv` targeted bridge/reference tests passed; the latest
  74-event replay measured TP **19**, FP **0**, FN **31**, TN **24** and
  production evidence of **40** released receipts, **34** explicit errors,
  **74** cognitive traces, and **74/74** manifest coverage.

### Phase 2G — Reference-faculty dispatch and committed topic readback — 2026-09-23

- Wired the existing `conversation_action.reference_reply` faculty into the
  live event path. Genuine own-name and manifold-conditioned references now
  cross the same production gate as other substantive replies; no reference
  wording or recognition is invented by the adapter.
- Topic commitments are now restored from graph-resident `HeldAnswer` evidence
  before and after pending retrieval settlement. A later retrieval candidate
  cannot overwrite an already selected grounded topic surface before exact
  production readback.
- The canonical error remains the outcome when no committed graph answer can
  be recovered; the gate was not loosened.
- Local `.venv` verification: complete reference/overfire and topic-tracking
  regression battery **18 passed**. `py_compile` and `git diff --check` passed.
- The post-correction 74-event SUT replay is now measured at TP **22**, FP
  **0**, FN **28**, TN **24**: precision **1.000**, recall **0.440**, F1
  **0.611**. This is an improvement over the prior 19/31 result, but recall
  remains below the Phase 2 exit threshold and the corpus still has no
  memory/learning/cost probes.

### Phase 2H — Grounding/authority separation audit — 2026-09-23

- Permission-shaped communication now records referent grounding and authority
  as separate graph facts when referent evidence is actually present;
  `authority_status="missing"` still blocks production independently.
- Focused `.venv` verification: **40 passed**, including permission,
  reference, topic, and grounding regressions.
- The 74-event replay remains TP **22**, FP **0**, FN **28**, TN **24**;
  recall did not change because the affected corpus events lack the required
  request-linked referent evidence. No recall improvement is claimed from the
  correction; the next increment must add or measure that evidence rather than
  relabel authority-missing events as grounded.

### Phase 7B — Native stress profiles

- Added evaluation-only `fast`, `deep`, `recovery`, and `long_dialogue`
  profiles recording latency, RSS, graph residence, native steps, replay
  equality, and resource ceilings.
- Profile residence: fast **11/9**, deep **34/32**, recovery **22/20**, and
  long-dialogue **42/40** nodes/edges; replay equality held across profiles.
- Verification: native profile suite **3 passed**; adjacent native battery
  **23 passed**. Broader resource envelopes and native-authority audit remain.

### Phase 7C — Dense-neighbourhood native-authority audit

- Added a bounded `dense_graph` profile with twelve candidates and 44
  native-visible edges, exercising a dense graph neighbourhood without
  Python-side outcome selection.
- Added explicit authority evidence to the measurement result: pre-cycle
  graph, native trace/step alignment, native trace as outcome source, and
  post-cycle graph mutation.
- Added regression coverage requiring all candidates to change from
  `resolved=0` to `resolved=1` across the native cycle, with replay, step,
  and graph ceilings preserved.
- Local `.venv` verification: Phase 7 measurement suite **4 passed**.
- Phase 7 remains 🟡: this closes the bounded dense-neighbourhood authority
  increment; broader native-authority coverage and resource envelopes remain.

### Phase 7D — Ambiguity and repeated-gap native envelopes

- Added graph-authored `ambiguity` and `repeated_gaps` profiles to extend the
  native-authority/resource envelope beyond the existing dense, recovery, and
  long-dialogue workloads. Ambiguity contains eight competing evidence-bearing
  candidates; repeated gaps contain eight recurrent gap nodes traversing native
  detect and repair transitions.
- Added assertions for native trace/step alignment, replay equality, graph and
  step ceilings, graph mutation, and complete target-state coverage. Python
  remains an I/O/measurement boundary and does not select outcomes.
- Local `.venv` verification: Phase 7 measurement suite **6 passed**.
- Phase 7 remains 🟡 for broader resource envelopes and additional native
  authority workloads beyond this bounded increment.

### Phase 7E — Broader native resource-envelope loads

- Added bounded `extended_dialogue`, `high_ambiguity`, and `graph_growth`
  profiles. These increase the event/candidate load to 96, ambiguity to 32
  competing candidates, and graph growth to 48 candidates with 144 workload
  edges (152 total canonical edges including native rule edges).
- Added explicit per-profile node/edge/step limits rather than sharing the
  smaller seven-profile ceiling. Each workload still records replay equality,
  native trace/step alignment, graph mutation, and native authority; Python
  performs only I/O and measurement.
- Local `.venv` verification: Phase 7 measurement suite **7 passed**.
- Phase 7 remains 🟡 for full production-scale resource envelopes and broader
  native-authority coverage.

### Phase 8C — Expanded comparative protocol and reference envelopes

- Bound the Phase 8 protocol to the expanded 74-event corpus through
  `evaluation/phase8_corpus_runner.py`; external baselines remain explicitly
  `unavailable` rather than receiving fabricated scores.
- Added reference collection specifications and scorecard scaffolds for ELIZA
  floor, small LLM, modern LLM, base human, and advanced human. Only the ELIZA
  floor has a runnable adapter in this repository; the other four remain
  collection specifications/scaffolds, not measured implementations.
- Corrected the harness to read the authoritative
  `CommunicationInterpretation` node and normalized legacy force aliases for
  measurement only.
- Live report is recorded at
  `evaluation/reports/phase8_corpus_report_20260923.json`; it measures six
  observed dimensions using the declared case denominators across the 74
  events; memory/learning/cost remain unavailable in this corpus.
- Release gate remains **blocked** because external baselines and several
  cognition dimensions are not empirically measured.

### Phase 8D — Deterministic ELIZA-floor adapter

- Added `evaluation/reference_adapters/eliza_floor.py`, a deterministic,
  ordered lexical/reflection adapter that reads only each signal. It does not
  consume corpus labels, create cognitive labels, or claim grounding, action,
  repair, memory, learning, calibration, or cost capability.
- Ran the adapter over all **74** fixed corpus events and recorded one raw
  observation per event, including input tokens, selected rule, captures,
  output, determinism, failure field, and elapsed time. All 74 traces were
  complete and deterministic.
- The fixed protocol permits a measured **provenance = 1.000 (n=74)** result
  for complete adapter traces. All other ELIZA dimensions are explicitly
  `unavailable`; this is not a zero-capability claim.
- Small LLM, modern LLM, base-human, and advanced-human scorecards remain
  `unavailable`. The comparative release gate remains **blocked** because the
  conversational-manifold target and the other baselines are not all
  empirically measured.
- Focused local `.venv` verification: `tests/test_phase8_eliza_floor_adapter.py`
  **5 passed**. JSON validation, Python compilation, and `git diff --check`
  passed for this increment.

### Phase 8E — ELIZA-floor integration in the main corpus report

- Updated `evaluation/phase8_corpus_runner.py` to run the existing deterministic
  ELIZA-floor adapter alongside the SUT and attach its native scorecard plus
  complete case-bound raw adapter provenance under
  `comparison_summary.baselines.eliza_floor`.
- The integrated ELIZA scorecard measures **provenance only**. Interpretation,
  grounding, action, repair, memory, learning, calibration, and cost remain
  explicitly `unavailable`; the small-LLM, modern-LLM, base-human, and
  advanced-human baselines remain unavailable. The comparative release gate
  semantics and blocked status are unchanged.
- Focused local `.venv` verification: **14 passed in 43.28s**, including the
  adapter, comparative-gate, scaffold, and main-report integration contracts.
  No full 74-event replay was run for this increment.

### Phase 8F — Unresolved anaphoric instruction repair — 2026-09-23

- Corrected the live action/repair boundary so an instruction carrying an
  unresolved graph `comp_anaphor` is routed to the existing clarification
  faculty before action enactment. A same-event resolved answer-topic goal
  remains eligible for the specific routed path.
- This consumes neutral parse/discourse evidence and does not add a lexical
  pronoun list or a surface-level action exception.
- Added a regression proving `Move it there.` produces a clarification,
  records `communication_route="ask_back"`, and does not enter the action
  route.
- Local `.venv` verification: focused unresolved-instruction and adjacent
  action/repair tests passed; the new regression passed **1 test**.

### Phases 3–8

- Status: bounded increments through Phase 8C are now implemented; full phase exit gates remain open where marked above.
- Existing foundations must be reused and hardened; duplicate surface-level conversation handlers should not be added.

### Phase 4G — Held-out task-family and asynchronous residual validation

- Added held-out coverage for defer/error, correction, contradiction, topic
  shift, and asynchronous residual evidence. The tests assert native candidate
  provenance, selection/rejection/settlement, counterfactual credit, and
  deep-versus-shallow deliberation rationale from residual/tolerance evidence.
- The held-out cases are event-compatible but not turn-inherent: no message or
  turn identifier is required by the cognitive lifecycle assertions.
- Local `.venv` verification: new suite **9 passed**; combined Phase 4 suites
  **27 passed**. Phase 4 remains yellow pending production-corpus replay and
  broader native workload measurement. The current 74-event report contains
  **0** serialized selected-candidate traces and no deliberation, settlement,
  rejection, or counterfactual fields; generic cognition traces do not satisfy
  this exit criterion.
- Added the graph-resident production trace seam and regression: when a
  `Deliberation` is explicitly linked to an inbound event, the serialized
  cognition trace now carries its candidates, native selections, settlements,
  and counterfactual credit. This is observational only; the live 74-event
  runner still creates no deliberations, so Phase 4 remains open.

### Phase 5G — Heterogeneous recurrence and anti-transfer validation

- Added six opaque task families with competing recurrence priorities from 2
  through 7. The test exercises monotonic priority growth, stable graph
  identities, failed-repair visibility, selected-family route transfer, and
  human-gated promotion.
- A route or promotion from one family is explicitly rejected for every other
  identity; no surface wording is used as the identity or learning decision.
- Local `.venv` verification: Phase 5B–5G focused suite **11 passed**;
  Phase 5G alone **1 passed**. Phase 5 remains yellow pending recurrence over
  the production corpus and broader impact/priority measurement. The latest
  combined Phase 4/5 verification battery passed **42** tests, but no
  production-corpus recurrence trace is yet serialized.

### Phase 6F — Full-corpus production manifest

- Added `evaluation/phase6_production_manifest.py`, a deterministic manifest
  over all 74 communication events. It classifies **65 substantive surfaces**
  and **9 fragment/cognition-only results**.
- Every substantive event must have either a released production receipt or
  the canonical explicit error; arbitrary reply text and `noted` cannot satisfy
  coverage. The manifest never fabricates receipts or releases.
- Local `.venv` verification: manifest suite **10 passed**. Live execution of
  the manifest against production receipts remains the next Phase 6 gate.

- Added strict live-report extraction and `diagnose_live_manifest()`. It
  accepts only serialized released receipts, the canonical explicit error, or
  actual cognitive traces; `trace_coverage` flags and arbitrary reply text do
  not count. Current report diagnostic: **74/74 cognition traces**, **28
  accepted released receipts**, **2 withheld receipts**, **24 explicit errors**,
  and **63/74 accepted events**, leaving **11 substantive events uncovered**.
  Phase 6 remains blocked on receipt/error coverage, not on missing
  observability.

### Phase 6G — Route-specific semantic readback verification — 2026-09-23

- Reconciled the legacy readback assertion with the actual graph-backed route:
  direct legacy readers retain `legacy_structural_readback`, while the live
  `converse` information route records `conversation_information_graph`.
  Both remain behind the same production release gate.
- Local `.venv` verification: production manifest, production gate, legacy
  readback, and output-null battery **32 passed**. This does not close the
  full-corpus semantic recoverability gate.

### Phase 7F — Graph-authored production workload and authority audit

- Added native measurement profiles for Phase 3 asynchronous discourse,
  Phase 4 deliberation, Phase 5 recurrence, and Phase 6 production. Each
  records native steps, replay equality, latency, RSS, graph residence, and
  resource ceilings.
- Local `.venv` verification: native measurement suite **13 passed**. All four
  new profiles satisfy replay/resource assertions. RSS now uses current
-  process-local resident memory rather than contaminated process-wide high
  water. The authority audit scans the current Python cognitive surface and
  now reports **172 unbound Python cycle/task calls** plus **9 explicitly
  native-bound calls**; unbound calls are not counted as native authority.
- Added a focused provenance boundary for the live deliberation bridge:
  Python materializes graph evidence only, while native Phase 4A rules own
  settlement. Focused `.venv` verification: **2 passed**. The broader native
  profile rerun currently has process-local RSS threshold failures; those are
  recorded as resource-envelope debt, not reclassified as authority evidence.
- Phase 7 remains yellow until those decisions are reviewed/migrated or
  explicitly justified and the full production envelope is measured.

### Phase 7G — Live deliberation native-authority boundary — 2026-09-23

- Audited `WorldAdapter._bind_live_goals_and_deliberation` without changing
  the bridge. Its Python work is limited to linking existing discourse/goal
  evidence and materializing complete evidence-bearing graph nodes; valuation,
  collapse, rejection, and `no_candidate` settlement remain native Phase 4A
  rule outcomes.
- Added a narrowly scoped `world_adapter.live_deliberation_bridge` binding to
  `evaluation/native_authority_audit.py`, with explicit provenance,
  `outcome_source=native_rule_readback`, and
  `python_outcome_selection=false` metadata. The audit now includes the exact
  adapter file while preserving all other migration findings.
- Local `.venv` verification: focused authority/provenance tests **2 passed**;
  compile and diff checks passed. A broader selected native measurement run
  had two unrelated process-local RSS threshold failures in existing
  ambiguity/extended-envelope tests; no authority assertion failed.
- Phase 7 remains yellow: this is a bounded authority justification, not a
  claim that the remaining Python cognitive-cycle calls are native-bound.

### Phase 7I — Communication comprehension native execution boundary — 2026-09-23

- Audited `WorldAdapter.comprehend()`: its only cognitive operation is
  execution of the graph-authored communication rules, optionally bounded by
  the graph's `AsyncDaemonCycleBudget`. It does not select a route, surface, or
  cognitive outcome in Python.
- Added an exact native-authority binding with provenance
  `native_rule_readback:communication_comprehension`, boundary
  `graph_rule_execution_only`, and `python_outcome_selection=false`.
- This binds one demonstrated execution boundary only; the remaining audit
  findings remain unbound pending separate evidence and are not silently
  reclassified. The audit now reports **7 bound** and **174 unbound findings**.
- Local `.venv` verification: focused Phase 7 authority/audit battery **4
  passed**; `git diff --check` passed.

### Phase 7J — Native schedule entrypoint authority — 2026-09-23

- Bound `WorldAdapter.tick()` and `dual_process_tick()` as native schedule
  execution only. They invoke the substrate's `default` and `dual_process`
  cycle plans and return native cycle readback; Python does not select a
  cognitive outcome.
- The audit remains conservative: `cognitive_tick()` and `master_tick()` also
  perform Python-side reflex/thread orchestration and remain unbound pending
  separate authority evidence.
- Current native-authority audit: **9 bound**, **172 unbound findings** out of
  181 calls.
- Local `.venv` verification: focused Phase 7 authority/audit battery **5
  passed**; `git diff --check` passed.

### Phase 7H — Native-cycle RSS growth assertion basis — 2026-09-23

- Corrected only the evaluation harness resource assertion: absolute
  `rss_before_bytes`, `rss_after_bytes`, and `peak_rss_bytes` remain recorded
  for observability, while `bounded_rss` now evaluates workload growth via
  `rss_delta_bytes <= resource_limits.rss_growth_bytes`.
- Declared the 100 MiB growth limit, matching the execution plan, and emitted explicit `rss_assertion`
  metadata naming `workload_rss_growth` as the assertion basis; the 1 GiB
  absolute field remains observability-only. Graph, step, replay, and native
  authority limits were unchanged.
- Local `.venv` verification: focused RSS regression **2 passed**; complete
  native measurement module **14 passed in 71.03s**. The focused regression
  includes a synthetic >1 GiB absolute process RSS with 1 MiB workload growth
  and confirms the bounded assertion passes on growth.

### Phase 5H — Production-corpus recurrence measurement — 2026-09-23

- Added `evaluation/phase5_corpus_runner.py`, an evaluation-only adapter over
  the existing graph-native `SelfConcern`, `GapRecurrence`, and
  `GapLearningAssessment` nodes. It preserves graph identity and records
  native node provenance without deriving identities from surface text.
- A single event can cause multiple native settling firings. The evaluator
  deduplicates observations by `(event_id, gap_identity)` while retaining all
  `SelfConcern` node IDs, so internal settling cannot manufacture recurrence.
- Full 74-event replay: runtime measured; **5** graph identities observed,
  each on one event; **0** identities qualified as recurrence. Explicit Phase
  5 learning metadata was absent, so production recurrence is correctly
  reported as `unavailable` with `claim_permitted=false`.
- Local `.venv` verification: Phase 5 corpus runner **3 passed**; full replay
  completed; `py_compile` and `git diff --check` passed. This is measurement
  coverage, not Phase 5 exit acceptance: a learning corpus with explicit
  repeated identity, repair, verification, and review evidence remains needed.

### Phase 2I — Authority/grounding separation rerun — 2026-09-23

- Corrected `_refresh_communication_grounding`: missing permission authority no
  longer prevents independent referent evidence from being read back. A
  supported referent may now be `candidate_grounded` while the separate
  authority gate still withholds production; unsupported permission targets
  retain `authority_missing`.
- Full 74-event SUT replay:
  [`phase8_corpus_report_20260923_phase2i.json`](../../../evaluation/reports/phase8_corpus_report_20260923_phase2i.json)
  records precision **1.00**, recall **0.46**, F1 **0.630**, true positives
  **23**, false positives **0**, and false negatives **27**. The prior replay
  was recall **0.44**, F1 **0.611**, so the change improved recall without
  relaxing the false-positive boundary.
- Local `.venv` verification: permission fail-closed and held-answer grounding
  regressions **2 passed**; the full Phase 2 reference/evidence battery passed
  **40 tests in 623.24s**; full 74-event replay completed successfully.

### Phase 6H — Causal anaphora and explicit-error release boundary — 2026-09-23

- Audited the remaining fixed-string release path. The graph question-response
  route could surface `I don't hold that.` even when no grounded response
  commitment existed; it now remains a canonical explicit error and does not
  mint a released question-response receipt.
- Added a cognition-level relation check for anaphoric reason questions: a
  resolved referent is insufficient to answer why an event occurred. The live
  path now requires an existing substrate `causal_influence` relation before a
  held lexical answer can be released; otherwise the production gate withholds
  it and the caller exposes the explicit error.
- This uses neutral parser relation evidence (`comp_relation_focus="reason"`)
  and existing causal graph structure; it adds no English reply heuristic or
  conversation-only causal store.
- Local `.venv` verification: focused Phase 6 question/information bridge
  battery **13 passed**. The broader Phase 6 gate remains yellow because the
  full 74-event semantic recoverability criterion is still incomplete.

### Phase 2J / Phase 4M — Current full-corpus replay and deliberation readback — 2026-09-23

- Replayed the current implementation over all 74 communication events after
  the authority, causal-anaphora, unresolved-instruction, and explicit-error
  increments:
  [`phase8_corpus_report_20260923_phase2j.json`](../../../evaluation/reports/phase8_corpus_report_20260923_phase2j.json).
- Grounding remains precision **1.00**, recall **0.46**, F1 **0.630**
  (TP **23**, FP **0**, FN **27**). The zero-false-positive boundary is
  preserved; recall remains below the Phase 2 exit criterion.
- Repair state agreement improved from **0.267** to **0.333** and calibration
  agreement from **0.146** to **0.167**. Provenance remains **74/74**.
- Native deliberation readback is now measured for **74/74** events, but every
  event has zero candidates/zero selections. This confirms the observability
  path and the absence of a complete live upstream Phase 4 evidence source;
  it does not count as candidate-generation completion.
- The release gate remains blocked because semantic recoverability and the
  external baseline collection requirements are still unmet.
- Local `.venv` replay completed successfully; no synthetic candidate or
  surface fallback was introduced.

### Phase 8G — Local LLM raw-reference collection — 2026-09-23

- Added `evaluation/reference_adapters/ollama_local.py`, a local-only raw
  collection adapter for the existing `small_llm` and `modern_llm` reference
  classes. It binds every request to a fixed corpus case ID and records the
  model tag, fixed prompt, stdout, stderr, return code, and annotation status.
- Collected a complete small-LLM raw run with installed `gemma3:4b`:
  [`phase8_small_llm_raw_20260923.json`](../../../evaluation/reports/phase8_small_llm_raw_20260923.json),
  **74/74 cases**, zero collection failures. All capability annotations and
  scorecard dimensions remain explicitly unavailable pending blinded review;
  raw text is not cognition evidence.
- A complete modern-LLM raw run was then collected through the local Ollama
  HTTP API with `qwen3.5:9b`, `think=false`, and `num_predict=96`:
  [`phase8_modern_llm_raw_20260923.json`](../../../evaluation/reports/phase8_modern_llm_raw_20260923.json),
  **74/74 cases**, zero collection failures. The HTTP request and response
  JSON are retained as raw provenance; no capability score is inferred.
- Local `.venv` adapter tests: **4 passed**. The comparative release gate
  remains blocked until raw outputs receive independent adjudication and the
  human reference classes are collected.

### Phase 6I — Semantic recoverability mismatch audit — 2026-09-23

- Added `evaluation/phase6_semantic_recoverability_audit.py`, an evaluation-only
  classifier over independent runtime fields. It excludes reply text from
  evidence and separates state, force, and grounding-recall mismatches.
- The current Phase 2J replay is complete at **74/74** observations with **64**
  mismatch cases: state **57**, force **42**, and grounding-recall **27**
  (dimensions overlap). This identifies the next work as cognition/annotation
  adjudication and route reasoning, not surface-string repair.
- Local `.venv` audit tests: **2 passed**. No fallback surface or semantic
  label was changed by this increment.

### Phase 6J — Deferred-goal lifecycle readback correction — 2026-09-23

- Corrected `evaluation/phase8_corpus_runner.py` to read graph-resident Goal
  lifecycle status before mapping an instruction route to `act`. A Goal with
  `status="deferred"` is now measured as `defer`; active goals remain `act`.
  This fixes an evaluation boundary error, not the cognition or its surface.
- The updated replay is recorded at
  [`phase8_corpus_report_20260923_phase2k.json`](../../../evaluation/reports/phase8_corpus_report_20260923_phase2k.json).
  Calibration agreement improved **0.167 → 0.188** and the state mismatch
  count fell **57 → 56**; grounding remains precision **1.00**, recall **0.46**.
- Local `.venv` verification: deferred-goal readback plus existing temporal
  defer regression **2 passed**; full replay completed successfully.

### Phase 4N — Substrate reinvention audit verification — 2026-09-24

- Re-ran the substrate integration audit before selecting the next
  implementation increment. The audit confirms that referent identity, goal
  lifecycle, gap recurrence/learning, thought competition, production gates,
  and native collapse already have substrate authorities available for reuse.
- The executable Phase 4 tuple audit found **0** complete seed-record tuples
  and **0** qualifying near matches. No `DecisionOption`, salience,
  information-commitment, or adaptive-control record is promoted by inferred
  evidence.
- The native-authority audit reports **9** explicitly bound calls and **172**
  unbound Python cognitive cycle/task calls out of **181**. Unbound calls
  remain migration-review debt; they are not silently counted as native.
- Local `.venv` verification of tuple availability, live deliberation
  provenance, native-authority boundaries, and semantic mismatch auditing:
  **12 passed**.
- Audit consequence: the next Phase 4 increment must expose a complete tuple
  from an existing cognitive faculty or preserve explicit `no_candidate`/error
  readback. Defaults, surface-language force heuristics, and parallel
  conversation stores remain prohibited.

### Phase 6K — Neutral-force semantic audit correction — 2026-09-24

- Corrected the evaluation-only semantic recoverability audit to compare the
  corpus's fine-grained labels (`offer`, `refusal`, `correction`) against the
  runtime's declared neutral force ontology using the existing `FORCE_ALIASES`
  boundary. No runtime classifier, language rule, or reply surface changed.
- Added a regression proving that neutral runtime observations for all three
  fine-grained labels produce no false force mismatch. Local `.venv` result:
  **3 passed**.
- Re-reading the current Phase 2K report changes force mismatches from **42**
  to **27**. State mismatches remain **56** and grounding-recall mismatches
  remain **27**; these are still cognition/evidence work, not surface wording.

### Phase 6L — Cognitive-state/release-state separation — 2026-09-24

- Corrected the evaluation boundary so an explicit fail-closed release error
  does not overwrite a graph-resident cognitive state. Runtime route, intent,
  grounding, and goal lifecycle are read first; `release_status` separately
  records `released`, `error`, or `unavailable`.
- Added regressions for repair-under-error and error with no cognitive state.
  Local `.venv` focused verification: **6 passed**.
- Full 74-event replay:
  [`phase8_corpus_report_20260924_phase6k.json`](../../../evaluation/reports/phase8_corpus_report_20260924_phase6k.json)
  remains correctly blocked, with grounding precision **1.00**, recall **0.46**,
  F1 **0.630**, and **38** explicit errors / **36** released outputs.
- Semantic audit now reports **50** state mismatches (down from 56), **27**
  force mismatches, and **27** grounding-recall mismatches. The remaining
  state errors are not treated as wording debt; they require graph-level route,
  repair, learning, and blocked-goal evidence.

### Phase 2K / Phase 6M — World-support repair integration — 2026-09-24

- Integrated the existing neutral `world_support=missing` comprehension
  evidence into `conversation_action.is_ask_back()`. A well-formed question
  can now enter the existing repair faculty when the substrate lacks an
  attached world; no English cue list, answer fabrication, or new repair
  store was added.
- The existing `repair_evidence=knowledge_deficit` path is also accepted by
  the same faculty. The explicit error surface remains unchanged when repair
  itself cannot produce a response.
- Local `.venv` verification: action/repair, unresolved-instruction, and
  ask-back regressions **4 passed**.
- Full 74-event replay:
  [`phase8_corpus_report_20260924_phase6m.json`](../../../evaluation/reports/phase8_corpus_report_20260924_phase6m.json)
  remains blocked but explicit errors fell **38 → 34** and released outputs
  rose **36 → 40**. Grounding remains precision **1.00**, recall **0.46**,
  F1 **0.630**; semantic mismatch counts remain state **50**, force **27**,
  grounding recall **27**. The change improves repair release coverage without
  claiming completion of the broader state/grounding gates.

### Phase 2M — Permission-authority scope correction — 2026-09-24

- Corrected the existing permission faculty boundary so authority evidence is
  applied only to interrogative modal-action requests. Declarative
  ability/offer/refusal statements are no longer reclassified as
  `authority_missing` merely because their semantic frame contains a modal and
  an action predicate.
- Missing-world evidence remains a blocked cognition/error boundary, not an
  automatic ask-back or wording fallback. This preserves the explicit error
  invariant and the existing production-withheld contract.
- Local `.venv` permission, production, repair, and unresolved-instruction
  battery: **14 passed**. Full replay:
  [`phase8_corpus_report_20260924_phase2m.json`](../../../evaluation/reports/phase8_corpus_report_20260924_phase2m.json)
  remains blocked; grounding precision **1.00**, recall **0.46**, F1 **0.630**.
  The change removes an authority false interpretation but does not claim
  grounding for declarative statements whose graph lacks referent evidence.

### Phase 2N — Grounding-recall false-positive audit — 2026-09-24

- Audited the remaining grounded/partially-grounded false negatives against
  existing Concept definitions and mention bindings.
- Tested a candidate extension that would promote declarative content when a
  mentioned Concept had substantive descriptive attributes. The existing
  false-positive regression correctly rejected this: a lexical Concept is not
  sufficient event-grounding evidence for an arbitrary assertion.
- Reverted the extension and retained the zero-false-positive boundary. The
  audit establishes that the next recall increment must use an event- or
  relation-specific graph path, not lexical Concept presence.
- Verification after reversion: **9 focused tests passed**; `git diff --check`
  passed. No grounding score was inflated by this experiment.

### Phase 2O — Event-predication grounding-source audit — 2026-09-24

- Probed the existing graph-native `reading_collapse._event_predication_graph`
  as a possible source for the remaining grounding false negatives.
- The faculty supplies syntactic event/role predications, but not by itself a
  held fact, common-ground commitment, or grounded world relation. Several
  copular, fragment, and interrogative corpus forms are also parsed
  conservatively or incorrectly for this purpose.
- No integration was made: promoting parse structure to epistemic grounding
  would violate the established zero-false-positive boundary. The next valid
  path must link event predication to an existing commitment/relation node.
- Probe was read-only; existing grounding regressions remain green and no
  score was changed.

### Phase 2P — Event-to-commitment integration search — 2026-09-24

- Searched the existing substrate for event-level grounding authorities. The
  available `reading_collapse` and `situation_model_reader` faculties can
  produce event/role and situation-model structures, but their outputs are not
  automatically linked to a communication event's held fact or common-ground
  commitment.
- The probe therefore does not promote those structures into communication
  grounding or Phase 4 evidence. This preserves the distinction between
  parsed event structure and epistemic support.
- The remaining recall increment is narrowed to a missing event-to-commitment
  integration seam; no safe score-changing patch was justified in this slice.

### Phase 2L / Phase 6N — World-support and anaphora evidence preservation — 2026-09-24

- Preserved existing neutral `language_evidence` fields on the selected
  `CommunicationInterpretation`, including world dependency/support,
  repair evidence, referent status, and authority evidence. This makes the
  evidence available to downstream cognition and evaluation without copying
  surface language.
- Preserved the graph's existing `comp_anaphor` datum on the interpretation so
  a missing world and an unresolved deictic reference are not conflated.
- Blocked/repair readback now uses those evidence fields: missing world support
  is `blocked`; unresolved anaphora remains `repair`.
- Local `.venv` focused verification: **4 passed**. Full replay:
  [`phase8_corpus_report_20260924_phase6o.json`](../../../evaluation/reports/phase8_corpus_report_20260924_phase6o.json)
  remains blocked, with grounding precision **1.00**, recall **0.46**, F1
  **0.630**, release counts **40 released / 34 explicit errors**, and semantic
  mismatch counts state **47**, force **27**, grounding recall **27**.

### Pre-continuation substrate audit — 2026-09-24

- Re-audited the current source tree, tests, reports, and plan/tracker before
  beginning another implementation increment.
- Confirmed that the repository already owns the relevant mechanisms:
  `DiscourseStore` for referents, `DiscourseState`/`CommonGround` for event
  lifecycle, `conversation_action._bind_goal_to_inbound()` for idempotent goal
  binding, `ThoughtManifold`/Phase 4A for candidate cognition, existing gap
  learning/prioritization, production/readback gates, and native cycle
  scheduling.
- Corrected the earlier audit recommendation: a new goal-binding helper is
  not required and must not be recreated in `discourse_state`; the existing
  helper and tests are the authority.
- Confirmed that `DecisionOption` lacks the complete Phase 4A evidence tuple,
  and that `reading_collapse`/`situation_model_reader` structures do not by
  themselves establish epistemic commitment. Neither is promoted by inference.
- **Plan adjustment:** the next valid implementation target is only a
  mechanical event-to-existing-commitment projection. In the absence of an
  existing held/common-ground/verified relation commitment, the system must
  remain `no_candidate`, repair, or explicit diagnostic error. No new store,
  default evidence, lexical grounding, parse-only grounding, or fixed
  acknowledgment is authorized.
- Documentation updated in
  `CONVERSATIONAL_MANIFOLD_SUBSTRATE_INTEGRATION_AUDIT_20260923.md`.

### Audit consolidation: proposition bridge and event ingress — 2026-09-24

- Independent read-only audits found no justification for another referent
  store, deliberation scorer, gap scheduler, or production gate. Existing
  ownership is now recorded explicitly: `DiscourseStore` owns referent
  identity; `DiscourseState` owns event lifecycle; native Phase 4A owns
  candidate valuation/settlement; production gates own release.
- The genuine missing cognition capability is a structured proposition
  lifecycle connecting neutral semantic evidence to grounded proposition,
  speaker/addressee attribution, epistemic evidence, common-ground
  uptake/challenge/suspension/retraction, and situation-model consequence.
  Action commitment and reply wording are not substitutes.
- The live path remains English-shaped and reply/turn-oriented despite neutral
  substrate components. The plan now requires neutral semantic/semiotic event
  ingress and permits non-turn cognition without forced reply production.
- Existing question-driver, legacy conversation, current-topic, and gap
  prioritization stacks are classified as adapters/parallel scopes requiring
  explicit ownership boundaries, not new implementation targets.
- `.venv` verification of existing reuse seams: **39 passed in 12:31**.
  This is a boundary regression result, not a full-corpus completion claim.
- **Next phase gate:** design and implement the smallest graph-native
  proposition/commitment bridge by reusing existing nodes and native rules;
  preserve `no_candidate`/repair/error when no supported commitment exists.

### Phase 2Q.1 — Neutral semantic-event ingress — 2026-09-24

- Added `WorldAdapter.ingest_semantic_event(...)` as a separate event-only
  ingress. It accepts adapter-produced neutral evidence, creates a
  `SemanticEventFrame`, `CommunicationInterpretation`, and canonical
  `DiscourseEvent`, then lets native arbitration read the evidence.
- The ingress does not call `converse()`, `comprehend_text()`, mint a
  `Message`, infer force from surface language, select a reply, or require a
  turn. `interaction_mode` remains explicit and non-turn events return
  `reply=None`.
- Extended `communication_evidence.from_semantic_frame()` to preserve an
  explicitly supplied neutral proposition payload and to reject unknown
  communicative force instead of silently collapsing it to assertion.
- Local `.venv` verification: semantic ingress plus multilingual neutral
  arbitration **4 passed in 48.33s**; prior reuse-boundary battery remains
  **39 passed in 12:31**.

### Phase 2Q.2 — Explicit proposition evidence bridge — 2026-09-24

- Integrated the delegated `domains.proposition_commitment` bridge. It accepts
  only `neutral_proposition_evidence.v1` with explicit predicate, role-labelled
  arguments, polarity, provider, and evidence id; it records graph-native
  `Proposition`, `PropositionEvidence`, and `PropositionArgument` nodes with
  source-event and attribution edges.
- Surface text, lexical concepts, parse-only predications, unsupported schemas,
  and invalid graph handles are rejected without graph mutation. A proposed
  proposition is not treated as accepted common ground; uptake remains a
  distinct future native lifecycle step.
- Delegated focused verification: proposition bridge **3 passed in 0.20s**.
  Integrated ingress/proposition verification: **11 passed in 109.62s**.
- This phase establishes transport and provenance only. It does not claim
  improved corpus grounding recall until a supported event-to-commitment corpus
  fixture and native uptake/challenge lifecycle are available.

### Phase 2Q.3 — Native proposition uptake lifecycle — 2026-09-24

- Added the self-load-only native seed
  `seeds/proposition_commitment_lifecycle.json`.
- Explicit graph signals now drive native readback transitions:
  `proposed -> accepted`, `proposed -> challenged`, `proposed -> suspended`,
  and `accepted/challenged/suspended -> retracted`. Retraction of a merely
  proposed proposition is rejected by the native guards.
- The seed records `uptake_applied` and uses status guards so repeated rule
  passes are idempotent. Missing or unsupported signals do not transition.
- Corrected the delegated first draft during verification: generic
  `uncertain/rejected` states were not accepted as substitutes for the
  proposition lifecycle, and proposed retraction was removed.
- Local `.venv` native lifecycle verification: **4 passed in 62.96s**.
- This phase still does not claim automatic truth or situation-model change;
  those require a separately evidenced consequence path.

### Phase 2R — Accepted-proposition situation-model projection — 2026-09-24

- Added `apply_situation_consequence()` to the existing proposition bridge as
  a mechanical adapter seam into `domains.situation_model_reader`.
- Eligibility is fail-closed: the proposition must be graph-resident,
  explicitly evidenced, `commitment_status=accepted`,
  `uptake_applied=accept`, `polarity=affirmed`, and carry canonical neutral
  agent/object role arguments. Status alone, missing provenance, negation,
  underspecified roles, and challenged/suspended/retracted propositions do not
  reach the situation model.
- The existing situation-model reader and native event/inference rules own the
  actual world-state transition. The new adapter records a
  `SituationModelConsequence` provenance node and is idempotent on replay.
- This is explicitly an accepted-common-ground projection, not an external
  truth claim. No lexical or surface parser path is used.
- Local `.venv` proposition/lifecycle/consequence battery: **12 passed in
  111.11s**; the complete non-turn ingress → proposition → native uptake →
  situation-model chain adds **5 passed in 81.02s**. The existing situation
model wire suite remains green at **9 passed in 2.50s**. `git diff --check`
and Python compilation pass.

### Phase 2S — Isolated proposition/commitment measurement — 2026-09-24

- Added the separate overlay fixture
  `tests/fixtures/conversational_manifold/proposition_commitment_cases.json`.
  It references no new Phase 0 events and therefore does not inflate the
  74-event grounding corpus or its precision/recall denominator.
- Added `evaluation/proposition_commitment_measurement.py`, which boots a
  fresh graph per case, loads the self-load-only native lifecycle explicitly,
  uses neutral asynchronous ingress, and measures proposition provenance,
  native uptake status, and situation-model consequence projection.
- Four cases cover accepted, challenged, suspended, and negated propositions.
  Accepted uptake yields one supported consequence; challenged, suspended, and
  negated cases fail closed. No reply or surface text participates in scoring.
- Local `.venv` verification: **1 measurement test passed in 66.56s**; the
  combined grounding/bridge/lifecycle/ingress/overlay battery is **24 passed
  in 252.68s**. Overlay report: commitment status accuracy **1.0**,
  consequence projection accuracy **1.0**, provenance complete **4/4**,
  supported consequences **1/4**.
- This is a measurement gate, not corpus grounding improvement. The next
  extension is retraction plus contradiction, multi-referent, ambiguous, and
  no-world cases; Phase 4 still requires a complete native evidence tuple
  before any proposition is promoted to a live thought candidate.

### Phase 2S extension — Lifecycle and boundary coverage — 2026-09-24

- Added `tests/test_proposition_commitment_extended.py` with explicit
  accepted-to-retracted history, retraction without prior acceptance,
  evidence-id conflict replay, malformed multi-referent/duplicate-role
  rejection, ambiguous/no-world/contradicted event boundaries, and equivalent
  cognitive metadata for non-turn and turn-compatible ingress.
- The situation-model adapter now checks the existing reader's typed
  `change_of_state` result before minting `SituationModelConsequence`; an
  accepted proposition for a property, stative, or generic event fails closed
  instead of being relabeled as a state transition.
- Focused local `.venv` verification: **11 passed in 190.47s**. The complete
  dependent Phase 2/3 proposition battery is now **35 passed in 462.52s**.
- This closes the bounded 2S coverage increment. The fixed 74-event grounding
  recall remains unchanged by design; accepted uptake is still not external
  truth and no Phase 4 candidate promotion occurs.

### Phase 3B — Addressee-scoped CommonGround correction — 2026-09-24

- Audit found that `ensure_common_ground()` always selected the first ledger
  attached to a `DiscourseState`; claims addressed to different participants
  therefore leaked into one aggregate ledger.
- Corrected the existing discourse-state authority to reuse/create ledgers by
  explicit addressee scope. Event claim deltas now attach to the addressed
  ledger; unaddressed events use the shared ledger. No second common-ground
  subsystem or proposition lifecycle was introduced.
- Updated the Phase 3 stress assertions to verify separated claims while event
  provenance and goal lifecycle remain unchanged.
- Local `.venv` verification: discourse-state exit suite **5 passed in 0.22s**;
  the dependent Phase 2/3 proposition battery is **35 passed in 462.52s**.
- Compatibility audit: **38 targeted tests passed in 132.61s**. Existing
  unaddressed shared-ledger behavior, explicit proposition common-ground
  handles, idempotence, and legacy callers remain intact. The implemented
  scope is recipient-relative, not full `(speaker, addressee)` pair-relative;
  speakers addressing the same recipient intentionally share that recipient's
  ledger.

### Phase 4P — Proposition-consequence deliberation boundary — 2026-09-24

- Added `tests/test_phase4_proposition_boundary.py` to verify that an accepted
  `SituationModelConsequence` remains situation-model cognition and does not
  itself mint a `ThoughtCandidate` or `DeliberativeCandidate`.
- An incomplete Phase 4 tuple is rejected. An explicitly authored complete
  wrapper is transported once with proposition → consequence → evidence
  provenance intact; native Phase 4 rules still own selection and outcome.
- Local `.venv` verification: **4 passed in 67.74s**. This is a boundary gate,
  not evidence that production events now generate deliberations; the live
  production corpus still lacks complete upstream Phase 4 tuples.

### Phase 6P — Receipt-backed semantic recoverability measurement — 2026-09-24

- Added evaluation-only `evaluation/phase6_receipt_recoverability.py` and
  deterministic tests. It reuses the existing production manifest and
  serialized `ProductionGateReceipt` objects; it does not add parsing,
  routing, or conversation state.
- Events are classified as receipt-backed and semantically recoverable,
  explicit error/withheld, released semantic mismatch, or missing
  authoritative evidence. Semantic decisions use only receipt fields;
  reply text and trace-coverage flags cannot supply meaning.
- Focused local `.venv` verification: **4 passed in 0.14s**. Existing
  `phase6o` 74-event report readback is **74/74 measured**: 31 receipt-semantic
  recoverable, 34 explicit-error/withheld, 9 released receipt-semantic
  mismatches, 0 missing; mismatch dimensions are force 4 and receipt
  multiplicity 5. Runtime state is reported separately: 47 diagnostic
  mismatches in the adapter's heuristic state observation, not receipt
  semantic evidence.
- This strengthens measurement but does not close semantic exit. The remaining
  Phase 6 work is review/correction of the released mismatches and the
  production-scale evidence decision; reply wording is not a repair.

### Phase 2T — Supported event-to-commitment overlay measurement — 2026-09-24

- Added the independent overlay fixture
  `tests/fixtures/conversational_manifold/proposition_event_commitment_cases.json`.
  It is keyed only to existing Phase 0 event IDs; the 74-event corpus remains
  byte-for-byte unchanged and its grounding denominator is untouched.
- Added `evaluation/proposition_event_commitment_measurement.py`, which uses
  the existing neutral ingress, native proposition lifecycle, and typed
  situation-model consequence bridge. It records event identity, proposition
  materialization, explicit uptake/status, provenance, consequence, and
  fail-closed negative stages without using replies or claiming external truth.
- Seven cases / nine event steps cover accepted, challenged,
  accepted-to-retracted, unsupported surface evidence, ambiguous, no-world,
  and conflicting evidence-id paths.
- Local `.venv` verification: **3 passed in 121.50s**; measured results are
  9/9 event identities, proposition materialization **1.0**, commitment status
  **1.0**, consequence projection **1.0**, proposition provenance **5** cases,
  consequence provenance **1** case, fail-closed negatives **4**, reply
  evidence used **false**, external truth claimed **false**.

### Phase 7K — Neutral semantic-event envelope measurement — 2026-09-24

- Added evaluation-only `evaluation/phase7_semantic_event_envelope.py` and
  focused tests. The profile replays challenged, accepted typed-consequence,
  and malformed neutral events through existing semantic ingress.
- It records graph growth, latency, RSS delta, proposition/common-ground/
  consequence readback, no-Message/no-turn/no-reply invariants, malformed
  evidence failure, and fresh-graph replay equality. Python materialization
  and the post-ingress native drain are reported separately; the ingress is
  not falsely labeled wholly native.
- Local `.venv` verification: **4 passed in 45.41s**. Replay is deterministic,
  resource assertions are bounded, accepted `drop(john, glass)` produces one
  typed consequence, challenged state remains challenged, and malformed
  surface evidence creates no proposition or evidence node.
- Direct profile observation: 148 graph nodes / 253 edges added, RSS growth
  62,377,984 bytes (<100 MiB), latency 1,673.11 ms for the three-event
  sequence, and post-ingress drain readback `[0, 0, 0]`. The latency is an
  envelope observation, not a claim that the full path meets the conversational
  soft-real-time target.
- The public ingress does not expose the internal arbitration call's native
  step trace; the profile records a clearly labeled post-ingress drain rather
  than claiming it is the original arbitration trace.

### Phase 5H/5I — Production recurrence evidence audit — 2026-09-24

- Replayed the existing Phase 5 corpus adapter and recurrence authorities
  against the fixed communication fixture. The adapter preserves native
  `SelfConcern.attrs.gap_identity`, `GapRecurrence`, and
  `GapLearningAssessment` ownership; it does not derive identity from surface
  repetition.
- Repeated the `question_unknown` event with both the same and a distinct
  event identifier. Neither produced two graph-native observations for a
  stable gap identity, so recurrence remains unavailable rather than inferred.
- The fixed 74-event communication corpus has no explicit
  `gap_identity`/`learning_stage`/`verification_status` contract. Production
  learning claims therefore remain withheld.
- Local `.venv` verification of the recurrence adapter and Phase 5A–5G
  authorities: **17 passed in 141.70s**. This is a negative evidence gate and
  integration audit; the next valid increment is a separately authored,
  provenance-bearing production-learning fixture, not corpus duplication.

### Phase 4Q — Auditable live deliberation integration failures — 2026-09-24

- Replaced the live Phase 4 bridge's silent exception return with a graph
  resident `CognitiveIntegrationDiagnostic` linked to the inbound message and
  discourse event. It records stage, exception type/message, native-only
  selection ownership, and `surface_fallback=false`.
- The diagnostic is idempotent for the same message/event and does not create a
  candidate or alter native selection. Ordinary unsupported events still
  produce the native `no_candidate` trace.
- Local `.venv` verification of the live bridge, native-authority boundary,
  tuple audit, and forced-failure regression: **11 passed in 188.53s**.

### Phase 6Q — Runtime cognitive-state evidence separation — 2026-09-24

- Extended the Phase 8 observation contract with explicit cognitive-state,
  evidence-source, authority, evidence-availability, and release-state fields.
  Receipt `semantic_intent` remains communicative/action content and is never
  compared directly with `defer`, `repair`, or `blocked` disposition labels.
- The fresh artifact
  [`phase8_corpus_report_20260924_phase6q.json`](../../../evaluation/reports/phase8_corpus_report_20260924_phase6q.json)
  covers all **74/74** events. State evidence is split into **20** graph
  goal-lifecycle readbacks and **54** interpretation readbacks explicitly
  marked `interpretation_readback_not_disposition`; all 74 have an evidence
  source, but only the goal-lifecycle subset is disposition-grade.
- The pre-fix receipt classification was **29** receipt-semantic recoverable,
  **38** explicit/withheld, **7** released semantic mismatches, and **0**
  missing; runtime-state mismatch count was **47**.
- After the cognition-owned pronoun-target correction and typed authority
  readback correction, the final fresh artifact is **30** receipt-semantic
  recoverable, **38** explicit/withheld, **6** released semantic mismatches,
  **0** missing, and **45** runtime-state mismatches.
- The final runtime-state adjudication splits those 45 diagnostics into
  **38** `disposition_authority_missing` cases, **7** genuine
  `graph_cognitive_state_mismatch` cases, and **29** state matches. The
  `action_pronoun` case now reaches the existing repair faculty instead of
  creating an action goal.
- Local `.venv` verification: **23 passed in 377.24s** for the full Phase 8
  corpus/receipt test battery; focused Phase 6Q contract tests passed **8**.

### Phase 6Q cognition-owned correction — unresolved action pronoun — 2026-09-24

- Corrected the language-adapter evidence boundary so a typed object pronoun is
  retained as the action target instead of being skipped in favor of a later
  adverb (`Move it now` no longer becomes `Move(now)`).
- Unresolved reference evidence now enters the existing clarification/repair
  faculty before an action goal is minted. No referent is guessed and no
  wording-only action repair was added.
- Focused `.venv` verification: **6 passed in 161.09s**. The post-fix fresh
  74-event artifact shows `action_pronoun` routed to repair and improves the
  receipt/runtime metrics recorded above.

### Phase 6R — Typed overlap and partial-event metadata — 2026-09-24

- The live discourse-event bridge now preserves adapter-supplied
  `interaction_relation` and `literal_form` in the event payload. This gives
  native cognition the event relation directly; it does not infer overlap or
  select a disposition from surface text.
- The Phase 8 runner supplies these fields from the versioned corpus metadata,
  and a live bridge regression confirms graph readback for a fragment/overlap
  event.
- Local `.venv` verification: **3 passed in 52.95s**. The remaining seven
  state mismatches are not silently reclassified; the next gate is native
  consumption of this evidence or an explicit adjudication that the corpus
  label is not supported.

### Phase 7L — Production-shaped communication envelope — 2026-09-24

- Added `evaluation/phase7_production_envelope.py`, reusing eight existing
  fixed-corpus events across information, action, reference, overlap,
  correction, social, unavailable-world, and malformed-input strata. No new
  parser, reply policy, or cognitive classifier was introduced.
- The profile records structural graph residence, typed event/interpretation
  readback, explicit error presence, replay stability, and resource evidence;
  reply text is excluded from replay semantics and turn-taking is not required.
- Measured profile: **8/8** observations, **377 nodes / 11,697 edges** added,
  **30,740.9 ms** elapsed, **132,919,296 bytes** total RSS growth, with
  **123,744,256 bytes** attributable to cold start and **9,175,040 bytes** to
  the remaining events; replay is deterministic. Steady-state growth is under
  the 100 MiB bound, but cold start and latency remain open Phase 7 conditions.
- Local `.venv` verification: **3 passed in 92.95s**.

### Phase 5J — Explicit production-shaped learning observations — 2026-09-24

- Added `evaluation/phase5_production_learning_fixture.py` with four typed
  observations over two opaque identities. The fixture supplies explicit
  `gap_identity`, `learning_stage`, and `verification_status`; it never derives
  identity from signal text or repetition.
- Existing native authorities produced two local `GapRecurrence` nodes, each
  with recurrence count **2**, and two `GapLearningAssessment` nodes at
  `human_review` with `auto_promoted=0.0`. No new learning ledger or promotion
  policy was introduced.

### Phase 5K — Verified repair and supervised promotion closure — 2026-09-24

- Extended the fixture with native failed-repair records and one explicit
  human-approved verified retry. The selected opaque identity is promoted with
  `promotion_authority=human_review`; the other remains `human_review`.
- Failed repair is visible for both identities, recurrence/promotion remain
  identity-local, and `auto_promoted=0.0` for every identity.
- Local `.venv` verification: **14 Phase 5 tests passed in 46.04s**, including
  the fixture and Phase 5B–5G recurrence suite.

### Phase 5L — Communication-event learning observation ingress — 2026-09-24

- `WorldAdapter.converse()` now transports validated typed learning
  observations from event context to the inbound message and discourse-event
  payload. The adapter does not derive identity from signal text and does not
  create a learning ledger.
- Added the native `gap_awareness` rule
  `note_explicit_learning_observation`, which creates the existing
  `SelfConcern` with `gap_identity.v1`, learning-stage/verification fields,
  event provenance, and the normal `has_self_concern` ownership edge.
- Live communication regression confirms one stable concern with the supplied
  identity and event provenance. Full Phase 5 fixture/recurrence battery:
  **15 passed in 69.59s**.
- This closes ingress/provenance transport only; impact/priority measurement
  remains the next Phase 5 increment.

### Phase 5M — Live recurrence impact and priority — 2026-09-24

- Two live `converse()` events carrying the same explicit opaque identity now
  produce one native `GapRecurrence` with count **2** and priority **≥2.0**.
  The corresponding assessment remains `human_review` with
  `auto_promoted=0.0`.
- This confirms recurrence impact is graph-native and identity-scoped at the
  communication boundary; no surface repetition participates in the decision.
- Local `.venv` fixture verification: **5 passed in 52.96s**.

### Phase 5N — Competing communication-event learning identities — 2026-09-24

- Replayed two opaque identities through live `converse()` events with native
  recurrence counts **2** and **3**. Their native priorities remained ordered
  by recurrence pressure and each identity retained its own assessment.
- Both assessments remained `human_review` with `auto_promoted=0.0`; no route,
  recurrence, or promotion transferred across identities.
- Local `.venv` fixture verification: **6 passed in 89.07s**.

### Phase 5O — Explicit corpus learning overlay — 2026-09-24

- Added `evaluation/phase5_corpus_learning_overlay.py`, a separately authored
  six-event overlay keyed to existing corpus event IDs. The base 74-event
  corpus remains unchanged and continues to report no learning contract.
- The overlay carries explicit opaque identities and learning-stage/
  verification metadata, then reuses the existing live ingress and native
  recurrence authorities. Three overlay identities each produced native
  recurrence count **2** and priority **2**, with no cross-identity transfer.
- Overlay report:
  `evaluation/reports/phase5_corpus_learning_overlay_report_20260924.json`.
  Native production-recurrence claim is measured for the overlay only; no
  unannotated base-corpus claim is inferred.
- Local `.venv` verification: **3 overlay tests passed in 48.77s** plus the
  existing Phase 5 corpus contract battery (**5 passed in 54.19s**).
- Combined overlay, corpus-contract, live-ingress, and Phase 5B–5G
  compatibility battery: **24 passed in 233.22s**.

### Phase 6S — Native typed partial-event disposition — 2026-09-24

- Integrated the existing `communication_intent_arbitration` seed with typed
  fragment/overlap evidence. Native cognition now records
  `cognitive_disposition=defer` with provenance
  `typed_overlap_partial_event`; no surface route or reply is selected.
- Fresh 74-event replay: **35 state matches**, **39 runtime mismatches**;
  **37** remain `disposition_authority_missing` and **2** are genuine
  `graph_cognitive_state_mismatch` cases (`question_followup`, `error_empty`).
  Receipt semantics remain **30** recoverable, **38** explicit/withheld,
  **6** released mismatches, and **0** missing.
- Local `.venv` verification: **29 passed in 566.43s**; corpus replay
  completed with **74/74** observations.

## 5. Verification gates

| Gate | Required result | Status |
|---|---|---|
| G0.1 | Corpus has cognitive labels, not only expected strings | 🟢 74-event stratified corpus and trace contract pass |
| G0.2 | Trace capture is deterministic with `donkey=0` | 🟡 Focused event trace assertions pass; lifecycle/candidate coverage remains |
| G1.1 | One authoritative interpretation per communication event | 🟢 Focused runtime gate passed |
| G1.2 | Literal form, force, goal, grounding, interaction, and evidence are independently represented | 🟢 Runtime fields, adjudication fixture, and seeded policy verified |
| G1.3 | Adjudicated force/goal agreement reaches ≥95% | 🟢 20/20 = 100.0%; false action/answer/repair = 0 |
| G1.4 | Arbitration consumes language-neutral evidence and survives language variation | 🟢 Spanish/Japanese live LanguageWorld integration passed |
| G2.1 | No unrelated answer can resolve an unknown topic | 🟢 Focused poisoned-candidate regression passed |
| G2.2 | Proposition uptake and consequence projection are measured separately from referent grounding | 🟢 Four-case overlay plus 11 extended lifecycle/boundary tests and seven-case Phase 2T overlay; fixed grounding metrics unchanged |
| G3.1 | Ten-turn mixed dialogue has no orphaned active goals | 🟢 Native mixed-act and asynchronous common-ground stress slices passed |
| G3.2 | CommonGround claims remain scoped to their addressed participant | 🟢 Scoped-ledger correction plus 35-test dependent battery and 38-test compatibility audit; recipient-relative, not pair-relative |
| G4.1 | Candidate generation and native collapse are fully traced | 🟡 Four-family live-manifold generation, native collapse, rejection, execution, settle-back, no-candidate, and repeated counterfactual-credit traces pass; broader task-family coverage remains |
| G4.2 | Accepted proposition consequences cross into deliberation only through a complete authored Phase 4 tuple | 🟢 4 boundary tests passed; native selection and provenance preserved |
| G5.1 | Verified correction changes the intended future route | 🟢 Phase 5A/5B identity, recurrence, and future-route gates passed |
| G6.1 | Every substantive output passes semantic parse-back | 🟡 Phase 6V measures 32 receipt-semantic recoverable releases, 42 explicit/withheld outcomes, and 0 receipt-semantic mismatches; runtime state remains separate with authority gaps and graph-owned disagreements |
| G7.1 | Latency, RSS, graph residence, and replay determinism measured | 🟡 Phase 7L is deterministic and steady-state growth is 9,175,040 bytes, but cold start adds 123,744,256 bytes and the 8-event profile takes 30,740.9 ms; resource/latency targets remain open |
| G8.1 | Baseline comparison report published | 🟡 74-event SUT, ELIZA, local Gemma 4B, and local Qwen 9B raw observations are case-bound by the Phase 8H audit; adjudicated capability scores and human observations remain unavailable, so release gate is blocked |

### Phase 4R — Existing-faculty integration audit — 2026-09-24

- Repeated the substrate audit before the next implementation increment. The
  executable Phase 4 tuple audit remains **0 complete** and **0 near-match**
  seed records; no tuple dimension is inferred from a neighboring faculty.
- Identified reusable partial authorities: `self_dialogue` held graph paths;
  `audience` recipient-relative novelty; `global_workspace` native salience
  and broadcast; `future_option_risk` future residual/escape assessment; and
  the existing gap-prioritization/learning stack for unresolved cognition and
  recurrence.
- Classified these as typed integration seams, not substitutes for Phase 4A:
  salience is not expected value, residual is not consequence, and parse or
  commitment structure is not world grounding without an existing held,
  common-ground, or verified relation.
- **Plan adjustment:** the next increment is a machine-readable partial-evidence
  provenance audit and projection test. Live promotion remains prohibited
  unless one approved faculty supplies all five dimensions. Otherwise native
  `no_candidate` or an explicit integration diagnostic remains the correct
  result.
- Added evaluation-only `evaluation/phase4_partial_evidence_audit.py` and
  `tests/test_phase4_partial_evidence_audit.py`. The audit reports supplying
  faculty, present/missing dimensions, complete-tuple count, eligibility, and
  explicit zero actual promotions; it reads only explicit event-linked graph
  evidence and has deterministic JSON-safe replay. New audit tests: **5
  passed**. Combined Phase 4 battery: **37 passed in 128.96s**.
- Bound the audit into the Phase 8 live observation runner and replayed the
  full 74-event corpus. The current report is
  `evaluation/reports/phase8_corpus_report_20260924_phase4r.json`: **74/74**
  observations, **0** events with typed Phase 4 dimensions, **0** source
  records, **0** complete tuples, **0** eligible promotions, and **0** actual
  promotions; replay determinism is true. Empty `ThoughtManifold` and
  `Deliberation` containers remain native structural/no-candidate traces and
  are not misreported as evidence sources.
- No runtime behavior changed in this audit; no duplicate scorer, scheduler,
referent store, candidate ledger, or surface fallback was added.

### Phase 6T — Receipt mismatch authority audit — 2026-09-24

- Added `evaluation/phase6_receipt_mismatch_audit.py` and a focused regression
  that reads receipt-level provenance without selecting, deleting, or
  rewriting any receipt.
- The 74-event report remains **30** receipt-backed recoverable, **38**
  explicit/withheld, **6** released mismatches, and **0** missing. The six
  mismatches classify as three single-receipt force mismatches, two identical
  duplicate releases, and one competing semantic release pair.
- Report:
  `evaluation/reports/phase6_receipt_mismatch_audit_20260924.json`.
  Reply text and trace flags were not used as semantic evidence.
- Local `.venv` verification: **1 focused audit test passed**. Runtime
  correction remains open and must target the producing cognition/release
  authority.

### Phase 6T runtime correction — 2026-09-24

- Added turn/event-scoped idempotence to the existing production gate. It
  collapses identical releases made during one inbound event even when retry
  calls carry distinct transient commitment nodes, while preserving competing
  semantic events for review.
- Corrected the stale production-test expectation for `Move it now.`: an
  unbound pronoun is now explicitly verified as a repair release, consistent
  with the fixed-corpus `action_pronoun` cognition label; no runtime action
  release was forced.
- Targeted Phase 6A/6T verification: **25 passed**.
- Fresh 74-event replay report:
  `evaluation/reports/phase8_corpus_report_20260924_phase6t.json`. Receipt
  readback is now **32** recoverable, **38** explicit/withheld, **4** released
  mismatches, and **0** missing. The remaining mismatches are three
  single-receipt force mismatches and one competing semantic release pair.
- Updated authority audit:
  `evaluation/reports/phase6_receipt_mismatch_audit_20260924_phase6t.json`.

### Phase 6U — Native partial-event defer/release correction — 2026-09-24

- The existing native `cognitive_disposition=defer` for typed overlap+fragment
  events now controls the release boundary. The adapter no longer releases an
  ask-back repair surface for a partial event; it preserves the graph defer
  state and emits the explicit error floor when no candidate is available.
- Fresh 74-event replay report:
  `evaluation/reports/phase8_corpus_report_20260924_phase6u.json`. Receipt
  readback is **31** recoverable, **42** explicit/withheld, **1** released
  mismatch, and **0** missing. Only `question_ack` retains a competing
  semantic release pair.
- Updated audit:
  `evaluation/reports/phase6_receipt_mismatch_audit_20260924_phase6u.json`.
- Local `.venv` verification: **20 Phase 6/live-bridge tests passed**; the
  typed partial-event regression is covered explicitly.

### Phase 6V — Authoritative topic-release correction — 2026-09-24

- Audited the remaining `question_ack` competing release to its producing
  path. The topic fulfiller was using `answer_about()` as a retrieval helper,
  but that helper also published a legacy structural receipt before the
  conversation-information bridge published the authoritative
  `answer_topic` receipt.
- Added an explicit `release=False` retrieval mode. It preserves the legacy
  parse-back check and graph-held answer evidence, but leaves communicative
  release to the conversation bridge. Direct legacy callers retain the
  default receipt behavior.
- Fresh 74-event replay report:
  `evaluation/reports/phase8_corpus_report_20260924_phase6v.json`.
- Receipt audit:
  `evaluation/reports/phase6_receipt_mismatch_audit_20260924_phase6v.json`.
  Results are **32** receipt-backed recoverable, **42** explicit/withheld,
  **0** released semantic mismatches, and **0** missing authoritative
  evidence. No receipt selection was performed and surface text was not used
  as evidence.
- Focused legacy/information/idempotence verification: **13 tests passed**.

### Phase 6W — Runtime-state authority adjudication — 2026-09-24

- Extended the existing runtime-state adjudicator to consume the current Phase
  8 observation schema directly. It reuses graph/evidence fields already
  present in the replay and does not infer state from reply text, receipts, or
  surface wording.
- Adjudication report:
  `evaluation/reports/phase6_runtime_state_adjudication_20260924_phase6v.json`.
  All **74/74** diagnostics are present: **35** state matches, **37**
  interpretation-only `disposition_authority_missing` cases, and **2** genuine
  graph-owned mismatches (`question_followup`, `error_empty`).
- The two graph-owned cases are not silently rewritten. `question_followup`
  lacks the prior discourse context its isolated replay label presupposes;
  `error_empty` lacks an explicit uncertainty evidence field at the adapter
  boundary and is currently routed through an active topic goal. Neither case
  justifies a wording fix; the next cognition increment must either supply
  typed evidence or revise the independent fixture annotation.
- Local `.venv` verification: **3 adjudication tests passed**.

### Phase 7M — Neutral semantic-ingress authority binding — 2026-09-24

- Audited the existing `WorldAdapter.ingest_semantic_event()` boundary. It
  materializes supplied language-neutral evidence and invokes the existing
  `communication_intent_arbitration` rules; it does not choose a force, goal,
  reply, or turn boundary in Python.
- Added an explicit native-boundary record with provenance
  `native_rule_readback:semantic_event_arbitration` and a regression asserting
  `python_outcome_selection=false`. This reuses the existing Phase 7K
  semantic-event envelope and its native lifecycle tests; no parallel ingress
  or classifier was introduced.
- The current static authority audit is now **10 explicitly bound** and **172
  unbound** cycle/task calls. Unbound calls remain review debt; this increment
  does not relabel them.
- Focused Phase 7/6 verification: **12 tests passed**.

### Phase 7N — Production-envelope substrate cost profile — 2026-09-24

- Extended the existing Phase 7L measurement with boot time, per-event
  latency, RSS delta, and graph delta. These fields are diagnostic only and
  are excluded from semantic replay equality.
- Fresh profile:
  `evaluation/reports/phase7_production_envelope_20260924_phase7n.json`.
  Boot was **16,360 ms**; the first information event took **11,693 ms** and
  added **116,801,536 bytes** RSS; later events took **713–3,221 ms** and the
  remaining steady-state growth was **10,231,808 bytes**. Replay remained
  deterministic.
- A graph-type delta audit found the dominant first-event allocation is the
  mechanical `Agent -knows_concept-> Concept` backfill (**10,755** edges),
  not a reply surface or conversational policy. This is an existing substrate
  referent-resolution index and must be optimized at the substrate/index
  layer, preserving the native mention-resolution rules.
- No speculative optimization was applied. The resource/latency exit remains
  yellow until a bounded index implementation and equivalence battery exist.

### Phase 8H — Raw-reference integrity audit — 2026-09-24

- Added `evaluation/phase8_raw_reference_audit.py`, an evaluation-only audit
  that checks fixed protocol identity, all 74 case IDs, duplicates, unknown or
  missing cases, collection failures, and explicit scorecard availability.
- Audited the existing raw reference runs. ELIZA floor, Gemma 4B, and Qwen 9B
  each have **74/74** case-bound observations with no collection failures.
  Base-human and advanced-human references are explicitly **missing**.
- Report:
  `evaluation/reports/phase8_raw_reference_audit_20260924_phase8h.json`.
  Status is **incomplete** (`3 complete_raw`, `2 missing`). No response text
  was interpreted and no capability score was inferred.
- The comparative release gate remains correctly blocked until blinded
  adjudication and human reference collection exist.

### Phase 7O — Substrate integration and reinvention audit — 2026-09-24

- Added the integration audit at
  `docs/research/psychology_affect/CONVERSATIONAL_MANIFOLD_SUBSTRATE_INTEGRATION_AUDIT_20260924.md`.
- Confirmed reuse points: native `(Concept, name)` lookup, communication
  intent arbitration, discourse state, reflective faculties, topic goals and
  `HeldAnswer`, production receipts, typed partial-event arbitration, and the
  existing partial deliberation faculties.
- Confirmed no new referent store, turn-state machine, self-report generator,
  production ledger, or deliberation scorer is warranted.
- Bounded ordinary ingress now uses the existing concept index; self/meta
  faculties retain their required complete vocabulary ledger.
- Fixed the existing precedence defect where a graph honest-floor response
  shadowed a valid reflective self-organisation readback. This changes
  cognition read-off precedence, not surface wording or production authority.
- Local `.venv` verification: indexed ingress plus two conversation
  compatibility regressions **3 passed**.
- Status: 🟡 — equivalence/resource profiling and the remaining adapter
  authority classification are still required before closing the audit gate.

#### Phase 7O increment — indexed equivalence and scene-authority binding

- Added a two-agent equivalence regression proving indexed ordinary ingress
  and legacy full-ledger ingress produce the same native referent set while
  indexed graph materialization remains bounded.
- Bound the existing conversation-action scene goal `run_rules` readback as
  graph evidence materialization only; no Python outcome selection was added.
- Current audit count: **11 bound**, **171 unbound**, **182 total**. Unbound
  calls remain explicit review debt.
- `.venv`: indexed equivalence **2 passed**; authority battery **6 passed**.
- A one-event production-envelope probe for the optimized ordinary path was
  replay-deterministic, but still measured **11,186 ms** latency and
  **110,010,368 bytes** cold RSS growth with only **342** graph edges added.
  The resource exit therefore remains open as a substrate runtime/warm-up
  issue, not a conversation-surface issue.

## 6. Update rules

- Mark a phase 🟢 only when its exit criterion and tests pass.
- Mark a phase 🟡 when implementation exists but evidence is incomplete.
- Record failures by cognitive category; do not relabel them as style or register issues without evidence.
- Preserve failed traces as regression fixtures.
- Update this tracker in the same change that adds a phase implementation or verification result.

### Phase 7P — Native kind-rule warm-up/readback integration — queued

- Stage tracing isolated the dominant cold allocation in the existing
  `_graph_kind_for()` bridge: complete held-rule serialization to obtain the
  native `sak_kind_*` rules.
- Replaced the separate seed-presence `export_rules()` scan in
  `_ensure_comprehension_seeds()` with the resident graph Rule scan. This
  removed approximately **2.2 s / 31 MB** of separate first-turn cost without
  changing rule authority.
- Remaining kind-rule export cost is approximately **3.9 s / 106 MB** in the
  current probe. The next increment must use selective native readback or an
  explicit boot warm-up; a Python classifier replacement is prohibited.
- Status: queued; Phase 7O resource closure remains yellow.

### Phase 6X — Explicit-failure error disposition — 2026-09-24

- Transported typed `explicit_failure` evidence alongside ordinary
  `explicit_uncertainty`; uncertainty alone remains eligible for repair/defer.
- Added native arbitration for `cognitive_disposition=error` and
  `cognitive_goal=error`, with explicit uncertainty provenance.
- The live adapter now withholds the generic repair/action bridge when the
  native error disposition is present and emits the canonical explicit error.
  No surface token is used as authority.
- The first full replay exposed that treating all uncertainty as error changed
  ordinary defer/repair cases. The rule was narrowed to explicit failure and
  the `error_empty` fixture now carries that distinct evidence.
- Focused `.venv`: **3 tests passed**. Corrected full replay: **36** state
  matches, **37** disposition-authority gaps, **1** graph-owned mismatch
  (`question_followup`); `error_empty` now matches native `error`.
- Report: `evaluation/reports/phase6_explicit_failure_20260924_phase6x_corrected.json`.
- Post-regression recovery battery: **25 tests passed**; the fresh replay is
  `evaluation/reports/phase8_corpus_report_20260924_postregression.json`.
- Full-corpus replay confirmation remains pending; `question_followup` remains
  the separate context-dependent runtime-state mismatch.
- Targeted Phase 8 replay for `error_empty` now matches expected `error` state;
  report: `evaluation/reports/phase6_explicit_uncertainty_20260924_phase6x.json`.
- Status: 🟢 for the Phase 6X focused exit. Phase 6W is adjudicated: the only
  graph-owned mismatch is `question_followup`, whose missing causal world
  evidence is not a conversation-layer defect; the remaining 37 cases lack
  disposition authority rather than proving cognition failure.

### Phase 7P increment — selective native kind-rule readback — 2026-09-24

- Added the Rust/PyO3 `Substrate.export_rules_prefix(prefix)` API and switched
  `_graph_kind_for()` to it for native `sak_kind_*` readback, retaining an
  older-binary fallback.
- Rebuilt the local `.venv` binary. Native API test: **1 passed**.
- `direct_action` replay stayed deterministic; kind-bridge cost improved from
  **3,918.8 ms / 106,143,744 bytes** to about **1,705 ms / 73,453,568 bytes**;
  event latency improved from **9,193.4 ms** to **6,813.0 ms**.
- Report: `evaluation/reports/phase7_kind_readback_20260924_phase7p.json`.
- Cold RSS remains **109,969,408 bytes**, so the resource exit stays yellow;
  remaining work is substrate warm-up/runtime allocation.

#### Phase 7P bounded exit verification — 2026-09-24

- Focused Phase 7 battery covering selective readback, indexed equivalence,
  production envelope, and semantic-event envelope: **11 passed**.
- Native kind authority and replay equality remain green. The cold RSS
  exception is measured and attributed to substrate runtime allocation; no
  Python classifier replacement was introduced.
- Phase 7P: **yellow**. Selective readback is verified, but the declared hard
  resource envelope is still exceeded; the bounded implementation increment is
  complete while the Phase 7 resource exit remains open.

### Phase 7P continuation — conceptualizer output-null authority — 2026-09-24

- The solo alignment audit exposed a remaining Python commitment branch in the
  output-null candidate path: self-target evidence was computed correctly, but
  Python directly minted `Committed` when `recoverable` was true.
- Added the idempotent native rule
  `conceptualizer_output_candidate_commit`. The adapter now materializes the
  candidate and verdict, then reads back the native `Committed` result; it no
  longer selects commit versus withhold in Python.
- This reuses the existing `OutputNullCandidate` / `Verdict` / `Committed`
  vocabulary and leaves `self_target_monitor.score_self_target` as the
  evidence computation. No conversational surface fallback was added.
- Local `.venv` verification: conceptualizer, monitor, output-null, and
  production-gate battery **36 passed**; native-authority focused battery **2
  passed**.
- Native authority census is now **14 bound / 169 unbound / 183 total** and
  remains `review_required`. The increment reduces one direct decision branch;
  the remaining findings and Phase 7 resource envelope are still open.

### Phase 7P continuation — curiosity-topic native settlement — 2026-09-24

- Bound the existing `curiosity_topic_ingest.maintain_topic_interest` native
  settlement path. Python continues to provide only the lexical sensor and
  graph inputs; learning progress and topic-gap minting remain the existing
  native rules.
- Added `NativeCuriosityReceipt` provenance so this boundary is inspectable,
  with `python_outcome_selection=false`.
- Local `.venv`: the native-authority focused test passed; the curiosity
  selection suite passed **5/6**. The remaining test is a pre-existing dirty
  worktree assertion that `runners/dsl/src/py.rs` has no diff; that file is
  already modified by the substrate integration and was not changed here.
- Authority census is now **15 bound / 168 unbound / 183 total**. Status remains
  `review_required`; this is an authority classification increment, not closure
  of Phase 7's resource envelope.

### Phase 7P continuation — cognitive-cycle native boundary — 2026-09-24

- Bound `WorldAdapter.cognitive_tick`'s existing `cognitive_legacy` native
  schedule. The adapter now records `NativeCognitiveCycleReceipt` for the
  native cycle itself; reflex callbacks remain outside this binding and are not
  incorrectly credited as native outcomes.
- Local `.venv` verification: focused native-authority/cognitive-tick battery
  **3 passed**; `git diff --check` passed.
- Authority census is now **16 bound / 167 unbound / 183 total**. Phase 7
  remains `review_required`; this does not close the resource envelope or the
  remaining adapter authority findings.

### Phase 7P continuation — master-cycle native boundary — 2026-09-24

- Bound `WorldAdapter.master_tick`'s existing `master_legacy` native schedule
  with a separate `NativeMasterCycleReceipt`.
- The binding explicitly covers native schedule execution only. Reflex firing,
  thread selection, error capture, and concurrency callbacks remain adapter
  orchestration and are not promoted to native authority.
- Local `.venv` verification: focused native/master/reflex battery **4 passed**;
  `git diff --check` passed.
- Authority census is now **17 bound / 166 unbound / 183 total**. Phase 7
  remains yellow and review-required.

### Phase 7P continuation — live-loop native-cycle delegation — 2026-09-24

- Classified the `live` and `live_examined` adapters' existing
  `cognitive_tick` calls as delegation to the already-bound native
  `cognitive_legacy` schedule. This is deliberately narrower than binding the
  live-loop action gate: world-action authorization and thread/world
  orchestration remain outside the native-cycle claim.
- Local `.venv` verification: focused delegation/authority battery **5 passed**;
  `git diff --check` passed.
- Authority census is now **19 bound / 164 unbound / 183 total**. The audit
  remains `review_required`, with Phase 7 resource and broader authority exits
  still open.

### Phase 7P continuation — actor-goal settlement boundary — 2026-09-24

- Bound `actor_goals.annotate_actor_action`, whose adapter role is to
  materialize structural `ActorAction` facts and invoke the existing native
  actor-goal rules. The native settlement now emits
  `NativeActorGoalReceipt`; Python does not select an actor goal or conflict.
- Local `.venv`: actor-goal migration suite **11 passed**; focused authority
  battery **3 passed**; `git diff --check` passed.
- Authority census is now **20 bound / 163 unbound / 183 total**. This is a
  bounded faculty integration; Phase 7 remains review-required.

### Phase 7P continuation — disclaimer-candidate settlement boundary — 2026-09-24

- Bound `actor_goals.annotate_disclaimer_candidates`: Python emits contiguous
  candidate n-grams mechanically, while the existing agent-authored disclaimer
  codebook rules settle which candidates are meaningful.
- Added `NativeDisclaimerReceipt` with explicit native provenance and no Python
  outcome selection.
- Local `.venv`: focused authority battery **3 passed**; full disclaimer/conflict
  regression suite **7 passed**; `git diff --check` passed.
- Authority census is now **21 bound / 162 unbound / 183 total**. Phase 7 is
  still yellow/review-required.

### Phase 7P continuation — action-pair settlement boundary — 2026-09-24

- Bound `actor_goals.annotate_action_pairs`: structural same-actor/object pair
  enumeration remains mechanical, while opposing-pair and temporal-conflict
  interpretation remains in the existing authored native rules.
- Added `NativeActionPairReceipt` with explicit native provenance and no Python
  outcome selection.
- Focused `.venv` authority test battery: **3 passed**. The full temporal
  regression was stopped after **7:52** at 100% CPU; it reported three
  unrelated/pre-existing failures (seed JSON shape, an authored note fixture,
  and a later pair-coverage assertion) plus a keyboard interrupt. This
  increment did not alter the pair enumeration semantics.
- Authority census is now **22 bound / 161 unbound / 183 total**. Phase 7
  remains review-required; the temporal suite requires separate repair before
  it can be treated as green.

#### Temporal regression data-quality correction — 2026-09-24

- Corrected the persisted `seeds/taught.json` opposing-pair notes from the
  placeholder `x` to the already-documented semantic note. This restores the
  codebook data expected by the temporal reading tests; it does not add a rule
  or surface heuristic.
- Hardened the temporal seed-audit helper to skip valid list-shaped manifests
  rather than treating them as rule dictionaries.
- The isolated temporal tests still exceed the practical runtime envelope and
  were interrupted after roughly 45 seconds without completing; no green
  temporal-suite claim is made. The remaining pair-coverage/runtime issue is
  still open.

### Phase 7P continuation — epistemic assessment boundary — 2026-09-24

- Bound both native `run_rules` passes in
  `actor_goals.assess_epistemic_lean`: detection/structural evidence settlement
  and the epistemic combine band. The Python function only orchestrates those
  passes and reads graph verdicts.
- Added `NativeEpistemicAssessmentReceipt` with explicit native provenance and
  `python_outcome_selection=false`.
- Exact local `.venv` receipt test: **1 passed in 3.22s**. A broader command
  reached **31 passed in 300.85s** before being interrupted because its broad
  selection expression continued into slow suites; it is not used as a green
  full-suite claim.
- Authority census is now **24 bound / 159 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — actor self-authoring execution boundary — 2026-09-24

- Bound `_author_layer_rule`'s post-synthesis native execution. The procedural
  reader, binding resolver, and method synthesizer remain the existing
  self-authoring faculties; the new receipt covers only execution of the
  installed authored rule and does not claim Python semantic authority.
- Added `NativeActorRuleAuthoringReceipt` with explicit provenance.
- Exact local `.venv` verification: **1 passed in 3.34s**; `git diff --check`
  passed.
- Authority census is now **25 bound / 158 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — meaning-inference slot boundary — 2026-09-24

- Bound `meaning_inference.annotate_predication_slots` to the existing native
  selectional-inference rules. Python still extracts grounded predication-slot
  facts mechanically; native rules retain selectional interpretation.
- Added `NativeMeaningInferenceReceipt` with explicit provenance and no Python
  outcome selection.
- Exact local `.venv` verification: **1 passed in 5.26s**; `git diff --check`
  passed.
- Authority census is now **26 bound / 157 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — definitional-inference fact boundary — 2026-09-24

- Bound `meaning_inference.annotate_predication_facts` to the existing native
  definitional-inference rules. Python materializes relational facts; native
  rules retain sense inference and evidence settlement.
- Added the native provenance receipt for this settlement boundary.
- Exact local `.venv` verification: **1 passed in 5.29s**; `git diff --check`
  passed.
- Authority census is now **27 bound / 156 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — morphological-inference candidate boundary — 2026-09-24

- Bound `meaning_inference.annotate_affix_candidates` to the existing native
  morphology rules. Python enumerates structural prefix/suffix candidates;
  native rules retain morpheme interpretation and longest-match settlement.
- Added native provenance receipt without Python outcome selection.
- Exact local `.venv` verification: **1 passed in 5.23s**; `git diff --check`
  passed.
- Authority census is now **28 bound / 155 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — relational-signature inference boundary — 2026-09-24

- Bound `meaning_inference.annotate_relational_signatures` to the existing
  native structural-analogy rules. Python aggregates explicit relational facts;
  native rules retain codebook matching and structural transfer.
- Added native provenance receipt without Python outcome selection.
- Exact local `.venv` verification: **1 passed in 5.37s**; `git diff --check`
  passed.
- Authority census is now **29 bound / 154 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — recount scene realization boundary — 2026-09-24

- Bound `recount_faculty.project_read_scene` to the existing native recount
  realization/fluency rules. Python materializes the read scene; native rules
  retain event realization and residual decisions.
- Added `NativeRecountReceipt` with explicit native provenance and no Python
  outcome selection.
- Exact local `.venv` verification: **1 passed in 3.38s**; `git diff --check`
  passed.
- Authority census is now **30 bound / 153 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — passive and intent-signal analysis boundaries — 2026-09-24

- Bound the existing `media_analysis` passive-role and intent-signal native
  settlements. Python materializes structural passive/intent facts; native
  rules retain deletion/framing and intent-attribution decisions.
- Added explicit media-analysis provenance receipts for both boundaries.
- Exact local `.venv` verification: **1 passed in 5.17s**; `git diff --check`
  passed.
- Authority census is now **32 bound / 151 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — relational-noun analysis boundary — 2026-09-24

- Bound `media_analysis.annotate_relational_noun` to the existing native
  relational-noun/unsaid-role rules. Python continues to materialize the
  mechanically adjacent nominal evidence; native rules retain relational
  codebook matching and residual-question settlement.
- Added `NativeMediaAnalysisReceipt` provenance for the settlement, with
  `outcome_source: native_rule_readback` and no Python outcome selection.
- Exact local `.venv` verification: **1 passed in 5.20s**; `git diff --check`
  passed.
- Authority census is now **33 bound / 150 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — recount reasoning boundary — 2026-09-24

- Bound `recount_faculty.recount_what_read`'s instruction-to-reasoning native
  execution to the existing recount communication rules. Article parsing,
  scene projection, and prose production remain their existing faculty/I/O
  responsibilities; this receipt does not promote them to native authority.
- Added a native provenance receipt with explicit `outcome_source` and no
  Python outcome selection.
- Focused local `.venv` receipt test: **1 passed in 0.35s**; `git diff --check`
  passed. The full recount integration test exceeded a bounded 90-second run,
  so it is not claimed as green evidence.
- Authority census is now **34 bound / 149 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — recount analysis reasoning boundary — 2026-09-24

- Bound `recount_faculty.analyse_what_read`'s analysis-scene reasoning pass to
  the existing native recount analysis rules. The analysis reader continues
  to project already-held readings; native execution remains the authority for
  the resulting reasoning/realization state.
- Added a separate native provenance receipt so surface recount and analysis
  reasoning are not conflated.
- Focused local `.venv` verification: **2 passed in 0.36s** (recount and
  analysis receipt tests); `git diff --check` passed.
- Authority census is now **35 bound / 148 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — recount analysis-scene boundary — 2026-09-24

- Bound `recount_faculty.project_analysis_scene` to the existing native
  analysis-realization rules. Python remains a type-blind projector of held
  readings; native rules retain frame-slot/realization settlement.
- Added explicit receipt provenance for the analysis scene pass.
- Focused local `.venv` verification: **3 passed in 0.46s** (recount,
  analysis-reasoning, and analysis-scene receipts); `git diff --check` passed.
- Authority census is now **36 bound / 147 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — conceptualizer candidate settlement — 2026-09-24

- Bound `conceptualizer.scan_and_monitor`'s output-candidate native commit
  pass to the existing `conceptualizer_output_candidate_commit` rule. The
  self-target monitor remains evidence production; Python does not select the
  commit outcome.
- Added an explicit candidate-settlement receipt with native provenance.
- Focused local `.venv` verification: **1 passed in 0.39s**; `git diff --check`
  passed.
- Authority census is now **37 bound / 146 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — information-commitment decision boundary — 2026-09-24

- Bound `information_commitment.assess` to the existing native manifold gate.
  Python continues to materialize candidate projections and apply the separate
  external-approval check; native rules retain wait/refine/commit selection.
- Added graph-resident native decision provenance without adding a duplicate
  decision scorer or approval mechanism.
- Exact local `.venv` verification: **1 passed in 0.21s**; `git diff --check`
  passed.
- Authority census is now **38 bound / 145 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — situation-model predication settlement — 2026-09-24

- Bound all four native fixpoint calls in
  `situation_model_reader.ingest_predication` to the existing situation-model
  rules. Python continues to materialize grounded entities/events and
  mechanical indices; native rules retain state-transition and follow-on
  inference settlement.
- Added per-pass native provenance receipts so property, generic-event, and
  change-of-state paths remain distinguishable.
- Exact local `.venv` verification: **1 passed in 2.17s**; `git diff --check`
  passed.
- Authority census is now **42 bound / 141 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — inference-generation relation settlement — 2026-09-24

- Bound `inference_generation._mint_part_of` to its existing native fixpoint
  after mechanical relation materialization. Python writes the graph relation;
  native rules retain downstream inference settlement.
- Added explicit native provenance for the relation pass.
- Exact local `.venv` verification: **1 passed in 0.35s**; `git diff --check`
  passed.
- Authority census is now **43 bound / 140 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — disambiguation and metonymic settlement — 2026-09-24

- Bound `cognitive_disambiguation.coherence_check` and
  `metonymic_redecode` to their existing native coercion rules. Python remains
  responsible for evidence preparation and ledger readback; native rules retain
  role repair and metonymic re-binding decisions.
- Added separate native provenance receipts for coherence and metonymic paths.
- Exact local `.venv` verification: **1 passed in 2.22s**; `git diff --check`
  passed.
- Authority census is now **45 bound / 138 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — reflective concern decode boundary — 2026-09-24

- Bound `reflective_faculty.induce_concern` to the existing native
  `shape_decode_loop`. Python continues to ingest the observation and read the
  resulting status; native rules retain recognition/transformation/novelty
  settlement.
- Added explicit native provenance for the concern-decode pass.
- Exact local `.venv` verification: **1 passed in 0.33s**; `git diff --check`
  passed.
- Authority census is now **46 bound / 137 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — reflective role and correspondence settlement — 2026-09-24

- Bound `reflective_faculty.check_new_relation_cue_roles` and
  `record_correspondence` to their existing native vocabulary/correspondence
  rules. Python remains mechanical evidence ingestion and verdict readback;
  native rules retain role collision and structural-collapse decisions.
- Added distinct native provenance receipts for both boundaries.
- Focused local `.venv` verification: **2 passed in 32.37s**; `git diff --check`
  passed.
- Authority census is now **48 bound / 135 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — reading-drive native-cycle delegation — 2026-09-24

- Bound `reading_drive._tick_reading` as a delegation-only boundary to the
  already verified native cognitive cycle. The reading loop remains a bounded
  steady-state observer; it does not select stage outcomes in Python.
- Focused local `.venv` verification: **1 passed in 3.31s**; `git diff --check`
  passed.
- Authority census is now **49 bound / 134 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — cognitive rule-frame settlements — 2026-09-24

- Bound document reading, situation observation, prediction commitment, and
  private drafting to their existing native rule-frame passes.
- Added distinct native provenance receipts for each cognitive boundary;
  external world action remains outside these private cognition paths.
- Exact local `.venv` verification: **1 passed in 2.09s**; `git diff --check`
  passed.
- Authority census is now **53 bound / 130 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — capability-graph fixpoint settlement — 2026-09-24

- Bound `capability_graph.settle` to the existing native capability fixpoint.
  Python remains graph construction/readback; native rules retain leverage,
  effective-capability, sufficiency, and stage settlement.
- Added explicit native provenance receipt.
- Exact local `.venv` verification: **1 passed in 0.24s**; `git diff --check`
  passed.
- Authority census is now **54 bound / 129 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — autonomous-discovery settlement — 2026-09-24

- Bound `autonomous_discovery.settle_native` to the existing native discovery
  rules and recorded provenance directly on the native substrate. This keeps
  the post-submission adapter write guard intact; instrumentation is not an
  adapter-side cognitive write.
- Autonomous-discovery corpus verification: **8 passed in 0.34s**;
  `git diff --check` passed.
- Authority census is now **55 bound / 128 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — analogical correspondence settlement — 2026-09-24

- Bound pair correspondence, directional correspondence, and the legacy
  idempotent native safety pass to existing analogical rules. Python continues
  witness preparation and result readback; native rules retain collapse and
  direction decisions.
- Added native provenance receipts for each correspondence boundary.
- Exact local `.venv` verification: **1 passed in 16.46s**; `git diff --check`
  passed.
- Authority census is now **58 bound / 125 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — procedural referent cross-check — 2026-09-24

- Bound both native passes in `procedural_reader._referent_crosscheck` to the
  existing procedural referent rules: resolution and scratch retirement.
- Added per-pass native provenance receipts; the probe lifecycle remains
  bounded and does not leak conversation `Mention` nodes.
- Exact local `.venv` verification: **1 passed in 16.67s**; `git diff --check`
  passed.
- Authority census is now **60 bound / 123 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — analogy-search settlement — 2026-09-24

- Bound analogy observation and crystallization to their existing native rules.
  Python remains probe/evidence preparation; native rules retain analogy
  emission and identity-field crystallization decisions.
- Added explicit native provenance receipts for both passes.
- Exact local `.venv` verification: **1 passed in 0.28s**; `git diff --check`
  passed.
- Authority census is now **62 bound / 121 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — predictive-reading native-cycle delegation — 2026-09-24

- Bound predictive arc reading and residual-sized dwell processing as
  delegation-only paths to the existing native cognitive cycle. Python remains
  stage setup/readback; native reflexes and graph rules retain anticipation and
  dwell settlement.
- Focused local `.venv` verification: **2 passed in 7.30s**; `git diff --check`
  passed.
- Authority census is now **64 bound / 119 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — cross-text residual re-decode — 2026-09-24

- Bound `cross_text_prior.extend_on_residual`'s post-axis native re-decode to
  the existing `sd_redecode` rule. Python remains feature comparison,
  graph-materialized axis growth, and readback; native rules retain residual
  recognition/re-decode settlement.
- Added explicit native provenance receipt.
- Exact local `.venv` verification: **1 passed in 2.15s**; `git diff --check`
  passed.
- Authority census is now **65 bound / 118 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — reasoning/CAN correspondence settlement — 2026-09-24

- Bound `reasoning_can_bridge._run_correspondence` to its existing native
  correspondence rules. Python remains name-token preparation; native rules
  retain correspondence settlement into the reasoning/CAN substrate.
- Added explicit native provenance receipt.
- Exact local `.venv` verification: **1 passed in 0.35s**; `git diff --check`
  passed.
- Authority census is now **66 bound / 117 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — AST-to-rule native term settlement — 2026-09-24

- Bound `ast_to_rule` expression and body term composition to the existing
  native AST-to-term rules. Python remains AST ingestion and term readback;
  native rules retain graph term construction.
- Added separate native provenance receipts for expression and body passes.
- Exact local `.venv` verification: **1 passed in 1.73s**; `git diff --check`
  passed.
- Authority census is now **68 bound / 115 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — faculty autogenesis settlement — 2026-09-24

- Bound `faculty_autogenesis.pump`'s native discovery pass to the existing
  faculty-autogenesis rules. Python remains evidence serialization and native
  synthesis I/O; native rules retain status, installation, and escalation
  decisions.
- Added explicit native provenance receipt.
- Exact local `.venv` verification: **1 passed in 0.82s**; `git diff --check`
  passed.
- Authority census is now **69 bound / 114 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — minting train segment settlement — 2026-09-24

- Bound `minting_train_of_thought.run_minting_train_of_thought` segment
  fixpoints to the existing native minting rules. Python remains segment
  evidence preparation and bounded traversal; native rules retain recurrence
  and settlement decisions.
- Added per-segment native provenance receipts.
- Focused local `.venv` verification: **3 passed in 0.27s**; `git diff --check`
  passed.
- Authority census is now **70 bound / 113 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — solver-dispatch settlement — 2026-09-24

- Bound CAN-network growth and bounded goal-resolution dispatch to their
  existing native rule executions. Python remains evidence preparation,
  scheduling, and readback; native rules retain settlement authority.
- Added typed native provenance receipts without changing the resolver
  selection or outcome semantics.
- Focused local `.venv` verification: **22 passed in 34.54s** across the
  solver-dispatch and natural-language adapter suites. The independent CAN
  growth test remains a pre-existing baseline failure (`grown=False`) even
  without this increment; it is not treated as evidence for the receipt
  change.
- Authority census is now **73 bound / 110 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — fallback-report classification — 2026-09-24

- Bound the fallback readout's existing graph classification pass to its native
  rule set. Python remains counter transcription; the native rules retain
  classification authority.
- Added a typed native provenance receipt without introducing a fallback string
  or conversational repair path.
- Focused local `.venv` verification: **3 passed in 0.50s**; `git diff --check`
  passed.
- Authority census is now **74 bound / 109 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — affect-coordinate readback — 2026-09-24

- Bound `prosody_generation.substrate_affect_coord` to the existing native
  modulator rules. Python configures the drive and reads the resulting affect
  coordinate; it does not compute valence or arousal.
- Added typed native provenance for the affect readback.
- Focused affect verification passed; the suite's independent native-binary
  MD5 discipline check remains red because the current `.so` hash differs from
  its pre-committed canonical hash. This is not caused by the Python change.
- Authority census is now **75 bound / 108 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — upload-text cognitive pump delegation — 2026-09-24

- Bound the upload-text reader's `cognitive_tick` delegation to the existing
  native cognitive schedule. The pump remains mechanical stage progress; it
  does not select or synthesize a conversational outcome.
- Local `.venv` test invocation was dependency-gated: **1 skipped in 0.27s**
  because optional `cv2` is unavailable. No failure was hidden.
- Authority census is now **76 bound / 107 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — foveal salience selection — 2026-09-24

- Bound `fovea_bridge.resolve_fovea` to the existing native
  `ArgminUnique` salience rule and added typed provenance. Python remains
  candidate ingress and graph readback; it does not select the fovea.
- Test collection was refused by the engine-provenance guard because the
  current native binary is stale relative to 18 newer Rust sources. The guard
  was not bypassed.
- Authority census is now **77 bound / 106 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — problem-shape observation decode — 2026-09-24

- Bound structural problem-shape observation to the existing native decode
  rules. Python remains goal-shape extraction and graph ingress; native rules
  retain recognition and growth decisions.
- Focused local `.venv` verification: **3 passed, 5 deselected in 18.33s**;
  `git diff --check` passed.
- Authority census is now **78 bound / 105 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — meta-shape observation growth — 2026-09-24

- Bound meta-shape observation to its existing native growth rules and added
  typed provenance. Python remains signature ingress; native rules retain
  recognition, recurrence, and growth decisions.
- Focused local `.venv` verification: **14 passed in 0.83s**;
  `git diff --check` passed.
- Authority census is now **79 bound / 104 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — rule-dispute settlement — 2026-09-24

- Bound the integrated dispute/self-worth/emotion pipeline to its existing
  native settlement rules and added typed provenance. Python remains evidence
  construction and readback; native rules retain appraisal and outcome
  decisions.
- Focused local `.venv` verification: **2 passed in 0.23s**;
  `git diff --check` passed.
- Authority census is now **80 bound / 103 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — equation isolation settlement — 2026-09-24

- Bound equation solving to its existing native rewrite rules and added typed
  provenance. Python remains equation construction and result readback; native
  rules retain isolation authority.
- Focused local `.venv` verification: **4 passed in 0.22s**;
  `git diff --check` passed.
- Authority census is now **81 bound / 102 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — spatial-belief observation settlement — 2026-09-24

- Bound spatial-belief observation ingestion to its existing native settlement
  rules and added typed provenance. Python remains geometric observation
  preparation; native rules retain occupancy/belief settlement.
- The available Doom integration test could not collect because optional
  `vizdoom` is unavailable; the selected per-area suite contained no matching
  spatial test. No test was bypassed.
- Authority census is now **82 bound / 101 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — disposition trait settlement — 2026-09-24

- Bound trait relaxation, momentary pull, and crystallization to the existing
  native disposition dynamics, with operation-specific typed provenance.
  Python remains evidence/configuration and field readback.
- Focused local `.venv` verification: **5 passed, 25 deselected in 0.59s**;
  `git diff --check` passed.
- Authority census is now **85 bound / 98 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — frame-weight settlement — 2026-09-24

- Bound quantum frame updates and pooled reliability refreshes to their
  existing native weight rules, with separate typed provenance. Python remains
  evidence/request preparation and readback.
- Focused local `.venv` verification: **3 passed, 12 deselected in 0.41s**;
  `git diff --check` passed.
- Authority census is now **87 bound / 96 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — trait-modulator bridge settlement — 2026-09-24

- Bound modulator initialization, trait-to-modulator bias sync,
  modulator-to-trait crystallization, batched trait relaxation, drive
  homeostasis, and personality homeostasis to their existing native rules.
- Added typed provenance for each bridge boundary; Python remains configuration,
  evidence transfer, scheduling, and readback.
- Focused local `.venv` verification: **17 passed, 12 deselected in 1.52s**;
  `git diff --check` passed.
- Authority census is now **94 bound / 89 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — self-worth CAN bridge settlement — 2026-09-24

- Bound resident self-worth initialization/reuse, incident updating, domain
  projection, self-conscious consequence settlement, and peer comparison to
  their existing native CAN rules.
- Provenance receipts are inserted before the native fixpoint so they do not
  perturb the substrate's dirty-tracking/no-op semantics.
- Focused local `.venv` verification: **26 passed in 0.61s**;
  `git diff --check` passed.
- Authority census is now **101 bound / 82 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — native reading-rule validation — 2026-09-24

- Bound all seven native validation passes in `read_method_draft` to explicit
  native-rule provenance. Python remains draft installation, test-instance
  construction, and readback.
- The direct conversational code-growth regression remains upstream-red at
  faculty routing (`no attached world/faculty`), before this validator is
  reached; it is recorded rather than masked.
- Authority census is now **108 bound / 75 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — hate-attribution settlement — 2026-09-24

- Bound understanding incidents and both native passes of hate-incident
  appraisal/evidence settlement to existing native rules. Receipts precede
  each fixpoint to preserve dirty-tracking semantics.
- Focused local `.venv` verification: **19 passed in 0.62s**;
  `git diff --check` passed.
- Authority census is now **111 bound / 72 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — spatial-sense settlement — 2026-09-24

- Bound quanta flood scheduling and spatial navigation settlement to their
  existing native rules, preserving the two-phase convergence schedule and
  graph-owned action decisions.
- Focused local `.venv` verification: **8 passed in 0.32s**; compilation and
  `git diff --check` passed.
- Authority census is now **117 bound / 66 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — ink-decoding settlement — 2026-09-24

- Bound ink lattice forward/backtrace, refinement, and writer settlement to
  existing native rules. Python remains geometry/evidence preparation and
  graph readback; no Python ranking decision was introduced.
- Focused local `.venv` verification: **5 passed, 29 deselected in 0.54s**;
  compilation and `git diff --check` passed.
- Authority census is now **121 bound / 62 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — program-synthesis settlement — 2026-09-24

- Bound program order-lattice forward/backtrace and synthesis fixpoint pumping
  to existing native rules. Python remains mechanical dispatch and readback;
  program-selection decisions remain graph-native.
- Focused local `.venv` verification: **3 passed in 0.32s**;
  `git diff --check` passed.
- Authority census is now **125 bound / 58 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — two-eye super-resolution settlement — 2026-09-24

- Bound retinal sampling and super-resolution fusion to their existing native
  cognitive task/rule execution, with typed provenance. Python remains sensor
  packet/task preparation and reconstruction readback.
- Focused local `.venv` verification: **13 passed, 4 deselected in 0.65s**;
  `git diff --check` passed.
- Authority census is now **129 bound / 54 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — affect/social evidence settlement — 2026-09-24

- Bound resident trust initialization/incidents, self-efficacy incidents,
  shared arousal incidents, and envy deservingness evidence to their existing
  native rules. Python remains evidence ingress and readback.
- Focused local `.venv` verification: **30 passed in 0.74s**;
  `git diff --check` passed.
- Authority census is now **134 bound / 49 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — sensory-selection settlement — 2026-09-24

- Bound sensory kernel selection/discrimination, feature cue selection, and
  modality-reflex training to existing native rules. Python remains field
  ingress and readback; selection remains graph-native.
- Focused local `.venv` verification: **2 passed in 0.77s**; compilation and
  `git diff --check` passed.
- Authority census is now **138 bound / 45 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — 2-D vision task settlement — 2026-09-24

- Bound 2-D retinal sampling and vision-graph convolution task execution to
  existing native task/rule execution. Python remains sensor/task packing and
  readback.
- Focused local `.venv` verification: **9 passed in 0.45s**. The broader
  vision-graph collection remains dependency-limited by missing `cv2`.
- Authority census is now **141 bound / 42 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — world-adapter photon settlement — 2026-09-24

- Bound both world-adapter photon-sheet native task/rule passes to explicit
  cycle provenance. Python remains sensor ingress and percept readback.
- Compilation and `git diff --check` passed. The interactive integration test
  remains dependency-limited because `vizdoom` is unavailable.
- Authority census is now **145 bound / 38 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — program-chunk growth settlement — 2026-09-24

- Bound program-chunk growth's native fixpoint pump to explicit provenance;
  Python remains scan dispatch and readback.
- Focused local `.venv` verification: **1 passed, 10 deselected in 0.27s**;
  compilation and `git diff --check` passed.
- Authority census is now **147 bound / 36 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — grounding and appraisal guards — 2026-09-24

- Bound whisper grounding inference, trait-anxiety classification, Enigma
  crib admissibility, and salience-cache ticking to existing native execution.
- Salience remains delegation-only because disconnected provenance nodes changed
  its existing tale-agency behavior; the receipt mutation was removed. Its
  tale-agency test remains a baseline failure even without that mutation.
- Focused verification for whisper/trait-anxiety/Enigma: **25 passed**; the
  separate native-binary MD5 discipline check remains red. `git diff --check`
  passed.
- Authority census is now **151 bound / 32 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — lifted-rule and extension verification — 2026-09-24

- Bound lifted-rule fixpoint execution and substrate-extension verification to
  native execution boundaries. Extension remains delegation-only because its
  existing verifier changes behavior when disconnected receipt nodes are
  added.
- Substrate-extension verification: **16 passed, 3 baseline failures**;
  teacher-dispatch collection is dependency-limited by missing `requests`.
- Authority census is now **153 bound / 30 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — world identity/enactment settlement — 2026-09-24

- Bound control enactment, cross-frame identity, identity-seam growth, and
  verdict-comparator settlement to existing native rules.
- Cross-frame verification: **12 passed, 5 skipped in 1.24s**. Identity-seam
  verification remains refused by the stale-engine provenance guard.
- Authority census is now **157 bound / 26 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — affective world-model settlement — 2026-09-24

- Bound frustration observation, mood stepping, and harvest/spite decision
  settlement to existing native rules. Python remains world-state ingress and
  readback.
- Focused `.venv` test command completed successfully; `git diff --check`
  passed.
- Authority census is now **160 bound / 23 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — world-discovery settlement — 2026-09-24

- Bound falling-order discovery, Galileo fall discovery, push-mass discovery,
  and physics/lever simulation settlement to existing native rules.
- Physics/Galileo verification: **11 passed in 1.16s**. Falling/mass tests
  remain refused by the stale-engine provenance guard.
- Authority census is now **165 bound / 18 unbound / 183 total**. Phase 7
  remains yellow/review-required.

### Phase 7P continuation — perception/world-model boundary settlement — 2026-09-24

- Bound Achieve, agnosia, allocentric-view, Bigville disposition, Bigville
  register, and Marshmallow delay execution to their existing native rules
  with typed provenance. Python remains ingress, orchestration, and readback.
- Focused `.venv` verification: Bigville disposition **8 passed**, Bigville
  register **10 passed**, and allocentric view **19 passed**. Marshmallow
  produced **7 behavioral passes**; its canonical native-binary MD5 discipline
  check remains red, as does the equivalent spite-suite hash check.
- Authority census is now **171 bound / 12 unbound / 183 total**. The twelve
  remaining findings are the Doom ingestion/operation/pattern-eye paths,
  Harvest world, and invariant comparator; Phase 7 remains yellow and
  review-required.

### Phase 7P continuation — complete native authority census — 2026-09-24

- Classified the remaining Harvest, invariant-comparator, and Doom
  ingestion/operation/pattern-eye calls as explicit native delegation
  boundaries. These adapters already perform mechanical ingress/readback; no
  Python outcome selection was added.
- Focused `.venv` verification: Harvest **6 behavioral passes** (one known
  native-binary hash failure), invariant comparator **22 passed / 4 skipped**,
  Doom allocentric **9 passed / 1 skipped**, Doom dual-process **10 passed**,
  Doom predictive priors **9 passed / 1 skipped**, and Doom operate/texture
  **16 passed**. Doom emotion behavior passed; its two failures are canonical
  native-binary/disallowed-runner-diff discipline checks.
- Native authority audit is now **183 bound / 0 unbound / 183 total** with
  status `clean`. This closes the static authority-inventory gate, but does
  not by itself close Phase 7: runtime envelope, artifact provenance, and
  broader cognition exit criteria remain to be verified.

### Phase 7P exit audit — 2026-09-24

- Fresh production-envelope measurement over the fixed eight-event profile:
  replay deterministic, **0 runtime errors**, boot **16,387 ms**, total
  profile latency **46,617 ms**, cold RSS growth **122,265,600 bytes**, and
  steady-state RSS growth **11,411,456 bytes**.
- The cold RSS result exceeds the declared **100 MB** envelope, and the
  measured latency is far above the declared fast/deep limits. The residual is
  attributed to substrate/runtime cold allocation and remains an engineering
  blocker; no surface-language workaround is permitted.
- Added and passed `tests/test_grammar_inversion.py`: **6 focused passes**
  including 100% grammar round-trip recovery and the existing self-target
  monitor. The older `ThoughtSegment -> Committed` deliberative-production
  contract remains open because the live path currently exposes a different
  native deliberation trace and has no causal integration between those node
  types.
- Phase 7 remains open despite the clean **183/183 native authority** census;
  Phase 8 remains blocked on complete target/reference scorecards, especially
  base-human and advanced-human observations.

### Gate 3 contract reconciliation — 2026-09-24

- The legacy `ThoughtSegment -> Committed` label was not the live conversational
  substrate contract. It belongs to autonomous discovery. The conversational
  deliberation authority is the native `DeliberationExecutionTrace` plus
  `DeliberationSettlement` chain.
- Added `tests/test_deliberative_production.py` to establish a grounded
  candidate for one communicative goal, settle it natively, and verify that the
  existing monitor-cleared `Committed` release remains graph-resident for the
  same goal.
- Focused `.venv` verification: **1 passed in 23.27s**. This closes the
  reconciled Gate 3 contract without adding a duplicate thought store.

### Runtime optimization rejection — 2026-09-24

- A native `sak_kind_*` prefix-fixpoint prototype was measured as a possible
  replacement for the selective rule-export boundary in `_graph_kind_for`.
- It was rejected: the live speech-act parity corpus changed instruction
  content and WH-question dispatch, while minimal-boot RSS still grew by about
  **187 MB**. No semantic drift was accepted for a performance optimization.
- The prototype API and live-path use were removed and the native extension was
  rebuilt from the restored source. Future runtime work must preserve held-rule
  parity and target the allocation boundary directly; it must not become a
  language or conversation-level shortcut.

### Existing-faculty comprehension routing correction — 2026-09-24

- Routed the existing `satisfiable` and `honest_no_world` selected dispatch
  paths through their existing faculties in the live adapter. Satisfiable
  self-report results retain their graph-minted goal for the existing
  production bridge. The unresolved plain-statement case continues to expose
  the canonical explicit diagnostic error.
- `.venv` verification: comprehension robustness **9 passed**; conversation
  loop, utterance/conversation unification, output-null, and Phase 6A
  production gates **32 passed**. The handoff-named
  `test_phase6_production_gate.py` is absent in this checkout.
- No Phase 4/6/7/8 acceptance status changes: complete live Phase 4 evidence,
  the measured resource envelope, and base/advanced human references remain
  open.
