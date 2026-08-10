# CAN ANY GRAPH-RESIDENT COMPARATOR SURVIVE TRANSLATION? — PRE-REGISTRATION

*Written and COMMITTED before any confirmatory number was taken (§3). Base
branch `gamma-substrate/vision-invariant-comparator` off
`eb403264d8055f124726d4a66d9e655b4a145079`.*

**Seed block: 57000–57999** (allocated before launch; a concurrent rung holds
56000–56999 — no seed outside this block is drawn).

---

## 0. THE QUESTION THIS RUNG EXISTS TO ANSWER

`VISION_CROSSFRAME_IDENTITY_RESULTS.md` established, and disproved its own
headline with, one measurement: **the graph's cross-frame score is EXACTLY pixel
Hamming overlap** (`xf_max == nn_score` on 74 560 of 74 560 trials). What it
demonstrated is **PERSISTENCE, not INVARIANCE**, and it priced that: on real
photographs, identity survives **one pixel** of translation, is
CI-indistinguishable from the arrangement floor at **two**, and falls *below*
the floor by four.

**This rung asks whether ANY graph-resident comparator beats that one-pixel
horizon — and it may only claim a win if invariance rises WITHOUT
discrimination collapsing.**

---

## 1. THE GROUP, AND WHY IT IS THE RIGHT ONE

**The nuisance group quotiented is 2D integer translation, ℤ².** Stated as
required, with the reason, because the immediately preceding rung got exactly
this wrong:

`VISION_INK_VENTRAL_RESULTS.md` imported **D4** identity-untangling from a
synthetic crossing into handwriting and it **HARMED −11.3pp at 8× the compute**
— because on that domain the group was wrong: a reflected or 90°-rotated glyph
is a *different* glyph, so D4 is identity-CHANGING for scripts, and untangling
the wrong group is worse than not untangling at all.

Translation is the opposite case on this domain, on three grounds:

1. **It is identity-PRESERVING for an image region.** A patch of fur, sky or
   cel-shaded line moved three pixels is the same patch. Nothing in the
   semantics of a natural-video region changes under translation, which is
   precisely what failed for D4 on glyphs.
2. **It is the DOMINANT nuisance between adjacent video frames.** Camera pan,
   camera shake and object motion are, to first order and at a small aperture,
   translation. The incumbent's own Δ curves are — by its §5 — a measurement of
   *how much sub-two-pixel motion a broadcast frame step contains*.
3. **It is the group the incumbent measurably fails on**, at a magnitude
   (one pixel) far below what the aperture's information content permits (§4.3).

**Rotation, scale and reflection are NOT quotiented here, deliberately.** They
are neither dominant at a 6×6 aperture across one frame step nor uniformly
identity-preserving, and the ink rung is the standing evidence that adding a
group you have not justified costs accuracy.

---

## 2. THE COMPARATORS (the arms)

Every comparator uses the **same decision**: `Argmax` over a held codebook by
`ShapeDecode`'s `covered_count`, expressed as graph data
(`seeds/vision_invariant_comparator.json`). **No new Rust, no new Term, no new
constant.** They differ only in what is held and what is presented.

| id | comparator | what quotients the group |
|---|---|---|
| **Q0** | orbit radius ρ=0 | **nothing — this IS the incumbent** |
| **Q1** | orbit radius ρ=1 | graph `MaxOver`/`Argmax` over a 3×3 orbit |
| **Q2** | orbit radius ρ=2 | … over a 5×5 orbit |
| **Q3** | orbit radius ρ=3 | … over a 7×7 orbit |
| **R** | centroid registration | one-shot: re-origin on the tile's own rounded intensity centroid, then compare. No search. |
| **H** | value histogram | position-free encoding. Translation-invariant BY CONSTRUCTION. |

**Q(ρ) — the quotient, and it is the GRAPH's.** A probe is presented as an
`ObsGroup` whose members are the same aperture sampled at every translation in
the Chebyshev ball of radius ρ. Rules 1–2 score each member against the 16-entry
codebook; rules 3–4 (`icg_score`, `icg_identify`) take the **max over the orbit**
and read the **winning member's answer**. The quotient is a `MaxOver` and an
`Argmax` over graph-resident members — not an adapter loop, not a Python branch.
**ρ is the INDEPENDENT VARIABLE of this experiment**, the extent of ℤ² being
quotiented; it is not tuned, and ρ=0 reproduces the incumbent exactly.

**H is the ANCHOR that makes the gate a real conjunction.** It is perfectly
translation-invariant and, because the A3 floor permutes values over positions
and therefore preserves the value multiset **exactly**, its discrimination
against that floor is **0 by construction**. An arm that "wins" on invariance
alone must land where H lands. It is included so that failure mode is visible on
the same axes as everything else rather than argued about.

**R is the cheap rival mechanism** — register once, compare once — included so
"quotient by searching the orbit" is tested against "quotient by registering",
not only against doing nothing.

### 2.1 What is NOT claimed, declared in advance (§13.1)

**On C3 the displacement is a RIGID INTEGER TRANSLATION, so for d ≤ ρ the orbit
CONTAINS the exact translate and Q(ρ) recovering it is FORCED BY CONSTRUCTION.**
Reproducing that is a tautology with error bars, not evidence, and it is named
here so it cannot be presented later as a discovery. **The quantities this rung
actually RISKS are three:**

- **(a) the DISCRIMINATION COST** — whether widening the orbit makes wrong
  regions match too;
- **(b) REAL VIDEO**, where motion is neither rigid, nor global, nor integer,
  and where nothing guarantees the true content is anywhere in the orbit;
- **(c) the TIES** — whether invariance is bought by making everything tie.

---

## 3. CORPORA (reused from the incumbent, so the numbers are comparable)

| id | what | statistics | motion | counts |
|---|---|---|---|---|
| **C1 CARTOON** | Jellyfin, *Middlemost Post* S2E1, `08630d4b7b215c469df19b9c42d7b617`, positional index 0 | broadcast cartoon | REAL | 150 frames, every 2nd from t=300 s, 24×24 grey; **50 base frames**; 800 trials per (arm, comparator, Δ) |
| **C2 LIVE-ACTION** | Jellyfin, *Secrets of the Zoo: Down Under* S3E15, `119eca433329b36b19e5d69fef84966e`, positional index 3 | natural photographic | REAL | same protocol; **50 base frames** |
| **C3 APERTURE** | BSDS300, **24 photographs**, 24×24 centre window translated by a KNOWN d | natural photographic | **SYNTHETIC (known d)** | 24 photos × 16 regions = **384 trials per (arm, comparator, d, mode)** |

**Coverage is part of every claim (§8).** Two episodes of two series and 24
photographs. Cartoon and natural photographs have very different statistics —
the retina rung measured firing rates of 46.6% vs 80.3% — so **no number is
pooled across corpora** and every claim carries its corpus.

**C3 is the PRIMARY instrument for invariance**, because it is the only corpus
where the displacement is known. The video corpora are the primary instrument
for **whether any of it transfers to real motion**.

Fixed at the incumbent's values for comparability and NOT swept: k=4
quantization levels, 6×6 regions, 24×24 grid. Both are hand-set (§13); the
incumbent already sensitivity-checked k ∈ {2,4,8} and found its verdict stable.

---

## 4. THE METRICS — BOTH, AND NEITHER ALONE IS A RESULT

### 4.1 INVARIANCE — the translation horizon `T`

On C3, accuracy as a function of displacement d ∈ {0,1,2,3,4,6}.

> **`T(arm)` = the largest d at which the arm's accuracy is CI-separated from
> its OWN A3 arrangement-destroyed floor at that same d.**

Primary unit is the **PHOTO** (16 regions of one photograph share content and
are not independent), n=24, mean with a 95% t-CI, t(0.975, 23) = 2.069.
Trial-level Wilson (n=384) is reported as a declared secondary and is
anticonservative. *(The incumbent read C3 at trial level only; using the photo
as the unit is strictly stricter against myself, which §5 permits and §1
demands.)*

**Displacement modes**, both declared now:
- **AXIS (0, d)** — PRIMARY, byte-matched to the incumbent's protocol so `T(Q0)`
  is directly comparable to its measured 1.
- **DIAGONAL (d, d)** — SECONDARY, the honest ℤ² condition, run at
  ρ ∈ {0, 2} and d ∈ {0,1,2,3} only (a declared cost bound, not a sweep).

### 4.2 DISCRIMINATION — the margin `M` against an alive floor

> **`M(arm)` = accuracy(d=0) − accuracy(A3 arrangement-destroyed, d=0)**,
> as a **paired per-photo difference** with a 95% t-CI on that difference.

Plus three aliveness conditions, every one of which must hold for an arm's
numbers to be read at all (§1 clause 4):

- **G3 ALIVE** — normalised answer entropy ≥ 0.50 on every arm;
- **G2 NOISE** — a uniform-random tile scores in [0.02, 0.15];
- **G1 CEILING** — the base tile itself is identified, reported per comparator
  (the incumbent's G1 FAILED on C2 at 0.9519 because natural 6×6 tiles are not
  unique after quantization; that ceiling is a property of the corpus and is
  expected to recur).

And the tie diagnostic that this rung exists to watch: **mean `icg_ntied`**, the
number of orbit members achieving the group maximum.

### 4.3 THE CONTENT BOUND — a §13 number that FALLS OUT

At a 6×6 aperture, an axis displacement of d retains **(6−d)/6** of the base
tile's content; a diagonal displacement retains **((6−d)/6)²**. At d=6 the
aperture holds **no** original content. **Therefore no comparator whatsoever can
have T ≥ 6 in axis mode**, and this bound is fixed by the aperture geometry, not
chosen. It is stated in advance so a ceiling is not later mistaken for a
failure. Note what it implies about the incumbent: at d=1, **five sixths** of
the content is still present and the incumbent already scores 0.464 — the gap
between one pixel and the information bound is real headroom, not noise.

Similarly derived, not chosen: **discrimination must collapse as ρ → 6**,
because the region tiling pitch is 6, so at ρ=6 a region's orbit reaches its
neighbour's position exactly. The predicted crossing of the invariance and
discrimination curves therefore falls out of the ratio ρ/REGION.

---

## 5. THE DECISION RULE — CONJUNCTIVE, fixed now

**An arm BEATS THE INCUMBENT iff ALL THREE hold:**

1. **INVARIANCE:** `T(arm) > T(Q0)` on C3, AXIS mode; **and**
2. **DISCRIMINATION:** `M(arm) > 0` with its 95% paired t-CI **excluding 0**;
   **and**
3. **ALIVE:** G3 entropy ≥ 0.50 and G2 noise in [0.02, 0.15].

**Every other outcome is named in advance:**

- (1) holds, (2) fails ⇒ **INVARIANCE BOUGHT WITH DISCRIMINATION.** Reported as
  the trade-off finding, never as a win. This is the H-anchor's territory.
- (2) holds, (1) fails ⇒ the quotient is inert on this domain.
- Neither holds for any arm ⇒ **CLEAN NEGATIVE: no graph-resident comparator in
  this family beats the one-pixel horizon.** This is a full result and will be
  reported as one — it localises the architecture's weakness rather than
  patching around it.

**The deliverable is the TRADE-OFF CURVE `(T, M)` over ρ, not a single number.**

**No metric may be changed after this file is committed (§5).** A failed gate is
reported failed. Exactly the arms and cells listed here; no sweeps, no re-runs.

---

## 6. MY PREDICTIONS, IN ADVANCE (§3.7)

| # | prediction |
|---|---|
| 1 | **Q0 reproduces the incumbent**: C3 axis `T(Q0) = 1`, accuracy(d=0) ≈ 0.89. *(On a DIFFERENT engine — `24fb7a714c38`, not the incumbent's `7d5f50c18673` — and with the codebook-scope defect closed, so I expect agreement in T and small movement in the levels.)* |
| 2 | **`T(Q ρ) = ρ`** for ρ ∈ {1,2,3} in axis mode, bounded above by §4.3's content bound. Forced by construction (§2.1) and stated so it is scored, not celebrated. |
| 3 | **`M` falls monotonically with ρ but does NOT collapse by ρ=3**: M(Q0) ≈ 0.69, M(Q1) ≈ 0.65, M(Q2) ≈ 0.58, M(Q3) ≈ 0.45, all CI-excluding 0. **⇒ I predict the conjunction is SATISFIED and the one-pixel horizon IS beaten, by Q1/Q2/Q3.** |
| 4 | **R FAILS**: `T(R) = 1`, no better than the incumbent, and `M(R)` ≈ 0.5 — a 6×6 tile at k=4 has too coarse a centroid, and aperture truncation moves it. |
| 5 | **H is flat in d and `M(H) = 0.0000` EXACTLY** — perfect invariance, zero discrimination. If M(H) is not exactly 0 my encoder is wrong, not the world. |
| 6 | **Video, two-sided.** Q1/Q2 raise A1 at Δ=25 on both corpora relative to Q0; the Δ-horizon moves up at most one step on C2 or not at all. At 24×24 the incumbent already reads 0.958 at Δ=1, so there is little headroom at short Δ, and I explicitly allow a null here. |
| 7 | **`icg_max == nn_score` on ≥0.99 of groups** — the group comparator is EXACTLY shift-tolerant Hamming, the incumbent's prediction 5 carried up one level. I expect this to be confirmed and to be, again, the most constraining fact in the result. |
| 8 | **mean `icg_ntied` rises monotonically with ρ** — the tie count is where invariance is paid for. |

**Provisos I expect to break:** that C3's per-photo variance is small enough for
n=24 (natural photographs contain near-duplicate 6×6 tiles — the incumbent's G1
failure — so some photos may be near-unidentifiable and the photo-level sd may
be large); and that real-video motion is enough like integer translation for
prediction 6 to be testable at all.

---

## 7. WHAT FALSIFIES THIS

- **The headline claim** ("a translation quotient beats one pixel") is falsified
  if no ρ yields `T > 1` **with** `M > 0` CI-excluding 0.
- **Prediction 3** is falsified if `M` collapses to 0 (or its CI covers 0) at any
  ρ ≤ 3 — which would place the orbit quotient in H's territory and make this a
  trade-off result rather than a win.
- **Prediction 7** is falsified if score agreement with the outside-the-graph
  reference falls below 0.99 — which would mean the graph is computing something
  other than shift-tolerant overlap, and would need its own investigation before
  any claim.
- **The instrument** is falsified if any G-gate fails: a dead arm scores a
  perfect floor (§1.1) and a floor produced by silence is not a floor.

---

## 8. BOUNDS ACCEPTED IN ADVANCE (§8)

- **Toy resolution.** 24×24 frames, 6×6 apertures. Nothing here is a claim about
  video at any real resolution.
- **Nothing is learned.** The codebook is one frame's regions, held for one
  comparison and discarded. This measures a COMPARISON.
- **Fixed aperture, not tracking.** No object correspondence, no segmentation.
- **Two episodes, 24 photographs.** Not a survey.
- **Q3 is not run on video** (cost) — a declared bound, not a result.
- **The cost of the quotient is linear in the orbit** ((2ρ+1)² decodes per
  probe) and IS a cost: Q3 is 49× Q0. Any win must be read against that, exactly
  as the ink rung's −11.3pp was read against its 8×.
- **§9:** the seed ships `invcomp = 0.0`, is not in the default boot set, and no
  committed seed, rule, default or Rust file is touched.
- **The measurement may not be fully deterministic.** The incumbent found an
  `Argmax`/`Eq` disagreement inside `ShapeDecode` that did not reproduce (its
  §4.2). That defect is NOT fixed here and is a live risk to these numbers; a
  replay check is run and reported.
