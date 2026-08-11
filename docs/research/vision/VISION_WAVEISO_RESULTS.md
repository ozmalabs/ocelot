# WAVE ISOTROPY — RESULTS

**THE PREMISE THREE RUNGS SHARED IS HALF TRUE, AND THE HALF THAT IS FALSE
RELOCATES THE BLOCKER.**

Engine **`74fc035c8595`** @ `runners/dsl/python/substrate_rs/_native.abi3.so`,
**`shared` build — Rust source byte-identical to this tree** (this rung adds NO
Rust; legitimate under §10.1 rule 4). Base `d9300ccc`; pre-registration committed
**BEFORE** the run at **`fb8af6ae`**. Seeds **20000–20015** (n=16, fixed in
advance). Runner: `scripts/waveiso_{lib,calibrate,pilot,confirm}.py`. Raw:
`results/waveiso_{calibrate,pilot,confirm}.json`.

**Scope: this rung measured the STIMULUS. No cortex was touched, no learning rule
run, no seed edited, no default moved, no constant introduced (§9).**

## 1. THE HEADLINE

| the claim | verdict |
|---|---|
| *"The wave ensemble is orientation-ISOTROPIC"* (rungs 8C, 8E) | **CONFIRMED — measured, for the first time.** |
| *"...therefore the input carries no orientation"* (the inference drawn from it) | **REFUTED. The waves are travelling FRONTS and every front is LOCALLY ORIENTED.** |
| *"No Oja-class rule can produce orientation selectivity from this ensemble"* | **CONFIRMED, and RENDERED. Arithmetic, not a bug.** |

**The structure is THERE. Oja cannot see it. Both are true, and the second is not
caused by the first.**

## 2. THE DECISIVE NUMBER — the eigenspectrum of `E[xx^T]`

**The leading eigenvector IS what Oja converges to.** Rendered, seed 20000
(every entry POSITIVE, peaked at centre, no sign change, no orientation):

```
leading eigenvector of M = E[xx^T]          leading eigenvector of SIGMA (mean-centred)
   **####*   +0.62 +0.67 +0.71 +0.73 ...       =++**++   +0.46 +0.53 +0.58 +0.61 ...
   *#%%%##   +0.68 +0.77 +0.84 +0.86 ...       +*#%##+   +0.54 +0.67 +0.76 +0.80 ...
   #%@@@%#   +0.72 +0.84 +0.93 +0.96 ...       +#%@@#*   +0.59 +0.77 +0.89 +0.95 ...
   #%@@@%#   +0.74 +0.87 +0.96 +1.00 ...       *%@@@%*   +0.62 +0.81 +0.95 +1.00 ...
   #%@@@%#   +0.73 +0.86 +0.94 +0.96 ...       *#@@%#+   +0.62 +0.79 +0.91 +0.95 ...
   ##%%%#*   +0.71 +0.80 +0.85 +0.86 ...       +##%#*+   +0.59 +0.71 +0.79 +0.80 ...
   *####**   +0.65 +0.70 +0.72 +0.73 ...       ++**++=   +0.52 +0.58 +0.61 +0.61 ...
```

**It is a DC BLOB.** Not a Gabor, not a grating, not an edge. A rotationally
symmetric, strictly positive, centre-weighted blob — **and mean-centring does not
rescue it.**

### The spectrum (n=16, 95% CI; FLOOR = disks, IDEAL = bars at one orientation)

| statistic | waves (CI95) | FLOOR | IDEAL | midpoint | verdict |
|---|---|---|---|---|---|
| `M_leading_OI` | **0.0855** [0.0655, 0.1056] | 0.0054 | 1.0000 | 0.5027 | **ISOTROPIC** |
| `Sigma_leading_OI` | **0.0966** [0.0751, 0.1182] | 0.0057 | 1.0000 | 0.5029 | **ISOTROPIC** |
| `Sigma_leading_DC` | **0.9576** [0.9558, 0.9594] | 0.9399 | **0.0000** | — | **a blob; the IDEAL's is a pure grating** |
| `A2_global` | **0.0214** [0.0135, 0.0292] | 0.0008 | 0.9532 | 0.4770 | **ISOTROPIC** |
| `coh_global` | **0.0560** [0.0325, 0.0796] | 0.0012 | 1.0000 | 0.5006 | **ISOTROPIC** |
| **`coh_local_RF`** | **0.7809** [0.7726, 0.7892] | 0.4643 | 1.0000 | 0.7322 | **ANISOTROPIC** |

Per-mode (seed 20000): the oriented modes **exist but are subdominant and
DEGENERATE**.

| mode | λ | OI | DC |
|---|---|---|---|
| 1 | **2.5589** | **0.0650** | **0.9832** ← the blob Oja converges to |
| 2 | 0.7170 | 0.4167 | 0.0000 ← oriented |
| 3 | 0.6835 | 0.0955 | 0.0003 |
| 4 | 0.6533 | 0.3831 | 0.0000 ← oriented |

- **`λ1/λ2` = 3.5236** [3.4524, 3.5948] — the blob wins by 3.5×, decisively.
- **`λ2/λ3` = 1.0907** [1.0668, 1.1145] — **the oriented modes are NEARLY
  DEGENERATE with each other.**

**⇒ Two independent barriers, and this is the mechanistic finding:**

1. **Oja converges to the blob** (λ1 wins by 3.5×). No orientation. Arithmetic.
2. **Even if you remove the DC — which is exactly what rung 7's decorrelation and
   rung 8E's H1 DID — the next eigenspace is a near-degenerate oriented pair
   (λ2/λ3 = 1.09).** The "preferred" orientation is then a **COIN FLIP**.

**That is rung 8D's ARGMAX LOTTERY, arriving independently from the stimulus
side, and it is a sharper account of rung 8E's H1 null than 8E's own.** 8E said
whitening *"removed a redundancy without installing an anisotropy."* Measured, the
truth is finer: **whitening EXPOSES oriented modes (OI 0.38–0.42) — it just hands
them over DEGENERATE, so nothing can consistently select among them.**

## 3. LOCAL vs GLOBAL — THEY DISAGREE, AND THE DISAGREEMENT IS THE FINDING

| ensemble | `coh_local` (per-RF) | `coh_global` (ensemble) |
|---|---|---|
| white noise (OOD) | 0.1956 | 0.0035 |
| **FLOOR — disks (isotropic + correlated)** | 0.4643 | 0.0012 |
| **DISCRIMINATOR — bars, random θ per frame** | 0.7060 | 0.0533 |
| **THE WAVES** | **0.7809** | **0.0560** |
| **IDEAL — bars, one fixed θ** | 1.0000 | 1.0000 |

**The waves land on the DISCRIMINATOR, on BOTH axes, almost exactly.** Our wave
ensemble is statistically a set of **randomly-oriented bars**: every wavefront
carries an orientation as strongly as a bar does (0.781 vs 0.706, both far above
the disk floor 0.464 and the white-noise floor 0.196), and the ensemble average
of those orientations is **isotropic** (0.056 vs 0.053, both at the floor).

**An ensemble of anisotropic waves with RANDOM propagation directions averages to
an ISOTROPIC ensemble covariance.** That is not a defect of the waves. It is the
arithmetic of averaging a quantity whose phase is uniform — and **Oja averages.**

## 4. DO THE WAVES FORM FRONTS? — YES

`front_nb_raw` = **1.9898** (mean number of active 4-neighbours of an active
cell). **A thin 1-cell CURVE reads ~2; a solid blob approaches 4; scatter
approaches 0.** The regimes are separated by the statistic's own geometry, not by
a chosen threshold.

The waves are **thin travelling fronts**, alive on every arm: `frames_dead` = **0
of 16 seeds**, density 0.1325 [0.1271, 0.1379]. At 128² the fronts are even
cleaner (`nb` = 1.9997).

**So H_A's PREMISE — "if our waves lack travelling fronts with local orientation"
— is REFUTED. They have both.**

## 5. THE VERDICT: NEITHER H_A NOR H_B — AND THE THIRD ANSWER CONTAINS THE TRUE HALF OF EACH

- **H_A — "the input is the problem".** **Its premise is FALSE** (fronts exist,
  locally oriented at 0.781). **But its CONCLUSION SURVIVES**: no Oja-class rule
  can produce orientation from this ensemble, because the ensemble's leading
  eigenvector is a blob. **The arc's cortical negatives ARE explained without any
  appeal to a broken cortex.**
- **H_B — "the input is fine and isotropy is a red herring".** **The isotropy is
  REAL, so it is not a herring** — for Oja it is an absolute barrier. **But H_B is
  RIGHT about the mechanism**, and this rung demonstrates it directly: see §6.

**THE SYNTHESIS — the blocker is the RULE CLASS.** Orientation lives
**per-wavefront**, with a phase that cancels under ensemble averaging. Oja
averages. The stimulus is not at fault and the cortex is not at fault: **a
second-order, averaging rule is blind to exactly the structure this stimulus
carries.** This is §0.2's own symmetry argument and §4.2's *"symmetry-breaking
faster than the averaging timescale"* — now measured for ORIENTATION rather than
direction, and with the eigenvector rendered.

## 6. WHAT GCAL ACTUALLY REQUIRES — read from the source, and INDEPENDENTLY VERIFIED (§12.4)

`VISION_PRIOR_ART.md` §2 is a peer's claim, so the four load-bearing points were
**re-retrieved independently from Stevens, Law, Antolík & Bednar (2013),
[PMC6618482](https://pmc.ncbi.nlm.nih.gov/articles/PMC6618482/)**. **All four
CORROBORATE the prior art:**

| point | verbatim from the paper | status |
|---|---|---|
| pre-eye-opening input | *"noisy disk-shaped patterns randomly placed on the retinal photoreceptors"* | ✔ as §2.6 says |
| learning rule | Hebbian, with *"divisive postsynaptic weight normalization"*, *"the total of all weights ω_ij to neuron j in projection p is 1.0"* | ✔ — and this Taylor-expands to **Oja** (§2.4) |
| V1 lateral settling | *"V1 continues to compute in a series of settling steps"* — **16 settling steps**, γE = **1.7**, γI = **−1.4** | ✔ |
| learning rates | α_A = **0.1**, α_E = **0.0**, α_I = **0.3** | ✔ |

**THE DEDUCTION THIS FORCES — and it is what makes the result decisive rather
than descriptive:**

1. **GCAL's input IS my FLOOR arm.** Noisy disks read `A2_global` = **0.0008**,
   `Sigma_leading_OI` = **0.0057**, `coh_global` = **0.0012** — **MORE isotropic
   than our waves on every statistic.**
2. **GCAL's learning rule IS Oja** (L1 where we use L2; same contraction).
3. **GCAL nevertheless produces orientation maps from that input.**

**⇒ GCAL's orientation CANNOT come from its stimulus's second-order statistics
(they are isotropic — measured here), and CANNOT come from its learning rule
(it is Oja, which converges to the blob — measured here). It can ONLY come from
the 16 SETTLING STEPS of lateral competition that run WITHIN each pattern
presentation, BEFORE the Hebbian step.** The bubble selects a subset of the
pattern; the Hebbian step then learns *that*, not the ensemble average — which is
precisely "symmetry breaking in the weights under lateral competition," H_B's
claim, now with the arithmetic that makes it necessary rather than optional.

### 6.1 A NAMING COLLISION, REPORTED NOT FIXED (§9) — we are NOT model "AL"

Rung 8B recorded: *"Our layer is model **'AL'** (adaptation, no gain control)."*
**Measured, that is not right, and the cause is one word doing double duty across
two layers.**

- **GCAL's `L`** = **V1** lateral excitation/inhibition, settled 16 steps into
  activity bubbles (γE=1.7, γI=−1.4, α_E=0.0, α_I=0.3). **It is the BASELINE of
  the whole L → GCL → AL → GCAL lattice.**
- **This tree's `vision_lateral.json`** is a **RETINAL centre-surround predictive
  coder** (`lat_pool` / `lat_residual` / `lat_bipolar` — *"resid = centre − g1·h1
  − g2·h2"*), and it is **subtractive**. It is a retinal analogue of GCAL's **GC**
  (which is **divisive**, in the LGN) — **not** GCAL's **L** at all.
- **Audited across all 22 `seeds/vision_*.json`: there is NO `exc_strength`, no
  `inh_strength`, no settling loop, and no Unit→Unit lateral anywhere.** The four
  matches for "settl*"/"bubble*" are **prose in comments**, not mechanism.
- Rung 8E's **`Δ_lateral`** is, by its own pre-registration's arm table, *"rung
  7's decorrelated ON/OFF"* — **the retina**, not V1 competition.

**⇒ We do not have model AL. We do not have model L. We have the afferent
projection alone — BELOW the lattice's baseline — and the one component the prior
art says MAKES the anisotropy has never been implemented in this tree.**

This is the same disease rung 8C caught in a different costume: *"Two TRUE facts
about DIFFERENT LAYERS composed into a premise about a seam neither crosses."*
**Reported, not repaired.**

## 7. §1 CALIBRATION — ALL GATES PASS, AND ONE FLOOR HAD TO BE REPLACED

| gate | arm | result |
|---|---|---|
| **1. FLOOR** (isotropic + correlated) | disks | `A2g` **0.0008**, `coh_global` **0.0012**, `Sigma_OI` **0.0057** — at floor ✔ |
| **2. IDEAL** (anisotropic) | bars, fixed θ | `A2g` **0.9532**, `coh_local`/`coh_global` **1.0000**, `M_OI` **1.0000** ✔ |
| **3. DISCRIMINATOR** | bars, random θ | `coh_global` **0.0533** (≈floor) AND `coh_local` **0.7060** (≈ideal) ✔ |
| **4. ARMS ALIVE** (§1 cl. 4) | every arm | `frames_dead` = **0** everywhere; densities 0.119–0.133 ✔ |
| **5. ANALYTIC** | iid Bernoulli | predicted `λ1`=0.693570 / `λ2`=0.098087; measured **0.693570 / 0.098087** — **exact to 6 dp** ✔ |

**Separation floor→ideal: `A2_global` 0.0008 → 0.9532 (~1200×); `M_leading_OI`
0.0054 → 1.0000 (~185×).** The instrument spans its own range (§13.1).

### 7.1 THE SIXTEENTH INERT INSTRUMENT WAS MINE, AND THE GATE CAUGHT IT

**The first cut used WHITE NOISE as the isotropic floor. It read `A2_global` =
0.5312, not ~0.** Diagnosis: white noise has `rho(d) ≈ 0` at every `d ≠ 0`, so
`A_m = |Σρe^{imθ}| / Σ|ρ|` is a **ratio of sampling noise to sampling noise** —
undefined, O(1). **That is `peak/base`'s disease in a third costume: a ratio whose
denominator goes to zero** (§1.1's corollary, which has now blown up in three
independent rungs).

**White noise is OUTSIDE this statistic's domain, not at its floor.** Had I read
the waves' `A2_global` = 0.021 against an assumed floor of 0, or against white
noise's 0.53, I would have reported *"the waves are MORE isotropic than noise"* —
a fluent, wrong sentence. **The honest floor must be isotropic AND correlated**,
which is why it is disks. White noise is retained as `CONTROL_white_noise_OOD` and
reported rather than hidden.

**A_2 is bounded in [0,1] by the triangle inequality BY CONSTRUCTION** — the
obvious alternative (normalising by `Σρ(d)`, a modulation depth) is the same
unbounded ratio that killed the calibration reframe. It cannot blow up.

### 7.2 §13.1 — COULD THIS HAVE PRODUCED THE OPPOSITE?

**Yes, demonstrably**: the same code path reads `OI = 1.0000` and `coh_local =
1.0000` on `bars_fixed_0`, and `coh_local = 0.196` on white noise.

**THE LATTICE HAZARD, declared before the run and now measured.** The retina's
`neighbour` edges are a **4-NEIGHBOURHOOD on a square lattice**, and this arc has
already found the 4-connected argmin to be a cardinal-axis artifact. A diamond
front is **4-fold symmetric**, and **a 4-fold-symmetric `ρ` has `A_2 = 0`
IDENTICALLY** (`e^{2i(θ+π/2)} = −e^{2iθ}`: the four lattice-equivalent
displacements cancel in pairs). **So an `A_2` at the floor is EXACTLY what a
lattice diamond would also look like, and `A_2` alone cannot tell them apart.**

That is why `A_4` was pre-registered at every arm. **Measured: `A4_global` =
0.0029 [0.0018, 0.0041] — BELOW the disk floor's own 0.0867.** So there is **no
detectable 4-fold lattice structure at the RF grain**, and the isotropy verdict is
**not** a diamond hiding under a blind harmonic. The `coh_local` result is also
immune to this by construction: it is a gradient statistic, not a lattice-sampled
harmonic.

## 8. THE PROVISOS — one broke my way, one did not, and both are reported

| proviso (declared in §6 of the prereg) | outcome |
|---|---|
| *"The window may be making the DC"* — `window_steps=2` ORs 3 frames | **BROKE MY CONCERN, i.e. the result SURVIVES.** At `window=0`: `M_DC` **0.9763**, `M_OI` **0.0959**, `coh_local` **0.8014**, density 0.0666. **The blob is not a window artifact.** |
| *"64×64 may be too small"* | **SURVIVES.** At 128²: `M_DC` **0.9799**, `M_OI` **0.0844**, `coh_local` **0.8503**, `coh_global` **0.0652** — same verdict, local coherence even higher. |
| *"`coh_local` is positively biased; if waves land near the disk floor, my claim is wrong"* | **HELD.** Waves 0.781 vs disk floor 0.464, CI excludes the midpoint. |
| *"The disk floor may be too high to separate"* | **HELD**, but honestly: disks read `coh_local` = 0.464 because **a disk's EDGE is locally oriented too**. The waves clear it, and clear the discriminator (0.706). |

**MY PREDICTION WAS RIGHT ON ALL FIVE POINTS — AND IT IS THE WEAKEST EVIDENCE
HERE.** The prediction was made **after** the burned-seed pilot had already shown
the pattern, and the pre-registration says so in those words. **A pilot-informed
prediction is cheap.** What was expensive, and what makes the result worth
anything, is that the design **could have produced the opposite** (§13.1) and that
the floor **had to be replaced when it failed its own gate** (§7.1).

## 9. WHAT THIS DOES NOT SHOW (§8)

- **It does not run GCAL.** It shows GCAL's *input* is ensemble-isotropic and
  GCAL's *rule* is Oja; the deduction that GCAL's orientation comes from the
  settling bubble is **forced by those two facts plus this measurement**, but it
  is **not** a demonstration that GCAL's L would work on OUR waves. **That is the
  obvious next rung and it is NOT claimed here.**
- **It licenses nothing about which biological mechanism is correct.** The
  verified research already refuted the Hebbian-vs-sparsity question 0–3.
- **No cell was trained.** This is linear algebra on a stimulus. `coh_local` shows
  orientation is present at the RF grain; it does **not** show any rule could
  extract it.
- *"No Oja-class rule can produce orientation"* is **arithmetic about THIS
  measured ensemble**, not a theorem about Hebbian learning in general. A
  **nonlinear** Hebbian rule (`Δw = η·g(y)·(x − g(y)w)`, PRIOR_ART §4.6) reaches
  higher-order statistics and is **explicitly not covered** by this result.
- **n=16 fresh seeds, ONE wave model, ONE grid size.** Our waves implement **no
  directional bias at all** (Ge 2021's temporal→nasal drift, PRIOR_ART §4.4), so
  nothing here generalises to real Stage II waves.
- The **64×64 / 200-step** choice is a choice, not a derivation (§2.1). The 128²
  descriptive agrees, but two sizes is not a scaling law.

## 10. §9 — NOTHING CHANGED

No seed edited, no Rust added, no default moved, no constant introduced into any
mechanism. New files only: `scripts/waveiso_{lib,calibrate,pilot,confirm}.py`,
`VISION_WAVEISO_PREREG.md`, this file, and `results/waveiso_*.json`.

**Bench (`scripts/rung7_vision_bench.sh`), quoted WITH its condition per §10.2:**
**200 passed / 0 failed / 0 skipped in 131.79s**, at engine `74fc035c8595`, base
`d9300ccc`, **`data/` SYMLINKED from canonical**. That is the **`200/0` WITH
`data/`** arm — it matches §10.2's recorded prediction exactly, and confirms it
independently: without `data/` this bench reports `190 passed / 10 skipped`, and
**those 10 have never run in any worktree** (`pytest.skip("BSDS300 corpus
absent")`). **A worktree that does not symlink `data/` is measuring a 5%-vacuous
gate and does not know it.**

Also verified by diff rather than by inspection (§12.3 — a claim pinned to its
own commit range, not to a mutable tree):
`git diff d9300ccc..HEAD -- runners/dsl/src runners/dsl/Cargo.toml` is **EMPTY**
(no Rust), and `git diff d9300ccc..HEAD -- seeds/ domains/ substrate/` is
**EMPTY** (no seed, no adapter). This rung's entire diff is new `scripts/waveiso_*`
files, its own two documents, and **one ledger line** in `VISION_PROTOCOL.md`.

## 11. FOR THE SUPERVISOR — three things, none of them mine to fix

1. **The isotropy premise is CONFIRMED but its INFERENCE is not.** Rungs 8C/8E's
   *"the input carries no orientation"* should be corrected to *"the input's
   SECOND-ORDER ENSEMBLE STATISTICS carry no orientation; the input itself does,
   per-wavefront."* The negatives all still stand — the diagnosis changes.
2. **We are not model AL; we are below model L** (§6.1). The `lateral` name spans
   two different layers (retina vs V1) and that collision is load-bearing in at
   least two committed documents.
3. **The next lever is named by the data, not by me:** a mechanism that acts
   **within a pattern, before averaging** — GCAL's settling bubble (16 steps,
   γE=1.7/γI=−1.4) or a **nonlinear** Hebbian rule (§4.6, *"a one-line change to
   `vg_learn_kernel_oja`"*). **Both are untested here.** Note §13's warning
   against importing GCAL's CONSTANTS: γE/γI fell out of GCAL's frame, not ours.
