# Contract query scaling v1 — analysis amendment

All ten source-locked workers completed without worker errors. The initial analyzer's native-evaluation count formula incorrectly charged each observation against the original full hypothesis set. The selector filters hypotheses sequentially, so later observations are evaluated only against survivors; if fewer than two remain, it skips candidate-input scoring. The independent work-count replay now mirrors those semantics and computes input scoring only over unused candidate values.

The raw capture and worker outputs are unchanged. The original lock is preserved as `substrate_contract_query_scaling_v1_lock_20261001_pre_analysis_correction.json`; the current lock records the corrected analyzer hash and checks that active code, runner, protocol, native binary, and capture source state are unchanged. This correction affects only the analyzer's expected native evaluation count, not the selection, target, or random-control data.
