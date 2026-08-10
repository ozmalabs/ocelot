# VIDEO PROBE — where does the assembled eye break on REAL VIDEO?

*Pre-registration. Written and committed BEFORE any measurement (PROTOCOL §3).*

**Base SHA:** `328065b62a31cf1daeb601557f21a0d331a2aed2`
**Branch:** `gamma-substrate/vision-video-probe`
**Engine:** `7d5f50c18673 @ /home/matt/ozma/internal/research/experiments/gamma-substrate/.../\_native.abi3.so`
(shared build, Rust source byte-identical — **this rung adds NO Rust**, §10.1 rule 4)
**Seed block claimed:** **54000–54999** (verified free: the ledger's highest consumed
block is 53999; 54000+ appears nowhere in `VISION_PROTOCOL.md` or any `*_PREREG.md`)

---

## 0. WHAT THIS RUNG IS, AND WHAT IT IS NOT

**This is a MEASUREMENT rung. It is an INSTRUMENT.** It adds no seed, edits no
rule, changes no default, touches no Rust, and moves no committed number. Its
entire deliverable is an **honest map of what breaks first** when the assembled
eye is pointed at real video, and in what order.

**It is explicitly NOT a build of a video-learning system.** If a stage fails, the
failure is the result (§7). **No stage will be patched to reach a nicer end
state.** The value of this rung is the fidelity of the failure map and nothing
else.

**A negative — including "the pipeline does not compose at all on real input" —
is the expected and acceptable outcome.**

---

## 1. THE STANDING CLAIM UNDER TEST

The intended next phase of the arc is *learning by watching video*: video is the
NATIVE input (motion-primary; a still is the degenerate one-frame case),
recognition turns unlabelled experience into learning, grounding is the sparse
fallback for the genuinely novel, and **the render residual is the learning
signal, so compute ∝ surprise**.

The arc's own stated bound on the category rung is that **the axes are GIVEN, not
learned from pixels**. The supervisor's prediction is that *this* is what breaks
first on real video.

**Predicting is not measuring.** This rung measures.

## 1.1 WHAT IS ALREADY KNOWN, so this rung does not re-claim it

Real BSDS300 photographs have **already** reached the retina/lateral stage
(`scripts/assembled_eye_scale.py::agreement`, `results/assembled_eye_agreement.json`).
Recorded there, and **not this rung's finding**:

| quantity (grid 32) | value |
|---|---|
| agreement sparsity, graph | **73.55%** fire |
| luminance-DoG reference | **17.59%** |
| change-detection sparsity | **96.06%** |
| control: uniform field | 0.00% (floor OK) |
| control: hard edge | 18.75%, boundary-localised (control passes) |

So on *still* natural images the retina is already known to be **~4× denser than
its own DoG reference and ~96% saturated on the change channel**. That input was a
**still crop drifted 1 px/tick** — synthetic motion.

The scale profile is also already known
(`results/assembled_eye_regimeA.json`, same engine family):

| grid | cells | ms/tick | µs/cell |
|---|---|---|---|
| 16 | 256 | 26.0 | 101.6 |
| 32 | 1024 | 355.4 | 347.0 |
| 64 | 4096 | **5684.0** | 1387.7 |

`fit_drive` exponent **1.988** (r²=0.99993) — the **O(N²) drive**, confirming the
known scale fact. `fit_python_ffi` exponent 0.953 (linear).

**What is therefore NEW and unmeasured, and is what this rung claims:**

1. **REAL VIDEO** — an actual temporal sequence off Jellyfin, not a drifted still.
2. **The stages ABOVE the retina on real imagery** — proto-objects and identity
   have *never* been fed a real frame.
3. **compute ∝ surprise** — never tested on anything.

---

## 2. CORPUS (declared in advance; no substitution after looking)

| source | what | count | provenance |
|---|---|---|---|
| **Jellyfin** | real broadcast child-directed video, HEVC 1080p MKV, streamed over HTTP by PyAV | catalogue 2785 episodes / 91 movies as user `william`; **this rung decodes a declared frame budget from a small declared set of episodes** | `https://jellyfin.hrdwrbob.net`, token validated live |
| **BSDS300** | real natural photographs | 300 jpg (200 train / 100 test) | `data/vision_curriculum/BSDS300` (via the `data/` symlink, §10.2) |

**No synthetic corpus stands in for either.** Where a synthetic input appears it is
a **declared control**, never data. Exact episode ids, frame indices and counts are
recorded in the results file — **not fabricated, and not chosen after seeing the
numbers**.

**Honest scope, stated now (§8):** Jellyfin is broadcast child-directed video. It
is **not egocentric** and not SAYCam. Cartoon/broadcast statistics (flat regions,
hard edges) differ from natural-scene statistics, which is exactly why BSDS is
carried alongside as the natural-statistics control.

---

## 3. THE STAGES, AND THE MEASURE AT EACH

The pipeline is staged in the order the arc assembled it. **At every stage three
things are recorded, separately:** (a) does it produce output AT ALL; (b) is that
output MEANINGFUL against a pre-declared criterion; (c) wall-clock cost.

### S1 — RETINA on real video

**Measure.** Boot the committed assembled eye (`change=1, sustain=1, lateral=1` —
the §9 opt-ins the eye ships with, set as graph data, no code fork). Present real
decoded video frames in temporal order. Per frame record: fraction of HCells whose
lateral residual fires, fraction of cells the change channel drives, and ms/frame.

**Positive control (§1, §10.2):** the same instrument on (i) a uniform field —
must read ~0% fire; (ii) a hard synthetic edge — must fire ONLY at the boundary.
**If either control fails, S1 is reported as UNINTERPRETABLE and no S1 number is
claimed.** A dense reading off a broken instrument is not a finding.

**Prediction (stated in advance):** dense firing, **>50%**, in family with the
known BSDS 73.55% / 96.06%. Real video is if anything *more* saturating than a
drifted still, because a real cut changes every pixel.

**What each outcome means.**
- **Dense (>50%)** ⇒ the retina does **not** sparsify real input; every downstream
  stage receives a nearly-full field, and the "sparse residual" premise of the
  learning story fails at the first stage.
- **Sparse (<25%)** ⇒ the premise survives S1; the bottleneck is further up, and
  the BSDS density was an artifact of the drifted-still protocol.
- **Between** ⇒ reported as indeterminate; no claim.

### S2 — COMPUTE ∝ SURPRISE (the headline test)

**Measure.** Over a declared contiguous run of real video frames spanning both
**static shots and hard cuts** (so surprise genuinely varies), record per frame:
- `surprise` = mean |frame_t − frame_{t−1}| over the presented field (the adapter's
  own mechanical difference — the render-residual proxy available today);
- `cost_ms` = wall-clock of the full drive+tick for that frame.

**Statistic.** Spearman ρ(surprise, cost_ms) across frames, plus the coefficient of
variation of `cost_ms`. **Unit of analysis is the FRAME** (§4); reported with n.

**Decision rule, fixed now.**
- **ρ < 0.3 AND CV(cost) < 10%** ⇒ **compute is FLAT in surprise.** The
  compute-∝-surprise claim is **refuted as currently built**: cost is set by cell
  count, not by content.
- **ρ > 0.5** ⇒ compute genuinely tracks surprise; the claim survives its first
  real test.
- **otherwise** ⇒ indeterminate, reported as such.

**Prediction:** ρ ≈ 0, CV small. The drive is a per-cell sweep whose cost is
content-independent; a cut and a still frame cost the same. **I expect to refute
the claim I would like to be true** — which is the point of stating it in advance.

**Positive control:** the surprise axis must be shown to genuinely vary (report
min/median/max surprise). A flat surprise axis makes ρ meaningless — if surprise
does not vary, S2 is reported UNINTERPRETABLE, not null.

### S3 — PROTO-OBJECTS on real frames

`border_ownership_world.add_field` consumes **`list[list[int]]` — an INTEGER value
grid**. Real luminance is continuous, so the adapter must **quantize to k levels**.

**k is not derived from anything. I choose it. That is the point** — it is the
"axes are GIVEN, not learned" bound in its most concrete form (§13: a number that
goes IN). Therefore k is **swept, not tuned**: k ∈ {2, 4, 8, 16}, and the
**k-sensitivity is itself a reported result**.

**Measure**, per (frame, k): does `run_rules` reach a fixpoint within a declared
budget; number of `ProtoObject` nodes minted; number of connected components;
ms/frame; node/edge counts.

**Meaningfulness criterion, declared in advance.** Proto-objects are meaningful iff
the count is **object-scaled, not texture-scaled**: `n_proto / n_cells < 0.05` AND
the count is **stable across k** (ratio max/min over the k-sweep **< 3×**).
Positive control: the committed synthetic bar figure from
`scripts/border_ownership_measure.py`, whose correct proto count is known —
**if the instrument does not reproduce the synthetic answer, no real-frame number
is claimed.**

**Prediction:** fails both halves — `n_proto` scales with texture (ratio ≫ 0.05)
and swings wildly with k, because a natural frame has no flat integer regions.

**What each outcome means.**
- **Fails** ⇒ proto-objects are a **construct of the hand-supplied quantization**,
  not a percept recovered from the image; the segmentation is GIVEN by the adapter.
- **Passes** ⇒ proto-objects survive real input and the seam is further up.

### S4 — IDENTITY / RECOGNITION

The identity layer (`ShapeDecode` / `GenInfer` / `vision_category`) consumes
**relation tuples** of the form `["cell", r, c, val]` with a declared `dim_types`.

**Measure — a STRUCTURAL AUDIT, enumerated positively (§13.2's method, never off a
soft accessor).** Enumerate every consumer of `ProtoObject` across the whole tree
and every producer of `"cell"` signature tuples, and determine whether **any** path
carries a proto-object (or any pixel-derived region) into a `ShapeSignature`.

**Decision rule.** If no such path exists, that is reported as a **structural
absence** — the seam is unbuilt — with the enumeration as evidence, **not** as a
performance number. If a path exists, it is exercised on a real frame and its
output reported.

**Prediction:** no path exists. `ProtoObject` appears in 6 files, none of which is
an identity script.

### S5 — SCALE on real frames

**Measure.** Sweep presented field size over a declared grid list; fit the
wall-clock exponent; attribute cost across FFI / drive / `run_rules`.

**Decision rule.** The known scale fact is *"the wall is the PyO3 boundary and then
an O(N²) drive, not the ALU."* **Confirmed** iff the drive exponent is ≈2 (within
the fit's own error) and the FFI term is ≈linear and subdominant at the sizes that
matter. Any other profile **refutes** it and is reported as such.

**Prediction:** confirmed — drive exponent ≈1.99, FFI ≈0.95, matching the
already-committed synthetic fit, because per-cell cost is content-independent. A
real frame should not change a content-independent cost. **If real frames DO change
it, that is a more interesting result than the confirmation.**

---

## 4. ANALYSIS RULES BINDING THIS RUNG

- **Unit of analysis is the FRAME** for S2, the **(frame, k) cell** for S3 (§4).
- **Exactly the tests listed above. No sweeps beyond the declared k-sweep and grid
  list. No re-runs.** A further attempt needs a new pre-registration (§3.6).
- **Every reported number carries its engine hash, its commit, and its selector**
  (§10, §12).
- **Every stage's instrument is positive-controlled before its number is read**
  (§1 clauses 1–5). A stage whose control fails is reported UNINTERPRETABLE — never
  as a null. **"The pipeline couldn't do it" is not a finding until the instrument
  is proven alive** (§10.2 rule 3).
- **No metric surgery (§5).** If a measure looks wrong after it fails, that is a new
  pre-registration, not a reinterpretation.
- **§9:** nothing ships on by default; no default is touched at all. Verified by the
  regression oracle below.

## 5. THE REGRESSION ORACLE (must be unmoved)

- the sd orbit law `{2:1, 3:2, 4:2, 6:2, 12:4}` unchanged;
- `pytest tests/ -k migrated` green (**with `data/` symlinked: ~200/0**; the
  condition is quoted with the number per §10.2);
- run as its OWN step, exit code captured, never piped into `tail` inside an `&&`.

## 6. PROVENANCE SELF-AUDIT

A test pins **BOTH endpoints** — `git diff BASE_SHA RUNG_SHA` — never `HEAD`, never
the working tree (§12.3; this defect has occurred three times). It asserts this
rung's own commit range adds **no Rust**, **no seed**, and **edits no other rung's
files**.

---

## 7. WHAT WOULD FALSIFY THE SUPERVISOR'S PREDICTION

The prediction is *"axes-are-given breaks first."* It is **falsified** if S1 or S2
breaks first — i.e. if the retina fails to produce interpretable output on real
video at all, or if the cost profile makes the pipeline unrunnable before any
representational question is reached. **In that case the axes bound is real but
NOT first, and the next rung should be pre-registered against whatever is.**

Recording this now so the ordering cannot be rationalised afterwards.
