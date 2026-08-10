# DOES WATCHING VIDEO CHANGE THE CODEBOOK USEFULLY? — RESULTS

*Pre-registration: `VISION_VIDEO_ACCUMULATION_PREREG.md`, committed BEFORE any
headline number at **`f9ec89711e6815d176dacfeadff7ad664ef8508e`** (base
**`5428104a`**). Both endpoints pinned; no range ends at `HEAD`.*

**Engine (§10):** `25fa11652e83` @
`runners/dsl/python/substrate_rs/_native.abi3.so` — a **shared build from the
canonical tree, Rust source verified byte-identical**. **This rung adds NO Rust,
NO Term, NO seed rule and NO constant.** `git diff 5428104a -- runners/dsl/src`
is **empty** and `seeds/vision_identity_seam.json` is **byte-identical to its
`5428104a` blob** — both gated, both positive-controlled.
`tests/test_engine_provenance_migrated.py` + `test_provenance_endpoint_guard_migrated.py`
were run **as their own step before any number**: **630 passed, exit 0.**
**`data/`** symlinked, so the oracle's condition is the **222/0** one.
**Machine:** AMD Ryzen 5 9600X, 12 logical cores; ran solo. Wall-clock is a cost
only.
**Selectors (§12):** `scripts/video_accum_measure.py` (confirmatory) ·
`scripts/video_accum_analyse.py` (the pre-registered decision rule + two
**labelled post-hoc** diagnostics) · `scripts/video_accum_calibrate.py` and
`video_accum_pilot.py` (**pilots, burned seeds**).
**Raw:** `results/video_accum.json`, `results/video_accum_rows_{C1,C2}.json`,
`results/video_accum_analysis.json`, `results/video_accum_calibrate.json` — all
committed (275 KB).
**Seeds:** block **74000–74999** claimed and consumed. 74000/74001 growth,
74100+ uniform control, 74200+ cut-matched control, 74300+ shuffled order,
74400+ evaluation calibration, 74500+ refusal probes, **74900–74999 declared
burned pilots**.

---

## 0. THE HEADLINE, IN ONE PARAGRAPH

**The codebook does change, the change IS worth something — and the
conjunction FAILS on both corpora, with the most interesting failure being one
neither the brief nor I predicted: the system's own minting policy is eating
its own selection gain.** Watching 90 training frames grows **32 (C1) / 31 (C2)
identities from 1,440 observations** (2.2%), and on held-out frames the grown
codebook beats a **size-matched uniformly-drawn** one by **+0.0360 [+0.0086,
+0.0635] on C1** (CI-separated, PASS) and by **+0.0054 [−0.0062, +0.0171] on
C2** (NULL, FAIL) — **the corpora disagree, for the fifth time in this arc.**
**The decomposition is the result.** Against a control matched to the grown
arm's *frame* distribution (**RAND-CUTMATCHED** — same frames, random region),
selection is CI-separated positive on **both** corpora (**+0.0625 / +0.0475**);
but that cut-concentrated frame distribution is itself a **handicap**, with
**RAND-CUTMATCHED scoring CI-separated BELOW plain uniform on both corpora
(−0.0265 / −0.0420)**. **So MDL tile-selection is real and works everywhere,
and on C2 it buys back exactly what the system's cut-aligned minting policy
cost — netting nothing.** Minting replicates the seam rung's cut alignment
(**9.0× C1, 1.78× C2** near vs far from a cut) and **gate 2 fails on both**:
the mint rate falls in the mean (C2 0.864 → 0.136 per frame, first to last
quartile) but is **nowhere CI-separated**, because the burstiness that is the
prior rung's own finding destroys the power. **Gate 3 passes on both** —
refusal survives at K≈31 (NOISE 0.984/0.922, SHUFFLE 0.984/1.000, all above a
CONTROL of 0.016/0.000) and, unlike the seam rung, **BSDS now separates too**.
**And the sharpest single number is post-hoc and negative: C1's last three
mints — 9% of its final codebook — improve the best-match score of ZERO of 800
held-out observations, max improvement 0.000e+00 exactly.** At the tail, growth
is pure accretion, and it is measurable to the bit.

**Two things I got wrong, both reported as findings.** (1) **P4 is refuted, and
backwards**: I predicted GROWN ≈ RAND-CUTMATCHED, i.e. that the value was in
WHEN the system minted. Cut-matching is the **worst** arm on both corpora. (2)
**My own adapter audit was inert and I only found it by mutating it** — it was
a substring selector and passed a planted decision (§6.2).

---

## 1. WHAT WAS MEASURED, AND AGAINST WHAT

`seeds/vision_identity_seam.json` (the NCC seam), **byte-unchanged and armed**.
Not the stock sd loop — the seam rung measured that force-matching 64/64
value-shuffled tiles, and a system that cannot refuse cannot accumulate
meaningfully. That exclusion is a citation, not a new finding.

150 frames per corpus at 24×24 grey, 6×6 regions, k=4, split into contiguous
blocks: **90 training frames, 50 held-out frames, with a 1-frame guard band**
so no held-out frame is a training frame's temporal neighbour. Gated:
`train ∩ held = ∅`, guard verified, and **no mint comes from a held-out frame**.

At five checkpoints (10/25/45/65/90 training frames) three codebooks of
**identical size K** are evaluated in **freshly built, identically constructed
substrates**:

| arm | K entries are… |
|---|---|
| **GROWN** | the K MDL-gated mints |
| **RAND-UNIFORM** *(the primary control)* | K training observations drawn uniformly from everything seen so far |
| **RAND-CUTMATCHED** *(the decomposition)* | one per grown mint, **same frame**, random region |

Every evaluation pass is **frozen**: `refreeze()` demotes anything minted
during the pass and re-arms the measured floor, and **`assert_frozen()` requires
K and the floor to be bit-identical at the start and end of every pass** — it
raised zero times across 30 passes and is positive-controlled (§6.1).

## 2. THE MEASURE WAS GATED FIRST — AND IT CAUGHT A BLIND READ-OUT OF MINE

Pre-registration §2, quoted here because it is a result. The first calibration
pass reported **`accept = 1.0000` for an IDEAL codebook AND for a codebook of
pure noise** — delta `+0.0000`, zero variance, the §1.1 dead-arm signature
exactly. **The cause was my read-out, not the substrate:** `is_decide` writes
`is_held` / `is_novel`, `is_mint` then rewrites `is_novel` → `is_minted`, so
`status != "is_novel"` scores every *mint* as a *recognition*. Corrected to
`status == "is_held"`, and gated by
`test_a_minted_observation_does_not_read_as_recognised`, which asserts **both**
that the correct predicate says "not recognised" and that the incorrect one
says "recognised".

Corrected calibration (C1, n=50 held-out frames, K=37):

| read-out | IDEAL | NULL (noise codebook) | delta |
|---|---|---|---|
| accept rate | 0.9988 | 0.3137 | **+0.6850** |
| mean best-NCC | 0.8229 | 0.3660 | **+0.4568** |

**The accept rate's ceiling (0.9988) was declared in advance**, which is why
mean best-NCC is the primary read-out and why §3.2's accept-rate results are
read as ceiling-affected rather than re-cut afterwards.

## 3. GATE 1 — RECOGNITION ABOVE THE SIZE-MATCHED CONTROL. **C1 PASS, C2 FAIL.**

Unit = held-out frame, n=50, paired by frame, 95% paired t-CI. Never pooled.

### 3.1 THE PRIMARY READ-OUT — mean best-NCC on held-out frames

| corpus | cp | K | GROWN | UNIFORM | CUTMATCHED | **GROWN − UNIFORM** | sep |
|---|---|---|---|---|---|---|---|
| C1 | 10 | 5 | 0.5048 | 0.4306 | 0.4163 | **+0.0742 [+0.0611, +0.0873]** | ✅ |
| C1 | 25 | 14 | 0.6139 | 0.5690 | 0.5371 | **+0.0450 [+0.0111, +0.0789]** | ✅ |
| C1 | 45 | 22 | 0.6869 | 0.6601 | 0.6000 | +0.0268 [−0.0003, +0.0539] | ❌ |
| C1 | 65 | 29 | 0.8002 | 0.7199 | 0.7018 | **+0.0802 [+0.0586, +0.1018]** | ✅ |
| **C1** | **90** | **32** | **0.8002** | **0.7641** | **0.7377** | **+0.0360 [+0.0086, +0.0635]** | **✅** |
| C2 | 10 | 8 | 0.5822 | 0.5287 | 0.4779 | **+0.0535 [+0.0457, +0.0613]** | ✅ |
| C2 | 25 | 19 | 0.6704 | 0.7025 | 0.6170 | **−0.0321 [−0.0523, −0.0119]** | ❌ (negative) |
| C2 | 45 | 28 | 0.7332 | 0.7256 | 0.6850 | +0.0076 [−0.0062, +0.0214] | ❌ |
| C2 | 65 | 28 | 0.7332 | 0.7340 | 0.6700 | −0.0008 [−0.0212, +0.0196] | ❌ |
| **C2** | **90** | **31** | **0.7477** | **0.7422** | **0.7002** | **+0.0054 [−0.0062, +0.0171]** | **❌** |

**Gate 1 is scored at the final checkpoint, as pre-registered: PASS on C1,
FAIL on C2.** All three arms rise with K in both corpora (P1 right), which is
exactly why the size-matched control had to exist.

**Reported against myself:** C2 at cp=25 is **CI-separated NEGATIVE** — the
grown codebook is *worse* than an arbitrary one of the same size at that point
in training. That is not noise around zero; it is a real, if transient, deficit.

### 3.2 THE DECOMPOSITION — AND IT REVERSES MY PREDICTION

At the final checkpoint:

| contrast | C1 | C2 |
|---|---|---|
| **GROWN − CUTMATCHED** (selection, frame distribution HELD FIXED) | **+0.0625 [+0.0575, +0.0675]** ✅ | **+0.0475 [+0.0369, +0.0580]** ✅ |
| **CUTMATCHED − UNIFORM** (the cost of WHERE it minted) | **−0.0265 [−0.0513, −0.0017]** ✅ negative | **−0.0420 [−0.0552, −0.0288]** ✅ negative |
| GROWN − UNIFORM (the net, = gate 1) | +0.0360 ✅ | +0.0054 ❌ |

**Read it as a budget.** MDL tile-selection is worth **+0.06 / +0.05** and is
CI-separated on **both** corpora — the mechanism works everywhere. But the
system chooses to mint at cut-concentrated moments, and drawing from *that*
frame distribution costs **−0.027 / −0.042**. **On C1 selection more than pays
for the policy; on C2 it exactly cancels it.**

**P4 predicted GROWN ≈ RAND-CUTMATCHED — that most of the value was in WHEN the
system minted. It is refuted and the sign is backwards: cut-matching is the
WORST arm at every checkpoint on both corpora.** WHEN is a liability; WHICH is
the asset.

### 3.3 THE ACCEPT RATE — AND THE FLOOR IS WHY IT DISAGREES

| corpus | GROWN accept | UNIFORM accept | paired | GROWN floor | UNIFORM floor |
|---|---|---|---|---|---|
| C1 | 0.9850 | 0.8850 | **+0.1000 [+0.0683, +0.1317]** ✅ | 0.4496 | 0.4273 |
| C2 | 0.9738 | 0.9875 | **−0.0138 [−0.0212, −0.0063]** ✅ negative | 0.4973 | 0.3872 |

**On C2 the grown codebook ACCEPTS LESS than a random one, CI-separated** —
while scoring no worse on the primary read-out. The mechanism is visible in the
last two columns: **a grown codebook raises its own measured noise floor**
(0.4973 vs 0.3872), because a diverse codebook gives calibration noise more
things to correlate with. It is more conservative *because* it is better
stocked. This is the refusal/acceptance trade the seam rung priced at 12.5–23.4%
false-novel, showing up here as the co-primary disagreeing with the primary —
which is precisely why the two were pre-registered together and why the primary
was chosen to be floor-independent.

## 4. GATE 2 — DOES THE CODEBOOK STOP GROWING? **FAIL, BOTH CORPORA.**

| corpus | mints/frame by training quartile | Q1 | Q4 | CI-separated? |
|---|---|---|---|---|
| C1 | 0.227 / **0.773** / 0.318 / 0.136 | 0.2273 [−0.245, +0.700] | 0.1364 [−0.071, +0.344] | **❌** |
| C2 | **0.864** / 0.409 / 0.000 / 0.091 | 0.8636 [+0.162, +1.565] | 0.1364 [−0.019, +0.292] | **❌** |

**The direction is right on both and the separation is nowhere.** C2 falls
6.3× in the mean; C1 is not even monotone — it peaks in Q2, which is where its
cuts at frames 34 and 47 land. The CIs are enormous (sd 1.07 and 1.58 against
means of 0.23 and 0.86) **because minting is bursty, and the burstiness is the
seam rung's own finding**. A per-frame count of a bursty event over 22 frames
cannot resolve a 6× change. **Gate 2 fails, and it fails for a reason that is
structural rather than fixable by more frames of the same corpus** — a
successor wanting this gate needs a corpus with many more cuts, or a unit of
analysis that is not the frame.

**What IS established:** 32 and 31 identities from 1,440 observations
(**2.22% / 2.15%**), close to the seam rung's 1.4–1.9%, so the codebook is not
growing without bound in absolute terms. It is the *decline* that is undemonstrated.

**Cut alignment replicates** (the seam rung's D3, on a different frame set):
mints/frame within 3 frames of a cut vs far from one — **1.778 vs 0.198 = 9.0×
on C1**, **0.526 vs 0.296 = 1.78× on C2** (seam rung: 16.7× and 4.1×). Same
direction, same ordering between corpora, smaller magnitudes.

## 5. GATE 3 — REFUSAL SURVIVES. **PASS, BOTH CORPORA.**

n=64 per class, unpaired, at the final checkpoint in the frozen GROWN world.

| corpus | CONTROL | BSDS | NOISE | SHUFFLE | gate |
|---|---|---|---|---|---|
| C1 | 0.0156 [−0.016, +0.047] | **0.3594 [+0.239, +0.480]** ✅ | **0.9844 [+0.953, +1.016]** ✅ | **0.9844 [+0.953, +1.016]** ✅ | **PASS** |
| C2 | **0.0000** [0, 0] | **0.1719 [+0.077, +0.267]** ✅ | **0.9219 [+0.854, +0.989]** ✅ | **1.0000** [1, 1] ✅ | **PASS** |

**Recognition was not bought by permissiveness** — the failure mode the stock
loop demonstrated. And **BSDS now separates on both corpora**, which the seam
rung failed on both; the plausible reason is codebook size (K≈31 here against
that rung's 137–170 at the point of measurement) and a fresh evaluation
substrate, but **this rung did not test that and does not claim it**.

**Two caveats, quoted rather than buried.** C2's **CONTROL and SHUFFLE both have
ZERO VARIANCE**, so C2's separations are against a **point interval** — the
instrument smell the salience rung named and the seam rung was caught by. And
the **false-novel rate on genuine held regions collapsed to 0.0156 / 0.0000**
from the seam rung's 0.125 / 0.234; that is a large change in the seam's
headline cost, it is consistent with the smaller codebook, and **it is an
observation from a different protocol, not a refutation of that rung's number**.

## 6. THE CONJUNCTION

| corpus | gate 1 | gate 2 | gate 3 | **CONJUNCTION** |
|---|---|---|---|---|
| C1 | **PASS** | FAIL | **PASS** | **FAIL** |
| C2 | FAIL | FAIL | **PASS** | **FAIL** |

**The conjunction fails on both corpora and is reported as failed.** No clause
was re-cut after looking (§5).

### 6.1 THE POST-HOC DIAGNOSTIC THAT IS THE SHARPEST NUMBER IN THE RUNG

**NOT pre-registered. Labelled post-hoc. It did not change any verdict.**

C1's cp=65 and cp=90 read-outs are **identical to full float precision** across
all 50 held-out frame means, despite K going **29 → 32**. That is a smell, so it
was checked rather than explained. **D2 re-derives it in numpy, entirely outside
the graph**: adding C1's last three mints improves the best-match NCC of
**0 of 800 held-out observations**, **max improvement `0.000e+00` exactly**. The
same check reproduces the graph's own mean to six decimals
(**0.800155 = 0.800155**) — an independent agreement check on the whole
measurement path.

**C1's final 9% of codebook growth contributes literally nothing to held-out
recognition.** That is what "accretes without accumulating" looks like when it
is measured to the bit, and it is the cleanest evidence in this rung that
codebook growth and codebook usefulness are different quantities.

### 6.2 THE INSTRUMENT DEFECT I FOUND BY MUTATING MY OWN GATE

`test_the_adapter_takes_no_decision_over_graph_state` was a **substring audit**,
and it **PASSED a planted decision**: the source `a["is_max"] > b` does not
contain the literal `"is_max >"`, because `"]` sits between. This is §12's *"a
selector that matches by substring is not a selector"* landing on my own gate.
Rewritten as an **AST walk over `Compare` nodes**, positive-controlled with the
exact mutation that defeated the substring version
(`test_the_adapter_audit_is_ABLE_to_fail`). It was then **narrowed, not
weakened**: `x is not None` presence guards are exempt because they are not
decisions over the verdict's *value*; ordering and equality on it are not.

**Found only because I mutated a green gate.** It had never been able to fail.

## 7. THE CUT QUESTION, ANSWERED — AND THE ANSWER IS NOT "DEAD ENTRIES"

The brief's specific hazard: the mints are cut-aligned, so they may encode
discontinuity artifacts rather than content. Measured three ways.

**(a) Are cut-driven entries DEAD?** No. Per-entry usage on held-out frames,
W=3 (the seam rung's inherited window, declared in advance):

| corpus | dead near-cut | dead far-from-cut | total dead |
|---|---|---|---|
| C1 | 0.0625 [−0.071, +0.196] (1/16) | 0.1875 [−0.027, +0.402] (3/16) | **4/32** |
| C2 | 0.3000 [−0.046, +0.646] (3/10) | 0.0476 [−0.052, +0.147] (1/21) | **4/31** |

**87–88% of all entries are used**, and the corpora **disagree in sign** on
which stratum is deader, neither CI-separated. **P6 was right: cut-minted
entries are not dead.**

**(b) Are they WORTH LESS?** Consistently yes in the mean, nowhere
CI-separated:

| corpus | usage near-cut | usage far-from-cut | continuous (usage vs frames-to-cut) |
|---|---|---|---|
| C1 | 18.31 [12.41, 24.22] | 30.94 [7.76, 54.11] | pearson **+0.183**, spearman +0.056 |
| C2 | 11.90 [3.63, 20.17] | 31.43 [16.12, 46.74] | pearson **+0.319**, spearman +0.316 |

Far-from-cut entries are used **1.7× / 2.6×** more, and the continuous
correlation is positive on both — but the far-stratum CIs are enormous (usage is
heavy-tailed) and **the separation fails on both corpora**. Direction consistent,
strength unproven.

**(c) THE ARM THAT ACTUALLY ANSWERS IT is RAND-CUTMATCHED (§3.2), and it is
CI-separated on both corpora.** Holding the frame distribution fixed at the
grown arm's own cut-concentrated one costs **−0.027 / −0.042** against uniform.
**So the cut-aligned minting policy IS a real cost — not because its entries are
dead, but because cut-adjacent frames are a worse place to sample the corpus
from.** That is a sharper and more useful answer than "dead entries", and it is
the one the pre-registered control was built to give.

## 8. ORDER — NO CONSISTENT CURRICULUM EFFECT (P8 right, with a confound)

| corpus | K in-order | K shuffled | shuffled − in-order (mean best-NCC) |
|---|---|---|---|
| C1 | 32 | 34 | **+0.0228 [+0.0078, +0.0378]** ✅ |
| C2 | 31 | 26 | −0.0090 [−0.0307, +0.0128] (null) |

**The two corpora take opposite signs and the comparison is NOT size-matched** —
shuffling changed K itself (32→34, 31→26), so the C1 "effect" is confounded with
a bigger codebook and is not evidence of a curriculum. **The honest reading is
that no order effect is demonstrated in either direction**, and that a clean
version of this test needs the shuffled arm truncated to matched K, which this
rung did not do.

## 9. PREDICTIONS, SCORED

| # | prediction | outcome |
|---|---|---|
| P1 | all three arms rise with K | **RIGHT**, every arm, both corpora |
| P2 | GROWN beats RAND-UNIFORM on mean best-NCC at the final checkpoint, both corpora | **HALF WRONG** — C1 +0.0360 ✅, C2 +0.0054 NULL |
| P3 | accept-rate contrast NULL or smaller, from the ceiling | **WRONG, and more interesting than predicted** — C1 is LARGER (+0.1000), C2 is CI-separated NEGATIVE. The driver is floor movement, not the ceiling |
| P4 | GROWN ≈ RAND-CUTMATCHED, both > UNIFORM | **REFUTED, SIGN BACKWARDS** — CUTMATCHED is the WORST arm at every checkpoint on both corpora |
| P5 | mint rate declines, weakly, confounded by cuts | **RIGHT IN SUBSTANCE, gate FAILS** — falls in the mean on both, CI-separated on neither, C1 not even monotone |
| P6 | cut-minted entries are NOT dead | **RIGHT** — 4/32 and 4/31 dead overall; corpora disagree on which stratum |
| P7 | refusal survives on NOISE/SHUFFLE, FAILS on BSDS, CONTROL stays materially above zero | **HALF WRONG in the useful half** — NOISE/SHUFFLE right, **BSDS PASSES on both** (the seam rung failed both), and CONTROL collapsed to 0.0156/0.0000 |
| P8 | no curriculum effect | **RIGHT**, and the arm is confounded by K (§8) |

**2 right, 2 half, 1 right-in-substance, 1 refuted, 1 right-with-a-confound.**
**P4 is the most useful miss** — it was the prediction I flagged in advance as
held most weakly and whose refutation would be most informative, and refuting it
is what turned "the mints are cut-aligned" from a worry into a **priced cost**.

## 10. BOUNDS ON EVERYTHING ABOVE (§8)

- **This is a demonstration that accumulation does or does not occur on this
  corpus at this resolution. It is NOT a claim about learning at scale.**
  24×24 grey, 6×6 regions, k=4, **two episodes of two series**, 150 frames each,
  90 training / 50 held-out.
- **The conjunction FAILS on both corpora.** The positive part of the result is
  one clause on one corpus, plus a decomposition that is CI-separated on both.
- **Regions are an adapter-chosen grid.** Nothing routes through proto-objects,
  border ownership or segmentation, and **no object label exists anywhere in the
  measurement**. "Recognition" here means *region identity against a held
  codebook* and nothing more.
- **Frames are not independent.** Blocks of 10 consecutive frames are heavily
  autocorrelated, so n=50 overstates the effective n. **No p-value is quoted
  anywhere** — CIs only, unit at the frame.
- **Gate 2 is under-powered by construction** (§4) and its failure should not be
  read as "the mint rate is constant"; it is "the decline is not resolvable at
  this n against this burstiness".
- **C2's refusal separations are against zero-variance point intervals** (§5).
- **The cut-usage stratification is not CI-separated on either corpus** (§7b);
  only the RAND-CUTMATCHED arm carries that conclusion.
- **The order arm is not size-matched** (§8), so it tests nothing cleanly.
- **The three codebook arms share the encoder, the evaluation machinery and the
  calibration draws.** That is the intended contrast and also its limit —
  nothing here tests a different featureset, and the identity-seam rung's
  measured false-novel cost is inherited, not re-litigated.
- **The BSDS improvement and the collapsed false-novel rate are observations
  from a different protocol than the seam rung's**, and are NOT offered as
  refutations of that rung's numbers.
- **§9:** no default moved, no existing seed was edited (gated, byte-hash
  against `5428104a`), no Rust was touched (gated, empty diff).

## 11. VERIFICATION

| check | result | exit |
|---|---|---|
| `tests/test_engine_provenance_migrated.py` + endpoint guard, **own step, before any number** | **630 passed** | **0** |
| `bash scripts/rung7_vision_bench.sh` **before** the rung | **222 passed** (149.1 s) | **0** |
| `bash scripts/rung7_vision_bench.sh` **after** the rung | **222 passed** | **0** |
| `tests/test_video_accumulation_migrated.py` | **9 passed** | 0 |
| freeze gate `assert_frozen()` across 30 evaluation passes | **never raised** | — |
| freeze gate positive control (no `refreeze()`) | **raises, and the control asserts growth first** | — |
| adapter audit positive control (planted `a["is_max"] > b`) | **caught** | — |
| seed byte-hash vs `5428104a`, mutation-tested | **identical; a one-byte edit turns it RED** | — |
| `git diff 5428104a -- runners/dsl/src` | **empty** | — |
| D2 numpy re-derivation vs the graph's own mean | **0.800155 = 0.800155** | — |

## 12. WHAT THE NEXT RUNG SHOULD PRE-REGISTER AGAINST

Ranked by what this evidence supports:

1. **MINT SOMEWHERE ELSE.** This rung priced the cut-aligned minting policy at
   **−0.027 / −0.042** against uniform sampling, CI-separated on both corpora.
   The sharp, cheap, pre-registrable follow-up is a minting policy that
   **abstains at a marked cut** — the machinery already exists next door in
   `seeds/vision_cut_abstention.json` — and the prediction is that GROWN −
   UNIFORM rises by roughly the cut-matched deficit, taking C2 off its null.
   **This is the one I would run first**, and note it is a prediction with a
   number attached in advance.
2. **GATE 2 NEEDS A DIFFERENT UNIT.** Mints per frame cannot resolve a 6×
   decline against burst variance. Pre-register **observations-between-mints**
   (a waiting time, which is what a saturating process actually makes
   monotone) on a corpus with enough cuts to power it.
3. **THE FLOOR RISES WITH CODEBOOK DIVERSITY** (§3.3) — a grown codebook is
   more conservative than a random one of the same size, CI-separated on C2.
   That is a mechanism, it was not predicted, and it is measurable directly:
   does the measured floor track codebook diversity rather than codebook size?
4. **SIZE-MATCH THE ORDER ARM** (§8), which this rung did not.

**What should NOT be pre-registered:** anything of the form *"the substrate
learns from video."* One clause of a three-clause conjunction passed, on one of
two corpora, at 24×24, with no object label anywhere in the measurement, and the
system's own minting policy measurably costs it most of what its selection
earns.
