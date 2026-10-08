# Think Python code-prediction panel v2 censored record

Date: 2026-09-27  
Status: do not use this run for output accuracy or capability estimates.

The v2 runner completed both workers and passed its source/process/call-count integrity checks. The independent analyzer correctly failed its gate: two `shift` oracle calls raised `TypeError` because the protocol supplied string prefixes to source that slices the prefix and concatenates a tuple. The source result was not a valid defined-output comparison for those two calls. Preserve the raw and failed analysis as diagnostic artifacts; the v2.1 amendment changes only those input types, preserves the same static eligibility and function set, and reruns under a new source lock.

- Parent protocol: [v2 preregistration](SUBSTRATE_THINKPYTHON_CODE_PREDICTION_PANEL_V2_PREREG_20260927.md)
- Failed analysis: [v2 analysis](../../../evaluation/reports/thinkpython_code_prediction_panel_v2_analysis_20260927.json)
- Raw worker capture: [v2 raw](../../../evaluation/reports/thinkpython_code_prediction_panel_v2_20260927.json)
- Corrected protocol: [v2.1 amendment](SUBSTRATE_THINKPYTHON_CODE_PREDICTION_PANEL_V2_1_AMENDMENT_20260927.md)
