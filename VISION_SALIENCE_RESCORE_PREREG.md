# DOES MISIDENTIFICATION LIVE IN LOW-SALIENCE REGIONS? — PRE-REGISTRATION

*Committed BEFORE any headline number is computed. Seeds **58000–58999**
(verified free; ledger high-water 57999). Branch
`gamma-substrate/vision-salience-rescore`.*

---

## 0. THE QUESTION AND WHY IT IS WORTH A RUNG

`VISION_INVARIANT_COMPARATOR_RESULTS.md` §2.5 established **two mechanisms**,
not one. On synthetic translation (C3) at d=0 the true region *always* attains
the maximum score and every error is an arbitrary tie-break. On **real motion**
it does not: on C2 (live-action), `true_achieves_max` on the A1|Δ=1 arm degrades
**0.9688 → 0.9225 → 0.7975** across Q0/Q1/Q2 — a wrong region **outright beats**
the true one. That is genuine misidentification.

**The hypothesis under test:** misidentification is concentrated in
**LOW-SALIENCE** regions, and therefore costs much less than the flat rate
suggests. Mistaking background curtains while attending to a phone is harmless;
error matters only where salience is high.

**If true**, the flat ~20% overstates the defect and the next rung should not be
aimed at it. **If false**, the verdict problem is real at its flat size. **If
inverted**, it is worse than it looks.

---

## 1. THE CRUX: WHY THIS SALIENCE MEASURE IS INDEPENDENT OF THE COMPARATOR

**The hazard, stated first so the design can be judged against it.** If salience
were derived from the features or scores the comparator uses, the finding
"errors live in low-salience regions" would be circular and worthless — a
restatement of "errors live where the comparator scores weakly."

**The measure: `csal`, the graph-resident cone-opponent surround-relative
contrast** computed by the committed seed rule `cc_contrast`
(`seeds/vision_colour.json`, the 34000-block COLOUR SALIENCE rung, unchanged).
Per cell it is the Euclidean distance, in opponent space `(L−M, S−(L+M))`, of
the cell from its 4-adjacent surround mean.

**Independence rests on three legs, of which the first is decisive:**

1. **CHROMA IS ABSENT FROM THE COMPARATOR'S INPUT BY CONSTRUCTION.** The
   comparator's frames are decoded `f.to_ndarray(format="gray")`
   (`scripts/video_probe_measure.py::jellyfin_frames`). Chroma is discarded by
   the *decoder*, before the comparator receives anything. `csal` is a function
   of `L−M` and `S−(L+M)`, both **identically zero on any greyscale input**.
   There is therefore **no function of the comparator's input that computes
   `csal`** — the independence is not a matter of degree or of feature choice,
   it is a matter of the information not being present. This is stronger than
   "a different feature of the same signal."
2. **The measure's own gated result is orthogonality to luminance.** The 34000
   rung's headline is that a **near-equiluminant** target pops out via `csal`
   where luminance salience `lsal` is **exactly 0**.
3. **Provenance: I cannot tune it.** `csal` is computed by a committed seed rule
   under `run_rules`, not by a Python heuristic authored in this rung. It has
   **no free parameters**. I supply cone triples (mechanical ingest, exactly as
   the rung supplies luminance) and read `csal` back.

**THE RESIDUAL I DECLARE IN ADVANCE, because it is real and is not the
circularity above.** Chroma and luminance are *statistically correlated in
natural images*: a coloured object usually also carries a luminance edge. So an
association between `csal` and error could be **mediated** by luminance
structure the comparator does see. That is a mediation caveat, not circularity —
it cannot manufacture the association from the comparator's own scores. To bound
it I will report, as an **explicitly CONFOUNDED secondary**, `lsal` — the
achromatic salience computed by the *same* seed rule from `L+M`. `lsal` **IS** a
function of the comparator's input and **must not be read as an independent
test**; it is reported only to show how the two channels compare.

**A stated risk to this measure's POWER, recorded before the result.** Measured
on the regenerated frames, the two corpora differ sharply in how chromatic they
are: sd(R−G) = **40.33** on C1 (cartoon) but only **8.69** on C2 (live-action).
C2 — the corpus where the misidentification finding actually lives — is the
**weakly chromatic** one. If C2 returns a null, "the measure had little chroma
to work with there" is a live alternative to "salience does not explain the
tail," and I will say so rather than claim a clean null.

---

## 2. INSTRUMENT — and its reproduction check, already passed

`scripts/salience_rescore_frames.py` re-decodes the same Jellyfin episodes with
the committed constants (n=150, every=2, start_s=300, size=24, episode_index
C1=0 / C2=3), keeping **grey** (to verify reproduction) and **rgb24** (the new
channel).

**REPRODUCTION VERIFIED BEFORE THIS COMMIT:** the committed motion statistic,
recomputed from the regenerated grey frames, matches
`results/invariant_comparator_video.json` **exactly, to the last bit**, on both
corpora (C1 mean `2.889526879907482`, sd `10.064604294365187`, min
`0.004360318183898926`, max `52.34345685659597`; C2 mean `3.1821214667293765`,
sd `6.040506321896707`, min `0.28368019726541305`, max `44.754071182674835`).
The frames analysed here **are** the frames the comparator scored. Catalogue
unchanged (46 series, as recorded).

**Cone ingest (zero free parameters).** For each of the 16 comparator regions of
a base frame, `cL,cM,cS` = the mean of the R,G,B channels over that region's 6×6
tile, **rounded to integer** (the frame/continuum invariant: an in-frame
coordinate is integer; the continuous magnitude appears only in the
cross-cell comparison `csal` computes). R,G,B → L,M,S is the standard
first-order long/medium/short-wavelength proxy and introduces **no constant**.
A proper Hunt-Pointer-Estevez matrix is pre-registered as a **declared
robustness variant** carrying the same outcome rule, so it cannot serve as a
rescue.

**Grid.** The 16 regions form a 4×4 grid; `colour_world.add_field` wires
4-adjacency, so `csal` is each region's chromatic contrast **against its
neighbouring regions** — salience at exactly the comparator's own unit.

**Salience is taken from the BASE frame** (frame `t`, which holds the codebook
and which `truth` indexes). Probe-frame salience is a named, unrun variant.

---

## 3. ANALYSIS PLAN — fixed here

**Rows.** `A1` arm only (the true probe = the identity task), Δ ∈ {1, 5, 25},
comparators Q0/Q1/Q2, corpora C1 and C2 **reported separately and never
pooled** (§2.5 of the source: the two corpora disagree on the sign of the
discrimination cost).

**Three outcomes per trial, kept separate and NEVER pooled:**

| label | definition |
|---|---|
| **MISID** | `true_is_max == False` — a wrong region outright beats the true one |
| **TIEBREAK** | `true_is_max == True` **and** `said_idx != truth` |
| **CORRECT** | `said_idx == truth` |

**Unit of analysis: the trial, CLUSTERED BY BASE FRAME.** The 16 regions of one
base frame share content and are not independent — the same reason the source
rung used the base frame as its unit. All CIs are **95% percentile intervals
from a cluster bootstrap that resamples the 50 base frames with replacement**
(10 000 draws; RNG seeded from block 58000–58999). Resampling frames carries all
of their rows, which correctly handles the reuse of a region across comparators
and Δ.

**Stratification: WITHIN-FRAME salience terciles.** Within each base frame, rank
its 16 regions by `csal` (ties broken by region index, deterministic) and split
**LOW = ranks 0–4 (5 regions), MID = ranks 5–10 (6), HIGH = ranks 11–15 (5)** —
the 5/6/5 split falls out of 16/3 and is not a chosen threshold. Within-frame
ranking is used so that the contrast is about **where in the frame** attention
would go — the actual hypothesis — and so frame-level differences in overall
colourfulness cannot drive it.

**PRIMARY STATISTIC:**

> **Δ_sal = MISID_rate(HIGH) − MISID_rate(LOW)**, per corpus, with a 95%
> cluster-bootstrap CI; reported per (comparator, Δ) cell **and** pooled over
> cells within a corpus.

**PRE-REGISTERED VERDICT RULE — applied mechanically, no exceptions:**

1. **CONCENTRATED IN LOW SALIENCE** iff **Δ_sal < 0 and its 95% CI excludes 0.**
   Then additionally report the **salience-weighted MISID rate** (weights =
   within-frame `csal` normalised to mean 1) against the flat rate, and state
   the factor by which the flat number overstates the cost.
2. **UNIFORM — THE NULL** iff **the CI includes 0.** Reported as a full result.
   The verdict problem stands at its flat size. It will **not** be rescued by
   re-stratifying, re-binning, switching to the confounded `lsal`, or dropping
   cells (§5).
3. **CONCENTRATED IN HIGH SALIENCE** iff **Δ_sal > 0 and CI excludes 0.** The
   most consequential outcome; would say the verdict problem is worse than flat.

**TIEBREAK is analysed with the identical machinery and reported separately.**
It is a different mechanism and pooling the two is forbidden.

**NEGATIVE CONTROL — and a CORRECTION to the framing I was given.** I was told
C3 "never" misidentifies. That is **false as stated**: `true_achieves_max` is
1.0000 on C3 only **at d=0**; at d>0 C3 has many misidentifications (Q0: 4288 of
8064 rows). The zero-misidentification control is therefore **C3 at d=0
specifically**, which I will verify from the rows directly (MISID count must be
exactly 0). **C3 colour salience is INFEASIBLE** — BSDS300 is not present in
this environment — and is declared a bound, not attempted.

**SECONDARY, same data: ADJACENCY.** For each MISID row, is `said_idx` adjacent
to `truth` on the 4×4 region grid? Reported as (a) 4-adjacency rate, (b)
8-adjacency rate, (c) mean Chebyshev distance. **The chance baseline is derived
from the actual grid geometry**, not assumed uniform, because corner and edge
regions have fewer neighbours: for each observed `truth` region, chance =
(its neighbour count)/15, averaged over the observed truth distribution. CI by
the same cluster bootstrap on the observed−chance difference. Adjacent-and-
similar suggests a resolution floor; scattered suggests the comparator keys on
something misleading.

---

## 4. PREDICTIONS (§3.7) — to be scored

1. **C1 shows a NEGATIVE Δ_sal with CI excluding 0** (misidentification
   concentrated in low salience). C1 is strongly chromatic and cel-shaded; flat
   background regions are both low-chroma-contrast and locally indistinctive.
   Confidence: moderate.
2. **C2 returns the NULL** (CI includes 0). C2's chroma is weak (sd(R−G)=8.69)
   and natural photographic texture is not organised the way cel-shading is.
   Confidence: moderate. **This is the corpus that matters**, so I expect the
   headline to be a null on the case of interest and a positive on the easier
   one — the least convenient combination, which is why I am recording it.
3. **The magnitude, where non-null, will be modest** — |Δ_sal| < 0.15. I do not
   expect salience to explain most of the tail.
4. **TIEBREAK will be flatter in salience than MISID** on both corpora. A
   tie-break is an identifiability limit of the k=4 lattice, which has no reason
   to respect chroma.
5. **Adjacency will EXCEED its geometric chance rate** on both corpora — wrong
   winners will be spatially near the true region, indicating a resolution
   floor rather than a misleading key. Confidence: moderate-high.
6. **`lsal` (confounded secondary) will show a LARGER negative Δ_sal than
   `csal`** on both corpora, precisely because it is confounded with what the
   comparator sees. If `csal` and `lsal` agree in sign and size, that is weak
   evidence the mediation caveat of §1 is biting.

---

## 5. BOUNDS DECLARED IN ADVANCE (§8)

- **Toy resolution.** 24×24 frames, 6×6 regions, 4×4 salience grid. Nothing here
  is a claim about video at any real resolution.
- **Two episodes.** One cartoon, one live-action nature documentary. Not a
  survey; the source rung already showed corpus statistics flip the sign of the
  discrimination cost, so no number here may be pooled across corpora.
- **Salience at region grain only.** A 4×4 grid of 6×6 tiles cannot express
  object-level salience. There is no objecthood, no segmentation, no tracking in
  this instrument — "the phone versus the curtains" is being approximated by
  "this sixth of the frame is chromatically distinct from its neighbours."
  **This is the weakest link in the whole design and no result should be read
  past it.**
- **`csal` is a WHERE-to-look proxy, not attention.** The arc's stream rung
  orders a budget by salience; nothing here shows a viewer would attend there.
- **C2's weak chroma bounds the power of the primary measure on the corpus of
  interest** (§1).
- **Mediation, not circularity** (§1): a `csal`–error association may run through
  luminance structure. Declared, not eliminated.
- **C3 has no colour salience here** (BSDS300 absent); its role is the d=0
  zero-misidentification control only.
- **Nothing is learned, nothing is trained.** This is a re-scoring of preserved
  rows plus a salience field computed by an unchanged seed.
- **§9:** no default moves, no committed seed is edited, no rule is changed, no
  Rust is touched. `vision_colour` and `vision_stream` are loaded by this
  rung's own script with their flags written blind by the existing adapter; they
  remain OFF by default and not boot-loaded.

---

## 6. WHAT WOULD MAKE ME WRONG

- If MISID rates are identical across terciles on **both** corpora, the
  hypothesis is dead and the flat number is the honest number.
- If Δ_sal is **positive** with a CI excluding 0 on either corpus, the
  benign-error story is not merely unsupported but inverted, and that becomes
  the headline regardless of what the other corpus does.
- If the adjacency rate sits **at** its geometric chance rate, "resolution
  floor" is unsupported and the comparator is keying on something that does not
  respect space.
