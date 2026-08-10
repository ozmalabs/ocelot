# HOLD THE PROPOSAL FIXED, VARY ONLY THE VERDICT — PRE-REGISTRATION

*Written and committed BEFORE any headline number. Protocol §3.*

**Branch:** `gamma-substrate/verdict-rung`.
**Seed block:** **70000–70999**, verified unclaimed in the §11 ledger before launch.
**Engine (§10):** `25fa11652e83` @
`runners/dsl/python/substrate_rs/_native.abi3.so` — a **shared build from the
canonical tree with Rust source verified byte-identical** (`python
domains/engine_provenance.py` reads `shared`; the sole difference in
`runners/dsl/src` is the untracked `py.rs.selfmod.bak`, which is not compiled).
**This rung adds NO Rust, NO Term and NO constant.** Every verdict below is
expressed in Terms that already exist (`Dot`, `Plus`, `Minus`, `Times`,
`MaxOver`, `Argmax`, `IfThenElse`), which is why no `scripts/engine_build.sh`
run is required and why the provenance gate is expected to stay green
throughout.

**Selector:** `scripts/verdict_comparator_measure.py` (confirmatory) +
`scripts/verdict_comparator_analyse.py` (the pre-registered decision rule,
applied mechanically).
**Seed:** `seeds/vision_verdict_comparator.json`. **Adapter:**
`domains/verdict_comparator_world.py`.
**Oracle:** `bash scripts/rung7_vision_bench.sh` → **222 passed, exit 0**, with
`data/` symlinked (§10.2 — the number is quoted with its condition).

---

## 1. WHY THIS RUNG EXISTS, AND WHY ONE FIX CANNOT DO IT

`VISION_INVARIANT_COMPARATOR_RESULTS.md` (merged `ea09d9fd`) built a comparator
that is graph-resident and measured its exact character: `icg_max == nn_score`
on **124 096 of 124 096** trials, i.e. **a shift-tolerant Hamming classifier
expressed as graph data**. It fails **two different ways**, and its own §10
named this rung:

- **SYNTHETIC translation (C3):** `true_achieves_max` = **1.0000 at every
  radius**. The true region ALWAYS attains the maximum. *All* loss is
  **tie-break** — widening the orbit never lowers the true region's score, it
  raises everyone else's until they tie (mean regions tied 3.219 → 4.391).
- **REAL MOTION (C2):** `true_achieves_max` **DEGRADES** with radius
  (0.9688 → 0.9225 → 0.7975). A **wrong region outright BEATS** the true one.
  **No verdict that only breaks ties can touch this.**

So the rung holds ρ at the measured knee (**ρ=2**) and varies **only** the
verdict. The proposal layer — which candidates are offered — is fixed and
**checked**, not asserted: `check_proposal_identity` hashes every orbit tile and
the codebook in order, and the four arms must produce the identical hash.

**The continuous verdict is architecturally licensed, not a violation.**
CLAUDE.md's frame/continuum invariant is explicit: in-frame coordinates are
integer, and **all real-valued structure lives in the MAP BETWEEN FRAMES**. A
comparator between a held frame and an observed frame is exactly such a map, and
the invariant's own examples are the SC+TPS and DTW verdict metrics. *"Bins
propose, continuous decides"* IS this invariant, and it is the arc's own measured
synthesis: on Omniglot a strong continuous verdict was worth **+51.5pp** over a
weak one under precisely this kind of failure (`VISION_INK_VENTRAL_RESULTS.md` /
the run-16 reconciliation). In-frame integers are untouched here: region-local
`r,c` and the k=4 levels are unchanged.

---

## 2. THE FOUR ARMS — a mechanism ladder, one change per rung

Every arm sees the **identical** candidate set (16 regions × 25 orbit shifts at
ρ=2, same seeded insertion-order permutation). Only the score changes.

| arm | score | the ONE thing it changes | invariant to |
|---|---|---|---|
| **V0 hamming** | `ShapeDecode.covered_count` over `["cell", r, c, "v<q>"]` | — **the incumbent, byte-for-byte** (the published Q2 arm) | translation only (via the orbit) |
| **V1 ssdq** | −‖p−c‖² on the **quantized** values | metric: categorical → **graded** | translation |
| **V2 ssdg** | −‖p−c‖² on the **raw grey** tile | representation: k=4 bins → **continuous** | translation |
| **V3 ncc** | ⟨p̂, ĉ⟩, mean-centred unit-normalised raw grey | **affine luminance invariance** | translation **+ gain and bias** |

V1 → V2 → V3 each add exactly one thing, so a win is attributable. This is a
**ladder, not a sweep** (§3.6): four listed arms, no parameter search, no re-runs.

### 2.1 WHICH NUISANCE, AND WHY IT IS THE RIGHT ONE FOR *THIS* DOMAIN

**Stated because "it worked elsewhere" is not an argument** — the ink rung
imported D4 untangling from a synthetic crossing and it **HARMED −11.3pp at 8×
the compute**, because on handwriting the group is identity-*changing*
(`VISION_INK_VENTRAL_RESULTS.md`).

The nuisance V3 quotients is **affine luminance change** — exposure drift,
auto-gain, shading, a cloud crossing the sun, lamp flicker, the encoder's rate
control. On natural video this is **identity-PRESERVING by definition**: a patch
of the same scene that got 10% brighter is the same patch. Unlike D4 on a glyph,
there is no reading on which a brighter patch is a *different* patch.

**And it is argued from this corpus's own measured statistics, not by import.**
The source rung measured cartoon (C1) *gaining* margin with radius while
live-action (C2) *loses* it (0.743 → 0.633 → 0.493), and attributed this to
natural photographic texture being non-distinctive at the tile level. A k=4
quantizer on a **fixed absolute 0..255 scale** is worst exactly there: a small
global luminance shift walks cells across bin boundaries, and Hamming charges
every crossing a full miss — identically to a three-level slip. V1/V2/V3 recover,
in three separable steps, precisely the distinctions k=4 collapses.

**The declared weakness, stated in advance:** NCC is **undefined on a
zero-variance tile**, and cel-shaded cartoon regions are often flat. The adapter
emits the zero vector and flags `nflat`; the seed scores such a tile **0.0 — no
evidence** — rather than a guarded division silently returning something (§1.1).
The flat rate is reported per corpus and is expected to be **materially worse on
C1 than C2**.

### 2.2 WHERE EACH QUOTIENT IS PERFORMED — stated, not blurred

The source rung's headline was that its quotient was **in the graph**; this rung
must not quietly weaken that claim.

- The **translation** quotient is in the graph, unchanged (`vd_group_score`'s
  `MaxOver` over orbit members).
- The **decision** is in the graph (`Argmax` over the codebook by the arm's score
  Term; `IfThenElse` for the abstention).
- The **affine-luminance** quotient of V3 is **in the ENCODING** — the adapter
  centres and unit-normalises, so the graph's score is one `Dot`. That is
  mechanical preprocessing of the same class as `quantize`, `sig_histogram` and
  the incumbent's own `sig_registered` centroid, but **it is not in the graph and
  this rung does not claim it is.** The cost reason is stated and is real:
  computing the mean inside the rule is O(n²) in the tile and was measured
  infeasible at this trial count. The identity ⟨p̂,ĉ⟩ = ncc(p,c) is exact, and
  the runner checks the graph's score against an independent reference **on
  every trial**.

---

## 3. THE THREE CONSTRAINTS, EACH FROM A LANDED RESULT

### 3.1 THE TWO MECHANISMS ARE REPORTED SEPARATELY, PER CORPUS, AND NEVER POOLED

`true_achieves_max` (a wrong region outright wins) and the tie rate (the true
region is among the winners, and the tie is broken arbitrarily) are **different
quantities measuring different failures**. The corpora already disagree on the
**sign** of the margin cost, so a pooled number averages two opposite effects.
**Any headline that pools them is invalid regardless of its value**, and the
analysis script has no pooled cell.

### 3.2 THE CUT CONFOUND — STRATIFIED, with a rule that has no free parameter

`VISION_SALIENCE_RESCORE_RESULTS.md` §4: at short Δ the failure unit is the
**FRAME, not the region** — all 31 of one arm's Δ=1 errors in **2 base frames of
50**, all 16 regions failing at once, per-frame error tracking per-frame motion
at **r = +0.987**, **100%** of errors in the top-10% motion frames. **Scene cuts,
not verdict failures.**

**The rule:** a probe `(t, Δ)` is a **CUT** iff the **maximum per-step mean |Δ|
over the interval `[t, t+Δ)` exceeds Otsu's threshold** on that corpus's
per-step motion distribution. A cut anywhere inside the interval breaks identity,
hence the max.

**Why Otsu (§13):** a percentile is a number *I* choose; Otsu's threshold is
**determined by the data's own bimodality and has no free parameter at all**. The
source rung independently measured both corpora as heavy-tailed — *"near-static
steps punctuated by shot cuts"* — so the split this rung needs is the split the
data already has, and Otsu finds it without being told where it is. **The
threshold, both class sizes and both class means are reported.**

**The primary misidentification claim is made on the NON-CUT stratum. The cut
stratum is reported beside it, never merged.** *Falsifiable corroboration
declared in advance:* the C1 cut set should contain base frames **34 and 47**,
which the salience rung's diagnostic named independently.

### 3.3 THE TIE STATISTIC IS NOT COMPUTED BY THE SELECTOR UNDER TEST

The standing lesson in its exact form. The source rung pre-registered
`icg_ntied` as "the load-bearing diagnostic" and **its own §5 retracted that**:
it counts tied **orbit members**, not tied **regions**, is 1 by construction at
ρ=0, and is computed by the very `Argmax` it is supposed to diagnose.

**Two things follow, and both are done:**

1. **This rung's seed computes NO tie statistic at all.** The `Count` is
   **deleted** from the rules, not merely unused.
2. The tie statistic is **`v0_region_ties`** — the number of **REGIONS** tied at
   the maximum **under the INCUMBENT's (V0's) score**, computed **outside the
   graph**, and **held FIXED across all four arms**. For arms V1/V2/V3 it is
   therefore computed by a component that is *not* under test.

**The declared bound:** for **V0 itself** the statistic *is* self-computed. V0 is
the control, and this is stated rather than hidden.

**And the forced part is declared in advance, so it cannot be presented later as
a result:** exact ties essentially **cannot occur** for the continuous arms, so
"the tie rate falls to ~0 for V2/V3" is **FORCED BY CONSTRUCTION** and is not
evidence of anything. **The RISKED quantity is whether the ties are broken
CORRECTLY** — a verdict can shatter every tie and still pick wrong. Hence the
primary tie statistic below is *accuracy on the V0-tied subset*.

---

## 4. THE STATISTICS, EXACTLY

**Unit of analysis is the BASE FRAME (video) or the PHOTO (C3)** — never the
trial. The 16 regions of one frame share content and are not independent (§4).
95% t-CIs; `t(0.975, 49) = 2.0096`, `t(0.975, 23) = 2.0687`. Every arm-vs-V0
comparison is **paired by unit**.

- **M (misidentification)** = `true_achieves_max` = the fraction of A1 trials in
  which the true region attains the maximum score. Primary cell: **C2, Δ=1,
  NON-CUT stratum**. Reported for every (corpus, Δ, stratum).
- **T (tie)** = accuracy on the **V0-tied subset** (`v0_region_ties ≥ 2`) of C3
  at **d=0**, per arm, paired by photo against V0.
- **R (refusal)** = refusal rate by probe kind, plus A1 answer rate and accuracy
  on answered.

---

## 5. THE GATE IS A CONJUNCTION — all three clauses, or the arm does not pass

An arm **beats the incumbent** iff:

1. **MISIDENTIFICATION IMPROVES ON REAL MOTION.** Paired Δ`true_achieves_max`
   vs V0, on **C2, Δ=1, NON-CUT**, with the **95% CI excluding 0** and pointing
   up.
2. **TIES ARE BROKEN CORRECTLY ON SYNTHETIC.** Paired Δaccuracy vs V0 on the
   **V0-tied subset** of C3 d=0, **95% CI excluding 0**, pointing up.
3. **REFUSAL SURVIVES.** The abstention must be **ALIVE** — refusal rate on
   **G2t** (an independent noise draw) strictly greater than on **G1** (the
   identical frame), CI excluding 0 — **and** the A1 answer rate must be
   strictly inside (0, 1). **An arm that discriminates better by becoming more
   willing to answer has bought accuracy with false confidence**, and this arc
   has caught that pattern repeatedly (the histogram anchor scored 0.716
   accuracy at **exactly 0.0000** margin). Accuracy is therefore always reported
   **with** the answer rate.

**A clean negative is a full result (§7).** If no verdict improves clause 1
without costing clause 3, that is evidence the weakness lives in the **PROPOSAL**
layer rather than the verdict — which redirects the next rung and is worth more
than a marginal win.

### 5.1 THE REFUSAL FLOOR IS MEASURED, NOT CHOSEN (§13)

A group answers only if its score **strictly exceeds the best score THIS SAME ARM
achieves on the calibration noise probes (`G2c`) presented in the SAME
substrate**. **No constant is written anywhere in the seed.** The floor is the
system's own measured noise floor, per arm and per base frame — §13's own example
of a number that *falls out* rather than going in.

**The control is deliberately not a tautology.** `G2c` *defines* the floor, so of
course it does not exceed it; that would be a **dead instrument**. The measured
control is **`G2t`**, an **independent** noise draw from the same distribution
that did not define the floor, against **`G1`**, the identical frame, which must
be answered.

---

## 6. n, FIXED IN ADVANCE BY A POWER PILOT ON ALREADY-BURNED SEEDS (§3.3)

**PILOT — seeds `57000`-block ONLY** (the invariant-comparator rung's, already
burned; **no confirmatory seed consumed**). C2, 10 base frames, all four arms.

**Measured on the pilot** (`results/verdict_comparator_pilot.json`):

| quantity | measured |
|---|---|
| sd of the paired per-base-frame Δ`true_achieves_max` (arm − V0), C2 Δ=1 | **ssdq 0.0000, ssdg 0.1508, ncc 0.1250** |
| wall cost per base frame | **hamming 28.7 s; ssdq/ssdg/ncc 1.2 s** (the Dot arms are 24× cheaper) |
| score agreement with the outside-the-graph reference | **1920/1920 on every arm** |

**n is therefore fixed at N_BASE = 50 base frames per corpus** — the source
rung's n, which keeps every number directly comparable to it. At the pilot's
largest sd (0.151), `t(0.975,49)·sd/√50` gives a **minimum detectable paired
difference of 0.043**. **C3: 24 photographs**, also the source rung's. The
confirmatory run costs ≈65 minutes total, so n is not cost-bound.

**No re-runs, no sweeps.** Exactly the arms, corpora, Δ and displacements listed
here. The confirmatory run draws **only** from block 70000–70999.

### 6.1 DISCLOSURE — WHAT THE PILOT SHOWED ME BEFORE I COMMITTED THIS

**Reported because concealing it would be exactly the forking-paths garden §4
forbids, and because the source rung set the standard by disclosing its own.**

The pilot is a *power* pilot on burned seeds, but a power pilot necessarily shows
effect sizes, and this one did: **I have seen the direction and rough magnitude
of every arm on C2 before committing this file.**

**What this does and does not compromise.** §7's predictions were written
**before the pilot finished running** and are **left unedited** — including
prediction 3, which the pilot already contradicts (it predicted
V3 > V2 > V1 > V0; the pilot shows V2 ≈ V3 ≫ V1 ≈ V0 at Δ=1). Leaving a
prediction I already know to be wrong is the point of §3.7: a proviso that breaks
tells me what I did not understand. No metric, arm, stratification or decision
rule was chosen after seeing the pilot — all of §2–§5 was drafted before it
returned. **What it does mean is that I was not blind while writing §6, and the
confirmatory C2 result is a replication of a seen effect on fresh seeds rather
than a first look.** C1 and C3 were **not** piloted and are genuinely blind.

**One thing the pilot found that changes an ARM'S MEANING, and it is arithmetic
rather than a result.** V1's paired difference at Δ=1 was **exactly 0.0000 with
sd exactly 0.0000** — a zero-width interval, which is an instrument smell
(§12.3's order: verify the fact, then decide what it means). It is not a bug.
**Measured: at Δ=1, 100.00% of cell differences between consecutive frames are
≤1 quantizer level.** When every mismatch is exactly one level,
`SSD = #mismatches = 36 − covered_count`, so **−SSD is an exact affine function
of `covered_count` and the two rank IDENTICALLY.** V1 is therefore not a weak
arm — it is a **provably degenerate** one at short Δ, and the corresponding
fractions at Δ=5 (99.88%) and Δ=25 (87.71%) predict exactly where it starts to
deviate. **V1 is retained as a declared informative null**: it establishes that
ordinality has nowhere to express itself on a 4-level quantizer, so any gain must
come from dequantization rather than from the metric.

---

## 7. MY PREDICTIONS, STATED IN ADVANCE (§3.7)

| # | prediction | proviso that would break it |
|---|---|---|
| 1 | **V0 reproduces the source rung's Q2 arm** — C2 Δ=1 `true_achieves_max` within ~0.03 of 0.7975 | a different frame draw, or a Δ-pooling difference I have not noticed |
| 2 | **Clause 2 passes for V2 and V3 and is nearly free** — ties are a k=4 identifiability limit, and any continuous score dissolves them; the risked part is whether they break CORRECTLY, and I expect yes, because the tied tiles differ in the *unquantized* signal | if tied tiles are genuinely identical in raw grey too, accuracy on the tied subset stays at chance-among-tied and clause 2 FAILS |
| 3 | **Clause 1 is where this rung will be decided, and I predict V3 > V2 > V1 > V0 on C2 non-cut** | if misidentification is driven by *geometry* (real content change) rather than *photometry*, all three are null and the answer is "the proposal layer" |
| 4 | **The effect will be much smaller than the ×3 CI width** on C1 (cartoon), possibly null or negative, because cel-shaded flats give NCC nothing and `nflat` will be high there | — |
| 5 | **`nflat` materially higher on C1 than C2** | — |
| 6 | **Refusal will be alive for all four arms**, with G2t refusal > 0.9 and G1 refusal < 0.1 | a noise floor that lands above typical A1 scores would refuse nearly everything and clause 3 fails |
| 7 | **The cut stratum will show a much LOWER `true_achieves_max` for every arm**, and the arm differences there will be smaller than in the non-cut stratum — because no verdict can fix a signal discontinuity | if arms differ *more* across cuts, my model of the cut mechanism is wrong |
| 8 | **Score agreement with the outside-the-graph reference = 1.0000** on every arm and every trial | any disagreement is an instrument defect and blocks every number above |
| 9 | **The proposal hash is identical across all four arms** | if not, "only the verdict varies" is false and the rung is void |

**Where I expect to be wrong:** prediction 3 is the one I am least sure of. The
source rung's C2 degradation was measured *as a function of orbit radius*, which
is a distractor-inflation mechanism, not obviously a photometric one. If
misidentification is really distractor inflation, a better *metric* may not touch
it — and that is a genuine possibility this design is built to detect rather
than to obscure.

---

## 8. WHAT THIS RUNG CANNOT SHOW (§8), stated before the run

- **Toy resolution only.** 24×24 frames, 6×6 apertures. **Nothing here is a
  claim about video at any real resolution**; the measured scale wall
  (O(N^1.887)) is untouched.
- **Nothing is learned.** One frame's regions held for one comparison and
  discarded. No training, no codebook growth. **This measures a COMPARISON.**
- **Fixed aperture, not tracking.** No object correspondence, no segmentation,
  no proto-objects, no border-ownership.
- **Two episodes and 24 photographs.** Not a survey, and the corpora are never
  pooled.
- **k=4 and the 6×6 tiling are hand-set** (§13), inherited unchanged from the
  incumbent for comparability, and **not swept** — this rung's independent
  variable is the verdict. V2/V3 partially *bypass* k=4 rather than replacing
  it, and the quantizer still governs the proposal layer.
- **ρ=2 is held fixed**, so nothing here re-opens the orbit trade-off.
- **The affine-luminance quotient is in the encoding, not the graph** (§2.2).
- **§9:** the seed ships `verdict: ""` (matching no arm) and is **not** in the
  default boot set; the runner loads the manifest explicitly, so every committed
  result reproduces byte-identically.
