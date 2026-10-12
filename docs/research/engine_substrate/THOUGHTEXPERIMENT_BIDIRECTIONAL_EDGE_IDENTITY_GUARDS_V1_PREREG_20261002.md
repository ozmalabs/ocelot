# Bidirectional edge-identity guard proposals v1 — preregistration

**Question.** Can a generic transformation derive output-edge guard hypotheses from either bound endpoint, and can the graph evidence selector choose the right scope across an idempotent mint rule and a rule that must emit repeated responses?

## Fixed rule families

Use two independently seeded rules. For recurrence, fault `mrl_offer_due_once` by removing its existing negative-existence guard; two separately keyed due candidates must each receive exactly one offer. For conversation, use `reply_to_adjacency_pair`, faulting only its existing per-message `Not Exists(m responds_to)` guard; every inbound message must receive one reply. Conversation training contains two greeting inputs to expose speech-act-level aliasing; held-out contains greeting, question, greeting.

The generic benchmark transformation scans each `add_edge` effect and each endpoint bound by the rule match. For a bound source it emits an outgoing `Neighbours` guard; for a bound target it emits an incoming `InNeighbours` guard. When both endpoints are bound, it adds equality against the other endpoint; when the opposite endpoint is a fresh effect variable, it records a coarse guard. The ordinary graph-Term composer contributes its fixed `add_match_guard` proposal. No recurrence or conversation candidate generator is called. Each family should produce three edge-derived proposals plus the composer proposal.

Four source/native-locked workers score every proposal on two fresh training episodes. The native graph-Term evidence selector sees opaque candidate IDs and only those training labels. Freeze decisions before held-out capture; then score every candidate on held-out inputs to measure false proposals and the frozen winner's transfer. Retain source-rule positive controls and all-wrong/tie selector controls.

## Gates and limits

- Four workers complete both families with stable source/native hashes and exact candidate-set reproduction.
- The generator emits three distinct edge-identity hypotheses plus one composer proposal per family and does not call `_default_candidates`.
- Recurrence uniquely selects the candidate-scoped outgoing `has_mint_offer` guard; conversation uniquely selects the incoming per-message `responds_to` guard after repeated-speech-act training.
- Each selected proposal passes its held-out oracle. The coarse recurrence episode/agent guards and conversation agent/speech-act guards fail at least one held-out condition; all-wrong and tie controls abstain.
- Proposal/evidence nodes remain branch-local, source rules are unchanged, and cost includes all candidate generation, scoring, composition, selection, and held-out evaluation phases.

This is a manually specified generic AST transform in an evaluation harness, not production substrate invention. The two task families are authored fixtures with external oracles; the result is not a natural-task false-proposal rate or an autonomous learning claim.

Capture source lock, training orders, and then held-out scores. Analyze with the separately locked analyzer.
