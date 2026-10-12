# Response-priority cross-family v1: result

Date: 2026-10-06  
Status: capture integrity and utility-profile gates passed; scene-description graph-parity gate failed.

## Result

The source-locked capture contains 20 unique workers: two counterbalanced pairs for each of five authored live-conversation routes. All worker inputs were stable, the current rebuilt engine passed its provenance guard, and mutation-attribution journaling was disabled. The utility profile exactly reproduced the pre-existing harvest baseline: held-self-knowledge, self-report, and unknown-word clarification passed in both arms; scene description and concern authoring failed in both arms. Priority introduced no utility regression relative to its paired global worker.

Final normalized graph fingerprints and node/edge counts matched in both pairs for four routes: held-self-knowledge, self-report, unknown-word clarification, and concern authoring. Scene description failed graph parity in both pairs even though replies matched and cardinalities were identical (25,225 nodes, 11,731 edges). The mismatch is already present before continuation and remains afterward. Both priority continuations reached zero residual without a round cap.

| Route | Baseline utility profile | Paired utility profile | Final graph parity |
|---|---|---|---|
| Scene description | Fail | Both arms fail | Fail in both pairs |
| Held self-knowledge answer | Pass | Both arms pass | Pass in both pairs |
| Self-report action | Pass | Both arms pass | Pass in both pairs |
| Unknown-word clarification | Pass | Both arms pass | Pass in both pairs |
| Concern authoring | Fail | Both arms fail | Pass in both pairs |

Response medians range from about 183–267 ms across the four shorter routes, with priority continuation around 15–17 ms versus global continuation around 7 ms. Scene description is a distinct heavy route at about 19.5–20.1 seconds because its faculty setup runs on demand. These two-replicate timings are descriptive and should not be pooled as a speed claim. The results show that the held-topic parity/cost signal transfers to four route families under this partition, while scene description exposes unresolved schedule-sensitive state on a known-failing utility route.

## Interpretation and next gate

The candidate partition preserves outcomes and final graph structure on four selected conversation routes but is not yet semantically equivalent across the five-route panel. The scene graph mismatch occurs before continuation, so the next experiment should retain graph-write provenance or typed snapshots for that route and identify the differing mutations. Do not claim cross-family parity until the scene discrepancy is explained and resolved. This authored panel still does not estimate natural-task prevalence, real frame separators, or the cost of learning new structure.

The task-oracle correction and baseline utility interpretation are documented in the [analysis amendment](SUBSTRATE_RESPONSE_PRIORITY_CROSS_FAMILY_V1_AMENDMENT_20261006.md). See the [preregistration](SUBSTRATE_RESPONSE_PRIORITY_CROSS_FAMILY_V1_PREREG_20261006.md), [runner](../../../scripts/substrate_response_priority_cross_family_v1_20261006.py), [analyzer](../../../scripts/analyze_response_priority_cross_family_v1_20261006.py), [source lock](../../../evaluation/substrate_capability/response_priority_cross_family_v1_20261006_lock.json), [capture](../../../evaluation/reports/response_priority_cross_family_v1_20261006/capture.json.gz), and [analysis](../../../evaluation/reports/response_priority_cross_family_v1_20261006/analysis.json).
