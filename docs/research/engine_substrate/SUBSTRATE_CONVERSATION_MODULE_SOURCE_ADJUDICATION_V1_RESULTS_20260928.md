# Conversation module source adjudication v1

Date: 2026-09-28  
Status: reviewed source-use grouping of the 37 task-observed Python modules that lacked direct capability-map links.

## Outcome

The crosswalk found 40 distinct called modules across five authored conversation tasks; three already had map links and 37 did not. All 37 were assigned once to a proposed map disposition using the locked source inventory's module docstring, symbol list, source hash, and task-condition footprint. The dispositions are conservative grouping decisions, not claims of causal necessity or independent capabilities.

| Proposed grouping | Count | Proposed map action |
|---|---:|---|
| `language_communication` | 25 | Group under a proposed language, grounded reference, and communicative production capability area; keep lifecycle identity evidence in its existing row. |
| `code_authoring` | 2 | Link as a distinct code-authoring subpath under the existing program synthesis/induction area, with graph-authored codebook growth kept separate from general synthesis results. |
| `frame_context_representation` | 4 | Create a separate graph-resident concept/frame/context representation area or link to a reviewed ontology row; do not count these as evidence that dependency cuts have low width. |
| `external_and_perceptual_adapters` | 2 | Link fetch dispatch to tools/external I/O and upload-text decoding to vision/perception; preserve their different effect boundaries. |
| `lexical_reference_support` | 4 | Link as lexical/reference data and loader support for the language area; do not create separate general capability scores for storage or seed registration. |

Current-source comparison found 1 path changed since the locked inventory: `domains/comprehend_text.py`. Keep its locked-run observation, but refresh its current-source source-map adjudication before linking it as present-day behavior.

The most important tractability boundary is explicit: concept/frame/context representation modules are not evidence of low dependency width or a cheap cut. Lexical slabs, seed registration, and lookup corpora are support surfaces and should not be counted as stand-alone reasoning capabilities. Code authoring and codebook growth remain distinct from enumerative program synthesis.

## Evidence and reproducibility

The machine record stores all 37 module paths, locked/current file hashes, observed condition sets, inventory docstrings/symbols, proposed group, and rationale. Its inputs are hash-linked to the [module activation crosswalk](../../../evaluation/reports/conversation_task_module_source_crosswalk_v1_20260928.json) and the [Python source census](../../../evaluation/substrate_capability/python_source_coverage_audit_v1_1_20260928.json). Reproduce with `python3 scripts/adjudicate_substrate_conversation_module_sources_v1.py`.

Next: update capability rows from this adjudication only after current-source review of changed files; rerun the source-coverage census as a new version; then select fresh task families for activation profiling. The full trace remains limited to conversation tasks and does not support a general substrate capability distribution.

## Current-source follow-up

The source drift noted in this adjudication was addressed by the locked current-source v1.2 repeat, and the 37 proposed source groupings were materialized as capability-map links. The v1.2 source census reports 69/833 directly linked Python files; its independent task-module join finds all 40 modules called by the five conversation tasks directly linked. This updates the map and resolves the conversation panel's module-link gap, while the other 764 Python files remain outside direct map links and need separate classification. See [v1.2 activation results](SUBSTRATE_CONVERSATION_TASK_MODULE_ACTIVATION_V1_2_RESULTS_20260928.md), [source census](SUBSTRATE_PYTHON_SOURCE_COVERAGE_AUDIT_V1_2_RESULTS_20260928.md), and [current crosswalk](../../../evaluation/reports/conversation_task_module_source_crosswalk_v1_2_20260928.json).
