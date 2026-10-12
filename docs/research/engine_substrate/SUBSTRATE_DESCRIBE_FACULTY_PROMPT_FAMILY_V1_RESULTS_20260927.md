# Describe faculty prompt-family construction v1 results (2026-09-27)

## Integrity and outcome

The ten-worker capture has full-source lock stability, ten distinct fresh processes, two workers per condition, and full-seed boot in every worker. The independent analysis passes capture-integrity checks. The preregistered prompt-family capability gate fails: only the canonical formulation succeeds as a scene description.

| Prompt | Final route | Faculty built? | Median request wall | Observed response / capability |
|---|---|---:|---:|---|
| `describe what you see` | `describe_scene` | Yes, +18 faculty rules (+24 total request rules) | 10.525 s | Expected three-colour scene description; resolved `describe_scene` Goal |
| `tell me what you see` | `self_report` after describe-handler attempt | Yes, +18 faculty rules (+24 total request rules) | 10.918 s | “I am Jabberwock.”; no scene-description Goal |
| `report what you observe` | `self_report` after describe-handler attempt | Yes, +18 faculty rules (+24 total request rules) | 11.096 s | “I am Jabberwock.”; no scene-description Goal |
| `describe the scene` | no action route | No | 0.209 s | Gap reply about describing “scene”; no Goal |
| `tell me about yourself` (control) | `self_report` | No scene faculty | 0.508 s | “I am Jabberwock.”; resolved `report_self` Goal |

Each condition has two fresh-process replicates with identical categorical behavior. The two paraphrases that enter `_act_describe_scene` incur the full faculty build before later falling through to self-report. This confirms that eager lazy-builder placement can charge nearly eleven seconds to a request that fails the requested scene-description capability. The third paraphrase fails earlier and does not build scene faculty. The self-identity control avoids the scene builder and succeeds on its intended route.

The control's total native rule count increases by six during ordinary request closure even though `_ensure_describe` and `_act_describe_scene` are never called. The runner's preregistered implementation gate treated total request rule delta as zero for this control; that subgate failed. The independent analysis therefore checks the intended mechanism directly (zero scene-handler and faculty-builder calls) and reports ordinary closure separately. It does not turn the failed prompt-family capability gate into a pass.

## Tractability interpretation

The 0.28 s cached-call estimate from repeated canonical prompts does not transfer even across this small, source-stratified set of formulations. Two formulations pay the approximately 11 s construction cost but return the wrong task response, while another fails quickly without construction. Cost alone therefore cannot be summarized as cheap operation plus rare, productive minting: route recognition and action success must be measured jointly with construction frequency and cost.

This is a deliberately selected five-prompt panel, not natural user traffic. It does not estimate population frequencies, show faculty rule necessity, or support general prompt robustness. The next work should repair routing/goal alignment for the failing formulations or explicitly narrow supported formulations, then rerun a frozen held-out language panel. Keep the failed outputs in that panel so regressions and any cost incurred on failed attempts remain visible.

## Artifacts

- [Preregistration](SUBSTRATE_DESCRIBE_FACULTY_PROMPT_FAMILY_V1_PREREG_20260927.md)
- [Runner](../../../scripts/substrate_describe_faculty_prompt_family_v1.py)
- [Independent analyzer](../../../scripts/analyze_substrate_describe_faculty_prompt_family_v1.py)
- [Source lock](../../../evaluation/substrate_capability/describe_faculty_prompt_family_v1_lock_20260927.json)
- [Raw capture](../../../evaluation/reports/describe_faculty_prompt_family_v1_20260927.json)
- [Analysis](../../../evaluation/reports/describe_faculty_prompt_family_v1_analysis_20260927.json)
