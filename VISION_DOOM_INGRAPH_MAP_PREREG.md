# PRE-REGISTRATION — the agent builds a persistent IN-GRAPH MAP of Doom from what it SEES

Block **161000–161999**. Branch `gamma-substrate/doom-ingraph-map`, worktree under
`research/.claude/worktrees/doom-ingraph-map`. Written and committed BEFORE the confirmatory
run (§3). A source correction (walls must be SEEN via depth-from-motion, not read from the
depth buffer) arrived before any commit and is folded in here — this is the first and only
prereg for this rung.

## SEED CLAIM (§3, clause 8 — recorded verbatim)

```
SEED CLAIM 161000-161999: CLEAN -- no collision DETECTED.
  Scope: 859 files with seed sinks; 581 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from one generator...
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots...). A CLEAN RESULT
    MEANS 'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

`check_claim(161000, 161999)` returned `ok = True` (same text). VizDoom seed used for the
E1M1 route: **1234** (well inside the block; the map decode itself draws no RNG).

## HYPOTHESIS (two-sided)

As the agent walks a FIXED, seeded route on E1M1, a persistent, GRAPH-NATIVE spatial map
GROWS from the agent's OWN senses + self-motion — explored free space, SEEN wall geometry,
and human area kinds — with the unknown (unexplored) region first-class as ABSENCE.

- **M1 (it builds):** the explored map GROWS over the walk; it is graph data (has_cell `Cell`
  belief + `SpaceQuantum` area boxes read FROM the graph), not a Python array; the accumulation
  is graph-native rules. *Null:* the map does not grow, or is a Python occupancy grid.
- **M2 (it's accurate, SEEN not read):** the WALL geometry is SEEN — depth-from-motion (block
  158000) on the RGB optical flow, calibrated to world units by the agent's own forward
  displacement (efference copy, 155000). Scored two ways against ground truth: (a) trajectory-
  consistency — the map never registers a wall on a cell the agent walked through; (b) the SEEN
  depth POSITIVELY correlates with the VizDoom depth buffer (Spearman), which is the SCORING
  ORACLE ONLY and is NEVER fed into the map. *Null:* the SEEN depth does not correlate with the
  oracle (rho ≤ 0 / frac_pos ≤ 0.5), or a wall lands on a walked cell.
- **M3 (unknown = absence):** an unexplored cell is neither free nor wall (no node — absent),
  and a `frontier` quantum marks the border; it fills in only as the agent senses it. *Null:*
  unexplored space is pre-filled as free/wall.

## SOURCE DISCIPLINE (the point — audited in the results)

The WHOLE map comes from the eye (RGB) + self-motion. **Both** the VizDoom depth buffer **and**
the labels buffer are SCORING ORACLES ONLY, never inputs:

- **Walls:** SEEN via depth-from-motion on RGB flow. The depth buffer validates the seen depth
  (Spearman), never feeds it.
- **Objects:** NOT placed this rung. Using the labels buffer as an object input would smuggle the
  oracle; the eye's RGB carve as the object source is a **named residual**.

## STATISTIC & DECISION RULE (exactly these; no sweeps)

1. Constructed known-layout gate (deterministic, cross-process): the map registers the expected
   free/occupied cells (able to fail); region kinds (room/corridor/area) fall out of geometry;
   unknown is absent + a frontier is minted; the merge rule (walk-frees-wall) is load-bearing.
2. Real E1M1 run (skips if WAD/VizDoom absent): report `final_cells`, the growth curve,
   `seen_forward_frames`, `M2_trajectory_consistency` (expect 1.0), `M2_walls_on_walked_cells`
   (expect 0), `M2_seen_vs_depthbuffer_spearman` (expect frac_pos > 0.5), frontier/passable counts,
   region-kind census. **Report raw distributions.** Decision: PASS if the constructed gate holds
   AND the real map grows AND trajectory-consistency = 1.0 AND the seen depth correlates positively
   with the oracle. A weak (bounded) correlation is an HONEST DEGRADE (map fidelity bounded by
   seen-depth quality — ties 158000's flow wall), NOT a failure, and NOT a reason to touch the
   depth buffer.

## MAGIC-NUMBER LEDGER (§13 — what each constant falls out of)

- **cell = 64 world units** — doom_world's OWN grid (`Body.x_bin = int(x // 64)`). Not mine.
- **body_w = 1 cell** — the agent's config-space footprint at the 64-unit grid; the corridor/room
  discriminator is body-relative, no aspect-ratio constant.
- **FOV 90°** — VizDoom's default horizontal FOV (engine config).
- **depth-from-motion flow config (grid 320×240, block 16, raw luma)** — the sensor's ADEQUATE
  operating point, MEASURED (coarse DOWN=2 quantized flow NULLs at median rho −0.14; full-res raw
  luma recovers median rho 0.38, in 158000's 0.40–0.94 band). Finer parallax resolution is a sensor
  property (159000's foveation direction), not tuning-to-oracle; FLOOR=0.5 / R_MIN=2 are 158000's
  declared sensor apertures.
- **world depth scale** — the agent's own per-frame forward displacement (efference copy). No
  absolute scale is put in.

## PREDICTION (stated in advance, with provisos)

The constructed gate passes cleanly. The real map grows and is trajectory-consistent by
construction. The SEEN wall geometry correlates positively but WEAKLY with the depth buffer
(I predict median Spearman ~0.2–0.5, frac_pos ~0.7–0.9) — a bounded map, because depth-from-motion
on Doom texture sits near the low end of 158000's flow wall. **Proviso that would teach me
something if it broke:** if the seen depth does NOT correlate at all (frac_pos ≤ 0.5) even on
full-res flow, the world placement or the efference calibration is wrong, not just noisy.

## SCOPE / what is NOT shown

- Absolute wall-position-vs-true-linedef ground truth is NOT extracted (E1M1 geometry parsing is
  out of scope); GT is the depth-buffer correlation + the trajectory consistency.
- Objects are NOT placed (named residual: the eye's RGB carve).
- lava/outside area kinds need a hazard/sky sense (named residuals; the value-keyed lava rule ships
  and is gated, exercised only on the constructed hazard case).
- The full-resolution flow is OFF the real-time ceiling (ties the scale wall); this map build is
  offline.
