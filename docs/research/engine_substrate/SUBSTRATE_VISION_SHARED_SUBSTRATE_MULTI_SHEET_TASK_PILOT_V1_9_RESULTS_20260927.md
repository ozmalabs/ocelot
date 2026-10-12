# Shared-substrate orientation/phase response panel v1.9 results

## Capture and phase gates

The source-stable frozen-state panel passes all ten analysis checks across 50 conditions: 25 each for root-scoped and global rules. The matched prepared graph hash is restored for every condition; all declared ON pixels match observed retinal bursts; every condition records the rate-write snapshot at Retina step 23,010; and the rate equation has zero mismatches at that write point. All trajectories are explicitly classified as fixed point, exact repeated state, or 512-pass cap. Cycle outcomes include per-unit orbit statistics.

This uses the response phases specified in the [v1.9 contract](SUBSTRATE_VISION_RESPONSE_PHASE_CONTRACT_V1_9_20260927.md): rate-write response is distinct from post-settling activation, and a cycle is reported as an orbit, not a final settled value.

## Termination distribution on this one learned state

| Rule scope, including native cap replay | Fixed point | Exact cycle | Unresolved |
|---|---:|---:|---:|
| Root-scoped | 5 | 20 | 0 |
| Global | 9 | 16 | 0 |

Every case that hit the 512-pass Python trace horizon is a both-sheets-stimulated condition under global rules. At pass 512, all 32 SUnits still changed `act`; maximum per-unit change from pass 511 ranged 0.0075–0.0533. V1.9.1 replayed those eight exact initial graph/input hashes through native full closure: one reaches a fixed point and seven reach exact repeated states in 1,416–8,850 passes (1,421–8,855 progress steps). The trace horizon was an instrumentation limit; no global joint case remains unresolved under the native 1.6M progress cap.

Combining v1.9 traces with v1.9.1 replays yields root-scoped 5 fixed points/20 cycles and global 9 fixed points/16 cycles on this prepared state. Global joint cases often require thousands of passes, while their native progress work stays below 9,000 steps here. This is a termination/work observation for one root-scoped-adapted graph, not an asymptotic cost or scope-safety result. Cycle periods for the long native replays are not exposed by the current report API.

## Single-sheet orientation/phase response

At the rate-write snapshot, B-only rate sums are identical under both rule scopes for all eight tested gratings, consistent with the shared input and adapted weights before subsequent cross-sheet settling:

| Orientation | Phase 0 | Phase π/2 |
|---:|---:|---:|
| 0° | 0.000 | 0.000 |
| 45° | 18.956 | 14.518 |
| 90° | 0.000 | 0.000 |
| 135° | 19.946 | 10.897 |

This is a small stimulus panel on the already learned bank, not new learning or a generalization estimate. Post-settle outcomes differ: single-sheet cases may reach fixed points or cycles depending on stimulus and scope.

## Limits and next gate

This result supports three bounded claims: the rate-write equation is valid at its measured phase; the frozen bank distinguishes some orientations/phases in this panel; and all eight global joint-sheet conditions reach a fixed point or exact cycle under native closure once the pass-trace horizon is extended. It does not estimate how often natural tasks exhibit these structures or whether learned frames generalize across seeds.

V1.9.1 has completed the native horizon extension for all eight cases. Next repeat the phase-aware panel on at least three independently adapted seeds and add independently authored visual task families; retain the same response contract and report response correctness separately from termination and work before estimating scope-locality prevalence or CPU cost distributions.

## Evidence

- [Raw summary and pass states](../../../evaluation/reports/substrate_vision_shared_substrate_multisheet_task_pilot_v1_9_20260927.json)
- [Passwise trace](../../../evaluation/reports/substrate_vision_shared_substrate_multisheet_task_pilot_v1_9_20260927.trace.jsonl)
- [Independent analysis](../../../evaluation/reports/substrate_vision_shared_substrate_multisheet_task_pilot_v1_9_analysis_20260927.json)
- [Runner](../../../scripts/substrate_vision_shared_substrate_multisheet_task_pilot_v1_9.py)
- [Analyzer](../../../scripts/analyze_substrate_vision_shared_substrate_multisheet_task_pilot_v1_9.py)
- [Preregistration](SUBSTRATE_VISION_SHARED_SUBSTRATE_MULTI_SHEET_TASK_PILOT_V1_9_PREREG_20260927.md)
- [Response-phase contract](SUBSTRATE_VISION_RESPONSE_PHASE_CONTRACT_V1_9_20260927.md)
- [Source lock](../../../evaluation/substrate_capability/vision_shared_substrate_multisheet_task_pilot_v1_9_lock_20260927.json)
- [V1.9.1 native extension results](SUBSTRATE_VISION_SHARED_SUBSTRATE_MULTI_SHEET_TASK_PILOT_V1_9_1_RESULTS_20260927.md)

This is one seed, one adapted graph, four orientations, two phases, and two rule variants. It is not a natural-task prevalence or scale estimate.
