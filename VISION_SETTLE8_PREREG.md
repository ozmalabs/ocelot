# THE NON-BIPARTITE SHEET — PRE-REGISTRATION

**Committed BEFORE the measurement (§3). Base `39f2ae29` (the settling rung),
engine `74fc035c8595` @ canonical, `shared` build — Rust source byte-identical
to this tree; this rung adds NO Rust. `data/` symlinked from canonical (§10.2).**

**Seeds: 22000–22999 CLAIMED.** 12000–21999 NOT TOUCHED (21000–21999 is the
settling rung's, allocated and clean). **Nothing in STEP 1 consumes a seed: it
is DETERMINISTIC linear algebra on the adjacency, with no RNG arm** — the same
move that made the wave-isotropy rung decisive.

**THIS IS ENGINEERING, NOT THE PARADIGM CLAIM (§7).** A working V1 is valuable
and **not novel** — GCAL already works. The sd rung's negative (*"the loop
composes what it holds; it does not discover what it lacks"*) **stands untouched
and is not reopened by anything here.**

---

## 0. WHAT I INHERITED, AND WHAT I MUST VERIFY MYSELF (§12.4)

Three load-bearing claims arrive from a sibling rung and a supervisor brief.
**A sibling's claim is not a source.** Each is re-derived here before use:

| inherited claim | status |
|---|---|
| `M = D⁻¹A − (1/N)J` on a bipartite square lattice has λ_min = −1.000000 exactly | **VERIFY** — reproduce independently at connectivity=4 (STEP 0) |
| GCAL's settling is a BOUNDED ITERATION that stops short of a fixpoint, not a fixpoint | **VERIFY from the primary** — and the settling rung's OWN document contradicts itself here (§0.1) |
| `run_rules` terminates only on an EXACT fixed point | **VERIFY** — observe it |

### 0.1 THE CONTRADICTION I AM INHERITING, NAMED IN ADVANCE

The settling rung's brief says *"the supervisor's 'GCAL's settling is a fixpoint'
hint was FALSE"*. But **the settling rung's own results file argues both sides**:

- `VISION_SETTLE_RESULTS.md` **§5.1**: *"GCAL does not converge either. It STOPS.
  GCAL never asks whether the sheet settled; it sweeps 16 times and reads out."*
  ⇒ 16 is a TRANSIENT.
- `VISION_SETTLE_RESULTS.md` **§3**, quoting GCAL's own words for its 16: *"a
  fixed number **sufficient to ensure that cortical activity is no longer
  changing significantly**"* — and then: *"we hold the **criterion**; GCAL holds
  a **count** that fell out of it."* ⇒ 16 REACHES convergence, and the count
  **fell out of** a convergence criterion.

**These cannot both be right, and the difference decides what object I am
allowed to build.** "Sufficient to ensure activity is no longer changing" IS a
convergence criterion; a count that "fell out of" it is an approximation TO a
fixed point, not a deliberate stop short of one. `VISION_PRIOR_ART.md` §2.2
independently records LISSOM/GCAL settling *"over ~16 iterations **into activity
bubbles**"* — a bubble that forms and persists is a stable state, not a
transient.

**I am NOT resolving this by preference.** It is being retrieved from the
primary (PMC6618482) by me and, independently, by a second reader with no sight
of this tree (§12.4's standard). **Both readings are pre-committed here so
neither can be chosen after the fact:**

- **If READING A (16 ≈ converged):** a fixpoint IS (approximately) GCAL's object,
  the settling rung's §5.1 over-read the words "fixed number", and building a
  convergent loop is building the right thing. **I must still say so plainly and
  report that the objects are not IDENTICAL** (GCAL truncates; I do not).
- **If READING B (16 is a transient that matters):** then **a converging loop is
  a DIFFERENT OBJECT WEARING THE SAME NAME**, and I must report exactly that —
  "we converged" would be the *"one word spanning two layers"* disease that has
  already bitten this arc twice (`Δ_lateral`; `mu_endo`). **In that case a
  convergent loop does not vindicate the mechanism and I will say so**, whatever
  the OSI does.

---

## 1. STEP 0 + STEP 1 — THE SPECTRUM. PREDICTED HERE, MEASURED AFTER.

### 1.1 The statistic, exactly

For the sheet actually wired by `settle_world.wire_sheet(connectivity=c)` on
`settle_lib.lattice_centres(n_side)` — **the operator read off the GRAPH's own
`sunit_neighbour` edges, never a re-derived idealisation** (the settling rung's
lesson: a float `linspace` silently wired 12 edges where 24 were due):

```
A      = the wired sunit_neighbour adjacency (n_side^2 square)
D      = diag(row sums of A)
M      = D^-1 A - (1/N) J          # J = all-ones, N = n_side^2
```

Report, for `c ∈ {4, 8}` and `n_side ∈ {3, 4, 5, 6}`:

1. **λ_min(M)** — the sibling's deciding number;
2. **ρ(M) = max |λ|** — **the number that actually governs convergence**;
3. bipartiteness of `A` (2-colourability, checked directly);
4. triangle count of `A`;
5. degree histogram of `A` (the sheet is NOT regular at an open boundary).

### 1.2 MY PREDICTION, IN ADVANCE, WITH ITS PROVISOS (§3.7)

**(a) λ_min(M) at c=8 will be > −1 STRICTLY — and I CLAIM NO CREDIT FOR IT
(§13.1).** An 8-connected lattice contains triangles — `(0,0)–(0,1)–(1,1)` closes
because `(0,0)–(1,1)` is a diagonal edge — so the graph is **non-bipartite**, and
for a connected non-bipartite graph the random-walk matrix `D⁻¹A` has
λ_min > −1 **as a theorem** (Perron–Frobenius: λ = −1 ⟺ bipartite). **This half
is FORCED. A prediction that cannot fail is not evidence** — it is arithmetic,
and I am reporting it as arithmetic.

**(b) The QUANTITATIVE prediction, which CAN fail: λ_min(D⁻¹A) ≈ −0.5.**
On the *infinite* 8-connected lattice the random-walk Fourier symbol is

```
f(k) = [2cos kx + 2cos ky + 4 cos kx cos ky] / 8
```

Substituting `u = cos kx, v = cos ky ∈ [−1,1]`, `f = (u + v + 2uv)/4`, whose
minimum over the square is **−0.5** (at `(u,v) = (−1,1)` or `(1,−1)`, i.e.
`k = (π,0)` / `(0,π)` — the **stripe** modes). Note the checkerboard `k=(π,π)`
gives `(−1−1+2)/4 = 0` **exactly** — 8-connectivity does not merely perturb the
checkerboard mode, **it annihilates it**, which is the mechanism claim.
**Prediction: λ_min(D⁻¹A) at c=8 lands in (−0.6, −0.35)** on the finite open
sheet. **Proviso that could break it:** the open boundary and the resulting
degree inhomogeneity (3/5/8) are a large perturbation on a small sheet, so the
finite value may sit outside that window; if it does, the *mechanism* claim
(no −1) survives but my *quantitative* understanding does not, and I will say
which broke.

**(c) THE REAL CONTENT — ρ(M) < 1, and it is NOT forced.**
`M·1 = D⁻¹A·1 − (1/N)J·1 = 1 − 1 = 0`, so the DC mode is killed **exactly** and
`0 ∈ spec(M)`. At c=4 the sibling measured `ρ(M) = 1.000000` — set NOT by DC (J
killed that) but by the checkerboard at −1. Removing the checkerboard should drop
ρ below 1. **BUT I cannot derive this**, and the reason is precise and is the
proviso: **the open-boundary sheet is NOT REGULAR** (degrees 3/5/8), so the
eigenvectors of `D⁻¹A` other than `1` have zero **degree-weighted** sum
(`Σ_k d_k v(k) = 0`), **not zero plain sum**. Therefore `J` does **not** act
trivially on them and

```
spec(M)  ≠  {0} ∪ (spec(D⁻¹A) \ {1})
```

`M` is a **rank-1 perturbation of a non-regular random walk**, and its spectrum
must be **measured, not assumed**. **Prediction: ρ(M) ∈ [0.5, 0.9] at c=8**, set
by the slowest non-DC mode. **Proviso: if the rank-1 J term pushes an eigenvalue
to |λ| ≥ 1, the loop still will not converge and STEP 2 is dead** — that is a
real possibility and it is why this is a measurement and not a formality.

**(d) At c=4 I predict I REPRODUCE the sibling: λ_min = −1.000000, ρ = 1.000000.**
If I do not, the sibling's theorem is wrong and that is the finding.

### 1.3 DECISION RULE — STATED BEFORE THE NUMBER

- **λ_min(M) ≤ −1 at c=8** (within 1e−9) ⇒ **STOP. Report. Burn nothing.** The
  2-colouring survived and the mechanism claim is false.
- **λ_min(M) > −1 but ρ(M) ≥ 1** ⇒ **STOP. Report.** Non-bipartiteness was
  necessary and not sufficient; a fixed point still does not exist. **This is a
  live outcome, not a formality** (§1.2c).
- **λ_min(M) > −1 AND ρ(M) < 1** ⇒ proceed to STEP 2, and ONLY then.

**A null at either gate is a RESULT (§7), and it is the eighth rung to stop at a
gate rather than burn a block. `mints(N)` and the sd negative are untouched
either way.**

---

## 2. STEP 2 — DOES THE LOOP ACTUALLY CONVERGE? (§2)

**Only if STEP 1 permits.** The spectrum is a claim about the LINEARISATION; the
loop is `act ← max(aff + M·act, 0)`, and the **ReLU is not the linear operator**.
A spectral radius under 1 is strong evidence, not a proof about the rectified
map. So it is measured, on the real graph, through the real engine:

- **Statistic:** `run_rules` applications per step, and whether the 200000 cap is
  hit, at `n_side ∈ {3,4,5}`, `c ∈ {4, 8}`, over ≥6 wave steps.
- **PASS:** c=8 terminates **well under** the cap on **every** step, and c=4 hits
  it on every step (the sibling's result reproduced as the paired control).
- **FAIL:** c=8 hits the cap ⇒ STOP, report; the spectrum said contract and the
  rectified loop did not, which would itself be the finding.

**§2's own requirement, not skipped:** if the loop converges I additionally
report `drift = ‖act(t) − act(t−1)‖ / ‖act‖` across steps, so "converges" is
shown and not asserted.

---

## 3. STEP 3 — 8D's UNANSWERED PREDICTION (only if STEP 2 passes)

Rung 8D predicted: *"there is NO η at which the learning rule is both convergent
and load-bearing"* (5e-4 runs away; 1e-4 near-vacuous). **This could not be asked
on a non-convergent scaffold.**

- **Statistic:** at `η ∈ {1e-4, 5e-4}`, on the SETTLED sheet (`settle=1`) vs the
  committed unsettled one (`settle=0`) — **weight drift** `‖w(t)−w(t−Δ)‖/‖w‖`
  (does it run away?) and **`D = max|settle1 − settle0|`** on `rate` (§1 clause
  5: is it load-bearing?).
- **CONJUNCTIVE GATE (§4):** an operating regime requires **BOTH** `drift → 0`
  **AND** `D > 0`. **A mechanism that converges by making itself inert FAILS** —
  that is attempt 2's disease ("removed the harm by removing the effect").
- **Two-sided (§3.1):** 8D's prediction may be **right** (no η works even with
  settling) — that is a clean, reportable outcome that would strengthen 8D, not a
  disappointment.

**NO OSI ARM IS PRE-REGISTERED HERE, AND THAT IS DELIBERATE (§13.1).** See §5.

---

## 4. §13 — IS `connectivity=8` A MAGIC NUMBER? THE ARGUMENT, MADE EXPLICITLY

**It is not a tuned scalar, and here is the case — including the part against me.**

**FOR (it falls out):**
1. **There is no dial.** On a square lattice the neighbourhood is `4` or `8` —
   von Neumann or Moore. It is a **2-element structural choice**, not a
   continuum. You cannot tune 8 to 8.3.
2. **8 is the lattice's OWN unit cell** — the full 3×3 block minus its centre.
   It introduces **no radius constant**: it is the same *"read the adjacency off
   the grid the units already sit on"* move the settling rung made, reading the
   **complete** local cell instead of the axis-only subset. GCAL's `σ_E=0.025`
   is still **NOT** imported.
3. **The 4-neighbourhood is OUR discretisation artifact, and this arc has already
   caught it as one — twice, in writing, before this rung:**
   `VISION_PRIOR_ART.md` E11: *"the deterministic **4-connected argmin** only
   steps N/S/E/W, a **cardinal-axis artifact that would tell the agent the
   answer**"*; and E14: *"our **4-neighbour lattice is below biological
   coordination number**, and percolation threshold depends directly on it"*.
   **Real cortex has no lattice.** 4-connectivity privileges the cardinal axes —
   in an ORIENTATION experiment, that is the axis of the dependent variable.
4. **The DIAGNOSIS PREDICTED THE FIX, and did so BEFORE the fix was run.** The
   settling rung named this route in advance (its §10 route 2) from a spectral
   theorem — *"8-connectivity adds the diagonals and destroys the 2-colouring …
   removes λ=−1 structurally, with no constant at all"*. **A mechanism change
   derived from a theorem is not a parameter search** (§3.6); a sweep over
   `c ∈ {4,8}` looking for the one that converges would be.

**AGAINST (the honest half — where it IS a knob):**
5. **Both 4 and 8 are lattice artifacts.** Neither is biology. The constant-free
   version — a distance-based neighbourhood — needs a RADIUS, which is exactly
   the constant (`σ_E`) §13 forbids importing. **So 8 is not "correct"; it is the
   less-artifactual of the only two options the lattice offers**, and I am
   choosing it on a stated structural argument, not on its output.
6. **If a THIRD connectivity were needed to make it converge, that would be a
   sweep and I would have to stop.** I am pre-committing: **c ∈ {4, 8} only. No
   other connectivity is measured, ever, under this pre-registration.**
7. **Degree-8 is a GAIN OF 8** (the settling rung's §13 sharpening: *"a sum over
   a degree-4 adjacency IS a gain of 4"*, measured at `act → 2.5e224`).
   `st_settle` uses `Div(Fold(...), Max(Count,1))` — **the degree-normalised
   MEAN** — so `D⁻¹A` normalises by whatever degree the graph supplies, and the
   gain is 1 by construction at BOTH connectivities. **This is VERIFIED, not
   assumed: row-sums of `D⁻¹A` are checked == 1 to 1e-12 in STEP 1.**

**NO FLOAT IS COMMITTED BY THIS RUNG.** `γE=1.7`, `γI=−1.4`, `16`, `σ_E`, `σ_I`,
`α_E`, `α_I`, `μ=0.024` appear **NOWHERE** — as in the settling rung, which
committed none. `connectivity` is an **integer anatomy selector already present
in committed code** (`wire_sheet`'s signature), defaulting to 4; the seed still
ships `settle=0, bubble=0` (§9).

---

## 5. §13.1 — COULD THIS PRODUCE THE OPPOSITE? THE CONTROL THAT CAN FAIL

**The forced half, conceded up front:** non-bipartiteness ⇒ λ_min > −1 is a
**theorem**. That half of STEP 1 **cannot fail**, so **it is not evidence and I
claim none for it** (§13.1). The falsifiable half is **ρ(M) < 1** and **whether
the rectified loop actually terminates** — neither is forced, and §1.3 pre-commits
to stopping if either fails.

**THE ORIENTATION TRAP, AND WHY I PRE-REGISTER NO OSI ARM.**
**GCAL makes orientation FROM ISOTROPIC DISKS.** Therefore *"orientation
appeared"* **cannot discriminate a working mechanism from a forced one** — the
settling rules force a **BUBBLE**, and on a thin travelling wavefront a bubble
**is** an oriented segment **by construction**. That is §13.1's third category
(architecture that forces the signature) and I will not walk into it.

**The control that could fail, if an orientation arm is ever run (NOT here):**
the **DISK arm** — the same rules on isotropic input. If oriented structure
appears on wavefronts AND on disks, the bubble is doing it and the input is not.
If it appears on neither, the mechanism is null. **No rule in this seed can
rescue either outcome.** That arm is NOT run under this pre-registration and
**nothing about orientation is claimed by it.**

**The control that CAN fail HERE, and it is the whole rung:**
- **c=4 is the paired control for STEP 1/2**, and it is *known to fail* — it must
  reproduce λ_min = −1.000000 and hit the cap. If **c=4 also converged**, my
  operator would not be the sibling's and the comparison would be meaningless.
- **STEP 2 can fail with STEP 1 passing** (spectrum ≠ rectified map).
- **STEP 3 is conjunctive** (§4) and fails if settling is inert — the
  §1-clause-5 catch that the settling rung's own first cut needed (`rate == aff`
  to the last digit).

---

## 6. THE ARCHITECTURE RULE IS THE EXPERIMENT (CLAUDE.md)

Every settling decision is a **seed rule** (`seeds/vision_settle.json`,
unmodified by this rung). The ablation is **graph DATA** (`SettleParams`). The
adapter states **anatomy** (`wire_sheet` — which units are lattice-adjacent) and
**writes params**. `connectivity` selects which lattice offsets are wired: it is
an **anatomical fact stated as edges**, not a conditional over graph state. **A
Python `if` deciding lateral dynamics fails the experiment, not just the review.**

`wire_sheet(connectivity=8)` **already exists in the committed adapter** and is
untested; this rung tests it. **I do not edit another rung's seed** (§11 rule 4).

---

## 7. §9 / §12 COMPLIANCE

- `vision_settle` continues to ship **INERT** (`settle=0`, `bubble=0`); no
  committed script loads it; `wire_sheet`'s default stays `connectivity=4`.
- Byte-identity to re-verify: fm0 **VACUOUS** (`D == 0.0`); fm0b
  `8.071079e-01 / 5.315726e-01 / 4.013261e-01 / 5.169134e-01`; the sd orbit law
  `{2:1, 3:2, 4:2, 6:2, 12:4}` with scrambled floor 12; Troxler 7/7.
- Bench: `scripts/rung7_vision_bench.sh` — the **named 20-file selector**, never
  `-k vision`. **Quoted WITH ITS CONDITION** (§10.2): `200/0` **with** `data/`
  (symlinked), not `190/10`.
- Config reads use `param()` / `PickUnique`-guarded singletons — **`PickUnique`
  PANICS on an ambiguous read** (§9).
- **Never `git add -A`.** Only my own files, by name. **The runner is COMMITTED**
  (§12).
- The probe is rung 8D's **CALIBRATED** one (IDEAL 0.9989, FLOOR 0.2691, n_dead=0)
  and is **NOT rebuilt** (§1/§5). **`peak/base` is NEVER read** (blown up in
  three rungs). **`osi()`'s argmax-over-exact-ties lottery** means floors are
  measured **in-run**, never assumed — but **no OSI arm is run here** (§5).

---

## 8. WHAT A NULL MEANS (§3.5)

- **STEP 1 null** (λ_min ≤ −1, or ρ ≥ 1): the sheet's spectrum still forbids a
  fixed point. The settling loop remains BUILT and INERT; the engine's
  single termination semantics remains the blocker; **route 3 (a bounded-iteration
  Rust Term) becomes the only route left, and its §13 tension — it hands the count
  back as a constant — is REAL and I am not resolving it by fiat.**
- **STEP 2 null:** the linearisation lied; the rectification is the blocker.
- **STEP 3 null:** 8D's prediction **CONFIRMED** — no η is both convergent and
  load-bearing **even with settling** — which would explain nine rungs in one
  stroke and is a **stronger** result than a pass.

**No outcome here reopens the paradigm claim (§7). A diagnosed negative beats an
un-understood positive; four results have been retracted in this arc. I will not
rescue.**
