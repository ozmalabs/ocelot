# Directed boundary replay preregistration

**Question.** Does caller-notified scoped settlement preserve the full-rescan state after repeated directed boundary-edge deletion, insertion, and weight replacement, including changes that propagate through multiple frames?

## Locked design

- Use the authored `can_native_update_3state` native rule with 12 Concept nodes in three four-node Microtheories.
- Create a directed path `i → i+1` for i=0…10, weight +0.75. The rule reads outgoing causal-influence neighbors, so each source's update depends on its target. Set all fields and states to zero except node 11's external field +1.0; settle the common starting graph before the sequence.
- Mutate the directed edge `7 → 8`, which crosses the frame-1/frame-2 boundary, through the repeated action sequence `(delete, insert +0.75, replace with -0.75, replace with +0.75)` three times.
- At each action, clone the mutation by constructing separate identical full and event graphs from the same locked fixture. In the event arm, directly notify the source frame (frame 1), then use the current directed edge relation to wake source readers when a target frame changes. The full arm round-robins all frames to closure.
- After every action, record exact active state, settling termination, progress applications, frame turns, and independently recomputable full-graph residual. Test an omission control on the first deletion by changing the edge but performing no settlement.
- Lock runner, this protocol, the reference helper, native seed, and source files before execution. Preserve every action-level result.

## Decision rules and limits

All 12 event/reference checkpoints must terminate, match exactly, and have zero independent full-graph residual. The initial deletion omission control must have positive residual; if it does not, sensitivity is unproven. Edge changes are applied between fixpoint calls, not concurrently during a native firing.

This is a synthetic directed path mechanism test. It does not establish natural dependency prevalence, arbitrary graph behavior, native effect-to-frame notification, or GALS. It specifically tests repeated invalidation/reconstruction of the caller-side dependency relation.
