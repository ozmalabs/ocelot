# RUNG 8B — θ IS NOT GCAL's θ

*Pre-registration, written and COMMITTED BEFORE ANY RUN OF THE MECHANISM
(PROTOCOL §3). Rung 8 stopped at the §1 calibration gate and explicitly refused
to fix θ in-run, because doing so inside a failed run is metric surgery (§5).
This document is the prospective hypothesis §5 demands. Nothing below was
written with a result in hand — the mechanism has never been run at the time of
this commit, and the git timestamp of this file predates every log it refers
to.*

**Engine:** `95167c01b7b3` @ `runners/dsl/python/substrate_rs/_native.abi3.so`
— shared build, Rust source byte-identical to canonical, resolved into THIS
worktree by `ensure_tree_engine()` (PROTOCOL §10.1). **This rung adds NO Rust**
(§7 below states why, and the claim is gated).
**Base commit:** `0580479857`.
**Selector:** explicit file lists. Never `-k vision` (§12).
**Seeds:** **13000–13999** — rung 8's own block, ALLOCATED, UNUSED, still CLEAN
(rung 8 burned none; the ledger says *"a future rung-8 attempt may take this
block"*). This is that attempt. Gates/pilots use already-burned 0–13 / 3000
only. 12000–12999 stays with the pre-visual rung.

---

## 1. The failure this addresses, in one line

An **ideal** split-Gabor — a perfect cell — scores **OSI 0.1290** on the
composed pathway against **1.0000** on rung 6's own. The probe is blind, so H1
and H2 were never tested. Rung 8's measured cause:

> θ is an EMA of the cell's own drive on the FORMATIVE input; rung 7's retina is
> a predictive coder, so waves are cheap (act **0.861**) and an
> out-of-distribution grating is expensive (act **1.902**, **2.21×**). θ lands at
> **0.774**, below the probe drive, and the iceberg never bites.

## 2. THE MECHANISM-LEVEL HYPOTHESIS — and it is a FIDELITY claim, not a fit

**Our θ is not GCAL's θ. It never was.** The rule
(`oo_sunit_adapt_theta`) cites GCAL and implements something structurally
different. This is documentable from the paper's equations and the rule's own
body, **with no reference to any score**:

| | **GCAL** (Stevens et al. 2013, Eqs 7–8; `VISION_PRIOR_ART.md` §2.2) | **ours** (`oo_sunit_adapt_theta`) |
|---|---|---|
| tracked signal | `η̄ = β·η̄ + (1−β)·η_j` — EMA of the **OUTPUT** (post-threshold rate) | `act` — the **INPUT** drive (pre-threshold) |
| update | `θ ← θ + λ·(η̄ − μ)` | `θ ← θ + theta_rate·(act − θ)` |
| error term | deviation from a **SETPOINT μ** | deviation from **itself** |
| fixed point | **mean OUTPUT = μ** | **θ = mean INPUT** |
| control type | **integral feedback with a setpoint** | **low-pass follower** |

**Ours regulates nothing.** A homeostat holds a regulated variable at a
setpoint; ours holds none — it *follows* its input. Rung 6 took GCAL's
**placement** (on the activation function, outside the learning rule, where it
cannot flip `dw`'s sign — correctly, and that is why it never annihilated like
BCM) and **dropped GCAL's setpoint**. Rung 8's §I.1 names exactly this gap:
*"nothing there pins its **scale** across distributions."* **μ is what pins it.**
The rule's own comment even states the defect as if it were a feature: *"theta is
an EMA of the cell's own act, so it adapts to whatever tonic drive the OFF
channel happens to impose."* Whatever the drive *happens to be* is precisely the
property that does not transfer across ensembles.

**The derivation, and the consequence follows from it rather than being aimed
at:**

- **A follower is scale-LOCKED to the ensemble it last saw.** `θ → E[act | A]`.
  Read on ensemble `B` with `E[act|B] = s·E[act|A]`: for `s > 1` the cell fires
  on *everything* (no iceberg — rung 8, `s = 2.21`); for `s < 1` it fires on
  *nothing*. The operating point is an accident of `s`.
- **A setpoint regulator has an operating point BY CONSTRUCTION.** `θ` moves
  until `E[rate] = μ`. With `μ` small, θ necessarily sits high in the response
  distribution, so only the phase-peaks of well-driven orientations cross — **that
  IS Priebe & Ferster's iceberg**, obtained by construction rather than by luck.

**And this reframes rung 6's success as LUCK, which is a claim about the arc's
own instrument.** Rung 6's θ=5.430 sat just above its probe's drive
(5.120) *only because its probe ensemble was slightly CHEAPER than its formative
one* (5.317). The instrument was never robust; it was accidentally positioned.
Rung 8's 0.1290 is the same instrument being unlucky. **If this is right, rung
6's 1.0000 was never evidence that the probe works — only that `s < 1` that
day.**

## 3. THE DISCRIMINATING TEST — what a parameter search structurally CANNOT do

**The trap, named so I can be held to it:** "tune θ until the ideal Gabor scores
high" is not a fix. So the pre-registered test is one a tuned constant **cannot**
pass:

> **ONE rule, ONE set of GCAL's PUBLISHED constants, must restore the measure on
> BOTH pathways at once — whose drive scales differ ~6× (0.861 vs 5.317).**

A fitted θ rescues at most one: any constant placed inside the composed
pathway's drive range (~1.8–2.3) sits far below the degenerate pathway's (~5.1)
and destroys its iceberg; any constant that works at 5.1 sits far above 1.9 and
silences the composed cell entirely. **Only a rule that self-positions can do
both.** Cross-pathway invariance is the mechanism's signature and is the reason
this is a hypothesis rather than a search.

## 4. THE CONSTANTS ARE GCAL's, LITERAL AND UNTUNED — and their failure mode is the finding

`β = 0.991`, `λ = 0.01`, `μ = 0.024`, `η̄(0) = μ` — **exactly the published
values** (`VISION_PRIOR_ART.md` §2.2, Eqs 7–8), used **unmodified**, **one set
for both pathways**. I am not free to move them: moving μ after seeing a score is
the search this document exists to forbid.

**The honest risk, stated in advance (this is the top proviso).** GCAL's `μ =
0.024` lives in *their* response units — L1-normalised weights (`Σw = 1`) with
inputs in `[0,1]`, so their `η ∈ [0,1]` and μ means *"fire at 2.4% of maximum."*
**Our weights are NOT normalised** (Miller subtractive, `wmax = 2.0`) and our
`act` runs ~0.86–5.3, so the literal constant does **not** carry its meaning
across. It may prove far too sparse.

**If it fails BY FLOOR INFLATION (§5's G2), that is a RESULT, not a prompt to
re-tune μ.** It would say: an absolute setpoint cannot transfer into unnormalised
response units — and the mechanism that puts responses into normalised units is
**GC, GCAL's other letter** (divisive contrast-gain control in the LGN, whose
stated purpose in the paper is *"reduce presynaptic drive variance across
patterns"* — verbatim the quantity rung 8 measured as 2.21×). **Our retina has
rung 7's SUBTRACTIVE predictive coding and no division.** That would locate the
next rung precisely, and it needs its own pre-registration. **I will not rescue a
failed μ by fitting μ.**

## 5. THE GATE (PROTOCOL §1) — declared BEFORE the run, and the quantity is SEPARATION

§1's error in this arc has been reading the ideal alone. **Raising θ raises the
ideal score AND the floor** — OSI takes an `argmax` over 12 orientations, so
clipping the orthogonal response to 0 inflates a *random* cell toward 1.0 just as
it does an ideal one. **So the gate is the SEPARATION, with floor and ideal
measured under the SAME θ rule, in-run, never inherited** (OSI's floor is
init-dependent — 0.0044 DC vs 0.3899 signed, 89×, same probe; rung 6's is a third
value, 0.3168; rung 8's composed a fourth, 0.0205).

On the **composed (lateral)** pathway, under the GCAL-θ rule, all must hold:

| | criterion | why this number |
|---|---|---|
| **G1** | ideal split-Gabor OSI **≥ 0.80** | a perfect cell must be plainly visible (rung 6's own ideal: 1.0000) |
| **G2** | untouched-init floor **≤ 0.50** | the measure must not be saturated by θ's placement alone (known signed floors: 0.3168 / 0.3899 — this admits them and rejects saturation) |
| **G3** | **separation (ideal − floor) ≥ 0.30** | declared between rung 8's failure (0.129 − 0.021 = **0.109**) and rung 6's success (1.000 − 0.311 = **0.69**). Not fitted to any number measured under the new rule — none exists at this commit. |
| **G4** | duration: OSI flat (Δ < 0.01) across 0/400/1600 probe-steps with θ FROZEN | the rung-8 check, unchanged |
| **G5** | θ CONVERGENCE (§2): θ's drift → 0 during adaptation, and OSI flat (Δ < 0.05) across adaptation durations past equilibrium | *does the rule settle on its own input* — the check that cracked rung 2 |
| **G6** | **§3's cross-pathway test: separation ≥ 0.30 on the DEGENERATE pathway TOO**, same rule, same constants | a re-tuning cannot pass this |

**Any gate failing ⇒ NO confirmatory arm, NO seed burned, and the failure is
reported as the result.** Rungs 5, 6, 8 and phase 0 all correctly burned nothing.

## 6. THE EXPOSURE QUESTION, decided in advance with reasons

Rung 8's §I.1 offers two routes: *"a threshold whose reference is the ensemble
being responded to, or a probe delivered at the formative drive magnitude."*
**I choose the first, and reject the second.**

- **Rejected — probe at the formative drive magnitude.** It changes what the
  probe *is*, makes the number incomparable to rung 6's 1.0000, and treats a
  legitimate stimulus as the defect. A grating is out-of-distribution for a
  predictive coder *by construction*, and that is a fact about the retina worth
  keeping, not sanding off.
- **Rejected — probe in-distribution (waves).** Orientation selectivity is
  *defined* by response to gratings; an in-distribution probe would measure a
  different thing and forfeit comparability.
- **Chosen — θ equilibrates on the ensemble being responded to, then FREEZES,
  then the measurement runs.** This is **adaptation**, and it is what every
  physiological experiment does: the animal sits in front of the display, adapts,
  and *then* you record.

**Why this does NOT violate rung 6's own discipline** (*"a probe must never let
theta chase the probe"*). That rule conflates two hazards which GCAL's placement
separates:

1. **A probe that TRAINS the weights it measures** — rung 5's freeze bug, real
   and fatal. **Weights stay frozen throughout, verified `max|dw| = 0.000e+00`.**
2. **A probe that lets the OPERATING POINT settle** — that is adaptation, not
   training. **θ cannot flip `dw`'s sign — that is precisely why rung 6 put it
   where GCAL puts it** — so with weights frozen, θ's adaptation changes no
   weight. The placement rung 6 chose is what licenses this, and the argument is
   internal to the arc.

**θ is FROZEN during the measurement itself** (`theta_adapt = 0`), verified
`Δθ = 0`, so the probe never chases anything. Adapt → freeze → measure.

**THE TIMESCALE HAZARD, and it is genuinely two-sided.** If θ adapts *fast*
enough to track each orientation, it **cancels the very modulation OSI
measures** — adaptation would destroy selectivity rather than reveal it. This is
why biology's homeostasis is slow relative to the stimulus, and why GCAL's
constants are slow (`β = 0.991` ⇒ τ ≈ 111 steps; `λ = 0.01`). **The adaptation
ensemble interleaves orientation and phase at random every step**, so θ's
timescale averages over many orientations by construction. **I measure this
rather than assert it** (G5). Note the brief's caution is about **synaptic
scaling** (Turrigiano, hours–days); GCAL's θ is **intrinsic threshold
adaptation**, a faster and distinct mechanism — but the hazard stands and is
gated.

## 7. Architecture (CLAUDE.md; PROTOCOL §0, §9)

**θ and its update are the AGENT's, so they are graph data.** New seed
`seeds/vision_theta.json`:

- `ThetaParams { theta_mode: 0.0, theta_adapt: 0.0, theta_mu: 0.024,
  theta_beta: 0.991, theta_lambda: 0.01 }`
- rule `th_track_rbar` — `rbar ← β·rbar + (1−β)·rate` (GCAL Eq 7)
- rule `th_adapt_gcal` — `θ ← θ + λ·(rbar − μ)` (GCAL Eq 8)

Both gated on `theta_mode > 0.5` **and** `theta_adapt > 0.5`, phase-guarded on
`rate_step == step` exactly as rung 6's own θ rule is, so they can only move
after this step's rate has been read.

- **NO Rust.** Both rules are `Plus`/`Times`/`Minus`/`Attr`/`Lit` — the Terms
  rung 6's rules already use. Expressibility is not a reason to reject a
  mechanism, but nor is it a reason to add a Term that is not needed. **Gated:
  the source fingerprint must read `shared`, not `own`.**
- **NO edit to `seeds/vision_onoff.json` or `seeds/vision_lateral.json`**
  (§11.4 — do not edit another rung's seed; rung 8's *"compose, don't modify"*).
  The GCAL arm sets rung 6's existing `homeo = 0` (which *pins* its EMA rule —
  its documented meaning) and `theta_mode = 1`. **The two θ rules can never both
  fire.**
- **`theta_mode = 0.0` DEFAULT ⇒ the seed is inert ⇒ every committed result
  reproduces byte-identically** (§9). Verified on the named gate before commit.
- Every arm is a flag on a params node — the agent's own configuration, never a
  Python code path (§0).

## 8. The confirmatory design — ONLY if every gate passes

Rung 8's H1/H2, unchanged, now readable:

- **H1** — SUnits on rung 7's decorrelated channels become orientation-selective:
  OSI ≫ the **lateral untrained floor measured in this run, under this θ rule**.
- **H2** — on the **degenerate** split, OSI stays at **its own** floor
  (rung 6's negative, reproduced as the control).

Two-sided (§3.1): OSI *below* the floor is as reportable as above — rung 3's
`strobe` dissolved an innate bias *below* the floor and only an `untrained` arm
caught it.

**Statistic:** mean OSI per **SEED** (§4 — units share input and compete under
WTA, so they are not independent). Because the arms have **different floors** and
the degenerate control is emphatically **non-null**, the pre-registered test is
the **INTERACTION** (§4):

    Δ_arm       = OSI(trained, arm) − OSI(untrained, arm)      [paired, per seed]
    INTERACTION = Δ_lateral − Δ_degenerate

**SESOI 0.0595** (rung 6's, adopted unchanged — same layer, same probe).
**n** fixed in advance by a power pilot on **already-burned** seeds (0–13, 3000).
**Confirmatory seeds 13000–13999**, never used for anything.

**Decision rule.** H1 CONFIRMED iff `Δ_lateral > SESOI` with a CI excluding 0
**and** the interaction CI excludes 0. **H1 NULL ⇒ decorrelated input is NOT
sufficient, and rung 6's negative DEEPENS** — a finding, locating the blocker
somewhere other than the channels' correlation structure (§8's isotropy is the
standing candidate). **If the degenerate control is not null, neither hypothesis
is interpretable.** **Exactly the listed tests. No sweeps. No re-runs.** η, RF,
period, `lat_eta`, `gmax`, and now `β`/`λ`/`μ` are FROZEN.

## 9. MY PREDICTION, IN ADVANCE, WITH ITS PROVISOS (§3.7)

**I predict the gate PASSES and H1 is NULL.**

- **Gate passes:** a setpoint regulator has an operating point on any ensemble,
  so the ideal cell becomes visible on both pathways. I put this at ~60% — the
  units mismatch in §4 is a real and unhedged risk.
- **H1 NULL:** I inherit rung 8's reasoning and believe it. **Oja's fixed point
  is the leading PC of the time-averaged covariance, and a contraction to the
  mean of an ISOTROPIC distribution is the mean.** Rung 7 gives the channels
  different *radial* spatial dependence; the wave ensemble remains
  **orientation-isotropic**. Decorrelation removes a redundancy — **it does not
  install an anisotropy.** Rungs 3 and 5 both died here. Fixing the readout lets
  us *see* the answer; I do not expect it to *change* the answer.

**Provisos — each, if it breaks, tells me what I did not understand:**

1. **If the gate fails by FLOOR INFLATION (G2/G3 while G1 passes)** — the
   setpoint is too sparse in our unnormalised units, OSI's `argmax` selection
   inflates the floor, and **GC (normalisation) is the missing mechanism, not a
   different μ.** §4 binds me to report this rather than re-tune.
2. **If the gate fails by SILENCE (G1 fails, ideal ≈ 0)** — θ overshot the whole
   distribution; μ is too small by more than a units factor, and my reading of
   GCAL's response scale is wrong.
3. **If G6 fails — composed rescued, degenerate broken** — then what I have is a
   re-tuning wearing a mechanism's clothes, my §3 argument is wrong, and **the
   result is a negative I must report as such.**
4. **If adaptation CANCELS selectivity (ideal *falls* below 0.1290)** — θ's
   timescale is not separated from the sweep; homeostasis is eating the signal,
   and the two-sided risk in §6 is real.
5. **If H1 CONFIRMS** — my model of "isotropic ⇒ no orientation" is wrong at the
   level of the *pair* of channels: the ON/OFF **relative** geometry, not the
   marginal ensemble, would carry orientation — closer to what Miller 1994
   actually claims than my reading of it.
6. **If the degenerate control is NOT null** — the interaction is the only
   interpretable quantity; simple effects are discarded.
7. **If rung 6's 1.0000 does NOT reproduce under the DEFAULT (EMA) rule** — my
   seed is not inert and §9 is violated; everything here stops until that is
   fixed.

## 10. What this rung will NOT claim, whatever happens (§8)

- **NOT** that GCAL's θ is biologically correct — only that it is what GCAL
  specifies and that our rule is not it. The verified research refuted the
  Hebbian-vs-sparsity question 0–3; this licenses nothing about which
  biological mechanism is true.
- **NOT** that a passing gate is a result about *development*. A readout that can
  see a perfect cell is a **precondition, not a result** — rung 7's own words.
- **NOT** anything about rung 2's `normal` arm, which does **not currently
  reproduce** (2026-07-17: `normal` 0.317 *below* `dark` 0.363, sign-reversed,
  p<0.0001; the headline is unattributable because attempt 10's runner was never
  committed). **Nothing here rests on it**, and the experience rung is NOT
  background this rung may assume.
- **NOT** that fixing θ vindicates rung 6's instrument. If §2's reframe holds,
  rung 6's 1.0000 was **luck**, and that is a debit against the arc's past
  calibration, not a credit.
- **NOT** map topography, pinwheels, complex cells, or anything above V1.

---

# OUTCOME — **THE GATE FAILS. THE PRE-REGISTERED CRITERIA ALL PASSED, AND THE PASS IS AN ARTIFACT.**

**No confirmatory arm was run. Seeds 13000–13999 are ALLOCATED, UNUSED and still
CLEAN. H1 and H2 remain NOT TESTED** — rung 8's verdict is neither deepened nor
overturned. **Engine `6fcc99edfa4a`** — this tree's OWN build (`scripts/engine_build.sh`),
resolved at
`.claude/worktrees/agent-a8f019f52295be5eb/.../runners/dsl/python/substrate_rs/_native.abi3.so`.
Base `0580479857`. Pre-registration committed `9ca38459` at 12:52:20, **before
any run**. Log: `results/rung8b_calibrate.log`.

## A. The reproduction control — rung 8 comes back EXACTLY

Rung 8's arm, through rung 8's own harness, on my freshly-built engine:

| arm | rung 8 (engine `95167c01b7b3`) | rung 8B (engine `6fcc99edfa4a`) |
|---|---|---|
| lateral floor / IDEAL / peak-base | 0.0205 / **0.1290** / 0.89 | 0.0205 / **0.1290** / 0.89 |
| degenerate floor / IDEAL / peak-base | 0.3105 / **1.0000** / 6.94 | 0.3105 / **1.0000** / 6.94 |

**Byte-identical on a DIFFERENT BINARY built from identical source** — an
independent confirmation of §10.1's invariant from a new direction: *the
invariant is the SOURCE, not the binary's hash.* Anything below is attributable
to this rung, not to the engine or the harness.

## B. The mechanism is BUILT, and the part of the claim it tests is CONFIRMED

`seeds/vision_theta.json`: GCAL Eqs 7–8 as **graph data** — `th_track_rbar`
(EMA of the cell's OUTPUT) + `th_adapt_gcal` (integrate the error against the
SETPOINT μ). **No Rust** (gated). **No edit to rung 6's or rung 7's seeds**
(gated) — the arm sets rung 6's own `homeo=0`. **`theta_mode=0` default ⇒ inert,
verified BYTE-IDENTICALLY** (θ's whole trajectory with and without the seed).
Weights `max|dw| = 0.000e+00` throughout adaptation; θ `|dθ| = 0.000e+00` during
every probe.

**And the setpoint IS reached, on both pathways, with GCAL's literal
constants** — on the ideal cell:

| pathway | act (probe) | θ | rbar | μ |
|---|---|---|---|---|
| lateral | 2.192 | **3.512** | **0.0213** | 0.024 |
| degenerate | 5.177 | **9.751** | **0.0242** | 0.024 |

**θ self-positioned at two different values for two different drive scales,
using one set of constants.** The regulator does exactly what §2 says a
regulator does. **That much of the mechanism claim is confirmed.**

## C. THE GATE'S "PASS" IS AN ARTIFACT — THE FLOOR ARM IS DEAD

| | G1 ideal ≥ 0.80 | G2 floor ≤ 0.50 | G3 sep ≥ 0.30 | G6 degenerate sep ≥ 0.30 |
|---|---|---|---|---|
| measured | **1.0000** | **0.0000** | **1.0000** | **1.0000** |
| verdict | PASS | PASS | PASS | PASS |

**Every pre-registered criterion passes. The gate fails anyway, and I am
reporting it as failed.** The diagnostic:

| pathway | cell | θ | tuning.max | **orientations firing (of 12)** | OSI |
|---|---|---|---|---|---|
| lateral | **random (the FLOOR)** | 26.99 | **0** | **0.00** | 0.0000 |
| lateral | IDEAL | 3.51 | 0.172 | 3.00 | 1.0000 |
| degenerate | **random (the FLOOR)** | 64.68 | **0** | **0.00** | 0.0000 |
| degenerate | IDEAL | 9.75 | 0.262 | 3.00 | 1.0000 |

**The floor arm NEVER FIRES — at any orientation.** `complex_cells.osi()` ends
`return (a-b)/(a+b) if (a+b) > 1e-9 else 0.0`, so **a cell that never fires
returns a PERFECT floor of 0.0000**. And `peak/base` reads **7.1×10⁷** /
**2.4×10⁸** — the *same unbounded-ratio signature* that killed the calibration
reframe (`base`→0 ⇒ the no-input control scored 1.6×10⁶ vs an ideal Gabor's
6.94; ledger 10000–10999). **The "separation of 1.0000" measures FIRES vs
DOES-NOT-FIRE, not selectivity.** A trained cell that failed to develop would
also be silent and score 0.0000; one that developed would score 1.0000. **That
is rung 8's blind probe in a new costume, and it would have made H1 a coin
flip.**

**This is NOT metric surgery (§5).** §5 forbids rescuing a FAILED gate by
changing the measure. This change disqualifies my own apparent SUCCESS — the
opposite direction, and the one §1 and §7 require. A measure may always be made
stricter against yourself.

## D. THE CAUSE, MEASURED — GCAL's Eq 8 WINDS UP in unnormalised units

    dθ/step = λ·(rbar − μ)
    UP-drive   = λ·rbar   — rbar is UNBOUNDED in our units (it reached ~20)
    DOWN-drive = λ·μ      = 0.00024/step — CONSTANT and TINY

| pathway | cell | act | θ | θ/act | rbar | setpoint reached? |
|---|---|---|---|---|---|---|
| lateral | random | **20.80** | 26.87 | 1.29 | **0.00000** | **NO — dead** |
| lateral | IDEAL | 2.19 | 3.51 | 1.60 | 0.0213 | yes |
| degenerate | random | **48.97** | 64.66 | 1.32 | **0.00000** | **NO — dead** |
| degenerate | IDEAL | 5.18 | 9.75 | 1.88 | 0.0242 | yes |

A random cell's drive is **~10× the ideal cell's** (unstructured `w0=1` weights
sum; a zero-mean Gabor cancels). So its θ winds up to 26.9, the cell goes
silent, `rbar` collapses to **exactly 0**, and θ can then fall only at
0.00024/step — **~25 000 steps to recover**. It never reaches μ. **The ideal
cell reaches the setpoint; the random cell dies. THAT ASYMMETRY IS THE ENTIRE
FAKE SEPARATION.**

**In GCAL this cannot happen.** L1-normalised weights (`Σw = 1`) and inputs in
`[0,1]` put `η ∈ [0,1]`, so `rbar − μ ≤ 0.976` and the up- and down-drives are
**comparable**. Ours are unnormalised (Miller subtractive, `wmax = 2.0`), so the
loop is asymmetric by ~100× and winds up.

> **AN ABSOLUTE SETPOINT CANNOT TRANSFER INTO UNNORMALISED RESPONSE UNITS.
> GCAL's A REQUIRES GCAL's GC.** Our layer is model **"AL"** (adaptation, no
> gain control) — and **GCAL's own ablation lattice (L → GCL → AL → GCAL) exists
> precisely because AL is not GCAL.**

**§4 binds me here and I am obeying it: I have NOT re-tuned μ.** The named next
rung is **GC** — divisive contrast-gain control, whose stated purpose in the
paper is *"reduce presynaptic drive variance across patterns"*, verbatim the
2.21× rung 8 measured — and it needs its **own** pre-registration.

## E. WHAT I GOT WRONG (§3.7)

**My prediction was wrong, and both provisos that should have caught it were
mis-specified.**

1. I predicted (proviso 1) the gate would fail by **FLOOR INFLATION** — θ
   clipping + OSI's `argmax` selection driving a random cell's score *toward
   1.0*. **The floor went the other way: to 0.0, by death.**
2. I predicted (proviso 2) silence would present as **G1 failing (ideal ≈ 0)**.
   **Silence hit the FLOOR arm, not the ideal arm.**
3. **So it presented as a clean PASS on every criterion.** I did not anticipate
   that the units failure could look like success. **My gate tested only ONE
   direction of failure (saturation) and was blind to the other (death) — the
   exact defect §4 warns of (*"adding a mechanism can silently invalidate your
   control"*) committed by me while writing a document about it.**
4. **Proviso 3 (G6) is void, not passed.** G6 "passed" — but vacuously: both
   pathways were silenced equally. **A test whose two arms are both dead cannot
   discriminate a mechanism from a re-tuning**, so my §3 anti-fitting argument
   is *untested*, not vindicated.
5. **Proviso 7 held** — the seed is inert and rung 8 reproduces exactly.
6. My probability estimate ("~60% the gate passes") was, in the only sense that
   matters, **wrong in an unanticipated direction**.

**What I got right:** the fidelity claim itself (verified and pinned as a source
audit: rung 6's rule reads `act`, GCAL's reads `rate` against μ); that the
regulator self-positions across drive scales; and — §4, written before the run —
**that a failure of the literal constant would point at GC rather than at a
different μ.** That is the one prediction the run confirmed.

## F. What this rung does NOT claim

- **NOT** that GCAL's θ is the wrong mechanism. It is **untested here**: the
  measure died before the mechanism could be judged. Rung 8's diagnosis (θ has
  no setpoint) stands **unrefuted and unconfirmed**.
- **NOT** that rung 6's 1.0000 was luck. §2's reframe is **NOT TESTED** — my
  `theta_mode=0` rows are the **θ=0 / no-threshold** condition, not rung 6's EMA
  condition (`prepare()` skips adaptation in that mode). They do incidentally
  reproduce rung 6's *"without the threshold, the ideal split-Gabor scores
  0.0006"* as **0.0007**, which is corroboration of rung 6's finding, not of my
  reframe. **The label was wrong in the first run and is corrected, not
  dropped.**
- **NOT** that the composed pathway lacks orientation selectivity. **Still
  untested**, for the second rung running.
- **NOT** anything resting on rung 2, which does **not currently reproduce**.

## G. Named next — each needing its own pre-registration

1. **GC — divisive contrast-gain control in the retina** (GCAL Eq 2:
   `η = f(γ_O·afferent / (k + γ_S·suppressive))`; `γ_O=14.0, γ_S=0.6, k=0.11`,
   and the ablation is `γ_S=0, k=1` — *"a clean, data-shaped ablation of exactly
   the kind our protocol §0 requires"*). It normalises the response scale, which
   is the precondition an absolute setpoint needs. **This is the measured
   consequence of D, not a new guess.** Note it is a genuinely new mechanism at
   a different layer, and rung 7's retina is **subtractive** by design — adding
   division must not be allowed to quietly relabel rung 7's earned claims.
2. **PROTOCOL §1 NEEDS A FOURTH CLAUSE — and this rung earned it.** *"Run the
   measure on random input; it must score at the floor"* **is satisfied by
   DEATH.** A floor is only a floor **if the arm FIRES**. §12's rule generalises
   exactly: an absence off a guarded division (`if (a+b) > 1e-9 else 0.0`) is
   evidence of a **LOOKUP**, not of a measurement. **Positive-control the ARM,
   not just the reader.**
3. **`peak/base` remains an unbounded ratio** and has now produced a
   ~10⁸ reading in a second, independent rung. It should be retired or bounded,
   not read.
4. The wave ensemble's **orientation ISOTROPY** is still untouched (rung 8's
   §I.2) — the standing candidate for H1's expected null, and still the cause
   rungs 3 and 5 died on.
