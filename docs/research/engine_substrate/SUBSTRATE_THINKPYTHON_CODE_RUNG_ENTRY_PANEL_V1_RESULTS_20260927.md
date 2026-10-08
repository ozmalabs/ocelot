# Think Python code-reading rung-entry panel v1 results

Date: 2026-09-27  
Status: locked two-worker panel passed all independent checks.

## Findings

Two fresh full-runtime workers read the same hash-selected 64 Python function examples in order through `domains.code_reading.read_function`. The independent analyzer passed 14 gates: it reconstructed all 124 eligible examples and the 64-item frame, verified every source hash and worker schedule, checked source-lock stability and worker parity, and confirmed raw task records contain no code text. There were no task exceptions.

The first request produced no concern receipt, so the post-startup denominator remains all 63 later tasks. Both workers recorded **7/63 tasks with a new concern receipt**. Five of those tasks produced an Observation with a native `minted` edge to a new axis; the other two Observations were `recognized` and had no minted edge. Thus the post-startup graph-linked mint incidence is **5/63** in both workers. `read_function` reports a minted construction on those same five tasks. The first-use conversation bootstrap event observed in the NaturalProofs panel does not occur on this direct code-reading route.

Across all 64 examples, 49 returned a construction and 3 emitted a native Term. The difference is expected in this route: code construction recognition covers shapes whose Term emitter is explicitly narrower. These counts are coverage outcomes, not semantic accuracy. Each worker added five `CapabilityAxis` nodes, all with missing `kind`; typed Observation status and the native `minted` relation provide the stronger mint evidence. No new Transform nodes were recorded.

Per-worker costs: full-runtime boot 12.03–12.06 s; peak RSS 2.044–2.045 GB; median read 4.08–4.23 ms; nearest-rank p95 32.9–36.6 ms; median CPU 4.24–4.31 ms. Boot reports 731 loaded of 742 seed manifests, with 11 manifest failures on both workers: eight reject nodes lacking `local_id`, and three generated `qwen3_reaped_*` seeds reject a seed reference that is not an object. Those repeatable boot failures are part of the measured runtime condition and are not hidden in the task-cost figures.

## Interpretation

The contrast with the NaturalProofs conversation panel is useful: post-startup concern receipts were absent on 126 math-reading worker tasks, while this selected code-reading stream generated five minted-edge outcomes and two recognized residual observations per worker. This shows that acquisition-entry frequency is route- and task-family-dependent in the current substrate. It does not establish that these examples are representative, that the minted constructions improve code understanding, or that the engine has general capability. The corpus is a textbook example collection, and the panel has no independent behavior oracle.

The cost profile is consistent with inexpensive application plus occasional induction at this scale, but no amortized cost comparison is justified from one textbook corpus. The five `kind`-missing axes also expose a schema-quality gap: downstream analysis must depend on the Observation-to-axis graph relation, while axis classification itself needs a reliable typed field.

## Reproduction artifacts

- Frozen protocol: [preregistration](SUBSTRATE_THINKPYTHON_CODE_RUNG_ENTRY_PANEL_V1_PREREG_20260927.md)
- Outcome-blind selector: [selector](../../../scripts/audit_thinkpython_code_frame_v1.py)
- Frozen frame (identifiers and hashes only): [frame](../../../evaluation/reports/thinkpython_code_rung_frame_v1_20260927.json)
- Runner: [panel runner](../../../scripts/substrate_thinkpython_code_rung_entry_panel_v1.py)
- Independent analyzer: [analyzer](../../../scripts/analyze_substrate_thinkpython_code_rung_entry_panel_v1.py)
- Source lock: [lock](../../../evaluation/substrate_capability/thinkpython_code_rung_entry_panel_v1_lock_20260927.json)
- Raw capture: [worker results](../../../evaluation/reports/thinkpython_code_rung_entry_panel_v1_20260927.json)
- Analysis: [independent analysis](../../../evaluation/reports/thinkpython_code_rung_entry_panel_v1_analysis_20260927.json)

## Next gate

The independent prediction probe now covers four safe pure functions and nine inputs, returning five exact predictions and four emitter abstentions. Expand it to a materially larger corpus with predeclared AST strata and fixed multi-vector coverage; include held-out functions whose construction patterns were absent during acquisition, explicit negative controls, and cold/warm conditions. Keep exact accuracy, coverage, and abstention separate. Separately diagnose why the 11 seed manifests fail to load before using boot-cost estimates to claim portable operating costs.
