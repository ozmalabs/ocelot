# Episodic checkpoint restart and corruption recovery — 2026-09-25

## Result

The amended, pre-locked run used distinct writer and reader PIDs and a 55,566-byte `WorldAdapter.save` checkpoint containing six bound episodes. A fresh `WorldAdapter.load` restored 18 memory rules and all six Episode→event/context/schema relations. The intact checkpoint then retrieved all six exact cues with the original summary, `recalled` provenance, and `not_observed` status. Median load was about 7.1 ms and median retrieval tick about 0.17 ms in these single-process measurements.

The corruption arms expose different failure modes:

- **Altered semantic content in valid JSON:** changing one event summary to `CORRUPTION-MARKER` did not prevent loading. Retrieval returned the corrupted summary as `recalled`, with confidence 0.85 and `not_observed` provenance. No integrity warning or abstention appeared. This is a content-integrity gap in this checkpoint path.
- **Missing `recorded_episode` edge:** the affected cue returned zero candidates and explicit `insufficient_information`; the other five recalled correctly. This is conservative degradation for this structural omission.
- **Malformed JSON:** load returned `JSONDecodeError` before a graph was created. The harness recorded the load error rather than treating it as a successful recovery.
- **Loaded-adapter cleanup:** each valid reader completed load and all queries, but `WorldAdapter.close()` then raised `AttributeError` because `_vision_illumination_nodes` was absent on the object reconstructed by `load()`. This is a lifecycle defect separate from graph restoration and must be addressed or explicitly handled in restart workflows.

## Interpretation and limits

The current WorldAdapter checkpoint path preserves the graph, rules, node IDs, and these episodic relationships across a real process boundary. That is distinct from `LongTermMemory`/`MemoryFaculty` JSON record persistence, which stores attribute snapshots and reconstructs a separate index. The checkpoint has no observed integrity check for valid-JSON semantic changes in this probe. This does not establish crash consistency, atomic writes, concurrent writers, adversarial security, large-checkpoint scaling, or natural-task memory utility.

The episode-link removal case is a targeted structural corruption, not a proof of robust repair. The semantic mutation shows the loader accepts altered content and downstream rules treat it as recalled evidence; no general corruption policy exists here. Future checkpoint work should decide on checksums/content addressing and recovery/refusal policy, and separately repair the post-load cleanup error before using load/close as a normal lifecycle.

## Harness history

Three pre-score harness attempts are retained. V1 lost buffered reader output when cleanup threw; v2 caught and recorded cleanup exceptions but queried checkpoint size after the temporary directory had been removed; v3 moved that size capture before cleanup. No checkpoint variant, task, or scoring criterion changed. V3 ran only after its amended lock was written.

## Reproducibility

- Protocol: [`SUBSTRATE_EPISODIC_CHECKPOINT_RECOVERY_PREREG_20260925.md`](SUBSTRATE_EPISODIC_CHECKPOINT_RECOVERY_PREREG_20260925.md)
- Amendments: [`v2`](SUBSTRATE_EPISODIC_CHECKPOINT_RECOVERY_AMENDMENT_20260925.md), [`v3`](SUBSTRATE_EPISODIC_CHECKPOINT_RECOVERY_AMENDMENT_V3_20260925.md)
- Locks: [v1](../../../evaluation/substrate_capability/episodic_checkpoint_recovery_lock_20260925.json), [v2](../../../evaluation/substrate_capability/episodic_checkpoint_recovery_amended_lock_20260925.json), [scored v3](../../../evaluation/substrate_capability/episodic_checkpoint_recovery_amended_v3_lock_20260925.json)
- Runner: [`substrate_episodic_checkpoint_recovery.py`](../../../scripts/substrate_episodic_checkpoint_recovery.py)
- Independent auditor: [`analyze_substrate_episodic_checkpoint_recovery.py`](../../../scripts/analyze_substrate_episodic_checkpoint_recovery.py)
- Raw run: [`substrate_episodic_checkpoint_recovery_amended_20260925.json`](../../../evaluation/reports/substrate_episodic_checkpoint_recovery_amended_20260925.json)
- Independent analysis: [`substrate_episodic_checkpoint_recovery_analysis_20260925.json`](../../../evaluation/reports/substrate_episodic_checkpoint_recovery_analysis_20260925.json)

All nine v3 input hashes matched during independent audit. The initial one-event serialization inspection is disclosed in the preregistration and was not scored.
