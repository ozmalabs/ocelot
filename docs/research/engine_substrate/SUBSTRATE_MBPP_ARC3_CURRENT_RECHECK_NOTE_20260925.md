# MBPP Arc 3 current-source recheck (2026-09-25)

**Run state:** current-source replication of the registered Arc 3 R3 benchmark, not confirmatory. The dataset, task split, prompts, arms, and outcomes have been studied previously. This recheck uses the unchanged [`PROGRAM_SYNTHESIS_ARC3_PREREG.md`](../program_synthesis/PROGRAM_SYNTHESIS_ARC3_PREREG.md) protocol and existing `scripts/mbpp_arc3_battery.py` runner against the currently installed source/native extension.

## Scope and preservation

Run the entire MBPP sanitized test split using the runner's existing `full_r3`, `no_retrieval`, and `official_r3` arms, both determinism passes per arm, and its registered 25-minute rule for an official-arm prefix if needed. Preserve its split and reference-code stripping. Save to a timestamped `evaluation/reports/` path; do not overwrite the historical `results/mbpp_arc3_endgame.json` or its cited Arc 2/oracle-ceiling inputs.

The measurement covers a naturally sourced Python-program task set with assertion-derived revealed/held-out rows and an explicit retrieval-off comparator. It rechecks a known task set and prior outcome distribution; it cannot establish new-task generalization, an independent evaluation, current training-data contamination absence beyond the existing split contract, or broad general intelligence. Record task-level outcomes, determinism hashes, uncertainty, cross-arm transitions, runtimes, memory, native/source hashes, and the original dependency artifact hashes.

The run lock is [`mbpp_arc3_current_recheck_lock_20260925.json`](../../../evaluation/substrate_capability/mbpp_arc3_current_recheck_lock_20260925.json); raw output is [`substrate_mbpp_arc3_current_recheck_20260925.json`](../../../evaluation/reports/substrate_mbpp_arc3_current_recheck_20260925.json). No engine, seed, task, or benchmark policy edits are part of this recheck.
