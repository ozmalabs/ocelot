# Conversation read-only boundary connected-frame preregistration (2026-09-26)

## Question

Can native full closure and repeated frame-scoped closure reach the same task outcomes when adjacent conversation frames read a shared immutable evidence node, while every mutable deliberation candidate and goal remains frame-local? If semantic gates pass, what work and wall cost does the current generic scoped path incur?

## Frozen workload

Use `conversation_deliberation_phase4a` at 1/2/4/8 deliberations, three fresh-process replicates per size and arm (`full`, `scoped`). Preserve the prior connected-frame chain shape, but correct its aliasing defect: each frame receives its own candidate copy for each incident boundary answer; a single read-only `BoundaryEvidence` node per adjacent pair is shared by the two frames. The candidate copies have unique mutable identities/status fields and each points to that shared node through `derived_from_evidence`. Both frame Microtheories own the shared evidence node via `has_concept`.

Patch only the scoring rule in an in-memory manifest: add the candidate-to-evidence match edge and add `Attr(e, boundary_value)` to its score. This makes the cross-frame boundary an actual runtime read dependency. No closure rule writes the shared evidence node. Candidate status, arbitration score, traces, goal and selection remain local to a frame. The deliberately shared mutable candidate case from the previous capture remains a separate negative control and is not mixed into this treatment.

Full closure uses native `run_rules_report`; scoped closure uses repeated round-robin native `run_rules_scoped` until a complete no-progress round, followed by a zero-work full-closure fixed-point probe. Record exact normalized frame projections, selected candidate, fixed-point status, rule/candidate/Term work, wall/CPU time, turns, and peak RSS. Exact paired projection and expected-winner parity are required before interpreting cost.

## Integrity gates and claim limits

Require 24 fresh worker cells, unique PIDs, balanced size/replicate/arm matrix, source/native freshness, exact connected chain topology, exactly N−1 shared evidence nodes, each shared evidence node owned by exactly its two adjacent frames, each candidate owned by exactly one frame, no cross-frame mutable candidates, and a scoring rule that includes the shared-boundary term. Require all arms to reach fixed points, expected decisions to pass, and exact full/scoped projection parity in every pair. Preserve failed captures.

This is one authored deliberation rule family and a read-only shared-evidence chain. It does not establish natural conversation topology frequency, arbitrary/dense dependency handling, mutation-triggered notification of evidence changes, general GALS correctness, asymptotic complexity, or large-scale CPU feasibility. The old shared-mutable-candidate capture remains a negative control.

## Provenance

Lock this protocol, runner, analyzer, seed, materializer, and engine/rewrite sources before execution. Store lock and raw capture separately from the earlier shared-mutable-candidate result.
