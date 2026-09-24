# Phase 1 Intent Arbitration Measurement

**Source:** `tests/fixtures/comprehension_divergence/divergence.json`  
**Measurement code:** `evaluation/conversation_intent_arbitration.py`  
**Adjudication fixture:** `tests/fixtures/comprehension_divergence/phase1_adjudications.json`  
**Policy:** Evidence only; this report does not promote either classifier as the winner. The disagreement buckets below are engineering measurements, not validated cognitive categories.

## Results

| Measure | Result |
|---|---:|
| Non-empty corpus rows | 160 |
| Kind agreement | 150 / 160 = **93.8%** |
| Kind disagreement | 10 |
| Predicate disagreement | 107 |
| Topic disagreement | 96 |

## Kind disagreement classes

| Class | Count | Interpretation |
|---|---:|---|
| `question_promoted_from_instruction` | 3 | Information requests expressed with imperative/reporting forms |
| `question_promoted_from_statement` | 5 | Meta/information requests or ambiguous declaratives promoted by comprehension |
| `instruction_promoted_from_statement` | 2 | Imperative-like forms not recognised by the shadow classifier |

## Examples requiring cognitive policy

- `Tell me about the rule hop_descend_gradient.` — comprehension: question; shadow: instruction.
- `Name one of your rules.` — comprehension: question; shadow: statement.
- `look left then quorplezap the door` — comprehension: instruction; shadow: statement.
- `Please describe your architecture.` — comprehension: instruction; shadow: statement.
- `There is a gap in your reasoning.` — comprehension: question; shadow: statement.

## Finding

The measured 93.8% kind agreement is below the Phase 1 acceptance target of 95%. The disagreement set must be classified against independent labels for literal form, communicative force, cognitive goal, grounding status, and interaction relation before Phase 1 can be accepted. The three current classes are not yet validated cognitive categories.

Predicate and topic disagreement are much larger and are tracked separately. They must not be hidden inside speech-act arbitration; they indicate later parsing, reference, and grounding work.

## Next Phase 1 action

Add explicit literal-form, communicative-force, cognitive-goal, grounding, and interaction evidence to `CommunicationInterpretation` for each disagreement example. Then test a graph-resident arbitration rule that chooses based on force, discourse state, addressee model, and available faculty—not on a surface preference for question or instruction.

## Adjudication increment

The 20-event fixture has independent labels for literal form, force, goal,
grounding, interaction relation, adjudication class, and evidence. The initial
ten disagreement labels split the former buckets into eight indirect
information requests, one compound event, and one assertion/report. The
expanded labels add direct action/information requests, ordinary assertions,
an unresolved action request, and a social act.

The important distinction is that eight events share an information-seeking
force across different literal forms, while “There is a gap in your reasoning.”
is treated as an assertion/correction rather than promoted to a question. The
compound imperative is treated as requiring segmentation before action or repair
selection.

## Expanded adjudication and route measurement

The adjudication fixture now contains **20** independently labelled events,
including direct and indirect information requests, direct action requests,
ordinary assertions, unresolved action requests, and a social act. The graph
policy matched the adjudicated communicative force and cognitive goal for
**20/20 events (100.0%)**. False action, false answer, and false repair routes
were all **0**.

The previous false route, `Please open the north gate.`, is now resolved by
canonical action evidence: after politeness stripping, the held verb-head
faculty recognizes `open` as an imperative head even though its primary POS
reading is adjective. This evidence changes cognition-level arbitration; no
surface response workaround was added. The same canonical layer now preserves
recognized account/enumeration force when the local POS lattice fragments a
leading word such as `List`.
