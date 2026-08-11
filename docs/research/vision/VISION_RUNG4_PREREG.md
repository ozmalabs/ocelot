# RUNG 4 — pre-registration: does an ORIENTATION MAP form from waves alone?

*Written and COMMITTED before the confirmatory run (PROTOCOL 3). Nothing below
the "OUTCOME" heading existed when the run started.*

## Background — why this rung, and what it is NOT allowed to claim

Every vision result committed so far measured **single-unit tuning** and
explicitly disclaimed *"no map topography is measured"* (`VISION_RUNG2_PREREG.md`,
attempt 10's honest scope). In real V1 orientation preference forms a smooth
**MAP**: nearby cells prefer similar orientations. The verified research is
**3-0** that this happens **without vision** — ferret maps emerge P31–36 with no
correlation to eye opening (Chapman/Stryker/Bonhoeffer 1996) and are present in
**dark-reared** animals (White/Coppola/Fitzpatrick 2001). The map is built by
**waves**, before and without sight.

**The research's own KILLED claims, which this rung must not build on** (refuted
0-3 in the verified pass): *"the map LAYOUT is fixed/pre-specified before
vision"* and *"earliest patches occupy the same size/shape/location as mature
patches"*. The layout is **NOT** pre-specified. What is established is only:
maps emerge without visual experience, and experience is a
refinement/maintenance signal.

**Why no map could possibly have formed before this rung.** Units sat at random
receptive-field centres with **no lateral interactions at all**, under a hard
**global** winner-take-all (`wv_unit_burst_winner`) in which **exactly one unit
learns per step**. Nearby units could not know about each other by any route —
there was no mechanism, so a map was not merely absent but impossible.

## The mechanism added (graph data, OFF by default)

`seeds/vision_maps.json` — a NEW seed; `vision_waves.json` is untouched.

- **`vm_burst_lateral`** — a Unit bursts if one of its `cortical_neighbour`s is
  the Argmax winner. The winner's **neighbourhood** therefore learns the SAME
  input on the SAME step (`oja_learn`'s guard is `bursting==1`), each unit with
  its own drive `y=act`. This is the **Kohonen/SOM neighbourhood update**.
- **Biology**: short-range lateral **EXCITATION** (the `cortical_neighbour`
  edges) + the retained **global Argmax competition** (only the winner's
  neighbourhood learns; everything beyond is suppressed) = a **Mexican hat**.
- **`MapParams.lateral`** — the ablation is **graph DATA**, not a Python code
  path (PROTOCOL 0). `lateral=0` default ⇒ every committed result reproduces.
- **`domains/cortex_sheet.py`** — the adapter wires a 6×6 cortical sheet at
  **retinotopic** RF centres with symmetric `cortical_neighbour` edges.
  Retinotopy is **anatomy** (the same kind of positional fact as the retina's
  own grid adjacency, which `wave_world` already states), not something a
  learning rule discovers. The **orientation** map superimposed on it is what
  the graph must make.

## What each arm corresponds to IN THE ANIMAL (PROTOCOL 6)

`dark` was set to "no input" for two pre-registrations because the design was
not checked against the biology before running. So, explicitly:

| arm | what runs | the animal |
|---|---|---|
| `lateral=1` | waves only, no vision, lateral interaction ON | **a normal neonate before eye opening** — retinal waves + an intact cortical sheet with lateral connections. This is the ferret at P31–36, and equally the **dark-reared** ferret (dark-reared animals **keep their waves**). |
| `lateral=0` | waves only, no vision, lateral interaction OFF | **not an animal** — it is the *mechanism ablation*: the same neonate with cortical lateral interaction deleted. It is the control that isolates what the lateral connections do, and it is honest about being a lesion with no clean in-vivo counterpart. |

**Neither arm sees anything.** That is the point: the claim under test is that
the map is built by waves, with no vision at all. There is no `normal`/`sutured`
arm here and no video is loaded — visual refinement is rung 2's question, already
answered, and is not re-opened.

## The measure, and its CALIBRATION (PROTOCOL 1 — run BEFORE the agent)

**Per-unit preferred orientation** = the phase of the receptive field's spectral
second moment, halved: `0.5 * angle(Σ p·e^{2iθ})`. This is the **same complex
moment** whose MAGNITUDE is the committed `anisotropy` readout, so the map and
tuning readouts stay commensurable rather than introducing a second,
differently-behaved instrument.

**The statistic**, exactly:

```
smoothness = mean over cortically-adjacent unit pairs of |Δ preferred-orientation|
             (axial, mod 180°, in [0°, 90°]; 45° = chance)
null       = mean smoothness over 200 random PERMUTATIONS of unit positions
d          = smoothness − null          (degrees; NEGATIVE = smoother than chance)
```

The **shuffled-position null** is the right null: it destroys topography while
holding the tuning **distribution** exactly fixed, so no arm can win by being
more/less tuned in aggregate, or by every unit sharing one orientation (which is
not a map). Unit of analysis is the **SEED**.

**Calibration table** (`scripts/rung4_calibrate.py`, seeds 4200–4215):

| check | result | verdict |
|---|---|---|
| **A.** ideal Gabor, orientation readout | max error **0.08°** over 9 orientations | **PASS** |
| **B.** ideal (hand-built ramp) map | d = **−31.28** | **PASS** |
| **C.** RANDOM tuning (the noise check) | d = **+0.278 ± 0.872** (SEM, n=16) | **PASS** — sits at the null |
| **D.** duration confound (lateral=0) | 200:−5.68 → 800:−10.18 → 1600:−11.38 → **3200:−11.27** | **PASS ONLY AT THE FIXED POINT** |
| **E.** hand-built pinwheel (descriptive) | d = −21.78 | reference only |

**D is the one that bites, and it is reported honestly.** The statistic **does**
move with duration *through the transient* and then **plateaus** (1600→3200 moves
+0.11, well inside SEM 0.89) — exactly as anisotropy does. So the measure is
duration-confounded mid-transient and trustworthy **at the fixed point**. Both
arms are therefore run at **3200 steps**, at equal duration, at the plateau. This
is the same discipline that rescued rung 2 after nine failures.

## Convergence FIRST (PROTOCOL 2) — the check that explains nine failures

`scripts/rung4_convergence.py`, waves only, n=8 seeds (4100–4107),
drift = `‖w(t)−w(t−100)‖/‖w(t)‖`:

| steps | `lateral=1` anisotropy | drift | `lateral=0` anisotropy | drift |
|---|---|---|---|---|
| 0 | 0.156 | — | 0.156 | — |
| 200 | 0.210 | 0.292 | 0.186 | 0.276 |
| 400 | 0.269 | 0.096 | 0.222 | 0.103 |
| 800 | 0.315 | 0.040 | 0.261 | 0.044 |
| 1600 | 0.318 | 0.026 | 0.280 | 0.021 |
| 3200 | **0.337** | **0.026** | **0.292** | **0.018** |

**CONVERGENT + USEFUL, both arms**: anisotropy rises monotonically and flattens
at NON-ZERO structure while drift falls monotonically toward 0. **0/288 NaN
units.** The scaffold is a **STATE**, not a transient — so, unlike the nine
failed attempts, the arms are not being compared at an arbitrary point on a decay
curve. Adding the lateral rule did **not** destabilise Oja (η=5e-4, the measured
stable regime; 2e-3 diverges to NaN).

## Hypotheses — two, co-primary, conjunctive

Both two-sided; **SEED is the unit of analysis**; paired within seed (the two
arms share a seed, hence identical wave entropy and identical initial weights).

- **H1 — a map forms from waves alone, with NO vision.**
  `d_on = smoothness(lateral=1) − its shuffled-position null`, two-sided,
  predicted **< 0**.
- **H2 — the LATERAL INTERACTION is what makes it (the MECHANISM test).**
  `interaction = d_on − d_off`, two-sided, predicted **< 0**.

**Why H2 replaces the "H1b: d_off ≈ null" form.** The suggested H1b asked us to
*accept a null*, which no test can do, and the calibration has already **measured
that d_off is NOT null** (−11.27, check D): cortical neighbours have overlapping
receptive fields (retinotopy = anatomy), so they see partly-shared input and some
smoothness arises with no lateral interaction at all. **PROTOCOL 4 requires the
INTERACTION, not the simple effect, whenever the no-mechanism control is
non-null.** `d_off` is reported with its CI as a pre-committed descriptive, not
as a test. This is a design refinement made **before** the run and stated here.

**BUILT** iff **both** pass at **Bonferroni α = 0.025** each. Sign-flip
permutation, **20,000** perms; bootstrap CIs, 20,000 resamples.

## n — FIXED IN ADVANCE (PROTOCOL 3.3)

Pilot on **already-burned** seeds 4200–4215 (`scripts/rung4_pilot.py`, n=16):
`d_on` SD **1.796**, interaction SD **2.638**. Smallest effect of interest fixed
at **|δ| = 1.0°**. For 80% power, two-sided α=0.025: H1 needs n=31, H2 needs
n=67.

**n = 70. FIXED.** Confirmatory seeds **5000–5069** — never used for anything
(ledger, `VISION_PROTOCOL.md`). **Exactly two hypothesis tests. No sweeps. No
re-runs.**

## PREDICTION, STATED IN ADVANCE — with its provisos

**H1: PASS, and it is nearly worthless on its own.** I say so in advance so the
outcome cannot be dressed up: calibration check D already showed even the
*no-mechanism* arm scores −11.27, so `d_on < 0` is close to guaranteed. H1 is the
"**a map exists at all, from waves alone, with no vision**" claim — the ferret /
dark-rearing result — and nothing more. **It is not evidence for the lateral
mechanism.** H2 is.

**H2: PASS.** The mechanism: under hard global WTA exactly **one** unit learns
per step, so two cortically adjacent units are updated on *disjoint* steps from
*different* wave fronts and their orientations are coupled only by whatever their
overlapping RFs happen to share. Bursting the winner's neighbourhood makes them
learn **the same wave front on the same step**, which drives their weight vectors
toward a common component — smaller |Δθ| between neighbours. Pilot: −8.69.

**THE PROVISO THAT COULD BREAK — and it is a real confound, named now.** The
lateral rule **also raises mean selectivity** (convergence: 0.337 vs 0.292; pilot:
0.337 vs 0.288). A weakly-tuned unit's preferred orientation is a noisy readout of
almost-nothing, and noise pushes `d` toward 0 (calibration C: random tuning ⇒
d≈0). So a more-selective arm will score more negative **even with identical
underlying topography**, purely because its orientations are read out more
cleanly. **The interaction therefore cannot cleanly separate "neighbours
co-tune" from "better-tuned units are measured less noisily."** If H2 passes,
that ambiguity stands and must be reported as a limit on the claim, not buried.

**Pre-committed DESCRIPTIVE (NOT a test, no α spent):** mean selectivity per arm,
and the per-seed Pearson correlation between the selectivity gap
(`sel_on − sel_off`) and the interaction. If the interaction is driven mainly by
readout cleanliness, that correlation should be strongly negative and the honest
reading of H2 weakens accordingly. **Disentangling it is a NEW pre-registration
with its own mechanism-level hypothesis (PROTOCOL 5) — never a reinterpretation
of this data.**

## Decision rule, including what a null means

- **Both pass** ⇒ **rung 4 BUILT**: an orientation map forms from waves alone,
  with no vision, and the lateral interaction is what makes it — subject to the
  selectivity proviso above.
- **H1 passes, H2 nulls** ⇒ **NOT BUILT**. The topography would be an artifact
  of retinotopic RF overlap (anatomy the adapter wired), not something the graph
  made. The lateral mechanism would be **refuted** as the cause and the rung
  would stay open. This is a real possible outcome and would be reported as the
  headline.
- **H1 nulls** ⇒ **NOT BUILT**, and the measure or scaffold is broken (given
  check D, this would be surprising and would need diagnosis before anything
  else).
- **H2 passes in the WRONG direction** (lateral makes the map *rougher*) ⇒
  **NOT BUILT**, reported as such. Four predicted directions in this arc were
  already wrong.

## What is NOT claimed, whatever the outcome (PROTOCOL 8)

- **NO pinwheels or singularities.** A 6×6 sheet over a 16×16 retina cannot
  resolve one. None is measured and none will be claimed.
- **The map layout is not claimed to be pre-specified** — the research killed
  that 0-3.
- The neighbourhood kernel is a **top hat** (binary, radius 1, fixed), not a
  graded Gaussian that shrinks over training.
- **Retinotopy is wired by the adapter**, not learned. Only the *orientation*
  map is at stake.
- This licenses **nothing** about which biological mechanism is correct — the
  verified research refuted the Hebbian-vs-sparsity question **0-3**.

---

# OUTCOME (run 2026-07-16/17, exactly as specified)

```
RUNG 4 CONFIRMATORY — n=70 seeds (5000-5069), 3200 steps, waves only, 6x6 sheet, oja eta=0.0005

THE TWO PRE-REGISTERED TESTS (Bonferroni alpha=0.025 each):
H1  d_on                           -20.1576   95% CI [-20.7197, -19.5505]   p = 0.0000   n = 70
H2  interaction (d_on - d_off)      -6.9124   95% CI [ -7.4593,  -6.3707]   p = 0.0000   n = 70

  H1 PASS   H2 PASS
  DECISION: *** BUILT ***

PRE-COMMITTED DESCRIPTIVES (not tests, no alpha spent):
  d_off (the ablation arm)         -13.2452   95% CI [-13.8814, -12.6036]   p = 0.0000   n = 70
  mean selectivity                 on 0.3314   off 0.2869   gap +0.0445
  corr(selectivity gap, interaction) r = -0.081

  arms: d_on -20.16 | d_off -13.25  (degrees; 0 = chance, negative = smoother than chance)
```

# **DECISION: *** BUILT *** — an orientation map forms from WAVES ALONE, with NO vision.**

Both co-primary hypotheses pass the conjunctive gate (Bonferroni α=0.025 each),
on a **stable scaffold** (drift 0.026, measured before the run), with a
**calibrated measure** (ideal Gabor 0.08° error; random tuning at the null), at
**equal duration at the fixed point**, on **fresh seeds**, from a
**pre-registration committed before the run**.

| arm | d (degrees) | reading |
|---|---|---|
| `lateral=1` (waves, no vision) | **−20.16** | the map |
| `lateral=0` (mechanism ablated) | **−13.25** | retinotopic RF overlap alone — **NOT null**, as calibration predicted |
| **interaction** | **−6.91** | **what the lateral interaction itself contributes** |

## Did the in-advance prediction hold? YES — including the part that said H1 was worthless

- **H1: predicted PASS, and predicted in advance to be "nearly worthless on its
  own."** Both held. d_on = −20.16 (p<0.0001) — but the *ablated* arm also scores
  −13.25, so **65% of H1's effect is present with the mechanism switched off**.
  H1 alone would have been a result about anatomy the adapter wired. Stating this
  before the run is what stopped it becoming the headline.
- **H2: predicted PASS (mechanism: under hard global WTA exactly one unit learns
  per step, so neighbours are updated on disjoint steps from different wave
  fronts; bursting the winner's neighbourhood makes them learn the same wave
  front on the same step).** Held: **−6.91, CI [−7.46, −6.37], p<0.0001.**
  Pilot −8.69 → confirmatory −6.91: same direction, somewhat smaller, both far
  outside the |δ|=1.0° smallest effect of interest.

## THE PRE-COMMITTED CONFOUND — it is NOT dissolved, and it is part of the claim

The pre-registration named this in advance: the lateral rule **also raises
selectivity** (0.331 vs 0.287, gap **+0.0445**), and a weakly-tuned unit's
preferred orientation is a noisy readout, so a more-selective arm scores more
negative **even with identical underlying topography**.

**The pre-committed descriptive:** `corr(selectivity gap, interaction) = −0.081`
— essentially zero. Across seeds, **how much lateral boosted selectivity does not
predict how much it smoothed the map.** This test had power, not restricted
range: the gap's SD is 0.0240 over [−0.0037, +0.0997], a **54% CV**. If
readout-cleanliness were the driver, seeds with a bigger selectivity boost should
show a bigger interaction. They do not.

**But that does NOT dissolve the proviso, and the following is reported because
suppressing it would be the forking-paths failure this project has already
committed once.** While assessing whether the pre-committed correlation had any
power, two **POST-HOC, NOT-PRE-COMMITTED, NOT-TESTS** correlations were computed:

```
corr(sel_on,  d_on)  = -0.650      corr(sel_off, d_off) = -0.257
```

**Within an arm, more-selective seeds do score more negative — the confound
mechanism is REAL and live, not hypothetical.** These two numbers are exploratory
and carry no α; they are recorded only because they bear directly on how the
result may be read.

**So the honest position is a split, and the claim carries it:** the confound
demonstrably operates on `d` (within-arm r=−0.650), while the pre-committed
between-seed test found the interaction does **not** track the selectivity boost
(r=−0.081, with range). **H2's effect is therefore not attributable to
readout-cleanliness by the evidence available, but neither is a mean-level
contribution excluded** — a constant +0.0445 selectivity boost could contribute a
constant amount to the interaction while producing no across-seed correlation.
**Disentangling this requires its own prospective pre-registration with its own
mechanism-level hypothesis (PROTOCOL 5) — e.g. a selectivity-matched comparison,
or a lateral variant that co-tunes without raising selectivity. It is NOT
attempted here, and this data is NOT reinterpreted to settle it.**

## WHAT IS CLAIMED

**An orientation map forms from the agent's own retinal waves, with no visual
input of any kind, and the lateral interaction is what makes it — subject to the
selectivity ambiguity above.** This is the ferret / dark-rearing result
(Chapman/Stryker/Bonhoeffer 1996; White/Coppola/Fitzpatrick 2001): maps emerge
without visual experience. The mechanism is graph data (`vm_burst_lateral`), the
ablation is graph data (`MapParams.lateral`), and the decision of which units
burst is an Argmax in a seed rule — no Python decides anything.

## WHAT IS **NOT** CLAIMED (PROTOCOL 8)

- **NO PINWHEELS. NO SINGULARITIES.** None is measured and none is claimed. A
  **6×6 sheet of 36 units over a 16×16 retina cannot resolve a pinwheel** — the
  claim is *smoothness* (neighbours prefer similar orientations), which is a far
  weaker property than the pinwheel/fracture topology real V1 shows.
  `test_known_gaps_are_pinned` fails if a pinwheel statistic ever appears.
- **The map is not claimed to be pre-specified in layout** — the research killed
  that claim 0-3, and nothing here speaks to it.
- **Retinotopy is WIRED BY THE ADAPTER, not learned** — and it is doing real work:
  the ablated arm scores −13.25 on RF overlap alone. Only the **−6.91
  interaction** is attributable to the graph's lateral mechanism; the larger part
  of the raw smoothness is anatomy.
- **Not Gabors.** Mean selectivity 0.331 vs an ideal Gabor's 0.867 (rung 2's
  scope statement stands unchanged).
- The neighbourhood kernel is a **top hat** (binary, radius 1, fixed), not a
  graded Gaussian shrinking over training. Real cortex is neither.
- **The `lateral=0` arm is a lesion, not an animal** — it has no clean in-vivo
  counterpart, and was labelled as such before the run.
- **This licenses nothing about which biological mechanism is correct** — the
  verified research refuted the Hebbian-vs-sparsity question **0-3**. It shows
  *this* rule on *this* scaffold produces map smoothness from waves.
- **n=70 seeds, one 6×6 sheet, one retina size, one η.** No claim of robustness
  across scales; none was tested (and testing it would be a new pre-registration,
  not a sweep on this one).
