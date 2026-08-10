# PARALLAX FROM KNOWN SELF-MOTION — PRE-REGISTRATION

*Rung 116000–116999. Committed BEFORE any confirmatory number. Pilot
characterisation (seeds 116900+) is disclosed in §7; every confirmatory
number below comes from FRESH seeds 116000–116079, drawn only after this file
is committed. Term enum index 180 is ALLOCATED to this rung and will be USED
only if the confirmatory CONFIRM holds AND the mechanism needs a Rust primitive
the DSL cannot express (PROTOCOL §0). The pilot already shows the DSL expresses
it — so the graph-resident realization is a SEED, `parallax_efference`, and
index 180 is expected to remain UNUSED.*

## 0. The insight under test (inherits the closure rung's terminus)

The closure rung (115000) proved, with a working positive control, that **a
single static frame cannot be carved into few-and-large by ANY per-frame
relation** — seven mechanisms failed identically; objecthood lives in TEMPORAL
coherence. This rung tests the architectural completion: **the eye does not
wait for the world to move — it MOVES ITSELF by a KNOWN shift Δ (efference
copy).** It predicts the reference-plane motion field that shift causes and
SUBTRACTS it; what survives is world structure. Over a scene WITH DEPTH the
residual is PARALLAX — piecewise-constant, discontinuous at depth boundaries —
so grouping by common fate carves the scene into surfaces (FEW, one per depth;
LARGE, each surface's full extent). Over a FLAT scene the shift is uniform, the
residual is ZERO everywhere, and nothing carves. This is why the self-generated
shift is not perceived (predicted and cancelled) and the same reason you cannot
tickle yourself.

## 1. The discriminating design — a BYTE-IDENTICAL static frame is the whole rigor

Stimulus (`scripts/parallax_char.py`, reusing `motion_sensor_lib`'s toroidal
periodic textures — exact integer rolls, no border fabrication): ONE periodic
texture `a`. N vertical bands.

- **DEPTH condition:** band i rolled horizontally by its own integer parallax
  shift `s_i` (∝ 1/depth, under a known lateral eye translation) → piecewise-
  constant motion field with discontinuities at the band boundaries.
- **FLAT control:** the SAME frame `a`, uniformly rolled by ONE shift `s_ref`
  (one depth) → uniform field, no boundary.

Because ALL bands share ONE texture, **the depth planes are INVISIBLE in the
static frame `a`** (no luminance/texture structure at the band boundaries), and
**`a` is byte-identical between DEPTH and FLAT — only the post-shift frame `b`
differs.** Anything that carves the identical static frame carves it EQUALLY in
both conditions and so cannot be the discriminator; only parallax vs uniform
motion differs. (Verified in the pilot: static-frame column gradient AT band
boundaries ≈ within-band gradient.)

## 2. The efference copy IS the known Δ — never an estimate

The reference-plane field subtracted is built from the shift I CHOSE (self-
generated, known), NEVER estimated from the image. The residual `R = V − Δ_ref`
is computed in exact integer arithmetic (the SAD sensor emits integer offsets;
`Δ_ref` is an integer shift). Grounded, graph-native realization: the seed
`parallax_efference` replaces `vision_motion_group`'s `mo_dominant` (which
ESTIMATES the reference frame as the largest group's velocity) with the SUPPLIED
`field.efference_v`; the fixated plane then reads STATIONARY (residual 0 =
refused = space constancy).

## 3. The statistics (knob-free — robust to the sensor's confabulation tail)

Group the sensed residual field into spatially-connected regions whose velocity
agrees within τ (common fate). The raw median/count are corrupted by the
sensor's ~11% confabulation specks (the 84000 over-grouping bound), so the
PRIMARY statistics are speck-robust and knob-free:

1. **eff_surfaces = 1 / Σ pᵢ²** (participation ratio / inverse Simpson over the
   group-size fractions pᵢ) — the effective number of surfaces; a tail of
   1-cell confab specks has pᵢ²→0 weight, so it reads the FEW large surfaces.
2. **largest_frac = max group / total cells** — the giant-ground test (the
   closure rung's own condition (c): "largest region NOT most of the frame").

Reported alongside (descriptive, not the verdict): full sorted size
distribution, raw count, median, and the graph-runtime minted `MotionObject`
counts.

**τ (§13) — DERIVED, two readings, both enumerated, neither chosen:**
- **exact τ = 0** — integer vector equality, NO NUMBER AT ALL (the strongest
  §13 outcome, mirroring `mo_tol_exact`);
- **τ = √5 ≈ 2.2361** — the motion-sensor-gate rung's (94000) MEASURED
  Otsu-within-aperture accuracy tolerance (the norm of the integer (1,2)); a
  boundary is a velocity jump exceeding what the sensor produces by accuracy
  error.
The verdict must hold at BOTH. **The manufacturing knob I name (§13): it is NOT
τ (τ falls out) — it is the sensor's APERTURE (`block`) and the depth SHIFTS
`s_i`, which are STIMULUS/SENSOR CONFIGURATION (declared, the same standing as
motion-energy's `DOT`/`FIELD_W`), NOT a verdict threshold.** The shifts are the
independent variable (the depth structure imposed); they are reported across a
gap sweep, never tuned to make the carve appear.

## 4. n, fixed in advance

**n = 80 fresh confirmatory seeds, 116000–116079**, unit of analysis the SEED,
95% bootstrap CI. Power: the pilot (burned seeds 116900–116939, n=40) gives
DEPTH largest_frac 0.360 [0.357, 0.363] vs FLAT 1.000 [1.000, 1.000] — zero
overlap, CI widths ≈ 0.006; the effect is enormous and n=80 is ample for a
comfortable bootstrap. No sweep beyond the listed arms.

## 5. The pre-registered discriminator (register all three BEFORE any number)

**Primary arm: GRID=144, block=8, N=3, shifts=[0,3,6], fixation = middle plane
(efference_v=(0,3)).** 324-cell field, 3 bands of 108 cells.

- **CONFIRM** = ALL of, co-holding, at BOTH τ:
  (a) DEPTH `eff_surfaces` ∈ [2.5, 3.5] (≈ N=3, few-but-plural);
  (b) DEPTH `largest_frac` < 0.5 (not one giant ground);
  (c) FLAT `eff_surfaces` ∈ [0.9, 1.2] (one blob) AND `largest_frac` > 0.9;
  (d) DEPTH-vs-FLAT **CI-separated** on BOTH eff_surfaces and largest_frac;
  (e) FLAT field discontinuity = 0 (the null EXPOSED — no boundary to segment
      on, so the one-blob result is not a vacuous null);
  (f) space constancy: reference-plane residual EXACTLY 0 (ground truth), and
      bounded by the sensor's confabulation on the sensed field.
- **FALSIFY** = the DEPTH scene shows no carve (eff_surfaces ≈ 1 OR largest_frac
  > 0.9 — parallax does not carve), OR the FLAT control ALSO carves
  (eff_surfaces > ~1.5 OR largest_frac < 0.9 — then the signal is NOT parallax
  but an artifact of adding motion).
- **AMBIGUOUS** = DEPTH-vs-FLAT not CI-separated, or the knee is a knife-edge
  (verdict flips between the two τ).

**Secondary arms (pre-registered, reported whatever they show):**
- **N=2, block 8, shifts=[0,4], fixation far (efference_v=(0,0)):** expect a
  clean 2-surface carve (eff ≈ 2, largest ≈ 0.55) vs FLAT one blob.
- **THE INHERITED-BOUND arm — block 4, N=3, shifts=[0,2,4]:** the aperture is
  too small to hold three resolvable depths. Prediction: **FALSIFY** — at τ=√5
  the bands MERGE (gaps 2 < √5 → one blob, largest → ~1), at τ=0 the confab
  fragments (eff inflated). The finding is the BOUND: **the number of resolvable
  depth planes ≤ aperture / tolerance ≈ block / √5** (block 4 → ~1.8 → 2 planes;
  block 8 → ~3.6 → 3 planes). This falls out of the sensor's measured aperture
  (= block, `vector_field`) and accuracy tolerance (√5, rung 94000).

**The graph build (`parallax_efference`), pre-registered checks:**
- default OFF ⇒ byte-identical to `vision_motion_group` (loaded+disarmed ==
  not loaded), §9;
- armed with the CHOSEN fixation `efference_v` ⇒ refuses the fixation plane
  (residual 0), NOT the estimated largest band — `D = |armed − baseline| > 0`
  on the minted object set (§13.2 load-bearing), positive-controlled both ways;
- FLAT armed ⇒ 0 minted objects (the whole world reads stationary).

## 6. My prediction, stated in advance (§3.7)

**~85% CONFIRM on the primary arm.** I predict: (a) DEPTH carves into eff≈3
surfaces, largest≈0.36, FLAT stays eff=1 largest=1.0, CI-separated at both τ;
(b) the block-4 N=3 arm FALSIFIES (aperture bound), and this is a finding not a
failure; (c) space constancy is EXACT 0 on ground truth; (d) the efference seed
is load-bearing (refuses a different plane than baseline) and default-OFF
byte-identical. **Provisos that would break informatively:** if the sensed
DEPTH field over-fragments even at block 8 (the confab tail overwhelming the
participation ratio), eff would exceed 3.5 — that would say the sensor bound is
tighter than the block/√5 estimate. If FLAT mints spurious surfaces at block 8,
the carve is not parallax. Two-sided: I could be wrong about the aperture
threshold (block 6 might already suffice, or block 8 might still fail).

## 7. Disclosures

- **Pilot (burned) seeds:** 116900–116939 (characterisation + prototype). These
  are NOT confirmatory and are recorded here as burned.
- **Scope / honest limits, declared in advance:** bands are FIXED image regions
  with per-region velocity (the small-baseline, ignore-boundary-motion
  idealization of a fronto-parallel plane) — occlusion/disocclusion at depth
  boundaries is NOT modelled; the finding is about the piecewise-constant flow
  field, not about occlusion cues. Synthetic Fourier textures, not found frames
  (the motion-sensor-gate rung's load-bearing assumption is inherited). One
  sensor (SAD `vector_field`), one aperture family. The efference-copy
  subtraction is TRANSLATION-INVARIANT for the PARTITION (subtracting a constant
  does not change which cells are equal), so it does not "cause" the carve — its
  load-bearing roles are space constancy (zero residual on the fixated plane)
  and choosing WHICH plane is the reference; this is stated, not smoothed over.

## 8. §3 clause 8 — the seed-claim check, VERBATIM (pre-run)

Pre-run (only the pilot seed 116900 is drawn; the confirmatory 116000–116079
are drawn only after this commit, by the confirmatory script):

```
SEED CLAIM 116000-116999: REFUSED.
  OCCUPIED: 1 seed integer(s) in this range are measurably drawn by 1 file(s).
    116900: scripts/parallax_char.py
  Scope: 820 files with seed sinks; 509 UNRESOLVED sink sites tree-wide (counted, not discarded).
  CAVEAT 1 -- THE UNIT IS THE SEED INTEGER, not consecutive draws from
    one generator. default_rng(S) burns an unbounded stream downstream of
    S; a rung seeding ONCE at its block base measures as ONE seed here.
  CAVEAT 2 -- THIS TOOL UNDER-REPORTS BY DESIGN (7 declared blind spots;
    unresolvable sinks are COUNTED, not discarded). A CLEAN RESULT MEANS
    'NO COLLISION DETECTED', NEVER 'NO COLLISION EXISTS'.
```

*(The verbatim POST-RUN `check_claim(116000,116999)` — including the confirmatory
seeds and the unresolved-sink count — is pasted in the results file §OUTCOME.)*
