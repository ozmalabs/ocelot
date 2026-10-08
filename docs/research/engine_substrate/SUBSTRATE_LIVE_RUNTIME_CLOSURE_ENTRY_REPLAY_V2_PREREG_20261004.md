# Live runtime closure-entry replay v2 preregistration

## Question

Does a rule-store import that preserves authored match order and `mutation_protected` metadata reduce the per-rule work discrepancy in independent replay of captured primary `run_rules` calls?

## Method

Use the source-locked closure-entry v1.1 capture. Restore each call's graph and the complete ordered rule list into a fresh native substrate using `import_rules_preserving_match_order`. Verify exact graph and rule round-trips, including protection metadata, then run once with the recorded progress cap. Collect per-rule metrics and aggregate by request against the parent's source-locked counters. Record work equality as an outcome, not an acceptance precondition. This revision does not yet restore scheduler dirty bits, dirty-node sets, cursors, or other mutable closure state.

## Acceptance

All 15 calls must restore and run; input locks must match before and after. Report exact rule metadata restoration and metric deltas. Preserve mismatches without filtering. The previous v1 result remains unchanged.

## Limits

This covers primary adapter `run_rules` calls on one authored route only. It tests a more faithful rule-store reconstruction but is not a complete scheduler checkpoint, nor evidence of broad task tractability or scaling.
