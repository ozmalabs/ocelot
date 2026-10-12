# Stacks Project string-predicate prediction panel v1 results

Date: 2026-09-27  
Status: source-stable two-worker run; all independent gates pass, including the positive control.

## Results

The outcome-blind structural selector reconstructed five one-argument predicates from the Stacks Project `functions.py` module. Lexical order assigns `beginning_of_definition` as the acquisition case; the other four functions are held out. Both workers processed 20 fixed Stacks cases plus two separate Think Python positive-control calls. The independent, non-executing AST oracle had zero errors, both workers matched on every outcome, source hashes and full runtime locks remained stable, and the shared run manifest and console log passed hash verification.

On the primary Stacks panel, each worker abstained on all **20/20** calls with `EmitError`; exact output coverage was **0/20**, including **0/16 held-out calls**. There were no incorrect returned values because no predictions were returned. Conditional accuracy is undefined. Both workers correctly predicted the two positive-control outputs (**2/2**) for `is_divisible(6, 3)` and `is_divisible(7, 2)`, showing that the measured path and oracle can score exact outputs on a supported arithmetic form. The control is excluded from all Stacks scores and ran after the Stacks sequence. No concern receipts or Observation-linked minted axes appeared in either run.

Median wall time across all 22 calls was 39.1 and 39.2 ms; p95 was 53.9 and 41.7 ms. Both full-runtime workers loaded 731/742 seed manifests with the same 11 failures; peak RSS was 1.806 and 1.805 GB. These costs include full-module parsing on Stacks calls and are not function-body-only timings.

## Interpretation

This is a clear negative behavioral result for the selected external string-function family, while the separate control rules out a wholly broken prediction/evaluation path. The selected Stacks functions all use the three-statement `Assign, If, Return` shape and Python string `.find`. Source inspection shows the production multi-statement dispatcher labels this shape `other`; its Term emitters cover let chains, accumulation, and branching returns, not this shape. The native Term algebra already contains `StringIndexOf` and `IfThenElse`, but no lowering connected this Python pattern to those Terms. `StringIndexOf` returns UTF-8 byte offsets, unlike Python's Unicode code-point offsets, so it is not generally interchangeable as a numeric result. For these functions specifically, the `< 0` and `== 0` predicates preserve their truth under either offset convention, provided the receiver is a string and the offset is not otherwise exposed. The measured abstention therefore points primarily to missing composition/lowering and input-type gating, rather than a missing search primitive.

The panel is intentionally narrow: one module, five related functions, one acquisition function, four held-out functions, and four tiny strings per function. It does not estimate transfer prevalence, semantic competence over software, or tractability across repositories. Next work should add a narrowly semantics-preserving lowering for this compared-offset pattern, rerun this frozen panel as a versioned candidate-vs-baseline comparison, and add at least one independently selected family from a second licensed repository. Preserve the current all-abstain baseline.

## Reproduction artifacts

- [Preregistration](SUBSTRATE_STACKS_STRING_PREDICTION_PANEL_V1_PREREG_20260927.md)
- [Selector](../../../scripts/audit_stacks_string_prediction_frame_v1.py)
- [Frame](../../../evaluation/reports/stacks_string_prediction_frame_v1_20260927.json)
- [Runner](../../../scripts/substrate_stacks_string_prediction_panel_v1.py)
- [Independent analyzer and bounded oracle](../../../scripts/analyze_substrate_stacks_string_prediction_panel_v1.py)
- [Source lock](../../../evaluation/substrate_capability/stacks_string_prediction_panel_v1_lock_20260927.json)
- [Raw capture](../../../evaluation/reports/stacks_string_prediction_panel_v1_20260927.json)
- [Analysis](../../../evaluation/reports/stacks_string_prediction_panel_v1_analysis_20260927.json)
