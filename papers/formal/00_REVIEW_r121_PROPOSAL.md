# Review of `00_is.tex` (draft-2026-09-02.1, r121) — proposal for fixes

Second pass. Scope: the whole file (1091 lines, 19 pp), its log/aux, the
r119 review and what r121 did with it, and 01 r278 / 06 r27 for every
cross-paper reference. Line numbers are r121. Nothing applied.

Compile: 0 warnings, 0 overfull, 18 bibitems all cited and correctly
formatted, bibliography sorted, propositions numbered flat (1, 2, 3), no
`??`. r121 did what r119 asked: the epistemic→ontic slide is gone (l.503–507,
534–536, 552–554 now agree); `prop:cohere` is structural with the measured
rendering set apart (l.339–361); four commitments in the order of the three
claims; falsifier 1's header is the concluded standard; the two objections
sit in their own subsection; the pointer defects are fixed; substance and
the global clock are run (l.195–196). The paper is in good shape. **What
this pass finds is small: one internal contradiction in the falsifiability
section, the set's cross-referencing convention not yet applied to the base
paper, an uncited list of confirming cases, and one clause in the figure
paragraph that says the opposite of the weak-discernibility argument.**

Seven of 00's labels are cited by other papers via `IS-` (`prop:is` ×6,
`prop:cohere` ×4, `sec:prior`, `sec:one-not-enough` ×2, `sec:one-way`,
`sec:claim`, `prop:one-way`). All must survive under the same names.

---

## A. Commitment 4 is "the easiest to test" and "not yet testable" in the same section

l.862–863: "the fourth is what the claim predicts **and is the easiest to
test**." l.912–913: "A consequence of the first and **the easiest to
test**." l.919–920: "*The commitment awaits an operationalisation of*
compression pressure *and is not yet testable without one*; the proxy
offered meanwhile is the formalism the field's standard textbook teaches,
read across successive editions."

Both cannot stand. The r119 fix (F) added the honest second sentence
without removing the first. **Fix:** "the easiest to test once
*compression pressure* is operationalised, and the one for which a proxy
is offered meanwhile" at l.863, and drop "the easiest to test" at l.913.
If the textbook-editions proxy is meant to make it testable now, say that
instead and drop "not yet testable".

---

## B. Cross-references: the base paper is the one paper still citing by description

00 has no `xr-hyper`. It refers to 01 nine times as "the companion" and to
06 twice as "the companion on assessment", always by description. Every
target exists in the current aux files:

| line | phrase | target |
|---|---|---|
| 180–181 | "Axiom −1 of the companion … insists on" (description length needs a vocabulary) | `GE-ax:no-view`; the vocabulary point is `GE-rem:mdl-ontic` ("the constant is the frame") |
| 250 | the frame-governing axiom "arrives with the machinery it constrains, in the companion account" | `GE-ax:no-view` |
| 264 | "the companion settles that they are not, distinctness being forced where sameness is supplied" | `GE-rem:types-forced` |
| 265–266 | substance returning inside the sentence that decomposed it | `GE-rem:one-substance` (now generic; cite as the place the refusal is made) |
| 420–421 | "the companion is explicit that a structure with no rules of its own is still a frame" | `GE-def:frame` — **verify the wording**: 01 r278 does not contain "no rules of its own"; find the sentence or state it on 00's own terms |
| 528–529, 538, 544 | "the companion's numbering of it as Axiom −1" | `GE-ax:no-view`, and 01's remark on why it is numbered −1 (`rem:why-minus-one`, verify) |
| 713–715 | "the companion's own ledger … a realisation operator and a destroy/preserve distinction" | `GE-tab:ledger` (verified: 01 l.413 lists exactly those two) |
| 729 | "the record of its application is in the companion on assessment" | `AS-sec:turned` (The same demand, turned on this work) |
| 813 | the trivial-or-wrong pairing "is in the companion on assessment" | `AS-sec:objection` (l.992–994: "the same claim is both trivial and consequential") |
| 963 | "decoheres, in the companion's exact sense" | `GE-prop:decoherence-one` |

**Fix.** `xr-hyper` + `\externaldocument[GE-]{01_…}` and `[AS-]{06_…}`,
hyperref after xr-hyper; each row a resolving `\ref` with the paper
named. Draft-box naming sentence: Graphic Equalisation and the assessment
companion, using 01's table names — **without** the "inherits their
definitions" clause, since 00 is the base and defines its own terms; say
instead that the companions presuppose this paper (which l.50 already
does). Compile order: 00 is compiled first today because nothing it cites
exists yet; after this it depends on 01's and 06's aux, so the build
becomes 01 → 06 → 00 → 01 (×3) or, simpler, 00 cites only labels and is
compiled last in the first pass.

Also three sections carry no label and so cannot be cited from the set:
l.338 "Coherence, and what fails to cohere", l.579 "A consequence with a
track record", l.691 "What the companions add". Add `sec:cohere`,
`sec:track-record`, `sec:companions`. 05 and 01 cite `IS-sec:one-not-enough`
for the two-zeros point today; `sec:cohere` is the one 01's `rem:cohere`
should point at.

---

## C. The confirming cases for the prediction are uncited

l.608–614: "physics reaching for spin networks, tensor networks and causal
sets; chemistry settling on the molecular graph; linguistics on dependency
structure; computing on data structures that are graphs and on a
categorical foundation in which the morphisms are primitive and the
objects recoverable from their identities; neuroscience on the connectome;
biology on phylogenies and interaction networks." Seven fields, no
citation, in the paragraph that carries the paper's one empirical
prediction — beside a double-entry case that carries seven. The set's
standard elsewhere (10 r5) is one citation per empirical claim.

**Fix:** either cite one canonical source per field (Penrose 1971 spin
networks; Bombelli–Lee–Meyer–Sorkin 1987 causal sets; Orús 2014 tensor
networks; Tesnière 1959 / de Marneffe–Nivre 2019 dependency; Mac Lane
1971 for morphisms-primitive; Sporns–Tononi–Kötter 2005 connectome; Felsenstein
2004 phylogenies) or mark the list explicitly as illustrative and let
commitment 4 rest on the one worked case. The first is a dozen bibitems;
the second is one clause. The paper's own l.665–669 ("the prediction is
about movement, not about drawability") means the list only helps if each
entry is a *movement* the source documents, which argues for the second
option unless someone will check the seven.

---

## D. The figure paragraph says position makes the marks two; the argument says the relation does

l.94: "What makes the marks two is their position on the page and nothing
in them." l.482–483: "What makes them two is the irreflexivity of the
relation between them." The figure paragraph is about the *drawing*
(position is what the page supplies) and the later passage is about the
*relata* (weak discernibility), and l.94 does say "All of that is supplied.
What is not is that there is a difference here at all." But a reader
meets l.94 first and reads "position makes them two" as the paper's
answer to the question `sec:graph` calls "the sharpest place to press".
**Fix:** one clause at l.94: "What makes the *marks* two is their position
on the page, which the page supplies; what makes the *relata* two is the
relation between them, which Section~\ref{sec:graph} argues and nothing
in the drawing shows."

Also l.94 is one 110-word paragraph in one sentence-run; split after
"demonstrates what it states rather than illustrating it."

---

## E. Smaller

1. Falsifier 1, l.886: "A claim about this instance and not about every
   possible one" — "this instance" is not defined; l.572–577 say "this
   world". Use "this world".
2. l.421 "no rules of its own" attribution — see B; if 01 does not say it,
   00 should not say 01 does.
3. l.826 "Pacioli in 1494 to Hamilton in 1837" — the 1837 is Hamilton's
   algebraic couples, which the paper does not name; "Hamilton's ordered
   couples of 1837" so a reader knows what was written down.
4. `\texorpdfstring` on the `\date` dashes (l.11); 00 is now the only
   released paper without it.
5. l.729 "(*Assessing an Account of This Kind*)" and l.813 "the companion
   on assessment" — use 01's table name once ("the assessment companion")
   after the box names it.

---

## What is right and should not be touched

- `sec:claim`'s placement of the one commitment at l.70–78 and the three
  separated claims; the four words and "the verbs" (l.135–144), which is
  the tool the rest of the paper now correctly uses on itself.
- `sec:method` l.157–166 (metalanguage vs base) and l.203–228 (a removal
  must be named and restorable; idealisation by subtraction, not
  distortion).
- `prop:cohere` as restated, and l.353–361 keeping the measured rendering
  as what the companions use.
- `sec:one-way` entire, especially l.408–415 (modelling as the only
  access) and l.430–431 (the base is a frame in every account that models
  it and contains none).
- `sec:graph` l.479–489 (weak discernibility) and l.498–536 as corrected:
  "a claim about the account and not a proof about the world".
- The double-entry case with Ellerman's refutation of the minimality
  reading and Yamey/Sangster as counterweight.
- `sec:falsifiability`'s opening on kinds of claim, and the first objection's
  handling ("*I tried and got nothing back* is a different result from
  *there was nothing to try*").

---

## Suggested order

1. **A** — one contradiction, two clauses.
2. **B** — `xr-hyper`, the three labels, the naming sentence; build-order
   note.
3. **D**, **C** (decide cite-or-mark), **E**.
