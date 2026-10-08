# Reflected Term cleanup hook behavior preregistration

**Question.** Does `remove_term_subgraph` emit exactly one `node_deleted` hook per deleted node, omit externally protected nodes, and define observable behavior when a hook raises after graph mutation?

## Fixed procedure

Use a fresh native Substrate and one `Cat(Lit, Reverse(Var))` reflected Term tree. Record the cleanup report's removed/protected IDs. In the success arm, register one callback collecting `(node_id, former_type)` and clean the root. Require hook records to equal the removed list in order, contain no protected IDs, and leave no Term nodes. In a second fresh substrate, register a callback that records its first invocation and raises `RuntimeError`; invoke cleanup and require an error to be surfaced after all four node events are delivered and all Term nodes are removed. A second observer registered after the raising callback must still receive all four events. This checks the documented per-callback tolerance while preserving first-error reporting.

Also run success with an externally owned leaf. Require protected nodes to receive no deletion callback and remain live. Do not change engine or binding code during the probe. Verify the installed native extension against its content-based build record and lock the runner, preregistration, and extension hashes before execution.

## Interpretation boundary

This is a local Python binding lifecycle probe, not a pytest regression suite. It does not test concurrent mutation, hook reentrancy, callback ordering across multiple callbacks, TermArena reclamation, or broad runtime cost. A surfaced callback error after native deletion is recorded as a contract/design finding, not a cleanup rollback failure.
