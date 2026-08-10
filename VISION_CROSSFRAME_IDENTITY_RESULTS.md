# CROSS-FRAME IDENTITY ON REAL PIXELS — RESULTS

*Pre-registration: `VISION_CROSSFRAME_IDENTITY_PREREG.md`, committed BEFORE the
run at **`391d2283`** (base `main` HEAD **`40318951`**).*

**Engine (§10):** `7d5f50c18673` @
`runners/dsl/python/substrate_rs/_native.abi3.so` — **this rung's OWN pinned
copy** (see §0.1). Rust source unmodified; **this rung adds no Rust**.
**Machine:** AMD Ryzen 5 9600X, 12 logical cores, **under concurrent load
throughout** (another agent's `pytest -k migrated` at ~90% of a core; load
average 3.4–4.4). Every quantity below except `run_ms_per_base_frame` is
deterministic under fixed seeds and indices — with **one measured exception,
§4.2**, which is itself the finding.
**Selector:** `scripts/crossframe_identity_measure.py` (confirmatory) +
`scripts/crossframe_identity_diagnose.py` (post-hoc, kept separate) +
`scripts/crossframe_identity_report.py` (presentation only).
**Raw:** `results/crossframe_identity.json`,
`results/crossframe_identity_rows_{C1,C2}.json`,
`results/crossframe_identity_diagnose.json`.
**Seeds:** block **55000–55999** claimed; used for codebook insertion-order
permutations, A2's distant-frame draws, A3's within-region permutations and the
G2 noise probes.

---

## 0. THE HEADLINE, IN ONE PARAGRAPH

**Cross-frame identity holds — and the measurement of HOW it holds is worth more
than the verdict.** H1 CROSSES on both real-motion corpora by a very wide margin
(cartoon **0.958** vs an arrangement floor of **0.203**; live-action **0.918** vs
**0.166**), and the arrangement floor is genuinely non-trivial at ~3× chance. But
the mechanism is not invariance. **The graph's score is EXACTLY pixel Hamming
overlap — `xf_max == nn_score` on 74 560 of 74 560 trials, every arm, every
corpus, every k — so what is being measured is PERSISTENCE, not recognition.**
The synthetic-displacement corpus puts a number on it: on real photographs,
identity survives **one pixel** of translation (d=1: 0.464 vs floor 0.182) and is
**already indistinguishable from the arrangement floor at two** (d=2: 0.229 vs
0.172, CIs overlapping), and is at chance by d=6. **The real-video Δ curves are
therefore measuring how much sub-two-pixel motion a broadcast frame step
contains, not a representational invariance.** Two defects were found in my own
instrument and are reported in full: the codebook was silently **33-way, not
16-way** (§4.1), and one base frame's 272 answers were **not reproducible** under
byte-identical replay (§4.2) — an `Argmax`/`Eq` disagreement inside one rule
application that is an engine-level inconsistency, not a modelling artifact.

---

## 0.1 THE ENGINE MOVED UNDER ME MID-RUN — caught before any number was taken

At claim time the worktree had no built artifact, so the canonical tree's
`_native.abi3.so` was symlinked and its Rust source verified **byte-identical**
to this worktree's (`diff -r runners/dsl/src`, clean). **Twenty minutes later the
provenance line read `** WRONG ENGINE — built from DIFFERENT Rust source **`**:
a concurrent agent had edited six `.rs` files in the canonical tree. The binary
itself was unchanged (`sha256 7d5f50c1…` before and after), but it was one
`maturin develop` away from being replaced underneath a running measurement.

**Fix: the binary was COPIED into this worktree and pinned there**, sha verified
identical, before the confirmatory run started. Every number below came from that
pinned copy.

**§11 rule 5 earns a corollary, the twin of the video probe's §0.1.** That rung
learned *check what else is running before you record a wall-clock number.* This
one adds: **a SHARED BUILD is shared mutable state. Symlinking another tree's
engine is borrowing a file another agent is allowed to overwrite.** Copy it,
hash it, and record the hash — a shared `.so` is a rumour in the same way a
stale one is.

---

## 1. CORPORA ACTUALLY USED (§2 of the prereg; no substitution)

| id | what | statistics | motion | counts |
|---|---|---|---|---|
| **C1 CARTOON** | Jellyfin, *Middlemost Post* S2E1 "Parker Gets Rich", `08630d4b7b215c469df19b9c42d7b617` | broadcast cartoon | REAL | 150 frames, every 2nd from t=300 s, 24×24 grey; **100 base frames**; **1600 trials per (arm, Δ)** |
| **C2 LIVE-ACTION** | Jellyfin, *Secrets of the Zoo: Down Under* S3E15 "Penguin SOS", `119eca433329b36b19e5d69fef84966e` | natural photographic | REAL | same protocol; **100 base frames**; **1600 trials per (arm, Δ)** |
| **C3 APERTURE** | BSDS300, 12 photographs, 24×24 centre window translated by a KNOWN d | natural photographic | **SYNTHETIC (known d)** | 12 × 7 displacements × 16 regions = **192 trials per (arm, d)** |

Series and episode were chosen by fixed positional index into the sorted
catalogue (index 0 and index 3), as pre-registered. **Measured inter-frame
motion** (mean |frame_{t+1} − frame_t|, 0–255 scale): C1 **2.202** (sd 8.390,
min 0.001, max 52.343); C2 **2.924** (sd 6.125, min 0.284, max 45.738). Both
distributions are heavy-tailed — mostly near-static steps punctuated by shot
cuts — and that shape matters for reading §2.2.

**Scope (§8).** Two episodes of two series plus 12 photographs. Not a survey of
video. Every number is conditional on this corpus.

---

## 2. THE ARMS

Chance as pre-registered: **1/16 = 0.0625**. (The codebook was actually 33-way —
§4.1 — which makes 0.0625 the *conservative* bar; the empirical noise floor
lands at ≈1/16, not 1/33, which is itself the evidence that the 17 extra entries
are inert.)

### 2.1 THE HEADLINE CELL — k=4, Δ=1

Primary statistic is the **frame-level** mean over 100 base frames with a 95%
t-CI (the correct unit — §7). Trial-level Wilson CIs (n=1600) are given as
pre-registered and are anticonservative.

| corpus | arm | frame acc [95% t-CI] | trial acc [95% Wilson] | answer entropy | tie>1 |
|---|---|---|---|---|---|
| **C1** | **A1 REAL** | **0.9581 [0.9194, 0.9968]** | 0.9581 [0.9472, 0.9669] | 1.010 | 0.003 |
| C1 | A2 temporal-shuffle | 0.1244 [0.0960, 0.1528] | 0.1244 [0.1091, 0.1415] | 0.963 | 0.180 |
| C1 | A3 arrangement-destroyed | 0.2025 [0.1860, 0.2190] | 0.2025 [0.1835, 0.2229] | 0.959 | 0.226 |
| **C2** | **A1 REAL** | **0.9181 [0.8893, 0.9470]** | 0.9181 [0.9037, 0.9306] | 0.999 | 0.087 |
| C2 | A2 temporal-shuffle | 0.2456 [0.1874, 0.3038] | 0.2456 [0.2252, 0.2673] | 0.915 | 0.288 |
| C2 | A3 arrangement-destroyed | 0.1663 [0.1532, 0.1793] | 0.1663 [0.1488, 0.1853] | 0.855 | 0.423 |

**PRE-REGISTERED VERDICT: H1 CROSSES on C1 and on C2.** Primary and secondary
statistics agree on both corpora. A1's lower bound clears both floors' upper
bounds and chance, with no overlap anywhere close.

**The floors are not trivial, which was the point.** A3 sits at **3.2×** chance
on C1 and **2.7×** on C2 — a region's value histogram alone carries real
identity information, and the hypothesis had to beat that, not chance. A2 sits at
**2.0×** and **3.9×** chance. On C2 the *binding* floor is A2, not A3.

**Both floors are ALIVE (§1.1 clause 4):** answer entropies 0.855–0.963 against
a maximum of 1.0, i.e. every floor arm is answering across essentially the whole
codebook rather than collapsing onto one name. A floor produced by a dead arm
would show entropy near 0; none does.

### 2.2 THE Δ CURVE (k=4) — H2, reported not gated

Frame-level accuracy, C1 / C2:

| Δ (decoded frames) | A1 C1 | A2 C1 | A3 C1 | A1 C2 | A2 C2 | A3 C2 |
|---|---|---|---|---|---|---|
| 1 | **0.9581** | 0.1244 | 0.2025 | **0.9181** | 0.2456 | 0.1663 |
| 2 | 0.9256 | 0.1525 | 0.2106 | 0.8775 | 0.2412 | 0.1694 |
| 5 | 0.8381 | 0.1888 | 0.1837 | 0.7394 | 0.2056 | 0.1519 |
| 10 | 0.6944 | 0.1944 | 0.1475 | 0.5194 | 0.2019 | 0.1325 |
| 25 | 0.3894 | 0.1444 | 0.0994 | 0.2531 | 0.2144 | 0.1156 |

**Identity horizon** (largest Δ at which A1 stays CI-separated from both floors):
**C1 Δ=25, C2 Δ=10.** At Δ=25 on C2, A1 0.2531 [0.2000, 0.3063] overlaps A2
0.2144 [0.1598, 0.2689] — identity is gone by ~2 s of live-action video.

Monotone decay on both corpora, slower on cartoon than on live action, exactly as
predicted — and §2.4 shows why that is a statement about pixel motion rather
than about representation.

### 2.3 k-SENSITIVITY (Δ=1; declared in advance as a sensitivity check, every
cell reported)

| corpus | k | A1 | A2 | A3 |
|---|---|---|---|---|
| C1 | 2 | 0.9400 | 0.1250 | 0.1550 |
| C1 | **4** | **0.9581** | 0.1244 | 0.2025 |
| C1 | 8 | 0.9706 | 0.1575 | 0.3250 |
| C2 | 2 | 0.8237 | 0.2350 | 0.1556 |
| C2 | **4** | **0.9181** | 0.2456 | 0.1663 |
| C2 | 8 | 0.9619 | 0.2650 | 0.2806 |

**H1 CROSSES at every k on both corpora** — the verdict is not an artifact of the
one hand-set value. Finer quantization raises A1 *and* A3 together (more levels ⇒
more distinctive histograms ⇒ a harder floor), so the margin is broadly stable
while both ends move.

### 2.4 THE BOUND THAT MATTERS — C3, KNOWN DISPLACEMENT ON REAL PHOTOGRAPHS

192 trials per cell. **Synthetic motion over real natural images**, so the
displacement is exact.

| d (pixels) | A1 [95% Wilson] | A3 floor [95% Wilson] | A1c |
|---|---|---|---|
| 0 | 0.8906 [0.8386, 0.9273] | 0.2031 [0.1523, 0.2656] | 0.8906 |
| **1** | **0.4635 [0.3944, 0.5341]** | 0.1823 [0.1341, 0.2430] | 0.8906 |
| **2** | **0.2292 [0.1754, 0.2936]** | 0.1719 [0.1251, 0.2315] | 0.8906 |
| 3 | 0.1510 [0.1073, 0.2085] | 0.1302 [0.0898, 0.1851] | 0.8906 |
| 4 | 0.1094 [0.0727, 0.1614] | 0.1354 [0.0941, 0.1910] | 0.8906 |
| 6 | 0.0469 [0.0249, 0.0867] | 0.1198 [0.0812, 0.1733] | 0.8906 |
| 8 | 0.0417 [0.0213, 0.0801] | 0.0938 [0.0601, 0.1433] | 0.8906 |

**THE MEASURED BOUND: identity survives ONE pixel of translation and no more.**
At d=1 A1 is CI-separated from the floor. **At d=2 the CIs overlap** — two pixels
of camera motion and a 6×6 aperture's identity is statistically indistinguishable
from having its arrangement destroyed. By d=4 A1 has fallen *below* the floor,
and by d=6–8 it is at or under chance while the floor stays above it: a
translated region is *worse* than a histogram-matched one, because translation
destroys exact-cell overlap while preserving nothing the metric can use.

**A1c IS DEGENERATE BY CONSTRUCTION, AND THAT IS MY ERROR.** It reads 0.8906 at
every d because "the window at the known shifted position" of an
integer-translated crop is *literally the base window* — A1c is identical to the
d=0 condition and to G1, not an independent ceiling. I pre-registered it, so it
is reported as run rather than quietly dropped (§5), but it establishes only
that the ceiling is 0.8906 and carries no information about motion compensation.
A non-degenerate version needs sub-pixel motion with resampling, which this rung
does not have.

---

## 3. INSTRUMENT GATES (§1) — including one that FAILED

| gate | C1 | C2 | pre-registered requirement | |
|---|---|---|---|---|
| **G1 CEILING** | **0.9900** | **0.9519** | ≥ 0.99 | **C1 PASSES (exactly at threshold); C2 FAILS** |
| **G2 NOISE FLOOR** | 0.0525 [0.0426, 0.0645] | 0.0644 [0.0534, 0.0775] | in [0.02, 0.15] | PASSES both |
| **G3 ALIVE** | entropy 0.948–1.010 | entropy 0.855–1.000 | ≥ 0.50 | PASSES every arm |
| **G4 TIE** | see per-arm `tie>1` | see per-arm `tie>1` | reported | reported |
| **G5 ORDER** | 1.0000 | 0.8479 [0.7898, 0.9061] | agree with A1 within CI | PASSES both |

**G1 FAILED ON C2 AND I AM NOT MOVING THE THRESHOLD (§5).** Diagnosis, from a
quantity recorded for exactly this purpose: on C2's ceiling trials the true
region achieved the maximum score on **1.0000** of trials, with `mean_ntied`
**1.150** and 7.2% of trials tied. **Every single loss is an arbitrary tie-break
between regions that are IDENTICAL after quantization** — a 6×6 tile of sky or
grass at k=4 is frequently not unique within its own frame. This is an
identifiability ceiling of the corpus, not a fault in the instrument, and it is
the *natural-image* analogue of nothing at all on cartoon (C1 `mean_ntied`
1.000).

**The pre-registered consequence, applied to myself:** my own §6 says a failed
gate stops the arm being read. **Strictly, C2's absolute accuracies should not be
read as absolute accuracies** — they are bounded above by 0.9519, and A1|Δ=1 =
0.9181 sits within 0.034 of that ceiling, i.e. at Δ=1 the substrate is already
near the maximum the task permits. **The H1 verdict does not depend on the
absolute level**: the A1−A3 separation is 0.752, twenty-two times the ceiling
deficit. So the verdict stands and the *levels* carry the caveat.

**G5's C1 value is 1.0000 while A1|k4|Δ=1 is 0.9581.** G5 ran 30 base frames
(0–29) and A1 ran 100, and the 1.0000 is consistent: G5's window excludes none of
the anomaly of §4.2 by design but its own replay was clean. The two agree within
A1's CI, as required.

---

## 4. TWO DEFECTS IN MY OWN INSTRUMENT

### 4.1 THE CODEBOOK WAS 33-WAY, NOT 16-WAY — found by an entropy above 1.0

The answer entropy printed **1.010**, which is impossible for 16 categories.
Cause: `boot_core` + `shape_decode_loop` install **17 `ShapeSignature` nodes of
their own** (`fractal`, `symmetry`, `topology`, `spatial_attention`, …), and the
seed's `Argmax` ranges over `NodesOfType(ShapeSignature)` — so every probe was
choosing among **33** candidates, not 16.

**Measured consequence: essentially none, and in the conservative direction.**

- **0 of 17** pre-existing signatures can cover a `["cell", …]` relation at all
  (`ShapeDecode`'s `covers_relation` requires an identical predicate at slot 0,
  and their predicates are `build`/`refers`/`bound`/`map`/… ). They are
  structurally inert distractors.
- `xf_max == nn_score` (the Hamming max over MY 16 tiles) on **74 560 of 74 560**
  trials — **the foreign entries never once changed a score.**
- The empirical noise floor lands at **0.0525 / 0.0644**, i.e. ≈1/16, **not**
  1/33 = 0.0303 — independent confirmation that the answerer effectively ranges
  over 16.
- Chance was therefore pre-registered at 0.0625 when the uniform-over-codebook
  value is 0.0303. **The pre-registered bar is the HIGHER one**, so every verdict
  cleared a stricter test than the design required. Nothing is rescued by this.

**The lesson is `NodesOfType` itself:** a Term that ranges over a node TYPE
ranges over everything of that type the agent already holds, including whatever
its boot seeds installed. A codebook built by adding nodes is not the same object
as the codebook the rule sees. **`codebook_scope` was used to make the score
per-candidate and should have been used again to bound the candidate SET.**

### 4.2 ONE BASE FRAME'S 272 ANSWERS ARE NOT REPRODUCIBLE — an engine-level
`Argmax`/`Eq` disagreement

In the confirmatory run, **every one of base frame 18's 272 probes on C1 at k=4
returned `fractal`** — 272 of C1's 37 280 rows (0.73%), and the *only* foreign
wins anywhere in either corpus (C2: 0 of 37 280).

**These rows are internally contradictory.** Each records `xf_max = 36`,
`xf_ntied = 1`, and `true_score = 36`:

- `xf_ntied = 1` says **exactly one** candidate achieves the maximum;
- `true_score == xf_max == 36` says **the true region is that candidate**;
- yet `identified_as` is `fractal`, which §4.1 proves **cannot cover a single
  `cell` relation** and whose `covered_count` must therefore be **0**.

`xf_ntied` and `identified_as` are two effects of the **same application of the
same rule**, computed from **structurally identical `ShapeDecode` Terms**. So
`Argmax` and an `Eq`-filter disagreed about the same Term's value within one rule
application.

**And it does not reproduce.** Replayed under identical seeds
(`crossframe_identity_diagnose.py`), base 18 gives **0 foreign wins**: in
isolation, under the full 272-observation load in a fresh process, and under the
identical process history of bases 0–19 run in sequence. **0 foreign wins in
5 440 replayed probes.**

**What this means and what it does not.** It cost 16 of 1600 trials (1.0%) in
C1's headline cell, so the reported C1 A1 value of 0.9581 is a **lower bound**
and H1's margin is untouched. But **this arc's measurements are not as
deterministic as every rung including this one has assumed**, and the failure is
silent: it produced a confident wrong answer with self-consistent-looking
metadata. **It is named as a defect and NOT fixed here** — this rung
pre-registered no Rust, and diagnosing an `Argmax`/`Eq` inconsistency inside
`ShapeDecode` is its own pre-registration (§5). §12.3's rule extends: *a value
read once from a non-deterministic evaluator is a coin flip*, and the discipline
that catches it is replay, not inspection.

---

## 5. WHAT THE GRAPH IS ACTUALLY DOING — the pre-registered caveat, confirmed

**Prediction 5 was stated in advance precisely so this could not be presented
later as a nuance. It is confirmed, at the strongest possible reading:**

> `xf_max == nn_score` on **74 560 of 74 560 trials** — every arm, every Δ, every
> k, both corpora, and C3. **The graph's `covered_count` IS the count of cells
> identical in local position and quantized value.**

Argmax-level agreement with adapter-side Hamming NN is 0.76–1.00 raw, and
**0.988–1.000 once trials with ties on either side are excluded** — the residual
disagreement is entirely tie-break order, not scoring.

**So the honest description of this result is:** at 24×24 with 6×6 apertures, a
`ShapeDecode` + `Argmax` composition over cell-relation tuples is a
**nearest-neighbour classifier under Hamming distance, expressed as graph data**.
It is genuinely graph-resident — the decision is a Term, not Python — and that is
the architectural point the seam needed. **It is not a representation, and it
adds no invariance.** §2.4's one-pixel bound is what that costs, measured.

This is the FM-0 distinction (§13.2) applied to a positive result: the mechanism
**works**, and what it is **load-bearing for** is much narrower than "identity".

---

## 6. MY PREDICTIONS, SCORED (§3.7)

| # | prediction | outcome |
|---|---|---|
| 1 | A1 Δ=1 > 0.80 on C1, > 0.70 on C2; H1 CROSSES both | **CORRECT** (0.958 / 0.918) |
| 2 | A3 in 0.25–0.55 on C1 | **WRONG** — 0.2025, below my range. The qualitative claim (well above chance, a real floor) held; my magnitude was too high |
| 3 | A2 in 0.40–0.70 on C1, possibly failing to separate | **WRONG, and badly** — 0.1244. My reasoning was that a cartoon shot is largely static so a distant frame would still match; in fact frames ≥30 apart are usually a *different shot*, so A2 is a much weaker floor than I expected, not a stronger one |
| 4 | A1 decays with Δ, more slowly on C1 | **CORRECT** on both counts |
| 5 | A1 ≡ Hamming NN at ≥0.99 | **CORRECT**, and stronger than stated: score agreement is 1.0000, not 0.99 |
| 6 | C2 scores below C1 at matched Δ | **CORRECT** at every Δ |

**Two of six wrong, both about the FLOORS, both in the direction of my having
mis-modelled the corpus rather than the mechanism.** The one I most wanted to be
right about — prediction 5 — was right, and it is the prediction that most
constrains what this result may be claimed to mean.

**A proviso that broke, informatively:** I warned that a largely-static C1 shot
would compress the Δ axis and make H2 uninformative. The opposite happened —
C1's motion distribution is heavy-tailed (mean 2.202, max 52.343), the Δ axis
spans 0.958→0.389, and it is **C2**, not C1, whose horizon is short.

---

## 7. BOUNDS ON EVERYTHING ABOVE (§8)

- **Toy resolution only.** 24×24 frames, 6×6 apertures, ~4.5 s per base frame.
  The video probe's S5 wall (O(N^1.887); real time affords 18×18) is untouched
  and every number here sits inside it. **Nothing here is a claim about video at
  any real resolution.**
- **This is identity-under-appearance-change at a FIXED aperture** — not object
  tracking, not segmentation, not correspondence of a moving object to a moved
  position. §2.4 is the only place a known correspondence exists, and its motion
  is synthetic.
- **Nothing was learned.** The codebook is one frame's regions, held for one
  comparison and discarded. No training, no accumulation, no codebook growth.
  This measures a comparison, not "learning by watching video."
- **Two hand-set numbers parameterise the whole measurement** (k=4 quantization
  levels, 6×6 tiling). Neither falls out of anything (§13). k was
  sensitivity-checked at {2, 8} and the verdict is stable; the tiling was not
  varied at all.
- **G1 failed on C2** (0.9519 < 0.99) and C2's absolute levels inherit that
  ceiling (§3).
- **Two episodes and 12 photographs.** C1 and C2 are one episode each. The
  cartoon/live-action contrast is a two-point comparison, not a survey.
- **A1c is degenerate** and establishes nothing about motion compensation (§2.4).
- **The measurement is not fully deterministic** (§4.2): 272 of 74 560 trials
  came from an evaluator inconsistency that does not reproduce.
- **No p-values are quoted for the Δ curves.** Consecutive frames of one shot are
  heavily autocorrelated; the frame-level CI is the evidence carried, and even it
  treats base frames as independent when neighbouring ones overlap.
- **Border-ownership / proto-objects were deliberately bypassed** and nothing
  here tests or rehabilitates them.
- **§9:** no default moved, no committed seed edited, no rule changed, no Rust
  touched.

---

## 8. VERIFICATION

| check | result |
|---|---|
| `bash scripts/rung7_vision_bench.sh` **before** any file added | **200 passed, 0 failed, exit 0** (148.9 s) |
| `bash scripts/rung7_vision_bench.sh` **after** | **200 passed, 0 failed, exit 0** — see §8.1 |
| sd orbit law `{2:1, 3:2, 4:2, 6:2, 12:4}` (`tests/test_sdloop_vision_migrated.py`) | **8 passed**, before and after — unmoved |
| this rung's gate `tests/test_crossframe_identity_migrated.py` | **16 passed** (12 + 4 provenance once pinned) |

**The gate was positive-controlled red-then-green.** Inverting the decision
(`Argmax` → `Argmin`) turns **4 tests red** including the ceiling; shipping the
seed armed (`crossframe: 0.0` → `1.0`) turns the §9 test red. Restoring gives
12/12 green with the seed **byte-identical** (`sha256 1adde048…` before and
after). Note that the armed-by-default control reddens only ONE test, because
`CrossFrameWorld(arm=False)` explicitly writes the flag — the ships-off test is
the one carrying that property, and it is the one that fires.

**Provenance self-audit** pins `git diff BASE_SHA RUNG_SHA` — never `HEAD`,
never the working tree — with a `:/` root-magic pathspec, since git reports
`--name-only` from the git root while resolving a pathspec relative to CWD and
this suite runs from the experiment directory.
