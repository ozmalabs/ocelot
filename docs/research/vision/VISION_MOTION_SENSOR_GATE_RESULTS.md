# THE MOTION SENSOR'S ACCURACY GATE — RESULTS

*Pre-registration: `VISION_MOTION_SENSOR_GATE_PREREG.md`, committed at
**`717f4303`** before any confirmatory number.*

- **branch (as observed):** `worktree-agent-acf1e2a2e45c10e00`
- **base SHA (as observed):** `ee0a1af25ef5dea0e9bc8919f85ebe7e8e19f463`
- **engine:** `a1d350bbd23b`, built IN THIS TREE by `scripts/engine_build.sh`
  (`own` — never symlinked from canonical). Rust source was verified
  byte-identical to canonical *before* the build, so a shared build would also
  have been legitimate under §10.1; the build was done anyway.
- **provenance gate, its OWN step, before any number:** `pytest
  tests/test_engine_provenance_migrated.py -q` → **7 passed**. The measuring
  process ALSO prints `provenance_line()` from inside itself, and it agrees:
  `engine a1d350bbd23b @ …/worktree-agent-acf1e2a2e45c10e00/…/_native.abi3.so`.
- **oracle:** `bash scripts/rung7_vision_bench.sh` → **212 passed, 10 skipped**,
  exit 0, both before and after this rung's changes. `data/` is absent from this
  worktree, so 212/10 is the correct §10.2 reading.
- **this rung's own gate:** `pytest tests/test_motion_sensor_gate_migrated.py -q`
  → **13 passed**.
- **seed block:** 94000–94999. **Seeds actually drawn, MEASURED not asserted**
  (runtime capture over a full confirmatory run): 2257 draws, **24 distinct
  in-block seeds 94000–94023**, and **exactly one outside the block: seed 0**,
  drawn by `assert_reference_is_the_real_sensor` — an instrument-equality check,
  not a confirmatory arm, on a seed burned since rung 1. Disclosed rather than
  buried; `scripts/seed_audit.py` reports **15 unknown sinks** for this script
  (the CLI blind spot: the seed list is `range(SEED_BLOCK, SEED_BLOCK +
  args.n_seeds)`), which is exactly why the runtime capture was run.
- **No Rust. No seed. No existing rung's file edited. Nothing ships on by
  default** (§9) — the gate is a new script and adds no default behaviour.

---

## THE HEADLINE, IN SIX LINES

**The sensor's arithmetic is PERFECT and its answer is ~11% wrong.** On every
block where the true offset is the unique SAD minimum, the error rate is
**0.0000 — exactly zero, at every magnitude tested.** Every error the arc has
ever inherited belongs to the OBJECTIVE, not to a bug.

**The dangerous class dominates and nobody had counted it.** At the arc's own
operating point: **confidently wrong 10.67% [10.60, 10.75]**, silent miss
**0.13% [0.06, 0.20]**, false motion on a static field **0.0000 exactly**.
**The sensor does not abstain — it CONFABULATES**, and beyond 1.5× its aperture
it is confidently wrong **>99%** of the time while still emitting a well-formed
vector.

**The recorded ~11% reproduced on a wholly independent corpus** (10.67% vs the
landed 10.9%/10.8%), which is what licenses everything below.

**And the bound inverts the landed reading: the pipeline over-mints by ≤1.75×
against ground truth, not by 23×.** The 23× is fragile in its DENOMINATOR, not
its numerator.

---

## 0 — WHAT THE THREE CLASSES ARE, AND WHY THEY HAD TO BE COUNTED SEPARATELY

| class | definition | downstream consequence |
|---|---|---|
| **silent miss** | `v == (0,0)` while `t ≠ 0` | the cell carries NO vector and cannot join any common-fate group. The phi rung's `n_nonzero = 0`. |
| **confidently wrong** | `v ≠ (0,0)`, `‖v − t‖ > τ` | a WELL-FORMED vector, wrong, **indistinguishable downstream from a true one**. The phi rung's `(0,4)`. |
| **correct** | `v ≠ (0,0)`, `‖v − t‖ ≤ τ` | — |
| *false motion* | `v ≠ (0,0)` while `t == 0` | motion invented from a static scene |

Silent miss is tested **first and unconditionally, ahead of the tolerance**: at a
large τ a small true motion reported as `(0,0)` would score "correct", but
downstream it is not a slightly-wrong vector, it is the ABSENCE of one.
*Disclosure, as registered:* the number of silent misses that would also have
passed τ is recorded in the results JSON and is negligible at the operating
point.

They had to be separated because **they do not move together** — the whole of
H1. Silent miss is ~0.1% on textured input and **50–75% on a uniform-background
figure**; confidently wrong is ~11% at the operating point and **>99%** beyond
the aperture; false motion is **exactly zero** everywhere it was measured on a
static field. One "error rate" would have averaged three unrelated phenomena.

---

## 1 — THE TOLERANCE, DERIVED (§13)

All three readings are reported, as registered before the run:

| reading | value | what it is |
|---|---|---|
| **exact** | **0.0** | NO NUMBER AT ALL — the strongest §13 outcome. **The primary headline.** |
| **Otsu, within aperture** | **2.2361** | the accuracy tolerance: among answers the sensor could have got right, where correct ends |
| **Otsu, all conditions** | **5.0990** | dominated by the beyond-aperture regime — **it recovers the APERTURE, not accuracy** |

Two facts worth recording. First, **the within-aperture split is √5** — the norm
of the integer vector `(1,2)`, i.e. the split lands exactly on a lattice
distance, which is what a discrete-valued Otsu should do and is a small
confirmation that no binning artefact is involved. Second, **it lands at 2.2361
against the motion rung's independently-derived 2.402 on C2** — two different
corpora, two different populations (adjacent-pair disagreement vs error
magnitude), one region.

**The all-conditions split recovering the aperture is itself a §13 result:** the
dominant structure in the sensor's error distribution is not accuracy, it is
where the search window stops.

---

## 2 — THE THREE RATES AT THE ARC'S OPERATING POINT

Block 4, radius 4, a global pan of exactly one block — **the same construction
the landed diagnostic used to read ~11%**. n = 24 seeds, unit of analysis the
SEED, 95% CI.

**Exact tolerance (τ = 0):**

| contrast | silent miss | **confidently wrong** | correct |
|---|---|---|---|
| 8 | 0.0013 [0.0006, 0.0020] | **0.1067 [0.1060, 0.1075]** | 0.8920 |
| 32 | 0.0009 [0.0003, 0.0015] | **0.1071 [0.1066, 0.1077]** | 0.8920 |

**Otsu-within-aperture tolerance (τ = 2.2361):**

| contrast | silent miss | **confidently wrong** | correct |
|---|---|---|---|
| 8 | 0.0013 | **0.0856 [0.0827, 0.0886]** | 0.9131 |
| 32 | 0.0009 | **0.0849 [0.0820, 0.0878]** | 0.9142 |

**P4 CONFIRMED, and it is the load-bearing check of the whole rung.** The
recorded figures are **10.9% (C1)** and **10.8% (C2)**, read off two television
episodes. This rung reads **10.67%** off Fourier-synthesised noise with ground
truth by construction. **A corpus-independent constant of the sensor at this
operating point, not a property of anyone's video.**

**Only ~2 percentage points of that 11% are "recoverable" error** — the gap
between the exact and Otsu readings (10.67% → 8.56%) is the share of wrong
vectors that are wrong by less than √5. The other ~8.5pp are wrong by more.

---

## 3 — ERROR AS A FUNCTION OF THE PARAMETERS THAT MATTER

### 3.1 Displacement magnitude — H2 CONFIRMED, P3's PROVISO BROKE

| `|D|` / block | block 2 | block 4 | block 8 |
|---|---|---|---|
| 0.12–0.25 | — | 0.0000 | 0.0000 |
| 0.50 | 0.0057 | 0.0044 | 0.0003 |
| **1.00** | **0.0182** | **0.0339** | **0.0853** |
| 1.50 | — | 0.7225 | 0.0265 |
| 2.00 | 0.6842 | 0.9911 | — |
| 3.00–4.00 | 0.9680 | — | — |

(confidently-wrong rate, Otsu-within-aperture tolerance)

**The governing variable is `|D|` RELATIVE TO the aperture, not absolute
pixels.** An 8-pixel displacement is catastrophic at block 4 (**99.1%** wrong)
and routine at block 8 (**8.5%**). That is H2, and it is a 12× swing on the same
physical motion.

**But P3's specific proviso BROKE, and the breakage is informative.** I
predicted that error would *collapse* onto `|D|/block`. It does not: **at matched
ratio 1.0 a LARGER block is WORSE** — 1.8% → 3.4% → 8.5% for blocks 2 → 4 → 8.
The mechanism is countable: the search window holds `(2r+1)²` candidates —
**25, 81, 289** — so a larger aperture offers proportionally more chances for a
spurious offset to beat the truth. **A bigger aperture buys reach and pays for
it in candidates**, and the arc has been reading only the reach half of that
trade.

### 3.2 Texture — H3 RESOLVED, and the landed C1 relationship is a CONFOUND

Contrast and spectral slope varied **orthogonally**, which found frames cannot do:

| contrast (sd) | β=0 | β=1 | β=2 |
|---|---|---|---|
| 2 | 0.0233 | 0.0178 | **0.0544** |
| 4 | 0.0226 | 0.0168 | 0.0213 |
| 8 | 0.0226 | 0.0166 | 0.0166 |
| 16 | 0.0226 | 0.0166 | 0.0157 |
| 32 | 0.0227 | 0.0166 | 0.0156 |
| 64 | 0.0228 | 0.0168 | 0.0172 |

**CONTRAST IS NOT LOAD-BEARING. Across a 32× range it moves the error rate by
0.0002.** P5 confirmed.

**This resolves the recorded disagreement, and it resolves it against C1.** The
motion rung found the flattest block-std quartile 4× more error-prone on C1 and
no monotone relationship on C2, and could not say which was right.
**Block std — which is what "texture quartile" measured — is not the driver.**
The C2 null was the correct reading; the C1 relationship was a confound, because
in a cartoon low block-std co-varies with large flat drawn regions, and it is the
*flatness* (no matchable structure at all), not the *contrast*, that hurts.

**What IS load-bearing is a floor, and it is sharp.** The single cell where
anything moves is `contrast 2, β 2` — **mean block std 0.398**, i.e. below half
an 8-bit level. There silent miss goes **0.0003 → 0.0641 (214×)** and confidently
wrong **0.0166 → 0.0544**. **The sensor is fine until the block carries less than
one quantisation step of structure, and then it falls off a cliff.** That is a
number that falls OUT — of the 8-bit lattice, not of anything chosen.

*Reported as unexplained:* `contrast 64, β 2` shows silent miss 0.0083 against
0.0004 at contrast 32 — a 20× rise with no monotone trend around it. I do not
have an account of it and am not manufacturing one.

### 3.3 Number of true bodies — the multi-body penalty is real and CI-separated

| true bodies | seam blocks | silent miss | **confidently wrong** |
|---|---|---|---|
| 1 | 0.000 | 0.0003 | **0.0283 [0.0258, 0.0308]** |
| 2 | 0.000 | 0.0017 | **0.0700 [0.0655, 0.0744]** |
| 3 | 0.000 | 0.0013 | 0.0592 [0.0552, 0.0631] |
| 4 | 0.111 | 0.0004 | 0.0558 [0.0522, 0.0595] |

**Adding a second true velocity MORE THAN DOUBLES the confidently-wrong rate**
(2.83% → 7.00%, CIs disjoint), and it does not keep rising with a third or
fourth. Blocks straddling a body seam were excluded and counted separately —
"this block has two true answers" is a different fact from "the sensor is wrong",
and pooling them would have manufactured a body-count trend.

**This matters directly for the landed claim:** C2 is live action, i.e. exactly
the multi-body condition, so the operating-point rate measured on a single rigid
pan is a LOWER bound for it.

### 3.4 Rotation, borders, and the uniform-background figure

**Rotation** (blocks whose within-block deformation exceeds half a pixel are
reported separately — there, one-vector-per-block is a REPRESENTATION failure,
not a sensor failure):

| degrees | blocks not translational | confidently wrong |
|---|---|---|
| 1 | 0.000 | 0.0000 |
| 2 | 0.000 | 0.0012 |
| 5 | 0.000 | 0.0159 |
| 10 | 0.000 | **0.3800** |
| 90 | **1.000** | 0.9886 *(on deforming blocks)* |

At block 4 a rotation stays translational-per-block out to ~27°, so the 10° cliff
is a genuine matching failure, not a representation one.

**Borders** (cropped, non-toroidal pan — the sensor pads with `mode="edge"`,
i.e. it fabricates the content it matches against):

| `|D|` | interior | border |
|---|---|---|
| 2 | 0.0000 | 0.0130 |
| 4 | 0.0000 | **0.0868** |
| 6 | 0.7062 | 0.7373 |
| 8 | 0.9912 | 0.9925 |

**Edge fabrication costs ~9pp at the aperture edge and is swamped beyond it.**

**Figure on a uniform background — the phi rung's exact stimulus class, and
where P2 lands:**

| figure | `|D|`=1 | `|D|`=8 | `|D|`=12 |
|---|---|---|---|
| 8 px | sm **0.500** | sm 0.500, cw 0.500 | sm **1.000** |
| 16 px | sm **0.750** | sm 0.750, cw 0.250 | sm 0.750, cw 0.250 |

**P2 CONFIRMED, and strongly. On a uniform field, HALF TO THREE QUARTERS of
figure blocks report NO MOTION AT ALL — at a displacement of ONE PIXEL.** This is
the aperture problem in its textbook form: a block containing only a straight
edge is ambiguous along that edge, ties, and the Occam tie-break returns `(0,0)`.

**So silent miss is a property of the STIMULUS'S EVIDENCE, not of the
displacement** — it is ~0.1% on textured input at any magnitude and 50–75% on a
uniform-background figure at every magnitude. **The phi rung's `n_nonzero = 0`
was not a temporal-gap effect at all; it is what this sensor does to a figure on
a blank field, at any separation.** That does not overturn the phi rung's
conclusion — its C-RIGID control already localised the failure to correspondence
across a gap — but it does mean the silent half of its "three regimes" is a
stimulus-class fact.

---

## 4 — THE DECOMPOSITION: SENSOR DEFECT IS EXACTLY ZERO (P7)

*Declared SECONDARY in advance: this shares the SAD objective with the sensor, so
it is not independent evidence about the arithmetic. It is ground-truth-
conditional — it asks about the known `t`, which the sensor cannot see.*

| `|D|` | truth is the unique SAD minimum | **SENSOR DEFECT** | STIMULUS AMBIGUITY |
|---|---|---|---|
| 1 | 1.0000 | **0.0000** | — |
| 2 | 0.9943 | **0.0000** | 0.7270 |
| 3 | 0.9444 | **0.0000** | 0.4884 |
| 4 | 0.9444 | **0.0000** | 0.7431 |
| 5–8 | 0.0000 | — | 0.6467 – 1.0000 |

**Every single error is stimulus ambiguity under the SAD objective. The
implementation is exactly right.** P7 confirmed with no residual.

**This is the most consequential line in the rung, because it changes what
"improve the sensor" can mean.** There is no bug to fix. The ~11% is the price of
(a) the SAD objective and (b) a search window of `radius = block`. Anything that
moves it must change the objective, the aperture, or the evidence — not the code.
It also retires, with a measurement, any future suspicion that the landed motion
numbers were contaminated by an implementation error.

---

## 5 — THE BOUND EVERY LANDED MOTION COUNT INHERITS

This is the deliverable other rungs cite. The **actual grouping pipeline**
(`seeds/vision_motion_group.json` via `motion_group_world`, `assert_settled`
clean on every field) was run on constructed fields whose true body count is
known, at two displacement families.

**The expected multi-cell group count is `k − 1`, not `k`**, because the
`mcontrast` rule REFUSES the dominant motion. That reading is not assumed — it is
**empirically confirmed at k=1**, where a single-body field inside the aperture
mints **0.00 [0.00, 0.00]** multi-cell groups.

| family | true bodies | expected | minted | over-grouping |
|---|---|---|---|---|
| inside aperture (`|D|`≈3.2) | 1 | 0 | 0.00 [0.00, 0.00] | — (0.00 spurious) |
| inside aperture | 2 | 1 | 1.75 [1.26, 2.24] | **1.75×** |
| inside aperture | 3 | 2 | 2.38 [1.86, 2.89] | **1.19×** |
| **aperture corner (`|D|`=(4,4))** | 1 | 0 | **0.62 [0.11, 1.14]** | — (0.62 **spurious**) |
| aperture corner | 2 | 1 | 1.75 [1.26, 2.24] | **1.75×** |
| aperture corner | 3 | 2 | 3.00 [2.26, 3.74] | **1.50×** |

*The aperture-corner family was added AFTER the first ran, and the reason is
disclosed rather than buried (§6): the first family's velocities sit at `|D|`≈3.2
where the sensor is ~3% wrong, whereas the landed global-pan control ran at
`dom_v = (4,4)` where this rung measures 10.7%. A bound read at 3% and quoted
against a claim made at 10.7% would not be a bound. No arm was re-run and no
number reinterpreted — a non-comparable arm was JOINED by a comparable one, and
both are reported.*

### The bound, stated

> **Given this error profile, the grouping pipeline over-mints multi-cell groups
> by a factor of 1.19–1.75× against ground truth, plus up to ~0.6 spurious
> multi-cell groups per frame from sensor error alone at the aperture corner.**

**The widest defensible reading of "3.95 multi-cell groups per frame" (C2, Otsu
tolerance):** it is consistent with roughly **3–4 genuinely motion-distinct
bodies per frame**, inflated ~1.2–1.75× and contaminated by ≲0.6 spurious groups.
**It is NOT evidence that the criterion runs away.** A criterion that over-mints
by under 2× cannot produce a 23× artefact.

**And therefore the 23× is fragile in its DENOMINATOR, not its numerator.** The
numerator 3.95 is now bounded to within ~1.75× by ground truth. The denominator —
the incumbent's 0.17 at the matched lattice — has **no ground-truth anchor at
all**, and the landed rung itself recorded that this control moved **60–100×**
from configuration alone (0.17 against a published 10–17). **The honest reading
of the 23× is that it compares a numerator whose error is now priced against a
denominator whose is not.** That does not overturn the landed conclusion —
"common motion did not deliver few-and-large" survives, because the *size*
finding (median 2 cells) is untouched by anything here — but it does relocate
where the remaining uncertainty lives.

**What a future rung should quote:**

| quantity | value | condition |
|---|---|---|
| confidently wrong, per block | **10.67% [10.60, 10.75]** | block 4, `|D|` = aperture corner, exact τ |
| confidently wrong, per block | **8.56% [8.27, 8.86]** | same, τ = 2.2361 (Otsu) |
| silent miss, per block | **0.13% [0.06, 0.20]** | textured input |
| silent miss, per block | **50–75%** | figure on a uniform field, ANY displacement |
| false motion, per block | **0.0000** | static field, noise sd ≤ 4 |
| confidently wrong | **>99%** | `|D|` > 1.5 × block |
| multi-body penalty | **2.83% → 7.00%** | 1 body → 2 bodies |
| grouping over-mint | **1.19–1.75×** | vs ground-truth body count |

---

## 6 — THE GATE, AND IT WAS PROVEN TO BITE

`scripts/motion_sensor_gate.py`, runnable by any future rung:

```
python3 scripts/motion_sensor_gate.py --mode confirm      # exit 0 = trust it
```

Two **exact structural invariants** (no tolerance, no constant), plus a
regression comparison against this tree's committed baseline — a comparison
point that falls OUT of a prior measurement rather than being chosen.

**Positive control. A gate that has never been ABLE to fail has not been
tested** — three provenance gates in this tree sat green for 51 commits and then
all fired at once as false accusations. Three deliberate degradations, each a
REAL bug rather than a caricature:

| degradation | what it is | result |
|---|---|---|
| `tiebreak_corner` | raw row-major offset scan — **exactly the footgun `vector_field`'s own docstring claims to avoid** | **RED via I1**: 35/324 blocks report motion on bit-identical frames |
| `radius_half` | search window shrunk to `block//2` | **RED via I2**: 306/306 resolvable blocks missed; + regression, cw 0.98 vs baseline 0.089 |
| `sad_coarse` | SAD on every other pixel — the classic subsampling speedup | **RED via I2** (8/323 missed) + regression on false motion, 0.0531 vs baseline 0.0000 |
| **none (restore)** | — | **GREEN**, compared against the committed baseline |

**Each degradation trips a DIFFERENT invariant, which is the point of having
two.** I1 catches tie-break bugs and is blind to the objective; I2 catches
objective/aperture bugs and is blind to ties. And the subtlest bug, `sad_coarse`,
moved the operating point by only 0.9pp — **it was the ZERO-FIELD arm that
caught it decisively** (5.3% invented motion against a baseline of exactly zero).
A gate without a static-field arm would have nearly missed it.

**The reference implementation is asserted BIT-IDENTICAL to `mgw.vector_field`
on 108 inputs every single time the gate runs.** Without that, the "undegraded"
arm could drift from the instrument under test and the whole control would be
theatre.

*One disclosed inconsistency in the committed artefacts:*
`results/motion_sensor_gate_baseline.json` was written by the confirmatory run
**before** the aperture-corner bound family was added, so its `grouping_bound`
block holds only the first family. **This does not affect the gate**, whose
regression comparison reads only `operating_point` and `zero_field` — neither of
which the addition touched, and both of which the restore run re-validated
against this exact baseline. The full two-family bound is in
`results/motion_sensor_gate_bound.json` and is what §5 quotes. Recording it
rather than silently regenerating the baseline, because a regenerated baseline
would no longer be the file the GREEN restore run was checked against.

---

## 7 — §13, AND THE HOLE I WALKED INTO

`tests/test_motion_sensor_gate_migrated.py`, **13 passed**. The AST walker
locates flagged sites **BY SHAPE**: a constant nested in a `BinOp` or a
`Subscript` slice is *arithmetic or addressing*, not a threshold. **Heeding the
phi rung's recorded defect — its first version counted ARRAY INDICES as
thresholds in 3 of 6 flagged sites — every site was audited BY HAND before any
carve-out was written**, and the audit is recorded in the test file so a later
reader can check it rather than trust it.

Two things removed rather than excused:

- **`1e-12` in the zero test is GONE.** Both `v` and `t` are integer
  displacements stored as float64, so exact equality is correct *and strictly
  stronger*. An epsilon there would have been a §13 number with nothing to fall
  out of.
- **`0.5` in the rotation arm was NAMED AND DERIVED**, not deleted:
  `SUBPIXEL_INVISIBLE = INTEGER_STEP / 2.0`. It falls out of the sensor's own
  output quantisation — it emits integer offsets, so a deformation below half a
  step cannot change any vector it could report.

**AND THE GATE HAD A HOLE, WHICH I PUT THERE AND THEN CLOSED.** The first version
walked only `ast.Constant` comparands. So when I moved the `0.5` out of a
comparison and into a named module constant, **the gate went green without the
number going anywhere.** Naming a threshold is not deriving it. The walker now
flags a NAME bound to a numeric literal exactly like the literal, and
`test_a_threshold_cannot_be_HIDDEN_BY_NAMING_IT` asserts it — including that the
hand-audit allowlist has exactly one entry, so growth is visible rather than
silent.

---

## 8 — WHICH REGISTERED OUTCOME OCCURRED

| # | prediction | outcome |
|---|---|---|
| P1 | confidently wrong ≫ silent miss on textured input; the sensor confabulates | **CONFIRMED** (10.67% vs 0.13%, 82×) |
| P2 | silent miss is a LOW-EVIDENCE property, not a displacement one | **CONFIRMED** (0.1% textured; 50–75% on a uniform field at `|D|`=1) |
| P3 | error collapses onto `|D|`/block | **H2 CONFIRMED, PROVISO BROKE** — the ratio governs, but at matched ratio a LARGER block is WORSE (1.8/3.4/8.5%), because the candidate count is `(2r+1)²` |
| P4 | the recorded ~11% reproduces on an independent corpus | **CONFIRMED** (10.67% vs 10.9%/10.8%) |
| P5 | contrast is not load-bearing; the C1 relationship is a confound | **CONFIRMED** (0.0002 across 32× contrast) |
| P6 | false motion on a static field ≈ 0 | **CONFIRMED** — exactly 0.0000 at every noise level |
| P7 | zero error on blocks where truth is the unique SAD minimum | **CONFIRMED EXACTLY** — 0.0000 at every resolvable magnitude |

**Six confirmed, one proviso broken.** The broken proviso is the informative one:
I understood that the aperture governs and did not understand that widening it
has a cost.

---

## 9 — WHAT I GOT WRONG

1. **THE GATE'S OWN §13 HOLE, above.** I closed a threshold by naming it and my
   own gate applauded. Caught only because the green came too easily.
2. **The `4px` figure arm has an EMPTY POPULATION and reports `None` for all six
   of its rows.** The figure is centred at `GRID//2 - fsize//2 = 34`, which is
   not block-aligned, so no block is ever *fully* inside a 4-pixel figure. The
   arm is dead and I am reporting it dead rather than quietly dropping the row.
   The 8px and 16px rows are unaffected and carry the finding.
3. **`background_false_motion` in the figure arm IS NOT INTERPRETABLE, and it is
   my labelling error, not the sensor's.** I labelled every non-figure block
   `t = (0,0)`, but blocks the figure moves INTO have genuinely changed content
   and have no correspondence to find. The 0.6–2.6% there is an artefact of my
   ground truth, not invented motion. **The clean false-motion number is the A6
   zero-field arm's exactly-0.0000**, which has no such defect.
4. **My first bound arm was NOT COMPARABLE to the claim it was bounding** — it
   ran at `|D|`≈3.2 (~3% error) against a landed control at `(4,4)` (~10.7%).
   Caught before writing the bound, fixed by ADDING the comparable family rather
   than replacing the first, and disclosed in §5.
5. **I mis-specified the bound's denominator on first reading.** I divided minted
   groups by `k` and read "0.8–0.9×, the pipeline under-mints". The `mcontrast`
   rule refuses the dominant body, so the expectation is `k − 1`, and the honest
   answer is the opposite direction: **1.19–1.75× over-minting.** Caught by the
   `k=1` row minting exactly 0.00, which `k` as a denominator cannot explain.
6. **`contrast 64, β 2`** shows a 20× silent-miss rise with no trend around it. I
   have no account of it and did not invent one.
7. **The bordered arm's interior rate (0.0000 at `|D|`=4) does not match the
   toroidal arm's (0.0339) at the nominally same condition**, because the two use
   different synthesis sizes (104 vs 72) and therefore different Fourier bases.
   Every rate here is conditional on the synthesis size as well as on `β` and
   contrast — a scope limit I did not anticipate when designing the arms.

---

## 10 — WHAT IS NOT SHOWN (§8), AND THE NAMED NEXT LEVERS

- **Constructed stimuli are not found frames.** Fourier textures have stationary
  statistics; real scenes have occlusion, non-rigid motion, lighting change and
  compression artefacts. **The stimulus family is the load-bearing assumption of
  this entire rung.** The operating-point arm ties exactly ONE point of it back to
  the recorded corpus figure, and that tie is what licenses the rest — it is not
  a general proof of representativeness.
- **The ambiguity decomposition shares the SAD objective with the sensor** and is
  declared secondary throughout. It cannot detect a defect that is *also* in the
  oracle.
- **No claim about temporal integration.** Everything here is two frames. The
  phi rung's named lever — `TimeInfer` on ≥3 frames, the only mechanism whose
  aperture is not a pixel length — is untouched and remains unrun.
- **No claim that a different objective would do better.** That every error is
  the objective's is a diagnosis, not a proposal, and the obvious follow-up
  (does a normalised or gradient-based objective move the 11%?) needs its own
  pre-registration with its own mechanism-level hypothesis, never a parameter
  search (§3.6).
- **The `(2r+1)²` candidate-count account of the matched-ratio ordering is a
  MECHANISM I am asserting from three data points, not one I measured.** It
  predicts the ordering and the direction; it has not been tested against an
  alternative.
- **Named next lever, deliberately not run, with its reason registered in
  advance:** the multi-body penalty (2.83% → 7.00%) is measured on rigid bands
  with block-aligned seams. Real motion boundaries are curved and unaligned, and
  the seam-block population — which this rung excluded by construction — is
  exactly where border ownership and motion grouping would have to agree. That is
  a different rung's hypothesis, and running it here would have been a sweep.

---

## 11 — LEDGER ROW (for the supervisor to append; NOT edited into the protocol by this rung)

| range | used for |
|---|---|
| **94000–94999 (24 seeds resolved in-block + seed 0 for the instrument-equality check, MEASURED by runtime capture over a full run: 2257 draws, 24 distinct in-block, 1 outside; `seed_audit` reports 15 unknown sinks — the CLI blind spot — which is WHY the capture was run)** | **THE SENSOR'S ARITHMETIC IS PERFECT AND ITS ANSWER IS ~11% WRONG — EVERY ERROR IN THIS ARC BELONGS TO THE OBJECTIVE, NOT TO A BUG.** Ground truth BY CONSTRUCTION (periodic Fourier textures + exact integer rolls). **SENSOR DEFECT = 0.0000 at EVERY resolvable magnitude** (secondary, declared: the oracle shares the SAD objective). **THE THREE RATES, COUNTED SEPARATELY BECAUSE THEY DO NOT MOVE TOGETHER: confidently wrong 10.67% [10.60,10.75], silent miss 0.13% [0.06,0.20], false motion EXACTLY 0.0000** at the arc's operating point, n=24, unit=seed. **THE RECORDED ~11% REPRODUCED ON A WHOLLY INDEPENDENT CORPUS (10.67% vs 10.9%/10.8%) — a constant of the sensor, not a property of anyone's video.** **THE SENSOR CONFABULATES RATHER THAN ABSTAINS: >99% confidently wrong beyond 1.5× aperture, still well-formed, still indistinguishable downstream.** H2 confirmed (`|D|`/block governs; 8px is 99.1% wrong at block 4 and 8.5% at block 8) **but P3's PROVISO BROKE — at MATCHED ratio a LARGER block is WORSE (1.8/3.4/8.5%), because candidates go 25/81/289: a wider aperture buys reach and PAYS IN CANDIDATES.** **THE C1/C2 TEXTURE DISAGREEMENT IS RESOLVED AGAINST C1: contrast moves the rate by 0.0002 across 32× — block-std was a CONFOUND; the real cliff is at mean block std < 0.4 (below one 8-bit step), where silent miss goes 0.0003 → 0.0641.** **SILENT MISS IS A STIMULUS-CLASS FACT, NOT A DISPLACEMENT ONE: 50–75% of figure blocks on a UNIFORM field report NO motion at `|D|`=1 — the phi rung's `n_nonzero=0` at any separation.** Multi-body penalty CI-separated (2.83% → 7.00% at two bodies). **THE BOUND, MEASURED ON THE REAL PIPELINE WITH GROUND TRUTH: over-minting is 1.19–1.75× (expectation `k−1`, since `mcontrast` refuses the dominant body — confirmed empirically by k=1 minting 0.00), plus ≲0.62 spurious groups/frame at the aperture corner. SO 3.95 MULTI-CELL GROUPS/FRAME IS CONSISTENT WITH ~3–4 GENUINE BODIES INFLATED <2×, AND THE 23× IS FRAGILE IN ITS DENOMINATOR, NOT ITS NUMERATOR — the numerator is now priced, the incumbent's 0.17 has no ground-truth anchor and already moved 60–100× on configuration alone.** GATE POSITIVE-CONTROLLED WITH THREE REAL BUGS, EACH TRIPPING A DIFFERENT INVARIANT: `tiebreak_corner` (the footgun the sensor's OWN docstring claims to avoid) RED via I1; `radius_half` and `sad_coarse` RED via I2; **the subtlest (`sad_coarse`, 0.9pp on the operating point) was caught DECISIVELY only by the ZERO-FIELD arm (5.3% invented motion vs baseline exactly 0)**; restore GREEN against the committed baseline. Reference impl asserted BIT-IDENTICAL to `mgw.vector_field` on 108 inputs every run. **WHAT IT GOT WRONG: THE §13 GATE HAD A HOLE I PUT THERE — I closed a threshold BY NAMING IT and my own walker went green; now a NAME bound to a literal is flagged like the literal, with a one-entry hand-audit allowlist asserted so growth is visible. The 4px figure arm has an EMPTY POPULATION (figure not block-aligned) and is reported dead, not dropped. `background_false_motion` in that arm is MY LABELLING ERROR (blocks the figure moves into have no correspondence) and is declared uninterpretable. THE FIRST BOUND ARM WAS NOT COMPARABLE to the claim it bounded (`|D|`≈3.2 at ~3% vs the landed control's (4,4) at 10.7%) — fixed by ADDING the comparable family, not replacing. AND I MIS-SPECIFIED THE BOUND'S DENOMINATOR, reading "0.8–0.9×, under-mints" before the k=1 row (0.00) forced the `k−1` expectation and the OPPOSITE direction.** No Rust, no seed; provenance gate its OWN step (7 passed) + `provenance_line()` printed from INSIDE the measuring process; own gate 13 passed; oracle 212/10. |
