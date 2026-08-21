# FIGURES — the plan for the papers and the book

**Status: plan, with twelve figures drawn.** Chapter 1's set is complete
(eight, plus a Class C selection); paper 01's set is complete; paper 05 and the
book's two most-cited conceptual diagrams are drawn. See § "Built so far". The five formal papers currently
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
**Chapter 1's selection is done: `book/figures/CLASS_C_CH1.md`** (five
selected, one rejected, each with provenance and generator).

**One rule changed as a result of doing it.** `git ls-files 'results/**.png'`
returns **zero** — none of those ~110 PNGs is tracked. They are run artefacts,
not committed evidence, so a Class C figure cannot be referenced by path in a
manuscript: the path may be empty on any other machine. **Class C therefore
inherits the generator rule rather than being exempt from it** — a selected
figure is admissible only if a committed script can remake it, and when a
chapter is typeset the PNG is copied into `book/figures/selected/` and
committed, with its generator named beside it.

Remaining candidates for later chapters: `results/held_surface/`,
`results/splat_over_time/` (contact sheets of a belief forming over time),
`results/doom_ingraph_map/map_frame_*.png` (ch. 7),
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

## Built so far

| id | figure | file | generator | source data |
|---|---|---|---|---|
| **PAPER-01-1** | the collapse dynamic | `papers/figures/fig01_collapse_dynamic.pdf` | `fig01_collapse_dynamic.tex` (+ `-body.tex`, `\input`-able into the paper) | — (conceptual) |
| **PAPER-01-2** | the situated graph and its boundary | `papers/figures/fig01_boundary.pdf` | `fig01_boundary.tex` (+ `-body.tex`) | — (conceptual) |
| **PAPER-05-1** | one synchronous executor round | `papers/figures/fig05_executor_round.pdf` | `fig05_executor_round.tex` (+ `-body.tex`) | — (conceptual) |
| **SD-1** | the growth ladder, Occam-ordered | `book/figures/sd_1_ladder.svg` | `fig_sd_ladder.py` | — (conceptual) |
| **FR-1** | in-frame integer, cross-frame continuum | `book/figures/frame_1_invariant.svg` | `fig_frame_invariant.py` | — (conceptual) |
| **EYE-1** | Troxler fading, replicated | `book/figures/eye_1_troxler.svg` | `fig_troxler_fade.py` | `results/troxler_confirm.json` |
| **EYE-2** | illumination invariance, log vs linear | `book/figures/eye_2_invariance.svg` | `fig_eye_invariance.py` | `results/eye_confirm.log` (H1) |
| **EYE-3** | Weber–Fechner, predicted then measured | `book/figures/eye_3_weber.svg` | `fig_eye_weber.py` | `results/eye_confirm.log` (H2) |
| **EYE-4** | the drift crossover, and its ablation | `book/figures/eye_4_drift.svg` | `fig_eye_drift.py` | `results/eye_confirm.log` (H3) |
| **EYE-5** | depth and stereo: the refusal matrix | `book/figures/eye_5_depth_controls.svg` | `fig_eye_depth_controls.py` | `results/depth_measure.json`, `results/stereo_measure.json` |
| **EYE-6** | centre-surround, emerged from a zero init | `book/figures/eye_6_centre_surround.svg` | `fig_eye_centre_surround.py` | `results/rung7_confirm.log` |
| **EYE-7** | the waves: globally isotropic, locally oriented | `book/figures/eye_7_waves.svg` | `fig_eye_waves.py` | `results/waveiso_confirm.json` |
| **EYE-8** | the eigenspectrum — why Oja cannot see it | `book/figures/eye_8_eigenspectrum.svg` | `fig_eye_eigenspectrum.py` | `results/waveiso_confirm.json` |
| **EMO-1** | the marshmallow confound, both directions | `book/figures/emotion_1_marshmallow_confound.svg` | `fig_marshmallow_confound.py` | `results/marshmallow_delay/results.json` |
| **EMO-2** | Harlow on equal drive weights | `book/figures/emotion_2_harlow.svg` | `fig_harlow_preference.py` | `results/harlow_d1.json` |

`book/figures/eye_confirm.py` parses `results/eye_confirm.log` — the eye's
confirmatory block (prereg committed **before** the run, seeds 11000–11999,
n=12) — and three figures read it. Means, CI95s and percentages are taken as
recorded; nothing is recomputed.

**Toolchain, chosen deliberately.** There is no matplotlib in this tree, and
adding a plotting dependency to draw twenty figures is a worse trade than
`book/figures/svgplot.py` — ~250 lines of stdlib emitting vector SVG. Figures
are theme-aware (one render reads correctly on paper and on a dark screen),
have no install step, and diff as text. Paper diagrams are TikZ, so they live
in the `.tex` source and set their type in the paper's own font.

Preview a figure while drafting:

```
google-chrome --headless --disable-gpu --screenshot=/tmp/f.png \
  --window-size=800,600 --default-background-color=FFFFFFFF book/figures/<f>.svg
pdflatex papers/figures/fig01_collapse_dynamic.tex   # paper diagrams
```

**Two errors this pass caught, both worth recording** because they are the
figure-side versions of defects this project already catalogues:

1. **EYE-1 first draft plotted `μ_endo` on a contrast axis.** μ_endo is a
   per-cell *response* setpoint; contrast fades to zero *because* every cell
   arrives at it. Plotting it as a contrast value was a category error of
   exactly the "number in the wrong frame" kind — caught by rendering the
   figure and reading it, not by any check. The redraw puts `μ_endo` on its own
   response axis beside `stab_mean_resp_final`, where the two coincide, which
   is the actual mechanism.
2. **PAPER-01-1 first draft drew the unrealised candidates as arrows into
   `G_{t+1}`**, implying they contribute to the successor. They do not — that
   is the whole content of collapse. They now terminate in `×`, labelled
   *admissible, not realised*.

**A third error, caught the same way, during the Class C pass:** `FIGURES.md`
listed `results/eye_timing/scaling.png` as the FFI-wall plot on the strength of
its filename. Opening it showed a **prune ablation** instead — a different and
more interesting result (without pruning, each tick costs more than the last),
but not the one it had been filed as. The FFI wall has no committed plot at
all. *A figure identified from its filename is an unread figure.*

**The rule these suggest, added to the ones above:** *render every figure and
read it before believing it.* A figure is an instrument, and this tree's own
standing lesson is that instruments need positive controls too.

## Order of work

1. ~~Paper 01's collapse diagram~~ — **done** (PAPER-01-1).
2. ~~Class B ch. 1 figures~~ — **done** (EYE-1 … EYE-5). The Weber and drift
   data turned out to be traceable after all: `results/eye_confirm.log` holds
   H1–H4 with CI95s and, crucially, the ablated and linear control arms.
   Remaining ch. 1 gaps, both needing their data located first: the
   centre-surround emergence figures (CS 1.0839, σ_ON,ON 1.627 vs σ_ON,OFF
   3.264) and retinal-wave structure (entropy 0.195 vs 0.000), and the
   DC-blob eigenspectrum behind the cortex null — **all three located and
   drawn** (EYE-6, EYE-7, EYE-8). The scaling wall (1317 → 137.8 ms) already
   has a plot in `results/eye_timing/scaling.png` (Class C — select, don't
   redraw), which closes chapter 1's figure set.
3. Paper conceptual diagrams — **paper 01 is complete** (collapse dynamic,
   boundary; the residual-delta figure folded into the collapse diagram rather
   than drawn separately, since it is the same arrow) and **paper 05's
   executor round is drawn**. Remaining: paper 02's shape tube and reachability
   compression, paper 03's narrative dimension, paper 04's budget and horizon —
   all four are THEORY figures and must be captioned as such, per the
   no-figure-of-an-unbuilt-mechanism rule below.
4. Book conceptual diagrams — **SD-1 (the ladder) and FR-1 (the frame
   invariant) are drawn**, the two that the most chapters cite. Remaining:
   shape-vs-rule (ch. 3), the two unbounded axes (ch. 2 + epilogue), the
   introduction's ten-box chain, and the part-structure page.
5. ~~Class C selection for chapter 1~~ — **done**
   (`book/figures/CLASS_C_CH1.md`). Class C selection for the remaining
   chapters, while drafting each.

**Where the eye's remaining data was hiding.** `THE_EYE.md` §1 states the
centre-surround and retinal-wave numbers without citing a path, and the two
sit in different places: centre-surround in `results/rung7_confirm.log` (the
one pre-registered confirmatory run, η frozen, Bonferroni across five tests),
and the waves in `results/waveiso_confirm.json` with committed runners
`scripts/waveiso_{lib,calibrate,pilot,confirm}.py`. Both turned out to be
richer than the summary line suggested — rung 7 carries Miller's
spatial-dependence reading and Atick & Redlich's SNR predictions as separate
gated hypotheses, and waveiso carries four control arms plus full per-seed
eigenspectra, which is what made EYE-8 possible at all.

**A note on what the eye data supports.** `depth_measure.json` and
`stereo_measure.json` record verdicts and minted-dimension structures rather
than dense curves — so those figures are *control matrices* (what minted, what
refused, 0/400 on shuffle), not scatter plots. That is the honest shape for
them: the claim in both cases is about refusal to hallucinate.
