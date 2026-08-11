# LOOMING / EXPANSION COMMON-FATE — PRE-REGISTRATION (block 154000–154999)

**The GENERAL capability** (not Doom support): carve an object by the coherent
TRANSFORM its cells undergo across frames — generalizing common-fate from
TRANSLATION ("moving together") to SCALE / EXPANSION ("looming together"). An
approaching object LOOMS: its cells expand radially from a focus of expansion
(FOE), which is near-zero *net* translation flow, so the translation-only
common-fate carve misses or fragments it. Looming is depth-from-motion /
time-to-contact (looming rate `s ∝ 1/TTC`). Doom (`defend_the_center`) is the
EVAL that hands per-pixel ground truth; the capability is general.

## §3 clause 1 — SEED CLAIM (verbatim `check_claim`, run BEFORE the probe file existed)

```
$ python3 scripts/seed_claim.py 154000 154999
SEED CLAIM 154000-154999: CLEAN -- no collision DETECTED.
  Scope: 854 files with seed sinks; 573 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

Seeds used within the block: `154000` (VizDoom `set_seed`), `154001`/`154002`
(synthetic RNG for H1 controls / H1b render). After the probe exists,
`check_claim` naturally reports these as occupied by THIS file; excluding it
returns CLEAN (verified). No other tree file draws in the block.

## Hypotheses (two-sided)

- **H1 (mechanism, SYNTHETIC — the ideal oracle).** Given a flow field with a
  looming object (radial expansion `v(p)=s·(p−foe)`), the EXPANSION carve (the
  common-fate union-find fed the per-cell DIVERGENCE instead of the raw flow
  vector) groups the object into ONE coherent region and the affine read-out
  recovers the KNOWN scale rate `s` and the FOE, where the translation-only
  carve fragments or misses it. Two-sided: it may be that divergence is too
  noisy to group, or the rate is not recoverable — recorded either way.
- **H2 (Doom, ground-truth-scored).** On `defend_the_center` (stationary player,
  approaching enemies loom; seed `154000`, ~2× downsample per 153000's
  real-time ceiling) the expansion carve recovers the looming enemy with
  materially higher IoU than 153000's translation floor (~0.015), scored
  against the labels buffer. Two-sided: if it does NOT, isolate why (loom
  sub-pixel even for expansion? flow too noisy on the small enemy?) — a named
  DEGRADE.

## Statistic (exactly)

- Per-object **IoU by POSITION** (Jaccard of cell-sets) between a carved region
  and the ground-truth object mask; best over carved regions. Reported as a raw
  distribution + mean/median/max.
- **Recovered scale rate** = `trace(A)/2` of the least-squares affine fit
  `v(p)=A(p−c)+t` over the carved region; **FOE** = where the fitted flow
  vanishes; sign discriminates loom (+) / recede (−).

## n, FIXED IN ADVANCE

- H1: 9 constructed cases (3 loom rates, recede, translate, static, noise,
  loom+egomotion, off-axis-FOE) — a deterministic mechanism grid, not a sample.
- H1b: the rendered loom's frames 2..9 (block-SAD flow needs a predecessor).
- H2: the enemy-present frames of a single seeded 60-tic capture (seed `154000`).

## Decision rule

- H1 supported iff, on the analytic loom, the expansion carve IoU exceeds the
  translation carve IoU by a material margin AND the recovered rate matches the
  known `s` to tolerance (|Δ|<0.02) with correct sign for BOTH loom and recede,
  AND the controls floor (translate/static/noise expansion IoU < 0.05).
- H2 supported iff expansion enemy-IoU (mean) > translation enemy-IoU on the
  same capture AND clears the 0.015 floor. Otherwise a NAMED DEGRADE, recorded.
- A NULL (expansion no better than translation) is a real result, reported as
  such (§7), not rescued by changing the measure (§5).

## Prediction (stated in advance, with provisos)

- H1 will hold cleanly on ANALYTIC flow: divergence is exactly `2s` inside a
  uniform loom, so the carve groups it and the affine trace recovers `s`.
  **Proviso:** on RENDERED loom the block-matcher sees a SCALING (non-rigid)
  block, so estimated flow — and its divergence — will be much noisier; H1b may
  degrade sharply. That proviso breaking would tell me the wall is flow
  ESTIMATION, not the carve.
- H2 is genuinely uncertain: a distant enemy looms sub-pixel (153000's finding),
  and divergence of a ~0 flow field is ~0, so expansion may ALSO floor. If it
  clears the floor it will likely be BIMODAL — strong on the close-approach
  frames (super-pixel loom), zero on the distant ones.

## §13 — the grouping criterion contains NO tuned constant

The Otsu tolerance FALLS OUT of the divergence field's own dispersion (the same
`otsu_threshold` the translation carve uses); no expansion constant is injected.
The flow aperture `block` and the downsample factor are DECLARED sensor
residuals (as in 152000/153000), not tuned to the score.

## Architecture (CLAUDE.md)

The grouping is the EXISTING Rust primitive `segment_motion_and_track`,
byte-identical (no Rust added, no seed, no default moved — new files only). The
divergence field and the affine fit are MECHANICAL sensor / measurement
transforms over arrays (no conditional over graph state, no agent decision). The
VizDoom driver is a world adapter; the labels buffer is the SCORING ORACLE.

## Gate

`tests/test_looming_common_fate_migrated.py` — H1 (rate + FOE both signs;
expansion-groups-where-translation-fragments; controls), H2 (expansion > floor
OR named degrade), scorer/read-out correct on constructed cases, translation
carve byte-identical (still fragments the loom). Reads measured/graph values,
skips if VizDoom absent.
