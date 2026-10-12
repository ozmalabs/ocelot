# Recursive self-improvement, tranche 2: results (2026-10-07)

Follows the [tranche 1 results](RECURSIVE_SELF_IMPROVEMENT_RESULTS_20261006.md); this tranche works through the six next gates recorded there. All new behaviour is opt-in and off by default.

## Summary

| Gate | Result |
|---|---|
| 1. Credit with recency | **Primary gate failed.** A 4-credit recency window adapts no better than unbounded credit after a shift (+1.1, CI −0.03 to 2.19) and forgets earlier winners. The window stays opt-in; the default is unbounded. The v1 shift harm came from v1's frozen evaluation design, not from the credit rule ([results](SUBSTRATE_VARIATION_CREDIT_RECENCY_V1_1_RESULTS_20261007.md)). |
| 2. Real judges | **Feasible, one example per candidate.** Real child dispatch with paired-control replay plus the real judge shape returned supported for the fix and refuted for the regression. The graph credit rules credited both verdicts. About 28 s per trial. |
| 3. Chunk retention | **Pass.** DimInfer work grows with held chunks (203 → 6,219 candidates, 0.46 → 24.3 ms at 0 → 64 chunks). A capacity of 8 kept recall at 4/4 with 8 live chunks instead of 27, and cut probe work from 3,484 to 1,014. |
| 4. Grain ladder for held generators | **Pass.** Held D4 maps on jittered real handwriting are recognised in 53/100 cases versus 0/100 without the ladder, with 0/100 false recognitions on different characters and exact maps unchanged (100/100). Coarse-graining commutes with D4, so the ladder works where it failed for shears. |
| 5. MDL witness in the sd loop | **Pass (feature build).** 34/34 partially corrupted handwriting cases are recognised with outliers, and the outliers are minted as their own quantum. 0/34 without the flag, 0/60 false generators on different characters, exact maps unchanged. |
| 6. Provenance at more mint sites | **Pass.** MetaShape and ProblemShape mints now record what they were minted from; the 40 related tests pass before and after. |

## Gate 3: chunk retention

`DimensionGenerator.retired` (Rust): a retired generator still resolves as a step of a composite built on it, but is not itself a decode candidate. `shape_decode_loop` v1.13.0 adds:

- an `ag -holds_chunk-> g` edge on every chunk;
- `sd_chunk_uses`, a usage count derived from Transform receipts;
- `sd_chunk_retire`, which retires the least-used then oldest live chunk while live chunks exceed `agent.gen_chunk_capacity`. Absent capacity → never.

[Report](../../../evaluation/reports/chunk_retention_cost_v1_20261007.json).

| held chunks | DimInfer candidates (unexplainable goal) | median ms |
|---:|---:|---:|
| 0 | 203 | 0.46 |
| 4 | 339 | 0.76 |
| 16 | 939 | 2.31 |
| 64 | 6,219 | 24.3 |

The stream was 40 episodes: half recurring depth-3 tasks, half one-off distractors. Afterwards each recurring task was probed on a held-out base with no curriculum:

| arm | recall | live chunks | probe candidates (median) |
|---|---:|---:|---:|
| unbounded | 4/4 | 27 | 3,484 |
| capacity 8 | 4/4 | 8 | 1,014 |
| capacity 4 | 4/4 | 4 | 678 |

The cost grows roughly quadratically in chunk count, because the length-2 pass pairs chunks with chunks. Usage-based retention bounds it without losing the recurring tasks on this stream. Recurrence was half the stream; a sparser stream would test retention harder.

## Gate 4: grain ladder for held generators

[Commutation analysis](../../../evaluation/reports/d4_grain_commutation_v1_20261007.json) on 20 drawings × 8 held maps, pure set arithmetic with no engine. "Jitter" counts jittered twins matching at that grain; "cross" counts different characters falsely matching.

| grain | commutes | jitter matches | cross matches |
|---:|---:|---:|---:|
| 0 | 160/160 | 0 | 0 |
| 1 | 104 | 10 | 0 |
| 2 | 96 | 71 | 0 |
| 3 | 116 | 113 | 57 |

Grain 2 separates jittered twins from different characters; grain 3 does not. The ×2 scale generator never commutes above grain 0.

Built on that analysis:

- DimInfer gains an optional `grain` field (absent = 0; the cache key is unchanged when it is 0).
- `shape_decode_loop` v1.14.0: `sd_infer_dimension` picks the finest grain in `agent.dim_grains` (a list, so the seed keeps its audited no-bound-comparator shape).
- `sd_dim_grain_residual` records `recognized_grain` and carries the full-resolution signature as a `grain_residual` axis.

Full sd-loop measurement with grains [0,1,2] ([report](../../../evaluation/reports/diminfer_grain_omniglot_v1_20261007.json)), 20 drawings × 5 held maps:

| condition | off | ladder |
|---|---:|---:|
| exact | 100/100 | 100/100 (grain 0) |
| jitter ±0.35 cell | 0/100 | 53/100 (grains 1–2) |
| cross-character | 0/100 | 0/100 |

This is exploratory and not preregistered. The grain range was chosen from the commutation analysis, which used the same 20 drawings. A held-out drawing set should confirm it before any default change.

## Gate 5: MDL witness in the sd loop

`shape_decode_loop` v1.15.0:

- every GenInfer Term reads `mdl_enabled = agent.gen_mdl_enabled`;
- `sd_mdl_outliers` marks an MDL-explained observation `recognized_with_outliers`, records the unexplained rows, and mints them as a `CapabilityAxis{source:'mdl_outlier'}`. The existing generator mint mints the map.

The MDL path itself needs the `geninfer_grain_mdl` Cargo feature. In the default build the flag is inert, and a test pins that.

[Report](../../../evaluation/reports/mdl_sd_loop_v1_20261007.json). Native built with `geninfer_linear_exact_prefilter,geninfer_grain_mdl`.

| condition | flag off | flag on |
|---|---|---|
| exact `M·A` (60) | 60 recovered | 60 recovered |
| 2 cells displaced, count preserved (34) | 0 generators | 34 recovered, 34 with outlier quantum |
| cross-character (60) | 0 generators | 0 generators |

## Gate 6: provenance at more mint sites

`scripts/emit_mint_aperture_provenance.py` now also applies the shared idiom to:

- `meta_shape_growth` v1.2.0 (`msg_mint_shape`);
- `problem_shape_growth` v1.1.0 (`ps_mint`).

Two fixes to the script were needed for this:

- It is now idempotent: an already-applied site is left untouched, so effect order is stable.
- It no longer overwrites seed versions.

The `test_problem_shape` and `test_meta_shape_arity` tests now assert provenance on minted entries. `analogy_search`'s `ap_emit` was not changed: it mints an Analogy record, not a codebook entry.

## Gate 2: real-judge feasibility

[Report](../../../evaluation/reports/variation_credit_real_judge_feasibility_v1_20261007.json).

The setup:

- a full-corpus agent recorded two real conversation turns;
- a human flag filed a `reply_fix` concern;
- two candidate deltas were dispatched to the real child process (`scripts/convo_child_run.py`, which replays the paired control and variant boots);
- the composer's judge shape scored each child's result, with `variation_credit` loaded.

| candidate | child score | regressions | verdict | credited | wall |
|---|---:|---:|---|---|---:|
| remove `reply_self_identity` (the flagged reply's rule) | +1 | 0 | supported | yes | 27.8 s |
| remove `reply_to_adjacency_pair` | −1 | 1 | refuted | yes | 28.0 s |

The credit rules consumed the real verdicts unchanged.

**Two blockers before a full real-judge gate:**

1. **Cost.** A 12 × 30 paired run is about 2 × 360 × 28 s ≈ 5.6 hours of child time per arm, excluding training.
2. **A broken authoring path.** The end-to-end promote → author-rule path does not mint an Experiment on this tree. `test_convo_experiment_migrated.py::test_flag_promote_experiment_judge_adopt_closes` and `test_agent_authors_new_rule_end_to_end` both fail with "exactly one conversation experiment expected, got 0". The second fails identically with this work's shape_decode_loop changes reverted (checked in tranche 1). The first was not baseline-checked here, because a safe revert of the dirty tree is not possible. Here the feasibility capture minted the Experiment with `mint_experiment`, so the authoring step is still the gap.

## Regression check

I re-ran the tranche 1 regression scope after all tranche 2 changes. That is 93 `*_migrated` test files: tranche 1's 88 files that reference the changed seeds and functions, plus the MetaShape/ProblemShape tests and the new test files.

- Result: 1,037 passed, 40 failed, 6 skipped, 1 collection error.
- The 40 failures are exactly the tranche 1 baseline set. That baseline was taken with the session's seed and Python edits reverted.
- No new failures, and no baseline failure changed state.
- The collection error is the same one present in tranche 1.
- The full `-k migrated` suite was not run to completion.

## Engine and flags

- Default engine (no feature flags) rebuilt with `scripts/engine_build.sh --lib-only` from current source. New Rust is limited to the `retired` attribute and DimInfer's `grain` field.
- The MDL measurements used a separate feature build at `/tmp/pfv14/g5.so`; its hash is in the report.
- Runtime flags introduced in this tranche, all absent by default:
  - `VariationPolicy.window`
  - `agent.gen_chunk_capacity`
  - `agent.dim_grains`
  - `agent.gen_mdl_enabled`

## Next

1. **Fix the promote → author path.** The flagged concern currently mints no Experiment. Then the variation credit loop can run on concerns the agent authors itself, rather than hand-minted Experiments.
2. **Run a real-judge adoption gate with context.** Give concerns observable features, and budget about 6 hours of child time per arm.
3. **Confirm the held-generator grain ladder on held-out drawings.** The 20 drawings used here also chose the grain range. After that, decide whether `dim_grains=[0,1,2]` can be a default for vision routes.
4. **Test retention on a sparser recurrence stream,** and measure chunk retirement within live sd-loop workloads.
