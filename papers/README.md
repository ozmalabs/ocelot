# papers/ — the formal record

`formal/` holds the twelve written preprints (LaTeX, theorem environments,
proofs, falsifiability sections). They are the **citable artefacts**, and they
do not disappear when the book is written: each book chapter carries a pointer
of the form *the formal statement is Paper N §M*, and the chapter drafts by
subtraction from them.

## The shape of the set

**Two premises, and what they force.** Paper 00 claims one thing — *to be is to
stand in relation*. The companions admit one more — that anything *happens* —
which 00 says is not required for there to be anything, so it is a real addition
and it is not derived: **The account carries two unpaid entries, not one** — that there is anything, which 00 claims and
nothing here grounds, and that anything happens. Neither follows from the other, and an earlier
version of this section located the single unpaid entry at the second.

**Forced by the admission:** transformation `r`. Something has to do the happening,
whatever does it is a graph, and the least graph that can do anything is a pattern
plus a change it makes. Admissibility comes with it — `Γ` names the rules that
decide admit-or-residual.

**Postulated, and both restored by audit after being folded away** — the second of
them three times: a **realisation
operator** (collapse is typed as a map out of `Poss`, and the physics grounding's
measurement account needs exactly one continuation realised), and a
**destroy/preserve distinction** (`prop:economics` exempts evaluation because it
*preserves*, so the operative criterion is that a change which *destroys* costs).

**Axiom −1 is split.** In paper 01 every use refuses an import — no frame-free
denominator, no absolute threshold — which is a discipline, not a place that paper
can fail. In the **groundings** it licenses positive results and is a commitment
that can fail; 04 already locates its exposure in its own falsifier. Guard here,
commitment there.

**A third tier** sits between postulate and consequence: four hypotheses, including
the Law of Graphic Equalisation itself, plus the near-uniqueness of the cheap cut.
Bets, neither assumed nor derived.

**How to read the count.** These reductions are re-descriptions — *X is a special
case of Y* — and the criterion licensing them applies to anything the account
posits, so a count driven to zero would be a theorem of the vocabulary rather than
a measurement. **The two restorations are worth more than the folds were.** What a
surviving re-description buys is narrower: two things cannot be varied
independently, which constrains what a grounding may do. It does not reduce the
number of ways the account can be wrong.

The full ledger is `rem:inherited` in paper 01, kept to about 900 words so it can
be checked at a glance; its revision history is in the review record rather than in
the paper.

| file | title |
|---|---|
| `formal/00_is.tex` | Is — the single claim, its method, and the case for it |
| `formal/01_law_of_graphic_equalisation_theory_referenced.tex` | The Law of Graphic Equalisation — Theory |
| `formal/01s_graphic_equalisation_statement.tex` | The Law of Graphic Equalisation — Statement (generated from 01 via `01s.spec`) |
| `formal/01a_graphic_equalisation_physics_grounding.tex` | The Law of Graphic Equalisation — Physics Grounding (c, relativity, constants, the second law) |
| `formal/01b_graphic_equalisation_mind_and_self_grounding.tex` | The Law of Graphic Equalisation — Mind and Self Grounding (frames, the run/record, free will, personal identity, death) |
| `formal/02_seldon_manifolds_theory_referenced.tex` | Seldon Manifolds — Theory |
| `formal/02a_seldon_manifolds_psychological_grounding.tex` | Seldon Manifolds — Psychological Grounding (forward models, acceptable regions, the aperture of one embodiment) |
| `formal/03_law_of_narrative_momentum_theory_referenced.tex` | The Law of Narrative Momentum — Theory |
| `formal/04_narrativium_theory_referenced.tex` | Narrativium — Theory |
| `formal/A1_constructive_graphic_equalisation_implementation_referenced.tex` | A Constructive Realisation of Graphic Equalisation |
| `formal/05_frames_relation_and_the_empty_limit.tex` | Frames, Relation, and the Empty Limit |
| `formal/06_assessing_an_account_of_this_kind.tex` | Assessing an Account of This Kind (the process material, split out of 01) |

`01s` is **generated**, never hand-edited: edit `01s.spec` and the long paper,
then `python3 ../../tools/build_statement.py 01s.spec` from `formal/`. The
generator exits non-zero on a dead `@pull` label and lists every labelled block
the spec does not pull, so material added to 01 surfaces as a review item
instead of silently diverging.

`figures/` holds paper figures — **a committed generator script plus its
output**, never an output alone; the plan for all of them (papers and book
together) is `../book/FIGURES.md`. Paper 02 currently includes two figures. Five
further bodies are built but included by no paper (`fig01_boundary`,
`fig01_collapse_dynamic`, `fig03_narrative_momentum`, `fig04_horizon`,
`fig05_executor_round`) — wiring those in is the first gap to close.

## Version

All twelve carry the same draft string in three places — the title block, a boxed
notice under the title, and the footer of every page:

> **`draft-2026-08-30.4`** · 30 August 2026

**The bump is checked, not trusted.** `python3 tools/check_draft_consistency.py`
verifies that all twelve are on one draft string, that no file mixes two, and
that each document's per-page footer and boxed DRAFT notice carry the same
revision as its title block. It exits non-zero on any finding. Each of those
three defects has actually occurred: on the `.4` bump, paper 01's footer and
notice still read `r152` while its title block read `r155` (three revisions of
drift, because the footer is a separate hand-maintained site), and 00 and 07
had no footer or notice at all despite this section claiming all of them do.

They are circulated for comment, not as finished results. **Bump all twelve
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
produces no PDF for that paper while the others succeed. Found the obvious
way: a batch loop reported fewer papers than it should have.
