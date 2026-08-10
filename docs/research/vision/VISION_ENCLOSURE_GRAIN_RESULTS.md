# ENCLOSURE × GRAIN — RESULTS: **THE APERTURE IS NOT THE BLOCKER EITHER. `bo_bgflood` IS NOT COMPUTING WINDOW-FIT — I PREDICTED IT WAS AND THE STRUCTURELESS CONTROL REFUTED ME. ENCLOSURE HAS ONE DEGREE OF FREEDOM AND IT TRADES SELECTIVITY AGAINST SIZE ONE-FOR-ONE; THE ENCLOSED MEDIAN IS 1 AT EVERY GRAIN FROM 3 TO 72.**

*Pre-registration `VISION_ENCLOSURE_GRAIN_PREREG.md`, committed **`dd3e6907`** BEFORE any
number. Nothing in it was edited after the first number. This rung reports its
pre-registered **OUTCOME N (NEITHER)** and **builds nothing.***

**ENGINE PROVENANCE (§10)** — printed from **inside** the measuring process into
`results/enclosure_grain.json` and `results/enclosure_grain.log`, **and re-verified after
the measurement**:

```
engine d657468d9e1f @ <this worktree>/runners/dsl/python/substrate_rs/_native.abi3.so
  [1 other tree build(s) shadowed]
```

`provenance == provenance_after`: **True** (asserted in the artifact, not inferred).
Branch `worktree-agent-a76ecc2f02ccbfe32`. **Every number in this document was measured at
`dd3e6907` (the prereg commit), whose base was `main` at `8f41cc2a`.** `main` has since
advanced to `85401476` **underneath this rung, mid-measurement** — recorded rather than
elided (§11 rule 5: *long-running measurement is not a lock*); nothing here was re-measured
against it, and the engine hash below is what actually produced the numbers. Engine built
in-tree by `scripts/engine_build.sh` (**`own`**); **no Rust
change in this rung**. Migrated provenance gate run as **its own step, first: 7 passed**.
`data/` is a symlink to canonical (§10.2), never a copy. Corpus pins asserted at run
time: C1 `08630d4b`, C2 `119eca43`.

**LOAD (recorded with every measurement, per the CPU directive).** `os.getloadavg()` is
written into both artifacts on every row. Main run: start `[4.84, 3.67, 4.26]`, end
`[6.27, 4.64, 4.56]`, **114.7 s total**. Contact run: start `[5.77, 5.11, 4.76]`, end
`[6.03, 5.22, 4.80]`, 18.9 s. **At most one worker at a time; no wall-clock cutoff is
used as a verdict anywhere in this rung.**

---

## 1. THE HEADLINE

**Two rungs eliminated the mint and the flood. This one eliminates the APERTURE — by the
same test, and the test is the size distribution.**

| | C1 tile `L=18` | C1 whole `L=72` | C2 tile | C2 whole |
|---|---|---|---|---|
| enclosed components (30 frames) | 21 812 | 28 391 | 16 176 | 21 552 |
| **enclosed size, MEDIAN** | **1** | **1** | **1** | **1** |
| enclosed size, mean | 2.01 | 3.48 | 2.33 | 4.43 |
| enclosed size, max | 67 | 426 | 82 | 736 |
| the region a typical ENCLOSED cell lives in | 2 | 12 | 3 | 13 |

**Removing the aperture entirely — going from an 18×18 window to the whole 72×72 frame,
a 16× area change — moves the enclosed-component count +30% and moves the MEDIAN 1 → 1.**
By the brief's own standing instruction, that is fragments more slowly. It is the third
time this arc has run that test and the third time the answer has been the same:

| lever | count moved | **median moved** |
|---|---|---|
| lifting the ENTIRE peer competition | +47% / +33% | **1 → 1** |
| the whole value-admissibility family (18 relations, 5 octaves) | 141× / 151× | **1 → 1–2** |
| **removing the APERTURE (this rung, 12 grains, 1 → 72)** | **+30% / +33%** | **1 → 1** |

### AND THE PREDICTION THAT BROKE IS THE LEAD

I pre-registered (P1) that `bo_bgflood` computes **window-fit** — that observed enclosure
would track a computed geometric null, because the predicate *is* a reachability test to
the window edge. **That is wrong, and the control that killed it is the structureless
one.**

| obs/null, band 4–7 cells, [95% CI over frames] | speckle (structureless) | C1 | C2 |
|---|---|---|---|
| `L=18` | **0.992 [0.966, 1.017]** | **0.668 [0.635, 0.702]** | **0.634 [0.610, 0.656]** |
| `L=72` | **1.005 [0.992, 1.016]** | 0.918 [0.908, 0.926] | 0.939 [0.913, 0.960] |

**On structureless input the observed enclosure rate equals the geometric null to within
1%, at every grain and every band the speckle reaches.** That is the null's positive
control, and it passed *on real measured data* rather than on a construction. **Natural
frames depart from it massively and the departure is CI-separated at every grain.**

**So `bo_bgflood` is reading real structure, not aperture geometry.** What it reads is
size-graded and it is present at **every** grain, including the whole frame:

| obs/null by component size, C1 | 1 | 2–3 | 4–7 | 8–15 | 16–31 | 32–63 | 64–127 | 128–255 | 256–511 |
|---|---|---|---|---|---|---|---|---|---|
| `L=18` | 0.95 | 0.83 | 0.67 | 0.40 | 0.27 | 0.19 | **0.04** | **0.00** | — |
| `L=72` | 1.03 | 0.99 | 0.92 | 0.82 | 0.74 | 0.69 | **0.49** | **0.44** | **0.43** |

**In a natural frame, the larger an equal-value region is, the more certainly it reaches
the picture edge — far beyond what its own extent requires.** The enclosure predicate is
reporting that correctly. That is why it cannot yield a large figure: **at every scale,
the large equal-value regions that exist are the ones that run off the edge.**

---

## 2. THE ENCLOSURE CHARACTERISATION — FIRST, AS THE BRIEF REQUIRED

### 2.0 THE INSTRUMENT, RECONCILED FIRST — AT EIGHT GRAINS, NOT ONE

The claim spans grains, so the instrument is reconciled across grains. Live fields put
through the **substrate** (`boot_core` + `vision_border_ownership`, `bown=1`), numpy
partition checked against the graph's `glabel` and numpy enclosure against the graph's
own `bg` flag, cell by cell:

| grain `L` | 4 | 6 | 8 | 9 | 12 | 18 | 24 | 36 |
|---|---|---|---|---|---|---|---|---|
| **partition ≡ `glabel`** (C1 / C2) | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 | **4/4** |
| **enclosed ≡ `bg`** (C1 / C2) | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 | 6/6 | **4/4** |

**Total agreement, both corpora, every reconciled grain.** `L=1,2,3` are degenerate (no
interior) and `L=72` was not put through the substrate — **which grains were reached is
reported, not assumed**, and the numpy read-out is the same function at every grain.

And the published floors, re-earned **on this rung's own code path** and **asserted
in-run** (the run raises rather than reports):

| | C1 | C2 |
|---|---|---|
| enclosed components, G72 / `REGION=18` / `k=16` / the published 7 frames | **5047** | **3978** |
| peer-competition + grouping-ceiling rungs, published | **5047** | **3978** |

The grouping-ceiling rung's **post-hoc cross-check reproduces to the unit, all four
cells**:

| ≥60-cell components, 7 frames | C1 tile | C1 whole | C2 tile | C2 whole |
|---|---|---|---|---|
| produced / enclosed, **this rung** | **86 / 1** | **94 / 42** | **111 / 0** | **83 / 34** |
| published | 86 / 1 | 94 / 42 | 111 / 0 | 83 / 34 |

### 2.1 THE GRAIN LADDER IS AN ENUMERATION

Every divisor of the standing `GRID = 72`: **1, 2, 3, 4, 6, 8, 9, 12, 18, 24, 36, 72** —
the complete set of windows that exactly tile the standing frame. **No grain is selected.**
All twelve are reported, including the degenerate ones, whose behaviour falls out of the
predicate rather than being chosen (`L≤2`: every cell is a border cell, so **nothing is
ever enclosed** — 0 of 155 520 components; `L=3`: only the centre cell can be, and the
enclosed max is exactly 1).

### 2.2 WHAT ENCLOSURE DOES AT EACH GRAIN — the full front, 30 frames per corpus

**C1 (cartoon):**

| `L` | comps | enclosed | **pass rate** | enc cell frac | ALL med / mean / max | **ENC med / mean / max** | typical enc cell's region | ground comps/frame | largest ground / field |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 155 520 | 0 | 0.000 | 0.0000 | 1 / 1.0 / 1 | *(empty)* | — | 5184.0 | 1.000 |
| 2 | 77 152 | 0 | 0.000 | 0.0000 | 2 / 2.0 / 4 | *(empty)* | — | 2571.7 | 1.000 |
| 3 | 57 955 | 2 144 | 0.037 | 0.0138 | 2 / 2.7 / 9 | **1 / 1.0 / 1** | 1 | 1860.4 | 1.000 |
| 4 | 49 259 | 5 125 | 0.104 | 0.0378 | 1 / 3.2 / 16 | **1 / 1.15 / 4** | 1 | 1471.1 | 1.000 |
| 6 | 42 009 | 10 523 | 0.250 | 0.0888 | 1 / 3.7 / 36 | **1 / 1.31 / 9** | 1 | 1049.5 | 1.000 |
| 8 | 38 654 | 13 816 | 0.357 | 0.1309 | 1 / 4.0 / 64 | **1 / 1.47 / 15** | 1 | 827.9 | 0.996 |
| 9 | 37 493 | 15 399 | 0.411 | 0.1508 | 1 / 4.1 / 81 | **1 / 1.52 / 24** | 2 | 736.5 | 0.990 |
| 12 | 35 501 | 18 019 | 0.508 | 0.1932 | 1 / 4.4 / 144 | **1 / 1.67 / 36** | 2 | 582.7 | 0.938 |
| **18 (incumbent)** | 33 573 | 21 812 | 0.650 | 0.2815 | 1 / 4.6 / 289 | **1 / 2.01 / 67** | **2** | 392.0 | 0.601 |
| 24 | 32 504 | 22 974 | 0.707 | 0.3447 | 1 / 4.8 / 344 | **1 / 2.33 / 153** | 3 | 317.7 | 0.451 |
| 36 | 31 493 | 26 201 | 0.832 | 0.4512 | 1 / 4.9 / 488 | **1 / 2.68 / 290** | 5 | 176.4 | 0.267 |
| **72 (whole frame)** | 30 586 | 28 391 | **0.928** | **0.6356** | 1 / 5.1 / 622 | **1 / 3.48 / 426** | **12** | 73.2 | 0.082 |

**C2 (live-action):** same shape throughout — pass rate 0.080 → 0.899, enc cell frac
0.0267 → 0.6141, **enclosed median 1 at every grain**, enclosed mean 1.15 → 4.43, enclosed
max 4 → 736, typical enclosed cell's region 1 → 13, ground comps/frame 1380.7 → 80.8,
largest ground / field 1.000 → 0.078.

**Three facts fall out of this table and none of them is about the aperture:**

1. **THE COMPONENT COUNT IS NEARLY GRAIN-INVARIANT.** 33 573 → 30 586 across a **16× area
   change per window** — a **9%** difference. Tiling adds ~9% more components by cutting
   the few that straddle a boundary. **This generalises the grouping-ceiling rung's
   "the flood is not fragmenting" from one grain pair to the whole ladder.**
2. **THE ALL-COMPONENT DISTRIBUTION BARELY MOVES EITHER.** Median 1 at every `L≥4`; mean
   4.6 → 5.1. What *does* move is the tail: max 16 → 622.
3. **THE ENCLOSED MEDIAN IS 1 AT EVERY GRAIN FROM 3 TO 72.** Nothing in the aperture axis
   touches it.

### 2.3 THE ONE DEGREE OF FREEDOM — selectivity traded against size, one-for-one

| C1 `L` | 4 | 6 | 8 | 9 | 12 | **18** | 24 | 36 | **72** |
|---|---|---|---|---|---|---|---|---|---|
| **pass rate** (share of components enclosed) | 0.104 | 0.250 | 0.357 | 0.411 | 0.508 | **0.650** | 0.707 | 0.832 | **0.928** |
| **≥60-cell survival** | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | **0.008** | 0.065 | 0.135 | **0.436** |
| **enclosed median** | **1** | **1** | **1** | **1** | **1** | **1** | **1** | **1** | **1** |

C2 is identical in shape (pass rate 0.080 → 0.899; ≥60 survival 0.000 → 0.393; median 1
throughout).

**Both axes are monotone in `L` and they move together. There is no grain at which
enclosure is both selective and size-permissive, because they are the same axis.**
**P3 CONFIRMED.** At the tile grain the predicate is selective (35% of components pass)
and discards precisely the large ones (0% of ≥60-cell regions); at the whole frame it
keeps the large ones (44%) and has stopped selecting at all (93% of components, 64% of
cells pass). The curve between them is monotone with **no knee**.

**This is structurally the same finding the grouping-ceiling rung reported about the value
family — "ONE degree of freedom, and it moves the BACKGROUND" — arrived at from a wholly
independent axis.** Two families, two rungs, one shape.

### 2.4 WHAT ENCLOSURE CALLS GROUND — **P5 REFUTED**

I predicted (P5) that at whole-frame grain the ground would be **one giant component**, so
that "enclosed" would mean "not part of the single largest connected equal-value region".
**It is not.** At `L=72` the ground is **73.2 (C1) / 80.8 (C2) components per frame**, and
**the largest of them holds only 8.2% / 7.8% of the field.**

Ground is not a background. **It is the frame ring's own neighbourhood**: whatever
equal-value regions happen to abut the 284-cell border. That is a fact about the predicate
at *every* grain — at `L=18` the largest ground component holds 60% of the tile, at `L=72`
it holds 8% — and the difference is simply that the ring is a larger *share* of a small
window.

---

## 3. THE DIAGNOSIS — **PRE-REGISTERED OUTCOME N: NEITHER**

§5 of the pre-registration fixed three verdicts before the numbers existed. The numbers
select **N**, and both of the other two are excluded by measurement:

- **NOT OUTCOME P (the predicate is wrong because it computes window-fit).** Excluded:
  on structureless input observed enclosure equals the null to within 1% at every grain,
  and natural frames depart from it by up to 25×, CI-separated everywhere. The predicate
  reads real structure.
- **NOT OUTCOME G (the predicate is right and the grain is wrong).** Excluded: the
  departure from the null is **size-graded at every grain including the whole frame**
  (`L=72`, band 64–127: 0.49), never size-independent; and the enclosed median is 1 at
  all twelve grains while the enclosed-cell fraction runs 0.00 → 0.64. There is no grain
  at which the predicate is both selective and size-preserving.

**⇒ WHAT ACTUALLY GATES IT, NAMED.** The enclosed-size distribution is pinned at median 1
**before enclosure sees it**, and enclosure cannot unpin it at any grain:

1. **The component field is median-1 at every grain** (all-components median 1 for every
   `L≥4`), and its count is grain-invariant to 9%. Enclosure is a *selection over* that
   field, exactly as minting is a selection over the enclosed set. **The peer rung's
   ceiling argument applies one rule earlier and survives the removal of the aperture.**
2. **Size and border-reachability are confounded IN THE MATERIAL, not in the predicate.**
   A natural equal-value region large enough to be an object is, with high probability,
   background — and background does run off the edge of a picture. The 25× departure from
   the geometric null *is* that confound, measured. The grouping-ceiling rung closed this
   from the other side, in the flood's own units: a 60-cell natural neighbourhood's
   internal spread is 5–7× the exact-value flood's resolving limit. **A region big enough
   to be an object is either not equal-valued, or it is the ground.**
3. **Therefore the aperture is not a free parameter that was mis-set.** `REGION=18` was
   adopted on statistical grounds and is load-bearing in three rungs' results — and this
   rung measures that **every** setting of it lands on the same one-dimensional curve.
   The 1.2% → 44.7% figure is real and its causal reading is **not** "the window edge is
   not a scene boundary" but "the predicate stops selecting."

**NO MECHANISM IS WARRANTED, AND NONE IS BUILT.** This rung adds no rule, no flag, no
node, no seed byte and no Rust. §5's build condition (OUTCOME G) was not met, and the
diagnostic that decided it cost 115 seconds — which is the fourth consecutive rung on
which the cheap diagnostic has ended the mechanism before it was written.

---

## 4. THE POST-HOC CROSS-CHECK — **BOTH DISEASES ARE REAL, AT OPPOSITE GRAINS, AND NEITHER IS THE BLOCKER**

***POST-HOC.*** *Not one of the pre-registered statistics. It extends PREREG M1's
"what enclosure calls background" line with the one quantity that separates the two live
readings of §1, and it is labelled POST-HOC in its script's docstring, in the artifact
(`"POST_HOC": true`) and here. §5 forbids me from treating it as this rung's earned
result.*

Two readings survived §1, with different next rungs: **(A)** large ground regions are
genuinely background — they run off the picture on a long stretch of more than one side;
**(B)** they are *brushing* the edge, the value-flood rung's recorded disease (*"the gate
lets ONE touching cell veto an entire component"*, the inversion of *"a circle with a bit
out isn't a discontinuous circle"*). The discriminator is contact measured **relative to
the component's own outline** — a ratio of like quantities, so no absolute length is
chosen.

| large GROUND components | band | n | contact (median cells) | sides touched (median) | **share of its own outline that is picture edge** |
|---|---|---|---|---|---|
| C1 `L=12` | 128–255 | 36 | 42.5 | **4** | **0.808** |
| C1 `L=18` | 128–255 | 96 | 21.0 | 3 | **0.409** |
| C1 `L=18` | 256–511 | 6 | 51.0 | **4** | **0.718** |
| C1 `L=72` | 512–1023 | 13 | 19.0 | 3 | **0.089** |
| C2 `L=36` | 256–511 | 35 | 10.0 | 1 | **0.061** |
| C2 `L=72` | 256–511 | 52 | 6.0 | 1 | **0.038** |
| C2 `L=72` | 512–1023 | 8 | 2.5 | **1** | **0.007** |

**Both are true, at opposite ends of the ladder, and that is why the trade-off in §2.3 is
a trade-off:**

- **At tile grain a large "ground" component IS mostly the window frame.** At `L=12` a
  128–255-cell ground region touches **all four sides** and **81% of its own outline is
  the picture edge**. Reading A holds trivially there because the "background" it finds is
  the aperture's own neighbourhood — not a scene.
- **At whole-frame grain the biggest regions are vetoed by a brush.** On C2 at `L=72` a
  512+-cell region is declared ground on a median of **2.5 contact cells = 0.7% of its own
  outline**, touching **one** side; one of those eight is vetoed by a **single cell**.
  Reading B holds there, and it is the recorded disease exactly.

**AND FIXING IT IS WORTH ALMOST NOTHING**, which is why this is reported as a
characterisation and not as a lead. The population a contact-extent conjunct could rescue
is **13 (C1) and 8 (C2) components in 30 frames** at `L=72`. The enclosed median at that
grain is already 1 with 28 391 components; rescuing eight of them moves nothing. **The
cheap diagnostic applied to my own would-be mechanism killed it before I wrote a line of
it** — which is the instruction, taken as an instruction.

---

## 5. GATES — EVERY FLOOR RE-EARNED IN THIS TREE, ON THIS ENGINE, NOTHING INHERITED

| gate | result |
|---|---|
| **Oracle** `bash scripts/rung7_vision_bench.sh`, **before** | **222 passed / 0 failed** (with `data/`) |
| **Oracle, after** | **222 passed / 0 failed** |
| Provenance gate, its own step, **first** | **7 passed** |
| **Engine fingerprint re-verified AFTER the measurement** | `d657468d9e1f`, **identical**; `provenance == provenance_after` asserted in the artifact |
| **M0 partition ≡ the graph's `glabel`** | **total agreement at 8 grains, both corpora** |
| **M0 enclosed ≡ the graph's `bg`** | **total agreement at 8 grains, both corpora** |
| **Published enclosed floor, asserted in-run (voids otherwise)** | **5047 / 3978 — exact** |
| **Predecessor's post-hoc cross-check, all four cells** | **86/1, 94/42, 111/0, 83/34 — exact** |
| Control: the null vs **brute-force enumeration** | **EXACT agreement at every (bbox, window) pair in the ladders** |
| Control: ideal disc SEEN at every grain that fits | **8/8**, and **LOST at the edge 8/8** |
| **Speckle floor, re-earned AT EVERY GRAIN** | **ran; 100 fields, seeds 108000–108099** |
| §13 `scripts/gate_audit.py` | **run; all 11 authored + 18 unresolved sinks enumerated one at a time below** |
| §13 injection positive control, **landing verified in the REGION** | **5/5 landed; gate bites 3/5; BLIND 2/5 — §5.2** |
| Seed audit | **`ok: true`, none outside block, `unknown_sinks: 1` — named and hand-resolved, §7** |
| `python3 -m domains.seed_record --write` | **run; ledger regenerated** |
| **§9** | **`git diff -- seeds/ runners/` is EMPTY.** No Rust, no seed, no rule, no flag. Byte-identity by construction. |

**A gate safe to READ is not safe to RUN**: no other rung's confirmatory gate was executed
by this rung. The only benches run were the shared oracle and the provenance gate.

### 5.1 THE §13 AUDIT, ENUMERATED — every sink, by class

`gate_audit.py` reports **11 authored-at-sink** and **18 unresolved** across the two
measurement scripts. A count is not a verdict:

| class | count | sites | verdict |
|---|---|---|---|
| population-liveness guards (`counts > 0`, `contact[idx] > 0`) | 3 | m:128, c:98, c:101 | **not thresholds** — which labels have any cells; and `contact > 0` **IS `bo_bgflood`'s own definition of ground**, where 0 is the absence of contact, not a level |
| divide-by-zero / empty-population guards (`u.sum() <= 0`, `un > 0`) | 2 | m:218, m:223 | **not decisions** — the bootstrap denominator |
| array geometry (`r0 > 0`, `c0 > 0`) | 2 | m:310 ×2 | **not thresholds** — 0 is the array's first index; this pair IS the definition of the border ring in the brute-force enumerator |
| exactness assertion (`abs(f - b) > 0.0`) | 1 | m:336 | **the strictest possible comparison**, and it makes the control stricter against me (§5 permits, §1 demands) |
| arithmetic floor of a quantity (`r < 1`) | 1 | m:367 | a radius in cells; 1 is the smallest disc that exists, not a chosen size |
| running-max identity (`max(largest_gnd, … else 0)`) | 1 | m:187 | **a FALSE POSITIVE of the checker** — 0 is the identity of `max` over counts. See §5.2: same cause as the blindness |
| the substrate's own 0/1 flag (`bg < 0.5`) | 1 | m:410 | **reading the graph's boolean**, the identical idiom the border-ownership seed's own AST audit records as a discriminator; the grouping-ceiling rung recorded this same site |

**The 18 unresolved sinks, hand-resolved one at a time** — *a check that passes with
unresolved sinks has verified less than it appears to*:

- **10 + 3 are the declared LADDER variables** — `T` from `T_CURVE`, `lo`/`hi` from
  `BANDS` (m:249, 257, 258, 263, 265×2, 271, 272, 274, 275, 460; c:139, 141×2). The T
  curve is **reported in full at every grain** and the bands are the **dyadic
  enumeration**; no single value decides anything.
- **2 are the border-ring definition** (m:310, `r0 + bh - 1 < L - 1`): `L-1` is the last
  index of an `L`-wide array.
- **2 are the control disc's own equation** (m:371, 376): `(y-cy)² + (x-cx)² ≤ r²`.
- **1 is `size -> untraced`** at m:460 — a numpy array from the data, i.e. the legitimate
  side of the invariant (a MEASUREMENT, not an authored value).

### 5.2 THE INJECTION CONTROL FOUND A HOLE IN THE §13 CHECKER — reported, not fixed, not routed around

The control plants **five** spellings, not one — *six spellings felt like a pattern and
were a sample* — and every plant is re-selected **through the audit's own selector** (AST
identity) and asserted to lie inside the resolved span. The landing check is itself
positive-controlled: a **no-op** injection is asserted to FAIL it, and does.

```
[region] `frame_record` resolves BY AST IDENTITY to lines 167-202
  P1 measurement vs bare literal          lands@188 in-region=True  RED=True
  P2 measurement vs NAME-bound literal    lands@189 in-region=True  RED=True
  P3 comparison with no `if` at all       lands@188 in-region=True  RED=True
  P4 ACCUMULATOR vs bare literal          lands@188 in-region=True  RED=False   <-- MISS
  P5 ACCUMULATOR vs NAME-bound literal    lands@189 in-region=True  RED=False   <-- MISS
ALL FIVE PLANTS LANDED IN THE AUDITED REGION: True
GATE BITES on 3/5    GATE IS BLIND to 2/5
```

**THE DEFECT, DIAGNOSED.** `trace` resolves a **rebound** name to its **first** binding.
An ACCUMULATOR — `enc_cells = 0` then `enc_cells += <measured>` — therefore grades
`AUTHORED (-> literal 0)`. One cause, firing in **both** directions:

- **FALSE NEGATIVE.** In `enc_cells / ncell > 0.42` both operands are accumulators, so
  both sides grade AUTHORED and `audit_source`'s *"both sides authored ⇒ constant
  comparison, dead code"* branch **suppresses the sink entirely**. A genuine magic-number
  threshold on an accumulated quantity is **invisible to the flagship gate**, in both the
  bare-literal and the name-bound spelling.
- **FALSE POSITIVE.** The same fold reports `max(largest_gnd, …)` as
  `largest_gnd -> literal 0` (§5.1's seventh row), where `largest_gnd` is a running
  maximum.

**NOT FIXED HERE.** `scripts/gate_audit.py` is not this rung's file (§11 rule 4) — reported
for the supervisor to sequence. **And not routed around**: because the gate is
demonstrably blind to that spelling, the affected sites in this rung's own code are
**hand-audited** rather than leant on. Every accumulator in both scripts (`enc_cells`,
`gnd_cells`, `ncell`, `n_ground`, `largest_gnd`, `checked`, `ok_p`, `ok_e`, `tot`, `big`)
is either divided and **reported**, or compared **against another accumulator**. Three
sites the checker could not see, declared by hand:

- **`published_floor`: `if tot != want: raise`** — `want` is the predecessor's
  **published** 5047 / 3978. Reported in full because the gate saw *nothing* in this
  function. It is a number I did not choose, and the comparison exists to **VOID my own
  run** if I fail to reproduce it — a gate against myself, not a level that shapes an
  output.
- **`reconcile`: `partition_agree == checked == enclosed_agree and checked`** — a
  like-quantity total-agreement test plus a nonzero-exposure guard.
- **`contact_stats`: `(con[m] == 1).sum()` and `np.maximum(bnd, 1)`** — a reported count
  at the arithmetic floor of `contact` (a ground component has ≥1 ring cell **by
  definition**), and a divide-by-zero guard.

---

## 6. WHAT I GOT WRONG — in full

### 6.1 P1 REFUTED — and the instrument that refuted it was the control, not the data

I predicted `bo_bgflood` computes window-fit. It does not: on structureless input observed
enclosure matches the null to within 1%, and on natural frames it falls to **0.04** of the
null at `L=18`. **My own registered proviso named this exact escape** — *"if observed
survival falls below null for large components, that is real content and P1 is wrong in
the informative direction"* — and it is what happened. Writing the proviso is the only
reason I read the result correctly instead of reporting a 25× departure as instrument
noise.

**The uncomfortable part: had I skipped the speckle arm, I would have published P1.**
A 0.67 ratio on natural frames alone is easy to narrate as "roughly geometric." It is the
**0.99 on noise** that makes 0.67 a finding. The control was pre-registered as a *floor*
and turned out to be the *discriminator*.

### 6.2 P4 REFUTED, AND ITS SCOPE IS NARROWER THAN I WROTE

I predicted speckle would be indistinguishable from natural frames. It is CI-separated at
every grain. **But the speckle arm cannot speak above 8 cells** — iid uniform noise at
`k=16` produces a maximum component of **8 cells** in 100 fields at every grain. So the
structureless comparison is established for components of **≤7 cells** and is
**EXTRAPOLATED, not measured, above that** — precisely where the question lives. I did not
foresee this when I wrote M3 and the prereg does not mention it. *Eval-subset coverage is
part of every claim*, and this is mine.

### 6.3 P1, P3 AND P4 WERE NOT ONE BET, AND I DECLARED IN ADVANCE THAT THEY WERE

I registered them as three readings of one hypothesis, to limit them. **They split**: P3
confirmed, P1 and P4 refuted, consistently with each other. So my coupling claim was
**wrong about P3** — it is a statement about the grain axis, not about the null, and it
stands on its own evidence. Declaring a coupling that does not exist understates
independent evidence; it is the opposite error from the one the declaration protects
against, and it is still an error.

### 6.4 P5 REFUTED — I predicted a giant background and there is none

At `L=72` the ground is 73–81 components with the largest holding **8%** of the field, not
one giant. I reasoned from percolation intuition about a *background* without checking
that exact-value equality produces one. It does not: ground is the frame ring's own
neighbourhood at every grain. **This is the same error the containment rung recorded —
`bg<0.5` means UNREACHABLE-FROM-FRAME, not "part of the background"** — and I made it
again after reading that rung's correction.

### 6.5 MY OWN NULL CONTROL'S PASS CRITERION WAS WRONG, AND THE INSTRUMENT CAUGHT ME

PREREG §4 said the null "must return 1.0 for a 1-cell component in a large window". **It
returns 0.945216**, and that is correct: a 1×1 shape has `L²` placements of which
`(L-2)²` are clear. A point can still land on the border ring. I replaced the criterion
with one **strictly stronger** — the closed form must agree **exactly** with an explicit
enumeration of every translation, at every `(bbox, window)` pair in the ladders (it does)
— which §5 permits because it sharpens the measure *against* me. But I should have derived
the value before registering the criterion; the derivation was available before any
measurement, and this is the same defect the grouping-ceiling rung recorded in its own
control ladder.

### 6.6 P2 WAS CONFIRMED AND IS WORTH ALMOST NOTHING, AS I DECLARED IN ADVANCE

Enclosed cell fraction rises monotonically and exceeds one half at `L=72`
(**0.6356 / 0.6141**, against the predecessor's published 0.637 / 0.609 on 7 frames). I
registered this as **weak evidence** because I had already read those numbers. It is a
reproduction, not a prediction, and it carries no weight in §3.

### 6.7 I CHANGED THE UNIT OF ANALYSIS AGAINST MYSELF AND SHOULD SAY SO

The predecessor bootstrapped over **tiles**. Tiles cut from one frame share that frame's
content and are not independent (§4), so this rung bootstraps over **frames** — 30 per
corpus rather than 480. That widens every CI. It is stricter against my own numbers, and
the §1 separations survive it, but it means my CIs are **not** comparable to the
predecessor's without noting the change.

---

## 7. SEEDS — 108000–108999

**Measured. `unknown_sinks: 1`, disclosed and hand-resolved; none outside the block.**

| seed(s) | consumed by | status |
|---|---|---|
| **108000–108099** | `speckle` — 100 iid uniform fields (M3, the random-input floor at every grain) | **BURNED** |
| **108100** | the bootstrap resampler `default_rng` | **BURNED** |
| 108101–108999 | not drawn | **CLEAN** |

```
$ python3 scripts/seed_audit.py --check 108000 108999 scripts/enclosure_grain_measure.py
{"declared": [108000, 108999], "ok": true, "outside": []}
   unknown_sinks: 1
$ python3 scripts/seed_audit.py --check 108000 108999 scripts/enclosure_grain_contact.py
{"declared": [108000, 108999], "ok": true, "outside": []}      unknown_sinks: 0
$ python3 scripts/seed_audit.py --check 108000 108999 scripts/enclosure_grain_injection.py
{"declared": [108000, 108999], "ok": true, "outside": []}      unknown_sinks: 0
```

**THE ONE UNKNOWN SINK IS NAMED.** Line 534, `np.random.RandomState(SEED_SPECKLE_BASE + i)`
inside a comprehension: the static analyser cannot resolve `base + i` and reports the
sink's seeds as `null`. Read from source, it draws exactly `108000…108099`, inside the
declared block. This is **the identical site and the identical failure mode** the
grouping-ceiling rung disclosed at its own line 499 — the analyser's blind spot is
structural, not incidental.

The verbatim `check_claim` output for 108000–108999, **including its 506 tree-wide
unresolved sinks and both caveats**, is in PREREG §0.1.

**`0/100` IS NOT COPIED FORWARD.** The peer rung restated the speckle floor as
**≈0.6% [0.17, 2.25]**, and no gate in this rung asserts `== 0` on a fresh draw. The
speckle arm here is a *distributional* control (the null's positive control at every
grain), not a zero-assertion.

---

## 8. SCOPE — WHAT IS NOT SHOWN (§8)

- **NOTHING HERE SAYS THE DISCARDED COMPONENTS ARE OBJECTS.** Many will be wall, sky,
  floor. Nothing in this rung inspects what any component is. The ~5–6 enclosed regions
  of ≥60 cells per frame that appear at `L=72` are **not** shown to be objects.
- **REMOVING THE APERTURE IS NOT SHOWN TO BE A FIX** — it is measured to be the opposite:
  at `L=72` the enclosure test passes 93% of components and 64% of cells, i.e. it stops
  selecting. No downstream gate has been priced on that population.
- **ONE QUANTIZER, ONE RELATION.** `k=16` exact-value luminance. The value family was
  closed by the grouping-ceiling rung and is not reopened; motion, contour, ownership and
  learned appearance are untested here and are not covered by this negative.
- **THE SPECKLE CONTROL CANNOT REACH THE SIZES THE QUESTION IS ABOUT** (§6.2): its maximum
  component is 8 cells. The structureless comparison is measured at ≤7 cells and
  extrapolated above.
- **COMPONENTS ARE COMPUTED OUTSIDE THE GRAPH.** They are reconciled against it at eight
  grains and against the published totals at the incumbent grain, but the sweep itself is
  **a characterisation of the relation, not a measurement of a mechanism**. No rule exists
  that tiles a frame at twelve grains.
- **`L=72` WAS NOT PUT THROUGH THE SUBSTRATE.** The reconciliation spans `L=4…36`; the
  whole-frame arm's agreement with the graph is inferred from the same numpy function
  agreeing at eight smaller grains, not measured at 72.
- **NO MECHANISM WAS BUILT, SO NO MECHANISM IS VALIDATED.** There is no conjunct to gate;
  the §13 audit and injection control cover the measurement scripts only.
- **TWO CORPORA, ONE VIDEO SOURCE**; 30 frames each; the contact arm is **POST-HOC**.
- **The §4 contact finding does not license a contact-extent conjunct** — it measures that
  such a conjunct's reachable population is 8–13 components in 30 frames.

---

## 9. LEDGER ROW (carried here — `VISION_PROTOCOL.md` NOT edited)

| **108000–108999 (108000–108100 measured; `unknown_sinks: 1`, hand-resolved to 108000–108099; none outside block)** | **ENCLOSURE × GRAIN — THE APERTURE IS NOT THE BLOCKER EITHER, AND `bo_bgflood` IS NOT COMPUTING WINDOW-FIT. PRE-REGISTERED OUTCOME N (NEITHER); THE RUNG BUILDS NOTHING.** Sent to price `bo_bgflood`'s enclosure predicate against the G72 tile grain that three rungs' results rest on, with the cheap diagnostic FIRST. **THE GRAIN LADDER IS AN ENUMERATION — every divisor of the standing GRID (1,2,3,4,6,8,9,12,18,24,36,72), no grain selected — 30 frames/corpus, unit of analysis the FRAME not the tile (STRICTER than the predecessor's tile bootstrap, against my own numbers).** **THE HEADLINE, BY THE ARC'S OWN STANDING TEST: removing the aperture ENTIRELY (18×18 → the whole 72×72, a 16× area change) moves the enclosed count +30%/+33% AND MOVES THE MEDIAN 1 → 1. The ENCLOSED MEDIAN IS 1 AT EVERY GRAIN FROM 3 TO 72** (mean 1.0→3.48/4.43, max 4→426/736, typical enclosed cell's region 1→12/13). **Third lever, third time: the mint moved 1→1, the whole value family moved 1→1–2, the aperture moves 1→1.** **P1 REFUTED AND IT IS THE LEAD — I predicted the predicate computes WINDOW-FIT and pre-registered a COMPUTED geometric null (exact, no fitted parameter: the share of translations at which a component's own bbox clears the border ring; positive-controlled against BRUTE-FORCE ENUMERATION of every (bbox, window) pair — EXACT AGREEMENT). ON STRUCTURELESS INPUT OBSERVED ENCLOSURE EQUALS THE NULL TO WITHIN 1% AT EVERY GRAIN (speckle L=18 band 4–7: 0.992 [0.966, 1.017]; L=72: 1.005 [0.992, 1.016]) — the null's positive control, passed on measured data rather than a construction — WHILE NATURAL FRAMES FALL TO 0.668 [0.635, 0.702] / 0.634 [0.610, 0.656] IN THE SAME BAND, CI-SEPARATED AT EVERY GRAIN.** **So the predicate READS REAL STRUCTURE, and what it reads is SIZE-GRADED AT EVERY GRAIN INCLUDING THE WHOLE FRAME (C1 obs/null by size at L=18: 0.95/0.83/0.67/0.40/0.27/0.19/0.04/0.00; at L=72: 1.03/0.99/0.92/0.82/0.74/0.69/0.49/0.44/0.43). IN A NATURAL FRAME THE LARGER AN EQUAL-VALUE REGION IS, THE MORE CERTAINLY IT REACHES THE PICTURE EDGE — far beyond what its own extent requires.** **P3 CONFIRMED AND IT CLOSES THE AXIS: ENCLOSURE HAS ONE DEGREE OF FREEDOM AND TRADES SELECTIVITY AGAINST SIZE ONE-FOR-ONE — pass rate 0.104→0.928 alongside ≥60-cell survival 0.000→0.436, MONOTONE WITH NO KNEE, while the enclosed median is 1 at every rung. At tile grain it is selective and discards precisely the large ones (0% of ≥60); at whole frame it keeps them (44%) and has STOPPED SELECTING (93% of components, 64% of cells). Structurally the SAME shape the grouping-ceiling rung found in the value family ("ONE degree of freedom, and it moves the BACKGROUND"), reached from an independent axis.** **⇒ WHAT ACTUALLY GATES IT, NAMED: the component field is MEDIAN-1 AT EVERY GRAIN and its count is GRAIN-INVARIANT TO 9% (33,573→30,586 across a 16× area change — generalising "the flood is not fragmenting" from one grain pair to the whole ladder); and SIZE AND BORDER-REACHABILITY ARE CONFOUNDED IN THE MATERIAL, NOT IN THE PREDICATE — a natural equal-value region big enough to be an object is either not equal-valued (the grouping-ceiling rung's 5–7× spread closure) or it IS the ground. The aperture is not a mis-set free parameter: EVERY setting lands on the same one-dimensional curve.** **P5 REFUTED: at L=72 ground is 73.2/80.8 components per frame with the largest holding only 8.2%/7.8% of the field — THERE IS NO GIANT BACKGROUND. Ground is THE FRAME RING'S OWN NEIGHBOURHOOD at every grain — the containment rung's correction (`bg<0.5` means UNREACHABLE-FROM-FRAME, not "background"), which I read and then made again.** **POST-HOC CONTACT ARM (labelled POST-HOC in script, artifact and text): BOTH RECORDED DISEASES ARE REAL, AT OPPOSITE GRAINS, AND NEITHER IS THE BLOCKER — at L=12 a 128–255-cell GROUND component touches ALL FOUR SIDES with 81% OF ITS OWN OUTLINE being picture edge (at tile grain "ground" IS the window frame), while at L=72 a C2 512+-cell region is vetoed on a median 2.5 contact cells = 0.7% OF ITS OUTLINE, one side, one of eight by a SINGLE CELL (the value-flood rung's "one touching cell vetoes an entire component" inversion). FIXING IT IS WORTH 8–13 COMPONENTS IN 30 FRAMES — the cheap diagnostic killed my own would-be mechanism before a line of it was written, the fourth consecutive rung on which it has done so.** **FLOORS RE-EARNED IN-TREE, NOTHING INHERITED: oracle 222/0 BEFORE AND AFTER; provenance its own step 7 passed FIRST and the engine fingerprint RE-VERIFIED AFTER the measurement (`provenance == provenance_after` asserted in the artifact); M0 reconciled against the graph's OWN `glabel` AND `bg` at EIGHT GRAINS (4,6,8,9,12,18,24,36) with total agreement on both corpora — not one grain; the published enclosed floor 5047/3978 ASSERTED IN-RUN on the sweep's own code path (raises, not reports); and the predecessor's post-hoc cross-check reproduced to the unit in ALL FOUR CELLS (86/1, 94/42, 111/0, 83/34). Speckle re-earned AT EVERY GRAIN on fresh seeds; `0/100` NOT copied forward (the peer rung's ≈0.6% [0.17, 2.25] stands and no gate here asserts ==0).** §9 trivial: `git diff -- seeds/ runners/` EMPTY; no Rust, no seed, no rule, no flag. **§13: 11 authored + 18 unresolved sinks ALL ENUMERATED ONE AT A TIME by class; AND THE INJECTION CONTROL FOUND A HOLE IN THE FLAGSHIP GATE — five spellings planted, ALL FIVE VERIFIED TO LAND IN THE AST-RESOLVED REGION (no-op asserted to FAIL the landing check, and does), GATE BITES ON 3/5 AND IS BLIND TO 2/5: `trace` resolves a REBOUND name to its FIRST binding, so an ACCUMULATOR (`x = 0` then `x += measured`) grades AUTHORED, and `audit_source`'s "both sides authored ⇒ dead code" branch SUPPRESSES a real magic-number threshold on an accumulated quantity — invisible in BOTH the bare-literal and name-bound spelling. Same cause produces a FALSE POSITIVE on `max(largest_gnd, …)`. REPORTED FOR THE SUPERVISOR, NOT FIXED (§11 rule 4) AND NOT ROUTED AROUND: the three sites the checker could not see are HAND-AUDITED, including `if tot != want: raise` (the published-floor assertion, a number I did not choose, existing to VOID my own run).** **WHAT IT GOT WRONG: P1 REFUTED and HAD I SKIPPED THE SPECKLE ARM I WOULD HAVE PUBLISHED IT — 0.67 on natural frames alone narrates as "roughly geometric"; it is the 0.99 ON NOISE that makes 0.67 a finding, and the control was pre-registered as a FLOOR and turned out to be the DISCRIMINATOR. P4 REFUTED WITH A COVERAGE HOLE I DID NOT FORESEE: iid speckle's MAXIMUM COMPONENT IS 8 CELLS at every grain, so the structureless comparison is MEASURED AT ≤7 CELLS AND EXTRAPOLATED ABOVE — precisely where the question lives, and the prereg does not mention it. I DECLARED P1/P3/P4 ONE BET IN ADVANCE AND THEY SPLIT — the coupling claim was WRONG ABOUT P3, which understates independent evidence, the opposite error from the one the declaration protects against. P5 REFUTED by a correction I had already read. MY OWN NULL CONTROL'S PRE-REGISTERED PASS CRITERION WAS WRONG (I said 1.0 for a 1×1 shape; it is (L-2)²/L² = 0.945216 — a point can land on the ring) and the instrument caught me; replaced with a STRICTLY STRONGER brute-force-enumeration criterion, but the derivation was available before I registered it. P2 CONFIRMED AND WORTH ALMOST NOTHING, declared weak in advance because I had already read the numbers. AND I CHANGED THE UNIT OF ANALYSIS (tile → FRAME) which widens every CI against me and makes my intervals NOT comparable to the predecessor's without noting it.** **NAMED NEXT LEVER — AND IT IS NOT IN THIS PIPELINE AT ALL. Three rungs have now eliminated the mint, the grouping relation and the aperture, each by measuring that the SIZE DISTRIBUTION does not move. The enclosed median is 1 because the COMPONENT FIELD is median-1 before any predicate sees it, at every grain, and because in this material size and border-reachability are the same variable. A rung that wants few-and-large must abandon EXACT-VALUE EQUALITY ON LUMINANCE as the thing that makes two cells one region — the value family is closed (grouping-ceiling), the selection over it is closed (peer competition), and the window it is computed in is closed (here). Motion, contour, ownership and learned appearance are untested and are NOT covered by any of the three negatives. NOT STARTED HERE: it needs a prospective pre-registration with its own mechanism-level hypothesis.** |
