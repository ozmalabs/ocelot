# Live self-report matcher cost v1.9 implementation amendment

Date: 2026-09-27 local

This capture extends the v1.8 self-report lifecycle fixture with native per-rule/per-clause matcher metadata, explicit unattributed work, and the v1.3 ambiguity semantics. The audit is reset and enabled only around each live lifecycle producer event. All source/native inputs, including `scale_audit.rs`, `rewrite.rs`, `substrate.rs`, `graph_rules.rs`, and the installed extension/build record, are fingerprinted. No matcher, rule, or task behavior is changed by the measurement harness.

See [the preregistration](SUBSTRATE_LIVE_SELF_REPORT_MATCHER_COST_V1_9_PREREG_20260927.md).
