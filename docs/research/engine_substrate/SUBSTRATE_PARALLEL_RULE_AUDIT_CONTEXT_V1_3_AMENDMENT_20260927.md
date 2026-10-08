# Parallel matcher rule-audit context v1.3 implementation amendment

Date: 2026-09-27 local

The v1.2 stable capture exposed audit identity reuse: a numeric ID was associated with more than one matcher shape during a request window, so later metadata could not validate earlier counts. v1.3 adds a request-window ambiguity set. On the first conflicting registration, the ID is permanently marked ambiguous, existing per-rule and per-clause candidate counts for that ID are removed, and those candidate tests move to `cand_tested_unattributed`. Subsequent candidate tests under that ID remain unattributed. The matcher and task behavior are unchanged. The gate requires exact conservation and verifies that ambiguous identities have no remaining attributed rows. See [the preregistration](SUBSTRATE_PARALLEL_RULE_AUDIT_CONTEXT_V1_3_PREREG_20260927.md).

An analyzer-only correction after capture changed the top-rule summary from an incorrectly pooled cross-request mapping to separate request A/B rankings. It does not change raw inputs, worker output, candidate totals, conservation, or any gate; the analysis output records the corrected analyzer hash. The first v1.2 source-race attempt remains excluded as documented in the v1.2 amendment.
