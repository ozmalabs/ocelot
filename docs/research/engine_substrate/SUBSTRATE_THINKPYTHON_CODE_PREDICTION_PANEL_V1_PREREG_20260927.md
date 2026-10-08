# Think Python code-prediction panel v1 preregistration

Date: 2026-09-27  
Status: freeze before substrate execution.  
Question: when production code reading emits a Term for a small statically safe sample of textbook functions, does native Term evaluation match an independently interpreted source result on fixed inputs, and how often does it abstain?

## Frozen frame and inputs

The selector scans the same Think Python fenced code corpus as the rung-entry panel. Eligibility is determined statically and before any substrate run: the first top-level function must have exactly one `return` statement; its expression must contain only AST nodes in the selector's explicit whitelist (arithmetic, unary/boolean/comparison/conditional expressions, names/constants, tuples/lists, and calls to `abs`, `min`, `max`, `sum`, `len`, or `round` by bare name); and the formal argument list must match one of four predeclared signatures. Rank eligible chapter/block IDs by SHA-256 of compact JSON `[chapter, block_index]`. The four eligible examples and fixed input cases are recorded in `evaluation/reports/thinkpython_code_prediction_frame_v1_20260927.json`; no code surfaces are copied there.

The inputs are fixed by the signature before evaluating any substrate output: `distance(x1,y1,x2,y2)` gets `(0,0,3,4)` and `(-2,4,1,0)`; `is_divisible(x,y)` gets `(6,3)`, `(7,2)`, and `(-8,4)`; `min_max(t)` gets `[1,3,2]` and `[-2,5,0]`; `different_words(hist)` gets `{"a":2,"b":1}` and `{}`. The frame contains nine function-input cases total.

## Independent oracle and measured route

The analyzer implements a small recursive AST interpreter with an explicit operator/call whitelist. It never uses `eval`, `exec`, imports, or the substrate's Term emitter. It computes the expected output directly from the source AST and frozen input objects. Unsupported AST at analysis time invalidates the frame gate rather than silently dropping a case.

Two fresh full-runtime workers load all seeds, then process the same four functions and nine calls in frame order. Each call uses production `domains.code_reading.predict_output`, which re-reads the function and evaluates only the emitted native Term. A raised `EmitError` or evaluation exception is recorded as abstention; unexpected predicted values count as incorrect, not abstentions. Report exact typed-output accuracy among all cases, coverage, accuracy conditional on a prediction, abstentions, route mint/receipt deltas, wall/CPU time, boot failures, and RSS. No code text or rendered source is saved in raw capture.

## Gates and limits

Lock protocol, selector, frame, runner, independent analyzer, source trees, native extension, seeds, and Think Python corpus. Require two fresh worker PIDs; source stability; exact frame/hash/input schedule; no hidden code execution in the oracle; exact output type and value agreement; and independent recomputation of all denominators. Preserve unsupported/abstained cases. These nine cases are a narrow proof-of-measurement and do not estimate general code capability, transfer, or natural workload accuracy. The safe whitelist and argument signatures bound conclusions to this sample.
