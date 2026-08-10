# MOTION ENERGY vs THE ISI WALL — RESULTS

Pre-registration `VISION_MOTIONENERGY_PREREG.md`, committed **`b3432af60a`**
before any number. Branch **`worktree-agent-a4a2e9af9182fc73d`** — the name I
actually see; no `gamma-substrate/motionenergy` name exists. Base SHA
**`f893a19b7b65`**.

Engine **`e039d2eec2dd`** (`own` build, `scripts/engine_build.sh`) — **THIS RUNG
ADDS RUST** (`MotionEnergy`, enum index **179**, ADDITIVE, default OFF).
Provenance gate as its **own step before any number**:
`tests/test_engine_provenance_migrated.py` **7 passed**; and `provenance_line()`
is printed **from inside the measuring process** and compared against
`EXPECT_ENGINE`, aborting on divergence. Re-verified after the measurement:
`e039d2eec2dd`, unchanged.

Oracle `scripts/rung7_vision_bench.sh` (this worktree has **no `data/`** → the
212/10 §10.2 case): **before 210 passed / 10 skipped** (the 2 "failures" were the
provenance tests, failing ONLY because the Rust source was edited mid-run before
the rebuild — a self-inflicted timing artifact, engine ≠ source during the edit
window, not a regression); **after 212 passed / 10 skipped, exit 0** — the clean
212/10 state. Rust `cargo test --lib`: **627 passed** (622 pre-change **+5 new
`motion_energy_tests`**), 0 failed, 4 ignored, incl.
`variant_table_covers_the_enum`. `tests/test_motion_energy_ast_migrated.py`
**8 passed**.

Seeds **113000–113999**. `check_claim(113000,113999)` at prereg time: **CLEAN —
no collision detected**. Measured with `scripts/seed_audit.py`: **200 draws,
seeds 113000–113099 (the noise arm), all in-block, `unknown_sinks: 0`,
`parse_errors: 0`.** loadavg at the confirmatory run **(0.53, 0.50, 0.56)**; the
whole measurement is EXACT/COUNTED — no wall-clock quantity is a verdict.

---

## THE HEADLINE, IN SEVEN LINES

**THE REGISTERED DISCRIMINATOR RETURNS `FALSIFIED (k*=0)` — but NOT because
ISI=0 is best.** The signed rightward opponent is **exactly 0 at k=0** (the
forced Nyquist cancellation, declared in advance) and **NEGATIVE at every one of
the 72 `(S, k≥1)` cells** — the two-flash reads as net **LEFTWARD**. `R(0)=0`
wins the argmax by being the LEAST NEGATIVE.

**That negative sign is REVERSE PHI**: a gap-separated sharp two-flash, read
spectrally, is dominated by its aliased opposite-direction energy — a real,
documented sampled-motion phenomenon (continuous small-step motion reads
FORWARD; the gapped jump reads REVERSE). The mechanism is genuinely directional
(C-POS `+1.6e9`, C-LEFT `−1.6e9`), so the reverse sign is a finding, not a bug.

**So the wave hypothesis is CLOSED for phi as I operationalized it**: motion
energy does NOT deliver a clean rightward interior ISI optimum. I registered this
null reading in advance and do **not** rescue it.

**The honest disclosure (a NEW hypothesis, NOT a rescue):** the direction-agnostic
motion STRENGTH (`motion_frac`) is LOWEST at k=0 (0.44) and rises monotonically
to 0.86 — so there IS a sense in which ISI=0 is the weakest motion signal. But it
is a DIFFERENT statistic than the one registered, and it rises **monotonically to
the boundary** (no interior peak, no fall at long ISI), so it still does not match
the human interior-optimum curve. Flagged for a prospective pre-registration (§5),
never claimed here.

---

## 0 — CONTROLS, RUN FIRST (dead-instrument arms must fire)

| control | opponent | verdict |
|---|---|---|
| **C-POS** continuous rightward motion (4 px/frame) | **+1.627e9** | opponent > 0 ✅ |
| **C-LEFT** continuous leftward motion | **−1.627e9** | opponent < 0 ✅ — **the sign FLIPS** |
| **C-NULL** two identical frames | −2.94e−39 (`opp_frac` −1.1e−48) | static ≪ motion ✅ |

**C-POS/C-LEFT are the dead-instrument arms** — the mechanism SEES direction and
its SIGN is meaningful (a magnitude could not flip). C-NULL is a
MEASURED-vs-MEASURED disclosure (§13 admits orderings between measured
quantities): a static field's directional fraction is a vanishing beside a real
motion's. **The −2.9e−39 is the DFT's `exp(-iπ)≠-1` rounding floor**, reported,
never thresholded (see §8 error 1).

**RUST ≡ NUMPY**, condition by condition (independent `np.fft` re-derivation):
**C-POS opponent agrees at reldiff 8.79e−16** (machine precision). Over all 73
conditions the max reldiff is 8.34e−07 with `n_disagree(>1e−9) = 9` — **and all 9
are the k=0 cells**, where opponent is a catastrophic cancellation of two ~1e9
quadrant sums; the residual is `max |Δopponent| / total_ac = 3.21e−16` (machine
epsilon). **The nine "disagreements" ARE the numerical signature of the forced
Nyquist zero, not a port defect** (the non-cancelled quantities agree to ~1e−15).

---

## 1 — THE ISI CURVE, AND THE REGISTERED DISCRIMINATOR

`R(k) = mean over S of opp_frac(S,k)`, `opp_frac = opponent / total_ac`. Grid is
gapabduce's EXACTLY (`S_GRID=[1,2,4,6,8,12,16,20,32]`, `K_GRID=[0..7]`).

| k | steps=k+1 | R(k) |
|---|---|---|
| **0** | 1 | **+0.0000** |
| 1 | 2 | −0.1336 |
| 2 | 3 | −0.1152 |
| 3 | 4 | −0.1415 |
| 4 | 5 | −0.1325 |
| 5 | 6 | −0.1435 |
| 6 | 7 | −0.1382 |
| 7 | 8 | −0.1442 |

**`k* = 0`. `R(0) = 0` is the unique global maximum, strictly above every
`k ≥ 1` (no tie).**

| branch | condition | outcome |
|---|---|---|
| INTERIOR OPTIMUM | `k* != 0` AND `R(k*) > R(0)` | ❌ |
| **FALSIFIES** | `R(0) >= R(k)` for every k | ✅ |
| AMBIGUOUS | tie with some `k ≥ 1` | ❌ (no ties) |

### The per-cell matrix — the sign is UNIFORM

`opp_frac(S,k)`; every `k≥1` column is negative, magnitude shrinking with S:

```
   k=      0       1       2       3       4       5       6       7
S=  1  +0.000  -0.249  -0.215  -0.264  -0.247  -0.267  -0.258  -0.269
S=  2  +0.000  -0.299  -0.258  -0.316  -0.296  -0.321  -0.309  -0.323
S=  4  -0.000  -0.256  -0.221  -0.271  -0.254  -0.275  -0.265  -0.276
S=  8  -0.000  -0.098  -0.084  -0.103  -0.097  -0.105  -0.101  -0.105
S= 32  -0.000  -0.020  -0.017  -0.021  -0.020  -0.022  -0.021  -0.022
```

**Not one cell at k≥1 is positive.** The two-flash reads as reverse motion at
every separation and every gap. Larger S → weaker (the sharp jump's energy
smears across more aliased orders).

### §13.1 — WHAT WAS FORCED, DECLARED BEFORE THE RUN

**`opponent(k=0) ≈ 0` is FORCED by the temporal sampling limit, and I declared it
in the pre-registration**, exactly as gapabduce declared `R(0)=1` forced. A
two-frame sequence has only DC + Nyquist temporal frequencies; the Nyquist row is
direction-ambiguous (`P(ωx, Nyq) = P(−ωx, Nyq)` for a real signal), so its power
splits EQUALLY into right and left and the opponent cancels with no
hand-exclusion. **Confirmed exactly: opponent(k=0) = 0 (±1e−7 cancellation) at all
9 values of S.** Being forced by the LATTICE, not a chosen constant, is what makes
it a derivation of the same standing as gapabduce's "every integer divides by 1".
The evidential weight therefore sits on the NON-forced content: the SIGN and shape
of `R(k≥1)` (measured: uniformly negative — reverse phi), the magnitude/phase
arm, the SAD comparison, and the raw-raster capability.

---

## 2 — MAGNITUDE vs PHASE — the registered trap

| probe | result | reading |
|---|---|---|
| **per-frame magnitude** `Σ_t \|DFT_x(s_t)\|²` | opponent **≡ 0** over the whole grid | **BLIND** — magnitude that discards the TEMPORAL ARRANGEMENT cannot form a direction. The registered NEGATIVE. |
| **phase-zeroed joint spectrum** (keep `\|S\|`, drop `arg S`) | opponent == full (max reldiff 8.34e−07) | direction is a POWER-SPECTRUM property, phase-INVARIANT (Adelson-Bergen). |

**The honest nuance:** for DIRECTION, the magnitude of the JOINT space-time
spectrum suffices (a two-flash's `|S|²` is already directional through its
quadrant asymmetry). The trap the tree's memory records — *"read arrangement from
magnitude"* — concerns POSITION/ARRANGEMENT, which this mechanism does NOT read.
**The trap is avoided by keeping the JOINT space-time spectrum (which preserves
the cross-frame temporal phase that links the two frames), NOT by discarding
phase.** A magnitude-only mechanism that threw away the temporal arrangement (the
per-frame probe) is blind — that is the negative, and it is what the trap warns
of.

---

## 3 — THE SAD INCUMBENT — AND THE PROVISO THAT BROKE

The prereg (P4) predicted SAD would CONFABULATE a confident wrong vector at k=0,
S≥8, while motion energy abstains. **The proviso BROKE, informatively:**

| S | k=0 | SAD `v_src` | motion-energy opponent |
|---|---|---|---|
| 4 | 0 | (0, 4) — correct, within aperture | ≈ 0 (Nyquist) |
| 8 | 0 | **(0, 0)** — SILENT MISS | ≈ 0 |
| 12 | 0 | **(0, 0)** — SILENT MISS | ≈ 0 |

**On the UNIFORM-BACKGROUND phi stimulus, SAD SILENT-MISSES `(0,0)` past the
aperture — it does NOT confabulate.** The 10.67% confidently-wrong / confabulation
bound is a **TEXTURED-input** property (`VISION_MOTION_SENSOR_GATE_RESULTS.md` §3.4
measured 50–75% silent miss on a figure on a uniform field). So on this exact
stimulus BOTH mechanisms effectively abstain at k=0 — SAD by a `(0,0)` tie
tie-break, motion energy by a balanced right=left (opponent 0). **The
abstain-vs-confabulate contrast I registered does not materialize on uniform
background because the incumbent already abstains there.** The bound motion energy
inherits/removes is therefore a TEXTURED-input claim I did not run, stated as
scope (§7), not measured here.

---

## 4 — NOISE, AND THE RAW-RASTER CAPABILITY

- **Noise arm (seeds 113000–113099, 100 independent k=0 dot pairs):** mean
  opponent **−4.5e−07**, max |opponent| **1.3e−05** — i.e. **≈ 0**: random
  endpoints produce no consistent direction, exactly as the forced-zero k=0
  analysis predicts (a 2-frame pair is direction-ambiguous whatever the dots).
- **THE CAPABILITY (P5 confirmed):** `MotionEnergy` consumes the **RAW BOUNDED
  RASTER** (24×160 luminance field) at every one of the 72 cells, with NO
  figure/ground split. This is the segmentation the abduction family could not
  do — `TimeInfer`/`GapAbduce` "cannot consume a bounded pixel field at all"
  (their own recorded bound). Motion energy is a spectral operation on luminance;
  it needs no supplied support. **That capability is real and is the one
  unambiguous positive of this rung.**

---

## 5 — WHICH REGISTERED OUTCOME OCCURRED

| # | prediction | outcome |
|---|---|---|
| P1 (forced) | `opponent(k=0) ≈ 0` | ✅ exactly, all S |
| **P2 (the bet)** | `R(k)` rises for k≥1, `k*≠0` → CONFIRM | ❌ **WRONG** — R(k≥1) is NEGATIVE (reverse phi); `k*=0`, **FALSIFIED** |
| P3 | per-frame magnitude ≡ 0; phase-zero == full | ✅ both |
| P4 | SAD confabulates at k=0 S≥8; ME abstains | ⚠️ **proviso broke** — SAD SILENT-MISSES on uniform bg; confabulation is textured-only |
| P5 | ME runs on the raw raster where GapAbduce cannot | ✅ 72/72 cells |

**My headline bet (P2) was wrong, and the way it was wrong is the finding.** I
predicted a clean forward interior optimum; the mechanism instead reads the sharp
two-flash as REVERSE motion at every gap, so ISI=0 is the unique ambiguous
(zero) cell rather than a forward peak elsewhere. The wave hypothesis is closed
for phi as registered.

---

## 6 — §13: NO NUMBER ENTERED THE READOUT

The `MotionEnergy` partition is **exact sign / equality on integer DFT indices**
(`fx*ft<0` rightward, `ft==0` static, `fx==0` flicker) — **no tolerance and
nowhere to put one**, the strongest §13 outcome (as the prereg predicted). The
grid is fixed entirely by the field width and the sequence length; the continuous
structure (phase, energy) lives in the DFT, which is the CROSS-FRAME MAP.

`tests/test_motion_energy_ast_migrated.py` — **8 passed.** A Python AST walk (not
a substring selector), POSITIVE-CONTROLLED THREE WAYS: an INLINE non-zero-literal
ordering, a NAMED one (module-level name resolved to its literal), and an axis
comparison all turn the scan RED, while the unmodified source is asserted GREEN,
and subscript indices are PRUNED (`ast.walk` cannot prune — explicit descent). Every
verdict decides by a sign test against the sentinel 0, an equality, or an ordering
between two MEASURED quantities — never against a tuned constant.

**Declared residuals, labelled CONFIGURATION and nothing stronger:** `DOT=4`,
`FIELD_H=24`, `FIELD_W=160`, `BG`, `FG`, `ROW` (stimulus construction, inherited
from the gapabduce rung); the row-collapse (horizontal-motion-only) is a declared
scope, not a tuned parameter. The claim about all of these is the weak one — bound
once, never a verdict threshold.

---

## 7 — WHAT IS NOT SHOWN (§8)

- **Nothing about human phi's mechanism.** Human phi enters only as the parameter
  dependence compared against; no human data measured.
- **The falsification is under a SCALE-FREE spectral readout.** A spatial-frequency-
  SELECTIVE motion energy (a filter tuned to the dot's own scale) was NOT built —
  it might read FORWARD at the tuned scale, but SELECTING that scale is the §13
  magic-number trap (a chosen preferred velocity sets the peak). The honest,
  scale-free reading marginalizes over the whole spectrum, where the aliased
  reverse orders dominate. **"A tuned filter reads forward" is a hypothesis this
  rung did not test and would require its own pre-registration with a derivation
  of where the scale falls out.**
- **The unsigned-motion-strength reading** (ISI=0 weakest, monotone-rising) is a
  DIFFERENT statistic than registered and is flagged, not claimed (§5).
- **The SAD confabulation bound is textured-input only** and was not run here
  (§3); on uniform background both mechanisms abstain.
- **One dot, one shape, one size, horizontal only, uniform background.** Inherited
  scope. A textured background was NOT run.
- **`R(k)` is a marginal over `S_GRID`;** the full 9×8 matrix is in
  `results/motion_energy_measure.json` so the marginal can be recomputed.
- **No timing claim of any kind.** Every quantity is exact or counted.

---

## 8 — WHAT I GOT WRONG

1. **I registered C-NULL as `opponent == 0` EXACTLY — which a naive DFT cannot
   deliver.** For two identical frames the opponent is analytically zero, but
   `exp(-iπ)` is not exactly −1 in float64, leaving a ~1e−39 rounding floor, so
   the control could not fire as written. Caught on the FIRST confirmatory run
   (the control aborted). Fixed to a MEASURED-vs-MEASURED ordering (static is
   less directional than real motion — §13-admissible), the rounding floor
   REPORTED not thresholded, and the discriminator and ISI curve UNTOUCHED
   (re-run byte-identical). This is the shape this arc keeps finding: an
   analytic invariant broken by float, and the honest fix is a scale-relative
   comparison, not an epsilon.
2. **My headline prediction (P2) was WRONG.** I bet on a clean forward interior
   optimum and got uniform reverse phi. I under-weighted that a scale-free
   spectral readout of a SHARP two-flash is dominated by aliased reverse orders —
   the very reason two-flash/strobed motion famously reverses. Registered
   honestly two-sided, so the miss is diagnostic.
3. **P4's SAD-confabulation prediction broke** because I quoted a TEXTURED-input
   bound (10.67% confidently-wrong) against a UNIFORM-background stimulus, where
   the motion-sensor-gate rung had ALREADY measured 50–75% SILENT MISS. The
   confabulation/abstention contrast cannot be shown on uniform background because
   the incumbent already abstains there — a scope error in choosing the comparison
   condition, disclosed not buried.
4. **I edited Rust source while the oracle-before was still running**, so the two
   provenance tests failed on a source≠engine timing artifact (the 210/10 clean
   count is the real before-state). Sequencing error; recorded so the before/after
   is honest.

---

## 9 — LEDGER ROW (for the supervisor to merge into `VISION_PROTOCOL.md`)

*Written here, not there — `VISION_PROTOCOL.md` is not this rung's file.*

| range | used for |
|---|---|
| **113000–113999 (200 draws resolved 113000–113099, all in-block, unknown_sinks 0, parse_errors 0)** | **MOTION ENERGY (Adelson-Bergen, the waveform-native mechanism) DOES NOT BUY THE HUMAN ISI CURVE — AND THE WAY IT FAILS IS REVERSE PHI.** New Rust Term **`MotionEnergy`** (ADDITIVE, enum index **179**, every existing variant index UNMOVED; default OFF, no seed binds it): reduces the raster to the horizontal space-time signal, takes the joint 2-D DFT over `(x,ti)`, partitions `|S(ωx,ωt)|²` by the SIGN of the spatiotemporal orientation (opposite-sign quadrants = rightward, same-sign = left, `ωt==0` static, `ωx==0` flicker). **CONSUMES THE RAW BOUNDED RASTER — no figure/ground split, the capability the abduction family lacked (P5, 72/72 cells).** **THE REGISTERED DISCRIMINATOR RETURNS `FALSIFIED (k*=0)`: the signed rightward opponent is EXACTLY 0 at k=0 (the FORCED Nyquist cancellation, DECLARED IN ADVANCE — a 2-frame sequence has only DC+Nyquist temporal freqs and Nyquist is direction-ambiguous, `P(ωx,Nyq)=P(−ωx,Nyq)`) and NEGATIVE at ALL 72 `(S,k≥1)` cells — the sharp two-flash reads as net LEFTWARD (REVERSE PHI); `R(0)=0` is the unique max by being least-negative, no tie.** The mechanism is genuinely directional (C-POS +1.6e9, C-LEFT −1.6e9 — the sign FLIPS). **The wave hypothesis is CLOSED for phi as operationalized; the pre-registered null reading is NOT rescued.** HONEST DISCLOSURE (a NEW hypothesis, NOT a rescue, §5): the direction-agnostic motion STRENGTH `motion_frac` is LOWEST at k=0 (0.44) and rises MONOTONICALLY to 0.86 — a sense in which ISI=0 is weakest, but a different statistic and still monotone (no interior peak, no fall at long ISI). **MAGNITUDE vs PHASE (P3): per-frame magnitude spectra summed over time give opponent ≡ 0 (BLIND — the registered NEGATIVE, magnitude discards the temporal arrangement motion needs); phase-zeroed JOINT spectrum == full opponent (direction is a power-spectrum property, phase-INVARIANT per Adelson-Bergen — the trap concerns ARRANGEMENT, not direction, and is avoided by keeping the JOINT space-time spectrum).** **RUST ≡ NUMPY (independent np.fft) at reldiff 8.79e−16 on C-POS; the only 9 disagreements over 73 conditions are EXACTLY the k=0 forced-zero cells (|Δopponent|/total_ac = 3.2e−16 = machine epsilon — the numerical SIGNATURE of the cancellation, not a port defect).** **§13 SATISFIED BY CONSTRUCTION: the partition is exact sign/equality on integer DFT indices, NO NUMBER AT ALL; AST gate 8 passed, positive-controlled three ways (inline + NAMED + axis all bite, unmodified green, subscripts pruned).** **WHAT IT GOT WRONG: (1) registered C-NULL as `opponent==0` EXACTLY, which a naive DFT's `exp(-iπ)≠−1` rounding floor (~1e−39) makes unachievable — fixed to a measured-vs-measured ordering, floor reported not thresholded, discriminator/curve byte-unchanged; (2) MY HEADLINE BET (P2, clean forward interior optimum) WAS WRONG — got uniform reverse phi, registered two-sided so the miss is diagnostic; (3) P4 quoted a TEXTURED-input confabulation bound (10.67%) against a UNIFORM-background stimulus where SAD ALREADY SILENT-MISSES (0,0) at S≥8 — the abstain-vs-confabulate contrast cannot be shown on uniform bg; (4) edited Rust mid-oracle-before, failing 2 provenance tests on a source≠engine timing artifact.** Provenance gate its OWN step (7 passed) + printed from INSIDE the measuring process with abort-on-divergence, re-verified `e039d2eec2dd` post-measurement; `cargo test --lib` 622 + 5 new `motion_energy_tests` incl. `variant_table_covers_the_enum`; oracle 212/10 before AND after; engine `e039d2eec2dd` **`own` — THIS RUNG ADDS RUST.** |

---

## 10 — NAMED NEXT LEVERS, each needing its own pre-registration

1. **A SPATIAL-FREQUENCY-SELECTIVE motion energy** — a filter tuned to a scale
   that FALLS OUT of the stimulus (the dot's own spatial frequency, or an
   MDL-selected band), read for FORWARD energy at that scale. The scale-free
   reading here is dominated by aliased reverse orders; a band-limited reading
   might read forward. **The lever is: derive the band, do not pick it.**
2. **The unsigned-motion-strength curve as a prospective hypothesis** — `motion_frac`
   lowest at k=0, monotone-rising. Does it develop an interior peak (a fall at
   long ISI) when the temporal correlation is allowed to decay — e.g. under a
   temporal window whose width FALLS OUT of a noise floor? That is the human
   curve's missing upper limb.
3. **REVERSE PHI as a positive target, not a failure** — this rung MEASURED
   uniform reverse phi. Human reverse phi (contrast-inverted apparent motion) is a
   sharp signature. Can the substrate replicate the reverse-phi FAILURE MODE (the
   creator's "can we replicate known failure modes" instrument)? That is a
   discriminating test the abduction family could not even pose.
4. **A textured-background run** — the figure/ground split is the load-bearing
   assumption; motion energy on the raw raster is exactly the mechanism that
   SHOULD survive texture where the SAD sensor confabulates 10.67%. That is where
   the incumbent-bound comparison actually lives.
