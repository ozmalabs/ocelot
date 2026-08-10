# Vision

By file count this is the largest research thread in the tree (360
`VISION_*.md` documents at the old repo root, now
`docs/research/vision/` — see that folder's `INDEX.md`). This doc is the
current-state summary; the historical arc is enormous and worth reading
directly for anyone building on a specific vision capability.

## What it is, and isn't

**It is an eye** — a retina, an oculomotor system, and the early
dimensional inference an eye feeds (motion, depth, depth-from-many-eyes) —
built on the substrate's own dynamic-quantization loop
(`docs/features/dynamic-quantization.md`), not as a bolted-on vision
module. Every dimension of sight is *discovered* from structured input, not
stored as a hand-set coordinate; every constant falls out of a measured
quantity. Example: the log photoreceptor isn't "a log nonlinearity we
chose" — it falls out because Weber's law *is* a log of the intensity
ratio, and the invariance gain from using it was measured (0.44% vs 100%
error, ~1000×), not assumed.

**It is not a visual cortex.** Form/orientation selectivity via Hebbian
learning was tried, diagnosed as a dead end across five pre-registered
rungs with a measured eigenspectral reason, and retired rather than forced.
Everything the eye does stays inside the **integer/in-frame** class the
frame invariant blesses (`CLAUDE.md`'s "BASE-AS-DIMENSION" section); the
continuous, cross-frame structures (real-angle rotation, a form cortex) are
named as deferred, not faked.

## The developmental arc

The vision work follows a genuinely bottom-up developmental spine rather
than a hand-designed pipeline: `seeds/stage0_prediction.json` →
`stage1_control.json` → `stage2_boundary.json`, where control and boundary
detection are never seeded directly — they're *derived* from prediction
error, the same way a human infant's early vision is thought to bootstrap.
`seeds/sensory_convolution.json` gives the agent sense-agnostic kernel
primitives (`MaxOver(patches, Dot(weights, vals))` +
`keep_discriminative_kernel`); the agent grows its own kernel codebook
bottom-up rather than using hand-picked Sobel/DoG filters, with
center-surround and oriented kernels expected to emerge from natural-image
statistics (an early claim that they had emerged was later retracted on
closer measurement — see `VISION_DEVELOPMENT_ARC.md` for the honest
correction, kept in the record rather than quietly fixed).

## Physics from observation

A named sub-thread (`docs/research/vision/physics_perception/`): the eye
watching an object fall and discovering a law of physics from pixels alone.
The generic order-N loop (`GENERIC_ORDER_N_RESULTS.md`) mints an order-2
generator — uniform acceleration — from a tracked object's trajectory, with
no seeded gravity constant. The witness for "order-k genuinely fits" moved
from exact finite-difference equality (which floors on any real, noisy
video) to a description-length (MDL) comparison — a robust median plus
residual must have *strictly lower* bit-cost than the raw stream — closing
the gap between synthetic and real footage. `GALILEO_EQUIVALENCE_*` extends
this to mass: a robot that pushes objects (discovering inertial mass by
`impulse/Δv`) and watches them fall under the same one constant should find
the two are the same physical quantity, viewed through two different
motor/perceptual frames.

## Doom: the "competent-man" agent

A dedicated sub-thread (`docs/research/doom/`, ~11 documents) applies the
vision loop to VizDoom's first level (E1M1): recognizing doors and switches
by texture (not by reading the game's depth/label buffers, which are used
only as a scoring oracle, never as agent input), then actually operating
them, then narrating its own emotional state while doing it. The honest
null this thread records: a "geometry" recognition channel measured at
chance (AUC 0.508) before a texture-based channel replaced it — the kind of
negative result this project keeps rather than discards.

## The Omniglot / handwriting arc

A ten-plus-run arc (`docs/research/vision/` and `docs/research/audio_speech/`
— handwriting shares machinery with the speech recognition-via-generation
loop) establishing that **generation and reading are one model**:
`StrokeRender` is `StrokeQuantize`'s exact inverse, and reading is
analysis-by-synthesis — propose a quantized index, render it, compare
against the observation. `CLAUDE.md`'s own body text carries the full,
carefully-caveated numbers (including a powered-gate correction that moved
an early ~81%/26.8% split down to a reconciled, CI-separated 73.5% once the
verdict comparator was held constant) — read that section directly rather
than trusting any single number quoted out of context; the standing lesson
from that correction is "power the gate before the endgame."

## Where the code lives

- Rust: vision-adjacent Terms live throughout `runners/dsl/src/` (no single
  `vision.rs` — kernels, change-detection, and the shared `ShapeDecode`
  machinery are the primitives; see `docs/CODE_MAP.md`).
- World adapters: `domains/eye_world.py`, `domains/vision_world.py`, the
  `domains/*_world.py` family for individual illusions/phenomena
  (`domains/mccollough_world.py`, `domains/crowding_world.py`, ...), and
  `domains/doom_pattern_eye.py` for the Doom thread.
- Seeds: `seeds/vision_floor.json`, `seeds/stage0_prediction.json` /
  `stage1_control.json` / `stage2_boundary.json`,
  `seeds/sensory_convolution.json`.
- Gates: `tests/test_vision_*_migrated.py` and the large family of
  phenomenon-specific migrated tests (crowding, McCollough, border
  ownership, ...).

## For the full history

Start with `docs/research/vision/THE_EYE.md` ("a from-scratch, first-
principles eye... every claim here was believed only because it failed
where it had to") and `docs/research/vision/VISION_DEVELOPMENT_ARC.md`.
`VISION_PROTOCOL.md` (repo root — it deliberately did not move into
`docs/research/vision/` with the rest; see `docs/CODE_MAP.md` for why) is
the binding-rules + burned-seed-ledger document every other vision document
cites. The 360-document index is `docs/research/vision/INDEX.md`.
