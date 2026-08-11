# RESIDUAL-SALIENCE — PRE-REGISTRATION (block 157000-157999)

Written and COMMITTED before the run (VISION_PROTOCOL §3).

```
SEED CLAIM 157000-157999: CLEAN -- no collision DETECTED.
  Scope: 857 files with seed sinks; 575 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

`check_claim(157000, 157999)` returned `ok=True` (verbatim above). Block
157000-157999 is reserved for the VizDoom seed + RNG base only.

## The one coupled fix — efference → residual → salience

156000 (`VISION_E1M1_SALIENCE_RESULTS.md`) found two coupled failures that are
ONE thing: (W2) `order_n_shape_salience` ranks the egomotion-swung WALKING
BACKGROUND highest instead of the mover, because it runs on the RAW
trajectories; (W3) E1M1's textured corridors make egomotion sensor-visible (42%
nonzero-flow) but 155000's `calibrate_gain` takes the MEDIAN over ALL cells →
(0,0) below 50% coverage → cancellation is a no-op.

THE FIX composes existing pieces:

1. a **DOMINANT-MODE egomotion gain** — the peak of the flow histogram over the
   MOVING cells (nonzero flow) — robust at 42% coverage where the all-cell
   median reads zero;
2. **cancel** the self-predicted flow (subtract cumulative egomotion from each
   region's trajectory; fold the view-fixed apparatus, exactly 155000's
   `efference_carve` zero-observed-flow readout);
3. run **salience** (`Substrate.shape_salience` = `memory::order_n_shape_salience`)
   on the RESIDUAL trajectories.

**surprise = residual** — salience must run on the residual, not the raw signal.
The capability is general: attend to the world's surprise AFTER cancelling the
self (efference copy). It is an ATTENTION RANKING that works even over a NOISY
carve (156000's E1M1 carve has 276 FP regions/frame) — attention needs a good
ranking, not a clean carve.

## H1 (synthetic — prove the pipeline against an ideal oracle)

**Hypothesis (two-sided).** A synthetic walk = known uniform egomotion + an
INDEPENDENTLY-moving object + a view-fixed apparatus + a textured background
(fragmented into many regions, like E1M1). *Predicted:* RAW salience ranks the
egomotion-swung background as high as the mover (fg-vs-bg AUC ≈ 0.5–0.6,
reproducing 156000). With the dominant-mode gain → cancel → RESIDUAL salience:
the mover ranks ABOVE both the background AND the apparatus (fg-vs-bg AUC →
≈1.0; mover in top-1). Separately, the dominant-mode gain recovers the true
egomotion on a <50%-coverage flow field where the median-over-all-cells reads
(0,0). *Null:* residual AUC ≤ raw AUC, or the mover is not top-1, or the mode
does not recover the true egomotion.

**Statistics, exactly.**
- `auc_raw = AUC(mover salience > background salience)` on raw centroid
  trajectories (Mann–Whitney, the 156000 `_auc`).
- `auc_residual = AUC(mover salience > background salience)` on residual
  (egomotion-cancelled, apparatus-folded) centroid trajectories.
- `mover_rank_residual` = 1-based rank of the mover track by residual salience
  (predict 1).
- `auc_residual_fg_vs_apparatus` (predict 1.0).
- `gain_mode` vs `gain_median_all` vs `E_true` on the coverage flow field
  (exact-equality recovery of the integer egomotion vector).

**Decision rule.** PASS iff `auc_residual > auc_raw` AND
`auc_residual ≥ 0.95` AND `mover_rank_residual == 1` AND `gain_mode == E_true`
while `gain_median_all == (0,0)`. A null on any = the mechanism does not do what
is claimed; report it as a DEGRADE, do not tune.

**n, fixed in advance.** H1 is a constructed ideal-oracle demonstration (like
155000's `run_h1`), not a sampled effect: `n_bg = 12` background tracks, 1
mover, 1 apparatus, `n_frames = 12`. The AUC over 1 positive × 12 negatives is
exact (deterministic given the seed); no power analysis applies to a
constructed oracle. Seed `157001` (pilot/construction), `157002` (background
jitter), `157003` (coverage field) — all in-block.

## H2 (E1M1, ground-truth-scored)

**Hypothesis (two-sided).** On the 156000 E1M1 walk (real WAD, same
deterministic seed 156000 / same scripted walk, down=2), the dominant-mode gain
captures the egomotion (nonzero, where 156000's median gave (0,0)); cancellation
cancels the background; RESIDUAL salience DEMOTES the background — the fg-vs-bg
AUC improves over 156000's 0.588 and the apparatus-demotion stays ≈0.717+.
*Null:* residual fg-vs-bg AUC ≤ raw fg-vs-bg AUC (no improvement), OR apparatus
demotion collapses below the raw 0.717.

**Statistics, exactly.**
- `auc_raw_fg_vs_bg` (reproduce ~0.588), `auc_residual_fg_vs_bg`.
- `auc_raw_fg_vs_apparatus` (reproduce ~0.717), `auc_residual_fg_vs_apparatus`.
- `gain_mode` per-frame distribution vs 156000's median (0,0).
- salience@k (k=1,2,3,5,8), raw vs residual: category of the top-k tracks.
- monster: if ≥1 monster track of length≥3 exists, test
  `auc_residual_monster_vs_bg`; if 0 (the 156000 sub-pixel wall), report the
  DEGRADE explicitly and name the sub-pixel-distant enemy as a SEPARATE wall.

**Decision rule.** WIN iff `auc_residual_fg_vs_bg > auc_raw_fg_vs_bg` AND
`auc_residual_fg_vs_apparatus ≥ 0.70` (apparatus stays demoted). Enemy-promotion
is a SEPARATE, conditional claim (only if a trackable imp exists); its absence
is an honest named DEGRADE, not a failure of the background-demotion win.

**n.** One map (E1M1), one skill (3), one seed (156000, already burned for the
VizDoom RNG in 156000), one scripted walk, one grid (down=2). Deterministic
capture; the AUC is over all tracks scored. This is a mechanism-on-real-data
measurement, reported with its 156000 baseline. Synthetic-proven mechanism ≠
benchmark value — both reported (the arc's standing rule).

## Controls (must correspond to the experiment, §6)

- **No egomotion (stationary).** E=(0,0) → dominant-mode gain ≈ (0,0) → residual
  == raw → salience ranking byte-identical. (able to fail)
- **Static scene + egomotion.** No independent object; egomotion present → all
  residuals ≈ 0 → flat/low salience everywhere (no track ranks high).
- **Independent mover with NO egomotion.** E=(0,0), mover present → mover ranked
  salient with AND without cancellation (residual == raw there).
- **Dominant-mode gain able-to-fail.** On a scene with a KNOWN egomotion and
  <50% flow coverage, the mode recovers the true vector while the old
  median-over-all reads (0,0) — the exact 156000 failure, now fixed.

## §13 — every number falls out, not in

- The dominant **MODE** is the histogram peak — the most common integer flow
  vector over the moving cells. It falls out of the flow histogram; it is NOT a
  tuned threshold.
- The **"moving cell" cutoff** is `|flow| > 0.5` — the block-matcher's own
  one-pixel integer step (155000's `ZERO_FLOOR`, a falls-out quantity, not
  tuned). Reported alongside an Otsu-on-magnitude cross-check.
- **grid (down=2 → 120×160), block aperture (8), level (4), walk, seed (156000),
  skill (3)** are the sensor's aperture / declared residuals, reused verbatim
  from 156000 — NOT tuned to the score.
- Raw distributions reported, not thresholded rates.

## §9 / §10 — defaults and engine

- NEW FILES ONLY (`scripts/residual_salience_probe.py`,
  `tests/test_residual_salience_migrated.py`, this doc + the results doc). NO
  Rust added, NO seed consumed for graph data, NO default moved — the shipped
  carve path and 155000's median-gain path are byte-identical BY CONSTRUCTION
  (the dominant-mode gain is an ADDITIVE new function; the existing
  `calibrate_gain` is untouched).
- Engine `shared`, `source_match` asserted (never a pinned build hash);
  fingerprint recorded in `results/residual_salience.json`.

## Architecture audit (CLAUDE.md — the agent is Rust)

- dominant-mode gain = a mechanical flow-histogram peak (numpy over an array the
  world adapter extracted); the peer of `vector_field` / `quantize`. No
  conditional over graph state.
- cancellation = arithmetic subtraction; apparatus fold = 155000's mechanical
  zero-observed-flow readout.
- salience = the EXISTING Rust operator `Substrate.shape_salience` =
  `memory::order_n_shape_salience`. NO re-implementation.
- tracking = the EXISTING mechanical `_collect_tracks` (nearest-overlap).
- scoring = IoU/position + salience rank vs the labels buffer; never
  cross-process region-id.
- `doom_world` / `capture_e1m1` = a world adapter (mechanical I/O over the real
  WAD, no interpretation). The scripted walk is a known world-adapter fact.

## Prediction stated in advance (with provisos)

I predict RESIDUAL salience beats RAW on fg-vs-bg on BOTH the synthetic oracle
(AUC → ~1.0) and E1M1 (AUC improves over 0.588), and that the apparatus stays
demoted (AUC ≥ 0.70) because folding leaves its trajectory flat. **Proviso 1:**
if the E1M1 per-frame egomotion mode is noisy (the carve is fragmented, 276 FP
regions/frame), residual demotion of the background may be partial — a good
RANKING over a noisy carve, not a clean cancellation; I still predict the AUC
moves in the right direction. **Proviso 2:** the live imp is sub-pixel at down=2
(0 trackable tracks in 156000); I predict enemy-promotion is UNTESTABLE on this
walk/grid and report it as a named sub-pixel DEGRADE, separate from the
background-demotion win. If either the synthetic AUC does not reach ~1.0 or the
E1M1 fg-vs-bg AUC does not improve, that is a DEGRADE I report, not tune away.
