# Thoughtexperiment mixed-receipt oracle v1 — preregistration

**Date:** 2026-10-01  
**Question:** Do randomized, explicitly approved mixed graph receipts commit exactly the intended node/edge delta, and do stale before-images prevent the entire proposal from applying?

## Design

Use five fresh worker processes and ten deterministic seeds per worker. Each small sparse directed graph produces six distinct proposal kinds: node attribute change, node addition, edge addition incident to the new node, edge attribute change, explicit edge removal, and node removal (including all incident-edge removals). A separate conflict arm for each seed regrounds the same shape, changes a protected edge after regrounding, then attempts commit.

For the approved arm, an independent full-graph Python oracle applies the operation specification to a copy of the pre-trace graph. Added node IDs are obtained from the writeback receipt mapping. Compare the complete semantic node/edge projection after commit with the oracle, excluding harness/gate trace nodes outside the operation's mapped identity set. For the conflict arm, compare the graph's semantic projection with the base plus only the injected concurrent edge change.

## Gates

Require 50 distinct positive trials and 50 conflict trials across five processes; exact full-projection parity for every approved trial; all six operation kinds reported as written; approved gate and writeback success for positive arms; stale edge refusal before authorization/writeback in conflict arms; and exact preservation of the competing edge update with no proposal writes.

## Source lock and limits

Capture runner/protocol/source SHA-256, native binary SHA-256, engine fingerprint, host/runtime, seeds, operations, and per-trial oracle outcomes. Refuse stale native builds. This mechanism probe constructs receipt records directly; it does not establish that imagination learns useful mixed proposals, nor does a 64-node synthetic graph estimate natural-task incidence distributions.
