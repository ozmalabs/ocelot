# ETA-SWEEP — PRE-REGISTRATION: the 8D 2×2, WITH the settling loop

*Committed BEFORE the confirmatory run. The design below is FIXED now; the only
fields filled from the burned-seed pilot (`scripts/eta_sweep_pilot.py`, seeds
0–7) are the final η grid, `n` (by power), and the map-structure NULLS. Engine
and provenance recorded in the OUTCOME.*

## 0. WHAT IS NEW, AND WHY THE QUESTION IS NOW ASKABLE

8D declared a §2 failure: **"there is NO η at which the learning rule is both
CONVERGENT and LOAD-BEARING"** (5e-4 near-vacuous; higher η moves the weights but
runs on). That was measured on the **bare cortex** — the wave-isotropy rung
proved it is BELOW model L — and **without a terminating settling loop**. The
settling layer is where GCAL's orientation actually comes from. It now exists
(`seeds/vision_settle.json`, load-ordered BEFORE `vision_onoff` so the learning
rule reads a SETTLED sheet) and, via cycle detection
(`w.detect_cycles`, engine `559d7f38…`), **it terminates**. This run asks 8D's
2×2 **with the settling loop running to a detected fixpoint**.

**The one-line opt-in (`domains/wave_world.step`) is committed with this rung and
proven inert by default** (§9: `getattr(self,"detect_cycles",False)`; DEFAULT ≡
explicit-OFF byte-identical, `max|Δact| = max|Δw| = 0.000e+00`; the learning
trajectory is unaffected by termination semantics — OFF ≡ ON, `max|Δ| = 0.0`).

## 1. HYPOTHESES (two-sided)

- **H_conv (§2):** the developmental learning rule (Oja on the ON/OFF weights),
  reading the SETTLED sheet, converges on its own formative input — drift(t) =
  ‖w(t)−w(t−Δ)‖/‖w(t)‖ → 0 over ≥3200 steps — **at some η in the grid**.
- **H_load:** at that η the converged state is LOAD-BEARING — Δ_OSI =
  OSI(trained) − OSI(untrained floor) exceeds the SESOI, cells alive.
- **H_2×2 (the 8D claim, two-sided):** there EXISTS an η that is BOTH (settling
  opens the window 8D found empty) — vs the null that **no η is both** (settling
  does not rescue the rule class).
- **H_struct (conditional on H_2×2):** if some η is both, the resulting map is
  STRUCTURED (per-cell preferred orientation spatially organised and/or
  across-seed reproducible) — vs the null (predicted by the wave-isotropy
  eigenspectrum) that **each cell's angle is an independent COIN FLIP**.

## 2. THE STATISTIC, EXACTLY

Per (η, seed), on the settling sheet (n_side=3, connectivity=8, settle=1.0 +
detect_cycles during development, settle=0.0 feedforward at the calibrated
probe):

- **CONVERGENCE:** the drift trajectory {drift(t)} at Δ=200-step checkpoints over
  TRAIN=3200 steps, summarised by `drift_final` (mean of the last 4 checkpoints)
  and `drift_first` (mean of the first 4). **Converged iff
  `drift_final < 0.5 · drift_first`** (a decaying trajectory; the 0.5 is the
  pilot script's own inherited cutoff, and the full trajectory is reported so the
  shape is visible, not just the ratio). The weight-drift floor **falls out**: a
  frozen arm has `drift ≡ 0` exactly (weights change ONLY via `oo_learn`), so 0
  is the true floor and any decay toward it is convergence.
- **LOAD-BEARING:** `Δ_OSI = OSI_mean(trained) − OSI_mean(untrained)`, PAIRED per
  seed (same init; the untrained arm is the in-run OSI floor, measured per seed).
  **Load-bearing iff the 95% CI of Δ_OSI (over seeds) lies above SESOI = 0.0595
  AND `n_dead = 0` on every arm.** `‖w‖` relative movement is reported alongside.
- **MAP STRUCTURE** (orientation mod 180 ⇒ every angle enters as a unit vector at
  2θ):
  - **Spatial:** `neighbour_similarity` = mean cos(2θ_i−2θ_j) over
    lattice-neighbour cell pairs, per seed, minus its **within-seed permutation
    null** (preferred angles shuffled across cell positions). Test the paired
    difference over seeds (95% CI vs 0).
  - **Across-seed:** `across_seed_R` = mean over the 9 lattice positions of the
    resultant length of the doubled preferred angles across seeds. **The control
    is the UNTRAINED FLOOR arm, NOT the pool-shuffle null** — see the pilot
    finding below.
  - `global_orientation_bias` (the pooled resultant) is reported so a global bias
    is neither mistaken for a map nor allowed to hide one.

**THE STRUCTURE CONTROL IS THE UNTRAINED FLOOR (pilot finding, and it MATTERS).**
The burned-seed pilot found the pool-shuffle null is FOOLED: the untrained floor
arm (NO cortical learning) already scores `across_seed_R = 0.549`, far above the
pool-shuffle null (0.42) and EQUAL to every trained arm (0.54–0.65). Cause: the
probe's argmax-tie aliasing (8D §4 — F0 over K=16 phases ties EXACTLY at
30/150° and 60/120° on the integer grid) makes a cell's preferred angle a
function of its POSITION, reproducible across seeds, **with no learning at all**.
So "across-seed reproducibility vs a pool-null" is a PROBE-GEOMETRY ARTIFACT, not
evidence of a learned map (exactly §13.1's "could the model have produced the
opposite?" — here the UNtrained model already produces the signal). **The honest
test is therefore TRAINED vs the UNTRAINED FLOOR, paired per seed:** learning is
structured iff training raises `neighbour_similarity` above the floor (CI of the
paired Δ > 0) OR raises `across_seed_R` materially above the floor's own R
(declared margin ≥ 0.10). Trained ≈ floor ⇒ learning adds NO structure ⇒ coin
flip in the only sense that matters.

**Unit of analysis is the SEED (§4).** `peak/base` is NOT read (§1.1). Floors are
measured IN-RUN, per arm, per seed; per-orientation alive counts reported.

## 3. THE ARMS, AND WHAT EACH CORRESPONDS TO (§6)

- **untrained (floor):** build_sheet(seed) → develop_retina(3000) → probe. No
  cortical learning. The in-run OSI floor for that seed's init. η-independent
  (one per seed). Corresponds to the newborn cortex on a developed retina.
- **trained(η):** build_sheet(seed) → develop_retina(3000) → cortex learns
  (`oo_eta=η`, lateral frozen) for 3200 steps on the agent's own spontaneous
  waves reading the SETTLED sheet → probe. Corresponds to development under the
  formative wave statistics.

The formative input is the agent's OWN retinal waves — dark-reared animals keep
their waves (§6), so this is the correct formative statistics, not "no input".

## 4. η GRID, n, AND WHAT IT COSTS

- **η grid (FIXED IN ADVANCE):** **{1e-4, 5e-4, 1e-3, 2e-3, 5e-3}** — the pilot
  maps the vacuous → run-on transition across exactly this span (5e-4: rel weight
  move 0.05, drift flat; 5e-3: rel move 0.59, drift RISING), and 1e-4 pins 8D's
  own cited "near-vacuous" point. η is a SWEPT IV, declared in advance (§4/§13);
  it is NOT a committed constant unless a single winner emerges (see §7).
- **n = 24** (seeds **24000–24023**). The pilot's `sd(Δ_OSI)` ∈ [0.061, 0.078]
  gives `n ≥ (2.8·sd/SESOI)²` = **9–14** for 80% power at the SESOI; n=24 exceeds
  that AND tightens the map-structure floor comparison (the pilot's `sd(Δ_nsim)`
  ≈ 0.11 gives n ≈ 24 to resolve a moderate spatial-organisation effect against
  the floor). **12000–23999 UNTOUCHED.**

### 4.1 PILOT SUMMARY (burned seeds 0–7; informs design, tests no hypothesis)

`scripts/eta_sweep_pilot.py`, engine `559d7f38…`. Per η (Δ_OSI vs the per-seed
floor; rel weight move; drift first→final over 3200 steps):

| η | Δ_OSI (sd) | rel move | drift 0→final | reading |
|---|---|---|---|---|
| 5e-4 | +0.044 (0.061) | 0.05 | 0.0041→0.0042 | vacuous; Δ_OSI < SESOI |
| 1e-3 | +0.009 (0.078) | 0.10 | 0.0083→0.0088 | vacuous |
| 2e-3 | −0.019 (0.074) | 0.22 | 0.0169→0.0192 | moves, drift RISES, OSI ↓ |
| 5e-3 | −0.017 (0.066) | 0.59 | 0.0441→0.0490 | moves a lot, drift RISES, OSI ↓ |

`n_dead = 0` on every arm. **No η is both convergent (drift→0) and load-bearing
(Δ_OSI>SESOI):** low η is vacuous, high η runs on (drift rising) with Δ_OSI going
NEGATIVE. **Structure:** the UNTRAINED floor already gives `across_seed_R`=0.549
(probe aliasing), and no trained arm exceeds it; neighbour-similarity is at/below
its permutation null at every η. This pilot on burned seeds is the basis for the
prediction below; the confirmatory run repeats it on the clean 24000 block.

## 5. MY PREDICTION, IN ADVANCE, WITH PROVISOS (§3.7)

**I predict the 2×2 stays EMPTY — a NEGATIVE (§7).** The wave-isotropy rung
measured the input covariance's leading eigenvector a DC blob (OI 0.0855) and the
next eigenpair NEAR-DEGENERATE (λ2/λ3 = 1.0907). Oja converges to the leading
principal component; a degenerate oriented eigenspace has NO unique leading PC, so
the weight vector rotates within it and **never settles** (drift stays up) while
the ANGLE it happens to point is a **coin flip**. The same degeneracy predicts
BOTH halves of the negative: low η is vacuous (converges, not load-bearing); high
η moves the weights (load-bearing) but drift does not fall (the rotation), and
whatever OSI appears carries a **random** preferred angle. **The settling loop
does not manufacture a leading PC the input statistics do not contain** — the
sd-loop rung's independent bound ("the loop composes what it holds; it does not
discover what it lacks").

**Provisos (a broken proviso tells me what I did not understand):**
1. **If some η is BOTH convergent and load-bearing**, the settling loop opened a
   window the bare cortex lacked — a real change, and then the map-structure test
   decides between a working V1 (structured) and the degeneracy realised (coin
   flip). Either is reportable; only a STRUCTURED map would be a working V1, and
   that would be ENGINEERING, not the paradigm claim (GCAL already works).
2. **If the winning η is a single value with no account** of what it falls out of,
   it is a KNOB and the mechanism is incomplete (§13) — I will say so, not bank it.
3. **If OSI never rises above its floor at any η** (feedforward probe), the load
   half is null regardless of convergence. SCOPE: I probe the learned RF
   feedforward with the CALIBRATED instrument; a settled-probe OSI (uncalibrated
   here) could be higher if lateral settling sharpens tuning — so feedforward OSI
   is a conservative lower bound on selectivity. The STRUCTURE (angle) verdict is
   robust to probe magnitude: sharpening tuning does not fix a random angle.

## 6. DECISION RULE, INCLUDING WHAT EACH OUTCOME MEANS

- **NO η is BOTH** (every η fails convergence OR load-bearing): the 2×2 is EMPTY.
  **8D's tension SURVIVES the settling loop.** The settling loop — GCAL's own
  orientation mechanism — does NOT rescue this rule class in this substrate. The
  cortex line through this mechanism is **EXHAUSTED with a diagnosed reason**
  (the input-covariance eigenspectrum, not a tuning failure). NEGATIVE, and the
  valuable outcome (§7).
- **Some η is BOTH, but the map is a COIN FLIP** (paired neighbour-sim Δ vs the
  UNTRAINED FLOOR has a CI including 0 AND trained `across_seed_R` does not exceed
  the floor's own R by ≥0.10): learning adds no structure over the probe artifact
  — the eigenspectrum degeneracy REALISED. A clean, distinct finding; **NOT a
  working map** and must not be reported as one.
- **Some η is BOTH and the map is STRUCTURED** (paired neighbour-sim Δ vs floor
  CI > 0 OR trained R exceeds floor R by ≥0.10): a converged, load-bearing,
  structured map — a **working V1**. **ENGINEERING, not the paradigm claim.** The
  sd-loop rung's negative stands untouched.

**No rescue, no η-tuning to manufacture a win, no coin-flip map reported as a
map (§7).** Exactly the grid, the n, and the arms listed — no sweeps beyond the
declared grid, no re-runs (a further attempt needs a NEW pre-registration with a
new mechanism-level hypothesis).

## 7. THE ρ→1 CEILING, RESTATED (§8)

This runs on a SMALL sheet (n_side=3) BY NECESSITY: ρ(M)→1 as the sheet grows
(0.45→0.87 over n_side 3→6), so a GCAL-scale sheet settles arbitrarily slowly
regardless of termination semantics. **A positive at small n does NOT clear that
ceiling** — it would license only "at this scale, with settling terminating,
the rule does/does not X". GCAL itself asserts convergence but shows "(data not
shown)". The scale I ran and what it licenses are stated in the outcome.

## §13 — WHAT FALLS OUT, WHAT GOES IN

The last three rungs committed **zero** constants. This run commits none either:
n_side/connectivity are the settling geometry (non-bipartite, ρ<1 — the sheet
that terminates); develop/train horizons are rung 7's and §2's; the drift floor
is exactly 0 (frozen weights do not move); the convergence ratio 0.5 is the pilot
script's inherited self-relative cutoff; SESOI 0.0595 is rung 6's. **η is a swept
IV, not a committed constant** — and if a single η wins with no account of what it
falls out of, it is named a KNOB and the mechanism called incomplete (§13). **GCAL's
η, γE/γI/16/σ/μ are NOT imported** (they killed cells twice in this tree).

### §13.1 — COULD THIS DESIGN HAVE PRODUCED THE OPPOSITE RESULT?

Yes. **Orientation appearing is NOT the signature I test** — GCAL makes
orientation from isotropic disks, so high OSI alone is the non-discriminating
signature that haunts this arc. The design measures **map STRUCTURE vs per-cell
OSI**: a pinwheel map and a field of randomly-oriented cells both give high mean
OSI, and the permutation nulls separate them. The convergence half could fail
(drift never falls) OR succeed (drift → 0) independently of the load half; the
structure half could read STRUCTURED (obs ≫ null) OR coin-flip (obs ≈ null) —
the nulls are computed from the SAME angles, so a structured map cannot hide as a
coin flip nor vice versa. The prediction (empty 2×2, and coin flip if not) is
therefore RISKED, not forced.
