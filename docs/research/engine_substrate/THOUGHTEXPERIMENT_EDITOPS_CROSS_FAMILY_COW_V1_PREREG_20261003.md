# Cross-family edit-op CoW integration v1 preregistration

## Question

Do generated edge-identity guards retain their measured selection quality when
the recurrence and conversation candidate pools execute in isolated CoW
branches, and can each selected proposal receipt return to the primary without
changing its active rules?

## Design

Use the current bidirectional edge-identity recurrence and conversation
fixtures with the shared `domains.edit_ops.find_edge_identity_sites` and
`apply_add_edge_identity_guard` candidate generator, plus the same graph
composer candidate used in the existing four-candidate panel. Four fresh
workers freeze a candidate permutation for each task family before scoring.
Every candidate runs in full-copy and shared-graph-page branches on the same
family's training sequence. The native graph-Term selector receives only
opaque candidate IDs and training outcomes. The held-out stage scores all
candidates on both backends only after the training order is frozen.

Each branch starts from a fresh faulted primary and patches one candidate rule
locally. Recurrence runs the two recurrence candidates through sequential
closure; conversation runs its locked utterances through a branch-bound
WorldAdapter. A training-selected candidate is replayed in a shared-page branch
and returns only a changed `ThoughtExperimentProposal` receipt through the
revision-checked graph-delta API. The primary active rule remains unchanged;
stale receipt replay must be rejected atomically. The authored, unfaulted rule
is a positive control in each family/backend.

## Gates

- Lock the runner, analyzer, protocol, helper fixtures, shared edit-op wrapper,
  task seeds, native binary, and build manifest before capture.
- Require four unique generated candidates per family, stable frozen order,
  exact full-copy/shared-page semantic parity, and unchanged primary state
  before receipt return.
- Require exactly one training winner per worker/family; the graph-Term
  selector must choose it. All-wrong and tied controls must abstain.
- Require the selected repair and authored source-rule control to pass every
  held-out case on both backends. Score all candidates, including failures.
- Require selected receipt content parity, active-rule preservation, and
  stale-retry rejection without mutation.
- Report candidate composition/generation, branch, closure, selector,
  held-out, receipt extraction, and return costs separately.

This tests two previously measured task families under branch execution. The
task, fault, cues, examples, and oracle remain harness supplied; it does not
measure autonomous residual diagnosis, rule activation, or self-improvement.
