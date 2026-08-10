# MOTION ENERGY vs THE ISI WALL — PRE-REGISTRATION

**Committed BEFORE any confirmatory number** (PROTOCOL §3). Seed block
**113000–113999**. Term enum index **179** (`MotionEnergy`, ADDITIVE, default
OFF — no seed binds it). Runner: `scripts/motion_energy_measure.py`. Gate:
`tests/test_motion_energy_ast_migrated.py`.

## 0 — THE WALL, AND WHY THIS IS THE REGISTERED TOOL

Five correspondence/abduction mechanisms (`phi`/`timephi`/`gapabduce` +
BlinkBridge + the SAD sensor) all peak at **ISI=0**, the INVERSE of human phi,
which REQUIRES a temporal gap. `GapVerify` proved *analytically* that no filter
over an abduction can produce an interior ISI optimum (`R(0)=1` doubly forced).
Task #145 states the open spec as a **requirement**: *something must make ISI=0
actively worse, and nothing in this tree does.*

**The hypothesis: MOTION IS ORIENTATION IN SPACE–TIME, READ AS INTERFERENCE**
(Adelson & Bergen 1985 motion energy). A quadrature pair of spatiotemporally
oriented filters; motion = a spatiotemporal frequency. A flash-then-flash pair
separated by a temporal gap has *different spectral content* than a
minimum-gap pair, so a temporal-frequency channel can respond to the gap and
NOT to the minimum-gap case — **ISI=0 genuinely worse, derived from the
spectrum rather than patched.**

**The architecture BLESSES this.** A Fourier/wave representation is a CROSS-FRAME
MAP by this project's own frame/continuum invariant: the spatial frame is the
integer pixel lattice, the spectral frame is integer-indexed bins, and the
real-valued structure (phase, energy) lives in the transform BETWEEN them. In-frame
stays integer; the continuous structure lives in the map; **"bins propose,
continuous decides."**

## 1 — THE MECHANISM (Rust Term `MotionEnergy`, index 179)

Reduce the raster to the horizontal space–time signal `s(x, ti) = Σ_row
frame[row, x]` (horizontal-motion-only, the arc's standing scope — a declared
collapse, NOT a tuned parameter). Take the joint 2-D DFT over `(x, ti)`.
Partition the power `|S(ωx, ωt)|²` by the SIGN of the spatiotemporal
orientation:

- opposite-sign quadrants (`ωx>0, ωt<0` etc.) → **right**;
- same-sign → **left**; `ωt==0` → **static**; `ωx==0` → **flicker**; `(0,0)` →
  **dc**.

Directional readout: **opponent = right − left**; **opp_frac = opponent /
total_ac** (total_ac = right+left+static+flicker). Consumes the RAW BOUNDED
RASTER directly — no figure/ground split (the abduction family could not).

## 2 — THE STATISTIC, EXACTLY

The two-flash grid is gapabduce's EXACTLY: `S_GRID = [1,2,4,6,8,12,16,20,32]`,
`K_GRID = [0..7]` (k = ISI = blank frames; temporal separation D = k+1). For
each `(S,k)` build `phi_frames = [dot@0] + [blank]×k + [dot@S]` and evaluate
`MotionEnergy`.

- **The ISI curve:** `R(k) = mean over S of opp_frac(S,k)`.
- **The discriminator statistic:** `k* = argmax_k R(k)` — **the LOCATION of the
  peak, NOT monotonicity** (the exact trap gapabduce nearly failed: a jagged
  curve peaking at 0 is a FAIL, and scoring "is it monotone?" publishes the
  opposite of the truth).

## 3 — THE DECISION RULE (fixed here, before any number)

| branch | condition | meaning |
|---|---|---|
| **CONFIRM (interior optimum)** | `k* != 0` AND `R(k*) > R(0)` | ISI=0 is worse; motion energy answers #145 — the wave/interference mechanism IS the missing ingredient. |
| **FALSIFY** | `R(0) >= R(k)` for every k | ISI=0 stays the peak; **the wave hypothesis is CLOSED for phi.** A clean, valuable negative. |
| **AMBIGUOUS** | `R(0)` is max but tied with some `k>=1` | undecided. |

`k* != 0` states the registered `k* >= 1` EXACTLY (K_GRID starts at 0) with no
ordering against a non-zero literal (PROTOCOL §13).

### THE NULL READING, REGISTERED IN ADVANCE — DO NOT RESCUE IT

**If ISI=0 stays the peak for motion energy too, the conclusion is
"interference/spatiotemporal-frequency is NOT the missing ingredient for phi" —
the wave hypothesis is closed for motion. I will report that and stop.** No
parameter search, no metric surgery (§5).

## 4 — §13.1: WHAT IS FORCED, DECLARED BEFORE THE RUN

**`opponent(k=0) ≈ 0` is FORCED by the temporal sampling limit, and I declare it
now so the k=0 dip is a DERIVATION, not an empirical discovery** (exactly as
gapabduce declared `R(0)=1` forced). A two-frame sequence (k=0, D=1) has only DC
and Nyquist temporal frequencies; the Nyquist temporal row is direction-ambiguous
(`P(ωx, Nyq) = P(−ωx, Nyq)` for a real signal), so its power falls EQUALLY into
right and left and **opponent cancels to 0 with no hand-exclusion**. A
single-frame displacement is at temporal Nyquist — maximally aliased — and has no
defined direction. **That IS why a mechanism here can finally make ISI=0 the
worst cell; and being forced by the LATTICE (not a chosen constant) is what makes
it a legitimate derivation, the same standing as gapabduce's "every integer
divides by 1".**

**Therefore the evidential weight sits on the NON-forced content:**

1. **Does `R(k)` for k≥1 actually rise above 0, and WHERE is `k*`?** (not forced)
2. **Is it a TRUE interior maximum — does `R(k)` FALL after the peak within the
   grid — or does it rise monotonically to the k=7 boundary?** Reported as a
   disclosure (`falls_after`). A boundary peak still satisfies the discriminator
   (`k*≠0`) but is a WEAKER form of the human curve (which also falls at long
   ISI). (not forced)
3. **Magnitude vs phase** (arm A2).
4. **The SAD abstain-vs-confabulate comparison** (arm A3).
5. **The raw-raster capability** — motion energy consumes the bounded field the
   abduction family could not.

## 5 — MAGNITUDE vs PHASE (the trap, registered as the NEGATIVE)

The tree's memory records *"log-polar gives invariance for free — REFUTED."*
Waves have the sibling seduction: *"Fourier MAGNITUDE is translation-invariant,
read motion from the power spectrum."* **A magnitude-only result is registered
here as the NEGATIVE, not the win.** Two probes:

- **Per-frame magnitude (`me_perframe_magnitude`):** `Σ_t |DFT_x(s_t)|²` keeps
  magnitude and discards the TEMPORAL ARRANGEMENT (which frame came first) — the
  cross-frame phase. **Predicted: it cannot form a directional opponent —
  identically 0 at every cell.** This is the trap demonstrated.
- **Phase-zeroed joint spectrum (`me_phase_zeroed`):** discard `arg S`, keep
  `|S|`, read the same opponent. `|S|²` is unchanged, so the opponent is
  IDENTICAL to the full mechanism. **Predicted: max reldiff ≈ 0** — a finding,
  not a failure: DIRECTION is a power-spectrum (magnitude) property,
  phase-INVARIANT by construction (Adelson-Bergen). **The trap concerns
  ARRANGEMENT/POSITION, which this mechanism does not read** — so keeping the
  joint space-time spectrum (which preserves the cross-frame temporal phase) is
  how the trap is avoided, NOT by discarding phase.

## 6 — THE SAD INCUMBENT (bound stated)

The incumbent is the SAD block-matcher: **confidently-wrong 10.67% at the
operating point, and it CONFABULATES rather than abstains** (a well-formed vector
of the wrong magnitude, indistinguishable downstream). **Predicted: at k=0, S≥8
(past the aperture) SAD emits a confident wrong `v_src` while motion energy reads
`opponent ≈ 0` — a graded LOW signal = ABSTENTION.** Motion energy does not emit
a displacement vector at all; it emits a directional energy, so a low energy is
an honest "no clear motion", removing the confabulation failure mode. Stated as
the bound this mechanism REMOVES (not a claim it beats SAD at producing vectors —
it produces a different, refusable readout).

## 7 — CONTROLS (dead-instrument arms, run FIRST; abort on failure)

- **C-POS:** continuous rightward motion → `opponent > 0` (a sign test against
  the sentinel 0). If it does not fire, the run is VOID.
- **C-NULL:** two identical frames → `opponent == 0` exactly.
- **C-LEFT:** continuous leftward motion → `opponent < 0` — the sign FLIPS, so
  the readout is genuinely directional, not an energy magnitude.

## 8 — CROSS-CHECK: RUST ≡ NUMPY

Every condition is evaluated by BOTH the Rust Term and an independent numpy
re-derivation (`me_numpy`, using `np.fft` — a different DFT algorithm). Agreement
is reported as the max RELATIVE disagreement across all fields and conditions
(`AGREE_RTOL = 1e-9`); a float DFT cannot be byte-identical across two
algorithms, so this is a CROSS-CHECK, not a verdict threshold. `n_disagree` (cells
over rtol) is reported verbatim.

## 9 — MY PREDICTION, STATED IN ADVANCE (with provisos)

- **P1 (forced):** `opponent(k=0) ≈ 0` (declared §4).
- **P2 (the bet):** `R(k)` rises for k≥1 and `k* != 0` → **CONFIRM**. Motion
  energy is the FIRST mechanism in this tree to invert the ISI curve. *Proviso
  that may break:* whether the peak is INTERIOR (falls after) or at the k=7
  boundary — I do not know which and register `falls_after` to find out.
- **P3:** per-frame magnitude opponent ≡ 0 (the trap); phase-zeroed joint ≡ full
  (direction is magnitude).
- **P4:** SAD confabulates a confident wrong vector at k=0, S≥8; motion energy
  abstains (`opponent≈0`).
- **P5:** motion energy runs on the RAW RASTER (no segmentation) at every cell —
  a capability GapAbduce lacked.

**If P2 is wrong (k*=0), the wave hypothesis is closed — see §3's null reading,
which I will not rescue.**
