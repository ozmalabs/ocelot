# Thoughtexperiment edit-operator node-identity hypotheses v1.1 preregistration

V1 was an invalid task fixture: it added another `RecipientVerb` node for each
action, creating cross-product rule matches within a single closure. The
capture is retained as a diagnostic and excluded from capability estimates.
V1.1 changes only this input materialization: each distinct verb has one shared
`RecipientVerb` node, and each event adds one `ActorAction`. This preserves the
actor/verb identity question while preventing duplicate recipient nodes from
manufacturing extra match combinations.

## Question and design

Can the shared structural edit algebra generate identity-guard candidates for
the faulted `mint_actor_goal_recipient` rule, and can graph-resident evidence
select the actor+verb guard over broader and narrower alternatives before
held-out outcomes are scored?

Use `domains.edit_ops.find_edge_identity_sites` and
`apply_add_edge_identity_guard` on the faulted rule. Include all generated edge
and `node_attrs` sites without filtering. The expected pool is eight hypotheses:
one edge-existence guard and seven attribute signatures. Freeze one candidate
permutation for each of four worker processes. Score all eight candidates on
the same four training events, then pass only opaque IDs and correctness
evidence to `select_candidate_from_graph_evidence`.

Training events are `(actor-a,sing,cup)`, `(actor-a,sing,bowl)`,
`(actor-a,dance,book)`, `(actor-b,sing,cup)`. The target permits one output for
each actor+verb pair, regardless of object. Held-out events, frozen before
training, are `(actor-c,sing,cup)`, `(actor-c,sing,bowl)`,
`(actor-c,dance,book)`, `(actor-d,sing,cup)`. Score all candidates and the
unmodified authored rule on this sequence.

## Gates

- Lock runner, analyzer, protocol, edit algebra, task seed, and native binary
  before capture; check source stability at every stage.
- Regenerate eight unique candidates from the locked rule, with no held-out
  outcome access during training or selection.
- Require exactly the actor+verb hypothesis to pass the training episode and
  be selected. All-wrong and tied evidence controls must abstain.
- Require the selected repair and source positive control to pass every
  held-out step; score every other candidate to expose false proposals.
- Verify primary rule state is stable and report generation, training,
  selection, and exhaustive held-out scoring costs separately.

This is one synthetic actor/verb task family with harness-authored rule,
fault, examples, and oracle. It measures generic edit-site generation and
evidence selection, not autonomous residual diagnosis, open-ended operator
invention, or general self-improvement.
