# Current-source replication of string PBE contrast pilot

**Outcome:** all 18 tasks completed under the four registered arms on the current source and rebuilt native extension. This is a source-drift replication on an already inspected suite, not new capability evidence.

## Reproduction and source drift

The original contrast pilot's lock still matches its recorded run. Relative to that lock, the current worktree differs in the P4 synthesis adapter, retrieval adapter, native extension, and native build manifest. The current-source wrapper locked the exact current versions before execution, ran the original benchmark logic without changing the fixture, arms, or candidate policy, wrote a new raw report, and ran a separate expected-output/replay audit. The earlier report and audit remain intact.

## Results

All four current-source arms exactly match the original report task by task on outcome, status, and construction. Main and its independent replay also match. The independent analyzer found 18 tasks, checked 126 fixture input/output pairs, and reported zero fixture errors and zero replay-outcome mismatches.

| Arm | Held-out passes | Accepted wrong | Gaps | Candidate evaluations |
|---|---:|---:|---:|---:|
| Main | 5/18 | 6 | 7 | 1,400,000 |
| Retrieval bypass | 5/18 | 6 | 7 | 1,974,447 |
| Retrieval bypass + 500k ceiling | 5/18 | 6 | 7 | 4,074,447 |
| Main replay | 5/18 | 6 | 7 | 1,400,000 |

Neither retrieval nor the declared escalation changes held-out outcomes on this suite. The result strengthens confidence that the prior failure/pass pattern is stable across the measured source/build drift. It cannot identify which individual source change preserves behavior, and the suite remains generated, small, and limited to supported string operations. Six accepted wrong programs remain a clear gap between revealed-example acceptance and held-out correctness.

See the [locked current-source protocol](SUBSTRATE_STRING_PBE_CONTRAST_CURRENT_SOURCE_PREREG_20260925.md), [runner](../../../scripts/substrate_string_pbe_contrast_current_source.py), [pre-run lock](../../../evaluation/substrate_capability/string_pbe_contrast_current_source_lock_20260925.json), [raw report](../../../evaluation/reports/substrate_string_pbe_contrast_current_source_20260925.json), and [independent analysis](../../../evaluation/reports/substrate_string_pbe_contrast_current_source_analysis_20260925.json). The original [pilot report](SUBSTRATE_STRING_PBE_CONTRAST_RESULTS.md) and [lock](../../../evaluation/substrate_capability/string_pbe_contrast_lock_20260925.json) preserve its original provenance.

## Next gate

The declared adversarial-near-retrieval, retrieval-bypass, budget-escalation, and replay comparison has now been executed and source-currently replicated. The next P4 gate should move beyond known string primitives: use a separately generated family with compositions or operators not directly represented by the current exemplar templates, compare full P4 with no-retrieval and frozen/codebook controls, and report unresolved residuals and mint/adoption separately. Do not tune on this contrast suite and reuse it as held out.
