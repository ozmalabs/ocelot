# AFFECT FRAME v0.2 — RESULTS (block 370000)

**Pre-registration:** [`AFFECT_FRAME_V02_PREREG.md`](AFFECT_FRAME_V02_PREREG.md), start
commit `d1e7d6abaaddc2b2c654449427cd12b5e1018486`.

**Outcome: all gates pass, every count exactly as predicted, first confirmatory run.**
- **Mixed events** get one `ComponentDirection` per shared emotion: 15 of 43 mixed trials,
  16 components. Single-frame trials get exactly one component equal to `af_direction`
  (139/221) or none (82/221).
- **The codebook grows from experience** through the sd loop's own mint → grow → re-decode
  cycle: 6 shapes in the predicted order, 6 axes, epoch 6.
- **The latest appraisal's frames are projected** onto the canonical `AffectiveState` for
  all 22 events, with the old attrs untouched.
- **The canonical codebook is now its own seed.** Splitting it out changed none of block
  369000's results.
- **One sd-loop defect predicted by code reading reproduced exactly.** 11 re-armed
  transformed frames are stuck at `decoded` (§1.5).

This is a mechanism result on synthetic appraisal events. Nothing measures a person.

## Source

| item | value |
|---|---|
| start commit | `d1e7d6abaaddc2b2c654449427cd12b5e1018486` |
| worktree / branch | `.worktrees/affect-frame-v02` / `affect-frame/v02` |
| engine | `engine ebc7f1282082` (no Rust changed) |
| `seeds/affect_frame.json` v0.2.0 | SHA-256 `be5c0858b7eedc8c3a597fa4517515af3be200d3a00b6f80de00110aa011d569` |
| `seeds/affect_frame_canonical.json` v0.1.0 | SHA-256 `abb68b5f61a6d5d01ba1c91edd8d96e0eee1dc9cf616f8f96fd6983edd96b4eb` |
| builder | `scripts/build_affect_frame_seed.py`, SHA-256 `24e279dddcd8b219be5ad880feb6cfeb9689adc0587435427ee5ea6b463a29ea`; two runs byte-identical for both seeds |
| tests | `tests/test_affect_frame_v02.py` `35d0da70…`; `tests/test_affect_frame_codebook.py` `39a5fe3a…` (load lines and codebook path only) |
| measurements | `results/affect_frame_v02.json` (gitignored), SHA-256 `fb23190946bfc8629c7a20e684faa2ba41474ff269ec87d3ed386792679d01a7` |
| command | `OZMA_SEED_PERSIST_DISABLED=1 .venv/bin/python -m pytest tests/test_affect_frame_v02.py tests/test_affect_frame_codebook.py -q -p no:cacheprovider` |
| result | 13 passed (executor run, then reproduced by the supervisor: 13 passed in 9.00 s) |

**Who did what.** The supervisor wrote the prereg and the brief. The
`ocelot-substrate-executor` subagent implemented the change and ran the gates. Its one
failure was a harness bug: it sorted `NodeID` objects without a sort key. It fixed that
before any gate value was read. The supervisor reviewed the diff and re-ran the gates.

**Split check.** The 13 block 369000 rules are byte-identical in v0.2.0. The 12 canonical
nodes are identical to block 369000's, and the growth rule was loaded during derivation.
Block 369000's test before and after the split produced identical payloads in every
section, except `header`/`timing` and the wall-clock field of X-2.

## Gates

| gate | prediction | measured | verdict |
|---|---|---|---|
| G-0 isolation | no change to `core_emotions.json`, its builder, `runners/`; neighbouring tests pass | diff empty; `test_core_emotions_migrated`, `test_affect_direction_judgement`, `test_affect_map_reuse_gridcode`, `test_codebook_partition_migrated`: 38 passed | PASS |
| G-1 components, single-frame | 139 with one component = `af_direction`; 82 none | 139; 82; 0 mismatches | PASS |
| G-2 components, mixed | 15 trials, 16 components; `af_direction` unset | 15; 16; unset in all 43; 0 mismatches | PASS |
| G-3 growth | 6 shapes in order, 6 axes, epoch 6, status 8/4/11 with stated deltas | sadness, none, joy, anxiety, fear, surprise; 6; 6; 8 recognized / 4 recognized_transformed / 11 decoded; 0 mismatches | PASS |
| G-4 projection | §4.3 after each of 22 events; old attrs unchanged | 22/22; mixed emitted order fear then joy; old attrs unchanged | PASS |
| G-5 block 369000 re-run | 8/8 with the split seeds | 8 passed | PASS |

## Reading

- **Mixed events: closed.** The policy is "compare like with like". A mixture gets a
  direction for each emotion it shares with the previous appraisal, and no single blended
  valence is invented. The old published `valence` (+1 under a fear label) is unchanged.
  Its readers are an old-contract concern.
- **Codebook from experience: closed.** The first experienced frame of each emotion becomes
  its held shape. The cost is one `CapabilityAxis` per emotion, plus one codebook-epoch bump,
  which re-decodes every earlier observation. Levels are then read relative to that first
  exemplar. For example, the surprise deltas are +1…+4 relative to r = 150, against −1…+2
  relative to the canonical r = 500.
- **A reader for the frame: partly closed.** The canonical `AffectiveState` now carries
  `frame_components`, `frame_count` and `frame_key`. No behaviour reads them yet. Bigville's
  `_sync_affective_state` and the PSI projection still use the old contract. Moving them
  changes behaviour in those worlds and needs a prereg there.
- **Sadness arousal: closed as not a defect** (prereg §1.4). The circumplex places sadness
  at low arousal, and loss size is carried by `val_level`.

## sd-loop findings for their own rung

1. **The re-arm defect, now measured.** `sd_redecode` re-arms `recognized_transformed`
   observations on every codebook growth. The re-decode recomputes `transform_explained`
   = 1, but `sd_recognize_transformed`'s guard ("no `has_transform` edge yet") blocks it. So
   the observation stays `decoded` permanently, although its earlier `Transform` is still
   attached. Here that was 11 of 23 frames. Any codebook that grows while transformed
   observations exist is affected.
2. **`covered_by` with JSON-string signatures** (prereg §1.5, probe on `boot_core`).
   `sd_recognize` scores parts by `FixedCount(AntiUnify(...))`, which treats a JSON-string
   signature as opaque. An exact match then reports the first part in the graph.

## Limits

- Synthetic events, harness defaults only. A single machine and engine build.
- The G-0 neighbour set is a scoped slice, not the full `-k migrated` sweep.
- `frame_*` on `AffectiveState` has no consumer yet.
