# Minting recurrence ledger — preregistration

## Locked policy
One `MintingRecurrenceEpisode` is opened for each `run_minting_train_of_thought` invocation. Candidate identity is **predicate-only**: every residual `(dimension, predicate, k)` witness projects to one predicate candidate, and a segment contributes at most one quantum for that predicate. Counts are episode-wide accumulated occurrences; absence neither resets nor decrements. `mint_after_quanta` is normalized to `max(1, int(value))`. The first native due condition makes exactly one offer, irrespective of its terminal shape-decode outcome.

## Boundary and schema
Python remains the evidence adapter: it reads the aperture residual, emits immutable `ResidualSegmentEvidence` facts, runs rules, and reads graph state. It holds no recurrence ledger, cannot compare readiness, cannot select due candidates, cannot create the offer `Observation`, and cannot mint an axis.

The graph contains `MintingRecurrenceEpisode`, one `ResidualSegmentEvidence` per `(episode, segment, predicate)`, a `PredicateRecurrenceCandidate`, and the native offer `Observation`. Evidence retains original tuple witnesses and set-point/observer/reached provenance. Candidate persistence is `Count(candidate -supported_by_segment-> evidence)`, not an incrementing mutable counter.

## Native rule order and idempotence
`mrl_open_candidate` creates one candidate per episode/predicate; `mrl_post_evidence_once` links immutable evidence exactly once; `mrl_derive_persistence` recomputes count and latest segment from edges; `mrl_offer_due_once` creates a single pending Observation; `mrl_record_offer_terminal` records all terminal statuses; `mrl_record_mint_result` retains candidate/episode-to-axis provenance. Edge absence guards and recomputation from immutable edges make a fixpoint rerun inert.

`shape_decode_loop` remains the only decode, recognition, duplicate, and `CapabilityAxis` mint authority.

## Held-out prediction
At threshold 2, `P, ∅, P` produces one predicate candidate, persistence 2, and one offer. A `bind(ITEM,SLOT)` witness on both evidence nodes should permit a downstream `OperationRequest{bind, ITEM, SLOT}` through the test-only native consumer seed. A binding-looking display label with no witness and a `bind(ITEM,GROUP)` witness must remain inadmissible: neither capability key nor spelling is a licensing route. The Rosch runner remains the end-to-end aperture extraction proof; deterministic native controls isolate the ledger and semantic counterfactual.
