# papers/ — the formal record

`formal/` holds the five written preprints (LaTeX, theorem environments,
proofs, falsifiability sections). They are the **citable artefacts**, and they
do not disappear when the book is written: each book chapter carries a pointer
of the form *the formal statement is Paper N §M*, and drafts by subtraction
from them.

| file | title |
|---|---|
| `formal/01_law_of_graphic_equalisation_theory_referenced.tex` | The Law of Graphic Equalisation — Theory |
| `formal/02_seldon_manifolds_theory_referenced.tex` | Seldon Manifolds — Theory |
| `formal/03_law_of_narrative_momentum_theory_referenced.tex` | The Law of Narrative Momentum — Theory |
| `formal/04_narrativium_theory_referenced.tex` | Narrativium — Theory |
| `formal/05_constructive_graphic_equalisation_implementation_referenced.tex` | A Constructive Realisation of Graphic Equalisation |

`figures/` holds paper figures — **a committed generator script plus its
output**, never an output alone. None are drawn yet; the plan for all of them
(papers and book together) is `../book/FIGURES.md`. The papers currently
contain zero figures, which that document treats as the first gap to close.

## Version

All five carry the same draft string in three places — the title block, a boxed
notice under the title, and the footer of every page:

> **`draft-2026-08-24`** · 24 August 2026

They are circulated for comment, not as finished results. **Bump all five
together**, so a reader comparing two papers is never comparing two drafts, and
keep the string identical across the title, the notice and the footer. The
version is deliberately a date rather than a number: these papers are revised in
response to measurement, and a date says when the claims were true of the
substrate.

Note that paper 01 has an older, separate `v1`–`v22` lineage outside this
directory (`~/law_of_graphic_equalisation_recursive_v*.tex`). The date string
does not continue that numbering and is not meant to.

**The book being built from these papers lives in `../book/`.** Start at
`../book/README.md`.
