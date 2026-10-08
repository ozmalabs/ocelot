# Two-sheet current-source vision scale sweep v2.3 results

## Result

The current-source run completed 96 isolated cells and passes all eight analysis gates: three seeds × four frame sizes × two fold scopes × two B-sheet activation settings × counter-off/on. All 48 paired counter-off/on trials produce exactly the same progress and SUnit outputs. All 96 outputs match the independent settlement equation within 1e-12, all root memberships are disjoint and exact, all closure runs remain below the 10,000 work cap, and the native audit totals reconcile with per-rule counters.

Each output's direct aggregate read scope is all `T` SUnits under the global fold and `T/2` units under root scoping. The measured `term_unit:NodesOfType` counter follows `T(2T+1)` globally, while root-scoped counts are `T`; at 512 SUnits it records 524,800 versus 512. **That 1,025× figure is specific to this counter.** The counter counts `NodesOfType` collection visits but does not count returned items from the root-scoped `Neighbours` source, so it is not a like-for-like total-work ratio. The more comparable total Term-evaluation counts at 512 units are 1,080,352 global versus 557,088 scoped (1.94×). Counter-off closure-call time is 24.846 ms versus 11.391 ms (2.18×). The rule-level reason remains clear: global output reads both sheets' SUnits for its mean; the root-scoped clone reads only its target Retina's SUnits.

| Side per sheet | Total SUnits | Direct aggregate inputs per output (global / scoped) | `NodesOfType` visits (global / scoped) | Total Term evaluations (global / scoped) | Closure median (global / scoped) | Median worker peak RSS |
|---:|---:|---:|---:|---:|---:|---:|
| 2 | 8 | 8 / 4 | 136 / 8 | 616 / 504 | 0.092 / 0.094 ms | 42 MiB |
| 4 | 32 | 32 / 16 | 2,080 / 32 | 5,824 / 3,840 | 0.230 / 0.171 ms | 42 MiB |
| 8 | 128 | 128 / 64 | 32,896 / 128 | 73,120 / 40,608 | 1.844 / 0.988 ms | 44 MiB |
| 16 | 512 | 512 / 256 | 524,800 / 512 | 1,080,352 / 557,088 | 24.846 / 11.391 ms | 51 MiB |

The closure timings are audit-counter-off medians across three seeds and two B states. At the largest size, root scoping reduces measured closure-call wall time by about 54% for this factor. This is not a general speedup claim: the frame's within-sheet mean remains global, so the root-scoped variant still has a dense all-to-all dependency among SUnits within each sheet. Counter instrumentation increases median call wall time by about 3.1× global and 3.4× scoped at size 16; counter-on timings are therefore not used as engine latency.

Peak RSS grows from about 42 MiB to 51 MiB across this small sweep. These isolated-process values include Python/runtime startup and fixture construction, so the small delta is not an estimate of per-node storage. The task is a controlled one-rule arithmetic fold with 512 total SUnits at its largest, not a natural workload or a large graph.

## Interpretation

This result strengthens the cheap-cut argument and makes its condition concrete: a small root boundary does not make execution local if a rule still evaluates a global fold across roots. Rewriting the fold to respect the frame reduces cross-root traversal and improves measured call time while preserving the same local equation on these test states. Conversely, root scoping alone does not remove dense work inside each sheet. A next scaling experiment should increase local frame size while also recording dependency width, and then repeat on a second task family with independently authored rules.

## Reproduction artifacts

- Protocol: [v2.3 preregistration](SUBSTRATE_VISION_TWO_SHEET_CURRENT_SOURCE_SCALE_V2_3_PREREG_20260927.md)
- Runner and analyzer: [96-cell runner](../../../scripts/substrate_vision_two_sheet_current_source_scale_v2_3.py), [independent analysis](../../../scripts/analyze_substrate_vision_two_sheet_current_source_scale_v2_3.py)
- Raw report and isolated cells: [aggregate](../../../evaluation/reports/vision_two_sheet_current_source_scale_v2_3_20260927.json), `evaluation/reports/vision_two_sheet_current_source_scale_v2_3_cells/`
- Analysis and source lock: [analysis](../../../evaluation/reports/vision_two_sheet_current_source_scale_v2_3_analysis_20260927.json), [lock](../../../evaluation/substrate_capability/vision_two_sheet_current_source_scale_v2_3_lock_20260927.json)
