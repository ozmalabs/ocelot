# Review of `01_law_of_graphic_equalisation_theory_referenced.tex` (draft-2026-09-02.1, r280) — proposal for fixes

Third pass. Scope: the whole file (3323 lines, ~70 pp), its log and aux, the
r278 review and what r279–r280 did with it, the two results r280 added
(`rem:one-write`, falsifier *A held program is one write*), and the aux files of
every companion 01 declares (00, 01a, 01b, 02, 02a, 03, 04, 05, 06, 09) for
each cross-paper reference. `00_REVIEW_r121` and `01a_REVIEW_r42` were read for
the set-wide conventions. Line numbers are r280. Nothing applied.

Compile: **0 warnings, 0 overfull, 0 underfull**, no `??`, 153 labels, no
duplicate labels; 83 bibitems, all 83 cited, none uncited, list sorted, no bare
`et al.` and no "and colleagues", `\texorpdfstring` on the `\date` dashes;
`check_paper_refs.py` reports **0 unreferenced by-name mentions**; all 70
distinct `GE-` labels cited by other papers resolve in 01's aux; all **37**
external `\ref`s (`IS- PH- MS- SM- SG- NM- NV- FR- AS- AD-`) were checked one by
one against the target `.aux` and **all 37 resolve** — the naming census of r278
§B is now clean (no "the companion", no "the Seldon paper", no
"the Narrative-momentum paper"), r278 §A (the A1-as-evidence sentence and the
`prop:partial-order` reconciliation), §C (falsifier 12's supply clause), §D (five
proposition/remark pairs) and §E (narrated drafting) are all done, and the eight
missing section labels are added. `BN-` is not declared and does not need to be:
01 names the Born note only in the companion table and makes no claim on its
content. **What this pass finds is substantive rather than mechanical: one whole
part of the paper — "Order and time", including an axiom and the most-cited
proposition in the set — carries no falsifier at all; the three remarks around
the new `rem:one-write` give three different and unreconciled destinations for
the same disappeared cost, and one of them contradicts `rem:third-cost`
outright; `rem:one-write` states its arrangement as flat mechanism where the
paper's own discipline requires a contingency status; two sites still bank on
the un-released realisation as evidence, one of them falsifying the scope
sentence's own "the one place"; two sites negotiate with a companion in the
text; one acyclicity argument uses a premise its axiom does not supply; and six
companion attributions remain by description with no number.**

Seventy of 01's labels are cited by other papers via `GE-` — most heavily
`ax:no-view` (25), `def:well-formed` (19), `sec:falsifiability` (10),
`sec:scope` (7), `rem:only-g`, `prop:cycle-unit`, `prop:compression-convergence`,
`def:frame` (6 each), `prop:no-direct-self-alter`, `prop:economics`,
`hyp:the-law` (5 each), `rem:types-forced`, `prop:self-governance`,
`prop:higher-frame`, `prop:decoherence-one`, `prop:convergence-observed` (4
each), and both of r280's new labels (`rem:one-write` ×2,
`rem:phase-not-time` ×2). All must survive under the same names and kinds.

---

## A. One part of the paper carries no falsifier: "Order and time"

Every `\ref` inside `sec:falsifiability` (l.2818–2887) was extracted. The
commitments reach 36 labels. **None of them is in Part "Order and time"**
(l.2047–2228). Uncovered, with nothing in the list that covers them by content:

| result | line | what is unexposed |
|---|---|---|
| `ax:no-time` (Axiom 1) | 2128–2132 | that the substrate has no time dimension and no succession-engine |
| `prop:ordinal` | 2052–2054 | that no primitive real-valued metric duration is required |
| `prop:time-observer` | 2138–2144 | $T\in\mathcal F$ iff the frame instantiates the representing relation |
| `prop:time-inferred` | 2158–2163 | that a frame acquires time only by inference |
| `cor:reactive` | 2165–2167 | that a frame can participate fully with $T=\mathrm{NULL}$ |
| `prop:cycle-unit` | 2186–2188 | that the unit is a cycle and requires closure |
| `rem:phase-not-time` | 2190–2210 | **new in r280** — no negative time, signed phase |

The two nearest entries do not reach these. *Partial-order sufficiency* tests
whether dynamics require a **total order across frames**; it says nothing about
whether a frame must instantiate a time dimension, nor about metric duration.
*Globally-async/locally-sync* tests coupling. So the paper's most-quoted
structural claim outside the axiom — `prop:cycle-unit`, cited six times by
companions and load-bearing in 01a's decay and dilation arguments — is stated,
grounded in a measured instance (`rem:empirical-instance`), and never staked.

This is the more serious because `rem:empirical-instance` (l.2174–2184) already
*is* a test of `prop:time-inferred`, run and reported; the list simply does not
record what it would have cost had it come out the other way.

**Fix.** Three entries, placed after *Globally-async/locally-sync*:

> `\item \textsc{[shape]}~\textbf{Time is inferred, not primitive.}` Fails if a
> frame's realised dynamics require a temporal coordinate that is not
> constructed from relations among what it holds — a collapse presenting a
> duration as a datum of the state rather than as a reading over states
> (Axiom~\ref{ax:no-time}, Proposition~\ref{prop:time-inferred}). A frame that
> represents succession is not the counterexample; that is what the claim
> predicts. Marked `[shape]` because what would fail is the range of everything
> derived through the absence of a substrate time dimension.

> `\item \textsc{[detail]}~\textbf{The unit of inferred time is a cycle
> requiring closure.}` Fails if a frame without a closed rule-loop nevertheless
> holds a time dimension, or if inferred time is found uniform in underlying
> change rather than varying with what a cycle does
> (Proposition~\ref{prop:cycle-unit}, Corollary~\ref{cor:reactive}). Marked
> `[detail]` because a different unit refines the reading rather than restoring
> a substrate time dimension.

> `\item \textsc{[detail]}~\textbf{A cycle count is one-way; phase is signed.}`
> Fails if a frame's own count of completed cycles is found to run below its
> entry point, or if a signed phase is shown to carry duration rather than
> orientation (Remark~\ref{rem:phase-not-time}).

Three further results are uncovered and each is a real claim, not a definition:

- **`prop:coupling`** (l.1001–1003, *Coupling is configuration, not
  architecture*) — that instances sharing a container propagate to each other
  through it, and that sharing is a continuous setting. Propose:
  `[shape]` **Coupling is a setting, not a kind.** Fails if instances that are
  subgraphs of one containing frame are found not to deform one another through
  it, or if the substrate is shown to fix the setting rather than leaving it to
  rule content (Proposition~\ref{prop:coupling}).
- **`prop:two-gates`** (l.1039–1045) — the absent/residual asymmetry this paper
  uses at least eight times ("The first is a limit of perception, the second a
  limit of expression"). *Residual is inadmissibility* tests $\Gamma_c$ only.
  Propose: `[shape]` **Two gates, and absence is not residual.** Fails if what a
  frame's aperture excludes is nonetheless held or disturbs it — an excluded
  input leaving a remainder in place — so that the input and output faces stop
  differing in what their exclusions cost (Proposition~\ref{prop:two-gates},
  Definitions~\ref{def:aperture} and~\ref{def:change-grammar}).
- **`prop:copyable-generators`** (l.1426–1428) — only the *copy* half is touched,
  by the second clause of *A held program is one write*. Either extend that
  entry's clause to name `prop:copyable-generators`, or say in one clause that
  the difference-in-kind claim is a consequence of `prop:economics` plus
  `def:self-identity` and belongs with the two derivations at l.2854.

`hyp:the-law` itself is not in the list either. It is arguably covered jointly
by *Antecedent-state*, *Graph-law determinism* and *Partial-order sufficiency*;
if so, say so in one clause where the list closes, since a reader checking
coverage will look for the Law by name and not find it.

---

## B. Three remarks, three destinations for the same disappeared cost — and one contradiction

`rem:cost-to-zero` (l.1144–1163, r280-adjacent), `rem:one-write` (l.1165–1184,
new in r280) and `rem:third-cost` (l.1308–1334) all explain where the cost of an
absorbed task goes, and they do not agree.

1. l.1152–1156: "A frame meeting something that coheres with what it already
   holds writes nothing, and what forces no write costs nothing --- so *the cost
   of a task falls toward zero as the task becomes held*, and the floor does not
   bind because the floor is on change and a fully absorbed task is not a
   change. That is what expertise is, mechanically: not a faster way of paying
   but **a task that has stopped costing**."
2. l.1174–1177: the per-step cost "has **moved below the frame's aperture into
   what supplies the program**", the runner still paying per lane.
3. l.1329–1333: "Driving the cost of tasks down means holding more, and what is
   held is searched: **the third cost rises exactly as the first falls.** So a
   frame does not approach zero total cost by absorbing everything."

(3) contradicts (1) flatly. Under `def:well-formed` (l.1345–1351) search "is paid
on every operation over what is held and scales with how much is held", so a
held task has not stopped costing — its cost has moved from the write column to
the search column. (2) gives a third and different destination (down the supply
chain). All three can compose — absorption moves a write cost partly into
in-frame search and partly into the runner's bill — but the paper never says so,
and (1) is stated as an unqualified limiting form of `prop:no-free-lunch`, which
is exactly the "assignment of the cost mistaken for the invariant" error
l.1119–1122 warns against.

The same remark's **title promises what its body does not deliver**: "The cost of
a task approaches zero, **and the total does not**". The four paragraphs are
statement, overhead reading, absorption reading, prepayment. The *total* claim
appears 170 lines later, in a different remark, without a pointer back.

**Fix.** In `rem:cost-to-zero`, replace "a task that has stopped costing" with
the accounting: *"That is what expertise is, mechanically: not a faster way of
paying but a task whose cost has left the write column — for the search cost of
holding it (Remark~\ref{rem:third-cost}) and for whatever supplies it
(Remark~\ref{rem:one-write}), neither of which the frame pays as a write."* Then
either move the l.1329–1333 sentence into `rem:cost-to-zero` as the paragraph
its title promises, or add one forward clause: *"The total does not follow it
down, for the reason Remark~\ref{rem:third-cost} gives."* If the sentence moves,
`rem:third-cost` keeps the aperture-as-live-setting conclusion and cites back.

---

## C. `rem:one-write` states a contingent arrangement as flat mechanism

l.1165–1184. The remark is right and is the piece the set needed. What it does
not say is what kind of claim it is. It asserts "The accounting is that of vector
hardware, one instruction over many data: one decode, many lanes" and "expertise
is a change in where the work is charged and not in how much work there is" with
no status marker at all — read straight, it is a claim about what a held program
*must* be.

That is not the position. A held program being one write is **forced by physics
and by observed behaviour, not by the nature of existence**: it is an
optimisation an efficient frame accretes under a budget, in exactly the sense
`rem:nothing-compulsory` (l.1414–1416) gives for the two gates and
`rem:writeability` (l.1418–1424) gives for the write-economics generally. The
falsifier the same revision added is marked `[detail]`, which is consistent with
contingency — but the remark itself never says it, so the mark and the text
carry different modalities.

**Fix.** Add one sentence after "one decode, many lanes":

> *The status of that arrangement is the one Remark~\ref{rem:nothing-compulsory}
> gives the gates: it is what a frame under a budget accretes, forced by what
> supplies it and confirmed by what such frames are observed to do, and not a
> necessity of graphhood. A substrate in which every step is separately written
> runs; it pays more to.*

The eye is the case worth naming in the same sentence if a case is wanted — it
works that way because the physics of the supplying tissue and the observed
behaviour force it, which is precisely the contingency being marked.

---

## D. Two sites still rest a claim on the un-released realisation, and one of them falsifies the scope sentence

The rule (l.72–73, and the table row at l.97): A1 "is cited below where its
*contents* bear on a claim, never as evidence for one".

**1. l.143.** "The last of these has a consequence for how the construction paper
should be read: construction has been a *source* of this theory rather than only
a test of it. **The evidence is** $r$'s own provenance immediately above --- ...
--- **and the construction paper's closing list of eleven distinctions** that
implementation forced upon the theory records eleven further instances of the
same direction of travel."

The sentence names two things as *the evidence* and the second is A1's contents.
That is banking a commitment on a document the reader cannot obtain, in the
paragraph that has just forbidden it. **Fix:** keep the first conjunct as the
evidence and demote the second to description — *"The evidence is $r$'s own
provenance immediately above ...; the construction paper describes eleven further
distinctions implementation forced upon the theory, about antecedence, identity
typing, residual and absent dimensions, which a reader cannot check and which is
offered as an account of the direction of travel rather than as support for it."*

**2. l.988.** "**The unification is not this paper's invention:** the substrate's
own implementation has no frame primitive at all, its grammar quantifying over
edge types, and a frame there is a selection of dimensions."

Three defects in one clause. It is an appeal to the un-released realisation as
evidence for a priority claim. It refers to that realisation as "the substrate's
own implementation", which is not one of the forms the companion table licenses
(l.70: "The short name in the middle column is the only form used below"). And it
makes the scope paragraph's "**The one place** below where a *measurement* is
reported from that programme's own record" (l.74) false as scoped — this is a
second report from the same un-circulated record, offered as evidence, and not
governed by the standard at l.74–78 because it is a structural fact rather than a
measurement.

**Fix.** Either delete the clause — `cor:frame-dimension` (l.976–978) already
argues the unification from the boundary edge and needs nothing else — or state
it as description under the licensed name and drop the evidential frame:
*"The construction paper's realisation carries no frame primitive, its grammar
quantifying over edge types; that is a description of one realisation and not
support for the corollary, which stands on the edge alone."* If it is deleted,
l.74 is true as written; if it is kept, l.74 must be widened from "*a
measurement*" to "any report from that programme's own record".

`l.71` (the table paragraph) and `l.2183` (`rem:empirical-instance`'s closing
sentence, which does invoke the standard by number) are both correct as they
stand.

---

## E. Two sites negotiate with a companion inside the text

Convention: a paper is what it says now; no inter-paper negotiation.

**1. l.2171**, inside `rem:no-denominator`: "*Narrativium*'s reconciliation is
right about the provenance and this remark is right about the type; **neither has
to give way.**" This is the forbidden form exactly, and it also cites
*Narrativium* by description with no `\ref`. It is redundant besides: 04 l.363–364
already states the same result and cites `GE-rem:no-denominator` for it, so the
agreement is on the record in the companion. **Fix:** delete the clause. The
sentence before it ("a rate is in-frame in its provenance and cross-frame in its
type") is the result and stands alone. If a pointer is wanted, *Narrativium*
carries it at its Proposition~\ref{NV-prop:overshoot} (verified in 04's aux; that
proposition's following prose is the site).

**2. l.2819–2820**, in `sec:falsifiability`'s preamble: "**So the papers do not
disagree**, and either sentence read alone will look as though they do." The
whole paragraph (l.2809–2820) is a reconciliation of 01's *carries no falsifiable
content* with 06's finding, and it sits between the `[shape]`/`[detail]`
definition sentence and the Composition falsifier, where it interrupts the list's
own setup. Its content is a scope note, not a falsifier. **Fix:** cut the last
sentence, and move the paragraph to *after* the enumerated list, in the short
scope-note form the set uses:

> `\noindent\emph{Scope note (not a falsifier).}` *Carries no falsifiable
> content* names the same condition the assessment companion reaches by asking
> whether *attempting* a counterexample has an outcome (its
> Proposition~\ref{AS-prop:discriminator}). Where the putative counterexample
> would not cohere, neither *testable* nor *empty* applies as a reader's ordinary
> falsifiability frame hears it; the distinction sits below the grain at which
> falsifiability is usually argued.

---

## F. Propositions and a corollary that argue rather than state

Convention 5. The worst three:

**`prop:runner-opaque`, l.2292–2298 (347 words, three paragraphs).** Paragraph 1
states. Paragraphs 2 and 3 argue: "Calling the runner unseeable rather than
unseen runs two claims together. That a runner is hidden is *contingent*.
Nothing forbids a runner from exposing its own state ... a tower in which each
level is available to the one above is a built artefact, not a thought
experiment." That is a defence against an objection, inside a numbered result, and
it is the longest proposition in the paper by a factor of two.

**Fix.** The proposition keeps two sentences: *"Where a frame has no boundary to
the substrate that runs it, its runner lies beyond the frame's epistemic boundary
(Section~\ref{sec:scope}); a hidden runner may execute the graph serially while
the graph appears asynchronous to itself (Remark~\ref{rem:gals}). And no level is
self-transparent: reading is an operation whose product lands one level up
(Remark~\ref{rem:evaluation-writes}), so a level cannot hold the reading of itself
while being the level that is running — a frame may be given sight of what runs
it and cannot be given sight of its own running."* Paragraphs 2–3 become a titled
remark immediately after, `\begin{remark}[Hidden is contingent;
non-self-transparent is not]\label{rem:opacity-two-claims}`, opening "Proposition
\ref{prop:runner-opaque} separates two claims that are easily run together." The
`\subsection*` prose at l.2299 that follows (the cellular-automaton
demonstration) can join it or stay.

**`cor:locked-in`, l.2037–2039 (182 words, one paragraph).** "The restriction to
container-supplied frames **is not a hedge**: termination propagates along supply
and not containment ..., so a graph whose supply is its own can stop itself by
withdrawing it, and the corollary says nothing of that case." A corollary
defending its own scope. **Fix:** the corollary states the locked-in result for a
container-supplied graph; the scope defence and the locked-in/brain-in-a-jar
reading move to a two-sentence remark after it. (The falsifier at l.2836 already
cites the corollary for the restriction, so the restriction must stay stated —
just not defended in the corollary body.)

**`prop:leak`, l.2261–2281 (236 words).** "Leaking is ordinary rather than
exceptional" is motivation; "How a leak reaches a frame at all is worth stating,
since ..." is a paragraph of argument. **Fix:** the proposition is the last
paragraph ("*partial always, complete never*") plus one sentence that primitives
disclose structure beneath them; the leak inventory and the
perception-versus-inference paragraph move into `rem:exposure-leakage`
(l.2242–2259), which is already the remark for exactly this.

Three lighter cases, worth one pass each: `prop:runner-recursion` (l.2301–2303)
carries the chain/fan-out illustration inside the statement;
`prop:no-direct-self-alter` (l.996–998) ends on "'Change only yourself' is
therefore not isolation but the mechanism of outward effect", which is the
argument's conclusion rather than the claim; `prop:economics` (l.1336–1342) ends
"This is a characterisation of the substrate as specified, not a necessity of
graphhood", which is a status note and belongs in the sentence after
`\end{proposition}` where the paper already puts such notes.

---

## G. Six companion attributions still carry no number

The by-name checker passes because it looks for a `\ref` near the companion's
name; these six state a companion's claim and give no target.

| line | attribution | where the target should be found |
|---|---|---|
| 500 | "the physics companion says so of free continuation" | 01a's free-continuation / information-preserving result; grep 01a for *free continuation* and take the enclosing label |
| 988 | "the substrate's own implementation" | see §D — not a companion reference at all |
| 1279 | "bears on the mind companion, where a frame under stress becomes manipulable by having its horizon shortened ... That paper gives its own account of the shortening" | 01b's horizon/stress result; `MS-prop:manipulation-structural` is already used at l.2019 and may be the site — verify before use |
| 1401 | "what lets the physics companion recover unitarity" | 01a's unitarity passage; grep 01a for *unitarity* |
| 1496 | "The physics companion separates the sense used here from the standard environmental one and states what relates them" | almost certainly `PH-rem:two-decoherences`, which 01 already uses at l.1749 — verify it is the site and reuse |
| 2171 | "*Narrativium*'s reconciliation" | see §E — delete rather than resolve |

Two more sites, smaller: l.185 ("treated in the assessment companion rather than
here") is a bare pointer where `AS-sec:risk` — already used at l.2791 — would
resolve it; and l.656–657 attributes the idealisation criterion to *Is* with no
number.

Every external target 01 currently uses was checked in the target `.aux` and all
37 resolve, so the mechanism is in place and only these rows are missing.

---

## H. `rem:funding-category`'s acyclicity argument uses a premise the axiom does not supply

l.1088–1092: "The event order cannot loop. Axiom~\ref{ax:no-time} makes
enablement asymmetric --- if one change makes another possible, the second does
not thereby make the first possible --- and Proposition~\ref{prop:partial-order}
totally orders a frame's own writes, **so an asymmetric transitive relation
admits no cycle of any length**."

Two problems. `ax:no-time` (l.2128–2132) asserts **asymmetry** and nothing else;
the conclusion needs **transitivity**, which is introduced in the "so" clause
without ever having been claimed. And `prop:partial-order`'s total-order clause
is in-frame only, while the conclusion the remark needs is about the event order
generally, across frames — so the cited proposition does not close the gap
either. Asymmetry alone forbids 2-cycles and permits longer ones.

**Fix.** Either add transitivity to `ax:no-time` where the asymmetry is stated
(*"and enablement is transitive: if one change makes a second possible and the
second a third, the first makes the third possible"*) and cite the axiom alone
here; or weaken the remark to what the premises give — *"Axiom~\ref{ax:no-time}
forbids a change enabling what enabled it, and
Proposition~\ref{prop:partial-order} makes a frame's own writes a total order, so
no cycle sits inside one frame; whether a longer cycle can close across frames is
not settled here, and nothing below needs it settled."* The second is the honest
one if transitivity is not wanted as an axiom clause, and it does not cost the
remark anything: the surviving claim is category-preservation, which the
remaining paragraphs argue on their own.

---

## Smaller

1. **l.656–657: a word duplicated by the naming sweep.** "the criterion that
   answers it belongs to the method rather than to this paper and is stated in
   \emph{Is}\n\emph{Is}: an idealisation is a frame ...". Delete one *Is* and add
   the number (`IS-` target to be located in 00 and verified).
2. **l.1423: a dangling self-reference.** "would be the same over-specification
   **the theory warns against** for a scalar knob put where a shape belongs."
   Nothing in this paper warns against that, in those terms or any other — the
   phrase is imported from outside the papers. Fix: *"...would be the same
   over-specification Remark~\ref{rem:nothing-compulsory} warns against, a fixed
   value put where the account has only a setting."*
3. **One verbatim sentence survives between a proposition and its remark.**
   l.1374–1375 (`prop:evaluation-writes`) and l.1398 (`rem:evaluation-writes`)
   both carry "a rule's cost is set by whatever supplies its primitives and is
   inherited along provision". Drop it from the remark, which cites
   `sec:rule-runner` in the same sentence and can say "for the reason the
   proposition gives".
4. **l.1077: "what the substrate forbids is nothing".** Read on its own this
   contradicts `prop:prohibition` (l.2324–2330), which forbids one thing. Fix:
   "what the substrate's *economics* forbids is nothing".
5. **l.1912: "this programme's own standing rule, learned expensively elsewhere
   in it".** The rule (a difference smaller than its noise is not a result) is
   right and load-bearing here; "learned expensively elsewhere in it" is
   programme history doing no work in the sentence. Cut the clause.
6. **Long remarks carrying several arguments** (convention 8), with proposed
   splits: `rem:evolution-compression` (l.2512–2605, 1192 w / 93 lines) is four
   arguments — the independence/antecedent trade, the junk-DNA objection and the
   `lynch2003` prediction, the dead-code and appendix cases on removal cost, and
   convergent evolution plus punctuated equilibrium; propose
   `rem:evolution-antecedent`, `rem:inert-sequence`, `rem:removal-cost`,
   `rem:convergent-evolution`. `rem:naming-economics` (l.1951–2017, 66 lines)
   splits at "The absence of a neutral term is not uniform" into the economics
   and the prior art on each half. `rem:sideways-and-up` (l.1186–1246, 60 lines)
   splits at "Two honest qualifications" and again at "One terminological
   caution", the last being a definitional note that belongs beside
   `def:capability`. `rem:inherited` (128 lines) is the ledger prose and reads
   correctly as one piece; leave it.
7. **Long single paragraphs.** `rem:no-denominator` (l.2171, 284 words in one
   paragraph) carries six moves — $\Delta$ not $\Delta/\Delta T$; the inputs are
   in-frame; the quotient is not; the *Narrativium* clause (delete, §E); the
   substrate-law-in-$\Delta$ consequence; the adaptive-rate regress. Break after
   "maps are where non-integer structure is allowed to live" and again before
   "It also diagnoses a familiar regress". Same treatment for
   `rem:landauer-change` (l.1362–1364, 229 w), `rem:nothing-compulsory`
   (l.1414–1416, 209 w) and `rem:collapse-write` (l.935–937, 195 w), each of
   which is two arguments in one block.
8. **Two `\subsection*` heads are unnumbered and uncitable:** "What kind of thing
   this is claimed to be" (l.181) and "The formal analogue" (l.2340). The second
   in particular is a self-contained four-qualification argument other papers
   will want; give it `\label{sec:formal-analogue}` at minimum.
9. `rem:axiom-in-bits` (l.293–295) and `rem:why-minus-one` (l.382–383) both say
   the axiom "is not a costless methodological guard"; `rem:inherited` (l.512–516)
   says that in *this paper* it is exactly a guard and "a discipline is not a
   place this paper can fail". The split is right and is stated in the third
   place only. One clause in each of the first two ("*in the groundings*") makes
   the three agree on first reading.

---

## What is right and should not be touched

- The mechanical state. Zero compile warnings, a clean and complete
  bibliography, no implementation identifiers anywhere in the typeset text (the
  greps for `.py`/`.rs`/`.json`/`seeds/`/hashes/Term names return only
  `jaffe1993`, a `PLoS Genetics` article id, and a `\newblock`), and the whole
  `xr-hyper` apparatus working across ten companions.
- The naming discipline, now actually enforced: every companion mention uses the
  table's short name, and the table itself is the licence.
- `rem:inherited` as it now stands — the ledger table plus named-not-counted
  entries, the withdrawal recorded with each, the third tier for the hypotheses,
  and "How to read the count" refusing the reduction-to-zero temptation.
- The r278 §A repair. The A1-as-evidence sentence is gone, and l.488 now rests
  the same argument on the physics companion by number while l.2064 states the
  sequential-write regime that agrees with it. Both sides now say the same thing.
- `rem:phase-not-time` (new). "There is no negative time; there is signed phase"
  with the $e^{\pm i\omega t}$ case handed to 01a by number is the right division
  of labour, and the diagnosis ("the manufactured object then needs a mechanism
  to forbid it --- a mechanism nothing owed") is the paper at its best.
- `sec:prohibition`'s four qualifications on the formal analogue, and
  "the impossibility has a formal analogue whose analogue is proved, and the
  mapping is argued --- which is weaker than 'the prohibition is proved'".
- `prop:no-free-lunch` stated as an observed universal with the quantifier
  refused, and the buffet, and the falsifier's two-level bound.
- `rem:evolution-compression`'s honesty about which axis biology wins on, the
  `whitney2010` contestation kept in, and "convergent evolution is
  Proposition 20.3 with a name biology gave it first".
- `rem:empirical-instance`'s structure: prediction, protocol, result, *the
  bound, which is real*, and the standard invoked by number at the close.
- The falsifier list's closing apparatus — four entries as one risk, the two
  postulates exposed by name, and "the marks themselves are revisable".

---

## Suggested order

1. **A** — the falsifier gap. Three entries for time, two for coupling and the
   gates, one clause for the copyable generator and one for the Law.
2. **B** and **C** — the three cost remarks reconciled, and `rem:one-write`
   given its status. These are adjacent in the text and should be done together.
3. **D** — the two evidence sites, and l.74 made true whichever way §D.2 goes.
4. **E** — two deletions and one paragraph moved after the list.
5. **H** — one axiom clause or one weakened sentence.
6. **F** — three splits, three lighter passes.
7. **G**, then **Smaller**.
