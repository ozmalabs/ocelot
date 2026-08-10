# Photon GraphEye — public eye cutover

Engine **375d08a6f227**, built from this worktree's Rust source. Canonical
post-merge engine **92b1b9f4c787**, `source_match="own"`.
Async-retina canonical engine **670abe005178**, `source_match="own"`.

## Naming correction

The class formerly called `GraphEye` is now `RGBEye` and carries
`__deprecated__ = True`. It remains available for explicit compatibility users
that require fixed Sobel/DoG, Harris, Gaussian blur, colour-component and
contour behavior.

Public `domains.vision_graph.GraphEye` now resolves to
`domains.photon_eye.GraphEye`.

## New sensory floor

The new eye represents:

1. integer photon packets `{retinal_column, wavelength_nm, count}`;
2. graph-resident rod/L/M/S `Photoreceptor` populations with spectral center,
   bandwidth, saturation, dark current, adaptation rate, current/previous
   activation, caught quanta and persistent adaptation;
3. one generic native `photon_transduce` `CognitiveTask` per receptor;
4. deterministic asynchronous execution and serial result fold from the core
   cognitive runtime;
5. graph rules that synthesize each `RetinalPercept`'s intensity, red–green and
   blue–yellow opponent channels, and temporal salience only after every
   receptor in that column has settled for the same input epoch.

The depth buffer is ignored. A range oracle is not a visual stimulus.

## Asynchronous operation

`GraphEye.build()` starts one autonomous Rust area cycle for its vision
substrate. `submit()` / `submit_photons()` only mint epoch-stamped receptor
tasks and return; they never call `run_cycle`.

The retinal area runs at its own configured `retina_tick_hz`, with
`worker_capacity` controlling pure receptor-task parallelism. `latest()` reads
only an epoch for which every retinal column has folded the same receptor
epoch, so callers never observe a half-updated retina. Completed task nodes are
retired after publication. `stop()` owns and joins the autonomous loop.

One-worker mode uses the same area-task cycle as multi-worker mode; worker
cardinality changes throughput, not semantics.

RGB screens remain accepted solely as external compatibility I/O: the adapter
integrates each retinal column into counts at approximate red/green/blue
wavelengths (610/550/460 nm). No `Image`, `Patch`, pixel, Sobel, Harris,
Gaussian or contour node enters the photon eye's graph.

## Gates

- Photon-specific gates: nonblocking submission/autonomous settling, spectral discrimination, receptor adaptation,
  RGB-to-photon boundary, no pixel nodes, depth refusal, public/deprecated name
  split, and worker-count determinism: **7 passed**.
- Async retina/scheduler gates: **23 passed**; asynchronous world-vision gates:
  **15 passed**.
- World-adapter vision integration updated to receptor introspection:
  **27 passed**.
- Standing vision oracle: **214 passed, 10 skipped, 0 failed**.

## Honest boundary

This is the biological sensory floor, not the completed developmental eye.

- Every retinal column currently contains all four receptor classes rather
  than a learned/eccentricity-dependent mosaic.
- Photon arrival statistics are supplied; the eye does not yet simulate an
  optical point-spread function, pupil, lens, bleaching, or stochastic shot
  noise.
- Retinal waves, horizontal/amacrine lateral circuits, ganglion direction
  selectivity, active foveal remeshing, region grouping and object permanence
  remain the existing developmental stages to connect above this floor.
- The new eye intentionally emits no pixel-contour polygons. Objecthood must
  emerge from temporal/retinal structure rather than be inherited from cv2.
