# VISION — THE RENDER MADE PRIMARY: the illusion battery (pre-registration)

*Written and COMMITTED before the confirmatory run (PROTOCOL §3). Seeds
**32000–32999** (declared below). 12000–31999 untouched.*

## 0. The claim, and why illusions are the sharp test

The downstream-prediction rungs proved the eye can RENDER `M^k(base)` from a held
generator (time→unseen frame, depth→unseen view, stereo→unseen eye), and the
blind-spot / blink rungs proved the render STANDS where input is ABSENT. This rung
asks whether those are two faces of **ONE bidirectional predictive loop**: the
field is populated TOP-DOWN from the prior FIRST; the sampled input is used only to
compute the RESIDUAL; the percept is the reconciliation, weighted by input strength.

**The falsifiable test is the illusion battery** (the creator: *"it should be easy
to test, because that is what illusions ARE"*). An illusion is BY DEFINITION a case
where the percept ≠ the stimulus — i.e. where the top-down render WINS over the
bottom-up input. So *"does the eye see the illusion?"* is literally *"does the eye
render top-down?"* A real render REPRODUCES the illusion (the prior wins where the
input is weak/absent); a pure bottom-up sampler does NOT (it reports only the
physical stimulus). **And the anti-overfit crux is the ORDERING:** the render must
ALSO be VERIDICAL where the input is strong and unambiguous — a render that sees
EVERY illusion maximally is a universal confabulator (DISQUALIFYING); one that sees
NONE is bottom-up. The falsifiable signature is *illusion where the prior should
win, veridical where the input should win.*

**No new Rust, no new seed rules.** The two render engines already exist and are
reused unchanged (the stereo-rung pattern):
- **spatial** — `seeds/vision_ground.json` (the grounded-field contour fill; render
  = LOCAL `Neighbours`/`Filter`/`Count`/`Sum` fold; residual = `gbel` vs `raw_sensor`).
- **temporal** — the `BlinkBridge` Term (render = `apply_generator_k` from the
  inferred transition generator; residual = `frames_symdiff` = `correction`).
Both ship OFF by default (`ground=0`, `blink_bridge_enabled=0`), so §9 holds by
construction. The rung's contribution is the UNIFICATION and the ILLUSION BATTERY,
not code.

## 1. Statistics — exact, per arm

Every arm is DETERMINISTIC except the two floor controls (n fixed in advance,
matching the blind-spot/blink precedent). `gbel` = the grounded belief field (the
spatial percept); `bridged` = the render-filled gap frames (the temporal percept);
`raw_sensor`/`raw gap frames` = the bottom-up baseline.

### Battery A — SPATIAL (amodal / illusory-contour completion, via `vision_ground`)

- **H_amodal (illusion):** a contour bar passing behind an OCCLUDER (a no-data hole,
  the blind-spot geometry re-used as an occluder) is completed as ONE contour:
  `mean|gbel−1|` over the occluded span ≤ 0.05 (a STEP), while the bottom-up baseline
  (`raw_sensor`) is NaN across the occluded span (two FRAGMENTS). PASS iff the render
  bridges AND the raw sensor does not.
- **H_boundary_liberal (the risked characterisation, stated in advance):** a
  ONE-SIDED inducer — the bar present only on the LEFT of the occluder, blank on the
  right — is STILL completed across the hole (`gbel≈1` across the occluded span). This
  is confabulate-by-default at the boundary (any contour touching the hole is
  continued across it), the spatial twin of the blink's fill-by-default. Reported as
  a characterisation, not a pass/fail gate: the fill is LIBERAL, and the
  falsifiability lives in H_veridical / H_floor / H_ambiguity, NOT in alignment-gating.
- **H_veridical_spatial (the anti-overfit — input wins where strong):** the SAME bar
  with a VISIBLE break (a real 0-gap in the SENSED region, away from the occluder) is
  NOT completed — `gbel` shows the break (0 at the broken cells). PASS iff the visible
  break survives in the percept (input dominates present, unambiguous data).
- **H_render_is_prediction (changes with the prior):** rotating the inducer
  (horizontal bar → VERTICAL bar) rotates the completed contour — the vertical bar is
  completed down the occluded column while the occluded ROW (no horizontal inducer)
  stays 0. PASS iff completion follows the inducer orientation.
- **H_ambiguity_ordering (don't confabulate against ambiguous evidence, reuse of the
  blind-spot H4):** an AMBIGUOUS crossing (H bar × V bar) is HELD OPEN at the hole
  centre (exactly 1 ambiguous cell, both contours still continue) where an
  interpolation control confabulates a single mean. PASS iff held open AND interp is not.
- **H_floor_spatial (universal-confabulator floor):** **100** random uniform surrounds
  with NO contour (**seeds 32000–32099**) invent ZERO illusory contours and ZERO
  ambiguity in the hole. PASS iff 0/100.

### Battery B — TEMPORAL (apparent motion, via `BlinkBridge`)

- **H_apparent_motion (illusion):** a prefix of ≥2 flashes establishing constant
  motion, then a temporal GAP (a blink), renders the object at the UNSHOWN
  intermediate positions (`bridged` == the true continuation `M^t(f0)` per gap tick,
  `constrained=1`), where the bottom-up baseline (the raw gap frames) is EMPTY (the
  object vanished). PASS iff the render fills the true motion AND the raw gap is empty.
- **H_veridical_temporal (input wins where it diverges strongly):** a CONTRADICTING
  resume (the object stopped/jumped during the gap) produces a LARGE `correction`
  (`diverged_at` ≥ resume, `correction > 0` growing with the gap), i.e. the render is
  NOT a universal confabulator — the surprise is not explained away; and continuous
  VISIBLE motion (gap=0) yields NO confabulated frames (`bridged` empty). PASS iff a
  contradiction corrects AND a fully-visible motion adds nothing.
- **H_render_is_prediction_temporal:** changing the velocity changes the predicted
  intermediate positions (`bridged` tracks `M`). PASS iff the fill follows the velocity.
- **H_floor_temporal (false-motion floor):** **400** shuffled prefixes (**seeds
  32100–32499**) each still confabulate a guess (fill-by-default) but **0** non-orbit
  shuffles are falsely marked `constrained` (an out-of-order prefix that happens to be
  monotonic is a genuine orbit under G/G⁻¹ and may be constrained — counted
  separately). PASS iff 0/400 falsely constrained.

### Cross-cutting

- **H_reconciliation_uses_both:** the percept is NEITHER the raw input NOR the pure
  render. It ≠ raw input (the render ADDS the completed contour / the moving object in
  the hole/gap, spatial AND temporal) AND ≠ pure render (the veridical arms follow the
  input: the visible break and the contradicting resume). PASS iff BOTH hold.
- **H_compute_proportional_to_surprise:** the fill is RESIDUAL/HOLE-directed and
  LOCAL. Fitted log-log exponent of fill cost vs field size ≤ 1.3 in BOTH modalities
  (NOT the O(N²)=exponent≈2 global-match drive). PASS iff both exponents ≤ 1.3.
- **H_offday (§9):** both seeds OFF by default are inert (`ground=0` → hole never
  filled; `blink_bridge_enabled=0` → no bridge), and committed results are
  byte-identical: bench 200/0 with `data/`; sd orbit law `{2:1,3:2,4:2,6:2,12:4}`
  unmoved; blink 9/9, vision-ground 11/11, time 6/6, depth 8/8, stereo 9/9,
  gen_infer/provenance 7/7, sdloop 15/15. PASS iff OFF inert AND nothing moves.

## 2. n, fixed in advance

Deterministic arms need no n. The two floor controls: **n=100** spatial (matching the
blind-spot blank floor's 100) and **n=400** temporal (matching the blink false-motion
floor's 400). No power analysis is required for a floor whose null is an EXACT 0 count
(any single false mint fails it); the n's are the sibling rungs' own, so the floors are
directly comparable. No sweeps, no re-runs (§3.6).

## 3. Burned-seed ledger for this rung

- **32000–32099** — spatial blank floor (H_floor_spatial), 100 seeds.
- **32100–32499** — temporal false-motion floor (H_floor_temporal), 400 seeds.
- **32500–32999** — CLEAN, reserved for any follow-up with its own prereg.

Confirmatory floor seeds are consumed ONCE here and never reused. The deterministic
arms were piloted only on hand-constructed stimuli and ALREADY-burned constructions
(no 32xxx seed touched) to inform the predictions below (§3.3 / §3.7).

## 4. Decision rule — what each answer means (§7: either answer is a result)

- **Both illusion arms reproduce AND both veridical arms are veridical AND both floors
  are 0 AND the reconciliation uses both AND compute is LOCAL** ⇒ the eye is ONE
  bidirectional predictive loop — the field is rendered top-down from the prior,
  corrected by a residual, illusion where the prior wins and veridical where the input
  wins, compute ∝ surprise. Bounded to the discrete/integer, in-frame,
  luminance/contour/rigid-motion class.
- **An illusion arm does NOT reproduce** (render can't populate the missing
  structure) ⇒ the render is not primary / can only be built bottom-up in that
  modality — a clean negative, reported, NOT rescued.
- **A veridical arm sees the illusion anyway** (the render overrides strong,
  unambiguous, present input) ⇒ the render is a UNIVERSAL CONFABULATOR — overfitting,
  DISQUALIFYING; reported as such, not tuned away.
- **A floor mints structure from noise** ⇒ the fill invents; overfitting; reported.

## 5. Prediction, stated in advance, with provisos (§3.7)

I predict **all illusion arms reproduce, all veridical arms are veridical, both floors
are 0, the reconciliation uses both, and compute is LOCAL** — because the render
engines are already proven and an illusion is the same fill run on a natural stimulus
that leaves the input locally absent/weak.

Provisos that could break (and what each would teach):
1. **H_boundary_liberal** — I predict the one-sided inducer IS completed (the fill is
   boundary-liberal, confabulate-by-default). If instead it refuses, the fill is
   alignment-gated and the confabulate-by-default reading is wrong for the spatial
   render. *(Piloted: it completes — stated here as the risked characterisation.)*
2. **Compute exponent** — I predict ≤ 1.3 (LOCAL). If the temporal bridge scales
   super-linearly under longer motion footprints, the "make it up is cheap" claim is
   bounded to short footprints.
3. **H_veridical_temporal** — I predict a contradiction corrects with a growing
   `correction`. If a long gap saturated `correction` at the field size, the residual
   is not resolving the surprise and the veridical claim is weaker than stated.

## 6. Scope — what is NOT shown (§8), the named frontier

- **BOUNDED to the discrete/integer, in-frame, luminance-contour / rigid-integer-motion
  class.** Binary/step stimuli, exact-equality contour labels, integer-velocity motion.
- **Full Kanizsa (the orthogonal illusory contour induced by pac-man TERMINATORS,
  spanning where there is no collinear inducer) is OUT OF SCOPE — the frontier, named,
  NOT attempted.** The tractable core demonstrated here is COLLINEAR completion across a
  no-data span (amodal/modal completion); the orthogonal-terminator variant needs a
  terminator/alignment prior the eye does not hold.
- **hollow-face, Ebbinghaus/Ponzo, checker-shadow / simultaneous-contrast** are OUT OF
  SCOPE — they need LEARNED object/context/reflectance priors (a face/convexity prior; a
  context-conditioned size prior; a surface-reflectance/shadow-inference constancy on a
  colour/"what" layer) not built here. That they are out of reach is itself an honest
  bound and maps exactly onto the in-class caveat: the render reproduces an illusion
  only where it HOLDS the prior.
- No claim about which biological mechanism is correct; no map topography; the temporal
  bridge is the interpolated-motion phenomenon at the mechanism level (a single
  contiguous gap), not the full multi-flash phi/beta timing literature.

## 7. Engine / bench (filled at OUTCOME)

Engine hash + resolution path, bench condition, and the §9 byte-identity table are
recorded in `VISION_ILLUSION_RESULTS.md` at the confirmatory run. This rung adds NO
Rust; the shared canonical build is legitimate iff the Rust source is byte-identical
(§10.1 rule 4) — verified by `provenance_line()`.
