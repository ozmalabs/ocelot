# HOLD THE PROPOSAL FIXED, VARY ONLY THE VERDICT — RESULTS

*Pre-registration: `VISION_VERDICT_PREREG.md`, committed BEFORE any headline
number at **`59cebc76c240d4a38e23a61d271fef627da79c74`** (branch base
**`7018fb48bd3c563618c99878f52ed856b141df33`**).*

**Engine (§10):** `25fa11652e83` @
`runners/dsl/python/substrate_rs/_native.abi3.so` — a **shared build from the
canonical tree, Rust source verified byte-identical** (`shared` verdict; the
sole difference in `runners/dsl/src` is the untracked `py.rs.selfmod.bak`, which
is not compiled). **This rung adds NO Rust, NO Term and NO constant** — every
verdict is expressed in Terms that already existed. `scripts/engine_build.sh`
was therefore not run, and `tests/test_engine_provenance_migrated.py` was run as
its own step **before any number was taken**: **7 passed**.
**Machine:** AMD Ryzen 5 9600X, 12 logical cores, **under concurrent load
throughout** (load average 5–9; this rung's own two confirmatory jobs overlapped
for part of the run). **Wall-clock is reported only as a cost. Every other
quantity is deterministic under fixed seeds**, and the graph's score was checked
against an independently computed reference on **every trial**.
**Selector:** `scripts/verdict_comparator_measure.py` (confirmatory) +
`scripts/verdict_comparator_analyse.py` (the pre-registered decision rule,
applied mechanically).
**Raw:** `results/verdict_comparator_{pilot,c3,video}.json`,
`results/verdict_analysis_{c3,video}.json`. The 12 per-trial row files
(`verdict_rows_*.json`, 8.5 MB) are **not committed**, following the incumbent's
precedent; their SHA256s are in §9 so they can be re-verified.
**Seeds:** block **70000–70999** for the confirmatory run; the **57000** block
(already burned by the incumbent) for the power pilot only. **No seed outside
those was drawn, and no confirmatory seed was spent on the pilot.**

---

## 0. THE HEADLINE, IN ONE PARAGRAPH

**A continuous verdict fixes the failure a tie-break could never touch — and the
conjunctive gate then disqualifies the arm that looked best.** Holding the
proposal layer fixed at ρ=2 and varying only the score, **normalized
cross-correlation on the raw grey tile (V3) is the only arm that passes all
three clauses.** On **C2 (live-action), the corpus where genuine
misidentification lives**, `true_achieves_max` at Δ=1 off cut frames rises
**0.8112 → 0.9898**, a paired **+0.1786 [+0.1462, +0.2109]**; on synthetic C3 it
takes accuracy on the incumbent's own tied subset from **0.1823 → 1.0000**
(**+0.7639 [+0.6624, +0.8654]**) **while leaving the untied subset at exactly
+0.0000** — it breaks the ties without breaking anything that already worked.
**The arm with the best raw accuracy is NOT the winner.** Plain squared distance
on grey (V2) beats V3 on C2 non-cut accuracy (0.9245 vs 0.9083) and **fails
clause 3 outright: its A1 answer rate is EXACTLY 1.0000 on both corpora — its
abstention never fires once.** The cut stratum shows why that matters: across a
cut **V2's accuracy is 0.0063 and it still never abstains**, while V3 refuses
**12× more often on cut trials than non-cut** (+0.0838 [+0.0300, +0.1375] over
V2, CI-separated). **V2 is the most accurate arm on good data and the most
dangerous on bad data.** Three further results are worth as much as the verdict.
**(1) V0 reproduces the incumbent to four decimals** — `true_achieves_max` =
**0.7975** against the published **0.7975**, independent implementation,
different engine, different seed block. **(2) The ordinal arm (V1) is a PROVEN
degeneracy, not a weak result:** at Δ=1, 100.00% of cell differences are ≤1
quantizer level, so `SSD = 36 − covered_count` **exactly** and the two rank
identically — measured Δ of **+0.0000 with sd +0.0000**. **On a 4-level
quantizer ordinality has nowhere to express itself; the entire gain is
dequantization.** **(3) The corpora take OPPOSITE SIGNS, again:** on **C1
(cartoon)** the same continuous verdict is **CI-separated NEGATIVE** at Δ=1
(V2 **−0.0117 [−0.0221, −0.0014]**) because V0 is already at 0.9831. **Pooling
the two would have reported a mid-sized positive that is true of neither.**

---

## 1. DISCLOSURE, AND AN INSTRUMENT DEFECT THIS RUNG FOUND IN ITSELF

**Two things are reported here rather than buried, because concealing either
would be exactly the forking-paths garden §4 forbids.**

### 1.1 I was not blind on C2

The power pilot ran on burned seeds and **showed me C2's effect sizes before the
pre-registration was committed**. This was disclosed in §6.1 of the prereg *at
commit time*, not retrospectively. §7's predictions were written **before the
pilot returned** and were **left unedited**, including prediction 3, which the
pilot already contradicted. No metric, arm, stratification or decision rule was
chosen after seeing it. **C2's confirmatory result is therefore a replication of
a seen effect on fresh seeds; C1 and C3 were genuinely blind.**

### 1.2 THE TRUNCATED APERTURE — caught by the rung's own per-trial check

The pre-registration declared (prediction 8) that score agreement with the
outside-the-graph reference must be **1.0000 on every arm and every trial**, and
that **any disagreement is an instrument defect that blocks every number**. The
first C3 run **disagreed**: 79/3456 rows (V1) and 150/3456 (V2). The fact was
verified first and the fix came second (§12.3's order).

**The defect.** `pad_edge(src, ρ)` widens a 24-wide frame to 28. A probe
presented at displacement `d` takes its window at `c0 + d + ρ + dc`, which for
the trailing-edge regions reaches 24 at `(d=2, dc=+2)` — so the slice `[24:30]`
on a 28-wide array returns **four columns, not six**, and **numpy does not
complain**. The tile is encoded with 24 cells instead of 36, its `‖p‖²` is a
norm over 24 while the candidate's is over 36, and the one-`Dot` expansion
silently compares mismatched quantities.

**The diagnosis was the pattern, and it matched the arithmetic exactly:** 100%
of disagreements were on A3, at `d1` and `d2`, and **never at `d0`** — and `d=0`
is the only displacement at which truncation is impossible.

**Why it had never been seen — and this is the part worth keeping.** The
incumbent's `covered_count` is a **set overlap**, so a short tile merely
contributes fewer tuples and **the graph and the reference agree on a wrong
number**. The same construction is latent in
`invariant_comparator_world.orbit_windows` (also padded by ρ, also presented at
`(0,d)`) and reports nothing.

> **A truncated aperture is INVISIBLE to a set-overlap verdict and VISIBLE to a
> norm-based one.** The disagreement was the instrument working, not failing.

**Scope of the correction, and what it does NOT touch.** The fix pads by
`ρ + max|displacement|` and makes a short window **raise**. At displacement
`(0,0)` — **every video probe** — `pad = ρ + 0 = ρ`, so the fix is a **no-op**
there. That is gated, not asserted
(`test_zero_displacement_padding_is_unchanged_by_the_fix` compares all 25 orbit
tiles array-by-array), and is independently confirmed by the fact that **C1 and
C2 score agreement is 1.0000 on all four arms** in the final run. **C3 was
re-run from scratch after the fix; the video run was not affected and stands.**
Reported to the supervisor as an incumbent-facing observation — that rung's files
are not mine to edit.

---

## 2. THE PREMISE, CHECKED RATHER THAN ASSERTED

"Hold the proposal fixed, vary only the verdict" is the whole design, so it is
hashed: `check_proposal_identity` rebuilds the candidate set — every orbit tile,
the codebook, the seeded insertion order — and hashes it in order.

| corpus | proposal identical across all four arms |
|---|---|
| **C3** | **True** |
| **C1** | **True** |
| **C2** | **True** |

**Every arm was offered the byte-identical 16 regions × 25 orbit shifts.** ρ was
held at **2**, the measured knee, and is not varied anywhere in this rung.

---

## 3. MECHANISM 1 — MISIDENTIFICATION, PER CORPUS, CUT-STRATIFIED

`true_achieves_max` on A1 probes, unit = **base frame**, n = 50, paired vs V0,
95% t-CI, `t(0.975,49) = 2.0096`. **`**` = CI excludes 0.** **The corpora are
never pooled and the strata are never merged.**

### 3.1 THE CUT RULE, AND ITS INDEPENDENT CORROBORATION

A probe `(t, Δ)` is a **CUT** iff the maximum per-step mean |Δ| over `[t, t+Δ)`
exceeds **Otsu's threshold** — a split with **no free parameter**, determined by
the data's own bimodality (§13).

| corpus | Otsu threshold | low class | high class |
|---|---|---|---|
| **C1** | **27.294** | 146 steps, mean **0.824** | 3 steps, mean **48.904** |
| **C2** | **24.606** | 146 steps, mean **2.070** | 3 steps, mean **49.462** |

**Both corpora are sharply bimodal — a 59× and 24× separation of class means —
so the split is real, not a percentile imposed on a smooth distribution.**

**AND THE FALSIFIABLE CORROBORATION DECLARED IN ADVANCE LANDS EXACTLY.** The
prereg predicted the C1 cut set would contain base frames **34 and 47**. Otsu's
cut steps within the first 50 bases are **[34, 47]** — precisely the two frames
`VISION_SALIENCE_RESCORE_RESULTS.md` §4 independently identified by *error
concentration* (base 34: 16 of 16 regions failed; base 47: 15 of 16). **Two
rungs, two entirely unrelated methods — motion bimodality and error clustering —
name the same two frames.**

### 3.2 C2 LIVE-ACTION — where genuine misidentification lives

| Δ / stratum | n | V0 hamming | V1 ssdq | V2 ssdg | V3 ncc |
|---|---|---|---|---|---|
| **Δ=1 NON-CUT** | 784 | **0.8112** | 0.8112 `+0.0000 [+0.0000, +0.0000]` | 0.9936 **`+0.1824 [+0.1485, +0.2163]`** | 0.9898 **`+0.1786 [+0.1462, +0.2109]`** |
| Δ=1 cut | 16 | 0.1250 | 0.1250 | 0.0000 | 0.0625 |
| Δ=5 NON-CUT | 720 | 0.5806 | 0.5986 **`+0.0181`** | 0.8583 **`+0.2778 [+0.2318, +0.3237]`** | 0.8708 **`+0.2903 [+0.2463, +0.3342]`** |
| Δ=5 cut | 80 | 0.1500 | 0.1500 | 0.0000 **`−0.1500`** | 0.0750 **`−0.0750`** |
| Δ=25 NON-CUT | 416 | 0.5938 | 0.5986 | 0.9087 **`+0.3149 [+0.2706, +0.3592]`** | 0.8197 **`+0.2260 [+0.1835, +0.2684]`** |
| Δ=25 cut | 384 | 0.1641 | 0.1589 | 0.0078 **`−0.1562`** | 0.1536 `−0.0104` |

**Clause 1 passes decisively for V2 and V3, and fails for V1.**

**THE SIGN REVERSES ACROSS THE CUT STRATUM, and it is CI-separated.** Off cuts
the continuous verdict is worth up to **+31pp**; across cuts it is worth
**−15pp**. **A continuous score is sharper, so when the signal is gone it commits
harder to a wrong answer** — where Hamming's coarseness accidentally leaves the
true region tied at the maximum more often. **This is exactly why the
stratification was mandated**: pooling would have diluted a +0.18 into a smaller
number *and* concealed that the effect inverts.

### 3.3 C1 CARTOON — the same verdict, the opposite sign

| Δ / stratum | n | V0 hamming | V1 ssdq | V2 ssdg | V3 ncc |
|---|---|---|---|---|---|
| **Δ=1 NON-CUT** | 768 | **0.9831** | 0.9753 **`−0.0078 [−0.0139, −0.0018]`** | 0.9714 **`−0.0117 [−0.0221, −0.0014]`** | 0.9740 `−0.0091 [−0.0197, +0.0015]` |
| Δ=5 NON-CUT | 640 | 0.9719 | 0.9688 | 0.9625 **`−0.0094`** | 0.9578 **`−0.0141`** |
| Δ=25 NON-CUT | 192 | 0.9531 | 0.9531 `+0.0000` | 0.9427 `−0.0104` | 0.9427 `−0.0104` |
| Δ=25 cut | 608 | 0.0740 | 0.0789 | 0.0789 | 0.1414 **`+0.0674`** |

**On cartoon the continuous verdict is CI-separated NEGATIVE at short Δ.** The
reason is visible in the first column: **V0 is already at 0.9831**. Cel-shaded
regions are locally flat and highly distinctive at the tile level — the k=4
quantizer is *well matched* to cel shading, so dequantization adds variance
rather than signal.

> **THE THIRD INDEPENDENT REPRODUCTION OF THE NO-POOLING RULE.** The source rung
> found the corpora disagree in sign on the *discrimination margin*; the salience
> rung found they disagree in sign on *salience-graded error*; this rung finds
> they disagree in sign on *the value of a continuous verdict*. **Any headline of
> the form "a continuous verdict is worth +Xpp on video" is quoting the easier or
> the harder corpus by accident.**

---

## 4. MECHANISM 2 — TIES, MEASURED AGAINST A STATISTIC THE SELECTOR DOES NOT COMPUTE

**The tie statistic is `v0_region_ties`** — the number of **REGIONS** tied at the
maximum **under the INCUMBENT's score**, computed **outside the graph** and
**held FIXED across all four arms**. This rung's seed **computes no tie statistic
at all**; the `Count` the source rung retracted is **deleted**, and a gate
positive-controlled that it stays deleted (injecting one turns the gate red).

C3, 24 BSDS photographs, unit = **photo**, n=24, `t(0.975,23) = 2.0687`.

| d=0 subset | n | V0 hamming | V1 ssdq | V2 ssdg | V3 ncc |
|---|---|---|---|---|---|
| **V0-TIED** | 181 | **0.1823** | 0.1823 `+0.0000` | 1.0000 **`+0.7639 [+0.6624, +0.8654]`** | 1.0000 **`+0.7639 [+0.6624, +0.8654]`** |
| **V0-UNTIED** | 203 | 1.0000 | 1.0000 `+0.0000` | 1.0000 **`+0.0000`** | 1.0000 **`+0.0000`** |
| all | 384 | 0.6146 | 0.6146 | 1.0000 **`+0.3854`** | 1.0000 **`+0.3854`** |

**Clause 2 passes for V2 and V3.** The two rows together are the result:
**accuracy on the incumbent's tied subset goes 0.1823 → 1.0000, and the untied
subset moves by EXACTLY +0.0000.** The continuous verdict **breaks the ties
without breaking anything that already worked** — it is not trading one error
class for another. `d=1` and `d=2` reproduce this (+0.7143, +0.7818).

**THE FORCED PART, DECLARED IN ADVANCE AND NOT PRESENTED AS A RESULT.** Exact
ties essentially cannot occur for a continuous score, so V2/V3's own tie count
falling to **1.000** is **forced by construction**. The *risked* quantity was
whether the ties would be broken **correctly** — a verdict can shatter every tie
and still pick wrong. They were.

**V2 and V3 are numerically IDENTICAL on C3, and that is a soundness check
passing, not a coincidence:** C3's probe is the *same photograph* displaced, so
there is **no photometric nuisance for NCC to quotient**. V3 ≡ V2 is exactly what
should happen when the nuisance V3 targets is absent.

---

## 5. CLAUSE 3 — REFUSAL, AND THE ARM IT DISQUALIFIES

**The floor is MEASURED, not chosen (§13):** a group answers only if it strictly
exceeds the best score the **same arm** achieves on the calibration noise probes
in the **same substrate**. **No numeric threshold appears anywhere in the seed**,
and a gate asserts that. The control is **not** the tautology "the max of a set
does not exceed itself": `G2c` *defines* the floor, and the measured control is
**`G2t`, an independent draw**, against **`G1`, the identical frame**.

| corpus | arm | refuse G1 | refuse G2t | **G2t − G1** | A1 answer rate | acc (all) | acc (answered) |
|---|---|---|---|---|---|---|---|
| C2 | V0 hamming | 0.0000 | 0.9712 | **+0.9712 [+0.9564, +0.9861]** | 0.9767 | 0.4371 | 0.4454 |
| C2 | V1 ssdq | 0.0000 | 0.9387 | **+0.9387** | 0.9954 | 0.4508 | 0.4529 |
| C2 | **V2 ssdg** | 0.0000 | 0.9300 | **+0.9300** | **1.0000** ❌ | 0.7408 | 0.7408 |
| C2 | **V3 ncc** | 0.0000 | 0.9387 | **+0.9387** | **0.9733** ✅ | 0.7542 | 0.7684 |
| C1 | **V2 ssdg** | 0.0000 | 0.9263 | **+0.9263** | **1.0000** ❌ | 0.6704 | 0.6704 |
| C1 | **V3 ncc** | 0.0000 | 0.9575 | **+0.9575** | **0.9508** ✅ | 0.6867 | 0.7156 |

**Every arm refuses noise and answers the identical frame.** But clause 3 also
required the A1 answer rate to be **strictly inside (0,1)**, and **V2's is
EXACTLY 1.0000 on both corpora: its abstention never fires once on a real
probe.**

### 5.1 THE POST-HOC ANALYSIS THAT SHOWS THIS IS NOT A TECHNICALITY

**NOT PRE-REGISTERED. Labelled post-hoc.** The cut stratum is where a verdict
*should* decline — across a cut the probe is a different scene and the identity
claim is void.

| corpus | arm | stratum | refuse | acc |
|---|---|---|---|---|
| **C2** | **V2 ssdg** | non-cut | **0.0000** | **0.9245** |
| **C2** | **V2 ssdg** | **cut** | **0.0000** | **0.0063** |
| **C2** | **V3 ncc** | non-cut | 0.0083 | 0.9083 |
| **C2** | **V3 ncc** | **cut** | **0.1000** | 0.1375 |
| C1 | V2 ssdg | non-cut / cut | 0.0000 / **0.0000** | 0.9644 / 0.0825 |
| C1 | V3 ncc | non-cut / cut | 0.0056 / **0.1363** | 0.9637 / 0.1325 |

> **V2 is confidently wrong on 99.4% of C2 cut trials and abstains on NONE of
> them.** Its refusal is a **dead instrument on the arm** — alive against noise,
> inert against the failure that actually occurs.

**V3's refusal is 12× more likely on cut trials than non-cut** (C2: 0.1000 vs
0.0083; C1: 0.1363 vs 0.0056, 24×), and the paired per-frame difference against
V2 on cut trials is **+0.0838 [+0.0300, +0.1375]** on C2 and **+0.1390 [+0.1016,
+0.1763]** on C1 — **both CI-separated.** V3 pays ~1.6pp of non-cut accuracy for
an abstention aimed at the right trials.

**This is the pattern the conjunction exists to catch, and it caught it.** The
source rung's histogram anchor scored 0.716 accuracy at exactly 0.0000 margin;
here the highest-accuracy arm on good data is the one that cannot decline on bad
data. **Ranking by accuracy alone would have crowned V2.**

---

## 6. THE PRE-REGISTERED VERDICT, APPLIED MECHANICALLY

| arm | clause 1 MISID (C2 Δ=1 non-cut) | clause 2 TIES (C3 V0-tied) | clause 3 REFUSAL | **VERDICT** |
|---|---|---|---|---|
| **V1 ssdq** | ✗ `+0.0000` | ✗ `+0.0000` | ✅ | **FAILS** (proven degeneracy, §7) |
| **V2 ssdg** | ✅ **+0.1824** | ✅ **+0.7639** | ❌ **answer rate 1.0000** | **FAILS the conjunction** |
| **V3 ncc** | ✅ **+0.1786** | ✅ **+0.7639** | ✅ **0.9733 / 0.9508** | **PASSES ALL THREE** |

**V3 (normalized cross-correlation on the raw grey tile) is the only arm that
beats the incumbent under the pre-registered gate.**

**Scope, stated with the verdict:** this holds **on C2**. On **C1 the same arm is
null-to-negative** at short Δ, and **across cuts every continuous arm is worse
than the incumbent.** The honest one-line form is: *a continuous,
photometrically-invariant verdict is worth ~+18pp of misidentification on
live-action video off cut frames, worth nothing on cartoon, and actively harmful
across a scene cut.*

---

## 7. THE ORDINAL ARM IS A PROVEN DEGENERACY, NOT A WEAK RESULT

V1's paired difference is **+0.0000 with sd +0.0000** — a zero-width interval,
which is an instrument smell (the salience rung's §4 lesson). It was chased, and
it is **arithmetic**:

> **Measured: at Δ=1, 100.00% of cell differences between consecutive frames are
> ≤1 quantizer level** (Δ=5: 99.88%; Δ=25: 87.71%). When every mismatch is
> exactly one level, `SSD = #mismatches = 36 − covered_count`, so **−SSD is an
> exact affine function of `covered_count` and the two rank IDENTICALLY.**

The Δ=5 and Δ=25 fractions predict exactly where V1 begins to deviate, and it
does (C2 Δ=5: `+0.0181`, CI-separated but tiny).

**The finding: on a 4-level quantizer, ordinality has nowhere to express
itself.** V1 was included to separate *metric* from *representation*, and it
does so conclusively — **the entire gain is DEQUANTIZATION, none of it is the
graded metric.** That is a result the ladder was built to produce, and it is why
V1 was retained rather than dropped once the pilot flagged it.

---

## 8. MY PREDICTIONS, SCORED (§3.7)

| # | prediction | outcome |
|---|---|---|
| 1 | V0 reproduces the source rung's Q2: C2 Δ=1 `true_achieves_max` within ~0.03 of 0.7975 | **RIGHT, EXACTLY.** Measured **0.7975** against the published **0.7975** — four decimals, independent implementation, different engine, different seed block. The strongest reproduction in the arc. |
| 2 | Clause 2 passes for V2/V3; ties break CORRECTLY | **RIGHT**, and stronger than predicted: tied-subset accuracy → **1.0000**, untied subset **+0.0000** exactly. |
| 3 | Clause 1 decides the rung; **V3 > V2 > V1 > V0** on C2 non-cut | **WRONG ON THE ORDERING, RIGHT ON THE MECHANISM.** V2 ≈ V3 ≫ V1 ≈ V0: dequantization does essentially all the work and affine invariance adds ~nothing *to accuracy*. I had the ladder's steps in the wrong proportion. **The pilot had already shown me this and I left the prediction unedited.** V3 does separate from V2 — but on **refusal**, which I did not predict at all. |
| 4 | C1's effect small, possibly null or negative | **RIGHT ON THE CONCLUSION, WRONG ON THE REASON.** C1 is CI-separated negative. My stated reason was flat tiles starving NCC — but `nflat` is **0.0000 everywhere** (prediction 5). The real reason is that **V0 is already at 0.9831**: cel shading is well matched to a 4-level quantizer. |
| 5 | `nflat` materially higher on C1 than C2 | **WRONG.** `nflat = 0.0000` on both corpora, every arm: at 6×6 tiles from a 24×24 frame, **no tile is exactly zero-variance**, not even in cel-shaded cartoon. The declared weakness of V3 never materialised at this resolution — and would return at finer tiling. |
| 6 | Refusal alive for all four arms; G2t > 0.9, G1 < 0.1 | **RIGHT** (G1 **0.0000** every arm; G2t 0.9263–0.9712) — **but incomplete in the way that mattered.** "Alive" against noise did not imply alive against the real failure: V2 passes this and still **never abstains on a real probe**. The A1-answer-rate sub-clause, not this one, is what disqualified V2. |
| 7 | The cut stratum shows much lower `true_achieves_max` for every arm, with SMALLER arm differences there | **HALF RIGHT, AND THE ERROR IS THE INTERESTING ONE.** The levels collapse as predicted (0.98 → 0.006–0.16). But the arm differences are **not smaller — they REVERSE**, CI-separated (V2 **−0.1562** at C2 Δ=25). I predicted no verdict could fix a signal discontinuity; I did not anticipate that a **sharper** verdict makes it actively **worse**. |
| 8 | Score agreement = 1.0000 on every arm and every trial | **RIGHT ONLY AFTER THE INSTRUMENT WAS FIXED — and the prediction is what found the defect** (§1.2). Final: **1.0000 on all four arms, all three corpora**. |
| 9 | The proposal hash is identical across all four arms | **RIGHT** — True on C3, C1 and C2. |

**Three right, one right-and-exact, two half, two wrong, one conditional.** The
two errors I care about (3 and 7) were both about **where the continuous
verdict's effect would show up**: I modelled its benefit correctly and its
*character* badly — it is not "more accurate everywhere", it is **sharper**,
which is a gain on good data and a liability on broken data. Prediction 6 is the
most useful miss: **I wrote an aliveness check that a dead instrument passes.**

---

## 9. BOUNDS ON EVERYTHING ABOVE (§8)

- **Toy resolution only.** 24×24 frames, 6×6 apertures. **Nothing here is a claim
  about video at any real resolution.** The measured scale wall (O(N^1.887)) is
  untouched.
- **Nothing was learned.** One frame's regions held for one comparison and
  discarded. No training, no accumulation, no codebook growth. **This measures a
  COMPARISON, not "learning by watching video."**
- **Fixed aperture, not tracking.** No object correspondence, no segmentation, no
  proto-objects, no border-ownership.
- **Two episodes and 24 photographs.** Not a survey — and the corpora take
  **opposite signs**, so pooling is forbidden and no single-corpus number
  generalises to "video".
- **THE AFFINE-LUMINANCE QUOTIENT IS IN THE ENCODING, NOT THE GRAPH.** The
  adapter centres and unit-normalises so the graph's score is one `Dot`. The
  DECISION and the ABSTENTION are the graph's (`Argmax`, `IfThenElse`); the
  invariance is preprocessing, of the same class as `quantize` and the
  incumbent's `sig_registered` centroid. **This rung does not claim that
  quotient is graph-resident.**
- **V3 beats V2 on REFUSAL, not on ACCURACY.** On C2 non-cut V2 is *more*
  accurate (0.9245 vs 0.9083). The entire case for V3 rests on clause 3, and
  anyone who values accuracy alone should read §5.1 and disagree explicitly.
- **The refusal floor is per-substrate and per-base-frame.** It is measured, not
  chosen — but it is measured from *uniform noise*, which is a weak null. A
  structured-but-wrong probe (the A2 distant frame) is a harder floor and was not
  used as the threshold source.
- **k=4 and the 6×6 tiling are hand-set** (§13), inherited unchanged for
  comparability and **not swept**. V2/V3 partially *bypass* k=4 rather than
  replacing it — **the quantizer still governs the proposal layer**, and §7 shows
  the quantizer is precisely what limited the incumbent.
- **ρ=2 is held fixed**, so nothing here re-opens the orbit trade-off.
- **`nflat = 0.0000` at this tiling** means V3's declared degenerate-tile weakness
  was never exercised. **It is untested, not absent**, and would return at finer
  tiling or on flatter content.
- **§5.1 and the V1 arithmetic in §7 are POST-HOC** and labelled as such.
- **Δ=25 non-cut on C1 has n=192** (192 of 800 trials survive the cut filter);
  the Δ=25 cells are the least powered in the table.
- **§9 (defaults):** no default moved, no committed seed edited, no rule changed,
  no Rust touched. The seed ships `verdict: ""` (matching no arm) and is not
  boot-loaded.

---

## 10. VERIFICATION

| check | result |
|---|---|
| `tests/test_engine_provenance_migrated.py`, **run as its own step before any number** | **7 passed** |
| engine hash pinned before and after | `25fa11652e83`, `shared`, Rust source byte-identical |
| `bash scripts/rung7_vision_bench.sh` **before** any file was added | **222 passed, exit 0** (189.4 s), with `data/` symlinked (§10.2) |
| `bash scripts/rung7_vision_bench.sh` **after** | **222 passed, exit 0** (147.1 s) |
| this rung's gate `tests/test_verdict_comparator_migrated.py` | **34 passed, 4 skipped** (the 4 provenance tests pinned below) |
| graph score == outside-the-graph reference | **1.0000 on all four arms, C1 / C2 / C3** (after §1.2's fix) |
| proposal-layer hash identical across arms | **True on C3, C1, C2** |
| V0 reproduces the incumbent's published `true_achieves_max` | **0.7975 vs 0.7975** |
| Otsu cut set vs the salience rung's independently-named frames | **C1 = [34, 47], exact match** |

*(The bench number is quoted with its condition per §10.2: **222/0 with `data/`
symlinked**, which it was throughout.)*

**The gate is positive-controlled red-then-green on the MECHANISM.** Replacing
the candidate-level `Argmax` with `Argmin` — the held region that explains the
observation *worst* — is loaded from a modified manifest and the ceiling control
goes red; restoring gives green. **The inversion is asserted to have applied at
exactly one site**, so an inert control cannot masquerade as a passing one.

**Two gates in this rung were positive-controlled because they could otherwise
have been vacuous:**
1. The **tie-count-is-gone** gate: injecting a tie `Count` into a rule turns it
   **red**. (Its first version was itself defective — it matched the string
   `"ntied"` in the seed's **prose**, §12's substring-selector defect in my own
   gate. The fact was verified first, then the selector narrowed to the rules.)
2. The **truncated-aperture** gate **drives the under-padded configuration and
   requires it to raise** — a guard that has never been *able* to fire is not a
   guard.

**Row-file checksums** (not committed, 8.5 MB; the incumbent's precedent):

```
9d8c56b4…  verdict_rows_C1_hamming.json     8608399e…  verdict_rows_C2_hamming.json
dc953c2e…  verdict_rows_C1_ncc.json         b3077d42…  verdict_rows_C2_ncc.json
a8f42a2c…  verdict_rows_C1_ssdg.json        9ce9107d…  verdict_rows_C2_ssdg.json
0ec35b5c…  verdict_rows_C1_ssdq.json        0ceeadc4…  verdict_rows_C2_ssdq.json
a2ac1dbd…  verdict_rows_C3_hamming.json     264d8f30…  verdict_rows_C3_ssdg.json
a4a07599…  verdict_rows_C3_ncc.json         fa23546f…  verdict_rows_C3_ssdq.json
```

Full digests: `results/verdict_rows_SHA256SUMS.txt`.


**THE AUDITED RANGE, AND WHAT LIES OUTSIDE IT — stated so the claim terminates.**
The provenance gates audit **`7018fb48..f900de0e`** — the branch base to the
results commit — which contains **all** of this rung's substantive content: the
pre-registration, the seed, the adapter, the runner, the analyser, the gate, the
five pinned result files and this document. **13 files, every one owned, zero
`.rs`, zero `Cargo.toml`, exactly one seed and it is mine.** Audited term by term,
not asserted. Exactly one commit follows, and it is named here rather than left
to a gate that would have to re-pin itself forever: the commit that writes
`PREREG_SHA`/`RUNG_SHA` into the gate and adds this paragraph. It touches only
`tests/test_verdict_comparator_migrated.py` and this file. **No Rust, no seed, no
result file, no other rung's anything.**

Both endpoints are fixed shas throughout; `HEAD` appears only in a `merge-base
--is-ancestor` reachability check, which is a question about *now* and correctly
resolves against the moving branch
(`tests/test_provenance_endpoint_guard_migrated.py` fails any range ending at
HEAD).

---

## 11. WHAT I WOULD PRE-REGISTER NEXT

**The measured bottleneck has moved, and it is now the CUT.** Off cut frames V3
sits at **0.9898** on C2 Δ=1 — there is ~1pp of headroom and further verdict work
is chasing it. Across cuts **every arm is at 0.006–0.16 and the continuous arms
are WORSE than the incumbent.** The cut stratum is now the dominant error mass
and the only place a large gain remains.

**So the next rung is the one the salience rung already named, and this rung has
now independently confirmed its premise from a second direction:** *cut detection
as a first-class percept.* Otsu on per-step motion separates the two classes at
**59×** and recovers exactly the frames error-concentration named. **A comparator
that knew a cut had occurred would know its identity claim is void rather than
being confidently wrong** — and §5.1 shows the best-accuracy arm is confidently
wrong **99.4%** of the time there while abstaining **never**. That is a
graph-resident abstention with a real trigger, and it addresses the actual
mechanism.

**And a sharper, cheaper question this rung raises:** V3's refusal already fires
12× more often on cut trials **without being told what a cut is**. The measured
question is whether a refusal floor calibrated on a **structured-but-wrong** null
(the A2 distant-frame probe) rather than uniform noise closes that gap on its
own — a threshold that still *falls out*, from a harder null.

Named and **NOT** done here, so they are not confused with results: whether the
knee ρ=2 moves once the verdict is continuous (the proposal and verdict layers
were deliberately decoupled, and their interaction is untested); whether any of
this survives above toy resolution; whether V3's degenerate-tile weakness bites
at finer tiling, where `nflat` would stop being 0; and a fusion of the incumbent
and V3 (Hamming is *better* across cuts, which suggests the two disagree
informatively rather than one dominating).
