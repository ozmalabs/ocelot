# DOES MISIDENTIFICATION LIVE IN LOW-SALIENCE REGIONS? — RESULTS

*Pre-registration: `VISION_SALIENCE_RESCORE_PREREG.md`, committed BEFORE any
headline number at **`fc9215cb95c2cf7eccb3751e96a8d02c0ee53b39`** (branch base
**`e0b0d0e7c0640a5b75cde323d75504e575a4556a`**).*

**Engine (§10):** `985fb252ce41cb23145dec79e382894f87e0cf910ffff88f0e79ca3582caa782`
@ `runners/dsl/python/substrate_rs/_native.abi3.so` — this rung's OWN pinned
copy, installed with `cp --remove-destination` and hashed at source and
destination (identical). Rust source verified byte-identical to the canonical
tree's (sole difference: an untracked `py.rs.selfmod.bak`, not compiled).
**This rung adds no Rust, no Term, no seed and no constant.**
**Selector:** `scripts/salience_rescore_frames.py` (frame regeneration) +
`scripts/salience_rescore_field.py` (salience field, computed by the seed) +
`scripts/salience_rescore_analyse.py` (pre-registered analysis) +
`scripts/salience_rescore_diagnose.py` (the post-hoc diagnostic of §4).
**Raw:** `results/salience_rescore.json`, `results/salience_rescore_field.json`,
`results/salience_rescore_diagnose.json`.
**Seeds:** block **58000–58999**; **58000 only**, and only as the cluster-
bootstrap RNG seed. No seed outside the block was drawn.

**INPUT PROVENANCE.** The 16 preserved per-trial row files of the
invariant-comparator rung (merged `ea09d9fd`), which were never committed.
**All 16 checksums verified OK before use and again after** against
`SHA256SUMS.txt` (itself
`04064bfd720558bce9bf5094d307be44aaf3ea8596af7b814609235036a2137e`).

---

## 0. THE HEADLINE, IN ONE PARAGRAPH

**The hypothesis is not supported, and the reason is more interesting than the
hypothesis.** On **C2 (live-action) — the corpus where genuine misidentification
actually lives — the pre-registered test returns the NULL**: Δ_sal = **+0.0240
[−0.0044, +0.0547]**, CI including 0, with the point estimate pointing the
*wrong way* for the benign-error story. On **C1 (cartoon)** the effect is
**CI-separated but negligible**: Δ_sal = **−0.0164 [−0.0276, −0.0049]** on a
flat rate of 0.3162 — re-weighting every trial by salience moves the error rate
from **0.3162 to 0.3149**, i.e. the flat number overstates the cost by a factor
of **1.004**. **Salience does not explain the tail on either corpus in any
amount that matters, and the next rung should not be aimed at it.** The
diagnosis, found by chasing a zero-width CI rather than by design: **at short Δ,
misidentification is not a REGION property at all — it is a FRAME event.** All
31 of C1/Q0's Δ=1 errors fall in **2 base frames of 50**, in which **every one of
the 16 regions failed at once**; per-frame error count correlates with per-frame
motion magnitude at **r = +0.987**, and **100%** of those errors sit in the
top-10% highest-motion frames (chance 10%). A within-frame salience measure
cannot explain a between-frame failure, and the null is exactly what that
predicts. One genuine asymmetry did appear and it is the opposite of what I
predicted: on C2 the **TIE-BREAK** mechanism *is* strongly salience-graded
(Δ_sal = **−0.0991 [−0.1289, −0.0707]**, HIGH 0.0436 vs LOW 0.1427) while
**misidentification is not** — so salience rescues the mechanism that was
already known to be arbitrary, and not the one that motivated the rung.

---

## 1. THE INDEPENDENCE ARGUMENT, AND WHY IT HOLDS

The crux hazard was circularity: a salience measure derived from the
comparator's own features or scores would trivially "discover" that errors live
where the comparator scores weakly.

**The measure is `csal`** — the Euclidean opponent-space distance of
`(L−M, S−(L+M))` from its 4-adjacent surround mean, computed by the **unchanged
seed rule `cc_contrast`** (`seeds/vision_colour.json`, the 34000-block rung).

**It is independent because chroma is absent from the comparator's input by
construction.** The comparator's frames are decoded
`f.to_ndarray(format="gray")`; chroma is discarded by the *decoder*, before the
comparator receives anything. `csal` is a function of `L−M` and `S−(L+M)`, both
**identically zero on any greyscale input**. There is therefore no function of
the comparator's input that computes `csal`. This is not "a different feature of
the same signal" — the information is **not present**. Two supporting legs: the
34000 rung's own gated result is that `csal` pops out a near-equiluminant target
where luminance salience is *exactly* 0; and `csal` is computed by a committed
seed rule with **no free parameters**, so I could not tune it toward a result.

**THE DECLARED MEDIATION RESIDUAL DID NOT BITE, and this is testable rather than
asserted.** Chroma and luminance are correlated in natural images, so a
`csal`–error association could in principle run through luminance structure the
comparator *does* see. I pre-registered `lsal` (the achromatic salience from the
*same* seed rule) as an explicitly CONFOUNDED secondary, and predicted it would
show a **larger** effect than `csal` if mediation were driving things. **It did
not.** On C1, `lsal` gives −0.0142 [−0.0244, −0.0040] against `csal`'s −0.0164 —
*smaller*. On C2, `lsal` gives −0.0129 [−0.0431, +0.0178], a null, against
`csal`'s null. The channel that *is* confounded with the comparator's input
carries no more signal than the channel that cannot be.

**The measure is not degenerate.** Per base frame the 16 regions take a mean of
**16.0** distinct `csal` values on C1 and **15.9** on C2 (min 15), with mean
within-frame spread **76.0** (C1) and **42.3** (C2) — so the tercile split is a
real ranking, not disguised tie-breaking by region index.

**The stated power risk was real but did not disable the measure.** C2 is the
weakly chromatic corpus (sd(R−G) = 8.69 vs C1's 40.33), and its `csal` is
correspondingly weaker (mean 16.7 vs 31.2). It nonetheless produced a
CI-separated result on the TIEBREAK mechanism (§3), which is direct evidence
that the measure had enough signal on C2 to detect a real salience gradient when
one existed. **The MISID null on C2 is therefore not simply "the instrument was
blind there."**

---

## 2. INSTRUMENT — REPRODUCTION IS EXACT

The frames were regenerated from Jellyfin with the committed constants (n=150,
every=2, start_s=300, size=24, episode_index C1=0 / C2=3; catalogue unchanged at
46 series). The committed motion statistic, recomputed from the regenerated grey
frames, **matches `results/invariant_comparator_video.json` to the last bit on
both corpora**:

| | mean | sd | min | max |
|---|---|---|---|---|
| C1 | `2.889526879907482` | `10.064604294365187` | `0.004360318183898926` | `52.34345685659597` |
| C2 | `3.1821214667293765` | `6.040506321896707` | `0.28368019726541305` | `44.754071182674835` |

**The frames analysed here ARE the frames the comparator scored.** (A first pass
differed in the 8th significant figure; the cause was found and is instructive —
the committed runner casts each frame to float64 via `np.asarray(f, float)`
*before* differencing, and I was differencing the float32 stack. Matching the
cast made it exact. A near-match was not accepted as a match.)

Cone ingest carries **zero free parameters**: per region, `cL,cM,cS` = the
integer-rounded mean of R,G,B over that region's 6×6 tile (the in-frame
coordinate stays integer per the frame/continuum invariant; the continuous
magnitude appears only in the cross-cell comparison `csal` computes). The
pre-registered **Hunt-Pointer-Estevez robustness variant agrees throughout**
(C1 MISID −0.0213 [−0.0347, −0.0080]; C2 MISID +0.0151 [−0.0120, +0.0427]) —
same signs, same verdicts, so no result here turns on the RGB→LMS proxy.

---

## 3. THE PRE-REGISTERED VERDICT, APPLIED MECHANICALLY

Unit: the trial, **clustered by base frame** (the 16 regions of a frame share
content and are not independent). All CIs are 95% percentile intervals from a
cluster bootstrap resampling the 50 base frames with replacement, 10 000 draws,
seed 58000. Pooled over Q0/Q1/Q2 and Δ ∈ {1,5,25}; **corpora never pooled.**

### 3.1 PRIMARY — `csal`, MISID (`true_is_max == False`)

| corpus | LOW | MID | HIGH | flat | **Δ_sal = HIGH − LOW** | **VERDICT** |
|---|---|---|---|---|---|---|
| **C1** cartoon | 0.3271 | 0.3119 | 0.3107 | 0.3162 | **−0.0164 [−0.0276, −0.0049]** | **(1) LOW-concentrated — CI excludes 0** |
| **C2** live-action | 0.3196 | 0.3615 | 0.3436 | 0.3428 | **+0.0240 [−0.0044, +0.0547]** | **(2) THE NULL — CI includes 0** |

**C1 satisfies outcome 1, and the pre-registered follow-up shows the win is
negligible.** The salience-weighted MISID rate (weights = within-frame `csal`
normalised to mean 1) is **0.3149 [0.2544, 0.3791]** against a flat
**0.3162**. **The flat number overstates the cost by a factor of 1.004 — 0.13
percentage points.** A statistically real effect that is practically nothing;
reporting it as "misidentification is concentrated in low-salience regions"
without the magnitude would be true and misleading.

**C2 returns the NULL, on the corpus that motivated the rung.** Per §5 it is not
rescued: not by re-stratifying, not by switching to `lsal`, not by dropping
cells. Its salience-weighted rate is **0.3474** against a flat **0.3428** —
weighting by salience makes C2 look *slightly worse*, not better.

### 3.2 THE ASYMMETRY I DID NOT PREDICT — TIEBREAK is salience-graded, MISID is not

| corpus | mechanism | LOW | HIGH | **Δ_sal** |
|---|---|---|---|---|
| C1 | TIEBREAK | 0.0102 | 0.0058 | −0.0044 [−0.0107, +0.0027] (null) |
| **C2** | **TIEBREAK** | **0.1427** | **0.0436** | **−0.0991 [−0.1289, −0.0707]** |
| C2 | MISID | 0.3196 | 0.3436 | +0.0240 [−0.0044, +0.0547] (null) |

**On C2 the two mechanisms have opposite salience signatures, and only the
already-benign one is graded.** Tie-break loss is **3.3× more common in the
lowest-salience third than the highest** — flat, low-chroma-contrast regions are
exactly where the k=4 lattice collapses distinctions, so ties concentrate there.
**Genuine misidentification does not follow that pattern at all.** So the
"harmless background curtains" intuition is *correct about ties and wrong about
misidentification* — and it is misidentification that the source rung flagged as
the real-motion cost.

### 3.3 PER-CELL — the two corpora take OPPOSITE SIGNS where power is greatest

`csal`, MISID, Δ_sal per (comparator, Δ). Cells are **not** multiplicity-
corrected: 18 cells at 5% would yield ~1 false positive by chance, so single
starred cells are weak evidence and are reported for shape, not for verdicts.

| cell | C1 | C2 |
|---|---|---|
| Q0 d1 | +0.0000 [0, 0] (see §4) | −0.0040 [−0.0240, +0.0160] |
| Q0 d5 | +0.0040 [−0.0160, +0.0280] | +0.0240 [−0.0360, +0.0840] |
| **Q0 d25** | **−0.0720 [−0.1200, −0.0240]** | **+0.0880 [+0.0320, +0.1440]** |
| Q1 d1 | −0.0040 [−0.0120, +0.0000] | +0.0280 [−0.0160, +0.0760] |
| Q1 d5 | −0.0120 [−0.0320, +0.0080] | +0.0240 [−0.0400, +0.0880] |
| **Q1 d25** | **−0.0360 [−0.0600, −0.0160]** | **+0.0840 [+0.0320, +0.1360]** |
| Q2 d1 | −0.0200 [−0.0400, −0.0040] | +0.0000 [−0.0680, +0.0680] |
| Q2 d5 | −0.0080 [−0.0280, +0.0120] | −0.0560 [−0.1280, +0.0160] |
| Q2 d25 | +0.0000 [−0.0400, +0.0400] | +0.0280 [−0.0480, +0.1000] |

**At Δ=25 — the best-powered cells, ~500 errors each — C1 is CI-separated
NEGATIVE and C2 is CI-separated POSITIVE.** The corpora do not merely differ in
magnitude; they differ in **sign**, in the same cells, with non-overlapping
intervals. This independently reproduces the source rung's warning that cartoon
and natural-photographic statistics may not be pooled, now on a second axis.
**On C2 at long Δ, misidentification is if anything concentrated in HIGH-salience
regions** — a local instance of outcome 3, which is why the pooled C2 point
estimate leans positive.

### 3.4 NEGATIVE CONTROL — C3 at d=0

| | Q0 | Q1 | Q2 | Q3 | R | H |
|---|---|---|---|---|---|---|
| n | 384 | 384 | 384 | 384 | 384 | 384 |
| **MISID** | **0** | **0** | **0** | **0** | **0** | **0** |
| TIEBREAK | 92 | 115 | 143 | 163 | 92 | 109 |

**Zero misidentification for every comparator, exactly as construction demands**,
with all loss as tie-break. The control behaves.

**A CORRECTION TO THE FRAMING THIS RUNG WAS GIVEN, recorded in the
pre-registration before any result.** I was told C3 "never" misidentifies. That
is false as stated: `true_achieves_max` is 1.0000 on C3 only **at d=0**. At d>0
C3 misidentifies heavily (Q0: **4288 of 8064** rows). The zero-misid control is
d=0 specifically, and that is how it is used here.

---

## 4. THE DIAGNOSIS — WHY THE NULL, AND IT IS A FRAME EFFECT

**NOT PRE-REGISTERED. Labelled post-hoc throughout.** It was found by refusing
to accept an anomaly: the C1/Q0/Δ=1 cell reported Δ_sal = +0.0000 with a
**zero-width CI**, which is an instrument smell. §12.3's order is verify the
fact, then decide what it means. An independent reimplementation reproduced it
exactly (10 000 draws, sd = 0, 100% of draws exactly 0), so it was not a bug —
and the reason is the finding.

**All 31 misidentifications in that cell come from 2 base frames of 50**, and in
those frames **every region failed at once** (base 34: 16 of 16; base 47: 15 of
16). With per-frame HIGH and LOW error counts equal in every contributing frame,
every bootstrap draw yields exactly 0. **A zero-width interval was the data
saying the failure unit is not the region.**

Generalised across all cells (`results/salience_rescore_diagnose.json`):

| cell | n_misid | frames with any error | frames where ALL 16 failed | share of errors in top-5 frames | Gini over frames | **r with frame motion** | share in top-10% motion frames |
|---|---|---|---|---|---|---|---|
| C1/Q0/**d1** | 31 | **2** | 1 | **1.000** | **0.961** | **+0.987** | **1.000** |
| C1/Q1/d1 | 31 | 3 | 1 | 1.000 | 0.958 | +0.986 | 1.000 |
| C1/Q2/d1 | 44 | 13 | 1 | 0.818 | 0.892 | +0.993 | 0.795 |
| C1/Q0/d5 | 161 | 14 | 4 | 0.491 | 0.792 | — | — |
| C1/Q0/d25 | 576 | 40 | 10 | 0.139 | 0.252 | — | — |
| C2/Q0/**d1** | 25 | 10 | 0 | **0.800** | **0.903** | **+0.968** | **0.680** |
| C2/Q1/d1 | 62 | 33 | 0 | 0.403 | 0.578 | +0.895 | 0.323 |
| C2/Q2/d1 | 162 | 47 | 0 | 0.259 | 0.386 | +0.676 | 0.210 |
| C2/Q0/d25 | 529 | 50 | 0 | 0.142 | 0.217 | — | — |

**At Δ=1 — the regime where identity should hold, and the arm whose degradation
(0.9688 → 0.9225 → 0.7975) motivated this rung — misidentification is a
BETWEEN-FRAME event.** Error count per frame tracks that frame's motion
magnitude at **r = +0.968 to +0.993**, and on C1 **every single** Δ=1 error lands
in the top-10% highest-motion frames. The source rung already measured both
corpora as heavy-tailed, "near-static steps punctuated by shot cuts." **Those
cuts are the errors.** Across a cut the probe frame is a different scene, so the
comparator fails on everything at once — and no within-frame measure, salient or
otherwise, can explain a failure that is uniform across the frame. **The C2 null
is not a weak instrument; it is the correct answer to a question aimed one level
below where the failure lives.**

**A second, cleaner mechanism separation falls out of the same table.** As the
orbit widens at Δ=1, failure becomes **less** frame-concentrated and **more**
region-distributed: C2's Gini falls **0.903 → 0.578 → 0.386** and the share in
high-motion frames falls **0.680 → 0.323 → 0.210** across Q0 → Q1 → Q2, while
error counts rise 25 → 62 → 162. **Q0's Δ=1 errors are cuts; Q2's Δ=1 errors are
distractor inflation.** The source rung established that over-quotienting is
actively harmful; this localises that harm as a genuinely region-level error mode
the wide orbit *manufactures* on top of the frame-level one.

---

## 5. THE ADJACENCY SECONDARY

Pre-registered with a **geometry-derived** chance baseline (corner and edge
regions have fewer neighbours, so uniform chance would be wrong). Over all MISID
rows pooled across comparators and Δ (C1 n=2277, C2 n=2468).

| corpus | measure | observed | chance | **difference** |
|---|---|---|---|---|
| C1 | 4-adjacent | 0.2411 [0.2276, 0.2551] | 0.2010 | **+0.0401 [+0.0268, +0.0539]** |
| C1 | 8-adjacent | 0.3650 | 0.3529 | +0.0121 [−0.0089, +0.0346] (null) |
| C1 | mean Chebyshev | 1.8902 | 1.8933 | −0.0030 [−0.0333, +0.0252] (null) |
| C2 | 4-adjacent | 0.2431 [0.2227, 0.2667] | 0.1985 | **+0.0447 [+0.0235, +0.0691]** |
| C2 | 8-adjacent | 0.3663 | 0.3468 | +0.0195 [−0.0073, +0.0479] (null) |
| C2 | mean Chebyshev | 1.9400 | 1.9080 | +0.0321 [−0.0085, +0.0721] (null) |

**A real but small excess of edge-sharing confusions on both corpora (+4.0pp,
+4.5pp, CIs excluding 0) — and NOTHING beyond it.** Diagonal neighbours show no
excess, and mean Chebyshev distance sits **at** its geometric chance value. So
the answer to "adjacent or scattered?" is **both, and mostly scattered**: there
is a modest resolution-floor component confined to directly abutting regions,
sitting on top of an otherwise spatially unstructured error distribution. **The
strong reading — "wrong winners are near-misses, so this is a resolution floor" —
is NOT supported**; if it were, mean Chebyshev distance would be below chance,
and it is not. **Bound:** this pools Δ, and §4 shows Δ=1 and Δ=25 are different
regimes; a Δ-resolved adjacency analysis was not pre-registered and is not run
here.

---

## 6. MY PREDICTIONS, SCORED (§3.7)

| # | prediction | outcome |
|---|---|---|
| 1 | C1 shows a NEGATIVE Δ_sal with CI excluding 0 | **RIGHT** (−0.0164 [−0.0276, −0.0049]) — but I did not anticipate it would be practically negligible (1.004× overstatement). |
| 2 | C2 returns the NULL | **RIGHT** (+0.0240 [−0.0044, +0.0547]). I recorded in advance that this was the least convenient combination — a null on the corpus of interest, a positive on the easier one — and it is what happened. |
| 3 | \|Δ_sal\| < 0.15 where non-null | **RIGHT**, and by a wide margin (0.0164). |
| 4 | TIEBREAK flatter in salience than MISID on both corpora | **HALF RIGHT — and the error was the most informative one.** RIGHT on C1. **WRONG on C2, dramatically**: TIEBREAK is −0.0991 (CI excluding 0) against a MISID null. My stated reasoning — "a tie-break is an identifiability limit of the k=4 lattice, which has no reason to respect chroma" — was backwards. Flat, low-chroma-contrast regions are precisely where k=4 collapses distinctions, so ties concentrate there. |
| 5 | Adjacency exceeds geometric chance on both corpora | **PARTLY.** 4-adjacency yes on both, CI-separated; **8-adjacency and mean Chebyshev distance are both at chance**, so the "near-miss / resolution floor" reading I intended is not supported. |
| 6 | `lsal` shows a LARGER negative Δ_sal than `csal` | **WRONG on both corpora** — and wrong in the reassuring direction. The confounded channel carries *no more* signal than the independent one, which is evidence the mediation caveat of §1 is not driving the C1 result. |

**Three right, one half, one partly, one wrong.** The wrong one (6) was a
soundness check I expected to fail and it passed instead; the half-wrong one (4)
inverted the mechanism I was most confident about, and is the most useful thing I
learned.

---

## 7. BOUNDS ON EVERYTHING ABOVE (§8)

- **Toy resolution.** 24×24 frames, 6×6 regions, a 4×4 salience grid. Nothing
  here is a claim about video at any real resolution.
- **THE WEAKEST LINK, declared in advance and unchanged by the result:** a 4×4
  grid of 6×6 tiles **cannot express object-level salience**. There is no
  objecthood, no segmentation, no tracking. "The phone versus the curtains" is
  approximated by "this sixth of the frame is chromatically distinct from its
  neighbours." **No result here should be read past that.** A genuine
  object-level salience measure could in principle overturn the null, and this
  rung does not test one.
- **`csal` is a WHERE-to-look proxy, not attention.** Nothing here shows a
  viewer would attend to a high-`csal` region.
- **Two episodes**, one cartoon and one nature documentary. Not a survey — and
  §3.3 shows they take **opposite signs**, so pooling is forbidden and no
  single-corpus number generalises to "video".
- **C2's chroma is weak** (sd(R−G) 8.69 vs 40.33). Mitigated but not eliminated
  by the CI-separated TIEBREAK result on the same corpus and measure (§1).
- **Mediation, not circularity** (§1): tested via `lsal` and not detected;
  "not detected" is not "absent".
- **§4 and the adjacency Δ-pooling are POST-HOC / unstratified.** §4 was not
  pre-registered; the per-cell table is not multiplicity-corrected.
- **C3 has no colour salience here** — BSDS300 is absent from this environment,
  so C3 serves only as the d=0 zero-misidentification control. Declared, not
  attempted.
- **Nothing was learned, nothing trained.** This is a re-scoring of preserved
  rows plus a salience field computed by an unchanged seed.
- **§9:** no default moved, no committed seed edited, no rule changed, no Rust
  touched. `vision_colour` / `vision_stream` remain OFF by default and not
  boot-loaded; this rung's scripts arm them locally via the existing adapter.

---

## 8. VERIFICATION

| check | result |
|---|---|
| `bash scripts/rung7_vision_bench.sh` | **200 passed, exit 0** (144.1 s), with `data/` symlinked per §10.2 |
| sd orbit law `{2:1, 3:2, 4:2, 6:2, 12:4}` | **unmoved** (inside the bench) |
| all 16 preserved row files vs `SHA256SUMS.txt` | **16/16 OK**, before and after use |
| committed motion statistic reproduced from regenerated frames | **EXACT, to the last bit, both corpora** |
| C3 d=0 negative control | **MISID = 0 for all six comparators** |
| zero-width CI anomaly | **independently reimplemented and reproduced** (sd = 0 over 10 000 draws); diagnosed structurally, not patched |
| HPE robustness variant | **same signs, same verdicts** on both corpora |

---

## 9. WHAT I WOULD PRE-REGISTER NEXT

**Not "salience, but better."** §4 says the Δ=1 failure unit is the FRAME, so the
aimed-at next rung is **cut detection as a first-class percept**: if the
comparator knew a cut had occurred — which per-frame motion magnitude predicts at
r ≈ +0.99 — it would know its identity claim is void rather than confidently
wrong. That is a graph-resident *abstention*, and it addresses the actual
mechanism.

Named and explicitly NOT done here, so they are not confused with results:
(a) **the object-level salience measure** the §7 bound names as the weakest link
— the honest retest of this rung's hypothesis, which needs proto-objects, not a
finer grid; (b) a Δ-resolved adjacency analysis, since §4 shows Δ=1 and Δ=25 are
different regimes; (c) re-running the salience test *within* non-catastrophic
frames only — deliberately withheld here, because after a pre-registered null it
would be indistinguishable from a rescue (§5), and it needs its own
pre-registration to be worth anything.
