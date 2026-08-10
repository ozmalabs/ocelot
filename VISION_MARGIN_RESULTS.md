# RUNG L1c — THE MARGIN INSTRUMENT: A DERIVED NEGATIVE, A BOUND THAT DOES FALL OUT, AND THE T1 RECORD CORRECTION — RESULTS

*Confirmatory run of `VISION_MARGIN_PREREG.md`, authored and **committed BEFORE the run**
at **`ebb3daec`** (§3). Runner `scripts/margin_measure.py`; seed `seeds/vision_margin.json`
(builder `tools/build_vision_margin.py`); adapter `domains/margin_world.py`; gate
`tests/test_margin_migrated.py`; pinned raw `results/margin_measure.json`. Seeds
**51000–51099** (FLOOR), **51100–51199** (DISAGREE); **51200–51999 remain CLEAN**. Base
`main` HEAD **07eeda24** (`git merge-base --is-ancestor 07eeda24 HEAD` verified, §11).
Branch `gamma-substrate/vision-margin-l1c`, worktree
`.claude/worktrees/agent-a0b4897bb592231f0`.*

## Engine / bench / provenance (§10)

- **Engine `7d5f50c18673`** @ `runners/dsl/python/substrate_rs/_native.abi3.so` — **shared
  build, Rust source byte-identical** to canonical. This rung adds **NO Rust**, so the
  shared build is a legitimate build of this tree's source (§10.1 rule 4), gated by
  `test_this_rung_adds_NO_Rust` **pinned to `07eeda24..HEAD`, tracked files only** (never
  base→working-tree, never a repo-wide untracked scan).
- `data/` symlinked to canonical (§10.2). **Baseline measured on this worktree BEFORE any
  file was added: 200 passed / 0 failed.**
- **NO new Rust, NO new constant, ONE new seed** (`vision_margin`, NOT boot-loaded; ships
  `MarginParams{margin:0.0}` **OFF by default**). **NO committed seed file is edited** —
  the only touched committed file is the one-entry registration in
  `domains/seed_registry.py`.

---

# PART A — THE DERIVATION

**VERDICT: NO MARGIN BOUND EXISTS. All six margin candidates are REJECTED BY
MEASUREMENT. But a BOUND does fall out — it is simply not a margin — and inside it
L1b's existing count predicate transfers to T1 unchanged.**

This is a **first-class derived negative (§7)**, predicted in advance, and the prediction
held in both halves: the margin's own shape fails, and a different shape succeeds.

## The six rivals, each killed by a measurement

| # | rival margin bound | measurement | verdict |
|---|---|---|---|
| **M1** | `√2/2` used as a **MARGIN** | rows with `d₂−d₁ ≥ √2/2`: **0/63 at s=1, 0/63 at s=2, 0/63 at s=4** | **REJECT — refuse-everything at every resolution** |
| **M2** | any **ABSOLUTE** margin | median margin **0.0906 → 0.1065 → 0.1873** as s goes 1→2→4: the margin **SCALES with resolution** while an absolute constant does not | **REJECT — a view from nowhere (§13); no single value transfers** |
| **M3** | the **exact-tie** margin | exact ties: **0/63 at every resolution** | **REJECT — vacuous** |
| **M4** | the **observational-resolution step** (the residual's own angle-grid jitter) | median **1.06e-4 / 2.68e-4 / 1.04e-3**, max **9.2e-3** — **two to three orders of magnitude BELOW the margins it would have to separate** | **REJECT — defined, but refuses nothing** |
| **M5** | the codebook's **PACKING RADIUS** `r_c = ½·min_{c'≠c} D(c,c')` — **the colour rung's own winning derivation, transplanted** | certifies **19/63 at s=1 — of which 3 are WRONG** — and only **3/63** (s=2) and **4/63** (s=4) | **REJECT TWICE — UNSOUND at the aliasing floor, NEAR-VACUOUS above it** |
| **M6** | a scale-free **RATIO** `d₁/d₂` | max ratio **0.9975** (s=1) vs **0.801** (s=4) — separating *in principle* | **REJECT — any threshold between them is chosen after seeing both: a magic number by construction (§13/§5)** |

**M5's rejection is the load-bearing one**, because it is the rival that *worked* for
colour. It fails here for a measured structural reason: **T1's lattice-rounding residual
(median winner 0.3838 at s=4) EXCEEDS its codebook's packing radius (0.248–0.284).** The
observations do not lie inside their own quantum's cell. **A packing-derived certificate
cannot be non-vacuous in a codebook whose observation noise exceeds its packing radius** —
a fact about T1's codebook, measured, not argued. (The triangle-inequality route I
expected to kill M5 did *not* materialise: **0 violations** among all codebook triples at
every resolution. M5 dies on vacuity and unsoundness instead, which is a different and
better-evidenced death than the one I anticipated.)

## WHAT DOES FALL OUT — `η`, the SELF-ROUNDING RESIDUAL

`√2/2` is the **worst-case per-point** rounding displacement — a loose absolute over-bound
imported from the lattice's geometry. The quantity the system actually has is the MHD the
rounding **actually induces on its own codebook**:

> **`η_c := max_{t ∈ cp_angles} resid( c , round(rotate(c, t)) )`**

computed from **codebook × lattice × the agent's OWN held angle grid** and nothing else —
never from the test observations, never from which answer is right. **No new constant**
(the probe grid *is* `cp_angles`, which T1 already holds). It is **derived by the
`mg_eta` SEED RULE in the graph**, not by the adapter — gated by
`test_eta_is_DERIVED_BY_THE_GRAPH_and_matches_the_committed_values`, which reads the value
back off the graph.

**Measured `η` at s=4:** `F 0.5330 · T 0.6180 · U 0.5573 · V 0.4464 · L 0.4286 · N 0.4376
· X 0.7071` — **per-shape and resolution-adapted**, where `√2/2` is one absolute number for
everything. `η_c ≤ √2/2` for **every** shape at **every** resolution (verified), so the
admission set can only ever **SHRINK**: this instrument **cannot widen any invariance
class** (§8).

## THE BOUND NOW BINDS — the whole point of the rung

| resolution | candidates inside **T1's `√2/2`** (min/med/max) | candidates inside the **derived `η`** |
|---|---|---|
| s=1 | **7 / 7 / 7** | **1 / 3 / 7** |
| s=2 | **5 / 7 / 7** | **1 / 2 / 5** |
| **s=4 (T1's headline)** | **2 / 4 / 7** | **1 / 1 / 4** |

**The median row goes from FOUR candidates to ONE.** L1b's premise — *"the
candidate-COUNT predicate only works where the bound actually BINDS"* — is satisfied by
replacing the bound, not by inventing a margin.

**Honest note on `η`'s own limit, predicted in proviso 2 and confirmed: `η_X = 0.7071 =
√2/2` EXACTLY.** X saturates the worst case at s≥2. Had every shape saturated, `η` would
have collapsed to `√2/2` and the derivation would have been empty. That six of seven do
not is the entire substance of this result — and X is the live warning of how close it
came to nothing. X's saturation is also the direct cause of the broken C3 prediction below.

---

# PART B — THE T1 RECORD CORRECTION

**T1's landed numbers STAND as measured and are NOT re-litigated: 63/63 invariance at
s=4, exact-0 discrimination, 0/100 noise. What was WRONG is the MECHANISM ATTRIBUTION.**

| question | measurement | corrected statement |
|---|---|---|
| Is T1's `√2/2` bound what discriminates? | **0 of 63** headline rows are bound-determined (a unique candidate inside `√2/2`) — at s=1 **and** at s=4 | **NO. T1's recognition is RANKING-BASED.** The bound admits 2–7 candidates in every single row; the `Argmin` does 100% of the discriminating work |
| Does a derived bound make it load-bearing? | under `η`: **38/63 bound-determined, 25/63 ranking-only** at s=4 (**4/59** at s=1) | **PARTIALLY — and this is the corrected record.** With a bound that falls out, a **majority** of T1's headline becomes bound-supported; a quarter remains ranking-only |

**THE CORRECTED ATTRIBUTION, stated plainly:**

> **T1 continuous pose, as landed, is a RANKING result, not a bound result.** Its `√2/2`
> threshold is a *sanity floor*, not a discriminator: it determines the identity in **zero**
> of its 63 headline trials. The 63/63 is produced entirely by the `Argmin` over the
> codebook. With the derived `η` bound substituted, **38/63 become genuinely
> bound-determined and 25/63 remain ranking-only** — so even the best available bound does
> not make T1 a bound-based recognizer. **Any future claim that T1 "recognizes within a
> bound" is wrong; it RANKS within a bound that admits almost everything.**

This is §13.2's *"works" vs "is load-bearing"* applied to a threshold, and it is now
measured on both sides rather than only diagnosed.

---

# PART C — THE INSTRUMENT

| arm | statistic | result | vs prereg |
|---|---|---|---|
| **A DERIVATION** *(RISKED)* | M1–M6 | every rival rejected, exactly as tabulated | ✓ as predicted |
| **A7 THE BOUND BINDS** *(RISKED)* | candidates within `η` at s=4 | **1 / 1 / 4** (vs **2 / 4 / 7**) | predicted 1/1/4 ✓ |
| **B1 T1 IS RANKING-BASED** *(RISKED)* | rows bound-determined under `√2/2` | **0/63** at s=1 and s=4 | predicted 0/63 ✓ |
| **B2 ATTRIBUTION CORRECTED** *(RISKED)* | under `η` at s=4 | **38 bound-determined / 25 ranking-only / 0 none** | predicted 38/25 ✓ |
| **C1 AMBIGUOUS-CASE REFUSAL** *(RISKED)* | s=1 rows **admitted AND WRONG** | **0** — all 22 of T1's confident wrong identities land in the ambiguous set (59 ambiguous, 4 admitted) | 0 ✓ |
| **C2 NO REGRESSION (CONJUNCTION)** *(RISKED)* | s=4 admitted; identity vs T1's own | **38 admitted, 38/38 byte-identical to T1's `covered_by`, 0 mismatches** | 38 ✓ |
| **C3 DISCRIMINATION / RECALL** *(RISKED)* | untransformed objects admitted | **exact-0 HOLDS (0 wrong admitted anywhere); but 2/7 untransformed admitted** | **PREDICTION BROKE — see below** |
| **C4 FLOOR** *(ENTAILED — reported, NOT banked)* | noise admitted, seeds 51000–51099 | **0/100** | ✓ (entailed: `η ≤ √2/2` ⇒ admission ⊆ T1's) |
| **C5 DISAGREEMENT** *(RISKED)* | seeds 51100–51199 | **DEAD ARM — 0 disagreements out of 0 opportunities** | **THE ARM FAILED — see below** |
| **X OFF-DAY** *(§9; ENTAILED)* | flag at default 0 | no `mg_*` attribute anywhere, **no `η` derived at all**, T1 unmoved (`recognized_continuous`/`F`) | ✓ |

## THE PREDICTION THAT BROKE — C3, and it is a REAL COST

**Pre-registered: "untransformed 7/7 admitted." Measured: 2/7.**

An **exact** match — an untransformed object, residual **0** — is still refused as
ambiguous in **5 of 7** cases, because a **rival** shape also falls within *its own* `η`.
X, whose `η` saturates at `√2/2`, is the principal offender. **The instrument buys honesty
with RECALL, and the exchange rate is worse than I predicted** — it refuses even
zero-residual exact matches when a loose-η rival is in contention.

**Pinned in the gate at the measured `2`, never at the convenient `7`**
(`test_C3_DISCRIMINATION_exact_0_HOLDS_but_MY_RECALL_PREDICTION_BROKE`), rather than
smoothed over (§3.7/§5). This is the same exchange L1b measured and the reason this
instrument, like L1b's, **ships OFF**. The *discrimination* half of C3 — no admitted row
is ever wrong — held everywhere.

## THE ARM THAT DIED — C5, §1.1 applied to myself

**C5 reports 0 disagreements. It also had 0 OPPORTUNITIES.** All 100 fresh random 5-cell
shapes are **refused by T1** (`status != recognized_continuous`), so the instrument's
rules — which fire only where T1 already claimed — **never fired on a single one**. Every
row returned an empty `mg_status`: the histogram is literally `{"": 100}`.

**A dead arm scores a perfect floor, and this one did.** Prereg proviso 1 anticipated a
*lopsided* split; the reality is worse — the arm is **INERT**, and had I not enumerated the
status histogram it would have passed as a clean 0/100 result. It is recorded as **this
rung's own instrument failure** and **supports no claim**
(`test_C5_IS_A_DEAD_ARM_and_is_recorded_as_such_NOT_banked_as_a_floor`).

**What replaces it, stated plainly because it was added AFTER seeing C5 come out dead:**
`test_the_graph_count_matches_an_INDEPENDENT_recount_on_LIVE_rows` re-derives the count
independently on 21 rows where the instrument **does** fire, and requires
`mg_status != ""` so it cannot itself die silently. It consumes **no seed** (T1's own
deterministic stimuli). The disagreement claim rests on that test, not on C5.

**The design error, for the next rung:** a disagreement arm must be drawn from the
regime where the instrument is LIVE. Because this instrument fires only downstream of a
T1 claim, random noise — which T1 refuses by construction — could never have exercised it.
**I chose the floor's stimulus distribution for a non-floor arm.** That is §6 (controls
must correspond to the actual experiment) in a new costume.

---

# THE POSITIVE CONTROLS (§12.3 / process rules 4, 5, 6) — measured, not asserted

**Process rule 4 — the `Times` trap — is discharged BY CONSTRUCTION and ASSERTED.** This
composition contains **zero `Times` nodes** (`Count`/`Filter`/`Lte`/`MaxOver`/`MinOver`/
`PointSetDist`/`Rotate`/`MapList`), gated by
`test_this_rung_uses_NO_Times_so_the_empty_product_trap_cannot_apply`, so the a/b
empty-product trap cannot silently apply. **The composition was FIXED at pre-registration
and did not change**, so no arm needed its reddening re-derived.

Three defects were injected into the **real** builder; each regenerates the seed, re-runs
the **real** runner, runs the **real** gate, then reverts. **After revert the seed is
verified BYTE-EQUAL by sha256 and the gate is 21/21.**

**Baseline 21/21. After revert 21/21, seed byte-equal by sha256 — verified.**

| injected defect | RED | what it proves |
|---|---|---|
| **REFUSE-EVERYTHING** (`mg_admit` never fires; `Gte(k,1)` ambiguous) | **3** — **`test_C2_NO_REGRESSION_the_conjunction`**, `test_C3_…RECALL_PREDICTION_BROKE`, `test_this_rung_adds_NO_new_constant` | **process rule 5, THE CRUX, confirmed live: `test_C4_the_noise_FLOOR…` and `test_C1_no_admitted_row_is_EVER_WRONG…` BOTH STAY GREEN.** A build that refuses everything scores a **perfect floor** and a perfect no-wrong-admissions record. **Floors are not a gate; only the CONJUNCTION caught it.** |
| **ADMIT-EVERYTHING** (`Gte(k,1)` admits; ambiguity never fires) | **4** — **`test_C1_no_admitted_row_is_EVER_WRONG…`**, C2, C3, the constant audit | the mirror direction: **C1 and C2 test OPPOSITE failure directions**, and neither alone is sufficient |
| **`η → √2/2`** (the derived bound replaced by T1's absolute one — the *pre-derivation* behaviour) | **5** — **`test_PART_A_the_bound_that_DOES_fall_out_BINDS…`**, **`test_eta_is_DERIVED_BY_THE_GRAPH…`**, **`test_PART_B_the_derived_bound_makes_a_MAJORITY…`**, C2, C3 | **THE control that makes the derivation worth believing.** A derivation whose instruments could not detect its absence would be worthless; installing T1's absolute bound in place of `η` reddens PART A **and** PART B. |

**C5 stayed GREEN under all three defects** — further confirmation that it is inert and
measures nothing (§1.1). An arm no injected defect can redden is not an arm.

---

# §13.1 — ENTAILED vs RISKED, declared BEFORE the run and honoured here

**ENTAILED, reported as consistency and NOT banked:** **C4** (the noise floor — `η_c ≤
√2/2` for every `c` makes the admission set a strict subset of T1's, and T1 already
refuses 100/100, so 0/100 was forced); **X** (the seed is not boot-loaded and every rule
is flag-gated at 0, so inertness is entailed by construction).

**RISKED — this is the result:** **A/M1–M6** (M5 could have been sound AND non-vacuous —
it is the colour rung's own winner — and was not), **A7** (`η` could have failed to bind
exactly as `√2/2` does; the `√2/2` arm is the live counter-example in the same run),
**B1**, **B2**, **C1** (**22 wrong-id rows exist at s=1** — the failing input was present
in the stimulus set and confirmed in range *before* the run), **C2**, **C3** (which
**broke**), **C5** (which **died**).

**Every risked arm's failing input was named in advance and confirmed IN RANGE** — and two
of them did not merely *could* have failed: **C3's prediction broke and C5's arm died.**

---

# §9 — defaults preserve committed results

- **Vision bench `scripts/rung7_vision_bench.sh`: 200 passed / 0 failed** with `data/` —
  identical to the baseline measured on this worktree **before any file was added**. Its
  no-Python-thresholds scan reports *"(none — every knob is graph data)"*.
- **sd orbit law `{2:1,3:2,4:2,6:2,12:4}` UNMOVED.**
- **Sibling gates green**, including continuous-pose **6/6** (T1 itself is untouched — this
  rung corrects its ATTRIBUTION, not its behaviour) and L1b uniqueness **21/21**.
- **New gate `tests/test_margin_migrated.py`: 21 passed.**
- The seed is **not boot-loaded** and ships its flag at **0**; **no committed seed file is
  edited**, so §9 holds on the files as well as at the flag.

# BOUNDS (§8) — what this rung does NOT do

A **uniqueness / refusal INSTRUMENT** and a **record correction**. **NOT a widening of any
invariance class** — `η_c ≤ √2/2` by construction and the rules fire only where T1 already
claimed, so no angle, shape or resolution refused before is recognized now; the instrument
can only turn a claim into a refusal. Specifically NOT shown:

- **NO MARGIN BOUND EXISTS** — that is now a *derived* fact rather than an open gap, but it
  is the same fact: **the margin instrument L1b named cannot be built honestly.** Do not
  describe this rung as having built one.
- **T1 remains a RANKING-based recognizer** even with the derived bound (25/63 ranking-only
  at s=4). The correction sharpens the record; it does not convert T1 into a bound-based
  result.
- **The instrument is built on T1 ONLY.** L1, `df_recognize`, colour identity and the
  similarity path are left exactly as L1b and the colour rungs left them.
- **`η` is derived FROM the codebook, so it inherits the codebook's limits.** These 7
  pentominoes are INSTALLED, not minted; whether `η` behaves under a *minted, growing*
  codebook is untested (prereg proviso 4).
- **`η_X` saturates at `√2/2`**, so the derivation is one degenerate shape away from
  emptiness on this codebook. It is not established that `η` is non-vacuous for codebooks
  in general.
- **The recall cost is REAL and larger than predicted** (2/7 untransformed admitted, 25/63
  headline refused). It is why the flag **ships OFF**.
- **C5 died and was replaced by a live test written after the fact** — the disagreement
  evidence is weaker than the pre-registration intended.
- **The triangle-inequality question is left open**: 0 violations were measured on this
  codebook, which is *not* a proof that the Modified Hausdorff verdict is a metric.
- Inherited unchanged from T1: the abstract lattice grain, dense-resampling as the
  definition of "resolution", the 2° angle grid, and the 7-pentomino object set.

## Why this is believed

Because the negative is **derived and instrumented**, not merely unfound: six rivals each
die to a *measurement*, including the one that won for colour, and the instruments are
proven able to see the opposite result — the `η → √2/2` control installs the
pre-derivation behaviour and the PART-A/PART-B arms go red. Because the positive is
gated against a **refuse-everything** build that scores perfect floors and is caught only
by the conjunction. And because **the two things that went wrong are reported first**: a
pre-registered prediction that broke (C3, pinned at its real value) and an arm that died
without noticing (C5, recorded as an instrument failure with its design error named).
