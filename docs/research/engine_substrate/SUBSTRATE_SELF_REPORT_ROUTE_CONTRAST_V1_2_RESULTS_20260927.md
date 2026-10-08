# Self-report route contrast panel v1.2 results

Date: 2026-09-27

## Status

This is the corrected full-runtime panel. The frozen snapshot locks source/seed files, all 36 `data/slabs` files, and all 3,355 Python modules under `scripts/`, including `scripts/collapse_engine.py`. It records 30 fresh PIDs, three workers per stimulus, stable locks at every boundary, and exact protocol/runner hashes. The source/runtime provenance gates pass.

The original order-sensitive within-stimulus graph-digest gate flagged stimulus J (`what is organisation?`): reply/route/comprehension were identical in all three workers, but two digests occurred, so the original analyzer correctly reports `all_checks_pass=false`. A source-locked follow-up captured the differing node attributes and found the only difference was order inside `Interlocutor.believed_concepts.__fset__`; after canonical sorting of tagged set values, all three full-graph digests match. The graph-state discrepancy is resolved as serialization-order variance, while the original failed gate and analysis remain preserved.

## Observed capabilities

| Stimulus | Stable behavior in the locked snapshot |
|---|---|
| A `report your organisation` | `self_report`; gives an inventory of 12 held areas, all 3/3 |
| B `describe your organisation` | Same `self_report` route and inventory, 3/3 |
| C `tell me about your organisation` | Same `self_report` route and inventory, 3/3 |
| D `report your purpose` | `self_report`; generic reply `I am Jabberwock.`, 3/3 |
| E `describe yourself` | `self_report`; same generic reply, 3/3 |
| F `tell me about yourself` | `self_report`; same generic reply, 3/3 |
| G `what do you do?` | `instruction_gap_report_graph`; says it holds no faculty for parsed target `what 'you'`, 3/3 |
| H `what does florpification mean?` | wordplay dispatch but no communicative response, 3/3 |
| I `florpification is a new word` | wordplay dispatch and an instruction-check deferral, 3/3 |
| J `what is organisation?` | table dispatch but no communicative response, 3/3 behavior; graph digest varies in one of three records |

All workers load 731 manifests and repeat the same 11 seed-load failures. `organisation` is a known noun under the locked Wiktionary POS slab and does not trigger coinage. Thus the earlier wordplay-preemption finding was an environment-lock artifact. The detailed, stable organisation report is a real existing capability in this frozen full-runtime source state; the account vocabulary itself appears selective because “report your purpose” receives only a generic identity string.

## Interpretation limits

This is a ten-utterance authored panel, not an estimate of natural-task frequency or general capability. Source identity is exact in the lock and may not match later worktree state. The eleven failed manifests co-occur but were not intervened on here.

The previous v1/v1.1 route results used incomplete snapshots: v1 omitted runtime slabs; v1.1 omitted the imported `collapse_engine` module. Their route/reply findings are superseded. The provider-scope hunk experiment also used the incomplete environment and cannot support behavioral causality for the provisioned system.

Reusable helpers now exist in `scripts/measurement_provenance.py` and `scripts/measurement_graph_digest.py`. Independent path-list rehashing with `lock_files` reproduces the panel's exact 3,355 script hashes and 36 slab hashes. Set-wrapper normalization in the graph helper reproduces the resolved J graph equality.

## Next

1. Make set-aware canonicalization the standard graph parity operation; the existing helper's digest preserves serialized set order.
2. Test the 12-item surface cap separately from structured inventory completeness across larger inventories, retaining the prior scale data as its own source-bound result.
3. Expand the panel across non-self-report task families; the ten stimuli here do not measure general substrate capability.
4. Use source/seed/runtime/script closure plus import tracing as the default evaluation lock template.

## Artifacts

- [v1 protocol](SUBSTRATE_SELF_REPORT_ROUTE_CONTRAST_V1_PREREG_20260927.md)
- [v1.1 runtime-asset amendment](SUBSTRATE_SELF_REPORT_ROUTE_CONTRAST_V1_1_AMENDMENT_20260927.md)
- [v1.2 imported-module amendment](SUBSTRATE_SELF_REPORT_ROUTE_CONTRAST_V1_2_AMENDMENT_20260927.md)
- [v1.3 set-order amendment](SUBSTRATE_SELF_REPORT_ROUTE_CONTRAST_V1_3_AMENDMENT_20260927.md)
- [Runner](../../../scripts/probe_self_report_route_contrast_v1_2.py)
- [Independent analyzer](../../../scripts/analyze_self_report_route_contrast_v1_2.py)
- [Full source/runtime lock](../../../evaluation/substrate_capability/self_report_route_contrast_v1_2_lock_20260927.json)
- [Raw 30-worker capture](../../../evaluation/reports/self_report_route_contrast_v1_2_20260927.json)
- [Analysis](../../../evaluation/reports/self_report_route_contrast_v1_2_analysis_20260927.json)
- [J graph canonical follow-up analysis](../../../evaluation/reports/route_j_graph_repeat_diagnostic_v1_1_canonical_analysis_20260927.json)
- [Measurement provenance helper](../../../scripts/measurement_provenance.py)
- [Canonical graph-digest helper](../../../scripts/measurement_graph_digest.py)
