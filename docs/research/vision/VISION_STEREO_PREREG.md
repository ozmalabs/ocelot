# STEREO — depth from N SIMULTANEOUS EYES — pre-registration

**Committed BEFORE the confirmatory run (PROTOCOL §3).** Extends the chain
gen-mint (`07515e87`) → time (`5aca5a2f`) → depth (`f3f3c30e`). The claim is a
UNIFICATION, not a new operator: **stereo is the depth operation on a SPATIAL
frame-pair instead of a TEMPORAL one.**

## The claim, bounded

`DepthInfer` mints `latent:depth` from the TEMPORAL residual of motion: a scene
with real depth translated past a MOVING eye over TICKS produces per-surface
translate generators that differ (near sweeps faster than far), and that residual
IS depth. **Stereo is the IDENTICAL operation on a different frame-source:**

> N eyes view one scene from displaced positions **at a single instant**. A
> surface at depth d projects to a different retinal column in each eye — the
> **disparity** — and disparity is the **inter-eye TRANSLATE**: near = large,
> far = small. With N eyes at equal baselines (positions 0,1,…,N−1), a surface's
> retinal column steps by a CONSTANT amount per eye (its disparity). So the map
> eye_i → eye_{i+1} is a constant-velocity translate exactly like the temporal
> transition, but SPATIAL; its VARIATION across surfaces IS depth. `DepthInfer`
> partitions by surface and finds distinct VELOCITIES (over ticks); stereo
> partitions by surface and finds distinct DISPARITIES (across eyes, one tick).
> **Same residual, same decision, different frame-source.**

**THE DEEP AIM — "eyes and ticks are the same resource," in code.** The strongest
outcome: `DepthInfer`, fed N-EYE frames at one instant, mints the SAME
`latent:depth` it mints from N-TICK frames of one eye, with the frame-source the
ONLY difference. **We first MEASURE whether `DepthInfer` generalizes directly (swap
the frame-set from "one eye over ticks" to "N eyes at one tick") or needs a
`StereoInfer` sibling.** The mechanism was read (§12.4): `eval_depth_infer` takes a
`sequence` of frames and requires each surface to be a rigid constant-velocity
translate ACROSS THE SEQUENCE — it has NO notion of time; the axis is whatever the
adapter puts in the sequence. **Prediction: it generalizes with only a frame-source
change (an Eye-hub adapter that assembles the sequence from eyes, not ticks); NO
new Rust, NO new seed rule.** If that prediction breaks, the finding is "stereo
needs a delta" and we keep it minimal (the `TimeInfer`→`DepthInfer` precedent).

**Scope, held to the frame/continuum invariant (`CLAUDE.md`).** INTEGER disparity
(discrete depth layers, each a different integer inter-eye translate) is
**in-frame/tractable** — built here. CONTINUOUS disparity (real depth, sub-integer
parallax, finer resolution by accumulating over a longer baseline) is
**cross-frame/deferred**, exactly as real-angle rotation is. Named, NOT built.

## BUILD FOR N — the cardinality principle IS the point

"2 is a local optimisation, but a fly does not have two eyes." A hardcoded count
is a magic number (§13). **The eye count falls out of the graph — `Count(Eye
hubs)` / hub traversal — never a literal `2`.** The adapter creates N `Eye` hub
nodes (each with an integer `baseline`), reads them BACK from the graph, and
assembles one frame per hub found; `frames.len()` IS the eye count. The SAME
frozen machinery runs at **N=2 AND N=3** (and N=4/5/8 for controls), the count
read from the graph every time. Cardinality-audited as the depth rung audited
`n_layers` (read back the count; the runner's decision path contains no literal
eye count).

## The mechanism (ALREADY BUILT — this rung adds nothing to Rust or seeds)

- Rust **`DepthInfer`** (`shape_decode.rs::eval_depth_infer`), UNCHANGED. It reads
  a `sequence` of frames; per surface it infers ONE constant-velocity translate
  (`infer_translate_offset`) and verifies it holds across EVERY consecutive pair;
  `≥2` distinct velocities → mint `latent:depth` ordered near→far by L1 speed;
  `≤1` → NO mint. Fed eye-frames, "velocity" is the per-eye-step disparity.
- Seed **`seeds/depth_axis.json`** (`depth_infer_mint` / `depth_infer_floor`),
  UNCHANGED, flag-gated on `depth_infer_enabled==1`, OFF by default (§9), matching
  `status=='depth_seq'` Observations. The stereo Observation IS a `depth_seq`
  whose `frames` came from eyes — that reuse is the unification.
- **The mint/floor DECISION is the Rust Term + the seed rule** — never a Python
  `if` over graph state; the eye count is `Count(Eye hubs)` / hub traversal, never
  a literal (the architecture rule IS the experiment). The Python runner does only
  mechanical world-building (project the scene onto each Eye hub — the optics) and
  mechanical read-back (the minted `LatentDimension`).

## The confirmatory arms, and what each failure means

All arms DETERMINISTIC except **H_shuffle**, whose random eye-order shuffles draw
from **declared seeds 28000–28399**. Runner: `scripts/stereo_measure.py`. Surfaces
share a coordinate span so no position-gradient can fake a disparity difference —
only appearance (a non-coord slot) distinguishes them. Disparity axis = `coord:c`.

- **H_single — THE DECISIVE ANTI-FORCED CONTROL. Run FIRST.** A scene at ONE
  depth (uniform disparity across eyes — incl. a multi-COLOUR scene all at one
  disparity, and a scene at infinity = ZERO disparity) → `depth_none`, **NO mint**,
  at N=2 AND N=3. *If a single-depth scene mints depth, the operation hallucinates
  from having multiple eyes/surfaces (§1.1 dead-arm / §13 magic dimension) —
  DISQUALIFYING.* Depth from disparity VARIATION, never from multiple eyes.
- **H_stereo — multi-depth mints, and COMPRESSES (MDL).** 2 layers (disparities
  2,1, same coord span) at N eyes → `latent:depth{n_layers:2}`, ordering near→far
  (larger disparity = nearer), MDL(with depth) < MDL(enumerate per-eye positions).
  *Fail ⇒ the operation does not generalize to the spatial frame-source; report
  "needs a StereoInfer delta."*
- **H_multiheld (§13.1) — DIFFERENT structures → DIFFERENT correct orderings.**
  2-layer / 3-layer / a REVERSED ordering / a dedup (3 surfaces, 2 disparities) →
  each the correct distinct verdict from ONE frozen Term; ≥3 distinct orderings.
  *Same-ordering-regardless = forced.*
- **H_shuffle (mismatched eyes) — floor at the LONGEST config.** Eye-ORDER
  shuffles (the spatial analog of the depth rung's tick-order shuffle: scramble
  which eye's view sits at which sequence position, so per-surface disparity is no
  longer constant) at the LONGEST eye-count (N=8), n=400, seeds 28000–28399 → **0**
  spurious mints (original/reversal counted separately as legitimate orbits). *A
  forced minter eventually hallucinates a layering at the longest configuration.*
- **H_downstream (§1.5/§13.2) — the minted depth predicts an UNSEEN EYE.** Build N
  eyes; hold out the LAST; feed eyes 0…N−2; `DepthInfer.predicted` (each surface
  advanced by its OWN disparity to eye-index N−1) must EQUAL the held-out eye's
  actual view. ON mints+predicts, OFF inert (D_mint>0, D_pred>0 — load-bearing, not
  decoration). *A depth map that can't predict a held-out eye is FM-0 decoration.*
- **H_cardinality (THE POINT) — N=2 AND N=3, count from the graph, N=3 MORE
  PRECISE.** SAME frozen machinery at N=2 and N=3, eye count read from `Count(Eye
  hubs)`. Precision: on an INCONSISTENT-disparity scene (a surface whose per-eye
  disparity is −1 then −2 — not a rigid single depth), **N=2 has ZERO verification
  pairs and MINTS the unreliable layering; N=3's extra baseline is a verification
  pair that REJECTS it (floors).** N=3 grounds the same depth tighter (fewer false
  layers). On a CLEAN scene N=2 and N=3 agree (both correct). *A hardcoded 2, or
  machinery that only works for two eyes, fails this rung even if every number is
  green.*
- **H_additive — the stereo payoff, measured.** (1) **SAME dimension:** feed the
  SAME depth structure once as N-eye-at-one-tick and once as one-eye-over-K-ticks
  (same depth→speed map); the `latent:depth` ordering AGREES. (2) **QUICKER:**
  stereo grounds depth at a SINGLE tick (N simultaneous eyes, no temporal orbit);
  motion needs K≥2 ticks — report the tick-count each needs. (3) **MORE PRECISE:**
  N=3 resolves (rejects) an ambiguous layering N=2 accepts (H_cardinality).
- **H_offday (§9) — flag OFF is inert.** Multi-depth eye-frames with the flag OFF →
  no mint.

## Statistics, n fixed in advance (§3)

- Deterministic arms (H_single, H_stereo, H_multiheld, H_downstream, H_cardinality,
  H_additive, H_offday): exact-equality verdicts, no sampling — pass iff the exact
  predicted structure is read back.
- **H_shuffle: n=400**, fixed in advance, mirroring the depth rung's powered floor
  (the depth/time floors were 0/400 at their longest window; a pilot on **burned**
  seeds (the depth rung's own 27xxx-range shuffles, re-run here on eye-order) gave
  0 spurious, so 400 is the same powered floor). Decision rule: **any** spurious
  mint (a non-original, non-reversal eye-order shuffle that mints) FAILS the arm.
- Unit of analysis = the SEED (§4). Seeds 28000–28399 for H_shuffle; 28400–28999
  reserved. **12000–27999 untouched.**

## Prediction, stated in advance, with provisos (§3.7)

**Prediction:** `DepthInfer` generalizes directly across frame-source — N-eye
frames mint the SAME `latent:depth` as N-tick frames, with NO new Rust and NO new
seed rule (frame-source is the only difference). Single-depth → nothing. N=2 and
N=3 both mint from the graph-read count; N=3 strictly more precise (rejects the
inconsistent layering N=2 accepts). Additive arm holds: same dimension, stereo at
1 tick vs motion's K, N=3>N=2.

**Provisos (a proviso that breaks tells me what I did not understand):**
1. The precision gain is a VERIFICATION-REJECTION (N=3 refuses a false layering),
   not a positive split of a clean scene — because in the integer-linear class
   equal baselines make disparity constant, so N=2 already resolves any clean
   depth. If instead N=3 splits a scene N=2 clean-mints wrong, my model of the
   class is incomplete. Finer/continuous-disparity precision (sub-integer
   resolution by accumulating over a longer baseline) is CROSS-FRAME/deferred.
2. The Eye-hub count must survive the audit: if any decision reads a literal eye
   count, the cardinality rung FAILS even with green numbers.
3. If the eye-order shuffle floor is NOT 0/400 at N=8, either the surfaces are not
   coord-span-matched (a position gradient fakes disparity) or the operation is a
   forced minter — either way a precise finding, reported not rescued.
4. If `DepthInfer` does NOT mint on eye-frames, stereo needs a `StereoInfer` delta;
   I keep it minimal and report the exact residual the Term could not express.

## §9 regression oracle (byte-identical; this rung adds nothing off by default)

Because the rung adds NO Rust and NO seed, `data/`-present bench must stay
**200/0**; sd orbit law `{2:1,3:2,4:2,6:2,12:4}` unmoved; depth 8/8, time 6/6,
gen_infer/genmint 6/6, dim-inference 8/8, provenance 7/7; fm0 VACUOUS D=0.0;
fm0b 8.071079e-01. Engine hash recorded on every result (§10).
