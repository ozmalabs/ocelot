# PRE-REGISTRATION — EYE ON DOOM (block 152000–152999)

**SEED CLAIM 152000-152999:** `CLEAN`

Verbatim `python3 scripts/seed_claim.py 152000 152999` output (§3 clause 8 —
the pasted verdict INCLUDING the unresolved-sink count, not a mention):

```
SEED CLAIM 152000-152999: CLEAN -- no collision DETECTED.
  Scope: 852 files with seed sinks; 571 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

The block is priced with 571 unresolved sinks tree-wide; the claim is that no
collision is DETECTED, never that none exists. This run seeds VizDoom ONCE at
`DOOM_SEED = 152000` (the block base) and draws no other RNG (the carve and the
scoring are deterministic).

## 0. Framing — this is a PROBE, not a CONFIRM

Like the first real-video probe (143000), this rung has NO pre-registered
CONFIRM target and does not spend a confirmatory seed on a directional bet. Its
deliverable is a GROUND-TRUTH-SCORED baseline + a precisely isolated wall. A low
IoU with the wall NAMED is the success condition; an impression is not. Doom is
far richer than a blob-on-black, so DEGRADE is expected and is not a failure.

## 1. Hypothesis (two-sided)

Pointing the shipped eye (`native.segment` value-carve and
`native.segment_motion` common-fate-carve) at greyscaled+downsampled Doom RGB
and scoring its carve against VizDoom's per-pixel labels buffer will produce a
NON-TRIVIAL but LOW per-object IoU on enemies, with a set of nameable failure
modes. The two-sided part: it is equally admissible that (a) the carve recovers
enemies at usable IoU (>~0.3) — Doom enemies are high-contrast sprites — OR
(b) background wall texture and the weapon sprite so dominate the carve that
enemy IoU is near zero. Which one, and WHY, is the finding.

For the depth channel: depth-assisted carving is predicted to score HIGHER than
RGB-only (enemies are nearer than walls, so they pop in the depth buffer), but
the magnitude of the gap is unknown and is measured, not asserted.

## 2. The statistics, exactly

Per carve mode (value / motion / depth), per condition (stationary / turning),
per quantization level L∈{4,8}:

- **enemy IoU**: for each ground-truth enemy object (labels-list entry with
  `object_name != "DoomPlayer"`), the best IoU between its downsampled
  labels-buffer cell-set and any non-ground carved region's cell-set (read from
  the graph via `within` edges). Report mean / median / min / max + the RAW
  per-frame distribution.
- **recovery (recall)** of enemy GT objects at IoU thresholds {0.1, 0.25, 0.5}
  — reported at ALL three, never one tuned threshold.
- **precision / false-positive regions**: non-ground carved regions matching no
  GT object at the loosest threshold (background/HUD over-segmentation).
- **tracking**: per GT enemy `object_id`, fragmentation = number of distinct
  carved region-ids that best-overlap it over its lifetime (1 = perfect); and
  persistence = fraction of consecutive frames where the best-overlapping carve
  keeps the same region-id.
- **weapon-sprite IoU**: IoU of a carved region against the DoomPlayer
  (value 255, weapon/self sprite) GT mask — the HUD/weapon false-object probe.
- **IoU vs GT enemy area**: enemy IoU as a function of GT enemy size in grid
  cells — the small/distant-enemy resolution wall.

## 3. n, fixed in advance

VizDoom `defend_the_center`, `set_seed(152000)`, capture up to `N_FRAMES = 60`
tics per condition (or until the episode ends). Two conditions × two carve
modes × two levels + depth. n is the number of frames captured (deterministic
under the fixed seed + fixed action), reported with the result. No power
analysis: this is an exploratory probe with no directional CONFIRM, so §3.3's
power requirement (which governs confirmatory claims) does not bind — stated
explicitly rather than skipped silently.

## 4. Confirmatory seeds never used for anything

None spent — this is a probe. The only seed drawn is `DOOM_SEED = 152000`
(VizDoom episode determinism), inside the declared block, seeded once.

## 5. Decision rule / what a null means

There is no accept/reject gate on the IoU. The record is the baseline. A
near-zero enemy IoU is a RESULT (the wall is real and named), not a failure.
The gate (`tests/test_eye_on_doom_migrated.py`) asserts only that (a) the
SCORER is correct on a constructed synthetic case and (b) the probe RAN
end-to-end and recorded well-formed scores — it does NOT hard-code the Doom IoU.

## 6. Exactly the listed measurements. No sweeps.

The two conditions, two carve modes, two L values, and the depth channel are the
complete measurement set. No parameter search over grid size / block / L to
improve the score — those are DECLARED §13 residuals below.

## 7. Prediction, stated in advance (with provisos)

- Enemy IoU will be LOW under RGB-only value carve, dominated by two failure
  modes: (i) background wall texture over-segmenting into many spurious regions,
  (ii) the weapon sprite carving as a persistent large false object.
  *Proviso that would break it:* if Doom enemies are high-contrast enough that
  the value carve isolates them cleanly at IoU>0.3, the "texture floods it"
  story is wrong and the real wall is elsewhere.
- The TURNING condition will collapse the common-fate MOTION carve relative to
  stationary (egomotion floods the flow field so the whole scene moves
  together), driving motion-carve enemy IoU toward zero and non-ground region
  count toward one giant region or many.
  *Proviso:* if motion-carve IoU is already ~0 when stationary, turning cannot
  make it worse and the egomotion wall is masked by an earlier one.
- Depth carve will beat RGB-only value carve on enemy IoU.
  *Proviso:* if the weapon sprite / floor also pop in depth, the depth win is
  smaller than expected.

## 8. DECLARED RESIDUALS (§13 — magic numbers stated, NOT tuned to the score)

- **grid 60×80** = exact 4× area-mean downsample of Doom's 240×320. Chosen to
  preserve aspect and be a clean integer factor, NOT to flatter IoU.
- **block = 4** for `vector_field` (the flow aperture) — already documented as a
  §13 residual in `vector_field`'s own docstring; it is the sensor aperture, not
  claimed to fall out.
- **L ∈ {4, 8}** — L=4 is the eye's SHIPPED default (fb downsample_quantize);
  L=8 reported alongside, not selected.
- **IoU thresholds {0.1, 0.25, 0.5}** — recovery reported at all three; the RAW
  IoU distribution is reported so no thresholded rate is dressed as the result.
- **DOOM_SEED = 152000** — the block base; fixed for reproducibility.

## 9. Architecture audit (CLAUDE.md — the agent is Rust)

- The carve is the EXISTING Rust primitive (`segment_and_track` /
  `segment_motion_and_track` via `native.segment` / `native.segment_motion`),
  byte-identical to the shipped eye. No Rust changed, no seed added.
- The VizDoom driver (`capture_doom`) is a WORLD ADAPTER: it reads bytes from
  the game and hands the eye raw pixels. It decides NOTHING about graph state.
  The labels buffer / labels list are the SCORING ORACLE — never fed to the eye.
- Scoring (`downsample_*`, `quantize`, `iou`, `score_frame`) is pure set
  arithmetic over the carve output and the labels grid. No conditional over
  graph state selects agent behaviour.
- New files only (`scripts/eye_on_doom_probe.py`, this prereg, the results doc,
  the gate). Because nothing existing changed, the coarse/shipped carve path is
  byte-identical BY CONSTRUCTION — the oracle bench must read 222/0 both sides.

## 10. Engine provenance

Engine is `shared`: the loaded native matches the tree's Rust source
fingerprint. The result records `source_match` + `source_fingerprint`; NO build
hash is pinned (§10 / §12 — assert source_match, never a mutable hash).

## 11. Oracle

`bash scripts/rung7_vision_bench.sh` BEFORE = **222 passed, 0 failed** (recorded
before writing any probe code). Re-run AFTER; must remain 222/0 (data/ symlinked
in the worktree).
