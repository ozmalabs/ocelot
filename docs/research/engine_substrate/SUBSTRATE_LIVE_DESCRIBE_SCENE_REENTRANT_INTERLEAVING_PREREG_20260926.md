# Live describe-scene reentrant interleaving probe preregistration

## Question

When request A is paused immediately after its production selection event and request B reenters the same `WorldAdapter`, does B complete without stealing A's Goal identity or disturbing A's active lifecycle?

## Method

- Three fresh full-seed processes; each attaches one three-percept scene and issues two same-recipient `describe what you see` instructions.
- A wrapper around the production lifecycle recorder calls the original recorder for A's `selection`, captures A as selected/active, and synchronously calls `converse` for B before A proceeds to execution. The wrapper does not recurse on B.
- Capture the shared state's event order, every event's `for_goal` edges, each inbound Message's unique parent Goal, origin links, child counts, replies, and Goal status/active/closed state at A's pause, after B returns, and after A returns.
- Lock runner, protocol, amendments, source files, seed, native build, and commit; fingerprint at worker start/end and after all workers.

## Pass conditions

- A is selected and active at the pause.
- B has a distinct parent Goal, exact origin link, and its own three utterance subgoals; after B returns it is resolved/closed/inactive while A remains selected/active.
- A resumes and resolves/closes/inactivates; neither Goal has cross-owned events.
- Shared event order is `instruction(A), selection(A), instruction(B), selection(B), execution(B), action_result(B), execution(A), action_result(A)`.
- Both replies are nonempty and equal the baseline describe-scene reply.
- All three source-stable workers reproduce the same normalized structure.

## Limits

This is deterministic same-thread reentrancy, not thread concurrency. It tests the live describe-scene path only and does not establish external-effect safety, other route behavior, or scale.
