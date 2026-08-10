# RUNG 8 — COMPOSE THE EYE WITH THE CORTEX

*Pre-registration of the CONFIRMATORY run, committed before it (PROTOCOL §3).*

**Precisely what predates what, so this document does not overclaim.** The
protocol's own order is: convergence (§2) → calibrate the measure + positive
control (§1) → **pre-register and commit** → ONE confirmatory run. So the
**gates below ran first, by design** — they are what decides whether a
confirmatory run may happen at all. Sections **1–8 pre-register the confirmatory
run** (its hypotheses, statistic, seeds, decision rule and my prediction), and
that run **was never executed**: the calibration gate failed, proviso 4 fired,
and the rung stopped. **Seeds 13000–13999 are untouched.** Nothing in §§1–8 was
written or revised with a confirmatory result in hand, because there is none.

**Engine:** `95167c01b7b3` @ `runners/dsl/python/substrate_rs/_native.abi3.so`
(shared build; Rust source byte-identical to the canonical tree — verified by
`domains.engine_provenance`, PROTOCOL §10.1).
**Commit:** rung-8 work is on top of `4aaccb9800`.
**Init:** `w0 = 1.0` (the default) on every number, and `w0 = 0.0` reported
alongside wherever a floor is measured — see §7.
**Selector:** explicit file lists only. `-k vision` is a substring trap
("pro**vision**al") — PROTOCOL §12.

---

## 1. What this rung is

Rung 7 named it: *"feed these channels to rung 6's SUnit layer and re-run its
convergence gate — the two seeds were deliberately never composed."*

- **Rung 6 FAILED** on the **degenerate** split: `x_OFF = 1 − x_ON` forces
  `C_ON,OFF(d) = −C_ON,ON(d)` **identically**, so the channels carry **no
  independent correlation structure**. Waves developed nothing (OSI 0.283 →
  0.329 against a 0.3168 floor; η=5e-4 ran away, η=1e-4 stable but empty).
  Miller 1994 needs correlations with **different spatial dependence**.
- **Rung 7 supplies exactly that**: the degeneracy breaks (SD 0.3601, 76.3% of
  range, p=3.6e-08; σ_ON,ON 1.627 vs σ_ON,OFF 3.264, **ratio 2.007**), and
  centre-surround **emerged** from `lat_g0=0.0` (CS 1.0839).
- **Rung 6 also established** that the **threshold**, not the split, makes a
  response signed (ideal cell OSI 0.0006 → **0.9115**, same weights).

**So: compose them, and re-run rung 6's own convergence gate and OSI measure,
UNCHANGED. This tests whether the precondition was the blocker.**

Rung 7 explicitly does **not** claim that learning breaks the degeneracy (a
fixed surround breaks it just as well) and claims **no orientation
selectivity** — *"a precondition is not a result."*

## 2. The composition — and the finding that it needs NO rule

`seeds/vision_compose.json` (new). **`seeds/vision_lateral.json` and
`seeds/vision_onoff.json` are NOT edited: compose, don't modify.**
`compose = 0.0` default ⇒ inert; every result committed before rung 8
reproduces byte-identically.

The seed adds **no rule to either seed**, and that is a finding rather than a
shortcut. Rung 6's SUnit rules bind their presynaptic channel by an **untyped**
edge traversal (`["b", "oo_pre", "sy"]`) and read only `bursting` + `bstep` off
it — the string "Bipolar" occurs in `oo_sunit_activate` and `oo_learn_sub`
**only in their comments**. Rung 7's `LBipolar` carries both attrs and
`lat_bipolar` sets both. **The cortex is grain-agnostic about which retina feeds
it.**

So the composition is exactly **one admissibility statement** — a production
declaring `LBipolar -[oo_pre]-> OOSynapse` — plus the `ComposeParams` node that
makes the arm the agent's own configuration (PROTOCOL §0). Γ **rejected** the
edge until that production existed (`InadmissibleEdge: Γ rejects (LBipolar)
-[oo_pre]-> (OOSynapse)`), which is the substrate enforcing its own grammar.

Verified before use, not assumed: `scripts/rung8_compose_check.py` — both arms
activate and learn, identical synapse counts (98/unit), and the pre types are
`{LBipolar}` / `{Bipolar}` respectively.

## 3. Hypotheses (two-sided)

- **H1** — SUnits on rung 7's decorrelated channels become orientation-selective
  in RESPONSE: OSI ≫ the **lateral untrained floor measured in this run**.
- **H2 (the ablation that makes it a test)** — on the **degenerate** split, OSI
  stays at **its own** floor, reproducing rung 6's negative as the control.
  **The control must be verified actually null** (rung 4's was not).

Two-sided: an OSI *below* the floor is as reportable as above (rung 3's `strobe`
dissolved an innate bias *below* the floor, and only an `untrained` arm caught
it).

## 4. The statistic, exactly

Mean OSI per **SEED** (PROTOCOL §4 — the unit of analysis is the seed, never the
unit: units share input and compete under WTA, so they are not independent).
Rung 5's calibrated probe via rung 6's wrapper (`osi_of`, `key="rate"`),
**frozen**, unchanged — rectification, period-4 anti-aliasing, phases in
isolation, F0 tuning.

Because the two arms have **different floors**, the arms are **not** compared
directly. The test is the **lift over each arm's own untrained floor**, and —
since the degenerate control is emphatically **non-null** (floor ≈ 0.33) — the
pre-registered test is the **INTERACTION** (PROTOCOL §4: *test the interaction,
not the simple effect, whenever the no-mechanism control is non-null*):

    Δ_arm        = OSI(trained, arm) − OSI(untrained, arm)     [paired, per seed]
    INTERACTION  = Δ_lateral − Δ_degenerate

## 5. Floors, SESOI, n

**The floor is measured in THIS run, per arm and per init, as a reported arm.**
It is **not** inherited: OSI's random floor is init-dependent (0.0044 DC vs
0.3899 signed — 89×, same probe; the w0 ablation) and rung 6's 0.3168 is a third
value. A "lift" below its own untrained floor is not a lift — that is how rung
5's zero-mean arm's apparent 0.3665 evaporated.

**SESOI: 0.0595** (rung 6's, adopted unchanged — it is the same layer and the
same probe).

**n:** fixed in advance by a power analysis on a pilot restricted to
**already-burned** seeds (0–13, 3000). **Confirmatory seeds: 13000–13999**,
never used for anything (ledger appended in `VISION_PROTOCOL.md`).

## 6. Decision rule

- **H1 CONFIRMED** iff Δ_lateral > SESOI with a CI excluding 0 **and** the
  interaction CI excludes 0.
- **H1 NULL** ⇒ decorrelated input is **not sufficient**, and **rung 6's
  negative deepens**. That is a **finding**, not a failure: it would locate the
  blocker somewhere other than the channels' correlation structure.
- **H2 must be null.** If the degenerate arm is *not* null, the control is
  invalid and neither hypothesis is interpretable.
- **Exactly the listed tests. No sweeps. No re-runs.** A further attempt needs a
  NEW pre-registration with a NEW **mechanism-level** hypothesis — never a
  parameter search. η, RF, period, `lat_eta`, `gmax` are FROZEN.

## 7. The `w0` question — answered by measurement, in this world

The supervisor asked that a rung minting Units be run at `w0=1.0` and `w0=0.0`,
or state why not. This rung mints **SUnits** — rung 6's layer — and the
w0-ablation agent established on that **identical** layer that the ablation is
**architecturally empty**. That is inherited reasoning, so it is **re-measured
here** rather than trusted (§7 of this file is a *measurement*, not a citation):

All numbers below are on a **developed** retina (§G), n=8 burned seeds, this run:

| `w0` | effective RF (`w⁺−w⁻`) DC power fraction | frac(w<0) | untrained OSI — lateral | untrained OSI — degenerate |
|---|---|---|---|---|
| 1.0 | **0.032671** | **0.4320** | 0.0174 ± 0.0055 | 0.3316 ± 0.1141 |
| 0.0 | **nan** (zero-power RF) | 0.0000 | 0.0162 ± 0.0062 | **0.0000 ± 0.0000** |

- At `w0=1` there is **no DC prior to ablate**: the effective RF is already
  zero-mean (DC fraction 0.033, not ~1.0) and **already signed** (43.2%
  negative), because ON and OFF start at the same `w0` with independent jitter.
- At `w0=0` the effective RF is **identically zero** (`max(0·(1+jitter), 1e-3)`
  = 1e-3 for *every* synapse, so `w⁺−w⁻ ≡ 0`; DC fraction is `nan` on a
  zero-power RF, and the degenerate arm's untrained OSI is **exactly** 0.0000).
  **`w0=0` is not an init variant — it is a dead layer**, and it deletes the
  symmetry-breaking jitter WTA needs.
- A *signed* init is forbidden by the **architecture**, not by taste:
  `oo_learn_sub` clips every weight to `[0, oo_wmax]` (Dale's law, a rule the
  agent holds). A negative initial weight is a state the first rule firing
  deletes.

**So both inits are reported, and neither is a DC-prior ablation, because this
layer has no DC prior in the quantity its rules and its probe both read.**

## 8. My prediction, stated in advance, with its provisos

**I predict H1 is NULL** — OSI stays near the lateral floor — and that the
composition therefore deepens rung 6's negative rather than rescuing it.

Reasoning: rung 3 and rung 5 both died on the SAME cause, stated twice in the
ladder — **Oja's fixed point is the leading PC of the time-averaged covariance,
and a contraction to the mean of an ISOTROPIC distribution is the mean.** Rung 7
gives the channels different spatial dependence *radially*, but the wave
ensemble remains **orientation-isotropic**: decorrelation removes a redundancy,
it does not install an anisotropy. Miller 1994 needs the correlation structure
*plus* competition that breaks the orientation symmetry; rung 7 supplies the
former only.

**Provisos — each of which, if it breaks, tells me what I did not understand:**

1. **If H1 confirms**, my model of "isotropic ⇒ no orientation" is wrong at the
   level of the *pair* of channels: the ON/OFF **relative** geometry, not the
   marginal ensemble, would be what carries orientation — which is closer to
   what Miller actually claims than my reading of it.
2. **If the degenerate control is NOT null**, the interaction is the only
   interpretable quantity and the simple effects must be discarded.
3. **If the composed system fails the CONVERGENCE gate**, nothing above is
   testable and the rung stops there (rungs 5, 6 and phase 0 all correctly
   burned no seeds when their gates failed).
4. **If the ideal-cell target on the composed pathway is not high**, the probe
   is not valid on this pathway and NO arm is interpretable — the rung stops at
   the calibration gate, per PROTOCOL §1.

---

# OUTCOME — **STOPPED AT THE CALIBRATION GATE (PROTOCOL §1). PROVISO 4 FIRED.**

**No confirmatory arm was run. Seeds 13000–13999 are ALLOCATED, UNUSED and still
CLEAN.** H1 and H2 are **NOT TESTED** — and the reason is itself the result.

**Engine `95167c01b7b3`, commit `4aaccb9800`, init `w0=1.0`, selector: explicit
file list.**

## A. The composition is BUILT and VERIFIED

`scripts/rung8_compose_check.py`, both arms, identical anatomy (98 synapses/unit):

| arm | pre type | max \|act\| | max rate | max \|dw\| / 200 steps |
|---|---|---|---|---|
| lateral (rung 7's channels) | `{LBipolar}` | 21.386 | 6.9996 | 1.82e-01 |
| degenerate (rung 6's) | `{Bipolar}` | 49.572 | 0.7713 | 5.81e-02 |

The cortex **activates and learns on both retinas, with no rule added to either
seed** — one production (`LBipolar -[oo_pre]-> OOSynapse`) is the entire
composition. Γ rejected the edge until it existed.

## B. The harness reproduces rung 6 EXACTLY (the reproduction control)

The `degenerate` arm is rung 6, re-run through rung 8's harness. It comes back to
the digit — so anything that differs in the `lateral` arm is the **channels**,
not the harness:

| quantity | rung 6 reported | rung 8 measured |
|---|---|---|
| convergence, MILLER η=5e-4 | drift 0.004 → **0.461**, clump → **0.85** | drift 0.0042 → **0.4612**, clump **0.849** |
| convergence, MILLER η=1e-4 | OSI **0.283 → 0.329** | OSI **0.2832 → 0.3287** |
| positive control (biased ensemble) | OSI **0.878**, peak/base **20.6**, clump **0.718**, every cell prefers the shown orientation | OSI **0.8823**, peak/base **19.36**, clump **0.704**, prefs all `0.0` |
| untrained floor | **0.3168** | **0.3316 ± 0.1141** (n=8, this run) |
| ideal split-Gabor | **0.9115** | **1.0000**, peak/base 6.94 |

## C. THE GATE THAT FAILED: the probe is BLIND on the composed pathway

PROTOCOL §1: *"run it on an ideal exemplar of the structure — it must score
high."*

| pathway | untrained floor | **IDEAL split-Gabor** | peak/base |
|---|---|---|---|
| degenerate (rung 6's) | 0.3105 | **1.0000** | 6.94 |
| **lateral (composed)** | 0.0205 | **0.1290** | **0.89** |

**A PERFECT cell scores 0.1290 on the composed pathway.** The instrument rung 6
calibrated on *its* channels is **not valid** on rung 7's. Every arm comparison
here would have been meaningless, and a null would have been uninterpretable —
"is the rule failing, or is the probe blind?" **So the rung stops.**

The duration check is clean (0.0205 flat across 0/400/1600 frozen probe-steps),
so the failure is **not** duration-confounding.

**THE POSITIVE CONTROL FAILS THE SAME WAY — a second, independent §1 check with
the same cause.** Given a PERFECTLY BIASED ensemble (0° only, 1500
presentations) — the condition under which the rule MUST succeed if it is
capable at all:

| arm | η | OSI | peak/base | prefs |
|---|---|---|---|---|
| degenerate | 5e-4 | **0.8823** | 19.36 | **all 0.0** — every cell prefers what it was shown |
| degenerate | 1e-4 | 0.5318 | 2.90 | mixed |
| **lateral** | 5e-4 | **0.0678** | **0.53** | scattered `[10,4,4,4,2,3]` |
| **lateral** | 1e-4 | **0.0671** | **0.53** | scattered `[10,2,4,4,2,3]` |

Both lateral controls sit near the lateral floor (0.0174) with peak/base **0.53**
— i.e. the cells respond *less* at their "preferred" orientation than at
baseline, which is what a threshold that never bites looks like. **This is the
same readout failure, not a second one:** the positive control is scored through
the same probe the ideal cell just failed. It therefore adds no independent
evidence about the rule, and is reported for completeness rather than as a
finding about learning.

## D. THE CAUSE, MEASURED — and it is rung 7's SUCCESS that causes it

Rung 6's main finding was *the threshold, not the split, makes the response
signed* (ideal cell 0.0006 → 0.9115). **Rung 8 reproduces that and sharpens it
into a precondition rung 6 never had to state**, because on its channels it held
by coincidence:

> **θ is an EMA of the cell's own drive on the FORMATIVE input. It transfers to
> the probe only if the probe's drive magnitude matches the formative input's.**

| arm | act under **waves** (formative) | act under **gratings** (probe) | ratio | θ | outcome |
|---|---|---|---|---|---|
| degenerate | 5.317 | 5.120 | **0.96** | 5.430 | θ sits AT the drive ⇒ slices a 0.2% modulation into OSI **1.0000** |
| **lateral** | **0.861** | **1.902** | **2.21** | **0.774** | θ sits FAR BELOW the drive ⇒ rectification never bites ⇒ OSI **0.1290** |

And the mechanism is **exactly what rung 7 earned**:

- The retina is a **predictive coder optimised for the wave ensemble**. On waves
  the surround **predicts** the centre, so the residual `c − g1·h1 − g2·h2` is
  **small** (act 0.861) — that *is* Atick & Redlich, working.
- A period-4 grating is **out of that distribution**: the surround cannot predict
  it, so the residual is **large** (act 1.902).
- θ, calibrated on the cheap formative input, therefore lands **below** the
  expensive probe — and the iceberg never bites.

**Rung 6's probe worked because its channels did NOT decorrelate**: the raw
binary field drives waves and gratings comparably (5.32 vs 5.12). **The very
decorrelation that removes rung 6's blocker breaks rung 6's readout.** The two
rungs are not composable through this instrument, and that is a structural fact
about the pair, not a bug in either.

## E. What the composed pathway DOES show — the FILTER is far better conditioned

Reported because it is measured, and **explicitly NOT a claim of orientation
selectivity** (that is what the invalid probe would have had to establish):

| arm | ideal cell's `act` tuning range | modulation on pedestal | OSI on `act` (drive) |
|---|---|---|---|
| degenerate | [5.120, 5.132] | **0.2%** | 0.0007 |
| **lateral** | [1.836, 2.310] | **~26%** | 0.0070 |

The decorrelated channels deliver a drive whose orientation modulation is **~100×
larger relative to its pedestal**. Rung 6 needed a threshold to rescue a 0.2%
modulation from a DC pedestal; the composed pathway does not have that pedestal
problem in the first place. **This is a property of the DRIVE, not evidence of a
developed selective RESPONSE, and it is measured on a hand-installed ideal cell
— not on anything the rules grew.**

## F. Convergence (PROTOCOL §2) — reported, and the drift facts ARE valid

Drift does not depend on the probe, so these stand even though the OSI column on
the lateral arm does not. `scripts/rung8_convergence.py`, seed 3000 (burned),
retina developed first, out to 6400 steps, 0 NaN everywhere:

| arm | rule | η | drift 400 → 6400 | clump | verdict |
|---|---|---|---|---|---|
| degenerate (rung 6 reproduced) | MILLER | 5e-4 | 0.0042 → **0.4612** | → 0.849 | **runs away** (rung 6's own result) |
| degenerate | MILLER | 1e-4 | 0.0008 → 0.0088 | → 0.562 | stable |
| **lateral** | MILLER | 5e-4 | **0.0063 → 0.0300** | 0.486 → 0.589 | **bounded** — rung 6's runaway is GONE |
| **lateral** | MILLER | 1e-4 | **0.0013 → 0.0055** | 0.468 → 0.510 | **stable** |
| lateral | plain OJA | 5e-4 | 1.0839 → 0.1827 | → 0.841 | does **not** settle |
| lateral | plain OJA | 1e-4 | 0.3238 → 0.2794 | → 0.506 | does **not** settle |

- **The lateral channels FIX rung 6's runaway.** MILLER subtractive at η=5e-4:
  rung 6 diverged (drift 0.0042 → **0.4612**, clump → 0.849); composed, it stays
  **bounded** (0.0063 → **0.0300**, clump 0.589) — a **15× smaller** terminal
  drift. Stated honestly: it is bounded and far below rung 6's runaway, but it is
  **rising** across checkpoints rather than settled, so "bounded" is the claim,
  not "converged". At η=1e-4 it is genuinely stable (0.0013 → 0.0055).
- **Plain OJA does not settle on these channels** (drift 0.18–0.28 at 6400 steps
  either way), so the MILLER subtractive rule is doing the stabilising.
- **The composed arm's OSI column (≈0.016–0.020 throughout) is NOT
  interpretable**: the probe that produced it is the one section C invalidated.
  `peak/base` sits at **0.83–0.85** — below 1.0 across every lateral checkpoint,
  which is the same threshold-never-bites signature §D diagnoses, showing up
  independently in the convergence run.

## G. The instrument bug found en route (the fourth in this arc; rung 5 found three)

`lat_g0 = 0.0` means the retina is born a **pure centre** — rung 7's whole point.
But at `g=0` the residual **is** the raw centre `c`, and `c ≥ 0` on a binary wave
field, so `OFF = max(−c, 0) ≡ 0`: **the OFF channel is identically DEAD at
init.** Measured: at g=0, ON mean 0.5000 / OFF mean **0.0000**; after 3000 wave
steps, gains [0.517, 0.448] and ON 0.1953 / OFF **0.1933** — alive and balanced.

A first calibration pass probed the cortex against that dead channel and scored
the ideal cell **0.1944**. `develop_retina()` fixes it: the retina is brought to
**its own fixed point** — the state every rung-7 claim is measured at, and the
sequence that corresponds to the animal (retinal centre-surround precedes
cortical simple cells) — before the cortex is probed or trained. **This changed
nothing about the readout** (PROTOCOL §5), and the gate **still fails**
(0.1290), which is why the failure is reported as real rather than as my bug.

## H. What this rung does NOT claim

- **NOT** that the composed system lacks orientation selectivity. It is
  **UNTESTED**: the probe is blind here, and a blind probe cannot support a
  negative any more than a positive. Rung 6's negative is **not** deepened, and
  it is **not** overturned.
- **NOT** that rung 7's channels are unsuitable — §E measures the opposite for
  the drive.
- **NOT** a new readout. Fixing θ (e.g. adapting it to the probe ensemble, or
  matching the probe's drive to the formative input's) is a **new hypothesis
  requiring its own prospective pre-registration** (PROTOCOL §5). Choosing a
  threshold rule *after* seeing which one rescues the number is metric surgery,
  and this arc has retracted three results already.
- The `w0` ablation is **architecturally empty for this layer** (§7) — that is
  measured here, not inherited.

## I. Named next — each needing its own pre-registration

1. **θ's calibration is the blocker, and it is a MECHANISM question, not a
   parameter search.** The composed system needs a threshold whose reference is
   the ensemble being *responded to*, not only the one it developed on — or a
   probe delivered at the formative input's drive magnitude. **State which, and
   why, in advance.** Note this is rung 6's own finding reaching its limit: it
   placed θ on the activation function *"where it cannot flip `dw`'s sign"*
   (GCAL's placement); nothing there pins its **scale** across distributions.
2. **The orientation-isotropy of the wave ensemble is still untouched** by
   rung 7 (§8's reasoning), and it is the cause rungs 3 and 5 both died on.
   Decorrelation removes a redundancy; it does not install an anisotropy.
   Competition between SUnits (rung 4's `vm_burst_lateral` is the precedent, and
   rung 5 named it) remains the untested lever.
3. **Plain OJA does not settle on these channels** (§F) — if a future rung wants
   it, that is a stability mechanism to find, not an η to search.
