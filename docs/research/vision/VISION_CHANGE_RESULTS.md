# THE CHANGE-DETECTION RUNG — RESULTS

*Pre-registered in `VISION_CHANGE_PREREG.md`, committed BEFORE the run (`eb16dcad`).
Runner: `scripts/change_sparsity_measure.py` (COMMITTED — rung 2's headline was lost
because its runner was not). Engine `366ce5f14eff`. Seeds 17000–17999.*

## THE HEADLINE — a NEGATIVE, and it kills the event-driven scaling argument

**Change detection at a threshold that FALLS OUT does NOT make the retina sparse on
natural scenes. It fires 83–97% of cells. There is no 100:1 compression, at any
biologically plausible drift.** The measurement and the literature agree, and they
agree for *different* reasons — which is what makes it solid.

**The median split is dead.** `driven%` was **exactly 50.00** in every visual regime;
it is now regime-dependent and nothing is round.

| regime | median split (`change=0`) | change detection (`change=1`) |
|---|---|---|
| waves (no visual input) | 0.00% | 0.00% |
| stabilised natural image | **50.00%** | **84.45%** |
| drifting natural image (σ=1px) | **50.00%** | **96.54%** |
| dynamic noise | **50.00%** | **99.16%** |

**They differ.** (Photograph PINNED at #0; the median column is the defect, reading
50.00 in all three visual regimes exactly as predicted.)

## What the threshold falls out of — one sentence

**The cell's own photon shot-noise floor: it fires iff `|I_t − I_{t−1}| > sqrt(I_t /
nmax)`, with `nmax = 255² = 65025` fixed by the input's own 8-bit dynamic range (a
well-matched sensor's quantization step is its noise at full scale) — nothing is tuned
against sparsity, and §13 names "its noise floor, its dynamic range" as legitimate
sources.**

**And the honest correction to the brief's premise.** The log receptor does Weber-
normalise change detection — and the normalisation is **vacuous for sparsity**, because
to first order the receptor gain cancels from both sides:

    signal = |Δlogr(I)| ≈ |ΔI|/(I+i0);  floor = |dlogr/dI|·σ_I = σ_I/(I+i0)
    ⇒ signal > floor ⟺ |ΔI| > σ_I

A *constant* log-contrast threshold (what a DVS actually uses) **is** genuinely Weber-
normalised — but that constant is **a tuned bias current**, i.e. exactly §13's magic
number. Independently confirmed from the DVS primary source (Graca/McReynolds/Delbruck
2023): the log transduction falls out of subthreshold MOSFET physics
(`Vpr = (UT/κ)·log(Ev,p + Ev,dark) + Vp0`, `UT`≈25mV thermal voltage) — **but the
threshold is set by user bias currents `OnBn`/`OffBn`/`DiffBn`, with no principled
derivation, no appeal to shot noise or scene statistics**. *The DVS literature offers no
precedent for a principled threshold — it offers a knob.* And the biology has the same
shape: the Weber normalisation is mechanistic, **nothing in the retina corresponds to a
tuned global threshold**.

Noted, not relied on: the eye seed runs `i0 = 1.0` with luminance in [0,1], where
`log(I+1)` has gain varying only 2× across the range — nearly **linear**, barely Weber
at all *at this operating point*. The 0.9991 Weber–Fechner fit must span a wider `I`
range than this rung's frames do.

## THE SURFACE — why the negative is robust, not a tuning artifact

Sparsity is a smooth function of drift amplitude with **no knee**. At the shot-noise
floor (nothing chosen), with the photograph PINNED so only drift varies:

| drift σ | photo #0 | photo #7 |
|---|---|---|
| 1.00 px | 97.12% | 91.02% |
| 0.50 px | 96.18% | 87.65% |
| 0.25 px | 89.80% | 82.98% |
| 0.10 px | 85.51% | 74.75% |
| 0.05 px | 84.51% | 68.43% |
| 0.02 px | 83.16% | 69.92% |

**At no drift amplitude does it go sparse.** The floor of the whole surface is ~68% —
i.e. **1.5:1**, not 100:1. Fixational drift moves the image by ~1 photoreceptor per step,
so every cell with any local gradient changes by more than its own noise. Getting DVS-
like 1–5% sparsity needs a threshold ~20–40× the noise floor: **the DVS bias current, a
magic number**. This is **not rescued** (§5, §7).

## THE BIOLOGY — the brief's premise is a category error

Commissioned research (sources below) refutes "compression happens because RGCs fire on
change" on a point of pure logic, **independent of my measurement**:

- **126M:1M is an ANATOMICAL CELL-COUNT ratio — a spatial fan-in. Temporal change-
  detection cannot contribute to a count of cells. Firing-on-change reduces
  spikes/second, not axons. Different axes.** No primary source argues the change story.
- **The 126M is an artifact of n=1** (Osterberg 1935, a single retina, diagnosed by
  Curcio 1990 as a peripheral outlier 30–40% high). Measured: 4.60M cones + 92.0M rods
  (Curcio 1990, n=6/3), 1.02M axons (n=221) ⇒ **≈90:1, not 126:1**. Within-eye ratio
  ranges **84.8:1 to 158.5:1** — a **1.87× spread between two individuals**, and cone and
  RGC counts are **uncorrelated** (Curcio & Allen 1990). **The ratio is a quotient of two
  independently-varying quantities — it is not a constant and must not be hard-coded.**
- **The fovea INVERTS it**: 1 cone → 2 midget RGCs (ON+OFF) ≈ **1:2 EXPANSION**. There is
  **zero compression where acuity lives**.
- **The retina is not a differentiator.** Midget/P cells are **sustained, linear** and
  ~80% of the optic nerve; Turner et al. 2020 — midget and parasol "divide naturalistic
  movies into adjacent spatiotemporal frequency domains with equal stimulus power". **The
  retina allocates its majority channel to the LOW temporal frequency band.** A
  differentiator would discard it.
- **Sparsity itself is the shakiest assumption**: eLife 2022;11:e78005 — bits/spike
  **awake 0.3 vs ex vivo 2.3 (~8×)**; *"the retina employs dense coding in vivo, rather
  than sparse efficient coding as has been often assumed from ex vivo studies."*
  **My measured 83–97% firing is closer to the awake retina than sparse coding is.**
- Where compression actually comes from: **space and energy** (Balasubramanian & Sterling
  2009 — optic nerve *diameter* limits cell number). And if you want decorrelation, it
  lives in a **threshold nonlinearity, not a DoG kernel**: Pitkow & Meister 2012 measured
  centre-surround ~25% vs sparsifying nonlinearity ~60%; *"the much-touted center-surround
  receptive field makes only a minor contribution"*, and *"the sparsifying nonlinearities
  account for the bulk of temporal decorrelation."*

## CONSEQUENCE FOR THE SCALE WALL

**An event-driven retina does not rescue the ~750ms fovea extrapolation.** Two
independent reasons, and either alone is sufficient:

1. **Measured**: it isn't sparse (83–97% fire), so there are no events to skip. The FFI
   crossing count is ~unchanged, and the wall is the FFI (75–82% of budget).
2. **Biological**: the extrapolation is about the **FOVEA**, and the fovea has ~**1:2
   expansion**, not compression. There is nothing there to compress.

**So the 100:1 compression is NOT present here, and it should not be — it is not a
temporal phenomenon and it does not exist in the fovea.** The scaling problem must be
attacked at the FFI boundary (batch the crossings; `s.node(n)` materialises a whole attr
dict to read one field, ~4N crossings/tick), not by an event camera.

## TRAP 2 — TROXLER REMAINS FALSIFIABLE, AND IT WAS NEARLY NOT

**Could this model have produced the opposite result? YES — and it is now measured, not
argued:**

| arm | stabilised image | drifting image |
|---|---|---|
| `sustain=0` (transient only — **the tautology**, kept as a CONTROL) | **0.00%** | 92.78% |
| `sustain=1` (transient + sustained — **the default**) | **90.64%** | 98.30% |

A pure differentiator **cannot** fire on a stabilised image: 0.00%, fading forced by
construction, §13.1's third category. With the sustained channel present the retina
**keeps firing at 90.64% on a perfectly stabilised image indefinitely** — **so this model
PREDICTS NO RETINAL FADING, which CONTRADICTS a retinal account of Troxler.** The model
can be wrong, and the experiment can say so. That is the falsifiable content the brief
demanded, and it survives.

**Which rule is solely responsible for which half (§13.1):** the transient channels alone
would *force* fading; `ch_sustained` alone makes the outcome contingent. I state that
plainly rather than claim the architecture derived anything.

**The biology says the model is right to predict no retinal fading** — which is the
strongest evidence this is not a rigged reproduction: McLelland, Ahmed & Bair 2009
(macaque LGN, 1-min static stimuli) measured **P cells τ≈17s, M cells τ≈22s**, responses
**not returning to baseline even after 64s**: *"these major feedforward inputs to cortex
adapt too slowly to account for visual fading… faster-adapting mechanisms in cortex are
likely to be required."* And Troxler's locus is substantially **cortical**: afterimages
are perfectly stabilised by construction yet still fade, and **TMS over early visual
cortex partially reverses the fading**; a cortically-stabilised, retinally-free image
also fades (Blakemore et al. 1971).

**I got this wrong first, and my own gate caught it.** The first `ch_sustained` tested
deviation from a **cumulative-mean temporal reference** — and it was **INERT** (0.00%
under stabilisation, per-channel `sus=0.00%`), because a cumulative mean's first sample
sets `ref = value` **exactly**, so the deviation is 0 forever. That is §13.2's disease
precisely: **a channel that works in principle and is wired to nothing** — and it would
have made the model a pure differentiator *wearing a sustained channel's clothes*, i.e.
**TRAP 2 unavoided while appearing avoided**. The fix is what the biology says: sustained
RGCs encode **centre-surround CONTRAST**, which is **spatial** and has no time argument to
adapt away. Caught only because clause 4 was reported **per channel** off a positive
stamp — the aggregate `driven%` looked fine.

## §1's FIVE CLAUSES — all five, on the instrument

| clause | result |
|---|---|
| **5. moves something downstream** (run FIRST, §13.2/FM-0) | `D_driven = 5.0e-01`, `D_bursting = 5.0e-01` ⇒ **LOAD-BEARING** |
| **1. floor** | stabilised, transient-only = **0.00%** |
| **2. ideal** | dynamic noise, transient-only = **98.58%** |
| **3. duration-stability** | n=30/60/120/240 → 92.54 / 94.23 / 93.57 / 94.05 — **no trend** (±1pp) |
| **4. arms alive** | **the waves arm: `burst%=21.51`, states `{active, recruited, refractory, rested}` (4 distinct)** |

**The positive-control witness is the waves arm's 4-state histogram + 21.51% bursting.**
`tick()`'s return is **not** reused: it counts progressing rule *visits* and reads 3 on a
live retina and a near-idle one (the scaling agent's control was nearly inert). Liveness
here is read off a **positive per-channel stamp** (`dstep_*` == this step), never off a
guarded division or an absence (§1.1).

## §9 — defaults preserve committed results (and a LIVE experiment)

Exact commands and results, engine `366ce5f14eff`:

| gate | baseline (before) | after |
|---|---|---|
| `bash scripts/rung7_vision_bench.sh` | **185 passed / 10 skipped** | **185 passed / 10 skipped** — identical (re-run again after the `ch_sustained` rewrite: still 185/10) |
| the same bench **incl. this rung's new gate** | — | **190 passed / 10 skipped** = 185 unchanged **+ 5 new** |
| `python scripts/fm0b_drift_wired_audit.py` | LOAD-BEARING; `8.071079e-01 / 5.315726e-01 / 4.013261e-01 / 5.169134e-01` | **LOAD-BEARING; identical to the last digit** |
| `python scripts/fm0_vacuity_audit.py` | VACUOUS; all `0.000000e+00` | **VACUOUS; unchanged** |
| `python -m pytest tests/test_vision_change_migrated.py` | — | **5 passed** |

**Files touched, in full:** `domains/wave_world.py`, `seeds/vision_change.json` (new),
`scripts/change_sparsity_measure.py` (new), `tests/test_vision_change_migrated.py` (new),
`scripts/rung7_vision_bench.sh` (one line), `VISION_CHANGE_PREREG.md` /
`VISION_CHANGE_RESULTS.md` (new), `VISION_PROTOCOL.md` (ledger).
**`seeds/vision_eye.json` and every eye/setpoint script are NOT touched** —
verified by `git diff --name-only HEAD --` on each. The concurrent Troxler run is
unperturbed: it reads `EyeParams`/`EyeCell`, and nothing here writes either.

## WHAT I GOT WRONG

1. **The sustained channel was inert** and I shipped it that way until the per-channel
   control caught it (above). The aggregate number looked fine.
2. **The first drift surface was non-monotonic** (98.7→8.3→89.3→55.9→91.4) because
   `frames()` picked the image as `seed % 200` — every row varied **image and drift
   together**. Image identity swings the sustained channel **18.59% → 94.91%**. The
   confound was doing the talking. Pinned.
3. **I hung the bench**: a rule whose effect does not change its own match re-fires
   forever under an `apply_rule_once` fixed point. Every drive rule now carries its OWN
   phase key; a shared one let ON silence OFF and sustained.
4. **My worktree was based on the wrong commit** (`dadffa15`, 6 behind) and every
   required file read as MISSING — indistinguishable from never having existed, exactly
   as warned. Rebased to `f7c1e104`.

## SCOPE — what is NOT shown (§8)

- 16×16 at these drifts is a coarse retina; the fractions are an **upper bound on
  sparsity** for a foveal-density sheet, not a foveal measurement.
- Drift is **simulated by sub-pixel window translation**, not the eye's own Engbert walk:
  the eye and `wave_world` are **separate, uncoupled worlds** (FM-0 established the eye
  reaches no retinal cell). So this rung does **not** test the drift-vs-adaptation race on
  the eye's real walk — it establishes that the race is *available* to test.
- BSDS300 crops are real photographs (1/f statistics) but **static scenes**.
- Only two photographs are on the surface; the image effect is large (68–97%), so the
  surface's *level* is image-dependent. **Its sign is not**: no image, at any drift, is
  sparse.
- This licenses nothing about which biological mechanism is correct.
- The research was commissioned from a subagent which **self-reported and retracted a
  mid-task fabrication**; its DVS answers (Q5/Q6) are its own less-deeply-sourced primary
  work. Numbers above are attributed to named primary sources and should be spot-checked
  before publication.
