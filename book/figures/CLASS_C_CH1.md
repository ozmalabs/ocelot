# Class C selection — chapter 1 (The Eye)

Figures that **already exist** under `results/` and should be *selected,
captioned and cited* rather than redrawn. Five selected, one rejected, each
with its provenance document and its committed generator.

> **A finding this selection produced, and it changes the rule.**
> **No PNG under `results/` is tracked by git** — `git ls-files 'results/**.png'`
> returns **zero** of the ~110 present. They are working artefacts of runs, not
> committed evidence. So a Class C figure cannot simply be *referenced by path*
> in a manuscript: the path may be empty on any other machine, including a
> future one of this author's.
>
> **Therefore Class C inherits the Class B rule rather than being exempt from
> it:** a selected figure is admissible only if a **committed generator** can
> remake it. All five below satisfy that (their generators are tracked in
> `scripts/`); the one rejection is rejected on legibility, not provenance.
> When a chapter is typeset, the selected PNG gets copied into
> `book/figures/selected/` **and committed**, with the generator named beside
> it — not linked into `results/`.

---

## Selected

### C1 — the accelerated path is near-linear
**File** `results/eye_accel/scaling.png` ·
**Generator** `scripts/eye_accel_measure.py` ·
**Provenance** `VISION_EYE_ACCEL_{PREREG,RESULTS}.md`

Per-tick cost against cells, log–log, two arms: the graph path at fitted
exponent **1.838** and the accelerated path at **1.072** — an exponent *drop*
of 0.765 against a pre-registered threshold of ≥ 0.4, with the accel arm gated
at ≤ 1.3.

**Caption to use.** *The cost of seeing, against the number of cells it sees
with. The upper arm is the graph path; the lower is the same computation with
the boundary bulked. The claim is the SLOPE, not the offset: 1.838 → 1.072 is
the difference between a cost that grows faster than the retina and one that
grows with it. The results document is careful that this is an O(cells) floor,
not sub-linear magic.*

**Why this one and not the other scaling plot:** this is the figure for
chapter 1's claim that *the wall is the boundary, not the arithmetic*.

### C2 — pruning removes the accumulation, not just the constant
**File** `results/eye_timing/scaling.png` ·
**Generator** `scripts/eye_timing_measure.py` ·
**Provenance** `VISION_EYE_TIMING_{PREREG,RESULTS}.md`

Two panels: per-tick cost vs cells (exponents 2.032 vs 1.825 — a modest
difference), and per-tick cost vs **tick index** at fixed size, where the
unpruned arm climbs (cumulative exponent 2.266) and the pruned arm is flat
(0.775).

**Caption to use.** *The left panel looks like a small win. The right panel is
the actual result: without pruning, each tick costs more than the last — the
eye slows down the longer it looks. Flatness in the right panel is the
property that matters, and it is not visible in the left one at all.*

**Note for the writer:** an earlier draft of `FIGURES.md` assumed this was the
FFI-wall figure (1317 → 137.8 ms). **It is not** — that was an assumption made
from the filename, corrected by opening it. The FFI figure has no committed
plot; if chapter 1 wants one it must be generated.

### C3 — held reconstruction, with the control that makes it a result
**File** `results/doom_eye/curves.png` ·
**Generator** `scripts/doom_eye_measure.py` ·
**Provenance** the doom-eye rung in `docs/research/doom/` and
`VISION_DOOM_CARVE_SCALE_RESULTS.md`

Left: normalized error against true luminance on a real Doom frame, for an
accumulating held surface (falls smoothly), a stateless single-tick reading
(flat), and a **scrambled-order control** (stays high and erratic). Right: the
cost bend — per-tick work drains to zero on a static scene, rises through
motion, drains again.

**Caption to use.** *Three readers of one stream. The accumulating held surface
falls smoothly; the scrambled-order arm is why that is a claim rather than a
curve, since the same frames in the wrong order do not accumulate; and the
**stateless reader is flat**. That flat line is the chapter's argument about
what a change-detecting eye obliges everything downstream to be: a difference
cannot be read without the thing it differs from, so a reader with no held base
extracts nothing, however good the diffs are. Right: work follows surprise. A
static scene costs nothing to keep looking at, which is the same fact the fading
figure states from the other side.*

**Note for the writer:** this figure was originally selected as a result about
accumulation. It is better read as the measurement behind the obligation to
generate — chapter 5's third argument for analysis-by-synthesis, in chapter 1's
own data.

### C4 — the eye goes blind to a static scene
**File** `results/doom_eye/contact_sheet.png` ·
**Generator** `scripts/doom_eye_measure.py` · same provenance as C3

Ten held reconstructions across ticks, each labelled with its change count `C`:
300 at t=1, **0 by t=20 with the scene unchanged**, rising again through
motion, draining again after.

**Caption to use.** *A pure change detector must move to see. Held for twenty
ticks on an unchanging scene, the eye's work count reaches zero — it has
nothing left to report. This is why the fixational drift is load-bearing rather
than decorative, and it is the same convergence the event-camera field reached
when it reinvented the microsaccade.*

**Pair it with EYE-1 and EYE-4.** These three are one argument.

### C5 — holes stay holes
**File** `results/eye_view/net_vs_eye.png` ·
**Generator** `scripts/eyeview_render.py` ·
**Provenance** `VISION_OVERLAY_RESULTS.md` (four pre-registered faithfulness
gates, all passing)

The eye's own output — boxes on 97.2% of the field, labels on 28.1%, the hole
carrying neither — beside a selection head that labels everything, including
the hole. Label-coverage gap **71.9 pp**.

**Caption to use, and the wording is not optional.** *Left: the eye's output.
It carves boxes where it has extent and names them only where a name is
grounded, so two surfaces are seen-but-unnamed and the hole carries neither box
nor label. **Right: an ILLUSTRATION of a selection head, drawn to show the
contrast — it is not a measured baseline, and no network was run.** The point
is structural: a head that must choose among fixed classes cannot return
"nothing here."*

> **This caption is a test of the book's own discipline.** The right-hand panel
> is a mock-up. The source document labels it as one, in capitals, twice. Any
> caption that lets a reader take it for a benchmark result would be the exact
> defect chapter 15 catalogues — a number standing where no measurement was
> made. If the caption cannot carry the caveat in the space available, cut the
> panel and keep the left half.

---

## Rejected

### `results/efference_egomotion_imgs/h1_scene_raw_vs_efference.png`
Three unlabelled panels of a synthetic scene. Legible only next to its own
results document, and a book figure has to stand on its caption. **Rejected on
legibility, not on evidence** — if chapter 1 wants the efference-copy point,
the figure should be regenerated with panel labels rather than shipped as is.

---

## Not available as Class C

- **The FFI wall** (75–82% of a tick at the boundary; fovea 1317 → 137.8 ms).
  Quoted in `THE_EYE.md` §5, no committed plot found. Class B if wanted.
- **Lid-suture worse than dark** (−0.1458). No plot located.
