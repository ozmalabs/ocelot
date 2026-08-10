# THE CHANGE-DETECTION RUNG — pre-registration

*Written and COMMITTED before the confirmatory run (PROTOCOL §3). Engine `366ce5f14eff`.*

## 0. The defect this rung exists to fix

`wave_world.drive()` thresholds each frame at **its own median**, so `driven%` is
**exactly 50.00** at every size and in every regime. A number that round is not
nature — it is the adapter asserting a statistic instead of the world supplying one.
It has cost two things:

1. rung 1's `waves+video` arm (−0.090, p=0.002, wrong direction) — the diagnosis was
   already written: the median split blasts ~50% of the retina every step, which is a
   *degraded* pattern, not normal rearing. The arm's biological label was wrong.
2. natural-image sparsity is **unmeasurable**, which blocks the scale question. The
   scaling measurement found the wall is the Python↔Rust FFI (75–82% of budget), the
   curve linear (exponent 0.971, r²=0.9996), human fovea (~150k cells) → ~750ms, 15×
   over budget. Whether an event-driven retina fixes that depends **entirely** on the
   sparsity number we cannot currently measure.

## 1. What the threshold falls out of — and the honest answer

**Nothing chooses it, and that is the point.** The threshold is the **per-cell photon
shot-noise floor**: for a cell at intensity `I`, the receptor's own noise is
`σ_I = sqrt(I / Nmax)`, with `Nmax = 255² = 65025` fixed by the **input's own 8-bit
dynamic range** (a well-matched sensor's quantization step is its noise at full scale).
A cell fires iff the frame-to-frame change exceeds **its own** noise:

    |I_t − I_{t−1}|  >  sqrt(I_t / Nmax)

This is §13-legal: it is fixed by *the system's own dynamic range*, which §13 names
explicitly as a legitimate source ("its noise floor, its dynamic range"). It is the
same move as `mu_endo` — per-cell, derived from the cell's own situation, replacing an
imported constant. **Nothing is tuned against sparsity.**

**The correction to the brief's premise, and it is load-bearing.** The brief expects the
log receptor to Weber-normalise change detection "for free". It does — and the
normalisation is **vacuous for sparsity**. To first order the receptor gain cancels:

    signal = |Δ logr(I)| ≈ |ΔI| / (I + i0)
    floor  = |d logr/dI| · σ_I = σ_I / (I + i0)
    ⇒ signal > floor  ⟺  |ΔI| > σ_I          (the gain 1/(I+i0) CANCELS)

So a shot-noise-referenced change detector is **scale-free in the receptor transform**;
the log buys nothing here. A *constant* log-contrast threshold (what a DVS actually
uses) is genuinely Weber-normalised — but that constant is a **tuned bias current**,
i.e. exactly §13's magic number. **Both roads are reported.**

Separately noted, not relied on: the eye seed runs `i0 = 1.0` with luminance in [0,1],
where `log(I+1)` has gain varying only 2× across the whole range — i.e. it is nearly
**linear** and barely Weber at all *at this operating point*. The Weber–Fechner 0.9991
fit must span a wider `I` range than this rung's frames do.

## 2. TRAP 2 — why this is NOT a Troxler tautology

A **pure** change detector makes Troxler fading true by construction: stabilised ⇒ no
change ⇒ no firing ⇒ fades, and **the model could not not fade**. That is §13.1's third
category (architecture forcing the signature) and it is worse than a bad constant.

**The biology is not a pure differentiator** and neither is this rung: parasol/M cells
are transient, midget/P cells are sustained; **both exist**. This rung therefore ships
**two channels**:

- `ch_transient_*` — fires on change above the cell's own shot-noise floor (ON on
  increase, OFF on decrease). These are *not* complements: both are silent when nothing
  changes, which also **repairs rung 6's `x_OFF = 1 − x_ON`** — a construction this
  protocol's own §13 table lists as "degenerate BY CONSTRUCTION".
- `ch_sustained` — fires on contrast against the cell's **own slowly-adapting
  reference** (`lum_ref`, a cumulative mean on the `mu_endo` precedent, whose timescale
  therefore falls out of 1/n and not from a chosen β).

**Could this model produce the opposite result? YES — and that is the whole point.**
Under a stabilised image the transient channel is silent, but the **sustained** channel
keeps firing until `lum_ref` catches up with `lum`. Whether it fades is a race between
the adaptation timescale (falling out of `mu_endo`'s 1/n) and the drift's own timescale
(Engbert's walk, α *measured* 1.1553/0.7590, never imported). **Neither was chosen with
the other in mind.** If adaptation is slower than the run, the model predicts **no
fading** — a stabilised image would keep driving the sustained channel indefinitely.
The model can therefore fail Troxler, and Troxler remains falsifiable after this change.

**What I will NOT claim:** that reproducing fading would vindicate the architecture. Per
§13.1, I will report **which rule is solely responsible for which half** of any
signature. The transient channel alone *would* force fading; it is the sustained
channel's presence that makes the outcome contingent.

## 3. Pre-registered hypothesis (two-sided)

**H1 (two-sided).** The four regimes' `driven%` are **not** all equal.

The null this rung exists to kill is the current one: `driven% = 50.00` in every regime,
identical at every size. **Exactly 50.00, or a value invariant across regimes, is the
tell that a new median split has been built.**

**Predictions** (stated in advance; a miss is a result, not a bug):

| regime | prediction |
|---|---|
| stabilised natural image (identical frame each step) | ≈ **0%** — no change, so only the sustained channel can fire |
| drifting natural image (~1px/step ≈ 1 cone/step) | **high, 60–95%** — NOT sparse |
| dynamic noise (i.i.d. frames) | ≈ **100%** |
| waves only (no frame) | **0%** on the `driven` channel by construction (no visual input) |

**The scientific prediction, and it is a NEGATIVE:** change detection at a threshold that
*falls out* does **NOT** make the retina sparse on natural scenes at biologically
realistic drift. Fixational drift moves the image by ~1 photoreceptor per step, so every
cell with any local gradient changes by more than its own noise. **If this holds, the
~100:1 compression is NOT attributable to temporal change detection, and the
event-driven scaling argument is dead** — an event retina would not rescue the ~750ms
fovea extrapolation, because it would not be sparse. **This will not be rescued** (§5,
§7). A tuned suprathreshold contrast (~20–40× the noise floor, i.e. the DVS bias) would
buy sparsity, and would be a magic number.

**Provisos.**
- Drift amplitude and threshold jointly set sparsity and there is **no knee** in the
  curve; I will report `driven%` as a **function** of both rather than a single point,
  so the dependence is visible instead of asserted.
- 16×16 at 1px drift is a coarse retina; the fraction is an upper bound on sparsity for
  a foveal-density sheet. Reported as scope, not corrected away.
- BSDS300 crops are real photographs (1/f statistics) but static scenes; drift is
  simulated by sub-pixel window translation, not by the eye's own walk (the eye and
  `wave_world` are separate, uncoupled worlds — FM-0 established the eye reaches no
  retinal cell).

## 4. §1's five clauses on the instrument (all five, before any arm)

1. **Floor** — a stabilised (identical) frame must score ≈0%. A measure that fires on no
   change is not a change detector.
2. **Ideal** — i.i.d. dynamic noise must score ≈100%.
3. **Duration-stability** — `driven%` on the *same* input must not drift with step count.
4. **Arms alive** — reported as a **state histogram + distinct-value count**, never off a
   guarded division. §1.1: a dead arm scores a perfect floor. The scaling agent's
   positive control was **nearly inert** — `tick()`'s return counts progressing rule
   *visits* and reads 3 on a live retina AND a near-idle one — **it is not reused here**.
5. **Moves something downstream (§13.2 / FM-0)** — toggling `change` must move a
   downstream attribute: `D = max|on − off|` over `driven`/`bursting`. **`D == 0.0`
   exactly ⇒ decorative; STOP and burn no seed.** Run FIRST.

## 5. Seeds

**Block 17000–17999** (declared here, recorded in the ledger). Pilots used seed **999**
and are declared as pilots, not confirmatory: `|Δlog|` distribution, the
sparsity-vs-threshold curve, and the shot-noise SNR check. 12000–16999 untouched.

## 6. §9 — defaults preserve committed results

`ChangeParams.change = 0` is the master default-off, on a **params node (graph data)**,
never a Python code path (§0). The median split is preserved *exactly* as the default
path and carries the complementary `change < 0.5` guard (the `mu_mode` precedent), so
every committed result reproduces **byte-identically**. Verified before anything else:
the rung-7 named bench (185 passed / 10 skipped), `fm0b_drift_wired_audit.py` and
`fm0_vacuity_audit.py` unchanged. **`seeds/vision_eye.json` and the eye/setpoint scripts
are NOT touched** — a concurrent agent is running Troxler against them.

## 7. Decision rule

If the vacuity gate (clause 5) reads `D == 0.0`, STOP and burn no seed. If the floor or
ideal clause fails, STOP. Otherwise run the four regimes on block 17000–17999 and report
`driven%` for each, plus the threshold×drift surface. **A negative is the result** (§7).
