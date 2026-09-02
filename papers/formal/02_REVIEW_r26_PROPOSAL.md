# Review of `02_seldon_manifolds_theory_referenced.tex` (draft-2026-09-02.1, r26) — proposal for fixes

Second pass. Scope: the whole file (1616 lines, 29 pp), its log and aux,
the r24 review and what r25–r26 did with it, and the companions it refers
to (01 r279, 01a r43, 02a r11, 03 r29, 04 r20). Line numbers are r26.
Nothing applied.

Compile: 0 warnings, 0 overfull, 60 bibitems all cited, no `??`, all
`GE-`/`PH-` refs resolve. r25–r26 did what r24 asked: the Remark 0.x
material is now `sec:standing` first; the glider case is `sec:onedim`;
the two stub sections folded; unit $c$ attributed to the physics
companion; `xr-hyper` to 01 and 01a; the inherited definitions marked
inherited; `cor:trap-antecedent`; the two missing commitments and the
re-mark; `sec:competing` cited (Fudenberg–Maskin, Axelrod, Kreps–Wilson)
and its strong claim reduced to the truncation reading with a falsifier;
the NHC cone cited; the font warning; the untitled remark titled. The
paper is in good shape. **What this pass finds: four by-name mentions of
the Graph Law without a reference; *Narrativium*, the Seldon grounding and
the momentum paper cited by description at ten sites with no external
document for any of them; one name off 01's table; the construction paper
named in the falsifier close; the "single pass" sentence; two placement
notes; and one body prediction without a falsifier.**

Nineteen of 02's labels are cited by other papers via `SM-` (`def:seldon`
×4, `def:dimension` ×4, `rem:underspecified`, `rem:optional-machinery`,
`rem:aperture` ×2 each, eleven more ×1). All must survive under the same
names and kinds.

---

## A. "The Graph Law" four times, no reference

`tools/check_paper_refs.py` flags l.212, 446, 948 and 1297: "a primitive of
the Graph Law", "The Graph Law is deterministic throughout", "not part of
the deterministic Graph Law", "not because the Graph Law is stochastic".
01 r279 names it: "Hypothesis~\ref{GE-hyp:the-law} is *the Law* throughout,
and *the Graph Law* where the contrast with a grounding's own laws matters."
**Fix:** `Graphic Equalisation's Hypothesis~\ref{GE-hyp:the-law}` at first
use (l.212); `the Graph Law (Hypothesis~\ref{GE-hyp:the-law})` or the bare
name with the ref once per section after. The checker should return zero.

---

## B. Three companions by description; one name; the construction paper in the close

`xr-hyper` resolves `GE-` and `PH-` only. Sites and targets (all verified
in the current aux files):

| line | claim | target |
|---|---|---|
| 162 | "the form the Seldon grounding takes" (asking whether a system implements anything of this shape) | `SG-sec:scope` |
| 284–285 | "The Seldon grounding reports that measurement" (the aperture-to-shoulder ratio) | `SG-sec:body` |
| 522 | "*Narrativium* supplies the second of them" | `NV-def:narrativium` |
| 575–580 | "the quantity *Narrativium* defines … the construction of $N$ as a measure over a reachable deformation set, and its deformation-class typing" | `NV-def:narrativium`, `NV-def:reachable-deformation`, `NV-sec:deformation-class` |
| 583 | "*Narrativium* establishes no such law and exhibits transitions that net-gain" | `NV-prop:no-conservation`, `NV-prop:spend-gain` |
| 630 | "*Narrativium* constructs $N$ from a reachable set" | `NV-def:narrativium` |
| 640 | "the contrast is set out in full in *Narrativium*" (Muchness vs $N$) | `NV-sec:not-muchness` |
| 643 | "this is the subject of the Narrative-momentum paper" | `NM-sec:narrative`, `NM-def:narrative` |
| 757 | "*Narrativium*'s state-versus-flow distinction" | `NV-sec:measurement-expenditure` (its expenditure definition) |
| 1277 | "the same commitment also appears in the Narrative-momentum paper" | `NM-sec:falsifiability` |

**Fix.** `\externaldocument[NV-]{04_…}`, `[SG-]{02a_…}`, `[NM-]{03_…}`; each
row a resolving `\ref` with the paper named. Note the `SG-` addition makes
02 read 02a's aux while 02a reads 02's; the labels are stable and one extra
pass settles it.

**Naming.** The box (l.53) and l.643, l.1277 say "the Narrative-momentum
paper"; 01's companion table says **"the momentum paper"**. Three sites.
Everything else in the box matches the table.

**The construction paper.** l.1276–1278: "the same commitment also appears
in the Narrative-momentum paper **and as a conformance test in the
corpus's constructive realisation: four listings, one risk**." That names
A1 (not circulated) as one of the four listings of the determinism
commitment. 01 r279's rule is that A1 is described where its contents bear
on a claim and never cited as evidence; here it is being counted as a
place the commitment is *banked*, which is closer to evidence than
description. **Fix:** "three listings, one risk" — Graphic Equalisation,
this paper, and the momentum paper — and drop the A1 clause.

---

## C. Narration and placement notes

1. l.1237–1240: "They were assigned in a single pass under that rule, and
   are the least-audited judgement in this document — a reader who thinks
   one is marked in the flattering direction is disagreeing with a fast
   call, not an argued position." The same sentence 01a, 01b, 01c and 02a
   are dropping this round. Keep 01's definition sentence (l.1233–1237,
   verbatim) and the "On a claimed class" paragraph before it; delete the
   rest.
2. l.638–643: "Two relationships to the companions belong here rather than
   in a section of their own." A placement note. State the two
   relationships without the note: "This paper distinguishes retained
   distinguishable future possibility (Muchness) from the capacity to
   deform it ($N$); the contrast is set out in *Narrativium* (…). Narrative
   is unnecessary for defining $\Seldon$, but where a containing frame
   carries operative history-bearing state, that state may orient the
   manifold (the momentum paper, …)."
3. l.1062: "This shared-arena case differs from one graph individuated by
   several frames: each individuating frame carries its own represented
   dimensions, resolution, and reachable geometry unless a containing
   relation explicitly couples them." This sentence belongs to the
   composition discussion at l.967–979 and is stranded after the
   game-theory material. Move it to follow l.979.

---

## D. One body prediction without a falsifier

`rem:aperture-shape` l.298–302: "a thing lying beyond the horizon attracts
little regardless of size … it predicts that the usual remedies for such
blindness — more information, greater vividness — do less than extending
the horizon does, because only the second puts the thing where a fit can
be judged." That is a testable prediction stated as one, and the list has
no entry for it (02a's item 4 tests salience-by-fit, not the remedy
asymmetry). Add `[detail]` **Horizon extension beats vividness for
beyond-horizon items**: fails if, for an item lying beyond a frame's
represented horizon, increasing its vividness or the information about it
raises its salience as much as bringing it inside the horizon does.

---

## E. Smaller

1. Bibliography order: `aubinbayen2011` (Aubin et al.) is filed before
   `aubin1990`/`aubin1991`/`aubin1999`; single author first. Cosmetic.
2. `nhccone` gives the URL in `\texttt{}`; the set uses `\url{}` (10 r5
   loads `url`). Cosmetic; either is findable.
3. l.771 "the closest operational instance of this whole assembly that
   this account has found" — fine (r24 H fixed).
4. `\input{../figures/…}` for the two figures — fine, but note that the
   build depends on `papers/figures/`; nothing to change.

---

## What is right and should not be touched

- `sec:standing`: `rem:already-in-use` (the cone misread as the storm's
  extent as a frame confusion), `rem:underspecified` ("underspecified
  exactly where you cannot build from it"; obviousness as the success
  condition for a description), and the three guards.
- `rem:aperture` as inherited from 01's aperture definition, and
  `rem:aperture-shape` (moved here from 02a per the r9 review).
- `sec:foveation`'s interpretation: no referent continuum behind the
  grain; refinement driven by incoherence at the held grain, not by a
  finer signal.
- `rem:two-deficits` and `def:blind-spot`.
- `sec:contours` → `def:trap` → `cor:trap-antecedent`, and
  `rem:second-field-prior`'s bookkeeping against Turner, Krakovna,
  Klyubin, Becker–Murphy, Ben-Porath, Ames.
- `sec:onedim` entire, including the vertical-landing limit case and "no
  version of it that is happening to nobody".
- `sec:claimed`: the strong frame-relativity commitment and the Halpern
  parenthetical.
- `sec:competing` as reduced: "the construction is named for prisoners,
  and the one thing it removes is the prison"; the truncation reading and
  the players-not-games inversion as the two claims beyond the literature.
- `sec:positioning`'s bookkeeping against Aubin, and "what is left is
  narrower and is epistemic rather than mathematical".

---

## Suggested order

1. **A** — four refs.
2. **B** — three external documents, ten refs, one name, the A1 clause.
3. **C**, **D**, **E**.
