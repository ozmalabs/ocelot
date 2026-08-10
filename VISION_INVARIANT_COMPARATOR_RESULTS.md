# CAN ANY GRAPH-RESIDENT COMPARATOR SURVIVE TRANSLATION? — RESULTS

*Pre-registration: `VISION_INVARIANT_COMPARATOR_PREREG.md`, committed BEFORE the
run at **`c5f34f29fd332eaaac1bf07a1e30e5e2f2b41fd7`** (base
**`eb403264d8055f124726d4a66d9e655b4a145079`**).*

**Engine (§10):** `24fb7a714c38` @
`runners/dsl/python/substrate_rs/_native.abi3.so` — **this rung's OWN pinned
copy**, installed with `cp --remove-destination` (never through a symlink, §11
rule 2) and hashed before and after (`24fb7a71…`, identical). Rust source
verified byte-identical to the canonical tree's; **this rung adds no Rust, no
Term and no constant.** *This is NOT the incumbent's engine* (`7d5f50c18673`) —
which is why the incumbent comparator is **re-measured here as an arm** rather
than quoted.
**Machine:** AMD Ryzen 5 9600X, 12 logical cores, **under heavy concurrent load
for most of the run** (a concurrent rung running ~30 CPU-saturated processes;
load average 8.1–9.9 at the start, 1.9–2.9 at the end). Wall-clock numbers are
therefore inflated and are reported only as costs. **Every other quantity is
deterministic under fixed seeds — verified, not assumed (§6).**
**Selector:** `scripts/invariant_comparator_measure.py` (confirmatory) +
`scripts/invariant_comparator_report.py` (presentation only).
**Raw:** `results/invariant_comparator_{c3,video,replay}.json`,
`results/invariant_comparator_rows_*.json`.
**Seeds:** block **57000–57999** claimed and used for codebook insertion-order
permutations, the arrangement-destroyed floors, the distant-frame draws and the
noise probes. **No seed outside the block was drawn.**

---

## 0. THE HEADLINE, IN ONE PARAGRAPH

**Yes — a graph-resident comparator survives translation, and the one-pixel
horizon is beaten. The trade-off is real, graded, and it turns.** Quotienting by
the translation group inside the graph (`MaxOver` + `Argmax` over an orbit held
as graph data) moves the measured translation horizon **1 → 2 → 3 → 3** as the
orbit radius goes ρ=0→1→2→3, while the discrimination margin against an alive
arrangement floor falls **0.578 → 0.531 → 0.492 → 0.438** and the mean number of
regions tied at the winning score rises **3.22 → 3.62 → 4.03 → 4.39**. Every
orbit arm passes the conjunction; **the curve KNEES AT ρ=2**, where the horizon
saturates while cost keeps doubling. Three findings are worth more than the
verdict. **(1) The entire discrimination cost is TIE INFLATION on synthetic
translation — `true_achieves_max` is 1.0000 for every comparator at every
radius, so widening the orbit never lowers the true region's score; it raises
other regions' scores until they tie.** **(2) Over-quotienting is ACTIVELY
HARMFUL, not merely wasteful:** outside its radius a wide orbit scores *below*
the incumbent (Q3 at d=4: 0.086 vs Q0's 0.122). **(3) The histogram anchor
scores 0.7161 accuracy — HIGHER than Q2 (0.628) and Q3 (0.576) — with a margin
of EXACTLY 0.0000 against its own floor.** Ranking by accuracy alone would have
crowned the one arm that carries no arrangement information at all, which is
precisely why the gate was pre-registered as a conjunction. And on **real
motion, where nothing is forced by construction**, the trade-off is starkest:
Q1 extends C2's identity horizon from **Δ=5 to Δ=25** while *losing 11.8pp at
Δ=1. The graph's score is again **EXACTLY** the outside-the-graph reference —
`icg_max == nn_score` on **204 of 204 cells, 124 096 of 124 096 trials** — so
what was built is a shift-tolerant Hamming classifier expressed as graph data.

---

## 1. DISCLOSURE: HOW FOUR OF THE SIX C3 CELLS WERE FIRST PRODUCED

**Reported because it affects how §2's Q0/Q1/R/H cells should be read, and
because concealing it would be exactly the forking-paths garden §4 forbids.**

After committing the pre-registration I launched what I intended as a **3-photo
smoke test**, by importing the runner and setting `m.N_PHOTOS = 3`. **The
override did not take**: `bsds_photos(n=N_PHOTOS)` binds its default at
definition time. So the "smoke" ran the **full pre-registered configuration** —
24 photographs, the pre-registered seeds, the pre-registered displacement grid —
for Q0, Q1, R and H. **I saw four of the six C3 comparator cells before Q2 and
Q3 had been run.**

**What this does and does not compromise.** It opens no forking path: the
pre-registration was already committed and immutable, every constant came from
it, no metric, arm or decision rule was changed afterwards, and the computation
is deterministic. What it does mean is that **I was not blind to Q0/Q1/R/H while
Q2/Q3 ran.** Discount accordingly.

**It also produced something useful, which is why it is documented rather than
merely confessed:** those four cells were then recomputed by the confirmatory
run in a **separate process**, and agreed. That is a full-scale cross-process
determinism check on top of the explicit replay (§6).

**The generalisable lesson, which is a §12-class instrument defect:** *a "smoke
test" that silently runs the full configuration is indistinguishable from the
real thing until you read the log.* A Python default argument is evaluated once,
at definition; overriding the module global afterwards does nothing. **A scale
knob that can be set and ignored is not a knob.**

---

## 2. THE TRADE-OFF CURVE — the deliverable

### 2.1 C3, AXIS MODE — the primary invariance instrument (known displacement)

24 BSDS300 photographs, 384 trials per cell. **Primary unit is the PHOTO**
(16 regions of one photograph share content and are not independent), n=24,
95% t-CI, t(0.975, 23)=2.0687. Trial-level Wilson given as declared secondary.

| cmp | ρ | **T (horizon)** | **M (margin) [95% paired t-CI]** | excl 0 | acc d=0 | A3 d=0 | entropy | G2 noise | ties/region | compute |
|---|---|---|---|---|---|---|---|---|---|---|
| **Q0** *(= incumbent)* | 0 | **1** | **0.5781 [0.4805, 0.6757]** | ✅ | 0.7604 | 0.1823 | 0.986 | 0.0651 | 3.219 | 1× |
| **Q1** | 1 | **2** | **0.5312 [0.4274, 0.6351]** | ✅ | 0.7005 | 0.1693 | 0.985 | 0.0677 | 3.622 | 9× |
| **Q2** | 2 | **3** | **0.4922 [0.3751, 0.6093]** | ✅ | 0.6276 | 0.1354 | 0.983 | 0.0833 | 4.029 | 25× |
| **Q3** | 3 | **3** | **0.4375 [0.3089, 0.5661]** | ✅ | 0.5755 | 0.1380 | 0.979 | 0.0599 | 4.391 | 49× |
| **R** *(centroid)* | — | **2** | **0.5625 [0.4604, 0.6646]** | ✅ | 0.7604 | 0.1979 | 0.986 | 0.0755 | 3.219 | 1× |
| **H** *(histogram)* | — | **none** | **0.0000 [0.0000, 0.0000]** | ❌ | 0.7161 | 0.7161 | 0.986 | 0.0807 | 3.323 | 1× |

**PRE-REGISTERED VERDICT (§5 of the prereg, applied mechanically): Q1, Q2, Q3
and R ALL BEAT THE INCUMBENT.** Each satisfies all three clauses — horizon
strictly greater than Q0's 1, margin CI excluding 0, and alive (entropy ≥ 0.50,
noise floor inside [0.02, 0.15]). **H fails clause 2 exactly, by construction.**

### 2.2 ACCURACY vs DISPLACEMENT — where each quotient earns and where it costs

A1 / A3-floor, photo-level. `*` = A1's CI lower bound above its own floor's upper bound.

| cmp | d=0 | d=1 | d=2 | d=3 | d=4 | d=6 |
|---|---|---|---|---|---|---|
| Q0 | 0.760/0.182* | 0.432/0.169* | 0.221/0.167 | 0.154/0.138 | 0.122/0.120 | 0.047/0.112 |
| Q1 | 0.701/0.169* | 0.711/0.154* | 0.292/0.154* | 0.172/0.141 | 0.135/0.115 | 0.055/0.107 |
| Q2 | 0.628/0.135* | 0.651/0.130* | 0.656/0.135* | 0.208/0.128* | 0.070/0.125 | 0.055/0.115 |
| Q3 | 0.576/0.138* | 0.560/0.130* | 0.578/0.135* | 0.583/0.130* | 0.086/0.107 | 0.065/0.112 |
| R | 0.760/0.198* | 0.500/0.174* | 0.279/0.159* | 0.174/0.135 | 0.109/0.133 | 0.055/0.099 |
| H | 0.716/0.716 | 0.271/0.271 | 0.182/0.182 | 0.143/0.143 | 0.130/0.130 | 0.047/0.047 |

**Read the Q3 row across.** It holds ~0.58 flat from d=0 to d=3 — the orbit
contains the exact translate throughout — and then falls off a cliff to 0.086 at
d=4, **BELOW Q0's 0.122 and below Q2's own d=0 floor-crossing**. Q2 does the
same thing one step earlier (0.070 at d=4). **A wide quotient is not merely
wasteful outside its range; it is worse than no quotient at all**, because every
one of the 15 distractor regions also gets (2ρ+1)² chances, and once the true
translate is out of reach the distractors win. This is the sharpest single
statement of the trade-off in the data.

**Every H row has A1 exactly equal to A3, to four decimals, at every
displacement.** That is not a coincidence to be explained; it is the anchor
doing its job.

### 2.3 THE KNEE, AND WHY IT IS AT ρ=2

**T saturates at 3 while M keeps falling and compute keeps doubling.** Q3 costs
2× Q2's comparisons, gives up a further 0.055 of margin, and buys **zero**
additional horizon. On this corpus **ρ=2 is the knee of the curve.**

**Why the horizon runs one step BEYOND the orbit at small ρ but not at large ρ**
— the mechanism, read off the data rather than asserted. At d = ρ+1 the best
orbit member leaves a 1-pixel residual offset, which is worth about what Q0
scores at d=1 (0.432). Q1 keeps that bonus (0.292 at d=2, separated) because it
has only 9 distractor windows per region; Q3 loses it (0.086 at d=4) because it
has 49. **The +1 partial-overlap bonus survives at small radius and is destroyed
at large radius by distractor inflation.** Both halves fall out of the geometry —
nothing was tuned.

**And the ceiling is the corpus's, not the instrument's.** `true_achieves_max`
is **1.0000** for every comparator at d=0: the true region *always* attains the
maximum score. Every single error is an arbitrary tie-break between 6×6 tiles
that are identical after k=4 quantization — mean regions tied 3.219 (Q0) rising
to 4.391 (Q3), fraction tied>1 rising 0.284 → 0.534. **So the whole
discrimination cost of the translation quotient, on this corpus, is TIE
INFLATION.** This is the natural-image identifiability limit the incumbent hit
as a failed G1 gate, here measured as a graded quantity.

### 2.4 C3, DIAGONAL MODE — the honest ℤ² condition (declared secondary)

| cmp | d=0 | d=1 | d=2 | d=3 | **T** |
|---|---|---|---|---|---|
| Q0 | 0.760/0.167* | 0.323/0.167* | 0.182/0.164 | 0.148/0.143 | **1** |
| Q2 | 0.628/0.133* | 0.677/0.148* | 0.760/0.146* | 0.177/0.138 | **2** |

The axis result is not an artifact of quotienting only one axis: under genuine
2D displacement the incumbent still stops at 1 and Q2 reaches 2. The content
bound bites harder here — ((6−d)/6)² retains only 4/9 at d=2 — which is why Q2's
diagonal horizon is 2 rather than the axis mode's 3.

### 2.5 REAL MOTION — where NOTHING is forced by construction

50 base frames per corpus, 800 trials per cell, base-frame level, t(0.975,49)=2.0096.
Measured inter-frame motion (mean |Δ|, 0–255): C1 **2.890** (sd 10.065, max 52.343);
C2 **3.182** (sd 6.041, max 44.754). Both heavy-tailed — near-static steps punctuated
by shot cuts.

**C1 CARTOON** — chance 0.0625.

| cmp | **T (Δ-horizon)** | A1 Δ=1 | A1 Δ=5 | A1 Δ=25 | **M(Δ=1)** | G1 | G2 |
|---|---|---|---|---|---|---|---|
| Q0 | **25** | 0.9613 [0.9067,1.0158] | 0.7925 | 0.2700 | +0.7462 [0.6970,0.7955] | 1.0000 | 0.0788 |
| Q1 | **25** | 0.9575 | 0.8075 | 0.3113 | +0.7662 [0.7176,0.8149] | 1.0000 | 0.0675 |
| Q2 | **25** | 0.9413 | 0.7825 | 0.2687 | +0.7800 [0.7277,0.8323] | 1.0000 | 0.0600 |
| R | **5** | 0.9525 | 0.7913 | 0.2838 | +0.7462 [0.6923,0.8002] | 1.0000 | 0.0700 |
| H | **none** | 0.8500 | 0.7013 | 0.2562 | **+0.0000** | 0.9550 | 0.0612 |

**C2 LIVE-ACTION** — chance 0.0625.

| cmp | **T (Δ-horizon)** | A1 Δ=1 | A1 Δ=5 | A1 Δ=25 | **M(Δ=1)** | G1 | G2 |
|---|---|---|---|---|---|---|---|
| Q0 | **5** | 0.8975 [0.8577,0.9373] | 0.6813 | 0.2625 | +0.7425 [0.7016,0.7834] | 0.9350 | 0.0638 |
| Q1 | **25** | 0.7800 | 0.6175 | **0.3900** | +0.6325 [0.5845,0.6805] | 0.8588 | 0.0650 |
| Q2 | **25** | 0.6050 | 0.4225 | 0.2850 | +0.4925 [0.4345,0.5505] | 0.7425 | 0.0800 |
| R | **5** | 0.8562 | 0.6350 | 0.2525 | +0.7050 [0.6618,0.7482] | 0.9350 | 0.0600 |
| H | **none** | 0.6038 | 0.3050 | 0.1800 | **+0.0000** | 0.9200 | 0.0750 |

**THE REAL-MOTION RESULT, AND IT IS THE ONE THAT WAS RISKED.** On C2, **Q1
extends the identity horizon from Δ=5 to Δ=25** and gains **+12.75pp at Δ=25**
(0.3900 vs 0.2625) — an invariance win on motion that is neither rigid, global,
nor integer, so nothing here is forced by construction. **It pays 11.75pp at
Δ=1** (0.7800 vs 0.8975) and 11.0pp of margin. **Q2 buys nothing over Q1** on
either corpus (C2 Δ=25: 0.2850, back to Q0's level) while costing 29.3pp at Δ=1
and 25.0pp of margin — the same knee, one step earlier than on synthetic data.

**THE TWO CORPORA DISAGREE ON THE SIGN OF THE DISCRIMINATION COST, and that is a
finding about corpus statistics, not noise.** On **cartoon**, M *rises* with ρ
(0.746 → 0.766 → 0.780): the arrangement floor falls faster than the arm, so the
quotient is free. On **live-action**, M *falls* sharply (0.743 → 0.633 → 0.493).
Cel-shaded regions are locally flat and highly distinctive at the tile level;
natural photographic texture is not. **No number here should be pooled across
the two**, and any claim about "video" that quotes one of them is quoting the
easier or the harder case by accident.

**R DOES NOT TRANSFER.** Centroid registration was the efficiency winner on
synthetic rigid translation (+1 pixel of horizon at 1× compute) and it is
**worthless on real motion** — the horizon is unchanged on C2 and *worse* on C1
(5 vs Q0's 25, because R's floors rise). A single-shot registration assumes the
aperture's content translated as a body; real inter-frame change does not.

**Two mechanisms, not one.** On synthetic translation the true region *always*
achieves the max (`true_achieves_max` = 1.0000) and all loss is tie-break. On
real motion it does not: `true_achieves_max` degrades with ρ on C2
(0.9688 → 0.9225 → 0.7975), meaning a **wrong region outright BEATS** the true
one. Real motion's cost is not tie inflation — it is genuine misidentification.

---

## 3. THE GROUP, AND WHY IT WAS THE RIGHT ONE

The nuisance group quotiented is **2D integer translation, ℤ²**, argued for on
the domain in §1 of the pre-registration rather than imported from what had
worked elsewhere — because the immediately preceding rung did import, and paid.
`VISION_INK_VENTRAL_RESULTS.md` brought D4 identity-untangling from a synthetic
crossing to handwriting and it **HARMED −11.3pp at 8× the compute**: a reflected
or rotated glyph is a *different* glyph, so D4 is identity-CHANGING there.

**The choice is vindicated, and the data also shows the ink rung's failure mode
reproduced inside this one.** Translation is identity-preserving for image
regions, and quotienting it wins — *within its radius*. Outside that radius the
same mechanism turns harmful in exactly the ink rung's shape: Q3 at d=4 scores
**below** Q0, and Q2 costs C2 29.3pp at Δ=1 for nothing. **The lesson generalises
past "pick the right group" to "pick the right AMOUNT of the right group."** A
group is not a switch; its extent is a parameter, and over-quotienting a
*correct* group is as harmful as quotienting a wrong one.

**Cost is reported with benefit, as the ink rung's was.** The quotient is linear
in the orbit: Q1 9×, Q2 25×, Q3 49× the comparisons of Q0.

---

## 4. WHAT THE GRAPH IS ACTUALLY DOING — the pre-registered caveat, confirmed

**Prediction 7 was stated in advance so this could not be presented later as a
nuance. It is confirmed at the strongest possible reading:**

> `icg_max == nn_score` on **204 of 204 cells — 36 096 C3 trials and 88 000
> video trials, 124 096 of 124 096** — every comparator, every displacement,
> every Δ, both corpora, all six encodings.

So the honest description is: **at 24×24 with 6×6 apertures, a `ShapeDecode` +
`MaxOver` + `Argmax` composition over an orbit held as graph data is a
shift-tolerant nearest-neighbour classifier under Hamming distance, expressed as
graph data.** The decision is genuinely a Term, not Python — the architectural
point the seam needed — and the quotient is genuinely performed by the graph.
**It is still not a representation.** The incumbent bought no invariance at all;
this buys exactly as much as the orbit it is handed, and pays for it in ties.

This is the FM-0 distinction (§13.2) applied a second time: the mechanism
**works**, and what it is **load-bearing for** is narrower than "invariance" —
it is "search a declared neighbourhood."

---

## 5. INSTRUMENT GATES

| gate | requirement | result |
|---|---|---|
| **G1 CEILING** | reported | C1 **1.0000** for Q0/Q1/Q2/R, 0.9550 (H). C2 **0.9350** (Q0), degrading with ρ to 0.8588 (Q1) and 0.7425 (Q2). C3's ceiling is A1\|d=0 by construction: 0.7604 (Q0). |
| **G2 NOISE** | in [0.02, 0.15] | **PASSES every arm, both corpora, C3**: 0.0599–0.0833 (C3), 0.0600–0.0800 (video). |
| **G3 ALIVE** | entropy ≥ 0.50 | **PASSES every arm**: 0.979–0.986 (C3), 0.936–1.000 (video). No arm collapsed onto one answer. |
| **G4 TIES** | reported | orbit-member ties 1.00 → 3.38 → 8.08 → 14.87 (C3, ρ=0…3); region ties 3.219 → 4.391. |
| **G5 REPLAY** | reported | **6 016 rows, 0 disagreeing** (§6). |

**G1 degrades with ρ on C2 and that caveat is carried, not waived.** Q2's C2
ceiling is 0.7425, so its C2 levels are bounded by that. The horizon verdicts do
not depend on absolute level — they are CI separations against each arm's own
floor — but the *levels* inherit the bound.

**A declared bound on my own tie diagnostic.** `icg_ntied` counts tied **orbit
members**, not tied **regions**, so at ρ=0 it is 1 by construction and carries no
information. The region-level tie count (§2.3) comes from the outside-the-graph
reference column and is the one that diagnoses the ceiling. I pre-registered
`icg_ntied` as "the load-bearing diagnostic" and it is only half of one; the
honest form is stated here rather than quietly substituted.

---

## 6. DETERMINISM — the incumbent's §4.2 risk did NOT recur

The incumbent found 272 rows produced by an `Argmax`/`Eq` disagreement inside
`ShapeDecode` that **did not reproduce**, and named it as a live risk to any
number this arc takes. It was not fixed here (that needs its own
pre-registration), so it was **measured** instead.

- **Explicit replay**, fresh process, all six comparators over a fixed C3
  subset: **6 016 rows compared, 0 disagreeing.**
- **Cross-process reproduction at full scale** (§1): the accidental full run and
  the confirmatory run agree on Q0/Q1/R/H.
- **204 of 204 cells** show exact score agreement with an independently computed
  reference (§4), which would break loudly on any evaluator inconsistency.

**No evidence of non-determinism in this rung's 124 096 trials.** That does not
retract the incumbent's finding — a defect that appears in 0.73% of one base
frame's rows can hide in this sample — but it is the strongest replay evidence
the arc has, and it is reported as a null.

---

## 7. MY PREDICTIONS, SCORED (§3.7)

| # | prediction | outcome |
|---|---|---|
| 1 | Q0 reproduces the incumbent: T=1, acc(d=0) ≈ 0.89 | **HALF RIGHT.** T=1 **exactly reproduced** — independent implementation, different engine, stricter photo-level statistic. The **level was wrong**: 0.7604 photo-level / 0.7604 trial-level vs the incumbent's 0.8906 on 12 photos. A different, larger photo set. |
| 2 | `T(Qρ) = ρ` for ρ ∈ {1,2,3} | **WRONG.** Measured **ρ+1** at ρ=1,2 (partial overlap gives a free step) and **ρ** at ρ=3 (distractor inflation destroys it). T **saturates at 3**. The error was informative: I had not seen that the orbit's harm scales with its size. |
| 3 | M falls monotonically, does not collapse by ρ=3; conjunction satisfied | **RIGHT on C3** (0.578→0.531→0.492→0.438, every CI excluding 0), levels ~0.1 too high throughout. **WRONG on C1**, where M *rises* with ρ. I did not anticipate the sign flipping by corpus. |
| 4 | R FAILS — no better than the incumbent | **WRONG on synthetic, RIGHT on real.** R reached T=2 on C3 at **zero** discrimination cost at d=0 and 1× compute (it is provably identical to Q0 at d=0, since registering identical tiles is a no-op). But on real motion it is worthless — horizon unchanged on C2, *worse* on C1. My reasoning (coarse centroid, truncation) was right about the mechanism and wrong about where it would bite. |
| 5 | H flat in d, `M(H) = 0.0000` EXACTLY | **RIGHT, exactly**, at every displacement and both corpora. |
| 6 | Video two-sided: Q1/Q2 raise A1 at Δ=25; horizon moves at most one step on C2 | **PARTLY.** Q1 gained on both (C2 +12.75pp, real; C1 +4.1pp, CIs overlapping); **Q2 gained on neither**, which I did not predict. The C2 horizon moved **5 → 25**, further than "at most one step". |
| 7 | Score agreement ≥ 0.99 | **RIGHT, and stronger**: 1.0000 on 204/204 cells, 124 096/124 096 trials. |
| 8 | mean `icg_ntied` rises with ρ | **RIGHT** (C3 1.00→3.38→8.08→14.87; C2 1.00→2.17→4.83). |

**Four right, two wrong, two partly.** Both outright errors (2 and 4) were about
**where the orbit's harm comes from** — I modelled the benefit correctly and the
cost badly. The prediction I most wanted to be right about (7) was right, and it
is again the one that most constrains what may be claimed.

---

## 8. BOUNDS ON EVERYTHING ABOVE (§8)

- **Toy resolution only.** 24×24 frames, 6×6 apertures. **Nothing here is a
  claim about video at any real resolution.** The video probe's measured scale
  wall (O(N^1.887)) is untouched, and the quotient multiplies cost by (2ρ+1)².
- **Nothing was learned.** The codebook is one frame's regions, held for one
  comparison and discarded. No training, no accumulation, no codebook growth.
  **This measures a COMPARISON, not "learning by watching video."**
- **Fixed aperture, not tracking.** No object correspondence, no segmentation,
  no proto-objects, no border-ownership.
- **The C3 invariance for d ≤ ρ was FORCED BY CONSTRUCTION** and declared as such
  in advance (§2.1 of the prereg). The risked quantities were the discrimination
  cost, real video, and the ties — all three delivered results, and §2.5 is the
  part of this rung that took a genuine risk.
- **Two hand-set numbers parameterise the whole measurement** (k=4, 6×6 tiling),
  inherited unchanged from the incumbent for comparability. Neither falls out of
  anything (§13); neither was swept here. **The knee at ρ=2 is conditional on
  the 6-pixel tiling pitch** and would move with it.
- **The content bound was declared in advance and bit exactly where predicted:**
  a 6×6 aperture retains (6−d)/6 of its content under axis displacement, so no
  comparator can have a horizon of 6, and every d≥4 number sits against a third
  or less of the original content.
- **Two episodes and 24 photographs.** Not a survey. Cartoon and
  natural-photographic statistics differ enough to **flip the sign of the
  discrimination cost**, and are never pooled here.
- **Q3 was not run on video** — a declared cost bound, not a result.
- **G1 degrades with ρ on C2** (0.9350 → 0.7425), and C2's absolute levels
  inherit that ceiling.
- **`icg_ntied` measures orbit ties, not region ties** (§5) — a bound on my own
  diagnostic, found while reading the data and reported rather than substituted.
- **§9:** no default moved, no committed seed edited, no rule changed, no Rust
  touched. The seed ships `invcomp = 0.0` and is not boot-loaded.

---

## 9. VERIFICATION

| check | result |
|---|---|
| `bash scripts/rung7_vision_bench.sh` **before** any file was added | **200 passed, 0 failed, exit 0** (130.6 s) |
| `bash scripts/rung7_vision_bench.sh` **after** | **200 passed, 0 failed, exit 0** (129.6 s) |
| sd orbit law `{2:1, 3:2, 4:2, 6:2, 12:4}` (`tests/test_sdloop_vision_migrated.py`) | **unmoved**, before and after |
| this rung's gate `tests/test_invariant_comparator_migrated.py` | **26 passed** (22 + 4 provenance once pinned) |
| `tests/test_provenance_endpoint_guard_migrated.py` + sd orbit + this gate | **641 passed** |
| replay determinism | **6 016 rows, 0 disagreeing** |

*(The bench's 200/0 is quoted with its condition, per §10.2: it is 200/0 **with**
`data/` symlinked, which it was throughout — 190/10 without.)*

**The gate is positive-controlled red-then-green on the MECHANISM.** Replacing
the member-level `Argmax` with `Argmin` — the held region that explains the
observation *worst* — is loaded from a modified manifest and the ceiling control
goes red; restoring gives green. The inversion is asserted to have applied
(exactly one site), so an inert control cannot masquerade as a passing one.

**And the PROVENANCE gate proved itself alive by catching two real defects of
mine, which is better evidence than an injected one.** (1) I first pinned the
diff range to the **pre-registration** commit, but the seed and adapter landed
*with* the prereg so the range excluded them — the no-foreign-seed test asserted
an empty diff and **failed**. (2) With the range corrected to the branch base,
the ownership test **failed again** on `scripts/invariant_comparator_report.py`,
written after the OWNED list. **Both were fixed only after auditing the real
diff term by term** (11 files, every one owned, zero `.rs`, zero `Cargo.toml`) —
§12.3's order: *verify the fact, then fix the gate, never the reverse.* Both
endpoints are fixed shas throughout; `HEAD` appears only in a `merge-base
--is-ancestor` reachability check, which is a question about now and correctly
resolves against the moving branch.

**The audited range and what lies outside it, stated so the claim terminates.**
The gates audit **`eb403264..ec992799`** — the branch base to the results
commit — which contains **all** of this rung's substantive content: the
pre-registration, the seed, the adapter, the runner, the reporter, the gate, the
three pinned result files and the protocol ledger row. Exactly two commits
follow and they are named here rather than left to a gate that would have to
re-pin itself forever: **`6858b996`**, which pins `RUNG_SHA` into this gate and
adds §9 above, and the commit carrying this paragraph. Both touch only
`tests/test_invariant_comparator_migrated.py` and this file. **No Rust, no seed,
no result file, no other rung's anything, in either.**

---

## 10. WHAT I WOULD PRE-REGISTER NEXT

**The measured bottleneck is no longer invariance — it is the TIE CEILING.**
`true_achieves_max = 1.0000` at every radius on C3 says the comparator's scoring
is not the limit; its **resolution** is. Roughly 28% of probes have ≥2 regions
tied at the maximum before any quotient is applied, rising to 53% at ρ=3, and
*every* error is one of those ties broken arbitrarily. **A comparator that could
break ties would gain more than any further widening of the group** — and this
is precisely where the arc's own measured synthesis applies: *bins propose,
continuous decides*. The orbit is a good proposer; `covered_count` over a k=4
lattice is a weak verdict, exactly as strict multiset matching was on Omniglot
before SC+TPS gave +51.5pp. **The next pre-registration should hold the orbit
fixed at ρ=2 (the measured knee) and vary only the VERDICT**, with the tie rate
as the primary statistic and the same conjunctive gate.

Named and *not* done here, so they are not confused with results: whether the
knee moves with the tiling pitch (it should, and that is a §13 prediction with a
derivation); whether an orbit whose radius is chosen per-probe from local motion
beats a fixed radius; and whether any of this survives above toy resolution.
