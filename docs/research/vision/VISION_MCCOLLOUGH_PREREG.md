# VISION — the McCOLLOUGH CONTINGENT AFTEREFFECT (PRE-REGISTRATION)

*Frontier rung T6 of the from-scratch EYE. THE decisive predictive-coding gate
(VISION_VENTRAL_GROUNDING.md, FAILURE-MODE GATES §2, "highest discriminative
value"). Written and COMMITTED before the confirmatory run (PROTOCOL §3).*

Seeds allocated: **41000–41999** (confirmatory noise floor uses **41000–41099**;
41100–41999 reserved). Flag **OFF by default** (§9). Engine recorded in OUTCOME (§10).

---

## §0. AUDIT — what exists to compose (PROTOCOL §12.4, file:line)

The McCollough mechanism the grounding names — *"the negative residual of an
over-fit contingency prior … render-from-prior + opponent-residual"* — decomposes
into four ingredients, and **all four already exist or compose from existing DSL,
so this rung adds NO new Rust:**

1. **Cone-opponent colour** — `seeds/vision_colour.json` `cc_contrast`
   (VISION_COLOUR_RESULTS.md) computes the opponent coordinates **rg = L−M** and
   **by = S−(L+M)** inline from raw cone attrs `cL,cM,cS` (builder
   `tools/build_vision_colour.py:RG/BY`). Reused verbatim as the colour
   representation. The opponent SUBTRACTION is what turns a missing red into a
   perceived green (negative rg = green) — the "opponent" in opponent-residual is
   intrinsic to this coordinate.
2. **The render/residual (predict-then-transmit) shape** —
   `seeds/vision_lateral.json` `lat_residual` (lines 388–583) is literally *"predict
   the centre from the surround; transmit the residual"* (centre − prediction). The
   McCollough percept is the **same shape** with the predictor swapped: predict the
   colour from the **orientation prior**, transmit the residual (observed − prior).
3. **A learnable JOINT (colour⊗orientation) prior** — **did NOT exist**; this rung
   builds it, as pure graph data. It is the running **MEAN colour given
   orientation**, `E[colour|orientation] = Div(sum, Max(n,1))`, accumulated by a
   seed rule (`mcc_learn`) using the EMA/accumulate idiom of `vision_theta.json`
   `th_track_rbar` (the `rbar_step<step` per-frame guard, here `astep<frame`). A
   running mean has **NO learning rate and NO magic number** (§13); the aftereffect
   SIGN is fixed by the sign of the adapting colour, invariant to scale.
4. **The join** — each stimulus region is wired by the adapter to its orientation's
   prior via a single `tunes` edge (`K -tunes-> R`; grid-geometry scaffolding, like
   `colour_world`'s `neighbour` wiring), matched with the incoming-edge join of
   `vision_onoff.json` `oo_bipolar_burst` (`[["scene","has_region","R"],
   ["K","tunes","R"]]`). Each R has exactly ONE incoming `tunes` — avoiding the
   two-incoming-edges matcher gotcha (CLAUDE.md). Orientation itself is supplied as
   a stimulus feature `theta` (as cone values are supplied); grown orientation maps
   are the **diagnosed Hebbian dead-end** (`vision_theta.json` / MEMORY) and are
   out of scope for a validation gate (§8).

**The contingent adaptation IS a seed rule on the residual, with no new Rust
(audit verdict: YES).** Three rules, all composition of existing Terms
(`Attr/Minus/Plus/Times/Div/Max/Gt/Lt/And/NodesWhere/PickUnique/set_attr`):
`mcc_learn` (adapt the colour⊗orientation association), `mcc_percept_pred`
(render-from-prior + opponent-residual), `mcc_percept_ff` (the feedforward control).

---

## §1. Hypothesis (two-sided)

**H_contingency (headline).** After adapting a PREDICTIVE/opponent code to
red-vertical + green-horizontal pairings, an ACHROMATIC test grating yields a
colour percept OPPOSITE the adapted colour, CONTINGENT on orientation: vertical →
green-biased (percept_rg < 0), horizontal → pink-biased (percept_rg > 0). The
aftereffect lives in the colour⊗orientation JOINT — swapping the test orientation
FLIPS the aftereffect colour. Two-sided: the effect could be absent (no
render-from-prior in this substrate) or non-contingent.

**H_crux (THE decisive test, §1.1).** A FEEDFORWARD control — direct read of the
input colour, NO render-from-prior, NO opponent-residual — produces **NO** contingent
aftereffect (achromatic in ⇒ achromatic out), for EITHER orientation. The predictive
and feedforward arms are the SAME seed, the SAME inputs, the SAME prior available
(both match K); they differ ONLY in whether the render-from-prior is subtracted.
**If the feedforward control ALSO produces the aftereffect, the test does not
discriminate and the result is a NEGATIVE** (report + diagnose, do not force, §7).

**H_persist (error-driven, not fatigue).** The aftereffect is a STORED, learned
prior: (a) ERROR-DRIVEN — the prior magnitude is the learned mean of the adapting
statistics, and grows with adaptation exposure; (b) PERSISTENT — it survives
arbitrary intervening ticks with no adapting input (unlike momentary fatigue, which
recovers). Measured: the prior and the aftereffect are bit-identical before and
after an intervening no-adaptation tick block.

**H_floor.** (a) NO adaptation ⇒ no aftereffect (prior n=0 ⇒ prior=0 ⇒ percept =
observed = 0). (b) Colour ALONE, no orientation pairing (SAME colour adapted on
BOTH orientations) ⇒ an aftereffect exists but is NOT orientation-contingent
(percept(vert) == percept(horiz); the contingency C = 0).

**H_noise (anti-overfit).** iid colour-noise adaptation (zero-mean random colour,
no consistent colour⊗orientation pairing) produces no coherent contingency: over
100 confirmatory seeds, 0/100 reach a contingency as strong as the structured
pairing, and the sign is not consistently reproduced.

**H_offday (§9).** With `mcc_enabled=0` (default) the seed is inert: every percept
is 0, no prior accumulates, and all sibling/bench results reproduce byte-identically.

---

## §2. The statistics, exactly

For a region, the percept is the opponent-space vector `(percept_rg, percept_by)`
written by the firing percept rule. The colour axis carrying the manipulation is
**rg** (red>0 / green<0); the adapting colours are equiluminant on **by**, so
`percept_by` is predicted 0 (reported, not a headline).

- **Aftereffect** on a test region = `percept_rg`.
- **Contingency** `C = percept_rg(vertical test) − percept_rg(horizontal test)`,
  BOTH tests achromatic. Structured adaptation predicts `C ≪ 0` (green minus pink).
- **Swap flip** = the SAME achromatic patch read under theta=vertical vs
  theta=horizontal; predicted `percept_rg` of opposite sign.
- **Crux discrimination** `D_crux = |percept_rg_pred − percept_rg_ff|` on the
  achromatic test; and `percept_rg_ff` itself (predicted exactly 0).
- **FF-alive** = `percept_rg_ff` on a genuinely coloured (red) test (predicted = the
  real opponent value +10; proves the control arm is ALIVE, §1.1).
- **Persistence** = `(prior, percept)` before vs after an intervening no-adapt tick
  block (predicted bit-identical).
- **Noise floor** = fraction of 100 seeds with `|C_noise| ≥ |C_structured|`, and the
  distribution of `C_noise`.

Stimuli (integer cone values, in-frame): NEUTRAL `(10,10,10)` rg=0; RED `(15,5,10)`
rg=+10; GREEN `(5,15,10)` rg=−10. Orientation labels theta ∈ {vertical=90,
horizontal=0} (arbitrary distinct labels; the result depends only on distinctness).
Adaptation = 8 frames (a fixed exposure; the SIGN-based claims are frame-count- and
scale-invariant — no arm's truth depends on this number, §13).

## §3. n, fixed in advance

Every headline/crux/floor/persistence arm is **DETERMINISTIC** (fixed stimuli, no
RNG) — n=1 exact, and the claim is an exact equality/inequality on the percept, not
a sampled mean. The only stochastic arm is **H_noise: n=100** iid colour-noise
adaptation sequences, seeds **41000–41099** (never used before; burned-seed ledger).
No power analysis is needed for a deterministic exact-value gate; the noise n=100
mirrors the colour-salience N_noise=100 precedent.

## §4. Confirmatory seeds

**41000–41099** — the 100 noise-floor adaptation sequences (H_noise). No other arm
consumes a seed. 41100–41999 reserved for any pre-registered follow-up (a NEW
mechanism-level hypothesis, never a parameter search, §3.6).

## §5. Decision rule (what a null means)

- **H_contingency PASS** iff `percept_rg(vert) < 0` AND `percept_rg(horiz) > 0` AND
  swap flips the sign. NULL (no/weak/non-contingent effect) ⇒ the substrate's
  render-from-prior does not produce McCollough — a clean NEGATIVE, reported (§7).
- **H_crux PASS** iff `percept_rg_ff == 0` for BOTH orientations (no aftereffect)
  AND `D_crux > 0` (the arms differ) AND FF-alive ≠ 0 (the FF arm is ALIVE). **If
  the FF arm ALSO produces the aftereffect (`percept_rg_ff ≠ 0` with the
  contingency sign), the gate FAILS to discriminate ⇒ NEGATIVE, diagnosed, NOT
  forced.** If the FF arm scores 0 everywhere INCLUDING the coloured positive
  control, it is a DEAD ARM (§1.1) and the crux is INVALID.
- **H_persist PASS** iff prior and percept are bit-identical across the intervening
  block. NULL ⇒ the effect is momentary/fatigue-like, reported.
- **H_floor PASS** iff (a) no-adapt percept == 0 AND (b) colour-alone `C == 0` with
  both percepts equal and non-zero.
- **H_noise PASS** iff `0/100` seeds reach `|C_noise| ≥ |C_structured|`.
- **H_offday PASS** iff all percepts == 0 with the flag off, and the §9 bench/sibling
  gates are unmoved.

**Exactly these tests. No sweeps, no re-runs.** A further attempt needs a NEW
pre-registration with a NEW mechanism-level hypothesis (§3.6).

## §6. Scope — what this does NOT show (§8)

- **A VALIDATION gate for predictive/opponent JOINT colour⊗orientation coding —
  NOT a recognition capability.** It shows the substrate's render-from-prior +
  opponent-residual reproduces the decisive contingent aftereffect that a
  feedforward classifier cannot, and nothing about object/scene recognition.
- **Orientation is supplied as a stimulus FEATURE (`theta`), not grown.** Grown
  orientation-selective maps are the diagnosed Hebbian dead-end; a validation gate
  legitimately takes orientation as input (as it takes cone values as input). The
  claim is about the JOINT PRIOR and the PREDICTIVE READOUT, which ARE the graph's.
- **The prior is a running mean over a small oriented-patch stimulus**, not a full
  grating field with spatial phase. The colour⊗orientation contingency, not the bar
  structure, is what the effect requires.
- **NOT claimed biological in magnitude or time-constant** — only that the SIGN,
  contingency, opponent character, and the feedforward/predictive DISSOCIATION
  reproduce. No decay dynamics, no persistence duration in real units.
- **NAMED FRONTIER (not this rung):** the other FAILURE-MODE GATES —
  apperceptive/associative dissociation, face-inversion + Thatcher, crowding,
  cerebral achromatopsia (VISION_VENTRAL_GROUNDING.md §FAILURE-MODE GATES).

## §7. MY PREDICTION, stated in advance (PROTOCOL §3.7)

I predict **every arm passes** and the gate DISCRIMINATES:

- **H_contingency:** `percept_rg(vert) = −10.0`, `percept_rg(horiz) = +10.0` exactly;
  swap flips sign. (The prior mean_rg = the adapting rg: +10 for red-vertical, −10
  for green-horizontal; the achromatic residual is 0 − prior.)
- **H_crux:** `percept_rg_ff = 0.0` for both orientations (achromatic observed rg =
  0, read directly); `D_crux = 10.0`; FF-alive on a red test = `+10.0` (ALIVE). The
  feedforward control produces NO aftereffect — the decisive dissociation.
- **H_persist:** prior `(sum_rg, n) = (+80, 8)` for vertical, `(−80, 8)` for
  horizontal, bit-identical across an intervening no-adapt tick block; percepts
  unchanged.
- **H_floor:** no-adapt `percept_rg = 0.0`; colour-alone `percept_rg(vert) =
  percept_rg(horiz) = −10.0`, `C = 0.0`.
- **H_noise:** `0/100`; mean `C_noise ≈ 0` (zero-mean adaptation averages to no
  pairing).
- **H_offday:** all 0.0; bench + siblings unmoved.

**Provisos (a broken one tells me what I did not understand):**
1. **The `by` axis reads 0.** The adapting colours are equiluminant on
   by = S−(L+M) (all have by=−10), so the prior mean_by = the observed by, and
   `percept_by = observed − prior = 0` at test. If `percept_by ≠ 0`, my opponent-axis
   accounting is wrong. (The manipulation is a pure rg-axis contingency.)
2. **The incoming-`tunes` join binds the right prior.** Each test region resolves to
   the Contingency of its own theta via the single incoming `tunes` edge. If the
   join mis-binds (e.g. NodesWhere/tunes ambiguity), the vertical test would read the
   horizontal prior and the contingency would INVERT. A sign inversion on
   H_contingency would indict the join, not the mechanism.
3. **The per-frame guard accumulates exactly n=frames samples.** `astep<frame`
   fires `mcc_learn` once per frame per adapting region. If the guard mis-fires,
   n≠8 and the mean still equals the (constant) adapting colour — so the SIGN
   claims survive, but H_persist's exact `(sum,n)` would break. This isolates the
   guard from the mechanism.
