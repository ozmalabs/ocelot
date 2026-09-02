# Review of `04_narrativium_theory_referenced.tex` (draft-2026-09-02.1, r20) — proposal for fixes

Second pass. Scope: the whole file (914 lines, 17 pp), its log and aux,
the r19 review and what r20 did with it, and the companions it attributes
to (01 r280, 01a r43, 01b r40, 02 r28, 03 r29). Line numbers are r20.
Nothing applied.

Compile: 0 warnings, 0 overfull, 37 bibitems all cited and sorted as one
list, no `??`, all `GE-`/`SM-`/`NM-`/`PH-` refs resolve, by-name check
clean, no implementation identifiers. r20 did everything r19 asked: the
160-line remark split into `prop:overshoot` and four remarks with the
evolutionary-momentum duplicate replaced by one sentence at
`NM-sec:evolutionary`; the subset-change claim corrected to 01's strict
restriction; the Axiom −1 note; the construction paper gone; Pratchett
credited; `xr-hyper` to four companions; the two missing falsifiers plus
the asymmetry one; the years; the author lists. The paper's core is
untouched and still tight. **What remains: two propositions that argue
rather than state; the lead-in remark still narrating an inter-paper
reconciliation; the mind companion named twice with no external document
and the physics companion under two names; four by-description references
with targets; the "single pass" sentence; and three claims without a
falsifier.**

Fourteen of 04's labels are cited by other papers via `NV-`
(`def:narrativium` ×4, `prop:no-sum`, `prop:overshoot`,
`def:reachable-deformation`, `sec:deformation-class`,
`prop:no-conservation`, `prop:spend-gain`, `sec:not-muchness`,
`sec:measurement-expenditure`, `def:horizon`, `sec:cross-frame`,
`prop:kappa-invariance`, `def:conversion`). All must survive under the
same names and kinds.

---

## A. Two propositions argue; the set's rule is that propositions state

1. `prop:overshoot` l.354–365 is eleven lines: it opens by defining
   equalisation, says "the other option is the one that matters", says
   "Put that way it is stated more sharply than a rate states it", and
   only then states the result. **Fix:** the proposition is two
   sentences — "A lineage *overshoots* when its rate of change carries it
   past the balance point at which what it meets no longer forces a write
   against what it holds: the supercritical regime of
   Remark~\ref{rem:supercritical}, a loop gain above unity. Overshoot is
   not rapid change but change whose products exceed their cause in
   number, and what it produces is capacity in excess of requirement,
   spendable at increasing remove from the structure holding it." The
   sentences about equalisation as a balance point and "the other option"
   go into the prose before the proposition (they are the motivation),
   and "at three increasing removes" stays in the paragraph after it,
   where the three are listed.
2. `prop:cross-frame-asymmetry` l.640–642: "This is the reverse leg of …
   There, … Here, … Container knows contained; contained shapes
   container. The operation is the same self-similar one either way
   (Graphic Equalisation); what is asymmetric is …" **Fix:** the
   proposition states: "A containing frame may hold the contained whole
   where it instantiates the relations to do so; the contained affects
   its container and cannot hold it whole. The asymmetry is in
   representational capacity, not in the operation, which is the same at
   both levels." The reverse-leg framing and the epigram move to one
   sentence of prose after it, with the refs (D.3 below).

---

## B. `rem:overshoot-lead` still narrates

l.345–352: "One term in what follows needs reconciling with Graphic
Equalisation, which holds that a substrate law must be stated in $\Delta$
rather than in a rate … and on that reading **neither paper concedes
anything**. Read alongside Remark~\ref{rem:supercritical},
Proposition~\ref{prop:overshoot} and the remarks after it are what a gain
above unity produces." The first sentence narrates two papers negotiating;
the second is a placement note. The reconciliation itself is one clause.
**Fix:** delete the remark; after l.370 ("…which is the subject of the
momentum paper one grounding over") add: "Stating overshoot as a rate does
not put a rate in a substrate law: a rate is in-frame in provenance and
cross-frame in type (Graphic Equalisation's Remark~\ref{GE-rem:no-denominator})."
`rem:overshoot-lead` is not cited by any other paper.

---

## C. Names

1. **The mind companion** is declared in the box (l.50–51) and used at
   l.699 ("the mind companion's *No frame is privileged*") with no
   `\externaldocument[MS-]`. The item in 01b r40 is unlabelled; its list
   is `MS-sec:falsifiability`. → "the mind companion's *No frame is
   privileged* (its Section~\ref{MS-sec:falsifiability})", and add
   `\externaldocument[MS-]{01b_graphic_equalisation_mind_and_self_grounding}`.
2. **The physics companion** is "the physics companion" at l.630 and "the
   physics grounding" three lines later (l.630, "That lever is the physics
   grounding's and not the substrate's"). One form: the physics companion.
3. l.367–370: "which is the subject of the momentum paper one grounding
   over" — name plus no ref; → `NM-def:narrative-momentum` (momentum as
   the carried rate) — "the momentum paper's Definition~\ref{…}".

---

## D. By-description references with targets

| line | claim | target (verified in the current aux files) |
|---|---|---|
| 72 | "The composition's own falsifiability commitment is stated in Graphic Equalisation and is inherited here" | `GE-sec:scope` (the composition paragraph) and `GE-sec:falsifiability` |
| 406 | "the empty limit this account reaches for perfection and for the view from nowhere" | `GE-rem:everything-nothing` ("where this programme's own empty limit sits") |
| 641 | "The operation is the same self-similar one either way (Graphic Equalisation)" | `GE-prop:no-direct-self-alter` (the sentence after it: "one *self-similar* operation … run at every level") |
| 88 | "the standing remarks of *Seldon* (Remark~\ref{SM-rem:optional-machinery})" | already resolved — no change |

Three refs.

---

## E. The preamble's "single pass" sentence

l.677–680: "The marks were assigned in a single pass under the rule just
stated, and are the least-audited judgement in this document — a reader
who thinks one is marked in the flattering direction is disagreeing with a
fast call, not an argued position." Dropped across the set this round.
Keep 01's definition sentence (l.673–677, verbatim) and the "On a claimed
class" paragraph; delete the rest.

---

## F. Three claims without a falsifier

The list has twelve items and covers the definitions, the conversion
results, the two remarks from `sec:replenishment`, the horizon, delayed
failure, and both cross-frame results. Not covered:

1. **The feasibility gate** (`sec:feasibility`, l.216: a net-positive
   transition "is realisable only where its cost is affordable *up
   front*"). This is what makes spend-and-gain a bootstrapping structure
   and is the paper's own result, not 01's. Add `[shape]` **Feasibility
   gates spend-and-gain.** Fails if, on an instantiated common comparison
   dimension, a transition is realised from a configuration whose cost
   exceeds its measured Narrativium — the entry threshold would then not
   bind, and the capital-threshold structure of Section~\ref{sec:feasibility}
   would be a description.
2. **Overshoot in the tetrapod grounding** (`rem:two-cases`, l.442–448:
   "The structure preceded its *effective* terrestrial use"). The
   grounding is claimed, so the class is live under the paper's own
   discipline. Add `[detail]` **Structure precedes effective use.** Fails
   for the tetrapod grounding if digit-bearing limbs are shown to postdate
   effective terrestrial locomotion in the lineage — overshoot would then
   not be exhibited there, and the case would be an ordinary adaptive
   sequence (Remark~\ref{rem:two-cases}).
3. **Loading as a cost transfer** (`sec:cross-frame-deformation`, l.630:
   "a cheap trigger can compel an expensive response"). Add `[detail]`
   **Loading is a cost transfer.** Fails for a container instantiating a
   finite throughput if the re-cohering cost it pays is bounded by the
   cost of the admissible change that triggered it — the leverage ratio
   would then be at most one, and loading could not move a large
   container.

Item 11's wording paragraph is right and should stay. `prop:no-path` is
covered by item 2 (measurement is not a sum of expenditures); say so in
item 2's text, as item 5 does for conversion.

---

## G. Smaller

1. l.437 "one where the received story was wrong in exactly the way this
   account predicts" — about the literature's story, not the draft's;
   fine.
2. l.463 "which is worth knowing beside \citet{hunt2025} below" — the
   citation is in the next paragraph; "below" is fine.
3. Bibliography: `aubin2011newdirections` after `aubin1991viability` —
   single author first; fine. Labels `et~al.` — fine.
4. `\begin{thebibliography}{99}` — fine.

---

## What is right and should not be touched

- `sec:measurement-expenditure` through `sec:feasibility`: the four
  short results and the bootstrapping paragraph.
- `sec:cross-frame`: `def:conversion`, `rem:kappa-kinds`, `rem:emc2` with
  the invariance test run "as a matter of course",
  `rem:nonconstant-kappa`, `prop:kappa-invariance`, and "convert if you
  must, but state $\kappa$".
- `rem:supercritical`: the loop gain, the slow-fraction constraint, the
  refusal to re-derive the constants.
- `rem:equilibrium-limit`, `rem:two-cases` (the *Qikiqtania* reading and
  the *Acanthostega* juvenile caveat), `rem:arrival` with the
  `NM-sec:evolutionary` sentence.
- `sec:horizon` through `sec:power-agility`.
- `sec:cross-frame-deformation`'s load / bend / break / mint and its
  "exploit against hardening is a continuous contest".
- The conclusion's "not a tank — which denies the vessel and not the
  charge".

---

## Suggested order

1. **A**, **B** — the two propositions and the deleted remark.
2. **C**, **D** — one external document, two names, four refs.
3. **E**, **F**, **G**.
