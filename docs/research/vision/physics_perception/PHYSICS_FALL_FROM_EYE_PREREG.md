# PHYSICS FROM OBSERVATION — the fall discovered by the EYE (pre-registration)

*Registered BEFORE any committed gate number. The discriminator below is fixed
here; the results doc reports what fell out of it.*

## The claim under test

The low-res EYE watches an object fall under ONE untuned constant gravity. The
world's only output is **pixels** (a 0/1 cell field). The eye
(`Substrate::segment_and_track`) carves the falling blob as a persistent
`Region`; the **generic order-N loop** (the generalized `TimeInfer`,
`GENERIC_ORDER_N_RESULTS.md`) runs over that tracked object's **perceived cy
trajectory** and — un-seeded, no hand-set order — mints the **order-2** generator
(the fall is uniformly accelerated). The substrate discovers a law of physics
from what it SAW.

## The genuine bar (no scaffolding)

- The world graph carries **only pixels + the eye's own Region perception**.
  NEVER a published position / velocity / acceleration / mass / `on_ground` /
  regime attribute. (The gate scans every node attribute and asserts the object's
  ground-truth kinematics never appear; grid cells carry no coordinate either.)
- **Gravity is UNTUNED.** g = 1 cell/tick² — the plainest discrete gravity
  (semi-implicit Euler, `v += g; y += v`, integer). Blob = a plain 3×3 square,
  field 30×18. The object size and gravity are NOT chosen to keep the fall
  sub-span (see FALSIFY); they are physically plain and reported.
- The fall-law is **DISCOVERED**, not asserted: no seeded predicate, no
  threshold, no hand-set order. Order-N reads the order off the perceived
  `cy` sequence via one finite-difference recursion.

## Discriminator (registered before any number)

Perceive the SAME pipeline on four worlds; read every verdict FROM THE GRAPH
(`native.evaluate` tuples for the Term; the `run_rules` fixpoint's minted
`LatentDimension{name:'latent:time'}.order` for the seeded path):

| world | eye's perceived `cy` | required order-N verdict |
|---|---|---|
| **untuned fall** (g=1) | accelerating (2nd diff = g) | **order-2** minted from the perceived trajectory |
| **constant velocity** (v const) | arithmetic | **order-1** (NOT order-2) |
| **static** | constant | **nothing** (no acceleration minted) |
| **noise** (no coherent object) | no persistent Region | **nothing** |

"A tracked object" = a Region id the eye holds continuously for at least the
order-2 witness minimum (**4 samples** → ≥2 second-differences; falls out of the
finite-difference pyramid, not tuned). Noise, which holds no id that long, has no
trajectory to feed → nothing.

## Verdicts

- **CONFIRM** — the eye tracks the untuned fall continuously (one Region id, no
  death+birth) for enough frames, order-N mints order-2 from the perceived `cy`
  un-seeded, and the controls give order-1 / nothing correctly.
- **DEGRADE** — it works but with a real caveat: the eye tracks cleanly only for
  the first K frames (before the fall outruns its span) and order-N mints order-2
  only because K is large enough. Report the exact K and the bound.
- **FALSIFY** — the eye loses the object's identity once per-frame displacement
  exceeds `span+2` (`substrate.rs` nearest-centroid `radius = span + 2`), the
  perceived trajectory FRAGMENTS (new Region ids), and order-N never sees a
  continuous ≥4-frame sequence, so no order-2 mints. Prove it with the
  death+birth, name the fix (better cross-frame association for accelerating
  objects), and REFUSE to rescue it by tuning gravity/object-size sub-span.

## Provenance / discipline (registered)

- Branch: `worktree-agent-a2b12e80236a3a424` (own worktree, NOT main).
- **NO Rust, NO new seed.** Composition of existing machinery + a thin pixel
  adapter (`domains/falling_world.py`) + a gate.
- Engine sha256 `88ca162c39f1d2d0d6d778f906316dece9b51e11ca4594d5497cf271b8d35c88`,
  `source_match = shared` (byte-identical Rust source to this worktree; no Rust
  edited so no own-build required — asserted in {own, shared}).
- Seed: `SEED CLAIM 138000-138999: CLEAN -- no collision DETECTED.` (noise RNG
  seeded at the block base 138000).
- Oracle `scripts/rung7_vision_bench.sh` (with `data/` symlinked): **BEFORE
  222 passed, 0 failed (222/0)**. AFTER to be recorded (no Rust ⇒ expected 222/0).
- Gate: `tests/test_fall_from_eye_migrated.py` — perceived fall mints order-2,
  const-velocity → order-1, static/noise → nothing, all through the eye; the
  world graph carries no published kinematics. Every product read from
  `native.evaluate()` (tuples) and the `run_rules` graph state — never a
  process-pattern wait.
