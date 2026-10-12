# Term access-dependency coverage v1 results

Date: 2026-09-28

## Generated inventory

The source crosswalk enumerates all 237 `TermNode` variants and finds one evaluator arm and one `children()` case for every variant. It classifies the access collector as 36 unconditional wildcard readers, 5 finite-key readers, 5 conditional finite-or-wildcard readers, and 191 variants reaching the generic child-walk fallback. It associates 61 variants with crate-qualified helpers and follows helper bodies/local or qualified callees to depth four using lexical source markers. This identifies 29 direct or transitive graph/trace helper paths; all 29 map to an explicit finite, conditional, or wildcard access declaration. Fifteen built-in access branches and 30 dynamic helper families have source notes. Three additional Terms are now classified separately as external boundaries: `ReadFile`, `UseTool`, and `ProgCallExtern`.

The generator's five source-crosswalk checks pass, including no unclassified direct graph access or detected graph helper path. This is not a proof of completeness: helper discovery is lexical, call traversal is depth-limited, local helpers in every module are not fully indexed, and no host-tool/file behavior is executed. The 191 generic-fallback variants are not thereby proven graph-pure. Next review those fallbacks by evaluator arm and value/host boundary, classify every `reads_any`/`RuleKey` source, and compare trace kinds/sites against those declarations. Select positive and negative operation fixtures from the remaining unreviewed set rather than inferring safety from the absence of mismatches in the two authored prompts.

Artifacts: [generator](../../../scripts/audit_term_access_dependency_coverage_v1.py), [machine-readable crosswalk](../../../evaluation/reports/term_access_dependency_coverage_v1_20260928.json), [focused Term audit protocol](SUBSTRATE_TERM_ACCESS_DEPENDENCY_AUDIT_V1_PREREG_20260928.md), and [replay results](SUBSTRATE_TERM_ACCESS_DEPENDENCY_AUDIT_V1_RESULTS_20260928.md).
