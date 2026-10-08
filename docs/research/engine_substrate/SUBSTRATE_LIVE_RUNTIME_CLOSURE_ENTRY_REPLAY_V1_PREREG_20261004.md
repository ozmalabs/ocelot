# Live runtime closure-entry replay v1 preregistration

## Question

When every primary `run_rules` call is replayed from its exact captured graph/rule entry state, do the summed per-rule work counts reproduce the live primary-store totals?

## Method

Read the source-locked closure-entry v1.1 capture. For each request and call in original order, restore its compressed graph and rule payload into a fresh native substrate, verify exact graph round-trip and semantic rule round-trip with match-clause order preserved, then call native `run_rules` once with the recorded progress cap. Install definitions using `add_rule_preserving_match_order`; source and replay UIDs may differ only if the native store must regenerate a duplicate/zero UID. The binding resets the replay copy's `mutation_protected` flag, so the analyzer must count such rules and report this as a behavioral caveat. Collect native per-rule metrics and map them back by local rule index. Sum independently replayed call costs by request.

Derive expected primary-store metrics from the source-locked v1.6 counters using each audit ID's `(store_id, local_rule_index)` identity. Compare all per-rule metric cells and exact aggregate candidate-test, Term-evaluation, and rule-enumeration counts. Keep missing/extra cells and per-call state digests in the raw output.

## Acceptance

All 15 call states must restore successfully, pass graph/rule checks, and reproduce the parent's task/reply/final-digest and behavioral-counter parity through the capture parent. The replay run must be source-locked before and after. Counter equality is a measured outcome, not a prerequisite to retain the result. If any metric differs, report it and retain the gap.

## Limits

This replay covers the primary adapter's Python-facade `run_rules` calls on one authored route. Secondary/free-standing stores, other native closure entrypoints, natural task prevalence, and scale are outside this panel. Rule mutation-protection metadata is not preserved by the current order-preserving Python binding and must be considered when interpreting a mismatch.
