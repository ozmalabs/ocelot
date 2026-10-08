# Accepted proposition polar-answer v1 preregistration

Date: 2026-10-03  
Runner: [`accepted_proposition_polar_answer_v1.py`](../../../evaluation/substrate_capability/accepted_proposition_polar_answer_v1.py)  
Lock: [`accepted_proposition_polar_answer_v1_lock_20261003.json`](../../../evaluation/substrate_capability/accepted_proposition_polar_answer_v1_lock_20261003.json)

## Question

Does the existing native communication-arbitration rule set select a sourced `PolarAnswerPlan` from an exact matching structured proposition, preserve polarity, and refuse status/evidence/predicate mismatches?

## Design

For each of seven controlled graph conditions, create a fresh `WorldAdapter(seeds=())`, load only the `communication_intent_arbitration` seed manifest, and explicitly write one query Message, `CommunicationInterpretation`, answer-topic Goal, and proposition graph. The query asks whether `gate` is `open`. Vary proposition commitment status, proposition polarity, question polarity, predicate, and evidence presence. Run native graph rules once and record plan, support, rule firings, and links from support to the exact proposition and evidence. Three graph instances per condition; the runner checks input/source hashes before and after.

## Conditions and exact oracle

- `accepted_affirmative`: accepted `open(gate)`, affirmed question -> exactly one `yes` plan.
- `accepted_negated_claim`: accepted `not open(gate)`, affirmed question -> exactly one `no` plan.
- `accepted_negated_question`: accepted `open(gate)`, negated question -> exactly one `no` plan.
- `proposed`, `suspended`, predicate mismatch (`closed(gate)`), and missing evidence -> zero plan.

Every positive plan must have exactly one support record linked to the proposition and its evidence. Negative controls must not produce a plan. Report if accepted status is supplied without `uptake_applied`; this panel is designed to expose that trust boundary.

## Scope

This is a native-rule graph-interface assay. The harness supplies the parse, query relation, and commitment status. It does not measure text comprehension, whether lifecycle uptake caused accepted status, source authentication, multi-claim conflict resolution, wh-question retrieval, episodic memory, or reply rendering. The existing live-route test fixture is separate evidence that one named polar route reaches a user-facing answer.
