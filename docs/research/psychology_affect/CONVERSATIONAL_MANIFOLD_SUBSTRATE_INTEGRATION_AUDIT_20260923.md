# Conversational Manifold Substrate Integration Audit

Date: 2026-09-23  
Scope: existing substrate primitives, recent conversation-manifold additions, and
the live `WorldAdapter.converse()` integration boundary.

## Outcome

The substrate already contains most of the required cognitive machinery. The
conversation layer should compose it, not introduce parallel state and decision
systems. The immediate blocker is an integration seam, not a missing reply
feature: conversation-created goals are not consistently linked to the inbound
message they comprehend, so live discourse state cannot bind those goals and
the Phase 4 deliberation bridge remains unexercised in the production corpus.

## Existing substrate primitives to reuse

| Cognitive responsibility | Existing authority | Integration action |
|---|---|---|
| Event/message identity | `Message`, `received`, `sent`, `responds_to`, `in_channel` | Treat `Message` as the event anchor; `DiscourseEvent` should be its state projection, not a second event identity. |
| Intent and force | `Intent`, `CommunicationInterpretation`, `communication_evidence.v1`, `seeds/communication_intent_arbitration.json` | Keep neutral evidence and interpretation; do not add another force classifier. |
| Goals | `Goal`, `agent -has_goal-> Goal`, `comprehends`, `interlocutor_model.wanted_by` | Make every conversation goal use the existing comprehension relation and existing goal ownership. |
| Reference/common ground | `domains.reference_resolution.DiscourseStore`, `DiscourseReferent`, `CenteringState`, `conversation.py` common-ground concepts | Consolidate the new `DiscourseState` common-ground ledger with the existing referent store; do not maintain parallel referent identities. |
| Thought competition | `ThoughtManifold`, `global_workspace`, `train_of_thought`, native `Argmax`/collapse paths | Use the existing manifold/workspace as candidate evidence; Phase 4 only transports evidence into its ledger. |
| Residual and learning | `SelfConcern`, `Residual`, `GoalResidual`, gap-awareness and self-correction faculties | Link communication failures to the existing residual/gap lifecycle rather than inventing a conversation-only learning store. |
| Production | `conceptualizer`, audience/production faculties, `ProductionGateReceipt`, parse-back/readback | Keep production gating as a release boundary; it must consume selected cognition and never select it. |
| Native execution | `Substrate.run_rules*`, scoped/native cycles, seed manifests | Load rules once at installation and let native rules own lifecycle/collapse decisions. |

## Duplication and risk findings

### 1. Duplicate common-ground/reference concepts

`domains/conversation.py` has an older channel-keyed common-ground helper,
`domains/reference_resolution.py` owns a `DiscourseStore` with
`DiscourseReferent`/`CenteringState`, and `domains/discourse_state.py` now creates
`CommonGround` plus a `DiscourseState`. These are related but currently separate
ledgers. The new `world_adapter._set_current_topic()` also creates
`DiscourseReferent` directly, bypassing the reference faculty.

Required direction: select one canonical referent store (the existing
`DiscourseStore`), and make `DiscourseState` point to it and record event-local
common-ground deltas. The state should not mint competing referent identities.

### 2. Duplicate goal minting and missing comprehension binding

`domains.conversation_action._mint_goal()` and other existing faculties mint
`Goal` nodes through `agent -has_goal-> Goal`, while
`domains.discourse_state.open_goal()` defines a second lifecycle-aware goal
constructor. The live action path currently creates goals but does not attach
`Goal -comprehends-> inbound Message`; the audit probe observed two goals for
`Check the pressure.` and neither comprehended the inbound message.

This is why `_bind_live_goals_and_deliberation()` finds no eligible live goal.
The helper's broad exception suppression also hides this failed integration.

Required direction: preserve the existing goal minting owner, add a shared
mechanical goal-binding operation that attaches origin event/message and
addressee, and use `discourse_state` only for lifecycle/state projection. Do not
create a second goal for the same communication event.

### 3. Phase 4 bridge is an evidence transport, not a generator

`domains.conversation_deliberation` correctly leaves valuation, Argmax, rejection,
settlement, and counterfactual credit to native rules. Its
`materialize_from_discourse_state()` and
`materialize_from_live_thought_manifold()` should be invoked only after an
existing goal/manifold has supplied evidence. Creating an empty deliberation
for every communication event would be a trace artifact, not cognition.

### 4. Native APIs already suffice

The Python substrate wrapper already exposes graph writes, seed loading,
attribute updates, scoped/native rule execution, and replay. No new substrate
API or Rust primitive is justified by this audit. The remaining work is binding,
authority consolidation, and evidence measurement.

## Immediate integration order

1. Add a single goal-to-event binding helper at the mechanical faculty boundary;
   apply it to conversation action and existing routed-goal paths.
2. Make the live state bridge record the canonical `Message`/`DiscourseEvent`
   relation and use the existing reference store for referent identity.
3. Replace the current silent catch-all in the live deliberation binder with an
   auditable nonblocking integration error record, while keeping cognition
   fail-closed.
4. Invoke Phase 4 materialization only for goals with evidence-bearing manifold,
   repair, residual, or grounded action evidence. An empty evidence set may
   produce an explicit native `no_candidate` trace only when a real deliberation
   was cognitively warranted.
5. Replay the 74-event corpus and require nonzero, event-justified deliberation
   traces; do not require deliberation on every event.
6. Re-run the native-authority audit and remove any new Python outcome selection
   introduced by the integration.

## Verification evidence

Read-only repository inspection found:

- existing graph/native APIs for node/edge/attribute writes, seed loading, and
  native rule execution;
- existing message, intent, goal, referent, common-ground, thought-manifold,
  residual, production, and native-collapse authorities;
- current production report still has 74/74 cognition traces but zero live
  deliberation traces;
- a live `.venv` probe produced `DiscourseState` and `DiscourseEvent`, but the
  action goals had no `comprehends` edge and no deliberation was bound.

No substrate or conversation source files were changed by this audit. The next
implementation increment is the goal/event binding correction described above.

## Current-state addendum — 2026-09-23

The earlier audit recommendations have since been implemented as bounded
integration increments. A second audit was performed before continuing, using
the current repository rather than introducing another abstraction layer.

### Reusable substrate found

| Remaining need | Existing substrate to integrate | Boundary decision |
|---|---|---|
| Stable referents and centering | `domains.reference_resolution.DiscourseStore`, `DiscourseReferent`, `CenteringState` | Keep this as referent identity authority. `DiscourseState`/`CommonGround` carry event-local lifecycle and participant claims only. |
| Gap recurrence and learning | `SelfConcern`, `GapRecurrence`, `domains.gap_driven_acquisition`, `domains.gap_prioritization`, `domains.gap_learning` seeds | Reuse existing gap identity, recurrence, source-reading, teaching, verification, and graph-prioritized scheduling. Do not create a conversation-only learning ledger. |
| Candidate cognition | `ThoughtManifold`, train-of-thought evidence, `domains.conversation_deliberation`, native Phase 4A rules | The conversation adapter may transport complete evidence only. Native rules own valuation, collapse, rejection, settlement, and counterfactual traces. |
| Production and readback | `LanguageProduction`, audience/production faculties, `ProductionGateReceipt`, parse-back/readback paths | Production remains a release gate over selected cognition; surface text cannot become evidence or select a candidate. |
| Native authority/performance | `Substrate.run_rules`, seed manifests, native cycle/profile measurement, authority audit | Extend existing native workloads and audit bindings. No new Rust API is justified by conversation needs alone. |
| Language-neutral communication | `domains.communication_evidence`, `communication_evidence.v1`, neutral arbitration seed, `LanguageWorld` adapters | Keep language-specific parsing at the adapter edge; cognition consumes force/goal/grounding evidence, not English route heuristics. |

### Duplication audit results

- `DecisionOption`/`ConversationDecisionState` remains a legacy conversational
  decision record. It has learned/grounded/residual values but lacks declared
  `consequence` and `novelty` evidence. It is therefore not an acceptable
  Phase 4A source; the executable boundary test records this as a deliberate
  no-promotion result.
- `DiscourseStore` and `DiscourseState` are complementary only when their
  ownership is kept distinct. Any new referent writer would recreate the
  duplication identified in the original audit.
- Gap acquisition already reuses the reference reader and graph teaching path;
  a new conversation acquisition path would be redundant.
- Gap prioritization already provides graph-resident salience normalization and
  repeated native selection; Python conversation code must not add a second
  priority sort.
- The production gate and native deliberation already provide the needed
  fail-closed boundaries. A fixed conversational acknowledgment is not a valid
  substitute for either one; a failed release must remain an explicit error.

### Remaining missing integration/evidence

1. The live production corpus still lacks complete evidence-bearing manifold
   candidates, so its native deliberation traces are correctly `no_candidate`.
   Adding defaults would be reinvention and would falsify the cognition test.
2. Production recurrence is still unmeasured in the 74-event corpus; its
   event-specific identities do not establish repeated cognitive gaps.
3. The native-authority audit still has unbound Python cognitive branches. The
   next migration work must bind existing substrate rules or classify a branch
   as mechanical I/O; it must not rewrite the same faculty under a new name.
4. External small-LLM, modern-LLM, base-human, and advanced-human baselines are
   unavailable without raw authorized session evidence. Their scorecards must
   remain `unavailable`, not be approximated from ELIZA or the local system.

This addendum is the gate for subsequent implementation: integrate an existing
substrate authority when one exists; add a new mechanism only when this audit
shows a genuine missing capability and its ownership is explicit.

## Verification addendum — 2026-09-24

The audit was rerun against the current workspace before beginning the next
implementation increment.

### Machine-checked results

- The Phase 4 tuple audit found **0** complete seed-record tuples and **0**
  near-match records meeting its two-dimension threshold. The required tuple
  remains `grounding`, `expected_value`, `residual_cost`, `consequence`, and
  `novelty`; no missing dimension was inferred from a neighboring faculty.
- The native-authority audit found **9** explicitly bound native calls and
  **172** unbound Python cognitive cycle/task calls, out of **181** total. The
  unbound calls remain review debt and are not counted as native authority.
- The focused live integration, native-authority, tuple-availability, and
  semantic-audit regressions passed **12 tests** in the local `.venv`.

### Reuse decisions confirmed

1. `DiscourseStore` remains the sole referent-identity owner. `DiscourseState`
   and `CommonGround` may project event-local lifecycle and participant claims,
   but must not mint competing referents.
2. Existing `Goal`/`comprehends`/`originated_in` relations remain the goal
   binding authority. `open_goal`-style lifecycle projection must not mint a
   second goal for the same message.
3. `ThoughtManifold`, train-of-thought, residual, and grounded-relation
   faculties are eligible evidence sources only when they expose the complete
   Phase 4 tuple. `DecisionOption`, salience, information-commitment, and
   adaptive-control records are not promoted by inference.
4. Native Phase 4A rules remain authoritative for valuation, selection,
   rejection, settlement, and counterfactual credit. The adapter only
   transports graph evidence and records provenance.
5. `LanguageProduction`, production/readback gates, gap recurrence, and native
   cycle schedules remain the integration points for later work. No parallel
   conversation learning store, candidate scorer, referent store, or substrate
   API is justified by this audit.

### Audit consequence

The next implementation increment must either expose an already-existing
cognitive faculty's complete Phase 4 tuple through its native graph output, or
remain an explicit `no_candidate`/error trace. Adding defaults, copying values
from near-match records, or improving force labels with surface-language rules
would violate the audit boundary.

## Grounding-source probe — 2026-09-24

The existing graph-native `reading_collapse._event_predication_graph` was
probed as a possible grounding source for the remaining corpus false
negatives. It is not promoted.

- It can emit syntactic event predications for some clauses, but the output
  does not itself establish a held fact, common-ground commitment, or grounded
  world relation.
- It mis-parses several copular, fragment, and interrogative forms in the
  communication corpus; treating those structures as epistemic grounding
  would violate the existing false-positive boundary.
- The safe integration condition is therefore stronger: an event predication
  must be linked to an existing held/common-ground or relation commitment
  before it can affect communication grounding or Phase 4 evidence.

This probe changed no runtime grounding behavior. It narrows the next search to
event-to-commitment graph edges rather than parse structure or lexical presence.

## Current substrate reuse audit — 2026-09-24

The audit was repeated immediately before the next Phase 4 increment. The
machine-readable tuple audit still finds **0** complete seed-record tuples and
**0** near matches. The required tuple remains
`grounding`, `expected_value`, `residual_cost`, `consequence`, and `novelty`.

### Reusable partial authorities

| Existing faculty | Evidence it already owns | Integration boundary |
|---|---|---|
| `domains.self_dialogue` | held graph frame, graph path, recovered concepts, residual concepts | May supply held-relation/path grounding evidence after an explicit commitment edge; it must not manufacture value, cost, consequence, or novelty. |
| `domains.audience` / `audience_driven_production` | recipient-relative known/new concept distinction and residual-to-audience | May supply novelty about an observed recipient model; it is not world grounding or candidate selection. |
| `domains.global_workspace` | graph-native salience quanta, focus proximity, tube deviation, native broadcast threshold | May prioritize already-valid cognitive items; salience is not expected value and must not be renamed into it. |
| `domains.future_option_risk` / `information_commitment` | future-manifold residual, escape, information loss, and safety veto | Reusable for future/action risk only when a real projection exists; it is not a conversational candidate tuple. |
| `domains.gap_prioritiser` and gap-learning stack | unresolved-gap priority, recurrence, verification, and learning lifecycle | Reusable for unresolved cognition and recurrence; it must not become a second conversation candidate scorer. |
| native Phase 4A | complete-tuple valuation, collapse, rejection, settlement, counterfactual credit | Remains the sole deliberative authority once an approved faculty supplies all tuple dimensions. |

### Findings and plan adjustment

1. No existing faculty currently exposes all five Phase 4 dimensions for live
   communication events. The live bridge must therefore remain fail-closed with
   native `no_candidate` or an explicit integration diagnostic.
2. The next valid increment is a **partial-evidence integration audit and
   typed provenance projection**, not a new scorer: expose which of the above
   faculties supplied which dimensions, and promote only when an existing
   commitment/verified relation completes the tuple.
3. `communicate.choose`, `moral_risk.choose`, `broadcast_winner`, and
   `information_commitment.assess` are not interchangeable selectors. Their
   outputs must not be copied into Phase 4 fields or used to bypass native
   Phase 4A collapse.
4. No new referent store, goal store, salience implementation, residual ledger,
   language parser, or surface fallback is justified by this audit.

This audit changes no runtime behavior. It updates the implementation order so
the next Phase 4 work measures and binds existing partial evidence before any
candidate promotion is attempted.

## Pre-continuation audit — 2026-09-24

This audit was repeated before the next implementation increment to detect
reinvention and stale recommendations. It inspected the current source,
tests, reports, and the execution/progress trackers.

### Existing authorities to reuse

| Cognitive responsibility | Existing authority | Audit decision |
|---|---|---|
| Referent identity and centering | `domains.reference_resolution.DiscourseStore`, `DiscourseReferent`, `CenteringState` | Sole referent owner; do not add a conversation-local referent table. |
| Event-local dialogue lifecycle | `domains.discourse_state` (`DiscourseState`, `CommonGround`, `DiscourseEvent`) | Reuse for lifecycle and participant projection; it does not establish world truth by itself. |
| Goal ownership and source binding | existing `Goal` graph plus `conversation_action._bind_goal_to_inbound()` | Reuse the existing idempotent binding seam. The earlier audit instruction to add a new helper is stale and is retired. |
| Candidate deliberation | `ThoughtManifold`, `conversation_deliberation`, native Phase 4A rules | Transport only complete evidence tuples; native rules own valuation, collapse, rejection, and settlement. |
| Learning and gap recurrence | `SelfConcern`, `GapRecurrence`, `gap_prioritization`, `gap_learning` | Reuse existing graph learning; no conversation-specific acquisition ledger. |
| Surface release | `LanguageProduction`, `conceptualizer`, `production_gate`, parse-back/readback | Keep cognition and release separate; failed release remains an explicit error. |
| Scheduling and authority | native cycle scheduler, `Substrate.run_rules`, native-authority audit | Do not add Python-side decision logic or another scheduler. |

### Duplication/stale-recommendation findings

1. The current tree already contains the goal-to-inbound binding operation and
   regression tests. Recreating it in `discourse_state` would produce duplicate
   goals and split ownership.
2. `DecisionOption`/`ConversationDecisionState` is not a substitute for the
   Phase 4A evidence tuple. Its values lack complete `consequence` and
   `novelty` evidence; promotion would be inference, not integration.
3. `reading_collapse` and `situation_model_reader` produce useful event
   structures, but neither is an epistemic commitment authority. Parse or
   predication structure must not be promoted to grounding without a relation
   to an existing held fact, common-ground commitment, or verified receipt.
4. Existing production, gap-learning, reference, and native-collapse paths are
   already distinct authorities. The next work must bind them, not create
   conversation duplicates with similar names.

### Corrected next seam

The only currently justified implementation target is a mechanical
event-to-commitment projection that consumes an already-supported relation or
common-ground commitment and exposes its provenance to communication grounding
and/or Phase 4 evidence. If no such commitment is present, the correct result
remains `no_candidate`, repair, or the explicit diagnostic error. No default
values, lexical Concept promotion, parse-only grounding, or fixed conversational
acknowledgment is permitted.

### Audit result

No new substrate API, referent store, conversation learner, candidate scorer, or
language-specific cognition layer is justified. The plan should be adjusted to
mark the existing binding seam as integrated and to make the event-to-commitment
condition an explicit gate before any further recall or deliberation work.

## Independent audit consolidation — 2026-09-24

Five read-only audits were reconciled against the source and the local `.venv`
verification run. They confirm the following additional boundaries.

### Existing overlap that must be consolidated, not duplicated

- The older `domains.conversation` speech-act/common-ground model overlaps the
  newer `communication_evidence.v1`/`CommunicationInterpretation` path. The
  latter remains the live event-level authority; the former is a theory and
  compatibility source unless explicitly adapted.
- `question_driver` has a separate goal/pump vocabulary. It must either emit
  the canonical communication/discourse goal records or remain explicitly
  isolated; it must not silently create a second conversational deliberation
  lifecycle.
- `DiscourseStore`, `CurrentTopic`/`DiscourseReferent`, `DiscourseState`,
  `context_model`, and `interlocutor_model` overlap in state vocabulary. Keep
  referent identity in `DiscourseStore`; use discourse state for event
  lifecycle; make any other state an adapter/projection.
- `gap_prioritization` and `gap_prioritiser` are different granularities, not a
  license for another scheduler: capability-frontier selection produces or
  classifies gaps, while salience prioritization schedules them.

### Genuine missing cognition seam

The existing substrate does not yet own this complete lifecycle:

```text
neutral semantic evidence
  -> grounded structured proposition
  -> speaker/addressee attribution
  -> evidence and epistemic status
  -> common-ground uptake, challenge, suspension, or retraction
  -> situation-model consequence
```

Action authorization and information-commitment gates are not substitutes for
epistemic proposition commitment. This is the justified next cognition
capability, provided it reuses existing `DiscourseStore`, `DiscourseState`,
grounding reach, situation-model, and native rule authorities.

### Language and event-mode boundary

`communication_evidence.v1`, `LanguageWorld`, acoustic/sign mechanisms, and
native arbitration are reusable, but the canonical live text path still enters
through English-shaped `comprehend_text` helpers and defaults to a statement.
English cue handling, referring-expression detection, and production templates
must be explicit adapter code. The cognition boundary must accept neutral
semantic/semiotic evidence and optional event metadata before text parsing.

The live architecture must also separate event processing from reply
production. `responds_to`, `_last_message`, `_finish_turn_reply`, and the
`utterance = converse` alias are useful compatibility mechanisms, but they must
not make cognition inherently one-in/one-out or turn-bound. Non-turn events may
update state, open/transition goals, defer, or produce no surface output.

### Implemented first seam — 2026-09-24

The smallest safe ingress was implemented as
`WorldAdapter.ingest_semantic_event(...)`. It reuses `communication_evidence`,
`DiscourseState`, `CommunicationInterpretation`, and `DiscourseEvent` without
creating a text `Message` or reply. Explicit neutral proposition payloads are
then passed to `domains.proposition_commitment`, which records provenance and
attribution but does not grant common-ground uptake. Unknown force and
surface/parse-only proposition evidence fail explicitly.

This closes transport, not epistemic commitment. The remaining subphase is
native proposition uptake/challenge/suspension/retraction and situation-model
consequence integration, with corpus evidence before grounding recall changes.

### Verification result

Using the repository `.venv`, the existing binding, bridge, grounding,
deliberation-authority, and semantic-reference suites passed **39 tests in
12:31**. This verifies reuse boundaries; it does not establish full corpus
correctness. Current known gates remain: grounding precision **1.00**, recall
**0.46**, F1 **0.630**; Phase 4 complete evidence tuples **0**; native
authority audit **9 bound / 173 unbound** across **182** calls; human and
adjudicated external baselines unavailable. A current full 74-event replay was
not generated by this audit.

## Current audit refresh — 2026-09-24

The audit was rerun after the proposition/event overlays, Phase 4 boundary,
receipt-semantics correction, and neutral semantic-event envelope increment.

- The existing tuple audit still reports **0 exact** and **0 near-match**
  Phase 4 seed records. No partial faculty was promoted into deliberation.
- The native-authority audit reports **9 explicitly bound**, **173 unbound**,
  **182 total** Python cycle/task calls. The increase from the earlier 172 is
  a current-tree audit count, not a new authority claim.
- The combined Phase 4 tuple/boundary/native-authority regression battery is
  green: **24 tests passed in 201.03s** using the repository `.venv`.
- The current reuse decision is unchanged: `DiscourseStore` owns referent
  identity, `DiscourseState` owns event lifecycle, native Phase 4A owns
  candidate outcomes, and production gates own release. The remaining work is
  to expose existing cognitive evidence or preserve `no_candidate`; it is not
  to add a parallel scorer, scheduler, referent store, or wording fallback.
