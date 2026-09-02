# Review of `01d_graphic_equalisation_born_recovery.tex` (draft-2026-09-02.1, r2) — proposal for fixes

Second pass. Scope: the whole file (462 lines, 6 pp), its log and aux,
the r1 review and what r2 did with it, and 01a r43 for the division of
labour. Line numbers are r2. Nothing applied.

Compile: 0 warnings (the five underfull boxes gone), 0 overfull, 7
bibitems all cited, no `??`, all `GE-`/`PH-`/`NM-` refs resolve, by-name
check clean. r2 did everything r1 asked: `xr-hyper` to three papers with
the substrate paragraph reduced to seven referenced notions; the physics
cut to one-sentence pointers at the physics companion (the squared
modulus, the reconciliation, the survey); the $K$ table and
`prop:contingent` kept; the rating scale defined once and matched in the
abstract; the two narration sites rewritten; the scope-note item moved
after the list; item 1 split; the composition-seam falsifier; the table
columns ragged; the bibliography ordered. The note is now 6 pp and its
own. **What remains: one pointer at the physics companion by name
because the target subsection is unlabelled there; one claim inside a
paragraph that says it adds nothing; and two small things.**

Five of 01d's labels are cited by 01a via `BN-` (`sec:level0`,
`prop:opt`, `sec:axioms`, `prop:crux`, `sec:residuals`). All must
survive under the same names and kinds.

---

## A. The reconciliation subsection is pointed at by name

l.325–327 (`sec:reconcile`): "the reconciliation is that companion's,
**argued in its subsection on Born, SR and GR**". The physics companion's
subsection (01a l.805, "The reconciliation: Born, SR, and GR on one
substrate") is `\subsection*` with no label, so it cannot be cited by
number. The fix is on 01a's side (a label, proposed in the 01a review
this round as `sec:reconciliation`); once it exists, l.326 → "argued in
its Section~\ref{PH-sec:reconciliation}". **Apply after 01a's next
revision compiles**, and verify the label in 01a's aux.

---

## B. A claim inside the paragraph that "adds nothing"

l.63–64 (`sec:substrate`): "this section fixes the references and adds
nothing." l.74–76: "*phase* is position on that cycle rather than a
signed time (its Remark~\ref{GE-rem:phase-not-time}) — **so an amplitude
is $r\,e^{i\theta}$**." The amplitude form is the note's own
identification, not a definition from the papers, and it is the one
this note turns on. **Fix:** drop the clause here and state it where it
is used — `prop:crux` (free continuation "whose phase is a continuous
$U(1)$") or the sentence before the axiom table — as "this note reads an
amplitude as $r\,e^{i\theta}$, modulus and cycle-phase".

---

## C. Smaller

1. Abstract l.47–48: "The papers named above carry the surrounding
   framework, **and are cited by number throughout rather than
   restated**." The second clause describes the note's citation practice;
   the reader sees it. Drop the clause.
2. `prop:contingent` l.300–301 opens "The framework forces almost
   nothing." — `rem:recover` l.88 already says it. Start the proposition
   at "Complex-over-real is contingent rule-content…".
3. l.53–55 of the box: "It is an *attempt*, rated step by step, and not a
   peer-reviewed result." — fine; keeps the note's standing explicit.

---

## What is right and should not be touched

- `rem:recover`: "a contingent law can only be recovered given its
  rule-content, never derived as compelled."
- `sec:level0` and `rem:affine`; the OPT table with its ratings.
- `prop:crux` and the sentence after it.
- The $K$ table, `prop:contingent`, `rem:misframing` as retitled.
- `sec:residuals` items 1–5.
- The falsifier list with items 1 and 2 split and item 6 added, and the
  scope note in the set's form.

---

## Suggested order

1. **B**, **C** — three single-site edits, can go now.
2. **A** — after 01a's next revision carries the label.
