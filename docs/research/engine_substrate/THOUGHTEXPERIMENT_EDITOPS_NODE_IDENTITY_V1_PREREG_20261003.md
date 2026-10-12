# Thoughtexperiment edit-operator node-identity hypotheses v1 preregistration

## Question

Can the shared structural edit algebra generate identity-guard candidates for
a fresh actor/recipient rule, and can graph-resident evidence select the
actor+verb guard over narrower or broader alternatives before held-out outcomes
are scored?

## Design

Use `domains.edit_ops.find_edge_identity_sites` and
`apply_add_edge_identity_guard` on the faulted `mint_actor_goal_recipient`
rule. Include every generated edge and `node_attrs` site without manual
filtering. The expected generated pool contains eight hypotheses: one
edge-existence guard and seven attribute-signature guards. Freeze a seeded
candidate permutation per worker before collecting results. Four fresh worker
processes each score every candidate on the same training sequence, then pass
only outcome evidence and opaque candidate IDs to
`select_candidate_from_graph_evidence`.

Training sequence: `(actor-a,sing,cup)`, `(actor-a,sing,bowl)`,
`(actor-a,dance,book)`, `(actor-b,sing,cup)`. The expected rule permits one
goal for each distinct actor+verb pair, regardless of object. This makes
actor-only, object-only, verb-only, and edge-only scopes observably different.
Freeze held-out sequence before training and selection:
`(actor-c,sing,cup)`, `(actor-c,sing,bowl)`, `(actor-c,dance,book)`,
`(actor-d,sing,cup)`. Score all eight candidates on it, whether selected or
not. Score the unmodified authored rule as a positive control.

## Gates

- Lock all runner, analyzer, protocol, edit-operator, task-seed, and native
  binary inputs before capture; verify source stability at each stage.
- Regenerate all eight candidates from the locked rule and verify unique,
  semantically distinct variants; no candidate may use held-out outcomes.
- Require training evidence to select exactly the actor+verb candidate;
  all-wrong and tied evidence controls must abstain.
- Require the selected candidate and source positive control to match all
  held-out expected per-step goal counts. Score and report every other
  candidate to expose false proposals and overgeneralization.
- Verify primary rule state remains unchanged and report generation, scoring,
  selection, and held-out costs separately.

This is one synthetic actor/verb family, with harness-authored rule, fault,
examples, and oracle. It measures generic edit-site generation and evidence
selection, not autonomous residual diagnosis, open-ended operator invention,
or general self-improvement.
