# The `w0` initialisation ablation — is the DC prior LOAD-BEARING?

**Engine:** `95167c01b7b3 @ runners/dsl/python/substrate_rs/_native.abi3.so`
(§10). **Commit:** worktree branch off `gamma-substrate/developmental-vision`
@ `692b36d51b`.
**Selector discipline (§12):** every number below names its script explicitly.
No `-k vision` anywhere in this document.

> **§10/§11 CONTRADICTION, FOUND AND RECORDED.** The protocol says the
> `substrate_rs.pth` fix makes the engine unambiguous "in every process, any
> cwd". It does not, in a worktree: the `.pth` contains an **absolute path into
> the canonical tree**
> (`/home/matt/ozma/internal/research/experiments/gamma-substrate/runners/dsl/python`),
> and the `.so` is **gitignored**, so a fresh worktree has NO engine of its own
> and silently resolves to **another tree's binary** — the exact hazard §10
> exists to kill, reintroduced by §11's isolation requirement. The two rules are
> incompatible as written.
>
> **What I actually loaded, verified rather than assumed:** I copied the
> canonical release `.so` into this worktree's `runners/dsl/python/substrate_rs/`
> (a PRIVATE copy — never a global install, §11.2) and every script here
> `sys.path.insert(0, …)`s the worktree path ahead of the `.pth`. Verified by
> `provenance_line()` at the head of every run: **`engine 95167c01b7b3 @
> …/agent-a00f8c2f0650cd637/…/_native.abi3.so`** — the worktree's own copy, hash
> identical to the canonical artifact. The copy is gitignored and is not
> committed. **Recommendation for the supervisor:** the `.pth` should resolve
> relatively, or the provenance gate should assert the loaded path is inside the
> CURRENT tree; today it can only assert the hash.

---

## 1. The charge

An adversarial review found that `domains/wave_world.py:285`'s
`add_units(w0=1.0, jitter=0.05)` — commented **"NOT structure, just a
tie-break"** — is a large **DC prior**: every initial weight strictly positive,
essentially all of the RF's power in its constant component. That is **rung 5's
measured root cause** (`frac(w<0)=0.0000` ⇒ DC-dominated response ⇒ OSI 0.004)
**present before any rule fires**. No init ablation exists anywhere in this arc.

The comment is **false as written** and I wrote it. A tie-break needs only the
jitter; the `w0` offset is a separate, large, structural prior. Whether it is
*load-bearing* is a different question from whether it is *there*, and this
document answers both.

## 2. The arms

Expressed as an adapter parameter, `add_units(init=…)`, threaded through
`add_cortex`. **The committed default is untouched** (§9): `init="multiplicative"`
is the committed expression character-for-character, and the RNG draw sequence is
identical across arms (one `normal()` per synapse), so the arms differ in the
initial weights and in **nothing else**.

| arm | formula | rationale |
|---|---|---|
| **DC** | `w = max(w0*(1+jitter*N), 1e-3)`, w0=1.0, jitter=0.05 | **the committed default** |
| **ZERO** | `w = w0 + jitter*N`, w0=0.0, jitter=0.05, no clamp | signed, DC-free |
| **ZEROM** | `w = w0 + jitter*N`, w0=0.0, jitter=1.0, no clamp | signed, DC-free, **‖w‖ matched to DC** |

**ZEROM is declared in advance and is not a sweep.** DC has ‖w‖≈7.0; ZERO has
‖w‖≈0.35. Oja's dynamics are norm-dependent (the decay term is `eta*y^2*w`), so a
ZERO arm that failed could fail for the trivial reason that it started 20× too
small. ZEROM holds ‖w‖ at DC's value and varies **only** the DC component. If
ZERO and ZEROM agree, the norm is not the explanation. η=5e-4 is FROZEN
throughout — the committed regime, not a search.

## 3. MY PREDICTION, STATED IN ADVANCE (PROTOCOL §3.7)

*Written and committed **before** `w0_part1`/`w0_part2`/`w0_part4`/`w0_part5`
produced any output. PART 0 (the init itself) and PART 3 (rung 6's architecture)
had run; nothing that fires a learning rule had.*

**I predict the DC prior is REAL but NOT LOAD-BEARING, and that rung 5's OSI
0.004 does NOT lift under a zero-mean init.**

The mechanism, and it is why I am willing to predict against the review:

- Oja's rule as built is `w ← w(1 − ηy²) + ηyx` with **y = w·x and no mean
  subtraction**. Its attractor is therefore the leading eigenvector of the
  **second-moment** matrix `E[xxᵀ]`, *not* of the covariance.
- The retina's input is **binary and non-negative** (`x ∈ {0,1}`), so `E[xxᵀ]` is
  **elementwise non-negative**. By **Perron–Frobenius**, the leading eigenvector
  of an elementwise-non-negative matrix can be chosen **non-negative**.
- So Oja's fixed point on this input is non-negative *whatever the init*, up to
  the overall sign (a run could converge to −v, which is uniformly non-positive
  and just as DC-dominated). **The DC mode is imposed by the INPUT's
  non-negativity meeting Oja's second-moment attractor — not by `add_units`.**

**The provisos, named in advance, each of which would break the prediction:**

1. **Sign.** Perron–Frobenius fixes the eigenvector up to sign; a zero-mean init
   could land in the −v basin. That does **not** rescue OSI (a uniformly negative
   RF rectifies to silence, which is worse), but it would show as
   `frac(w<0)→1.0` and I would be wrong about the *description* even while right
   about the OSI.
2. **Convergence.** ZERO/ZEROM are different dynamical starting points. If either
   fails PROTOCOL §2 the arm is a transient and **stops there** — no OSI claim.
   ZERO's small ‖w‖ makes `y` small, so early learning is slow; this is exactly
   what ZEROM controls for.
3. **Rung 2/4 are probably insensitive for a SECOND, independent reason.** Their
   statistic is `orientation_selectivity(rf)`, a **spectral moment that ignores
   the DC bin**. PART 0 already shows this: all three inits score anisotropy
   **0.1525**, identically. If so, rungs 2/4 cannot move by construction, and
   that is a fact about the measure, not evidence about the prior.
4. **The prediction is only about THIS input.** On a zero-mean input (an OFF
   pathway, rung 6's subtraction) the argument collapses — `E[xxᵀ]` is no longer
   non-negative and Oja can find a signed component. That is precisely rung 6's
   design and precisely why rung 6 is the right next rung.

**If I am wrong** — if OSI lifts materially under ZERO/ZEROM — then "our Units
are blind" is an **adapter artifact**, rungs 5 and 6 were measuring the
initialisation, and rung 6 was built to remove a blocker that a one-line init
change would have removed. **That is a finding, not a failure**, and it would
retract rung 5's root-cause diagnosis.

## 4. PART 0 — the init itself (`scripts/w0_part0_init.py`)

**The reviewer's numbers REPRODUCE.** No rule has fired; step 0; n=8 seeds.

| arm | DC power frac | DC:structure | frac(w<0) | ‖w‖ | anisotropy |
|---|---|---|---|---|---|
| **DC** | **0.99758** | **431:1** | **0.0000** | 7.006 | 0.1525 |
| ZERO | 0.02173 | 0.022:1 | 0.5021 | 0.347 | 0.1525 |
| ZEROM | 0.02173 | 0.022:1 | 0.5021 | 6.938 | 0.1525 |

The no-DC floor for a 7×7 RF is `1/N = 0.02041`; both zero-mean arms sit on it.
The review's figures were **0.99798 / 494:1** and **0.01366**; mine are
**0.99758 / 431:1** and **0.02173**. The small gaps are draw-level and
directionally irrelevant — an analytic check on the same formulae, with no engine
in the loop, gives 0.99756 / 426:1 / 0.0000 and 0.02065 / 0.4979. **The charge is
upheld: the committed init is a ~430:1 DC prior with `frac(w<0)` exactly 0, and
the "just a tie-break" comment is wrong.**

**Note the last column, and it is the first substantive finding.** Anisotropy —
**rung 1/2/4's entire statistic** — is **identical (0.1525) across all three
inits**, because `orientation_selectivity` is a spectral moment that ignores the
DC bin. The measure those rungs use is *blind to the prior by construction*.

## 5. PART 3 — rung 6: the ablation is ARCHITECTURALLY EMPTY (`scripts/w0_part3_rung6.py`)

Rung 6 cannot be run "both ways", and the reason is itself the finding, so it is
**measured rather than asserted** (n=8 seeds, 6 SUnits each):

| quantity | DC power frac | DC:structure | frac(w<0) |
|---|---|---|---|
| ONE CHANNEL (`w⁺`), Dale-clipped | 0.99766 | 425.6:1 | 0.0000 |
| **EFFECTIVE RF (`w⁺ − w⁻`) — what the SUnit READS** | **0.02316** | **0.024:1** | **0.4915** |

(no-DC floor `1/49` = 0.02041.)

1. **A zero-mean init is forbidden by the architecture, not by taste.**
   `oo_learn_sub` clips every weight to `[0, oo_wmax]` — Dale's law, a **rule the
   agent holds**. A negative initial weight is not a different arm; it is a state
   the first rule firing deletes.
2. **Rung 6 has no DC prior to ablate.** Its cells read `w⁺ − w⁻`, and ON/OFF
   start at the same `w0` with *independent* jitter, so the effective RF starts
   **at the no-DC floor** with `frac(w<0)≈0.49`. `add_signed_units`'s docstring
   claimed this; it is now measured.

**Therefore rung 6's convergence failure — runaway at η=5e-4, empty at the 0.3168
floor at η=1e-4 — CANNOT be an artifact of the DC prior**, because there is no DC
prior in the quantity its rules and its probe both read. Rung 6's stated
diagnosis (ensemble degeneracy: `x_OFF = 1−x` determines the OFF channel exactly,
so the channels carry no independent correlation structure) is untouched by this
ablation.

## 6. PART 1 — CONVERGENCE, PER ARM (`scripts/w0_part1_convergence.py`)

PROTOCOL §2, run BEFORE any comparison, on waves alone. n=8 burned seeds (0–7),
η=5e-4 frozen. 0/1728 NaN weights at every checkpoint, every arm.

| arm | steps | anisotropy | drift | DC frac | frac(w<0) | ‖w‖ |
|---|---|---|---|---|---|---|
| **DC** | 0 | 0.1525 | — | 0.9976 | 0.0000 | 7.006 |
| | 1600 | 0.2851 | 0.1977 | 0.9834 | 0.0000 | 1.117 |
| | 3200 | **0.2897** | 0.1371 | 0.9664 | 0.0000 | 1.026 |
| | 6400 | 0.2701 | **0.1129** | 0.9481 | **0.0000** | 1.003 |
| **ZERO** | 0 | 0.1525 | — | 0.0217 | 0.5021 | 0.347 |
| | 3200 | 0.1637 | 0.2017 | 0.0922 | 0.4630 | 0.394 |
| | 6400 | **0.1685** | **0.2463** | **0.1104 ↗** | **0.4549 ↘** | 0.408 |
| **ZEROM** | 0 | 0.1525 | — | 0.0217 | 0.5021 | 6.938 |
| | 3200 | 0.1915 | 0.2776 | 0.2858 | 0.3423 | 3.084 |
| | 6400 | **0.2395** | **0.2922** | **0.4281 ↗** | **0.2716 ↘** | 2.541 |

**Three facts, and they decide the whole ablation:**

1. **The DC arm CONVERGES** (drift 1.79 → 0.113, falling monotonically;
   anisotropy plateaus ≈0.29). It is the only arm entitled to a fixed-point
   claim, and it is the arm every committed rung ran.
2. **NEITHER zero-mean arm converges by 6400** (drift ~0.20–0.29, flat or
   *rising*). Under §2 that is *"never converges ⇒ the scaffold is a TRANSIENT
   and every arm is measured at an arbitrary point on a decay curve"* — **so no
   fixed-point claim is read off them**, exactly as rungs 5 and 6 correctly
   stopped.
3. **But the DIRECTION of travel is unambiguous, monotonic, and identical at
   both norms: TOWARD THE DC MODE.** DC frac rises 0.022 → 0.110 (ZERO) and
   0.022 → 0.428 (ZEROM); frac(w<0) falls 0.502 → 0.455 and 0.502 → 0.272. The
   DC arm meanwhile holds frac(w<0) at **exactly 0.0000 for 6400 steps** — Oja
   never makes a single weight negative on this input.

**That is the prediction's mechanism showing up as dynamics** (§3): the
non-negativity is being imposed by the *input* meeting Oja's second-moment
attractor, and a zero-mean init does not escape it — it is *dragged out of*
zero-mean. ZEROM (20× the norm, so ~20× the effective learning speed on `y`)
travels the same road much faster, which is the norm control doing its job.

## 7. PART 2 — RUNG 5's PRECONDITION (`scripts/w0_part2_rung5.py`)

Rung 5's OWN frozen probe, unchanged. **The instrument reproduces exactly**:
ideal signed Gabor **OSI 1.0000**, ideal Gabor+DC **OSI 0.0000** — rung 5's two
calibration references, to four decimals.

| condition | arm | OSI | OSI max | anisotropy | frac(w<0) | DC frac | base/act |
|---|---|---|---|---|---|---|---|
| UNTRAINED | **DC** | **0.0040** | 0.0143 | 0.1525 | 0.0000 | 0.9976 | 1.011 |
| UNTRAINED | ZERO | **0.3899** | 1.0000 | 0.1525 | 0.5021 | 0.0217 | 1.000 |
| UNTRAINED | ZEROM | **0.3899** | 1.0000 | 0.1525 | 0.5021 | 0.0217 | 1.000 |
| TRAINED 1600 | **DC** | **0.0041** | 0.0148 | 0.2851 | 0.0000 | 0.9834 | 1.012 |
| TRAINED 1600 | ZERO | **0.3693** | 1.0000 | 0.1591 | 0.4702 | 0.0785 | 1.010 |

**Rung 5's headline REPRODUCES on the DC arm to four decimals**: OSI **0.0040**
untrained, **0.0041** trained, against its quoted 0.004 / floor 0.0044.

**AND THE ZERO-MEAN ARM IS NOT A LIFT — IT IS ITS OWN FLOOR.** This is the trap
the arc has fallen into repeatedly and it nearly caught me: `0.3693` looks like a
92× improvement over `0.0041` until you read the row above it. **An UNTRAINED
zero-mean unit — random signed weights, no rule has ever fired — scores 0.3899.**
Training *lowers* it to 0.3693. The units learn **no** orientation selectivity
under a zero-mean init; they sit at (very slightly below) the random floor for
their own initialisation, and their weight anisotropy (0.1591) is likewise at the
random floor (0.1525).

**Both inits are blind. The DC arm is blind at 0.004 against a floor of 0.004;
the zero-mean arm is blind at 0.37 against a floor of 0.39.**

**The full rung-5 table** (n=8 burned seeds 0–7; the DC rows ARE rung 5's
committed measurement, reproduced):

| condition | arm | OSI | anis | frac(w<0) | DC frac |
|---|---|---|---|---|---|
| UNTRAINED | DC | 0.0040 | 0.1525 | 0.0000 | 0.9976 |
| UNTRAINED | ZERO | **0.3899** ← *its floor* | 0.1525 | 0.5021 | 0.0217 |
| UNTRAINED | ZEROM | **0.3899** ← *its floor* | 0.1525 | 0.5021 | 0.0217 |
| TRAINED 1600 | DC | 0.0041 | 0.2851 | 0.0000 | 0.9834 |
| TRAINED 1600 | ZERO | 0.3693 | 0.1591 | 0.4702 | 0.0785 |
| TRAINED 1600 | ZEROM | 0.3003 | 0.1595 | 0.4256 | 0.1285 |
| TRAINED 3200 | DC | **0.0045** | 0.2897 | 0.0000 | 0.9664 |
| TRAINED 3200 | ZERO | **0.3665** | 0.1637 | 0.4630 | 0.0922 |
| TRAINED 3200 | ZEROM | **0.2580** | 0.1915 | 0.3423 | 0.2858 |

**Every trained zero-mean cell is BELOW its own untrained floor** (0.3665 and
0.2580 vs 0.3899), and ZEROM — the arm that travels fastest toward the DC mode —
falls the furthest. **Training does not build orientation selectivity under a
zero-mean init; it erodes the accidental selectivity of random signed weights,
in the direction of the DC arm.**

### 7.1 A SECOND FINDING, and it is a PROTOCOL §1 defect in the arc's instrument

**The OSI measure's random floor is INIT-DEPENDENT: 0.0044 for DC weights,
0.3899 for signed weights — an 89× difference on the SAME probe.** §1 says *"run
the measure on random input — it must score at the floor"*. On random **signed**
weights this measure scores **0.39**, i.e. it **passes noise at 39% of its
range**.

- Rung 5's *"OSI 0.004 (floor 0.0044)"* is **correct for its own arm** — DC
  weights, DC floor, honestly matched — and rung 5's conclusion is unaffected.
- **But that floor is not the measure's floor**, and any comparison that carries
  it across an architecture boundary is a category error. Rung 6's *"through the
  IDENTICAL frozen probe on which rung 5's units scored OSI 0.004, an ideal split
  cell scores 0.9115"* invites exactly that reading — against a **signed** floor
  the honest contrast is 0.9115 vs **~0.32–0.39**, not vs 0.004.
- **Rung 6's actual gate got this right** and independently corroborates the
  number: it used its own untrained floor of **0.3168** with SESOI 0.0595 — the
  signed-RF noise floor, arrived at from the other direction. **Two rungs, two
  architectures, one floor ≈0.32–0.39 for signed RFs.** The methodology was
  sound; only the rhetorical juxtaposition is loose. Recorded so no future rung
  quotes 0.0044 at a signed layer.

## 8. PART 1B — WHERE ARE THE ZERO-MEAN ARMS GOING? (`scripts/w0_part1b_longhorizon.py`)

§2's check, completed at an adequate horizon (n=4 burned seeds 0–3, η=5e-4
frozen, **51 200 steps = 16× rung 5's**). Extending a horizon that was measured
to be too short is completing §2, not a sweep: no parameter is searched.

| arm | steps | anisotropy | drift | DC frac | frac(w<0) | ‖w‖ |
|---|---|---|---|---|---|---|
| **DC** | 3200 | 0.2899 | — | 0.9657 | **0.0000** | 1.025 |
| | 12800 | 0.2819 | 0.1340 | 0.9311 | **0.0000** | 1.001 |
| | 51200 | **0.2787** | 0.1571 | **0.9246** | **0.0000** | 1.001 |
| **ZERO** | 3200 | 0.1664 | 0.5541 | 0.0855 | 0.4704 | 0.391 |
| | 12800 | 0.1763 | 0.2431 | 0.1184 | 0.4548 | 0.419 |
| | 51200 | **0.1856** | 0.2567 | **0.1567 ↗** | **0.4362 ↘** | 0.445 |
| **ZEROM** | 3200 | 0.1931 | 1.2020 | 0.2776 | 0.3519 | 3.270 |
| | 12800 | 0.2658 | 0.2965 | 0.5085 | 0.2314 | 2.304 |
| | 51200 | **0.2721** | 0.2570 | **0.6693 ↗** | **0.1565 ↘** | 1.819 |

**The DC arm never makes a single negative weight in 51 200 steps.**
`frac(w<0) = 0.0000` at every checkpoint, at every horizon, in every arm that
starts DC. That is Perron–Frobenius, observed: **Oja on non-negative binary input
has a non-negative attractor, and the rule simply never leaves it.**

**The ZERO arm is still travelling after 51 200 steps** — DC frac monotonically
0.021 → 0.157, frac(w<0) monotonically 0.504 → 0.436, drift ~0.26 and not
falling, anisotropy 0.158 → 0.186 (barely off the 0.1525 random floor while DC
sits at 0.28). It is being dragged toward the DC mode and has not arrived.

**Honest limit, stated rather than glossed:** neither arm reaches drift→0.
Even the DC arm's drift plateaus at ~0.12–0.16 rather than vanishing — its
*score* is a stable state (anisotropy flat at ~0.28 from 3200 to 51200) while its
*weights* keep jittering. That is the eye rung's own diagnosis recurring
(**WTA at a fixed learning rate has no fixed point**; Kohonen anneals η→0, this
rule does not). So the strict §2 reading is that **no arm here has a true fixed
point**, and the DC arm's committed numbers are read at a *score plateau*, not at
a fixed point. **I cannot show the zero-mean arms REACH the DC arm's state — only
that they move monotonically toward it and never away, at two norms, over 16× the
committed horizon.**

### 8.1 THE NORM-MATCHED ARM ARRIVES — the DC prior is a HEAD START, not a destination

**ZEROM is the arm that answers the question, and it converges on the DC arm's
state.** At 51 200 steps, starting from a *signed, DC-free, ‖w‖-matched* init:

| statistic | ZEROM @51200 | **DC @51200** | direction of travel |
|---|---|---|---|
| **anisotropy** | **0.2721** | **0.2787** | **arrived** (0.158 → 0.272, monotonic) |
| DC power frac | 0.6693 | 0.9246 | ↗ still climbing (0.021 → 0.669) |
| frac(w<0) | 0.1565 | 0.0000 | ↘ still falling (0.504 → 0.157) |
| ‖w‖ | 1.819 | 1.001 | ↘ still falling (6.97 → 1.82) |

**Every single statistic moves monotonically toward the DC arm's value, and the
headline one — anisotropy, rung 1/2/4's entire measure — has essentially
arrived** (0.2721 vs 0.2787, a 2.4% gap after starting 45% below). The zero-mean
arm is not finding a different, signed, structured solution. **It is walking to
the same place the DC init starts at**, and the only difference the init makes is
**how long the walk takes** — which is why ZERO (‖w‖=0.35, ~20× slower on `y`) is
still barely off the floor at 51 200 while ZEROM (‖w‖ matched) has covered the
distance. **The norm control did exactly the job it was declared to do.**

**This is the prediction's mechanism, confirmed dynamically rather than
asserted:** Oja's attractor on non-negative binary input is non-negative
(Perron–Frobenius on `E[xxᵀ]`), and a zero-mean init does not escape it — it is
*dragged out of* zero-mean, monotonically, at every norm, over 16× the committed
horizon. **The DC prior is real, it is 431:1, the comment describing it was
false — and it is NOT LOAD-BEARING. It is where the rule was going anyway.**

## 9. THE VERDICT ON EACH RUNG

| rung | committed | re-measured DC | zero-mean | does the committed result change? |
|---|---|---|---|---|
| **5** | OSI **0.004** (floor 0.0044) | **0.0045** @3200 ✓ | 0.3665 vs **its own floor 0.3899** | **NO.** Both inits blind. The zero-mean "lift" is its own noise floor, and training pushes it *below* that floor. |
| **6** | no development; runaway/empty | — | **not expressible** | **NO.** Dale's law is a rule; the effective RF `w⁺−w⁻` starts at the no-DC floor (0.0232 vs 1/N=0.0204). Architecturally immune. |
| **4** | interaction **−6.91** [−7.46,−6.37] | §10 below | §10 below | see §10 |
| **2** | 0.402 / 0.363 / 0.216 | §11 below | §11 below | see §11 |

**Rung 5's root-cause diagnosis SURVIVES and is now better founded than when it
was written.** It said: *"Oja on nonneg binary input yields strictly-positive
weights ⇒ DC-dominated response ⇒ the oriented structure never reaches the
RESPONSE."* The ablation shows the **"on nonneg binary input"** clause is doing
all the work and the init is doing none: `frac(w<0)=0.0000` holds for **51 200
steps** from a DC init, and a signed init is **dragged toward** it. What rung 5
attributed to the rule+input, the review attributed to the adapter; **the rule +
input is correct.**

**And rung 6 was NOT built to remove a blocker a one-line init change would have
removed.** A zero-mean init does not give the simple layer a signed *fixed
point* — only a signed *starting point* that Oja erases. Rung 6's subtraction
(`x_OFF = 1−x`, `oo_learn_sub`'s zero-sum update) changes the **input's** sign
structure, which is the only thing that changes the attractor. **That was the
right move, for the reason it was made.**

## 10. PART 4 — RUNG 4's MAP INTERACTION (`scripts/w0_part4_rung4.py`)

A **REPRODUCTION**, not a reconstruction: rung 4's own `rung4_lib` constants,
`map_stats`, `sign_flip_p`, `boot_ci`, on rung 4's own confirmatory seeds
**5000–5069**, changing exactly one thing — the `init=`.

### 10.1 The DC arm reproduces rung 4 EXACTLY — the apparatus is faithful

| statistic | committed | **re-measured (DC)** |
|---|---|---|
| `d_on` (lateral ON) | −20.16 | **−20.1576** [−20.7197, −19.5505] |
| `d_off` (ablated) | −13.25 | **−13.2452** [−13.8814, −12.6036] |
| **INTERACTION** | **−6.91**, CI [−7.46, −6.37] | **−6.9124**, CI [−7.4593, −6.3707], p<0.0001, n=70 |

Four decimal places, all three statistics, both CI bounds. **Whatever else this
document says, the worktree, the engine and the code path reproduce rung 4
byte-for-byte** — so a difference in another arm is the init and nothing else.

### 10.2 The zero-mean arm — the interaction SURVIVES but SHRINKS 4.4×

| arm | d_on | d_off | **INTERACTION** | mean selectivity (ON/OFF) |
|---|---|---|---|---|
| **DC** | −20.1576 | −13.2452 | **−6.9124** [−7.4593, −6.3707] | 0.3314 / 0.2869 |
| **ZEROM** | — | — | **−3.5909** [−4.2840, −2.9023] | 0.2139 / 0.1857 |
| **ZERO** | −2.1300 | −0.5661 *(p=0.15, null)* | **−1.5640** [−2.1959, −0.9445] | 0.1850 / 0.1656 |

Ablation contrasts: `ZERO − DC` = **+5.3485** [+4.4871, +6.2004]; `ZEROM − DC` =
**+3.3216** [+2.4689, +4.1557]. Both p<0.0001, n=70 — **the init moves rung 4's
statistic, and this is the one place in the ablation where it does.**

**The three arms order by SELECTIVITY, monotonically, and that IS the
explanation:** DC (sel 0.331) → −6.91; ZEROM (sel 0.214) → −3.59; ZERO
(sel 0.185) → −1.56. ZEROM — the norm-matched arm that PART 1B showed travels
the same road *faster* — lands exactly where that predicts: **between** the
other two. The interaction is not being created by the DC prior; it is being
*read out* through units that the DC prior has already had 3200 steps to tune.

**Rung 4's claim is NOT overturned.** The pre-registered statistic — the
mechanism **interaction** — is **negative, CI-excluding-zero and p<0.0001 under
both inits**. A map forms from waves alone, and `vm_burst_lateral` is what makes
it, either way.

**But its MAGNITUDE is init-dependent at the committed horizon, and that is a
real caveat I did not predict.** The honest reading is not "the DC prior inflates
rung 4" — it is that **at 3200 steps the zero-mean arm has barely learned
anything** (PART 1B: anisotropy 0.166 vs DC's 0.290; here: selectivity 0.185 vs
0.331), and rung 4's *own documented ambiguity* predicts the consequence:
*"lateral also raises selectivity (+0.045) and better-tuned units read out more
cleanly (within-arm r=−0.65), so a mean-level readout contribution to the
interaction is not excluded"*. Untuned units carry less orientation to be smooth
*about*. The interaction tracks how far along the learning curve the arm is —
and the DC init starts it 3200 steps ahead.

**So proviso 3 of my prediction BROKE, and this is what it taught me.** I
predicted rungs 2/4 *"cannot move by construction"* because `orientation_selectivity`
is a spectral moment blind to the DC bin. **That is true at step 0 and false
after learning.** The measure's DC-blindness does not imply arm-insensitivity,
because the init does not change the *readout* — it changes the *trajectory*, and
therefore where the arm sits on it when you measure. **A measure being blind to a
parameter does not make the RESULT blind to it.** That is the general lesson and
it applies to every "the statistic ignores X, so X can't matter" argument in this
arc, including one I made in §3 of this very document.

## 11. PART 5 — RUNG 2's THREE ARMS (`scripts/w0_part5_rung2.py`) — a RECONSTRUCTION

**Rung 2 attempt 10 has no committed runner.** This rebuilds its design from the
pre-registration's prose (phase 1 = 1600 steps waves; phase 2 = 400 steps, `dark`
= waves continue, `normal` = video/waves cease, `sutured` = noise/waves cease;
statistic = mean anisotropy over 10 units; seed = unit of analysis), on attempt
10's own seeds **1900–1999**. **Its numbers are RECONSTRUCTIONS, not
reproductions** (§ this document's own rule), and the DC arm is the fidelity check.

### 11.1 The fidelity check SPLITS — and it splits exactly where it should

| arm | committed (attempt 10) | **reconstruction (DC)** | verdict |
|---|---|---|---|
| `dark` (waves continue) | **0.363** | **0.363** | **EXACT** |
| `sutured` (noise) | **0.216** | **0.217** | **EXACT** |
| `normal` (video) | **0.402** | **0.288** | **DOES NOT REPRODUCE** |
| `d_sutured` | **−0.1474** [−0.1546, −0.1400] | **−0.1458** [−0.1523, −0.1394] | **EXACT** |
| `d_normal` | **+0.0385** [+0.0320, +0.0451] | **−0.0752** [−0.0822, −0.0679] | **INVERTED** |

**The two arms that need no video reproduce to three decimals; the one arm that
needs video does not — and it is the only thing I had to substitute.** That is
the cleanest possible outcome for a reconstruction: it validates the harness and
localises the discrepancy to the known substitution.

### 11.2 Why I do NOT claim rung 2's H1a fails — the confound is mine

> **RETRACTED 2026-07-17, same day, by the supervisor. The claim below —
> "`normal`'s video source is gone" — is FALSE.** The Jellyfin catalogue DOES
> contain Sesame Street (Series `a6152b4a3b12f70779d1cb6364fa97e6`, **78
> episodes**); frames decode today with **adjacent-frame correlation 0.9904**.
> **The 137-item count was RIGHT** (46 Series + 91 Movie) — the right catalogue
> was enumerated and then read with the **wrong key**: `catalog()` returns dicts
> keyed lowercase `name`, and the absence check read `Name`, so `.get('Name','')`
> returned `''` for all 137 items and reported a stocked library as empty. **A
> soft accessor cannot raise, so the false negative was silent.** Two readers hit
> it independently. **The substitution below was therefore unnecessary, and the
> confound it introduced was self-inflicted.** See PROTOCOL §12. The original
> text is kept verbatim below.
>
> **UPDATE (the rung-2 RE-RUN, same day): the surviving hazard is CLOSED, and
> this section's JUDGEMENT is UPHELD.** *"Rung 2 still has no committed runner"*
> is now superseded: `scripts/rung2_rerun.py` is the runner and
> `tests/fixtures/vision_rung2/sesame_16x16.npz` the pinned, hashed stimulus.
> **This section's refusal to score 0.288 as a refutation of H1a was CORRECT and
> stands.** But its diagnosis was incomplete: on the REAL source `normal` reaches
> only **0.317** — still far below `dark` (0.363), d **−0.0463**, p<0.0001,
> replicated on fresh seeds. **Temporal decorrelation was worth ~+0.03 and was
> never what separated 0.402 from 0.363** — restoring the corpus did NOT restore
> the result. The larger cause is the stimulus **construction** (whole-frame
> downsample anisotropy **0.2136** vs native-res crops **0.5769** — 2.7× on the
> quantity Oja converges to). See `VISION_RUNG2_PREREG.md`'s RE-RUN section and
> `VISION_PROTOCOL.md`.

**`normal`'s video source is gone.** Attempt 10 used Sesame Street over
Jellyfin; the catalogue on this machine (137 items, queried 2026-07-17) no longer
contains it and no frames are cached. I substituted **BSDS300 natural-image
crops**.

**And they are NOT the same stimulus in a way that matters here.**
`bsds_crops` draws each frame as an **independent random crop from a randomly
chosen photograph** — so my `normal` arm is spatially natural but **temporally
DECORRELATED**, while video is natural in space *and* correlated in time.
`wv_unit_activate` integrates pre-bursts over `window_steps`; the entire rung is
about spatioTEMPORAL structure. **A temporally-shuffled natural-image stream is
much closer to the `sutured` arm than to video**, and my `normal` lands exactly
where that predicts: **between** video (0.402) and noise (0.217), at **0.288**.

**So this is NOT evidence against rung 2.** It is a **reconstruction confound I
introduced**, of precisely the kind §6 warns about (*"controls must correspond to
the actual experiment"*), and I am naming it rather than reporting `d_normal` as
a refutation. What I can say honestly:

- **`d_sutured` (H1b — "unstructured drive actively dissolves structure") is
  REPRODUCED** (−0.1458 vs −0.1474): source-independent, because noise is noise.
- **`d_normal` (H1a — "vision refines") is NOT REPRODUCIBLE ON THIS MACHINE**,
  and my substitute cannot test it. **This is a real reproducibility hazard for
  the supervisor, independent of the `w0` question:** rung 2's headline "BUILT"
  verdict is conjunctive, so it rests on an arm whose input no longer exists and
  whose runner was never committed. Attempt 10's own pre-registration flagged
  H1a as *"genuinely uncertain — it requires natural video's leading principal
  component to be MORE anisotropic than the waves'"*. That question is now
  **unanswerable as committed**. Re-establishing it needs a cached, committed
  stimulus, and that is a supervisor decision, not mine to make in this worktree.

### 11.3 The `w0` ablation on rung 2 — the same story as rung 4

| arm | DC | ZEROM | ZERO | random floor |
|---|---|---|---|---|
| `dark` | **0.363** | 0.198 | 0.172 | **0.1525** |
| `normal` | 0.288 | 0.176 | 0.156 | 0.1525 |
| `sutured` | 0.217 | 0.155 | 0.151 | 0.1525 |
| `d_sutured` | **−0.1458** | −0.0426 | −0.0214 | — |

Ablation contrasts, all p<0.0001, n=100: `dark ZERO−DC` = **−0.1908**
[−0.1979, −0.1836]; `dark ZEROM−DC` = **−0.1654**; `sutured ZERO−DC` = −0.0664.

**Under a zero-mean init at the committed 2000-step horizon, ALL THREE arms
collapse to the random floor** (0.151–0.198 vs a floor of 0.1525) and every
effect shrinks with them (`d_sutured` −0.146 → −0.021). **This is not the DC
prior manufacturing rung 2's result. It is the zero-mean arms not having learned
anything yet** — the identical transient PART 1B measured directly (ZERO's
anisotropy at 3200 steps: 0.166, against DC's 0.290), and ZEROM again sits
**between** DC and ZERO on every single arm, exactly as its faster transit
predicts.

**Two things survive the init, and they are the ones that matter:**

1. **The ARM ORDERING is preserved in all three arms:** `dark > normal >
   sutured` under DC (0.363/0.288/0.217), ZEROM (0.198/0.176/0.155) and ZERO
   (0.172/0.156/0.151).
2. **H1b's SIGN and significance survive** (`d_sutured` < 0, p<0.0001, CI
   excluding zero, under all three inits) — *unstructured drive dissolves
   structure* is init-independent.

## 12. THE ANSWER TO THE QUESTION ASKED

**Do the reviewer's numbers reproduce?** **YES.** DC power fraction **0.99758**
(claimed 0.99798), ratio **431:1** (claimed 494:1), `frac(w<0)` **0.0000**
(claimed 0.0000), zero-mean **0.02173** (claimed 0.01366, and 1/N = 0.02041 is
the floor both are near). **The charge is upheld and the comment is retracted as
false.**

**Does any committed result change?**

| rung | verdict |
|---|---|
| **5** | **NO.** OSI 0.0045 reproduces 0.004; the zero-mean "lift" to 0.3665 is **below its own untrained floor of 0.3899**. Both inits blind. **Rung 5's root-cause diagnosis is CONFIRMED and strengthened** — the non-negativity comes from the INPUT meeting Oja's second-moment attractor (`frac(w<0)=0.0000` for 51 200 steps; a signed init is dragged *out of* zero-mean), not from the adapter. |
| **6** | **NO.** Architecturally immune: Dale's law is a rule, and the effective RF `w⁺−w⁻` already starts at the no-DC floor (0.0232 vs 1/N=0.0204). **Rung 6 was not built to remove a blocker a one-line init change would have removed** — a zero-mean init gives a signed *start*, not a signed *fixed point*; only rung 6's subtraction changes the attractor. |
| **4** | **The CLAIM: no. The MAGNITUDE: yes.** The interaction is negative, CI-excluding-zero, p<0.0001 under **all three** inits (−6.91 / −3.59 / −1.56), and the DC arm reproduces the committed −6.9124 [−7.4593, −6.3707] to four decimals. But magnitude orders **monotonically by unit selectivity** (0.331/0.214/0.185) — rung 4's own documented readout ambiguity. |
| **2** | **H1b: no** (sign + significance survive every init; DC reproduces −0.1458 vs −0.1474). **H1a: UNANSWERABLE HERE, and not because of `w0`** — its video source no longer exists on this machine and its runner was never committed. |

**THE HEADLINE: the DC prior is REAL (431:1), the comment describing it was
FALSE, and it is NOT LOAD-BEARING.** It is a **head start**, not a destination:
Oja's attractor on non-negative binary input is non-negative by Perron–Frobenius,
the DC init simply begins there, and a zero-mean init walks to the same place —
demonstrated by the norm-matched arm arriving at DC's anisotropy (0.2721 vs
0.2787) over 16× the committed horizon, with every other statistic still
monotonically en route. **"Our Units are blind" is NOT an adapter artifact.**

**What I do NOT claim:**
- **Not** that any arm reaches a true §2 fixed point. Even the DC arm's drift
  plateaus at ~0.12–0.16 rather than →0 (WTA at fixed η has no fixed point — the
  eye rung's diagnosis, recurring). The committed numbers are read at a **score
  plateau**, not a fixed point.
- **Not** that the zero-mean arms *reach* the DC state — only that they move
  monotonically toward it and never away, at two norms, over 51 200 steps.
- **Not** anything about rung 2's H1a. My substitute stimulus is temporally
  decorrelated where video is not; that confound is mine and it is disqualifying
  for that arm.
- **Not** that the init is harmless. It costs ~3200+ steps of learning, it made
  rung 4's magnitude horizon-dependent, and **the comment on it was wrong for
  two years of this arc.** "Not load-bearing" is a measured verdict about the
  *fixed point*, not a defence of the line.

## 13. POSTSCRIPT — RUNG 7 LANDED CONCURRENTLY AND CONFIRMS PROVISO 4

*Merged into this worktree after the ablation's numbers were committed
(`f7858f0486`; §11.5 — another agent may commit under you, so this is recorded
with its own provenance rather than folded in silently).*

**Proviso 4 of my prediction (§3), written before any arm ran:**

> *"The prediction is only about THIS input. On a zero-mean input (an OFF
> pathway, rung 6's subtraction) the argument collapses — `E[xxᵀ]` is no longer
> non-negative and Oja can find a signed component. That is precisely rung 6's
> design and precisely why rung 6 is the right next rung."*

**Rung 7 did exactly that, independently, and it works.** A horizontal cell pools
rung 1's `neighbour` edges; the bipolar transmits the **residual**
`c − g1·h1 − g2·h2` — **a signed quantity** — and ON/OFF are its two rectified
halves, which thereby acquire *genuinely different spatial dependence*
(`σ_ON,ON = 1.627` vs `σ_ON,OFF = 3.264`, ratio 2.007, p=1.2e-08). The
degeneracy that blocked rung 6 breaks (SD 0.3601, 76.3% of range, against a
4.441e-16 floor), and **centre-surround EMERGES from a `lat_g0 = 0.0` ZERO
INIT** — the same zero init that is inert in the unsigned layer.

**Rung 7 also reports itself `w0`-init-free** (byte-identical, 0.000e+00 on every
rung-7 number: it mints no `Unit` and its learned parameter starts at exactly
0.0) — arrived at independently, from the other direction.

**The two lines agree, and the agreement is the point:**

| change | effect on the attractor |
|---|---|
| the INIT (this ablation: 431:1 DC prior → zero-mean, norm-matched, 51 200 steps) | **nothing** — the arm walks back to the same place |
| the INPUT's sign structure (rung 7: a signed bipolar residual) | **everything** — the degeneracy breaks and structure emerges from a zero init |

**That is the whole finding of this document, stated by two independent rungs
from opposite directions.** The reviewer was right that the DC prior is real,
undocumented and mis-commented; the arc was right that it is not what makes the
Units blind. **What makes them blind is the input, and rung 7 is what fixes it.**
