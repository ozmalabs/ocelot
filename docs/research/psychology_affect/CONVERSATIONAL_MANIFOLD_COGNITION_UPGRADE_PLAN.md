# Conversational Manifold Cognition Upgrade Plan

**Document path:** `docs/research/psychology_affect/CONVERSATIONAL_MANIFOLD_COGNITION_UPGRADE_PLAN.md`  
**Companion tracker:** [`CONVERSATIONAL_MANIFOLD_COGNITION_UPGRADE_TRACKER.md`](CONVERSATIONAL_MANIFOLD_COGNITION_UPGRADE_TRACKER.md)  
**Status:** Proposed next-generation cognition plan  
**Scope:** Comprehension, discourse state, grounding, goal formation, deliberation, action/repair selection, learning, and substrate-native verification.

## 1. Purpose

The current conversational manifold is no longer primarily blocked by surface generation. The live loop can now process turn-compatible utterance events, produce grounded self-reports, describe an attached scene, ask for clarification, route instructions to held faculties, monitor output-null candidates, and expose an explicit error when cognition cannot produce a response.

The next upgrade is therefore a cognition program. It must improve what the agent understands, believes, remembers, chooses, and learns from a communication event. It must not disguise those limitations with acknowledgements, canned empathy, punctuation changes, or richer prose.

### Interaction model

The cognitive primitive is a **communication event**, not a turn. An event may be a complete utterance, partial stream, overlap, interruption, asynchronous message, environmental signal, internally generated thought, or unsolicited agent action. Turn-taking is a coordination policy layered over events and remains a supported mode for compatibility with the current text API. No cognitive state may require an alternating speaker schedule.

## 2. Review-derived starting point

### 2.1 What is working

- Native Rust cognitive-cycle tests pass in the repository virtual environment.
- The live action/repair bridge passes the conversation-loop gates: self-report goals, attached-scene description, clarification repair, and behavioural discrimination.
- Five-turn non-question continuity and `converse`/`utterance` parity are covered.
- The system records decision-state values and settle-back experience.
- Grounded production has audience selection, grammar realization, output-null monitoring, and bounded repair.
- Runtime LLM use remains disabled (`donkey=0`).
- Exact `noted` and generic non-social acknowledgement fallbacks are forbidden. Failed generation is observable as `ERROR: no communicative response could be generated.`

### 2.2 Current cognitive deficits

These are cognition failures, not conversation-surface failures:

1. **Intent competition:** speech-act classification, comprehension kind, instruction parsing, topic routing, and repair routing can disagree or pre-empt one another.
2. **Grounding contamination:** an unanswerable topic can be routed to an unrelated held/search answer instead of remaining unresolved.
3. **Discourse-state weakness:** assertions, questions, answers, corrections, commitments, and expected responses are not yet represented as one auditable dialogue state machine.
4. **Goal lifecycle gaps:** some goals are minted and spoken but do not consistently progress through proposed, executing, resolved, blocked, or learned-from-failure states.
5. **Deliberation coverage:** the thought manifold and decision collapse are present, but live candidate generation and credit assignment remain partial and legacy-path dependent.
6. **Audience-state instability:** audience design does not always change delivery when common ground differs, indicating incomplete cognitive use of interlocutor state.
7. **Self-monitoring coverage:** parse-back and semantic recoverability are not yet gated across every live production path.
8. **Learning-loop incompleteness:** gap filing exists, but gap identity, recurrence, prioritisation, promotion, resolution, and regression evidence need one closed loop.
9. **Measurement gaps:** latency, memory, graph residence, semantic recoverability, and baseline comparisons are not yet measured as a repeatable battery.

## 3. Baseline comparison

This is a capability model, not a claim that the system is generally equivalent to any baseline. Each baseline names the capability floor to beat and the dimension that matters.

| Baseline | Typical strength | Current system relative position | Upgrade implication |
|---|---|---|---|
| **ELIZA floor** | Surface pattern matching and local acknowledgement | Above it on graph state, self-report, explicit uncertainty, goal evidence, and no-LLM operation; still vulnerable to routing dead ends | Preserve explicit internal evidence and prevent generic acknowledgement collapse |
| **Small LLM** | Broad fluent completion, shallow topical association | Stronger on inspectable graph residence, deterministic grounding boundaries, and teacher-free self-state; weaker on breadth, flexible intent resolution, and coherent multi-turn world modelling | Improve cognitive breadth through graph learning and retrieval, not canned prose |
| **Modern LLM** | Broad knowledge, flexible dialogue, strong surface adaptation | Weaker on coverage, speed-to-capability, and general pragmatic robustness; stronger on provenance, zero hallucination policy, inspectable decisions, and substrate-native learning constraints | Add structured grounding, discourse memory, and deliberative candidate competition while retaining provenance |
| **Base human** | Everyday turn-taking, repair, common-ground tracking, practical action selection | Approaches selected narrow tasks; below human robustness in ambiguity, reference, topic continuity, error recovery, and implicit context | Build a persistent discourse model and evaluate task families, not isolated replies |
| **Advanced human** | Metacognition, abstraction, analogical transfer, audience adaptation, calibrated uncertainty | Far below this baseline outside narrow introspection/graph tasks | Prioritise abstraction, counterfactual reasoning, self-correction, and learning transfer after core grounding is reliable |

The comparison must be re-run with fixed tasks and scored dimensions: intent accuracy, grounding precision, repair appropriateness, goal completion, semantic recoverability, discourse continuity, calibration, provenance, and resource cost.

## 4. Cognitive and communication-science grounding

The system must not treat an engineering label as a cognitive explanation. Each
implementation claim requires a construct, an observable representation, a
decision consequence, and a falsifiable test. These foundations are design
commitments, not claims that the current implementation has matched human
performance.

| Scientific construct | Relevant tradition | Operational representation | Falsifiable prediction |
|---|---|---|---|
| Communicative force is not identical to grammatical mood | Speech-act theory; indirect-request research | Separate `literal_mood`, `communicative_force`, `goal_kind`, and `addressee_effect` in `CommunicationInterpretation` | “Tell me about X”, “Can you tell me about X?”, and “Please tell me about X” may share an information-seeking goal while retaining different literal forms |
| Joint grounding / common ground | Clark’s collaborative grounding model | Graph deltas for `shared`, `new_to_addressee`, `presupposed`, `unresolved`, and `repair_needed` | The same content is encoded differently when addressee knowledge changes, while semantic content remains stable |
| Conversation repair is an interactional operation | Conversation analysis; other-initiated repair | `RepairRequest` linked to trouble-source event, repair type, and expected resolution event | An ungrounded item triggers clarification or defer, not an answer fabricated from unrelated content |
| Informativeness is audience-relative | Gricean quantity/relevance; audience design | Candidate costs and listener-recovery evidence in the conceptualizer/production trace | A more explicit candidate is selected when the audience lacks the concept; a shorter candidate is selected when common ground is verified |
| Production is staged and monitored | Levelt speaker model; self-monitoring research | `CommunicativeGoal -> MessageShape -> ClausePlan -> Committed`, with parse-back/efference copy | Unsupported candidates are withheld or repaired before release |
| Internal speech is condensed relative to overt speech | Vygotsky; contemporary inner-speech work | Intermediate manifold paths store relations/goals, not overt clauses | Deep reasoning can traverse several graph relations without generating intermediate surface text |
| Dialogue is temporally interactive, not inherently alternating | Interactive alignment and event-based communication models | `CommunicationEvent` with `interaction_mode`, event order, overlap/partial status, and optional turn boundary | Interpretation remains valid for stream fragments, interruptions, asynchronous events, and unsolicited signals without requiring a speaker swap |

### 4.1 Phase 1 annotation contract

Each corpus event must be annotated on independent axes:

1. **Literal form:** grammatical mood/syntax as perceived from the signal.
2. **Communicative force:** request-information, request-action, assertion, correction, acknowledgement, offer, repair, refusal, or other held force.
3. **Cognitive goal:** answer, act, clarify, update-belief, establish-common-ground, learn, defer, or error.
4. **Grounding status:** grounded, partially grounded, unknown, contradicted, unavailable-world, or unresolved-reference.
5. **Interaction relation:** standalone event, continuation, overlap, interruption, response, or turn-compatible event.
6. **Evidence:** graph path, lexical/syntactic cue, discourse state, addressee model, or explicit uncertainty.

The first four axes must not be inferred from one another by naming convention.
A grammatical imperative may have the force of an information request, while a
declarative may be a correction or report rather than a question.

### 4.2 Adjudicating current disagreement classes

The current corpus buckets are provisional measurements, not validated cognitive
categories. Each example must be reclassified as one of:

- **Indirect information request:** directive/report form whose force is to obtain information.
- **Direct action request:** force is to cause an external or internal action.
- **Assertion/report:** force is to update common ground, file a gap, or correct a belief.
- **Parser/classifier error:** signal and discourse evidence do not support the selected interpretation.
- **Compound event:** one signal contains multiple candidate events that must be segmented first.

This prevents `question_promoted_from_statement` from becoming one catch-all:
“Name one of your rules” may be an indirect information request, while “There is
a gap in your reasoning” is more likely an assertion/report or parser error.

## 5. Non-negotiable architecture rules

- Cognition decides; the adapter transports data and performs bounded I/O.
- The cognition layer is language-agnostic. Language-specific perception,
  segmentation, morphology, syntax, prosody, and politeness interpretation are
  evidence providers, not the ontology of thought or the arbitration policy.
- No cognitive decision may depend directly on English word lists, English word
  order, English POS labels, or English punctuation. Language adapters must
  translate those observations into substrate-level evidence such as event
  roles, dependency relations, deixis, social stance, evidentiality, force
  hypotheses, and grounding confidence.
- Every language adapter must express uncertainty and partial interpretation.
  Missing language coverage produces an explicit evidence gap, never a silent
  English-shaped statement/action fallback.
- Every selected response must have a graph-resident communicative goal, evidence path, or explicit unresolved/error state.
- Unknown, contradictory, and unperformable inputs must remain distinct states.
- No unrelated search result may satisfy an unresolved topic without an evidence path linking it to the requested referent.
- `noted`, generic acknowledgements, and surface empathy are never failure handling.
- No LLM inference occurs during runtime tests or live communication events.
- Event interpretation must remain valid when no turn boundary exists; `turn_compatible` is an interaction mode, not the ontology.
- Intermediate thought remains semantic/graph-native; only the collapsed candidate is realized overtly.
- Every phase adds a falsifiable test and preserves the existing zero-LLM and explicit-error invariants.

## 6. Phased implementation plan

### Architecture integration gate — before further Phase 4 expansion

Before extending live deliberation, audit every proposed conversation faculty
against existing substrate authorities. Reuse `Message`, `Intent`, `Goal`, the
canonical reference store, `ThoughtManifold`/workspace competition, residual
learning, production gates, and native cycle APIs. A new node or writer is
permitted only when it represents a genuinely missing cognitive state and has a
non-overlapping owner. In particular, bind existing goals to their originating
communication event before attempting live candidate materialization, and do not
create a deliberation merely to make a trace appear. The audit and required
integration corrections are recorded in
`CONVERSATIONAL_MANIFOLD_SUBSTRATE_INTEGRATION_AUDIT_20260923.md`.

### Phase 0 — Evaluation contract and failure taxonomy

**Goal:** Make the review repeatable before changing cognition.

**Implement:**

- Create a fixed communication-manifold evaluation corpus covering statements, questions, instructions, corrections, references, topic shifts, unknowns, contradictions, social acts, partial/overlapping events, asynchronous events, and turn-compatible sequences.
- Label expected cognitive state, not just expected text: `answer`, `act`, `repair`, `defer`, `learn`, `blocked`, or `error`.
- Add structured trace assertions for decision state, goal lifecycle, grounding evidence, reply provenance, and `donkey=0`.
- Record baseline results for the five comparison classes without treating fluent text as correctness.

**Exit:** Repeated runs produce stable per-dimension scores and classify every failure without relying on string snapshots alone.

### Phase 1 — Canonical comprehension and intent arbitration

**Goal:** Produce one authoritative, graph-resident interpretation per communication event.

**Implement:**

- Unify speech-act, grammatical kind, communicative force, predicate/object structure, and uncertainty into a `CommunicationInterpretation` record. A turn-compatible utterance is represented as an event with `interaction_mode="turn_compatible"`.
- Record literal-form evidence separately from hypotheses about communicative force, cognitive goal, grounding status, and interaction relation; the evidence source must remain inspectable.
- Apply force/goal arbitration through graph-resident rules (`seeds/communication_intent_arbitration.json`), including an explicit exception for declarative native evidence overriding an erroneous table promotion.
- Add explicit precedence and conflict evidence when native classification and Python front-end interpretation diverge.
- Separate instruction, assertion, question, answer, correction, and social act before faculty dispatch.
- Ensure an instruction cannot be silently converted into topic lookup or a generic acknowledgement, whether it arrives as a complete utterance or a stream segment later completed by subsequent events.

**Exit:** The fixed corpus has independent science-grounded labels for literal form, force, goal, grounding, and interaction relation; every disagreement has a recorded reason and deterministic fallback state; arbitration reaches at least 95% agreement with adjudicated force/goal labels. Agreement with another classifier alone is insufficient.

**Language-agnostic gate:** The canonical interpretation must consume a
language-neutral evidence schema. English-specific cues may remain inside an
English adapter, but must not appear in the graph arbitration ontology or be
required by cognition tests. At least one non-English or language-neutral event
representation is required before Phase 1 acceptance.

### Phase 2 — Grounding, reference, and epistemic state

**Goal:** Prevent unrelated knowledge from answering an unresolved request.

**Implement:**

- Represent each candidate referent with provenance, confidence band, source, and relation path.
- Require an evidence path from requested concept to answer content before `resolved` is allowed.
- Distinguish unknown, not-attached-to-world, ungrounded-in-current-context, contradicted, and search-failed.
- Make search and retrieval return candidates to cognition; they must not directly claim the turn.
- Add reference/coreference tracking for current topic, prior goal, speaker, addressee, and scene.

**Exit:** Unknown-topic tests never return unrelated content; contradiction and no-world tests remain distinct; every resolved answer exposes an evidence path.

### Phase 3 — Discourse state and goal lifecycle

**Goal:** Give the agent persistent, inspectable conversation state.

**Implement:**

- Add a graph-resident `DiscourseState` with current topic, active frame, open repair, pending expectation, common ground delta, commitments, and unresolved residuals.
- Link every `Goal` to its originating turn, addressee, evidence, outcome, and next action.
- Implement lifecycle transitions: `proposed -> selected -> executing -> resolved|blocked|repaired|abandoned`.
- Track adjacency obligations without forcing a reply when the correct state is defer or error.

**Exit:** Ten-turn mixed-act dialogues preserve topic/goal identity, close obligations correctly, and expose no orphaned active goals.

### Phase 4 — Deliberative candidate generation and cognitive arbitration

**Goal:** Make the thought manifold select among grounded cognitive actions.

**Implement:**

- Generate candidates from discourse state, grounded relations, active goals, residual stance, repair need, and available faculties.
- Route candidate valuation through the native decision-collapse path.
- Record rejected candidates and counterfactual credit, not only the winner.
- Use deep thought only when residual, contradiction, novelty, or consequence warrants it; keep the shallow path observable.
- Add bounded search and an explicit `no_candidate` state.

**Exit:** Deliberative traces show candidate generation, valuation, selection, rejection, and settle-back; repeated tasks reduce residual without reducing grounding quality.

### Phase 5 — Learning, gap closure, and self-correction

**Goal:** Convert failures into useful, bounded cognitive improvement.

**Implement:**

- Canonicalise gap identity by kind, referent, evidence deficit, and originating turn.
- Prioritise gaps by recurrence, impact, confidence, and available repair path.
- Connect `SelfConcern` to promotion, attempted resolution, verification, and retirement.
- Add correction handling that revises level-2 models without rewriting the original asserted record.
- Add regression tests proving a repaired gap changes future cognition and does not create duplicate concerns.

**Exit:** A repeated failure produces one stable concern, a reviewed repair changes the correct route, and failed repairs remain visible rather than being marked resolved.

### Phase 6 — Production as a cognitively gated release

**Goal:** Ensure language production expresses a selected meaning and cannot conceal an unresolved one.

**Implement:**

- Require each overt utterance to reference a selected communicative goal and semantic content.
- Run audience design from graph-resident common ground and verify that changed audience state can change the selected encoding.
- Apply grammar realization and parse-back to every substantive live path, including legacy readbacks.
- Store efference copy: expected interpretation, conveyed concepts, and expected next-state.
- On monitor failure, perform one bounded repair; otherwise emit explicit diagnostic failure.

**Exit:** 100% semantic recoverability on the fixed production corpus, with no ungrounded content or forbidden fallback surfaces.

### Phase 7 — Native substrate integration and performance envelope

**Goal:** Move remaining cognitive decisions into the Rust substrate and measure real constraints.

**Implement:**

- Migrate remaining turn arbitration, discourse-state updates, and candidate collapse from adapter-side decisions into graph rules/native cycle execution.
- Verify graph residence and replay determinism.
- Measure fast/deep latency, RSS, rule-pass counts, graph growth, and recovery cost under bounded corpus loads.
- Add stress tests for long dialogues, high ambiguity, repeated gaps, and dense graph neighborhoods.

**Exit:** Native trace is authoritative, resource budgets are measured, and no Python branch selects a cognitive outcome outside the documented I/O boundary.

### Phase 8 — Comparative capability evaluation and release gate

**Goal:** Compare the upgraded system against the baseline classes and decide what remains.

**Implement:**

- Run the fixed corpus against ELIZA floor, small LLM, modern LLM, base-human, and advanced-human reference protocols.
- Score cognition separately from wording: interpretation, grounding, action, repair, memory, learning, calibration, provenance, and cost.
- Publish failure slices and confidence intervals where repeated trials are available.
- Update the main conversational manifold plan only from measured evidence.

**Exit:** A dated report identifies capabilities above/below each baseline and selects the next cognitive bottleneck.

## 7. Definition of done

The system is not considered upgraded because it sounds more natural. It is upgraded when it can, with graph evidence:

1. identify what kind of communication event occurred;
2. maintain the relevant discourse and goal state;
3. distinguish known, unknown, unsupported, contradictory, and unperformable;
4. select an appropriate cognitive action or repair;
5. produce only a monitored expression of that selected meaning;
6. learn from a verified correction or retain the failure honestly; and
7. demonstrate those properties under repeatable tests and resource measurements.
