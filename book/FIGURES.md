# FIGURES — the plan for the papers and the book

**Status: plan. Nothing here is drawn yet.** The five formal papers currently
contain **zero figures** (no `includegraphics`, no TikZ), and the book has none
because it has no chapters yet. This document says what each needs, where the
data for it already lives, and the one rule that governs all of them.

Homes: `papers/figures/` (paper figures), `book/figures/` (book figures).

---

## The rule: a figure is a committed generator plus its output

This tree already holds the discipline in two places and the figures inherit
it. `THE_EYE.md`'s retraction 3 — *"an uncommitted runner means the result is
not a result"* — extends exactly: **an uncommitted generator means the figure
is not evidence.** And `~/ozmadev/internal/research/docs/figures/` already
works this way: every `*.png` sits beside the `*.py` that made it.

Therefore, for every data figure:

1. A committed script under `papers/figures/` or `book/figures/`, named for the
   figure, reading **only** from a committed results path.
2. Its output committed beside it (`.png` for raster, `.svg`/`.pdf` where the
   figure is line art).
3. A one-line caption stating the source data path and the N.
4. **No figure may re-derive a number.** If the plot disagrees with the results
   document, the results document is right and the script is broken — the
   figure reads, it does not recompute.

Conceptual diagrams (no data behind them) are exempt from 1–3 but not from
honesty: a diagram that implies a mechanism that isn't built is a claim, and
gets the same "named, not faked" treatment as prose.

---

## Class A — conceptual diagrams (the papers need these most)

The formal papers are dense prose with no visual anchor at all. Each needs a
small number of line diagrams, in TikZ so they live in the `.tex` source.

| paper | figure | shows |
|---|---|---|
| **01** | the collapse dynamic | `G_t → 𝒫(G_t) → 𝒞_t → G_{t+1}`, with the realised successor becoming the next antecedent. **The single most load-bearing diagram in the whole programme** — it is the book's opening idea too. |
| **01** | the situated graph and its boundary | world-caused change entering without Γ veto; frame-relative termination |
| **01** | residual as a delta | proposal image vs realised image, the four-way difference |
| **02** | the shape tube | a time-indexed manifold with width, and `wait` / `refine` / `commit` projections measured against it |
| **02** | reachability compression | the tube narrowing as commitment accumulates |
| **03** | narrative as a dimension | history as first-class axis; momentum; revision cost as displacement |
| **04** | the budget and the horizon | narrativium expenditure, feasibility boundary, the horizon |
| **05** | one executor round | antecedent base → positive frontier → typed proposal effects → deterministic merge → boundary execution, with the same-round non-readability barrier marked |
| **05** | removal/freshness stratification | why removal is stratified |

Book-side conceptual diagrams (SVG, drawn once, reused):

- **The four-rung Occam ladder** — recognise → transform → infer dimension →
  mint. Needed by ch. 4 and referenced by ch. 1, 5, 7, 8.
- **The frame invariant** — in-frame integer lattice, cross-frame continuous
  map, the continuum sitting in `Hom(frame, frame)`. Ch. 2.
- **Shape vs Rule, the two axes** — execution vs acquisition. Ch. 3.
- **The two unbounded axes** — extensive frontier vs intensive refinement.
  Ch. 2, reused by the epilogue.
- **The book's own part structure** — one page in the front matter.
- **The introduction's chain** — meeting → KVMA → one map → model protocol →
  the collision → Γ → no LLM → collapse → residual. Ten boxes, one line each.

## Class B — data figures that already have their data and no plot

These are the highest-value figures in the book, and every one of them has
committed results sitting unplotted. **This is the first drawing work to do.**

| book ch. | figure | data |
|---|---|---|
| **1** | Troxler fade: stabilised vs drifting, fade to setpoint while 100% alive | `results/troxler_confirm.json` |
| **1** | the two independently-derived timescales, 53× apart (`τ_drift = 3`, `τ_adapt = 160`) | same, plus `THE_EYE.md` §4 |
| **1** | Weber–Fechner fit (0.9991) and the invariance gap (0.44% log vs 100% linear) | vision results behind `THE_EYE.md` §1 — **locate before drawing** |
| **1** | the drift walk's α crossover (1.1553 / 0.7590 against 0.79±0.11) | the drift measurement behind §1 |
| **1** | depth from velocity *variation* — and the flat-scene control minting nothing | `results/depth_measure.json`, `results/depth_from_motion.json` |
| **1** | stereo: N=2 vs N=3, and N=3 rejecting what N=2 hallucinates | `results/stereo_measure.json`, `results/two_eye_k0dom.json`, `results/assembled_eye_neyes.json` |
| **1** | the DC-blob eigenspectrum — why the cortex path is arithmetic, not tuning | the H1 null's spectrum data |
| **1** | scaling: the FFI wall, 1317 → 137.8 ms | `results/eye_timing/scaling.png`, `results/eye_accel/scaling.png` (**exist**) |
| **5** | the Omniglot arc as a trajectory with intervals — including the run-15 correction and the run-16 jump | `results/` run logs |
| **7** | surprise 1.0 → 0.0 in lockstep with model accuracy → 1.0 | ls20 results |
| **10** | Harlow: approach preference under equal drive weights, N=200/condition | `results/harlow_d1.json` |
| **10** | marshmallow: temperament vs reliability-prior, both effects, confound in both directions | `results/marshmallow_delay/results.json` |
| **10** | mood as momentum + set-point | `results/mood_r1/`, `mood_r1b/`, `mood_r1c/` (**plots exist**) |
| **11** | psychosis: both native forms + confirmer, against matched control | `results/psychosis_demo/psychosis_demo.png` (**exists**) |
| **11** | seizure model | `results/seizure_engine_figure.png`, `results/seizure_v2_figure.png` (**exist**) |
| **12** | the fifteen rungs as one table-figure, each with its control and its interval | the rung RESULTS docs via `ABUSIVE_RELATIONSHIPS_LINE_SUMMARY.md` |
| **13** | desire paths forming — before/after wear | bigville (external repo) |
| **15** | the 60 count-divided learners across 8 seeds; 159/634 seeds with zero productions | `SHAPE_AUDIT.md`, the census docs |

## Class C — figures that already exist and need only selection

~110 PNGs under `results/`. Do not redraw these; pick, caption, and cite.
Strongest candidates: `results/doom_eye/contact_sheet.png` and
`doom_eye/curves.png` (prologue), `results/eye_view/*` (ch. 1),
`results/held_surface/`, `results/splat_over_time/` (contact sheets showing a
belief forming over time), `results/doom_ingraph_map/map_frame_*.png` (ch. 7),
`results/cascade_ink/reconstruction.png` (ch. 5),
`results/staleness_decay/power_law.png`, `results/modulator_emergence/`.

---

## Two things the figures must not do

1. **No figure without its interval**, where the underlying claim has one. A
   bar chart of point estimates is exactly the defect run 15 corrected — five
   deltas that were noise. Error bars are not decoration here; they are the
   finding.
2. **No figure of a mechanism that isn't built.** Paper 02's tube diagram is a
   *theory* figure and must be captioned as one, because the composition that
   would make it measurable does not exist yet (`future_manifold.rs` ×
   `admissible_moves`). Drawing it as if it were instrumented would be the
   defect ch. 15 catalogues, in picture form.

## Order of work

1. **Paper 01's collapse diagram** — one figure, used by a paper and the book.
2. **Class B ch. 1 figures** — the eye's data is committed and unplotted, and
   ch. 1 is the first chapter drafted.
3. The remaining paper conceptual diagrams, as each paper is revised.
4. Class C selection, per chapter, while drafting.
