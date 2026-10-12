# Episodic checkpoint recovery post-fix rerun — 2026-09-25

The v3 corruption report remains the record of behavior before the loader fix. `WorldAdapter.load()` now initializes `_vision_illumination_nodes`, the session-local list that `close()` expects. A direct distinct-process save/load/close check passed, then a v5 locked rerun repeated all four checkpoint variants on the repaired source.

The post-fix rerun again restored six episodes and all 18 memory rules; intact retrieval returned all six expected summaries. The modified-summary case still returned `CORRUPTION-MARKER` as recalled content without warning, the removed episode link still caused an explicit miss only for that cue, and malformed JSON still raised `JSONDecodeError`. All three valid loaded adapters closed cleanly. Thus the lifecycle omission is fixed and directly verified; semantic integrity checking remains an open defect.

The first four harness attempts and their amendments remain documented with the pre-fix results. The v5 lock covers the current `WorldAdapter.load` source, v5 runner, seed, and native artifacts; the independent audit matched all ten locked hashes.

## Artifacts

- Amendment: [`SUBSTRATE_EPISODIC_CHECKPOINT_RECOVERY_AMENDMENT_V4_20260925.md`](SUBSTRATE_EPISODIC_CHECKPOINT_RECOVERY_AMENDMENT_V4_20260925.md) (source fix and rerun intent); [`SUBSTRATE_EPISODIC_CHECKPOINT_RECOVERY_AMENDMENT_V5_20260925.md`](SUBSTRATE_EPISODIC_CHECKPOINT_RECOVERY_AMENDMENT_V5_20260925.md) (harness correction)
- Lock: [`episodic_checkpoint_recovery_postfix_v5_lock_20260925.json`](../../../evaluation/substrate_capability/episodic_checkpoint_recovery_postfix_v5_lock_20260925.json)
- Raw: [`substrate_episodic_checkpoint_recovery_postfix_v5_20260925.json`](../../../evaluation/reports/substrate_episodic_checkpoint_recovery_postfix_v5_20260925.json)
- Independent analysis: [`substrate_episodic_checkpoint_recovery_postfix_v5_analysis_20260925.json`](../../../evaluation/reports/substrate_episodic_checkpoint_recovery_postfix_v5_analysis_20260925.json)
- Runner: [`substrate_episodic_checkpoint_recovery.py`](../../../scripts/substrate_episodic_checkpoint_recovery.py)
- Auditor: [`analyze_substrate_episodic_checkpoint_recovery_postfix.py`](../../../scripts/analyze_substrate_episodic_checkpoint_recovery_postfix.py)
