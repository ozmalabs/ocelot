# THE GROUPING CEILING — RESULTS: **EVERY RELAXATION OF ADMISSIBILITY IS SPENT ON THE GROUND. THE FIGURE-SIDE SIZE DISTRIBUTION IS IMMOBILE ACROSS THE WHOLE FAMILY. NO MECHANISM IS WARRANTED — AND THE APERTURE, WHICH I PREDICTED WAS INNOCENT, IS NOT.**

*Pre-registration `VISION_GROUPING_CEILING_PREREG.md`, committed **`fcdff1e7`** BEFORE
any number. Nothing in it was edited after the first number. This rung reports its
pre-registered **OUTCOME A (DEGENERATE)** and **builds nothing.***

**ENGINE PROVENANCE (§10)** — printed from **inside** the measuring process into
`results/grouping_ceiling.json` and `results/grouping_ceiling.log`:

```
engine 9931e144d19b @ <this worktree>/runners/dsl/python/substrate_rs/_native.abi3.so
  [1 other tree build(s) shadowed]
```

Branch `worktree-agent-ab36b4c2cad253f28`, base `main` HEAD **`91e367f0`**. Engine built
in-tree by `scripts/engine_build.sh` (**`own`**); **no Rust change in this rung**.
Migrated provenance gate run as **its own step, first: 7 passed**. `data/` is a symlink
to canonical (§10.2), never a copy. Corpus pins asserted at run time: C1 `08630d4b`,
C2 `119eca43`.

---

## 1. THE HEADLINE

**The family of value-admissibility relations has ONE degree of freedom, and it moves the
BACKGROUND.**

Across **18 admissibility relations** — 11 quantizer coarsenesses spanning 5 octaves
(`k` = 2…64) and 7 chaining tolerances (`τ` = 0…8) — on 112 tiles per corpus:

| quantity | C1 cartoon | C2 live-action | span |
|---|---|---|---|
| **giant component** (largest / 324 cells) | 0.116 → **1.000** | 0.066 → **1.000** | **the whole range** |
| components per tile | 141.4 → 1.0 | 151.0 → 1.0 | **141× / 151×** |
| **ENCLOSED component size, median** | **1 – 2** | **1 – 2** | **does not move** |
| **ENCLOSED component size, mean** | 1.63 – 4.25 | 1.13 – 3.37 | 2.6× / 3.0× |
| **size of the component a typical ENCLOSED cell lives in** | **2 – 10** | **1 – 7** | never reaches the target decade |
| **largest enclosed component, over the BIN ladder** | 43 – **70** | 24 – **75** | **≤ 23.1% of a tile — and the CHAIN arms are strictly SMALLER (down to 2)** |

**The ground traverses its entire range while the figure side stands still.** The
pre-registered front does not "jump over" the target band — **it never enters the plane
at all.** Relaxing admissibility by any means in this family buys background, and the
enclosed components it is supposed to enlarge are the same 1–2 cells they were at the
incumbent `k=16`.

**⇒ PRE-REGISTERED OUTCOME A. NO MECHANISM IS WARRANTED IN THIS FAMILY.** No tolerance,
no quantizer coarseness, and no combination of the two produces few-and-large. The
value-flood rung's *"loosening loses"* is not a fact about the two tolerances it tried —
it is the shape of the entire family, measured.

### AND THE FINDING THAT OUTRANKS IT — **THE FLOOD IS NOT FRAGMENTING. ENCLOSURE IS DISCARDING.**

A cross-check I ran to quantify a confound I had already flagged **undercut my own §3 and
produced the sharper result** (§3 in full; **POST-HOC**, and marked so everywhere):

| at the incumbent `k=16`, 7 frames | C1 tiled 18×18 | C1 whole 72×72 | C2 tiled | C2 whole |
|---|---|---|---|---|
| components of **≥ 60 cells the flood produces** | **86** | 94 | **111** | 83 |
| of those, how many **survive the enclosure test** | **1** | 42 | **0** | 34 |
| **share surviving** | **1.2%** | **44.7%** | **0.0%** | **41.0%** |

**THE EXACT-VALUE FLOOD AT k=16 PRODUCES 83–111 REGIONS OF ≥60 CELLS PER SEVEN FRAMES,
AT BOTH GRAINS, IN COMPARABLE NUMBERS.** A quarter to a third of **all** cells in a tile
live in a component of ≥60 cells (C1 0.256, C2 0.305), and the typical tile cell's region
is **21–23 cells**, not one. **The flood's own output is not a field of singletons. The
ENCLOSED SUBSET is** — because `bo_bgflood` classifies anything reachable from the field
border as ground, and **in an 18×18 window a 60-cell region almost always touches the
edge.** Geometry, not statistics: only **19.75%** of centre positions in an 18×18 tile can
hold a 61-cell disc clear of the border, against **74.15%** in a 72×72 frame.

**This is the value-flood rung's own diagnosis of `G_figadj` — *"it encodes ISOLATION,
not objecthood"* — one rule EARLIER, and worse: `bo_bgflood` encodes "does not touch the
WINDOW" as "is a figure", and a window edge is not a scene boundary.** It does not
overturn the §1 negative (the value family is still closed for enclosed size at either
grain); it says the negative was being measured downstream of a predicate that had
already thrown the large regions away.

---

## 2. THE CHARACTERISATION, WITH NO MECHANISM (the brief's first instruction)

### 2.0 THE INSTRUMENT, RECONCILED FIRST — and it caught me

`M0` puts live tiles through the **substrate** and checks the numpy component field
against the graph's own `glabel` partition, cell by cell:

| | C1 | C2 |
|---|---|---|
| tiles put through the substrate | 32 | 32 |
| **partition identical to the graph's `glabel`** | **32/32** | **32/32** |
| **enclosed set identical to the graph's `bg` flag** | **32/32** | **32/32** |

And the published floor, re-earned **on the sweep's own code path** and asserted in-run
(the run VOIDS otherwise):

| | C1 | C2 |
|---|---|---|
| enclosed components at BIN `k=16`, 112 tiles | **5047** | **3978** |
| peer-competition rung, published | **5047** | **3978** |

**THAT ASSERTION EXISTS BECAUSE THE FIRST VERSION OF THIS SCRIPT WAS WRONG AND M0
PASSED ANYWAY.** See §6.1 — it is the most useful thing that happened in this rung.

### 2.1 What IS the size distribution the flood produces?

At the standing configuration (G72, `REGION=18`, BIN `k=16`), per corpus over 112 tiles:

| | C1 | C2 |
|---|---|---|
| enclosed components | 5047 | 3978 |
| **median size** | **1** | **1** |
| mean size | 2.06 | 2.27 |
| p90 | 4 | 5 |
| max | 66 | 50 |
| **median size of the component a typical ENCLOSED cell lives in** | **3** | **3** |
| **fraction of enclosed cells in components ≥ 60** | **0.0063** | **0.0000** |
| within-component raw-luminance range (p99) | 13.5 | 13.9 |

This reproduces the peer rung exactly and adds the statistic the arc had never
reported — **the size-biased one.** *Median component size* is dominated by singletons
and can be dismissed as an artifact of counting; *the size of the region a typical cell
belongs to* cannot. **It is 3 cells.** Six in every thousand enclosed cells on C1, and
none on C2, belong to a region of the target size.

### 2.2 Does ANY configuration in the family change that? — **no**

The full front, tiled, both corpora (`enc` = enclosed):

| arm | C1 comps/tile | C1 enc median / mean / max | C1 cell's region | C1 giant [95% CI] | C2 enc median / mean / max | C2 cell's region | C2 giant [95% CI] |
|---|---|---|---|---|---|---|---|
| BIN k=2 | 5.7 | 2 / 4.25 / 64 | 10 | 0.603 [0.574, 0.627] | 2 / 2.93 / 27 | 5 | 0.787 [0.719, 0.860] |
| BIN k=3 | 11.5 | 1 / 3.15 / 43 | 6 | 0.500 [0.474, 0.543] | 2 / 3.17 / 24 | 5 | 0.650 [0.593, 0.685] |
| BIN k=4 | 18.2 | 2 / 3.06 / 61 | 5 | 0.412 [0.370, 0.465] | 2 / 3.37 / 40 | 7 | 0.548 [0.491, 0.599] |
| BIN k=6 | 28.5 | 1 / 2.65 / 53 | 4 | 0.363 [0.318, 0.414] | 1 / 2.85 / 75 | 5 | 0.424 [0.404, 0.472] |
| BIN k=8 | 39.4 | 1 / 2.37 / 44 | 3 | 0.312 [0.272, 0.347] | 1 / 2.75 / 40 | 5 | 0.390 [0.347, 0.424] |
| BIN k=11 | 51.6 | 1 / 2.10 / 55 | 3 | 0.256 [0.241, 0.284] | 1 / 2.61 / 73 | 4 | 0.333 [0.290, 0.357] |
| **BIN k=16 (incumbent)** | 69.3 | **1 / 2.06 / 66** | **3** | 0.205 [0.184, 0.253] | **1 / 2.27 / 50** | **3** | 0.256 [0.224, 0.289] |
| BIN k=23 | 85.9 | 1 / 1.87 / 48 | 2 | 0.178 [0.148, 0.228] | 1 / 2.17 / 73 | 3 | 0.187 [0.173, 0.199] |
| BIN k=32 | 102.5 | 1 / 1.81 / 47 | 2 | 0.157 [0.136, 0.191] | 1 / 1.98 / 55 | 3 | 0.142 [0.117, 0.154] |
| BIN k=45 | 120.9 | 1 / 1.72 / 50 | 2 | 0.133 [0.117, 0.168] | 1 / 1.85 / 47 | 2 | 0.086 [0.082, 0.103] |
| BIN k=64 | 141.4 | 1 / 1.63 / **70** | 2 | 0.116 [0.096, 0.144] | 1 / 1.72 / 54 | 2 | 0.066 [0.060, 0.077] |
| CHAIN τ=1 | 17.0 | 1 / 2.25 / 63 | 3 | 0.617 [0.540, 0.674] | 1 / 1.78 / 20 | 2 | 0.853 [0.750, 0.883] |
| CHAIN τ=2 | 6.2 | 1 / 2.20 / 45 | 4 | 0.944 [0.907, 0.968] | 1 / 1.13 / 4 | 1 | 0.999 [0.994, 1.000] |
| CHAIN τ=3 | 2.6 | 1 / 1.94 / 14 | 2 | 0.994 [0.991, 1.000] | 1 / 1.14 / 2 | 1 | **1.000** |
| CHAIN τ=4 | 1.4 | 1 / 2.47 / 14 | 5 | **1.000** | *(empty)* | — | **1.000** |
| CHAIN τ=6 | 1.1 | 2 / 2.50 / 3 | 3 | **1.000** | *(empty)* | — | **1.000** |
| CHAIN τ=8 | 1.0 | *(empty)* | — | **1.000** | *(empty)* | — | **1.000** |

**Read the two right-hand columns of each corpus against each other.** The giant goes
from a sixth of a tile to the whole tile. The typical enclosed cell's region goes from
3 cells to 3 cells.

**EXPOSURE IS REPORTED, NEVER ASSUMED.** The enclosed population thins as the ground
grows (C1: 5047 components at k=16 → 140 at k=2 → 2 at τ=6 → **0** at τ=8; C2 → **0**
at τ≥4). **The empty arms are marked EMPTY and no statistic is computed over them** —
they are structurally exhausted, not null. Every number above is over a non-zero
population, and the thin ones say so.

**The counterintuitive detail, reported because it is the opposite of the obvious
expectation:** the **largest** enclosed component anywhere on C1 (**70 cells**) occurs at
`k=64`, the **finest** quantization in the ladder — not the coarsest. Coarsening does not
grow figures; it dissolves them into the ground.

### 2.3 What would have to change for a 60-cell region? — **MEASURED, IN THE REPRESENTATION'S OWN UNITS**

The instrument's own resolving limit **falls out** (§13), from control 3: a constant
region survives quantization only while its internal spread fits inside **ONE quantizer
bin**. Measured, not asserted — recovery of a genuine 61-cell disc against a fixed
boundary contrast:

| internal spread / boundary contrast | 0 | 1/64 | 1/32 | 3/64 | **1/16 = 0.0625** | 3/32 = 0.094 | ≥ 0.125 |
|---|---|---|---|---|---|---|---|
| disc recovered | 20/20 | 20/20 | 20/20 | 20/20 | **20/20** | **0/20** | 0/20 |

The limit sits **exactly at `1/k` = 1/16 = 0.0625** — the arithmetic's own bin, no
constant chosen. Now the material, in those same units:

| | C1 T=60 | C2 T=60 |
|---|---|---|
| disc cells | 61 | 61 |
| **internal luminance spread, median** | **114.05** | **79.56** |
| frame dynamic range | ~250 | ~237 |
| **spread as a fraction of the range** | **0.456** | **0.336** |
| **× the instrument's own 0.0625 limit** | **7.3×** | **5.4×** |
| **spread ÷ the frame's own step p95 ("the edges")** | **1.886** | **1.901** |
| **fraction of positions where that ratio exceeds 1** | **0.805** | **0.768** |
| **quantizer levels required to unify the disc, median** | **1.91** | **2.86** |

**A 60-cell neighbourhood of a natural frame varies internally by MORE than the
strongest 5% of adjacent-pair steps in the same frame, at ~80% of positions.** The
tolerance that would hold such a region together is a tolerance that crosses almost
every edge in the image.

And the closure, in the mechanism's own parameter: **to make a typical 60-cell disc one
exact-value component you need fewer than 3 quantizer levels for the entire frame** — and
at `k=2`/`k=3` the giant already owns **60–79%** of the tile while the typical enclosed
cell's region is still 5–10 cells. **The `k` that unifies a 60-cell region is a `k` at
which the field is one background blob.** The mechanism is self-contradictory in its own
measured units, and no parameter rescues it.

The curve over T is monotone and shows no knee: required-`k` falls 7.5 → 3.6 → 2.5 → 1.9
→ 1.7 → 1.5 (C1) and 10.9 → 5.5 → 3.6 → 2.9 → 2.3 → 1.9 (C2) for T = 10, 20, 40, 60,
100, 150. **60 is not special; the whole decade is out of reach.** Even T=20 needs
`k ≈ 3.6` (C1).

### 2.4 H2 — CHAINING IS THE MECHANISM OF THE SWALLOW, AND THE MARGIN IS LARGE

`vrange` (within-component raw range) discriminates as pre-registered. Under BIN it is
bounded by one bin **by construction**; under CHAIN it is unbounded and here it is
measured:

| arm | admitted local step | vrange p99 | vrange max | **max ÷ admitted step** |
|---|---|---|---|---|
| BIN k=16 (C1) | 15.6 | 13.5 | 15.5 | **1.0** — one bin, as constructed |
| BIN k=64 (C1) | 3.9 | 3.3 | 3.9 | **1.0** |
| **CHAIN τ=1, k=16 (C1)** | **15.6** | **127.5** | **185.6** | **11.9×** |
| **CHAIN τ=2, k=16 (C1)** | 31.3 | 187.0 | 234.5 | **7.5×** (94% of the dynamic range) |
| CHAIN τ=1, k=16 (C2) | 14.8 | 145.1 | 187.3 | **12.7×** |

**A component built from steps of one quantizer bin spans up to twelve of them.** That
is the ground walking into the figure one admissible step at a time, and it is why the
value-flood rung's `|Δ|≤1` and `|Δ|≤2` produced *fewer* protos rather than larger ones.
**H2 confirmed. The failure of loosening is CHAINING, not tolerance** — and this does
NOT rescue tolerance, because §2.2 shows binning (which cannot chain, by construction)
fails on the same axis for a different reason: it dissolves figures into the ground.
**Both ends of the family fail, and now each failure has its own named mechanism.**

### 2.5 The random-input floor — structure is real and does not change the shape

The identical sweep on 100 iid uniform speckle fields (seeds 103000–103099):

| BIN k=16 | speckle | C1 | C2 |
|---|---|---|---|
| enclosed mean size | **1.13** | 2.06 | 2.27 |
| enclosed max size | **6** | 66 | 50 |
| giant | 0.012 | 0.205 | 0.256 |

**Natural frames carry structure far above the noise floor** — 1.8–2× the mean, 8–11×
the max. P5's first half confirmed. **And the front has the same shape on noise:**
speckle's enclosed median is **1 at all 18 arms** while its giant runs 0.006 → 0.983.
P5's second half confirmed: the structure is real and it is not enough to put a window
in the front.

One inversion worth recording: **natural frames PERCOLATE EARLIER than noise.** Under
chaining, C1/C2 reach giant > 0.9 at τ = 2–3; speckle needs τ = 6. Natural images are
locally smooth, so admissible steps chain more readily on them. **The material's
structure works AGAINST this mechanism, not for it.**

---

## 3. THE FINDING THAT REFUTES MY OWN PREDICTION — **AND THE CROSS-CHECK THAT REFUTED MY FIRST READING OF IT** (POST-HOC)

I predicted (P4) that whole-frame components would look like tiled ones — *"a field of
singletons is not being cut by anything."* **Measured, at the identical `k=16`:**

| | C1 tiled 18×18 | **C1 whole 72×72** | C2 tiled | **C2 whole** |
|---|---|---|---|---|
| enclosed mean size | 2.06 | **3.54** | 2.27 | **4.21** |
| enclosed **max** size | 66 | **275** | 50 | **736** |
| the typical enclosed cell's region | 3 | **12** | 3 | **13** |
| **fraction of ENCLOSED cells in components ≥ 60** | **0.0063** | **0.2050** | **0.0000** | **0.2546** |

**My first reading of this was that the aperture FRAGMENTS large regions — a 33× effect.
That reading is WRONG, and the measurement that killed it is one I ran only because my
own pre-registration had flagged the enclosure confound.** On the basis that does not
involve the enclosure predicate at all:

| | C1 tiled | C1 whole | C2 tiled | C2 whole |
|---|---|---|---|---|
| **fraction of ALL cells in components ≥ 60** | **0.2559** | 0.3695 | **0.3053** | 0.4374 |
| the typical cell's region, **all cells** | **21** | 32 | **23** | 38 |
| **components of ≥ 60 cells produced, 7 frames** | **86** | 94 | **111** | 83 |
| of those, surviving the enclosure test | **1** | 42 | **0** | 34 |
| enclosed cells as a share of the field | 0.287 | 0.637 | 0.249 | 0.609 |

**The flood produces essentially the SAME number of ≥60-cell regions at both grains
(86 vs 94; 111 vs 83 — on C2 the TILED field produces MORE).** It is not fragmenting
them. What changes by 34–37× is **the share that survives `bo_bgflood`'s enclosure
test**: 1.2% / 0.0% tiled against 44.7% / 41.0% whole.

**The mechanism is geometry, and it is computable rather than fitted.** `bo_bgflood`
declares any region reachable from the field border to be **ground**. A 61-cell disc
clears an 18×18 border from only **19.75%** of centre positions, against **74.15%** of a
72×72 frame's. A large region inside a small window is *almost obliged* to touch the
window edge, and the predicate then calls it background.

> **`bo_bgflood` encodes "does not touch the WINDOW" as "is a FIGURE". A window edge is
> not a scene boundary.** This is the value-flood rung's diagnosis of `G_figadj` — *"it
> encodes ISOLATION rather than OBJECTHOOD, and was validated only on stimuli where the
> two coincide"* — **one rule earlier in the same pipeline**, where the synthetic control
> (a figure centred in a blank field, well clear of the frame) again makes the two
> coincide trivially.

**STATUS AND SCOPE — this is an OBSERVATION, not a claim, and it is POST-HOC.** It comes
from a pre-registered arm (M4) plus a supplementary count I ran to quantify a confound
my own prereg named; it was not among the pre-registered statistics, and **§5 forbids me
from treating it as this rung's earned result.** Three things it does **not** establish:

- **that those ≥60-cell components are objects.** Many will be wall, sky, floor. Nothing
  here inspects what they are.
- **that removing the aperture is a fix.** On the whole frame, `enclosed cells` become
  63.7% / 60.9% of the field — the enclosure test stops being selective at all, which is
  its own failure mode, and the peer rung's downstream gates were never priced on that
  population.
- **that the value family reopens.** §1's negative holds at BOTH grains: the whole-frame
  enclosed median is still 1 and the whole-frame front has the same shape.

**What it does establish is where to look next**, and it is one rule upstream of every
predicate the last five rungs have argued about. `REGION=18` was chosen by the resolution
rung on **statistical** grounds (n_eff, cost), with its own scope note that component
structure changes sharply with tile size; **nobody had priced what it does to the
enclosure predicate.**

---

## 4. THE DECISION — STATED PLAINLY, AS THE BRIEF REQUIRED

**NO MECHANISM IS WARRANTED, AND NONE IS BUILT.** This rung adds no rule, no flag, no
node, no seed byte and no Rust.

1. **The family is exhausted by measurement, not by argument.** 18 admissibility
   relations over 5 octaves of quantizer and 8 chaining steps; the figure-side
   distribution is immobile in all of them; the largest enclosed component anywhere is
   ≤ 23% of a tile at every one.
2. **The material forbids it in its own units.** A target-sized region's internal spread
   is 5–7× the exact-value flood's own resolving limit and ~1.9× the frame's edge
   contrast. The `k` that would unify it is a `k` at which the field has percolated.
3. **Both failure directions now have named mechanisms** — coarsening dissolves figures
   into the ground; chaining walks the ground into the figures across up to 12 quantizer
   bins. Neither is repairable by a parameter, and §13 forbids tuning one anyway.

**What this licenses, and what it does not.** It closes *"change what makes two cells the
same region, in the value domain"* — the peer rung's named next lever, measured and
found empty. It says **nothing** about non-value grouping (motion, contour, ownership,
learned appearance): those are different relations and this rung did not test them. And
it does not show that anything fixes the problem — **"the lever is not here" is a
diagnosis.**

**THE NAMED NEXT LEVER, AND IT IS NOT A GROUPING RELATION AT ALL.** §3's post-hoc
cross-check puts it one rule further upstream than anyone has been looking: the flood
produces the large regions; **`bo_bgflood`'s enclosure predicate discards 99% of them at
tile grain**, because it reads *"touches the window edge"* as *"is background"*. That is
`G_figadj`'s recorded disease — isolation standing in for objecthood, validated on
synthetic stimuli where the two coincide — **one rule earlier**. A rung that wants large
figures should price **that predicate against the aperture**, before touching another
mint gate.

**It is NOT started here, and it must not be started from this document.** It is
post-hoc, it does not show the discarded regions are objects, and removing the aperture
makes the enclosure test non-selective (60% of the field becomes "enclosed") — a failure
mode nobody has priced either. It needs a prospective pre-registration with its own
mechanism-level hypothesis (§3 clause 6), and this rung deliberately does not write it.

---

## 5. GATES — EVERY FLOOR RE-EARNED IN THIS TREE, ON THIS ENGINE, NOTHING INHERITED

| gate | result |
|---|---|
| **Oracle** `bash scripts/rung7_vision_bench.sh`, **before** | **222 passed / 0 failed** (with `data/`) |
| **Oracle, after** | **222 passed / 0 failed** |
| Provenance gate, its own step, **first** | **7 passed** |
| **M0 partition ≡ the graph's `glabel`** | **32/32 both corpora** |
| **M0 enclosed set ≡ the graph's `bg`** | **32/32 both corpora** |
| **Published enclosed-component floor, asserted in-run** | **5047 / 3978 — exact** |
| Control 2, ideal exemplar | **found exactly, all 6 targets × all 11 `k`** |
| Control 3, graded exemplar | **limit falls out at 1/k, measured** |
| Control 1, random input | **ran; front identical in shape, floor 1.13 mean** |
| §13 `scripts/gate_audit.py` | **run; all 18 sinks enumerated below, one at a time** |
| Seed audit | **`ok: true`, none outside block, `unknown_sinks: 1` — resolved BY HAND, §7** |
| `python3 -m domains.seed_record --write` | **run; ledger regenerated** |
| **§9** | **`git diff -- seeds/ runners/` is EMPTY.** No Rust, no seed, no rule, no flag. Byte-identity by construction. |

### 5.1 THE §13 AUDIT, ENUMERATED — not waved at

`gate_audit.py` reports **18 authored-at-sink** findings and **6 unresolved**. A count is
not a verdict, so here is every one, by class:

| class | count | sites | verdict |
|---|---|---|---|
| array-bounds / index guards (`0 <= rr < H`, `lab[r,c] >= 0`) | 6 | 112, 120×3, 290×2 | **not decisions** — geometry of an array, the §13 gate's own documented false-positive direction |
| emptiness guards (`counts > 0`, `sp > 0`, `p95 > 0`, `noise_amp > 0`, `fld > 0`) | 8 | 139, 145, 164, 292, 293, 448, 451×2 | **not thresholds** — divide-by-zero and empty-population guards |
| `np.clip(..., 0, k-1)` | 1 | 83 | **the incumbent quantizer, reproduced verbatim** from `peer_competition_measure.quantize`; the bound is the alphabet's own size |
| `bg < 0.5` | 1 | 260 | reading the **substrate's own 0/1 flag** — the identical idiom the border-ownership seed's own AST audit records as a boolean discriminator, not a threshold |
| `tau` (resolves to literal 0) | 1 | 121 | **a declared SWEEP AXIS** (`TAU_LADDER`), reported in full; the default is the incumbent's own exact equality |
| `ratios > 1.0` | 1 | 457 | a ratio of **like quantities** (spread ÷ step): 1 is the identity, not a level. **And nothing branches on it** — it is a reported statistic; the decision is read off the whole T-curve |

**No measured quantity in this rung is compared against a chosen number to decide
anything.** The sweep ladders and the target curve are axes; every one is reported in
full; no level was selected after seeing an outcome.

`scripts/grouping_ceiling_enclosure_check.py` (the POST-HOC arm) audits at **3 authored,
0 unresolved**: `max(1, big)` (a divide-by-zero guard) and **`x >= TARGET` ×2, where
`TARGET = 60`** — flagged correctly by the reachability checker, since it is a
name-bound literal at a comparison. It is **the brief's own target size and ONE POINT of
the pre-registered T-curve** in §2.3, reported as a count rather than used to decide
anything; the curve itself is monotone with no knee, so the finding does not turn on
which point is read. **Recorded here rather than exempted** — the audit is right that a
name is not a hiding place, and the defence has to be what the number IS, not what it is
called.

---

## 6. WHAT I GOT WRONG — in full

### 6.1 THE BIG ONE: **M0 PASSED WHILE THE SWEEP WAS MEASURING SOMETHING ELSE**

The pipeline quantizes **per frame** (min/max over the whole 72×72) and **then** cuts
tiles. My first sweep quantized **each 18×18 tile against its own min/max**. That is a
different, more permissive representation, and it inflated C1's enclosed component count
**5047 → 6331 (+25%)** and every downstream distribution with it.

**The reconciliation did not catch it, because the reconciliation used the correct path.**
M0 booted the substrate on per-frame-quantized tiles and agreed 32/32; the sweep, in a
different function, quantized differently. **I verified the PRODUCER and reported it as
verifying the PRODUCT — the exact failure the brief names, committed by the agent who had
just read the warning.** I found it only because I cross-checked the enclosed-component
total against the peer rung's published 5047 and it did not match.

The fix is structural, not a patch: `sweep_fields` now takes a **callback** that owns the
quantization, so the reconciliation path and the sweep path are the same path, and the
published floor is **asserted in-run** so the run voids rather than reports. **No number
from the first version appears anywhere in this document.**

### 6.2 P4 WAS WRONG — AND SO WAS MY FIRST READING OF *WHY*, WHICH I NEARLY PUBLISHED

I predicted the aperture was innocent — *"a field of singletons is not being cut by
anything."* Wrong: the ≥60-cell mass among **enclosed** cells is 0.6% tiled vs 20.5%
whole (C1) and 0.0% vs 25.5% (C2). **I predicted it in the direction that would have let
me skip measuring it; had I dropped M4 as uninformative, as my own prediction argued, the
rung would have reported a clean, confident, materially incomplete negative.**

**And then I got the explanation wrong too.** I wrote §3 as *"the aperture destroys the
large regions — 33×"*, with the enclosure confound noted as a caveat. Running the
caveat's own number showed the flood produces the **same** count of ≥60-cell regions at
both grains (86 vs 94; **111 vs 83**, i.e. tiled produces MORE on C2). **Roughly 90% of
my 33× was the enclosure predicate's definition, not fragmentation** — a caveat I had
written down and not quantified, which is the same failure as §6.1 in a different
costume: I noted the risk and then reasoned as though I had checked it. The corrected
version is a better finding than the one I nearly published, and I got it by measuring my
own caveat rather than by reasoning about it.

**And the framing it corrects is not only mine.** *"The components ARE the fragments"* is
true of the **enclosed** components and **false of the flood's output**: at `k=16` the
typical tile cell lives in a **21–23 cell** region and a quarter to a third of all cells
are in a ≥60-cell component. That distinction was available in every prior rung's data
and nobody, including me until the cross-check, had separated the two populations.

### 6.3 MY CONTROL LADDER STRADDLED THE LIMIT IT EXISTED TO MEASURE

Control 3's pre-registered rungs were `0, 0.125, 0.25, …`. The analytic limit is `1/k`
= **0.0625**, so the control read `20/20` then `0/20` with nothing in between and could
locate the limit only to *"somewhere below 0.125"*. I added a finer sub-ladder,
**marked POST-HOC in the data (`prereg: false`) and here**. It rescues no failure — it
makes my own instrument's limit sharper against me, which §5 permits and §1 demands —
but I should have derived the expected limit before choosing the ladder, and the
derivation was available before any measurement.

### 6.4 P1 WAS RIGHT FOR A WEAKER REASON THAN I GAVE

I predicted the front would be degenerate because it would **jump over** the target band.
It does not jump over it: the figure-side axis **barely moves at all** while the ground
axis traverses its full range. That is a stronger result than I predicted and it is a
**different shape** — I was reasoning about a percolation transition in one variable when
the real finding is that the two sides are nearly decoupled and only one of them
responds. Being right about the verdict while wrong about the shape is worth recording,
because the shape is what generalises.

### 6.5 P2 WAS RIGHT IN DIRECTION AND UNDERSTATED BY 3×

I predicted chained components would exceed 4× the admitted step at τ=1. Measured:
**11.9× (C1) / 12.7× (C2)** at the maximum, p99 8×. The direction was the bet and it
held; the magnitude is what makes chaining the *decisive* rather than *contributing*
mechanism, and I did not predict it.

### 6.6 I DECLARED IN ADVANCE THAT P1, P3 AND P5 WERE ONE BET — WHICH LIMITS THEM

They are three readings of *"the material is not piecewise-constant at object scale"* and
cannot independently confirm each other. What carries §4 is not their agreement but §2.3's
closure in the mechanism's own parameter (`k_req` vs `giant` at that `k`), which is a
single self-contained contradiction, and §2.2's exposure-checked immobility.

### 6.7 A THIN POPULATION I ALMOST QUOTED AS A RATE

C1 at `k=2` shows `fraction of enclosed cells in components ≥ 60` = **0.2151**, which
reads like the target being reached. It is **two components out of 140**, over a total
enclosed population of ~595 cells. It is reported in the table with its exposure and it
is **not** evidence of a window; I flag it because a reader skimming the column would
reasonably think otherwise.

---

## 7. SEEDS — 103000–103999

**Measured. `unknown_sinks: 1`, disclosed and hand-resolved; none outside the block.**

| seed(s) | consumed by | status |
|---|---|---|
| **103000–103099** | `controls`/`speckle` — 100 iid uniform fields (control 1) | **BURNED** |
| **103000** | the bootstrap resampler `default_rng` | **BURNED** (same integer, distinct sink) |
| **103100** | graded-exemplar noise draws (control 3) | **BURNED** |
| 103101–103999 | not drawn | **CLEAN** |

```
$ python3 scripts/seed_audit.py --check 103000 103999 scripts/grouping_ceiling_measure.py
{"declared": [103000, 103999], "ok": true, "outside": []}
   unknown_sinks: 1
```

**THE ONE UNKNOWN SINK IS NAMED, NOT ROUNDED AWAY.** Line 499,
`np.random.RandomState(SEED_SPECKLE_BASE + i)` inside a comprehension: the static
analyser cannot resolve `base + i` and reports the sink's seeds as `null`. Read from
source, it draws exactly `103000…103099`, inside the declared block. **A check that
passes with an unresolved sink has verified less than it appears to** — this rung's
predecessor recorded that lesson and it applies here, to one site.

The verbatim `check_claim` output for 103000–103999, **including its 497 tree-wide
unresolved sinks and both caveats**, is in PREREG §0.1.

---

## 8. SCOPE — WHAT IS NOT SHOWN (§8)

- **ONE GRAIN for the primary front.** G72, `REGION=18`, two corpora, 7 frames × 16
  tiles. §3 shows the aperture matters, so **the immobility claim is specific to this
  grain** — and that is precisely why §3 is reported as the rung's lead.
- **The whole-frame arm has an enclosure confound** (§3). Nothing here says its large
  components are objects.
- **VALUE ONLY.** The family tested is quantizer coarseness and chaining tolerance on
  luminance. Motion, contour, ownership and learned appearance are untested here and are
  not covered by this negative.
- **The components are computed OUTSIDE the graph.** They are reconciled against it
  32/32 per corpus at the incumbent `k` and against the published totals at `k=16`, but
  the sweep's other 17 arms were never run through the substrate — no rule exists that
  behaves that way. **They are a characterisation of the relation, not a measurement of
  a mechanism.**
- **No mechanism was built, so no mechanism is validated.** There is no injection
  control and no `§13` seed audit in this rung because there is no conjunct to gate.
- **The speckle control is uniform iid.** It is the random-input floor, not a model of
  sensor noise.
- **No claim about proto-objects downstream.** This rung stops at the component field.
  Minting is a selection over it; that inheritance was established by the peer rung and
  is not re-measured here.

---

## 9. LEDGER ROW (carried here — `VISION_PROTOCOL.md` NOT edited)

| **103000–103999 (103000–103100 measured; `unknown_sinks: 1`, hand-resolved to 103000–103099; none outside block)** | **THE GROUPING CEILING — EVERY RELAXATION OF ADMISSIBILITY IS SPENT ON THE GROUND; THE FIGURE-SIDE DISTRIBUTION IS IMMOBILE ACROSS THE WHOLE FAMILY. NO MECHANISM WARRANTED, AND THE RUNG BUILDS NOTHING.** Instructed to characterise before building. **18 ADMISSIBILITY RELATIONS — 11 QUANTIZER COARSENESSES OVER 5 OCTAVES (k=2…64) × 7 CHAINING TOLERANCES (τ=0…8), 112 tiles/corpus: the GIANT COMPONENT traverses its ENTIRE range (C1 0.116→1.000, C2 0.066→1.000) and components/tile move 141×/151×, while the ENCLOSED median size stays 1–2, the enclosed MEAN spans only 2.6×/3.0×, THE TYPICAL ENCLOSED CELL'S REGION NEVER EXCEEDS 10 CELLS, and the LARGEST ENCLOSED COMPONENT ANYWHERE IS ≤23% OF A TILE AT EVERY ARM.** The pre-registered front does not jump over the target band — **the figure axis never enters the plane; the two sides are nearly DECOUPLED and only the ground responds** (P1 right on the verdict, WRONG ON THE SHAPE, and the shape is what generalises). **THE MATERIAL CLOSES IT IN THE MECHANISM'S OWN UNITS: control 3 shows the resolving limit FALLS OUT at exactly ONE QUANTIZER BIN (recovery 20/20 up to spread/contrast = 1/16 = 0.0625, 0/20 at 3/32 — no constant chosen), and a 60-cell natural neighbourhood's internal spread is 114.05/79.56 = 0.456/0.336 OF THE DYNAMIC RANGE, i.e. 7.3×/5.4× that limit, and 1.886/1.901× the frame's OWN edge contrast (step p95) at 80.5%/76.8% of positions. THE k REQUIRED TO UNIFY A 60-CELL DISC IS 1.91/2.86 — FEWER THAN 3 LEVELS FOR THE WHOLE FRAME — AND AT k=2/3 THE GIANT ALREADY OWNS 60–79% OF THE TILE. THE MECHANISM IS SELF-CONTRADICTORY IN ITS OWN PARAMETER; the T-curve is monotone with no knee, so 60 is not special and even T=20 needs k≈3.6.** **H2 CONFIRMED AND DECISIVE: chaining, not tolerance, is the swallow — a component built from ONE-BIN steps spans up to 11.9×/12.7× the admitted step (94% of the dynamic range at τ=2), while BIN's vrange is one bin BY CONSTRUCTION. So BOTH ends of the family now have NAMED mechanisms: coarsening DISSOLVES figures into the ground, chaining WALKS the ground into the figures. Neither is repairable by a parameter.** **CONTROLS: ideal exemplar found EXACTLY at all 6 targets × all 11 k; random-input floor RAN and natural structure is REAL (enclosed mean 2.06/2.27 vs speckle 1.13; max 66/50 vs 6) AND CHANGES NOTHING ABOUT THE FRONT'S SHAPE (speckle enclosed median 1 at all 18 arms while its giant runs 0.006→0.983) — and NATURAL FRAMES PERCOLATE EARLIER THAN NOISE (τ=2–3 vs τ=6): the material's smoothness works AGAINST this mechanism. EMPTY ARMS ARE MARKED EMPTY, never reported as nulls (C1 enclosed 5047→140→2→0; C2→0 at τ≥4).** **THE PREDICTION THAT BROKE IS THE LEAD, AND THE FINDING THAT OUTRANKS THE HEADLINE IS POST-HOC AND LABELLED SO THROUGHOUT: THE FLOOD IS NOT FRAGMENTING — ENCLOSURE IS DISCARDING.** P4 said the aperture was innocent and it is not (fraction of ENCLOSED cells in ≥60-cell components 0.0063 tiled vs 0.2050 whole on C1; 0.0000 vs 0.2546 on C2; max enclosed 66→275 and 50→736). **BUT MY FIRST READING — "the aperture FRAGMENTS large regions, 33×" — IS WRONG, AND THE MEASUREMENT THAT KILLED IT IS THE CONFOUND MY OWN PREREG HAD FLAGGED AND I HAD ONLY REASONED ABOUT: THE FLOOD PRODUCES THE SAME NUMBER OF ≥60-CELL REGIONS AT BOTH GRAINS (C1 86 tiled vs 94 whole; C2 111 vs 83 — THE TILED FIELD PRODUCES MORE), AND WHAT CHANGES 34–37× IS THE SHARE SURVIVING `bo_bgflood`'s ENCLOSURE TEST: 1.2%/0.0% TILED vs 44.7%/41.0% WHOLE.** The mechanism is COMPUTED, not fitted: a 61-cell disc clears an 18×18 border from 19.75% of centre positions against 74.15% of a 72×72 frame's. **`bo_bgflood` ENCODES "DOES NOT TOUCH THE WINDOW" AS "IS A FIGURE", AND A WINDOW EDGE IS NOT A SCENE BOUNDARY — the value-flood rung's own `G_figadj` diagnosis (ISOLATION standing in for OBJECTHOOD, validated only where the two coincide) ONE RULE EARLIER IN THE SAME PIPELINE.** **AND IT CORRECTS A FRAMING THE WHOLE ARC HAS CARRIED: "the components ARE the fragments" is true of the ENCLOSED components and FALSE of the FLOOD'S OUTPUT — at k=16 the typical TILE CELL lives in a 21–23 CELL region and a quarter to a third of all cells are in a ≥60-cell component.** Reported as an OBSERVATION, NOT this rung's earned result: it is post-hoc (§5), it does NOT show those components are objects, and removing the aperture makes enclosure NON-SELECTIVE (60%+ of the field becomes "enclosed") — its own unpriced failure mode. Its script is committed separately and labelled POST-HOC in its docstring; starting from it requires a prospective prereg. **WHAT IT GOT WRONG: M0 PASSED WHILE THE SWEEP MEASURED SOMETHING ELSE — the first version quantized PER TILE instead of PER FRAME, inflating C1's enclosed count 5047→6331, and the reconciliation did not catch it BECAUSE THE RECONCILIATION USED THE CORRECT PATH: I VERIFIED THE PRODUCER AND REPORTED IT AS VERIFYING THE PRODUCT, the exact failure the brief names, committed after reading the warning. Found only by cross-checking the peer rung's published 5047; fixed STRUCTURALLY (the sweep now takes a callback owning the quantization, so both paths are one path) and the published floor is ASSERTED IN-RUN so the run VOIDS rather than reports; NO NUMBER FROM THE FIRST VERSION APPEARS. P4 wrong in the direction that would have let me DROP the arm that produced the rung's only real lead. MY CONTROL LADDER STRADDLED THE LIMIT IT EXISTED TO MEASURE (0 then 0.125 around 1/k=0.0625) — refined POST-HOC and marked as such in the data. P2 right in direction, UNDERSTATED 3× (predicted >4×, measured 11.9×). P1/P3/P5 DECLARED IN ADVANCE as one bet, which limits rather than rescues them. **I NOTED THE ENCLOSURE CONFOUND AND THEN REASONED AS THOUGH I HAD CHECKED IT — the same failure as the M0 defect in a different costume, twice in one rung; ~90% of my headline 33× was definitional.** AND A THIN POPULATION I NEARLY QUOTED AS A RATE: C1 k=2's "21.5% of enclosed cells in ≥60-cell components" is TWO COMPONENTS OUT OF 140.** **FLOORS RE-EARNED IN-TREE, NOTHING INHERITED: oracle 222/0 BEFORE AND AFTER; provenance its own step 7 passed FIRST; M0 partition ≡ the graph's `glabel` 32/32 and enclosed ≡ `bg` 32/32 on BOTH corpora; the peer rung's published enclosed totals 5047/3978 reproduced EXACTLY and asserted in-run.** §9 trivial: `git diff -- seeds/ runners/` EMPTY; no Rust, no seed, no rule, no flag. §13 gate_audit run with ALL 18 SINKS ENUMERATED ONE AT A TIME (bounds guards, emptiness guards, the incumbent quantizer's own alphabet size, the substrate's 0/1 bg flag, the declared sweep axis, and a ratio of LIKE QUANTITIES whose 1 is an identity and on which nothing branches). **NAMED NEXT LEVER, NOT STARTED: the value domain is CLOSED — this negative covers quantizer coarseness and chaining tolerance on luminance ONLY and says NOTHING about motion, contour, ownership or learned appearance grouping. The aperture is a LEAD WITH A CONFOUND, not a result.** |
