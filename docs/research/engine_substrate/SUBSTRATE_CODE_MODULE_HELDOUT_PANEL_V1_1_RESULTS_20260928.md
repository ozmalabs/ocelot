# CPython module-held-out code prediction panel v1.1 results

Date: 2026-09-28  
Status: complete; all 12 independent analysis gates pass.

## Selection and outcome

The copied corpus contains 154 top-level CPython 3.13.5 Python files. The v1 hash sample of 32 modules yielded zero functions under its frozen safe-fragment selector; that valid empty result is retained in `code_module_heldout_panel_v1_frame_20260928.json` and gives no capability estimate. Preregistered v1.1 searched all 151 ordinary non-`stat.py`, non-`__*` modules and found only three functions matching the bounded bitwise grammar: `operator.xor`, `operator.or_`, and `operator.and_`. All three are in the same module. No candidate was manually replaced. The candidate signatures are two-argument functions; nine frozen integer-pair inputs per function produced 27 oracle cases.

Both fresh workers returned all 27/27 outputs exactly, with zero wrong outputs and zero abstentions. The independent AST oracle and frame reconstruction passed. Each worker had one receipt/Observation and no minted-axis edge; exact-output parity held. This is transfer to a new module within the same CPython project, but the sample’s realized diversity is one module and the functions are simple binary bitwise operations closely related to the previously measured `stat.py` predicates. It is not evidence of broad or independent-project transfer.

| Measure | Worker 0 | Worker 1 |
|---|---:|---:|
| Exact outputs | 27/27 | 27/27 |
| Predictions / abstentions / wrong returns | 27 / 0 / 0 | 27 / 0 / 0 |
| Receipts / observations / minted axes | 1 / 1 / 0 | 1 / 1 / 0 |
| Median / p95 call wall | 44.77 / 63.43 ms | 45.88 / 68.96 ms |
| Median / p95 call CPU | 44.77 / 62.79 ms | 45.89 / 64.06 ms |
| Boot | 731/742; 11 failures | 731/742; 11 failures |
| Peak RSS | 1.805 GB | 1.805 GB |

## Integrity and artifacts

The 12 independent checks passed: module inventory and selected frame reconstruction, oracle coverage, two fresh PIDs, full measured-source locks before/during/after, complete schedule and source hashes, worker parity, console capture, no wrong return, and worker success. The runner uses the byte-copied source and matching CPython license.

- Raw report SHA-256: `a37bc680103ebd9f0cce5b74bc61727f221c2d5caa69b43dc7b698d14d0928f5`
- Independent analysis SHA-256: `55112cfde4ee24a2ce519c6264d389ff85ad4076d3d4895d6163d5441e00823f`
- Frozen frame SHA-256: `dd5f46981cade4b9abad48d914fa4565fe0d75e10a16470ae6ec0cc481b8e0e8`
- Source lock SHA-256: `0b1fb0ba5d6d8cd1bef8ec3f480aaa2c9fa755ec3859c746dc8dff765c7ad1f7`

## Next measurement

The selector’s three-function yield is itself an important limit: the chosen exact grammar is rare in this sample. Do not broaden it after seeing these outputs and reuse this result as confirmatory. A next version should either preregister a broader safe grammar (with new oracle validation) or sample a second licensed project by filename hash before inspecting any source. Preserve this run as the bounded bitwise-transfer result and keep conditional accuracy distinct from coverage.

## Artifacts

- [v1.1 preregistration](SUBSTRATE_CODE_MODULE_HELDOUT_PANEL_V1_1_PREREG_20260928.md)
- [v1 empty-selector preregistration](SUBSTRATE_CODE_MODULE_HELDOUT_PANEL_V1_PREREG_20260928.md)
- [Selector](../../../scripts/select_cpython_module_heldout_frame_v1_1.py)
- [Runner](../../../scripts/substrate_code_module_heldout_panel_v1_1.py)
- [Independent analyzer and oracle](../../../scripts/analyze_substrate_code_module_heldout_panel_v1_1.py)
- [Frame](../../../evaluation/substrate_capability/code_module_heldout_panel_v1_1_frame_20260928.json)
- [Raw report](../../../evaluation/reports/code_module_heldout_panel_v1_1_20260928.json)
- [Analysis](../../../evaluation/reports/code_module_heldout_panel_v1_1_analysis_20260928.json)
- [Source lock](../../../evaluation/substrate_capability/code_module_heldout_panel_v1_1_lock_20260928.json)
- [Licensed source snapshot](../../../data/cpython_lib_3_13_5/SOURCE.md)
