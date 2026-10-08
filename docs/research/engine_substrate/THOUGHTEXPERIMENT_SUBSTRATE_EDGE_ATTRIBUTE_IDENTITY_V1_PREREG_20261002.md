# Substrate edge-attribute identity v1 — preregistration

## Question

Can the structural composer propose an attribute-scoped guard for an edge whose target is a freshly created node, and does that representation repair the actor/verb false-suppression boundary without regressing relation-level idempotence or per-message replies?

## Change under evaluation

The pure edit layer now derives bounded hypotheses from `add_node` effects linked to fresh edge endpoints: each bound-attribute singleton, each pair, and the complete bound-attribute set when there are more than two. The graph exposes those as `EditSite` records. The applier constructs a `Not Exists(NodesOfType(...))` predicate comparing selected attributes against the new-node effect terms. Search is O(m²) sites per associated node effect, not a full power set. The graph Term must choose one uniquely; tied scopes abstain.

## Frozen conditions

Repeat the recurrence and conversation proposals as regression controls. For the real `mint_actor_goal_recipient` rule, score two proposal cues on identical task states:

- Relation-only cue: `mint recipient actor goal once edge output any endpoint`; expected proposal is the v1.1 outgoing agent-edge guard and expected held-out output is `[1,0]` for two distinct verbs.
- Attribute identity cue: `mint recipient actor verb pair identity`; expected proposal is `out agent has_actor_goal attributes actor+verb` and expected output is `[1,1]`.

The target and cue remain harness supplied. The harness may construct task states and compute the independent outcome oracle, but may not scan edge sites, enumerate proposal variants, or apply edits itself. Four workers each use two one-verb training episodes and two fresh two-verb held-out episodes for both actor proposals. Recurrence/reply use their prior two-train/two-held-out schedules. The no-overlap and ambiguous-site abstention controls remain.

## Gates

Require exact locked workers, stable source/native hashes, expected target/operator/site per condition, semantic change from the faulted source, all training outcomes correct, recurrence and conversation held-outs all correct, relation-only actor false suppression `[1,0]` in all eight held-out episodes, attribute-identity actor success `[1,1]` in all eight, source controls correct, honest abstention controls, primary rule preservation, complete nonnegative phase timings, and analysis linkage to frozen orders/scores. Record composition, training, held-out, and source-control costs. This is prompted edit-space transfer, not autonomous residual discovery.

Capture lock, then orders, then separate held-out scores. No post-lock source or protocol edits are permitted; a failure is retained as the result.
