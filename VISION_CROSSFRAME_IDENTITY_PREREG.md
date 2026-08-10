# CROSS-FRAME IDENTITY ON REAL PIXELS — PRE-REGISTRATION

*Written and COMMITTED before any measurement on the confirmatory corpora (§3).
Nothing in this file was written after looking at a real-corpus number.*

**Base `main` HEAD:** `40318951` (the video-probe merge).
**Branch:** `gamma-substrate/vision-crossframe-identity`.
**Engine (§10):** `7d5f50c18673` @
`/home/matt/ozma/internal/research/experiments/gamma-substrate/runners/dsl/python/substrate_rs/_native.abi3.so`
— **shared build**, Rust source verified byte-identical to this worktree
(`diff -r runners/dsl/src` clean but for an untracked `py.rs.selfmod.bak`).
**This rung adds NO Rust.**
**Seed block claimed:** **55000–55999.** Verified free: the ledger's highest
allocated block is `54000–54999` (video probe, consumed-none) and `55000+`
appears in no pre-registration in this tree.

---

## 0. WHERE THIS COMES FROM

`VISION_VIDEO_PROBE_RESULTS.md` §5 ranks this first. Its exploratory §2.4b showed
the identity layer **ingests pixel-derived `["cell", r, c, v]` tuples and
self-recognises a real 16×16 frame** — so the seam is unbuilt, not unreachable,
and the open question is no longer *can pixels reach identity* but:

> **Is a region recognised in frame *t* recognised as the SAME thing in frame
> *t+Δ*, under real motion, above a floor that is actually hard?**

Three constraints are inherited and binding:

- **Toy resolution, 24×24.** Scale is a BUILD task (S5: O(N^1.887); real time
  affords 18×18). Nothing here is a claim about real-resolution video.
- **It must NOT route through border-ownership / proto-objects.** S3 is
  measured-broken on real frames (0 protos on 7/7 at k=16) and its percept
  tracks an adapter-chosen `k`. Tuples are built straight from quantized
  pixels, exactly as §2.4b did. Border-ownership is not on the path.
- **The floor must be one that can actually be lost to.** See §4.

---

## 1. WHAT IS AND IS NOT BEING OPERATIONALISED

The percept is a **fixed 6×6 aperture** at one of 16 tiled positions in a 24×24
frame. "The same thing in frame *t+Δ*" means **the content seen through the same
aperture after the world has moved**, not an object tracked to a new location.

**Stated up front so it cannot be read as more (§8):** this measures
**identity-under-appearance-change at a fixed aperture**. It is NOT object
tracking, NOT segmentation, NOT correspondence of a moving object to a moved
position. The one place a true moved-position correspondence is tested is the
synthetic-displacement corpus C3, where ground-truth displacement exists
(arm A1c), and it is labelled synthetic there.

---

## 2. CORPORA (declared in full, with counts; §8 — eval-subset coverage is part
of the claim)

| id | source | statistics | motion | counts |
|---|---|---|---|---|
| **C1 CARTOON** | Jellyfin, *Middlemost Post* S2E1, episode id `08630d4b7b215c469df19b9c42d7b617`, series index **0** of the sorted catalogue | broadcast cartoon (video probe measured 46.6% retina fire) | **REAL** | 150 frames, every 2nd decoded frame from t=300 s, area-averaged to **24×24** grey; **100 base frames** (indices 0–99) |
| **C2 LIVE-ACTION** | Jellyfin, series index **3** of the same sorted catalogue (*Secrets of the Zoo: Down Under*), episode picked by the same fixed positional rule | natural photographic (the video probe measured natural photos at 80.3% — a different regime) | **REAL** | same protocol: 150 frames, every 2nd from t=300 s, 24×24, **100 base frames** |
| **C3 APERTURE** | BSDS300 (`data/vision_curriculum/BSDS300`), **12** photographs, centre 24×24 window translated by a KNOWN integer displacement | natural photographic | **SYNTHETIC (known d)** | 12 photos × 7 displacements |

Series/episode selection is a **fixed positional index into the sorted
catalogue** — deterministic, no content decision (the video probe's convention).
C2's series index 3 was chosen from the catalogue *names only*, before any pixel
was decoded from it, to obtain a live-action title; that choice is recorded here
in advance and is not revisited.

**If a corpus fails to decode, it is REPORTED AS ABSENT. No substitution.**

---

## 3. THE SEAM (mechanical adapter work only)

Frame → 24×24 grey → quantize to **k=4** levels on a **FIXED absolute 0–255
scale** (not per-frame min/max: a per-frame adaptive scale would silently
normalise away exactly the cross-frame appearance change under test) → tile into
**16 regions of 6×6** → each region emitted as its **complete** relation set

```
[["cell", r_local, c_local, "v<q>"] , … ]     # 36 relations, ALWAYS
```

Two encoding decisions, both declared:

- **Region-LOCAL coordinates.** Absolute frame coordinates would let a probe
  match its held region by POSITION alone, which would be a catastrophic
  confound (the task would be solved without looking at the content).
- **All 36 cells emitted, including the lowest quantization level.** No
  background threshold. A threshold would be an adapter decision about what
  counts as content, and would make the signature length vary; with all cells
  emitted `covered_count` is a clean 0–36 overlap and every region is
  non-degenerate.

`k=4` and the 6×6 tiling are **hand-set** and are named as bounds (§13 — they do
NOT fall out of anything here). A **k-sensitivity check** at k∈{2,8} is run at
Δ=1 only and is declared here as a sensitivity check, not a sweep: every cell
run is reported.

---

## 4. THE DECISION IS THE GRAPH'S (architecture rule)

One new seed, `seeds/vision_crossframe_identity.json`, **two rules**, built
ENTIRELY from existing Terms (**no new Rust, no new Term, no new constant**):

- `xf_score` — `status=="xf_pending"` ⇒ `xf_max :=`
  `MaxOver(NodesOfType(ShapeSignature), sig, ShapeDecode(goal=obs.signature,
  codebook_scope=SetT([sig.name]), field="covered_count"))`; `status:="xf_scored"`.
- `xf_identify` — `status=="xf_scored"` ⇒ `identified_as :=`
  `Argmax(NodesOfType(ShapeSignature), sig, <the same ShapeDecode>).name`;
  `xf_ntied := Count(Filter(ShapeSignature, sig, Eq(<same ShapeDecode>, obs.xf_max)))`;
  `status:="xf_done"`.

`codebook_scope` is the existing per-net basin affordance (`seeds/reflex_net.json
::reflex_ground_residual`) pointed at a **singleton** name set, so
`ShapeDecode`'s own `covered_count` becomes a per-candidate score and `Argmax`
does the choosing. **Python adds tuples, calls `run_rules()`, and reads
`identified_as` back. It makes no comparison and takes no branch on graph state.**

`ShapeDecode`'s `covered_relation` is same-arity + same-predicate + `Covers`, so
on these tuples `covered_count` is **exactly the number of cells identical in
local position and quantized value** — an integer overlap, stated here so that
§7's reference arm cannot be presented as a surprise.

**§9:** the seed is gated on `CrossFrameParams.crossframe > 0.5`, ships **OFF**,
and is **not registered in the default boot set**. The runner loads its manifest
explicitly. No committed seed, rule, default or artifact is edited.

---

## 5. ARMS

All arms share ONE codebook per base frame: the 16 regions of frame *t*, inserted
in a **seed-randomised order** (so `Argmax`'s tie-breaking cannot systematically
favour index 0). Δ ∈ **{1, 2, 5, 10, 25}** decoded frames.

| arm | probe | what it destroys |
|---|---|---|
| **A1 REAL** | region *i* of frame *t+Δ* | nothing — the hypothesis |
| **A2 TEMPORAL-SHUFFLE** | region *i* of a frame *t′* drawn uniformly from the sequence with \|t′−t\| ≥ 30 | temporal correspondence; image statistics preserved |
| **A3 ARRANGEMENT-DESTROYED** | region *i* of frame *t+Δ* with its 36 cell VALUES randomly permuted over the 36 positions | spatial arrangement; the value multiset preserved EXACTLY |
| **A1c MOTION-COMPENSATED** (C3 only) | the window at the KNOWN shifted position | nothing — the ceiling / positive control |

**A3 is the floor that matters.** It leaves the region's value histogram exactly
intact, so it is beaten only by information that lives in *arrangement*. On
cartoon statistics (large flat regions with very distinctive histograms) it is
expected to score well above chance — that is the point. **A2 is the floor the
task named; it is included, and it is explicitly NOT assumed to be hard**: on a
static shot the scene barely changes, so A2 may be nearly as easy as A1, and if
so that is a fact about the corpus which will be reported as such rather than
read as a null.

Chance is **1/16 = 0.0625** (analytic, reported as a line, not an arm).

---

## 6. INSTRUMENT GATES (§1) — run and reported BEFORE any arm is read

| gate | requirement |
|---|---|
| **G1 CEILING** | Δ=0 (probe IS the held region): accuracy ≥ 0.99 |
| **G2 NOISE FLOOR** | probes of uniform-random cell values: accuracy within \[0.02, 0.15\] (chance 0.0625), and answer entropy high |
| **G3 ALIVE (§1.1 cl.4)** | per-arm normalized entropy of the 16 possible `identified_as` answers; an arm below 0.50 is FLAGGED as possibly dead and its "floor" is not read as a floor |
| **G4 TIE** | mean `xf_ntied` and the fraction of trials with `xf_ntied > 1`; a high tie rate makes the strict top-1 number uninterpretable and must be reported alongside it |
| **G5 ORDER** | A1 at Δ=1 re-run under a second, independent codebook insertion order; the two must agree within CI |

**A failed gate stops the arm being read. It is not repaired by moving a
threshold (§5).**

---

## 7. STATISTICS, EXACTLY

**Unit of analysis is the BASE FRAME (§4), not the region.** The 16 regions of
one frame share that frame's content and compete against one codebook, so they
are not independent.

- **PRIMARY:** per-base-frame accuracy (0–16 correct / 16); the arm's statistic
  is the **mean over 100 base frames**, with a **95% t-CI over base frames**.
- **SECONDARY:** pooled trial-level accuracy (n = 1600) with a **95% Wilson CI**,
  reported for every arm as the task requires, and **declared anticonservative**
  because of within-frame dependence.
- **If PRIMARY and SECONDARY disagree on a verdict, PRIMARY governs.** Declared
  now, in advance.

**REFERENCE R1 — PIXEL NEAREST-NEIGHBOUR (adapter-side, NOT an arm).** The same
16-way choice made outside the graph by maximum exact-cell overlap. Reported as
the **trial-for-trial agreement rate** with `identified_as`. This is not a
control and cannot pass or fail; it exists so the rung cannot claim substrate
structure that is really Hamming distance.

---

## 8. n, FIXED IN ADVANCE

100 base frames per real-motion corpus × 16 regions = **1600 trials per (arm, Δ,
corpus)**. Fixed by a timing pilot on **synthetic random regions only** (no real
corpus was decoded for it): 240 observations per base frame resolve in ~4.3 s
under concurrent load, so the full grid is ~15–30 min of wall clock — n is fixed
by the design, not by what the machine could stretch to. At the frame-level unit
(n=100) a per-arm sd of 0.20 gives a t-CI half-width of ±0.04, which separates
arms differing by ≳0.09. **No arm will be extended, re-run or added after
looking.**

---

## 9. DECISION RULE

**H1 (primary), evaluated INDEPENDENTLY on C1 and C2, at k=4, Δ=1:**

- **CROSSES** iff A1's 95% CI lower bound exceeds **both** A3's and A2's CI upper
  bounds **and** 0.0625.
- **NULL** iff A1's CI overlaps A3's, or overlaps A2's.
- A null on either corpus is reported as a null on that corpus. A split verdict
  is reported as a split verdict, not resolved in favour of the better one.

**WHAT WOULD FALSIFY THE HYPOTHESIS, stated plainly:** if a region's identity
across one real frame step is carried no better than by its value histogram
alone, A1's CI will overlap A3's, and **cross-frame identity on real pixels does
not hold**. That is a complete result and it redirects the video phase. It will
be reported as the headline if it occurs.

**H2 (secondary, reported not gated):** the **identity horizon** — the largest Δ
at which A1 remains CI-separated from max(A2, A3).

**H3 (C3, reported not gated):** accuracy vs KNOWN displacement d ∈ {0,1,2,3,4,6,8}
pixels, with A1c as the ceiling at each d.

**Exactly the tests listed here. No sweeps. No re-runs. A further attempt needs a
new pre-registration with a new mechanism-level hypothesis (§3.6).**

---

## 10. MY PREDICTIONS, IN ADVANCE (§3.7)

1. **A1 at Δ=1 will be high — I predict > 0.80 on C1 and > 0.70 on C2 — and H1
   will CROSS on both.** One frame step at 24×24 changes few quantized cells.
2. **A3 will be well above chance — I predict 0.25–0.55 on C1.** Cartoon regions
   have very distinctive value histograms. The floor is not trivial and I expect
   to have to beat it by a real margin, not by default.
3. **A2 will also be well above chance — I predict 0.40–0.70 on C1** — because
   much of a cartoon shot is static. **A2 may fail to separate from A1 at large
   Δ, and that would be a fact about the corpus, not evidence for identity.**
4. **A1 will decay with Δ**, more slowly on C1 (static shots) than on C2.
5. **A1 ≡ R1 (pixel Hamming NN) at ≥ 0.99 trial-for-trial agreement.** The
   graph's verdict at this grain IS exact-cell overlap. If this prediction holds,
   the results file must say so in the headline: the substrate is not adding
   representational structure here, it is running nearest-neighbour through a
   Term. I am stating this before the run so it cannot later be presented as a
   discovered nuance.
6. **C2 (natural statistics) will score LOWER than C1 at matched Δ.**

**Provisos.** Shot cuts inside the 150-frame window will make individual base
frames collapse; the per-pair mean absolute pixel difference is reported so this
is visible rather than averaged away. If C1's shot is largely static, the whole
Δ axis compresses and H2's horizon is uninformative — that would be a corpus
limitation and will be labelled one.

---

## 11. WHAT THIS RUNG WILL NOT CLAIM (§8, declared in advance)

- Nothing about real resolution. 24×24, 6×6 apertures, 16-way choice.
- Nothing about object tracking or segmentation (§1).
- Nothing about learning — nothing is trained; the codebook is one frame's
  regions, held for one comparison and discarded.
- Nothing about proto-objects or border-ownership, which are deliberately bypassed.
- Nothing about which of the substrate's mechanisms is responsible, beyond what
  §7's R1 reference measures.
- **Two hand-set numbers (k=4, 6×6 tiling) parameterise the whole measurement.**
  Neither falls out of anything. They are swept/sensitivity-checked, not derived.

---

## 12. VERIFICATION (§9, §12.3)

- `bash scripts/rung7_vision_bench.sh` → **200 passed, exit 0**, measured on this
  worktree BEFORE any file is added and again after.
- sd orbit law `{2:1, 3:2, 4:2, 6:2, 12:4}` (`tests/test_sdloop_vision_migrated.py`)
  unmoved, before and after.
- A provenance self-audit pinned to **BOTH** endpoints (`git diff BASE_SHA
  RUNG_SHA`, never `HEAD`, never the working tree), using a `:/` root-magic
  pathspec (git reports `--name-only` from the git ROOT but resolves a pathspec
  relative to CWD — this defect has occurred four times in this arc), and
  **positive-controlled red-then-green** before it is trusted.
- Machine state (`ps`, load average) recorded alongside any wall-clock number
  (§0.1 of the video probe: a contended timing is a rumour).
