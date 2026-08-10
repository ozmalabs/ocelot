# GRAPH-RESIDENT ABSTENTION ON A DISCONTINUED PRIOR — RESULTS

*Pre-registration: `VISION_CUT_ABSTENTION_PREREG.md`, committed BEFORE any
headline number at **`9f0bc789`** (branch base **`212212e30b767466eca100f80e023f22365bd8d9`**).*

**Engine (§10):** `25fa11652e83` @
`runners/dsl/python/substrate_rs/_native.abi3.so` — a **shared build from the
canonical tree, Rust source verified byte-identical** (`shared` verdict).
**This rung adds NO Rust, NO Term and NO constant to the engine** — every part
of the mechanism is expressed in Terms that already existed
(`TemporalDiff`, `XCorrPeak`, `Argmax`, `Sum`, `Count`, `Filter`, `Abs`).
`scripts/engine_build.sh` was therefore not run, and
`tests/test_engine_provenance_migrated.py` was run **as its own step before any
number was taken**: **7 passed, exit 0**.
**Selector:** `scripts/cut_abstention_measure.py` (confirmatory) +
`scripts/cut_abstention_analyse.py` (the pre-registered decision rule, applied
mechanically) + `scripts/cut_abstention_diagnose.py` (the post-hoc diagnostic
of §7, labelled post-hoc throughout).
**Raw:** `results/cut_abstention_{video,stress,diagnose,analysis}.json`. The 12
per-trial row files (`cut_rows_*.json`, 56 MB) are **not committed**, following
the incumbent's precedent; their SHA256s are in
`results/cut_rows_SHA256SUMS.txt`.
**Seeds:** block **73000–73999**. `73000` for the confirmatory run, `73500/73501`
for the post-hoc diagnostic, `73001/73002` in the gates. **No seed outside the
block was drawn**; the concurrent rung's 72000–72999 was not touched.

**INPUT PROVENANCE.** The corpora were regenerated from Jellyfin with the
committed constants and **reproduce the committed motion statistic exactly**:
C1 max `52.34345685659597`, C2 max `57.8950993584262`, identical to the last
digit to `results/verdict_comparator_video.json`.

---

## 0. THE HEADLINE, IN ONE PARAGRAPH

**The abstention works, it is entirely graph-resident, its threshold genuinely
falls out — and the same property that makes the threshold fall out is what
makes it unable to tell a discontinuity from fast continuous motion.** On the
protected arm V3, a probe spanning a step the graph marked goes from
**0.1647 → 1.0000 refused on C1** (paired **+0.8353 [+0.7950, +0.8755]**) and
**0.0720 → 1.0000 on C2** (**+0.9280 [+0.8872, +0.9687]**), while a probe
spanning no marked step moves by **EXACTLY +0.0000** on both corpora and **all
8 000 / 8 640 off-cut rows are field-by-field identical** to the inert baseline.
That is the cliff converted into a decision: on the marked probes V3's accuracy
was **0.1316 (C1) / 0.1280 (C2)**, so the rule trades ~13% correct answers for
declining ~87% confident errors, and on the V2 contrast — the arm the verdict
rung proved has a dead refusal — accuracy on marked probes is **0.0035** and its
baseline refusal there is **0.0026**, i.e. it was answering confidently and
wrongly essentially every time. **The recall over V3's ACTUAL errors is
0.9078 on C1 and 0.4591 on C2** (+0.7537 / +0.4001, both CI-separated), and the
Δ-resolution shows exactly why: **+0.8040 at Δ=25, and a NULL at Δ=1**
(+0.1023 [−0.0366, +0.2412] on C1) — a frame-level statistic cannot see the
region-level distractor inflation the salience rung localised at short Δ.
**And then the mechanism fails its own two hardest arms.** On a CUT-FREE run of
real footage the rule marks **5/69 (C1) and 22/61 (C2)** steps as
discontinuities, whose magnitudes top out at **5.94 / 4.46 against a real cut's
43.52 / 44.75** — **an order of magnitude below any actual cut**. **Otsu has no
free parameter and it also has no NULL HYPOTHESIS:** handed a distribution with
no cut in it, it splits it anyway, and `marked_are_the_top_n` is **True** — the
rule marks the top of whatever it is given. **Arm 2b's PASS is worthless and I
broke it myself:** a constant-velocity `np.roll` pan has `sd(motion) = 0.0` and
**exactly one distinct value**, so no split exists above its maximum; the
non-degenerate pan (velocity varies, still no discontinuity anywhere) is marked
**106/149 (C1) and 90/149 (C2)**. The secondary statistic S1 (`XCorrPeak`) is
**byte-identical to the primary on both real corpora** — the row files have the
same sha256 — and **strictly worse** under stress, marking **50–124 of 149** steps
of a pure rigid pan.

---

## 1. THE MECHANISM — AND THE ARCHITECTURE CLAIM, CHECKED RATHER THAN ASSERTED

Five rules in `seeds/vision_cut_abstention.json`. The adapter
(`domains/cut_abstention_world.py`) writes one `VidFrame` per decoded frame,
one `FrameStep` per consecutive pair, and one `spans` edge from each probe's
`ObsGroup` to the steps of the interval **the runner already constructed when
it built that probe**. Then it stops.

| rule | what it decides |
|---|---|
| `ca_step_mag` | the motion of a step — `Sum(TemporalDiff(a,b), Abs)/Count`, computed by the graph from the pixels |
| `ca_step_res` | the alternative statistic — `1 − max(XCorrPeak(rows), XCorrPeak(cols))` |
| `ca_otsu` | **the threshold**, as `Argmax` over the held steps of `(s0·n1 − s1·n0)² / (n0·n1)` |
| `ca_mark_cut` | which steps are discontinuities |
| `ca_abstain` | **whether to answer**, and mints the `Refusal` node that records it |

**THE THRESHOLD FALLS OUT, and this is gated, not claimed (§13).**
`test_no_numeric_threshold_is_written_anywhere_in_the_seed` walks every `Lit`
in every rule and asserts the set of numeric literals is a subset of
`{0, 1, 2, −1}` — all structural (counts, the exponent, the empty-upper-class
sentinel, the `1.0` that turns a correlation into a residual) — with a
**non-vacuity assertion** beside it so the gate cannot pass on an empty walk.
`test_the_threshold_is_a_value_the_data_supplied` asserts the threshold Term is
an `Attr(key="mag")` of an `Argmax`, i.e. **the motion of a step the graph
picked**. There is no percentile, no cutoff and no corpus constant anywhere.

**The architecture rule is gated too.** `test_the_adapter_takes_no_decision_over_graph_state`
is a source audit: the adapter may not contain `np.mean`, `np.abs`, `np.diff` or
`otsu`, and the names `is_cut` / `cut_threshold` may appear **only** inside its
read-back methods — never inside `present`, which is what writes to the graph.
Deleting the mechanism turns each of these red.

## 2. THE INSTRUMENT — EVERY CHECK PASSES, AND THEY WERE ABLE TO FAIL

| check | result |
|---|---|
| in-graph `mag` vs `np.mean(np.abs(frames[t+1]-frames[t]))` | **exact to 1e-9, both corpora, every step** |
| in-graph Otsu PARTITION vs the committed numpy Otsu | **identical, both corpora** — C1 `[34, 47, 79]`, C2 `[23, 85, 143]` |
| C1's graph-marked steps vs the frames the SALIENCE rung named by error concentration | **34 and 47 — a THIRD independent method naming the same two frames** |
| the comparator is unmoved by the arming (`true_is_max`, `said`, `graph_max`) | **True for all 4 corpus×verdict combinations** |
| the threshold VALUE differs from numpy's | **as predicted** — the seed picks the lower endpoint (C1 11.0637, C2 4.4577), numpy the midpoint (27.2941, 24.6059); the classification is unchanged |

The threshold-value difference is worth stating plainly rather than burying:
**the two thresholds differ by a factor of 2.5–5.5 and produce the identical
partition**, because everything between the largest non-cut step and the
smallest cut step is empty. That is the same 4×–10× separation §3 of the
pre-registration declared in advance as making arm 2a weak.

## 3. ARM 1 — ABSTAINS ON CUTS

Unit = base frame, paired 95% t-CI, `t(0.975,49) = 2.0096`. **Per corpus, never
pooled.** Ground truth is the comparator's **realised error**, not the motion
label. `**` = CI excludes 0.

### 3.1 V3 (ncc) — the protected arm

| population | corpus | baseline | armed | **paired increment** | n frames / trials |
|---|---|---|---|---|---|
| **cells where ALL 16 REGIONS FAILED** | **C1** | 0.2292 | 1.0000 | **+0.7708 [+0.6199, +0.9218]** | 3 / 48 |
| | **C2** | 0.0500 | 1.0000 | **+0.9500 [+0.8495, +1.0505]** | 5 / 80 |
| all V3 errors | C1 | 0.1541 | 0.9078 | **+0.7537 [+0.6829, +0.8246]** | 40 / 752 |
| | C2 | 0.0590 | 0.4591 | **+0.4001 [+0.2780, +0.5223]** | 50 / 590 |
| V3 errors, Δ=1 | C1 | 0.0795 | 0.1818 | +0.1023 [−0.0366, +0.2412] **(NULL)** | 11 / 50 |
| | C2 | 0.0095 | 0.1429 | +0.1333 [−0.1346, +0.4013] **(NULL)** | 7 / 23 |
| V3 errors, Δ=5 | C1 | 0.1455 | 0.5368 | **+0.3913 [+0.2054, +0.5772]** | 19 / 169 |
| | C2 | 0.0237 | 0.1535 | **+0.1298 [+0.0196, +0.2401]** | 38 / 167 |
| V3 errors, Δ=25 | C1 | 0.1510 | 0.9550 | **+0.8040 [+0.7315, +0.8765]** | 40 / 533 |
| | C2 | 0.0689 | 0.5417 | **+0.4727 [+0.3328, +0.6127]** | 48 / 400 |

**The all-16-failed row is the pre-registered headline and it passes on both
corpora**, well past the declared ≥0.80 bar. **The Δ-resolution is the honest
part.** At Δ=1 the increment is a **NULL on both corpora** — exactly what
prediction 2 said would happen, and for the stated reason: the salience rung
established that Δ=1 errors at a wide orbit are region-level distractor
inflation, and **no frame-level statistic can see a region-level failure.** The
mechanism covers the cliff and does not touch the gradient, which is what it was
built to do and all it does.

### 3.2 V2 (ssdg) — the contrast whose refusal the verdict rung proved dead

| population | corpus | baseline | armed | increment | n frames |
|---|---|---|---|---|---|
| **all 16 failed** | **C1** | **0.0000** | 1.0000 | **+1.0000 [+1.0000, +1.0000]** | **18** |
| | **C2** | **0.0026** | 1.0000 | **+0.9974 [+0.9922, +1.0026]** | **24** |
| all V2 errors | C1 | 0.0019 | 0.9074 | **+0.9056 [+0.8336, +0.9776]** | 40 |
| | C2 | 0.0012 | 0.4318 | **+0.4305 [+0.3019, +0.5592]** | 48 |

**This reproduces the verdict rung's diagnosis and quantifies its cost.** V2 has
**18 (C1) and 24 (C2) base frames** in which every one of 16 regions failed —
against V3's **3 and 5** — and its baseline refusal on those frames is
**0.0000 / 0.0026**. Its accuracy on marked probes is **0.0754 (C1) / 0.0035
(C2)**. **On C2, V2 answers confidently and wrongly on 99.65% of the probes
spanning a cut, and declines 0.26% of them.** The rule takes that to 1.0000.

## 4. ARM 2a — DOES NOT ABSTAIN ON HARD-BUT-CONTINUOUS

Population: A1 probes the comparator got RIGHT, whose span touches the **top
motion decile among non-cut steps** and no cut.

| corpus | verdict | baseline | armed | **increment** | n frames / trials |
|---|---|---|---|---|---|
| C1 | ncc | 0.0000 | 0.0000 | **+0.0000 [+0.0000, +0.0000]** | 10 / 239 |
| C2 | ncc | 0.0191 | 0.0191 | **+0.0000 [+0.0000, +0.0000]** | 29 / 733 |
| C1 | ssdg | 0.0000 | 0.0000 | **+0.0000 [+0.0000, +0.0000]** | 10 / 240 |
| C2 | ssdg | 0.0000 | 0.0000 | **+0.0000 [+0.0000, +0.0000]** | 29 / 760 |

And on **every** correct answer with a cut-free span (n = 1 542–1 775 trials per
cell): **+0.0000** in all four. **The arm passes exactly, and the pass is WEAK
EVIDENCE — declared as such in the pre-registration before any number.** C1's
"hard" decile spans motion 2.31–11.06 and C2's spans 3.25–4.46, against cut
steps at 43.5+ and 44.8+. A 4×–10× gap means a wide range of thresholds gives
this answer, so **arm 2a cannot distinguish a good rule from a lucky one on
these corpora.** That is why arm 2b and arm 4 exist, and they are where the
mechanism breaks.

## 5. ARM 3 — BYTE-IDENTITY OFF THE CUT FRAMES

| corpus | verdict | statistic | rows off cut | rows differing | **identical** |
|---|---|---|---|---|---|
| C1 | ncc | mag / xcorr | 8 000 | **0** | **True** |
| C1 | ssdg | mag / xcorr | 8 000 | **0** | **True** |
| C2 | ncc | mag / xcorr | 8 640 | **0** | **True** |
| C2 | ssdg | mag / xcorr | 8 640 | **0** | **True** |

Twenty fields per row (`said`, `answer`, `refused`, `graph_max`, `noise_floor`,
`status`, `ref_max`, `true_score`, `true_is_max`, …), **all identical**. §9
holds: the seed ships inert, is not in the default boot set (gated), and an
armed run changes nothing outside the probes it declined.

## 6. THE INCREMENT OVER V3's EXISTING REFUSAL — H0 IS REJECTED

| corpus | verdict | probes | baseline refusal | armed | **increment** | baseline accuracy |
|---|---|---|---|---|---|---|
| **C1** | **ncc** | **marked** | **0.1647** | 1.0000 | **+0.8353 [+0.7950, +0.8755]** | **0.1316** |
| C1 | ncc | unmarked | 0.0009 | 0.0009 | **+0.0000 [0, 0]** | 0.9651 |
| **C2** | **ncc** | **marked** | **0.0720** | 1.0000 | **+0.9280 [+0.8872, +0.9687]** | **0.1280** |
| C2 | ncc | unmarked | 0.0072 | 0.0072 | **+0.0000 [0, 0]** | 0.9145 |
| C1 | ssdg | marked | 0.0026 | 1.0000 | **+0.9974** | 0.0754 |
| C2 | ssdg | marked | 0.0026 | 1.0000 | **+0.9974** | **0.0035** |

**V3's latent refusal does NOT already cover this.** It catches 16.5% of C1's
and 7.2% of C2's cut-spanning probes; the rule takes both to 1.0000 and leaves
the other ~92–98% of the trial set untouched to the bit. My measured baseline
(0.1647 / 0.0720) is consistent with the verdict rung's published cut-stratum
figures (0.1363 / 0.1000) — different seed block, different insertion
permutation, and a per-probe span rather than a pooled stratum, so agreement in
magnitude is the most that should be claimed and is what is observed.

**The forced part is stated, not presented as a result:** `armed = 1.0000` is
forced — the rule refuses every marked probe by construction. **The risked
quantities are the baseline rate, the exact zero on unmarked probes, the exact
byte-identity, and the recall over the comparator's real errors**, and those are
what the tables above report.

## 7. ARM 2b AND ARM 4 — THE MECHANISM'S LIMIT, AND MY OWN BROKEN ARM

### 7.1 ARM 4 FAILS, AS PRE-REGISTERED, AND THE MAGNITUDE IS THE FINDING

Population: the longest CONTIGUOUS CUT-FREE run of each corpus. Real footage,
real texture, real camera motion, **no discontinuity**.

| corpus | frames | steps | **marked as cuts** | graph threshold | max motion in the run | **a REAL cut is** |
|---|---|---|---|---|---|---|
| **C1** | 80–149 | 69 | **5 (7.2%)** | 2.104 | 5.94 | **≥ 43.52** |
| **C2** | 24–85 | 61 | **22 (36.1%)** | 2.329 | 4.46 | **≥ 44.75** |

**The rule calls a 4.46 a discontinuity in a sequence whose largest step is 4.46
and where an actual cut is 44.75 — an order of magnitude away.** And
`marked_are_the_top_n` is **True** on both corpora: it is not finding structure,
it is **marking the top of whatever distribution it is handed**. C2 is the
damning case — max/median motion is **2.22**, a nearly flat distribution with no
tail at all, and Otsu still splits it 39/22.

> **Otsu has no free parameter, and it also has NO NULL HYPOTHESIS.** A
> parameter-free threshold is not the same as a CALIBRATED one. Otsu has now
> been used twice in this arc (the verdict rung's cut labels, and here) and this
> is the first time it has been asked what it does when there is nothing to
> find. It splits anyway.

### 7.2 ARM 2b PASSED, AND THE PASS IS WORTHLESS — I BROKE MY OWN ARM

`mag` marked **0/149** steps of a rigid pan at **every** velocity, on both
corpora. That is a pass, and it is arithmetic rather than understanding:
`np.roll(frame0, v·t)` is a **constant-velocity** pan, so its per-step motion is
the same number at every step. Measured, not argued: **`sd(motion) = 0.0` with
exactly ONE distinct value**, at all four velocities on both corpora. A
zero-variance distribution has no Otsu split above its maximum, so nothing
**can** be marked.

**The post-hoc diagnostic (`scripts/cut_abstention_diagnose.py`, NOT
pre-registered and labelled so) runs the non-degenerate pan** — velocity varies
per step, as a real camera's does, while every frame remains a rigid translation
of the same source frame, so there is still **no discontinuity anywhere**:

| corpus | pan | motion sd | **`mag` marks** | **`xcorr` marks** |
|---|---|---|---|---|
| C1 | velocity ~U{1..8} | 9.18 | **106 / 149 (71%)** | 119 / 149 |
| C2 | velocity ~U{1..8} | 14.02 | **90 / 149 (60%)** | 116 / 149 |
| C1 | 90% slow, 10% fast | 9.10 | **16 / 149** | 112 / 149 |
| C2 | 90% slow, 10% fast | 13.14 | **16 / 149** | 124 / 149 |

**Pre-registered prediction 4 was RIGHT and my ARM was broken.** The magnitude
statistic cannot distinguish a pan from a cut; it needed a non-degenerate pan to
show it, and the "90% slow / 10% fast" row is the exact failure mode named in
H2 — the 16 marked steps ARE the fast pans.

### 7.3 WHAT ARM 2b's DEGENERACY DOES ESTABLISH, AND IT IS REAL

A uniformly fast sequence is uniformly normal. **A hand-set corpus-wide
threshold would have marked 100% of a 46-mean-motion pan as cuts; the derived
threshold marks 0%.** So the relativity is worth something concrete.

> **AND IT IS THE SAME PROPERTY AS THE FAILURE.** §13 says *"an absolute
> constant IS a view from nowhere"* and that gain control is what makes a scale
> RELATIVE. This rung is the limit case of that rule: **a threshold derived from
> the observation's own distribution cannot, even in principle, distinguish
> "everything is moving fast" from "everything just changed", because both are
> the same distribution.** Relativity buys transfer and costs absolute
> discrimination. That is not a bug in Otsu; it is what "no view from nowhere"
> means when the thing you need to detect IS an absolute event.

## 8. S1 (`XCorrPeak`) — MEASURED, AND IT IS NOT THE ANSWER

**On the real corpora S1 is byte-identical to the primary.** The row files have
the **same sha256** for every corpus and verdict
(`cut_rows_C1_ncc_mag.json` ≡ `cut_rows_C1_ncc_xcorr.json`, and so on) — it
selects the same steps `[34, 47, 79]` / `[23, 85, 143]` and therefore refuses
exactly the same probes. Every arm-1/2a/3 number in §3–§6 is the same for both.

**Under stress it is strictly worse.** On a pure rigid pan — the case it was
designed for, since a pan IS a shift — it marks **50–124 of 149** steps at every
velocity on both corpora, against `mag`'s 0. **The pre-registered weakness was
the wrong one.** I predicted saturation would leave it no dynamic range; it has
ample range (it separates the real cuts cleanly at a threshold of 0.0029). The
actual defect is that `xcorr_peak` sweeps integer lags over the OUTER index of a
frames×bands array with a **hardcoded band of 8**, so it registers a *linear*
lag, while `np.roll` produces a *cyclic* shift and `v·t` accumulates past the
±8 window. **A Term named for shift-invariance is not invariant to the shift you
happen to construct**, and this is a measured property of an existing engine
Term, reported as one rather than patched.

## 9. OBSERVABILITY — THE INVENTORY IS NON-EMPTY, WITH A CORRECTION TO MY OWN PREDICTION

`VISION_REDUNDANCY_RESULTS.md` ARM 4 found the marker inventory **EMPTY in all
26 probe runs including baseline**. Taken with that rung's **UNCHANGED** regex
(`unresolved|gap|refus|ambig|residual|stale|fallback|missing|degrad|absent|unknown`)
over this rung's own final graphs:

| configuration | inventory |
|---|---|
| inert baseline | `val:vd_answer=refused: 80` (C1) / `94` (C2), and **no `type:Refusal`** |
| armed | the same, **plus `type:Refusal: 32`** (C2 base 0), up to **96 per substrate**; **1 600 abstentions on C1 and 960 on C2** across the run |

**PREDICTION 8 WAS HALF WRONG AND THE CORRECTION MATTERS.** I predicted the
inventory would "become non-empty". It was **already non-empty at baseline** —
the verdict seed's `vd_answer = "refused"` matches `refus` in that regex. What
this rung actually adds is the **`Refusal` NODE**: a first-class graph object
carrying `reason = "prior_invalidated"` and `statistic`, i.e. **WHY** rather than
merely **THAT**. The redundancy rung's finding was about a *different* seed set
that never loaded the verdict seed; my restatement of it as "the inventory is
empty everywhere" was sloppier than the source.

**A second honest correction.** The marker snapshot recorded in
`cut_abstention_video.json` is from **base frame 0 only**, so C1's shows no
`Refusal` — C1's first cut is at step 34 and base 0's probes span steps 0–24.
That is a limitation of what I chose to record, not of the mechanism; the
per-row `abstain_reason` and `n_refusal_nodes` columns carry the full count.

**What reads it:** (a) the adapter's `read()`, which emits `abstain_reason` and
`n_refusal_nodes` per row and is what §3–§6 are computed from; (b) the
redundancy rung's marker-inventory logic, unchanged, which is what the table
above is; (c) `test_the_abstention_leaves_a_trace_the_existing_scanner_finds`,
which asserts both the node count and that each node carries its reason.

## 10. MY PREDICTIONS, SCORED (§3.7)

| # | prediction | outcome |
|---|---|---|
| 1 | in-graph Otsu reproduces the numpy PARTITION exactly; the threshold VALUE differs | **RIGHT, both clauses, both corpora.** C1 `[34,47,79]`, C2 `[23,85,143]`; values 11.06 vs 27.29 and 4.46 vs 24.61. |
| 2 | arm 1 largely forced; recall ≥0.80 on catastrophic frames, **under 0.30 pooled at Δ=1** | **RIGHT.** 1.0000 on all-16-failed; Δ=1 increments are +0.1023 and +0.1333, both **NULL**. |
| 3 | arm 2a passes and the pass is WEAK EVIDENCE | **RIGHT**, and I said so before measuring: exact +0.0000 in all four cells, on a 4×–10× separation that a wide range of thresholds would also clear. |
| 4 | arm 2b FAILS for `mag` at v ≥ 4 | **RIGHT IN SUBSTANCE, WRONG ON THE ARM — and the arm was mine.** The pre-registered arm PASSED because I built a zero-variance pan. The non-degenerate pan fails at 71% / 60%. **This is the most useful error in the rung: I wrote a stress test that could not stress.** |
| 5 | arm 4 FAILS — Otsu splits a cut-free sequence anyway | **RIGHT, and worse than I expected.** Not merely non-zero: 36% of C2's cut-free run, at magnitudes an order of magnitude below a real cut. |
| 6 | S1 two-sided; I feared saturation | **WRONG ON THE MECHANISM, RIGHT TO DOUBT IT.** No saturation — it separates real cuts cleanly. It fails on the lag geometry instead, and is byte-identical to the primary where it works. |
| 7 | arm 3 exact | **RIGHT.** 0 of 8 000 / 8 640 rows differ across 20 fields, all four cells. |
| 8 | the marker inventory becomes non-empty | **HALF WRONG** — it was already non-empty at baseline (§9). The `Refusal` node is what is new. |
| 9 | large increment on cut trials, exactly zero off them; H0 if V3 already covers it | **RIGHT.** +0.8353 / +0.9280 and exactly +0.0000. **H0 rejected.** |

**Five right, one right-in-substance-with-a-broken-arm, one half, one wrong, one
right-to-doubt.** The two errors worth keeping are 4 and 8, and both are of the
same kind: **I checked whether the mechanism did the right thing more carefully
than I checked whether my instrument could tell.**

## 11. BOUNDS ON EVERYTHING ABOVE (§8)

- **Toy resolution.** 24×24 frames, 6×6 regions. Nothing here is a claim about
  video at any real resolution; the measured O(N^1.887) scale wall is untouched.
- **Two episodes, never pooled.** One cartoon, one nature documentary.
- **The statistic and the comparator read the same grey pixels.** Declared in
  the pre-registration and unchanged by the result: this is **weaker
  independence than the salience rung's chroma argument.** The defensible claim
  is only that the cut statistic is **not computed by the component whose
  failure it predicts** — no codebook, no orbit, no region Argmax enters it.
- **Arm 2a is under-powered by construction** (§4) and arm 2b as
  pre-registered was **degenerate** (§7.2). The arm that actually discriminates
  is arm 4, and it fails.
- **`is_cut` is per-STEP and abstention is per-PROBE.** A probe straddling a cut
  is refused wholesale. No partial credit, no per-region abstention, no attempt
  to answer the regions a cut did not touch — and §6 shows that costs 13% of
  correct answers on marked probes.
- **The Δ=1 cut stratum is small** (C2: 23 error trials over 7 frames) and every
  number from it carries its n. The Δ=1 NULLs are consistent with the
  pre-registered prediction but are not strong evidence on their own.
- **The abstention is not free and its cost is not modelled.** Refusing is
  scored here as "not wrong"; nothing in this rung says what a downstream
  consumer does with 1 600 refusals.
- **Nothing was learned.** No codebook growth, no training, no accumulation.
- **§9:** no default moved, no committed seed edited, no Rust touched. The new
  seed ships inert and is not boot-loaded.

## 12. VERIFICATION

| check | result |
|---|---|
| `tests/test_engine_provenance_migrated.py` (own step, before any number) | **7 passed, exit 0** |
| `bash scripts/rung7_vision_bench.sh` at the branch base, `data/` symlinked | **222 passed, exit 0** (147.8 s) |
| `bash scripts/rung7_vision_bench.sh` after the rung | **222 passed, exit 0** (see the ledger commit) |
| `tests/test_cut_abstention_migrated.py` | **15 passed** |
| in-graph motion vs numpy reference | **exact, 1e-9, every step, both corpora** |
| in-graph Otsu partition vs numpy Otsu partition | **identical, both corpora** |
| comparator unmoved by the arming | **True, all four corpus×verdict cells** |
| arm 3 byte-identity off cut frames | **0 differing rows of 33 280** |
| `mag` and `xcorr` row files on the real corpora | **identical sha256, all 4 pairs** |
| constant-velocity pan degeneracy | **sd = 0.0, 1 distinct value**, all velocities, both corpora |

## 13. WHAT I WOULD PRE-REGISTER NEXT

**Not "a better threshold."** §7.3 argues the failure is structural: a
distribution-relative threshold cannot detect an absolute event, and tuning
Otsu, swapping it for a mixture model or adding a percentile floor all re-enter
the magic-number regime §13 forbids. The aimed-at next rung is **a threshold
with a NULL — an abstention that can decline to abstain.** Two candidate
mechanisms, both parameter-free and both expressible in existing Terms:

1. **The refusal floor precedent, applied to motion.** `vd_refuse` derives its
   floor from probes the substrate *holds* (the G2c noise draws) rather than
   from the sequence under test. The motion analogue is a **held expectation** —
   the distribution of motion this agent has seen before — so "a cut" becomes
   "motion unlike anything I hold", which HAS a null: a sequence resembling what
   it holds produces no marks. This is the one I would pre-register first,
   because the machinery already exists in the seed next door.
2. **Two-sided evidence rather than a split.** Otsu asks *where* to split; it
   never asks *whether*. A between-class variance that must exceed what the
   same statistic yields on a **shuffled** copy of the same steps is a
   permutation null, costs one more `Sum` in the same rule, and would return
   "no cut here" on §7.1's cut-free runs.

Named and explicitly NOT done here so they are not confused with results:
(a) **per-region abstention** — the §11 bound, which would recover the 13% of
correct answers a wholesale refusal discards; (b) a **2-D registration residual**
(the honest version of S1's intent, which needs a Term `XCorrPeak` is not);
(c) **anything at Δ=1** — §3 shows that failure is region-level and this
mechanism is the wrong instrument for it, which the salience rung already said.
