# EYE-VIEW SPLAT RENDER — RESULTS: **A FAITHFUL READ-OUT OF THE EYE'S HELD PARALLAX CARVE. SPLATS DISPLAY THE GRAPH; THE EYE DOES NOT COMPUTE WITH THEM. ALL FOUR PRE-REGISTERED FAITHFULNESS GATES PASS — HOLES STAY HOLES, SPARSE STAYS SPARSE, THE RENDER RE-CARVES TO THE SAME SURFACES EXACTLY (IoU 1.0), THE REFERENCE PLANE IS STATIONARY EXACTLY. THE HONEST PICTURE IS A TODDLER EYE: THREE FLAT TILTED STRIPS AND A HOLE.**

*Pre-registration `VISION_EYEVIEW_PREREG.md`, committed **`6b5256d0d8`** BEFORE any
faithfulness number (only the held-state RECOVERY numbers — eff_surfaces, confab rate,
surface velocities — had been computed, and those are the parallax rung's carve, not
this rung's gates). The four faithfulness gates and their DERIVED tolerances were fixed
in the prereg. Nothing in it was edited after the first gate number.*

## The boundary this render KEEPS (`VISION_SPLATTING_SCIENCE.md`)

The user's question was *"is 3DGS a good way to VISUALISE what the eye is seeing?"* — and
the answer is **yes, ONLY as a read-out.** The splatting adjudication REFUTED "the brain
computes with splats": **Claim C** (a persistent dense internal splat cloud) is refuted by
change-blindness / grand-illusion; **Claim B** (per-scene residual densification =
foveation) is refuted — cortical magnification is a FIXED anatomical gradient + active
gaze, not error-driven densification. So **splats are the DISPLAY; the eye's held state is
the graph (the parallax carve). This render translates what the eye HOLDS into an image.
It does NOT claim the eye computes with splats**, and it cites that boundary. What the
render IS: the "native pose from efference copy" advantage (Claim C-i, SUPPORTED) made
visible — the eye supplies its own poses, so you can look around what it holds.

## ENGINE PROVENANCE (§10) — NO RUST, this rung is an EMIT-ADAPTER

- Branch **`worktree-agent-a368a4419f7981f21`**; base SHA **`91aa551c93`** (contains the
  three required docs + the parallax carve machinery). Prereg commit **`6b5256d0d8`**.
- Engine built in-tree by `scripts/engine_build.sh`: **`e039d2eec2dd`** — **byte-identical
  to the parallax rung's engine** (same Rust source; THIS RUNG ADDS NO RUST). Re-verified
  AFTER the measurement: `engine e039d2eec2dd @ <this worktree>/...` — **unchanged**.
- Migrated provenance gate as its own step, FIRST: **7 passed**.
- The render + all four gates are **pure numpy** — they reuse the parallax rung's carve
  (`parallax_char.make_scene/vector_field/group_common_fate`), which needs no engine. The
  engine is built and the oracle run only to PROVE §9 (no committed result moved).
- **ORACLE `bash scripts/rung7_vision_bench.sh` (with `data/` symlinked, §10.2):** BEFORE
  **222 passed / 0 failed**; AFTER **222 passed / 0 failed**. §9 is trivial (no Rust, no Term, no
  seed) and the oracle confirms it: UNCHANGED.
- **LOAD (§ concurrency):** `os.getloadavg()` recorded in `results/eyeview.json`
  (start `[0.35,0.60,0.72]` → end `[1.97,1.03,0.86]`); render+gates wall **2.1 s**; ≤2
  workers (`OMP_NUM_THREADS=2`). No wall-clock quantity is a verdict — every gate number is
  an exact/counted quantity or a bootstrap-free deterministic measurement.
- **SEED CLAIM 118000–118999 (verbatim, §3 clause 8):**
  ```
  SEED CLAIM 118000-118999: CLEAN -- no collision DETECTED.
    Scope: 823 files with seed sinks; 512 UNRESOLVED sink sites tree-wide (counted, not discarded).
  ```
  The block is ALLOCATED to this rung and drawn from by NONE of its code: the held state
  reuses the parallax rung's already-burned seed **116000** (as pre-registered), and the
  render + gates are deterministic (no RNG). `unknown_sinks: 0` for this rung; 512
  unresolved sinks tree-wide (counted, not discarded). Term enum index 180 remains UNUSED.

## 1. WHAT THE EYE HOLDS (recovered by re-running the deterministic seeded carve)

`results/parallax.json` holds only summaries (eff_surfaces, largest_frac), not per-cell
labels — so the full held state was recovered by RE-RUNNING the parallax rung's carve
(seed 116000, `shifts=[0,3,6]`, `block=8`, `grid=144`, `ref_idx=1`, `τ=√5`). The held
state on the 18×18 = 324-cell field:

| surface | residual velocity (= relative depth) | image band | n cells | confidence | held luminance | anisotropy (2nd-moment) |
|---|---|---|---|---|---|---|
| **FAR** | vx = **−3** | x∈[0,5] | 108 | 1.000 | 125 | **3.04 : 1** (tall thin, vertical) |
| **REF / fixated** | vx = **0** (space constancy) | x∈[6,11] | 91 | 1.000 | 125 | **3.64 : 1** |
| **NEAR** | vx = **+3** | x∈[11,17] | 116 | 0.908 | 134 | **2.74 : 1** |

- `eff_surfaces = 1/Σpᵢ² = 3.142` → **K = round(eff) = 3** (this rounding is threshold-free;
  it falls out of the participation ratio). Rounds to 3 on every seed 116000–116009.
- **The middle plane is the fixated reference at residual velocity 0** — the ungrounded
  fixed point (memory: the centre of gaze is the origin). Space constancy.
- **confab rate (sensed ≠ ground-truth cells) = 8.64 %** (28/324; 6.8–8.6 % across seeds).
- **9 HOLE cells** — the un-carved residual — **all at the right-edge column** (the sensor's
  toroidal-wrap / aperture-corner confabulation). The participation ratio down-weights them
  (top-5 fractions [0.36, 0.33, 0.28, 0.003, 0.003]); the render leaves them as GAPS.

**HOW SPARSE THE HELD STATE ACTUALLY IS (honest, §8):** three FLAT-ish fronto-parallel
strips at three residual velocities, plus a hole strip. There is **no shape, no object, no
occlusion, no colour** — one grayscale luminance texture and a piecewise-constant velocity
field. The render WILL look like three tilted planes with a hole, because that is the whole
of what a moving eye with one SAD motion sensor holds after one known self-shift. **That
accurate picture of a toddler-level eye IS the deliverable.** Overselling it as a scene
would be the failure this project fights.

## 2. THE RENDER (mechanical emit; pure-numpy forward splatter)

Each surface is rendered as a CLOUD of anisotropic Gaussians — one per carved cell
(3DGS-style: many small Gaussians tile a surface; the brief's "Gaussian(s)", plural). Each
cell-splat: mean = (image x, y) lifted to **z = residual velocity** (the depth the eye
MEASURED, reference at z=0 — NOT an invented metric depth); **colour = that cell's HELD
LUMINANCE** (grayscale — colour is NOT invented; memory: luminance is structure, colour is
a sparse sign); opacity = confidence; covariance = `CELL_STD²` rotated to the surface's
principal axis, inflated by (1−confidence) so a low-confidence surface renders MORE DIFFUSE
/ MORE TRANSPARENT. `CELL_STD = 0.5` = **half a coarse cell = half the sensor aperture** —
the sampling grain, which FALLS OUT of the aperture, not picked (confirmed load-bearing:
Gate 3 fails at CELL_STD ≥ 3). The per-surface 2nd-moment anisotropic Gaussian (the ~3:1
ellipse in the table) is the REPORTED "surface's oriented spatial extent". Un-carved cells
get NO splat → a VISIBLE HOLE. Forward render only: project each Gaussian, alpha-composite
front-to-back by z (~90 lines, `scripts/eyeview_render.py`, no training, no heavy dep;
matplotlib only assembles the PNGs).

**One design correction en route (recorded, §7):** the FIRST render used ONE anisotropic
Gaussian per surface and the round-trip FAILED (IoU 0.36) — a single Gaussian's elliptical
core cannot cover a rectangular band, so the re-carve recovered thin cores. The faithful
fix is the 3DGS-native answer: a CLOUD of small Gaussians (which also preserves the
per-cell luminance TEXTURE, more faithful than a mean gray). A SECOND correction: the
velocity-field read-back must be **winner-take-all**, not alpha-blended — a carve LABEL is
a segmentation, not radiance; alpha-blending velocities smeared the REF/NEAR boundary into
intermediate values (0.6, 0.9, 2.9) that BRIDGED the 0→3 gap under τ=√5 and merged two
surfaces. Luminance composites; a velocity label does not. Winner-take-all preserves the
sharp boundaries the carve keys on — and the gate still bites (an over-broad splat whose
tail WINS a neighbour's cell shifts the boundary and drops IoU).

## 3. THE FOUR FAITHFULNESS GATES — ALL PASS (numbers + derived tolerances)

| gate | statistic | derived tolerance | measured | verdict |
|---|---|---|---|---|
| **1 — HOLE-PRESERVATION** | fraction of a KNOWN no-data region (a removed surface, 116 cells) covered by any splat (cell α ≥ 0.5) | **0.0 exact** (a splat on held surfaces cannot reach a region with no surface) | **0.000** (a FILLING renderer would cover **1.00**; natural 9-cell hole coverage **0.000**) | **PASS** |
| **2 — NO OVER-COMPLETION** | render-complexity `round(eff)` of the RE-CARVED field vs held complexity, on sparse arms | render ≤ held (integer counts) | DEPTH **3→3**, 1-surface DEPTH **1→1**, FLAT **1→1** — never exceeds | **PASS** |
| **3 — ROUND-TRIP (analysis-by-synthesis)** | carve → splat → render velocity field → RE-CARVE → count + per-surface IoU | count == K == 3 AND IoU == **1.0** (exact, no number; fallback floor 1−hole_frac = 0.972 from τ=√5) | count **3/3**, per-surface IoU **[1.0, 1.0, 1.0]**, mean **1.000** | **PASS** |
| **4 — PARALLAX / SPACE-CONSTANCY** | across efference-frame poses: reference displacement; others' displacement per unit d | ref = **0.0 exact** (parallax rung's residual = 0); others = held vx | ref **0.0 exactly** (stationary); FAR **−3.0/d**, NEAR **+3.0/d** — matches input | **PASS** |

**The gates have TEETH (positive controls + adversarial sweep):**
- Gate 1: a FILLING renderer (splats stretched over the gap) would cover the known no-data
  region **1.00** — the gate distinguishes a faithful hole from a fill.
- Gate 3: IoU vs CELL_STD (prettify sweep): **0.5 → 1.000 (PASS)**, 1.5 → 0.976, **3.0 →
  0.873 (FAIL)**, 6.0 → 0.781 (FAIL). An inflated/prettified covariance is CAUGHT — a
  beautiful (over-broad) render is a confabulating one, and this gate rejects it. The
  faithful CELL_STD = 0.5 is the derived aperture grain, not tuned to pass.
- Gate 2: the render never has MORE surfaces than the eye holds, on every sparse arm.

**The residual renders as a HOLE, confirmed:** the 9 un-carved right-edge cells receive
NO splat (cell α < 0.5) and appear as gaps in every pose render and in the coverage-α map
(`gates.png`, right panel). The parallax rung's FLAT→one-blob / graph-arm 0-objects null is
the residual in embryo; here the DEPTH residual renders as a visible strip of gaps.

## 4. THE DELIVERABLE PNGs (all under `results/eye_view/`)

| path | what it shows |
|---|---|
| `results/eye_view/pose_d0.png` | efference-frame pose d=0 (reference frame; all three strips aligned) |
| `results/eye_view/pose_d1.png` | efference-frame pose d=1 (REF stationary; NEAR/FAR parallax by ±3) |
| `results/eye_view/pose_d2.png` | efference-frame pose d=2 (NEAR/FAR slid ±6; REF stationary — the dark gaps are where surfaces moved away) |
| `results/eye_view/orbit.png` | NOVEL ORBIT (θ = −0.6…+0.6 rad about the vertical) — the three surfaces SEPARATE in depth (z = the residual velocity the eye measured); the "look around what the eye holds" the efference-copy poses make possible |
| `results/eye_view/held_vs_render.png` | side-by-side: HELD luminance (bands invisible) ∥ HELD carve (3 surface bands + 9 red HOLE cells) ∥ SPLAT RENDER (textured cloud, holes = gaps) |
| `results/eye_view/gates.png` | Gate 1 (removed-surface region = black hole, coverage 0.000) ∥ Gate 3 (re-carve recovers 3 surfaces, IoU 1.000) ∥ render coverage α (dark = HOLE) |

Machine-readable: `results/eyeview.json` (held state, all four gate numbers, PNG paths,
loadavg, wall).

## 5. WHAT IS NOT SHOWN (§8)

- **The eye does NOT compute with splats.** This is a read-out of a graph the parallax rung
  carved. Splatting the held state ≠ the held state being a splat cloud (Claim C refuted).
- **Nothing here says the surfaces are OBJECTS** (inherited from the parallax rung §10): the
  three surfaces are the three depth planes by construction, not inspected for content.
- **No occlusion, no colour, no shape, no metric depth.** z is residual velocity (relative
  depth to the fixated plane), not metres. Colour is held luminance only.
- **One seed's held state** is rendered (116000, the parallax primary). The gates are
  deterministic on it; the held-state recovery (eff→3, confab, hole strip) is stable across
  116000–116009, but the render/gate PNGs are the single primary seed.
- **The round-trip is on the VELOCITY field** (the carve's own representation), not on the
  fine luminance texture — a flat-luminance splat carries no gradient for SAD to track, so
  re-carving a rendered luminance IMAGE is a different, un-run test.

## 6. WHAT I GOT WRONG — in full (§7)

1. **I ORIENTED IN THE SHARED CHECKOUT ON MY FIRST COMMAND** — the exact §11 hazard the
   parallax and closure rungs hit. My first `cd` + `git rev-parse --show-toplevel` returned
   `/home/matt/ozma/internal` (the shared root), not my worktree. Caught on the FIRST
   command, moved ALL work into `.claude/worktrees/agent-a368a4419f7981f21/...`, symlinked
   `data/` (§10.2, not a copy), built + measured only there. Nothing written to the shared
   tree. Disclosed, not elided.
2. **ONE anisotropic Gaussian per surface FAILED the round-trip** (IoU 0.36) — a Gaussian
   core cannot cover a rectangular band. Fixed with the 3DGS-native cloud (many small
   Gaussians), which is more faithful (preserves luminance texture). The round-trip gate
   CAUGHT the lossy first design — the gate working as intended.
3. **I initially alpha-BLENDED velocities in the inverse** and two surfaces MERGED (count
   2/3): a carve label is a segmentation, not radiance. Blended boundary velocities (0.6,
   0.9, 2.9) bridged the 0→3 gap under τ=√5. Fixed to winner-take-all (velocity labels do
   not composite). Diagnosed by printing the re-carved field, not by tuning τ.
4. **The confidence signal is nearly flat** (FAR/REF conf 1.000, NEAR 0.908) — the eye is
   genuinely confident about all three surfaces; the softness the brief wanted from
   confidence shows mainly as the NEAR surface being slightly more diffuse and as the hole
   strip, NOT as three visibly-different softnesses. I did NOT manufacture a confidence
   spread to make the render prettier — reported flat because it IS flat.
5. **The task cited a "~10.67% confabulation" figure; I measure 8.64%** on this seed (6.8–
   8.6% across seeds). I report the MEASURED per-seed rate, not the quoted one.

## 7. LEDGER ROW (for the supervisor to merge into `VISION_PROTOCOL.md`)

*Written here, not there — `VISION_PROTOCOL.md` is not this rung's file.*

| range | used for |
|---|---|
| **118000–118999 (seed_claim CLEAN — this rung DRAWS NO seed in-block; held state reuses parallax's burned 116000; render deterministic. Term enum index 180 UNUSED — NO Rust, NO Term, NO seed rule; a pure EMIT-ADAPTER)** | **EYE-VIEW SPLAT RENDER — a FAITHFUL READ-OUT of the eye's held parallax carve. Answers the user's "is 3DGS a good way to VISUALISE what the eye is seeing?": YES, ONLY as a DISPLAY. Splats render what the eye HOLDS (the parallax carve 116000); the eye does NOT compute with them (`VISION_SPLATTING_SCIENCE.md` Claims B/C refuted — no persistent dense splat cloud, no residual densification). Held state recovered by re-running the deterministic carve: 3 surfaces at residual velocities −3/0/+3 (middle = fixated reference at 0 = space constancy), confab 8.64%, 9 un-carved right-edge HOLE cells. Rendered as a pure-numpy forward splatter: per-carved-cell anisotropic Gaussian CLOUD, z = residual velocity (measured depth, not invented), colour = held luminance (colour NOT invented), opacity ∝ confidence, covariance ∝ (1−confidence); un-carved cells → VISIBLE HOLE. FOUR PRE-REGISTERED FAITHFULNESS GATES ALL PASS: (1) HOLE-PRESERVATION — a KNOWN no-data region covers 0.000 (a fill would be 1.00); (2) NO OVER-COMPLETION — render re-carves to ≤ held on every sparse arm (3→3, 1→1, FLAT 1→1); (3) ROUND-TRIP (analysis-by-synthesis, the StrokeRender/StrokeQuantize precedent) — carve→splat→render velocity field→re-carve recovers 3 surfaces at IoU 1.000 EXACT (winner-take-all inverse; teeth confirmed — IoU drops to 0.87/0.78 and FAILS at inflated CELL_STD 3/6, so a prettified render is caught); (4) PARALLAX/SPACE-CONSTANCY — across efference-frame poses the reference is STATIONARY 0.0 exactly and NEAR/FAR parallax by ±3/d, matching the eye's input. Every threshold FALLS OUT (§13): 1σ Gaussian scale, τ=√5 sensor tolerance, round(eff) participation, CELL_STD=half-aperture, 0-exact / IoU-1.0 (the strongest no-number outcomes). Honest: the held state is a TODDLER eye — three flat tilted strips + a hole, no object/colour/occlusion — and the render shows exactly that, warts and all. PNGs: results/eye_view/{pose_d0,pose_d1,pose_d2,orbit,held_vs_render,gates}.png. WHAT IT GOT WRONG: oriented in the shared checkout on the first command (caught by show-toplevel, moved to worktree); one-Gaussian-per-surface failed the round-trip (0.36) → fixed with a 3DGS cloud; alpha-blended velocities merged surfaces → fixed with winner-take-all (a label is not radiance); confidence is nearly flat and reported flat; measured confab 8.64% not the quoted 10.67%. Provenance its OWN step (7 passed); engine e039d2eec2dd `own` byte-identical to parallax (NO RUST), re-verified post-run; oracle rung7_vision_bench 222/0 BEFORE and AFTER (§9 trivial); seed_claim CLEAN; loadavg [0.35→1.97], ≤2 workers, wall 2.1s.** |

## 8. NAMED NEXT LEVERS (each its own pre-registration)

1. **RENDER THE MOTOR-CLOSED LOOP.** The parallax rung's Δ is a rendering parameter; when
   the eye EMITS a saccade (`seeds/motor_intent_core.json`) the same efference copy drives
   both the parallax AND this render — the pose sequence becomes the agent's own motor acts.
2. **HOLES THAT SELF-HEAL BY LOOKING.** A hole is "I don't hold this yet" (Claim C-i's
   world-as-outside-memory). The next fixation re-carves the hole region; the render should
   FILL a hole only after the eye actually re-samples it — never by inpainting.
3. **DEPTH-ORDER FROM OCCLUSION.** z here is residual velocity (relative depth, no order).
   `vision_border_ownership` + a parallax boundary gives which surface is IN FRONT — a
   render with correct occlusion, not just parallax.
