# Review of `00_is.tex` (draft-2026-09-02.1, r119) — proposal for fixes

Scope: the whole file (1073 lines, 18 pp), its log/aux, and the places the
monograph (01) cites it. Line numbers are r119. Nothing applied.

Compile is clean: 0 warnings, 0 overfull, every `\cite` has a `\bibitem`,
every `\ref` a `\label`. So unlike 01 there is nothing mechanical to fix
first; the findings are about what the paper says. Ordered by severity.

---

## A. The epistemic→ontic slide is back, in the paragraph after it is refused

Commit 01de8718 (r115) fixed this once — "the referee found a slide from
epistemic limit to ontic absence, and it was fatal as written". It has
returned in `sec:graph`, and the two paragraphs contradict each other.

- **l.503–510 (correct):** "an argument running from the first to the
  second is the slide from an epistemic limit to an ontic absence. The
  prohibition below constrains what may be *claimed*. It does not by itself
  empty the world of whatever no claim could reach, and this paper does not
  get to have it both ways."
- **l.512–520 (correct):** the MDL step is "a claim about the account and not
  a proof about the world … weaker than a demonstration of impossibility".
- **l.522–538 (the slide):** the zero-bits argument concludes "So what
  survives every standpoint is the bare relational minimum, and the bare
  relational minimum is a graph. The graph is not selected for convenience;
  **it is what is left when no vantage is allowed to add anything**." —
  "what is left" is ontic. What survives every *standpoint* is what may be
  *claimed*; the paragraph at l.503 just said those are different questions.
- **l.555–556 (the slide, sharpened):** "**A world** in which some structure
  has an intrinsic form readable from no standpoint would violate it." A
  constraint on claims (l.508) cannot be violated by a world. Only a claim
  can violate it.
- **l.461–462:** "*Everything is a graph* — and that sentence is the whole
  thesis" vs **l.707–710:** "This paper does not assume that everything is a
  graph. It establishes that … the bare untyped graph is the least ontology
  this account may retain." Commit b018847e said the graph conclusion "said
  three different strengths in three sections"; it still says two.

**Fix.** State the strength once, at l.461, in the sec:graph-licensed form
("the bare untyped graph is the least ontology this account may retain"),
and make every later sentence agree:
- l.536–538 → "So what survives every standpoint *as a claim* is the bare
  relational minimum, and what this account retains is therefore a graph.
  That is what the discipline leaves; it is not what the world is shown to
  lack."
- l.555–556 → "A *claim* that some structure has an intrinsic form readable
  from no standpoint would violate it; a world is not the kind of thing that
  can."
- l.461 → "*Everything is a graph* is the companions' thesis. What is
  established here is narrower and is all they need: …"

This is the one item a hostile reader lands on first, and the paper's own
l.174–175 asks for exactly this defect to be "reported as one rather than
absorbed".

---

## B. `prop:cohere` is stated in the reading the paper says is not the ground

- **l.127–137** ("What the words carry"): coherence is *structural* — "a
  relation coheres when its ends are distinct … stated as a condition and
  not derived … The informational reading … *agrees* with it here … The
  agreement runs in that direction only. The base condition is structural;
  the informational criterion is what it becomes once there is something to
  measure with."
- **l.350–356, the proposition itself:** "A relation suffices only where it
  *coheres*: **where what it reports about one end given the other was not
  already given**." That is the informational reading, verbatim.
- **l.362–364:** "To cohere is for a relation to *carry* something — a fact
  about one end given the other that was not already had — which makes the
  criterion **a quantity**."
- **l.369–376:** "neither [reading] grounds the condition … The verdict is
  settled without a frame."

So the proposition is worded in the reading the gloss says is derivative,
and l.364 calls it a quantity while l.130 says it "is not an epistemic
measure". Worse, **01 relies on 00 having done this right**: 01's
`rem:cohere` (l.773–779) says "At the base the condition is structural — a
relation coheres when its ends are distinct — and the companion states it
that way for the reason it gives." The companion does not state it that way.

**Fix.** Restate `prop:cohere`:
> A relation suffices only where it *coheres*: where its ends are distinct.
> Neither degenerate case is a thing that fails the condition: where no
> relation holds there is nothing to cohere, and where the only relation is
> to oneself the ends are not two. In both, what fails is the *description*,
> which picks out nothing. Relation is necessary; coherence is what makes it
> sufficient.

Move the "carries something / not already given / a quantity" wording
(l.362–366) into a paragraph explicitly labelled as the measured rendering
the companions use, matching l.132–137.

---

## C. "Relation is what carries information" is used as a base premise

l.523–532: "A view is informative in proportion to the relation … a relation
is what carries information; so a standpoint in no relation to what it
views carries nothing about it." This derives the prohibition from bits. But
l.130–131 says the informational reading "requires no informational state,
language, frame or evaluator, none of which exist at this level and all of
which the account would have to buy." Using *informative*, *bits*, *delivers*
at the base is the metatheory/base slip l.166–175 names and asks to have
reported.

l.540–543 half-repairs it ("used as a constraint on claims rather than as
the ontological premise") — but only after l.536–538 has drawn the ontic
conclusion (item A). **Fix:** open l.522 with "In the metatheory, where
there is something to measure with, the denial is sharper as a measure…",
and let the conclusion at l.536 be about claims (A). Then C dissolves into A.

---

## D. Two triads that do not line up

`sec:claim` l.89–94 separates **three claims**: (1) determinacy is
relational; (2) time, cause, rule, observer are not entailed by it; (3)
removal-against-MDL is a reasonable audit. `sec:falsifiability` l.863 has
**three commitments**: (1) to be is to be related; (2) compression moves
toward graph form; (3) the method's yield is low.

Claim (2) — separability — is not commitment (2). Its falsifier exists but
sits *outside* the list at l.969–973 ("A second thing would count against
the paper without falsifying the proposition … if time, cause, or rule
turned out not to be separable"). A reader maps claim (2) onto commitment
(2) and gets the wrong test.

**Fix:** four commitments, in the order of the three claims plus the
prediction:
1. To be is to be related (claim 1).
2. Time, cause, rule and observer are separable (claim 2) — the text at
   l.969–973, promoted into the list.
3. The method's yield is low (claim 3).
4. Compression moves toward graph form (the prediction, "a consequence of
   the first").

---

## E. Falsifier 1's "Fails if" clause contradicts its own conclusion

l.879–883: "Fails on the exhibition of an extant something standing in no
relation whatever." Then l.885–915 argues, correctly and at length, that
such an exhibition "cannot be a coherent counterexample" and that the real
challenge is "an intelligible counterexample, or a rival account with lower
cost at equal or better coverage" (l.901–902). The header clause and the
conclusion disagree inside one item.

**Fix:** make the header clause the concluded standard: "Met by an
intelligible counterexample — a determinate something for which standing in
any relation is *coherently* deniable — or by a rival account at lower cost
and equal coverage. An unrelated existent merely *asserted* is not one:
the attempt decoheres, and that outcome is checkable (below)."

Also: the item carries four paragraphs of objection-handling *inside* the
`enumerate`, and a second objection to the same item is handled *outside*
it at l.947–967. Put both in one `\subsection*{Two objections to the first
commitment}` after the list.

---

## F. Falsifier 2 is stated, declared failed, then restated

l.925 "Read strictly, that is already failed, and the failure is visible in
this paper's own worked example." A commitment that announces its own
failure and then narrows is narrated revision. **Fix:** state only the
narrow form (bearer-of-distinction, l.930–934), and keep the arity/count
observation as the *reason* for the wording, not as a retraction. The
"remaining hole" (no operationalisation of *compression pressure*, l.935)
means the commitment is not yet testable; either say so in the header or
supply a proxy ("the formalism the field's standard textbook teaches, across
successive editions").

---

## G. `[shape]`/`[detail]` used, never defined; item 3 mis-marked

The marks are 01's vocabulary (01 l.2677 defines them). 00 uses `[shape]`
on all three items without definition. And item 3 ("The method's yield is
low") is, by l.91–94, methodological — "can fail without touching the
first" — which is a `[detail]` by 01's definition (survives with a mechanism
replaced), not a `[shape]` (costs range). **Fix:** one sentence defining the
marks, or drop them from 00; re-mark item 3 `[detail]`; item 4 (compression)
is also `[detail]` — the paper says so itself at l.611 ("a prediction about
the history of formalisms rather than about the world").

---

## H. Stale cross-paper claim

l.273–274: "*Substance* is worse, being already on the list and returned
anyway in a companion's own sentence about having decomposed it away." 01's
`rem:one-substance` (l.695–700) now *refuses* "one substance" explicitly
("One substance is not the correction to three kinds of thing; *no*
substance is"). The sentence 00 accuses no longer exists. **Fix:** make it
generic — "Substance is the worse case: already on the list, it can return
inside the very sentence that claims to have decomposed it away" — so it
stops depending on the companion's current text.

---

## I. "Everything is a frame" vs "the base has no frames"

- l.212–213: "an idealisation is just a frame — which is no defence on its
  own, since **everything is one**."
- l.220–222: "Nothing described here is individuated by anything, and
  everything real is."
- l.426–427: "a structure with no rules of its own is still a frame".
- l.433–436: "a level at which nothing runs has nothing doing it, so **it has
  no frames**".

These reconcile (the base is not a thing anyone meets, l.223; it is a frame
*in every account that models it* and has none *within* it), but the paper
never says so in one place, and l.213's "everything is one" is read against
l.435 within twenty lines. **Fix:** one sentence at l.433: "The base is a
frame in every account that models it — this one included — and contains
none, there being nothing in it to instantiate one."

---

## J. Pointer and antecedent defects (mechanical)

1. l.588 "contradicts the accounting **two sections above**" — from
   section 7 that is section 5 (`sec:one-way`); the accounting is in
   section 2. Fix: `Section~\ref{sec:method}`.
2. l.262 "which forces the graph **above**" — the graph is section 6,
   below. Fix: `(Section~\ref{sec:graph})`.
3. l.445–450: "The other half of that axiom … is retained: denying that any
   characterisation is privileged says nothing about acts or frames … **It
   arrives with the machinery that performs them.**" The final "It" now
   says the *retained* half arrives with the machinery. It is the *removed*
   (act-governing) half that does. Move that sentence to follow "there are
   no acts here" at l.446.
4. l.150 "One consequence of **the last of the four** is worth stating" —
   "the four" are the four nouns, but the paragraph "The verbs" intervenes.
   Move l.150–153 to before "The verbs" (l.139).
5. l.236 "**It** also has to come first" — antecedent (this paper) lost
   across the spherical-cow paragraph. "This paper also has to come first".
6. `prop:is` is labelled and never `\ref`'d; l.107, 358, 361 say "the first
   proposition". Use `Proposition~\ref{prop:is}`.
7. "The companion" (singular, unnamed) at l.189, 272, 273, 426, 530, 716,
   908 — 00 has no companion table. Name it once at first use (l.189): "the
   companion (*The Law of Graphic Equalisation — Theory*, hereafter *the
   companion*)". "the companion on assessment" (l.734, 817) is a different
   document and should be distinguished.
8. l.306–308 and l.942–944 both say the base rate was reconstructed not
   recorded. Say it once, at the commitment.
9. l.716–717 "corrected after audit and moved in both directions since",
   l.732–733 "has moved the count more than once" — narrated revision, and
   about the *companion's* drafting at that. Cut.

---

## K. Proposition numbering drifts across companions

`\newtheorem{definition}{Definition}[section]` with propositions sharing
that counter yields **1.1, 4.1, 5.1** for a paper with three propositions.
01 cited "Propositions 1.1–1.2" and "Proposition 8.1" — both wrong today
(see 01 review A.1). **Fix:** for 00 only, number propositions flat:
`\newtheorem{proposition}{Proposition}` → 1, 2, 3. Then 01's citations
become "Is, Propositions 1–2" and "Is, Proposition 3", and stop drifting
when a section is added. Coordinate with the 01 agent's `xr`/`@xref` fix so
whichever mechanism lands reads the new numbers.

---

## L. Candidate list vs removals actually run

l.201–208 runs three removals (time, cause, rule) and concludes "it stops
in one place". l.250–254 then lists seven candidates: time, causation,
substance/intrinsic nature, an observer, a privileged frame or global
clock, admissibility, and an axiom restricting where a distinction is made
from. Observer is argued in `sec:one-way`; the frame-axiom at l.256–258 and
l.445; *substance* and *global clock* are never run — only listed. **Fix:**
one line each at l.201 ("Substance can go: nothing here bears properties;
a relatum is an end. A global clock can go with time."), or say the list
records what *was* tried and where.

---

## M. The rock is the embedded case, not the posited one

l.214 "The rock is what this claim looks like at the grain at which it is a
rock" uses the rock to illustrate the *base*. l.403–408 then separates two
cases: the base *embedded* (a rock, "met, related to, distinguished by
something that does have the machinery") and the base *posited*, "embedded
in nothing". The rock illustrates the first; l.220–223 says the posited base
"is not a thing anybody meets". A rock is. **Fix:** at l.214, "The rock is
what this claim looks like *from outside*, at the grain at which it is a
rock — the embedded case of Section~\ref{sec:one-way}; the case this paper
posits has no outside and no rock."

---

## N. Prose (representative)

- l.57 abstract: "and --- nothing containing it --- cannot be observed
  either" → "and, where nothing contains it, cannot be observed either".
- l.464–471: one ~100-word sentence; split at "A node is an *end*…" and
  again at "— the reverse of the order…".
- l.545–547: "and why it has to be a prohibition rather than another
  removal explains the companion's odd numbering" — garbled. → "…the one
  prohibition it has. Why it must be a prohibition rather than a removal
  is also why the companion numbers it as it does."
- l.853: 45-word sentence; split at "since nobody could…".
- Double blank lines at l.247–249, 280–282.
- Preamble: `\Poss`, `\Coll`, `\Hist`, and the axiom/theorem/hypothesis/
  corollary/definition/remark environments are unused (copied from 01).
  Harmless; remove or leave.
- `\bibitem[Sangster(2016)]{sangster2015}` — key year ≠ label year.
  Rename key `sangster2016` (one `\citet` at l.641).

---

## What is right and should not be touched

- The Ellerman / Pacioli / Lee / Yamey / Sangster chain checks out
  (Farolfi 1299–1300; *Particularis* 1494; Cayley 1894; group of
  differences). The counterweight paragraph (l.637–647) is exactly how a
  contested history should be reported.
- Weak discernibility via Black 1952 / Saunders 2003 for $K_2$ is the
  correct citation and the correct notion; the "sharpest place to press"
  paragraph (l.482–492) is the best-argued page in the set.
- The metatheory/base distinction (l.166–175) is right and is the tool
  that fixes A, B, C; the paper only needs to apply it to itself at the
  three places above.

---

## Suggested order

1. **A** (with C folded in) — the fatal-as-written slide, one section.
2. **B** — restate `prop:cohere`; this also makes 01's `rem:cohere` true.
3. **D + E + F + G** — one pass over `sec:falsifiability`.
4. **J, H, I, L, M** — pointers and single sentences.
5. **K** — with the 01 numbering fix, not before it.
6. **N**.
