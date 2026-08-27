# papers/ — the formal record

`formal/` holds the eight written preprints (LaTeX, theorem environments,
proofs, falsifiability sections). They are the **citable artefacts**, and they
do not disappear when the book is written: each book chapter carries a pointer
of the form *the formal statement is Paper N §M*, and the chapter drafts by
subtraction from them.

| file | title |
|---|---|
| `formal/01_law_of_graphic_equalisation_theory_referenced.tex` | The Law of Graphic Equalisation — Theory |
| `formal/01a_graphic_equalisation_physics_grounding.tex` | The Law of Graphic Equalisation — Physics Grounding (c, relativity, constants, the second law) |
| `formal/01b_graphic_equalisation_mind_and_self_grounding.tex` | The Law of Graphic Equalisation — Mind and Self Grounding (frames, the run/record, free will, personal identity, death) |
| `formal/02_seldon_manifolds_theory_referenced.tex` | Seldon Manifolds — Theory |
| `formal/02a_seldon_manifolds_psychological_grounding.tex` | Seldon Manifolds — Psychological Grounding (forward models, acceptable regions, the aperture of one embodiment) |
| `formal/03_law_of_narrative_momentum_theory_referenced.tex` | The Law of Narrative Momentum — Theory |
| `formal/04_narrativium_theory_referenced.tex` | Narrativium — Theory |
| `formal/05_constructive_graphic_equalisation_implementation_referenced.tex` | A Constructive Realisation of Graphic Equalisation |

`figures/` holds paper figures — **a committed generator script plus its
output**, never an output alone; the plan for all of them (papers and book
together) is `../book/FIGURES.md`. Paper 02 currently includes two figures. Five
further bodies are built but included by no paper (`fig01_boundary`,
`fig01_collapse_dynamic`, `fig03_narrative_momentum`, `fig04_horizon`,
`fig05_executor_round`) — wiring those in is the first gap to close.

## Version

All eight carry the same draft string in three places — the title block, a boxed
notice under the title, and the footer of every page:

> **`draft-2026-08-27`** · 27 August 2026

They are circulated for comment, not as finished results. **Bump all eight
together**, so a reader comparing two papers is never comparing two drafts, and
keep the string identical across the title, the notice and the footer. The
version is deliberately a date rather than a number: these papers are revised in
response to measurement, and a date says when the claims were true of the
substrate.

**A number would be a fiction, and here is the specific reason.** There are
files outside this directory named `law_of_graphic_equalisation_recursive_v1`
through `v22`, and it is tempting to read them as the paper's revision history.
They are not. Every one of them carries a modification time inside a two-day
window (20–21 August 2026): they are one rewriting session's intermediate saves.
The paper's actual history is much longer — on the author's own account, in the
hundreds of revisions — and it runs through differently-named documents in
several places, none of which shares a numbering scheme with any other.

So there is no continuous count to continue, and inventing one would assert a
history that no artefact records. The date says the one thing that is true and
checkable: when these claims were true of the substrate.

> **Standing note, third instance.** This is the third time in this work that
> provenance was inferred from a filename and was wrong — after
> `eye_timing/scaling.png` (filed as an FFI-wall plot on the strength of its
> name) and `per_area_settlement.png` (read as a town figure; "settlement" meant
> *settling*). The rule generalises past figures: **an artefact's history cannot
> be read off its filename.** `v22` is not the twenty-second version any more
> than `scaling.png` was the scaling result.

## Reading aperture

These papers are narrow by design and should be, but the design has a cost worth
knowing. The components used here are individually established and are cited as
such, so a reader evaluating each part against its own field's standard will
find each one known or borrowed and will be locally correct every time. **The
claim is the arrangement**, and it is not reachable that way — which is why
paper 01 now carries a composition claim and its own falsifier before the
component ones.

**The book in `../book/` is the wide aperture on the same work**, not a
plain-language edition of it. A reader who takes only the papers gets the
multiset.

**The book being built from these papers lives in `../book/`.** Start at
`../book/README.md`.

## Building

Compile **from inside `formal/`**, not with `-output-directory`:

```
cd papers/formal && pdflatex 02_seldon_manifolds_theory_referenced.tex
```

Paper 02 `\input`s its figures by relative path (`../figures/fig02_*-body`), so
`-output-directory` changes how those paths resolve and the build silently
produces no PDF for that paper while the other six succeed. Found the obvious
way: a batch loop reported four papers and should have reported five.
