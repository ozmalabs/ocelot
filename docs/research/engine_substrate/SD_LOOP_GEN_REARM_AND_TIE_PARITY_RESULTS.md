# SD LOOP — GenInfer flag reset on re-arm, and ClosestShape tie parity — RESULTS (block 372000)

**Pre-registration:** [`SD_LOOP_GEN_REARM_AND_TIE_PARITY_PREREG.md`](SD_LOOP_GEN_REARM_AND_TIE_PARITY_PREREG.md)
(start commit `dca17cfa`). No amendment.

**Outcome.** H-0 passes. H-3 passes: 0 per-id outcome changes on the 2022-id set. **H-1 and
H-2 fail as written.** The failures come from how the two gates were specified, not from
the change. They are reported as failures, and the gate assertions are kept unchanged in
the test file under `xfail(strict=True)`. A labelled post-hoc diagnostic (§2.3) shows the
fix does what G1 intended. The pre-fix control confirms G1 was a real defect: 13 det1 shear
views carried a stale `gen_explained == 1` across a re-arm.

## 1. What changed

- **G1 (seed).** `sd_redecode` in `seeds/shape_decode_loop.json` (v1.18.0 → v1.19.0) also
  sets `gen_checked := 0` and `gen_explained := 0`. This uses the same idiom as the
  transform and dimension resets. The change is made by
  `scripts/gen_sd_rearm_and_closest_shape.py`, which stays idempotent (second run: "no
  change"). A diff against the start commit shows only `version`, `description` and rule
  `sd_redecode` changed.
- **G2 (Rust).** `eval_closest_shape` in `runners/dsl/src/shape_decode.rs` reports to the
  `argmin_tie` census as `Argmax` does: `note_firing`, `note_empty`/`note_tie`,
  `note_site("ClosestShape", <goal JSON>, true)` on a tie, and `note_nulls`. Under
  `coerces_refusal(false)` a tie returns `None` after `note_refusal`. Everything sits behind
  the instruments' default-off loads.
- **Engine** `614b55413052`, built with `scripts/engine_build.sh --lib-only`.
- **Test** `tests/test_sd_gen_rearm_tie_parity_migrated.py`. It writes
  `results/sd_gen_rearm_tie_parity.json` (gitignored).

## 2. Gates

| gate | result |
|---|---|
| **H-0** engine | **PASS.** Rust `closest_shape` tests 8/8 (4 existing, 4 new: tie recorded with 1 site; tie refused under `refuse_all` and untouched by `refuse_min`; unique best records 0 ties; instruments off leaves the winner unchanged). `variant_table_covers_the_enum` passes. Provenance tests 9 passed, 1 skipped (`own`). Seed source check passes |
| **H-1** re-arm ≡ fresh | **FAIL.** Agreement on the full state tuple: (a) affect 6/23, (b) det1 views 0/35, (c) tromino 0/1. Predicted 100% |
| **H-2** flags re-checked | **FAIL.** All 35 re-armed views in (b) end with `gen_checked = 0`, not 1 |
| **H-3** regression | **PASS.** §3 |

### 2.1 Why H-1 fails

There are two classes of disagreement. Neither is a behavioural difference.

1. **Raw `gen_explained`: 0 versus absent.** The fix writes `0`, as prereg §2 specifies. A
   fresh observation never gets the key. H-1 compares the raw value, so every re-armed row
   that the GenInfer stage did not revisit differs: 17 rows in (a), 17 in (b), 1 in (c).
   Every guard reads `== 1` or `Eq True`, and 0 and absent are both falsy for them. The
   prereg specified a 0 write and an exact raw comparison together, and the two are
   incompatible.
2. **The first-recognition `has_transform` receipt (18 rows in (b)).** These views end
   `recognized` with one `has_transform` edge; a fresh decode has none. This is by design:
   the block 371000 amendment keeps the Transform as the receipt of the first recognition.
   The same 18 rows differ before the fix. The prereg's 100% prediction did not account for
   the amendment.

`status` and `covered_by` agree on every row in all three streams.

### 2.2 Why H-2 fails

The 35 re-armed views are re-recognised by the transform rung or the dimension rung (22
`recognized`, 13 `recognized_transformed`). The GenInfer stage only fires on residuals those
rungs leave, so it never runs on these views. `gen_checked` is therefore 0 after the reset,
which is the correct state. H-2 asserted that every re-armed view gets a fresh GenInfer look.
The views in stream (b) do not need one.

Stream (a) does not exercise GenInfer at all (`gen_infer_enabled` is off in the affect
graph), so its H-1 agreement says nothing about G1. No stream contains a re-armed residual
that GenInfer must decide afresh. That case is untested.

### 2.3 Post-hoc diagnostic (not a pre-registered gate)

The same recorded rows were compared on guard truth: `gen_explained == 1` on each side,
with `status` and `covered_by`. The test is `test_posthoc_guard_truth_rearm_equals_fresh`.

| stream | n | fix: guard-truth disagreements | pre-fix control: full-tuple agreement | pre-fix control: guard-truth disagreements |
|---|---|---|---|---|
| (a) affect | 23 | 0 | 23/23 | 0 |
| (b) det1 views | 35 | 0 | 4/35 | **13** |
| (c) tromino | 1 | 0 | 1/1 | 0 |

The pre-fix control removes the two resets from `sd_redecode` in memory, through a
`seed_loader.manifest_for` monkeypatch; the seed is not edited. Its 13 rows are the shear
views `F/shearY`, `T/shearX`, `T/shearY`, `U/shearX`, `U/shearY`, `V/shearX`, `V/shearY`,
`L/shearX`, `L/shearY`, `N/shearX`, `N/shearY`, `X/shearX` and `X/shearY`. Each kept
`gen_checked = 1` and `gen_explained = 1` from the first pass, which is the stale state G1
described. The fix removes all 13.

## 3. H-3: regression comparison by node id

**Set.** The block 371000 scoped set: [`SD_LOOP_REARM_SCOPE.txt`](SD_LOOP_REARM_SCOPE.txt)
minus `test_humanoid_walking_migrated.py`, 2022 ids. It ran with the same id list
(`pytest @ids`) in two detached worktrees: the start commit `dca17cfa` (engine
`d24a8be15ff3`) and the fix `b9dd0783` (engine `614b55413052`).

| tree | failed | passed | skipped | errors | wall |
|---|---|---|---|---|---|
| start `dca17cfa` | 207 | 1730 | 52 | 33 | 1:28:16 |
| fix `b9dd0783` | 207 | 1730 | 52 | 33 | 1:27:58 |

Per-id comparison of the 1970 non-skipped outcome rows: **0 differences**. The shared
failures come from the worktree environment (no `data/`, no gitignored `results/`). They
match block 371000's.

**Humanoid walking (32 ids, 3-hour cap per tree).** Both trees finished inside the cap with
31 passed and 1 failed, and the per-id outcomes are identical. Start commit: 2:28:30. Fix:
2:23:17. The shared failure is
`test_graph_walks_with_alternating_support_and_bounded_aerial_phases`, with
`bounded_lateral_drift: False` (expected True) on both trees. It is not caused by this
change, and its cause was not investigated here.

## 4. Measurement of committed records (prereg §4)

The prereg asked for each consumer whose codebook stores JSON-string signatures to be
re-measured on the pre-371000 tree (`1281a482`, engine `ebc7f1282082`) and on the current
tree. Separate worktrees were used. Block 372000 itself (engine `614b55413052`) was also
measured for det1 and identity_untangling.

| script | `1281a482` | after 371000 (`dca17cfa`) | after 372000 (`b9dd0783`) | record |
|---|---|---|---|---|
| `det1_measure.py` A2 shears | 12/14, wrong `F→X`, `T→X` | 11/14, wrong `F→U`, `T→N`, `X→V` | 11/14, same | correction note appended to `VISION_DET1_RESULTS.md` |
| `identity_untangling_measure.py` B2 | 61/63, 2 wrong | 60/63, 3 wrong | 60/63, same | correction note appended to `VISION_IDENTITY_UNTANGLING_RESULTS.md` |
| `identity_untangling_measure.py` Regime A, B1, B2 discrimination, B2 floor-b | 49/49; leak `L`; 0/42; 11/21 | same | same | unchanged |
| `agnosia_measure.py` | all 10 checks True | all 10 True | not re-run | unchanged |
| `similarity_measure.py` | measured in block 371000: identical | | | unchanged |
| `identity_seam_measure.py` | **not runnable** | **not runnable** | | `ModuleNotFoundError: No module named 'av'` in `video_probe_measure.jellyfin_frames`. The package was not installed. Unmeasured |

`agnosia_measure.py` needs `PYTHONPATH=$PWD`. Run without it, the exit code was 1 in both
trees; the logged results above come from the rerun.

The correction notes are dated, appended, and leave the original text in place (commit
`173be37c`).

## 5. Gaps

- H-1 and H-2 failed. The guard-truth reading in §2.3 is post hoc. A future gate should
  compare guard truth and exclude the receipt edge from the state, or the reset should
  delete the key. Either change needs its own prereg.
- No stream has a re-armed residual that GenInfer must decide again against a grown
  codebook. The fix is shown to clear stale flags; it is not shown to change a decision.
- `ClosestShape`'s tie site key is the goal Term's JSON, not the old `Argmax` value Term's.
  Census rows from before and after this change name the site differently.
- `identity_seam` is unmeasured (no `av`).
- The `/home/matt/ocelot-atsm-baseline` checkout is a frozen baseline. Its engine lacks the
  `Round` Term, so loading the current seeds there prints
  `skipping malformed rule 'psi_resolve_disposition_gains': bad computed effect arg: UnknownTermType("Round")`.
  This is out of scope and was not touched.

## 6. Provenance

- Branch `gen-fix/v1`. Implementation by the `ocelot-substrate-executor` subagent. The
  regression runs, measurements, xfail marks and post-hoc diagnostic are by the supervisor.
- SHA-256 prefixes at `b9dd0783`: engine artifact `614b554130529e65`, seed
  `196f0362281d2258`, generator `3116537b55f4e233`, `shape_decode.rs` `6c0ef9ccd4e68653`.
- Logs: `/tmp/ocelot_gen_fix/logs/` (`base_g6.log`, `fix_g6.log`, `base_walking.log`,
  `fix_walking.log`, `step*.log`) and `/tmp/ocelot_followup/logs/` (measurements).
