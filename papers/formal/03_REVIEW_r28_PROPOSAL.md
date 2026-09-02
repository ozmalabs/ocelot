# Review of `03_law_of_narrative_momentum_theory_referenced.tex` (draft-2026-09-02.1, r28) — proposal for fixes

Scope: the whole file (524 lines, 12 pp), its log and aux, and 01 r278 /
02 r26 / 04 for what it attributes to them. Line numbers are r28. Nothing
applied.

Compile: 0 warnings, 0 overfull, all twelve citations resolve and are
correct (Mayergoyz, David, Arthur, Pierson, AGM, Rao–Ballard, Schmidt,
Kirkpatrick–Lande 1989, Lande–Kirkpatrick 1990 — where "evolutionary
momentum" is indeed named — McAdam–Boutin, Thorne et al.). The cost-form
statement of the law, the "Γ decides membership; Narrative decides cost"
separation, the impulse identity and the two-currencies remark are the
paper's strength and are not questioned. The findings are one remark that
argues, retracts, and salvages in sequence; a citation of the
non-releasable construction paper; a definition 01a leans on that is not a
definition here; and cross-reference hygiene.

---

## A. `rem:evo-tests` carries an argument, its own retraction, and the salvage, in that order

l.316–389 (74 lines). The sequence:

1. l.316–319: the lag reading is "not a competitor", and staking a
   falsifier on it "would be a mistake".
2. l.321–333: an argument *against* the lag reading anyway —
   "*Transmission cannot lag, because there is no time for it to lag in*
   … the temporal metaphor borrows explanatory force it does not have".
3. l.335–337: a **second opening**, near-verbatim of the first: "The
   published account describes the effect as a *lag*, and it is tempting
   to treat that as something to correct … Neither is right, and the
   reason is this."
4. l.339–343: the retraction — "*Kirkpatrick and Lande hold the position
   this paper holds* … an argument mounted against them would be aimed at
   a position no one occupies, and the correction would be agreement
   dressed as a correction." Which is what paragraph 2 was.
5. l.345–367: the salvage — "One claim in the vicinity survives … *Nothing
   can be pending that is not currently held*", with a falsifier in a
   custom `falsifiable` environment used nowhere else in the set.
6. l.369–388: the honest limits (no cost quantity in the cited work; the
   model damps).

This is the drafting history left in place. **Fix.** One pass, in this
order: K&L's carrier is present structure and they hold this paper's
position (4); the lag is a location in causal order and not a mechanism,
in one sentence (the surviving content of 2); the one claim that survives,
promoted to `\begin{proposition}[Nothing is pending that is not held]
\label{prop:no-unheld-pending}` with its falsifier moved into the list
(5); the two limits (6). Delete the second opening (3) and the
`falsifiable` environment (preamble l.33 and its one use).

Also l.355–356 "the causal-set treatment **cited above**" — nothing in 03
cites causal sets; Bombelli is 01's citation. → "the causal-set treatment
Graphic Equalisation cites" with a `GE-` ref to 01's causal-order section.

---

## B. The construction paper is cited for a claim

l.216 (`Why the cost form is the substrate-level statement`): "a gauge
condition of the same kind **the companion construction paper** imposes on
relative weighting." A1 is outside the releasable set and must not be
cited as the source of anything. The claim (cost form is invariant under
choice of basis) stands on its own. **Fix:** drop the clause, or say "a
gauge condition: invariant under the choice of basis" without attribution.
Give this remark a label (`rem:cost-form-substrate`); it is the only
titled remark in the paper without one.

---

## C. A definition 01a builds on is stated here as a parenthetical

`rem:momentum-delta` l.154: "Put as a definition: the Narrative is what a
subgraph runs when *no rule fires* — the free continuation in its pure
form." 01a's Born recovery (`sec:amplitudes`, the *Linear* step) and 01d
rest on exactly this sentence ("Free evolution is the amplitude's own
Narrative, and a Narrative is what a subgraph runs when no rule fires").
It is buried in a 20-line single-paragraph remark. The same remark
introduces the **internal / external Narrative** distinction (l.154–156),
which 01a also uses by name.

**Fix.** Extract two numbered results before the remark:
- `\begin{definition}[Free continuation]\label{def:free-continuation}` —
  the Narrative is what a subgraph runs when no rule fires; $S$ carrying
  forward with nothing writing against it; having rules adds only the
  possibility of a write.
- `\begin{definition}[Internal and external Narrative]\label{def:internal-external}`
  — internal: $S$ read in the terms the frame's current rule set fixes;
  external: another frame's cross-frame reading of the same $S$
  ("velocity"); no rule-set-independent reading exists.
Then split `rem:momentum-delta` into three paragraphs (persistence is the
absence of an event; to change course is to write $S$; the momentum
quantity is $\Delta$ not $\Delta/\Delta T$) so it can be read. 01a and 01d
can then cite `NM-def:free-continuation` by number in a later pass.

---

## D. Cross-references and naming

1. **Names.** "Graphic Equalisation" (14), "the foundational paper" (4),
   "the substrate paper" (3), "the companion manifold paper", "the
   companion construction paper", "the companion Narrativium paper",
   "the physics companion", "Seldon-manifold theory", "Seldon manifolds".
   Draft box is the generic one. Add the naming sentence with 01's table
   names (Graphic Equalisation; *Seldon*; *Narrativium*; the physics
   companion) and the "inherits their definitions…" clause; collapse the
   rest.
2. **`xr-hyper`.** Every by-description reference to 01 has a label now:
   history principle (l.148 → `GE-cor:history`); collapse as a local write
   (l.154 → `GE-rem:collapse-write`); evaluation as a write (l.154 →
   `GE-prop:evaluation-writes`); the missing denominator (l.156 →
   `GE-rem:no-denominator`); founding axiom (l.161 → `GE-ax:no-view`);
   higher-frame principle (l.101 → `GE-prop:higher-frame`); time inferred
   (l.323 → `GE-prop:time-inferred`); no implicit historical state
   (falsifier 3 → `GE-prop:no-implicit-historical-state`); discrete
   sufficiency (falsifier 2 → `GE-hyp:discrete`); inertial =
   representational frame (l.288 → 01 `sec:scope`). To 02: dimension/value
   typing (l.85 → `SM-def:dimension`); irreversibility (l.204 →
   `SM-def:irreversible`); reachable geometry (l.66). To 04: Narrativium
   (l.405 → `NV-def:narrativium`). Add `\externaldocument` for `[GE-]`,
   `[SM-]`, `[NV-]`.

---

## E. Falsifiability

1. **"On the tags" (l.428–436)** is the pre-harmonisation text with the
   "has carried these marks for some time" history. Replace with 01's
   sentence verbatim (trailing clauses dropped as 01a/02a did); keep the
   "On a claimed class" paragraph, which is good.
2. **Items 2 and 3 carry their inherited-status caveats as italic
   parentheticals inside the item.** 01/02 pattern: one sentence after the
   list.
3. **Item 1 "First-class Narrative" is indexed to "a claimed grounding"**,
   and by the paper's own claimed-class rule only the evolutionary
   grounding (`sec:evolutionary`) is worked; `sec:groundings` lists
   candidates without claiming them. Say which is live: "live for the
   maternal-inheritance grounding; stated, not live, for the cognitive and
   institutional candidates".
4. **Missing:** `def:narrative-revision` and the proposition promoted in
   A (nothing pending unheld — move its falsifier here, `[detail]`).
   `hyp:lockin` has one (item 7) ✓; `hyp:history-projection` ✓.
5. Item 6's candour ("on present evidence this commitment is closer to
   failing than to holding") is right and should stay; but it and A.6's
   damping limit say the same thing twice — point one at the other.

---

## F. Structure and mechanical

1. `sec:groundings` (l.397–402, three short paragraphs) and
   `sec:narrativium` (l.404–405, two lines) are stub sections. Fold the
   first into `sec:prior-art` (whose second paragraph already lists the
   same three literatures) and the second into `sec:dependencies`.
2. Abstract l.52 "stated **primarily** in cost form, which is its
   **primary** commitment" — one of the two.
3. `\texorpdfstring` on the `\date` dashes; `et al.` → `et~al.` (AGM).
4. Bibliography: not alphabetical (Mayergoyz, David, Arthur, Pierson, AGM,
   Rao, Schmidt, Kirkpatrick…); initials-only author names for the first
   eight entries against full names for the last four; missing blank line
   before `kirkpatricklande1989` (l.501–502). Sort; use full names
   throughout.
5. Custom `falsifiable` environment (l.33) removed with A.

---

## What is right and should not be touched

- The cost form as the primary statement, direction recovered as the
  special case for frames that instantiate one, and the reason
  (`rem:cost-form-substrate`): a law that presupposed a basis would be
  about representations, not reachability.
- `rem:membership-vs-cost`: Γ decides membership; Narrative decides cost;
  an account that let history remove continuations would have no way to
  tell which was responsible for an absence.
- `rem:impulse` and `rem:currencies`: momentum is the cost of stopping;
  $mv$ and $\tfrac12 mv^2$ are two prices for one alteration and neither
  is more correct.
- `rem:not-analogy`: the mechanical case is an instance, not an analogy,
  and the scope guard that follows.
- The two honest limits on the biological grounding (no cost quantity;
  the model damps) and falsifier 6's admission.

---

## Suggested order

1. **A** — the remark, one pass; the custom environment gone.
2. **B** — the construction-paper clause.
3. **C** — the two definitions extracted.
4. **D** — names and `xr-hyper`.
5. **E**, **F**.
