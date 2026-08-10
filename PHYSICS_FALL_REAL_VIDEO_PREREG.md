# PHYSICS FROM REAL VIDEO — PRE-REGISTRATION

Registered BEFORE any carve / track / order-N number. Fixes the clip, the
pipeline, the discriminator, and the provenance plan. Committed before the
results doc.

## The claim under test

End to end, on REAL video of a rigid object accelerating under gravity, with NO
seeding of the order: the eye (common-fate carve `segment_motion` + the
velocity-predictive tracker) carves and tracks the falling object as ONE region
down the fall, and the generic order-N loop (`discover_order` → `run_rules`)
mints the **order-2** generator (uniformly accelerated fall) from the object's
REAL PERCEIVED `cy` trajectory — read from the graph. This is the real-footage
counterpart of the synthetic `PHYSICS_FALL_FROM_EYE` (perceived
`cy=[1,2,4,7,11,16]`, order-2).

## The clip (REAL footage — fully disclosed)

- **Source:** YouTube `E6jv9WTcgEQ` — "Slow motion acceleration of gravity trial
  5 at 4000 frames per second." A high-speed-camera physics measurement clip: a
  small white ball in genuine FREE FALL past a vertical measuring ruler, STATIC
  camera, NO person in frame. 128×640 (portrait), 24 fps playback, ~91 s (the
  4000 fps capture played back slow).
- **Why this clip:** the ball is a RIGID mover; the camera is static so the ball
  is the sole significant mover (ruler + background are static → common fate can
  isolate it); the ruler PROVES it is a real gravitational free-fall measurement,
  not a synthetic render. The tall portrait frame gives vertical extent for the
  fall.
- **HONEST sim-vs-real caveat, declared up front:** this is a LAB high-speed
  clip — a bright ball on a light background with a ruler. It is NOT the
  "black-background single-bright-object cheat" (the background is light, the ball
  is small and near-speckle-sized after downsample, and there is a static textured
  ruler), but it IS an easier CARVE than a textured object on a cluttered scene.
  So the carve is served partly by the ball's brightness; the genuine real-video
  test here is the PHYSICS DISCOVERY from a REAL PERCEIVED trajectory (a real
  free-fall filmed by a real camera), not a hard-texture carve. The hard-texture
  carve wall was already located in `VISION_REAL_VIDEO_PROBE_RESULTS.md`; the
  common-fate carve that answers it in `VISION_OBJECT_CARVE_RESULTS.md`.
- **Window & downsample (final values RECORDED in the results doc after
  measurement of the fall extent):** a window spanning the ball's visible fall,
  decoded greyscale (luma only) and downsampled to the eye's working grid
  (target ≈ 48 wide, tall enough to resolve the parabola — stated exactly in the
  results). Quantization = the eye's shipped `downsample_quantize` L=4 default.
  Honest downsample/greyscale only; no clip tuning, no cropping to manufacture a
  clean fall.

## The pipeline (COMPOSE landed machinery — likely NO Rust, NO seed)

Thin video→grid adapter (admissible I/O) + the LANDED primitives:
1. ffmpeg decode → grey → downsample to the eye grid (stated).
2. `motion_group_world.vector_field` (block-SAD) per adjacent frame pair.
3. `native.segment_motion` (common-fate carve `segment_motion_and_track`) per
   frame → `read_regions`.
4. Identify the falling object = the largest non-ground moving region; track it
   by persistent Region id across frames (`longest_continuous_run` logic).
5. Feed the tracked object's perceived `cy` (with `cx`) to
   `discover_order` → `run_rules`; read the minted `LatentDimension.order` from
   the graph. Also read the Rust Term product via `native.evaluate()` (TUPLES).

If Rust or a new seed appears necessary, STOP and report why (it should not be —
this is pure composition).

## Discriminator (registered NOW, before any number)

- **CONFIRM:** the eye carves+tracks the real falling ball as ONE trajectory, and
  order-N mints **order-2** (accelerating fall) from that REAL perceived `cy`,
  un-seeded, read from the graph. Report trajectory, minted order/coeffs, and how
  noisy vs the synthetic `[1,2,4,7,11,16]`.
- **DEGRADE:** it tracks the object and the trajectory is fall-shaped, but order-2
  is noisy / only over part of the fall / order-1-with-residual / needs the
  integer eye to jitter. Quantify exactly what is noisy and by how much.
- **FALSIFY (name the wall):** perception cannot hold the ball for enough clean
  frames (too fast → outruns tracking; too short; confab dominates), OR the
  perceived trajectory's integer jitter defeats the exact-constant order-N witness
  (floors to `time_none` / mints a spurious order). Name precisely which wall —
  data, trajectory-length, noise, or tracking-reach.

## Provenance / discipline plan

- Worktree branch `worktree-agent-a142711f0e028d8ab` (NOT main).
- SEED CLAIM 145000-145999 (recorded verbatim in results). The pipeline draws NO
  seed (deterministic decode + block-SAD + Otsu + carve + tracking + finite
  differences).
- Engine hash + `source_match ∈ {own, shared}` asserted from inside the process
  (its own step). Expect `shared` (NO Rust).
- ORACLE `scripts/rung7_vision_bench.sh` (data/ symlinked) 222/0 BEFORE and AFTER.
- Instrument seams `pytest -k migrated` (provenance + failure_baseline): the 3
  pre-existing reds are not mine.
- Every product read from `native.evaluate()` (TUPLES) and the `run_rules` graph
  state — never a process-pattern wait. Per-frame wall-clock + resolution
  recorded. Report what I got WRONG.
