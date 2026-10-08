# Stacks Project code-reading panel v1 results

Date: 2026-09-27  
Status: two-worker source-stable capture; all independent analysis gates pass.

## Corpus and integrity

The panel covers every top-level function in six locally vendored Stacks Project helper modules: 37 functions across five nonempty modules. Source commit `9b335a632509b7b16cc9eb7bf771ec2cf82ac640` and the Apache-2.0 scripts license are included in the lock. The harness parsed the source but did not import or execute it. It passed selector reconstruction, exact function/module hash schedule, two unique worker processes, complete 37-task schedules, worker outcome parity, and parent/worker source stability. No task raised an exception.

## Results

Both workers returned a construction for all 37 functions. Each had one cold-start mint route on `get_path`, then zero post-cold-start mint routes. One later task (`add_defs`) produced a concern receipt without a mint. No function emitted a Term. Construction presence here is a route outcome, not proof that the returned explanation is semantically correct. The corpus has no task-level behavioral oracle, so this is not an accuracy result.

Per-worker median task wall time was 39.8 and 40.1 ms; p95 was 55.3 and 62.5 ms. Peak RSS was 1.805 and 1.806 GB. Full boot loaded 731/742 manifests and repeated the same 11 failures in both workers. The runner passes the whole containing module to `read_function` for each function, so these timings include repeated module ingestion; they are not function-body-only cost or a scaling curve. The shared run manifest captures the full boot-selected seed set, runtime sources, native build metadata, dirty workspace fingerprint, and a hash-verified console log.

## Interpretation and next gate

This extends code-reading route evidence beyond a teaching corpus to one real, independently authored repository slice. It suggests that after a single cold-start mint, the held construction route covered every sampled function, while the stricter Term-emission route covered none. The source is one repository, dominated by a single 28-function module, and the panel measures neither semantic correctness nor task utility. It cannot establish that natural software workloads are tractable or that minting is rare across repositories.

Next, construct a separate behavior panel from functions with explicit input contracts and a safe independent interpreter. Freeze a diverse function sample, use fixed and held-out composition cases, score exact typed outputs, abstentions and errors separately, and test transfer from acquired structures against near-neighbor negatives. Keep this panel's result as route coverage evidence only.

## Reproduction artifacts

- [Preregistration](SUBSTRATE_STACKS_CODE_READING_PANEL_V1_PREREG_20260927.md)
- [Selector](../../../scripts/audit_stacks_code_reading_frame_v1.py)
- [Frame](../../../evaluation/reports/stacks_code_reading_frame_v1_20260927.json)
- [Runner](../../../scripts/substrate_stacks_code_reading_panel_v1.py)
- [Independent analyzer](../../../scripts/analyze_substrate_stacks_code_reading_panel_v1.py)
- [Source lock](../../../evaluation/substrate_capability/stacks_code_reading_panel_v1_lock_20260927.json)
- [Raw capture](../../../evaluation/reports/stacks_code_reading_panel_v1_20260927.json)
- [Analysis](../../../evaluation/reports/stacks_code_reading_panel_v1_analysis_20260927.json)
