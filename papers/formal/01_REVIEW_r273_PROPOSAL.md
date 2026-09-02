# Review of `01_law_of_graphic_equalisation_theory_referenced.tex` (draft-2026-09-02.1, r273) — proposal for fixes

Scope: the whole file (3197 lines, 71 pp, ~43.7k words), its compile log, its
`.aux`, `01s.spec`, and the companion `.aux`/headers where the paper cites them
by number. Line numbers are r273. Nothing below has been applied.

Ordered by what breaks a reader first. Each item: **where — what — fix**.

---

## A. Verified defects (mechanical; fix without discussion)

1. **Companion citations by number are wrong.**
   - l.212 `\emph{Is}, Proposition~8.1` — `00_is.aux` has no 8.1. The
     observation-is-one-way result is **Proposition 5.1** (`prop:one-way`).
   - l.397 `\emph{Is}, Propositions 1.1--1.2` — there is no 1.2. The two
     propositions are **1.1** (`prop:is`) and **4.1** (`prop:cohere`).
   - l.2627 `\emph{Is}, Proposition~1.1` — correct today.
   - Fix now: correct the numbers. Fix properly: stop hard-coding companion
     numbers (see E.2).

2. **Second axiom prints as "Axiom 0".** l.203 `\setcounter{axiom}{-2}` makes
   `ax:no-view` = −1 (intended) and `ax:no-time` (l.2016) = **0**
   (`.aux` confirms). `rem:why-minus-one` argues −1 sits *before the counting
   starts*, i.e. before Axiom 1. Fix: `\setcounter{axiom}{0}` immediately after
   `\end{axiom}` at l.206, so the time axiom is Axiom 1.

3. **Document-count sentences are stale, twice.**
   - l.57 "Seventeen documents … refers to the other sixteen", l.58 "One of the
     twelve", l.89 heading "Why these are twelve documents and not one". The
     table lists 17; the directory holds **19** `.tex` (see A.4); "twelve" is
     two bumps old.
   - l.169–171 "nineteen definitions, twenty-seven propositions, **forty**
     remarks, six corollaries, four hypotheses, two theorems, two axioms …
     over **eighty-three** references." Measured: 19 / 27 / **42** / 6 / 4 / 2 /
     2 = **102**, not "a hundred"; **84** `\bibitem`s, 83 cited.
   - "refers to the other sixteen" is also false in substance: the CAN, audit,
     adaptability ×2 and applied papers appear **only** in the table row.
   - Fix: this is exactly the count-shaped-claim defect CLAUDE.md retracts
     elsewhere. Either (a) have `tools/build_statement.py` emit a
     `01.counts.tex` with `\newcommand{\nRemarks}{42}` etc. and `\input` it, or
     (b) drop the numbers ("some hundred numbered results over eighty-odd
     references"). (a) is preferred; the build already parses the file.

4. **Two companions missing from the companion table (l.63–87).**
   `01c_graphic_equalisation_cosmology_grounding.tex` (r6, same version
   string) and `10_applied_graphic_equalisation.tex` (r3, same version string)
   are not listed. l.610's "the companion result that reasons from a rock's
   being a frame to the universe's being one" is almost certainly 01c and is
   unnamed. Fix: add both rows; name 01c at l.610.

5. **Uncited bibliography entry.** `heinlein1973` (l.2937) is never cited.
   Cite or delete.

6. **Stale self-reference to a section as "this remark".** `sec:crossings` is
   a `\section`, but l.1714 "The remark so far", l.1723 "a mechanism this
   remark was missing", l.1891 "this remark's opening asked about who pays"
   still call it a remark. Fix: "this section".

7. **Dangling antecedent.** l.1189 "That also corrects the class named a moment
   ago, which was drawn too narrowly. An information hazard is…" — nothing in
   the preceding 40 lines names information hazards; they are introduced 500
   lines later in `sec:crossings`. Fix: delete "That also corrects the class
   named a moment ago, which was drawn too narrowly." and forward-reference:
   "Section~\ref{sec:crossings} will use this: an information hazard is…".

8. **Duplicated sentence.** The body of `prop:economics` (l.1267) and the
   paragraph after it (l.1273) both say, nearly verbatim, "whether continuation
   is free *simpliciter* … is set by the rules of the superframes, which may
   sustain a frame without charge or require a write to keep it standing, and
   [nothing in] the substrate [does not] decide[s] between them". Keep one
   (the proposition's).

9. **Stale pointer.** l.2674 "which is a record and not a proof, and is
   reported *above* with its gaps" — the implementation record was moved to
   the assessment companion (l.2659–2662 says so two sentences earlier). Fix:
   "reported in that companion".

10. **Stale pointer.** l.2755 "after the commitments for
    Section~\ref{sec:residual}'s newer material were written" — the newer
    material (handlers, vacancy, supply) lives in `sec:decoherence`, not
    `sec:residual`.

11. **Broken syntax from stacked dashes.**
    - l.1064 "…is therefore \emph{absent} --- it is simply absent to the frame
      --- there is nothing there for it to hold or to be disturbed by ---
      rather than residual." Three dashes, and "absent — it is simply absent".
      Fix: "…never enters and is therefore \emph{absent} rather than residual:
      there is nothing there for the frame to hold or be disturbed by."
    - l.1087 "the third thing --- unattested rather than excluded, since
      Proposition~\ref{prop:no-free-lunch} is an observed universal and not a
      prohibition: getting the result without anyone having paid." The colon
      after the aside attaches to the wrong clause. Fix: move the aside to a
      trailing sentence.
    - l.1338 `rem:nothing-compulsory` "…a collapse needs something to select
      from --- so **they** are what an efficient graph accretes" — "they" (the
      two gates) is lost across two dash-asides. Split into two sentences.

12. **Sentence in the wrong paragraph.** l.1176–1179: "There is a third,
    narrower use in the companion on assessment … and is not this word. **It
    fails the feasibility gate and not the desirability one.**" — the "It" is
    the boots arrangement from *before* the terminological caution; the
    caution was inserted mid-argument. Fix: move the caution (l.1170–1177,
    "One terminological caution … not this word") to after l.1179, or to a
    footnote.

13. **Editorial note left in the text.** l.2348 "What follows belongs here,
    after the proposition it follows from, rather than upstream of the premise
    a reader needs to have met." Delete.

14. **Unclear ordinal.** l.2214 "This is not a *fourth* answer to what is
    compulsory" — no three prior answers are enumerated anywhere. Fix: "This is
    not a further answer…".

15. **Inconsistent reference style.** l.2263 `\S\ref{sec:falsifiability}`;
    everywhere else `Section~\ref{…}`.

16. **Compile warnings** (all cosmetic, all fixable in the preamble):
    - `hyperref: Token not allowed in a PDF string` ×2 — from `$-1$` in the
      section title l.202 and `\textemdash`/`\textbullet` in `\date`. Fix:
      `\section{Axiom \texorpdfstring{$-1$}{-1}: …}` and
      `\texorpdfstring{\textemdash}{—}` in `\date`.
    - `Font shape T1/lmr/bx/sc undefined` — `\textsc{[shape]}` inside the bold
      `\paragraph` at l.2689. `T1/lmr/m/scit` — `\textsc` inside `\emph`.
      lmodern has no bold/italic small caps. Fix: `\usepackage{cfr-lm}` or
      wrap those with `\textnormal`.
    - `\renewcommand\thepart{\Roman{part}}` (l.28) is a no-op in `article`.
    - Load `hyperref` after `geometry`/`fancyhdr` (currently before).

17. **Bibliography style drift.** `et~al.` vs `et al.` (e.g. bombelli1987 vs
    bollinger2007, jaffe1993, jonsson2008, kocher2019, mani2013, osvik2006,
    smith2013, basiri2016); those same entries omit the full-author list in
    the `\bibitem[...]` optional argument that the others carry. Normalise.

---

## B. Argument-level inconsistencies (need the author's decision)

1. **`[shape]` "Cost is the write" (l.2701) contradicts two remarks.**
   - `rem:writeability` (l.1341): the distribution of costs is "a pattern
     rather than a universal … a structure with a different writeability
     profile **refines the characterisation rather than breaking the
     substrate**" — that is the definition of a `[detail]` failure (l.2677).
   - `sec:prohibition` (l.2210): "That a frame cannot decide anything without
     writing is the write-economics, which Remark~\ref{rem:writeability}
     carries as a pattern rather than a universal."
   - And `rem:evaluation-writes` makes reads *be* writes, so the falsifier
     "if reading … must be paid for with a cost that is not the cost of the
     write" can never fire — a paid read is redescribed as a write. This is the
     absorbs-its-own-falsifier pattern the paper explicitly defends for
     *Minimal graph sufficiency* (l.2723) and does not address here.
   - Proposal: either re-mark it `[detail]` with `rem:writeability` cited, or
     rewrite the falsifier so it names something a read-as-write cannot absorb
     (e.g. *the boundary relation itself* or *retention* carrying a cost
     that is not any write's — those are the two non-write costs the remark
     itself names).

2. **The graph is derived from this paper's economics, and this paper
   presupposes the graph.** `rem:axiom-in-bits` l.248–258 licenses the
   companion's bare-graph conclusion via "the fourth and silent cost of
   Definition~\ref{def:well-formed}". But l.135–148 say this paper
   *presupposes* the graph as the companion's result and its own axioms
   concern only change in it. Using downstream economics (which needs
   *happening*, the one thing the companion does not have) to underwrite the
   companion's static base inverts the declared dependence — the same shape
   the paper diagnoses for MDL at l.340–345 ("if the method is a consequence
   of the account, the method cannot be independent support"). Proposal: state
   at l.248 that this is a *consistency check* ("the economics agrees with the
   companion's own argument") and not a step the companion needs, exactly as
   `rem:mdl-ontic` does for MDL.

3. **Is Γ required or an optimisation?** `def:graph` makes Γ a component;
   `rem:only-g` says r and Γ together "buy occurrence"; `rem:inherited` files Γ
   as "taken to follow"; `rem:nothing-compulsory` calls the two gates
   "optimisations … not constituents of graphhood", and l.545–548 of the ledger
   then says the frame interface is *not* a consequence for that reason. The
   reconciliation exists (l.1338: an everything-admitting Γ is still a Γ,
   because P is defined through it — what is optional is *restrictiveness*)
   but is buried mid-remark and not stated where the tension first appears.
   Proposal: one sentence in `rem:only-g`: "Γ is definitional — an
   everything-admitting grammar is still the grammar P is written over —
   and what Remark~\ref{rem:nothing-compulsory} calls an optimisation is the
   *restrictiveness* of its two faces, not its existence."

4. **Two Theorems, neither proved to theorem standard.**
   - `thm:no-frame-free` (l.1025) has no proof at all.
   - "The grammar is the loop" (l.967) has a three-sentence proof that asserts
     the conclusion.
   Proposal: downgrade both to Proposition, or give `thm:no-frame-free` the
   short argument it deserves (it follows from `def:frame` + Axiom −1 in two
   lines: identity is an `Id_W` edge; an edge is instantiated by a frame; no
   frame-free instantiation).

5. **The near-uniqueness posit is labelled a posit twice and named a third
   way.** `prop:convergence-observed` (l.2343) and the paragraph under
   `prop:compression-convergence` (l.2370–2376) each say it is "an empirical
   posit … labelled again where it is used"; the ledger (l.540) calls it "the
   near-uniqueness of the cheap cut"; falsifier 1 calls it "the posit".
   Proposal: one `\begin{hypothesis}[Near-uniqueness of the cheap cut]
   \label{hyp:cheap-cut}` placed before `prop:convergence-observed`, referenced
   from all four sites. This also makes it pullable by the statement.

6. **"Empirical instance" remark (l.2063) cites nothing.** It reports a
   measurement ("it has been measured … a perceptual system given ordered
   frames … infers a transition generator") with no pointer. The paper's own
   rule (l.59) is that built-and-ran claims cite the construction paper or the
   adaptability implementation. Add the pointer or soften to "is measurable".

7. **`cor:locked-in`'s "a living substrate does not admit stop"** (l.1920) is
   stated as if universal; the falsifier "Self-change is subset-change"
   (l.2702) then treats self-termination-without-container as a `[shape]`
   failure. But `rem:supply-not-containment` shows termination follows
   *supply*, so a graph whose supply is self-contained could stop itself by
   withdrawing its own supply. Either say why that case is excluded, or
   restrict the corollary to container-supplied frames.

8. **`rem:decay`'s four cases are enumerated out of order.** l.2290 introduces
   "a fourth that is admissible and unattested" before the three have been
   listed. Reorder: three cases, then the fourth, then the falsifier.

9. **Naming: "Graph Law" (5×) vs "Graphic Equalisation" (11×) vs "the Law".**
   `prop:determinism`, `cor:reactive`, l.2581, l.2651 use "Graph Law" with no
   definition. Add once, at the hypothesis (l.949): "…(hereafter *the Law*, or
   *the Graph Law* where the contrast with a grounding's laws matters)".

---

## C. Structure: promote, split, label

The statement is generated by `@pull` on labels, and `[shape]` falsifiers
point at remarks. Both push toward the same fix: **the load-bearing claims
currently inside 150-line remarks need to be numbered results of their own.**

1. **Split `rem:inherited` (l.382–570, ~190 lines).** It is a subsection
   wearing a remark's clothes. Proposal:
   - The table → a captioned `table` environment, `\label{tab:ledger}`.
   - The five status paragraphs stay as the remark body.
   - The excursion l.471–511 ("A change is paid for in change … not available
     here") is about `prop:no-free-lunch`, not the ledger. Move it to
     `sec:interface` as `\begin{remark}[Funding is category-preserving, not
     closed]\label{rem:funding-category}` directly after `prop:no-free-lunch`.
   - The candidate list l.452–457 ("The candidate list this minimality claim
     was tested against is…") belongs to the "least graph that does anything
     is a rule" claim at l.424–428, not after the empty-set rival argument.
     Move it up.
   - "Two unpaid entries, not one" (l.496–502) argues against an earlier draft
     of itself. The table already says "one of two". Cut to the one sentence
     that survives ("Nothing forbids two brute facts, so no argument from
     scarcity is available").

2. **Split `rem:decoherence-one` (l.1392–1548, ~155 lines).** Falsifier 16
   (`[shape]`, "Decoherence is one operation") points at a *remark*. Proposal:
   - `\begin{proposition}[Decoherence is one operation; the frames are what
     differ]\label{prop:decoherence-one}` — l.1426–1430, three sentences.
   - `remark[Write versus read: $2+2=5$ is not false]` — l.1403–1419.
   - `remark[The handler analogy, and what the substrate does not fix]` —
     l.1440–1485 (analogy, computing conventions, economics).
   - `remark[Prior art: handlers as policies]` — l.1460–1466 + l.1507–1539.
   - `remark[The physical case: criticality]` — l.1486–1505.
   - `remark[The second string is not false]` — l.1541–1547.
   The statement then pulls the proposition, not 155 lines.

3. **Split `rem:cost-to-zero` (l.1103–1264, ~160 lines).** It contains the
   capability/accessibility distinction that `sec:crossings` and falsifier 21
   (`[shape]`) depend on, plus Coase/Maynard Smith, scarcity, R&D, and the
   fourth cost. Proposal:
   - Keep `rem:cost-to-zero` to l.1104–1121 (the two readings + prepayment).
   - `remark[Sideways and up: externalising versus moving up]` l.1127–1166.
   - **`\begin{definition}[Capability and accessibility]\label{def:capability}`**
     from l.1181–1187, then `remark[Aperture is purchased, so the two couple
     over time]` l.1202–1231 (with the Mani/Mullainathan evidence).
   - `remark[The third cost: finding the structure]` l.1239–1263.

4. **Consolidate `sec:crossings` (l.1699–1911).** The hazard definition is
   given four times (l.1708, l.1749, l.1801, l.1893), the threshold argument is
   split across l.1823–1856 and l.1893–1899, and the section narrates its own
   redrafting five times (l.1723, 1786–1787, 1807, 1858–1859, 1893). Proposal
   — one pass, order:
   1. result, stated once (keep l.1706–1712);
   2. `\begin{definition}[Information hazard]\label{def:info-hazard}` —
      *a capability change whose negative sign is admissible in the reference
      frame, above the point at which the impact forces a write*;
   3. `\begin{proposition}[The threshold is a ratio, and sits where the impact
      forces a write]\label{prop:hazard-threshold}`;
   4. the three consequences of "admissible sign" (l.1809–1821) as a remark;
   5. latency / Collingridge / lead-asbestos as a remark;
   6. naming economics + prior art (Hacking, Kauffman, Sen, Bresnahan, Jaffe,
      Bostrom, "capability uplift") as one remark;
   7. the ethical location (l.1908–1911).
   Everything reached "from the other direction", "a moment ago", "the earlier
   treatment" goes.

5. **Label every numbered result that prose refers to by name.** Unlabelled
   today, referred to by name elsewhere:
   | result | line | referred to as |
   |---|---|---|
   | Hypothesis: Minimal graph sufficiency | 681 | falsifier 4, ledger |
   | Hypothesis: Discrete sufficiency | 900 | falsifier 5, `rem:no-denominator` |
   | Hypothesis: Law of Graphic Equalisation | 949 | the paper's title; ledger |
   | Proposition: Antecedent-state principle | 956 | ~8 sites, `cor:mint-is-grammar`, falsifier 6 |
   | Corollary: No self-authorisation | 959 | — |
   | Theorem: The grammar is the loop | 967 | "the reflection theorem" ×5 |
   | Proposition: Admissibility is self-governance | 993 | "Admissibility is not armour" l.2721 |
   | Proposition: Higher-frame first-class | 1924 | l.2721 |
   | Proposition: Ordinal sufficiency | 1934 | — |
   | Proposition: Arbitrary refinement | 907 | — |
   | Remark (untitled, Rovelli) | 378 | — (give it a title too) |
   | Remark: Empirical instance | 2063 | — |
   Add `\label`s and replace the by-name references with `\ref`s.

6. **Move `def:states` earlier.** It is defined at l.1959 but its four states
   are spelled out at l.436 and l.989 (the latter restating the whole thing
   "accordingly"). It is about *edges*, so its home is `sec:situated`, right
   after `cor:frame-dimension`; `sec:present` then only needs `U_F`.

7. **`def:runner` (l.2115) is a definition carrying a two-paragraph
   argument** ("Two different things can be meant by provenance being
   hidden…"). Keep the first paragraph as the definition; the exposure/leakage
   contrast becomes `remark[Exposure is excluded; leakage is produced]`. Also
   rename the label to `def:primitives` (it was the runner definition once;
   the title changed and the label did not).

8. **`def:well-formed` (l.1275–1287) is five paragraphs.** Definition = graded
   along four costs (l.1276–1281). The pruning dynamics, "systems clean up
   after being burned", and "an ill-formed graph runs; it pays more to"
   (l.1282–1287) are a remark.

9. **Orphan sentence at l.679** ("No parent pointer, world model, … is
   primitive.") sits between `rem:idealising` and the sufficiency hypothesis
   with no environment. Fold it into the hypothesis's lead-in or into
   `def:graph`.

10. **Misplaced paragraph at l.2061** ("This orders two capabilities…") is
    about inference-precedes-time and should directly follow `cor:reactive`
    (l.2055), not `rem:no-denominator`.

11. **"Frame" is used ~100 times before `def:frame` at l.982.** Acceptable in
    a reference work, but Axiom −1 (l.205) should carry one forward pointer:
    "…made in some frame (Definition~\ref{def:frame})".

---

## D. Narrated drafting — remaining sites

Commit 7309f2b9 removed twelve. These survive (all "a paper is what it says
now" violations; each is a delete or a one-clause rewrite):

| line | phrase |
|---|---|
| 362 | "an earlier reading here held it was a methodological guard" |
| 459, 2728 | "both were folded away at some point and restored by audit" |
| 496–502 | "And the account has two unpaid entries, not one … Counting only one invites…" |
| 633–634 | "the earlier claim that … It is withdrawn." (keep the *content*; drop the retraction framing) |
| 827 | "though less than a first statement of this remark claimed" |
| 845 | "*the partition is forced; the names are not* overreaches by exactly that margin" |
| 1189 | "corrects the class named a moment ago" (see A.7) |
| 1323 | "conflating them is what the earlier phrasing did" |
| 1723 | "a mechanism this remark was missing" |
| 1786–1787 | "the earlier suspicion that this account had simply not read enough was half right" |
| 1807 | "what the earlier treatment of latency was missing" |
| 1858–1859 | "this section had nonetheless concluded that the transfer event was unnamed" |
| 1893 | "The ratio framing only gestured at what follows" |
| 2348 | placement note (A.13) |
| 2664–2666 | "reached its form by successive correction and records those corrections … Stated once, without the history" — then states it with the history |
| 2693 | "Marked [shape] on reconsideration" |
| 2721 | "Two commitments that once sat in the list above" |
| 2743–2753 | "all four were still counted separately … what is withdrawn is the implication" |
| 2755 | "three entries above were re-marked after…" |

The ledger's own rule (l.386–388) is that withdrawals are recorded *in the
review record*, not in the paper. Apply it.

---

## E. Build and tooling

1. **Generate the counts** (A.3): extend `tools/build_statement.py` to write
   `01.counts.tex` (environment counts, `\bibitem` count, cited count) and
   `\input` it at l.169. A count that is regenerated cannot drift.

2. **Cross-document numbering** (A.1): either the `xr` package
   (`\externaldocument{00_is}` then `\ref{prop:one-way}`), or have the build
   script resolve `@xref 00_is prop:one-way` lines the way it resolves
   `@pull`. Three hard-coded numbers are wrong today; more will be.

3. **Lint for the statement.** After C.2–C.4, update `01s.spec` to pull
   `prop:decoherence-one`, `def:capability`, `def:info-hazard`,
   `prop:hazard-threshold`, `hyp:cheap-cut` instead of the remarks. Today the
   statement pulls `rem:decoherence-one` and `rem:inherited` whole — that is
   ~350 lines of argument in a document that says it "argues for none of
   them".

4. **A `\ref`-by-name check.** A 20-line script that greps
   `antecedent-state principle|reflection theorem|Graph Law|Minimal graph
   sufficiency|Discrete sufficiency` and fails if any occurrence is not
   adjacent to a `\ref` would have caught C.5.

---

## F. Prose (lower priority, representative not exhaustive)

- l.1266–1272 `prop:economics`: one 90-word sentence with four nested
  qualifications. Split at "Free here means…".
- l.1291–1294 `rem:landauer-change`: a 60-word parenthetical ("which is the
  strong form of that claim and is not derived — an append-only rule … — so
  change and irreversible operation coincide") inside the main clause. Pull
  the parenthetical out as its own sentence *after* the claim.
- l.2094 `rem:processor` opens with a ~150-word sentence whose final "which
  is why 'time is a variable-length cycle' reads as exotic" has lost its
  subject. Split at "The variable timing's mechanism…" and again at "which
  is the leak…".
- l.2487 "That proposition is the paper's discriminating test" — two
  paragraphs and a 90-line remark after `prop:convergence-observed`; name it.
- l.1944 `prop:partial-order` is a proposition body of ~180 words containing
  its own proof and a rebuttal. Statement first; argument after `\end{}`.

---

## Suggested order of work

1. A.1–A.5, A.7–A.10, A.13–A.14 (an hour; zero judgement calls).
2. B.1 and B.2 (author decision; both are places a hostile reader lands
   first).
3. C.5 labels, then C.2/C.3/C.4 splits, then `01s.spec` (E.3).
4. D sweep.
5. E.1/E.2 so A.1 and A.3 cannot recur.
6. C.1, F.
