# SD LOOP block 371000 — AMENDMENT before the final regression run

**Status:** written 5 November 2026. This is after a first, partial G-6 run and before the
final one. It amends [`SD_LOOP_REARM_AND_JSON_SIGNATURE_PREREG.md`](SD_LOOP_REARM_AND_JSON_SIGNATURE_PREREG.md).
Everything below that first run produced is reported as found.

## 1. What the first G-6 pass showed

The scoped set has 2054 collected tests. For the first 1070, outcomes were compared by node
id between the start-commit worktree and the fix worktree. Both runs then stalled for more
than an hour on `tests/test_humanoid_walking_migrated.py` and were stopped. That test is
heavy and unrelated to the sd loop; it was in the set only because it mentions a
`…ShapeSignature` codebook type.

Four node ids went from pass to fail. No test went from fail to pass.

| test | cause | verdict |
|---|---|---|
| `test_agnosia_migrated.py::test_the_ablations_are_flags_not_python_decisions` | It enumerates the rules carrying the `AgnosiaParams.associative` guard and expects exactly `sd_recognize`, `sd_recognize_dim` and `sd_recognize_transformed`. The two new rules write `covered_by`, so they must carry the guard, and they do (copied verbatim). | Correct new behaviour. The enumeration is updated to the five `covered_by` writers. |
| `test_det1_migrated.py::test_shear_over_merge_persists_under_unimodular` | The sheared F reaches `sd_recognize` through a 3-part cover (plan `U, F, V`), and det1's codebook stores signatures as `json.dumps`. Pre-fix, every part scored 0 under `AntiUnify` and the tie returned `X`. `ClosestShape` scores them properly and returns `U`. Traced on both trees: same status, same plan, only `covered_by` differs. | The pinned alias `X` was an artefact of defect D2. The finding the test guards (a det=1 shear aliases onto ANOTHER identity) still holds, since `U ≠ F`. The pin is updated to `U`. |
| `test_chunk_composite_migrated.py::test_retirement_removes_a_candidate_not_a_capability_built_on_live_chunks` | `sd_chunk_retire` bumps `codebook_epoch`, which re-arms every observation. The prereg's D1 design rewrote the existing `Transform` in place with the current explanation. Observation `a` was re-explained as the single step `[chunk A]`, the chunk it had itself minted, so A's `uses` went from 1 to 2. `sd_chunk_uses` counts `Transform.generators` as receipts. | **A defect in the prereg's D1 design.** `Transform` is a per-observation receipt of how the observation was first recognised, and rewriting it changes retention accounting. The design is amended (§2). |
| `test_goal_residual_migrated.py::test_gr3_no_new_termnode_variants` | It diffs the live `term.rs` against `HEAD`. The fix's new variant is uncommitted in the worktree. | An artefact of running on uncommitted Rust. It passes once the change is committed. Not a behaviour change. |

## 2. Design amendment (D1)

`sd_rerecognize_transformed` and `sd_rerecognize_dim` keep their match and where clauses,
but **no longer write to the `Transform` node**. Their only effects are:

- `sd_rerecognize_transformed`: `status := "recognized_transformed"` and
  `covered_by := TransformDecode(...).base`;
- `sd_rerecognize_dim`: the same, plus `transform_explained := 1`, with `covered_by` from
  DimInfer.

The `Transform` stays the receipt of the first recognition. `covered_by` carries the
current identity.

## 3. Revised predictions

- **G-4 is unchanged:** 8/15/0, the same deltas, 15 Transform nodes. In the affect growth
  stream the receipts already equal the current explanation.
- **G-5 is unchanged:** `recognized_transformed`, the receipt keeps base `part_tromino`,
  `rotation90`, k=1, and there is 1 Transform and 1 LatentDimension.
- **G-6:** the same comparison over all 2052 tests except the two
  `test_humanoid_walking_migrated.py` ids. Both trees run the same id list. The predicted
  outcome changes are:
  - the agnosia enumeration and the det1 pin, both updated as §1 states and passing on the
    fix tree;
  - `test_affect_frame_v02::test_G3_growth`, updated as the prereg states.

  Nothing else should change, including `test_chunk_composite_migrated.py`, which now
  passes. Any other pass→fail is a failure of this rung.

## 4. Consequence for committed research records (reported, not rewritten)

D2 affected every sd-loop consumer whose codebook stores JSON-string signatures and that
reads `covered_by` after an exact or multi-part cover. det1 is one confirmed case.
`results/det1.json` and `VISION_DET1_RESULTS.md` record the alias as `X`. This rung re-runs
`scripts/det1_measure.py` on both trees and reports the difference. It does not edit those
records. Other JSON-string consumers (agnosia, identity_seam, the stroke and composer
codebooks) are listed in the results as needing the same check.
