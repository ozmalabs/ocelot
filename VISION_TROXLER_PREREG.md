# TROXLER — pre-registration

*Written and COMMITTED before the confirmatory run. PROTOCOL §3. The commit
timestamp of this file is the gate; the run logs are timestamped against it.*

**Engine:** `366ce5f14eff`, resolution verified by
`tests/test_engine_provenance_migrated.py` (7/7) — the loaded engine is a build of
THIS TREE'S Rust source (§10.1's invariant is CONTENT, not location; my tree's tracked
`runners/dsl/src` is byte-identical to the canonical tree's, the only difference being
an untracked `py.rs.selfmod.bak` that cargo never compiles).
**Base:** `80e706f5` (rebased onto the rewritten main tip; my worktree was 5 commits
behind and 0 ahead — a fast-forward, never a merge).
**This rung adds NO Rust.**

---

## 1. Why this test is possible now, and why it was not before

FM-0 condemned the Troxler test: the Engbert drift was **decorative**. `D = max|saw1 −
saw0|` was `0.000000e+00` EXACTLY on `lum`/`x`/`theta`/`resp` at every one of 400 steps,
because no production admitted a Gaze↔Eye edge and `gaze_pos()`'s only consumers were
`walk()` and one test assertion — **the walk's sole consumer was the ruler that measured
it.**

I re-ran both halves myself before building anything on them (engine `366ce5f14eff`,
seed 0, 400 steps):

| attribute | FM-0 at defaults (re-run) | FM-0b wired (re-run) |
|---|---|---|
| `D_lum` | 0.000000e+00 | **8.071079e-01** |
| `D_x` | 0.000000e+00 | **5.315726e-01** |
| `D_theta` | 0.000000e+00 | **4.013261e-01** |
| `D_resp` | 0.000000e+00 | **5.169134e-01** |

Both reproduce the brief's numbers exactly. **§9 holds**: at the defaults
(`world_sample=0`) FM-0 still reports VACUOUS, so every committed result reproduces.
This is §1's **fifth clause** — the entry gate Troxler now has and did not have.

**`D > 0` is PLUMBING, NOT A FINDING** (the drift-wiring rung says so itself). It buys
the right to ask the question; it does not answer it.

---

## 2. §6 — WHAT EACH ARM CORRESPONDS TO IN THE ANIMAL

*§6 exists because `dark` was set to "no input" for TWO pre-registrations while the plan
itself said dark-reared animals keep their waves. Pre-registration protects the
statistics; it does NOT protect the design. This section is the design.*

**"Freeze the drift" is NOT "stabilise the image."** Ditchburn & Ginsborg 1952 / Riggs &
Ratliff 1952 / Yarbus stabilised the image *against* eye movement with a mirror on a
contact lens: **the eye keeps moving; the image follows it**, so the RETINAL image is
static. Freezing the gaze is **paralysis** — a different manipulation with a different
meaning.

| arm | `saw` | the world | the retina sees | in the animal |
|---|---|---|---|---|
| **A — DRIFT** | 1 | stationary scene | a MOVING image | a normal eye at fixation |
| **B — STABILISED** | **1 — the eye still moves** | scene re-painted at the eye's current position each step | a STATIC image | **Ditchburn's mirror**: the image follows the eye |
| **C — FROZEN** | 0 | stationary scene | a STATIC image | **paralysis** — a DIFFERENT experiment |

**Arm B is the honest Troxler arm.** Arm C is included ONLY to MEASURE whether the two
coincide in this model, rather than assume it (PART A below). They coincide **iff** the
gaze's only wired consumer is the sampling — and that is measured with FM-0's own
statistic, not grepped (§12.1: the ninth inert instrument was the supervisor's and it
WAS a grep).

**MEASURED BEFORE THE RUN (`scripts/troxler_calibrate.py` PART A, burned seed 0, 400
steps, FM-0's own statistic): `D(B,C) = 0.000000e+00` EXACTLY on `lum`, `x`, `theta` AND
`resp`.** The two arms coincide. So in THIS model the drift's only wired effect IS moving
the image, and "freeze the gaze" and "stabilise the image" are the same experiment. **In
the ANIMAL they are NOT** — paralysis removes the eye's motion, stabilisation removes only
the image's. **The model cannot currently tell them apart. That is a SCOPE LIMIT (§8),
declared here in advance, not a convenience.** Arm B is still the arm that is reported,
because it is the one that corresponds to Ditchburn.

**Where the stabilisation lives, and why.** Ditchburn's mirror is **apparatus, not
physiology**, so it lives in the WORLD. The adapter's documented job is to state that
photons exist at world locations (`add_world`: *"It does NOT say which receptor sees
which photon — that is `ey_sample_at_gaze`'s decision"*), and `present_world` exists
verbatim *"for a moving-scene control"*. Arm B **is** that moving-scene control: a scene
whose motion equals the gaze's. The EYE is byte-identical across all three arms but for
`saw`, which is graph DATA on `EyeParams` (§0). Implementing the stabilisation as a RULE
would put the mirror INSIDE the eye and make the retina cancel its own gaze — that is
**efference copy / VOR, a different mechanism** that no stabilisation experiment
contains. There is no Python conditional over graph state: the apparatus is an
unconditional affine translation of the photon field.

**Ordering, measured not assumed:** within one tick the sampler reads the gaze BEFORE
`ey_saw_move` moves it, so the apparatus paints at the gaze read before `step()`. Arm B
**asserts its own success every step** (`stab_err = max|lum − W_img|`), because a
stabilisation that silently failed would look exactly like "the drift does not matter".

---

## 3. The mechanism, stated before the result (§13.1)

`resp = max(x − θ, 0)`; `xbar = β·xbar + (1−β)·resp` (β=0.991, an EMA of the **output**);
`θ += λ·(xbar − μ)` (λ=0.01). `μ = mu_endo`, the setpoint each cell measured in itself
during the pre-visual phase (`mu_mode=1`).

**The homeostat drives each cell's mean OUTPUT to μ — not to zero.** So on a static
image every cell converges to `θ_i → x_i − μ` and hence `resp_i → μ` **for every i**:
the sheet ends **uniform and ALIVE**, not silent. The image is gone; the cells are firing
at exactly their own measured setpoint. That is what a fade IS here, and it is why
aliveness must be read beside the contrast.

`mu_mode=1` is used because `mu_mode=0` (GCAL's imported 0.024) drives the sheet to **0%
aliveness for a window** — §1's fourth clause would fail on the arm before any fade could
be read. That is the setpoint rung's own finding, used rather than re-litigated.

---

## 4. The statistic, exactly

- **`contrast(t) = SD over the 256 cells of `resp` at step t`.** The fade measure.
- **`alive(t) = frac(resp > 0)`.** Reported at EVERY timepoint for EVERY arm.
- **Primary statistic:** `contrast_final` = `contrast(t = 3200)`, per arm, per seed.
- **Primary comparison:** paired within seed, **arm A (DRIFT) vs arm B (STABILISED)**.

**`SD(resp)` reads 0 for a SILENT sheet and a UNIFORM one alike.** This is exactly how
FM-1's headline fade window (t≈300–800) was disqualified as dead-arm readings once
aliveness came back 10.5% (§1.1). **So contrast is NEVER read alone**: a fade claim
requires the sheet to be ALIVE and UNIFORM. **A silent arm is a FAILED GATE, never a
successful fade.** `peak/base` is NOT read (unbounded; blown up in two independent
rungs).

---

## 5. §13 — what every number here falls out of

*"Magic numbers fall OUT of natural processes, they do not go IN." A tuned fade is worth
nothing. Before committing a float, say in one sentence what it falls out of.*

| number | falls out of |
|---|---|
| **VIS_STEPS = 3200** | **the §2 SETTLE**: the stabilised arm's contrast is identical at t=3200, 4800 and 6399 (measured on burned seed 0: `|c(6399)−c(3200)| = 4.174e-09`). It is where the arm has REACHED ITS FIXED POINT — not where a fade looks best. The fixed point is `mean_resp = 0.144319` = `mu_endo` = 0.144319 **exactly**, which is what the homeostat's equations say it must be. |
| **CALIB_STEPS = 3200** | the setpoint rung's own measured convergence, inherited unchanged. |
| **the scene** (period-8 grating + blob) | the setpoint rung's committed `static_frame`, reused unchanged and extended to the world's extent. Not chosen here. |
| **`mu_endo` ≈ 0.1443** | the cell's own spontaneous wave activity, measured in itself. No constant of anyone's. |
| **the fade threshold** | **THERE IS NONE.** No fade threshold, adaptation rate or stabilisation duration is chosen so that fading appears. The arms are compared to EACH OTHER on a continuous statistic. |

**I set no free parameter of the drift or of the adaptation.** `temp`, `saw_lam`,
`saw_eps` came from the Engbert rung; `λ`, `β` from GCAL. Neither was chosen with the
other in mind — which is the whole point of §7 below.

---

## 6. §13.1 — COULD THIS MODEL HAVE PRODUCED THE OPPOSITE RESULT?

**This is the crux, and the answer is different for the two arms. I state it before the
run.**

**Arm B's fade is ARCHITECTURALLY FORCED.** A per-cell homeostat on a static input MUST
equalise every cell to μ — I derived it from the rule equations in §3 above, before
running. **No rule could have failed to yield it.** Reporting "the stabilised image
faded" as a discovery would therefore be **a tautology with error bars** — the §13.1
disease, the same as the Engbert crossover (`ey_saw_relax` solely responsible for the
persistence, `ey_saw_potential` solely responsible for the antipersistence: one rule per
half ⇒ assembled, not derived). **I claim no credit for arm B fading.**

**The falsifiable content is ENTIRELY in arm A.** *Does the drift's own timescale outrun
adaptation?* That is **not** forced by any rule:

- the **drift** timescale falls out of **Engbert's self-avoiding walk** (α measured, never
  imported: 1.1553 / 0.7590);
- the **adaptation** timescale falls out of **λ, β and `mu_endo`** (the last derived from
  endogenous activity);
- **neither was chosen with the other in mind.**

If they land on opposite sides of the fade boundary, that is a genuine falling-out of two
independently-derived quantities. **If the drift is too slow and BOTH arms fade — or too
fast and NEITHER does — that is a real, reportable NEGATIVE** about whether the wired
drift is *quantitatively* right, not merely topologically connected.

**Is arm A the "one rule per half" disease?** No, and here is the distinction. The Engbert
crossover had one rule *solely responsible* for each half of a QUALITATIVE signature. Here
the homeostat forces the fade on ANY static input; whether drift makes the input
non-static ENOUGH is a **quantitative race between two timescales** that no rule fixes.
Either outcome is expressible. **Arm A could have failed. Arm B could not.**

---

## 7. Hypothesis (two-sided) and my PREDICTION with provisos (§3.7)

**H1 (two-sided):** `contrast_final` differs between arm A (DRIFT) and arm B
(STABILISED).
**H0:** it does not.

**My prediction, stated in advance:** **A > B.** The stabilised arm fades to ~0 contrast
while remaining ~100% alive; the drifting arm does not fade.

*(Predicted directions in this arc have been wrong four times. Two-sided regardless.)*

**Provisos — what breaks if I am wrong:**

1. **If BOTH arms fade** ⇒ the drift is **too slow** to outrun adaptation. A real
   negative about the drift's quantitative calibration. Report; do not rescue.
2. **If NEITHER fades** ⇒ 3200 steps did not reach the homeostat's fixed point, or
   `mu_mode=1` is not regulating. Since §2 measured the settle on burned seed 0 in
   advance, this would mean the settle does not generalise across seeds — also a
   reportable negative.
3. **If arm B fades but the sheet is SILENT (`alive → 0`)** ⇒ **FAILED GATE, not a
   fade** (§1.1). The claim is withdrawn, not reinterpreted.
4. **If `stab_err > 0`** ⇒ the mirror did not stabilise, and arm B is not the experiment
   I claimed. Withdraw.
5. **If D(B,C) ≠ 0** ⇒ the gaze has a wired consumer beyond sampling; then arm C is NOT
   equivalent to arm B and only B may be read as Troxler.

**The prediction I am LEAST confident in:** that the drift arm's aliveness stays high
enough for its contrast to be read as structure rather than as rectification noise. The
ReLU silences whichever cells sit below θ, and in a moving image that set churns.

---

## 8. n, FIXED IN ADVANCE (§3.3)

Power pilot on **already-burned seeds 0–5** (variance only), reported in PART D of
`scripts/troxler_calibrate.py`. **Measured:** drift mean 0.133422 (sd 0.002011),
stabilised mean 0.000220 (sd 0.000102), paired diff mean 0.133202 (sd 0.001962),
**6/6 positive, Cohen dz = 67.89**. The separation is **deterministic in sign**.

**n = 8.** With a deterministic sign, the exact two-sided sign test gives
`p = 2·(1/2)^8 = 0.0078` — the smallest n that can reach p < 0.01, and the setpoint
rung's own precedent. Fixed before the confirmatory run and not revisited.

**Unit of analysis is the SEED** (§4), never the cell: the 256 cells share one input and
one gaze, so they are not independent.

---

## 9. Confirmatory seeds — DECLARED IN ADVANCE

**Block: 15000–15007** (n=8), taken from the free block **15000–15999** declared in the
brief. Recorded in the ledger.

**Never used for anything before.** 14000–14999 is the failure-mode battery's (14000–14007
consumed by the endogenous setpoint); 12000–12999 and 13000–13999 are allocated to other
rungs. **I touch none of them.** Calibration/pilot/settle work above is on already-burned
seeds 0–5 and burns nothing new.

---

## 10. Decision rule, including what a null means

- **Statistic:** exact two-sided **sign test** on the paired per-seed difference
  `contrast_final(A) − contrast_final(B)`, n=8. The pilot indicates the separation is
  deterministic (sd → 0 across the sign), which makes a t-test undefined or meaningless —
  **the sign test is declared here, in advance, for exactly that reason** (the setpoint
  rung's precedent, where sd=0 made the t-test undefined).
- **Secondary (descriptive, not a gate):** paired difference with a bootstrap 95% CI, and
  per-arm per-timepoint aliveness.
- **PASS (H1):** p < 0.01 **AND** arm B `alive_min` > 0.99 **AND** arm B `max_stab_err`
  == 0 **AND** arm A `alive_min` > 0 at every timepoint. **Conjunctive** (§4): a
  mechanism must not be able to pass by making itself inert.
- **NULL:** if p ≥ 0.01, the drift does not measurably protect contrast at this
  duration ⇒ **the wired drift is topologically connected but quantitatively wrong**, and
  I report that as the result. **A null is a finding about the drift's calibration, not a
  licence to re-run with another duration.**
- **Exactly these tests. No sweeps. No re-runs.** A further attempt needs a NEW
  pre-registration with a NEW mechanism-level hypothesis (§3.6).

---

## 11. §8 — scope limits, declared in advance

- **This licences nothing about which biological mechanism is correct.** A homeostatic
  threshold is ONE candidate for Troxler; adaptation in the receptor, in the bipolar, or
  synaptic depression are others, and this result does not discriminate them.
- **The drift here moves ~1 receptor per step** — LARGE relative to receptor spacing. Real
  fixational drift is a small fraction of the receptor lattice per comparable interval. So
  a non-fade in arm A is demonstrated in a **coarse-drift regime**, NOT in the delicate
  biological one where the margin is thin. **The margin, not just the sign, is the
  reportable quantity.**
- **`mu_endo` inherits rung 1's wave protocol** — free of a *constant*, not free of the
  ladder beneath it.
- **The commensurability wound is unhealed** (the setpoint rung's own): `mu_endo` averages
  a `{0,1}` burst alphabet while `resp` is graded. Nothing here tests that they are the
  same quantity.
- **If D(B,C) == 0**, this model **cannot distinguish paralysis from stabilisation**. The
  animal can (the animal's drift has consumers this model does not have). That is a scope
  limit on the model, and it is reported as one rather than hidden.
