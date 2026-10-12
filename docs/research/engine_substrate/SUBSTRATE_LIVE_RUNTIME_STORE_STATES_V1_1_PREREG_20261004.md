# Live runtime store state capture v1.1

## Question

Which native matcher stores contribute to the paired closure counters in the fixed replicate-0, audit-on, two-request conversation, and what graph and rule definitions were present when each store first entered matching?

## Protocol

Use the existing locked `live_runtime_closure_counters_v1_6` worker, replicate 0, audit mode on. At each outer `WorldAdapter.converse` request boundary, clear the opt-in native store-state registry and enable it. The native matcher records the first complete graph and rule table seen for each store ID in that request. After the request, disable capture and export the recorded store rows as individually gzipped JSON files. Reconcile each exported ID and local rule index against the parent worker's process-wide identity rows and per-rule counters. Do not infer a store state for an identity absent from the exported snapshots.

The snapshot is first-observed-at-matcher-entry, not a prompt-boundary snapshot. It captures store contents as visible when a matcher first uses the store in that request; stores never entered during the request are not expected to appear. Primary request-boundary state remains covered by `live_runtime_pre_request_state_v1`.

## Acceptance

The capture must use the source-matched engine, match the parent v1.6 replicate-0/audit-on task projection, replies, and final graph digest, match all behavioral counter rows and identity rows after excluding explicitly timed `*_ns` and `scheduler_plan_ns` global metrics, retain raw timed values for audit, and have stable locked inputs before and after execution. An independent analyzer must decode every gzip payload, verify its SHA-256, graph node/edge referential integrity, unique store IDs, rule-table indexing, and exact reconciliation of every counter identity into either a captured store/local rule slot or an explicit no-snapshot status. No store or rule identity may be silently dropped.

## Scope limits

This is a single fixed-route instrumentation sample. It can establish attribution coverage and inspect captured state; it does not estimate population rates, prove all native entry paths are instrumented, or establish tractability at scale.
