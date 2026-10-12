# Multi-route static dependency metadata supplement v1

Date: 2026-10-06  
Purpose: capture declared native read/write keys for RuleUIDs observed in the already completed multi-route frame/access capture.

The frame capture retained observed `rule_uid`, event kind, resource key, concrete node/peer IDs, and rule name, but not each rule's static access declaration. This supplement replays one worker per route under the same locked harvest inputs and records the final active/inactive rule access table and RuleUID mapping after the route's ordinary `converse`. It performs no access tracing and makes no timing claims. It does not modify or replace the original frame capture.

The five routes and route prompts come from `live_conversation_task_graph_harvest_v2.py`; use replicate 0. Require source lock stability and one returned route record for every worker. After capture, match observed RuleUIDs to the captured table by RuleUID and require every event UID to resolve. Verify each matching rule name agrees with the name attached to the original trace. Compare resource-key events to declared keys/wildcards using the same conservative categories in `analyze_rooted_frame_access_scope_reconciliation_v1_2.py`. Compare concrete attribute/edge reads and writes by `(kind, node, resource[, peer])` to find observed dynamic cross-rule pairs, then compare them with static possible pairs. Unresolved resources and trace kinds without a static key remain explicitly uncheckable.

This supplement can detect observed static-key mismatches and concrete pairs absent from the static projection for this panel. It cannot establish complete dependencies for unobserved paths, semantic necessity, all host-side accesses, or natural task prevalence.
