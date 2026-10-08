# Rate-refresh intervention v1.1 amendment (2026-09-29)

The v1 intervention called `apply_rule_batch` once. Its capture and analysis are retained at the v1 paths. The engine API documentation states that `apply_rule_batch` behaves like `apply_rule_once` for non-batch rules; `oo_sunit_rate` is non-batch. A single call therefore advances only one matching binding and is not a full rate refresh. The v1 analysis correctly rejected the full-target equation/stamp gates.

V1.1 changes the intervention to invoke the existing rule repeatedly until the first no-progress call, with a hard cap of 17 progressing calls for the 16 target SUnits plus one termination check. It requires every target `rate_step` to equal the Retina's current step, every target rate to match `max(act-theta,0)`, and the only graph differences from the reset-before-refresh snapshot to be target `rate`/`rate_step` attributes. No other protocol factor changes. The new runner, analyzer, lock, and capture use the `natural_image_rate_refresh_intervention_v1_1_20260929` stem.

