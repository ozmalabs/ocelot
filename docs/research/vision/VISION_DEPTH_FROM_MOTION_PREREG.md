# DEPTH-FROM-MOTION / DEPTH-AWARE EGOMOTION — PRE-REGISTRATION (block 158000-158999)

Written and COMMITTED before the run (VISION_PROTOCOL.md §3).

## SEED CLAIM 158000-158999: CLEAN

Verbatim `check_claim` (`python3 scripts/seed_claim.py 158000 158999`):

```
SEED CLAIM 158000-158999: CLEAN -- no collision DETECTED.
  Scope: 859 files with seed sinks; 581 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

The block reserves the VizDoom seed + RNG base only (no seed manifest consumed).

## THE WALL (from 157000)

157000 proved efference→residual→salience on UNIFORM egomotion (rotation), and its
dominant-mode gain CAPTURED E1M1's egomotion in 154/159 frames. But the end-to-end
FAILED: E1M1 is a FORWARD WALK, whose optic flow is DEPTH-DEPENDENT (parallax — near
surfaces flow faster than far). A single global translation vector cannot cancel
parallax, so the mover stays buried in the near/far residual (fg-vs-bg AUC 0.563, below
the 0.585 raw baseline; apparatus promoted). THE WALL IS DEPTH-AWARE EGOMOTION.

## THE MECHANISM — forward walk = global radial expansion from the FOE (154000's op, global)

Forward translation makes the STATIC scene flow RADIALLY OUTWARD from the Focus Of
Expansion (FOE = heading point). This is EXACTLY 154000's expansion/divergence op applied
GLOBALLY. Two consequences, one depth-independent (the key):

- **DIRECTION is depth-INDEPENDENT.** Every static point flows radially away from the
  FOE regardless of depth. So a per-cell radial-DIRECTION-CONSISTENCY check (does this
  cell's flow point radially from the estimated FOE?) isolates INDEPENDENTLY-MOVING
  objects (direction-inconsistent) WITHOUT per-cell depth. Formally: decompose flow into
  a radial component (along p−FOE) + a TANGENTIAL component. Static forward-walk flow is
  purely radial ⇒ tangential ≈ 0 at ANY depth; a non-radial mover keeps a tangential
  residual. **Residual = the tangential (direction-inconsistent) component. This is the
  robust, depth-independent egomotion cancellation.**
- **MAGNITUDE gives DEPTH.** For a static (radial-consistent) cell, |flow| = speed·r/Z
  where r = |p−FOE| and Z = depth ⇒ recovered depth = r/|flow| = Z/speed ∝ Z (the r
  cancels exactly). A depth-from-motion field up to the unknown translation-speed scale.

**Reused from 154000 (`looming_common_fate_probe.py`):** `divergence_field` (the same
central-difference stencil) for the expansion gate, and the affine-fit FOE idea. **Added
(mechanical numpy sensors, peers of `vector_field`/`divergence_field`):** `estimate_foe`
(least-squares intersection of the flow lines — falls out, no tuned point), the
radial-direction-consistency (tangential) residual, and depth-from-radial-magnitude.
**Reused from 157000:** the single-global-vector `dominant_mode_gain` baseline (the thing
that FAILS on parallax), `shape_salience`, the `_collect_tracks` tracker, `_auc`, the
E1M1 world adapter + walk/seed/grid, the labels buffer scorer.

## HYPOTHESES, STATISTICS, DECISION RULES

### H1 — SYNTHETIC (ideal oracle, able to fail). A forward-translation scene = radial expansion from a KNOWN FOE over a DEPTH-VARYING background (near flows faster) + an INDEPENDENTLY-moving object (non-radial) + a view-fixed apparatus (zero flow).

- **(i) single-vector FAILS on parallax.** Statistic: AUC(single-vector residual on mover
  cells > on background cells), where single-vector residual = |observed − dominant-mode
  global vector|. Decision: AUC ≤ 0.65 (mover buried in the near/far background residual).
- **(ii) FOE / radial-consistency ISOLATES the mover.** Statistic: AUC(tangential residual
  on mover cells > on background cells) AND IoU(Otsu-flagged tangential cells, mover GT).
  Decision: AUC ≥ 0.90 AND IoU ≥ 0.25, both strictly greater than the single-vector arm.
- **(iii) recovered depth CORRELATES with known depth.** Statistic: Spearman(r/|flow|,
  true Z) over radial-consistent static cells. Decision: Spearman ≥ 0.90 (synthetic, no
  noise ⇒ near-exact since r/|flow| = Z/speed).
- **(iv) apparatus stays demoted.** Statistic: apparatus (zero-flow) cells are NOT flagged
  as movers by the radial residual (excluded — no flow to judge direction), while the
  single-vector residual PROMOTES them (|0 − vec| large). Decision: radial flags 0% of
  apparatus cells; single-vector flags a majority.

### H2 — E1M1 (real WAD, 157000's walk/seed/grid, down=2), GROUND-TRUTH-SCORED against the VizDoom DEPTH buffer + labels buffer.

- **(a) FOE estimated per frame.** Report the FOE distribution + the expansion gate
  (mean divergence vs mean |curl|). A forward corridor walk ⇒ FOE near image centre.
- **(b) HEADLINE — DEPTH-FROM-MOTION vs the VizDoom DEPTH BUFFER.** Statistic: per-frame
  Spearman(recovered depth r/|flow|, downsampled depth buffer) over radial-consistent
  cells (|flow|>floor, r>r_min, |tangential|<Otsu). Report the per-frame distribution +
  the median. Decision: a POSITIVE result is median |Spearman| ≥ 0.30 with a
  CI/distribution excluding 0 (does self-motion recover real scene depth?). Sign reported
  (depth-buffer polarity measured, not assumed).
- **(c) independent-mover isolation vs 157000.** Statistic: per-cell fg-vs-bg AUC using
  the tangential (radial-inconsistency) residual, compared to the single-vector residual
  AUC; AND, at track level, the residual-salience fg-vs-bg AUC with DEPTH-AWARE (radial-
  projected) cancellation vs 157000's single-vector 0.563. Decision: POSITIVE if the
  radial arm beats the single-vector arm by a CI-separated margin. The imp is expected
  sub-pixel at down=2 (0 monster tracks, the 156000/157000 wall) — if so, monster
  isolation is a named DEGRADE and the depth-recovery + FOE-cancellation-vs-single-vector
  is the measurable win.

### CONTROLS (must correspond, §6)

- **Pure ROTATION (uniform flow, no translation).** Expansion gate: mean divergence ≈ 0,
  |curl| dominates ⇒ NO FOE fitted ⇒ fall back to 155000's uniform cancellation. Decision:
  `expansion_dominant` is False; the least squares is NOT spuriously fit to an FOE.
- **Static scene + forward translation (no mover).** All cells radial-consistent ⇒
  tangential residual ~0 everywhere ⇒ NOTHING flagged as a mover; depth recovered
  everywhere (Spearman ≥ 0.90). Decision: max tangential residual low; no Otsu mover split.
- **Independent mover + NO egomotion.** No expansion ⇒ radial check is a no-op ⇒ the
  PLAIN residual (raw flow magnitude) flags the mover. Decision: mover flagged by plain
  flow; the radial machinery does not suppress it.

## PREDICTIONS (stated in advance, with provisos)

- H1 (i)–(iv): I predict all four hold on synthetic GT — the mechanism is analytic (r
  cancels; tangential is depth-free). Proviso: if my depth-varying field is too gentle,
  the single-vector residual might accidentally separate the mover (AUC > 0.65); I make
  the near/far span wide (Z ∈ [2,12]) so the background residual brackets the mover.
- H2 (b): I predict a POSITIVE but MODEST depth correlation (median Spearman ~0.3–0.6):
  real block-matched flow is noisy and quantized, the walk has rotation mixed in (turns),
  and textureless walls give unreliable flow. Proviso that would break: if the walk is
  rotation-dominated on most frames, the FOE is unstable and depth washes out — I will
  gate frames by the expansion score and report coverage.
- H2 (c): I predict the radial (tangential) residual BEATS the single-vector residual on
  per-cell fg-vs-bg (the whole point), but the track-level monster AUC is UNTESTABLE
  (sub-pixel imp, 0 monster tracks — the named 157000 wall). The item (looming pickup)
  fg-vs-bg may or may not clear a CI margin on the noisy carve.
- Honest DEGRADE path: if FOE-based does NOT beat single-vector, or depth does NOT
  correlate with the buffer, I diagnose (noisy real flow / FOE instability / rotation
  contamination / coverage) — a diagnosed negative is a result (§7).

## EXACTLY THE LISTED TESTS

`tests/test_depth_from_motion_migrated.py`: H1 (i)–(iv) able-to-fail; the three controls
(rotation→no-FOE, static→depth-everywhere-no-mover, mover-no-ego→plain-residual-flags);
H2 (depth-vs-depth-buffer Spearman + per-cell fg-vs-bg radial-vs-single-vector, or the
named sub-pixel monster DEGRADE); the §10 provenance assertion is `source_match in
{own, shared}` (NEVER `== "shared"`, NEVER a pinned hash). Reads measured values, never an
exact d2; skips if WAD/VizDoom absent. No sweeps, no re-runs — a further attempt needs a
NEW pre-registration.

## ARCHITECTURE (CLAUDE.md — the agent is Rust)

NO agent decision in Python. `estimate_foe` / radial-consistency / depth-from-magnitude /
divergence / curl are MECHANICAL numpy sensors (peers of `vector_field`/`divergence_field`
/ `quantize`), no conditional over graph state. The salience is the EXISTING Rust
`Substrate.shape_salience`; the tracker is the EXISTING `_collect_tracks`; the carve is the
EXISTING value carve. `doom_world.py`/`capture_e1m1` is a world adapter (mechanical I/O
over the real WAD). The depth + labels buffers are the SCORING ORACLE, never fed to the
eye; scoring is Spearman/IoU/AUC by position, never cross-process region-id. NO Rust added,
NO seed consumed, NO default moved — NEW FILES ONLY, so the shipped carve / 154000 / 155000
/ 157000 paths are byte-identical BY CONSTRUCTION (the §9 OFF-default is vacuous — nothing
existing is touched). Engine `shared` (source identical), asserted `in {own, shared}`.

## OUTCOME (engine + oracle)

- Engine (worktree, no Rust change): `engine 64dbce1e7f47 @ .../runners/dsl/python/substrate_rs/_native.abi3.so  [shared build — Rust source identical]`, `source_match = shared`.
- Oracle `scripts/rung7_vision_bench.sh` BEFORE: recorded in the results doc.
- Oracle AFTER + all H1/H2/control numbers: recorded in `VISION_DEPTH_FROM_MOTION_RESULTS.md`.
