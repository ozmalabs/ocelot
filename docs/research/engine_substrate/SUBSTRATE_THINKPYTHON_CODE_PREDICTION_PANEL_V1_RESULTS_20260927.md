# Think Python code-prediction panel v1 results

Date: 2026-09-27  
Status: source-locked two-worker panel passed all 13 analysis gates.

## Results

The panel covers four functions selected by a frozen static whitelist from the Think Python example corpus, with nine fixed function-input cases. Two fresh workers had distinct PIDs, stable source locks, identical schedules, and identical typed predictions. The independent analyzer reconstructed the four-row frame, interpreted every eligible AST using its own operator whitelist, and verified all nine input/output records per worker.

Each worker made five predictions and abstained on four. All five predictions exactly matched the independent oracle in both value and type: **5/9 exact outputs overall, 5/5 among attempted predictions, with four honest `EmitError` abstentions and zero wrong predictions**. The five predictions came from only two functions: the constant-return `distance` example and arithmetic/comparison `is_divisible`. Both `min_max` inputs and both `different_words` inputs abstained because the emitter did not produce a Term for those expressions. The `distance` label is the literal behavior of the frozen code example; it is not an oracle for the textbook's intended distance function.

On this sequential route, both workers also recorded three concern receipts: two were Observation-linked minted axes and one was a recognized Observation. This is mechanism attribution only; the minted construction on `different_words` did not yield an emittable Term on either call. A mint is not evidence of useful transfer.

Per-worker boot: 11.87–11.94 s, 731/742 manifests loaded with the same 11 failures. Peak RSS was about 1.951 GB. Across nine calls, median wall time was 4.00–4.38 ms and nearest-rank p95 was 40.2–44.8 ms; the first call to each function includes route/shape setup and should not be read as steady-state scaling.

## Interpretation

This probe gives direct, independent evidence that the emitted Term path can produce exact outputs for a small arithmetic/comparison subset and that the system abstains on unsupported call shapes. It also identifies a coverage boundary: source forms using `min`, `max`, or `len` pass the static oracle eligibility rule but are not currently Term-emittable in this route. The absence of incorrect predictions among five attempts is too little evidence for a meaningful accuracy estimate. Nine cases across four functions, from one textbook corpus and one route, do not support general code-capability, transfer, or tractability claims.

The result complements the broader code rung-entry panel: that panel measured construction coverage and mint incidence on 64 examples; this one adds a narrowly scored behavioral oracle. It does not repair the 11 seed-load failures or establish full-runtime portability.

## Reproduction artifacts

- Frozen protocol: [preregistration](SUBSTRATE_THINKPYTHON_CODE_PREDICTION_PANEL_V1_PREREG_20260927.md)
- Outcome-blind static selector: [selector](../../../scripts/audit_thinkpython_code_prediction_frame_v1.py)
- Frozen frame and inputs: [frame](../../../evaluation/reports/thinkpython_code_prediction_frame_v1_20260927.json)
- Runner: [panel runner](../../../scripts/substrate_thinkpython_code_prediction_panel_v1.py)
- Independent oracle/analyzer: [analyzer](../../../scripts/analyze_substrate_thinkpython_code_prediction_panel_v1.py)
- Source lock: [lock](../../../evaluation/substrate_capability/thinkpython_code_prediction_panel_v1_lock_20260927.json)
- Raw capture: [worker results](../../../evaluation/reports/thinkpython_code_prediction_panel_v1_20260927.json)
- Analysis: [independent analysis](../../../evaluation/reports/thinkpython_code_prediction_panel_v1_analysis_20260927.json)

## Next gate

Expand the behavioral panel only after fixing its sampling base: select a materially larger source corpus with predeclared, statically safe AST strata, stratify by construction family and arity, and freeze multiple input vectors per function before execution. Keep unsupported syntax as an abstention class and add explicit negative controls. Then test acquired-construction transfer on held-out source functions whose shapes were not seen during the acquisition phase. Preserve an independent source interpreter and type-sensitive exact scoring.
