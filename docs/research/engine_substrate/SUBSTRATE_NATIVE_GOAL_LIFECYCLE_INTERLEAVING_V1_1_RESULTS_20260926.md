# Native Goal lifecycle interleaving v1.1 results

## Confirmatory result

Three fresh full-seed workers pass the six-checkpoint A/B interleaving sequence under the amended native rules. Each event has the intended single owner; both Goals follow their own selection → execution → result transitions and finish resolved, closed, and inactive. A selection event with no owner transitions neither Goal. A deliberately ambiguous selection event with two `for_goal` edges is detected but transitions neither Goal.

The independent analyzer confirms lock integrity, source stability, three distinct process IDs, all six expected checkpoints, and both negative-owner controls. The original v1 capture showed both Goals transitioning from one multi-owner event; v1.1 demonstrates the amended rule suppresses that behavior while preserving valid interleaving semantics.

This is native rule behavior on an explicit graph fixture. It does not establish thread safety, live producer behavior during true concurrent execution, arbitrary scheduler completeness, or performance.

## Artifacts

- Original preregistration: [`SUBSTRATE_NATIVE_GOAL_LIFECYCLE_INTERLEAVING_PREREG_20260926.md`](SUBSTRATE_NATIVE_GOAL_LIFECYCLE_INTERLEAVING_PREREG_20260926.md)
- v1.1 amendment: [`SUBSTRATE_NATIVE_GOAL_LIFECYCLE_INTERLEAVING_V1_1_AMENDMENT_20260926.md`](SUBSTRATE_NATIVE_GOAL_LIFECYCLE_INTERLEAVING_V1_1_AMENDMENT_20260926.md)
- Runner: [`substrate_native_goal_lifecycle_interleaving_v1_1.py`](../../../scripts/substrate_native_goal_lifecycle_interleaving_v1_1.py)
- Independent analyzer: [`analyze_substrate_native_goal_lifecycle_interleaving_v1_1.py`](../../../scripts/analyze_substrate_native_goal_lifecycle_interleaving_v1_1.py)
- Lock: [`native_goal_lifecycle_interleaving_v1_1_lock_20260926.json`](../../../evaluation/substrate_capability/native_goal_lifecycle_interleaving_v1_1_lock_20260926.json)
- Raw capture: [`substrate_native_goal_lifecycle_interleaving_v1_1_20260926.json`](../../../evaluation/reports/substrate_native_goal_lifecycle_interleaving_v1_1_20260926.json)
- Independent analysis: [`substrate_native_goal_lifecycle_interleaving_v1_1_analysis_20260926.json`](../../../evaluation/reports/substrate_native_goal_lifecycle_interleaving_v1_1_analysis_20260926.json)
- Preserved pre-fix diagnostic: [`v1 raw`](../../../evaluation/reports/substrate_native_goal_lifecycle_interleaving_v1_20260926.json), [`v1 analysis`](../../../evaluation/reports/substrate_native_goal_lifecycle_interleaving_v1_analysis_20260926.json)
