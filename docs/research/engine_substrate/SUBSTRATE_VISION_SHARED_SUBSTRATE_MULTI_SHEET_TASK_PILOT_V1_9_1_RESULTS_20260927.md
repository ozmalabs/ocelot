# V1.9.1 native closure replay of global joint-sheet cases

## Outcome

All seven independent checks pass for the replay of the eight global both-sheet cases that hit v1.9's 512-pass Python trace horizon. The eight native runs begin from the exact initial input graph hashes captured in v1.9, including the exact π/2 stimuli. All eight reach either a fixed point or exact repeated-graph state under the native cycle detector within the 1.6M progress ceiling.

| Orientation | Phase | Native outcome | Passes | Progress steps |
|---:|---:|---|---:|---:|
| 0° | 0 | Fixed point | 1,497 | 1,500 |
| 0° | π/2 | Exact repeated state | 2,174 | 2,178 |
| 45° | 0 | Exact repeated state | 5,232 | 5,237 |
| 45° | π/2 | Exact repeated state | 1,416 | 1,421 |
| 90° | 0 | Exact repeated state | 1,788 | 1,792 |
| 90° | π/2 | Exact repeated state | 2,844 | 2,848 |
| 135° | 0 | Exact repeated state | 8,850 | 8,855 |
| 135° | π/2 | Exact repeated state | 2,276 | 2,281 |

Thus the 512-pass outcomes in the v1.9 Python trace were instrumentation horizons, not unresolved engine termination: one case reaches a fixed point and seven enter exact cycles when native closure is allowed to continue. The native report does not expose cycle period, so this replay does not add period estimates. The cycle terminal graph is a point on an orbit, not a converged output.

The first attempted replay rounded π/2 to the six-decimal condition label, producing two different initial graph hashes. That capture was excluded. The final replay reconstructs π/2 from the preregistered exact value; the independent hash gate confirms all eight initial graphs match v1.9 exactly.

## Combined termination distribution

Combining v1.9's root-scoped traces and global single-sheet/blank conditions with these exact native replays gives the following result for this one prepared graph:

| Rule scope | Fixed point | Exact cycle | Unresolved cap |
|---|---:|---:|---:|
| Root-scoped | 5 | 20 | 0 |
| Global | 9 | 16 | 0 |

This is not a prevalence estimate. It shows that the same learned state has many exact cycles under both modes and that global joint stimulation often takes thousands of passes before exact termination. Across these eight cases, native progress work remains small in absolute terms for this graph (1,421–8,855 steps), but no scaling inference follows from one anatomy.

## Evidence

- [Raw native replay](../../../evaluation/reports/substrate_vision_shared_substrate_multisheet_task_pilot_v1_9_1_20260927.json)
- [Independent analysis](../../../evaluation/reports/substrate_vision_shared_substrate_multisheet_task_pilot_v1_9_1_analysis_20260927.json)
- [Runner](../../../scripts/substrate_vision_shared_substrate_multisheet_task_pilot_v1_9_1.py)
- [Analyzer](../../../scripts/analyze_substrate_vision_shared_substrate_multisheet_task_pilot_v1_9_1.py)
- [Amendment](SUBSTRATE_VISION_SHARED_SUBSTRATE_MULTI_SHEET_TASK_PILOT_V1_9_1_AMENDMENT_20260927.md)
- [Source lock](../../../evaluation/substrate_capability/vision_shared_substrate_multisheet_task_pilot_v1_9_1_lock_20260927.json)
- [V1.9 panel results](SUBSTRATE_VISION_SHARED_SUBSTRATE_MULTI_SHEET_TASK_PILOT_V1_9_RESULTS_20260927.md)
