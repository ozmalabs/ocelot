# Proposition recall bridge contract

Date: 2026-10-03  
Status: design contract for a future implementation and benchmark; no runtime behavior is claimed here.

## Existing partial capability and design decision

There is already a **narrow proposition-to-answer route**. `seeds/communication_intent_arbitration.json` can match an accepted, explicitly evidenced proposition to a selected polar relation and mint `PolarAnswerPlan` support; separate rules select affirmative or negative plans from proposition polarity. The live test `test_live_named_polar_question_releases_accepted_unary_answer` checks “Is the gate open?” and a negative-polarity follow-up. A source-locked minimal graph panel passes 21/21: 9 exact accepted proposition/polarity matches create one support-linked plan, while 12 proposed, suspended, predicate-mismatch, or missing-evidence controls create none. A follow-up conflict panel exposes a serious boundary: two contradictory accepted claims both receive support, then the graph emits `yes` in all six insertion-order conditions instead of abstaining ([conflict protocol](SUBSTRATE_ACCEPTED_PROPOSITION_POLAR_CONFLICT_V1_PREREG_20261003.md), [results](SUBSTRATE_ACCEPTED_PROPOSITION_POLAR_CONFLICT_V1_RESULTS_20261003.md)). The current route therefore works for unique exact matches but is not safe under contradictory evidence. It does not create episodic-memory events or general wh-question recall requests.

Treat communicated propositions as **attributed claims**, not observed episodic events. The existing proposition graph already preserves predicate, role-labelled arguments, polarity, evidence provider/ID, commitment status, and source `DiscourseEvent`. The episodic binder is stricter: it binds only an explicit event/context/schema with `observation_status=observed` and `provenance_kind=perceived|grounded`. Widening that binder by relabelling accepted speech as observed would violate its current rule guard.

Therefore, the preferred direction is to extend the existing proposition-to-polar-answer mechanism into bounded proposition recall over `Proposition` / `PropositionEvidence`, reusing its source-support pattern and adding non-polar query targets. A query adapter supplies a neutral predicate/argument cue; native graph rules select an eligible proposition candidate or emit explicit insufficiency/conflict. The reply layer reports the claim with attribution (for example, “You told me …”), preserving that uptake status is not proof of world truth. Episodic memory remains the route for directly perceived/grounded observations and event sequences.

Two source-level trust gaps must be closed or scoped explicitly. The polar rules check `commitment_status=accepted` and evidence-node presence but do not require `uptake_applied=accept`; the live test directly supplies accepted status. The panel also shows that neither `Proposition.originated_in` nor speaker attribution is required by the current support rules. Thus, the current route demonstrates accepted-status gating plus a support edge to the evidence node, not that native uptake caused acceptance or that claim lineage is authenticated. A generalized recall route should either require lifecycle-applied uptake and source-event attribution, or explicitly bind accepted status to a trusted, provenance-audited producer and test that boundary.

## Admission and lineage invariants

An eligible positive recall candidate must:

1. Point to one existing `Proposition` whose `commitment_status=accepted` and `uptake_applied=accept`.
2. Preserve the original `PropositionEvidence` and source `DiscourseEvent` links. If a speaker handle was resolved, retain it; do not infer an identity from text or provider name.
3. Preserve predicate, argument roles/values, and polarity exactly. Affirmed and negated propositions remain distinct; do not normalize a negated claim into a positive fact.
4. Carry `provenance_kind=recalled_claim` (or another explicit claim-recall label) and `observation_status=not_observed`. Retrieval must not create an `EpisodicEvent`, set `observation_status=observed`, or trigger situation projection as a side effect.
5. Require an explicit neutral query target. Parsing a question to `dispatch=table/know` alone is not a retrieval request.

Eligibility should fail closed for `proposed`, `challenged`, `suspended`, `retracted`, `rejected`, `uncommitted`, unsupported, or ambiguous inputs. A retracted or challenged claim may remain inspectable as history but cannot be returned as the current positive answer. Multiple contradictory accepted propositions must produce a conflict/clarification outcome or an explicitly uncertain bounded candidate set; never overwrite the older evidence silently. The measured polar route currently violates this requirement by answering `yes` when both affirmed and negated versions are accepted. Missing attribution must be reported as unknown source, not filled from a default.

## Suggested graph contract

These names are provisional until design review; a first implementation could use equivalent schemas:

- `PropositionRecallRequest`: neutral `predicate`, role-labelled cue arguments, `status=pending`, request ID, and query-event link.
- `PropositionRecallCandidate`: link to exactly one source `Proposition`, plus source `PropositionEvidence`/`DiscourseEvent`, returned polarity, uncertainty, and `observation_status=not_observed`.
- `PropositionRecallOutcome`: explicit `insufficient_information`, `conflict`, or `unsupported_query` outcome when there is no unique eligible answer.

Candidate selection, conflict counting, commitment eligibility, and outcome status should be native graph rules. The adapter may translate a recognized utterance into the neutral request structure and render an already-selected candidate; it must not choose which claim wins or mark claims accepted. A unique candidate should be bounded by a declared policy and carry the source claim, not merely a copied value. Use a separate `ClaimSchema` or explicit predicate/role vocabulary where needed; do not force world-state observations into claim syntax.

## Gated evaluation before deployment

Use source-locked fresh graphs and identical facts across each stage:

| Gate | Positive control | Negative/adversarial controls | Required evidence |
|---|---|---|---|
| Existing polar baseline | Accepted, evidenced unary/binary proposition and matching polar question | Mismatched predicate/role, unsupported shapes, changed commitment status, negated question | One `PolarAnswerPlan` with source support or an honest non-answer; preserve the existing route behavior |
| Claim write | Explicit accepted neutral proposition | Proposed without uptake; unsupported fields; unresolved speaker | Exact proposition/evidence/source graph and no automatic acceptance |
| Recall eligibility | One accepted affirmed or negated claim | Challenged, retracted, suspended, rejected, uncommitted | Only eligible source propositions yield candidates; polarity preserved; accepted-status producer trust is explicit |
| Query binding | Explicit neutral cue matching predicate and role | Unknown predicate, partial/ambiguous role, unrelated query | Request linked to query event; no candidate if cue is unresolved |
| Conflict handling | One unique accepted claim | Two accepted contradictory values; an old claim then a retraction | Explicit conflict/clarification; no silent last-write-wins |
| Provenance rendering | Known speaker/source event | Unknown speaker, adapter-ID spoof, missing evidence node | Output attributes the claim and remains `not_observed` |
| Integration | Same-conversation value is retrieved after a query | Fresh-control, wrong-context, challenged/retracted controls | Exact counterbalanced output or honest abstention; full graph/source checks |

Keep value extraction as its own gate: current parser evidence is 15/18 surface-value recovery but 0/18 complete target propositions. An upstream semantic adapter can be used to test downstream substrate capability, but its extraction accuracy and provider trust must be reported separately. The explicit-ingress and accepted-proposition-to-episode benchmarks provide current write and boundary controls; the structured episodic benchmark provides the independent observation-memory positive control.

## Source basis and unresolved work

- `seeds/communication_intent_arbitration.json` already supports a restricted proposition-to-polar-answer route using accepted-status, evidence, relation, and argument matches.
- The source-locked polar-answer panel passes exact unique-claim, polarity, status, mismatch, and evidence-presence conditions; it exposes the missing lifecycle-applied-uptake and source-event requirements.
- The contradictory-claim panel fails conflict abstention in 6/6 insertion-order conditions: both propositions receive support but the affirmative plan is selected every time. The retracted-claim control passes in 3/3.
- `seeds/episodic_working_memory_core.json` currently binds only observed events with perceived/grounded provenance, and generates `Episode` nodes with non-observed trace provenance.
- `domains/proposition_commitment.py` materializes neutral claims with source evidence and discourse-event lineage; `apply_situation_consequence` requires explicit acceptance, affirmative polarity, evidence, and recognized change-of-state roles.
- The source-locked accepted-proposition integration panel passes proposition uptake but creates no episodic event/context/schema or retrieval request in 9/9 graphs.
- The text extraction panel fails complete proposition structure in 18/18 statements, while query classification alone does not produce a live memory request.

The extension from matched polar questions to wh-query claim recall, rule-level conflict handling, calibration, security/authentication boundaries, and attributed response rendering remains unimplemented and unmeasured. The existing polar route is a real partial capability; neither it nor the contract is evidence of self-improvement or general memory integration.
