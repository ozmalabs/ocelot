# Generic-fallback helper triage v1 results

Date: 2026-09-28

## Scope and findings

This source scan narrows the 191 `TermNode` variants that reach the generic child-walk fallback to the 21 variants whose evaluator arms link to crate-qualified helpers. It resolves all 23 helper paths in source and finds no lexical graph-access marker in those helper bodies. Six helper paths recursively evaluate child Terms; six use the symbol interner, and one reads the derived-operator registry. Those ambient inputs and recursively evaluated child Terms remain dependencies to account for. The other 170 fallback variants without detected crate-qualified helpers are outside this pass.

The findings support a limited statement: this helper-linked subset does not show direct graph reads in the scanned helper bodies, so graph dependencies appear to flow through child Terms or other evaluator paths. This is not proof of graph purity: source scanning can miss indirect calls, macros, callbacks, aliases, or non-graph external state. It also does not validate that every child is represented by `TermNode::children()` or that runtime access tracing observes all child evaluation. The remaining fallback variants and three external boundaries still need review and runtime controls.

## Reproduction

Run `python3 scripts/audit_term_access_fallback_helpers_v1.py`. The generated report links each variant and helper to source paths/lines and records source digests: [machine report](../../../evaluation/reports/term_access_fallback_helper_review_v1_20260928.json). The scan is deliberately labeled lexical and does not upgrade the engine-wide access-fidelity claim.
