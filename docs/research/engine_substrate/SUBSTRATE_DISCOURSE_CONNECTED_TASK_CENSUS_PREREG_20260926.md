# Connected discourse task graph and access census (diagnostic)

**Question:** does an authored mixed-act discourse sequence expose small event-frame separators in its actual native graph, and which dependencies cross them while the graph grows? **Grade:** new workload diagnostic, not a representative natural-task estimate or a boundary-aware execution result.

## Frozen workload and frame rule

Use the ten-event `phase3_mixed_act_dialogue.v1` fixture as ordered. Materialize its request, selection, execution, action-result, assertion, question, and epistemic-limit events through `domains.discourse_state`; attach native goal objects to each `origin` event, and apply the registered discourse-state rules after each event. Frame assignment is determined only by fixture metadata: every `origin` starts a new frame; `unsolicited` starts a standalone event frame; `continuation`, `response`, and `repair` belong to the current frame. A goal belongs to the frame of its origin. DiscourseState, CommonGround, participants, and other unassigned nodes are boundary/global nodes.

This workload is authored and has been used for mechanism tests. It is selected to measure a genuinely connected task flow, not to estimate a task-population frequency. Do not change frame assignment after inspecting graph or trace results.

## Capture

Run fresh processes for full native closure with tracing disabled, full native closure with the partial runtime access trace enabled, and a second untraced replay. After each event, capture closure status/progress, graph digest and node/edge counts. At the final checkpoint retain full node/edge identities and types, event/goal frame ownership, global-boundary incidence by frame, direct cross-frame edge count, static native rule read/write declarations, and concrete access-trace rows by rule and checkpoint. Compute the exact treewidth of the three-frame interaction graph induced by direct cross-frame edges and shared global boundary nodes. Report graph treewidth separately only if computed on the full graph projection with its semantics stated. The input lock records the fixture, protocol, runner, materializer, rule seed, Rust sources, native extension, native build manifest, Cargo lock, commit, and dirty-worktree state.

## Checks and claim boundary

- All three fresh processes must reproduce the same exact graph digest and task-oracle state.
- The fixture must materialize ten events and the registered two-goal lifecycle must resolve through native rules with expected event provenance.
- Every task event and goal must have one frame owner; unassigned nodes remain explicit boundary nodes.
- Tracing must preserve graph state and drop no events. An empty observed access set does not imply absent dependency.
- Report direct interframe graph edges separately from shared-boundary incidence and trace-derived accesses; do not treat a partial trace as complete.

This census does not run partitioned closure, compare a boundary scheduler, or establish timing advantage. It supplies a connected task-derived structural sample and runtime access panel for those future gates.
