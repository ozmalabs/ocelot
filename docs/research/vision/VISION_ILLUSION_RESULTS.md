# VISION — THE RENDER MADE PRIMARY: the illusion battery (RESULTS)

*Confirmatory run of `VISION_ILLUSION_PREREG.md` (committed BEFORE the run at
`a2ad3065`, §3). Runner `scripts/illusion_measure.py`; gate
`tests/test_illusion_render_migrated.py`; raw `results/illusion_measure.json`.*

## Engine / bench / provenance (§10)

- **Engine `7d5f50c18673`** @ `runners/dsl/python/substrate_rs/_native.abi3.so`
  — **shared build, Rust source byte-identical** to canonical (`provenance_line()`
  reads `shared`; this rung adds NO Rust, so the shared build is legitimate,
  §10.1 rule 4). `data/` symlinked to canonical (§10.2).
- **Bench 200 passed / 0 failed with `data/`** (`scripts/rung7_vision_bench.sh`,
  130.7s); the no-Python-thresholds scan is clean ("every knob is graph data").
- Sibling gates green: blink 9 · vision-ground 11 · time 6 · depth 8 · stereo 9 ·
  dim 8 · provenance 7 (66 passed together) · sdloop 8/8 (sd orbit law
  `{2:1,3:2,4:2,6:2,12:4}` unmoved). New gate `test_illusion_render_migrated.py`
  **8/8**.
- **NO new Rust, NO new seed rules.** The two render engines are reused unchanged;
  both ship OFF by default (`ground=0`, `blink_bridge_enabled=0`), so §9
  byte-identity holds by construction and is verified above.

## Verdict — 12 of 13 gated arms PASS; one pre-registered partial null, diagnosed

| arm | result |
|---|---|
| **A_amodal** (spatial illusion) | **PASS** — contour completed behind occluder (`mean|gbel−1|=0.0000`), raw sensor NaN (fragments) |
| A_boundary_liberal (characterisation) | one-sided inducer **completes** — the fill is boundary-liberal (as predicted) |
| **A_veridical_visible_break** | **PASS** — visible break survives (`gbel`=[1,1,**0,0**,1,1]); input wins where strong |
| **A_render_is_prediction** | **PASS** — vertical inducer → vertical completion; occluded row (no H inducer) stays 0 |
| **A_ambiguity_ordering** | **PASS** — ambiguous crossing held open (1 ambig cell, both contours continue); interp confabulates |
| **A_floor_spatial** | **PASS** — **0/100** blank surrounds (seeds 32000–32099) invented a contour |
| **B_apparent_motion** (temporal illusion) | **PASS** — gap filled with true motion (`bridged`=dot@cols 2,3,4, `constrained=1`); raw gap empty; render OFF → no bridge |
| **B_veridical_temporal** | **FAIL as written** (growth sub-clause) — see below |
| **B_render_is_prediction** | **PASS** — bridged tracks velocity (v01≠v02, matches truth) |
| **B_floor_temporal** | **PASS** — **0/400** shuffles (seeds 32100–32499) falsely constrained; all still fill |
| **X_reconciliation_uses_both** | **PASS** — percept ≠ raw input (render adds structure in holes) AND ≠ pure render (veridical arms follow input) |
| **X_compute_spatial** | **PASS** — fitted exponent **1.017** (LOCAL / O(N), not the O(N²) drive) |
| **X_compute_temporal** | **PASS** — fitted exponent **0.691** (LOCAL / sub-linear) |
| **X_offday** (§9) | **PASS** — both seeds OFF inert |

## The falsifiability pair (the headline)

**Illusion where the prior should win; veridical where the input should win — the
render REPRODUCES documented illusions AND is NOT a universal confabulator:**

- **Illusory contour / amodal completion (spatial):** a bar behind an occluder is
  seen as ONE continuous contour (`mean|gbel−1|=0.0000`, a STEP) where the raw
  sensor has only two fragments (NaN across the occluded span). The percept ≠ the
  stimulus — that IS the illusion, and it is the render winning where the input is
  absent.
- **Apparent motion (temporal):** two flashes + a gap → the render populates the
  moving object at the unshown intermediate positions (cols 2, 3, 4), == the true
  continuation `M^t(f0)`, where the raw gap frames are empty (the object vanished).
  The percept ≠ the stimulus — the render seeing motion the input does not carry.
- **Anti-overfit (the crux):** the render does NOT see illusions everywhere. A
  **visible** break survives in the percept (input wins where strong); the render
  tracks the inducer (a real prediction: a vertical bar completes vertically and
  invents NO horizontal contour); an ambiguous crossing is held open, not
  confabulated to one mean; **0/100** blank surrounds and **0/400** scrambled
  motions invent structure. A render that "explained" any input would fail all of
  these — none fail.

**"You see what you expect" — the input-absent limit reconfirmed under the general
render:** the blind-spot fill (spatial hole) and the blink fill (temporal hole)
are the SAME render engines here, driven on natural stimuli that leave the input
locally absent. The illusion battery is those two fills generalised: the render
always populates; the residual corrects; where the input is absent the render
stands unopposed (blind spot / occluder / between-flash gap), where it is present
and strong the input corrects (visible break / diverging resume).

**Compute ∝ surprise, LOCAL:** spatial fit **1.017**, temporal fit **0.691** — both
O(N) or better, NOT the O(N²) global-match drive. The fill is residual/hole-directed
(the occluder diameter and the gap are fixed; work does not grow with the field²),
which is the "make it up" payoff: the field is populated top-down cheaply and only
the residual is processed.

**The render is a real prediction (changes with the prior):** rotating the spatial
inducer rotates the completed contour; changing the temporal velocity changes the
predicted intermediate positions. A render that ignored the prior would not do this.

**The reconciliation uses BOTH:** the percept is neither the raw input (it adds the
completed contour / the moving object where the input is absent) nor the pure render
(the visible break and the diverging resume follow the input).

## What I got WRONG — the pre-registered partial null (§7)

**B_veridical_temporal FAILS as written, on one conjunct: `correction_grows=False`.**
The correction is a CONSTANT `2` at every gap ∈ {1,2,3,5} (`diverged_at` = 5,6,7,9;
confidence 0.75→0.60→0.50→0.375 decays correctly). **Diagnosis:** I used a
single-cell dot, so the symmetric-difference between the predicted-moving position
and the stopped position is gap-INDEPENDENT (= 2: one cell appears, one disappears)
— and `2` is the MAXIMAL possible residual for a one-cell object (the render is 100%
wrong). The "grows with the gap" clause I imported from the blink rung's
`H_correction` is a PERCEPTUAL-STARTLE phenomenology that only manifests for a
MULTI-cell footprint (the blink rung used a 4-cell L and measured 6→8→8→8); it is
degenerate for a point.

**The anti-overfit CORE of the arm HOLDS decisively and is what the headline needs:**
`all_diverge=True` (the surprise is detected at EVERY gap), `correction>0` (maximal,
for a point), and `no_confab_when_fully_visible=True` (a gap-0 motion adds no
confabulated frames). So *"a surprising input produces a large residual that is not
explained away"* — the falsifiability claim — is confirmed; only the phenomenological
growth detail is a null, because a point object cannot exhibit it.

**Per §5 (never rescue a failed gate by changing the measure) and §3.6 (no re-runs),
I did NOT swap in a footprint and re-run to flip it green.** The arm is reported as
pre-registered = FAIL, diagnosed. (Had I used a footprint from the start — as the
blink rung did — this arm would have read like `H_correction`; that this was left as
a point is the design error, honestly recorded.)

## The risked characterisation that held (§3.7 proviso 1)

**A_boundary_liberal:** the one-sided inducer (bar only on the left of the occluder)
IS completed across the whole occluded span. The spatial fill is **boundary-liberal**
— any contour touching the hole boundary is continued across it, WITHOUT requiring
exit evidence on the far side. This is the spatial twin of the blink's
confabulate-by-default, and it means the render is NOT alignment-gated; its
falsifiability lives entirely in the present-input and no-structure controls (which
all pass), never in refusing to bridge. Stated in advance in the prereg; confirmed.

## Scope — what is NOT shown (§8), and the named frontier

- **BOUNDED to the discrete/integer, in-frame, luminance-contour /
  rigid-integer-motion class** (binary/step stimuli, exact-equality contour labels,
  integer-velocity motion). The spatial and temporal fills are the two proven engines;
  nothing continuous is claimed (the frame/continuum invariant: the continuous sits
  in the cross-frame map, not in a frame).
- **Full Kanizsa (orthogonal illusory contour from pac-man TERMINATORS) is the
  frontier — NOT attempted.** The tractable core here is COLLINEAR completion across a
  no-data span (amodal/modal); the orthogonal-terminator variant needs a
  terminator/alignment prior the eye does not hold.
- **hollow-face, Ebbinghaus/Ponzo, checker-shadow/simultaneous-contrast — OUT OF
  SCOPE.** They need LEARNED object/context/reflectance priors (a face/convexity prior;
  a context-conditioned size prior; a surface-reflectance/shadow constancy on a
  colour/"what" layer). That they are unreachable is itself the honest bound: the
  render reproduces an illusion ONLY where it HOLDS the prior — which is precisely the
  bidirectional-loop claim, stated as a limit.
- The temporal bridge is the interpolated-motion phenomenon at the mechanism level (a
  single contiguous gap), not the full phi/beta timing literature.

## Is the eye now a BIDIRECTIONAL predictive loop? — the plain answer

**Yes, bounded.** The field is rendered TOP-DOWN from the prior (a spatial contour
render via `vision_ground`; a temporal generator render via `BlinkBridge`), it is
corrected by a SPARSE, LOCAL residual (O(N), exponents 1.017 / 0.691), and the
reconciliation weights render vs input by input strength — reproducing documented
illusions where the input is weak/absent AND remaining veridical where the input is
strong, without inventing structure from noise (0/100, 0/400). The render is a real
prediction (it changes with the prior) that CAN be wrong (a surprising input is not
explained away). **Bounded to** the discrete/integer, in-frame,
luminance-contour/rigid-integer-motion class; illusions needing learned
object/context/reflectance priors are the named, unreached frontier. The one
pre-registered sub-clause that broke (temporal correction growth for a point object)
is diagnosed and was not rescued.
