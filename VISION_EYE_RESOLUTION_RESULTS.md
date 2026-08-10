# EYE RESOLUTION vs the free-fall acceleration signal — RESULTS (block 147000–147999)

**VERDICT: DEGRADE.** The ideal-oracle SIGNAL LAW is confirmed and H2 (exact never
fires) is confirmed, but H1's *threshold* prediction is FALSIFIED (R\* ≤ 64, not a
mid-ladder threshold) and the real-clip payoff DEGRADES: 128×640 mints only a
**degenerate** order-2 (recovered acceleration = 0), 64×320 floors on aperture
overrun. **The wall on the real clip is SENSING (block-SAD aperture overrun +
carve/track noise), exactly the frontier 146000 named — not resolution, not the
witness, not frame-count.** Resolution ALONE does not suffice on this slow-mo clip.

---

## SEED CLAIM 147000-147999: CLEAN

Verbatim `python3 scripts/seed_claim.py 147000 147999` (PROTOCOL §3 clause 8 —
including the unresolved-sink count):

```
SEED CLAIM 147000-147999: CLEAN -- no collision DETECTED.
  Scope: 846 files with seed sinks; 564 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

This rung draws **no seed** (measurement only). The confirmatory RNG stream used
by the random control is `default_rng(147000 + R)` — inside the declared block.

## Engine provenance (PROTOCOL §10)

`source_match == "shared"`, engine `64dbce1e7f47` @ the canonical
`runners/dsl/python/substrate_rs/_native.abi3.so` (byte-identical Rust source to
the merged canonical — this rung builds **NO Rust and touches NO seed**, so the
engine is the shared canonical, asserted by `source_match`, never a pinned hash).
`engine_preamble()` pins in every measuring process; `provenance_stamp()` is
recorded in `results/eye_resolution_measure.json`. The gate asserts
`source_match in {own, shared}` (`test_engine_is_own_or_shared`).

## Oracle bench — UNMOVED (PROTOCOL §9)

- **BEFORE** (HEAD `599aa6de92`, `data/` symlinked): `bash scripts/rung7_vision_bench.sh` → **222 passed / 0 failed** (176.40 s).
- **AFTER** (this branch, `data/` symlinked): **222 passed / 0 failed** (172.80 s).

**Pre-existing reds outside the oracle (verified, NOT introduced by this rung).**
`tests/test_instrument_seams_migrated.py` has 3 failures on base HEAD `599aa6de92`
INDEPENDENT of this rung — verified by removing this rung's 5 files and re-running
the underlying scans: (1) `test_the_measured_ledger_record_is_CURRENT` (blocks
133000–146000 draw seeds the committed `seed_ledger_measured.json` never
recorded — other rungs' neglect; this rung leaves that file byte-identical to
base HEAD and its own `default_rng(147000+R)` control is not a declared block);
(2) `test_every_new_prereg_records_its_check_claim_output` (`VISION_CLOSURE_`,
`VISION_EYEVIEW_`, `VISION_MOTIONENERGY_` PREREGs, all tracked at base HEAD, lack
a check_claim verdict — this rung's `VISION_EYE_RESOLUTION_PREREG.md` records its
own, so it is NOT in the missing list); (3)
`test_the_preamble_gate_binds_NEW_violations_only` (in the enumerated failure
baseline; the preamble audit finds NO `eye_resolution` file). This rung adds no
new red; the oracle is 222/0 both sides.

This rung adds one test file, one measure script, one results JSON — **no Rust,
no seed, no flag**, so the OFF/default path is byte-identical by construction.

---

## H1 — SIGNAL LAW confirmed; THRESHOLD form FALSIFIED (R\* ≤ 64)

Ideal oracle (constant-physical-size hard disc under real Galileo physics,
quantized to R rows, integer region centroid = the eye's cy; n_frames = 12; the
render is the cross-frame map, the cy is in-frame integer). Every order-2 verdict
is the **seed rule** reading back a minted `LatentDimension`; the SNR columns are
the perceived-cy diagnostics.

| R (rows) | \|curv\|=\|med(d2)\| | disp(d2) | SNR=curv/disp | ROBUST witness (graph) | recovered accel (coeff) | EXACT witness (graph) |
|---:|---:|---:|---:|:--|---:|:--|
| 64   | 1  | 2 | 0.50 | **order-2** (time_inferred) | 1  | — (time_none) |
| 128  | 2  | 2 | 1.00 | **order-2** | 2  | — |
| 256  | 4  | 2 | 2.00 | **order-2** | 4  | — |
| 512  | 7  | 3 | 2.33 | **order-2** | 8  | — |
| 1024 | 15 | 2 | 7.50 | **order-2** | 16 | — |

**Signal law CONFIRMED:** the curvature \|median(d2)\| grows ∝ R (1, 2, 4, 7, 15)
while the d2 dispersion stays a fixed ~2-cell floor — SNR ∝ R exactly as predicted
(the reference scoping numbers reproduce: 1,2,4,7,15). The **recovered
acceleration read from the minted generator** (`coeffs[-1][0]`) grows 1 → 16 with
R, ∝ R — the graph-native form of the same law.

**Threshold form FALSIFIED.** H1 predicted a resolution threshold R\* *above which*
the robust witness mints and *below which* it floors. **There is no such floor rung
on the ladder: the robust witness mints genuine order-2 at EVERY R, including the
bottom R=64 (SNR 0.5).** So **R\* ≤ 64** (measured; the lowest rung the render
apparatus supports — at R<64 the disc radius `0.03·R < 2` cells degenerates).

**Why the SNR-ratio prediction was the wrong lens (mechanism):** `robust_order`
(`shape_decode.rs`) is an **MDL** witness — it keys on the **absolute residual
bit-cost** about the median 2nd difference, not on the SNR *ratio*. At R=64 the
residuals about the median are 0–1 cells (cheap in bits) and compress below the
null, so order-2 mints even though curv/disp = 0.5. Higher R grows the curvature
but the residuals stay ~1–2 cells (still cheap). The witness therefore reads the
acceleration across the whole ladder. **Resolution is a real property of the
signal (|curv| ∝ R) but it is NOT the gate on the robust witness — the witness's
floor already sits below R=64.**

## H2 — EXACT NEVER FIRES (confirmed): resolution and robustness are COMPLEMENTARY

Driving the **same** quantized free-fall cy through the default **exact** witness
(`status=='motion_seq'`) mints **nothing at every resolution, including R=1024**
(`time_none`, 0 mints, read from the graph — the whole "EXACT" column above). The
±1 integer-rounding jitter in d2 is resolution-INDEPENDENT, so the exact
all-equal test never becomes satisfiable no matter how high R goes. **This
confirms 146000's robust witness is NECESSARY, not a crutch — resolution cannot
substitute for it.**

## Controls (all hold)

| control (at every R) | status | orders | reading |
|---|---|---|---|
| const-velocity, EXACT integer ramp | time_inferred | **[1]** | order-1, NOT order-2 ✓ |
| const-velocity, RENDERED (sub-cell jitter) | time_none | [] | no false order-2 ✓ |
| static (constant cy) | time_none | [] | mints nothing ✓ |
| random (`default_rng(147000+R)`) | time_none | [] | floors — no confab ✓ |
| exact witness on the free-fall cy | time_none | [] | floors where robust mints (H2) ✓ |

The exact-integer-ramp mints order-1 via the exact-first path (robust never
suppresses an exact mint); the *rendered* constant velocity (with quantization
jitter) floors rather than confabulating order-2 — the robust witness is a strict
order-≥2 capability that does not read acceleration into constant velocity.

---

## H2b — REAL clip, end to end: DEGRADE (128×640 mints, but DEGENERATE)

Real slow-mo free-fall clip (`gravity_freefall_ruler_E6jv9WTcgEQ.mp4`, native
128×640, ~24 fps super-slow-mo), driven END TO END: ffmpeg grey → downsample →
`vector_field` block-SAD → `native.segment_motion` common-fate carve →
velocity-predictive tracker → integer cy → **ROBUST** witness (and the exact
witness on the same cy).

| config | grid | block/aperture | fps | tracked run | perceived cy (int) | d2 | ROBUST | recovered accel | EXACT |
|---|---|---:|---:|---:|---|---|:--|---:|:--|
| 64×320 b6 | 64×320 | 6 | 2 | 6 | `[240,244,248,250,261,258]` | `[0,-2,9,-14]` | **FLOOR** (time_none) | — | floor |
| **128×640 b6** | **128×640** | 6 | 2 | 7 | `[394,398,406,414,420,426,431]` | `[4,0,-2,0,-1]` | **order-2** (time_inferred) | **0** | floor |
| 64×320 b4 | 64×320 | 4 | 3 | 5 | `[202,205,206,210,210]` | `[-2,3,-4]` | **FLOOR** | — | floor |
| 128×640 b4 | 128×640 | 4 | 3 | 3 | — | — | run < 4 (no witness) | — | — |

**The literal H2b question answers YES** — at native **128×640 (2× the 64×320
that floored in block 145000) the robust witness flips from FLOOR to a minted
order-2** where 64×320 floors. **But the mint is DEGENERATE: the recovered
acceleration is 0** (coeffs `((4,0),(0,0))` — leading velocity 4, acceleration 0),
versus a clean synthetic parabola of the same length which recovers acceleration 1
(`((1,0),(1,0))`). The perceived velocity `[4,8,8,6,6,5]` is roughly constant with
carve noise; the witness, which excludes order-1, is pushed to a zero-acceleration
order-2 that squeaks past the MDL null. **The real clip does NOT recover the
gravitational curvature at either resolution.**

### The wall is SENSING, not resolution / witness / frame-count (isolated)

Driving the IDEAL oracle at the **real clip's own frame count** (n = 6–7) still
mints **genuine** order-2 with **nonzero, ∝R** acceleration:

| ideal oracle | perceived cy | ROBUST | recovered accel |
|---|---|:--|---:|
| R=64, n=7  | `[3,4,9,17,28,43,60]`        | order-2 | **3** |
| R=128, n=7 | `[5,8,18,34,56,85,120]`     | order-2 | **6** |
| R=320, n=7 | `[11,19,43,83,139,211,299]` | order-2 | **16** |
| R=640, n=7 | `[20,36,84,164,276,420,596]`| order-2 | **32** |
| R=320, n=6 | `[11,22,57,114,195,299]`    | order-2 | **24** |

So **7 frames are plenty** and the **witness is fine** — the ideal oracle recovers
genuine acceleration at the real clip's frame count and resolutions. **The real
clip fails purely in the SENSING:** the carve+track produces a cy whose per-frame
acceleration (a few cells over the ~7-frame window) is buried under block-SAD
centroid noise (±2–4 cells) and, at 64×320, an aperture-overrun glitch
(`250→261→258`). The ideal-vs-real gap ISOLATES the wall to the carve/aperture —
this rung's whole point.

## H3 — aperture cost twin (characterized; not fixed)

The block-SAD sensor `vector_field` has aperture `radius = block` (a declared §13
magic-number residual): beyond a displacement of its own extent a block shares no
pixels with its source and the match is unconstrained.

| config | max per-frame displacement (cells) | aperture (block) | displacement / aperture |
|---|---:|---:|---:|
| 64×320 b6  | 11 | 6 | **1.83 (OVERRUN)** |
| 128×640 b6 | 8  | 6 | 1.33 (overrun) |
| 64×320 b4  | 4  | 4 | 1.00 (at the limit) |

**Resolution ALONE does not suffice on this slow-mo clip: the aperture is
overrun.** At 64×320 the tracked object moves up to 11 cells/frame against an
aperture of 6 (ratio 1.83) — the block-SAD match becomes unconstrained,
corrupting the cy (`250→261→258`) and flooring the witness. Even at 128×640, where
the mint fires, displacement (8) exceeds the aperture (6) and the carve noise
flattens the recovered acceleration to 0. **This names the foveated /
motion-compensated-search frontier (adaptive/larger aperture + cleaner centroid) —
exactly the sensing frontier 146000 named, and NOT built here.**

---

## WHAT I GOT WRONG

- **I expected a mid-ladder resolution THRESHOLD R\* (H1's headline framing) and
  there is none.** The SNR-ratio intuition (curv grows ∝R, disp fixed, so SNR must
  cross a witness threshold) is the wrong lens for an **MDL** witness: `robust_order`
  keys on the *absolute residual bit-cost*, not the ratio, so it already reads
  order-2 at R=64 (SNR 0.5). R\* ≤ 64. The signal law is real; the threshold on the
  *robust witness* is not — the framing conflated "the signal grows with R" with
  "the witness needs R." They are different claims and only the first holds.
- **I over-anticipated a clean real-clip CONFIRM at 128×640.** The mint fires, but
  it is DEGENERATE (recovered acceleration 0). Reading only the mint *status*
  (time_inferred/order-2) would have been the mistake 140000/144000 warn about
  ("synthetic-proven mechanism ≠ benchmark value"); the recovered *coefficient*,
  read from the graph, is what exposes it. The honest headline is DEGRADE.
- **The rendered constant-velocity control does not mint order-1** (it floors),
  because sub-cell quantization jitter is not exactly constant velocity and the
  robust witness excludes order-1. I added a clean **exact integer-ramp** control
  for the "order-1 not order-2" prereg control, and report the rendered one as the
  separate "no false order-2" bar. Both are in the gate.
- **Worktrees lack gitignored files** (PROTOCOL §10.2): `data/` and the
  `naming_corpus/` clip were absent; symlinked from the canonical tree before any
  measurement (the eye bench needs `data/`; H2b needs the clip).

## Files

- `scripts/eye_resolution_measure.py` — the gated measurement (Parts A/B, controls,
  frame-count isolation). NO Rust, NO seed; every verdict is the seed rule read
  back from the graph.
- `tests/test_eye_resolution_migrated.py` — the gate (20 passed): robust mints
  order-2 at both ends of the ladder (graph-read), recovered acceleration grows
  with R (graph-read coeff), exact never mints (H2), const-velocity→order-1,
  random/static floor. Every assertion reads a minted `LatentDimension`, not a
  Python re-derivation, and each is able to fail.
- `results/eye_resolution_measure.json` — the full record incl. `engine_provenance`.

## Proposed ledger row for VISION_PROTOCOL.md

```
| **147000–147999 (measurement only; NO Rust, NO seed, NO flag — drives the 146000 witnesses)** | **RESOLUTION IS NOT THE FREE-FALL LEVER — the wall is SENSING, as 146000 said (DEGRADE).** Tests whether grid RESOLUTION lifts a free-fall's acceleration above the integer-centroid floor. **Ideal oracle (constant-physical-size disc, integer cy, R∈{64..1024}): the SIGNAL LAW holds — |median(d2)| grows ∝R (1,2,4,7,15), d2 dispersion pinned ~2, so SNR∝R; the robust generator's recovered acceleration read from the graph grows 1→16 ∝R. But H1's THRESHOLD form is FALSIFIED: the ROBUST witness mints GENUINE order-2 at EVERY R including the bottom R=64 (SNR 0.5) → R\*≤64. Mechanism: `robust_order` is MDL — it keys on ABSOLUTE residual bit-cost about the median 2nd difference (0–2 cells everywhere), NOT the SNR ratio, so its floor already sits below R=64; the SNR-ratio prediction was the wrong lens.** H2 CONFIRMED: the EXACT witness (`motion_seq`) mints NOTHING from the same quantized cy at ANY R incl. 1024 (±1 rounding floor is resolution-INDEPENDENT) — resolution and robustness are COMPLEMENTARY, not substitutes. **H2b real clip (native 128×640, 2× the 64×320 that floored in 145000), end to end (common-fate carve + velocity-predictive tracker → integer cy → robust witness): DEGRADE. 128×640 flips FLOOR→order-2 where 64×320 floors, but the mint is DEGENERATE — recovered acceleration = 0 (coeffs ((4,0),(0,0)) vs a clean parabola's ((1,0),(1,0))); neither resolution recovers the gravitational curvature.** WALL ISOLATED to SENSING: the ideal oracle at the real clip's OWN frame count (n=6,7) mints GENUINE order-2 with nonzero ∝R acceleration (3,6,16,32) → frame-count and witness are fine; the block-SAD carve/track noise (±2–4 cells) buries the small real per-frame acceleration and, at 64×320, an aperture-overrun glitch (250→261→258) floors it outright. **H3 aperture: max per-frame displacement 11 cells > aperture 6 at 64×320 (ratio 1.83, OVERRUN), 8>6 at 128×640 — resolution ALONE does NOT suffice on this slow-mo clip; names the foveated/motion-compensated-search frontier (NOT built here), exactly the sensing frontier 146000 named.** Controls: const-velocity exact ramp→order-1 (not 2) at every R; rendered const-velocity→floor (no false order-2); static→floor; random→floor; exact floors the free-fall cy the robust witness mints. WHAT IT GOT WRONG: expected a mid-ladder R\* (MDL keys on absolute bits, not SNR ratio → R\*≤64); over-anticipated a clean real-clip CONFIRM (the mint fires but a=0 — read the coeff, not the status); the rendered const-velocity control floors not order-1 (added a clean exact-ramp control). shared engine `64dbce1e7f47`; oracle 222/0 BEFORE and AFTER; gate `test_eye_resolution_migrated` 20/20 (graph-read); `SEED CLAIM 147000-147999 CLEAN`. |
```
