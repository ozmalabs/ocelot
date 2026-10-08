# Stacks string-predicate panel v2 interpretation amendment

Date: 2026-09-27  
Applies to: [v2 preregistration](SUBSTRATE_STACKS_STRING_PREDICTION_PANEL_V2_PREREG_20260927.md) and [v2 results](SUBSTRATE_STACKS_STRING_PREDICTION_PANEL_V2_RESULTS_20260927.md).

## Scope correction

The v2 lowering was deliberately designed after inspection of the five functions in the v1 frame. Although the protocol fixes one acquisition function and four within-frame held-out functions, the remaining functions were not blind to feature design. The v2 result is therefore a targeted, source-locked engineering intervention on known syntax, not an independent or out-of-sample transfer estimate. Preserve the original v1 all-abstain baseline and the v2 raw capture; do not describe the 20 within-frame held-out cases as a blind confirmatory set.

## Claim boundary

The supportable claim is that the new constrained path returns the independent oracle's exact typed value on these 25 frozen Stacks calls (including five Unicode-prefix cases) in two fresh full-runtime workers, while the captured v1 path abstains on all 20 paired Stacks calls. The two arithmetic positive-control cases pass in both versions. The implementation creates no new concern receipts or minted axes, so this measures engineered execution coverage, not new-structure acquisition. The final live tree subsequently changed the untracked `substrate/boot_profiles.py`; raw worker locks and run manifest agree with each other, but not with that later file. Thus the result is tied to the locked pre-change runtime snapshot. Generalization requires a fresh function family selected after the implementation is frozen, preferably from a second licensed repository, with an independent selector/oracle and candidate-vs-baseline lock.
