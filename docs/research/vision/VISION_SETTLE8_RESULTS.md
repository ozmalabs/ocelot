# THE NON-BIPARTITE SHEET — RESULTS

**THE SHEET SETTLES. THE ENGINE CANNOT SEE THAT IT HAS. `λ_min = −1` WAS NEVER
THE BLOCKER — IN THE OPERATING REGIME THE ReLU HAD ALREADY DESTROYED THE
CHECKERBOARD, AT BOTH CONNECTIVITIES. THE REAL BLOCKER IS THAT `run_rules` TESTS
**EXACT FLOAT EQUALITY** AND A SETTLED SHEET **DITHERS AT ONE ULP, FOREVER.**

Pre-registration `VISION_SETTLE8_PREREG.md`, committed at **`536c0a31`
(2026-07-17 22:58:35+10:00)** — **before** any measurement. Engine
**`74fc035c8595`** @ `runners/dsl/python/substrate_rs/_native.abi3.so`,
**`shared` build — Rust source byte-identical to this tree** (this rung adds NO
Rust; legitimate under §10.1 rule 4). Base **`39f2ae29`** (the settling rung) —
**rebased, not merged**: my worktree was 3 commits BEHIND main and lacked
`seeds/vision_settle.json`, `domains/settle_world.py`, `scripts/settle_lib.py`
and `scripts/waveiso_lib.py`. `data/` **symlinked** from canonical (§10.2).
Runners committed: `scripts/settle8_spectrum.py`, `settle8_converge.py`,
`settle8_amplitude.py`, `settle8_dither.py`, `settle8_diagnose.py`,
`settle8_terminate.py`.

**Seeds 22000–22999: ALLOCATED, BURNED NONE, still CLEAN.** The rung stopped at
its pre-registered **STEP 2** gate. Every measurement is either DETERMINISTIC
linear algebra (no RNG) or runs on **already-burned seed 0**. **The eighth rung
to stop at a gate rather than burn a block.** 12000–21999 untouched.

**THIS IS ENGINEERING, NOT THE PARADIGM CLAIM (§7).** A working V1 is valuable
and **NOT novel** — GCAL already works. The sd rung's negative (*"the loop
composes what it holds; it does not discover what it lacks"*; `mints(N)` = orbits
under the held generators, 8/8 prospective) **stands untouched and is not
reopened by one word of this.**

---

## 1. THE HEADLINE

| the question | the verdict |
|---|---|
| **λ_min under c=8, predicted then measured** | **−0.4528 / −0.4612 / −0.4858 / −0.4885** (n_side 3/4/5/6) — **> −1**, as a THEOREM. Predicted ≈ −0.5 in advance, window (−0.6,−0.35): **all four inside**, converging on −0.5. |
| Did I stop at STEP 1? | **No** — λ_min > −1 **and** ρ(M) < 1, both pre-registered gates passed. |
| **Did the loop converge (§2)?** | **THE DYNAMICS: YES.** Amplitude ~1e-16 at c=8 in ρ-predicted sweeps. **THE ENGINE: NO.** c=8 terminated **9/20** steps, c=4 **1/20**. **STEP 2 FAILS its pre-registered criterion (c=8 had to terminate on EVERY step). STOP.** |
| **Did it give the learning rule an operating regime (8D)?** | **NOT ASKED. §2 forbids it, and my own prereg pre-committed the stop.** Still unanswered — and honestly so, for the second rung running. |
| **Which object did I build — fixpoint or bounded transient?** | **A FIXPOINT.** And — **verified from the primary MYSELF** — **that IS GCAL's object**, up to a tolerance. See §5: **the settling rung's central claim is an over-read, and its own document contains the correct reading.** |
| Is `connectivity=8` a magic number? | **No dial exists** (4 or 8), and the diagnosis predicted it from a theorem. **But it is not why anything improved** — see §4.3. |

**The one-sentence result:** *8-connectivity does exactly what the theorem says
to the LINEAR operator, the rectified loop settles at both connectivities, and
the engine still cannot terminate — because "settled" is a **tolerance
predicate** and `run_rules` has only **exact equality**, which is the one
criterion float arithmetic cannot deliver.*

---

## 2. STEP 1 — THE SPECTRUM. PREDICTED, THEN MEASURED.

The operator is read off the **graph's own `sunit_neighbour` edges**, wired by
the committed `wire_sheet` on the committed `lattice_centres` — never a
re-derived idealisation (the settling rung's `linspace` bug wired 12 edges where
24 were due, silently). Cross-checked: the minimal sheet's adjacency is
**identical** to a full `build_sheet` boot's, at both connectivities (24/24 and
40/40 edges at n_side=3).

| c | n_side | N | edges | bipartite | triangles | **λ_min(M)** | **ρ(M)** | λ₂(D⁻¹A) | ‖M·1‖ |
|---|---|---|---|---|---|---|---|---|---|
| 4 | 3 | 9 | 24 | **True** | 0 | **−1.000000** | **1.000000** | 0.577350 | 5.6e−17 |
| 4 | 4 | 16 | 48 | **True** | 0 | **−1.000000** | **1.000000** | 0.781736 | 5.6e−17 |
| 4 | 5 | 25 | 80 | **True** | 0 | **−1.000000** | **1.000000** | 0.868699 | 2.0e−16 |
| 4 | 6 | 36 | 120 | **True** | 0 | **−1.000000** | **1.000000** | 0.912769 | 3.6e−16 |
| 8 | 3 | 9 | 40 | **False** | 16 | **−0.452753** | **0.452753** | 0.365148 | 1.1e−16 |
| 8 | 4 | 16 | 84 | **False** | 36 | **−0.461214** | **0.667941** | 0.667941 | 5.6e−17 |
| 8 | 5 | 25 | 144 | **False** | 64 | **−0.485804** | **0.800156** | 0.800156 | 1.2e−16 |
| 8 | 6 | 36 | 220 | **False** | 100 | **−0.488508** | **0.867407** | 0.867407 | 3.6e−16 |

**The sibling's theorem REPRODUCES EXACTLY** (§12.4 — I verified it rather than
inherited it): c=4 is bipartite, 0 triangles, **λ_min = −1.000000, ρ = 1.000000**.
**The paired control that had to fail, failed.**

**The triangle counts independently confirm the adjacency**: 16/36/64/100 = **4
per 2×2 block** — each block is a K₄ (4 sides + 2 diagonals), and K₄ has exactly
4 triangles. 4/9/16/25 blocks. Nothing is off by one.

### 2.1 THE SCORECARD ON MY OWN PREDICTIONS (§3.7)

| prediction | outcome |
|---|---|
| **(a) λ_min > −1 at c=8** — 8-connectivity closes triangles ⇒ non-bipartite ⇒ Perron–Frobenius | **TRUE, AND FORCED. I CLAIM NO CREDIT** (§13.1). It could not fail. It is arithmetic, and it is reported as arithmetic. |
| **(b) λ_min(D⁻¹A) ≈ −0.5**, window **(−0.6, −0.35)**, from the infinite-lattice symbol `f(k)=[2cos kx+2cos ky+4cos kx cos ky]/8`, min `(u+v+2uv)/4 = −0.5` at `k=(π,0)` | **CONFIRMED, all four inside** — and **−0.4528 → −0.4612 → −0.4858 → −0.4885 converges on −0.5 from above** as the boundary fraction shrinks, which is the quantitative shape the derivation predicts. This one could have failed and did not. |
| the checkerboard `k=(π,π)` gives **exactly 0** under c=8 — 8-connectivity does not perturb that mode, it **annihilates** it | **CONFIRMED** structurally (0 → non-bipartite, 0 triangles → 16). |
| **(c) ρ(M) ∈ [0.5, 0.9]** | **3 of 4 inside. MISSED at n_side=3: 0.4528, BELOW my window.** Honest miss — at the smallest sheet the boundary is most of the graph. |
| **(d) c=4 reproduces λ_min=−1.000000, ρ=1.000000** | **CONFIRMED to six decimals.** |

**A caveat I did not predict and that matters: ρ(M) GROWS with the sheet** —
0.4528 → 0.6679 → 0.8001 → 0.8674. The spectral gap closes as the lattice grows.
**Extrapolated to a GCAL-scale sheet, ρ → 1 and settling becomes arbitrarily
slow.** Nothing here licenses a claim about a big sheet, and the trend runs
against one.

---

## 3. STEP 2 — THE DYNAMICS SETTLE. THE ENGINE DOES NOT TERMINATE.

### 3.1 The instrument correction that decided the rung (§1.1, §12)

**My first cut reported "LIMIT CYCLE period 2" for BOTH connectivities and they
are NOT THE SAME OBJECT.** The detector tested `array_equal` — exact bytes — and
called everything that failed it a limit cycle. **That is a lookup, not a
measurement.** The discriminator is **AMPLITUDE**:

| c | n_side | ρ(M) | predicted sweeps `log(ε)/log(ρ)` | measured sweeps | **amplitude** | verdict |
|---|---|---|---|---|---|---|
| 4 | 3 | 1.000000 | **∞** | 710 | **1.104e−02** | **TRUE LIMIT CYCLE** (9/9 active) |
| 4 | 4 | 1.000000 | **∞** | 373 | 8.882e−16 | converged (12/16 active) |
| 4 | 5 | 1.000000 | **∞** | 472 | 3.331e−16 | converged (21/25 active) |
| 8 | 3 | 0.452753 | 45 | **49** | 1.110e−16 | converged (9/9 active) |
| 8 | 4 | 0.667941 | 89 | **69** | 2.220e−16 | converged (13/16 active) |
| 8 | 5 | 0.800156 | 162 | **158** | 2.776e−17 | converged (23/25 active) |

**The sweep counts land on the ρ-derived prediction** (162 predicted, 158
measured) — geometric convergence to machine precision, arriving on schedule.
That is the strongest evidence in this document that the operator is the one I
think it is.

### 3.2 THE ReLU IS THE MECHANISM, AND `aff` DECIDES — 200 draws per cell

**The checkerboard eigenvector needs the WHOLE bipartite lattice. A lattice with
units clamped to zero is not bipartite.** So whether `λ_min=−1` bites is a
property of the **ACTIVE SET**, hence of `aff` — not of the lattice.

| c | n_side | frac TRUE cycle | **frac all-active** | median amp | max amp |
|---|---|---|---|---|---|
| 4 | 3 | **0.450** | **0.400** | 1.11e−15 | 2.32e−01 |
| 4 | 4 | **0.085** | **0.065** | 8.88e−16 | 1.05e−01 |
| 4 | 5 | **0.015** | **0.010** | 1.11e−15 | 9.12e−02 |
| 8 | 3/4/5 | **0.000** | — | ~1e−16 | ≤4.4e−16 |

**`frac_true` tracks `frac_all_active` almost exactly** (0.450/0.400,
0.085/0.065, 0.015/0.010). That is the mechanism, quantified: **the checkerboard
bites IF AND ONLY IF the ReLU leaves the entire lattice active.**

**And in the regime the sheet is ACTUALLY in — a sparse travelling wavefront
(sparsity 0.3):**

| c | n_side=3 | n_side=4 | n_side=5 |
|---|---|---|---|
| 4 | **0.005** | **0.000** | **0.000** |
| 8 | 0.000 | 0.000 | 0.000 |

**λ_min = −1 essentially NEVER bites in the operating regime — at c=4.** The ReLU
had already destroyed the checkerboard before 8-connectivity was asked to.

### 3.3 THE ENGINE — 20 steps, n_side=4, and the pre-registered verdict

```
c=4: terminated  1/20   [XXXXXXXXXXXXX.XXXXXX]
c=8: terminated  9/20   [..XXX.XXXX.XX.XX....]        ( . = terminated, X = burned the 200000 cap )
```

**PRE-REGISTERED PASS (§2): c=8 terminates on EVERY step. → 9/20. STEP 2 FAILS.
STOP. No STEP 3. No seed burned.**

### 3.4 WHAT THE CAP-BURNING STEPS ARE ACTUALLY DOING — the decisive tick-by-tick

Watched one application at a time, on a step that burns the cap:

```
c=4, step 0: act scale = 1.8358,  1 ULP = 2.220e-16
  tick 0: apps=1  d_act=0.000e+00  d_act_next=8.882e-16
  tick 1: apps=1  d_act=8.882e-16  d_act_next=0.000e+00
  tick 2: apps=1  d_act=0.000e+00  d_act_next=8.882e-16   ... forever
  => max delta on the orbit = 8.882e-16  (4.0 ULP)  -> ULP DITHER of a SETTLED sheet

c=8, step 2: act scale = 18.3001, 1 ULP = 3.553e-15
  tick 0: apps=1  d_act=3.553e-15  d_act_next=0.000e+00
  tick 1: apps=1  d_act=0.000e+00  d_act_next=3.553e-15   ... forever
  => max delta on the orbit = 3.553e-15  (1.0 ULP)  -> ULP DITHER of a SETTLED sheet
```

**BOTH are ULP dithers. Neither is an O(1) dynamics.** `st_settle` writes an
`act_next` one ULP away; `st_commit` copies it into `act`; `st_settle` writes it
back. **The sheet has SETTLED. The engine is oscillating between two adjacent
floats and calling it progress, 200,000 times per step.**

---

## 4. THE CORRECTED DIAGNOSIS — THE SIBLING'S CONCLUSION IS RIGHT AND ITS MECHANISM IS WRONG

The settling rung concluded:

> *"λ_min = −1.000000 exactly … A period-2 orbit is not a fixed point, so an
> exact-equality fixpoint provably cannot terminate … The synchronous fix did not
> rescue it, because the schedule was never the defect."*

**What survives:** the linear algebra (reproduced exactly, §2), and the
**conclusion** — *the engine expresses the settling DYNAMICS and cannot express
the settling TERMINATION*. That stands, and it is now **better supported**.

**What does NOT survive — three corrections:**

### 4.1 λ_min = −1 is NOT what stops the engine

The theorem is about the **LINEAR** operator `M`. The loop is
`act ← max(aff + M·act, 0)`, and **the ReLU is not `M`**. Measured: with the
sheet's actual sparse drive, the checkerboard survives the ReLU on **0.000–0.005**
of draws (§3.2). **The sibling generalised a linear-algebra fact to a rectified
loop without measuring the rectified loop** — and my own pre-registration named
this exact proviso in advance (§2: *"a spectral radius under 1 is strong evidence,
not a proof about the rectified map"*), which is the only reason I looked.

### 4.2 The real blocker is EXACT EQUALITY vs a TOLERANCE PREDICATE, and it is general

**`run_rules` terminates on exact value equality. "Settled" is an ε-predicate.**
A contraction's fixed point is generically **not exactly representable in
float64**, so the iteration lands in a **period-2 orbit between the two nearest
floats** and never satisfies exact equality. **This afflicts BOTH
connectivities** — c=4 burned 19/20, c=8 burned 11/20, and **every cap-burning
step measured, at both, is a ULP dither of a settled sheet.**

**This is a strictly more general and more damning diagnosis than the spectral
one.** It is not a fact about this sheet, this lattice, or this seed. **It is a
fact about exact-equality fixpoints over float arithmetic**, and it would afflict
any relaxation the substrate ever runs.

### 4.3 8-CONNECTIVITY HELPED — BUT NOT BY THE MECHANISM IT WAS PRESCRIBED FOR

**This is the §13.1 finding turned on the FIX itself, and it is the subtlest
thing in this document.**

- **Prescribed mechanism:** *"destroy the 2-colouring ⇒ remove λ=−1 ⇒ a fixed
  point exists ⇒ the loop terminates."*
- **What actually happened:** the ReLU had **already** destroyed the checkerboard
  in the operating regime, at c=4, before 8-connectivity was applied (§3.2). So
  removing λ=−1 **cannot** be what improved anything.
- **The real mechanism of the improvement (1/20 → 9/20):** `ρ(M) = 1.000000` is
  **MARGINAL** — round-off noise injected into the checkerboard mode **never
  decays**, so the last bit alternates forever. `ρ(M) = 0.668 < 1` **damps
  round-off too**, so the iteration can land on an exactly-representable fixed
  point **more often**. **9/20 is a probabilistic improvement in float landing,
  not a fix.**

**The prescribed mechanism and the observed improvement are different mechanisms
that happen to share a cause.** Had I reported *"8-connectivity destroyed the
checkerboard and termination improved"*, every word would have been true and the
causal claim would have been **false**.

---

## 5. WHICH OBJECT DID I BUILD? — AND THE SETTLING RUNG'S CENTRAL CLAIM IS AN OVER-READ

**I built a FIXPOINT.** The brief warned this may be a different object wearing
GCAL's name. **I verified it from the primary myself (§12.4), and independently
by a second reader with no sight of this tree. Both retrieved PMC6618482
directly. Both return the same verdict.**

**Verbatim, from the paper's Materials and Methods:**

> *"At t + 0.20 and every 0.05 iterations until t + 1.0, V1 continues to compute
> in a series of settling steps, **a fixed number sufficient to ensure that
> cortical activity is no longer changing significantly** (data not shown)."*

> *"Once all 16 settling steps are complete, the settled V1 activation pattern is
> deemed to be the V1 response to the presented pattern."*

> *"The afferent and lateral connections lead to the formation of isolated
> **bubbles of activity** in V1 in response to the input pattern."*

**"Sufficient to ensure that cortical activity is no longer changing
significantly" IS A CONVERGENCE CRITERION.** GCAL's 16 is a **practical stand-in
for "iterate until settled"** — a count that **FELL OUT** of an ε-criterion.
Neither reader found **any** statement that the settling fails to converge, that
the settled pattern is a transient, or that iterating further would change it.

**⇒ THE SETTLING RUNG'S §5.1 — *"GCAL does not converge either. It STOPS. GCAL
never asks whether the sheet settled; it sweeps 16 times and reads out"* — IS AN
OVER-READ OF THE WORDS "fixed number", AND ITS OWN §3 TABLE HOLDS THE CORRECT
READING:** *"we hold the **criterion**; GCAL holds a **count** that fell out of
it."* The two halves of that document contradict each other, and **the half the
rung built on is the wrong one.**

**⇒ AND THE BRIEF'S INSTRUCTION TO ME WAS WRONG IN THE SAME DIRECTION.** I was
told: *"the supervisor's 'GCAL's settling is a fixpoint' hint was FALSE and it
decided that rung. Do not inherit it."* **The hint was substantially RIGHT.** I
pre-committed both readings' consequences before retrieving the paper
(`VISION_SETTLE8_PREREG.md` §0.1) precisely so this could not be chosen after the
fact.

**So the objects are NOT identical, and the difference runs the SAFE way:**

| | GCAL | this rung |
|---|---|---|
| criterion | activity no longer changing **significantly** (ε-tolerance) | **exact float equality** |
| implementation | a count (16) that fell out of that criterion | `run_rules`' fixpoint |
| relation | **the WEAKER, satisfiable one** | **the STRONGER, UNSATISFIABLE one** |

**We are not a different mechanism wearing the same name. We are the SAME
mechanism with a stricter stopping rule — and the stricter rule is the one float
arithmetic cannot deliver.** GCAL's 16 is not a hack around a missing feature.
**It IS the tolerance predicate**, and the engine has no way to say it.

**The honest caveat, which the second reader found and I confirm:** the paper says
**"(data not shown)"**. The authors **assert** convergence rather than
demonstrate it; there is no stability analysis, no settling-error curve, no
eigenvalue argument anywhere in it. **So "16 reaches the fixed point" is GCAL's
own claim about GCAL, not a measured fact I can stand on.**

---

## 6. §13 — EVERY CONSTANT, AND WHAT IT FALLS OUT OF

**THIS RUNG COMMITS NO FLOAT. GCAL's `γE=1.7`, `γI=−1.4`, `16`, `σ_E`, `σ_I`,
`α_E`, `α_I`, `μ=0.024` appear NOWHERE** — as in the settling rung, which
committed none. Held.

| number | what it falls out of |
|---|---|
| `connectivity = 8` | **NOT a dial — a 2-element structural choice.** On a square lattice the neighbourhood is 4 (von Neumann) or 8 (Moore). You cannot tune 8 to 8.3. It is the lattice's **own unit cell** (3×3 minus centre) and introduces **no radius constant** — the same *"read the adjacency off the grid the units already sit on"* move, reading the **complete** local cell instead of the axis-only subset. **Pre-committed to c ∈ {4,8} ONLY; a third value would be a sweep and I would have stopped.** |
| the degree normalisation | **`D⁻¹A`'s rows sum to 1 — ASSERTED to 1e−12 at BOTH connectivities, not assumed.** §13's sharpening from the settling rung (*"a sum over degree-4 adjacency IS a gain of 4"*, `act → 2.5e224`) means **degree-8 is a gain of 8**; `st_settle`'s `Div(Fold(...), Max(Count,1))` is the degree-normalised MEAN, so the gain is **1 by construction at both**. |
| the −0.5 in my prediction | **DERIVED, not fitted** — the min of the infinite-lattice symbol. It is a prediction I could have got wrong, not a parameter. |
| 200000 | **the engine's pre-existing cap** (`wave_world.step`'s `s.tick(200_000)`), not mine. |
| **the ε a tolerance predicate would need** (§8) | **the float64 ULP at the sheet's own scale** — `np.spacing(scale)`. See §8: this is a real §13 candidate, and it is why the route matters. |

### 6.1 The half of the `connectivity=8` argument that runs AGAINST me

**Both 4 and 8 are lattice artifacts. Neither is biology. Real cortex has no
lattice.** The constant-free version — a distance-based neighbourhood — needs a
**radius**, which is exactly the constant (`σ_E`) §13 forbids importing. **So 8
is not "correct"; it is the LESS artifactual of the only two options the lattice
offers**, chosen on a stated structural argument and a spectral theorem, not on
its output.

**What supports it beyond taste, and it is in this tree in writing, before this
rung:** `VISION_PRIOR_ART.md` **E11** — *"the deterministic **4-connected argmin**
only steps N/S/E/W, a **cardinal-axis artifact that would tell the agent the
answer**"*; **E14** — *"our **4-neighbour lattice is below biological coordination
number**, and percolation threshold depends directly on it."* **In an ORIENTATION
experiment, the cardinal axes are the axis of the dependent variable.**

**But §4.3 is the honest verdict on it: it is not why anything improved.**

---

## 7. §13.1 — COULD THIS HAVE PRODUCED THE OPPOSITE? THE CONTROLS THAT COULD FAIL

**The forced half, conceded up front and claimed as nothing:** non-bipartite ⇒
λ_min > −1 is a **theorem**. It could not fail. **It is arithmetic and I claim no
credit for it** (§13.1).

**The controls that COULD fail — and the rung is decided by one of them failing:**

1. **STEP 2's PASS criterion FAILED.** c=8 had to terminate on **every** step. It
   terminated on **9/20**. **The measurement that killed the rung is the one the
   rung was built to pass.**
2. **`c=4` is the paired control** and it behaved **differently** (1/20 vs 9/20),
   so the comparison is real and the instrument is not measuring nothing. *(Note:
   c=4 terminated **1/20**, not 0/20 — even the bipartite sheet lands exactly
   sometimes, which is itself evidence for the float-landing mechanism of §4.3
   and against the spectral one.)*
3. **`ρ(M) < 1` was NOT forced** and could have come back ≥ 1 (the rank-1 `J` term
   on a **non-regular** graph — degrees 3/5/8 — means
   `spec(M) ≠ {0} ∪ spec(D⁻¹A)\{1}`; it had to be measured). It came back < 1.
4. **My quantitative λ_min prediction could have missed** and did not; **my ρ
   window DID miss** at n_side=3 (§2.1).

**NO ORIENTATION ARM WAS RUN, AND NONE WAS PRE-REGISTERED — deliberately.**
**GCAL makes orientation from ISOTROPIC DISKS**, so *"orientation appeared"*
cannot discriminate a working mechanism from a forced one. The settling rules
force a **BUBBLE**; on a thin wavefront a bubble **is** an oriented segment **by
construction** — §13.1's third category. **Nothing about orientation is claimed
by this rung.** The control that would be required (the **disk arm** — same
rules, isotropic input) is named, not run.

---

## 8. WHAT A NEXT ATTEMPT MUST DECIDE — AND THE §13 TENSION THE SIBLING DECLARED UNRESOLVED IS RESOLVABLE

The settling rung left route 3 with a stated tension:

> *"A bounded-iteration Term in Rust would give the engine GCAL's actual
> semantics (sweep k times, stop) … but it hands the count back as a constant,
> which is precisely what §13 forbids importing. That tension is unresolved."*

**§5 dissolves the premise: GCAL's 16 is not a count, it is a TOLERANCE. And a
tolerance does NOT have to be imported — there is one the system already
supplies.**

**THE ROUTE THIS RUNG'S EVIDENCE POINTS AT: a fixpoint up to the ARITHMETIC'S OWN
RESOLUTION.** `run_rules` currently progresses when a `SetAttr` writes a value
that differs **at all**. Every cap-burning step measured, at both connectivities,
differs by **exactly 1–4 ULP** of a **settled** sheet. A `SetAttr` that does not
progress **when the new value is within the float resolution of the old** would
terminate every one of them.

**And that ε is a §13 number that FALLS OUT, not one that goes in:**

- it is **`np.spacing(x)`** — the float64 mantissa's own resolution at the
  sheet's own scale;
- it is **RELATIVE**, so it satisfies §13's corollary directly (*"an absolute
  constant IS a view from nowhere; ratios transfer, absolutes do not"*) — it is a
  fraction of a dynamic range **the system measures for itself**;
- it is fixed by **something real the system already has** — its arithmetic's
  noise floor — and **not by the answer I wanted**. That is §13's own test, and it
  passes it.
- **It imports NOTHING from GCAL.** GCAL's ε is "not changing *significantly*" in
  GCAL's units; ours would be the ULP in ours. **Same mechanism, own frame** —
  which is exactly what §13 demands (*"import a paper's MECHANISM, never its
  CONSTANTS"*).

**I am NOT claiming this works — I did not build it, and this rung burns no seed
on an unrun claim.** Three things must be decided first, and none by fiat:

1. **Is a ULP-tolerance fixpoint SOUND for the engine at large?** It changes
   `run_rules`' termination semantics for **every rule in every seed**, not just
   settling. §9's byte-identity is the gate, and the blast radius is the whole
   tree.
2. **Is `np.spacing` the right ε, or is it `n·ULP`?** The measured dithers are
   1.0–4.0 ULP, so a 1-ULP threshold would **not** catch the 4-ULP one.
   **The moment that becomes "tune it to 4", it is a magic number** and §13 kills
   it. What does the factor fall out of? **I do not know, and that is the open
   question, stated as open.**
3. **ρ(M) → 1 as the sheet grows** (§2.1). On a GCAL-scale sheet the settling is
   arbitrarily slow regardless of termination semantics. **A tolerance fixpoint
   fixes the STOPPING, not the MIXING.**

**The other routes stand where the settling rung left them:** damping
(`α` is a **KNOB** and must be named one); a bounded-iteration Rust Term
(now known to be **GCAL's ε in disguise**, so it is the tolerance route with the
tolerance hidden inside a count — **the worse form of the same idea**).

---

## 9. WHAT I GOT WRONG

1. **I built a cycle detector that could not tell a limit cycle from a rounding
   error, and it nearly decided the rung.** `array_equal` returns "not a fixed
   point" for a sheet that has settled to 1e−16. **An exact-equality test is a
   LOOKUP, not a measurement of dynamics** — §1.1's disease in a new costume. The
   amplitude is the discriminator and I did not measure it until the sweep counts
   (158 vs a ρ-predicted 162) made the omission impossible to ignore.
2. **I read `|act − act_next|` off a single snapshot and got `0.000e+00` on a
   sheet that was dithering forever.** The residual is **PHASE-DEPENDENT** — zero
   on the post-commit phase, 1 ULP on the post-settle phase. **I nearly reported
   "the residual is exactly zero and the engine still burns the cap" as an
   unexplained anomaly.** The tick-by-tick is the instrument; the snapshot is a
   proxy, and a proxy read at one phase of a period-2 orbit is a coin flip.
3. **My ρ window missed at n_side=3** (0.4528 vs a predicted [0.5, 0.9]) — §2.1.
4. **I did not predict that ρ grows with the sheet**, which is the caveat that
   most limits what any of this would mean at GCAL scale.
5. **I nearly credited 8-connectivity with the improvement it did not cause**
   (§4.3). Every word of *"8-connectivity destroyed the checkerboard and
   termination improved 1/20 → 9/20"* is true and the causal claim is **false** —
   the ReLU had already destroyed the checkerboard at c=4.

---

## 10. §9 — DEFAULTS PRESERVE COMMITTED RESULTS

`scripts/rung7_vision_bench.sh` (the **named 20-file selector**, never
`-k vision`): **200 passed / 0 failed / 0 skipped** at engine `74fc035c8595`.

**Quoted WITH ITS CONDITION (§10.2): the `200/0` WITH `data/` number, not
`190/10`.** My worktree symlinks `data/` from canonical, so the 10 BSDS300 tests
that *"have never run in a worktree"* ran here and passed.

`vision_settle` still ships **INERT** (`settle=0`, `bubble=0`) — **unmodified by
this rung**; `wire_sheet`'s default stays `connectivity=4`. **No committed file
was edited: this rung adds only new `scripts/settle8_*.py`, its
pre-registration, and this results file.** No seed, no adapter, no other rung's
anything (§11 rule 4). No Rust. `PickUnique` config reads are the seed's own,
untouched.

---

## 11. SCOPE — WHAT IS **NOT** SHOWN (§8)

- **NOTHING about orientation.** No arm was run; none was pre-registered; the
  disk control that would be required is named and not run.
- **NOTHING about 8D's question.** *"Is there an η at which the learning rule is
  both convergent and load-bearing?"* remains **UNANSWERED** for the second rung
  running — §2 forbids the arm on a scaffold that does not settle, and my own
  pre-registration pre-committed the stop.
- **NOTHING about a large sheet.** ρ(M) → 1 as N grows; every number here is
  n_side ≤ 6 (N ≤ 36). GCAL's sheet is far larger and the trend runs against me.
- **NOTHING about whether GCAL's settling literally converges.** GCAL **asserts**
  it, "(data not shown)". I verified **what the paper says**, not that it is true.
- **NOTHING about the paradigm claim (§7).** This is engineering. A working V1
  would be valuable and **not novel**. **The sd rung's negative stands
  untouched.**

**The honest summary: the missing cortical layer settles — its dynamics reach a
fixed point to machine precision, on schedule, at a rate the measured spectrum
predicts. The engine cannot terminate on it, and the reason is neither the
lattice nor the schedule nor the spectrum: `run_rules` has exactly one
termination semantics — exact float equality — and a settled sheet dithers at one
ULP forever. GCAL's "16" is that missing tolerance predicate, wearing a count's
clothes. That is a diagnosed negative (§7), it is more general than the one it
replaces, and it cost no seed.**
