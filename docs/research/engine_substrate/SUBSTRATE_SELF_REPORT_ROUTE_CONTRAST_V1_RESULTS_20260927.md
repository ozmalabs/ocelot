# Self-report route contrast panel v1 results

Date: 2026-09-27

## Result and source identity

**Measurement status: superseded.** This run locked source files and seeds but not the runtime `data/slabs` reference tables. The [v1.1 amendment](SUBSTRATE_SELF_REPORT_ROUTE_CONTRAST_V1_1_AMENDMENT_20260927.md) shows those tables determine whether `organisation` is known; therefore the v1 wordplay/arbitration outcomes are an incomplete-environment artifact and must not be used as provisioned-substrate capability evidence.

The preregistered panel passed all 8 independent checks: 30 fresh PIDs, three replicates for each of ten utterances, stable source locks at every worker/driver boundary, complete records, and exact within-stimulus behavioral/graph repetition. This result applies to the locked snapshot whose `substrate/boot_all.py` hash is `9b9c2ac025f0fea54a9b463e818737e7d765bcce351d69a0572b9ede746bf494`; it must not be described as the live worktree's current behavior. During a separate worktree run, `boot_all.py` and `boot_profiles.py` changed, causing the provenance gate to fail. The snapshot is retained as a reproducible historical source state.

## Outcomes

| Stimuli | Repeatable outcome (3/3 each) |
|---|---|
| A–C: three request forms containing `organisation` | comprehension `statement`, dispatch `wordplay`, no route; generic instruction-gap reply |
| D–F: `report your purpose`, `describe yourself`, `tell me about yourself` | comprehension `instruction`, route `ask_back` on unresolved verb (`report`, `describe`, `tell`) |
| G: `what do you do?` | `instruction_gap_report_graph`; unsupported target `what` |
| H–I: definition question and statement with `florpification` | wordplay dispatch; respectively no generated response and a deferral response |
| J: `what is organisation?` | wordplay dispatch; no generated response |

Each worker loaded 731 seed manifests and reproduced the same 11 boot failures. Graph size and semantic digest repeat within each stimulus. The positive coinage control proves the classifier path can fire; the missing/deferral responses show that classification alone does not establish a working conversational capability.

## Interpretation

On this exact source snapshot, wordplay recognition preempts the whole utterance when it finds an OOV suffix-bearing token, even in request syntax. Removing that preemption in the earlier one-worker intervention reached instruction comprehension but asked back about `report`. The action-head and question-target gaps therefore remain distinct from token-level arbitration.

This is a ten-item authored panel, not a prevalence estimate or tractability result. It does not establish current-worktree behavior, and the changed-source worktree capture is excluded because its lock failed. See the [v1.1 amendment](SUBSTRATE_SELF_REPORT_ROUTE_CAUSAL_INTERVENTION_V1_1_AMENDMENT_20260927.md) for a source-change follow-up.

## Artifacts

- [Protocol](SUBSTRATE_SELF_REPORT_ROUTE_CONTRAST_V1_PREREG_20260927.md)
- [Runner](../../../scripts/probe_self_report_route_contrast_v1.py)
- [Independent analyzer](../../../scripts/analyze_self_report_route_contrast_v1.py)
- [Source lock](../../../evaluation/substrate_capability/self_report_route_contrast_v1_lock_20260927.json)
- [Raw 30-worker capture](../../../evaluation/reports/self_report_route_contrast_v1_20260927.json)
- [Analysis](../../../evaluation/reports/self_report_route_contrast_v1_analysis_20260927.json)

## Next

The provider-scope selection hunk, tested alone against this locked baseline, changes neither the loaded seed set nor the route. Test the subsequent content-selection and Microtheory scaffold-retention changes as separate interventions, then rerun a compact route panel on a stable latest-source snapshot before making current capability claims.
