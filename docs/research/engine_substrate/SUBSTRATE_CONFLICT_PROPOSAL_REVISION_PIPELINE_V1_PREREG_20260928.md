# Explicit revision pipeline for proposal resolution v1

## Question

Can an explicit graph revision event plus ordered closure stages keep a materialized proposal resolver correct under additions, tie creation/removal, and score changes, with reproducible counted work?

## Pipeline

Three source-locked workers run N=2/8/32/64. The caller applies one input mutation, creates a fresh revision node linked to the target, then adds and settles three stage edges in order: `compute_max` materializes one `MaxOver`; `compute_count` counts current proposals equal to the stored maximum; `compute_decision` writes `ambiguous` and writes the unique top label or empty-string sentinel. The stage rules are distinct and each closure runs only after its stage edge is added. Mutations are: initial proposal set; add a higher proposal; add an equal-scoring proposal; remove that proposal edge; lower the higher proposal's score. Every stage captures its rule report, native counters, and elapsed time.

## Gates

Every stage settles at fixed point. After each three-stage revision, target maximum/count/ambiguity/selection must equal a separately computed Python oracle. Integer native counters must reproduce across workers after excluding elapsed time and metric keys ending `_ns`. Stages execute in the preregistered order; no stage may be skipped or silently retried. The score mutation must be followed by a fresh revision event, making explicit that automatic score-change wakeup is not part of this claim.

## Limits

This tests a caller-orchestrated revision protocol on one proposal family through N=64. It does not establish automatic invalidation, failure recovery between stages, concurrent updates, general truth maintenance, or asymptotic complexity. Empty string is the selected no-winner sentinel. Counted operations exclude host-side mutation/event creation and are not latency or memory guarantees.
