# CPython `stat` file-mode predicate panel v1 results

Date: 2026-09-27  
Status: completed; all integrity and independent analysis gates pass.

## Capability result

The outcome-blind AST rule selected all seven qualifying predicates (`S_ISBLK`, `S_ISCHR`, `S_ISDIR`, `S_ISFIFO`, `S_ISLNK`, `S_ISREG`, `S_ISSOCK`). Two fresh workers processed 35 fixed file-mode cases and two pre-existing arithmetic controls. Both workers abstained with `EmitError` on all 35 primary cases, returned no incorrect values, and passed the controls 2/2. Workers matched case by case. There were no receipts or mints. All independent frame, oracle, source/case hash, full-lock stability, schedule, parity, manifest and console-capture gates pass.

This is a reproducible zero-coverage result on a separate CPython source module, not a general code-accuracy estimate. The corpus and target AST family were selected after inspecting the local source inventory and module, though the deterministic selector was frozen before any prediction/oracle run and exhaustively included every matching function. It is not blind family transfer; see the [selection-provenance amendment](SUBSTRATE_STDLIB_STAT_PREDICTION_PANEL_V1_AMENDMENT_20260927.md). The oracle implements the behavior independently as `(mode & S_IFMT_MASK) == S_IF*`; expected outputs are exact Booleans.

## Runtime and cost

| Measure | Worker 0 | Worker 1 |
|---|---:|---:|
| Primary exact outputs | 0/35 | 0/35 |
| Primary abstentions | 35/35 | 35/35 |
| Wrong returned outputs | 0 | 0 |
| Arithmetic controls | 2/2 | 2/2 |
| Median call wall time | 20.88 ms | 21.17 ms |
| p95 call wall time | 33.18 ms | 34.79 ms |
| Median call CPU time | 20.88 ms | 21.17 ms |
| p95 call CPU time | 33.19 ms | 34.80 ms |
| Boot manifests loaded | 731/742 | 731/742 |
| Boot failures | 11 | 11 |
| Peak RSS | 1.805 GB | 1.806 GB |

Call costs include full-module AST ingestion and code-reading. Whole-runtime boot is reported separately. The repeated 11 seed-load failures and high boot RSS remain part of the operational envelope.

## Diagnosed substrate boundary

The source helper `S_IFMT(mode)` and module-level `S_IF*` constants are outside the selected function's emitted Term. `AstTermEmitter.emit_function` emits the selected function's return expression; calls are restricted to registered held leaves, sum folds, and prebuilt faculties. A call to an ordinary module helper such as `S_IFMT` therefore has no composition route, and free module constants are not bound into the prediction environment. A second gap remains after helper expansion: native `TermNode::BitAnd` exists and is evaluated by the Rust engine, but the Python AST emitter's `_BINOP` map does not include `ast.BitAnd`.

These are concrete integration gaps between source-level composition and available substrate primitives. This panel does not prove that adding helper/global binding would be safe or tractable; the next implementation should use an explicit bounded fragment (acyclic local helper depth, literal module constants, concrete integer inputs), retain exact refusal outside it, and be measured against frozen behavior plus a separately selected transfer family.

## Corpus provenance and reproduction

The benchmark uses an unchanged copy of CPython 3.13.5 `Lib/stat.py`, byte-compared with the local Python 3.13.5 installation. Its matching `LICENSE.txt` is included. CPython's release license specifies the Python Software Foundation License Version 2 for Python software; see the [official release license](https://github.com/python/cpython/blob/v3.13.5/LICENSE) and [tagged standard-library source](https://github.com/python/cpython/tree/v3.13.5/Lib). The FSDD Python helpers were not used because the local repository README grants a license for the dataset without clearly stating a license for those helper files.

- [Source provenance and license note](../../../data/python_stdlib_3_13_5/SOURCE.md)
- [Frozen protocol](SUBSTRATE_STDLIB_STAT_PREDICTION_PANEL_V1_PREREG_20260927.md)
- [Selection-provenance amendment](SUBSTRATE_STDLIB_STAT_PREDICTION_PANEL_V1_AMENDMENT_20260927.md)
- [Selector](../../../scripts/audit_stdlib_stat_prediction_frame_v1.py)
- [Runner](../../../scripts/substrate_stdlib_stat_prediction_panel_v1.py)
- [Independent analyzer](../../../scripts/analyze_substrate_stdlib_stat_prediction_panel_v1.py)
- [Source lock](../../../evaluation/substrate_capability/stdlib_stat_prediction_panel_v1_lock_20260927.json)
- [Selected frame](../../../evaluation/reports/stdlib_stat_prediction_frame_v1_20260927.json)
- [Raw worker results and run manifest](../../../evaluation/reports/stdlib_stat_prediction_panel_v1_20260927.json)
- [Independent analysis](../../../evaluation/reports/stdlib_stat_prediction_panel_v1_analysis_20260927.json)
- [Console capture](../../../evaluation/run_logs/stdlib-stat-prediction-panel-v1-20260927.stdout_stderr.log)

SHA-256: source `f76eaa7f02d6ef4a8c3c3e82cae34ed72870b643b8c94937a34c697d1e9d6ca2`; license `78b12c3a81360b357002334f0e70ea0e92eebf7a9b358805c03c48484945f3bb`; frame `d1538bb1dec48de2ef8d89252f1afd4f9e8159a0e9768688b29945b1ac5d8bc0`; raw `0a45d7f3df52630995ca62ed7f3fafe3c419a5983f7f888c26baaf288a77da98`; analysis `1b9b71713dd905056a1c0282e72409d4e823e5b8c0f3d567115fd3b0162a4589`; lock `446445c9fbefe80a9b0137fbd167e23344a4280b5151786bf189148de46ac03c`.
