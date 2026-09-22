# papers/ — the formal record

`formal/` holds 27 formal documents: LaTeX preprints with theorem environments,
proofs, and falsifiability sections. They are the **citable artefacts**, and
they do not disappear when the book is written: each book chapter carries a
pointer of the form *the formal statement is Paper N §M*, and the chapter drafts
by subtraction from them. `01s` is the generated formal statement associated
with the long Paper 01.

## Writing standard

[`WRITING_STANDARD.md`](WRITING_STANDARD.md) is the shared communication
standard for the formal papers, book, outreach, and editorial prose. It makes
coherence and reader-pathing explicit while preserving the distinct formal and
narrative registers; `../book/BOOK_VOICE.md` supplies the book-specific
contract.

## The shape of the set

**Two premises, and what they force.** Paper 00 claims one thing — *to be is to
stand in relation*. The companions admit one more — that anything *happens* —
which 00 says is not required for there to be anything, so it is a real addition
and it is not derived: **The account carries two unpaid entries, not one** — that
there is anything, which 00 claims and nothing here grounds, and that anything
happens. Neither follows from the other, and an earlier version of this section
located the single unpaid entry at the second.

**Forced by the admission:** transformation `r`. Something has to do the
happening, whatever does it is a graph, and the least graph that can do anything
is a pattern plus a change it makes. Admissibility comes with it — `Γ` names the
rules that decide admit-or-residual.

**Postulated, and both restored by audit after being folded away** — the second
of them three times: a **realisation operator** (collapse is typed as a map out
of `Poss`, and the physics grounding's measurement account needs exactly one
continuation realised), and a **destroy/preserve distinction**
(`prop:economics` exempts evaluation because it *preserves*, so the operative
criterion is that a change which *destroys* costs).

**Axiom −1 is split.** In paper 01 every use refuses an import — no frame-free
denominator, no absolute threshold — which is a discipline, not a place that
paper can fail. In the **groundings** it licenses positive results and is a
commitment that can fail; 04 already locates its exposure in its own falsifier.
Guard here, commitment there.

**A third tier** sits between postulate and consequence: four hypotheses,
including the Law of Graphic Equalisation itself, plus the near-uniqueness of
the cheap cut. Bets, neither assumed nor derived.

**How to read the count.** These reductions are re-descriptions — *X is a
special case of Y* — and the criterion licensing them applies to anything the
account posits, so a count driven to zero would be a theorem of the vocabulary
rather than a measurement. **The two restorations are worth more than the folds
were.** What a surviving re-description buys is narrower: two things cannot be
varied independently, which constrains what a grounding may do. It does not
reduce the number of ways the account can be wrong.

The full ledger is `rem:inherited` in paper 01, kept to about 900 words so it
can be checked at a glance; its revision history is in the review record rather
than in the paper.

| file | title |
|---|---|
| `formal/00_is.tex` | Is — the single claim, its method, and the case for it |
| `formal/01_law_of_graphic_equalisation_theory_referenced.tex` | The Law of Graphic Equalisation — Theory |
| `formal/01s_graphic_equalisation_statement.tex` | The Law of Graphic Equalisation — Statement (generated from 01 via `01s.spec`) |
| `formal/01a_graphic_equalisation_physics_grounding.tex` | The Law of Graphic Equalisation — Physics Grounding |
| `formal/01b_graphic_equalisation_mind_and_self_grounding.tex` | The Law of Graphic Equalisation — Mind and Self Grounding |
| `formal/01c_graphic_equalisation_cosmology_grounding.tex` | The Law of Graphic Equalisation — Cosmology Grounding |
| `formal/01d_graphic_equalisation_born_recovery.tex` | The Law of Graphic Equalisation — Born Recovery |
| `formal/01e_graphic_equalisation_communication_grounding.tex` | The Law of Graphic Equalisation — Communication Grounding |
| `formal/01f_graphic_equalisation_qualia_and_consciousness_grounding.tex` | The Law of Graphic Equalisation — Qualia and Consciousness Grounding |
| `formal/01g_graphic_equalisation_total_perspective_vortex_grounding.tex` | The Law of Graphic Equalisation — Total Perspective Vortex Grounding |
| `formal/01h_graphic_equalisation_information_gravity_quantum_reconciliation.tex` | The Law of Graphic Equalisation — Information Gravity Grounding: Change-Load, Quantum Realisation, and the Reconciliation Programme |
| `formal/01i_graphic_equalisation_passive_continuation_momentum_gravity.tex` | The Law of Graphic Equalisation — Passive Continuation Grounding: Momentum, Gravity, and the Cost of Alteration |
| `formal/02_seldon_manifolds_theory_referenced.tex` | Seldon Manifolds — Theory |
| `formal/02a_seldon_manifolds_psychological_grounding.tex` | Seldon Manifolds — Psychological Grounding |
| `formal/02b_seldon_manifolds_social_and_psychological_application.tex` | Seldon Manifolds — Social and Psychological Application |
| `formal/02c_seldon_manifolds_decision_making.tex` | Seldon Manifolds — Decision Making |
| `formal/03_law_of_narrative_momentum_theory_referenced.tex` | The Law of Narrative Momentum — Theory |
| `formal/04_narrativium_theory_referenced.tex` | Narrativium — Theory |
| `formal/05_frames_relation_and_the_empty_limit.tex` | Frames, Relation, and the Empty Limit |
| `formal/06_assessing_an_account_of_this_kind.tex` | Assessing an Account of This Kind |
| `formal/07_causal_attitude_networks_on_the_substrate.tex` | Causal Attitude Networks on the Substrate |
| `formal/08_certified_answers_as_an_audit.tex` | Certified Answers as an Audit |
| `formal/09_adaptability.tex` | Adaptability |
| `formal/09a_adaptability_implementation.tex` | Adaptability — Implementation |
| `formal/10_applied_graphic_equalisation.tex` | Applied Graphic Equalisation |
| `formal/10a_red_queen_race_civilisational_rate_of_change_llms_biological_timescales_anthropocene_transition.tex` | Cost-Floor Compression, the AI Wedge, and Civilisational Transition — A Conditional GE Assessment |
| `formal/A1_constructive_graphic_equalisation_implementation_referenced.tex` | A Constructive Realisation of Graphic Equalisation |

`01s` is **generated**, never hand-edited: edit `01s.spec` and the long paper,
then run `python3 ../../tools/build_statement.py 01s.spec` from `formal/`. The
generator exits non-zero on a dead `@pull` label and lists every labelled block
the spec does not pull, so material added to 01 surfaces as a review item
instead of silently diverging.

`figures/` holds paper figures — **a committed generator script plus its
output**, never an output alone; the plan for all of them (papers and book
together) is `../book/FIGURES.md`. Paper 02 currently includes two figures. Five
further bodies are built but included by no paper (`fig01_boundary`,
`fig01_collapse_dynamic`, `fig03_narrative_momentum`, `fig04_horizon`,
`fig05_executor_round`) — wiring those in is the first gap to close.

## Version and release status

[`formal/paper_metadata.json`](formal/paper_metadata.json) is the sole editable
source of formal-paper identity. It declares the shared draft version and
display date, plus each document's revision; the current release-wide draft is:

> **`draft-2026-09-06.1`** · 6 September 2026

[`formal/paper_metadata.tex`](formal/paper_metadata.tex) is a committed,
generated LaTeX include. Do not edit it: change the JSON manifest and run
`python3 tools/build_paper_metadata.py` from the repository root. Before a
build or release, run:

```sh
python3 tools/build_paper_metadata.py --check
python3 tools/check_draft_consistency.py
```

The first command fails if the generated include is missing or stale. The second
validates manifest coverage and inclusion, rejects handwritten draft/date/
revision metadata, checks title, notice, and footer agreement, and retains the
bibliography and revision-history checks. `python3 tools/papers.py build
<stem> ...` regenerates the include before compiling named papers; `round` also
runs the consistency gate.

The release gate is deliberately separate and fail-closed. As of this draft it
clears 20 documents. The adaptation and implementation papers
`09_adaptability`, `09a_adaptability_implementation`, and
`A1_constructive_graphic_equalisation_implementation_referenced` remain excluded
because they concern adaptive autonomous-control capability or executable
realisation. Other new documents, including the conditional 01h reconciliation
programme and the conditional 01i passive-continuation programme, remain
excluded unless an explicit editorial release decision adds them to the
fail-closed allowlist. Validate the cleared set, including rendered-PDF stamps,
with:

```sh
python3 tools/release_papers.py --dry-run
```

The papers are circulated for comment, not as finished results. The generated
metadata keeps the shared citable draft identity aligned across title blocks,
notices, footers, generated statements, and release checks while retaining each
document's own revision.

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

From the repository root, verify generated metadata and build named papers with
the wrapper:

```sh
python3 tools/build_paper_metadata.py --check
python3 tools/papers.py build 02_seldon_manifolds_theory_referenced
```

The wrapper compiles from inside `formal/` and refreshes
`paper_metadata.tex` before it starts. Direct `pdflatex` builds remain
reproducible because the generated include is committed, but must also be run
from inside `formal/`:

```sh
cd papers/formal && pdflatex 02_seldon_manifolds_theory_referenced.tex
```

Paper 02 `\input`s its figures by relative path (`../figures/fig02_*-body`), so
`-output-directory` changes how those paths resolve and the build silently
produces no PDF for that paper while the others succeed. Found the obvious way:
a batch loop reported fewer papers than it should have.
