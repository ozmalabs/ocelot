# Review of `03_law_of_narrative_momentum_theory_referenced.tex` (draft-2026-09-02.1, r29) — proposal for fixes

Second pass. Scope: the whole file (548 lines, 12 pp), its log and aux,
the r28 review and what r29 did with it, and the companions it attributes
to (01 r280, 01a r43, 02 r28, 04 r20). Line numbers are r29. Nothing
applied.

Compile: 0 warnings, 0 overfull, 12 bibitems all cited, no `??`, all
`GE-`/`SM-`/`NV-` refs resolve, no implementation identifiers. r29 did
everything r28 asked: `prop:no-unheld-pending` promoted with its falsifier
(item 11); `def:free-continuation` and `def:internal-external` extracted;
the naming sentence; the construction-paper clause gone;
`rem:cost-form-substrate` labelled; the inherited-status note after the
list. The theory holds on re-reading. **What remains: the physics companion
named twice with no external document; one by-name mention of the Graph
Law with no reference; one bare "(Graphic Equalisation)"; two claims about
*Narrativium* resolved only to its definition; the "single pass" sentence;
one remark whose first paragraph argues three things at once; and two
propositions without a falsifier.**

Thirteen of 03's labels are cited by other papers via `NM-` (`sec:law`,
`def:narrative`, `def:narrative-momentum`, `def:internal-external`,
`def:free-continuation`, `rem:currencies`, `sec:evolutionary`,
`def:narrative-revision`, `sec:narrative`, `sec:falsifiability`,
`hyp:narrative-momentum`, `prop:no-unheld-pending`, `rem:evo-tests`). All
must survive under the same names and kinds.

---

## A. The physics companion is named and never resolved

The box (l.49–50) declares "the physics companion"; the preamble has no
`\externaldocument[PH-]`. Two sites:

| line | claim | target (verified in 01a r43's aux) |
|---|---|---|
| 314 (`rem:impulse`) | "what the physical superframe is charged to sustain it is that container's affair, and the physics companion holds that it charges" | `PH-sec:budget` (the change-budget: throughput per cycle, split between motion and internal change) with `PH-prop:c-unit` for the unit |
| 187–190 (`rem:momentum-delta`) | "what a containing frame is charged to sustain it is that container's rule content and not this frame's" | same `PH-sec:budget`, once |

**Fix.** `\externaldocument[PH-]{01a_graphic_equalisation_physics_grounding}`
after the `NV-` line; l.314 → "and the physics companion holds that it
charges (its Section~\ref{PH-sec:budget})".

---

## B. Three unresolved references to Graphic Equalisation

1. l.266: "it does not add stochasticity to the Graph Law." The checker
   flags it. 01 r280 names the Law: "*the Graph Law* where the contrast
   with a grounding's own laws matters." → "to the Graph Law
   (Graphic Equalisation's Hypothesis~\ref{GE-hyp:the-law})". The checker
   should then return zero.
2. l.187 (`rem:momentum-delta`): "a self-change of $S$, gated by the
   container (Graphic Equalisation)" — a bare name in parentheses. →
   "(Graphic Equalisation's Proposition~\ref{GE-prop:no-direct-self-alter})".
3. l.432 (`sec:prior-art`): "Graphic Equalisation supplies the causal
   reason the pattern works: only present structure enters the next
   deterministic transition relation." → `GE-prop:no-implicit-historical-state`
   (already cited at l.470 for the same claim).

---

## C. *Narrativium* resolved only to its definition

l.83–88: "$N$ the reachable capacity to change it (*Narrativium*,
Definition~\ref{NV-def:narrativium}), **which is where that contrast and
its counterpart against Muchness are set out**. Revision horizons produced
by comparing current capacity with minimum revision cost **are developed
there** rather than here." Two claims, one ref, and the ref is to neither.
→ the Muchness contrast is `NV-sec:not-muchness`; the horizon is
`NV-def:horizon`. Both in 04 r20's aux.

---

## D. The preamble's "single pass" sentence

l.450–453: "The marks were assigned in a single pass under the rule just
stated, and are the least-audited judgement in this document — a reader
who thinks one is marked in the flattering direction is disagreeing with a
fast call, not an argued position." Dropped from 01a, 01b, 01c, 02, 02a,
02b this round. Keep 01's definition sentence (l.446–450, verbatim);
delete the rest; the list follows directly.

---

## E. `rem:momentum-delta`'s first paragraph

l.187–190 is one paragraph carrying three arguments: (i) the Narrative is
the frame's own standing structure, and a delta is a write to it; (ii)
continuation is the absence of an action in the frame's own terms, with a
parenthetical on what the container is charged (A above); (iii) nothing
re-applies $S$ because there is no global tick, so persistence is free and
change paid. The second and third paragraphs are clean. **Fix:** split
the first paragraph at "Continuation is then…" and again at "$S$ persists
until…", so each argument is one paragraph; move the container-charge
clause into a parenthetical of one line with the `PH-` ref. No content
changes.

---

## F. Two propositions without a falsifier

The list covers the cost form, the directional form, discrete Narrative,
historical sufficiency, the carried rate, lock-in, history projection, the
level stack, material revision, and the pending case. Not covered:

1. `prop:no-emergence-gap` (l.115): "Where the defining relation exists in
   $W$, Narrative is ordinary first-class state in $W$." Item 1
   (First-class Narrative) is its falsifier already — say so in the
   item's parenthetical, as item 11 does for `prop:no-unheld-pending`.
   No new entry.
2. `prop:momentum-present` (l.158): "The past need not continue to exist
   for momentum to be real." That is item 3's converse and is not stated
   there. Add `[shape]` **Momentum is present structure.** Fails if a
   measured momentum in a claimed grounding changes when the record of
   prior change is altered while the present structure that change left
   is held fixed — momentum would then be carried by the history and not
   by what it left behind (Proposition~\ref{prop:momentum-present}).

---

## G. Smaller

1. Box l.49: "*Narrativium* (*Narrativium --- Theory*)" — fine; add
   nothing. The naming sentence is otherwise complete for the names used.
2. l.103 "the dimension/value typing of Graphic Equalisation, stated in
   full in *Seldon* (Definition~\ref{SM-def:dimension})" — fine.
3. Bibitem labels use `et~al.` — fine. Sorted — fine.
4. Item 1 of the list runs to five lines of parenthetical on which
   groundings are live; the "On a claimed class" paragraph above already
   fixes the discipline. Keep, but the parenthetical could be one
   sentence: "Live for the maternal-inheritance grounding of
   Section~\ref{sec:evolutionary}; stated, not live, for the others."

---

## What is right and should not be touched

- `sec:narrative` → `sec:history`: NULL is not zero; historical
  sufficiency; the Narrative dimension as a container relation.
- `sec:momentum-present`, including `def:free-continuation` and
  `def:internal-external` as extracted.
- `hyp:narrative-momentum` in cost form, and `rem:membership-vs-cost`,
  `rem:nothing-pushes`, `rem:irreversibility`, `rem:cost-form-substrate`.
- `rem:impulse` ("the momentum of a body is exactly the cost of stopping
  it"), `rem:currencies`, `rem:not-analogy`.
- `sec:evolutionary`: `prop:no-unheld-pending` and `rem:evo-tests` — the
  lag as description, the carried-rate falsifier kept honest.
- The inherited-status note after the list.

---

## Suggested order

1. **A**, **B**, **C** — one external document, seven refs.
2. **D**, **E**, **F**.
3. **G**.
