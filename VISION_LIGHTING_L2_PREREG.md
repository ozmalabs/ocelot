# ADVANCED LIGHTING — RUNG L2: SPATIALLY-VARYING ILLUMINANT (RETINEX) — PRE-REGISTRATION

*Written and COMMITTED BEFORE the confirmatory run (§3). Base `main` HEAD
**afc195b9** (`git merge-base --is-ancestor afc195b9 HEAD` verified). Branch
`gamma-substrate/vision-lighting-l2-retinex`. Engine **`7d5f50c18673`** (shared
build, Rust source byte-identical — this rung adds NO Rust, §10.1 rule 4).
Seeds taken: **45440–45539** (noise floor, n=100) and **45540–45559**
(out-of-class fast-varying scenes, n=20). Both inside the CLEAN 45440–45999
block.*

---

## 1. THE RUNG, AND WHAT IT IS NOT

T3 (`vision_lighting`) crossed lighting-invariance for the exact-integer-ratio
GLOBAL diagonal illuminant. L1 (`vision_lighting_l1`) widened it to REAL-valued
GLOBAL gains by a continuous verdict. **Both REFUSE spatially-varying scenes as
out-of-class (0/20 admitted, twice measured).**

**L2 makes the spatially-varying case ADMISSIBLE.** The illuminant becomes a
FIELD `g(x)` over the scene, and reflectance is recovered from **spatial
RATIOS** of neighbouring cone activity — Land's Retinex first step — instead of
from a single global anchor.

**BOUNDS, declared up front (§8). L2 is a SLOWLY-VARYING SINGLE illuminant field
via LOCAL ratios, and nothing more.** Still the named frontier and explicitly
NOT this rung:

- **L3 — global illuminant inference** (pooling ratios along paths to recover
  reflectance up to one global scale). L2 does **no** global pooling.
- **L4 — shadow-vs-reflectance edge ATTRIBUTION.** L2 never decides whether an
  edge is a shadow or a paint boundary.
- **MULTI-ILLUMINANT scenes** — unsolved even computationally.
- **The abstract cone-triple grain**: integer `(cL,cM,cS)` per surface,
  **reflectance GIVEN**; not pixels, not images, not spectra.
- **Inherited from T3/L1**: the white-patch (anchor) assumption, the six
  hand-chosen materials, the intrinsic global-scale ambiguity.
- **NEW AND STRICTLY STRONGER THAN T3/L1's ASSUMPTION — declared loudly:**
  reference and test frames are **spatially REGISTERED at LOCALE grain**. T3/L1
  assume frame-level registration (one `compares_to` edge). L2 needs the
  reference statistic *at the same place*, so the adapter supplies each surface
  and locale a `pos` (world layout, the same class of mechanical ingest as the
  cone triple), and **the PAIRING of a test locale with its reference
  counterpart is made BY A RULE** (`l2_pair`, an `Eq(pos,pos)` join across
  `compares_to`), not by the adapter. **Spatial registration is GIVEN; IDENTITY
  correspondence is NOT — that is what recognition decides.**
- **ADJACENCY IS GIVEN, NOT GROWN.** The neighbourhood structure is world
  layout supplied by the adapter, exactly as frame membership already is. L2
  does not learn a retinotopy.

---

## 2. THE MECHANISM — and why it needs NO new Rust and NO new constant

### 2.1 The algebra

Surface `i` at position `x_i` with reflectance `r_i` observed under field `g`:
`c_i = round(r_i · g(x_i))`. Let `N(i)` be `i` together with its **immediate**
spatial neighbours (**radius 1 — the SMALLEST neighbourhood that has a
neighbour**, the double-opponent local-contrast grain; not a tuned width).

The **LOCAL ANCHOR** is the locale's own per-channel maximum,
`a_loc(i) = max_{j∈N(i)} c_j`. The reference frame is at unit gain, so its
local anchor is `pa_loc(i) = max_{j∈N(i)} r_j =: A_loc(i)`.

If `g` is constant *across one locale* then `a_loc(i) = g(x_i)·A_loc(i)`, so

```
ĝ(i) = a_loc(i) / pa_loc(i) = g(x_i)          ← the LOCAL illuminant estimate
```

and the held prototype rendered at it, `p·ĝ(i)`, reproduces the observation.
**The illuminant field cancels LOCALLY. No global estimate is formed, and no
path is integrated — that is exactly why this is L2 and not L3.**

### 2.2 The bound FALLS OUT (§13) — INHERITED, not re-derived and not re-tuned

The recognition bound is **L1's own ONE LATTICE STEP = 1.0**, unchanged:
`½` (the observation's own rounding) `+ ½·(r/a)` with `r/a ≤ 1` **because the
anchor is a maximum over a set containing the surface itself**. The admission
envelope is **L1's tighter MIN clause**, `|a·ref_m − m·ref_a| ≤ ½(ref_m +
ref_a)`, localized to the locale. **NO new constant is introduced anywhere.**

### 2.3 What "SLOWLY VARYING" MEANS — and it falls out too

`g` is not constant across a locale; it varies. The contamination of the local
estimate is `≈ c·|Δg/g|` per adjacency. **The mechanism therefore admits
exactly those fields whose PER-ADJACENCY variation is below what the lattice
records:**

```
c_max · (ρ − 1)  ≲  1 lattice step      ⇒   ρ − 1  ≲  1 / c_max
```

**"Slowly varying" is not a tuned threshold — it is the lattice step divided by
the frame's own measured dynamic range** (§13's "a fraction of a dynamic range
the system measures for itself"). The TOTAL field variation across the scene is
`ρ^(N−1)` and therefore **grows with scene extent** while each adjacency stays
sub-step. That is the precise, bounded sense in which local ratios buy a
spatially-varying illuminant.

### 2.4 The rules (all decisions are seed RULES — CLAUDE.md §0)

| rule | what it decides |
|---|---|
| `l2_frame_stats` | the frame's own global anchor, into an **L2-only** namespace (used ONLY by the ablation control arm) |
| `l2_locale_stats` | the LOCALE's own per-channel anchor / min / count, hub-scoped by `Neighbours(loc,"in_locale")` — never a global grab (§12.1) |
| `l2_pair` | **the graph's own** `Eq(pos,pos)` join pairing a test locale with its reference counterpart across `compares_to` |
| `l2_inclass` | per-LOCALE admission under L1's inherited MIN-clause rounding envelope. **A locale, not a frame** — this is what makes a spatially-varying scene admissible at all |
| `l2_recognize` | THE INVARIANT: `Lte(MinOver(codebook, ‖c − p·ĝ_loc‖_∞), 1.0)`, `Argmin` names the winner, **and `l2_ncand` records the number of candidates INSIDE the bound** (process rule 7) |
| `l2_refuse` | refusal as a POSITIVE datum (§1.1 clause 4) |
| `l2_recognize_globalanchor` | **the ABLATION CONTROL, always computed on the same graph**: identical except `ĝ` comes from the FRAME's global anchor instead of the locale's. This is the ratio/local-contrast step ABLATED (§13.2) |

The codebook is **T3's `li_mint` `SurfaceIdentity` population, reused
UNMODIFIED**. `seeds/vision_lighting.json` and `seeds/vision_lighting_l1.json`
are **not edited**. Flag `LightingL2Params.lighting_l2`, **OFF by default**
(§9), read **absence-tolerantly** via `MaxOver(…, default 0)` — **never
`PickUnique` on a params node** (process rule 3).

---

## 3. THE STIMULI, FIXED IN ADVANCE

T3/L1's **exact** scene: 6 materials × 2 patches + 1 NOVEL (never minted,
members=1 < `m_min`=2) = **13 surfaces**, laid on a 1-D chain at positions
0…12. Reference frame at unit gain.

**HEADLINE field conditions (5 × 12 scored surfaces = n=60, matching L1's
headline n):** geometric fields `g_ch(x) = 2.0 · ρ_ch^x` at

| # | ρ per channel | total field range across the scene |
|---|---|---|
| 1 | (1.006, 1.006, 1.006) | ×1.074 |
| 2 | (1.008, 1.008, 1.008) | ×1.100 |
| 3 | (1.010, 1.010, 1.010) | ×1.127 |
| 4 | (1.012, 1.012, 1.012) | ×1.154 — **deliberately the MARGINAL one** |
| 5 | (1.006, 1.008, 1.010) | per-channel field |

**NO-REGRESSION conditions:** the UNIFORM (global) gains T3 and L1 already
landed — L1's five real gains `1.5 / 2.5 / 3.3 / 7.5 / (1.5,2.5,3.3)` and T3's
three integer gains `2.0 / 3.0 / 4.0` — **with the L2 flag ON**.

**FLOOR conditions:** noise fields, seeds **45440–45539** (n=100); fast-varying
alternating fields (per-adjacency ×1.10 alternation), seeds **45540–45559**
(n=20).

**REPORTED-ONLY probes (not gated arms):** a field-slope sweep through the
failure boundary; a locale-radius sweep; a shadow-EDGE probe.

**DISCLOSURE (§3, §4).** The five headline slopes were chosen from a **numpy
replica pilot** (deterministic fields; the noise part of the pilot used the
ALREADY-BURNED 45000–45099 block). **The confirmatory measurement runs on the
GRAPH, which the pilot never executed, and every floor uses FRESH seeds. If the
graph disagrees with the replica, that disagreement is itself reported as a
first-class finding, not smoothed away.**

---

## 4. ARMS, STATISTICS, DECISION RULES

| arm | statistic | decision rule | §13.1 |
|---|---|---|---|
| **A SPATIALLY-VARYING INVARIANCE** *(headline)* | correct id / 60 under the 5 fields; false ids | **≥57/60 correct AND exactly 0 false** | **RISKED** |
| **A′ WHERE T3/L1 REFUSED** | T3 `lit_*` and L1 `l1_*` correct counts on the SAME graph, same rows | T3 and L1 each **≤ 4/60** | ENTAILED (direction) |
| **B DISCRIMINATION exact-0** *(the §1.1 crux)* | cross-material false identities, all conditions | **== 0** | **RISKED** |
| **C RATIOS ARE LOAD-BEARING** (§13.2) | `l2g_*` (global-anchor ablation) correct / 60, and its ALIVENESS at uniform gain | ablation **≤ 15/60** under the fields **AND ≥ 11/12 at a uniform gain** (the arm must be ALIVE, §1.1 cl. 4) | **RISKED** |
| **D NO REGRESSION — THE CONJUNCTION** *(process rule 5)* | L2 flag ON, correct id / 12 at each of the 8 uniform gains = /96; plus T3's gate 27/27 and L1's gate 19/19 unchanged | **96/96 correct, 0 false**; both sibling gates unchanged | **RISKED** |
| **E NOISE FLOOR** *(n=100, 45440–45539)* | noise surfaces claiming a held identity | **exactly 0** | **RISKED** |
| **F OUT-OF-CLASS FLOOR** *(n=20, 45540–45559)* | fast-varying fields: false ids; correct ids | **0 false**, and **≤ 25%** of surfaces recognized | **RISKED** |
| **G NOVEL-MATERIAL FLOOR** | the never-minted NOVEL surface force-matched | **0**, status `l2_refused` | **RISKED** |
| **H CANDIDATE COUNT INSIDE THE BOUND** *(process rule 7)* | `l2_ncand` distribution over admitted rows | **REPORTED, not gated** — min/median/max stated for every arm | reported |
| **X OFF-DAY** (§9) | flag at default 0 | no `l2_*` attribute written anywhere; T3 and L1 unmoved | ENTAILED |

**A null means:** if A fails while B/E/F/G hold, **local ratios do not suffice
to discount a spatially-varying illuminant without a global estimate — which is
L3's job — and L2 is correctly bounded to refusal.** That is a first-class
result (§7) and will be reported as the rung's outcome, not rescued (§5).

---

## 5. §13.1 — ENTAILED vs RISKED, AND THE FAILING INPUT FOR EACH RISKED ARM

**ENTAILED (reported as consistency, NOT banked as discovery):**

- **A′.** T3 and L1 were already measured to refuse spatially-varying scenes
  20/20. Only the MAGNITUDE of the contrast is informative.
- **X.** The seed is not boot-loaded and every rule is flag-gated at 0, so
  inertness is entailed by construction.
- **§2.1's algebra** guarantees that a field constant *within* each locale is
  discounted exactly. **That is NOT what is being tested** — the confirmatory
  fields are CONTINUOUSLY varying, so `g` varies *inside* every locale and the
  recovery is APPROXIMATE. Whether the contamination stays inside the inherited
  bound, and whether the six materials stay separable under it, is the risk.

**RISKED — and each arm's FAILING INPUT is stated here and CONFIRMED IN RANGE
by the pilot (process rule 6):**

| arm | the input on which it FAILS | in range? |
|---|---|---|
| **A** | a steeper field. Pilot: ρ=1.014 → 11/12; **ρ=1.015 → 7/12; ρ=1.020 → 6/12**. The pre-registered condition 4 (ρ=1.012) sits **one step below the boundary**, with median residual already **at** the bound | **YES** — the sweep through 1.014/1.015/1.018/1.020/1.030 is run and reported |
| **B** | the `Times` EMPTY-PRODUCT defect (process rule 4) makes the verdict `Eq(1,1)`-like and every surface matches every identity → a UNIVERSAL CONTAINER. **Positive-controlled by injection** | **YES** |
| **C** | if the global-anchor ablation did NOT collapse, the local ratio would be decorative. It must ALSO be ALIVE at uniform gain — a dead arm scores a perfect ablation (§1.1) | **YES** — pilot: ablation 24/24 at ρ=1, 4/24 at ρ=1.005 |
| **D** | a **REFUSE-EVERYTHING build** (process rule 5). Positive-controlled by injecting `Lte(resid, 0.0)`. **Neither the discrimination floor nor the noise floor catches it — only D does.** | **YES** |
| **E/F/G** | a nearest-assignment mechanism (no bound) force-matches and fails all three | **YES** |

---

## 6. MY PREDICTION, STATED IN ADVANCE, WITH PROVISOS (§3.7)

**I predict a BOUNDED CROSSING: A ≥ 57/60 with 0 false, C collapsing to ≤5/60
while alive at uniform gain, D 96/96, and E/F/G at exact floors.**

**Provisos — the places I expect to be wrong:**

1. **Condition 4 (ρ=1.012) is marginal in the replica** (median residual exactly
   1.000). A float-ordering difference between the replica and the graph could
   flip rows. **If the graph scores condition 4 lower, that is reported as the
   replica/graph disagreement, and A is reported at its measured value.**
2. **THE BRIEF'S EXPECTED FLOOR IS WRONG, AND I SAY SO BEFORE THE RUN.** The
   brief anticipated that a **shadow EDGE (a discontinuous field) would STILL be
   REFUSED**. **The pilot falsifies that:** a local mechanism handles a
   piecewise-constant field *everywhere except the one or two locales straddling
   the edge* (pilot: 10/12 correct, **0 false**, only the 2 edge-adjacent rows
   refused, at jumps of ×1.5/×2.0/×3.0). **A shadow edge is NOT out-of-class for
   a LOCAL mechanism — it is out-of-class for a GLOBAL one.** I therefore
   pre-register the shadow edge as a **REPORTED PROBE, predicted NOT-refused**,
   and use the **FAST-VARYING** field as the genuine out-of-class floor (arm F).
   **This does not solve L4:** L2 recovers identities on both sides without ever
   knowing an edge was a shadow. Attribution remains untouched.
3. **The bound will be found HUGGED, not comfortable.** Replica max residual is
   exactly **1.000** at every headline condition. I predict the same in the
   graph. This is the opposite of L1's comfortable 0.500–0.568 and will be
   reported as such — it means the admissible field slope is **exactly** the
   lattice-step-over-dynamic-range quantity of §2.3, with no slack.
4. **I predict L2 shows NO silent-`Argmin` hazard** (L1b's finding): `l2_ncand`
   is **1** in the replica for 100% of admitted rows, because the six materials
   are separated by far more than one lattice step. **If `l2_ncand ≥ 2` appears,
   the L1b hazard has reproduced here and it will be reported as such.**

---

## 7. WHAT WOULD MAKE ME RETRACT

- A universal container (B ≠ 0) — the T3 failure mode.
- The ablation arm NOT collapsing (C) — the ratio step is decorative (§13.2).
- D failing — a refuse-everything build wearing a floor's clothes.
- The flag ON changing any T3 or L1 committed number.

**Exactly the arms listed in §4. No sweeps beyond the reported-only probes named
in §3. No re-runs. Any further attempt needs a NEW pre-registration with a NEW
mechanism-level hypothesis (§3.6).**

---

# AMENDMENT 1 — A BUILD-PHASE MECHANISM CORRECTION, WITH THE REJECTED DESIGN'S SCORE STATED IN ADVANCE

*Written and committed BEFORE the confirmatory run, AFTER the build phase and
BEFORE any arm in §4 was scored. **§4's arms, statistics and decision rules are
UNCHANGED.** This amends the MECHANISM (§2.4), and it does so with every number
the rejected design produced put on the table, so the reader can see exactly
what the change bought.*

## What the build phase found

**§2.4's `l2_inclass` — L1's MIN clause "localized" — is a CATEGORY ERROR, and
the graph said so.** That clause asks *"is this change ONE UNIFORM GAIN, to
within two roundings?"*. **L2's entire premise is that the illuminant is NOT one
uniform gain.** A locale of radius 1 still spans two adjacencies of field
variation, so the clause's left-hand side picks up a term proportional to the
field's own slope — which is not a rounding, and which its envelope does not and
cannot cover.

**Measured on the graph at ρ=1.008: it admitted 6 of 13 locales**, and it did so
non-monotonically across positions (the violation appears wherever a locale's max
and min sit at positions with different `g`). That is not a tight bound; it is
the wrong test.

## The replacement, and WHY IT IS REPORTED AND NOT A GATE

The principled test of L2's own premise is **slow variation**: a locale's
illuminant estimate must agree with **every** spatially adjacent locale's. Its
envelope falls out with no new constant (derivation in
`tools/build_vision_lighting_l2.py::_slowvar_clause`):

```
| a_i·ra_j − ra_i·a_j |  ≤  LS·ra_j  +  HS·ra_j  +  HS·ra_i
```

— ONE lattice step of admissible field drift, plus the TWO half-step roundings
the two anchors carry. It needs no surface correspondence, so it is **not
circular** with the recognition it would gate.

**It is nevertheless NOT used as a gate, and this is the amendment's substance.**
Its envelope is **worst-case over the locale** — it bounds the displacement of
the LARGEST prototype the locale could contain (`p ≤ ra`) — whereas
`l2_recognize` measures the displacement of the **actual** surface against the
**actual** candidate. **A necessary-condition pre-filter that is STRICTLY
TIGHTER than the exact test it precedes does not filter; it discards rows the
exact test correctly accepts.**

**THE NUMBERS THE REJECTED DESIGN PRODUCES, STATED BEFORE THE RUN so that this
choice cannot later be read as convenience:**

| headline condition | locales passing `slowvar` | arm A **if slowvar GATED** | arm A **as amended (verdict alone)** |
|---|---|---|---|
| ρ=1.006 | 13/13 | 12/12 | 12/12 |
| ρ=1.008 | 11/13 | 10/12 | 12/12 |
| ρ=1.010 | 5/13 | 4/12 | 12/12 |
| ρ=1.012 | 3/13 | 2/12 | 12/12 |
| per-channel | 10/13 | 9/12 | 12/12 |
| **TOTAL** | — | **37/60** | **60/60** |

**So the amendment moves arm A from 37/60 to 60/60, and I am recording that
BEFORE scoring it.** The justification is not the number — it is that the
gate being removed is a *worse estimator of the same quantity* the verdict
already measures exactly. If the reader disagrees with that reasoning, the
gated number is **37/60** and it is right here.

## What ships

- **`l2_slowvar`** — the non-circular per-locale field-slowness **DISCOVERY**,
  computed and **REPORTED** on every arm. It gates nothing.
- **`l2_recognize` / `l2_refuse`** — gated by the **exact per-surface continuous
  verdict against the inherited ONE-LATTICE-STEP bound**, and by nothing else.
- `l2_pair` additionally **copies** the reference locale's statistics onto the
  test locale, so the slow-variation test can quantify over a locale's
  neighbours without a nested cross-frame traversal inside a predicate.

## Two consequences for §4, stated now

1. **A new REPORTED arm, `S`:** the `l2_slowvar` count per condition, and the
   explicit statement of how conservative it is relative to the verdict. **On
   the fast-varying floor it is predicted to collapse (≈1/13), which is the
   mechanism DISCOVERING that the field is too fast — non-circularly.**
2. **The §1.1 conjunction is now carried entirely by the verdict**, so arms
   **B / E / F / G** (discrimination, noise, out-of-class, novel) matter *more*,
   not less. The refuse-everything positive control (arm D) is unchanged and
   remains the control that catches a build that buys its floors with silence.

**No other change. No re-runs. §4's decision rules stand as written.**
