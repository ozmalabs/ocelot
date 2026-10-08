# Think Python code-prediction panel v2.1 amendment

Date: 2026-09-27  
Parent protocol: [v2 preregistration](SUBSTRATE_THINKPYTHON_CODE_PREDICTION_PANEL_V2_PREREG_20260927.md)

The first v2 source-locked execution passed its runner gates, but independent analysis found that both fixed `shift(prefix, word)` cases used string values for `prefix`, while the frozen source slices `prefix` and concatenates it with a one-element tuple. The oracle correctly raised `TypeError`; the all-cases oracle gate therefore failed. Preserve the first raw run and failed analysis as a censored measurement. Do not use its 36-case accuracy summary.

For v2.1, the two `shift` inputs use tuple-valued prefixes, encoded in JSON as `{"$tuple": [...]}` and decoded by both the runner and independent analyzer. The frame, runner, analyzer, and amended protocol are versioned separately and receive a new source lock. No other eligibility, test case, scoring, or runtime conditions change. The analyzer requires all 36 independently interpreted inputs to be type-compatible and bounded; an oracle error invalidates the amended run rather than becoming an unscored omission.
