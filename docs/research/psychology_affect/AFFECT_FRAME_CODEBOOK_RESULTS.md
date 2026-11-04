# AFFECT FRAME + CODEBOOK — RESULTS (block 369000)

**Pre-registration:** [`AFFECT_FRAME_CODEBOOK_PREREG.md`](AFFECT_FRAME_CODEBOOK_PREREG.md),
start commit `2e674bd99454403d4a01d90e195ba328e1345723`.

**Outcome: all six gates pass on the second run.** The first run failed G-2, as described
below. The fix was a storage-format bug in the builder that brought the codebook in line
with the prereg's "copies each frame's signature verbatim". No prediction changed.

With the opt-in `affect_frame` seed loaded:
- each fired emotion publishes an integer log₂-level affect frame;
- the unchanged sd loop recognises every frame as its own emotion: 8 exactly and 15 as
  rung-1 transforms with exactly the predicted per-predicate deltas, with zero mint;
- the new `af_direction` rule gets valence direction **121/121** (within category
  **40/40**, against 0/40 for the published `valence` in block 368000);
- arousal direction is 25/25/25/5 as predicted;
- the old `valence`/`arousal`/`emotion` contract is byte-identical.

This is a mechanism result on synthetic appraisal events. Nothing consumes the frame yet,
and nothing here measures a person.

## Source

| item | value |
|---|---|
| start commit | `2e674bd99454403d4a01d90e195ba328e1345723` |
| worktree / branch | `.worktrees/affect-frame` / `affect-frame/v0` (HEAD at run = start commit; new files uncommitted at run time) |
| engine | `engine 5b8c1b5d35e3 @ …/.worktrees/affect-frame/runners/dsl/python/substrate_rs/_native.abi3.so` (shared build; no Rust changed) |
| seed | `seeds/affect_frame.json`, SHA-256 `2e094e7d5d5e7cc1c8c7ea42d0b624375a9fc8beea17196de6410d3e2b17befb`; built twice, byte-identical |
| builder | `scripts/build_affect_frame_seed.py`, SHA-256 `57c6874683e46486800a64aaeb954e5115ff12b28e44eb6453fe78ebac5054f6` |
| test | `tests/test_affect_frame_codebook.py`, SHA-256 `2dde1904f23c19884c01fc453c74ea32ace2e60736e378858d3fae891a99aa71` |
| measurements | `results/affect_frame_codebook.json` (gitignored), SHA-256 `4031ce944c1a39e277ce0d0ed25c1e98198eb47e410f943db3739c9912c94422` |
| command | `OZMA_SEED_PERSIST_DISABLED=1 COLUMNS=250 .venv/bin/python -m pytest tests/test_affect_frame_codebook.py -q -p no:cacheprovider --confcutdir=<worktree>` |
| result | run 2: **8 passed in 2.53 s** |

**Who did what.** The supervising session wrote the prereg and the task brief. The
`ocelot-substrate-executor` subagent implemented the builder, the seed and the test, ran
run 1 and the G-0 regression set, then stopped at the G-2 failure as the brief required.
The supervisor diagnosed the failure from the subagent's evidence, applied the one-line
fix, and ran run 2 and the final regression set.

## Run 1 failure, declared (G-2)

Run 1 gave 7 of 8 tests passing. G-2 failed on one field only: all 8 exactly-matching
frames had `covered_by = "fractal"` instead of their own `affect:<tag>`. The 15
transformed frames already matched on status, base and deltas, and nothing minted.

- **Cause.** The builder stored codebook signatures as JSON strings, `json.dumps(sig)`.
  The brief had suggested this as a default, from how other seeds store signatures.
  - `ShapeDecode` and `TransformDecode` parse a JSON-string signature correctly, which is
    why transformed frames were right.
  - `sd_recognize` computes `covered_by` differently. It takes an `Argmax` of
    `FixedCount(AntiUnify([obs.signature, sig.signature]))` over all `ShapeSignature`
    nodes, and that Term sees a JSON string as one opaque value. Every part therefore
    scored 0, and the tie went to the first node, `fractal`, which comes from
    `shape_decode_loop`'s dependency seeds.
  - The executor's probes: identical native signatures score 6; obs against the
    JSON-string `affect:joy` scores 0.
- **Fix.** Store the frame's signature verbatim as a native list. This is what prereg §2.3
  says ("copies each resulting frame's `signature` verbatim"). The test's codebook reader
  was adjusted to accept a list. No prediction, rule or constant changed. The run-1 seed is
  kept at `/tmp/ocelot_affect_frame/affect_frame.run1_jsonstring.json`, and its measurement
  log is in the executor's report.
- **Finding for the sd loop, independent of affect (inferred, not measured).** By the same
  mechanism, `sd_recognize`'s `covered_by` should be unreliable for any codebook part whose
  signature is stored as a JSON string, which is the convention the stroke and composer
  codebooks use. This rung did not test those codebooks, and did not check whether any
  existing consumer reads `covered_by` from such a part. That should be its own item.

## Gates (run 2)

| gate | prediction | measured | verdict |
|---|---|---|---|
| G-0 default preserved | no change to `core_emotions.json`, its builder, `runners/`; regression set unchanged by node id | diff empty. Regression set (10 files, 123 tests): the 10 baseline failures are unchanged; 2 further failures (`test_instrument_seams_migrated.py::test_the_record_PRICES_ITS_OWN_SILENCE`, `::test_the_static_audit_LANDS_on_the_real_tree_not_only_on_plants`) also fail in the worktree **with `seeds/affect_frame.json` removed**, because they read gitignored `results/` files that a fresh worktree lacks; both pass in the canonical tree | PASS |
| G-1 codebook and frames | 12 codebook entries and 23 frames as §4 | 12/12, 23/23, 0 mismatches | PASS |
| G-2 recognition | 8 recognized + 15 transformed, own base, §4 deltas, 0 mint | 23/23 checked, 0 mismatches; CapabilityAxis 1 → 1 | PASS |
| G-3 valence direction | 121/121, within 40/40 | 121/121, 40/40 | PASS |
| G-4 arousal direction | 25, 25, 25, 5 | threat 25, surprise 25, gain 25, loss 5 | PASS |
| G-5 old contract | 22 read-offs = block 368000 oracle; 221 trials context-free | 22/22; 0 of 221 differ | PASS |

**Exploratory.**
- X-1 (mixed event): two frames, `fear` and `joy`, both `recognized`. The following
  gain trial got no `val_direction`, as designed.
- X-2 (cost): 2.15 s for the whole measurement; 23 `Observation` nodes after the isolated
  run.

## Reading (prereg §6)

- **Treating affect like the substrate's other dimensions works on the existing machinery.**
  A ×2 change in a value signal is a ±1 integer step. The sd loop recognises an emotion at
  any intensity as the same held shape plus a per-predicate transform, as it does for
  rotated strokes. No Rust, no change to the sd loop, and no change to the old contract
  were needed.
- **The measured block 368000 defects are closed in the new channel.** Within-category
  valence direction goes from 0/40 to 40/40. Loss magnitude is now carried by
  `aff:sadness:val_level`. The judgement is made by a graph rule, not an offline observer.
- **Still open:**
  - nothing reads the frame;
  - published sadness arousal is still flat (loss row 5/25);
  - mixed events are decomposed into one frame per emotion but have no valence policy;
  - the codebook comes from canonical exemplars, not from experience.

  The natural next rung is to move a reader (bigville's `ModulatorState` sync, or the PSI
  projection) onto the frame, under its own prereg.

## Limits

- Synthetic events, declared truth columns, harness defaults only.
- Run 2 followed a failed run 1. The fix is declared above. Both runs used the same test
  logic and predictions.
- The G-0 regression set is a scoped slice, not the full `-k migrated` sweep.
- Single machine and a single engine build.
