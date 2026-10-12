# Stacks Project string-predicate prediction panel v2 results

Date: 2026-09-27  
Status: source-stable two-worker targeted intervention; all 15 analyzer checks pass. Interpretation is limited by the [scope amendment](SUBSTRATE_STACKS_STRING_PREDICTION_PANEL_V2_AMENDMENT_20260927.md).

## Candidate vs frozen baseline

V2 adds a strict lowering for a one-argument `str.find` assignment followed by `if n < 0` or `if n == 0` with one early return and one final return. With a concrete call type of `str`, it builds existing `StringIndexOf`, `Let`, comparison, and `IfThenElse` Terms. It rejects unknown receiver types, other `.find` signatures, unsafe comparisons, and any use of the byte index outside the predicate. The v1 raw, analysis and frame hashes are pinned in the v2 lock; the independent analyzer rechecks v1's 0/20 primary coverage and 2/2 arithmetic controls.

Across both v2 workers, the five Stacks functions score **25/25 exact typed outputs**, with **25/25 coverage**, zero abstentions and zero wrong returned values. This includes the 20 cases exactly paired with v1 (v1 returned no predictions) and five appended Unicode-prefix cases that check the `< 0`/`== 0` branch truth despite native byte offsets. The first lexically selected function scores 5/5; the four within-frame held-out functions score 20/20. The separate arithmetic positive control scores 2/2 in each worker. Neither worker produces a new concern receipt or minted axis.

Median wall time across the 27-call schedule is 38.6 and 40.1 ms; p95 is 49.0 and 49.6 ms. Boot loads 731/742 manifests with 11 repeated failures; peak RSS is 1.805 and 1.806 GB. Each task includes full Stacks-module ingestion; timings are not function-body-only measurements.

The raw workers' before/after locks and end-of-run manifest agree on the captured `substrate/boot_profiles.py` hash `7b8ce5aefe8b45e7207467945a39e8db83a2e9f8b1115866c40b8fe9aa93df84`. A later live-worktree check found that path now has hash `3dafdba4c1bece04c03e96cef3e0023c48a5eebafb80369c62463ec2b60ee166`; it is currently untracked and is the only difference found in the V2 lock comparison. The results remain internally source-stable for the captured snapshot, but they do not establish behavior on this later live source. Re-run before treating them as current-runtime results.

## Interpretation

This shows a large, measured coverage change for the precisely targeted grammar: v1 abstains on all 20 paired external calls; v2 returns every expected value on those calls and five added Unicode cases. The shared native StringIndexOf operation was already present; v2 supplies a narrow Python lowering plus control-flow composition and runtime type gating. The numeric StringIndexOf result remains a UTF-8 byte offset, but this grammar exposes only whether the result is negative or exactly zero, for which the branch truth matches Python `str.find` on valid strings.

The functions and AST shape were inspected before implementing the candidate. Therefore, the four other functions are not blind implementation holdouts. The 25/25 score supports targeted engineering correctness on this frozen family, not learned structural transfer, broad code prediction, or general capability. No rung-three mint occurred. Next freeze the implementation, choose a distinct family with a new outcome-blind selector, and run a candidate-vs-baseline evaluation without changing code after the new frame is revealed.

## Reproduction artifacts

- [V2 preregistration](SUBSTRATE_STACKS_STRING_PREDICTION_PANEL_V2_PREREG_20260927.md)
- [Interpretation amendment](SUBSTRATE_STACKS_STRING_PREDICTION_PANEL_V2_AMENDMENT_20260927.md)
- [V2 selector](../../../scripts/audit_stacks_string_prediction_frame_v2.py)
- [V2 frame](../../../evaluation/reports/stacks_string_prediction_frame_v2_20260927.json)
- [V2 runner](../../../scripts/substrate_stacks_string_prediction_panel_v2.py)
- [V2 independent analyzer and oracle](../../../scripts/analyze_substrate_stacks_string_prediction_panel_v2.py)
- [V2 source lock](../../../evaluation/substrate_capability/stacks_string_prediction_panel_v2_lock_20260927.json)
- [V2 raw capture](../../../evaluation/reports/stacks_string_prediction_panel_v2_20260927.json)
- [V2 analysis](../../../evaluation/reports/stacks_string_prediction_panel_v2_analysis_20260927.json)
- [Frozen v1 results](SUBSTRATE_STACKS_STRING_PREDICTION_PANEL_V1_RESULTS_20260927.md)
