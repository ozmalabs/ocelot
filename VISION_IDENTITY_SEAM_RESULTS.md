# CONNECT PERCEPT TO IDENTITY — RESULTS

*Pre-registration: `VISION_IDENTITY_SEAM_PREREG.md`, committed BEFORE any
headline number at **`100945b1099f07fbf3b2ce129b770a6f0154b404`** (base
**`212212e30b767466eca100f80e023f22365bd8d9`**). Both endpoints pinned; no range
ends at `HEAD`.*

**Engine (§10):** `25fa11652e83` @
`runners/dsl/python/substrate_rs/_native.abi3.so` — a **shared build from the
canonical tree, Rust source verified byte-identical** (`shared`, via
`ensure_tree_engine()`). **This rung adds NO Rust and NO new Term.**
`tests/test_engine_provenance_migrated.py` + `test_provenance_endpoint_guard_migrated.py`
were run **as their own step before any number**: **628 passed, exit 0**.
**`data/`** symlinked, so the oracle's condition is the **200/0 → 222/0** one.
**Machine:** AMD Ryzen 5 9600X, 12 logical cores. **Ran solo**; load 0.40 at the
start of the C1 window. Wall-clock is reported as a cost only.
**Selectors (§12):** `scripts/identity_seam_measure.py` (confirmatory) ·
`scripts/identity_seam_diagnose.py` (**post-hoc**, kept separate) ·
`scripts/identity_seam_pilot{,2}.py` (**pilots, burned seeds**).
**Raw:** `results/identity_seam_{C1,C2}.json`,
`results/identity_seam_rows_{C1,C2}_{stock,ncc}.json` (6,400 per-observation
rows, committed), `results/identity_seam_diagnose.json`,
`results/identity_seam_pilot{,2}.json`.
**Seeds:** block **72000–72999** claimed and consumed (shuffled-frame floor
draws, noise probes, value-shuffles, gate seeds at 72900+). The **55000** block
(already burned by the cross-frame rung) was used for the pilots only.

---

## 0. THE HEADLINE, IN ONE PARAGRAPH

**The seam is built and it carries identity — and the conjunction fails in both
arms, for two completely different reasons, which is the result.** Pixels now
reach the identity layer and cause it to GROW: a region observed at frame *t*
resolves to the same held identity at *t+1* at **0.982 (C1) / 0.892 (C2)** in
the stock loop and **0.985 / 0.932** in the NCC arm, against a shuffled-frame
floor of **0.26–0.28** — paired **+0.61 to +0.72**, CI-separated, on both
corpora and both arms. Distinctness holds too: genuinely-different region pairs
collapse to one identity **less** often than similar pairs on every arm and
corpus (paired −0.044 to −0.150, all CI-separated), with **7.6–10.5 distinct
identities live per frame**. **Clause 3 is where it dies, and the two arms die
differently.** The **STOCK sd loop force-matches 64 of 64 value-shuffled tiles
on BOTH corpora** — arrangement destroyed, multiset preserved — and is
CI-separated above its control on **zero of six** (corpus × class) novelty
tests on C2 and one of three on C1. **Its mint gate is vacuous on real pixels:
`Count(residual)==0` over a *compositional* decode is satisfiable by anything
once the parts library is large enough, so the loop cannot refuse, and its
decaying mint rate means nothing.** The NCC arm fixes exactly that — **shuffle
handled 0.984 / 0.859, noise 0.953 / 0.641, both CI-separated** — and fails on
the one class the stock loop also fails: **BSDS photographs, 0.203 / 0.047
against controls of 0.141 / 0.234.** **The mint trajectory is the best news
here and was not predicted: minting is not per-frame and not zero — it is
BURSTY AND CUT-ALIGNED**, 1.33 mints/frame within 3 frames of a scene cut
versus 0.080 far from one on C1 (a **16×** ratio), settling at **23–30 held
identities from 1,600 observations** (mint rate 1.4–1.9%).

**Two things I got wrong, both reported as findings.** (1) **My own
contamination hypothesis was refuted by my own diagnostic** — I suspected
clause 3 was measured against a codebook inflated 6× by the preceding floor
pass, re-ran it clean, and the numbers barely moved (§5.1). (2) **P5 was wrong
in both halves**: the NCC verdict's cartoon penalty did not transfer from the
verdict rung, and **P6 was wrong too — the corpora AGREE in sign on all three
clauses**, the first time in this arc that they have.

---

## 1. WHAT WAS ACTUALLY ABSENT — a correction to the brief's own framing

Two probes measured the seam as **6 ProtoObject files ∩ 98 identity files = 0**
and called it a structural absence. **That framing is right about the conclusion
and imprecise about the mechanism, and this rung has to say so before reporting
anything.**

The cross-frame rung *did* identify real video regions against held
`ShapeSignature`s. What it never did was let a percept **change** the identity
layer: its codebook was a **fixed, pre-loaded 16 tiles cut from the base
frame**. Nothing was minted; the codebook never grew.

**So the absence was specifically this: no percept had ever CAUSED the identity
layer to grow.** That is what is now built, and it is why the mint gate — not
the identification — is the crux.

---

## 2. HOW IT IS WIRED

### ARM A — the STOCK loop, unmodified, and NO new rule

`shape_decode_loop` + `vision_sdloop`, byte-unchanged. The adapter writes an
`Observation` carrying exactly the attrs those rules already read —
`signature` (36 `["cell", r, c, "v<q>"]` tuples, region-local),
`dim_types`, `key`, `status:"pending"` — plus `vq: 1`, the flag
`vq_grow_quantum` already uses to install a minted quantum as a held
`ShapeSignature` and bump `codebook_epoch`. **The whole of arm A is four
attributes and an edge.** That the seam needed no new rule at all is itself
worth recording: the loop was always able to accept pixels; nobody had handed
it any.

### ARM B — `seeds/vision_identity_seam.json`, 5 rules, one thing changed

Same topology — **decode → gate → mint → grow → epoch → re-decode** — with the
recognition predicate replaced by the **V3 continuous verdict** (normalized
cross-correlation, one `Dot` of two unit-centred 36-vectors) and the accept/mint
decision made against a **MEASURED floor**: an observation is held **iff its best
score strictly exceeds the best score the same comparator achieves, in the same
substrate, against the same codebook, on `probe_kind == "G2c"` calibration
noise**. `is_recalib` re-arms that floor on every `codebook_epoch` bump.

This is the verdict rung's own design — *hold the proposal fixed, vary only the
verdict* — applied one level up, and is named as such rather than presented as a
new mechanism.

**§13:** no numeric threshold appears anywhere in the seed. The only literals
are `0`/`1`/`1.0` (counts and boolean flags), `0.5` (the arming discriminator on
a 0.0/1.0 flag — the idiom every vision seed uses), and `-1e18` (`MaxOver`'s
empty-source sentinel). `test_the_seam_writes_NO_numeric_threshold` asserts
exactly that set.

**§9:** the seed ships `seam = 0.0`, is in no default boot set, and the oracle
is unmoved (§8).

**Declared in the prereg, not discovered after:** the two arms do **not** start
from an identical codebook. Arm B's is scoped to `seam_grown == 1.0` and starts
**empty**; arm A inherits the **17 non-pixel-derived `ShapeSignature`s
`boot_core` installs**. No arm-A-vs-arm-B difference below is attributed to the
verdict alone.

---

## 3. CORPORA AND THE CUT SPLIT

| id | episode id (pinned, verified at run time) | otsu | cuts / 100 |
|---|---|---|---|
| **C1 cartoon** | `08630d4b7b215c469df19b9c42d7b617` | **11.085** | **3** |
| **C2 live-action** | `119eca433329b36b19e5d69fef84966e` | **4.576** | **2** |

100 base frames, 16 regions of 6×6, k=4, **24×24** grey. Both pins matched; had
either differed the run was declared void. Otsu on each corpus's own per-step
motion — no free parameter (§13), the verdict rung's rule reused verbatim.

**Resolution did not creep: 24×24 throughout**, inside the drive's ~57×57
real-time affordance and outside the identity layer's ~10×10-at-K=1 one (§7).

---

## 4. THE THREE CLAUSES

### 4.1 CLAUSE 1 — CROSS-FRAME IDENTITY PERSISTS. **PASS, 4/4.**

Unit = **base frame** (§4), non-cut stratum, n=96 (C1) / 97 (C2), 95% paired t-CI.

| corpus | arm | persistence | shuffled-frame floor | paired | PASS |
|---|---|---|---|---|---|
| C1 | stock | **0.9818** [0.9709, 0.9926] | 0.2793 | **+0.7025** [+0.6270, +0.7779] | ✅ |
| C1 | ncc | **0.9850** [0.9704, 0.9997] | 0.2604 | **+0.7246** [+0.6617, +0.7875] | ✅ |
| C2 | stock | **0.8918** [0.8739, 0.9096] | 0.2803 | **+0.6115** [+0.5645, +0.6584] | ✅ |
| C2 | ncc | **0.9323** [0.9150, 0.9497] | 0.2287 | **+0.7036** [+0.6432, +0.7641] | ✅ |

**A region recognised at frame *t* is the same held identity at *t+1*, on real
motion, far above a shuffled-frame floor, on both corpora and in both arms.**
The floor is non-trivial (~0.26–0.28, roughly 4× chance for ~10 live
identities), so the margin is not an artifact of a degenerate baseline.

**THE CUT STRATUM, and it is the reason the stratification was mandated:**
persistence across a cut is **0.042 / 0.083 (C1)** and **0.031 / 0.094 (C2)** —
essentially total failure, on n=3 and n=2 frames respectively. Pooling would
have dragged the headline down by a couple of points and hidden that the failure
is **total** and **confined to the cut**. Identity is not claimed to survive a
scene change, and this rung does not count that as a failure of identity.

### 4.2 CLAUSE 2 — DISTINCT THINGS STAY DISTINCT. **PASS, 4/4.**

*The clause an identity layer that merges everything passes clause 1 by
failing.* "Genuinely different" is **mean absolute RAW-GREY pixel difference**,
computed in numpy **outside the graph** — deliberately not NCC, which is the
comparator under test.

| corpus | arm | collapse DIFFERENT | collapse SIMILAR | paired (D − S) | distinct/frame | PASS |
|---|---|---|---|---|---|---|
| C1 | stock | 0.0299 | 0.1181 | **−0.0883** [−0.0923, −0.0842] | **10.49** | ✅ |
| C1 | ncc | 0.0756 | 0.1973 | **−0.1217** [−0.1306, −0.1128] | **7.64** | ✅ |
| C2 | stock | 0.0145 | 0.1648 | **−0.1504** [−0.1629, −0.1378] | **10.35** | ✅ |
| C2 | ncc | 0.0657 | 0.1103 | **−0.0446** [−0.0562, −0.0329] | **9.52** | ✅ |

Every arm assigns the same identity to two regions **less** often when they are
genuinely different, CI-separated. **The seam has not collapsed.**

**Reported against myself:** arm B collapses **more** in absolute terms than arm
A on both corpora (0.0756 vs 0.0299; 0.0657 vs 0.0145) and holds **fewer**
distinct identities per frame on C1 (7.64 vs 10.49). The continuous verdict is
more willing to call two things the same. It passes the pre-registered
*relative* test and is the worse arm on the *absolute* one, and both are stated.

### 4.3 CLAUSE 3 — REFUSAL. **FAIL, 4/4 — and the two arms fail differently.**

`novel_handled` = minted **or** refused. n=64 per class. Unit = probe.
"sep" = CI-separated above the matched CONTROL of 64 re-presented genuine held
regions.

| corpus | arm | CONTROL | BSDS | NOISE | SHUFFLE | clause |
|---|---|---|---|---|---|---|
| C1 | **stock** | 0.0000 | 0.0781 sep✅ | 0.0312 sep❌ | **0.0000** sep❌ | ❌ |
| C1 | **ncc** | 0.1250 | 0.1562 sep❌ | **0.9531** sep✅ | **0.9844** sep✅ | ❌ |
| C2 | **stock** | 0.0000 | **0.0000** sep❌ | 0.0469 sep❌ | **0.0000** sep❌ | ❌ |
| C2 | **ncc** | 0.2344 | 0.0469 sep❌ | **0.6406** sep✅ | **0.8594** sep✅ | ❌ |

**THE STOCK LOOP CANNOT REFUSE.** It force-matched **64 of 64** value-shuffled
tiles on **both** corpora — tiles whose value multiset is preserved exactly and
whose arrangement is destroyed, the cross-frame rung's own arrangement floor —
and **0 of 64** BSDS photographs on C2. On C2 it is separated above its control
on **none** of the three classes. Its single "pass" (C1 BSDS, 0.0781) is
separated only from a **zero-variance control** whose CI is a point at 0.0000 —
a zero-width interval, which the salience rung named as an instrument smell, and
which is quoted here as a caveat rather than as a pass.

**THE NCC ARM FIXES THAT AND ONLY THAT.** Shuffle 0.984 / 0.859 and noise
0.953 / 0.641, all four CI-separated. **The seam's actual contribution is
refusal**, and it is large.

**BOTH ARMS FAIL ON BSDS PHOTOGRAPHS**, and the honest reading is not settled
(§7): at 6×6 and k=4 a natural-photograph tile and a broadcast-video tile may be
genuinely indistinguishable, in which case force-matching them is correct
behaviour being scored as a failure. **This rung did not measure that**, and the
clause is reported as failed rather than reinterpreted (§5).

**And arm B's control rate is a real cost, not a rounding error:** **12.5% (C1)
and 23.4% (C2) of GENUINE re-presented held regions were minted as novel.** The
measured floor refuses things it already holds. That is the price of the
refusal, it is paid on every frame, and it is quoted with the benefit.

---

## 5. THE MINT-RATE TRAJECTORY — the part that was not predicted

**Neither failure mode occurred.** Mint rate is not sustained near 1.0 (logging)
and not zero (a vacuous gate looking like stability):

| corpus | arm | mints / 1,600 obs | rate | K after main |
|---|---|---|---|---|
| C1 | stock | **26** | 1.63% | 26 |
| C1 | ncc | **23** | 1.44% | 23 |
| C2 | stock | **30** | 1.87% | 30 |
| C2 | ncc | **23** | 1.44% | 23 |

**But the shape is the finding, and it is not a decay curve — it is BURSTY, and
the bursts are CUT-ALIGNED** (D3, post-hoc):

| corpus | arm | mints/frame within 3 frames of a cut | far from a cut | ratio |
|---|---|---|---|---|
| C1 | stock | **1.083** (13 over 12 frames) | 0.148 | **7.3×** |
| C1 | ncc | **1.333** (16 over 12 frames) | 0.080 | **16.7×** |
| C2 | stock | **0.500** | 0.283 | 1.8× |
| C2 | ncc | **0.750** | 0.185 | 4.1× |

**Minting is event-driven: the codebook grows when the scene changes and is
quiet when it does not.** That is the behaviour the loop was supposed to have,
it was not designed for here, and it emerged from the same structural gate on
both arms. The C1 effect (7–17×) is much stronger than the C2 effect (1.8–4.1×),
consistent with C1's cuts being harder (otsu 11.085 vs 4.576).

**Caveat, stated with it:** D3 is **post-hoc**, n = 3 and 2 cuts respectively,
and "within 3 frames" is a window I chose after seeing the trajectory. **It is a
described shape, not a tested hypothesis**, and it is exactly the kind of thing
that should be pre-registered by a successor rather than banked here.

### 5.1 COST — linear in K, and the NCC verdict is ~100× cheaper than ShapeDecode

| corpus/arm | median ms at low K | at high K | ratio |
|---|---|---|---|
| C1 / ncc | 0.18 (K≈4) | 6.25 (K≈23) | 34.7× |
| C2 / ncc | 0.17 (K≈7) | 5.27 (K≈23) | 31.0× |
| C1 / stock | 3.83 | 6.99 | 1.8× |
| C2 / stock | 4.46 | 7.04 | 1.6× |

Arm B is **linear in K** as the re-run rung predicted the identity layer would
be, at roughly **6 µs/cell/K** — against that rung's measured **698 µs/cell at
K=1** for the `ShapeDecode` path. **The continuous verdict is about two orders
of magnitude cheaper per comparison than the compositional decode it replaces**,
which is the same direction the verdict rung found (SC+TPS cheaper than the weak
render path). Arm A's flatter ratio is not an efficiency: it starts from a large
constant and its codebook grows less.

---

## 6. THE DIAGNOSTIC THAT REFUTED MY OWN HYPOTHESIS

**NOT pre-registered. Labelled post-hoc. It did not change the verdict.**

The pre-registered pass order was main → clause-1 floor → clause-3 probes, all
in ONE substrate. The floor pass presents 1,600 distant-frame regions, which
mint — so clause 3 was measured against a codebook **6× larger** than clause 1's
(K = 170 vs 23 on C1/ncc). **I suspected this was the cause of the BSDS failure
and the high control rate, and measured it rather than arguing it.** D1 re-runs
clause 3 with the probes presented immediately after the main pass:

| corpus/arm | K at clause 3 | BSDS | NOISE | SHUFFLE | CONTROL |
|---|---|---|---|---|---|
| C1/ncc **confirmatory** | 170 | 0.156 | 0.953 | 0.984 | 0.125 |
| C1/ncc **D1 clean** | **23** | **0.203** | 0.969 | 0.984 | **0.141** |
| C2/ncc **confirmatory** | 137 | 0.047 | 0.641 | 0.859 | 0.234 |
| C2/ncc **D1 clean** | **23** | **0.047** | 0.641 | 0.859 | **0.234** |
| C1/stock clean | 26 | 0.078 | 0.031 | 0.000 | 0.000 |
| C2/stock clean | 30 | 0.000 | 0.047 | 0.000 | 0.000 |

**THE HYPOTHESIS IS REFUTED.** At a codebook 7× smaller, BSDS moves +0.047 on C1
and **+0.000 on C2**; the control rate moves +0.016 and +0.000. **Neither the
BSDS failure nor the false-novel rate is a codebook-size artifact.** BSDS
photographs genuinely score above the noise floor against a video codebook, and
the measured floor genuinely rejects ~14–23% of things it already holds even at
K=23. The confound was real and was not the cause — which is worth more than if
I had guessed right, because the alternative was to report the failure with an
excuse attached.

**D2 — the floor is alive and moves with K**, slowly: 0.3254 at K=4 (C1),
0.348 → 0.3598 as K goes 6 → 14 (C2). This is what `is_recalib` exists for and
is gated by `test_the_floor_MOVES_as_the_codebook_grows` — the **G5
RESPONSIVENESS** gate the video-probe re-run earned, because an instrument that
is alive, deterministic and INSENSITIVE passes every other check.

---

## 7. BOUNDS ON EVERYTHING ABOVE (§8)

- **Two episodes of two series**, plus BSDS300 crops. Not a survey of video.
  Every number is conditional on this corpus, verified by episode id at run time.
- **24×24, 6×6 regions, k=4.** Whether any of this holds at a resolution where
  a 6×6 tile is not most of an object is **not measured**.
- **The BSDS clause-3 failure is not diagnosed.** It may be a genuine refusal
  failure or it may be that a 36-pixel photograph tile and a 36-pixel video tile
  are genuinely the same thing. **This rung cannot tell those apart** and does
  not claim to.
- **Arm B never REFUSES; it always MINTS.** `novel_handled` pooled the two by
  design, and the measured refuse rate is **0.000 everywhere**. So "refusal
  survives" is demonstrated in its minting form only.
- **The two arms do not share a starting codebook** (§2), so arm-A-vs-arm-B
  deltas are not clean verdict contrasts.
- **Clause 1's cut stratum is n=3 and n=2 frames.** The cut numbers are
  descriptive; no CI is quoted for them.
- **Clause 3's stock-arm controls have ZERO variance** (all 64 zero), so the one
  stock "sep=True" is separation from a point interval. It is quoted as a
  caveat, not a pass.
- **D3 (cut-aligned minting) is post-hoc**, with a window chosen after looking,
  on 3 and 2 cuts. Described, not tested.
- **Frames are not independent.** Consecutive frames of one shot are heavily
  autocorrelated; n=96 base frames overstates the effective n and **no p-value
  is quoted anywhere** — only CIs, with the unit at the frame.
- **Nothing here routes through proto-objects**, as the brief required and as
  S3's continued emptiness demands. **No claim is made about proto-objects,
  border ownership, or segmentation.**
- **No claim is made about learning**, beyond codebook growth. Recognition
  accuracy against a ground-truth object label was not measured because there is
  no such label in this corpus.
- **§9:** no default moved, no existing seed was edited, no Rust was touched.
  Oracle **222 passed, exit 0** (§8 below).

---

## 8. THE REGRESSION ORACLE

Run as its **own step**, after all measurement, exit code captured.

| selector | result | exit |
|---|---|---|
| `bash scripts/rung7_vision_bench.sh` | **222 passed** in 148.2 s | **0** |
| `tests/test_engine_provenance_migrated.py` + endpoint guard | **628 passed** | **0** |
| `tests/test_identity_seam_migrated.py` (this rung's gates) | **9 passed** | **0** |

**222/0 is the `data/`-PRESENT figure**, and the symlink was verified live
before the run (§10.2).

---

## 9. PREDICTIONS, SCORED

| # | prediction | outcome |
|---|---|---|
| P1 | ARM A passes clause 1 | **RIGHT** — +0.7025 / +0.6115 |
| P2 | ARM A FAILS clause 3, driven by SHUFFLE | **RIGHT**, and stronger than predicted — 0/64 shuffle on BOTH corpora *(not blind on C1; blind on C2, where it replicated)* |
| P3 | ARM A's mints decay to ≈0 within ~20 frames | **WRONG** — mints are BURSTY and CUT-ALIGNED, with new mints as late as frame 89. The mechanism I named (a compositionally-complete parts library) is nonetheless confirmed by clause 3 |
| P4 | ARM B passes clause 3 on all three classes | **HALF WRONG** — passes NOISE and SHUFFLE on both corpora, fails BSDS on both |
| P5 | ARM B persistence LOWER on C1, comparable/higher on C2 | **WRONG IN BOTH HALVES** — higher on C1 (0.9850 vs 0.9818) *and* higher on C2 (0.9323 vs 0.8918). The verdict rung's cartoon penalty did not transfer |
| P6 | The corpora disagree in sign on at least one clause | **WRONG** — they agree in sign on all three, in both arms. The first time in this arc |
| P7 | ARM B's mints plateau at non-zero where ARM A's go to zero | **WRONG** — neither goes to zero; both are bursty and their rates are within 0.4pp |
| P8 | ARM A passes clause 2 | **RIGHT** — −0.0883 / −0.1504 |

**3 right, 1 half, 4 wrong.** **The proviso I flagged in advance as most likely
to break (P5's C1 half) broke** — and it broke in the direction I had not
considered: a growing codebook changes what "the alternatives" are, so the
verdict rung's fixed-16-way cartoon result does not transfer at all. **P6 is the
most interesting miss**: four prior rungs found the corpora disagreeing in sign,
and this rung's brief warned me about it; the honest report is that on THIS
question they agree, which is evidence about the question rather than about the
corpora.

---

## 10. WHAT THE NEXT RUNG SHOULD PRE-REGISTER AGAINST

Ranked by what the evidence supports:

1. **IS THE BSDS FAILURE A REFUSAL FAILURE OR A RESOLUTION FLOOR?** The sharp,
   cheap, pre-registrable question this rung leaves open. At 6×6/k=4, measure
   whether a human-or-reference discriminator can separate BSDS tiles from video
   tiles **at all**. If it cannot, clause 3's BSDS arm is measuring the corpus,
   not the seam, and the seam passes on the two classes that carry information.
2. **THE FALSE-NOVEL RATE IS THE SEAM'S REAL PRICE.** 12.5% / 23.4% of genuine
   held regions minted as novel, and it is **not** a codebook-size artifact
   (§6). The measured floor is a `MaxOver` — a single worst-case noise draw
   sets it, so it is driven by the tail of 8 probes. **Does the false-novel rate
   fall as the number of calibration probes rises, and does it do so without a
   constant going in?** That is a §13-clean question with an obvious mechanism.
3. **CUT-ALIGNED MINTING, PROPERLY.** §5's D3 is post-hoc on 3 and 2 cuts with a
   chosen window. Pre-register the window, use a corpus with enough cuts to
   power it, and test it against a motion-matched non-cut control.
4. **THE ARMS DO NOT SHARE A CODEBOOK.** Re-run with arm A scoped to
   pixel-derived signatures only, so the verdict contrast is clean.

**What should NOT be pre-registered:** anything of the form *"the substrate
recognises objects across frames."* It carries **region identity** across
frames, at 6×6, on two episodes, with **no proto-objects involved** and **no
object label anywhere in the measurement**. The regions are an adapter-chosen
grid, which is the same "axes are GIVEN" bound the video probe named — this rung
moved the identity layer and did not touch that.
