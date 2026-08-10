# VIDEO PROBE — RESULTS: the failure map

*Pre-registration: `VISION_VIDEO_PROBE_PREREG.md`, committed BEFORE the run at
`0fd1536a3d8f37e483fcb6b655420fe622389d05` (base `328065b62a31cf1daeb601557f21a0d331a2aed2`).*

**Engine (§10):** `7d5f50c18673 @ /home/matt/ozma/internal/research/experiments/gamma-substrate/runners/dsl/python/substrate_rs/_native.abi3.so`
— `shared` build, **Rust source byte-identical**; this rung adds no Rust.
**Machine:** AMD Ryzen 5 9600X, 12 logical cores.
**Selector (§12):** `scripts/video_probe_measure.py` (confirmatory) +
`scripts/video_probe_diagnose.py` (post-hoc diagnostics) +
`scripts/video_probe_explore_seam.py` (exploratory, §2.4b) — all three kept separate.
**Raw:** `results/video_probe.json` (confirmatory), `results/video_probe_diagnose.json`
(diagnostics), `results/video_probe_seam_explore.json` (exploratory, §2.4b).
**Seeds:** block 54000–54999 claimed; **none consumed** (the run was fully
deterministic under fixed positional indices).

---

## 0. THE HEADLINE, IN ONE PARAGRAPH

**The pipeline does not fall over on real video — it degrades in a specific,
ordered way, and the first HARD blocker is not the one predicted.** The retina
runs and is interpretable. Motion/cost runs. Proto-objects run and **silently
return nothing**. The identity layer is **never reached, because the seam to it
does not exist** — though forcing that seam by hand shows it is missing rather
than impossible. And underneath all of it, the O(N²) drive makes native-resolution video
arithmetically unreachable: **one 1920×1080 frame extrapolates to 164 hours**,
and a real-time budget affords an **18×18** field. The supervisor's prediction —
*"axes are GIVEN, not learned, and that breaks first"* — is **CONFIRMED as a real
bound, REFUTED as the FIRST one, and narrower than predicted**: it bites at
proto-objects (where the percept is a function of an adapter-chosen threshold),
not at the identity layer (whose input format turned out reachable from pixels).

---

## 0.1 ⚠️ THE TIMING NUMBERS WERE TAKEN UNDER CONCURRENT LOAD — found after the run

**§11 rule 5: *"Long-running measurement is not a lock. Another agent may commit,
merge, or rebase under you."* It applies to the CPU too, and I did not check
before measuring.**

Discovered by `ps` while the regression bench ran: **another agent, in worktree
`agent-aa9def1a0f13b03bb`, started a full `pytest -k migrated` at 07:31:36**, and
my confirmatory artifact was written at **07:34:38**. Load average during the
window: **4.40 on 12 cores**. My own regression bench was also running during the
diagnostics (07:53) and the exploratory probe (07:55).

**What this contaminates, and what it does not** — separated by whether the
quantity is deterministic:

| stage | quantity | contaminated? | evidence |
|---|---|---|---|
| S1 | fire % | **NO** | deterministic; D1's BSDS value reproduced to 12 significant figures across separate runs |
| S3 | proto counts, components | **NO** | deterministic; byte-identical rows across two separate diagnostic runs |
| S4 | enumeration | **NO** | structural, no timing |
| **S2** | **cost, CV, ρ** | **YES** | wall-clock under contention |
| **S5** | **absolute ms** | **YES** | wall-clock under contention |
| S5 | **exponent** | **partly** | all four sizes measured in one window, so contention is largely common-mode; the fit r²=0.997 and the exponent 1.887 sits close to the committed synthetic 1.988 measured on an idle machine |

**The direction matters, and it cuts against my own preferred reading.**
Scheduler noise adds cost variance that is **uncorrelated with content** — so it
**inflates CV** and **dilutes ρ**. CV is precisely the half of S2's decision rule
that blocked the **FLAT** verdict (ρ=0.2998 cleared its half; CV=0.2197 missed
its by 2.2×). **So it is likely that FLAT was withheld because of machine load,
not because of the substrate.** I am **not** re-deciding the pre-registered
verdict on that reasoning (§5) — I am recording that the verdict is weaker than
it looks, in the direction of the refutation I predicted.

**§4 corollary this earns:** *check what else is running before you record a
wall-clock number.* This arc already has a rule that every number needs its
engine, its commit and its selector (§12). **It needs one more: its machine
state.** A contended timing is a rumour in the same way a stale binary is.

---

## 1. CORPUS ACTUALLY USED (§2 of the prereg; no substitution)

| source | what | counts |
|---|---|---|
| **Jellyfin** (live, HTTP stream, PyAV) | *Middlemost Post* S2E1 "Parker Gets Rich", episode id `08630d4b7b215c469df19b9c42d7b617` | catalogue **46 series**; **23 episodes** in the chosen series; **150 frames** decoded, every 2nd decoded frame from t=300 s, area-averaged to 24×24 grey 0–255; decode **1.92 s** |
| **BSDS300** (`data/vision_curriculum/BSDS300`, via the §10.2 symlink) | real natural photographs | **300 jpg** (200 train / 100 test); **12** centre-crops used as the natural-statistics control |

Episode and frame selection are **fixed positional indices** (sorted series,
sorted episodes) — deterministic, no content decision, no seed drawn.

**Scope (§8).** ONE episode of ONE broadcast cartoon series, plus 12 BSDS crops.
This is not a survey of video. Every S1/S2/S3 number below is conditional on that
corpus, and the cartoon-vs-photo contrast in §2.1 is the reason that matters.

---

## 2. PER-STAGE RESULTS

### S1 — RETINA on real video: **RUNS, INTERPRETABLE, INDETERMINATE density**

Controls pass (§1 cl.4): uniform field **0.00%** fire (floor calibrated);
hard edge **25.0%** fire at **mean distance 1.5** from the boundary (sparse and
boundary-localised). **The instrument is alive**, so the number below is readable.

| | value |
|---|---|
| fire, mean over 40 real frames | **46.64%** |
| sd / min / max | 6.85 / 35.76 / 64.93 |
| pre-registered verdict | **INDETERMINATE (25–50%)** |

**Prediction: WRONG.** I predicted dense (>50%), in family with the committed
BSDS 73.55%. It came in at 46.6% — below the threshold I set.

#### 2.1 Why — and this is the useful part (diagnostic D1)

The **same instrument** on real BSDS300 photographs, same grid, controls passing:

| corpus | fire |
|---|---|
| BSDS300 natural photographs | **80.30%** |
| Jellyfin broadcast cartoon | **46.64%** |

So the density gap is **a property of the corpus, not of the instrument**.
Natural photographs saturate the retina (80.3%, consistent with the committed
73.55% at grid 32 — an independent reproduction on a different grid). Broadcast
cartoon is **~1.7× sparser**, because cartoon statistics are flat-region +
hard-edge — exactly the difference `vision_corpus.py`'s own docstring names as
the reason BSDS is carried as the non-circular control.

**What this licenses:** the "sparse residual" premise is **less dead than the BSDS
number alone suggested** — on cartoon video it is merely bad (47%), not
catastrophic (80%). **What it does NOT license:** any claim that the retina
sparsifies. 47% of cells firing is not a sparse code, and the DoG reference on
still images is 17.6%. It is dense; it is just less dense on cartoons.

### S2 — COMPUTE vs SURPRISE: **INDETERMINATE**, and the confound is NOT the cause

| statistic | value |
|---|---|
| n (paired frames) | **149** |
| Spearman ρ(surprise, cost) | **0.2998** |
| cost ms mean / sd / CV | 102.84 / 22.59 / **0.2197** |
| cost ms min / max | 70.50 / 180.54 |
| surprise min / median / max | 0.00109 / 0.3556 / **52.34** |
| surprise max/min ratio | **48 236×** (the axis genuinely varies — control passes) |
| pre-registered verdict | **INDETERMINATE** |

**Instrument check (§1).** ρ is computed by a hand-rolled rank correlation (the
tree carries no scipy dependency for the measure itself). It was validated
against `scipy.stats.spearmanr` on 5 random samples — agreement to **5.6×10⁻¹⁷** —
and on a deliberately tie-heavy vector, where average-rank handling is the thing
that usually goes wrong: **0.861640 vs 0.861640**. The statistic is not the
source of the ambiguity below.

The decision rule required **ρ<0.3 AND CV<0.10** for FLAT. **ρ=0.2998 cleared its
half by 0.0002; CV=0.2197 missed its half by 2.2×.** So the verdict is
INDETERMINATE, and I am **not** rounding ρ down to claim the refutation (§5).

**Prediction: PARTIALLY WRONG.** I predicted ρ≈0 with small CV — a clean
refutation of compute-∝-surprise. Cost turned out to vary **2.6× across frames**
and to correlate **weakly but positively** with surprise.

#### 2.2 The confound I introduced, and its measured size (diagnostic D2)

The committed drive convention ignites the wave every 5th frame
(`IGNITE_EVERY=5`), adding cost **independently of surprise** on 20% of frames. I
did not declare this in the prereg. Stratifying:

| stratum | n | ρ | CV |
|---|---|---|---|
| pooled (the pre-registered value, reproduced) | 149 | 0.2837 | 0.2173 |
| **non-ignite** (confound absent) | 120 | **0.3131** | **0.2133** |
| ignite | 29 | 0.1911 | 0.2292 |

The ignite phase costs only **+3.9% of the pooled mean**. **The confound explains
essentially none of the spread** — removing it moves ρ from 0.28 to 0.31 and CV
from 0.217 to 0.213. So the INDETERMINATE verdict is **diagnosed, not excused**:
cost genuinely varies with content, weakly.

#### 2.3 Does ρ REPLICATE? (diagnostic D4) — the sign does, the magnitude does not

§4: *"replicate on fresh seeds before believing — p=0.013 and p=0.0016 both
evaporated."* A single ρ=0.30 off one pass is exactly the shape of finding this
arc has twice watched evaporate. Eight independent passes over the same frames:

| pass | ρ(surprise, cost) | ρ(frame index, cost) — the DRIFT control |
|---|---|---|
| confirmatory (S2) | 0.300 | — |
| D2 pooled | 0.241 | — |
| standalone | 0.184 | **−0.184** |
| D4 rep 0 | 0.401 | +0.110 |
| D4 rep 1 | 0.360 | +0.310 |
| D4 rep 2 | 0.384 | +0.104 |
| D4 rep 3 | 0.257 | +0.040 |
| **D4 mean ± sd** | **0.351 ± 0.056** | |

**ρ is positive in 8 of 8 passes** — the sign is robust. **Its magnitude spans
0.184–0.401, a 2.2× swing** — the effect size is not.

**And a confound I found by looking for it.** Surprise itself drifts across the
sequence (ρ(index, surprise) = **+0.284**, identical in every pass — same frames).
So any drift in *cost* over the run aligns with surprise by construction. Sorting
the passes by their drift makes the contamination visible: the pass with the
**largest positive** cost drift (+0.310) gives the **high** ρ=0.360, and the pass
with a **negative** drift (−0.184) gives the **lowest** ρ=0.184. **The
least-contaminated estimates (|drift| ≤ 0.04) are ρ ≈ 0.18–0.26.**

**Honest reading.** Compute weakly and consistently tracks surprise, at ρ≈0.2–0.3
once drift is accounted for — **under 9% of rank variance, and part of even that
is a timing artifact.** Compute is **much closer to flat than to proportional**.
The compute-∝-surprise claim is **not refuted and not supported**; it is measured
for the first time, at a value far too small to carry the architecture that was
being hung on it. **Any future claim of "compute ∝ surprise" must beat ρ≈0.3 and
must report its drift control**, because this one nearly reported an artifact as
a mechanism.

### S3 — PROTO-OBJECTS: **FAILS**, and it fails by returning NOTHING

**Positive control reproduces the committed answer exactly** (§1 cl.4): the
synthetic closed figure gives **1 proto, 24 members, 7 sweeps, 1.76 ms** — the
values `border_ownership_measure.py::arm_figure_ground` asserts. The instrument
is alive, so the real-frame nulls below are real nulls.

Pre-registered run (frames 0,1,2 at grid 16, k ∈ {2,4,8,16}):

| criterion | threshold | measured | |
|---|---|---|---|
| object-scaled: `n_proto/n_cells` | < 0.05 | **0.0156** | **PASSES** |
| k-stable: max/min over k | < 3.0 | **4.0** | **FAILS** |
| verdict | | **FAILS — k-unstable** | |

**Prediction: HALF WRONG, and the half that was right was right for the wrong
reason.** I predicted proto count would **explode with texture** (fail the
object-scale half) *and* swing with k. It does **not** explode — the flood is
well-behaved and the count stays small. It fails purely on k, and it fails
**downward**.

#### 2.4 The sampling defect, and the repaired result (diagnostic D3)

Frames 0,1,2 came from **one static shot** and returned **byte-identical rows** —
the pre-registered S3 had an effective **n of 1, not 3**. Repeating the
**unchanged criterion** on frames spread across the whole sequence
(0, 25, 50, 75, 100, 125, 149) gives 6 distinct profiles over 7 frames:

| frame | k=2 | k=4 | k=8 | k=16 |
|---|---|---|---|---|
| 0 | 3 | 4 | 1 | **0** |
| 25 | 4 | 3 | 1 | **0** |
| 50 | 3 | 3 | 1 | **0** |
| 75 | 2 | **0** | **0** | **0** |
| 100 | 4 | 2 | **0** | **0** |
| 125 | 2 | **0** | **0** | **0** |
| 149 | 2 | 1 | **0** | **0** |

Against the reference 4-connected component count on the same grids:

| k | reference components | mean protos | mean ms |
|---|---|---|---|
| 2 | 10.3 | 2.9 | 7.7 |
| 4 | 38.4 | 1.9 | 21.6 |
| 8 | 79.3 | 0.3 | 22.1 |
| 16 | 127.6 | **0.0** | 34.5 |

**THE FINDING: at k=16, ALL 7 of 7 frames yield ZERO proto-objects. At k=8, 4 of
7 do. The regions are there — the reference count rises monotonically 10 → 128 —
but essentially none of them satisfy the enclosed/closed/singly-connected
predicate `bo_mint_enclosed` requires.** As quantization gets finer, the
substrate sees *more* structure and mints *fewer* percepts, converging on none.

**Why this is the dangerous failure mode, not the loud one.** The stage does not
crash, does not warn, and does not hit the step cap. It returns an **empty
result that is indistinguishable from "there is nothing here"** — the exact
disease §1.1 (guarded division), §10.2 (missing slab → fluent wrong answer) and
§12.3 (`Pick` silently returning one of N) are all instances of. **A rung that
fed real frames to this stage without the synthetic positive control would have
reported "the agent perceives no objects in this scene" and been wrong about
why.**

**And k is the whole story.** k is not derived from anything — I chose it, swept
it, and the percept is entirely a function of my choice. **This is the
"axes are GIVEN, not learned" bound in its most concrete measured form**: the
segmentation the proto-object stage operates on is supplied by the adapter, and
the stage's output tracks the adapter's arbitrary parameter, not the image.

### S4 — IDENTITY SEAM: **STRUCTURAL ABSENCE**

A positive enumeration over `domains/ scripts/ seeds/ substrate/ tests/`, with
the bridge defined as **dataflow** (a file that both touches `ProtoObject` and
constructs either a `["cell", …]` signature tuple or a `ShapeSignature` node) —
**not** as co-mention (§12.1: *"a claim about what code SELECTS is not established
by counting the tokens that select it. Read one."*):

| | count |
|---|---|
| files touching `ProtoObject` | **6** |
| files constructing `["cell", …]` signature tuples | **33** |
| files constructing `ShapeSignature` nodes | **56** |
| identity files, UNION (deduplicated) | **60** |
| **files doing BOTH** | **0** |

The 6 proto files are `domains/border_ownership_world.py`,
`domains/seed_registry.py`, `scripts/border_ownership_measure.py`,
`seeds/vision_border_ownership.json`, `seeds/vision_lighting_l4.json`,
`tests/test_border_ownership_migrated.py`.

**The crude first pass reported a bridge and it was FALSE** — two co-mentions,
both read by hand as §12.1 requires: `domains/seed_registry.py` names
`ProtoObject` only inside a **registration description string** (prose, not
code, and it constructs no cell tuple), and the other was **this probe's own
script**. Excluding the instrument itself and testing construction rather than
mention: **zero bridges.**

**Prediction: CORRECT.** No path exists. The proto-object layer and the identity
layer are **two disjoint subsystems that have never been connected**. Everything
above proto-objects in the arc — generator discovery, depth, category, style,
continuous pose, agnosia — consumes **hand-constructed symbolic relation tuples**
(`["cell", r, c, "red"]` with a declared `dim_types`), and **nothing in the tree
produces such a tuple from a pixel**.

This is an FM-0-class result (§13.2: *"works" and "is load-bearing" are different
properties*): **the entire identity half of the arc is, with respect to real
imagery, currently decorative.** It is correct, gated, tested — and wired to
nothing that a camera can reach.

#### 2.4b EXPLORATORY — what if the seam is FORCED? (`scripts/video_probe_explore_seam.py`)

**NOT a pre-registered result; nothing above or below depends on it.** S4's
decision rule was "report the absence and stop", and it does. But "no path
exists" does not distinguish *the seam is merely unbuilt* from *the seam is
unreachable at this grain*, and the next rung's pre-registration depends entirely
on which it is. So: one real 16×16 frame, quantized, hand-encoded as
`["cell", r, c, "v<k>"]` tuples (non-zero cells only — the most charitable
encoding, i.e. what a segmenter would hand over if one existed), presented to the
sd loop against its own held signature — **literal self-identity, the easiest
recognition that exists.**

| k | cells | held? | status | axes minted | ms |
|---|---|---|---|---|---|
| 2 | 142 | yes | `recognized_transformed` | 1 | 105 |
| 2 | 142 | no | `minted` | 2 | 0 |
| 4 | 207 | yes | `recognized_transformed` | 1 | 177 |
| 4 | 207 | no | `minted` | 2 | 0 |
| *synthetic 4-cell control* | 4 | yes | `recognized_transformed` | — | 2.8 |

**The identity layer INGESTS pixel-derived tuples and recognises them.** A 16×16
real frame becomes a 142–207-cell signature and decodes in 105–177 ms; the
held/not-held contrast behaves correctly (not held ⇒ mints). So the answer is
**(a): the seam is UNBUILT, not unreachable.** Building it is plumbing.

**And it bypasses S3 entirely** — these tuples came straight from quantized
pixels, not from proto-objects. Border-ownership is **not on the critical path**
to a first pixel→identity connection.

**What this does NOT show, and the caveats are large.** This is *literal
self-identity* — the same signature in and out. It says nothing about recognising
the same object in a *different* frame, under motion, or under any nuisance. The
status is `recognized_transformed` rather than `recognized` even for a byte-identical
signature, which is the rung-2 transform path firing with an identity delta and
is **not** investigated here. And 16×16 is well inside the toy regime S5 bounds.

### S5 — SCALE on real frames: **CONFIRMED quadratic**

| grid | cells | ms/tick | µs/cell |
|---|---|---|---|
| 12 | 144 | 7.76 | 53.9 |
| 16 | 256 | 28.28 | 110.5 |
| 24 | 576 | 114.53 | 198.8 |
| 32 | 1024 | 331.61 | 323.8 |

log–log fit of ms vs cells: **exponent 1.887, r² 0.9971** (n=4), against the
committed synthetic `fit_drive` exponent **1.988**.

**Prediction: CORRECT**, including its reasoning — per-cell cost is
content-independent, so real frames do not change the profile. The known scale
fact (*"the wall is the PyO3 boundary and then an O(N²) drive, not the ALU"*) is
**confirmed on real video**.

#### 2.5 What the exponent costs, extrapolated

| field | cells | per frame | fps |
|---|---|---|---|
| 24×24 (measured) | 576 | 115 ms | 8.7 |
| 64×64 | 4 096 | 4.7 s | 0.21 |
| 320×240 (QVGA) | 76 800 | 19.6 min | 0.00085 |
| **1920×1080 (native)** | **2 073 600** | **164 hours** | **1.7×10⁻⁶** |

**At a 23.976 fps real-time budget (41.7 ms/frame) the affordable field is 336
cells — an 18×18 image.** The source video is 1080p. **The gap between what the
substrate can watch in real time and what the camera produces is a factor of
~6 200 in cells, and ~10⁷ in time.**

---

## 3. THE FAILURE MAP — WHAT BREAKS, IN WHAT ORDER

| order | stage | status | signature |
|---|---|---|---|
| — | S1 retina | **runs, interpretable** | dense-ish (46.6% cartoon / 80.3% photo); not sparse, but alive and readable |
| — | S2 motion/cost | **runs** | cost varies 2.6×, ρ≈0.2–0.3 with surprise — weak, sign-robust, mechanism unknown; **timings taken under concurrent load, §0.1** |
| **1st (hard)** | **S5 scale** | **BLOCKS EVERYTHING** | O(N^1.89); real-time affords 18×18; native frame = 164 h |
| **2nd (hard)** | **S3 proto-objects** | **SILENTLY EMPTY** | 0 protos on 7/7 frames at k=16; percept is a function of an adapter-chosen k |
| **3rd (soft)** | **S4 identity seam** | **DOES NOT EXIST — but is PLUMBING** | 6 proto files ∩ 60 identity files = **0**; yet forcing the seam by hand works (§2.4b, exploratory) |

**The first hard blocker is SCALE, and it is not close.** Every representational
question is downstream of being able to look at more than 336 pixels, and at
1080p the substrate is ~7 orders of magnitude short.

**The supervisor's predicted blocker — "the axes are GIVEN, not learned" — is
CONFIRMED, and it is SECOND, and it is narrower than predicted.** Where it bites
is **S3**: the proto-object percept is a function of an adapter-chosen
quantization k, and vanishes entirely as k refines. Where it does **not** bite is
S4: the identity layer's input format turned out to be *reachable* from pixels
(§2.4b, exploratory) — the seam is missing, not impossible.

**Why the ordering matters for the next rung.** S3 is architectural, S5 is
arithmetic, and they are independent — fixing either does not help the other. The
cheapest real progress available is at toy resolution, bypassing S3 entirely.
**But a system that recognises objects in 18×18 images is what that will produce,
and it must not be reported as "learning by watching video."**

---

## 4. BOUNDS ON EVERYTHING ABOVE (§8)

- **One episode, one series, one cartoon.** S1/S2/S3 numbers are conditional on
  *Middlemost Post* S2E1 plus 12 BSDS crops. Broadcast cartoon is **not**
  egocentric video and its statistics are known to differ from natural scenes —
  measured here as 46.6% vs 80.3%.
- **S2's ρ is only PARTLY decomposed.** I measured that cost weakly tracks
  surprise, that the ignite confound does not explain it (+3.9% of mean), that
  the sign replicates 8/8, and that a cost-vs-time drift inflates the magnitude.
  **I did not find out what the residual mechanism is.** The candidate — that the
  change/sustained channels drive more cells on high-surprise frames, so more
  rules fire — is **untested**, and is a hypothesis for the next rung, not a
  finding.
- **S2's frames are NOT independent.** Consecutive frames of one shot are heavily
  autocorrelated, so the nominal n=149 overstates the effective n and no p-value
  is quoted for ρ. The replication across passes (D4) is the evidence carried
  here, not a significance test.
- **S3's k-sweep is 4 points on one grid (16×16).** Whether the collapse to zero
  is a k effect, a grid-size effect, or both is **not separated**. The reference
  component counts suggest k, but that is an inference, not a measurement.
- **S3's null is a null about `bo_mint_enclosed`'s predicate**, not about
  proto-objects in general. A different enclosure predicate might survive real
  imagery. Nothing here tests that.
- **S4 is a structural claim about THIS TREE at this commit**, established by
  enumeration over five directories and two construction forms. A bridge written
  in a form my two regexes miss would be missed. I read the co-mentions by hand;
  I did not read all 60 identity files.
- **S5's fit is 4 points over an 7.1× range in cells.** The extrapolation to
  2 073 600 cells is **3 orders of magnitude beyond the measured range** and
  assumes the exponent holds. It is an extrapolation, labelled as one. What is
  *measured* is 144–1024 cells.
- **No claim is made about accuracy, recognition rate, or learning.** Nothing was
  trained. Nothing was recognised. This rung measured only whether stages produce
  output, whether that output is meaningful by a pre-declared criterion, and what
  it costs.
- **THE TIMING NUMBERS (S2, S5-absolute) WERE TAKEN UNDER CONCURRENT CPU LOAD**
  from another agent's worktree — see §0.1. The deterministic stages (S1, S3, S4)
  are unaffected and were verified so by exact reproduction. S5's *exponent* is
  largely common-mode; S5's *absolute* ms and all of S2's spread are not.
- **§9:** no default moved, no seed edited, no rule added, no Rust touched.

---

## 4.1 THE REGRESSION ORACLE — and a CORRECTION to how it was specified

**Result: GREEN.**

| selector | result | exit |
|---|---|---|
| `scripts/rung7_vision_bench.sh` (the §12 NAMED 20-file selector) | **200 passed, 0 failed, 0 skipped** in 167 s | **0** |
| `tests/test_sdloop_vision_migrated.py` (the **sd orbit law** `{2:1, 3:2, 4:2, 6:2, 12:4}`) | **8 passed** | **0** |
| the 36 post-rung-7 vision-arc files (agnosia, border-ownership, category, colour, depth, stereo, lighting L1–L4, style, pose, similarity, uniqueness, McCollough, Troxler, …) + this rung's provenance test | **539 passed, 0 failed, 5 skipped** in 952 s | **0** |

The **5 skips are this rung's OWN provenance test** skipping on its
not-yet-substituted `RUNG_SHA` placeholder — not a pre-existing dormant gate.
Every other test in the arc ran. Once pinned (§4.2) it is **5 passed**.

## 4.2 THE PROVENANCE SELF-AUDIT — pinned to BOTH endpoints, and POSITIVE-CONTROLLED

`tests/test_video_probe_provenance_migrated.py` pins **`git diff BASE_SHA
RUNG_SHA`** — never `HEAD`, never the working tree (§12.3; this defect has
occurred three times in this arc). It asserts this rung's own commit range adds
no Rust, adds/edits no seed, touches only files it owns, and that its one edit to
the shared `VISION_PROTOCOL.md` is exactly **one appended ledger row with no
deletions**. A fifth test asserts that commits *after* `RUNG_SHA` add only the
test file itself — closing the last place a mutable endpoint could hide.

**It was positive-controlled, and it FOUND A BUG IN ITSELF FIRST.** On its first
pinned run the ledger test failed with *"expected ONE appended ledger row, got
0"* — because **git reports `--name-only` paths from the git ROOT but resolves a
PATHSPEC relative to CWD**, and the suite runs from the experiment dir. Fixed
with a `:/` root-magic pathspec. Then the control proper: widening `BASE_SHA` to
an old arc commit (a range that really does contain Rust, seed and foreign
edits) turns the gate **RED on 4 of 5**, and restoring it turns it **GREEN on
5 of 5**. **A gate that has only ever been seen to pass is not a gate that has
been tested.**

**200/0 is exactly the §10.2 figure for `data/` PRESENT** (`190 passed / 10
skipped` without it, `200 passed / 0 skipped` with) — so the `data/` symlink is
confirmed live and the 10 BSDS-gated tests actually ran rather than silently
skipping.

**THE CORRECTION.** The oracle was specified to me as *"`pytest tests/ -k
migrated` must stay green (~200/0 with `data/` symlinked; ~190/10 without)"*.
**Those two numbers are `rung7_vision_bench.sh`'s, not `-k migrated`'s.**
Measured here: **`pytest tests/ -k migrated` collects 3487 tests**, not ~200 —
`-k` is a substring match over the whole node id (§12), and "migrated" is a
suffix on most of this tree's test files. At the observed rate under load it
would run for **tens of hours**, and 24% of it took over an hour.

This is §12's own defect one more time: **a selector quoted without its
definition drifts into a number that belongs to a different selector.** The 200/0
figure is real and is reproduced above — it just belongs to the named file list.
**Reported, not silently substituted:** the full `-k migrated` sweep was started,
run to 24%, and stopped once its true size was measured; the protocol's own named
selector was run to completion instead.

---

## 5. WHAT THE NEXT RUNG SHOULD PRE-REGISTER AGAINST

Ranked by what the evidence actually supports:

1. **CROSS-FRAME IDENTITY ON REAL PIXELS, at toy resolution.** The exploratory
   probe (§2.4b) removes the question I expected to recommend: the identity layer
   already ingests pixel-derived tuples and self-recognises a real 16×16 frame in
   ~100 ms. So the pre-registration should NOT be *"can pixels reach the identity
   layer"* (answered: yes, it is plumbing) but the first question that is
   genuinely open: **does a region recognised in frame t get recognised as the
   SAME thing in frame t+1, under real motion, above a shuffled-frame floor?**
   That is the smallest real instance of "recognition turns unlabelled experience
   into learning", it is measurable today at 16–24 px with no scale work, and it
   has a clean null. **Critically, it must NOT route through border-ownership** —
   §2.4b built the tuples straight from quantized pixels, so S3 is not on the
   critical path.
2. **S3's enclosure predicate — but ONLY if proto-objects are wanted for their
   own sake.** The measured fact to pre-register against is *0 protos on 7/7
   frames at k=16, and the count falling monotonically as quantization refines*.
   The question is whether an enclosure predicate exists whose output is **stable
   across k**; if not, the proto percept is the adapter's threshold wearing a
   percept's clothes. **This is now demoted** — §2.4b showed the identity path
   does not need it.
3. **S2's ρ, decomposed.** Cheap, and it turns a weak correlation into a
   mechanism or kills it. Pre-register: does driven-cell count mediate the
   surprise→cost relation, **with the cost-vs-time drift control included from
   the start** (§2.3 — it nearly manufactured the effect). If mediated,
   compute-∝-surprise has a real substrate and a number to improve; if not, the
   ρ≈0.2–0.3 is timing structure and should be retired rather than cited.
4. **Scale — but as a BUILD TASK, not a rung.** The standing directive is that
   engine limits are build tasks, not vetoes. The measured profile says the drive
   is quadratic in cells and the FFI is linear; the Amdahl decomposition already
   committed in `assembled_eye_scale.py` says where the parallelisable fraction
   is. **This should not be pre-registered as a hypothesis — there is nothing to
   discover, only work to do.** It is nonetheless the FIRST hard blocker for
   anything at real resolution, and no toy-resolution result should be reported
   as if it were not.

**What should NOT be pre-registered:** anything of the form *"the agent learns by
watching video."* On the measured numbers the substrate can watch an 18×18 field
in real time, produces zero proto-objects on most real frames, and has no path
from any percept to its identity layer. That claim is **two hard blockers and one
unbuilt seam away**, and this rung's job was to say so with numbers rather than to
find out later.
