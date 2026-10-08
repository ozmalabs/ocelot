# Generic edge-idempotence proposal generation v1 — preregistration

**Question.** Can a structure-derived generic rule transform, combined with native graph-Term evidence selection, surface and select a recurrence repair without including the host's recurrence-specific `dedup_identity_fix` candidate?

## Candidate construction and task

Four fresh workers start from the existing `mrl_offer_due_once` fixture with only its negative-existence guard removed. The harness does not call `_default_candidates` or any recurrence-specific repair builder. A generic AST transform scans the faulted rule's `add_edge` effects, and for every source variable bound by the match emits one hypothesis that adds `Not Exists(Neighbours(source, edge_type))` to the rule's `where`. The general structural composer also contributes its ordinary fixed `add_match_guard` proposal. For this fixture this should yield three edge-derived proposals and one composer proposal. The candidate labels and rule bodies are not given to the selector; it receives opaque digests.

For each proposal, score two fresh training episodes, each containing two sequentially admitted due candidates. Recompute the label from exactly one offer per candidate and zero progress at fixed point. A native Term selects a unique positive maximum from those outcomes in an isolated snapshot branch. Freeze that selection before scoring two separate held-out episodes. The held-out stage reconstructs the candidate pool from the same generic algorithm and verifies descriptor parity before it evaluates only the selected proposal. Include all-wrong and tied-evidence selector controls.

## Gates and limits

- Four workers, exact source/native/input parity, and a frozen order-before-held-out sequence.
- Exactly four unique proposals, including three `add_edge`-derived guards and the ordinary composer proposal; no specialized recurrence candidate or `_default_candidates` call in proposal generation.
- The native Term selects the unique two-of-two training winner; it selects an edge-derived candidate, not the fixed composer proposal.
- The selected proposal passes both disjoint held-out episodes in every worker; all-wrong and tie controls abstain.
- Proposal/evidence nodes stay in the branch and the primary rule store is unchanged.

This evaluates one manually specified generic AST transformation in a benchmark harness. It is not evidence that the substrate invented that transformation, autonomously diagnosed the fault, or learned a rule from natural tasks. The labels and task oracle remain host-supplied; the useful result would be that the good candidate need not be injected into the candidate list and selection itself can be substrate-side.

Capture the source lock, then training orders, then held-out scores, and run the independent analyzer.
