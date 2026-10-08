# Live describe-scene threaded interleaving probe preregistration

## Question

Do two simultaneous Python threads calling `converse` on one `WorldAdapter` preserve Goal identity and lifecycle when B runs to completion while A waits after its selection event?

## Source basis and method

The native `PySubstrate` stores the graph core behind `Arc<Mutex<SubstrateRs>>`; `run_rules` releases the GIL while holding that mutex. This protects individual native graph operations, but does not establish synchronization for mutable Python-side adapter state. The probe therefore runs in isolated fresh worker processes.

Each worker loads full seeds, attaches one scene, starts request A in a thread, and blocks A in the live lifecycle recorder immediately after its selection event. The main thread then starts request B in a second thread. B proceeds through selection, execution, and result, signals completion, and releases A. Capture both thread exceptions, event order/owners, Goal/Message/origin links, state while A is paused and after B finishes, terminal state, subgoal ownership, and replies.

## Pass conditions

- A reaches the barrier as selected and active.
- B completes while A remains blocked and selected/active; B has a distinct request-owned Goal and its own lifecycle events.
- After release, A completes with its own identity-bound lifecycle.
- Both Goals resolve, close, leave the active set, and own three utterance children; all lifecycle events link to exactly their own Goal.
- Both replies match the sequential baseline and no worker raises or times out.
- Three source-stable fresh workers reproduce the normalized structure.

## Limits

This is controlled concurrent request overlap on one `WorldAdapter`, with graph operations individually serialized by the native mutex. It does not establish safety for arbitrary concurrent adapter methods, background scheduler work, external I/O, or general workload scaling.
