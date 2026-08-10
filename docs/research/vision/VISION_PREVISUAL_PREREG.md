# THE PRE-VISUAL PHASE — pre-registration

**Engine:** `95167c01b7b3 @ …/agent-a00f8c2f0650cd637/…/runners/dsl/python/substrate_rs/_native.abi3.so`
(§10 — a PRIVATE worktree copy of the canonical release build, hash-identical;
see `W0_ABLATION.md` for the §10/§11 contradiction this exposes).
**Commit:** worktree branch off `gamma-substrate/developmental-vision` @ `692b36d51b`.
**Selector (§12):** explicit file lists only. No `-k vision` anywhere.
**Seeds:** block **12000–12999** requested and appended to the ledger.

*Written and committed BEFORE any confirmatory run (§3). Every number in the
GATE section below was measured on already-burned seeds (0–2) before this file
was written.*

---

## 1. The claim this is meant to test

The creator's constraint, from `VISION_EYE_PREREG.md`:

> *Waves cannot calibrate photometric response before phototransduction works;
> they establish topology, correlation, timing, pathway relationships. Later
> visual input calibrates gains and environmental statistics.*

And the eye agent's Amendment 1 correction: **eyelids are translucent.** A closed
lid passes diffuse, scattered light, so phototransduction *does* work behind it —
on light with no fine spatial structure. That yields a genuine **pre-visual phase
with two jobs running in parallel**: waves → **relational** structure; diffuse
light → **photometric** gains. The lid then opens and structure arrives as a
perturbation of an already-grounded, already-calibrated system.

The eye agent measured, at **calibration grade on burned seeds** and explicitly
*not* retrofitted: θ calibrates behind a closed lid, never having seen a sharp
image, then reads one **invariantly** (patdiff 0.005982 vs a floor of 0.582486 =
**1.1% of floor**), with detail arriving as a **structured residual** (sd 0.195).
It named this as the design for the next pre-registration. **This is that
pre-registration.**

## 2. The hypotheses, as proposed

- **H1** — a system that calibrated behind a closed lid reads a *sharp* image
  invariantly on eye-opening, where an **uncalibrated** system does not.
- **H2** — the sharp image arrives as a **structured residual**: eye-opening's
  information is in what the calibrated prediction fails to explain (sd 0.195),
  quantified against a floor.
- **H3 (THE DISCRIMINATING ONE)** — a **double dissociation**:
  **(a)** waves move the photometric gain by ~0, diffuse light moves it;
  **(b)** waves move the relational measures, diffuse light does not.
  *That double dissociation IS the creator's two-phase claim, and it is what
  makes the other two non-vacuous.*

## 3. THE GATE, RUN FIRST — can H3 fail? (`scripts/previsual_vacuity_audit.py`)

**PROTOCOL §1 says gate the measure before the agent. The instruction here was
sharper: `check your test can fail before you run it`, and `if everything is
structural, the test is vacuous — report that instead of a pass`.** The eye's
Amendment 1 already concedes that H3(a)'s first half is **structural** — the
photometric rules read `EyeCell.lum`, waves live on `RetinaCell.bursting`, no
edge joins them, waves move θ by exactly 0.0. So the only live question is
whether the **other** half is structural too.

### 3.1 The positive control caught a DEAD INSTRUMENT first

My first run of this audit scored **0.000000 in all four cells** — a flawless
"double dissociation". It was a dead instrument: **`eye=0.0` is `EyeParams`'
master default-off** (§9) and `phase0=0.0` gates the relational rules; I had set
neither. **Nothing had run at all.** That is the fourth inert-arm catch in this
arc (the eye's own θ-OUTSIDE arm; the phase-0 clock bug; the per-cell reference)
and it is the reason a positive control is non-negotiable: *an all-zero table is
what a perfect dissociation and a corpse both look like.* The audit now asserts
`diffuse light → |Δθ| > 0` before reading anything else: **0.463261, ALIVE.**

### 3.2 STATIC — no rule couples the two paths

`seeds/vision_eye.json`, classifying each rule by which attributes it reads:

| | count |
|---|---|
| photometric-only rules (read `lum`/`resp`/`theta`/`xbar`) | 8 |
| relational-only rules (read `bursting`) | 2 |
| **COUPLING rules (read BOTH)** | **0** |

Two disjoint populations — `EyeCell`→`EySynapse`→`EyeUnit` (light) and
`RetinaCell`→`WSynapse`→`WUnit` (waves). The only edge between them is
`has_wclock` (Retina→Eye), which carries **timing, not signal**.

### 3.3 DYNAMIC — all four cells, measured (n=3 burned seeds 0–2, 400 steps)

| arm | \|Δθ\| (photometric) | \|Δw\| (relational) |
|---|---|---|
| waves only | **0.028280** | **1.721994** |
| diffuse light only | **0.463261** | **0.000000** |
| both | **0.463261** | **1.721994** |
| neither (null control) | **0.028280** | 0.000000 |

**Read the null column.** `waves only` moves θ by 0.028280 — **exactly** what
`neither` moves it by. Waves' effect on the gain is `0.028280 − 0.028280` =
**exactly 0.0** (the 0.028 is θ adapting to darkness, and the null control is the
only reason that is visible rather than being read as a small wave effect).
Symmetrically, `diffuse light only` moves the relational weights by **exactly**
what `neither` does: 0.000000. And `both` equals each single arm **to six
decimals, with zero interaction**.

**That perfection is the tell.** Measured effects do not cancel to six decimals.
This is not a dissociation; it is the architecture restating itself.

### 3.4 GATE VERDICT: **H3 IS VACUOUS — BOTH HALVES. IT CANNOT FAIL.**

Not one half structural and one measured: **both**. No rule reads both attribute
sets; no edge joins the populations; the measured table is exactly what "no
edge" predicts, in all four cells. Running H3 would produce a flawless double
dissociation that is a **tautology**, and reporting it as confirmation of the
creator's two-phase claim would be the purest false positive in this arc — worse
than the ones already retracted, because it would be *unfalsifiable by
construction*.

**The two-phase split is not a finding of this model. It is an ASSUMPTION WIRED
INTO IT.** The creator's claim may well be true of biology; this architecture
cannot bear witness either way, because it was built with the answer already in
its node types.

## 4. THE SECOND, INDEPENDENT STOP: §2 CONVERGENCE

Even were H3 non-vacuous, its relational half is unmeasurable here.
`VISION_EYE_PREREG.md` §1.3 measured phase 0's retinotopic refinement out to
32 000 steps: **drift ~0.24 throughout, never decreasing**, spread pinned at the
diffuse floor. Under §2 that is *"never converges ⇒ the scaffold is a TRANSIENT
and every arm is measured at an arbitrary point on a decay curve"*, with a named
mechanism (WTA at fixed η has no fixed point; Kohonen anneals η→0, this rule does
not). **The relational measures H3(b) needs are transient-measured, so no arm
comparison over them is meaningful** — which is exactly why the eye agent ran no
phase-0 confirmatory arms and burned no seed.

## 5. H1 and H2 without H3

With H3 dead, do H1/H2 still earn fresh seeds? **No, and the reason is the
instruction's own warning.**

- **H1 is near-vacuous by arithmetic.** *"Global illumination invariance is
  vacuous by arithmetic in both frames — a scalar cancels; the non-vacuous form
  needs a spatial gradient + surround."* H1 scales illumination by a **global
  scalar** k. In log space that is an additive ln(k) which a subtractive
  reference cancels **identically**. Its only discriminating content is
  log-vs-linear — and the eye's §1.1 convergence measurement **already
  established that**, more cleanly and at no seed cost (LINEAR at k=1000: drift
  0.239, never converges; LOG converges at every illumination). A confirmatory
  run would re-derive a known arithmetic identity on fresh seeds.
- **H2 is descriptive, not a test.** "The residual is structured (sd 0.195)" has
  no pre-registered floor that could fail: any receptor that does not saturate
  leaves a non-zero residual on a sharp image. The eye's own §3.3 shows the
  *interesting* failure mode (a per-cell reference on a static scene erases the
  image, sd→0), and the lid fix already dissolved it. What remains is a
  measurement of "the blur is not the image", which is true of the blur operator,
  not of the agent.
- **The non-vacuous form is named, not run:** a **spatial gradient + surround** —
  invariance that a scalar cannot deliver, requiring lateral structure the eye
  does not have. That is a mechanism and needs its own pre-registration.

## 6. DECISION — declared in advance, and executed

**NO CONFIRMATORY RUN. NO SEED BURNED.** The gate in §3 fails on the
discriminating hypothesis, before any confirmatory arm, on two independent
grounds (vacuity; §2 non-convergence), and the two survivors do not test the
claim the rung exists to test.

This is the arc's own precedent and it is the right outcome, not a shortfall:
rung 5 stopped at its precondition, rung 6 at its convergence gate, phase 0 at
its convergence gate, and the calibration reframe at its measure-calibration
gate — **each burning zero confirmatory seeds**. Seeds **12000–12999** are
recorded on the ledger as **ALLOCATED, UNUSED and CLEAN**.

**A negative with a measured cause is the deliverable.**

## 7. MY PREDICTION, AND WHAT BREAKING IT TAUGHT ME (§3.7)

Stated before the audit ran: *"H3(a)'s first half is structural (the eye already
says so); H3(b) is measured; so the test is half-real and worth running."*

**The proviso that broke: I assumed 'diffuse light reaches the relational path'.**
It does not — and it *cannot*, because `PreVisualWorld` wires `WSynapse.pre` to
`RetinaCell`, whose `bursting` is set only by the wave state machine. Light is
written to `EyeCell.lum`, a different population entirely. I had read the eye's
"no edge joins them" as a statement about *one* direction; it is a statement
about the **partition**, and a partition has no directions.

**What I did not understand, and it generalises past this rung:** `wave_world`
already implements the biologically correct convergence — **"TWO PATHWAYS, ONE
OUTPUT"**, where `bursting = (state=="active") OR (driven==1.0)`, so waves and
light both drive the RGC and only waves propagate. The **eye's phase 0 does not
use it.** A pre-visual model that wired the lid's diffuse light into the
`driven` channel would make H3(b) genuinely measurable — light *could* move the
relational measures, and the question of whether it *does* would have an
empirical answer. **That is the design for a real version of this rung**, and it
is named here rather than retrofitted (§5). It is still blocked by §4 until the
retinotopy rule has a fixed point.

## 8. What is NOT claimed (§8)

- **Not claimed:** that waves and diffuse light dissociate in this model *as a
  finding*. They dissociate **by construction**, and that is all the audit shows.
- **Not claimed:** anything about biology's two-phase organisation. This
  architecture assumes it; it cannot test it.
- **Not claimed:** that the eye agent's 1.1%-of-floor and sd-0.195 numbers are
  wrong. They reproduce as calibration-grade facts about a log receptor with a
  subtractive reference; what is denied is that they *test the two-phase claim*.
- **Not retracted:** `VISION_EYE_PREREG.md`'s phase-1 confirmatory result. This
  document concerns the pre-visual (phase-0/lid) claim only.
