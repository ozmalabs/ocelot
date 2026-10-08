# Residual CoW return v1 preregistration

This follow-up tests whether the action-geometry residual proposal path can run in an isolated Thoughtexperiment branch, return only its post-input graph residual to the host graph, and preserve the host rule store. It pairs shared-graph-pages branches with deep-copy controls over the same four cardinal inversions and nine negative/absent-target controls from cue-derivation v1.

The shared-graph-pages backend shares node/edge storage pages and adjacency pages; native rule vectors and query indexes remain eagerly copied. Therefore this is a partial CoW engine path, not a claim that all substrate state is copy-on-write. Begin the mutation journal before `induce_concern`; checkpoint after induction; finish after `ground_concern`. Score successful proposals on the existing held-out navigation cases before applying the `derived_only` graph delta to the host using its captured graph/rule revision. Do not merge the branch's native rewrite-rule additions.

## Gates

- Both backends reproduce the v1 semantic outcomes: four correct `flip_comparison` proposals with held-out utility; four valid non-inversions and four malformed/underdetermined residuals abstain; an absent target produces no proposal.
- The candidate target rule remains unchanged in the branch. Before graph-delta return, the complete host graph and native rule export equal their pre-fork state.
- For each positive case, applying only `derived_only` succeeds against the recorded revision, the host native rule export remains byte-for-byte equal, and the host graph delta equals the returned residual. Negative cases return no proposal and do not apply a residual.
- Record full and derived-only mutation counts, their digests, fork/induction/grounding/journal/adoption time, and source hashes. Report graph-page CoW versus deep-copy timing descriptively; no broad speed claim from this one workload.

The returned residual is graph state only. The experiment does not merge native rewrite-rule vectors, prove that every returned graph node is independently useful, or authorize adoption into a live production agent. Results remain limited to an authored navigation family and the current partial-CoW implementation.
