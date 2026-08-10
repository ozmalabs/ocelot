# PHASE-FIELD PROTO-OBJECTS — RESULTS: **THE MEDIAN MOVES OFF 1 — BUT ONLY TO ~3 CELLS, THE MOVE IS LARGELY REPRODUCED BY A MAGNITUDE COMPARATOR, AND THE FULL-SWEEP DISTRIBUTION IS THE VALUE-FLOOD'S OWN GIANT-GROUND + TINY-MEDIAN TRADE-OFF IN A NEW REPRESENTATION. PRE-REGISTERED VERDICT: AMBIGUOUS — BUILD NOTHING.**

*Pre-registration `VISION_PHASEFIELD_PREREG.md`, committed **`b4b8ae3e48`** BEFORE any
confirmatory number (only synthetic positive-controls and the value-flood floor had been
computed). Nothing in it was edited after the first number. This rung reports its
pre-registered **AMBIGUOUS** outcome and **builds nothing** (Term enum index 180 reserved,
UNUSED).*

**ENGINE PROVENANCE (§10).** Printed from **inside** the measuring process into
`results/phasefield.json`, asserted `== EXPECT_ENGINE`, and **re-verified after the
measurement**:

```
engine e039d2eec2dd @ <this worktree>/runners/dsl/python/substrate_rs/_native.abi3.so  [1 other tree build(s) shadowed]
```

`provenance_stable` (provenance == provenance_after): **True** (asserted in the artifact).
Branch **`worktree-agent-a00a59252dd578bd5`** — the name I actually see; no
`gamma-substrate/phasefield` name exists. Base SHA **`e451d73208`** (this worktree
fast-forwarded to include the motion-energy merge, so index 179 is present and index 180
is free). Engine built in-tree by `scripts/engine_build.sh` (**`own`**); **THIS RUNG ADDS
NO RUST** — the wave transform is characterised in numpy first, per the brief. Migrated
provenance gate run as **its own step, first: 7 passed**.

**LOAD (recorded with every measurement).** `os.getloadavg()` written into the artifact:
start `[0.31, 0.43, 0.62]`, end `[0.44, 0.46, 0.63]`; wall **4.9 s** (cached-friendly: the confirmatory
compute is FFT-per-frame, exact). **At most one worker; no wall-clock quantity is a
verdict anywhere in this rung.**

**FLOORS re-earned IN-TREE, on this rung's OWN code path, asserted in-run (the run VOIDS
otherwise):** the value-flood / peer-competition enclosed floor **C1 5047 / C2 3978** at
G72 / REGION=18 / k=16 / the published 7 SAMPLED_FRAMES — reproduced EXACTLY, proving the
frames are the published frames. Corpus pins asserted at run time: C1 `08630d4b`,
C2 `119eca43`.

---

## 1. THE HEADLINE

**The question was: does reading the frame as a WAVEFIELD move the object size
distribution off the value-flood's median-1? The answer is a QUALIFIED, NON-PHASE-SPECIFIC
"a little" — which by the pre-registered discriminator is AMBIGUOUS, not CONFIRM.**

At the whole frame **L=72** (30 frames/corpus, unit = FRAME), the value-flood gives
enclosed median **1 [1, 1]** with **~946 / ~718 enclosed components per frame**. Phase
congruency (Kovesi monogenic) bounded regions, at the §13-clean **Otsu** operating point,
nscale=3:

| | enclosed median CI | all-region median | regions/frame | value-flood enclosed median | value-flood comps/frame |
|---|---|---|---|---|---|
| **C1** cartoon | **3.25 [2.5, 4.0]** | 4.0 | **24.0** | **1 [1,1]** | ~946 |
| **C2** live-action | **3.00 [2.5, 4.0]** | 9.0 | **8.1** | **1 [1,1]** | ~718 |

**The enclosed median IS CI-separated above 1 at Otsu on both corpora, and the region
count COLLAPSED 48× (C1) / 205× (C2) — the first lever in the object line to move the
enclosed median at all, and it is genuinely FEWER.** But three measured facts, each
pre-registered, keep it out of CONFIRM:

1. **THE MOVE IS SMALL — median ~3 cells, never the object decade.** Across the ENTIRE
   threshold sweep (edge-density 0.02 → 0.50) and both nscales, the enclosed median stays
   in **single-digit cells (2 – 9)**. It never reaches tens-to-hundreds — it is not
   "LARGE".
2. **THE FULL-SWEEP DISTRIBUTION IS THE VALUE-FLOOD'S OWN SHAPE.** The largest region (the
   ground) traverses **98% → 17% of the frame** as edge-density rises, while the enclosed
   median stands still at 2 – 6. A giant background region + a mass of tiny fragments, at
   every threshold — the SAME "one degree of freedom that moves the BACKGROUND" the value
   and aperture rungs measured, now confirmed to hold in the WAVEFIELD representation.
3. **THE MOVE IS LARGELY REPRODUCED BY THE MAGNITUDE COMPARATOR (the pre-registered
   trap).** Local monogenic ENERGY (contrast-DEPENDENT, no phase normalisation) at Otsu
   gives enclosed median **2 – 5** — the same shift off 1. PC beats LE cleanly only on C1
   (3.25 vs 2.0; nscale=4 6.25 vs 2.0); on C2 they are indistinguishable (3.0 vs 3.0). **So
   the median shift is generic multi-scale CONTOUR segmentation, not PHASE.**

**⇒ PRE-REGISTERED VERDICT: AMBIGUOUS.** By §5's decision rule the two §13-clean operating
points DISAGREE for C1 (Otsu separates above 1; the noise floor does not — see §3) AND
PC ≈ LE on C2 — both are explicit AMBIGUOUS triggers. **The wave hypothesis is NOT a clean
lever for few-and-large, and its median move is not phase-specific.** No mechanism is
warranted; **index 180 is unused, no seed byte, no Rust.** A build would need a new
prospective pre-registration (§5).

---

## 2. THE INSTRUMENT IS ALIVE (controls, run first)

| control | result | reading |
|---|---|---|
| **uniform field** 128 | `PC max = 0.0000` | dead-instrument fires: no congruency, no contours |
| **ideal disc** | Otsu → **2 regions**, sizes 3947 / ~800, median **2374** | the instrument CAN produce large regions (positive control) |
| **speckle** (100 iid fields, seeds 114000–114099) | Otsu → **1.0 regions/frame**, median 5161 (whole frame) | structureless → **no coherent contours → ONE region**; the noise floor correctly suppresses noise |

**The speckle behaviour is itself a finding: on structureless input PC gives ONE giant
region (the degenerate end), the OPPOSITE of the value-flood, which fragments noise to
median-1.** PC reads real structure on natural frames (edge-fraction 0.23 – 0.54 at
Otsu / noise-floor) — it is not at its null there — but it reads that structure into the
giant-ground + tiny-fragment shape, not into few-and-large. **`0/100` was NOT copied
forward** — the speckle arm is distributional; the peer rung's **≈0.6% [0.17, 2.25]**
stands and no gate here asserts `== 0`.

---

## 3. THE FULL SWEEP — the value-flood's trade-off, in the wavefield

**C1, PC, nscale=3, the density ladder in full** (edge-fraction is the swept axis; the
verdict rides on the two §13-clean points, `noise0` and `otsu`):

| operating point | edge frac | regions/frame | enclosed median | all-region median | largest region (% frame) |
|---|---|---|---|---|---|
| d=0.02 | 0.02 | 1.0 | — | 5080 | **98%** (one blob — gappy contours leak) |
| d=0.05 | 0.05 | 1.3 | 3.0 | 4924 | 95% |
| d=0.10 | 0.10 | 2.0 | 1.5 | 4665 | 90% |
| d=0.15 | 0.15 | 5.2 | 4.0 | 6.0 | 84% |
| d=0.20 | 0.20 | 10.3 | 2.0 | 3.0 | 79% |
| **otsu** | **0.29** | **24.0** | **3.25** | **4.0** | **39%** |
| d=0.30 | 0.30 | 26.4 | 2.75 | 4.0 | 33% |
| d=0.40 | 0.40 | 36.3 | 3.0 | 3.8 | 20% |
| **noise0** | **0.54** | **38.5** | **2.0 [1.0, 2.25]** | 3.0 | 16% |
| d=0.50 | 0.49 | 39.6 | 2.0 | 3.0 | 17% |

**Read down the last two columns: the ground (largest region) falls from 98% to 16% of
the frame while the enclosed median never leaves 1.5 – 4.** This is the enclosure rung's
sentence verbatim, in a new representation: *"pass rate rises monotone with no knee while
the enclosed median is 1 at every rung; at one end it keeps the large ones and stops
selecting, at the other it selects and discards the large ones."* Here the two ends are
**gappy-contours-leak (one 98% blob)** and **dense-contours-fragment (median 2, 40
regions)**, and there is no threshold between them at which the typical enclosed region is
LARGE. C2 is the same shape (largest region 98% → 37%, enclosed median 1.75 – 3.5).

**The noise floor `noise0` is over-dense on natural frames** (edge-fraction 0.51 – 0.71 —
half the frame is "above the Rayleigh noise", because natural texture has real congruency
everywhere), so at `noise0` C1's enclosed median is **2.0 [1.0, 2.25]** — the CI TOUCHES 1.
`otsu` (0.23 – 0.33 edge-fraction) is the cleaner operating point and separates above 1.
**The two clean points disagreeing for C1 is the pre-registered AMBIGUOUS trigger** —
and it is diagnostic: it says natural-frame phase congruency is DENSE, exactly proviso (a)
I registered.

---

## 4. PHASE vs MAGNITUDE — the registered trap, measured

Enclosed-region median CI, PC (phase-congruency, contrast-invariant) vs LE (local energy
magnitude, contrast-dependent), Otsu, same pipeline:

| corpus | nscale | PC enclosed median | LE enclosed median | PC beats LE? |
|---|---|---|---|---|
| C1 | 3 | 3.25 [2.5, 4.0] | 2.00 [2.0, 2.2] | **yes** (CI-separated) |
| C1 | 4 | 6.25 [3.0, 7.0] | 2.00 [2.0, 2.5] | **yes** (clearly) |
| C2 | 3 | 3.00 [2.5, 4.0] | 3.00 [2.0, 3.5] | **no** (identical) |
| C2 | 4 | 5.00 [4.0, 8.8] | 4.75 [3.5, 7.0] | **no** (overlap) |

**PC's phase normalisation contributes something REAL but corpus-dependent and small:** on
the cartoon (C1) PC gives CI-separated larger regions; on live-action (C2) PC ≈ LE. The
all-region medians show PC consistently a little larger than LE (C1 4/8 vs 3/3; C2 9/12
vs 5.8/8) — contrast-invariance helps the tail. **But the HEADLINE (enclosed median) is
moved off 1 by LE alone**, so the median shift is not attributable to phase. **The one
place phase is decisively load-bearing is the NOISE FLOOR:** at `noise0`, LE > 0 is
trivially the WHOLE frame (edge-fraction 1.000, 0 regions), while PC's Rayleigh-derived
noise floor makes `PC > 0` meaningful — the phase normalisation is what gives PC a
principled zero. **That matters for the representation's well-posedness, not for the size
median.**

**So the trap fired in the informative direction:** I read PHASE (PC is a phase-alignment
measure by construction, not the position-blind power spectrum the trap warns of), and the
result is that phase is NOT what moves the median. The pre-registered NEGATIVE reading of
the magnitude arm applies to the headline.

---

## 5. WHICH REGISTERED OUTCOME OCCURRED

| criterion (§5, both `noise0` AND `otsu`, nscale=3) | measured | met? |
|---|---|---|
| enclosed median CI lower-bound > 1 | otsu: C1 2.5, C2 2.5 ✓; **noise0: C1 lo = 1.0 ✗**, C2 2.5 ✓ | **partial** |
| region count median ≥ 3 (a segmentation) | otsu 24.0 / 8.1 ✓ | ✓ |
| materially FEWER than value-flood | 48× / 205× fewer ✓ | ✓ |
| **PC beats LE** | C1 yes; **C2 no** | **✗** |
| non-degenerate (count > 2 at the operating point) | otsu yes; low-density end no | partial |

Two explicit AMBIGUOUS triggers fired: **`noise0` and `otsu` disagree for C1**, and
**PC ≈ LE for C2**. Per the pre-registered rule this is **AMBIGUOUS → build nothing; a
build needs a new prospective prereg.** It is neither a clean CONFIRM (the median move is
small, non-phase-specific, and the clean thresholds disagree) nor a clean FALSIFY (the
median DID move off 1, CI-separated at Otsu) nor a clean DEGENERATE (at Otsu the count is
8–24, not ≤ 2 — though the low-density end of the sweep IS the one-giant-blob degenerate).

---

## 6. WHAT ACTUALLY GATES IT — NAMED (the missing ingredient is CLOSURE, not the representation)

The value-flood fragments to median-1 because equal-value adjacency is DENSE (a boundary
at every quantizer step). Phase congruency changes the adjacency predicate from dense to
sparse — and the size distribution STILL does not reach few-and-large, for a NEW and
specific reason this sweep measured:

- **Phase-congruent contours are DENSE where there is texture** (edge-fraction 0.5+ at the
  noise floor) → the frame fragments to median 2 – 3 (proviso a, fired).
- **AND they are OPEN / GAPPY at object boundaries** → at low edge-density the flood LEAKS
  through the gaps and ONE region swallows 90–98% of the frame (proviso b, fired).
- There is **no threshold between these two failures** at which the typical enclosed region
  is object-sized. The wavefield representation reproduces the value family's
  **selectivity-vs-background trade-off**, one degree of freedom, no knee.

**The missing ingredient is contour CLOSURE / grouping, not the representation** — a
phase-congruent edge map is still a per-pixel LOCAL flag map, and this tree's own recorded
principle is that *"edges are grounded contours, transitive and decaying, MDL-gated,
refusing over-completion — a circle with a bit out isn't a discontinuous circle."* Neither
the value flood nor the wavefield closes contours; both either leak or over-cut. **A single
frame read as a static field — value OR wavefield — does not yield few-and-large; the
lever the object line has not tried is transitive contour grouping (closure), or the
motion/multi-frame evidence the pixel-seam and motion-energy rungs point to.**

---

## 7. §13 — WHERE THE NUMBERS CAME FROM

- **The `1` the median is compared against is the value-flood's OWN reproduced median**
  (enclosed median 1 [1,1] on the identical 30 frames), backed by the 5047/3978 floor
  asserted in-run. A measured incumbent result, not a chosen constant.
- **The two verdict thresholds FALL OUT:** `noise0` is the Rayleigh noise floor (the noise
  mean/sigma are the Rayleigh moments of the smallest-scale amplitude — Kovesi's derivation,
  not a picked number); `otsu` falls out of the PC histogram. The **edge-density ladder is
  an ENUMERATION** of the threshold axis, reported in full, none selected. **nscale is
  enumerated {3, 4, 5}**; the SHAPE of the result is invariant across it (medians 3–8, same
  giant-ground trade-off); nscale=5 is degenerate on a 72px frame (coarsest wavelength
  3·2.1⁴≈58px ≈ the frame) and reported as such.
- **Kovesi's filter-bank constants** (minWaveLength=3, mult=2.1, sigmaOnf=0.55, cutOff=0.5,
  g=10, k_noise=2.0) are the imported log-Gabor MECHANISM, declared **CONFIGURATION** — the
  same standing the motion-energy rung's DFT grid and `FIELD_W`/`DOT` had. The load-bearing
  quantity (the size median) is measured across the noise-floor / Otsu / density sweep and
  across nscale so no single filter constant is a verdict threshold. **This is the honest
  weak point of the rung (§8): the filter constants are Kovesi's defaults, not derived.**
- Seed audit: **`unknown_sinks: 0`, `ok: true`, none outside the block**; seeds resolved
  **114000–114100** (the 100 speckle fields + the bootstrap). `git diff -- seeds/ runners/`
  EMPTY — no Rust, no seed, no rule, no flag; byte-identity by construction (§9).

---

## 8. WHAT I GOT WRONG — in full

1. **MY HEADLINE PREDICTION (P6, ~55% CONFIRM) was WRONG in the informative direction.** I
   predicted the sparse phase-contour predicate would move the enclosed median to
   OBJECT-sized regions. It moved it to **~3 cells** and reproduced the value-flood's own
   giant-ground trade-off. **Both provisos I registered fired at once** — texture makes PC
   dense (fragments) AND object contours are gappy (leak) — and I did not foresee that they
   would fire in DIFFERENT regions of the SAME threshold sweep, which is exactly why there
   is no good operating point. Registering the provisos two-sided is the only reason I read
   this as AMBIGUOUS rather than narrating the Otsu 1→3 move as a CONFIRM.
2. **I nearly let the Otsu 1→3 move BE the headline.** The enclosed median IS CI-separated
   above 1 at Otsu, and the count DID collapse 48–205×. Taken alone that reads as "the wave
   representation moves the median — the finding of the object line." The magnitude
   comparator is what stops that: LE moves it off 1 too, so it is not phase — and the
   density sweep is what stops it further: the median never leaves single digits. **Had I
   measured only PC at only Otsu I would have published a CONFIRM.** The LE arm and the full
   density ladder were pre-registered precisely against this, and they earned their place.
3. **`noise0` was a worse operating point than I expected.** I registered `PC > 0` (above
   the Rayleigh noise floor) as a clean threshold-free anchor. On natural frames it labels
   **half the frame** as edge (real texture congruency is dense above noise), so it
   fragments and its median for C1 touches 1. It is still a legitimate §13-clean point and
   I report it — but the informative one is Otsu, and I should have anticipated that the
   raw noise floor is over-dense on textured natural input (the pixel-seam rung's own
   liveness curve says texture is everywhere).
4. **The filter-bank constants are Kovesi's defaults, not derived (§13 weak point).** I
   declared them configuration and measured robustness across nscale and the threshold
   sweep, but I did NOT derive mult / sigmaOnf / cutOff / g from anything in the frame. A
   stronger rung would derive the bandwidth from the frame's own spectral statistics. This
   is the honest residual, stated not buried; it does not change the verdict (the giant-
   ground trade-off holds across every nscale I ran).
5. **I fast-forwarded my worktree mid-task to pick up the motion-energy merge (index 179).**
   My worktree was created at `f893a19b7b` (before the motion-energy merge), so index 179 /
   the MotionEnergy docs were absent. I fast-forwarded to `e451d73208` to read the rung the
   brief told me licenses this one and to keep index 180 collision-free. Recorded rather than
   elided; the fast-forward changed no working-tree content of mine.

---

## 9. WHAT IS NOT SHOWN (§8)

- **NOTHING HERE SAYS THE PC REGIONS ARE OBJECTS OR NON-OBJECTS.** No region is inspected
  for content. The ~8–24 enclosed regions/frame at Otsu are not shown to be objects, and
  the giant ground region is not shown to be background.
- **ONE GRAIN (whole frame L=72), one video source, 30 frames/corpus.** Tiles (REGION=18)
  are too small for a 4-scale log-Gabor (coarsest wavelength ≈ 28px > 18) and were not run;
  L=72 is the aperture-free case the enclosure rung showed is where large regions would
  appear if anywhere.
- **MONOGENIC PC, one formulation.** The oriented `phasecong3` was not run; the finding is
  a claim about this monogenic segmentation, not about every phase-congruency variant.
- **NO CLOSURE / GROUPING was tested.** §6 names it as the missing ingredient by argument,
  not measurement — this rung measures only that the static wavefield field, like the static
  value field, does not close contours.
- **The filter-bank constants are not derived (§8/§13 above).**
- **NO TIMING CLAIM.** Every quantity is exact, counted, or a bootstrap over frames.

---

## 10. LEDGER ROW (for the supervisor to merge into `VISION_PROTOCOL.md`)

*Written here, not there — `VISION_PROTOCOL.md` is not this rung's file.*

| range | used for |
|---|---|
| **114000–114999 (seeds resolved 114000–114100 — 100 speckle fields + the bootstrap — unknown_sinks 0, none outside block)** | **PHASE-FIELD PROTO-OBJECTS — READING THE FRAME AS A WAVEFIELD MOVES THE ENCLOSED SIZE MEDIAN OFF 1, BUT ONLY TO ~3 CELLS, NON-PHASE-SPECIFICALLY, AND REPRODUCES THE VALUE-FLOOD'S GIANT-GROUND + TINY-MEDIAN TRADE-OFF. PRE-REGISTERED VERDICT AMBIGUOUS; BUILDS NOTHING (index 180 reserved, UNUSED).** Numpy-first characterisation of Kovesi MONOGENIC phase congruency (contrast-invariant phase-alignment; the wave transform the motion-energy rung proved CONSUMES THE RAW BOUNDED RASTER), whole frame L=72, 30 frames/corpus, unit=FRAME, vs the value-flood's enclosed median 1 [1,1] reproduced on the IDENTICAL frames (floor 5047/3978 asserted in-run, VOIDS otherwise). **AT OTSU (the §13-clean data-derived threshold): enclosed median C1 3.25 [2.5,4.0], C2 3.0 [2.5,4.0] — CI-SEPARATED ABOVE 1 — and the region count COLLAPSED 48× (C1) / 205× (C2): the FIRST lever in the object line to move the enclosed median at all, and genuinely FEWER.** **BUT NOT few-and-LARGE and NOT phase: (1) across the ENTIRE edge-density sweep (0.02→0.50) and nscale {3,4,5} the enclosed median stays SINGLE-DIGIT (2–9), never the object decade; (2) the largest region (ground) traverses 98%→17% of the frame while the enclosed median stands still — the value/aperture rungs' ONE-DEGREE-OF-FREEDOM-THAT-MOVES-THE-BACKGROUND, now in the wavefield representation, with the two failures being GAPPY-CONTOURS-LEAK (one 98% blob at low density) and DENSE-CONTOURS-FRAGMENT (median 2, 40 regions at high density), NO KNEE between; (3) THE MAGNITUDE TRAP FIRED — local ENERGY (contrast-dependent, no phase normalisation) reproduces the median shift at Otsu (C2 identical 3.0/3.0; C1 PC 3.25 beats LE 2.0 but C2 does not), so the median move is generic multi-scale CONTOUR segmentation, not PHASE. Phase is decisively load-bearing ONLY at the noise floor (LE>0 is trivially the whole frame; PC's Rayleigh-derived floor gives PC>0 a principled zero) — well-posedness, not the size median.** The two §13-clean operating points DISAGREE for C1 (Otsu separates above 1; the noise floor `PC>0` is over-dense on natural texture — edge-fraction 0.5+ — median 2.0 [1.0,2.25] touching 1) and PC≈LE for C2: two explicit pre-registered AMBIGUOUS triggers. **NAMED GATE: the missing ingredient is contour CLOSURE / transitive grouping, NOT the representation — a phase-congruent edge map is still a per-pixel LOCAL flag map; neither value nor wavefield closes contours, both leak or over-cut. A single static frame (value OR wave) does not yield few-and-large.** CONTROLS: uniform PC=0.0000 (dead arm fires); ideal disc → 2 regions median 2374 (instrument CAN produce large regions); speckle (100 fields, seeds 114000–114099) → ONE region/frame (structureless → no contours; the OPPOSITE of the value-flood's noise fragmentation; `0/100` NOT copied forward, peer ≈0.6% [0.17,2.25] stands). §13: the `1` is the value-flood's REPRODUCED median; thresholds are the Rayleigh noise floor and Otsu (both fall out); density ladder + nscale are ENUMERATIONS; Kovesi filter constants declared CONFIGURATION and robustness measured (honest weak point: not derived). WHAT I GOT WRONG: predicted CONFIRM (~55%) and BOTH provisos fired at once in different regions of ONE sweep (why there is no good operating point); I NEARLY let the Otsu 1→3 move be a CONFIRM headline — the pre-registered LE arm and full density ladder are what stopped it (had I measured only PC at only Otsu I would have published CONFIRM); `noise0` is over-dense on natural texture (worse anchor than expected); filter constants not derived; fast-forwarded my worktree to pick up the motion-energy merge (index 179) so index 180 is collision-free. FLOORS re-earned in-tree (5047/3978 exact, asserted in-run); provenance its own step (7 passed) + printed from inside the process, re-verified `e039d2eec2dd` post-measurement (`provenance_stable` True); oracle `scripts/rung7_vision_bench.sh` 222 passed / 0 failed (with `data/`) before AND after (zero seed/Rust/default changes → before==after by §9, `git diff seeds/ runners/` EMPTY); engine `e039d2eec2dd` **`own` — NO RUST ADDED.** |

---

## 11. NAMED NEXT LEVERS, each needing its own pre-registration

1. **CONTOUR CLOSURE / TRANSITIVE GROUPING — the lever this rung earns.** Both the value
   flood and the wavefield produce a per-pixel edge/region flag and then flood; neither
   CLOSES a contour. The tree's own "grounded contour" principle (transitive, decaying,
   MDL-gated, refusing over-completion) is the untested mechanism. A phase-congruent edge
   map is a GOOD input to closure (contrast-invariant, oriented) — the question is whether
   closure over it yields few-and-large where raw flooding does not.
2. **MULTI-FRAME, not a single static field.** The pixel-seam and motion-energy rungs both
   point out that a single bounded raster cannot express the structure objecthood needs;
   the object line has only ever measured single frames. Motion/temporal coherence is the
   evidence a static field lacks.
3. **DERIVE the filter bandwidth from the frame's spectrum** (§8 weak point) — mult /
   sigmaOnf from the image's own spectral statistics, so the representation carries no
   imported constant.
