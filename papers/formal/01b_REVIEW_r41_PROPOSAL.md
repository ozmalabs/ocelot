# Review of `01b_graphic_equalisation_mind_and_self_grounding.tex` (draft-2026-09-02.1, r41) — proposal for fixes

Fourth pass. Scope: the whole file (1978 lines, 32 pp), its log, aux and
PDF metadata, the r40 review and what r41 did with it, and the companions
it resolves by number (01, 01a, 03, 04). Line numbers are r41. Nothing
applied; nothing compiled or committed here.

Compile: 0 warnings, 0 overfull, 0 underfull, no `??`, 77 bibitems all
cited (77 distinct `\cite` keys against 77 `\bibitem`s), all
`GE-`/`PH-`/`NM-`/`NV-` refs resolve. The four `\externaldocument`
imports (`GE-` 01, `PH-` 01a, `NM-` 03, `NV-` 04) all load from present
aux files (log lines 8–11). Every one of the 33 distinct external refs
used in the body was checked against its companion aux and resolves (see
the verification block at the end). **r41 did essentially everything r40
asked, and the substance holds on a fourth reading.** The seven
propositions r40 flagged now state and no longer argue; the tags
sentence, list form and scope note are corrected; the three references
by description resolve by number; the "horizon material" that referred to
nothing is now stated as this remark's own conjecture; the three results
lacking a falsifier have `[detail]`/`[shape]` commitments. **What this
pass finds is small: one three-dash sentence that parses two ways, two
free-text editor lists still on `et al.` where the set uses `et~al.`, and
a handful of optional tightenings. No structural or citation defect
remains.**

Eight of 01b's labels are cited by other papers via `MS-`
(`prop:minimal-universe` ×5, `sec:minimal` ×3, `prop:selfmodel` ×2,
`prop:manipulation-structural`, `prop:one-influence`,
`rem:death-decoherence`, `rem:realisation`, `sec:falsifiability`;
imported by 01, 01a, 01s, 04, 06). All eight are present in 01b's aux
under the same names and kinds and must stay so.

---

## What r40 asked, and what r41 demonstrably did

All items below were verified against the r41 source, log, aux, and the
companion aux files — not inferred.

**A — seven propositions reduced to statements, seven remarks/paragraphs created. COMPLETE.**
`prop:run-record` (l.187) now states in four sentences with the two
inherited components moved to the paragraph after (l.196 "Two of the
three components there are inherited…"). The created remarks all exist:
`rem:imagination-consequences` (l.307), `rem:pushback` (l.371),
`rem:other-model-composition` (l.933), `rem:death-persists` (l.1031),
`rem:identity-cases` (l.1060). `prop:imagination-real` (l.293),
`prop:grounding` (l.360), `prop:selfmodel` (l.418), `prop:other-model`
(l.929), `prop:death` (l.1013) and `prop:identity` (l.1050) all read as
statements with the argument in following prose. `prop:minimal-universe`,
`prop:free-will`, `prop:one-influence`, `prop:manipulation-structural`
state as before.

**B — the tags sentence, list form, scope note. COMPLETE.**
1. l.1462 reads "something **the substrate** is claimed to require or to
   permit" — restored from "the account". ✓
2. The falsifiability list is now `enumerate` (l.1464–1580, 23 items),
   and the note after it (l.1582) reads "**Items 6 and 20** are falsified
   by the same object". ✓
3. The scope note (l.1587–1589) ends "…none is offered." with the
   trailing "This sits outside the list because nothing about the world
   could settle it" sentence dropped. ✓

**C — three references by description, and the one with no referent. COMPLETE.**
- l.100–102 "the collapse bridge (its Remark~\ref{GE-rem:qm-provenance})":
  verified — 01 l.2705 names `rem:qm-provenance` "the conditional collapse
  bridge". ✓
- l.744–748 the crab's persistence "(\emph{Narrativium}'s
  Remark~\ref{NV-rem:two-cases})" and overshoot cited again by number:
  verified — 04 l.411 is "Two cases: the horseshoe crab and the tetrapod
  limb". ✓
- l.898–899 "the $+1$ direction of the level stack (the momentum paper's
  Remark~\ref{NM-rem:level-stack})": verified — 03 l.200 is "The Narrative
  level stack: inferred, carried, read". ✓
- l.750–752 the "window of tolerance" is now stated as this remark's own
  conjecture ("the step from window width to horizon length is conjectured
  here and not established anywhere in the set"); the phrase occurs only
  in this one sentence, no longer leaning on non-existent corpus material.
  Item 10 of the list (l.1510) carries the matching "the window→horizon
  step is the untested half". ✓

**D — three results given a falsifier. COMPLETE.**
Item 21 `[detail]` **Transparency varies with formation.**
(`rem:transparency`, l.1553), item 22 `[detail]` **Cognition converges
with distributed engineering only where the two constraints bind.**
(`rem:cognition-compression`, l.1557), item 23 `[shape]` **No frame
handles its own stop.** (`rem:death-decoherence`, l.1577) all present, at
the end, positions 1–20 unchanged.

**E — smaller. COMPLETE.**
1. l.464–465 now reads "The account **was later developed** in terms of
   self-modelling epistemic spaces…" — the drafting-tense "since been
   developed" is gone, and it is about Metzinger's literature. ✓
2. `\texttt{fork}` (l.1310) is the POSIX call cited to `posix2017`; r40
   confirmed this is fine. Still fine.
3. `posix2017` is filed under I ("IEEE and The Open Group(2017)"),
   between `hume1748` and `karpus2025` — the r39/E.1 request. ✓
4. Bibitem author-label fields use `et~al.` (12 ties); the two remaining
   `et al.` are in `\newblock In Peter H\"uhn et al., editors,…`
   free-text editor lists (see B1 below).

The narration sweep is clean: none of the ten r39/B phrases nor any
"this paper/section did/has not…" drafting construction survives (grep
returns nothing). No A1 companion is cited anywhere, let alone as
evidence. No project implementation identifier appears; "seed" is the
record's generic term (l.724, 728) under the l.94–101 evidence standard.

---

## A. What is left, weighted

### A1. One sentence parses two ways (readability, medium)

l.465–466:

> Read as a property of self-models as such --- a reading Metzinger does
> not take --- calibration would be foreclosed --- a construction
> invisible from inside is not correctable from inside, and residual
> would be absorbed…

Three em-dash breaks in a row. The first pair brackets "a reading
Metzinger does not take"; the third dash then opens a second aside, so
the main clause "calibration would be foreclosed" is stranded between two
parentheticals and the reader cannot tell on first pass whether it closes
the aside or is the sentence's spine. Every other multi-clause sentence
in the paper resolves its dashes into one bracketed aside. **Fix**
(punctuation only, no content change):

> Read as a property of self-models as such --- a reading Metzinger does
> not take --- calibration would be foreclosed: a construction invisible
> from inside is not correctable from inside, and residual would be
> absorbed…

The colon makes "a construction invisible…" the gloss on
"foreclosed" that it already is, and leaves one aside.

### A2. Two editor lists still on `et al.` (consistency, low)

l.1905 (`schmid2014`) and l.1965 (`wolf2014`) carry `In Peter H\"uhn et
al., editors,` in the `\newblock`. The author-label fields were all moved
to `et~al.` (the r39/E.2 fix); these two free-text lists were not. The
set's convention is the non-breaking tie throughout. **Fix:** `H\"uhn
et~al.` in both. Cosmetic; two edits.

### A3. Optional tightenings (low)

1. l.418–427 `prop:selfmodel` states cleanly, but the paragraph that
   follows (l.429 "Both halves of that are read off inherited
   machinery…") carries the Kruger–Dunning material with the disputed
   status flagged twice — once in the prose ("That reading is contested")
   and once in the bibitem note (l.1799 "The size and interpretation of
   the effect are contested"). One statement of the caveat is the set's
   habit; the bibitem note is the place the other papers keep it, so the
   prose "so it is cited here as one disputed candidate for the shape"
   already carries the point and the doubled hedge could lose one clause.
   Not a defect.
2. l.728–732 `rem:comm-engine`'s "\emph{Scope.}" paragraph and the
   inline scope sentence at l.724 both bound the same fixture; this is
   the correct disclosure and reads as intended. Leave it.

---

## What is right and should not be touched

- `sec:minimal`: the third-condition reading of "rock", the
  one-directional inference (l.130 "A single inert example bounds the
  compulsory set from above"), "the rock's inertness is not a defect in
  the example but the whole of its content", and the naming reciprocated
  with `GE-rem:space-test`.
- `sec:runrecord`: Conway/movie/machinima on one axis, and
  `prop:run-record` now stated with the inherited components attributed
  after it.
- `sec:freewill`: `prop:free-will`, the two corollaries, and
  `rem:three-frames`'s "foreknowledge is always post-run record-holding,
  never pre-run read-ahead"; `rem:reader` with its two qualifications and
  the three literatures (Currie, Rabinowitz/Polvinen, Nichols/Gendler/
  Walton/Wolf) kept as functional-not-metaphysical separation.
- `sec:grounding`: `prop:imagination-real`, `rem:detection`'s proxy
  dissociation with its first-order/second-order guard, `prop:grounding`
  anti-foundationalist-without-flat-coherentism, and the perspectival-
  realism paragraph.
- `sec:selfmodel`: the three sources of incompleteness (aperture, proper
  part, lesser object) kept apart, `prop:selfmodel`'s expression/aperture
  split, the access-mode-not-accuracy asymmetry, `rem:transparency` as
  agreement-with-a-residual-disagreement, and `rem:realisation`'s "the
  self as modelled did not; the modelling did".
- `sec:compression`: `rem:cognition-compression`'s two named binding
  constraints with the two excluded candidates, and
  `rem:public-aperture`'s residual-not-education prediction.
- `sec:communication` entire: the two propositions and their joint
  reading, `rem:comm-engine` as measurements with scope,
  `rem:comm-horizon` reciprocating `GE-rem:aperture-purchased`,
  `rem:boredom` (Narrative minus pressure), `rem:comm-calibrated`'s
  negative result (recurrence runs the wrong way), `rem:comm-prior`'s
  Austin correction.
- `sec:other-models`: Genette given the generativity in full ("only the
  personification and the truth condition attaching to it are not"),
  Porter–Machery below-chance used correctly, Schwitzgebel's tell,
  `prop:other-model` and `rem:other-model-composition`'s one-step
  ownership.
- `sec:death`: `prop:death`, `prop:identity`, `rem:identity-cases`,
  `rem:record-gradient`, `rem:fidelity-not-capture` (Chalmers as a live
  position), `rem:death-prior`'s attributions (Sandberg, Campbell,
  Karpus, Cerullo), `rem:parfit`, `rem:hofstadter` ("threshold per
  coherence, gradient across coherences"), `rem:death-decoherence`,
  `rem:death-computing`'s "an implementation is free to add rules to
  suit" and the reachability/re-runnability caution, `rem:death-relative`.
- `sec:prior-art`'s asymptotic-approach reading and "tiny and different
  in kind … orthogonal to the sequence, not further along it";
  `sec:no-privilege`'s honest boundary.
- The falsifiability list: 23 items, tags correct, the two-object note,
  the scope note as a non-falsifier with the trailing sentence dropped.

---

## External-target verification (all against current companion aux)

Every distinct external ref in the body, resolved:

- `GE-` (→ `01_…theory_referenced.aux`, 23 refs): `ax:no-view`,
  `def:aperture`, `def:change-grammar`, `def:self-identity`,
  `def:supergraph-identity`, `def:well-formed`,
  `prop:compression-convergence`, `prop:decoherence-one`,
  `prop:determinable`, `prop:no-direct-self-alter`, `prop:no-start-end`,
  `prop:runner-recursion`, `prop:self-governance`,
  `prop:vacated-three-states`, `rem:aperture-purchased`,
  `rem:evolution-compression`, `rem:qm-provenance`, `rem:rock`,
  `rem:self-edge`, `rem:space-test`, `rem:supply-not-containment`,
  `rem:types-forced`, `rem:vacated` — all OK.
- `PH-` (→ `01a_…physics_grounding.aux`, 5 refs): `cor:observer`,
  `prop:dim-boundary`, `prop:self-location`, `rem:gauge-contingent`,
  `sec:dimensions` — all OK.
- `NM-` (→ `03_…narrative_momentum…aux`, 2 refs): `def:free-continuation`,
  `rem:level-stack` — all OK.
- `NV-` (→ `04_narrativium…aux`, 3 refs): `prop:no-sum`,
  `prop:overshoot`, `rem:two-cases` — all OK.

01b's own eight `MS-`-cited labels all present in
`01b_…_grounding.aux`: `prop:minimal-universe`, `sec:minimal`,
`prop:selfmodel`, `prop:manipulation-structural`, `prop:one-influence`,
`rem:death-decoherence`, `rem:realisation`, `sec:falsifiability`.
Preserve all under the same names and kinds.

---

## Suggested order

1. **A1** — the one three-dash sentence (punctuation, one edit).
2. **A2** — the two editor `et~al.` ties (two edits).
3. **A3** — optional; leave if the pass is otherwise clean.

The paper is in good shape. Compile order stays 01, 01a, 03, 04 before
01b; 01/06 that cite `MS-` want a second pass after 01b to settle the
cycle, but nothing in r41 changes an externally cited label.
