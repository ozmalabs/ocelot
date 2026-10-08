# Graph-authored episodic memory task pilot — 2026-09-25

## Result

The frozen task pilot passed all preregistered mechanism checks. Six known route episodes were recalled exactly in each of the 0, 18, and 72 unrelated-episode arms: **18/18 exact unique-cue recalls**, all with `recalled` provenance and `not_observed` status. All six same-cue collision queries reported confidence 0.5 and uncertainty 0.5; the fixed 0.75 evaluator threshold abstained on all six, while the retrieved route was one of the two stored alternatives. Never-seen cues were unanswered in every arm. The reset-memory arm returned explicit `insufficient_information` on all 13 queries. The no-memory arm returned no candidate on all 13 queries.

## Cost observations

| Arm | Episode records | Median query tick | Max query tick | Acquisition tick | Peak worker RSS |
|---|---:|---:|---:|---:|---:|
| Memory, no distractors | 6 | 0.171 ms | 0.188 ms | 0.462 ms | 35.3 MiB |
| Memory + 18 unrelated | 24 | 0.349 ms | 0.371 ms | 0.704 ms | 35.0 MiB |
| Memory + 72 unrelated | 78 | 1.977 ms | 2.019 ms | 2.468 ms | 35.8 MiB |
| Cue collision + 18 unrelated | 30 | 0.360 ms | 0.382 ms | 0.637 ms | 35.0 MiB |
| Reset memory | 0 | 0.134 ms | 0.417 ms | 0 | 35.2 MiB |
| No memory seed | 0 | 0.095 ms | 0.252 ms | 0 | 26.6 MiB |

Boot was about 11.5–11.9 ms with the episodic rules loaded and 0.16 ms for the empty profile. These timings are single-run descriptive measurements from fresh child processes, and RSS includes Python/native import baseline. The query tick cost rises with the tested episode count; this is not enough scale or repetition to fit a complexity curve or identify the dominant cost.

## Interpretation

This supplies task-linked evidence for the **current authored episodic cue-retrieval path**: it retrieves a known event under these synthetic unrelated additions, represents cue ambiguity as lower confidence, and abstains at the preregistered threshold. The paired reset/no-memory controls show that the answer is not produced without acquired events under this task wiring. The ambiguous controls count as correct only for the abstention behavior; they provide no task answer.

It does not test natural-language or semantic cues, task utility outside this hand-authored route schema, forgetting, retention/eviction, consolidation, restart persistence, realistic memory sizes, distribution shift, or learned frame locality. The cues are exact unique keys. The alternatives have deliberately separated salience/value and the observed confidence is mechanism behavior, not a calibration estimate. This does not upgrade general memory or general capability status.

## Reproducibility and artifacts

- Frozen protocol: [`SUBSTRATE_EPISODIC_MEMORY_TASK_PREREG_20260925.md`](SUBSTRATE_EPISODIC_MEMORY_TASK_PREREG_20260925.md)
- Pre-run input lock: [`episodic_memory_task_pilot_lock_20260925.json`](../../../evaluation/substrate_capability/episodic_memory_task_pilot_lock_20260925.json)
- Runner: [`substrate_episodic_memory_task_pilot.py`](../../../scripts/substrate_episodic_memory_task_pilot.py)
- Independent raw-record audit: [`analyze_substrate_episodic_memory_task_pilot.py`](../../../scripts/analyze_substrate_episodic_memory_task_pilot.py)
- Raw records: [`substrate_episodic_memory_task_pilot_20260925.json`](../../../evaluation/reports/substrate_episodic_memory_task_pilot_20260925.json)
- Independent analysis: [`substrate_episodic_memory_task_pilot_analysis_20260925.json`](../../../evaluation/reports/substrate_episodic_memory_task_pilot_analysis_20260925.json)

The lock records a dirty worktree. All 12 frozen input hashes matched during the independent audit. Development probes were run before preregistration and are disclosed in the preregistration; they are not included in the scored sample.

## Next E1 measurements

Run fresh preregistered tasks with paraphrased/partial cues and controlled near-neighbor distractors; measure retention over intervening updates and explicit eviction/capacity behavior; test persistence/restart and corruption recovery for episodic records; vary payload and graph size over repeated fresh-process workers; and compare acquisition plus retrieval costs against no-memory, reset-memory, and a simple exact-key host baseline. Keep these separate from long-term ShapeIndex evaluations.
