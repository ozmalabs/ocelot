# Concern-prompt grounding diagnostic v1 results

**Run:** 2026-09-28; six fresh full-seed workers across three matched wording arms.  
**Protocol:** [preregistration](SUBSTRATE_CONCERN_PROMPT_GROUNDING_DIAGNOSTIC_V1_PREREG_20260928.md).  
**Evidence:** [raw capture](../../../evaluation/reports/concern_prompt_grounding_diagnostic_v1_20260928.json), [independent analysis](../../../evaluation/reports/concern_prompt_grounding_diagnostic_v1_analysis_20260928.json), [input/source lock](../../../evaluation/substrate_capability/concern_prompt_grounding_diagnostic_v1_lock_20260928.json), [runner](../../../scripts/substrate_concern_prompt_grounding_diagnostic_v1.py), [analyzer](../../../scripts/analyze_substrate_concern_prompt_grounding_diagnostic_v1.py).

## Result

All six workers completed in unique processes, two per arm; all 11 independent integrity and route checks pass. Parent inputs and every worker's source/runtime locks remained stable. In all three arms, both workers classify the utterance as an instruction with `typed_unresolved_action_dependency`, return via `ask_back`, create zero goals, and record no concern action or teacher call.

| Wording arm | Clarification returned in both workers | Ask-back | Goals | Concern actions |
|---|---|---:|---:|---:|
| “the two letters” (baseline) | `two` | 2/2 | 0, 0 | 0/2 |
| “the pair of letters” | `place` | 2/2 | 0, 0 | 0/2 |
| “letter A and letter B” | `B` | 2/2 | 0, 0 | 0/2 |

The clarified token changes with the wording, but the pre-action unresolved-dependency route does not. Therefore the baseline result is not specifically explained by the token `two`; all three phrasings fail before the concern action. Instrumented task wall medians were 225 ms, 234 ms, and 220 ms in the order above; these descriptive values include booted-worker instrumentation and are not service-cost estimates.

## Interpretation and limits

This narrows the observed concern-task issue to a broader interpretation/grounding gap for the three tested comparison phrasings. It does not establish which relation or trial dependency is unresolved, because the probe changes the surface wording but does not inspect or manipulate the resulting candidate referents. The concern-authoring faculty still was not reached, so its capability remains untested. The next measurement must provide an independently verified grounded representation of the same comparison task, then test the concern action separately from natural-language interpretation.

This is one task, three authored phrasings, and two repeats each. It estimates neither general language capability nor prompt-family prevalence. No source, seed, native code, or runtime behavior was changed.
