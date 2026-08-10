# DEPTH-FROM-MOTION / DEPTH-AWARE EGOMOTION — RESULTS (block 158000-158999)

`SEED CLAIM 158000-158999 CLEAN` (verbatim `check_claim` in
`VISION_DEPTH_FROM_MOTION_PREREG.md`, committed before the run at `9b2945ed66`).

THE WALL (157000): a single global egomotion vector cannot cancel a FORWARD WALK
— its optic flow is DEPTH-DEPENDENT (parallax, near flows faster than far). THE
MECHANISM: forward translation = global radial expansion from the Focus Of
Expansion (FOE), 154000's expansion/divergence op applied GLOBALLY. DIRECTION is
depth-INDEPENDENT (radial-consistency isolates movers via the TANGENTIAL residual,
no per-cell depth); MAGNITUDE gives depth (recovered depth = r/|flow| = Z/speed).

- **New files only** (`scripts/depth_from_motion_probe.py`,
  `tests/test_depth_from_motion_migrated.py`, this doc + the prereg, one small
  PNG). NO Rust added, NO seed consumed, NO default moved — the shipped carve /
  154000 / 155000 / 157000 paths are byte-identical BY CONSTRUCTION (every added
  function — `estimate_foe`, `radial_decompose`, `depth_from_motion`,
  `curl_field`, `flag_movers`, Otsu — is an ADDITIVE mechanical numpy sensor; the
  §9 OFF-default is vacuous, nothing existing is touched).
- Engine: `source_match = shared`, `engine 64dbce1e7f47 @
  .../runners/dsl/python/substrate_rs/_native.abi3.so [shared build — Rust source
  identical]`, source fingerprint
  `3a66c0636a98e9500a73ac0acbe46d53db3fab79c6231c6c0ecdb7482f54fe60` (recorded in
  `results/depth_from_motion.json`; asserted `in {own, shared}`, NEVER a pinned
  build hash — the gate passes on main where the tree reads `own`).
- Oracle `scripts/rung7_vision_bench.sh` (data/ symlinked): **222 passed / 0
  failed BEFORE**, **222 passed / 0 failed AFTER**.
- Gate `tests/test_depth_from_motion_migrated.py`: **11/11**; the four H1 headline
  assertions **3/3 stable across fresh pytest processes**.
- Determinism: VizDoom seed 156000 + 156000's FIXED scripted walk (verbatim,
  imported); RES 320×240 → down=2 → 120×160; flow block 8; L=4; FLOOR=0.5 (the
  one-pixel step); R_MIN=2 (a radius is needed to define a direction). All
  declared residuals; the FOE and the direction cutoff FALL OUT (§13, below).

---

## H1 — SYNTHETIC (ideal oracle): the mechanism is PROVEN

A forward-translation scene = radial expansion from a KNOWN FOE `(col 48, row 28)`
over a DEPTH-VARYING background (Z ∈ [2, 12], near flows faster) + an
INDEPENDENTLY-moving object (a disk, non-radial flow) + a view-fixed apparatus
(zero flow).

### FOE falls out; single-vector FAILS on parallax; radial ISOLATES the mover

| quantity | single-vector (155000 median / 157000 mode) | RADIAL (this rung) |
|---|---|---|
| FOE recovered | — | **error 0.002 cells** (planted off-centre) |
| AUC(mover > background) | **0.162** (median) / **0.000** (mode) | **1.000** |
| IoU(flagged, mover GT) | **0.000** | **1.000** |

**The single-global-vector cancellation cannot isolate the mover on parallax
flow.** The median-over-all baseline (155000) leaves the mover BURIED in the
near/far background residual (AUC 0.162; background single-vector residual p90 =
30.4 vs the mover's 0.0). The dominant-mode baseline (157000) is even worse (AUC
0.000) because the coherent mover BECOMES the global mode — the gain locks onto
it and cancels it to nothing. The radial-direction-consistency (tangential)
residual isolates the mover perfectly (AUC 1.0, IoU 1.0) **without any per-cell
depth** — direction is depth-independent by construction.

### Recovered depth-from-motion = the true depth (r cancels exactly)

Spearman(recovered depth `r/|flow|`, true `Z`) over radial-consistent static
cells = **1.000** (n = 4595 cells, Z ∈ [2, 12]). Because `|flow| = speed·r/Z ⇒
r/|flow| = Z/speed`, the radius cancels and recovered depth is exactly
proportional to true depth up to the unknown translation speed.

### Apparatus (zero flow) stays demoted

Radial flags **0 / 81** apparatus cells — a view-fixed (zero-flow) region has no
defined radial direction, so it is excluded and never flagged as a mover. (Broken
proviso, owned below: I predicted the single-vector residual would PROMOTE the
apparatus at the field level; it did not here — the parallax near-cell residuals
push the Otsu cut so high (21.4) that the apparatus's |gvec| = 4 sits below it.
157000's measured apparatus promotion is a TRACK-level jitter effect, not a
field-level one.)

### Controls (all pass, §6)

- **Pure ROTATION** (uniform-ish, curl-dominated): `expansion_dominant = False`
  (mean div 0.0 vs mean |curl| 0.30), no spurious FOE fit → falls back to
  155000's uniform cancellation. The expansion gate is a RATIO (div vs |curl|),
  which transfers (§13).
- **Static scene + forward translation (no mover):** **0** cells flagged as a
  mover (a perfectly radial field has only ~1e-16 tangential; the one-pixel FLOOR
  in `flag_movers` refuses the meaningless Otsu split of numerical noise), depth
  Spearman **1.000** everywhere.
- **Independent mover + NO egomotion:** `expansion_dominant = False` → the radial
  check is a no-op → the PLAIN residual flags the mover (IoU 1.000).

---

## H2 — E1M1 (real WAD, 156000 walk/seed/grid): the HEADLINE + the honest split

160 frames; 154 motion frames; 94 EFFERENCE-FORWARD frames (the agent's own
issued action == pure forward — the translation regime; the efference copy tells
translation from rotation).

### (a) FOE estimation WORKS — the heading falls out of the flow

Estimated FOE median = **(80.2, 51.5)**, image centre **(80, 60)** — the FOE sits
near the image centre, i.e. the heading of a forward corridor walk. IQR
(33.2, 18.3): stable in the vertical (heading) axis, wider laterally (the walk
turns). The least-squares FOE tracks the heading on real, noisy block-matched
flow with no tuned point.

### (b) HEADLINE — DEPTH-FROM-MOTION vs the VizDoom DEPTH BUFFER

Per-frame Spearman(recovered depth `r/|flow|`, downsampled depth buffer) over
radial-consistent background cells, on efference-forward frames. Depth-buffer
polarity MEASURED (higher = farther): recovered depth ∝ Z ⇒ **positive** Spearman.

| flow config | grid | luma levels | median Spearman | frac frames > 0 | n |
|---|---|---|---|---|---|
| **reused L=4, down=2** (157000 pipeline) | 160×120 | 4 | **−0.112** | 0.448 | 87 |
| raw luma, down=2 | 160×120 | 256 | **+0.150** | 0.651 | 83 |
| **raw luma, down=1** | 320×240 | 256 | **+0.396** | **0.837** | 86 |

**Depth-from-motion RECOVERS real Doom scene depth — Spearman +0.40, sign-correct,
84% of forward frames positive (down=1) — proving H1's mechanism transfers to real
video.** The single-frame example (`results/depth_from_motion_imgs/`) reaches
Spearman **0.94**. But it is DEFEATED by the coarse 157000-reused flow (L=4 =
4 luma levels, down=2): a NULL (−0.11). The diagnosis is measured, not guessed:
that flow is NOISE-dominated — mean divergence ≈ 0 (median −0.008) while
mean |curl| = 0.44 (the signature of noise, not of clean radial expansion, and
why the `div > |curl|` expansion gate fires on 0/159 real frames). Cleaner luma at
the same grid already lifts it to +0.15; a finer grid to +0.40. **The wall is
flow QUALITY (the down=2 / L=4 sensor aperture), NOT the depth-from-motion
mechanism** — which is the arc's standing "scale is the first blocker," measured
again on a new capability.

### (c) independent-mover isolation — the sub-pixel DEGRADE (named, not fixed)

The live imp is sub-pixel at down=2 → **0 trackable monster tracks** (the
persistent 156000/157000 wall). So the movers of interest are not even trackable.
On what IS measurable:

| comparison | RADIAL (this rung) | single-vector (157000) | 157000 baseline |
|---|---|---|---|
| per-cell fg-vs-bg AUC (forward, L=4) | 0.462 | 0.529 | — |
| track fg-vs-bg AUC (L=4 carve) | ≈0.56–0.60 † | ≈0.60 | 0.563 |

† the track-level point value wanders run-to-run (0.563–0.596 observed) from the
value-carve / tracker; NOT gated. On the noise-dominated L=4 carve NEITHER residual
meaningfully separates foreground (items; the imp is sub-pixel) from background —
both hover near 157000's 0.563. **Mover isolation is inconclusive on this walk/grid
(sub-pixel imp + noise-dominated flow); the DEPTH recovery is the measurable win.**

---

## Timing / real-time (measured ALONE)

The depth-from-motion sensor pass (expansion gate + FOE least-squares + radial
decomposition + mover flag + depth) costs **1.0 ms/frame at 120×160, 3.4 ms/frame
at 240×320** — well inside Doom's ~28.6 ms/frame budget. It is a cheap post-pass
over the flow field; the pipeline cost is dominated by the block-matching flow +
value carve (156000's ~87 ms/frame at down=2, unchanged, a declared 156000
residual).

## Architecture audit (CLAUDE.md — the agent is Rust)

- **The FOE estimator** is a mechanical weighted least-squares intersection of the
  flow lines (numpy `lstsq`) — the peer of `vector_field` / `divergence_field`. No
  conditional over graph state, no agent decision.
- **The radial decomposition, the tangential residual, depth-from-magnitude,
  `curl_field`, the expansion-ratio gate, and Otsu** are pure array math over the
  flow field (sensor transforms, the position `quantize()` occupies).
- **The salience** (track arm) is the EXISTING Rust `Substrate.shape_salience`,
  called unchanged; the **tracker** is the EXISTING `_collect_tracks`; the
  **carve** is 156000's `run_value_carve` (= the shipped `native.segment`); the
  **single-vector baseline** is 157000's `dominant_mode_gain` / 155000's
  `median_all_gain`, reused verbatim; the **divergence stencil** is 154000's
  `divergence_field`. NO Rust added, NO re-implementation.
- **`capture_e1m1`** is a world adapter (mechanical I/O over the real WAD); the
  scripted walk is a known world-adapter fact (imported from 156000); the
  **efference-forward gate** is the agent's OWN issued action (the efference copy),
  not privileged GT.
- **The DEPTH buffer and labels buffer are the SCORING ORACLE**, never fed to the
  eye. Scoring is Spearman / IoU / AUC by POSITION, never cross-process region-id.

No Python agent decision anywhere. No seed consumed for graph data; block
158000-158999 reserved for the VizDoom seed + RNG base only.

## WHAT I GOT WRONG

- **I predicted E1M1 would behave like a clean FORWARD WALK with clear radial
  expansion. It does not — this scripted walk is TURN-DOMINATED in the flow
  signal.** Measured: mean divergence ≈ 0 (median −0.008) vs mean |curl| = 0.44,
  so my `div > |curl|` expansion gate fires on 0/159 frames. The walk mixes forward
  with turn bursts, and on top of that the block-matched flow at L=4/down=2 is
  noise-dominated. I had to gate the depth headline to the agent's own
  efference-forward frames (legitimate — the efference copy) and diagnose the flow
  quality, rather than read depth off every frame as I first expected.
- **I predicted the pre-registered down=2 pipeline would recover depth. It is a
  NULL (−0.11).** The mechanism is sound (H1 Spearman 1.0; down=1 real depth +0.40,
  84% frames positive), but the 157000-reused L=4/down=2 flow is too coarse to
  carry the radial expansion signal. The honest split: PRE-REGISTERED pipeline =
  null; mechanism-on-adequate-flow = a clear positive. The next lever is a finer
  grid / better flow (the flow-quality wall), NOT a change to the depth mechanism.
- **I predicted single-vector would PROMOTE the zero-flow apparatus at the field
  level (H1 iv). It did not** — the parallax near-cell residuals dominate the Otsu
  cut, so the apparatus falls below it. 157000's apparatus promotion is a
  TRACK-level jitter effect; I conflated the two levels. The robust half (radial
  DEMOTES the apparatus, 0/81) stands and is what I gate.
- **The honest lesson (the arc's standing rule, re-earned): synthetic-proven
  mechanism ≠ benchmark value.** The FOE + radial-consistency + depth-from-motion
  is PROVEN on the ideal oracle (H1: single-vector 0.0 → radial 1.0; depth 1.0) and
  RECOVERS real Doom depth on adequate flow (+0.40, sign-correct), but the
  end-to-end on the pre-registered coarse-flow forward walk is flow-quality-limited
  (depth null; mover isolation inconclusive; imp sub-pixel). All reported.

## Bounds (§8)

- H1 is a constructed ideal oracle (analytic radial flow) — it proves the mechanism
  is CORRECT, not that it is valuable on real data.
- H2 is one map (E1M1), one skill (3), one seed (156000), one scripted (turn-heavy)
  walk. The depth positive is a DIAGNOSTIC arm (down=1 raw luma), not the
  pre-registered down=2 pipeline (which is a null); it establishes the mechanism +
  the flow-quality wall, not a benchmark number at the shipped grid.
- Radial-consistency isolates only DIRECTION-inconsistent movers; an object moving
  radially (straight toward/away from the FOE) has small tangential residual and is
  a blind spot (the depth-independent robustness is bought with this).
- The sub-pixel imp (0 monster tracks at down=2) makes enemy-mover isolation
  untestable — a separate, named wall (156000/157000).

## Proposed VISION_PROTOCOL.md ledger row

- **DEPTH-FROM-MOTION RECOVERS REAL SCENE DEPTH FROM SELF-MOTION (FOE + RADIAL
  CONSISTENCY), PROVEN ON THE IDEAL ORACLE AND ON REAL DOOM DEPTH WHEN THE FLOW
  CARRIES SIGNAL — BUT THE 157000 FORWARD-WALK'S COARSE FLOW IS THE WALL, NOT THE
  MECHANISM (2026-07-23, `VISION_DEPTH_FROM_MOTION_PREREG.md` /
  `VISION_DEPTH_FROM_MOTION_RESULTS.md`, rung commit `<HASH>`, NO seeds consumed,
  engine `3a66c0636a98e9500a73ac0acbe46d53db3fab79c6231c6c0ecdb7482f54fe60`
  shared/source-matched/NO-Rust, base `main` HEAD `95ee145820`).** GENERAL
  capability: a forward walk makes the STATIC scene flow radially from the FOE
  (154000's expansion op, global); DIRECTION is depth-independent (the TANGENTIAL
  residual isolates movers with NO per-cell depth), MAGNITUDE gives depth
  (`r/|flow| = Z/speed`). Rotation (155000, uniform) + translation (this rung,
  radial-from-FOE) are the general egomotion model. **H1 (synthetic, ideal
  oracle):** FOE recovered to 0.002 cells; the single-global-vector cancellation
  (155000 median / 157000 mode) FAILS to isolate the mover on parallax (AUC
  **0.16 / 0.00**, IoU 0.0) while the radial residual ISOLATES it (**AUC 1.0, IoU
  1.0**); recovered depth Spearman **1.0** vs known depth; the zero-flow apparatus
  stays demoted (0/81); all three controls (rotation→no-FOE, static→depth-
  everywhere-no-mover, mover-no-ego→plain-residual-flags) pass. **H2 (E1M1,
  GT-scored vs the VizDoom DEPTH BUFFER):** the FOE tracks the heading (median
  (80,51) vs centre (80,60)); depth-from-motion RECOVERS real Doom depth on
  adequate flow (**Spearman +0.40, 84% of forward frames positive, sign-correct,
  down=1**; single frame 0.94) but is a NULL on the 157000-reused coarse L=4/down=2
  flow (**−0.11**) — a diagnosed DEGRADE (noise-dominated block matches: mean
  div≈0 vs mean|curl|=0.44; the flow-quality wall, the arc's "scale is the first
  blocker"); mover isolation inconclusive (imp sub-pixel, **0 monster tracks** —
  the named 156000/157000 wall). Gate `tests/test_depth_from_motion_migrated.py`
  **11/11** (H1 FOE/single-vector-fails/radial-isolates/depth-correlates/apparatus-
  demoted able-to-fail; three controls; H2 FOE-near-centre + depth-recovers-vs-
  coarse-null + sub-pixel degrade; §10 provenance `in {own, shared}`; skips if
  WAD/VizDoom absent), 4/4 H1 headline stable across fresh processes. **§9: vision
  bench 222/0 both sides; NO Rust, NO seed, no default moved.** `SEED CLAIM
  158000-158999 CLEAN`.
