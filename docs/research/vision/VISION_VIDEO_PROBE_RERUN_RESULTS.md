# VIDEO PROBE, RE-RUN — RESULTS: the wall FELL in the drive and MOVED to the identity layer

*Pre-registration: `VISION_VIDEO_PROBE_RERUN_PREREG.md`, committed BEFORE any
measurement at `fcc194c5d0e330dde339f29b898b0f0c75e019a8` (base
`c6c022f8fc2ab212b130ad3e34a761af6a20aaee`). Both endpoints pinned; no range
ends at `HEAD`.*

**Engine (§10):** `4d451d8f6ed0` / md5 `ab01c23ed643a9a406120c08be5fa4b3`
`@ .../agent-a0c149cb0a125ada7/.../runners/dsl/python/substrate_rs/_native.abi3.so`
— **built in THIS worktree** by `scripts/engine_build.sh`. This rung adds no
Rust; the build is nonetheless this tree's own. **Its md5 is byte-identical to
`VISION_BATCH_APPLY_RESULTS.md`'s `after` engine**, recorded in the
pre-registration *before* measuring — a reproducible build, and the fact that
**the Rust source has not moved since batch-apply**.
**Machine:** AMD Ryzen 5 9600X, 12 logical cores. **I ran SOLO.** Load state is
reported as a FIELD on every timing below, never as a caveat.
**Selectors (§12):** `scripts/video_probe_measure.py` (**UNCHANGED**, confirmatory)
· `scripts/video_probe_diagnose.py` (**UNCHANGED**, diagnostics) ·
`scripts/video_probe_rerun_layers.py` (A8/A9, new) ·
`scripts/video_probe_rerun_sd_explore.py` (**EXPLORATORY**, new).
**Raw:** `results/video_probe_rerun.json` · `results/video_probe_diagnose_rerun.json`
· `results/video_probe_rerun_layers.json` · `results/video_probe_rerun_sd_explore.json`
· `results/video_probe_rerun_s2_attrib.json`.
**Seeds:** block 65000–65999 claimed; **none consumed** (fully deterministic
under fixed positional indices).

---

## 0. THE HEADLINE, IN ONE PARAGRAPH

**The wall did not fall and it did not move — it did both, and the two halves
belong to different layers.** In the drive, it **FELL, completely**: the
real-frame exponent goes **1.887 → 1.0137** (r² 0.99998), per-cell cost is now
flat at **12.6 µs**, a real-time budget affords **3,305 cells (57×57) instead of
336 (18×18)**, and one 1080p frame goes **164 hours → 26.2 seconds** — a
**22,562×** reduction. **And the entire exponent delta is attributable to
batch-apply alone**: on ONE engine, in ONE session, stripping five booleans from
the seed data restores **1.874** (against the original's 1.887). But the ceiling
did not rise with it. **The sd/identity layer is now the binding term**, and not
because its exponent is worse — it is **linear in signature size (1.010)** and
**linear in codebook size (0.939)** — but because its **per-cell coefficient is
55× the drive's (698 µs vs 12.6 µs)** and it carries a **second multiplicative
axis the drive does not have at all**. Real time affords the drive a **57×57**
field and the identity layer **60 cells (~10×10) against a codebook of ONE**,
divided by K thereafter. Meanwhile **S1, S3 and S4 did not move by one digit**:
the retina still fires 46.64% on cartoon and 80.30% on BSDS, proto-objects still
return **0 on 7/7 frames at k=16**, and the pixel→identity seam is still **6 ∩
60 = 0**. **A 155× op reduction bought exactly one thing — arithmetic headroom —
and bought nothing representational**, which is what the original rung predicted
when it said S3 and S5 were independent.

**Two things I got wrong, both load-bearing and both reported as findings rather
than footnotes.** (1) **My own new arm's instrument was BLIND, all four of my
pre-declared gates PASSED, and it would have produced a confident wrong answer**
(§3.1). (2) **The original rung's self-diagnosis of its own contamination was
mistaken in its direction** — S2's FLAT verdict was won by batch-apply, **not**
by the clean machine, and I measured that rather than argued it (§4.2).

---

## 0.1 THE MACHINE STATE, AS A FIELD — the corollary the original earned

The original probe's §0.1 minted the rule: *check what else is running before you
record a wall-clock number.* Every timing window below carries its load:

| window | load1 before → after | concurrent load |
|---|---|---|
| A1–A5 confirmatory (incl. **the S2 window**) | **0.84 → 1.01** | none but the desktop; a `git` background fetch at ~25% of one core |
| A6 diagnostics | 1.03 → 1.02 | as above |
| A8/A9 layers | 1.43 → 1.42 | as above |
| sd exploratory (E1/E2) | 0.97 → 1.19 | as above |
| S2 attribution | 2.33 → 2.25 | as above |
| regression bench | run as its OWN step, after all timing | — |

**No other rung was running** (the supervisor ran this rung solo, deliberately,
because the original's S2 was contaminated). A `vllm-xpu` podman container is a
**standing system service on this box**, named in the pre-registration *in
advance* so its appearance in `ps` would be a known constant rather than a
discovery.

**And the load turned out not to be the variable that mattered** — see §4.2,
where the pre-batch drive misses the CV bar on a *clean* machine.

---

## 1. CORPUS — IDENTICAL, verified, not assumed

| source | what | counts |
|---|---|---|
| **Jellyfin** | *Middlemost Post* S2E1 "Parker Gets Rich", episode id **`08630d4b7b215c469df19b9c42d7b617`** | **150 frames**, every 2nd decoded frame from t=300 s, area-averaged to 24×24 grey; decode **1.72 s** |
| **BSDS300** | via the §10.2 `data/` symlink | 12 centre-crops |

The pre-registration declared that **if the returned episode id were not
`08630d4b7b215c469df19b9c42d7b617`, every delta would be UNINTERPRETABLE as a
delta**. It is that id. The corpus has not moved, so the comparison below is a
comparison of the substrate and not of two different videos.

**Scope (§8), unchanged and still binding:** ONE episode of ONE broadcast cartoon
series plus 12 BSDS crops. Not a survey of video.

---

## 2. THE FIVE DELTAS

### S1 — RETINA: **IDENTICAL TO TWELVE SIGNIFICANT FIGURES**

Controls pass (§1 cl.4), and pass at exactly their original values: uniform field
**0.00%**, hard edge **25.0%** at mean distance **1.5** from the boundary.

| | original | re-run | delta |
|---|---|---|---|
| fire, cartoon (mean over 40 frames) | 46.64% | **46.640625%** | **0.000000** |
| sd / min / max | 6.85 / 35.76 / 64.93 | **6.85374 / 35.76389 / 64.93056** | **0** |
| fire, BSDS300 (D1) | 80.30% | **80.29513888888889%** | **0** |
| verdict | INDETERMINATE (25–50%) | **INDETERMINATE (25–50%)** | unmoved |

**P1 CORRECT.** This is the delta that had to be zero, and its being zero is
evidence about the whole rung: **batch-apply's byte-identity claim (235,200
values, zero differing) holds on the real-video path too**, on a corpus that rung
never ran. The retina is still not sparse — 46.6% of cells firing is a dense
code — and the cartoon/photo gap is still a property of the corpus, not the
instrument.

### S2 — COMPUTE vs SURPRISE: **FLAT.** The verdict the original never got.

| statistic | original | re-run | delta |
|---|---|---|---|
| n (paired frames) | 149 | **149** | 0 |
| Spearman ρ(surprise, cost) | 0.2998 | **0.29775** | −0.002 |
| **cost ms CV** | **0.2197** | **0.04243** | **÷5.2** |
| cost ms mean | 102.84 | **7.188** | **÷14.3** |
| cost ms min / max | 70.50 / 180.54 | **6.900 / 9.042** | — |
| surprise ratio max/min | 48,236× | **48,236×** | 0 (same frames) |
| **verdict** | INDETERMINATE | **FLAT — compute-∝-surprise REFUTED as built** | **CHANGED** |

The rule was fixed in the original and is **unchanged here**: FLAT iff **ρ<0.3
AND CV<0.10**. The original cleared the ρ half by 0.0002 and missed the CV half
by 2.2×. **The re-run clears both**: CV falls to 0.0424, and ρ stays put.

**AND I AM FLAGGING THE FRAGILITY RATHER THAN BANKING THE VERDICT.** ρ=0.29775
clears its bar by **0.00225 — 0.75%**. This is the *same knife-edge* the original
sat on, in the same direction. Had ρ landed at 0.301 the verdict would read
INDETERMINATE with a CV of 0.042. **The FLAT verdict is carried by CV, and its ρ
half is a coin-flip's width from failing.** The original declined to round ρ
*down* to claim a refutation; I decline to present ρ as though it robustly
cleared anything.

**And the diagnostics push the same way, which is the unusual part** — normally
they cut against the verdict. D4, four independent passes on the same frames,
**with the drift control the original's §5 required be included from the start**:

| pass | ρ(surprise, cost) | ρ(frame index, cost) — the DRIFT control |
|---|---|---|
| D4 rep 0 | 0.3002 | +0.0767 |
| D4 rep 1 | 0.2732 | +0.1202 |
| **D4 rep 2** | **0.0300** | **−0.0483** ← least contaminated |
| D4 rep 3 | 0.3625 | **+0.3140** ← most contaminated |
| **mean ± sd** | **0.2415 ± 0.1263** | |
| D2 pooled | 0.1132 | — |
| D2 non-ignite stratum | 0.1464 | — |

**ρ tracks the drift control almost monotonically**, exactly as the original
diagnosed — and the least-drifting pass gives **ρ=0.030**. The original's
equivalent estimate was ρ≈0.18–0.26; it is now **≈0.03–0.15**. The ignite
confound is smaller than ever (**+2.2%** of pooled mean, vs +3.9%) and its
stratum's ρ has gone **negative** (−0.190).

**Honest reading:** compute is now flat in surprise by the pre-registered rule,
and the residual ρ is substantially a timing-drift artifact. **The
compute-∝-surprise claim is refuted as currently built** — and §4.2 shows it was
only ever *weakly true for a reason nobody would want*.

**P2 WRONG, and wrong in an instructive way.** I predicted ρ would fall (because
batch-apply removed the content-dependent re-derivation loop) and CV would stay
above 0.10, giving INDETERMINATE again. **The opposite happened on both halves**:
ρ held almost exactly, CV collapsed. My model of *which* statistic the
re-derivation loop was feeding was backwards — see §4.2, where I measure it
instead of guessing.

### S3 — PROTO-OBJECTS: **UNMOVED. Still zero on 7/7 at k=16.**

Positive control reproduces the committed synthetic answer exactly: **1 proto, 24
members, 7 sweeps** — the values `border_ownership_measure.py::arm_figure_ground`
asserts. The instrument is alive, so the real-frame nulls are real nulls.

| criterion | threshold | original | re-run |
|---|---|---|---|
| object-scaled `n_proto/n_cells` | < 0.05 | 0.0156 | **0.0156** |
| k-stable, max/min over k | < 3.0 | 4.0 | **4.0** |
| verdict | | FAILS — k-unstable | **FAILS — k-unstable** |

The D3 spread-frame table is **byte-identical to the original's**, including the
reference component counts:

| frame | k=2 | k=4 | k=8 | k=16 |
|---|---|---|---|---|
| 0 | 3 | 4 | 1 | **0** |
| 25 | 4 | 3 | 1 | **0** |
| 50 | 3 | 3 | 1 | **0** |
| 75 | 2 | **0** | **0** | **0** |
| 100 | 4 | 2 | **0** | **0** |
| 125 | 2 | **0** | **0** | **0** |
| 149 | 2 | 1 | **0** | **0** |

| k | reference components | mean protos |
|---|---|---|
| 2 | **10.3** | 2.86 |
| 4 | **38.4** | 1.86 |
| 8 | **79.3** | 0.43 |
| 16 | **127.6** | **0.00** |

**P3 CORRECT.** Border-ownership loads `vision_border_ownership`, not
`vision_change`; no batched rule is in its path, and **the 155× op reduction did
not touch this stage at all.** The percept is still entirely a function of the
adapter-chosen k, and still converges on **nothing** as quantization refines.
**This is the "axes are GIVEN, not learned" bound, unchanged by a scale fix — as
the original said it would be, because S3 is architectural and S5 is
arithmetic.**

### S4 — IDENTITY SEAM: **STILL A STRUCTURAL ABSENCE**

| | original | re-run |
|---|---|---|
| files touching `ProtoObject` | 6 | **6** |
| files constructing `["cell", …]` tuples | 33 | **39** |
| files constructing `ShapeSignature` nodes | 56 | **59** |
| **files doing BOTH** | **0** | **0** |

The 6 proto files are *the same 6 files*. The identity side grew by 9 files and
**not one of them touches a proto-object**. **P4 CORRECT.**

The tree got bigger; the seam did not get built. This remains an FM-0-class
result: **the identity half of the arc is still, with respect to real imagery,
decorative** — correct, gated, tested, and wired to nothing a camera can reach.

### S5 — SCALE: **THE WALL FELL. Exponent 1.887 → 1.0137.**

| grid | cells | original ms/tick | **re-run ms/tick** | original µs/cell | **re-run µs/cell** |
|---|---|---|---|---|---|
| 12 | 144 | 7.76 | **1.763** | 53.9 | **12.24** |
| 16 | 256 | 28.28 | **3.169** | 110.5 | **12.38** |
| 24 | 576 | 114.53 | **7.146** | 198.8 | **12.41** |
| 32 | 1024 | 331.61 | **12.923** | 323.8 | **12.62** |

log–log fit: **exponent 1.0137, r² 0.99998** (n=4), against the original's
**1.887, r² 0.9971**. **P5 CORRECT** (predicted 0.9–1.3, and grid-32 < 60 ms).

**The most legible form of the result is the last column: µs/cell is now
CONSTANT** (12.24 → 12.62 over a 7.1× range in cells) where it used to *scale
with the field* (53.9 → 323.8). That is what linear means, read directly off the
instrument rather than off a fit.

#### 2.1 What the new exponent buys, extrapolated

| field | cells | original | **re-run** |
|---|---|---|---|
| 24×24 | 576 | 115 ms | **7.1 ms** |
| 64×64 | 4 096 | 4.7 s | **51.7 ms** |
| 320×240 (QVGA) | 76 800 | 19.6 min | **0.97 s** |
| **1920×1080** | **2 073 600** | **164 hours** | **26.2 s** |

**At a 23.976 fps real-time budget (41.7 ms/frame) the affordable field is now
3,305 cells — a 57×57 image**, against the original's **336 cells / 18×18**.
**9.8× more cells; 22,562× less time for a native frame.**

**These are extrapolations, labelled as such** — the *measured* range is
144–1024 cells, and 1080p is three orders beyond it. What is measured is that the
exponent is 1.01 with r²=0.99998 and that µs/cell is flat across the measured
range.

---

## 3. THE NEW ARM — AND ITS INSTRUMENT FAILED

### 3.1 ⚠️ A8's PRE-REGISTERED STATISTIC IS BLIND, AND ALL FOUR OF MY GATES PASSED

**This is the most important methodological finding of the rung, and it is
against me.**

A8 pre-registered a **counted-operation** exponent for the sd/identity layer,
using the merged `scale_audit.rs` instrumentation, behind four gates declared in
advance because *this arc has caught eleven inert instruments*. The result:

| n_cells | 12 | 20 | 37 | 58 | 93 | 123 | 142 |
|---|---|---|---|---|---|---|---|
| **counted ops** | **253** | **253** | **253** | **253** | **253** | **253** | **253** |
| wall ms | 7 | 13 | 24 | 37 | 60 | 79 | 93 |

**Every counter is byte-identical across an 11.8× range of N** — `cand_enum` 21,
`rule_enumerations` 68, `ffi_calls` 1, `leaf_visits` 4, at every single point —
while wall-clock grows **13×**.

| gate | result |
|---|---|
| **G1 zero-when-off** — every counter 0 with the audit off, on a LIVE workload | **PASS** |
| **G2 liveness** — ops>0 and `recognized`/`recognized_transformed` at every point | **PASS** (all 7 `recognized_transformed`) |
| **G3 determinism** — two runs byte-identical | **PASS** (zero differing counters) |
| **G4 N varies** — span ≥4× | **PASS** (11.8×) |
| **all_pass** | **TRUE — and the answer is still unusable** |

**Taken literally, the pre-registered rule fires**: `e_sd` = 1.67×10⁻¹⁶ ≈ 0.0,
which is ≤ `e_drive` + 0.1, which reads **"the sd/identity layer is NOT the
binding term; the wall FELL."** That is a **fluent, gated, entirely wrong
answer** — the exact disease §1 exists to prevent, arriving through a gate I
wrote myself specifically to prevent it.

**THE DIAGNOSIS, and it is architectural, not a bug.** **A signature is an
ATTRIBUTE, not a subgraph.** All N cells live inside ONE node's attribute list,
so the graph the rule engine matches over is *constant in N* — one `Observation`,
one `ShapeSignature`, a handful of sd rules. The entire cost sits inside
`ShapeDecode` / `TransformDecode` **Term evaluation**, which `scale_audit` does
not count and was never built to count.

**The consequence is much larger than this arm.** The whole scale toolkit the
last three rungs built — counted-op attribution, the F/C/R split, the locality
index, batch-apply — operates on **graph-level rule matching**. The sd/identity
layer is **structurally invisible to all of it**, and **structurally immune to
all of it**: you cannot batch-apply a Term evaluation, and you cannot index a
list that lives in an attribute. **The three rungs that each closed with "ONE
workload; the sd/identity layer is NOT measured" were not merely incomplete —
their instrument could not have measured it.**

**THE STANDING LESSON THIS EARNS.** The arc's eleven inert instruments were all
*dead*: a counter reading zero, a hook on the wrong store, a path that never ran.
**This one is ALIVE, DETERMINISTIC, CONSERVED, AND INSENSITIVE**, which no
existing gate catches. So:

> **A LIVENESS GATE MUST CHECK THAT THE COUNTER MOVES WITH THE THING BEING
> VARIED, NOT MERELY THAT IT IS NON-ZERO.** "Ops > 0" and "the result is
> correct" are jointly satisfied by an instrument measuring something else
> entirely. The missing gate is **G5 RESPONSIVENESS**: across the declared
> sweep, the statistic must vary by more than its own determinism noise — and
> since G3 pins that noise at exactly zero, the test is simply *did it move at
> all*.

**Handled per §5: the statistic is NOT redefined to rescue the arm.** A8 is
reported **UNINTERPRETABLE on its pre-registered statistic**, and the layer is
measured separately and **exploratorily** below — the same separation the
original rung used for its §2.4b seam probe.

### 3.2 EXPLORATORY — the sd/identity layer, measured the only way left

***NOT a pre-registered result. Nothing in §5's failure map depends on the
exponents here; the "binding term" conclusion is argued from the per-cell
coefficient and the second axis, both of which are read directly off the table.***
Wall-clock, 5 repeats per point, median reported with spread, load state
recorded, **explicitly not load-independent and therefore explicitly not a
share**.

**E1 — the N axis** (A8's declared workload, timed instead of counted; codebook
K=1, literal self-identity — the easiest recognition that exists):

| side | n_cells | ms (median) | spread |
|---|---|---|---|
| 4 | 12 | 7.7 | 0.6% |
| 6 | 20 | 13.5 | 4.9% |
| 8 | 37 | 24.2 | 2.6% |
| 10 | 58 | 37.2 | 0.6% |
| 12 | 93 | 60.5 | 3.1% |
| 14 | 123 | 79.6 | 1.3% |
| 16 | 142 | 99.1 | 6.8% |

**exponent 1.0104, r² 0.9990.** **LINEAR in signature size.**

**E2 — the CODEBOOK axis, which no rung has ever measured.** A8's workload holds
exactly ONE signature; real recognition decodes against many. Target and its held
twin fixed, only the number of *other* held signatures varies; decoys are **real
frames from later in the same episode**, not synthetic:

| K (codebook) | ms (median) | spread |
|---|---|---|
| 1 | 64.5 | 16.5% |
| 2 | 129.1 | 5.0% |
| 4 | 247.2 | 7.9% |
| 8 | 484.8 | 5.1% |
| 16 | 903.6 | 2.3% |
| 32 | 1672.2 | 2.3% |

**exponent 0.9394, r² 0.9996.** **LINEAR in codebook size.**

**P6 WRONG.** I predicted `e_sd ≥ 1.5` — a quadratic-flavoured decode. It is
linear on both axes. **My reasoning ("an N-cell observation against an N-cell
held entry, with a fixpoint on top") was wrong about the shape of the work.**

**But the conclusion P6 attached to that exponent survives on different
evidence**, and this is the locality-index rung's standing lesson arriving
exactly where I pre-registered that it would (*"neither a share nor an exponent
decides alone; the PAIR does"*):

| | drive (post-batch) | **sd/identity (K=1)** | ratio |
|---|---|---|---|
| exponent | 1.0137 | **1.0104** | ≈1 |
| **per-cell cost** | **12.6 µs** | **698 µs** | **55×** |
| second multiplicative axis | **none** | **codebook size K, linear** | — |
| real-time affordable cells | **3,305 (57×57)** | **60 (~10×10 at 55% fill)** | **55×** |

**The identity layer is 55× more expensive per cell than the entire retina drive
— at a codebook of ONE — and it divides by K thereafter:**

| codebook K | ms for one 16×16 frame (142 cells) | fps |
|---|---|---|
| 1 | 99 | 10.1 |
| 10 | 991 | 1.0 |
| 100 | 9,913 | 0.10 |
| 1000 | 99,133 | 0.01 |

**A "codebook of one" is not recognition.** Any system that recognises things
holds many shapes, and the cost is the product **N × K**. **That product is the
new wall**, and it is made of two linear terms, which is why no exponent test
finds it.

---

## 4. ATTRIBUTION

### 4.1 BATCH-APPLY'S CONTRIBUTION, ISOLATED — and it is essentially total

**Seven engine-touching commits landed since the original probe, and the brief
correctly forbade attributing the whole delta to batch-apply.** The isolation was
cheap, so it was done rather than hedged. **Same engine, same session, same
machine, same corpus; the only difference is five booleans in seed DATA** (the
batch rung's own `off_new` control mechanism, reused verbatim — the flag is graph
data, so the control varies the data, not the code path):

| arm | counted-op exponent | **wall exponent** | ops @1024 cells | ms/tick @1024 |
|---|---|---|---|---|
| **batch LIVE** (as committed) | **0.9997** (r² 0.99998) | **0.9776** | 5,484,249 | **13.39** |
| **batch STRIPPED** (control) | **1.9592** (r² 0.99995) | **1.8743** | 300,655,100 | **251.18** |
| ratio | | | **54.8×** | **18.8×** |

Verified by reading, not assumed: `_drive_phase` dispatches to
**`apply_rule_batch`**, the native method **exists**, and all five
`vision_change` rules carry `batch: true`.

**The batch-STRIPPED wall exponent is 1.8743, against the original probe's
1.887.** It reproduces the original **within fit error**, on the same corpus and
the same frame schedule. **P7 CORRECT.**

**What this establishes and what it does not:**

- **ISOLATED:** batch-apply accounts for the **entire exponent delta**
  (1.874 → 0.978). Nothing else needed to be invoked, and nothing else could
  have produced it, because everything else was held fixed by construction.
- **AGGREGATE, and named as such:** the *absolute* residual. The stripped arm
  reads **251.18 ms/tick** at 1024 cells where the original read **331.61**.
  That **24% gap is aggregate** — the other six commits, plus PyAV/numpy/machine
  drift, plus (most plausibly) the fact that **the original's absolute
  milliseconds were taken under load 4.40 on 12 cores** and mine were not. **I do
  not decompose it further, and I do not attribute it.**
- **BOUNDED BY THE ENGINE HASH:** this build's md5 is byte-identical to the
  batch-apply rung's `after` engine, so **the Rust has not moved since
  batch-apply**. The residual confound is seed/adapter/machine — it is *not*
  engine.

### 4.2 AND THE ORIGINAL RUNG'S SELF-DIAGNOSIS WAS WRONG — measured, not argued

The original's §0.1 reasoned carefully about its own contamination and concluded:
*"it is likely that FLAT was withheld because of machine load, not because of the
substrate."* The reasoning was sound — scheduler noise is uncorrelated with
content, so it inflates CV and dilutes ρ.

**It was also wrong, and this rung can say so because it can run the
counterfactual.** Same clean machine, same session, same engine, same 149 frames;
only the batch flag varies:

| arm | ρ(surprise, cost) | **CV** | mean ms | verdict by the unchanged rule |
|---|---|---|---|---|
| **batch LIVE** | 0.0944 | **0.0170** | 7.21 | **FLAT** |
| **batch STRIPPED** | **0.4907** | **0.1255** | 79.26 | **INDETERMINATE** |

**On a clean machine the pre-batch drive still misses the CV bar (0.1255 vs
0.10) and its ρ nearly reaches the TRACKS threshold (0.4907 vs 0.5).** So:

- **S2's FLAT verdict was won by batch-apply, not by the clean machine.** Load
  was never the dominant term. The original was right that its numbers were
  contaminated and right about the *direction* of the contamination, but wrong
  about its *size* relative to the real cause.
- **The real cause is mechanistic and slightly embarrassing for the
  architecture.** `apply_rule_once` re-derived the binding set once per applied
  binding, so the drive's cost tracked **the number of firing cells** — which is
  exactly **content**. **Compute genuinely did track surprise, weakly, because of
  an inefficiency.** Removing the inefficiency removed the property. **The
  compute-∝-surprise behaviour the architecture wanted was being delivered
  accidentally by a re-scan loop, and the scale fix destroyed it.**

**Any future claim of "compute ∝ surprise" must now beat ρ≈0.09 on the batched
path, report its drift control, and name a mechanism that is not re-scanning.**

*(§4.2 is a post-hoc diagnostic on a pre-registered question. It is labelled as
such, its raw is `results/video_probe_rerun_s2_attrib.json`, and the
pre-registered S2 verdict in §2 stands on the confirmatory run alone.)*

---

## 5. THE NEW FAILURE MAP

| order | stage | original status | **re-run status** |
|---|---|---|---|
| — | S1 retina | runs, dense-ish (46.6/80.3) | **unchanged, to 12 s.f.** |
| — | S2 motion/cost | INDETERMINATE, contaminated | **FLAT — refuted as built** |
| **was 1st (hard)** | S5 scale (drive) | **BLOCKS EVERYTHING**, O(N^1.89), 18×18 | **FELL — O(N^1.01), 57×57, 1080p in 26 s** |
| **NOW 1st (hard)** | **sd/IDENTITY layer** | *never measured — and could not be, by the available instrument* | **BINDING: 698 µs/cell (55× the drive) × codebook K; real time affords ~10×10 at K=1** |
| **2nd (hard)** | S3 proto-objects | 0 protos on 7/7 at k=16 | **unchanged — 0 protos on 7/7 at k=16** |
| **3rd (soft)** | S4 identity seam | 6 ∩ 60 = 0 | **unchanged — 6 ∩ 60 = 0** |

**THE NEW FIRST BLOCKER IS THE sd/IDENTITY LAYER'S COEFFICIENT, MULTIPLIED BY
CODEBOOK SIZE.** Characterised precisely enough to pre-register against:

- it is **linear in signature cells** (1.0104, r² 0.9990) and **linear in
  codebook size** (0.9394, r² 0.9996) — so **it is not an exponent problem and no
  exponent test will find it**;
- its **per-cell constant is 698 µs at K=1, 55× the drive's 12.6 µs**;
- the binding quantity is the **product N×K**, and **K is the axis that has never
  been measured or optimised**;
- it is **structurally invisible to every scale tool this arc has built**,
  because signatures are attributes and the tools count graph-level rule
  matching (§3.1);
- and it sits **downstream of two unmoved blockers** (S3 empty, S4 absent), so
  fixing it alone buys nothing perceptual.

**Did the wall fall or move? BOTH, and the distinction matters.** In the drive it
**fell** — genuinely, by 22,562× on a native frame, with the exponent gone from
quadratic to linear and the entire delta attributable to five seed booleans. In
the pipeline it **moved** — to a layer that was never measured, whose cost is a
coefficient rather than an exponent, and which the entire optimisation toolkit
built over the last three rungs **cannot see and cannot help.**

**And the representational blockers did not move at all.** S1, S3 and S4 are
digit-for-digit what they were. **A 155× op reduction bought arithmetic headroom
and nothing else** — precisely as the original predicted when it said S3 was
architectural, S5 was arithmetic, and fixing either would not help the other.
**That prediction is now confirmed by experiment rather than asserted.**

---

## 6. BOUNDS ON EVERYTHING ABOVE (§8)

- **One episode, one series, one cartoon**, plus 12 BSDS crops. Broadcast cartoon
  is not egocentric video. Every S1/S2/S3/S5 number is conditional on this
  corpus, verified to be the *same* corpus by episode id.
- **S2's FLAT rests on a ρ that clears its bar by 0.75%** (§2). It is carried by
  CV. And ρ itself spans **0.030–0.3625** across four passes on the same frames —
  the effect size is not stable, only its smallness is.
- **S2's frames are NOT independent.** Consecutive frames of one shot are heavily
  autocorrelated; the nominal n=149 overstates the effective n and no p-value is
  quoted.
- **A8 IS UNINTERPRETABLE ON ITS OWN STATISTIC** (§3.1). The sd/identity numbers
  in §3.2 are **EXPLORATORY WALL-CLOCK**, 5 repeats, medians, spreads 0.6–16.5%.
  They are not load-independent and are not a share. **They should be re-taken
  with a counted statistic once one exists that can see Term evaluation.**
- **E2's decoys are 31 real frames from ONE episode**, and a codebook of 32
  near-neighbours from one cartoon is not a codebook of 32 objects. Whether
  decode cost depends on codebook *content* as well as *size* is **not
  measured**.
- **The N×K product is an inference from two separately-measured linear axes, not
  a measured surface.** I did not sweep N and K jointly. A cross-term would not
  show up in either fit.
- **The real-time affordance figures assume the drive's 12.6 µs/cell and the sd
  layer's 698 µs/cell hold outside the measured ranges** (144–1024 cells;
  12–142 signature cells; K 1–32). The 1080p and K=1000 rows are **extrapolations
  three orders beyond measurement**, labelled as such.
- **S5's fit is 4 points over a 7.1× range**, exactly as the original's was.
- **S4 is a structural claim about THIS TREE at this commit**, by enumeration over
  five directories and two construction forms. A bridge written in a form the two
  regexes miss would be missed.
- **A9's isolation is exact for the exponent and aggregate for the absolute
  milliseconds** (§4.1). The 24% residual is named and NOT decomposed.
- **No claim is made about accuracy, recognition rate, or learning.** Nothing was
  trained. The only "recognition" measured is literal self-identity, which is the
  easiest case that exists.
- **§9:** no default moved, no seed edited, no rule added, no Rust touched. A9's
  batch-off arm writes a temp file the process deletes; the repo is untouched.

---

## 7. PREDICTIONS, SCORED

| # | prediction | outcome |
|---|---|---|
| P1 | S1 unchanged to rounding | **RIGHT** — identical to 12 s.f. |
| P2 | ρ falls to 0.05–0.30, CV 0.10–0.30, **INDETERMINATE again** | **WRONG on both halves and on the verdict** — ρ held at 0.298, CV collapsed to 0.042, verdict **FLAT** |
| P3 | S3 unchanged, 0 protos on 7/7 at k=16 | **RIGHT** — byte-identical |
| P4 | S4 still 0 bridges | **RIGHT** — identity side grew 9 files, still 0 |
| P5 | S5 exponent 0.9–1.3, grid-32 < 60 ms | **RIGHT** — 1.0137, 12.9 ms |
| P6 | `e_sd` ≥ 1.5, sd layer is binding, **the wall MOVED** | **HALF WRONG** — exponent is 1.01 not ≥1.5, so the stated reasoning fails; the *conclusion* (binding, wall moved) survives on the coefficient and the K axis instead |
| P7 | batch-stripped 1.75–2.00, live ≈1.0, attribution essentially total | **RIGHT** — 1.874 / 0.978 |

**5 right, 1 half, 1 wrong.** **P2 is the one I flagged in advance as most likely
to be wrong, and it was** — which is worth exactly as much as it sounds, i.e. it
does not make the wrong prediction right. **P6's exponent was wrong and its
conclusion was right, which is the least satisfying way to be correct**, and is
recorded that way rather than as a win.

---

## 8. THE REGRESSION ORACLE

**Result: GREEN.** Run as its OWN step, exit code captured, never piped into
`tail` inside an `&&`, and never overlapping a timing window.

| selector | result | exit |
|---|---|---|
| `bash scripts/rung7_vision_bench.sh` | **200 passed, 0 failed, 0 skipped** in 129.5 s | **0** |
| `tests/test_sdloop_vision_migrated.py` (**sd orbit law** `{2:1, 3:2, 4:2, 6:2, 12:4}`) | **8 passed** | **0** |

**200/0 is the §10.2 figure for `data/` PRESENT** (190/10 without), and the
symlink was verified live before the run — so the 10 BSDS-gated tests actually
ran rather than silently skipping. **The condition is quoted with the number**,
as §10.2 requires.

---

## 9. WHAT THE NEXT RUNG SHOULD PRE-REGISTER AGAINST

Ranked by what the evidence supports:

1. **A COUNTED STATISTIC FOR TERM EVALUATION — the instrument, before the
   science.** §3.1 established that the sd/identity layer is invisible to every
   scale tool this arc has. **Every number in §3.2 is wall-clock because there is
   no alternative.** The unblocking work is a `scale_audit` counter *inside* Term
   evaluation (`ShapeDecode`/`TransformDecode`), which would make the identity
   layer measurable the way the drive already is. **This is a BUILD TASK, not a
   hypothesis** — and it should carry the new **G5 RESPONSIVENESS** gate (§3.1),
   because the gate set that missed this failure is the one currently in the
   tree.
2. **THE CODEBOOK AXIS, PROPERLY.** §3.2's E2 is exploratory, one episode, 32
   near-neighbour decoys, wall-clock. The pre-registrable question is sharp:
   **is decode cost linear in K because the loop is exhaustive, and does a
   codebook of genuinely distinct shapes cost the same as one of near-neighbours?**
   If exhaustive, the fix is the same shape as batch-apply was — an indexing
   problem with a known answer — and **the N×K product is where the remaining
   3–4 orders of magnitude live.**
3. **CROSS-FRAME IDENTITY ON REAL PIXELS, at toy resolution** — the original's
   own recommendation 1, **still standing and now cheaper**. The drive affords
   57×57 in real time instead of 18×18, and the seam is still plumbing. The
   question is unchanged: *does a region recognised in frame t get recognised as
   the SAME thing in frame t+1, under real motion, above a shuffled-frame floor?*
   **It must still NOT route through border-ownership** (S3 is still empty).
4. **S3's enclosure predicate — still demoted, and now demoted twice over.** The
   measured fact is unchanged (0 protos on 7/7 at k=16, count falling
   monotonically as quantization refines) and the identity path still does not
   need it.

**What should NOT be pre-registered:** anything of the form *"the agent learns by
watching video."* The substrate can now *drive* a 57×57 field in real time — a
real and large improvement — but it still produces **zero proto-objects on most
real frames**, still has **no path from any percept to its identity layer**, and
its identity layer still costs **55× per cell what the retina does, times the
size of its codebook**. **That claim is one fallen wall closer and three blockers
away**, and the original rung's job — to say so with numbers rather than find out
later — is this rung's job too.
