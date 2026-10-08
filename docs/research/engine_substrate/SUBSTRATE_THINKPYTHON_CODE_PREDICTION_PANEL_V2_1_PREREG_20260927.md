# Think Python code-prediction panel v2.1 preregistration

Date: 2026-09-27  
Status: frozen corrected rerun protocol.  
Parent design: [v2 preregistration](SUBSTRATE_THINKPYTHON_CODE_PREDICTION_PANEL_V2_PREREG_20260927.md).  
Amendment: [v2.1 input correction](SUBSTRATE_THINKPYTHON_CODE_PREDICTION_PANEL_V2_1_AMENDMENT_20260927.md).

The v2 design and its eligibility grammar, independent bounded AST interpreter, 18-function outcome-blind frame, 36-call schedule, source locks, two-worker runtime, and type-sensitive scoring remain frozen as specified in the parent protocol. The v2 execution is censored because the analyzer found two `TypeError` inputs in `shift` caused by a test value that was incompatible with the source expression's tuple operation.

The v2.1 frozen frame corrects only the `shift` input types: `prefix` is a tuple (`{"$tuple":["p","q","r"]}` and `{"$tuple":["a"]}` in the JSON frame), decoded to Python tuples by the runner and independent analyzer. The analyzer must independently reconstruct these cases, successfully interpret all 36 calls within the declared bounds, and fail the confirmatory gate if any input has an oracle error. Keep every substrate `EmitError` as an abstention; do not drop cases based on substrate output.
