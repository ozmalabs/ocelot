# PHYSICS FROM REAL VIDEO — RESULTS: **a LOCATED FALSIFY (with a real CONFIRM inside it).**

On a REAL free-fall (a white ball dropped past a measuring ruler, static
high-speed camera, no person), the common-fate eye **carves and tracks the
falling ball as ONE persistent Region id** (CONFIRM on the perception
precondition) — but the generic order-N loop **does NOT mint order-2** from the
real perceived trajectory: it FLOORS to `time_none` in every configuration. The
wall is named precisely and is **exactly the FALSIFY condition the prereg
registered**: *the perceived trajectory's integer jitter defeats the
exact-constant order-N witness*. And the deeper, more interesting finding —
established by driving even the CLEANEST POSSIBLE perception (a bright-blob
oracle) through the same loop — is that **the uniform acceleration IS
perceptibly present in the real trajectory** (the second difference clusters
tightly around a constant ≈3 cells, with five consecutive *exactly*-equal
second-differences visible) yet order-N still floors, because its witness
requires the second difference to be **exactly** constant and real perception
delivers *approximately* constant. The synthetic `[1,2,4,7,11,16]` minted
order-2 because integer Euler physics is exactly constant; real perception is
not. **The wall is a brittle exact-equality witness meeting real noise — not the
carve, and not the tracker.**

Pre-registration `PHYSICS_FALL_REAL_VIDEO_PREREG.md`, committed **`4146db8895`**
BEFORE any carve/track/order-N number. The CONFIRM/DEGRADE/FALSIFY discriminator
was fixed there.

## The clip — REAL free-fall footage, fully disclosed

- **Source:** YouTube `E6jv9WTcgEQ`, "Slow motion acceleration of gravity trial 5
  at 4000 frames per second." A high-speed-camera physics MEASUREMENT clip: a
  small white ball in genuine FREE FALL past a vertical measuring ruler, STATIC
  camera, NO person in frame. A copy is kept at
  `naming_corpus/gravity_freefall_ruler_E6jv9WTcgEQ.mp4`.
- **Raw:** 128×640 (portrait), 24 fps playback, ~91 s (a 4000 fps capture played
  back slow). The ball descends `cy ≈ 10 → 476` raw px over `t ≈ 5 → 83 s`, then
  BOUNCES (cy reverses) — so the downward fall is `t ≈ 5–78 s`. `cx ≈ 62`
  throughout: a clean VERTICAL fall.
- **Downsample:** ffmpeg `fps=<f>,scale=<gw>:<gh>,format=gray`. Greyscale (luma
  only) + downsample to the eye grid, quantized at the eye's shipped `L=4`.
  Primary grid **64×320** (scale 2.0, aspect-preserving) and **48×240**
  (scale 2.667). At 64×320 the ball is a compact ~3–4-cell bright blob — see
  `results/physics_fall_real_video_input.png` (8 frames of what the eye
  processes: the blob descending past the black ruler on a light background).
- **HONEST sim-vs-real caveat (declared in the prereg, restated):** this is a LAB
  high-speed clip — a bright ball on a light background with a ruler. It is NOT
  the "black-background single-bright-object cheat" (the background is light,
  there is a static textured ruler, and the ball is small/near-speckle after
  downsample), but it IS an **easier CARVE** than a cluttered textured scene. So
  the carve here is served partly by the ball's brightness+isolation via common
  fate. The hard-texture carve wall was already located in
  `VISION_REAL_VIDEO_PROBE_RESULTS.md` and answered by common fate in
  `VISION_OBJECT_CARVE_RESULTS.md`; **the genuine real-video test completed here
  is the PHYSICS DISCOVERY from a REAL PERCEIVED trajectory** — a real camera's
  view of a real free fall.

## The pipeline — COMPOSED landed machinery (NO Rust, NO seed)

`scripts/physics_fall_real_video.py`, a thin video→grid adapter (admissible I/O)
over the landed primitives, exactly as pre-registered:
ffmpeg decode → grey → downsample → `motion_group_world.vector_field` (block-SAD)
→ `native.segment_motion` (common-fate carve `segment_motion_and_track`) →
track the object (largest non-ground moving region) by persistent Region id →
`discover_order` (order-N / `run_rules`) on the perceived `cy`. Every product is
read FROM THE GRAPH (`read_regions`, the minted `LatentDimension`) and from the
Rust Term (`native.evaluate`, **TUPLES**). No Rust or seed was needed or written.

## 1. CARVE + TRACK — the real falling ball IS held as ONE Region (CONFIRM)

Registered graph product, five configurations across the fall (per-frame values
read from `read_regions`):

| config | grid | block | frames | longest run | ONE id? | ms/frame |
|---|---|---|---|---|---|---|
| whole_fall 0.5 fps | 64×320 | 8 | 39 | 4 | **yes** | 195 |
| mid 1 fps | 64×320 | 6 | 40 | **9** | **yes** | 195 |
| fast 2 fps | 64×320 | 6 | 40 | 7 | **yes** | 194 |
| fast 2 fps | 48×240 | 4 | 40 | 5 | **yes** | 62 |
| fastest 3 fps | 64×320 | 4 | 54 | 6 | **yes** | 196 |

- In **every** configuration the tracked object is held under **ONE persistent
  Region id** across the continuous run (`run_one_id = True`). Common fate carves
  the real rigid falling ball as one moving region against the static
  ruler/background — the physics-discovery precondition (*one object ⇒ one Region
  trajectory*) is MET on real footage for this rigid mover. This is the CONFIRM
  the earlier equal-value probe could not reach (it shattered a textured object
  into 113–528 regions).
- The runs are SHORT (4–9 frames) because of the **aperture–velocity tension**
  (§3): a fixed block-SAD aperture can only track a velocity-limited slice.

## 2. ORDER-2 DISCOVERY — floors in every configuration (the FALSIFY)

The registered order-N verdict on the perceived `cy` (Rust Term + `run_rules`):

| config | perceived `cy` (from the graph) | d1 | d2 | Term | run_rules |
|---|---|---|---|---|---|
| mid 1 fps | `[60,61,67,72,74,78,84,88,84]` | `[1,6,5,2,4,6,4,-4]` | `[5,-1,-3,2,2,-2,-8]` | explained=**False**, order=0 | **time_none** |
| fast 2 fps | `[173,175,178,180,184,186,190]` | `[2,3,2,4,2,4]` | `[1,-1,2,-2,2]` | explained=**False**, order=0 | **time_none** |
| fastest 3 fps | `[202,205,206,210,210,214]` | `[3,1,4,0,4]` | `[-2,3,-4,4]` | explained=**False**, order=0 | **time_none** |

- **No mint, anywhere.** `native.evaluate(... "explained")` is `False`,
  `... "order"` is `0`, `run_rules` status is `time_none`, zero `LatentDimension`
  minted. Read from the graph and the Term (tuples), not a process wait.
- Two failure shapes are visible: the **fast/short** windows (2–3 fps) are nearly
  LINEAR — the trackable velocity slice is so short that the curvature is tiny and
  `d2` just oscillates around ~0 (constant-velocity + jitter); the **mid** window
  has more curvature but its `d2` is dominated by ±2–8 cell jitter. Neither is an
  exactly-constant second difference, so the honest MDL floor stands.

## 3. WHY — the wall, isolated to the WITNESS, not the carve

I drove the **cleanest possible perception** — a bright-blob oracle (background
subtraction on the raw 128×640, `cx≈62` vertical fall, far smoother than the
block-SAD carve) — through the SAME order-N loop, sampled uniformly over the
clean fall (impact excluded), at the eye grid. It STILL floors:

| N (samples over the fall) | oracle `d2` (grid 64) | mean | std | all-equal? | order-N |
|---|---|---|---|---|---|
| 14 | `[5,4,3,3,3,3,3,-13,9,6,3,-4]` | 2.08 | 5.36 | no | **time_none** |
| 16 | `[3,3,4,1,3,1,4,1,-9,1,10,1,1,-1]` | 1.64 | 3.87 | no | **time_none** |
| 18 | `[1,5,1,1,3,1,3,0,3,-1,-12,11,2,-4,9,2]` | 1.56 | 4.92 | no | **time_none** |

- **The parabola IS present.** At N=14 the second difference is a run of
  **five consecutive exactly-equal 3-cell** values (`…3,3,3,3,3…`) — the uniform
  acceleration is literally readable in the perceived trajectory. But a couple of
  ±1–2-cell perception glitches (the ball's rendered shape/brightness shifts as it
  passes the ruler on a coarse grid, plus integer rounding) break exact equality,
  and the order-N pyramid needs the WHOLE second-difference level to be equal.
- **So the wall is the WITNESS, not the carve or the tracker.** The synthetic
  `[1,2,4,7,11,16]` minted order-2 because integer Euler physics gives `d2`
  **exactly** `[1,1,1,1]` (std 0). Real perception gives `d2` ≈ constant (std
  ~4–5). The exact-equality finite-difference witness — correct and load-bearing
  on integer physics — is **too brittle for real (noisy-integer) perception.**

**A second, compounding wall — aperture vs velocity (why the runs are short).**
Over the whole fall at grid 64×320 the per-frame displacement `d1` ranges from
**~1 cell (top) to ~26 cells (fast end)**, while the block-SAD aperture is only
**4–8 cells** (its `radius=block`, a geometric overlap limit). No single fps/block
covers a free fall's ~30× velocity range: sample slow enough to catch the top and
the fast end outruns the aperture (the ball's motion region fragments / the
tracker drops it); sample fast enough for the fast end and the top's per-frame
acceleration falls below the ±1–2-cell perception jitter. This is why every
trackable run is a short, low-curvature slice.

## 4. VERDICT — FALSIFY (located), carve+track CONFIRMED

Per the registered discriminator this is a **FALSIFY on the order-2 discovery** —
and precisely the FALSIFY branch named in the prereg: *"the perceived
trajectory's integer jitter defeats the exact-constant order-N witness (floors to
`time_none`)."* It is a **located** FALSIFY (the point of the exercise), with a
genuine CONFIRM inside it:

- **CONFIRM:** the common-fate eye carves+tracks the REAL falling ball as ONE
  Region id (all five configs) — the perception precondition holds for a rigid
  mover on real footage.
- **FALSIFY:** order-2 does not mint from the real perceived `cy` (floors every
  time). Wall = **NOISE meets an EXACT-EQUALITY witness** — the uniform
  acceleration is perceptibly present (near-constant `d2`, five exact-3s visible)
  but not exactly constant; compounded by the **aperture–velocity tension** that
  keeps every trackable window short and low-curvature.

**How noisy vs synthetic:** synthetic `d2 = [1,1,1,1]`, std **0**, mints order-2.
Real perceived `d2` (best case, the bright-blob oracle): mean ≈ 2, std ≈ **4–5**,
never all-equal, floors. The graph carve is noisier still (block-quantized motion
centroid) and its windows shorter.

## 5. THE FIX (named, NOT built — would be the next rung)

1. **A noise-tolerant / MDL order-N witness.** Replace exact-equality of the
   deepest finite-difference level with a robust constant test whose tolerance
   FALLS OUT (a RANSAC/MDL fit: is `d2` constant to within the trajectory's own
   dispersion?). This is the real-perception analog of "bins propose, continuous
   decides" — the integer eye PROPOSES a near-constant second difference; a
   robust verdict must DECIDE it is constant. It is a Rust/`shape_decode.rs`
   change (out of scope here: this rung composes only), and it must not become a
   picked threshold.
2. **Multi-aperture / foveated motion sensing** so one pass tracks a fall's full
   velocity range (coarse aperture at the fast end, fine at the top) — the
   variable-aperture idea the memory notes already point at.

## 6. PROVENANCE / DISCIPLINE

- Worktree branch **`worktree-agent-a142711f0e028d8ab`** (NOT main); prereg
  **`4146db8895`** BEFORE any number.
- Engine **`10b553cc0aee`**, **`source_match = shared`** (Rust source identical to
  this worktree's build; NO Rust, NO seed, NO existing file touched by this rung —
  only a new probe script + prereg + this doc). Asserted from inside the process
  via `engine_preamble()`.
- **SEED CLAIM 145000-145999:** `SEED CLAIM 145000-145999: CLEAN -- no collision
  DETECTED.` The pipeline draws NO seed (deterministic ffmpeg decode + block-SAD +
  Otsu tolerance + carve + tracking + finite differences).
- **ORACLE** `scripts/rung7_vision_bench.sh` (data/ symlinked): **BEFORE 222
  passed / 0 failed** (212.93 s); **AFTER 222 passed / 0 failed** (214.21 s).
- Instrument seams `pytest -k migrated` (provenance + failure_baseline): **18
  passed** (the 3 pre-existing reds are not mine). Composed physics gates
  (`test_fall_from_eye_migrated` + `test_generic_order_n_migrated` +
  `test_object_carve_migrated`): **21 passed** — the landed machinery I compose is
  green and byte-unchanged.
- Resolution 64×320 (20480 cells) / 48×240 (11520 cells); per-frame wall
  **62 ms (48×240) – 196 ms (64×320)**, `OMP_NUM_THREADS=2`. Machine-readable:
  `results/physics_fall_real_video.json`. Visual:
  `results/physics_fall_real_video_input.png`.

## 7. WHAT I GOT WRONG (in full)

1. **I expected to feed one tracked window to order-N and get order-2** (the
   synthetic result made it look close). I under-estimated how badly an
   exact-equality witness interacts with integer perception jitter. The
   reframing came from driving the IDEAL bright-blob oracle through the loop and
   watching it ALSO floor — that moved the diagnosis from "the block-SAD carve is
   too noisy" to "the discovery WITNESS is too brittle for ANY real perception,"
   which is the stronger and truer finding.
2. **My first oracle trajectory used frame-differencing** (a motion smear that
   doubles the centroid between old/new ball positions), which added its own
   jitter. I switched to background-subtraction bright-blob for the cleanest
   possible oracle — and it STILL floors. Check every read-back: the diagnostic
   must not add the noise it is measuring.
3. **The bounce contaminated the whole-fall analysis.** cy reverses at the floor
   (~t=78 s), injecting a −50 to −110 second-difference crash that first looked
   like enormous "noise." I had to exclude the impact to isolate the clean fall
   parabola; including it would have mis-stated the wall as raw noise rather than
   an exact-vs-approximate-constant witness problem.
4. **I leaned on an easy carve and must say so.** The bright isolated ball makes
   the CARVE easy relative to the real-texture wall; the honest completed test is
   the physics-discovery-from-real-perception, and I disclose the carve was not
   the hard part on this clip.

## Ledger row (this doc, not VISION_PROTOCOL.md)

| rung | claim | engine | oracle before/after | verdict |
|---|---|---|---|---|
| physics-from-real-video (block 145000-145999) | On a REAL free fall (white ball past a ruler, static high-speed camera, no person; 128×640→64×320 grey L=4), the common-fate eye (`segment_motion` + velocity-predictive tracker) carves+tracks the ball as **ONE Region id** in all 5 configs (CONFIRM on the precondition) — but the generic order-N loop **FLOORS to `time_none`** on the real perceived `cy` in every config (no order-2). Wall = **integer perception jitter defeats the EXACT-CONSTANT order-N witness**: even the cleanest bright-blob oracle shows a near-constant second difference (≈3 cells, five exact-3s visible; mean~2, std~4–5) but never all-equal, so the witness floors — the synthetic minted only because integer Euler physics is `d2=[1,1,1,1]` exactly. Compounded by an **aperture–velocity tension** (block-SAD reach 4–8 vs per-frame displacement 1–26 over the fall) that keeps runs short/low-curvature. Fix named (noise-tolerant/MDL witness; foveated motion), not built. NO Rust, NO seed. | `10b553cc0aee` (shared; NO Rust) | 222/0 → 222/0 | **FALSIFY (located): carve+track CONFIRM, order-2 discovery FALSIFY on the exact-equality witness** |
