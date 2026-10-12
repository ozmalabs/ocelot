# Describe faculty first use and reuse v1.1 results (2026-09-27)

## Result

The corrected six-process confirmation passes all worker and source-lock gates on `world_adapter.py` `517cec9914d600ca…`. Each arm has three unique fresh processes; all six return the expected scene description twice, and every request resolves one Goal through selection, execution, and action result.

| Measure | Lazy first use median (range) | Prebuilt median (range) |
|---|---:|---:|
| Full-seed boot wall / CPU | 12.324 / 13.124 s (12.211–12.805 / 12.712–13.664) | 12.467 / 13.335 s (12.373–12.654 / 12.852–13.379) |
| Faculty setup wall / CPU | inside first request | 10.907 / 10.910 s (10.426–10.911 / 10.420–11.033) |
| First request wall / CPU | 11.112 / 11.063 s (10.524–11.182 / 10.522–11.427) | 0.388 / 0.384 s (0.377–0.398 / 0.376–0.390) |
| Cached second request wall / CPU | 0.278 / 0.279 s (0.276–0.279 / 0.278–0.280) | 0.282 / 0.283 s (0.274–0.284 / 0.275–0.284) |
| Peak RSS | 1.784 GiB (1.783–1.784) | 1.735 GiB (1.735–1.736) |

Rule deltas agree across replicates. Lazy first request adds 24 rules, corresponding to 18 faculty rules plus six conceptualizer rules; the next request adds zero. Prebuilt setup adds 18 faculty rules before the request, the first request adds six conceptualizer rules, and the next adds zero. Current RSS after lazy scene attachment is 1.345 GiB median; after explicit prebuild it is 1.413 GiB. This is phase timing on one fixture, not component ownership.

The setup cost is shifted earlier rather than avoided. The prebuilt arm's median setup plus first-request wall time is 11.295 s, close to the lazy first-request median of 11.112 s. The sums use separate arm medians, not within-process paired differences. Both arms then run cached calls in about 0.28 s. These sequential-request peaks are below the prior concurrent-call peak and are not directly comparable to that schedule.

## Pilot correction

The preceding v1 run is retained at [pilot raw report](../../../evaluation/reports/describe_faculty_first_use_reuse_v1_pilot_20260927.json). Its workers produced the expected replies and lifecycles, but the preregistered gate incorrectly expected no rules on the first request after `_ensure_describe`. All three prebuilt workers added six conceptualizer rules there. The v1.1 preregistration explicitly separates those six from the 18 faculty rules, then the independent confirmation passed. No pilot result was silently recast as a passing run.

## Interpretation boundary and next work

This supports a path-specific economic profile: expensive one-time faculty setup followed by cheap reuse, on this repeated scene-description request. It does not establish that faculty construction is rare across tasks, that the authored rules are necessary, or that prebuilding improves total runtime or memory. The current route pays setup on the first request without first observing a held-basis failure. Next evaluate independent held-out prompts and task families, count how often faculty is constructed, and run a rule-removal/ablation study with complete output and lifecycle gates. Continue the separate rule-dependency and frame-partition work before using these timings as evidence for tractable factorization.

## Artifacts

- [v1.1 preregistration](SUBSTRATE_DESCRIBE_FACULTY_FIRST_USE_REUSE_V1_1_PREREG_20260927.md)
- [runner](../../../scripts/substrate_describe_faculty_first_use_reuse_v1.py)
- [independent analyzer](../../../scripts/analyze_substrate_describe_faculty_first_use_reuse_v1.py)
- [source lock](../../../evaluation/substrate_capability/describe_faculty_first_use_reuse_v1_1_lock_20260927.json)
- [raw capture](../../../evaluation/reports/describe_faculty_first_use_reuse_v1_1_20260927.json)
- [analysis](../../../evaluation/reports/describe_faculty_first_use_reuse_v1_1_analysis_20260927.json)
