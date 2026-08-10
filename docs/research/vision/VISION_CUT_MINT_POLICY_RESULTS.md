# DOES ABSTAINING FROM MINTING AT A MARKED CUT BUY BACK THE POLICY DEFICIT? — RESULTS

*Pre-registration: `VISION_CUT_MINT_POLICY_PREREG.md`, committed BEFORE any
headline number at **`9c0ac19de79eceb0425d99a699cd6710c88761b4`** (base
**`17cb3f3d`**). Mechanism committed at **`f37562c8`**, also before any number.
Both endpoints pinned; no range ends at `HEAD`.*

**Engine (§10):** `25fa11652e83` @
`runners/dsl/python/substrate_rs/_native.abi3.so` — a **shared build from the
canonical tree, Rust source verified byte-identical**. **This rung adds NO
Rust, NO Term and NO constant.** `git diff 17cb3f3d -- runners/dsl/src` is
**empty**, and `seeds/vision_identity_seam.json` + `seeds/vision_cut_abstention.json`
are **byte-identical to their `17cb3f3d` blobs** — all three gated.
`tests/test_engine_provenance_migrated.py` +
`test_provenance_endpoint_guard_migrated.py` were run **as their own step
before any number: 631 passed, exit 0.** `data/` symlinked, so the oracle's
condition is the **222/0** one.
**Machine:** AMD Ryzen 5 9600X, 12 logical cores; ran solo.
**Selectors (§12):** `scripts/cut_mint_measure.py` (confirmatory) ·
`scripts/cut_mint_analyse.py` (the pre-registered decision rule, applied
mechanically, with every predicted value read from the pre-registration) ·
`scripts/cut_mint_diagnose.py` (**labelled post-hoc**, changes no verdict).
**Raw:** `results/cut_mint.json`, `cut_mint_analysis.json`,
`cut_mint_diagnose.json` — all committed (69 KB).
**Seeds:** block **75000–75999**. 75000/75001 growth, 75100+ uniform control,
75200+ subsample control, 75400+ evaluation calibration, 75900+ declared burned
pilots (the gates' synthetic corpus).

---

## 0. THE HEADLINE, IN ONE PARAGRAPH

**The inherited prediction FAILS on both corpora, my own prediction lands
inside its tolerance on both AND IS RIGHT FOR THE WRONG REASON, and the
mechanism does something neither prediction described: it does not DELETE the
cut-aligned burst, it DEFERS it by one frame.** Abstention is CI-separated
**positive on both corpora under BOTH pre-registered size-matches** —
**+0.0507 / +0.0236** against a uniformly-subsampled non-abstaining codebook
and **+0.0138 / +0.0127** against a prefix-truncated one — which makes this the
first thing in this video line to be CI-separated positive on **both** corpora
for the mechanism itself. But the NET against a uniform control is **+0.0272
[+0.0049, +0.0494] on C1 (separated) and +0.0001 [−0.0340, +0.0341] on C2
(NULL)**, against a predicted **+0.0625 / +0.0474**. **C2 does not come off its
null.** The reason is arithmetic and was declared in advance as a proviso:
`C-A = C-B + C-C`, and the non-abstaining baseline at this K is itself
**−0.0235 below uniform on both corpora** — the incumbent's +0.0360 at K = 32
does not survive to K = 23. **So the decomposition's arithmetic was right and
its K-SCOPE was not.** The false-positive price is measured and not netted: at
corpus level the graph's marked set is **exactly** the committed reference
(`[34, 47, 79]` / `[23, 85, 143]`, **zero** false positives), but on a cut-free
run of training frames the same marker fires **2/17 (C1) and 4/17 (C2)** times
at magnitudes **14× below a real cut**, and those marks **would veto 2 and 5
good mints** — the inherited arm-4 defect, priced. **And the sharpest number is
post-hoc: my PRIMARY size-match crippled its own control** — the entry it
happened to discard improves **112 of 800** held-out observations, while the
secondary discarded one improving **0 of 800**, which is the whole 3.7× spread
between them.

**Three things I got wrong, all reported as findings.** (1) **My
f-proportionality model is REFUTED**: I predicted the isolated policy effect at
+0.0050 / +0.0081 and measured +0.0507 / +0.0236 — because the model assumed
the policy DELETES entries and it RELOCATES them. (2) **I predicted C-B would
be UNPOWERED on C1**; it is CI-separated with a half-width of ±0.006, because I
sized the instrument from the incumbent's UNPAIRED CI and this contrast is
paired on nearly-identical codebooks. (3) **My own reproduction check was
invalid** — it compared against the incumbent's *seed-74000* codebook, and the
real check (§2.1) had to be run separately.

---

## 1. WHAT WAS MEASURED, AND AGAINST WHAT

`seeds/vision_identity_seam.json` (the NCC seam) and
`seeds/vision_cut_abstention.json` (the cut marker), **both byte-unchanged**,
plus **one new rule**: `cm_abstain_mint`
(`seeds/vision_cut_mint_policy.json`). An Observation the seam has declared
`is_novel`, whose frame is incident on a step `ca_mark_cut` marked, does not
mint. The threshold is `ca_otsu`'s, derived from the sequence's own
distribution; **no numeric threshold and no window appears anywhere** (gated:
the policy seed's numeric literals are a subset of `{0, 0.5, 1}`, with a
non-vacuity assertion beside it).

150 frames per corpus at 24×24 grey, 6×6 regions, k = 4, split into the
incumbent's contiguous blocks: **90 training, 50 held-out, 1-frame guard band.**
Four codebooks of **identical size K = K_a** are evaluated in freshly built,
frozen substrates by **the incumbent's `eval_pass`, imported verbatim**, so the
UNIFORM arm is directly comparable to its published one.

| arm | K_a entries are… | C1 | C2 |
|---|---|---|---|
| **ABSTAIN** | the mints the abstaining policy made | 23 | 25 |
| **NOABSTAIN_SUB** *(primary size-match)* | K_a of the K_n non-abstaining mints, uniform without replacement | 23 of 24 | 25 of 27 |
| **NOABSTAIN_PRE** *(secondary, declared in advance)* | the first K_a in training order | 23 of 24 | 25 of 27 |
| **UNIFORM** | K_a training observations drawn uniformly | 23 | 25 |

**The policy is armed during GROWTH ONLY**; evaluation substrates carry no
`FrameStep` and a disarmed `CutParams`.

### 1.1 A FACT THAT FELL OUT AND IS WORTH RECORDING: K IS CALIBRATION-SEED SENSITIVE

The incumbent grew **32 (C1) / 31 (C2)** identities at calibration seed 74000.
At seed **75000/75001** the *same code on the same frames* grows **24 / 27**.
Eight `G2c` noise probes set the measured floor, the floor sets what counts as
novel, and a different noise draw moves the final codebook by **33% on C1**.
Nothing here is wrong — but **codebook size is not a property of the corpus
alone**, and any cross-rung comparison of K (or of a contrast at a given K) has
to carry the calibration seed with it.

## 2. THE MEASURE AND THE MECHANISM WERE GATED FIRST (§1)

13 gates, `tests/test_cut_mint_policy_migrated.py`, **two positive-controlled**:

| gate | result |
|---|---|
| `git diff 17cb3f3d -- runners/dsl/src` | **empty** |
| seam + cut-abstention seeds byte-identical to `17cb3f3d` | **identical** |
| policy seed's numeric literals ⊆ {0, 0.5, 1}, with non-vacuity | **passes** |
| policy seed ships disarmed (§9) | **passes** |
| adapter takes no decision in its WRITE PATH (AST walk over `Compare`) | **passes** |
| **that audit is ABLE to fail** (planted `self.s.node(0)["is_max"] > 0.5` inside `present_at`) | **caught** |
| the split seam is the seam verbatim (both halves reconstitute the file's rules body-for-body) | **passes** |
| `is_decide` < `cm_abstain_mint` < `is_mint` in install order | **passes** |
| disarmed growth ≡ incumbent `AccumWorld`, mint for mint | **passes** |
| armed policy declines exactly the 16 regions of the incident frame | **passes** |
| **that gate is ABLE to fail** (the DISARMED world DOES mint there) | **confirmed** |
| the policy leaves `identified_as` intact | **passes** |

**THE INSTRUMENT DEFECT I INHERITED AND HAD TO DESIGN AROUND, found by
measurement rather than by reading.** `Substrate::run_rules` does **not**
break on progress the way `rewrite::run_rules` does — it schedules **every
dirty rule in one pass, in index order, with no break**. So `is_decide`
(writing `status = "is_novel"`) and `is_mint` (reading it) fire in the **same
pass**, and a rule at any index below `is_decide` sees the pre-decision state
while one above `is_mint` arrives after the codebook already grew. The first
build of this rung installed the policy after the seam, watched it never fire,
and only then read the scheduler. **The only position that works is between
them**, so the adapter installs the seam's own manifest in two halves and puts
the policy in the gap — re-authoring nothing.

### 2.1 MY REPRODUCTION CHECK WAS INVALID, AND I REPORT IT AS AN ERROR

`cut_mint_measure.py` records `reproduces_incumbent_growth`, comparing the
disarmed arm's mints against `results/video_accum.json`. It came back **False
on both corpora**, and **the field is meaningless**: the incumbent's committed
mint list was grown at calibration seed 74000 and mine at 75000, so the two
were never going to agree (§1.1). **The check that matters was run separately
and PASSES:** the incumbent `AccumWorld` and the disarmed `CutMintWorld`, at
**the same seed**, on **the same real frames**, grow **identical** codebooks —
**24 = 24 mint-for-mint on C1 and 27 = 27 on C2**. That is what licenses
attributing every difference below to the policy. The invalid field is left in
the raw JSON rather than quietly deleted.

## 3. THE CONTRASTS. **INHERITED PREDICTION: NOT CONFIRMED, BOTH CORPORA.**

Unit = held-out frame, n = 50, paired by frame, 95% paired t-CI. Never pooled.
Primary read-out = mean best-NCC (`is_max`). `✅` = CI excludes 0.

| id | contrast | **C1** | **C2** |
|---|---|---|---|
| **C-A** | **ABSTAIN − UNIFORM** *(carries the inherited prediction)* | **+0.0272 [+0.0049, +0.0494]** ✅ | **+0.0001 [−0.0340, +0.0341]** ❌ NULL |
| **C-B** | **ABSTAIN − NOABSTAIN_SUB** *(the policy, isolated; primary size-match)* | **+0.0507 [+0.0444, +0.0569]** ✅ | **+0.0236 [+0.0171, +0.0300]** ✅ |
| **C-C** | NOABSTAIN_SUB − UNIFORM *(gate 1 re-measured at K_a)* | −0.0235 [−0.0498, +0.0028] ❌ | −0.0235 [−0.0606, +0.0135] ❌ |
| **C-D** | ABSTAIN − NOABSTAIN_PRE *(secondary size-match)* | **+0.0138 [+0.0088, +0.0187]** ✅ | **+0.0127 [+0.0060, +0.0194]** ✅ |

Absolute means, all arms at the common K:

| corpus | K | ABSTAIN | NOABSTAIN_SUB | NOABSTAIN_PRE | UNIFORM |
|---|---|---|---|---|---|
| C1 | 23 | **0.7364** | 0.6857 | 0.7226 | 0.7092 |
| C2 | 25 | **0.7090** | 0.6854 | 0.6963 | 0.7089 |

### 3.1 PREDICTED VERSUS MEASURED, WITH BOTH NUMBERS QUOTED

| corpus | **inherited prediction** | **my prediction** | **MEASURED** | err vs inherited | err vs mine |
|---|---|---|---|---|---|
| **C1** | **+0.0625** | **+0.0410** | **+0.0272** | **−0.0353** ✗ | −0.0138 ✓ |
| **C2** | **+0.0474**, CI excludes 0 | **+0.0135**, stays NULL | **+0.0001**, NULL | **−0.0473** ✗ | −0.0134 ✓ |

**Decision rule 1 (fixed in advance, ±0.02 and C2's CI excluding 0): the
INHERITED PREDICTION IS NOT CONFIRMED on either corpus.** It over-predicts by
2.3× on C1, and on C2 it predicts a CI-separated +0.0474 where the measurement
is +0.0001 with the CI straddling zero. **My prediction is within tolerance on
both, and I called C2's null correctly.**

### 3.2 BUT I WAS RIGHT FOR THE WRONG REASON, AND THE ARITHMETIC PROVES IT

`C-A = C-B + C-C`, exactly, on both corpora
(0.0507 − 0.0235 = 0.0272; 0.0236 − 0.0235 = 0.0001). My +0.0410 / +0.0135 was
built from **a small policy effect on top of the incumbent's +0.0360 / +0.0054
baseline**. What actually happened is **a large policy effect on top of a
baseline that collapsed to −0.0235**. Two errors of opposite sign, cancelling.
**Reported against myself:** a prediction that lands inside tolerance through
cancelling errors is not evidence the model is right, and this one is not.

**The declared proviso is what bit.** The pre-registration recorded that the
incumbent's GROWN − UNIFORM is **not K-invariant** (+0.0742 at K=5, +0.0450 at
K=14, **+0.0268 at K=22**, +0.0802 at K=29, +0.0360 at K=32 on C1) and that
this is *"precisely why C-C re-measures the incumbent's contrast at K_a inside
this run."* At K = 23–25, **C-C is negative in the mean on both corpora and
separated on neither** — the size-matched selection advantage the incumbent
reported at K = 32 is simply not there at this K. **That is the honest
explanation for C2 staying null, and it is a fact about the baseline, not about
abstention.**

### 3.3 THE TWO SIZE-MATCHES DISAGREE BY 3.7×, AND THE POST-HOC DIAGNOSTIC SAYS WHY

**NOT pre-registered. Labelled post-hoc. It changes no verdict.**

C-B (+0.0507) and C-D (+0.0138) are the same policy under two size-matches that
were **both** declared in advance. With `K_n − K_a = 1` on C1, "size-matching"
the non-abstaining arm is a **one-entry lottery**, so D1 priced the entry each
one discarded by leave-one-out on the held-out observations:

| corpus | SUB discarded | improves | PRE discarded | improves |
|---|---|---|---|---|
| **C1** | (frame 0, region 3) | **112 / 800** | (frame 143, region 6) | **0 / 800** |
| C2 | (0,15) + (24,1) | 65 / 800 | (65,8) + (147,14) | 46 / 800 |

**On C1 the PRIMARY control was crippled by its own draw** — it threw away an
entry that improves 112 held-out observations, while the secondary threw away a
tail entry that improves **exactly zero** (the incumbent's "accretes without
accumulating" signature, reproduced at a different K and a different seed).
**So C1's +0.0507 is inflated and the conservative reading of the policy effect
is C-D's +0.0138.** On C2 the two draws are comparable (65 vs 46) and the
+0.0236 / +0.0127 spread is only partly explained.

**What survives regardless of which size-match you take:** the sign, on both
corpora, under both, all four CI-separated. **The defensible magnitude is a
bracket — [+0.0138, +0.0507] on C1 and [+0.0127, +0.0236] on C2 — not a point.**
The primary is reported as the primary because it was pre-registered as such;
swapping them now would be §5.

### 3.4 THE ACCEPT RATE — AGREES THIS TIME, AND THE FLOORS SAY WHY IT MIGHT NOT MEAN MUCH

| corpus | ABSTAIN | UNIFORM | paired | ABSTAIN floor | NOABSTAIN floor | UNIFORM floor |
|---|---|---|---|---|---|---|
| C1 | 0.9050 | 0.8600 | **+0.0450 [+0.0244, +0.0656]** ✅ | 0.4565 | **0.4565** | 0.3591 |
| C2 | 0.9788 | 0.8588 | **+0.1200 [+0.0731, +0.1669]** ✅ | 0.4301 | 0.4497 | 0.4378 |

The incumbent's finding replicates: **a grown codebook raises its own measured
noise floor** (0.4565 vs 0.3591 on C1). **The co-primary AGREES with the
primary on C1 and DISAGREES on C2**, where accept is +0.1200 CI-separated while
the primary is +0.0001. C2's ABSTAIN floor is **lower** than both comparators
(0.4301 vs 0.4497 / 0.4378), so **at least part of C2's accept gain is floor
movement, not codebook quality** — which is exactly why the floor-independent
read-out was made primary in advance, and why no accept number here is offered
as a policy result.

**One clean sub-result:** on C1 the ABSTAIN and NOABSTAIN floors are
**identical to four decimals (0.4565)**, so **C1's C-B is not floor-confounded
at all.**

## 4. WHAT THE MECHANISM ACTUALLY DOES: DEFERRAL, NOT DELETION

**Post-hoc (D2), labelled, and it refutes my own model.**

| corpus | direct vetoes | at frame | same region re-minted later | the abstaining arm's own new mints |
|---|---|---|---|---|
| **C1** | **4** | 35 (cut step 34) | **4 / 4** | (36,1) (36,9) (81,1) |
| **C2** | **9** | 24 (cut step 23) | **8 / 9** | **(25,0) (25,1) (25,4) (25,6) (25,10) (25,13) (25,15)** + (51,2) |

**Look at C2's right-hand column.** Seven regions are declined at frame 24 and
**the same seven regions mint at frame 25** — one frame later, past the
discontinuity. C1 does the same thing from frame 35 to frame 36. **The policy
does not remove the cut-aligned burst; it slides it one frame off the cut.**

That is why K barely moves (24 → 23, 27 → 25) despite 4 and 9 vetoes, which is
**P4 confirmed**. And it is why **my f-proportionality prediction is refuted**:
I modelled the policy as *deleting* a fraction f of entries and therefore
recovering f × the deficit. It **substitutes** them instead, and a codebook of
the same size built one frame off the cut is measurably better than one built
on it. **The mechanism is better than my model of it, and the model is the
thing that was wrong.**

## 5. THE FALSE-POSITIVE COST — MEASURED SEPARATELY, NEVER NETTED (§6 of the prereg)

### 5.1 AT CORPUS LEVEL THERE ARE NO FALSE POSITIVES

| corpus | graph threshold | graph-marked steps | committed reference | FP | missed |
|---|---|---|---|---|---|
| C1 | 11.0637 | **[34, 47, 79]** | [34, 47, 79] | **0** | **0** |
| C2 | 4.4577 | **[23, 85, 143]** | [23, 85, 143] | **0** | **0** |

**P5's first clause is right**: over the full 149-step sequence the marker
reproduces the committed partition exactly, so **every mint the policy vetoed
was vetoed by a TRUE cut**, and the cost below is charged to the policy, not to
the marker.

### 5.2 WHAT THE VETOED MINTS WERE WORTH — THE GOOD-MINTS-LOST NUMBER

Leave-one-out in numpy, outside the graph, on the 800 held-out observations,
for every mint present in NOABSTAIN and absent from ABSTAIN:

| corpus | entries | held-out observations improved | entries improving NOTHING | max single drop |
|---|---|---|---|---|
| **C1** | 4 | **101 / 800** | **1** — (35,5), `0.000e+00` exactly | 0.652 |
| **C2** | 10 | **150 / 800** | 0 | 0.512 |

**P6 is right: the discarded mints are not worthless.** Abstention throws away
entries that were the best match for 101 and 150 held-out observations
respectively. **This is a trade, not a free win** — and the reason the net is
still positive is §4: the discarded entries are replaced by deferred ones.
**One C1 entry improves exactly zero observations**, the incumbent's
tail-accretion signature turning up again at a different K and seed.

### 5.3 THE COUNTERFACTUAL — WHAT THE MARKER COSTS WHERE ARM 4 SHOWED IT BREAKS

The same graph marker on the **longest contiguous cut-free run of training
frames** (51–68, 17 steps, both corpora):

| corpus | threshold | **marked** | their magnitudes | a real cut is | **would veto** |
|---|---|---|---|---|---|
| **C1** | 0.7749 | **2 / 17 (11.8%)** | 2.82, 3.08 | **≥ 43.52** | **2** — (51,2) (51,10) |
| **C2** | 2.3269 | **4 / 17 (23.5%)** | 2.61 – 3.15 | **≥ 44.75** | **5** — (62,1) (64,0) (64,3) (64,11) (65,8) |

**The inherited defect reproduces exactly as the cut-abstention rung described
it.** Handed 17 steps with no discontinuity in them, Otsu splits anyway and
marks the top of the distribution at magnitudes **14× below a real cut**. The
rates (11.8% / 23.5%) sit inside the bracket arm 4 measured on longer runs
(7.2% / 36.1%). **So the price of deploying this policy on cut-free footage is
2–5 vetoed good mints per 17 steps**, and that price is stated here rather than
subtracted from anything.

**P5's second clause is WRONG on magnitude** — I predicted ≥5 (C1) and ≥20 (C2)
marks, quoting arm 4's counts off runs of 69 and 61 steps and applying them to
a run of 17. **The rates transfer; the counts I quoted did not, and I should
have converted them.**

## 6. MY PREDICTIONS, SCORED (§3.7)

| # | prediction | outcome |
|---|---|---|
| **P1** | the INHERITED one: C-A = +0.0625 / +0.0474, C2 off its null | **NOT CONFIRMED, both corpora.** −0.0353 and −0.0473 outside the ±0.02 tolerance; C2's CI straddles zero. I predicted it would fail and it did. |
| **P2** | mine: C-A = +0.0410 / +0.0135, C2 stays NULL | **WITHIN TOLERANCE on both, and C2's null called correctly — BUT RIGHT FOR THE WRONG REASON** (§3.2, cancelling errors). |
| **P3** | C-B = +0.0050 / +0.0081, **UNPOWERED on C1** | **WRONG, twice.** Measured +0.0507 / +0.0236, i.e. **10× and 2.9× my value**, and CI-separated on both with a C1 half-width of ±0.006. I sized the instrument off the incumbent's UNPAIRED CI; this contrast pairs nearly-identical codebooks and is far sharper. |
| **P4** | K_a ≥ K_n − (vetoes) — the codebook does not simply shrink | **RIGHT, and §4 says why:** 4 vetoes cost 1 entry, 9 vetoes cost 2. |
| **P5** | marked set == reference (FP = 0 at corpus level); ≥5 / ≥20 marks on the cut-free run | **RIGHT on the first clause, WRONG on the second's magnitude** (2 and 4 marks) — the counts were quoted off 69/61-step runs and applied to 17 steps. The RATES bracket arm 4's. |
| **P6** | the prevented mints are not worthless | **RIGHT** — 101/800 and 150/800 observations improved, one C1 entry at exactly zero. |
| **P7** | accept disagrees with the primary, driven by floor movement | **HALF WRONG** — accept AGREES on C1 (+0.0450) and on C2 goes CI-separated **+0.1200 where the primary is +0.0001**. The floor did move (0.3591 → 0.4565 on C1) and C2's ABSTAIN floor is the lowest of the three, so the disagreement is on the corpus and in the direction the floor argument predicts. |

**One right in the useful half, one right, one right-with-a-caveat, two half,
one refuted twice, one right-for-the-wrong-reason.** **P3 is the most useful
miss**: it was a quantitative model of the mechanism (deletion, proportional
recovery) and its refutation is what produced §4.

## 7. BOUNDS ON EVERYTHING ABOVE (§8)

- **n = 1 EVENT PER CORPUS.** The entire policy effect is **one burst at one
  frame** — C1 frame 35, C2 frame 24. The CIs are over 50 held-out frames, not
  over cut events, so **they license "on this corpus this one relocation
  improved held-out recognition", NOT "abstaining at cuts helps in general".**
  Two corpora × one event is not a sample.
- **The inherited prediction was made at K = 32/31 and tested at K = 23/25**,
  because the calibration seed moved the codebook size (§1.1). The
  pre-registration declared the contrast is not K-invariant and re-measured the
  baseline in-run (C-C) for exactly this reason — but **the test is still not
  the one the prediction was written for**, and that is a real limitation of
  this comparison rather than a defence of it.
- **The two pre-registered size-matches differ by 3.7× on C1**, and §3.3 shows
  the primary's control was crippled by a one-entry draw. **The magnitude of
  the policy effect is a bracket, not a point.**
- **Gate 2 (bounded growth) is NOT re-litigated and remains UNPOWERED** on this
  corpus — burstiness destroys the CI. No mint-rate claim is made in either
  direction.
- **Gate 3 (refusal) was not re-run.**
- **A grown codebook raises its own measured noise floor**, so accept-rate
  comparisons across arms of different diversity are confounded (§3.4). The
  primary read-out was chosen floor-independent in advance.
- **Toy resolution.** 24×24 grey, 6×6 regions, k = 4, two episodes, 150 frames
  each. **Regions are an adapter-chosen grid**; nothing routes through
  proto-objects or segmentation, and **no object label exists anywhere in the
  measurement**. "Recognition" means region identity against a held codebook.
- **Frames are not independent** (blocks of 10 consecutive), so n = 50
  overstates the effective n. **No p-value is quoted anywhere.**
- **The marker cannot tell a discontinuity from fast continuous motion** — the
  cut-abstention rung's structural finding, inherited whole. §5.3 prices it on
  cut-free footage and does not repair it.
- **§9:** no default moved, no committed seed was edited (gated, byte-hash
  against `17cb3f3d`), no Rust was touched (gated, empty diff). The new seed
  ships disarmed and is not in the default boot set.

## 8. VERIFICATION

| check | result | exit |
|---|---|---|
| `tests/test_engine_provenance_migrated.py` + endpoint guard, **own step, before any number** | **631 passed** | **0** |
| `bash scripts/rung7_vision_bench.sh` **before** the rung | **222 passed** (148.5 s) | **0** |
| `bash scripts/rung7_vision_bench.sh` **after** the rung | **222 passed** | **0** |
| `tests/test_cut_mint_policy_migrated.py` | **13 passed** | 0 |
| adapter audit positive control (planted `["is_max"] > 0.5` in `present_at`) | **caught** | — |
| abstention gate positive control (disarmed world DOES mint there) | **confirmed** | — |
| disarmed `CutMintWorld` vs incumbent `AccumWorld`, **same seed, real frames** | **24 = 24 (C1), 27 = 27 (C2), mint-for-mint** | — |
| in-graph marked steps vs the committed reference | **identical, both corpora** | — |
| `C-A = C-B + C-C` | **holds to float precision, both corpora** | — |
| seed byte-hash vs `17cb3f3d`, both reused seeds | **identical** | — |
| `git diff 17cb3f3d -- runners/dsl/src` | **empty** | — |

## 9. WHAT THE NEXT RUNG SHOULD PRE-REGISTER AGAINST

Ranked by what this evidence supports:

1. **THE BASELINE IS THE PROBLEM, NOT THE POLICY.** C-C is **−0.0235 on both
   corpora at K ≈ 24** where the incumbent measured **+0.0360 at K = 32**. The
   selection advantage that the whole line rests on is **K-dependent and this
   rung could not confirm it at its own K**. Pre-register the K-dependence
   directly — grow to a fixed K on many calibration seeds and measure
   GROWN − UNIFORM as a function of K — because at the moment two rungs
   disagree about whether MDL selection beats uniform, and the difference
   between them is 9 codebook entries and a noise draw.
2. **DEFER, DON'T DECLINE — AND TEST IT AS THE MECHANISM.** §4 shows the policy
   is really a one-frame deferral. That is a *different, testable* hypothesis
   from "abstain": mint the burst from frame t+1 always, cut or no cut, and see
   whether the gain survives. If it does, the cut marker is not load-bearing at
   all and the whole Otsu apparatus (with its arm-4 defect) can be dropped.
   **This is the one I would run first**, and it is cheap.
3. **SIZE-MATCH BY DISTRIBUTION, NOT BY ONE DRAW.** §3.3: with `K_n − K_a = 1`
   a single-draw control is a lottery worth 3.7× the effect. Pre-register the
   subsample control as **the mean over many draws with a CI over draws**.
4. **THE FLOOR TRACKS DIVERSITY, NOT SIZE** — still unmeasured, still the
   incumbent's best unclaimed mechanism, and this rung adds a data point
   (identical floors for two same-size codebooks on C1, different on C2).

**What should NOT be pre-registered:** anything of the form *"abstaining at
cuts improves accumulation."* The effect is CI-separated on both corpora and it
rests on **one frame per corpus**, at a K where the baseline it improves on
does not itself beat a random codebook.
