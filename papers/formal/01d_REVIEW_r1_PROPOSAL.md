# Review of `01d_graphic_equalisation_born_recovery.tex` (draft-2026-09-02.1, r1) — proposal for fixes

First review. Scope: the whole file (494 lines, 8 pp), its log, the two
sources it was promoted from (`papers/outreach/born_recovery_note.md`,
`docs/research/engine_substrate/BORN_HILBERT_AXIOM_MAPPING.md`), and the
papers it sits between (01 r279, 01a r42→r43 in flight, 03 r29). Line
numbers are r1. Nothing applied.

Compile: 5 underfull-hbox warnings (all in the two rating tables), 0
overfull, 13 bibitems all cited and correct, no `??`, by-name check clean.
The note's distinctive content is sound and worth having as its own
document: Level 0 (the substrate instantiates the operational-
probabilistic core from the classical total-probability backbone, and
that affinity is not superposition linearity); `prop:crux` (two
reconstructions' different most-quantum axioms each supplied natively
from a different substrate principle); the rated axiom table; and the
rated residual list. **The findings: the note cites nothing by number and
restates 01/01a at length in a preamble paragraph that contradicts its
own box; about a third of it duplicates 01a's amplitude section verbatim;
the rating scale is stated one way in the abstract and used another way
in the tables; two narration sites; one falsifier is a scope note; and
the tables' column widths.**

01a r43 (in flight) will cite `BN-sec:level0`, `BN-prop:opt`,
`BN-sec:axioms`, `BN-prop:crux`, `BN-sec:residuals`. Those labels must
survive under the same names and kinds.

---

## A. Nothing is resolved by number, and the preamble restates two papers

No `xr-hyper`. The box (l.29–32) says the note "inherits those papers'
definitions"; the abstract (l.42) says "It is self-contained; the papers
carry the surrounding framework"; and `sec:substrate` (l.62–92) is then a
31-line single paragraph restating 01 and 01a — frame, Narrative, closure
cycle, free continuation, evaluation-is-a-write with the return-channel
argument, the runner's charge, unit $c$ and the indirect route, nesting.
Most of it is not used by the mapping ($c$ appears only in `sec:reconcile`,
which is itself duplicated from 01a, see B). The return-channel argument
is 01's `prop:evaluation-writes` nearly verbatim; the $c$ paragraph is
01a's `rem:c-indirect` nearly verbatim.

**Fix.** Add `\externaldocument[GE-]{01_…}`, `[PH-]{01a_…}`, `[NM-]{03_…}`
(xr-hyper before hyperref; pull hyperref out of the bundle line l.4).
Rewrite `sec:substrate` as the six definitions the mapping actually uses,
one sentence each, each a resolving ref:

| notion | target |
|---|---|
| frame as a subgraph that runs; nesting | `GE-def:frame`, `GE-prop:no-direct-self-alter` |
| Narrative as the standing structure carried forward; direction and phase | `NM-def:narrative`, `NM-def:internal-external`, `NM-def:narrative-momentum` |
| closure cycle; phase as position on it | `GE-prop:cycle-unit`, `GE-rem:phase-not-time` |
| realisation as a local write with a weight; strictly ordered | `GE-def:collapse`, `GE-prop:partial-order` |
| free continuation as the information-preserving default; injective hence reversible | `NM-def:free-continuation`, `GE-prop:evaluation-writes` |
| no privileged frame, phase origin, or basis | `GE-ax:no-view` |
| entanglement as a superframe dimension; a mixed subframe state | `PH-prop:mixed`, `PH-cor:nonlocal` |

Drop the abstract's "self-contained". Other by-description sites to
resolve: l.100–104 ("what survives every attempted removal is a container
relation across which rules run … as with the number of spatial
dimensions or the gauge group" → `GE-rem:only-g`, `PH-sec:dimensions`,
`PH-rem:gauge-contingent`); l.136 and l.392 ("history-optional,
present-structure-acts first law" → `NM-sec:law` and `GE-cor:history`);
l.209 (minimum description length as a native commitment →
`GE-rem:mdl-ontic`); l.283 (self-location → `PH-prop:self-location`);
l.374–377 (the spectrum floor → `PH-prop:spectrum-floor`). Name the
momentum paper in the box (01's table name), since Narrative and the
first law are its vocabulary.

---

## B. About a third of the note duplicates 01a's amplitude section

| 01d | 01a r42 | relation |
|---|---|---|
| `prop:square` l.224–235 | l.666–679 (the phase-averaging argument) | verbatim |
| l.237–242 (Gleason supplies uniqueness) | l.681–694 | near-verbatim |
| `rem:identifications` l.244–253 | l.696–711 | condensed |
| the $K$ table l.260–270 and `prop:contingent` l.278–284 | l.739–761 | 01a has the numbers in prose; the table is the note's |
| `rem:misframing` l.286–296 | l.754–756 | expanded |
| l.298–318 (reconstruction survey) | l.713–727, 762–766 | near-verbatim |
| `sec:reconcile` l.320–341 | l.789–807 ("The reconciliation: Born, SR, and GR on one substrate") | near-verbatim |
| `sec:residuals` items 1–4 | l.768–787 ("Honest residuals, collected") | same four |
| `sec:residuals` item 6 | l.1315–1319 | verbatim |

01a r43 is being rewritten to cite this note for the Level-0
instantiation and the axiom mapping. The division that follows from
that: **01a carries the physics** (the squared modulus, complex over real
with the $K$ numbers, the reconciliation, the reconstruction survey) and
**the note carries the mapping** (Level 0, `prop:crux`, the rated tables,
the rated residuals). Recommended cuts here:

- `prop:square` → one sentence: "The squared modulus is selected among
  the natural candidates by phase-averaged additivity, and made unique by
  Gleason, in the physics companion (its Proposition~\ref{PH-prop:born}
  and the argument following it); this note uses the result."
- `sec:reconcile` → two sentences pointing at `PH-prop:sr-gr`,
  `PH-cor:reconcile`, `PH-sec:collapse`, and 01a's reconciliation
  subsection. The constructor-theory and RQM sentences stay in 01a.
- l.298–318 survey → keep only the Masanes–Müller sentence (it names the
  seam this note is about) and one clause for Höhn (rebits) as
  independent support; the rest is 01a's `sec:prior-art`.
- `sec:residuals` items 1–4 stay (they are the note's own list; 01a's
  "collected" list should point here instead — note that for 01a's next
  touch); item 6 (in-frame energy as a count) is 01a's `prop:spectrum-floor`
  residual and does not belong to a Born note. Drop it.
- Keep the $K$ table and `prop:contingent` here (the table is the note's
  evidence for the contingency verdict) and let 01a cite `BN-prop:contingent`
  for the numbers.

That takes the note from 8 pp to about 5, all of it its own.

---

## C. The rating scale is stated one way and used another

Abstract l.46: "Each step is rated solid, plausible or gap". The tables
use **solid / earned / plausible / contingent**; "gap" appears nowhere.
l.218–222 defines "plausible" (genre-match, not statement-match) but not
the others. **Fix:** one sentence before the first table defining the
four: *solid* — the substrate structure is the axiom's statement;
*earned* — derived here from a substrate principle rather than read off
one; *plausible* — a commitment of the right kind, statement-match not
shown; *contingent* — rule-content, admitted and self-located, not
supplied. Abstract to match.

---

## D. Narrated drafting

| line | phrase |
|---|---|
| 173–175 | "None of these is the 'does it convex-linearise at all' worry that Level 0 **originally named**. **That worry is resolved**; these are carried forward" |
| 286–289 | "Treating 'does the substrate *force* the complex composite?' as the open question **was an error** of the framework's own kind" |

Both state a result as a correction of the note's own earlier framing.
l.173 → "None of these is the question whether the state space
convex-linearises at all, which Level 0 answers; they are carried
forward." `rem:misframing` → retitle "Why forcing is the wrong question"
and open "Whether the substrate *forces* the complex composite is not the
open question, and asking it would be an error of the framework's own
kind."

---

## E. Falsifiers

1. Item 6 `[detail]` **Recovery, not derivation** — "Fails as an honest
   sizing if any step above is read as compelling the Born rule … refused
   if the arrangement is presented as a necessity." That is the scope-note
   shape the set moves out of lists. Fold into the scope note after the
   list.
2. Item 1 `[shape]` **The operational-probabilistic instantiation** has
   two clauses of different weight: the core (convex states … from
   weighted ordered realisations) is `[shape]`; "or if the hygiene
   conditions of Section~\ref{sec:residuals} cannot be met" is `[detail]`
   (finite tomographic dimension, closure, the composition axioms — each a
   mechanism the note could lose). Split into two items.
3. Missing: the composition seam. l.301–305 names Masanes–Müller as "the
   one this note would most like tested against". Add `[detail]`: fails
   if the substrate's composition rule, tested against requirements
   stated on single systems plus a composition rule, yields a composite
   that is neither the complex ($K_{AB}=16$) nor the real ($K_{AB}=10$)
   admissible configuration — which would make the contingency verdict of
   `prop:contingent` a verdict about the wrong set.
4. Item 3 `[shape]` **The axiom mapping** is right and is the note's real
   exposure; keep.

---

## F. Mechanical

1. Five underfull boxes: `>{\raggedright\arraybackslash}` on the
   `p{}`-columns of both rating tables (and `\usepackage{array}`), as 01
   r279 did for its companion table.
2. Bibitem labels "et al." → `et~al.`; `hoehnwever2017` before `hoehn2017`
   (single author first). Both cosmetic and shared with 01a.
3. `\texorpdfstring` already on the date. `{99}` fine.
4. "this note" ×4 is consistent with the title and 01's table name ("the
   Born note"); keep.

---

## What is right and should not be touched

- `rem:recover`: "a contingent law can only be recovered given its
  rule-content, never derived as compelled."
- `sec:level0` entire, and `rem:affine` — the affinity of effects is total
  probability over ordered branchings, prior to and distinct from
  superposition linearity, and the argument would be circular otherwise.
- `prop:crux` and the sentence after it: two crux axioms, two principles,
  neither introduced for the purpose.
- The rated axiom table, and l.218–222's "a reader who upgrades one of
  them is disagreeing with a rating, which is the intended form of the
  disagreement".
- `prop:contingent` and the $K$ table; "real amplitudes cost
  self-similarity" as a direction without a compulsion.
- `sec:residuals` items 1–5 as the note's own ledger.

---

## Suggested order

1. **A** — `xr-hyper`, the six-definition preamble, the momentum paper
   named.
2. **B** — the cuts, coordinated with 01a r43 (which cites this note's
   labels; all survive).
3. **C**, **D**, **E**, **F**.
