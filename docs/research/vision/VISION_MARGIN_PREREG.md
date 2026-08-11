# RUNG L1c — THE MARGIN INSTRUMENT, and the T1 RECORD CORRECTION — PRE-REGISTRATION

*Written and **committed BEFORE the confirmatory run** (§3). Base `main` HEAD
**07eeda24** (`git merge-base --is-ancestor 07eeda24 HEAD` verified, §11). Branch
`gamma-substrate/vision-margin-l1c`, worktree
`.claude/worktrees/agent-a0b4897bb592231f0`. Seeds **51000–51099** (FLOOR),
**51100–51199** (DISAGREE); **51200–51999 remain CLEAN**. Engine `7d5f50c18673`
(shared build, Rust source byte-identical; this rung adds **NO Rust**). `data/`
symlinked to canonical (§10.2); **baseline bench measured on this worktree BEFORE any
file was added: 200 passed / 0 failed.**

## 0. THE PREMISE — what L1b measured and deliberately did not build

`VISION_UNIQUENESS_RESULTS.md` established that **a candidate-COUNT predicate is only
meaningful where the bound actually BINDS**, and that T1 continuous pose is exactly where
it does not: **≥2 candidates lie inside its `√2/2` bound in 63/63 of its own headline
regime (median 4), margin 0.025 aliasing vs 0.180 clean.** L1b named a MARGIN instrument
and **refused to build it**, because picking a threshold that separates 0.025 from 0.180
*after seeing both* is precisely the magic number §13 forbids. This rung supplies the
derivation L1b demanded — or reports that none exists.

## 1. HYPOTHESIS (two-sided, §3.1)

**H_A (PART A):** a margin bound — a threshold on the winner-vs-runner-up separation —
**FALLS OUT** of the system's own constraints (§13). **Two-sided:** it may equally be
that **no margin bound exists**, in which case the derived negative is the result and
T1's recognition must be **restated as ranking-based rather than bound-based**.

**H_B (PART B):** with the derived instrument, T1's `√2/2` bound becomes **load-bearing**.
**Two-sided:** it may remain **near-vacuous**, leaving T1's 63/63 attributable to the
`Argmin` ranking alone (§13.2 applied to a threshold).

**MY PREDICTION, STATED IN ADVANCE (§3.7):** **H_A FAILS in the margin's own shape and
succeeds in a different one.** I predict **no margin bound falls out** — every candidate
threshold on the winner/runner-up *separation* is either an absolute constant (a view
from nowhere, §13), vacuous, or unsound — **but that a genuinely derived ADMISSION bound
does fall out**, namely **`η`, the codebook's own self-rounding residual**, and that
substituting it for `√2/2` makes L1b's *existing* count instrument transfer to T1. I
predict the corrected attribution is: **T1 as landed is 100% ranking-determined (0/63
rows have a unique candidate inside `√2/2`), and under the derived bound 38/63 become
bound-determined.** Provisos declared in §7.

## 2. THE DERIVATION AUDIT — the rivals, and how each is REJECTED (§13)

Each rival is rejected **BY MEASUREMENT** wherever measurement is possible. All PART-A
statistics are computed on T1's **deterministic** stimulus set (7 pentominoes × angles
5°..85°, 63 rows per resolution) — **no seed is drawn**, so these are reproductions of a
landed rung's own stimuli, not a fresh random draw. The pilot values below were measured
on that deterministic set and are **stated here in advance** (§3.7), which is the
strongest available form of prediction.

| # | rival margin bound | how it is tested | pilot value — PREDICTED for the confirmatory run | verdict |
|---|---|---|---|---|
| **M1** | **the lattice rounding floor `√2/2`** used as a MARGIN (T1's own bound) | rows with `d₂−d₁ ≥ √2/2` | **0/63 at s=1, s=2 AND s=4** | **REJECT — refuse-everything** |
| **M2** | **any ABSOLUTE margin** | median margin vs resolution | **0.0906 / 0.1065 / 0.1873** at s=1/2/4 — the margin SCALES with resolution | **REJECT — no absolute value transfers (§13 "a constant is a view from nowhere")** |
| **M3** | **the exact-tie margin** (refuse only `d₁ == d₂`) | count of exact ties | **0/63 at every resolution** | **REJECT — vacuous** |
| **M4** | **the observational-resolution step** — the residual's own angle-grid jitter | `|resid(2° grid) − resid(0.125° grid)|` | median **1.14e-4** (s=1) / **9.14e-4** (s=4), max **9.2e-3** — **two orders of magnitude BELOW the margins it would have to separate** | **REJECT — defined, but refuses nothing** |
| **M5** | **the codebook's PACKING RADIUS** `r_c = ½·min_{c'≠c} D(c,c')` — the colour rung's derivation transplanted | rows certified by `d₁ ≤ r_win`; and whether any certification is WRONG | `r ∈ [0.139,0.188]` (s=1), `[0.221,0.254]` (s=2), `[0.248,0.284]` (s=4). Certifies **19/63 at s=1 — of which 3 are WRONG** — and only **3/63, 4/63** at s=2, s=4 | **REJECT TWICE — UNSOUND at the aliasing floor, NEAR-VACUOUS above it** |
| **M6** | **a scale-free RATIO `d₁/d₂`** | max ratio per resolution | **0.9975** (s=1) vs **0.801** (s=4) — separating *in principle*, but **any threshold between them is chosen after seeing both** | **REJECT — a magic number by construction (§13/§5)** |

**M5's rejection is the load-bearing one**, because it is the rival that *did* work for
colour. It fails here for a measured structural reason: **the lattice-rounding residual
(median winner 0.38 at s=4) EXCEEDS the codebook's packing radius (≈0.25)** — T1's
observations do not lie inside their own quantum's cell. **A packing-derived certificate
cannot be non-vacuous in a codebook whose observation noise exceeds its packing radius**,
and that is a fact about T1's codebook, measured, not an argument.

### WHAT DOES FALL OUT — `η`, the SELF-ROUNDING RESIDUAL (the PART-A positive)

`√2/2` is the **worst-case per-point** rounding displacement — a loose absolute
over-bound imported from the lattice's geometry. The quantity the system actually has is
the **MHD the rounding actually induces on its own codebook**:

> **`η_c := max_{t ∈ cp_angles} resid( c , round(rotate(c, t)) )`**

— the largest residual a **true** instance of `c` can produce, computed from the
**codebook × the lattice × the system's OWN held angle grid** and **nothing else**: never
from the test observations, never from which answer is right. It introduces **no new
constant** (the probe grid *is* `cp_angles`, the grid T1 already holds) and it is
**per-shape and resolution-adapted**, where `√2/2` is one absolute number for everything.
`η_c ≤ √2/2` for every `c` by construction, so **the admission set can only ever
SHRINK** — this instrument cannot widen any invariance class (§8).

**It is not a margin.** The honest PART-A result is therefore: *the margin instrument
L1b named does not exist; the defect it was named to fix is real and is fixed by a
BOUND, after which L1b's existing count predicate transfers unchanged.*

## 3. THE STATISTICS, EXACTLY

`d_c` := T1's own per-candidate residual term, **extracted VERBATIM** from
`cp_recognize` (single source of truth, L1b's discipline). `k` := `Count(Filter(
NodesOfType('ShapeSignature'), c, Lte(d_c, Attr(c,'mg_eta'))))`. A row is **admitted**
iff `k < 2`, **ambiguous** iff `k ≥ 2`, **none** iff `k == 0`.

## 4. ARMS, PREDICTIONS, and §13.1 ENTAILED-vs-RISKED

| arm | statistic | **predicted** | §13.1 | failing input, and that it is IN RANGE |
|---|---|---|---|---|
| **A DERIVATION** *(RISKED)* | M1–M6 as tabulated in §2 | exactly the §2 column | **RISKED** | M5 could have been sound AND non-vacuous (it is the colour rung's own winner); it is not |
| **A7 THE BOUND BINDS** *(RISKED)* | candidates within `η` at s=4, min/med/max | **1 / 1 / 4** (vs **2 / 4 / 7** within `√2/2`) | **RISKED** | `η` could have failed to bind (median staying ≥2), exactly as `√2/2` does; the `√2/2` arm is the live counter-example in the same run |
| **B1 T1 IS RANKING-BASED** *(RISKED)* | rows with a UNIQUE candidate inside **T1's OWN** `√2/2` at s=4 | **0/63** | **RISKED** | any row with min-count 1 would refute; L1b measured min-count 2, one step away |
| **B2 ATTRIBUTION CORRECTED** *(RISKED)* | of T1's 63 headline recognitions: bound-determined vs ranking-only under `η` | **38 bound-determined / 25 ranking-only** | **RISKED** | could have been 0/63 or 63/63; both are in range |
| **C1 AMBIGUOUS-CASE REFUSAL** *(RISKED)* | at s=1: rows **unambiguous AND WRONG** | **0** (all 22 wrong ids fall inside the ambiguous set) | **RISKED** | **22 wrong-id rows exist at s=1** — any one landing unambiguous reddens this. **Confirmed in range: the failing input is present in the stimulus set.** |
| **C2 NO REGRESSION (CONJUNCTION)** *(RISKED)* | the 38 admitted rows at s=4 carry `mg_covered_by` **byte-identical** to T1's `covered_by`; T1 gate **6/6**; L1/L1b/L2/L3/category/similarity gates unchanged | 38/38 identical; all siblings green | **RISKED** | a refuse-everything build; **injected as control 1** |
| **C3 DISCRIMINATION exact-0** *(RISKED)* | wrong ids among ADMITTED rows; untransformed objects admitted | **0 wrong; 7/7** | **RISKED** | an admit-everything build; **injected as control 2** |
| **C4 FLOOR** *(ENTAILED — reported, NOT banked)* | 100 random 5-cell blobs, seeds **51000–51099**, admitted | **0/100** | **ENTAILED**: `η_c ≤ √2/2 ∀c` ⇒ admission ⊆ T1's, and T1 refuses 100/100 | — (declared unrisked in advance) |
| **C5 DISAGREEMENT** *(RISKED)* | fresh random shapes, seeds **51100–51199**: graph `mg_ncand` vs a re-derived independent count; and the split non-degenerate BOTH ways | **0 disagreements**, both classes non-empty | **RISKED** | a composition defect; a degenerate all-one-way split is reported as a finding, not passed |
| **X OFF-DAY (§9)** *(ENTAILED)* | flag at default 0 | no `mg_*` attribute written anywhere; T1 unmoved; bench **200/0**; sd orbit law **{2:1,3:2,4:2,6:2,12:4}** unmoved; siblings green | **ENTAILED** (seed not boot-loaded, every rule flag-gated at 0) | — |

## 5. POSITIVE CONTROLS (§12.3 / process rules 4, 5, 6) — to be MEASURED, not asserted

**Process rule 4 — the `Times` trap — is discharged BY CONSTRUCTION and ASSERTED:** this
composition contains **no `Times` node at all** (it is `Count`/`Filter`/`Lte`/`MaxOver`/
`MinOver`/`PointSetDist`/`Rotate`/`MapList`). A test pins that the emitted seed contains
zero `Times` terms, so the trap cannot silently apply. **The composition is FIXED as of
this pre-registration**; if it changes, that will be stated and the reddening re-derived.

**Process rule 5 — floors are NOT a gate.** Three defects will be injected into the real
builder, each regenerating the seed, running the gate, then reverting (seed verified
byte-equal by sha256 afterwards):

| control | injected defect | **must** redden | why it is the right control |
|---|---|---|---|
| **1 REFUSE-EVERYTHING** | `Gte(k,1)` in place of `Gte(k,2)` | **C2 NO-REGRESSION** | a build that refuses everything scores **perfect floors** on C4 and passes C3 — the conjunction is the gate |
| **2 ADMIT-EVERYTHING** | the ambiguity branch never fires | **C1** (and C3) | the mirror direction; proves C1 and C2 test opposite failures |
| **3 `η → √2/2`** | the derived bound replaced by T1's absolute one | **A7 and B2** | **the control that makes the derivation worth believing** — it installs the *pre-derivation* behaviour and the PART-A/B arms must SEE it |

## 6. DECISION RULE

- **PART A** returns a **derived negative on the margin** (predicted) or a derived margin
  bound (if one falls out). Either is reported first-class (§7). A bare *"I looked and
  found nothing"* is **NOT** sufficient — the negative must be carried by the measured
  rejection of each named rival, as the colour k=1 rung's was.
- **PART B**'s corrected attribution is reported **whatever it says**, and recorded in the
  ladder. T1's landed numbers (63/63, exact-0) **STAND as measured and are not
  re-litigated**; only the MECHANISM ATTRIBUTION is at issue.
- The instrument **ships OFF by default** (§9) regardless of outcome. It is a
  **refusal/uniqueness instrument, NOT a widening of any invariance class** (§8): it can
  only turn a T1 claim into a refusal.
- **No sweeps, no re-runs, exactly the listed arms** (§3.6). A further attempt needs a new
  pre-registration with a new mechanism-level hypothesis.

## 7. MY PREDICTION'S PROVISOS (§3.7) — what I expect to be wrong about

1. **I expect C5's fresh-shape split may come out lopsided.** Random 5-cell blobs are
   mostly far from every pentomino, so `k == 0` may dominate. If the split is degenerate I
   will **report it as the finding** (the colour rung's k=1 dead-zone precedent), not pass
   it off as a clean floor.
2. **I expect `η_X = √2/2` exactly** (X saturates the worst case at s≥2). If every shape
   saturated, `η` would collapse to `√2/2` and the whole derivation would be empty — that
   it does not is the substance of A7, and X is the live warning that it nearly could.
3. **I am least confident in B2's exact 38/25 split**, which depends on the codebook and
   the angle grid; the *direction* (a strict, non-trivial improvement over 0/63) is what I
   am confident in, and I will report the magnitude as measured, pinned at its real value
   rather than a convenient one.
4. **`η` is derived from the codebook, so it inherits the codebook's own limits.** If the
   codebook were minted rather than installed, `η` would move with it. This rung does not
   test that, and will say so in BOUNDS.

## 8. BOUNDS DECLARED IN ADVANCE (§8)

A **uniqueness / refusal INSTRUMENT** and a **record correction**. NOT a widening of any
invariance class; no angle, shape or resolution refused before is recognized now. Built on
**T1 only** — L1, deformation and colour identity are left exactly as L1b and the colour
rungs left them. The 7-pentomino codebook, the abstract lattice grain, and the
dense-resampling definition of "resolution" are all inherited from T1 unchanged.
