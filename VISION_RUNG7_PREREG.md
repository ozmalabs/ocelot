# RUNG 7 — RETINAL LATERAL INHIBITION (centre-surround EMERGES): pre-registration

*Binding order (PROTOCOL): convergence → calibrate the measure + positive control →
pre-register and COMMIT → ONE confirmatory run → append the outcome verbatim.*

**Everything above the OUTCOME line was written and committed BEFORE the confirmatory run.**

**ENGINE (PROTOCOL §10):** `engine 95167c01b7b3 @
/home/matt/ozma/internal/research/experiments/gamma-substrate/runners/dsl/python/substrate_rs/_native.abi3.so`,
`ambiguous: False`, exactly ONE artifact resolvable.
**COMMIT:** recorded in the OUTCOME.
**RUST:** rung 7 adds **no Rust**. Every compiled `.rs` in this worktree is byte-identical
to the canonical tree's (manifest md5 `7fce72365e7a7351cc2d56e4852ea20d` both sides; the
only tree difference is an untracked `py.rs.selfmod.bak`, which `rustc` never compiles), so
the canonical binary IS the correct binary for this source. **This was verified, not
assumed** — see §0.3.

---

## The rung, and why it exists

Rung 6 built the signed simple layer, removed rung 5's blocker (ideal split cell OSI
**0.9115** through the identical probe on which rung 5's units scored 0.004) — and then
**waves developed nothing**. Its diagnosis was structural:

> `x_OFF = 1 − x_ON` is **itself degenerate** — it determines OFF exactly, so
> `C_ON,OFF(d) = −C_ON,ON(d)` **identically**, and the channels carry **no independent
> correlation structure**. **Miller 1994** gets ON/OFF segregation from correlations with
> *different spatial dependence*. The ON/OFF sign is **necessary but not sufficient**.

**Rung 7 gives the channels independent correlation structure by GROWING centre-surround**
— retinal lateral inhibition as a RULE over the `neighbour` edges rung 1 declared and left
unused (`wv_propagate` was their sole consumer across every seed in the tree).

**The bolt-on error, rejected explicitly (PROTOCOL §0).** `substrate_rs/vision.py`'s
`lgn_pair`/`dog` are hand-designed numpy DoG kernels (`origin="dog"`) whose output is
already *signed* — they would assume away the exact thing rung 5 measured and break Dale
rather than model it. Rung 6 rejected them; so does this rung. **Centre-surround must FALL
OUT of lateral inhibition.**

**The mechanism** (`seeds/vision_lateral.json`, `lateral=0` default; adapter
`domains/lateral_world.py`; emitter `tools/build_vision_lateral_seed.py`):

| rule | what it does |
|---|---|
| `lat_pool` | `h1`,`h2` = mean burst over the RetinaCell's radius-1 / radius-2 rings |
| `lat_residual` | `resid = c − g1·h1 − g2·h2` — **predict the centre from the surround, transmit the residual** |
| `lat_bipolar` | `x_ON = [resid]+`, `x_OFF = [−resid]+` — two NON-NEGATIVE channels, signed difference |
| `lat_learn_gain` | `dg_k = eta·resid·h_k`, clipped `[0, gmax]` — **anti-Hebbian decorrelation** |

**THIS CLOSES THE ARC'S OLDEST LOOP.** Centre-surround IS predictive coding / redundancy
reduction (Srinivasan, Laughlin & Dubs 1982: *the surround is the optimal linear predictor
of the centre, subtracted; the output is the residual*) — the substrate's own
`prediction_minus_observation` shape, in the first synapse, which
`seeds/vision_floor.json`'s `vf_predictive_suppression` already encodes.

**Why the gain is LEARNED and not hand-set — the load-bearing choice.** `lat_learn_gain`'s
fixed point is `E[resid·h_k] = 0` ∀k: **the normal equations**, i.e. Srinivasan's optimal
linear predictor, DERIVED rather than received. VISION_PRIOR_ART.md is blunt that σ ratios
and τ values are *"hand-set constant[s] with no derivation — do not claim those emerge."*
A learned regression coefficient must also **shrink as the surround becomes a worse
predictor**, which is Atick & Redlich's falsifiable prediction (H3). **A hand-set gain
cannot make that prediction; a learned one can fail it.** That asymmetry is the evidential
point.

**Dale.** `g1,g2 ≥ 0` always (clipped). The horizontal cell is a **sign-constant inhibitory
pathway** whose MAGNITUDE is learned — never a weight that may change sign.

**Ablations are DATA** (PROTOCOL §0): `learn_gain=0` pins `g` (fixed-gain control);
`radius2=0` pins `g2=0` **with the anatomy standing** (rung 4's lesson); `frozen=1` is a
real freeze; `lateral=0` (default) makes the layer inert. A gate parses
`domains/lateral_world.py` with `ast` and fails if any `if`/`while` **test** mentions an
ablation flag — checking CODE, not prose (a plain grep fired on this module's own
docstring; a gate a comment can trip is a gate that gets silenced by rewording).

**The anatomy the adapter states, and why it is not the answer in disguise.** The adapter
wires `neighbour2` (the radius-2 ring) exactly as `WaveWorld` already wires `neighbour`:
*"mechanical geometry (the grid's own adjacency)… WHAT travels along it, and whether
anything does, is the rules' business."* It states WHICH cells touch — never that the
surround inhibits, nor how strongly. **`lat_g0 = 0.0`: the layer starts as a PURE CENTRE
with no surround at all**, and the profile is grown.

---

## 0. HYGIENE FINDINGS FROM THE ADVERSARIAL REVIEW, ANSWERED WITH MEASUREMENTS

### 0.1 The `w0` DC prior (`VISION_FABLE_REVIEW.md`) — **does not touch rung 7, verified**

The review measured `wave_world.add_units(w0=1.0, jitter=0.05)` as a **494:1 DC prior**
(DC power fraction 0.99798, `frac(w<0)=0.0000`) present *before any rule fires*, and asked
every rung to run the `w0 = 1.0 → 0.0` ablation.

**Run (`scripts/rung7_init_audit.py`), structurally and empirically:**

```
Unit nodes minted by rung 7    : 0        Synapse nodes : 0      SUnit nodes : 0
rung7_lib / lateral_world call add_units : False    mention w0 : False

RUNG 7'S LEARNED PARAMETER AT INIT:  max|g| = 0.000000   frac(g != 0) = 0.000000

THE REQUESTED ABLATION, rung-7 headline numbers (seed 3000, 3200 steps):
  w0=1.0 :  CS=0.986423   SD=0.474023   g1=0.528137  g2=0.458286
  w0=0.0 :  CS=0.986423   SD=0.474023   g1=0.528137  g2=0.458286
  max |diff| :  CS 0.000e+00   SD 0.000e+00   gains 0.000e+00
```

**BYTE-IDENTICAL.** Rung 7 mints no `Unit`, never calls `add_units`, and never reads a Unit
weight. **Its learned parameter (`g1`,`g2`) initialises at EXACTLY 0.0** — so the critique
is not merely inapplicable here, it is **inverted: rung 7 already uses the zero init the
review asks for**, and `test_the_seed_ships_inert_so_every_committed_result_reproduces`
gates `lat_g0 == 0.0` so it cannot regress. **Every rung-7 number below is init-free: the
surround is grown from nothing.**

This says nothing about rungs 2/4/5/6, whose numbers DO come from `add_units`. That audit
is theirs, not this document's.

### 0.2 `-k vision` IS NOT A DEFINITION — the seven-baselines cause, and the named selector

`pytest -k` substring-matches the **whole node ID**, so `-k vision` collects
`test_adoption.py`, `test_audio.py`, and `test_meaning_inference_migrated.py`'s
`..._infers_provisional_sense_...` tests — **pro-VISION-al**. 36 files, most unrelated to
vision. **That is a sufficient cause for one suite reporting several different
"baselines"**, and it is why this rung reports against an **EXPLICIT FILE LIST**:
`scripts/rung7_vision_bench.sh` (16 named files).

**RUNG 7's NAMED BASELINE: `163 passed, 1 skipped, 0 failed`** (includes rung 7's own 18
gates). Recorded with its engine hash and commit in the OUTCOME.

Two honest notes: (a) the 1 skip is `test_vision_growth_migrated`'s BSDS300 corpus, which
is untracked data absent from a fresh worktree — symlinked read-only here, and its skip
guard crashes before it can fire because `preprocess_patches` reshapes an empty array
first; **not rung 7's file to fix, reported not touched**; (b) two
`test_meaning_inference_migrated` tests fail on this branch and are **pre-existing and
non-vision** — they were failing before rung 7 made any edit, and the named selector
excludes them by construction rather than by convenience.

### 0.3 §10 vs §11 — the worktree/engine contradiction, verified benign HERE

The review is right that `site-packages/substrate_rs.pth` is an **absolute path into the
canonical tree**, so a worktree imports *another tree's* binary. Checked rather than
trusted:

- this worktree had **no** `_native.abi3.so` (a build artifact, untracked), so the import
  failed outright rather than silently resolving;
- fixed with a **symlink** to the canonical artifact — *a pointer, not a copy* (§10's own
  principle: "a copy goes stale; a pointer cannot"). `resolvable_natives()` dedups by
  `realpath`, so exactly ONE artifact resolves and `ambiguous` is `False`;
- **no global state was mutated** (§11.2): no `.pth` edit, no pip/maturin into the shared
  env;
- and the binary is *correct for this source*: every compiled `.rs` is byte-identical
  across both trees (md5 `7fce72365e7a7351cc2d56e4852ea20d`).

**The general contradiction stands and is the supervisor's to sequence.** It is benign for
rung 7 **only because rung 7 changes no Rust** — a rung that did would silently measure the
canonical tree's binary against its own source. That is a live trap for the next rung.

---

## 1. THE MEASURES, AND THEIR CALIBRATION (PROTOCOL §1)

### THE REAL GATE — `SD`, the SHAPE departure

```
rho = Pearson correlation, across d = 1..6, of C_ON,OFF(d) vs C_ON,ON(d)
SD  = 1 - rho^2
```

**Why not "is `C_ON,OFF(d) ≠ −C_ON,ON(d)`?"** Because that would be passed by **any**
non-affine relation between the channels — including a pure pointwise rectification change
with **no spatial structure whatever**. Miller needs the correlation functions to have
**DIFFERENT SPATIAL DEPENDENCE**. `SD` is therefore **scale- and sign-invariant by
construction**: it is the fraction of the ON/OFF correlation function's spatial variation
NOT explained by *any* affine image of the ON/ON one. A sign flip cannot pass it; a
rescaling cannot pass it.

**`d = 0` is EXCLUDED, and that is load-bearing.** At zero distance the channels are the
two rectified halves of ONE residual, so `Corr(x_ON(i), x_OFF(i))` is driven by the
rectification nonlinearity alone and carries no spatial information. Including it would let
a pointwise nonlinearity pass a test about space.

**THE FLOOR IS ANALYTIC, NOT EMPIRICAL** — the strongest floor this ladder has had.
`x_OFF = 1 − x_ON` is affine with negative slope ⇒ `rho = −1` ⇒ **SD = 0 exactly**.
Measured through the actual instrument on the actual waves (seed 0, 300 steps):

```
C_ON,ON(d)  [ 0.4396  0.1339  0.0884  0.0616  0.0205  0.0209]
C_ON,OFF(d) [-0.4396 -0.1339 -0.0884 -0.0616 -0.0205 -0.0209]
sum          [ 0.      0.      0.      0.      0.      0.    ]     <- identically zero
SD = 0.0000        sigma_ON,ON = sigma_ON,OFF = 1.719              <- identical
```

**Rung 6's diagnosis, reproduced exactly by an independent instrument.** Gated by
`test_THE_ANALYTIC_FLOOR_the_rung6_split_scores_exactly_zero`.

**`SD` is UNDEFINED (`nan`), not 0, when the OFF channel does not exist** (`g=0` ⇒
`resid = c ≥ 0` ⇒ OFF silent ⇒ zero variance ⇒ no correlation function). Reporting 0 there
would read as "maximally degenerate" when the truth is "there is no second channel to be
degenerate WITH". Gated.

### THE CALIBRATION TABLE (`scripts/rung7_poscontrol.py`, frozen probe, through the graph)

| reference | **SD** | σ_ON,ON | σ_ON,OFF | OFF mean |
|---|---|---|---|---|
| **rung-6 complementary split** = **THE FLOOR** | **0.0000** | 1.705 | 1.705 | 0.864 |
| pure centre (`g=0`) — no surround at all | **nan** (OFF dead) | 2.350 | — | 0.000 |
| weak surround (`g1=g2=0.25`) | 0.8703 | 2.319 | 5.593 | 0.039 |
| **BALANCED DoG (`g1=g2=0.5`, DC-cancelling)** = **THE TARGET** | **0.4719** | 1.781 | 4.379 | 0.079 |
| strong surround (`g1=g2=0.75`) | 0.8012 | 1.701 | 2.557 | 0.160 |
| near-only (`g1=1.0, g2=0`) | 0.6185 | 1.547 | 1.825 | 0.066 |

**THE MEASURE IS NOT A NULL INSTRUMENT:** every hand-installed surround moves `SD` far off
its analytic floor.

**Stated honestly in advance: `SD` is NON-MONOTONE in surround strength** (0.87 weak, 0.47
balanced, 0.80 strong). It is a **degeneracy-break** statistic, *not* a
surround-strength statistic, and is never interpreted as one. The **balanced DoG (0.4719)**
is the target because it is the textbook DC-cancelling centre-surround and the reference the
learned system actually approaches (`CS → ~1.07 ≈ balanced`). Because of the
non-monotonicity, **`SD` above the target is NOT "better than ideal"** and will not be
reported as such.

### SESOI — stated in advance

**10% of the measure's dynamic range**, matching rungs 3/5/6.

- **`SD`**: floor 0.0000 → target 0.4719 ⇒ **SESOI = 0.0472**.
- **`CS`**: floor 0.0 (pure centre, analytic) → target 1.0 (balanced DoG) ⇒ **SESOI = 0.1**.

### `CS` — the centre-surround index, and why it reads the FILTER

A single lit pixel at offset (dr,dc); response read off the **residual** — the signed
FILTER. Rung 6 established that the filter and the rectified RESPONSE are different objects
(OSI 0.0006 vs 0.9115 on identical weights) and that the RF is a property of the filter.
The rectified **surround suppression** is reported alongside, since that is what a
downstream cell actually receives.

Because each `h_k` is a **mean** over its ring, a lit pixel in ring k contributes `−g_k/n_k`
and the ring sums to `−g_k`, so **`CS = −Σsurround/centre = g1 + g2`**: the index IS the
total learned surround gain, and pure centre scores 0 *by construction*. Verified against
hand-installed references:

```
pure centre (g=0)         CS = -0.0000  (expect 0.00)   surround_suppression = 0.0000
BALANCED DoG (g1=g2=0.5)  CS =  1.0000  (expect 1.00)   surround_suppression = 0.5000
strong       (g1=g2=0.75) CS =  1.5000  (expect 1.50)   surround_suppression = 0.7500

effective RF (residual field), balanced DoG:
   +0.000 +0.000 -0.062 +0.000 +0.000
   +0.000 -0.062 -0.125 -0.062 +0.000
   -0.062 -0.125 +1.000 -0.125 -0.062      <- a centre-surround, read out of the graph
   +0.000 -0.062 -0.125 -0.062 +0.000
   +0.000 +0.000 -0.062 +0.000 +0.000
```

### DURATION (PROTOCOL §1's third check)

`CS` **is** duration-dependent by design: it grows 0 → ~1.07 over training, from an
`lat_g0 = 0.0` init. **That is the SIGNAL, not a confound** — the rung's claim is precisely
that the surround is GROWN. This is the opposite of the anisotropy failure, where a score
changing with duration on the *same* input meant the measure was reading the clock. Here the
duration-dependence is the hypothesis, the init is zero, the endpoint is a **fixed point**
(§2), and the fixed point is compared to an **analytic** target (`g1+g2 = 1`), not to
"more than nothing".

---

## 2. CONVERGENCE (PROTOCOL §2) — **RUN FIRST; THE GATE PASSES**

*"Before any experience/ablation arm is run, measure: does the rule settle?"*

Formative input ONLY (the agent's own waves), seed 3000, **FIXED** drift window of 1600
(the first pass used doubling checkpoints, making `drift` a moving target — corrected).

| step | g1 | g2 | CS | **drift** | SD | σ_nn | σ_nf | ratio | ON | OFF | NaN |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1600 | 0.4086 | 0.3556 | 0.7642 | 1.0000 | 0.7088 | 2.048 | 4.856 | 2.371 | 0.135 | 0.065 | 0 |
| 3200 | 0.5293 | 0.4585 | 0.9878 | 0.2275 | 0.4692 | 1.768 | 4.136 | 2.340 | 0.089 | 0.086 | 0 |
| 4800 | 0.5642 | 0.4863 | 1.0505 | 0.0627 | 0.3763 | 1.675 | 3.655 | 2.183 | 0.071 | 0.085 | 0 |
| 6400 | 0.5746 | 0.4937 | 1.0683 | 0.0231 | 0.3589 | 1.638 | 3.434 | 2.097 | 0.069 | 0.088 | 0 |
| 9600 | 0.5797 | 0.4970 | 1.0767 | 0.0136 | 0.3965 | 1.617 | 3.260 | 2.016 | 0.067 | 0.089 | 0 |
| 12800 | 0.5804 | 0.4950 | 1.0755 | 0.0116 | 0.3163 | 1.659 | 3.521 | 2.122 | 0.066 | 0.087 | 0 |
| 19200 | 0.5817 | 0.4950 | 1.0767 | 0.0096 | 0.3974 | 1.566 | 3.178 | 2.029 | 0.078 | 0.103 | 0 |
| **25600** | **0.5831** | **0.4952** | **1.0783** | **0.0081** | **0.3375** | **1.628** | **3.193** | **1.962** | 0.066 | 0.088 | 0 |

**CONVERGENT + USEFUL — both of PROTOCOL §2's stop conditions are CLEARED:**

1. **Drift → 0**, monotonically, on a fixed window: 1.0 → **0.0081**. Not a runaway (rung
   6's η=5e-4 went 0.004 → 0.461).
2. **It plateaus at NON-ZERO structure**: `CS` settles at **1.078** — within 8% of the
   analytic DC-cancelling balance of 1.0 — and `SD` plateaus at **~0.32–0.44**, far above
   its analytic floor of 0. Not "converges to death" (rung 6's η=1e-4 sat on its floor).
3. **0 NaN** everywhere.
4. Both channels are alive and roughly balanced (ON 0.066 / OFF 0.088).

`SD`'s residual jitter (0.32–0.44) is measurement noise from the 300-step read-out window,
not drift: the gains are settled to 4 decimals from ~9600 on.

**This is the first rung since rung 4 to clear the convergence gate, and it is why arms may
be run at all.** η is **frozen at 2e-3** by this table; it is not an axis.

---

## 3. POSITIVE CONTROL (PROTOCOL §1) — the rule is **NOT** a null instrument

Asked separately from the hypothesis. *Given input where the surround is a PERFECT
predictor of the centre (the whole retina co-bursts), does the rule find the analytic
optimum?* The fixed point is derivable: `resid = 0 ⟺ g1 + g2 = 1`.

```
eta=2e-3    g1=0.4988  g2=0.4988   TOTAL = 0.9976   (target 1.0)   residual 0.0024
eta=5e-4    g1=0.3885  g2=0.3885   TOTAL = 0.7770   (target 1.0)   residual 0.2230
```

**THE POSITIVE CONTROL PASSES** at the frozen η: the rule drives the surround to within
**0.24%** of the analytic optimum and stops, because the residual it feeds on has been
explained away. **That is redundancy reduction, scored against a derived number rather than
against "more than nothing".** (η=5e-4 merely undershoots at 1500 steps — consistent with
the convergence table, and not an argument for a sweep.)

**Rules fire, verified** (rung 6's `oo_learn_oja` silently never fired and read as a
result): `max|dg| = 0.0785` over 200 steps, **100%** of gains moved.
**The freeze is exact**: `max|dg| = 0.000e+00` across a full probe.
**`lateral=0` is completely inert**: `max|dg| = 0.000e+00`, both channels silent.

---

## 4. THE PRE-REGISTERED CONFIRMATORY RUN

### Seeds — FRESH, never used for anything (ledger appended)

- **9000–9007** (n=8): H1, H2, H2b — the agent's own waves.
- **9100–9107** (n=8): H3a, H3b — the SNR arms.

All calibration, convergence, positive-control and pilot work above used **burned** seeds
(0, 1, 2, 3000) only.

### n, FIXED IN ADVANCE by a pilot on BURNED seeds (0,1,2)

```
SD  mean 0.3566  sd 0.0341   -> Cohen d vs SESOI 0.0472 = 9.08
CS  mean 1.0686  sd ~3e-5    -> effectively DETERMINISTIC across seeds
sigma ratio mean 2.118
SNR (balanced): total 0.7594 -> 0.6261 (sd ~0.006);  share 0.3402 -> 0.3950 (sd ~0.004)
```

**n = 8** per block ⇒ power > 0.999 for every test below. **Unit of analysis is the SEED**
(PROTOCOL §4), never the cell: the 256 HCells in one run share a wave field and are not
independent.

### THE HYPOTHESES — two-sided, exactly these five inferential tests, no others

| # | hypothesis | statistic | test |
|---|---|---|---|
| **H1** | **THE REAL GATE.** The agent's own waves grow a surround that breaks the ON/OFF degeneracy | `SD` at 6400 steps | one-sample t vs **SESOI 0.0472**, two-sided |
| **H2** | Centre-surround EMERGES from a zero init | `CS = g1+g2` | one-sample t vs **SESOI 0.1**, two-sided |
| **H2b** | **Miller's own reading:** the channels have DIFFERENT spatial dependence | `σ_ON,OFF` vs `σ_ON,ON` | paired t, two-sided |
| **H3a** | **Atick & Redlich WEAKENS:** the surround weakens as SNR falls | total gain, `p=0` vs `p=0.20` | paired t, two-sided |
| **H3b** | **Atick & Redlich BROADENS:** the surround broadens as SNR falls | `g2/(g1+g2)`, `p=0` vs `p=0.20` | paired t, two-sided |

**Bonferroni: α = 0.05/5 = 0.01.** 95% CIs reported for every estimate.

**Plus ONE analytic check (not a hypothesis test):** the rung-6 complementary split on the
SAME seeds' burst movies must score `SD = 0` to numerical precision. If it does not, the
instrument is broken and the run is void.

### A PRE-REGISTERED DEVIATION, declared BEFORE the run (and why it is not a loophole)

The pilot measured `CS`'s between-seed sd at **~3e-5**: the fixed point `g*` is a
**population statistic of the wave ensemble** and is essentially seed-independent. A t-test
on ~1e-5 variance returns a p-value of ~1e-30 that means **nothing** — it measures the
determinism of the rule, not the reliability of the effect. **So for H2 I pre-register:
report the per-seed values, the exact range, and the comparison to the analytic floor and
SESOI; report the t only if between-seed sd > 1e-3, and otherwise state plainly that the
result is deterministic and the p-value uninterpretable.** Declaring this in advance is the
point: discovering it afterwards and choosing a statistic would be the forking path.

### THE ATICK & REDLICH INSTRUMENT — and a negative already measured

**The control is exact**: `replay_noisy` replays **ONE pre-recorded wave movie** at every
noise level, so the stimulus is byte-identical across arms and only SNR moves — *"the same
video at two luminances"*, literally, not by analogy.

**Noise is `balanced` (density-preserving)**: an ON cell turns OFF with prob `p`, an OFF
cell turns ON with prob `p·m/(1−m)`, so `E[mean(f')] = mean(f)` exactly.

**THE NAIVE INSTRUMENT FAILED, AND THE FAILURE IS RECORDED RATHER THAN DELETED.** A
symmetric flip at rate `p` is **not** a pure SNR knob on a sparse binary field: it moves
mean activity from `m` to `m + p(1−2m)` (0.13 → 0.28 at p=0.2), varying **density and SNR
together** — two mechanisms on one knob (PROTOCOL §4). Measured on burned seeds, it
reproduced BROADENING monotonically (share 0.340 → 0.490) while **inverting** the predicted
WEAKENING (total 0.759 → **0.797**). **The failure was the instrument's, not the
mechanism's**, it was found in the pilot before any hypothesis was gated (which is what
pilots are for), and both noise models are kept in `_corrupt_frame` with the negative
recorded in its docstring.

**Two bugs of my own, found and fixed before gating** (both are PROTOCOL §4's "adding a
mechanism can silently invalidate your control"):
1. The first SNR cut corrupted the field *after* `world.step()` had already run the rules to
   fixpoint on the CLEAN field; clearing the phase guards to re-run made `lat_learn_gain`
   fire **twice per step**. The arms would have differed in *number of learning events* as
   well as SNR. Fixed by setting the field once, then ticking once.
2. The `ast` gate above replaced a substring grep that fired on its own docstring.

### DECISION RULE, including what a null means

- **H1 passes** iff `SD` mean > SESOI **and** p < 0.01. A null on H1 means lateral
  inhibition does **not** give the channels independent correlation structure ⇒ rung 6's
  named next hypothesis is **refuted**, the ladder's ON/OFF-segregation route needs a
  different mechanism, and I say so.
- **H2 passes** iff `CS` > SESOI (per the declared deviation). A null means the surround did
  not grow ⇒ "centre-surround emerges" is **not built**.
- **H2b** null ⇒ `SD > 0` would be structure Miller's mechanism *cannot* use, and H1's pass
  would be **downgraded to a statistic without a mechanism**. H1 and H2b are read
  **conjunctively** (PROTOCOL §4: a mechanism must not pass by making itself inert).
- **H3a/H3b** are **independent of H1/H2**: they can fail while the degeneracy still breaks.
  A null on **both** means the surround is not behaving as a predictor and the "it's
  predictive coding" reading is **withdrawn** — the mechanism would be *a* subtraction that
  happens to decorrelate, not Srinivasan's predictor. **A split (one passes, one fails)
  is reported as a split**, as the naive-noise pilot already was.
- **No re-runs. No sweeps.** η, `gmax`, `lat_g0`, the rings, the probe and `DMAX` are
  **frozen**. A further attempt needs a NEW pre-registration with a NEW mechanism-level
  hypothesis.

### MY PREDICTION, STATED IN ADVANCE, WITH ITS PROVISOS

**H1 PASS** (`SD ≈ 0.36`, ~76% of the floor→target range), **H2 PASS** (`CS ≈ 1.07`),
**H2b PASS** (σ ratio ≈ 2.1), **H3a PASS**, **H3b PASS**. The pilot on burned seeds
supports all five, and the confirmatory run's only new information is fresh seeds — which,
given `CS`'s ~3e-5 between-seed variance, I expect to change nothing.

**The provisos — what would break, and what each would teach:**

1. **H1's mechanism is NOT learning, and I state it before the run.** The calibration table
   shows a **hand-installed fixed surround breaks the degeneracy just as well** (SD 0.47–0.87).
   So **the break is a property of the SUBTRACTION (lateral inhibition), not of learning
   it.** What learning earns is (a) the gain is DERIVED not hand-set and (b) H3.
   `test_NOT_CLAIMED_the_degeneracy_break_is_not_caused_by_LEARNING` pins this in code.
   **Anyone reading rung 7 as "learning breaks the degeneracy" is reading it wrong.**
2. **`SD`'s non-monotonicity means a HIGH `SD` is not a good `SD`.** If the confirmatory
   `SD` lands near 0.87 rather than 0.47 I will **not** call that a stronger result — it
   would indicate a *weak* surround, and the honest reading would be that the ladder should
   watch `CS`.
3. **`CS ≈ 1.07` slightly EXCEEDS the balanced DoG's 1.0.** I predict this replicates, and
   it is **not** "better than ideal": it means the learned predictor slightly over-subtracts
   relative to a DC-cancelling DoG, which is what an unconstrained regression on a sparse,
   spatially-correlated field should do. If it instead lands *below* 1.0 my model of the
   fixed point is wrong.
4. **The largest thing I could be wrong about is that H3 is easier than Atick & Redlich's
   real test.** Their prediction concerns the surround's *spatial profile* fitted from
   responses; mine reads two learned scalars off the graph, and the "broadening" axis has
   exactly **two** rings — a very coarse width. If H3b passes, it shows the *direction* the
   theory predicts, **not** that the fitted spatial profile matches their closed form. I
   will not claim the latter.
5. **`SD` is a diagnostic of my own construction, not a field-standard statistic.** Its
   analytic floor is what makes it trustworthy; that it is novel is a reason for scope
   discipline, which is why **H2b (Miller's own space-constant reading) is gated
   conjunctively** rather than reported as a nicety.
6. **If waves' correlation length and the rings are mismatched, H2b could pass trivially.**
   σ_nn ≈ 1.6 and the rings are at d=1 and d=2, so the surround operates *inside* the wave's
   correlation length — which is why the predictor has anything to learn. A retina whose
   waves were much smoother would make this rung vacuous, and that is a scope limit on the
   claim, not a result.

### WHAT THIS RUNG CANNOT CLAIM, WHATEVER THE OUTCOME (PROTOCOL §8)

- **NOT that orientation selectivity develops.** Rung 7 mints **no SUnit and no cortical
  Unit** (gated). It is a claim about the **retina's output statistics** and nothing else.
  Whether these channels let a cortical cell develop orientation is the **next** rung's
  question — rung 7 supplies Miller's *precondition*, and a precondition is not a result.
- **NOT that centre-surround IS whitening.** VISION_PRIOR_ART.md's scepticism is respected:
  the direct test (PMC1575921) concludes it is **not** — whitening yields the `|f|` ramp,
  not a DoG; you need **three** constraints (decorrelation + response equalisation + a
  size/sparseness constraint). **Rung 7 claims DECORRELATION ONLY**, one of the three.
- **NOT that the DoG's shape is derived.** The *profile* here has exactly two free scalars
  on two hand-wired rings. That the ratio `g1:g2 ≈ 1.18:1` resembles a DoG is **not** a
  derivation of a DoG.
- **NOT rungs 5/6's retraction.** Their measurements stand; rung 7 addresses the diagnosis
  rung 6 *named*, and does not revisit its numbers.
- **NOT anything about `w0`'s effect on other rungs.** §0.1 shows only that rung 7 is immune.
- **NOT that the wave model is right.** VISION_PRIOR_ART.md §3.4: the fixed refractory
  period is the toy part; Godfrey & Swindale use no stochastic ignition at all.

---

# OUTCOME / DECISION

**ONE run, executed at commit `7ec2769d41` (this document's pre-registration commit),
engine `95167c01b7b3`, `ambiguous: False`. No sweeps, no re-runs.** Raw log:
`results/rung7_confirm.log`.

# **DECISION: RUNG 7 is *** BUILT ***.**

## The confirmatory run, verbatim

```
  seed       SD       CS   sig_nn   sig_nf   ratio  SD_rung6ref    supp
  9000   0.3530   1.0847    1.642    3.211   1.956     0.00e+00  0.5735
  9001   0.4017   1.0917    1.627    3.503   2.153     4.44e-16  0.5717
  9002   0.3472   1.0812    1.616    3.079   1.905     0.00e+00  0.5722
  9003   0.3623   1.0808    1.621    3.417   2.108     0.00e+00  0.5717
  9004   0.3456   1.0873    1.639    3.358   2.048     0.00e+00  0.5714
  9005   0.3343   1.0812    1.629    3.064   1.881     0.00e+00  0.5731
  9006   0.4206   1.0786    1.588    3.241   2.042     0.00e+00  0.5708
  9007   0.3162   1.0857    1.652    3.240   1.961     4.44e-16  0.5683

ANALYTIC CHECK — rung-6 complementary split must score SD = 0
  max |SD_ref| across 8 seeds = 4.441e-16   => PASS (instrument sound)

H1  SD mean 0.3601  95% CI [0.3311, 0.3891]  sd 0.0347
    vs SESOI 0.0472:  t=25.527  p=3.617e-08   PASS        (76.3% of range)
H2  CS mean 1.083918  range [1.078611, 1.091738]  sd 4.294e-03
    vs SESOI 0.1: t=648.082 p=5.500e-18       PASS        (108.4% of range)
    surround suppression (RESPONSE side): mean 0.5716
H2b sigma_ON,ON 1.627   sigma_ON,OFF 3.264   ratio 2.007
    diff 1.637  95% CI [1.508, 1.767]  t=29.944  p=1.194e-08   PASS
H3a p=0 0.7748 -> p=0.20 0.6447   diff -0.1301  95% CI [-0.1311, -0.1291]
    t=-298.906  p=1.239e-15   PASS (weakens, as predicted)
H3b p=0 0.3332 -> p=0.20 0.3932   diff +0.0600  95% CI [+0.0582, +0.0618]
    t=78.708  p=1.406e-11   PASS (broadens, as predicted)
```

**Named bench** (`scripts/rung7_vision_bench.sh`, 16 explicit files):
**163 passed, 1 skipped, 0 failed**, including rung 7's 18 gates.

## What IS established (measured, gated, reproducible)

1. **THE REAL GATE PASSES — THE DEGENERACY BREAKS.** `SD = 0.3601` [0.3311, 0.3891],
   **76.3%** of the floor→target range, against a floor the *same instrument* returns as
   **4.441e-16** on rung 6's split on these same seeds' own waves. `C_ON,OFF(d)` is no
   longer an affine image of `C_ON,ON(d)`. **Miller 1994's precondition — the thing rung 6
   named as missing — now holds.**
2. **MILLER'S OWN READING AGREES (H2b).** The channels have genuinely **different spatial
   dependence**: `σ_ON,ON = 1.627` vs `σ_ON,OFF = 3.264`, **ratio 2.007**, diff 1.637
   [1.508, 1.767]. This is the conjunctive check that stops H1 being a statistic without a
   mechanism, and it passes.
3. **CENTRE-SURROUND EMERGES FROM A ZERO INIT.** `CS = 1.0839` [1.0786, 1.0917] from
   `lat_g0 = 0.0` — a layer that begins as a **pure centre with no surround at all** grows a
   balanced centre-surround, **108.4%** of the analytic DC-cancelling target of 1.0, and the
   effective RF reads out as a textbook DoG (`+1.000` centre, `−0.125` ring-1, `−0.062`
   ring-2). The response-side surround suppression is **0.5716**. **No DoG kernel was ever
   handed over** — `substrate_rs/vision.py::lgn_pair` stays rejected.
4. **ATICK & REDLICH'S FALSIFIABLE PREDICTION IS CONFIRMED — BOTH HALVES.** On **the same
   movie replayed at two luminances**: the surround **WEAKENS** (total gain 0.7748 →
   0.6447, −0.1301 [−0.1311, −0.1291]) and **BROADENS** (far-ring share 0.3332 → 0.3932,
   +0.0600 [+0.0582, +0.0618]). VISION_PRIOR_ART.md nominated this as one of only two
   mechanisms in the whole survey with a **noise-free control** — *"a bare grid + drift
   cannot accidentally pass this"* — and **a hand-set gain cannot pass it by construction.**
   This is the rung's strongest evidence that the mechanism is **doing predictive coding
   rather than imitating a DoG**: the surround is a **regression coefficient**, and it moves
   the way a regression coefficient must when its regressor gets noisier.
5. **THE ARC'S OLDEST LOOP IS CLOSED.** Whitening/decorrelation is now an **output** of the
   substrate's own `prediction_minus_observation` motion (Srinivasan/Laughlin/Dubs 1982),
   grown by a rule whose fixed point is the normal equations — not a kernel we handed over.
   The positive control scored the rule against a **derived number**: 0.9976 vs an analytic
   optimum of 1.0.
6. **CONVERGENCE (the gate that stopped rungs 5 and 6) PASSES:** fixed-window drift
   1.0 → 0.0081 out to 25600 steps, plateau at non-zero structure, 0 NaN.
7. **RUNG 7 IS INIT-FREE** (§0.1): the `w0` DC prior the adversarial review measured is
   **byte-identical** (0.000e+00) on every rung-7 number, because rung 7 mints no `Unit` and
   its learned parameter starts at exactly 0.0.

## MY PREDICTION HELD — all five, including the provisos

Predicted in advance: H1 PASS (`SD ≈ 0.36`) → **0.3601**. H2 PASS (`CS ≈ 1.07`) →
**1.0839**. H2b PASS (ratio ≈ 2.1) → **2.007**. H3a PASS. H3b PASS.

**Proviso 3 held and is the informative one:** I predicted `CS` would land **above** the
balanced DoG's 1.0 and said in advance that this is **not** "better than ideal" — it means
the learned predictor **slightly over-subtracts** relative to a DC-cancelling DoG, which is
what an unconstrained regression on a sparse, spatially-correlated field should do. It did:
108.4%. Had it landed below 1.0, my model of the fixed point would have been wrong.

**Proviso 2 did not trigger:** `SD` landed at 0.36, near the balanced-DoG target (0.47),
not up in the weak-surround band (0.87) — consistent with `CS ≈ 1`.

**The declared H2 deviation did not fire:** between-seed sd was **4.294e-03**, above the
pre-registered 1e-3 threshold, so the t is reported as specified. It is still an absurd
number and is not the finding (below).

## WHAT IS **NOT** CLAIMED (PROTOCOL §8)

- **THE DEGENERACY BREAK IS NOT CAUSED BY LEARNING.** Stated before the run and confirmed by
  calibration: **a hand-installed FIXED surround breaks it just as well** (SD 0.47–0.87).
  The break is a property of **lateral inhibition — the subtraction — not of learning it.**
  What learning earns is exactly two things: the gain is **DERIVED** rather than hand-set,
  and **H3**, which a fixed gain cannot produce. Pinned in code by
  `test_NOT_CLAIMED_the_degeneracy_break_is_not_caused_by_LEARNING`. **Anyone reading rung 7
  as "learning breaks the degeneracy" is reading it wrong.**
- **THE p-VALUES ARE NOT THE FINDING.** `t = 648`, `p = 1e-15` are artifacts of a
  near-deterministic fixed point: `g*` is a **population statistic of the wave ensemble**, so
  all 8 seeds converge to nearly the same value (CS range 1.0786–1.0917). The story is
  **reproducibility and effect size**, not significance. A p-value on variance of ~4e-3 says
  the rule is deterministic, not that the effect is important.
- **NO ORIENTATION SELECTIVITY IS MEASURED, AND NONE IS IMPLIED.** Rung 7 mints **0 SUnit
  and 0 Unit** (gated). It is a claim about the **retina's output statistics** only. **A
  precondition is not a result:** whether these channels let a cortical cell develop
  orientation is the NEXT rung's question, and rung 6's negative is **not** thereby
  overturned.
- **NOT that centre-surround IS whitening.** VISION_PRIOR_ART.md's scepticism is respected:
  the direct test (PMC1575921) says it is **not** — whitening gives the `|f|` ramp, not a
  DoG; three constraints are needed (decorrelation + response equalisation +
  size/sparseness). **Rung 7 claims DECORRELATION ONLY** — one of the three.
- **NOT that the DoG's SHAPE is derived.** The profile has exactly **two free scalars on two
  hand-wired rings**. `g1:g2 ≈ 1.18:1` resembling a DoG is not a derivation of one.
- **NOT Atick & Redlich's closed form.** H3 shows the **direction** their theory predicts, on
  a width axis with exactly **two** rings — a very coarse profile. It does **not** show the
  fitted spatial profile matches `K_exp = M/√(M²(R+N²)+N₀²)`.
- **NOT that `SD` is a field-standard statistic.** It is a diagnostic of my own construction;
  its analytic floor is what makes it trustworthy, and that is why **H2b (Miller's own
  space-constant reading) was gated conjunctively** rather than offered as a nicety.
- **NOT that `SD` measures surround STRENGTH.** It is non-monotone in it (0.87 weak / 0.47
  balanced / 0.80 strong), stated in advance and never interpreted otherwise.
- **NOT a rescue of the wave model.** VISION_PRIOR_ART.md §3.4 stands: the fixed refractory
  period is the toy part.
- **NOT anything about `w0`'s effect on rungs 2/4/5/6.** §0.1 shows only that rung 7 is
  immune; those rungs' audit is theirs.
- **NOT a stability claim beyond 25600 steps**, and not at any other η (frozen at 2e-3).

## THE NAMED NEXT HYPOTHESIS (NOT run, NOT built here)

**Feed these channels to rung 6's SUnit layer and re-run rung 6's convergence gate.** Rung 6
failed because `x_OFF = 1 − x_ON` gave waves nothing to sculpt; rung 7 has now produced
channels with **independent correlation structure and space constants differing 2:1** —
which is precisely what Miller 1994's mechanism consumes. **That is the ladder's next rung
and it needs its own pre-registration.** Rung 7 establishes the precondition and deliberately
stops there: `vision_lateral` and `vision_onoff` are separate seeds and were never composed
in this run.

Two hygiene items this rung surfaced for the supervisor to sequence, neither fixable from
one worktree: (a) **§10/§11 still contradict** — the `.pth` is an absolute path into the
canonical tree, so any rung that **changes Rust** will silently measure the canonical
binary against its own source (benign here only because rung 7 adds none); (b)
**`test_vision_growth_migrated`'s skip guard crashes before it can fire** when the BSDS300
corpus is absent (it reshapes an empty array first), so a fresh worktree reports 5 errors
that are really 1 honest skip.

## POST-MERGE RECONCILIATION (appended, nothing above rewritten)

Merging `gamma-substrate/developmental-vision` after the run showed the branch had moved
under this rung (PROTOCOL §11.5 — *"long-running measurement is not a lock"*). Every number
above is unaffected: each carries its commit (`7ec2769d41`) and engine (`95167c01b7b3`),
which is exactly what §10 exists for.

- **Hygiene item (b) is ALREADY FIXED upstream** by `8720bc3abb`, independently and
  concurrently. **Both defects this rung reported in §0.2 were found by two agents in two
  worktrees from two directions** — the corpus guard and the `-k vision` /
  "pro-**vision**-al" substring. That is corroboration, not duplication: they are
  properties of the bench, not of one agent's setup. The upstream fix is kept; this rung's
  §12 was folded into theirs, leaving its unique contribution — the **named selector**
  (`scripts/rung7_vision_bench.sh`, 16 explicit files, **163 / 1 skipped / 0**).
- **Hygiene item (a) STANDS** and is still the supervisor's to sequence.
- **The ledger conflict resolved by keeping BOTH sides**, as §11.1 prescribes; the
  free-block list is reconciled (rung 7 consumed 9000–9107, so `9000+` is no longer free —
  now `2100+, 4300+, 6100+, 9200+, 12000+`).
- **No committed number moves**, mine or anyone's.
