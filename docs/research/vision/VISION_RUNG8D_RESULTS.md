# RUNG 8D — THE PROBE IS CALIBRATED, PROSPECTIVELY. AND ITS FLOOR IS A LOTTERY.

*§1/§2 CALIBRATION + the pre-registered CONFIRMATION of it. **H1/H2 are NOT in
this file** — they are rung 8E's, and this rung is what licensed them.*

**Engine `a06584eaa362`** @ `<this worktree>/runners/dsl/python/substrate_rs/_native.abi3.so`
— **`own` build**, built by `scripts/engine_build.sh` **in this worktree**
(§11.5; the brief's warning that an agent turned another's provenance gate RED by
rebuilding canonical). **Base commit `de5f96b8`** — rung 8C's `d4bb1781` is an
ancestor. **This rung adds NO Rust; no seed is edited; no constant is introduced.**
`tests/test_engine_provenance_migrated.py` **7/7**. §9 bench via the named
selector `scripts/rung7_vision_bench.sh`: **190 passed / 10 skipped** — the
brief's stated baseline, unchanged.

**PROVENANCE OF THE TREE ITSELF, recorded because it nearly went wrong again:**
this worktree was based on **`3edc2888`** — **behind the tip and missing rung 8C
entirely** (`d4bb1781` was not an ancestor; no `VISION_RUNG8C_RESULTS.md` on
disk). That is the seventh occurrence of the base error the brief warns about.
**Rebased onto `de5f96b8` before any measurement**, never merged (§: "REBASE onto
the tip; NEVER merge a stale branch"). Had I not checked, every number below
would have been measured against a tree that did not contain the rung it was
correcting.

---

## 0. THE HEADLINE

**Rung 8C's 1.0000 REPRODUCES PROSPECTIVELY — and its three open items are
CLOSED, one of them by dissolving the question.**

Pre-registered in `VISION_RUNG8D_PREREG.md`, **committed at `fd0c2107`,
10:32:00Z**; the confirmation run started **10:32:06Z** and ended **10:36:41Z**.
The ordering is checkable in git, which is what §3 means by COMMITTED and what
8C honestly recorded it did not have.

**Fresh seeds 6100–6107 (n=8), declared in the prereg, never used for anything.
Seeds 13000–13999 NOT touched by this rung.**

| statistic | mean | sd | **95% CI (the gate reads the CI, not the point)** | 8C's n=1 point |
|---|---|---|---|---|
| **IDEAL** | **0.9989** | 0.0016 | **[0.9975, 1.0003]** | 1.0000 ✓ inside |
| **FLOOR** | **0.2691** | 0.0877 | **[0.1933, 0.3450]** | 0.2304 ✓ inside |
| **SEPARATION** | **0.7298** | 0.0887 | **[0.6530, 0.8065]** | 0.7696 ✓ inside |

| gate | verdict | value |
|---|---|---|
| G1 IDEAL ≥ 0.80 (CI lower) | **PASS** | 0.9975 |
| G2 FLOOR ≤ 0.50 (CI upper) | **PASS** | 0.3450 |
| G3 SEPARATION ≥ 0.30 (CI lower) | **PASS** | 0.6530 |
| G0 no dead arm (`n_dead == 0`, every arm, every seed) | **PASS** | 0 dead |
| G4 weights frozen (`max|dw| == 0` exactly) | **PASS** | 0.0e+00 |

**The gate is stricter than 8C's**: every threshold is cleared by the **CI**, not
by a point estimate at n=1. **My pre-registered predictions were accurate** — I
predicted FLOOR CI upper ≈ 0.35 (measured **0.3450**) and SEPARATION CI ≈
[0.62, 0.82] (measured **[0.6530, 0.8065]**), and I explicitly predicted **8C's
exact digits would NOT reproduce** because the floor has sd 0.1091 across seeds.
They did not, and the gate did.

---

## 1. OPEN ITEM 1 — THE CALIBRATION NOW HAS THE PROSPECTIVE PREREG IT OWED

8C's own disclosure: *"'written before' is not 'committed before'"*, plus an
ordering hazard it flagged against itself (it saw the sweep's window at ~2.1
before measuring the rule land at 2.168).

**What I could repair, and what I could not.** I committed the pre-registration
before the run and confirmed on seeds nobody had measured. **I could not un-know
8C's answer** — I knew the target before I declared the prediction, and the
prereg says so in those words. **This is a weaker prospectivity than if 8C had
written the file first, and it is recorded as a limitation rather than argued
away.** What it does establish: the gate is not a property of seed 0.

## 2. OPEN ITEM 2 — SEPARATION IS BY **SELECTIVITY**, NOT DRIVE. PROVEN.

The brief: *"Your calibrated probe must be shown to separate by SELECTIVITY.
Prove it — do not inherit it."*

**8C's drive verdict is TRUE — and it is a fact about a GLOBAL theta, which does
not transfer to rung 6's PER-CELL rule.** Nobody had asked the per-cell question.

**(a) The readout is EXACTLY scale-invariant in the drive.** Analytically:
`act` is a linear Fold over weights, `theta`'s EMA is linear in `act` with init
0, so scaling every weight by `k` gives `act→k·act`, `theta→k·theta`,
`rate→k·rate`, and `osi = (a−b)/(a+b)` **cancels `k` exactly**. **Measured, not
asserted** (`rung8d_scale_invariance.py`, 9.51× scaling):

| | max relative deviation |
|---|---|
| weights scale | 2.220e-16 |
| theta scales | 4.441e-16 |
| **tuning curves scale** | **5.55e-16 (settle=0), 1.005e-13 (settle=2000)** |

**A per-cell EMA theta divides the 9.5× drive gap out by construction. That is
exactly what a global theta cannot do.**

**(b) The drive-matched control — which 8C never ran.**

| arm | drive | OSI | verdict |
|---|---|---|---|
| A1 ideal ×1 | 2.1854 | 0.9912 | |
| A2 ideal ×9.51 | **8.7435** | 0.9909 | **VOID — see below** |
| A3 floor ×1 | 20.8076 | 0.1420 | |
| A4 floor ×1/9.51 | **2.1874** | 0.1912 | matched to A1 within **0.09%** |

**SEPARATION AT MATCHED DRIVE: A1 − A4 = 0.8000** (drives 2.1854 vs 2.1874),
versus **0.8491 unmatched**. **The 9.5× drive gap carries NONE of the
separation** — there is no drive difference left to carry it.

**A2 VOIDED ITSELF AND I REPORT IT AS VOID, NOT AS A PASS.** Scaling the ideal
cell UP hit `oo_wmax = 2.0` clipping (`max|dw| = 7.5 ≈ 9.51 − 2.0`), so its drive
landed at 8.74 instead of 20.75 and its RF was **distorted, not scaled**. **The
arm's own pre-registered proviso 2 fired against it** (*"the match failed and
A2-vs-A3 is not a matched comparison — the arm is void, not passed"*). A1-vs-A4
is the clean matched pair and needs no A2.

## 3. OPEN ITEM 3 — BOTH INSTRUMENT FACTS, EXPLAINED

### 3.1 ALIVENESS 8.33/12 — NOT A DEFECT. IT IS WHAT AN EMA THRESHOLD MUST DO.

Read off the two seed rules:

    rate  = max(act - theta, 0)                    (`oo_sunit_rate`, THE ICEBERG)
    theta <- theta + theta_rate*(act - theta)      (`oo_sunit_adapt_theta`)

`theta` settles at **E[act] over the ensemble it is settled on**, per cell. So
every orientation whose `act` lies below the cell's **own mean** at all 16 phases
is silenced. **Roughly half a cell's orientations sit below its own mean, by
construction.** 8.33/12 is arithmetic, not death.

**`n_dead = 0` on EVERY arm of EVERY pathway** — the decisive column, which no
rung had reported (`rung8d_percell_audit.py`, per CELL not the mean). **§1.1's
divide-guard fires NOWHERE in this pathway.** 8C's G0 passed for the right
reason, though it read a mean that *could* have hidden a dead cell.

**And the IDEAL's 11/12 is SELECTIVITY ITSELF**: `tc_orth = 0.0000` on all 6
cells — a perfect split-Gabor is silent at exactly the orthogonal orientation.
**Silence at exactly one orientation is what a textbook simple cell IS.**

**MY PREDICTION HERE WAS WRONG, AND I RECORD IT.** I predicted the 8.33 hid a
MIXTURE containing dead cells (`osi = 0.0000` via §1.1's divide-guard) averaged
against orthogonally-silenced ones (`osi ≈ 1.0`). **`n_dead = 0` everywhere
killed that.** The mixture story was wrong; the arithmetic story is right.

### 3.2 FLOOR 0.2304 < 0.3105 — THE QUESTION DISSOLVES. IT WAS NEVER APPLES-TO-APPLES.

**0.2304 is lateral / PROBE-settled. 0.3105 is degenerate / WAVES-settled.**
Different pathways **and** different protocols. Under **matched** protocol:

| pathway | floor, θ on WAVES | floor, θ on PROBE |
|---|---|---|
| lateral (composed) | 0.0205 | **0.2304** |
| degenerate (rung 6) | **0.3105** | **0.5352** |

**Under the matched (probe-settled) protocol the composed floor is 0.2304 vs the
degenerate's 0.5352 — the composed floor is LOWER, which is the good direction
(more headroom), and there is no anomaly to explain.** 8C compared across the
diagonal of its own table.

**And the deeper answer: neither number is a stable quantity — see §4.**

## 4. THE NEW §1-CLASS DEFECT — **THE FLOOR'S OSI IS A LOTTERY**

*Found while chasing an anomaly I could not explain from theory and refused to
hand-wave. It is the most important thing in this file.*

The pilot's A3 (0.1420) and 8C's identical arm (0.2304) differ **only** in 200
extra settling steps. And A3-vs-A4 differ by 0.049 **while their tuning curves
agree to 1e-13**. Both cannot be true unless something discontinuous sits between
`tc` and `osi`. **It does: `argmax`.**

**The floor's tuning curve contains EXACT TIES between distinct orientations:**

    cell 0:  tc[30°] == tc[150°] == 1.057486     (top1−top2 relative gap 4.2e-16)
             tc[60°] == tc[120°] == 0.598743
    5 of 6 floor cells have a top-2 relative gap of 3.5e-16 … 1.2e-15

**MEASURED CAUSE — an ALIASING DEGENERACY OF THE PROBE'S OWN DISCRETISATION.**
`tc` is **F0: a mean over the 16 probe phases**. At exactly the orientations
where `cos θ` or `sin θ = ±0.5` — i.e. **30/150 and 60/120** — the per-pixel
phase increment is exactly `2π·0.5/4 = π/4`, which is **2 of the 16 phase
samples**. So a unit translation on the integer grid **IS** a phase shift, and a
**phase-AVERAGED** statistic is exactly translation-invariant there. The mirror
orientations then tie **exactly**. It is a property of `period 4 × K=16 phases ×
integer grid × 15° steps` — **not of the cortex**. (Positive-controlled: the
stimulus patterns are all 12 distinct, at frame scale AND at RF scale — the
degeneracy is created by the phase AVERAGE, not by the stimuli.)

**The consequence, traced end-to-end on one cell:** `osi()` reads `argmax` and
its **orthogonal**. When the argmax is a tie, the two winners have **different
orthogonals with different values**:

    cell 2:  argmax 8 → orth 2 (0.7285) → osi 0.0789
             argmax 4 → orth 10 (0.4502) → osi 0.3093
    …decided by float rounding at 1e-16.

**THE IDEAL ARM IS IMMUNE** — its tuning curve has REAL gaps (top1−top2 relative
gap **0.15–0.28**), so no tie, no lottery. **That is why it is 0.9999 ± 0.0005
across 14 seeds while the floor's sd is 0.1091.**

**This is §1.1's disease in a THIRD costume.** §1.1: *"an absence off a GUARDED
DIVISION is evidence of a LOOKUP, not of a measurement."* Here: **an OSI off an
ARGMAX over EXACT TIES is evidence of a LOTTERY, not of a measurement.**

**I did NOT fix the measure** (§5: never rescue by changing the readout; and the
gate passes as-is). A tie-aware OSI — circular variance, averaging over tied
argmaxes, or an orientation step co-prime with the grid — is a **NEW MEASURE
requiring its OWN prospective pre-registration**, and it would move **every
committed OSI in this arc**. **Named as the next rung's business; deliberately
not done here.**

## 5. §2, APPLIED TO THE RULE THE WHOLE GATE RESTS ON

**Never run before for theta on the probe ensemble**, though §2 says run it
FIRST. Composed pathway, weights frozen, both arms spanning the identical
duration (§1.2):

| settling steps | IDEAL | FLOOR | separation |
|---|---|---|---|
| 400 | 0.9976 | 0.2044 | 0.7931 |
| 2000 | **1.0000** | **0.2304** | **0.7696** ← 8C read here |
| 3200 | 0.9918 | 0.1760 | 0.8158 |
| 4800 | 1.0000 | 0.1694 | 0.8306 |
| 6400 | 1.0000 | 0.2324 | 0.7676 |

- **theta NEVER stops fluctuating**: `max|dθ|` = 0.10–0.54 out to 6400 steps. It
  converges in MEAN and wobbles around it forever — an EMA on a stationary
  ensemble does exactly that.
- **The FLOOR's OSI wobbles over a range of 0.0630** at steps ≥ 2000; **the IDEAL
  is flat (range 0.0082).** The asymmetry is §4's lottery: theta's wobble
  re-rolls the argmax tie on a flat curve and cannot touch a peaked one.
- **The GATE's VERDICT is duration-robust — it passes at EVERY checkpoint from
  400 to 6400.** The floor's **VALUE** is not.

**Honest form:** the probe is calibrated **as an instrument whose floor is a wide
random variable**, at a settling duration **declared in advance (2000)**. Duration
is not the independent variable and both arms span it identically (§1.2).

## 6. THE PILOT — AND THE NUMBER THAT MATTERS FOR EVERYTHING DOWNSTREAM

`rung8d_pilot_variance.py`, **burned seeds 0–13** (rung 8 §5's own declared pilot
block), n = 14, unit of analysis = **SEED** (§4):

| arm | mean | **sd (per seed)** | min | max |
|---|---|---|---|---|
| IDEAL | 0.9999 | **0.0005** | 0.9980 | 1.0000 |
| FLOOR | 0.2754 | **0.1091** | **0.0620** | **0.4618** |
| SEPARATION | 0.7244 | 0.1092 | 0.5382 | 0.9380 |

**THE FLOOR'S PER-SEED sd IS 0.1091 = 1.8× THE SESOI (0.0595).**

**8C measured n = 1**, and §4 is explicit that the unit of analysis is the SEED.
So **8C's 0.2304 is one draw from a distribution spanning 0.062 → 0.462**. It
happened to be a typical draw (the confirmation mean is 0.2691). **It could have
been 0.4618, and G2's threshold is 0.50.**

## 7. §13 — WHAT FELL OUT, WHAT WENT IN

**This rung introduces NO constant, so §13 has nothing to bite on.** Rung 6's
`theta_rate`, `eta`, `oo_wmax` and placement are untouched; no seed is edited; no
Rust. **θ ≈ 2.17 FALLS OUT** of the cell's own EMA of its own drive under the
ensemble it responds to. `n = 8` **falls out** of the pilot's measured sd.

### §13.1 — COULD THIS HAVE PRODUCED THE OPPOSITE? **YES, AND IT NEARLY DID.**

- **G2's margin is thin and the pilot proves it**: the worst pilot seed hit
  **0.4618** against a 0.50 threshold. A fresh block drawing from the upper tail
  would have failed G2 outright, and I declared the seeds before seeing them.
- **The drive-matched control was built to collapse if the separation were
  drive-carried.** It did not collapse — but the arm that would have shown it
  **voided itself** on clipping, exactly as its proviso predicted it might.
- **My own §3.1 prediction (the dead-cell mixture) was FALSIFIED** by `n_dead = 0`.

**What no rule here is solely responsible for:** whether wave-drive and
probe-drive agree is a property of **rung 7's retina being a predictive coder** —
earned two rungs ago, not consulted. Had rung 7's channels driven waves and
gratings equally (as rung 6's do, ratio 0.96), this protocol would have changed
**nothing**, which is exactly what the degenerate column shows.

## 8. WHAT THIS DOES **NOT** CLAIM

- **NOT that waves develop orientation selectivity.** This calibrates the **PROBE
  ONLY**. H1/H2 are rung 8E's.
- **NOT that the cross-pathway G2 failure is resolved.** 8C's §4.2 stands: on the
  **degenerate** pathway, probe-settling gives floor **0.5352 > 0.50** and G2
  FAILS there. **This rung's gate is the composed pathway only** — and §4 now
  suggests that 0.5352 may itself be a lottery draw, which is a reason to
  **distrust it**, not a reason to dismiss it. Unresolved; named.
- **NOT that the 9.5× drive gap is fixed.** It is untouched. It is *divided out*
  by a per-cell theta at the READOUT, which is a different claim.
- **NOT that the measure is sound.** §4 says the opposite: the floor is a
  lottery. The gate passes **despite** it, because the IDEAL is exact and the
  separation is ~13× the floor's sd.
- **NOT that rung 6's negative is overturned.** Untouched.

## 9. NAMED NEXT — each needing its own PRE-REGISTRATION

1. **H1/H2** — now licensed. `VISION_RUNG8E_PREREG.md`, seeds 13000–13015.
2. **A TIE-AWARE OSI** (§4). The current one is a lottery on flat curves. Any fix
   is a new measure needing a prospective prereg, and it would move every
   committed OSI in this arc. **This is the highest-value instrument work left.**
3. **The cross-pathway G2 failure** (§8) — a θ protocol passing on both
   pathways, or an argued reason why it need not.
4. **The §2 non-convergence of the LEARNING rule** — there is **no η at which it
   is both convergent and load-bearing** (rung 8E §3 measures this). That is a
   finding about the rule and it is upstream of every arm.
