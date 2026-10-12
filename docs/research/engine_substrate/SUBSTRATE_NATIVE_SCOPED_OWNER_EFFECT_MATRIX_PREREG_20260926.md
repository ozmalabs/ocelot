# Preregistration: native scoped owner reports across graph effects

**Question.** Does `run_rules_scoped_delta_report` map the graph writes of one scoped writer to all directly owning Microtheories for common native graph effects, including edge insertion/deletion and node birth/deletion?

**Rationale.** The conversation write-owner confirmation establishes this for one shared-node `SetAttr`. A generic graph-delta probe exercises more direct effects but does not compare scoped owner reports with the full snapshot oracle. This matrix closes that gap for five bounded effect shapes.

**Frozen matrix.** Five cases (`shared_add_edge`, `shared_del_edge`, `shared_set_attr`, `owned_node_birth`, `owned_node_deletion`) at 2, 4, and 8 consumer frames. Each cell runs in separate fresh processes for scoped mutation logging and full before/after snapshot reporting. A controller Microtheory owns the trigger; consumer frames own the touched nodes. For edge changes, the two endpoints belong to distinct frames. Unrelated frames are present as negative owner controls. Each writer is one-shot and must reach a non-budgeted settled result. The lock freezes this protocol, runner, analyzer, and native/source inputs before capture.

**Primary gates.** (1) Every paired scoped/oracle run performs the intended state transition and settles without a cap. (2) Scoped reported Microtheory IDs exactly equal the full snapshot oracle’s owner IDs. (3) Every oracle-changed node and edge target is covered by the scoped report. (4) Unrelated frame owners are absent. (5) A second scoped call is zero-progress with no residual deferred queue. Identity and counts of all cases must match the frozen matrix.

**Deferred effects.** This matrix intentionally does not claim deferred-effect support. Existing behavior exposes `deferred_effects_pending`; if observed, the cell fails the settled-report gate and is preserved. Scoped callers must not treat such a report as a complete notification set.

**Claim boundary.** This is a synthetic, five-case native mechanism confirmation at up to eight frames. It tests direct ownership, not arbitrary dependency discovery, automatic queue delivery, scheduler completeness, natural task locality, or performance. Full snapshot comparison is an O(V+E) oracle and is not a fair speed baseline.

## Harness amendment v1.1

The first locked launch stopped on its first scoped/oracle pair because the runner assumed the snapshot oracle returned `hit_progress_budget`; that field is absent from the snapshot API. It produced no complete cell and no accepted raw capture. The amendment reads this optional field as false only for the oracle arm; the scoped arm continues to require the explicit native field. The protocol, cases, outcome criteria, and primary gates are unchanged. The corrected runner and analyzer receive a new amended lock before the confirmatory run. The original v1 lock is retained.

The second launch then found the analogous absent `deferred_effects_pending` field on the snapshot oracle. It also stopped before a complete cell. Amendment v1.2 treats absent oracle-only status fields as false, while retaining explicit pending-effect checks for scoped reports. The v1 and v1.1 locks are retained; v1.2 is the confirmatory lock. No outcome gate or fixture changed.
